# GGBot API Documentation

This document provides a comprehensive overview of all API endpoints in the GGBot system.

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

## Future Endpoints (Planned)

### Extraction Module API
- `POST /extract/indicators` - Extract technical indicators
- `GET /extract/market-data` - Get latest market data
- `POST /extract/schedule` - Schedule extraction tasks

### Decision Module API
- `POST /decision/analyze` - Analyze market data and generate intents
- `GET /decision/history` - Get decision history
- `POST /decision/backtest` - Run strategy backtest

### Configuration API
- `GET /config/user/{user_id}` - Get user configuration
- `PUT /config/user/{user_id}` - Update user configuration
- `GET /config/strategies` - List available strategies
- `POST /config/validate` - Validate configuration

### Monitoring API
- `GET /monitor/account/{user_id}` - Get account monitoring data
- `GET /monitor/performance` - Get performance metrics
- `POST /monitor/alerts` - Configure alerts

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