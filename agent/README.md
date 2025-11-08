# Autonomous Trading Agent

**Status**: Phase 3 Complete - Production Ready with Session Persistence
**Last Updated**: 2025-11-08

---

## 🎯 Overview

The ggbots autonomous trading agent enables 24/7 AI-powered trading with full control over strategy execution, position management, and self-directed timing. Built on Claude Agent SDK with 12 specialized MCP tools and **conversation persistence** across crashes and restarts.

**Architecture**: Two-mode system (Strategy Definition → Autonomous Trading) with SDK-powered session resumption

**Current Support**:
- ✅ **Paper Trading** - 142 symbols, full simulation with $10k accounts
- ✅ **Aster Live Trading** - 33 symbols, decentralized futures with Web3 auth
- 🔜 **Symphony Live Trading** - Pending API fixes (see Symphony Integration section)

---

## 📁 File Structure

```
agent/
├── README.md              # This file - usage guide
├── __init__.py           # Package initialization
├── run_agent.py          # Main agent runner (CLI entry point)
├── mcp_server.py         # 12 MCP tool definitions
├── service_client.py     # HTTP client for ggbot API
├── config_manager.py     # Config CRUD (stub, not currently used)
├── chat.py               # CLI chat interface for testing
└── test_mcp_tools.py     # Tool testing script
```

---

## 🚀 Quick Start

### 1. Start Agent in Strategy Definition Mode

```bash
# Activate environment
cd /home/sev/ggbot && source .venv/bin/activate

# Start agent
python agent/run_agent.py --config-id=<config_id> --mode=strategy_definition
```

### 2. Chat with Agent (Separate Terminal)

```bash
# In another terminal
python agent/chat.py --config-id=<config_id>
```

Agent will guide you through:
1. Assessing your experience level
2. Showing available data sources (7 categories, 32 data points)
3. Building a complete trading strategy
4. Saving strategy and exiting

### 3. Start Autonomous Trading

```bash
# Agent automatically saved strategy to database
# Now start autonomous mode
python agent/run_agent.py --config-id=<config_id> --mode=autonomous
```

Agent executes 24/7 with self-directed timing using `wait_for` tool.

---

## 🛠️ MCP Tools (12 Total)

### **Market Data Tools**

#### 1. `query_market_data`
Query market data across 7 categories with 32+ data points.

**Categories**:
- `technical_analysis`: RSI, MACD, Stochastic, Williams_R, CCI, MFI, ADX, PSAR, Aroon, ATR, BB, OBV, SMA, EMA, ROC, VWAP, TRIX, Vortex, BBWidth, Keltner, Donchian
- `macro_economics`: vix, dxy, cpi, nfp
- `sentiment_social`: twitter_sentiment
- `derivatives_leverage`: btc_funding_rate, eth_funding_rate
- `on_chain_analytics`: btc_tvl, whale_activity
- `news_regulatory`: crypto_news
- `trading_signals`: ggshot (PREMIUM)

**Example**:
```json
{
  "symbol": "BTC",
  "categories": {
    "technical_analysis": ["RSI", "MACD"],
    "trading_signals": ["ggshot"]
  },
  "timeframe": "1h"
}
```

**Features**:
- Symbol format auto-detection (BTC, BTCUSDT, BTC/USDT all work)
- Category validation with helpful errors
- Timeframe support: 5m, 15m, 30m, 1h, 4h, 1d, 1w

#### 2. `get_current_price`
Lightweight price check using WebSocket cache (sub-millisecond).

**Use Case**: Quick price verification before executing trades.

---

### **Trading Execution Tools**

#### 3. `execute_trade`
Execute trades with REQUIRED stop loss and take profit.

**Parameters**:
- `symbol` (required): Trading pair
- `side` (required): "long" | "short"
- `stop_loss_price` (required): Safety exit
- `take_profit_price` (required): Profit target
- `confidence` (optional): 0-1 score, default 0.7
- `size_usd` (optional): Position size override (NOTIONAL)
- `leverage` (optional): Leverage override (1-20x)

**Position Sizing**:
- `size_usd` is TOTAL POSITION SIZE (notional), NOT margin
- Actual margin = `size_usd / leverage`
- Example: $1000 position @ 10x = $100 margin required

**Trading Mode Routing**:
- Paper: Simulated execution via `SupabasePaperTradingService`
- Aster: Live execution via `AsterDEXV3LiveTradingService`
- Symphony: (Pending integration)

