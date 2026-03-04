# CHANGELOG - ggbots Platform

Complete history of features, fixes, and improvements. For current status see ACTIVE.md, upcoming work see TODO.md.

**WRITING STYLE**: Telegraphic style. Omit articles (a, an, the). Include file references, technical accuracy. Target 3-8 lines recent entries, 1-3 lines older entries.

---

## 2026-03-04 - Code Quality Fixes + Dead Code Removal

**Dead Code Removal** (`ggbot.py`, -618 lines):
- Removed all Symphony endpoints (setup/status/disconnect, positions, account metrics, trade history) — integration BLOCKED, API returns 404s
- Removed all Aster endpoints (setup/status/disconnect, positions) — integration BLOCKED
- Removed Symphony/Aster branches from agent trade execution, config creation validation, symbol compatibility checks
- Removed `symphony_agent_id` from ConfigCreateRequest/ConfigUpdateRequest models
- `ggbot.py`: 4802 → 4185 lines. Total reduction from original monolith: 6204 → 4185 (-32%)

**Bug Fix** (`ggbot.py`):
- `get_scheduler_status` total active bots query missing `OR config_type IS NULL` — legacy rows invisible in count. Now consistent with reconcile loop and per-user query.

**Import Cleanup** (`ggbot.py:1-98`):
- Organized imports into stdlib/third-party/local blocks, alphabetized. Removed 4 inline `import re`, 3 inline `import traceback`, 1 duplicate `import os`. Updated module docstring.

**Logging** (`ggbot.py`):
- Replaced 3x `import traceback; traceback.print_exc()` with `exc_info=True` on logger.error() — tracebacks now route through Loguru pipeline instead of bypassing to stderr.

**Constants** (`ggbot.py:95-98`):
- `PAPER_INITIAL_BALANCE` (was literal `10000.0` in 10 places), `CREDIT_PURCHASE_MIN_CENTS`/`MAX_CENTS` (was duplicated in 2 endpoints), `API_BASE_URL` (was hardcoded production domain in IPN callback).

**Frontend** (`frontend/app/layout.tsx`):
- Added Virtual Protocol site verification meta tag.

---

## 2026-03-01 - Orchestrator Refactor Phase 2: Scheduler Separation

**Planning Doc**: [DOCS/completed/ORCHESTRATOR_REFACTOR.md](DOCS/completed/ORCHESTRATOR_REFACTOR.md)

**Problem**: Frontend hung 5-10min at every hourly candle close. Single `ggbot.py` process ran both API server and APScheduler — 13+ bots firing simultaneously starved event loop, blocking all HTTP requests.

**Architecture Change** — split monolith into two PM2 processes:
- `ggbot` (API-only): HTTP/SSE, "Run Now", fast always
- `ggbot-scheduler` (scheduler-only): APScheduler, bot execution, Stripe meter cron
- Database is sole communication channel — no Redis pub/sub, no new infrastructure

**New Files**:
- `core/orchestrator/orchestrator.py` — GGBotOrchestrator class + OrchestrationResult extracted from ggbot.py (~1000 lines moved)
- `core/scheduler/bot_runner.py` — `run_once()`, `add_bot_job()`, `remove_bot_job()` + new `reconcile_loop()` (polls DB every 10s, diffs with scheduler jobs)
- `core/scheduler/utils.py` — added `calculate_next_run()` (computes next fire time without scheduler instance) + `extract_timeframe_from_config()` (moved from ggbot.py)
- `ggbot_scheduler.py` — thin entry point, creates scheduler + orchestrator, enters reconcile loop

**Modified Files**:
- `ggbot.py` — removed ~1400 lines (orchestrator class, scheduler code). Start/stop/update/delete endpoints write DB state only. `get_scheduler_status` queries DB instead of APScheduler. 6204→4802 lines
- `core/sse/dashboard_data.py` — replaced `from ggbot import get_next_run_from_scheduler, has_scheduler_job` with `calculate_next_run()` from utils
- `ecosystem.config.js` — added `ggbot-scheduler` PM2 entry (1G max memory, same env vars)

**How start/stop works now**: User presses Start → API sets `state='active'` → returns immediately with calculated `next_run` → scheduler detects new active bot within 10s → adds APScheduler job. Stop is reverse. Handles all edge cases: timeframe change, delete, crash recovery.

---

## 2026-03-01 - Virtuals 60 Days Application Draft + NOWPayments Integration Guide

