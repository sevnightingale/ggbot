# Market Data Intelligence Update

**Status**: 🟡 IN PROGRESS
**Created**: 2026-01-23
**Complexity**: Low-Medium (~4-6 hours total)
**Priority**: Medium

---

## Overview

Update market data intelligence stack:
1. **ggShot Soft Disable** - Remove from user-selectable data points (signals are 90+ days stale)
2. **Astrology Indicator** - Add cosmic timing signals via Grok agentic API
3. **Nansen API Exploration** - Leverage free credits to test on-chain intelligence

---

## 1. ggShot Soft Disable

### Problem
- ggShot signals in database are 90+ days old (stale data)
- No active ggShot integration currently running
- Users selecting ggShot get confusing/harmful outdated data
- Need to hide option without full code deletion (may re-enable later)

### Scope (What We're NOT Doing)
- ❌ NOT deleting `signals/listener_service.py`
- ❌ NOT deleting `signals/ggshot_parser.py`
- ❌ NOT deleting `market_intelligence/adapters/signals/ggshot_adapter.py`
- ❌ NOT removing PM2 service config (already stopped)
- ❌ NOT deleting historical signal data from `market_data` table

### Implementation

**Phase 1: Database** (~10 min)
```sql
-- Disable ggshot data point (soft delete)
UPDATE data_points
SET enabled = false
WHERE name = 'ggshot';

-- Optionally disable entire trading_signals source
UPDATE data_sources
SET enabled = false
WHERE name = 'trading_signals';
```

**Phase 2: Frontend** (~30 min)
- Remove `SignalsConfiguration` from Configure tabs
- File: `frontend/app/forge/components/configure/ConfigureLayout.tsx` (or wherever tabs are defined)
- Keep `SignalsConfiguration.tsx` file intact (archived for future use)

**Phase 3: Cleanup Any Hardcoded References** (~20 min)
- Search for `ggshot` references in frontend that might show UI elements
- Check `permissions.tsx` - may need to remove ggshot case or leave dormant

### Files to Modify
| File | Change |
|------|--------|
| Database `data_points` | Set `enabled=false` for ggshot |
| Database `data_sources` | Set `enabled=false` for trading_signals |
| `ConfigureLayout.tsx` or tab definition | Remove Signals tab |
| `permissions.tsx` | Leave ggshot case (dormant) or remove |

### Verification
- [ ] ggshot doesn't appear in data source selection UI
- [ ] Signals tab not visible in Configure section
- [ ] Existing bots with ggshot in config don't break (graceful handling)
- [ ] No console errors related to missing ggshot components

---

## 2. Astrology Indicator

### Rationale
Financial astrology provides timing signals based on planetary cycles, moon phases, and aspects. Not predictive, but correlative with collective psychology. Treat as sentiment overlay.

### Data Point Design

**Name**: `astro_timing`
**Category**: `sentiment_social`
**Cache TTL**: 21600 (6 hours - planetary positions change slowly)
**Cost**: ~$0.025/query (Grok web search)

### Implementation

**Phase 1: Grok Prompt Template** (~20 min)
File: `market_intelligence/adapters/agentic/grok_agentic.py`

```python
'astro_timing': """
Analyze current astrological factors relevant to crypto/financial markets:

1. **Moon Phase**: Current phase (New/Waxing/Full/Waning), days until next phase change
2. **Mercury Status**: Retrograde or direct, impact on trading/communication
3. **Major Aspects**: Any significant planetary aspects today (Jupiter trines, Saturn squares, etc.)
4. **Key Transits**: Notable planetary movements affecting market sentiment

Return JSON:
{
  "moon_phase": "<New Moon|Waxing Crescent|First Quarter|Waxing Gibbous|Full Moon|Waning Gibbous|Third Quarter|Waning Crescent>",
  "moon_phase_sentiment": "<bullish|bearish|neutral>",
  "mercury_retrograde": <true|false>,
  "major_aspects": ["<aspect description>", ...],
  "overall_signal": <-10 to +10 scale>,
  "interpretation": "<1-2 sentence market interpretation>",
  "caution_periods": ["<any high-volatility windows>"],
  "timestamp": "<ISO 8601>"
}

Focus on actionable timing signals, not fortune-telling. Be specific about dates/times.
"""
```

**Phase 2: Catalog Mapping** (~5 min)
File: `market_intelligence/catalog_mapping.py`

