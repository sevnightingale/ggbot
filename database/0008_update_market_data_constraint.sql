-- database/0008_update_market_data_constraint.sql
-- Modifies the market_data table to allow multiple entries per user-symbol-timeframe

-- 1. First, drop the existing unique constraint
ALTER TABLE market_data DROP CONSTRAINT IF EXISTS market_data_user_id_symbol_timeframe_key;

-- 2. Create a new unique constraint that includes updated_at
ALTER TABLE market_data ADD CONSTRAINT market_data_user_id_symbol_timeframe_updated_at_key 
UNIQUE (user_id, symbol, timeframe, updated_at);

-- 3. Update the ON CONFLICT clause in your code to reference the new constraint
COMMENT ON CONSTRAINT market_data_user_id_symbol_timeframe_updated_at_key 
ON market_data IS 'Ensures no duplicate timestamps for the same user-symbol-timeframe';

-- 4. Update the index to include updated_at
DROP INDEX IF EXISTS idx_market_data_user_id_symbol_timeframe;
CREATE INDEX idx_market_data_user_id_symbol_timeframe_updated
ON market_data (user_id, symbol, timeframe, updated_at);

-- 5. Add a comment explaining the change
COMMENT ON TABLE market_data IS 'Stores market data from various sources with indicators. Multiple entries per user-symbol-timeframe allowed with different timestamps.';