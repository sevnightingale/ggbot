# Market Data System - Complete Architecture

**Status**: ✅ Production Deployed
**Version**: Phase 1 Complete (33 data points live, cost-optimized)
**Last Updated**: 2026-01-13

The **Market Data System** is ggbots' unified pipeline for acquiring, processing, and serving market intelligence to AI trading agents. It orchestrates **33 data points** across **6 categories**, from technical indicators to real-time sentiment, using a scalable catalog-driven architecture.

---

## 📚 Table of Contents

1. [Overview & Evolution](#-overview--evolution)
2. [Architecture](#-architecture)
3. [Core Components](#-core-components)
4. [Data Sources (32 Total)](#-data-sources-32-total)
5. [Data Flow Examples](#-data-flow-examples)
6. [Adding New Data Sources](#-adding-new-data-sources)
7. [Performance & Economics](#-performance--economics)
8. [Operations & Debugging](#-operations--debugging)
9. [Implementation References](#-implementation-references)

---

## 🎯 Overview & Evolution

### **The Problem**
AI trading decisions need **contextual market intelligence** beyond price and volume:
- Macro factors (VIX volatility, dollar strength, inflation)
- On-chain signals (whale movements, DeFi activity)
- Social sentiment (Twitter/X analysis)
- Breaking news (regulatory events, adoption announcements)
- Technical analysis (21 sophisticated indicators)
- Derivatives data (funding rates, open interest)

### **The Evolution**

**V1 (MCP-Based)** → Technical indicators only, Node.js + Python complexity, 0.753s extraction time

**V2 (Pure Python)** → 12x performance improvement (0.064s), 21 preprocessors, dual storage

**Universal Data Layer** → Catalog-driven gateway, Redis caching, adapter pattern for any data source

**Intelligence Orchestrator** → Config-driven routing, parallel execution, permission system, agent support

### **Current Capabilities**
- ✅ **33 data points** across 6 categories (all FREE tier)
- ✅ **5 adapter types** handling diverse data sources (hybrid Grok + Perplexity)
- ✅ **Parallel query execution** (~30s for all 8 sources, 5.3x speedup)
- ✅ **Custom cache TTL** per data point (10min to 24hrs)
- ✅ **Agent dynamic queries** (query without modifying config)
- ✅ **$0.76/user/month** at 257 users, scales to $0.20/user at 1000 users

---

## 🏗️ Architecture

### **System Diagram**

```
┌────────────────────────────────────────────────────────────┐
│                    User Configuration                      │
│  config.extraction.selected_data_sources = {              │
│    "macro_economics": ["vix", "dxy"],                     │
│    "sentiment_social": ["twitter_sentiment"]             │
│  }                                                         │
└────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────┐
│            Intelligence Orchestrator (NEW!)                │
│  orchestrator.py - Config-driven routing layer             │
│  ────────────────────────────────────────────────────      │
│  1. Parse config → extract enabled data points             │
│  2. Check user permissions (FREE vs PREMIUM)               │
│  3. Map data_point names → catalog data_types              │
│  4. Query gateway IN PARALLEL (asyncio.gather)             │
│  5. Aggregate results by category                          │
│  ────────────────────────────────────────────────────      │
│  Output: {                                                 │
│    "macro_economics": {"vix": {...}, "dxy": {...}},      │
│    "sentiment_social": {"twitter_sentiment": {...}}      │
│  }                                                         │
└────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────┐
│         Universal Data Layer (Gateway + Catalog)           │
│  gateway.py - Core query interface                         │
│  ────────────────────────────────────────────────────      │
│  1. Load catalog entry for data_type                       │
│  2. Validate query params                                  │
│  3. Check Redis cache (key: "intel:{name}:{params}")      │
│  4. On miss → route to adapter                             │
│  5. Cache result with custom TTL                           │
│  6. Format response                                        │
│  ────────────────────────────────────────────────────      │
│  Catalog: YAML definitions in catalog/data_types/          │
│  - Query parameters schema                                 │
│  - Adapter routing (priority, cost, rate limits)           │
│  - Cache config (TTL, key pattern)                         │
│  - Response schema                                         │
└────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┴──────────────────────┐
        ↓                                             ↓
┌──────────────────┐                         ┌────────────────┐
│   Redis Cache    │                         │   Adapters     │
│                  │                         │   (4 types)    │
│  TTL: Variable   │                         │                │
│  - VIX: 15min    │                         │ 1. ExtractionV2│
│  - CPI: 24hrs    │                         │ 2. Grok Agentic│
│  - News: 10min   │                         │ 3. Binance API │
│  Cache hit →     │                         │ 4. ggShot DB   │
│  Return cached   │                         │                │
│                  │                         │ Cache miss →   │
│  Key format:     │                         │ Fetch from API │
│  "intel:name:    │                         │                │
│  {query_params}" │                         │                │
└──────────────────┘                         └────────────────┘
        ↓                                             ↓
┌──────────────────┐                         ┌────────────────┐
│  Cache Storage   │                         │  External APIs │
│  (Redis 6379)    │                         │                │
│  - Shared across │                         │ • XAI Grok API │
│    all users     │                         │ • Binance API  │
│  - Cost savings  │                         │ • Supabase DB  │
│    via reuse     │                         │ • Hummingbot   │
└──────────────────┘                         └────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────┐
│                    Database Storage                        │
│  market_data table (PostgreSQL/Supabase)                   │
│  ────────────────────────────────────────────────────      │
│  - Permanent record of what data was seen at decision time │
│  - Multi-timeframe support (7 rows per symbol/config)      │
│  - Queryable by config_id + symbol                         │
│  - Used for backtesting, audit trail, analysis             │
└────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────┐
│                    Decision Engine                         │
│  Receives aggregated market intelligence + technicals      │
│  Formats for LLM consumption (summary-first approach)      │
│  Generates trading decision with comprehensive reasoning   │
└────────────────────────────────────────────────────────────┘
```

### **Key Architectural Principles**

1. **Separation of Concerns**
   - **Orchestrator** = User-facing routing (config → queries)
   - **Gateway** = Infrastructure (catalog, caching, adapter routing)
   - **Adapters** = Data acquisition (each source has specialized logic)

2. **Shared Cache Economics**
   - VIX is same for all users → 1 API call serves 1000 users
   - Cost per user **decreases** as platform grows
   - Custom TTL per data type (fast-moving vs static data)

3. **Graceful Degradation**
   - Individual data point failures don't crash the system
   - Parallel execution with exception handling
   - Decision engine receives partial data if some sources fail

4. **Extensibility Without Breaking Changes**
   - Adding new data sources = new catalog YAML + mapping entry
   - No changes to orchestrator or gateway code
   - Frontend auto-populates from database (data_sources table)

---

## 🧩 Core Components

### **1. Intelligence Orchestrator** (`orchestrator.py`)

**Purpose**: Config-driven routing layer between user configs and the Universal Data Layer.

**Key Responsibilities**:
- Parse `config.extraction.selected_data_sources` to extract enabled data points
- Check user permissions (query database for `requires_premium` flags)
- Map data point names → catalog data types (via `catalog_mapping.py`)
- Execute queries **in parallel** using `asyncio.gather()` (5.3x speedup)
- Aggregate results by category for decision engine consumption

**Key Methods**:
```python
async def fetch_market_intelligence(
    config,                                    # BotConfigV2 with selected_data_sources
    user_id: str,
    symbol: str,
    data_points_override: Optional[Dict] = None  # For agent dynamic queries
) -> Dict[str, Dict[str, Any]]:
    # Returns: {"macro_economics": {"vix": {...}}, "sentiment_social": {...}}
```

**Agent Support**:
```python
# Agent can query dynamically without modifying config
market_intel = await fetch_market_intelligence(
    config, user_id, symbol,
    data_points_override={
        "macro_economics": ["vix", "dxy"],  # Not in config, just for this query
        "sentiment_social": ["twitter_sentiment"]
    }
)
```

**Performance**: Parallel execution via `asyncio.gather()` - 8 queries complete in ~30s (max of slowest query) vs 160s sequential.

---

### **2. Universal Data Layer - Gateway** (`gateway.py`)

**Purpose**: Core query interface providing catalog-driven data fetching with caching.

**Key Features**:
- **Catalog System**: YAML definitions in `catalog/data_types/` define:
  - Query parameters schema (validation rules)
  - Available adapters (priority, cost, rate limits)
  - Cache configuration (backend, TTL, key pattern)
  - Response schema expectations

- **Intelligent Caching**: Redis-backed with:
  - Custom TTL per data type (override via `cache_ttl_override`)
  - Key pattern: `intel:{data_type_name}:{query_params}`
  - Cache hit returns immediately (sub-millisecond)
  - Cache miss triggers adapter query + storage

- **Adapter Routing**:
  - Multiple adapters per data type (fallback support)
  - Priority-based selection
  - Cost tracking and rate limiting
  - Dynamic adapter loading via factory pattern

**Key Methods**:
```python
async def query(
    data_type: str,                      # e.g., "grok_agentic", "funding_rate"
    params: Dict[str, Any],              # e.g., {"query_type": "vix_index"}
    format: QueryFormat = QueryFormat.RAW,
    cache_ttl_override: Optional[int] = None  # Seconds, overrides catalog default
) -> MarketDataResponse
```

**Adapter Routing Logic**:
```python
# gateway.py:_adapter_name_to_module()
# Maps adapter class name → Python module path
# Examples:
#   GrokAgenticAdapter → market_intelligence.adapters.agentic.grok_agentic
#   BinanceFundingAdapter → market_intelligence.adapters.derivatives.binance_funding
```

---

### **3. Catalog Mapping** (`catalog_mapping.py`)

**Purpose**: Hardcoded dictionary mapping user-facing data_point names → catalog data_types.

**Why Hardcoded?**:
- Fast lookup (no database queries)
- Explicit control over routing
- Easy to audit and modify
- Type-safe in code

**Structure**:
```python
CATALOG_MAPPING: Dict[Tuple[str, str], Dict[str, Any]] = {
    # (source_name, point_name) → catalog config
    ('macro_economics', 'vix'): {
        'data_type': 'grok_agentic',              # Catalog data type
        'params_template': {'query_type': 'vix_index'},  # Query params
        'cache_ttl': 900  # 15 minutes (optional override)
    },
    ('derivatives_leverage', 'btc_funding_rate'): {
        'data_type': 'funding_rate',
        'params_template': {'symbol': 'BTC/USDT', 'include_mark_price': True},
        'cache_ttl': 3600  # 1 hour
    }
}
```

**Adding New Data Points**: Just add a new entry here + seed database.

---

### **4. Adapters** (4 Types)

Adapters are specialized modules that fetch data from specific sources.

#### **Type 1: ExtractionEngineV2** (`extraction/v2/`)
**Purpose**: Technical indicator calculations (21 sophisticated preprocessors)

**Capabilities**:
- 21 indicators: RSI, MACD, Stochastic, Williams %R, CCI, MFI, ADX, Parabolic SAR, Aroon, ATR, Bollinger Bands, OBV, SMA, EMA, ROC, VWAP, TRIX, Vortex, BB Width, Keltner, Donchian
- Multi-timeframe support (5m to 1w)
- Advanced preprocessing with pattern recognition, divergence detection, zone analysis
- 12x performance improvement over V1 (0.064s vs 0.753s)

**See**: `extraction/v2/README.md` for deep technical details

**Integration**: Called directly by orchestrator via `ExtractionEngineV2.extract_for_symbol()`

---

#### **Type 2: GrokAgenticAdapter** (`adapters/agentic/grok_agentic.py`)
**Purpose**: Twitter/on-chain intelligence via XAI's autonomous agentic API

**Revolutionary Approach**: Native X/Twitter access + code execution + web search:
- X (Twitter) search and NLP analysis (xAI owns Twitter)
- On-chain data aggregation with code execution
- Breaking news via web search

**4 Prompt Templates** (query_type parameter):
1. `twitter_sentiment` - X/Twitter sentiment analysis (symbol-specific)
2. `crypto_news` - Breaking crypto headlines (symbol-specific)
3. `btc_tvl` - Bitcoin Total Value Locked in DeFi
4. `whale_activity` - Large wallet movements (symbol-specific)

**Cost Per Query**: $0.0017 (BTC TVL) to $0.0637 (Twitter sentiment with NLP)

---

#### **Type 3: OpenRouterMarketAdapter** (`adapters/agentic/openrouter_adapter.py`)
**Purpose**: Macro economic indicators via OpenRouter + Perplexity Sonar Pro

**Approach**: Perplexity models with native web search for real-time macro data:
- Web search (CBOE, Bloomberg, BLS, Fed, etc.)
- JSON-structured responses
- 5-10× cheaper than Grok for macro queries

**4 Prompt Templates** (query_type parameter):
1. `vix_index` - VIX volatility index
2. `dxy_index` - US Dollar strength
3. `cpi_inflation` - Latest CPI inflation data
4. `nfp_jobs` - Nonfarm payrolls report

**Cost Per Query**: ~$0.01 per query (251-346 tokens)

**Features**:
- Streaming support with tool call observability
- Citation tracking (URLs from web/X search)
- Cost estimation (reasoning tokens + tool calls)
- Structured JSON responses with interpretation

**Example Response**:
```json
{
  "value": 15.98,
  "timestamp": "2025-10-28T08:16:25",
  "signal": "neutral",
  "interpretation": "Moderate volatility suggests stable environment, neutral for crypto",
  "risk_regime": "moderate"
}
```

---

#### **Type 4: BinanceFundingAdapter** (`adapters/derivatives/binance_funding.py`)
**Purpose**: Real-time perpetual funding rates from Binance

**Capabilities**:
- BTC/USDT and ETH/USDT funding rates
- Mark price and next funding timestamp
- FREE (direct Binance API, no cost)

**Use Case**: Detect overleveraged setups (extreme funding = correction risk)

---

#### **Type 5: GGShotAdapter** (`adapters/signals/ggshot_adapter.py`)
**Purpose**: Premium trading signals from ggShot Telegram channels

**Integration**:
- Signals stored in `market_data` table by listener service
- Adapter queries database for latest signal per timeframe
- **PREMIUM** (requires third-party subscription, manually added to `paid_data_points`)

**Data Source**: `trading_signals` (seeded in database)

---

### **5. Storage Layer**

#### **Redis Cache** (`cache/redis_cache.py`)
- **Backend**: Redis 6379
- **TTL**: Variable per data type (10min to 24hrs)
- **Key Pattern**: `intel:{data_type_name}:{query_params}`
- **Serialization**: Pickle (handles complex Python objects)
- **Shared**: All users benefit from cache hits (cost savings)

**Example Keys**:
```
intel:grok_agentic:{query_type:'vix_index'}  TTL=900s (15min)
intel:grok_agentic:{query_type:'cpi_inflation'}  TTL=86400s (24hrs)
intel:funding_rate:{symbol:'BTC/USDT'}  TTL=3600s (1hr)
```

#### **PostgreSQL/Supabase** (`market_data` table)
- **Purpose**: Permanent storage for audit trail, backtesting, analysis
- **Schema**:
  - `data_source`: UUID FK to `data_sources` table
  - `symbol`: Trading pair
  - `timeframe`: Candle timeframe (5m, 1h, etc.)
  - `config_id`: Links to bot configuration (for multi-timeframe queries)
  - `data_points`: JSONB with preprocessed indicator/intelligence data
  - `raw_data`: JSONB with OHLCV or raw source data
- **Multi-timeframe**: Each timeframe stored as separate row with same `config_id`

---

## 📊 Data Sources (32 Total)

### **Complete Data Source Matrix**

| Category | Data Point | Adapter | Cost/Query | Cache TTL | Tier |
|----------|-----------|---------|------------|-----------|------|
| **Technical Analysis** (21 indicators) |
| | RSI, MACD, Stochastic, Williams %R, CCI, MFI, ADX, PSAR, Aroon, ATR, BB, OBV, SMA, EMA, ROC, VWAP, TRIX, Vortex, BBWidth, Keltner, Donchian | ExtractionV2 | FREE | N/A (realtime calc) | 🆓 |
| **Trading Signals** (1 source) |
| | ggShot signals | GGShotAdapter (DB) | N/A | N/A | 💎 Premium |
| **Derivatives & Leverage** (2 rates) |
| | BTC Funding Rate | BinanceFunding | FREE | 1 hour | 🆓 |
| | ETH Funding Rate | BinanceFunding | FREE | 1 hour | 🆓 |
| **Macro Economics** (4 indicators) |
| | VIX Volatility Index | GrokAgentic | ~$0.025 | 4 hours | 🆓 |
| | DXY Dollar Index | GrokAgentic | ~$0.025 | 4 hours | 🆓 |
| | CPI Inflation | GrokAgentic | ~$0.025 | 24 hours | 🆓 |
| | NFP Jobs Report | GrokAgentic | ~$0.025 | 24 hours | 🆓 |
| **On-Chain Analytics** (2 sources) |
| | BTC TVL in DeFi | GrokAgentic | ~$0.025 | 6 hours | 🆓 |
| | Whale Activity | GrokAgentic | ~$0.025 | 2 hours | 🆓 |
| **Sentiment & Social** (3 sources) |
| | Twitter/X Sentiment | GrokAgentic | ~$0.05 | 4 hours | 🆓 |
| | Lunar Phase | GrokAgentic | ~$0.005 | 12 hours | 🆓 |
| | Mercury Retrograde Status | GrokAgentic | ~$0.001 | 24 hours | 🆓 |
| **News & Regulatory** (1 source) |
| | Crypto News Headlines | GrokAgentic | ~$0.025 | 2 hours | 🆓 |

**Total**: 33 data points (all FREE tier)

*Note: ggShot (Premium) disabled 2026-01-23 due to stale signals. Astrology data points (lunar_phase, mercury_status) added same date.*

---

## 🔄 Data Flow Examples

### **Example 1: User Enables VIX in Config**

```
1. User in Frontend:
   ✓ Check "VIX Volatility Index" in Macro Economics category
   → Click Save

2. Frontend → Backend:
   POST /api/v2/config/{config_id}
   {
     "extraction": {
       "selected_data_sources": {
         "macro_economics": {
           "data_points": ["vix"]
         }
       }
     }
   }
   → Config saved to database

3. Bot Execution (Scheduled or Manual Trigger):
   ggbot.py:_run_extraction_v2()
   ↓
   orchestrator.fetch_market_intelligence(config, user_id, symbol)
   ↓
   Reads config → finds ('macro_economics', 'vix')
   ↓
   catalog_mapping.py → {'data_type': 'grok_agentic', 'params_template': {'query_type': 'vix_index'}, 'cache_ttl': 900}
   ↓
   gateway.query(data_type='grok_agentic', params={'query_type': 'vix_index'}, cache_ttl_override=900)
   ↓
   Check Redis: key='intel:grok_agentic:{query_type:vix_index}'

   ── Cache HIT (within 15min) ──────────────────
   Return cached: {"value": 15.98, "signal": "neutral", ...}
   Latency: <1ms

   ── Cache MISS (>15min) ───────────────────────
   Route to GrokAgenticAdapter
   ↓
   Grok autonomously:
     1. Web search (CBOE, Bloomberg, Yahoo)
     2. Extract VIX value (15.98)
     3. Interpret for crypto impact
     4. Return structured JSON
   ↓
   Store in Redis (TTL=900s / 15min)
   Latency: ~18-20s
   Cost: ~$0.0036

4. Decision Engine Receives:
   {
     "market_intelligence": {
       "macro_economics": {
         "vix": {
           "value": 15.98,
           "signal": "neutral",
           "interpretation": "Moderate volatility...",
           "risk_regime": "moderate"
         }
       }
     }
   }
   ↓
   LLM considers VIX in trading decision:
   "VIX 15.88 moderate, neutral for crypto traders..."
```

---

### **Example 2: Agent Queries Twitter Sentiment Dynamically**

```
1. Agent Runtime:
   Agent wants to check current BTC sentiment on Twitter (not in config)
   ↓
   agent.query_market_data({
     "symbol": "BTCUSDT",
     "data_sources": {
       "sentiment_social": ["twitter_sentiment"]  # Not in config!
     }
   })

2. API Endpoint:
   POST /api/v2/agent/query-market-data
   {
     "config_id": "abc123",
     "symbol": "BTCUSDT",
     "data_sources": {"sentiment_social": ["twitter_sentiment"]}
   }
   ↓
   orchestrator.fetch_market_intelligence(
     config,
     user_id,
     symbol="BTC/USDT",
     data_points_override={"sentiment_social": ["twitter_sentiment"]}  # Override!
   )
   ↓
   Uses override instead of config → routes to gateway

3. Gateway Query:
   data_type='grok_agentic'
   params={'query_type': 'twitter_sentiment', 'symbol': 'BTC'}
   cache_ttl_override=1800 (30min)
   ↓
   Check Redis: key='intel:grok_agentic:{query_type:twitter_sentiment,symbol:BTC}'

   ── Cache MISS (sentiment changes fast) ───────
   GrokAgenticAdapter:
     1. X search for "BTC" posts (last 24hrs)
     2. NLP sentiment analysis
     3. Extract themes, influencer positioning
     4. Calculate sentiment score (-1 to +1)
   ↓
   Response:
   {
     "sentiment_score": 0.3,
     "sample_size": 62,
     "bullish_ratio": 0.4,
     "key_themes": ["Institutional Adoption", "ETF Approvals"],
     "signal": "bullish"
   }
   ↓
   Store in Redis (TTL=1800s / 30min)
   Cost: ~$0.0637

4. Agent Receives:
   {
     "market_intelligence": {
       "sentiment_social": {
         "twitter_sentiment": {...}
       }
     }
   }
   ↓
   Agent reasoning: "Twitter sentiment at 0.3 (bullish) suggests positive momentum..."
```

---

### **Example 3: Multi-Timeframe Technical Indicators**

```
1. User Config:
   {
     "extraction": {
       "selected_data_sources": {
         "technical_analysis": {
           "data_points": ["RSI", "MACD", "BB"],
           "timeframes": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
         }
       }
     }
   }

2. Bot Execution:
   ggbot.py:_run_extraction_v2()
   ↓
   FOR EACH timeframe in ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]:
     extraction_engine.extract_for_symbol(
       symbol="BTC/USDT",
       indicators=["RSI", "MACD", "BB"],
       timeframe=timeframe,      # Different each time
       config_id=config.config_id  # Same config_id for all
     )
     ↓
     ExtractionEngineV2:
       1. Fetch OHLCV from WebSocket cache (Redis)
       2. Calculate 3 indicators using pandas-ta
       3. Run 3 preprocessors (advanced analysis)
       4. Store in market_data table
     ↓
     7 separate rows in market_data:
       Row 1: config_id, symbol=BTC/USDT, timeframe=5m, data_points={RSI: {...}, MACD: {...}}
       Row 2: config_id, symbol=BTC/USDT, timeframe=15m, data_points={...}
       ...
       Row 7: config_id, symbol=BTC/USDT, timeframe=1w, data_points={...}

3. Decision Engine Query:
   SELECT * FROM market_data
   WHERE config_id = ? AND symbol = ?
   ↓
   Receives 7 rows (one per timeframe)
   ↓
   Consolidates into structured format:
   {
     "symbol": "BTC/USDT",
     "timeframes": {
       "5m": {"indicators": {RSI: {...}, MACD: {...}}, "latest_price": 114541.56},
       "15m": {...},
       "1h": {...},
       ...
     },
     "timeframes_available": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
   }
   ↓
   LLM sees: "On 5m RSI is 73 (overbought), but 1h RSI is 54 (neutral), suggesting short-term overextension within healthy uptrend..."
```

---

## 🛠️ Adding New Data Sources

### **Decision Tree: New Adapter vs Existing?**

```
Do you need to fetch data from a NEW external API/source?
├─ NO: Data can be calculated from existing OHLCV?
│   └─→ Add new preprocessor to ExtractionEngineV2
│       (See extraction/v2/README.md)
│
├─ YES: Is it macro/sentiment/on-chain intelligence?
│   └─→ Can Grok autonomously research it via web/X search?
│       ├─ YES: Add new prompt template to GrokAgenticAdapter
│       │   (30 minutes, no new adapter needed!)
│       └─ NO: Does it require specialized API/scraping?
│           └─→ Create new adapter (see below)
```

### **Option 1: Add Grok Query Type (Easiest)**

**When to Use**: Twitter/X sentiment, on-chain data, crypto news (requires native X access or code execution)

**Steps** (30 minutes):
1. Add prompt template to `grok_agentic.py:PROMPT_TEMPLATES`
2. Add mapping entry to `catalog_mapping.py`
3. Seed database with new data_point
4. Test with test script

**Example**: Adding "Fear & Greed Index" (to Perplexity for macro, or Grok for sentiment)

```python
# 1. Add to openrouter_adapter.py (macro data) OR grok_agentic.py (sentiment/on-chain)
PROMPT_TEMPLATES = {
    # ... existing templates ...
    'fear_greed_index': """
    Get the current Crypto Fear & Greed Index from alternative.me or similar sources.

    Return JSON:
    {
      "value": <int 0-100>,
      "classification": <string: "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed">,
      "timestamp": <ISO 8601>,
      "interpretation": <string: crypto market psychology and implications>,
      "signal": <"bullish" | "bearish" | "neutral">
    }
    """
}

# 2. Add to catalog_mapping.py
('sentiment_social', 'fear_greed_index'): {
    'data_type': 'grok_agentic',
    'params_template': {'query_type': 'fear_greed_index'},
    'cache_ttl': 3600  # 1 hour
}

# 3. Seed database (SQL)
INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled)
VALUES (
    (SELECT source_id FROM data_sources WHERE name = 'sentiment_social'),
    'fear_greed_index',
    'Fear & Greed Index',
    'Crypto market sentiment gauge from 0 (Extreme Fear) to 100 (Extreme Greed)',
    ARRAY['fear_greed_index']::TEXT[],
    FALSE,
    TRUE
);

# 4. Test
python -m scripts.test_grok_intelligence
```

**Cost**: ~$0.002-0.005 per query (simple web search)

---

### **Option 2: Create New Adapter (Advanced)**

**When to Use**: Specialized APIs, complex data processing, custom protocols

**Steps** (2-4 hours):

1. **Create adapter file**: `market_intelligence/adapters/{category}/{name}.py`

```python
from market_intelligence.adapters.base import DataAdapter
from market_intelligence.types import QueryParams, AdapterResponse

class MyNewAdapter(DataAdapter):
    name = "my_new_adapter"
    data_type = "my_data_type"

    async def fetch(self, params: QueryParams) -> AdapterResponse:
        # 1. Extract params
        symbol = params.get('symbol')

        # 2. Call external API
        data = await self._fetch_from_api(symbol)

        # 3. Process & structure
        processed = self._process_data(data)

        # 4. Return response
        return AdapterResponse(
            data=processed,
            metadata={"source": "MyAPI", "cost": 0.01},
            confidence=0.9
        )
```

2. **Create catalog YAML**: `market_intelligence/catalog/data_types/{category}/{name}.yaml`

```yaml
name: my_data_type
category: my_category
description: "Description of what this provides"

query_params:
  symbol:
    type: string
    required: true
    description: "Trading pair symbol"

sources:
  - adapter: MyNewAdapter
    priority: 1
    cost: 0.01

cache:
  backend: redis
  ttl: 3600
  key_pattern: "my_data:{symbol}"

response_schema:
  type: object
  properties:
    value:
      type: number
    signal:
      type: string
```

3. **Add catalog mapping**: `catalog_mapping.py`

```python
('my_category', 'my_point'): {
    'data_type': 'my_data_type',
    'params_template': {'symbol': '{symbol}'},
    'cache_ttl': 3600
}
```

4. **Seed database**: Create data_source + data_point entries

5. **Test**: Write test script, validate end-to-end

---

## ⚡ Performance & Economics

### **Performance Benchmarks**

| Metric | Sequential (Old) | Parallel (Current) | Improvement |
|--------|-----------------|-------------------|-------------|
| **8 Grok queries** | 160 seconds | ~30 seconds | **5.3x faster** |
| **Technical indicators (21)** | 0.753s (V1) | 0.064s (V2) | **12x faster** |
| **Cache hit latency** | N/A | <1ms | Instant |
| **Cache miss latency** | N/A | 15-30s (Grok) | Acceptable |

### **Cost Economics**

**Per-Query Costs** (8 sources, hybrid setup):
- **Perplexity (macro)**: ~$0.01 each (VIX, DXY, CPI, NFP)
- **Grok (Twitter/on-chain)**:
  - BTC TVL: $0.0017
  - Whale Activity: $0.0134
  - Crypto News: $0.0149
  - Twitter Sentiment: $0.0637 (most expensive, native X access + NLP)

**Total**: ~$0.08 for all 8 queries (first run, no cache) - 27% cost reduction vs pure Grok

**Monthly Platform Cost** (257 users):
```
Scenario: All users enable all 8 Grok data points

Without caching:
  257 users × 8 queries × 24 times/day = 49,344 queries/day
  49,344 × $0.0138 avg = $680/day = $20,400/month ❌

With Smart Caching + Hybrid (Custom TTL per data type):
  VIX/DXY/CPI/NFP (Perplexity): 98 queries/day × $0.01 = $0.98/day
  Twitter (Grok, 30min): 48 queries/day × $0.0637 = $3.06/day
  News (Grok, 10min): 144 queries/day × $0.0149 = $2.15/day
  BTC TVL (Grok, 1hr): 24 queries/day × $0.0017 = $0.04/day
  Whale (Grok, 30min): 48 queries/day × $0.0134 = $0.64/day

  Total: ~$6.87/day = $206/month ✅
  Cost per user: $0.80/month 🎉
```

**Scaling Economics**:
- At 1000 users: $0.20/user/month (cost per user **decreases**)
- At 10,000 users: $0.02/user/month (economies of scale!)

**Why? Shared cache** - VIX is same for all users, so 1 API call serves everyone who queries within TTL window.

### **Cache Hit Rate Optimization**

**Custom TTL Strategy** (2026-01-13 cost optimization):
- **Static data** (CPI, NFP) → 24 hours → 96% fewer queries
- **Slow-moving** (BTC TVL) → 6 hours → 95% fewer queries
- **Moderate** (VIX, DXY, sentiment) → 4 hours → 94% fewer queries
- **Semi-fast** (news, whale) → 2 hours → 88% fewer queries

**Result**: ~95% cache hit rate across all data types = **20x cost reduction**

**Cache Key Pattern**: `intel:grok:{query_type}:{symbol}` (fixed 2026-01-13)

**Legacy Category Aliases** (backward compatibility):
- `on_chain` → `onchain_analytics`
- `sentiment` → `sentiment_social`
- `news` / `news_events` → `news_regulatory`
- `derivatives` → `derivatives_leverage`

---

## 🔍 Operations & Debugging

### **Enabling Data Sources in Config**

**Frontend**:
1. Navigate to bot configuration
2. Expand data source categories (Macro, On-Chain, Sentiment, etc.)
3. Check desired data points
4. Click Save

**Config Structure**:
```json
{
  "extraction": {
    "selected_data_sources": {
      "macro_economics": {
        "timeframes": ["5m", "15m", "1h"],  // Ignored for non-technical
        "data_points": ["vix", "dxy", "cpi"]
      },
      "sentiment_social": {
        "data_points": ["twitter_sentiment"]
      }
    }
  }
}
```

### **Monitoring Cache Hit Rates**

```bash
# Connect to Redis
redis-cli

# Check cache keys
KEYS intel:*

# Check specific key TTL
TTL intel:grok_agentic:{query_type:vix_index}

# Monitor cache stats
INFO stats
# Look for: keyspace_hits, keyspace_misses
# Hit rate = hits / (hits + misses)
```

**Target**: 70-90% cache hit rate for cost efficiency

### **Troubleshooting Common Issues**

#### **Issue: Data Point Not Showing in Frontend**

**Check**:
1. Database seeding: `SELECT * FROM data_points WHERE name = 'vix';`
2. Enabled flag: `enabled = TRUE`
3. Data source enabled: `SELECT * FROM data_sources WHERE source_id = ?`

**Fix**: Run seed script or update `enabled = TRUE`

---

#### **Issue: Gateway Returns "Unknown data type"**

**Check**:
1. Catalog YAML exists: `ls market_intelligence/catalog/data_types/**/*.yaml`
2. Catalog loaded: Check logs for "Loaded X catalog entries"
3. Mapping exists: Check `catalog_mapping.py` for entry

**Fix**: Add catalog YAML or mapping entry

---

#### **Issue: Cache Miss Every Query (High Cost)**

**Check**:
1. Redis running: `redis-cli ping` (should return "PONG")
2. Cache key pattern: Check logs for "Cache key: intel:..."
3. TTL set correctly: `TTL intel:...` (should return seconds, not -1 or -2)

**Fix**:
- Restart Redis if down
- Verify `cache_ttl` in mapping or catalog YAML
- Check `gateway.py` applies TTL override correctly

---

#### **Issue: Parallel Execution Slow**

**Check**:
1. How many queries: If 1-2, sequential is fine
2. Network latency: Grok API in different region?
3. Adapter blocking: Check if adapter has sync operations (use `async`/`await`)

**Fix**:
- Use `asyncio.gather()` for 3+ queries
- Profile with `time` module to identify bottleneck
- Convert blocking operations to async

---

### **Debugging Flow**

```python
# 1. Enable debug logging
from core.common.logger import logger
logger.setLevel("DEBUG")

# 2. Test orchestrator
from market_intelligence.orchestrator import fetch_market_intelligence
result = await fetch_market_intelligence(config, user_id, "BTC/USDT")
print(result)

# 3. Test gateway directly
from market_intelligence.gateway import MarketIntelligence
gateway = MarketIntelligence()
response = await gateway.query(
    data_type='grok_agentic',
    params={'query_type': 'vix_index'}
)
print(response.data)

# 4. Test adapter directly
from market_intelligence.adapters.agentic.grok_agentic import GrokAgenticAdapter
adapter = GrokAgenticAdapter()
result = await adapter.fetch(QueryParams(params={'query_type': 'vix_index'}))
print(result.data)

# 5. Check database storage
# SELECT * FROM market_data WHERE config_id = ? ORDER BY created_at DESC LIMIT 10;
```

---

## 📚 Implementation References

### **Deep Dive Documentation**

- **Technical Indicators (21 Preprocessors)**: See [`extraction/v2/README.md`](../extraction/v2/README.md)
  - Preprocessor architecture
  - How to add new indicators
  - Advanced analysis features
  - Token optimization (summary-first approach)

- **Database Schema**: See [`database/schema.md`](../database/schema.md)
  - market_data table structure
  - data_sources / data_points tables
  - Multi-timeframe storage pattern
  - Query examples

- **Catalog Schemas**: See `market_intelligence/catalog/data_types/`
  - YAML schema reference
  - Parameter validation rules
  - Cache configuration options
  - Response schema definitions

- **Current Status**: See [`ACTIVE.md`](../ACTIVE.md)
  - Production deployment status
  - System health metrics
  - Current data source availability

- **Implementation History**: See [`CHANGELOG.md`](../CHANGELOG.md)
  - 2025-10-28: Phase 1 production deployment
  - Bug fixes and performance optimizations
  - Architecture evolution

- **Future Roadmap**: See [`TODO.md`](../TODO.md)
  - Phase 2 plans
  - Additional data sources
  - System enhancements

### **Directory Structure**

```
market_intelligence/
├── README.md                           # THIS FILE - Complete architecture
├── orchestrator.py                     # Config-driven routing layer
├── gateway.py                          # Universal Data Layer gateway
├── catalog_mapping.py                  # Data point → catalog mapping
├── types.py                            # Type definitions, data classes
├── response_formatter.py               # Response formatting utilities
├── catalog/                            # Catalog system
│   ├── __init__.py                    # Catalog loader
│   └── data_types/                    # YAML schemas (4 types currently)
│       ├── derivatives/
│       │   └── funding_rate.yaml      # BTC/ETH funding rates
│       ├── agentic/
│       │   └── grok_agentic.yaml      # Universal Grok intelligence
│       ├── signals/
│       │   └── ggshot_signals.yaml    # ggShot trading signals
│       └── market_data/
│           └── ohlcv.yaml             # OHLCV candle data
├── adapters/                           # Data source adapters
│   ├── base.py                        # Base adapter interface
│   ├── derivatives/
│   │   └── binance_funding.py         # Binance funding rates
│   ├── agentic/
│   │   ├── grok_agentic.py            # XAI Grok (4 Twitter/on-chain sources)
│   │   └── openrouter_adapter.py      # OpenRouter/Perplexity (4 macro sources)
│   ├── signals/
│   │   └── ggshot_adapter.py          # ggShot signal queries
│   └── market_data/
│       └── redis_websocket.py         # WebSocket price cache
└── cache/
    └── redis_cache.py                  # Redis caching implementation
```

---

## 🚀 Quick Start Examples

### **Example 1: Query VIX in Python**

```python
from market_intelligence.orchestrator import fetch_market_intelligence
from core.domain.bot_config_v2 import BotConfigV2

# Load config with VIX enabled
config = BotConfigV2.from_dict({
    "extraction": {
        "selected_data_sources": {
            "macro_economics": {"data_points": ["vix"]}
        }
    }
})

# Fetch market intelligence
result = await fetch_market_intelligence(config, user_id, "BTC/USDT")
vix_data = result["macro_economics"]["vix"]
print(f"VIX: {vix_data['value']}, Signal: {vix_data['signal']}")
```

### **Example 2: Agent Dynamic Query**

```python
# Agent queries Twitter sentiment without config
result = await fetch_market_intelligence(
    config,
    user_id,
    "BTC/USDT",
    data_points_override={
        "sentiment_social": ["twitter_sentiment"]
    }
)
sentiment = result["sentiment_social"]["twitter_sentiment"]
print(f"Sentiment: {sentiment['sentiment_score']} ({sentiment['signal']})")
```

### **Example 3: Test All Grok Sources**

```bash
# Run comprehensive test suite
cd /home/sev/ggbot
source .venv/bin/activate
python -m scripts.test_all_grok_data_points

# Generates markdown report in DOCS/
```

---

## 📞 Support & Contributing

### **Getting Help**

- **Architecture questions**: This README
- **Technical indicators**: `extraction/v2/README.md`
- **Database queries**: `database/schema.md`
- **Production status**: `ACTIVE.md`

### **Logging**

All components use structured logging:
```python
from core.common.logger import logger
_log = logger.bind(component="market_intelligence", user_id=user_id)
_log.info("Market intelligence fetched", data_points=8, latency_ms=30123)
```

### **Adding Features**

1. **New Grok query type**: See "Adding New Data Sources" → Option 1
2. **New adapter**: See "Adding New Data Sources" → Option 2
3. **New preprocessor**: See `extraction/v2/README.md`

### **Testing**

```python
# System health check
from market_intelligence.gateway import MarketIntelligence
gateway = MarketIntelligence()
test_result = await gateway.catalog.load_all()
print(f"Catalog loaded: {len(gateway.catalog.list_all())} data types")

# Test orchestrator
from market_intelligence.orchestrator import fetch_market_intelligence
result = await fetch_market_intelligence(config, user_id, "BTC/USDT")
print(f"Fetched {sum(len(cat) for cat in result.values())} data points")
```

---

**The Market Data System represents ggbots' complete data pipeline - from user configuration to AI-driven trading decisions, orchestrating 33 data points across 6 categories with production-proven performance, cost efficiency, and extensibility.** 🚀

**Phase 1 Status**: ✅ **PRODUCTION DEPLOYED** (2025-10-28, cost-optimized 2026-01-13)
