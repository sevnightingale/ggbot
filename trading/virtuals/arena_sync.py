"""
Arena Sync — Mirror position closes to DGClaw arena agents.

Close-mirroring (mirror_close_to_arena):
Single idempotent function called from all close paths:
- Paper TP/SL (supabase_service.close_position)
- Live TP/SL (hyperliquid_adapter._detect_and_log_closes)
- Manual close (ggbot.py close endpoint)
- Reconciler (orchestrator, before new trades)

Checks DGClaw position exists before closing — safe to call multiple times.

Close-backfill (sync_closes_from_hl):
Backfills arena_exit activities for closes that happened via DGClaw's own
server-side TP/SL execution — those never produce an ACP job, so none of
the mirror paths above fire. Queries Hyperliquid Info API directly using
the agent's captured HL subaccount. Invoked from the /status endpoint on
every modal poll (Redis-throttled to 60s per agent).
"""

import asyncio
from typing import Any, Dict, Optional

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


# =============================================================================
# Close backfill from Hyperliquid Info API
# =============================================================================

# 60s throttle keeps /status polling cheap. HL query is ~100ms but there's no
# point hammering it while a user idles with the modal open.
_SYNC_THROTTLE_SECONDS = 60

# Look-back window for HL fills. 7 days covers the current gap (ggbot-004's
# Apr 5 close) and keeps payloads small.
_SYNC_LOOKBACK_DAYS = 7