**Virtuals 60 Days** (`NOTE.md`):
- Platform token application for Virtuals 60 Days framework — Core Idea, What It Does, How It Works, Why, Roadmap, Token Utility, Tokenomics sections
- Cross-referenced with `ggbots-voice-guide.md` for tone/brand alignment
- Season 1 data (The Arbiter +45% autonomous, 44 bots, 21 days) integrated as proof point
- Trade37 Championship in Future Vision (AI vs Human in-person competition)

**NOWPayments Guide** (`DOCS/NOWPAYMENTS_INTEGRATION_GUIDE.md`):
- Standalone integration guide extracted from production `ggbot.py` implementation
- Covers: invoice creation, HMAC-SHA512 webhook verification (sorted compact JSON gotcha), idempotency via Redis, order_id encoding pattern, payment status reference

---

## 2026-02-26 - Cumulative Bot Cost Tracking + Activity Cost Display + Cost Estimation

**Per-Bot Lifetime Cost** (`decision/engine_v2.py`, `api/usage.py`, `ActivationBar.tsx`):
- New Redis key `usage:config:total:{config_id}` — incremented on every LLM call, no TTL
- `/api/v2/usage/config/{id}` returns `total_usage_usd` (all-time bot cost)
- ActivationBar shows "$X.XX total" next to daily cost
- Backfill script (`scripts/backfill_prepaid_cumulative.py`) now includes per-config cumulative keys — 92 configs, $584.88 total

**Activity Cost Display** (`api/activities.py`, `activity-modal.tsx`):
- Activities API returns `platform_cost_usd` per activity (column added to SELECT)
- Activity modal `LLMThoughtContent` shows "Cost: $0.XXXX" on LLM thought activities

**Cost Estimation for New Bots** (`frontend/lib/cost-estimation.ts`, `ActivationBar.tsx`, `UpgradeModal.tsx`):
- Extracted `MODEL_TIER_COSTS` + `FREQUENCY_TO_DECISIONS` to shared `lib/cost-estimation.ts`
- ActivationBar daily cost slot: shows "~$X.XX/day est." for new bots (no usage data), switches to actual avg once bot has run
- UpgradeModal imports from shared util (was duplicated)

---

## 2026-02-26 - Hyperliquid Trade Close Fixes + Account Stats + Live Strategy Tuning

**Trade Close Activity Logging** (`trading/live/hyperliquid_service.py`):
- `close_position()` now snapshots position via Info API BEFORE `market_close()` — captures entry_price, side, size, leverage, unrealized_pnl
- Extracts exit price from `market_close()` fill data (`statuses[].filled.avgPx`)
- Computes realized P&L from actual prices, duration from `live_trades.created_at`
- Activity details now match paper trading format: entry_price, exit_price, pnl, pnl_pct, side, size_usd, leverage, duration_seconds
- Telegram exit notifications enriched with real P&L and side (was hardcoded `pnl: 0`, `side: 'unknown'`)

**Adapter Close Detection** (`core/monitoring/adapters/hyperliquid_adapter.py`):
- Auto-close activities now include derived entry_price (`entry = exit ± pnl/size`), pnl_pct, size_usd, duration
- `bot_symbols` query: removed `closed_at IS NULL` filter — closed trade symbols now match fills for realized P&L
- Fill aggregation: groups by timestamp to count trades, not individual partial fills (8 fills from 1 `market_close` = 1 trade)

**Account Endpoint** (`ggbot.py`):
- `/bot/{config_id}/account` for Hyperliquid: replaced hardcoded zeros with `account_snapshots` data (total_trades, win_trades, win_rate, realized_pnl)
- Added `initial_equity` lookup + `performance_percent` calculation (was 0.0)

**Live Strategy Tuning** (config_data update, `b9d9bf00`):
- Softened regime anchor: removed "Do NOT exit for 4H pullback within intact 1D regime"; added "3+ domains reversed = exit, regime gets voice not veto"
- Lowered counter-trend bar: "exceptional evidence" → "strong confluence (3+ domains)"; penalty -0.12/-0.08 → -0.08/-0.05
- Added profit protection: when meaningfully profitable, burden of proof flips — need reasons to stay, not reasons to leave

---

## 2026-02-17 - Hyperliquid Phase 5: Single Live Bot Slot + Strategy Versioning + Equity Tracking

**Planning Doc**: [DOCS/completed/SINGLE_LIVE_BOT_SLOT.md](DOCS/completed/SINGLE_LIVE_BOT_SLOT.md)

