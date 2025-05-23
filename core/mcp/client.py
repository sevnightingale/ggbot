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
        command: Union[str, List[str]],
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        config_path: Optional[str] = None,
        user_id: Optional[str] = None,
        connection_timeout: int = 30,
    ):
        """
        Initialize the MCP client.
        
        Args:
            server_name: Name of the MCP server, used for logging and identification
            command: Command string or path to launch the MCP server
            args: Optional list of arguments for the command
            env: Optional environment variables for the server process
            config_path: Optional path to a configuration file
            user_id: Optional user ID to associate with this client
            connection_timeout: Timeout in seconds for connection attempts
        """
        self.server_name = server_name
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.config_path = config_path
        self.user_id = user_id
        self.connection_timeout = connection_timeout
        
        self.session = None
        self.is_connected = False
        self._log = logger.bind(user_id=user_id) if user_id else logger
        
        # Initialize context objects to None
        self._client_context = None
        self._session_context = None
        
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
        
        # Close existing session if one exists
        if self.is_connected and self.session:
            try:
                await self.disconnect()
            except Exception as e:
                self._log.warning(f"Error during disconnection: {str(e)}")
                # Continue with reconnection attempt
        
        try:
            # Check if we're connecting to an existing PM2-managed server
            use_existing_server = os.environ.get("USE_PM2_MCP_SERVER", "0") == "1"
            
            if use_existing_server:
                self._log.info(f"Connecting to existing {self.server_name} MCP server managed by PM2")
                # Use the pm2 command to get the server pid
                import subprocess
                proc = subprocess.run(["pm2", "jlist"], capture_output=True, text=True)
                pm2_data = json.loads(proc.stdout)
                
                server_pid = None
                for app in pm2_data:
                    if app.get("name") == "ccxt-mcp-server" and app.get("pm2_env", {}).get("status") == "online":
                        server_pid = app.get("pid")
                        break
                
                if not server_pid:
                    raise MCPConnectionError("No running PM2-managed MCP server found")
                
                self._log.info(f"Found existing MCP server with PID {server_pid}")
                
                # Connect to the existing server using stdio redirection
                # For simplicity, we'll just try the normal connection method
                # but without starting a new process
                command = "dummy"  # Will not be used as we're not starting a process
                args = []
            else:
                # Ensure command is a string
                if isinstance(self.command, list) and len(self.command) > 0:
                    command = self.command[0]
                    # Combine any args from the list with self.args
                    args = self.command[1:] + self.args
                else:
                    command = self.command
                    args = self.args
                
                self._log.debug(f"Launching command: {command} with args: {args}")
            
            # Only launch a new server if we're not connecting to an existing one
            if not use_existing_server:
                # Create and configure server parameters
                server_params = StdioServerParameters(
                    command=command,
                    args=args,
                    env=self.env
                )
                
                # Connect to the server using stdio transport
                self._client_context = stdio_client(server_params)
                read_stream, write_stream = await asyncio.wait_for(
                    self._client_context.__aenter__(),
                    timeout=self.connection_timeout
                )
            
            # Create the session
            self._session_context = ClientSession(read_stream, write_stream)
            raw_session = await asyncio.wait_for(
                self._session_context.__aenter__(),
                timeout=self.connection_timeout
            )
            
            # Initialize the session with timeout
            try:
                await asyncio.wait_for(
                    raw_session.initialize(),
                    timeout=self.connection_timeout
                )
            except Exception as e:
                self._log.error(f"Session initialization failed: {str(e)}")
                # Clean up resources - ensure we exit both context managers
                await self._cleanup_contexts()
                raise
            
            # Create the application-level session wrapper
            self.session = MCPSession(raw_session, self.server_name, self.user_id)
            self.is_connected = True
            
            self._log.info(f"Successfully connected to {self.server_name} MCP server")
            return self.session
            
        except asyncio.TimeoutError:
            self._log.error(f"Connection to {self.server_name} MCP server timed out")
            await self._cleanup_contexts()
            raise MCPTimeoutError(f"Connection to {self.server_name} MCP server timed out")
        except Exception as e:
            self._log.error(f"Failed to connect to {self.server_name} MCP server: {str(e)}")
            await self._cleanup_contexts()
            if isinstance(e, MCPConnectionError) or isinstance(e, MCPTimeoutError):
                raise
            else:
                raise MCPConnectionError(f"Failed to connect to {self.server_name} MCP server: {str(e)}")
    
    async def _cleanup_contexts(self):
        """Helper method to clean up context managers safely."""
        # Clean up session context
        if self._session_context:
            try:
                await self._session_context.__aexit__(None, None, None)
                self._log.debug("Exited session context")
            except Exception as e:
                self._log.error(f"Error exiting session context: {str(e)}")
        
        # Clean up client context
        if self._client_context:
            try:
                await self._client_context.__aexit__(None, None, None)
                self._log.debug("Exited client context")
            except Exception as e:
                self._log.error(f"Error exiting client context: {str(e)}")
    
    async def disconnect(self) -> None:
        """
        Disconnect from the MCP server.
        """
        self._log.info(f"Disconnecting from {self.server_name} MCP server")
        self.is_connected = False
        
        # Close MCPSession wrapper first (if it exists)
        if self.session:
            try:
                await self.session.close()
                self._log.info(f"Closed {self.server_name} MCP session")
            except Exception as e:
                self._log.error(f"Error closing session: {str(e)}")
        
        # Clean up contexts
        await self._cleanup_contexts()
        
        # Reset session
        self.session = None
        self._log.info(f"Disconnected from {self.server_name} MCP server")
        
    async def __aenter__(self) -> 'MCPSession':
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