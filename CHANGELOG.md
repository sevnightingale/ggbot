# CHANGELOG - ggbots Platform

Complete history of features, fixes, and improvements to the ggbots autonomous trading platform.

**Note**: This file contains historical records only. For current status, see `ACTIVE.md`. For upcoming work, see `TODO.md`. For new Claude Code instances, start with `GO.md`.

---

## 2025-10-24 - Symphony Dashboard Integration & SSE Enrichment

**Live Trading Dashboard Integration** (Production):
- **SSE Stream Enrichment**: Dashboard stream now fetches Symphony data for live bots in parallel
- **Unified Account Metrics**: PerformanceChart displays both paper and live bot performance seamlessly
- **Position Display**: PositionsTable shows paper and live positions with unified interface
- **Close Position Routing**: Close button routes to Symphony API for live positions, paper service for paper positions
- **Performance**: Symphony API calls parallelized, ~1-2s additional latency for live bots
- **Error Isolation**: Symphony failures don't break paper trading or SSE stream
- **Architecture**: `_enrich_live_positions_and_accounts()` in `core/sse/dashboard_data.py`

**Backend Changes**:
- Extended SSE SQL query with `trading_mode` and `symphony_agent_id` fields
- Modified `open_positions` CTE to UNION paper_trades + live_trades (with source tagging)
- Added Symphony enrichment function with parallel API fetching
- Updated `get_unified_dashboard_data()` to call enrichment before portfolio analytics
- Created endpoints: `GET /api/v2/account/live/{config_id}`, `GET /api/v2/trades/live/{config_id}`
- Symphony service methods: `get_account_metrics()`, `get_trade_history()` with batch iteration

**Frontend Changes**:
- Updated `PositionsTable.tsx` interface with `position_id` and `source` fields
- Enhanced close handler to route based on `source: 'paper' | 'live'`
- Updated all position references to use unified `positionId` (trade_id or batch_id)
- PerformanceChart works automatically (no changes needed - unified account interface)

**Files Modified**: `core/sse/dashboard_data.py`, `trading/live/symphony_service.py`, `ggbot.py`, `frontend/app/forge/components/monitor/PositionsTable.tsx`

**Production Impact**:
- ✅ Live bots display real-time metrics from Symphony in dashboard
- ✅ Switch between paper and live bots seamlessly
- ✅ Close positions from UI (both modes)
- ✅ SSE stream stable with Symphony integration
- ✅ Graceful degradation on Symphony API errors

---

## 2025-10-24 - Hybrid Price Service & Symbol Coverage Fix

**Status Check Script for Internal Monitoring**:
- **New Tool**: `scripts/status_check.py` for comprehensive platform metrics
- **Metrics Collected**: User counts (256 total, 5 Pro), bot stats (376 total, 57 active), trading activity, open positions, top symbols, decision activity
- **Usage Modes**: Full report, auto-update ACTIVE.md (`--update`), quiet mode for monitoring (`--quiet`)
- **Comparison to X-Bot**: More comprehensive than daily tweets - includes win rates, account balances, decision activity, system health
- **Files**: `scripts/status_check.py`, `scripts/README_STATUS_CHECK.md`

**Hybrid Price Service - All 142 Symbols Supported** (CRITICAL):
- **Issue**: Symbol coverage mismatch - 142 symbols in registry vs 100 in WebSocket cache
- **Impact**: Users creating bots for non-cached symbols (e.g., SUI/USDT) experienced price lookup failures
- **Root Cause Analysis**: code-scout identified 42 symbols missing from WebSocket cache (ACHUSDT, ALPHAUSDT, AXSUSDT, etc.)
- **Solution**: Hybrid price architecture - WebSocket-first (100 symbols, <1ms) + REST fallback (42 symbols, ~100ms, 5s cache)
- **Architecture**: `HybridPriceService` with intelligent tiering for different use cases
- **Rate Limit Safety**: Built-in monitoring (1,200 weight/min Binance limit), circuit breaker at 80%/90%, exponential throttling
- **Performance**: 5-second REST cache reduces calls from 20/min to ~4/min per position (80% reduction)
- **Capacity**: Safe for 10+ concurrent non-cached positions (~80 weight/min = 6.6% of limit)

