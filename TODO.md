# TODO.md - ggbots Implementation Plan

## 🏆 **URGENT - AsterDEX Live Trading Integration** [ASTER.md]

**Timeline**: 7-8 days - Win $50k ASTER token prize in Vibe Trading Competition
**Status**: Phase 1 Complete - Live Trading Operational ✅

**See**: [DOCS/ASTER.md](DOCS/ASTER.md) for complete technical architecture and design

**Competition Context**: AsterDEX is running a trading competition with $50,000 in ASTER tokens for highest volume trader. ggbots' autonomous 24/7 AI trading is perfectly positioned to win.

**Integration Approach**: Follow proven Symphony.io pattern with minimal code changes:
- Same orchestrator routing (`trading_mode: 'aster'`)
- Same trade intent interface
- Same credential management (Vault)
- Same frontend display logic

### **Phase 1: Service Foundation** (Days 1-2)

**Goal**: Core trading execution working

- [x] **AsterDEX Service Implementation** (`trading/live/aster_service_v3.py`)
  - [x] Create `AsterDEXV3LiveTradingService` class with Symphony-style interface
  - [x] Implement Web3 ECDSA signature generation (v3 API)
  - [x] Implement `execute_trade_intent()` method
  - [x] Add symbol validation using standardizer
  - [x] Add idempotency protection (decision_id uniqueness)
  - [x] Test live trade execution (BTC-USDT: OPEN + CLOSE successful)
  - [ ] Add SL/TP conditional order creation (STOP_MARKET, TAKE_PROFIT_MARKET)
  - [ ] Add leverage management (currently defaults to 10x)

- [x] **Symbol Standardization** (`core/symbols/standardizer.py`)
  - [x] Add `to_aster()` method (BTC-USDT → BTCUSDT)
  - [x] Add `from_aster()` method (BTCUSDT → BTC-USDT)
  - [x] Add `is_aster_compatible()` method
  - [x] Cross-reference 33 compatible symbols from 142 total

- [ ] **Vault Integration** (`core/auth/vault_utils.py`)
  - [ ] Add `get_aster_credential(user_id)` method
  - [ ] Add `store_aster_credential(user_id, api_key, api_secret)` method
  - [ ] Add `delete_aster_credential(user_id)` method
  - [ ] Test credential encryption/decryption

- [x] **Database Schema** (`database/migrations/`)
  - [x] Extend `live_trades` table with `provider` field (VARCHAR 20, DEFAULT 'symphony')
  - [x] Backfill existing trades: `UPDATE live_trades SET provider = 'symphony'`
  - [x] Add `stop_loss_order_id` and `take_profit_order_id` fields (nullable)
  - [x] Add provider-aware indexes (`idx_live_trades_provider`, `idx_live_trades_provider_open`)
  - [x] **Add `symbol` column** (VARCHAR 20) for position-trade matching (2025-11-04)
  - [x] **Add `idx_live_trades_symbol` index** on (config_id, symbol, closed_at) (2025-11-04)
  - [x] Execute migration in Supabase
  - [ ] Fix `decision_id` foreign key (make nullable for test trades)

### **Phase 2: Position Management** (Days 3-4) ✅

**Goal**: Query positions, close trades, get account status

- [x] **Query Endpoints Implementation**
  - [x] Implement `_get_position_risk()` (GET /fapi/v3/positionRisk)
  - [x] Implement `_get_account_balance()` (GET /fapi/v3/balance)
  - [x] Add response transformation to standard format
  - [x] Test with live credentials

- [x] **Close Position Functionality**
  - [x] Implement market close via `_place_market_order()`
  - [x] Test position close (BTC-USDT closed successfully)
  - [x] **Fixed batch_id matching** - Added `symbol` column to `live_trades`, position matching now works (2025-11-04)
  - [ ] Add SL/TP order cancellation before close
  - [ ] Update `live_trades.closed_at` timestamp via `close_position(batch_id, user_id)`

- [ ] **Error Handling**
  - [ ] Add rate limit tracking and backoff logic
  - [ ] Implement circuit breaker at 80% rate limit
  - [ ] Add retry logic with exponential backoff
  - [ ] Handle common API errors gracefully (-1121, -2010, etc.)

### **Phase 3: Orchestrator Integration** (Day 5) ✅

**Goal**: Connect AsterDEX service to main trading pipeline

- [x] **Orchestrator Changes** (`ggbot.py`)
  - [x] Import `AsterDEXV3LiveTradingService`
  - [x] Initialize `self.aster_trading` in `__init__()`
  - [x] Add `'aster'` routing to `_run_trading_v2()`
  - [x] Test routing with live service
  - [x] Verify no impact on existing paper/Symphony flows

