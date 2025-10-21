# 🚀 ACTIVE - ggbots System Status

**Last Updated**: 2025-10-20 (Hummingbot-API deprecated, replaced with WebSocket live prices)
**System Health**: 🟢 Production Live (225+ users, 100+ active bots)
**Project Status**: Live application with complete Stripe monetization and Universal Data Layer in production

---

## 🎯 Current Development Focus

**Production Status**: Live platform with 225+ active users managing 100+ autonomous trading bots

**Primary Objectives**:
- **Feature Refinement**: Trading system completeness (manual position management, SL/TP verification)
- **Monetization**: Stripe integration and paid tier implementation (ggbase subscription)
- **User Experience**: API key management, settings interface, status messaging improvements
- **System Polish**: Error handling, mobile responsiveness, comprehensive testing

**Architecture Status**: V2 implementation complete and operational in production

---

## 🌐 API Access Points

### Production Endpoints
| Service | URL | Status | Purpose |
|---------|-----|--------|---------|
| **V2 Orchestrator** | `https://ggbots-api.nightingale.business` | ✅ | Main backend API |
| **Frontend** | `https://ggbot-app.vercel.app` | ✅ | Next.js application |

### Core API Endpoints
**Bot Control & Scheduling**
- `POST /api/v2/bot/{config_id}/start` - Start autonomous bot with scheduling
- `POST /api/v2/bot/{config_id}/stop` - Stop bot and remove scheduler jobs
- `GET /api/v2/scheduler/status` - Active scheduled jobs per user
- `GET /api/v2/bot/{config_id}/status` - Real-time bot status
- `WS /ws/bot-status/{user_id}` - WebSocket for real-time updates

**Symbol Validation**
- `GET /api/v2/symbols/supported` - Get all 141 supported trading symbols
- `GET /api/v2/symbols/search/{query}` - Search symbols by base currency

**Signal Processing**
- `POST /api/v2/signal-validation/{config_id}` - Service-to-service signal validation endpoint
- `POST /api/v2/orchestrate/{config_id}` - General orchestration endpoint
- Signal listener service (PM2 background process with service authentication)

**Trading & Analytics**
- `GET /api/live-position-data` - Current positions with real-time P&L
- `POST /paper/execute` - Execute paper trades
- `GET /paper/positions/{config_id}` - Position tracking

---

## 📊 System Architecture

### Core Services (PM2)
| Service | Status | CPU | Memory | Purpose |
|---------|--------|-----|--------|---------|
| ggbot | 🟢 Online | 0% | ~205MB | V2 Orchestrator API server with integrated scheduler & telegram publishing |
| market-data-ws | 🟢 Online | 0% | ~140MB | Real-time WebSocket market data cache (100 symbols × 7 timeframes = 700 datasets) |
| signal-listener | 🟢 Online | 0% | ~62MB | External signal processing service (ggShot integration) |
| x-bot | 🟢 Online | 0% | ~41MB | X (Twitter) bot for @ggbots_ai - automated platform status tweets and engagement |
| error-alerts | 🟢 Online | 0% | ~20MB | Error monitoring and Telegram alert service |

### PM2 Modules
| Module | Status | Purpose |
|--------|--------|---------|
| pm2-logrotate | ✅ Installed | Automated log rotation and compression (10MB rotation, 5 files max) |

### Infrastructure Services
| Service | Status | Port | Purpose |
|---------|--------|------|---------|
| Supabase PostgreSQL | 🟢 Online | Remote | Main application database (managed) |
| Redis | 🟢 Online | 6379 | WebSocket cache, live prices, scheduler idempotency |

---

## ✅ Production-Ready Features

### **Autonomous Scheduler System** 
- **Zero-drift execution** at candle boundaries (e.g., 09:35:30 for 5-minute bots)
- **Redis idempotency** prevents duplicate trades across restarts
- **Multi-timeframe support**: 5m, 15m, 30m, 1h, 4h, 1d
- **Real-time rescheduling** when users change bot configurations
- **Startup reconciliation** automatically restores active bots