**Symbol Registry Enhancement**:
- **New Field**: `websocket_cached: True/False` added to all 142 symbols
- **Helper Functions**: `is_websocket_cached()`, `get_websocket_cached_count()`
- **Validation**: 100 symbols marked as cached (WebSocket real-time), 42 as non-cached (REST fallback)
- **Files**: `core/symbols/registry.py`

**Bot Creation Validation**:
- **Restriction**: Autonomous bots limited to 100 WebSocket-cached symbols only
- **Endpoints**: Validation added to `POST /api/v2/config` (create) and `PUT /api/v2/config/{id}` (update)
- **Error Message**: Clear user feedback - "Symbol {X} requires real-time price data. Choose from 100 available symbols."
- **Rationale**: Ensures fast position monitoring (3s cycles) without REST API latency/rate limits
- **Files**: `ggbot.py` (bot creation/update endpoints)

**ggShot Signal Validation - Full 142 Symbol Support**:
- **Use Case**: ggShot can send signals for any of 142 symbols
- **Implementation**: Signal validation + paper trading use hybrid service (REST fallback for non-cached)
- **Frequency**: Low-frequency (10-20 signals/hour) makes REST API safe despite rate limits
- **Result**: All ggShot signals process successfully regardless of symbol

**Bug Fixes**:
- **Python Boolean Syntax**: Fixed `true`/`false` (JavaScript) → `True`/`False` (Python) in registry
- **LivePriceService**: Removed orphaned `_get_redis_client()` reference in `get_multiple_prices()`
- **Service Stability**: Fixed crash loop (79 restarts) caused by syntax error

**Files Modified**:
- `core/symbols/registry.py` (added `websocket_cached` field + validation functions)
- `trading/paper/hybrid_price_service.py` (NEW - hybrid price fetching with caching + rate limit monitoring)
- `trading/paper/live_price_service.py` (updated to delegate to hybrid service)
- `ggbot.py` (added bot creation/update validation)
- `scripts/status_check.py` (NEW - platform metrics tool)

**Production Impact**:
- ✅ All 142 symbols now work for ggShot signal validation
- ✅ All 142 symbols work for paper trading with position monitoring
- ✅ Autonomous bots validated to use only 100 WebSocket symbols (prevents errors)
- ✅ Rate limit safety guaranteed with 5s caching + monitoring
- ✅ Service stable after fixing Python boolean syntax bug

---

## 2025-10-22 - Live Trading Position Management Fix & Market Data Reliability

**Critical Bug Fix - Division by Zero in Live Trading** (BLOCKING):
- **Issue**: Live trading bots crashed when managing open positions (division by zero error)
- **Root Cause**: `_get_active_position()` returned placeholder data with `entry_price = 0.0` instead of fetching real position data from Symphony API
- **Impact**: "Opus 92 (Live)" bot with 3 open positions unable to perform position management
- **Fix #1**: Integrated Symphony API calls into `decision/engine_v2.py:_get_active_position()` to fetch real position data (entry_price, current_price, unrealized_pnl, side)
- **Fix #2**: Added safety check in `_format_position_data_for_llm()` to prevent division by zero with graceful fallback
- **Features Added**: Position matching by batch_id, orphan detection (position in DB but not Symphony), comprehensive error handling
- **Result**: Live trading position management now functional with real Symphony data

**Market Data Pipeline Fixes**:
- **Redis Key Collision**: Fixed namespace collision between WebSocket service (`ws:candles:*`) and MarketIntelligence cache (`mi:candles:*`)
- **Missing Import**: Added `import asyncio` to `universal_data_client.py` for cancellation shielding
- **Error Messages**: Enhanced Binance REST adapter to show exception type and details instead of empty error strings
- **Cache Cleanup**: Deleted 416 corrupted Redis keys, rebuilt 700 clean WebSocket candle datasets
- **AsyncIO Cancellation**: Added `asyncio.shield()` to protect market data queries from orchestrator timeouts

