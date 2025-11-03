"""
Activities API - Activity Timeline endpoints

Provides activity data for the Canvas-based Activity Timeline viewer.
Endpoints return activities, balance series, and metadata for a specific bot config.
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional, List
from datetime import datetime, timezone

from core.auth.supabase_auth import AuthenticatedUser, get_current_user_v2
from core.common.db import get_db_connection
from core.common.logger import logger
from trading.live.aster_service_v3 import AsterDEXV3LiveTradingService


router = APIRouter(prefix="/api/v2/activities", tags=["activities"])


@router.get("/{config_id}")
async def get_activities(
    config_id: str,
    start_time: Optional[str] = Query(None, description="ISO timestamp filter start"),
    end_time: Optional[str] = Query(None, description="ISO timestamp filter end"),
    activity_types: Optional[List[str]] = Query(None, description="Filter by activity types"),
    trade_id: Optional[str] = Query(None, description="Filter by specific trade"),
    min_importance: int = Query(1, ge=1, le=10, description="Minimum importance level"),
    limit: int = Query(500, ge=1, le=1000, description="Max activities to return"),
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Get all activities for a bot configuration (timeline data).

    Returns activities in reverse chronological order with optional filtering.
    Used by ActivityTimelineViewer to render the canvas timeline.

    Query parameters:
    - start_time: ISO timestamp (optional) - filter activities after this time
    - end_time: ISO timestamp (optional) - filter activities before this time
    - activity_types: List of activity types (optional) - filter by specific types
    - trade_id: UUID (optional) - filter activities related to a specific trade
    - min_importance: 1-10 (default 1) - hide activities below this importance
    - limit: Max activities (default 500, max 1000)

    Returns:
    {
        "status": "success",
        "activities": [
            {
                "id": "uuid",
                "timestamp": "2025-11-03T10:30:00Z",
                "type": "trade_entry_long",
                "priority": 1,
                "data": {
                    "summary": "Opened long BTC/USDT at $110,229",
                    "details": {...},
                    "symbol": "BTC/USDT",
                    "importance": 9,
                    "trade_id": "uuid",
                    "trade_type": "paper"
                }
            }
        ],
        "count": 47
    }
    """
    try:
        # Verify config ownership
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id FROM configurations
                    WHERE config_id = %s
                """, (config_id,))
                config = cur.fetchone()

                if not config:
                    raise HTTPException(status_code=404, detail="Configuration not found")

                if config[0] != current_user.user_id:
                    raise HTTPException(status_code=403, detail="Not authorized to access this configuration")

                # Build query with filters
                query = """
                    SELECT
                        activity_id, activity_type, activity_source, summary, details,
                        trade_id, trade_type, decision_id, related_symbol,
                        priority, importance, created_at
                    FROM activities
                    WHERE config_id = %s
                """
                params = [config_id]

                # Apply time filters
                if start_time:
                    query += " AND created_at >= %s"
                    params.append(start_time)

                if end_time:
                    query += " AND created_at <= %s"
                    params.append(end_time)

                # Apply type filter
                if activity_types:
                    query += " AND activity_type = ANY(%s)"
                    params.append(activity_types)

                # Apply trade filter
                if trade_id:
                    query += " AND trade_id = %s"
                    params.append(trade_id)

                # Apply importance filter
                query += " AND importance >= %s"
                params.append(min_importance)

                # Order and limit
                query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)

                # Execute query
                cur.execute(query, params)
                activities = cur.fetchall()

                # Format response
                return {
                    "status": "success",
                    "activities": [
                        {
                            "id": str(a[0]),
                            "timestamp": a[11].isoformat(),
                            "type": a[1],
                            "priority": a[9],
                            "data": {
                                "summary": a[3],
                                "details": a[4],  # Already JSONB, returns as dict
                                "symbol": a[8],
                                "importance": a[10],
                                "trade_id": str(a[5]) if a[5] else None,
                                "trade_type": a[6]
                            }
                        }
                        for a in activities
                    ],
                    "count": len(activities)
                }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get activities for config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve activities: {str(e)}")


@router.get("/{config_id}/balance-series")
async def get_balance_series(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Get cumulative P&L over time for timeline chart.

    Reconstructs P&L history from all closed trades (paper, live, aster).
    Chart starts at $0 and shows cumulative realized P&L.
    Works for all trade types, not just paper trading.

    Returns:
    {
        "status": "success",
        "balance_series": [
            {"timestamp": "2025-11-01T00:00:00Z", "balance": 0},
            {"timestamp": "2025-11-01T14:23:00Z", "balance": 125.50},
            {"timestamp": "2025-11-01T18:45:00Z", "balance": 75.50}
        ],
        "current_balance": 75.50,
        "initial_balance": 0
    }
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Verify ownership
                cur.execute("""
                    SELECT user_id, created_at FROM configurations WHERE config_id = %s
                """, (config_id,))
                config = cur.fetchone()

                if not config:
                    raise HTTPException(status_code=404, detail="Configuration not found")

                if config[0] != current_user.user_id:
                    raise HTTPException(status_code=403, detail="Not authorized")

                config_created_at = config[1]

                # Get closed paper trades from database
                cur.execute("""
                    SELECT closed_at, realized_pnl
                    FROM paper_trades
                    WHERE config_id = %s AND status = 'closed' AND closed_at IS NOT NULL
                    ORDER BY closed_at
                """, (config_id,))
                paper_trades = cur.fetchall()

        # Get Aster trades from API (if user is trading on Aster)
        aster_service = AsterDEXV3LiveTradingService()
        aster_trades_raw = await aster_service.get_user_trades(limit=1000)

        # Build unified trade list with timestamps and P&L
        all_trades = []

        # Add paper trades
        for trade in paper_trades:
            closed_at, realized_pnl = trade
            all_trades.append({
                "timestamp": closed_at,
                "pnl": float(realized_pnl)
            })

        # Add Aster trades (filter by config if needed - for now include all)
        if aster_trades_raw:
            for aster_trade in aster_trades_raw:
                # Aster trades have 'time' in milliseconds
                trade_time_ms = aster_trade.get('time', 0)
                trade_time = datetime.fromtimestamp(trade_time_ms / 1000, tz=timezone.utc) if trade_time_ms else None
                realized_pnl = float(aster_trade.get('realizedPnl', 0))

                if trade_time:
                    all_trades.append({
                        "timestamp": trade_time,
                        "pnl": realized_pnl
                    })

        # Sort all trades by timestamp
        all_trades.sort(key=lambda x: x['timestamp'])

        if not all_trades:
            # No closed trades yet - return flat $0 line
            return {
                "status": "success",
                "balance_series": [
                    {"timestamp": config_created_at.isoformat(), "balance": 0},
                    {"timestamp": datetime.utcnow().isoformat(), "balance": 0}
                ],
                "current_balance": 0,
                "initial_balance": 0
            }

        # Build cumulative P&L series starting at $0
        pnl_points = [
            {
                "timestamp": config_created_at.isoformat(),
                "balance": 0
            }
        ]

        cumulative_pnl = 0.0
        for trade in all_trades:
            cumulative_pnl += trade['pnl']
            pnl_points.append({
                "timestamp": trade['timestamp'].isoformat(),
                "balance": cumulative_pnl
            })

        # Add current P&L as final point
        pnl_points.append({
            "timestamp": datetime.utcnow().isoformat(),
            "balance": cumulative_pnl
        })

        return {
            "status": "success",
            "balance_series": pnl_points,
            "current_balance": cumulative_pnl,
            "initial_balance": 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get balance series for config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve balance series: {str(e)}")


@router.get("/{config_id}/metadata")
async def get_timeline_metadata(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Get bot/agent metadata for timeline header display.

    Returns bot name, type, performance metrics from all trade types (paper, live, aster).
    Metrics calculated from closed trades across all sources.

    Returns:
    {
        "status": "success",
        "metadata": {
            "botName": "RSI Scalper v2",
            "configType": "scheduled_trading",
            "startingBalance": 0,
            "currentBalance": 125.50,  # Cumulative P&L
            "totalTrades": 12,
            "winRate": 66.7,
            "performance": 125.50,  # Cumulative P&L
            "createdAt": "2025-11-01T00:00:00Z"
        }
    }
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Verify ownership
                cur.execute("""
                    SELECT user_id FROM configurations WHERE config_id = %s
                """, (config_id,))
                config = cur.fetchone()

                if not config:
                    raise HTTPException(status_code=404, detail="Configuration not found")

                if config[0] != current_user.user_id:
                    raise HTTPException(status_code=403, detail="Not authorized")

                # Get config info
                cur.execute("""
                    SELECT config_name, config_type, created_at
                    FROM configurations
                    WHERE config_id = %s
                """, (config_id,))
                config_row = cur.fetchone()

                # Get paper trade metrics
                cur.execute("""
                    SELECT
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN realized_pnl >= 0 THEN 1 ELSE 0 END) as wins,
                        SUM(realized_pnl) as total_pnl
                    FROM paper_trades
                    WHERE config_id = %s AND status = 'closed'
                """, (config_id,))
                paper_metrics = cur.fetchone()

        # Get Aster trade metrics from API
        aster_service = AsterDEXV3LiveTradingService()
        aster_trades = await aster_service.get_user_trades(limit=1000)

        # Combine metrics
        paper_total = paper_metrics[0] or 0
        paper_wins = paper_metrics[1] or 0
        paper_pnl = float(paper_metrics[2]) if paper_metrics[2] else 0.0

        aster_total = len(aster_trades) if aster_trades else 0
        aster_wins = sum(1 for t in (aster_trades or []) if float(t.get('realizedPnl', 0)) >= 0)
        aster_pnl = sum(float(t.get('realizedPnl', 0)) for t in (aster_trades or []))

        total_trades = paper_total + aster_total
        win_trades = paper_wins + aster_wins
        total_pnl = paper_pnl + aster_pnl

        win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0

        return {
            "status": "success",
            "metadata": {
                "botName": config_row[0],
                "configType": config_row[1],
                "startingBalance": 0,
                "currentBalance": total_pnl,
                "totalTrades": total_trades,
                "winRate": round(win_rate, 1),
                "performance": total_pnl,  # Cumulative P&L (paper + aster)
                "createdAt": config_row[2].isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get timeline metadata for config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metadata: {str(e)}")
