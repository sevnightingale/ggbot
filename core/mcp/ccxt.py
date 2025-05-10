"""
CCXT MCP client module.

This module provides a specialized client for connecting to the CCXT MCP
server, which enables interaction with cryptocurrency exchanges.
"""

import os
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from core.common.config import DEFAULT_USER_ID
from core.common.logger import logger
from core.mcp.client import MCPClient
from core.mcp.exceptions import MCPError
from core.mcp.session import MCPSession
from core.mcp.config import get_mcp_config, get_ccxt_mcp_exchange_id
from core.mcp.dynamic_account import DynamicAccountManager
from core.config.providers.env_credential_provider import EnvCredentialProvider
from core.config.interfaces.credential_provider import CredentialProvider


class CCXTMCPClient(MCPClient):
    """
    Client for interacting with the CCXT MCP server.
    
    This client provides specialized functionality for:
    - Fetching market data from exchanges
    - Executing trades on exchanges
    - Managing exchange accounts
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        user_id: Optional[str] = None,
        connection_timeout: int = 30,
        credential_provider: Optional[CredentialProvider] = None,
        exchange_id: Optional[str] = None,
        use_local_server: bool = False,
        server_path: Optional[str] = None
    ):
        """
        Initialize the CCXT MCP client.

        Args:
            config_path: Path to the CCXT accounts configuration file
            user_id: User ID to associate with this client
            connection_timeout: Timeout in seconds for connection attempts
            credential_provider: Provider for exchange credentials
            exchange_id: Specific exchange ID to use credentials for
            use_local_server: If True, use the local server script instead of global command
            server_path: Path to the local server script (defaults to core/mcp/servers/ccxt_mcp_server.py)
        """
        self.user_id = user_id or DEFAULT_USER_ID
        self.exchange_id = exchange_id
        self.credential_provider = credential_provider or EnvCredentialProvider()
        self.account_manager = DynamicAccountManager(self.credential_provider)

        # Get config from configuration system if no specific path provided
        if not config_path:
            mcp_config = get_mcp_config('ccxt', self.user_id)
            self.config_path = mcp_config.get('config_path')

            # If still not set, use default
            if not self.config_path:
                self.config_path = os.path.join(
                    str(Path(__file__).parents[2]),  # ggbot root directory
                    'core', 'config', 'ccxt-accounts.json'
                )
        else:
            self.config_path = config_path

        # If exchange_id is provided, create dynamic config with credentials
        if self.exchange_id:
            try:
                self.config_path = self.account_manager.create_config_file(
                    self.exchange_id,
                    self.user_id
                )
            except Exception as e:
                logger.error(f"Failed to create dynamic config for {self.exchange_id}: {str(e)}")
                # Fall back to the static config
                logger.warning(f"Falling back to static config file: {self.config_path}")

        # Determine command based on whether to use local server or global command
        if use_local_server:
            # Use local server script
            if not server_path:
                server_path = os.path.join(
                    str(Path(__file__).parent),  # core/mcp directory
                    'servers', 'ccxt_mcp_server.py'
                )
            command = 'python'
            args = [server_path, '--config', self.config_path]
            logger.info(f"Using local CCXT MCP server: {server_path}")
        else:
            # Use global command
            command = 'ccxt-mcp'
            args = ['--config', self.config_path]
        
        # Set up environment variables to pass to the server process
        env = None
        if use_local_server:
            # Copy current environment and add exchange credentials for test/dev setups
            env = os.environ.copy()

            # Add the exchange ID and credentials
            if self.exchange_id:
                env["EXCHANGE_NAME"] = self.exchange_id

                # Try to get credentials from provider
                try:
                    creds = self.credential_provider.get_credentials(self.exchange_id, self.user_id)
                    env["EXCHANGE_API"] = creds.get("apiKey", "")
                    env["EXCHANGE_SECRET"] = creds.get("secret", "")

                    # Password is not always required
                    if "password" in creds:
                        env["EXCHANGE_PASSWORD"] = creds.get("password", "")
                except Exception as e:
                    logger.warning(f"Could not get credentials for env: {str(e)}")

        super().__init__(
            server_name='CCXT',
            command=command,
            args=args,
            user_id=self.user_id,
            config_path=self.config_path,
            connection_timeout=connection_timeout,
            env=env  # Pass environment variables to the server
        )
        
        self._log = logger.bind(user_id=self.user_id)
        self._client_context = None
        self._session_context = None

    async def get_exchange_ids(self) -> List[str]:
        """
        Get a list of all available exchange IDs.
        
        Returns:
            List of exchange IDs supported by CCXT
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        try:
            result = await self.session.call_tool(
                'get_exchange_ids',  # Updated to snake_case naming convention
                {}
            )
            return result.get('ids', [])
        except Exception as e:
            self._log.error(f"Error getting exchange IDs: {str(e)}")
            raise MCPError(f"Error getting exchange IDs: {str(e)}")
            
    async def fetch_ticker(
        self,
        exchange_id: str,
        symbol: str,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch the ticker data for a specific symbol from an exchange.
        
        Args:
            exchange_id: ID of the exchange (e.g., 'binance', 'kucoin')
            symbol: Symbol to fetch (e.g., 'BTC/USDT')
            account_id: Optional account ID if using an authenticated account
            
        Returns:
            Ticker data
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        inputs = {
            'exchange_id': exchange_id,  # Updated to snake_case naming convention
            'symbol': symbol
        }
        
        if account_id:
            inputs['account_id'] = account_id  # Updated to snake_case naming convention
            
        try:
            result = await self.session.call_tool(
                'fetch_ticker',  # Updated to snake_case naming convention
                inputs
            )
            return result
        except Exception as e:
            self._log.error(
                f"Error fetching ticker for {symbol} on {exchange_id}: {str(e)}"
            )
            raise MCPError(
                f"Error fetching ticker for {symbol} on {exchange_id}: {str(e)}"
            )
    
    async def fetch_ohlcv(
        self,
        exchange_id: str,
        symbol: str,
        timeframe: str = '1h',
        since: Optional[int] = None,
        limit: Optional[int] = None,
        account_id: Optional[str] = None
    ) -> List[List[float]]:
        """
        Fetch OHLCV (candle) data for a specific symbol from an exchange.
        
        Args:
            exchange_id: ID of the exchange (e.g., 'binance', 'kucoin')
            symbol: Symbol to fetch (e.g., 'BTC/USDT')
            timeframe: Timeframe (e.g., '1m', '5m', '1h', '1d')
            since: Optional timestamp in milliseconds to fetch data since
            limit: Optional limit on the number of candles to fetch
            account_id: Optional account ID if using an authenticated account
            
        Returns:
            List of OHLCV candles, each as [timestamp, open, high, low, close, volume]
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        inputs = {
            'exchange_id': exchange_id,  # Updated to snake_case naming convention
            'symbol': symbol,
            'timeframe': timeframe
        }
        
        if since is not None:
            inputs['since'] = since
            
        if limit is not None:
            inputs['limit'] = limit
            
        if account_id:
            inputs['account_id'] = account_id  # Updated to snake_case naming convention
            
        try:
            result = await self.session.call_tool(
                'fetch_ohlcv',  # Updated to snake_case naming convention
                inputs
            )
            return result
        except Exception as e:
            self._log.error(
                f"Error fetching OHLCV for {symbol} ({timeframe}) on {exchange_id}: {str(e)}"
            )
            raise MCPError(
                f"Error fetching OHLCV for {symbol} ({timeframe}) on {exchange_id}: {str(e)}"
            )
            
    async def create_order(
        self,
        exchange_id: str,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        params: Optional[Dict[str, Any]] = None,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an order on an exchange.
        
        Args:
            exchange_id: ID of the exchange (e.g., 'binance', 'kucoin')
            symbol: Symbol to trade (e.g., 'BTC/USDT')
            order_type: Type of order ('limit', 'market', etc.)
            side: Side of the order ('buy' or 'sell')
            amount: Amount to buy or sell
            price: Price for limit orders
            params: Optional additional parameters for the exchange
            account_id: Optional account ID if using multiple accounts
            
        Returns:
            Order information
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        inputs = {
            'exchange_id': exchange_id,  # Updated to snake_case naming convention
            'symbol': symbol,
            'type': order_type,
            'side': side,
            'amount': amount
        }
        
        if price is not None:
            inputs['price'] = price
            
        if params:
            inputs['params'] = params
            
        if account_id:
            inputs['account_id'] = account_id  # Updated to snake_case naming convention
            
        try:
            result = await self.session.call_tool(
                'create_order',  # Updated to snake_case naming convention
                inputs
            )
            self._log.info(
                f"Created {order_type} {side} order for {amount} {symbol} on {exchange_id}"
            )
            return result
        except Exception as e:
            self._log.error(
                f"Error creating order for {symbol} on {exchange_id}: {str(e)}"
            )
            raise MCPError(
                f"Error creating order for {symbol} on {exchange_id}: {str(e)}"
            )