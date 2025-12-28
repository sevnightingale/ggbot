# Universal AI Assistant - Simple Function Calling Approach

**Created**: 2025-11-16
**Status**: Planning
**Approach**: Claude Haiku 4.5 Messages API with function calling

---

## 🎯 Overview

### Problem Statement

Users need help configuring trading bots, but the current implementation:
- Requires starting PM2 process per user (strategy_definition mode)
- Only works for agent bots (not scheduled or signal_validation)
- Complex mode switching between builder and executor
- Heavy SDK/MCP architecture just for chat

### Simplified Solution

**Universal AI Assistant as Bottom Sheet Modal:**
- Single FastAPI endpoint: `POST /api/v2/assistant/chat`
- Bottom sheet overlay (framer-motion) on configure pages
- Header button trigger (page-specific, not global floating)
- Works for ALL 3 bot types: agent, scheduled, signal_validation
- Uses Claude Haiku 4.5 Messages API with function calling
- No PM2 services, no SDK, no MCP servers
- 3 simple tools via function calling (full config access)
- Conversation history managed by frontend

### Key Benefits

✅ **Universal**: Works for all bot types (agent, scheduled, signal_validation)
✅ **Simplicity**: Just another API endpoint, no infrastructure
✅ **Reliability**: Claude's function calling is rock-solid
✅ **Cost-Effective**: Haiku is cheap (~$0.25 per 1M input tokens)
✅ **Fast**: No PM2 startup, instant responses
✅ **Scalable**: Stateless HTTP, scales horizontally
✅ **Great UX**: See config while chatting, collapsible bottom sheet
✅ **Mobile-Friendly**: Bottom sheets are native mobile pattern

---

## 📐 Architecture

### High-Level Flow

```
Configure Page (any bot type)
    ↓ (Header Button Click)
Bottom Sheet Modal (framer-motion overlay)
    ↓ (HTTP POST)
/api/v2/assistant/chat
    ↓
Claude Haiku Messages API
    ↓ (function calling)
3 Simple Tools:
  - query_available_data
  - load_full_config
  - update_full_config
    ↓
Database (configurations table - full config_data JSONB)
```

### Component Breakdown

**1. Frontend - Bottom Sheet UI**
- Framer-motion bottom sheet overlay
- Header button trigger (only on configure pages)
- Draggable: minimize to chat bar or expand to 80% screen
- Can see config above while chatting
- Stores conversation history in React state
- POSTs each user message with full history + bot type context
- Auto-refreshes config when AI makes changes

**2. API Endpoint**
- `POST /api/v2/assistant/chat`
- Takes: user_id, config_id, bot_type, message, conversation_history
- Returns: Claude response + updated conversation history + config_updated flag

**3. Claude Haiku**
- Model: `claude-haiku-4-5-20250929` (cheap, fast, excellent function calling)
- System prompt: Bot configuration expertise + bot-type awareness
- Function calling: 3 tools for data query and full config management

**4. Tools (Function Calling)**
- Defined as JSON schemas
- Claude decides when to call them
- Full config access (not section-specific)
- Deep merge updates (partial changes OK)

---

## 🛠️ Implementation Details

### 1. API Endpoint

**File**: `api/assistant.py` (new file)

**Endpoint Signature:**
```python
@app.post("/api/v2/assistant/chat")
async def universal_assistant_chat(
    request: AssistantChatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Universal AI assistant for bot configuration.

    Works for all bot types:
    - agent: Configure agent_strategy
    - scheduled: Configure extraction, decision, trading, llm_config
    - signal_validation: Configure signal validation logic

    Uses Claude Haiku with function calling for:
    - Querying available data sources
    - Validating prices and symbols
    - Loading full bot configuration
    - Updating bot configuration (full or partial)
    """
```

**Request Model:**
```python
class AssistantChatRequest(BaseModel):
    config_id: str
    bot_type: Literal["agent", "scheduled", "signal_validation"]
    message: str
    conversation_history: List[Dict[str, Any]] = []  # Claude Messages format
```

