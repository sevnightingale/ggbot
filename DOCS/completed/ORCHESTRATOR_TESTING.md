# Intelligence Orchestrator - Testing & Validation Guide

**Date**: 2025-10-27
**Status**: Implementation Complete - Ready for Testing

---

## 🎯 What Was Built

The Intelligence Orchestrator is a lightweight module that enables scalable market intelligence integration (funding rates, macro data, on-chain, sentiment, news) without bloating ggbot.py.

### Architecture

```
Config → Orchestrator → MarketIntelligence Gateway → Adapters → Data Sources
   ↓            ↓                    ↓                    ↓            ↓
User     Permission Check      Cache Layer         BinanceFunding   Binance API
Enabled        ↓                    ↓                    ↓            ↓
Sources    Route Queries        Redis TTL           Response      Live Data
   ↓            ↓                    ↓                    ↓
Aggregate Results → Decision Engine → LLM Prompt → AI Reasoning
```

### Key Components

1. **Orchestrator** (`market_intelligence/orchestrator.py`)
   - Reads `config.extraction.selected_data_sources`
   - Checks permissions (free vs premium)
   - Maps data_points → catalog data_types
   - Queries MarketIntelligence gateway
   - Returns dict organized by category

2. **Catalog Mapping** (`market_intelligence/catalog_mapping.py`)
   - Hardcoded mapping dictionary
   - Currently supports: ggshot, btc_funding_rate, eth_funding_rate
   - Easy to extend (just add entries)

3. **Decision Engine Integration** (`decision/engine_v2.py`)
   - Accepts `market_intelligence` parameter
   - 6 formatting methods for different categories
   - Injects formatted data into LLM prompts

4. **ggbot.py Integration**
   - Calls orchestrator after technical indicators
   - Passes market_intelligence to decision engine
   - Graceful degradation on errors

---

## ✅ Unit Tests Status

**Test File**: `tests/test_orchestrator.py`

**Results**: ✅ 16/16 tests passing

**Coverage**:
- Config parsing (filters technical_analysis, handles empty configs)
- Catalog mapping lookup (funding rates, ggshot, not found)
- Template replacement (symbol, timeframe, multiple templates)
- Permission checking (free data points, premium with/without access)
- Full integration (funding rates, empty configs, graceful degradation)

---

## 🧪 End-to-End Testing

### Prerequisites

1. **Active bot config** with `state = 'active'`
2. **User ID** associated with the config
3. **Symbol** that has funding rate data (BTC/USDT, ETH/USDT)

### Option 1: Automated Test Script

**Use the provided test script** (`scripts/test_funding_rates.py`):

```bash
# 1. Edit the script - replace placeholders:
#    USER_ID = "your-actual-user-id"
#    CONFIG_ID = "your-actual-config-id"

# 2. Run the test
source .venv/bin/activate
python scripts/test_funding_rates.py
```

**What it does**:
1. Loads your bot config
2. Enables funding rates (`btc_funding_rate`, `eth_funding_rate`)
3. Runs extraction (technical + funding rates)
4. Runs decision engine
5. Checks if funding rates appear in AI reasoning

**Expected Output**:
```
📋 Step 1: Loading config
✅ Config loaded: Test Bot
   Symbol: BTC/USDT

⚙️  Step 2: Enabling funding rates
✅ Funding rates enabled:
   - BTC Funding Rate
   - ETH Funding Rate

📊 Step 3: Running extraction
✅ Market intelligence: 2 data points from 1 categories (derivatives_leverage)

   BTC Funding Rate Details:
      Rate: 0.0026%
      Level: neutral
      Risk: minimal
      Implication: Neutral funding - no leverage warning signals

🧠 Step 4: Running decision engine
✅ Decision completed:
   Action: wait
   Confidence: 0.650
   ✅ FUNDING RATES MENTIONED IN REASONING!

📝 Decision Reasoning Excerpt:
   "The BTC funding rate is currently at 0.0026% (neutral level) with minimal
   risk. This indicates balanced positioning in the perpetual futures market
   with no excessive leverage on either side..."
```

---

### Option 2: Manual Testing via Database

**Step 1: Enable funding rates in a bot config**

