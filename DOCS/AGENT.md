# Autonomous Trading Agent - Architecture & Implementation

**Status**: Planning
**Timeline**: 1-2 weeks
**Purpose**: Enable fully autonomous AI trading agents using Claude Agent SDK with ggbots infrastructure

---

## Executive Summary

Transform ggbots from a **bot platform** (scheduled execution) into an **agent infrastructure platform** (autonomous AI decision-making).

**Key Innovation**: Agent IS the orchestrator and decision engine. Uses existing extraction/trading services as tools.

**Architecture Pattern**:
```
Agent (Claude Opus) - Full autonomy over timing and decisions
  ├─ Tool: query_market_data → Extraction Service
  ├─ Agent reasons about market conditions
  ├─ Tool: execute_trade → Trading Service
  ├─ Tool: get_positions → Database query
  └─ Tool: close_position → Trading Service
```

**vs Traditional Bot**:
```
Scheduler (fixed 1h/4h/1d)
  → Orchestrator
    → Extraction Service (get data)
    → Decision Engine (AI decides)
    → Trading Service (execute)
```

---

## Core Architecture Decisions

### **1. Agent = Orchestrator + Decision Engine**

**Agent Replaces:**
- ❌ Orchestrator (agent decides when to run what)
- ❌ Decision Engine (agent IS the decision maker)
- ❌ Scheduler (agent controls own timing)

**Agent Uses:**
- ✅ Extraction Service (fetch market data)
- ✅ Trading Service (execute trades)
- ✅ Config System (dynamic state storage)
- ✅ Database (position/account queries)

**Why**: Having TWO AIs make decisions (agent + decision engine) is redundant. Agent should make all decisions directly.

---

### **2. One Agent = One Config**

**Config Strategy**:
- Each agent instance gets its own `config_id`
- Config type: `"agent"` (distinguishes from `"autonomous_trading"` bots)
- Each agent has isolated paper trading account ($10K starting balance)
- Each agent's performance tracked independently

**Benefits**:
- **Multi-Agent Support**: User can run multiple agents with different strategies
- **Isolated Tracking**: Each agent's P&L tracked separately
- **Independent Risk**: One agent blowing up doesn't affect others
- **Dashboard Clarity**: "My Bots" vs "My Agents" sections

**Example**:
```python
User has 3 agents running:
├─ Agent: Conservative BTC ($10,842, +8.42%)
├─ Agent: Aggressive Alts ($9,234, -7.66%)
└─ Agent: Macro Focused ($11,456, +14.56%)

Each with own config_id, paper account, trade history
```

---

### **3. Config = Dynamic Agent State**

**Agent updates its own config via tools:**

```python
# Agent wants BTC data with RSI and sentiment
query_market_data(symbol="BTC/USDT", indicators=["RSI_1h"], data_sources=["sentiment"])

# Tool updates config:
PATCH /api/v2/config/{agent_config_id}
{
    "selected_pair": "BTC/USDT",
    "extraction": {
        "data_sources": {
            "technical_indicators": ["RSI_1h"],
            "sentiment_and_trends": ["twitter_sentiment"]
        }
    }
}

# Then calls extraction service (which reads updated config)
```

**Config is agent's working memory:**
- Changes per agent decision
- Full audit trail of what agent requested
- Dashboard shows "Agent is currently analyzing ETH with MACD + news"

---

### **4. Tools Call Services Directly (Not Orchestrator)**

**Direct Service Pattern**:

| Tool | Service Called | Config Needed? |
|------|----------------|----------------|
| `query_market_data` | Extraction Service | ✅ Yes (reads config) |
| `execute_trade` | Trading Service | ❌ No (just intent dict) |
| `get_positions` | Database | ❌ No (direct query) |
| `close_position` | Trading Service | ❌ No (just trade_id) |
| `get_account_status` | Database | ❌ No (direct query) |

**Why Not Orchestrator?**
- Orchestrator runs full pipeline: extraction → decision → trading
- Agent only needs individual services
- Agent IS the decision maker (no need for decision engine)

---

## Implementation Architecture

### **File Structure**
```
agent/
├── __init__.py
├── mcp_server.py           # MCP tool definitions (Claude Agent SDK)
├── config_manager.py       # Agent config CRUD operations
├── service_client.py       # Wrappers for extraction/trading services
├── run_agent.py            # Main agent runner with Claude SDK loop
└── README.md               # Agent usage guide
```