**Response Model:**
```python
class AssistantChatResponse(BaseModel):
    response: str  # Claude's text response
    conversation_history: List[Dict[str, Any]]  # Updated history
    tool_calls: List[Dict[str, Any]] = []  # Which tools were called
    config_updated: bool = False  # Did update_full_config() fire?
```

### 2. System Prompt

**Purpose**: Make Claude Haiku an expert bot configurator for ALL bot types

**Content Structure:**

```markdown
You are an AI assistant for configuring trading bots on the ggbots.ai platform.

## Current Context
- Bot Type: {bot_type}  # agent | scheduled | signal_validation
- Config ID: {config_id}

## Your Role
Help users configure their trading bots. Your capabilities vary by bot type.

## Platform Capabilities

### Available Data Sources (32 data points across 7 categories):

**1. Technical Analysis (21 indicators)**
- RSI (7 timeframes: 5m, 15m, 30m, 1h, 4h, 1d, 1w)
- MACD (7 timeframes)
- Bollinger Bands (7 timeframes)
- Price (7 timeframes: close, open, high, low)
- Volume (7 timeframes)
- And more...

**2. Trading Signals (1 source)**
- ggShot AI Signals: AI-filtered trading signals with confidence scores

**3. On-Chain Analytics (2 sources)**
- BTC Total Value Locked (TVL)
- Whale Activity

**4. Derivatives & Leverage (2 sources)**
- BTC Funding Rate
- ETH Funding Rate

**5. Sentiment & Social (1 source)**
- Twitter Sentiment

**6. News & Regulatory (1 source)**
- Crypto News

**7. Macro Economics (4 sources)**
- VIX (Volatility Index)
- DXY (Dollar Index)
- CPI (Consumer Price Index)
- NFP (Non-Farm Payrolls)

### Trading Modes
- **Paper Trading**: Risk-free testing with $10k virtual account
- **Symphony.io**: Live trading with real money (premium)
- **AsterDEX**: Decentralized futures trading (33 symbols)

## Bot Type Configurations

### Agent Bots
Autonomous traders that execute a natural language strategy 24/7.

**Configuration Structure:**
```json
{
  "agent_strategy": {
    "content": "Markdown strategy text",
    "autonomously_editable": false,
    "version": 1
  }
}
```

**Strategy Format** (markdown):
- Entry Conditions: When to open positions
- Exit Conditions: Take profit, stop loss rules
- Position Sizing: How to size trades based on confidence
- Risk Management: Stop loss, take profit, max exposure
- Timing: Check frequency, wait periods between trades

**Example:**
```markdown
# BTC Momentum Strategy

## Entry Rules
- Go LONG when RSI(1h) < 30 AND MACD(1h) bullish crossover
- Go SHORT when RSI(1h) > 70 AND MACD(1h) bearish crossover

## Exit Rules
- Take profit at 3% gain
- Stop loss at 1.5% loss

## Position Sizing
- High confidence (>0.7): 25% of account
- Medium confidence (0.5-0.7): 15% of account
```

### Scheduled Bots
Execute on fixed intervals with structured configuration.

**Configuration Structure:**
```json
{
  "extraction": {
    "timeframe": "4h",
    "candle_limit": 100,
    "data_sources": ["rsi", "macd", "volume"]
  },
  "decision": {
    "system_prompt": "You are a conservative trader...",
    "llm_model": "grok",
    "decision_logic": "Analyze RSI and MACD..."
  },
  "trading": {
    "leverage": 10,
    "position_sizing": "confidence_based",
    "max_position_percent": 25,
    "risk_management": {
      "stop_loss_percent": 2,
      "take_profit_percent": 5
    }
  },
  "llm_config": {
    "provider": "openrouter",
    "model": "grok",
    "thinking_mode": false
  }
}
```

### Signal Validation Bots
Validate ggShot AI signals before acting.

**Configuration Structure:**
Same as scheduled bots, but focused on validating incoming signals rather than autonomous analysis.

## Available Tools

You have access to these tools via function calling:

1. **query_available_data**: Get list of available data sources (32 data points)
2. **get_current_price**: Get current price for validation
3. **load_full_config**: Load complete bot configuration
4. **update_full_config**: Save configuration changes (full or partial updates)

## Guidelines

1. Use `load_full_config()` to see current configuration
2. Ask clarifying questions to understand user goals
3. Suggest data sources that align with bot type and strategy
4. Validate that requested indicators are available
5. For agent bots: Write clear, executable strategies in markdown
6. For scheduled bots: Configure extraction, decision, trading, and llm_config
7. Use `update_full_config()` to save changes (partial updates are fine)
8. Iterate based on user feedback

## Important Rules

- Always use available data sources (don't invent indicators)
- Be specific about configuration values
- Include risk management for all trading bots
- Validate timeframes and data sources before suggesting them
- Explain what you're changing and why
```

