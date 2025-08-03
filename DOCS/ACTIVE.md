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



● Updated Assessment with Technical Analysis 8/2/25

  Based on your clarifications and technical investigation, here's the revised
  assessment:

  Current System Status Analysis ✅

  1. Database & Migration Status

  - CURRENT STATE: ✅ Database is FULLY migrated including latest schemas
  - CONFIRMED: 19 tables including trades, strategy_runs, ggshot_filter
  - HUMMINGBOT IMPACT: ⚠️ Your hummingbot transition will require new trade schema -
  current PostgreSQL is configured for legacy system

  2. Active MCP Services ✅

  PM2 Status (Currently Running):
  - ccxt-mcp-server (ID: 1) - AUTHORITATIVE for extraction/decision
  - ggbots-api (ID: 4) - Main API server
  - ggshot-filter (ID: 2) - ggShot filtering (production)

  ✅ CONFIRMED: ccxt-mcp-server is the live system that extraction/decision modules use

  3. Config System Status

  - TEMPLATE: /home/sev/ggbot/core/config/template.json exists and current
  - GOOD NEWS: Template is clean, well-structured JSON blob approach
  - CONFIG-ID PLAN: /home/sev/ggbot/DOCS/CONFIG.md has comprehensive implementation
  roadmap

  Critical Actions Needed 🔥

  1. CLEANUP: Remove Unused MCP Systems

  SAFE TO DELETE:
  # These are legacy/unused indicator systems:
  rm -rf /home/sev/ggbot/extraction/sources/indicators_mcp/
  rm -rf /home/sev/ggbot/extraction/sources/ccxt_mcp/
  rm -rf /home/sev/ggbot/extraction/sources/exchange_api/
  KEEP: core/mcp/servers/crypto-indicators-mcp/ (the 20-indicator system currently
  running)

  2. ENVIRONMENT VARIABLES: Scattered References

  ISSUE FOUND: 15+ files reference environment variables but NO .env FILE EXISTS

  Files mentioning env vars:
  - extraction/README.md: EXTRACTION_LLM_API_KEY, EXCHANGE_NAME
  - decision/engine.py: DECISION_LLM_API_KEY
  - hummingbot/README.md: HUMMINGBOT_API_HOST
  - ggshot/README.md: GGSHOT_CONFIG_ID, TG_API_ID, etc.

  RECOMMENDATION: Create central .env file:
  # /home/sev/ggbot/.env
  EXTRACTION_LLM_API_KEY=your_key
  DECISION_LLM_API_KEY=your_key
  EXCHANGE_NAME=binance
  HUMMINGBOT_API_HOST=http://localhost:8088
  GGSHOT_CONFIG_ID=e249bb49-0455-4596-9657-09bf9e14ca14
  # ... etc

  3. CONFIG SYSTEM: Immediate Improvements

  CURRENT: JSON blob approach works but needs refinement

  RECOMMENDATIONS:
  1. Validation Schema: Add JSON schema validation to template.json
  2. Environment Integration: Merge env vars into config system
  3. Default Configs: Pre-populate common configs in template
  4. Config Versioning: Add version field for future migrations

  4. HUMMINGBOT INTEGRATION: Database Priority

  CRITICAL: Hummingbot has its own PostgreSQL schema - you need to decide:

  Option A: Dual database (keep current + hummingbot's)
  Option B: Migrate all trade data to hummingbot's schemaOption C: Use hummingbot for
  execution, your DB for decision/config

  RECOMMENDATION: Check hummingbot's schema first:
  -- Connect to hummingbot's postgres and explore
  \dt

  Immediate Next Steps Priority Order 🎯

  Phase 1: Critical Infrastructure

  1. Create .env file with all scattered environment variables
  2. Test hummingbot integration thoroughly (highest priority)
  3. Remove unused MCP systems for cleanup

  Phase 2: Config-ID Implementation

  4. Follow DOCS/CONFIG.md plan for config-id based system
  5. Test frontend API integration with real backend
  6. Implement unified test suite

  Phase 3: Production Readiness

  7. Document deployment procedures
  8. Create end-to-end journey documentation
  9. Consolidate all environment variable references

  Documentation Update Recommendations

  1. Remove all Bubble.io references from documentation
  2. Update README.md files to reflect hummingbot transition
  3. Clarify current vs legacy systems in each module
  4. Add environment variable central documentation
  5. Create unified testing documentation

  The platform is architecturally solid but needs integration testing and consolidation
  rather than new features. Your biggest decision point is the hummingbot database
  integration strategy.