---

### **Tool Suite Design**

#### **Tool 1: `query_market_data`**

**Purpose**: Get market data with custom indicators

**Input Schema**:
```python
{
    "symbol": str,           # "BTC/USDT"
    "indicators": list,      # ["RSI_1h", "MACD_4h", "BB_1h"]
    "timeframes": list,      # ["1h", "4h"]
    "data_sources": list     # ["sentiment", "news", "funding_rate"]
}
```

**Implementation**:
```python
@tool("query_market_data", ...)
async def query_market_data(args):
    # 1. Update agent config
    await update_agent_config({
        "selected_pair": args["symbol"],
        "extraction": {
            "data_sources": {
                "technical_indicators": args["indicators"],
                "sentiment_and_trends": build_sentiment_config(args["data_sources"]),
                "onchain_analytics": build_onchain_config(args["data_sources"])
            }
        }
    })

    # 2. Load config (same pattern as orchestrator)
    config = await config_service.get_config(AGENT_CONFIG_ID, AGENT_USER_ID)

    # 3. Call extraction service directly
    extraction_engine = ExtractionEngineV2(user_id=AGENT_USER_ID)
    result = await extraction_engine.extract_for_config(
        config=config,
        user_id=AGENT_USER_ID,
        requested_indicators=args["indicators"],
        timeframes=args["timeframes"]
    )

    # 4. Format for agent consumption
    return format_market_data_for_agent(result)
```

**Output**:
```
Market Analysis for BTC/USDT:

Current Price: $96,200

Technical Indicators:
  RSI_1h: 65 (bullish momentum)
  MACD_4h: Bullish crossover
  BB_1h: Price at upper band (potential resistance)

Sentiment: 78/100 (optimistic)
Funding Rate: 2.1% (overleveraged longs - caution)
```

---

#### **Tool 2: `execute_trade`**

**Purpose**: Execute a paper trade with agent's decision

**Input Schema**:
```python
{
    "symbol": str,
    "action": str,           # "long" | "short"
    "size_usd": float,       # Position size in dollars
    "stop_loss_pct": float,  # Stop loss percentage
    "take_profit_pct": float,
    "reasoning": str         # Agent's full reasoning
}
```

**Implementation**:
```python
@tool("execute_trade", ...)
async def execute_trade(args):
    # Get current price
    current_price = await get_current_price(args["symbol"])

    # Calculate SL/TP prices
    if args["action"] == "long":
        sl_price = current_price * (1 - args["stop_loss_pct"] / 100)
        tp_price = current_price * (1 + args["take_profit_pct"] / 100)
    else:
        sl_price = current_price * (1 + args["stop_loss_pct"] / 100)
        tp_price = current_price * (1 - args["take_profit_pct"] / 100)

    # Create trading intent (agent's decision)
    intent = {
        "decision_id": str(uuid.uuid4()),
        "user_id": AGENT_USER_ID,
        "config_id": AGENT_CONFIG_ID,
        "symbol": args["symbol"],
        "action": args["action"],
        "confidence": 1.0,  # Agent is certain
        "stop_loss_price": sl_price,
        "take_profit_price": tp_price,
        "reasoning": args["reasoning"]
    }

    # Call trading service directly (NO decision engine, NO orchestrator)
    paper_service = SupabasePaperTradingService()
    result = await paper_service.execute_trade_intent(intent)

    return format_trade_result_for_agent(result)
```

**Output**:
```
✅ Trade executed successfully!

Action: LONG
Symbol: BTC/USDT
Size: $500.00
Entry: $96,200.00
Stop Loss: $93,266.00 (3%)
Take Profit: $102,012.00 (6%)
Trade ID: abc-123-def
```

---

#### **Tool 3: `get_positions`**

**Purpose**: View all open positions

**Implementation**:
```python
@tool("get_positions", ...)
async def get_positions(args):
    # Direct DB query (same as API endpoint)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT symbol, side, entry_price, current_price,
                       size_usd, unrealized_pnl, trade_id, opened_at
                FROM paper_trades
                WHERE config_id = %s AND user_id = %s AND status = 'open'
                ORDER BY opened_at DESC
            """, (AGENT_CONFIG_ID, AGENT_USER_ID))

            positions = cur.fetchall()

    return format_positions_for_agent(positions)
```