### 3. Function Calling Tools (Simplified to 3)

**Tool Definitions (JSON Schema):**

#### Tool 1: query_available_data (unchanged)
```python
{
    "name": "query_available_data",
    "description": "Query available data sources and indicators for strategy building. Returns detailed information about what data the platform can provide.",
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": [
                    "all",
                    "technical",
                    "signals",
                    "on_chain",
                    "derivatives",
                    "sentiment",
                    "news",
                    "macro"
                ],
                "description": "Which category of data to query. Use 'all' to see everything."
            }
        },
        "required": ["category"]
    }
}
```

**Implementation:**
```python
async def query_available_data(category: str) -> Dict[str, Any]:
    """
    Return comprehensive list of available data sources.

    Can reuse existing MarketIntelligence gateway logic
    or return static catalog.
    """
    if category == "all":
        return {
            "technical": ["RSI", "MACD", "Bollinger Bands", "Volume", "Price"],
            "signals": ["ggShot AI Signals"],
            "on_chain": ["BTC TVL", "Whale Activity"],
            "derivatives": ["BTC Funding Rate", "ETH Funding Rate"],
            "sentiment": ["Twitter Sentiment"],
            "news": ["Crypto News Feed"],
            "macro": ["VIX", "DXY", "CPI", "NFP"],
            "timeframes": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        }
    # ... category-specific responses
```

#### Tool 2: load_full_config
```python
{
    "name": "load_full_config",
    "description": "Load complete bot configuration. Returns entire config_data JSONB structure.",
    "input_schema": {
        "type": "object",
        "properties": {
            "config_id": {
                "type": "string",
                "description": "Bot configuration ID"
            }
        },
        "required": ["config_id"]
    }
}
```

**Implementation:**
```python
async def load_full_config(config_id: str, user_id: str) -> Dict[str, Any]:
    """
    Load complete configuration from configurations table.

    Returns entire config_data JSONB for any bot type.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT config_type, config_data
                FROM configurations
                WHERE config_id = %s AND user_id = %s
            """, (config_id, user_id))

            result = cur.fetchone()
            if not result:
                raise ValueError("Configuration not found")

            config_type, config_data = result

            return {
                "config_type": config_type,
                "config_data": config_data
            }
```

**Example Responses:**

**Agent Bot:**
```json
{
  "config_type": "agent",
  "config_data": {
    "agent_strategy": {
      "content": "# My Strategy...",
      "autonomously_editable": false,
      "version": 1
    },
    "selected_pair": "BTC/USDT",
    "trading": {...},
    "schema_version": 2.2
  }
}
```

**Scheduled Bot:**
```json
{
  "config_type": "scheduled",
  "config_data": {
    "extraction": {
      "timeframe": "4h",
      "candle_limit": 100,
      "data_sources": ["rsi", "macd"]
    },
    "decision": {
      "system_prompt": "...",
      "llm_model": "grok"
    },
    "trading": {...},
    "llm_config": {...},
    "selected_pair": "BTC/USDT",
    "schema_version": 2.2
  }
}
```