```sql
-- Update an existing bot config
UPDATE configurations
SET config_data = jsonb_set(
    config_data,
    '{extraction,selected_data_sources,derivatives_leverage}',
    '{"data_points": ["btc_funding_rate", "eth_funding_rate"]}'
)
WHERE config_id = 'YOUR_CONFIG_ID';

-- Verify the update
SELECT
    config_id,
    config_name,
    config_data->'extraction'->'selected_data_sources'->'derivatives_leverage' as funding_config
FROM configurations
WHERE config_id = 'YOUR_CONFIG_ID';
```

**Step 2: Trigger a bot run**

```bash
# Option A: Via API (if bot is active)
# Wait for next scheduled run, or manually trigger via API endpoint

# Option B: Via PM2 restart (forces immediate re-evaluation)
pm2 restart ggbot

# Option C: Via Python console
source .venv/bin/activate
python
>>> import asyncio
>>> from ggbot import GGBotOrchestrator
>>> orchestrator = GGBotOrchestrator()
>>> asyncio.run(orchestrator._run_pipeline('YOUR_CONFIG_ID'))
```

**Step 3: Check decision logs**

```bash
# Watch logs in real-time
pm2 logs ggbot | grep -i "funding\|derivatives\|market intelligence"

# Or check database
SELECT
    decision_id,
    action,
    confidence,
    substring(reasoning, 1, 200) as reasoning_preview,
    created_at
FROM decisions
WHERE config_id = 'YOUR_CONFIG_ID'
ORDER BY created_at DESC
LIMIT 5;
```

---

## 🔍 What to Look For

### 1. Extraction Logs

**✅ Success indicators:**
```
✅ Market intelligence: 2 data points from 1 categories (derivatives_leverage)
✅ derivatives_leverage.btc_funding_rate: fetched from binance_funding (50ms, cached=false)
✅ derivatives_leverage.eth_funding_rate: fetched from binance_funding (45ms, cached=false)
```

**❌ Failure indicators:**
```
⚠️  No catalog mapping for derivatives_leverage.btc_funding_rate
⚠️  Failed to fetch derivatives_leverage.btc_funding_rate: [error details]
❌  Failed to fetch market intelligence (non-critical): [error]
```

### 2. Decision Reasoning

**✅ Funding rates mentioned:**
```
"The BTC funding rate is currently neutral at 0.0026%, indicating balanced
positioning without excessive leverage. ETH funding rate at 0.0063% shows
similar neutral conditions..."
```

**✅ Market intelligence section present:**
The LLM prompt should include:
```
## MARKET INTELLIGENCE
Additional market context beyond technical indicators:

## DERIVATIVES & LEVERAGE

**BTC Funding Rate**: 0.0026% (Neutral)
  - Risk Level: Minimal
  - Interpretation: Balanced positioning (0.003%)
  - Trading Implication: Neutral funding - no leverage warning signals
  - Next Funding: 2025-10-27T16:00:00+00:00
```

### 3. Database Verification

**Check decision record includes market intelligence:**
```sql
SELECT
    config_id,
    action,
    market_data->>'market_intelligence' as market_intel_snapshot
FROM decisions
WHERE config_id = 'YOUR_CONFIG_ID'
ORDER BY created_at DESC
LIMIT 1;
```

---

## 🐛 Troubleshooting

### Issue: "No market intelligence in extraction result"

**Possible Causes:**
1. Config not saved correctly
2. Orchestrator import error
3. Permission check failed (user lacks access)

**Debug Steps:**
```python
# 1. Check config
from core.services.config_service import ConfigService
config = await ConfigService().get_config(config_id, user_id)
print(config.extraction.get('selected_data_sources', {}))

# 2. Check permissions
from core.services.user_service import UserService
profile = await UserService().get_profile(user_id)
print(f"Paid data points: {profile.paid_data_points}")

# 3. Test orchestrator directly
from market_intelligence.orchestrator import fetch_market_intelligence
result = await fetch_market_intelligence(config, user_id, 'BTC/USDT')
print(result)
```

---

### Issue: "Funding rates not in decision reasoning"

