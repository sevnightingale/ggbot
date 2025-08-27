-- database/0005_additional_improvements.sql
-- Additional improvements based on review feedback

-- Add data_type column to market_data table
ALTER TABLE market_data 
ADD COLUMN IF NOT EXISTS data_type VARCHAR;

-- Add comment to explain data_type values
COMMENT ON COLUMN market_data.data_type IS 'Type of data: indicator_values, report, sentiment, news, etc.';

-- Add config_name to configurations table
ALTER TABLE configurations
ADD COLUMN IF NOT EXISTS config_name VARCHAR;

-- Add comment to explain config_name usage
COMMENT ON COLUMN configurations.config_name IS 'Optional name for the configuration to allow multiple configurations per type';

-- Add config_id to trades table
ALTER TABLE trades
ADD COLUMN IF NOT EXISTS config_id UUID,
ADD CONSTRAINT fk_trades_config_id 
    FOREIGN KEY (config_id) REFERENCES configurations(config_id);

-- Add comment to explain config_id usage
COMMENT ON COLUMN trades.config_id IS 'Reference to the configuration used for this trade';

-- Update index for improved querying
CREATE INDEX IF NOT EXISTS idx_trades_user_config
    ON trades (user_id, config_id);