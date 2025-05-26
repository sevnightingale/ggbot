#!/usr/bin/env python
"""
Simple script to check available tools from the CCXT MCP server.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.common.logger import logger
from core.mcp.ccxt import CCXTMCPClient

async def main():
    # Setup environment
    os.environ["TESTNET"] = "1"
    os.environ["EXCHANGE_NAME"] = "bitmex"
    
    # Create client
    client = CCXTMCPClient(
        exchange_id="bitmex",
        user_id="test_user",
        use_local_server=True,
        server_path=str(Path(__file__).parent.parent / "core" / "mcp" / "servers" / "ccxt_mcp_server.py")
    )
    
    try:
        # Connect
        print("Connecting to MCP server...")
        await client.connect()
        print("Connected successfully")
        
        # Get tools
        print("Getting tools...")
        tools = await client.session.get_tools()
        print(f"Retrieved {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}")
        
    finally:
        # Clean up
        if client.is_connected:
            print("Disconnecting...")
            await client.disconnect()
            print("Disconnected")

if __name__ == "__main__":
    asyncio.run(main())