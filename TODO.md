# TODO.md - ggbots Implementation Plan

Active tasks and planned work. See CHANGELOG.md for completed features.

---

## 🏆 **CRITICAL - ggArena Season 1 Launch**

**Status**: 🔴 URGENT - Launch tweet Jan 8, Season 1 starts Jan 21
**Planning Doc**: [DOCS/todo/GGARENA_SEASON1_LAUNCH.md](DOCS/todo/GGARENA_SEASON1_LAUNCH.md)

**Competition Details**:
- **Dates**: Jan 21 12:00 UTC → Feb 11 12:00 UTC (21 days)
- **Prize Pool**: $2,500 in USX on Scroll
- **Top 3**: Also get funded live trading on Symphony
- **Winning Criteria**: Highest equity after 21 days
- **Eligibility**: Active bots with usage-based subscription

### **Phase 1: Tonight (Jan 7) - Launch Prep** ✅ COMPLETE

**Arena Page Updates**:
- [x] Update hero copy: Season 1 framing, $2,500 prize pool, dates
- [x] Add countdown timer component (to Jan 21 12:00 UTC)
- [x] Reframe prototype bots as "Training Ground" / examples
- [x] Update hardcoded dates (Dec 18 - Jan 8) → (Jan 21 - Feb 11)
- [ ] Add "Registered Competitors" section (for future registrations)

**Registration Mechanism**:
- [x] Create `POST /api/v2/bot/{config_id}/arena/register` endpoint
- [x] Validate: user owns bot, bot active, user subscribed
- [x] Set `is_public_performance = true` on registration
- [x] Create registration confirmation modal (frontend)
- [x] Add "Enter Arena" button to bot config page

**Navigation & Branding**:
- [x] Add ggArena link to navbar
- [x] Add banner message about Season 1 (Jan 21st)
- [ ] Update logo everywhere
- [ ] Update favicon

### **Phase 2: Critical Polish (Tonight/Tomorrow)** ✅ COMPLETE

- [x] Fix duplicate and reset buttons (missing config_type, UI not refreshing)
- [x] Fix "Setting up your ggbot" message (shows when no bots exist, misleading)
- [x] Remove "free" labels from bot creation modal (usage-based now)
- [x] Fix theme/light mode issues (strategy advisor buttons, image upload icon)
- [x] Remove floating question mark helper icon
- [x] Add socials to header + landing footer (Twitter/X, Telegram)
- [x] Arena page performance fix (countdown timer isolated, removed heavy ArenaTimeline)
- [x] Arena page UX overhaul (How It Works, Leaderboard, prize breakdown, varied CTAs)
- [x] Arena CTAs link to app.ggbots.ai (direct to app, not landing)

### **Phase 3: Before Jan 21**

**Infrastructure**:
- [ ] Create `scripts/arena_reset.py` - bulk reset all registered bots to $10k
- [ ] Test reset script on staging
- [ ] Add `arena_registered_at` timestamp column (optional)

**Communications**:
- [ ] Draft launch email for ggbots v2 + ggArena announcement
- [ ] Draft Telegram post for same
- [ ] Post launch tweet + video (Jan 8)

**Polish**:
- [ ] Fix Google auth showing Supabase project ID
- [ ] Update x-bot to different account

### **Phase 4: Future (Post-Launch)**

- [ ] Inline arena bot creation modal (components exist, just need flow)
- [ ] Full onboarding flow reassessment

### **Open Questions**
1. Late registrations after Jan 21 - allow with fresh $10k?
2. Should Sev's 7 prototype bots compete in Season 1?
3. Multiple bots per user - allowed?

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

## 🔧 **API Extraction Refactor - Scheduler Process Separation**

**Status**: 🔴 CRITICAL - Production 502s during bot execution
**Planning Doc**: [DOCS/todo/API_EXTRACTION_REFACTOR.md](DOCS/todo/API_EXTRACTION_REFACTOR.md)
**Complexity**: High (~64 hours / 5 weeks)
**Priority**: P0 - Blocking user experience

