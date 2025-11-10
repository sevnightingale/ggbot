# TODO.md - ggbots Implementation Plan

Active tasks and planned work. See CHANGELOG.md for completed features.

---

## 💳 **CRITICAL - Metered Billing & Pricing Overhaul** [metered_billing.md]

**Status**: Planning (2025-11-08)
**Planning Doc**: [DOCS/todo/metered_billing.md](DOCS/todo/metered_billing.md)

**Goal**: Complete platform pricing overhaul from freemium to usage-based billing + premium subscription.

### **Business Model**
- **Eliminate free tier** - all users pay based on consumption
- **Usage tier**: Pay-as-you-go, charged monthly for LLM token consumption (70% markup)
- **Premium tier**: $100/month unlocks agents + base usage allowance + premium features
- **Low barrier to test**: Estimated $2-5/month for minimal usage (DeepSeek, 1h frequency)

### **Phase 1: Token Tracking Infrastructure** (2 days)
- [ ] **Database Schema**
  - [ ] Create `token_usage` table (user_id, config_id, provider, model, tokens, costs)
  - [ ] Create `llm_model_pricing` table (provider, model, input/output rates, effective_date)
  - [ ] Create `usage_alerts` table (threshold tracking for email alerts)
  - [ ] Add indexes for monthly aggregation and Stripe reporting queries

- [ ] **Token Tracking Service**
  - [ ] Create `TokenTrackingService` class (record_usage, get_current_month_spend, get_unreported_usage)
  - [ ] Implement cost calculator (70% markup, model-specific pricing)
  - [ ] Add token tracking wrapper to all LLM calls (decision, agent, extraction, signal validation)

- [ ] **LLM Pricing Research**
  - [ ] Research current token rates: GPT-4, GPT-5, Claude Opus 4, DeepSeek R1, Grok 4
  - [ ] Seed `llm_model_pricing` table with current rates
  - [ ] Document pricing sources and update schedule

- [ ] **OpenRouter Investigation**
  - [ ] Research: Are all current models available via OpenRouter?
  - [ ] Test token tracking: Verify `usage` object in responses
  - [ ] Compare pricing: OpenRouter rates vs direct API + 70% markup
  - [ ] Test latency: Direct API vs OpenRouter proxy (<500ms overhead acceptable)
  - [ ] Decision: Migrate immediately or after metered billing stabilizes?

### **Phase 2: Stripe Metered Billing Setup** (1 day)
- [ ] **Stripe Product Configuration**
  - [ ] Create "ggbots Usage-Based Billing" product in Stripe
  - [ ] Create metered price ($1 per unit, quantity = dollars spent)
  - [ ] Set billing threshold: $20 OR monthly, whichever comes first

- [ ] **Subscription Management**
  - [ ] Implement `create_metered_subscription()` on user signup (requires credit card)
  - [ ] Add payment method requirement to signup flow
  - [ ] Update webhook handlers for metered invoices

- [ ] **Usage Reporting**
  - [ ] Create hourly background job to report usage to Stripe
  - [ ] Implement idempotency keys (timestamp-based)
  - [ ] Add Stripe usage record API integration
  - [ ] Mark usage records as reported in database

- [ ] **Payment Failure Handling**
  - [ ] Auto-pause all bots on payment failure
  - [ ] Send email notification to user
  - [ ] Auto-resume bots when payment resolved

### **Phase 3: Premium Subscription** (0.5 days)
- [ ] **Database Schema**
  - [ ] Add `premium_subscription_id`, `premium_tier_active` to user_profiles
  - [ ] Add `premium_base_allowance_usd`, `premium_base_allowance_used_usd`

- [ ] **Stripe Product**
  - [ ] Create "ggbots Pro - Agent Access" product ($100/month recurring)
  - [ ] Implement combined subscription (metered + fixed $100)
  - [ ] Add upgrade flow (add fixed item to existing metered subscription)

