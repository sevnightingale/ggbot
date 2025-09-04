# 🚀 ACTIVE - GGBots System Status

**Last Updated**: 2025-09-03  
**System Health**: 🟢 Operational  
**V2 Architecture**: Phase 7 Frontend-Backend Integration ✅ Complete

---

## 🎯 V2 Architecture Progress
- ✅ **Phase 1: Supabase Migration** - Multi-user database with RLS, auth utilities, 15 tables deployed
- ✅ **Phase 2: V2 Extraction System** - 21 preprocessors, 12x performance improvement, pandas-ta integration
- ✅ **Phase 7: Frontend-Backend Integration** - Dashboard connected to V2 API, mock auth, full data flow

---

## 🌐 API Access Points

### Production API Endpoints
| Service | Internal Port | Public URL | SSL | Purpose |
|---------|--------------|------------|-----|---------|
| **V2 Orchestrator** | `localhost:8001` | TBD | ✅ | V2 backend with Supabase auth |
| **ggbots-api** | `localhost:8000` | `https://ggbots-api.nightingale.business` | ✅ | V1 backend API |
| **Frontend** | N/A | `https://ggbot-app.vercel.app` | ✅ | Next.js application |

### Active API Calls (Most Used)

**Bot Control** (Currently placeholder - will rebuild)
- `GET /agent/api/bots` - List all bots for a user (frontend loads on mount)
- `POST /agent/api/bots/{config_id}/start` - Start bot (with optional `demo_mode`)
- `POST /agent/api/bots/{config_id}/stop` - Stop bot
- `WS /ws/bot-status/{user_id}` - WebSocket placeholder (monitoring removed)

**Trading Data**
- `GET /api/live-position-data` - Fetch current positions with P&L (frontend polls every 15s)
- `GET /api/ggshot-filter-stats` - Historical ggShot performance data

**Paper Trading Engine**
- `POST /paper/execute` - Execute paper trade from Decision Module intent
- `GET /paper/positions/{config_id}` - Get open positions with real-time P&L
- `GET /paper/account/{config_id}` - Account summary with performance analytics
- `POST /paper/close/{trade_id}` - Close position manually
- `GET /paper/health` - Service health and diagnostics

**Signal Processing (Backend-to-Backend)**
- `POST /api/run-extraction` - ggshot-filter calls this to process new signals
- `POST /api/run-decision` - Decision validation after extraction
- `POST /decision/webhooks/trigger-decision` - Trigger decision → paper trading pipeline

**Demo Mode**
- `POST /agent/api/bots/e249bb49-0455-4596-9657-09bf9e14ca14/start` - Start ggbot-01 demo
- WebSocket broadcasts `demo_position_create` messages during demo

### Frontend Configuration
- **Production**: Uses `NEXT_PUBLIC_API_URL=https://ggbots-api.nightingale.business`
- **Development**: Uses `NEXT_PUBLIC_API_URL=http://localhost:8000`
- **Nginx Proxy**: SSL termination handled by nginx with Let's Encrypt certificates
- **CORS**: Enabled for frontend access from Vercel deployment

---

## 📊 System Overview

### Core Services (PM2)
| Service | Status | CPU | Memory | Purpose |
|---------|--------|-----|---------|---------|
| ggbots-api | 🟢 Online | 0% | 200MB | Main API server (FastAPI) |
| ccxt-mcp-server | 🟢 Online | 0% | 5MB | Crypto price/data provider |
| ggshot-filter | 🟢 Online | 0% | 25MB | Signal filtering service |

### Infrastructure Services
| Service | Status | Port | Purpose |
|---------|--------|------|---------|
| PostgreSQL (ggbot) | 🟢 Online | 5432 | Main application database |
| PostgreSQL (hummingbot) | 🟢 Online | 5433 | Hummingbot API database (Docker) |
| Hummingbot API | 🟢 Online | 8888 | Trade execution and market data (Docker) |
| EMQX Message Broker | 🟢 Online | 1883+ | Real-time bot communication (Docker) |

---

## 🎯 Current Focus

