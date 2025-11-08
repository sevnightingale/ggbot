-- Migration: Add agent_sessions table for Claude Agent SDK session resumption
-- Date: 2025-11-08
-- Purpose: Enable conversation persistence across agent restarts/crashes

-- Create agent_sessions table to store SDK session IDs
CREATE TABLE IF NOT EXISTS agent_sessions (
    config_id UUID PRIMARY KEY REFERENCES configurations(config_id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    last_active_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_agent_sessions_session_id ON agent_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_last_active ON agent_sessions(last_active_at);

-- Add comment
COMMENT ON TABLE agent_sessions IS 'Stores Claude Agent SDK session IDs for conversation persistence';
COMMENT ON COLUMN agent_sessions.session_id IS 'Claude Agent SDK session ID from init message';
COMMENT ON COLUMN agent_sessions.last_active_at IS 'Last time agent was active (for health monitoring)';

-- Fix activities table UUID issue for AsterDEX trades
-- AsterDEX uses integer orderIds, not UUIDs
ALTER TABLE activities ALTER COLUMN trade_id TYPE TEXT;

-- Add comment explaining the change
COMMENT ON COLUMN activities.trade_id IS 'Trade ID - TEXT to support both UUID (paper) and integer (AsterDEX) formats';
