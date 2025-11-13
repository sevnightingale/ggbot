# TODO.md - ggbots Implementation Plan

Active tasks and planned work. See CHANGELOG.md for completed features.

---

## ✅ **COMPLETED - Confidence-Based Position Sizing Implementation**

**Status**: Verified & Working (2025-11-11)
**Completion Doc**: [DOCS/completed/2025-11-10_confidence_based_position_sizing.md](DOCS/completed/2025-11-10_confidence_based_position_sizing.md)

**Resolution**: Implementation is sound and working correctly. Created comprehensive test suite and verified across all trading modes.

**Completed Tasks:**
- [x] Review implementation approach and identify all issues
- [x] Fix test script design (created proper multi-mode test suite)
- [x] Create proper testing strategy for paper/aster/symphony modes
- [x] Execute actual tests and verify position sizing calculations (all passed)
- [x] Validate backend calculation logic across all services
- [x] Fix validation bug (added 'agent_driven' to valid analysis frequencies)

**Test Results:**
- ✅ Paper Trading: Formula verified with 10x leverage, 25% max position
- ✅ AsterDEX: Formula verified with 10x leverage, 25% max position
- ✅ Symphony: Weight calculation verified with 15x leverage, 25% max position

**Additional Fixes:**
- Fixed Symphony credentials vault deletion (was leaving orphaned secrets)
- Fixed trading_mode='symphony' validation (removed old 'live' constraint)
- Agent bots now default to confidence_based sizing (10x leverage, 25% max)

---

## 🎯 **Activities Unification & Token Tracking**

**Status**: In Progress (2025-11-12)
**Timeline**: 3 days (12-15 hours total)
**Goal**: Unified activity logging with token tracking for metered billing

**Architecture Decision**: Use `activities` table for everything (no separate `token_usage` table). More elegant, simpler queries, powers timeline + billing from one source.

### **Key Decisions**
- ✅ **OpenRouter First**: Unified LLM API (simplifies token tracking)
- ✅ **Stripe Meter**: Pre-computed costs (we calculate, Stripe aggregates/invoices)
- ✅ **Per-Bot Tracking**: Essential for user value
- ✅ **No Base Allowance**: $100 flat (simpler)
- ✅ **Daily Reporting**: Once per day (not hourly)
- ✅ **Estimator Last**: Build after launch with real measured costs
- ❌ **No Hard Caps**: Not day 1 (add if users request)
- ❌ **No Email Alerts**: Not day 1 (add if users request)
- ❌ **No Fancy Charts**: Just total + per-bot list

### **Phase 0: OpenRouter Migration** (1 day) - ✅ **COMPLETE**
- [x] **Research & Validation**
  - [x] Sign up for OpenRouter
  - [x] Verify all models available (7 models: Grok, Claude, Gemini, DeepSeek, GPT, Kimi, Qwen)
  - [x] Check pricing (verified via OpenRouter API)
  - [x] Test token tracking format (standardized across all models)

- [x] **Implementation**
  - [x] Create `decision/llm_providers/openrouter_provider.py` (14 variants: 7 models × 2 thinking modes)
  - [x] Add `OPENROUTER_API_KEY` to .env
  - [x] Implement model name mapping (user-friendly names → OpenRouter IDs)
  - [x] Create `llm_models` reference table with pricing
  - [x] Add API endpoint `GET /api/v2/llm-models`
  - [x] Update Pydantic schemas for OpenRouter support

- [x] **Frontend Integration** (2025-11-11)
  - [x] Update StrategyEditor.tsx to fetch models from API
  - [x] Display dynamic model cards with pricing per decision
  - [x] Add thinking mode toggle below provider selection
  - [x] Add model logos in colored circles (7 brand colors)
  - [x] Update default config data to schema v2.2

