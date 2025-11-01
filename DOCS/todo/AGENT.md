# Autonomous Trading Agent - Architecture & Implementation

**Status**: Phase 2 Complete (MCP Server) → Phase 3 Ready (Agent Runner)
**Timeline**: Weeks 1-2 complete, Week 3 starting
**Purpose**: Enable fully autonomous AI trading agents using Claude Agent SDK with ggbots infrastructure
**Last Updated**: 2025-10-28 (Phase 3 & 4 implementation plan finalized with SDK clarity)

---

## SDK Verification Notes

**Verified Against**: Official Claude Agent SDK documentation, GitHub source code, and Anthropic docs

**Model Strategy**:
- **Testing/Development**: `claude-haiku-4-5-20251001` ($1/$5 per MTok - 3x cheaper)
- **Production**: `claude-sonnet-4-5-20250929` ($3/$15 per MTok - "smartest for agents")
- **Rationale**: Test with Haiku to iterate cheaply, upgrade to Sonnet for superior trading decisions

**Key Architecture Decisions** (Verified via DOCS/RESEARCH.md):
1. ✅ **Streaming mode**: Use `ClaudeSDKClient` with two async tasks (agent loop + user interrupts)
2. ✅ **receive_messages()**: Streams indefinitely for autonomous loop
3. ✅ **receive_response()**: Streams until ResultMessage for user queries
4. ✅ **client.interrupt()**: Stops mid-execution when user sends message
5. ✅ **Tool context access**: Module-level state pattern for Phase 3, closure pattern for Phase 4
6. ✅ **Compaction**: SDK auto-compacts at 95%, inject fresh context in Phase 4
7. ✅ **System prompt**: Set via `ClaudeAgentOptions.system_prompt` at init (cannot change mid-session)
8. ✅ **MCP integration**: Pass via `ClaudeAgentOptions(mcp_servers={"name": server})`
9. ✅ **Tool naming**: Tools prefixed as `mcp__server-name__tool-name`
10. ✅ **Redis queue**: Production-ready from day 1, API/frontend use same queues in Phase 4

---

## Executive Summary

Transform ggbots from a **bot platform** (scheduled execution) into an **agent infrastructure platform** (autonomous AI decision-making).

**Key Innovation**: Agent IS the orchestrator and decision engine. Two distinct modes:

1. **Conversation Mode**: Collaborate with user to define strategy
2. **Autonomous Mode**: Execute 24/7 with self-controlled timing via `wait_for` tool

**Two Agent Personalities**:

- **Guided Mode** (`autonomously_editable: false`): Execute user-defined strategy faithfully
- **Experimental Mode** (`autonomously_editable: true`): Full autonomy to evolve strategy over time

---

## Core Architecture Decisions

### **1. Two-Phase Agent System**

```python
# Agent Flow
User creates agent → [CONVERSATION MODE] → Strategy confirmed → [AUTONOMOUS MODE]
                                                                      ↓
                                                            24/7 trading with wait_for
                                                            User can send messages
```

**Conversation Mode**:
- Interactive strategy building with user
- Back-and-forth refinement
- Confirmation: "Proceed with this strategy?"
- **No database persistence** - ephemeral chat in SDK memory
- Only **final strategy** saved to `config_data.agent_strategy`

**Autonomous Mode**:
- 24/7 execution with agent-controlled timing
- Agent uses `wait_for` tool to sleep between checks
- User can send messages via Redis queue
- Agent responds while continuing trading
- Decisions logged to `decisions` table with `created_by='agent'`

---

### **2. Autonomously Editable Flag**

**Two distinct agent types via single flag:**

```json
{
  "agent_strategy": {
    "content": "Current strategy description...",
    "autonomously_editable": false,  // or true
    "version": 1,
    "last_updated_at": "2025-01-26T14:30:00Z",
    "last_updated_by": "user",  // or "agent"
    "performance_log": [...]
  }
}
```

**Guided Mode** (`autonomously_editable: false`):
- Agent executes user-defined strategy faithfully
- Can learn tactical patterns (via `record_learning`)
- **Cannot modify core strategy** without user approval
- User updates strategy by re-entering conversation mode

**Experimental Mode** (`autonomously_editable: true`):
- Agent has **full strategic autonomy**
- Can test different approaches
- Updates strategy via `update_strategy` tool
- Measures performance, evolves tactics
- User provides broad mandate ("Trade BTC, max 10% risk")

---

### **3. Minimal Database Changes**

**Total additions: 1 field + 1 table**

```sql
-- 1. Distinguish agent decisions from bot decisions
ALTER TABLE decisions ADD COLUMN created_by TEXT DEFAULT 'decision_engine_v2';
-- Values: 'decision_engine_v2' | 'agent' | 'signal_validation'

-- 2. Store post-trade reflections and learnings (RENAMED from agent_memory)
CREATE TABLE trade_observations (
    observation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID NOT NULL REFERENCES configurations(config_id),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    trade_id UUID NOT NULL REFERENCES paper_trades(trade_id),

    -- Post-trade reflection
    observation_type TEXT CHECK (observation_type IN ('win_analysis', 'loss_analysis')),
    what_went_well TEXT,
    what_went_wrong TEXT,
    predictive_data_points JSONB,  -- Which data points were most useful
    decision_review TEXT,  -- Review of original entry reasoning

    -- Metadata
    trade_pnl DECIMAL(20,8),
    trade_duration_minutes INTEGER,
    importance INTEGER DEFAULT 5 CHECK (importance BETWEEN 1 AND 10),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX (config_id, importance DESC, created_at DESC),
    INDEX (trade_id),
    INDEX (config_id, observation_type, created_at DESC)
);
```

**Design Philosophy**: Trade observations are triggered after closing positions. Agent reflects on what worked/failed, which data points were predictive. User + agent review observations together to refine strategy.

