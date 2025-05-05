"""
Check the contents of the MCP SDK.
"""

import os
import sys
import inspect

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import the MCP package
import mcp
import mcp.client

# Show what's in the MCP package
print("MCP Package Contents:")
for name in dir(mcp):
    if not name.startswith('_'):
        print(f"- {name}")

print("\nMCP Client Module Contents:")
for name in dir(mcp.client):
    if not name.startswith('_'):
        print(f"- {name}")

# If there's a Client class, let's see its methods
if hasattr(mcp.client, 'Client'):
    print("\nMCP Client Class Methods:")
    for name, obj in inspect.getmembers(mcp.client.Client):
        if not name.startswith('_') and callable(obj):
            print(f"- {name}")

# If there's a stdio module, check that too
if hasattr(mcp.client, 'stdio'):
    print("\nMCP Stdio Module Contents:")
    for name in dir(mcp.client.stdio):
        if not name.startswith('_'):
            print(f"- {name}")
            
# Get the version
print(f"\nMCP SDK Version: {mcp.__version__ if hasattr(mcp, '__version__') else 'Unknown'}")