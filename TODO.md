# TODO.md - ggbots Implementation Plan

Active tasks and planned work, ordered by priority. See CHANGELOG.md for completed features.

---

## 🥋 **The Dojo** (Phases 1-4 COMPLETE)

**Status**: 🟢 COMPLETE — All 4 phases deployed
**Planning Doc**: [DOCS/todo/DOJO.md](DOCS/todo/DOJO.md)

Chess.com-inspired competitive environment. Elo on bots directly. Dojo = third tab in Forge (paper bots only). Copy-trade model: matches mirror bot decisions to isolated $10k accounts (zero LLM cost). House Bots: decision oracle mode (opportunity-only, signal dispatch). Full lock during match (forfeit to unlock). Composite score: PnL 40%, Sortino 25%, Drawdown 20%, Win Rate 15%.

### ~~Phase 1: Dojo Foundation~~ ✅ (2026-04-01)
### ~~Phase 2: Elo Engine~~ ✅ (2026-04-01)
### ~~Phase 3: House Bots~~ ✅ (2026-04-01)
### ~~Phase 4: 1v1 Matches~~ ✅ (2026-04-02)

`dojo_matches` table, `core/arena/matches.py` (lifecycle), `core/arena/dojo_mirror.py` (copy-trade + signal dispatch), orchestrator + close path hooks, lock guards on 7 endpoints, scheduler jobs (5min lifecycle + weekly Elo), 7 API endpoints, full frontend (challenge UI, active match cards, match history, lock banner + states).

### **Remaining / Future**
- [ ] Activate House Bots (currently inactive — needs strategy tuning)
- [ ] Public `/dojo` leaderboard page (separate from Forge tab)
- [ ] User-vs-user challenges (accept/reject flow — backend ready, frontend not built)
- [ ] Match instance config retention policy (accumulate over time in `configurations` table)

---

## 🏟️ **ggArena Season 2** (DEFERRED)

**Planning Doc**: [DOCS/todo/ARENA_S2_DEFERRED.md](DOCS/todo/ARENA_S2_DEFERRED.md)

Postponed — Virtuals Degen Arena ($100K/week) is the active competitive event. Entry package ($75 bundle), referral system, seat-based registration all designed and ready to build when timing is right. Existing infrastructure: `arena_registrations` table, register/unregister endpoints, config lock, reset script.

---

## 🗄️ **Database Optimizations**

### ~~RLS Policy Performance~~ ✅ (2026-03-20)

All 18 RLS policies now use `(SELECT auth.uid())` subquery pattern. 7 bare `auth.uid()` policies fixed across `activities`, `agent_sessions`, `live_trades`, `trade_observations`, and `storage.objects` (3 avatar policies). 11 `optimized_*` policies were already correct.

### **RLS Disabled Tables**
- [ ] Enable RLS on `account_snapshots` (or confirm backend-only access)
- [ ] Enable RLS on `arena_pledges` (or confirm backend-only access)

### **Multiple Permissive Policies**
- [ ] `activities` — `activities_public_access` + `activities_user_access`
- [ ] `data_points` — `reference_data_points_read` + `service_manages_data_points`
- [ ] `data_sources` — `reference_data_sources_read` + `service_manages_data_sources`

### ~~Async DB Migration — Phase 1~~ ✅ (2026-03-26)

Bot execution pipeline migrated to `asyncio.to_thread()`. 20 call sites across 6 files. See CHANGELOG 2026-03-26.

### **Async DB — Phase 2: Trading Pipeline** (Lower Priority)

Only fires on actual trades (not every cycle). Wrap in `asyncio.to_thread()`:
- [ ] `trading/paper/positions.py` — 5 calls (position CRUD)
- [ ] `trading/paper/supabase_service.py` — 2 calls (account updates)
- [ ] `trading/live/hyperliquid_service.py` — position/trade DB ops

### **Scaling Capacity Tuning** (At 60+ Active Bots)