- [x] **Dynamic Position Sizing** (`trading/live/aster_service_v3.py`)
  - [x] Implement `_calculate_weight()` with account balance query
  - [x] Respect bot config (ACCOUNT_PERCENTAGE, CONFIDENCE_BASED, FIXED_USD)
  - [x] Add safety caps (95% of available balance)
  - [x] Validate minimum quantities (0.001 BTC)
  - [x] Test with $9.84 account balance

- [x] **Agent Position Size Overrides** (Full Stack Implementation)
  - [x] Add override support to all trading services (Aster, Paper, Symphony)
  - [x] Create `/api/v2/agent/execute-trade` endpoint with override params
  - [x] Update agent API client to pass `size_usd` and `leverage` params
  - [x] Wire up agent MCP tool with override parameters
  - [x] Add comprehensive validation and safety checks

- [ ] **Configuration Support** (`core/config/models.py`)
  - [x] Add `'aster'` to trading_mode options (already supports via string field)
  - [ ] Add `aster_account_id` optional field
  - [ ] Update BotConfigV2 validation for aster mode
  - [ ] Test config creation/loading

- [ ] **API Endpoints** (`ggbot.py` or `api/aster.py`)
  - [x] Add `POST /api/v2/agent/execute-trade` (agent trade execution with overrides)
  - [ ] Add `POST /api/v2/aster/setup` (store credentials)
  - [ ] Add `GET /api/v2/aster/status` (check connection)
  - [ ] Add `POST /api/v2/aster/disconnect` (remove credentials)
  - [ ] Add `GET /api/v2/positions/aster/{config_id}` (query positions)
  - [ ] Add `POST /api/v2/positions/aster/{order_id}/close` (close position)
  - [ ] Add `GET /api/v2/account/aster/{config_id}` (account metrics)
  - [ ] Add `POST /api/v2/config/duplicate-as-aster` (duplicate bot)
  - [ ] Test all endpoints with Postman/curl

### **Phase 4: Frontend Integration** (Day 6)

**Goal**: UI for credential setup and aster mode selection

- [ ] **Settings Modal** (`frontend/app/forge/components/settings/`)
  - [ ] Add "AsterDEX" tab to Settings modal
  - [ ] Add API Key + Secret input fields
  - [ ] Add "Test Connection" button (calls /api/v2/aster/status)
  - [ ] Add "Disconnect" button with confirmation
  - [ ] Show connection status indicator

- [ ] **Trading Mode Selection** (`frontend/app/forge/components/configure/`)
  - [ ] Add "AsterDEX Live" option to trading mode selector
  - [ ] Show AsterDEX badge in bot rail (orange/purple color)
  - [ ] Disable AsterDEX option if credentials not configured
  - [ ] Add tooltip explaining AsterDEX mode

- [ ] **Dashboard Display** (`frontend/app/forge/components/monitor/`)
  - [ ] Add SSE enrichment for `trading_mode === 'aster'`
  - [ ] Route close button to `/api/v2/positions/aster/`
  - [ ] Show "Track on AsterDEX" for balance (like Symphony)
  - [ ] Add AsterDEX icon/badge to active positions

- [ ] **Duplicate Bot Flow**
  - [ ] Add "Deploy AsterDEX Version" button (like Symphony)
  - [ ] Show confirmation modal with warning
  - [ ] Create new bot with `trading_mode='aster'`
  - [ ] Navigate to new bot config

### **Phase 5: Testing & Validation** (Day 7)

**Goal**: Production-ready, all tests passing

- [ ] **Unit Tests**
  - [ ] Test signature generation with known examples
  - [ ] Test symbol conversion (all 141 pairs)
  - [ ] Test order parameter formatting
  - [ ] Test error handling logic
  - [ ] All unit tests passing (pytest)

- [ ] **Integration Tests**
  - [ ] Test API connection (ping, time, exchangeInfo)
  - [ ] Test authentication with testnet credentials
  - [ ] Test account balance query
  - [ ] Test order placement on testnet
  - [ ] Test position query on testnet
  - [ ] Test order cancellation on testnet

- [ ] **End-to-End Tests**
  - [ ] Create aster bot via frontend
  - [ ] Setup credentials via Settings modal
  - [ ] Execute 1 manual trade cycle
  - [ ] Verify order on AsterDEX platform
  - [ ] Close position via dashboard
  - [ ] Verify audit trail in aster_trades table
  - [ ] Run autonomous bot for 1 hour
  - [ ] Verify all trades logged correctly

