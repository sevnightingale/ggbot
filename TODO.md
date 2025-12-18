# TODO.md - ggbots Implementation Plan

Active tasks and planned work. See CHANGELOG.md for completed features.

---

## 🚨 **CRITICAL - CVE-2025-66478 Secret Rotation**

**Status**: 🔴 URGENT - Application was vulnerable for ~11 hours (Dec 4-5, 2025)
**Planning Doc**: [DOCS/todo/CVE_2025_66478_SECRET_ROTATION.md](DOCS/todo/CVE_2025_66478_SECRET_ROTATION.md)

**Vulnerability**: Next.js/React Server Components RCE (CVSS 10.0)
- Application ran vulnerable Next.js 15.3.3 during exposure window
- Upgraded to patched 15.5.7 on Dec 5, 2025
- Per advisory: "rotate any secrets it uses, starting with your most critical ones"

**Action Required**: Follow rotation checklist in priority order
- [ ] **Day 1**: CRITICAL secrets (Supabase, Auth, Trading APIs)
- [ ] **Day 1-2**: HIGH PRIORITY secrets (AI APIs, Market Data, Email)
- [ ] **Week 1**: MEDIUM PRIORITY secrets (Admin, Redis, OAuth)

See planning doc for complete provider-specific instructions and verification steps.

---

## 🏆 **HIGH PRIORITY - ggArena Bot Preparation** (2025-12-18)

**Status**: 🟡 IN PROGRESS - 7 bots configured but need optimization before 21-day public competition
**Analysis Doc**: [ARENA_BOT_ANALYSIS.md](ARENA_BOT_ANALYSIS.md)

**Current State**:
- 7 arena bots identified (ggSignals, The Compass, The Arbiter, The Contrarian, The Herald, The Sentinel, The Nomad)
- All bots currently INACTIVE (making decisions but not executing trades)
- Only "The Technician (old)" active: 32 trades, 50% win rate, -$105.79 P&L
- Key issue: Some bots too conservative (1-3% confidence = 100% waits), Symphony integration not working

### **Task 1: Strategy Deep-Dive & Optimization** 🔍

**Goal**: Analyze decision patterns and improve strategy prompts for better trade execution

**The Technician Analysis** (Active bot, poor performance):
- [ ] Query last 50 decisions with full reasoning
- [ ] Identify pattern: Why 50% win rate despite 21 indicators?
- [ ] Analyze entry/exit timing (5m frequency = over-trading?)
- [ ] Check stop loss/take profit hit rates
- [ ] Review confidence distribution (55% avg = too low threshold?)
- [ ] Compare successful trades vs losing trades (indicators at entry)
- [ ] Recommend: Strategy refinements, frequency change, or indicator subset

**Low-Confidence Bots** (Herald 1%, Sentinel 3%, Arbiter 10%):
- [ ] Query sample "wait" decisions with reasoning
- [ ] Identify why confidence is so low (prompt wording? risk aversion? data quality?)
- [ ] Review strategy prompts for overly conservative language
- [ ] Test hypothesis: "when in doubt, wait" vs "when in doubt, trade" bias
- [ ] Recommend specific prompt changes to increase action bias

**ggSignals Analysis** (68% confidence but 0 trades):
- [ ] Query enter/exit decisions (91 enters, 17 exits in 7 days)
- [ ] Verify decision quality and reasoning patterns
- [ ] Confirm strong conviction = likely to succeed
- [ ] Check if Symphony integration is blocking execution (see Task 3)

**Deliverables**:
- Detailed decision pattern analysis for each bot
- Specific strategy prompt recommendations
- Confidence threshold recommendations
- Indicator effectiveness analysis (which ones correlate with wins?)

---

### **Task 2: Tune Conservative Bots for Arena Activity** ⚙️

**Goal**: Adjust prompts/configs so all bots will actually trade during 21-day competition

**The Herald** (30m, 1% confidence, 0/128 trades):
- [ ] Review current prompt for overly cautious language
- [ ] Add explicit "bias toward action" guidance
- [ ] Lower implicit confidence bar in reasoning
- [ ] Test: Activate for 24h, monitor if trades trigger
- [ ] Target: 20-30% confidence minimum, 20%+ action rate