**Type Serialization Fixes**:
- **numpy.bool_ Errors**: Added `_to_python_type()` helper to base preprocessor for recursive numpy type conversion
- **Pydantic Compatibility**: Enhanced `serialize_numpy_types()` to handle numpy.bool_, pandas NA, and tuples
- **Conversion Points**: Force float conversion in `_calculate_velocity()`, `_calculate_acceleration()`, `_calculate_position_rank()`
- **Result**: Signal validation endpoint no longer crashes on numpy type serialization

**Files Modified**: `decision/engine_v2.py`, `extraction/v2/preprocessors/base.py`, `extraction/v2/universal_data_client.py`, `market_intelligence/catalog/data_types/market_data/ohlcv.yaml`, `market_intelligence/adapters/market_data/redis_websocket.py`, `market_intelligence/adapters/market_data/binance_rest.py`, `ggbot.py`

---

## 2025-10-22 - UX Polish & Performance Chart

**User Experience Quick Wins**:
- **Status Messaging**: User-friendly pipeline messages ("Gathering market data..." vs "Extracting 12 indicators...")
- **Countdown Context**: "Waiting for 1h candle close in 3m 45s" vs "Next run: 3m 45s"
- **Pipeline Tooltips**: Explanatory tooltips on Extraction/Decision/Trading stages
- **Animation Delays**: 3s/7s/3s delays for smooth pipeline flow visibility

**PerformanceChart Component** (Replaces MetricsBar):
- **Equity Curve Visualization**: Line chart showing account balance over time with trade markers
- **Interactive Trade Dots**: Click dots for full trade details (green = wins, red = losses)
- **Metrics Strip**: Clean horizontal strip below chart (Balance | Return | Trades | Win Rate)
- **Recharts Integration**: Professional charting with last 50 trades, no SSE jitter
- **Files**: `PerformanceChart.tsx`, updates to `page.tsx`

**Security Fix - ggShot Access Control** (CRITICAL):
- **Issue**: Users without ggShot subscription could enable ggShot signals
- **Root Cause #1**: Permission check used `can_use_signal_validation` instead of `paid_data_points.includes('ggshot')`
- **Root Cause #2**: Toggle button disable logic allowed enabling if already enabled
- **Fix**: Updated `permissions.tsx` to check `paid_data_points` array directly
- **Result**: ggShot only accessible with manual database grant to `user_profiles.paid_data_points`

---

## 2025-10-21 - Frontend Reliability & Error Recovery

**Production Resilience for Symphony Integration**:
- **API Client Retry Logic**: Exponential backoff (1s, 2s, 4s) with 3 retry attempts on network failures
- **SSE Auto-Reconnection**: Automatic reconnection with exponential backoff (5s → 60s) for real-time updates
- **Error State UI**: Visual feedback banners for load failures and connection status
- **Page Visibility Retry**: Automatic retry when user returns to tab after errors
- **Symphony Auth Fix**: Fixed 401 Unauthorized in Settings modal (proper session token handling)
- **Result**: Frontend now resilient to network issues, no manual refresh required

---

## 2025-10-19 - Symphony Live Trading Integration

**Production-Ready Live Trading via Symphony.io**:

**Database Schema**:
- Extended `user_profiles`, `configurations`, and new `live_trades` table with idempotency protection
- Added `symphony_vault_id`, `symphony_smart_account`, `symphony_agent_id`, `trading_mode` columns
- Idempotency constraint: `UNIQUE(decision_id)` prevents duplicate trades
- Indexes on `config_id` and open positions

**Vault Integration**:
- Encrypted Symphony API key storage with credential management endpoints
- `store_symphony_credential()`, `get_symphony_credential()`, `delete_symphony_credential()` methods
- Automatic live bot disabling on credential removal