**What we reuse** (no changes needed):
- `configurations` table with `config_type='agent'`
- `paper_accounts`, `paper_trades` - trading infrastructure works as-is
- `decisions` - stores all AI decisions with reasoning
- Existing API endpoints - paper close endpoint exists at `POST /api/v2/paper/{config_id}/positions/{trade_id}/close`

---

### **4. Strategy Storage**

**Strategy lives in `config_data.agent_strategy`:**

```json
{
  "config_type": "agent",
  "config_data": {
    "agent_strategy": {
      "content": "Trade BTC conservatively. Entry: RSI < 30, funding < 1.5%. Position: 5% size, 2% SL, 6% TP. Check every 2h.",
      "autonomously_editable": false,
      "version": 1,
      "last_updated_at": "2025-01-26T14:30:00Z",
      "last_updated_by": "user",
      "performance_log": [
        {
          "version": 1,
          "period": "2025-01-20 to 2025-01-26",
          "trades": 15,
          "win_rate": 0.53,
          "pnl": 234.50
        }
      ]
    },
    "selected_pair": "BTC/USDT",
    "trading": {...},
    "risk_management": {...}
  }
}
```

**Conversation → Strategy Flow**:
1. User and agent converse (ephemeral, in SDK memory)
2. Agent: "Here's the strategy I understand: [summary]. Proceed?"
3. User: "Yes"
4. Save to `config_data.agent_strategy.content`
5. Switch to autonomous mode

**No chat history in database** - only the outcome (strategy) is persisted.

---

## Implementation Architecture

### **File Structure**

```
agent/
├── __init__.py
├── mcp_server.py           # 7 MCP tool definitions (@tool decorators)
├── config_manager.py       # Agent config CRUD operations
├── service_client.py       # Wrappers for extraction/trading/DB services
├── run_agent.py            # Main agent runner with ClaudeSDKClient
└── README.md               # Agent usage guide
```

---

## Tool Suite Design (9 Tools)

### **Architecture Notes**

**Multi-Agent Scalability**:
- **Phase 2 (Testing)**: Module-level state (single agent, simple)
- **Phase 4 (Production)**: Closure pattern (each agent gets own tool instances, thread-safe)

**Market Data = Data Points**:
- Agent queries specific data points by name (from `data_points` table)
- One unified tool, not 24 separate tools
- Data points organized by `data_sources` (technical analysis, derivatives, macro, etc.)

**Position Sizing**:
- Agent can override config defaults for position size and leverage
- Trade intents accept optional `size_usd` and `leverage` params
- Default behavior: Use config's `risk_per_trade` + `leverage` settings

---

### **Tool 1: `query_market_data`**

**Purpose**: Query any supported data points from catalog

**Architecture**: One tool with data point names as arguments. Agent receives catalog of available data points from `data_points` table organized by `data_sources`.

**CRITICAL IMPLEMENTATION NOTES**:

1. **Tool Descriptions**: The @tool decorator's description parameter is the ONLY thing the agent sees. Python docstrings are NOT exposed to the model. ALL category names and data point lists MUST be in the description string, not in function docstrings.

2. **Symbol Normalization**: The agent can send symbols in any format (BTC, BTCUSDT, BTC-USDT, BTC/USDT). The API automatically normalizes to CCXT format (BTC/USDT) using UniversalSymbolStandardizer. This works for all 142 registered symbols with fallback logic for others.

3. **Category Validation**: Invalid category names are caught server-side and return helpful error messages listing valid categories, preventing silent failures.

**Schema**:
```python
{
    "symbol": str,                    # "BTCUSDT"
    "categories": dict,               # {"technical_analysis": ["RSI"], "trading_signals": ["ggshot"]}
    "timeframe": str                  # "1h" (default)
}
```

**Examples**:
- Technical only: `["RSI", "MACD", "BB"]`
- Intelligence only: `["vix", "btc_funding_rate", "twitter_sentiment"]`
- Mixed: `["RSI", "vix", "btc_funding_rate"]`
- Config defaults: Omit `data_point_names` to use config's default selections

**Implementation** (agent/mcp_server.py):
```python
@tool(
    "query_market_data",
    """Query market data across 7 categories:

CATEGORIES (use exact names):
- technical_analysis: RSI, MACD, Stochastic, Williams_R, CCI, MFI, ADX, PSAR, Aroon, ATR, BB, OBV, SMA, EMA, ROC, VWAP, TRIX, Vortex, BBWidth, Keltner, Donchian
- macro_economics: vix, dxy, cpi, nfp
- sentiment_social: twitter_sentiment (exact name "twitter_sentiment")
- derivatives_leverage: btc_funding_rate, eth_funding_rate
- on_chain_analytics: btc_tvl, whale_activity
- news_regulatory: crypto_news
- trading_signals: ggshot (PREMIUM, exact name "ggshot")

EXAMPLE: {"symbol": "BTC", "categories": {"technical_analysis": ["RSI"], "trading_signals": ["ggshot"]}}

Symbol formats: "BTC", "BTCUSDT", "BTC/USDT" all work. Indicators are case-insensitive.
Params: symbol (required), categories (dict), timeframe (optional, default '1h')""",
    {"symbol": str, "categories": dict, "timeframe": str}
)
async def query_market_data(args: dict[str, Any]) -> dict[str, Any]:
    # 1. Parse and validate categories
    categories = args.get("categories", {})
    VALID_CATEGORIES = {
        "technical_analysis", "macro_economics", "sentiment_social",
        "derivatives_leverage", "on_chain_analytics", "news_regulatory", "trading_signals"
    }

    # Validate category names (fail fast with helpful error)
    unknown = set(categories.keys()) - VALID_CATEGORIES
    if unknown:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Unknown categories: {unknown}\n\nValid categories:\n{list(VALID_CATEGORIES)}"
            }]
        }

    # 2. Separate technical from intelligence sources
    technical_indicators = categories.get("technical_analysis", [])
    intelligence_sources = {k: v for k, v in categories.items() if k != "technical_analysis"}

    # 3. Call API (symbol normalized server-side: BTC → BTC/USDT)
    result = await agent_context.api_client.query_market_data(
        config_id=agent_context.config_id,
        symbol=args["symbol"],
        indicators=technical_indicators if technical_indicators else None,
        data_sources=intelligence_sources if intelligence_sources else None,
        timeframe=args.get("timeframe", "1h")
    )

    # 4. Format response for agent
    return {"content": [{"type": "text", "text": format_market_data(result)}]}
```

