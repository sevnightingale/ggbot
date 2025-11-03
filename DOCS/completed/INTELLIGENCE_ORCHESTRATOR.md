# Intelligence Orchestrator - Design Specification

**Purpose**: Unified orchestration layer for scalable market intelligence integration (150+ data points)

**Status**: Planning Phase - Not Yet Implemented

**Date**: 2025-10-26

---

## Executive Summary

### The Problem We Discovered

While implementing funding rates (Phase 1 of Market Intelligence expansion), we identified a critical architectural issue: **the current integration pattern doesn't scale**.

**Current State:**
- Technical indicators (21): Hardcoded in `ggbot.py` via `ExtractionEngineV2`
- ggShot signals (1): Hardcoded query in `ggbot.py` (lines 794-830)
- Funding rates (2): Built adapter, but no integration yet

**The Issue:**
If we continue this pattern for 150 data points, `ggbot.py` becomes a 10,000-line monolith with:
- Manual adapter instantiation for each data type
- Manual permission checks repeated everywhere
- Manual result aggregation
- No code reuse
- Impossible to maintain

**We have the infrastructure** (Universal Data Layer with gateway, adapters, catalog, caching) **but we're not using it for orchestration.**

---

## What We Built Today (Context)

### 1. Funding Rate Adapter (Proof of Concept)

**Created:**
- `BinanceFundingAdapter` - Fetches funding rates with interpretation logic
- `funding_rate.yaml` - Catalog definition
- Database seeding - Added "Derivatives & Leverage" category with BTC/ETH funding rates
- Tested live - Successfully fetching real data (BTC: 0.0026%, ETH: 0.0063%)

**Output Format:**
```json
{
  "symbol": "BTC/USDT",
  "funding_rate": 0.000026,
  "funding_rate_pct": 0.002591,
  "interpretation": {
    "level": "neutral",
    "risk": "minimal",
    "interpretation": "Balanced positioning (0.003%)",
    "trading_implication": "Neutral funding - no leverage warning signals",
    "color": "green"
  },
  "next_funding_time": "2025-10-26T16:00:00+00:00"
}
```

**Status**: ✅ Adapter works, ❌ Not integrated into orchestrator yet

### 2. Database Reorganization (7 Categories)

**Finalized 7 Top-Level Categories:**

| # | Category | Status | Points | Access | Description |
|---|----------|--------|--------|--------|-------------|
| 1 | **Technical Analysis** | ✅ Live | 21 | 🆓 Free | Momentum, trend, volatility, volume indicators |
| 2 | **Trading Signals** | ✅ Live | 1 | 💎 Premium | ggShot AI-filtered signals |
| 3 | **On-Chain Analytics** | ⏳ Planned | 0 | 💎 Premium | Whale activity, exchange flows, TVL, dev metrics |
| 4 | **Derivatives & Leverage** | ✅ Live | 2 | 🆓 Free | Funding rates, liquidations, OI, microstructure |
| 5 | **Sentiment & Social** | ⏳ Planned | 0 | 💎 Premium | Twitter/X, Reddit, narratives, influencers |
| 6 | **News & Regulatory** | ⏳ Planned | 0 | 💎 Premium | Headlines, regulatory events, catalysts |
| 7 | **Macro Economics** | ⏳ Planned | 0 | 💎 Premium | VIX, DXY, inflation, Fed policy, yields |

**Database Changes:**
- Updated `data_sources` table with renamed categories
- Consolidated from 8 → 7 sources
- Updated `schema.md` and `ACTIVE.md` documentation

---

## The Solution: Intelligence Orchestrator

### Design Philosophy

