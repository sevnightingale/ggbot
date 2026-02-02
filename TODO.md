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

## 🗄️ **Supabase Database Optimizations**

**Status**: 🟡 PARTIAL - Disk IO fixes done, policy fixes pending
**Reference**: `NOTE.md` (Supabase advisor output), `SQL.md` (migration scripts)

### **Completed (2026-01-29)**
- [x] VACUUM FULL on decisions (1160 MB → 402 MB)
- [x] Added `idx_paper_trades_config_status` composite index
- [x] Added `idx_paper_trades_decision` FK index
- [x] Renamed duplicate/unused indexes to `_deprecated_*`
- [x] Code change: stop storing prompts in decisions table

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
- ✅ Redis caching on Arena endpoint (60s TTL)
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