- [ ] **Production Validation**
  - [ ] Test with real credentials (small amounts)
  - [ ] Execute 10 trades successfully
  - [ ] Verify SL/TP conditional orders work
  - [ ] Test error scenarios (insufficient balance, invalid symbol)
  - [ ] Monitor rate limiting (no 429 errors)
  - [ ] Verify no impact on paper/Symphony trading

### **Phase 6: Competition Launch** (Day 8+)

**Goal**: Compete for $50k prize

- [ ] **Competition Strategy**
  - [ ] Create 5-10 aster bots (multi-symbol)
  - [ ] Configure for high-frequency trading (5m interval)
  - [ ] Set moderate leverage (3-5x)
  - [ ] Enable tight SL/TP for quick exits
  - [ ] Activate all bots simultaneously

- [ ] **Monitoring & Optimization**
  - [ ] Monitor total volume daily
  - [ ] Track competition leaderboard ranking
  - [ ] Optimize strategies based on performance
  - [ ] Adjust position sizes for max volume
  - [ ] Monitor balance stability (>80% starting capital)

- [ ] **Risk Management**
  - [ ] Set max position size to 1% of balance per bot
  - [ ] Monitor total exposure across all bots
  - [ ] Set balance alert at -20% drawdown
  - [ ] Emergency stop all bots if needed
  - [ ] Daily balance reconciliation

### **Success Metrics**

- ✅ Zero authentication errors in production
- ✅ <1% failed trade rate
- ✅ Sub-2s trade execution latency
- ✅ 100% audit trail accuracy
- ✅ Top 10 competition ranking (volume)
- ✅ $50k prize won (stretch goal)

**Next Steps**: Start with Phase 1 - Service Foundation (Days 1-2)

### **Phase 7: Post-Competition Cleanup** (After Competition)

**Goal**: Update Symphony service for consistency with provider pattern

- [ ] **Symphony Service Update** (`trading/live/symphony_service.py`)
  - [ ] Update `_save_trade_record()` to include `provider='symphony'` in INSERT
  - [ ] Update trade queries to use `WHERE provider='symphony'`
  - [ ] Test Symphony trades still save/query correctly
  - [ ] Verify backward compatibility with existing trades
  - [ ] Update any hardcoded table queries in `get_open_positions()`

**Note**: This is non-urgent cleanup. Symphony works fine without this change due to DEFAULT value, but explicit is better than implicit.

---

## 📊 **Activity Timeline Integration** ✅ COMPLETE (2025-11-06)

**Status**: Production-ready activity logging for all bot types (agents, scheduled, signal validation)
**See**: [DOCS/todo/ACTIVITY_TIMELINE.md](DOCS/todo/ACTIVITY_TIMELINE.md) for full implementation details

**Completed Features**:
- ✅ Activities table with RLS, indexes, priority-based grouping
- ✅ Activity logger helper with auto-logging from 11 agent MCP tools
- ✅ 3 API endpoints (activities, balance-series, metadata)
- ✅ Aster P&L integration (combines paper + live trades)
- ✅ Frontend Activity Timeline with real data, 10s polling
- ✅ UI polish (trade_win/loss icons, live status, responsive layout)

**Optional Future Enhancements**:
- Scheduled bot activity logging (orchestrator integration)
- Trade lifecycle linking with click highlighting
- "View Configuration" modal for competition
- Active Positions section at bottom of timeline

---

## 🤖 **HIGH PRIORITY - Autonomous Trading Agent** [AGENT.md] ✅ OPERATIONAL

**Timeline**: Phases 1-4c Complete (Production Ready) | Phase 5: Production Polish In Progress

**See**: [agent/README.md](agent/README.md) for usage guide | [DOCS/todo/AGENT.md](DOCS/todo/AGENT.md) for architecture

**Vision**: Transform ggbots from bot platform (scheduled execution) to agent infrastructure (autonomous AI decision-making)

**Status**: ✅ Production - 12 tools operational, 2 agents running live, frontend integration complete

**Completed Features**:
- ✅ **12 MCP Tools**: Market data, price checks, trading, positions, account, orders, strategy, observations, timing
- ✅ **Two-mode system**: Strategy Definition (interactive chat) → Autonomous (24/7 trading)
- ✅ **Frontend Integration**: AgentConfigurator with real-time Redis polling, bot creation flow
- ✅ **Trading Support**: Paper (142 symbols) + Aster (33 symbols) fully operational
- ✅ **Activity Logging**: All agent actions logged to timeline for monitoring
- ✅ **Production Deployment**: PM2 process management, Redis queues, service auth

### **Phases 1-4c: Foundation & Frontend** ✅ COMPLETE (2025-11-03)