### **Signal Validation System**
- **Generic framework** supporting multiple signal sources (ggShot implemented)
- **AI confidence evaluation** of external signals using user strategies
- **Premium gating** through ggBase subscription tier
- **Service-to-service authentication** with dedicated `/api/v2/signal-validation` endpoint
- **Telegram publishing** to user-specified channels with APPROVED/REJECTED status (integrated into ggbot.py orchestrator)
- **Fixed confidence threshold** - all signals publish (classification handled by orchestrator)
- **Complete V2 integration** using standard extraction → decision → trading flow

### **Paper Trading Engine**
- **Live WebSocket prices** from Binance (sub-millisecond Redis access, ~1s freshness)
- **$10,000 isolated accounts** per configuration
- **✅ 3-second position monitoring** ACTIVE (batch SQL updates for efficiency)
- **Liquidation system** - automatic position liquidation when losses exceed margin
- **Confidence-based position sizing**
- **Real-time updates** - position P&L calculated with live streaming prices

---

## 🔌 Complete Port Reference

### Application Ports
| Port | Service | Protocol | Access | Purpose |
|------|---------|----------|--------|---------|
| **8000** | V2 Orchestrator (ggbot.py) | HTTP | Public | Complete V2 API server with E2E pipeline |
| **8080** | code-server | HTTP | Public | VSCode in browser (development environment) |

### Database Ports
| Port | Service | Access | Purpose |
|------|---------|--------|---------|
| **Remote** | Supabase PostgreSQL | HTTPS/SSL | Main application database (managed) |
| **6379** | Redis | Localhost | WebSocket cache, live prices, scheduler idempotency |

### System Ports
| Port | Service | Access | Purpose |
|------|---------|--------|---------|
| **22** | SSH | Public | Remote access |
| **80** | HTTP | Public | Web server |
| **443** | HTTPS | Public | Secure web server |

---

## 🔄 Background Tasks

- **Position Monitoring**: ✅ ACTIVE (3-second cycles monitoring 120+ configs with open positions)
- **Autonomous Trading**: ✅ ACTIVE (scheduled bot execution across multiple timeframes with APScheduler)
- **Signal Processing**: ✅ ACTIVE (ggShot signal validation and telegram publishing)
- **Log Rotation**: ✅ ACTIVE (pm2-logrotate with 10MB rotation, 5 file retention, compression)
- **Disk Space Monitoring**: ✅ ACTIVE (automated checks every 6 hours)
- **Process Cleanup**: Every 5min (terminated processes)
- **Cache Cleanup**: Every hour (old statuses/decisions)

---

## 🔧 Quick Commands

```bash
# Service status
pm2 list
pm2 monit

# Logs
pm2 logs ggbot

# Disk space monitoring (includes Docker logs)
/home/sev/ggbot/scripts/disk_monitor.sh

# Setup monitoring cron job (if needed)
/home/sev/ggbot/scripts/setup_monitoring.sh

# Docker log management
/home/sev/ggbot/scripts/fix_docker_logging.sh

# E2E Testing
python -m tests.test_full_e2e_integration

# Resources
htop
df -h
```

---

## 📁 Recent Implementations

### **Multi-Exchange Fallback** (Complete - 2025-09-19)
- **Files**: `extraction/v2/data_client.py`, `trading/paper/market_data.py`, `decision/engine_v2.py`
- **Enhancement**: Automatic failover across 5 exchanges (kucoin→binance→okx→gate_io→ascend_ex)
- **Safety**: Removed dangerous mock price fallback from decision engine
- **Tests**: `test_fallback_methods.py`, `test_complete_multi_exchange.py` (100% pass rate)

### **Scheduler System** (Complete)
- **Files**: `core/scheduler/utils.py`, `ggbot.py` (APScheduler integration)
- **Database**: Added `state` field to `configurations` table
- **Tests**: `tests/test_scheduler.py`

### **Signal Validation** (Complete)
- **Files**: `signals/listener_service.py`, `signals/publishing_service.py`, `decision/prompts/signal_validation.py`
- **Publishing**: Integrated into ggbot.py orchestrator (signal-publisher PM2 service discontinued)

### **Multi-Timeframe Architecture** (Complete)
- **7 timeframes**: 5m, 15m, 30m, 1h, 4h, 1d, 1w extraction
- **Parallel extraction**: asyncio.gather for simultaneous timeframe fetching (~30-60s vs 2min sequential)
- **Rich LLM context** across all timeframes for decision making
- **Database storage** with separate rows per timeframe

