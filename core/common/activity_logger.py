"""
Activity Logger - Universal activity logging for Activity Timeline

This module provides a simple interface for logging all bot/agent activities
to the unified activities table with optional token tracking for metered billing.
Used by scheduled bots, agents, and signal validation.

Note: Total equity calculations use formulas from AccountMetricsCalculator
(core.domain.metrics_calculator) to ensure consistency across platform.
"""

from core.common.db import get_db_connection
import json
import redis
from typing import Optional, Dict, Any
from datetime import datetime

# Import for formula reference (not used directly in SQL, but documents source of truth)
from core.domain.metrics_calculator import AccountMetricsCalculator

# Redis client for equity cache
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def get_latest_snapshot(config_id: str) -> Optional[Dict[str, Optional[float]]]:
    """
    Get total equity for activity logging - represents AI's current perception.

    Data sources (in priority order):
    1. Redis cache (updated every 5s by account monitor) - FASTEST, MOST RECENT
    2. Recent database snapshot (within last 10 minutes)
    3. Direct account table query (race condition fallback)

    The Redis cache represents the AI's "consciousness" - what it sees every 5 seconds.
    This is what gets logged with each activity, creating the AI's timeline.

    Args:
        config_id: Bot configuration ID

    Returns:
        Dict with 'current_balance' (contains total equity value) and 'total_pnl' keys
        Note: Key is 'current_balance' for backward compatibility, value is total_equity

    Example:
        >>> snapshot = get_latest_snapshot("uuid")
        >>> if snapshot:
        ...     print(f"Total Equity: {snapshot['current_balance']}, P&L: {snapshot['total_pnl']}")
    """
    try:
        # TIER 1: Try Redis cache first (updated every 5s, most recent)
        redis_key = f"equity:{config_id}"
        cached_data = redis_client.get(redis_key)

        if cached_data:
            cache = json.loads(cached_data)
            return {
                'current_balance': cache.get('total_equity'),  # This is total equity!
                'total_pnl': cache.get('total_pnl')  # Now included in cache
            }

        # TIER 2 & 3: Fallback to database queries (below)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # First, determine trading mode to use correct balance formula
                cur.execute("""
                    SELECT trading_mode
                    FROM configurations
                    WHERE config_id = %s
                    LIMIT 1
                """, (config_id,))
                mode_result = cur.fetchone()

                if not mode_result:
                    return None

                trading_mode = mode_result[0]

                # Try recent snapshot first (preferred - includes all trading modes)
                # For paper mode: Use Total Equity formula from AccountMetricsCalculator
                #   Formula: total_equity = current_balance + unrealized_pnl
                #   Note: current_balance already includes margin_used
                # For live modes: Use total_pnl (already includes unrealized)
                if trading_mode == 'paper':
                    balance_field = "COALESCE(current_balance + unrealized_pnl, current_balance)"
                else:
                    balance_field = "current_balance"

                cur.execute(f"""
                    SELECT {balance_field}, total_pnl
                    FROM account_snapshots
                    WHERE config_id = %s
                      AND timestamp > NOW() - INTERVAL '10 minutes'
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (config_id,))
                result = cur.fetchone()

                if result:
                    return {
                        'current_balance': float(result[0]) if result[0] is not None else None,
                        'total_pnl': float(result[1]) if result[1] is not None else None
                    }

                # FALLBACK: No recent snapshot - query account table directly
                # This handles race condition where trade closes before monitor creates snapshot

                # Query appropriate account table based on trading mode
                if trading_mode == 'paper':
                    # For paper: Calculate total equity using AccountMetricsCalculator formula
                    #   Formula: total_equity = current_balance + unrealized_pnl
                    #   Note: current_balance already includes margin_used
                    cur.execute("""
                        SELECT
                            pa.current_balance + COALESCE(pt.unrealized_pnl, 0) as total_equity,
                            pa.total_pnl
                        FROM paper_accounts pa
                        LEFT JOIN (
                            SELECT config_id,
                                   SUM(unrealized_pnl) as unrealized_pnl
                            FROM paper_trades
                            WHERE status = 'open'
                            GROUP BY config_id
                        ) pt ON pa.config_id = pt.config_id
                        WHERE pa.config_id = %s
                        LIMIT 1
                    """, (config_id,))
                    fallback = cur.fetchone()

                    if fallback:
                        return {
                            'current_balance': float(fallback[0]) if fallback[0] is not None else None,
                            'total_pnl': float(fallback[1]) if fallback[1] is not None else None
                        }

                # For symphony/aster, fallback to most recent snapshot (even if older than 10 min)
                # This is better than returning None, though may be slightly stale
                elif trading_mode in ['symphony', 'aster', 'hyperliquid']:
                    cur.execute("""
                        SELECT current_balance, total_pnl
                        FROM account_snapshots
                        WHERE config_id = %s
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """, (config_id,))
                    fallback = cur.fetchone()

                    if fallback:
                        return {
                            'current_balance': float(fallback[0]) if fallback[0] is not None else None,
                            'total_pnl': float(fallback[1]) if fallback[1] is not None else None
                        }

                return None
    except Exception as e:
        # Non-critical - snapshot is optional for activity logging
        from core.common.logger import logger
        logger.bind(config_id=config_id).debug(f"Could not fetch latest snapshot: {str(e)}")
        return None


# Activity type definitions (no priority - that was a mistake)
ACTIVITY_TYPES = {
    # Market Intelligence (no tokens)
    'market_query',      # Queried technical indicators, prices, signals
    'price_check',       # Quick price lookup via WebSocket cache

    # LLM Reasoning (HAS tokens)
    'llm_thought',       # Any LLM call (decision, validation, agent chat)

    # Trading Actions
    'trade_entry',       # Position opened (long or short in details.side)
    'trade_exit',        # Position closed
    'trade_update',      # Modified SL/TP or added to position

    # Agent-Specific
    'agent_wait',        # Agent self-scheduled pause
    'observation_recorded',  # Post-trade reflection
    'strategy_updated',  # Agent modified bot config

    # Signal Processing
    'signal_received',   # External signal ingested (ggShot, TradingView)

    # Bot Lifecycle
    'bot_created',       # Bot configuration created
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
    importance: int = 5
) -> str:
    """
    Universal activity logger for all bot types (WITHOUT token tracking).

    For LLM calls, use log_llm_activity() instead.

    Args:
        config_id: Bot configuration ID
        user_id: User ID (for RLS)
        activity_type: Type of activity (see ACTIVITY_TYPES for valid types)
        activity_source: Source of activity ('agent_tool', 'scheduled_bot', 'signal_validation', etc.)
        summary: Brief title for timeline icon (max 200 chars)
        details: Full structured data (activity-type specific, stored as JSONB)
        trade_id: Optional trade linking (paper_trades.trade_id or live_trades.batch_id)
        trade_type: Optional trade type ('paper', 'symphony', 'aster')
        decision_id: Optional decision linking (decisions.decision_id - deprecated)
        related_symbol: Optional symbol context (e.g., "BTC/USDT")
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

    # Validate importance
    if not (1 <= importance <= 10):
        importance = 5

    # Fetch latest snapshot for timeline chart
    snapshot = get_latest_snapshot(config_id)
    account_balance = snapshot['current_balance'] if snapshot else None
    account_pnl = snapshot['total_pnl'] if snapshot else None

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO activities
                    (config_id, user_id, activity_type, activity_source, summary, details,
                     trade_id, trade_type, decision_id, related_symbol, importance,
                     total_equity, account_pnl)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING activity_id
                """, (
                    config_id, user_id, activity_type, activity_source, summary,
                    json.dumps(details), trade_id, trade_type, decision_id,
                    related_symbol, importance, account_balance, account_pnl
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


def log_llm_activity(
    config_id: str,
    user_id: str,
    activity_source: str,
    summary: str,
    details: Dict[str, Any],
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    provider_cost_usd: float,
    platform_cost_usd: float,
    thinking_mode: Optional[bool] = None,
    reasoning_tokens: Optional[int] = None,
    decision_id: Optional[str] = None,
    related_symbol: Optional[str] = None,
    importance: int = 5,
    stripe_reported: bool = False
) -> str:
    """
    Log LLM activity WITH token tracking for metered billing.

    This is the primary function for logging all LLM calls (decision engine,
    signal validation, agent conversations). Token fields are required.

    Args:
        config_id: Bot configuration ID
        user_id: User ID (for RLS)
        activity_source: Source ('scheduled_bot', 'agent_tool', 'signal_validation')
        summary: Brief title (max 200 chars)
        details: Full structured data with reasoning, confidence, etc.
        provider: LLM provider ('openrouter', 'openai', 'anthropic', etc.)
        model: Model used ('grok', 'claude', 'gpt-5', etc.)
        input_tokens: Input tokens consumed
        output_tokens: Output tokens consumed
        provider_cost_usd: Raw provider cost (before markup)
        platform_cost_usd: Cost with 70% markup (billed to user)
        thinking_mode: Whether extended reasoning was enabled
        reasoning_tokens: Reasoning tokens (if applicable)
        decision_id: Optional decision linking (deprecated)
        related_symbol: Optional symbol context
        importance: User-facing importance (1-10), default 5
        stripe_reported: Set True for prepaid users (no meter reporting needed)

    Returns:
        activity_id: UUID of created activity

    Raises:
        Exception: If database operation fails

    Example:
        >>> log_llm_activity(
        ...     config_id="uuid",
        ...     user_id="uuid",
        ...     activity_source="scheduled_bot",
        ...     summary="Analyzed BTC/USDT (confidence: 85%)",
        ...     details={"reasoning": "...", "confidence": 0.85},
        ...     provider="openrouter",
        ...     model="grok",
        ...     input_tokens=2500,
        ...     output_tokens=150,
        ...     provider_cost_usd=0.0234,
        ...     platform_cost_usd=0.0398
        ... )
        'activity-uuid-here'
    """
    # Truncate summary if too long
    if len(summary) > 200:
        summary = summary[:197] + "..."

    # Validate importance
    if not (1 <= importance <= 10):
        importance = 5

    # Fetch latest snapshot for timeline chart
    snapshot = get_latest_snapshot(config_id)
    account_balance = snapshot['current_balance'] if snapshot else None
    account_pnl = snapshot['total_pnl'] if snapshot else None

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO activities
                    (config_id, user_id, activity_type, activity_source, summary, details,
                     decision_id, related_symbol, importance,
                     provider, model, thinking_mode, input_tokens, output_tokens,
                     reasoning_tokens, provider_cost_usd, platform_cost_usd, stripe_reported,
                     total_equity, account_pnl)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING activity_id
                """, (
                    config_id, user_id, 'llm_thought', activity_source, summary,
                    json.dumps(details), decision_id, related_symbol, importance,
                    provider, model, thinking_mode, input_tokens, output_tokens,
                    reasoning_tokens, provider_cost_usd, platform_cost_usd, stripe_reported,
                    account_balance, account_pnl
                ))
                activity_id = cur.fetchone()[0]
                conn.commit()
                return str(activity_id)
    except Exception as e:
        # Log error but don't crash the main flow
        from core.common.logger import logger
        logger.bind(
            config_id=config_id,
            provider=provider,
            model=model
        ).error(f"Failed to log LLM activity: {str(e)}")
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
            importance=importance
        )
    except Exception as e:
        from core.common.logger import logger
        logger.bind(
            config_id=config_id,
            activity_type=activity_type
        ).warning(f"Activity logging failed (non-critical): {str(e)}")
        return None


