-- Seed Grok-Powered Market Intelligence Data Points
-- Part of Market Intelligence Phase 1: Intelligence Orchestrator + GrokAgenticAdapter
-- 8 new data points across 4 categories (all using GrokAgenticAdapter)

-- =============================================================================
-- Step 1: Insert/Update Data Sources (4 new categories)
-- =============================================================================

-- 1. Macro Economics (FREE - VIX, DXY, CPI, NFP accessible to all)
INSERT INTO data_sources (name, display_name, description, enabled, requires_premium)
VALUES (
    'macro_economics',
    'Macro Economics',
    'Global macro indicators (VIX volatility index, DXY dollar index, CPI inflation, NFP jobs) that influence crypto risk-on/risk-off sentiment. Grok-powered via autonomous web search.',
    TRUE,
    FALSE  -- FREE - macro indicators benefit all users
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    enabled = EXCLUDED.enabled,
    updated_at = NOW();

-- 2. On-Chain Analytics (FREE for now - shared caching makes this scalable)
INSERT INTO data_sources (name, display_name, description, enabled, requires_premium)
VALUES (
    'onchain_analytics',
    'On-Chain Analytics',
    'Blockchain data analysis including Bitcoin TVL in DeFi and whale wallet movements. Grok-powered via autonomous research of on-chain data sources (DefiLlama, Dune Analytics, whale alerts).',
    TRUE,
    FALSE  -- FREE - shared caching economics allow free access
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    enabled = EXCLUDED.enabled,
    requires_premium = EXCLUDED.requires_premium,
    updated_at = NOW();

-- 3. Sentiment & Social (FREE for now - shared caching makes this scalable)
INSERT INTO data_sources (name, display_name, description, enabled, requires_premium)
VALUES (
    'sentiment_social',
    'Sentiment & Social',
    'Social media sentiment analysis from Twitter/X, Reddit, and crypto communities. Grok-powered via X search and NLP to gauge market psychology and narrative shifts.',
    TRUE,
    FALSE  -- FREE - shared caching economics allow free access
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    enabled = EXCLUDED.enabled,
    requires_premium = EXCLUDED.requires_premium,
    updated_at = NOW();

-- 4. News & Regulatory (FREE for now - shared caching makes this scalable)
INSERT INTO data_sources (name, display_name, description, enabled, requires_premium)
VALUES (
    'news_regulatory',
    'News & Regulatory',
    'Breaking crypto news headlines and regulatory events. Grok-powered via web and X search to identify market-moving catalysts and policy changes.',
    TRUE,
    FALSE  -- FREE - shared caching economics allow free access
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    enabled = EXCLUDED.enabled,
    requires_premium = EXCLUDED.requires_premium,
    updated_at = NOW();

-- =============================================================================
-- Step 2: Insert Data Points (8 new Grok-powered indicators)
-- =============================================================================

-- -------------------------
-- MACRO ECONOMICS (FREE)
-- -------------------------

-- VIX Index
INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
VALUES (
    (SELECT source_id FROM data_sources WHERE name = 'macro_economics'),
    'vix',
    'VIX Volatility Index',
    'CBOE VIX Index measuring stock market volatility expectations. VIX > 30 indicates fear (risk-off, bearish for crypto), VIX < 15 indicates complacency (risk-on, bullish for crypto). Grok autonomously fetches live VIX data from financial sources.',
    ARRAY['vix_index']::TEXT[],
    FALSE,  -- FREE - macro indicator
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

-- DXY Index
INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
VALUES (
    (SELECT source_id FROM data_sources WHERE name = 'macro_economics'),
    'dxy',
    'DXY Dollar Index',
    'US Dollar strength index (DXY). Strong dollar (DXY rising) typically bearish for crypto due to inverse correlation. Weak dollar (DXY falling) typically bullish for crypto. Grok fetches live DXY data and trend analysis.',
    ARRAY['dxy_index']::TEXT[],
    FALSE,  -- FREE - macro indicator
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

-- CPI Inflation
INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
VALUES (
    (SELECT source_id FROM data_sources WHERE name = 'macro_economics'),
    'cpi',
    'CPI Inflation',
    'US Consumer Price Index measuring inflation. High inflation (>4%) drives Fed hawkishness (bearish for crypto). Declining inflation enables Fed dovish pivot (bullish for crypto). Grok fetches latest CPI data and Fed policy implications.',
    ARRAY['cpi_inflation']::TEXT[],
    FALSE,  -- FREE - macro indicator
    TRUE,
    2
)
ON CONFLICT (source_id, name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config_values = EXCLUDED.config_values,
    enabled = EXCLUDED.enabled,
    sort_order = EXCLUDED.sort_order,
    updated_at = NOW();

-- NFP Jobs Report
INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
VALUES (
    (SELECT source_id FROM data_sources WHERE name = 'macro_economics'),
    'nfp',
    'NFP Jobs Report',
    'US Nonfarm Payrolls measuring employment strength. Strong jobs (>300k) signals Fed hawkishness (bearish for crypto). Weak jobs (<100k) signals Fed dovish pivot (bullish for crypto). Grok fetches latest NFP data and economic health assessment.',
    ARRAY['nfp_jobs']::TEXT[],
    FALSE,  -- FREE - macro indicator
    TRUE,
    3
)
ON CONFLICT (source_id, name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config_values = EXCLUDED.config_values,
    enabled = EXCLUDED.enabled,
    sort_order = EXCLUDED.sort_order,
    updated_at = NOW();

-- -------------------------
-- ON-CHAIN ANALYTICS (FREE)
-- -------------------------

-- BTC TVL
INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
VALUES (
    (SELECT source_id FROM data_sources WHERE name = 'onchain_analytics'),
    'btc_tvl',
    'Bitcoin TVL in DeFi',
    'Total Value Locked (TVL) of Bitcoin in DeFi protocols. Rising TVL indicates BTC accumulation in DeFi (reduced sell pressure, bullish). Falling TVL indicates BTC withdrawals (potential selling, bearish). Grok fetches TVL data from DefiLlama and on-chain sources.',
    ARRAY['btc_tvl']::TEXT[],
    FALSE,  -- FREE - shared caching economics
    TRUE,
    0
)
ON CONFLICT (source_id, name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config_values = EXCLUDED.config_values,
    requires_premium = EXCLUDED.requires_premium,
    enabled = EXCLUDED.enabled,
    sort_order = EXCLUDED.sort_order,
    updated_at = NOW();

-- Whale Activity
INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
VALUES (
    (SELECT source_id FROM data_sources WHERE name = 'onchain_analytics'),
    'whale_activity',
    'Whale Activity',
    'Large wallet movements and exchange flows (>$1M transfers). Net outflows from exchanges = whale accumulation (bullish). Net inflows to exchanges = whale distribution (bearish). Grok analyzes whale alerts and on-chain data for accumulation/distribution patterns.',
    ARRAY['whale_activity']::TEXT[],
    FALSE,  -- FREE - shared caching economics
    TRUE,
    1
)
ON CONFLICT (source_id, name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config_values = EXCLUDED.config_values,
    requires_premium = EXCLUDED.requires_premium,
    enabled = EXCLUDED.enabled,
    sort_order = EXCLUDED.sort_order,
    updated_at = NOW();

-- -------------------------
-- SENTIMENT & SOCIAL (FREE)
-- -------------------------

-- Twitter Sentiment
INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
VALUES (
    (SELECT source_id FROM data_sources WHERE name = 'sentiment_social'),
    'twitter_sentiment',
    'Twitter/X Sentiment',
    'Social sentiment analysis from Twitter/X posts over the last 24 hours. Sentiment score ranges from -1.0 (very bearish) to +1.0 (very bullish). Grok uses X search and NLP to analyze sentiment, identify key themes, and track influencer positioning.',
    ARRAY['twitter_sentiment']::TEXT[],
    FALSE,  -- FREE - shared caching economics
    TRUE,
    0
)
ON CONFLICT (source_id, name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config_values = EXCLUDED.config_values,
    requires_premium = EXCLUDED.requires_premium,
    enabled = EXCLUDED.enabled,
    sort_order = EXCLUDED.sort_order,
    updated_at = NOW();

-- -------------------------
-- NEWS & REGULATORY (FREE)
-- -------------------------

-- Crypto News
INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
VALUES (
    (SELECT source_id FROM data_sources WHERE name = 'news_regulatory'),
    'crypto_news',
    'Breaking Crypto News',
    'Recent breaking crypto news and headlines (last 6 hours). Categorized by sentiment (bullish/bearish/neutral) and importance (high/medium/low). Types include regulation, technology, adoption, partnerships. Grok searches crypto news sites and X for market-moving headlines.',
    ARRAY['crypto_news']::TEXT[],
    FALSE,  -- FREE - shared caching economics
    TRUE,
    0
)
ON CONFLICT (source_id, name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config_values = EXCLUDED.config_values,
    requires_premium = EXCLUDED.requires_premium,
    enabled = EXCLUDED.enabled,
    sort_order = EXCLUDED.sort_order,
    updated_at = NOW();

-- =============================================================================
-- Step 3: Verification Query
-- =============================================================================

-- Verify all 8 new Grok data points were inserted
SELECT
    ds.name as source_name,
    ds.display_name as source_display,
    ds.enabled as source_enabled,
    ds.requires_premium as source_premium,
    dp.name as point_name,
    dp.display_name as point_display,
    dp.config_values,
    dp.enabled as point_enabled,
    dp.requires_premium as point_premium,
    dp.sort_order
FROM data_sources ds
JOIN data_points dp ON ds.source_id = dp.source_id
WHERE ds.name IN ('macro_economics', 'onchain_analytics', 'sentiment_social', 'news_regulatory')
ORDER BY ds.name, dp.sort_order;

-- Summary count
SELECT
    ds.name as category,
    ds.requires_premium as premium_required,
    COUNT(dp.data_point_id) as data_point_count
FROM data_sources ds
JOIN data_points dp ON ds.source_id = dp.source_id
WHERE ds.name IN ('macro_economics', 'onchain_analytics', 'sentiment_social', 'news_regulatory')
GROUP BY ds.name, ds.requires_premium
ORDER BY ds.name;