---

### **Position Management Tools**

#### 4. `get_positions`
Get all open positions (paper or live).

**Returns**:
```json
{
  "symbol": "BTC/USDT",
  "side": "long",
  "entry_price": 111092.50,
  "current_price": 111500.00,
  "size_usd": 750.0,
  "unrealized_pnl": 27.50,
  "unrealized_pnl_percentage": 3.67,
  "leverage": 5,
  "stop_loss": 108000.0,
  "take_profit": 115000.0,
  "opened_at": "2025-11-06T10:30:00Z",
  "trade_id": "uuid" // or batch_id for live
}
```

#### 5. `close_position`
Close an open position manually.

**Parameters**:
- `trade_id` (required): Position ID (trade_id for paper, batch_id for live)
- `reasoning` (required): Why closing (logged to database)

**Use Cases**:
- Manual profit taking
- Risk reduction
- Strategy adjustment
- Market condition changes

#### 6. `cancel_order`
Cancel orphaned TP/SL orders.

**Support**:
- ✅ Paper Trading
- ✅ Aster Trading
- ❌ Symphony (batch-based orders, close position instead)

**Parameters**:
- `order_id` (required): Order ID from `get_account_status`
- `symbol` (required): Trading pair

---

### **Account Management Tools**

#### 7. `get_account_status`
Get account balance and performance metrics.

**Returns**:
```json
{
  "balance": 9875.50,           // Paper/Aster only
  "total_pnl": -124.50,
  "total_trades": 25,
  "win_rate": 0.56,
  "open_positions": 2,
  "open_orders": []             // Aster only
}
```

**Mode Differences**:
- **Paper**: Full simulation with accurate balance
- **Aster**: Real-time balance from API (`availableBalance`)
- **Symphony**: Balance NOT available (API limitation)

---

### **Learning & Reflection Tools**

#### 8. `record_trade_observation`
Record post-trade reflection after closing positions.

**Parameters**:
```json
{
  "trade_id": "uuid",
  "observation_type": "win_analysis" | "loss_analysis",
  "what_went_well": "RSI signal accurate, entry timing perfect",
  "what_went_wrong": "Exit too early, left profit on table",
  "predictive_data_points": {
    "RSI": "Strong oversold signal at 28",
    "vix": "Low volatility helped smooth entry"
  },
  "decision_review": "Confidence 0.75 was appropriate",
  "importance": 8  // 1-10 scale
}
```

**Philosophy**: Structured learning tied to specific trades. Agent reflects immediately after close when context is fresh.

#### 9. `query_trade_observations`
Search past observations for learning.

**Parameters**:
- `symbol` (optional): Filter by symbol
- `observation_type` (optional): win_analysis | loss_analysis
- `min_importance` (optional): Threshold filter
- `limit` (optional): Max results, default 10

**Use Cases**:
- "What have we learned about BTC trades?"
- Review before entering similar trade
- Strategy refinement discussions

---

### **Strategy Management Tools**

#### 10. `update_strategy`
Update trading strategy (experimental mode only).

**Requirements**:
- `agent_strategy.autonomously_editable: true` in config

**Parameters**:
- `new_strategy` (required): Updated strategy text
- `reason` (required): Why changing
- `performance_summary` (required): Results that motivated change

**Use Case**: Agent learns from performance and evolves approach (if permitted).

---

### **Timing Control Tools**

#### 11. `wait_for`
Agent controls its own timing (max 24 hours).

**Parameters**:
- `duration_minutes` (required): How long to sleep (max 1440)
- `reason` (optional): Why waiting (logged)

**Examples**:
- `wait_for(60, "Waiting for clearer market signal")`
- `wait_for(240, "Letting position develop")`
- `wait_for(15, "High volatility, checking frequently")`

**System Prompt Guidance**:
```
PATIENCE & TIMING:
- Markets need time to develop. Don't overthink or overquery.
- After entering with SL/TP, wait hours. Let it play out.
- Volatile: 15-30 min | Normal: 1-2 hours | Position running: 4-6 hours
```

---

### **Mode Management Tools**

#### 12. `save_strategy_and_exit`
Save strategy and exit strategy definition mode.

**Parameters**:
- `strategy_summary` (required): Final strategy text
- `autonomously_editable` (optional): Allow agent to modify, default false

**What Happens**:
1. Saves strategy to `config_data.agent_strategy`
2. Sets Redis flag for run_agent.py to detect
3. Deletes PM2 process (prevents auto-restart)
4. Logs activity to timeline

