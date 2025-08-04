-- Demo User Management for Hackathon
-- Expand existing users table to support demo email signup

-- Add email column for demo signup
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE;

-- Add demo access flag
ALTER TABLE users ADD COLUMN IF NOT EXISTS demo_access BOOLEAN DEFAULT TRUE;

-- Add index for email lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Create constraint to ensure either username or email exists
ALTER TABLE users ADD CONSTRAINT check_username_or_email 
CHECK (username IS NOT NULL OR email IS NOT NULL);

-- Insert demo users if they don't exist (for testing)
INSERT INTO users (user_id, email, demo_access, created_at) 
VALUES ('00000000-0000-0000-0000-000000000001', 'demo@ggbot.dev', TRUE, NOW())
ON CONFLICT (user_id) DO UPDATE SET
  email = EXCLUDED.email,
  demo_access = EXCLUDED.demo_access;