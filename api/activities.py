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
from trading.live.symphony_service import SymphonyLiveTradingService


router = APIRouter(prefix="/api/v2/activities", tags=["activities"])


@router.get("/{config_id}")
async def get_activities(
    config_id: str,
    start_time: Optional[str] = Query(None, description="ISO timestamp filter start"),
    end_time: Optional[str] = Query(None, description="ISO timestamp filter end"),
    activity_types: Optional[List[str]] = Query(None, description="Filter by activity types"),
    trade_id: Optional[str] = Query(None, description="Filter by specific trade"),
    min_importance: int = Query(1, ge=1, le=10, description="Minimum importance level"),
    limit: int = Query(500, ge=1, le=1000, description="Max activities to return")
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
        # Verify config exists (no auth required for public viewing)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id FROM configurations
                    WHERE config_id = %s
                """, (config_id,))
                config = cur.fetchone()

                if not config:
                    raise HTTPException(status_code=404, detail="Configuration not found")

                # Build query with filters
                query = """
                    SELECT
                        activity_id, activity_type, activity_source, summary, details,
                        trade_id, trade_type, decision_id, related_symbol,
                        importance, created_at, platform_cost_usd
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
                            "timestamp": a[10].isoformat(),
                            "type": a[1],
                            "priority": a[9],  # Use importance as priority for frontend compatibility
                            "data": {
                                "summary": a[3],
                                "details": a[4],  # Already JSONB, returns as dict
                                "symbol": a[8],
                                "importance": a[9],
                                "trade_id": str(a[5]) if a[5] else None,
                                "trade_type": a[6],
                                "platform_cost_usd": float(a[11]) if a[11] else None
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
    mode: str = Query("pnl", description="Chart mode: 'pnl' (cumulative P&L from $0) or 'balance' (actual account balance)")
):
    """
    Get cumulative P&L or account balance over time for timeline chart.

    Reconstructs P&L/balance history from all closed trades (paper, live, aster).

    Modes:
    - pnl: Chart starts at $0 and shows cumulative realized P&L
    - balance: Chart shows actual account balance over time (for Aster, uses current balance - future P&L)

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
        "initial_balance": 0,
        "mode": "pnl"
    }
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Verify config exists (no auth required for public viewing)
                cur.execute("""
                    SELECT user_id, created_at FROM configurations WHERE config_id = %s
                """, (config_id,))
                config = cur.fetchone()

                if not config:
                    raise HTTPException(status_code=404, detail="Configuration not found")

                config_created_at = config[1]

                # Get closed paper trades from database
                cur.execute("""
                    SELECT closed_at, realized_pnl
                    FROM paper_trades
                    WHERE config_id = %s AND status = 'closed' AND closed_at IS NOT NULL
                    ORDER BY closed_at
                """, (config_id,))
                paper_trades = cur.fetchall()

                # Check trading mode
                cur.execute("""
                    SELECT trading_mode FROM configurations WHERE config_id = %s
                """, (config_id,))
                trading_row = cur.fetchone()
                trading_mode = trading_row[0] if trading_row else 'paper'
                is_aster = trading_mode == 'aster'
                is_symphony = trading_mode == 'symphony'

        # Get live trades from API (if Aster or Symphony bot)
        all_trades = []

        # Add paper trades
        for trade in paper_trades:
            closed_at, realized_pnl = trade
            all_trades.append({
                "timestamp": closed_at,
                "pnl": float(realized_pnl)
            })

        # Add Symphony trades (account-wide for this agent)
        if is_symphony:
            symphony_service = SymphonyLiveTradingService()
            symphony_trades = await symphony_service.get_trade_history(config_id, limit=1000)

            for symphony_trade in (symphony_trades or []):
                realized_pnl = float(symphony_trade.get('realized_pnl', 0))

                # Only include trades with actual P&L
                if realized_pnl != 0 and symphony_trade.get('closed_at'):
                    # Symphony trades have timestamps as ISO strings
                    try:
                        trade_time = datetime.fromisoformat(symphony_trade['closed_at'].replace('Z', '+00:00'))
                    except (ValueError, TypeError):
                        continue

                    all_trades.append({
                        "timestamp": trade_time,
                        "pnl": realized_pnl
                    })

        # Add Aster trades (account-wide, only with non-zero P&L)
        if is_aster:
            aster_service = AsterDEXV3LiveTradingService()

            # Use income endpoint (more complete than userTrades)
            # userTrades only shows recent ~7 days, income shows full history
            income_records = await aster_service.get_income_history(
                income_type="REALIZED_PNL",
                start_time=int(config_created_at.timestamp() * 1000),  # From bot creation
                limit=1000
            )

            for income_record in (income_records or []):
                income_amount = float(income_record.get('income', 0))

                # Only include non-zero P&L records
                if income_amount != 0:
                    # Income records have 'time' in milliseconds
                    income_time_ms = income_record.get('time', 0)
                    income_time = datetime.fromtimestamp(income_time_ms / 1000, tz=timezone.utc) if income_time_ms else None

                    if income_time:
                        all_trades.append({
                            "timestamp": income_time,
                            "pnl": income_amount
                        })

        # Sort all trades by timestamp
        all_trades.sort(key=lambda x: x['timestamp'])

        if not all_trades:
            # No closed trades yet - return flat $0 line
            return {
                "status": "success",
                "balance_series": [
                    {"timestamp": config_created_at.isoformat(), "balance": 0},
                    {"timestamp": datetime.now(timezone.utc).isoformat(), "balance": 0}
                ],
                "current_balance": 0,
                "initial_balance": 0
            }

        # Balance mode: Show account balance over time (reconstructed from current balance)
        # Only supported for Aster (Symphony doesn't provide balance)
        if mode == "balance" and is_aster:
            # Get current Aster balance (sum USDT + USDC)
            balance_data = await aster_service._get_account_balance()
            current_balance = 0.0

            if balance_data and isinstance(balance_data, dict):
                # Sum both USDT and USDC (Aster pays profits in USDT, capital may be in USDC)
                assets = balance_data.get('assets', [])
                for asset in assets:
                    if isinstance(asset, dict) and asset.get('asset') in ['USDT', 'USDC']:
                        # crossWalletBalance = settled balance + unrealized P&L for this asset
                        current_balance += float(asset.get('crossWalletBalance', 0))

            if not all_trades:
                # No trades yet - show flat line at current balance
                return {
                    "status": "success",
                    "balance_series": [
                        {"timestamp": config_created_at.isoformat(), "balance": current_balance},
                        {"timestamp": datetime.now(timezone.utc).isoformat(), "balance": current_balance}
                    ],
                    "current_balance": current_balance,
                    "initial_balance": current_balance,
                    "mode": "balance"
                }

            # Calculate starting balance by working backwards from current balance
            # Current balance = starting balance + total P&L
            # Starting balance = current balance - total P&L
            cumulative_pnl = sum(trade['pnl'] for trade in all_trades)
            starting_balance = current_balance - cumulative_pnl

            # Build balance series showing how balance changed with each trade
            balance_points = [
                {"timestamp": config_created_at.isoformat(), "balance": starting_balance}
            ]

            running_balance = starting_balance
            for trade in all_trades:
                running_balance += trade['pnl']
                balance_points.append({
                    "timestamp": trade['timestamp'].isoformat(),
                    "balance": running_balance
                })

            # Add current balance as final point (ensure timestamp is after last trade)
            last_trade_time = all_trades[-1]['timestamp'] if all_trades else config_created_at
            final_timestamp = max(last_trade_time, datetime.now(timezone.utc))
            balance_points.append({
                "timestamp": final_timestamp.isoformat(),
                "balance": current_balance
            })

            return {
                "status": "success",
                "balance_series": balance_points,
                "current_balance": current_balance,
                "initial_balance": starting_balance,
                "mode": "balance"
            }
        else:
            # P&L mode (default): Show cumulative P&L starting from $0
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

            # Add current P&L as final point (ensure timestamp is after last trade)
            last_trade_time = all_trades[-1]['timestamp'] if all_trades else config_created_at
            final_timestamp = max(last_trade_time, datetime.now(timezone.utc))
            pnl_points.append({
                "timestamp": final_timestamp.isoformat(),
                "balance": cumulative_pnl
            })

            return {
                "status": "success",
                "balance_series": pnl_points,
                "current_balance": cumulative_pnl,
                "initial_balance": 0,
                "mode": "pnl"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get balance series for config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve balance series: {str(e)}")


@router.get("/{config_id}/metadata")
async def get_timeline_metadata(
    config_id: str
):
    """
    Get bot/agent metadata for timeline header display.

    Uses account_snapshots as single source of truth (same as SSE dashboard).
    Works for all trading modes: paper, hyperliquid, symphony, aster.

    Returns:
    {
        "status": "success",
        "metadata": {
            "botName": "RSI Scalper v2",
            "startingBalance": 10000.0,
            "currentBalance": 10125.50,  # Total equity (balance + unrealized P&L)
            "totalTrades": 12,
            "winRate": 66.7,  # Percentage (0-100)
            "performance": 1.26,  # Percentage return
            "createdAt": "2025-11-01T00:00:00Z"
        }
    }
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Single query: config + latest snapshot (works for ALL trading modes)
                # Uses account_snapshots as single source of truth (same as SSE dashboard)
                cur.execute("""
                    SELECT
                        c.config_name,
                        c.config_type,
                        c.created_at,
                        c.trading_mode,
                        c.initial_equity,
                        asn.current_balance,
                        asn.unrealized_pnl,
                        asn.total_pnl,
                        asn.total_trades,
                        asn.win_trades,
                        asn.win_rate
                    FROM configurations c
                    LEFT JOIN LATERAL (
                        SELECT current_balance, unrealized_pnl, total_pnl,
                               total_trades, win_trades, win_rate
                        FROM account_snapshots
                        WHERE config_id = c.config_id
                        ORDER BY timestamp DESC
                        LIMIT 1
                    ) asn ON true
                    WHERE c.config_id = %s
                """, (config_id,))
                row = cur.fetchone()

                if not row:
                    raise HTTPException(status_code=404, detail="Configuration not found")

                (config_name, config_type, created_at, trading_mode,
                 initial_equity, current_balance, unrealized_pnl, total_pnl,
                 total_trades, win_trades, win_rate) = row

        # Defaults for bots with no snapshots yet
        trading_mode = trading_mode or 'paper'
        initial_equity = float(initial_equity) if initial_equity else 10000.0
        total_trades = total_trades or 0
        win_trades = win_trades or 0
        total_pnl = float(total_pnl) if total_pnl else 0.0

        # Compute total equity (same formula as SSE dashboard_data.py)
        is_legacy_live = trading_mode in ('symphony', 'aster')
        if is_legacy_live:
            # Legacy live modes: cumulative P&L (no account balance concept)
            current_equity = total_pnl
            starting_balance = 0.0
        else:
            # Paper + Hyperliquid: real account equity
            cb = float(current_balance) if current_balance else initial_equity
            upnl = float(unrealized_pnl) if unrealized_pnl else 0.0
            current_equity = cb + upnl
            starting_balance = initial_equity

        # Win rate: stored as decimal (0-1), display as percentage
        # Same conversion as page.tsx:1241
        win_rate_pct = round(float(win_rate) * 100, 1) if win_rate else 0.0

        # Performance %: same formula as dashboard_data.py:187-188
        if initial_equity > 0 and not is_legacy_live:
            performance_pct = ((current_equity - initial_equity) / initial_equity) * 100
        elif is_legacy_live:
            performance_pct = total_pnl  # Dollar P&L for legacy (no % possible)
        else:
            performance_pct = 0.0

        return {
            "status": "success",
            "metadata": {
                "botName": config_name,  # Consistent camelCase
                "startingBalance": starting_balance,
                "currentBalance": round(current_equity, 2),
                "totalTrades": total_trades,
                "winRate": win_rate_pct,
                "performance": round(performance_pct, 2),
                "createdAt": created_at.isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get timeline metadata for config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metadata: {str(e)}")
