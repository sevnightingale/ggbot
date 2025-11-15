-- Migration: Add snapshot values to activities table
-- Date: 2025-11-15
-- Purpose: Store account balance and P&L from snapshots for efficient timeline chart rendering
-- Related: Snapshot-Based Timeline Chart Integration (Workstream 1)

-- Add new columns to activities table
ALTER TABLE activities
ADD COLUMN account_balance NUMERIC(20, 8),
ADD COLUMN account_pnl NUMERIC(20, 8);

-- Add index for efficient chart queries
CREATE INDEX idx_activities_chart_data
ON activities(config_id, created_at, account_balance);

-- Add column comments for documentation
COMMENT ON COLUMN activities.account_balance IS
'Balance from most recent account snapshot at activity creation time. Used for timeline chart rendering without API calls.';

COMMENT ON COLUMN activities.account_pnl IS
'Total P&L from most recent account snapshot at activity creation time. Used for timeline chart rendering without API calls.';

-- Verify migration
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'activities'
  AND column_name IN ('account_balance', 'account_pnl')
ORDER BY ordinal_position;
