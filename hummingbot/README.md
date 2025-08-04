# Hummingbot Integration for ggBot

**Status**: ✅ **PHASE 1 COMPLETE** - Universal Paper Trading Ready  
**Last Updated**: August 3, 2025

## Overview
Complete Hummingbot integration providing universal paper trading for all ggBot strategies. **HUM_INTEGRATION Phase 1 complete with config-based instance mapping, isolated paper accounts, and end-to-end testing.**

### ✅ **PHASE 1 COMPLETE** (2025-08-03)
- **Critical Fixes**: Import paths and random instance creation resolved
- **Config Mapping**: Each config_id maps to persistent Hummingbot instance
- **Account Isolation**: $10k paper trading accounts per configuration
- **Universal Support**: Works with ggShot signals, manual trades, API calls, future strategies
- **Integration Tests**: All tests passing (3/3 success rate)

## 📁 **Directory Structure**

```
hummingbot/
├── README.md               # This file (updated)
├── docker-compose.yml      # Main deployment config (port 15888:8000)
├── api/                    # Official hummingbot-api server (moved from root)
│   ├── docker-compose.yml  # API server deployment (EMQX + PostgreSQL)
│   ├── bots/               # Bot configurations and instances
│   ├── services/           # Core API services
│   ├── models/             # Data models
│   ├── routers/            # API endpoints
│   └── main.py             # API server entry point
├── client/                 # Generated API client library (moved from root)
│   └── hummingbot_api_client/  # Python client for API integration
├── hummingbot_data/        # Bot configurations and logs
├── hummingbot_conf/        # Configuration templates
└── hummingbot_logs/        # Runtime logs
```

## 🎯 **Current Status**

### Infrastructure ✅
- **Hummingbot API**: Running on port **15888** via official setup (hummingbot/api/)
- **EMQX Broker**: Message bus for real-time communication (7 ports: 1883,8081,8083,8084,8883,18083,61613)
- **PostgreSQL**: Dedicated trading database (localhost:5434)
- **Docker Setup**: Full containerized deployment ready
- **API Client**: Generated client library organized in hummingbot/client/
- **Port Consistency**: All services standardized to port 15888

### Integration Services ✅
1. **InstanceManager** (`/trading/services/instance_manager.py`) **NEW**
   - Config-based instance mapping: `ggbot-{user_id[:8]}-{config_id[:8]}`
   - Persistent instance names (no more random creation)
   - Database-backed mapping with config_instances table
   - **Ready**: For all strategy types

2. **PaperTradingManager** (`/trading/services/paper_trading_manager.py`) **NEW**
   - Isolated $10k paper accounts per config_id
   - Account initialization and reset capabilities
   - Performance tracking per configuration
   - **Ready**: For strategy testing and isolation

3. **HummingbotExecutionAdapter** (`/trading/services/hummingbot_execution_adapter.py`) **ENHANCED**
   - LLM normalization with DeepSeek Reasoner
   - Config-based instance mapping integration
   - Paper trading account management
   - **Universal**: Works with any trade intent format

4. **Trading API** (`/trading/api.py`) **ENHANCED**
   - Fixed import paths for hummingbot client
   - Same endpoints as legacy (`/webhooks/execute-trade`)
   - Multi-config routing support
   - **Ready**: For all ggBot strategies (ggShot, manual, API, future)

## 🚀 **Quick Reference**

```bash
# Start main services (port 15888)
cd /home/sev/ggbot/hummingbot
sg docker -c "docker-compose up -d"

# Start API server services (EMQX + PostgreSQL)
cd /home/sev/ggbot/hummingbot/api
sg docker -c "docker-compose up -d"

# Check service status
sg docker -c "docker-compose ps"

# Check logs
sg docker -c "docker-compose logs -f hummingbot-api"  # Main service
cd api && sg docker -c "docker-compose logs -f hummingbot-api"  # API server

# Test API health (port 15888)
curl -u admin:admin http://localhost:15888/

# Test market data integration
source /home/sev/ggbot/.venv/bin/activate
python -c "
import asyncio
import os
os.environ['HUMMINGBOT_API_HOST'] = 'http://localhost:15888'
from trading.services.market_data_service import MarketDataService
async def test(): 
    service = MarketDataService()
    prices = await service.get_current_prices(['BTCUSDT'])
    print(f'BTC Price: {prices}')
asyncio.run(test())
"

# Stop services
sg docker -c "docker-compose down"
```

## 📝 **Key Files**

- `docker-compose.yml` - Main service configuration (port 15888:8000)
- `api/docker-compose.yml` - API server configuration (EMQX + PostgreSQL)
- `api/.env` - API server environment variables
- `client/` - Generated API client library for integration
- `hummingbot_data/` - Persistent data (configs, logs, credentials)
- `/trading/services/market_data_service.py` - Market data integration (updated for port 15888)
- `/trading/services/hummingbot_execution_adapter.py` - Trade execution (updated for port 15888)
- `/trading/api.py` - New trading API (replaces legacy, same endpoints)

## 🏗️ **Architecture Flow**

