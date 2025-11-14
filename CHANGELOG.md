# CHANGELOG - ggbots Platform

Complete history of features, fixes, and improvements. For current status see ACTIVE.md, upcoming work see TODO.md.

---

## 2025-11-14 - Agent Strategy Auto-Save Fix

**Bug Fix**: Agent strategy auto-save was overwriting bot names with "Untitled Bot". Fixed by always passing `config_name` and `config_type` parameters during auto-save to preserve existing values.

---

## 2025-11-14 - Critical Bug Fixes

**Bug Fixes**: Fixed three production-blocking issues identified in error logs.

- Fixed meter reporter to skip free users gracefully (INFO log instead of ERROR)
- Fixed orchestrator missing `user_service` attribute (blocking bot execution)
- Fixed timeline metadata iterating over dict keys instead of assets array

**Files Modified**: `billing/stripe_meter_reporter.py`, `ggbot.py`, `api/activities.py`

---

## 2025-11-13 - Metered Billing System Production Ready

**Stripe Metered Billing**: Fixed and tested complete end-to-end metered billing system. Daily usage reporting operational, permission system enforces payment status, webhooks handle subscription lifecycle.

- Fixed `stripe.billing.MeterEvent.create()` API call in meter reporter
- Tested: $0.0072 usage successfully reported to Stripe, activities marked as reported
- Verified: Permission system blocks past_due users from bot activation
- Documented: Complete implementation guide in `DOCS/completed/METERED_BILLING_IMPLEMENTATION.md`

**Status**: Production ready. APScheduler runs daily at midnight UTC. All webhook handlers implemented (checkout, subscription updates, payment failures, cancellations).

**Files Modified**: `billing/stripe_meter_reporter.py` (API fix), `DOCS/completed/METERED_BILLING_IMPLEMENTATION.md` (new)

---

## 2025-11-13 - Metered Billing Infrastructure & Subscription Tier Updates

**Stripe Integration**: Completed core metered billing infrastructure with daily usage reporting and subscription tier architecture.

- **LLM Pricing Service Fix**:
  - Fixed schema mismatch in `llm_pricing_service.py` (queried non-existent `pricing_input_per_1m_thinking` column)
  - Updated to query actual schema: `pricing_input_per_1m` and `pricing_output_per_1m` from `llm_models` table
  - Token prices same regardless of thinking mode (extended reasoning uses more tokens, not different rates)

- **Stripe Meter Reporting**:
  - Created `billing/stripe_meter_reporter.py` for daily usage aggregation and reporting
  - Uses existing `STRIPE_SECRET_KEY` from .env (no new credentials needed)
  - Integrated with APScheduler (midnight UTC daily job, not cron)
  - Reports pre-computed dollar amounts to Stripe Meter API (`llm_tokens_usd` event)
  - Query aggregates unreported `platform_cost_usd` by user_id from activities table

- **Billing API Endpoints**:
  - Added `/api/v2/billing/usage` - current billing period summary (total cost, token breakdown, model breakdown)
  - Added `/api/v2/billing/usage/breakdown` - detailed analysis (by_bot, by_day, with optional filters)
  - Both endpoints query activities table with billing indexes for fast aggregation

- **Subscription Tier Architecture**:
  - **FREE**: Can browse and configure bots, cannot activate (no LLM calls)
  - **USAGE_BASED**: Pay per LLM call with 70% markup, no base fee (new tier)
  - **PRO**: $29/month + usage + agent access (renamed from 'ggbase')
  - Updated `user_profile.py` with `can_activate_bots()` and `can_use_agents()` permissions
  - Created SQL migration in `SQL.md` (adds 'usage_based' and 'pro' tiers, migrates existing users)

- **End-to-End Validation**:
  - Ran live bot execution showing accurate token tracking in activities table
  - Verified: OpenRouter returns tokens → llm_pricing_service calculates costs → activities logged with billing columns
  - Example: 2,251 tokens tracked with $0.000675 provider cost, $0.001148 platform cost

**Impact**: Core metered billing infrastructure operational. Every LLM call tracked with costs and ready for Stripe reporting. Subscription tier model ready for frontend checkout integration.

**Files Modified**: core/services/llm_pricing_service.py, core/domain/user_profile.py, billing/stripe_meter_reporter.py (new), billing/__init__.py (new), ggbot.py (scheduler + 2 endpoints), SQL.md (migration), TODO.md, CHANGELOG.md

**Pending**: Webhook handler for `invoice.payment_failed` event, frontend checkout flow updates

---

## 2025-11-13 - Agent fixes, RLS security, Aster position sizing

- **Security**: RLS migration executed - `activities`, `agent_sessions`, `llm_models` tables secured, public bot performance via `is_public_performance` flag
- **Agent**: Fixed startup crashes - removed `ACTIVITY_PRIORITY` import, `priority` param from log_activity calls, added `timezone` import
- **Agent**: Fixed trading mode detection - `get_configuration()` now returns `trading_mode` column, agents start in correct mode (aster/paper/symphony)
- **Aster**: Switched to `/fapi/v3/account` endpoint - proper equity calculation, position sizing now works correctly
- **Aster**: Fixed position sizing - uses `availableBalance + totalPositionInitialMargin` instead of negative wallet balance
- **Aster**: Complete income history - switched from `userTrades` to `income` endpoint, recovered 26 missing trades (Nov 4-6), correct cumulative P&L ($-5.89 vs incorrect $-43.52)
- **Aster**: Fixed execute_trade response format - now matches paper trading with complete fields (trade_id, entry_price, size_usd, account_balance, etc)
- **Frontend**: Null safety for price fields - added `Number(x || 0)` guards to prevent `.toLocaleString()` crashes on null values in PositionsTable, PerformanceChart, TradeHistoryModal, timeline components
- **Files**: core/config/config_main.py, agent/run_agent.py, agent/mcp_server.py, trading/live/aster_service_v3.py, api/agent.py, api/activities.py, frontend components

---

## 2025-11-13 - Symphony Timeline Support: Multi-Mode Activity Tracking

**Timeline API**: Added full Symphony support to activity timeline endpoints, enabling unified timeline view across all trading modes.

- **Symphony Balance Series**: Queries Symphony API `get_trade_history()` for closed trades with P&L
- **Symphony Metadata**: Queries Symphony API `get_account_metrics()` for win rate, trade count, cumulative P&L
- **Activities Endpoint Fix**: Removed non-existent `priority` column from query (use `importance` field)
- **Multi-Mode Support**: Timeline now works for paper, Symphony, and Aster bots
- **Account-Wide Metrics**: Symphony & Aster show account-wide performance (shared wallet design)
- **Test Suite**: Created `tests/test_symphony_timeline.py` validating all 3 endpoints

**Impact**: Symphony bots now display complete activity timelines with trade history and performance metrics from Symphony API. All trading modes (paper/symphony/aster) supported in timeline view.

**Files Modified**: api/activities.py (3 endpoints), tests/test_symphony_timeline.py (new)

**Note**: Aster & Symphony use account-wide metrics (shared wallets), paper trading is per-bot.

---

## 2025-11-12 - Activities Unification & Token Tracking Infrastructure

**Backend Integration**: Implemented metered billing foundation with unified activity logging and per-call LLM cost tracking.

- **Schema Migration**:
  - Removed `priority` column from activities table (design mistake)
  - Added 10 token tracking columns (provider, model, thinking_mode, input_tokens, output_tokens, reasoning_tokens, provider_cost_usd, platform_cost_usd, stripe_reported, stripe_reported_at)
  - Created 2 billing indexes (user-level and per-bot aggregation)

- **Activity Logger Refactor**:
  - Removed all priority logic
  - Added `log_llm_activity()` function for LLM calls with token tracking
  - Added `log_llm_activity_safe()` non-blocking wrapper
  - Updated activity types taxonomy (removed old types, added: market_query, llm_thought, trade_entry, trade_exit, trade_update, agent_wait, observation_recorded, strategy_updated, signal_received)

- **LLM Pricing Service**:
  - Created `core/services/llm_pricing_service.py`
  - Queries `llm_models` table for current pricing
  - Calculates provider cost and platform cost with 70% markup
  - Handles thinking mode pricing (extended reasoning costs more)

