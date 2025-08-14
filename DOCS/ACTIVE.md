# 🚀 ACTIVE - GGBots System Status

**Last Updated**: 2025-08-04  
**System Health**: 🟢 Operational

---

## 🌐 API Access Points

### Production API Endpoints
| Service | Internal Port | Public URL | SSL | Purpose |
|---------|--------------|------------|-----|---------|
| **ggbots-api** | `localhost:8000` | `https://ggbots-api.nightingale.business` | ✅ | Main backend API |
| **Frontend** | N/A | `https://ggbot-app.vercel.app` | ✅ | Next.js application |

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
| ggbots-api | 🟢 Online | 28% | 324MB | Main API server (FastAPI + integrated bot monitoring) |
| ccxt-mcp-server | 🟢 Online | 0% | 5MB | Crypto price/data provider |
| ggshot-filter | 🟢 Online | 0% | 25MB | Signal filtering service |

### Infrastructure Services
| Service | Status | Port | Purpose |
|---------|--------|------|---------|
| PostgreSQL (ggbot) | 🟢 Online | 5432 | Main application database |
| PostgreSQL (hummingbot) | 🟢 Online | 5433 | Trading data storage |
| hummingbot-api | 🟢 Online | 15888 | Trading API server |
| hummingbot-broker (EMQX) | 🟢 Online | 1883,8081,8083,8084,8883,18083,61613 | Message broker |

---

## 🎯 Current Focus

### 🟢 Live Production Service
**ggShot Signal Filtering** 
- Status: **ACTIVE** - 2-week test with improved prompting
- Processing: ~10-12 signals/day
- Publishing: High-confidence signals to Telegram (≥0.50)

### ✅ Recent Completion
**Hummingbot Trading Integration - Phase 1 COMPLETE** (2025-08-03)
- ✅ Universal paper trading ready for all ggBot strategies
- ✅ Config-based instance mapping implemented
- ✅ $10k isolated paper accounts per configuration
- ✅ All integration tests passing (3/3)

### 🔐 Demo Authentication System - DEPLOYED (2025-08-04)
- ✅ Password protection active ("vibecodecamp")
- ✅ Email-based UUID generation working
- ✅ Backend API endpoints functional (`/api/users/demo-signup`)
- ✅ Frontend deployed on Vercel with proper API configuration
- ⏳ Config API endpoints needed for full demo functionality

### ✅ Recently Completed
**Bot Monitoring Integration - COMPLETED** (2025-08-14)
- ✅ Integrated bot monitoring into main ggbots-api service
- ✅ WebSocket endpoint `/ws/bot-status/{user_id}` operational
- ✅ Real-time bot status broadcasting every 10 seconds
- ✅ Frontend-ready data structure and heartbeat system
- ✅ Removed separate bot-monitor PM2 service (consolidated architecture)
- ✅ 24MB memory savings from service consolidation

### Active Tasks
1. **Frontend WebSocket integration** (connect to `/ws/bot-status/{user_id}`)
2. **Bot control API endpoints** ✅ COMPLETED (start/stop bots via `/agent/api/bots`)
3. **Demo bot configuration system** (12 pre-built configs)
4. **Continue ggShot filter test** (ongoing 2-week evaluation)

---

## 🔌 Complete Port Reference

### Application Ports
| Port | Service | Protocol | Access | Purpose |
|------|---------|----------|--------|---------|
| **8000** | ggbots-api | HTTP | Public | Main API server (extraction, decision, trading, agent control) |
| **8080** | Node.js | HTTP | Local | Active Node.js process (PID 214156) |
| **15888** | hummingbot-api | HTTP | Internal | Trading execution & monitoring |

### Database Ports
| Port | Service | Access | Purpose |
|------|---------|--------|---------|
| **5432** | PostgreSQL (ggbot) | Localhost only | Main application data (not in VSCode ports) |
| **5433** | PostgreSQL (hummingbot) | All interfaces | Trading data & configurations (visible in VSCode) |

### EMQX Message Broker Ports (Hummingbot)
| Port | Protocol | Access | Purpose |
|------|----------|--------|---------|
| **1883** | MQTT | Public | Standard MQTT messaging |
| **8081** | HTTP | Public | EMQX Dashboard |
| **8083** | WebSocket | Public | MQTT over WebSocket |
| **8084** | SSL/WebSocket | Public | Secure MQTT over WebSocket |
| **8883** | MQTTS | Public | MQTT over SSL/TLS |
| **18083** | HTTP | Public | EMQX Management API |
| **61613** | STOMP | Public | STOMP protocol messaging |

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
- **Process Cleanup**: Every 5min (terminated processes)
- **Cache Cleanup**: Every hour (old statuses/decisions)
- **Autonomous Trading**: DISABLED
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

*Last major update: Bot monitoring integrated into main API - WebSocket endpoint `/ws/bot-status/{user_id}` operational with real-time status broadcasting*