**The Sentinel** (15m, 3% confidence, 0/261 trades):
- [ ] Current: "only trade when setup, trend, and confirmation align perfectly"
- [ ] Revise: "trade when 2 of 3 align with reasonable confidence"
- [ ] Remove "capital is sacred" language (creates fear)
- [ ] Add "taking calculated risks is part of trading"
- [ ] Test: Activate for 24h, verify trades execute
- [ ] Target: 10-15% confidence minimum, 15%+ action rate

**The Arbiter** (4h, 10% confidence, 0/16 trades):
- [ ] Review "weigh all evidence" prompt (analysis paralysis?)
- [ ] Add tiebreaker logic: "when evidence is mixed, trust momentum"
- [ ] Reduce required confluence from "all indicators" to "majority"
- [ ] Test: Activate for 24h
- [ ] Target: 40-50% confidence, 10%+ action rate

**The Contrarian** (1h, 13% confidence, 0/67 trades):
- [ ] Strategy may be fundamentally sound (waiting for extremes)
- [ ] Review: Are RSI/funding extremes actually occurring?
- [ ] Consider: Lower threshold for "extreme" (RSI <30/>70 instead of <20/>80)
- [ ] Add: "Minor extremes are still tradeable"
- [ ] Test: Activate for 24h
- [ ] Target: 30-40% confidence, 15%+ action rate

**The Nomad** (Agent, no strategy):
- [ ] Create initial agent strategy prompt
- [ ] Define: Autonomous market scanner, opportunity-driven
- [ ] Tools: query_market_data, execute_trade, record observations
- [ ] Guidance: "Scan for 7 symbols daily, trade best 2-3 setups"
- [ ] Test: Start agent for 24h
- [ ] Target: 2-5 trades/day

**General Tuning Principles**:
- Remove fear-based language ("capital is sacred", "only when perfect")
- Add action-bias language ("when in doubt, trust the setup")
- Lower confidence thresholds implicitly via prompt tone
- Add explicit tiebreaker rules for mixed signals
- Test each bot 24h before competition starts

---

### **Task 3: Symphony Integration Debug** 🔌

**Status**: BLOCKED - ggSignals making 91 enter decisions but 0 trades executing

**Issue**: Symphony trades may be executing on Symphony side, but API calls failing to track/record them

**Investigation Steps**:
- [ ] Check Symphony credentials configured for user
  - Query: `SELECT symphony_vault_id, symphony_smart_account FROM user_profiles WHERE user_id = '<admin_id>'`
  - Verify vault decryption works
- [ ] Check ggSignals paper account vs Symphony account
  - Bot config shows `trading_mode='symphony'` but `paper_accounts` table has $10k
  - Verify: Does Symphony mode use paper_accounts or live_trades table?
- [ ] Review Symphony service execution logs
  - Check: `pm2 logs ggbot | grep -i symphony`
  - Look for: API call failures, auth errors, position creation failures
- [ ] Test manual Symphony trade via API
  - Call: `POST /api/v2/agent/execute-trade` with ggSignals config_id
  - Verify: Trade executes on Symphony + records in live_trades table
- [ ] Check decision → trade linking
  - Query: ggSignals decisions with `decision_id` vs `live_trades.decision_id`
  - Expected: 91 enter decisions should create 91 live_trades records (if conditions met)
- [ ] Review Symphony service code
  - File: `trading/live/symphony_service.py`
  - Check: execute_trade() method, error handling, batch_id creation
  - Verify: live_trades INSERT after Symphony API success
- [ ] Check symbol compatibility
  - BTC/USDT should be Symphony-compatible (verify in registry)
  - Check: Symbol conversion BTC/USDT → Symphony format
- [ ] API endpoint investigation
  - File: `ggbot.py` orchestrator
  - Check: Does scheduled_trading + symphony mode route to Symphony service?
  - Expected flow: decision engine → trading router → symphony_service.execute_trade()

**Potential Issues**:
1. Symphony credentials not configured (vault_id NULL)
2. Decision confidence < execution threshold (but 68% seems high enough)
3. Position sizing calculation failing
4. Symphony API authentication failing silently
5. Orchestrator not routing Symphony bots correctly
6. live_trades table constraint preventing INSERTs

**Testing Plan**:
- [ ] Activate ggSignals for 1 hour (test mode)
- [ ] Monitor logs in real-time: `pm2 logs ggbot --lines 100`
- [ ] Verify: Decision made → Trade execution attempted → Result logged
- [ ] Check: Any error messages in logs?
- [ ] Query live_trades table after 1 hour: Any new records?

