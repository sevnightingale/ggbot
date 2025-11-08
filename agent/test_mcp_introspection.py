#!/usr/bin/env python3
"""
Quick test to see what the MCP server object exposes
"""
import sys
sys.path.insert(0, '/home/sev/ggbot')

from agent.mcp_server import create_mcp_server

# Create the server
server = create_mcp_server()

print("=" * 80)
print("MCP SERVER OBJECT INTROSPECTION")
print("=" * 80)
print(f"\nServer type: {type(server)}")
print(f"Server class: {server.__class__.__name__}")
print(f"Server module: {server.__class__.__module__}")

print("\n" + "=" * 80)
print("PUBLIC METHODS AND ATTRIBUTES:")
print("=" * 80)
for attr in dir(server):
    if not attr.startswith('_'):
        attr_value = getattr(server, attr)
        attr_type = type(attr_value).__name__
        print(f"  {attr:30} {attr_type}")

print("\n" + "=" * 80)
print("CHECKING COMMON METHOD NAMES:")
print("=" * 80)
test_methods = ['tools', 'list_tools', 'get_tools', 'tools_list', 'get_tool_descriptions', 'describe_tools']
for method_name in test_methods:
    has_it = hasattr(server, method_name)
    print(f"  {method_name:30} {'✅ EXISTS' if has_it else '❌ NOT FOUND'}")

print("\n" + "=" * 80)
print("TRYING TO ACCESS TOOL DATA:")
print("=" * 80)

# Try different approaches
if hasattr(server, 'tools'):
    print("\nserver.tools exists, checking if callable:")
    if callable(server.tools):
        print("  ✅ server.tools() is callable")
        try:
            result = server.tools()
            print(f"  Result type: {type(result)}")
            print(f"  Result length: {len(result) if hasattr(result, '__len__') else 'N/A'}")
            if result:
                print(f"  First item type: {type(result[0]) if len(result) > 0 else 'N/A'}")
                if len(result) > 0:
                    first_tool = result[0]
                    print(f"  First tool attributes: {dir(first_tool)}")
        except Exception as e:
            print(f"  ❌ Error calling server.tools(): {e}")
    else:
        print(f"  server.tools is NOT callable, it's a: {type(server.tools)}")
        print(f"  Value: {server.tools}")

print("\n" + "=" * 80)
print("RAW SERVER DICT CONTENTS:")
print("=" * 80)
print(f"\nServer is a dict with {len(server)} keys:")
for key in server.keys():
    value = server[key]
    print(f"\n  Key: '{key}'")
    print(f"  Type: {type(value).__name__}")
    if isinstance(value, (list, tuple)) and len(value) > 0:
        print(f"  Length: {len(value)}")
        print(f"  First item type: {type(value[0])}")
        if hasattr(value[0], '__dict__'):
            print(f"  First item attributes: {list(value[0].__dict__.keys())[:5]}...")
    elif isinstance(value, dict):
        print(f"  Dict keys: {list(value.keys())[:5]}")
    else:
        print(f"  Value: {str(value)[:100]}")

# Now inspect the actual Server instance
if 'instance' in server:
    print("\n" + "=" * 80)
    print("INSPECTING server['instance'] (THE ACTUAL MCP SERVER):")
    print("=" * 80)
    mcp_instance = server['instance']
    print(f"\nInstance type: {type(mcp_instance)}")
    print(f"Instance class: {mcp_instance.__class__.__name__}")

    print("\n📚 PUBLIC METHODS:")
    for attr in dir(mcp_instance):
        if not attr.startswith('_') and callable(getattr(mcp_instance, attr)):
            print(f"  - {attr}()")

    print("\n📦 PUBLIC ATTRIBUTES:")
    for attr in dir(mcp_instance):
        if not attr.startswith('_') and not callable(getattr(mcp_instance, attr)):
            attr_value = getattr(mcp_instance, attr)
            print(f"  - {attr}: {type(attr_value).__name__}")

    # Check for tool-related stuff
    print("\n🔧 CHECKING FOR TOOLS:")
    if hasattr(mcp_instance, 'list_tools'):
        print("  ✅ list_tools() exists!")
        try:
            result = mcp_instance.list_tools()
            print(f"     Result: {result}")
        except Exception as e:
            print(f"     Error: {e}")

    if hasattr(mcp_instance, '_tools'):
        tools = mcp_instance._tools
        print(f"  ✅ _tools attribute exists! Type: {type(tools).__name__}, Length: {len(tools) if hasattr(tools, '__len__') else 'N/A'}")
        if isinstance(tools, dict):
            print(f"     Tool names: {list(tools.keys())}")
            if len(tools) > 0:
                first_tool_name = list(tools.keys())[0]
                first_tool = tools[first_tool_name]
                print(f"     First tool ('{first_tool_name}'): {type(first_tool)}")
                if hasattr(first_tool, '__dict__'):
                    print(f"     Tool attributes: {list(first_tool.__dict__.keys())}")
                if hasattr(first_tool, 'description'):
                    print(f"     Description: {first_tool.description[:100]}...")
