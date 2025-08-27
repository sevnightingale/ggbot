-- Add data integrity constraints to prevent phantom trades and bad data

-- 1. Ensure entry_price is not null for active trades
ALTER TABLE trades 
ADD CONSTRAINT valid_entry_price 
CHECK (
    (trade_status IN ('open', 'active', 'pending') AND entry_price IS NOT NULL) 
    OR 
    (trade_status NOT IN ('open', 'active', 'pending'))
);

-- 2. Ensure leverage is reasonable (1-100x)
ALTER TABLE trades 
ADD CONSTRAINT valid_leverage 
CHECK (leverage >= 1 AND leverage <= 100);

-- 3. Ensure collateral_amount is positive
ALTER TABLE trades 
ADD CONSTRAINT positive_collateral 
CHECK (collateral_amount > 0);

-- 4. Ensure valid trade status transitions
ALTER TABLE trades 
ADD CONSTRAINT valid_trade_status 
CHECK (trade_status IN ('open', 'active', 'pending', 'closed', 'canceled', 'expired', 'failed'));

-- 5. Ensure closed trades have closed_at timestamp
ALTER TABLE trades 
ADD CONSTRAINT closed_trades_have_timestamp 
CHECK (
    (trade_status IN ('closed', 'canceled', 'expired') AND closed_at IS NOT NULL) 
    OR 
    (trade_status NOT IN ('closed', 'canceled', 'expired'))
);

-- 6. Ensure stop_loss and take_profit are reasonable if set
ALTER TABLE trades 
ADD CONSTRAINT reasonable_stop_loss 
CHECK (
    stop_loss IS NULL 
    OR 
    (stop_loss > 0 AND stop_loss != entry_price)
);

ALTER TABLE trades 
ADD CONSTRAINT reasonable_take_profit 
CHECK (
    take_profit IS NULL 
    OR 
    (take_profit > 0 AND take_profit != entry_price)
);

-- 7. Add index for active trades queries (used heavily)
CREATE INDEX IF NOT EXISTS idx_trades_active_user 
ON trades(user_id, trade_status) 
WHERE trade_status IN ('open', 'active', 'pending');

-- 8. Add index for recent trades (used in reconciliation)
CREATE INDEX IF NOT EXISTS idx_trades_recent_created 
ON trades(user_id, created_at DESC) 
WHERE created_at > NOW() - INTERVAL '7 days';

-- 9. Create a function to validate trade state consistency
CREATE OR REPLACE FUNCTION validate_trade_consistency()
RETURNS TRIGGER AS $$
BEGIN
    -- Ensure user_id is always set
    IF NEW.user_id IS NULL THEN
        RAISE EXCEPTION 'user_id cannot be null';
    END IF;
    
    -- Ensure trade_id is always set
    IF NEW.trade_id IS NULL THEN
        RAISE EXCEPTION 'trade_id cannot be null';
    END IF;
    
    -- Ensure pair/symbol is set
    IF NEW.pair IS NULL OR NEW.pair = '' THEN
        RAISE EXCEPTION 'pair cannot be null or empty';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 10. Create trigger to enforce consistency on insert/update
DROP TRIGGER IF EXISTS trigger_validate_trade_consistency ON trades;
CREATE TRIGGER trigger_validate_trade_consistency
    BEFORE INSERT OR UPDATE ON trades
    FOR EACH ROW
    EXECUTE FUNCTION validate_trade_consistency();

-- 11. Add a reconciliation log table for audit trail
CREATE TABLE IF NOT EXISTS trade_reconciliation_log (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    trade_id UUID NOT NULL,
    reconciliation_time TIMESTAMP DEFAULT NOW(),
    action VARCHAR(50) NOT NULL, -- 'validated', 'closed', 'error'
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    reason TEXT,
    error_message TEXT,
    exchange_data JSONB,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id)
);

CREATE INDEX idx_reconciliation_log_user_time 
ON trade_reconciliation_log(user_id, reconciliation_time DESC);

CREATE INDEX idx_reconciliation_log_trade 
ON trade_reconciliation_log(trade_id, reconciliation_time DESC);

-- 12. Create a view for active trades with validation
CREATE OR REPLACE VIEW active_trades_validated AS
SELECT 
    t.*,
    CASE 
        WHEN t.entry_price IS NULL THEN 'INVALID: Missing entry price'
        WHEN t.collateral_amount <= 0 THEN 'INVALID: Invalid collateral'
        WHEN t.leverage < 1 OR t.leverage > 100 THEN 'INVALID: Invalid leverage'
        ELSE 'VALID'
    END as validation_status
FROM trades t
WHERE t.trade_status IN ('open', 'active', 'pending')
ORDER BY t.created_at DESC;

-- Verify constraints were added successfully
SELECT 
    conname as constraint_name,
    contype as constraint_type,
    pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint 
WHERE conrelid = 'trades'::regclass 
AND conname LIKE '%valid%'
ORDER BY conname;