**Completed Work**:
- ✅ **Phase 1**: Database schema (`decisions.created_by`, `trade_observations` table), `.venv-agent` setup
- ✅ **Phase 2**: 12 MCP tools implemented, category-based market data, service client with retries
- ✅ **Phase 3**: Agent runner (strategy_definition + autonomous modes), Redis queues, PM2 lifecycle
- ✅ **Phase 4a**: Frontend integration (AgentConfigurator, bot creation modal, Redis polling)
- ✅ **Phase 4c**: Autonomous launch flow (save_strategy_and_exit tool, activation routing)

### **Symphony Live Trading Integration** - 🔜 PENDING API FIX

**Blocker**: Symphony `/agent/all-positions` endpoint returns 404 (documented but not implemented)

**What's Needed**: Symphony team must fix/implement the following API endpoint:
```
GET https://api.symphony.io/agent/all-positions?userAddress={WALLET_ADDRESS}
Returns: accountSummary with totalEquity, availableBalance, marginUsed
```

**Current State**:
- ✅ `SymphonyLiveTradingService` exists and works (uses `/agent/positions`, `/agent/batches`)
- ❌ Balance data NOT available (Symphony API limitation)
- ✅ Agent endpoints support Paper + Aster modes
- 🔜 Symphony branches ready to add once API is fixed

**Implementation Plan** (Once API Fixed):
1. Add `get_account_summary()` method to Symphony service (~30 mins)
2. Add Symphony branches to 5 agent endpoints (~45 mins)
3. Update system prompt with Symphony capabilities (~15 mins)
4. Test end-to-end with real Symphony credentials (~1 hour)

**See**: [agent/README.md](agent/README.md) "Symphony Integration Steps" section for complete implementation guide

### **Phase 5: Production Deployment** (1-2 days) - 🟡 **IN PROGRESS**

**Goal**: Deploy, monitor, document

- [x] **Deployment** - Core infrastructure operational
  - [x] Agent code deployed to production
  - [x] PM2 service working (agents spawn via `/api/v2/agent/{id}/start`)
  - [x] Environment variables configured (.venv-agent, ANTHROPIC_API_KEY)
  - [x] Redis message queues operational (messages, responses, history)
  - [x] Agent startup/shutdown/restart tested and working
  - [ ] Lifecycle management improvements (cleanup on delete, restart policies)

- [ ] **Monitoring**
  - [ ] Agent-specific logging (mode, tokens, strategy version)
  - [ ] Track tool call frequency
  - [ ] Monitor compaction events
  - [ ] Alert on agent failures/errors
  - [ ] Track strategy performance by mode (guided vs experimental)

- [x] **Documentation**
  - [x] Agent usage guide (`agent/README.md` - complete with Symphony integration roadmap)
  - [ ] Example strategies (conservative, aggressive, experimental)
  - [ ] Advanced troubleshooting guide
  - [ ] API documentation for agent endpoints (partially in ACTIVE.md)

### **Future Enhancements** (Post-Launch)

- [ ] **Multi-Agent Support**
  - [ ] Multiple agents per user
  - [ ] Agent coordination and position awareness
  - [ ] Portfolio-level risk management

- [ ] **Enhanced Learning**
  - [ ] Automatic learning promotion (agent_memory → config_data)
  - [ ] Learning importance auto-scoring
  - [ ] Strategy template library from successful experimental agents

- [ ] **Advanced Interaction**
  - [ ] Mid-trade explanations ("Why did you enter here?")
  - [ ] Strategy refinement via conversation while autonomous
  - [ ] Real-time reasoning display in dashboard

- [ ] **Model Flexibility**
  - [ ] Per-agent model selection (Haiku for budget, Sonnet for premium, Opus for specialized)
  - [ ] Cost tracking per agent
  - [ ] Model performance comparison dashboard

---

## 🧠 **HIGH PRIORITY - Market Intelligence Expansion**

**Timeline**: 4-6 weeks - Add contextual data to improve AI decision quality

**See**: [DOCS/MARKET_INTELLIGENCE_ROADMAP.md](DOCS/MARKET_INTELLIGENCE_ROADMAP.md) for complete roadmap