---

## 🎯 Current Focus

### 🟢 Production Status (Live Platform)
**User Base**: 225+ active users managing 100+ autonomous trading bots
**System Health**: All core systems operational with real-time monitoring
**Platform Focus**: Feature refinement, monetization implementation, and user experience polish

### 📈 Active Development Priorities

**Trading System Completeness**:
- Manual position management and close functionality
- Stop loss/take profit verification and automated execution
- Volume analysis fixes and trading parameter validation

**Monetization Implementation**:
- ✅ Stripe integration complete (checkout, webhooks, billing portal)
- ✅ Pro Plan subscription ($29/mo, 14-day free trial, 50% off early adopter coupon)
- ✅ Premium feature gating with UpgradeModal and subscription status display
- ✅ Subscription management via Stripe Customer Portal

**User Experience Enhancement**:
- ✅ Trading settings validation with real-time error/warning feedback
- Complete user settings and API key management
- Status messaging improvements and tooltips
- Mobile responsive design implementation

---

## 💳 Stripe Subscription System

### Pro Plan Features ($29/month)
| Feature | Free Plan | Pro Plan |
|---------|-----------|----------|
| **Active Bots** | 1 bot | 10 bots |
| **Analysis Frequency** | 1 hour minimum | 5 minutes minimum |
| **AI Models** | Default Model (basic intelligence) | Frontier Reasoning Models (GPT-5, Claude Opus 4, Grok 4, DeepSeek R1) |
| **Live Trading** | ❌ | ✅ (Symphony.io integration) |
| **Telegram Publishing** | ❌ | ✅ |
| **Priority Support** | ❌ | ✅ |

### Stripe Integration (Complete)
**Backend API Endpoints** (`/api/v2/`):
- `POST /create-checkout-session` - Create Stripe Checkout with 14-day free trial
- `POST /stripe-webhook` - Handle subscription events (HMAC verified)
- `POST /create-portal-session` - Stripe billing portal for self-service management
- `GET /me` - User profile with subscription status

**Frontend Components**:
- `<UpgradeModal>` - Pricing modal with monthly/annual toggle (Dialog system)
- `<PermissionGate>` - Premium feature gates that trigger upgrade modal
- `<UserProfile>` - Subscription badge (Free/Pro) with upgrade/billing buttons
- Updated landing page with accurate Pro Plan pricing

**Early Adopter Promotion**:
- Coupon code: `EARLY50` (50% off for 6 months)
- Coupon ID: `DehSHqyc` (configured in Stripe dashboard)

**Testing Keys**: Currently in Stripe test mode for validation
**Production Switch**: Ready to swap environment variable suffixes for go-live

---

telegram group invite link: https://t.me/+ndI762EkfcszZTUx

### 📡 Recent Session Fixes (2025-09-23)

**Critical Bug Fixes**:
- ✅ **XAI Provider Interface** - Fixed signature mismatch causing signal validation failures
- ✅ **Telegram Publishing Gate** - Removed confidence threshold blocking all low-confidence signals
- ✅ **Symbol Selection UX** - Moved from locked exchange section to accessible trading settings

**New Features**:
- ✅ **Symbol Validation System** - 141 supported trading pairs with dropdown + search
- ✅ **Help Widget** - Floating question mark with Telegram community invitation
- ✅ **Signal Publishing Transparency** - All signals publish with APPROVED/REJECTED status

**UX Improvements**:
- ✅ **Trading Pair Selection** - Professional dropdown replacing free-text input
- ✅ **Symbol Search** - Type-ahead search by base currency (BTC, ETH, SOL, etc.)
- ✅ **Community Access** - Always-visible help widget for user support

### 💽 Disk Space Crisis Resolution (Complete - 2025-09-27)
- **Root Cause**: Single Docker container log file reached 26GB (hummingbot-api)
- **Space Recovery**: 25GB+ freed (disk usage: 67% → 41%)
- **Docker Log Rotation**: Configured 10MB max-size, 3 files (30MB total cap)
- **PM2 Log Rotation**: `pm2-logrotate` with 10MB rotation and compression
- **System Log Management**: Fail2ban installed to prevent auth log bloat
- **Error Rate Limiting**: Connection errors limited to prevent log spam
- **Monitoring**: Enhanced scripts check Docker, PM2, and system logs
- **hummingbot-API**: Restored with proper network, database, and auth configuration

