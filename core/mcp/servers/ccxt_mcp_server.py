#!/usr/bin/env python
"""
CCXT MCP Server for ggbots.

This server exposes cryptocurrency exchange functionality via MCP.
"""

import logging
import sys
import os
import json
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[3]))

from mcp.server.fastmcp import FastMCP, Context

# Setup logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ccxt_mcp_server")

# Simplified server with direct environment variable credential handling
logger.info("Running CCXT MCP server with simplified credential handling")

# Create MCP server
mcp = FastMCP("CCXTExchange")

# Trading pair mapping for different exchanges
EXCHANGE_SYMBOL_MAP = {
    'bitmex': {
        'BTC/USD': 'XBT/USD:XBt',
        'BTC/USDT': 'XBT/USDT:USDT',
        'ETH/USD': 'ETH/USDT:USDT',
        'ETH/USDT': 'ETH/USDT:USDT',
        'XRP/USD': 'XRP/USD:XBt',
        'XRP/USDT': 'XRP/USDT:USDT',
        'SOL/USD': 'SOL/USD:XBt',
        'SOL/USDT': 'SOL/USDT:USDT',
        'DOGE/USD': 'DOGE/USD:XBt',
        'DOGE/USDT': 'DOGE/USDT:USDT'
    }
}

def map_symbol_for_exchange(exchange_id, symbol):
    """Map a standard symbol to exchange-specific format."""
    exchange_map = EXCHANGE_SYMBOL_MAP.get(exchange_id.lower(), {})
    return exchange_map.get(symbol, symbol)

async def get_exchange_instance(exchange_id, user_id=None):
    """Get a CCXT exchange instance with simplified credential handling."""
    try:
        # Dynamically import CCXT
        import ccxt.async_support as ccxt

        # Log environment variables for debugging
        env_api = os.environ.get("EXCHANGE_API", "")
        env_secret = os.environ.get("EXCHANGE_SECRET", "")
        env_exchange = os.environ.get("EXCHANGE_NAME", "")

        logger.debug(f"Environment variables: EXCHANGE_NAME={env_exchange}, "
                    f"API key exists: {bool(env_api)}, Secret exists: {bool(env_secret)}")

        # Get the exchange class
        if not hasattr(ccxt, exchange_id):
            raise ValueError(f"Exchange {exchange_id} not supported by CCXT")

        exchange_class = getattr(ccxt, exchange_id)

        # Simplified credential handling - use environment variables with hardcoded fallbacks
        # Hardcoded fallback values for testing BitMEX testnet
        api_key = env_api or "arfvFIW1EQSs_gm2OGooR_f4"
        secret = env_secret or "a8XHhSw8IX5OAp3wOfRAypNUrQj1y5k3tNWWd4O6gZ9GrIGU"

        # Create direct credentials dictionary
        credentials = {
            "apiKey": api_key,
            "secret": secret,
            "enableRateLimit": True,
            "test": True  # Always use testnet for safety
        }

        # Log the credentials (without the actual secret)
        logger.debug(f"Creating exchange with credentials: apiKey={api_key[:4]}..., secret=****")

        # Create the exchange instance
        exchange = exchange_class(credentials)

        # Enable sandbox mode if available
        if hasattr(exchange, 'setSandboxMode'):
            exchange.setSandboxMode(True)

        logger.info(f"Successfully created {exchange_id} exchange instance")
        return exchange
    except Exception as e:
        logger.error(f"Error creating exchange instance: {str(e)}")
        logger.exception("Stack trace:")
        raise

@mcp.tool()
async def get_exchange_ids() -> dict:
    """
    Get a list of all supported exchange IDs.

    Returns:
        Dictionary containing a list of exchange IDs
    """
    logger.info("Executing get_exchange_ids")

    try:
        import ccxt

        exchange_ids = ccxt.exchanges
        return {"ids": exchange_ids}
    except Exception as e:
        logger.error(f"Error getting exchange IDs: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def fetch_markets(exchange_id: str = None, user_id: str = None) -> list:
    """
    Fetch markets available on an exchange.

    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        user_id: Optional user ID for authenticated requests

    Returns:
        List of market data
    """
    if exchange_id is None:
        return {"error": "Missing required parameter: exchange_id"}

    logger.info(f"Executing fetch_markets on {exchange_id}")

    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)

        try:
            # Fetch markets
            markets = await exchange.fetch_markets()

            # Clean the data for return
            cleaned_markets = []
            for market in markets:  # Return all markets
                cleaned_market = {
                    "symbol": market.get('symbol'),
                    "base": market.get('base'),
                    "quote": market.get('quote'),
                    "type": market.get('type'),
                    "active": market.get('active')
                }
                cleaned_markets.append(cleaned_market)

            # Debug the return value type
            logger.debug(f"Returning markets result type: {type(cleaned_markets)}")

            # Return plain list of dictionaries, FastMCP will handle the wrapping
            return cleaned_markets
        finally:
            await exchange.close()

    except Exception as e:
        logger.error(f"Error fetching markets: {str(e)}")
        # Return a simple error dictionary
        return {"error": str(e)}

