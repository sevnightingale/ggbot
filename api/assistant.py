"""
Universal AI Assistant API - Chat endpoint for bot configuration

Provides AI assistance for configuring scheduled trading bots
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
    bot_type: Literal["scheduled"]
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

### Data Sources Across 6 Categories:

**1. Technical Analysis (21 indicators)**
- RSI, MACD, BB (Bollinger Bands), Volume, Price (OHLC)
- EMA, SMA, ATR, Stochastic, CCI, Williams_R, MFI
- OBV, VWAP, ADX, Aroon, PSAR, KC (Keltner), DC (Donchian)
- **7 timeframes**: 5m, 15m, 30m, 1h, 4h, 1d, 1w

**2. On-Chain Analytics**
- BTC Total Value Locked (TVL)
- Whale Activity

**3. Derivatives & Leverage**
- BTC Funding Rate
- ETH Funding Rate

**4. Sentiment & Social**
- Twitter Sentiment

**5. News & Regulatory**
- Crypto News Feed

**6. Macro Economics**
- VIX (Volatility Index)
- DXY (Dollar Index)
- CPI (Consumer Price Index)
- NFP (Non-Farm Payrolls)

### Trading Modes
- **Paper Trading**: Risk-free testing with $10k virtual account
- **Hyperliquid**: Live decentralized perp trading with real money

---

## Configuration Structure

You'll be configuring these sections using the `update_full_config` tool:

### Bot Configuration:

**decision.user_prompt** (REQUIRED)
- This is where the strategy goes (in markdown format)
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

### Additional Sections:

**extraction** (what data to fetch)
```json
{{
  "selected_data_sources": {{
    "technical_analysis": {{
      "data_points": ["RSI", "MACD", "Volume"],
      "timeframes": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"],
      "per_indicator_timeframes": {{
        "RSI": ["5m", "15m"],
        "MACD": ["4h", "1d"]
      }}
    }}
  }}
}}
```
Note: `per_indicator_timeframes` is optional. Indicators not listed use the global `timeframes`.

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
   - Categories: "all", "technical", "on_chain", "derivatives", "sentiment", "news", "macro"
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

1. **Strategy field**: ALWAYS use `decision.user_prompt` for strategy
   - Strategy should be markdown format with clear executable instructions

2. **Data sources**: Only suggest data sources that actually exist (use `query_available_data` if unsure)

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
   - `5m`, `15m`, `30m`, `1h`, `4h`, `1d`
   - Do NOT use `6h`, `2h`, `12h`, or `1w` — they are not supported by the scheduler

9. **Timeframes**: The bot supports per-indicator timeframe customization.
   - Global timeframes (the `timeframes` array) apply to all indicators by default
   - Individual indicators can override with `per_indicator_timeframes` (e.g., RSI on 5m/15m only, MACD on 4h/1d)
   - If you suggest per-indicator timeframes, add `per_indicator_timeframes` to the technical_analysis config
   - ALWAYS state explicitly when you're changing timeframes and why
   - Default is all 7 timeframes: 5m, 15m, 30m, 1h, 4h, 1d, 1w
   - Only reduce timeframes if the user asks or the strategy clearly benefits

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
                "enum": ["all", "technical", "on_chain", "derivatives", "sentiment", "news", "macro"],
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
                "description": "Configuration updates (partial or full). Will be deep merged with existing config. Use 'decision.user_prompt' for the trading strategy. Other sections: 'extraction', 'trading', 'llm_config'."
            }
        },
        "required": ["config_id", "updates"]
    }
}


async def get_available_data_points_from_db() -> Dict[str, Any]:
    """
    Query database for all enabled data sources and their data points.
    Returns structured data for prompt building.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        ds.name as source_name,
                        ds.display_name as source_display,
                        array_agg(dp.name ORDER BY dp.sort_order) as data_points,
                        array_agg(dp.display_name ORDER BY dp.sort_order) as display_names
                    FROM data_sources ds
                    JOIN data_points dp ON ds.source_id = dp.source_id
                    WHERE ds.enabled = true AND dp.enabled = true
                    GROUP BY ds.name, ds.display_name, ds.sort_order
                    ORDER BY ds.sort_order
                """)

                result = {}
                for row in cur.fetchall():
                    source_name, source_display, points, displays = row
                    result[source_name] = {
                        'display_name': source_display,
                        'data_points': points,
                        'display_names': displays
                    }
                return result
    except Exception as e:
        logger.error(f"Failed to fetch data points from database: {e}")
        # Return hardcoded fallback if DB query fails
        return {
            'technical_analysis': {
                'display_name': 'Technical Analysis',
                'data_points': ['RSI', 'MACD', 'BB', 'EMA', 'SMA', 'ATR', 'Stochastic', 'ADX', 'Aroon'],
                'display_names': ['RSI', 'MACD', 'Bollinger Bands', 'EMA', 'SMA', 'ATR', 'Stochastic', 'ADX', 'Aroon']
            }
        }


def build_data_points_prompt_section(available_data: Dict[str, Any]) -> str:
    """Build the data points section of the prompt dynamically."""
    sections = []

    for source_name, source_data in available_data.items():
        display_name = source_data['display_name']
        points = source_data['data_points']

        # Format based on category
        if source_name == 'technical_analysis':
            # Show count and list for technical indicators
            points_str = ', '.join(points)
            sections.append(f"**{display_name}** ({len(points)} indicators):\n{points_str}")
            sections.append("Available timeframes: 5m, 15m, 30m, 1h, 4h, 1d, 1w")
        else:
            # Non-technical categories - simpler format
            points_str = ', '.join(points)
            sections.append(f"**{display_name}**: {points_str}")

    return '\n\n'.join(sections)


async def query_available_data(category: str) -> Dict[str, Any]:
    """Return list of available data sources from database."""

    # Get fresh data from database
    available = await get_available_data_points_from_db()

    # Map database names to API category names
    category_mapping = {
        'technical_analysis': 'technical',
        'derivatives_leverage': 'derivatives',
        'macro_economics': 'macro',
        'sentiment_social': 'sentiment',
        'onchain_analytics': 'on_chain',
        'news_regulatory': 'news'
    }

    all_data = {}
    for source_name, source_data in available.items():
        key = category_mapping.get(source_name, source_name)
        all_data[key] = {
            "description": source_data['display_name'],
        }
        # Use 'indicators' for technical, 'sources' for others
        if source_name == 'technical_analysis':
            all_data[key]["indicators"] = source_data['data_points']
            all_data[key]["timeframes"] = ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        else:
            all_data[key]["sources"] = source_data['data_points']

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
    VALID_FREQUENCIES = {'5m', '15m', '30m', '1h', '4h', '1d'}
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
    AI assistant for scheduled trading bot configuration.

    Configures extraction, decision, trading, and llm_config sections.

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


class CreateConfigRequest(BaseModel):
    """Request model for one-shot config creation."""
    description: str
    symbol: str = "BTC/USDT"
    timeframe: str = "1h"


class CreateConfigResponse(BaseModel):
    """Response model for config creation."""
    success: bool
    user_prompt: str = ""
    extraction: Dict[str, Any] = {}
    error: str | None = None


STRATEGY_GENERATION_PROMPT = """You are the Strategy Generator for ggbots.ai. Your job is to convert a user's description of their trading philosophy into a concrete, executable trading strategy that the bot's decision engine will use.

