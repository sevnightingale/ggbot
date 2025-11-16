# CHANGELOG - ggbots Platform

Complete history of features, fixes, and improvements. For current status see ACTIVE.md, upcoming work see TODO.md.

**WRITING STYLE**: Use telegraphic style for all entries. Omit articles (a, an, the), conjunctions where possible. Maintain specificity: include file references, error details, technical accuracy. Prioritize brevity while preserving all key information. Target 3-8 lines per entry for recent work, 1-3 lines for older entries. Example: "WebSocket cache 3 candles, bots need 100 → RSI failed" not "The WebSocket cache had 3 candles but the bots requested 100 which caused RSI to fail".

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
