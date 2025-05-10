#!/usr/bin/env python
"""
Minimal test script for MCP connectivity.

This script tests just the basic MCP connection without additional complexity.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import necessary components
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp import ClientSession

async def test_mcp_connection():
    """Test a direct connection to the MCP using the SDK directly."""
    print("Testing minimal MCP connection...")
    
    # Set up parameters
    script_path = str(Path(__file__).parent.parent / "core" / "mcp" / "servers" / "crypto-indicators-mcp" / "index.js")
    print(f"Script path: {script_path}")
    
    params = StdioServerParameters(
        command="node",
        args=[script_path],
        env={"EXCHANGE_NAME": "binance"}
    )
    
    try:
        print("Connecting to MCP server...")
        async with stdio_client(params) as streams:
            print("Got streams, creating session...")
            async with ClientSession(streams[0], streams[1]) as session:
                print("Initializing session...")
                await session.initialize()
                print("Session initialized successfully!")
                
                # Try to get tools
                print("Getting available tools...")
                tools = await session.list_tools()
                print(f"Got tools object: {type(tools)}")
                # Access the tools correctly based on the result type
                try:
                    if hasattr(tools, 'tools'):
                        # Try to access as attribute
                        tool_list = tools.tools
                        print(f"Found {len(tool_list)} tools")
                        for i, tool in enumerate(tool_list[:5]):  # Show first 5 tools
                            print(f"Tool {i+1}: {tool.name if hasattr(tool, 'name') else tool.get('name', 'Unknown')}")
                    else:
                        # Try to iterate
                        print(f"Got a {type(tools)} - trying to iterate...")
                        count = 0
                        for i, tool in enumerate(tools):
                            count += 1
                            if i < 5:  # Show first 5 tools
                                print(f"Tool {i+1}: {tool.name if hasattr(tool, 'name') else tool.get('name', 'Unknown')}")
                        print(f"Found {count} tools") 
                except Exception as e:
                    print(f"Error accessing tools: {type(e).__name__}: {str(e)}")
                    print(f"Tools object details: {dir(tools)}")
                    # Just try to print the raw object
                    print(f"Raw tools data: {tools}")
                
                print("Connection test succeeded!")
                return True
    except Exception as e:
        print(f"Connection failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function."""
    success = await test_mcp_connection()
    if success:
        print("\nTest PASSED: MCP connection works!")
    else:
        print("\nTest FAILED: Could not connect to MCP.")

if __name__ == "__main__":
    asyncio.run(main())