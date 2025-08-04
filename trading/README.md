# Trading Module

**Status**: ✅ **PRODUCTION READY** - Hummingbot Integration Complete with Performance Tracking  
**Last Updated**: August 3, 2025

## Overview

The Trading Module is the execution engine of the ggbot system, responsible for converting AI trading decisions into actual trades via Hummingbot integration. **Phase 1 complete with universal paper trading, config-based instance mapping, and comprehensive performance tracking.**

### ✅ **Current Status**

- **Hummingbot Integration**: Universal paper trading for all strategies
- **ggShot Paper Trading**: Live and operational with $10k isolated account
- **Performance Tracking**: Dual-database P&L monitoring across all configurations
- **Config Management**: Template-based strategy creation with automatic paper account setup
- **API Integration**: Complete REST endpoints for dashboard and frontend integration

## 📁 **Directory Structure**

```
trading/
├── README.md                           # This file
├── api.py                             # REST API endpoints (webhooks + direct)
├── services/                          # Core trading services
│   ├── hummingbot_execution_adapter.py # Main execution engine
│   ├── market_data_service.py         # Price and market data
│   ├── instance_manager.py            # Config-to-instance mapping
│   ├── paper_trading_manager.py       # Paper account management
│   └── performance_tracker.py         # NEW: P&L and performance analytics
└── hummingbot_api.py                  # Hummingbot API integration
```

## 🚀 **Key Features**

### **1. Universal Paper Trading**
- **Config-based Isolation**: Each strategy gets isolated $10k paper account
- **Instance Mapping**: Consistent `ggbot-{user_id[:8]}-{config_id[:8]}` naming
- **Multi-Strategy Support**: Unlimited parallel strategies per user
- **Real Execution**: Uses actual Hummingbot PositionExecutor for realistic simulation

### **2. Performance Tracking System** ⭐ NEW
```python
# /trading/services/performance_tracker.py
class PerformanceTracker:
    async def get_config_performance(config_id: str) -> Dict[str, Any]
    async def get_all_active_configs(user_id: str) -> List[Dict[str, Any]]
    async def get_recent_trades(config_id: str, limit: int = 10) -> List[Dict[str, Any]]
```

**Capabilities:**
- **Dual-Database Queries**: ggBot (strategy_runs) + Hummingbot (trade_fills)
- **Real-time P&L**: Live calculation from actual trade executions
- **Win Rate Analytics**: Comprehensive trade statistics and metrics
- **Per-Config Tracking**: Isolated performance for each strategy
- **Trade History**: Detailed entry/exit analysis with confidence scores

### **3. ggShot Integration** ⭐ LIVE
- **Live Paper Trading**: ggShot signals automatically execute paper trades
- **Config ID**: `e249bb49-0455-4596-9657-09bf9e14ca14`
- **Instance**: `ggbot-00000000-e249bb49` with `ggshot_paper_account`
- **Status**: Active and processing signals → paper trades
- **Protection**: Marked as flagship (non-editable) configuration

## 🔄 **Trading Flow**

### **Standard Pipeline**
```
Decision Intent → Trading Webhook → HummingbotExecutionAdapter → Instance Mapping → Paper Trade Execution
     ↓                ↓                        ↓                      ↓                    ↓
Trade Request    LLM Normalize         Config-based Route    Hummingbot API        P&L Tracking
```

### **ggShot Pipeline** (Live)
```
ggShot Signal → Decision (action="long"/"short") → Trading Webhook → ggShot Paper Account → Performance Data
     ↓                    ↓                              ↓                    ↓                    ↓
Telegram Msg      Dynamic Action Extract        Config Routing        $10k Isolated        Real P&L
```

## 📊 **API Endpoints**

### **Core Trading**
```bash
# Execute trade (webhook format)
POST /trading/webhooks/execute-trade
{
  "intent": {
    "action": "long",
    "symbol": "BTC/USDT", 
    "confidence": 0.75,
    "user_id": "uuid",
    "config_id": "uuid"
  }
}

# Direct trade execution
POST /trading/execute-trade
{
  "action": "long",
  "symbol": "BTC/USDT",
  "confidence": 0.75
}
```

### **Performance Tracking** ⭐ NEW
```bash
# Get all strategies for user
GET /dashboard/api/dashboard/strategies/{user_id}

# Get detailed performance for strategy
GET /dashboard/api/dashboard/performance/{config_id}

# Get recent trades
GET /dashboard/api/dashboard/trades/{config_id}
```

## 🔧 **Configuration Management**

### **Instance Mapping**
Each configuration automatically gets:
- **Unique Instance**: `ggbot-{user_id[:8]}-{config_id[:8]}`
- **Paper Account**: `paper_{config_type}_{config_id[:8]}`
- **Initial Balance**: $10,000 USDT
- **Database Entry**: `config_instances` table mapping