- [ ] **Base Allowance Logic**
  - [ ] Implement allowance calculation (e.g., $30 included with Pro)
  - [ ] Deduct allowance from billable usage before Stripe reporting
  - [ ] Reset allowance monthly

- [ ] **Permission Updates**
  - [ ] Add `can_use_agents` property to UserProfile
  - [ ] Update frontend agent creation gate (require Pro)
  - [ ] Determine other premium-only features

### **Phase 4: Usage Estimator** (1.5 days)
- [ ] **Backend Calculator**
  - [ ] Create `UsageEstimator` service
  - [ ] Calculate monthly executions from analysis_frequency
  - [ ] Estimate tokens per execution (historical avg or template-based)
  - [ ] Apply model pricing + 70% markup
  - [ ] Return range (low/high with ±25% variance)

- [ ] **API Endpoint**
  - [ ] `POST /api/v2/estimate-cost` (accepts bot config, returns estimate)
  - [ ] Support draft configs (not yet saved)

- [ ] **Frontend Integration**
  - [ ] Add cost estimator to bot creation/edit modal
  - [ ] Real-time updates as user changes model/frequency (debounced)
  - [ ] Display: "Estimated cost: $X-Y/month"

### **Phase 5: Usage Dashboard** (1 day)
- [ ] **Backend API**
  - [ ] `GET /api/v2/usage/current-month` (total, breakdown by bot/model, estimate)
  - [ ] `GET /api/v2/usage/history` (past N months)
  - [ ] `POST /api/v2/usage/set-hard-cap` (optional spending limit)

- [ ] **Frontend Component**
  - [ ] Create `UsageDashboard` component
  - [ ] Current month spend (big number)
  - [ ] Breakdown by bot (pie chart)
  - [ ] Breakdown by model (bar chart)
  - [ ] Historical trend (line chart, 6 months)
  - [ ] Hard cap settings (input + save)
  - [ ] Link to Stripe billing portal (invoices)

### **Phase 6: Alerts & Safeguards** (0.5 days)
- [ ] **Email Alerts**
  - [ ] Create `UsageAlertService`
  - [ ] Trigger alerts at $10, $20, $50, $100 thresholds
  - [ ] Resend email templates (usage_alert.html)
  - [ ] Hourly background job to check and send alerts

- [ ] **Hard Cap Enforcement**
  - [ ] Background job (every 5 min) to check hard caps
  - [ ] Auto-pause all bots when hard cap exceeded
  - [ ] Send email notification
  - [ ] Auto-resume when new billing cycle starts or cap raised

### **Testing & Launch** (2 days)
- [ ] **Stripe Test Mode**
  - [ ] Test subscription creation with credit card
  - [ ] Test usage reporting (send test records)
  - [ ] Test billing threshold (trigger $20 mid-cycle invoice)
  - [ ] Test payment failure flow (card decline)

- [ ] **End-to-End Flows**
  - [ ] New user: signup → add card → create bot → run → verify invoice
  - [ ] Existing user: upgrade to Premium → verify $100 + usage
  - [ ] Hard cap: set $10 cap → run bot → verify pause at limit

- [ ] **Launch Prep**
  - [ ] Create pricing page on ggbots.ai
  - [ ] Draft user communication (pricing changes)
  - [ ] Prepare FAQ/support docs
  - [ ] Switch Stripe to live mode
  - [ ] Deploy to production

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

### **User Settings & API Key Management**
- [ ] Complete API key management interface for LLM credentials
- [ ] Add secure credential storage using Supabase Vault
- [ ] Implement credential validation and testing
- [ ] Support OpenAI, DeepSeek, Anthropic, XAI credentials
- [ ] Add subscription downgrade workflow

### **Trading System Completeness**
- [ ] Verify SL/TP values read from configuration properly
- [ ] Verify trade monitoring triggers TP/SL execution automatically
- [ ] Validate risk management parameters enforced
- [ ] Implement open position limits per configuration

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
