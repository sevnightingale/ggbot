"""
Stripe Meter Reporter - Daily LLM Usage Aggregation & Reporting

This script aggregates unreported LLM token usage from the activities table
and reports it to Stripe's Meter API for metered billing.

Automatically scheduled via APScheduler in ggbot.py to run daily at midnight UTC.

Can also be run manually:
    python -m billing.stripe_meter_reporter
"""

import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Tuple
from decimal import Decimal

import stripe
from core.common.db import get_db_connection
from core.common.logger import logger


# Use existing Stripe initialization from ggbot.py (STRIPE_SECRET_KEY)
# When run standalone, initialize Stripe
if not stripe.api_key:
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

STRIPE_METER_ID = os.getenv("STRIPE_LLM_METER_ID")
STRIPE_EVENT_NAME = os.getenv("STRIPE_LLM_EVENT_NAME")


def get_unreported_usage() -> List[Tuple[str, Decimal, int]]:
    """
    Query activities table for unreported LLM usage.

    Excludes prepaid tier users - they pay upfront and should never
    be reported to Stripe meters. This is defense in depth; prepaid activities
    should already have stripe_reported=TRUE at creation time.

    Returns:
        List of (user_id, total_cost, activity_count) tuples
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        a.user_id,
                        SUM(a.platform_cost_usd) as total_cost,
                        COUNT(*) as activity_count
                    FROM activities a
                    JOIN user_profiles up ON a.user_id = up.user_id
                    WHERE a.stripe_reported = FALSE
                      AND a.platform_cost_usd IS NOT NULL
                      AND a.platform_cost_usd > 0
                      AND up.subscription_tier != 'prepaid'  -- Exclude prepaid users
                    GROUP BY a.user_id
                    ORDER BY total_cost DESC
                """)
                results = cur.fetchall()
                return [(row[0], Decimal(str(row[1])), row[2]) for row in results]
    except Exception as e:
        logger.error(f"Failed to query unreported usage: {e}")
        raise


def get_stripe_customer_id(user_id: str) -> str:
    """
    Get Stripe customer ID for a user.

    Args:
        user_id: Internal user UUID

    Returns:
        Stripe customer ID (cus_xxxxx)

    Raises:
        ValueError: If user has no Stripe customer ID (free tier users)
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT stripe_customer_id, subscription_tier
                FROM user_profiles
                WHERE user_id = %s
            """, (user_id,))
            result = cur.fetchone()

            if not result:
                raise ValueError(f"User {user_id} not found in database")

            customer_id, tier = result

            if not customer_id:
                # Expected for free tier users - raise without logging error
                raise ValueError(f"User is on '{tier}' tier (no billing)")

            return customer_id