---

### **Tool 2: `execute_trade`**

**Purpose**: Execute trades with optional config overrides

**Schema**:
```python
{
    "symbol": str,
    "side": str,                      # "long" | "short"
    "confidence": float,              # 0-1 (default: 0.7)

    # Optional overrides (use config defaults if not specified)
    "size_usd": float,                # Override position size
    "leverage": int,                  # Override leverage

    # Required risk management
    "stop_loss_price": float,         # REQUIRED (safety)
    "take_profit_price": float        # REQUIRED (safety)
}
```

**Design Note**: Agent can override position sizing and leverage. If not specified, uses config's `risk_per_trade` and `leverage` settings. SL/TP are REQUIRED for safety (prevents runaway losses if agent breaks).

**Implementation**:
```python
@tool("execute_trade", "Execute a trading position", {
    "symbol": str,
    "action": str,
    "size_usd": float,
    "stop_loss_pct": float,
    "take_profit_pct": float,
    "reasoning": str
})
async def execute_trade(args: dict[str, Any]) -> dict[str, Any]:
    # Create decision record
    decision_id = str(uuid.uuid4())
    await db.execute("""
        INSERT INTO decisions (decision_id, user_id, config_id, symbol, action,
                               confidence, reasoning, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'agent')
    """, (decision_id, AGENT_USER_ID, AGENT_CONFIG_ID, args["symbol"],
          args["action"], 1.0, args["reasoning"]))

    # Execute trade
    paper_service = SupabasePaperTradingService()
    result = await paper_service.execute_trade_intent({
        "decision_id": decision_id,
        "symbol": args["symbol"],
        "action": args["action"],
        "size_usd": args["size_usd"],
        "stop_loss_pct": args["stop_loss_pct"],
        "take_profit_pct": args["take_profit_pct"]
    })

    return {"content": [{"type": "text", "text": format_trade_result(result)}]}
```

---

### **Tool 3: `get_positions`**

**Purpose**: View all open positions (paper and live)

**Returns**: All fields from `paper_trades` table (or Symphony API for live):
- trade_id, symbol, side, entry_price, current_price
- size_usd, leverage, unrealized_pnl, unrealized_pnl_percent
- stop_loss, take_profit, confidence_score, opened_at
- For live: additional Symphony-specific fields (batch_id, margin, etc.)

**Implementation**:
```python
@tool("get_positions", "Get all open trading positions", {})
async def get_positions(args: dict[str, Any]) -> dict[str, Any]:
    positions = await db.query("""
        SELECT symbol, side, entry_price, current_price,
               size_usd, unrealized_pnl, trade_id, opened_at
        FROM paper_trades
        WHERE config_id = %s AND status = 'open'
        ORDER BY opened_at DESC
    """, (AGENT_CONFIG_ID,))

    return {"content": [{"type": "text", "text": format_positions(positions)}]}
```

---

### **Tool 4: `close_position`**

**Purpose**: Close a specific position

**Schema**:
```python
{
    "trade_id": str,
    "reasoning": str
}
```

**Implementation**:
```python
@tool("close_position", "Close an open position", {
    "trade_id": str,
    "reasoning": str
})
async def close_position(args: dict[str, Any]) -> dict[str, Any]:
    paper_service = SupabasePaperTradingService()
    result = await paper_service.close_position(
        trade_id=args["trade_id"],
        reason=args["reasoning"]
    )

    return {"content": [{"type": "text", "text": format_close_result(result)}]}
```

---

### **Tool 5: `get_account_status`**

**Purpose**: Check paper account balance and performance

**Note**: Currently supports paper trading only. Live trading account status via Symphony coming soon.

**Returns**:
- balance, total_pnl, open_positions
- total_trades, win_trades, loss_trades, win_rate
- total_return_percent, current_equity (balance + unrealized pnl)

**Implementation**:
```python
@tool("get_account_status", "Get account balance and trading performance", {})
async def get_account_status(args: dict[str, Any]) -> dict[str, Any]:
    account = await db.query("""
        SELECT current_balance, total_pnl, total_trades,
               win_trades, loss_trades
        FROM paper_accounts
        WHERE config_id = %s
    """, (AGENT_CONFIG_ID,))

    win_rate = account['win_trades'] / account['total_trades'] if account['total_trades'] > 0 else 0

    return {"content": [{"type": "text", "text": f"""
Account Status:
Balance: ${account['current_balance']:.2f}
Total P&L: ${account['total_pnl']:.2f}
Trades: {account['total_trades']} (Win Rate: {win_rate:.1%})
    """}]}
```

---

### **Tool 6: `wait_for`**

**Purpose**: Agent controls its own timing

**Schema**:
```python
{
    "duration_minutes": int,  # Max: 1440 (24 hours)
    "reason": str             # Optional, for logging
}
```

**Future Enhancement (Phase 3+)**: Wake-up triggers
- Agent can set alerts: "Wake me if BTC drops below $95k"
- Volume spike detection
- News break notifications
- Enables reactive behavior while sleeping

