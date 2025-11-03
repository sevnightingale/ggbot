"""
Activities API - Activity Timeline endpoints

Provides activity data for the Canvas-based Activity Timeline viewer.
Endpoints return activities, balance series, and metadata for a specific bot config.
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional, List
from datetime import datetime

from core.auth.dependencies import get_current_user
from core.common.db import get_db_connection
from core.common.logger import logger


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
    user: dict = Depends(get_current_user)
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

                if config[0] != user['id']:
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
    user: dict = Depends(get_current_user)
):
    """
    Get account balance over time for equity curve visualization.

    Reconstructs balance history from closed trades to show equity curve
    on the activity timeline. Used by ActivityTimelineViewer for the chart background.

    Returns:
    {
        "status": "success",
        "balance_series": [
            {"timestamp": "2025-11-01T00:00:00Z", "balance": 10000},
            {"timestamp": "2025-11-01T14:23:00Z", "balance": 10125.50}
        ],
        "current_balance": 10125.50,
        "initial_balance": 10000
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

                if config[0] != user['id']:
                    raise HTTPException(status_code=403, detail="Not authorized")

                # Get account info
                cur.execute("""
                    SELECT initial_balance, current_balance, created_at
                    FROM paper_accounts
                    WHERE config_id = %s
                """, (config_id,))
                account = cur.fetchone()

                if not account:
                    # No paper account yet (probably new bot or live-only)
                    return {
                        "status": "success",
                        "balance_series": [],
                        "current_balance": 10000,
                        "initial_balance": 10000
                    }

                # Get all closed trades for balance reconstruction
                cur.execute("""
                    SELECT closed_at, realized_pnl
                    FROM paper_trades
                    WHERE config_id = %s AND status = 'closed'
                    ORDER BY closed_at
                """, (config_id,))
                trades = cur.fetchall()

                # Reconstruct balance over time
                initial_balance = float(account[0])
                current_balance = float(account[1])
                account_created_at = account[2]

                balance_points = [
                    {
                        "timestamp": account_created_at.isoformat(),
                        "balance": initial_balance
                    }
                ]

                # Add balance point after each closed trade
                running_balance = initial_balance
                for trade in trades:
                    closed_at, realized_pnl = trade
                    running_balance += float(realized_pnl)
                    balance_points.append({
                        "timestamp": closed_at.isoformat(),
                        "balance": running_balance
                    })

                # Add current balance as final point
                balance_points.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "balance": current_balance
                })

                return {
                    "status": "success",
                    "balance_series": balance_points,
                    "current_balance": current_balance,
                    "initial_balance": initial_balance
                }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get balance series for config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve balance series: {str(e)}")


@router.get("/{config_id}/metadata")
async def get_timeline_metadata(
    config_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get bot/agent metadata for timeline header display.

    Returns bot name, type, performance metrics for displaying at top of timeline.
    Used by ActivityTimelineViewer for the header information.

    Returns:
    {
        "status": "success",
        "metadata": {
            "botName": "RSI Scalper v2",
            "configType": "scheduled_trading",
            "startingBalance": 10000,
            "currentBalance": 10125.50,
            "totalTrades": 12,
            "winRate": 66.7,
            "performance": 1.26,
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

                if config[0] != user['id']:
                    raise HTTPException(status_code=403, detail="Not authorized")

                # Get config info
                cur.execute("""
                    SELECT config_name, config_type, created_at
                    FROM configurations
                    WHERE config_id = %s
                """, (config_id,))
                config_row = cur.fetchone()

                # Get account metrics
                cur.execute("""
                    SELECT
                        current_balance,
                        initial_balance,
                        total_trades,
                        win_trades,
                        loss_trades,
                        total_pnl
                    FROM paper_accounts
                    WHERE config_id = %s
                """, (config_id,))
                account = cur.fetchone()

                if not account:
                    # No trades yet
                    win_rate = 0
                    performance = 0
                    current_balance = 10000
                    initial_balance = 10000
                    total_trades = 0
                else:
                    current_balance = float(account[0])
                    initial_balance = float(account[1])
                    total_trades = account[2]
                    win_trades = account[3]

                    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
                    performance = ((current_balance - initial_balance) / initial_balance) * 100

                return {
                    "status": "success",
                    "metadata": {
                        "botName": config_row[0],
                        "configType": config_row[1],
                        "startingBalance": initial_balance,
                        "currentBalance": current_balance,
                        "totalTrades": total_trades,
                        "winRate": round(win_rate, 1),
                        "performance": round(performance, 2),
                        "createdAt": config_row[2].isoformat()
                    }
                }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get timeline metadata for config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metadata: {str(e)}")