**Problem**: ggbot.py is 4345-line monolith with FastAPI + APScheduler in same process. Long-running LLM calls (10-30s) during bot execution block event loop, causing 502 errors on API endpoints and SSE stream disconnects.

**Solution**: Split into two independent processes:
- `ggbot-api.py` - FastAPI server (port 8000)
- `ggbot-scheduler.py` - APScheduler bot execution (no HTTP)

**Communication**: Redis pub/sub for instant updates, DB polling fallback

### **Implementation Phases**

**Phase 1: Extract Orchestrator** (~4 hours, Low Risk)
- [ ] Create `core/orchestrator/orchestrator.py`
- [ ] Move GGBotOrchestrator class (lines 312-1177)
- [ ] Update imports in ggbot.py
- [ ] Run integration tests

**Phase 2: Extract Scheduler Logic** (~6 hours, Medium Risk)
- [ ] Create `core/orchestrator/scheduler.py`
- [ ] Move APScheduler functions (lines 1188-1388)
- [ ] Test scheduler startup/shutdown
- [ ] Verify bot lifecycle endpoints

**Phase 3: Add Lifecycle Communication** (~8 hours, Medium Risk)
- [ ] Create `core/orchestrator/lifecycle.py`
- [ ] Add `next_run_at` column to configurations table
- [ ] Implement Redis pub/sub (bot_lifecycle channel)
- [ ] Update scheduler to write next_run_at to DB
- [ ] Test Redis message passing

**Phase 4: Create Scheduler Process** (~10 hours, High Risk)
- [ ] Create `ggbot-scheduler.py`
- [ ] Implement Redis lifecycle listener
- [ ] Implement DB reconciliation loop (5min interval)
- [ ] Add health check endpoint (port 8001)
- [ ] Test standalone execution

**Phase 5: Create API Process** (~12 hours, High Risk)
- [ ] Create `ggbot-api.py` (all endpoints, no scheduler)
- [ ] Update bot lifecycle endpoints (notify_scheduler_*)
- [ ] Update /api/v2/scheduler/status (read from DB)
- [ ] Test all 60+ endpoints
- [ ] Verify SSE stream stability

**Phase 6: Integration Testing** (~16 hours, High Risk)
- [ ] Update PM2 configuration (two processes)
- [ ] Deploy to staging environment
- [ ] Stress test: 50+ concurrent bot executions
- [ ] Test scheduler crash recovery
- [ ] Verify no 502s during peak execution
- [ ] Monitor API latency (<100ms target)

**Phase 7: Production Deployment** (~8 hours, Medium Risk)
- [ ] Update ACTIVE.md documentation
- [ ] Create rollback plan (monolith fallback)
- [ ] Deploy during off-peak (03:00 UTC)
- [ ] Monitor for 24 hours
- [ ] Verify all active bots running

### **Success Metrics**
- API p99 latency: <100ms during bot execution (currently 3-10s)
- 502 errors: 0 during peak hours (currently 10-20/hour)
- SSE stream uptime: 99.9% (currently 95%)
- Bot execution success rate: >98% (no regression)

### **Rollback Plan**
If issues detected: Stop new processes, restore `ggbot.py` monolith via PM2. Expected recovery: 5 minutes.

---

## 🎲 **USX Staking Modal - Bot Competition Betting**

**Status**: 🔵 PLANNING
**Planning Doc**: [DOCS/todo/USX_STAKING_MODAL.md](DOCS/todo/USX_STAKING_MODAL.md)
**Complexity**: Medium (~6-8 hours)

**Summary**: Gamification feature allowing users to stake USX (Scroll stablecoin) on which bot they think will win competitions. Standard Scroll staking (USX→sUSX) + simple DB record of bot choice. Competition logic deferred.

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

---

## 🎨 **Activity Modal Redesign** [ACTIVITY_MODAL_REDESIGN.md]

**Status**: 🟢 COMPLETE
**Planning Doc**: [DOCS/todo/ACTIVITY_MODAL_REDESIGN.md](DOCS/todo/ACTIVITY_MODAL_REDESIGN.md)

**Problem**: Bottom sheet for activity details was poor UX - unformatted text blobs, no navigation between activities, mobile-unfriendly.

