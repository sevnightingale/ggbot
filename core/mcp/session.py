"""
MCP Session module.

This module provides session management for MCP interactions,
wrapping the raw ClientSession with additional error handling and logging.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Union
from mcp import ClientSession
from core.common.logger import logger
from core.mcp.exceptions import MCPError


class MCPSession:
    """
    Wrapper for MCP ClientSession that provides additional functionality.
    
    This class wraps the raw ClientSession from the MCP SDK with additional
    error handling, logging, and convenience methods.
    """
    
    def __init__(
        self, 
        raw_session: ClientSession,
        server_name: str,
        user_id: Optional[str] = None
    ):
        """
        Initialize the MCP session.
        
        Args:
            raw_session: The underlying ClientSession from MCP SDK
            server_name: Name of the MCP server, used for logging
            user_id: Optional user ID to associate with this session
        """
        self.raw_session = raw_session
        self.server_name = server_name
        self.user_id = user_id
        self._log = logger.bind(user_id=user_id) if user_id else logger
    
    async def call_tool(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        timeout: Optional[int] = 60
    ) -> Any:
        """
        Call an MCP tool with the given inputs.
        
        Args:
            tool_name: Name of the tool to call
            inputs: Dictionary of input parameters
            timeout: Optional timeout in seconds
            
        Returns:
            Tool response
            
        Raises:
            MCPError: If the tool call fails
        """
        self._log.info(f"Calling {self.server_name} MCP tool: {tool_name}")
        
        try:
            result = await asyncio.wait_for(
                self.raw_session.call_tool(tool_name, inputs),
                timeout=timeout
            )
            
            self._log.debug(f"Tool call result: {json.dumps(result)[:200]}...")
            return result
            
        except asyncio.TimeoutError:
            error_msg = f"Tool call to {tool_name} timed out after {timeout} seconds"
            self._log.error(error_msg)
            raise MCPError(error_msg)
            
        except Exception as e:
            error_msg = f"Error calling {tool_name}: {str(e)}"
            self._log.error(error_msg)
            raise MCPError(error_msg)
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get the list of available tools from the MCP server.
        
        Returns:
            List of tools with their schemas
            
        Raises:
            MCPError: If getting tools fails
        """
        try:
            tools = await self.raw_session.get_tools()
            self._log.info(f"Retrieved {len(tools)} tools from {self.server_name} MCP server")
            return tools
            
        except Exception as e:
            error_msg = f"Error getting tools from {self.server_name} MCP server: {str(e)}"
            self._log.error(error_msg)
            raise MCPError(error_msg)
    
    async def close(self) -> None:
        """
        Close the MCP session.
        
        Raises:
            MCPError: If closing the session fails
        """
        try:
            await self.raw_session.__aexit__(None, None, None)
            self._log.info(f"Closed {self.server_name} MCP session")
            
        except Exception as e:
            error_msg = f"Error closing {self.server_name} MCP session: {str(e)}"
            self._log.error(error_msg)
            raise MCPError(error_msg)