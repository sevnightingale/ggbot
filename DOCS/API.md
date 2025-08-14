# GGBots API Documentation

**Last Updated**: 2025-08-14  
**API Version**: 1.0.0  
**Base URL**: `https://ggbots-api.nightingale.business`

## Overview

The GGBots platform exposes a comprehensive REST API through a unified FastAPI server that aggregates multiple service modules. The API supports autonomous trading operations, market data extraction, decision analysis, and real-time monitoring.

### Architecture

```
Frontend → Main API (port 8000) → Module APIs
                ↓
            Database Layer (PostgreSQL)
```

## Authentication & Access

- **Demo Mode**: Password-protected (`vibecodecamp`)
- **User Management**: Email-based UUID generation
- **Default User**: `00000000-0000-0000-0000-000000000001`

---

## 🚀 Main API Endpoints

### Root & Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root endpoint showing available APIs |
| `GET` | `/health` | Combined health check for all services |

### Test Endpoints (Connection Verification)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| `GET` | `/test/health` | Backend API health check | ✅ Working |
| `GET` | `/test/ggbot-db` | GGBot PostgreSQL connection test | ✅ Working |
| `GET` | `/test/hummingbot-db` | Hummingbot PostgreSQL connection test | ❌ **ISSUE: Port 5433** |

---

## 🔍 Extraction Module (`/extraction`)

**Purpose**: Market data gathering and technical analysis

### Core Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| `POST` | `/api/extraction/run` | Trigger market data extraction | ✅ |
| `GET` | `/api/extraction/status/{extraction_id}` | Get extraction job status | ✅ |
| `GET` | `/api/extraction/latest/{user_id}` | Get latest market data | ✅ |
| `POST` | `/webhooks/trigger-extraction` | Webhook for pipeline triggers | ✅ |
| `GET` | `/health` | Module health check | ✅ |

### Request/Response Models

**ExtractionRequest**:
```json
{
  "user_id": "00000000-0000-0000-0000-000000000001",
  "symbols": ["BTC/USDT", "ETH/USDT"],
  "timeframes": ["15m", "1h", "4h"],
  "config_id": "default",
  "custom_mode": "ggshot"
}
```

**Key Features**:
- Supports new config_id system
- Legacy fallback system
- ggShot signal processing
- Webhook chaining to decision module
- Account monitoring integration

---

## 🧠 Decision Module (`/decision`)

**Purpose**: AI-powered trading decision generation

### Core Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| `POST` | `/api/decision/analyze` | Generate trading decision | ✅ |
| `GET` | `/api/decision/history/{user_id}` | Get decision history | ✅ |
| `GET` | `/api/decision/current/{user_id}` | Get current decision | ✅ |
| `GET` | `/api/decision/status/{decision_id}` | Get decision generation status | ✅ |
| `POST` | `/webhooks/trigger-decision` | Webhook for pipeline triggers | ✅ |
| `GET` | `/health` | Module health check | ✅ |

### Request/Response Models

**DecisionRequest**:
```json
{
  "user_id": "00000000-0000-0000-0000-000000000001",
  "config_id": "config-uuid",
  "mode": "auto",
  "symbol": "BTC/USDT",
  "timeframes": ["15m", "1h", "4h"]
}
```

**Key Features**:
- Auto mode detection (NEW_TRADE vs MANAGE_TRADE)
- Config-ID based isolation
- ggShot signal validation
- Webhook chaining to trading module
- Account monitoring integration

---

## ⚡ Trading Module (`/trading`)

**Purpose**: Hummingbot-based trade execution

### Core Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| `POST` | `/webhooks/execute-trade` | Execute trade via webhook | ✅ |
| `POST` | `/trade/execute` | Direct trade execution | ✅ |
| `GET` | `/status` | Trading system status | ✅ |
| `GET` | `/health` | Module health check | ✅ |
| `GET` | `/` | Root endpoint | ✅ |

### Hummingbot Integration (`/trading/hummingbot`)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| `GET` | `/portfolio/{user_id}` | Get user portfolio | ✅ |
| `GET` | `/positions/{user_id}` | Get active positions | ✅ |
| `GET` | `/orders/{user_id}` | Get active orders | ✅ |
| `GET` | `/trades/{user_id}` | Get trade history | ✅ |
| `GET` | `/dashboard/{user_id}` | Get dashboard data | ✅ |
| `GET` | `/bot/{instance_name}/status` | Get bot status | ✅ |
| `GET` | `/system/status` | Get system status | ✅ |

### Request/Response Models

**TradingIntent**:
```json
{
  "decision_id": "decision-uuid",
  "action": "enter_long",
  "symbol": "BTC/USD",
  "confidence": 0.75,
  "stop_loss_price": 45000,
  "take_profit_price": 50000,
  "reasoning": "Strong bullish momentum"
}
```

