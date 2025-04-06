-- db_migrations/0001_create_tables.sql
-- Schema creation script for ggbot.

-- 1. sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID,
    cookie_data JSONB,
    created_at TIMESTAMP,
    expires_at TIMESTAMP
);

-- Index on sessions.expires_at
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at
    ON sessions (expires_at);

-- 2. trades table
CREATE TABLE IF NOT EXISTS trades (
    trade_id UUID PRIMARY KEY,
    pair_index VARCHAR,
    timeframe VARCHAR,
    collateral_amount NUMERIC,
    leverage INTEGER,
    stop_loss NUMERIC,
    take_profit NUMERIC,
    confidence_score NUMERIC,
    reasoning_log TEXT,
    trade_status VARCHAR,
    created_at TIMESTAMP
);

-- Indexes on trades.created_at, pair_index, timeframe
CREATE INDEX IF NOT EXISTS idx_trades_created_at
    ON trades (created_at);

CREATE INDEX IF NOT EXISTS idx_trades_pair_index
    ON trades (pair_index);

CREATE INDEX IF NOT EXISTS idx_trades_timeframe
    ON trades (timeframe);

-- 3. logs table
CREATE TABLE IF NOT EXISTS logs (
    log_id SERIAL PRIMARY KEY,
    module VARCHAR,
    log_level VARCHAR,
    message TEXT,
    timestamp TIMESTAMP
);

-- Additional indexes for logs if you prefer, e.g. timestamp