**Symphony Service**:
- Thin wrapper (`trading/live/symphony_service.py`) - 3 core methods (execute, close, query)
- Idempotency check before Symphony API calls (decision_id uniqueness)
- Symbol conversion using UniversalSymbolStandardizer
- Weight calculation using existing position sizing logic (account_percent & confidence_based)
- 3-second settlement wait after trade execution

**Orchestrator Routing**:
- Smart routing between paper/live based on `trading_mode` (locked per bot)
- Position management integration for live mode (close position routing)
- Query live_trades vs paper_trades based on trading_mode

**API Endpoints** (6 total):
- `POST /api/v2/symphony/setup` - Store credentials with format validation
- `GET /api/v2/symphony/status` - Check connection status
- `POST /api/v2/symphony/disconnect` - Remove credentials & disable live bots
- `GET /api/v2/positions/live/{config_id}` - Query Symphony positions
- `POST /api/v2/positions/live/{batch_id}/close` - Close live position with ownership check
- `POST /api/v2/config/duplicate-as-live` - Duplicate paper bot with validation

**Frontend UX**:
- Settings modal for Symphony connection (API key + smart account inputs)
- "Deploy Live Version" flow via DuplicateAsLiveModal
- LIVE badge distinction in bot cards
- Premium permission check with upgrade prompt
- Auto-suggest bot name: "{Original Name} (Live)"
- Disabled FIXED_USD position sizing for live bots (Symphony requires %)

**Symbol Compatibility**:
- 100 out of 141 symbols ready for live trading
- Extended symbol registry with Symphony format support
- `to_symphony()`, `from_symphony()`, `is_symphony_compatible()` methods

**Security**:
- API keys encrypted in Vault
- Ownership verification on all operations
- Service-level credential isolation

---

## 2025-10-21 - Hummingbot-API Deprecation & Production Resilience

**Replaced Hummingbot API with WebSocket live prices**:
- **Removed Infrastructure**: Hummingbot API (port 8888), PostgreSQL (5433), EMQX broker (1883+)
- **New Implementation**: LivePriceService using WebSocket live candle data from market-data-ws
- **Performance**: Sub-millisecond Redis access vs 800ms+ REST API calls
- **Freshness**: ~1 second updates vs 30 second cache
- **Resource Savings**: Freed 200MB+ RAM from 3 Docker containers
- **Architecture**: Live candles stored at `price:live:{symbol}` in Redis, updated every ~1s
- **Files Archived**: `archive/hummingbot/` (market_data.py, data_client.py, HBOT_API.md)
- **Migration**: Paper trading, decision engine, and position monitoring now use LivePriceService

**Production Resilience Improvements**:
- **Automatic Reconnection**: Exponential backoff (1s → 300s max) with up to 100 retry attempts
- **Connection Health Monitoring**: 30s recv() timeout prevents infinite blocking
- **Proactive Reconnection**: Automatic reconnect every 15 minutes (prevents Binance disconnects before they happen)
- **Faster Silence Detection**: 60s threshold (was 120s) - reconnects before live price TTL expires
- **Seamless Reconnection**: Historical candles refetched on every reconnect (1-2s, prevents indicator errors)
- **Connection Lifecycle Logging**: Detailed logging of connections, disconnects, and uptime
- **PM2 Logging Fix**: Logs now go to `logs/market-data-ws-*.log` (was `/dev/null`)
- **Increased Resilience**: max_restarts 20 → 50 for production reliability
- **Result**: Zero-downtime operation with proactive prevention, no price data errors, no indicator calculation failures

---

## 2025-10-19 - Universal Data Layer & WebSocket Market Data Cache