**Single Live Bot Slot** (`ggbot.py`, `BotRail.tsx`, `BotCreationModal.tsx`, `ConfigureLayout.tsx`):
- Replaced multi-live-bot model with one permanent live config per user, auto-created during HL setup
- `POST /api/v2/bot/{config_id}/promote-to-live` — copies paper bot strategy to live slot with version tracking
- Paper-only bot creation (blocked `trading_mode='hyperliquid'` in `create_config`)
- Removed allocation validation + unique symbol enforcement from `start_bot`
- BotRail: pinned live slot with 4 states (not connected / no strategy / promoted / disconnected)
- Disconnect preserves live slot (`state='inactive'`, not converted to paper)

**Equity Tracking** (`hyperliquid_adapter.py`, `account_snapshot.py`, `dashboard_data.py`, `page.tsx`):
- Adapter returns `current_balance=account_value` (was `None` in multi-bot model)
- `total_equity = current_balance + unrealized_pnl` for Hyperliquid (same formula as paper)
- ActivationBar/PerformanceChart show real equity, not cumulative P&L
- SSE dashboard enrichment merges HL API data with DB snapshots

**Strategy Versioning** (`ggbot.py`, `activity_logger.py`, `tv-timeline.tsx`, `ActivationBar.tsx`):
- `strategy_updated` activity logged on promote-to-live (with version number + config snapshot)
- `strategy_updated` activity logged on config edits via batched save (changed fields tracked)
- `bot_created` activity logged during HL setup auto-creation
- TV timeline: square marker for strategy updates, gear icon in activity modal
- `initial_equity` fallback in `get_latest_snapshot()` for new bots without snapshots

**Bug Fixes** (discovered during live testing):
- `config_service.py`: `data["selected_pair"]` → `data.get("selected_pair", "")` — empty live bot config crashed `from_dict`
- `ggbot.py:start_bot`: missing `from core.common.db import get_db_connection` import
- `ActivationBar.tsx`: guard `temp-` IDs from API calls during duplication
- `BotManagementMenu.tsx`: standardized promote confirmation as inline popover (was browser `confirm()`)
- `account-monitor` PM2 process: 6-day stale code caused NULL `current_balance` in snapshots

**15 files changed across 3 workstreams** — backend, frontend, monitoring.

---

## 2026-02-13 - Vercel Build Fix (CVE-2026-0969) + Frontend Cleanup + Arena Filter

**Vercel Deployment Blocker** (`frontend/package.json`):
- `next-mdx-remote` 5.0.0 → 6.0.0 — fixes CVE-2026-0969 (XSS via JS in MDX). v6 adds `blockJS`/`blockDangerousJS` defaults; transparent for pure-markdown blog.
- `next` 15.5.7 → 15.5.11, `eslint-config-next` aligned — fixes `@next/swc` version mismatch warning
- Browserslist DB updated (1.0.30001721 → 1.0.30001769)
- `npm audit fix` — 2 high severity → 0 vulnerabilities

**React Hook Warnings** (`components/BotImageUpload.tsx`, `components/UpgradeModal.tsx`):
- `BotImageUpload`: `resizeImage` moved to module scope (pure utility), `handleUpload` wrapped in `useCallback`, `handleDrop` deps fixed
- `UpgradeModal`: `FREQUENCY_LABELS` moved to module scope (static lookup table, was recreating identity each render)

**Arena Leaderboard** (`components/arena/ArenaWithStaking.tsx`):
- Filter `total_trades > 0` on `rankedBots` — excludes bots that never traded (stuck at $10k). Cascades to podium, autonomous leaderboard, overall leaderboard, hero/footer count text.

---

## 2026-02-11 - Hyperliquid Phase 4 + 4.5: Polish, Error Handling, Position Tracking Fixes

**Planning Doc**: [DOCS/todo/HYPERLIQUID_INTEGRATION.md](DOCS/todo/HYPERLIQUID_INTEGRATION.md)

**Error Handling** (`trading/live/hyperliquid_service.py`):
- Error classifier: `_classify_error()` categorizes insufficient_balance, rate_limit, credentials_expired
- Retry logic: 2 retries with exponential backoff (1s → 2s) for rate limits + network errors
- Fill error extraction: checks `statuses[]` for errors (top-level "ok" ≠ filled)
- Zero-balance detection: `_calculate_position_size()` returns 0.0, caller rejects with clear message

