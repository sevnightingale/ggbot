"""
Agent MCP Server

Defines 12 MCP tools for autonomous trading agent using Claude Agent SDK.
Tools provide market data queries, trade execution, account management,
order management, trade observation learning, and mode switching.

Architecture:
- Module-level state (AgentContext) for single-agent Phase 2 testing
- Will refactor to closure pattern for multi-agent Phase 4 production
- Tools return helpful error messages (not exceptions)
"""

import os
import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone
from loguru import logger
import redis.asyncio as redis

# Claude Agent SDK imports
from claude_agent_sdk import tool, create_sdk_mcp_server

# Local imports (HTTP client, not direct ggbot imports)
from agent.service_client import GGBotAPIClient
from core.common.activity_logger import log_activity_safe


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
    trading_mode: Optional[str] = None  # 'paper', 'aster', or 'symphony'


agent_context = AgentContext()


async def set_agent_context(config_id: str, user_id: str, api_client: GGBotAPIClient):
    """
    Initialize agent context (called by runner before agent starts).
    Fetches trading_mode from database to enable proper activity logging.
    """
    agent_context.config_id = config_id
    agent_context.user_id = user_id
    agent_context.api_client = api_client

    # Fetch trading_mode from database
    try:
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT trading_mode FROM configurations WHERE config_id = %s",
                    (config_id,)
                )
                row = cur.fetchone()
                if row:
                    agent_context.trading_mode = row[0] or 'paper'
                else:
                    agent_context.trading_mode = 'paper'

        logger.info(f"Agent context set: config_id={config_id}, user_id={user_id}, trading_mode={agent_context.trading_mode}")
    except Exception as e:
        logger.error(f"Failed to fetch trading_mode, defaulting to paper: {e}")
        agent_context.trading_mode = 'paper'


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

GGSHOT SCAN MODE (NEW - for dynamic symbol discovery):
To find which symbols have recent ggshot signals, omit the symbol parameter:
{"categories": {"trading_signals": ["ggshot"]}, "scan_days": 2}
Returns list of symbols with signals from last N days (AsterDEX-compatible only).
Use this to discover active trading opportunities, then query full history for those symbols.

EXAMPLES:
{"symbol": "BTC", "categories": {"technical_analysis": ["RSI"]}}
{"symbol": "BTC", "categories": {"technical_analysis": ["RSI", "MACD"]}, "timeframe": "15m"}
{"symbol": "ETH", "categories": {"technical_analysis": ["Stochastic"], "sentiment_social": ["twitter_sentiment"]}, "timeframe": "4h"}
{"categories": {"trading_signals": ["ggshot"]}, "scan_days": 2}  # Scan mode - find active symbols

