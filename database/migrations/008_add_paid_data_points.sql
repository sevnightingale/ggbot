-- Migration 008: Add paid_data_points to user_profiles
-- Adds flexible premium data points array for granular access control
-- Date: 2025-01-04

BEGIN;

-- Add flexible premium data points array to user profiles
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS paid_data_points TEXT[] DEFAULT ARRAY[]::TEXT[];

-- Create index for efficient array searches
CREATE INDEX IF NOT EXISTS idx_user_profiles_paid_data_points ON user_profiles USING GIN (paid_data_points);

-- Add comment for documentation
COMMENT ON COLUMN user_profiles.paid_data_points IS 'Array of premium data point names user has access to (e.g., ["ggShot", "premium_indicator_x"])';

COMMIT;

-- Verify the column was added
SELECT column_name, data_type, column_default
FROM information_schema.columns 
WHERE table_name = 'user_profiles' 
AND column_name = 'paid_data_points';