**Current State**:
- ✅ Infrastructure complete (data_sources/data_points tables, UI, API)
- ✅ 7 categories finalized (Technical Analysis, Trading Signals, On-Chain, Derivatives & Leverage, Sentiment & Social, News & Regulatory, Macro Economics)
- ✅ 7/7 data sources populated (Technical Analysis: 21, Trading Signals: 1, Derivatives & Leverage: 2, Macro: 4, On-Chain: 2, Sentiment: 1, News: 1 = **32 total**)
- ✅ Intelligence Orchestrator **PRODUCTION READY** (`market_intelligence/orchestrator.py`) - parallel query execution, custom TTL per data point
- ✅ **GrokAgenticAdapter PRODUCTION DEPLOYED** - ONE universal adapter handles 8 data sources via XAI's agentic API (web search, X search, code execution)
- ✅ 8 new Grok data points **LIVE IN PRODUCTION** (VIX, DXY, CPI, NFP, BTC TVL, whale activity, Twitter sentiment, crypto news) - all FREE tier
- ✅ Decision engine integration complete (formatting methods, prompt updates, real bot tested)
- ✅ Tested production: All 8 data points working, parallel execution ~30s, comprehensive AI reasoning
- ✅ **PHASE 1 COMPLETE** - $195/month platform cost ($0.76/user/month at 257 users, $0.20/user at 1000 users)

### **Phase 1: Grok-Powered Intelligence** (COMPLETE - Ready for Production) - $160-240/month platform cost

**Goal**: Add 7 contextual data points via 3 acquisition methods (Direct API, Grok Search, Browser-Use)

**New Data Source: Derivatives & Leverage** (2 points) - ✅ COMPLETE
- [x] Create `BinanceFundingAdapter` for perpetual funding rates
- [x] Create catalog YAML: `funding_rate.yaml`
- [x] Seed database: INSERT 1 data_source + 2 data_points (BTC, ETH)
- [x] Test: Fetch BTC/ETH funding rates from Binance API (tested live: BTC 0.0026%, ETH 0.0063%)

**New Data Sources via GrokAgenticAdapter** (8 points) - ✅ **PRODUCTION DEPLOYED**
- [x] Create `GrokAgenticAdapter` - universal adapter with 8 prompt templates (VIX, DXY, CPI, NFP, Twitter, news, TVL, whales)
- [x] Create catalog YAML: `grok_agentic.yaml` with query_type parameter support
- [x] Update `catalog_mapping.py` with 8 new entries + custom cache TTL per data point (10min to 24hrs)
- [x] Test all 8 query types - ✅ SUCCESS (total cost $0.11, all queries working)
- [x] Install xai-sdk (v1.3.1) - supports agentic tool calling with streaming
- [x] **Seed database**: INSERT 4 data_sources + 8 data_points (all FREE tier)
- [x] Fix gateway adapter routing for `agentic` category
- [x] Fix ggShot adapter data source name (`signals_group_chats` → `trading_signals`)
- [x] Fix cache key KeyError (missing `name` in format context)
- [x] Fix Redis protobuf serialization (citations + tool_calls conversion)

**Intelligence Orchestrator Implementation** - ✅ **PRODUCTION DEPLOYED**
- [x] Build `IntelligenceOrchestrator` class (market_intelligence/orchestrator.py) - 260 lines, config-driven routing
- [x] Implement config parsing (read selected_data_sources from config) - `_parse_config_sources()`
- [x] Create data_point → catalog mapping logic (catalog_mapping.py) - hardcoded dict, 12 entries (2 funding + 8 Grok + 2 signals)
- [x] Add funding rates to orchestrator routing - ✅ Working via mapping
- [x] Add `data_points_override` parameter for agent dynamic queries
- [x] Implement parallel query execution - ✅ 5.3x speedup (160s → 30s)
- [x] Update `ggbot.py` to call orchestrator - ✅ Hybrid approach (technicals via old way, market intel via orchestrator)
- [x] Write comprehensive tests - 16/16 unit tests passing (tests/test_orchestrator.py)
- [ ] Migrate ggShot to use orchestrator (FUTURE - keep hardcoded for now, low risk approach)

**Decision Engine Integration** - ✅ **PRODUCTION DEPLOYED**
- [x] Add market intelligence formatting methods to decision engine - 6 methods (_format_derivatives_data, _format_macro_data, etc.)
- [x] Update prompts to include market intelligence section - opportunity_analysis.py updated
- [x] Add `market_intelligence` parameter to make_decision() - ✅ Flows from extraction → decision
- [x] Test end-to-end with real bot - ✅ Comprehensive AI reasoning with all 8 data points

**Expected Impact**: +30-40% trading edge (avoid overleveraged setups, macro-aware decisions)

---

### **Phase 2: Premium On-Chain** (Week 3-4) - $100-500/month

- [ ] Whale wallet tracking (Nansen via Browser-Use OR Arkham API)
- [ ] Exchange reserves & flows (Glassnode/CryptoQuant)
- [ ] Active addresses & network health (on-chain explorers)
- [ ] Token unlocks calendar (TokenUnlocks.app)
- [ ] Dev activity metrics (GitHub API)

