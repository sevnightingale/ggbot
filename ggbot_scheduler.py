"""
GGBot Scheduler — autonomous bot execution, decoupled from API.

This process owns APScheduler and all bot cycle execution.
It polls the database every 10 seconds to detect state changes
(start, stop, timeframe change, delete) and reconciles scheduler jobs.

The API process (ggbot.py) only writes state to the database.
This process reads state and acts on it.

Run with: python ggbot_scheduler.py
PM2:      pm2 start ecosystem.config.js --only ggbot-scheduler
"""

import asyncio
import signal
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from core.orchestrator.orchestrator import GGBotOrchestrator
from core.scheduler.bot_runner import reconcile_loop, init as init_runner
from core.common.logger import logger


async def main():
    """Start scheduler, initialize orchestrator, enter reconciliation loop."""
    logger.info("Starting GGBot Scheduler process")

    scheduler = AsyncIOScheduler()
    orchestrator = GGBotOrchestrator()

    # Initialize bot_runner module with scheduler/orchestrator references
    init_runner(scheduler, orchestrator)

    scheduler.start()
    logger.info("APScheduler started")

    # Schedule daily Stripe meter reporting (midnight UTC)
    try:
        from billing.stripe_meter_reporter import run_daily_report

        scheduler.add_job(
            func=run_daily_report,
            trigger=CronTrigger(hour=0, minute=0),
            id="stripe_meter_reporting",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
        )
        logger.info("Stripe meter reporting scheduled (daily at midnight UTC)")
    except ImportError:
        logger.warning("billing.stripe_meter_reporter not available, skipping")

    logger.info("Entering reconciliation loop (10s interval)")
    await reconcile_loop(scheduler, orchestrator, interval=10)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        sys.exit(0)
