"""
Snapshot-based timeline endpoints.

Efficient alternative to activities endpoints that make API calls.
Uses account_snapshots table for performance.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from core.common.db import get_db_connection
from core.common.logger import logger

router = APIRouter(prefix="/api/v2/snapshots", tags=["snapshots"])


@router.get("/{config_id}/balance-series")
async def get_snapshot_balance_series(config_id: str) -> Dict[str, Any]:
    """
    Get balance/P&L timeline from snapshots + activities.

    Returns unified timeline combining:
    - 5-minute snapshots (continuous background)
    - Activities with snapshot values (exact timestamps)

    Response format matches /api/v2/activities/{config_id}/balance-series
    for drop-in frontend compatibility.

    Args:
        config_id: Bot configuration ID

    Returns:
        {
            "status": "success",
            "balance_series": [{"timestamp": "...", "balance": 123.45}, ...],
            "current_balance": 123.45,
            "initial_balance": 100.0,
            "mode": "balance" | "pnl"
        }
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Verify config exists and get trading mode
                cur.execute("""
                    SELECT trading_mode, created_at
                    FROM configurations
                    WHERE config_id = %s
                """, (config_id,))
                config = cur.fetchone()

                if not config:
                    raise HTTPException(status_code=404, detail="Config not found")

                trading_mode = config[0]
                config_created = config[1]

                # Determine which field to use based on trading mode
                # Paper: current_balance + margin_used + unrealized_pnl (Total Equity = cash + locked margin + live P&L)
                # Live (Aster/Symphony): total_pnl (P&L from $0, already includes unrealized)
                if trading_mode == "paper":
                    value_field_snapshots = "COALESCE(current_balance + margin_used + unrealized_pnl, total_pnl)"
                    value_field_activities = "COALESCE(account_balance, account_pnl)"
                else:  # aster, symphony, or other live modes
                    value_field_snapshots = "COALESCE(total_pnl, current_balance)"
                    value_field_activities = "COALESCE(account_pnl, account_balance)"

                # Get snapshots
                cur.execute(f"""
                    SELECT
                        timestamp,
                        {value_field_snapshots} as balance
                    FROM account_snapshots
                    WHERE config_id = %s
                    ORDER BY timestamp ASC
                """, (config_id,))
                snapshots = cur.fetchall()

                # Get activities with snapshot values (only those populated)
                cur.execute(f"""
                    SELECT
                        created_at,
                        {value_field_activities} as balance
                    FROM activities
                    WHERE config_id = %s
                      AND (account_balance IS NOT NULL OR account_pnl IS NOT NULL)
                    ORDER BY created_at ASC
                """, (config_id,))
                activities = cur.fetchall()

        # Combine into timeline
        timeline = []

        # Add snapshots
        for snap in snapshots:
            timeline.append({
                "timestamp": snap[0].isoformat(),
                "balance": float(snap[1]) if snap[1] is not None else 0
            })

        # Add activities (only those with balance data)
        for act in activities:
            timeline.append({
                "timestamp": act[0].isoformat(),
                "balance": float(act[1]) if act[1] is not None else 0
            })

        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'])

        # Calculate current and initial balance
        current_balance = timeline[-1]['balance'] if timeline else 0
        initial_balance = timeline[0]['balance'] if timeline else 0

        # Determine mode (Symphony shows P&L, others show balance)
        mode = "pnl" if trading_mode == "symphony" else "balance"

        logger.bind(config_id=config_id).info(
            f"Snapshot balance series: {len(snapshots)} snapshots, "
            f"{len(activities)} activities with balance, "
            f"{len(timeline)} total points"
        )

        return {
            "status": "success",
            "balance_series": timeline,
            "current_balance": current_balance,
            "initial_balance": initial_balance,
            "mode": mode
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.bind(config_id=config_id).error(f"Snapshot balance series failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
