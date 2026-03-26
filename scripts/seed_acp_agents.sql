-- Seed ACP agent data points under agentic_intelligence source
-- These appear in the frontend bot builder automatically
-- Part of ACP Agent Intelligence initiative
-- Created: 2026-03-24

-- =============================================================================
-- ACP Agent Data Points (under existing agentic_intelligence source)
-- =============================================================================

-- ggbots.ai — Self-consumption via ACP (generates $GG graduation volume)
INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
VALUES (
    (SELECT source_id FROM data_sources WHERE name = 'agentic_intelligence'),
    'ggbots_acp',
    'ggbots.ai — Market Brief (ACP)',
    'Cross-market intelligence brief from ggbots.ai via Virtuals ACP protocol. Covers market regime, equities, bonds, commodities, crypto, geopolitics, monetary policy, and dominant narratives. Each invocation generates an on-chain ACP transaction.',
    ARRAY['acp_agent']::TEXT[],
    FALSE,
    TRUE,
    5
)
ON CONFLICT (source_id, name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config_values = EXCLUDED.config_values,
    enabled = EXCLUDED.enabled,
    sort_order = EXCLUDED.sort_order,
    updated_at = NOW();

-- Otto AI — Crypto News (uncomment when wallet address is discovered)
-- INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
-- VALUES (
--     (SELECT source_id FROM data_sources WHERE name = 'agentic_intelligence'),
--     'otto_ai_news',
--     'Otto AI — Crypto News (ACP)',
--     'Real-time crypto news aggregation and analysis from Otto AI via Virtuals ACP. Curated headlines with sentiment scoring. Per-symbol analysis.',
--     ARRAY['acp_agent']::TEXT[],
--     FALSE,
--     TRUE,
--     10
-- )
-- ON CONFLICT (source_id, name) DO UPDATE SET
--     display_name = EXCLUDED.display_name,
--     description = EXCLUDED.description,
--     config_values = EXCLUDED.config_values,
--     enabled = EXCLUDED.enabled,
--     sort_order = EXCLUDED.sort_order,
--     updated_at = NOW();

-- Wolfpack Intelligence — Composite Risk Score (uncomment when wallet address is discovered)
-- INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
-- VALUES (
--     (SELECT source_id FROM data_sources WHERE name = 'agentic_intelligence'),
--     'wolfpack_risk',
--     'Wolfpack — Risk Score (ACP)',
--     'Composite risk scoring for crypto assets from Wolfpack Intelligence via Virtuals ACP. Multi-factor risk analysis per symbol.',
--     ARRAY['acp_agent']::TEXT[],
--     FALSE,
--     TRUE,
--     20
-- )
-- ON CONFLICT (source_id, name) DO UPDATE SET
--     display_name = EXCLUDED.display_name,
--     description = EXCLUDED.description,
--     config_values = EXCLUDED.config_values,
--     enabled = EXCLUDED.enabled,
--     sort_order = EXCLUDED.sort_order,
--     updated_at = NOW();

-- BlackSwan — Prediction Market Monitor (uncomment when wallet address is discovered)
-- INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
-- VALUES (
--     (SELECT source_id FROM data_sources WHERE name = 'agentic_intelligence'),
--     'blackswan_predictions',
--     'BlackSwan — Predictions (ACP)',
--     'Prediction market monitoring and anomaly detection from BlackSwan via Virtuals ACP. Tracks Polymarket and other prediction platforms.',
--     ARRAY['acp_agent']::TEXT[],
--     FALSE,
--     TRUE,
--     30
-- )
-- ON CONFLICT (source_id, name) DO UPDATE SET
--     display_name = EXCLUDED.display_name,
--     description = EXCLUDED.description,
--     config_values = EXCLUDED.config_values,
--     enabled = EXCLUDED.enabled,
--     sort_order = EXCLUDED.sort_order,
--     updated_at = NOW();

-- =============================================================================
-- Verification
-- =============================================================================

SELECT
    ds.name as source_name,
    dp.name as point_name,
    dp.display_name,
    dp.enabled,
    dp.sort_order
FROM data_sources ds
JOIN data_points dp ON ds.source_id = dp.source_id
WHERE ds.name = 'agentic_intelligence'
ORDER BY dp.sort_order;
