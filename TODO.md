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
- **14 bots competing**, all reset to $10k at launch

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

## ⚡ **Frontend Snappiness - React Query & Optimistic Updates**

**Status**: 🟡 PHASE 1 COMPLETE
**Complexity**: Low-Medium (~1-2 days total)
**Priority**: Medium - UX improvement, not blocking

**Current State**:
- ✅ SSE real-time updates (excellent)
- ✅ Batched config saves with dirty tracking (excellent)
- ✅ LoadingSkeleton component exists
- ✅ Optimistic updates for delete/rename/duplicate/reset (2026-01-13)
- ✅ Skeleton loading states (2026-01-13)
- ✅ SaveStatusContext extended for custom operation feedback (2026-01-13)
- ❌ No server state caching (React Query / SWR)

### **Phase 1: Quick Wins** ✅ COMPLETE (2026-01-13)

See CHANGELOG.md entry for details.

### **Phase 2: React Query Integration** (~4-6 hours)

**Setup**:
- [ ] Install `@tanstack/react-query`
- [ ] Create `frontend/lib/providers.tsx` with QueryClientProvider
- [ ] Wrap app in provider (layout.tsx or page.tsx)
- [ ] Configure staleTime, refetchOnWindowFocus

**Convert Core Fetches**:
- [ ] `useBots()` - Replace `listConfigs` useState with useQuery
- [ ] `useBot(configId)` - Single bot fetch with caching
- [ ] `useDataSources()` - Data sources (rarely changes, long staleTime)
- [ ] `useUserProfile()` - User profile/permissions

**Mutation Hooks with Optimistic Updates**:
- [ ] `useDeleteBot()` - Optimistic remove + rollback
- [ ] `useCreateBot()` - Optimistic add + rollback
- [ ] `useUpdateBot()` - Optimistic update + rollback

**Files**:
- `frontend/lib/queries.ts` (NEW)
- `frontend/lib/providers.tsx` (NEW)
- `frontend/app/forge/page.tsx`

### **Phase 3: Advanced Patterns** (~2-3 hours, optional)

- [ ] Prefetch bot data on hover in BotRail
- [ ] Background refetch on window focus
- [ ] Infinite scroll for trade history (if needed)
- [ ] React Query DevTools for debugging

### **Benefits**

| Before | After |
|--------|-------|
| Re-fetch on every page visit | Cached for 30s, instant on return |
| Delete waits 200-500ms for API | Instant removal, async confirmation |
| Plain "Loading..." text | Skeleton shows page structure |
| Manual loading/error states | Built-in with React Query |
| No request deduplication | Auto-deduped concurrent requests |

### **Implementation Notes**

**SSE + React Query Coexistence**:
```typescript
// SSE pushes updates → invalidate React Query cache
stream.addEventListener('dashboard', (event) => {
  queryClient.setQueryData(['bots'], data.bots)  // Direct update
  // OR
  queryClient.invalidateQueries(['bots'])  // Trigger refetch
})
```

**Optimistic Delete Pattern**:
```typescript
const useDeleteBot = () => useMutation({
  mutationFn: (id) => apiClient.deleteConfig(id),
  onMutate: async (id) => {
    await queryClient.cancelQueries(['bots'])
    const previous = queryClient.getQueryData(['bots'])
    queryClient.setQueryData(['bots'], old => old.filter(b => b.config_id !== id))
    return { previous }
  },
  onError: (err, id, ctx) => queryClient.setQueryData(['bots'], ctx.previous),
  onSettled: () => queryClient.invalidateQueries(['bots']),
})
```

---

## 📱 **Telegram Publishing - Platform Bot Implementation**

**Status**: 🟡 READY TO IMPLEMENT
**Planning Doc**: [DOCS/todo/TELEGRAM_PUBLISHING.md](DOCS/todo/TELEGRAM_PUBLISHING.md)
**Complexity**: Medium (~6-8 hours)
**Priority**: P2 - Feature completion

**Problem**: Telegram publishing UI exists but feature is non-functional. Users can't get channel ID (no `/chatid` command), permission gate is broken, only signal_validation bots publish.

**Solution**: Platform Bot Model - ggbots maintains `@ggFilter_Bot`, users add it to channels, we publish on their behalf.

### **Implementation Phases**

**Phase 1: Bot Command Handler** (~2-3 hours)
- [ ] Create `signals/telegram_bot_handler.py` with `/start`, `/chatid`, `/help` commands
- [ ] Add `telegram-bot` PM2 service to `ecosystem.config.js`
- [ ] **USER ACTION**: Verify `@ggFilter_Bot` exists and token is valid
- [ ] **USER ACTION**: Disable "Group Privacy" in BotFather settings

**Phase 2: Frontend Permission Fix** (~30 min)
- [ ] Add `telegram_publishing` case to `permissions.tsx` switch statement
- [ ] Gate returns `userProfile.can_publish_telegram_signals`

**Phase 3: Extend to Scheduled Trading Bots** (~2-3 hours)
- [ ] Add `publish_trading_decision()` function to `publishing_service.py`
- [ ] Hook into `_run_autonomous_trading_cycle()` in `ggbot.py`
- [ ] Publish on successful trade entries (not waits)

**Phase 4: Error Handling & UX** (~1 hour)
- [ ] Return structured errors from publishing service
- [ ] Update test endpoint with specific error messages
- [ ] Frontend displays meaningful error (not generic alert)

**Phase 5: Testing & Documentation** (~1 hour)
- [ ] Manual test: `/chatid` in channel/group/private
- [ ] Manual test: non-subscriber sees premium lock
- [ ] Manual test: successful publish from scheduled_trading bot
- [ ] Update frontend instructions if needed

### **User Actions Required Before Implementation**
1. Verify `@ggFilter_Bot` exists on Telegram
2. Test bot token: `curl https://api.telegram.org/bot<TOKEN>/getMe`
3. Check BotFather settings (Group Privacy should be OFF)
4. Decide on message branding (logo, disclaimer, link to ggbots.ai)

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
