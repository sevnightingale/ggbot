#!/usr/bin/env python
"""Script to list available tools in the CCXT MCP server."""

import asyncio
import json
from pathlib import Path

# Add project root to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp import ClientSession

async def print_tools():
    """Connect to CCXT MCP server and list available tools."""
    params = StdioServerParameters(
        command='ccxt-mcp',
        args=['--config', '/home/sev/ggbot/core/config/ccxt-accounts.json']
    )
    
    async with stdio_client(params) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            try:
                tools = await session.list_tools()
                
                # Handle different possible return types
                print(f"Tools object type: {type(tools)}")
                print(f"Dir(tools): {dir(tools)}")
                
                if hasattr(tools, 'tools'):
                    # It might be a ListToolsResult with a tools attribute
                    tool_list = tools.tools
                    print(f"Found {len(tool_list)} tools:")
                    for i, tool in enumerate(tool_list):
                        if hasattr(tool, 'name'):
                            print(f"{i+1}. {tool.name}")
                        else:
                            print(f"{i+1}. {tool}")
                elif hasattr(tools, '__iter__'):
                    # It might be directly iterable
                    print("Iterating through tools:")
                    i = 1
                    for tool in tools:
                        if hasattr(tool, 'name'):
                            print(f"{i}. {tool.name}")
                        else:
                            print(f"{i}. {tool}")
                        i += 1
                else:
                    # Just print what we got
                    print(f"Tools: {tools}")
                
            except Exception as e:
                print(f"Error listing tools: {e}")

if __name__ == "__main__":
    asyncio.run(print_tools())