### **ggShot Configuration**
```sql
-- ggShot config_instances entry
INSERT INTO config_instances (
  config_id, instance_name, hummingbot_account, status, paper_balance_usd
) VALUES (
  'e249bb49-0455-4596-9657-09bf9e14ca14',
  'ggbot-00000000-e249bb49', 
  'ggshot_paper_account',
  'active',
  10000.00
);
```

## 🧪 **Testing & Verification**

### **Test ggShot Performance**
```bash
# Check ggShot paper account status
curl http://localhost:8000/dashboard/api/dashboard/performance/e249bb49-0455-4596-9657-09bf9e14ca14

# Expected response:
{
  "config_id": "e249bb49-0455-4596-9657-09bf9e14ca14",
  "account_balance": 10000.0,
  "total_pnl": 0.0,  # Will update when trades execute
  "trade_count": 0,  # Will increment with each trade
  "win_rate": 0.0,
  "active_positions": 0
}
```

### **Test Instance Mapping**
```bash
source .venv/bin/activate
python -c "
from trading.services.instance_manager import HummingbotInstanceManager
import asyncio

async def test():
    manager = HummingbotInstanceManager()
    mapping = await manager.ensure_mapping(
        '00000000-0000-0000-0000-000000000001',
        'e249bb49-0455-4596-9657-09bf9e14ca14'
    )
    print('ggShot mapping:', mapping)

asyncio.run(test())
"
```

### **Test Performance Tracker**
```bash
python -c "
from trading.services.performance_tracker import get_performance_tracker
import asyncio

async def test():
    tracker = get_performance_tracker()
    performance = await tracker.get_config_performance('e249bb49-0455-4596-9657-09bf9e14ca14')
    print('P&L:', performance['total_pnl'])
    print('Trades:', performance['trade_count'])

asyncio.run(test())
"
```

## 📈 **Performance Metrics**

The PerformanceTracker provides comprehensive analytics:

### **Basic Metrics**
- **Total P&L**: Dollar amount and percentage
- **Trade Count**: Total executed trades
- **Win Rate**: Percentage of profitable trades
- **Account Balance**: Current paper account balance

### **Advanced Analytics**
- **Largest Win/Loss**: Best and worst trade performance
- **Average Win/Loss**: Mean profit/loss per trade type
- **Active Positions**: Currently open trades
- **Last Trade Time**: Most recent trading activity

### **Data Sources**
- **Primary**: `strategy_runs` table (ggBot database)
- **Enhancement**: `trade_fills` table (Hummingbot database)
- **Real-time**: Live Hummingbot API queries

## 🔄 **Trade Lifecycle**

### **1. Signal Reception**
- ggShot signals arrive via Telegram
- Decision module processes with 4-Pillar validation
- Generates actionable intent (`long`/`short` vs `validate`)

### **2. Trade Execution**
- Trading webhook receives intent
- HummingbotExecutionAdapter normalizes signal
- Instance mapping routes to correct paper account
- Hummingbot PositionExecutor handles actual execution

### **3. Performance Tracking**
- Strategy_runs table logs all decisions
- PerformanceTracker calculates P&L from trade entries/exits
- Dashboard APIs serve real-time performance data
- WebSocket updates push live changes to frontend

## 🛡️ **Risk Management**

### **Paper Trading Safety**
- **No Real Money**: All trading is paper simulation
- **Account Isolation**: Each config has separate $10k account
- **Position Limits**: Configurable per-strategy limits
- **Stop Loss/Take Profit**: Automatic TP/SL management via Hummingbot

### **ggShot Protection**
- **Flagship Status**: Cannot be edited or deleted
- **Config Protection**: Marked as non-editable in permissions
- **Instance Isolation**: Dedicated paper account for ggShot only

## 🚀 **Integration Points**

### **With Decision Module**
- Receives trade intents via `/webhooks/execute-trade`
- Processes confidence-based position sizing
- Supports all decision modes (NEW_TRADE, MANAGE_TRADE, signal_validation)

### **With Hummingbot**
- Direct API integration (port 15888)
- PositionExecutor for trade management
- Real-time P&L tracking
- Paper trading account management

### **With Dashboard**
- Performance data via REST APIs
- Real-time updates via WebSocket
- Multi-strategy portfolio view
- Trade history and analytics

## 📋 **Future Enhancements**

### **Phase 2: Live Trading**
- Real money execution (beyond paper trading)
- Enhanced risk controls and position sizing
- Multi-exchange support expansion

### **Phase 3: Advanced Features**
- Portfolio-level risk management
- Advanced order types (TWAP, iceberg, OCO)
- Real-time strategy optimization
- Machine learning position sizing

---

## 🎯 **Current Live Status**

**ggShot Paper Trading**: ✅ **ACTIVE**
- Processing live Telegram signals
- Executing paper trades automatically  
- Tracking real P&L performance
- Ready for demo with actual trading data

**Performance Dashboard**: ✅ **OPERATIONAL**
- Real-time P&L tracking across all configurations
- Multi-strategy portfolio management
- Template-based strategy creation
- Complete API integration for frontend

The Trading Module is production-ready and actively managing paper trades from live ggShot signals!