def report_to_stripe(user_id: str, stripe_customer_id: str, total_cost: Decimal) -> bool:
    """
    Report usage to Stripe Meter API with idempotency.

    Args:
        user_id: Internal user UUID (for logging)
        stripe_customer_id: Stripe customer ID (cus_xxxxx)
        total_cost: Total billable cost in USD (already marked up)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Stripe expects integer cents or float dollars
        # We'll send as string to preserve precision
        value = str(total_cost)

        # Create idempotency identifier to prevent double billing
        # Format: user:date:cost_hash - unique per user per day per amount
        report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        identifier = f"{user_id}:{report_date}:{hash(value)}"

        # Create meter event with idempotency
        event = stripe.billing.MeterEvent.create(
            event_name=STRIPE_EVENT_NAME,
            payload={
                "stripe_customer_id": stripe_customer_id,
                "value": value,
            },
            identifier=identifier  # Stripe deduplicates based on this
        )

        logger.bind(
            user_id=user_id,
            stripe_customer_id=stripe_customer_id,
            cost=value,
            event_id=event.identifier,
            idempotency_key=identifier
        ).info(f"Reported ${value} to Stripe meter")

        return True

    except stripe.error.StripeError as e:
        logger.bind(
            user_id=user_id,
            stripe_customer_id=stripe_customer_id,
            cost=str(total_cost)
        ).error(f"Stripe API error: {e}")
        return False
    except Exception as e:
        logger.bind(
            user_id=user_id,
            stripe_customer_id=stripe_customer_id,
            cost=str(total_cost)
        ).error(f"Failed to report to Stripe: {e}")
        return False


def mark_as_reported(user_id: str) -> int:
    """
    Mark all unreported activities for a user as reported.

    Args:
        user_id: User UUID

    Returns:
        Number of activities marked as reported
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE activities
                    SET stripe_reported = TRUE,
                        stripe_reported_at = NOW()
                    WHERE user_id = %s
                      AND stripe_reported = FALSE
                      AND platform_cost_usd IS NOT NULL
                      AND platform_cost_usd > 0
                    RETURNING activity_id
                """, (user_id,))
                updated_count = len(cur.fetchall())
                conn.commit()
                return updated_count
    except Exception as e:
        logger.error(f"Failed to mark activities as reported for user {user_id}: {e}")
        raise


def run_daily_report() -> Dict[str, any]:
    """
    Main entry point: Aggregate and report unreported LLM usage to Stripe.

    Returns:
        Summary dict with stats
    """
    logger.info("Starting daily Stripe meter reporting")

    # Validate required env vars
    if not stripe.api_key:
        logger.error("STRIPE_API_KEY not set in environment")
        return {"error": "Missing STRIPE_API_KEY"}

    if not STRIPE_METER_ID:
        logger.error("STRIPE_LLM_METER_ID not set in environment")
        return {"error": "Missing STRIPE_LLM_METER_ID"}

    if not STRIPE_EVENT_NAME:
        logger.error("STRIPE_LLM_EVENT_NAME not set in environment")
        return {"error": "Missing STRIPE_LLM_EVENT_NAME"}

    # Get unreported usage
    usage_data = get_unreported_usage()

    if not usage_data:
        logger.info("No unreported usage to report")
        return {
            "success": True,
            "users_processed": 0,
            "total_reported_usd": 0,
            "activities_marked": 0
        }

    logger.info(f"Found unreported usage for {len(usage_data)} users")

    # Process each user
    stats = {
        "users_processed": 0,
        "users_succeeded": 0,
        "users_failed": 0,
        "total_reported_usd": Decimal("0"),
        "activities_marked": 0,
        "errors": []
    }

    for user_id, total_cost, activity_count in usage_data:
        try:
            logger.bind(
                user_id=user_id,
                cost=str(total_cost),
                activity_count=activity_count
            ).info(f"Processing user usage")

            # Get Stripe customer ID (skip free tier users)
            try:
                stripe_customer_id = get_stripe_customer_id(user_id)
            except ValueError as e:
                # Expected for free tier users - skip silently
                logger.bind(user_id=user_id).info(f"Skipping user: {e}")
                continue

            # Report to Stripe
            success = report_to_stripe(user_id, stripe_customer_id, total_cost)

            if success:
                # Mark as reported
                marked = mark_as_reported(user_id)
                stats["users_succeeded"] += 1
                stats["total_reported_usd"] += total_cost
                stats["activities_marked"] += marked

                logger.bind(
                    user_id=user_id,
                    cost=str(total_cost),
                    activities=marked
                ).info("Successfully reported and marked")
            else:
                stats["users_failed"] += 1
                stats["errors"].append(f"{user_id}: Failed to report to Stripe")

            stats["users_processed"] += 1

        except Exception as e:
            logger.bind(user_id=user_id).error(f"Error processing user: {e}")
            stats["users_failed"] += 1
            stats["errors"].append(f"{user_id}: {str(e)}")

    # Final summary
    logger.bind(**{k: str(v) for k, v in stats.items()}).info("Daily reporting complete")

    return {
        **stats,
        "success": True,
        "total_reported_usd": float(stats["total_reported_usd"])
    }


if __name__ == "__main__":
    try:
        result = run_daily_report()
        if result.get("success"):
            logger.info(f"Report completed: {result['users_succeeded']}/{result['users_processed']} users, ${result['total_reported_usd']:.4f} reported")
            sys.exit(0)
        else:
            logger.error(f"Report failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error in daily report: {e}")
        sys.exit(1)
