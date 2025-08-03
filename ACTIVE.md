# 🚀 ACTIVE - GGBots System Status

**Last Updated**: 2025-08-02  
**System Health**: 🟢 Operational

---

## 📊 System Overview

### Core Services (PM2)
| Service | Status | CPU | Memory | Uptime | Purpose |
|---------|--------|-----|---------|---------|---------|
| ggbots-api | 🟢 Online | 0% | 201MB | 6m | Main API server (FastAPI) |
| ccxt-mcp-server | 🟢 Online | 0% | 12MB | 25h | Crypto price/data provider |
| ggshot-filter | 🟢 Online | 0% | 64MB | 5m | Signal filtering service |

### Database Services
| Service | Status | Port | Purpose |
|---------|--------|------|---------|
| PostgreSQL (ggbot) | 🟢 Online | 5432 | Main application database |
| PostgreSQL (hummingbot) | 🟢 Online | 5434 | Trading data storage |

### Hummingbot Trading Infrastructure
| Service | Status | Port | Purpose |
|---------|--------|------|---------|
| hummingbot-api | 🟢 Online | **15888** | Trading API server |
| hummingbot-broker (EMQX) | 🟢 Online | 1883,8081,8083,8084,8883,18083,61613 | Message broker for real-time updates |

---

## 🔌 **COMPLETE PORT REFERENCE**

### Application Ports
| Port | Service | Protocol | Access | Purpose |
|------|---------|----------|--------|---------|
| **8000** | ggbots-api | HTTP | Public | Main API server (extraction, decision, trading, dashboard) |
| **8080** | Node.js (unknown) | HTTP | Local | Unknown service |
| **15888** | hummingbot-api | HTTP | Internal | Trading execution & monitoring |

### Database Ports
| Port | Service | Access | Purpose |
|------|---------|--------|---------|
| **5432** | PostgreSQL (ggbot) | Local | Main application data |
| **5434** | PostgreSQL (hummingbot) | Local | Trading data & configurations |

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
| **53** | DNS | Local | DNS resolution |
| **80** | HTTP | Public | Web server |
| **443** | HTTPS | Public | Secure web server |
| **631** | CUPS | Local | Printing services |

---

## 🔄 Background Tasks & Scheduled Jobs

### Always Running
1. **WebSocket Updates** (`dashboard_api.py`)
   - Frequency: Every 30 seconds
   - Purpose: Push position updates to connected dashboard clients
   - Status: ✅ Fixed - only runs when connections exist

2. **Process Cleanup** (`agent_control_api.py`)
   - Frequency: Every 5 minutes (was 60s)
   - Purpose: Clean up terminated trading/extraction/decision processes
   - Status: ✅ Fixed - only runs when processes exist

3. **Old Status Cleanup** (`extraction/api.py`)
   - Frequency: Every hour
   - Purpose: Clean up extraction statuses older than 24 hours
   - Status: ✅ Low impact

4. **Decision Cache Cleanup** (`decision/api.py`)
   - Frequency: Every hour
   - Purpose: Clean up decision cache older than 24 hours
   - Status: ✅ Low impact

### Scheduled Jobs (When Enabled)
- **Autonomous Trading**: Currently DISABLED
- **Scheduled Extractions**: Currently DISABLED

---

## 🎯 Current Focus

### Live Production Service
**ggShot Signal Filtering** 
- Status: 🟢 **ACTIVE** - Running 2-week test with improved prompting structure
- Processing: ~10-12 signals/day with 10 technical indicators
- Publishing: High-confidence signals to Telegram (≥0.50)
- Test Started: 3 days ago with enhanced prompt framework

### 🚀 NEW PRIORITY: Hummingbot Trading Integration
**Status**: ✅ **PHASE 1 COMPLETE** (2025-08-02)
- **Goal**: Replace CCXT MCP with Hummingbot for paper trading
- **Phase 1**: ✅ Core infrastructure deployed and **ggShot signals working**
  - Official hummingbot-api running (localhost:15888) ✅
  - EMQX message broker configured (7 ports for real-time communication) ✅
  - PostgreSQL database dedicated to trading (localhost:5434) ✅
  - HummingbotExecutionAdapter with LLM normalization ✅
  - **ggShot filter fixed - signals processing correctly** ✅
  - **Test signal execution successful (CFX/USDT SHORT)** ✅
  - Port configuration clean and documented ✅
- **Phase 2**: Multi-pair & multi-user support + database integration (Next: Week 2)
- **Phase 3**: Production features & strategic management (Week 3)
- **Benefits**: Paper trading capability + 70-80% monitoring overhead reduction

### Active Tasks
1. **Priority 1**: Hummingbot integration implementation (TRADING_UPDATE.md checklist)
2. **Ongoing**: 2-week test of improved ggShot filter service

---

## 🏗️ What We Just Completed

**4-Pillar Framework Implementation** ✅
- Replaced simple RSI with 10-indicator analysis
- Market regime detection (Aroon/BBW)
- Volume confirmation (SMA_Volume_30/Vortex/VWAP)
- Multi-timeframe context (RSI + RSI_4h)
- Risk assessment (Bollinger Bands/ATR)
- Custom system prompts for ggShot mode
- Graduated confidence scoring (0.00-1.00)

## 🎯 Next Steps
1. **Execute Hummingbot Integration** - Follow TRADING_UPDATE.md implementation checklist (3-week plan)
2. **Complete ggShot Test** - Continue 2-week test of improved prompting structure (parallel track)

---

## 📈 Performance Metrics

### ggShot Performance
- Framework: 4-Pillar validation with improved prompting
- Indicators: 10 technical indicators per signal
- Processing time: ~55 seconds
- Confidence threshold: 0.50
- Test Phase: Day 3 of 2-week improved version test

### System Resources
- API: 280MB (57% CPU)
- CCXT MCP: 52MB stable
- ggShot: 58MB stable

---

## 🔧 Maintenance Notes

### Recent Changes
- **2025-08-02**: ✅ **MAJOR**: Completed Hummingbot Phase 1 - ggShot signals working end-to-end
- **2025-08-02**: Fixed critical port configuration issues (ggbots-api:8000, hummingbot:15888)
- **2025-08-02**: Updated comprehensive port documentation (15 total ports mapped)
- 2025-07-31: **NEW PRIORITY**: Started Hummingbot trading integration implementation (TRADING_UPDATE.md)
- 2025-07-31: Started 2-week test of improved ggShot prompting structure
- 2025-07-16: Fixed DeepSeek parsing issues and Claude 4 API integration
- 2025-06-29: **Major**: Implemented 4-Pillar validation framework

### Monitoring Commands
```bash
# Check service status
pm2 list
pm2 monit

# View logs
pm2 logs ggbots-api
pm2 logs ggshot-filter

# Check system resources
htop
df -h

# Database connections
psql -U ggbots -d ggbots -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## 🚨 Emergency Contacts

- **System**: Ubuntu VM on personal infrastructure
- **Database**: PostgreSQL (local)
- **External Services**:
  - Telegram API (ggShot signals)
  - **LLM APIs**: DeepSeek, OpenAI (o1), Anthropic (Claude 4)
  - Multiple crypto exchanges (CCXT)

---

*This file should be updated regularly to reflect the current system state*