"""
Usage & Billing API Endpoints

Provides real-time usage visibility from Redis counters.
Used by frontend to display current period usage, credits, and per-bot breakdown.
"""
import os
import json
import redis
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from core.auth.supabase_auth import AuthenticatedUser, get_current_user_v2
from core.services.config_service import config_service
from core.common.logger import logger


router = APIRouter(prefix="/api/v2/usage", tags=["usage"])

# Redis client for usage counters (decode_responses=True returns strings instead of bytes)
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'), decode_responses=True)


@router.get("/me")
async def get_my_usage(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Get current user's usage summary.

    Returns cached summary (updated every 5min by account-monitor)
    or live Redis counter if no cached summary available.

    Response:
    {
        "period": "2026-01",
        "usage_usd": 12.34,
        "credits_usd": 50.00,
        "net_balance_usd": 37.66,
        "updated_at": "2026-01-15T10:30:00Z",
        "cached": true
    }
    """
    user_id = str(current_user.user_id)

    try:
        # Try cached summary first (includes credits from Stripe)
        cached = redis_client.get(f"usage:summary:{user_id}")
        if cached:
            summary = json.loads(cached)
            summary["cached"] = True
            return summary

        # Fallback to direct Redis read (no Stripe call - credits will be None)
        period = datetime.utcnow().strftime("%Y-%m")
        usage_raw = redis_client.get(f"usage:user:{user_id}:{period}")
        usage = float(usage_raw) if usage_raw else 0.0

        return {
            "period": period,
            "usage_usd": usage,
            "credits_usd": None,  # Requires Stripe call - use cached summary
            "net_balance_usd": None,
            "updated_at": datetime.utcnow().isoformat(),
            "cached": False
        }

    except Exception as e:
        logger.error(f"Failed to get usage for user {user_id}: {e}")
        # Return empty response rather than error
        return {
            "period": datetime.utcnow().strftime("%Y-%m"),
            "usage_usd": 0.0,
            "credits_usd": None,
            "net_balance_usd": None,
            "updated_at": datetime.utcnow().isoformat(),
            "cached": False,
            "error": "Unable to fetch usage data"
        }


@router.get("/config/{config_id}")
async def get_config_usage(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Get specific bot's usage - instant from Redis.

    Response:
    {
        "config_id": "uuid",
        "config_name": "My BTC Bot",
        "period": "2026-01",
        "period_usage_usd": 5.67,
        "today_usage_usd": 0.89
    }
    """
    user_id = str(current_user.user_id)

    # Verify ownership
    config = await config_service.get_config(config_id, user_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    try:
        period = datetime.utcnow().strftime("%Y-%m")
        day = datetime.utcnow().strftime("%Y-%m-%d")

        period_usage_raw = redis_client.get(f"usage:config:{config_id}:{period}")
        today_usage_raw = redis_client.get(f"usage:config:{config_id}:{day}")

        period_usage = float(period_usage_raw) if period_usage_raw else 0.0
        today_usage = float(today_usage_raw) if today_usage_raw else 0.0

        return {
            "config_id": config_id,
            "config_name": config.config_name,
            "period": period,
            "period_usage_usd": period_usage,
            "today_usage_usd": today_usage
        }

    except Exception as e:
        logger.error(f"Failed to get usage for config {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch config usage")


@router.get("/breakdown")
async def get_usage_breakdown(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Get usage breakdown by bot for current user.

    Response:
    {
        "period": "2026-01",
        "breakdown": [
            {
                "config_id": "uuid",
                "config_name": "BTC Scalper",
                "state": "active",
                "period_usage_usd": 8.50
            },
            ...
        ],
        "total_usage_usd": 12.34
    }
    """
    user_id = str(current_user.user_id)

    try:
        configs = await config_service.list_configs(user_id)
        period = datetime.utcnow().strftime("%Y-%m")

        breakdown = []
        total = 0.0

        for config in configs:
            usage_raw = redis_client.get(f"usage:config:{config.config_id}:{period}")
            usage = float(usage_raw) if usage_raw else 0.0

            breakdown.append({
                "config_id": config.config_id,
                "config_name": config.config_name,
                "state": config.state,
                "period_usage_usd": usage
            })
            total += usage

        # Sort by usage descending
        breakdown.sort(key=lambda x: x["period_usage_usd"], reverse=True)

        return {
            "period": period,
            "breakdown": breakdown,
            "total_usage_usd": total
        }

    except Exception as e:
        logger.error(f"Failed to get usage breakdown for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch usage breakdown")


@router.get("/history/{config_id}")
async def get_config_usage_history(
    config_id: str,
    days: int = 30,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Get daily usage history for a specific bot.

    Query params:
    - days: Number of days to look back (default 30, max 90)

    Response:
    {
        "config_id": "uuid",
        "config_name": "BTC Scalper",
        "history": [
            {"date": "2026-01-15", "usage_usd": 0.89},
            {"date": "2026-01-14", "usage_usd": 1.23},
            ...
        ]
    }
    """
    user_id = str(current_user.user_id)

    # Verify ownership
    config = await config_service.get_config(config_id, user_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Limit to 90 days (our TTL)
    days = min(days, 90)

    try:
        from datetime import timedelta

        history = []
        today = datetime.utcnow().date()

        for i in range(days):
            day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            usage_raw = redis_client.get(f"usage:config:{config_id}:{day}")
            usage = float(usage_raw) if usage_raw else 0.0

            # Only include days with usage
            if usage > 0:
                history.append({
                    "date": day,
                    "usage_usd": usage
                })

        return {
            "config_id": config_id,
            "config_name": config.config_name,
            "history": history
        }

    except Exception as e:
        logger.error(f"Failed to get usage history for config {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch usage history")
