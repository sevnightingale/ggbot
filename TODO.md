# TODO.md - ggbots Implementation Plan


## 🔧 **HIGH PRIORITY - Maintenance Mode Infrastructure**

**Timeline**: 1-2 days - Complete maintenance mode system for safe production updates

**Status**: Foundation complete, needs final touches for production readiness

### **Phase 1: Core Maintenance Mode** (COMPLETE)
- [x] Update frontend layout.tsx to check auth before maintenance
- [x] Add user ID whitelist support via NEXT_PUBLIC_WHITELIST_USER_ID
- [x] Create maintenance_deactivate_all_bots.py script
- [x] Create maintenance_close_all_positions.py script
- [x] Exclude signal_validation configs from deactivation
- [x] Document maintenance procedures in DOCS/MAINTENANCE_MODE.md
- [x] Create MAINTENANCE_QUICK_START.md for fast reference

### **Phase 2: Production Testing & Validation**
- [ ] Test maintenance mode activation on Vercel
- [ ] Verify whitelisted user can bypass maintenance page
- [ ] Test bot deactivation script with real data
- [ ] Test position closure script with real positions
- [ ] Verify signal_validation configs remain active during maintenance
- [ ] Test frontend deployment while in maintenance mode
- [ ] Document maintenance runbook with screenshots

### **Phase 3: Communication & UX**
- [ ] Create maintenance notification system (optional)
- [ ] Add maintenance mode banner for admin preview
- [ ] Create user communication template for maintenance windows
- [ ] Add maintenance status page or indicator
- [ ] Plan first maintenance window for major update rollout

---

## 🤖 **HIGH PRIORITY - Autonomous Trading Agent**

**Timeline**: 1-2 weeks - Enable fully autonomous AI trading agents using Claude Agent SDK

**See**: [DOCS/AGENT.md](DOCS/AGENT.md) for complete architecture and design decisions

**Vision**: Transform ggbots from bot platform (scheduled execution) to agent infrastructure (autonomous AI decision-making)

**Key Features**:
- **Two-phase system**: Conversation Mode → Autonomous Mode
- **Two personalities**: Guided (user-defined strategy) vs Experimental (agent-evolving strategy)
- **Minimal DB changes**: 1 field + 1 table
- **7 tools**: Market data, trading, positions, account, wait, update_strategy, record_learning
- **Context-based compaction**: Auto-reload at 150k tokens
- **Single agent per user** (initially)

### **Phase 1: Database & Foundation** (1 day)

**Goal**: Database schema changes, project setup

**Architecture Decision**: Agent runs as **separate microservice** with isolated venv to avoid dependency conflicts.
- Agent uses `.venv-agent/` (isolated dependencies)
- Main ggbot uses `.venv/` (unchanged)
- Communication: HTTP API + direct DB/Redis access
- Deployment: PM2 process with interpreter path to `.venv-agent/bin/python`

- [x] **Database Changes**
  - [x] Add `created_by TEXT DEFAULT 'decision_engine_v2'` column to `decisions` table
  - [x] Create `agent_memory` table (id, config_id, user_id, memory_type, content, importance, created_at)
  - [x] Migration executed successfully in Supabase
  - [x] Verified paper close endpoint exists: `POST /api/v2/paper/{config_id}/positions/{trade_id}/close`

- [x] **Project Setup**
  - [x] Create `agent/` directory structure (5 stub files)
  - [x] Create `requirements-agent.txt` with isolated dependencies
  - [x] Create `scripts/setup_agent_venv.sh` for venv setup
  - [x] Update `.env.example` with agent configuration
  - [x] Redis already running (verified in ACTIVE.md)
  - [x] Run `./scripts/setup_agent_venv.sh` to create agent venv
  - [x] Test agent venv installation (Claude Agent SDK imported successfully)
  - [x] Configure `.env` with ANTHROPIC_API_KEY and AGENT_WHITELIST_USER_ID
  - [x] Add `.venv-agent/` to `.gitignore`

**Phase 1 Status**: ✅ **COMPLETE**

### **Phase 2: MCP Server & Tools** (2-3 days)

**Goal**: Build 9 MCP tools, implement trade observations model

- [x] **Database Migration**
  - [x] Replace `agent_memory` with `trade_observations` table (post-trade reflection model)
  - [x] Migration executed in Supabase, verified with 13 columns, 8 indexes, RLS enabled