- [x] **Migration**
  - [x] Keep old providers as fallback (not deleted)
  - [ ] Update bot configs to use `provider: 'openrouter'` (deferred - can be done gradually)
  - [ ] Test with real bot execution (decision engine) - deferred to Phase 1 testing
  - [ ] Update `agent/run_agent.py` if needed (deferred - agents use Claude SDK directly)

- [x] **Testing**
  - [x] Create test scripts (`test_14_models.py`, `test_model_parameters.py`)
  - [x] Test all 14 model variants (7 models × 2 thinking modes)
  - [x] Verify token counts accurate and standardized
  - [x] Test frontend build (npm run build)
  - [ ] Run 3 real bot executions (deferred to Phase 1)
  - [ ] Monitor for 24 hours (deferred to Phase 1)

### **Phase 1: Core Infrastructure** ✅ COMPLETE
- [x] Extend activities table schema (priority removed, token columns added)
- [x] Update documentation (README.md, ACTIVE.md, DATABASE_CONTEXT.md)
- [x] Schema migration successful (23 columns, billing indexes created)

### **Phase 2: Implementation** (Est. 12-15 hours)

#### 2.1 Core Infrastructure Updates (2-3 hours) ✅ COMPLETE
- [x] Update `core/common/activity_logger.py`
  - [x] Remove priority logic (column dropped)
  - [x] Add token tracking parameters
  - [x] Update activity types taxonomy
  - [x] Add `log_llm_activity()` helper function
  - [x] Update SQL INSERT (remove priority, add token columns)

- [x] Create `core/services/llm_pricing_service.py`
  - [x] Query `llm_models` table for pricing
  - [x] Calculate costs with 70% markup
  - [x] Handle nested pricing structure (standard vs thinking modes)

#### 2.2 Decision Engine Migration (3-4 hours) ✅ COMPLETE
- [x] Update `decision/engine_v2.py`
  - [x] Updated `_call_llm()` to return (response, metadata) tuple
  - [x] Added `_log_llm_activity()` helper for token tracking
  - [x] Updated 3 LLM callsites (signal validation, opportunity analysis, position management)
  - [x] Updated 3 save methods to log llm_thought activities with costs
  - [x] Keep `INSERT INTO decisions` for compatibility (deprecated)

- [x] Signal validation integration complete (covered by decision engine updates)

#### 2.3 Trading Engine Updates (2 hours)
- [ ] Update `trading/paper/supabase_service.py`
  - [ ] Ensure `trade_entry` activities have unified structure
  - [ ] Ensure `trade_exit` activities have P&L details

- [ ] Update `trading/live/symphony_service.py` and `trading/live/aster_service_v3.py`
  - [ ] Consistent activity logging across all trading modes

#### 2.4 Stripe Billing Integration (3-4 hours) ✅ MOSTLY COMPLETE
- [x] Create `billing/stripe_meter_reporter.py`
  - [x] Query unreported activities WHERE stripe_reported = FALSE
  - [x] Group by user_id, SUM(platform_cost_usd)
  - [x] Send Stripe Meter events to `mtr_61TcMoxbXUvKBLQG741J9gH6H6LiHGyW`
  - [x] Mark activities as stripe_reported = TRUE
  - [x] Error handling and retry logic
  - [x] Fixed schema mismatch (query actual llm_models columns)
  - [x] Uses existing STRIPE_SECRET_KEY (not new var)

- [x] Add billing API endpoints in `ggbot.py`
  - [x] `GET /api/v2/billing/usage` (current unreported usage + model breakdown)
  - [x] `GET /api/v2/billing/usage/breakdown` (per-bot + daily breakdown, 30-day default)

- [x] Set up scheduled job
  - [x] Integrated with APScheduler (midnight UTC daily)
  - [x] Logs: "✅ Stripe meter reporting scheduled"

- [ ] Webhook handler
  - [ ] Add `invoice.payment_failed` event handler (pause bots on payment failure)