**User Action Required**: Click "Activate Agent" in UI to start autonomous mode.

---

## 🎭 Two Agent Modes

### **Strategy Definition Mode**

**Purpose**: Interactive conversation to build trading strategy

**Flow**:
1. Agent assesses user experience level
2. Shows available data sources (if needed)
3. Defines entry/exit conditions
4. Sets position sizing and risk management
5. Confirms monitoring frequency
6. Saves strategy via `save_strategy_and_exit`

**Key Features**:
- Educational for beginners (explains indicators)
- Validation for experts (checks feasibility)
- Grounded in reality (only suggests available data)
- No auto-activation (user must restart in autonomous mode)

### **Autonomous Mode**

**Purpose**: 24/7 trading execution with self-directed timing

**Flow**:
1. Startup checks (balance, positions, mode)
2. Query market data per strategy
3. Execute trades when conditions met
4. Use `wait_for` between actions
5. Record observations after closing
6. Repeat forever

**Key Features**:
- No user interaction needed
- Agent controls timing (no scheduled runs)
- Full position lifecycle management
- Automatic activity logging to timeline
- **Session persistence** - survives crashes, restarts, and compaction with full memory intact
- Health monitoring via periodic heartbeat updates

---

## 🔄 Session Persistence & Recovery

**Problem Solved**: Agents now remember their conversation history across crashes and restarts.

### How It Works

**Session Storage** (`agent_sessions` table):
- Stores Claude SDK `session_id` for each bot
- Tracks `last_active_at` for health monitoring
- Updates every 10 messages as heartbeat

**First Run**:
1. Agent starts, no session exists
2. SDK creates new session
3. Agent captures `session_id` from init message
4. Saves to database

**After Restart/Crash**:
1. Agent loads `session_id` from database
2. Passes to SDK via `ClaudeAgentOptions(resume=session_id)`
3. SDK automatically restores full conversation history
4. Agent continues from where it left off (not cold start!)

**After Auto-Compaction**:
- SDK compacts context at 95% token usage (summarizes old messages)
- Compacted state persists in session
- If agent crashes after compaction, resume loads compacted state
- Agent retains summarized context instead of complete amnesia

**Benefits**:
- ✅ Full conversation memory across restarts
- ✅ No more "amnesiac agent" problem
- ✅ Resilient to PM2 restarts and crashes
- ✅ Compaction doesn't erase history
- ✅ Continuous learning from past analysis

**Database Schema**:
```sql
CREATE TABLE agent_sessions (
    config_id UUID PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,  -- SDK session ID
    last_active_at TIMESTAMP,          -- Health monitoring
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Health Monitoring**:
- Agent updates `last_active_at` every 10 messages
- Can detect hung agents (no activity >30 minutes)
- Foundation for future auto-restart systems

**Documentation**: See `DOCS/completed/agent-session-resumption-implementation.md` for complete implementation details and testing instructions.

---

## 🔧 Configuration

### Environment Variables

```bash
# Agent Model (testing vs production)
AGENT_MODEL=claude-sonnet-4-5-20250929  # Smartest for agents ($3/$15 per MTok)
# AGENT_MODEL=claude-haiku-4-5-20251001  # Cheaper for testing ($1/$5 per MTok)

# Redis for message queues
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379

# API Authentication
SUPABASE_SERVICE_KEY=your-service-key-here  # For agent → API auth

# Trading Modes
# (Set in bot config, not .env)
```

### Bot Configuration

```json
{
  "config_id": "uuid",
  "config_type": "agent",
  "trading_mode": "paper",  // or "aster" or "live" (symphony)

  "config_data": {
    "agent_strategy": {
      "content": "Trade BTC conservatively. Entry: RSI < 30...",
      "autonomously_editable": false,
      "version": 1,
      "last_updated_at": "2025-11-06T10:00:00Z",
      "last_updated_by": "user",
      "performance_log": []
    },

    "selected_pair": "BTC/USDT",

    "trading": {
      "leverage": 10,
      "position_sizing": {
        "method": "ACCOUNT_PERCENTAGE",
        "account_percent": 10.0
      },
      "risk_management": {
        "default_stop_loss_percent": 2.0,
        "default_take_profit_percent": 5.0
      }
    }
  }
}
```

---

## 🧪 Testing

### Test MCP Tools

```bash
# Test all tools with mock data
python agent/test_mcp_tools.py