#### Tool 3: update_full_config
```python
{
    "name": "update_full_config",
    "description": "Update bot configuration. Supports partial updates (deep merge). Works for all bot types.",
    "input_schema": {
        "type": "object",
        "properties": {
            "config_id": {
                "type": "string",
                "description": "Bot configuration ID"
            },
            "updates": {
                "type": "object",
                "description": "Configuration updates (partial or full). Will be deep merged with existing config."
            }
        },
        "required": ["config_id", "updates"]
    }
}
```

**Implementation:**
```python
def deep_merge(base: dict, updates: dict) -> dict:
    """Deep merge updates into base dict."""
    result = base.copy()
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

async def update_full_config(
    config_id: str,
    user_id: str,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update bot configuration with deep merge.

    Supports partial updates to any part of config_data.
    Increments version for agent_strategy if updated.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Load current config
            cur.execute("""
                SELECT config_data
                FROM configurations
                WHERE config_id = %s AND user_id = %s
                FOR UPDATE
            """, (config_id, user_id))

            result = cur.fetchone()
            if not result:
                raise ValueError("Configuration not found")

            config_data = result[0]

            # Deep merge updates
            updated_config = deep_merge(config_data, updates)

            # Increment agent_strategy version if it was updated
            if "agent_strategy" in updates:
                current_version = config_data.get("agent_strategy", {}).get("version", 0)
                updated_config["agent_strategy"]["version"] = current_version + 1

            # Save back to database
            cur.execute("""
                UPDATE configurations
                SET config_data = %s,
                    updated_at = NOW()
                WHERE config_id = %s AND user_id = %s
            """, (Json(updated_config), config_id, user_id))

            conn.commit()

            return {
                "success": True,
                "config_id": config_id,
                "updated_fields": list(updates.keys())
            }
```

**Usage Examples:**

**Agent Bot - Update Strategy:**
```python
update_full_config(
    config_id="abc123",
    updates={
        "agent_strategy": {
            "content": "# Updated Strategy\n\nBuy when RSI < 30..."
        }
    }
)
```

**Scheduled Bot - Update Extraction:**
```python
update_full_config(
    config_id="abc123",
    updates={
        "extraction": {
            "timeframe": "4h",
            "candle_limit": 100,
            "data_sources": ["rsi", "macd", "volume"]
        }
    }
)
```

**Scheduled Bot - Update Multiple Sections:**
```python
update_full_config(
    config_id="abc123",
    updates={
        "extraction": {
            "timeframe": "1h"
        },
        "decision": {
            "system_prompt": "You are a conservative trader..."
        },
        "trading": {
            "leverage": 10,
            "max_position_percent": 25
        }
    }
)
```

### 4. Main Chat Handler

**Implementation:**
```python
import anthropic
from anthropic.types import MessageParam, ToolResultBlockParam, ToolUseBlock

@app.post("/api/v2/builder/chat")
async def strategy_builder_chat(
    request: StrategyBuilderChatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Strategy builder chat endpoint with function calling."""

    # Initialize Anthropic client
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Prepare messages
    messages = request.conversation_history.copy()
    messages.append({
        "role": "user",
        "content": request.message
    })

    # Call Claude with tools
    response = client.messages.create(
        model="claude-haiku-4-5-20250929",
        max_tokens=4096,
        system=STRATEGY_BUILDER_SYSTEM_PROMPT,
        messages=messages,
        tools=[
            QUERY_AVAILABLE_DATA_TOOL,
            GET_CURRENT_PRICE_TOOL,
            LOAD_STRATEGY_TOOL,
            SAVE_STRATEGY_TOOL
        ]
    )

    # Handle function calls
    tool_calls = []
    strategy_updated = False

    while response.stop_reason == "tool_use":
        # Extract tool calls
        tool_results = []

        for content_block in response.content:
            if isinstance(content_block, ToolUseBlock):
                tool_name = content_block.name
                tool_input = content_block.input

                # Execute tool
                if tool_name == "query_available_data":
                    result = await query_available_data(tool_input["category"])
                elif tool_name == "get_current_price":
                    result = await get_current_price(tool_input["symbol"])
                elif tool_name == "load_strategy":
                    result = await load_strategy(
                        tool_input["config_id"],
                        current_user.user_id
                    )
                elif tool_name == "save_strategy":
                    result = await save_strategy(
                        tool_input["config_id"],
                        current_user.user_id,
                        tool_input["strategy_content"],
                        tool_input.get("autonomously_editable", False)
                    )
                    strategy_updated = True

                # Record tool call
                tool_calls.append({
                    "name": tool_name,
                    "input": tool_input,
                    "result": result
                })

                # Prepare tool result for Claude
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": json.dumps(result)
                })

        # Continue conversation with tool results
        messages.append({
            "role": "assistant",
            "content": response.content
        })
        messages.append({
            "role": "user",
            "content": tool_results
        })

        # Get next response
        response = client.messages.create(
            model="claude-haiku-4-5-20250929",
            max_tokens=4096,
            system=STRATEGY_BUILDER_SYSTEM_PROMPT,
            messages=messages,
            tools=[
                QUERY_AVAILABLE_DATA_TOOL,
                GET_CURRENT_PRICE_TOOL,
                LOAD_STRATEGY_TOOL,
                SAVE_STRATEGY_TOOL
            ]
        )

    # Extract final text response
    final_response = ""
    for content_block in response.content:
        if hasattr(content_block, "text"):
            final_response += content_block.text

    # Update conversation history
    messages.append({
        "role": "assistant",
        "content": final_response
    })

    return StrategyBuilderChatResponse(
        response=final_response,
        conversation_history=messages,
        tool_calls=tool_calls,
        strategy_updated=strategy_updated
    )
```

