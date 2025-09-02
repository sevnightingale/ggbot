-- ============================================================================
-- GGBot V1 Supabase Migration Script (SAFE VERSION)
-- Handles existing tables gracefully with IF NOT EXISTS
-- ============================================================================

-- Enable Row Level Security extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. CONFIGURATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS configurations (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    config_type VARCHAR(50) NOT NULL,
    config_name VARCHAR(100),
    config_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add foreign key constraint only if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'configurations' 
        AND constraint_name = 'configurations_user_fkey'
    ) THEN
        ALTER TABLE configurations 
        ADD CONSTRAINT configurations_user_fkey 
        FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Enable RLS
ALTER TABLE configurations ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist, then create new ones
DROP POLICY IF EXISTS "Users can only access their own configurations" ON configurations;
CREATE POLICY "Users can only access their own configurations" ON configurations
    FOR ALL USING (auth.uid() = user_id);

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_configurations_user ON configurations(user_id);
CREATE INDEX IF NOT EXISTS idx_configurations_type ON configurations(config_type);
CREATE UNIQUE INDEX IF NOT EXISTS idx_configurations_user_type ON configurations(user_id, config_type);

-- ============================================================================
-- 2. UNIFIED DECISIONS TABLE (replaces strategy_runs + ggshot_filter)
-- ============================================================================
CREATE TABLE IF NOT EXISTS decisions (
    decision_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    config_id UUID,        -- NULL for ggShot signals (no user config)
    
    -- Core decision data
    symbol VARCHAR(20) NOT NULL,
    action VARCHAR(20) NOT NULL,          -- 'enter', 'wait', 'exit' (always present)
    status VARCHAR(20),                   -- 'approved', 'rejected' (primarily for signal validation)
    confidence DECIMAL(4,3) NOT NULL CHECK (confidence >= 0.000 AND confidence <= 1.000),
    reasoning TEXT,                       -- LLM reasoning/explanation text
    
    -- Full decision context (new audit fields)
    prompt TEXT,           -- Complete LLM prompt sent for decision
    market_data JSONB,     -- Raw indicator values used in decision
    
    -- Flexible context storage
    decision_data JSONB,   -- Type-specific data (trade_id, stop_loss_price, take_profit_price, etc.)
    
    -- Decision linking and audit
    parent_decision_id UUID, -- Links related decisions (entry → management → exit)
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add foreign key constraints only if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'decisions' 
        AND constraint_name = 'decisions_user_fkey'
    ) THEN
        ALTER TABLE decisions 
        ADD CONSTRAINT decisions_user_fkey 
        FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'decisions' 
        AND constraint_name = 'decisions_config_fkey'
    ) THEN
        ALTER TABLE decisions 
        ADD CONSTRAINT decisions_config_fkey 
        FOREIGN KEY (config_id) REFERENCES configurations(config_id) ON DELETE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'decisions' 
        AND constraint_name = 'decisions_parent_fkey'
    ) THEN
        ALTER TABLE decisions 
        ADD CONSTRAINT decisions_parent_fkey 
        FOREIGN KEY (parent_decision_id) REFERENCES decisions(decision_id);
    END IF;
END $$;

-- Enable RLS
ALTER TABLE decisions ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist, then create new ones
DROP POLICY IF EXISTS "Users can only access their own decisions" ON decisions;
CREATE POLICY "Users can only access their own decisions" ON decisions
    FOR ALL USING (auth.uid() = user_id);

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_decisions_user_config ON decisions(user_id, config_id);
CREATE INDEX IF NOT EXISTS idx_decisions_action_status ON decisions(action, status);
CREATE INDEX IF NOT EXISTS idx_decisions_symbol_created ON decisions(symbol, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_parent ON decisions(parent_decision_id);
CREATE INDEX IF NOT EXISTS idx_decisions_confidence ON decisions(confidence DESC);

-- ============================================================================
-- 3. MARKET DATA TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    config_id UUID,           -- Config-specific extraction
    source VARCHAR(100),      -- 'crypto_indicators_mcp', 'hummingbot_api', etc.
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    data_type VARCHAR(50),    -- 'indicator_values', 'price_data', etc.
    indicators JSONB,         -- Technical indicators data
    raw_data JSONB NOT NULL,  -- Source-specific data
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add foreign key constraints only if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'market_data' 
        AND constraint_name = 'market_data_user_fkey'
    ) THEN
        ALTER TABLE market_data 
        ADD CONSTRAINT market_data_user_fkey 
        FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'market_data' 
        AND constraint_name = 'market_data_config_fkey'
    ) THEN
        ALTER TABLE market_data 
        ADD CONSTRAINT market_data_config_fkey 
        FOREIGN KEY (config_id) REFERENCES configurations(config_id) ON DELETE CASCADE;
    END IF;
END $$;

