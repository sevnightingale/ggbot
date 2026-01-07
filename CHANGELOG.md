# CHANGELOG - ggbots Platform

Complete history of features, fixes, and improvements. For current status see ACTIVE.md, upcoming work see TODO.md.

**WRITING STYLE**: Telegraphic style. Omit articles (a, an, the). Include file references, technical accuracy. Target 3-8 lines recent entries, 1-3 lines older entries.

---

## 2026-01-06 - Reasoning Tier Fix + Billing Accuracy + Upgrade Modal Redesign

**Reasoning Tier Bug** (`core/config/schemas.py`, `core/config/models.py`):
- `LLMConfig` Pydantic model missing `reasoning_tier` field → silently dropped on config load
- Bots configured economy/premium all ran as standard tier
- Added field with validator, backward compat with `thinking_mode`

**Billing Fix** (`decision/engine_v2.py:816-831`):
- Was using static `llm_models` table pricing (standard tier only)
- Economy users overcharged ~3x, premium users undercharged ~6x
- Now uses actual OpenRouter cost from `usage['cost']` + 70% markup
- Fallback to calculated cost if actual unavailable

**Upgrade Modal Redesign** (`frontend/components/UpgradeModal.tsx`, `ActivationBar.tsx`):
- Netflix-style checkout: bot name, value prop, cost estimate, trust bullets
- Bot-specific pricing based on model + tier + frequency
- Real cost data from production testing all 21 model+tier combinations
- Test script: `scripts/test_model_tier_costs.py`

**Extraction Fix** (`ggbot.py:580-610`):
- `_extract_indicators_from_config()` was collecting ALL data_points from ALL sources
- Market intelligence points (btc_funding_rate, etc.) passed to technical indicator calculator → warnings
- Fixed to only extract from `technical_analysis` source

---

## 2026-01-04 - Strategy Advisor Performance Analysis

Universal bot performance analysis engine. Surfaces hidden patterns users couldn't see manually.

**Backend** (`core/services/performance_analyzer.py`):
- Basic stats: WR, R:R ratio, breakeven WR, P&L
- Direction breakdown: long vs short performance
- Universal pattern extraction from market_query (technical + sentiment + volume)
- Pattern combination analysis: 2-pattern combos, confirmation vs risk patterns
- Timeframe alignment: multi-TF correlation with outcomes
- Exit reasoning classification: thesis_complete, trend_override, capitulation
- Confidence calibration: expected vs actual win rates per bucket
- Claude Haiku LLM synthesis for actionable recommendations
- Exit analysis caveat: LLM instructed early exits may have avoided worse losses (no counterfactual data)

**API**: `/api/v2/assistant/analyze/{config_id}` - returns full analysis with AI insights

**Frontend** (`StrategyAdvisorPanel.tsx`):
- Two buttons: "Create Strategy" (always), "Analyze Performance" (when bot has closed trades)
- Uses `/api/v2/bot/{config_id}/account` to check trade count
- Inline analysis report with stats, patterns, critical issues, positive edges, recommendations
- "Discuss with Strategy Advisor" sends report summary to chat for follow-up discussion

---

## 2026-01-04 - Activity Modal Redesign

Replaced bottom-sheet with centered modal for activity details. New `activity-modal.tsx` component with carousel navigation (swipe mobile, arrows desktop). Type-specific formatters for trade_entry, trade_exit, llm_thought, market_query. Fixed Framer Motion transform conflict by using flexbox centering wrapper. Updated all 3 decision prompts with structured REASONING format (KEY_SIGNAL, SUPPORTING, RISK, SUMMARY) - frontend parses with graceful fallback.

---

## 2025-12-28 - Symphony Position Display Fix

**Root Cause**: SSE dashboard returned NULL for Symphony positions, enrichment function existed but never called

**Fixes Applied**:
- symphony_service.py: Added collateralAmount, pnlPercentage, liquidationPrice, status fields
- symphony_adapter.py: Calculates margin_used from sum of position collateral fields
- dashboard_data.py: Enabled `_enrich_live_positions_and_accounts()`, fixed source filter 'symphony' (was 'live')
- PositionsTable.tsx: Added 'symphony' source type, close button routing