---

### **Phase 3: Sentiment & Social** (Week 5-6) - $100-500/month

- [ ] Twitter/X sentiment analysis (Twitter API + NLP)
- [ ] Reddit crypto sentiment (Reddit API + NLP)
- [ ] Narrative velocity tracking (topic modeling)

---

### **Phase 4: Advanced Intelligence** (Week 7-10) - $200-1000/month

- [ ] Order book liquidity heatmaps (Coinalyze)
- [ ] CEX/DEX market share tracking
- [ ] Institutional flows (BTC ETF data)
- [ ] App/exchange traffic (SimilarWeb)
- [ ] L2 gas fees & bridge flows

---

## 🎨 **HIGH PRIORITY - User Experience Polish**

- [ ] **Improve Status Messaging**
  - [ ] Change 'next run...' to 'waiting for next candle close...' in frontend
  - [ ] Update countdown messages to be more user-friendly
  - [ ] Add explanatory tooltips for bot status states
  - [ ] Improve activation/deactivation feedback messages

- [ ] **Optional Market Data Display**
  - [ ] Consider adding expandable market analysis panel to positions
  - [ ] Implement "Show Analysis" toggle for power users
  - [ ] Add hover tooltips showing key indicators that influenced decisions
  - [ ] Design market context drawer/modal for detailed technical analysis

- [ ] **Trade History Modal**
  - [ ] Add clickable "Total Trades" metric in MetricsBar
  - [ ] Implement full-screen modal with minimalist design
  - [ ] Display last 50 closed trades: Symbol, Side, P&L, Close Reason, Timestamp
  - [ ] Color-code by win/loss for quick scanning
  - [ ] Show summary stats at top: win count, loss count, win rate
  - [ ] Optional: Click individual trade to expand details (entry/exit prices, duration, confidence)

### **Phase 3: Agent SDK Integration** (Week 3)

- [ ] **Tool Generation**
  - [ ] Implement ToolGenerator (auto-generate from catalogs)
  - [ ] Create tool registry for Agent SDK
  - [ ] Add tool discovery endpoint

- [ ] **MCP Server**
  - [ ] Implement MCP server with universal query tool
  - [ ] Add data type discovery
  - [ ] Test with Claude Desktop

- [ ] **Response Formatting Enhancement**
  - [ ] Enhance LLM format mode with better templates
  - [ ] Add insight extraction logic
  - [ ] Create default templates for all data types

### **Phase 4: Scale Data Sources** (Weeks 4-8)

- [ ] **Sentiment Analysis** (Week 4)
  - [ ] Twitter/X sentiment catalog + adapter
  - [ ] Reddit sentiment catalog + adapter
  - [ ] LunarCrush aggregated sentiment catalog + adapter

- [ ] **News & Events** (Week 5)
  - [ ] Crypto news aggregator catalog + adapter
  - [ ] Google News API catalog + adapter

- [ ] **On-Chain Data** (Week 5)
  - [ ] Glassnode (exchange flows) catalog + adapter
  - [ ] Etherscan (blockchain metrics) catalog + adapter

- [ ] **Fundamentals** (Week 6)
  - [ ] SEC EDGAR filings catalog + adapter
  - [ ] Alpha Vantage fundamentals catalog + adapter
  - [ ] Financial Modeling Prep catalog + adapter

- [ ] **Macro & Economic** (Week 7)
  - [ ] FRED (Federal Reserve data) catalog + adapter
  - [ ] BLS (Bureau of Labor Statistics) catalog + adapter
  - [ ] Treasury data catalog + adapter

- [ ] **Options & Derivatives** (Week 8)
  - [ ] Options flow aggregators catalog + adapter
  - [ ] Unusual options activity catalog + adapter
  - [ ] Put/call ratios catalog + adapter

### **Benefits Delivered**

- **Immediate**: 3x faster extractions (WebSocket cache vs REST polling)
- **Scalability**: Add 150+ data sources in weeks instead of years
- **Agent-Ready**: AI agents as first-class consumers via auto-generated tools
- **Zero Breaking Changes**: Backward compatible migration with feature flag

## 🔧 **MEDIUM PRIORITY - Paper Trading Engine Modernization** ✅ **COMPLETE**

**Status**: Migration from Hummingbot to WebSocket live prices completed October 2025 (see CHANGELOG.md).

**Implementation Details**:
- Paper trading now uses `LivePriceService` (WebSocket-first, REST fallback)
- Sub-millisecond Redis access for 100 WebSocket-cached symbols
- REST API fallback with 5s caching for remaining 42 symbols
- All 142 symbols supported with intelligent tiering
- Hummingbot archived to `archive/hummingbot/`

