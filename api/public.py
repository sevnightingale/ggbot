"""
Public API Endpoints

Public-facing endpoints that require no authentication.
Used for showcase features like the Arena competition page.
"""

import os
import json
import redis
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Query

from core.common.db import get_db_connection
from core.common.logger import logger
from core.arena.seasons import (
    SEASONS, CURRENT_SEASON_ID, get_current_season, get_season_phase, get_current_phase
)

router = APIRouter(prefix="/api/v2/public", tags=["public"])


# Season 1 competition window - freeze results to this period
COMPETITION_START = datetime(2026, 1, 21, 12, 0, 0, tzinfo=timezone.utc)
COMPETITION_END = datetime(2026, 2, 11, 12, 0, 0, tzinfo=timezone.utc)

# Redis cache for arena performance
ARENA_CACHE_KEY = "arena:performance"
ARENA_CACHE_TTL = 300  # 5 minutes - leaderboard doesn't need real-time updates

def _get_redis_client():
    """Get Redis client for caching."""
    return redis.from_url(
        os.getenv('REDIS_URL', 'redis://localhost:6379'),
        decode_responses=True
    )


@router.get("/arena/performance")
async def get_arena_performance(
    hours: int = Query(default=504, ge=1, le=720)  # Default 21 days (504 hours), max 30 days
) -> Dict[str, Any]:
    """
    Get performance comparison for Arena showcase bots.

    Public endpoint - no authentication required.
    Returns performance data only for bots marked with is_public_performance = true.

    Formula: total_equity = current_balance + unrealized_pnl
    (Source: AccountMetricsCalculator.calculate_total_equity)

    Note: Data always starts from COMPETITION_START (Jan 21 12:00 UTC) regardless
    of the hours parameter, to ensure fair comparison from competition start.

    Data is downsampled to hourly granularity for performance (reduces ~81k rows to ~2k).

    Args:
        hours: Time window in hours (ignored for Season 1 - uses competition start)

    Returns:
        {
            "success": true,
            "hours": 504,
            "competition_days": 21,
            "bots": [
                {
                    "config_id": "...",
                    "config_name": "The Nomad",
                    "profile_image_url": "...",
                    "description": "Bot description text",
                    "data_points": [{"timestamp": "...", "equity": 10500.50}, ...],
                    "current_equity": 10500.50,
                    "current_pnl": 500.50,
                    "initial_balance": 10000.00,
                    "total_trades": 45,
                    "win_rate": 0.67,
                    "open_positions": 2,
                    "frequency": "1h",
                    "model": "grok",
                    "symbol": "BTC/USDT",
                    "data_sources": {...},
                    "stop_loss": "5",
                    "take_profit": "10",
                    "max_margin": "20"
                }
            ]
        }
    """
    # Check Redis cache first
    try:
        redis_client = _get_redis_client()
        cached = redis_client.get(ARENA_CACHE_KEY)
        if cached:
            logger.info("Arena performance: cache hit")
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Arena cache read failed: {e}")
        # Continue without cache

    # Cache miss - query database
    # Always use competition start time - ignore hours param during Season 1
    cutoff_time = COMPETITION_START

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get equity snapshots for showcase bots - OPTIMIZED TWO-QUERY APPROACH
            # Problem: JSONB extraction (config_data->...) is expensive when done 81k times
            # Solution: Fetch bot metadata once (30 bots), then fetch snapshots separately

            # Query 1: Get bot metadata with config_data (extracted only ~30 times)
            # Season 1 complete — show all participants (not just active)
            cur.execute("""
                SELECT
                    c.config_id,
                    c.config_name,
                    c.profile_image_url,
                    c.description,
                    pa.initial_balance,
                    c.config_data->'decision'->>'analysis_frequency' as frequency,
                    c.config_data->'llm_config'->>'model' as model,
                    c.config_data->>'selected_pair' as symbol,
                    c.config_data->'extraction'->'selected_data_sources' as data_sources,
                    c.config_data->'trading'->'risk_management'->>'default_stop_loss_percent' as stop_loss,
                    c.config_data->'trading'->'risk_management'->>'default_take_profit_percent' as take_profit,
                    c.config_data->'trading'->'position_sizing'->>'max_margin_percent' as max_margin,
                    COALESCE((
                        SELECT COUNT(*)
                        FROM paper_trades pt
                        WHERE pt.config_id = c.config_id
                          AND pt.close_reason = 'manual'
                          AND pt.status = 'closed'
                          AND pt.opened_at >= '2026-01-21 12:00:00+00'
                          AND pt.closed_at <= '2026-02-11 12:00:00+00'
                    ), 0) as manual_closes
                FROM configurations c
                LEFT JOIN paper_accounts pa ON c.config_id = pa.config_id
                WHERE c.is_public_performance = true
            """)
            bot_metadata = {row[0]: row for row in cur.fetchall()}

            # Query 2: Get hourly snapshots (no JSONB extraction - fast!)
            # Capped at COMPETITION_END to freeze Season 1 results
            cur.execute("""
                SELECT DISTINCT ON (s.config_id, date_trunc('hour', s.timestamp))
                    s.config_id,
                    s.timestamp,
                    COALESCE(s.current_balance, 0) + COALESCE(s.unrealized_pnl, 0) as total_equity,
                    s.total_pnl,
                    s.total_trades,
                    s.win_rate,
                    s.open_positions,
                    s.current_balance,
                    s.unrealized_pnl
                FROM account_snapshots s
                WHERE s.config_id IN (SELECT config_id FROM configurations WHERE is_public_performance = true)
                AND s.timestamp >= %s
                AND s.timestamp <= %s
                ORDER BY s.config_id, date_trunc('hour', s.timestamp), s.timestamp DESC
            """, (cutoff_time, COMPETITION_END))
            snapshots = cur.fetchall()

            # Build bots_data by combining metadata with snapshots
            # Metadata columns: config_id, config_name, profile_image_url, description,
            #                   initial_balance, frequency, model, symbol, data_sources,
            #                   stop_loss, take_profit, max_margin
            # Snapshot columns: config_id, timestamp, total_equity, total_pnl, total_trades,
            #                   win_rate, open_positions, current_balance, unrealized_pnl
            bots_data = {}
            for snap in snapshots:
                config_id = snap[0]
                timestamp = snap[1]
                total_equity = float(snap[2])
                total_pnl = float(snap[3] or 0)
                total_trades = snap[4] or 0
                win_rate = float(snap[5] or 0)
                open_positions = snap[6] or 0
                current_balance = float(snap[7] or 0)
                unrealized_pnl = float(snap[8] or 0)

                if config_id not in bots_data:
                    # Get metadata for this bot (extracted only once per bot)
                    meta = bot_metadata.get(config_id)
                    if not meta:
                        continue  # Skip if no metadata found

                    bots_data[config_id] = {
                        "config_id": config_id,
                        "config_name": meta[1],
                        "profile_image_url": meta[2],
                        "description": meta[3],
                        "data_points": [],
                        "current_equity": total_equity,
                        "current_pnl": total_pnl,
                        "initial_balance": float(meta[4] or 10000),
                        "total_trades": total_trades,
                        "win_rate": win_rate,
                        "open_positions": open_positions,
                        "current_balance": current_balance,
                        "unrealized_pnl": unrealized_pnl,
                        # Config details (from metadata - extracted once)
                        "frequency": meta[5],
                        "model": meta[6],
                        "symbol": meta[7],
                        "data_sources": meta[8],
                        "stop_loss": meta[9],
                        "take_profit": meta[10],
                        "max_margin": meta[11],
                        "manual_closes": int(meta[12] or 0)
                    }

                # Add data point
                bots_data[config_id]["data_points"].append({
                    "timestamp": timestamp.isoformat(),
                    "equity": total_equity
                })

                # Update current values (last snapshot)
                bots_data[config_id]["current_equity"] = total_equity
                bots_data[config_id]["current_pnl"] = total_pnl
                bots_data[config_id]["total_trades"] = total_trades
                bots_data[config_id]["win_rate"] = win_rate
                bots_data[config_id]["open_positions"] = open_positions
                bots_data[config_id]["current_balance"] = current_balance
                bots_data[config_id]["unrealized_pnl"] = unrealized_pnl

            # Convert to list and sort by current equity descending
            bots_list = list(bots_data.values())
            bots_list.sort(key=lambda x: x["current_equity"], reverse=True)

    logger.info(f"Arena performance: cache miss, {len(bots_list)} showcase bots, {hours}h window")

    result = {
        "success": True,
        "hours": hours,
        "competition_days": hours // 24,
        "bots": bots_list
    }

    # Cache result
    try:
        redis_client = _get_redis_client()
        redis_client.setex(ARENA_CACHE_KEY, ARENA_CACHE_TTL, json.dumps(result))
        logger.info(f"Arena performance: cached for {ARENA_CACHE_TTL}s")
    except Exception as e:
        logger.warning(f"Arena cache write failed: {e}")

    return result


