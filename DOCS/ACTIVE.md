# 🚀 ACTIVE - GGBots System Status

**Last Updated**: 2025-08-03  
**System Health**: 🟢 Operational

---

## 📊 System Overview

### Core Services (PM2)
| Service | Status | CPU | Memory | Purpose |
|---------|--------|-----|---------|---------|
| ggbots-api | 🟢 Online | 0% | 201MB | Main API server (FastAPI) |
| ccxt-mcp-server | 🟢 Online | 0% | 12MB | Crypto price/data provider |
| ggshot-filter | 🟢 Online | 0% | 64MB | Signal filtering service |

### Infrastructure Services
| Service | Status | Port | Purpose |
|---------|--------|------|---------|
| PostgreSQL (ggbot) | 🟢 Online | 5432 | Main application database |
| PostgreSQL (hummingbot) | 🟢 Online | 5434 | Trading data storage |
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

### Active Tasks
1. **Deploy ggShot paper trading** (infrastructure ready)
2. **Continue ggShot filter test** (ongoing 2-week evaluation)

---

## 🔌 Complete Port Reference

### Application Ports
| Port | Service | Protocol | Access | Purpose |
|------|---------|----------|--------|---------|
| **8000** | ggbots-api | HTTP | Public | Main API server (extraction, decision, trading, dashboard) |
| **8080** | Node.js | HTTP | Local | Active Node.js process (PID 214156) |
| **15888** | hummingbot-api | HTTP | Internal | Trading execution & monitoring |

### Database Ports
| Port | Service | Access | Purpose |
|------|---------|--------|---------|
| **5432** | PostgreSQL (ggbot) | Localhost only | Main application data (not in VSCode ports) |
| **5434** | PostgreSQL (hummingbot) | All interfaces | Trading data & configurations (visible in VSCode) |

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

- **WebSocket Updates**: Every 30s (dashboard clients)
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

*Last major update: HUM_INTEGRATION Phase 1 complete - universal paper trading ready*