**Telegram Publishing** (`signals/publishing_service.py`, `ggbot.py`):
- Exit notifications added to `close_position()` — same pattern as Symphony
- `live_tag` field threads through orchestrator → publishing service for "Live on Hyperliquid" badge
- Entry messages already worked (mode-agnostic), just needed `live_tag` enrichment

**Position Tracking Fixes** (`hyperliquid_service.py`, `dashboard_data.py`):
- `_close_stale_trades()` — closes old `live_trades` before new insert (position flip handling)
- Dashboard enrichment: `current_price` from LivePriceService (was None), `opened_at` from `live_trades.created_at` (was None)
- `trade_id=batch_id` in `log_activity_safe()` — activity timeline can now link entries to trades
- SL/TP trigger order logging: detailed params + response statuses for debugging

**DB Constraints**:
- `valid_trading_mode` on `configurations`: added 'hyperliquid'
- `account_snapshots_trading_mode_check`: added 'hyperliquid'

**Documentation** (`trading/README.md`, `ACTIVE.md`):
- Full Hyperliquid section in trading/README.md (architecture, trust model, error table, endpoints)
- ACTIVE.md: Hyperliquid in trading modes, bot stats, capabilities, API endpoints, user_profiles schema

---

## 2026-02-09 - Hyperliquid Phase 3: Dashboard Monitoring + Account Adapter

**Planning Doc**: [DOCS/todo/HYPERLIQUID_INTEGRATION.md](DOCS/todo/HYPERLIQUID_INTEGRATION.md)

**Summary**: Hyperliquid positions and P&L now flow through dashboard SSE. Per-bot P&L tracking via symbol attribution (shared wallet, per-bot cumulative P&L). Same pattern as Symphony — chart shows "Cumulative P&L" from $0.

**New: HyperliquidAccountAdapter** (`core/monitoring/adapters/hyperliquid_adapter.py`):
- Queries `Info.user_state()` (118ms) for account balance, margin, positions
- Cross-references `live_trades` to attribute positions to specific bots by symbol
- Computes per-bot realized P&L from `user_fills_by_time()` (77ms)
- Detects closed positions via fill history, logs `trade_exit` activities
- Caches wallet address per user_id to avoid repeated Vault lookups

**Backend** (`ggbot.py`, `dashboard_data.py`, `account_snapshot.py`, `universal_account_monitor.py`):
- `POST /api/v2/positions/hyperliquid/{batch_id}/close` — close with ownership verification
- `/bot/{config_id}/account` + `/positions` handle `trading_mode='hyperliquid'`
- SSE CTE: added `UNION ALL` for Hyperliquid `live_trades` in `open_positions`
- `_enrich_live_positions_and_accounts()` fetches real positions from Info API, groups by user_id
- `total_equity` property: returns `total_pnl` for all live modes (per-bot cumulative P&L)
- `UniversalAccountMonitor`: 4 adapters (paper/symphony/aster/hyperliquid)

**Frontend** (`PerformanceChart.tsx`, `PositionsTable.tsx`):
- `source: 'hyperliquid'` triggers cumulative P&L mode (start at $0, title: "Cumulative P&L")
- Position close routing via `/api/v2/positions/hyperliquid/{batch_id}/close`

**Info API Exploration** (`scripts/tests/test_hyperliquid_info_api.py`):
- 12 endpoints tested: user_state, open_orders, frontend_open_orders, user_fills, user_fills_by_time, all_mids, candles_snapshot, meta_and_asset_ctxs, portfolio, user_fees, user_funding_history, user_non_funding_ledger_updates, extra_agents, user_rate_limit
- Latency: 73-258ms range. 228 perp markets, 512 mids (includes spot), 10,435 req/min cap

**CLAUDE.md**: Added `npx tsc --noEmit` as type-check command; documented OOM risk with `npm run build` (Web3 deps)

---

## 2026-02-09 - Hyperliquid Phase 2: Forge Integration (Live Trading)

**Planning Doc**: [DOCS/todo/HYPERLIQUID_INTEGRATION.md](DOCS/todo/HYPERLIQUID_INTEGRATION.md)

**Summary**: Replaced Symphony/Aster with "Live Trading" (powered by Hyperliquid) across Forge. Users can create live bots, manage funds, and activate with credential + unique-symbol enforcement.

**Backend** (`ggbot.py`):
- `/api/v2/user/profile` returns `hyperliquid_connected` (DB check for non-null wallet address)
- `start_bot` endpoint: Hyperliquid credential check + unique symbol enforcement per active bot (prevents position netting conflicts)

