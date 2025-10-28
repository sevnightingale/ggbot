-- ============================================================================
-- GGBot Autonomous Trading Agent - Phase 1 Migration
-- Adds support for agent-created decisions and agent memory storage
-- ============================================================================

-- ============================================================================
-- 1. ADD CREATED_BY COLUMN TO DECISIONS TABLE
-- ============================================================================

-- Check if created_by column exists, if not add it
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'decisions'
        AND column_name = 'created_by'
    ) THEN
        ALTER TABLE decisions
        ADD COLUMN created_by TEXT DEFAULT 'decision_engine_v2';

        -- Backfill existing rows
        UPDATE decisions SET created_by = 'decision_engine_v2' WHERE created_by IS NULL;

        RAISE NOTICE 'Added created_by column to decisions table';
    ELSE
        RAISE NOTICE 'created_by column already exists in decisions table';
    END IF;
END $$;

-- Add index for filtering by creator
CREATE INDEX IF NOT EXISTS idx_decisions_created_by ON decisions(created_by);

-- ============================================================================
-- 2. CREATE AGENT_MEMORY TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID NOT NULL,
    user_id UUID NOT NULL,
    memory_type TEXT NOT NULL CHECK (memory_type IN ('observation', 'learning', 'strategy_test')),
    content TEXT NOT NULL,
    importance INTEGER DEFAULT 5 CHECK (importance BETWEEN 1 AND 10),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add foreign key constraints only if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'agent_memory'
        AND constraint_name = 'agent_memory_config_fkey'
    ) THEN
        ALTER TABLE agent_memory
        ADD CONSTRAINT agent_memory_config_fkey
        FOREIGN KEY (config_id) REFERENCES configurations(config_id) ON DELETE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'agent_memory'
        AND constraint_name = 'agent_memory_user_fkey'
    ) THEN
        ALTER TABLE agent_memory
        ADD CONSTRAINT agent_memory_user_fkey
        FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Enable Row Level Security
ALTER TABLE agent_memory ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist, then create new ones
DROP POLICY IF EXISTS "Users can only access their own agent memory" ON agent_memory;
CREATE POLICY "Users can only access their own agent memory" ON agent_memory
    FOR ALL USING (auth.uid() = user_id);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_agent_memory_config ON agent_memory(config_id);
CREATE INDEX IF NOT EXISTS idx_agent_memory_user ON agent_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_memory_type ON agent_memory(memory_type);
CREATE INDEX IF NOT EXISTS idx_agent_memory_importance ON agent_memory(importance DESC);
CREATE INDEX IF NOT EXISTS idx_agent_memory_created_at ON agent_memory(created_at DESC);

-- Composite index for common queries (user + config + recent)
CREATE INDEX IF NOT EXISTS idx_agent_memory_user_config_created
    ON agent_memory(user_id, config_id, created_at DESC);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify tables
DO $$
BEGIN
    RAISE NOTICE '✓ Migration complete!';
    RAISE NOTICE '✓ decisions.created_by column added';
    RAISE NOTICE '✓ agent_memory table created';
    RAISE NOTICE '✓ RLS policies enabled';
    RAISE NOTICE '✓ Indexes created for performance';
END $$;
