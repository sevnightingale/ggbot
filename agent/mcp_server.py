"""
Agent MCP Server

Defines 10 MCP tools for autonomous trading agent using Claude Agent SDK.
Tools provide market data queries, trade execution, account management,
trade observation learning, and mode switching.

Architecture:
- Module-level state (AgentContext) for single-agent Phase 2 testing
- Will refactor to closure pattern for multi-agent Phase 4 production
- Tools return helpful error messages (not exceptions)
"""

import os
import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import redis.asyncio as redis

# Claude Agent SDK imports
from claude_agent_sdk import tool, create_sdk_mcp_server

# Local imports (HTTP client, not direct ggbot imports)
from agent.service_client import GGBotAPIClient


# ============================================================================
# MODULE-LEVEL STATE (Single Agent Context)
# ============================================================================

class AgentContext:
    """
    Module-level state for tools to access agent context.

    Phase 2 (single agent): Simple module-level state
    Phase 4 (multi-agent): Refactor to closure pattern (each agent gets own tool instances)
    """
    config_id: Optional[str] = None
    user_id: Optional[str] = None
    api_client: Optional[GGBotAPIClient] = None


agent_context = AgentContext()


def set_agent_context(config_id: str, user_id: str, api_client: GGBotAPIClient):
    """Initialize agent context (called by runner before agent starts)"""
    agent_context.config_id = config_id
    agent_context.user_id = user_id
    agent_context.api_client = api_client
    logger.info(f"Agent context set: config_id={config_id}, user_id={user_id}")


# ============================================================================
# TOOL 1: QUERY MARKET DATA
# ============================================================================

@tool(
    "query_market_data",
    "Get market data for trading decisions. Params: symbol (required), data_point_names (optional list), timeframe (optional, default '1h')",
    {"symbol": str, "data_point_names": list, "timeframe": str}
)
async def query_market_data(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Query market data with optional dynamic overrides.

    NOTE: Currently passes data_point_names as 'indicators' to API.
    Future: Will map data points to proper categories (technical vs intelligence sources).
    """
    try:
        symbol = args["symbol"]
        data_point_names = args.get("data_point_names")
        timeframe = args.get("timeframe", "1h")

        # TODO: Map data_point_names to indicators vs. data_sources categories
        # For now, treat all as indicators (works for technical indicators)
        result = await agent_context.api_client.query_market_data(
            config_id=agent_context.config_id,
            symbol=symbol,
            indicators=data_point_names,
            timeframe=timeframe
        )

        return {
            "content": [{
                "type": "text",
                "text": f"Market Data for {symbol} ({timeframe}):\n\n{json.dumps(result['data'], indent=2)}"
            }]
        }

    except Exception as e:
        logger.error(f"query_market_data failed: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to query market data: {str(e)}"
            }]
        }


# ============================================================================
# TOOL 2: EXECUTE TRADE
# ============================================================================

@tool(
    "execute_trade",
    "Execute a trade with REQUIRED stop loss and take profit. Params: symbol, side (long/short), stop_loss_price, take_profit_price (all required). Optional: confidence (0-1), size_usd, leverage",
    {"symbol": str, "side": str, "confidence": float, "size_usd": float, "leverage": int, "stop_loss_price": float, "take_profit_price": float}
)
async def execute_trade(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute trade with optional position sizing overrides.

    NOTE: size_usd and leverage overrides not yet implemented in paper trading service.
    Currently uses config defaults for position sizing.
    """
    try:
        symbol = args["symbol"]
        side = args["side"]
        confidence = args.get("confidence", 0.7)
        stop_loss_price = args["stop_loss_price"]
        take_profit_price = args["take_profit_price"]

        # TODO: Add size_usd and leverage to API call once paper service supports overrides

        result = await agent_context.api_client.execute_trade(
            config_id=agent_context.config_id,
            symbol=symbol,
            side=side,
            confidence=confidence,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price
        )

        if result.get("status") == "success":
            trade = result.get("trade", {})
            return {
                "content": [{
                    "type": "text",
                    "text": f"✅ Trade executed successfully!\n\n"
                            f"Symbol: {symbol}\n"
                            f"Side: {side}\n"
                            f"Entry Price: ${trade.get('entry_price', 'N/A')}\n"
                            f"Size: ${trade.get('size_usd', 'N/A')}\n"
                            f"Stop Loss: ${stop_loss_price}\n"
                            f"Take Profit: ${take_profit_price}\n"
                            f"Trade ID: {trade.get('trade_id', 'N/A')}"
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": f"⚠️ Trade execution issue: {result.get('message', 'Unknown error')}"
                }]
            }

    except Exception as e:
        logger.error(f"execute_trade failed: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to execute trade: {str(e)}"
            }]
        }


