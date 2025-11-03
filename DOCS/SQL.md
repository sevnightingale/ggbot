-- ============================================================================
-- ACTIVITY TIMELINE MIGRATION
-- ============================================================================
-- Creates the unified activities table for tracking all bot/agent actions
-- Supports: scheduled bots, agents, signal validation
-- Date: 2025-11-03
-- ============================================================================

-- Ensure uuid extension is enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create activities table
CREATE TABLE IF NOT EXISTS activities (
    activity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID NOT NULL REFERENCES configurations(config_id) ON DELETE CASCADE,
    user_id UUID NOT NULL,

    -- Classification
    activity_type TEXT NOT NULL,
    -- Common types across all bot types:
    --   'market_query' - Data extraction/query
    --   'decision_made' - AI decision (enter/wait/exit)
    --   'trade_entry_long' - Long position opened
    --   'trade_entry_short' - Short position opened
    --   'trade_exit' - Position closed
    --   'agent_wait' - Agent waiting period
    --   'analysis' - Market analysis (agent)
    --   'reasoning' - Decision reasoning (agent)
    --   'observation' - Trade observation/learning
    --   'strategy_updated' - Strategy modification
    --   'position_adjusted' - Position size/SL/TP change

    activity_source TEXT NOT NULL,
    -- Values: 'agent_tool', 'scheduled_bot', 'signal_validation', 'system_event', 'user_action'

    -- Content
    summary TEXT NOT NULL CHECK (length(summary) <= 200),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Optional Linking (NULL if not applicable)
    trade_id UUID,
    trade_type TEXT,
    decision_id UUID,
    related_symbol TEXT,

    -- Display Metadata
    priority INT NOT NULL DEFAULT 2 CHECK (priority IN (1,2,3)),
    -- Priority mapping (controls zoom visibility):
    --   1 = High (trades, critical actions) - Always visible
    --   2 = Medium (analysis, queries, decisions) - Visible at 4h zoom and tighter
    --   3 = Low (waits, observations, minor events) - Visible at 1h zoom only

    importance INT NOT NULL DEFAULT 5 CHECK (importance BETWEEN 1 AND 10),
    -- User-facing filtering (1=low, 10=critical)

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Primary index: Config + time-range queries (most common)
CREATE INDEX IF NOT EXISTS idx_activities_config_time
ON activities(config_id, created_at DESC);

-- Trade lifecycle linking
CREATE INDEX IF NOT EXISTS idx_activities_trade
ON activities(trade_id)
WHERE trade_id IS NOT NULL;

-- Activity type filtering
CREATE INDEX IF NOT EXISTS idx_activities_type
ON activities(config_id, activity_type, created_at DESC);

-- Priority-based filtering (zoom levels)
CREATE INDEX IF NOT EXISTS idx_activities_priority
ON activities(config_id, priority, created_at DESC);

-- Decision linking
CREATE INDEX IF NOT EXISTS idx_activities_decision
ON activities(decision_id)
WHERE decision_id IS NOT NULL;

-- User-wide queries (analytics)
CREATE INDEX IF NOT EXISTS idx_activities_user
ON activities(user_id, created_at DESC);

-- Symbol-based filtering
CREATE INDEX IF NOT EXISTS idx_activities_symbol
ON activities(config_id, related_symbol, created_at DESC)
WHERE related_symbol IS NOT NULL;

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;

-- User isolation policy
CREATE POLICY activities_user_isolation ON activities
    FOR ALL
    USING (user_id = auth.uid());

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check table was created successfully
SELECT
    tablename,
    tableowner,
    tablespace
FROM pg_tables
WHERE schemaname = 'public' AND tablename = 'activities';

-- Check indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public' AND tablename = 'activities'
ORDER BY indexname;

-- Check RLS is enabled
SELECT
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public' AND tablename = 'activities';

-- Check policies
SELECT
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE schemaname = 'public' AND tablename = 'activities';
