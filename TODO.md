# TODO.md - ggbots Implementation Plan

Active tasks and planned work. See CHANGELOG.md for completed features.

---

## ✅ **DEPLOYED - Universal AI Assistant** (2025-11-16)

**Status**: 🟢 PRODUCTION READY - Backend live, frontend ready for testing

### **Implementation Complete**
- [x] Backend API endpoint: `POST /api/v2/assistant/chat`
- [x] Claude Haiku 4.5 function calling with 3 tools
- [x] Bot-type aware system prompts (agent, scheduled, signal_validation)
- [x] Frontend bottom sheet component (UniversalAIAssistant.tsx)
- [x] Framer-motion draggable/collapsible UI
- [x] Integrated into Forge configure pages
- [x] Auto-refreshes config on AI updates
- [x] Build test passing (TypeScript, ESLint clean)

### **Features**
- Works for ALL 3 bot types (agent, scheduled, signal_validation)
- See config while chatting (bottom sheet overlay)
- Query 32 available data points across 7 categories
- Load and update full bot configurations
- Deep merge for partial updates (update just one field)
- Cost: ~$0.016 per session (~$16/month for 1000 users)

### **Next Steps**
- [ ] Test on production (Vercel deployment)
- [ ] Monitor Claude API costs and usage
- [ ] Gather user feedback for improvements
- [ ] Consider adding conversation persistence (Redis cache)

### **Files Created/Modified**
- `api/assistant.py` - Main chat endpoint with function calling
- `frontend/components/UniversalAIAssistant.tsx` - Bottom sheet UI
- `frontend/app/forge/page.tsx` - Integration with configure pages
- `DOCS/todo/strategy_builder_api.md` - Planning documentation
- `DOCS/archived/strategy_builder_agent_complex.md` - Old complex approach (archived)

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

## 📊 **Market Maker - Kuru Integration**

**Status**: ⏸️ WAITING - Module complete, needs Kuru API launch (Monday Nov 24?)

**What's Ready**:
- [x] Core Avellaneda-Stoikov engine (~900 lines)
- [x] Simulation tested (+0.20% P&L, inventory management working)
- [x] Exchange adapter interface
- [x] Kuru adapter template (needs real API docs)

**Next Steps (When Kuru Launches)**:
- [ ] **Get API Access** (~30 min)
  - [ ] Register on Kuru platform
  - [ ] Obtain API key + secret
  - [ ] Read official API documentation

- [ ] **Update KuruAdapter** (~1-2 hours)
  - [ ] Update authentication method (currently assumes HMAC-SHA256)
  - [ ] Fix endpoint URLs in `market_maker/exchanges/kuru.py`
  - [ ] Update request/response parsing based on actual API format
  - [ ] Confirm symbol format (CHOG-USDC vs CHOG/USDC vs CHOG_USDC)
  - [ ] Add WebSocket integration for real-time fills

- [ ] **Testing** (~2-3 hours)
  - [ ] Test with $100-200 order size, $2k capital
  - [ ] Validate orderbook fetching works
  - [ ] Confirm limit orders placed successfully
  - [ ] Monitor fill rate and spread competitiveness
  - [ ] Test inventory rebalancing logic
  - [ ] Verify P&L tracking accuracy (account for fees)

- [ ] **Production Deployment** (if successful)
  - [ ] Scale gradually ($500 orders, $5k capital after 24h)
  - [ ] Monitor for adverse selection (consecutive fills one side)
  - [ ] Add missing features: rebalancing, error handling, market impact detection
  - [ ] Consider integration with ggbots monitoring/logging

**Files**: `market_maker/`, `DOCS/MM.md`

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
- [x] Add name field to bot creation modal (completed 2025-11-13)

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

**Status**: ✅ SQL migration executed and verified

- [x] **Supabase RLS Audit** ✅ COMPLETE
  - [x] Identified 3 tables with RLS issues:
    - `activities`: Policy exists but RLS disabled (intentional for aster.ggbots.ai)
    - `agent_sessions`: No RLS at all (medium risk)
    - `llm_models`: No RLS (low risk, reference data)
  - [x] Documented authentication flows (user JWT, service role bypass, optional auth for public viewing)
  - [x] Architecture decision: Per-bot privacy via `configurations.is_public_performance`

- [x] **Execute SQL Migration** ✅ COMPLETE (2025-11-13)
  - [x] Reviewed SQL commands in `SQL.md`
  - [x] Executed Step 1: Add `is_public_performance` column
  - [x] Executed Step 2: Fix activities table RLS (2 policies)
  - [x] Executed Step 3: Fix agent_sessions table RLS
  - [x] Executed Step 4: Fix llm_models table RLS
  - [x] Verified Step 5-6: Policies active and working
  - [x] Tested with user account (activities visible)
  - [x] Tested public access (aster.ggbots.ai working)

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