-- Enable RLS
ALTER TABLE market_data ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist, then create new ones
DROP POLICY IF EXISTS "Users can only access their own market data" ON market_data;
CREATE POLICY "Users can only access their own market data" ON market_data
    FOR ALL USING (auth.uid() = user_id);

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_market_data_user_symbol_timeframe ON market_data(user_id, symbol, timeframe, updated_at);
CREATE INDEX IF NOT EXISTS idx_market_data_config_symbol ON market_data(config_id, symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_updated_at ON market_data(updated_at DESC);

-- ============================================================================
-- 4. PAPER TRADING TABLES
-- ============================================================================

-- Paper Accounts (isolated per config)
CREATE TABLE IF NOT EXISTS paper_accounts (
    account_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    config_id UUID UNIQUE NOT NULL, -- One account per config
    initial_balance DECIMAL(20,8) NOT NULL DEFAULT 10000.00,
    current_balance DECIMAL(20,8) NOT NULL DEFAULT 10000.00,
    total_pnl DECIMAL(20,8) NOT NULL DEFAULT 0.00,
    open_positions INTEGER NOT NULL DEFAULT 0,
    total_trades INTEGER NOT NULL DEFAULT 0,
    win_trades INTEGER NOT NULL DEFAULT 0,
    loss_trades INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add foreign key constraints only if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'paper_accounts' 
        AND constraint_name = 'paper_accounts_user_fkey'
    ) THEN
        ALTER TABLE paper_accounts 
        ADD CONSTRAINT paper_accounts_user_fkey 
        FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'paper_accounts' 
        AND constraint_name = 'paper_accounts_config_fkey'
    ) THEN
        ALTER TABLE paper_accounts 
        ADD CONSTRAINT paper_accounts_config_fkey 
        FOREIGN KEY (config_id) REFERENCES configurations(config_id) ON DELETE CASCADE;
    END IF;
END $$;

-- Enable RLS
ALTER TABLE paper_accounts ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist, then create new ones
DROP POLICY IF EXISTS "Users can only access their own paper accounts" ON paper_accounts;
CREATE POLICY "Users can only access their own paper accounts" ON paper_accounts
    FOR ALL USING (auth.uid() = user_id);

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_paper_accounts_user ON paper_accounts(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_paper_accounts_config ON paper_accounts(config_id);

-- Paper Trades
CREATE TABLE IF NOT EXISTS paper_trades (
    trade_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    account_id UUID NOT NULL,
    config_id UUID NOT NULL,
    decision_id UUID,         -- Links to decision that created this trade
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL, -- 'long' or 'short'
    entry_price DECIMAL(20,8) NOT NULL,
    current_price DECIMAL(20,8),
    size_usd DECIMAL(20,8) NOT NULL,
    leverage INTEGER NOT NULL DEFAULT 1,
    unrealized_pnl DECIMAL(20,8),
    realized_pnl DECIMAL(20,8),
    status VARCHAR(20) NOT NULL DEFAULT 'open', -- 'open' or 'closed'
    stop_loss DECIMAL(20,8),
    take_profit DECIMAL(20,8),
    confidence_score DECIMAL(3,2),
    opened_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMP WITH TIME ZONE
);

-- Add foreign key constraints only if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'paper_trades' 
        AND constraint_name = 'paper_trades_user_fkey'
    ) THEN
        ALTER TABLE paper_trades 
        ADD CONSTRAINT paper_trades_user_fkey 
        FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'paper_trades' 
        AND constraint_name = 'paper_trades_account_fkey'
    ) THEN
        ALTER TABLE paper_trades 
        ADD CONSTRAINT paper_trades_account_fkey 
        FOREIGN KEY (account_id) REFERENCES paper_accounts(account_id) ON DELETE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'paper_trades' 
        AND constraint_name = 'paper_trades_config_fkey'
    ) THEN
        ALTER TABLE paper_trades 
        ADD CONSTRAINT paper_trades_config_fkey 
        FOREIGN KEY (config_id) REFERENCES configurations(config_id) ON DELETE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'paper_trades' 
        AND constraint_name = 'paper_trades_decision_fkey'
    ) THEN
        ALTER TABLE paper_trades 
        ADD CONSTRAINT paper_trades_decision_fkey 
        FOREIGN KEY (decision_id) REFERENCES decisions(decision_id) ON DELETE SET NULL;
    END IF;
END $$;

-- Enable RLS
ALTER TABLE paper_trades ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist, then create new ones
DROP POLICY IF EXISTS "Users can only access their own paper trades" ON paper_trades;
CREATE POLICY "Users can only access their own paper trades" ON paper_trades
    FOR ALL USING (auth.uid() = user_id);

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_paper_trades_user_config ON paper_trades(user_id, config_id);
CREATE INDEX IF NOT EXISTS idx_paper_trades_account ON paper_trades(account_id);
CREATE INDEX IF NOT EXISTS idx_paper_trades_status ON paper_trades(status);
CREATE INDEX IF NOT EXISTS idx_paper_trades_symbol_opened ON paper_trades(symbol, opened_at DESC);

