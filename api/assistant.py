"""
Universal AI Assistant API - Chat endpoint for bot configuration

Provides AI assistance for configuring all bot types (agent, scheduled, signal_validation)
using Claude Haiku with function calling.
"""

import os
import json
from typing import List, Dict, Any, Literal
from datetime import datetime

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from psycopg2.extras import Json

from core.common.db import get_db_connection
from core.common.logger import logger
from core.auth.supabase_auth import get_current_user_v2, AuthenticatedUser


router = APIRouter(prefix="/api/v2", tags=["assistant"])


# ============================================================================
# Request/Response Models
# ============================================================================

class AssistantChatRequest(BaseModel):
    config_id: str
    bot_type: Literal["agent", "scheduled", "signal_validation"]
    message: str
    conversation_history: List[Dict[str, Any]] = []


class AssistantChatResponse(BaseModel):
    response: str
    conversation_history: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]] = []
    config_updated: bool = False


# ============================================================================
# System Prompt
# ============================================================================

def get_system_prompt(bot_type: str, config_id: str) -> str:
    """Generate system prompt based on bot type."""

    return f"""You are the Strategy Advisor for ggbots.ai — an AI assistant that helps users create and configure their trading bots. Think of yourself as a guide helping someone bring their trading bot to life.

Your job is to have a conversation that results in a **working bot with a personality and strategy**.

## Current Context
- Bot Type: {bot_type}
- Config ID: {config_id}

## First Interaction Protocol

**ALWAYS start with these two questions:**

1. "What's your trading experience level?"
   - Inexperienced / Beginner
   - Intermediate
   - Advanced / Experienced

2. "Do you have a strategy in mind already?"
   - No, not yet
   - Yes, I have a specific idea
   - Sort of / vague idea

Based on their answers, adapt your approach using one of the 4 scenarios below.

---

## Adaptive Response Framework

### Scenario A: Inexperienced + No Strategy
**Character Creation Mode** — Make bot creation fun and accessible.

**Approach:**
- Frame it as creating a character: "Let's create your bot's personality!"
- Ask evocative questions about the bot's traits:
  - "Should your bot be **patient** and wait for the perfect moment, or **aggressive** and always looking for action?"
  - "Should it **trust the crowd** or **fade the crowd**?"
  - "Should it **react to news and hype**, or **ignore the noise** and just watch the charts?"
  - "What should we **name** it?"
- Use personality archetypes if helpful (e.g., "The Contrarian", "The Momentum Rider", "The Patient Sniper")
- Translate personality choices into concrete strategy elements
- Keep it playful and engaging — they're bringing a little trading creature to life

**Example Opening:**
> "No problem! Let's create your bot's personality. Think of it like creating a character — what kind of trader should your bot be?"

---

### Scenario B: Inexperienced + Has Vague Idea
**Educational Translator Mode** — Help them flesh out rough ideas.

**Approach:**
- Listen to their vague input (e.g., "I heard RSI is good" or "buy low sell high")
- Ask clarifying questions to understand what they're imagining
- Explain concepts simply without being condescending
- Build something concrete from their rough idea
- Suggest complementary indicators or approaches
- Validate their intuition while adding structure

**Example Opening:**
> "Cool! Tell me more about your idea. What made you interested in that approach?"

---

### Scenario C: Experienced + No Specific Strategy
**Thesis Exploration Mode** — Go deeper into philosophy and worldview.

**Approach:**
- Ask about their **thesis**: "What do you think moves crypto prices?"
- Explore their philosophy: "Are you more about technicals, smart money flows, or sentiment and narrative?"
- Identify market conditions they want to exploit
- Discuss setups, edge, and market structure
- Help translate their worldview into a concrete strategy
- Respect their knowledge — this is a peer conversation

**Example Opening:**
> "Got it. What's your thesis? Are there specific market conditions or setups you're looking to exploit?"

---

### Scenario D: Experienced + Has Strategy
**Get Out of Their Way Mode** — Translate their strategy to config quickly.

**Approach:**
- Let them describe it
- Ask minimal clarifying questions (only what's needed for config)
- Translate their strategy to bot config efficiently
- Don't waste their time with basics
- Respect that they know what they're doing

**Example Opening:**
> "Perfect. Describe your strategy and I'll help translate it into a working bot config."

---

## Platform Capabilities

When users need to know what's available, you can reference these data sources:

### 32 Data Sources Across 7 Categories:

**1. Technical Analysis (21 indicators)**
- RSI, MACD, Bollinger Bands, Volume, Price (OHLC)
- EMA, SMA, ATR, Stochastic RSI, CCI, Williams %R, MFI
- Support/Resistance, Pivot Points, Fibonacci, Chart Patterns
- **7 timeframes**: 5m, 15m, 30m, 1h, 4h, 1d, 1w

**2. Trading Signals**
- ggShot AI Signals (AI-filtered signals with confidence scores)

**3. On-Chain Analytics**
- BTC Total Value Locked (TVL)
- Whale Activity

**4. Derivatives & Leverage**
- BTC Funding Rate
- ETH Funding Rate

**5. Sentiment & Social**
- Twitter Sentiment

**6. News & Regulatory**
- Crypto News Feed

**7. Macro Economics**
- VIX (Volatility Index)
- DXY (Dollar Index)
- CPI (Consumer Price Index)
- NFP (Non-Farm Payrolls)

### Trading Modes
- **Paper Trading**: Risk-free testing with $10k virtual account
- **Symphony.io**: Live CEX trading with real money (premium feature)
- **AsterDEX**: Decentralized futures (33 symbols, up to 20x leverage, premium)

---

## Configuration Structure

You'll be configuring these sections using the `update_full_config` tool:

### For ALL Bot Types:

**decision.user_prompt** (REQUIRED)
- This is where the strategy goes (in markdown format)
- Used for agent, scheduled, AND signal_validation bots
- Should include: entry conditions, exit conditions, position sizing, risk management, timing

**Example strategy structure:**
```markdown
# Strategy Name

## Entry Rules
- Specific conditions for going LONG
- Specific conditions for going SHORT

## Exit Rules
- Take profit conditions
- Stop loss conditions

## Position Sizing
- How to size trades based on confidence/conditions

## Risk Management
- Max position size
- Max daily loss
- Stop loss rules

## Timing
- Check frequency
- Wait periods between trades
```

### Additional Sections (for scheduled/signal_validation bots):

**extraction** (what data to fetch)
```json
{{
  "selected_data_sources": {{
    "technical_analysis": {{
      "data_points": ["RSI", "MACD", "Volume"],
      "timeframes": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
    }}
  }}
}}
```

**llm_config** (which model to use)
```json
{{
  "provider": "openrouter",
  "model": "grok",
  "reasoning_tier": "standard"
}}
```

Available models: `grok`, `deepseek`, `gemini`, `claude`, `gpt`, `kimi`, `qwen`

Available reasoning tiers:
- `economy`: Fast/cheap (good for frequent checks)
- `standard`: Balanced (default, recommended)
- `premium`: Best quality (extended reasoning)

**trading** (execution settings)
```json
{{
  "leverage": 10,
  "position_sizing": {{
    "method": "confidence_based",
    "max_position_percent": 25
  }},
  "risk_management": {{
    "max_positions": 3,
    "default_stop_loss_percent": 2,
    "default_take_profit_percent": 5
  }}
}}
```

Position sizing methods:
- `fixed_usd`: Fixed dollar amount per trade
- `account_percent`: Fixed % of account per trade
- `confidence_based`: Variable sizing based on signal confidence

---

## Available Tools

You have access to 3 tools via function calling:

1. **query_available_data(category)**
   - Get detailed list of available data sources
   - Categories: "all", "technical", "signals", "on_chain", "derivatives", "sentiment", "news", "macro"
   - Use when user asks "what data can I use?"

2. **load_full_config(config_id)**
   - Load the current bot configuration
   - Use at start of conversation to see what's already configured
   - Use when user asks "what's my bot doing now?"

3. **update_full_config(config_id, updates)**
   - Save configuration changes (supports partial updates via deep merge)
   - Use after you've gathered enough info to update the config
   - Explain what you're changing and why
   - Can update just one field or entire sections

---

## Conversation Guidelines

### DO:
- **Adapt to user experience level** — beginners get hand-holding, experts get efficiency
- **Make it conversational** — this is a chat, not a form
- **Ask follow-up questions** — understand before configuring
- **Explain what you're doing** — when you update config, say what and why
- **Support multiple approaches** — both "philosophical worldview bots" and "rigid rules bots" are valid
- **Use personality framing for beginners** — "what kind of bot do you want to create?"
- **Name the bot** — encourage users to give their bot a personality/name
- **End with something concrete** — working config with clear strategy

### DON'T:
- **Force one approach on everyone** — adapt to what the user wants
- **Be prescriptive** — don't say "you should do X"
- **Overwhelm beginners** — don't dump all 32 data sources at once
- **Bore experienced traders** — get out of their way
- **Make it feel like a form** — avoid "fill out these fields" vibe
- **Invent capabilities** — only suggest data sources that actually exist
- **Update config without explanation** — always tell user what you're changing

---

## Important Technical Rules

1. **Strategy field**: ALWAYS use `decision.user_prompt` for strategy (for ALL bot types)
   - `agent_strategy` is deprecated — do NOT use it
   - Strategy should be markdown format with clear executable instructions

2. **Data sources**: Only suggest data sources from the 32 available (use `query_available_data` if unsure)

3. **Risk management**: Always include stop loss and take profit rules in strategies

4. **Reasoning tier**: Use `reasoning_tier` (economy/standard/premium), NOT `thinking_mode`
   - `thinking_mode` is deprecated but kept for backward compatibility

5. **Config updates**: Use partial updates via `update_full_config` — you don't need to send entire config, just the fields you're changing

6. **User keys**: Users cannot provide their own API keys anymore — all keys are platform-managed

7. **CRITICAL - Update format**: When calling `update_full_config`, send fields DIRECTLY at the top level.
   - ✅ CORRECT: `{{"decision": {{...}}, "extraction": {{...}}}}`
   - ❌ WRONG: `{{"config_data": {{...}}, "config_name": "..."}}` — NEVER wrap in config_data!
   - The `config_data` and `config_name` keys are reserved for internal use

8. **Valid analysis frequencies**: Only use these values for `decision.analysis_frequency`:
   - `5m`, `15m`, `30m`, `1h`, `4h`, `1d` (for scheduled bots)
   - Do NOT use `6h`, `2h`, `12h`, or `1w` — they are not supported by the scheduler

---

## Examples of Good Openings

**For first-time user:**
> "Hey! I'm here to help you create your trading bot. Quick questions: What's your trading experience level? And do you have a strategy in mind already, or should we brainstorm one together?"

**After they answer (Scenario A):**
> "Perfect! Let's create your bot's personality. Think of it like building a character — what kind of trader should your bot be? Patient and careful, or aggressive and opportunistic?"

**After they answer (Scenario D):**
> "Great! Describe your strategy and I'll translate it into a working bot config. What are your entry/exit conditions?"

---

## Success Criteria

A successful interaction results in:
1. ✅ User feels understood and supported (not talked down to or overwhelmed)
2. ✅ Bot has a clear, executable strategy in `decision.user_prompt`
3. ✅ Config is complete and valid for the bot type
4. ✅ User understands what their bot will do
5. ✅ (Bonus) Bot has a name/personality that resonates with user

---

## Remember

You're not just filling out a form — you're helping someone **bring a trading bot to life**. Make it engaging, adaptive, and fun. The user should feel like they created something, not just configured something.
"""


