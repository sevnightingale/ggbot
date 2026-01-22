#!/usr/bin/env python3
"""
Telegram Bot Command Handler for @ggFilter_Bot

A PM2-managed service that handles bot commands:
- /start - Welcome message with setup instructions
- /chatid - Returns the current chat/channel/group ID
- /help - Shows available commands

Uses long polling (getUpdates) to receive commands.
"""

import asyncio
import aiohttp
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add project root to path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from core.common.logger import logger


class TelegramBotHandler:
    """Handles incoming Telegram bot commands via long polling."""

    def __init__(self):
        self.bot_token = os.getenv('GG_FILTER_TOKEN')
        if not self.bot_token:
            raise ValueError("GG_FILTER_TOKEN environment variable required")

        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"
        self.logger = logger.bind(service='telegram_bot_handler')
        self.running = False
        self.last_update_id = 0

        # Rate limiting
        self.poll_timeout = 30  # Long polling timeout in seconds
        self.error_backoff = 5  # Seconds to wait after error
        self.max_error_backoff = 60  # Maximum backoff time

    async def start(self):
        """Start the bot command handler with long polling."""
        self.logger.info("🤖 Starting Telegram Bot Handler (@ggFilter_Bot)")

        # Test connection
        if not await self._test_connection():
            self.logger.error("Failed to connect to Telegram API. Exiting.")
            return

        self.running = True
        error_count = 0

        while self.running:
            try:
                updates = await self._get_updates()

                if updates:
                    for update in updates:
                        await self._process_update(update)
                        # Track last processed update
                        self.last_update_id = update.get('update_id', 0)

                # Reset error count on successful poll
                error_count = 0

            except asyncio.CancelledError:
                self.logger.info("Bot handler cancelled")
                break
            except Exception as e:
                error_count += 1
                backoff = min(self.error_backoff * error_count, self.max_error_backoff)
                self.logger.error(f"Error in poll loop: {e}. Waiting {backoff}s before retry.")
                await asyncio.sleep(backoff)

        self.logger.info("🔄 Telegram Bot Handler stopped")

    async def _test_connection(self) -> bool:
        """Test bot connection and log bot info."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base}/getMe",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            bot_info = result.get('result', {})
                            self.logger.info(
                                f"✅ Connected as @{bot_info.get('username')} "
                                f"(ID: {bot_info.get('id')})"
                            )
                            return True
            return False
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    async def _get_updates(self) -> list:
        """Get updates from Telegram using long polling."""
        try:
            params = {
                'offset': self.last_update_id + 1,
                'timeout': self.poll_timeout,
                'allowed_updates': ['message']  # Only receive message updates
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base}/getUpdates",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.poll_timeout + 10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            return result.get('result', [])
                    else:
                        error_text = await response.text()
                        self.logger.error(f"getUpdates failed: {response.status} - {error_text}")
            return []
        except asyncio.TimeoutError:
            # Normal timeout from long polling, no updates available
            return []
        except Exception as e:
            self.logger.error(f"Error getting updates: {e}")
            raise

    async def _process_update(self, update: Dict[str, Any]):
        """Process a single update from Telegram."""
        try:
            message = update.get('message')
            if not message:
                return

            text = message.get('text', '')
            chat = message.get('chat', {})
            chat_id = chat.get('id')
            chat_type = chat.get('type')  # 'private', 'group', 'supergroup', 'channel'
            chat_title = chat.get('title') or chat.get('username') or 'Private Chat'

            # Extract command (handle @mentions like /chatid@ggFilter_Bot)
            command = text.split()[0].split('@')[0].lower() if text.startswith('/') else None

            if not command:
                return

            self.logger.info(f"📨 Command: {command} from {chat_type} '{chat_title}' (ID: {chat_id})")

            # Route to command handlers
            if command == '/start':
                await self._handle_start(chat_id, chat_type)
            elif command == '/chatid':
                await self._handle_chatid(chat_id, chat_type, chat_title)
            elif command == '/help':
                await self._handle_help(chat_id)
            else:
                # Unknown command - ignore silently
                pass

        except Exception as e:
            self.logger.error(f"Error processing update: {e}")

    async def _handle_start(self, chat_id: int, chat_type: str):
        """Handle /start command."""
        if chat_type == 'private':
            message = (
                "👋 Welcome to ggbots Signal Publisher!\n\n"
                "I can publish your AI trading signals to your Telegram channels.\n\n"
                "📋 Setup Instructions:\n"
                "1. Add me to your channel or group\n"
                "2. Make me an admin with 'Post Messages' permission\n"
                "3. Send /chatid in the channel to get the ID\n"
                "4. Enter the ID in your ggbots.ai bot config\n\n"
                "Commands:\n"
                "/chatid - Get this chat's ID\n"
                "/help - Show this message\n\n"
                "🌐 https://ggbots.ai"
            )
        else:
            message = (
                "👋 ggbots Signal Publisher is ready!\n\n"
                "Use /chatid to get this channel's ID for your bot config.\n\n"
                "🌐 https://ggbots.ai"
            )

        await self._send_message(chat_id, message)

    async def _handle_chatid(self, chat_id: int, chat_type: str, chat_title: str):
        """Handle /chatid command."""
        # Format chat type for display
        type_display = {
            'private': 'Private Chat',
            'group': 'Group',
            'supergroup': 'Supergroup',
            'channel': 'Channel'
        }.get(chat_type, chat_type)

        message = (
            f"📍 Chat ID for \"{chat_title}\"\n\n"
            f"Type: {type_display}\n"
            f"ID: {chat_id}\n\n"
            f"Copy this ID to your ggbots.ai bot config in the Telegram Publishing section.\n\n"
            f"🌐 https://ggbots.ai"
        )

        await self._send_message(chat_id, message)
        self.logger.info(f"✅ Sent chat ID {chat_id} for '{chat_title}'")

    async def _handle_help(self, chat_id: int):
        """Handle /help command."""
        message = (
            "🤖 ggbots Signal Publisher\n\n"
            "I publish your AI trading bot's signals to Telegram.\n\n"
            "Commands:\n"
            "/start - Setup instructions\n"
            "/chatid - Get this chat's ID\n"
            "/help - Show this message\n\n"
            "Setup:\n"
            "1. Add me to your channel/group\n"
            "2. Make me admin (Post Messages)\n"
            "3. Use /chatid to get the ID\n"
            "4. Enter ID at ggbots.ai\n\n"
            "🌐 https://ggbots.ai"
        )

        await self._send_message(chat_id, message)

    async def _send_message(self, chat_id: int, text: str) -> bool:
        """Send a message to a chat."""
        try:
            payload = {
                'chat_id': chat_id,
                'text': text,
                'disable_web_page_preview': True
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/sendMessage",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('ok', False)
                    else:
                        error_text = await response.text()
                        self.logger.error(f"sendMessage failed: {response.status} - {error_text}")
                        return False
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False

    def stop(self):
        """Stop the bot handler."""
        self.running = False


async def main():
    """Main entry point for the bot handler service."""
    handler = TelegramBotHandler()

    try:
        await handler.start()
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        handler.stop()
        logger.info("🔄 Telegram Bot Handler shutdown complete")


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(main())
