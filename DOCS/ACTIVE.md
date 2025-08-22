# 🚀 ACTIVE - GGBots System Status

**Last Updated**: 2025-08-21  
**System Health**: 🟢 Operational

---

## 🌐 API Access Points

### Production API Endpoints
| Service | Internal Port | Public URL | SSL | Purpose |
|---------|--------------|------------|-----|---------|
| **ggbots-api** | `localhost:8000` | `https://ggbots-api.nightingale.business` | ✅ | Main backend API |
| **Frontend** | N/A | `https://ggbot-app.vercel.app` | ✅ | Next.js application |

### Active API Calls (Most Used)

**Bot Control & Monitoring**
- `GET /agent/api/bots` - List all bots for a user (frontend loads on mount)
- `POST /agent/api/bots/{config_id}/start` - Start bot (with optional `demo_mode`)
- `POST /agent/api/bots/{config_id}/stop` - Stop bot
- `WS /ws/bot-status/{user_id}` - WebSocket for real-time status updates

**Trading Data**
- `GET /api/live-position-data` - Fetch current positions with P&L (frontend polls every 15s)
- `GET /api/ggshot-filter-stats` - Historical ggShot performance data

**Signal Processing (Backend-to-Backend)**
- `POST /api/run-extraction` - ggshot-filter calls this to process new signals
- `POST /api/run-decision` - Decision validation after extraction
- ~~`POST /api/execute-trade` - Trade execution~~ **REMOVED** (Hummingbot integration removed)

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
| ggbot-api | 🟢 Online | 0% | 329MB | Main API server (FastAPI + integrated bot monitoring) |
| ccxt-mcp-server | 🟢 Online | 0% | 5MB | Crypto price/data provider |
| ggshot-filter | 🟢 Online | 0% | 25MB | Signal filtering service |

### Infrastructure Services
| Service | Status | Port | Purpose |
|---------|--------|------|---------|
| PostgreSQL (ggbot) | 🟢 Online | 5432 | Main application database |

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
1. **Demo Buildout** - Polish design & UX (core functionality complete)
   - Add restart demo button
   - Mobile responsiveness testing
   - agent configurations
   
2. **Fresh Hummingbot Integration** - Clean slate approach
   - **Status**: **COMPLETE REMOVAL** - All legacy integration deleted (2025-08-21)
   - **Current**: Clean system with no Hummingbot components
   - **Next Steps**: Implement new API-only integration per DOCS/HUMMINGBOT.md
   - **Approach**: Official Hummingbot API Docker deployment
   - **Phase 1**: Core API Setup targeting single ggShot signal execution

---

## 🔌 Complete Port Reference

### Application Ports
| Port | Service | Protocol | Access | Purpose |
|------|---------|----------|--------|---------|
| **8000** | ggbot-api | HTTP | Public | Main API server (extraction, decision, agent control) |
| **8080** | code-server | HTTP | Public | VSCode in browser (development environment) |

### Database Ports
| Port | Service | Access | Purpose |
|------|---------|--------|---------|
| **5432** | PostgreSQL (ggbot) | Localhost only | Main application data |

### Freed Ports (Available for New Hummingbot Integration)
| Port | Previous Use | Status |
|------|-------------|--------|
| **15888** | hummingbot-api | 🟢 **AVAILABLE** |
| **5433** | PostgreSQL (hummingbot) | 🟢 **AVAILABLE** |
| **1883, 8081, 8083, 8084, 8883, 18083, 61613** | EMQX Message Broker | 🟢 **AVAILABLE** |

### System Ports
| Port | Service | Access | Purpose |
|------|---------|--------|---------|
| **22** | SSH | Public | Remote access |
| **80** | HTTP | Public | Web server |
| **443** | HTTPS | Public | Secure web server |

---

## 🔄 Background Tasks

- **Bot Status Monitoring**: Every 10s (integrated into main API)
- **WebSocket Bot Status**: Every 10s (real-time broadcasting to connected clients)  
- **ggShot Filter Service**: ACTIVE (processing signals 24/7, Test #3 preparing)
- **Process Cleanup**: Every 5min (terminated processes)
- **Cache Cleanup**: Every hour (old statuses/decisions)
- **Demo Mode**: On-demand (45-second sequences with real ggshot_filter data)
- **Autonomous Trading**: DISABLED (legacy Hummingbot integration removed)
- **Scheduled Extractions**: DISABLED

---

## 🔧 Quick Commands

```bash
# Service status
pm2 list
pm2 monit

# Logs  
pm2 logs ggbot-api
pm2 logs ggshot-filter

# Resources
htop
df -h
```

---

*Last major update: Complete Hummingbot integration removal - Clean slate achieved, all legacy components deleted, ports freed for new API-only integration (2025-08-21)*