Symbol formats: "BTC", "BTCUSDT", "BTC/USDT" all work. Indicators are case-insensitive.
Params: symbol (optional for scan mode), categories (dict), timeframe (optional, default '1h'), scan_days (optional, for ggshot scan mode)""",
    {"symbol": str, "categories": dict, "timeframe": str, "scan_days": int}
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

        symbol = args.get("symbol")  # Optional now for scan mode
        categories_raw = args.get("categories", {})
        timeframe = args.get("timeframe", "1h")
        scan_days = args.get("scan_days", 2)  # Default 2 days for scan mode

        # Handle JSON string if SDK serializes the dict
        if isinstance(categories_raw, str):
            categories = json.loads(categories_raw)
        else:
            categories = categories_raw

        # SCAN MODE: No symbol provided + ggshot requested = find active symbols
        if not symbol and "trading_signals" in categories and "ggshot" in categories.get("trading_signals", []):
            logger.debug(f"   SCAN MODE: Finding symbols with ggshot signals from last {scan_days} days")

            # Query database for recent ggshot signals
            from core.common.db import get_db_connection
            from core.symbols.standardizer import UniversalSymbolStandardizer
            from core.config.repository import get_configuration

            standardizer = UniversalSymbolStandardizer()
            trading_signals_source_id = '556e0a48-8f57-4c46-a537-ad645ceb21b3'

            # Get agent's trading mode from config_data (raw JSONB)
            trading_mode = 'paper'  # default
            with get_db_connection() as config_conn:
                with config_conn.cursor() as config_cur:
                    config_cur.execute("""
                        SELECT config_data
                        FROM configurations
                        WHERE config_id = %s AND user_id = %s
                    """, (agent_context.config_id, agent_context.user_id))

                    config_row = config_cur.fetchone()
                    if config_row and config_row[0]:
                        trading_mode = config_row[0].get('trading_mode', 'paper')

            logger.debug(f"   Trading mode: {trading_mode}")

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT DISTINCT symbol, COUNT(*) as signal_count, MAX(updated_at) as last_signal
                        FROM market_data
                        WHERE data_source = %s
                        AND updated_at >= NOW() - INTERVAL '%s days'
                        AND data_points->'ggshot_signal'->>'direction' IS NOT NULL
                        GROUP BY symbol
                        ORDER BY last_signal DESC
                    """, (trading_signals_source_id, scan_days))

                    results = cur.fetchall()

                    # Filter based on trading mode
                    active_symbols = []
                    for row in results:
                        db_symbol = row[0]  # e.g., "BTC/USDT"

                        # Apply filter based on trading mode
                        is_compatible = False
                        if trading_mode == 'aster':
                            is_compatible = standardizer.is_aster_compatible(db_symbol, format_type="ccxt")
                        elif trading_mode == 'symphony':
                            is_compatible = standardizer.is_symphony_compatible(db_symbol, format_type="ccxt")
                        else:  # paper mode - all symbols supported
                            is_compatible = True

                        if is_compatible:
                            active_symbols.append({
                                "symbol": db_symbol,
                                "signal_count": row[1],
                                "last_signal": str(row[2])
                            })

                    # Dynamic response based on trading mode
                    mode_label = {
                        'aster': 'AsterDEX-compatible',
                        'symphony': 'Symphony-compatible',
                        'paper': 'available'
                    }.get(trading_mode, 'available')

                    response_text = f"🔍 Active Trading Symbols (Last {scan_days} Days)\n\n"
                    response_text += f"Trading Mode: {trading_mode.upper()}\n"
                    response_text += f"Found {len(active_symbols)} {mode_label} symbols with recent ggshot signals:\n\n"

                    for s in active_symbols:
                        response_text += f"• {s['symbol']}: {s['signal_count']} signals, last at {s['last_signal']}\n"

                    response_text += f"\nNext step: Query full ggshot history for these symbols to see all timeframes and signals."

                    # Log activity
                    log_activity_safe(
                        config_id=agent_context.config_id,
                        user_id=agent_context.user_id,
                        activity_type='market_query',
                        activity_source='agent_tool',
                        summary=f"Scanned ggshot signals: {len(active_symbols)} active symbols",
                        details={
                            'scan_mode': True,
                            'scan_days': scan_days,
                            'active_symbols': [s['symbol'] for s in active_symbols]
                        },
                        importance=6
                    )

                    return {
                        "content": [{
                            "type": "text",
                            "text": response_text
                        }]
                    }

        # Validate symbol is provided for non-scan mode
        if not symbol:
            return {
                "content": [{
                    "type": "text",
                    "text": "❌ Symbol required for market data query. Use scan mode (omit symbol + request ggshot) to find active symbols first."
                }]
            }

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

        # Extract market data for activity logging
        market_data = {}
        if result.get('data', {}).get('technicals'):
            market_data['technicals'] = result['data']['technicals']
        if result.get('data', {}).get('market_intelligence'):
            market_data['market_intelligence'] = result['data']['market_intelligence']

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
                'data_returned': bool(response_parts),
                'market_data': market_data  # NEW: Actual data agent received
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
    "Execute trade with AUTOMATIC position sizing based on confidence. REQUIRED: symbol, side (long/short), confidence (0.0-1.0), stop_loss_price, take_profit_price. System calculates position size automatically using: margin = confidence × max_position_percent × account_balance, then applies leverage. Your job: assess trade quality and provide confidence score. Confidence scale: 0.2-0.4 (weak/testing), 0.4-0.6 (decent), 0.6-0.8 (strong), 0.8-1.0 (exceptional). Higher confidence = larger position within risk limits.",
    {"symbol": str, "side": str, "confidence": float, "stop_loss_price": float, "take_profit_price": float}
)
async def execute_trade(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute trade with automatic confidence-based position sizing.

    The system automatically:
    1. Queries your account balance
    2. Calculates position size: margin = confidence × max_position_percent × balance
    3. Applies leverage from bot config (e.g., 20x)
    4. Validates stop loss distance and R/R ratio
    5. Ensures margin doesn't exceed 95% of available balance
    6. Executes trade on configured platform (paper/aster/symphony)

    Your responsibility:
    - Identify good trade setups
    - Assess conviction (confidence 0.0-1.0)
    - Determine stop loss price (technical level)
    - Determine take profit price (target level)

    Do NOT calculate position sizes or margins - the system handles this.
    Focus on: Is this a good trade? How confident am I?
    """
    try:
        symbol = args["symbol"]
        side = args["side"]
        confidence = args["confidence"]
        stop_loss_price = args["stop_loss_price"]
        take_profit_price = args["take_profit_price"]

        # Position sizing is handled by backend based on confidence
        # No manual size_usd or leverage overrides
        result = await agent_context.api_client.execute_trade(
            config_id=agent_context.config_id,
            symbol=symbol,
            side=side,
            confidence=confidence,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            size_usd=None,  # Let backend calculate from confidence
            leverage=None   # Use bot config leverage
        )

        # Check if API call succeeded AND trade actually executed
        if result.get("status") == "success":
            trade = result.get("trade", {})

            # Check nested trade status - API can return success but trade can fail!
            if trade.get("status") == "failed":
                return {
                    "content": [{
                        "type": "text",
                        "text": f"❌ Trade execution FAILED\n\n"
                                f"Symbol: {symbol}\n"
                                f"Side: {side}\n"
                                f"Reason: {trade.get('reason', 'Unknown error')}\n\n"
                                f"No position was opened. You can try again with different parameters."
                    }],
                    "isError": True
                }

            # Trade succeeded - paper_service already logs trade_entry activity
            # No duplicate logging needed here

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
            pnl_pct = pos.get("unrealized_pnl_percentage", 0)  # Fixed typo: was unrealized_pnl_percent
            entry_price = pos.get('entry_price', 0)
            current_price = pos.get('current_price', 0)
            size = pos.get('size', pos.get('size_usd', 0))  # Try 'size' first, fallback to 'size_usd'
            leverage = pos.get('leverage', 1)

            positions_text += f"• {pos['symbol']} {pos['side'].upper()}\n"
            positions_text += f"  Entry: ${entry_price:.2f} | Current: ${current_price:.2f}\n"
            positions_text += f"  Size: ${size:.2f} | Leverage: {leverage}x\n"
            positions_text += f"  P&L: ${pnl:.2f} ({pnl_pct:.2f}%)\n"

            # Show ID field based on what's available (paper uses trade_id, live uses batch_id or orderId)
            if 'trade_id' in pos:
                positions_text += f"  Trade ID: {pos['trade_id']}\n\n"
            elif 'batch_id' in pos:
                positions_text += f"  Batch ID: {pos['batch_id']}\n\n"
            elif 'orderId' in pos:
                positions_text += f"  Order ID: {pos['orderId']}\n\n"
            else:
                positions_text += "\n"  # No ID field available

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

    Supports both paper trading and live trading (Aster/Symphony).
    """
    try:
        result = await agent_context.api_client.get_account_status(
            config_id=agent_context.config_id
        )

        account = result.get("account", {})
        trading_mode = result.get("trading_mode", "paper")

        # Fix: API returns 'balance', not 'current_balance'
        balance = account.get("balance", 0)
        total_pnl = account.get("total_pnl", 0)
        total_trades = account.get("total_trades", 0)
        win_rate = account.get("win_rate", 0)
        open_positions = account.get("open_positions", 0)

        # Additional live trading metrics
        margin_balance = account.get("margin_balance", 0)
        unrealized_pnl = account.get("unrealized_pnl", 0)
        open_orders = account.get("open_orders", [])

        # Dynamic header based on trading mode
        mode_label = {
            "paper": "Paper Trading",
            "aster": "Live Trading (AsterDEX)",
            "symphony": "Live Trading (Symphony)"
        }.get(trading_mode, "Trading")

        account_text = f"""
📊 Account Status ({mode_label})

Balance: ${balance:,.2f}
Total P&L: ${total_pnl:,.2f}
Total Trades: {total_trades}
Win Rate: {win_rate:.1%}

Open Positions: {open_positions}
        """.strip()

        # Add live trading specific details if available
        if trading_mode in ["aster", "symphony"] and margin_balance != 0:
            account_text += f"""

Margin Balance: ${margin_balance:,.2f}
Unrealized P&L: ${unrealized_pnl:,.2f}
            """.strip()

        # Add open orders section if any exist
        if open_orders:
            account_text += f"""

📋 Open Orders ({len(open_orders)}):
            """.strip()

            for order in open_orders:
                order_type = order.get('type', 'UNKNOWN')
                symbol = order.get('symbol', 'UNKNOWN')
                side = order.get('side', 'UNKNOWN')
                qty = float(order.get('origQty', 0))
                order_id = order.get('orderId', 'unknown')

                # Format based on order type
                if order_type in ['STOP_MARKET', 'STOP']:
                    stop_price = float(order.get('stopPrice', 0))
                    account_text += f"""
  • SL: {symbol} {side} {qty} @ ${stop_price:,.2f} (ID: {order_id})"""
                elif order_type in ['TAKE_PROFIT_MARKET', 'TAKE_PROFIT']:
                    stop_price = float(order.get('stopPrice', 0))
                    account_text += f"""
  • TP: {symbol} {side} {qty} @ ${stop_price:,.2f} (ID: {order_id})"""
                elif order_type == 'LIMIT':
                    price = float(order.get('price', 0))
                    account_text += f"""
  • LIMIT: {symbol} {side} {qty} @ ${price:,.2f} (ID: {order_id})"""
                else:
                    account_text += f"""
  • {order_type}: {symbol} {side} {qty} (ID: {order_id})"""

            account_text += """

💡 Tip: Use cancel_order tool to remove orphaned orders"""

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
    "Close an open trading position. Params: trade_id (required - use batch_id from get_positions for live trades, or trade_id for paper trades), reasoning (required - explain why closing)",
    {"trade_id": str, "reasoning": str}
)
async def close_position(args: Dict[str, Any]) -> Dict[str, Any]:
    """Close a specific position. For live trades (Aster/Symphony), use the batch_id from get_positions as trade_id."""
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

            # Trade exit - paper_service already logs trade_exit activity
            # No duplicate logging needed here

            return {
                "content": [{
                    "type": "text",
                    "text": f"✅ Position closed successfully!\n\n"
                            f"Symbol: {trade.get('symbol', 'N/A')}\n"
                            f"Side: {trade.get('side', 'N/A')}\n"
                            f"P&L: ${pnl:.2f} ({pnl_pct:.2f}%)\n"
                            f"Reason: {reasoning}\n\n"
                            f"**NEXT STEPS:**\n"
                            f"1. Record a trade observation (optional but recommended)\n"
                            f"2. Use wait_for() to schedule your next market scan\n"
                            f"3. Continue autonomous trading loop\n\n"
                            f"Remember: You must ALWAYS use wait_for() to control timing between actions."
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
# TOOL 6: CANCEL ORDER
# ============================================================================

@tool(
    "cancel_order",
    "Cancel a specific open order (TP/SL/Limit). Params: order_id (required), symbol (required)",
    {"order_id": str, "symbol": str}
)
async def cancel_order(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cancel an open order by ID.

    Use this to clean up orphaned TP/SL orders or cancel pending limit orders.
    Check get_account_status to see all open orders first.
    """
    try:
        order_id = args["order_id"]
        symbol = args["symbol"]

        result = await agent_context.api_client.cancel_order(
            config_id=agent_context.config_id,
            order_id=order_id,
            symbol=symbol
        )

        if result.get("status") == "success":
            return {
                "content": [{
                    "type": "text",
                    "text": f"✅ Order cancelled successfully!\n\n"
                            f"Order ID: {order_id}\n"
                            f"Symbol: {symbol}\n\n"
                            f"The order has been removed from your account."
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": f"⚠️ Failed to cancel order: {result.get('message', 'Unknown error')}"
                }]
            }

    except Exception as e:
        logger.error(f"cancel_order failed: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to cancel order: {str(e)}"
            }]
        }


# ============================================================================
# TOOL 7: UPDATE STRATEGY
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

        next_check = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)

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
                "text": f"⏳ Waited {duration_minutes} minutes. Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                        f"Reason: {reason}\n\n"
                        f"**CONTINUE YOUR LOOP NOW** - Call get_positions() to check position status, "
                        f"then query_market_data_for_rei() if you need fresh analysis. "
                        f"Do NOT just acknowledge this message - CALL A TOOL."
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

        logger.info(f"Recording observation: trade_id={trade_id}, type={observation_type}")

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
            observation_id = result.get("observation_id", "unknown")
            logger.info(f"Observation recorded successfully: {observation_id}")

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
                            f"Trade ID: {trade_id}\n"
                            f"Observation ID: {observation_id}\n\n"
                            f"This learning is now queryable for future reference."
                }]
            }
        else:
            error_msg = result.get('message') or result.get('error') or result.get('detail') or 'Unknown error'
            logger.error(f"record_trade_observation API failed: {error_msg}, full response: {result}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"❌ Failed to record observation: {error_msg}"
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

        logger.info(f"Querying observations: symbol={symbol}, type={observation_type}, min_importance={min_importance}, limit={limit}")

        result = await agent_context.api_client.query_trade_observations(
            config_id=agent_context.config_id,
            symbol=symbol,
            observation_type=observation_type,
            min_importance=min_importance,
            limit=limit
        )

        # Check for API error response
        if result.get("status") == "error":
            error_msg = result.get("error", "Unknown API error")
            logger.error(f"query_trade_observations API error: {error_msg}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"❌ API error querying observations: {error_msg}"
                }]
            }

        # Check if response has expected structure
        if "observations" not in result:
            logger.warning(f"query_trade_observations unexpected response: {result}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"⚠️ Unexpected API response format. Raw: {str(result)[:200]}"
                }]
            }

        observations = result.get("observations", [])
        logger.info(f"Query returned {len(observations)} observations")

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

        # Log activity to timeline
        log_activity_safe(
            config_id=config_id,
            user_id=user_id,
            activity_type='strategy_updated',
            activity_source='agent_tool',
            summary=f"Strategy saved (autonomously_editable={autonomously_editable})",
            details={
                'strategy_content': strategy_summary[:200],  # First 200 chars
                'autonomously_editable': autonomously_editable,
                'version': 1
            },
            importance=10
        )

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
# TOOL 13: QUERY MARKET DATA FOR REI
# ============================================================================

@tool(
    "query_market_data_for_rei",
    """Fetch comprehensive market data and prepare it for Rei consultation.

This tool fetches ALL available market data (32 data points) and stores it for the
consult_rei_for_decision tool. Use this BEFORE consulting Rei.

DATA FETCHED:
- 21 Technical Indicators: RSI, MACD, Stochastic, Williams_R, CCI, MFI, ADX, PSAR, Aroon, ATR, BB, OBV, SMA, EMA, ROC, VWAP, TRIX, Vortex, BBWidth, Keltner, Donchian
- 11 Market Intelligence: btc_funding_rate, eth_funding_rate, vix, dxy, cpi, nfp, btc_tvl, whale_activity, twitter_sentiment, crypto_news, ggshot

Returns a SUMMARY for you to see. Full data is stored in session buffer for Rei.

Params: symbol (required, e.g. "BTC" or "BTC/USDT"), timeframe (optional, default "4h")""",
    {"symbol": str, "timeframe": str}
)
async def query_market_data_for_rei(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch all market data and store in session buffer for Rei consultation.

    This is a preparation step before calling consult_rei_for_decision.
    The full data (~15-20KB) goes to the buffer, Claude receives a summary.

    Uses HTTP API calls (same pattern as query_market_data) to work in agent venv.
    """
    try:
        from agent.session_buffer import get_session_buffer

        symbol = args["symbol"]
        timeframe = args.get("timeframe", "4h")
        config_id = agent_context.config_id
        user_id = agent_context.user_id

        logger.info(f"query_market_data_for_rei: Fetching data for {symbol} ({timeframe})")

        # All technical indicators
        all_indicators = [
            "rsi", "macd", "stochastic", "williams_r", "cci", "mfi",
            "adx", "psar", "aroon", "atr", "bbands", "obv",
            "sma", "ema", "roc", "vwap", "trix", "vortex",
            "bbwidth", "keltner", "donchian"
        ]

        # All market intelligence data points
        # NOTE: Category names must match catalog_mapping.py exactly
        all_intel_sources = {
            "derivatives_leverage": ["btc_funding_rate", "eth_funding_rate"],
            "macro_economics": ["vix", "dxy", "cpi", "nfp"],
            "onchain_analytics": ["btc_tvl", "whale_activity"],  # Fixed: was "on_chain_analytics"
            "sentiment_social": ["twitter_sentiment"],
            "news_regulatory": ["crypto_news"],
            "trading_signals": ["ggshot"]
        }

        # Use HTTP API client (same pattern as query_market_data)
        result = await agent_context.api_client.query_market_data(
            config_id=config_id,
            symbol=symbol,
            indicators=all_indicators,
            data_sources=all_intel_sources,
            timeframe=timeframe
        )

        # Debug: Log what we got back
        logger.info(f"query_market_data_for_rei: API result type={type(result)}, content={str(result)[:500]}")

        # Handle case where result might be a string (error) or None
        if not isinstance(result, dict):
            logger.error(f"Unexpected result type from API: {type(result)} - {str(result)[:200]}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"❌ API returned unexpected type: {type(result).__name__}. Check API logs."
                }]
            }

        # Extract data from API response
        # API returns nested structure: {'data': {'technicals': {'status': 'success', 'result': {'indicators': {...}}}}}
        technicals_response = result.get('data', {}).get('technicals', {})
        technicals = technicals_response.get('result', {}).get('indicators', {}) if isinstance(technicals_response, dict) else {}

        market_intel = result.get('data', {}).get('market_intelligence', {})
        # market_intel is already flat dict of categories (no nested 'result' key)

        collected_data = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.utcnow().isoformat(),
            "technical_indicators": technicals,
            "market_intelligence": market_intel
        }

        # Build summary
        summary_parts = []

        # Summarize technicals
        if technicals:
            key_summaries = []
            for ind_name in ["rsi", "macd", "adx"]:
                ind_data = technicals.get(ind_name, {})
                if isinstance(ind_data, dict):
                    current = ind_data.get("current", {})
                    if isinstance(current, dict):
                        value = current.get("value", current.get("adx", "N/A"))
                        if isinstance(value, (int, float)):
                            key_summaries.append(f"{ind_name.upper()}={value:.1f}")
            summary_parts.append(f"Technical ({len(technicals)} indicators): {', '.join(key_summaries)}")
        else:
            summary_parts.append("Technical: No data")

        # Summarize intelligence
        if market_intel and isinstance(market_intel, dict):
            intel_summaries = []
            for category, points in market_intel.items():
                if isinstance(points, dict):
                    for point_name, point_data in points.items():
                        if isinstance(point_data, dict):
                            # Safely extract signal from either top level or nested interpretation
                            signal = point_data.get("signal", "")
                            if not signal:
                                interpretation = point_data.get("interpretation", {})
                                if isinstance(interpretation, dict):
                                    signal = interpretation.get("signal", "")
                            if signal and isinstance(signal, str):
                                intel_summaries.append(f"{point_name}={signal}")
            if intel_summaries:
                summary_parts.append(f"Intelligence: {', '.join(intel_summaries[:5])}")
        else:
            summary_parts.append("Intelligence: No data")

        # Store in session buffer
        buffer = get_session_buffer()
        buffer.store(
            session_key=config_id,
            data=collected_data,
            symbol=symbol,
            metadata={
                "indicator_count": len(technicals),
                "intel_categories": len(market_intel)
            }
        )

        # Log activity
        log_activity_safe(
            config_id=config_id,
            user_id=user_id,
            activity_type='market_query',
            activity_source='agent_tool',
            summary=f"Prepared data for Rei: {symbol}",
            details={
                'symbol': symbol,
                'timeframe': timeframe,
                'indicator_count': len(technicals),
                'intel_categories': list(market_intel.keys()) if market_intel else []
            },
            related_symbol=symbol,
            importance=5
        )

        response_text = f"""📊 Market Data Ready for Rei Consultation

Symbol: {symbol}
Timeframe: {timeframe}

{chr(10).join(summary_parts)}

Data stored in session buffer. Call consult_rei_for_decision() to get Rei's trading decision."""

        return {
            "content": [{
                "type": "text",
                "text": response_text
            }]
        }

    except Exception as e:
        logger.error(f"query_market_data_for_rei failed: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to prepare market data for Rei: {str(e)}"
            }]
        }


