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

router = APIRouter(prefix="/api/v2/public", tags=["public"])


# Season 1 competition start time - all chart data starts from here
COMPETITION_START = datetime(2026, 1, 21, 12, 0, 0, tzinfo=timezone.utc)

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
                    ), 0) as manual_closes
                FROM configurations c
                LEFT JOIN paper_accounts pa ON c.config_id = pa.config_id
                WHERE c.is_public_performance = true
            """)
            bot_metadata = {row[0]: row for row in cur.fetchall()}

            # Query 2: Get hourly snapshots (no JSONB extraction - fast!)
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
                ORDER BY s.config_id, date_trunc('hour', s.timestamp), s.timestamp DESC
            """, (cutoff_time,))
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
            cur.execute("""
                SELECT
                    created_at,
                    total_equity
                FROM activities
                WHERE config_id = %s
                  AND total_equity IS NOT NULL
                ORDER BY created_at ASC
            """, (config_id,))
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

            # Get activities
            cur.execute("""
                SELECT
                    activity_id, activity_type, activity_source, summary, details,
                    trade_id, trade_type, decision_id, related_symbol,
                    importance, created_at
                FROM activities
                WHERE config_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (config_id, limit))
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

            # Get trade metrics
            cur.execute("""
                SELECT
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(realized_pnl) as total_pnl
                FROM paper_trades
                WHERE config_id = %s AND status = 'closed'
            """, (config_id,))
            metrics = cur.fetchone()

            # Get current balance from latest snapshot
            cur.execute("""
                SELECT current_balance + COALESCE(unrealized_pnl, 0) as total_equity
                FROM account_snapshots
                WHERE config_id = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """, (config_id,))
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
