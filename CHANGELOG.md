# CHANGELOG - ggbots Platform

Complete history of features, fixes, and improvements. For current status see ACTIVE.md, upcoming work see TODO.md.

**WRITING STYLE**: Use telegraphic style for all entries. Omit articles (a, an, the), conjunctions where possible. Maintain specificity: include file references, error details, technical accuracy. Prioritize brevity while preserving all key information. Target 3-8 lines per entry for recent work, 1-3 lines for older entries. Example: "WebSocket cache 3 candles, bots need 100 → RSI failed" not "The WebSocket cache had 3 candles but the bots requested 100 which caused RSI to fail".

---

## 2025-12-19 - ggArena Bot Strategy Tuning

**7 arena bots prepared for 21-day competition**
- Created strategy files: `trading/strategies/{the_technician,the_compass,the_arbiter,the_contrarian,the_herald,the_sentinel,the_nomad}.md`
- Revised prompts with action bias: lowered confidence thresholds (0.55+ action vs 0.75+), removed paralysis language ("pass is default", "wait for perfect clarity")
- Updated data sources for Compass (added 8 technical indicators), Arbiter (5 domains), Contrarian (oscillators + sentiment + funding)
- Added descriptions and set `is_public_performance=TRUE` for all 7 bots
- Key insight from Technician analysis: 4/5 big losers were longs against bearish 1H regime → added regime gating to prompt
- Documentation fixes: Added decision→trade linkage docs to trading/README.md, ACTIVE.md, GO.md (paper_trades.decision_id = ENTRY only, query activities for exit tracing)
- Legacy position_sizing fields (method, fixed_amount_usd) still in 380 configs but unused; code clean, Pydantic ignores extras

## 2024-12-18 - Bot Profile Images + Arena Enhancements + Mobile Fix

**Complete Documentation**: See [DOCS/completed/2024-12-18_bot_avatars_arena_enhancements.md](DOCS/completed/2024-12-18_bot_avatars_arena_enhancements.md)

## 2025-12-17 - Bot Image Upload Fixes

**Critical Fixes** - Bot name preservation + image display in ActivationBar
- Bug: Image upload reset config_name to "Untitled Bot" → config_service.py flat structure path missing db_config_name assignment (line 324)
- Bug: SSE dashboard query omitted profile_image_url → added to SELECT (dashboard_data.py:72) and json_build_object (line 177)
- Bug: Frontend SSE listener didn't update allBots state → added setAllBots() merge in SSE handler (forge/page.tsx:432-443)
- Bug: BotImageUpload preview didn't sync with prop changes → added useEffect to sync preview with currentImageUrl (BotImageUpload.tsx:27-29)
- Result: Name preserved during image upload, image displays in ActivationBar after SSE update (2-3 sec), Arena page shows images correctly

## 2025-12-17 - Arena Public Competition Page

**Public Arena** - No-auth bot competition leaderboard at /arena (future arena.ggbots.ai subdomain)
- Backend: GET /api/v2/public/arena/performance - No auth required, returns showcase bots only (api/public.py)
- Database: Uses existing is_public_performance flag on configurations table (defaults false)
- Query: account_snapshots WHERE is_public_performance = true, formula = current_balance + unrealized_pnl
- Frontend: /app/arena/page.tsx - Recharts multi-line comparison, defaults 21-day competition period (504h)
- UI: Gold trophy header, ranked leaderboard cards (gold/silver/bronze badges), time selectors (7d, 14d, 21d, 30d)
- Colors: Brass, signal, jade, ruby, amethyst, amber for bot lines
- Setup: Admins manually flag showcase bots via is_public_performance column, users see public performance without login

## 2025-12-17 - TV Timeline Dual-Mode + Timeframe Aggregation

**Frontend** - Dual-mode equity chart with timeframe aggregation in TV Timeline component
- Activity Timeline mode: Irregular intervals, bot subjective awareness (activities.total_equity), shows markers/tooltips/details
- Performance Chart mode: Regular 5-min intervals, objective tracking (account_snapshots), clean line only
- Timeframe aggregation: 5M (base), 1H, 4H, 1D views (Performance mode only, uses LAST value per period)
- Backend: Added GET /api/v2/snapshots/{config_id}/performance-series endpoint (api/snapshots.py)
- Conditional fetching: Activity mode fetches activities for markers, Performance mode skips unnecessary calls
- UI: Brass toggle buttons, signal-blue timeframe selector, updates trigger data refetch via useEffect dependencies
- Users choose between contextual activity view or clean performance trending

## 2025-12-17 - Bot Limit Removal + Market Intelligence Hybrid Setup

**SSE Dashboard Fix** - core/sse/dashboard_data.py:205 - Added tuple length check, prevented "tuple index out of range" crash for 2 users

**Market Intelligence Hybrid** - Split sources between Grok (Twitter/on-chain) and Perplexity (macro) for optimal quality/cost
- Created market_intelligence/adapters/agentic/openrouter_adapter.py - Perplexity Sonar Pro with native web search
- Created perplexity_macro.yaml - VIX, DXY, CPI, NFP via Perplexity (~$0.01/query)
- Updated grok_agentic.yaml - Twitter sentiment, crypto news, BTC TVL, whale activity via Grok XAI ($0.05-0.15/query)
- Grok uses native X/Twitter access + code execution (superior quality), Perplexity handles macro (5-10× cheaper)

**Bot Limit Removed** - Usage-based pricing model, no artificial caps
- Dropped PostgreSQL trigger trigger_check_user_bot_limit + check_user_bot_limit() function (was blocking at 7 bots)
- frontend/app/forge/components/layout/BotRail.tsx - removed limit check, alert, counter display (was 10 bot limit)
- frontend/app/success/page.tsx - "10 active bots" → "Unlimited active bots"

## 2025-12-15 - Account Metrics Standardization (MAJOR REFACTOR)

**Major Refactor** - Centralized all account performance metric calculations, eliminated formula duplication across 6 locations

**New Centralized Calculator** - `core/domain/metrics_calculator.py`
- Created AccountMetricsCalculator with static methods for all metrics (single source of truth)
- Methods: calculate_total_equity(), calculate_available_balance(), calculate_performance_percent(), calculate_win_rate_percent(), calculate_realized_pnl()
- All formulas now reference this calculator, eliminating 6 duplicate implementations
- Future formula changes require single-file update (was 6 files)

**Domain Model Updates** - Standardized to use calculator
- `core/domain/account_snapshot.py` - Updated total_equity, return_pct properties to use calculator
- Fixed AccountSnapshot.return_pct formula bug (was incorrectly calculating initial_balance)
- `core/domain/models/account.py` - Updated Account.total_return, account_equity, AccountStatistics.win_rate
- `core/monitoring/adapters/paper_adapter.py` - Replaced win_rate, realized_pnl, available_balance formulas
- `core/common/activity_logger.py` - Added documentation comments referencing calculator as source of truth
- `api/admin.py` - Added formula reference comments in equity comparison endpoint

**API Enhancements** - Added missing calculated fields
- `ggbot.py:3362-3469` - Enhanced /api/v2/bot/{config_id}/account endpoint
- Added fields: total_equity, available_balance, margin_used, unrealized_pnl, realized_pnl, performance_percent
- All metrics calculated using AccountMetricsCalculator for consistency
- Fallback values for accounts without data (initial state)

