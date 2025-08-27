-- =============================================================
-- ggShot Filter Decision Logging Table
-- Migration: 0014_create_ggshot_filter_table.sql
-- Simple table to track ggShot filter decisions for analysis
-- =============================================================

CREATE TABLE ggshot_filter (
    filter_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(20) NOT NULL,
    signal_direction VARCHAR(10), -- 'LONG', 'SHORT'
    confidence_score NUMERIC(4,3) NOT NULL, -- 0.000-1.000
    filter_status VARCHAR(10) NOT NULL, -- 'APPROVED', 'REJECTED'
    reasoning_text TEXT,
    entry_price DECIMAL(20,8),
    stop_loss_price DECIMAL(20,8),
    take_profit_price DECIMAL(20,8),
    signal_timeframe VARCHAR(10), -- '15m', '30m', '1h', etc.
    volume_analysis TEXT,
    original_signal_text TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Add indexes for common queries
CREATE INDEX idx_ggshot_filter_symbol ON ggshot_filter(symbol);
CREATE INDEX idx_ggshot_filter_confidence ON ggshot_filter(confidence_score);
CREATE INDEX idx_ggshot_filter_status ON ggshot_filter(filter_status);
CREATE INDEX idx_ggshot_filter_created ON ggshot_filter(created_at);

-- Add comments
COMMENT ON TABLE ggshot_filter IS 'Tracks all ggShot signal filter decisions for analysis and monitoring';
COMMENT ON COLUMN ggshot_filter.confidence_score IS 'LLM confidence score (0.000-1.000)';
COMMENT ON COLUMN ggshot_filter.filter_status IS 'Whether signal was approved or rejected by filter';
COMMENT ON COLUMN ggshot_filter.reasoning_text IS 'Full LLM reasoning for the decision';

-- Verification
SELECT 'ggshot_filter' as table_name, COUNT(*) as column_count 
FROM information_schema.columns 
WHERE table_name = 'ggshot_filter';