### 📝 Logging System Consolidation (Complete - 2025-09-29)
- **Architecture Cleanup**: Consolidated dual logging systems into single standard configuration
- **Legacy Removal**: Deleted redundant `core/common/logging_config.py` (test files using legacy system ignored)
- **PM2 Integration**: All logs routed through PM2 to `/home/sev/ggbot/logs/` directory structure
- **Log Structure**: Separated by service (ggbot, signal-listener) and type (error, out)
- **Rotation Management**: pm2-logrotate handles compression and cleanup (10MB rotation, 5 files max)
- **Verbosity Reduction**: Removed excessive prompt logging from decision engine (saved to database instead)

### 🔧 Signal Publishing Consolidation (Complete - 2025-09-27)
- **Architecture Cleanup**: Removed unused `signal-publisher` PM2 service and empty queue processing
- **Publishing Integration**: Telegram publishing now handled directly by ggbot.py orchestrator
- **Code Consolidation**: Preserved working publishing functions while removing PM2 service scaffolding
- **Production Mode**: Fixed `DEVELOPMENT_MODE=false` for proper Supabase authentication
- **Ecosystem Update**: Removed signal-publisher from PM2 configuration (ecosystem.config.js)

### 🚀 Position Monitoring Reliability Fix (Complete - 2025-09-27)
- **Critical Issue**: ConnectionTerminated errors preventing stop-loss/take-profit execution
- **Root Cause**: 100+ individual HTTP requests to Supabase every 3 seconds (1200+ requests/minute)
- **Elegant Solution**: Batch SQL updates using PostgreSQL `UPDATE FROM VALUES` pattern
- **Performance**: 100 position updates = 1 SQL query instead of 100 HTTP requests (99% reduction)
- **Trading Safety**: Position closures now execute before price updates (no more failed SL/TP)
- **Graceful Fallback**: Automatic fallback to individual updates if batch fails
- **Results**: ConnectionTerminated errors eliminated, monitoring running reliably

### 💳 Stripe Subscription System (Complete - 2025-10-01)
- **Pro Plan Implementation**: $29/month with 14-day free trial, annual option at $279/year
- **Complete Backend Integration**: Checkout sessions, webhook handlers (4 events), billing portal, user profile endpoint
- **Frontend Upgrade Flow**: Modal-based upgrade system with permission gate integration
- **Subscription UI**: Pro/Free badges in UserProfile, upgrade buttons, billing portal access
- **Early Adopter Campaign**: 50% off for 6 months (coupon: EARLY50)
- **Landing Page Update**: Accurate pricing display (removed blur, updated features)
- **Testing Ready**: Full Stripe test mode integration, ready for production key swap

### ✅ Trading Settings Validation (Complete - 2025-10-01)
- **Validation Hook**: Real-time field validation with error/warning states
- **6 Validated Fields**: Leverage (1-100, warning >20), Stop Loss (1-50%), Take Profit (1-500%), Position Size (0.1-100%, warning >50%), Fixed Amount (max account balance), Max Positions (1-50, warning >10)
- **Visual Feedback**: Red borders/text for errors, yellow for warnings, inline messages with icons
- **UX Enhancement**: Errors block save, warnings allow save with notification
- **Component**: ValidationMessage with AlertCircle/AlertTriangle icons

### 🚀 LLM & Extraction Performance Upgrades (Complete - 2025-10-03)
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

*Last major update: LLM provider upgrades + extraction parallelization (2025-10-03)*

### 🚀 Hummingbot-API Deprecation + Resilience (Complete - 2025-10-21)
**Replaced Hummingbot API with bulletproof WebSocket live prices**:
- **Removed Infrastructure**: Hummingbot API (port 8888), PostgreSQL (5433), EMQX broker (1883+)
- **New Implementation**: LivePriceService using WebSocket live candle data from market-data-ws
- **Performance**: Sub-millisecond Redis access vs 800ms+ REST API calls
- **Freshness**: ~1 second updates vs 30 second cache
- **Resource Savings**: Freed 200MB+ RAM from 3 Docker containers
- **Architecture**: Live candles stored at `price:live:{symbol}` in Redis, updated every ~1s
- **Files Archived**: `archive/hummingbot/` (market_data.py, data_client.py, HBOT_API.md)
- **Migration**: Paper trading, decision engine, and position monitoring now use LivePriceService