**API Response Updates** - Improved naming clarity with backward compatibility
- `api/snapshots.py` - Updated /api/v2/snapshots/{config_id}/balance-series response
- New keys: equity_series, current_equity, initial_equity (was balance_series, current_balance, initial_balance)
- Legacy keys retained for backward compatibility (deprecated but functional)
- Updated docstring to reflect total_equity semantic (not just balance)

**Frontend Updates** - Support new API keys with fallback
- `frontend/components/tv-timeline.tsx` - Updated BalancePoint interface with total_equity field
- Chart data uses `point.total_equity ?? point.balance` (new key with legacy fallback)
- Updated comments from "balance" to "equity" terminology throughout

**Documentation** - Comprehensive metrics glossary added to README
- Added "Account Metrics Glossary" section to README.md (lines 314-383)
- Tables: Core Balance Metrics, P&L Metrics, Performance Metrics, Data Sources
- Important notes section explaining equity vs balance, margin accounting, win_rate representation
- Code references section with file locations for all metric calculations
- Documented formula fragmentation issue resolved by this refactor (was 6 locations, now 1)

**SQL Query Documentation** - Added formula reference comments
- `core/sse/dashboard_data.py` - Added comments noting account_balance column contains total_equity
- Noted future migration will rename column for clarity

**Impact** - Single source of truth for metrics, consistent calculations platform-wide, easier maintenance
- Formula changes: 6 files → 1 file (83% reduction in maintenance surface)
- Reduced formula inconsistency risk across backend, frontend, monitoring
- Enhanced API responses with comprehensive account metrics
- Backward-compatible frontend updates (supports both old and new API keys)
- Complete documentation of all metrics formulas and data sources

**Database Schema Migration** - Added total_equity column to activities table
- Added activities.total_equity column (NUMERIC(20, 8), nullable)
- Migrated all existing data from account_balance to total_equity (6,910 rows)
- Updated activity_logger.py INSERT statements to use total_equity column
- Updated api/snapshots.py, core/sse/dashboard_data.py to read from total_equity
- Legacy account_balance column retained temporarily (will be removed in future cleanup)

**No Breaking Changes** - All updates backward-compatible
- API response includes both legacy and new keys
- Frontend supports both field names with graceful fallback
- Database migration completed with data preservation

---

## 2025-12-14 - Admin Dashboard: Equity Calculation Fix

**Bug Fix** - Corrected total equity formula in bot comparison chart
- api/admin.py:1022-1023 - Removed margin_used from equity calculation (was double-counting)
- Changed: `current_balance + margin_used + unrealized_pnl` → `current_balance + unrealized_pnl`
- Aligns with platform-wide equity fix (core/domain/account_snapshot.py, activity_logger.py, forge/page.tsx)
- Impact: Chart equity values drop by margin_used amount for bots with open positions (now accurate)

---

## 2025-12-14 - Admin Dashboard: Bot Performance Comparison

**Feature** - Equity curve comparison chart for paper trading bots
- Backend: api/admin.py - Added GET /api/v2/admin/bots/equity-comparison endpoint
- Query params: user_id (optional), hours (default 72, max 720)
- Calculates total_equity = current_balance + unrealized_pnl from account_snapshots table
- Returns time-series data grouped by bot, sorted by current equity descending
- Frontend: /admin/bots-comparison page with Recharts line chart (6 color-coded lines)
- Profile images: 48px circular avatars with color-coded borders matching chart lines
- Time range selector (24h/3d/7d/30d), stats cards per bot (equity, P&L %, trades, win rate, open positions)
- Filters active paper bots only (excludes symphony/aster modes with incomplete equity data)
- Navigation link added to main admin dashboard page.tsx
- Fixed unused variable warning in TradeSettings.tsx (removed tradingMode, isSymphonyBot)

---

## 2025-12-10 - Position Sizing Simplification (BREAKING CHANGE)

**📄 Full Documentation:** `DOCS/completed/2025-12-10_position_sizing_simplification.md`

**Major Refactor** - Removed position sizing methods, simplified to confidence-based only
- Deleted PositionSizingMethod enum (FIXED_USD, ACCOUNT_PERCENTAGE, CONFIDENCE_BASED)
- Deleted position_sizing.method, .fixed_amount_usd, .account_percent fields
- Deleted risk_management.max_positions, .max_daily_loss_usd fields
- Renamed max_position_percent → max_margin_percent (semantic clarity: margin = collateral risked, not position size)

**New Simplified Structure**
```python
position_sizing: { max_margin_percent: 20.0 }  # Only 1 field
risk_management: { default_stop_loss_percent: 5.0, default_take_profit_percent: 10.0 }  # Only 2 fields
leverage: 5  # Moved to trading root level
```

**Calculation Semantics** - Clear margin vs position distinction
- Margin = confidence × max_margin_percent × balance (collateral risked)
- Position = margin × leverage (market exposure)
- Example: $10k account, 80% confidence, 20% max, 5x leverage → $1,600 margin → $8,000 position

**Backend Changes**
- core/config/models.py: Deleted enum, simplified PositionSizingConfig to 1 field, updated get_position_size()
- core/config/schemas.py: Same simplification
- trading/paper/supabase_service.py: Removed max_positions check (now natural limit via balance)
- trading/live/symphony_service.py: _calculate_weight() simplified (3 methods → 1)
- trading/live/aster_service_v3.py: Same simplification
- core/services/config_service.py + templates: Updated defaults

**Frontend Changes** - Massive UI simplification
- lib/api.ts: Updated TypeScript types, simplified createDefaultConfigData()
- TradeSettings.tsx: **MAJOR UX OVERHAUL** - Removed method selector, removed 3 inputs → 1 clean input for max_margin_percent
- useTradeValidation.ts: Removed unused rules (fixedAmountUsd, positionSizePercent, maxPositions)
- forge/page.tsx, test/page.tsx: Updated default configs

**New Defaults** (More realistic for crypto)
- leverage: 1x → 5x (moderate leverage, not scary)
- max_margin_percent: 20% (was max_position_percent: 10%)
- default_stop_loss_percent: 3% → 5% (breathing room)
- default_take_profit_percent: 6% → 10% (clean 2:1 R/R)

**Migration** - Old configs auto-upgrade via load_config_from_dict() fallback to defaults

**Impact** - Cleaner UI, clearer semantics, better defaults, no method confusion

---

## 2025-12-10 - Frontend/Backend Validation Mismatch Fix (Leverage Not Applied)

**Critical Bug** - User sets leverage 20x in frontend → trades execute with 1x (defaults)
- Root cause: Frontend allows max_position_percent up to 100, backend Pydantic validation limits to ≤25
- Flow: User saves max_position_percent=100 → backend validation fails → falls back to DEFAULT config (leverage=1, SL=3%, TP=6%)
- Impact: User's leverage, SL, TP settings silently ignored, trades execute with wrong parameters

**Validation Mismatch Details**
- core/config/models.py:102 - Backend: `max_position_percent: Field(10.0, ge=1.0, le=25.0)`
- frontend/app/forge/components/configure/TradeSettings.tsx:229 - Frontend: `<input max="100">`
- frontend/lib/useTradeValidation.ts - No validation rule for max_position_percent (missing)
- core/config/repository.py:73 - Fallback on validation error: `return self.get_default_config_for_type(config_type)`

**Fix Applied**
- core/config/models.py:102 - Increased backend limit from le=25.0 to le=100.0 (match frontend)
- frontend/lib/useTradeValidation.ts:86-91 - Added maxPositionPercent validation rule (max 100, warning >50%)
- frontend/app/forge/components/configure/TradeSettings.tsx - Applied validation styling, added ValidationMessage component
- Result: Config loads successfully, user's leverage/SL/TP settings actually apply

