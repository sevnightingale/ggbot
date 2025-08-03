# GGBot API Documentation

This document provides a comprehensive overview of all API endpoints in the GGBot system.

## Running the Combined API Server (Recommended for Prototype)

For simplified deployment, all APIs can be run as a single service:

```bash
# Method 1: Direct Python
cd /home/sev/ggbot
source .venv/bin/activate
python main_api.py

# Method 2: Using uvicorn
uvicorn main_api:app --host 0.0.0.0 --port 8000 --reload

# Method 3: With custom settings
export API_HOST=0.0.0.0
export API_PORT=8000
python main_api.py
```

**Combined API URLs:**
- Main docs: http://localhost:8000/docs
- Extraction: http://localhost:8000/extraction/...
- Decision: http://localhost:8000/decision/...
- Trading: http://localhost:8000/trading/...
- Dashboard: http://localhost:8000/dashboard/...
- Agent Control: http://localhost:8000/agent/...

## Running Individual Services (For Development/Production)

Alternatively, each service can be run independently on different ports:

## Trading Module API

Base URL: `http://localhost:5000` (configurable via `TRADING_API_PORT`)

### Authentication
Currently using mock authentication with `DEFAULT_USER_ID` for testing. Production will use JWT tokens.

### Endpoints

#### 1. Health Check
```
GET /health
```

Check if the Trading API service is running and healthy.

**Response:**
```json
{
  "status": "healthy",
  "service": "trading-api",
  "timestamp": "2024-01-10T12:00:00Z",
  "engines_active": 1
}
```

---

#### 2. Execute Trade
```
POST /trade/execute
```

Execute a trading intent from the Decision Module. This endpoint accepts semi-structured input that is interpreted by an LLM.

**Request Body:**
```json
{
  "decision_id": "550e8400-e29b-41d4-a716-446655440000",
  "action": "enter_long",              // Can be: "enter_long", "go long", "buy", etc.
  "symbol": "BTC/USD",                 // Can be: "BTC/USD", "Bitcoin", etc.
  "exchange": "bitmex",                // Optional, defaults to configured exchange
  "timeframe": "15m",                  // Optional
  "collateral_amount": 1000,           // Optional, in USD
  "leverage": 10,                      // Optional
  "stop_loss_price": 100000,          // Optional
  "take_profit_price": 120000,        // Optional
  "confidence": 0.85,                  // Optional, 0-1 scale
  "reasoning": "Strong bullish signals" // Optional
}
```

**Response (Success):**
```json
{
  "status": "success",
  "trade_id": "123e4567-e89b-12d3-a456-426614174000",
  "data": {
    "order_id": "order_12345",
    "filled_amount": 1000,
    "average_price": 110000
  },
  "details": {
    "tool_calls": [...],
    "execution_time": 1.23
  }
}
```

**Response (Rejected):**
```json
{
  "status": "rejected",
  "error": "Insufficient margin",
  "details": {
    "required_margin": 1000,
    "available_margin": 500
  }
}
```

**Response (Error):**
```json
{
  "status": "error",
  "error": "Exchange connection failed",
  "details": "Connection timeout"
}
```

**Notes:**
- The `action` field is flexible - the LLM interprets variations like "go long" vs "enter_long"
- Additional fields can be included and will be passed to the Trading Engine
- Validation happens at the tool call level, not at the API input level

---

#### 3. Get Trade Status
```
GET /trade/status
```

Get current account balance and open positions.

**Response:**
```json
{
  "account": {
    "BTC": {
      "free": 0.1,
      "used": 0.05,
      "total": 0.15
    },
    "info": {
      "marginBalance": 0.15,
      "availableMargin": 0.1,
      "marginUsedPcnt": 0.33
    }
  },
  "positions": [
    {
      "symbol": "BTC/USD:BTC",
      "contracts": 10000,
      "side": "long",
      "entry_price": 110000,
      "current_price": 111000,
      "pnl": 0.91,
      "margin": 0.05
    }
  ],
  "timestamp": "2024-01-10T12:00:00Z"
}
```