**Solution**: Centered modal with carousel navigation + structured LLM output formatting.

### **Phase 1: Modal Component (COMPLETE)**

- [x] Created `activity-modal.tsx` - centered modal with swipe/arrow navigation
- [x] Type-specific formatters (trade_entry, trade_exit, llm_thought, market_query)
- [x] Integrated with tv-timeline.tsx, replaced bottom-sheet

### **Phase 2: LLM Output Restructure (COMPLETE)**

- [x] Updated all 3 prompts with structured REASONING format (KEY_SIGNAL, SUPPORTING, RISK, SUMMARY)
- [x] Frontend parses structured sections with graceful fallback to raw text
- [x] No backend parser changes needed (frontend-only parsing)

---

## 📊 **Strategy Advisor Analysis** [STRATEGY_ADVISOR_ANALYSIS.md]

**Status**: 🟢 COMPLETE
**Planning Doc**: [DOCS/todo/STRATEGY_ADVISOR_ANALYSIS.md](DOCS/todo/STRATEGY_ADVISOR_ANALYSIS.md)
**Completed**: 2026-01-04

**Problem**: Users had no automated way to understand why their bot wins or loses.

**Solution**: Universal performance analysis with pattern correlation and AI-synthesized recommendations.

### **What Was Built**
- [x] `core/services/performance_analyzer.py` - Universal analysis engine
- [x] Basic stats: win rate, P&L, R:R ratio, breakeven WR
- [x] Direction analysis: long vs short performance
- [x] Universal pattern extraction from all market_query data types
- [x] Pattern combination analysis (2-pattern combos, confirmation vs risk)
- [x] Timeframe alignment analysis
- [x] Exit reasoning classification (thesis_complete, trend_override, etc.)
- [x] Confidence calibration (expected vs actual win rates)
- [x] Claude Haiku LLM synthesis for recommendations
- [x] Exit analysis caveat (LLM instructed: no counterfactual data for early exits)
- [x] `/api/v2/assistant/analyze/{config_id}` endpoint
- [x] Two buttons: "Create Strategy" (always), "Analyze Performance" (when trades exist)
- [x] "Discuss with Strategy Advisor" sends report summary to chat

---

## ⏸️ **BLOCKED - External Dependencies**

### Symphony Live Trading Integration

**Status**: BLOCKED - Waiting for Symphony API fix

**Blocker**: Symphony `/agent/all-positions` endpoint returns 404 (documented but not implemented)

**Our Work (Once API Fixed - ~2.5 hours)**:
- [ ] Add `get_account_summary()` method to Symphony service
- [ ] Add Symphony branches to 5 agent endpoints
- [ ] Update system prompt with Symphony capabilities
- [ ] Test end-to-end with real credentials

### Symphony Spot Trading - Monad (MON)

**Status**: BLOCKED - Waiting for Symphony API deployment

Both spot trading endpoints return 404 (not deployed yet):
- `GET /token/price` - Token price lookup
- `POST /agent/swap` - Execute spot swaps

All test scripts and documentation ready. See [DOCS/symphony_spot_integration.md](DOCS/symphony_spot_integration.md).

### Market Maker - Kuru Integration

**Status**: WAITING - Module complete, needs Kuru API launch

**What's Ready**:
- [x] Core Avellaneda-Stoikov engine (~900 lines)
- [x] Simulation tested (+0.20% P&L, inventory management working)
- [x] Exchange adapter interface
- [x] Kuru adapter template (needs real API docs)

**Next Steps (When Kuru Launches)**:
- [ ] Register on Kuru platform, get API credentials
- [ ] Update KuruAdapter with actual endpoints/auth
- [ ] Test with small capital ($100-200 orders, $2k capital)
- [ ] Production deployment if successful

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

## 📚 Documentation References

- **New Claude Code Instances**: `GO.md` - Start here for onboarding
- **Current Status**: `ACTIVE.md` - Production system status
- **Complete History**: `CHANGELOG.md` - All completed features and fixes
- **Architecture**: `README.md` - Platform overview