- [x] **API Endpoints** (`api/agent.py`)
  - [x] 7 existing endpoints + 2 new: `POST /agent/trade-observations`, `POST /agent/trade-observations/query`

- [x] **Service Client** (`agent/service_client.py`)
  - [x] HTTP client with retry logic for all 9 endpoints (market data, trading, positions, account, strategy, observations)

- [x] **MCP Server Tools** (`agent/mcp_server.py`)
  - [x] 9 tools implemented: query_market_data, execute_trade, get_positions, get_account_status, close_position, update_strategy, wait_for, record_trade_observation, query_trade_observations
  - [x] Module-level AgentContext for single-agent testing
  - [x] MCP server tested and verified (9 tools registered)

**Phase 2 Status**: ✅ **COMPLETE**

### **Phase 3: Agent Runner** (2-3 days) - ✅ **COMPLETE**

**Goal**: Build conversation + autonomous modes, test end-to-end

**Status**: All 9 tools operational, agent ready for autonomous trading. Auth deadlock resolved via simplified service authentication.

- [x] **TradingAgent Class** (`agent/run_agent.py`)
  - [x] Simplified architecture: Separate strategy_definition and autonomous modes (no dual tasks)
  - [x] Initialize ClaudeSDKClient with MCP server
  - [x] Build single system prompt with mode/strategy context injection
  - [x] Added 32 data points documentation (7 categories) to system prompt
  - [x] Redis queue integration (messages and responses)
  - [x] Strategy definition mode: Simple query/response loop via Redis
  - [x] Autonomous mode: Pure `receive_messages()` infinite loop
  - [x] Mode switching logic: Detects flag, handles user confirmation "1" (save)/"2" (revise)
  - [x] Strategy persistence: Saves to `config_data.agent_strategy` in database
  - [ ] Compaction context injection (deferred to Phase 4 - SDK auto-compacts at 95%)

- [x] **Message Queue Integration**
  - [x] Redis queue for user → agent messages: `agent:{config_id}:messages`
  - [x] Redis queue for agent → user responses: `agent:{config_id}:responses`
  - [x] Removed dual-task complexity after SDK stream conflicts

- [x] **MCP Tools** - All 10 tools operational ✅
  - [x] Added `request_autonomous_mode` tool (10 tools total)
  - [x] Updated `query_market_data` tool to use category-based structure (7 categories, 32 data points)
  - [x] Fixed dict parameter parsing (JSON string handling)
  - [x] Added tool sandboxing with `disallowed_tools` (restricts agent to trading-only operations)
  - [x] Tool Status (9/9 working):
    - ✅ `query_market_data` - 32 data points across 7 categories
    - ✅ `execute_trade` - Opens positions with SL/TP
    - ✅ `get_positions` - Returns all open positions
    - ✅ `close_position` - Closes trades with realized P&L
    - ✅ `get_account_status` - Account balance & performance metrics
    - ✅ `wait_for` - Agent timing control (up to 24 hours)
    - ✅ `update_strategy` - Strategy modification (when autonomously_editable=true)
    - ✅ `record_trade_observation` - Post-trade reflection logging
    - ✅ `query_trade_observations` - Search past learnings
    - ✅ `request_autonomous_mode` - Mode switching with user confirmation

- [x] **API Endpoints** (`api/agent.py`) - All 8 endpoints operational ✅
  - [x] All 8 endpoints exist and registered in ggbot.py
  - [x] Orchestrator supports `data_points_override` for dynamic queries
  - [x] Simplified service authentication (removed `Depends()` complexity)
  - [x] Fixed `get_configuration()` positional argument bug
  - [x] Added JSON serialization for numpy/pandas objects
  - [x] Fixed paper trading method signatures (`get_open_positions`, `close_position`)
  - [x] Fixed SQL column names (`current_price` vs `exit_price`)
  - [x] Fixed request body structure for `record_trade_observation`

- [x] **Service Client** (`agent/service_client.py`)
  - [x] Complete rewrite with service authentication
  - [x] Sends `Authorization: Bearer {SERVICE_KEY}` header
  - [x] Sends `X-Service-Auth: agent-runner` header
  - [x] All methods send `params={"user_id": self.user_id}` query parameter
  - [x] Proper retry logic with exponential backoff

- [x] **Backend Authentication** - Production-safe service auth ✅
  - [x] Replaced complex `Depends(get_service_or_user_auth)` with simple `validate_agent_service_auth()`
  - [x] Synchronous header validation (no async dependency chain)
  - [x] Resolved FastAPI event loop deadlock
  - [x] All endpoints tested and working without timeout