# Expected: All 12 tools respond with proper format
```

### Test Strategy Definition

```bash
# Terminal 1: Start agent
python agent/run_agent.py --config-id=<id> --mode=strategy_definition

# Terminal 2: Chat
python agent/chat.py --config-id=<id>

# Test flow:
# 1. Agent asks about experience
# 2. Discuss strategy
# 3. Agent saves and exits
# 4. Check database for saved strategy
```

### Test Autonomous Trading

```bash
# Start autonomous mode
python agent/run_agent.py --config-id=<id> --mode=autonomous

# Watch logs
tail -f logs/agent-debug.log

# Check activity timeline in UI
# Stop: Ctrl+C
```

---

## 📊 Monitoring

### Redis Queues

```bash
# Check message queues
redis-cli llen agent:<config_id>:messages
redis-cli llen agent:<config_id>:responses
redis-cli llen agent:<config_id>:history

# Read conversation history
redis-cli lrange agent:<config_id>:history 0 -1
```

### Database Queries

```sql
-- View agent strategy
SELECT config_data->'agent_strategy'
FROM configurations
WHERE config_id = 'uuid';

-- View agent decisions
SELECT * FROM decisions
WHERE created_by = 'agent'
ORDER BY created_at DESC;

-- View trade observations
SELECT * FROM trade_observations
WHERE config_id = 'uuid'
ORDER BY importance DESC, created_at DESC;

-- View activity timeline
SELECT * FROM activity_timeline
WHERE config_id = 'uuid' AND activity_source = 'agent_tool'
ORDER BY created_at DESC;
```

### Logs

```bash
# Agent debug logs (comprehensive)
tail -f logs/agent-debug.log

# Filter for specific config
grep "config_id=abc123" logs/agent-debug.log

# PM2 logs (if running as service)
pm2 logs agent-<config_id>
```

---

## 🐛 Troubleshooting

### Agent Won't Start

**Symptom**: Exits immediately after starting

**Check**:
1. Config exists in database: `SELECT * FROM configurations WHERE config_id = 'uuid'`
2. Strategy is saved (autonomous mode): Check `config_data.agent_strategy`
3. Redis is running: `redis-cli ping`
4. Virtual environment activated: `which python` → should show `.venv/bin/python`

### Tools Returning Errors

**Symptom**: Tool calls fail with 401/500 errors

**Check**:
1. API server running: `curl http://localhost:8000/health`
2. Service auth configured: Check `SUPABASE_SERVICE_KEY` in .env
3. Trading mode valid: Paper/Aster implemented, Symphony pending
4. Symbol compatibility: Use `/api/symbols/supported` to verify

### Agent Not Trading

**Symptom**: Agent waits forever, no trades executed

**Check**:
1. Strategy defines executable conditions: Not too strict
2. Market data queries working: Check logs for API errors
3. Balance available (Paper/Aster): Agent can't trade with $0
4. Symbol compatibility: Agent may be trying unsupported symbols

### Position Not Closing

**Symptom**: `close_position` returns error

**Check**:
1. Correct position ID: Use `get_positions` to get current IDs
2. Trading mode match: Paper uses `trade_id`, live uses `batch_id`
3. Position still open: May have hit SL/TP already
4. API timeout: Live trading may take 3-5 seconds

---

## 🔜 Symphony Live Trading Integration

**Status**: Waiting for Symphony API fixes
**Blocker**: `/agent/all-positions` endpoint returns 404 (documented but not implemented)

### What's Needed from Symphony Team

The following API endpoint must be fixed/implemented:

```
GET https://api.symphony.io/agent/all-positions?userAddress={WALLET_ADDRESS}

Headers: x-api-key: {API_KEY}

Expected Response:
{
  "success": true,
  "data": {
    "userAddress": "0x...",
    "accountSummary": {
      "totalEquity": 53.28,              // ← CRITICAL: Account balance
      "availableBalance": 45.29,         // ← CRITICAL: Free cash
      "marginUsed": 7.99,                // ← CRITICAL: Locked capital
      "totalRealizedPnl": -0.2,
      "totalUnrealizedPnl": 0,
      "totalPnl": -0.21,
      "totalFeesPaid": 0.17,
      "totalVolume": 139.75,
      "totalTrades": 1,
      "openPositionsCount": 1,
      "performance": {
        "roi": -1.72,
        "roiPercent": -3.12,
        "totalTrades": 1,
        "averageTradeSize": 49.99
      }
    },
    "openPositions": [...]
  }
}
```