#### 2.5 Frontend Updates (2 hours)
- [ ] Update timeline component
  - [ ] Handle unified `trade_entry` with `details.side`
  - [ ] Add token cost display for `llm_thought` activities
  - [ ] Show market data in `market_query` activities

#### 2.6 Agent Integration (1 hour)
- [ ] Verify `agent/mcp_server.py` and `agent/run_agent.py`
  - [ ] Ensure agent LLM calls log with token tracking
  - [ ] Verify agent tools already log correctly

#### 2.7 Testing & Validation (2-3 hours)
- [ ] Test scheduled bot execution (market_query + llm_thought created)
- [ ] Test agent execution (all actions logged correctly)
- [ ] Test signal validation (signal_received + llm_thought)
- [ ] Verify token tracking (costs calculated correctly with 70% markup)
- [ ] Test Stripe reporting (dry-run mode first)
- [ ] Query per-bot breakdown (verify costs grouped by config_id)
- [ ] Test frontend timeline (new activity types display correctly)

- [ ] **LLM Pricing Research**
  - [ ] Research token rates: GPT-4, GPT-5, Claude Opus/Sonnet/Haiku, DeepSeek, Grok
  - [ ] Seed `llm_model_pricing` table with current rates

- [ ] **Integration**
  - [ ] Wrap all LLM calls with token tracking:
    - [ ] `decision/engine_v2.py`
    - [ ] `agent/run_agent.py`
    - [ ] `signals/listener_service.py`

### **Phase 2: Stripe Metered Billing** (1 day)
- [ ] **Stripe Configuration**
  - [ ] Create Meter: "LLM API Usage Cost" (event: `llm_usage_cost`)
  - [ ] Create Price: $1/unit (where 1 unit = $1)
  - [ ] Set billing threshold: $20 OR monthly

- [ ] **Subscription Creation**
  - [ ] Add `POST /api/v2/create-metered-subscription` endpoint
  - [ ] Update signup flow (require credit card)

- [ ] **Daily Reporting Job**
  - [ ] Create `scripts/report_stripe_usage.py`
  - [ ] Aggregate yesterday's usage per user
  - [ ] Send to Stripe Meter (dollar amounts)
  - [ ] Mark as reported in database
  - [ ] Add to crontab (1am daily)

- [ ] **Webhook Updates**
  - [ ] Add `invoice.payment_failed` handler (pause bots)

### **Phase 3: Premium Subscription** (0.5 days)
- [ ] **Database**
  - [ ] Add `premium_tier_active` to user_profiles

- [ ] **Stripe**
  - [ ] Create product: "ggbots Pro - Agent Access" ($100/month)

- [ ] **Backend**
  - [ ] Add `POST /api/v2/upgrade-to-premium` endpoint
  - [ ] Add `can_use_agents` property to UserProfile
  - [ ] Update `/api/v2/me` endpoint (include can_use_agents)

- [ ] **Frontend**
  - [ ] Gate agent creation behind premium check

### **Phase 4: Minimal UI** (0.5 days)
- [ ] **Backend API**
  - [ ] `GET /api/v2/usage/current-month` (total + per-bot breakdown)

- [ ] **Frontend Component**
  - [ ] Create `UsageDisplay` component
  - [ ] Show: Current month total (big number)
  - [ ] Show: Per-bot breakdown (list with costs)
  - [ ] Show: Estimated month-end
  - [ ] Link to Stripe billing portal

- [ ] **Integration**
  - [ ] Add to Settings modal or create "Usage" tab

### **Phase 6: Estimator (Post-Launch)** (+1 day after 24-48h data collection)
- [ ] **Collect Real Data**
  - [ ] Run test bots for 24-48 hours (various configs)
  - [ ] Query actual costs from `token_usage` table
  - [ ] Build lookup table of daily costs per (model, frequency)

- [ ] **Estimator Service**
  - [ ] Create `core/services/usage_estimator.py` (lookup-based)
  - [ ] Add `POST /api/v2/estimate-cost` endpoint

