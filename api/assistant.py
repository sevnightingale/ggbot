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

    base_prompt = f"""You are an AI assistant for configuring trading bots on the ggbots.ai platform.

## Current Context
- Bot Type: {bot_type}
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
- EMA, SMA, ATR, Stochastic RSI

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
- **AsterDEX**: Decentralized futures trading (33 symbols, up to 20x leverage)

## Bot Type Configurations
"""

    if bot_type == "agent":
        base_prompt += """
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
The strategy should be clear, executable instructions including:
- **Entry Conditions**: When to open positions (long/short)
- **Exit Conditions**: Take profit and stop loss rules
- **Position Sizing**: How to size trades based on confidence
- **Risk Management**: Stop loss, take profit, max exposure
- **Timing**: Check frequency, wait periods between trades

**Example Strategy:**
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
- Low confidence (<0.5): Skip trade

## Timing
- Check conditions every 1 hour
- Maximum 1 trade per 4 hours
```
"""

    elif bot_type == "scheduled":
        base_prompt += """
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
    "llm_model": "grok"
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

**Configuration Sections:**

1. **Extraction** - What data to fetch
   - `timeframe`: Which timeframe to analyze ("5m", "15m", "30m", "1h", "4h", "1d")
   - `candle_limit`: How much historical data (50-500)
   - `data_sources`: Which indicators to use (e.g., ["rsi", "macd", "volume"])

2. **Decision** - How to analyze data
   - `system_prompt`: Instructions for the LLM decision maker
   - `llm_model`: Which model to use (grok, claude, gpt-5, etc.)

3. **Trading** - Trade execution settings
   - `leverage`: 1-100x leverage
   - `position_sizing`: "confidence_based" or "fixed"
   - `max_position_percent`: Max % of account per trade (1-100)
   - `risk_management.stop_loss_percent`: Stop loss %
   - `risk_management.take_profit_percent`: Take profit %

4. **LLM Config** - LLM provider settings
   - `provider`: "openrouter" or "anthropic"
   - `model`: Model name (grok, claude, gpt-5, deepseek, etc.)
   - `thinking_mode`: Enable extended reasoning (true/false)
"""

    else:  # signal_validation
        base_prompt += """
### Signal Validation Bots
Validate ggShot AI signals before acting on them.

**Configuration Structure:**
Same as scheduled bots, but focused on validating incoming signals rather than autonomous analysis.

The bot receives signals from ggShot and uses the LLM to decide whether to act on them based on:
- Signal confidence
- Current market conditions
- Additional data sources
- Risk management rules
"""

    base_prompt += """

## Available Tools

You have access to these tools via function calling:

1. **query_available_data**: Get list of available data sources (32 data points)
2. **load_full_config**: Load complete bot configuration
3. **update_full_config**: Save configuration changes (full or partial updates)

## Guidelines

1. Start by using `load_full_config()` to see what's currently configured
2. Ask clarifying questions to understand user goals
3. Suggest data sources that align with bot type and strategy
4. Validate that requested indicators are available (use query_available_data)
5. For agent bots: Write clear, executable strategies in markdown
6. For scheduled bots: Configure extraction, decision, trading, and llm_config sections
7. Use `update_full_config()` to save changes (partial updates are fine - you can update just one field)
8. Explain what you're changing and why
9. Iterate based on user feedback

## Important Rules

- ALWAYS use available data sources (don't invent indicators)
- Be specific about configuration values
- Include risk management for all trading bots
- Validate timeframes and data sources before suggesting them
- For agent strategies: Be detailed and executable
- For scheduled configs: Ensure all required fields are present
- When updating config, use deep merge (partial updates work)
"""

    return base_prompt


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
                "description": "Configuration updates (partial or full). Will be deep merged with existing config. You can update just 'agent_strategy' for agents, or 'extraction', 'decision', 'trading', 'llm_config' for scheduled bots."
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
                    SELECT config_type, config_data, config_name, selected_pair
                    FROM configurations
                    WHERE config_id = %s AND user_id = %s
                """, (config_id, user_id))

                result = cur.fetchone()
                if not result:
                    raise ValueError("Configuration not found")

                config_type, config_data, config_name, selected_pair = result

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