**Production Resilience Improvements** (2025-10-21):
- **Automatic Reconnection**: Exponential backoff (1s → 300s max) with up to 100 retry attempts
- **Connection Health Monitoring**: 30s recv() timeout prevents infinite blocking
- **Proactive Reconnection**: Automatic reconnect every 15 minutes (prevents Binance disconnects before they happen)
- **Faster Silence Detection**: 60s threshold (was 120s) - reconnects before live price TTL expires
- **Seamless Reconnection**: Historical candles refetched on every reconnect (1-2s, prevents indicator errors)
- **Connection Lifecycle Logging**: Detailed logging of connections, disconnects, and uptime
- **PM2 Logging Fix**: Logs now go to `logs/market-data-ws-*.log` (was `/dev/null`)
- **Increased Resilience**: max_restarts 20 → 50 for production reliability
- **Result**: Zero-downtime operation with proactive prevention, no price data errors, no indicator calculation failures

### 📉 Liquidation System (Complete - 2025-10-04)
**Paper Trading Engine Realism**:
- **Liquidation Price Calculation**: Automatically calculated on trade open based on margin and leverage
- **Automatic Liquidation**: Positions auto-close when price hits liquidation level (checked first, highest priority)
- **Database Schema**: Added `liquidation_price` column to paper_trades table
- **Realistic Simulation**: High leverage positions now liquidate correctly (e.g., 10x leverage liquidates at ~10% adverse move)
- **Priority Order**: Liquidation → Stop Loss → Take Profit (matches real exchange behavior)

### 🐦 X Bot Service (Complete - 2025-10-04)
**Automated X (Twitter) Bot for @ggbots_ai**:
- **Separate PM2 Service**: Independent x-bot process with APScheduler (isolates social media from trading operations)
- **Platform Status Tweets**: Daily automated tweets at 9:00 AM UTC with real-time platform metrics (active bots, users, trades, symbols tracked, open positions)
- **Database Integration**: Queries configurations and paper_trades tables for live platform statistics
- **Free Tier Strategy**: ~90 reads/month + ~240 writes/month (well within 100 read/500 write limits)
- **Architecture**: Tweepy v4 wrapper with error handling, separate schedulers directory for extensibility
- **Files**: `x_bot/bot.py` (main service), `x_bot/utils/x_client.py` (API wrapper), `x_bot/schedulers/platform_status.py` (daily tweet logic)
- **Future Expansion**: Ready for trade announcements, weekly summaries, targeted account replies (documented in X_BOT.md)

### 📧 Resend Email Integration (Phase 1 Complete - 2025-10-11)
**Automated Email System for User Communication**:
- **Service Module**: `core/services/resend_service.py` with full Resend API integration
- **Contact Management**: Automated sync of Supabase users to Resend audience (189/261 users synced)
- **Email Templates**: Professional responsive templates in `core/email_templates/` (welcome, trade alerts, signal alerts, generic notifications)
- **Active Features**: Welcome emails automatically sent on new user signup via `user_service.py`
- **User Sync**: Bulk sync script `scripts/sync_resend_contacts.py` for migrating existing users
- **Rate Limiting**: Handles Resend's 2 req/sec limit with graceful error handling
- **Future Integration**: Trade notification and signal alert templates ready, awaiting integration into trading/decision pipelines
- **Documentation**: Complete setup and usage guide in `DOCS/RESEND.md`

