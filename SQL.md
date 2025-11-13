-- Drop priority field and add token tracking to activities table

-- Remove priority column and index
DROP INDEX IF EXISTS idx_activities_priority;
ALTER TABLE activities DROP COLUMN IF EXISTS priority;

-- Add token tracking columns
ALTER TABLE activities
ADD COLUMN IF NOT EXISTS provider VARCHAR(50),
ADD COLUMN IF NOT EXISTS model VARCHAR(100),
ADD COLUMN IF NOT EXISTS thinking_mode BOOLEAN,
ADD COLUMN IF NOT EXISTS input_tokens INTEGER,
ADD COLUMN IF NOT EXISTS output_tokens INTEGER,
ADD COLUMN IF NOT EXISTS reasoning_tokens INTEGER,
ADD COLUMN IF NOT EXISTS provider_cost_usd NUMERIC(10, 6),
ADD COLUMN IF NOT EXISTS platform_cost_usd NUMERIC(10, 6),
ADD COLUMN IF NOT EXISTS stripe_reported BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS stripe_reported_at TIMESTAMP WITH TIME ZONE;

-- Add billing index for efficient Stripe reporting queries
CREATE INDEX IF NOT EXISTS idx_activities_billing
ON activities(user_id, stripe_reported, created_at)
WHERE platform_cost_usd IS NOT NULL;

-- Add index for per-bot spend queries
CREATE INDEX IF NOT EXISTS idx_activities_config_billing
ON activities(config_id, created_at)
WHERE platform_cost_usd IS NOT NULL;
