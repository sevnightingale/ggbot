-- Market Conditions Table
-- Daily market intelligence reports produced by Sebastian (AI research agent)
-- Consumed by MI pipeline as a data source for bot decision-making
-- Created: 2026-03-20

CREATE TABLE IF NOT EXISTS market_conditions (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    generated_at timestamptz NOT NULL,
    schema_version varchar(10) DEFAULT '0.1',
    regime jsonb NOT NULL,          -- {overall, confidence, primary_driver}
    domains jsonb NOT NULL,         -- {equities, bonds, commodities, crypto, fed_policy, geopolitics}
    narratives jsonb NOT NULL,      -- [{name, strength, direction, implication}, ...]
    synthesis text NOT NULL,        -- Narrative synthesis paragraph (the money shot)
    data_quality jsonb,             -- {high_confidence: [...], medium_confidence: [...], low_confidence: [...]}
    raw_tables jsonb,               -- Full granular data from research pass (per-metric confidence preserved)
    created_at timestamptz DEFAULT now()
);

-- Primary access pattern: get the latest report
CREATE INDEX idx_market_conditions_generated ON market_conditions(generated_at DESC);

-- RLS: backend-only table (no direct Supabase client access)
-- Access is via authenticated API endpoints with service auth
