-- db_migrations/0002_add_user_id.sql
-- Create a placeholder users table for multi-user support.
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY,
    username VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add foreign key constraint to trades table.
ALTER TABLE trades
ADD CONSTRAINT fk_trades_user_id
    FOREIGN KEY (user_id) REFERENCES users (user_id);

-- Add foreign key constraint to sessions table.
ALTER TABLE sessions
ADD CONSTRAINT fk_sessions_user_id
    FOREIGN KEY (user_id) REFERENCES users (user_id);

