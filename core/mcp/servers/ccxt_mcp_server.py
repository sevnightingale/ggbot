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

# Import local modules if available
try:
    from core.common.db import get_connection
    from core.config.config_main import get_user_exchange_credentials
    STANDALONE_MODE = False
    logger.info("Imported ggbot modules. Running in integrated mode.")
except ImportError:
    logger.warning("Failed to import ggbot modules. Running in standalone mode.")
    STANDALONE_MODE = True
    # Define placeholder functions for standalone testing
    async def get_connection():
        return None
        
    async def get_user_exchange_credentials(user_id, exchange_id, conn=None):
        # Return test credentials from environment variables in standalone mode
        api_key = os.environ.get("EXCHANGE_API", "")
        secret = os.environ.get("EXCHANGE_SECRET", "")
        password = os.environ.get("EXCHANGE_PASSWORD", "")

        if not api_key or not secret:
            logger.warning(f"Missing API credentials for {exchange_id} in environment variables")
        else:
            logger.info(f"Found API credentials for {exchange_id} in environment variables")

        return {
            "apiKey": api_key,
            "secret": secret,
            "password": password,
            "test": True  # Always use testnet in standalone mode
        }

# Create MCP server
mcp = FastMCP("CCXTExchange")

# Trading pair mapping for different exchanges
EXCHANGE_SYMBOL_MAP = {
    'bitmex': {
        'BTC/USD': 'XBT/USD',
        'BTC/USDT': 'XBT/USDT',
        'ETH/USD': 'ETH/USDT:USDT'  # BitMEX uses different format for ETH
    }
}

def map_symbol_for_exchange(exchange_id, symbol):
    """Map a standard symbol to exchange-specific format."""
    exchange_map = EXCHANGE_SYMBOL_MAP.get(exchange_id.lower(), {})
    return exchange_map.get(symbol, symbol)

async def get_exchange_instance(exchange_id, user_id=None):
    """Get a CCXT exchange instance with appropriate credentials."""
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
        
        # Get credentials (simplified approach)
        if STANDALONE_MODE:
            # Standalone mode - use environment variables or fallback
            api_key = env_api or "REDACTED_EXCHANGE_API_KEY"
            secret = env_secret or "REDACTED_EXCHANGE_SECRET"
            
            credentials = {
                "apiKey": api_key,
                "secret": secret,
                "enableRateLimit": True,
                "test": True  # Always use testnet for safety
            }
        else:
            # Integrated mode - try to get from user credentials
            try:
                if user_id is not None:
                    credentials = await get_user_exchange_credentials(user_id, exchange_id)
                else:
                    # Fallback to environment variables
                    api_key = env_api
                    secret = env_secret
                    credentials = {
                        "apiKey": api_key,
                        "secret": secret,
                        "enableRateLimit": True,
                        "test": True
                    }
            except Exception as e:
                logger.warning(f"Failed to get credentials: {str(e)}")
                # Fallback to environment variables
                api_key = env_api
                secret = env_secret
                if not api_key or not secret:
                    logger.error("No API credentials found")
                    raise ValueError("No API credentials available")
                credentials = {
                    "apiKey": api_key,
                    "secret": secret,
                    "enableRateLimit": True,
                    "test": True
                }
        
        # Log the credentials (without the actual secret)
        logger.debug(f"Creating exchange with credentials: apiKey={credentials.get('apiKey')[:4]}..., secret=****")
        
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
async def fetch_markets(exchange_id: str = None, exchangeId: str = None, user_id: str = None) -> list:
    """
    Fetch markets available on an exchange.

    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        exchangeId: Legacy parameter for exchange ID (deprecated, use exchange_id instead)
        user_id: Optional user ID for authenticated requests

    Returns:
        List of market data
    """
    # Handle legacy camelCase parameter
    if exchange_id is None and exchangeId is not None:
        exchange_id = exchangeId

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
            for market in markets[:20]:  # Limit to 20 markets for manageable output
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
                      exchangeId: str = None, user_id: str = None) -> dict:
    """
    Fetch current ticker data for a symbol from an exchange.

    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        exchangeId: Legacy parameter for exchange ID (deprecated, use exchange_id instead)
        user_id: Optional user ID for authenticated requests

    Returns:
        Dictionary containing ticker data
    """
    # Handle legacy camelCase parameter
    if exchange_id is None and exchangeId is not None:
        exchange_id = exchangeId

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
async def fetch_ohlcv(exchange_id: str = None, symbol: str = None, exchangeId: str = None,
                    timeframe: str = '1h', since: int = None, limit: int = None,
                    user_id: str = None) -> list:
    """
    Fetch OHLCV (candle) data for a symbol from an exchange.

    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        exchangeId: Legacy parameter for exchange ID (deprecated, use exchange_id instead)
        timeframe: Timeframe (e.g., '1m', '5m', '1h', '1d')
        since: Optional timestamp in milliseconds to fetch data since
        limit: Optional limit on the number of candles to fetch
        user_id: Optional user ID for authenticated requests

    Returns:
        List of OHLCV candles [timestamp, open, high, low, close, volume]
    """
    # Handle legacy camelCase parameter
    if exchange_id is None and exchangeId is not None:
        exchange_id = exchangeId

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
                          exchangeId: str = None, limit: int = None,
                          user_id: str = None) -> dict:
    """
    Fetch order book for a symbol from an exchange.

    Args:
        exchange_id: ID of the exchange (e.g., 'binance', 'bitmex')
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        exchangeId: Legacy parameter for exchange ID (deprecated, use exchange_id instead)
        limit: Optional limit on the number of orders to fetch
        user_id: Optional user ID for authenticated requests

    Returns:
        Dictionary containing order book data
    """
    # Handle legacy camelCase parameter
    if exchange_id is None and exchangeId is not None:
        exchange_id = exchangeId

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
                                 exchangeId: str = None, user_id: str = None, params: dict = None) -> dict:
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
    # Handle legacy camelCase parameter
    if exchange_id is None and exchangeId is not None:
        exchange_id = exchangeId
        
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