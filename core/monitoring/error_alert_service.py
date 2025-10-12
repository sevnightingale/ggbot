#!/usr/bin/env python3
"""
Error Alert Service

Monitors logs/ggbot.log for ERROR and CRITICAL entries and sends
real-time Telegram notifications to a dedicated error channel.
"""

import asyncio
import aiohttp
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from collections import deque
from typing import Optional

# Add project root to path
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from core.common.logger import logger


class TelegramAlertBot:
    """Lightweight Telegram bot for error alerts."""

    def __init__(self, bot_token: str, channel_id: str):
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.api_base = f"https://api.telegram.org/bot{bot_token}"
        self.logger = logger.bind(component='telegram_alert')

    async def send_alert(self, message: str) -> bool:
        """Send alert message to error channel."""
        try:
            payload = {
                "chat_id": self.channel_id,
                "text": message,
                "disable_web_page_preview": True,
                "parse_mode": "HTML"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/sendMessage",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            return True
                        else:
                            self.logger.error(f"Telegram API error: {result.get('description')}")
                            return False
                    else:
                        error_text = await response.text()
                        self.logger.error(f"HTTP {response.status}: {error_text}")
                        return False

        except Exception as e:
            self.logger.error(f"Failed to send telegram alert: {e}")
            return False

    async def test_connection(self) -> bool:
        """Test bot connection."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base}/getMe",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            bot_info = result.get('result', {})
                            self.logger.info(
                                f"Alert bot connected: @{bot_info.get('username')} "
                                f"→ channel {self.channel_id}"
                            )
                            return True
            return False
        except Exception as e:
            self.logger.error(f"Bot connection test failed: {e}")
            return False


class ErrorAlertService:
    """Monitors log file and sends error alerts."""

    def __init__(self):
        # Configuration
        self.bot_token = os.getenv('GG_FILTER_TOKEN')
        self.channel_id = os.getenv('ERROR_ALERT_CHANNEL_ID')

        if not self.bot_token:
            raise ValueError("GG_FILTER_TOKEN environment variable required")
        if not self.channel_id:
            raise ValueError("ERROR_ALERT_CHANNEL_ID environment variable required")

        # Initialize bot
        self.telegram_bot = TelegramAlertBot(self.bot_token, self.channel_id)

        # Log file configuration
        self.log_file = PROJECT_DIR / "logs" / "ggbot.log"

        # Rate limiting: track last alert time per error pattern
        self.last_alert_time = {}
        self.alert_cooldown = 60  # seconds between duplicate alerts

        # Track recently seen errors to avoid duplicates
        self.recent_errors = deque(maxlen=100)

        self.logger = logger.bind(service='error_alerts')

    async def start(self):
        """Start monitoring log file."""
        self.logger.info("🚨 Error Alert Service starting...")

        # Test Telegram connection
        if not await self.telegram_bot.test_connection():
            self.logger.error("Failed to connect to Telegram. Exiting.")
            return

        # Send startup notification
        await self.telegram_bot.send_alert(
            "🚨 <b>Error Alert Service Started</b>\n\n"
            f"Monitoring: <code>{self.log_file}</code>\n"
            f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )

        # Start monitoring
        await self._monitor_log_file()

    async def _monitor_log_file(self):
        """Tail log file and process error lines using subprocess."""
        import subprocess

        self.logger.info(f"Monitoring {self.log_file}")

        # Ensure log file exists
        while not self.log_file.exists():
            self.logger.warning(f"Log file not found: {self.log_file}")
            await asyncio.sleep(5)

        self.logger.info(f"📍 Starting tail -F to monitor log file")

        # Use tail -F to follow the log file (handles rotation)
        process = subprocess.Popen(
            ['tail', '-F', '-n', '0', str(self.log_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        try:
            while True:
                line = process.stdout.readline()

                if line:
                    # Process line if it contains ERROR or CRITICAL
                    # Skip our own monitoring logs to prevent feedback loop
                    skip_patterns = [
                        '📥 New error', '✉️  Sending alert', '✅ Alert sent', '⏱️  Skipping',
                        '❌ Failed to send', 'error_alert_service', '__main__:send_alert',
                        '__main__:_process_error_line', '__main__:test_connection'
                    ]
                    if ('ERROR' in line or 'CRITICAL' in line) and not any(pattern in line for pattern in skip_patterns):
                        self.logger.info(f"📥 New error detected, processing...")
                        await self._process_error_line(line.strip())
                else:
                    # Check if process is still running
                    if process.poll() is not None:
                        self.logger.error("tail process died, restarting...")
                        break

                    await asyncio.sleep(0.1)
        finally:
            process.terminate()
            process.wait()

    async def _process_error_line(self, line: str):
        """Process an error log line and send alert if needed."""
        try:
            # Skip if we've seen this exact error recently
            if line in self.recent_errors:
                self.logger.debug("Skipping - already in recent_errors")
                return

            # Parse log line format: YYYY-MM-DD HH:MM:SS | LEVEL | module:function:line - message
            parts = line.split(' | ', maxsplit=2)
            if len(parts) < 3:
                self.logger.warning(f"Skipping - invalid format (parts={len(parts)})")
                return

            timestamp = parts[0].strip()
            level = parts[1].strip()
            location_and_message = parts[2].strip()

            # Split location and message by " - "
            if ' - ' in location_and_message:
                location, message = location_and_message.split(' - ', maxsplit=1)
            else:
                location = location_and_message
                message = ""

            self.logger.debug(f"Processing {level} from {location[:30]}")

            # Extract error pattern for rate limiting (first 50 chars of message)
            error_pattern = message[:50]

            # Check rate limiting
            current_time = time.time()
            last_time = self.last_alert_time.get(error_pattern, 0)
            time_since_last = current_time - last_time

            if time_since_last < self.alert_cooldown:
                self.logger.info(f"⏱️  Skipping - cooldown ({time_since_last:.0f}s < {self.alert_cooldown}s)")
                return

            self.logger.info(f"✉️  Sending alert to Telegram...")

            # Format alert message
            alert_message = self._format_alert(timestamp, level, location, message)

            # Send alert
            success = await self.telegram_bot.send_alert(alert_message)

            if success:
                # Update rate limiting
                self.last_alert_time[error_pattern] = current_time
                self.recent_errors.append(line)
                self.logger.info(f"✅ Alert sent: {level} in {location}")
            else:
                self.logger.error(f"❌ Failed to send alert")

        except Exception as e:
            self.logger.error(f"Failed to process error line: {e}", exc_info=True)

    def _format_alert(self, timestamp: str, level: str, location: str, message: str) -> str:
        """Format error alert message for Telegram."""
        # Determine emoji based on level
        emoji = "🔴" if level == "CRITICAL" else "🟠"

        # Truncate message if too long
        max_message_length = 500
        if len(message) > max_message_length:
            message = message[:max_message_length] + "..."

        # HTML escape for Telegram
        def html_escape(text):
            return (text
                    .replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;'))

        location = html_escape(location)
        message = html_escape(message)

        alert = (
            f"{emoji} <b>{level}</b>\n\n"
            f"<b>Time:</b> {timestamp}\n"
            f"<b>Location:</b> <code>{location}</code>\n\n"
            f"<b>Message:</b>\n{message}"
        )

        return alert


async def main():
    """Main entry point."""
    try:
        service = ErrorAlertService()
        await service.start()
    except KeyboardInterrupt:
        logger.info("Error Alert Service stopped by user")
    except Exception as e:
        logger.error(f"Error Alert Service crashed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
