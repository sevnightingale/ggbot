-- =============================================================
-- Universal Trade Lifecycle System Migration
-- Migration: 0012_universal_trade_lifecycle.sql
-- Single script to transform phantom-trade system to position-based
-- =============================================================

-- 1. Drop existing trade-related tables (clean slate)
DROP TABLE IF EXISTS trade_reconciliation_log CASCADE;
DROP TABLE IF EXISTS position_reconciliations CASCADE;
DROP TABLE IF EXISTS trades CASCADE;

-- 2. Create new simplified trades table
CREATE TABLE trades (
    trade_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id),
    account_id VARCHAR NOT NULL DEFAULT 'main',
    exchange VARCHAR NOT NULL,    -- 'bitmex', 'binance', etc.
    symbol VARCHAR NOT NULL,      -- 'BTC/USD', 'ETH/USDT'
    side VARCHAR,                 -- 'long', 'short' (NULL for net exchanges like BitMEX)
    status VARCHAR NOT NULL DEFAULT 'open', -- 'open', 'closed'
    
    -- Single source of truth for position
    size_contracts DECIMAL(20,8) NOT NULL DEFAULT 0,
    entry_price DECIMAL(20,8),    -- VWAP calculated from trade_orders
    mark_price DECIMAL(20,8),     -- Current market price (updated frequently)
    
    -- P&L (computed fields)
    unrealized_pnl DECIMAL(20,8),
    realized_pnl DECIMAL(20,8),   -- Final P&L when closed
    total_fees DECIMAL(20,8),     -- Sum from trade_orders
    
    -- Timing
    opened_at TIMESTAMP NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMP,
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Position key uniqueness (exchange-dependent)
    UNIQUE(user_id, account_id, exchange, symbol, side)
);

-- 3. Create trade orders table for order-level tracking
CREATE TABLE trade_orders (
    id SERIAL PRIMARY KEY,
    trade_id UUID NOT NULL REFERENCES trades(trade_id),
    
    -- Exchange/symbol for better joins
    exchange VARCHAR NOT NULL,
    symbol VARCHAR NOT NULL,
    
    exchange_order_id VARCHAR NOT NULL,
    client_order_id VARCHAR,     -- our trade_id when exchange supports it
    order_type VARCHAR NOT NULL, -- 'market', 'limit', 'stop'
    side VARCHAR NOT NULL,       -- 'buy', 'sell'
    
    price DECIMAL(20,8),
    size DECIMAL(20,8),
    filled_size DECIMAL(20,8),
    fee DECIMAL(20,8),
    fee_currency VARCHAR,
    status VARCHAR NOT NULL,     -- 'open', 'filled', 'canceled'
    
    filled_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Ensure uniqueness across all exchanges
    UNIQUE(exchange, exchange_order_id)
);

-- 4. Create instrument metadata table
CREATE TABLE instrument_metadata (
    id SERIAL PRIMARY KEY,
    exchange VARCHAR NOT NULL,
    symbol VARCHAR NOT NULL,
    
    -- Contract specifications
    contract_value DECIMAL(20,8), -- 1.0 for BitMEX BTC/USD, varies for others
    contract_currency VARCHAR,    -- 'USD', 'BTC', etc.
    tick_size DECIMAL(20,8),      -- Minimum price increment
    lot_size DECIMAL(20,8),       -- Minimum size increment
    
    -- Position mode configuration
    supports_hedge_mode BOOLEAN DEFAULT false,
    default_position_mode VARCHAR DEFAULT 'net', -- 'net' or 'hedge'
    
    active BOOLEAN DEFAULT true,
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(exchange, symbol)
);

-- 5. Create essential indices for performance
CREATE INDEX idx_trades_active ON trades(user_id, exchange, status) WHERE status = 'open';
CREATE INDEX idx_trades_position_key ON trades(user_id, exchange, symbol, side, status);
CREATE INDEX idx_trade_orders_trade ON trade_orders(trade_id);
CREATE INDEX idx_trade_orders_exchange ON trade_orders(exchange, exchange_order_id);
CREATE INDEX idx_instrument_lookup ON instrument_metadata(exchange, symbol);

-- 6. Add BitMEX instrument metadata for current testing
INSERT INTO instrument_metadata (exchange, symbol, contract_value, contract_currency, tick_size, lot_size)
VALUES ('bitmex', 'BTC/USD', 1.0, 'USD', 0.5, 1.0);

-- 7. No data migration needed - fresh start for prototype phase
-- The current 4000-contract position will be picked up by new monitoring system

COMMENT ON TABLE trades IS 'Position-based trade tracking - one record per exchange position';
COMMENT ON TABLE trade_orders IS 'Order-level details for precise VWAP and P&L calculation';
COMMENT ON TABLE instrument_metadata IS 'Exchange-specific contract specifications';

-- 8. Verify tables were created successfully
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('trades', 'trade_orders', 'instrument_metadata')
ORDER BY table_name, ordinal_position;