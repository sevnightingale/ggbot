-- Migration: Add first_run_used column to configurations table
-- Purpose: Track whether a bot has used its free first run (for onboarding flow)
-- Run this in Supabase SQL Editor

ALTER TABLE configurations
ADD COLUMN IF NOT EXISTS first_run_used BOOLEAN DEFAULT FALSE;

-- Add comment for documentation
COMMENT ON COLUMN configurations.first_run_used IS 'Tracks if the free first run has been used (for new user onboarding)';

-- Verify the column was added
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'configurations' AND column_name = 'first_run_used';
