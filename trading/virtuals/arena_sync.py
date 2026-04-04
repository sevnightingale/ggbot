"""
Arena Sync — Mirror position closes to DGClaw arena agents.

Single idempotent function called from all close paths:
- Paper TP/SL (supabase_service.close_position)
- Live TP/SL (hyperliquid_adapter._detect_and_log_closes)
- Manual close (ggbot.py close endpoint)
- Reconciler (orchestrator, before new trades)

Checks DGClaw position exists before closing — safe to call multiple times.
"""

import asyncio
from typing import Optional

from core.common.logger import logger

_log = logger.bind(component="arena_sync")


def _arena_to_pair(symbol: str) -> Optional[str]:
    """Convert any symbol format to HL bare name (e.g., 'ETH')."""
    if not symbol:
        return None
    for sep in ['/', '-']:
        if sep in symbol:
            symbol = symbol.split(sep)[0]
    for suffix in ['USDT', 'USD', 'USDC', 'PERP']:
        if symbol.upper().endswith(suffix) and len(symbol) > len(suffix):
            symbol = symbol[:-len(suffix)]
    return symbol.upper() if symbol.isalpha() and len(symbol) <= 10 else None


async def mirror_close_to_arena(
    config_id: str,
    symbol: str,
    close_reason: str = "auto",
    user_id: Optional[str] = None,
):
    """
    Mirror a position close to the arena agent for this config.

    Fire-and-forget — failures are logged but never affect the primary close.
    Idempotent — checks DGClaw position exists before closing.

    Supports both Phase 2 (claw API via arena_agents) and Phase 1 (ACP SDK
    via ARENA_ENABLED_CONFIGS env var + Redis queue).
    """
    try:
        from core.common.db import db_fetch_one

        # 1. Does this config have an arena agent? (Phase 2 — claw API)
        agent = await db_fetch_one("""
            SELECT aa.wallet_address, vs.decrypted_secret, aa.agent_name,
                   aa.assigned_user_id
            FROM arena_agents aa
            JOIN vault.decrypted_secrets vs ON vs.id = aa.claw_api_key_vault_id
            WHERE aa.assigned_config_id = %s AND aa.status = 'assigned'
        """, (str(config_id),))

        if agent:
            await _close_via_claw_api(config_id, symbol, close_reason, user_id, agent)
            return

        # 2. Fallback: Phase 1 admin bot (ARENA_ENABLED_CONFIGS env var)
        import os
        arena_configs = os.environ.get('ARENA_ENABLED_CONFIGS', '')
        if arena_configs and str(config_id) in [c.strip() for c in arena_configs.split(',') if c.strip()]:
            await _close_via_redis_queue(config_id, symbol, close_reason, user_id)
            return

        # Not arena-enabled — nothing to do
    except Exception as e:
        _log.error(f"Arena sync close failed for config {config_id}: {e}")


async def _close_via_claw_api(
    config_id: str, symbol: str, close_reason: str,
    user_id: Optional[str], agent: tuple,
):
    """Close arena position via claw REST API (Phase 2 agents)."""
    wallet, api_key, agent_name, agent_user_id = agent
    effective_user_id = user_id or (str(agent_user_id) if agent_user_id else None)

    pair = _arena_to_pair(symbol)
    if not pair:
        _log.warning(f"Cannot convert symbol '{symbol}' for arena close")
        return

    from trading.virtuals.claw_api import ClawAPIClient
    client = ClawAPIClient(api_key)
    positions = await client.get_dgclaw_positions(wallet)
    has_position = any(p.get('pair') == pair for p in positions)

    if not has_position:
        _log.debug(f"Arena {agent_name}: no {pair} position to close (already closed by TP/SL?)")
        return

    _log.info(f"Arena sync: closing {pair} for {agent_name} (reason={close_reason})")
    result = await client.close_trade(pair)
    status = result.get('status', 'unknown')

    if effective_user_id:
        from core.common.activity_logger import log_activity_safe
        log_activity_safe(
            config_id=str(config_id),
            user_id=effective_user_id,
            activity_type='arena_exit',
            activity_source='arena_sync',
            summary=f"Arena: Closed {pair} ({close_reason})",
            details={
                'pair': pair, 'close_reason': close_reason,
                'agent': agent_name, 'job_id': result.get('job_id'),
                'status': status,
            },
            importance=6,
        )
    _log.info(f"Arena sync: {pair} close {status} for {agent_name}")


async def _close_via_redis_queue(
    config_id: str, symbol: str, close_reason: str,
    user_id: Optional[str],
):
    """Close arena position via Redis queue → sebastian-virtuals (Phase 1 admin bot)."""
    import json
    import redis as sync_redis
    from datetime import datetime, timezone

    pair = _arena_to_pair(symbol)
    if not pair:
        _log.warning(f"Cannot convert symbol '{symbol}' for Phase 1 arena close")
        return

    _log.info(f"Arena sync (Phase 1): enqueueing close {pair} for config {config_id[:8]}")

    try:
        r = sync_redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.lpush('arena:trade_queue', json.dumps({
            'config_id': str(config_id),
            'user_id': user_id,
            'symbol': symbol,
            'action': 'close',
            'confidence': 0,
            'enqueued_at': datetime.now(timezone.utc).isoformat(),
            'close_reason': close_reason,
        }))
        r.close()

        if user_id:
            from core.common.activity_logger import log_activity_safe
            log_activity_safe(
                config_id=str(config_id),
                user_id=user_id,
                activity_type='arena_exit',
                activity_source='arena_sync',
                summary=f"Arena: Close {pair} enqueued ({close_reason})",
                details={'pair': pair, 'close_reason': close_reason, 'path': 'phase1_queue'},
                importance=6,
            )
    except Exception as e:
        _log.error(f"Phase 1 arena close enqueue failed: {e}")