- [ ] **Frontend Integration**
  - [ ] Real-time estimate in bot config UI (debounced)
  - [ ] Display: "Est. $X/day ($Y/month)"

### **Testing** (Throughout)
- [ ] Test token tracking (50 executions, verify accuracy)
- [ ] Test Stripe integration (test mode)
- [ ] Test daily reporting job
- [ ] Test billing threshold ($20 trigger)
- [ ] Test payment failure (bots pause)
- [ ] Test Premium upgrade
- [ ] End-to-end: new user → add card → bot → invoice

### **Launch**
- [ ] Switch Stripe to live mode
- [ ] Deploy backend + frontend
- [ ] Monitor for 48 hours
- [ ] Collect estimator data

---

## 🤖 **Agent - Session Persistence Testing & Monitoring**

**Status**: Session resumption implemented (2025-11-08), needs production validation

- [ ] **Test Crash Recovery**
  - [ ] Restart live agent, verify session resumption logs
  - [ ] Test compaction → crash → resume flow
  - [ ] Validate conversation memory preserved

- [ ] **Monitor Session Behavior**
  - [ ] Test session longevity (does it expire after 24 hours? 7 days?)
  - [ ] Track health monitoring (`last_active_at` updates)
  - [ ] Verify no session_id changes after compaction

- [ ] **Health Check System**
  - [ ] Implement auto-restart for hung agents (no activity >30 minutes)
  - [ ] Add alerting for agent failures
  - [ ] Track tool call frequency and errors

- [ ] **Strategy Builder UX Refinement**
  - [ ] Test real-time collaborative editing (user + agent editing same strategy)
  - [ ] Verify SSE updates push agent edits to frontend
  - [ ] Test debounced auto-save (1s delay)

---

## 🏗️ **Agent Architecture - Builder/Executor Separation**

**Status**: Planning (2025-11-08)
**Planning Doc**: [DOCS/todo/strategy_builder_agent.md](DOCS/todo/strategy_builder_agent.md)

**Goal**: Split agent into two distinct services:
- **Strategy Builder** (shared, multi-user) - Configuration assistant always available
- **Autonomous Traders** (dedicated, per-bot) - Execution-only agents

### **Phase 1: Create Builder Service** (No Breaking Changes)
- [ ] **Database**
  - [ ] Create `strategy_builder_sessions` table
  - [ ] Rename `agent_sessions` → `trading_agent_sessions`
  - [ ] Run migration (backward-compatible)

- [ ] **Builder Service Implementation**
  - [ ] Create `agent/builder_service.py` (session pool manager)
  - [ ] Create `agent/builder_mcp_server.py` (6 configuration tools)
  - [ ] Create `api/builder.py` (WebSocket endpoints)
  - [ ] Start as PM2 service: `pm2 start agent/builder_service.py --name strategy-builder`

- [ ] **Frontend Integration**
  - [ ] Add WebSocket connection to builder service
  - [ ] Update chat interface to always connect (no "Start" button)
  - [ ] Add feature flag: `ENABLE_BUILDER_SERVICE`

- [ ] **Testing**
  - [ ] Test 10+ concurrent users chatting with builder
  - [ ] Verify session resumption across reconnects
  - [ ] Validate zero cross-user session contamination
  - [ ] Test update_bot_config saves correctly

### **Phase 2: Clean Up Trading Agents** (Breaking Change)
- [ ] **Remove Mode Switching**
  - [ ] Delete `strategy_definition` mode from `run_agent.py`
  - [ ] Remove mode parameter from API endpoints
  - [ ] Remove builder tools from trading agent MCP server
  - [ ] Add startup validation (strategy must exist)

- [ ] **Update Frontend**
  - [ ] Remove "Start Strategy Builder" button
  - [ ] Update "Activate" button to validate strategy exists
  - [ ] Update status display (builder always available)

- [ ] **Communication**
  - [ ] Notify users about simplified UX (no mode switching)
  - [ ] Update `agent/README.md` documentation

