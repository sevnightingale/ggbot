# TODO.md - ggbots Implementation Plan

Active tasks and planned work. See CHANGELOG.md for completed features.

---

## 🏆 **ggArena Season 1** - 🟢 LIVE

**Status**: Competition running Jan 21 12:00 UTC → Feb 11 12:00 UTC
**Planning Doc**: [DOCS/completed/GGARENA_SEASON1_LAUNCH.md](DOCS/completed/GGARENA_SEASON1_LAUNCH.md)

**Competition Details**:
- **Dates**: Jan 21 12:00 UTC → Feb 11 12:00 UTC (21 days)
- **Prize Pool**: $2,500 in USX on Scroll
- **Top 3**: Also get funded live trading on Symphony
- **33 bots competing** (updated 2026-01-26), all reset to $10k at launch

**Remaining Work**:
- [ ] Update x-bot to different account
- [ ] Inline arena bot creation modal (optional, future)
- [ ] Add "Registered Competitors" section (optional, future)

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

## 🎲 **USX Staking Modal - Arena Pledging** [CC-B]

**Status**: 🟡 IN PROGRESS (parallel with CC-A)
**Planning Doc**: [DOCS/todo/USX_STAKING_MODAL.md](DOCS/todo/USX_STAKING_MODAL.md)
**Coordination**: See `CONTEXT.md` for cross-session coordination
**Complexity**: Medium (~5-6 hours)
**Assigned**: CC-B (USX Session)

**Summary**: Gamification feature allowing users to pledge USX (Scroll stablecoin) on which bot they think will win competitions. Web3 code is **scoped to Arena page only** to avoid bloating rest of app.

### **Architecture Decision**
```
Web3 providers (wagmi/rainbowkit) are LAZY-LOADED on Arena page only.
- Forge page: 0KB Web3 overhead
- Arena page: ~65KB loaded only when visiting /arena
- React Query at root level (CC-A handles this)
```

### **User Flow**
1. Visit Arena page → Click "Pledge USX" on bot card
2. Connect wallet (RainbowKit modal)
3. Enter USX amount, see balance
4. Execute 2 txs: approve + deposit to sUSX vault
5. Record pledge in DB
6. User earns sUSX yield (worst case) + prize share if bot wins (best case)

### **Implementation Phases**

**Phase 1: Research & Setup** (~1 hour)
- [ ] Find USX/sUSX contract addresses on Scroll mainnet (docs.usx.capital, Scrollscan)
- [ ] Get WalletConnect Project ID (cloud.walletconnect.com)
- [ ] Install deps (Arena scope): `wagmi`, `viem`, `@rainbow-me/rainbowkit`
- [ ] Create `frontend/lib/wagmi-config.ts` with Scroll chain

**Phase 2: Arena Page Architecture** (~1 hour)
- [ ] Create `frontend/components/arena/ArenaWithStaking.tsx` (provider wrapper)
- [ ] Update `frontend/app/arena/page.tsx` to lazy-load with `dynamic()`
- [ ] Create `frontend/lib/contracts.ts` with USX/sUSX addresses + ABIs
- [ ] Test wallet connection works on Arena page only

**Phase 3: Database & Backend** (~1 hour)
- [ ] Create `arena_pledges` table (user_id, wallet_address, config_id, usx_amount, tx_hash)
- [ ] Add `POST /api/v2/arena/pledge` endpoint
- [ ] Add `GET /api/v2/arena/pledges` endpoint

**Phase 4: PledgeModal Component** (~2-3 hours)
- [ ] Build `frontend/components/arena/PledgeModal.tsx`
- [ ] Bot selector dropdown (arena bots only)
- [ ] Amount input with USX balance display
- [ ] Implement approve + deposit transactions
- [ ] Transaction progress overlay (Approving → Pledging → Done)
- [ ] Success state with tx link
- [ ] Theme RainbowKit to match brass palette

**Phase 5: Integration & Testing** (~1 hour)
- [ ] Add "Pledge USX" button to Arena leaderboard bot cards
- [ ] End-to-end test on Scroll mainnet with small amounts
- [ ] Communicate 15-day unstaking cooldown in UI
- [ ] Deploy to Vercel