```
Any Trade Intent → Trading Module → Config-Based Instance Mapping
     ↓                    ↓                    ↓
  ggShot Signal    →  InstanceManager  →  ggbot-user123-conf456
  Manual Trade     →  LLM Normalize   →  $10k Paper Account
  API Call         →  Position Size   →  Isolated Execution
  Future Strategy  →  Deploy Trade    →  Performance Tracking
                                        ↓
            Hummingbot API (port 15888) → PositionExecutor
                                        ↓
                        Real-time TP/SL Management (Paper Trading)
```

### **Universal Trade Support**
- **Input**: Any signal format (ggShot text, JSON, API calls)
- **Processing**: LLM normalization + config-based routing
- **Output**: Isolated paper trading per configuration
- **Result**: Universal paper trading for all ggBot strategies

## 🔧 **Integration Points**

### Core Features
- **Paper Trading**: Full simulation environment without real money
- **Multi-Exchange**: Support for 50+ crypto exchanges via CCXT
- **Real-time Data**: Live market data and order book streaming via EMQX
- **Strategy Framework**: Advanced algorithmic trading strategies
- **Risk Management**: Built-in position sizing and stop-loss controls
- **API-First**: Complete REST API with generated Python client

### Technical Integration
- **REST API**: All trading operations via HTTP endpoints (port 15888)
- **WebSocket**: Real-time updates via EMQX message broker (7 ports)
- **Database**: Dedicated PostgreSQL for trade history (port 5434)
- **Python Client**: Generated client library in `hummingbot/client/`
- **Monitoring**: Comprehensive logging and error tracking

### Architecture
- **API-First Design**: Modern microservices architecture (hummingbot/api/)
- **Message Broker**: EMQX for real-time communication (7 ports)
- **Containerized**: Docker deployment for easy scaling
- **Database Integration**: Dedicated PostgreSQL for persistent storage (port 5434)
- **Generated Client**: Python API client library (hummingbot/client/)
- **Port Standardization**: Consistent use of port 15888 across all services

## 🐛 **Troubleshooting**

### Common Issues
1. **Service Communication Errors**: Ensure `HUMMINGBOT_API_HOST` points to `http://localhost:15888`
2. **Database Connection**: Check PostgreSQL is running on port 5434
3. **Docker Issues**: Verify Docker service is running and accessible
4. **Port Conflicts**: Ensure port 15888, 5434, and EMQX ports (1883,8081,8083,8084,8883,18083,61613) are available
5. **Import Errors**: Python path includes `hummingbot/client/` for API client imports

### Verification Commands
```bash
# Check container health
sg docker -c "docker-compose ps"

# Test API response (port 15888)
curl -u admin:admin http://localhost:15888/

# Verify API client imports
python -c "
import sys
sys.path.append('/home/sev/ggbot/hummingbot/client')
from hummingbot_api_client import Client
print('✅ API client import successful')
"

# Check environment variables
echo $HUMMINGBOT_API_HOST
```

## 📋 **Next Steps**

### ✅ **Phase 1: COMPLETE** (Universal Paper Trading Ready)
- ✅ Config-based instance mapping implemented
- ✅ Isolated paper trading accounts per configuration  
- ✅ Universal trade intent support (ggShot, manual, API, future strategies)
- ✅ All integration tests passing (3/3 success rate)
- ✅ **ggShot paper trading LIVE and operational**

### ✅ **Phase 2: COMPLETE** (Performance Tracking Live)
- ✅ Performance tracking with dual-database queries (PerformanceTracker service)
- ✅ Dashboard API integration for frontend
- ✅ Real-time P&L monitoring and trade analytics
- ✅ ggShot flagship configuration protection

### Phase 3: Production Features (Future)
- Multi-user scaling and isolation
- Live trading capabilities (beyond paper trading)
- Advanced risk management
- Strategy deployment automation

---

## 🎯 **Live ggShot Configuration**

### **Current Status**: ✅ **OPERATIONAL**
- **Config ID**: `e249bb49-0455-4596-9657-09bf9e14ca14`
- **Instance Name**: `ggbot-00000000-e249bb49`
- **Paper Account**: `ggshot_paper_account`
- **Balance**: $10,000 USDT (isolated)
- **Status**: Actively processing live Telegram signals

### **Database Mapping**
```sql
-- config_instances entry for ggShot
config_id: e249bb49-0455-4596-9657-09bf9e14ca14
instance_name: ggbot-00000000-e249bb49
hummingbot_account: ggshot_paper_account
status: active
paper_balance_usd: 10000.00
```

### **Verification Commands**
```bash
# Check ggShot paper account balance
curl -u admin:admin http://localhost:15888/paper-trade/balance/ggshot_paper_account

# Monitor ggShot trades in Hummingbot logs
sg docker -c "docker-compose logs -f hummingbot-api" | grep ggbot-00000000-e249bb49

# Check performance tracking
curl http://localhost:8000/dashboard/api/dashboard/performance/e249bb49-0455-4596-9657-09bf9e14ca14
```

---

**Note**: HUM_INTEGRATION Phases 1-2 completed August 3, 2025. ggShot paper trading is live and operational with real performance tracking.