**Separation of Concerns:**
1. **Technical Indicators** - Keep existing `ExtractionEngineV2` + Preprocessors (don't break what works)
2. **Everything Else** - Route through new `IntelligenceOrchestrator` (scalable architecture)

**Hybrid Approach Rationale:**
- ✅ Zero risk to existing 59 active bots using technical indicators
- ✅ Clean migration path for new data sources
- ✅ Scales to 150+ data points without touching `ggbot.py`
- ✅ Can migrate technical indicators later if desired

---

## Architecture Overview

### Current Flow (Before Orchestrator)

```
┌─────────────────────────────────────────────────────────────┐
│                        ggbot.py                             │
│  ┌────────────────────────────────────────────────────┐     │
│  │  _run_extraction_v2()                              │     │
│  │                                                     │     │
│  │  # Hardcoded technical indicators                  │     │
│  │  extraction_engine.extract(indicators=[...])       │     │
│  │                                                     │     │
│  │  # Hardcoded ggShot query                          │     │
│  │  if 'ggshot' in paid_data_points:                  │     │
│  │      ggshot_adapter = GGShotAdapter()              │     │
│  │      response = await ggshot_adapter.fetch(...)    │     │
│  │                                                     │     │
│  │  # Hardcoded funding rates (NOT YET ADDED)         │     │
│  │  if enabled:                                        │     │
│  │      funding_adapter = BinanceFundingAdapter()     │     │
│  │      response = await funding_adapter.fetch(...)   │     │
│  │                                                     │     │
│  │  # Repeat for 150 data points... 💀               │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

**Problems:**
- Manual permission checks everywhere
- Manual adapter instantiation
- Manual result aggregation
- Doesn't use Universal Data Layer infrastructure
- `ggbot.py` grows linearly with data points

---

### Proposed Flow (With Orchestrator)

```
┌─────────────────────────────────────────────────────────────────────┐
│                            ggbot.py                                 │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  _run_extraction_v2()                                      │     │
│  │                                                            │     │
│  │  # OLD WAY - Keep for technical indicators                │     │
│  │  tech_results = await extraction_engine.extract(...)      │     │
│  │                                                            │     │
│  │  # NEW WAY - One call for everything else                 │     │
│  │  orchestrator = IntelligenceOrchestrator()                │     │
│  │  market_intel = await orchestrator.fetch_all_enabled(     │     │
│  │      config=config,                                       │     │
│  │      user_id=user_id,                                     │     │
│  │      symbol=symbol                                        │     │
│  │  )                                                         │     │
│  │                                                            │     │
│  │  return {                                                  │     │
│  │      "timeframes": tech_results,      # Technicals        │     │
│  │      "market_intelligence": market_intel  # Everything else │  │
│  │  }                                                         │     │
│  └────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
         ┌──────────────────────────────────────────────────────┐
         │       IntelligenceOrchestrator                       │
         │  ┌────────────────────────────────────────────────┐  │
         │  │ fetch_all_enabled()                            │  │
         │  │                                                 │  │
         │  │ 1. Read config.selected_data_sources           │  │
         │  │ 2. Map data_points → catalog data_types        │  │
         │  │ 3. Check user permissions                      │  │
         │  │ 4. Query MarketIntelligence gateway            │  │
         │  │ 5. Aggregate results by category               │  │
         │  └────────────────────────────────────────────────┘  │
         └──────────────────────────────────────────────────────┘
                                    │
                                    ▼
         ┌──────────────────────────────────────────────────────┐
         │       MarketIntelligence Gateway                     │
         │  ┌────────────────────────────────────────────────┐  │
         │  │ query(data_type, params)                       │  │
         │  │                                                 │  │
         │  │ 1. Lookup catalog entry                        │  │
         │  │ 2. Check cache (Redis)                         │  │
         │  │ 3. Route to adapter (if cache miss)            │  │
         │  │ 4. Format response                             │  │
         │  │ 5. Store in cache                              │  │
         │  └────────────────────────────────────────────────┘  │
         └──────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │  GGShot      │  │  Binance     │  │  FRED API    │
         │  Adapter     │  │  Funding     │  │  Adapter     │
         │              │  │  Adapter     │  │  (future)    │
         └──────────────┘  └──────────────┘  └──────────────┘
```

**Benefits:**
- ✅ Config-driven (no hardcoding)
- ✅ Automatic permission checks
- ✅ Automatic caching
- ✅ Unified result structure
- ✅ `ggbot.py` stays minimal
- ✅ Scales to 150+ data points

---

## Detailed Design

### 1. IntelligenceOrchestrator Class

**File**: `market_intelligence/orchestrator.py`

**Responsibilities:**
1. Parse user config to determine enabled data sources
2. Map database `data_points` to catalog `data_types`
3. Check user permissions for premium data
4. Query `MarketIntelligence` gateway for each enabled source
5. Aggregate results by category
6. Return unified structure to orchestrator

**Key Methods:**

```python
class IntelligenceOrchestrator:
    """
    Orchestrates queries across all enabled market intelligence sources
    based on user configuration.

    This layer sits between ggbot.py and the Universal Data Layer,
    providing config-driven data fetching without hardcoding.
    """

    def __init__(self):
        self.gateway = MarketIntelligence()
        self.user_service = UserService()
        self._log = logger.bind(component="intelligence_orchestrator")

    async def fetch_all_enabled(
        self,
        config: BotConfigV2,
        user_id: str,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Fetch all market intelligence enabled in user config.

        Args:
            config: Bot configuration with selected_data_sources
            user_id: User ID for permission checks
            symbol: Trading pair (e.g., 'BTC/USDT')

        Returns:
            Dict organized by category:
            {
                'trading_signals': {'ggshot': {...}},
                'derivatives_leverage': {'btc_funding_rate': {...}},
                'macro_economics': {'vix': {...}, 'dxy': {...}},
                ...
            }
        """

    async def _get_enabled_sources(
        self,
        config: BotConfigV2,
        user_id: str
    ) -> Dict[str, List[str]]:
        """
        Parse config to get enabled data sources with permission filtering.

        Returns:
            {
                'derivatives_leverage': ['btc_funding_rate', 'eth_funding_rate'],
                'trading_signals': ['ggshot'],
                'macro_economics': ['vix', 'dxy']
            }
        """

    async def _map_data_point_to_catalog(
        self,
        source_name: str,
        point_name: str
    ) -> Optional[str]:
        """
        Map database data_point to catalog data_type.

        Examples:
            ('derivatives_leverage', 'btc_funding_rate') → 'funding_rate'
            ('trading_signals', 'ggshot') → 'ggshot_signals'
            ('macro_economics', 'vix') → 'vix_index'

        This mapping is necessary because:
        - Database uses user-facing names (btc_funding_rate)
        - Catalog uses adapter names (funding_rate)
        """

    async def _fetch_data_point(
        self,
        data_type: str,
        symbol: str,
        params: Dict[str, Any]
    ) -> Optional[AdapterResponse]:
        """
        Query gateway for a single data point.

        Handles:
        - Gateway query with proper params
        - Error handling (log warning, return None)
        - Response unwrapping
        """
```

---

### 2. Config Structure Parsing

**User Config Format** (`config_data.extraction.selected_data_sources`):

```json
{
  "extraction": {
    "selected_data_sources": {
      "technical_analysis": {
        "data_points": ["rsi", "macd", "bollinger_bands"]
      },
      "derivatives_leverage": {
        "data_points": ["btc_funding_rate", "eth_funding_rate"]
      },
      "trading_signals": {
        "data_points": ["ggshot"]
      },
      "macro_economics": {
        "data_points": ["vix", "dxy"]
      }
    }
  }
}
```

**Orchestrator Output Format**:

```python
{
    "trading_signals": {
        "ggshot": {
            "signals": {
                "5m": {"direction": "LONG", "confidence": 0.85, ...},
                "1h": {"direction": "LONG", "confidence": 0.92, ...}
            },
            "metadata": {...},
            "confidence": 0.95
        }
    },
    "derivatives_leverage": {
        "btc_funding_rate": {
            "funding_rate_pct": 0.0026,
            "interpretation": {
                "level": "neutral",
                "risk": "minimal",
                "trading_implication": "Neutral funding..."
            },
            "next_funding_time": "2025-10-26T16:00:00+00:00"
        },
        "eth_funding_rate": {
            "funding_rate_pct": 0.0063,
            "interpretation": {...}
        }
    },
    "macro_economics": {
        "vix": {
            "value": 15.2,
            "interpretation": "Low volatility, risk-on environment",
            "signal": "bullish"
        },
        "dxy": {
            "value": 106.3,
            "interpretation": "Dollar strength headwind for crypto",
            "signal": "bearish"
        }
    }
}
```

---

### 3. Data Point → Catalog Mapping

**Challenge**: Database uses user-facing names, catalog uses adapter-specific names.

**Mapping Table** (can be stored in YAML or hardcoded):

```python
CATALOG_MAPPING = {
    # Derivatives & Leverage
    ('derivatives_leverage', 'btc_funding_rate'): {
        'data_type': 'funding_rate',
        'params': {'symbol': 'BTC/USDT'}
    },
    ('derivatives_leverage', 'eth_funding_rate'): {
        'data_type': 'funding_rate',
        'params': {'symbol': 'ETH/USDT'}
    },

    # Trading Signals
    ('trading_signals', 'ggshot'): {
        'data_type': 'ggshot_signals',
        'params': {'symbol': '{symbol}'}  # Template - replace with actual
    },

    # Macro Economics (future)
    ('macro_economics', 'vix'): {
        'data_type': 'vix_index',
        'params': {}
    },
    ('macro_economics', 'dxy'): {
        'data_type': 'dxy_index',
        'params': {}
    },

    # On-Chain Analytics (future)
    ('onchain_analytics', 'btc_tvl'): {
        'data_type': 'defi_tvl',
        'params': {'chain': 'bitcoin'}
    }
}
```

**Alternative**: Store mapping in database or YAML config file.

---

### 4. Permission Checking

**Current State:**
- `user_profiles.paid_data_points` array stores granted permissions
- Each data point can have `requires_premium` flag in database

**Orchestrator Permission Flow:**

```python
async def _check_permission(self, user_id: str, source_name: str, point_name: str) -> bool:
    """
    Check if user has permission to access a data point.

    Logic:
    1. Query data_points table for requires_premium flag
    2. If free → return True
    3. If premium → check user_profiles.paid_data_points
    4. Return True if user has access, False otherwise
    """

    # Get data point from database
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT dp.requires_premium
                FROM data_points dp
                JOIN data_sources ds ON dp.source_id = ds.source_id
                WHERE ds.name = %s AND dp.name = %s
            """, (source_name, point_name))

            result = cur.fetchone()
            if not result:
                return False

            requires_premium = result[0]

            # If free, allow
            if not requires_premium:
                return True

            # If premium, check user access
            profile = await self.user_service.get_profile(user_id)
            if not profile or not profile.paid_data_points:
                return False

            # Check if user has specific data point access
            # For now, 'ggshot' grants access to ggshot signals
            # In future, could be more granular
            return point_name in profile.paid_data_points
```

---

### 5. Integration with ggbot.py

**Minimal Changes to Orchestrator** (`ggbot.py`):

```python
async def _run_extraction_v2(
    self,
    extraction_engine: ExtractionEngineV2,
    config: BotConfigV2,
    user_id: str,
    indicators: List[str],
    timeframes: List[str] = ["1h"],
    override_symbol: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run V2 extraction with hybrid approach:
    - Technical indicators: OLD way (ExtractionEngineV2)
    - Everything else: NEW way (IntelligenceOrchestrator)
    """

    symbol = override_symbol or config.selected_pair or "BTC/USDT"

    # ============================================================
    # OLD WAY - Technical Indicators (21 data points)
    # Keep as-is - don't break existing bots
    # ============================================================
    self._log.info(f"Extracting {len(indicators)} indicators for {symbol} across {len(timeframes)} timeframes")

    tasks = [
        extraction_engine.extract_for_symbol(
            symbol=symbol,
            indicators=indicators,
            timeframe=timeframe,
            limit=200,
            connector="kucoin",
            config_id=config.config_id
        )
        for timeframe in timeframes
    ]

    results = await asyncio.gather(*tasks)

    # Map results to timeframes
    timeframe_results = {}
    successful_extractions = 0

    for timeframe, result in zip(timeframes, results):
        timeframe_results[timeframe] = result
        if result.get("status") == "success":
            successful_extractions += 1

    # ============================================================
    # NEW WAY - Market Intelligence (all other data points)
    # Scalable to 150+ data points without changing this code
    # ============================================================
    market_intel = {}
    try:
        from market_intelligence.orchestrator import IntelligenceOrchestrator

        orchestrator = IntelligenceOrchestrator()
        market_intel = await orchestrator.fetch_all_enabled(
            config=config,
            user_id=user_id,
            symbol=symbol
        )

        # Count what we fetched
        total_points = sum(len(category) for category in market_intel.values())
        categories = list(market_intel.keys())

        if total_points > 0:
            self._log.info(f"✅ Market intelligence: {total_points} data points from {len(categories)} categories ({', '.join(categories)})")
        else:
            self._log.debug("No additional market intelligence enabled for this config")

    except Exception as e:
        self._log.warning(f"Failed to fetch market intelligence (non-critical): {e}")
        market_intel = {}

    # ============================================================
    # Combine Results
    # ============================================================
    return {
        "status": "success" if successful_extractions > 0 else "error",
        "symbol": symbol,
        "timeframes": timeframe_results,  # Technical indicators (old way)
        "market_intelligence": market_intel,  # Everything else (new way)
        "summary": {
            "total_timeframes": len(timeframes),
            "successful_extractions": successful_extractions,
            "failed_extractions": len(timeframes) - successful_extractions,
            "indicators": indicators,
            "market_intel_categories": list(market_intel.keys()),
            "market_intel_points": sum(len(cat) for cat in market_intel.values())
        }
    }
```

**Lines Changed**: ~40 lines added, ~30 lines removed (ggShot hardcoding)
**Net Impact**: Minimal code change, massive scalability gain

---

### 6. Decision Engine Integration

**Current Decision Engine Input:**

```python
decision_result = await self._run_decision_v2(
    config,
    extraction_result  # Contains: timeframes, ggshot_signals (hardcoded)
)
```

**New Decision Engine Input:**

```python
decision_result = await self._run_decision_v2(
    config,
    extraction_result  # Now contains: timeframes, market_intelligence
)
```

**Decision Engine Updates** (`decision/engine_v2.py`):

```python
async def make_decision(
    self,
    config: BotConfigV2,
    extraction_result: Dict[str, Any],
    ...
) -> Dict[str, Any]:
    """Make trading decision with technical + market intelligence."""

    # Extract technical indicators (old way)
    timeframe_data = extraction_result.get("timeframes", {})

    # Extract market intelligence (new way)
    market_intel = extraction_result.get("market_intelligence", {})

    # Build prompt sections
    technical_section = self._format_technical_indicators(timeframe_data)

    # Format market intelligence dynamically
    intel_sections = []

    if "trading_signals" in market_intel:
        signals_section = self._format_trading_signals(market_intel["trading_signals"])
        intel_sections.append(signals_section)

    if "derivatives_leverage" in market_intel:
        derivatives_section = self._format_derivatives_data(market_intel["derivatives_leverage"])
        intel_sections.append(derivatives_section)

    if "macro_economics" in market_intel:
        macro_section = self._format_macro_data(market_intel["macro_economics"])
        intel_sections.append(macro_section)

    # Combine into prompt
    prompt = f"""
    {technical_section}

    {chr(10).join(intel_sections)}

    Based on the above analysis, make a trading decision...
    """
```

**New Formatting Methods Needed:**

```python
def _format_derivatives_data(self, derivatives: Dict[str, Any]) -> str:
    """
    Format derivatives & leverage data for LLM prompt.

    Input:
        {
            'btc_funding_rate': {...},
            'eth_funding_rate': {...}
        }

    Output:
        ## Derivatives & Leverage

        BTC Funding Rate: 0.0026% (Neutral)
        - Risk Level: Minimal
        - Interpretation: Balanced positioning
        - Trading Implication: Neutral funding - no leverage warning signals

        ETH Funding Rate: 0.0063% (Neutral)
        ...
    """

def _format_macro_data(self, macro: Dict[str, Any]) -> str:
    """Format macro economic data for LLM prompt."""

def _format_onchain_data(self, onchain: Dict[str, Any]) -> str:
    """Format on-chain analytics for LLM prompt."""
```

---

## Implementation Plan

### Phase 1: Build Orchestrator (Week 1)

**Tasks:**
1. ✅ Create `market_intelligence/orchestrator.py`
2. ✅ Implement `fetch_all_enabled()` method
3. ✅ Implement config parsing logic
4. ✅ Implement permission checking
5. ✅ Create catalog mapping table
6. ✅ Write unit tests for orchestrator

**Deliverables:**
- Working orchestrator that can query multiple data sources based on config
- Test coverage for permission checks, config parsing, error handling

---

### Phase 2: Migrate ggShot (Week 1-2)

**Tasks:**
1. ✅ Update orchestrator to handle ggShot signals
2. ✅ Remove hardcoded ggShot query from `ggbot.py` (lines 794-830)
3. ✅ Update decision engine to consume from `market_intelligence.trading_signals`
4. ✅ Test with existing ggShot users

**Deliverables:**
- ggShot signals flowing through orchestrator instead of hardcoded path
- Zero regression for existing users

---

### Phase 3: Integrate Funding Rates (Week 2)

**Tasks:**
1. ✅ Add funding rate mapping to orchestrator
2. ✅ Update decision engine formatting for derivatives data
3. ✅ Add funding rate context to decision prompts
4. ✅ Test end-to-end: Enable funding rates → See in decision reasoning

**Deliverables:**
- Funding rates available to users via UI toggle
- AI decision engine receives funding rate context
- Prompt templates updated with derivatives section

---

### Phase 4: Expand Data Sources (Weeks 3-6)

**Add Phase 1 Remaining Data Points:**
1. ✅ VIX Index (macro)
2. ✅ DXY Dollar Index (macro)
3. ✅ CPI Inflation (macro)
4. ✅ NFP Jobs Report (macro)
5. ✅ BTC DeFi TVL (on-chain)

**For each data point:**
1. Create adapter (or use Grok Search adapter)
2. Create catalog YAML
3. Add to database (data_points table)
4. Add mapping to orchestrator
5. Update decision engine formatting
6. Test

**Deliverables:**
- 7 total new data points (2 funding + 5 macro/on-chain)
- Decision engine receiving macro and on-chain context
- ~30-40% trading edge improvement (per roadmap estimates)

---

## Testing Strategy

### Unit Tests

**`test_orchestrator.py`:**
```python
async def test_fetch_all_enabled():
    """Test orchestrator fetches all enabled sources from config."""

async def test_permission_filtering():
    """Test premium data points filtered based on user permissions."""

async def test_catalog_mapping():
    """Test data_point names map correctly to catalog data_types."""

async def test_error_handling():
    """Test orchestrator handles adapter failures gracefully."""
```

### Integration Tests

**`test_orchestrator_integration.py`:**
```python
async def test_ggshot_via_orchestrator():
    """Test ggShot signals fetched through orchestrator match old method."""

async def test_funding_rates_end_to_end():
    """Test funding rates flow from adapter → orchestrator → decision engine."""

async def test_multiple_categories():
    """Test orchestrator handles multiple categories simultaneously."""
```

### End-to-End Tests

**`test_full_extraction_with_orchestrator.py`:**
```python
async def test_extraction_with_market_intel():
    """Test full extraction pipeline with technical + market intelligence."""
    # 1. Create test config with enabled data sources
    # 2. Run extraction
    # 3. Verify technical indicators present
    # 4. Verify market intelligence present
    # 5. Verify decision engine receives both
```

---

## Migration Checklist

### Before Starting Implementation

- [x] ✅ Funding rate adapter built and tested
- [x] ✅ Database categories finalized (7 categories)
- [x] ✅ Documentation updated (schema.md, ACTIVE.md)
- [ ] Review this design doc with team
- [ ] Get approval on hybrid approach (keep technical indicators as-is)
- [ ] Decide on catalog mapping storage (hardcoded vs YAML vs database)

### During Implementation

- [ ] Create feature branch: `feature/intelligence-orchestrator`
- [ ] Build orchestrator with comprehensive tests
- [ ] Migrate ggShot first (lower risk, existing users)
- [ ] Add funding rates second (new feature, no existing dependencies)
- [ ] Update decision engine formatting methods
- [ ] Test with real user configs
- [ ] Monitor performance (caching effectiveness, latency)

### After Implementation

- [ ] Deploy to staging
- [ ] Test with subset of users
- [ ] Monitor error rates, cache hit rates
- [ ] Document new config format for users
- [ ] Update frontend UI to reflect new capabilities
- [ ] Rollout to production

---

## Success Metrics

### Technical Metrics

- **Code Reduction**: `ggbot.py` extraction method < 100 lines (currently ~200)
- **Scalability**: Add new data point in < 30 minutes (create adapter + mapping)
- **Performance**: Orchestrator overhead < 50ms (compared to hardcoded approach)
- **Cache Hit Rate**: > 80% for market intelligence queries (1-hour TTL)
- **Error Rate**: < 1% adapter failures (graceful degradation)

### Business Metrics

- **Data Point Growth**: 24 → 30+ data points in 4 weeks (Phase 1 complete)
- **User Adoption**: > 20% of active bots enable new data sources
- **Trading Edge**: Win rate improvement for bots using market intelligence
- **Developer Velocity**: 50% faster new data source integration

---

## Future Enhancements

### v2.0 - Advanced Features (Post-Launch)

1. **Dynamic Prompt Templates**
   - Store formatting templates in catalog YAML
   - Auto-generate decision engine prompt sections from catalog
   - No code changes needed to add new data source

2. **Data Point Dependencies**
   - Define dependencies in catalog (e.g., "VIX requires DXY for context")
   - Orchestrator auto-fetches dependencies
   - Reduce config complexity for users

3. **Conditional Fetching**
   - Only fetch data when decision is pending (not on "wait" decisions)
   - Symbol-specific data filtering (don't fetch VIX for SOL trading)
   - Timeframe-aware fetching (daily data not needed for 5m bots)

4. **Performance Optimizations**
   - Parallel fetching with `asyncio.gather()`
   - Batch queries for similar data types
   - Smarter caching strategies (TTL per data type)

5. **Migrate Technical Indicators**
   - Build preprocessor adapters
   - Route through orchestrator
   - Fully unified data pipeline

---

## Open Questions

### Design Decisions

1. **Catalog Mapping Storage**: Hardcode vs YAML vs Database?
   - **Hardcoded**: Fast, no I/O, version controlled
   - **YAML**: Flexible, no code changes
   - **Database**: Most flexible, requires migration
   - **Recommendation**: Start hardcoded, migrate to YAML later

2. **Error Handling Philosophy**: Fail-fast vs graceful degradation?
   - **Current Approach**: Log warning, return empty dict (graceful)
   - **Alternative**: Raise exception if critical data missing (fail-fast)
   - **Recommendation**: Graceful degradation (market intel is supplemental)

3. **Permission Granularity**: Per-data-point vs per-category?
   - **Current**: Per-data-point (`paid_data_points = ['ggshot']`)
   - **Alternative**: Per-category (`paid_categories = ['trading_signals']`)
   - **Recommendation**: Keep per-data-point for flexibility

4. **Caching Strategy**: Shared vs isolated?
   - **Current**: Shared cache across users (symbol-based keys)
   - **Alternative**: Isolated cache per user (user_id in key)
   - **Recommendation**: Shared for efficiency, isolated for user-specific data

### Technical Debt

1. **ggShot Signal Storage**: Why is ggShot stored in `market_data` table but other sources aren't?
   - Should funding rates be stored too?
   - Should we standardize storage vs live queries?
   - **Recommendation**: Document pattern, revisit during Phase 2

2. **Technical Indicators vs Everything Else**: Long-term should they unify?
   - Pros: Single pipeline, simpler architecture
   - Cons: Risk to existing bots, significant refactor
   - **Recommendation**: Keep separate for now, revisit in 6 months

---

## Appendix

### A. Current Data Sources & Adapters

**Implemented:**
- `technical_analysis`: 21 preprocessors (RSI, MACD, Bollinger, etc.) - OLD WAY
- `trading_signals`: GGShotAdapter - NEEDS MIGRATION
- `derivatives_leverage`: BinanceFundingAdapter - NEEDS INTEGRATION

**Planned (Phase 1):**
- `macro_economics`: VixAdapter, DxyAdapter, CpiAdapter, NfpAdapter
- `onchain_analytics`: DefiLlamaAdapter (TVL)

**Planned (Phase 2+):**
- `sentiment_social`: TwitterAdapter, RedditAdapter
- `news_regulatory`: CryptoPanicAdapter

### B. Catalog Data Type Examples

**funding_rate.yaml:**
```yaml
name: funding_rate
category: derivatives
description: Perpetual futures funding rates

query_params:
  symbol:
    type: string
    required: true

sources:
  - adapter: binance_funding
    priority: 1
    cost: free

cache:
  backend: redis
  ttl: 3600  # 1 hour
```

**ggshot_signals.yaml:**
```yaml
name: ggshot_signals
category: signals
description: ggShot AI-filtered trading signals

query_params:
  symbol:
    type: string
    required: true

sources:
  - adapter: ggshot_adapter
    priority: 1
    cost: free

cache:
  backend: redis
  ttl: 300  # 5 minutes
```

### C. User Config Examples

**Minimal Config (Only Technical Indicators):**
```json
{
  "extraction": {
    "selected_data_sources": {
      "technical_analysis": {
        "data_points": ["rsi", "macd"]
      }
    }
  }
}
```

**Advanced Config (Multiple Categories):**
```json
{
  "extraction": {
    "selected_data_sources": {
      "technical_analysis": {
        "data_points": ["rsi", "macd", "bollinger_bands", "adx"]
      },
      "derivatives_leverage": {
        "data_points": ["btc_funding_rate", "eth_funding_rate"]
      },
      "trading_signals": {
        "data_points": ["ggshot"]
      },
      "macro_economics": {
        "data_points": ["vix", "dxy"]
      }
    }
  }
}
```

---

## Conclusion

The Intelligence Orchestrator solves a critical architectural problem: **scalable integration of 150+ market intelligence data points** without turning `ggbot.py` into an unmaintainable monolith.

**Key Benefits:**
1. ✅ **Scalability**: Add new data points in < 30 minutes
2. ✅ **Maintainability**: `ggbot.py` stays clean (one method call)
3. ✅ **Safety**: Zero risk to existing technical indicators
4. ✅ **Architecture**: Uses Universal Data Layer properly
5. ✅ **Performance**: Automatic caching for all data sources

**Implementation Effort**: ~2-3 weeks for full Phase 1 (orchestrator + ggShot migration + funding rates + 5 macro/on-chain data points)

**Ready to proceed when approved.**

---

**Document Version**: 1.0
**Author**: Claude Code
**Last Updated**: 2025-10-26
**Status**: Planning Phase - Awaiting Approval
