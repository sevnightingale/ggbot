"""
MCP Client module.

This module provides client functionality for connecting to and interacting
with MCP (Model Context Protocol) servers. It handles server process management,
connection, and basic communication.
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, Callable, Awaitable
from pathlib import Path
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp import ClientSession

from core.common.logger import logger
from core.mcp.exceptions import MCPConnectionError, MCPTimeoutError, MCPError
from core.mcp.session import MCPSession


class MCPClient:
    """
    Base class for MCP clients.
    
    This class handles connection to MCP servers, maintains the session,
    and provides a high-level interface for executing MCP commands.
    """
    
    def __init__(
        self,
        server_name: str,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        config_path: Optional[str] = None,
        user_id: Optional[str] = None,
        connection_timeout: int = 30,
    ):
        """
        Initialize the MCP client.
        
        Args:
            server_name: Name of the MCP server, used for logging and identification
            command: Command list to launch the MCP server
            env: Optional environment variables for the server process
            config_path: Optional path to a configuration file
            user_id: Optional user ID to associate with this client
            connection_timeout: Timeout in seconds for connection attempts
        """
        self.server_name = server_name
        self.command = command
        self.env = env or {}
        self.config_path = config_path
        self.user_id = user_id
        self.connection_timeout = connection_timeout
        
        self.session = None
        self.is_connected = False
        self._log = logger.bind(user_id=user_id) if user_id else logger
        
    async def connect(self) -> MCPSession:
        """
        Connect to the MCP server.
        
        Returns:
            An MCPSession object for interacting with the server
            
        Raises:
            MCPConnectionError: If connection fails
            MCPTimeoutError: If connection times out
        """
        self._log.info(f"Connecting to {self.server_name} MCP server")
        
        try:
            # Convert command list to string if it's a list
            command_str = self.command if isinstance(self.command, str) else " ".join(self.command)
            
            params = StdioServerParameters(
                command=command_str,
                env=self.env
            )
            
            streams = await asyncio.wait_for(
                stdio_client(params).__aenter__(),
                timeout=self.connection_timeout
            )
            
            raw_session = await asyncio.wait_for(
                ClientSession(streams[0], streams[1]).__aenter__(),
                timeout=self.connection_timeout
            )
            
            await asyncio.wait_for(
                raw_session.initialize(),
                timeout=self.connection_timeout
            )
            
            self.session = MCPSession(raw_session, self.server_name, self.user_id)
            self.is_connected = True
            
            self._log.info(f"Successfully connected to {self.server_name} MCP server")
            return self.session
            
        except asyncio.TimeoutError:
            self._log.error(f"Connection to {self.server_name} MCP server timed out")
            raise MCPTimeoutError(f"Connection to {self.server_name} MCP server timed out")
        except Exception as e:
            self._log.error(f"Failed to connect to {self.server_name} MCP server: {str(e)}")
            raise MCPConnectionError(f"Failed to connect to {self.server_name} MCP server: {str(e)}")
    
    async def disconnect(self) -> None:
        """
        Disconnect from the MCP server.
        """
        if self.session:
            try:
                await self.session.close()
                self.is_connected = False
                self._log.info(f"Disconnected from {self.server_name} MCP server")
            except Exception as e:
                self._log.error(f"Error disconnecting from {self.server_name} MCP server: {str(e)}")
        
    async def __aenter__(self) -> MCPSession:
        """
        Context manager entry point.
        
        Returns:
            MCPSession object
        """
        return await self.connect()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit point.
        """
        await self.disconnect()


async def create_mcp_client(
    server_type: str,
    config_path: Optional[str] = None,
    user_id: Optional[str] = None,
    **kwargs
) -> MCPClient:
    """
    Factory function to create appropriate MCP client based on server type.
    
    Args:
        server_type: Type of MCP server ('ccxt' or 'indicators')
        config_path: Optional path to configuration file
        user_id: Optional user ID to associate with the client
        **kwargs: Additional keyword arguments for the client
        
    Returns:
        Appropriate MCPClient instance
        
    Raises:
        ValueError: If server_type is not recognized
    """
    from core.mcp.ccxt import CCXTMCPClient
    from core.mcp.indicators import IndicatorsMCPClient
    
    if server_type.lower() == 'ccxt':
        return CCXTMCPClient(config_path=config_path, user_id=user_id, **kwargs)
    elif server_type.lower() == 'indicators':
        return IndicatorsMCPClient(config_path=config_path, user_id=user_id, **kwargs)
    else:
        raise ValueError(f"Unknown MCP server type: {server_type}")