# ============================================================================
# TOOL 14: CONSULT REI FOR DECISION
# ============================================================================

@tool(
    "consult_rei_for_decision",
    """Consult Rei (learning AI) for a trading decision using prepared market data.

IMPORTANT: Call query_market_data_for_rei FIRST to prepare the data.

Rei analyzes all 32 data points and returns a structured decision with:
- action: enter_long, enter_short, exit, wait
- confidence: 0.0-1.0 (Rei's calibrated confidence)
- reasoning: explanation of key factors
- key_signals: list of important signals
- warnings: any concerns

Rei learns from every outcome you report, improving over time.

Params: current_positions (required - describe open positions or "none"), account_balance (required - current USD balance)""",
    {"current_positions": str, "account_balance": float}
)
async def consult_rei_for_decision(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send market data to Rei and get a trading decision.

    Reads from session buffer (populated by query_market_data_for_rei),
    builds a self-contained message for Rei API, and returns the decision.
    """
    try:
        import os
        from agent.session_buffer import get_session_buffer
        from core.services.rei_service import ReiService, ReiServiceError

        current_positions = args["current_positions"]
        account_balance = args["account_balance"]
        config_id = agent_context.config_id

        # Get data from session buffer
        buffer = get_session_buffer()
        market_data = buffer.retrieve(config_id, clear=True)

        if not market_data:
            return {
                "content": [{
                    "type": "text",
                    "text": "❌ No market data in buffer. Call query_market_data_for_rei first."
                }]
            }

        # Check for Rei credentials
        rei_secret = os.getenv("REI_01_UNIT_SECRET")
        if not rei_secret:
            return {
                "content": [{
                    "type": "text",
                    "text": "❌ Rei not configured. Set REI_01_UNIT_SECRET environment variable."
                }]
            }

        # Build self-contained message for Rei (API has NO session context)
        rei_message = {
            "task": "trading_decision",
            "symbol": market_data.get("symbol"),
            "timeframe": market_data.get("timeframe"),
            "current_positions": current_positions,
            "account_balance_usd": account_balance,
            "market_data": {
                "technical_indicators": market_data.get("technical_indicators", {}),
                "market_intelligence": market_data.get("market_intelligence", {})
            },
            "question": "Based on this market data, what trading action should I take? Provide your decision as JSON."
        }

        logger.info(f"Consulting Rei for {market_data.get('symbol')} decision...")

        # Call Rei API
        try:
            rei = ReiService(agent_secret_key=rei_secret)

            response = await rei.chat_completion(
                messages=[{
                    "role": "user",
                    "content": json.dumps(rei_message, indent=2)
                }],
                response_format={"type": "json_object"},
                temperature=0.45,
                max_tokens=2000
            )

            await rei.close()

            # Parse Rei's response
            try:
                decision = json.loads(response.content)
            except json.JSONDecodeError:
                # If not valid JSON, wrap the response
                decision = {
                    "action": "wait",
                    "confidence": 0.0,
                    "reasoning": response.content,
                    "key_signals": [],
                    "warnings": ["Response was not valid JSON"]
                }

            # Extract decision fields
            action = decision.get("action", "wait")
            confidence = decision.get("confidence", 0.0)
            reasoning = decision.get("reasoning", "No reasoning provided")
            key_signals = decision.get("key_signals", [])
            warnings = decision.get("warnings", [])
            take_profit = decision.get("take_profit")
            stop_loss = decision.get("stop_loss")

            # Log activity
            log_activity_safe(
                config_id=config_id,
                user_id=agent_context.user_id,
                activity_type='rei_decision',
                activity_source='agent_tool',
                summary=f"Rei: {action.upper()} ({confidence:.0%} confidence)",
                details={
                    'action': action,
                    'confidence': confidence,
                    'reasoning': reasoning,
                    'key_signals': key_signals,
                    'warnings': warnings,
                    'symbol': market_data.get("symbol"),
                    'take_profit': take_profit,
                    'stop_loss': stop_loss
                },
                related_symbol=market_data.get("symbol"),
                importance=8
            )

            # Format TP/SL lines if present
            tp_sl_text = ""
            if take_profit is not None or stop_loss is not None:
                tp_sl_text = "\n"
                if take_profit is not None:
                    tp_sl_text += f"Take Profit: ${take_profit:,.2f}\n"
                if stop_loss is not None:
                    tp_sl_text += f"Stop Loss: ${stop_loss:,.2f}\n"

            # Format response for Claude
            response_text = f"""🧠 Rei Trading Decision

Symbol: {market_data.get('symbol')}
Action: {action.upper()}
Confidence: {confidence:.1%}
{tp_sl_text}
Reasoning: {reasoning}

Key Signals: {', '.join(key_signals) if key_signals else 'None specified'}
Warnings: {', '.join(warnings) if warnings else 'None'}

{"⚠️ Low confidence - consider waiting" if confidence < 0.55 else "✅ Confidence threshold met" if confidence >= 0.60 else "⚡ Marginal confidence - proceed with caution"}"""

            return {
                "content": [{
                    "type": "text",
                    "text": response_text
                }]
            }

        except ReiServiceError as e:
            logger.error(f"Rei API error: {e}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"❌ Rei API error: {str(e)}\n\nFallback: Use your own judgment based on the market data summary."
                }]
            }

    except Exception as e:
        logger.error(f"consult_rei_for_decision failed: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to consult Rei: {str(e)}"
            }]
        }


# ============================================================================
# TOOL 15: REPORT TRADE OUTCOME TO REI
# ============================================================================

@tool(
    "report_trade_outcome_to_rei",
    """Report a closed trade outcome to Rei for learning.

CRITICAL: Call this after every trade closes. This is how Rei learns and improves.

Send RAW FACTS only - do not include Rei's previous reasoning or predictions.
Rei uses this feedback to strengthen patterns that work and weaken patterns that don't.

Params:
- symbol (required): e.g. "BTC/USDT"
- side (required): "long" or "short"
- entry_price (required): price at entry
- exit_price (required): price at exit
- pnl_usd (required): profit/loss in USD
- pnl_percent (required): profit/loss percentage
- duration_hours (required): how long the trade was open
- close_reason (required): "take_profit", "stop_loss", "manual", or "liquidation"
- conditions_at_entry (required): brief description of market conditions when entered""",
    {"symbol": str, "side": str, "entry_price": float, "exit_price": float, "pnl_usd": float, "pnl_percent": float, "duration_hours": float, "close_reason": str, "conditions_at_entry": str}
)
async def report_trade_outcome_to_rei(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Report trade outcome to Rei for learning.

    Sends raw facts about the trade without Rei's previous output.
    This is critical for Rei's pattern evolution.
    """
    try:
        import os
        from core.services.rei_service import ReiService, ReiServiceError

        symbol = args["symbol"]
        side = args["side"]
        entry_price = args["entry_price"]
        exit_price = args["exit_price"]
        pnl_usd = args["pnl_usd"]
        pnl_percent = args["pnl_percent"]
        duration_hours = args["duration_hours"]
        close_reason = args["close_reason"]
        conditions_at_entry = args["conditions_at_entry"]

        config_id = agent_context.config_id

        # Check for Rei credentials
        rei_secret = os.getenv("REI_01_UNIT_SECRET")
        if not rei_secret:
            return {
                "content": [{
                    "type": "text",
                    "text": "❌ Rei not configured. Set REI_01_UNIT_SECRET environment variable."
                }]
            }

        # Build feedback message (RAW FACTS ONLY - no previous Rei output)
        outcome = "WIN" if pnl_usd > 0 else "LOSS" if pnl_usd < 0 else "BREAKEVEN"

        feedback_message = f"""TRADE OUTCOME REPORT

Symbol: {symbol}
Side: {side.upper()}
Result: {outcome}

Entry Price: ${entry_price:,.2f}
Exit Price: ${exit_price:,.2f}
P&L: ${pnl_usd:+,.2f} ({pnl_percent:+.2f}%)

Duration: {duration_hours:.1f} hours
Close Reason: {close_reason}

Market Conditions at Entry:
{conditions_at_entry}

Learn from this outcome. If this was a winning trade, strengthen the patterns that led to this entry. If this was a losing trade, weaken those patterns or identify what was missed."""

        logger.info(f"Reporting trade outcome to Rei: {symbol} {side} {outcome}")

        try:
            rei = ReiService(agent_secret_key=rei_secret)

            response = await rei.chat_completion(
                messages=[{
                    "role": "user",
                    "content": feedback_message
                }],
                temperature=0.3,  # Lower temperature for learning
                max_tokens=500
            )

            await rei.close()

            # Log activity
            log_activity_safe(
                config_id=config_id,
                user_id=agent_context.user_id,
                activity_type='rei_learning',
                activity_source='agent_tool',
                summary=f"Reported {outcome} to Rei: {symbol} {side}",
                details={
                    'symbol': symbol,
                    'side': side,
                    'outcome': outcome,
                    'pnl_usd': pnl_usd,
                    'pnl_percent': pnl_percent,
                    'close_reason': close_reason
                },
                related_symbol=symbol,
                importance=7
            )

            return {
                "content": [{
                    "type": "text",
                    "text": f"""✅ Trade outcome reported to Rei

Symbol: {symbol}
Side: {side.upper()}
Result: {outcome} (${pnl_usd:+,.2f})

Rei's acknowledgment:
{response.content[:500]}{'...' if len(response.content) > 500 else ''}

Rei will use this feedback to improve future decisions."""
                }]
            }

        except ReiServiceError as e:
            logger.error(f"Rei API error reporting outcome: {e}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"⚠️ Could not report to Rei: {str(e)}\n\nThe trade outcome was not recorded for learning."
                }]
            }

    except Exception as e:
        logger.error(f"report_trade_outcome_to_rei failed: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to report trade outcome: {str(e)}"
            }]
        }