- [x] **Model Configuration**
  - [x] Model selected: `claude-haiku-4-5-20251001` for testing ($1/$5 per MTok)
  - [ ] Test token usage and performance with Haiku
  - [ ] Note: Upgrade to `claude-sonnet-4-5-20250929` for production ($3/$15 per MTok)

- [x] **CLI Testing Interface**
  - [x] Rewrote `agent/chat.py` with concurrent tasks for real-time responses
  - [x] Uses `aioconsole.ainput()` for non-blocking input
  - [x] Response monitor shows agent messages immediately

- [ ] **End-to-End Testing** - Ready for full autonomous testing
  - [x] All 9 tools verified working
  - [ ] Test: Conversation mode → strategy confirmation → autonomous mode switch
  - [ ] Test: Guided mode agent executes user-defined strategy
  - [ ] Test: Experimental mode agent updates its own strategy
  - [ ] Test: Agent runs for 1+ hours autonomously with wait_for
  - [ ] Test: Compaction triggers (SDK auto-compacts at 95%)
  - [ ] Verify all decisions logged with `created_by='agent'`
  - [ ] Verify trade_observations records created

**Phase 3 Status**: ✅ **COMPLETE** (with known issues below)

**Known Issues**:
- [x] **SSL Connection Error in User Service** - ✅ FIXED with retry logic (2025-10-30)
  - Added 3-retry mechanism with 100ms delay for SSL/connection errors
  - File: `core/services/user_service.py:83-145`
  - Testing shows ggshot signals now work reliably with BTCUSDT format

- [ ] **Agent Tool Documentation Not Visible** - 🔧 IN PROGRESS (2025-11-01)
  - Problem: Python docstrings in MCP tools are NOT exposed to the agent
  - Agent can only see: tool name, @tool description parameter, and schema
  - Impact: Agent doesn't know valid category names (technical_analysis, sentiment_social, etc.)
  - Solution: Move ALL category documentation from docstring into @tool description
  - File: `agent/mcp_server.py:71-74`
  - Status: Identified root cause, fix in progress

**Next Session Priority**:
1. **CRITICAL**: Fix query_market_data tool description so agent sees categories
2. Add validation in MCP tool to return helpful errors for wrong category names
3. Test full strategy definition → autonomous mode flow with corrected tool descriptions
4. Run agent autonomously for 1+ hour with real trades
5. Monitor token usage and costs with Haiku model

### **Phase 4: Frontend & User Experience** (2-3 days)

**Goal**: Agent creation UI, dashboard integration

- [ ] **Backend API Endpoints**
  - [ ] `POST /api/v2/agent/create` - start conversation mode
  - [ ] `POST /api/v2/agent/{config_id}/message` - send message to agent
  - [ ] `GET /api/v2/agent/{config_id}/status` - get mode, strategy version, performance
  - [ ] `POST /api/v2/agent/{config_id}/stop` - gracefully stop agent
  - [ ] Filter agent configs: `GET /api/v2/config?config_type=agent`

- [ ] **Frontend Integration**
  - [ ] "Create Agent" flow - conversation UI
  - [ ] Agent status display (mode, strategy version, P&L)
  - [ ] Chat interface for conversation mode
  - [ ] Message agent while autonomous (status checks)
  - [ ] Strategy evolution timeline (for experimental mode)
  - [ ] Show learnings from agent_memory table
  - [ ] "My Agents" vs "My Bots" sections

- [ ] **Testing**
  - [ ] Create guided mode agent via UI
  - [ ] Create experimental mode agent via UI
  - [ ] Send messages to autonomous agent
  - [ ] View strategy evolution for experimental agent
  - [ ] Stop/restart agent

### **Phase 5: Production Deployment** (1-2 days)

**Goal**: Deploy, monitor, document

- [ ] **Deployment**
  - [ ] Deploy agent code to production
  - [ ] Set up PM2 service for agents (one per user initially)
  - [ ] Configure production environment variables
  - [ ] Set up Redis for message queue
  - [ ] Test agent startup/shutdown/restart

- [ ] **Monitoring**
  - [ ] Agent-specific logging (mode, tokens, strategy version)
  - [ ] Track tool call frequency
  - [ ] Monitor compaction events
  - [ ] Alert on agent failures/errors
  - [ ] Track strategy performance by mode (guided vs experimental)

