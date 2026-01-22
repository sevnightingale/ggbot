#!/usr/bin/env python3
"""
Signal Publishing Service

A PM2-managed service that publishes validated signals to user Telegram channels.
Only available to ggBase tier users with proper access control.
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Add project root to path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from core.common.logger import logger
from core.common.db import get_db_connection


@dataclass
class TelegramChannel:
    """User's telegram channel configuration."""
    chat_id: str
    channel_name: Optional[str] = None
    enabled: bool = True
    message_template: Optional[str] = None
    include_reasoning: bool = True
    include_market_context: bool = False
    confidence_threshold: float = 0.6


class AccessControlService:
    """Access control for signal publishing features."""
    
    def __init__(self):
        self.logger = logger.bind(component='access_control')
    
    async def can_publish_signals(self, user_id: str) -> bool:
        """Check if user can publish signals (any paid tier with active subscription)."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT subscription_tier, subscription_status
                        FROM user_profiles
                        WHERE user_id = %s
                    """, (user_id,))

                    result = cur.fetchone()
                    if not result:
                        return False

                    tier, status = result

                    # Match frontend permission: can_activate_bots logic
                    # Paid tiers (usage_based, prepaid, pro) with active status can publish
                    paid_tiers = ('usage_based', 'prepaid', 'pro')
                    return (
                        tier in paid_tiers and
                        status == 'active'
                    )

        except Exception as e:
            self.logger.error(f"Failed to check signal publishing access for {user_id}: {e}")
            return False
    
    async def get_user_telegram_config(self, config_id: str) -> Optional[TelegramChannel]:
        """Get user's telegram channel configuration for a specific bot config."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # First, get the config and check if telegram publishing is enabled
                    cur.execute("""
                        SELECT config_data 
                        FROM configurations 
                        WHERE config_id = %s
                    """, (config_id,))
                    
                    config_result = cur.fetchone()
                    if not config_result:
                        return None
                    
                    config_data = config_result[0]
                    
                    # Handle nested config_data structure like in config_service
                    if "config_data" in config_data:
                        inner_config = config_data["config_data"] 
                        telegram_config = inner_config.get('telegram_integration', {})
                    else:
                        telegram_config = config_data.get('telegram_integration', {})
                        
                    publisher_config = telegram_config.get('publisher', {})
                    
                    if not publisher_config.get('enabled', False):
                        return None
                    
                    # Check for user-provided channel ID (frontend uses 'filter_channel')
                    user_channel_id = publisher_config.get('filter_channel') or publisher_config.get('user_channel_id')
                    if not user_channel_id:
                        return None
                    
                    return TelegramChannel(
                        chat_id=user_channel_id,
                        channel_name=publisher_config.get('channel_name'),
                        enabled=True,
                        message_template=publisher_config.get('message_template'),
                        include_reasoning=publisher_config.get('include_reasoning', True),
                        include_market_context=publisher_config.get('include_market_context', True),
                        confidence_threshold=publisher_config.get('confidence_threshold', 0.6)
                    )
                    
        except Exception as e:
            self.logger.error(f"Failed to get telegram config for {config_id}: {e}")
            return None


class TelegramBot:
    """Telegram bot for publishing signals to user channels."""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.api_base = f"https://api.telegram.org/bot{bot_token}"
        self.logger = logger.bind(component='telegram_bot')
    
    async def send_message(self, chat_id: str, text: str) -> bool:
        """Send message to a telegram chat/channel."""
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": True
                # No parse_mode - plain text like old ggShot format
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_base}/sendMessage", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            self.logger.debug(f"Message sent successfully to {chat_id}")
                            return True
                        else:
                            self.logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                            return False
                    else:
                        error_text = await response.text()
                        self.logger.error(f"HTTP {response.status}: {error_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Failed to send telegram message: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test bot connection and get bot info."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/getMe") as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            bot_info = result.get('result', {})
                            self.logger.info(
                                f"Bot connection successful: {bot_info.get('username', 'Unknown')} "
                                f"({bot_info.get('first_name', 'Unknown')})"
                            )
                            return True
                        else:
                            self.logger.error(f"Bot API error: {result.get('description', 'Unknown error')}")
                            return False
                    else:
                        error_text = await response.text()
                        self.logger.error(f"HTTP {response.status}: {error_text}")
                        return False
        except Exception as e:
            self.logger.error(f"Failed to test bot connection: {e}")
            return False


class SignalPublishingService:
    """Signal publishing service for telegram integration (PM2 service methods removed)."""

    def __init__(self):
        # Use platform bot token from environment
        self.bot_token = os.getenv('GG_FILTER_TOKEN')
        if not self.bot_token:
            raise ValueError("GG_FILTER_TOKEN environment variable is required")
        self.telegram_bot = TelegramBot(self.bot_token)
        self.access_control = AccessControlService()
        self.logger = logger.bind(service='signal_publisher')

    async def publish_validated_signal(
        self,
        config_id: str,
        user_id: str,
        signal_data: Dict,
        decision_result: Dict
    ) -> bool:
        """Publish validated signal to user's configured telegram channel."""
        try:
            self.logger.info(f"📡 Publishing signal for config {config_id}")

            # 1. Check user access (ggBase tier only)
            if not await self.access_control.can_publish_signals(user_id):
                self.logger.info(f"User {user_id} not authorized for signal publishing")
                return False

            # 2. Get user's telegram channel configuration
            channel_config = await self.access_control.get_user_telegram_config(config_id)
            if not channel_config:
                self.logger.info(f"No telegram config found for config {config_id}")
                return False

            # 3. Format message with validation results
            message = self._format_signal_message(signal_data, decision_result, channel_config)

            # 4. Send to user's channel (using user's bot token passed via telegram_bot)
            success = await self.telegram_bot.send_message(
                chat_id=channel_config.chat_id,
                text=message
            )

            if success:
                # 5. Update usage metrics
                await self._update_signal_metrics(user_id, decision_result)
                self.logger.info(f"✅ Signal published successfully to {channel_config.chat_id}")
            else:
                self.logger.error(f"❌ Failed to publish signal to {channel_config.chat_id}")

            return success

        except Exception as e:
            self.logger.error(f"Error publishing signal: {e}")
            return False

    def _format_signal_message(
        self,
        signal_data: Dict,
        decision_result: Dict,
        channel_config: TelegramChannel
    ) -> str:
        """Format signal with ggbots branding."""

        # Extract data for formatting
        action = decision_result.get('action', 'UNKNOWN').upper()
        confidence = decision_result.get('confidence', 0.0)
        reasoning = decision_result.get('reasoning', 'No reasoning provided')

        # Get bot name and symbol from signal_data
        bot_name = signal_data.get('bot_name', 'ggbot')
        symbol = signal_data.get('symbol', 'UNKNOWN')
        config_type = signal_data.get('config_type', 'scheduled_trading')

        # Format action with emoji
        if action in ['LONG', 'BUY', 'ENTER']:
            action_display = "📈 LONG"
        elif action in ['SHORT', 'SELL']:
            action_display = "📉 SHORT"
        else:
            action_display = f"🔥 {action}"

        # Different format for signal_validation vs scheduled_trading
        if config_type == 'signal_validation':
            # Signal validation: show approval status
            threshold_met = confidence >= channel_config.confidence_threshold
            approval_status = "✅ APPROVED" if threshold_met else "❌ REJECTED"

            message_parts = [
                f"Signal: {approval_status}",
                f"{action_display} {symbol}",
                f"Confidence: {confidence:.0%}",
                "",
                f"Reasoning: {reasoning}"
            ]

            # Add original signal context if available
            raw_message = signal_data.get('raw_message', '')
            if raw_message and raw_message.strip():
                message_parts.extend([
                    "",
                    "Original Signal:",
                    raw_message
                ])
        else:
            # Scheduled trading: show bot name prominently
            message_parts = [
                f"🤖 {bot_name}",
                "",
                f"{action_display} {symbol}",
                f"Confidence: {confidence:.0%}",
                "",
                f"Reasoning: {reasoning}",
                "",
                "🌐 ggbots.ai"
            ]

        return "\n".join(message_parts)

    async def _update_signal_metrics(self, user_id: str, decision_result: Dict) -> None:
        """Update user's signal publishing usage metrics."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE user_profiles 
                        SET monthly_signal_count = monthly_signal_count + 1,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (user_id,))
                    
                    self.logger.debug(f"Updated signal metrics for user {user_id}")
                    
        except Exception as e:
            self.logger.error(f"Failed to update signal metrics: {e}")


# Orchestrator integration function
async def publish_signal_to_telegram(
    config_id: str,
    user_id: str,
    signal_data: Dict,
    decision_result: Dict
) -> bool:
    """Publish signal to telegram using platform bot - called by orchestrator after signal validation."""
    try:
        # Create service instance using platform bot token from environment
        service = SignalPublishingService()

        return await service.publish_validated_signal(
            config_id, user_id, signal_data, decision_result
        )
        
    except Exception as e:
        logger.error(f"Failed to publish signal to telegram: {e}")
        return False


async def publish_exit_to_telegram(
    config_id: str,
    user_id: str,
    exit_data: Dict
) -> bool:
    """Publish trade exit notification to telegram.

    Args:
        config_id: Bot configuration ID
        user_id: User ID
        exit_data: Dict with keys:
            - bot_name: Name of the bot
            - symbol: Trading symbol (e.g., BTC/USDT)
            - side: 'long' or 'short'
            - entry_price: Entry price
            - exit_price: Exit price
            - pnl: P&L in USD
            - pnl_pct: P&L percentage
            - close_reason: Why position closed
            - duration_seconds: How long position was open
    """
    try:
        service = SignalPublishingService()
        access_control = AccessControlService()

        # Check permissions
        if not await access_control.can_publish_signals(user_id):
            return False

        # Get telegram config
        telegram_config = await access_control.get_user_telegram_config(config_id)
        if not telegram_config:
            return False

        # Format exit message
        message = _format_exit_message(exit_data)

        # Send message
        success = await service.telegram_bot.send_message(
            chat_id=telegram_config.chat_id,
            text=message
        )

        if success:
            logger.info(f"📡 Published exit notification for {exit_data.get('bot_name', config_id)}")

        return success

    except Exception as e:
        logger.error(f"Failed to publish exit to telegram: {e}")
        return False


def _format_exit_message(exit_data: Dict) -> str:
    """Format trade exit notification message."""
    bot_name = exit_data.get('bot_name', 'ggbot')
    symbol = exit_data.get('symbol', 'UNKNOWN')
    side = exit_data.get('side', 'long').upper()
    pnl = exit_data.get('pnl', 0)
    pnl_pct = exit_data.get('pnl_pct', 0)
    close_reason = exit_data.get('close_reason', 'unknown')
    duration_seconds = exit_data.get('duration_seconds', 0)

    # Format P&L with color indicator
    if pnl >= 0:
        pnl_display = f"✅ +${pnl:.2f} (+{pnl_pct:.1f}%)"
    else:
        pnl_display = f"❌ ${pnl:.2f} ({pnl_pct:.1f}%)"

    # Format duration
    if duration_seconds < 3600:
        duration_display = f"{int(duration_seconds / 60)}m"
    elif duration_seconds < 86400:
        duration_display = f"{duration_seconds / 3600:.1f}h"
    else:
        duration_display = f"{duration_seconds / 86400:.1f}d"

    # Format close reason nicely
    reason_display = {
        'take_profit': '🎯 Take Profit',
        'stop_loss': '🛑 Stop Loss',
        'trailing_stop': '📉 Trailing Stop',
        'position_management': '🤖 AI Exit',
        'manual': '👤 Manual Close',
        'account_reset': '🔄 Account Reset',
        'liquidation': '💀 Liquidation'
    }.get(close_reason, close_reason.replace('_', ' ').title())

    message_parts = [
        f"🤖 {bot_name}",
        "",
        f"CLOSED {side} {symbol}",
        "",
        pnl_display,
        f"Duration: {duration_display}",
        f"Reason: {reason_display}",
        "",
        "🌐 ggbots.ai"
    ]

    return "\n".join(message_parts)


# NOTE: PM2 service main() removed - this module now only provides utility functions
# Telegram publishing is handled directly by the orchestrator (ggbot.py)