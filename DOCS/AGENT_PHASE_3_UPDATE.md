# Autonomous Trading Agent - Phase 3 Progress

**Last Updated:** 2025-10-29
**Status:** 🟡 Partially Complete - Agent infrastructure working, authentication issues need resolution

---

## 🎯 Overview

Phase 3 implements the **Agent Runner** - a long-running process that executes trading strategies using Claude's Agent SDK. The agent can operate in two modes:

1. **Strategy Definition Mode** - Interactive conversation to build trading strategy
2. **Autonomous Mode** - 24/7 trading execution with self-directed timing

---

## ✅ What's Working

### Core Agent Infrastructure
- ✅ **Agent Runner** (`agent/run_agent.py`) - Mode routing with strategy_definition and autonomous modes
- ✅ **MCP Server** (`agent/mcp_server.py`) - 10 trading tools registered and functional
- ✅ **Chat CLI** (`agent/chat.py`) - Interactive terminal interface with real-time response monitoring
- ✅ **Service Client** (`agent/service_client.py`) - HTTP client with service authentication headers

### Architecture
- ✅ **Simplified dual-mode design** - Separate processes for strategy building vs autonomous trading
- ✅ **Mode switch logic** - Agent can request autonomous mode, user confirms with "1" or "2"
- ✅ **Strategy persistence** - Saves to `config_data.agent_strategy` in database
- ✅ **Redis queue communication** - Messages flow between agent and chat CLI

### Agent Tools - Partially Working
- ✅ **query_market_data** - Successfully queries 32 data points across 7 categories (RSI, MACD, VIX, DXY, etc.)
- ✅ **wait_for** - Sleep for specified duration
- ✅ **request_autonomous_mode** - Prompts user for confirmation

### Backend Authentication
- ✅ **Service auth in ggbot.py** - Added `agent-runner` to allowed services (600 req/min rate limit)
- ✅ **API agent endpoints** - All 8 endpoints updated with `get_service_or_user_auth()` dual auth
- ✅ **Service client headers** - Sends `Authorization: Bearer {SERVICE_KEY}` + `X-Service-Auth: agent-runner`
- ✅ **JSON serialization** - Converts numpy/pandas objects to JSON-compatible format

---

## ❌ What's Broken

### Critical Blocking Issues

#### 1. **ggbot Deadlock on Agent API Requests**
- **Symptom:** After 1-2 agent tool calls, ggbot completely hangs on subsequent requests
- **Evidence:**
  - First call to `query_market_data` works perfectly
  - Subsequent calls to other endpoints timeout (30s each × 3 retries)
  - Curl test works immediately after restart, then deadlocks after agent uses it
- **Suspected cause:** `get_service_or_user_auth()` dependency in FastAPI causing resource leak or blocking
- **Impact:** All trading tools (execute_trade, get_positions, close_position, etc.) unusable after first request

#### 2. **Agent API Endpoints Status**
- ❌ **execute_trade** - Times out
- ❌ **get_positions** - Times out
- ❌ **get_account_status** - Times out
- ❌ **close_position** - Times out
- ❌ **record_trade_observation** - Times out
- ❌ **query_trade_observations** - Times out
- ❌ **update_strategy** - Times out

---

## 🔧 Technical Details

### Files Modified

#### agent/run_agent.py (Lines 195-465)
- Mode routing logic
- Strategy definition: Simple query/response loop via Redis
- Autonomous mode: Pure `receive_messages()` for 24/7 operation
- Mode switch confirmation: Handles "1" (save) or "2" (revise)
- `_save_strategy()`: Persists strategy to database

#### agent/mcp_server.py (Lines 60-666)
- Fixed `query_market_data` to accept dict parameter (handles JSON serialization)
- Fixed `record_trade_observation` to parse dict parameters
- Enhanced `request_autonomous_mode` to store strategy in Redis

#### agent/service_client.py (Complete rewrite)
- Added service authentication headers
- All methods now send `params={"user_id": self.user_id}` query parameter
- Proper timeout handling (30s per request)

#### agent/chat.py (Complete rewrite)
- Concurrent tasks: `response_monitor()` + `input_handler()`
- Uses `aioconsole.ainput()` for non-blocking input
- Real-time response display (no more waiting for next message)

#### api/agent.py (Lines 44-104, All endpoints)
- Added `get_service_or_user_auth()` function - dual auth support
- Updated all 8 endpoints to use service OR JWT authentication
- Fixed `get_configuration()` calls to use keyword arguments
- Added JSON serialization for numpy/pandas extraction results

#### ggbot.py (Lines 53-82)
- Updated `get_service_user()` to allow both `signal-listener` and `agent-runner`
- Per-service rate limiting (agent-runner: 600/min, signal-listener: 120/min)