async def sync_closes_from_hl(config_id: str, agent: Dict[str, Any]) -> int:
    """
    Backfill arena_exit activities from Hyperliquid fills.

    Queries ``Info.user_fills_by_time`` for the agent's HL subaccount, filters
    to close fills, dedups against existing activities via
    ``details->>'hl_order_id'``, groups partial fills into 5-second buckets,
    and inserts missing rows with ``created_at`` set to the historical fill
    time so they appear at the correct timeline position.

    Idempotent and safe to call on every modal poll — a Redis 60s throttle
    key short-circuits repeat calls per agent.

    Args:
        config_id: Bot config UUID that owns the arena agent.
        agent: Dict from ``VaultManager.get_arena_credential_by_config``.
            Must contain ``agent_id``, ``user_id`` and
            ``hl_subaccount_address`` (None is fine; function no-ops).

    Returns:
        Number of new ``arena_exit`` rows inserted.
    """
    import json
    from collections import defaultdict
    from datetime import datetime, timedelta, timezone

    hl_sub = agent.get('hl_subaccount_address')
    if not hl_sub:
        # Subaccount not yet captured. Self-heals on the next /status call
        # that sees a non-null hlSubaccountAddress from Railway.
        return 0

    agent_id = agent.get('agent_id')
    user_id = agent.get('user_id')
    if not agent_id or not user_id:
        return 0

    # Redis throttle — 60s per agent. If Redis is unavailable, fall through
    # (single-request failure is cheaper than failing to sync at all).
    try:
        import redis as sync_redis
        r = sync_redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        throttle_key = f"arena:sync_closes_last_run:{agent_id}"
        if r.get(throttle_key):
            r.close()
            return 0
        r.setex(throttle_key, _SYNC_THROTTLE_SECONDS, "1")
        r.close()
    except Exception as e:
        _log.debug(f"sync_closes_from_hl: Redis throttle unavailable ({e}), proceeding without throttle")

    # Query Hyperliquid Info API in a thread pool (SDK is sync).
    try:
        from hyperliquid.info import Info
        from hyperliquid.utils import constants

        lookback_start_ms = int(
            (datetime.now(timezone.utc) - timedelta(days=_SYNC_LOOKBACK_DAYS)).timestamp() * 1000
        )

        def _query():
            info = Info(constants.MAINNET_API_URL, skip_ws=True)
            return info.user_fills_by_time(hl_sub, lookback_start_ms)

        fills = await asyncio.to_thread(_query)
    except Exception as e:
        _log.error(f"sync_closes_from_hl: HL query failed for {hl_sub[:10]}...: {e}")
        return 0

    if not fills:
        return 0

    close_fills = [f for f in fills if str(f.get('dir', '')).startswith('Close')]
    if not close_fills:
        return 0

    # Load existing dedup keys up front. Two parallel strategies:
    #
    #  1. Primary: match by hl_order_id in details. Catches any row we
    #     previously inserted from this sync function (and any future close
    #     path that starts recording the HL oid).
    #
    #  2. Secondary: match by (pair, created_at ± 60s). Catches rows inserted
    #     by the live close paths (arena_sync, claw_arena, arena_reconciler)
    #     which do NOT carry hl_order_id. Without this, the first sync run
    #     on a previously-tracked agent would insert duplicates for every
    #     close that was already logged by a different code path.
    from core.common.db import db_execute, db_fetch_all

    existing_rows = await db_fetch_all(
        """
        SELECT details->>'hl_order_id', details->>'pair', created_at
          FROM activities
         WHERE config_id = %s
           AND activity_type = 'arena_exit'
           AND created_at >= NOW() - INTERVAL '8 days'
        """,
        (str(config_id),),
    )
    existing_oids: set = set()
    existing_by_pair: Dict[str, list] = defaultdict(list)
    for row in existing_rows:
        oid_cell, pair_cell, created_at_cell = row
        if oid_cell:
            existing_oids.add(oid_cell)
        if pair_cell and created_at_cell is not None:
            existing_by_pair[pair_cell].append(created_at_cell)

    # ±60s window. Back-to-back closes of the same pair within one minute
    # are effectively impossible for bots on 3-5min cycles, so this is safe.
    _DEDUP_WINDOW_SECONDS = 60

    def _already_logged(pair: str, fill_ms: int) -> bool:
        existing_times = existing_by_pair.get(pair)
        if not existing_times:
            return False
        fill_dt = datetime.fromtimestamp(fill_ms / 1000, tz=timezone.utc)
        for ts in existing_times:
            if abs((ts - fill_dt).total_seconds()) <= _DEDUP_WINDOW_SECONDS:
                return True
        return False

    # Group partial fills: market_close() can produce multiple fills at the
    # same instant on different liquidity levels. Bucket by 5s so a single
    # close is one activity row regardless of how it filled.
    groups: Dict[tuple, Dict[str, Any]] = defaultdict(lambda: {
        'total_sz': 0.0,
        'total_pnl': 0.0,
        'weighted_px': 0.0,
        'earliest_oid': None,
        'earliest_time': None,
        'is_liquidation': False,
        'coin': '',
        'dir': '',
    })

    for fill in close_fills:
        oid = str(fill.get('oid', '') or '')
        if not oid or oid in existing_oids:
            continue

        try:
            fill_time_ms = int(fill.get('time', 0))
            sz = float(fill.get('sz', 0))
            px = float(fill.get('px', 0))
            pnl = float(fill.get('closedPnl', 0))
        except (TypeError, ValueError):
            continue

        if sz <= 0:
            continue

        coin = str(fill.get('coin', ''))
        dir_ = str(fill.get('dir', ''))
        bucket_key = (coin, fill_time_ms // 5000, dir_)

        g = groups[bucket_key]
        g['total_sz'] += sz
        g['total_pnl'] += pnl
        g['weighted_px'] += px * sz
        g['coin'] = coin
        g['dir'] = dir_
        if fill.get('liquidation'):
            g['is_liquidation'] = True
        if g['earliest_time'] is None or fill_time_ms < g['earliest_time']:
            g['earliest_time'] = fill_time_ms
            g['earliest_oid'] = oid

    if not groups:
        return 0

    inserted = 0
    for group in groups.values():
        total_sz = group['total_sz']
        if total_sz <= 0 or group['earliest_oid'] is None:
            continue

        fill_time_ms = group['earliest_time']

        # Secondary dedup: skip if a matching arena_exit already exists within
        # the ±60s window for this pair, even if it has no hl_order_id.
        if _already_logged(group['coin'], fill_time_ms):
            continue

        avg_px = group['weighted_px'] / total_sz
        side = 'long' if 'Long' in group['dir'] else 'short'
        close_reason = 'liquidation' if group['is_liquidation'] else 'dgclaw_server_side'
        created_at = datetime.fromtimestamp(fill_time_ms / 1000, tz=timezone.utc)

        details = {
            'pair': group['coin'],
            'side': side,
            'close_reason': close_reason,
            'close_price': avg_px,
            'realized_pnl': group['total_pnl'],
            'size': total_sz,
            'hl_order_id': group['earliest_oid'],
            'hl_fill_time_ms': fill_time_ms,
            'source': 'hl_sync',
        }
        summary = f"Arena: Closed {group['coin']} (HL sync)"

        try:
            await db_execute(
                """
                INSERT INTO activities
                    (config_id, user_id, activity_type, activity_source,
                     summary, details, importance, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(config_id),
                    str(user_id),
                    'arena_exit',
                    'hl_sync',
                    summary,
                    json.dumps(details),
                    6,
                    created_at,
                ),
            )
            inserted += 1
        except Exception as e:
            _log.error(f"sync_closes_from_hl insert failed for {group['coin']} oid={group['earliest_oid']}: {e}")
            continue

    if inserted > 0:
        _log.info(
            f"sync_closes_from_hl: {inserted} new close(s) for "
            f"config={str(config_id)[:8]} agent={agent.get('agent_name', '?')}"
        )

    return inserted
