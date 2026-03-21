-- Seed Agentic Intelligence data source and Sebastian data point
-- Part of ACP Agent Intelligence initiative
-- Created: 2026-03-21

-- =============================================================================
-- Data Source: Agentic Intelligence (ACP agent umbrella category)
-- =============================================================================

INSERT INTO data_sources (name, display_name, description, enabled, requires_premium)
VALUES (
    'agentic_intelligence',
    'Agentic Intelligence',
    'AI agent-produced market intelligence via Virtuals ACP (Agent Commerce Protocol). Curated agents provide cross-market analysis, sentiment research, and trading context. Updated daily or on-demand.',
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
-- Data Point: Sebastian — Daily Market Brief
-- =============================================================================

INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
VALUES (
    (SELECT source_id FROM data_sources WHERE name = 'agentic_intelligence'),
    'sebastian',
    'Sebastian — Daily Market Brief',
    'Cross-domain market regime assessment by Sebastian AI research agent. Covers equities, bonds, commodities, crypto, geopolitics, monetary policy, and dominant narratives. Identifies risk-on/risk-off regime, causal chains across markets, and key narratives driving price action. Updated daily.',
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

-- Future ACP agents would be added as additional data_points under the same source:
-- ('agentic_intelligence', 'agent_name'): 'Agent Display Name'

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
WHERE ds.name = 'agentic_intelligence';