# ============================================================================
# Function Calling Tools
# ============================================================================

TOOL_QUERY_AVAILABLE_DATA = {
    "name": "query_available_data",
    "description": "Query available data sources and indicators. Returns detailed information about what data the platform can provide.",
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["all", "technical", "signals", "on_chain", "derivatives", "sentiment", "news", "macro"],
                "description": "Which category of data to query. Use 'all' to see everything."
            }
        },
        "required": ["category"]
    }
}

TOOL_LOAD_FULL_CONFIG = {
    "name": "load_full_config",
    "description": "Load complete bot configuration. Returns entire config_data JSONB structure including all settings.",
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

TOOL_UPDATE_FULL_CONFIG = {
    "name": "update_full_config",
    "description": "Update bot configuration. Supports partial updates (deep merge). You can update just one field or multiple sections at once.",
    "input_schema": {
        "type": "object",
        "properties": {
            "config_id": {
                "type": "string",
                "description": "Bot configuration ID"
            },
            "updates": {
                "type": "object",
                "description": "Configuration updates (partial or full). Will be deep merged with existing config. For ALL bot types, use 'decision.user_prompt' for the trading strategy. Other sections: 'extraction', 'trading', 'llm_config'. Do NOT use 'agent_strategy' - it is deprecated."
            }
        },
        "required": ["config_id", "updates"]
    }
}


async def query_available_data(category: str) -> Dict[str, Any]:
    """Return list of available data sources."""

    all_data = {
        "technical": {
            "description": "Technical indicators across 7 timeframes",
            "indicators": ["RSI", "MACD", "Bollinger Bands", "Volume", "Price", "EMA", "SMA", "ATR", "Stochastic RSI"],
            "timeframes": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        },
        "signals": {
            "description": "AI-filtered trading signals",
            "sources": ["ggShot AI Signals"]
        },
        "on_chain": {
            "description": "Blockchain analytics",
            "sources": ["BTC TVL", "Whale Activity"]
        },
        "derivatives": {
            "description": "Futures market data",
            "sources": ["BTC Funding Rate", "ETH Funding Rate"]
        },
        "sentiment": {
            "description": "Social sentiment analysis",
            "sources": ["Twitter Sentiment"]
        },
        "news": {
            "description": "Crypto news aggregation",
            "sources": ["Crypto News Feed"]
        },
        "macro": {
            "description": "Macroeconomic indicators",
            "sources": ["VIX", "DXY", "CPI", "NFP"]
        }
    }

    if category == "all":
        return all_data
    elif category in all_data:
        return {category: all_data[category]}
    else:
        return {"error": f"Unknown category: {category}"}


async def load_full_config(config_id: str, user_id: str) -> Dict[str, Any]:
    """Load complete configuration from database."""

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT config_type, config_data, config_name
                    FROM configurations
                    WHERE config_id = %s AND user_id = %s
                """, (config_id, user_id))

                result = cur.fetchone()
                if not result:
                    raise ValueError("Configuration not found")

                config_type, config_data, config_name = result

                # Extract selected_pair from config_data JSONB if it exists
                selected_pair = config_data.get("selected_pair") if config_data else None

                return {
                    "config_type": config_type,
                    "config_name": config_name,
                    "selected_pair": selected_pair,
                    "config_data": config_data
                }

    except Exception as e:
        logger.error(f"Failed to load config {config_id}: {e}")
        raise


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
    """Update bot configuration with deep merge."""

    # Validate updates - reject reserved/invalid keys
    FORBIDDEN_KEYS = {'config_data', 'config_name', 'config_id', 'user_id'}
    invalid_keys = FORBIDDEN_KEYS.intersection(updates.keys())
    if invalid_keys:
        raise ValueError(
            f"Invalid update keys: {invalid_keys}. "
            "Send fields directly (e.g., 'decision', 'extraction'), not wrapped in config_data."
        )

    # Validate analysis_frequency if present
    VALID_FREQUENCIES = {'5m', '15m', '30m', '1h', '4h', '1d', 'signal_driven', 'agent_driven'}
    if 'decision' in updates and 'analysis_frequency' in updates.get('decision', {}):
        freq = updates['decision']['analysis_frequency']
        if freq not in VALID_FREQUENCIES:
            raise ValueError(
                f"Invalid analysis_frequency: '{freq}'. "
                f"Must be one of: {sorted(VALID_FREQUENCIES)}"
            )

    try:
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

                # Save back to database
                cur.execute("""
                    UPDATE configurations
                    SET config_data = %s,
                        updated_at = NOW()
                    WHERE config_id = %s AND user_id = %s
                """, (Json(updated_config), config_id, user_id))

                conn.commit()

                logger.bind(
                    user_id=user_id,
                    config_id=config_id,
                    updated_fields=list(updates.keys())
                ).info("AI assistant updated bot configuration")

                return {
                    "success": True,
                    "config_id": config_id,
                    "updated_fields": list(updates.keys())
                }

    except Exception as e:
        logger.error(f"Failed to update config {config_id}: {e}")
        raise


# ============================================================================
# Main Chat Endpoint
# ============================================================================

@router.post("/assistant/chat", response_model=AssistantChatResponse)
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

    Uses Claude Haiku with function calling.
    """

    try:
        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Get system prompt
        system_prompt = get_system_prompt(request.bot_type, request.config_id)

        # Prepare messages
        messages = request.conversation_history.copy()
        messages.append({
            "role": "user",
            "content": request.message
        })

        # Call Claude with tools
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
            tools=[
                TOOL_QUERY_AVAILABLE_DATA,
                TOOL_LOAD_FULL_CONFIG,
                TOOL_UPDATE_FULL_CONFIG
            ]
        )

        # Handle function calls in a loop
        tool_calls = []
        config_updated = False

        while response.stop_reason == "tool_use":
            # Extract tool calls
            tool_results = []

            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.input

                    logger.bind(
                        tool_name=tool_name,
                        tool_input=tool_input
                    ).info("AI assistant calling tool")

                    # Execute tool
                    try:
                        if tool_name == "query_available_data":
                            result = await query_available_data(tool_input["category"])

                        elif tool_name == "load_full_config":
                            result = await load_full_config(
                                tool_input["config_id"],
                                current_user.user_id
                            )

                        elif tool_name == "update_full_config":
                            result = await update_full_config(
                                tool_input["config_id"],
                                current_user.user_id,
                                tool_input["updates"]
                            )
                            config_updated = True

                        else:
                            result = {"error": f"Unknown tool: {tool_name}"}

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

                    except Exception as e:
                        logger.error(f"Tool execution error: {e}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": json.dumps({"error": str(e)})
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
                model="claude-haiku-4-5-20251001",
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=[
                    TOOL_QUERY_AVAILABLE_DATA,
                    TOOL_LOAD_FULL_CONFIG,
                    TOOL_UPDATE_FULL_CONFIG
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

        logger.bind(
            user_id=current_user.user_id,
            config_id=request.config_id,
            bot_type=request.bot_type,
            tool_calls_count=len(tool_calls),
            config_updated=config_updated
        ).info("AI assistant chat completed")

        return AssistantChatResponse(
            response=final_response,
            conversation_history=messages,
            tool_calls=tool_calls,
            config_updated=config_updated
        )

    except Exception as e:
        logger.error(f"AI assistant chat error: {e}")
        raise HTTPException(500, f"Chat error: {str(e)}")


# ============================================================================
# Strategy Generation Endpoint (One-Shot)
# ============================================================================

class GenerateStrategyRequest(BaseModel):
    """Request model for one-shot strategy generation."""
    description: str
    symbol: str = "BTC/USDT"
    timeframe: str = "1h"


class GenerateStrategyResponse(BaseModel):
    """Response model for strategy generation."""
    success: bool
    user_prompt: str = ""
    error: str | None = None


STRATEGY_GENERATION_PROMPT = """You are a trading strategy translator. Your job is to convert a user's description of their trading philosophy, worldview, or bot personality into a concrete, executable trading strategy.

The user will provide:
- A description of how they want their bot to trade (could be personality-based, philosophical, or specific)
- The symbol they want to trade (e.g., BTC/USDT)
- The timeframe for analysis (e.g., 1h, 4h)

Your task is to output ONLY the strategy text (user_prompt) that will be used by the trading decision engine. The strategy should be in markdown format with clear sections.

## Output Format

Your response should follow this structure:

```
# [Bot Name/Personality]

## Identity
[1-2 sentences describing the bot's trading personality and philosophy]

## Entry Rules
### Long Entries
- [Specific conditions for going long]
- [Include indicators, thresholds, sentiment conditions]

### Short Entries
- [Specific conditions for going short]
- [Include indicators, thresholds, sentiment conditions]

## Exit Rules
- Take profit: [Specific conditions]
- Stop loss: [Specific conditions]
- Early exit: [Optional conditions]

## Confidence Levels
- 0.75+: [High confidence conditions]
- 0.60-0.75: [Medium confidence conditions]
- 0.55-0.60: [Lower confidence conditions]
- Below 0.55: Pass (wait for better setup)

## Risk Management
- Max position size: [Guidance]
- Stop loss placement: [Guidance]
```

## Guidelines

1. **Be specific**: Convert vague descriptions into concrete rules with actual indicator values
2. **Include confidence thresholds**: Always specify when to trade with high vs medium vs low confidence
3. **Add risk management**: Every strategy needs stop loss and take profit guidance
4. **Match the personality**: If they want a cautious bot, reflect that in the rules. If aggressive, likewise.
5. **Keep it executable**: The trading engine will read this, so make it clear and actionable
6. **Use available indicators**: RSI, MACD, Bollinger Bands, EMA, SMA, Stochastic, CCI, ATR, OBV, VWAP, ADX, Aroon, etc.
7. **Consider sentiment**: Can include twitter_sentiment, funding rates, whale_activity if relevant to their description

## Examples

If user says "A bot that fades the crowd when everyone is panicking or euphoric":
- Convert to: Mean-reversion strategy with RSI oversold/overbought levels, sentiment extremes triggering entries

If user says "A patient sniper that waits for the perfect moment":
- Convert to: High-threshold strategy with multiple confirmation requirements, only trading when 4+ indicators align

If user says "An aggressive scalper that catches quick moves":
- Convert to: Momentum-following strategy on lower timeframes, tight stops, quick profits

Now generate the strategy based on the user's description."""


@router.post("/assistant/generate-strategy", response_model=GenerateStrategyResponse)
async def generate_strategy_from_description(
    request: GenerateStrategyRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    One-shot strategy generation from user description.

    Takes a description of trading philosophy/personality and generates
    a complete trading strategy (user_prompt) for the decision engine.

    This is used during bot creation to convert the user's description
    into an actionable trading strategy.
    """
    try:
        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Build the user message
        user_message = f"""Generate a trading strategy based on this description:

**Description**: {request.description}
**Symbol**: {request.symbol}
**Timeframe**: {request.timeframe}

Convert this into a complete, executable trading strategy following the format in your instructions."""

        # Call Claude Haiku (fast and cheap for this task)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=STRATEGY_GENERATION_PROMPT,
            messages=[{
                "role": "user",
                "content": user_message
            }]
        )

        # Extract the response text
        strategy_text = ""
        for content_block in response.content:
            if hasattr(content_block, "text"):
                strategy_text += content_block.text

        if not strategy_text.strip():
            raise ValueError("Empty strategy generated")

        logger.bind(
            user_id=current_user.user_id,
            symbol=request.symbol,
            timeframe=request.timeframe,
            description_length=len(request.description)
        ).info("Generated trading strategy from description")

        return GenerateStrategyResponse(
            success=True,
            user_prompt=strategy_text.strip()
        )

    except Exception as e:
        logger.error(f"Strategy generation error: {e}")
        return GenerateStrategyResponse(
            success=False,
            user_prompt="",
            error=str(e)
        )


# ============================================================================
# Performance Analysis Endpoint
# ============================================================================

class AnalyzeResponse(BaseModel):
    """Response model for performance analysis."""
    success: bool
    config_id: str
    config_name: str
    trade_count: int
    message: str = ""
    report: Dict[str, Any] = {}


@router.get("/assistant/analyze/{config_id}", response_model=AnalyzeResponse)
async def analyze_bot_performance_endpoint(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Analyze a bot's trading performance.

    Returns comprehensive analysis including:
    - Basic stats (win rate, R:R ratio, P&L)
    - Direction breakdown (long vs short performance)
    - Confidence calibration (predicted vs actual win rates)
    - Exit reasoning classification
    - Pattern analysis (confirmation vs risk patterns)
    - Pattern combinations (best/worst 2-pattern combos)
    - Timeframe alignment analysis
    - AI-synthesized insights and recommendations
    """
    from core.services.performance_analyzer import analyze_bot_performance

    try:
        # Verify config ownership
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id FROM configurations WHERE config_id = %s
                """, (config_id,))
                result = cur.fetchone()

                if not result:
                    raise HTTPException(404, "Configuration not found")

                if result[0] != current_user.user_id:
                    raise HTTPException(403, "Not authorized to analyze this bot")

        # Run analysis
        report = await analyze_bot_performance(config_id, include_llm_insights=True)

        # Check minimum trades
        if report.trade_count < 10:
            return AnalyzeResponse(
                success=False,
                config_id=config_id,
                config_name=report.config_name,
                trade_count=report.trade_count,
                message=f"Need at least 10 trades for meaningful analysis. Current: {report.trade_count}",
                report={}
            )

        logger.bind(
            user_id=current_user.user_id,
            config_id=config_id,
            trade_count=report.trade_count
        ).info("Performance analysis completed via API")

        return AnalyzeResponse(
            success=True,
            config_id=config_id,
            config_name=report.config_name,
            trade_count=report.trade_count,
            report=report.to_dict()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Performance analysis error: {e}")
        raise HTTPException(500, f"Analysis error: {str(e)}")