@router.get("/arena/{config_id}/balance-series")
async def get_arena_balance_series(config_id: str) -> Dict[str, Any]:
    """
    Get activity-based equity timeline for a public arena bot.

    Public endpoint - only works for bots with is_public_performance = true.
    Returns equity timeline from activities table (AI consciousness moments).

    Args:
        config_id: Bot configuration ID

    Returns:
        {
            "status": "success",
            "equity_series": [{"timestamp": "...", "total_equity": 123.45}, ...],
            "current_equity": 123.45,
            "initial_equity": 10000.0
        }
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Verify this is a public arena bot (Season 1 complete — include inactive bots)
            cur.execute("""
                SELECT config_id, created_at
                FROM configurations
                WHERE config_id = %s
                  AND is_public_performance = true
            """, (config_id,))
            config = cur.fetchone()

            if not config:
                return {"status": "error", "message": "Bot not found or not public"}

            config_created = config[1]

            # Get activities with equity data (AI's conscious moments)
            # Capped at competition window for Season 1
            cur.execute("""
                SELECT
                    created_at,
                    total_equity
                FROM activities
                WHERE config_id = %s
                  AND total_equity IS NOT NULL
                  AND created_at >= %s
                  AND created_at <= %s
                ORDER BY created_at ASC
            """, (config_id, COMPETITION_START, COMPETITION_END))
            activities = cur.fetchall()

    # Build timeline from AI's observations
    timeline = []
    for act in activities:
        timeline.append({
            "timestamp": act[0].isoformat(),
            "total_equity": float(act[1]) if act[1] is not None else 0
        })

    # Deduplicate by Unix second (lightweight-charts requires unique timestamps)
    if timeline:
        seen_seconds = {}
        for point in timeline:
            ts = datetime.fromisoformat(point['timestamp'].replace('Z', '+00:00'))
            unix_second = int(ts.timestamp())
            seen_seconds[unix_second] = point
        timeline = list(seen_seconds.values())
        timeline.sort(key=lambda x: x['timestamp'])

    current_equity = timeline[-1]['total_equity'] if timeline else 10000.0
    initial_equity = timeline[0]['total_equity'] if timeline else 10000.0

    logger.info(f"Arena balance series: {config_id}, {len(timeline)} points")

    return {
        "status": "success",
        "equity_series": timeline,
        "current_equity": current_equity,
        "initial_equity": initial_equity
    }


@router.get("/arena/{config_id}/activities")
async def get_arena_activities(
    config_id: str,
    limit: int = Query(default=500, ge=1, le=1000)
) -> Dict[str, Any]:
    """
    Get activities for a public arena bot.

    Public endpoint - only works for bots with is_public_performance = true.
    Returns activity events (trades, thoughts, waits, etc.) for timeline markers.

    Args:
        config_id: Bot configuration ID
        limit: Max activities to return (default 500)

    Returns:
        {
            "status": "success",
            "activities": [
                {
                    "id": "uuid",
                    "timestamp": "2025-12-01T10:30:00Z",
                    "type": "trade_entry",
                    "priority": 9,
                    "data": {
                        "summary": "Opened long BTC/USDT",
                        "details": {...},
                        "symbol": "BTC/USDT"
                    }
                }
            ],
            "count": 47
        }
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Verify this is a public arena bot (Season 1 complete — include inactive bots)
            cur.execute("""
                SELECT config_id
                FROM configurations
                WHERE config_id = %s
                  AND is_public_performance = true
            """, (config_id,))
            config = cur.fetchone()

            if not config:
                return {"status": "error", "message": "Bot not found or not public"}

            # Get activities (only within competition window)
            cur.execute("""
                SELECT
                    activity_id, activity_type, activity_source, summary, details,
                    trade_id, trade_type, decision_id, related_symbol,
                    importance, created_at
                FROM activities
                WHERE config_id = %s
                  AND created_at >= %s AND created_at <= %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (config_id, COMPETITION_START, COMPETITION_END, limit))
            activities = cur.fetchall()

    return {
        "status": "success",
        "activities": [
            {
                "id": str(a[0]),
                "timestamp": a[10].isoformat(),
                "type": a[1],
                "priority": a[9],
                "data": {
                    "summary": a[3],
                    "details": a[4],
                    "symbol": a[8],
                    "importance": a[9],
                    "trade_id": str(a[5]) if a[5] else None,
                    "trade_type": a[6]
                }
            }
            for a in activities
        ],
        "count": len(activities)
    }


@router.get("/arena/{config_id}/metadata")
async def get_arena_metadata(config_id: str) -> Dict[str, Any]:
    """
    Get metadata for a public arena bot.

    Public endpoint - only works for bots with is_public_performance = true.
    Returns bot name, performance metrics from paper trading.

    Args:
        config_id: Bot configuration ID

    Returns:
        {
            "status": "success",
            "metadata": {
                "botName": "The Nomad",
                "startingBalance": 10000,
                "currentBalance": 10500,
                "totalTrades": 12,
                "winRate": 66.7,
                "performance": 5.0,
                "createdAt": "2025-12-01T00:00:00Z"
            }
        }
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Verify this is a public arena bot and get config info (Season 1 complete — include inactive bots)
            cur.execute("""
                SELECT c.config_id, c.config_name, c.created_at, pa.initial_balance
                FROM configurations c
                LEFT JOIN paper_accounts pa ON c.config_id = pa.config_id
                WHERE c.config_id = %s
                  AND c.is_public_performance = true
            """, (config_id,))
            config = cur.fetchone()

            if not config:
                return {"status": "error", "message": "Bot not found or not public"}

            config_name = config[1]
            created_at = config[2]
            initial_balance = float(config[3]) if config[3] else 10000.0

            # Get trade metrics (only trades within competition window)
            cur.execute("""
                SELECT
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(realized_pnl) as total_pnl
                FROM paper_trades
                WHERE config_id = %s AND status = 'closed'
                  AND opened_at >= %s AND closed_at <= %s
            """, (config_id, COMPETITION_START, COMPETITION_END))
            metrics = cur.fetchone()

            # Get balance at competition end (not latest — Season 1 is frozen)
            cur.execute("""
                SELECT current_balance + COALESCE(unrealized_pnl, 0) as total_equity
                FROM account_snapshots
                WHERE config_id = %s
                  AND timestamp <= %s
                ORDER BY timestamp DESC
                LIMIT 1
            """, (config_id, COMPETITION_END))
            latest = cur.fetchone()

    total_trades = metrics[0] or 0
    wins = metrics[1] or 0
    total_pnl = float(metrics[2]) if metrics[2] else 0.0
    current_balance = float(latest[0]) if latest else initial_balance
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    performance = ((current_balance - initial_balance) / initial_balance * 100) if initial_balance > 0 else 0

    logger.info(f"Arena metadata: {config_id}, {config_name}")

    return {
        "status": "success",
        "metadata": {
            "botName": config_name,
            "startingBalance": initial_balance,
            "currentBalance": current_balance,
            "totalTrades": total_trades,
            "winRate": round(win_rate, 1),
            "performance": round(performance, 2),
            "createdAt": created_at.isoformat()
        }
    }


# =============================================================================
# Season 2 Arena Endpoints
# =============================================================================

@router.get("/arena/season/current")
async def get_current_season_status() -> Dict[str, Any]:
    """
    Get current arena season metadata, computed phase, and registration count.
    Public endpoint — Redis cached 60s.
    """
    cache_key = "arena:season:current"

    # Check cache
    try:
        redis_client = _get_redis_client()
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass

    season = get_current_season()
    phase = get_current_phase()

    # Count active registrations
    registration_count = 0
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM arena_registrations
                    WHERE season_id = %s AND unregistered_at IS NULL
                """, (CURRENT_SEASON_ID,))
                registration_count = cur.fetchone()[0]
    except Exception as e:
        logger.warning(f"Failed to count arena registrations: {e}")

    result = {
        "success": True,
        "season_id": season['season_id'],
        "name": season['name'],
        "phase": phase,
        "training_start": season['training_start'].isoformat(),
        "registration_start": season['registration_start'].isoformat(),
        "registration_end": season['registration_end'].isoformat(),
        "competition_start": season['competition_start'].isoformat(),
        "competition_end": season['competition_end'].isoformat(),
        "prize_description": season.get('prize_description', ''),
        "registration_count": registration_count,
    }

    # Cache 60s
    try:
        redis_client = _get_redis_client()
        redis_client.setex(cache_key, 60, json.dumps(result))
    except Exception:
        pass

    return result


def _calculate_active_days(config_id: str, start: datetime, end: datetime) -> int:
    """
    Count distinct days a bot made at least one decision within a date range.
    Used for 18/21 day activity requirement.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(DISTINCT DATE(created_at))
                FROM decisions
                WHERE config_id = %s
                  AND created_at >= %s
                  AND created_at <= %s
            """, (config_id, start, end))
            return cur.fetchone()[0] or 0


@router.get("/arena/season/{season_id}/leaderboard")
async def get_season_leaderboard(season_id: int) -> Dict[str, Any]:
    """
    Get leaderboard for a specific arena season.
    Public endpoint — Redis cached 300s.

    During registration: shows registered bots (no equity data yet).
    During competition: equity from account_snapshots within competition window.
    After competition: final snapshotted results from arena_registrations.
    """
    season = SEASONS.get(season_id)
    if not season:
        return {"success": False, "error": "Season not found"}

    cache_key = f"arena:s{season_id}:leaderboard"

    # Check cache
    try:
        redis_client = _get_redis_client()
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass

    phase = get_season_phase(season_id)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get all active registrations with bot metadata
            cur.execute("""
                SELECT
                    ar.id,
                    ar.config_id,
                    ar.user_id,
                    ar.registered_at,
                    ar.starting_balance,
                    ar.final_balance,
                    ar.final_pnl_pct,
                    ar.active_days,
                    ar.eligible,
                    ar.rank,
                    c.config_name,
                    c.profile_image_url,
                    c.description,
                    c.config_data->'decision'->>'analysis_frequency' as frequency,
                    c.config_data->'llm_config'->>'model' as model,
                    c.config_data->>'selected_pair' as symbol,
                    c.config_data->'extraction'->'selected_data_sources' as data_sources,
                    c.config_data->'trading'->'risk_management'->>'default_stop_loss_percent' as stop_loss,
                    c.config_data->'trading'->'risk_management'->>'default_take_profit_percent' as take_profit,
                    c.config_data->'trading'->'position_sizing'->>'max_margin_percent' as max_margin
                FROM arena_registrations ar
                JOIN configurations c ON ar.config_id = c.config_id
                WHERE ar.season_id = %s AND ar.unregistered_at IS NULL
                ORDER BY ar.rank ASC NULLS LAST, ar.registered_at ASC
            """, (season_id,))
            rows = cur.fetchall()

            bots = []
            for row in rows:
                config_id = str(row[1])
                bot = {
                    "registration_id": str(row[0]),
                    "config_id": config_id,
                    "user_id": str(row[2]),
                    "registered_at": row[3].isoformat() if row[3] else None,
                    "starting_balance": float(row[4] or 10000),
                    "config_name": row[10],
                    "profile_image_url": row[11],
                    "description": row[12],
                    "frequency": row[13],
                    "model": row[14],
                    "symbol": row[15],
                    "data_sources": row[16],
                    "stop_loss": row[17],
                    "take_profit": row[18],
                    "max_margin": row[19],
                    "current_equity": float(row[4] or 10000),
                    "current_pnl": 0.0,
                    "pnl_pct": 0.0,
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "active_days": row[7] or 0,
                    "is_eligible": row[8] if row[8] is not None else True,
                    "rank": row[9],
                }

                # If competition completed, use snapshotted results
                if phase == 'completed' and row[5] is not None:
                    bot["current_equity"] = float(row[5])
                    bot["pnl_pct"] = float(row[6] or 0)
                    bot["current_pnl"] = float(row[5] or 10000) - float(row[4] or 10000)

                # During competition, get live equity from latest snapshot
                elif phase == 'competition':
                    cur.execute("""
                        SELECT
                            COALESCE(s.current_balance, 0) + COALESCE(s.unrealized_pnl, 0) as equity,
                            s.total_trades,
                            s.win_rate
                        FROM account_snapshots s
                        WHERE s.config_id = %s
                          AND s.timestamp >= %s
                        ORDER BY s.timestamp DESC
                        LIMIT 1
                    """, (config_id, season['competition_start']))
                    snap = cur.fetchone()
                    if snap:
                        equity = float(snap[0])
                        bot["current_equity"] = equity
                        bot["current_pnl"] = equity - bot["starting_balance"]
                        bot["pnl_pct"] = ((equity - bot["starting_balance"]) / bot["starting_balance"]) * 100
                        bot["total_trades"] = snap[1] or 0
                        bot["win_rate"] = float(snap[2] or 0)

                    # Calculate live active days
                    bot["active_days"] = _calculate_active_days(
                        config_id, season['competition_start'], season['competition_end']
                    )
                    bot["is_eligible"] = bot["active_days"] >= 18

                bots.append(bot)

            # Sort by equity during competition, by rank if completed
            if phase == 'competition':
                bots.sort(key=lambda b: b["current_equity"], reverse=True)
            elif phase == 'completed':
                bots.sort(key=lambda b: (b["rank"] or 999, -(b["pnl_pct"] or 0)))

    result = {
        "success": True,
        "season_id": season_id,
        "phase": phase,
        "bot_count": len(bots),
        "bots": bots,
    }

    # Cache: 300s during competition, 60s during registration, 3600s when completed
    ttl = 300 if phase == 'competition' else (60 if phase == 'registration' else 3600)
    try:
        redis_client = _get_redis_client()
        redis_client.setex(cache_key, ttl, json.dumps(result))
    except Exception:
        pass

    return result


# ─── Dojo Public Endpoints ───────────────────────────────────────────────────


@router.get("/dojo/bots")
async def get_dojo_bots_endpoint() -> Dict[str, Any]:
    """Public leaderboard: all active, visible paper bots with Elo and performance."""
    from core.arena.dojo_public import get_dojo_bots
    bots = get_dojo_bots()
    return {"status": "success", "bots": bots, "count": len(bots)}


@router.get("/dojo/stats")
async def get_dojo_stats_endpoint() -> Dict[str, Any]:
    """Aggregate Dojo statistics: total bots, average Elo, active matches."""
    from core.arena.dojo_public import get_dojo_stats
    stats = get_dojo_stats()
    return {"status": "success", **stats}


@router.get("/dojo/house-bots")
async def get_house_bots_endpoint() -> Dict[str, Any]:
    """House Bots available for Dojo challenges."""
    from core.arena.dojo_public import get_house_bots
    bots = get_house_bots()
    return {"status": "success", "bots": bots, "count": len(bots)}


@router.get("/dojo/match/{match_id}")
async def get_dojo_match_detail(match_id: str) -> Dict[str, Any]:
    """Public match detail — shareable match result."""
    from core.arena.matches import get_match_detail
    detail = get_match_detail(match_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Match not found")
    return {"status": "success", "match": detail}
