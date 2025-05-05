"""
MCP exception classes.

This module defines custom exceptions for MCP-related errors.
"""


class MCPError(Exception):
    """Base exception for MCP-related errors."""
    pass


class MCPConnectionError(MCPError):
    """Exception raised when connection to an MCP server fails."""
    pass


class MCPTimeoutError(MCPError):
    """Exception raised when an MCP operation times out."""
    pass


class MCPToolError(MCPError):
    """Exception raised when an MCP tool call fails."""
    pass