**Implementation**:
```python
@tool("wait_for", "Sleep for specified duration", {
    "duration_minutes": int,
    "reason": str
})
async def wait_for(args: dict[str, Any]) -> dict[str, Any]:
    """Log wait reason, sleep."""
    duration = min(args["duration_minutes"], 1440)  # Cap at 24h
    next_check = datetime.utcnow() + timedelta(minutes=duration)

    logger.info(f"Agent waiting {duration}m: {args.get('reason', 'No reason')}")

    await asyncio.sleep(duration * 60)

    return {"content": [{"type": "text", "text":
        f"⏳ Waited {duration} minutes. Next check: {next_check.strftime('%H:%M:%S')} UTC"
    }]}
```

---

### **Tool 7: `update_strategy`** (Experimental Mode Only)

**Purpose**: Agent modifies its own strategy (if permitted)

**Schema**:
```python
{
    "new_strategy": str,
    "reason": str,
    "performance_summary": str
}
```

**Implementation**:
```python
@tool("update_strategy", "Update your trading strategy (requires autonomously_editable=true)", {
    "new_strategy": str,
    "reason": str,
    "performance_summary": str
})
async def update_strategy(args: dict[str, Any]) -> dict[str, Any]:
    config = await load_config(AGENT_CONFIG_ID)
    agent_strategy = config['config_data']['agent_strategy']

    # Check permission
    if not agent_strategy.get('autonomously_editable', False):
        return {"content": [{"type": "text", "text":
            "❌ Strategy is not autonomously editable. Ask user for approval."
        }]}

    # Log old version performance
    agent_strategy['performance_log'].append({
        "version": agent_strategy['version'],
        "ended_at": datetime.now().isoformat(),
        "reason_for_change": args['performance_summary']
    })

    # Update strategy
    agent_strategy['content'] = args['new_strategy']
    agent_strategy['version'] += 1
    agent_strategy['last_updated_at'] = datetime.now().isoformat()
    agent_strategy['last_updated_by'] = 'agent'

    await save_config(AGENT_CONFIG_ID, config)

    return {"content": [{"type": "text", "text":
        f"✅ Strategy updated to v{agent_strategy['version']}. New approach active."
    }]}
```

---

### **Tool 8: `record_trade_observation`** (NEW)

**Purpose**: Post-trade reflection after closing positions

**Trigger**: Agent calls this after `close_position` to reflect on what worked/failed

**Schema**:
```python
{
    "trade_id": str,                          # Closed trade ID
    "observation_type": str,                  # "win_analysis" | "loss_analysis"
    "what_went_well": str,                    # What worked in this trade
    "what_went_wrong": str,                   # What didn't work
    "predictive_data_points": dict,           # {"vix": "low volatility helped", "rsi": "accurate signal"}
    "decision_review": str,                   # Review of original entry decision
    "importance": int                         # 1-10 (how valuable is this learning)
}
```

**Philosophy**: Structured learning tied to specific trades. Agent reflects immediately after close, when context is fresh. User can review observations with agent to refine strategy collaboratively.

---

### **Tool 9: `query_trade_observations`** (NEW)

**Purpose**: Search past trade observations for learning

**Schema**:
```python
{
    "symbol": str,                # Filter by symbol (optional)
    "observation_type": str,      # "win_analysis" | "loss_analysis" (optional)
    "min_importance": int,        # Minimum importance threshold (optional)
    "limit": int                  # Max results (default: 10)
}
```

**Use Cases**:
- **User asks**: "What have we learned about BTC trades?"
- **Agent reviews**: Before entering similar trade, check past observations
- **Strategy refinement**: User + agent discuss patterns, improve strategy together

**Design Note**: Observations are queryable, NOT auto-injected after compaction. Agent retrieves when needed. Keeps compaction context lean.

---

## Agent Runner Implementation

### **Tool Context Pattern (Module-Level State)**

```python
# agent/mcp_server.py - CRITICAL: Tools need access to agent context

from typing import Any
from claude_agent_sdk import tool

# Module-level state for tools to access (SDK has no built-in pattern)
class AgentContext:
    config_id: str | None = None
    user_id: str | None = None

agent_context = AgentContext()

# Example tool using context
@tool("execute_trade", "Execute a trading position", {
    "symbol": str,
    "action": str,
    "size_usd": float,
    "stop_loss_pct": float,
    "take_profit_pct": float,
    "reasoning": str
})
async def execute_trade(args: dict[str, Any]) -> dict[str, Any]:
    # Access context from module state
    config_id = agent_context.config_id
    user_id = agent_context.user_id

    # Create decision record
    decision_id = str(uuid.uuid4())
    await db.execute("""
        INSERT INTO decisions (decision_id, user_id, config_id, symbol, action,
                               confidence, reasoning, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'agent')
    """, (decision_id, user_id, config_id, args["symbol"],
          args["action"], 1.0, args["reasoning"]))

    # Execute via service
    paper_service = SupabasePaperTradingService()
    result = await paper_service.execute_trade_intent({
        "decision_id": decision_id,
        "symbol": args["symbol"],
        "action": args["action"],
        "size_usd": args["size_usd"],
        "stop_loss_pct": args["stop_loss_pct"],
        "take_profit_pct": args["take_profit_pct"]
    })

    return {"content": [{"type": "text", "text": format_trade_result(result)}]}
```

---

### **Main Agent Loop (Corrected SDK Pattern)**

