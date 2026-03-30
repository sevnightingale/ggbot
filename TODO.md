# TODO.md - ggbots Implementation Plan

Active tasks and planned work, ordered by priority. See CHANGELOG.md for completed features.

---

## 🥋 **The Dojo** (ACTIVE — Primary Focus)

**Status**: 🟡 PLANNING COMPLETE — Implementation ready
**Planning Doc**: [DOCS/todo/DOJO.md](DOCS/todo/DOJO.md)

Chess.com-inspired competitive environment. ELO on bots directly (no archetype entity). Dojo = third tab in Forge + public leaderboard at `/dojo`. Matches run isolated temp instances ($10k, frozen config). Composite score: PnL 40%, Sortino 25%, Drawdown 20%, Win Rate 15%.

### **Phase 1: Dojo Foundation** (Start Here)
- [ ] Add `dojo_visible`, `elo_rating`, `is_house_bot` columns to configurations
- [ ] `GET /api/v2/public/dojo/bots` — all active visible paper bots + performance + ELO
- [ ] `GET /api/v2/public/dojo/stats` — aggregate stats
- [ ] `PUT /api/v2/config/{id}/visibility` — toggle dojo visibility
- [ ] `EloTierBadge` shared component + add to BotRail bot cards
- [ ] Add `'dojo'` tab to Forge TabNavigation (shell: ELO, tier, placeholder match UI)
- [ ] Public `/dojo` page (leaderboard, House Bot profiles, S1 results as "Past Seasons")

### **Phase 2: ELO Engine**
- [ ] `elo_history` table
- [ ] `core/arena/elo.py` — Sortino-based composite score + ELO update functions
- [ ] Weekly rolling ELO scheduler job (Sundays midnight UTC)
- [ ] Real ELO values replace placeholder on leaderboard + bot rail

### **Phase 3: House Bots**
- [ ] Create The Arbiter Standard config (Sev tunes)
- [ ] Create Rapid + Blitz variants
- [ ] Mark `is_house_bot = true`, featured on public `/dojo` + Forge challenge UI

### **Phase 4: 1v1 Matches**
- [ ] `dojo_matches` table (with config snapshots + temp instance references)
- [ ] `core/arena/matches.py` — full lifecycle (challenge → temp instance → complete → ELO update)
- [ ] Cost estimation endpoint
- [ ] Match lifecycle scheduler job (start, complete, forfeit)
- [ ] Forge: EnterMatchPanel, ChallengeModal, ActiveMatchCard, MatchHistoryList
- [ ] Public: active match spectating on `/dojo`

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
- [x] `market_intelligence/adapters/acp/acp_agent_adapter.py` — cache-first MI adapter
- [x] Catalog YAML + `catalog_mapping.py` entries (ggbots_acp active, Otto/Wolfpack/BlackSwan commented)
- [x] `sebastian_virtuals.py` — PM2 background service (provider + buyer queue + monitor)
- [x] `ecosystem.config.js` — sebastian-virtuals PM2 entry
- [x] DB seed: `ggbots_acp` data point under `agentic_intelligence`

### **Remaining: ACP Activation** (~1 day)
- [ ] Create separate EOA wallet for Sebastian provider (fixes `OnlyCounterParty` revert on evaluate)
- [ ] Whitelist new EOA on Sebastian agent, update `.env` with separate provider key
- [ ] Start `sebastian-virtuals` PM2 service, verify automated provider + buyer lifecycle
- [ ] Discover third-party agent wallet addresses (`browse_agents` for Otto, Wolfpack, BlackSwan)
- [ ] Uncomment third-party entries in `catalog_mapping.py`, run seed SQL
- [ ] Enable ACP data points on test bots, verify end-to-end via bot cycle
- [ ] Submit for graduation review (7 working days)

---

## 🏟️ **Virtuals DGClaw Arena** ($GG Graduation — Volume Driver)

**Status**: 🟡 IN PROGRESS — Phase 1 deployed, awaiting first automated trade
**Architecture Doc**: [trading/virtuals/README.md](trading/virtuals/README.md)

AI trading arena on Virtuals Protocol. Every trade = on-chain ACP transaction = $GG volume. Arena is a parallel execution layer — bot runs normally (paper/live), arena mirrors trade intents to DGClaw via ACP.

### ~~DGClaw Registration~~ ✅ (2026-03-25)
### ~~Phase 1: Arena Execution Layer~~ ✅ (2026-03-26)

Sev's live HL bot (`b9d9bf00...`) mirrors trades to DGClaw. `dgclaw_service.py` handles ACP lifecycle, orchestrator enqueues to `arena:trade_queue`, `sebastian-virtuals` processes. Balance $35.79 in DGClaw account.

### **Phase 1: Remaining**
- [ ] Verify first automated arena trade end-to-end
- [ ] Arena position monitoring/logging
- [ ] Keep ACP wallet funded for $0.01/trade fees

### **Phase 2: Any User Can Enter** (major feature — VALIDATED)

Lite agent pool model — claw REST API control (no EOA needed). Full flow validated 2026-03-26: create → tokenize → fund → register → deposit → trade. See [trading/virtuals/README.md](trading/virtuals/README.md) for full scoping.

- [ ] Agent pool creation script (batch lite API + tokenize + DGClaw join_leaderboard)
- [ ] `arena_agents` table + assignment logic
- [ ] Claw API adapter for per-user arena trades (POST /acp/jobs with user's apiKey)
- [ ] `/virtuals-arena` frontend page (leaderboard, deposit address, bot selector, positions)
- [ ] Deposit detection (poll claw API `/acp/wallet-balances`, trigger perp_deposit)
- [ ] Per-user arena trading (orchestrator routes to claw API per assigned agent)
- [ ] Withdrawal flow (perp_withdraw via claw API → USDC back to user)

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
