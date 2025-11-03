"""
Activity Logger - Universal activity logging for Activity Timeline

This module provides a simple interface for logging all bot/agent activities
to the unified activities table. Used by scheduled bots, agents, and signal validation.
"""

from core.common.db import get_db_connection
import json
from typing import Optional, Dict, Any
from datetime import datetime


# Activity type to priority mapping
# Priority controls GROUPING behavior (not visibility):
#   1 = Never consolidate (trades, critical actions) - Each activity shows as separate icon
#   2 = Can consolidate (analysis, queries, decisions) - Group by type within time windows
# Note: All activity types always visible at all zoom levels (grouped, not hidden)
ACTIVITY_PRIORITY = {
    # Priority 1 - Never consolidate (always show individually)
    'trade_entry_long': 1,
    'trade_entry_short': 1,
    'trade_win': 1,
    'trade_loss': 1,
    'strategy_updated': 1,

    # Priority 2 - Can consolidate (group by type + time)
    'market_query': 2,
    'agent_wait': 2,
    'observation_recorded': 2,
    'analysis': 2,      # Frontend: Maps to "Agent Thoughts"
    'reasoning': 2,     # Frontend: Maps to "Agent Thoughts"
    'plan': 2,          # Frontend: Maps to "Agent Thoughts"
}


def log_activity(
    config_id: str,
    user_id: str,
    activity_type: str,
    activity_source: str,
    summary: str,
    details: Dict[str, Any],
    trade_id: Optional[str] = None,
    trade_type: Optional[str] = None,
    decision_id: Optional[str] = None,
    related_symbol: Optional[str] = None,
    priority: Optional[int] = None,
    importance: int = 5
) -> str:
    """
    Universal activity logger for all bot types.

    Args:
        config_id: Bot configuration ID
        user_id: User ID (for RLS)
        activity_type: Type of activity (see ACTIVITY_PRIORITY for valid types)
        activity_source: Source of activity ('agent_tool', 'scheduled_bot', 'signal_validation', etc.)
        summary: Brief title for timeline icon (max 200 chars)
        details: Full structured data (activity-type specific, stored as JSONB)
        trade_id: Optional trade linking (paper_trades.trade_id or live_trades.batch_id)
        trade_type: Optional trade type ('paper', 'live', 'aster')
        decision_id: Optional decision linking (decisions.decision_id)
        related_symbol: Optional symbol context (e.g., "BTC/USDT")
        priority: Optional priority override (1-3), defaults to ACTIVITY_PRIORITY mapping
        importance: User-facing importance (1-10), default 5

    Returns:
        activity_id: UUID of created activity

    Raises:
        Exception: If database operation fails

    Example:
        >>> log_activity(
        ...     config_id="uuid",
        ...     user_id="uuid",
        ...     activity_type="market_query",
        ...     activity_source="scheduled_bot",
        ...     summary="Queried BTC/USDT: 21 indicators",
        ...     details={"symbol": "BTC/USDT", "indicators": [...]}
        ... )
        'activity-uuid-here'
    """
    # Truncate summary if too long
    if len(summary) > 200:
        summary = summary[:197] + "..."

    # Auto-assign priority if not provided
    if priority is None:
        priority = ACTIVITY_PRIORITY.get(activity_type, 2)  # Default to medium

    # Validate priority
    if priority not in [1, 2]:
        priority = 2

    # Validate importance
    if not (1 <= importance <= 10):
        importance = 5

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO activities
                    (config_id, user_id, activity_type, activity_source, summary, details,
                     trade_id, trade_type, decision_id, related_symbol, priority, importance)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING activity_id
                """, (
                    config_id, user_id, activity_type, activity_source, summary,
                    json.dumps(details), trade_id, trade_type, decision_id,
                    related_symbol, priority, importance
                ))
                activity_id = cur.fetchone()[0]
                conn.commit()
                return str(activity_id)
    except Exception as e:
        # Log error but don't crash the main flow
        from core.common.logger import logger
        logger.bind(
            config_id=config_id,
            activity_type=activity_type
        ).error(f"Failed to log activity: {str(e)}")
        raise


def log_activity_safe(
    config_id: str,
    user_id: str,
    activity_type: str,
    activity_source: str,
    summary: str,
    details: Dict[str, Any],
    trade_id: Optional[str] = None,
    trade_type: Optional[str] = None,
    decision_id: Optional[str] = None,
    related_symbol: Optional[str] = None,
    priority: Optional[int] = None,
    importance: int = 5
) -> Optional[str]:
    """
    Safe wrapper for log_activity that catches exceptions.

    Use this when activity logging should not crash the main flow.
    Returns None on failure instead of raising.

    Args:
        Same as log_activity()

    Returns:
        activity_id on success, None on failure
    """
    try:
        return log_activity(
            config_id=config_id,
            user_id=user_id,
            activity_type=activity_type,
            activity_source=activity_source,
            summary=summary,
            details=details,
            trade_id=trade_id,
            trade_type=trade_type,
            decision_id=decision_id,
            related_symbol=related_symbol,
            priority=priority,
            importance=importance
        )
    except Exception as e:
        from core.common.logger import logger
        logger.bind(
            config_id=config_id,
            activity_type=activity_type
        ).warning(f"Activity logging failed (non-critical): {str(e)}")
        return None
