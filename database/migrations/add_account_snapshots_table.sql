-- Unified Account Snapshots Table
-- Stores account state for ALL trading modes (paper, symphony, aster)
-- Enables historical balance/P&L tracking and unified monitoring

CREATE TABLE IF NOT EXISTS account_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID NOT NULL REFERENCES configurations(config_id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    trading_mode VARCHAR(20) NOT NULL CHECK (trading_mode IN ('paper', 'symphony', 'aster')),

    -- Timestamp
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Balance fields (current_balance may be NULL for Symphony if API doesn't provide it)
    current_balance NUMERIC(20, 8),
    available_balance NUMERIC(20, 8),
    margin_used NUMERIC(20, 8),

    -- P&L fields
    total_pnl NUMERIC(20, 8) NOT NULL,
    realized_pnl NUMERIC(20, 8),
    unrealized_pnl NUMERIC(20, 8),

    -- Performance metrics
    total_trades INTEGER NOT NULL DEFAULT 0,
    win_trades INTEGER NOT NULL DEFAULT 0,
    loss_trades INTEGER NOT NULL DEFAULT 0,
    win_rate NUMERIC(5, 4),  -- 0.0000 to 1.0000

    -- Position metrics
    open_positions INTEGER NOT NULL DEFAULT 0,
    position_value NUMERIC(20, 8),
    total_exposure NUMERIC(20, 8),

    -- Advanced metrics (optional, for future use)
    avg_win NUMERIC(20, 8),
    avg_loss NUMERIC(20, 8),
    largest_win NUMERIC(20, 8),
    largest_loss NUMERIC(20, 8),
    sharpe_ratio NUMERIC(10, 4),
    max_drawdown NUMERIC(20, 8),

    -- Raw API response for debugging/auditing
    raw_data JSONB,

    -- Change tracking (for on-change storage optimization)
    balance_change_pct NUMERIC(10, 4),  -- % change since last snapshot
    is_heartbeat BOOLEAN DEFAULT FALSE,  -- True if this is a periodic heartbeat snapshot

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for efficient queries
CREATE INDEX idx_snapshots_config_time ON account_snapshots(config_id, timestamp DESC);
CREATE INDEX idx_snapshots_user_time ON account_snapshots(user_id, timestamp DESC);
CREATE INDEX idx_snapshots_mode_time ON account_snapshots(trading_mode, timestamp DESC);
CREATE INDEX idx_snapshots_heartbeat ON account_snapshots(config_id, is_heartbeat, timestamp DESC);

-- Index for latest snapshot queries (very common)
-- Note: Can't use NOW() in partial index (not immutable), so index all rows
CREATE INDEX idx_snapshots_latest ON account_snapshots(config_id, timestamp DESC);

-- Comments for documentation
COMMENT ON TABLE account_snapshots IS 'Unified account state snapshots for all trading modes (paper/symphony/aster)';
COMMENT ON COLUMN account_snapshots.current_balance IS 'Total account balance (may be NULL for Symphony if API does not provide)';
COMMENT ON COLUMN account_snapshots.is_heartbeat IS 'True for periodic snapshots even when no change (for gap detection)';
COMMENT ON COLUMN account_snapshots.raw_data IS 'Original API response for debugging (paper: DB data, symphony/aster: API JSON)';

-- Retention policy (optional - can be added later)
-- Delete snapshots older than 90 days, except keep 1 daily snapshot
COMMENT ON TABLE account_snapshots IS 'Retention: Keep all snapshots for 90 days, then 1 per day for historical data';