```python
# agent/run_agent.py

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    HookMatcher
)
from .mcp_server import (
    agent_context,  # Import context to set
    query_market_data, execute_trade, get_positions,
    close_position, get_account_status, wait_for,
    update_strategy, record_learning
)
from core.common.logger import logger
import asyncio

class TradingAgent:
    def __init__(self, config_id: str, user_id: str):
        self.config_id = config_id
        self.user_id = user_id
        self.mode = "conversation"  # or "autonomous"
        self.redis = Redis()

        # Set context for tools to access
        agent_context.config_id = config_id
        agent_context.user_id = user_id

        # Build system prompt based on mode
        self.system_prompt = self._build_system_prompt()

        # Create MCP server
        self.mcp_server = create_sdk_mcp_server(
            name="ggbots-trading",
            version="1.0.0",
            tools=[query_market_data, execute_trade, get_positions,
                   close_position, get_account_status, wait_for,
                   update_strategy, record_learning]
        )

        # Configure agent options
        self.options = ClaudeAgentOptions(
            # Model (use specific dated version)
            # Testing: Haiku 4.5 (3x cheaper: $1/$5 per MTok)
            # Production: Sonnet 4.5 (smarter for agents: $3/$15 per MTok)
            model="claude-haiku-4-5-20251001",

            # System prompt
            system_prompt=self.system_prompt,

            # MCP tools
            mcp_servers={"ggbots-trading": self.mcp_server},
            allowed_tools=[
                "mcp__ggbots-trading__query_market_data",
                "mcp__ggbots-trading__execute_trade",
                "mcp__ggbots-trading__get_positions",
                "mcp__ggbots-trading__close_position",
                "mcp__ggbots-trading__get_account_status",
                "mcp__ggbots-trading__wait_for",
                "mcp__ggbots-trading__update_strategy",
                "mcp__ggbots-trading__record_learning"
            ],

            # Context management (SDK handles auto-compaction)
            max_turns=100,  # Auto-compact after 100 turns

            # Hooks for monitoring
            hooks={
                "PreCompact": [
                    HookMatcher(matcher="*", hooks=[self._on_precompact])
                ]
            },

            # Working directory
            cwd="/home/sev/ggbot"
        )

    async def _on_precompact(self, input_data, tool_use_id, context):
        """Hook called before automatic compaction"""
        logger.info(f"Context compaction triggered for agent {self.config_id}")

        # Compaction SUMMARIZES conversation (not a hard reload)
        # After compaction, SDK injects new system prompt with essentials:
        # - Current strategy
        # - Account status
        # - Open positions
        # - Recent trades (last 20)
        # - Performance metrics
        # - Note: Query trade_observations dynamically when needed

        return {}

    def _build_system_prompt(self) -> str:
        """Build system prompt based on mode and strategy"""
        if self.mode == "conversation":
            return """You are an autonomous trading agent in CONVERSATION MODE.

Your goal: Collaborate with the user to define a trading strategy.

Ask clarifying questions:
- What assets to trade?
- Entry/exit criteria?
- Risk management (position size, stop loss, take profit)?
- Market conditions to avoid?
- Should you have permission to modify the strategy autonomously?

When strategy is clear, summarize and ask: "Shall I proceed with this strategy?"

If user confirms, you'll switch to AUTONOMOUS MODE and execute 24/7."""

        # Load strategy for autonomous mode
        config = asyncio.run(self._load_config())
        strategy = config['config_data']['agent_strategy']

        if strategy.get('autonomously_editable', False):
            # Experimental mode
            return f"""You are an autonomous trading agent with FULL STRATEGIC AUTONOMY.

CURRENT STRATEGY (Version {strategy['version']}):
{strategy['content']}

Autonomously Editable: YES

You have complete freedom to:
- Test different strategies
- Measure what works
- Modify approach using update_strategy tool
- Learn and evolve

Be methodical: test strategies for enough trades before changing.
Document reasoning when updating strategy.

After closing trades, use record_trade_observation to reflect on what worked/failed.
Query trade_observations to learn from past patterns.

Tools: query_market_data, execute_trade, get_positions, close_position,
       get_account_status, wait_for, update_strategy,
       record_trade_observation, query_trade_observations

You control timing via wait_for. Trade thoughtfully."""
        else:
            # Guided mode
            return f"""You are an autonomous trading agent in AUTONOMOUS MODE.

STRATEGY (User-defined):
{strategy['content']}

Autonomously Editable: NO

Execute this strategy faithfully. You CANNOT modify the core strategy without user approval.
If you think strategy should change, discuss with the user.

After closing trades, use record_trade_observation to reflect on what worked/failed.
Query trade_observations to learn from past patterns and improve execution.

Tools: query_market_data, execute_trade, get_positions, close_position,
       get_account_status, wait_for, record_trade_observation,
       query_trade_observations

You control timing via wait_for. Trade thoughtfully."""

    async def run(self):
        """Main agent loop - handles both modes"""
        async with ClaudeSDKClient(options=self.options) as client:
            # Context manager handles connection automatically

            while True:
                if self.mode == "conversation":
                    await self._conversation_mode(client)
                elif self.mode == "autonomous":
                    await self._autonomous_mode(client)

    async def _conversation_mode(self, client):
        """Interactive strategy building"""
        # Get user message from queue
        msg = await self.redis.lpop(f"agent:{self.config_id}:messages")
        if not msg:
            await asyncio.sleep(1)
            return

        # Send message to agent
        await client.query(msg)

        # Process response (stops at Result message)
        async for response in client.receive_response():
            # Check for strategy confirmation
            if self._is_strategy_confirmation(response):
                # Extract strategy, save, switch mode
                await self._save_strategy_and_activate()
                self.mode = "autonomous"

                # Update system prompt for autonomous mode
                self.options.system_prompt = self._build_system_prompt()

                await client.query("Strategy confirmed. Starting autonomous trading.")
                return

            # Send response to user
            await self._send_to_user(response)

    async def _autonomous_mode(self, client):
        """24/7 autonomous trading"""
        # Check for user messages (non-blocking)
        if user_msg := await self.redis.lpop(f"agent:{self.config_id}:messages"):
            await client.query(f"[USER MESSAGE]: {user_msg}")

            # Process user query response
            async for response in client.receive_response():
                await self._send_to_user(response)
                return  # Return to main loop after handling message

        # Give agent initial prompt to start trading
        await client.query("Continue autonomous trading. Analyze markets and execute your strategy.")

        # Process agent's autonomous actions
        async for message in client.receive_response():
            # Log agent activity
            logger.info(f"Agent {self.config_id} activity: {message}")

            # Agent will use wait_for tool to control timing
            # This loop will complete when agent finishes a decision cycle
```