**Fix Actions** (TBD based on findings):
- [ ] Configure Symphony credentials if missing
- [ ] Fix position sizing if failing
- [ ] Add error handling/logging if silent failures
- [ ] Update orchestrator routing if misconfigured
- [ ] Update documentation on Symphony mode behavior

**Success Criteria**:
- ggSignals makes decision with action='enter'
- Symphony API receives trade request
- Trade executes on Symphony (visible in Symphony dashboard)
- live_trades table records new entry with provider='symphony'
- Decision links to trade via decision_id

---

## ✅ **DEPLOYED - Strategy Advisor (Character Creation UX)** (2025-12-05)

**Status**: 🟢 PRODUCTION READY - Onboarding-focused prompt deployed

### **Implementation Complete**
- [x] Backend API endpoint: `POST /api/v2/assistant/chat`
- [x] Claude Haiku 4.5 function calling with 3 tools
- [x] **NEW**: Adaptive prompt with 4 scenarios (character creation, educational translator, thesis exploration, efficiency mode)
- [x] **NEW**: Experience-level detection (beginner/intermediate/advanced)
- [x] **NEW**: Strategy clarity detection (no idea/vague/specific)
- [x] Bot-type aware system prompts (agent, scheduled, signal_validation)
- [x] Frontend bottom sheet component (UniversalAIAssistant.tsx)
- [x] Framer-motion draggable/collapsible UI
- [x] Integrated into Forge configure pages
- [x] Auto-refreshes config on AI updates
- [x] Build test passing (TypeScript, ESLint clean)

### **Character Creation Approach**
For beginners with no strategy:
- "Let's create your bot's personality!"
- Evocative questions: patient vs aggressive, trust crowd vs fade, react to news vs ignore noise
- Personality archetypes: The Contrarian, Momentum Rider, Patient Sniper
- Bot naming encouraged
- Translates personality into executable strategy

### **Features**
- Works for ALL 3 bot types (agent, scheduled, signal_validation)
- Adapts conversation based on user experience + strategy clarity
- Query 32 available data points across 7 categories
- Load and update full bot configurations
- Deep merge for partial updates (update just one field)
- Cost: ~$0.016 per session (~$16/month for 1000 users)
- Technical accuracy: reasoning_tier (economy/standard/premium), 7 model families

### **Next Steps**
- [ ] Test on production (Vercel deployment) with new prompt
- [ ] Monitor Claude API costs and usage
- [ ] Gather user feedback on character creation UX
- [ ] A/B test conversion rates (form-based vs character creation)
- [ ] Consider adding conversation persistence (Redis cache)

### **Files Created/Modified**
- `api/assistant.py` - Main chat endpoint with function calling
- `frontend/components/UniversalAIAssistant.tsx` - Bottom sheet UI
- `frontend/app/forge/page.tsx` - Integration with configure pages
- `DOCS/todo/strategy_builder_api.md` - Planning documentation
- `DOCS/archived/strategy_builder_agent_complex.md` - Old complex approach (archived)

---

## ✅ **COMPLETE - Admin Dashboard** [ADMIN_DASHBOARD.md]

**Status**: 🟢 COMPLETE (2025-12-05)
**Planning Doc**: [DOCS/todo/ADMIN_DASHBOARD.md](DOCS/todo/ADMIN_DASHBOARD.md)

**Summary**: Internal admin dashboard at `/admin` for platform management, restricted to admin user ID.

### **Implementation Complete**
- [x] Backend: `api/admin.py` with 14 endpoints (1084 lines)
- [x] Platform stats: users, bots, trades, P&L, health
- [x] PM2/VM/Redis monitoring with services table
- [x] Billing overview: token usage, provider vs platform costs, unreported amounts
- [x] User management: search by email, view/edit subscription tiers
- [x] User detail page: editable fields, bot controls, token usage per bot
- [x] Bot control: start/stop any bot, reset paper accounts
- [x] Config editing: JSONB preview (form-based editor deferred)
- [x] Bot performance comparison: equity curves chart (2025-12-14)
- [x] Frontend: 4 pages with manual refresh
- [x] Security: JWT → admin ID check → service role
- [x] Environment variables set (ADMIN_USER_ID, NEXT_PUBLIC_ADMIN_USER_ID)
- [x] Build passing, deployed to production

