# Core Module

**Status**: ✅ **PRODUCTION READY** - Infrastructure APIs and Services Complete  
**Last Updated**: August 3, 2025

## Overview

The Core Module provides the foundational infrastructure for the ggbots platform, including configuration management, dashboard APIs, monitoring services, and shared utilities. **Phase 1 complete with Config API, Performance Tracking, and Dashboard integration.**

### ✅ **Current Status**

- **Config API**: Template-based strategy creation with automatic paper trading setup
- **Dashboard API**: Performance tracking and real-time monitoring endpoints
- **Performance Tracking**: Dual-database P&L analytics across all configurations
- **Agent Control**: Service management and health monitoring
- **Database Integration**: Universal trade lifecycle and multi-user support

## 📁 **Directory Structure**

```
core/
├── README.md                          # This file
├── api/                              # REST API endpoints and services
│   ├── config_api.py                 # NEW: Strategy configuration management
│   └── agent_control_api.py          # Bot control and service management
├── common/                           # Shared utilities and services
│   ├── config.py                     # Environment and configuration management
│   ├── db.py                         # Database connection and utilities
│   └── logger.py                     # Structured logging with context binding
├── config/                           # Configuration templates and management
│   └── config_main.py                # Configuration loading and validation
├── mcp/                              # MCP (Model Context Protocol) servers
│   └── servers/                      # External tool integration servers
└── scheduling/                       # Background task scheduling
    └── scheduler.py                  # APScheduler integration for automated tasks
```

## 🚀 **Key Features**

### **1. Configuration Management API** ⭐ NEW
```python
# /core/api/config_api.py
@app.post("/api/configs/create-from-template")
@app.put("/api/configs/{config_id}")
@app.get("/api/configs/{config_id}/permissions")
@app.get("/api/configs/user/{user_id}")
@app.delete("/api/configs/{config_id}")
```

**Template-Based Strategy Creation:**
- **RSI Momentum**: Oversold/overbought trading with RSI confirmation
- **MACD Trend Following**: Crossover-based trend entries
- **Manual Trading**: High-confidence manual signal execution
- **Momentum Breakout**: Volume-based breakout trading
- **Bollinger Bands**: Mean reversion from statistical extremes

**Auto-Configuration:**
- Automatic `config_instances` entry creation
- $10k paper trading account initialization
- Risk parameter adjustment by risk level (low/medium/high)
- Template-specific indicator selection

### **2. Bot Control API** ⭐ NEW
```python
# /core/api/agent_control_api.py  
@app.get("/api/bots")                               # List all bot configurations
@app.post("/api/bots/{config_id}/start")            # Start/activate a bot
@app.post("/api/bots/{config_id}/stop")             # Stop/deactivate a bot
@app.get("/api/bots/{config_id}/status")            # Get detailed bot status
```

**Bot Management Features:**
- **Config-Based Control**: Start/stop bots by configuration ID
- **Real-Time Status**: Live bot activity and pipeline monitoring
- **Universal Support**: Works with all bot types (ggshot, demo, etc.)
- **Production Ready**: Integrated with existing PM2 services

### **3. Permissions System** ⭐ NEW
**Flagship Protection:**
- ggShot configuration marked as `is_flagship: True`
- Non-editable and non-deletable protection
- Template-created strategies fully editable
- Permission checking before all modification operations

## 📊 **API Reference**

### **Configuration Management**

#### Create Strategy from Template
```bash
POST /api/configs/create-from-template
{
  "template": "rsi",
  "symbol": "BTC/USDT", 
  "risk_level": "medium",
  "user_id": "uuid",
  "config_name": "My RSI Bot"
}

# Response:
{
  "config_id": "uuid",
  "config_name": "My RSI Bot",
  "config_type": "rsi_momentum",
  "editable": true,
  "is_flagship": false,
  "instance_name": "ggbot-user123-conf456",
  "paper_balance": 10000.0
}
```