---

## Agent Behavior Examples

### **Guided Mode Example**

```
[Conversation Phase]
User: "Create an agent for BTC"
Agent: "Let's design your strategy. What's your approach?"
User: "Conservative. RSI < 30 for entries, 5% position size, 2% stop loss"
Agent: "Got it. Strategy summary:
       - Trade: BTC/USDT
       - Entry: RSI < 30 (oversold)
       - Position: 5% of account
       - Stop Loss: 2%, Take Profit: 6%
       - Check markets every 2 hours

       Should I have permission to modify this strategy autonomously?"
User: "No, stick to the plan"
Agent: "Understood. Autonomously editable: NO. Proceeding..."

[Autonomous Phase]
[10:00] Agent: Checking BTC conditions
[10:00] Tool: query_market_data(BTC, indicators=[RSI_1h])
[10:01] Agent: RSI 45 (neutral). No entry signal. Waiting...
[10:01] Tool: wait_for(7200, "RSI neutral, checking again in 2h")

[12:00] Agent: Re-checking
[12:00] Tool: query_market_data(BTC, indicators=[RSI_1h])
[12:01] Agent: RSI 28 (oversold)! Entry signal. Executing...
[12:01] Tool: execute_trade(BTC, long, $500, sl=2%, tp=6%)
```

### **Experimental Mode Example**

```
[Conversation Phase]
User: "Create an agent for BTC. Figure out what works."
Agent: "Exciting! What constraints?"
User: "Max 10% risk per trade, max 2 positions, 1h+ timeframes"
Agent: "Understood. Should I have full autonomy to evolve my strategy?"
User: "Yes, show me what you can do"
Agent: "Perfect. Autonomously editable: YES.

       Starting strategy: RSI mean reversion
       - Long when RSI < 30, Short when RSI > 70
       - Position: 8%, SL: 3%, TP: 6%

       I'll test this, measure results, and evolve. Beginning..."

[Autonomous Phase - Day 1]
Agent: "Testing RSI mean reversion..."
[Trades 1-10: 40% win rate, -$150]

Agent: "After 10 trades, 40% win rate. RSI signals in ranging market are
       low quality. Updating strategy..."
[Tool: update_strategy]
New Strategy: "Trend following: Only trade with 50MA trend. Long when
              price > 50MA and RSI < 40."

[Day 2]
[Trades 11-25: 60% win rate, +$320]
Agent: "Better! Trend filter helps. But getting stopped out in volatility.
       Adding ATR-based stops..."
[Tool: update_strategy]
New Strategy v3: "Same trend system, dynamic stops: SL = 1.5 × ATR(14)"

[Day 5]
[Trades 26-50: 68% win rate, +$890]
Agent: "Working well. One refinement: avoiding trades when funding > 1.5%"
```

---

## Phase 3 & 4 Implementation Plan

### **Phase 3: Agent Runner** ✅ **COMPLETE** (Week 3)

**Status**: Foundation complete, all 10 tools operational, ready for end-to-end testing

**Completed Features**:
- ✅ TradingAgent class with strategy_definition and autonomous modes
- ✅ All 10 MCP tools working (query_market_data validated with correct categories)
- ✅ Redis queue integration for bidirectional user ↔ agent messaging
- ✅ Symbol normalization: agent can use any format (BTC, BTCUSDT, BTC/USDT)
- ✅ Category validation with helpful error messages
- ✅ Comprehensive debug logging to agent-debug.log

**Key Implementation Learnings**:
1. **Tool Documentation**: Categories MUST be in @tool description, not docstrings
2. **Symbol Handling**: UniversalSymbolStandardizer converts all formats → CCXT (BTC/USDT)
3. **Validation Pattern**: Fail fast with helpful errors vs silent failures

**Goal**: Build conversation + autonomous modes with Redis queue architecture

#### **Architecture Pattern: Streaming Mode with Two Async Tasks**

Based on Claude Agent SDK best practices, we use **streaming mode** with parallel task execution:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import asyncio

async def run_agent(config_id: str, user_id: str, mode: str):
    # Initialize with MCP server and system prompt
    options = ClaudeAgentOptions(
        mcp_servers={"trading": create_mcp_server()},
        allowed_tools=[
            "mcp__trading__query_market_data",
            "mcp__trading__execute_trade",
            "mcp__trading__get_positions",
            # ... all 9 tools
        ],
        system_prompt={
            "type": "append",
            "preset": "claude_code",
            "append": build_system_prompt(mode, strategy, config_id)
        }
    )

    async with ClaudeSDKClient(options=options) as client:
        # Two parallel tasks
        agent_task = asyncio.create_task(process_agent_loop(client))
        interrupt_task = asyncio.create_task(handle_user_messages(client))

        await asyncio.gather(agent_task, interrupt_task)

async def process_agent_loop(client):
    """Task 1: Process agent's autonomous loop"""
    async for message in client.receive_messages():
        # Agent uses tools, sleeps via wait_for, trades forever
        # Log agent actions to Redis for user visibility

