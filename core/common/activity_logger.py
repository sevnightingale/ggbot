"""
Activity Logger - Universal activity logging for Activity Timeline

This module provides a simple interface for logging all bot/agent activities
to the unified activities table with optional token tracking for metered billing.
Used by scheduled bots, agents, and signal validation.
"""

from core.common.db import get_db_connection
import json
from typing import Optional, Dict, Any
from datetime import datetime


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

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO activities
                    (config_id, user_id, activity_type, activity_source, summary, details,
                     trade_id, trade_type, decision_id, related_symbol, importance)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING activity_id
                """, (
                    config_id, user_id, activity_type, activity_source, summary,
                    json.dumps(details), trade_id, trade_type, decision_id,
                    related_symbol, importance
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
    importance: int = 5
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

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO activities
                    (config_id, user_id, activity_type, activity_source, summary, details,
                     decision_id, related_symbol, importance,
                     provider, model, thinking_mode, input_tokens, output_tokens,
                     reasoning_tokens, provider_cost_usd, platform_cost_usd, stripe_reported)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING activity_id
                """, (
                    config_id, user_id, 'llm_thought', activity_source, summary,
                    json.dumps(details), decision_id, related_symbol, importance,
                    provider, model, thinking_mode, input_tokens, output_tokens,
                    reasoning_tokens, provider_cost_usd, platform_cost_usd, False
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
    importance: int = 5
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
            importance=importance
        )
    except Exception as e:
        from core.common.logger import logger
        logger.bind(
            config_id=config_id,
            provider=provider,
            model=model
        ).warning(f"LLM activity logging failed (non-critical): {str(e)}")
        return None