**Why We Need This**:
- Current endpoints (`/agent/positions`, `/agent/batches`) don't expose balance
- Agents need balance for intelligent position sizing
- Single endpoint = better performance (1 call vs 3)
- Matches Aster's functionality (balance-aware trading)

### Current Symphony Service (Works, But Missing Balance)

The existing `SymphonyLiveTradingService` already implements:

```python
# trading/live/symphony_service.py

✅ execute_trade_intent(intent)           # Live trade execution
✅ close_position(batch_id, reason)       # Position closing
✅ get_open_positions(config_id)          # Open positions (no balance)
✅ get_account_metrics(config_id)         # Win rate, P&L (no balance)
✅ get_trade_history(config_id, limit)    # Closed trades

# What's missing:
❌ get_account_summary(user_id, wallet)   # Would use /agent/all-positions
```

### Integration Steps (Once API Fixed)

#### Step 1: Add New Method to Symphony Service

```python
# trading/live/symphony_service.py

async def get_account_summary(
    self,
    user_id: str,
    wallet_address: str
) -> Dict[str, Any]:
    """
    Get full account summary including balance from Symphony.

    Uses: GET /agent/all-positions?userAddress={wallet}

    Returns:
        {
            "totalEquity": float,
            "availableBalance": float,
            "marginUsed": float,
            "totalPnl": float,
            "performance": {...},
            "openPositions": [...]
        }
    """
    credentials = await VaultManager.get_symphony_credential(user_id)
    if not credentials:
        return {}

    api_key = credentials['api_key']
    url = f"{self.base_url}/agent/all-positions"

    headers = {"x-api-key": api_key}
    params = {"userAddress": wallet_address}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers, timeout=self.timeout) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('data', {})
            else:
                self._log.error(f"Symphony account summary error {response.status}")
                return {}
```

#### Step 2: Update `get_account_metrics` to Use New Endpoint

```python
# Replace existing multi-call approach with single call

async def get_account_metrics(self, config_id: str) -> Dict[str, Any]:
    # Get wallet address from database
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, wallet_address
                FROM configurations
                WHERE config_id = %s
            """, (config_id,))
            result = cur.fetchone()
            user_id, wallet_address = result

    # NEW: Single API call instead of 3
    summary = await self.get_account_summary(user_id, wallet_address)
    account_summary = summary.get('accountSummary', {})

    return {
        'config_id': config_id,
        'current_balance': account_summary.get('totalEquity'),      # ← NOW AVAILABLE!
        'available_balance': account_summary.get('availableBalance'), # ← BONUS!
        'margin_used': account_summary.get('marginUsed'),            # ← BONUS!
        'total_pnl': account_summary.get('totalPnl', 0),
        'total_trades': account_summary.get('totalTrades', 0),
        'win_rate': account_summary.get('performance', {}).get('roiPercent', 0) / 100,
        'open_positions': account_summary.get('openPositionsCount', 0)
    }
```

#### Step 3: Add Symphony Branches to Agent Endpoints

```python
# api/agent.py - Add to all 5 agent endpoints

# 1. Execute Trade (line ~434)
elif trading_mode == 'live':  # Symphony
    from trading.live.symphony_service import SymphonyLiveTradingService
    symphony_service = SymphonyLiveTradingService()
    result = await symphony_service.execute_trade_intent(intent)

# 2. Get Positions (line ~503)
elif trading_mode == 'live':
    symphony_service = SymphonyLiveTradingService()
    positions = await symphony_service.get_open_positions(config_id)
    # Transform to agent format (already done by service)

# 3. Get Account Status (line ~578)
elif trading_mode == 'live':
    symphony_service = SymphonyLiveTradingService()
    metrics = await symphony_service.get_account_metrics(config_id)
    # Now includes balance!

# 4. Close Position (line ~625)
elif trading_mode == 'live':
    symphony_service = SymphonyLiveTradingService()
    result = await symphony_service.close_position(trade_id, "agent_decision")

# 5. Cancel Order (line ~687)
elif trading_mode == 'live':
    # Symphony doesn't support standalone order cancellation
    raise HTTPException(status_code=400,
        detail="Symphony uses batch-based orders. Close position instead.")
```

#### Step 4: Update Agent System Prompt