Current capacity: ~100 bots with zero changes. Tuning knobs when needed:
- [ ] Raise `Semaphore(30)` → 50 in `bot_runner.py`
- [ ] Raise `ThreadPoolExecutor(32)` → 48 in `ggbot_scheduler.py`
- [ ] Raise pool `maxconn=50` → 80 in `core/common/db.py`
- [ ] At 300+ bots: migrate to `asyncpg` (native async PostgreSQL driver)

---

## 🎯 **LLM-Driven SL/TP — Phase 2** (Mid-Trade Updates)

**Status**: 🔵 PLANNED — Phase 1 complete and verified in production
**Planning Doc**: [DOCS/todo/LLM_DRIVEN_SL_TP.md](DOCS/todo/LLM_DRIVEN_SL_TP.md)
**Origin**: Dennis feedback analysis → Sev confirmed SL/TP as the actionable item

Phase 1 shipped (prompt-only). LLM now provides SL/TP on entry — verified working on both paper (Rhoda) and live (Hyperliquid) trades. Phase 2 enables mid-trade SL/TP updates.

- [ ] `position_management.py` — add optional STOP_LOSS/TAKE_PROFIT to wait/hold output
- [ ] Paper trading: `update_position_stops()` method (UPDATE on paper_trades)
- [ ] Hyperliquid: `update_trigger_orders()` (cancel existing + place new trigger orders)
- [ ] Orchestrator: handle SL/TP updates on wait decisions
- [ ] Include current SL/TP in position data sent to LLM

---

## 🤖 **ACP Agent Intelligence** ($GG Graduation — Revenue Driver)

**Status**: 🟡 IN PROGRESS — Third-party agents discovered + tested, pending scheduler restart for end-to-end verification
**Planning Doc**: [DOCS/todo/ACP_AGENT_INTELLIGENCE.md](DOCS/todo/ACP_AGENT_INTELLIGENCE.md)
**Context**: [NOTE.md](NOTE.md) — Strategic context, $GG graduation, ACP overview

New MI category: "Agent Intelligence" — curated Virtuals ACP agents as data sources. Users toggle agents on like VIX or funding rates. Bot cycles generate ACP transactions (USDC on Base). Platform pays, bills users via existing metered billing.

### ~~Market Conditions Data Source~~ ✅ (2026-03-21)
- [x] `market_conditions` Supabase table + API endpoints (GET/POST with `SEBASTIAN_API_KEY` auth)
- [x] `MarketConditionsAdapter` — MI adapter reading from Redis/Supabase
- [x] Catalog YAML + mapping + DB seed (auto-populates in frontend bot builder)
- [x] Sebastian daily research pass producing structured JSON reports
- See CHANGELOG for details

### ~~Marketplace Exploration~~ ✅ (2026-03-21)
- [x] Butler survey: 6 agents identified, 3 strong candidates (Otto AI, Wolfpack, BlackSwan)
- [x] Marketplace is active — Otto AI has 55K jobs, real ecosystem

### ~~Agent Registration~~ ✅ (2026-03-24, revised)
- [x] ggbots.ai registered as $GG token agent (`isVirtualAgent: true`, entity 40623)
- [x] Smart wallet: `0x2E48f...A2DFE8`, funded $9 USDC
- [x] Sebastian registered as separate provider (wallet `0xDAD56...422612`)
- [x] Shared EOA: `0xFF0ab...19bbD`, on-chain entity_id: **2** (not API ID!)
- [x] Job offering: marketBrief ($0.07, 20min SLA)
- [x] `virtuals-acp==0.3.23` SDK installed
- [x] First ACP transactions: Otto AI crypto_news + self-consumption (ggbots→Sebastian)

### ~~Workstream 1: ACP Buyer + Provider Code~~ ✅ (2026-03-24)
- [x] `core/services/acp_client.py` — dual-client wrapper (buyer=ggbots.ai, provider=Sebastian)
- [x] `market_intelligence/adapters/acp/acp_agent.py` — cache-first MI adapter (renamed from `acp_agent_adapter.py`)
- [x] Catalog YAML + `catalog_mapping.py` entries
- [x] `sebastian_virtuals.py` — PM2 background service (provider + buyer queue + monitor)
- [x] `ecosystem.config.js` — sebastian-virtuals PM2 entry

