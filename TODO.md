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

## ✅ **Orchestrator Refactor - COMPLETE**

**Planning Doc**: [DOCS/completed/ORCHESTRATOR_REFACTOR.md](DOCS/completed/ORCHESTRATOR_REFACTOR.md)

- Phase 1 (Quick Wins) + Phase 2 (Scheduler Separation) — shipped 2026-03-01
- Code quality pass + dead code removal (Symphony/Aster) — 2026-03-04
- `ggbot.py`: 6204 → 4185 lines (-32%)
- Frontend hang at hourly candle close: **resolved**
- Future: async DB (asyncpg), module extraction — both cosmetic/optional, no open issues

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

## 🧠 **Market Intelligence - Expansion**

**Phase 1 Complete**: 8 Grok sources live ($7-10/week with 4hr TTLs)
**Planning Doc**: [DOCS/MARKET_INTELLIGENCE_ROADMAP.md](DOCS/MARKET_INTELLIGENCE_ROADMAP.md)

### **Community-Requested: Cross-Asset Context** (from Denis @ Buidler Labs)
- [ ] **USDT.D (USDT Dominance)** — rising = money exits crypto (bearish), falling = money entering (bullish). CoinGecko/Binance API, ~1-2hr
- [ ] **MOVE Index** — ICE BofA bond volatility. High MOVE = bond stress = risk-off cascade for crypto. Grok web search, ~1hr
- Fits existing Phase 1 macro data points. Same adapter pattern, $0 cost.

### **Community-Requested: Order Blocks Preprocessor**
- [ ] **Order Block Detection** — ICT concept: last opposite candle before impulse move = institutional accumulation zone. Requires swing high/low detection + impulse validation + zone tracking over time. New preprocessor (#22), ~4-6hr
- [ ] **Enhanced Position Statefulness** — enrich position management prompts with: bars-in-trade, max drawdown during trade, avg entry (for DCA). Extends DecisionEngineV2 position recap, ~2-3hr

### **Existing Roadmap Phases**
- **Phase 2: Premium On-Chain** ($100-500/mo) — Nansen/Arkham whale tracking, Glassnode flows, token unlocks
- **Phase 3: Sentiment & Social** ($100-500/mo) — Twitter/Reddit NLP, narrative velocity
- **Phase 4: Advanced Intelligence** ($200-1000/mo) — order book heatmaps, institutional flows (BTC ETF)

---

## 📚 Documentation References

- **New Claude Code Instances**: `GO.md` - Start here for onboarding
- **Current Status**: `ACTIVE.md` - Production system status
- **Complete History**: `CHANGELOG.md` - All completed features and fixes
- **Architecture**: `README.md` - Platform overview