# ============================================================================
# TOOL 3: GET POSITIONS
# ============================================================================

@tool(
    "get_positions",
    "Get all open trading positions (paper and live). No parameters required.",
    {}
)
async def get_positions(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve all open positions for the current config.
    Returns all fields from paper_trades table.
    """
    try:
        result = await agent_context.api_client.get_positions(
            config_id=agent_context.config_id
        )

        positions = result.get("positions", [])

        if not positions:
            return {
                "content": [{
                    "type": "text",
                    "text": "No open positions"
                }]
            }

        # Format positions nicely
        positions_text = f"Open Positions ({len(positions)}):\n\n"
        for pos in positions:
            pnl = pos.get("unrealized_pnl", 0)
            pnl_pct = pos.get("unrealized_pnl_percent", 0)
            positions_text += f"• {pos['symbol']} {pos['side'].upper()}\n"
            positions_text += f"  Entry: ${pos['entry_price']:.2f} | Current: ${pos.get('current_price', 0):.2f}\n"
            positions_text += f"  Size: ${pos.get('size_usd', 0):.2f} | Leverage: {pos.get('leverage', 1)}x\n"
            positions_text += f"  P&L: ${pnl:.2f} ({pnl_pct:.2f}%)\n"
            positions_text += f"  Trade ID: {pos['trade_id']}\n\n"

        return {
            "content": [{
                "type": "text",
                "text": positions_text
            }]
        }

    except Exception as e:
        logger.error(f"get_positions failed: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to get positions: {str(e)}"
            }]
        }


# ============================================================================
# TOOL 4: GET ACCOUNT STATUS
# ============================================================================

@tool(
    "get_account_status",
    "Get paper account balance and trading performance metrics. No parameters required.",
    {}
)
async def get_account_status(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get account status with performance metrics.

    NOTE: Currently paper trading only. Live trading account status coming soon.
    """
    try:
        result = await agent_context.api_client.get_account_status(
            config_id=agent_context.config_id
        )

        account = result.get("account", {})
        metrics = result.get("metrics", {})

        balance = account.get("current_balance", 0)
        total_pnl = account.get("total_pnl", 0)
        total_trades = metrics.get("total_trades", 0)
        win_rate = metrics.get("win_rate", 0)

        account_text = f"""
📊 Account Status (Paper Trading)

Balance: ${balance:,.2f}
Total P&L: ${total_pnl:,.2f}
Total Trades: {total_trades}
Win Rate: {win_rate:.1%}

Open Positions: {metrics.get('open_positions', 0)}
        """.strip()

        return {
            "content": [{
                "type": "text",
                "text": account_text
            }]
        }

    except Exception as e:
        logger.error(f"get_account_status failed: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to get account status: {str(e)}"
            }]
        }


# ============================================================================
# TOOL 5: CLOSE POSITION
# ============================================================================

@tool(
    "close_position",
    "Close an open trading position. Params: trade_id (required), reasoning (required)",
    {"trade_id": str, "reasoning": str}
)
async def close_position(args: Dict[str, Any]) -> Dict[str, Any]:
    """Close a specific position"""
    try:
        trade_id = args["trade_id"]
        reasoning = args["reasoning"]

        result = await agent_context.api_client.close_position(
            config_id=agent_context.config_id,
            trade_id=trade_id
        )

        if result.get("status") == "success":
            trade = result.get("trade", {})
            pnl = trade.get("realized_pnl", 0)
            pnl_pct = trade.get("realized_pnl_percent", 0)

            return {
                "content": [{
                    "type": "text",
                    "text": f"✅ Position closed successfully!\n\n"
                            f"Symbol: {trade.get('symbol', 'N/A')}\n"
                            f"Side: {trade.get('side', 'N/A')}\n"
                            f"P&L: ${pnl:.2f} ({pnl_pct:.2f}%)\n"
                            f"Reason: {reasoning}\n\n"
                            f"Consider recording a trade observation to reflect on this trade."
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": f"⚠️ Failed to close position: {result.get('message', 'Unknown error')}"
                }]
            }

    except Exception as e:
        logger.error(f"close_position failed: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to close position: {str(e)}"
            }]
        }