---

#### 4. Get Trade History
```
GET /trade/history?limit=10
```

Get recent trade history.

**Query Parameters:**
- `limit` (optional): Maximum number of trades to return (default: 10)

**Response:**
```json
{
  "trades": [
    {
      "trade_id": "123e4567-e89b-12d3-a456-426614174000",
      "symbol": "BTC/USD",
      "action": "enter_long",
      "entry_price": 110000,
      "status": "open",
      "created_at": "2024-01-10T11:00:00Z"
    }
  ],
  "count": 1,
  "timestamp": "2024-01-10T12:00:00Z"
}
```

---

#### 5. Close Position
```
POST /trade/close-position
```

Close an open position for a specific symbol.

**Request Body:**
```json
{
  "symbol": "BTC/USD"
}
```

**Response:**
```json
{
  "status": "success",
  "symbol": "BTC/USD",
  "details": {
    "closed_contracts": 10000,
    "exit_price": 111000,
    "realized_pnl": 100
  },
  "timestamp": "2024-01-10T12:00:00Z"
}
```

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing authentication |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error |

## Environment Variables

### Trading API Configuration
- `TRADING_API_HOST`: API host (default: "0.0.0.0")
- `TRADING_API_PORT`: API port (default: "5000")
- `TESTNET`: Set to "1" for testnet mode
- `EXCHANGE_NAME`: Exchange to use (default: "bitmex")
- `EXCHANGE_API`: Exchange API key
- `EXCHANGE_SECRET`: Exchange secret key
- `TRADING_LLM_API_KEY`: OpenAI API key for Trading LLM
- `DEBUG`: Set to "1" for debug mode with detailed errors

---

## Extraction Module API (IMPLEMENTED)

### Running the Extraction API

```bash
# Method 1: Direct Python
cd /home/sev/ggbot
source .venv/bin/activate
python -m extraction.run_api

# Method 2: Using uvicorn directly
uvicorn extraction.api:app --host 0.0.0.0 --port 5001 --reload

# Method 3: With custom settings
export EXTRACTION_API_PORT=5001
export EXTRACTION_API_HOST=0.0.0.0
python -m extraction.api
```

**API Documentation URLs:**
- Swagger UI: http://localhost:5001/docs
- ReDoc: http://localhost:5001/redoc

### Extract Market Data
```
POST /api/extraction/run
```

Trigger market data extraction for specified symbols and timeframes.

**Request Body:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "symbols": ["BTC/USDT", "ETH/USDT"],  // Optional, uses config if not provided
  "timeframes": ["15m", "1h"]           // Optional, uses config if not provided
}
```

**Response:**
```json
{
  "status": "started",
  "extraction_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Extraction started for 2 symbols across 2 timeframes"
}
```

### Get Extraction Status
```
GET /api/extraction/status/{extraction_id}
```

**Response:**
```json
{
  "extraction_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "started_at": "2024-01-10T12:00:00Z",
  "completed_at": "2024-01-10T12:00:45Z",
  "data_points_extracted": 8,
  "errors": []
}
```

### Get Latest Market Data
```
GET /api/extraction/latest/{user_id}
```

**Query Parameters:**
- `symbol` (required): Trading symbol (e.g., "BTC/USDT")
- `timeframe` (required): Timeframe (e.g., "15m")
- `data_type` (optional): "indicator_values" or "indicator_analysis"

**Response:**
```json
{
  "symbol": "BTC/USDT",
  "timeframe": "15m",
  "data": {
    "RSI": [45.2, 46.1, 47.3, ...],  // 100 data points
    "MACD": {...},
    "BB": {...}
  },
  "analysis": "Current RSI indicates neutral momentum...",
  "created_at": "2024-01-10T12:00:00Z"
}
```

---

## Decision Module API (IMPLEMENTED)

### Running the Decision API

```bash
# Method 1: Direct Python
cd /home/sev/ggbot
source .venv/bin/activate
python -m decision.run_api

