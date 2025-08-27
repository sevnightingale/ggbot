-- Fix the constraint and index issues

-- First, let's check what trades have invalid timing
SELECT trade_id, created_at, closed_at, 
       CASE WHEN closed_at < created_at THEN 'INVALID' ELSE 'OK' END as timing_status
FROM trades 
WHERE closed_at IS NOT NULL AND closed_at < created_at;

-- Fix any invalid timestamps (set closed_at = created_at for invalid records)
UPDATE trades 
SET closed_at = created_at 
WHERE closed_at IS NOT NULL AND closed_at < created_at;

-- Now add the timing constraint
ALTER TABLE trades 
ADD CONSTRAINT valid_trade_timing 
CHECK (closed_at IS NULL OR closed_at >= created_at);

-- Fix the recent trades index to use a constant interval
DROP INDEX IF EXISTS idx_trades_recent;
CREATE INDEX idx_trades_recent 
ON trades(user_id, created_at)
WHERE created_at > '2025-06-01 00:00:00'::timestamp;