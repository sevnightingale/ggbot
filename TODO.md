# TODO.md - ggbots Implementation Plan


## 🤖 **HIGH PRIORITY - Autonomous Trading Agent**

**Timeline**: 1-2 weeks - Enable fully autonomous AI trading agents using Claude Agent SDK

**See**: [DOCS/AGENT.md](DOCS/AGENT.md) for complete architecture and design decisions

**Vision**: Transform ggbots from bot platform (scheduled execution) to agent infrastructure (autonomous AI decision-making)

**Architecture**: Agent IS the orchestrator + decision engine, using extraction/trading services as tools

### **Phase 1: Foundation & MCP Server** (3-4 days)

**Goal**: Build MCP server with 6 core tools, test individual tool functionality

- [ ] **Project Setup**
  - [ ] Create `agent/` directory structure
  - [ ] Set up Claude Agent SDK dependencies
  - [ ] Create `.mcp.json` configuration file
  - [ ] Set up environment variables (AGENT_CONFIG_ID, AGENT_USER_ID, AUTH_TOKEN)

- [ ] **Missing Backend Endpoint**
  - [ ] Add `POST /api/v2/positions/paper/{trade_id}/close` endpoint
  - [ ] Test paper position closing via API
  - [ ] Verify response format matches live trading close endpoint

- [ ] **Config Management** (`agent/config_manager.py`)
  - [ ] Implement `create_agent_config(user_id, strategy)` → creates config_type="agent"
  - [ ] Implement `update_agent_config(updates)` → PATCH config dynamically
  - [ ] Implement `get_agent_config()` → load current config state
  - [ ] Test config CRUD operations via API

- [ ] **Service Client** (`agent/service_client.py`)
  - [ ] Implement `get_current_price(symbol)` wrapper
  - [ ] Implement `call_extraction_service(config)` wrapper
  - [ ] Implement `call_trading_service(intent)` wrapper
  - [ ] Implement `query_positions()` DB query wrapper
  - [ ] Implement `query_account()` DB query wrapper
  - [ ] Test all service wrappers with real config_id

- [ ] **MCP Server Tools** (`agent/mcp_server.py`)
  - [ ] Tool 1: `query_market_data` (update config → call extraction)
  - [ ] Tool 2: `execute_trade` (create intent → call trading service)
  - [ ] Tool 3: `get_positions` (query open trades from DB)
  - [ ] Tool 4: `close_position` (call paper trading close endpoint)
  - [ ] Tool 5: `get_account_status` (query account metrics)
  - [ ] Tool 6: `wait_for` (log wait reason, return next check time)
  - [ ] Create `ggbots_trading_server` with all 6 tools
  - [ ] Test each tool individually with mock agent config

### **Phase 2: Agent Runner & Integration** (2-3 days)

**Goal**: Build agent loop, test autonomous operation, verify full integration

- [ ] **Agent Runner** (`agent/run_agent.py`)
  - [ ] Implement `run_trading_agent(user_id, strategy)` main loop
  - [ ] Configure Claude Agent SDK with MCP server
  - [ ] Set allowed_tools list (all 6 tools)
  - [ ] Build system prompt with strategy context
  - [ ] Implement agent message streaming and logging
  - [ ] Add error handling and graceful shutdown

- [ ] **Integration Testing**
  - [ ] Create test agent config (paper trading, $10K balance)
  - [ ] Test: Agent queries market data → receives formatted analysis
  - [ ] Test: Agent executes trade → trade appears in database
  - [ ] Test: Agent checks positions → sees open trades
  - [ ] Test: Agent closes position → position marked closed
  - [ ] Test: Agent checks account → sees balance/P&L
  - [ ] Verify all decisions logged with `created_by = 'agent'`

- [ ] **Autonomous Operation Test**
  - [ ] Run agent for 1 hour with simple strategy
  - [ ] Verify agent makes decisions autonomously
  - [ ] Verify agent controls its own timing (wait_for works)
  - [ ] Check database audit trail (decisions, trades, config updates)
  - [ ] Monitor agent reasoning quality

### **Phase 3: Dashboard & Multi-Agent Support** (2-3 days)

**Goal**: Show agents in UI, support multiple concurrent agents

- [ ] **Database & Backend**
  - [ ] Verify `config_type = 'agent'` filtering works
  - [ ] Test multiple agent configs for same user
  - [ ] Ensure paper accounts isolated per agent config_id
  - [ ] Test agent metrics endpoints (`/api/v2/bot/{config_id}/metrics`)

- [ ] **Frontend Integration**
  - [ ] Filter configs by type: bots vs agents
  - [ ] Create "My Agents" section in dashboard
  - [ ] Show agent status (Active, Current Focus, Open Positions)
  - [ ] Display agent current config state ("Analyzing BTC with RSI, Sentiment")
  - [ ] Show agent performance metrics (same as bots)
  - [ ] Add "Create Agent" flow (strategy input → agent creation)

