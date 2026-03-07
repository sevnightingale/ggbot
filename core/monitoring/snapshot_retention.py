"""
Account Snapshots Tiered Retention

Deletes old snapshots to prevent unbounded table growth.

Retention tiers:
- 0-7 days: full resolution (every 5 min, as written by monitor)
- 7-30 days: 1 per hour per config (keep latest per hour)
- 30+ days: 1 per day per config (keep latest per day)

Runs daily at 3am UTC via ggbot_scheduler.py.
Batched DELETEs to avoid long-running transactions and excessive WAL.
"""

from core.common.db import get_db_connection
from core.common.logger import logger

BATCH_SIZE = 10000


async def run_snapshot_retention():
    """Delete old snapshots, keeping tiered resolution."""
    logger.info("Starting account_snapshots retention cleanup")

    total_deleted = 0

    # Phase 1: 7-30 days old -> keep 1 per hour per config
    phase1_deleted = _delete_batched("""
        DELETE FROM account_snapshots
        WHERE snapshot_id IN (
            SELECT snapshot_id FROM (
                SELECT snapshot_id,
                       ROW_NUMBER() OVER (
                           PARTITION BY config_id, date_trunc('hour', timestamp)
                           ORDER BY timestamp DESC
                       ) as rn
                FROM account_snapshots
                WHERE timestamp < NOW() - INTERVAL '7 days'
                  AND timestamp >= NOW() - INTERVAL '30 days'
            ) ranked
            WHERE rn > 1
            LIMIT %s
        )
    """)
    total_deleted += phase1_deleted
    logger.info(f"Retention phase 1 (7-30d hourly): deleted {phase1_deleted} snapshots")

    # Phase 2: 30+ days old -> keep 1 per day per config
    phase2_deleted = _delete_batched("""
        DELETE FROM account_snapshots
        WHERE snapshot_id IN (
            SELECT snapshot_id FROM (
                SELECT snapshot_id,
                       ROW_NUMBER() OVER (
                           PARTITION BY config_id, date_trunc('day', timestamp)
                           ORDER BY timestamp DESC
                       ) as rn
                FROM account_snapshots
                WHERE timestamp < NOW() - INTERVAL '30 days'
            ) ranked
            WHERE rn > 1
            LIMIT %s
        )
    """)
    total_deleted += phase2_deleted
    logger.info(f"Retention phase 2 (30d+ daily): deleted {phase2_deleted} snapshots")

    logger.info(f"Snapshot retention complete: {total_deleted} total rows deleted")
    return total_deleted


def _delete_batched(delete_sql: str) -> int:
    """Execute a DELETE statement in batches, returning total rows deleted."""
    total = 0
    while True:
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(delete_sql, (BATCH_SIZE,))
                    deleted = cur.rowcount
                    conn.commit()

            total += deleted
            if deleted < BATCH_SIZE:
                break  # No more rows to delete in this phase

            logger.debug(f"Retention batch: deleted {deleted} rows (total so far: {total})")

        except Exception as e:
            logger.error(f"Retention batch failed after {total} rows: {e}")
            break

    return total