# ============================================================================
# MCP SERVER CREATION
# ============================================================================

def create_mcp_server():
    """
    Create MCP server with 15 tools for autonomous trading agent.

    Returns:
        MCP server instance to be used with Claude Agent SDK
    """
    logger.info("Creating MCP server with 15 trading tools (including Rei integration)")

    # LOG: All tool definitions
    logger.debug("📚 MCP TOOLS BEING REGISTERED:")
    logger.debug("   1. query_market_data - Query market data across 7 categories")
    logger.debug("   2. get_current_price - Get current price for a symbol")
    logger.debug("   3. execute_trade - Execute a trade")
    logger.debug("   4. get_positions - Get open trading positions")
    logger.debug("   5. get_account_status - Get account balance, statistics, and open orders")
    logger.debug("   6. close_position - Close an open position")
    logger.debug("   7. cancel_order - Cancel a specific open order (TP/SL/Limit)")
    logger.debug("   8. update_strategy - Update trading strategy")
    logger.debug("   9. wait_for - Pause execution")
    logger.debug("   10. record_trade_observation - Record trade learnings")
    logger.debug("   11. query_trade_observations - Query past observations")
    logger.debug("   12. save_strategy_and_exit - Save strategy and exit")
    logger.debug("   13. query_market_data_for_rei - Fetch all data and prepare for Rei")
    logger.debug("   14. consult_rei_for_decision - Get trading decision from Rei")
    logger.debug("   15. report_trade_outcome_to_rei - Report trade results for Rei learning")

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
            cancel_order,
            update_strategy,
            wait_for,
            record_trade_observation,
            query_trade_observations,
            save_strategy_and_exit,
            # Rei integration tools
            query_market_data_for_rei,
            consult_rei_for_decision,
            report_trade_outcome_to_rei
        ]
    )

    logger.info("MCP server created successfully with 15 tools")
    return server


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "create_mcp_server",
    "set_agent_context",
    "agent_context"
]