---

## 2025-12-27 - Error Log Fixes

- **binance_funding Adapter**: gateway.py lacked derivatives category pattern → added `elif 'funding' in snake_case`
- **WebSocket Queue Overflow**: Increased max_queue_size 100→1000 (700 streams overwhelmed default)
- **Redis TTL**: Timeframe-aware TTL for 4h/1d/1w (was 1h TTL < candle interval) → TIMEFRAME_TTL mapping
- **Minor**: KC indicator alias, volume log wording fix

---

## 2025-12-27 - Arena Activity Timeline + TradeSettings Fix

- **Arena Timeline**: 3 public endpoints (balance-series, activities, metadata), lazy-loaded timeline in expanded accordion
- **TradeSettings Fix**: Nested object data loss on save → added spread operator for position_sizing
- **TP/SL Labels**: "Stop Loss (%)" → "Stop Loss (price drop %)", added leverage P&L explanation

---

## 2025-12-19 - ggArena Bot Strategy Tuning

7 arena bots prepared for competition. Created `trading/strategies/*.md`. Revised prompts with action bias (0.55+ threshold vs 0.75+), removed paralysis language. Key insight: 4/5 Technician losers = longs against bearish 1H regime → added regime gating.

## 2025-12-18 - Bot Profile Images + Arena Enhancements

**Full Documentation**: [DOCS/completed/2024-12-18_bot_avatars_arena_enhancements.md](DOCS/completed/2024-12-18_bot_avatars_arena_enhancements.md)

## 2025-12-17 - Bot Image Upload + Arena Page + TV Timeline Dual-Mode

- **Image Upload**: Fixed name preservation, SSE query, frontend sync
- **Arena**: Public leaderboard /arena, Recharts multi-line, 21-day competition, no auth
- **TV Timeline**: Dual-mode (Activity/Performance), timeframe aggregation (5M/1H/4H/1D)
- **Bot Limit Removed**: Dropped PostgreSQL trigger, frontend 10-bot limit removed

---

## 2025-12-15 - Account Metrics Standardization

**Full Documentation**: [DOCS/completed/2025-12-10_position_sizing_simplification.md](DOCS/completed/2025-12-10_position_sizing_simplification.md)

Major refactor: Created `core/domain/metrics_calculator.py` as single source of truth for all account metrics. Eliminated 6 duplicate formula implementations → 1. Added total_equity column to activities table. Updated API responses with comprehensive account metrics. Added Account Metrics Glossary to README.md.

---

## 2025-12-14 - Admin Dashboard Equity Fix + Bot Comparison

- **Equity Fix**: Removed margin_used from calculation (was double-counting) → `current_balance + unrealized_pnl`
- **Bot Comparison**: GET /api/v2/admin/bots/equity-comparison, Recharts line chart, profile images, time selectors

---

## 2025-12-10 - Position Sizing Simplification (BREAKING)

**Full Documentation**: [DOCS/completed/2025-12-10_position_sizing_simplification.md](DOCS/completed/2025-12-10_position_sizing_simplification.md)

Removed position sizing methods, simplified to confidence-based only. Deleted PositionSizingMethod enum, renamed max_position_percent → max_margin_percent. New defaults: leverage 5x, max_margin 20%, SL 5%, TP 10%.

## 2025-12-10 - Frontend/Backend Validation Mismatch + Stop Loss Inversion Fix

- **Validation**: Backend le=25 vs Frontend max=100 → increased backend limit, added frontend validation
- **Stop Loss Inversion**: Parser extracted Bollinger Band values as SL/TP → added directional validation, removed LLM SL/TP fields from prompts, config defaults always apply

---

## 2025-12-05 - Admin Dashboard + Signal Filtering + Strategy Advisor

**Full Documentation**: [DOCS/completed/ADMIN_DASHBOARD.md](DOCS/todo/ADMIN_DASHBOARD.md)