def log_llm_activity_safe(
    config_id: str,
    user_id: str,
    activity_source: str,
    summary: str,
    details: Dict[str, Any],
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    provider_cost_usd: float,
    platform_cost_usd: float,
    thinking_mode: Optional[bool] = None,
    reasoning_tokens: Optional[int] = None,
    decision_id: Optional[str] = None,
    related_symbol: Optional[str] = None,
    importance: int = 5,
    stripe_reported: bool = False
) -> Optional[str]:
    """
    Safe wrapper for log_llm_activity that catches exceptions.

    Use this when LLM activity logging should not crash the main flow.
    Returns None on failure instead of raising.

    Args:
        Same as log_llm_activity()

    Returns:
        activity_id on success, None on failure
    """
    try:
        return log_llm_activity(
            config_id=config_id,
            user_id=user_id,
            activity_source=activity_source,
            summary=summary,
            details=details,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider_cost_usd=provider_cost_usd,
            platform_cost_usd=platform_cost_usd,
            thinking_mode=thinking_mode,
            reasoning_tokens=reasoning_tokens,
            decision_id=decision_id,
            related_symbol=related_symbol,
            importance=importance,
            stripe_reported=stripe_reported
        )
    except Exception as e:
        from core.common.logger import logger
        logger.bind(
            config_id=config_id,
            provider=provider,
            model=model
        ).warning(f"LLM activity logging failed (non-critical): {str(e)}")
        return None