# Method 2: Using uvicorn directly
uvicorn decision.api:app --host 0.0.0.0 --port 5002 --reload

# Method 3: With custom settings
export DECISION_API_PORT=5002
export DECISION_API_HOST=0.0.0.0
python -m decision.api
```

**API Documentation URLs:**
- Swagger UI: http://localhost:5002/docs
- ReDoc: http://localhost:5002/redoc

### Generate Trading Decision
```
POST /api/decision/analyze
```

Analyze market data and generate a trading decision.

**Request Body:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "mode": "auto"  // "auto", "NEW_TRADE", or "MANAGE_TRADE"
}
```

**Response:**
```json
{
  "decision_id": "789e0123-e89b-12d3-a456-426614174000",
  "mode": "NEW_TRADE",
  "intent": {
    "action": "enter_long",
    "symbol": "BTC/USDT",
    "confidence": 0.85,
    "leverage": 10,
    "stop_loss": 42000,
    "take_profit": 48000
  },
  "reasoning": "Strong bullish divergence on RSI with support bounce...",
  "created_at": "2024-01-10T12:05:00Z"
}
```

### Get Decision History
```
GET /api/decision/history/{user_id}
```

**Query Parameters:**
- `limit` (optional): Number of decisions to return (default: 10)
- `offset` (optional): Pagination offset
- `status` (optional): Filter by decision outcome

**Response:**
```json
{
  "decisions": [
    {
      "decision_id": "789e0123-e89b-12d3-a456-426614174000",
      "mode": "NEW_TRADE",
      "intent": {...},
      "reasoning": "...",
      "trade_id": "123e4567-e89b-12d3-a456-426614174000",
      "outcome": "profitable",
      "created_at": "2024-01-10T12:05:00Z"
    }
  ],
  "total": 45,
  "limit": 10,
  "offset": 0
}
```

### Get Current Decision
```
GET /api/decision/current/{user_id}
```

Get the most recent decision for active trade management.

**Response:**
```json
{
  "decision_id": "789e0123-e89b-12d3-a456-426614174000",
  "mode": "MANAGE_TRADE",
  "original_reasoning": "Bullish divergence entry",
  "current_analysis": "Trade progressing as expected, maintaining position",
  "active_trade": {
    "trade_id": "123e4567-e89b-12d3-a456-426614174000",
    "unrealized_pnl": 125.50
  }
}
```

---

## Dashboard API (IMPLEMENTED - Updated for Universal Trade Lifecycle)

### Running the Dashboard API

```bash
# Method 1: Direct Python
cd /home/sev/ggbot
source .venv/bin/activate
python -m core.api.dashboard_api

# Method 2: Using uvicorn directly
uvicorn core.api.dashboard_api:app --host 0.0.0.0 --port 5003 --reload

# Method 3: With custom settings
export DASHBOARD_API_PORT=5003
export DASHBOARD_API_HOST=0.0.0.0
python core.api.dashboard_api
```

**API Documentation URLs:**
- Swagger UI: http://localhost:5003/docs
- ReDoc: http://localhost:5003/redoc

### Schema Migration Notes (Phase 3)

The Dashboard API has been updated to work with the new Universal Trade Lifecycle system while maintaining full backward compatibility:

- **Database Access**: All queries now use `trades_legacy` view instead of direct `trades` table access
- **Field Mapping**: Automatic translation between new and old field names:
  - `symbol` ↔ `pair`
  - `status` ↔ `trade_status` 
  - `unrealized_pnl` ↔ `profit_loss`
  - `opened_at` ↔ `created_at`
- **API Compatibility**: All endpoints maintain identical request/response formats
- **Enhanced Data**: Improved trade tracking with TP/SL order monitoring and automated closure

