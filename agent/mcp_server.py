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
from core.common.activity_logger import log_activity_safe, ACTIVITY_PRIORITY


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
    """Query market data across 7 categories:

CATEGORIES (use exact names):
- technical_analysis: RSI, MACD, Stochastic, Williams_R, CCI, MFI, ADX, PSAR, Aroon, ATR, BB, OBV, SMA, EMA, ROC, VWAP, TRIX, Vortex, BBWidth, Keltner, Donchian
- macro_economics: vix, dxy, cpi, nfp
- sentiment_social: twitter_sentiment (exact name "twitter_sentiment")
- derivatives_leverage: btc_funding_rate, eth_funding_rate
- on_chain_analytics: btc_tvl, whale_activity
- news_regulatory: crypto_news
- trading_signals: ggshot (PREMIUM, exact name "ggshot")

TIMEFRAMES (for technical_analysis):
Technical indicators support 7 timeframes: "5m", "15m", "30m", "1h", "4h", "1d", "1w"
Default: "1h". Other categories use latest available data regardless of timeframe.

EXAMPLES:
{"symbol": "BTC", "categories": {"technical_analysis": ["RSI"]}}
{"symbol": "BTC", "categories": {"technical_analysis": ["RSI", "MACD"]}, "timeframe": "15m"}
{"symbol": "ETH", "categories": {"technical_analysis": ["Stochastic"], "sentiment_social": ["twitter_sentiment"]}, "timeframe": "4h"}

Symbol formats: "BTC", "BTCUSDT", "BTC/USDT" all work. Indicators are case-insensitive.
Params: symbol (required), categories (dict), timeframe (optional, default '1h')""",
    {"symbol": str, "categories": dict, "timeframe": str}
)
async def query_market_data(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Query market data with category-based structure.

    The tool is forgiving with inputs:
    - Symbol: "BTC", "BTCUSDT", or "BTC/USDT" all work
    - Indicators: "rsi", "RSI", "Rsi" all work (case-insensitive)
    - Data point names: Use exact names shown below

    Categories:
    - technical_analysis: RSI, MACD, Stochastic, Williams_R, CCI, MFI, ADX, PSAR, Aroon, ATR, BB, OBV, SMA, EMA, ROC, VWAP, TRIX, Vortex, BBWidth, Keltner, Donchian
    - macro_economics: vix, dxy, cpi, nfp
    - sentiment_social: twitter_sentiment (use exact name "twitter_sentiment", NOT "twitter" or "sentiment")
    - derivatives_leverage: btc_funding_rate, eth_funding_rate
    - on_chain_analytics: btc_tvl, whale_activity
    - news_regulatory: crypto_news
    - trading_signals: ggshot (PREMIUM - use exact name "ggshot", NOT "ggshot_signals")

    Examples:
        # Simple query - symbol formats are flexible
        query_market_data({
            "symbol": "BTC",  # or "BTCUSDT" or "BTC/USDT"
            "categories": {"technical_analysis": ["RSI"]}  # case-insensitive
        })

        # Multiple data sources
        query_market_data({
            "symbol": "BTC",
            "categories": {
                "technical_analysis": ["RSI", "MACD"],
                "trading_signals": ["ggshot"],
                "sentiment_social": ["twitter_sentiment"]
            }
        })

    Note: Use exact data point names (ggshot, twitter_sentiment, btc_funding_rate)
    """
    try:
        # LOG: Raw arguments from agent
        logger.debug(f"🔧 query_market_data CALLED")
        logger.debug(f"   Args received: {json.dumps(args, indent=2)}")

        symbol = args["symbol"]
        categories_raw = args.get("categories", {})
        timeframe = args.get("timeframe", "1h")

        # Handle JSON string if SDK serializes the dict
        if isinstance(categories_raw, str):
            categories = json.loads(categories_raw)
        else:
            categories = categories_raw

        # Validate category names
        VALID_CATEGORIES = {
            "technical_analysis", "macro_economics", "sentiment_social",
            "derivatives_leverage", "on_chain_analytics", "news_regulatory", "trading_signals"
        }

        unknown_categories = set(categories.keys()) - VALID_CATEGORIES
        if unknown_categories:
            error_msg = f"❌ Unknown categories: {', '.join(unknown_categories)}\n\nValid categories:\n"
            for cat in sorted(VALID_CATEGORIES):
                error_msg += f"  - {cat}\n"

            logger.warning(f"Agent used invalid categories: {unknown_categories}")
            return {
                "content": [{
                    "type": "text",
                    "text": error_msg
                }]
            }

        # Separate technical indicators from intelligence sources
        technical_indicators = categories.get("technical_analysis", [])
        intelligence_sources = {k: v for k, v in categories.items() if k != "technical_analysis"}

        # LOG: Parsed structure
        logger.debug(f"   Parsed technical_indicators: {technical_indicators}")
        logger.debug(f"   Parsed intelligence_sources: {intelligence_sources}")

        # Call API with proper structure
        logger.debug(f"   Calling API with symbol={symbol}, indicators={technical_indicators}, data_sources={intelligence_sources}, timeframe={timeframe}")
        result = await agent_context.api_client.query_market_data(
            config_id=agent_context.config_id,
            symbol=symbol,
            indicators=technical_indicators if technical_indicators else None,
            data_sources=intelligence_sources if intelligence_sources else None,
            timeframe=timeframe
        )

        # Format response for agent
        response_parts = []

        if result.get('data', {}).get('technicals'):
            tech_data = result['data']['technicals']
            response_parts.append(f"📊 Technical Indicators ({timeframe}):")
            response_parts.append(json.dumps(tech_data, indent=2))

        if result.get('data', {}).get('market_intelligence'):
            intel_data = result['data']['market_intelligence']
            response_parts.append(f"\n🌐 Market Intelligence:")
            response_parts.append(json.dumps(intel_data, indent=2))

        formatted_response = "\n".join(response_parts) if response_parts else "No data available"

        # LOG: Response being returned to agent
        logger.debug(f"   Response: {formatted_response[:500]}{'...' if len(formatted_response) > 500 else ''}")

        # Auto-log activity to timeline
        categories_list = list(categories.keys())
        log_activity_safe(
            config_id=agent_context.config_id,
            user_id=agent_context.user_id,
            activity_type='market_query',
            activity_source='agent_tool',
            summary=f"Queried {symbol}: {', '.join(categories_list)}",
            details={
                'symbol': symbol,
                'categories': categories,
                'timeframe': timeframe,
                'data_returned': bool(response_parts)
            },
            related_symbol=symbol,
            importance=6
        )

        return {
            "content": [{
                "type": "text",
                "text": f"Market Data for {symbol}:\n\n{formatted_response}"
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
# TOOL 1B: GET CURRENT PRICE (Lightweight price check)
# ============================================================================

@tool(
    "get_current_price",
    "Get current price for a symbol (FAST - uses WebSocket cache, sub-millisecond). Use this before executing trades to check the current market price. Params: symbol (required)",
    {"symbol": str}
)
async def get_current_price(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get current price without indicators.

    Lightweight tool for quick price checks before trading.
    Uses WebSocket cache for 100 symbols (sub-ms response), falls back to REST API.
    Returns current price, bid/ask spread, and data source.
    """
    try:
        # LOG: Tool called
        logger.debug(f"🔧 get_current_price CALLED with args: {args}")

        symbol = args["symbol"]

        result = await agent_context.api_client.get_current_price(symbol=symbol)

        if result.get("status") == "success":
            price = result.get("current_price", 0)
            bid = result.get("bid", 0)
            ask = result.get("ask", 0)
            spread = result.get("spread_percent", 0)
            source = result.get("source", "unknown")

            source_emoji = "⚡" if source == "websocket_cache" else "🌐"

            return {
                "content": [{
                    "type": "text",
                    "text": f"💰 Current Price for {symbol} {source_emoji}\n\n"
                            f"Mid Price: ${price:,.2f}\n"
                            f"Bid: ${bid:,.2f}\n"
                            f"Ask: ${ask:,.2f}\n"
                            f"Spread: {spread:.3f}%\n"
                            f"Source: {source.replace('_', ' ').title()}"
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": f"⚠️ Could not fetch price for {symbol}"
                }]
            }

    except Exception as e:
        logger.error(f"get_current_price failed: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to get current price: {str(e)}"
            }]
        }


