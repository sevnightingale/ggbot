#!/usr/bin/env python
"""
Simple test to list and save available tools from CCXT MCP for BitMEX.
This script helps understand what capabilities are available through the MCP interface.
"""

import os
import sys
import json
import asyncio
import uuid
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.common.logger import logger
from core.mcp.ccxt import CCXTMCPClient
from trading.exchanges.ccxt_mcp import CCXTMCPAdapter
from trading.engine.model.config import EngineConfig

# Configure logging
import logging
logger.configure(handlers=[{"sink": sys.stdout, "level": logging.INFO}])

async def main():
    """Retrieve and save available tools from CCXT MCP for BitMEX."""
    logger.info("Starting tool discovery for CCXT MCP")
    
    # Create unique user ID for testing
    user_id = str(uuid.uuid4())
    exchange_id = "bitmex"
    
    # Create config with server path
    server_path = str(Path(__file__).parent.parent / "core" / "mcp" / "servers" / "ccxt_mcp_server.py")
    config = EngineConfig(
        llm={
            "model": "gpt-4.1",
            "system_prompt": "You are an expert trading assistant"
        },
        validation={
            "max_leverage": 10,
            "max_position_pct": 0.05
        },
        execution={
            "polling_interval": 5,
            "max_retries": 2
        },
        default_exchange="bitmex",
        use_testnet=True,
        server_path=server_path,
        credentials={
            "apiKey": os.environ.get("EXCHANGE_API"),
            "secret": os.environ.get("EXCHANGE_SECRET")
        }
    )
    
    # Create MCP client
    logger.info(f"Using server path: {config.server_path}")
    
    mcp_client = CCXTMCPClient(
        exchange_id=exchange_id,
        user_id=user_id,
        use_local_server=True,
        server_path=config.server_path
    )
    
    # Connect to MCP server
    logger.info("Connecting to MCP server...")
    await mcp_client.connect()
    logger.info("MCP client connected successfully")
    
    # Create CCXT adapter
    logger.info("Creating CCXT adapter...")
    adapter = CCXTMCPAdapter(
        exchange_id=exchange_id,
        user_id=user_id,
        config=config.model_dump()
    )
    adapter.mcp_client = mcp_client
    adapter.connected = True
    
    try:
        # Get list of available tools
        logger.info("Retrieving available tools from CCXT MCP...")
        tools = await adapter.get_tools_schema()
        
        # Extract tool names and details
        tool_names = [tool["name"] for tool in tools]
        logger.info(f"Found {len(tool_names)} available tools:")
        for name in tool_names:
            logger.info(f"  - {name}")
        
        # Save detailed tool information
        output_path = Path(__file__).parent / "ccxt_mcp_tools.json"
        with open(output_path, "w") as f:
            json.dump(tools, f, indent=2)
        logger.info(f"Saved detailed tool information to {output_path}")
        
        # Save just the tool names for quick reference
        names_path = Path(__file__).parent / "ccxt_mcp_tool_names.txt"
        with open(names_path, "w") as f:
            for name in sorted(tool_names):
                f.write(f"{name}\n")
        logger.info(f"Saved tool names to {names_path}")
        
    finally:
        # Clean up
        if mcp_client and mcp_client.is_connected:
            logger.info("Disconnecting MCP client...")
            await mcp_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())