### **Files Created**
- `api/admin.py` - 14 admin endpoints (~1084 lines)
- `frontend/app/admin/layout.tsx` - Admin auth check
- `frontend/app/admin/page.tsx` - Dashboard overview
- `frontend/app/admin/users/page.tsx` - User search + list
- `frontend/app/admin/users/[user_id]/page.tsx` - User detail + edit
- `frontend/app/admin/bots-comparison/page.tsx` - Bot equity comparison chart

### **Next Steps (Optional)**
- [ ] Form-based config editor (currently shows JSON preview)
- [ ] Audit logging for admin actions
- [ ] Multiple admin user support

---

## 🎲 **USX Staking Modal - Bot Competition Betting**

**Status**: 🔵 PLANNING
**Planning Doc**: [DOCS/todo/USX_STAKING_MODAL.md](DOCS/todo/USX_STAKING_MODAL.md)
**Complexity**: Medium (~6-8 hours)

**Summary**: Gamification feature allowing users to stake USX (Scroll stablecoin) on which bot they think will win competitions. Standard Scroll staking (USX→sUSX) + simple DB record of bot choice. Competition logic deferred.

### **Elegant Architecture**
- Users stake normally via Scroll's USX/sUSX system (no custom contracts)
- Modal records: `{ user_id, wallet_address, config_id, usx_amount, tx_hash }`
- Single table: `usx_stakes`
- All competition logic (winners, prizes, leaderboards) added later

### **User Flow**
1. Click "Stake on Bot" → Modal opens
2. Connect wallet (RainbowKit)
3. Select bot to back (dropdown)
4. Enter USX amount
5. Execute 2 txs: approve + deposit to sUSX vault
6. Record stake in DB
7. User earns base yield (worst case) + prize if bot wins (best case)

### **Implementation Phases**

**Phase 1: Research & Setup** (~1 hour)
- [ ] Find USX/sUSX contract addresses on Scroll mainnet (docs.usx.capital, Scrollscan)
- [ ] Get WalletConnect Project ID (cloud.walletconnect.com)
- [ ] Install deps: `wagmi`, `viem`, `@rainbow-me/rainbowkit`, `@tanstack/react-query`
- [ ] Set up wagmi config with Scroll chain

**Phase 2: Database & Backend** (~1 hour)
- [ ] Create `usx_stakes` table (user_id, wallet_address, config_id, usx_amount, tx_hash)
- [ ] Add `POST /api/v2/usx/stake` endpoint (record stake after on-chain tx)
- [ ] Add `GET /api/v2/usx/stakes` endpoint (list user stakes)

**Phase 3: Frontend Web3 Integration** (~2-3 hours)
- [ ] Wrap app in WagmiProvider + RainbowKitProvider + QueryClientProvider
- [ ] Create contract constants (`lib/contracts.ts` with USX/sUSX addresses + ABIs)
- [ ] Build StakingModal component with wallet connect, bot selector, amount input
- [ ] Test wallet connection and balance reading

**Phase 4: On-Chain Integration** (~2-3 hours)
- [ ] Implement approve transaction (USX.approve → sUSX vault)
- [ ] Implement deposit transaction (Vault.deposit → receive sUSX)
- [ ] Add transaction waiting/success/error states
- [ ] Test on Scroll mainnet with small amounts

**Phase 5: UI Integration** (~1 hour)
- [ ] Add "Stake on Bot" trigger (location TBD)
- [ ] Integrate modal with existing UI
- [ ] End-to-end testing
- [ ] Deploy to Vercel

### **Deferred (Future Work)**
- Competition logic (winners, prize distribution)
- Leaderboard UI
- Competition admin interface
- Public competition pages

**Why defer**: Already have bot performance tracking via `account_snapshots`. Can determine winners retroactively. Staking mechanism is the hard part.

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

## ✅ **COMPLETE - Strategy Advisor Unification & Agent Cleanup** [STRATEGY_UNIFICATION.md]

**Status**: 🟢 COMPLETE (2025-12-04)
**Planning Doc**: [DOCS/todo/STRATEGY_UNIFICATION.md](DOCS/todo/STRATEGY_UNIFICATION.md)

**Goal**: Unify configuration experience across all bot types using the existing Strategy Advisor API. Remove old PM2-based strategy_definition mode and consolidate strategy fields.

### **Summary of Changes**
- Agent bots now use the same `ConfigureLayout` + `StrategyAdvisorPanel` as scheduled bots
- Strategy saved to `decision.user_prompt` for ALL bot types (agent_strategy deprecated)
- `strategy_definition` mode deprecated in both API and agent runner
- AgentConfigurator.tsx deleted (old PM2 + Redis polling approach)
- Build passes ✓