```python
('sentiment_social', 'astro_timing'): {
    'data_type': 'grok_agentic',
    'params_template': {'query_type': 'astro_timing'},
    'cache_ttl': 21600  # 6 hours - planetary positions change slowly
},
```

**Phase 3: Database Seed** (~10 min)
```sql
INSERT INTO data_points (
    source_id,
    name,
    display_name,
    description,
    config_values,
    requires_premium,
    enabled,
    sort_order
) VALUES (
    (SELECT source_id FROM data_sources WHERE name = 'sentiment_social'),
    'astro_timing',
    'Astro Timing Signals',
    'Cosmic timing signals based on moon phases, planetary aspects, and astrological transits. Treats astrology as sentiment/timing overlay.',
    ARRAY['astro_timing']::TEXT[],
    FALSE,  -- Free tier
    TRUE,
    99  -- Sort last in category
);
```

**Phase 4: Test** (~15 min)
```bash
# Test Grok query directly
cd /home/sev/ggbot
source .venv/bin/activate
python -c "
import asyncio
from market_intelligence.adapters.agentic.grok_agentic import GrokAgenticAdapter

async def test():
    adapter = GrokAgenticAdapter()
    result = await adapter.fetch({'query_type': 'astro_timing'})
    print(result.data)

asyncio.run(test())
"
```

### Files to Modify
| File | Change |
|------|--------|
| `grok_agentic.py` | Add `astro_timing` prompt template |
| `catalog_mapping.py` | Add mapping entry |
| Database `data_points` | Insert new row |

### Verification
- [ ] Grok returns valid JSON with moon phase, aspects, signal
- [ ] Data point appears in frontend data source selector
- [ ] Can be selected in bot config
- [ ] Cache works (second query within 6hr returns cached)
- [ ] Cost is reasonable (~$0.02-0.03)

---

## 3. Nansen API Exploration

### Context
User has free Nansen credits + 1 month premium subscription to explore.

### Research Phase (~1-2 hours)
- [ ] Review Nansen API documentation
- [ ] Identify available endpoints (smart money, whale tracking, token flows)
- [ ] Check authentication method (API key? OAuth?)
- [ ] Estimate costs per query type
- [ ] Identify most valuable data points for trading bots

### Potential Data Points
| Data Point | Description | Value for Bots |
|------------|-------------|----------------|
| `smart_money_flows` | Track wallets of known successful traders | High - leading indicator |
| `whale_transactions` | Large wallet movements | High - market impact |
| `exchange_flows` | CEX deposit/withdrawal trends | Medium - sentiment |
| `token_holder_analysis` | Holder concentration, distribution | Medium - risk assessment |

### Implementation (If Viable)

**New Adapter**: `market_intelligence/adapters/onchain/nansen_adapter.py`
```python
class NansenAdapter(DataAdapter):
    name = "nansen_adapter"
    data_type = "nansen_onchain"

    def __init__(self):
        self.api_key = os.getenv('NANSEN_API_KEY')
        self.base_url = "https://api.nansen.ai/v1"  # TBD

    async def fetch(self, params: QueryParams) -> AdapterResponse:
        # Implementation based on API docs
        pass
```

**Catalog**: `market_intelligence/catalog/data_types/onchain/nansen.yaml`

### Decision Point
After research, decide:
- Worth integrating? (cost vs value)
- Which endpoints to prioritize?
- Free tier sufficient or need paid?

---

## Implementation Order

1. **ggShot Disable** (first - quick win, removes confusion)
2. **Astrology Indicator** (second - adds value, simple implementation)
3. **Nansen Research** (third - exploration, may or may not implement)

---

## Success Metrics

| Metric | Target |
|--------|--------|
| ggShot hidden from UI | 100% - not selectable |
| Astro timing available | Shows in sentiment_social category |
| Astro cache hit rate | >90% (6hr TTL) |
| Nansen research complete | API docs reviewed, decision made |

---

## Rollback Plan

**ggShot**: Set `enabled=true` in database, re-add Signals tab
**Astrology**: Remove catalog mapping entry, set `enabled=false` in data_points
**Nansen**: No rollback needed (exploration only)

---

## Documentation Updates Required

After completion:
- [ ] Update `market_intelligence/README.md` (32 → 31 data points for ggShot removal, +1 for astro)
- [ ] Update `ACTIVE.md` if data point counts change
- [ ] Add CHANGELOG entry
