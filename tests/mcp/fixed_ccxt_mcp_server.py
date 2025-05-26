#!/usr/bin/env python
"""
Simplified CCXT MCP Server for debugging integration issues.

This version removes complex credential management and directly injects 
credentials from environment variables, bypassing the file-based config.
"""

import logging
import sys
import os
import json
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from mcp.server.fastmcp import FastMCP, Context

# Setup logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ccxt_mcp_server")

# Create MCP server
mcp = FastMCP("CCXTExchange")

async def get_exchange_instance(exchange_id, user_id=None):
    """Get a CCXT exchange instance with credentials from environment variables."""
    try:
        # Dynamically import CCXT
        import ccxt.async_support as ccxt

        # Log environment variables for debugging
        env_api = os.environ.get("EXCHANGE_API", "")
        env_secret = os.environ.get("EXCHANGE_SECRET", "")
        env_exchange = os.environ.get("EXCHANGE_NAME", "")
        
        logger.debug(f"Environment variables: EXCHANGE_NAME={env_exchange}, " 
                    f"API key exists: {bool(env_api)}, Secret exists: {bool(env_secret)}")

        # Hardcoded fallback values for testing BitMEX testnet
        api_key = env_api or "REDACTED_EXCHANGE_API_KEY"
        secret = env_secret or "REDACTED_EXCHANGE_SECRET"
        
        # Get the exchange class
        if not hasattr(ccxt, exchange_id):
            raise ValueError(f"Exchange {exchange_id} not supported by CCXT")

        exchange_class = getattr(ccxt, exchange_id)
        
        # Create the exchange instance with direct credentials
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
async def fetch_ticker(exchange_id: str = None, symbol: str = None, exchangeId: str = None, user_id: str = None) -> dict:
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

    logger.info(f"Executing fetch_ticker for {symbol} on {exchange_id}")

    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)

        try:
            ticker = await exchange.fetch_ticker(symbol)

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

    logger.info(f"Executing fetch_order_book for {symbol} on {exchange_id}")

    try:
        exchange = await get_exchange_instance(exchange_id, user_id=user_id)

        try:
            # Fetch order book
            order_book = await exchange.fetch_order_book(symbol, limit)

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

if __name__ == "__main__":
    logger.info("Starting CCXTExchange MCP server with simplified credential handling")
    
    # Log startup information for debugging
    logger.info(f"API key exists: {bool(os.environ.get('EXCHANGE_API', ''))}")
    logger.info(f"Secret exists: {bool(os.environ.get('EXCHANGE_SECRET', ''))}")
    logger.info(f"Exchange name: {os.environ.get('EXCHANGE_NAME', 'Not set')}")
    
    # Log available tools for debugging
    registered_tools = [tool.__name__ for tool in getattr(mcp, '_tools', [])]
    logger.info(f"Registered tools: {registered_tools}")
    
    # Run the server
    mcp.run(transport="stdio")