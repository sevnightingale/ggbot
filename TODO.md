# TODO.md - ggbots Implementation Plan

Active tasks and planned work, ordered by priority. See CHANGELOG.md for completed features.

---

## 🏟️ **ggArena Season 2 — Phase B: Database + API** (URGENT — Before Apr 1)

**Status**: 🔴 NOT STARTED — Phase A shipped (Mar 10), Phase B deadline Apr 1
**Planning Doc**: [DOCS/todo/ARENA_SEASON2.md](DOCS/todo/ARENA_SEASON2.md)

Registration opens Apr 1, competition Apr 7-28. Table `arena_registrations` exists with correct schema, zero registrations.

- [ ] Season status endpoint (`GET /api/v2/public/arena/season/current`)
- [ ] Register/unregister endpoints with config lock check
- [ ] S2 leaderboard endpoint
- [ ] Registration status in config list response
- [ ] Frontend registration UI + Forge lock UI
- [ ] Update `arena_reset.py` for S2
- [ ] Active days calculation (18/21 eligibility)

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

### **Async DB Migration** (Before 100+ Active Bots)

Currently 36 active bots, 10/50 connections used. Not urgent — defer until 60+ active or next deadlock.

Sync `get_db_connection()` (psycopg2) blocks asyncio event loop when pool is contended. Wrap hot-path calls in `asyncio.to_thread()` so DB I/O runs in thread pool.

**Phase 1 — Bot execution pipeline** (~15 call sites):
- [ ] `core/orchestrator/orchestrator.py` — 4 calls (ggshot query, market_data cleanup, config loading)
- [ ] `decision/engine_v2.py` — 6 calls (decision save, position queries, config load)
- [ ] `core/common/activity_logger.py` — 3 calls (activity logging)
- [ ] Set `ThreadPoolExecutor(max_workers=32)` as default executor in scheduler entry point

**Phase 2 — Trading pipeline** (fires only on actual trades, lower priority):
- [ ] `trading/paper/positions.py` — 5 calls (position CRUD)
- [ ] `trading/paper/supabase_service.py` — 2 calls (account updates)
- [ ] `trading/live/hyperliquid_service.py` — position/trade DB ops

**Long-term** (500+ bots): migrate to asyncpg (async PostgreSQL driver). Separate project.

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

**Status**: 🟡 IN PROGRESS — Market Conditions data source shipped, ACP integration next
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

### ~~Agent Registration~~ ✅ (2026-03-21)
- [x] "Sebastian by ggbots.ai" registered as Hybrid agent (entity_id: 29537)
- [x] Smart wallet: `0xDAD56...422612`, EOA whitelisted: `0xFF0ab...19bbD`
- [x] Job offering: marketBrief ($0.01, 10min SLA)
- [x] Credentials in `.env` (`ACP_WALLET_ADDRESS`, `ACP_WALLET_PRIVATE_KEY`, `ACP_ENTITY_ID`)
- [x] `virtuals-acp` SDK installed

### **Workstream 1: ACP Buyer Integration** (~2-3 days)
- [ ] Fund smart wallet with USDC on Base ($5-10 for testing)
- [ ] `core/services/acp_client.py` — ACP client wrapper (wallet, job lifecycle, polling mode)
- [ ] `market_intelligence/adapters/acp/acp_agent_adapter.py` — MI adapter for ACP agents
- [ ] Catalog YAML + `catalog_mapping.py` entries for curated agents (Otto, Wolfpack, BlackSwan)
- [ ] DB seed: additional `data_points` under `agentic_intelligence` for each curated agent

### **Workstream 2: ACP Provider Service**
- [ ] Provider process: listen for ACP jobs → read latest report from Supabase → deliver
- [ ] Self-consumption: wire our agent into Agentic Intelligence category via ACP
- [ ] Submit for graduation review (7 working days)

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