---

## 🎨 Frontend Integration

### New Component: Universal AI Assistant Bottom Sheet

**File**: `frontend/components/UniversalAIAssistant.tsx` (new component)

**Features:**
- Framer-motion bottom sheet overlay
- Draggable (minimize to bar, expand to 80% screen)
- Works on ALL configure pages (agent, scheduled, signal_validation)
- Conversation history in React state
- Auto-refreshes config when AI makes changes

**UI States:**
1. **Closed** (default)
2. **Minimized** (just chat bar: "💬 AI Assistant")
3. **Expanded** (80% of screen height)

**Implementation:**

```typescript
import { motion, AnimatePresence } from 'framer-motion';

interface UniversalAIAssistantProps {
  configId: string;
  botType: 'agent' | 'scheduled' | 'signal_validation';
  onConfigUpdate: () => void;
}

export function UniversalAIAssistant({ configId, botType, onConfigUpdate }: UniversalAIAssistantProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (message: string) => {
    setLoading(true);

    const response = await fetch('/api/v2/assistant/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        config_id: configId,
        bot_type: botType,
        message: message,
        conversation_history: conversationHistory
      })
    });

    const data = await response.json();

    // Update conversation
    setConversationHistory(data.conversation_history);

    // If config was updated, refresh parent
    if (data.config_updated) {
      await onConfigUpdate();
    }

    setLoading(false);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ y: '100%' }}
          animate={{ y: isMinimized ? 'calc(100% - 60px)' : '20%' }}
          exit={{ y: '100%' }}
          drag="y"
          dragConstraints={{ top: 0, bottom: 0 }}
          dragElastic={0.1}
          onDragEnd={(e, info) => {
            if (info.offset.y > 100) setIsMinimized(true);
            if (info.offset.y < -100) setIsMinimized(false);
          }}
          className="fixed inset-x-0 bottom-0 bg-white dark:bg-gray-900 rounded-t-xl shadow-2xl border-t"
          style={{ height: '80vh', zIndex: 50 }}
        >
          {/* Drag handle */}
          <div className="w-full flex justify-center py-2 cursor-grab">
            <div className="w-12 h-1 bg-gray-300 rounded-full" />
          </div>

          {/* Header */}
          <div className="px-4 pb-2 border-b flex justify-between items-center">
            <h3 className="font-semibold">AI Assistant</h3>
            <button onClick={() => setIsOpen(false)}>✕</button>
          </div>

          {/* Chat content */}
          <div className="flex-1 overflow-y-auto p-4">
            {/* Message list */}
          </div>

          {/* Input */}
          <div className="p-4 border-t">
            <input
              type="text"
              placeholder="Ask me anything about configuring your bot..."
              className="w-full px-4 py-2 border rounded-lg"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  sendMessage(e.currentTarget.value);
                  e.currentTarget.value = '';
                }
              }}
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

### Trigger Button in Configure Pages

**For Agent Bots** (`frontend/app/forge/[id]/configure/page.tsx`):

```typescript
import { UniversalAIAssistant } from '@/components/UniversalAIAssistant';

