#!/usr/bin/env python3
"""
Backfill Redis usage counters from activities table.

Run once after deploying the Redis counter feature to populate counters
with existing data from the current billing period.

Usage:
    python scripts/backfill_usage_counters.py [--dry-run]

Options:
    --dry-run    Show what would be set without actually writing to Redis

Example:
    # First, do a dry run to see what will be backfilled
    python scripts/backfill_usage_counters.py --dry-run

    # Then run for real
    python scripts/backfill_usage_counters.py
"""
import os
import sys
import argparse
import redis
from datetime import datetime
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.common.db import get_db_connection
from core.common.logger import logger


def backfill_counters(dry_run: bool = False) -> dict:
    """
    Backfill Redis usage counters from activities table.

    Args:
        dry_run: If True, print what would be set without writing

    Returns:
        Stats dict with counts of users/configs backfilled
    """
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_client = redis.from_url(redis_url)

    current_period = datetime.utcnow().strftime("%Y-%m")

    stats = {
        "period": current_period,
        "users_backfilled": 0,
        "configs_backfilled": 0,
        "daily_keys_set": 0,
        "total_usage_usd": Decimal("0"),
        "dry_run": dry_run
    }

    logger.info(f"Starting backfill for period {current_period} (dry_run={dry_run})")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # 1. Backfill user-level usage for current period
            cur.execute("""
                SELECT user_id, SUM(platform_cost_usd) as total
                FROM activities
                WHERE created_at >= date_trunc('month', NOW() AT TIME ZONE 'UTC')
                AND platform_cost_usd IS NOT NULL
                GROUP BY user_id
                HAVING SUM(platform_cost_usd) > 0
            """)

            for row in cur.fetchall():
                user_id, total = row
                if total is None:
                    continue

                key = f"usage:user:{user_id}:{current_period}"
                total_float = float(total)

                if dry_run:
                    print(f"[DRY RUN] SET {key} = {total_float:.6f}")
                else:
                    redis_client.set(key, str(total_float))
                    logger.info(f"Set {key} = ${total_float:.4f}")

                stats["users_backfilled"] += 1
                stats["total_usage_usd"] += Decimal(str(total))

            # 2. Backfill config-level monthly usage
            cur.execute("""
                SELECT config_id, SUM(platform_cost_usd) as total
                FROM activities
                WHERE created_at >= date_trunc('month', NOW() AT TIME ZONE 'UTC')
                AND platform_cost_usd IS NOT NULL
                AND config_id IS NOT NULL
                GROUP BY config_id
                HAVING SUM(platform_cost_usd) > 0
            """)

            for row in cur.fetchall():
                config_id, total = row
                if total is None:
                    continue

                key = f"usage:config:{config_id}:{current_period}"
                total_float = float(total)

                if dry_run:
                    print(f"[DRY RUN] SET {key} = {total_float:.6f}")
                else:
                    redis_client.set(key, str(total_float))
                    logger.info(f"Set {key} = ${total_float:.4f}")

                stats["configs_backfilled"] += 1

            # 3. Backfill config-level daily usage (with 90-day TTL)
            cur.execute("""
                SELECT config_id,
                       DATE(created_at AT TIME ZONE 'UTC') as day,
                       SUM(platform_cost_usd) as daily_total
                FROM activities
                WHERE created_at >= date_trunc('month', NOW() AT TIME ZONE 'UTC')
                AND platform_cost_usd IS NOT NULL
                AND config_id IS NOT NULL
                GROUP BY config_id, DATE(created_at AT TIME ZONE 'UTC')
                HAVING SUM(platform_cost_usd) > 0
                ORDER BY config_id, day
            """)

            for row in cur.fetchall():
                config_id, day, daily_total = row
                if daily_total is None:
                    continue

                day_str = day.strftime("%Y-%m-%d")
                key = f"usage:config:{config_id}:{day_str}"
                total_float = float(daily_total)

                if dry_run:
                    print(f"[DRY RUN] SETEX {key} = {total_float:.6f} (TTL: 90 days)")
                else:
                    redis_client.setex(key, 90 * 24 * 3600, str(total_float))

                stats["daily_keys_set"] += 1

    # Log summary
    summary = f"""
Backfill Complete:
  Period: {stats['period']}
  Users backfilled: {stats['users_backfilled']}
  Configs backfilled: {stats['configs_backfilled']}
  Daily keys set: {stats['daily_keys_set']}
  Total usage: ${float(stats['total_usage_usd']):.2f}
  Dry run: {stats['dry_run']}
"""

    if dry_run:
        print(summary)
    else:
        logger.info(summary)

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Backfill Redis usage counters from activities table"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be set without writing to Redis"
    )

    args = parser.parse_args()

    try:
        stats = backfill_counters(dry_run=args.dry_run)

        if not args.dry_run:
            print(f"Successfully backfilled {stats['users_backfilled']} users and {stats['configs_backfilled']} configs")

        return 0

    except Exception as e:
        logger.error(f"Backfill failed: {e}")
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