**Possible Causes:**
1. LLM ignored the data (not relevant to strategy)
2. Prompt formatting error
3. Decision engine not receiving market_intelligence

**Debug Steps:**
```python
# 1. Check if decision engine received market intelligence
from decision.engine_v2 import DecisionEngineV2
engine = DecisionEngineV2(config_id, user_id)
await engine.initialize()

# Manually set market_intelligence
engine.market_intelligence = {
    'derivatives_leverage': {
        'btc_funding_rate': {'funding_rate_pct': 0.0026}
    }
}

# 2. Check formatting
formatted = engine._format_market_intelligence_for_llm()
print(formatted)  # Should show formatted section

# 3. Run decision and inspect prompt
# (Add logging to see full prompt sent to LLM)
```

---

### Issue: "Permission denied for funding rates"

**Solution:**

Funding rates are **free** data points (requires_premium = false in database).

**Check database:**
```sql
SELECT
    ds.name as source,
    dp.name as data_point,
    dp.requires_premium
FROM data_points dp
JOIN data_sources ds ON dp.source_id = ds.source_id
WHERE ds.name = 'derivatives_leverage';
```

**Should return:**
```
source                | data_point         | requires_premium
---------------------+--------------------+-----------------
derivatives_leverage | btc_funding_rate   | false
derivatives_leverage | eth_funding_rate   | false
```

If `requires_premium = true`, update:
```sql
UPDATE data_points
SET requires_premium = false
WHERE name IN ('btc_funding_rate', 'eth_funding_rate');
```

---

## 📊 Performance Expectations

**Orchestrator Overhead**: ~50-100ms (permission checks + mapping lookups)

**Gateway Query (cached)**: ~5-15ms per data point

**Gateway Query (uncached)**: ~50-150ms per data point (Binance API call)

**Total Added Latency**: ~100-300ms for 2 funding rates

**Cache TTL**: 1 hour (funding rates update every 8 hours, so 1hr is safe)

**Expected Cache Hit Rate**: >80% after first query

---

## ✨ Next Steps After Validation

Once funding rates are working end-to-end:

### Phase 4: Add Macro Data (5 indicators)

Add to `catalog_mapping.py`:
```python
# Macro Economics
('macro_economics', 'vix'): {
    'data_type': 'vix_index',
    'params_template': {}
},
('macro_economics', 'dxy'): {
    'data_type': 'dxy_index',
    'params_template': {}
},
# ... CPI, NFP, BTC TVL
```

**For each**:
1. Create adapter (e.g., `GrokSearchAdapter` or `FredApiAdapter`)
2. Create catalog YAML
3. Seed database (data_points table)
4. Test with script
5. Validate in decision reasoning

**Timeline**: 4-6 hours per indicator = 20-30 hours total

---

## 📝 Success Criteria

### Technical Checklist

- [x] ✅ Unit tests passing (16/16)
- [ ] ⏳ Funding rates in extraction result
- [ ] ⏳ Funding rates in decision reasoning
- [ ] ⏳ No errors in PM2 logs
- [ ] ⏳ Cache hit rate >80% after 2nd query
- [ ] ⏳ Decision latency <5s (including orchestrator)

### Business Checklist

- [ ] ⏳ User can toggle funding rates in UI (frontend work pending)
- [ ] ⏳ AI mentions funding rates in trading decisions
- [ ] ⏳ Zero regressions for existing bots (ggShot still works)
- [ ] ⏳ Ready to add 5 macro indicators (architecture validated)

---

## 🎓 Key Learnings

### Architecture Decisions

1. **Separate module** (not in ggbot.py) - prevents bloat
2. **Hardcoded mapping** (not YAML/DB) - fast, version controlled
3. **Keep ggShot hardcoded** (migrate later) - lower risk
4. **Graceful degradation** (log warning, continue) - resilience

### Scaling Path

Adding 150 data points:
- ✅ Orchestrator: 0 new lines (just iterates config)
- ✅ Mapping dict: +150 entries (in separate file)
- ✅ ggbot.py: 0 new lines (already complete)
- ✅ Decision engine: 0 new lines (formatting auto-routes)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-27
**Status**: Ready for End-to-End Testing