**Testing** - Config 1ddd2381-f806-4f05-bbef-a53ddfdfa8ed
- Before fix: leverage=1 (default), max_position=10% (default), SL=3%, TP=6% (defaults)
- After fix: leverage=20x (user setting), max_position=100% (user setting), SL=5%, TP=10% (user settings)

---

## 2025-12-10 - Stop Loss Inversion Bug Fix + Config-Driven Risk Management

**Critical Bug Fix** - Inverted stop loss causing instant trade closures and chart crashes
- Root cause: LLM prompt requested STOP_LOSS/TAKE_PROFIT outputs, parser somehow extracted Bollinger Band values (experimental code removed)
- Bug behavior: LONG BTC/USDT entry $92,192.56 → SL $92,403.13 (ABOVE entry, inverted!) → closed 0.39s later
- Chart crash: Rapid trade closure created activity data pattern causing "Value is null" error in TradingView library
- Pattern: Only 1 of 7 decisions had SL/TP values (SL=$92,403.13 = BB lower band, TP=$92,713.27 = BB middle band)

**Fix 1: Directional Validation** - Parser now validates SL/TP against entry price
- decision/engine_v2.py _parse_llm_response(): Added validation logic after line 1450
- LONG: SL must be below entry, TP above entry (otherwise rejected → config defaults apply)
- SHORT: SL must be above entry, TP below entry
- Logs warnings when invalid values detected for debugging
- Prevents Bollinger Band bug and similar issues

**Fix 2: Config-Driven Risk Management** - Removed LLM SL/TP fields from all prompts
- decision/prompts/opportunity_analysis.py: Removed STOP_LOSS/TAKE_PROFIT from output format
- decision/prompts/signal_validation.py: Same removal
- decision/prompts/position_management.py: Same removal
- LLM now outputs: ACTION + CONFIDENCE + REASONING only
- Config defaults (default_stop_loss_percent, default_take_profit_percent) always apply via trading/paper/supabase_service.py
- User settings (20x leverage, 1% SL, 2% TP) now actually used instead of silently bypassed
- Simpler, more predictable, no LLM can mess up risk levels

**Impact**: Chart renders correctly, trades execute with proper SL/TP, user config settings respected

---

## 2025-12-05 - Signal Listener Symbol Filtering

**Signal Listener Symbol Compatibility Filtering** - Symphony bots now only receive tradeable signals
- signals/listener_service.py: _get_signal_subscribers() filters by trading_mode + symbol compatibility
- Symphony bots: Only route 100 symphony-compatible symbols (BTC, ETH, SOL, etc.)
- Paper bots: Accept all 142 ggShot symbols (no filtering)
- AsterDEX bots: Only route aster-compatible symbols
- Prevents: $45/mo wasted LLM calls on incompatible symbols (KNC, MATIC, SUSHI, etc.)
- Implementation: Query trading_mode from DB, use UniversalSymbolStandardizer.is_symphony_compatible()
- 42 symbols filtered: ACH, ALPHA, AXS, BAKE, BAL, BAND, BEL, BIGTIME, BNT, CELR, CETUS, CHR, CHZ, COTI, CRV, CYBER, FLM, GTC, HIGH, HOOK, ICX, ID, IOST, KAVA, KNC, LEVER, LPT, LQTY, MATIC, MKR, NKN, OGN, ONE, ONT, RLC, RUNE, SFP, SKLUS, SUI, SUSHI, SXP, VANRY
- Result: Symphony bots no longer reject incompatible symbols, cleaner logs, cost savings
- Testing: test_signal_filtering.py validates filtering logic (6/6 tests passing)

## 2025-12-05 - Admin Dashboard + Resend Rate Limit Fix

