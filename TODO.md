# TODO.md - ggbots Implementation Plan

Active tasks and planned work. See CHANGELOG.md for completed features.

---

## 🚨 **CRITICAL - CVE-2025-66478 Secret Rotation**

**Status**: 🔴 URGENT - Application was vulnerable for ~11 hours (Dec 4-5, 2025)
**Planning Doc**: [DOCS/todo/CVE_2025_66478_SECRET_ROTATION.md](DOCS/todo/CVE_2025_66478_SECRET_ROTATION.md)

**Vulnerability**: Next.js/React Server Components RCE (CVSS 10.0)
- Application ran vulnerable Next.js 15.3.3 during exposure window
- Upgraded to patched 15.5.7 on Dec 5, 2025

**Action Required**: Follow rotation checklist in priority order
- [ ] **Day 1**: CRITICAL secrets (Supabase, Auth, Trading APIs)
- [ ] **Day 1-2**: HIGH PRIORITY secrets (AI APIs, Market Data, Email)
- [ ] **Week 1**: MEDIUM PRIORITY secrets (Admin, Redis, OAuth)

---

## 🔧 **Orchestrator Refactor - Performance First**

**Status**: 🟡 IN PROGRESS - Quick wins done, scheduler separation next
**Planning Doc**: [DOCS/todo/ORCHESTRATOR_REFACTOR.md](DOCS/todo/ORCHESTRATOR_REFACTOR.md)
**Priority**: P0 - Blocking user experience

**Problem**: API returns 502s and SSE streams disconnect during bot execution.
Root causes: psycopg2 sync blocking → single process contention → 5,260-line monolith.

### **Phase 1: Quick Wins** ✅ COMPLETE
- [x] Remove artificial UX delays (13s saved per cycle)
- [ ] Add timing instrumentation to identify actual bottlenecks
- [ ] Verify connection pooling is properly configured

### **Phase 2: Scheduler Separation** (~16-24 hours)
- [ ] Create `ggbot-scheduler.py` (APScheduler, no HTTP)
- [ ] Create `core/orchestrator/lifecycle.py` (Redis pub/sub)
- [ ] Update `ggbot.py` (remove scheduler startup)
- [ ] Update PM2 config (two processes)
- [ ] Test: API responsive during bot execution

### **Phase 3: Async Database** (~40-60 hours)
- [ ] Create `core/common/async_db.py` (asyncpg pool)
- [ ] Migrate hot paths (SSE stream, bot lifecycle)
- [ ] Feature flag for gradual rollout

### **Phase 4: Code Organization** (Optional)
- [ ] Extract billing/arena/bot_lifecycle to separate `api/` modules
- [ ] Move GGBotOrchestrator to `core/orchestrator/`

| Metric | Current | Phase 2 | Phase 3 |
|--------|---------|---------|---------|
| API p99 latency | 3-10s | <500ms | <100ms |
| 502 errors/hour | 10-20 | <5 | 0 |
| SSE uptime | 95% | 98% | 99.9% |

---

## 🔥 **Hyperliquid - Remaining Phases**

**Phases 1-5 COMPLETE** — see CHANGELOG.md. Single live bot slot, equity tracking, strategy versioning all shipped.
**Planning Doc**: [DOCS/todo/HYPERLIQUID_INTEGRATION.md](DOCS/todo/HYPERLIQUID_INTEGRATION.md)

### **Phase 6: HIP-3 — Equities, Commodities, Indices** (PLANNED)

**Status**: ⏸️ PLANNED — research + API verification complete
**Planning Doc**: [DOCS/todo/HIP3_EQUITIES_COMMODITIES.md](DOCS/todo/HIP3_EQUITIES_COMMODITIES.md)

HIP-3 enables equities (NVDA, TSLA), commodities (GOLD, SILVER), indices (US500), forex, pre-IPO on Hyperliquid DEXes. XYZ dex: $809M/day, $635M OI, 44 assets. Candle format identical to standard perps.

**POC scope** (1 new file, 5 edits):
- [ ] `HyperliquidCandleAdapter` — Priority 3 in MI pipeline, ~200-400ms latency
- [ ] `ohlcv.yaml` — wire adapter
- [ ] `registry.py` — add `nvda_xyz` with `hip3: True`, `sz_decimals: 3`
- [ ] `ggbot.py` — skip `is_websocket_cached` gate for HIP-3 symbols
- [ ] `hybrid_price_service.py` — Hyperliquid `allMids` fallback for HIP-3 prices
- [ ] `hyperliquid_service.py` — isolated-margin-only, dynamic rounding, $10 min notional

