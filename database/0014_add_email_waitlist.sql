-- Email waitlist and event tracking migration
-- Migration: 0014_add_email_waitlist.sql
-- Purpose: Add tables for LaunchList integration and email event tracking

-- Email waitlist table for syncing LaunchList data
CREATE TABLE email_waitlist (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  launchlist_id VARCHAR(100), -- LaunchList user ID for sync
  referral_code VARCHAR(50) UNIQUE,
  signup_source VARCHAR(100), -- e.g., 'direct', 'twitter', 'referral'
  signup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  verified BOOLEAN DEFAULT FALSE,
  referral_count INTEGER DEFAULT 0,
  position_in_queue INTEGER,
  metadata JSONB -- Store additional LaunchList data
);

-- Email events table for tracking email delivery and engagement
CREATE TABLE email_events (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  event_type VARCHAR(50) NOT NULL, -- 'welcome', 'update', 'trading_alert'
  template_name VARCHAR(100),
  sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  status VARCHAR(20) DEFAULT 'sent', -- 'sent', 'delivered', 'bounced', 'opened'
  resend_message_id VARCHAR(100), -- For tracking with Resend
  metadata JSONB -- Additional event data
);

-- Indexes for performance
CREATE INDEX idx_email_waitlist_email ON email_waitlist(email);
CREATE INDEX idx_email_waitlist_verified ON email_waitlist(verified);
CREATE INDEX idx_email_waitlist_signup_date ON email_waitlist(signup_date);
CREATE INDEX idx_email_events_email ON email_events(email);
CREATE INDEX idx_email_events_type ON email_events(event_type);
CREATE INDEX idx_email_events_sent_at ON email_events(sent_at);

-- Insert initial admin user for testing
INSERT INTO email_waitlist (email, verified, signup_source, position_in_queue) 
VALUES ('admin@ggbots.ai', true, 'admin', 1);

-- Add comments for documentation
COMMENT ON TABLE email_waitlist IS 'Stores waitlist signups synced from LaunchList with referral tracking';
COMMENT ON TABLE email_events IS 'Tracks all email events for analytics and deliverability monitoring';
COMMENT ON COLUMN email_waitlist.launchlist_id IS 'LaunchList user ID for syncing data';
COMMENT ON COLUMN email_waitlist.metadata IS 'Additional LaunchList data in JSON format';
COMMENT ON COLUMN email_events.resend_message_id IS 'Resend API message ID for tracking delivery status';