### 🟢 Live Production Service
**ggShot Signal Filtering - Test #3** 
- Status: **LAUNCHED** - Test #3 active with v4.1 refined guardrails (2025-08-17)
- Previous Test #2: Ran 7/28 - 8/13, comprehensive analysis completed
- Processing: ~10-12 signals/day with enhanced 4-Pillar scoring
- Publishing: High-confidence signals to Telegram (≥0.65 threshold)

### ✅ Recently Completed

**Demo Mode Implementation - COMPLETED** (2025-08-17)
- ✅ 45-second intelligence showcase with real ggShot data
- ✅ WebSocket message forwarding for demo position creation
- ✅ 4-Pillar Validation Framework display in BotControlModal
- ✅ AI reasoning expandable rows in trade tables
- ✅ Live P&L updates using real market prices
- ✅ Frontend WebSocket integration via callback system

**Bot Monitoring Integration - COMPLETED** (2025-08-14)
- ✅ Integrated bot monitoring into main ggbots-api service
- ✅ WebSocket endpoint `/ws/bot-status/{user_id}` operational
- ✅ Real-time bot status broadcasting every 10 seconds
- ✅ Frontend-ready data structure and heartbeat system
- ✅ Removed separate bot-monitor PM2 service (consolidated architecture)
- ✅ 24MB memory savings from service consolidation

### Active Tasks
1. **GGBotConfig Design System** - ✅ **COMPLETED** (2025-08-22)
   - ✅ Trading Agent configuration with risk management and exchange connections
   - ✅ Interactive sliders, professional button groups, and responsive layouts
   - ✅ Visual hierarchy fixes for data source tabs and indicator selection
   - ✅ Component height increased to 90vh for better user experience
   - ✅ Custom CSS slider styling with agent-trading orange theming
   
2. **Next Phase: Backend Integration & Demo Fork**
   - **Production Version**: Wire up real backend APIs, strip mock data
   - **Demo Version**: Enhanced mock data for sales/marketing showcase
   - Configuration persistence with save/load functionality
   - Real-time validation and error handling from API responses
   
2. **Paper Trading Engine** - ✅ **PRODUCTION READY** (2025-08-27)
   - **Status**: **FULLY OPERATIONAL** - Complete paper trading system with Hummingbot integration
   - **Architecture**: Real-time market data from Hummingbot API + custom execution engine
   - **Features**: Isolated $10k accounts, 7-second monitoring, confidence-based sizing
   - **Database**: New paper trading tables (paper_accounts, paper_trades, paper_orders)
   - **Integration**: Decision Module → Paper Trading → Real-time P&L tracking
   - **Next**: Frontend integration for position monitoring and portfolio analytics

---

## 🔌 Complete Port Reference

### Application Ports
| Port | Service | Protocol | Access | Purpose |
|------|---------|----------|--------|---------|
| **8000** | ggbots-api | HTTP | Public | Main API server (extraction, decision, agent control) |
| **8080** | code-server | HTTP | Public | VSCode in browser (development environment) |

### Database Ports
| Port | Service | Access | Purpose |
|------|---------|--------|---------|
| **5432** | PostgreSQL (ggbot) | Localhost only | Main application data |
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

- **Paper Trading Monitor**: ACTIVE (7-second position updates with auto TP/SL execution)
- **ggShot Filter Service**: ACTIVE (processing signals 24/7, Test #3 preparing)
- **Process Cleanup**: Every 5min (terminated processes)
- **Cache Cleanup**: Every hour (old statuses/decisions)
- **Demo Mode**: On-demand (45-second sequences with real ggshot_filter data)
- **Autonomous Trading**: PAPER MODE ACTIVE (live trading expansion planned)
- **Scheduled Extractions**: DISABLED

---

## 🔧 Quick Commands

```bash
# Service status
pm2 list
pm2 monit

# Logs  
pm2 logs ggbots-api
pm2 logs ggshot-filter

# Resources
htop
df -h
```

---

*Last major update: V2 Architecture Phase 7 complete - Dashboard integrated with V2 orchestrator, Supabase auth, full frontend-backend data flow operational (2025-09-03)*