#### Check Configuration Permissions
```bash
GET /api/configs/{config_id}/permissions

# ggShot flagship response:
{
  "editable": false,
  "is_flagship": true,
  "config_type": "ggshot",
  "owner_id": "00000000-0000-0000-0000-000000000001"
}

# User-created strategy response:
{
  "editable": true,
  "is_flagship": false,
  "config_type": "rsi_momentum", 
  "owner_id": "uuid"
}
```

### **Performance Analytics**

#### Get All User Strategies
```bash
GET /dashboard/api/dashboard/strategies/{user_id}

# Response: Array of strategy summaries
[
  {
    "config_id": "e249bb49-0455-4596-9657-09bf9e14ca14",
    "config_name": "ggShot MVP Configuration",
    "config_type": "ggshot",
    "status": "active",
    "account_balance": 10000.0,
    "total_pnl": 247.50,
    "total_pnl_pct": 2.48,
    "trade_count": 5,
    "win_rate": 80.0,
    "active_positions": 1
  }
]
```

#### Get Detailed Performance
```bash
GET /dashboard/api/dashboard/performance/{config_id}

# Response: Comprehensive performance metrics
{
  "config_id": "e249bb49-0455-4596-9657-09bf9e14ca14",
  "total_pnl": 247.50,
  "total_pnl_pct": 2.48,
  "trade_count": 5,
  "win_count": 4,
  "loss_count": 1,
  "win_rate": 80.0,
  "account_balance": 10247.50,
  "largest_win": 150.00,
  "largest_loss": -25.00,
  "avg_win": 93.13,
  "avg_loss": -25.00,
  "last_trade_time": "2025-08-03T18:45:00Z",
  "active_positions": 1,
  "trades": [...]
}
```

## 🔧 **Strategy Templates**

### **Template Configuration Structure**
Each template includes:
- **Strategy Description**: Natural language trading approach
- **Risk Guidelines**: Position sizing, leverage, stop loss rules
- **Additional Context**: Market conditions, best practices
- **Indicator Selection**: Relevant technical indicators
- **Risk Scaling**: Multipliers based on risk level selection

### **Available Templates**

#### **RSI Momentum Strategy**
```python
{
  "strategy": "Trade based on RSI oversold/overbought conditions. Enter long when RSI < 30 and showing reversal signs, enter short when RSI > 70 with bearish divergence.",
  "risk_guidelines": "Max position size 5% of capital. Max leverage 3x. Stop loss at 2% per trade.",
  "indicators": ["RSI_15m", "RSI_1h", "BollingerBands_1h", "ATR_1h", "VWAP_1h"]
}
```

#### **MACD Trend Following**
```python
{
  "strategy": "Follow MACD crossovers for trend entries. Enter long on MACD line crossing above signal line with positive histogram.",
  "risk_guidelines": "Max position size 4% of capital. Max leverage 5x. Trailing stop loss at 3%.",
  "indicators": ["MACD_1h", "RSI_1h", "BollingerBands_1h", "ATR_1h", "VWAP_1h"]
}
```

#### **Manual Trading Bot**
```python
{
  "strategy": "Execute trades based on manual analysis and external signals. Wait for high-confidence setups with clear risk/reward ratios.",
  "risk_guidelines": "Max position size 3% of capital. Max leverage 2x. Fixed stop loss at 1.5%.",
  "indicators": ["RSI_15m", "RSI_1h", "BollingerBands_1h", "ATR_1h", "VWAP_1h"]
}
```

## 🧪 **Testing & Verification**

### **Test Config API**
```bash
# Create RSI strategy from template
curl -X POST http://localhost:8000/api/configs/create-from-template \
  -H "Content-Type: application/json" \
  -d '{
    "template": "rsi",
    "symbol": "BTC/USDT",
    "risk_level": "medium",
    "user_id": "00000000-0000-0000-0000-000000000001"
  }'

# Check ggShot permissions (should be non-editable)
curl http://localhost:8000/api/configs/e249bb49-0455-4596-9657-09bf9e14ca14/permissions

# List all user strategies
curl http://localhost:8000/api/configs/user/00000000-0000-0000-0000-000000000001
```