- [ ] **Multi-Agent Testing**
  - [ ] Run 2 agents simultaneously with different strategies
  - [ ] Verify configs don't interfere (isolated state)
  - [ ] Verify paper accounts isolated (separate balances)
  - [ ] Check dashboard shows both agents correctly
  - [ ] Test stopping one agent while other continues

### **Phase 4: Production Deployment & Monitoring** (1-2 days)

**Goal**: Deploy to production, monitor initial agent performance

- [ ] **Deployment**
  - [ ] Deploy agent code to production server
  - [ ] Set up agent service (PM2 or systemd)
  - [ ] Configure production environment variables
  - [ ] Test agent startup/shutdown procedures

- [ ] **Monitoring & Logging**
  - [ ] Add agent-specific logging (agent_id, strategy, decisions)
  - [ ] Monitor agent API call volume
  - [ ] Track agent decision quality metrics
  - [ ] Set up alerts for agent errors/failures

- [ ] **Documentation**
  - [ ] Write agent usage guide (`agent/README.md`)
  - [ ] Document strategy creation patterns
  - [ ] Create example strategies (conservative, aggressive, macro)
  - [ ] Document debugging procedures

### **Future Enhancements** (Post-Launch)

- [ ] **Agent Learning**
  - [ ] Track strategy performance (win rate by strategy type)
  - [ ] Recommend strategy adjustments based on performance
  - [ ] Strategy template library

- [ ] **User Interaction**
  - [ ] Mid-trade chat interface ("Why did you enter here?")
  - [ ] Strategy refinement via conversation
  - [ ] Real-time reasoning display in dashboard

- [ ] **Multi-Agent Coordination**
  - [ ] Shared context between agents
  - [ ] Position correlation awareness
  - [ ] Portfolio-level risk management

---

## 🧠 **HIGH PRIORITY - Market Intelligence Expansion**

**Timeline**: 4-6 weeks - Add contextual data to improve AI decision quality

**See**: [DOCS/MARKET_INTELLIGENCE_ROADMAP.md](DOCS/MARKET_INTELLIGENCE_ROADMAP.md) for complete roadmap

**Current State**:
- ✅ Infrastructure complete (data_sources/data_points tables, UI, API)
- ✅ 2/6 data sources populated (Technical Analysis: 21 indicators, ggShot signals: 1)
- ⏳ 4/6 data sources empty (On-Chain, Sentiment, News, Macro)
- **Gap**: Zero context beyond technicals - no macro, sentiment, on-chain, or news awareness

### **Phase 1: Free Quick Wins** (Week 1-2) - $0/month

**Goal**: Add 7 contextual data points via 3 acquisition methods (Direct API, Grok Search, Browser-Use)

**New Data Source: Crypto Derivatives** (2 points)
- [ ] Create `BinanceFundingAdapter` for perpetual funding rates
- [ ] Create catalog YAML: `funding_rate.yaml`
- [ ] Seed database: INSERT 1 data_source + 2 data_points (BTC, ETH)
- [ ] Test: Fetch BTC/ETH funding rates from Binance API

**New Data Source: Macro Context** (4 points)
- [ ] Create `GrokSearchAdapter` OR `FredApiAdapter` base class
- [ ] Create catalog YAMLs: `vix.yaml`, `dxy.yaml`, `cpi.yaml`, `nfp.yaml`
- [ ] Seed database: INSERT 1 data_source + 4 data_points
- [ ] Test Grok API with web search tool for VIX scraping
- [ ] Test FRED API key setup and data fetch

**Expand Data Source: On-Chain Analytics** (1 point)
- [ ] Create `DefiLlamaAdapter` for DeFi TVL metrics
- [ ] Create catalog YAML: `tvl.yaml`
- [ ] Seed database: INSERT 1 data_point (BTC DeFi TVL)
- [ ] Test: Fetch TVL from DefiLlama API

**Decision Engine Integration**
- [ ] Update `decision/prompts/opportunity_analysis.py` with context section
- [ ] Modify `decision/engine_v2.py` to fetch enabled data sources from config
- [ ] Add market intelligence formatting for LLM prompts
- [ ] Test end-to-end: User enables funding rates → Decision agent sees data

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

## 📊 **MEDIUM-LOW PRIORITY - Trade Timeline Feature**

**Timeline**: 9-12 days - Complete trade lifecycle visualization and analytics foundation

**See**: [DOCS/TRADE_TIMELINE.md](DOCS/TRADE_TIMELINE.md) for complete design specification

### Overview
Comprehensive trade lifecycle view showing Market Data → Entry Decision → Trade Management → Exit Decision, enabling transparency and advanced analytics.

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
  - [ ] Test all 140+ crypto symbols for KuCoin data availability
  - [ ] Verify Hummingbot integration works for all supported pairs
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

