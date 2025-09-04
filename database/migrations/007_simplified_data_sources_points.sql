-- Migration 007: Simplified data_sources <> data_points schema
-- Replaces over-engineered indicators + user_indicator_access with clean structure
-- Date: 2025-01-04

BEGIN;

-- =====================================================
-- STEP 1: Drop over-engineered tables
-- =====================================================

DROP TABLE IF EXISTS user_indicator_access CASCADE;

-- Rename indicators to data_points and restructure
DROP TABLE IF EXISTS indicators CASCADE;

-- Keep data_sources but simplify it (remove if it doesn't exist)
DROP TABLE IF EXISTS data_sources CASCADE;

-- =====================================================
-- STEP 2: Create new simplified schema
-- =====================================================

-- Data sources (categories like "Technical Analysis", "Signals")
CREATE TABLE data_sources (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,              -- "technical_analysis", "signals_group_chats"
    display_name VARCHAR(100) NOT NULL,            -- "Technical Analysis", "Signals in Group Chats" 
    description TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    requires_premium BOOLEAN DEFAULT FALSE,        -- Whole category premium gate
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Data points (specific indicators/signals within each source)
CREATE TABLE data_points (
    data_point_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES data_sources(source_id) ON DELETE CASCADE,
    
    name VARCHAR(50) NOT NULL,                     -- "RSI", "MACD", "ggShot"
    display_name VARCHAR(100) NOT NULL,            -- "RSI (Relative Strength Index)"
    description TEXT,
    
    -- CRITICAL: What goes into config_data JSONB
    config_values TEXT[] NOT NULL,                 -- ["RSI_5m", "RSI_15m", "RSI_30m", "RSI_1h", "RSI_4h", "RSI_1d", "RSI_1w"]
    
    requires_premium BOOLEAN DEFAULT FALSE,        -- Individual data point premium gate
    enabled BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(source_id, name)
);

-- =====================================================
-- STEP 3: Create indexes for performance
-- =====================================================

CREATE INDEX idx_data_sources_enabled ON data_sources(enabled, sort_order);
CREATE INDEX idx_data_sources_premium ON data_sources(requires_premium, enabled);

CREATE INDEX idx_data_points_source ON data_points(source_id, enabled, sort_order);
CREATE INDEX idx_data_points_premium ON data_points(requires_premium, enabled);
CREATE INDEX idx_data_points_name ON data_points(name);

-- =====================================================
-- STEP 4: Row Level Security (RLS)
-- =====================================================

-- Enable RLS (these are reference tables - all authenticated users can read)
ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_points ENABLE ROW LEVEL SECURITY;

-- Allow all authenticated users to read enabled data sources and points
CREATE POLICY "Authenticated users can read enabled data sources" ON data_sources
    FOR SELECT USING (auth.role() = 'authenticated' AND enabled = true);

CREATE POLICY "Authenticated users can read enabled data points" ON data_points  
    FOR SELECT USING (auth.role() = 'authenticated' AND enabled = true);

-- Service role can manage everything
CREATE POLICY "Service role full access data sources" ON data_sources
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access data points" ON data_points
    FOR ALL USING (auth.role() = 'service_role');

-- =====================================================
-- STEP 5: Populate with initial data
-- =====================================================

-- Technical Analysis data source
INSERT INTO data_sources (name, display_name, description, enabled, requires_premium, sort_order) VALUES
('technical_analysis', 'Technical Analysis', 'Core technical indicators for market analysis', true, false, 1);

-- Get the technical analysis source ID for reference
DO $$
DECLARE
    tech_source_id UUID;
BEGIN
    SELECT source_id INTO tech_source_id FROM data_sources WHERE name = 'technical_analysis';
    
    -- Technical indicators with all timeframes
    INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order) VALUES
    -- Momentum indicators
    (tech_source_id, 'RSI', 'RSI (Relative Strength Index)', 'Momentum oscillator measuring speed and magnitude of price changes', 
     ARRAY['RSI_5m', 'RSI_15m', 'RSI_30m', 'RSI_1h', 'RSI_4h', 'RSI_1d', 'RSI_1w'], false, true, 1),
    
    (tech_source_id, 'MACD', 'MACD (Moving Average Convergence Divergence)', 'Trend-following momentum indicator', 
     ARRAY['MACD_5m', 'MACD_15m', 'MACD_30m', 'MACD_1h', 'MACD_4h', 'MACD_1d', 'MACD_1w'], false, true, 2),
    
    (tech_source_id, 'Stochastic', 'Stochastic Oscillator', 'Momentum indicator comparing closing price to price range', 
     ARRAY['STOCH_5m', 'STOCH_15m', 'STOCH_30m', 'STOCH_1h', 'STOCH_4h', 'STOCH_1d', 'STOCH_1w'], false, true, 3),
    
    (tech_source_id, 'Williams_R', 'Williams %R', 'Momentum indicator measuring overbought/oversold levels', 
     ARRAY['WILLR_5m', 'WILLR_15m', 'WILLR_30m', 'WILLR_1h', 'WILLR_4h', 'WILLR_1d', 'WILLR_1w'], false, true, 4),
    
    (tech_source_id, 'CCI', 'CCI (Commodity Channel Index)', 'Momentum oscillator measuring price deviation from average', 
     ARRAY['CCI_5m', 'CCI_15m', 'CCI_30m', 'CCI_1h', 'CCI_4h', 'CCI_1d', 'CCI_1w'], false, true, 5),
    
    (tech_source_id, 'MFI', 'MFI (Money Flow Index)', 'Volume-weighted momentum indicator', 
     ARRAY['MFI_5m', 'MFI_15m', 'MFI_30m', 'MFI_1h', 'MFI_4h', 'MFI_1d', 'MFI_1w'], false, true, 6),
    
    (tech_source_id, 'ROC', 'ROC (Rate of Change)', 'Momentum oscillator measuring percentage change', 
     ARRAY['ROC_5m', 'ROC_15m', 'ROC_30m', 'ROC_1h', 'ROC_4h', 'ROC_1d', 'ROC_1w'], false, true, 7),
    
    (tech_source_id, 'Aroon', 'Aroon Indicator', 'Trend indicator identifying trend changes', 
     ARRAY['AROON_5m', 'AROON_15m', 'AROON_30m', 'AROON_1h', 'AROON_4h', 'AROON_1d', 'AROON_1w'], false, true, 8),
    
    (tech_source_id, 'Vortex', 'Vortex Indicator', 'Oscillator identifying trend reversals', 
     ARRAY['VI_5m', 'VI_15m', 'VI_30m', 'VI_1h', 'VI_4h', 'VI_1d', 'VI_1w'], false, true, 9),
    
    (tech_source_id, 'TRIX', 'TRIX', 'Triple exponential moving average oscillator', 
     ARRAY['TRIX_5m', 'TRIX_15m', 'TRIX_30m', 'TRIX_1h', 'TRIX_4h', 'TRIX_1d', 'TRIX_1w'], false, true, 10),
    
    -- Trend indicators
    (tech_source_id, 'ADX', 'ADX (Average Directional Index)', 'Trend strength indicator', 
     ARRAY['ADX_5m', 'ADX_15m', 'ADX_30m', 'ADX_1h', 'ADX_4h', 'ADX_1d', 'ADX_1w'], false, true, 11),
    
    (tech_source_id, 'PSAR', 'Parabolic SAR', 'Trend-following indicator showing potential reversal points', 
     ARRAY['PSAR_5m', 'PSAR_15m', 'PSAR_30m', 'PSAR_1h', 'PSAR_4h', 'PSAR_1d', 'PSAR_1w'], false, true, 12),
    
    (tech_source_id, 'EMA', 'EMA (Exponential Moving Average)', 'Trend-following moving average giving more weight to recent prices', 
     ARRAY['EMA_5m', 'EMA_15m', 'EMA_30m', 'EMA_1h', 'EMA_4h', 'EMA_1d', 'EMA_1w'], false, true, 13),
    
    (tech_source_id, 'SMA', 'SMA (Simple Moving Average)', 'Basic trend-following moving average', 
     ARRAY['SMA_5m', 'SMA_15m', 'SMA_30m', 'SMA_1h', 'SMA_4h', 'SMA_1d', 'SMA_1w'], false, true, 14),
    
    -- Volatility indicators
    (tech_source_id, 'BB', 'Bollinger Bands', 'Volatility bands around moving average', 
     ARRAY['BB_5m', 'BB_15m', 'BB_30m', 'BB_1h', 'BB_4h', 'BB_1d', 'BB_1w'], false, true, 15),
    
    (tech_source_id, 'KC', 'Keltner Channels', 'Volatility-based envelope indicator', 
     ARRAY['KC_5m', 'KC_15m', 'KC_30m', 'KC_1h', 'KC_4h', 'KC_1d', 'KC_1w'], false, true, 16),
    
    (tech_source_id, 'DC', 'Donchian Channels', 'Price channel indicator based on highest high and lowest low', 
     ARRAY['DC_5m', 'DC_15m', 'DC_30m', 'DC_1h', 'DC_4h', 'DC_1d', 'DC_1w'], false, true, 17),
    
    (tech_source_id, 'ATR', 'ATR (Average True Range)', 'Volatility indicator measuring price movement', 
     ARRAY['ATR_5m', 'ATR_15m', 'ATR_30m', 'ATR_1h', 'ATR_4h', 'ATR_1d', 'ATR_1w'], false, true, 18),
    
    (tech_source_id, 'BBW', 'Bollinger Band Width', 'Measures the width between Bollinger Bands', 
     ARRAY['BBW_5m', 'BBW_15m', 'BBW_30m', 'BBW_1h', 'BBW_4h', 'BBW_1d', 'BBW_1w'], false, true, 19),
    
    -- Volume indicators
    (tech_source_id, 'OBV', 'OBV (On-Balance Volume)', 'Volume-based momentum indicator', 
     ARRAY['OBV_5m', 'OBV_15m', 'OBV_30m', 'OBV_1h', 'OBV_4h', 'OBV_1d', 'OBV_1w'], false, true, 20),
    
    (tech_source_id, 'VWAP', 'VWAP (Volume Weighted Average Price)', 'Volume-weighted average price indicator', 
     ARRAY['VWAP_5m', 'VWAP_15m', 'VWAP_30m', 'VWAP_1h', 'VWAP_4h', 'VWAP_1d', 'VWAP_1w'], false, true, 21);
END $$;

-- Premium Signals data source
INSERT INTO data_sources (name, display_name, description, enabled, requires_premium, sort_order) VALUES
('signals_group_chats', 'Signals in Group Chats', 'Premium AI-filtered trading signals from monitored channels', true, true, 2);

-- Get the signals source ID and add ggShot premium signal
DO $$
DECLARE
    signals_source_id UUID;
BEGIN
    SELECT source_id INTO signals_source_id FROM data_sources WHERE name = 'signals_group_chats';
    
    INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order) VALUES
    (signals_source_id, 'ggShot', 'ggShot Premium Signals', 'AI-filtered premium trading signals from 140+ cryptocurrency pairs with confidence scoring', 
     ARRAY['ggShot'], true, true, 1);
