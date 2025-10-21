-- Migration 016: Symphony Live Trading Support
-- Description: Add database support for Symphony.io live trading integration
-- Date: 2025-01-19
-- Author: Symphony Integration Day 2

-- =============================================================================
-- PART 1: Extend user_profiles table with Symphony account credentials
-- =============================================================================

-- Add Symphony vault reference and smart account storage
ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS symphony_vault_id UUID,
ADD COLUMN IF NOT EXISTS symphony_smart_account VARCHAR(42);

-- Add comments for documentation
COMMENT ON COLUMN user_profiles.symphony_vault_id IS 'Foreign key to vault.secrets - stores encrypted Symphony API key';
COMMENT ON COLUMN user_profiles.symphony_smart_account IS 'Symphony smart account address (0x...) for future balance queries';

-- =============================================================================
-- PART 2: Extend configurations table with trading mode and Symphony agent
-- =============================================================================

-- Add trading mode and Symphony agent ID to bot configurations
ALTER TABLE configurations
ADD COLUMN IF NOT EXISTS symphony_agent_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS trading_mode VARCHAR(20) DEFAULT 'paper';

-- Add constraint to ensure trading_mode is valid
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'configurations_trading_mode_check'
    ) THEN
        ALTER TABLE configurations
        ADD CONSTRAINT configurations_trading_mode_check
        CHECK (trading_mode IN ('paper', 'live'));
    END IF;
END $$;

-- Add comments for documentation
COMMENT ON COLUMN configurations.symphony_agent_id IS 'Symphony agent ID for live trading bots (required when trading_mode=live)';
COMMENT ON COLUMN configurations.trading_mode IS 'Trading mode: paper (simulated) or live (real money). Locked at creation, cannot be changed.';

-- =============================================================================
-- PART 3: Create live_trades table for Symphony trade tracking
-- =============================================================================

-- Create live_trades table with minimal schema (Symphony is source of truth)
CREATE TABLE IF NOT EXISTS live_trades (
    -- Primary key: Symphony batch ID
    batch_id VARCHAR(255) PRIMARY KEY,

    -- Link to bot configuration
    config_id UUID NOT NULL REFERENCES configurations(config_id) ON DELETE CASCADE,

    -- Link to AI decision (for audit trail)
    decision_id UUID REFERENCES decisions(decision_id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMP  -- NULL = position is still open
);

-- Add unique constraint for idempotency (prevents duplicate trades on retries)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'live_trades_decision_id_unique'
    ) THEN
        ALTER TABLE live_trades
        ADD CONSTRAINT live_trades_decision_id_unique
        UNIQUE (decision_id);
    END IF;
END $$;

-- Create index for main query pattern: "get all trades for this bot"
CREATE INDEX IF NOT EXISTS idx_live_trades_config ON live_trades(config_id);

-- Create index for finding open positions quickly
CREATE INDEX IF NOT EXISTS idx_live_trades_open ON live_trades(config_id, closed_at)
WHERE closed_at IS NULL;

-- Add table comment
COMMENT ON TABLE live_trades IS 'Minimal audit trail linking Symphony batch_id to ggbots decision_id. Symphony is source of truth for P&L, prices, and position status.';
COMMENT ON COLUMN live_trades.batch_id IS 'Symphony batch ID (primary key from Symphony API)';
COMMENT ON COLUMN live_trades.config_id IS 'Which bot opened this trade';
COMMENT ON COLUMN live_trades.decision_id IS 'Link to AI decision for audit trail. Unique constraint prevents duplicate trades on network timeouts.';
COMMENT ON COLUMN live_trades.created_at IS 'When position was opened via Symphony';
COMMENT ON COLUMN live_trades.closed_at IS 'When position was closed. NULL = still open.';

-- =============================================================================
-- VERIFICATION QUERIES (Uncomment to test after running migration)
-- =============================================================================

-- Verify user_profiles columns were added
-- SELECT column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'user_profiles'
-- AND column_name IN ('symphony_vault_id', 'symphony_smart_account');

-- Verify configurations columns were added
-- SELECT column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'configurations'
-- AND column_name IN ('symphony_agent_id', 'trading_mode');

-- Verify live_trades table was created
-- SELECT table_name FROM information_schema.tables
-- WHERE table_name = 'live_trades';

-- Verify indexes were created
-- SELECT indexname FROM pg_indexes
-- WHERE tablename = 'live_trades';

-- =============================================================================
-- ROLLBACK INSTRUCTIONS (If you need to undo this migration)
-- =============================================================================

/*
-- Rollback Part 3: Drop live_trades table
DROP TABLE IF EXISTS live_trades CASCADE;

-- Rollback Part 2: Remove configurations columns
ALTER TABLE configurations
DROP COLUMN IF EXISTS symphony_agent_id,
DROP COLUMN IF EXISTS trading_mode;

-- Rollback Part 1: Remove user_profiles columns
ALTER TABLE user_profiles
DROP COLUMN IF EXISTS symphony_vault_id,
DROP COLUMN IF EXISTS symphony_smart_account;
*/