---

## 📊 Dashboard Module (`/dashboard`)

**Purpose**: Real-time monitoring and performance metrics

### Core Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| `GET` | `/api/dashboard/{user_id}/positions` | Get current positions (legacy) | ✅ |
| `GET` | `/api/dashboard/{user_id}/trades` | Get current trades | ✅ |
| `GET` | `/api/dashboard/{user_id}/performance` | Get performance metrics | ✅ |
| `GET` | `/api/agent/{user_id}/status` | Get agent status | ✅ |
| `GET` | `/api/dashboard/strategies/{user_id}` | Get user strategies | ✅ |
| `GET` | `/api/dashboard/performance/{config_id}` | Get strategy performance | ✅ |
| `GET` | `/api/dashboard/trades/{config_id}` | Get recent trades | ✅ |
| `WebSocket` | `/ws/dashboard/{user_id}` | Real-time updates | ✅ |
| `GET` | `/health` | Module health check | ✅ |

### Key Features

- Real-time WebSocket updates (30s intervals)
- Performance metrics with P&L calculation
- Multi-strategy tracking
- Background update tasks

---

## ⚙️ Agent Control Module (`/agent`)

**Purpose**: Bot lifecycle management and configuration

### Core Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| `POST` | `/api/agent/{user_id}/start` | Start trading bot | ✅ |
| `POST` | `/api/agent/{user_id}/stop` | Stop trading bot | ✅ |
| `POST` | `/api/agent/{user_id}/pause` | Pause trading | ✅ |
| `POST` | `/api/agent/{user_id}/resume` | Resume trading | ✅ |
| `GET` | `/api/config/{user_id}/{module}` | Get configuration | ⚠️ **ISSUE** |
| `PUT` | `/api/config/{user_id}/{module}` | Update configuration | ⚠️ **ISSUE** |
| `POST` | `/api/scheduler/start` | Start autonomous scheduler | ✅ |
| `POST` | `/api/scheduler/stop` | Stop autonomous scheduler | ✅ |
| `GET` | `/api/scheduler/status` | Get scheduler status | ✅ |
| `GET` | `/health` | Module health check | ✅ |

---

## 🔧 Configuration Management (`/api/configs`)

**Purpose**: Strategy configuration templates and management

### Core Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| `POST` | `/create-from-template` | Create strategy from template | ✅ |
| `GET` | `/{config_id}` | Get single configuration | ✅ |
| `PUT` | `/{config_id}` | Update configuration | ✅ |
| `DELETE` | `/{config_id}` | Delete configuration | ✅ |
| `GET` | `/{config_id}/permissions` | Get configuration permissions | ✅ |
| `GET` | `/user/{user_id}` | Get user configurations | ✅ |

### Templates Available

- `rsi`: RSI Momentum Strategy
- `macd`: MACD Trend Following
- `manual`: Manual Trading Bot
- `momentum`: Momentum Breakout Strategy
- `bollinger`: Bollinger Bands Mean Reversion

### Key Features

- Template-based strategy creation
- Flagship bot protection (ggShot)
- Permission management
- Paper trading integration

---

## 👥 User Management (`/api/users`)

**Purpose**: Demo user signup and management

### Core Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| `POST` | `/demo-signup` | Create/retrieve demo user | ✅ |
| `GET` | `/{user_id}` | Get user information | ✅ |

---

## 🚨 Identified Issues & Discrepancies

### Critical Issues

1. **Hummingbot Database Connection** ❌
   - **Issue**: Test endpoint fails with HTTP 500
   - **Root Cause**: Port discrepancy (API uses 5434, actual is 5433)
   - **Impact**: Connection tests fail, may affect Hummingbot integrations
   - **Status**: **PARTIALLY FIXED** - Updated test API, documentation corrected

2. **Hardcoded Config IDs** ⚠️
   - **Location**: `agent_control_api.py:242, 269`
   - **Issue**: Hardcoded `default_config_id = "a93de31b-9b8a-42e3-827d-c31e580f5f36"`
   - **Impact**: Breaks multi-user/multi-bot functionality
   - **Fix Required**: Use dynamic config_id resolution

3. **Module Import Dependencies** ⚠️
   - **Issue**: Several imports may fail if services aren't running
   - **Examples**: `HummingbotExecutionAdapter`, `get_performance_tracker`
   - **Impact**: API endpoints may fail with import errors

### Configuration Inconsistencies

4. **Config System Duality** ⚠️
   - **Issue**: Mixed usage of legacy and new config systems
   - **Examples**: Some endpoints use `config_name`, others use `config_id`
   - **Impact**: Inconsistent behavior across modules

