# TODO.md - ggbots Implementation Plan

Active tasks and planned work. See CHANGELOG.md for completed features.

---

## 🏆 **ggArena Season 1** - 🟢 COMPLETE

**Status**: Season 1 finished Feb 11, 2026. Results page live at /arena.
**Planning Doc**: [DOCS/completed/GGARENA_SEASON1_LAUNCH.md](DOCS/completed/GGARENA_SEASON1_LAUNCH.md)

**Competition Results**:
- **Dates**: Jan 21 12:00 UTC → Feb 11 12:00 UTC (21 days)
- **Prize Pool**: $2,500 in USX on Scroll
- **Bots that traded**: filtered to active participants only (0-trade bots excluded from leaderboard)

**Season 2 Backlog**:
- [ ] Inline arena bot creation modal
- [ ] Add "Registered Competitors" section

---

## 🔥 **HIGH PRIORITY - Hyperliquid Live Trading Integration** [HYPERLIQUID_INTEGRATION.md]

**Status**: 🟢 PHASE 5 COMPLETE — Single live bot slot + equity tracking
**Planning Doc**: [DOCS/todo/HYPERLIQUID_INTEGRATION.md](DOCS/todo/HYPERLIQUID_INTEGRATION.md)
**Priority**: P1 — Replaces blocked Symphony integration

**Summary**: Non-custodial live trading via Hyperliquid. Users connect wallet → deposit USDC → authorize ggbots API wallet → bot trades 228 perp markets. API wallets cryptographically cannot withdraw funds (protocol-enforced). Reuses existing Web3 infra from Arena (wagmi/RainbowKit).

### **Phase 1: Backend Trading Service** ✅ COMPLETE (2026-02-08)
- [x] Create `trading/live/hyperliquid_service.py` (HyperliquidLiveTradingService)
- [x] Add `trading_mode='hyperliquid'` routing in `ggbot.py` (5 locations: import, constructor, _run_trading_v2 close+open, config creation, agent execute-trade)
- [x] Add Hyperliquid symbol mapping in `core/symbols/registry.py` + `standardizer.py` (100 symbols)
- [x] Add `hyperliquid_wallet_address`, `hyperliquid_vault_id` columns to `user_profiles`
- [x] Add Vault credential methods: `store/get/delete_hyperliquid_credential` in `vault_utils.py`
- [x] Account allocation validation: sum of `max_margin_percent` across user's Hyperliquid bots ≤ 100%
- [x] Install `hyperliquid-python-sdk==0.22.0`
- [x] Add `HYPERLIQUID` to TradingMode enum in `schemas.py`
- [x] Remove legacy "Pro subscription required" gate from config creation (all tiers can create live bots, activation is the real gate)