**New Components**:
- `LiveTradingSetupModal.tsx` — modal wrapper with `next/dynamic` SSR-disabled import
- `LiveTradingModalContent.tsx` — full Web3 flow (connect wallet, deposit, authorize, manage funds, test trade, disconnect) extracted from `HyperliquidSetup.tsx`

**Modified Frontend** (10 files):
- `SettingsModal.tsx` — replaced ~300 lines Symphony/Aster with "Live Trading" section (connected status + manage funds, or setup CTA)
- `BotCreationModal.tsx` — 2 trading modes (Paper + Live Trading); opens setup modal for unconfigured users; removed `symphonyAgentId`
- `page.tsx` — updated `TradingMode` to `'paper' | 'hyperliquid'`, removed symphony references
- `TradeSettings.tsx` — allocation indicator bar showing margin distribution across live bots
- `ActivationBar.tsx` — added `'hyperliquid'` to `isLiveTrading` check
- `UserProfile.tsx` — live trading balance display in dropdown
- `permissions.tsx` — added `refreshProfile()` to context for real-time state updates after connect/disconnect
- `RiskAcknowledgmentModal.tsx` — accepts `'hyperliquid'` trading mode
- `api.ts` — `hyperliquid_connected` on `UserProfile`, `'hyperliquid'` on `BotConfiguration.trading_mode`
- `ConfigureLayout.tsx` — passes `allBots` through to TradeSettings for allocation calculation

---

## 2026-02-03 - SSE Dashboard Query Optimization (Denormalize initial_equity)

**Purpose**: Eliminate expensive `DISTINCT ON` scan of activities table in dashboard SSE query.

**Problem**: Dashboard query ran every 5s per user, included `first_activities` CTE that scanned entire activities table to find first `total_equity` per bot. Accounted for ~80% of DB time.

**Solution**: Denormalize `initial_equity` onto `configurations` table.

**Database** (`configurations` table):
- Added `initial_equity NUMERIC` column
- Backfilled 478 existing bots using reset-aware query (respects `last_reset_at`)
- Arena bots correctly use $10,000 post-reset baseline

**Code Changes**:
- `core/sse/dashboard_data.py` - Removed `first_activities` CTE, now uses `bc.initial_equity`
- `trading/paper/supabase_service.py:731-755` - `reset_account()` sets `initial_equity = 10000`
- `core/services/config_service.py:253-264` - New bots created with `initial_equity = 10000`
- `core/config/repository.py:129-132` - New bots created with `initial_equity = 10000`
- `core/common/db.py:187-191` - New bots created with `initial_equity = 10000`
- `core/config/insert_config.py`, `import_user_config.py` - Same

**Note**: Arena leaderboard (`api/public.py`) unaffected - uses separate query with `COMPETITION_START` filter and `paper_accounts.initial_balance`.

**Additional Indexes**:
- `idx_configurations_is_public_performance` - btree on `is_public_performance` (16 KB) - Arena filter
- `idx_activities_platform_cost` - btree on `platform_cost_usd` - Billing query optimization (21% faster)

**Arena Query Optimization** (`api/public.py`):
- Problem: Arena query took 9.7s due to JSONB extraction (`config_data->...`) for 81k rows
- Root cause: JSONB fields extracted inside DISTINCT ON, so 81k extractions instead of 30
- Fix: Split into two queries - (1) bot metadata with JSONB (30 rows), (2) hourly snapshots without JSONB (7k rows)
- Also: Downsample to hourly using `DISTINCT ON`, increased cache TTL 60s → 300s
- Result: **9.7s → 0.46s (21x faster)** 🚀

---

## 2026-02-02 - Billing Fixes + Memory Leak Fix + DB Indexes

**Purpose**: Fix prepaid credit tracking bug, failed payment handling, memory leak, and slow queries.

**Database Indexes** (Arena query optimization):
- Added `idx_configurations_state` - btree on `state` column (16 KB)
- Added `idx_snapshots_timestamp` - btree on `timestamp` column (3.6 MB)
- Arena leaderboard query was 8.4s average, should improve significantly