**Universal Data Layer (Production)**:
- **Phase 1 Foundation**: MarketIntelligence gateway with DataCatalog, CacheManager, ResponseFormatter
- **Phase 2 Migration**: ExtractionEngine migrated to UniversalDataClient via Adapter Pattern (2 lines changed)
- **Production Deployment**: Live in production, 100% success rate across all test scenarios
- **Performance**: 3x-3000x faster extractions (1-5ms cached vs 2-3s REST polling)
- **Data Sources**: RedisWebSocketAdapter (priority 1) + BinanceRestAdapter (automatic fallback)
- **Testing**: 8 integration tests passing (OHLCV flow, Preprocessor compatibility, ExtractionEngine validation)
- **Architecture**: Foundation for 150+ future data sources (sentiment, news, on-chain, fundamentals)
- **Files**: `market_intelligence/*` (complete framework), `extraction/v2/universal_data_client.py` (adapter)
- **Documentation**: Complete architecture in `DOCS/UNIVERSAL_DATA.md`

**WebSocket Market Data Cache (Production)**:
- **Coverage**: 100 symbols (ggbots + Symphony compatible) × 7 timeframes = 700 datasets
- **Symbols**: Expanded from 20 → 100 to cover all Symphony.io-compatible trading pairs
- **Performance**: Sub-100ms data retrieval for cached symbols (vs ~800ms REST fallback)
- **Architecture**: 200-candle rolling windows maintained in Redis via WebSocket push updates
- **Capacity**: 700/1024 Binance WebSocket streams (68% utilization, room for growth)
- **Historical Fetch**: 1.8 seconds for all 700 datasets on startup (100% success rate)
- **Memory Impact**: ~16MB total (Redis + service overhead)
- **Symphony Ready**: All 100 cached symbols work with Symphony.io live trading
- **Files**: `core/services/websocket_market_data_service.py`

**Subscription Permission Fix** (CRITICAL):
- **Issue**: `subscription_expires_at` set to trial end date instead of NULL for active subscriptions
- **Impact**: Users with expired trials couldn't access premium features despite active paid subscriptions
- **Root Cause**: Webhook handler setting expiration date for ongoing subscriptions (should be NULL)
- **Fix**: Updated `handle_checkout_completed` to set `subscription_expires_at = NULL` for active subs
- **Result**: Premium permissions now work correctly (can_use_premium_features = true for ggbase tier)
- **Files**: `ggbot.py` (webhook handler), database migration for existing users

---

## 2025-10-11 - Resend Email Integration (Phase 1)

**Automated Email System for User Communication**:
- **Service Module**: `core/services/resend_service.py` with full Resend API integration
- **Contact Management**: Automated sync of Supabase users to Resend audience (189/261 users synced)
- **Email Templates**: Professional responsive templates in `core/email_templates/` (welcome, trade alerts, signal alerts, generic notifications)
- **Active Features**: Welcome emails automatically sent on new user signup via `user_service.py`
- **User Sync**: Bulk sync script `scripts/sync_resend_contacts.py` for migrating existing users
- **Rate Limiting**: Handles Resend's 2 req/sec limit with graceful error handling
- **Future Integration**: Trade notification and signal alert templates ready, awaiting integration into trading/decision pipelines
- **Documentation**: Complete setup and usage guide in `DOCS/RESEND.md`

---

## 2025-10-04 - Trading System Fixes, Liquidation & X Bot

**Manual Position Management**:
- Added "Close Position" button to active trades in PositionsTable
- Implemented API endpoint: `POST /api/v2/bot/{config_id}/positions/{trade_id}/close`
- Updated paper trading service to handle manual position closure
- Tested manual close functionality with real-time SSE updates
- Fixed 401 auth errors by using apiClient instead of direct fetch
- Included paper trading router in ggbot.py to expose endpoint

**Trading Settings Validation & Position Sizing**:
- Frontend validation with real-time error/warning feedback
- Leverage (1-100, warning >20x), Stop Loss (1-50%), Take Profit (1-500%)
- Position sizing (0.1-100%, warning >50%), Max positions (1-50, warning >10)
- Red borders for errors (blocking), yellow borders for warnings (non-blocking)
- **Position sizing FIXED**: Settings now represent MARGIN (risk), multiplied by leverage for position size
- **P&L calculation FIXED**: Removed double leverage multiplier (was showing 10x too high)
- Tested position sizing calculations match configuration