### **Phase 1.5: Frontend Setup Page + Mainnet Test** ✅ COMPLETE (2026-02-09)
- [x] Created `/hyperliquid` page with dedicated Arbitrum wagmi config (separate from Arena's Scroll config)
- [x] RainbowKit wallet connect → EIP-712 `approveAgent` signing → API wallet creation
- [x] USDC deposit (on-chain ERC-20 transfer to bridge) + withdrawal (EIP-712 `withdraw3`, no gas)
- [x] Backend: 4 endpoints — `POST /setup`, `GET /status`, `POST /disconnect`, `POST /test-trade`
- [x] Account status display: wallet address, account value, available balance, open positions
- [x] Test trade button (0.01 ETH long → close) — verified on mainnet at $2,071.90
- [x] Credentials stored in Supabase Vault via `VaultManager.store_hyperliquid_credential()`
- **Key learnings**: viem enforces EIP-712 domain chainId must match connected wallet (use Arbitrum 42161/0xa4b1, not SDK default 421614/0x66eee). `market_open` top-level `status: "ok"` doesn't mean filled — must check `statuses[]` for errors.

### **Phase 2: Forge Integration** ✅ COMPLETE (2026-02-09)
- [x] `SettingsModal.tsx` — replaced Symphony/Aster with "Live Trading" section (connect/manage/disconnect via modal)
- [x] `BotCreationModal.tsx` — Paper + Live Trading modes; opens setup modal if not connected
- [x] `LiveTradingSetupModal.tsx` + `LiveTradingModalContent.tsx` — extracted Web3 setup flow into reusable modal
- [x] `ggbot.py` — `hyperliquid_connected` in profile endpoint; credential + unique-symbol gates on `start_bot`
- [x] `TradeSettings.tsx` — allocation indicator showing margin distribution across live bots
- [x] `ActivationBar.tsx` — recognizes `'hyperliquid'` as live trading mode
- [x] `UserProfile.tsx` — live trading balance in dropdown
- [x] `permissions.tsx` — `refreshProfile()` for real-time state updates after connect/disconnect
- [x] `RiskAcknowledgmentModal.tsx` — accepts `'hyperliquid'` trading mode

### **Phase 3: Dashboard Integration** ✅ COMPLETE (2026-02-09)
- [x] `HyperliquidAccountAdapter` — queries Info API `user_state`, per-bot P&L via symbol attribution
- [x] Registered in `UniversalAccountMonitor` (4 adapters: paper/symphony/aster/hyperliquid)
- [x] SSE dashboard: Hyperliquid CTE in DB query + `_enrich_live_positions_and_accounts()` enrichment
- [x] `PerformanceChart.tsx` — recognizes `source: 'hyperliquid'` → cumulative P&L mode (starts at $0)
- [x] `PositionsTable.tsx` — close routing for Hyperliquid positions
- [x] `POST /api/v2/positions/hyperliquid/{batch_id}/close` endpoint
- [x] `GET /bot/{config_id}/account` and `/positions` handle `trading_mode='hyperliquid'`
- [x] Info API exploration test (`scripts/tests/test_hyperliquid_info_api.py` — 12 endpoints)
- **Key design**: Shared account problem solved — per-bot cumulative P&L (realized+unrealized), not shared balance. Same pattern as Symphony.

### **Phase 4: Polish + Production** ✅ COMPLETE (2026-02-11)
- [x] Error handling: retry logic (2 attempts, exponential backoff), error classification, clear user messages
- [x] Telegram publishing: entry + exit notifications with "Live on Hyperliquid" tag
- [x] Documentation: `trading/README.md`, `ACTIVE.md` updated with Hyperliquid sections
- [x] Mainnet smoke test: first live bot running on 4h candle since 2026-02-09
- [ ] Agent bot support (`trading_mode='hyperliquid'` for agents) — deferred, not needed yet

### **Phase 4.5: Position Tracking Fixes** ✅ COMPLETE (2026-02-11)
- [x] Position flip tracking: `_close_stale_trades()` prevents unclosed `live_trades` accumulation
- [x] Dashboard enrichment: current_price from LivePriceService, opened_at from live_trades
- [x] Activity logging: `trade_id=batch_id` (was None, broke timeline linking)
- [x] DB constraint: added 'hyperliquid' to `valid_trading_mode` + `account_snapshots_trading_mode_check`
- [x] SL/TP debug logging: detailed trigger order params + response statuses

**See**: [DOCS/todo/HYPERLIQUID_INTEGRATION.md](DOCS/todo/HYPERLIQUID_INTEGRATION.md) for complete architecture, verified SDK methods, and technical details.

### **Phase 5: Single Live Bot Slot + Strategy Versioning + Equity Tracking** ✅ COMPLETE (2026-02-17)

See CHANGELOG.md (2026-02-17) and [DOCS/completed/SINGLE_LIVE_BOT_SLOT.md](DOCS/completed/SINGLE_LIVE_BOT_SLOT.md).

### **Phase 6: HIP-3 — Equities, Commodities, Indices** (PLANNED)

**Status**: ⏸️ PLANNED — research + API verification complete, ready to implement when prioritized
**Planning Doc**: [DOCS/todo/HIP3_EQUITIES_COMMODITIES.md](DOCS/todo/HIP3_EQUITIES_COMMODITIES.md)

**Summary**: Hyperliquid's HIP-3 protocol enables builder-deployed perp dexes (XYZ, Felix, Kinetiq, etc.) hosting equities (NVDA, TSLA, AAPL), commodities (GOLD, SILVER, COPPER), indices (US500, USTECH, MAG7), forex (EUR, JPY), and pre-IPO (SPACEX, OPENAI). XYZ dex alone does **$809M/day volume** with **$635M OI** across 44 assets. Candle format is byte-for-byte identical to standard perps — our 21 indicators work unchanged.

**POC scope**: One asset (xyz:NVDA) end-to-end — 1 new file, 5 edits:

- [ ] `HyperliquidCandleAdapter` — new adapter in MarketIntelligence pipeline (Priority 3 after Redis WS + Binance REST). Fast-rejects non-HIP-3 symbols via `:` check (<1ms). Fetches candles from HL Info API (~200-400ms).
- [ ] `ohlcv.yaml` — wire adapter as Priority 3 source
- [ ] `registry.py` — add `nvda_xyz` entry with `hip3: True`, `sz_decimals: 3`, `max_leverage: 10`, `asset_class: "equity"`. Add `is_hip3_symbol()` helper.
- [ ] `ggbot.py` — skip `is_websocket_cached` gate for HIP-3 symbols (they're not in Binance WS but are tradeable)
- [ ] `hybrid_price_service.py` — add Hyperliquid `allMids` fallback for HIP-3 price lookups (position sizing + dashboard)
- [ ] `hyperliquid_service.py` — HIP-3 assets are **isolated-margin-only** (`is_cross=False`); dynamic `sz_decimals`/rounding; $10 min notional floor

**Key findings from API verification (2026-02-11)**:
- All 7 timeframes (1m→1d) return clean OHLCV data, 100-500ms latency
- 5,014 1m candles / 2,017 5m candles in 7-day lookback (sufficient for all bot frequencies)
- 30-day depth: 181 4h candles, 721 1h candles. 90-day: 52 1d candles for GOLD
- All HIP-3 assets `onlyIsolated: true` — must use `is_cross=False` (our current code uses `is_cross=True`)
- NVDA: szDecimals=3, maxLeverage=10, $26M/day volume, $58M OI, $100M OI cap
- Adapter cascade cost: Redis miss 5ms + Binance fail 76ms + HL success ~300ms = ~380ms total (only on MI cache miss)

**After POC**: Expand to curated set of high-volume assets, add frontend symbol picker with asset class categories, dynamic HIP-3 asset discovery from `perpDexs` API.

### **Future: Strategy Marketplace (Copy Trading)**
- [ ] Design marketplace tables (strategy_listings, strategy_subscriptions, strategy_trades)
- [ ] Trade fan-out service: creator's bot signal → replicate to all subscriber Hyperliquid accounts
- [ ] Stripe Connect for creator revenue share
- [ ] Legal review for copy-trading regulatory requirements

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

## 🗄️ **Supabase Database Optimizations**

**Status**: 🟡 PARTIAL - Infrastructure upgraded, policy fixes pending
**Reference**: `NOTE.md` (Supabase advisor output), `SQL.md` (migration scripts)

### **Completed (2026-01-29)**
- [x] VACUUM FULL on decisions (1160 MB → 402 MB)
- [x] Added `idx_paper_trades_config_status` composite index
- [x] Added `idx_paper_trades_decision` FK index
- [x] Renamed duplicate/unused indexes to `_deprecated_*`
- [x] Code change: stop storing prompts in decisions table

### **Completed (2026-01-30)**
- [x] Upgraded Supabase compute tier (disk IO budget exhausted)
- [x] Switched to Supabase Pooler connection (direct DB was IPv6-only, VM has no IPv6)
- [x] DATABASE_URL now uses `pooler.supabase.com` with project ref in username

### **Completed (2026-02-03)** - Major Query Optimizations
- [x] Denormalized `initial_equity` on `configurations` table (eliminates expensive DISTINCT ON scan)
- [x] SSE dashboard query: removed `first_activities` CTE, uses `bc.initial_equity` directly
- [x] Arena query: split into two queries to avoid JSONB extraction for 81k rows (9.7s → 0.46s, 21x faster)
- [x] Added `idx_configurations_is_public_performance` index
- [x] Added `idx_activities_platform_cost` index
- [x] Arena cache TTL: 60s → 300s

### **Pending: Drop Deprecated Indexes** (after 3-7 day monitoring)
- [ ] Drop `_deprecated_idx_snapshots_config_time` (10 MB)
- [ ] Drop `_deprecated_idx_snapshots_heartbeat` (12 MB)

### **Pending: RLS Policy Performance**
6 tables have RLS policies that re-evaluate `auth.uid()` per row instead of once:
- [ ] `data_sources` - change `auth.uid()` → `(select auth.uid())`
- [ ] `data_points` - change `auth.uid()` → `(select auth.uid())`
- [ ] `live_trades` - change `auth.uid()` → `(select auth.uid())`
- [ ] `trade_observations` - change `auth.uid()` → `(select auth.uid())`
- [ ] `activities` - change `auth.uid()` → `(select auth.uid())`
- [ ] `agent_sessions` - change `auth.uid()` → `(select auth.uid())`

### **Pending: RLS Disabled Tables**
- [ ] Enable RLS on `account_snapshots` (or confirm backend-only access)
- [ ] Enable RLS on `arena_pledges` (or confirm backend-only access)

### **Pending: Multiple Permissive Policies**
Tables with conflicting RLS policies that OR together (review and consolidate):
- [ ] `activities` - has `activities_public_access` + `activities_user_access`
- [ ] `data_points` - has `reference_data_points_read` + `service_manages_data_points`
- [ ] `data_sources` - has `reference_data_sources_read` + `service_manages_data_sources`

---

## 🔧 **Orchestrator Refactor - Performance First**

**Status**: 🟡 IN PROGRESS - Quick wins done, scheduler separation next
**Planning Doc**: [DOCS/todo/ORCHESTRATOR_REFACTOR.md](DOCS/todo/ORCHESTRATOR_REFACTOR.md)
**Priority**: P0 - Blocking user experience

**Problem**: API returns 502s and SSE streams disconnect during bot execution.

**Root Causes** (in order of impact):
1. **psycopg2 is synchronous** — DB queries block entire event loop
2. **Single process** — API and scheduler compete for same event loop
3. **5,260-line monolith** — maintenance burden (not performance)

### **Phase 1: Quick Wins** ✅ COMPLETE

- [x] Remove artificial UX delays (13s saved per cycle) — 2026-01-30
- [ ] Add timing instrumentation to identify actual bottlenecks
- [ ] Verify connection pooling is properly configured

### **Phase 2: Scheduler Separation** (~16-24 hours)

**Goal**: API server never blocks on LLM calls.

- [ ] Create `ggbot-scheduler.py` (APScheduler, no HTTP)
- [ ] Create `core/orchestrator/lifecycle.py` (Redis pub/sub)
- [ ] Update `ggbot.py` (remove scheduler startup)
- [ ] Update PM2 config (two processes)
- [ ] Test: API responsive during bot execution

### **Phase 3: Async Database** (~40-60 hours)

**Goal**: True async concurrency for DB operations.

- [ ] Create `core/common/async_db.py` (asyncpg pool)
- [ ] Migrate hot paths (SSE stream, bot lifecycle)
- [ ] Gradually migrate all endpoints
- [ ] Feature flag for gradual rollout

### **Phase 4: Code Organization** (Optional, parallel)

**Goal**: Elegant, maintainable codebase.

- [ ] Extract billing endpoints to `api/billing.py`
- [ ] Extract arena endpoints to `api/arena.py`
- [ ] Extract bot lifecycle to `api/bot_lifecycle.py`
- [ ] Create shared `api/dependencies.py` (config ownership check)
- [ ] Move GGBotOrchestrator to `core/orchestrator/`

### **Success Metrics**

| Metric | Current | Phase 2 | Phase 3 |
|--------|---------|---------|---------|
| API p99 latency | 3-10s | <500ms | <100ms |
| 502 errors/hour | 10-20 | <5 | 0 |
| SSE uptime | 95% | 98% | 99.9% |

---

## 🎲 **USX Arena Betting** [CC-B]

**Status**: 🟡 IN PROGRESS - Core flow deployed, needs USX tokens for end-to-end test
**Planning Doc**: [DOCS/todo/USX_STAKING_MODAL.md](DOCS/todo/USX_STAKING_MODAL.md)

**Summary**: Users bet USX on which arena bot will win. Win = sUSX yield + prize share. Lose = sUSX yield only (no downside). Web3 scoped to Arena page only.

### **Completed (2026-01-27)**
- [x] Web3 infra: wagmi v2, viem v2, RainbowKit v2 on Scroll
- [x] BetModal: wallet connect → amount → approve → deposit → record
- [x] "Bet on This Bot" CTA in expanded bot cards
- [x] Public pledge endpoint (wallet = identity, no auth)
- [x] Dynamic USX decimals reading from contract
- [x] Error handling: wallet rejection, on-chain failure, retry mechanism
- [x] Side-by-side chart + stats layout in expanded cards

### **Remaining**
- [ ] Acquire USX tokens for end-to-end test on Scroll mainnet
- [ ] Verify full approve → deposit → record flow with real tokens
- [ ] Display "Total Backed" per bot on leaderboard
- [ ] Show "You bet X on this bot" badge for users with active bets
- [ ] Prize distribution logic (after competition ends)

---

## ⚡ **Frontend Performance - React Query & Arena Redesign**

**Status**: 🟢 PHASE 1-2 COMPLETE + Arena Redesign
**Planning Doc**: [DOCS/completed/FRONTEND_PERFORMANCE_REACT_QUERY.md](DOCS/completed/FRONTEND_PERFORMANCE_REACT_QUERY.md)

**Completed** (2026-01-27):
- ✅ React Query at root level (`providers.tsx`, `queries.ts`, `layout.tsx`)
- ✅ Redis caching on Arena endpoint (300s TTL, updated 2026-02-03)
- ✅ Arena page redesign: Top3Chart + Sparklines (eliminated Recharts spaghetti)
- ✅ Bundle: 212KB → 168KB first load JS (44KB reduction)
- ✅ Forge page hooks: `useDataSources()` (10min), `useBotList()`, `useLatestActivity()` (30s refetch)
- ✅ Arena podium: refresh button feedback (`isFetching`), inline legend, taller chart

### **Future**

- [ ] Integrate SSE updates with React Query cache (write SSE data into query cache)
- [ ] Create `useUserProfile()` hook
- [ ] Full mutation hooks for bot CRUD (replace manual optimistic updates)

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
**Planning Doc**: [DOCS/completed/ACTIVITY_MODAL_REDESIGN.md](DOCS/completed/ACTIVITY_MODAL_REDESIGN.md)

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
**Planning Doc**: [DOCS/completed/STRATEGY_ADVISOR_ANALYSIS.md](DOCS/completed/STRATEGY_ADVISOR_ANALYSIS.md)
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

## 🚀 **Landing Page Quick Wins**

**Status**: 🟢 PHASE 1-4 COMPLETE
**Priority**: High - Product solid, time to optimize funnel

**Completed (2026-01-30)**:
- [x] Removed Arcade demo embed → replaced with SocialProof component
- [x] Added live stats: 470+ bots, 5,900+ trades, 86K+ AI decisions
- [x] ggArena Season 1 banner with "LIVE NOW" badge + "Watch the competition" CTA
- [x] Added CTA after Process section ("Build your first bot in 2 minutes")
- [x] Added CTA after Features section ("Watch live bots compete in ggArena")
- [x] Removed shadows from Hero/Features/Pricing/PersonalStory
- [x] Updated FAQ contact → Telegram community link
- [x] Added "Sign Up" to header navigation
- [x] Fixed footer logo stretching

### **Future Enhancements**
- [ ] Testimonial or tweet embed (when available)
- [ ] Dynamic stats from API (currently hardcoded)

---

## 📈 **SEO & Content Strategy**

**Status**: 🟢 PHASE 1-3 COMPLETE
**Documentation**: [frontend/SEO.md](frontend/SEO.md)
**Priority**: High - Foundation complete, content pipeline active

### **Completed (2026-01-30)**

**Phase 1: Technical SEO** ✅
- [x] `sitemap.ts` - Auto-generated sitemap with all pages + blog posts
- [x] `robots.ts` - Crawl rules blocking protected routes
- [x] OG images generated via Playwright (1200×630, brand colors)
- [x] Twitter cards configured
- [x] PWA icons (192, 512, apple-touch-icon)
- [x] JSON-LD schema on landing (SoftwareApplication) and blog (BlogPosting)
- [x] Meta titles/descriptions on all public pages
- [x] Canonical URLs configured

**Phase 3: Blog Infrastructure** ✅
- [x] `/blog` route with MDX support
- [x] Blog post template with frontmatter (title, description, author, keywords)
- [x] RSS feed at `/feed.xml`
- [x] First cornerstone article published: "What is Vibe Trading?"
- [x] Blog linked in landing header + footer

### **Remaining Work**

**Phase 2: Keyword Research** ✅ COMPLETE (2026-01-30)
- [x] Competitive analysis: vibetrading.dev, vibetradingai.com, Gainium, 3Commas, Pionex
- [x] 4-tier keyword strategy documented in SEO.md
- [x] ggbots differentiators identified (confidence scoring, multi-agent, ggArena)
- [x] Content calendar Q1 2026 planned

**Phase 4: Content Calendar** (In Progress)
8 articles planned for Q1 2026 - see `frontend/SEO.md` for full calendar:
- [ ] Feb 7: Trading Bots vs AI Agents (comparison)
- [ ] Feb 14: AI Confidence Scores & Position Sizing (strategy)
- [ ] Feb 21: ggArena Season 1 Results (analysis)
- [ ] Feb 28: Mean Reversion Strategy Guide (strategy)
- [ ] Mar 7: Multi-Agent Architecture (education)
- [ ] Mar 14: Getting Started with AI Trading (tutorial)
- [ ] Mar 21: Risk Management for AI Bots (strategy)

**Future Considerations**:
- [ ] Newsletter signup / email capture on blog
- [ ] Lead magnet: "5 AI Trading Strategies" PDF
- [ ] Mintlify docs setup (when user questions increase)

---

## 🎭 **Landing Page Scrollytelling Redesign** (Future)

**Status**: ⏸️ PLANNED - After quick wins + SEO foundation
**Priority**: Medium - Larger investment, do after validating current changes
**Estimated Effort**: ~16-24 hours

**Goal**: Transform landing page into app-like onboarding journey.

### **Design Principles**
- Scroll = Progress (each section unlocks next piece)
- Show, Don't Tell (interactive elements woven into narrative)
- Emotional Arc: Problem → Solution → Proof → Action
- Single CTA per viewport
- Scroll-triggered animations (Framer Motion)

### **Proposed Section Flow**
```
Hero (problem statement)
    ↓ scroll
"The Old Way" (pain points, visual)
    ↓ scroll
"The ggbots Way" (solution reveal)
    ↓ scroll
Live Demo (interactive, inline)
    ↓ scroll
Social Proof (stats, testimonials)
    ↓ scroll
How It Works (3 steps, animated)
    ↓ scroll
Pricing (transparent, simple)
    ↓ scroll
Founder Story (trust building)
    ↓ scroll
Final CTA (urgency, ggArena)
```

### **Technical Requirements**
- [ ] Framer Motion scroll animations
- [ ] Intersection Observer for section triggers
- [ ] Performance optimization (lazy load below-fold)
- [ ] Mobile-optimized experience

### **Inspiration**
- Linear.app (product reveals on scroll)
- Vercel.com (journey through capabilities)
- Arc browser (emotional, personal narrative)

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
