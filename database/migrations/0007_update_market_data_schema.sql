-- database/0007_update_market_data_schema.sql
-- Standardizes market_data table schema to match our code structure

-- 1. Ensure raw_data and indicators columns exist with proper defaults
ALTER TABLE market_data 
    ADD COLUMN IF NOT EXISTS raw_data JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS indicators JSONB DEFAULT '{}'::jsonb;

-- 2. Make sure source and data_type columns exist
ALTER TABLE market_data 
    ADD COLUMN IF NOT EXISTS source VARCHAR DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS data_type VARCHAR DEFAULT 'price_data';

-- 3. Drop the 'data' column if it exists (do this first to avoid constraint conflicts)
ALTER TABLE market_data DROP COLUMN IF EXISTS data;

-- 4. Set default values for any NULL entries before making columns required
UPDATE market_data SET raw_data = '{}'::jsonb WHERE raw_data IS NULL;
UPDATE market_data SET indicators = '{}'::jsonb WHERE indicators IS NULL;
UPDATE market_data SET source = 'unknown' WHERE source IS NULL;
UPDATE market_data SET data_type = 'price_data' WHERE data_type IS NULL;

-- Now make raw_data required
ALTER TABLE market_data ALTER COLUMN raw_data SET NOT NULL;

-- 5. Add helpful comments
COMMENT ON TABLE market_data IS 'Stores market data from various sources with indicators';
COMMENT ON COLUMN market_data.raw_data IS 'Raw price data (OHLCV) in JSON format';
COMMENT ON COLUMN market_data.indicators IS 'Technical indicators in JSON format';
COMMENT ON COLUMN market_data.source IS 'Source of the data (e.g., yfinance, tradingview)';
COMMENT ON COLUMN market_data.data_type IS 'Type of data: price_data, report, sentiment, etc.';

-- 6. Ensure we have proper indexes
CREATE INDEX IF NOT EXISTS idx_market_data_user_id_symbol_timeframe
ON market_data (user_id, symbol, timeframe);

CREATE INDEX IF NOT EXISTS idx_market_data_updated_at
ON market_data (updated_at);