```python
# agent/run_agent.py - _build_system_prompt()

if trading_mode == "live":  # Symphony
    base_prompt += """
🌐 SYMPHONY LIVE TRADING MODE:

FEATURES (AFTER API FIX):
1. ✅ Balance Available: totalEquity, availableBalance, marginUsed
2. ✅ Position Sizing: Percentage-based (converted from USD amounts)
3. ✅ Account Metrics: Full performance tracking with ROI
4. ⚠️  Order Management: Batch-based (close entire position, not individual orders)

WORKFLOW:
1. Check account status (balance now available!)
2. Query market data for opportunities
3. Execute with SL/TP (required)
4. Monitor positions, close manually if needed
5. Record observations

SYMPHONY STRENGTHS:
- Real money execution
- Non-custodial trading
- Professional infrastructure
- Full balance visibility (after fix)
"""
```

#### Step 5: Update Tool Responses

```python
# agent/mcp_server.py - get_account_status tool

if trading_mode == "live":  # Symphony (AFTER FIX)
    account_text = f"""
📊 Account Status (Symphony Live Trading)

Balance: ${balance:,.2f}                    # ← NOW AVAILABLE!
Available Balance: ${available:,.2f}        # ← FREE CASH
Margin Used: ${margin_used:,.2f}            # ← LOCKED
Total P&L: ${account.get('total_pnl', 0):,.2f}
Win Rate: {account.get('win_rate', 0):.1%}
Open Positions: {account.get('open_positions', 0)}

💡 Symphony now provides full balance visibility!
"""
```

### Database Schema Changes (Minor)

```sql
-- Add wallet_address to configurations (if not exists)
ALTER TABLE configurations
ADD COLUMN wallet_address VARCHAR(42);  -- Ethereum address

-- Update existing Symphony configs
UPDATE configurations
SET wallet_address = '0x...'
WHERE trading_mode = 'live' AND symphony_agent_id IS NOT NULL;
```

### Testing Checklist (Post-Fix)

```bash
# 1. Test API endpoint directly
curl -H "x-api-key: $SYMPHONY_API_KEY" \
  "https://api.symphony.io/agent/all-positions?userAddress=0x..."

# 2. Test Symphony service method
python -c "
import asyncio
from trading.live.symphony_service import SymphonyLiveTradingService
svc = SymphonyLiveTradingService()
result = asyncio.run(svc.get_account_summary('user_id', '0x...'))
print(result)
"

# 3. Test agent endpoint
curl -H "Authorization: Bearer $SERVICE_KEY" \
     -H "x-service-auth: agent-runner" \
  "http://localhost:8000/api/v2/agent/account/<config_id>?user_id=<user_id>"

# 4. Test full agent flow
python agent/run_agent.py --config-id=<symphony-config> --mode=autonomous

# Expected: Agent queries balance, executes trades, monitors positions
```

### Estimated Integration Time (After API Fix)

- **Symphony Service Update**: 30 mins (add new method, update existing)
- **Agent Endpoint Branches**: 45 mins (5 endpoints + testing)
- **System Prompt Updates**: 15 mins (mode-aware instructions)
- **Database Migration**: 5 mins (add wallet_address column)
- **End-to-End Testing**: 1 hour (strategy definition → autonomous)

**Total**: ~2.5 hours of focused development

---

## 📚 Additional Resources

- **Architecture Details**: See `DOCS/todo/AGENT.md` for complete design decisions
- **Trading README**: See `trading/README.md` for trading engine details
- **Symbol Registry**: See `core/symbols/registry.py` for supported symbols
- **Activity Logging**: See `core/common/activity_logger.py` for timeline integration

---

## 🎯 Current Limitations & Known Issues

1. **Single Agent Per Bot**: Multi-agent support (closure pattern) planned for Phase 4
2. **Symphony Integration**: Pending API fixes (balance endpoint) - see Symphony section for details
3. **Session Longevity**: Unknown if sessions expire after extended periods (needs testing)
4. **Frontend Integration**: Agent chat UI complete, but strategy builder UX pending refinement

**Fixed in 2025-11-08**:
- ✅ **Session Persistence**: Agents now survive crashes/restarts with full memory (was: context loss on restart)
- ✅ **AsterDEX UUID Bug**: Trade close events now log correctly (was: invalid UUID errors)
- ✅ **Compaction Recovery**: SDK handles compaction gracefully with session resumption (was: manual context injection)

---

**For questions or issues**: See troubleshooting section or check `logs/agent-debug.log`
