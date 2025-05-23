#!/usr/bin/env python
"""
Simple test to check if we can access BitMEX testnet through our MCP client.
This test is more focused and limited than the full test_execution_service.py.
"""

import os
import sys
import asyncio
import uuid
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment variables
os.environ["TESTNET"] = "1"
os.environ["EXCHANGE_NAME"] = "bitmex"

from core.common.logger import logger
from core.mcp.ccxt import CCXTMCPClient
from trading.exchanges.ccxt_mcp import CCXTMCPAdapter

# Configure basic logging
import logging
logger.configure(handlers=[{"sink": sys.stdout, "level": logging.INFO}])

async def test_bitmex_testnet():
    """Test basic connectivity and operations with BitMEX testnet."""
    logger.info("Starting BitMEX testnet check")
    
    user_id = str(uuid.uuid4())
    exchange_id = "bitmex"
    
    # Create MCP client
    server_path = str(Path(__file__).parent.parent / "core" / "mcp" / "servers" / "ccxt_mcp_server.py")
    logger.info(f"Using server path: {server_path}")
    
    mcp_client = CCXTMCPClient(
        exchange_id=exchange_id,
        user_id=user_id,
        use_local_server=True,
        server_path=server_path
    )
    
    # Connect to MCP server
    logger.info("Connecting to MCP server...")
    await mcp_client.connect()
    
    # Get list of available tools
    logger.info("Getting available tools...")
    tools = await mcp_client.session.get_tools()
    logger.info(f"Got {len(tools)} tools")
    
    # Create CCXT adapter
    logger.info("Creating CCXT adapter...")
    adapter = CCXTMCPAdapter(
        exchange_id=exchange_id,
        user_id=user_id,
        config={"use_testnet": True}
    )
    
    # Manually set the MCP client (bypassing connect method)
    adapter.mcp_client = mcp_client
    adapter.connected = True
    
    # Try to fetch markets
    logger.info("Fetching markets...")
    markets = await adapter.fetch_markets()
    logger.info(f"Fetched {len(markets)} markets")
    
    # Try to fetch ticker for BTC/USD
    logger.info("Fetching BTC/USD ticker...")
    symbol = "BTC/USD:BTC"  # BitMEX symbol format
    ticker = await adapter.fetch_ticker(symbol)
    logger.info(f"Ticker for {symbol}: {ticker}")
    
    # Check if fetch_positions is supported
    logger.info("Checking if fetch_positions is supported...")
    try:
        positions = await adapter.fetch_positions()
        logger.info(f"Fetched {len(positions)} positions")
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
    
    # Disconnect
    logger.info("Disconnecting...")
    await mcp_client.disconnect()
    
    logger.info("BitMEX testnet check completed")

if __name__ == "__main__":
    asyncio.run(test_bitmex_testnet())