### **Phase 3: Expand Builder Scope** (Enhancement)
- [ ] **Scheduled Bot Configuration**
  - [ ] Add `update_bot_config` support for `extraction`, `decision`, `trading` sections
  - [ ] Add validation for scheduled bot configs
  - [ ] Update builder system prompt with scheduled guidance

- [ ] **Frontend Integration**
  - [ ] Enable builder chat for scheduled bot config pages
  - [ ] Add context detection (agent vs scheduled)

---

## 🏆 **AsterDEX - Frontend Integration & Competition**

**Status**: Core trading operational, needs UI and testing for competition

### **Vault & Credentials**
- [ ] Add `get_aster_credential(user_id)` to vault_utils.py
- [ ] Add `store_aster_credential(user_id, api_key, api_secret)`
- [ ] Add `delete_aster_credential(user_id)`
- [ ] Test credential encryption/decryption

### **Frontend Integration**
- [ ] **Settings Modal**
  - [ ] Add "AsterDEX" tab to Settings modal
  - [ ] Add API Key + Secret input fields
  - [ ] Add "Test Connection" button
  - [ ] Show connection status indicator

- [ ] **Trading Mode Selection**
  - [ ] Add "AsterDEX Live" option to bot creation modal
  - [ ] Show AsterDEX badge in bot rail (orange/purple)
  - [ ] Disable if credentials not configured
  - [ ] Add tooltip explaining AsterDEX mode

- [ ] **Dashboard Display**
  - [ ] Add SSE enrichment for `trading_mode === 'aster'` (SSE already supports this, verify frontend)
  - [x] Route close button to Aster service
  - [ ] Show "Track on AsterDEX" for balance
  - [x] Add AsterDEX icon/badge to active positions

### **API Endpoints**
- [ ] `POST /api/v2/aster/setup` (store credentials)
- [ ] `GET /api/v2/aster/status` (check connection)
- [ ] `POST /api/v2/aster/disconnect` (remove credentials)
- [ ] `GET /api/v2/positions/aster/{config_id}` (query positions)
- [ ] `POST /api/v2/positions/aster/{order_id}/close` (close position)
- [ ] `GET /api/v2/account/aster/{config_id}` (account metrics)

### **SL/TP Improvements**
- [ ] Add SL/TP conditional order creation (STOP_MARKET, TAKE_PROFIT_MARKET)
- [ ] Add SL/TP order cancellation before close
- [ ] Add leverage management (currently defaults to 10x)

### **Error Handling**
- [ ] Add rate limit tracking and backoff logic
- [ ] Implement circuit breaker at 80% rate limit
- [ ] Add retry logic with exponential backoff
- [ ] Handle common API errors (-1121, -2010, etc.)

### **Testing & Competition**
- [ ] Execute 10 test trades successfully
- [ ] Verify SL/TP conditional orders work
- [ ] Test error scenarios (insufficient balance, invalid symbol)
- [ ] Monitor rate limiting (no 429 errors)
- [ ] Create competition strategy (high-frequency, 5-10 bots)
- [ ] Monitor leaderboard ranking and total volume

---

## 🌐 **Symphony Live Trading Integration**

**Status**: BLOCKED - Waiting for Symphony API fix

**Blocker**: Symphony `/agent/all-positions` endpoint returns 404 (documented but not implemented)

**What's Needed from Symphony Team**:
```
GET https://api.symphony.io/agent/all-positions?userAddress={WALLET_ADDRESS}
Returns: accountSummary with totalEquity, availableBalance, marginUsed
```

**Our Work (Once API Fixed - ~2.5 hours)**:
- [ ] Add `get_account_summary()` method to Symphony service
- [ ] Add Symphony branches to 5 agent endpoints
- [ ] Update system prompt with Symphony capabilities
- [ ] Test end-to-end with real credentials

See: [agent/README.md](agent/README.md) "Symphony Integration Steps" for complete guide