# ============================================================================
# TOOL 6: UPDATE STRATEGY
# ============================================================================

@tool(
    "update_strategy",
    "Update your trading strategy (requires autonomously_editable=true in config). Params: new_strategy, reason, performance_summary (all required)",
    {"new_strategy": str, "reason": str, "performance_summary": str}
)
async def update_strategy(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update agent's strategy (experimental mode only).

    NOTE: Requires autonomously_editable flag in config's agent_strategy section.
    """
    try:
        new_strategy = args["new_strategy"]
        reason = args["reason"]

        result = await agent_context.api_client.update_strategy(
            config_id=agent_context.config_id,
            strategy_content=new_strategy,
            updated_by="agent"
        )

        if result.get("status") == "success":
            strategy = result.get("strategy", {})
            version = strategy.get("version", "unknown")

            return {
                "content": [{
                    "type": "text",
                    "text": f"✅ Strategy updated to version {version}\n\n"
                            f"Reason: {reason}\n\n"
                            f"New strategy is now active."
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": f"⚠️ {result.get('message', 'Strategy is not autonomously editable')}"
                }]
            }

    except Exception as e:
        logger.error(f"update_strategy failed: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to update strategy: {str(e)}"
            }]
        }


# ============================================================================
# TOOL 7: WAIT FOR
# ============================================================================

@tool(
    "wait_for",
    "Sleep for a specified duration (max 24 hours). Params: duration_minutes (required, max 1440), reason (optional)",
    {"duration_minutes": int, "reason": str}
)
async def wait_for(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent controls its own timing.

    Future Enhancement: Wake-up triggers (price alerts, volume spikes, news breaks)
    """
    try:
        duration_minutes = min(args["duration_minutes"], 1440)  # Cap at 24 hours
        reason = args.get("reason", "No reason provided")

        next_check = datetime.utcnow() + timedelta(minutes=duration_minutes)

        logger.info(f"Agent waiting {duration_minutes}m: {reason}")

        await asyncio.sleep(duration_minutes * 60)

        return {
            "content": [{
                "type": "text",
                "text": f"⏳ Waited {duration_minutes} minutes.\n"
                        f"Next check: {next_check.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                        f"Reason: {reason}"
            }]
        }

    except Exception as e:
        logger.error(f"wait_for failed: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Wait failed: {str(e)}"
            }]
        }


# ============================================================================
# TOOL 8: RECORD TRADE OBSERVATION
# ============================================================================