- **Decision Engine Integration**:
  - Updated `_call_llm()` to return (response, metadata) tuple
  - Added `_log_llm_activity()` helper method for consistent token tracking
  - Updated 3 LLM callsites: signal validation, opportunity analysis, position management
  - Updated 3 save methods to log `llm_thought` activities with full cost tracking
  - Backward compatible: Still writes to `decisions` table (marked deprecated)

**Impact**: Every LLM call in scheduled_trading and signal_validation bots now tracked with costs. Foundation ready for Stripe Meter integration.

**Files Modified**: 3 backend files (activity_logger.py, llm_pricing_service.py [new], engine_v2.py)

**Database**: activities table now 23 columns with billing indexes

---

## 2025-11-11 - Confidence-Based Position Sizing: Verified & Production-Ready

**Testing**: Comprehensive validation of confidence-based sizing implementation across paper/symphony/aster modes.

- **Test Suite**: Created `tests/test_confidence_sizing.py` with multi-mode validation
- **Formula Verified**: `margin = confidence × max_position_percent × balance`, `position_size = margin × leverage`
- **Paper Trading**: ✅ All tests passed (10x leverage, 25% max position, $10k balance)
- **AsterDEX**: ✅ All tests passed (10x leverage, 25% max position, $100 mock balance)
- **Symphony**: ✅ Weight calculation verified (15x leverage, 25% max position)
- **Agent Defaults**: Updated bot creation to use confidence_based sizing (10x leverage, 25% max)
- **Validation Fix**: Added 'agent_driven' to valid analysis frequencies
- **Vault Fix**: Symphony credential deletion now properly removes vault secrets (no orphaned secrets)
- **Trading Mode Fix**: Removed old 'live' constraint, fixed 'symphony' validation (dropped duplicate constraint)
- **Backend Updates**: Fixed 5 locations checking `trading_mode == 'live'` → `trading_mode == 'symphony'`

**Impact**: Confidence-based position sizing validated and ready for production. Agent bots automatically calculate position sizes from confidence scores (0.0-1.0), simplifying UX. All vault/validation bugs resolved.

**Files Modified**: core/config/models.py, core/auth/vault_utils.py, ggbot.py (5 locations), frontend/app/forge/page.tsx, tests/test_confidence_sizing.py (new)

---

## 2025-11-11 - UI Enhancements: OpenRouter Model Selection & Theme-Adaptive Design

**Frontend Integration**: Completed Phase 0 OpenRouter migration with polished model selection UI and theme system improvements.