# ============================================================================
# TOOL 2: EXECUTE TRADE
# ============================================================================

@tool(
    "execute_trade",
    "Execute a trade with REQUIRED stop loss and take profit. Params: symbol, side (long/short), stop_loss_price, take_profit_price (all required). Optional: confidence (0-1), size_usd (total position size in USD, NOT margin - e.g., 1000 with 10x leverage means $1000 position using $100 margin), leverage (1-20x multiplier)",
    {"symbol": str, "side": str, "confidence": float, "size_usd": float, "leverage": int, "stop_loss_price": float, "take_profit_price": float}
)
async def execute_trade(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute trade with optional position sizing overrides.

    Agents can control position size and leverage:
    - size_usd: Total position size in USD (NOTIONAL, not margin/collateral)
      Example: size_usd=1000 with leverage=10 means $1000 position using $100 margin
      Example: size_usd=500 with leverage=5 means $500 position using $100 margin
    - leverage: Leverage multiplier (e.g., 10 = 10x leverage)
      Actual capital at risk = size_usd / leverage

    If not specified, uses bot config defaults for position sizing.

    IMPORTANT: size_usd is the FULL POSITION SIZE, not the margin.
    To calculate margin: margin = size_usd / leverage
    """
    try:
        symbol = args["symbol"]
        side = args["side"]
        confidence = args.get("confidence", 0.7)
        stop_loss_price = args["stop_loss_price"]
        take_profit_price = args["take_profit_price"]

        # Extract position sizing overrides (optional)
        size_usd = args.get("size_usd")
        leverage = args.get("leverage")

        result = await agent_context.api_client.execute_trade(
            config_id=agent_context.config_id,
            symbol=symbol,
            side=side,
            confidence=confidence,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            size_usd=size_usd,
            leverage=leverage
        )

        if result.get("status") == "success":
            trade = result.get("trade", {})

            # Auto-log activity to timeline
            activity_type = f"trade_entry_{side}" if side in ['long', 'short'] else 'trade_entry_long'
            log_activity_safe(
                config_id=agent_context.config_id,
                user_id=agent_context.user_id,
                activity_type=activity_type,
                activity_source='agent_tool',
                summary=f"Opened {side} {symbol} at ${trade.get('entry_price', 'N/A')}",
                details={
                    'symbol': symbol,
                    'side': side,
                    'entry_price': trade.get('entry_price'),
                    'size_usd': trade.get('size_usd'),
                    'leverage': leverage,
                    'stop_loss_price': stop_loss_price,
                    'take_profit_price': take_profit_price,
                    'confidence': confidence
                },
                trade_id=trade.get('trade_id'),
                trade_type='paper',  # TODO: Detect paper/live/aster from config
                related_symbol=symbol,
                importance=9
            )

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
            symbol = trade.get('symbol', 'N/A')

            # Auto-log activity to timeline (trade_win or trade_loss based on P&L)
            activity_type = 'trade_win' if pnl >= 0 else 'trade_loss'
            log_activity_safe(
                config_id=agent_context.config_id,
                user_id=agent_context.user_id,
                activity_type=activity_type,
                activity_source='agent_tool',
                summary=f"Closed {symbol}: {'+' if pnl > 0 else ''}{pnl:.2f} ({pnl_pct:.1f}%)",
                details={
                    'symbol': symbol,
                    'side': trade.get('side'),
                    'exit_price': trade.get('exit_price'),
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'duration_minutes': trade.get('duration_minutes'),
                    'close_reason': reasoning
                },
                trade_id=trade_id,
                trade_type='paper',  # TODO: Detect paper/live/aster from config
                related_symbol=symbol,
                importance=9
            )

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
            old_version = strategy.get("old_version", version - 1 if isinstance(version, int) else "unknown")

            # Auto-log activity to timeline
            log_activity_safe(
                config_id=agent_context.config_id,
                user_id=agent_context.user_id,
                activity_type='strategy_updated',
                activity_source='agent_tool',
                summary=f"Updated strategy: v{old_version} → v{version}",
                details={
                    'old_version': old_version,
                    'new_version': version,
                    'reason': reason,
                    'new_strategy_content': new_strategy
                },
                importance=10
            )

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

        # Auto-log activity to timeline BEFORE sleeping
        log_activity_safe(
            config_id=agent_context.config_id,
            user_id=agent_context.user_id,
            activity_type='agent_wait',
            activity_source='agent_tool',
            summary=f"Waiting {duration_minutes} minutes: {reason[:50]}",
            details={
                'duration_minutes': duration_minutes,
                'reason': reason,
                'next_check_at': next_check.isoformat()
            },
            importance=4
        )

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

        # Handle JSON string if SDK serializes the dict
        predictive_data_points_raw = args.get("predictive_data_points")
        if isinstance(predictive_data_points_raw, str):
            try:
                # Try to parse as JSON first
                predictive_data_points = json.loads(predictive_data_points_raw)
            except json.JSONDecodeError:
                # If not JSON, treat as plain text string (agent wrote freeform description)
                predictive_data_points = {"notes": predictive_data_points_raw}
        else:
            predictive_data_points = predictive_data_points_raw

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
            # Auto-log activity to timeline
            log_activity_safe(
                config_id=agent_context.config_id,
                user_id=agent_context.user_id,
                activity_type='observation_recorded',
                activity_source='agent_tool',
                summary=f"Recorded {observation_type} for trade",
                details={
                    'observation_type': observation_type,
                    'what_went_well': what_went_well,
                    'what_went_wrong': what_went_wrong,
                    'predictive_data_points': predictive_data_points,
                    'decision_review': decision_review
                },
                trade_id=trade_id,
                importance=importance
            )

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
    "save_strategy_and_exit",
    "Save the trading strategy to database and exit strategy definition mode. Call this when strategy is finalized. Params: strategy_summary (required), autonomously_editable (optional, default false)",
    {"strategy_summary": str, "autonomously_editable": bool}
)
async def save_strategy_and_exit(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save strategy and signal run_agent.py to exit.
    No confirmation needed - agent decides when strategy is ready.
    """
    try:
        strategy_summary = args["strategy_summary"]
        autonomously_editable = args.get("autonomously_editable", False)
        config_id = agent_context.config_id
        user_id = agent_context.user_id

        # Save strategy to database directly
        from core.common.db import get_db_connection
        import json

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get current config_data
                cur.execute(
                    "SELECT config_data FROM configurations WHERE config_id = %s",
                    (config_id,)
                )
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Config {config_id} not found")

                config_data = row[0]

                # Add agent_strategy
                config_data["agent_strategy"] = {
                    "content": strategy_summary,
                    "autonomously_editable": autonomously_editable,
                    "version": 1,
                    "last_updated_at": datetime.utcnow().isoformat(),
                    "last_updated_by": "user",
                    "performance_log": []
                }

                # Update database
                cur.execute(
                    "UPDATE configurations SET config_data = %s, updated_at = NOW() WHERE config_id = %s",
                    (json.dumps(config_data), config_id)
                )
                conn.commit()

        # Set exit flag for run_agent.py to detect
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = await redis.from_url(redis_url)
        await redis_client.set(f"agent:{config_id}:strategy_saved_exit", "true")

        # Also stop PM2 process to prevent auto-restart
        import subprocess
        agent_name = f"agent-{config_id}"
        try:
            subprocess.run(['pm2', 'delete', agent_name], check=False)  # Don't fail if not running
            logger.info(f"PM2 process {agent_name} deleted")
        except Exception as e:
            logger.warning(f"Could not delete PM2 process: {e}")

        await redis_client.aclose()

        logger.info(f"Strategy saved for config {config_id}, autonomously_editable={autonomously_editable}")

        return {
            "content": [{
                "type": "text",
                "text": f"✅ Strategy saved! Shutting down strategy definition mode.\n\nTo start autonomous trading, click 'Activate Agent' in the UI."
            }]
        }

    except Exception as e:
        logger.error(f"save_strategy_and_exit failed: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to save strategy: {str(e)}"
            }]
        }