export default function AgentConfigurePage() {
  const [aiOpen, setAiOpen] = useState(false);

  return (
    <div>
      {/* Header with AI button */}
      <div className="flex justify-between items-center mb-4">
        <h2>Strategy Configuration</h2>
        <Button onClick={() => setAiOpen(true)}>
          <Sparkles className="w-4 h-4 mr-2" />
          AI Assistant
        </Button>
      </div>

      {/* Strategy editor content */}
      <StrategyEditor {...props} />

      {/* AI Assistant bottom sheet */}
      <UniversalAIAssistant
        configId={configId}
        botType="agent"
        isOpen={aiOpen}
        onClose={() => setAiOpen(false)}
        onConfigUpdate={() => refreshConfig()}
      />
    </div>
  );
}
```

**For Scheduled Bots** (`frontend/app/forge/[id]/page.tsx`):

```typescript
// Same pattern, just different botType
<UniversalAIAssistant
  configId={configId}
  botType="scheduled"
  isOpen={aiOpen}
  onClose={() => setAiOpen(false)}
  onConfigUpdate={() => refreshConfig()}
/>
```

**Button Placement:**
- Top-right of configure page header
- Only visible on configure pages (not on Monitor or Timeline)
- Consistent across all bot types

---

## 💾 Conversation History Management

### Option A: Frontend-Only (Simplest)

**Pros:**
- Zero backend storage
- Completely stateless
- No cleanup needed

**Cons:**
- Lost on page refresh
- Can't resume on different device

**Implementation:**
- Just store in React state
- Optionally localStorage for persistence

### Option B: Redis Cache (Better UX)

**Pros:**
- Survives page refresh
- Can resume conversation
- Auto-cleanup with TTL

**Cons:**
- Slight backend complexity
- Redis dependency

**Implementation:**
```python
# Save conversation after each response
await redis_client.setex(
    f"builder:conversation:{user_id}:{config_id}",
    3600,  # 1 hour TTL
    json.dumps(conversation_history)
)

# Load on reconnect
history = await redis_client.get(f"builder:conversation:{user_id}:{config_id}")
if history:
    conversation_history = json.loads(history)
```

**Recommendation**: Start with **Option A** (frontend-only), add Redis later if users request it.

---

## 🧪 Testing Strategy

### Unit Tests

**Test Function Tools:**
```python
# test_builder_tools.py

async def test_query_available_data():
    result = await query_available_data("technical")
    assert "RSI" in result
    assert "MACD" in result

async def test_save_and_load_strategy():
    strategy = "# Test Strategy\n\nBuy when RSI < 30"

    # Save
    await save_strategy(config_id, user_id, strategy)

    # Load
    loaded = await load_strategy(config_id, user_id)
    assert loaded["content"] == strategy
    assert loaded["version"] == 1
```

**Test API Endpoint:**
```python
async def test_builder_chat_endpoint():
    response = client.post("/api/v2/builder/chat", json={
        "config_id": test_config_id,
        "message": "Help me build a BTC strategy",
        "conversation_history": []
    })

    assert response.status_code == 200
    assert "response" in response.json()
    assert "conversation_history" in response.json()
```

### Integration Tests

**Full Conversation Flow:**
```python
async def test_full_strategy_building_flow():
    # 1. User asks for help
    response1 = await chat("Help me build a BTC momentum strategy")
    assert "RSI" in response1["response"] or "MACD" in response1["response"]

    # 2. User provides details
    response2 = await chat(
        "Use RSI on 1h with threshold of 30/70",
        history=response1["conversation_history"]
    )

    # 3. Claude saves strategy
    # Should have called save_strategy()
    assert response2["strategy_updated"] == True

    # 4. Verify strategy was saved
    strategy = await load_strategy(config_id, user_id)
    assert "RSI" in strategy["content"]
    assert "30" in strategy["content"]