### Get Current Positions (Legacy Compatibility)
```
GET /api/dashboard/{user_id}/positions
```

Returns all open positions via `trades_legacy` view for backward compatibility. Uses field mappings to maintain API compatibility while accessing new Universal Trade Lifecycle schema.

**Response:**
```json
{
  "positions": [
    {
      "trade_id": "123e4567-e89b-12d3-a456-426614174000",
      "symbol": "BTC/USD",
      "side": "long",
      "size": 1000,
      "entry_price": 45000,
      "current_price": 46000,
      "unrealized_pnl": 22.22,
      "unrealized_pnl_percentage": 2.22,
      "stop_loss": 44000,
      "take_profit": 47000,
      "duration": "2h 15m",
      "decision_id": "789e0123-e89b-12d3-a456-426614174000"
    }
  ],
  "total_positions": 1,
  "total_unrealized_pnl": 22.22
}
```

### Get Current Trades (Universal Trade Lifecycle)
```
GET /api/dashboard/{user_id}/trades
```

Returns all trades from the Universal Trade Lifecycle system via `trades_legacy` view. Includes automatic field mapping and backward compatibility support.

**Response:**
```json
{
  "trades": [
    {
      "trade_id": "123e4567-e89b-12d3-a456-426614174000",
      "symbol": "BTC/USD",
      "side": null,
      "status": "open",
      "size_contracts": 4000,
      "entry_price": 45000,
      "mark_price": 46000,
      "unrealized_pnl": 0.0217,
      "opened_at": "2024-01-10T11:00:00Z",
      "closed_at": null,
      "last_updated": "2024-01-10T12:00:00Z"
    }
  ],
  "total_trades": 1
}
```

### Get Performance Metrics
```
GET /api/dashboard/{user_id}/performance?period=7d
```

Returns performance metrics for the specified period. Now uses `trades_legacy` view to access closed trades with proper field mapping (`profit_loss` → `realized_pnl`).

**Query Parameters:**
- `period`: Time period (1d, 7d, 30d, all)

**Response:**
```json
{
  "period": "7d",
  "metrics": {
    "total_pnl": 1250.50,
    "total_pnl_percentage": 12.5,
    "win_rate": 0.65,
    "total_trades": 20,
    "winning_trades": 13,
    "losing_trades": 7,
    "average_win": 150.25,
    "average_loss": -75.10,
    "profit_factor": 2.0,
    "max_drawdown": -5.2,
    "sharpe_ratio": 0
  },
  "daily_pnl": [
    {"date": "2024-01-10", "pnl": 125.50, "trades": 3}
  ]
}
```

### WebSocket Real-time Updates
```
WS /ws/dashboard/{user_id}
```

Connect for real-time position updates.

**Message Types:**
```json
{
  "type": "position_update",
  "data": {
    "positions": [...],
    "total_positions": 1,
    "total_unrealized_pnl": 22.22
  }
}
```

---

## Agent Control API (IMPLEMENTED)

### Running the Agent Control API

```bash
# Method 1: Direct Python
cd /home/sev/ggbot
source .venv/bin/activate
python -m core.api.agent_control_api

# Method 2: Using uvicorn directly
uvicorn core.api.agent_control_api:app --host 0.0.0.0 --port 5004 --reload

# Method 3: With custom settings
export AGENT_CONTROL_API_PORT=5004
export AGENT_CONTROL_API_HOST=0.0.0.0
python core.api.agent_control_api
```

**API Documentation URLs:**
- Swagger UI: http://localhost:5004/docs
- ReDoc: http://localhost:5004/redoc

### Start Trading Bot
```
POST /api/agent/{user_id}/start
```

Start the trading bot for a user.

**Request Body:**
```json
{
  "modules": ["all"]  // or specific modules: ["extraction", "decision", "trading"]
}
```

**Response:**
```json
{
  "status": "started",
  "modules_started": ["extraction", "decision", "trading", "monitoring"],
  "message": "Trading bot started successfully"
}
```

