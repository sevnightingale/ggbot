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


class AccessControlService:
    """Access control for signal publishing features."""
    
    def __init__(self):
        self.logger = logger.bind(component='access_control')
    
    async def can_publish_signals(self, user_id: str) -> bool:
        """Check if user can publish signals (ggBase tier only)."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT subscription_tier, subscription_status, paid_data_points
                        FROM user_profiles 
                        WHERE user_id = %s
                    """, (user_id,))
                    
                    result = cur.fetchone()
                    if not result:
                        return False
                    
                    tier, status, paid_points = result
                    
                    # Must be ggBase tier with active subscription
                    return (
                        tier == 'ggBase' and 
                        status == 'active' and 
                        paid_points and 'ggshot' in paid_points
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
                        enabled=True
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
    """Main service for publishing validated signals to user channels."""
    
    def __init__(self):
        self.bot_token = os.getenv('GG_FILTER_TOKEN')
        if not self.bot_token:
            raise ValueError("GG_FILTER_TOKEN environment variable is required")
            
        self.telegram_bot = TelegramBot(self.bot_token)
        self.access_control = AccessControlService()
        self.logger = logger.bind(service='signal_publisher')
        self.running = False
    
    async def start(self):
        """Start the signal publishing service."""
        self.logger.info("🚀 Starting Signal Publishing Service")
        
        try:
            # Test telegram bot connection
            if not await self.telegram_bot.test_connection():
                raise ValueError("Failed to connect to Telegram bot")
            
            self.running = True
            self.logger.info("✅ Signal Publishing Service ready")
            
            # Start the publishing queue processor
            await self._run_publishing_queue()
            
        except Exception as e:
            self.logger.error(f"Signal publishing service failed to start: {e}")
            raise
    
    async def _run_publishing_queue(self):
        """Process signal publishing queue (placeholder - would use actual queue system)."""
        self.logger.info("📤 Signal publishing queue processor started")
        
        # TODO: Implement actual queue processing
        # For now, this would be triggered by the orchestrator directly
        while self.running:
            await asyncio.sleep(5)  # Polling interval
            # In production, this would process a queue (Redis, database, etc.)
    
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
            message = self._format_signal_message(signal_data, decision_result)
            
            # 4. Send to user's channel
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
        decision_result: Dict
    ) -> str:
        """Format validated signal for telegram publishing - matches old ggShot format."""
        
        action = decision_result.get('action', 'unknown').upper()
        confidence = decision_result.get('confidence', 0.0)
        
        # Determine status and emoji (matching old ggShot format)
        is_validated = action in ['VALIDATE', 'LONG', 'SHORT', 'ENTER']
        status_emoji = "✅" if is_validated else "❌"
        status_text = "APPROVED" if is_validated else "REJECTED"
        
        # Get confidence threshold from config or use default
        confidence_threshold = 0.65  # Default ggShot threshold
        
        # Build message parts (matching old ggShot structure)
        message_parts = [
            f"{status_emoji} Filter: {status_text} - Confidence: {confidence:.1%}",
            ""
        ]
        
        # Original signal (if available)
        raw_message = getattr(signal_data, 'raw_message', '')
        if raw_message and raw_message != "Manual trigger initiated by user":
            message_parts.extend([
                raw_message.strip(),
                ""
            ])
        else:
            # For manual triggers or missing raw message, create a summary
            symbol = getattr(signal_data, 'symbol', 'Unknown')
            direction = getattr(signal_data, 'direction', 'Unknown')
            source = getattr(signal_data, 'source', 'unknown')
            
            if source == 'manual_trigger':
                signal_summary = f"Manual validation test for {symbol} - {direction} signal analysis"
            else:
                signal_summary = f"{source.upper()} signal for {symbol} - {direction} direction"
            
            message_parts.extend([
                signal_summary,
                ""
            ])
        
        # Reasoning (matching old format)
        reasoning = decision_result.get('reasoning', 'No analysis provided')
        message_parts.extend([
            "Reasoning:",
            reasoning.strip(),
            ""
        ])
        
        # Summary details (matching old ggShot format)
        message_parts.extend([
            "Summary:",
            f"• Confidence Score: {confidence:.3f}",
            f"• Threshold: {confidence_threshold}",
            f"• Status: {status_text}"
        ])
        
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
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for monitoring."""
        bot_status = await self.telegram_bot.test_connection()
        
        return {
            'status': 'healthy' if (self.running and bot_status) else 'unhealthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'telegram_bot_connected': bot_status,
            'service_running': self.running
        }
    
    async def shutdown(self):
        """Shutdown the publishing service."""
        self.running = False
        self.logger.info("🔄 Signal Publishing Service shutdown complete")


# Convenience function for integration with orchestrator
async def publish_validated_signal(
    config_id: str,
    user_id: str,
    signal_data: Dict,
    decision_result: Dict
) -> bool:
    """
    Convenience function to publish a validated signal.
    
    This can be called directly by the orchestrator or via a queue system.
    """
    service = SignalPublishingService()
    return await service.publish_validated_signal(
        config_id, user_id, signal_data, decision_result
    )


# Orchestrator integration function
async def publish_signal_to_telegram(
    config_id: str,
    user_id: str, 
    signal_data: Dict,
    decision_result: Dict
) -> bool:
    """Publish signal to telegram - called by orchestrator after signal validation."""
    try:
        # Get user's bot token from their config
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT config_data 
                    FROM configurations 
                    WHERE config_id = %s
                """, (config_id,))
                
                result = cur.fetchone()
                if not result:
                    logger.warning(f"Config {config_id} not found")
                    return False
                
                config_data = result[0]
                
                # Handle nested config_data structure like in config_service
                if "config_data" in config_data:
                    inner_config = config_data["config_data"] 
                    telegram_config = inner_config.get('telegram_integration', {})
                else:
                    telegram_config = config_data.get('telegram_integration', {})
                
                publisher_config = telegram_config.get('publisher', {})
                bot_token = publisher_config.get('bot_token')
                
                if not bot_token:
                    logger.warning(f"No bot token configured for config {config_id}")
                    logger.debug(f"Config structure: telegram_integration keys = {list(telegram_config.keys()) if telegram_config else 'None'}")
                    logger.debug(f"Publisher config keys = {list(publisher_config.keys()) if publisher_config else 'None'}")
                    return False
        
        # Create a temporary service instance with user's bot token
        service = SignalPublishingService()
        service.bot_token = bot_token  # Override with user's token
        service.telegram_bot = TelegramBot(bot_token)  # Create new bot with user's token
        
        return await service.publish_validated_signal(
            config_id, user_id, signal_data, decision_result
        )
        
    except Exception as e:
        logger.error(f"Failed to publish signal to telegram: {e}")
        return False


async def main():
    """Main entry point for the signal publishing service."""
    service = SignalPublishingService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await service.shutdown()


if __name__ == "__main__":
    # Set up logging for the service
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the service
    asyncio.run(main())