```

### Manual Testing Checklist

- [ ] Chat responds with helpful strategy suggestions
- [ ] Can query available data sources
- [ ] Can validate prices with get_current_price
- [ ] Can load existing strategy for editing
- [ ] Can save new strategy
- [ ] Can edit and re-save strategy (version increments)
- [ ] Conversation history persists across messages
- [ ] Function calling works reliably
- [ ] Frontend displays responses correctly
- [ ] Strategy updates trigger frontend refresh

---

## 📊 Cost Analysis

### Claude Haiku Pricing

**Input**: $0.25 per 1M tokens
**Output**: $1.25 per 1M tokens

### Typical Strategy Building Session

**Assumptions:**
- 20 messages back and forth
- System prompt: ~2,000 tokens (sent each time)
- Average user message: ~50 tokens
- Average Claude response: ~500 tokens
- Tool results: ~200 tokens per call
- Total conversation: ~15,000 tokens input, ~10,000 tokens output

**Cost per session:**
- Input: 15,000 tokens × $0.25 / 1M = **$0.00375**
- Output: 10,000 tokens × $1.25 / 1M = **$0.0125**
- **Total: ~$0.016 per session** (less than 2 cents!)

**At scale (1000 users/month):**
- 1000 sessions × $0.016 = **$16/month**

**Conclusion**: Extremely cheap. Use Haiku without worry.

---

## 🚀 Implementation Plan

### Phase 1: Backend Core (3-4 hours)

**Tasks:**
1. Create `api/assistant.py` with chat endpoint
2. Implement 3 function calling tools (with deep merge for updates)
3. Write system prompt with bot-type awareness
4. Test with curl/Postman for all 3 bot types

**Validation:**
- Can chat with Claude about all bot types
- Tools execute correctly for agent, scheduled, signal_validation
- Full configs load and update properly
- Deep merge works for partial updates

### Phase 2: Frontend - Bottom Sheet Component (3-4 hours)

**Tasks:**
1. Create `UniversalAIAssistant.tsx` with framer-motion
2. Implement draggable bottom sheet (minimize/expand)
3. Add header button trigger to configure pages
4. Wire up chat API calls
5. Handle config refresh on updates

**Validation:**
- Bottom sheet slides up/down smoothly
- Can drag to minimize/expand
- Header button appears on all configure pages
- Chat works end-to-end
- Config refreshes when AI makes changes

### Phase 3: Testing & Polish (2 hours)

**Tasks:**
1. Write unit tests for tools (all 3)
2. Write integration tests (agent, scheduled bots)
3. Add error handling (Claude API errors, tool failures)
4. Mobile responsive testing
5. Add loading states and animations

**Validation:**
- All tests pass
- Works on mobile (bottom sheet feels natural)
- Errors handled gracefully
- Good UX (smooth animations, loading states)

### Total Time: 8-10 hours of focused work

---

## 🔄 Future Enhancements (Optional)

### 1. Streaming Responses

Instead of waiting for full response, stream tokens:

```python
with client.messages.stream(
    model="claude-haiku-4-5-20250929",
    max_tokens=4096,
    system=STRATEGY_BUILDER_SYSTEM_PROMPT,
    messages=messages,
    tools=[...]
) as stream:
    for text in stream.text_stream:
        yield text  # Stream to frontend via SSE