### Stop Trading Bot
```
POST /api/agent/{user_id}/stop
```

**Request Body:**
```json
{
  "modules": ["all"],
  "close_positions": false  // If true, closes all open positions
}
```

**Response:**
```json
{
  "status": "stopped",
  "modules_stopped": ["extraction", "decision", "trading"],
  "open_positions": 1,
  "message": "Trading bot stopped. 1 position remains open."
}
```

### Get Agent Status
```
GET /api/agent/{user_id}/status
```

**Response:**
```json
{
  "overall_status": "running",
  "modules": {
    "extraction": {
      "status": "running",
      "last_run": "2024-01-10T12:15:00Z",
      "next_run": "2024-01-10T12:30:00Z",
      "errors": 0
    },
    "decision": {
      "status": "running",
      "last_run": "2024-01-10T12:20:00Z",
      "mode": "MANAGE_TRADE",
      "errors": 0
    },
    "trading": {
      "status": "running",
      "active_positions": 1,
      "last_execution": "2024-01-10T11:00:00Z"
    },
    "monitoring": {
      "status": "running",
      "last_update": "2024-01-10T12:25:00Z"
    }
  }
}
```

### Start Autonomous Scheduler
```
POST /api/scheduler/start
```

Start autonomous trading mode with scheduled extraction every 15 minutes.

**Response:**
```json
{
  "status": "started",
  "message": "Autonomous trading mode activated",
  "job_id": "extraction_job",
  "interval": "15 minutes",
  "next_run": "2024-01-10T12:30:00Z"
}
```

**Response (Already Running):**
```json
{
  "status": "already_running",
  "message": "Autonomous mode is already active",
  "job_id": "extraction_job"
}
```

### Stop Autonomous Scheduler
```
POST /api/scheduler/stop
```

Stop autonomous trading mode (API server remains running).

**Response:**
```json
{
  "status": "stopped",
  "message": "Autonomous trading mode deactivated",
  "job_id": "extraction_job"
}
```

**Response (Not Running):**
```json
{
  "status": "already_stopped",
  "message": "Autonomous mode is not currently running"
}
```

### Get Scheduler Status
```
GET /api/scheduler/status
```

Get current scheduler status and configuration.

**Response:**
```json
{
  "status": "healthy",
  "scheduler": {
    "scheduler_state": "running",
    "autonomous_mode": "active",
    "job_count": 1,
    "config_id": "a93de31b-9b8a-42e3-827d-c31e580f5f36",
    "symbols": ["BTC/USDT"],
    "timeframes": ["15m"],
    "next_run": "2024-01-10T12:30:00Z"
  }
}
```

**Response (Inactive):**
```json
{
  "status": "healthy",
  "scheduler": {
    "scheduler_state": "running",
    "autonomous_mode": "inactive",
    "job_count": 0,
    "config_id": "a93de31b-9b8a-42e3-827d-c31e580f5f36",
    "symbols": ["BTC/USDT"],
    "timeframes": ["15m"]
  }
}
```

---

## Configuration API (To Be Implemented)

### Get Configuration
```
GET /api/config/{user_id}/{module}
```

Get configuration for a specific module.

**Response:**
```json
{
  "module": "extraction",
  "config": {
    "symbols": ["BTC/USDT", "ETH/USDT"],
    "timeframes": ["15m", "1h"],
    "indicators": ["RSI", "MACD", "BB"]
  },
  "last_updated": "2024-01-10T10:00:00Z"
}
```

### Update Configuration
```
PUT /api/config/{user_id}/{module}
```

Update configuration for a specific module.

**Request Body:**
```json
{
  "config": {
    "symbols": ["BTC/USDT"],
    "timeframes": ["15m"],
    "indicators": ["RSI", "MACD"]
  }
}
```

**Response:**
```json
{
  "status": "updated",
  "module": "extraction",
  "config": {...},
  "message": "Configuration updated successfully"
}
```

