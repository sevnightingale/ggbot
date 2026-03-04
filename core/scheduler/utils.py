"""
Scheduler Utilities for GGBot

Provides cron configuration and timing functions for candle-aligned execution
following the SCHEDULDER.md specification.
"""

from datetime import datetime, timezone
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo
from typing import Dict, Any, Optional

# Timezone configuration
UTC = ZoneInfo("UTC")

# Misfire grace times per timeframe (seconds)
MISFIRE_GRACE_TIMES: Dict[str, int] = {
    "5m": 120,   # 2 minutes
    "15m": 180,  # 3 minutes
    "30m": 300,  # 5 minutes
    "1h": 300,   # 5 minutes
    "4h": 600,   # 10 minutes
    "1d": 900,   # 15 minutes
    "1w": 3600,  # 1 hour
}

# Timeframe to seconds mapping for close_ts calculation
TIMEFRAME_SECONDS: Dict[str, int] = {
    "5m": 300,    # 5 minutes
    "15m": 900,   # 15 minutes
    "30m": 1800,  # 30 minutes
    "1h": 3600,   # 1 hour
    "4h": 14400,  # 4 hours
    "1d": 86400,  # 1 day
    "1w": 604800, # 1 week
}


def cron_for(timeframe: str) -> CronTrigger:
    """
    Generate CronTrigger for given timeframe with 30-second delay after candle close.
    
    All executions are UTC-aligned with 30-second delay to allow candle completion.
    
    Args:
        timeframe: Timeframe string (5m, 15m, 30m, 1h, 4h, 1d)
        
    Returns:
        CronTrigger configured for the timeframe
        
    Raises:
        ValueError: If timeframe is not supported
    """
    if timeframe == "5m":
        return CronTrigger(minute="*/5", second=30, timezone=UTC)
    elif timeframe == "15m":
        return CronTrigger(minute="0,15,30,45", second=30, timezone=UTC)
    elif timeframe == "30m":
        return CronTrigger(minute="0,30", second=30, timezone=UTC)
    elif timeframe == "1h":
        return CronTrigger(minute=0, second=30, timezone=UTC)
    elif timeframe == "4h":
        return CronTrigger(hour="0,4,8,12,16,20", minute=0, second=30, timezone=UTC)
    elif timeframe == "1d":
        return CronTrigger(hour=0, minute=0, second=30, timezone=UTC)
    elif timeframe == "1w":
        return CronTrigger(day_of_week="mon", hour=0, minute=0, second=30, timezone=UTC)
    else:
        raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: {list(TIMEFRAME_SECONDS.keys())}")


def last_closed_close_ts(timeframe: str, now: datetime = None) -> int:
    """
    Calculate the Unix timestamp of the last closed candle for the given timeframe.
    
    This ensures we're always processing the most recently completed candle,
    aligned to the timeframe boundaries.
    
    Args:
        timeframe: Timeframe string (5m, 15m, 30m, 1h, 4h, 1d)
        now: Current time (defaults to UTC now)
        
    Returns:
        Unix timestamp of the last closed candle end time
        
    Raises:
        ValueError: If timeframe is not supported
        
    Example:
        If it's 14:32:30 UTC and timeframe is "15m":
        - Last closed candle: 14:15:00 - 14:30:00
        - Returns: timestamp for 14:30:00 UTC
    """
    if now is None:
        now = datetime.now(timezone.utc)
    
    if timeframe not in TIMEFRAME_SECONDS:
        raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: {list(TIMEFRAME_SECONDS.keys())}")
    
    # Convert to Unix timestamp
    current_ts = int(now.timestamp())
    
    # Get timeframe duration in seconds
    interval_seconds = TIMEFRAME_SECONDS[timeframe]
    
    # Calculate the start of the last completed candle
    # This floors the timestamp to the nearest interval boundary
    last_candle_start_ts = (current_ts // interval_seconds) * interval_seconds
    
    # The close timestamp is the end of that candle (start + duration)
    # But since we want the timestamp of when it closed, we return the boundary
    return last_candle_start_ts


def get_misfire_grace_time(timeframe: str) -> int:
    """
    Get the misfire grace time for a given timeframe.
    
    Args:
        timeframe: Timeframe string
        
    Returns:
        Grace time in seconds
        
    Raises:
        ValueError: If timeframe is not supported
    """
    if timeframe not in MISFIRE_GRACE_TIMES:
        raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: {list(MISFIRE_GRACE_TIMES.keys())}")
    
    return MISFIRE_GRACE_TIMES[timeframe]


def format_redis_idempotency_key(user_id: str, config_id: str, timeframe: str, close_ts: int) -> str:
    """
    Format Redis key for idempotency checking.
    
    Args:
        user_id: User ID
        config_id: Bot configuration ID
        timeframe: Timeframe string
        close_ts: Close timestamp
        
    Returns:
        Redis key string
    """
    return f"bot_exec:{user_id}:{config_id}:{timeframe}:{close_ts}"


def get_redis_ttl_for_timeframe(timeframe: str) -> int:
    """
    Get appropriate TTL for Redis keys based on timeframe.
    
    Uses 2x the timeframe duration to ensure keys don't expire too early
    but also don't accumulate indefinitely.
    
    Args:
        timeframe: Timeframe string
        
    Returns:
        TTL in seconds
    """
    if timeframe not in TIMEFRAME_SECONDS:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    
    # Minimum 2x timeframe, with reasonable maximums
    base_ttl = TIMEFRAME_SECONDS[timeframe] * 2
    
    # Set reasonable bounds
    min_ttl = 3600  # 1 hour minimum
    max_ttl = 7 * 24 * 3600  # 1 week maximum
    
    return max(min_ttl, min(base_ttl, max_ttl))


def calculate_next_run(timeframe: str) -> Optional[str]:
    """
    Calculate next run time for a timeframe without needing a scheduler instance.

    Uses the same CronTrigger logic as add_bot_job, so the calculated time
    matches what APScheduler would schedule.

    Args:
        timeframe: Timeframe string (5m, 15m, 30m, 1h, 4h, 1d, 1w)

    Returns:
        Next run time as ISO string (UTC), or None if timeframe is invalid
    """
    try:
        trigger = cron_for(timeframe)
        next_fire = trigger.get_next_fire_time(None, datetime.now(timezone.utc))
        return next_fire.strftime('%Y-%m-%dT%H:%M:%SZ') if next_fire else None
    except (ValueError, AttributeError):
        return None


def extract_timeframe_from_config(config: Dict[str, Any]) -> str:
    """
    Extract analysis_frequency (timeframe) from bot config.

    Args:
        config: Bot configuration dictionary (may be nested)

    Returns:
        Timeframe string (defaults to "1h"). For signal_driven bots, returns "signal_driven"
    """
    # Handle nested config structure from database
    if "config_data" in config:
        inner_config = config["config_data"]
        decision_config = inner_config.get("decision", {})
        config_type = config.get("config_type", "scheduled_trading")  # Use table field
    else:
        # Handle flat config structure
        decision_config = config.get("decision", {})
        config_type = config.get("config_type", "scheduled_trading")

    analysis_frequency = decision_config.get("analysis_frequency", "1h")

    # For signal validation bots, respect signal_driven frequency
    if config_type == "signal_validation" and analysis_frequency == "signal_driven":
        return "signal_driven"

    # For other bots, default signal_driven to 1h
    if analysis_frequency == "signal_driven":
        return "1h"

    return analysis_frequency