- **Admin Dashboard**: /admin with 13 endpoints (stats, services, billing, users, bot control)
- **Signal Filtering**: Symphony bots only receive 100 compatible symbols (42 filtered)
- **Strategy Advisor**: Character creation UX, 4-scenario framework, reasoning tier system (economy/standard/premium)
- **Strategy Unification**: Agent bots now use same ConfigureLayout as scheduled bots
- **Resend Fix**: Added 600ms delay between sync and send (rate limit)
- **Grok Timeouts**: Query-specific timeouts (NFP 300s, Twitter 180s, VIX 120s)

---

## 2025-12-04 - Unified Config Saving + Symphony Win Rate Fix

**Full Documentation**: [DOCS/completed/UNIFIED_CONFIG_SAVING.md](DOCS/completed/UNIFIED_CONFIG_SAVING.md)

- Batched config save: 40+ API calls → 1, 5s debounce, dirty field tracking
- Symphony win_rate: Divided by 100 (was overflow NUMERIC(5,4))

---

## 2025-11-30 - Activity Timeline Data Visibility

Market query activities now log exact LLM prompt data. Frontend bottom sheet shows formatted sections. Fixed llm_thought field name (reasoning→thought). ggShot config enforcement (only fetch if enabled in bot config).

---

## 2025-11-23 - Balance Tracking + API Fixes

- **Balance**: Fixed race condition (log after update), removed duplicate logging, added total_pnl to Redis
- **API**: Added missing fields to GET /config/{id} (state, trading_mode, symphony_agent_id, updated_at)
- **Frontend**: TypeScript fixes, theme-adaptive colors
- **Auto-Save**: Fixed missing config_name/config_type params overwriting bot names

---

## 2025-11-20 - Legal + Trading Mode Refactor + AsterDEX

**Full Documentation**: [DOCS/completed/trading-mode-refactor.md](DOCS/completed/trading-mode-refactor.md)

- **Legal**: Terms, Privacy, signup disclaimer, risk modal for live trading
- **Trading Mode**: execution_mode removed, single source trading_mode column
- **AsterDEX**: 1,394-line aster_service_v3.py, Web3 signatures, 33 compatible symbols
- **Market Maker**: Avellaneda-Stoikov engine for Kuru DEX (~900 lines experimental)

---

## 2025-11-19 - Strategy Advisor Auto-Save

Replaced floating modal + SaveConfigBar with always-visible 500px panel. Auto-save with 1s debounce, optimistic updates, rollback on error. Added SaveStatusContext for global status coordination.

---

## 2025-11-16 - Universal AI Assistant + Metered Billing + Critical Fixes

**Full Documentation**: [DOCS/completed/METERED_BILLING_IMPLEMENTATION.md](DOCS/completed/METERED_BILLING_IMPLEMENTATION.md)

- **AI Assistant**: `/api/v2/assistant/chat` with 3 tools, Claude Haiku function calling, bottom sheet modal
- **Metered Billing**: Stripe Billing Meters operational, weekly invoicing, $0.107734 first period
- **OpenRouter Migration**: 7 providers, 14 variants, llm_models table
- **ActivationBar**: Replaced pipeline ticker with activity-based status + KPIs
- **Critical Fixes**: WebSocket cache 3→100 candles, SSL connection pooling (5-20 conn)

---

## 2025-11-15 - Snapshot Timeline + Activities Overhaul + Account Monitoring

**Full Documentation**: [DOCS/completed/snapshot_timeline_workstream1_complete.md](DOCS/completed/snapshot_timeline_workstream1_complete.md)

- Snapshot-optimized chart, time-based X-axis, activities-only query
- Activities logging overhaul: llm_thought standalone, auto trade_entry/exit, 1%→95% visibility
- Universal Account Monitoring: PM2 service, 5s checks, 5min snapshots, adapter pattern
- Symphony mode migration: trading_mode='live'→'symphony'

---

## 2025-11-13 - Metered Billing Infrastructure + Agent/RLS/Aster Fixes

Core billing w/ daily reporting, tier architecture (FREE/USAGE_BASED/PRO). LLM Pricing Service (70% markup). RLS secured activities/agent_sessions/llm_models. Aster: proper sizing, income API (26 missing trades recovered).

---

## 2025-11-11 - Confidence Sizing + OpenRouter UI

Tested confidence-based sizing paper/symphony/aster. Formula: margin = confidence × max_margin × balance. Model selection UI: 7 models, colored logos, thinking toggle. Tailwind dark mode theme system.

