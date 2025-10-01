-- Migration 0016: Add close_reason column to paper_trades
-- Tracks why positions were closed for performance analysis
-- Author: Claude Code
-- Date: 2025-10-01

BEGIN;

-- Add close_reason column to paper_trades table
ALTER TABLE paper_trades
ADD COLUMN IF NOT EXISTS close_reason VARCHAR(50);

-- Add check constraint with all known close reasons
ALTER TABLE paper_trades
ADD CONSTRAINT paper_trades_close_reason_check
CHECK (close_reason IN (
    'take_profit',      -- Position hit take profit target
    'stop_loss',        -- Position hit stop loss target
    'manual',           -- User manually closed position
    'liquidation',      -- Position was liquidated
    'system_reset_v2',  -- Closed during system reset/upgrade
    'position_management' -- LLM decided to exit position
) OR close_reason IS NULL);

-- Add comment
COMMENT ON COLUMN paper_trades.close_reason IS 'Reason position was closed: take_profit, stop_loss, manual, liquidation, system_reset_v2, position_management';

-- Create index for close_reason analysis queries
CREATE INDEX idx_paper_trades_close_reason ON paper_trades(close_reason) WHERE status = 'closed';

COMMIT;

-- Verification query
/*
SELECT close_reason, COUNT(*) as count
FROM paper_trades
WHERE status = 'closed'
GROUP BY close_reason
ORDER BY count DESC;
*/
