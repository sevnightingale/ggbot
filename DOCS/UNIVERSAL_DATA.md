# Universal Data Layer - Architecture & Implementation Plan

**Status:** Planning Phase
**Branch:** `universal-data-layer`
**Vision:** Catalog-driven market intelligence platform serving both trading bots and AI agents

---

## Executive Summary

The Universal Data Layer transforms ggbots from a technical-analysis-only system into a comprehensive market intelligence platform. Instead of building isolated data clients, we create a unified gateway that:

1. **Replaces** existing HummingbotDataClient with WebSocket-backed OHLCV (immediate win)
2. **Expands** to 156 data sources via catalog-driven architecture (future scaling)
3. **Exposes** all data as Agent SDK tools (AI-first design)
4. **Maintains** backward compatibility with zero breaking changes (safe deployment)

**Key Innovation:** Declare data sources in YAML catalogs, implement simple adapter classes, get automatic caching, validation, routing, agent tools, API endpoints, and CLI commands.

---

## Vision & Goals

### Primary Goals

1. **Unified Intelligence Gateway**
   - Single entry point for ALL market data (OHLCV, sentiment, news, on-chain, fundamentals, macro)
   - Consistent query interface regardless of data type
   - Intelligent routing with automatic fallback
   - Multi-tier caching strategy

2. **Catalog-Driven Architecture**
   - Data sources defined declaratively in YAML
   - Adapters implement single `fetch()` method
   - Framework handles everything else (caching, validation, formatting, tools)
   - Add new sources in hours, not days

3. **Agent-First Design**
   - Auto-generate Agent SDK tools from catalog
   - LLM-optimized response formatting
   - Natural language summaries with actionable insights
   - Self-documenting with usage examples

4. **Zero Breaking Changes**
   - ExtractionEngine uses new system transparently
   - DecisionEngine requires no modifications
   - Database schema unchanged
   - Gradual migration path

### Success Metrics

- **Phase 1:** OHLCV replacement working in production (1 week)
- **Phase 2:** 5 additional data sources live (sentiment, news, on-chain) (2 weeks)
- **Phase 3:** Agent SDK integration complete (1 week)
- **Phase 4:** 50+ data sources available (8 weeks)

---

## Architecture Overview

### Three-Layer Design