**Admin Dashboard** - Internal platform management at /admin, restricted to admin user ID
- Backend: api/admin.py with 13 endpoints (stats, services, billing, users, bot control)
- Platform stats: users, bots, trades, P&L, health checks
- PM2/VM/Redis monitoring: services table with CPU/memory, disk usage, Redis status
- Billing overview: token usage, provider vs platform costs (70% markup), unreported amounts
- User management: search by email, view/edit subscription tiers, bot counts, trading activity
- User detail page: editable subscription_tier/status, bot list with start/stop controls, per-bot token costs, paper account summaries
- Bot control: start/stop any bot, reset paper accounts to $10k
- Config editing: JSONB preview (form-based editor planned but JSON sufficient for now)
- Security: JWT auth → admin user ID check → service role (layered defense)
- Frontend: 3 pages (/admin, /admin/users, /admin/users/[user_id]) with manual refresh
- Env vars: ADMIN_USER_ID (backend), NEXT_PUBLIC_ADMIN_USER_ID (frontend)
- Files: api/admin.py (~930 lines), frontend/app/admin/* (3 pages + layout)

**Resend Email Rate Limit Fix** - Welcome emails no longer fail on new signups
- Added 600ms delay between sync_user_to_resend() and send_welcome_email()
- Issue: 3 API calls in 1s (get_contact, add_contact, send_email) exceeded Resend's 2/second limit
- Fix spreads calls across >1s: sync (1-2 calls) → wait 600ms → send (1 call)
- File: core/services/user_service.py get_or_create_profile()

## 2025-12-05 - Strategy Advisor Character Creation Prompt + Reasoning Tier System

**Strategy Advisor Prompt Overhaul** - Character creation UX for onboarding, adaptive 4-scenario framework
- Opening protocol: Always asks 2 questions (experience level + strategy clarity)
- Scenario A (Inexperienced + No strategy): Character creation mode w/ personality questions (patient vs aggressive, trust crowd vs fade, react to news vs ignore noise), archetypes, bot naming encouraged
- Scenario B (Inexperienced + Vague idea): Educational translator, fleshes out rough concepts ("I heard RSI is good")
- Scenario C (Experienced + No strategy): Thesis exploration mode (what moves prices? technicals vs smart money vs sentiment?)
- Scenario D (Experienced + Has strategy): Get out of their way, minimal questions, fast translation
- Tone shift: "Bring your trading bot to life" vs "configure trading bots" (form-filling vibe removed)
- Technical accuracy: reasoning_tier economy/standard/premium (not thinking_mode), 7 model families (grok/deepseek/gemini/claude/gpt/kimi/qwen), decision.user_prompt for ALL bot types
- DO/DON'T guidelines: Adapt to user, conversational not form, support both philosophical + rules bots
- Success criteria: User feels understood, bot has executable strategy, bonus if named/personality resonates
- File: api/assistant.py get_system_prompt() rewritten (~320 lines), planning doc DOCS/new_assistant_prompt.md

## 2025-12-05 - Reasoning Tier System + Strategy Advisor Unification

**Reasoning Tier System** - Replaces boolean thinking_mode with 3-tier economy/standard/premium
- openrouter_provider.py: Added MODEL_TIER_MAP for 21 (model, tier) combinations
- Grok: grok-3-mini / grok-4-fast / grok-4
- DeepSeek: deepseek-chat / deepseek-v3.2 / deepseek-r1
- Gemini: gemini-2.0-flash / gemini-2.5-pro / gemini-3-pro-preview
- Claude: claude-haiku-4.5 / claude-sonnet-4.5 / claude-opus-4.5
- GPT: gpt-4.1-mini / gpt-5 / gpt-5-pro
- Kimi: kimi-k2 / kimi-k2-0905 / kimi-k2-thinking
- Qwen: qwen-turbo / qwen-plus / qwen3-max
- Tier-based max_tokens (2048/4096/8192) and reasoning effort (none/medium/high)
- Backward compatible: thinking_mode true→premium, false→standard

**Frontend Reasoning Selector** - 3-button UI replaces toggle
- StrategyEditor.tsx: Economy/Standard/Premium buttons instead of thinking toggle
- api.ts: Added reasoning_tier to ConfigData type
- Config stores both reasoning_tier (new) and thinking_mode (legacy compatibility)

**Testing**: scripts/test_provider_tier_models.py verified all 21 models via OpenRouter API

**Grok Agentic Adapter Query-Specific Timeouts** - Resolved DEADLINE_EXCEEDED errors, all 8 data points passing
- Implemented query-specific timeout system: NFP 300s, CPI/TVL/Whale/Twitter 180s, VIX/DXY/News 120s
- Previous: no timeout → gRPC default caused DEADLINE_EXCEEDED on complex queries (NFP, Twitter)
- NFP (Non-Farm Payroll) requires 5min for BLS.gov/Bloomberg/Reuters multi-source searches
- Twitter sentiment needs 3min for X search + sentiment analysis + code execution
- Test results: 8/8 passing, $0.08 per full suite, 38 tool calls total
- Query times: VIX/DXY/CPI 15-17s, NFP 25s, BTC TVL 33s, Whale 23s, Twitter 18s, News 24s
- Enhanced error handling shows query-specific timeout duration for debugging
- File: market_intelligence/adapters/agentic/grok_agentic.py query_timeouts map
- Note: market_intelligence uses xai-sdk directly, separate from decision engine OpenRouter calls

**Agent Configuration Now Uses Strategy Advisor** - Unified UX across all bot types
- Agent bots now use same ConfigureLayout + StrategyAdvisorPanel as scheduled/signal bots
- Added AgentStrategySection component (ConfigureLayout.tsx:35-125) - simplified UI for agents
- Conditional rendering: agent mode shows only strategy textarea, hides ConfigTabs
- Deleted AgentConfigurator.tsx (old PM2 + Redis polling approach, ~300 lines removed)
- Removed agent state from page.tsx: agentMessages, agentInputValue, isWaitingForAgent, handlers

**Strategy Field Consolidation** - Single source of truth for all bot strategies
- api/assistant.py updated: uses decision.user_prompt for ALL bot types
- agent_strategy deprecated in system prompts and tool descriptions
- Removed agent_strategy version increment logic

**strategy_definition Mode Deprecated** - Agent only runs in autonomous mode
- api/agent.py: returns 400 error if strategy_definition mode requested
- agent/run_agent.py: raises ValueError with helpful message pointing to Strategy Advisor API
- Argument parser updated: mode defaults to 'autonomous', warns on strategy_definition

**Documentation**: agent/README.md updated with new architecture, DOCS/todo/STRATEGY_UNIFICATION.md

---

## 2025-12-04 - Unified Config Saving + Symphony Win Rate Fix

**Unified Batched Config Save System** - Reduced 40+ API calls to 1
- Created useBatchedConfigSave hook (frontend/lib/hooks/useBatchedConfigSave.ts)
- 5s debounce accumulates all changes, single API call after idle
- Dirty field tracking prevents SSE from overwriting user edits mid-type
- Converted all config components to controlled: StrategyEditor (removed 4 useAutoSave hooks), TradeSettings (removed debounce timer), MarketDataSelector, SignalsConfiguration
- SSE handler updated: skips dirty fields, updates non-dirty fields only
- Documentation: DOCS/completed/UNIFIED_CONFIG_SAVING.md

**Symphony Win Rate Numeric Overflow Fix**
- Database column account_snapshots.win_rate is NUMERIC(5,4), max 9.9999
- Symphony service returned 0-100 percentage (50.0 for 50%), caused overflow
- Fixed in symphony_adapter.py:55-58: divide raw_win_rate by 100
- Now matches paper_adapter which already returns 0-1 format

---

## 2025-11-30 - Activity Timeline Data Visibility + ggShot Config Fix

**Market Query Activity Logging** - Exact LLM prompt data now stored for full traceability
- Added formatted_data to market_query activities (decision/engine_v2.py:1923-2010)
- Logs technical_analysis, volume_confirmation, ggshot_signals, market_intelligence strings sent to LLM
- Token count tracking per section with metadata.breakdown
- 3 logging calls in opportunity_analysis, signal_validation, position_management handlers

**Frontend Bottom Sheet Rendering** - Collapsible sections display formatted LLM prompts
- Complete rewrite of market_query bottom sheet (tv-timeline.tsx:1119-1215)
- Shows query mode, price at query, data age, timeframes/indicators/token counts
- Formatted data sections collapsible with <details>, monospace <pre> for readability
- Replaced OLD structure (categories, market_data.technicals) with NEW formatted_data structure

**llm_thought Field Name Fix** - Frontend expected 'thought' but backend logged 'reasoning'
- Changed details.reasoning → details.thought in decision/engine_v2.py:832
- Added backward compatibility in frontend (accepts both 'thought' and 'reasoning')
- Fixed broken llm_thought activity display in timeline bottom sheet

**ggShot Signal Config Enforcement** - Only fetch if enabled in bot config AND user has permission
- Added config check: extraction.selected_data_sources.trading_signals.data_points must contain 'ggshot'
- Previously only checked user permissions → ALL bots fetched ggShot if user had paid access
- Fixed in ggbot.py:845-888, now respects bot-level configuration
- Default scheduled bots no longer show ggShot unless explicitly configured

---

## 2025-11-23 - Balance Tracking System Overhaul

**account_pnl Population** - NULL in 100% activities, Redis cache missing total_pnl
- Added total_pnl to Redis (universal_account_monitor.py:173), activity logger now reads (activity_logger.py:51)
- Backfilled 1,114 historical activities with calculated cumulative P&L

**Race Condition Fix** - Activity logging before account update → stale balances
- Moved log_activity() after account update in close_position() (supabase_service.py:595-624)
- Future closes log correct post-update balance, no more $0.39 discrepancies

**Duplicate Logging Removed** - Position monitor logged ALL closes, paper service already logged
- Removed logging from paper_adapter._detect_and_log_closes() (paper_adapter.py:156-208)
- Single trade_exit per close, timeline charts clean (was 37 duplicates in test config)

**Frontend TypeScript Fix** - Obsolete 'live' mode causing build errors
- Removed 'live' checks from ActivationBar.tsx:68, RiskAcknowledgmentModal.tsx:10,25
- 'live' migrated to 'symphony' on 2025-11-15, stale references broke Vercel deploy

---

## 2025-11-23 - API Endpoint & Frontend Build Fixes

**GET /api/v2/config/{config_id} Missing Fields** - Frontend couldn't display Symphony/Aster bot details
- Query missing: state, trading_mode, symphony_agent_id, updated_at columns (ggbot.py:1647-1665)
- Frontend received incomplete data → configType undefined, trading mode badges missing
- Added 4 missing columns to SELECT, expanded response object with proper indices
- Impact: Symphony/Aster bots now display correctly in UI (was: no mode badge, broken settings)

**Frontend TypeScript Build Errors** - Type 'unknown' not assignable to ReactNode
- tv-timeline.tsx: Wrapped 7 unknown conditions in Boolean() (lines 1123,1139,1158,1164,1169,1174,1184)
- Direct rendering unknown values → build failure, wrapped indicators_count in String()
- StrategyEditor.tsx: Added eslint-disable for intentional mount-only useEffect (line 86)
- Build: ✅ 17 pages generated, no TS errors

**Documentation Updates** - Prevent future architectural misunderstandings
- CLAUDE.md: Added "Documentation Quick Reference by Topic" table (trading/README for mode issues)
- GO.md: Added explicit warning "DON'T assume paper_accounts exists for all trading modes"
- Lesson: Symphony/Aster use live_trades table only, paper mode uses paper_accounts (already in trading/README.md)

---

## 2025-11-23 - UI Spacing & Auto-Save Data Loss Fix

**Critical Auto-Save Bug** - Missing config_name/config_type params overwrote bot names with defaults
- Root cause: apiClient.updateConfig() calls lacked config_name, config_type → backend applied defaults
- Fixed all config forms: StrategyEditor.tsx:98,136, MarketDataSelector.tsx:136, SignalsConfiguration.tsx:98, TradeSettings.tsx:109
- Pattern: `await apiClient.updateConfig(configId, updates, configName, configType)` now mandatory

**Spacing Standardization** - Uniform 16px padding, 12px vertical gaps
- All components p-4 (16px): ActivationBar, TVTimeline, PositionsTable, Configure sections (previously mixed p-4/p-6)
- Vertical: TabNavigation my-3, Monitor space-y-3 = consistent 12px
- TVTimeline: min-h-screen only standalone (embedded no longer forces full-screen height)
- Main content: pb-32 → pb-8 (excessive 128px → 32px)

---

## 2025-11-20 - Legal Documentation Implementation

**Terms & Privacy Complete** - Full legal framework, signup integration, live trading risk modal
- Terms of Service: 21 sections adapted from Symphony (AI disclaimer, arbitration, Panama jurisdiction, US restriction)
- Privacy Policy: 13 sections (GDPR rights, data retention, third-party disclosure)
- Legal pages: /terms + /privacy w/ layout, navigation (frontend/app/(legal)/)
- Signup disclaimer: "By creating an account, you agree..." below auth form (signup/page.tsx)
- Footer component: Terms, Privacy, Telegram, Contact links (components/Footer.tsx)
- Risk modal: Pre-activation acknowledgment for live/aster bots, 5 risk categories, checkbox required (RiskAcknowledgmentModal.tsx, ActivationBar.tsx)

---

## 2025-11-20 - Trading Mode Refactor + AsterDEX Integration

**Trading Mode Refactor** - execution_mode removed, single source: `configurations.trading_mode` column
- Vault credentials for Symphony/Aster w/ encryption (vault_utils.py)
- Frontend: Settings modal, bot creation selector, mode badges (SettingsModal.tsx, BotCreationModal.tsx, BotRail.tsx)
- API endpoints: setup/status/disconnect for both modes (ggbot.py 2719-2858)
- Deleted DuplicateAsLiveModal.tsx (308 lines)

**AsterDEX Integration** - Core implementation complete, pending production hardening
- 3-field credential form w/ validation, bot creation mode selector, purple/red badges
- Trading service: 1,394-line aster_service_v3.py (Web3 signatures, market orders, SL/TP conditionals)
- Audit trail via live_trades table (provider='aster')

---

## 2025-11-20 - Market Maker Module (Experimental)

**Orderbook Market Making** - Avellaneda-Stoikov engine for Kuru DEX (not nad.fun AMM)
- Spread calculation, inventory skew, volatility adaptation (~900 lines)
- Simulation tested: +0.20% P&L, 3 fills, successful inventory management
- Exchange adapter pattern w/ Kuru template (needs API docs)
- Files: market_maker/engine.py, simulator.py, exchanges/kuru.py, DOCS/MM.md

---

## 2025-11-20 - AI Consciousness Timeline Architecture

**Activities-Only Chart** - Timeline shows bot's subjective awareness, Redis-cached equity, no snapshots
- Chart displays AI's discrete observation moments, not continuous time
- Redis equity cache: account monitor caches total equity every 5s (TTL 30s)
- Activity logger reads from Redis (tier 1), DB snapshots (tier 2), account table (tier 3)
- Total equity = current_balance + margin_used + unrealized_pnl (paper trading fix)
- Chart API queries activities table only (/api/v2/snapshots/{config_id}/balance-series)
- Files: core/domain/account_snapshot.py (total_equity @property), core/monitoring/universal_account_monitor.py (_cache_total_equity), core/common/activity_logger.py (Redis tier), api/snapshots.py (activities-only query)

**Marker Redesign** - Green/red circles w/ P&L text for exits, solid colors, vertical positioning
- Trade exits: green/red circles (size 1.5) w/ dynamic P&L text (+$5.23 / -$2.10), position by profit/loss
- Trade entries: green/red arrows (size 2), below/above line
- Observations: brass/blue/gray circles (size 1), on line (inBar)
- All solid colors, no transparency
- Files: frontend/components/tv-timeline.tsx (marker logic), frontend/components/bottom-sheet.tsx (centered on desktop)

---

## 2025-11-19 - Strategy Advisor Auto-Save Redesign

**Strategy Advisor Inline Chat Panel** - Replaced floating modal + SaveConfigBar w/ always-visible chat interface
- Removed SaveConfigBar (explicit save/cancel/reset buttons), removed floating modal overlay
- Strategy Advisor now 500px fixed-height panel at top of Configure tab, always visible
- Markdown rendering for AI responses (ReactMarkdown w/ custom styling for lists, headers, code)
- All borders unified to `border-[var(--border)]` (removed bright accent borders on chat + textarea)
- Removed "Default Strategy Example" box from StrategyEditor, cleaner single-purpose section
- Files: StrategyAdvisorPanel.tsx (new), SaveConfigBar.tsx (deleted), ConfigureLayout.tsx, StrategyEditor.tsx

**Auto-Save Implementation** - All config forms auto-save w/ 1s debounce, optimistic updates, rollback on error
- Removed hasUnsavedChanges, originalConfig, isEditingConfig state flags from page.tsx (-300 lines state logic)
- useAutoSave hook: debounced saves, optimistic UI, automatic rollback on failure, reports to SaveStatusContext
- SaveStatusContext: global status coordination (idle → saving → saved → error), auto-hide after 2s
- SaveStatusIndicator: animated global indicator (Loader2 spinner → Check → AlertCircle)
- Forms auto-save: StrategyEditor (prompt, frequency, LLM, thinking mode), MarketDataSelector (data sources), TradeSettings (all settings), SignalsConfiguration (ggShot toggle)
- Critical bug fix: Wrapped onSave callbacks in useCallback to prevent timer cancellation on re-render
- Files: useAutoSave.ts (new), SaveStatusContext.tsx (new), SaveStatusIndicator.tsx (new), StrategyEditor.tsx, MarketDataSelector.tsx, TradeSettings.tsx, SignalsConfiguration.tsx, page.tsx

**AI Config Updates Sync to Forms** - Strategy Advisor changes automatically reflected in form fields
- Added useEffect syncs for currentStrategy, analysisFrequency, llmModel, thinkingMode states
- When AI updates config via `/api/v2/assistant/chat` → handleConfigUpdate reloads → forms update
- Prevents stale form data when AI makes changes, user sees real-time updates

---

## 2025-11-16 - Universal AI Assistant Implementation

**Universal AI Assistant Deployed** - Claude Haiku function calling for bot configuration assistance
- Single endpoint `/api/v2/assistant/chat` w/ 3 tools (query_available_data, load_full_config, update_full_config)
- Works for ALL bot types: agent (strategy building), scheduled (config sections), signal_validation
- Bottom sheet modal (framer-motion) overlays configure pages, draggable/collapsible
- Bot-type aware system prompts, deep merge for partial config updates
- Cost: ~$0.016/session (~$16/mo @ 1000 users), conversation history in React state
- Auto-refreshes parent config when AI makes changes
- Files: api/assistant.py, frontend/components/UniversalAIAssistant.tsx, frontend/app/forge/page.tsx
- Planning: DOCS/todo/strategy_builder_api.md (new simplified approach), archived complex PM2/SDK version

**TypeScript Build Fixes** - Frontend build compilation passing, all type errors resolved
- Added Activity, ConversationMessage, AccountData interfaces for proper typing
- Removed unused executionStatus/statusMessage state (linter cleaned old status tracking)
- Type assertions for Record<string, unknown> fields in ActivationBar activity details
- Config auto-reload after AI updates via apiClient.getConfig() → setAllBots merge
- Build: 15 pages generated, 330 kB /forge bundle, zero TS/ESLint errors

**AI Assistant UX Redesign** - Ceremonial brutalist styling, proper layout, contextual placement
- Bottom sheet: 80vh → 50vh height, fixed flex layout ensures input always visible
- Colors: Full VIBE.md compliance (--bg-secondary, --accent, --border, --text-primary)
- User messages: brass accent bg, assistant messages: --bg-tertiary w/ border
- Button relocated: Header → Strategy section banner (contextual, not global)
- Banner: "Need help building your strategy? Launch AI Assistant" w/ brass CTA button
- Files: UniversalAIAssistant.tsx, StrategyEditor.tsx, ConfigureLayout.tsx, forge/page.tsx

**Configure Tab Reorganization** - Strategy-first layout, streamlined components
- Tab order: Strategy (1st), Market Data (2nd), Trade Settings (3rd), Signals (4th)
- Strategy section order: Strategy Prompt (w/ AI Assistant banner) → LLM Selection → Analysis Frequency
- Removed "Complete Prompt Template" collapsible section (simplified UX, -70 lines)
- Analysis Frequency: 4 options → 7 options (5m, 15m, 30m, 1h, 4h, 1d, 1w), compact 7-column grid
- Frequency buttons: Removed "Every" prefix, smaller padding (px-3 py-2), tighter spacing (gap-2)
- Configure page defaults to Strategy tab for scheduled/signal_validation bots
- Files: ConfigTabs.tsx, StrategyEditor.tsx
- Bundle size: 330 kB → 329 kB (-1 kB from removed sections)

**ActivationBar UX Overhaul** - Replaced pipeline ticker + backend messages w/ activity-based status + KPIs
- SSE now reads account_snapshots (UniversalAccountMonitor) instead of paper_accounts, removed live API enrichment
- ActivationBar Option A layout: Row 1 (bot name + activity status + controls), Row 2 (5 KPI cards)
- Removed PipelineTicker (Extraction→Decision→Trading circles), removed backend orchestration messages
- Activity-based status w/ 9 types (trade_entry, trade_exit, market_query, llm_thought, agent_wait, price_check, observation_recorded, strategy_updated, signal_received)
- Braille spinner always active, 3 rotating message variants/4s, live time updates/1s
- Status pulls real data from activity details: symbol, price, P/L, confidence, leverage, countdown for agent_wait
- TVTimeline KPI header hidden in embedded mode (shown in ActivationBar), visible standalone only
- Latest activity fetched every 30s from /api/v2/activities/{config_id}?limit=1
- Files: core/sse/dashboard_data.py, ActivationBar.tsx, page.tsx (ForgeApp), tv-timeline.tsx

---

## 2025-11-16 - Metered Billing Production Deployment

**Metered Billing System Verified LIVE** - Stripe Billing Meters operational w/ weekly invoicing
- Verified meter events sent successfully ($0.107734 aggregated current period)
- APScheduler midnight UTC runs confirmed (17 activities reported to date)
- Meter aggregation perfectly aligned w/ subscription billing period (Nov 13-20)
- Invoice preview shows $0 until period end (expected Stripe behavior for metered usage)
- First production invoice: Nov 20, 2025 @ 19:04:46 UTC
- Files: billing/stripe_meter_reporter.py, DOCS/completed/METERED_BILLING_IMPLEMENTATION.md

---

## 2025-11-16 - OpenRouter Migration + Symphony Fix

**OpenRouter Migration Complete** - Full migration from 'default' provider to OpenRouter unified API
- Frontend: Removed 'Default Model' button, all 7 models via OpenRouter (grok, claude, gemini, deepseek, gpt, kimi, qwen)
- Backend: Removed 'default' → XAI mapping in engine_v2.py, factory.py uses OpenRouter + Grok as default
- Database: Migrated 344 existing configs (provider='default' → 'openrouter', model='grok', thinking_mode=false)
- Thinking mode toggle always available for premium users (no longer gated by model != 'default')
- All new bot creation defaults to OpenRouter + Grok with thinking_mode flag

**Symphony SL/TP Fix** - Fixed AttributeError in default SL/TP calculation
- Issue: symphony_service.py accessed `config.trading.risk_management` as object property, but config.trading is dict
- Fix: Changed to dict access pattern `config.trading.get("risk_management", {})`
- Impact: Symphony bots can now apply default SL/TP without errors

Files: StrategyEditor.tsx, page.tsx, engine_v2.py, factory.py, symphony_service.py

---

## 2025-11-16 - Critical Production Fixes

**Issue 1: Insufficient Candle Data** - WebSocket cache 3 candles, bots need 100 → RSI failed → no trading
- Fix: gateway.py validates OHLCV count, redis_websocket.py raises AdapterError → auto-fallback Binance REST
- Impact: Trading restored (was completely blocked)

**Issue 2: SSL Connection Errors** - No pooling → hundreds SSL conn/min → Supabase rejecting → SSE broken
- Fix: db.py ThreadedConnectionPool (5-20 conn), ~95% load reduction
- Impact: Dashboard usable

Files: gateway.py, redis_websocket.py, db.py, monitoring adapters, positions.py, sse/dashboard_data.py, indicators.py

---

## 2025-11-15 - Snapshot-Based Timeline Chart

Snapshot-optimized chart w/ time-based X-axis, accurate P&L
- /api/v2/snapshots/{config_id}/balance-series merges 5min snapshots + activities
- Simplified tv-timeline.tsx (-50 lines)
- No Symphony/Aster API calls during render (was every 10s)
- Aster P&L: Use totalWalletBalance (income API only ~10 records, was $-0.01 vs $-29.03)
- Files: api/snapshots.py, tv-timeline.tsx, aster_adapter.py

---

## 2025-11-15 - Activities Logging Overhaul

Complete timeline all modes w/ auto position monitoring, snapshot integration, unified types
- llm_thought standalone, account_balance/pnl auto-populate
- trade_entry/exit logging paper+symphony, auto-close every 5s (paper: DB, symphony: API, aster: income)
- Type migration: analysis→llm_thought, unified system
- 1%→95% timeline visibility

---

## 2025-11-14 - Universal Account Monitoring

PM2 account-monitor, 5s checks, 5min snapshots across paper/symphony/aster
- Adapter pattern, account_snapshots table
- Snapshots on position changes or >0.1% balance movement

---

## 2025-11-14 - Critical Bug Fixes

- Meter reporter skip free users gracefully
- Orchestrator missing user_service (blocked execution)
- Timeline metadata iterate assets not dict keys

---

## 2025-11-13 - Metered Billing Production

End-to-end billing operational, $0.0072 tested, blocks past_due users
- APScheduler midnight UTC, all webhooks
- Files: stripe_meter_reporter.py

---

## 2025-11-13 - Metered Billing Infrastructure

Core billing w/ daily reporting, tier architecture
- LLM Pricing: Fixed schema, query llm_models
- Stripe Reporter: Aggregates platform_cost_usd
- Endpoints: /usage, /usage/breakdown
- Tiers: FREE (browse), USAGE_BASED (70% markup), PRO ($29/mo + agents)
- Validated: 2,251 tokens, $0.000675→$0.001148

---

## 2025-11-13 - Agent fixes, RLS, Aster

- RLS: activities, agent_sessions, llm_models secured
- Agent: Fixed crashes, trading mode detection
- Aster: /fapi/v3/account, proper sizing (availableBalance+totalPositionInitialMargin), userTrades→income (26 missing trades, $-5.89 vs $-43.52)
- Frontend: Number(x||0) null safety

---

## 2025-11-13 - Symphony Timeline

Symphony timeline support, unified paper/symphony/aster view
- get_trade_history() for P&L, get_account_metrics() for stats
- Removed priority column (use importance)

---

## 2025-11-12 - Activities & Token Tracking

Activity logging w/ per-call LLM cost tracking
- Removed priority column, added 10 token cols (provider, model, tokens, costs, stripe_reported)
- log_llm_activity() function, LLM Pricing Service (70% markup)
- Decision engine: _call_llm() returns (response, metadata), logs llm_thought activities
- Every LLM call tracked w/ costs

---

## 2025-11-11 - Confidence Sizing Verified

Tested confidence-based sizing paper/symphony/aster
- Formula: margin = confidence × max_position_percent × balance, position_size = margin × leverage
- All tests passed (10x leverage, 25% max)
- Agent defaults: confidence_based, 10x, 25% max
- Fixed: vault deletion, trading_mode symphony validation

---

## 2025-11-11 - OpenRouter UI & Theme

Model selection UI, theme system
- 7 models dynamic cards from /api/v2/llm-models, colored logos, pricing display, thinking toggle
- Tailwind dark mode [data-theme="dark"], 6 components theme-adaptive colors
- Brass #c1a87d works both themes

---

## 2025-11-10 - 5 Critical Fixes

1. Config Save 404: result indices shifted (result[2] created_at not result[1])
2. SSE Dashboard: missing config_type in CTE SELECT
3. OpenRouter: LLMProvider enum missing 'openrouter'
4. Timeline Race: Guard chartRef.current null
5. Aster Metrics Zero: Read trading_mode from column not JSONB

---

## 2025-11-10 - Config System Cleanup v2.2

373 bots migrated, field deduplication, 3 bugs fixed
- autonomous_trading→scheduled_trading
- Deleted trading.execution_mode JSONB (use trading_mode column)
- SQL migration 378 configs 10s, CHECK constraints, trading_mode NOT NULL
- ~150 lines dead code removed

---

## 2025-11-10 - OpenRouter Integration Phase 0

7 providers (Grok, DeepSeek, Kimi, Qwen, Gemini, GPT-5, Claude) w/ 14 variants (thinking mode)
- llm_models table, /api/v2/llm-models endpoint, OpenRouterProvider
- Not in production (awaiting migration)

---

## 2025-11-10 - Confidence Sizing (Incomplete)

execute_trade tool simplified: only confidence (0.0-1.0), system auto-calcs sizing
- NOT TESTED, needs review

---

## 2025-11-08 - Trading Mode Refactor

Eliminated "duplicate as live", first-class AsterDEX
- Users select mode at creation (Paper/Symphony/Aster)
- Vault integration (user_wallet, aster_wallet, private_key)
- SYMPHONY badge, ASTERDEX badge
- Deleted DuplicateAsLiveModal.tsx (308 lines), -250 lines dead code
- 5→3 steps creation

---

## 2025-11-08 - Agent Session Resumption

Agents survive crashes/restarts w/ full memory via Claude SDK session resumption
- agent_sessions table stores SDK session IDs
- On restart: load session_id → SDK restores history
- 80-90% context loss reduction
- Fixed: activities.trade_id UUID→TEXT for Aster integer orderIds

---

## 2025-11-08 - Timeline in Forge Monitor

Replaced DecisionFeed+PerformanceChart w/ full-width TVTimeline
- variant prop: embedded (600px) vs standalone (full viewport)
- Removed: DecisionFeed, PerformanceChart, TradeHistoryModal

---

## 2025-11-07 - Agent Strategy v4

Hardcoded 7 pairs→dynamic discovery via ggshot scan (last 2 days), auto-filtered Aster/Symphony/Paper
- query_market_data scan mode returns active symbols
- Fixes: Anthropic 500 retry, trade_observation 422, AsterDEX balance

---

## 2025-11-07 - TradingView Timeline

Professional TradingView Lightweight Charts w/ live status, markers
- Line chart P&L 700+ points
- Markers: trades (↑↓ arrows), queries (blue), thoughts (brass), waits (ivory)
- Bottom sheet preprocessed indicators
- Files: tv-timeline.tsx, bottom-sheet.tsx, aster_service_v3.py, agent files

---

## 2025-11-06 - Ceremonial Brutalism Rebrand

Platform rebrand to ceremonial brutalism
- Obsidian/ivory/brass palette, Bodoni Moda/Space Grotesk/IBM Plex Mono
- 56 emojis→Lucide icons
- 18 files modified

---

## 2025-11-04 - Aster Position Close

Added symbol column to live_trades for position-trade matching
- Agent can close Aster positions via symbol→batch_id map

---

## 2025-11-03 - Agent Phase 4c Autonomous

24/7 autonomous trading live
- save_strategy_and_exit tool, agent exits after definition
- Frontend routing fixed (activate→/api/v2/agent/{id}/start?mode=autonomous)
- Tested 13+ min live, 5min cycles

---

## 2025-11-03 - Activity Timeline Logging

activities table 14 cols, 7 indexes, RLS
- Activity logger w/ log_activity(), auto-logging 6 MCP tools
- 3 endpoints: /activities/{id}, /balance-series, /metadata
- Aster integration via /fapi/v3/userTrades

---

## 2025-11-03 - Agent Phase 4a Extended

Bot creation modal w/ type selection at creation
- 3 types: Scheduled (Free), Signal Validation (Pro), Agentic (Whitelist)
- 4-state machine: no strategy, has strategy inactive/active, agent running
- Autonomously editable checkbox

---

## 2025-11-03 - Agent Position Overrides

Override support position_size_override, leverage_override for Aster/Paper/Symphony
- /api/v2/agent/execute-trade endpoint
- Aster dynamic sizing: real-time balance, config-based calc, 95% margin cap

---

## 2025-11-02 - Agent Phase 4a Strategy UI

AgentConfigurator 2-column layout (chat left, strategy right)
- Redis polling 2s, show_confirm_button detection
- 5 endpoints: start, stop, message, poll-response, status

---

## 2025-11-02 - AsterDEX Integration Phase 1

142 ggbot vs 140 Aster→33 compatible (23.2%)
- aster_service_v3.py w/ Web3 ECDSA auth
- Full trade cycle tested: OPEN 0.001 BTC @$110,269.70, CLOSE @$110,197.16
- live_trades extended: provider field, SL/TP order IDs

---

## 2025-11-01 - Agent Phase 3 Complete

Live autonomous trading operational
- 90min wait cycles, strategy-neutral framework
- 11 tools operational

---

## 2025-11-01 - Agent Config Integration

AgentStrategy model, config_type='agent', conditional validation
- agent_strategy field (content, autonomously_editable, version)
- Frontend: extraction/decision/llm_config optional

---

## 2025-11-01 - Maintenance Mode

Whitelist system, 59 bots deactivated, 24 positions closed ($186.88 P&L)
- Scripts: maintenance_deactivate_all_bots.py, maintenance_close_all_positions.py
- Frontend: NEXT_PUBLIC_MAINTENANCE_MODE + WHITELIST_USER_ID

---

## 2025-11-01 - Documentation Cleanup

- ggshot/ggshot_parser.py→signals/ggshot_parser.py
- Archived legacy ggshot/ dir
- Added 19 missing API endpoints to ACTIVE.md

---

## 2025-10-30 - Activity Timeline Viewer

Canvas timeline /view/[config_id], 850 lines, 60fps, 6.17kB
- Drag pan, zoom (1h/4h/1d/1w/All), activity grouping

---

## 2025-10-30 (Eve) - Agent Tool #11

get_current_price - Sub-ms WebSocket w/ REST fallback
- Universal Symbol Standardizer fixes BTCUSDT→BTC/USDT

---

## 2025-10-30 - Agent Phase 3 Auth

Fixed FastAPI deadlock, sync validate_agent_service_auth()
- Tool sandboxing: disallowed_tools blocks Claude Code built-ins
- 11 tools operational

---

## 2025-10-29 - Agent Architecture Simplified

Separate processes strategy_definition vs autonomous
- Redis query/response, request_autonomous_mode tool
- chat.py CLI verified

---

## 2025-10-28 - Agent Infrastructure

TradingAgent ClaudeSDKClient, Redis queues, 10 MCP tools
- 32 data points system prompt

---

## 2025-10-28 - Market Intelligence LIVE

8 Grok sources LIVE: VIX, DXY, CPI, NFP, BTC TVL, whale, Twitter, news
- $195/mo ($0.76/user @257, $0.20 @1k)
- Parallel 160s→30s (5.3x)

---

## 2025-10-27 - Agent Phase 2 MCP

agent_memory→trade_observations (13 cols, 8 indexes)
- 9 tools, 2 API endpoints

---

## 2025-10-27 - Intelligence Orchestrator

orchestrator.py (260 lines), GrokAgenticAdapter handles 8+ sources via XAI
- VIX tested: 5 tool calls, 18s, $0.0072

---

## 2025-10-26 - 7 Categories + Funding

Reorganized 8→7 categories, 24 data points (21 technical + 1 ggshot + 2 funding)
- BinanceFundingAdapter 7-level interpretation

---

## 2025-10-26 - ggShot Universal Data

878 signals backfilled 60 days, real-time storage
- Multi-timeframe DISTINCT ON, confidence age-based
- Dual mode: push (validation) + pull (autonomous)

---

## 2025-10-25 - Symphony Fixes

SQL UNION type casts, position size sizeUSD→positionSize
- Default SL/TP, market price pre-execution

---

## 2025-10-24 - Symphony Dashboard SSE

SSE fetches Symphony data parallel ~1-2s
- UNION open_positions (paper+live)

---

## 2025-10-24 - Hybrid Price Service

142 symbols: WebSocket (100 <1ms) + REST fallback (42 ~100ms, 5s cache)
- Rate limit monitoring 1200 weight/min, circuit breaker 80%/90%
- Safe for 10+ concurrent non-cached positions

---

## 2025-10-22 - Live Position Management Fix

_get_active_position() fetches Symphony API vs placeholder (entry_price=0.0)
- Position matching batch_id, orphan detection

---

## 2025-10-22 - UX Polish

User-friendly pipeline messages, PerformanceChart equity curve
- ggShot access check paid_data_points.includes('ggshot')

---

## 2025-10-21 - Frontend Reliability

API exponential backoff (1s/2s/4s, 3 attempts), SSE auto-reconnect (5s→60s)

---

## 2025-10-21 - Hummingbot Deprecation

Removed Hummingbot API (8888), PostgreSQL (5433), EMQX - freed 200MB+ RAM
- LivePriceService WebSocket, sub-ms Redis vs 800ms+ REST

---

## 2025-10-19 - Symphony Integration

Vault encrypted storage, symphony_service.py (execute, close, query)
- 6 endpoints, frontend settings modal, LIVE badge
- 100/141 symbols compatible

---

## 2025-10-19 - Universal Data Layer

MarketIntelligence gateway w/ DataCatalog, CacheManager
- 100% success 3x-3000x faster (1-5ms cached vs 2-3s REST)
- WebSocket: 100 symbols × 7 timeframes = 700 datasets

---

## 2025-10-11 - Resend Email

189/261 users synced, welcome emails on signup

---

## 2025-10-04 - Trading Fixes

Manual close button, trade settings validation (6 fields)
- Position sizing FIXED (settings=MARGIN × leverage)
- P&L FIXED (removed double leverage)
- Liquidation auto when losses>margin
- Account reset: 92 deactivated, preserved 22 custom
- X bot: daily 9AM UTC tweets

---

## 2025-10-03 - LLM Performance

GPT-5 Responses API, PRO 200s timeout
- Extraction parallel asyncio.gather ~60s saved vs 2min

---

## 2025-10-01 - Stripe Monetization

$29/mo Pro 14-day trial, annual $279/yr
- 4 webhook events, billing portal
- EARLY50 coupon 50% off 6mo

---

## 2025-09-29 - Logging Consolidation

PM2 logs to /home/sev/ggbot/logs/, pm2-logrotate 10MB 5 files

---

## 2025-09-27 - Disk Space Crisis

Docker log 26GB, freed 25GB+ (67%→41%)
- Docker 10MB max-size 3 files, pm2-logrotate, fail2ban
- Position monitoring batch SQL: UPDATE FROM VALUES, 100 updates=1 query (99% reduction)

---

## 2025-09-23 - Symbol Validation

XAI provider signature fix, 141 symbols dropdown+search
- Telegram transparency: APPROVED/REJECTED status

---

## 2025-09-19 - Multi-Exchange Fallback

5 exchanges failover (kucoin→binance→okx→gate_io→ascend_ex)
- Removed mock price fallback

---

## Earlier (Pre-Sept 2025)

- Scheduler: APScheduler, zero-drift candles, Redis idempotency, 5m-1d multi-timeframe
- Signal Validation: ggShot AI confidence, premium gating, Telegram publishing
- Paper Trading: WebSocket prices (sub-ms), $10k isolated, 3s monitoring, liquidation
- Core V2: Frontend SSE real-time, decision carousel, Vercel Analytics

---

## 2025-11-15 - Symphony Mode Migration

Complete trading_mode='live'→'symphony'
- Backend: 3 paths updated (SSE, decision, dashboard)
- Frontend: BotRail badge, editing state merge
- Result: Symphony fully functional

**Documentation**: See README.md (architecture), ACTIVE.md (production status), TODO.md (roadmap)
