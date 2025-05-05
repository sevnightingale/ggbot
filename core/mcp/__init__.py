"""
Core MCP (Model Context Protocol) package for ggbots.

This package provides base functionality for integrating MCPs (Model Context Protocols)
including connection management, client sessions, and error handling.
"""

from core.mcp.client import create_mcp_client, MCPClient
from core.mcp.session import MCPSession
from core.mcp.exceptions import MCPError, MCPConnectionError, MCPTimeoutError

__all__ = [
    'create_mcp_client', 
    'MCPClient',
    'MCPSession',
    'MCPError',
    'MCPConnectionError', 
    'MCPTimeoutError',
]