```
┌─────────────────────────────────────────────────────────────┐
│                    CONSUMER LAYER                            │
│                                                              │
│  • ExtractionEngine (existing, backward compatible)         │
│  • Agent SDK Tools (auto-generated from catalogs)           │
│  • External Agents via MCP (standardized interface)         │
│  • Direct API clients (REST/GraphQL endpoints)              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│               INTELLIGENCE GATEWAY LAYER                     │
│                                                              │
│  • MarketIntelligence class (unified query interface)       │
│  • DataCatalog registry (loads YAML definitions)            │
│  • QueryValidator (schema-based validation)                 │
│  • ResponseFormatter (raw/analysis/LLM modes)               │
│  • RouterEngine (priority-based source selection)           │
│  • CacheManager (multi-backend with TTL)                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 DATA ADAPTER LAYER                           │
│                                                              │
│  Abstract DataAdapter base class with single method:        │
│    async def fetch(params: QueryParams) -> AdapterResponse  │
│                                                              │
│  Concrete adapters by category:                             │
│  • market_data/ (redis_websocket, binance_rest, ccxt)      │
│  • sentiment/ (twitter, reddit, telegram, lunarcrush)       │
│  • news/ (crypto_news, benzinga, google_news)              │
│  • onchain/ (glassnode, nansen, dune, etherscan)           │
│  • fundamentals/ (sec_edgar, alpha_vantage, finnhub)       │
│  • macro/ (fred, bls, treasury, fed)                       │
│  • ... (150+ total adapters)                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   CACHING LAYER                              │
│                                                              │
│  • Redis (real-time: OHLCV, sentiment, news)               │
│  • PostgreSQL (historical: fundamentals, transcripts)       │
│  • In-Memory (static: calendars, schedules)                │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

**Query Path:**
1. Consumer calls `MarketIntelligence.query(data_type, params)`
2. DataCatalog validates params against schema
3. CacheManager checks for cached result (key pattern from catalog)
4. On cache miss: RouterEngine selects adapter by priority
5. Adapter.fetch() retrieves data from source
6. ResponseFormatter applies output mode (raw/analysis/LLM)
7. CacheManager stores result with catalog-defined TTL
8. Formatted response returns to consumer

**Agent Tool Path:**
1. Agent SDK loads all catalog entries at startup
2. For each entry, generates AgentTool with params from catalog
3. Tool execution calls MarketIntelligence.query()
4. Response auto-formatted using catalog's agent_format template
5. Natural language summary + key insights returned to agent

---

## Core Components

### 1. DataCatalog (Declarative Registry)

**Location:** `market_intelligence/catalog.py`

**Responsibilities:**
- Load all YAML catalog entries from `catalog/data_types/`
- Validate catalog schema (required fields, types, constraints)
- Provide lookup by data_type name
- Generate query parameter schemas for validation
- Build cache keys from templates
- Format agent responses from templates

**Catalog Schema:**
- name: Unique identifier for data type
- category: Grouping (market_data, sentiment, news, etc.)
- description: Human-readable explanation
- query_params: Input schema with types, defaults, constraints
- sources: Prioritized list of adapters with fallback
- cache: Backend, TTL, key pattern
- response_schema: Output structure definition
- agent_format: Summary and insights templates
- examples: Usage examples for documentation
- data_quality: Latency/freshness targets

### 2. MarketIntelligence (Unified Gateway)

**Location:** `market_intelligence/gateway.py`

**Responsibilities:**
- Single query interface for all data types
- Coordinate validation → caching → routing → formatting
- Handle errors and fallback logic
- Track metrics (latency, cache hit rate, source usage)
- Provide discovery API (list available data types)

**Key Methods:**
- `async query(data_type, params, format=QueryFormat.ANALYSIS)` - Main entry point
- `get_catalog_entry(data_type)` - Lookup catalog definition
- `validate_params(data_type, params)` - Schema validation
- `list_data_types(category=None)` - Discovery
- `get_metrics()` - Performance statistics

### 3. DataAdapter (Abstract Base)

**Location:** `market_intelligence/adapters/base.py`

**Responsibilities:**
- Define adapter interface (single method)
- Provide utility methods (HTTP client, retry logic, rate limiting)
- Handle common error scenarios
- Calculate data quality confidence scores

**Required Method:**
- `async fetch(params: QueryParams) -> AdapterResponse`

**Response Format:**
- data: The actual payload (DataFrame, dict, list, etc.)
- metadata: Source info, timestamps, query details
- confidence: Data quality score (0.0-1.0)
- related_queries: Suggested follow-up queries

### 4. CacheManager (Multi-Backend)

**Location:** `market_intelligence/cache/manager.py`

**Responsibilities:**
- Abstract caching across Redis, PostgreSQL, in-memory
- Build cache keys from catalog templates
- Handle TTL per data type
- Provide invalidation API
- Track cache statistics

**Cache Backends:**
- RedisCache: Real-time data (OHLCV, sentiment, news) - sub-second TTL
- PostgresCache: Historical data (fundamentals, transcripts) - hours/days TTL
- MemoryCache: Static data (calendars, schedules) - session TTL

### 5. ResponseFormatter (Output Modes)

**Location:** `market_intelligence/response_formatter.py`

**Responsibilities:**
- Format responses based on consumer needs
- Apply catalog templates for agent mode
- Generate natural language summaries
- Extract key insights and signals

**Format Modes:**
- RAW: Unprocessed data from adapter
- ANALYSIS: Structured with metadata and insights
- LLM: Natural language optimized for agents

### 6. RouterEngine (Source Selection)

**Location:** `market_intelligence/router.py`

**Responsibilities:**
- Select adapter based on priority in catalog
- Handle fallback on adapter failure
- Track source performance metrics
- Support A/B testing of sources

**Selection Logic:**
- Try sources in priority order
- Skip if required env vars missing
- Skip if rate limit exceeded
- Log failures for monitoring
- Return first successful response

---

## Catalog-Driven Design

### Catalog Entry Structure

**File Location:** `market_intelligence/catalog/data_types/{category}/{name}.yaml`

**Sections:**

**Metadata:**
- name: snake_case identifier
- category: Categorical grouping
- description: What this data provides

**Input Definition:**
- query_params: Schema with type, required, default, min/max, enum
- Automatically generates validation logic
- Automatically generates API/CLI parameters

**Source Configuration:**
- sources: Array of adapters with priority, cost, rate limits
- required_env: Environment variables needed
- Supports multi-source fallback

**Caching Strategy:**
- backend: redis | postgres | memory
- ttl: Seconds until expiration
- key_pattern: Template with {param} placeholders

**Output Definition:**
- response_schema: JSON Schema for response structure
- Validates adapter output
- Generates documentation

**Agent Integration:**
- agent_format: Templates for summary and insights
- Uses Jinja2-style placeholders
- Automatically applied when format=LLM

**Quality & Documentation:**
- data_quality: Latency/freshness targets
- examples: Query examples with descriptions
- Used for testing and documentation generation

### Auto-Generated Artifacts

**From Single Catalog Entry:**

1. **Agent SDK Tool**
   - Tool name from catalog.name
   - Description from catalog.description
   - Parameters from catalog.query_params
   - Execute function auto-wired to MarketIntelligence.query()

2. **API Endpoint**
   - GET /api/intelligence/{data_type}
   - Query params from catalog.query_params
   - OpenAPI spec auto-generated

3. **CLI Command**
   - `market-intel query {data_type} [--param value ...]`
   - Help text from catalog.description
   - Argument parsing from catalog.query_params

4. **Validation Logic**
   - Pydantic model from query_params schema
   - Type checking, range validation, enum validation
   - Automatic error messages

5. **Cache Key Builder**
   - Template rendering with actual param values
   - Consistent keys across system

6. **Test Cases**
   - Example queries from catalog.examples
   - Schema validation tests
   - Adapter contract tests

7. **Documentation**
   - API docs with examples
   - CLI help text
   - Agent tool descriptions

---

## Integration Points

### Backward Compatibility Strategy

#### ExtractionEngine Integration

**File:** `extraction/v2/extraction_engine.py`

**Current State:**
- Uses HummingbotDataClient for OHLCV
- Fetches candles via `get_candles_with_fallback()`
- Calculates indicators using pandas-ta
- Stores to Supabase via SupabaseStorage

**Migration Path:**
1. Replace HummingbotDataClient instantiation with MarketIntelligence
2. Modify `_fetch_candles()` to call `intelligence.query('ohlcv', params)`
3. Keep indicator calculation logic unchanged
4. Keep storage logic unchanged
5. Response format maps directly to existing structure

**Key Changes:**
- Constructor: Initialize MarketIntelligence instead of HummingbotDataClient
- Data fetching: Use `query()` instead of `get_candles_with_fallback()`
- Everything else: Zero changes

**Result:**
- Same database records
- Same API responses
- Same behavior for DecisionEngine
- But now uses WebSocket cache + multi-source fallback

#### DecisionEngine Integration

**File:** `decision/engine_v2.py`

**No changes required!**

DecisionEngine reads from `market_data` table which ExtractionEngine continues to populate. The data source change is transparent.

**Optional Enhancement (Future):**
- DecisionEngine could directly query additional data types
- Example: `intelligence.query('sentiment', {symbol: 'BTC'})`
- Example: `intelligence.query('news', {symbol: 'BTC', since: '24h'})`
- Enriches decision context beyond just OHLCV

#### Orchestrator Integration

**File:** `ggbot.py`

**Current Flow:**
1. Scheduler triggers execution by config_id
2. Calls ExtractionEngine.extract_for_config()
3. Calls DecisionEngine.make_decision()
4. Calls TradingEngine.execute()

**After Migration:**
- Flow unchanged
- ExtractionEngine internally uses MarketIntelligence
- No orchestrator modifications needed

**Benefits:**
- Same scheduling logic
- Same error handling
- Same monitoring
- But faster extractions (WebSocket vs REST)

### Agent SDK Integration

#### Tool Generation

**Location:** `market_intelligence/tools/agent_sdk.py`

**Process:**
1. Load all catalog entries at initialization
2. For each entry, instantiate AgentTool class
3. Tool name from catalog.name
4. Parameters from catalog.query_params
5. Execute method calls MarketIntelligence.query()

**Agent Usage:**
- Agent receives list of available tools
- Chooses tool based on task
- Provides parameters
- Receives LLM-formatted response with summary + insights

#### MCP Server Integration

**Location:** `market_intelligence/tools/mcp.py`

**Provides:**
- Single MCP tool: `query_market_intelligence`
- Parameters: data_type (string) + dynamic params (dict)
- Discovers available data types from catalog
- Returns natural language responses

**Agent Experience:**
- Agent sees one tool with 156 data types available
- Can query any market intelligence
- Response always formatted for agent consumption

---

## Implementation Plan

### Phase 1: Foundation & OHLCV Migration (Week 1)

**Goal:** Replace HummingbotDataClient with MarketIntelligence, using existing WebSocket cache

#### Step 1.1: Core Framework (Day 1-2)

**Tasks:**
1. Create directory structure under `market_intelligence/`
2. Implement DataCatalog class with YAML loading
3. Implement MarketIntelligence gateway with basic routing
4. Implement DataAdapter abstract base class
5. Implement CacheManager with Redis backend
6. Implement ResponseFormatter with RAW mode only
7. Create catalog schema validator

**Files Created:**
- `market_intelligence/__init__.py`
- `market_intelligence/gateway.py`
- `market_intelligence/catalog.py`
- `market_intelligence/adapters/base.py`
- `market_intelligence/cache/manager.py`
- `market_intelligence/cache/redis_cache.py`
- `market_intelligence/response_formatter.py`
- `market_intelligence/types.py` (QueryParams, AdapterResponse, etc.)

**Testing:**
- Unit tests for DataCatalog loading
- Unit tests for cache key generation
- Integration test: query → cache → response

#### Step 1.2: OHLCV Catalog & Adapter (Day 2-3)

**Tasks:**
1. Create OHLCV catalog entry with full schema
2. Implement RedisWebSocketAdapter (reads from existing Redis cache)
3. Implement BinanceRestAdapter (fallback for cache misses)
4. Add catalog validation for OHLCV
5. Test adapter contract compliance

**Files Created:**
- `market_intelligence/catalog/data_types/market_data/ohlcv.yaml`
- `market_intelligence/adapters/market_data/redis_websocket.py`
- `market_intelligence/adapters/market_data/binance_rest.py`

**Catalog Entry Defines:**
- Query params: symbol, timeframe, indicators, limit
- Sources: [redis_websocket (priority 1), binance_rest (priority 2)]
- Cache: Redis, 3600s TTL, key pattern from existing WebSocket service
- Response: DataFrame schema matching current ExtractionEngine format

**Testing:**
- Query OHLCV from Redis (should hit cache from WebSocket service)
- Query OHLCV for uncached symbol (should fetch from Binance REST)
- Verify DataFrame format matches existing structure

#### Step 1.3: ExtractionEngine Migration (Day 3-4)

**Tasks:**
1. Modify ExtractionEngine constructor to use MarketIntelligence
2. Replace HummingbotDataClient.get_candles_with_fallback() calls
3. Map MarketIntelligence response to existing format
4. Add logging for source tracking (Redis vs REST)
5. Test with single bot configuration
6. Compare database records (before vs after)

**Files Modified:**
- `extraction/v2/extraction_engine.py` (replace data_client usage)

**Migration Strategy:**
- Keep HummingbotDataClient imported (commented out)
- Add feature flag: `USE_UNIVERSAL_DATA=true` (default false)
- If flag enabled, use MarketIntelligence, else HummingbotDataClient
- Test both paths in parallel
- Remove HummingbotDataClient after validation

**Testing:**
- Run extraction for BTC/USDT, compare to baseline
- Verify market_data table records identical
- Check cache hit rate (should be 95%+ from WebSocket)
- Monitor extraction latency (should be 3x faster)

#### Step 1.4: Production Validation (Day 4-5)

**Tasks:**
1. Enable for 1 test bot (config_id from dev)
2. Monitor for 24 hours
3. Enable for 5 bots
4. Monitor for 24 hours
5. Enable for all bots
6. Remove feature flag, make default

**Validation Checklist:**
- ✅ Extractions succeed at same rate
- ✅ Database records identical structure
- ✅ Decision engine receives same data format
- ✅ Trading executions unaffected
- ✅ Cache hit rate >90%
- ✅ Extraction latency reduced 3x
- ✅ No errors in logs

**Rollback Plan:**
- Set `USE_UNIVERSAL_DATA=false`
- Restart PM2 processes
- System reverts to HummingbotDataClient
- No data loss, no downtime

### Phase 2: Expand Data Sources (Week 2-3)

**Goal:** Add 5 high-value data sources beyond OHLCV

#### Step 2.1: Sentiment Analysis (Day 6-8)

**Sources:**
1. Twitter/X sentiment
2. Reddit sentiment
3. LunarCrush aggregated sentiment

**Tasks Per Source:**
1. Create catalog YAML (query params, caching, agent format)
2. Implement adapter class (fetch method only)
3. Add integration tests
4. Validate catalog compliance

**Files Created:**
- `catalog/data_types/sentiment/twitter.yaml`
- `catalog/data_types/sentiment/reddit.yaml`
- `catalog/data_types/sentiment/lunarcrush.yaml`
- `adapters/sentiment/twitter.py`
- `adapters/sentiment/reddit.py`
- `adapters/sentiment/lunarcrush.py`

**Testing:**
- Query each source independently
- Verify caching works (5min TTL)
- Test response format (sentiment_score, mentions, trend, topics)

#### Step 2.2: News & Events (Day 9-10)

**Sources:**
1. Crypto news aggregator (CoinDesk, CoinTelegraph)
2. Google News API

**Files Created:**
- `catalog/data_types/news/crypto_news.yaml`
- `catalog/data_types/news/google_news.yaml`
- `adapters/news/crypto_news.py`
- `adapters/news/google_news.py`

**Testing:**
- Query recent news for BTC
- Verify article extraction (title, summary, sentiment, timestamp)
- Test caching (10min TTL)

#### Step 2.3: On-Chain Data (Day 11-13)

**Sources:**
1. Glassnode (exchange flows, whale activity)
2. Etherscan (blockchain metrics)

**Files Created:**
- `catalog/data_types/onchain/glassnode.yaml`
- `catalog/data_types/onchain/etherscan.yaml`
- `adapters/onchain/glassnode.py`
- `adapters/onchain/etherscan.py`

**Testing:**
- Query Bitcoin exchange netflow
- Query Ethereum gas metrics
- Verify caching (30min TTL)

### Phase 3: Agent SDK Integration (Week 4)

**Goal:** Auto-generate agent tools from catalogs, enable AI agents to query intelligence

#### Step 3.1: Tool Generator (Day 14-15)

**Tasks:**
1. Implement ToolGenerator class
2. Generate AgentTool from catalog entry
3. Create tool registry with all data types
4. Add tool discovery endpoint

**Files Created:**
- `market_intelligence/tools/generator.py`
- `market_intelligence/tools/registry.py`
- `market_intelligence/tools/agent_sdk.py`

**Tool Generation Logic:**
- Load catalog entry
- Extract name, description, parameters
- Create execute function that calls MarketIntelligence.query()
- Apply agent_format template to response
- Return natural language summary + insights

**Testing:**
- Generate tools from all catalog entries
- Verify tool parameters match catalog
- Test tool execution returns formatted response

#### Step 3.2: MCP Server (Day 15-16)

**Tasks:**
1. Implement MCP server with single tool
2. Tool accepts data_type + dynamic params
3. Returns LLM-formatted response
4. Add data type discovery

**Files Created:**
- `market_intelligence/tools/mcp.py`
- `market_intelligence/tools/mcp_server.py`

**MCP Tool:**
- Name: `query_market_intelligence`
- Parameters: data_type (enum of all types), params (object)
- Returns: Natural language summary with insights
- Discovery: Lists all available data types with descriptions

**Testing:**
- Start MCP server
- Query via MCP protocol
- Verify response formatting
- Test with Claude Desktop

#### Step 3.3: Response Formatting Enhancement (Day 16-17)

**Tasks:**
1. Implement ANALYSIS format mode
2. Implement LLM format mode with templates
3. Add insight extraction logic
4. Create default templates for all data types

**Files Modified:**
- `market_intelligence/response_formatter.py`

**Format Modes:**
- RAW: Direct adapter output (for system use)
- ANALYSIS: Structured with metadata, insights, signals (for dashboards)
- LLM: Natural language with summary and key points (for agents)

**Template Variables:**
- Access all response data fields
- Use conditionals for dynamic content
- Include confidence scoring
- Suggest related queries

**Testing:**
- Query same data in all three formats
- Verify LLM format is human-readable
- Test template variable substitution
- Validate insight extraction quality

### Phase 4: Scale & Optimize (Week 5-8)

**Goal:** Add remaining high-priority data sources, optimize performance

#### Step 4.1: Fundamentals (Week 5)

**Sources:**
- SEC EDGAR filings
- Alpha Vantage fundamentals
- Financial Modeling Prep

**Categories:**
- Income statements
- Balance sheets
- Cash flow statements
- Consensus estimates
- Earnings transcripts

#### Step 4.2: Macro & Economic (Week 6)

**Sources:**
- FRED (Federal Reserve Economic Data)
- BLS (Bureau of Labor Statistics)
- Treasury data
- Economic calendars

**Metrics:**
- Inflation (CPI/PCE)
- Employment (NFP, JOLTS)
- Interest rates
- Yield curves

#### Step 4.3: Options & Derivatives (Week 7)

**Sources:**
- Options flow aggregators
- Unusual options activity
- Put/call ratios
- Implied volatility surfaces

#### Step 4.4: Additional Categories (Week 8)

**Complete remaining categories:**
- ETF flows
- Insider trading
- Short interest
- Technical patterns
- Market breadth
- Futures positioning

---

## Standard Operating Procedure: Adding New Data Source

### Prerequisites

1. Identify data source (API, scraper, calculated, aggregated)
2. Obtain API credentials if needed (add to .env)
3. Review existing adapters in same category for patterns
4. Determine appropriate cache TTL based on data freshness

### Step-by-Step Process

#### Step 1: Create Catalog Entry (15 minutes)

**Location:** `market_intelligence/catalog/data_types/{category}/{name}.yaml`

**Required Sections:**
1. Metadata (name, category, description)
2. Query parameters (with types, defaults, validation)
3. Source configuration (adapter class, env vars, rate limits)
4. Cache strategy (backend, TTL, key pattern)
5. Response schema (output structure)
6. Agent format (summary and insights templates)
7. Examples (at least 2 usage examples)
8. Quality targets (latency, freshness)

**Validation:**
- Run `market-intel validate-catalog {name}`
- Fix any schema errors
- Ensure key pattern has unique placeholders

#### Step 2: Implement Adapter (2-3 hours)

**Location:** `market_intelligence/adapters/{category}/{name}.py`

**Required:**
1. Import DataAdapter base class
2. Define adapter class inheriting from DataAdapter
3. Implement `__init__()` with credential setup
4. Implement `async fetch(params: QueryParams) -> AdapterResponse`
5. Add confidence scoring logic
6. Add error handling with specific exceptions

**Fetch Method Pattern:**
1. Extract params from QueryParams object
2. Call external API/scraper/calculator
3. Transform response to expected schema
4. Calculate data quality confidence
5. Return AdapterResponse with data + metadata

**Best Practices:**
- Use async HTTP client from base class
- Implement retry logic with exponential backoff
- Rate limit using base class utilities
- Log failures with context
- Return partial results if possible

#### Step 3: Write Tests (30 minutes)

**Test Files:**
1. Unit tests: `tests/market_intelligence/adapters/test_{name}.py`
2. Integration tests: `tests/market_intelligence/integration/test_{name}.py`

**Test Coverage:**
1. Catalog validation passes
2. Required env vars checked
3. Adapter fetch with valid params succeeds
4. Response matches schema
5. Caching works correctly
6. Agent format template renders
7. Error scenarios handled gracefully

**Run Tests:**
- `pytest tests/market_intelligence/adapters/test_{name}.py`
- `market-intel test {name}` (auto-generated tests)

#### Step 4: Validate Integration (15 minutes)

**Manual Testing:**
1. Query via CLI: `market-intel query {name} --param value`
2. Query via Python: `await intelligence.query('{name}', params)`
3. Check cache: Verify Redis/Postgres entry
4. Query again: Verify cache hit
5. Test in Agent SDK: Verify tool appears and works

**Validation Checklist:**
- ✅ Query succeeds with valid params
- ✅ Query fails gracefully with invalid params
- ✅ Response matches catalog schema
- ✅ Cache stores and retrieves correctly
- ✅ Agent format produces readable summary
- ✅ Tool auto-generated in Agent SDK
- ✅ API endpoint accessible
- ✅ CLI command works

#### Step 5: Documentation (10 minutes)

**Auto-Generated:**
- API docs (from catalog)
- CLI help (from catalog)
- Agent tool description (from catalog)

**Manual Documentation:**
- Add entry to `DOCS/DATA_SOURCES.md` with use cases
- Add example queries to catalog.examples
- Update `DOCS/UNIVERSAL_DATA.md` with new count

#### Step 6: Deploy (5 minutes)

**Deployment:**
1. Commit catalog YAML and adapter Python file
2. Push to branch
3. CI runs auto-generated tests
4. Merge to main
5. Adapter auto-discovered on next deployment
6. Available immediately in all interfaces

**No Manual Steps:**
- No registration code
- No routing updates
- No tool configuration
- No API endpoint creation
- Framework handles everything

**Total Time: 3-4 hours from concept to production**

---

## File Structure

```
market_intelligence/
├── __init__.py
├── gateway.py                          # MarketIntelligence class
├── catalog.py                          # DataCatalog registry
├── router.py                           # RouterEngine
├── response_formatter.py               # ResponseFormatter
├── types.py                            # Type definitions
│
├── adapters/
│   ├── __init__.py
│   ├── base.py                         # DataAdapter abstract class
│   │
│   ├── market_data/
│   │   ├── __init__.py
│   │   ├── redis_websocket.py          # Phase 1
│   │   ├── binance_rest.py             # Phase 1
│   │   └── ccxt_universal.py           # Future
│   │
│   ├── sentiment/
│   │   ├── __init__.py
│   │   ├── twitter.py                  # Phase 2
│   │   ├── reddit.py                   # Phase 2
│   │   ├── telegram.py                 # Future
│   │   └── lunarcrush.py               # Phase 2
│   │
│   ├── news/
│   │   ├── __init__.py
│   │   ├── crypto_news.py              # Phase 2
│   │   ├── google_news.py              # Phase 2
│   │   └── benzinga.py                 # Future
│   │
│   ├── onchain/
│   │   ├── __init__.py
│   │   ├── glassnode.py                # Phase 2
│   │   ├── etherscan.py                # Phase 2
│   │   ├── nansen.py                   # Future
│   │   └── dune.py                     # Future
│   │
│   ├── fundamentals/
│   │   ├── __init__.py
│   │   ├── sec_edgar.py                # Phase 4
│   │   ├── alpha_vantage.py            # Phase 4
│   │   └── financial_modeling.py       # Phase 4
│   │
│   ├── macro/
│   │   ├── __init__.py
│   │   ├── fred.py                     # Phase 4
│   │   ├── bls.py                      # Phase 4
│   │   └── treasury.py                 # Phase 4
│   │
│   └── ... (additional categories)
│
├── cache/
│   ├── __init__.py
│   ├── manager.py                      # CacheManager
│   ├── redis_cache.py                  # RedisCache
│   ├── postgres_cache.py               # PostgresCache
│   └── memory_cache.py                 # MemoryCache
│
├── catalog/
│   ├── schema.yaml                     # Catalog schema definition
│   ├── validator.py                    # Catalog validator
│   │
│   └── data_types/
│       ├── market_data/
│       │   └── ohlcv.yaml              # Phase 1
│       │
│       ├── sentiment/
│       │   ├── twitter.yaml            # Phase 2
│       │   ├── reddit.yaml             # Phase 2
│       │   └── lunarcrush.yaml         # Phase 2
│       │
│       ├── news/
│       │   ├── crypto_news.yaml        # Phase 2
│       │   └── google_news.yaml        # Phase 2
│       │
│       ├── onchain/
│       │   ├── glassnode.yaml          # Phase 2
│       │   └── etherscan.yaml          # Phase 2
│       │
│       └── ... (150+ total catalogs)
│
├── tools/
│   ├── __init__.py
│   ├── generator.py                    # ToolGenerator
│   ├── registry.py                     # Tool registry
│   ├── agent_sdk.py                    # Agent SDK tools
│   └── mcp.py                          # MCP server
│
└── legacy/
    └── extraction_adapter.py           # Backward compat helpers

