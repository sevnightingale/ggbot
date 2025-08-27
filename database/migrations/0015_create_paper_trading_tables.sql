-- Migration 0015: Create Paper Trading Tables
-- Creates tables for paper trading engine with Hummingbot API integration
-- Author: Claude Code
-- Date: 2025-08-27

BEGIN;

-- Paper trading accounts (one per config_id)
CREATE TABLE paper_accounts (
    account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID UNIQUE NOT NULL REFERENCES configurations(config_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    initial_balance DECIMAL(20,8) NOT NULL DEFAULT 10000.00,
    current_balance DECIMAL(20,8) NOT NULL DEFAULT 10000.00,
    total_pnl DECIMAL(20,8) NOT NULL DEFAULT 0.00,
    open_positions INTEGER NOT NULL DEFAULT 0,
    total_trades INTEGER NOT NULL DEFAULT 0,
    win_trades INTEGER NOT NULL DEFAULT 0,
    loss_trades INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for paper_accounts
CREATE INDEX idx_paper_accounts_config_id ON paper_accounts(config_id);
CREATE INDEX idx_paper_accounts_user_id ON paper_accounts(user_id);
CREATE INDEX idx_paper_accounts_updated ON paper_accounts(updated_at);

-- Paper trades (extends existing trades table concept)
CREATE TABLE paper_trades (
    trade_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES paper_accounts(account_id) ON DELETE CASCADE,
    config_id UUID NOT NULL REFERENCES configurations(config_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    decision_id UUID,  -- Links back to Decision Module
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('long', 'short')),
    entry_price DECIMAL(20,8) NOT NULL,
    current_price DECIMAL(20,8),
    size_usd DECIMAL(20,8) NOT NULL,
    size_contracts DECIMAL(20,8),
    leverage INTEGER NOT NULL DEFAULT 1 CHECK (leverage > 0 AND leverage <= 100),
    unrealized_pnl DECIMAL(20,8) NOT NULL DEFAULT 0.00,
    realized_pnl DECIMAL(20,8) DEFAULT 0.00,
    fees DECIMAL(20,8) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    stop_loss DECIMAL(20,8),
    take_profit DECIMAL(20,8),
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    reasoning TEXT,
    opened_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    close_reason VARCHAR(50) CHECK (close_reason IN ('take_profit', 'stop_loss', 'manual', 'liquidation')),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for paper_trades
CREATE INDEX idx_paper_trades_config_status ON paper_trades(config_id, status);
CREATE INDEX idx_paper_trades_account_id ON paper_trades(account_id);
CREATE INDEX idx_paper_trades_symbol ON paper_trades(symbol);
CREATE INDEX idx_paper_trades_opened ON paper_trades(opened_at DESC);
CREATE INDEX idx_paper_trades_user_id ON paper_trades(user_id);
CREATE INDEX idx_paper_trades_decision_id ON paper_trades(decision_id);
CREATE INDEX idx_paper_trades_status ON paper_trades(status);

-- Partial index for active trades (performance optimization)
CREATE INDEX idx_paper_trades_open_positions ON paper_trades(config_id, symbol) WHERE status = 'open';

-- Paper orders (audit trail)
CREATE TABLE paper_orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id UUID NOT NULL REFERENCES paper_trades(trade_id) ON DELETE CASCADE,
    order_type VARCHAR(20) NOT NULL CHECK (order_type IN ('market', 'limit', 'stop_loss', 'take_profit')),
    side VARCHAR(10) NOT NULL CHECK (side IN ('buy', 'sell')),
    requested_price DECIMAL(20,8),
    filled_price DECIMAL(20,8) NOT NULL,
    size DECIMAL(20,8) NOT NULL,
    fees DECIMAL(20,8) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) NOT NULL DEFAULT 'filled' CHECK (status IN ('filled', 'cancelled', 'rejected')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    filled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for paper_orders
CREATE INDEX idx_paper_orders_trade_id ON paper_orders(trade_id);
CREATE INDEX idx_paper_orders_created ON paper_orders(created_at DESC);
CREATE INDEX idx_paper_orders_type ON paper_orders(order_type);

-- Create trigger to update paper_accounts.updated_at on changes
CREATE OR REPLACE FUNCTION update_paper_account_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE paper_accounts 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE account_id = NEW.account_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for paper_trades changes
CREATE TRIGGER trigger_update_paper_account_on_trade_change
    AFTER INSERT OR UPDATE OR DELETE ON paper_trades
    FOR EACH ROW
    EXECUTE FUNCTION update_paper_account_timestamp();

-- Create function to update paper_trades.last_updated automatically
CREATE OR REPLACE FUNCTION update_paper_trade_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for paper_trades timestamp updates
CREATE TRIGGER trigger_paper_trades_last_updated
    BEFORE UPDATE ON paper_trades
    FOR EACH ROW
    EXECUTE FUNCTION update_paper_trade_timestamp();

-- Add comments to tables for documentation
COMMENT ON TABLE paper_accounts IS 'Paper trading accounts, one per config_id, with $10k starting balance';
COMMENT ON TABLE paper_trades IS 'Paper trades executed via Hummingbot API market data, linked to Decision Module';
COMMENT ON TABLE paper_orders IS 'Audit trail of paper orders for each trade (entry, stop loss, take profit)';

COMMENT ON COLUMN paper_accounts.config_id IS 'Links to configurations table - each config gets one paper account';
COMMENT ON COLUMN paper_accounts.initial_balance IS 'Starting balance in USD (default $10,000)';
COMMENT ON COLUMN paper_accounts.current_balance IS 'Current available balance after trades and fees';
COMMENT ON COLUMN paper_accounts.total_pnl IS 'Cumulative realized P&L from all closed trades';

COMMENT ON COLUMN paper_trades.decision_id IS 'Links back to Decision Module decision that created this trade';
COMMENT ON COLUMN paper_trades.symbol IS 'Trading pair in internal format (e.g., BTC/USDT)';
COMMENT ON COLUMN paper_trades.size_usd IS 'Position size in USD (before leverage)';
COMMENT ON COLUMN paper_trades.confidence_score IS 'Decision Module confidence score (0.0-1.0)';
COMMENT ON COLUMN paper_trades.unrealized_pnl IS 'Current unrealized P&L updated with real-time prices';
COMMENT ON COLUMN paper_trades.realized_pnl IS 'Final P&L when trade is closed';

COMMENT ON COLUMN paper_orders.order_type IS 'Type of order: market (entry), stop_loss, take_profit';
COMMENT ON COLUMN paper_orders.filled_price IS 'Actual fill price from Hummingbot API market data';

-- Create view for paper trading dashboard
CREATE VIEW paper_trading_summary AS
SELECT 
    pa.config_id,
    pa.user_id,
    pa.initial_balance,
    pa.current_balance,
    pa.total_pnl,
    pa.open_positions,
    pa.total_trades,
    pa.win_trades,
    pa.loss_trades,
    CASE 
        WHEN pa.total_trades > 0 THEN ROUND((pa.win_trades::DECIMAL / pa.total_trades * 100), 2)
        ELSE 0 
    END as win_rate_pct,
    ROUND((pa.total_pnl / pa.initial_balance * 100), 2) as total_return_pct,
    COUNT(pt.trade_id) FILTER (WHERE pt.status = 'open') as currently_open,
    SUM(pt.unrealized_pnl) FILTER (WHERE pt.status = 'open') as total_unrealized_pnl,
    pa.created_at,
    pa.updated_at
FROM paper_accounts pa
LEFT JOIN paper_trades pt ON pa.account_id = pt.account_id
GROUP BY pa.account_id, pa.config_id, pa.user_id, pa.initial_balance, 
         pa.current_balance, pa.total_pnl, pa.open_positions, 
         pa.total_trades, pa.win_trades, pa.loss_trades, 
         pa.created_at, pa.updated_at;

COMMENT ON VIEW paper_trading_summary IS 'Dashboard view combining account stats with real-time position data';

COMMIT;

-- Verification queries
/*
-- Verify tables were created
SELECT table_name FROM information_schema.tables 
WHERE table_schema='public' AND table_name LIKE 'paper_%';

-- Check constraints and indexes
SELECT conname, contype FROM pg_constraint 
WHERE conrelid IN (
    SELECT oid FROM pg_class WHERE relname IN ('paper_accounts', 'paper_trades', 'paper_orders')
);

-- Test the summary view
SELECT * FROM paper_trading_summary LIMIT 1;
*/