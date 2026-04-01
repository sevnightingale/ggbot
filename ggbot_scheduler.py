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
import concurrent.futures
import signal
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from core.orchestrator.orchestrator import GGBotOrchestrator
from core.scheduler.bot_runner import reconcile_loop, init as init_runner
from core.common.logger import logger


async def main():
    """Start scheduler, initialize orchestrator, enter reconciliation loop."""
    # Dedicated thread pool for asyncio.to_thread() DB calls.
    # Prevents sync psycopg2 queries from blocking the event loop when
    # 30+ bot coroutines fire simultaneously at candle boundaries.
    loop = asyncio.get_event_loop()
    loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=32))

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

    # Schedule daily account_snapshots retention (3am UTC, low traffic)
    try:
        from core.monitoring.snapshot_retention import run_snapshot_retention

        scheduler.add_job(
            func=run_snapshot_retention,
            trigger=CronTrigger(hour=3, minute=0),
            id="snapshot_retention",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
        )
        logger.info("Snapshot retention scheduled (daily at 3am UTC)")
    except ImportError:
        logger.warning("snapshot_retention not available, skipping")

    # Dojo match lifecycle processor (start, complete, expire — every 5 minutes)
    try:
        from core.arena.matches import process_dojo_matches

        scheduler.add_job(
            func=process_dojo_matches,
            trigger=IntervalTrigger(minutes=5),
            id="dojo_match_lifecycle",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )
        logger.info("Dojo match lifecycle scheduled (every 5 min)")
    except ImportError:
        logger.warning("core.arena.matches not available, skipping Dojo lifecycle")

    # Weekly rolling Elo update (Sundays at midnight UTC)
    try:
        from core.arena.elo import weekly_rolling_update

        scheduler.add_job(
            func=weekly_rolling_update,
            trigger=CronTrigger(day_of_week='sun', hour=0, minute=0),
            id="weekly_rolling_elo",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
        )
        logger.info("Weekly rolling Elo scheduled (Sundays at midnight UTC)")
    except ImportError:
        logger.warning("core.arena.elo not available, skipping weekly Elo")

    logger.info("Entering reconciliation loop (10s interval)")
    await reconcile_loop(scheduler, orchestrator, interval=10)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        sys.exit(0)
