-- ============================================================================
-- GGBot Autonomous Trading Agent - Trade Observations Migration
-- Replaces agent_memory with trade_observations (post-trade reflection model)
-- ============================================================================

-- ============================================================================
-- 1. DROP OLD AGENT_MEMORY TABLE
-- ============================================================================

DROP TABLE IF EXISTS agent_memory CASCADE;

-- ============================================================================
-- 2. CREATE TRADE_OBSERVATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS trade_observations (
    observation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID NOT NULL REFERENCES configurations(config_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    trade_id UUID NOT NULL REFERENCES paper_trades(trade_id) ON DELETE CASCADE,

    -- Post-trade reflection
    observation_type TEXT NOT NULL CHECK (observation_type IN ('win_analysis', 'loss_analysis')),
    what_went_well TEXT,
    what_went_wrong TEXT,
    predictive_data_points JSONB,  -- Which data points were most useful
    decision_review TEXT,  -- Review of original entry reasoning

    -- Metadata
    trade_pnl DECIMAL(20,8),
    trade_duration_minutes INTEGER,
    importance INTEGER DEFAULT 5 CHECK (importance BETWEEN 1 AND 10),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- 3. ENABLE ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE trade_observations ENABLE ROW LEVEL SECURITY;

-- Drop existing policy if it exists, then create new one
DROP POLICY IF EXISTS "Users can only access their own trade observations" ON trade_observations;
CREATE POLICY "Users can only access their own trade observations" ON trade_observations
    FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- 4. CREATE INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_trade_observations_config ON trade_observations(config_id);
CREATE INDEX IF NOT EXISTS idx_trade_observations_user ON trade_observations(user_id);
CREATE INDEX IF NOT EXISTS idx_trade_observations_trade ON trade_observations(trade_id);
CREATE INDEX IF NOT EXISTS idx_trade_observations_type ON trade_observations(observation_type);
CREATE INDEX IF NOT EXISTS idx_trade_observations_importance ON trade_observations(importance DESC);

-- Composite index for common queries (config + importance + recent)
CREATE INDEX IF NOT EXISTS idx_trade_observations_config_importance_created
    ON trade_observations(config_id, importance DESC, created_at DESC);

-- Composite index for type + created queries
CREATE INDEX IF NOT EXISTS idx_trade_observations_config_type_created
    ON trade_observations(config_id, observation_type, created_at DESC);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✓ Migration complete!';
    RAISE NOTICE '✓ agent_memory table dropped';
    RAISE NOTICE '✓ trade_observations table created';
    RAISE NOTICE '✓ RLS policies enabled';
    RAISE NOTICE '✓ Indexes created for performance';
END $$;
