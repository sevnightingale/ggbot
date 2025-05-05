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
        connection_timeout: int = 30
    ):
        """
        Initialize the CCXT MCP client.
        
        Args:
            config_path: Path to the CCXT accounts configuration file
            user_id: User ID to associate with this client
            connection_timeout: Timeout in seconds for connection attempts
        """
        self.user_id = user_id or DEFAULT_USER_ID
        
        # Get config from configuration system
        mcp_config = get_mcp_config('ccxt', self.user_id)
        
        # Use provided config_path or get from configuration
        self.config_path = config_path or mcp_config.get('config_path')
        
        # If still not set, use default
        if not self.config_path:
            self.config_path = os.path.join(
                str(Path(__file__).parents[2]),  # ggbot root directory
                'core', 'config', 'ccxt-accounts.json'
            )
        
        command = ['ccxt-mcp', '--config', self.config_path]
        
        super().__init__(
            server_name='CCXT',
            command=command,
            user_id=self.user_id,
            config_path=self.config_path,
            connection_timeout=connection_timeout
        )
        
        self._log = logger.bind(user_id=self.user_id)

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
                'getExchangeIds',
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
            'exchangeId': exchange_id,
            'symbol': symbol
        }
        
        if account_id:
            inputs['accountId'] = account_id
            
        try:
            result = await self.session.call_tool(
                'fetchTicker',
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
            'exchangeId': exchange_id,
            'symbol': symbol,
            'timeframe': timeframe
        }
        
        if since is not None:
            inputs['since'] = since
            
        if limit is not None:
            inputs['limit'] = limit
            
        if account_id:
            inputs['accountId'] = account_id
            
        try:
            result = await self.session.call_tool(
                'fetchOHLCV',
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
            'exchangeId': exchange_id,
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
            inputs['accountId'] = account_id
            
        try:
            result = await self.session.call_tool(
                'createOrder',
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