---

## 🐛 Debugging Notes

### Deadlock Investigation
**Symptoms observed:**
1. Fresh ggbot restart → curl test works perfectly
2. Agent calls `query_market_data` → works perfectly
3. Agent calls `get_account_status` → hangs for 30s, times out
4. All subsequent requests hang indefinitely
5. No logs in ggbot showing the request even arrived

**Debug logging added:**
- `api/agent.py:53` - Logs service_header, auth header, and query params
- `agent/service_client.py:82` - Logs request method, endpoint, kwargs
- `agent/service_client.py:84` - Logs response URL

**Theories:**
1. FastAPI Depends() with async function causing event loop blocking
2. httpx client connection pool exhaustion
3. Redis connection leak in auth function
4. Circular dependency in get_service_or_user_auth

---

## 📋 Next Steps (Priority Order)

### Immediate (Session 2)
1. **Fix ggbot deadlock**
   - Option A: Remove `get_service_or_user_auth` complexity, use simple header check
   - Option B: Debug with async profiler to find blocking call
   - Option C: Revert to JWT-only auth, skip service auth for agents

2. **Test all agent trading tools**
   - Once deadlock fixed, systematically test each tool
   - Document any request/response format issues

3. **Test full strategy definition flow**
   - Build complete strategy with agent
   - Call `request_autonomous_mode`
   - Confirm with "1", verify strategy saves to database

### Phase 3 Completion
4. **Test autonomous mode**
   - Restart agent with `--mode=autonomous`
   - Verify it loads strategy from database
   - Watch it use tools (query_market_data, execute_trade, wait_for)

5. **Add API endpoints for agent management**
   - `POST /agent/{config_id}/start` - Start agent process (PM2)
   - `POST /agent/{config_id}/stop` - Stop agent process
   - `POST /agent/{config_id}/message` - Send message to running agent
   - `GET /agent/{config_id}/status` - Check if agent is running

### Phase 4 - Frontend Integration
6. **Agent UI components**
   - Agent chat interface
   - Strategy editor with agent assistance
   - Agent status indicator
   - Start/stop controls

---

## 🧪 Testing Commands

### Start Agent (Strategy Definition Mode)
```bash
cd /home/sev/ggbot
source .venv/bin/activate
API_BASE_URL=http://localhost:8000 python agent/run_agent.py \
  --config-id=d13d5536-2498-4f27-b2bc-e4f98958e1d8 \
  --mode=strategy_definition
```

### Start Chat CLI (Separate Terminal)
```bash
cd /home/sev/ggbot
source .venv/bin/activate
python agent/chat.py --config-id=d13d5536-2498-4f27-b2bc-e4f98958e1d8
```

### Test Agent API Endpoints
```bash
# Test with service auth
cd /home/sev/ggbot
./test_agent_api.sh
```

### Check Logs
```bash
# Agent logs (Terminal 1 shows agent/run_agent.py output)
# ggbot logs
tail -f logs/ggbot.log | grep -E "agent|Auth check"
```

---

## 📚 Related Documentation

- **Architecture:** `README.md` - Overall platform architecture
- **Phase 1-2:** `CHANGELOG.md` - MCP server and tool implementation
- **Agent SDK:** Claude Agent SDK docs for message streaming patterns
- **Database Schema:** `database/schema.md` - agent_strategy field in config_data

---

## 🎓 Lessons Learned

1. **FastAPI Depends with Request injection** - Must be careful with async dependencies that access Request object
2. **Agent SDK patterns** - Separate `receive_response()` (bounded) from `receive_messages()` (infinite loop)
3. **Service authentication** - Rate limiting per service prevents abuse
4. **JSON serialization** - Numpy/pandas objects must be explicitly converted for API responses
5. **httpx params** - Query parameters work with `params={}` argument in httpx

---

## 🚨 Known Issues

1. **Deadlock after first agent API call** - Blocks all subsequent requests (CRITICAL)
2. **No compaction context injection** - Phase 4 feature, agent will lose context after ~200k tokens
3. **No PM2 process management** - Agent must be manually started/stopped
4. **No frontend integration** - All testing via CLI only

---

## ✨ Success Metrics

- ✅ Agent can chat interactively via Redis queues
- ✅ Agent can query BTC RSI and receive real market data
- ✅ Mode switch logic prompts user for confirmation
- ⏳ Agent can complete full strategy definition (blocked by deadlock)
- ⏳ Agent can trade autonomously 24/7 (blocked by deadlock)
- ⏳ Agent can learn from past trades via observations (blocked by deadlock)

---

**Session 1 Progress:** 60% complete. Core infrastructure working, authentication causing deadlock. Ready for debug session.