# ============================================================================
# MCP SERVER CREATION
# ============================================================================

def create_mcp_server():
    """
    Create MCP server with 12 tools for autonomous trading agent.

    Returns:
        MCP server instance to be used with Claude Agent SDK
    """
    logger.info("Creating MCP server with 12 trading tools")

    # LOG: All tool definitions
    logger.debug("📚 MCP TOOLS BEING REGISTERED:")
    logger.debug("   1. query_market_data - Query market data across 7 categories")
    logger.debug("   2. get_current_price - Get current price for a symbol")
    logger.debug("   3. execute_trade - Execute a trade")
    logger.debug("   4. get_positions - Get open trading positions")
    logger.debug("   5. get_account_status - Get account balance and statistics")
    logger.debug("   6. close_position - Close an open position")
    logger.debug("   7. update_strategy - Update trading strategy")
    logger.debug("   8. wait_for - Pause execution")
    logger.debug("   9. record_trade_observation - Record trade learnings")
    logger.debug("   10. query_trade_observations - Query past observations")
    logger.debug("   11. log_activity - Log agent reasoning/analysis to timeline")
    logger.debug("   12. save_strategy_and_exit - Save strategy and exit")

    # Create server with all tools
    server = create_sdk_mcp_server(
        name="ggbot-trading-agent",
        version="1.0.0",
        tools=[
            query_market_data,
            get_current_price,
            execute_trade,
            get_positions,
            get_account_status,
            close_position,
            update_strategy,
            wait_for,
            record_trade_observation,
            query_trade_observations,
            save_strategy_and_exit
        ]
    )

    logger.info("MCP server created successfully with 11 tools")
    return server


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "create_mcp_server",
    "set_agent_context",
    "agent_context"
]
