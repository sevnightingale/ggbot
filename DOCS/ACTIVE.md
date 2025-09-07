# 🚀 ACTIVE - GGBots System Status

**Last Updated**: 2025-09-07  
**System Health**: 🟢 Operational  
**V2 Architecture**: Phase 8 Full E2E Pipeline ✅ Complete

---

## 🎯 V2 Architecture Progress
- ✅ **Phase 1: Supabase Migration** - Multi-user database with RLS, auth utilities, 15 tables deployed
- ✅ **Phase 2: V2 Extraction System** - 21 preprocessors, 12x performance improvement, pandas-ta integration
- ✅ **Phase 7: Frontend-Backend Integration** - Dashboard connected to V2 API, mock auth, full data flow
- ✅ **Phase 8: Full E2E Pipeline** - Complete Extraction → Decision → Trading pipeline with GPT-5 integration

---

## 🌐 API Access Points

### Production API Endpoints
| Service | Internal Port | Public URL | SSL | Purpose |
|---------|--------------|------------|-----|---------|
| **V2 Orchestrator** | `localhost:8000` | `https://ggbots-api.nightingale.business` | ✅ | V2 backend with Supabase auth |
| **Frontend** | N/A | `https://ggbot-app.vercel.app` | ✅ | Next.js application |

### Active API Calls (V2 Endpoints)

**Configuration Management**
- `GET /api/v2/config` - List all bot configurations for user
- `POST /api/v2/config` - Create new bot configuration
- `GET /api/v2/config/{config_id}` - Get specific configuration
- `PUT /api/v2/config/{config_id}` - Update configuration
- `DELETE /api/v2/config/{config_id}` - Delete configuration

**Bot Control & Orchestration**
- `POST /api/v2/orchestrate/{config_id}` - Run full E2E trading cycle
- `POST /api/v2/bot/{config_id}/start` - Start bot (placeholder)
- `POST /api/v2/bot/{config_id}/stop` - Stop bot (placeholder)
- `GET /api/v2/bot/{config_id}/status` - Get bot status
- `WS /ws/bot-status/{user_id}` - WebSocket for real-time updates

**Bot Data & Analytics**
- `GET /api/v2/bot/{config_id}/metrics` - Performance metrics
- `GET /api/v2/bot/{config_id}/positions` - Live positions
- `GET /api/v2/bot/{config_id}/trades` - Trade history

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
| ggbot | 🟢 Online | 0% | 213MB | V2 Orchestrator API server (ggbot.py) |
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
   
2. **Multi-Timeframe E2E Pipeline** - ✅ **COMPLETED** (2025-09-07)
   - ✅ Full Extraction → Decision → Trading pipeline operational
   - ✅ **Multi-Timeframe Architecture**: Extraction runs across 7 timeframes (5m, 15m, 30m, 1h, 4h, 1d, 1w)
   - ✅ **Rich Decision Context**: Decision engine receives consolidated data from all timeframes
   - ✅ **Enhanced LLM Prompts**: GPT-5 gets comprehensive market analysis across timeframes
   - ✅ GPT-5 integration with Responses API for trading decisions  
   - ✅ Real market data processing with 21 technical indicators
   - ✅ Database persistence for decisions and orchestration results
   - ✅ E2E test suite: `tests/test_full_e2e_integration.py` - validates complete pipeline
   
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
| **8000** | V2 Orchestrator (ggbot.py) | HTTP | Public | Complete V2 API server with E2E pipeline |
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

## 🎯 Multi-Timeframe Architecture (V2.1)

### **Enhanced Trading Pipeline** 
**Latest Update**: 2025-09-07 - Complete multi-timeframe implementation

#### **Configuration Structure**
```json
{
  "extraction": {
    "selected_data_sources": {
      "technical_analysis": {
        "data_points": ["RSI", "MACD", "BB", "EMA", "SMA"],
        "timeframes": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
      }
    }
  }
}
```

#### **Data Flow Architecture**
```
Configuration → Orchestrator → V2 Extraction (7 timeframes) → Market Data (7 rows)
                                         ↓
Decision Engine → Multi-timeframe Query → Consolidated Data → Rich LLM Context
                                         ↓
GPT-5 Analysis → Trading Decision → Paper Trading Execution
```

#### **Market Data Storage Pattern**
- **Separate Rows**: Each timeframe stored as individual `market_data` record
- **Config Association**: All rows linked to `config_id` for user isolation  
- **Rich Data**: V2 preprocessors provide sophisticated analysis per timeframe
- **Decision Consolidation**: Engine queries all timeframes and organizes by timeframe

#### **LLM Prompt Enhancement**
```
MARKET ANALYSIS FOR BTC/USDT
Current Price: $110,984.20
Timeframes Available: 5m, 15m, 30m, 1h, 4h, 1d, 1w

=== 5M TIMEFRAME ===
  RSI:
    Current Value: 54.2
    Trend: falling
    Zone: neutral
    
=== 1H TIMEFRAME ===
  RSI:
    Current Value: 48.7  
    Trend: sideways
    Zone: approaching_oversold
```

**Benefits Achieved**:
- ✅ Decision engine gets rich context across 7 timeframes
- ✅ LLM can analyze short-term vs long-term trends  
- ✅ User prompts can reference specific timeframes naturally
- ✅ Storage remains clean and queryable per timeframe
- ✅ Configuration is intuitive ("RSI" = all 7 timeframes)

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
pm2 logs ggbot
pm2 logs ggshot-filter

# E2E Testing
python -m tests.test_full_e2e_integration

# Resources
htop
df -h
```

---

*Last major update: V2 Architecture Phase 8 complete - Full E2E pipeline operational with GPT-5 decision engine, real market data extraction, paper trading integration (2025-09-07)*