---

## 🔧 **MEDIUM - Trading System Completeness**

**Timeline**: 2-3 days - Core trading functionality verification and enhancement

- [ ] **Stop Loss / Take Profit Verification**
  - [ ] Check if SL/TP values are being read from configuration properly
  - [ ] Verify trade monitoring triggers TP/SL execution automatically
  - [ ] Test automated position closing at profit/loss targets
  - [ ] Ensure SL/TP levels display correctly in positions table

- [ ] **Risk Management Enforcement**
  - [ ] Validate risk management parameters are enforced
  - [ ] Implement open position limits per user/bot configuration

- [ ] **User Communication (Account Reset)**
  - [ ] Email encouraging users to try reset feature for clean V2.0 accounting
  - [ ] Optional: Add banner promoting account reset for fresh start with leverage fixes
  - [ ] Monitor user feedback channels (Telegram community, support tickets)

## 🔧 **HEDIUM PRIORITY - User Settings & API Key Management**

**Timeline**: 1-2 days - Critical for user onboarding and self-service

- [ ] **Complete User Settings Page**
  - [ ] Finish API key management interface for LLM credentials
  - [ ] Add secure credential storage using Supabase Vault
  - [ ] Implement credential validation and testing functionality
  - [ ] Add interface for managing multiple API keys per provider

- [ ] **LLM Provider Management**
  - [ ] Support OpenAI, DeepSeek, Anwhythropic, and XAI credential management
  - [ ] Add credential naming and organization features
  - [ ] Implement credential usage tracking and validation
  - [ ] Test credential encryption/decryption flow

- [ ] **Subscription & Profile Management**
  - [ ] Implement downgrade workflow (cancellation flow)
  - [ ] Implement user profile settings (Telegram integration, preferences)
  - [ ] Add account settings and preferences management


## 🔧 **MEDIUM PRIORITY - System Robustness**

**Timeline**: 2-3 days - Code quality, error handling, and reliability

- [ ] **Database Schema Optimization**
  - [ ] Remove unused `market_data` column from decisions table schema
  - [ ] Implement market data parsing utilities for future analysis needs
  - [ ] Add database indexes for performance optimization
  - [ ] Clean up any remaining schema inconsistencies

- [ ] **Error Handling & Resilience**
  - [ ] Add comprehensive error boundaries to frontend components
  - [ ] Implement graceful API failure handling with retries
  - [ ] Add circuit breakers for external service failures
  - [ ] Improve logging and error taxonomy (replace broad exceptions)

- [ ] **Node.js & Dependencies**
  - [ ] Plan upgrade from Node.js 18 to Node.js 20+ (removes Supabase warnings)
  - [ ] Update dependencies to latest compatible versions
  - [ ] Test compatibility after Node upgrade
  - [ ] Update deployment configurations for new Node version

- [ ] **Code Quality Improvements**
  - [ ] Run `ruff` + `black` for Python code formatting
  - [ ] Remove unused imports and clean up import hygiene
  - [ ] Add proper TypeScript types for signal_data structures
  - [ ] Implement defensive action mapping with unknown value logging

## 📚 **MEDIUM-LOW PRIORITY - Documentation Completeness**

**Timeline**: 3-4 days - Complete module documentation coverage and accuracy

**Current State**: 7/10 major modules have excellent READMEs (extraction/v2, market_intelligence, decision, trading, database, frontend, ggshot)

### **Phase 1: Missing Module READMEs** (2 days)
- [ ] **Create agent/README.md**
  - [ ] Document MCP server architecture and tools
  - [ ] Explain conversation mode vs autonomous mode
  - [ ] Detail agent-orchestrator communication (Redis queues, HTTP API)
  - [ ] Include tool documentation and examples
  - [ ] Document service authentication pattern
  - [ ] Add development status: "Phase 3 - Foundation Complete, Frontend In Progress"

- [ ] **Create api/README.md** (Optional - Low Priority)
  - [ ] Document all agent-specific endpoints (9 total)
  - [ ] Include authentication patterns
  - [ ] Add request/response examples
  - [ ] Note: Most other endpoints documented in ACTIVE.md

- [ ] **Create core/config/README.md** (Optional - Medium Priority)
  - [ ] Document configuration system architecture
  - [ ] Explain config_data JSONB structure
  - [ ] Detail template-based setup
  - [ ] Include config migration patterns

### **Phase 2: Existing README Review & Updates** (1-2 days)
- [ ] **Review extraction/v2/README.md** (845 lines)
  - [ ] Verify 21 preprocessors are accurate
  - [ ] Update performance metrics if changed
  - [ ] Confirm API examples still work