### **Test Dashboard API**
```bash
# Get all strategies with performance
curl http://localhost:8000/dashboard/api/dashboard/strategies/00000000-0000-0000-0000-000000000001

# Get ggShot detailed performance
curl http://localhost:8000/dashboard/api/dashboard/performance/e249bb49-0455-4596-9657-09bf9e14ca14

# Get recent trades
curl http://localhost:8000/dashboard/api/dashboard/trades/e249bb49-0455-4596-9657-09bf9e14ca14
```

### **Test Paper Trading Integration**
```bash
# Create strategy and verify paper account setup
source .venv/bin/activate
python -c "
import asyncio
from trading.services.performance_tracker import get_performance_tracker

async def test():
    tracker = get_performance_tracker()
    configs = await tracker.get_all_active_configs('00000000-0000-0000-0000-000000000001')
    
    for config in configs:
        print(f'{config[\"config_name\"]}: ${config[\"account_balance\"]} balance')
        if config['config_type'] == 'ggshot':
            print('  ✅ ggShot flagship - live paper trading')
        else:
            print(f'  📊 {config[\"config_type\"]} - ready for trading')

asyncio.run(test())
"
```

## 🔄 **Integration Architecture**

### **Config API Flow**
```
Template Selection → Config Creation → Instance Mapping → Paper Account Setup → Dashboard Integration
       ↓                   ↓                ↓                    ↓                    ↓
   Template Data    config_instances   Hummingbot API    Paper Trading      Performance APIs
```

### **Dashboard API Flow**
```
Frontend Request → Performance Tracker → Dual Database Query → Real-time Calculation → JSON Response
       ↓                    ↓                    ↓                    ↓                    ↓
   Strategy List    ggBot + Hummingbot    Trade History     P&L Analytics     Live Updates
```

### **Permission System Flow**
```
API Request → Permission Check → Flagship Detection → Allow/Deny → Action Execution
     ↓              ↓                  ↓                ↓              ↓
Edit Request   Check config_type   ggshot = readonly   403 Error   Success/Fail
```

## 🛡️ **Security & Permissions**

### **Flagship Protection**
- **ggShot Configuration**: Protected from edits/deletion
- **Config Type Check**: `config_type IN ['ggshot', 'ggshot_production']`
- **API Enforcement**: All modification endpoints check permissions
- **Frontend Integration**: Permission flags control UI edit controls

### **User Isolation**
- **Multi-User Support**: All configs filtered by `user_id`
- **Account Separation**: Each config gets isolated paper trading account
- **Performance Isolation**: P&L tracking per configuration
- **Resource Limits**: Configurable limits per user/strategy

## 📈 **Live Status (August 2025)**

### **ggShot Integration**: ✅ **OPERATIONAL**
- Config ID: `e249bb49-0455-4596-9657-09bf9e14ca14`
- Flagship status: Protected from modifications
- Paper trading: Live with real P&L tracking
- Performance API: Serving real trading data

### **Template System**: ✅ **READY**
- 5 strategy templates available
- Automatic paper account initialization
- Risk level scaling (low/medium/high)
- Full lifecycle from creation to performance tracking

### **Dashboard Integration**: ✅ **ACTIVE**
- Real-time performance APIs
- Multi-strategy portfolio view
- WebSocket live updates
- Dual-database P&L calculation

## 🚀 **Future Enhancements**

### **Phase 2 Features**
- Advanced template customization
- Template sharing between users
- Strategy performance comparison
- Portfolio-level risk management

### **Phase 3 Features**
- Live trading capabilities (beyond paper)
- Advanced order types and execution
- Real-time strategy optimization
- Machine learning position sizing

---

## 🎯 **Production Ready**

The Core Module provides enterprise-grade infrastructure for:
- **Multi-strategy management** with template-based creation
- **Real-time performance tracking** with dual-database integration
- **Secure configuration management** with flagship protection
- **Scalable API architecture** ready for frontend integration

All systems operational and serving live ggShot paper trading with real performance data!