@tool(
    "record_trade_observation",
    "Record post-trade reflection after closing a position. Params: trade_id, observation_type (win_analysis/loss_analysis) required. Optional: what_went_well, what_went_wrong, predictive_data_points (dict), decision_review, importance (1-10)",
    {"trade_id": str, "observation_type": str, "what_went_well": str, "what_went_wrong": str, "predictive_data_points": dict, "decision_review": str, "importance": int}
)
async def record_trade_observation(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Post-trade reflection for structured learning.

    Agent reflects immediately after closing position, when context is fresh.
    User + agent can review observations together to refine strategy.
    """
    try:
        trade_id = args["trade_id"]
        observation_type = args["observation_type"]
        what_went_well = args.get("what_went_well")
        what_went_wrong = args.get("what_went_wrong")
        predictive_data_points = args.get("predictive_data_points")
        decision_review = args.get("decision_review")
        importance = args.get("importance", 5)

        result = await agent_context.api_client.record_trade_observation(
            config_id=agent_context.config_id,
            trade_id=trade_id,
            observation_type=observation_type,
            what_went_well=what_went_well,
            what_went_wrong=what_went_wrong,
            predictive_data_points=predictive_data_points,
            decision_review=decision_review,
            importance=importance
        )

        if result.get("status") == "success":
            return {
                "content": [{
                    "type": "text",
                    "text": f"✅ Trade observation recorded (importance: {importance}/10)\n\n"
                            f"Type: {observation_type}\n"
                            f"Trade ID: {trade_id}\n\n"
                            f"This learning is now queryable for future reference."
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": f"⚠️ Failed to record observation: {result.get('message', 'Unknown error')}"
                }]
            }

    except Exception as e:
        logger.error(f"record_trade_observation failed: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to record observation: {str(e)}"
            }]
        }


# ============================================================================
# TOOL 9: QUERY TRADE OBSERVATIONS
# ============================================================================

@tool(
    "query_trade_observations",
    "Search past trade observations for learning and strategy refinement. All params optional: symbol, observation_type (win_analysis/loss_analysis), min_importance, limit (default 10)",
    {"symbol": str, "observation_type": str, "min_importance": int, "limit": int}
)
async def query_trade_observations(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Query trade observations for learning.

    Use Cases:
    - User asks: "What have we learned about BTC trades?"
    - Agent reviews: Before entering similar trade, check past observations
    - Strategy refinement: User + agent discuss patterns, improve together

    Design Note: Observations are queryable, NOT auto-injected after compaction.
    """
    try:
        symbol = args.get("symbol")
        observation_type = args.get("observation_type")
        min_importance = args.get("min_importance")
        limit = args.get("limit", 10)

        result = await agent_context.api_client.query_trade_observations(
            config_id=agent_context.config_id,
            symbol=symbol,
            observation_type=observation_type,
            min_importance=min_importance,
            limit=limit
        )

        observations = result.get("observations", [])

        if not observations:
            return {
                "content": [{
                    "type": "text",
                    "text": "No trade observations found matching the criteria."
                }]
            }

        # Format observations nicely
        obs_text = f"Trade Observations ({len(observations)}):\n\n"
        for obs in observations:
            obs_text += f"• {obs['symbol']} {obs['side'].upper()} ({obs['observation_type']})\n"
            obs_text += f"  P&L: ${obs.get('trade_pnl', 0):.2f}\n"
            obs_text += f"  Importance: {obs['importance']}/10\n"

            if obs.get('what_went_well'):
                obs_text += f"  ✅ Went well: {obs['what_went_well']}\n"
            if obs.get('what_went_wrong'):
                obs_text += f"  ❌ Went wrong: {obs['what_went_wrong']}\n"
            if obs.get('predictive_data_points'):
                obs_text += f"  📊 Key data points: {json.dumps(obs['predictive_data_points'])}\n"
            if obs.get('decision_review'):
                obs_text += f"  🔍 Decision review: {obs['decision_review']}\n"

            obs_text += f"  📅 {obs['created_at']}\n\n"

        return {
            "content": [{
                "type": "text",
                "text": obs_text
            }]
        }

    except Exception as e:
        logger.error(f"query_trade_observations failed: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to query observations: {str(e)}"
            }]
        }


# ============================================================================
# TOOL 10: REQUEST AUTONOMOUS MODE
# ============================================================================

@tool(
    "request_autonomous_mode",
    "Request permission to switch to autonomous trading mode. Params: strategy_summary (required)",
    {"strategy_summary": str}
)
async def request_autonomous_mode(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Request mode switch from strategy_definition to autonomous.

    Agent calls this when strategy is complete and ready for execution.
    Sets Redis flag that run_agent.py will detect and wait for user confirmation.
    """
    try:
        strategy_summary = args["strategy_summary"]
        config_id = agent_context.config_id

        # Connect to Redis and set pending flag
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = await redis.from_url(redis_url)

        await redis_client.set(f"agent:{config_id}:mode_switch_pending", "true")
        await redis_client.aclose()

        logger.info(f"Mode switch requested for config {config_id}")

        return {
            "content": [{
                "type": "text",
                "text": f"""
📋 Strategy Ready for Autonomous Trading

{strategy_summary}

⚠️ I'm ready to start trading autonomously with this strategy.

Reply with:
1 - CONFIRM and start autonomous trading
2 - REVISE strategy

Waiting for your confirmation...
                """
            }]
        }

    except Exception as e:
        logger.error(f"request_autonomous_mode failed: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to request mode switch: {str(e)}"
            }]
        }


# ============================================================================
# MCP SERVER CREATION
# ============================================================================

def create_mcp_server():
    """
    Create MCP server with 10 tools for autonomous trading agent.

    Returns:
        MCP server instance to be used with Claude Agent SDK
    """
    logger.info("Creating MCP server with 10 trading tools")

    # Create server with all tools
    server = create_sdk_mcp_server(
        name="ggbot-trading-agent",
        version="1.0.0",
        tools=[
            query_market_data,
            execute_trade,
            get_positions,
            get_account_status,
            close_position,
            update_strategy,
            wait_for,
            record_trade_observation,
            query_trade_observations,
            request_autonomous_mode
        ]
    )

    logger.info("MCP server created successfully with 10 tools")
    return server


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "create_mcp_server",
    "set_agent_context",
    "agent_context"
]