@mcp.tool()
async def fetch_ticker(exchange_id: str = None, symbol: str = None,
                      user_id: str = None) -> dict:
    """
    Fetch current ticker data for a symbol from an exchange.

    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        user_id: Optional user ID for authenticated requests

    Returns:
        Dictionary containing ticker data
    """
    if exchange_id is None:
        return {"error": "Missing required parameter: exchange_id"}

    if symbol is None:
        return {"error": "Missing required parameter: symbol"}

    # Map symbol to exchange-specific format if needed
    mapped_symbol = map_symbol_for_exchange(exchange_id, symbol)
    if mapped_symbol != symbol:
        logger.info(f"Mapped {symbol} to {mapped_symbol} for {exchange_id}")

    logger.info(f"Executing fetch_ticker for {mapped_symbol} on {exchange_id}")

    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)

        try:
            ticker = await exchange.fetch_ticker(mapped_symbol)

            # Clean result for serialization - ensure we return a plain dictionary
            cleaned_ticker = {k: v for k, v in ticker.items() if k not in ['info']}

            # Debug the return value type to confirm it's a simple dict
            logger.debug(f"Returning result type: {type(cleaned_ticker)}")

            # Return the cleaned ticker as a simple dictionary
            # FastMCP will handle wrapping it in a CallToolResult
            return cleaned_ticker
        finally:
            await exchange.close()

    except Exception as e:
        logger.error(f"Error fetching ticker: {str(e)}")
        # Return a simple error dictionary
        return {"error": str(e)}

@mcp.tool()
async def fetch_ohlcv(exchange_id: str = None, symbol: str = None,
                    timeframe: str = '1h', since: int = None, limit: int = None,
                    user_id: str = None) -> list:
    """
    Fetch OHLCV (candle) data for a symbol from an exchange.

    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        timeframe: Timeframe (e.g., '1m', '5m', '1h', '1d')
        since: Optional timestamp in milliseconds to fetch data since
        limit: Optional limit on the number of candles to fetch
        user_id: Optional user ID for authenticated requests

    Returns:
        List of OHLCV candles [timestamp, open, high, low, close, volume]
    """
    if exchange_id is None:
        return {"error": "Missing required parameter: exchange_id"}

    if symbol is None:
        return {"error": "Missing required parameter: symbol"}

    # Map symbol to exchange-specific format if needed
    mapped_symbol = map_symbol_for_exchange(exchange_id, symbol)
    if mapped_symbol != symbol:
        logger.info(f"Mapped {symbol} to {mapped_symbol} for {exchange_id}")

    logger.info(f"Executing fetch_ohlcv for {mapped_symbol} ({timeframe}) on {exchange_id}")

    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)

        try:
            # Check if the exchange supports OHLCV data
            if not exchange.has['fetchOHLCV']:
                return {"error": f"Exchange {exchange_id} does not support OHLCV data"}

            # Fetch OHLCV data
            ohlcv = await exchange.fetch_ohlcv(mapped_symbol, timeframe, since, limit)

            # Ensure consistent data format for all exchanges
            processed_ohlcv = []
            for candle in ohlcv:
                # Make sure all values are regular Python types (not numpy, etc.)
                processed_candle = [float(val) if isinstance(val, (int, float)) else val for val in candle]
                processed_ohlcv.append(processed_candle)

            return processed_ohlcv
        finally:
            await exchange.close()

    except Exception as e:
        logger.error(f"Error fetching OHLCV data: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def fetch_order_book(exchange_id: str = None, symbol: str = None,
                          limit: int = None, user_id: str = None) -> dict:
    """
    Fetch order book for a symbol from an exchange.

    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        limit: Optional limit on the number of orders to fetch
        user_id: Optional user ID for authenticated requests

    Returns:
        Dictionary containing order book data
    """
    if exchange_id is None:
        return {"error": "Missing required parameter: exchange_id"}

    if symbol is None:
        return {"error": "Missing required parameter: symbol"}

    # Map symbol to exchange-specific format if needed
    mapped_symbol = map_symbol_for_exchange(exchange_id, symbol)
    if mapped_symbol != symbol:
        logger.info(f"Mapped {symbol} to {mapped_symbol} for {exchange_id}")

    logger.info(f"Executing fetch_order_book for {mapped_symbol} on {exchange_id}")

    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)

        try:
            # Fetch order book
            order_book = await exchange.fetch_order_book(mapped_symbol, limit)

            # Create a cleaned, serializable result dictionary
            cleaned_result = {
                "symbol": symbol,
                "bids": order_book.get('bids', [])[:10],  # Limit to top 10 orders
                "asks": order_book.get('asks', [])[:10],  # Limit to top 10 orders
                "timestamp": order_book.get('timestamp'),
                "datetime": order_book.get('datetime')
            }

            # Debug the return value type
            logger.debug(f"Returning order book result type: {type(cleaned_result)}")

            # Return plain dictionary, FastMCP will handle the wrapping
            return cleaned_result
        finally:
            await exchange.close()

    except Exception as e:
        logger.error(f"Error fetching order book: {str(e)}")
        # Return a simple error dictionary
        return {"error": str(e)}

