# 🚀 ACTIVE - ggbots System Status

**Last Updated**: 2025-09-19 (Multi-exchange integration)
**System Health**: 🟢 Operational (enhanced reliability)
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

**Signal Processing**
- `POST /api/v2/orchestrate/{config_id}/signal` - Signal validation endpoint
- Signal listener and publisher services (PM2 background processes)

**Trading & Analytics**
- `GET /api/live-position-data` - Current positions with real-time P&L
- `POST /paper/execute` - Execute paper trades
- `GET /paper/positions/{config_id}` - Position tracking

---

## 📊 System Architecture

### Core Services (PM2)
| Service | Status | CPU | Memory | Purpose |
|---------|--------|-----|--------|---------|
| ggbot | 🟢 Online | 0% | 218MB | V2 Orchestrator API server with integrated scheduler |

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
- **Telegram publishing** to user-specified channels
- **Complete V2 integration** using standard extraction → decision → trading flow

### **Paper Trading Engine**
- **Multi-exchange Hummingbot integration** with automatic fallback (5 exchanges)
- **$10,000 isolated accounts** per configuration
- **❌ 7-second monitoring** MISSING (needs re-integration)
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
- **PM2 Services**: `signal-listener`, `signal-publisher` (configured)

### **Multi-Timeframe Architecture** (Complete)
- **7 timeframes**: 5m, 15m, 30m, 1h, 4h, 1d, 1w extraction
- **Rich LLM context** across all timeframes for decision making
- **Database storage** with separate rows per timeframe

---

## 🎯 Current Focus

### 🟡 Production Status (Transition Phase)
**Autonomous Scheduling** - ✅ Multi-timeframe bots running with zero-drift execution
**Paper Trading Engine** - ❌ Missing real-time position monitoring (manual testing phase)
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

*Last major update: Forge architecture Phase 1 complete - data foundation with multi-bot support and SSE integration (2025-09-13)*