**Volume Analysis Fixes**:
- Debugged volume analysis broken in technical indicators
- Fixed volume data not appearing in decision prompts
- Tested volume-based signal validation
- Verified volume metrics in market analysis formatting

**Liquidation System**:
- Automatic position liquidation when losses exceed margin (realistic leverage behavior)
- Liquidation price calculated on trade open based on margin and leverage
- Priority order: Liquidation → Stop Loss → Take Profit (matches real exchanges)
- Database schema updated with liquidation_price column
- Monitoring system checks liquidation before SL/TP

**Self-Service Account Reset Feature**:
- Default bot cleanup (92 bots deactivated, 83 users affected)
- Verified 22 custom strategy bots remain active
- Added "Reset Account" option to bot 3-dot dropdown menu
- Implemented backend endpoint: `POST /api/v2/bot/{config_id}/reset-account`
- Reset logic: Close all positions, reset balance to $10k, clear stats, preserve bot config
- Added confirmation modal with clear warning messaging
- Tested reset functionality with active positions and historical trades
- **Metrics filtering by last_reset_at**: Win rate and stats only show post-reset trades

**Extraction Connection Stability**:
- Fixed session race conditions in parallel timeframe extraction
- Removed problematic context manager usage causing "Session is closed" errors
- Added ensure_connected() method for shared session across parallel tasks
- Improved error message handling for empty aiohttp exceptions
- Fixed dict error response handling in get_candles method

**Subscription Management UI**:
- Display current subscription tier and status (Pro/Free badges in UserProfile)
- Add subscription upgrade interface (UpgradeModal with Stripe Checkout)
- Add subscription management interface (Stripe Customer Portal)
- **Upgrade modal update**: Changed to FIRST100 coupon with strikethrough pricing ($29 → $14.50)
- 50% off promotion for first 100 customers clearly displayed

**X Bot Service**:
- **Separate PM2 Service**: Independent x-bot process with APScheduler (isolates social media from trading operations)
- **Platform Status Tweets**: Daily automated tweets at 9:00 AM UTC with real-time platform metrics (active bots, users, trades, symbols tracked, open positions)
- **Database Integration**: Queries configurations and paper_trades tables for live platform statistics
- **Free Tier Strategy**: ~90 reads/month + ~240 writes/month (well within 100 read/500 write limits)
- **Architecture**: Tweepy v4 wrapper with error handling, separate schedulers directory for extensibility
- **Files**: `x_bot/bot.py` (main service), `x_bot/utils/x_client.py` (API wrapper), `x_bot/schedulers/platform_status.py` (daily tweet logic)
- **Future Expansion**: Ready for trade announcements, weekly summaries, targeted account replies (documented in X_BOT.md)

---

## 2025-10-03 - LLM & Extraction Performance Upgrades

**LLM Provider Optimizations**:
- **GPT-5 Responses API Migration**: Full integration with reasoning effort controls, CoT passing, and verbosity settings
- **PRO Model Settings**: 200s timeout + max tokens (OpenAI/Anthropic: 16384, DeepSeek: 8192, XAI: 16384) for quality reasoning
- **Universal System Prompts**: All 4 providers support 3 modes (standard, ggshot, trade_management)
- **Frontend Redesign**: Free users see "Default Model" + locked "Frontier Reasoning Models"; Pro users get 4 individual providers

**Extraction Performance**:
- **Parallel Timeframes**: asyncio.gather for simultaneous extraction (~60s saved)
- **Balanced Timeout**: 10s per exchange (reliability under load vs 2s aggressive timeout)
- **Result**: ~30-60s extraction vs 2 min sequential processing