**Output**:
```
Open Positions (2):

• BTC/USDT LONG
  Size: $500.00
  Entry: $96,200.00
  Current: $96,850.00
  P&L: +$6.50

• ETH/USDT SHORT
  Size: $300.00
  Entry: $3,420.00
  Current: $3,380.00
  P&L: +$3.20
```

---

#### **Tool 4: `close_position`**

**Purpose**: Close a specific position

**Input Schema**:
```python
{
    "trade_id": str,
    "reasoning": str
}
```

**Implementation**:
```python
@tool("close_position", ...)
async def close_position(args):
    # Call trading service directly
    paper_service = SupabasePaperTradingService()
    result = await paper_service.close_position(
        trade_id=args["trade_id"],
        reason=args["reasoning"]
    )

    return format_close_result_for_agent(result)
```

---

#### **Tool 5: `get_account_status`**

**Purpose**: Check balance and performance

**Implementation**:
```python
@tool("get_account_status", ...)
async def get_account_status(args):
    # Direct DB query for account metrics
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT balance, total_pnl, total_trades, win_rate
                FROM paper_accounts
                WHERE config_id = %s
            """, (AGENT_CONFIG_ID,))

            account = cur.fetchone()

    return format_account_for_agent(account)
```

**Output**:
```
Account Status:

Balance: $10,842.00
Total P&L: $842.00
Total Trades: 24
Win Rate: 62.5%
Open Positions: 2
```

---

#### **Tool 6: `wait_for`**

**Purpose**: Agent controls its own timing

**Input Schema**:
```python
{
    "seconds": int,
    "reason": str
}
```

**Implementation**:
```python
@tool("wait_for", ...)
async def wait_for(args):
    """
    Log wait reason for monitoring.
    Agent SDK handles actual sleep.
    """
    next_check = datetime.utcnow() + timedelta(seconds=args["seconds"])

    logger.info(f"Agent waiting {args['seconds']}s: {args['reason']}")

    return {
        "content": [{
            "type": "text",
            "text": f"⏳ Waiting {args['seconds']} seconds\n"
                    f"Reason: {args['reason']}\n"
                    f"Next check: {next_check.strftime('%H:%M:%S')} UTC"
        }]
    }
```

---

## Agent Runner Implementation

### **Agent Loop Pattern**

```python
# agent/run_agent.py

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from .mcp_server import ggbots_trading_server
import asyncio

async def run_trading_agent(user_id: str, strategy: str):
    """Run autonomous trading agent."""

    # Create agent config
    agent_config_id = await create_agent_config(user_id, strategy)

    # Set environment
    os.environ["AGENT_CONFIG_ID"] = agent_config_id
    os.environ["AGENT_USER_ID"] = user_id

    # Configure agent
    options = ClaudeAgentOptions(
        mcp_servers={"ggbots-trading": ggbots_trading_server},
        allowed_tools=[
            "mcp__ggbots-trading__query_market_data",
            "mcp__ggbots-trading__execute_trade",
            "mcp__ggbots-trading__get_positions",
            "mcp__ggbots-trading__close_position",
            "mcp__ggbots-trading__get_account_status",
            "mcp__ggbots-trading__wait_for"
        ],
        model="claude-opus-4-20250514",
        max_turns=50
    )

    system_prompt = f"""
    You are an autonomous cryptocurrency trading agent.

    Strategy: {strategy}

    Your tools:
    - query_market_data: Check market data, indicators, sentiment
    - execute_trade: Open positions (long or short)
    - get_positions: Monitor open trades
    - close_position: Exit positions
    - get_account_status: Check balance and performance
    - wait_for: Sleep until next market check

    You decide:
    - WHEN to check markets (not on a schedule)
    - WHAT data to analyze
    - WHEN to trade
    - HOW LONG to wait between checks

    Always explain your reasoning clearly.
    Be thoughtful about risk.
    """

    # Run agent
    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Start autonomous trading: {strategy}. "
            "Check markets, analyze, and trade as you see fit."
        )

        # Stream responses
        async for message in client.receive_response():
            print(f"\n[Agent]: {message}")
```

---