5. **Default User Assumptions** ⚠️
   - **Issue**: Many endpoints default to hardcoded user ID
   - **Impact**: May not work correctly in multi-user scenarios

### Database Schema Issues

6. **Missing PostgreSQL Import** ⚠️
   - **Location**: `config_api.py:471-472`
   - **Issue**: PostgreSQL imports at bottom of file
   - **Impact**: Potential import order issues

7. **Account Monitoring Dependencies** ⚠️
   - **Issue**: Many endpoints assume exchange credentials are available
   - **Impact**: Graceful degradation may not work as expected

### Performance & Reliability

8. **In-Memory Caches** ⚠️
   - **Issue**: `extraction_status` and `decision_cache` use in-memory storage
   - **Impact**: Data loss on restart, no persistence
   - **Better**: Use Redis or database storage

9. **WebSocket Connection Tracking** ⚠️
   - **Issue**: WebSocket connections stored in memory
   - **Impact**: Connections lost on restart

10. **Background Task Management** ⚠️
    - **Issue**: Multiple background tasks with no centralized management
    - **Impact**: Resource leaks, difficult to monitor

### API Design Issues

11. **Inconsistent Error Handling** ⚠️
    - **Issue**: Different modules use different error response formats
    - **Impact**: Frontend needs to handle multiple error formats

12. **Missing Rate Limiting** ⚠️
    - **Issue**: No rate limiting on any endpoints
    - **Impact**: Potential API abuse

13. **No Authentication Middleware** ⚠️
    - **Issue**: No centralized authentication system
    - **Impact**: Security vulnerability in production

### Environment Dependencies

14. **Environment Variable Usage** ⚠️
    - **Issue**: Heavy reliance on environment variables without validation
    - **Examples**: `DECISION_WEBHOOK_URL`, `TRADING_WEBHOOK_URL`
    - **Impact**: Silent failures if env vars are missing

15. **Docker vs Local Execution** ⚠️
    - **Issue**: Different behavior in Docker vs local development
    - **Impact**: Development/production parity issues

---

## 🔧 Recommended Fixes

### Immediate (High Priority)

1. **Fix Hummingbot Connection**: Update port configuration in all references
2. **Remove Hardcoded Config IDs**: Implement proper config_id resolution
3. **Add Input Validation**: Validate all API inputs with proper error messages
4. **Centralize Error Handling**: Standardize error response format across modules

### Medium Priority

5. **Implement Rate Limiting**: Add rate limiting middleware
6. **Add Authentication**: Implement proper authentication system
7. **Database Connection Pooling**: Optimize database connections
8. **Replace In-Memory Storage**: Move to Redis/database for persistence

### Long Term

9. **API Versioning**: Implement proper API versioning strategy
10. **Comprehensive Testing**: Add integration tests for all endpoints
11. **OpenAPI Documentation**: Generate interactive API documentation
12. **Monitoring & Observability**: Add proper logging and metrics

---

## 📈 API Usage Examples

### Starting a Trading Bot

```bash
# 1. Create configuration from template
curl -X POST "https://ggbots-api.nightingale.business/api/configs/create-from-template" \
  -H "Content-Type: application/json" \
  -d '{
    "template": "rsi",
    "symbol": "BTC/USDT",
    "risk_level": "medium",
    "user_id": "your-user-id"
  }'

# 2. Start the scheduler
curl -X POST "https://ggbots-api.nightingale.business/api/scheduler/start"

# 3. Monitor status
curl "https://ggbots-api.nightingale.business/api/scheduler/status"
```

### Manual Trade Execution

```bash
# Execute a trade
curl -X POST "https://ggbots-api.nightingale.business/trading/trade/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "enter_long",
    "symbol": "BTC/USD",
    "confidence": 0.8,
    "stop_loss_price": 45000,
    "take_profit_price": 52000
  }'
```

### Getting Performance Data

```bash
# Get user performance
curl "https://ggbots-api.nightingale.business/dashboard/api/dashboard/your-user-id/performance?period=7d"

# Get strategy performance
curl "https://ggbots-api.nightingale.business/dashboard/api/dashboard/performance/config-id"
```

---

## 🚀 Testing Your Connection

Use the test endpoints to verify your setup:

```bash
# Test backend connection
curl "https://ggbots-api.nightingale.business/test/health"

# Test database connections  
curl "https://ggbots-api.nightingale.business/test/ggbot-db"
curl "https://ggbots-api.nightingale.business/test/hummingbot-db"
```

---

**Status Legend**:
- ✅ **Working**: Endpoint functional and tested
- ⚠️ **Issue**: Has problems that need fixing
- ❌ **Broken**: Currently not working
- 🚧 **Partial**: Some functionality working

*This documentation reflects the current state of the API as of 2025-08-14. Issues identified should be prioritized for fixes to ensure robust production deployment.*