**Prepaid Balance Bug** (`core/monitoring/usage_monitor.py`, `api/admin.py`):
- Bug: Prepaid users showed incorrect balance because Stripe Credit Grants only decrease when applied to invoices (prepaid users never get invoices)
- Fix: `get_balance_status()` now uses all-time `SUM(platform_cost_usd) FROM activities` for prepaid tier instead of monthly Redis counter
- Admin page (`api/admin.py:717-739`) also fixed - calculates `available = total_purchased - total_usage_cost` for prepaid users
- `cache_usage_summaries()` also fixed - UserProfile dropdown now shows correct balance for prepaid users
- Added `_get_total_purchased_from_stripe()` helper to sum all Credit Grant amounts

**$10 Spending Cap** (`ggbot.py`, `scripts/add_billing_thresholds.py`):
- Added `billing_thresholds.amount_gte = 1000` to all usage_based subscriptions
- Stripe auto-generates invoice when usage hits $10, limiting bad debt exposure
- Script updated 7 existing subscriptions

**Payment Failure Handling** (`ggbot.py:4757-4860`):
- Enhanced `handle_payment_failed()` webhook handler
- Now pauses ALL user's bots on payment failure (not just subscription)
- Sends email notification via Resend
- Publishes to Redis for real-time UI updates

**Memory Leak Fix** (`ggbot.py:314-334`, `:833-854`, `:1006-1022`):
- Bug: `_extraction_engines` and `_decision_engines` dicts grew unbounded (300MB → 1GB over hours)
- Fix: LRU eviction using `OrderedDict` with `MAX_EXTRACTION_ENGINES=30`, `MAX_DECISION_ENGINES=50`
- Oldest engines evicted with proper cleanup (`ExtractionEngineV2.cleanup()` disconnects data client)

---

## 2026-01-30 - SEO Infrastructure + Blog Launch + Keyword Research
Sitemap, robots.txt, OG images (Playwright), Twitter cards, PWA icons, JSON-LD schema. Blog infra with MDX, RSS feed, first article "What is Vibe Trading?". 4-tier keyword strategy, Q1 content calendar. See `frontend/SEO.md`.

---

## 2026-01-30 - Performance: Remove UX Delays + Refactor Planning
Removed 6 `asyncio.sleep()` calls (13s/cycle saved). New `DOCS/todo/ORCHESTRATOR_REFACTOR.md` — root cause: psycopg2 sync blocking, not architecture. 4-phase plan replaces over-engineered 7-phase.

---

## 2026-01-30 - Infrastructure: Supabase Pooler + Mobile Touch Fix
Supabase disk IO exhausted → upgraded compute, switched to Pooler (`pooler.supabase.com`). 46ms connect, 7ms queries. Mobile touch fix: `mousedown`→`pointerdown` for 3-dot menu.

---

## 2026-01-30 - Landing Page Quick Wins + Webapp Testing Skill
SocialProof component (live stats), CTAs after Process/Features sections, shadow removal, Telegram FAQ link, header Sign Up. Playwright webapp-testing skill installed.

---

## 2026-01-30 - Enriched Preprocessor Summaries
All 21 preprocessors updated with conditional signals (divergence, crossovers, squeeze, acceleration). Token-neutral — signals only appear when detected. `⚠️` warnings, `✓` confirmations.

---

## 2026-01-29 - Rei Compact Format + Behavior Prompt
Payload ~22KB→~7KB via `to_compact()` on all 21 preprocessors + timeframe filtering. Universal compact schema ~400 bytes/indicator. Strategy file `trading/strategies/rei_core.md`.

---

## 2026-01-28 - Rei Scheduled Bot Engine (Experimental)
`decision/rei_engine.py` — alternative to LLM decisions. `rei_enabled` config flag routes to Rei API. Feedback loop reports trade outcomes for inference-time learning. Test bot: "The Nightingale".

---

## 2026-01-28 - Kimi K2.5 Model Update + LLM Update Workflow
Kimi standard/premium→k2.5. New `decision/llm_providers/MODEL_UPDATE.md` — systematic update checklist for 21 model×tier combinations.

---

## 2026-01-27 - Forge React Query + Arena Podium Fixes
`useDataSources()` (10min), `useBotList()`, `useLatestActivity()` (30s). Removed ~60 lines manual fetch boilerplate. Arena podium: `isFetching` spinner, inline legend, taller chart.

---

## 2026-01-27 - Frontend Performance & Arena Redesign
React Query at root (30s stale, 5min gc). Redis arena cache 60s. SVG sparklines, lightweight-charts podium. Bundle 212KB→168KB (44KB reduction). See [DOCS/completed/FRONTEND_PERFORMANCE_REACT_QUERY.md].

---