## Database Integration

### **Agent Config Creation**

```python
async def create_agent_config(user_id: str, strategy: str) -> str:
    """Create config for agent instance."""

    config = {
        "config_name": f"Agent: {strategy}",
        "config_type": "agent",  # NEW: distinguishes from bots
        "selected_pair": "BTC/USDT",
        "extraction": {
            "data_sources": {
                "technical_indicators": ["RSI_1h"],
                "sentiment_and_trends": [],
                "news_and_regulations": [],
                "onchain_analytics": []
            }
        },
        "decision": {
            "analysis_frequency": "agent_driven",
            "user_prompt": f"Strategy: {strategy}"
        },
        "trading": {
            "execution_mode": "paper",
            "position_sizing": {
                "method": "confidence_based",
                "max_position_percent": 10.0
            },
            "risk_management": {
                "max_positions": 3,
                "default_stop_loss_percent": 3.0,
                "default_take_profit_percent": 6.0
            }
        },
        "llm_config": {
            "provider": "anthropic",
            "model": "claude-opus-4",
            "use_platform_keys": True
        }
    }

    # Create via API
    result = await call_api("/api/v2/config", method="POST", json=config)
    config_id = result["config_id"]

    # Initialize paper account
    paper_service = SupabasePaperTradingService()
    await paper_service.initialize_account(config_id, user_id)

    return config_id
```

### **Decision Records**

Agent decisions stored with `created_by = 'agent'`:

```sql
INSERT INTO decisions (
    decision_id,
    config_id,
    symbol,
    action,
    reasoning,
    confidence,
    created_by
) VALUES (
    'abc-123',
    'agent-config-456',
    'BTC/USDT',
    'long',
    'Agent reasoning: BTC at support with RSI oversold, funding normalized...',
    1.0,
    'agent'  -- vs 'decision_engine' for bots
);
```

**Audit Trail Benefits**:
- Distinguish agent decisions from bot decisions
- Full reasoning preserved
- Dashboard shows "Agent made this decision at 14:32"

---

## Infrastructure Requirements

### **Zero Changes to Existing Services**

All services already support dynamic parameters:

| Service | How It Works | Agent Usage |
|---------|-------------|-------------|
| **Extraction** | Reads `config.selected_pair`, `config.extraction` | Agent updates config, calls extraction |
| **Trading** | Accepts intent dict with all params | Agent passes intent directly |
| **Positions** | Direct DB query via endpoints | Agent queries same endpoints |
| **Account** | Direct DB query via endpoints | Agent queries same endpoints |

**Only New Code**:
- MCP server (tool definitions) - `agent/mcp_server.py`
- Agent runner (Claude SDK loop) - `agent/run_agent.py`
- Config helpers - `agent/config_manager.py`
- Service wrappers - `agent/service_client.py`

### **Missing Endpoint: Paper Position Close**

Currently exists for live trading, need to add for paper:

```python
# In ggbot.py

@app.post("/api/v2/positions/paper/{trade_id}/close")
async def close_paper_position(
    trade_id: str,
    reason: str = "manual",
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Close a paper trading position."""
    paper_service = SupabasePaperTradingService()
    result = await paper_service.close_position(trade_id, reason)
    return result
```

---

## Agent Behavior Examples

### **Example 1: Conservative Strategy**

**User**: "Run agent with conservative BTC strategy"

**Agent Loop**:
```
[10:00] Agent: Let me check BTC conditions
[10:00] Tool: query_market_data(BTC, indicators=[RSI_1h, MACD_4h], data_sources=[funding_rate])
[10:01] Agent: BTC at $96,200. RSI 65 (bullish), but funding 2.1% (overleveraged).
               I'll wait for funding to normalize.
[10:01] Tool: wait_for(1800, "Waiting for funding rate to normalize")

[10:30] Agent: Time to recheck
[10:30] Tool: query_market_data(BTC, indicators=[RSI_1h], data_sources=[funding_rate])
[10:31] Agent: Funding down to 0.8%, RSI still 63. Good setup, I'll enter small.
[10:31] Tool: execute_trade(BTC, long, $300, sl=3%, tp=6%, reasoning="...")

[11:00] Agent: Let me check my position
[11:00] Tool: get_positions()
[11:01] Agent: BTC position up $12. Still healthy. I'll hold.
[11:01] Tool: wait_for(3600, "Position profitable, checking again in 1h")

[12:00] Agent: Position check
[12:00] Tool: get_positions()
[12:01] Agent: BTC hit take profit! Closing.
[12:01] Tool: close_position(trade_id=abc-123, reasoning="Take profit target hit")
```