### 📊 Universal Data Layer (Production - 2025-10-19)
**Catalog-Driven Market Intelligence Platform**:
- **Phase 1 Foundation**: MarketIntelligence gateway with DataCatalog, CacheManager, ResponseFormatter
- **Phase 2 Migration**: ExtractionEngine migrated to UniversalDataClient via Adapter Pattern (2 lines changed)
- **Production Deployment**: Live in production, 100% success rate across all test scenarios
- **Performance**: 3x-3000x faster extractions (1-5ms cached vs 2-3s REST polling)
- **Data Sources**: RedisWebSocketAdapter (priority 1) + BinanceRestAdapter (automatic fallback)
- **Testing**: 8 integration tests passing (OHLCV flow, Preprocessor compatibility, ExtractionEngine validation)
- **Architecture**: Foundation for 150+ future data sources (sentiment, news, on-chain, fundamentals)
- **Files**: `market_intelligence/*` (complete framework), `extraction/v2/universal_data_client.py` (adapter)
- **Documentation**: Complete architecture in `DOCS/UNIVERSAL_DATA.md`

### 🌐 WebSocket Market Data Cache (Production - 2025-10-19)
**Real-Time Market Data Streaming via Binance WebSocket**:
- **Coverage**: 100 symbols (ggbots + Symphony compatible) × 7 timeframes = 700 datasets
- **Symbols**: Expanded from 20 → 100 to cover all Symphony.io-compatible trading pairs
- **Performance**: Sub-100ms data retrieval for cached symbols (vs ~800ms REST fallback)
- **Architecture**: 200-candle rolling windows maintained in Redis via WebSocket push updates
- **Capacity**: 700/1024 Binance WebSocket streams (68% utilization, room for growth)
- **Historical Fetch**: 1.8 seconds for all 700 datasets on startup (100% success rate)
- **Memory Impact**: ~16MB total (Redis + service overhead)
- **Symphony Ready**: All 100 cached symbols work with Symphony.io live trading
- **Files**: `core/services/websocket_market_data_service.py`

### 🔐 Subscription Permission Fix (2025-10-19)
**Critical Bug Fix for Premium Feature Access**:
- **Issue**: `subscription_expires_at` set to trial end date instead of NULL for active subscriptions
- **Impact**: Users with expired trials couldn't access premium features despite active paid subscriptions
- **Root Cause**: Webhook handler setting expiration date for ongoing subscriptions (should be NULL)
- **Fix**: Updated `handle_checkout_completed` to set `subscription_expires_at = NULL` for active subs
- **Result**: Premium permissions now work correctly (can_use_premium_features = true for ggbase tier)
- **Files**: `ggbot.py` (webhook handler), database migration for existing users

### 🎯 Symphony Live Trading Integration (Complete - 2025-01-19)
**Production-Ready Live Trading via Symphony.io**:
- **Database Schema**: Extended `user_profiles`, `configurations`, and new `live_trades` table with idempotency protection
- **Vault Integration**: Encrypted Symphony API key storage with credential management endpoints
- **Symphony Service**: Thin wrapper (`trading/live/symphony_service.py`) - 3 core methods (execute, close, query)
- **Orchestrator Routing**: Smart routing between paper/live based on `trading_mode` (locked per bot)
- **API Endpoints**: 6 endpoints for setup, status, disconnect, positions, close, and duplicate-as-live
- **Frontend UX**: Settings modal for Symphony connection, "Deploy Live Version" flow, LIVE badge distinction
- **Position Sizing**: Leverages existing account_percentage & confidence_based (Symphony requires %)
- **Symbol Compatibility**: 100 out of 141 symbols ready for live trading
- **Weight Calculation**: Automatic conversion using existing position sizing logic
- **Security**: API keys encrypted in Vault, ownership verification on all operations
- **Files**: Database migration, `symphony_service.py`, `DuplicateAsLiveModal.tsx`, 6 API endpoints, BotConfigV2 model updates

### 🛡️ Frontend Reliability & Error Recovery (Complete - 2025-01-21)
**Production Resilience for Symphony Integration**:
- **API Client Retry Logic**: Exponential backoff (1s, 2s, 4s) with 3 retry attempts on network failures
- **SSE Auto-Reconnection**: Automatic reconnection with exponential backoff (5s → 60s) for real-time updates
- **Error State UI**: Visual feedback banners for load failures and connection status
- **Page Visibility Retry**: Automatic retry when user returns to tab after errors
- **Symphony Auth Fix**: Fixed 401 Unauthorized in Settings modal (proper session token handling)
- **Result**: Frontend now resilient to network issues, no manual refresh required