## 2026-01-27 - USX Arena Betting (Full Stack)
wagmi/viem/RainbowKit v2 on Scroll. BetModal: 6-step flow (approve→deposit→record). Public pledge endpoint (wallet=identity). sUSX preview, cooldown warning. See [DOCS/todo/USX_STAKING_MODAL.md].

---

## 2026-01-23 - Market Data Intelligence Update
ggShot soft-disabled (90+ days stale). Astrology indicators: `lunar_phase`, `mercury_status` under sentiment_social via Grok (~$0.005/query). See [DOCS/completed/MARKET_DATA_INTELLIGENCE_UPDATE.md].

---

## 2026-01-23 - Onboarding Tour & Strategy Advisor UX
5-step tutorial overlay post-first-bot. "Explain Strategy" + "Update Strategy" + "Analyze Performance" buttons. Border highlight, pointer-events pass-through, localStorage persistence.

---

## 2026-01-22 - Rei Integration Hardening
Opus 4.5→Haiku (follows instructions better). System prompt hardening: forbidden phrases, EXIT=immediate, ENTER≥50%. Confidence-based sizing (70% confidence = 70% max size). Timeout 60s→180s.

---

## 2026-01-22 - Telegram Publishing (Platform Bot)
PM2 `telegram-bot` service with /start, /chatid, /help commands. Entry + exit notifications with P&L display. Publishing service checks all paid tiers. See [DOCS/completed/TELEGRAM_PUBLISHING.md].

---

## 2026-01-21 - ggArena Season 1 Launch
`arena_reset.py` → 14 bots reset. `arena_registered_at` column. Competition start filter. Late registration with auto-reset. See [DOCS/completed/GGARENA_SEASON1_LAUNCH.md].

---

## 2026-01-21 - Unified Modal System
Unified `Modal` component (Framer Motion, responsive sizing, full-screen mobile, focus trap). Migrated 6 modals from 3 different systems. See [DOCS/completed/UNIFIED_MODAL_SYSTEM.md].

---

## 2026-01-21 - Prepaid Tier Implementation
Separate `prepaid` enum (was confusingly `usage_based`). Pre-LLM credit check (fail-closed). Meter reporter excludes prepaid. Usage monitor: hard block on depletion. See [DOCS/completed/PREPAID_TIER.md].

---

## 2026-01-20 - Onboarding Revamp & Free Test Runs
5-step typeform bot creation. 3 archetypes (Contrarian/Compass/Arbiter). Strategy generation via Haiku. Free test runs: `first_run_used` + `free_runs_remaining=3`. All models/frequencies unlocked for everyone. See [DOCS/completed/ONBOARDING_REVAMP.md].

---

## 2026-01-16 - Rei Agent Integration
Claude+Rei hybrid: Claude orchestrates, Rei reasons+learns. 3 MCP tools (query/consult/report). Session buffer for ~15-20KB market data. See [DOCS/completed/REI_AGENT_INTEGRATION.md].

---

## 2026-01-16 - Frontend Usage Display
`getUsageSummary()`, `getConfigUsage()` API methods. UserProfile: credit/metered adaptive display. ActivationBar: per-bot daily cost estimate with 5min refresh.

---

## 2026-01-15 - Real-Time Usage Tracking & Billing Hardening
Redis INCRBYFLOAT counters on every LLM call. UsageMonitor in account-monitor (60s checks, auto-pause on depletion). 4 usage API endpoints. Idempotency fixes for Stripe + NOWPayments. See [DOCS/completed/USAGE_BILLING_TRACKING.md].

---

## 2026-01-13 - Frontend Snappiness Phase 1
Optimistic updates for delete/duplicate/rename/reset (0ms perceived). Skeleton loading states. Bot switching skeleton (prevents stale flash).

---

## 2026-01-13 - Market Intelligence Cost Optimization
Fixed Grok cache key bug (all queries shared one key). Extended TTLs (VIX 15min→4hr, etc). $50/week→$7-10/week (80-86% reduction). Arena reset script.

---

## 2026-01-13 - Bot Analysis Framework + Platform Defaults
`core/services/performance_analyzer.py` — pattern correlation, confidence calibration, Haiku synthesis. Default SL/TP: 5%/10%→1.5%/3% (old defaults never triggered). LLM tier display names.

---

## 2026-01-13 - Strategy Advisor Fixes
f-string bug: unescaped `{...}` in prompt → Ellipsis format specifier error. Auto-scroll via `useRef` + `requestAnimationFrame`.

---