async def handle_user_messages(client):
    """Task 2: Poll Redis queue and interrupt agent when user sends messages"""
    while True:
        user_msg = await redis.blpop(f"agent:{config_id}:messages", timeout=1)
        if user_msg:
            await client.interrupt()  # Stop current execution
            await client.query(user_msg)
            # Collect response with receive_response()
```

**Key SDK Concepts**:
- `receive_messages()` - Streams indefinitely, perfect for autonomous loop
- `receive_response()` - Streams until ResultMessage, perfect for user queries
- `client.interrupt()` - Stop mid-execution when user sends message
- System prompt set once at init, cannot change mid-session

#### **Two Scripts Architecture**

**1. `agent/run_agent.py`** - Pure agent logic (production-ready):
```python
"""
Agent Runner - Production Entry Point

Usage:
    python agent/run_agent.py --config-id=abc123 --mode=strategy_definition
    python agent/run_agent.py --config-id=abc123 --mode=autonomous

Architecture:
    - Reads from Redis: agent:{config_id}:messages
    - Writes to Redis: agent:{config_id}:responses
    - Zero throwaway code (same queues used by API/frontend in Phase 4)
"""

import argparse
from agent.mcp_server import create_mcp_server, set_agent_context
from agent.service_client import GGBotAPIClient
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config-id', required=True)
    parser.add_argument('--mode', choices=['strategy_definition', 'autonomous'], required=True)
    args = parser.parse_args()

    # Load config from DB
    config = await load_config(args.config_id)

    # Initialize agent context
    api_client = GGBotAPIClient(user_id=config['user_id'])
    set_agent_context(args.config_id, config['user_id'], api_client)

    # Run agent
    await run_agent(args.config_id, config['user_id'], args.mode, config)
```

**2. `agent/chat.py`** - CLI interface for testing (reusable as debug tool):
```python
"""
Chat CLI - Test Interface for Agent

Usage:
    # Terminal 1: Start agent
    python agent/run_agent.py --config-id=abc123 --mode=strategy_definition

    # Terminal 2: Chat with agent
    python agent/chat.py --config-id=abc123

Pushes messages to Redis queue, polls for responses.
"""

import asyncio
import redis.asyncio as redis

