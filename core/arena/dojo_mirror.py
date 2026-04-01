"""
Dojo Mirror — Copy-trade and signal dispatch for Dojo matches.

Two mirror paths:
1. User bots: copy-trade decision to active match instance accounts
2. House Bots: broadcast entry signal to IDLE match accounts (no positions)

All functions are fire-and-forget (asyncio.create_task). Failures are logged
but never affect the primary bot cycle. Pattern matches arena_sync.py.
"""

from typing import Optional

from core.common.db import db_fetch_all, db_fetch_one
from core.common.logger import logger

_log = logger.bind(component="dojo_mirror")


async def mirror_trade_to_dojo(
    config_id: str,
    decision_result: dict,
    trading_result: dict,
) -> None:
    """
    Mirror a user bot's trade to its active Dojo match account.

    Called from orchestrator after trading step. Only mirrors actual entries
    (long/short), not wait/hold/exit. Proportional sizing relative to
    match account balance.
    """
    try:
        action = decision_result.get('action', 'wait').lower()
        if action not in ('long', 'short', 'enter_long', 'enter_short', 'enter'):
            return

        # Normalize action
        side = 'short' if 'short' in action else 'long'

        # Find active match where this config is the challenger
        match = await db_fetch_one("""
            SELECT m.id, m.challenger_instance_id, m.challenger_user_id
            FROM dojo_matches m
            WHERE m.status = 'active'
              AND m.challenger_config_id = %s
        """, (config_id,))

        if not match:
            return

        match_id, instance_id, user_id = str(match[0]), str(match[1]), str(match[2])

        await _execute_mirror_trade(
            instance_id=instance_id,
            user_id=user_id,
            symbol=decision_result.get('symbol', ''),
            side=side,
            confidence=decision_result.get('confidence', 0.5),
            stop_loss=decision_result.get('stop_loss_price'),
            take_profit=decision_result.get('take_profit_price'),
            source_config_id=config_id,
        )

        _log.debug(
            f"Dojo mirror: {side} mirrored to instance={instance_id[:8]} "
            f"from config={config_id[:8]}"
        )

    except Exception as e:
        _log.error(f"Dojo mirror failed for config {config_id}: {e}")


async def mirror_close_to_dojo(
    config_id: str,
    symbol: str,
    close_reason: str = "auto",
) -> None:
    """
    Mirror a position close to Dojo match account(s).

    Called from all close paths (same pattern as arena_sync.py).
    Idempotent — only closes if the match account has the position.
    Checks both challenger and opponent sides (user-vs-user future).
    """
    try:
        # Find active matches where this config participates
        matches = await db_fetch_all("""
            SELECT
                m.id,
                CASE WHEN m.challenger_config_id = %s THEN m.challenger_instance_id
                     ELSE m.opponent_instance_id END AS instance_id
            FROM dojo_matches m
            WHERE m.status = 'active'
              AND (m.challenger_config_id = %s OR m.opponent_config_id = %s)
        """, (config_id, config_id, config_id))

        if not matches:
            return

        for match_row in matches:
            instance_id = str(match_row[1])
            if not instance_id or instance_id == 'None':
                continue

            await _close_mirror_position(instance_id, symbol, close_reason)

    except Exception as e:
        _log.error(f"Dojo mirror close failed for config {config_id}: {e}")


async def dispatch_house_bot_signal(
    config_id: str,
    decision_result: dict,
) -> None:
    """
    Dispatch a House Bot's entry signal to all active match accounts in IDLE state.

    House Bots run in Signal Mode (awareness_level='low') — they only do
    opportunity analysis, never hold positions. When they signal an entry,
    each match account independently decides whether to consume it:
    - IDLE (no open positions) → execute entry with TP/SL
    - IN_POSITION (has open position) → ignore, waiting for TP/SL to trigger

    The state machine is derived from paper_trades count — no extra state column.
    """
    try:
        action = decision_result.get('action', 'wait').lower()
        if action not in ('long', 'short', 'enter_long', 'enter_short', 'enter'):
            return

        side = 'short' if 'short' in action else 'long'

        # Find all active matches where this House Bot is the opponent
        matches = await db_fetch_all("""
            SELECT m.id, m.opponent_instance_id, m.opponent_user_id
            FROM dojo_matches m
            WHERE m.status = 'active'
              AND m.opponent_config_id = %s
        """, (config_id,))

        if not matches:
            return

        dispatched = 0
        for match_row in matches:
            instance_id = str(match_row[1])
            user_id = str(match_row[2])

            if not instance_id or instance_id == 'None':
                continue

            # Check IDLE state: no open positions on this match account
            open_count = await db_fetch_one("""
                SELECT COUNT(*) FROM paper_trades
                WHERE config_id = %s AND status = 'open'
            """, (instance_id,))

            if open_count and open_count[0] > 0:
                _log.debug(f"House Bot signal: instance={instance_id[:8]} IN_POSITION, skipping")
                continue

            await _execute_mirror_trade(
                instance_id=instance_id,
                user_id=user_id,
                symbol=decision_result.get('symbol', ''),
                side=side,
                confidence=decision_result.get('confidence', 0.5),
                stop_loss=decision_result.get('stop_loss_price'),
                take_profit=decision_result.get('take_profit_price'),
                source_config_id=config_id,
            )
            dispatched += 1

        if dispatched:
            _log.info(
                f"House Bot signal dispatched: {side} from {config_id[:8]} "
                f"→ {dispatched} match account(s)"
            )

    except Exception as e:
        _log.error(f"House Bot signal dispatch failed for config {config_id}: {e}")


# ─── Internal Helpers ───────────────────────────────────────────────────────

async def _execute_mirror_trade(
    instance_id: str,
    user_id: str,
    symbol: str,
    side: str,
    confidence: float,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    source_config_id: Optional[str] = None,
) -> None:
    """
    Execute a paper trade on a match instance account.

    Uses SupabasePaperTradingService directly — the same service that
    handles normal paper trades. The match instance's config_id routes
    trades to the match paper account automatically.
    """
    import asyncio
    from trading.paper.supabase_service import SupabasePaperTradingService

    service = SupabasePaperTradingService()
    intent = {
        'config_id': instance_id,
        'user_id': user_id,
        'symbol': symbol,
        'action': side,
        'confidence': confidence,
        'stop_loss_price': stop_loss,
        'take_profit_price': take_profit,
    }

    result = await service.execute_trade(intent)
    status = result.get('status', 'unknown')

    if status != 'success':
        _log.warning(
            f"Dojo mirror trade failed: instance={instance_id[:8]} "
            f"status={status} reason={result.get('reason', '?')}"
        )


async def _close_mirror_position(
    instance_id: str,
    symbol: str,
    close_reason: str,
) -> None:
    """Close open position(s) on a match instance for a given symbol."""
    from trading.paper.supabase_service import SupabasePaperTradingService

    # Find open positions for this symbol on the match instance
    positions = await db_fetch_all("""
        SELECT trade_id, user_id FROM paper_trades
        WHERE config_id = %s AND symbol = %s AND status = 'open'
    """, (instance_id, symbol))

    if not positions:
        return

    service = SupabasePaperTradingService()
    for pos in positions:
        trade_id, user_id = str(pos[0]), str(pos[1])
        try:
            await service.close_position(
                trade_id=trade_id,
                reason=close_reason,
            )
            _log.debug(f"Dojo mirror close: instance={instance_id[:8]} trade={trade_id[:8]}")
        except Exception as e:
            _log.warning(f"Dojo mirror close failed: trade={trade_id[:8]} error={e}")