---

## 2025-11-10 - Config System Cleanup v2.2 + 5 Critical Fixes

373 bots migrated autonomous_trading→scheduled_trading. Deleted execution_mode JSONB. 5 fixes: Config save 404, SSE missing config_type, OpenRouter enum, timeline race, Aster metrics zero.

---

## 2025-11-08 - Agent Session Resumption + Timeline in Forge

Agents survive crashes via Claude SDK session resumption (80-90% context loss reduction). Replaced DecisionFeed+PerformanceChart with full-width TVTimeline.

---

## 2025-11-07 - TradingView Timeline + Agent Strategy v4

Professional TradingView Lightweight Charts: line chart 700+ points, markers (trades, queries, thoughts, waits), bottom sheet. Agent dynamic symbol discovery via ggshot scan.

---

## 2025-11-06 - Ceremonial Brutalism Rebrand

Obsidian/ivory/brass palette, Bodoni Moda/Space Grotesk/IBM Plex Mono typography. 56 emojis→Lucide icons. 18 files modified.

---

## 2025-11-03 - Agent Phase 4c Autonomous + Activity Timeline

24/7 autonomous trading live, 13+ min tested. Activities table 14 cols, 7 indexes, activity logger, 3 endpoints.

---

## 2025-11-02 - AsterDEX Integration Phase 1

142 ggbot vs 140 Aster → 33 compatible (23.2%). aster_service_v3.py Web3 ECDSA auth. Full trade cycle tested.

---

## 2025-11-01 - Agent Phase 3 + Maintenance Mode

Live autonomous trading operational. Maintenance mode: 59 bots deactivated, 24 positions closed ($186.88 P&L).

---

## 2025-10-30 - Activity Timeline Viewer

Canvas timeline /view/[config_id], 850 lines, 60fps. Drag pan, zoom levels.

---

## 2025-10-28 - Market Intelligence LIVE

8 Grok sources LIVE: VIX, DXY, CPI, NFP, BTC TVL, whale, Twitter, news. $195/mo platform cost. Parallel 160s→30s (5.3x).

---

## 2025-10-27 - Intelligence Orchestrator

orchestrator.py (260 lines), GrokAgenticAdapter. 7 categories, 24 data points.

---

## 2025-10-26 - ggShot Universal Data

878 signals backfilled 60 days. Multi-timeframe, dual mode (push validation + pull autonomous).

---

## 2025-10-24 - Hybrid Price Service + Symphony Dashboard

142 symbols: WebSocket (100 <1ms) + REST fallback (42 ~100ms). SSE fetches Symphony parallel.

---

## 2025-10-19 - Symphony Integration + Universal Data Layer

Vault encrypted storage, symphony_service.py. 100/141 symbols compatible. MarketIntelligence gateway 3x-3000x faster.

---

## 2025-10-11 - Resend Email

189/261 users synced, welcome emails on signup.

---

## 2025-10-04 - Trading Fixes

Manual close button, trade settings validation. Position sizing FIXED, P&L FIXED (removed double leverage). Account reset: 92 deactivated.

---

## 2025-10-03 - LLM Performance

GPT-5 Responses API, PRO 200s timeout. Extraction parallel ~60s saved.

---

## 2025-10-01 - Stripe Monetization

$29/mo Pro 14-day trial, annual $279/yr. 4 webhook events, billing portal. EARLY50 coupon.

---

## Earlier (Pre-Oct 2025)

- **Scheduler**: APScheduler, zero-drift candles, Redis idempotency, 5m-1d multi-timeframe
- **Signal Validation**: ggShot AI confidence, premium gating, Telegram publishing
- **Paper Trading**: WebSocket prices (sub-ms), $10k isolated, 3s monitoring, liquidation
- **Core V2**: Frontend SSE real-time, decision carousel, Vercel Analytics
- **Disk Crisis (Sept 27)**: Docker log 26GB freed, batch SQL 99% reduction
- **Multi-Exchange (Sept 19)**: 5 exchanges failover

---

**Documentation**: See README.md (architecture), ACTIVE.md (production status), TODO.md (roadmap)
