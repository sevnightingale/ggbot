#!/usr/bin/env python
"""
Test script to inspect MCP ClientSession methods.

This script examines the available methods in the ClientSession class.
"""

import sys
import inspect
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import MCP components
from mcp import ClientSession

# Print available methods
print("Available methods in ClientSession:")
for name, obj in inspect.getmembers(ClientSession):
    if not name.startswith('_'):  # Skip private/internal methods
        print(f"- {name}: {obj}")

# Print module info
print("\nMCP Module Information:")
import mcp
print(f"MCP Version: {getattr(mcp, '__version__', 'Unknown')}")
print(f"MCP Path: {mcp.__file__}")

# Show dir() output to see all attributes
print("\nAll attributes via dir():")
print(dir(ClientSession))