---

## 🧠 **Market Intelligence - Future Phases**

**Phase 1 Complete**: 8 Grok sources live ($195/month platform cost)

### **Phase 2: Premium On-Chain** ($100-500/month)
- [ ] Whale wallet tracking (Nansen/Arkham)
- [ ] Exchange reserves & flows (Glassnode/CryptoQuant)
- [ ] Token unlocks calendar (TokenUnlocks.app)
- [ ] Dev activity metrics (GitHub API)

### **Phase 3: Sentiment & Social** ($100-500/month)
- [ ] Twitter/X sentiment analysis (Twitter API + NLP)
- [ ] Reddit crypto sentiment (Reddit API + NLP)
- [ ] Narrative velocity tracking (topic modeling)

### **Phase 4: Advanced Intelligence** ($200-1000/month)
- [ ] Order book liquidity heatmaps (Coinalyze)
- [ ] CEX/DEX market share tracking
- [ ] Institutional flows (BTC ETF data)

---

## 🎨 **User Experience & Frontend**

### **Bot Creation UX**
- [ ] Add name field to bot creation modal (currently defaults to "Untitled Bot")

### **Legal & Compliance**
- [ ] Add Terms of Service page/modal to frontend
- [ ] Add Privacy Policy page/modal to frontend
- [ ] Add financial risk disclaimers (prominent placement on bot creation, settings, and trading pages)
- [ ] Add "I acknowledge the risks" checkbox for live trading activation

### **Public Performance Features**
**Dependencies**: ✅ RLS migration ready in `SQL.md` - see System Improvements → Security

**Architecture Decided**:
- Per-bot privacy control via `configurations.is_public_performance`
- No usernames shown (just bot names)
- All activities public when opted in (trades, thoughts, market queries)
- Public arena shows: Bot Name | Mode | P&L | Win Rate | Trades

Implementation tracked under **System Improvements → Security → Backend API Updates** and **Frontend Implementation** sections.

### **Trading Modes Refactor** (In Progress - Other CC Instance)
- [ ] Remove `execution_mode` duplication from JSONB
- [ ] Add `trading_mode` selection to bot creation modal
- [ ] Update frontend to use table field only

### **Mobile Responsive Design**
- [ ] Transform desktop 3-column to mobile single column
- [ ] Implement 70%-width slide-in drawers
- [ ] Create bottom tab system for drawer triggers
- [ ] Add touch gestures for carousel navigation

### **Status Messaging Improvements**
- [ ] Change "next run..." to "waiting for next candle close..."
- [ ] Add explanatory tooltips for bot status states
- [ ] Improve activation/deactivation feedback

---

## 🔧 **System Improvements**

### **Security & Data Access**
**Priority**: HIGH - Current RLS rules may allow unauthorized access to some tables

**Status**: SQL migration ready in `SQL.md` - review and execute in Supabase

- [x] **Supabase RLS Audit** ✅ COMPLETE
  - [x] Identified 3 tables with RLS issues:
    - `activities`: Policy exists but RLS disabled (intentional for aster.ggbots.ai)
    - `agent_sessions`: No RLS at all (medium risk)
    - `llm_models`: No RLS (low risk, reference data)
  - [x] Documented authentication flows (user JWT, service role bypass, optional auth for public viewing)
  - [x] Architecture decision: Per-bot privacy via `configurations.is_public_performance`

- [ ] **Execute SQL Migration** (30 min)
  - [ ] Review SQL commands in `SQL.md`
  - [ ] Run Step 1: Add `is_public_performance` column
  - [ ] Run Step 2: Fix activities table RLS (2 policies)
  - [ ] Run Step 3: Fix agent_sessions table RLS
  - [ ] Run Step 4: Fix llm_models table RLS
  - [ ] Run Step 5-6: Verify policies active
  - [ ] Test with your user account (verify you can still see your activities)
  - [ ] Test public access (verify aster.ggbots.ai still works)

