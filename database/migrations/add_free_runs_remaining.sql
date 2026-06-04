-- Add free_runs_remaining column for per-bot free test runs
-- Each bot gets 3 free manual "Run Once" clicks (in addition to the creation auto-run)

ALTER TABLE configurations
ADD COLUMN IF NOT EXISTS free_runs_remaining INTEGER DEFAULT 3;

-- Set existing bots to 0 free runs (they've been around, fair to start fresh)
-- New bots will get the default of 3
UPDATE configurations
SET free_runs_remaining = 0
WHERE free_runs_remaining IS NULL;