extraction/v2/
├── extraction_engine.py                # Modified to use MarketIntelligence
└── ... (other files unchanged)

tests/
├── market_intelligence/
│   ├── test_gateway.py
│   ├── test_catalog.py
│   ├── test_cache.py
│   ├── test_formatter.py
│   │
│   ├── adapters/
│   │   ├── test_redis_websocket.py
│   │   ├── test_binance_rest.py
│   │   ├── test_twitter.py
│   │   └── ... (test per adapter)
│   │
│   └── integration/
│       ├── test_ohlcv_flow.py
│       ├── test_sentiment_flow.py
│       └── test_agent_tools.py
```

---

## Testing Strategy

### Unit Tests

**Gateway Layer:**
- DataCatalog loads all YAML files
- Catalog validation catches schema errors
- Query parameter validation works
- Cache key generation from templates
- Response formatting in all modes

**Adapter Layer:**
- Each adapter implements required interface
- Fetch method returns valid AdapterResponse
- Error handling works correctly
- Confidence scoring is reasonable
- Rate limiting prevents overload

**Cache Layer:**
- Redis cache stores and retrieves
- PostgreSQL cache handles large data
- Memory cache works for static data
- TTL expiration functions correctly
- Cache key uniqueness guaranteed

### Integration Tests

**End-to-End Flows:**
1. Query OHLCV from Redis cache (hit)
2. Query OHLCV for uncached symbol (miss → fetch → store)
3. Query sentiment, verify 5min cache works
4. Query news, verify aggregation from multiple sources
5. Query fundamentals, verify PostgreSQL storage

**Agent SDK Integration:**
1. Tools auto-generated from catalogs
2. Tool execution calls MarketIntelligence
3. Response formatted for agent consumption
4. Error handling provides useful feedback

**Backward Compatibility:**
1. ExtractionEngine produces same database records
2. DecisionEngine receives expected format
3. Orchestrator flow unchanged
4. No breaking changes in API responses

### Performance Tests

**Metrics to Track:**
- Query latency (target: <100ms for cached, <1s for fetch)
- Cache hit rate (target: >90% for OHLCV, >70% for others)
- Adapter success rate (target: >95% with fallback)
- Response formatting time (target: <50ms)
- Agent tool execution time (target: <2s end-to-end)

**Load Testing:**
- 100 concurrent OHLCV queries (should use cache)
- 50 concurrent mixed queries (test routing)
- Cache eviction under memory pressure
- Adapter retry logic under failures

### Validation Tests

**Auto-Generated from Catalogs:**
- Example queries from catalog.examples
- Parameter validation from catalog.query_params
- Response schema validation from catalog.response_schema
- Agent format template rendering

**Contract Tests:**
- Adapter adheres to DataAdapter interface
- Response structure matches catalog schema
- Cache keys follow key_pattern template
- Agent format produces valid output

---

## Monitoring & Observability

### Key Metrics

**Query Metrics:**
- Total queries per data_type
- Query latency percentiles (p50, p95, p99)
- Error rate per data_type
- Cache hit/miss ratio per data_type

**Adapter Metrics:**
- Fetch success/failure rate per adapter
- Fetch latency per adapter
- Rate limit hits per adapter
- Fallback activation frequency

**Cache Metrics:**
- Cache hit rate by backend (Redis/Postgres/Memory)
- Cache memory usage
- Cache eviction rate
- Cache key distribution

**Agent Metrics:**
- Tool execution count per data_type
- Tool success rate
- Agent response quality (via feedback)
- Tool discovery patterns

### Logging Strategy

**Query Logging:**
- Log level INFO: Successful queries with latency
- Log level WARNING: Cache misses with reason
- Log level ERROR: Query failures with stack trace
- Include: data_type, params, source, latency, cache_hit

**Adapter Logging:**
- Log level DEBUG: Adapter selection logic
- Log level INFO: Fetch started/completed
- Log level WARNING: Fallback triggered
- Log level ERROR: All sources failed
- Include: adapter_name, params, latency, error_details

**Cache Logging:**
- Log level DEBUG: Cache operations
- Log level INFO: Cache statistics (hourly)
- Log level WARNING: High eviction rate
- Include: backend, operation, key, size, ttl

**Agent Logging:**
- Log level INFO: Tool executions
- Log level ERROR: Tool failures
- Include: tool_name, params, execution_time, success

### Alerting Rules

**Critical Alerts:**
- Cache hit rate drops below 50% for OHLCV
- Any adapter has >50% failure rate
- Query latency p99 exceeds 5s
- Redis connection failures

**Warning Alerts:**
- Cache hit rate drops below 70%
- Adapter failure rate exceeds 20%
- Query latency p95 exceeds 2s
- High cache eviction rate

**Info Alerts:**
- New data source added (auto-discovered)
- Catalog validation failures
- Rate limit approaching threshold
- Unusual query patterns

---

## Migration Checklist

### Pre-Migration

- [ ] WebSocket market data service running stably (already done)
- [ ] Redis contains OHLCV data for active symbols (already populated)
- [ ] All tests passing for Phase 1 implementation
- [ ] Feature flag `USE_UNIVERSAL_DATA` implemented
- [ ] Rollback procedure documented and tested

### Phase 1 Migration (OHLCV)

- [ ] Deploy MarketIntelligence framework to production
- [ ] Enable feature flag for 1 test bot
- [ ] Monitor for 24 hours (extractions, decisions, trades)
- [ ] Compare database records (before vs after)
- [ ] Verify cache hit rate >90%
- [ ] Enable for 5 additional bots
- [ ] Monitor for 24 hours
- [ ] Enable for all bots
- [ ] Monitor for 48 hours
- [ ] Remove feature flag, make default
- [ ] Archive HummingbotDataClient code

### Phase 2 Migration (New Sources)

- [ ] Add sentiment data sources
- [ ] Add news data sources
- [ ] Add on-chain data sources
- [ ] Each source: catalog → adapter → test → validate
- [ ] Update DecisionEngine to query additional context (optional)

### Phase 3 Migration (Agent SDK)

- [ ] Implement tool generation
- [ ] Deploy MCP server
- [ ] Test with Claude Desktop
- [ ] Document agent usage patterns
- [ ] Create example agent workflows

### Phase 4 Migration (Scale)

- [ ] Add fundamentals sources
- [ ] Add macro/economic sources
- [ ] Add options/derivatives sources
- [ ] Optimize performance based on metrics
- [ ] Scale infrastructure as needed

### Post-Migration Validation

- [ ] All original features working
- [ ] No regression in decision quality
- [ ] Performance improved (faster extractions)
- [ ] Agent tools available and functional
- [ ] Documentation complete
- [ ] Team trained on new system

---

## Success Criteria

### Phase 1 Success (OHLCV)

**Functional:**
- ✅ 100% of extractions succeed using MarketIntelligence
- ✅ Database records identical to baseline
- ✅ DecisionEngine receives expected format
- ✅ Zero breaking changes in API responses

**Performance:**
- ✅ Extraction latency reduced 3x (from 2-3s to <1s)
- ✅ Cache hit rate >90% for active symbols
- ✅ API timeout errors eliminated
- ✅ WebSocket integration stable

**Quality:**
- ✅ All tests passing
- ✅ No errors in production logs
- ✅ Monitoring metrics green
- ✅ Rollback capability verified

### Phase 2 Success (New Sources)

**Functional:**
- ✅ 5+ new data sources operational
- ✅ Sentiment data available for decision context
- ✅ News data available for decision context
- ✅ On-chain data available for decision context

**Integration:**
- ✅ Catalog-driven approach validated
- ✅ Adding sources takes <4 hours
- ✅ Auto-discovery working
- ✅ Caching effective per source

### Phase 3 Success (Agent SDK)

**Functional:**
- ✅ All data sources available as agent tools
- ✅ MCP server operational
- ✅ Tools working in Claude Desktop
- ✅ LLM-formatted responses quality validated

**Developer Experience:**
- ✅ Tools auto-generated from catalogs
- ✅ Natural language responses useful
- ✅ Agent can query 156 data types
- ✅ Tool documentation comprehensive

### Phase 4 Success (Scale)

**Coverage:**
- ✅ 50+ data sources operational
- ✅ All major categories represented
- ✅ Path to 156 sources clear

**Performance:**
- ✅ System handles 1000+ queries/minute
- ✅ Response times remain <1s average
- ✅ Cache efficiency maintained
- ✅ Infrastructure costs reasonable

---

## Future Enhancements

### Advanced Features

**Multi-Source Aggregation:**
- Combine sentiment from Twitter + Reddit + Telegram
- Aggregate news from multiple outlets with deduplication
- Cross-validate on-chain metrics from multiple providers
- Consensus scoring across sources

**Predictive Caching:**
- Pre-fetch data based on trading patterns
- Anticipate queries before requested
- Smart cache warming for scheduled executions
- Learning-based cache TTL adjustment

**Data Quality Scoring:**
- Track adapter reliability over time
- Confidence scoring based on historical accuracy
- Source ranking based on performance
- Automatic source switching on degradation

**Query Optimization:**
- Batch similar queries
- Parallel source fetching
- Response streaming for large datasets
- Query result caching at gateway level

### Agent Enhancements

**Context-Aware Tools:**
- Tools suggest related queries
- Auto-chain dependent data (e.g., OHLCV → sentiment for same symbol)
- Smart parameter defaults from context
- Query history for better suggestions

**Natural Language Queries:**
- Accept free-text queries
- Parse to structured params using LLM
- Support conversational follow-ups
- Multi-step query planning

**Agent Memory:**
- Remember previous queries per session
- Learn agent preferences over time
- Optimize tool selection based on success
- Personalized data source prioritization

### Platform Features

**Data Marketplace:**
- Community-contributed adapters
- Premium data source integrations
- Adapter marketplace with ratings
- Revenue sharing for adapter authors

**Real-Time Streaming:**
- WebSocket API for live data
- Subscribe to data type updates
- Push notifications on signals
- Stream aggregation pipelines

**Advanced Analytics:**
- Time-series analysis across sources
- Correlation detection
- Anomaly detection
- Pattern recognition

---

## Conclusion

The Universal Data Layer represents a foundational shift in how ggbots accesses market intelligence. By moving from specialized clients to a catalog-driven gateway, we enable:

1. **Immediate Value:** OHLCV replacement with 3x performance improvement
2. **Rapid Expansion:** 156 data sources in 8 weeks (vs 2+ years manually)
3. **Agent-First Design:** AI agents as first-class consumers
4. **Zero Breaking Changes:** Backward compatible migration path
5. **Developer Velocity:** Add sources in hours, not days

**Next Step:** Begin Phase 1 implementation with core framework and OHLCV migration.

**Timeline:**
- Week 1: OHLCV replacement live in production
- Week 2-3: 5 additional sources operational
- Week 4: Agent SDK integration complete
- Week 5-8: Scale to 50+ sources

**Success Metrics:**
- Extraction latency: <1s (currently 2-3s)
- Cache hit rate: >90% (currently N/A)
- Data sources: 50+ (currently 1)
- Agent tools: Auto-generated (currently 0)

The foundation is solid. The architecture is elegant. The path forward is clear.

**Let's build the most comprehensive market intelligence platform for AI-powered trading.**
