-- Seed Market Conditions data source and data point
-- Part of Sebastian Market Intelligence integration
-- Created: 2026-03-20

-- =============================================================================
-- Data Source: Market Conditions (new category)
-- =============================================================================

INSERT INTO data_sources (name, display_name, description, enabled, requires_premium)
VALUES (
    'market_conditions',
    'Market Conditions',
    'Daily cross-market intelligence report covering equities, bonds, commodities, crypto, monetary policy, geopolitics, and dominant narratives. AI research agent synthesizes web data into actionable market regime assessment. Updated daily.',
    TRUE,
    FALSE  -- FREE — platform-produced intelligence, no marginal cost
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    enabled = EXCLUDED.enabled,
    requires_premium = EXCLUDED.requires_premium,
    updated_at = NOW();

-- =============================================================================
-- Data Point: Daily Market Brief
-- =============================================================================

INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
VALUES (
    (SELECT source_id FROM data_sources WHERE name = 'market_conditions'),
    'daily_brief',
    'Daily Market Brief',
    'Cross-domain market regime assessment: equities, bonds, commodities, crypto, geopolitics, monetary policy, and dominant narratives. Identifies risk-on/risk-off regime, causal chains across markets, and key narratives driving price action. Updated daily by AI research agent.',
    ARRAY['market_conditions']::TEXT[],
    FALSE,  -- FREE
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

-- =============================================================================
-- Verification
-- =============================================================================

SELECT
    ds.name as source_name,
    ds.display_name as source_display,
    dp.name as point_name,
    dp.display_name as point_display,
    dp.enabled
FROM data_sources ds
JOIN data_points dp ON ds.source_id = dp.source_id
WHERE ds.name = 'market_conditions';
