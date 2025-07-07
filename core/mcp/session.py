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

            # Handle CallToolResult objects from FastMCP
            # Extract the actual result value to avoid serialization issues
            if hasattr(result, 'result'):
                self._log.debug(f"Received CallToolResult object, extracting result")
                result = result.result
            
            # Handle MCP content responses (extract text from content field)
            if hasattr(result, 'content') and hasattr(result.content, '__iter__'):
                try:
                    # Extract text from content list
                    text_content = []
                    for content_item in result.content:
                        if hasattr(content_item, 'text'):
                            text_content.append(content_item.text)
                        elif hasattr(content_item, 'type') and content_item.type == 'text':
                            text_content.append(getattr(content_item, 'text', str(content_item)))
                    
                    if text_content:
                        # If we have text content, try to parse as JSON first
                        combined_text = ''.join(text_content)
                        try:
                            import json
                            result = json.loads(combined_text)
                            self._log.debug(f"Successfully parsed MCP content as JSON")
                        except (json.JSONDecodeError, ValueError):
                            # If not valid JSON, return the text as-is
                            result = combined_text
                            self._log.debug(f"MCP content is not JSON, returning as text")
                except Exception as e:
                    self._log.warning(f"Error processing MCP content: {str(e)}")
                    # Fall through to normal processing

            # Verify the result is JSON serializable
            try:
                # Test serialization - this will fail if result isn't serializable
                json.dumps(result)
                self._log.debug(f"Tool call result: {json.dumps(result)[:200]}...")
            except TypeError:
                # If result is not serializable, convert to a string representation
                self._log.warning(f"Tool call result is not JSON serializable, converting to string")
                if isinstance(result, dict):
                    # Create a clean dictionary with string representations of non-serializable values
                    clean_result = {}
                    for k, v in result.items():
                        try:
                            json.dumps({k: v})
                            clean_result[k] = v
                        except TypeError:
                            clean_result[k] = str(v)
                    result = clean_result
                elif isinstance(result, list):
                    # Create a clean list with string representations of non-serializable values
                    clean_result = []
                    for item in result:
                        if isinstance(item, dict):
                            clean_dict = {}
                            for k, v in item.items():
                                try:
                                    json.dumps({k: v})
                                    clean_dict[k] = v
                                except TypeError:
                                    clean_dict[k] = str(v)
                            clean_result.append(clean_dict)
                        else:
                            try:
                                json.dumps(item)
                                clean_result.append(item)
                            except TypeError:
                                clean_result.append(str(item))
                    result = clean_result
                else:
                    # For other types, convert to string
                    result = str(result)

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
            # Use list_tools method which is the correct method name in the MCP SDK
            result = await self.raw_session.list_tools()
            
            # Handle different return types from the MCP SDK
            # In newer versions, list_tools returns a ListToolsResult object
            if hasattr(result, 'tools'):
                tools = result.tools
            else:
                # Handle the case where it's iterable but not a list
                try:
                    tools = list(result)
                except TypeError:
                    # If all else fails, just return the object itself
                    tools = result
                    
            self._log.info(f"Retrieved tools from {self.server_name} MCP server")
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