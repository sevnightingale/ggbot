"""
Bot Runner — scheduler job functions and reconciliation loop.

Extracted from ggbot.py so the scheduler process can run bot cycles
independently of the API process.
"""

import asyncio
import os
import uuid
from typing import Dict, Any, Optional

import redis.asyncio as redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.common.db import get_db_connection
from core.common.logger import logger
from core.scheduler.utils import (
    cron_for,
    last_closed_close_ts,
    get_misfire_grace_time,
    format_redis_idempotency_key,
    get_redis_ttl_for_timeframe,
    extract_timeframe_from_config,
)

# Limit concurrent bot executions to prevent resource exhaustion
execution_semaphore = asyncio.Semaphore(50)

# These are set by the scheduler entry point after initialization
_scheduler: Optional[AsyncIOScheduler] = None
_orchestrator = None  # GGBotOrchestrator instance


def init(scheduler: AsyncIOScheduler, orchestrator) -> None:
    """Initialize module-level references. Called once at startup."""
    global _scheduler, _orchestrator
    _scheduler = scheduler
    _orchestrator = orchestrator


async def run_once(user_id: str, config_id: str, timeframe: str):
    """
    Job function executed by APScheduler for each bot.
    Implements Redis idempotency and calls the orchestrator.
    """
    # CHECK STATE BEFORE EXECUTING — prevents inactive bots from running.
    # This catches bots paused by UsageMonitor (credit exhaustion) or other means.
    from core.services.config_service import config_service
    state = await config_service.get_bot_state(config_id, user_id)
    if state != 'active':
        logger.info(f"Skipping execution for {config_id} - state is '{state}', removing scheduler job")
        remove_bot_job(user_id, config_id, timeframe)
        return

    close_ts = last_closed_close_ts(timeframe)
    key = format_redis_idempotency_key(user_id, config_id, timeframe, close_ts)

    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_client = redis.from_url(redis_url, decode_responses=True)

    async with execution_semaphore:
        try:
            ttl = get_redis_ttl_for_timeframe(timeframe)
            if not await redis_client.set(key, "executing", ex=ttl, nx=True):
                logger.info(f"Skipping execution for {user_id}:{config_id}:{timeframe}:{close_ts} - already executed")
                return

            try:
                run_id = uuid.uuid4().hex[:6]
                result = await _orchestrator.run_autonomous_cycle(config_id, user_id, run_id=run_id)

                await redis_client.set(key, "completed", ex=ttl)
                logger.bind(run_id=run_id, config_id=config_id).info(
                    f"Completed execution for {timeframe}:{close_ts} in {result.execution_time_ms}ms"
                )

            except Exception as e:
                logger.error(f"Execution failed for {user_id}:{config_id}:{timeframe}:{close_ts}: {e}")

        finally:
            await redis_client.aclose()


def add_bot_job(scheduler: AsyncIOScheduler, user_id: str, config_id: str, timeframe: str, jitter: int = 30):
    """
    Add a scheduled job for a bot configuration.

    Args:
        scheduler: APScheduler instance
        user_id: User ID
        config_id: Configuration ID
        timeframe: Trading timeframe
        jitter: Random jitter in seconds (default 30, spread load)
    """
    trigger = cron_for(timeframe)
    job_id = f"bot:{user_id}:{config_id}:{timeframe}"
    misfire_grace = get_misfire_grace_time(timeframe)

    scheduler.add_job(
        func=run_once,
        trigger=trigger,
        id=job_id,
        args=[user_id, config_id, timeframe],
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=misfire_grace,
        jitter=jitter,
    )

    logger.info(f"Added scheduler job {job_id} with {timeframe} cadence")


def remove_bot_job(user_id: str, config_id: str, timeframe: str):
    """Remove a scheduled job for a bot configuration."""
    if _scheduler is None:
        logger.warning("Scheduler not initialized, cannot remove job")
        return False
    job_id = f"bot:{user_id}:{config_id}:{timeframe}"
    try:
        job = _scheduler.get_job(job_id)
        if job:
            _scheduler.remove_job(job_id)
            logger.info(f"Removed scheduler job {job_id}")
            return True
        else:
            logger.info(f"Job {job_id} was already removed or never existed")
            return True
    except Exception as e:
        logger.warning(f"Failed to remove job {job_id}: {e}")
        return False


async def reconcile_loop(scheduler: AsyncIOScheduler, orchestrator, interval: int = 10):
    """
    Continuously sync scheduler jobs with DB state. Runs forever.

    Every `interval` seconds:
    1. Query DB for all active scheduled_trading bots
    2. Compare with current APScheduler jobs
    3. Add missing jobs (bots started via API)
    4. Remove extra jobs (bots stopped/deleted via API, permission lost)

    This handles ALL edge cases: start, stop, timeframe change, delete, crash recovery.
    """
    while True:
        try:
            # Get active scheduled_trading bots from DB
            db_active = set()  # {(user_id, config_id, timeframe)}
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT user_id, config_id, config_type, config_data
                        FROM configurations
                        WHERE state = 'active'
                          AND (config_type = 'scheduled_trading' OR config_type IS NULL)
                    """)
                    for row in cur.fetchall():
                        user_id, config_id, config_type, config_data = row
                        tf = extract_timeframe_from_config(config_data)
                        if tf and tf != 'signal_driven':
                            db_active.add((str(user_id), str(config_id), tf))

            # Get current scheduler jobs
            sched_active = set()
            for job in scheduler.get_jobs():
                if job.id.startswith("bot:"):
                    parts = job.id.split(":")
                    if len(parts) == 4:
                        sched_active.add((parts[1], parts[2], parts[3]))

            # Add missing (new bots started via API)
            for user_id, config_id, tf in (db_active - sched_active):
                add_bot_job(scheduler, user_id, config_id, tf)

            # Remove extra (bots stopped via API, deleted, or permission lost)
            for user_id, config_id, tf in (sched_active - db_active):
                job_id = f"bot:{user_id}:{config_id}:{tf}"
                try:
                    scheduler.remove_job(job_id)
                    logger.info(f"Reconcile: removed orphaned job {job_id}")
                except Exception as e:
                    logger.warning(f"Reconcile: failed to remove job {job_id}: {e}")

        except Exception as e:
            logger.error(f"Reconciliation loop error: {e}")

        await asyncio.sleep(interval)
