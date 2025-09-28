# 🚀 ACTIVE - ggbots System Status

**Last Updated**: 2025-09-23 (Symbol validation, Telegram publishing fixes, Help widget)
**System Health**: 🟢 Operational (enhanced reliability + UX improvements)
**V2 Architecture**: Complete - Full E2E Pipeline with Multi-Exchange Fallback

---

## 🔄 V2 Architecture Transition

**Current Status**: V2 implementation complete but codebase cleanup in progress

**Module Status**:
- `extraction/` - Legacy code + `v2/` folder (use v2)
- `decision/` - Legacy code + V2 engine integrated (use V2 engine)
- `trading/` - Current and up-to-date
- `core/` - V2 architecture (scheduler, config, etc.)

**Legacy cleanup pending** - old modules preserved for reference during transition

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
| ggbot | 🟢 Online | 0% | 218MB | V2 Orchestrator API server with integrated scheduler & telegram publishing |
| pm2-logrotate | 🟢 Online | 0% | 52MB | Automated log rotation and compression (10MB/7-day retention) |

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

- **Paper Trading Monitor**: ❌ MISSING (needs re-integration from legacy)
- **ggShot Filter Service**: ❌ REMOVED (functionality integrated into V2)
- **Autonomous Trading**: ✅ ACTIVE (scheduled bot execution with APScheduler)
- **Log Rotation**: ✅ ACTIVE (PM2-logrotate with 10MB size limits and compression)
- **Disk Space Monitoring**: ✅ ACTIVE (automated checks every 6 hours)
- **Process Cleanup**: Every 5min (terminated processes)
- **Cache Cleanup**: Every hour (old statuses/decisions)
- **Demo Mode**: On-demand (V2 orchestrator integration)

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

### 🟡 Production Status (Transition Phase)
**Autonomous Scheduling** - ✅ Multi-timeframe bots running with zero-drift execution
**Paper Trading Engine** - ✅ Real-time position monitoring active (3-second cycles with batch SQL updates)
**V2 Dashboard** - 🟡 Transitioning to Forge architecture (legacy dashboard deprecated)

### 🔄 Frontend Architecture Transition

**Legacy Dashboard Issues**:
- Complex WebSocket system with infinite loop errors (React #185)
- 600+ line botStore with data transformation layers
- Architectural debt preventing elegant evolution
- Global state management complexity

**New Forge Implementation** (see `FORGE.md`):
- ✅ Clean local state architecture with direct API types
- ✅ Simple SSE streams replacing complex WebSocket patterns
- ✅ Multi-bot switching with `selectedConfigId` pattern
- ✅ Phase 1 data foundation complete, ready for Phase 2 (design system)
- **Working Document**: All development guided by `FORGE.md`

**Migration Status**: Legacy dashboard functional but buggy. Forge page under active development as complete replacement using elegant, maintainable patterns.

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

*Last major update: Position monitoring reliability fix (2025-09-27)*