- [ ] **Documentation**
  - [ ] Agent usage guide (`agent/README.md`)
  - [ ] Example strategies (conservative, aggressive, experimental)
  - [ ] Troubleshooting guide
  - [ ] API documentation for agent endpoints

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

## 📊 **MEDIUM-LOW PRIORITY - Trade Timeline Feature**

**Timeline**: 9-12 days - Complete trade lifecycle visualization and analytics foundation

**See**: [DOCS/TRADE_TIMELINE.md](DOCS/TRADE_TIMELINE.md) for complete design specification
**Status**: ✅ Canvas-based visualization prototype complete at `/view/[config_id]` (mock data, competition demo)

### Overview
Comprehensive trade lifecycle view showing Market Data → Entry Decision → Trade Management → Exit Decision, enabling transparency and advanced analytics.

### Phase 0: Prototype Visualization (COMPLETE)
- [x] Create Canvas-based Activity Timeline component
- [x] Implement zoom levels (1h/4h/1d/1w/All) with activity grouping
- [x] Add interactive features (drag pan, hover, click for details)
- [x] Deploy at `/view/[config_id]` route (public, no auth, mock data)
- [ ] Connect to real API data (future - currently mock data only)

### Phase 1: Database Schema (2-3 days)
- [ ] Add `exit_decision_id` to `paper_trades` table
- [ ] Add `exit_decision_id` to `live_trades` table
- [ ] Add `trade_id` to `decisions` table (reverse lookup)
- [ ] Add `trade_type` ('paper'/'live') to `decisions` table
- [ ] Create indexes for performance
- [ ] Write and test migration scripts
- [ ] Deploy schema changes to production

### Phase 2: Backend Integration (3-4 days)
- [ ] Update Decision Engine V2
  - [ ] Add `active_trade` parameter to `make_decision()`
  - [ ] Implement `_link_decision_to_trade()` method
  - [ ] Link "wait" decisions to active trades
- [ ] Update Paper Trading Engine
  - [ ] Link opening decision to trade on entry
  - [ ] Store exit_decision_id on close
  - [ ] Update `execute_trade()` method
  - [ ] Update `close_position()` method
- [ ] Update Live Trading Engine (Symphony)
  - [ ] Link opening decision to live_trades
  - [ ] Store exit_decision_id on Symphony close
  - [ ] Update Symphony service methods
- [ ] Update Orchestrator (ggbot.py)
  - [ ] Pass active_trade context to decision engine
  - [ ] Pass exit_decision_id when closing positions
  - [ ] Implement `_get_active_trade()` helper

### Phase 3: API Endpoints (1 day)
- [ ] Create `GET /api/v2/trade/{trade_id}/timeline` endpoint
  - [ ] Support both paper and live trades
  - [ ] Verify ownership/permissions
  - [ ] Return entry decision, monitoring decisions, exit decision
  - [ ] Parse and return formatted market data
- [ ] Update API client (frontend/lib/api.ts)
  - [ ] Add `getTradeTimeline(tradeId, tradeType)` method

### Phase 4: Frontend Component (2-3 days)
- [ ] Create `TradeTimelineModal.tsx` component
  - [ ] 4-section timeline UI (Market Data, Entry, Management, Exit)
  - [ ] Expandable/collapsible sections
  - [ ] Loading and error states
  - [ ] Mobile responsive design
- [ ] Add Timeline triggers to existing components
  - [ ] "View Timeline" in TradeDetailPopover
  - [ ] Timeline icon in PerformanceChart trade dots
  - [ ] Timeline button in DecisionFeed cards
  - [ ] Timeline option in Trade History Modal
- [ ] Market data formatting component
  - [ ] Parse multi-timeframe data from prompt
  - [ ] Format indicators for readability
  - [ ] Highlight critical signals

### Phase 5: Testing & Polish (2 days)
- [ ] Test with existing trades (NULL exit_decision_id handling)
- [ ] Test with new trades (verify full linking)
- [ ] Test paper and live trades separately
- [ ] Verify monitoring decisions link correctly
- [ ] Test Timeline modal on mobile
- [ ] Add fallback queries for old trades without links

### Future Analytics Capabilities
- [ ] Win/loss pattern analysis by market conditions
- [ ] Confidence calibration analysis
- [ ] Indicator effectiveness correlation
- [ ] Monitoring frequency vs outcomes
- [ ] Multi-timeframe analysis effectiveness

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