## How ggbots Work

The bot follows a 3-step pipeline:
1. **Extraction**: Fetches market data based on selected indicators and timeframes
2. **Decision**: An LLM reads your strategy + the extracted data, then decides: LONG, SHORT, CLOSE, or HOLD
3. **Trading**: Executes the decision with position sizing and risk management

The strategy you generate goes into `decision.user_prompt` - this is what the LLM reads to make trading decisions.

## Available Data Sources

The bot can ONLY use these data sources (don't reference anything else):

**Technical Analysis (21 indicators)**
Use these EXACT internal names in extraction.selected_data_sources.technical_analysis.data_points:
- RSI, MACD, BB, EMA, SMA, ATR, Stochastic, CCI, Williams_R, MFI
- OBV, VWAP, ADX, Aroon, PSAR, KC, DC, BBW, ROC, Vortex, TRIX
- Available timeframes: 5m, 15m, 30m, 1h, 4h, 1d, 1w

**Market Intelligence**
- twitter_sentiment (social sentiment analysis)
- btc_funding_rate, eth_funding_rate (derivatives positioning)
- whale_activity (large holder movements)
- VIX (market fear gauge)
- DXY (dollar strength)

## Output Format

Generate ONLY the strategy text (no JSON, no code blocks around the whole thing). Use this structure:

# [Strategy Name]

**Timeframe**: [Primary timeframe]
**Style**: [1-line description]

---

## Identity

[2-3 sentences describing the bot's trading personality and philosophy. What does it believe about markets? When does it act?]

---

## How You Read the Data

**Primary indicators** (main signals):
[List the key indicators and what you look for]

**Secondary indicators** (confirmation):
[List confirmation indicators]

**Context/Filters**:
[Any trend filters, sentiment checks, etc.]

---

## Entry Conditions

**LONG when:**
- [Specific condition with indicator values, e.g., "RSI < 30"]
- [Additional conditions]

**SHORT when:**
- [Specific condition with indicator values, e.g., "RSI > 70"]
- [Additional conditions]

---

## Exit Conditions

**Take Profit:**
- [Specific targets based on structure or indicators]

**Stop Loss:**
- [Where to place stops and why]

---

## Confidence Thresholds

- **0.70+ confidence**: [Conditions for high confidence trades]
- **0.55-0.70 confidence**: [Conditions for medium confidence]
- **Below 0.55**: Pass - wait for better setup

---

## When You Pass

- [Conditions where you don't trade]
- [Market states to avoid]

## Guidelines

1. **ONLY reference available indicators** - Don't mention indicators that aren't in the list above
2. **Be specific with values** - "RSI below 30" not "RSI oversold"
3. **Include confidence levels** - The decision engine uses 0.0-1.0 confidence scores
4. **Match the personality** - Cautious bot = higher thresholds, aggressive = lower thresholds
5. **Add stop/take profit logic** - Every strategy needs exit rules
6. **Keep it readable** - The LLM needs to understand and execute this

## Personality Translations

- "Contrarian/fade the crowd" → Mean-reversion with RSI extremes, sentiment fading
- "Trend follower" → ADX/Aroon for trend, EMA alignment, momentum confirmation
- "Patient/sniper" → Multiple confirmations required, higher confidence thresholds
- "Aggressive/scalper" → Lower timeframes, quick entries, tight stops
- "Macro-aware" → Include VIX/DXY, longer timeframes, regime-based decisions
- "Multi-timeframe" → Use per_indicator_timeframes: RSI/Stochastic on lower TFs (5m, 15m), ADX/EMA on higher TFs (4h, 1d)

Generate the strategy now based on the user's description."""


CONFIG_CREATION_PROMPT_TEMPLATE = """You are the Config Creator for ggbots.ai. Your job is to convert a user's strategy description into a COMPLETE bot configuration including both the trading strategy AND the extraction config.

## How ggbots Work

The bot follows a 3-step pipeline:
1. **Extraction**: Fetches market data based on selected indicators and timeframes
2. **Decision**: An LLM reads your strategy + the extracted data, then decides: LONG, SHORT, CLOSE, or HOLD
3. **Trading**: Executes the decision with position sizing and risk management

You must create BOTH:
- `user_prompt`: The trading strategy (markdown format)
- `extraction`: The data sources config (JSON format)

## Available Data Sources

{data_points_section}

## CRITICAL: Use EXACT Names

The extraction config MUST use the exact internal names listed above. Examples:
- ✅ "RSI" not "Relative Strength Index"
- ✅ "BB" not "Bollinger Bands"
- ✅ "btc_funding_rate" not "BTC Funding Rate"
- ✅ "twitter_sentiment" not "Twitter Sentiment"

## Output Format

You MUST respond with valid JSON in this exact structure:

```json
{{
  "user_prompt": "# Strategy Name\\n\\n**Timeframe**: 1h\\n**Style**: Description\\n\\n---\\n\\n## Identity\\n\\n[Bot personality]\\n\\n---\\n\\n## How You Read the Data\\n\\n**Primary indicators**:\\n[Key indicators]\\n\\n**Secondary indicators**:\\n[Confirmation]\\n\\n---\\n\\n## Entry Conditions\\n\\n**LONG when:**\\n- [Conditions]\\n\\n**SHORT when:**\\n- [Conditions]\\n\\n---\\n\\n## Exit Conditions\\n\\n**Take Profit:**\\n- [Targets]\\n\\n**Stop Loss:**\\n- [Stops]\\n\\n---\\n\\n## Confidence Thresholds\\n\\n- **0.70+ confidence**: [High confidence]\\n- **0.55-0.70 confidence**: [Medium]\\n- **Below 0.55**: Pass\\n\\n---\\n\\n## When You Pass\\n\\n- [Conditions to avoid]",
  "extraction": {{
    "selected_data_sources": {{
      "technical_analysis": {{
        "data_points": ["RSI", "MACD", "ADX", "EMA", "ATR"],
        "timeframes": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"],
        "per_indicator_timeframes": {{
          "RSI": ["5m", "15m", "1h"],
          "MACD": ["4h", "1d"]
        }}
      }},
      "sentiment_social": {{
        "data_points": ["twitter_sentiment"],
        "timeframes": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
      }}
    }}
  }}
}}
```

## Guidelines

1. **Match extraction to strategy**: If your strategy mentions ADX, include ADX in extraction
2. **Use minimal indicators**: Only include what the strategy actually uses (5-12 technical indicators typical)
3. **Include relevant categories**: If strategy mentions sentiment/macro/funding, add those categories
4. **Be specific with values**: "RSI below 30" not "RSI oversold"
5. **Include confidence levels**: Decision engine uses 0.0-1.0 confidence scores
6. **Add stop/take profit logic**: Every strategy needs exit rules
7. **Always use all 7 timeframes**: Unless the user specifically requests fewer, always include: 5m, 15m, 30m, 1h, 4h, 1d, 1w. More timeframes = better analysis. Use `per_indicator_timeframes` when specific indicators benefit from targeted TFs (e.g., RSI on low TFs for entries, ADX on high TFs for trend)

## Personality Translations

- "Contrarian/fade the crowd" → RSI, Stochastic, BB extremes + twitter_sentiment
- "Trend follower" → ADX, Aroon, EMA alignment + MACD momentum
- "Patient/sniper" → Multiple confirmations, higher thresholds
- "Macro-aware" → vix, dxy + longer timeframes
- "Multi-timeframe" → per_indicator_timeframes: RSI/Stochastic on 5m/15m, ADX/EMA on 4h/1d
- "Funding-aware" → btc_funding_rate, eth_funding_rate

Create the complete config now. Respond ONLY with the JSON object, no other text."""


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
# Config Creation Endpoint (One-Shot with Extraction)
# ============================================================================

@router.post("/assistant/create-config", response_model=CreateConfigResponse)
async def create_bot_config(
    request: CreateConfigRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    One-shot config creation from user description.

    Returns complete config including:
    - user_prompt: Trading strategy (markdown)
    - extraction: Data sources config

    This endpoint dynamically queries the database for available data points
    and uses AI to generate both the strategy AND matching extraction config.
    """
    try:
        # Get available data points from database
        available_data = await get_available_data_points_from_db()

        # Build dynamic prompt section
        data_points_section = build_data_points_prompt_section(available_data)

        # Format the full prompt
        system_prompt = CONFIG_CREATION_PROMPT_TEMPLATE.format(
            data_points_section=data_points_section,
            timeframe=request.timeframe
        )

        # Build user message
        user_message = f"""Create a complete bot config for:

**Description**: {request.description}
**Symbol**: {request.symbol}
**Timeframe**: {request.timeframe}

Respond with the JSON config only."""

        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Call Claude Haiku
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )

        # Extract response text
        response_text = ""
        for content_block in response.content:
            if hasattr(content_block, "text"):
                response_text += content_block.text

        # Parse JSON response
        # Handle potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        config_data = json.loads(response_text.strip())

        # Validate required fields
        if "user_prompt" not in config_data:
            raise ValueError("Missing user_prompt in response")
        if "extraction" not in config_data:
            raise ValueError("Missing extraction in response")

        # Get indicator count for logging
        indicators_count = len(
            config_data.get('extraction', {})
            .get('selected_data_sources', {})
            .get('technical_analysis', {})
            .get('data_points', [])
        )

        logger.bind(
            user_id=current_user.user_id,
            symbol=request.symbol,
            timeframe=request.timeframe,
            indicators_count=indicators_count
        ).info("Created bot config from description")

        return CreateConfigResponse(
            success=True,
            user_prompt=config_data["user_prompt"],
            extraction=config_data["extraction"]
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse config JSON: {e}")
        return CreateConfigResponse(
            success=False,
            error=f"Failed to parse AI response as JSON: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Config creation error: {e}")
        return CreateConfigResponse(
            success=False,
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
