# CHANGELOG - ggbots Platform

Complete history of features, fixes, and improvements. For current status see ACTIVE.md, upcoming work see TODO.md.

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
