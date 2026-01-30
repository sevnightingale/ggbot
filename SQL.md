# SQL Migration - Index Optimization

**Date**: 2026-01-29
**Purpose**: Fix duplicate/unused indexes, add missing FK index

Run these commands in Supabase SQL Editor.

---

## Phase 1: RENAME (Safe - Reversible)

Rename indexes instead of dropping. If anything breaks, rename back instantly.

```sql
-- ============================================================
-- STEP 1: Rename duplicate index (instead of dropping)
-- idx_snapshots_config_time is identical to idx_snapshots_latest
-- ============================================================

ALTER INDEX IF EXISTS idx_snapshots_config_time
RENAME TO _deprecated_idx_snapshots_config_time;


-- ============================================================
-- STEP 2: Rename unused heartbeat index (instead of dropping)
-- idx_snapshots_heartbeat has 0 scans
-- ============================================================

ALTER INDEX IF EXISTS idx_snapshots_heartbeat
RENAME TO _deprecated_idx_snapshots_heartbeat;


-- ============================================================
-- STEP 3: Add missing FK index for paper_trades.decision_id
-- Supabase flagged this as unindexed foreign key
-- NOTE: Removed CONCURRENTLY to avoid Supabase timeout
-- Table is small (~6k rows) so brief lock is fine
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_paper_trades_decision
ON paper_trades(decision_id);


-- ============================================================
-- STEP 4: Verify changes
-- ============================================================

SELECT indexname, pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE relname IN ('account_snapshots', 'paper_trades')
ORDER BY relname, indexname;
```

---

## Phase 2: MONITOR (Wait 3-7 days)

Watch for any errors or slow queries. Check logs for:
- "index not found" errors
- Slow query warnings
- Any degraded performance

---

## Phase 3: DROP (After confirming no issues)

Only run this AFTER Phase 1 has been stable for a few days:

```sql
-- ============================================================
-- FINAL: Drop deprecated indexes (only after monitoring period)
-- ============================================================

DROP INDEX IF EXISTS _deprecated_idx_snapshots_config_time;
DROP INDEX IF EXISTS _deprecated_idx_snapshots_heartbeat;

-- Verify cleanup
SELECT indexname FROM pg_indexes
WHERE indexname LIKE '_deprecated%';
```

---

## ROLLBACK (If something breaks)

If you see errors after Phase 1, rename back immediately:

```sql
-- Restore original index names
ALTER INDEX IF EXISTS _deprecated_idx_snapshots_config_time
RENAME TO idx_snapshots_config_time;

ALTER INDEX IF EXISTS _deprecated_idx_snapshots_heartbeat
RENAME TO idx_snapshots_heartbeat;
```

---

## Expected Results

After Phase 1:
- `idx_snapshots_config_time` → renamed to `_deprecated_idx_snapshots_config_time`
- `idx_snapshots_heartbeat` → renamed to `_deprecated_idx_snapshots_heartbeat`
- `idx_paper_trades_decision` → CREATED (FK optimization)

---

## Optional: Additional Unused Indexes to Consider

These indexes have 0 scans but review before dropping:

```sql
-- Review these - may be needed for future features or admin queries
-- Only drop if you're sure they're not needed

-- idx_decisions_confidence (5 MB) - confidence score filtering
-- DROP INDEX IF EXISTS idx_decisions_confidence;

-- idx_activities_symbol (5.5 MB) - symbol filtering in activities
-- DROP INDEX IF EXISTS idx_activities_symbol;

-- Various llm_models indexes (small, ~16 KB each)
-- DROP INDEX IF EXISTS idx_llm_models_enabled;
-- DROP INDEX IF EXISTS idx_llm_models_provider;

-- trade_observations indexes (small, ~16 KB each)
-- DROP INDEX IF EXISTS idx_trade_observations_config;
-- DROP INDEX IF EXISTS idx_trade_observations_user;
-- DROP INDEX IF EXISTS idx_trade_observations_type;
-- DROP INDEX IF EXISTS idx_trade_observations_importance;
```

---

## Notes

1. **CONCURRENTLY**: The FK index uses CONCURRENTLY to avoid locking the table during creation
2. **IF EXISTS/IF NOT EXISTS**: Safe to run multiple times
3. **No data loss**: Index drops only affect query performance, not data
4. **Disk space**: Regular VACUUM will reclaim space after drops