---

## Dashboard API (To Be Implemented)

### Get Current Positions
```
GET /api/dashboard/{user_id}/positions
```

**Response:**
```json
{
  "positions": [
    {
      "trade_id": "123e4567-e89b-12d3-a456-426614174000",
      "symbol": "BTC/USD",
      "side": "long",
      "size": 1000,
      "entry_price": 45000,
      "current_price": 46000,
      "unrealized_pnl": 22.22,
      "unrealized_pnl_percentage": 2.22,
      "stop_loss": 44000,
      "take_profit": 47000,
      "duration": "2h 15m",
      "decision_id": "789e0123-e89b-12d3-a456-426614174000"
    }
  ],
  "total_positions": 1,
  "total_unrealized_pnl": 22.22
}
```

### Get Performance Metrics
```
GET /api/dashboard/{user_id}/performance
```

**Query Parameters:**
- `period`: Time period (1d, 7d, 30d, all)

**Response:**
```json
{
  "period": "7d",
  "metrics": {
    "total_pnl": 1250.50,
    "total_pnl_percentage": 12.5,
    "win_rate": 0.65,
    "total_trades": 20,
    "winning_trades": 13,
    "losing_trades": 7,
    "average_win": 150.25,
    "average_loss": -75.10,
    "profit_factor": 2.0,
    "max_drawdown": -5.2,
    "sharpe_ratio": 1.8
  },
  "daily_pnl": [
    {"date": "2024-01-10", "pnl": 125.50, "trades": 3},
    {"date": "2024-01-09", "pnl": -50.25, "trades": 2}
  ]
}
```

### WebSocket Real-time Updates
```
WS /ws/dashboard/{user_id}
```

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:5000/ws/dashboard/user-id');
```

**Message Types:**

Position Update:
```json
{
  "type": "position_update",
  "data": {
    "trade_id": "123e4567-e89b-12d3-a456-426614174000",
    "current_price": 46100,
    "unrealized_pnl": 24.44,
    "unrealized_pnl_percentage": 2.44
  }
}
```

New Decision:
```json
{
  "type": "new_decision",
  "data": {
    "decision_id": "789e0123-e89b-12d3-a456-426614174000",
    "mode": "NEW_TRADE",
    "action": "enter_long",
    "symbol": "BTC/USD",
    "confidence": 0.85
  }
}
```

Module Status:
```json
{
  "type": "module_status",
  "data": {
    "module": "extraction",
    "status": "completed",
    "message": "Extracted data for 2 symbols"
  }
}
```

---

## Testing the API

### Using curl

1. Health check:
```bash
curl http://localhost:5000/health
```

2. Execute a trade:
```bash
curl -X POST http://localhost:5000/trade/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "enter_long",
    "symbol": "BTC/USD",
    "collateral_amount": 1000,
    "leverage": 10,
    "reasoning": "Testing API"
  }'
```

3. Get account status:
```bash
curl http://localhost:5000/trade/status
```

### Using Python

```python
import requests

# Execute trade
response = requests.post('http://localhost:5000/trade/execute', json={
    'action': 'enter_long',
    'symbol': 'BTC/USD',
    'collateral_amount': 1000,
    'leverage': 10
})
print(response.json())

# Get status
response = requests.get('http://localhost:5000/trade/status')
print(response.json())
```

---

## Notes

1. **Semi-Structured Intents**: The Trading API is designed to accept flexible input formats. The LLM interprets variations in field values, making the API more robust to different Decision Module implementations.

2. **Async Architecture**: All endpoints are fully asynchronous, allowing for high concurrency and efficient resource usage.

3. **Error Handling**: Comprehensive error handling with detailed error messages in debug mode.

4. **MCP Integration**: The Trading Module uses MCP (Model Context Protocol) servers for exchange interactions, providing a standardized interface across different exchanges.

5. **Testnet Support**: Full testnet support for safe testing without real funds.