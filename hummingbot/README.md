# Hummingbot Integration for ggBot

## Overview
Hummingbot integration to replace CCXT MCP server with a more robust trading infrastructure. **Infrastructure deployment complete using official hummingbot-api setup with proper EMQX message broker architecture.**

## Current Status

### ✅ COMPLETED (Phase 1) - INFRASTRUCTURE DEPLOYED
1. **Official Hummingbot Infrastructure** ✅
   - **Hummingbot API**: Running on port 8000 via official setup (hummingbot-api:latest)
   - **EMQX Message Broker**: Full real-time communication stack (7 ports: 1883,8081,8083,8084,8883,18083,61613)
   - **PostgreSQL**: Dedicated trading database on port 5434 with persistent volumes
   - **Authentication**: admin/admin configured via official setup script
   - **Architecture**: Official docker-compose.yml with proper service networking

2. **Python API Client** ✅
   - Generated from OpenAPI spec
   - Installed as `hummingbot_api_client`
   - Basic auth headers working
   - **VERIFIED**: End-to-end API connectivity confirmed

3. **MarketDataService** ✅
   - Location: `/trading/services/market_data_service.py`
   - Supports top 20 ggShot pairs
   - Methods: `get_current_prices()`, `get_order_book()`, `get_candles()`
   - Uses `binance_perpetual_testnet` connector
   - **FIXED**: Dynamic API URL resolution via environment variables
   - **TESTED**: Successfully retrieving live price data (BTC: $115,900)

4. **HummingbotExecutionAdapter** ✅
   - Location: `/trading/services/hummingbot_execution_adapter.py`
   - LLM normalization with DeepSeek Reasoner
   - Uses existing `DECISION_LLM_API_KEY`
   - Balance-based position sizing (queries portfolio API)
   - Risk levels: High confidence 5%, Medium 3%, Low 2%, Very low 1%
   - Paper trading default: $10,000 USDT balance
   - **FIXED**: Service communication for containerized deployments

5. **New Trading API** ✅
   - Location: `/trading/api.py`
   - Same endpoints as legacy (`/webhooks/execute-trade`)
   - Clean break: `trading/` → `trading-legacy/`
   - Multi-config routing (no hardcoded config_id)
   - Full compatibility with Decision Module
   - **READY**: For ggShot signal integration testing

6. **Environment Configuration** ✅
   - **FIXED**: Proper environment variable management
   - **CONFIGURED**: `HUMMINGBOT_API_HOST` for service name resolution
   - **SUPPORTS**: Both development (localhost) and production (service names) deployments

### 🎯 READY FOR PRODUCTION
**All Phase 1 objectives completed and tested. System is ready for ggShot signal integration.**

### 📋 NEXT PHASES
**Phase 2: Scale to Full Universe**
- Expand to full 140+ ggShot symbol mappings
- Enhanced Monitoring Service integration (5-minute strategic polling)
- Multi-user database schema updates
- Performance testing with concurrent users

**Phase 3: Advanced Features**
- Position Executors for sophisticated trade management
- Multiple take-profit levels and trailing stops
- Strategic trade management pipeline
- Live trading preparation

## Quick Reference

```bash
# Start services
cd /home/sev/ggbot/hummingbot
sg docker -c "docker-compose up -d"

# Check service status
sg docker -c "docker-compose ps"

# Check logs
sg docker -c "docker-compose logs -f hummingbot-api"

# Test API health
curl -u admin:admin http://localhost:8088/

# Test market data (should return live BTC price)
source /home/sev/ggbot/.venv/bin/activate
python -c "
import asyncio
import os
os.environ['HUMMINGBOT_API_HOST'] = 'http://localhost:8088'
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

## Key Files
- `docker-compose.yml` - Service configuration (pinned to `hummingbot-api:1.0.1`)
- `.env` - Environment variables (`HUMMINGBOT_API_HOST=http://hummingbot-api:8000`)
- `/trading/services/market_data_service.py` - Market data integration with dynamic URL resolution
- `/trading/services/hummingbot_execution_adapter.py` - LLM normalization & execution with fixed networking
- `/trading/api.py` - New trading API (replaces legacy, same endpoints)
- `/hummingbot_client/` - Generated Python API client
- `/hummingbot_data/` - Persistent volume mount for Hummingbot configuration

## Architecture Flow
```
ggShot Signal → Decision Module → /webhooks/execute-trade
                                        ↓
                            HummingbotExecutionAdapter
                                        ↓
                    LLM Normalization (DeepSeek Reasoner)
                                        ↓  
                    Balance-Based Position Sizing (1-5%)
                                        ↓
            Hummingbot API (service communication) → PositionExecutor
                                        ↓
                        Real-time TP/SL Management (Paper Trading)
```

## Environment Configuration
- **API Access**: `http://localhost:8000` (official Hummingbot API)
- **Authentication**: Basic auth (admin/admin) 
- **Message Broker**: EMQX on multiple ports for real-time communication
- **Database**: PostgreSQL on localhost:5434 for trading data
- **Paper Trading**: Ready for binance_paper_trade connector
- **Integration**: HUMMINGBOT_API_HOST environment variable configured

## Docker Network Details
- **Network**: `hummingbot_ggbot-network` (bridge driver)
- **Subnet**: `172.18.0.0/16`
- **Services**:
  - `hummingbot-backend-api`: `172.18.0.3` (port 8000 → 8088)
  - `hummingbot-postgres`: `172.18.0.2` (port 5432 → 5433)

## Troubleshooting

### Common Issues
1. **Service Communication Errors**: Ensure `HUMMINGBOT_API_HOST` is set correctly in environment
2. **Container Startup Issues**: Check logs with `sg docker -c "docker-compose logs"`
3. **API Not Responding**: Wait 15-20 seconds after startup for initialization
4. **Version Conflicts**: Ensure using pinned version `1.0.1` in docker-compose.yml

### Verification Commands
```bash
# Check container health
sg docker -c "docker-compose ps"

# Test API response
curl -u admin:admin http://localhost:8088/

# Verify networking
sg docker -c "docker network inspect hummingbot_ggbot-network"

# Check environment variables
cat .env | grep HUMMINGBOT
```