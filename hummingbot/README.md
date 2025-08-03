# Hummingbot Integration for ggBot

**Status**: ✅ **COMPLETE** - Ready for Production Use  
**Last Updated**: August 3, 2025

## Overview
Hummingbot integration to replace CCXT MCP server with a more robust trading infrastructure. **Infrastructure deployment complete with reorganized directory structure and standardized port configuration.**

### ✅ **REORGANIZATION COMPLETE** (2025-08-03)
- **Directory Structure**: Reorganized from root-level directories to clean hummingbot/ organization
- **Port Standardization**: All services now use port **15888** (per ACTIVE.md specifications)
- **API Client Integration**: Generated client library properly organized and integrated

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
1. **MarketDataService** (`/trading/services/market_data_service.py`)
   - Supports top 20 ggShot pairs
   - Methods: `get_current_prices()`, `get_order_book()`, `get_candles()`
   - Uses `binance_perpetual_testnet` connector
   - **Updated**: Default API URL points to `localhost:15888`

2. **HummingbotExecutionAdapter** (`/trading/services/hummingbot_execution_adapter.py`)
   - LLM normalization with DeepSeek Reasoner
   - Balance-based position sizing (1-5% risk levels)
   - Paper trading with $10,000 USDT balance
   - **Updated**: Default API URL points to `localhost:15888`

3. **Trading API** (`/trading/api.py`)
   - Same endpoints as legacy (`/webhooks/execute-trade`)
   - Multi-config routing support
   - Full compatibility with Decision Module
   - **Ready**: For ggShot signal integration

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
ggShot Signal → Decision Module → /webhooks/execute-trade
                                        ↓
                            HummingbotExecutionAdapter
                                        ↓
                    LLM Normalization (DeepSeek Reasoner)
                                        ↓  
                    Balance-Based Position Sizing (1-5%)
                                        ↓
            Hummingbot API (port 15888) → PositionExecutor
                                        ↓
                        Real-time TP/SL Management (Paper Trading)
```

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

### Phase 2: Scale to Full Universe
- Expand to full 140+ ggShot symbol mappings
- Enhanced monitoring service integration
- Multi-user database schema updates
- Performance testing with concurrent users

### Phase 3: Advanced Features
- Position Executors for sophisticated trade management
- Multiple take-profit levels and trailing stops
- Strategic trade management pipeline
- Live trading preparation

---

**Note**: Directory reorganization completed August 3, 2025. All services now use consistent port 15888 configuration as specified in ACTIVE.md.