"""
Activities API - Activity Timeline endpoints

Provides activity data for the Canvas-based Activity Timeline viewer.
Endpoints return activities, balance series, and metadata for a specific bot config.
"""

import json
import re
from fastapi import APIRouter, Query, Depends, HTTPException, Response
from typing import Optional, List
from datetime import datetime, timedelta, timezone

from core.auth.supabase_auth import AuthenticatedUser, get_current_user_v2
from core.common.db import get_db_connection
from core.common.logger import logger


router = APIRouter(prefix="/api/v2/activities", tags=["activities"])


# ─────────────────────────────────────────────────────────────────────────────
# Activity Export Constants
# ─────────────────────────────────────────────────────────────────────────────
EXPORT_MAX_RANGE_DAYS = 90
EXPORT_MAX_ROWS = 50_000  # Safety cap against runaway memory

# Columns kept in the export — billing/token fields are intentionally excluded
# so users don't debate costs/usage. `user_id` is also excluded (internal only).
EXPORT_COLUMNS_SQL = """
    activity_id, config_id, activity_type, activity_source,
    summary, details, trade_id, trade_type, decision_id,
    related_symbol, importance, created_at,
    account_balance, account_pnl, total_equity
"""


def _slugify_bot_name(name: Optional[str], config_id: str) -> str:
    """
    Convert a bot name to a filesystem-safe slug for the export filename.

    Rules: lowercase, alphanumeric + hyphens, collapse repeats, max 40 chars.
    Fallback to `bot_{short_id}` if name is empty or produces an empty slug.
    """
    if not name:
        return f"bot_{config_id[:8]}"
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)[:40]
    return slug or f"bot_{config_id[:8]}"


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

        all_trades = []

        # Add paper trades
        for trade in paper_trades:
            closed_at, realized_pnl = trade
            all_trades.append({
                "timestamp": closed_at,
                "pnl": float(realized_pnl)
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

        # Cumulative realized P&L starting from $0 (paper-trade history).
        # (Aster/Symphony balance-mode reconstruction removed — those modes are gone.)
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

        # Performance %: use cost_basis for HL bots (initial + deposits - withdrawals)
        cost_basis = initial_equity
        if trading_mode == 'hyperliquid' and initial_equity > 0:
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT
                                COALESCE(SUM(CASE WHEN activity_type = 'deposit' THEN (details->>'amount_usdc')::numeric ELSE 0 END), 0),
                                COALESCE(SUM(CASE WHEN activity_type = 'withdrawal' THEN (details->>'amount_usdc')::numeric ELSE 0 END), 0)
                            FROM activities
                            WHERE config_id = %s AND activity_type IN ('deposit', 'withdrawal')
                        """, (config_id,))
                        transfer_row = cur.fetchone()
                        if transfer_row:
                            cost_basis = initial_equity + float(transfer_row[0]) - float(transfer_row[1])
            except Exception:
                pass

        if cost_basis > 0 and not is_legacy_live:
            if trading_mode == 'hyperliquid':
                performance_pct = (total_pnl / cost_basis) * 100
            else:
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


# ─────────────────────────────────────────────────────────────────────────────
# Activity Log Export
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{config_id}/export")
async def export_activities(
    config_id: str,
    start_time: str = Query(..., description="ISO timestamp — inclusive start of export range"),
    end_time: str = Query(..., description="ISO timestamp — inclusive end of export range"),
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
):
    """
    Export a bot's activity log as a gzipped JSON file.

    Owner-only. Returns every activity row for the specified config within the
    given time range (up to 90 days max, 50k rows max), including full LLM
    thought details. Billing/token columns are intentionally excluded.

    Query parameters:
        start_time: ISO-8601 timestamp (required) — range start
        end_time:   ISO-8601 timestamp (required) — range end (must be > start, ≤ now)

    Returns:
        200: plain JSON file (application/json)
             Content-Disposition forces a download with filename
             `{slug}_activities_{start}_to_{end}.json`
        400: invalid time params, range > 90 days, end before start, end in future,
             or result set exceeds row cap
        403: authenticated user does not own the config
        404: config not found
        500: query or serialization failure

    Response body (after gunzip):
    {
      "export_metadata": {
        "config_id": "...",
        "bot_name": "...",
        "exported_at": "2026-04-07T10:45:00Z",
        "start_time": "...",
        "end_time": "...",
        "row_count": 2363
      },
      "activities": [
        {
          "activity_id": "...", "config_id": "...", "activity_type": "...",
          "activity_source": "...", "summary": "...", "details": {...},
          "trade_id": "...", "trade_type": "...", "decision_id": "...",
          "related_symbol": "...", "importance": 7, "created_at": "...",
          "account_balance": ..., "account_pnl": ..., "total_equity": ...
        }
      ]
    }

    Note on `details`: this JSONB column passes through untransformed. If any
    future activity type starts storing token counts or costs inside `details`,
    those will leak through — the filter only strips top-level billing columns.
    """
    # ── 1. Parse and validate time range ──────────────────────────────────
    try:
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid start_time or end_time — must be ISO-8601 timestamps",
        )

    # Normalize to UTC if naive
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)

    if end_dt <= start_dt:
        raise HTTPException(
            status_code=400, detail="end_time must be after start_time"
        )
    if end_dt > now + timedelta(minutes=5):  # 5min tolerance for clock skew
        raise HTTPException(
            status_code=400, detail="end_time cannot be in the future"
        )
    if (end_dt - start_dt) > timedelta(days=EXPORT_MAX_RANGE_DAYS):
        raise HTTPException(
            status_code=400,
            detail=f"Time range exceeds {EXPORT_MAX_RANGE_DAYS}-day maximum",
        )

    # ── 2. Ownership check + fetch bot name ──────────────────────────────
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT user_id, config_name
                    FROM configurations
                    WHERE config_id = %s
                    """,
                    (config_id,),
                )
                config_row = cur.fetchone()

                if not config_row:
                    raise HTTPException(
                        status_code=404, detail="Configuration not found"
                    )

                owner_id, bot_name = config_row

                if str(owner_id) != str(current_user.user_id):
                    raise HTTPException(
                        status_code=403,
                        detail="You do not own this bot configuration",
                    )

                # ── 3. Count rows first (cheap with index) ────────────────
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM activities
                    WHERE config_id = %s
                      AND created_at >= %s
                      AND created_at <= %s
                    """,
                    (config_id, start_dt, end_dt),
                )
                row_count = cur.fetchone()[0]

                if row_count > EXPORT_MAX_ROWS:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Export contains {row_count:,} rows, exceeds "
                            f"{EXPORT_MAX_ROWS:,} limit. Narrow the time range."
                        ),
                    )

                # ── 4. Fetch activities ──────────────────────────────────
                cur.execute(
                    f"""
                    SELECT {EXPORT_COLUMNS_SQL}
                    FROM activities
                    WHERE config_id = %s
                      AND created_at >= %s
                      AND created_at <= %s
                    ORDER BY created_at ASC
                    """,
                    (config_id, start_dt, end_dt),
                )
                rows = cur.fetchall()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Activity export query failed for config {config_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to query activities: {str(e)}"
        )

    # ── 5. Transform rows to dicts ───────────────────────────────────────
    activities = []
    for row in rows:
        try:
            activities.append(
                {
                    "activity_id": str(row[0]) if row[0] else None,
                    "config_id": str(row[1]) if row[1] else None,
                    "activity_type": row[2],
                    "activity_source": row[3],
                    "summary": row[4],
                    "details": row[5],  # JSONB → dict (full prompts included)
                    "trade_id": str(row[6]) if row[6] else None,
                    "trade_type": row[7],
                    "decision_id": str(row[8]) if row[8] else None,
                    "related_symbol": row[9],
                    "importance": row[10],
                    "created_at": row[11].isoformat() if row[11] else None,
                    "account_balance": float(row[12]) if row[12] is not None else None,
                    "account_pnl": float(row[13]) if row[13] is not None else None,
                    "total_equity": float(row[14]) if row[14] is not None else None,
                }
            )
        except Exception as e:
            # Don't let one bad row kill the whole export
            logger.warning(
                f"Activity export: skipping malformed row {row[0]} in {config_id}: {e}"
            )
            continue

    # ── 6. Build response payload ────────────────────────────────────────
    payload = {
        "export_metadata": {
            "config_id": config_id,
            "bot_name": bot_name,
            "exported_at": now.isoformat(),
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "row_count": len(activities),
        },
        "activities": activities,
    }

    try:
        body = json.dumps(payload, default=str, indent=2).encode("utf-8")
    except Exception as e:
        logger.error(
            f"Activity export serialization failed for config {config_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to serialize export: {str(e)}"
        )

    # ── 7. Build filename and return ─────────────────────────────────────
    slug = _slugify_bot_name(bot_name, config_id)
    start_date = start_dt.strftime("%Y-%m-%d")
    end_date = end_dt.strftime("%Y-%m-%d")
    filename = f"{slug}_activities_{start_date}_to_{end_date}.json"

    logger.info(
        f"Activity export: {len(activities)} rows, {len(body):,} bytes, "
        f"config={config_id[:8]}, user={str(current_user.user_id)[:8]}"
    )

    return Response(
        content=body,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
