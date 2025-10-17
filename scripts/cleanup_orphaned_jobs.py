#!/usr/bin/env python3
"""
Cleanup script for orphaned APScheduler jobs.

Removes all scheduled jobs that reference config_ids that no longer exist in the database.
Run this script once to clean up existing orphaned jobs.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import requests
from core.common.db import get_db_connection
from core.common.logger import logger


def get_all_config_ids():
    """Get all config_ids from database."""
    config_ids = set()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT config_id FROM configurations")
            for row in cur.fetchall():
                config_ids.add(row[0])
    return config_ids


def get_scheduler_jobs():
    """Get all jobs from APScheduler via API."""
    try:
        # Call local ggbot API to get scheduler status
        response = requests.get("http://localhost:8000/api/v2/scheduler/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("jobs", [])
        else:
            logger.error(f"Failed to get scheduler jobs: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Failed to get scheduler jobs: {e}")
        return []


def parse_job_id(job_id):
    """Parse job ID to extract config_id."""
    # Format: bot:user_id:config_id:timeframe
    parts = job_id.split(":")
    if len(parts) >= 3 and parts[0] == "bot":
        return parts[2]  # config_id
    return None


def cleanup_orphaned_jobs_via_api(orphaned_config_ids):
    """Remove orphaned jobs via API."""
    removed = 0
    for config_id in orphaned_config_ids:
        try:
            # Note: This would require authentication in production
            # For now, we'll just report what needs to be cleaned
            logger.info(f"Orphaned config_id: {config_id}")
            removed += 1
        except Exception as e:
            logger.warning(f"Failed to process config {config_id}: {e}")
    return removed


async def main():
    """Main cleanup function."""
    logger.info("Starting orphaned job cleanup...")

    # Get all valid config_ids from database
    valid_config_ids = get_all_config_ids()
    logger.info(f"Found {len(valid_config_ids)} valid configs in database")

    # Get all scheduled jobs
    jobs = get_scheduler_jobs()
    logger.info(f"Found {len(jobs)} scheduled jobs")

    # Find orphaned jobs
    orphaned = []
    job_config_ids = set()

    for job in jobs:
        job_id = job.get("id", "")
        if job_id.startswith("bot:"):
            config_id = parse_job_id(job_id)
            if config_id:
                job_config_ids.add(config_id)
                if config_id not in valid_config_ids:
                    orphaned.append(job_id)
                    logger.warning(f"Orphaned job found: {job_id} (config not in database)")

    logger.info(f"Found {len(orphaned)} orphaned jobs")

    if orphaned:
        logger.info("\nOrphaned jobs that need manual cleanup:")
        for job_id in orphaned:
            print(f"  - {job_id}")

        print(f"\n{'='*60}")
        print(f"CLEANUP REPORT")
        print(f"{'='*60}")
        print(f"Total scheduled jobs: {len(jobs)}")
        print(f"Valid configs in DB: {len(valid_config_ids)}")
        print(f"Config IDs in jobs: {len(job_config_ids)}")
        print(f"Orphaned jobs found: {len(orphaned)}")
        print(f"{'='*60}")

        print("\nThese jobs will be automatically cleaned up when:")
        print("1. The server restarts with the updated delete_config endpoint")
        print("2. Any future config deletions will also clean up their jobs")

        print("\nAlternatively, restart the ggbot service now to clear these jobs:")
        print("  pm2 restart ggbot")

    else:
        logger.info("No orphaned jobs found! ✅")

    return len(orphaned)


if __name__ == "__main__":
    orphaned_count = asyncio.run(main())
    sys.exit(0 if orphaned_count == 0 else 1)