**Bug Fixes**:
- GPT-5 response parsing (handles dict with 'output' + direct list formats)
- Pandas dtype warnings (MFI volume conversion)
- Numpy.bool_ serialization errors
- Frontend LLM selection spread order bug

---

## 2025-10-01 - Stripe Monetization Complete

**Pro Plan Implementation**:
- $29/month with 14-day free trial, annual option at $279/year
- Complete Backend Integration: Checkout sessions, webhook handlers (4 events), billing portal, user profile endpoint
- Frontend Upgrade Flow: Modal-based upgrade system with permission gate integration
- Subscription UI: Pro/Free badges in UserProfile, upgrade buttons, billing portal access
- Early Adopter Campaign: 50% off for 6 months (coupon: EARLY50)
- Landing Page Update: Accurate pricing display (removed blur, updated features)
- Testing Ready: Full Stripe test mode integration, ready for production key swap

**Trading Settings Validation**:
- Validation Hook: Real-time field validation with error/warning states
- 6 Validated Fields: Leverage (1-100, warning >20), Stop Loss (1-50%), Take Profit (1-500%), Position Size (0.1-100%, warning >50%), Fixed Amount (max account balance), Max Positions (1-50, warning >10)
- Visual Feedback: Red borders/text for errors, yellow for warnings, inline messages with icons
- UX Enhancement: Errors block save, warnings allow save with notification
- Component: ValidationMessage with AlertCircle/AlertTriangle icons

---

## 2025-09-29 - Logging System Consolidation

**Architecture Cleanup**:
- Consolidated dual logging systems into single standard configuration
- Legacy Removal: Deleted redundant `core/common/logging_config.py` (test files using legacy system ignored)
- PM2 Integration: All logs routed through PM2 to `/home/sev/ggbot/logs/` directory structure
- Log Structure: Separated by service (ggbot, signal-listener) and type (error, out)
- Rotation Management: pm2-logrotate handles compression and cleanup (10MB rotation, 5 files max)
- Verbosity Reduction: Removed excessive prompt logging from decision engine (saved to database instead)

---

## 2025-09-27 - Disk Space Crisis Resolution & Position Monitoring Fix

**Disk Space Crisis Resolution**:
- **Root Cause**: Single Docker container log file reached 26GB (hummingbot-api)
- **Space Recovery**: 25GB+ freed (disk usage: 67% → 41%)
- **Docker Log Rotation**: Configured 10MB max-size, 3 files (30MB total cap)
- **PM2 Log Rotation**: `pm2-logrotate` with 10MB rotation and compression
- **System Log Management**: Fail2ban installed to prevent auth log bloat
- **Error Rate Limiting**: Connection errors limited to prevent log spam
- **Monitoring**: Enhanced scripts check Docker, PM2, and system logs
- **hummingbot-API**: Restored with proper network, database, and auth configuration

**Signal Publishing Consolidation**:
- **Architecture Cleanup**: Removed unused `signal-publisher` PM2 service and empty queue processing
- **Publishing Integration**: Telegram publishing now handled directly by ggbot.py orchestrator
- **Code Consolidation**: Preserved working publishing functions while removing PM2 service scaffolding
- **Production Mode**: Fixed `DEVELOPMENT_MODE=false` for proper Supabase authentication
- **Ecosystem Update**: Removed signal-publisher from PM2 configuration (ecosystem.config.js)

**Position Monitoring Reliability Fix** (CRITICAL):
- **Critical Issue**: ConnectionTerminated errors preventing stop-loss/take-profit execution
- **Root Cause**: 100+ individual HTTP requests to Supabase every 3 seconds (1200+ requests/minute)
- **Elegant Solution**: Batch SQL updates using PostgreSQL `UPDATE FROM VALUES` pattern
- **Performance**: 100 position updates = 1 SQL query instead of 100 HTTP requests (99% reduction)
- **Trading Safety**: Position closures now execute before price updates (no more failed SL/TP)
- **Graceful Fallback**: Automatic fallback to individual updates if batch fails
- **Results**: ConnectionTerminated errors eliminated, monitoring running reliably

