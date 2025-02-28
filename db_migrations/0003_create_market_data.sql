-- db_migrations/0002_create_market_data.sql
-- Creates the market_data table with user_id for multi-user support

CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    symbol VARCHAR NOT NULL,
    timeframe VARCHAR NOT NULL,
    data JSONB NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Unique constraint per user-symbol-timeframe (prevents duplicates)
    UNIQUE (user_id, symbol, timeframe),

    -- Foreign key linking user_id to the users table
    CONSTRAINT fk_market_data_user_id FOREIGN KEY (user_id) REFERENCES users(user_id)
);
