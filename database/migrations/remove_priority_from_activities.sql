-- Remove priority field from activities table
-- Priority was a mistake - activities don't need grouping priority

-- Drop index that uses priority
DROP INDEX IF EXISTS idx_activities_priority;

-- Remove priority column
ALTER TABLE activities DROP COLUMN IF EXISTS priority;

-- Vacuum to reclaim space
VACUUM ANALYZE activities;
