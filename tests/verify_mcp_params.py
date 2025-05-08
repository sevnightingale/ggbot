"""
Test script to verify the correct format for StdioServerParameters.
"""

import os
import sys
import pprint

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

print("Checking MCP SDK API behavior...")

# First, try to import the modules to see what's available
try:
    from mcp.client.stdio import StdioServerParameters
    print("Successfully imported StdioServerParameters from mcp.client.stdio")
    
    # Check StdioServerParameters documentation
    print("\nStdioServerParameters docstring:")
    print(StdioServerParameters.__doc__ or "No docstring available")
    
    # Check StdioServerParameters signature
    import inspect
    signature = inspect.signature(StdioServerParameters)
    print("\nStdioServerParameters signature:")
    pprint.pprint(str(signature))
    
    print("\nParameter details:")
    for param_name, param in signature.parameters.items():
        print(f"{param_name}: {param.annotation}")
    
except ImportError as e:
    print(f"Import error: {e}")

print("\nTesting both formats for command parameter...")

try:
    # Try with a list of strings
    from mcp.client.stdio import StdioServerParameters
    params_list = StdioServerParameters(command=["echo", "test"])
    print("List format ACCEPTED ✓")
    print(f"  Type: {type(params_list.command)}")
    print(f"  Value: {params_list.command}")
except Exception as e:
    print(f"List format ERROR: {e}")

try:
    # Try with a single string
    from mcp.client.stdio import StdioServerParameters
    params_string = StdioServerParameters(command="echo test")
    print("String format ACCEPTED ✓")
    print(f"  Type: {type(params_string.command)}")
    print(f"  Value: {params_string.command}")
except Exception as e:
    print(f"String format ERROR: {e}")

print("\nChecking MCP version...")
try:
    import mcp
    version = getattr(mcp, "__version__", "Unknown")
    print(f"MCP version: {version}")
except Exception as e:
    print(f"Error checking MCP version: {e}")

print("\nTest complete!")