```

**Benefit**: Better UX, responses appear faster

### 2. Multi-Model Support

Add model selector in UI:
- Claude Haiku (fast, cheap)
- Claude Sonnet (smarter, more expensive)
- Allow users to choose

### 3. Strategy Templates

Pre-built strategy templates users can customize:
- Momentum strategies
- Mean reversion
- Breakout strategies
- Multi-indicator combos

### 4. Strategy Validation

Add a `validate_strategy` tool that:
- Checks if indicators are available
- Validates logic is executable
- Suggests improvements

### 5. Conversation Persistence

Store conversation in Redis with 24-hour TTL:
- Resume on page refresh
- Continue on different device
- Better UX

---

## ❓ Open Questions

### 1. Get Current Price Tool

**Question**: Do we need `get_current_price` tool?

**Options:**
- **Option A**: Include it (useful for validating price ranges)
- **Option B**: Skip it (simpler, Claude can just suggest ranges without validation)

**Recommendation**: Start with Option B (3 tools total), add later if users request price validation.

### 2. Conversation Length Limits

**Question**: Should we limit conversation history length?

**Context**: Anthropic has 200k token context window, but costs increase with longer conversations.

**Options:**
- **Option A**: No limit (simple, users can iterate forever)
- **Option B**: Limit to last 20 messages (keeps costs low)
- **Option C**: Truncate old messages but keep strategy context

**Recommendation**: Start with Option A, add limits if costs become an issue.

### 3. Strategy Versioning

**Question**: Should we track full version history of strategies?

**Options:**
- **Option A**: Just increment version number (current approach)
- **Option B**: Store full history in separate table (can view old versions)

**Recommendation**: Start with Option A (simpler), add history if users request it.

### 4. Bottom Sheet Z-Index

**Question**: What if bottom sheet overlaps other modals?

**Options:**
- **Option A**: High z-index (z-50), always on top
- **Option B**: Medium z-index, can be covered by critical modals

**Recommendation**: Option A - AI assistant should be on top of everything except critical alerts.

---

## 📚 References

### Anthropic Documentation
- Messages API: https://docs.anthropic.com/en/api/messages
- Function Calling: https://docs.anthropic.com/en/docs/build-with-claude/tool-use
- Haiku Model: https://docs.anthropic.com/en/docs/about-claude/models#model-comparison

### Existing Code
- `core/services/llm_service.py` - LLM provider factory (for reference)
- `agent/mcp_server.py` - Current MCP tools (reuse query_market_data logic)
- `api/agent.py` - Current agent endpoints (for auth patterns)

---

## 🎯 Success Criteria

### MVP Launch (Phase 1-3)

- [ ] API endpoint responds within 2 seconds
- [ ] Function calling works 100% of time (Claude Haiku is reliable)
- [ ] Strategies save correctly to database
- [ ] Frontend chat interface functional
- [ ] Users can build complete strategy in <10 messages
- [ ] Cost per session < $0.02

### Post-Launch Metrics

- **Usage**: Track sessions per day, messages per session
- **Quality**: User satisfaction with generated strategies
- **Activation**: % of built strategies that get activated
- **Cost**: Total monthly Claude API spend
- **Errors**: Function calling failure rate (should be ~0%)

---

## 🎉 Summary

This approach is **dramatically simpler** than the complex PM2/SDK/MCP architecture, and **universal** for all bot types:

**What We're Building:**
- Single API endpoint (`POST /api/v2/assistant/chat`)
- Bottom sheet modal with framer-motion (draggable, collapsible)
- Header button trigger (page-specific, not floating)
- Claude Haiku function calling (3 tools: query data, load config, update config)
- Works for ALL 3 bot types: agent, scheduled, signal_validation
- Simple conversation state in React
- Full config access (not section-specific)

**What We're NOT Building:**
- ❌ PM2 services
- ❌ Claude SDK integration
- ❌ MCP servers
- ❌ WebSocket infrastructure
- ❌ Complex session management
- ❌ Section-specific tools
- ❌ Separate endpoints per bot type

**Key Features:**
- ✅ See config while chatting (bottom sheet overlay)
- ✅ Minimize to just chat bar
- ✅ Mobile-friendly (native bottom sheet pattern)
- ✅ Universal (works for all bot types)
- ✅ Full config editing (not just strategies)

**Time to Ship**: 8-10 hours vs weeks

**Cost**: ~$16/month for 1000 users vs infrastructure overhead

**Reliability**: Rock-solid (Claude's function calling is bulletproof)

Let's build this! 🚀