async def chat_loop(config_id):
    redis_client = await redis.from_url("redis://localhost")

    print("Chat CLI started. Type your messages:\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break

        # Push to Redis
        await redis_client.lpush(f"agent:{config_id}:messages", user_input)

        # Poll for response
        response = await redis_client.brpop(f"agent:{config_id}:responses", timeout=60)
        if response:
            print(f"Agent: {response[1].decode()}\n")
```

#### **Mode Switching: Strategy Definition → Autonomous**

Agent calls special `request_autonomous_mode` tool:

```python
@tool(
    "request_autonomous_mode",
    "Request permission to switch to autonomous trading mode",
    {"strategy_summary": str}
)
async def request_autonomous_mode(args):
    await redis.set(f"agent:{config_id}:mode_switch_pending", "true")

    return {
        "content": [{
            "type": "text",
            "text": f"""
📋 Strategy Ready for Autonomous Trading

{args['strategy_summary']}

Reply with:
1 - CONFIRM and start autonomous trading
2 - REVISE strategy
            """
        }]
    }

# In run_agent.py
if await redis.get(f"agent:{config_id}:mode_switch_pending"):
    # Wait for user confirmation
    while True:
        user_msg = await wait_for_user_message()
        if user_msg == "1":
            mode = "autonomous"
            await client.query("CONFIRMED. Starting autonomous trading mode.")
            break
        elif user_msg == "2":
            await redis.delete(f"agent:{config_id}:mode_switch_pending")
            await client.query("Understood, let's revise the strategy.")
            break
```

#### **Autonomous Loop: Agent Self-Directs Timing**

Agent uses `wait_for` tool to control its own schedule:

```python
# Agent's autonomous loop (happens naturally via tools)
1. query_market_data (check RSI, funding)
2. Decide: Trade opportunity? Position adjustment? Wait?
3. execute_trade OR close_position OR wait_for(duration_minutes=60)
4. Loop forever (agent controls timing)

# Example agent behavior:
Agent: "RSI neutral, no setup. Will check again in 1 hour."
[calls wait_for(60, "waiting for clearer signal")]
[sleeps 1 hour]
Agent: "Checking again... RSI oversold, funding negative, entering long!"
[calls execute_trade with SL/TP]
Agent: "Trade opened. Will monitor in 4 hours."
[calls wait_for(240, "letting position develop")]
```

**System Prompt Guidance** (prevents excessive querying):
```
PATIENCE & TIMING:
- Markets need time to develop. Don't overthink or overquery.
- After entering trade with SL/TP, you can wait hours. Let it play out.
- Use wait_for() strategically:
  - Volatile: 15-30 minutes
  - Normal: 1-2 hours
  - Position running: 4-6 hours
  - Waiting for event: up to 24 hours

COST CONSCIOUSNESS:
- Each query costs credits. Query with purpose.
- Plan your checks instead of constant monitoring.
```

#### **Strategy Updates in Autonomous Mode**

The `update_strategy` tool checks `autonomously_editable` flag:

```python
@tool("update_strategy", ...)
async def update_strategy(args):
    config = await load_config(config_id)

    if not config['agent_strategy'].get('autonomously_editable', False):
        # GUIDED MODE: Request user approval
        await redis.lpush(
            f"agent:{config_id}:approval_queue",
            {"type": "strategy_update", "new_strategy": args['new_strategy']}
        )
        return {"content": [{"type": "text", "text": "⚠️ Approval requested from user"}]}

    # EXPERIMENTAL MODE: Auto-update
    # Update config_data directly
    return {"content": [{"type": "text", "text": "✅ Strategy updated"}]}
```

#### **Compaction Handling**

SDK auto-compacts at 95% token usage. Phase 3: Let it happen naturally. Phase 4: Inject fresh context.

```python
# Phase 3: No custom logic, SDK handles automatically

# Phase 4: Detect compaction and re-inject context
async for message in client.receive_messages():
    if message.type == "system" and message.subtype == "compact_boundary":
        # Compaction just happened, inject fresh trading context
        await client.query(f"""
CONTEXT UPDATE AFTER COMPACTION:

Strategy: {strategy_content}
Account Balance: ${balance}
Open Positions: {positions_summary}
Recent Performance: {win_rate}% win rate, ${total_pnl} P&L
        """)
```

#### **Error Handling**

**Tool errors**: Return error message to agent (don't crash):
```python
try:
    result = await api_client.execute_trade(...)
except Exception as e:
    return {"content": [{"type": "text", "text": f"❌ Trade failed: {e}"}]}
```

**Process crashes**: Manual restart for Phase 3, PM2 auto-restart in Phase 4

**Connection issues**: Log, retry 3x, exit gracefully

---

### **Phase 4: Production Polish** (Week 4)

**Goal**: Add API endpoints, frontend integration, PM2 management, compaction enhancements

#### **1. API Endpoints** (`api/agent.py` additions)

```python
@router.post("/agent/{config_id}/start")
async def start_agent(config_id: str, mode: str):
    """Spawn agent as PM2 process"""
    # Check if already running
    # Spawn: pm2 start agent/run_agent.py --interpreter .venv-agent/bin/python -- --config-id=...

@router.post("/agent/{config_id}/stop")
async def stop_agent(config_id: str):
    """Stop agent PM2 process"""

@router.post("/agent/{config_id}/message")
async def send_message(config_id: str, message: str):
    """Push message to Redis queue"""
    await redis.lpush(f"agent:{config_id}:messages", message)
```

#### **2. Frontend Integration**

- Agent creation UI
- Chat interface (WebSocket or polling Redis)
- Agent status display (running, mode, recent actions)
- Strategy editor with confirmation flow

#### **3. Compaction Context Injection**

```python
async def inject_post_compaction_context(client, config_id):
    config = await load_config(config_id)
    positions = await get_positions(config_id)
    metrics = await get_metrics(config_id)
    recent_trades = await get_recent_trades(config_id, limit=10)

    context = f"""
TRADING CONTEXT REFRESH:

Strategy: {config['agent_strategy']['content']}
Mode: {'Experimental' if config['agent_strategy']['autonomously_editable'] else 'Guided'}

Account: ${metrics['balance']}, {metrics['total_trades']} trades, {metrics['win_rate']}% win rate
Open Positions: {len(positions)} ({', '.join([f"{p['symbol']} {p['side']}" for p in positions])})

Recent Trades (last 10):
{format_trades(recent_trades)}
    """

    await client.query(context)
```

#### **4. Multi-Agent Refactor** (Closure Pattern)

Refactor from module-level state to closure pattern for thread-safe multi-agent support:

```python
def create_agent_tools(config_id: str, user_id: str, api_client: GGBotAPIClient):
    """Create tool instances with captured context (closure pattern)"""

    @tool("execute_trade", "Execute trade", {...})
    async def execute_trade(args):
        # config_id and api_client captured via closure
        result = await api_client.execute_trade(config_id=config_id, ...)
        return result

    return [
        execute_trade,
        get_positions,
        # ... all 9 tools
    ]

# Each agent gets own tool instances
tools = create_agent_tools(config_id, user_id, api_client)
server = create_sdk_mcp_server("trading", tools=tools)
```

---

## Production Deployment

### **PM2 Service Setup**

```bash
# PM2 ecosystem file
{
  "apps": [{
    "name": "agent-{user_id}-{config_id}",
    "script": "agent/run_agent.py",
    "interpreter": "python",
    "cwd": "/home/sev/ggbot",
    "env": {
      "AGENT_CONFIG_ID": "{config_id}",
      "AGENT_USER_ID": "{user_id}",
      "ANTHROPIC_API_KEY": "{api_key}"
    },
    "max_restarts": 20,
    "min_uptime": "10s"
  }]
}
```

### **Monitoring**

```python
# Add to agent loop
async def _log_metrics(self):
    await db.execute("""
        INSERT INTO logs (user_id, module, log_level, message)
        VALUES (%s, 'agent', 'INFO', %s)
    """, (self.user_id, json.dumps({
        "config_id": self.config_id,
        "mode": self.mode,
        "turn_count": self.turn_count,
        "tokens_used": self.tokens_used,
        "strategy_version": self.strategy_version
    })))
```

---

## Success Metrics

**Phase 1** (Week 1):
- ✅ MCP server with 7 tools implemented
- ✅ Conversation mode working
- ✅ Autonomous mode operational
- ✅ Strategy storage in config_data
- ✅ Full audit trail in database

**Phase 2** (Week 2):
- ✅ Agent runs 24h+ autonomously
- ✅ Compaction working (context-based)
- ✅ Guided vs Experimental modes both functional
- ✅ Dashboard integration
- ✅ Agent makes profitable trades (baseline test)

---

## Related Documentation

- **Agent SDK Reference**: `DOCS/agent-sdk/PYTHON.md`
- **Custom Tools Guide**: `DOCS/agent-sdk/CUSTOM_TOOLS.md`
- **MCP Documentation**: `DOCS/agent-sdk/MCP.md`
- **Current TODO**: `TODO.md`

---

**Last Updated**: 2025-11-01
**Status**: Phase 3 Complete (Agent Runner) - Ready for End-to-End Testing
**Next Steps**:
1. Test full strategy definition → autonomous mode flow
2. Run agent autonomously for 1+ hour with real market data
3. Monitor token usage and costs with Haiku model
4. Begin Phase 4 - Frontend integration and PM2 deployment