### ~~Workstream 2: Third-Party Agent Discovery~~ ✅ (2026-04-01)
- [x] Fixed ACPAgentAdapter import bug (`ACP` → `a_c_p_agent` snake_case, added special case)
- [x] Discovered Otto AI, Wolfpack, BlackSwan via `browse_agents()`
- [x] Test purchases verified: Otto ($0.01, crypto news + sentiment), BlackSwan ($0.01, risk flares)
- [x] Wolfpack disabled (requires Base token address, not perp-compatible)
- [x] DB seeded: 3 new data_points. Consolidated: removed `ggbots_acp` (self-consumption), kept `sebastian` (direct Redis)
- [x] Added `_format_agentic_intelligence_data()` to `engine_v2.py` (was silently dropping ACP data from prompts)

### **Remaining: ACP Activation**
- [ ] Create separate EOA wallet for Sebastian provider (fixes `OnlyCounterParty` revert on evaluate)
- [ ] Whitelist new EOA on Sebastian agent, update `.env` with separate provider key
- [ ] Enable ACP data points on test bot, verify end-to-end via bot cycle (Otto + BlackSwan should work now after scheduler restart)
- [ ] Submit for graduation review (7 working days)

---

## 🏟️ **Virtuals DGClaw Arena** ($GG Graduation — Volume Driver)

**Status**: 🟡 IN PROGRESS — Phase 2 user flow verified, close backfill shipped (2026-04-07)
**Architecture Doc**: [trading/virtuals/README.md](trading/virtuals/README.md)

AI trading arena on Virtuals Protocol. Every trade = on-chain ACP transaction = $GG volume. Arena is a parallel execution layer — bot runs normally (paper/live), arena mirrors trade intents to DGClaw via ACP.

### ~~DGClaw Registration~~ ✅ (2026-03-25)
### ~~Phase 1: Arena Execution Layer~~ ✅ (2026-03-26)
### ~~Phase 2: Backend + Pool + Trade Routing~~ ✅ (2026-03-30)

1-bot-1-agent model. 40 agents total: 27 available (tokenized, pool), 11 assigned (10 Denis SZN2 + 1 user), 2 retired. `claw_api.py` for per-agent control, `arena_sync.py` for close mirroring, reconciler in orchestrator.

### ~~Arena Close Sync~~ ✅ (2026-04-01, Phase 1 fallback 2026-04-04, HL backfill 2026-04-07)

Four real-time hooks (paper TP/SL, HL fill detection, manual close, reconciler) + `sync_closes_from_hl()` backfill for the 5th path (DGClaw server-side TP/SL, which never produces an ACP job). Opportunistic `hl_subaccount_address` capture on `/status`, Redis 60s throttle, dual dedup by oid + (pair,±60s). No frontend changes — rides existing 10s modal/timeline polling.

### ~~Phase 2: Modal UX + Bug Fixes~~ ✅ (2026-04-04)

- [x] Frontend: modal UX polish — async registration, smart button labels, correct fee messaging
- [x] ActivationBar stateful button: Enter Degen Arena → Arena: Needs Funds → Manage Arena Agent
- [x] Vault bug: `store_arena_credential` duplicate key crash on DGClaw registration
- [x] Close sync Phase 1 fallback: admin bot closes now enqueue via Redis
- [x] End-to-end user test: join → assign agent → deposit $6 → DGClaw funded ($4.99 after bridge)

### **Remaining**
- [ ] Phase 1 admin bot fix: `user_id='system'` fails UUID validation in activity logger
- [ ] Tokenize ggbot-003 (or keep retired)
- [ ] End-to-end: wait for bot entry signal → verify arena mirror fires (close sync now fully covered)

---

## 🧠 **Bot State v2: LLM-Writable Memory** (HIGH VALUE — Retention Feature)

Bots can write observations that persist across cycles — market context, strategy notes, pattern recognition. Requires prompt engineering discussion before implementation.