### **Key Files (CC-B owns these)**
- `frontend/lib/wagmi-config.ts` (NEW)
- `frontend/lib/contracts.ts` (NEW)
- `frontend/components/arena/ArenaWithStaking.tsx` (NEW)
- `frontend/components/arena/PledgeModal.tsx` (NEW)
- `frontend/app/arena/page.tsx` (modify for lazy-load)
- `api/public.py` or `ggbot.py` (pledge endpoints)
- Database migration for `arena_pledges`

---

## ⚡ **Frontend Performance - React Query & Arena Caching** [CC-A]

**Status**: 🟡 IN PROGRESS (parallel with CC-B)
**Planning Doc**: [DOCS/todo/FRONTEND_PERFORMANCE_REACT_QUERY.md](DOCS/todo/FRONTEND_PERFORMANCE_REACT_QUERY.md)
**Coordination**: See `CONTEXT.md` for cross-session coordination
**Complexity**: Low-Medium (~3-4 hours)
**Assigned**: CC-A (Snappiness Session)

**Problem**: Arena page and Forge page feel sluggish due to no caching, re-fetches on every visit, and heavy chart rendering.

**Solution**:
1. Add React Query at root level (benefits all pages)
2. Add Redis caching to Arena endpoint (instant loads)
3. Convert Forge to use React Query hooks (Phase 3, after testing)

### **Phase 1: Foundation** (~1 hour) 🟡 IN PROGRESS

- [ ] Install `@tanstack/react-query`
- [ ] Create `frontend/lib/providers.tsx` (QueryClientProvider only)
- [ ] Wrap app in providers (`frontend/app/layout.tsx`)
- [ ] Verify app loads without errors

### **Phase 2: Arena Performance** (~1-2 hours)

**Backend - Redis Caching**:
- [ ] Add Redis cache to `/api/v2/public/arena/performance` (60s TTL)
- [ ] Log cache hits/misses for monitoring

**Frontend - React Query Hook**:
- [ ] Create `useArenaPerformance()` hook in `frontend/lib/queries.ts`
- [ ] Update `frontend/app/arena/page.tsx` to use hook
- [ ] Test: revisiting Arena within 30s should be instant

### **Phase 3: Forge Page** (~2-3 hours, AFTER Phase 2 testing)

**Only proceed after Phase 2 is tested and feels good.**

- [ ] Create `useBots()` hook
- [ ] Integrate SSE updates with React Query cache
- [ ] Create `useDataSources()` hook (5min staleTime)
- [ ] Create `useUserProfile()` hook
- [ ] Remove old useState/useEffect patterns

### **Key Files (CC-A owns these)**
- `frontend/lib/providers.tsx` (NEW)
- `frontend/lib/queries.ts` (NEW)
- `frontend/app/layout.tsx` (wrap with Providers)
- `frontend/app/arena/page.tsx` (use hooks)
- `api/public.py` (Redis caching)

### **Success Metrics**

| Metric | Before | Target |
|--------|--------|--------|
| Arena page revisit | ~500ms | <100ms (cache) |
| Bot switching | 200-500ms flash | Instant |
| Arena API calls | 1 per visit | 1 per 60s max |

### **Previously Completed** (Phase 1: Quick Wins - 2026-01-13)
- ✅ Optimistic updates for delete/rename/duplicate/reset
- ✅ Skeleton loading states
- ✅ SaveStatusContext for custom operation feedback

---

## 🔮 **Market Data Intelligence Update** [MARKET_DATA_INTELLIGENCE_UPDATE.md]

**Status**: 🟢 PHASE 1-2 COMPLETE
**Planning Doc**: [DOCS/completed/MARKET_DATA_INTELLIGENCE_UPDATE.md](DOCS/completed/MARKET_DATA_INTELLIGENCE_UPDATE.md)

**Completed** (2026-01-23):
- ✅ ggShot soft disable (database + frontend + orchestrator permission check)
- ✅ Astrology indicators: `lunar_phase`, `mercury_status` under sentiment_social
- ✅ Tested Grok queries (~$0.005 lunar, ~$0.001 mercury)

### **Phase 3: Nansen API Exploration** (~2-3 hours)

**Leverage free credits to evaluate on-chain intelligence.**

- [ ] Review Nansen API documentation
- [ ] Identify valuable endpoints (smart money, whale tracking)
- [ ] Test with free credits
- [ ] Decision: implement adapter or defer?

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

**Phase 1 Complete**: 8 Grok sources live, cost-optimized ($7-10/week with 4hr TTLs)

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
