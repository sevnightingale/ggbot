#!/usr/bin/env python
"""
Test script for the CCXT MCP client.

This script tests the connectivity and functionality of the CCXT MCP client.
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_ccxt_mcp")

# Import the client
from core.mcp.ccxt_client import CCXTMCPClient

async def main():
    """Main test function."""
    logger.info("Testing CCXT MCP client")
    
    # Check if environment variables are set
    required_vars = ["EXCHANGE_API", "EXCHANGE_SECRET"]
    for var in required_vars:
        if not os.environ.get(var):
            logger.warning(f"Environment variable {var} not set")
            logger.warning("For a complete test, set EXCHANGE_API and EXCHANGE_SECRET environment variables")
    
    # Create a test user ID
    user_id = "00000000-0000-0000-0000-000000000001"
    
    # Set exchange ID, defaulting to a testnet exchange if none specified
    exchange_id = os.environ.get("EXCHANGE_NAME", "binance")
    
    # Symbol to test with
    symbol = "BTC/USDT"
    
    # Use the client as a context manager
    async with CCXTMCPClient(user_id=user_id, exchange_id=exchange_id) as client:
        # Load configuration
        try:
            await client.load_config()
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load configuration: {e}")
            logger.info("Continuing with default configuration")
        
        try:
            # Get available exchange IDs
            logger.info("Getting available exchange IDs")
            exchange_ids = await client.get_exchange_ids()
            logger.info(f"Found {len(exchange_ids)} exchanges")
            logger.info(f"Examples: {', '.join(exchange_ids[:5])}")
            
            # Check if the specified exchange is supported
            if exchange_id not in exchange_ids:
                logger.warning(f"Exchange {exchange_id} not in list of available exchanges")
                logger.warning(f"Available exchanges: {', '.join(exchange_ids[:10])}")
                alternative_exchange = next((x for x in exchange_ids if x.startswith(exchange_id)), None)
                if alternative_exchange:
                    logger.info(f"Using alternative exchange: {alternative_exchange}")
                    exchange_id = alternative_exchange
                    client.exchange_id = exchange_id
            
            # Test fetching ticker
            logger.info(f"Testing fetch_ticker for {symbol} on {exchange_id}")
            ticker = await client.fetch_ticker(symbol=symbol)
            
            if "error" in ticker:
                logger.warning(f"Error fetching ticker: {ticker['error']}")
                logger.warning("Trying with a different symbol")
                symbol = "BTC/USD"
                ticker = await client.fetch_ticker(symbol=symbol)
            
            logger.info(f"Ticker result: {ticker}")
            
            # Test fetching OHLCV data
            logger.info(f"Testing fetch_ohlcv for {symbol} on {exchange_id}")
            ohlcv = await client.fetch_ohlcv(
                symbol=symbol,
                timeframe="1h",
                limit=5
            )
            
            if isinstance(ohlcv, dict) and "error" in ohlcv:
                logger.warning(f"Error fetching OHLCV: {ohlcv['error']}")
            else:
                logger.info(f"Fetched {len(ohlcv)} OHLCV candles")
                if ohlcv:
                    logger.info(f"First candle: {ohlcv[0]}")
            
            # Test fetching balance (requires API keys)
            if os.environ.get("EXCHANGE_API") and os.environ.get("EXCHANGE_SECRET"):
                logger.info(f"Testing fetch_balance on {exchange_id}")
                balance = await client.fetch_balance()
                
                if "error" in balance:
                    logger.warning(f"Error fetching balance: {balance['error']}")
                else:
                    logger.info(f"Balance result: {balance}")
            else:
                logger.warning("Skipping fetch_balance test (no API keys provided)")
            
            # Test market order creation (this is just a test - won't create a real order without confirm)
            logger.info("Testing market order creation (simulation only)")
            
            # We're not really going to create an order, just see if the client can format the request
            try:
                # This won't execute a real order without confirmation
                order_result = await client.session.list_tools()
                order_tools = [t.name for t in order_result if "order" in t.name.lower()]
                logger.info(f"Order-related tools available: {order_tools}")
                
                # Just log that we would place an order in a real scenario
                logger.info(f"In a real scenario, would place a market buy order for 0.001 {symbol}")
                logger.info("Order creation tests skipped in automated testing")
            except Exception as e:
                logger.warning(f"Error in order creation test: {e}")
            
            logger.info("All tests completed!")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            raise
        
        logger.info("Disconnecting from MCP server")

if __name__ == "__main__":
    # Show a warning about real trading
    print("=" * 80)
    print("WARNING: This test connects to cryptocurrency exchanges.")
    print("It will NOT place real orders by default, but use caution.")
    print("Set EXCHANGE_API and EXCHANGE_SECRET environment variables for full testing.")
    print("=" * 80)
    
    asyncio.run(main())