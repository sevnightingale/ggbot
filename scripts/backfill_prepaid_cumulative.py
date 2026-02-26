#!/usr/bin/env python3
"""
Backfill cumulative Redis usage keys for prepaid users.

Reads all-time usage from the activities table and SETs the
usage:prepaid:{user_id} Redis key for each prepaid user.

This must run BEFORE switching code to read from the cumulative key.
Safe to re-run (idempotent — uses SET, not INCR).

Usage:
    python scripts/backfill_prepaid_cumulative.py [--dry-run]

Options:
    --dry-run    Show what would be set without actually writing to Redis
"""
import os
import sys
import argparse
import redis
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.common.db import get_db_connection
from core.common.logger import logger


def backfill_prepaid_cumulative(dry_run: bool = False) -> dict:
    """
    Backfill cumulative Redis usage keys for prepaid users.

    1. Find all prepaid users from user_profiles
    2. Sum their all-time platform_cost_usd from activities
    3. SET usage:prepaid:{user_id} in Redis

    Args:
        dry_run: If True, print what would be set without writing

    Returns:
        Stats dict
    """
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_client = redis.from_url(redis_url, decode_responses=True)

    stats = {
        "users_found": 0,
        "users_with_usage": 0,
        "total_usage_usd": Decimal("0"),
        "dry_run": dry_run
    }

    logger.info(f"Starting prepaid cumulative backfill (dry_run={dry_run})")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # 1. Get all prepaid users
            cur.execute("""
                SELECT user_id
                FROM user_profiles
                WHERE subscription_tier IN ('prepaid', 'ggbase')
            """)
            prepaid_users = [row[0] for row in cur.fetchall()]
            stats["users_found"] = len(prepaid_users)

            logger.info(f"Found {len(prepaid_users)} prepaid users")

            # 2. For each, get all-time usage from activities
            for user_id in prepaid_users:
                cur.execute("""
                    SELECT COALESCE(SUM(platform_cost_usd), 0)
                    FROM activities
                    WHERE user_id = %s
                    AND platform_cost_usd > 0
                """, (user_id,))
                result = cur.fetchone()
                total_usage = Decimal(str(result[0])) if result and result[0] else Decimal("0")

                # Check existing Redis value for comparison
                redis_key = f"usage:prepaid:{user_id}"
                existing_raw = redis_client.get(redis_key)
                existing = Decimal(existing_raw) if existing_raw else Decimal("0")

                if total_usage > 0:
                    stats["users_with_usage"] += 1
                    stats["total_usage_usd"] += total_usage

                if dry_run:
                    print(f"[DRY RUN] SET {redis_key} = {float(total_usage):.6f}"
                          f"  (existing: {float(existing):.6f}, delta: {float(total_usage - existing):.6f})"
                          f"  user_id={user_id}")
                else:
                    redis_client.set(redis_key, str(float(total_usage)))
                    logger.info(
                        f"SET {redis_key} = ${float(total_usage):.4f}"
                        f" (was: ${float(existing):.4f})"
                    )

    summary = f"""
Prepaid Cumulative Backfill Complete:
  Users found: {stats['users_found']}
  Users with usage: {stats['users_with_usage']}
  Total usage: ${float(stats['total_usage_usd']):.2f}
  Dry run: {stats['dry_run']}
"""

    if dry_run:
        print(summary)
    else:
        logger.info(summary)

    return stats


def backfill_config_cumulative(dry_run: bool = False) -> dict:
    """
    Backfill cumulative Redis usage keys for all configs.

    1. Sum all-time platform_cost_usd per config_id from activities
    2. SET usage:config:total:{config_id} in Redis

    Args:
        dry_run: If True, print what would be set without writing

    Returns:
        Stats dict
    """
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_client = redis.from_url(redis_url, decode_responses=True)

    stats = {
        "configs_found": 0,
        "total_usage_usd": Decimal("0"),
        "dry_run": dry_run
    }

    logger.info(f"Starting config cumulative backfill (dry_run={dry_run})")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT config_id, COALESCE(SUM(platform_cost_usd), 0)
                FROM activities
                WHERE platform_cost_usd > 0
                GROUP BY config_id
                HAVING SUM(platform_cost_usd) > 0
            """)
            rows = cur.fetchall()

            stats["configs_found"] = len(rows)

            for config_id, total_cost in rows:
                total_cost = Decimal(str(total_cost))
                stats["total_usage_usd"] += total_cost

                redis_key = f"usage:config:total:{config_id}"
                existing_raw = redis_client.get(redis_key)
                existing = Decimal(existing_raw) if existing_raw else Decimal("0")

                if dry_run:
                    print(f"[DRY RUN] SET {redis_key} = {float(total_cost):.6f}"
                          f"  (existing: {float(existing):.6f}, delta: {float(total_cost - existing):.6f})"
                          f"  config_id={config_id}")
                else:
                    redis_client.set(redis_key, str(float(total_cost)))
                    logger.info(
                        f"SET {redis_key} = ${float(total_cost):.4f}"
                        f" (was: ${float(existing):.4f})"
                    )

    summary = f"""
Config Cumulative Backfill Complete:
  Configs with usage: {stats['configs_found']}
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
        description="Backfill cumulative Redis usage keys for prepaid users and per-config totals"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be set without writing to Redis"
    )

    args = parser.parse_args()

    try:
        # Backfill prepaid user cumulative keys
        stats = backfill_prepaid_cumulative(dry_run=args.dry_run)

        if not args.dry_run:
            print(f"Successfully backfilled {stats['users_with_usage']} prepaid users "
                  f"(${float(stats['total_usage_usd']):.2f} total usage)")

        # Backfill per-config cumulative keys
        config_stats = backfill_config_cumulative(dry_run=args.dry_run)

        if not args.dry_run:
            print(f"Successfully backfilled {config_stats['configs_found']} configs "
                  f"(${float(config_stats['total_usage_usd']):.2f} total usage)")

        return 0

    except Exception as e:
        logger.error(f"Backfill failed: {e}")
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