### **Phase 1: Frontend Unification** ✅
- [x] **Update ConfigureLayout.tsx** - Added `AgentStrategySection` component, agent mode shows simplified UI
- [x] **Update page.tsx** - Removed AgentConfigurator routing, cleaned up agent state variables
- [x] **Delete AgentConfigurator.tsx** - Removed entirely

### **Phase 2: Strategy Field Consolidation** ✅
- [x] **Update api/assistant.py** - Now only updates `decision.user_prompt`, agent_strategy deprecated

### **Phase 3: Backend Cleanup** ✅
- [x] **Update api/agent.py** - Returns 400 error for strategy_definition mode, always uses autonomous
- [x] **Update agent/run_agent.py** - Raises ValueError if strategy_definition mode requested

### **Phase 4: Documentation & Testing** ✅
- [x] **Update agent/README.md** - Documented new architecture, marked strategy_definition as deprecated
- [x] **Build test** - Frontend build passes

### **Files Modified**
| File | Changes |
|------|---------|
| `frontend/app/forge/components/configure/ConfigureLayout.tsx` | Added AgentStrategySection, conditional rendering |
| `frontend/app/forge/page.tsx` | Removed AgentConfigurator routing, cleaned agent state |
| `frontend/app/forge/components/configure/AgentConfigurator.tsx` | DELETED |
| `api/assistant.py` | Updated to use decision.user_prompt, deprecated agent_strategy |
| `api/agent.py` | Returns 400 for strategy_definition mode |
| `agent/run_agent.py` | Raises error for strategy_definition mode |
| `agent/README.md` | Updated documentation |

### **Remaining Work (Future)**
- [ ] Remove `agent_strategy` column from configurations table (after verifying no usage)
- [ ] Clean up Redis endpoints `/message`, `/poll-response` (kept for now)
- [ ] Production testing of agent configuration flow

---

## 📚 **Documentation - Prompt System Architecture Review**

**Status**: 🟡 NEEDS REVIEW
**Planning Doc**: [DOCS/todo/PROMPT_SYSTEM_ARCHITECTURE.md](DOCS/todo/PROMPT_SYSTEM_ARCHITECTURE.md)

**Summary**: Comprehensive analysis of prompt generation system, trade settings integration, and position management flows.

### **Documentation Complete**
- [x] Output format instructions (exact LLM requirements)
- [x] Trade settings integration (leverage, position sizing, SL/TP defaults)
- [x] Position management mode (routing, data fetching, formatting)
- [x] Complete flow diagrams (opportunity analysis + position management)
- [x] Key design insights (separation of concerns, context continuity)
- [x] 8 potential improvements identified

### **Review Tasks**
- [ ] Read complete documentation (PROMPT_SYSTEM_ARCHITECTURE.md)
- [ ] Evaluate proposed improvements for priority/feasibility
- [ ] Decide if any improvements should move to active development
- [ ] Update system documentation if architecture changes are planned