END $$;

-- Future data sources (disabled for now)
INSERT INTO data_sources (name, display_name, description, enabled, requires_premium, sort_order) VALUES
('fundamental_analysis', 'Fundamental Analysis', 'Economic indicators and financial metrics', false, true, 3),
('sentiment_trends', 'Sentiment & Trends on Social Media', 'Social media sentiment analysis and trend detection', false, true, 4),
('influencer_kol', 'Influencer/Key Opinion Leaders', 'Key opinion leader analysis and influence tracking', false, true, 5),
('news_regulatory', 'News & Regulatory Actions', 'News analysis and regulatory impact assessment', false, true, 6),
('onchain_analytics', 'On-Chain Analytics', 'Blockchain-based analytics and metrics', false, true, 7);

-- =====================================================
-- STEP 6: Add paid_data_points to user_profiles
-- =====================================================

-- Add flexible premium data points array to user profiles
ALTER TABLE user_profiles 
ADD COLUMN paid_data_points TEXT[] DEFAULT ARRAY[]::TEXT[];

-- Create index for efficient array searches
CREATE INDEX idx_user_profiles_paid_data_points ON user_profiles USING GIN (paid_data_points);

-- Add comment for documentation
COMMENT ON COLUMN user_profiles.paid_data_points IS 'Array of premium data point names user has access to (e.g., ["ggShot", "premium_indicator_x"])';

-- =====================================================
-- STEP 7: Create updated_at trigger
-- =====================================================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic updated_at
CREATE TRIGGER update_data_sources_updated_at BEFORE UPDATE ON data_sources 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_points_updated_at BEFORE UPDATE ON data_points 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;

-- =====================================================
-- Verify migration
-- =====================================================

-- Check data was inserted correctly
SELECT 
    ds.display_name as data_source,
    COUNT(dp.data_point_id) as data_points_count,
    COUNT(CASE WHEN dp.requires_premium THEN 1 END) as premium_count
FROM data_sources ds
LEFT JOIN data_points dp ON ds.source_id = dp.source_id
WHERE ds.enabled = true
GROUP BY ds.source_id, ds.display_name
ORDER BY ds.sort_order;