- [ ] New prompt section: "YOUR PREVIOUS OBSERVATIONS" injected into decision prompt
- [ ] LLM response includes optional `state_update` field (structured JSON)
- [ ] Redis persistence: `bot_memory:{config_id}` with size limits (~2KB)
- [ ] Output instruction updates for all prompt templates (opportunity, position management)
- [ ] Config toggle: `enable_bot_memory: true` (opt-in, not default)
- [ ] Guardrails: max field sizes, structured fields, system fields LLM cannot overwrite

---

## 🔥 **Hyperliquid — Remaining Items**

**Phases 1-5 COMPLETE** — see CHANGELOG.md
**Planning Doc**: [DOCS/todo/HYPERLIQUID_INTEGRATION.md](DOCS/todo/HYPERLIQUID_INTEGRATION.md)

### **Phase 6: HIP-3 — Equities, Commodities, Indices** (PLANNED)

**Status**: ⏸️ Research + API verification complete. Only 3 live users — expand instruments after live user base grows.
**Planning Doc**: [DOCS/todo/HIP3_EQUITIES_COMMODITIES.md](DOCS/todo/HIP3_EQUITIES_COMMODITIES.md)

HIP-3 enables equities (NVDA, TSLA), commodities (GOLD, SILVER), indices (US500), forex on Hyperliquid DEXes.

**POC scope** (1 new file, 5 edits):
- [ ] `HyperliquidCandleAdapter` — Priority 3 in MI pipeline, ~200-400ms latency
- [ ] `ohlcv.yaml` — wire adapter
- [ ] `registry.py` — add `nvda_xyz` with `hip3: True`, `sz_decimals: 3`
- [ ] `ggbot.py` — skip `is_websocket_cached` gate for HIP-3 symbols
- [ ] `hybrid_price_service.py` — Hyperliquid `allMids` fallback for HIP-3 prices
- [ ] `hyperliquid_service.py` — isolated-margin-only, dynamic rounding, $10 min notional

### **Other HL Items**
- [ ] Agent bot support (`trading_mode='hyperliquid'` for agents) — deferred
- [ ] Strategy Marketplace / copy trading — design tables, trade fan-out, Stripe Connect, legal review

---

## 🧠 **Market Intelligence — Expansion**

**Phase 1 Complete**: 8 Grok sources live ($7-10/week with 4hr TTLs)
**Planning Doc**: [DOCS/MARKET_INTELLIGENCE_ROADMAP.md](DOCS/MARKET_INTELLIGENCE_ROADMAP.md)

### **Order Blocks Preprocessor** (Community-Requested)
- [ ] ICT concept: last opposite candle before impulse move = institutional accumulation zone
- [ ] Requires swing high/low detection + impulse validation + zone tracking. New preprocessor (#22), ~4-6hr

### **Existing Roadmap Phases**
- **Phase 2: Premium On-Chain** ($100-500/mo) — Nansen/Arkham whale tracking, Glassnode flows, token unlocks
- **Phase 3: Sentiment & Social** ($100-500/mo) — Twitter/Reddit NLP, narrative velocity
- **Phase 4: Advanced Intelligence** ($200-1000/mo) — order book heatmaps, institutional flows (BTC ETF)

---

## ⚡ **Frontend Improvements**

### React Query Completion
- [ ] Integrate SSE updates with React Query cache
- [ ] Create `useUserProfile()` hook
- [ ] Full mutation hooks for bot CRUD

### Landing Page
- [ ] Testimonial or tweet embed (when available)
- [ ] Dynamic stats from API (currently hardcoded)
- [ ] Scrollytelling redesign (Framer Motion scroll animations) — lower priority

### Market Data Intelligence
- [ ] Nansen API exploration (free credits available) — smart money, whale tracking

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

## 📚 Documentation References

- **New Claude Code Instances**: `GO.md` - Start here for onboarding
- **Current Status**: `ACTIVE.md` - Production system status
- **Complete History**: `CHANGELOG.md` - All completed features and fixes
- **Architecture**: `README.md` - Platform overview
