-- Database constraints and indexes for data consistency
-- Migration: 0010_add_constraints_and_indexes.sql

-- Add constraints to prevent inconsistent trade states
ALTER TABLE trades 
ADD CONSTRAINT valid_trade_status_transition 
CHECK (
    (trade_status IN ('open', 'active', 'pending') AND closed_at IS NULL) OR
    (trade_status = 'closed' AND closed_at IS NOT NULL)
);

-- Add trade lifecycle tracking columns
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS last_sync_at TIMESTAMP DEFAULT NOW();

ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS sync_status VARCHAR(20) DEFAULT 'synced';

-- Add unique constraint to account_states (should only be one per user/config/exchange)
ALTER TABLE account_states 
ADD CONSTRAINT unique_account_state 
UNIQUE (user_id, config_id, exchange);

-- Create partial indexes for performance on active trades
CREATE INDEX IF NOT EXISTS idx_trades_active 
ON trades(user_id, config_id, trade_status) 
WHERE trade_status IN ('open', 'active', 'pending');

-- Index for trade reconciliation queries
CREATE INDEX IF NOT EXISTS idx_trades_sync_status 
ON trades(user_id, sync_status, last_sync_at)
WHERE trade_status IN ('open', 'active', 'pending');

-- Index for recent trades (used in reconciliation)
CREATE INDEX IF NOT EXISTS idx_trades_recent 
ON trades(user_id, created_at)
WHERE created_at > NOW() - INTERVAL '1 day';

-- Index for account states by user and exchange
CREATE INDEX IF NOT EXISTS idx_account_states_user_exchange 
ON account_states(user_id, exchange, updated_at);

-- Create position reconciliation tracking table
CREATE TABLE IF NOT EXISTS position_reconciliations (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id),
    trade_id UUID REFERENCES trades(trade_id),
    reconciliation_type VARCHAR(50) NOT NULL, -- 'auto_close', 'size_mismatch', 'validated', etc.
    exchange_data JSONB,
    database_data JSONB,
    resolution JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for reconciliation history
CREATE INDEX IF NOT EXISTS idx_reconciliations_user_time 
ON position_reconciliations(user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_reconciliations_type 
ON position_reconciliations(reconciliation_type, created_at);

-- Add check constraint for confidence scores (0.0 to 1.0)
ALTER TABLE trades 
ADD CONSTRAINT valid_confidence_score 
CHECK (confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0));

-- Add check constraint for leverage (reasonable range)
ALTER TABLE trades 
ADD CONSTRAINT valid_leverage 
CHECK (leverage IS NULL OR (leverage >= 1 AND leverage <= 1000));

-- Add check constraint for positive amounts
ALTER TABLE trades 
ADD CONSTRAINT positive_collateral 
CHECK (collateral_amount IS NULL OR collateral_amount > 0);

-- Ensure proper timestamp ordering
ALTER TABLE trades 
ADD CONSTRAINT valid_trade_timing 
CHECK (closed_at IS NULL OR closed_at >= created_at);

-- Add index for decision engine queries (active trades by user/config)
CREATE INDEX IF NOT EXISTS idx_trades_decision_queries 
ON trades(user_id, config_id, trade_status, created_at)
WHERE trade_status IN ('open', 'active', 'pending');

-- Add index for trading engine position monitoring
CREATE INDEX IF NOT EXISTS idx_trades_monitoring 
ON trades(user_id, exchange, pair, trade_status)
WHERE trade_status IN ('open', 'active', 'pending');

-- Performance index for market data queries
CREATE INDEX IF NOT EXISTS idx_market_data_queries 
ON market_data(user_id, symbol, timeframe, updated_at);

-- Index for configuration lookups
CREATE INDEX IF NOT EXISTS idx_configurations_lookup 
ON configurations(user_id, config_name, config_type);

-- Update existing trades to have sync status
UPDATE trades 
SET sync_status = CASE 
    WHEN trade_status = 'closed' THEN 'synced'
    WHEN created_at > NOW() - INTERVAL '1 hour' THEN 'recent'
    ELSE 'needs_sync'
END
WHERE sync_status IS NULL;

-- Comments for documentation
COMMENT ON CONSTRAINT valid_trade_status_transition ON trades IS 
'Ensures trade status consistency: open trades have no close time, closed trades have close time';

COMMENT ON CONSTRAINT unique_account_state ON account_states IS 
'Ensures only one account state record per user/config/exchange combination';

COMMENT ON TABLE position_reconciliations IS 
'Tracks trade reconciliation events between database and exchange';

COMMENT ON COLUMN trades.last_sync_at IS 
'Timestamp of last reconciliation check with exchange';

COMMENT ON COLUMN trades.sync_status IS 
'Sync status: synced, needs_sync, recent, error';