-- Paper Orders (audit trail)
CREATE TABLE IF NOT EXISTS paper_orders (
    order_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    trade_id UUID NOT NULL,
    order_type VARCHAR(20) NOT NULL, -- 'market', 'stop_loss', 'take_profit'
    side VARCHAR(10) NOT NULL,       -- 'buy' or 'sell'
    filled_price DECIMAL(20,8) NOT NULL,
    size DECIMAL(20,8) NOT NULL,
    fees DECIMAL(20,8) NOT NULL DEFAULT 0.00,
    filled_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add foreign key constraints only if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'paper_orders' 
        AND constraint_name = 'paper_orders_user_fkey'
    ) THEN
        ALTER TABLE paper_orders 
        ADD CONSTRAINT paper_orders_user_fkey 
        FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'paper_orders' 
        AND constraint_name = 'paper_orders_trade_fkey'
    ) THEN
        ALTER TABLE paper_orders 
        ADD CONSTRAINT paper_orders_trade_fkey 
        FOREIGN KEY (trade_id) REFERENCES paper_trades(trade_id) ON DELETE CASCADE;
    END IF;
END $$;

-- Enable RLS
ALTER TABLE paper_orders ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist, then create new ones
DROP POLICY IF EXISTS "Users can only access their own paper orders" ON paper_orders;
CREATE POLICY "Users can only access their own paper orders" ON paper_orders
    FOR ALL USING (auth.uid() = user_id);

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_paper_orders_user ON paper_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_paper_orders_trade ON paper_orders(trade_id);
CREATE INDEX IF NOT EXISTS idx_paper_orders_filled_at ON paper_orders(filled_at DESC);

-- ============================================================================
-- 5. LOGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS logs (
    log_id SERIAL PRIMARY KEY,
    user_id UUID,
    module VARCHAR(100),
    log_level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add foreign key constraint only if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'logs' 
        AND constraint_name = 'logs_user_fkey'
    ) THEN
        ALTER TABLE logs 
        ADD CONSTRAINT logs_user_fkey 
        FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Enable RLS
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist, then create new ones
DROP POLICY IF EXISTS "Users can only access their own logs" ON logs;
CREATE POLICY "Users can only access their own logs" ON logs
    FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "System logs are accessible to authenticated users" ON logs;
CREATE POLICY "System logs are accessible to authenticated users" ON logs
    FOR SELECT USING (user_id IS NULL AND auth.role() = 'authenticated');

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_logs_user_timestamp ON logs(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_level_timestamp ON logs(log_level, timestamp DESC);

-- ============================================================================
-- 6. FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.triggers 
        WHERE trigger_name = 'update_configurations_updated_at'
    ) THEN
        CREATE TRIGGER update_configurations_updated_at 
        BEFORE UPDATE ON configurations 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.triggers 
        WHERE trigger_name = 'update_paper_accounts_updated_at'
    ) THEN
        CREATE TRIGGER update_paper_accounts_updated_at 
        BEFORE UPDATE ON paper_accounts 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- ============================================================================
-- 7. VIEWS FOR DASHBOARD
-- ============================================================================

-- Drop view if it exists, then recreate
DROP VIEW IF EXISTS paper_trading_summary;

CREATE VIEW paper_trading_summary AS
SELECT 
    pa.account_id,
    pa.user_id,
    pa.config_id,
    pa.current_balance,
    pa.total_pnl,
    pa.open_positions,
    pa.total_trades,
    pa.win_trades,
    pa.loss_trades,
    CASE 
        WHEN pa.total_trades > 0 THEN ROUND((pa.win_trades::DECIMAL / pa.total_trades) * 100, 2)
        ELSE 0 
    END as win_rate_percent,
    CASE 
        WHEN pa.initial_balance > 0 THEN ROUND(((pa.current_balance - pa.initial_balance) / pa.initial_balance) * 100, 2)
        ELSE 0 
    END as total_return_percent,
    COALESCE(SUM(pt.unrealized_pnl), 0) as total_unrealized_pnl,
    pa.created_at,
    pa.updated_at
FROM paper_accounts pa
LEFT JOIN paper_trades pt ON pa.account_id = pt.account_id AND pt.status = 'open'
GROUP BY pa.account_id, pa.user_id, pa.config_id, pa.current_balance, pa.total_pnl, 
         pa.open_positions, pa.total_trades, pa.win_trades, pa.loss_trades, 
         pa.initial_balance, pa.created_at, pa.updated_at;

-- ============================================================================
-- MIGRATION COMPLETE (SAFE VERSION)
-- ============================================================================