---

## 2025-09-23 - Critical Bug Fixes & Symbol Validation

**Critical Bug Fixes**:
- **XAI Provider Interface**: Fixed signature mismatch causing signal validation failures
- **Telegram Publishing Gate**: Removed confidence threshold blocking all low-confidence signals
- **Symbol Selection UX**: Moved from locked exchange section to accessible trading settings

**New Features**:
- **Symbol Validation System**: 141 supported trading pairs with dropdown + search
- **Help Widget**: Floating question mark with Telegram community invitation
- **Signal Publishing Transparency**: All signals publish with APPROVED/REJECTED status

**UX Improvements**:
- **Trading Pair Selection**: Professional dropdown replacing free-text input
- **Symbol Search**: Type-ahead search by base currency (BTC, ETH, SOL, etc.)
- **Community Access**: Always-visible help widget for user support

---

## 2025-09-19 - Multi-Exchange Fallback System

**Files**: `extraction/v2/data_client.py`, `trading/paper/market_data.py`, `decision/engine_v2.py`

**Enhancement**: Automatic failover across 5 exchanges (kucoin→binance→okx→gate_io→ascend_ex)

**Safety**: Removed dangerous mock price fallback from decision engine

**Tests**: `test_fallback_methods.py`, `test_complete_multi_exchange.py` (100% pass rate)

---

## Earlier Completed Systems

**Scheduler System**:
- Files: `core/scheduler/utils.py`, `ggbot.py` (APScheduler integration)
- Database: Added `state` field to `configurations` table
- Tests: `tests/test_scheduler.py`
- Zero-drift execution at candle boundaries
- Redis idempotency prevents duplicate trades across restarts
- Multi-timeframe support: 5m, 15m, 30m, 1h, 4h, 1d
- Real-time rescheduling when users change bot configurations
- Startup reconciliation automatically restores active bots

**Signal Validation System**:
- Files: `signals/listener_service.py`, `signals/publishing_service.py`, `decision/prompts/signal_validation.py`
- Publishing: Integrated into ggbot.py orchestrator (signal-publisher PM2 service discontinued)
- Generic framework supporting multiple signal sources (ggShot implemented)
- AI confidence evaluation of external signals using user strategies
- Premium gating through ggBase subscription tier
- Service-to-service authentication with dedicated `/api/v2/signal-validation` endpoint
- Telegram publishing to user-specified channels with APPROVED/REJECTED status
- Fixed confidence threshold - all signals publish (classification handled by orchestrator)
- Complete V2 integration using standard extraction → decision → trading flow

**Multi-Timeframe Architecture**:
- 7 timeframes: 5m, 15m, 30m, 1h, 4h, 1d, 1w extraction
- Parallel extraction: asyncio.gather for simultaneous timeframe fetching (~30-60s vs 2min sequential)
- Rich LLM context across all timeframes for decision making
- Database storage with separate rows per timeframe

**Paper Trading Engine**:
- Live WebSocket prices from Binance (sub-millisecond Redis access, ~1s freshness)
- $10,000 isolated accounts per configuration
- 3-second position monitoring ACTIVE (batch SQL updates for efficiency)
- Liquidation system - automatic position liquidation when losses exceed margin
- Confidence-based position sizing
- Real-time updates - position P&L calculated with live streaming prices

**Core V2 Pipeline**:
- Core V2 pipeline operational (scheduler, signal flow, multi-timeframe extraction)
- Frontend SSE real-time updates working
- Decision carousel display fixed and working
- Frontend slide animations polished (removed ugly pulse/flash effects)
- Database market_data column issue resolved
- Vercel Analytics integration added
- ggShot signal integration working
- Multi-user isolation and premium access
- Profit/loss color schemes implemented
- Configuration save/load cycle working
- Paper trading accounts and metrics display

---

**For detailed architecture and current production status, see README.md and ACTIVE.md**
