#!/usr/bin/env python3
"""
X Bot for @ggbots_ai
Autonomous X (Twitter) bot running as separate PM2 service.
Posts platform status updates and manages scheduled content.
"""

import asyncio
import os
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from core.common.logger import logger
from x_bot.utils.x_client import XClient
from x_bot.schedulers import platform_status

load_dotenv()


class XBot:
    """
    Main X bot service with APScheduler for scheduled tweets.
    """

    def __init__(self):
        self.logger = logger.bind(service="x-bot")
        self.x_client = XClient()
        self.scheduler = AsyncIOScheduler()
        self.enabled = os.getenv('X_BOT_ENABLED', 'true').lower() == 'true'

    async def start(self):
        """Initialize and start the X bot service."""
        if not self.enabled:
            self.logger.warning("X bot disabled via X_BOT_ENABLED env var")
            return

        self.logger.info("=" * 60)
        self.logger.info("Starting X Bot for @ggbots_ai")
        self.logger.info("=" * 60)

        # Test authentication
        if not self.x_client.test_auth():
            self.logger.error("X API authentication failed - stopping service")
            return

        # Register scheduled jobs
        self._register_jobs()

        # Start scheduler
        self.scheduler.start()
        self.logger.info("X bot scheduler started successfully")
        self.logger.info(f"Active jobs: {len(self.scheduler.get_jobs())}")

        # List scheduled jobs
        for job in self.scheduler.get_jobs():
            self.logger.info(f"  - {job.name} (next run: {job.next_run_time})")

        # Keep running
        try:
            self.logger.info("X bot running... Press Ctrl+C to stop")
            await asyncio.Event().wait()  # Run forever
        except KeyboardInterrupt:
            self.logger.info("Shutting down X bot")
            self.scheduler.shutdown()

    def _register_jobs(self):
        """Register all scheduled jobs with APScheduler."""

        # Daily platform status - 9:00 AM UTC
        self.scheduler.add_job(
            platform_status.post_platform_status,
            trigger=CronTrigger(hour=9, minute=0),
            id='platform_status',
            name='Daily platform status tweet',
            kwargs={'x_client': self.x_client}
        )

        self.logger.info("Registered 1 scheduled job")

        # TODO: Add more schedulers here as we build them
        # - Trade announcements (every minute polling)
        # - Weekly summary (Sunday 8pm)
        # - Targeted replies (3x per day)


if __name__ == "__main__":
    bot = XBot()
    asyncio.run(bot.start())