### **Potential Improvements to Consider**
1. Add risk context to prompts (leverage, defaults visible to LLM)
2. Dynamic TP/SL defaults based on volatility/timeframe
3. Implement SL/TP trailing updates (currently LLM can suggest but system doesn't apply)
4. Multi-position portfolio management
5. Performance classification granularity improvements
6. Feedback loop for default applications
7. Structured output format (JSON schema)
8. Portfolio context in opportunity analysis

---

## 🏆 **AsterDEX - Production Hardening**

**Status**: ✅ Core implementation complete, needs production hardening and testing

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

## 🪙 **Symphony Spot Trading - Monad (MON) Integration**

**Status**: ⏸️ BLOCKED - Waiting for Symphony API deployment

**Planning Doc**: [DOCS/symphony_spot_integration.md](DOCS/symphony_spot_integration.md)
**Test Report**: [DOCS/symphony_spot_test_report.md](DOCS/symphony_spot_test_report.md)

### **Overview**
Symphony has launched spot trading support on Monad testnet for token swaps (not perpetuals). Integration is ready but waiting for API endpoints to go live.

**MON Details**:
- Chain: Monad (new Layer 1)
- SID: 10056
- Trading: Spot swaps only (no perps)
- Status: Testnet active, eligible for trading rewards

### **Current Blocker**
Both spot trading endpoints return 404 (not deployed yet):
- `GET /token/price` - Token price lookup (public)
- `POST /agent/swap` - Execute spot swaps (auth required)

**Symphony perp endpoints work perfectly** - credentials validated, 6 open positions found.

### **Prepared Assets** ✅
All test scripts and documentation complete, ready to run once APIs available:

**Test Scripts** (4 files created):
- [x] `trading/live/symphony_price_test.py` - Token price testing
- [x] `trading/live/symphony_swap_test.py` - Spot swap execution
- [x] `trading/live/symphony_endpoint_discovery.py` - Auto-discovery
- [x] `trading/live/symphony_connectivity_test.py` - Credential validation ✅

**Documentation**:
- [x] Complete 5-phase integration plan
- [x] Architecture decisions (separate service, reuse live_trades table)
- [x] Symbol registry design (symphony_spot_compatible flag)
- [x] Agent MCP tool specifications

### **Integration Phases** (Once APIs Available)

**Phase 1: Testing** (~30 min)
- [ ] Run `symphony_price_test.py` to validate token price endpoint
- [ ] Verify MON SID = 10056
- [ ] Run `symphony_swap_test.py` to test swap execution
- [ ] Test MON → USDC and USDC → MON swaps
- [ ] Verify batchId tracking works

**Phase 2: Symbol Registry** (~15 min)
- [ ] Add MON to `core/symbols/registry.py`
- [ ] Add `symphony_spot_compatible` flag
- [ ] Add `sid` field (10056)
- [ ] Add `chain` field ("monad")
- [ ] Update standardizer with `is_symphony_spot_compatible()` method
- [ ] Update standardizer with `get_symphony_sid()` method

**Phase 3: Spot Trading Service** (~2-3 hours)
- [ ] Create `trading/live/symphony_spot_service.py`
- [ ] Implement `get_token_price()` method (public API)
- [ ] Implement `execute_swap()` method (auth required)
- [ ] Implement `calculate_swap_pnl()` for P&L tracking
- [ ] Add swap history queries (if API supports)
- [ ] Extend `live_trades` table with `provider='symphony_spot'`
- [ ] Test end-to-end swap execution

**Phase 4: Bot Configuration** (~2-3 hours)
- [ ] Extend `trading_mode` to include `'symphony_spot'`
- [ ] Update decision engine to handle spot signals (Buy → USDC→MON, Sell → MON→USDC)
- [ ] Implement inventory tracking (track MON vs USDC holdings)
- [ ] Add frontend trading mode selector option
- [ ] Update symbol selector to show only spot-compatible symbols
- [ ] Remove leverage/SL/TP fields for spot mode in settings

**Phase 5: Agent Integration** (~1-2 hours)
- [ ] Create `execute_spot_swap` MCP tool
- [ ] Update agent system prompt with spot trading capabilities
- [ ] Add inventory management to agent strategy
- [ ] Test autonomous spot trading
- [ ] Verify activity logging for swaps

### **Next Actions**
- [ ] Contact Symphony team to ask:
  - When will `/token/price` and `/agent/swap` be deployed?
  - Is there a testnet/staging URL for early testing?
  - Do spot endpoints require different auth (Privy vs API key)?
  - What's the ETA for Monad spot trading going live?
- [ ] Monitor Symphony Discord/docs for deployment announcements
- [ ] Test endpoints periodically for availability

**Estimated Time**: 6-9 hours once APIs are deployed (all groundwork complete)

**Files Created**:
- `trading/live/symphony_price_test.py`
- `trading/live/symphony_swap_test.py`
- `trading/live/symphony_endpoint_discovery.py`
- `trading/live/symphony_connectivity_test.py`
- `DOCS/symphony_spot_integration.md`
- `DOCS/symphony_spot_test_report.md`

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

### **Legal & Compliance** ✅ COMPLETE
- [x] Terms of Service page (/terms)
- [x] Privacy Policy page (/privacy)
- [x] Footer component with legal links
- [x] Signup page disclaimer
- [x] Live trading risk acknowledgment modal

### **Public Performance Features**
**Dependencies**: ✅ RLS migration ready in `SQL.md` - see System Improvements → Security

**Architecture Decided**:
- Per-bot privacy control via `configurations.is_public_performance`
- No usernames shown (just bot names)
- All activities public when opted in (trades, thoughts, market queries)
- Public arena shows: Bot Name | Mode | P&L | Win Rate | Trades

Implementation tracked under **System Improvements → Security → Backend API Updates** and **Frontend Implementation** sections.

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