- [ ] **Review market_intelligence/README.md** (1154 lines)
  - [ ] Verify 32 data points match production
  - [ ] Update cost economics section ($195/month platform cost)
  - [ ] Confirm GrokAgenticAdapter documentation is current

- [ ] **Review decision/README.md** (525 lines)
  - [ ] Verify V2 template system docs
  - [ ] Update with any prompt improvements
  - [ ] Confirm webhook integration details

- [ ] **Review trading/README.md** (723 lines)
  - [ ] Verify paper trading section accurately reflects WebSocket prices (migration complete Oct 2025)
  - [ ] Verify Symphony integration docs are current
  - [ ] Update with any position monitoring improvements

- [ ] **Review database/README.md** (567 lines)
  - [ ] Add trade_observations table documentation
  - [ ] Verify paper trading tables match schema
  - [ ] Update with any recent migrations

- [ ] **Review frontend/README.md** (488 lines)
  - [ ] Verify Forge architecture documentation
  - [ ] Remove references to "new-landing" (now integrated into /landing)
  - [ ] Update subscription system details if changed

- [ ] **Review ggshot/README.md** (384 lines)
  - [ ] Verify 4-pillar framework documentation
  - [ ] Update signal processing flow if changed

### **Phase 3: Documentation Consistency** (1 day)
- [ ] **Cross-Reference Validation**
  - [ ] Ensure ACTIVE.md and module READMEs don't contradict
  - [ ] Verify README.md links to all module READMEs
  - [ ] Update DOCS/ references as needed
  - [ ] Remove any legacy/outdated information

- [ ] **Update Main README.md**
  - [ ] Add directory structure section
  - [ ] List all 7+ module READMEs with descriptions
  - [ ] Clarify agent status (Phase 3 - Foundation Complete)
  - [ ] Update frontend section (Forge = production, landing = updated)

**Benefits**:
- **Onboarding**: New developers can quickly understand each module
- **Accuracy**: Documentation matches actual production code
- **Completeness**: No major systems undocumented
- **Maintenance**: Easier to keep docs updated with clear ownership

---

## 📱 **MEDIUM PRIORITY - Mobile & Frontend Polish**

**Timeline**: 2-3 days - Complete mobile experience and component improvements

- [ ] **Mobile Responsive Design**
  - [ ] Transform three-column desktop layout to single column mobile
  - [ ] Implement 70%-width slide-in drawers for navigation
  - [ ] Create bottom tab system for drawer triggers
  - [ ] Add touch gestures for carousel navigation
  - [ ] Optimize components for narrow screen widths and touch interaction

- [ ] **Frontend Component Polish**
  - [ ] Remove any remaining hard-coded values or demo data
  - [ ] Add virtual scrolling for scenarios with >10 bots
  - [ ] Optimize performance for large bot lists
  - [ ] Polish loading states and skeleton components
  - [ ] Ensure all components handle edge cases gracefully

## 🧪 **LOW PRIORITY - Testing & Validation**

**Timeline**: 1-2 weeks - Comprehensive system validation

- [ ] **Symbol Coverage Testing**
  - [ ] Test all 142 crypto symbols for data availability
  - [ ] Verify WebSocket + REST fallback works for all supported pairs
  - [ ] Test symbol extraction success rates across all timeframes
  - [ ] Create symbol blacklist for unsupported pairs
  - [ ] Full end-to-end pipeline testing: extraction → decision → trading

- [ ] **Technical Analysis Validation**
  - [ ] Test all 21 indicator preprocessors individually
  - [ ] Validate indicator calculations against reference implementations
  - [ ] Test multi-timeframe indicator consistency and performance
  - [ ] Edge case testing (low volume, missing data, extreme price movements)

- [ ] **Load Testing & Performance**
  - [ ] Test system performance with multiple concurrent bots
  - [ ] Validate database performance under load
  - [ ] Test SSE stream performance with many connected clients
  - [ ] Cross-browser compatibility testing

- [ ] **Security & Reliability Testing**
  - [ ] Audit API endpoints for security vulnerabilities
  - [ ] Test rate limiting and authentication flows
  - [ ] Validate data isolation between users
  - [ ] Test backup and recovery procedures

---


---

## 📚 Documentation References

- **New Claude Code Instances**: `GO.md` - Start here for onboarding procedure
- **Current Status**: `ACTIVE.md` - Production system status and operational reference
- **Complete History**: `CHANGELOG.md` - All completed features, fixes, and improvements
- **Architecture**: `README.md` - Platform overview and getting started guide

