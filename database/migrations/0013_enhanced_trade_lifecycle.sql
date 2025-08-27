-- =============================================================
-- Enhanced Trade Lifecycle System Migration
-- Migration: 0013_enhanced_trade_lifecycle.sql
-- Adds config_id, TP/SL tracking, and strategy metadata support
-- =============================================================

-- 1. Add missing columns to trades table for decision module compatibility
ALTER TABLE trades
ADD COLUMN config_id UUID REFERENCES configurations(config_id),
ADD COLUMN leverage INTEGER,
ADD COLUMN collateral_amount DECIMAL(20,8),
ADD COLUMN stop_loss DECIMAL(20,8),
ADD COLUMN take_profit DECIMAL(20,8),
ADD COLUMN confidence_score NUMERIC(3,2),
ADD COLUMN reasoning_log TEXT;

-- 2. Enhance trade_orders table for TP/SL tracking
ALTER TABLE trade_orders
ADD COLUMN is_risk_order BOOLEAN DEFAULT FALSE,
ADD COLUMN risk_type VARCHAR(10); -- 'TP', 'SL', NULL

-- 3. Create strategy metadata table for decision context tracking
CREATE TABLE strategy_runs (
    strategy_run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id UUID REFERENCES trades(trade_id) ON DELETE CASCADE,
    config_id UUID REFERENCES configurations(config_id),
    decision_id UUID,
    leverage INTEGER,
    confidence_score NUMERIC(3,2),
    reasoning_log TEXT,
    decision_data JSONB,
    scenario VARCHAR(50), -- 'TRADE_ENTRY', 'TRADE_MANAGEMENT', 'TRADE_EXIT'
    parent_strategy_run_id UUID REFERENCES strategy_runs(strategy_run_id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 4. Create indexes for strategy_runs
CREATE INDEX idx_strategy_runs_trade ON strategy_runs(trade_id);
CREATE INDEX idx_strategy_runs_config ON strategy_runs(config_id);
CREATE INDEX idx_strategy_runs_scenario ON strategy_runs(scenario);
CREATE INDEX idx_strategy_runs_parent ON strategy_runs(parent_strategy_run_id);

-- 5. Create legacy compatibility view for decision module
CREATE OR REPLACE VIEW trades_legacy AS
SELECT 
    trade_id,
    user_id,
    config_id,
    exchange,
    symbol AS pair,                      -- Map symbol to pair
    status AS trade_status,              -- Map status to trade_status
    leverage,
    collateral_amount,
    stop_loss,
    take_profit,
    confidence_score,
    reasoning_log,
    entry_price,
    size_contracts,
    unrealized_pnl AS profit_loss,       -- Map for compatibility
    opened_at AS created_at,             -- Map opened_at to created_at
    closed_at,
    '{}'::jsonb AS execution_details     -- Stub for compatibility
FROM trades;

-- 6. Add comments for documentation
COMMENT ON COLUMN trades.config_id IS 'Configuration ID linking to user trading settings';
COMMENT ON COLUMN trades.leverage IS 'Leverage used for this trade';
COMMENT ON COLUMN trades.collateral_amount IS 'Collateral amount in base currency';
COMMENT ON COLUMN trades.stop_loss IS 'Stop loss price level';
COMMENT ON COLUMN trades.take_profit IS 'Take profit price level';
COMMENT ON COLUMN trades.confidence_score IS 'Decision confidence score (0.0 to 1.0)';
COMMENT ON COLUMN trades.reasoning_log IS 'Decision reasoning for audit trail';

COMMENT ON COLUMN trade_orders.is_risk_order IS 'True if this is a TP/SL order';
COMMENT ON COLUMN trade_orders.risk_type IS 'Type of risk order: TP (take profit) or SL (stop loss)';

COMMENT ON TABLE strategy_runs IS 'Tracks decision context and strategy metadata for trades';
COMMENT ON VIEW trades_legacy IS 'Backward compatibility view mapping new schema to legacy field names';

-- 7. Grant appropriate permissions (adjust as needed)
-- GRANT SELECT ON trades_legacy TO ggbot_user;
-- GRANT ALL ON strategy_runs TO ggbot_user;

-- 8. Verification query to ensure migration success
SELECT 
    'trades' as table_name,
    COUNT(*) as column_count,
    array_agg(column_name ORDER BY ordinal_position) as columns
FROM information_schema.columns
WHERE table_name = 'trades'
UNION ALL
SELECT 
    'trade_orders' as table_name,
    COUNT(*) as column_count,
    array_agg(column_name ORDER BY ordinal_position) as columns
FROM information_schema.columns
WHERE table_name = 'trade_orders'
UNION ALL
SELECT 
    'strategy_runs' as table_name,
    COUNT(*) as column_count,
    array_agg(column_name ORDER BY ordinal_position) as columns
FROM information_schema.columns
WHERE table_name = 'strategy_runs';