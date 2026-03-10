# TODO.md - ggbots Implementation Plan

Active tasks and planned work. See CHANGELOG.md for completed features.

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

### ~~Audit: Live Trading Integration~~ ✅ (2026-03-07)
- [x] 4 bugs found and fixed: duplicate close activities, partial fill P&L, fill window drift, duration timezone
- [x] `live_trades` schema expanded (side, entry/exit price, size_usd, leverage, realized_pnl) — P&L now per-trade, same pattern as paper_trades
- [x] Adapter snapshot reads `SUM(realized_pnl) FROM live_trades` instead of Hyperliquid fills API — eliminates drift and pre-bot attribution
- [x] Cross-source dedup between `hyperliquid_service` and `hyperliquid_adapter` close paths
- [x] See CHANGELOG for full details

### ~~Bug: Live Config 404~~ ✅ (2026-03-07)
- [x] Fixed — `validate()` now skips validation for unconfigured HL bots (`config_service.py:155-159`). See CHANGELOG.

### **Remaining HL Items**
- [ ] Agent bot support (`trading_mode='hyperliquid'` for agents) — deferred
- [ ] Strategy Marketplace / copy trading — design tables, trade fan-out, Stripe Connect, legal review

---

## 🏟️ **ggArena Season 2 + $GG Launch** (March 10 – April 28)

**Status**: 🟡 IN PROGRESS — Phase A shipped, Phase B before Apr 1
**Planning Doc**: [DOCS/todo/ARENA_SEASON2.md](DOCS/todo/ARENA_SEASON2.md)

### ~~Phase A: Arena Page Update~~ ✅ (2026-03-10)
- [x] S2 hero, timeline visualization, phase-aware progress bar
- [x] Rules section (10 rules), "How It Works" updated for S2 flow
- [x] Season toggle (S2 default, S1 results preserved as archive view)
- [x] Forge banner updated, SEO metadata updated
- See CHANGELOG for details

### **Phase B: Database + API** (Before Apr 1)
- [ ] Create `arena_registrations` table (single table, season metadata as Python/TS constants)
- [ ] Season status endpoint (`GET /api/v2/public/arena/season/current`)
- [ ] Register/unregister endpoints with config lock check
- [ ] S2 leaderboard endpoint
- [ ] Registration status in config list response
- [ ] Frontend registration UI + Forge lock UI
- [ ] Update `arena_reset.py` for S2
- [ ] Active days calculation (18/21 eligibility)

---

## 🗄️ **Supabase Database Optimizations**

**Status**: 🟢 MAJOR — IO optimization shipped, policy fixes pending

### ~~IO Optimization~~ ✅ (2026-03-04)
- [x] paper_trades position prices → Redis (0 UPD/day, was 230K/day)
- [x] account_snapshots tiered retention (713K → 406K rows, daily cron at 3am UTC)
- [x] Dashboard CTE: `latest_activities` join fix (1525ms → 7ms)
- [x] Dashboard CTE: `LATERAL` account_summaries (834ms → 13ms)
- [x] New indexes: `idx_activities_equity_latest`, `idx_decisions_config_created`
- [x] Dropped deprecated indexes (127 MB freed)

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

### ~~Bug: Strategy Advisor Timeframe Collapse~~ ✅ (2026-03-07)
- [x] Configurable timeframes with picker UI (MarketDataSelector)
- [x] Strategy Advisor prompt guardrail (rule #9), AI config creation defaults to all 7
- [x] Archetypes default to all 7 timeframes
- See CHANGELOG for details

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

## 🧠 **Market Intelligence - Expansion**

**Phase 1 Complete**: 8 Grok sources live ($7-10/week with 4hr TTLs)
**Planning Doc**: [DOCS/MARKET_INTELLIGENCE_ROADMAP.md](DOCS/MARKET_INTELLIGENCE_ROADMAP.md)

### ~~Community-Requested: Cross-Asset Context~~ ✅ (2026-03-07)
- [x] USDT.D (USDT Dominance) — CoinGeckoGlobalAdapter, $0 cost, 4hr cache
- [x] MOVE Index — Grok web search, ~$0.005/query, 4hr cache
- See CHANGELOG for full details

### **Community-Requested: Order Blocks Preprocessor**
- [ ] **Order Block Detection** — ICT concept: last opposite candle before impulse move = institutional accumulation zone. Requires swing high/low detection + impulse validation + zone tracking over time. New preprocessor (#22), ~4-6hr

### ~~Community-Requested: Position Statefulness Phase 1~~ ✅ (2026-03-07)
- [x] `bars_in_trade` — derived from `opened_at` + `analysis_frequency`, no persistence needed
- [x] `max_drawdown_during_trade` — Redis `trade:max_drawdown:{trade_id}`, 7-day TTL, updates each cycle
- [x] HL position management fixes: SL/TP computed from config, leverage shown, side normalized
- See CHANGELOG for details

### ~~Community-Requested: Account Performance as MI Data Source (Phase 2a)~~ ✅ (2026-03-07)
- [x] `AccountPerformanceAdapter` — internal DB adapter, paper + HL paths, 5-min cache
- [x] Per-config routing via `{config_id}` template in orchestrator
- [x] DB seed (free tier), frontend auto-populates "Account Performance" category
- See CHANGELOG for details

### **Community-Requested: Position Statefulness Phase 2b** [COMMUNITY_FIXES_MAR2026.md §4]
- [ ] `bot_state` JSONB persistence across cycles (PeakEquity, ConsecutiveLosses, CooldownRemaining)
- [ ] Toggle: `enable_persistent_state: true` in config_data (not default — avoids altering existing bot behavior)
- [ ] System-computed state (not LLM-written) for deterministic counters
- Requested by denisigin for deterministic state-machine strategies

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