### **Remaining HL Items**
- [ ] Agent bot support (`trading_mode='hyperliquid'` for agents) — deferred
- [ ] Strategy Marketplace / copy trading — design tables, trade fan-out, Stripe Connect, legal review

---

## 🗄️ **Supabase Database Optimizations**

**Status**: 🟡 PARTIAL - Infrastructure upgraded, policy fixes pending

### **Pending: Drop Deprecated Indexes**
- [ ] Drop `_deprecated_idx_snapshots_config_time` (10 MB)
- [ ] Drop `_deprecated_idx_snapshots_heartbeat` (12 MB)

### **Pending: RLS Policy Performance**
6 tables re-evaluate `auth.uid()` per row — change to `(select auth.uid())`:
- [ ] `data_sources`, `data_points`, `live_trades`, `trade_observations`, `activities`, `agent_sessions`

### **Pending: RLS Disabled Tables**
- [ ] Enable RLS on `account_snapshots` (or confirm backend-only access)
- [ ] Enable RLS on `arena_pledges` (or confirm backend-only access)

### **Pending: Multiple Permissive Policies**
- [ ] `activities` — `activities_public_access` + `activities_user_access`
- [ ] `data_points` — `reference_data_points_read` + `service_manages_data_points`
- [ ] `data_sources` — `reference_data_sources_read` + `service_manages_data_sources`

---

## 🎲 **USX Arena Betting**

**Status**: 🟡 IN PROGRESS - Core flow deployed, needs USX tokens for e2e test
**Planning Doc**: [DOCS/todo/USX_STAKING_MODAL.md](DOCS/todo/USX_STAKING_MODAL.md)

- [ ] Acquire USX tokens for end-to-end test on Scroll mainnet
- [ ] Verify full approve → deposit → record flow with real tokens
- [ ] Display "Total Backed" per bot on leaderboard
- [ ] Show "You bet X on this bot" badge for users with active bets
- [ ] Prize distribution logic (after competition ends)

**Season 2 Backlog**:
- [ ] Inline arena bot creation modal
- [ ] Add "Registered Competitors" section

---

## 📈 **SEO & Content Strategy**

**Status**: 🟢 Infra complete, content calendar in progress
**Documentation**: [frontend/SEO.md](frontend/SEO.md)

**Content Calendar** (Q1 2026 — see `frontend/SEO.md`):
- [ ] Trading Bots vs AI Agents (comparison)
- [ ] AI Confidence Scores & Position Sizing (strategy)
- [ ] ggArena Season 1 Results (analysis)
- [ ] Mean Reversion Strategy Guide (strategy)
- [ ] Multi-Agent Architecture (education)
- [ ] Getting Started with AI Trading (tutorial)
- [ ] Risk Management for AI Bots (strategy)

**Future**:
- [ ] Newsletter signup / email capture on blog
- [ ] Lead magnet: "5 AI Trading Strategies" PDF
- [ ] Mintlify docs (when user questions increase)

---

## ⚡ **Frontend Improvements**

### React Query Completion
- [ ] Integrate SSE updates with React Query cache
- [ ] Create `useUserProfile()` hook
- [ ] Full mutation hooks for bot CRUD

### Market Data Intelligence
- [ ] Nansen API exploration (free credits available) — smart money, whale tracking

### Landing Page
- [ ] Testimonial or tweet embed (when available)
- [ ] Dynamic stats from API (currently hardcoded)
- [ ] Scrollytelling redesign (Framer Motion scroll animations) — lower priority

---

## ⏸️ **BLOCKED - External Dependencies**

### Symphony Live Trading
**BLOCKED**: `/agent/all-positions` returns 404 (not implemented). ~2.5 hours once fixed.

### Symphony Spot Trading (Monad)
**BLOCKED**: Both spot endpoints return 404. See [DOCS/symphony_spot_integration.md].

---

## 🧠 **Market Intelligence - Future Phases**

**Phase 1 Complete**: 8 Grok sources live ($7-10/week with 4hr TTLs)

- **Phase 2: Premium On-Chain** ($100-500/mo) — Nansen/Arkham whale tracking, Glassnode flows, token unlocks
- **Phase 3: Sentiment & Social** ($100-500/mo) — Twitter/Reddit NLP, narrative velocity
- **Phase 4: Advanced Intelligence** ($200-1000/mo) — order book heatmaps, institutional flows (BTC ETF)

---

## 📚 Documentation References

- **New Claude Code Instances**: `GO.md` - Start here for onboarding
- **Current Status**: `ACTIVE.md` - Production system status
- **Complete History**: `CHANGELOG.md` - All completed features and fixes
- **Architecture**: `README.md` - Platform overview
