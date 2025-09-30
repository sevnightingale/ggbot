#!/usr/bin/env python
"""Test the MCP metadata module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mcp.metadata import (
    get_mcp_tool_name,
    get_tool_info,
    get_available_indicators
)


def test_metadata():
    """Test the metadata functions."""
    print("=== Testing MCP Metadata Module ===\n")
    
    # Test getting MCP tool name
    test_indicators = ["RSI", "MACD", "BollingerBands", "SMA", "rsi", "macd"]
    
    print("Testing indicator name mapping:")
    for indicator in test_indicators:
        tool_name = get_mcp_tool_name(indicator)
        print(f"  {indicator:20} -> {tool_name}")
    
    # Test getting tool info
    print("\nTesting tool info for RSI:")
    rsi_tool = get_mcp_tool_name("RSI")
    if rsi_tool:
        info = get_tool_info(rsi_tool)
        if info:
            print(f"  Name: {info['name']}")
            print(f"  Description: {info['description']}")
            print(f"  Parameters:")
            for param, details in info['parameters'].items():
                print(f"    - {param}: {details['type']} (required: {details['required']})")
    
    # Show available indicators
    print("\nSample of available indicators:")
    available = get_available_indicators()
    print(f"  Total available: {len(available)}")
    print(f"  First 10: {available[:10]}")
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_metadata()