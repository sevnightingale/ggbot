-- Seed funding rate data source and data points
-- Part of Market Intelligence Phase 1: Free Quick Wins

-- Step 1: Insert crypto_derivatives data source
INSERT INTO data_sources (name, display_name, description, enabled, requires_premium)
VALUES (
    'crypto_derivatives',
    'Crypto Derivatives',
    'Perpetual futures funding rates and leverage metrics showing long/short positioning. Extreme funding rates indicate overleveraged positions and potential liquidation cascades.',
    TRUE,
    FALSE  -- FREE data source!
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    enabled = EXCLUDED.enabled,
    updated_at = NOW();

-- Step 2: Insert BTC funding rate data point
INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
VALUES (
    (SELECT source_id FROM data_sources WHERE name = 'crypto_derivatives'),
    'btc_funding_rate',
    'BTC Funding Rate',
    'Binance perpetual futures funding rate for BTC/USDT. Positive rates indicate long-heavy positioning (longs pay shorts), negative rates indicate short-heavy positioning. Extreme rates (>±1%) signal overleveraged positions and liquidation risk.',
    ARRAY['funding_rate_btc']::TEXT[],
    FALSE,  -- FREE data point!
    TRUE,
    0
)
ON CONFLICT (source_id, name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config_values = EXCLUDED.config_values,
    enabled = EXCLUDED.enabled,
    sort_order = EXCLUDED.sort_order,
    updated_at = NOW();

-- Step 3: Insert ETH funding rate data point
INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
VALUES (
    (SELECT source_id FROM data_sources WHERE name = 'crypto_derivatives'),
    'eth_funding_rate',
    'ETH Funding Rate',
    'Binance perpetual futures funding rate for ETH/USDT. Positive rates indicate long-heavy positioning, negative rates indicate short-heavy positioning. Useful for detecting overcrowded trades and potential reversals.',
    ARRAY['funding_rate_eth']::TEXT[],
    FALSE,  -- FREE data point!
    TRUE,
    1
)
ON CONFLICT (source_id, name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config_values = EXCLUDED.config_values,
    enabled = EXCLUDED.enabled,
    sort_order = EXCLUDED.sort_order,
    updated_at = NOW();

-- Verify insertion
SELECT
    ds.name as source_name,
    ds.display_name as source_display,
    ds.enabled as source_enabled,
    ds.requires_premium as source_premium,
    dp.name as point_name,
    dp.display_name as point_display,
    dp.config_values,
    dp.enabled as point_enabled,
    dp.requires_premium as point_premium
FROM data_sources ds
JOIN data_points dp ON ds.source_id = dp.source_id
WHERE ds.name = 'crypto_derivatives'
ORDER BY dp.sort_order;
