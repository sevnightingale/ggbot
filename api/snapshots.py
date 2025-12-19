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
    Get AI's consciousness timeline - ACTIVITIES ONLY.

    This chart represents the AI's subjective experience, not objective reality.
    Each point = a moment when the AI observed its account state.
    Between points = the AI was "asleep" (not conscious of what happened).

    Time spacing is irrelevant - this is a sequence of observations, not a clock.

    NEW PARADIGM:
    - Query ONLY activities (no snapshots)
    - Each activity has total_equity from Redis cache (updated every 5s)
    - Chart connects the AI's discrete moments of awareness

    Args:
        config_id: Bot configuration ID

    Returns:
        {
            "status": "success",
            "equity_series": [{"timestamp": "...", "total_equity": 123.45}, ...],
            "current_equity": 123.45,
            "initial_equity": 10000.0,
            "mode": "equity"
        }

    Note: Response keys updated from 'balance' to 'total_equity' for clarity.
          Data comes from activities.total_equity column.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Verify config exists
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

                # Get activities ONLY - these are the AI's conscious moments
                # total_equity field contains total equity (from Redis cache)
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

        # Build timeline from AI's observations only
        timeline = []

        # Each activity = one moment of AI consciousness
        for act in activities:
            timeline.append({
                "timestamp": act[0].isoformat(),
                "total_equity": float(act[1]) if act[1] is not None else 0
            })

        # Sort by timestamp (though order should already be correct)
        timeline.sort(key=lambda x: x['timestamp'])

        # Deduplicate by Unix second (lightweight-charts requires unique timestamps)
        # Multiple activities in same second (parallel queries) have same equity - keep last
        if timeline:
            from datetime import datetime
            seen_seconds = {}
            for point in timeline:
                ts = datetime.fromisoformat(point['timestamp'].replace('Z', '+00:00'))
                unix_second = int(ts.timestamp())
                seen_seconds[unix_second] = point  # Last value wins
            timeline = list(seen_seconds.values())
            timeline.sort(key=lambda x: x['timestamp'])

        # Calculate current and initial equity
        current_equity = timeline[-1]['total_equity'] if timeline else 10000.0
        initial_equity = timeline[0]['total_equity'] if timeline else 10000.0

        # Mode is always "equity" - total account value
        mode = "equity"

        logger.bind(config_id=config_id).info(
            f"AI consciousness timeline: {len(activities)} moments of awareness"
        )

        return {
            "status": "success",
            "equity_series": timeline,
            "current_equity": current_equity,
            "initial_equity": initial_equity,
            "mode": mode,
            # Legacy keys for backward compatibility (deprecated)
            "balance_series": timeline,
            "current_balance": current_equity,
            "initial_balance": initial_equity
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.bind(config_id=config_id).error(f"Snapshot balance series failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{config_id}/performance-series")
async def get_performance_series(config_id: str) -> Dict[str, Any]:
    """
    Get objective performance timeline - ACCOUNT_SNAPSHOTS ONLY.

    This chart represents objective 5-minute performance tracking,
    regardless of bot activity. Every 5 minutes the Universal Account
    Monitor records a snapshot of the account state.

    Time spacing is uniform - every 5 minutes exactly.

    Args:
        config_id: Bot configuration ID

    Returns:
        {
            "status": "success",
            "equity_series": [{"timestamp": "...", "total_equity": 123.45}, ...],
            "current_equity": 123.45,
            "initial_equity": 10000.0
        }

    Note: Data comes from account_snapshots table.
          Formula: total_equity = current_balance + unrealized_pnl
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Verify config exists
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

                # Get account snapshots - regular 5-minute intervals
                # Formula: total_equity = current_balance + unrealized_pnl
                cur.execute("""
                    SELECT
                        timestamp,
                        current_balance + COALESCE(unrealized_pnl, 0) as total_equity
                    FROM account_snapshots
                    WHERE config_id = %s
                    ORDER BY timestamp ASC
                """, (config_id,))
                snapshots = cur.fetchall()

        # Build timeline from snapshots
        timeline = []

        for snap in snapshots:
            timeline.append({
                "timestamp": snap[0].isoformat(),
                "total_equity": float(snap[1]) if snap[1] is not None else 0
            })

        # Sort by timestamp (though order should already be correct)
        timeline.sort(key=lambda x: x['timestamp'])

        # Calculate current and initial equity
        current_equity = timeline[-1]['total_equity'] if timeline else 10000.0
        initial_equity = timeline[0]['total_equity'] if timeline else 10000.0

        logger.bind(config_id=config_id).info(
            f"Performance timeline: {len(snapshots)} snapshots (5-min intervals)"
        )

        return {
            "status": "success",
            "equity_series": timeline,
            "current_equity": current_equity,
            "initial_equity": initial_equity
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.bind(config_id=config_id).error(f"Performance series failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