---

### **Example 2: Multi-Asset Strategy**

**User**: "Run agent that trades BTC and ETH based on macro trends"

**Agent Loop**:
```
[14:00] Agent: Let me check macro environment first
[14:00] Tool: query_market_data(BTC, indicators=[RSI_1h], data_sources=[sentiment, news])
[14:01] Agent: VIX spiked to 32 (high fear), crypto sentiment 45/100 (bearish).
               This is risk-off environment. I'll stay in cash.
[14:01] Tool: wait_for(7200, "Risk-off macro, waiting 2h")

[16:00] Agent: Recheck macro
[16:00] Tool: query_market_data(BTC, data_sources=[sentiment])
[16:01] Agent: Sentiment improving to 62/100. Let me check both BTC and ETH.
[16:01] Tool: query_market_data(BTC, indicators=[RSI_1h, MACD_4h])
[16:02] Tool: query_market_data(ETH, indicators=[RSI_1h, MACD_4h])
[16:03] Agent: BTC: RSI 58 (neutral), ETH: RSI 42 (oversold), both MACD bullish.
               ETH has better setup. I'll go long ETH.
[16:03] Tool: execute_trade(ETH, long, $400, sl=3%, tp=8%, reasoning="...")
```

---

## Dashboard Integration

### **Bot List Enhancement**

**Filter by config_type**:

```typescript
// Frontend: Show bots and agents separately

const bots = allConfigs.filter(c => c.config_type === "autonomous_trading")
const agents = allConfigs.filter(c => c.config_type === "agent")

return (
  <>
    <BotList bots={bots} />
    <AgentList agents={agents} />
  </>
)
```

**Display**:
```
My Bots (3):
├─ BTC Scalper (1h) - Active - $10,234 (+2.34%)
├─ ETH Swing (4h) - Inactive - $9,876 (-1.24%)
└─ SOL Momentum (15m) - Active - $11,456 (+14.56%)

My Agents (2):
├─ Agent: Conservative BTC - Active - $10,842 (+8.42%)
│  └─ Current: Analyzing BTC/USDT with RSI, MACD, Sentiment
└─ Agent: Aggressive Alts - Active - $9,234 (-7.66%)
   └─ Current: Waiting 30min (funding too high)
```

---

## Success Metrics

**Phase 1** (Week 1):
- ✅ MCP server with 6 tools implemented
- ✅ Agent can query market data
- ✅ Agent can execute trades
- ✅ Agent can manage positions
- ✅ Full audit trail in database

**Phase 2** (Week 2):
- ✅ Agent runs autonomously for 24h+
- ✅ Multiple agents can run simultaneously
- ✅ Dashboard shows agent activity
- ✅ Agent makes profitable trades (baseline test)

---

## Future Enhancements

### **Multi-Agent Coordination**
- Agents can communicate via shared context
- "Agent 1: I'm long BTC" → "Agent 2: I'll avoid correlated positions"

### **Strategy Library**
- Pre-built strategy templates
- "Conservative Swing Trader"
- "Aggressive Scalper"
- "Macro Trend Follower"

### **Agent Learning**
- Track agent performance by strategy type
- "Conservative strategies win 65% vs Aggressive 48%"
- Recommend strategy adjustments

### **User Interaction**
- Mid-trade chat: "Why did you enter BTC here?"
- Strategy refinement: "Be more conservative on weekends"
- Real-time reasoning display in dashboard

---

## Related Documentation

- **Agent SDK Reference**: `DOCS/agent-sdk/OVERVIEW.md`
- **Custom Tools Guide**: `DOCS/agent-sdk/CUSTOM_TOOLS.md`
- **MCP Documentation**: `DOCS/agent-sdk/MCP.md`
- **Trading Infrastructure**: `README.md`
- **Current TODO**: `TODO.md`

---

**Last Updated**: 2025-01-26
**Status**: Architecture Complete - Ready for Implementation
**Next Step**: Begin MCP server implementation
