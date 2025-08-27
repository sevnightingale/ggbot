-- database/0004_update_schema_for_platform.sql
-- Updates database schema to support the platform architecture

-- Update users table to include additional fields
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS email VARCHAR,
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;

-- Create configurations table
CREATE TABLE IF NOT EXISTS configurations (
    config_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    config_type VARCHAR NOT NULL,
    config_data JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_configurations_user_id FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE (user_id, config_type)
);

-- Create index on configurations
CREATE INDEX IF NOT EXISTS idx_configurations_user_id_type
    ON configurations (user_id, config_type);

-- Update trades table
ALTER TABLE trades
ADD COLUMN IF NOT EXISTS exchange VARCHAR,
ADD COLUMN IF NOT EXISTS pair VARCHAR,
ADD COLUMN IF NOT EXISTS closed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS profit_loss NUMERIC;

-- Rename pair_index to pair if it doesn't exist yet
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trades' AND column_name = 'pair_index'
    ) THEN
        BEGIN
            -- Copy data from pair_index to pair if pair is null
            UPDATE trades SET pair = pair_index WHERE pair IS NULL;
        EXCEPTION WHEN OTHERS THEN
            -- Handle any errors
            RAISE NOTICE 'Error updating pair column: %', SQLERRM;
        END;
    END IF;
END $$;

-- Update market_data table if needed
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'market_data' AND column_name = 'symbol'
    ) THEN
        BEGIN
            -- Create source column if it doesn't exist
            ALTER TABLE market_data ADD COLUMN IF NOT EXISTS source VARCHAR;
            
            -- Create indicators and raw_data columns if they don't exist
            ALTER TABLE market_data 
            ADD COLUMN IF NOT EXISTS indicators JSONB,
            ADD COLUMN IF NOT EXISTS raw_data JSONB;
        EXCEPTION WHEN OTHERS THEN
            -- Handle any errors
            RAISE NOTICE 'Error updating market_data table: %', SQLERRM;
        END;
    END IF;
END $$;

-- Ensure all tables have proper user_id foreign keys
DO $$
BEGIN
    -- Add user_id foreign key to logs if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'logs' AND column_name = 'user_id'
    ) THEN
        ALTER TABLE logs ADD COLUMN user_id UUID;
        ALTER TABLE logs 
        ADD CONSTRAINT fk_logs_user_id FOREIGN KEY (user_id) REFERENCES users(user_id);
    END IF;
END $$;

-- Create appropriate composite indexes for multi-user queries
-- Index for trades by user_id and created_at
CREATE INDEX IF NOT EXISTS idx_trades_user_id_created_at
    ON trades (user_id, created_at);

-- Index for market_data efficient retrieval
CREATE INDEX IF NOT EXISTS idx_market_data_user_pair_timeframe_timestamp
    ON market_data (user_id, symbol, timeframe, updated_at);