- **Model Selection UI**:
  - Dynamic model cards fetched from `/api/v2/llm-models` (7 models: Grok, DeepSeek, Kimi, Qwen, Gemini, GPT-5, Claude Sonnet 4.5)
  - Model logos in colored circular backgrounds with brand-specific hex codes (qwen: #8760ec, deepseek: #617aef, claude: #ff6938, grok: #030303, gemini: #458dfb, gpt: #1d967b, kimi: #080808)
  - Pricing display per decision (formatted from nested pricing structure)
  - Thinking mode toggle (enables extended reasoning with higher token limits)
  - Default config updated to schema v2.2 with OpenRouter support

- **Theme System**:
  - Fixed Tailwind dark mode configuration to recognize app's `[data-theme="dark"]` attribute
  - Updated 6 components with theme-adaptive button text colors (light text in light mode, dark text in dark mode)
  - Components updated: ActivationBar.tsx, StrategyEditor.tsx, BotCreationModal.tsx, EmptyState.tsx, AgentConfigurator.tsx, BotManagementMenu.tsx
  - Brass accent color (#c1a87d) now works correctly in both themes with proper text contrast

**Impact**: OpenRouter frontend integration complete, users can now select from 14 LLM variants (7 models × 2 thinking modes) with clear pricing visibility. Theme consistency improved across light/dark modes.

**Files Modified**: 7 frontend files (tailwind.config.ts, StrategyEditor.tsx, ActivationBar.tsx, BotCreationModal.tsx, EmptyState.tsx, AgentConfigurator.tsx, BotManagementMenu.tsx), 1 backend file (lib/api.ts)

---

## 2025-11-10 - CRITICAL FIXES: Config Save, SSE Dashboard, OpenRouter, Timeline, Aster Metrics

**Critical Bugfixes**: Fixed 5 errors (4 backend, 1 frontend):

1. **Config Save 404**: When `config_name` was added to SELECT statement in `get_config()`, all result array indices shifted by 1, but lines 307-308 and 321-324 weren't updated. Code was calling `result[1].isoformat()` on config_data JSON instead of `result[2]` (created_at timestamp), causing exception → `get_config()` returned `None` → 404 error. **All config saves were broken**.
   - **Fix**: Updated result indices to use correct positions (`result[2]` for created_at, `result[3]` for updated_at)

2. **SSE Dashboard SQL Error**: CTE `bot_configs` in dashboard query didn't include `config_type` in SELECT list (line 86), but line 150 tried to reference `bc.config_type`. Caused "column bc.config_type does not exist" error every 5 seconds.
   - **Fix**: Added `c.config_type` to CTE SELECT statement

3. **OpenRouter Pydantic Validation**: `LLMProvider` enum in `core/config/models.py` didn't include 'openrouter', causing validation errors when loading configs with OpenRouter models. Bot executed trades successfully but logged errors.
   - **Fix**: Added `OPENROUTER = "openrouter"` to enum

4. **TradingView Timeline Race Condition**: Frontend console error "Cannot set data: {hasLineSeries: false, dataLength: 2}". Polling interval from previous render fired after chart cleanup nulled refs, attempting to set data on destroyed chart.
   - **Fix**: Added guard in `fetchData()` to bail early if `chartRef.current` or `lineSeriesRef.current` are null

5. **Aster Bot Metrics Showing Zero**: Timeline metadata endpoint for Aster bots returned all zeros (balance, trades, win rate). Query read `trading_mode` from JSONB `config_data->>'trading_mode'` which was removed during Config System Cleanup, returned NULL, defaulted to 'paper', executed wrong code branch.
   - **Fix**: Changed query to read from table column `trading_mode` instead of JSONB field

**Impact**: All errors resolved. Config saves work, dashboard SSE streams cleanly, OpenRouter configs validate correctly, timeline charts render without warnings, Aster bot metrics display correctly.

**Root Cause**: Backend - Index offset bug and missing fields from 2025-11-10 Config System Cleanup (trading_mode moved from JSONB to table column). Frontend - Interval race condition during component cleanup.

**Files Modified**: `core/services/config_service.py`, `core/sse/dashboard_data.py`, `core/config/models.py`, `api/activities.py`, `frontend/components/tv-timeline.tsx`, `frontend/components/tv-timeline-standalone.tsx`

---

## 2025-11-10 - Configuration System Cleanup & Schema v2.2 Migration

**Technical Debt Elimination**: Comprehensive cleanup of config system accumulated over 6 months - migrated 373 bots to canonical naming, removed field duplication, fixed 3 critical bugs, added database constraints.

- **Naming Migration**: All 373 `autonomous_trading` bots → `scheduled_trading` (single source of truth)
- **Duplication Removed**: Deleted `trading.execution_mode` from JSONB (use table `trading_mode` only), removed `trading.exchange_config` legacy bloat, removed `trading.provider` from agents
- **Critical Fixes**: Agent strategy deep merge (metadata preserved), config_name query bug (no more "Untitled Bot"), SSE hardcoded config_type bug (now reads from table)
- **Database**: One-shot SQL migration (378 configs in 10s), bumped `schema_version` to 2.2, added CHECK constraints on `config_type`/`trading_mode`/`state`, made `trading_mode` NOT NULL
- **Backend**: Updated `core/config/schemas.py` (removed legacy classes, simplified validation), updated defaults in ConfigService/ggbot.py, removed ~150 lines dead code
- **Analysis**: Used code-scout to audit entire system, created 4 reference docs (2,000+ lines) documenting issues and future improvements

**Impact**: Cleaner architecture, eliminated 3 duplication bugs, prepared foundation for Pydantic discriminated union migration (v3.0)

**Files Modified**: 7 backend files, 3 frontend files, 1 database migration script
**Docs Created**: CONFIG_REVIEW.md, CONFIG_SCHEMA_ANALYSIS.md, CONFIG_ARCHITECTURE_PROPOSAL.md, CONFIG_MIGRATION_PLAN.md
**Details**: See [DOCS/completed/2025-11-10_config_system_cleanup.md](DOCS/completed/2025-11-10_config_system_cleanup.md)

---

## 2025-11-10 - OpenRouter LLM Integration (Phase 0)

**Unified LLM API**: Integrated OpenRouter for standardized access to 7 LLM providers (Grok, DeepSeek, Kimi, Qwen, Gemini, GPT-5, Claude Sonnet 4.5) with 14 total variants (thinking mode flag). Created `llm_models` reference table with pricing, added `GET /api/v2/llm-models` API endpoint, built `OpenRouterProvider` with automatic parameter handling (temperature, reasoning, max_tokens). Updated Pydantic schemas to validate OpenRouter configs. Standardized token tracking format across all models. **Not yet in production** - awaiting bot config migration and real execution testing.

---

## 2025-11-10 - Confidence-Based Position Sizing (Incomplete)

**Agent MCP Tool Simplified**: Removed manual position sizing parameters (`size_usd`, `leverage`) from `execute_trade` tool. Agents now provide only confidence score (0.0-1.0); system auto-calculates position sizes using `margin = confidence × max_position_percent × balance`. Updated ggAster bot config to `confidence_based` method with 20x leverage, 5-25% risk range. **NOT TESTED** - implementation flawed, needs review and proper testing approach. See [DOCS/completed/2025-11-10_confidence_based_position_sizing.md](DOCS/completed/2025-11-10_confidence_based_position_sizing.md).

---

## 2025-11-08 - Trading Mode Architecture Refactor

**Simplified Bot Creation + AsterDEX Integration**: Eliminated "duplicate as live" workaround, removed dead code duplication, added first-class AsterDEX support with upfront trading mode selection during bot creation.

- **Duplication Removed**: Deleted unused `config_data.trading.execution_mode` JSONB field, kept `trading_mode` table column as single source of truth
- **New Creation Flow**: Users select bot type + trading mode (Paper/Symphony/Aster) in unified modal, no more hidden duplicate-as-live button
- **AsterDEX Credentials**: Full vault integration (user_wallet + aster_wallet + private_key), Settings UI with 3-field setup, API endpoints `/api/v2/aster/*`
- **UI Updates**: Renamed "LIVE TRADING" → "SYMPHONY" badge (red), added "ASTERDEX" badge (purple), trading mode visible at creation
- **Backend Validation**: Pro tier gating, credential checks, symbol compatibility (Symphony/Aster), Symphony Agent ID UUID validation
- **SSE Dashboard**: Added Aster position/account enrichment, parallel fetching from AsterDEXV3 service alongside Symphony data
- **Cleanup**: Deleted `DuplicateAsLiveModal.tsx` (308 lines), removed `/api/v2/config/duplicate-as-live` endpoint (112 lines), net -250 lines dead code
- **Migration**: Added `user_profiles.aster_vault_id`, `aster_user_wallet`, `aster_wallet` columns (nullable), backwards compatible with existing live bots

**Impact**: Bot creation flow reduced 5→3 steps, trading mode immutable at creation (prevents confusion), Aster equal to Symphony (no second-class citizen), 450 lines dead code removed

**Follow-up** (same day):
- **Theme Consistency**: Brass color (#c1a87d) now consistent across light/dark themes, TradingView timeline + bottom sheet theme-aware with smooth transitions
- **Position Closing**: Fixed PositionsTable to route Aster close button to `/api/v2/positions/aster/{order_id}/close` (was falling through to paper logic)
- **Color Updates**: Changed Symphony badge to signal blue, Aster badge to ember red (from VIBE.md design system)

**Files**: 18 modified (10 frontend, 7 backend, 1 deleted) - See [DOCS/completed/trading-mode-refactor.md](DOCS/completed/trading-mode-refactor.md) for full details

---

## 2025-11-08 - Agent Session Resumption: Conversation Persistence

**Session Persistence**: Agents now survive crashes, restarts, and auto-compaction with full conversation memory intact using Claude Agent SDK's built-in session resumption feature.

**Implementation**:
- **Database**: Created `agent_sessions` table to store SDK session IDs for each bot
- **Session Management**: Added load/save/update functions to agent runner with automatic capture from SDK init message
- **Recovery Flow**: On restart, agent loads session_id from DB → SDK automatically restores conversation history → agent continues from last state
- **Health Monitoring**: Heartbeat updates every 10 messages to `last_active_at` for detecting hung agents
- **Compaction Resilience**: SDK preserves compacted state in sessions, eliminating context loss

**Bug Fixes**:
- **AsterDEX UUID**: Changed `activities.trade_id` from UUID to TEXT type, fixing "invalid input syntax" errors for integer orderIds
- **Activity Timeline**: Trade close events now log correctly for Aster live trading

**Impact**:
- Eliminated "amnesiac agent" problem - full memory preservation across restarts
- 80-90% reduction in context loss during crashes/compactions
- Foundation for auto-restart and health check systems

**Files**: `agent/run_agent.py` (session mgmt), `scripts/migrations/add_agent_sessions_table.sql`, `DOCS/completed/agent-session-resumption-implementation.md`

---

## 2025-11-08 - Activity Timeline Integration in Forge Monitor Tab

- **UX**: Replaced DecisionFeed + PerformanceChart with full-width TVTimeline component in Forge Monitor tab
- **Dual-Mode Component**: TVTimeline now serves both `/view/[config_id]` standalone page and `/forge` Monitor tab
- **Variant Prop**: Added `variant` prop - `embedded` (600px fixed height) vs `standalone` (full viewport)
- **Layout**: Timeline shows KPIs (Balance, P&L, Trades, Win Rate) + TradingView chart + activity markers, eliminates duplicate MetricsBar
- **Data Streaming**: Timeline polls activity API (10s interval) alongside existing SSE stream for positions - dual streams acceptable for now
- **Components Removed**: DecisionFeed carousel, PerformanceChart equity curve, TradeHistoryModal - all functionality consolidated into Timeline
- **Files**: frontend/components/tv-timeline.tsx (variant prop), frontend/app/forge/page.tsx (Monitor tab refactor)
- **Status**: ✅ Build successful, ESLint warnings pending cleanup after parallel agent work

---

## 2025-11-07 - Agent Strategy v4: Dynamic Symbol Discovery

- **Agent**: Hardcoded 7 pairs → dynamic discovery via ggshot scan (last 2 days), auto-filtered to Aster/Symphony/Paper compatibility
- **MCP Tool**: query_market_data scan mode returns active symbols when omitting symbol param, reads trading_mode from config_data
- **Bug Fixes**: Anthropic 500 retry logic + exponential backoff, trade_observation 422 Dict[str,Any], AsterDEX balance (all stablecoins)
- **Strategy**: Leverage 5-20x, check freq 15-60m/5-30m, position close discretion, SL/TP from current price emphasis
- **Files**: agent/mcp_server.py (scan mode), agent/run_agent.py (retry+logging), api/agent.py (balance+422 fix)
- **Docs**: DOCS/completed/strategy-v4-dynamic-symbol-discovery.md

---

## 2025-11-07 - TradingView Activity Timeline with Live Agent Status

**Consolidated Timeline System**: Replaced basic activity viewer with professional TradingView Lightweight Charts integration featuring live status indicators, activity markers, and comprehensive market data display.

**Key Features**:
- **TradingView Integration**: Financial-grade line chart showing P&L over time with 700+ data points
- **Activity Markers**: Trade entries (green ↑/red ↓ arrows), market queries (blue ○), agent thoughts (brass ○), waits (ivory ○)
- **Live Status**: Pulsing colored dot showing current agent activity with countdown timers for waits
- **Market Data Display**: Bottom sheet showing preprocessed technical indicators (trend, patterns, levels) and market intelligence
- **Grouped Activities**: Multiple activities at same timestamp consolidated into single marker with list view
- **Interactive**: Click markers to view full details, hover for tooltips, markdown rendering for analysis

**Backend Enhancements**:
- **Enhanced Activity Logging**: Market queries now log full preprocessed data (200-500 analytical fields per query)
- **Total Equity Calculation**: Fixed AsterDEX balance reporting (wallet + unrealized P&L instead of just available balance)
- **Bug Fixes**: Agent crash on None result, activity logging UUID errors, position sizing accuracy

**Technical Implementation**:
- **Chart**: TradingView Lightweight Charts v4.2.0 with brass color scheme, $ formatting, no price line
- **Markers**: Priority-based (trades > thoughts > queries > waits), sorted chronologically, size/color differentiated
- **Bottom Sheet**: Framer Motion slide-up drawer with drag-to-dismiss, type-specific field rendering
- **Status System**: Real-time updates every second, colored by activity type, countdown for agent waits
- **Routing**: Consolidated `/timeline-v2/` → `/view/`, `aster.ggbots.ai` routes to new timeline

**Files Changed**: 8 files (tv-timeline.tsx, bottom-sheet.tsx, middleware.ts, aster_service_v3.py, api/agent.py, mcp_server.py, run_agent.py, routing consolidation)

**Impact**: Professional trading analytics experience, full transparency into agent decision-making process, competition-ready monitoring for AsterDEX trading.

---

## 2025-11-06 - Brand Refresh: Ceremonial Brutalism Design System

Complete platform rebrand to match trade37's ceremonial brutalism aesthetic. Replaced colorful multi-agent system with unified brass accent, upgraded to premium editorial fonts, and converted all 56 emojis to professional Lucide icons.

**Key Changes**:
- **Colors**: Obsidian/ivory/brass palette with dual dark/light themes ("obsidian and metal" / "parchment and stone")
- **Typography**: Bodoni Moda (display), Space Grotesk (sans), IBM Plex Mono (mono)
- **Icons**: All emojis replaced with Lucide React icons (tree-shakeable, scalable, consistent)
- **Buttons**: Emerald → brass throughout forge, brass text on obsidian for contrast
- **Pipeline**: Agent extraction/decision/trading now use light/medium/dark brass variants

**Files Modified**: 18 files (design system, landing page, forge components)

**Status**: ✅ Build successful, production-ready

**Full Documentation**: See `DOCS/completed/REBRAND.md` for complete implementation details, icon mappings, and migration guide.

---

## 2025-11-04 - AsterDEX Position Management: Agent Can Now Close Trades

**Database Schema Enhancement**:
- **Added `symbol` column to `live_trades` table**: VARCHAR(20) column to store trading pair for position-trade matching
- **Index**: Created `idx_live_trades_symbol` on (config_id, symbol, closed_at) for fast lookups
- **Migration**: Backfilled 2 existing open trades with "BTC/USDT" symbol

**Trade Recording Fix** (`trading/live/aster_service_v3.py`):
- **Updated `_save_live_trade_record()`**: Added `symbol` parameter, saves universal symbol format (e.g., "BTC/USDT") to database
- **Updated caller**: `execute_trade_intent()` now passes symbol when creating trade records (line 546)
- **Database**: INSERT statement now includes symbol column (line 714)

**Position Matching Fix** (`trading/live/aster_service_v3.py`):
- **Updated `get_open_positions()`**: Queries database for open trades by config_id, builds symbol → batch_id map
- **Matching Logic**: Matches exchange positions with database records by symbol (lines 730-756)
- **Return Value**: Each position now includes correct `batch_id` for the agent to use when closing

**Issue Resolved**:
- **Problem**: Agent couldn't close Aster positions because `batch_id` was None in position data
- **Root Cause**: `live_trades` table had no symbol column, making it impossible to match exchange positions with database trade records
- **Solution**: Added symbol column, populate it during trade creation, use it to match positions with their batch_ids
- **Impact**: Agent can now properly close positions using `close_position(trade_id='7215356800', reasoning='...')`

**Files Changed**:
- `trading/live/aster_service_v3.py`: 3 methods updated (_save_live_trade_record, execute_trade_intent, get_open_positions)
- Database: 1 column added, 1 index created, 2 trades backfilled

**Status**: ✅ Agent position closing operational for Aster live trading

---

## 2025-11-03 - Agent Phase 4c: Autonomous Mode Launch (24/7 Trading Live!)

**Confirmation Flow Removed** (Backend):
- **Tool**: Replaced `request_autonomous_mode` with `save_strategy_and_exit` - saves strategy to DB, deletes own PM2 process, exits cleanly
- **Files**: `agent/mcp_server.py` (save_strategy_and_exit tool at line 987), `agent/run_agent.py` (exit detection at line 355)
- **Behavior**: Agent exits after strategy definition, no user confirmation needed, prevents PM2 auto-restart loop

**Frontend Activation Routing** (Frontend):
- **Fix**: Activate button routes agent configs to `/api/v2/agent/{id}/start?mode=autonomous` (not `/api/v2/bot/`)
- **Fix**: Stop button routes to `/api/v2/agent/{id}/stop`
- **Fix**: `config_type` check corrected (was `selectedBot.config_data.config_type`, now `selectedBot.config_type` column)
- **Files**: `frontend/app/forge/page.tsx` (startBot/stopBot at lines 582-662)
- **Status**: Activate/Deactivate buttons functional for agentic configs

**System Prompt Fixes** (Backend):
- **Fix**: F-string syntax error (escaped curly braces in JSON examples: `{{` and `}}`)
- **Enhancement**: Explicit ggshot category rules - `trading_signals` NOT `technical_analysis` with ✅/❌ examples
- **Files**: `agent/run_agent.py` (system prompt at line 186-197)

**Autonomous Mode Validation** (Production):
- **Test**: Agent running live for 13+ minutes (config: bb2560fd-b053-464f-8a58-8e254e4d36fa)
- **Behavior**: 5-min monitoring cycles, disciplined no-entry decisions (waits for ALL conditions: RSI extreme + MACD reversal + Stochastic)
- **Analysis**: Creates data tables, tracks price changes ($106,604 → $106,164), professional market regime assessment
- **Tools**: Using query_market_data (RSI/Stochastic/MACD/funding), get_current_price (WebSocket), wait_for (strategic 5min intervals)
- **Status**: ✅ Agents can autonomously trade 24/7 with zero human intervention

---

## 2025-11-03 - Activity Timeline: Agent Activity Logging + Aster P&L Integration

**Activity Logging System** (Backend + Agent MCP):
- **Database**: Created `activities` table with 14 columns, 7 indexes, RLS policy for unified activity tracking across all bot types
- **Activity Logger**: `core/common/activity_logger.py` with `log_activity()` and `log_activity_safe()` helpers, priority-based grouping system (1=never group, 2=can group by type+time)
- **Agent MCP Integration**: Added `log_activity` tool + auto-logging to 6 existing tools (query_market_data, execute_trade, close_position, update_strategy, wait_for, record_trade_observation)
- **Activity Types**: trade_entry_long/short, trade_win/loss (P&L-aware), strategy_updated, market_query, agent_wait, observation_recorded, analysis/reasoning/plan

**Activity Timeline API** (Backend):
- **3 Endpoints**: `/api/v2/activities/{config_id}` (timeline data), `/balance-series` (cumulative P&L chart), `/metadata` (bot stats)
- **Aster Integration**: Queries `/fapi/v3/userTrades` endpoint, combines paper + Aster trades for unified P&L calculation starting at $0
- **Added Method**: `AsterDEXV3LiveTradingService.get_user_trades()` for trade history with realized P&L

**Activity Timeline Viewer** (Frontend):
- **Real API Integration**: Replaced mock data with live polling (10s interval) from activities API endpoints
- **UI Refinements**: Split trade_exit into trade_win/loss with 📈/📉 icons, consolidated agent thoughts (💭), intelligent live status indicator with pulsing dot
- **Layout**: Dynamic chart height, legend moved below chart, improved spacing
- **Fixes**: React hooks rules compliance, canvas null checks, timezone handling for Aster trades

**Status**: Agent activity logging operational, Activity Timeline working with Aster P&L, awaiting agent activities for full visualization

---

## 2025-11-03 - Agent Phase 4a Extended: Bot Creation Flow + Agentic State Machine

**Bot Creation Modal** (Frontend):
- **Type Selection at Creation**: Moved config type selector from Configure tab to new BotCreationModal component shown on "+ New" click
- **3 Bot Types**: Scheduled Trading (Free), Signal Validation (Pro), Agentic (Whitelist only)
- **Permission Gating**: Each type shows tier badge, locked types trigger UpgradeModal
- **createDefaultBot() Enhancement**: Now accepts botType parameter, creates minimal config for agentic (no selected_pair, no extraction/decision - agent defines via chat)
- **Integration**: Updated BotRail and MobileNav to open modal instead of direct creation
- **Files**: `components/modals/BotCreationModal.tsx` (new, 170 lines), `page.tsx` (createDefaultBot refactor), `BotRail.tsx` (modal integration)

**SaveConfigBar Refactor** (Frontend):
- **Static Type Display**: Removed 3-button selector, replaced with static badge showing current type (icon + label)
- **Cleaner ConfigureLayout**: Type is immutable after creation, only Save/Cancel/Reset buttons remain
- **Usage Pattern**: SaveConfigBar only rendered for scheduled_trading and signal_validation (via ConfigureLayout), NOT for agentic bots
- **Files**: `SaveConfigBar.tsx` (static display), `page.tsx` (removed SaveConfigBar from agentic rendering)

**Agentic Bot State Machine** (Frontend):
- **4 States Implementation**:
  - State 1: No strategy + inactive → Large centered "Start Strategy Discussion" button with empty state
  - State 2: Has strategy + inactive → Strategy card + "Refine Strategy" button (editable)
  - State 3: Has strategy + active → Strategy card + DISABLED button with lock icon (must deactivate first)
  - State 4: Agent running → AgentConfigurator chat interface (messages.length > 0)
- **handleStartStrategyDiscussion()**: Checks agent status, starts in strategy_definition mode, auto-sends existing strategy as context if editing
- **Context-Aware Editing**: When refining, waits 2s for agent init, then sends: "Here is my current strategy:\n\n{content}\n\nI'd like to refine it..."
- **Files**: `page.tsx` (state machine rendering + handler, ~80 lines)

**Autonomously Editable Setting** (Full Stack):
- **Frontend**: Checkbox in AgentConfigurator confirmation UI with label: "Allow agent to modify strategy autonomously (Advanced)"
- **Confirmation Flow**: Updated `handleConfirmStrategy(autonomouslyEditable)` to send JSON: `{confirm: true, autonomously_editable: boolean}`
- **Backend Parsing**: `run_agent.py` parses JSON confirmation, extracts autonomously_editable flag, passes to `_save_strategy()`
- **Database**: Saves user's choice to `configurations.config_data.agent_strategy.autonomously_editable` with version increment
- **Backward Compatibility**: Supports old "1"/"2" text format and new JSON format
- **Files**: `AgentConfigurator.tsx` (checkbox component), `page.tsx` (JSON send), `agent/run_agent.py` (JSON parsing + save)

**Architecture**:
- Bot type selection now part of creation flow, not configuration flow (prevents invalid type switching)
- Agentic bots have completely separate UI path (no ConfigTabs, no SaveConfigBar, just state machine)
- State machine uses `agentMessages.length === 0` to detect button vs chat view
- Agent auto-starts only when "Start/Refine Strategy" button clicked (removed auto-start on tab entry)

**Status**: Phase 4a fully complete - elegant bot creation flow, clear state machine, user choice for autonomy level

---

## 2025-11-03 - Agent Position Size Overrides + Dynamic AsterDEX Sizing

**Agent Autonomous Position Control** (Full Stack):
- **Trading Services**: Added override support to all three services (Aster, Paper, Symphony) for `position_size_override`, `position_size_usd_override`, `leverage_override`
- **Sizing Semantics**: `size_usd` = total position size (notional), NOT margin. Example: $1000 position @ 10x = $100 margin required
- **Backend API**: Created `/api/v2/agent/execute-trade` endpoint with service authentication and override parameter support
- **Agent Integration**: Updated agent API client (`agent/service_client.py`) and MCP tool (`agent/mcp_server.py`) to pass override params with clear documentation
- **Validation**: Comprehensive safety checks (balance validation, minimum quantities, leverage limits) across all services
- **Files**: `trading/live/aster_service_v3.py`, `trading/paper/supabase_service.py`, `trading/live/symphony_service.py`, `ggbot.py`, `agent/service_client.py`, `agent/mcp_server.py`

**AsterDEX Dynamic Position Sizing**:
- **Account Balance Query**: Implemented real-time USDT balance fetching for dynamic position sizing
- **Config-Based Sizing**: Respects bot config (ACCOUNT_PERCENTAGE, CONFIDENCE_BASED, FIXED_USD) with proper leverage calculations
- **Safety Caps**: Automatically reduces position if margin exceeds 95% of available balance
- **Minimum Enforcement**: Validates against AsterDEX minimums (0.001 BTC) with fallback to minimum if calculated size too small
- **Test Results**: Validated with $9.84 account, proper scaling confirmed (10% account = $0.98 margin @ 10x leverage)

**LivePriceService Format Fix**:
- **Symbol Format Agnostic**: `LivePriceService.get_current_price()` now accepts both `BTC-USDT` (platform) and `BTC/USDT` (CCXT) formats
- **Auto-Normalization**: Automatically converts dash separator to slash for Binance API compatibility
- **Cleaner Code**: Removed manual symbol conversion from Aster service and other call sites
- **Files**: `trading/paper/live_price_service.py`

**Status**: Agents can now control position sizing and leverage independently from bot config, enabling intelligent risk management based on market analysis

---

## 2025-11-02 - Agent Phase 4a: Strategy Definition UI Complete

**Frontend**:
- **Config Type Selector**: 3-button (Scheduled Trading | Signal Validation | Agentic), permission-gated, renamed autonomous_trading → scheduled_trading
- **AgentConfigurator**: Two-column layout (chat left, strategy right), Redis polling 2s, auto-scroll, typing indicator, empty states
- **Conversation Flow**: Send message → poll responses → detect show_confirm_button → confirm strategy → display in right column
- **State Management**: Page-level agent state (messages, input, waiting, showConfirm), handlers for send/confirm, auto-start in strategy_definition mode
- **Files**: app/forge/page.tsx (+150 lines agent state/handlers), components/configure/AgentConfigurator.tsx (new, 200 lines), SaveConfigBar.tsx (3-button UI), types/index.ts (ConfigType), lib/api.ts (type comments)

**Backend**:
- **Agent Lifecycle API**: 5 endpoints (start, stop, message, poll-response, status), PM2 process mgmt, Redis client, service auth
- **request_autonomous_mode**: Pushes JSON to Redis with show_confirm_button flag, frontend detects and shows confirm button vs text input
- **Files**: api/agent.py (+290 lines, 5 endpoints), agent/mcp_server.py (request_autonomous_mode update)

**Architecture**:
- Frontend conditionally renders AgentConfigurator when config_type='agentic', replaces ConfigTabs entirely
- Agent auto-starts on Configure tab entry, polls Redis responses:queue every 2s, pushes to messages:queue on send
- Clean separation: strategy definition (chat) vs autonomous mode (will use ActivityTimeline in Phase 4b)

**Status**: Phase 4a complete, ready for end-to-end testing with real agent

---

## 2025-11-02 - AsterDEX Live Trading Integration (Phase 1)

**Symbol Registry**:
- Cross-referenced 142 ggbot symbols with 140 Aster symbols → 33 compatible (23.2%)
- Updated `core/symbols/registry.py` with `aster_compatible` flags
- Added `is_aster_compatible()`, `to_aster()`, `from_aster()` methods to standardizer

**Live Trading**:
- Built `trading/live/aster_service_v3.py` with Web3 ECDSA authentication
- Executed full trade cycle on AsterDEX mainnet: OPEN 0.001 BTC @ $110,269.70 (Order: 7086939384), CLOSE @ $110,197.16 (Order: 7087174440)
- Symbol validation, leverage support (10x default), position management working

**Database**:
- Extended `live_trades` with `provider` field ('symphony', 'aster'), `stop_loss_order_id`, `take_profit_order_id`

**Documentation**:
- Created `DOCS/ASTER_SYMBOL_REGISTRY_UPDATE.md`, `DOCS/ASTER_INTEGRATION_SESSION_SUMMARY.md`
- Test scripts: `scripts/test_aster_live_trade.py`, `scripts/close_aster_position.py`

**Status**: Core integration operational, ready for Vibe Trading Competition ($50k prize)

---

## 2025-11-01 - Agent Phase 3 Complete: Live Autonomous Trading

- **Live Testing**: Strategy creation → autonomous mode switch → disciplined market analysis with 90min wait cycles
- **System Prompts**: Strategy-neutral framework, experience-based branching, data-grounded onboarding (32 data points, 7 timeframes)
- **Bug Fixes**: .env port (8002→8000), record_trade_observation JSON parsing (freeform text support)
- **Files**: agent/run_agent.py, agent/mcp_server.py, .env
- **Status**: Phase 3 complete, all 11 tools operational, agent running in production

---

## 2025-11-01 - Agent Config Integration (Complete)

**Backend**:
- **Models**: AgentStrategy model, BotConfig + BotConfigV2 support config_type='agent', conditional validation
- **Config Fields**: agent_strategy (content, autonomously_editable, version, performance_log), extraction/decision now Optional
- **Data Source Fix**: signals_group_chats → trading_signals (4 refs in listener_service.py)
- **Agent Config Repair**: Fixed d13d5536-2498-4f27-b2bc-e4f98958e1d8 (version, timestamps, BTC/USDT format, missing fields)
- **Files**: core/config/models.py, core/services/config_service.py, signals/listener_service.py

**Frontend**:
- **Type Definitions**: Made extraction/decision/llm_config optional in ConfigData, added agent_strategy field, added ConfigType union
- **Page Guards**: Added null checks and fallback guards in forge/page.tsx for safe editing of agent configs
- **Bot Rail**: Added "Agent" label for config_type='agent'
- **Config Components**: Added optional chaining guards in MarketDataSelector, SignalsConfiguration, StrategyEditor
- **Files**: frontend/types/index.ts, frontend/lib/api.ts, frontend/app/forge/page.tsx, frontend/app/forge/components/

**Status**: Full stack integration complete, agent configs working in production (tested with d13d5536-2498-4f27-b2bc-e4f98958e1d8)

## 2025-11-01 - Maintenance Mode Infrastructure Complete

- **Maintenance Mode**: Production-tested whitelist system, 59 bots deactivated, 24 positions closed ($186.88 P&L)
- **Scripts**: maintenance_deactivate_all_bots.py, maintenance_close_all_positions.py (production-ready with UUID casting, Decimal handling)
- **Frontend**: layout.tsx whitelist check, NEXT_PUBLIC_MAINTENANCE_MODE + NEXT_PUBLIC_WHITELIST_USER_ID
- **Bug Fixes**: SQL column names (config_id, trade_id, size_usd, etc.), close_reason constraint ('manual'), async LivePriceService
- **Files**: scripts/maintenance_*.py, frontend/app/forge/layout.tsx, DOCS/completed/MAINTENANCE_MODE.md

## 2025-11-01 - Documentation Cleanup
- **ggShot Parser Migration**: Moved `ggshot/ggshot_parser.py` → `signals/ggshot_parser.py`, updated imports (listener_service.py, ggbot.py, scripts)
- **Archive ggshot/**: Moved entire legacy directory to `archive/ggshot/`
- **API Docs**: Added 19 missing endpoints to ACTIVE.md (config CRUD, user mgmt, bot metrics, Stripe)
- **Hummingbot Cleanup**: Updated all docs reflecting Oct 2025 migration complete (README diagram, TODO tasks, code docstrings)
- **Timing Fix**: Corrected 7-second → 3-second position monitoring across docs

## 2025-01-30 - Activity Timeline Viewer (Competition Demo)
- **Canvas Timeline**: `/view/[config_id]` - 850-line Canvas component, 60fps, 6.17kB bundle
- **Features**: Drag pan, zoom (1h/4h/1d/1w/All), activity grouping, 3-rail stacking, pulsing "now" indicator
- **Mock Data**: 3-day history, 260 activities, currently demo-only (API integration pending)
- **Files**: `ActivityTimelineViewer.tsx`, `app/view/[config_id]/page.tsx`
- **Bug Fix**: Added missing `config_type`/`telegram_integration` fields to default bot creation (forge/page.tsx)

## 2025-10-30 (Evening) - Agent Tool #11 + Symbol Fix
- **Tool**: `get_current_price` - Sub-ms WebSocket lookup with REST fallback
- **Symbol Normalization**: Added Universal Symbol Standardizer to orchestrator, fixes BTCUSDT→BTC/USDT mismatch
- **Files**: api/agent.py, agent/service_client.py, agent/mcp_server.py, market_intelligence/orchestrator.py

## 2025-10-30 - Agent Phase 3 Complete
- **Auth Deadlock**: Fixed FastAPI event loop blocking, replaced `Depends()` with sync `validate_agent_service_auth()`
- **Tools Fixed**: get_positions (removed extra user_id), close_position (removed config_id), query_trade_observations (exit_price→current_price)
- **Tool Sandboxing**: Added `disallowed_tools` - blocks all Claude Code built-ins, restricts to 10 trading tools
- **Status**: 11 tools operational, agent ready for autonomous trading
- **Files**: api/agent.py (8 endpoints), agent/run_agent.py, agent/mcp_server.py

## 2025-10-29 (Session 2) - Agent Auth & Testing
- **Service Auth**: Added agent-runner to service whitelist (600 req/min)
- **Tool Testing**: query_market_data working, others timeout due to deadlock
- **Bug Fixes**: Dict param parsing, get_configuration() kwargs, JSON serialization for numpy/pandas
- **Chat CLI**: Rewrote with concurrent tasks + aioconsole for real-time display
- **Docs**: Created AGENT.md, updated TODO.md with Phase 3 blocker details

## 2025-10-29 (Session 1) - Agent Simplified Architecture
- **Pivot**: Removed dual-task complexity, separate processes for strategy_definition vs autonomous modes
- **Strategy Mode**: Clean query/response via Redis, `request_autonomous_mode` tool for switch
- **Autonomous Mode**: Pure `receive_messages()` loop, no user interaction
- **Testing**: Strategy definition verified end-to-end with chat.py CLI
- **Files**: agent/run_agent.py (rewrite), agent/mcp_server.py (strategy storage)

## 2025-10-28 - Agent Phase 3 Complete Infrastructure
- **TradingAgent**: ClaudeSDKClient streaming, mode/strategy context injection, 32 data points in system prompt
- **Redis Queues**: `agent:{config_id}:messages`, `:responses`
- **MCP Tools**: 10 tools (added request_autonomous_mode, updated query_market_data for 7 categories)
- **CLI**: chat.py (106 lines) - Redis-based testing interface with blocking blpop
- **Files**: agent/run_agent.py (370 lines), agent/mcp_server.py, agent/chat.py

## 2025-10-28 - Market Intelligence Phase 1 PRODUCTION
- **8 Grok Sources LIVE**: VIX, DXY, CPI, NFP, BTC TVL, whale activity, Twitter sentiment, crypto news
- **Cost**: $195/month platform ($0.76/user at 257 users, $0.20/user at 1000)
- **Bug Fixes**: Gateway adapter routing (agentic category), ggShot name (signals_group_chats→trading_signals), cache key KeyError, Redis protobuf serialization
- **Performance**: Parallel execution 160s→30s (5.3x speedup)
- **Orchestrator**: Config-driven routing, custom cache TTL per data point, data_points_override for agents
- **Decision Integration**: 6 formatting methods, prompt updates, real bot tested (~30s with comprehensive AI reasoning)
- **Files**: orchestrator.py (260 lines), catalog_mapping.py (180 lines), grok_agentic.py (500+ lines), seed_grok_intelligence.sql

## 2025-10-27 - Agent Phase 2: MCP Server & Trade Observations
- **DB**: Migrated agent_memory→trade_observations (post-trade reflection: 13 cols, 8 indexes, RLS)
- **API**: Added 2 endpoints (POST /agent/trade-observations, /query)
- **Service Client**: Updated with observation methods + HTTP retry
- **MCP Server**: 9 tools implemented (agent/mcp_server.py, 671 lines), module-level AgentContext
- **Tools**: query_market_data, execute_trade, get_positions, get_account_status, close_position, update_strategy, wait_for, record/query_trade_observations
- **Files**: database/migrations/agent_trade_observations.sql, agent/mcp_server.py, agent/service_client.py, api/agent.py

## 2025-10-27 - Intelligence Orchestrator + GrokAgenticAdapter
- **Orchestrator**: market_intelligence/orchestrator.py (260 lines) - config-driven routing
- **Catalog Mapping**: catalog_mapping.py (180 lines) - data_point→catalog translation
- **GrokAgenticAdapter**: ONE adapter handles 8+ sources via XAI agentic API (web search, X search, code execution)
- **Query Types**: VIX, DXY, CPI, NFP, Twitter sentiment, crypto news, BTC TVL, whale activity
- **Testing**: VIX live query successful - 5 tool calls, 18s, $0.0072, 7 citations
- **Integration**: ggbot.py calls orchestrator post-technicals, passes market_intelligence to decision engine
- **Decision Engine**: Added 6 formatting methods, updated opportunity_analysis.py prompt
- **Tests**: 16/16 unit tests passing (tests/test_orchestrator.py)
- **Files**: orchestrator.py, catalog_mapping.py, adapters/agentic/grok_agentic.py, catalog/data_types/agentic/grok_agentic.yaml

## 2025-10-26 - Market Intelligence 7 Categories + Funding Rates
- **Reorganization**: Renamed sources (crypto_derivatives→derivatives_leverage, signals_group_chats→trading_signals, etc.), consolidated from 8→7 categories
- **7 Categories**: Technical Analysis (21pts), Trading Signals (1pt), On-Chain (0pts), Derivatives & Leverage (2pts), Sentiment & Social (0pts), News (0pts), Macro Economics (0pts)
- **Total**: 24 data points (21 technical + 1 ggshot + 2 funding rates)
- **Funding Rates**: BinanceFundingAdapter with 7-level interpretation (extreme/high/slight long/short, neutral)
- **Testing**: BTC 0.0026% (neutral), ETH 0.0063% (neutral) - live queries working
- **Orchestrator Design**: DOCS/INTELLIGENCE_ORCHESTRATOR.md (500+ lines) - hybrid approach design spec
- **Files**: adapters/derivatives/binance_funding.py, catalog/data_types/derivatives/funding_rate.yaml, scripts/seed_funding_rates.py

## 2025-10-26 - ggShot Signals Universal Data Layer
- **Historical Backfill**: 878 signals last 60 days (130 symbols, 4 timeframes)
- **Real-Time Storage**: Listener stores every new signal alongside validation (backwards compatible)
- **Multi-Timeframe Query**: DISTINCT ON queries latest per timeframe
- **Confidence Scoring**: Age-based (1.0 <1hr, 0.9 <1day, 0.7 <3days, 0.5 older)
- **Autonomous Integration**: Extraction queries ggshot post-technicals (ggbot.py:794-830), decision formats for LLM, prompt updated
- **Permission Gating**: `'ggshot' in paid_data_points` check enforced
- **Dual Mode**: Push (validation) + Pull (autonomous)
- **Files**: catalog/data_types/signals/ggshot.yaml, adapters/signals/ggshot_adapter.py, scripts/backfill_ggshot_signals.py

## 2025-10-25 - Symphony Live Trading Bug Fixes
- **SQL Fix**: Cast trade_id::text, batch_id::text for UNION compatibility
- **ConfigService Fix**: Direct DB query in get_open_positions() (missing user_id param)
- **Position Size**: Changed sizeUSD→positionSize (actual Symphony API field)
- **Trade Age**: Use Symphony createdTimestamp vs DB created_at
- **SL/TP**: Map Symphony slPrice/tpPrice fields
- **Frontend**: PerformanceChart for live (balance "Track on Symphony", return "N/A", chart "Cumulative P&L"), trade history routing, type safety fixes
- **Features**: Default SL/TP for live trades, market price fetch pre-execution, graceful fallback
- **Docs**: trading/README.md updated (Symphony integration architecture, 250 lines)
- **Files**: trading/live/symphony_service.py, core/sse/dashboard_data.py, frontend/app/forge/components/monitor/

## 2025-10-24 - Symphony Dashboard Integration & SSE
- **SSE Enrichment**: Dashboard stream fetches Symphony data for live bots in parallel (~1-2s latency)
- **Unified Display**: PerformanceChart + PositionsTable show paper/live seamlessly
- **Close Position Routing**: Routes to Symphony API (live) or paper service (paper) based on source
- **Error Isolation**: Symphony failures don't break paper trading/SSE
- **Backend**: Extended SSE SQL (trading_mode, symphony_agent_id), UNION open_positions (paper+live), parallel API fetching
- **Endpoints**: GET /api/v2/account/live/{config_id}, /trades/live/{config_id}
- **Frontend**: Updated PositionsTable interface (position_id, source), enhanced close handler
- **Files**: core/sse/dashboard_data.py, trading/live/symphony_service.py, ggbot.py, PositionsTable.tsx

## 2025-10-24 - Hybrid Price Service & Symbol Coverage
- **Status Check Script**: scripts/status_check.py - comprehensive metrics, auto-update ACTIVE.md (--update), quiet mode (--quiet)
- **Hybrid Price**: 142 symbols supported - WebSocket-first (100 symbols <1ms) + REST fallback (42 symbols ~100ms, 5s cache)
- **Rate Limit Safety**: Built-in monitoring (1200 weight/min limit), circuit breaker at 80%/90%, exponential throttling
- **Capacity**: Safe for 10+ concurrent non-cached positions (~80 weight/min = 6.6% limit)
- **Symbol Registry**: Added websocket_cached field to all 142 symbols, helper functions is_websocket_cached(), get_websocket_cached_count()
- **Bot Validation**: Autonomous bots restricted to 100 WebSocket symbols (POST /api/v2/config validation)
- **ggShot Support**: All 142 symbols work for signal validation (low frequency = safe with REST)
- **Bug Fixes**: Python boolean syntax (true→True), removed orphaned _get_redis_client(), fixed 79 restart crash loop
- **Files**: core/symbols/registry.py, trading/paper/hybrid_price_service.py, trading/paper/live_price_service.py, ggbot.py, scripts/status_check.py

## 2025-10-22 - Live Trading Position Management Fix
- **Critical Bug**: Division by zero crash with live bots managing open positions
- **Root Cause**: _get_active_position() returned placeholder data (entry_price=0.0) vs fetching from Symphony API
- **Fixes**: Integrated Symphony API calls into decision/engine_v2.py:_get_active_position(), safety check in _format_position_data_for_llm()
- **Features**: Position matching by batch_id, orphan detection, comprehensive error handling
- **Market Data**: Fixed Redis key collision (ws:candles vs mi:candles), added asyncio.shield() for cancellation protection
- **Type Serialization**: Added _to_python_type() for recursive numpy conversion, enhanced serialize_numpy_types() for numpy.bool_/pandas NA/tuples
- **Files**: decision/engine_v2.py, extraction/v2/preprocessors/base.py, extraction/v2/universal_data_client.py, market_intelligence/adapters/

## 2025-10-22 - UX Polish & PerformanceChart
- **Status Messaging**: User-friendly pipeline messages ("Gathering market data..." vs technical), countdown context ("Waiting for 1h candle close in 3m 45s")
- **PerformanceChart**: Equity curve line chart with trade dots, click for details (green=wins, red=losses), metrics strip (Balance|Return|Trades|Win Rate), Recharts, last 50 trades
- **Security Fix**: ggShot access control - check paid_data_points.includes('ggshot') vs can_use_signal_validation, fixed toggle disable logic
- **Files**: PerformanceChart.tsx, permissions.tsx

## 2025-10-21 - Frontend Reliability & Error Recovery
- **API Client**: Exponential backoff retry (1s/2s/4s, 3 attempts)
- **SSE**: Auto-reconnection with backoff (5s→60s)
- **Error UI**: Visual feedback banners, page visibility retry
- **Symphony Auth**: Fixed 401 in Settings modal (proper session token)
- **Files**: frontend/lib/api.ts, components

## 2025-10-19 - Symphony Live Trading Integration
- **Database**: Extended user_profiles, configurations, new live_trades table (UNIQUE decision_id idempotency)
- **Vault**: Encrypted API key storage (store/get/delete methods)
- **Symphony Service**: trading/live/symphony_service.py - 3 methods (execute, close, query), idempotency check, symbol conversion, weight calculation, 3s settlement wait
- **Orchestrator Routing**: Smart paper/live routing based on trading_mode (locked per bot)
- **API**: 6 endpoints (setup, status, disconnect, positions, close, duplicate-as-live)
- **Frontend**: Settings modal (API key + smart account), "Deploy Live Version" flow, LIVE badge, premium check, disabled FIXED_USD sizing
- **Symbol Compatibility**: 100/141 symbols ready, to_symphony()/from_symphony()/is_symphony_compatible()
- **Files**: trading/live/symphony_service.py, ggbot.py, frontend/app/forge/components/

## 2025-10-21 - Hummingbot Deprecation & WebSocket Migration
- **Removed**: Hummingbot API (8888), PostgreSQL (5433), EMQX (1883+) - freed 200MB+ RAM
- **New**: LivePriceService using WebSocket candles from market-data-ws
- **Performance**: Sub-ms Redis access vs 800ms+ REST, ~1s updates vs 30s cache
- **Architecture**: Live candles at price:live:{symbol}, updated ~1s
- **Archived**: archive/hummingbot/ (market_data.py, data_client.py, HBOT_API.md)
- **Migration**: Paper trading, decision engine, position monitoring all use LivePriceService
- **Resilience**: Exponential backoff (1s→300s, 100 retries), 30s recv() timeout, proactive 15min reconnect, 60s silence detection, historical refetch on reconnect, PM2 logs to logs/market-data-ws-*.log, max_restarts 20→50
- **Files**: trading/paper/live_price_service.py, core/services/websocket_market_data_service.py

## 2025-10-19 - Universal Data Layer & WebSocket Cache
- **Universal Data**: MarketIntelligence gateway with DataCatalog, CacheManager, ResponseFormatter
- **Migration**: ExtractionEngine→UniversalDataClient via Adapter Pattern (2 lines changed)
- **Production**: 100% success, 3x-3000x faster (1-5ms cached vs 2-3s REST)
- **Sources**: RedisWebSocketAdapter (priority 1) + BinanceRestAdapter (fallback)
- **Testing**: 8 integration tests passing
- **Files**: market_intelligence/* (complete framework), extraction/v2/universal_data_client.py
- **WebSocket Cache**: 100 symbols × 7 timeframes = 700 datasets, sub-100ms retrieval, 200-candle windows, 700/1024 Binance streams (68%), 1.8s historical fetch, ~16MB memory
- **Subscription Fix**: Set subscription_expires_at=NULL for active subs (was trial end date), fixes premium permissions
- **Files**: core/services/websocket_market_data_service.py, ggbot.py (webhook handler)

## 2025-10-11 - Resend Email Integration
- **Service**: core/services/resend_service.py - Resend API integration
- **Contact Sync**: 189/261 users synced to Resend audience
- **Templates**: core/email_templates/ (welcome, trade alerts, signal alerts, generic)
- **Active**: Welcome emails on signup via user_service.py
- **Sync Script**: scripts/sync_resend_contacts.py (handles 2 req/sec limit)
- **Docs**: DOCS/RESEND.md

## 2025-10-04 - Trading System Fixes
- **Manual Close**: Added "Close Position" button, POST /api/v2/bot/{config_id}/positions/{trade_id}/close, fixed 401 auth (apiClient), included paper router in ggbot.py
- **Trade Settings Validation**: Frontend real-time errors/warnings, 6 fields (leverage 1-100 warn>20, SL 1-50%, TP 1-500%, position size 0.1-100% warn>50%, fixed amount max balance, max positions 1-50 warn>10)
- **Position Sizing**: FIXED - settings represent MARGIN (risk), multiplied by leverage for position size
- **P&L**: FIXED - removed double leverage multiplier (was 10x too high)
- **Volume Analysis**: Fixed not appearing in prompts
- **Liquidation**: Auto liquidation when losses exceed margin, liquidation_price on open, priority: Liquidation→SL→TP
- **Account Reset**: Default bot cleanup (92 deactivated, 83 users), preserved 22 custom, added "Reset Account" to dropdown, POST /api/v2/bot/{config_id}/reset-account, confirmation modal, metrics filtered by last_reset_at
- **Extraction Stability**: Fixed session race conditions in parallel extraction, removed context manager causing "Session is closed", added ensure_connected(), improved error handling
- **Subscription UI**: Pro/Free badges in UserProfile, upgrade modal with FIRST100 coupon ($29→$14.50), 50% strikethrough pricing
- **X Bot**: Separate PM2 service, daily 9AM UTC tweets, platform metrics (bots/users/trades/symbols/positions), Tweepy v4, ~90 reads/240 writes per month (within limits)
- **Files**: frontend/components/PositionsTable.tsx, trading/paper/supabase_service.py, extraction/v2/data_client.py, x_bot/

## 2025-10-03 - LLM & Extraction Performance
- **GPT-5 Responses API**: Full integration with reasoning effort controls, CoT passing, verbosity settings
- **PRO Settings**: 200s timeout, max tokens (OpenAI/Anthropic 16384, DeepSeek 8192, XAI 16384)
- **Universal System Prompts**: All 4 providers support 3 modes (standard, ggshot, trade_management)
- **Frontend**: Free users see "Default Model" + locked "Frontier Reasoning", Pro get 4 individual providers
- **Extraction**: Parallel timeframes via asyncio.gather (~60s saved), 10s timeout per exchange (reliability), ~30-60s total vs 2min sequential
- **Bug Fixes**: GPT-5 parsing (dict with 'output' + direct list), pandas dtype warnings (MFI volume), numpy.bool_ serialization, frontend LLM order

## 2025-10-01 - Stripe Monetization Complete
- **Pro Plan**: $29/month with 14-day trial, annual $279/year
- **Backend**: Checkout sessions, 4 webhook events, billing portal, user profile endpoint
- **Frontend**: Upgrade modal, permission gates, Pro/Free badges, upgrade buttons, billing portal access
- **Early Adopter**: 50% off 6 months (EARLY50 coupon)
- **Landing**: Accurate pricing (removed blur, updated features)
- **Testing**: Full Stripe test mode, ready for production swap
- **Trade Settings Validation**: 6 fields with real-time errors/warnings, red borders (blocking), yellow (non-blocking), ValidationMessage component

## 2025-09-29 - Logging Consolidation
- **Cleanup**: Deleted redundant core/common/logging_config.py
- **PM2 Integration**: All logs to /home/sev/ggbot/logs/ (separated by service/type)
- **Rotation**: pm2-logrotate (10MB, 5 files)
- **Verbosity**: Removed excessive prompt logging (saved to DB instead)

## 2025-09-27 - Disk Space Crisis & Position Monitoring
- **Root Cause**: Single Docker log 26GB (hummingbot-api)
- **Space Recovery**: 25GB+ freed (67%→41%)
- **Docker Logs**: 10MB max-size, 3 files (30MB cap)
- **PM2 Rotation**: pm2-logrotate 10MB with compression
- **Fail2ban**: Installed to prevent auth log bloat
- **Error Rate Limiting**: Connection errors limited
- **Monitoring**: Scripts check Docker/PM2/system logs
- **Position Monitoring Fix**: Batch SQL updates (UPDATE FROM VALUES), 100 updates = 1 query vs 100 HTTP (99% reduction), eliminated ConnectionTerminated errors

## 2025-09-23 - Critical Bug Fixes & Symbol Validation
- **XAI Provider**: Fixed signature mismatch causing signal validation failures
- **Telegram Publishing**: Removed confidence threshold blocking signals
- **Symbol Selection**: Moved from locked exchange to accessible trading settings
- **Symbol Validation**: 141 supported pairs with dropdown + search
- **Help Widget**: Floating question mark with Telegram community invite
- **Transparency**: All signals publish with APPROVED/REJECTED status

## 2025-09-19 - Multi-Exchange Fallback
- **Fallback**: Automatic failover across 5 exchanges (kucoin→binance→okx→gate_io→ascend_ex)
- **Safety**: Removed dangerous mock price fallback from decision engine
- **Tests**: test_fallback_methods.py, test_complete_multi_exchange.py (100% pass)
- **Files**: extraction/v2/data_client.py, trading/paper/market_data.py, decision/engine_v2.py

## Earlier Systems (Pre-Sept 2025)
- **Scheduler**: APScheduler integration, zero-drift candle execution, Redis idempotency, multi-timeframe (5m-1d), real-time rescheduling, startup reconciliation
- **Signal Validation**: signals/listener_service.py + publishing_service.py, ggShot integration, AI confidence eval, premium gating, service auth, Telegram publishing, V2 integration
- **Multi-Timeframe**: 7 timeframes (5m-1w), parallel extraction, rich LLM context, DB storage per timeframe
- **Paper Trading**: WebSocket prices (sub-ms Redis, ~1s freshness), $10k isolated accounts, 3-second monitoring (batch SQL), liquidation system, confidence-based sizing, real-time P&L
- **Core V2**: Scheduler + signal flow + multi-timeframe extraction operational, frontend SSE real-time, decision carousel, frontend animations polished, DB market_data fixed, Vercel Analytics, ggShot integrated, multi-user isolation, P&L colors, config save/load, paper accounts/metrics

---

**Documentation**: See README.md (architecture), ACTIVE.md (production status), TODO.md (roadmap)
