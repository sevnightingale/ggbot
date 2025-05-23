-- Migration 0009: Add Account Monitoring Support
-- 
-- This migration adds support for real-time account monitoring and secure
-- credential storage to enable the Account Monitoring Layer functionality.
--
-- Changes:
-- 1. Create account_states table for real-time balance/position monitoring
-- 2. Create exchange_credentials table for secure API key storage
-- 3. Add indexes for efficient monitoring queries
-- 4. Add trade execution tracking fields to trades table

-- Create account_states table for real-time account monitoring
CREATE TABLE account_states (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    config_id UUID NOT NULL REFERENCES configurations(config_id) ON DELETE CASCADE,
    exchange VARCHAR(50) NOT NULL,
    balance_data JSONB NOT NULL,        -- Full balance object from exchange
    position_data JSONB NOT NULL,       -- Current positions array from exchange
    equity NUMERIC(20, 8) NOT NULL,     -- Total account value
    available_margin NUMERIC(20, 8),    -- Available margin for new trades
    used_margin NUMERIC(20, 8),         -- Currently used margin
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient account monitoring queries
CREATE INDEX idx_account_states_user_config ON account_states(user_id, config_id);
CREATE INDEX idx_account_states_updated_at ON account_states(updated_at);
CREATE INDEX idx_account_states_exchange ON account_states(exchange);

-- Unique constraint to ensure one account state per user/config/exchange combination
-- (allows for multiple exchanges per config in the future)
CREATE UNIQUE INDEX idx_account_states_unique ON account_states(user_id, config_id, exchange);

-- Create exchange_credentials table for secure API key storage
CREATE TABLE exchange_credentials (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    config_id UUID NOT NULL REFERENCES configurations(config_id) ON DELETE CASCADE,
    exchange VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT NOT NULL,     -- Encrypted API key
    secret_encrypted TEXT NOT NULL,      -- Encrypted secret
    passphrase_encrypted TEXT,           -- For exchanges requiring passphrase (e.g., OKX)
    testnet BOOLEAN DEFAULT TRUE,        -- Whether to use testnet/sandbox mode
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    last_used TIMESTAMP WITHOUT TIME ZONE,
    UNIQUE(user_id, config_id, exchange) -- One credential set per user/config/exchange
);

-- Create indexes for credential management
CREATE INDEX idx_exchange_credentials_user_config ON exchange_credentials(user_id, config_id);
CREATE INDEX idx_exchange_credentials_exchange ON exchange_credentials(exchange);
CREATE INDEX idx_exchange_credentials_last_used ON exchange_credentials(last_used);

-- Add additional fields to trades table for better execution tracking
ALTER TABLE trades ADD COLUMN IF NOT EXISTS decision_id UUID;
ALTER TABLE trades ADD COLUMN IF NOT EXISTS execution_details JSONB;
ALTER TABLE trades ADD COLUMN IF NOT EXISTS entry_price NUMERIC(20, 8);
ALTER TABLE trades ADD COLUMN IF NOT EXISTS exit_price NUMERIC(20, 8);
ALTER TABLE trades ADD COLUMN IF NOT EXISTS order_ids JSONB;

-- Add comments for documentation
COMMENT ON TABLE account_states IS 'Real-time account state data from exchange monitoring';
COMMENT ON COLUMN account_states.balance_data IS 'Full balance object returned from exchange API';
COMMENT ON COLUMN account_states.position_data IS 'Array of current positions from exchange API';
COMMENT ON COLUMN account_states.equity IS 'Total account value (balance + unrealized PnL)';
COMMENT ON COLUMN account_states.available_margin IS 'Available margin for opening new positions';
COMMENT ON COLUMN account_states.used_margin IS 'Margin currently used by open positions';

COMMENT ON TABLE exchange_credentials IS 'Encrypted exchange API credentials for secure storage';
COMMENT ON COLUMN exchange_credentials.api_key_encrypted IS 'Encrypted exchange API key';
COMMENT ON COLUMN exchange_credentials.secret_encrypted IS 'Encrypted exchange API secret';
COMMENT ON COLUMN exchange_credentials.passphrase_encrypted IS 'Encrypted passphrase for exchanges that require it';
COMMENT ON COLUMN exchange_credentials.testnet IS 'Whether credentials are for testnet/sandbox environment';

COMMENT ON COLUMN trades.decision_id IS 'Links trade to the decision that created it';
COMMENT ON COLUMN trades.execution_details IS 'LLM tool calls, MCP responses, and execution metadata';
COMMENT ON COLUMN trades.entry_price IS 'Actual price at which position was entered';
COMMENT ON COLUMN trades.exit_price IS 'Actual price at which position was exited';
COMMENT ON COLUMN trades.order_ids IS 'Exchange order IDs associated with this trade';

-- Create indexes for new trade fields
CREATE INDEX IF NOT EXISTS idx_trades_decision_id ON trades(decision_id);
CREATE INDEX IF NOT EXISTS idx_trades_entry_price ON trades(entry_price);
CREATE INDEX IF NOT EXISTS idx_trades_exit_price ON trades(exit_price);

-- Example of account_states data structure (for documentation)
-- balance_data format:
-- {
--   "total": 10000.00,
--   "free": 8500.00,
--   "used": 1500.00,
--   "BTC": {"free": 0.5, "used": 0.1, "total": 0.6},
--   "USD": {"free": 8500.00, "used": 1500.00, "total": 10000.00}
-- }
--
-- position_data format:
-- [
--   {
--     "symbol": "BTC/USD:BTC",
--     "contracts": 100,
--     "side": "long",
--     "size": 100,
--     "entryPrice": 45000.00,
--     "markPrice": 46000.00,
--     "unrealizedPnl": 100.00,
--     "percentage": 2.22
--   }
-- ]
--
-- execution_details format:
-- {
--   "llm_tool_calls": [...],
--   "validated_calls": [...],
--   "mcp_responses": [...],
--   "execution_timestamp": "2023-10-01T12:00:00Z",
--   "execution_duration_ms": 1500
-- }