- [ ] **Backend API Updates** (2-3 hours)
  - [ ] Add `PATCH /api/v2/config/{config_id}/public` endpoint (toggle is_public_performance)
  - [ ] Create `GET /api/v2/arena/leaderboard` endpoint (public bots only, no auth required)
  - [ ] Create `GET /api/v2/arena/{config_id}` endpoint (public bot detail, no auth required)
  - [ ] Update activities API endpoints to document public access behavior
  - [ ] Add filters for public arena (trading_mode, timeframe, sort by performance)
  - [ ] Test with RLS enabled (verify isolation works)

- [ ] **Frontend Implementation** (3-4 hours)
  - [ ] Add privacy toggle in bot settings/config page
    - [ ] Checkbox: "Show this bot's performance publicly"
    - [ ] Warning: "Public bots show all activities (trades, thoughts, market queries)"
    - [ ] Save calls PATCH endpoint
  - [ ] Create `/arena` public leaderboard page
    - [ ] Table: Bot Name | Mode | P&L | Win Rate | Trades | Performance %
    - [ ] Filters: Trading Mode (All/Paper/Symphony/Aster), Timeframe (24h/7d/30d/All)
    - [ ] Sort: By P&L, Win Rate, or Trade Count
    - [ ] Click bot → navigate to `/view/{config_id}` (existing timeline page)
  - [ ] Update `/view/{config_id}` to work without auth (already supports optional auth)
  - [ ] Add "Make Public" button to bot rail dropdown menu

### **System Robustness**
- [ ] Add comprehensive error boundaries to frontend
- [ ] Implement graceful API failure handling with retries
- [ ] Add circuit breakers for external service failures
- [ ] Improve logging and error taxonomy
- [ ] Plan upgrade from Node.js 18 to Node.js 20+

### **Code Quality**
- [ ] Run `ruff` + `black` for Python formatting
- [ ] Remove unused imports and clean up hygiene
- [ ] Add proper TypeScript types for signal_data structures

---

## 📚 **Documentation**

### **Missing/Incomplete READMEs**
- [ ] Create `api/README.md` (document agent endpoints)
- [ ] Create `core/config/README.md` (config system architecture)

### **README Reviews & Updates**
- [ ] Review `market_intelligence/README.md` (verify 32 data points, update cost to $195/month)
- [ ] Review `decision/README.md` (verify V2 template system)
- [ ] Review `trading/README.md` (verify WebSocket migration complete)
- [ ] Review `database/README.md` (add agent_sessions, trade_observations tables)
- [ ] Review `frontend/README.md` (verify Forge architecture)

### **Documentation Consistency**
- [ ] Ensure ACTIVE.md and module READMEs don't contradict
- [ ] Verify README.md links to all module READMEs
- [ ] Remove legacy/outdated information

---

## 🧪 **Testing & Validation**

### **Symbol Coverage**
- [ ] Test all 142 crypto symbols for data availability
- [ ] Verify WebSocket + REST fallback for all pairs
- [ ] Create symbol blacklist for unsupported pairs

### **Technical Analysis Validation**
- [ ] Test all 21 indicator preprocessors individually
- [ ] Validate calculations against reference implementations
- [ ] Edge case testing (low volume, missing data, extreme movements)

### **Load Testing**
- [ ] Test system with multiple concurrent bots
- [ ] Validate database performance under load
- [ ] Test SSE stream with many connected clients
- [ ] Cross-browser compatibility testing

### **Security**
- [ ] Audit API endpoints for vulnerabilities
- [ ] Test rate limiting and authentication flows
- [ ] Validate data isolation between users

---

## 📚 Documentation References

- **New Claude Code Instances**: `GO.md` - Start here for onboarding
- **Current Status**: `ACTIVE.md` - Production system status
- **Complete History**: `CHANGELOG.md` - All completed features and fixes
- **Architecture**: `README.md` - Platform overview