## 2026-01-08 - Credit Packs & Crypto Payments
Stripe credit packs ($10-$100) + NOWPayments crypto. Credit Grants auto-apply to invoices. HMAC-SHA512 IPN verification. See [DOCS/completed/CREDIT_PACKS.md].

---

## 2026-01-07 - ggArena Season 1 Launch Prep
Arena UX overhaul: isolated countdown timer, restructured bot details, varied CTAs, $2,500 prize breakdown. Registration endpoints + modal. nginx 502 fix (300s timeout, buffering off). APScheduler jitter 15s→30s.

---

## 2026-01-06 - Reasoning Tier Fix + Billing Accuracy
`reasoning_tier` field missing from Pydantic model → all bots ran standard tier. Billing switched to actual OpenRouter `usage.cost` (was static table). Netflix-style upgrade modal with real cost estimates.

---

## 2026-01-04 - Strategy Advisor Performance Analysis
`performance_analyzer.py` — universal pattern extraction, confidence calibration, exit classification. `/api/v2/assistant/analyze/{config_id}`. "Discuss with Advisor" sends report to chat.

---

## 2026-01-04 - Activity Modal Redesign
Centered modal with carousel navigation (swipe/arrows). Type-specific formatters. Structured REASONING format (KEY_SIGNAL/SUPPORTING/RISK/SUMMARY) in decision prompts.

---

## 2025-12-28 - Symphony Position Display Fix
SSE enrichment function existed but never called. Fixed source filter, added collateral/PnL/liquidation fields.

---

## 2025-12-27 - Error Log Fixes + Arena Timeline + TradeSettings Fix
binance_funding gateway pattern, WebSocket queue 100→1000, timeframe-aware Redis TTL. Arena 3 public endpoints. TradeSettings nested object data loss fix.

---

## 2025-12-19 - ggArena Bot Strategy Tuning
7 arena bots prepared. Action bias 0.55+ (was 0.75+). Regime gating: block longs against bearish 1H.

---

## 2025-12-17/18 - Bot Images + Arena Page + TV Timeline
Image upload, public leaderboard /arena, dual-mode timeline (Activity/Performance). Bot limit removed.

---

## 2025-12-15 - Account Metrics Standardization
`metrics_calculator.py` — single source of truth. 6 duplicate formula implementations → 1. `total_equity` column on activities.

---

## 2025-12-14 - Admin Dashboard Equity Fix + Bot Comparison
Removed margin_used double-counting. Bot equity comparison chart endpoint.

---

## 2025-12-10 - Position Sizing Simplification (BREAKING)
Confidence-based only. Deleted PositionSizingMethod enum. max_position_percent→max_margin_percent. Defaults: 5x leverage, 20% margin, 1.5% SL, 3% TP.

---

## 2025-12-05 - Admin Dashboard + Signal Filtering + Strategy Advisor
/admin with 13 endpoints. Symphony 100-symbol filter. Strategy character creation UX. Reasoning tiers (economy/standard/premium).

---

## 2025-12-04 - Unified Config Saving
Batched save: 40+ API calls → 1, 5s debounce. Symphony win_rate overflow fix.

---

## 2025-11-30 and earlier — Compressed Archive

**Nov 2025**: Activity timeline data visibility, balance tracking fixes, legal pages + AsterDEX integration (33 symbols), strategy advisor auto-save, universal AI assistant + metered billing (Stripe Meters), snapshot timeline + activities overhaul + universal account monitoring, metered billing infra, confidence sizing + OpenRouter UI, config system cleanup v2.2, agent session resumption, TradingView timeline + agent v4, ceremonial brutalism rebrand (obsidian/ivory/brass), agent Phase 4c autonomous trading, AsterDEX Phase 1, agent Phase 3 + maintenance mode, activity timeline viewer.

**Oct 2025**: Market intelligence LIVE (8 Grok sources, $195/mo→$7-10/wk after optimization), intelligence orchestrator, ggShot universal data (878 signals), hybrid price service (WebSocket+REST), Symphony integration + universal data layer, Resend email (189 users), trading fixes (position sizing, P&L double leverage), GPT-5 Responses API, Stripe monetization ($29/mo Pro).

**Pre-Oct 2025**: APScheduler zero-drift, signal validation, paper trading engine, frontend SSE, disk crisis (26GB Docker logs), multi-exchange failover.

---

**Documentation**: See README.md (architecture), ACTIVE.md (production status), TODO.md (roadmap)
