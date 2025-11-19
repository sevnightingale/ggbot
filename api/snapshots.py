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
            "balance_series": [{"timestamp": "...", "balance": 123.45}, ...],
            "current_balance": 123.45,
            "initial_balance": 10000.0,
            "mode": "equity"
        }
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
                # account_balance field now contains total equity (from Redis cache)
                cur.execute("""
                    SELECT
                        created_at,
                        account_balance as total_equity
                    FROM activities
                    WHERE config_id = %s
                      AND account_balance IS NOT NULL
                    ORDER BY created_at ASC
                """, (config_id,))
                activities = cur.fetchall()

        # Build timeline from AI's observations only
        timeline = []

        # Each activity = one moment of AI consciousness
        for act in activities:
            timeline.append({
                "timestamp": act[0].isoformat(),
                "balance": float(act[1]) if act[1] is not None else 0
            })

        # Sort by timestamp (though order should already be correct)
        timeline.sort(key=lambda x: x['timestamp'])

        # Calculate current and initial equity
        current_balance = timeline[-1]['balance'] if timeline else 10000.0
        initial_balance = timeline[0]['balance'] if timeline else 10000.0

        # Mode is always "equity" - total account value
        mode = "equity"

        logger.bind(config_id=config_id).info(
            f"AI consciousness timeline: {len(activities)} moments of awareness"
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
