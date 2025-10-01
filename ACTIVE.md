# 🚀 ACTIVE - ggbots System Status

**Last Updated**: 2025-10-01 (Stripe subscription system + trading validation)
**System Health**: 🟢 Production Live (225+ users, 100+ active bots)
**Project Status**: Live application with complete Stripe monetization and trading validation

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
| ggbot | 🟢 Online | 0% | ~165MB | V2 Orchestrator API server with integrated scheduler & telegram publishing |
| signal-listener | 🟢 Online | 0% | ~63MB | External signal processing service (ggShot integration) |
| pm2-logrotate | 🟢 Online | 0% | ~57MB | Automated log rotation and compression (10MB rotation, 5 files max) |

### Infrastructure Services
| Service | Status | Port | Purpose |
|---------|--------|------|---------| 
| Supabase PostgreSQL | 🟢 Online | Remote | Main application database (managed) |
| PostgreSQL (hummingbot) | 🟢 Online | 5433 | Hummingbot API database (Docker) |
| Hummingbot API | 🟢 Online | 8888 | Trade execution and market data (Docker) |
| EMQX Message Broker | 🟢 Online | 1883+ | Real-time bot communication (Docker) |
| Redis | 🟢 Online | 6379 | Scheduler idempotency and caching |

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
- **Multi-exchange Hummingbot integration** with automatic fallback (5 exchanges)
- **$10,000 isolated accounts** per configuration
- **✅ 3-second position monitoring** ACTIVE (batch SQL updates for efficiency)
- **Confidence-based position sizing**
- **Enhanced reliability** - eliminates single exchange failure points

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
| **5433** | PostgreSQL (hummingbot) | Docker only | Hummingbot API database |

### Hummingbot Integration Ports (Active)
| Port | Service | Status | Purpose |
|------|---------|--------|------------|
| **8888** | hummingbot-api | 🟢 **ACTIVE** | HTTP API server (Docker container) |
| **1883** | EMQX Message Broker | 🟢 **ACTIVE** | MQTT communication |
| **8081** | EMQX Management | 🟢 **ACTIVE** | HTTP management API |
| **8083, 8084** | EMQX WebSocket | 🟢 **ACTIVE** | MQTT over WebSocket |
| **8883** | EMQX SSL | 🟢 **ACTIVE** | MQTT over SSL |
| **18083** | EMQX Dashboard | 🟢 **ACTIVE** | Web management interface |
| **61613** | EMQX STOMP | 🟢 **ACTIVE** | Web-STOMP gateway |

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
- **Templates**: `core/config/template_signal_validation.json`
- **Publishing**: Integrated into ggbot.py orchestrator (signal-publisher PM2 service discontinued)

### **Multi-Timeframe Architecture** (Complete)
- **7 timeframes**: 5m, 15m, 30m, 1h, 4h, 1d, 1w extraction
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
| **AI Models** | Basic models | Frontier reasoning models |
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

*Last major update: Stripe subscription system + trading validation (2025-10-01)*