@mcp.tool()
async def create_market_buy_order(exchange_id: str = None, symbol: str = None, amount: float = None,
                                 user_id: str = None, params: dict = None) -> dict:
    """
    Create a market buy order on an exchange.

    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        amount: Amount to buy
        user_id: User ID for authenticated request
        params: Optional additional parameters for the exchange

    Returns:
        Dictionary containing order details
    """
    if exchange_id is None:
        return {"error": "Missing required parameter: exchange_id"}

    if symbol is None:
        return {"error": "Missing required parameter: symbol"}
        
    if amount is None:
        return {"error": "Missing required parameter: amount"}
        
    # Map symbol to exchange-specific format if needed
    mapped_symbol = map_symbol_for_exchange(exchange_id, symbol)
    if mapped_symbol != symbol:
        logger.info(f"Mapped {symbol} to {mapped_symbol} for {exchange_id}")
    
    logger.info(f"Executing create_market_buy_order for {mapped_symbol} on {exchange_id}, amount={amount}")
    
    if params is None:
        params = {}
    
    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)
        
        try:
            # Create the order
            order = await exchange.create_market_buy_order(mapped_symbol, amount, params)
            
            # Clean result for serialization
            cleaned_order = {}
            for k, v in order.items():
                if k != 'info':  # Skip the raw exchange info
                    if isinstance(v, (int, float, str, bool, list, dict)) or v is None:
                        cleaned_order[k] = v
                    else:
                        # Convert non-serializable types to string
                        cleaned_order[k] = str(v)
            
            return cleaned_order
        finally:
            await exchange.close()
            
    except Exception as e:
        logger.error(f"Error creating market buy order: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def create_market_sell_order(exchange_id: str, symbol: str, amount: float, 
                                  user_id: str, params: dict = None) -> dict:
    """
    Create a market sell order on an exchange.
    
    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        amount: Amount to sell
        user_id: User ID for authenticated request
        params: Optional additional parameters for the exchange
        
    Returns:
        Dictionary containing order details
    """
    if symbol is None:
        return {"error": "Missing required parameter: symbol"}
        
    if amount is None:
        return {"error": "Missing required parameter: amount"}
        
    # Map symbol to exchange-specific format if needed
    mapped_symbol = map_symbol_for_exchange(exchange_id, symbol)
    if mapped_symbol != symbol:
        logger.info(f"Mapped {symbol} to {mapped_symbol} for {exchange_id}")
    
    logger.info(f"Executing create_market_sell_order for {mapped_symbol} on {exchange_id}, amount={amount}")
    
    if params is None:
        params = {}
    
    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)
        
        try:
            # Create the order
            order = await exchange.create_market_sell_order(mapped_symbol, amount, params)
            
            # Clean result for serialization
            cleaned_order = {}
            for k, v in order.items():
                if k != 'info':  # Skip the raw exchange info
                    if isinstance(v, (int, float, str, bool, list, dict)) or v is None:
                        cleaned_order[k] = v
                    else:
                        # Convert non-serializable types to string
                        cleaned_order[k] = str(v)
            
            return cleaned_order
        finally:
            await exchange.close()
            
    except Exception as e:
        logger.error(f"Error creating market sell order: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def fetch_balance(exchange_id: str, user_id: str) -> dict:
    """
    Fetch account balance from an exchange.
    
    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        user_id: User ID for authenticated request
        
    Returns:
        Dictionary containing balance information
    """
    logger.info(f"Executing fetch_balance on {exchange_id} for user {user_id}")
    
    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)
        
        try:
            # Fetch balance
            balance = await exchange.fetch_balance()
            
            # Clean result for serialization
            cleaned_balance = {}
            
            # Extract the core balance info (total, free, used)
            if 'total' in balance:
                cleaned_balance['total'] = balance['total']
            if 'free' in balance:
                cleaned_balance['free'] = balance['free']
            if 'used' in balance:
                cleaned_balance['used'] = balance['used']
                
            # Add individual currency balances
            currencies = {}
            for currency in balance:
                if currency not in ['total', 'free', 'used', 'info'] and isinstance(balance[currency], dict):
                    currencies[currency] = balance[currency]
            
            cleaned_balance['currencies'] = currencies
            
            return cleaned_balance
        finally:
            await exchange.close()
            
    except Exception as e:
        logger.error(f"Error fetching balance: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def fetch_orders(exchange_id: str, symbol: str, user_id: str, 
                      since: int = None, limit: int = None) -> list:
    """
    Fetch orders for a symbol from an exchange.
    
    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        user_id: User ID for authenticated request
        since: Optional timestamp in milliseconds to fetch orders since
        limit: Optional limit on the number of orders to fetch
        
    Returns:
        List of order objects
    """
    if symbol is None:
        return {"error": "Missing required parameter: symbol"}
        
    # Map symbol to exchange-specific format if needed
    mapped_symbol = map_symbol_for_exchange(exchange_id, symbol)
    if mapped_symbol != symbol:
        logger.info(f"Mapped {symbol} to {mapped_symbol} for {exchange_id}")
        
    logger.info(f"Executing fetch_orders for {mapped_symbol} on {exchange_id}")
    
    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)
        
        try:
            # Check if the exchange supports fetching orders
            if not exchange.has['fetchOrders']:
                return {"error": f"Exchange {exchange_id} does not support fetching orders"}
            
            # Fetch orders
            orders = await exchange.fetch_orders(mapped_symbol, since, limit)
            
            # Clean result for serialization
            cleaned_orders = []
            for order in orders:
                cleaned_order = {}
                for k, v in order.items():
                    if k != 'info':  # Skip the raw exchange info
                        if isinstance(v, (int, float, str, bool, list, dict)) or v is None:
                            cleaned_order[k] = v
                        else:
                            # Convert non-serializable types to string
                            cleaned_order[k] = str(v)
                cleaned_orders.append(cleaned_order)
                
            return cleaned_orders
        finally:
            await exchange.close()
            
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def fetch_positions(exchange_id: str, symbol: str = None, user_id: str = None) -> list:
    """
    Fetch current positions from an exchange.
    
    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        symbol: Optional trading pair symbol to filter positions
        user_id: User ID for authenticated request
        
    Returns:
        List of position objects with details like size, unrealized PnL, etc.
    """
    logger.info(f"Executing fetch_positions on {exchange_id}")
    
    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)
        
        try:
            # Check if the exchange supports fetching positions
            if not exchange.has['fetchPositions']:
                return {"error": f"Exchange {exchange_id} does not support fetching positions"}
            
            # Map symbol to exchange-specific format if provided
            mapped_symbol = None
            if symbol:
                mapped_symbol = map_symbol_for_exchange(exchange_id, symbol)
                if mapped_symbol != symbol:
                    logger.info(f"Mapped {symbol} to {mapped_symbol} for {exchange_id}")
            
            # Fetch positions (with or without symbol filter)
            if mapped_symbol:
                positions = await exchange.fetch_positions(mapped_symbol)
            else:
                positions = await exchange.fetch_positions()
            
            # Clean result for serialization
            cleaned_positions = []
            for position in positions:
                cleaned_position = {}
                for k, v in position.items():
                    if k != 'info':  # Skip raw exchange data
                        if isinstance(v, (int, float, str, bool, list, dict)) or v is None:
                            cleaned_position[k] = v
                        else:
                            cleaned_position[k] = str(v)
                cleaned_positions.append(cleaned_position)
            
            return cleaned_positions
        finally:
            await exchange.close()
            
    except Exception as e:
        logger.error(f"Error fetching positions: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def close_position(exchange_id: str, symbol: str, user_id: str, params: dict = None) -> dict:
    """
    Close an open position for a specific symbol.
    
    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        user_id: User ID for authenticated request
        params: Optional additional parameters for the exchange
        
    Returns:
        Dictionary containing the result of closing the position
    """
    if symbol is None:
        return {"error": "Missing required parameter: symbol"}
        
    # Map symbol to exchange-specific format if needed
    mapped_symbol = map_symbol_for_exchange(exchange_id, symbol)
    if mapped_symbol != symbol:
        logger.info(f"Mapped {symbol} to {mapped_symbol} for {exchange_id}")
    
    logger.info(f"Executing close_position for {mapped_symbol} on {exchange_id}")
    
    if params is None:
        params = {}
    
    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)
        
        try:
            # Check if the exchange supports closing positions
            if not exchange.has['closePosition']:
                return {"error": f"Exchange {exchange_id} does not support direct position closing"}
            
            # Close the position
            result = await exchange.close_position(mapped_symbol, params=params)
            
            # Clean result for serialization
            cleaned_result = {}
            for k, v in result.items():
                if k != 'info':  # Skip the raw exchange info
                    if isinstance(v, (int, float, str, bool, list, dict)) or v is None:
                        cleaned_result[k] = v
                    else:
                        # Convert non-serializable types to string
                        cleaned_result[k] = str(v)
            
            return cleaned_result
        finally:
            await exchange.close()
            
    except Exception as e:
        logger.error(f"Error closing position: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def set_leverage(exchange_id: str, leverage: int, symbol: str, user_id: str, params: dict = None) -> dict:
    """
    Set leverage for a specific trading pair symbol.
    
    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        leverage: Leverage value (e.g., 2, 10, 50, 100)
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        user_id: User ID for authenticated request
        params: Optional additional parameters for the exchange
        
    Returns:
        Dictionary containing the result of setting leverage
    """
    if leverage is None:
        return {"error": "Missing required parameter: leverage"}
        
    if symbol is None:
        return {"error": "Missing required parameter: symbol"}
        
    # Map symbol to exchange-specific format if needed
    mapped_symbol = map_symbol_for_exchange(exchange_id, symbol)
    if mapped_symbol != symbol:
        logger.info(f"Mapped {symbol} to {mapped_symbol} for {exchange_id}")
    
    logger.info(f"Executing set_leverage for {mapped_symbol} on {exchange_id}, leverage={leverage}")
    
    if params is None:
        params = {}
    
    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)
        
        try:
            # Check if the exchange supports setting leverage
            if not exchange.has['setLeverage']:
                return {"error": f"Exchange {exchange_id} does not support setting leverage"}
            
            # Set leverage
            result = await exchange.set_leverage(leverage, mapped_symbol, params=params)
            
            # Clean result for serialization
            if isinstance(result, dict):
                cleaned_result = {}
                for k, v in result.items():
                    if k != 'info':  # Skip the raw exchange info
                        if isinstance(v, (int, float, str, bool, list, dict)) or v is None:
                            cleaned_result[k] = v
                        else:
                            # Convert non-serializable types to string
                            cleaned_result[k] = str(v)
                return cleaned_result
            else:
                # Some exchanges may return a boolean or other type
                return {"success": True, "leverage": leverage, "symbol": symbol, "result": str(result)}
        finally:
            await exchange.close()
            
    except Exception as e:
        logger.error(f"Error setting leverage: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def create_limit_order(exchange_id: str, symbol: str, side: str, amount: float, price: float, user_id: str, params: dict = None) -> dict:
    """
    Create a limit order on an exchange.
    
    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        side: Order side ('buy' or 'sell')
        amount: Order quantity
        price: Order price
        user_id: User ID for authenticated request
        params: Optional additional parameters for the exchange
        
    Returns:
        Dictionary containing order details
    """
    if symbol is None:
        return {"error": "Missing required parameter: symbol"}
    
    if side is None:
        return {"error": "Missing required parameter: side"}
    
    if side not in ['buy', 'sell']:
        return {"error": "Invalid side parameter: must be 'buy' or 'sell'"}
        
    if amount is None:
        return {"error": "Missing required parameter: amount"}
        
    if price is None:
        return {"error": "Missing required parameter: price - use create_market_buy_order or create_market_sell_order for market orders"}
        
    # Map symbol to exchange-specific format if needed
    mapped_symbol = map_symbol_for_exchange(exchange_id, symbol)
    if mapped_symbol != symbol:
        logger.info(f"Mapped {symbol} to {mapped_symbol} for {exchange_id}")
    
    logger.info(f"Executing create_limit_order for {mapped_symbol} on {exchange_id}, side={side}, amount={amount}, price={price}")
    
    if params is None:
        params = {}
    
    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)
        
        try:
            # Check if the exchange supports creating limit orders
            if not exchange.has['createLimitOrder']:
                return {"error": f"Exchange {exchange_id} does not support creating limit orders directly"}
            
            # Create the order
            order = await exchange.create_limit_order(mapped_symbol, side, amount, price, params)
            
            # Clean result for serialization
            cleaned_order = {}
            for k, v in order.items():
                if k != 'info':  # Skip the raw exchange info
                    if isinstance(v, (int, float, str, bool, list, dict)) or v is None:
                        cleaned_order[k] = v
                    else:
                        # Convert non-serializable types to string
                        cleaned_order[k] = str(v)
            
            return cleaned_order
        finally:
            await exchange.close()
            
    except Exception as e:
        logger.error(f"Error creating limit order: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def create_stop_order(exchange_id: str, symbol: str, side: str, amount: float, price: float, 
                           user_id: str, params: dict = None) -> dict:
    """
    Create a stop order on an exchange.
    
    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        side: Order side ('buy' or 'sell')
        amount: Order quantity
        price: Trigger price
        user_id: User ID for authenticated request
        params: Optional additional parameters for the exchange
        
    Returns:
        Dictionary containing order details
    """
    if symbol is None:
        return {"error": "Missing required parameter: symbol"}
    
    if side is None:
        return {"error": "Missing required parameter: side"}
    
    if side not in ['buy', 'sell']:
        return {"error": "Invalid side parameter: must be 'buy' or 'sell'"}
        
    if amount is None:
        return {"error": "Missing required parameter: amount"}
        
    if price is None:
        return {"error": "Missing required parameter: price"}
        
    # Map symbol to exchange-specific format if needed
    mapped_symbol = map_symbol_for_exchange(exchange_id, symbol)
    if mapped_symbol != symbol:
        logger.info(f"Mapped {symbol} to {mapped_symbol} for {exchange_id}")
    
    logger.info(f"Executing create_stop_order for {mapped_symbol} on {exchange_id}, side={side}, amount={amount}, price={price}")
    
    if params is None:
        params = {}
    
    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)
        
        try:
            # Check if the exchange supports creating stop orders
            if not exchange.has['createStopOrder']:
                return {"error": f"Exchange {exchange_id} does not support creating stop orders directly"}
            
            # Create the stop order
            order = await exchange.create_stop_order(mapped_symbol, side, amount, price, params)
            
            # Clean result for serialization
            cleaned_order = {}
            for k, v in order.items():
                if k != 'info':  # Skip the raw exchange info
                    if isinstance(v, (int, float, str, bool, list, dict)) or v is None:
                        cleaned_order[k] = v
                    else:
                        # Convert non-serializable types to string
                        cleaned_order[k] = str(v)
            
            return cleaned_order
        finally:
            await exchange.close()
            
    except Exception as e:
        logger.error(f"Error creating stop order: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def create_reduce_only_order(exchange_id: str, symbol: str, type: str, side: str, 
                                   amount: float, price: float = None, user_id: str = None, 
                                   params: dict = None) -> dict:
    """
    Create a reduce-only order on an exchange, which will only reduce an existing position.
    
    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        type: Order type ('limit' or 'market')
        side: Order side ('buy' or 'sell')
        amount: Order quantity
        price: Order price (required for limit orders)
        user_id: User ID for authenticated request
        params: Optional additional parameters for the exchange
        
    Returns:
        Dictionary containing order details
    """
    if symbol is None:
        return {"error": "Missing required parameter: symbol"}
    
    if type is None:
        return {"error": "Missing required parameter: type"}
    
    if type not in ['limit', 'market']:
        return {"error": "Invalid type parameter: must be 'limit' or 'market'"}
    
    if side is None:
        return {"error": "Missing required parameter: side"}
    
    if side not in ['buy', 'sell']:
        return {"error": "Invalid side parameter: must be 'buy' or 'sell'"}
        
    if amount is None:
        return {"error": "Missing required parameter: amount"}
        
    if type == 'limit' and price is None:
        return {"error": "Price is required for limit orders"}
        
    # Map symbol to exchange-specific format if needed
    mapped_symbol = map_symbol_for_exchange(exchange_id, symbol)
    if mapped_symbol != symbol:
        logger.info(f"Mapped {symbol} to {mapped_symbol} for {exchange_id}")
    
    logger.info(f"Executing create_reduce_only_order for {mapped_symbol} on {exchange_id}, type={type}, side={side}, amount={amount}")
    
    if params is None:
        params = {}
    
    # Add the reduce-only flag
    params['reduceOnly'] = True
    
    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)
        
        try:
            # Check if the exchange supports creating reduce-only orders
            if not exchange.has['createReduceOnlyOrder']:
                return {"error": f"Exchange {exchange_id} does not support creating reduce-only orders directly"}
            
            # Create the reduce-only order based on the order type
            if type == 'limit':
                order = await exchange.create_limit_order(mapped_symbol, side, amount, price, params)
            else:  # market order
                if side == 'buy':
                    order = await exchange.create_market_buy_order(mapped_symbol, amount, params)
                else:  # sell
                    order = await exchange.create_market_sell_order(mapped_symbol, amount, params)
            
            # Clean result for serialization
            cleaned_order = {}
            for k, v in order.items():
                if k != 'info':  # Skip the raw exchange info
                    if isinstance(v, (int, float, str, bool, list, dict)) or v is None:
                        cleaned_order[k] = v
                    else:
                        # Convert non-serializable types to string
                        cleaned_order[k] = str(v)
            
            return cleaned_order
        finally:
            await exchange.close()
            
    except Exception as e:
        logger.error(f"Error creating reduce-only order: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def cancel_order(exchange_id: str, id: str, symbol: str, user_id: str, params: dict = None) -> dict:
    """
    Cancel an existing order on an exchange.
    
    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        id: Order ID to cancel
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        user_id: User ID for authenticated request
        params: Optional additional parameters for the exchange
        
    Returns:
        Dictionary containing the result of canceling the order
    """
    if id is None:
        return {"error": "Missing required parameter: id"}
        
    if symbol is None:
        return {"error": "Missing required parameter: symbol"}
        
    # Map symbol to exchange-specific format if needed
    mapped_symbol = map_symbol_for_exchange(exchange_id, symbol)
    if mapped_symbol != symbol:
        logger.info(f"Mapped {symbol} to {mapped_symbol} for {exchange_id}")
    
    logger.info(f"Executing cancel_order for order ID {id} on {exchange_id}, symbol={mapped_symbol}")
    
    if params is None:
        params = {}
    
    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)
        
        try:
            # Check if the exchange supports canceling orders
            if not exchange.has['cancelOrder']:
                return {"error": f"Exchange {exchange_id} does not support canceling orders"}
            
            # Cancel the order
            result = await exchange.cancel_order(id, mapped_symbol, params)
            
            # Clean result for serialization
            cleaned_result = {}
            for k, v in result.items():
                if k != 'info':  # Skip the raw exchange info
                    if isinstance(v, (int, float, str, bool, list, dict)) or v is None:
                        cleaned_result[k] = v
                    else:
                        # Convert non-serializable types to string
                        cleaned_result[k] = str(v)
            
            return cleaned_result
        finally:
            await exchange.close()
            
    except Exception as e:
        logger.error(f"Error canceling order: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def fetch_open_orders(exchange_id: str, symbol: str = None, since: int = None, 
                            limit: int = None, user_id: str = None) -> list:
    """
    Fetch open orders from an exchange.
    
    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        symbol: Optional trading pair symbol to filter orders
        since: Optional timestamp in milliseconds to fetch orders since
        limit: Optional limit on the number of orders to fetch
        user_id: User ID for authenticated request
        
    Returns:
        List of open order objects
    """
    logger.info(f"Executing fetch_open_orders on {exchange_id}")
    
    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)
        
        try:
            # Check if the exchange supports fetching open orders
            if not exchange.has['fetchOpenOrders']:
                return {"error": f"Exchange {exchange_id} does not support fetching open orders"}
            
            # Map symbol to exchange-specific format if provided
            mapped_symbol = None
            if symbol:
                mapped_symbol = map_symbol_for_exchange(exchange_id, symbol)
                if mapped_symbol != symbol:
                    logger.info(f"Mapped {symbol} to {mapped_symbol} for {exchange_id}")
            
            # Fetch open orders
            orders = await exchange.fetch_open_orders(mapped_symbol, since, limit)
            
            # Clean result for serialization
            cleaned_orders = []
            for order in orders:
                cleaned_order = {}
                for k, v in order.items():
                    if k != 'info':  # Skip the raw exchange info
                        if isinstance(v, (int, float, str, bool, list, dict)) or v is None:
                            cleaned_order[k] = v
                        else:
                            # Convert non-serializable types to string
                            cleaned_order[k] = str(v)
                cleaned_orders.append(cleaned_order)
            
            return cleaned_orders
        finally:
            await exchange.close()
            
    except Exception as e:
        logger.error(f"Error fetching open orders: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def edit_order(exchange_id: str, id: str, symbol: str, type: str = None, 
                     side: str = None, amount: float = None, price: float = None, 
                     user_id: str = None, params: dict = None) -> dict:
    """
    Edit an existing order on an exchange.
    
    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        id: Order ID to edit
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        type: Optional new order type
        side: Optional new order side ('buy' or 'sell')
        amount: Optional new order amount
        price: Optional new order price
        user_id: User ID for authenticated request
        params: Optional additional parameters for the exchange
        
    Returns:
        Dictionary containing the updated order details
    """
    if id is None:
        return {"error": "Missing required parameter: id"}
        
    if symbol is None:
        return {"error": "Missing required parameter: symbol"}
        
    # At least one parameter to edit must be provided
    if amount is None and price is None and not params:
        return {"error": "At least one parameter to edit (amount, price, or params) must be provided"}
    
    # Map symbol to exchange-specific format if needed
    mapped_symbol = map_symbol_for_exchange(exchange_id, symbol)
    if mapped_symbol != symbol:
        logger.info(f"Mapped {symbol} to {mapped_symbol} for {exchange_id}")
    
    logger.info(f"Executing edit_order for order ID {id} on {exchange_id}, symbol={mapped_symbol}")
    
    if params is None:
        params = {}
    
    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)
        
        try:
            # Check if the exchange supports editing orders
            if not exchange.has['editOrder']:
                return {"error": f"Exchange {exchange_id} does not support editing orders"}
            
            # Edit the order
            order = await exchange.edit_order(id, mapped_symbol, type, side, amount, price, params)
            
            # Clean result for serialization
            cleaned_order = {}
            for k, v in order.items():
                if k != 'info':  # Skip the raw exchange info
                    if isinstance(v, (int, float, str, bool, list, dict)) or v is None:
                        cleaned_order[k] = v
                    else:
                        # Convert non-serializable types to string
                        cleaned_order[k] = str(v)
            
            return cleaned_order
        finally:
            await exchange.close()
            
    except Exception as e:
        logger.error(f"Error editing order: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    logger.info("Starting CCXTExchange MCP server")
    
    # Log startup information for debugging
    logger.info(f"API key exists: {bool(os.environ.get('EXCHANGE_API', ''))}")
    logger.info(f"Secret exists: {bool(os.environ.get('EXCHANGE_SECRET', ''))}")
    logger.info(f"Exchange name: {os.environ.get('EXCHANGE_NAME', 'Not set')}")
    
    # Log available tools for debugging
    registered_tools = [tool.__name__ for tool in getattr(mcp, '_tools', [])]
    logger.info(f"Registered tools: {registered_tools}")
    
    # Run the server
    mcp.run(transport="stdio")