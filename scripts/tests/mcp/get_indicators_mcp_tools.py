#!/usr/bin/env python
"""
Get and save the list of available tools from Crypto Indicators MCP.
This will help us know the exact tool names and parameters.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mcp.indicators import IndicatorsMCPClient


async def get_and_save_tool_list():
    """Connect to MCP and save the tool list."""
    print("Connecting to Crypto Indicators MCP...")
    
    # Set default exchange
    os.environ["EXCHANGE_NAME"] = "binance"
    
    # Create and connect client
    mcp_client = IndicatorsMCPClient()
    await mcp_client.connect()
    
    print("Connected! Getting tool list...")
    
    # Get tools using the raw session
    result = await mcp_client.session.raw_session.list_tools()
    
    # Extract tools
    tools = []
    if hasattr(result, 'tools'):
        raw_tools = result.tools
    else:
        raw_tools = result
    
    # Process each tool
    for tool in raw_tools:
        tool_info = {
            "name": tool.name,
            "description": tool.description
        }
        
        # Extract parameters
        if hasattr(tool, 'inputSchema') and tool.inputSchema:
            schema = tool.inputSchema
            if isinstance(schema, dict):
                properties = schema.get('properties', {})
                required = schema.get('required', [])
                
                params = {}
                for param_name, param_info in properties.items():
                    params[param_name] = {
                        "type": param_info.get('type', 'unknown'),
                        "description": param_info.get('description', ''),
                        "required": param_name in required,
                        "default": param_info.get('default')
                    }
                
                tool_info["parameters"] = params
                tool_info["required_params"] = required
        
        tools.append(tool_info)
    
    # Save to file
    output_file = f"indicators_mcp_tools_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(tools, f, indent=2)
    
    print(f"\nSaved {len(tools)} tools to {output_file}")
    
    # Print summary
    print("\nTool Summary:")
    print("-" * 50)
    
    # Group tools by type
    indicators = []
    other_tools = []
    
    for tool in tools:
        if any(keyword in tool['name'].lower() for keyword in ['fetch', 'backtest', 'analyze', 'get']):
            other_tools.append(tool['name'])
        else:
            indicators.append(tool['name'])
    
    print(f"\nIndicator Tools ({len(indicators)}):")
    for ind in sorted(indicators):
        print(f"  - {ind}")
    
    print(f"\nOther Tools ({len(other_tools)}):")
    for tool in sorted(other_tools):
        print(f"  - {tool}")
    
    # Disconnect
    await mcp_client.disconnect()
    
    return tools


if __name__ == "__main__":
    tools = asyncio.run(get_and_save_tool_list())
    
    # Also create a simple mapping file
    print("\nCreating indicator name mapping...")
    
    # Extract just indicator names for mapping
    indicator_mapping = {}
    for tool in tools:
        name = tool['name']
        if not any(keyword in name.lower() for keyword in ['fetch', 'backtest', 'analyze', 'get']):
            # Create common variations
            indicator_mapping[name] = name
            indicator_mapping[name.upper()] = name
            indicator_mapping[name.lower()] = name
            
            # Handle common abbreviations
            if name == "RSI":
                indicator_mapping["RelativeStrengthIndex"] = name
            elif name == "MACD":
                indicator_mapping["MovingAverageConvergenceDivergence"] = name
    
    # Save mapping
    with open('indicator_name_mapping.json', 'w') as f:
        json.dump(indicator_mapping, f, indent=2)
    
    print(f"Created mapping file with {len(indicator_mapping)} entries")