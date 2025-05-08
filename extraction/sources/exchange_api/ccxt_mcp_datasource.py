"""
CCXT MCP data source implementation.

This module provides an implementation of a DataSource using the CCXT MCP
to fetch market data from cryptocurrency exchanges.
"""

import os
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from core.common.logger import logger
from core.mcp.ccxt import CCXTMCPClient
from extraction.interfaces.data_source import DataSource, DataTimeframe


class CCXTMCPDataSource(DataSource):
    """
    DataSource implementation using the CCXT MCP.
    
    This data source uses the CCXT MCP to fetch OHLCV and other market data
    from various cryptocurrency exchanges. It automatically uses the credentials
    from environment variables or other credential providers.
    """
    
    def __init__(self, exchange_id: str, user_id: Optional[str] = None):
        """
        Initialize the CCXT MCP data source.
        
        Args:
            exchange_id: ID of the exchange to use
            user_id: Optional user ID for user-specific credentials
        """
        self.exchange_id = exchange_id.lower()
        self.user_id = user_id
        self.client = None
        self.logger = logger.bind(
            component="CCXTMCPDataSource", 
            exchange=self.exchange_id,
            user_id=self.user_id or "system"
        )
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        
    async def connect(self):
        """Connect to the CCXT MCP."""
        if self.client and self.client.is_connected:
            return
            
        self.client = CCXTMCPClient(
            exchange_id=self.exchange_id,
            user_id=self.user_id
        )
        
        await self.client.connect()
        self.logger.info(f"Connected to {self.exchange_id} via CCXT MCP")
        
    async def disconnect(self):
        """Disconnect from the CCXT MCP."""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            self.logger.info(f"Disconnected from {self.exchange_id}")
        
    async def get_available_symbols(self) -> List[str]:
        """
        Get a list of available symbols from the exchange.
        
        Returns:
            List of symbols (e.g., ['BTC/USDT', 'ETH/USDT', ...])
        """
        if not self.client or not self.client.is_connected:
            await self.connect()
            
        try:
            # This is a placeholder - CCXT MCP doesn't have a direct method
            # We would need to implement a custom tool call for this
            # For now, we'll return a default list for common symbols
            return [
                "BTC/USDT", "ETH/USDT", "XRP/USDT", "LTC/USDT", "BCH/USDT",
                "EOS/USDT", "BNB/USDT", "XTZ/USDT", "ADA/USDT", "LINK/USDT"
            ]
        except Exception as e:
            self.logger.error(f"Error getting available symbols: {str(e)}")
            return []
        
    async def get_ohlcv(
        self, 
        symbol: str, 
        timeframe: Union[str, DataTimeframe], 
        limit: int = 100,
        since: Optional[Union[int, datetime]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get OHLCV (candle) data for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe for the candles
            limit: Maximum number of candles to retrieve
            since: Start time for data retrieval
            
        Returns:
            List of candle dictionaries with keys: timestamp, open, high, low, close, volume
        """
        if not self.client or not self.client.is_connected:
            await self.connect()
            
        # Convert DataTimeframe enum to string if needed
        if isinstance(timeframe, DataTimeframe):
            tf_str = {
                DataTimeframe.MINUTE_1: "1m",
                DataTimeframe.MINUTE_5: "5m",
                DataTimeframe.MINUTE_15: "15m",
                DataTimeframe.MINUTE_30: "30m",
                DataTimeframe.HOUR_1: "1h",
                DataTimeframe.HOUR_4: "4h",
                DataTimeframe.DAY_1: "1d",
                DataTimeframe.WEEK_1: "1w"
            }.get(timeframe, "1h")
        else:
            tf_str = timeframe
            
        # Convert datetime to timestamp if needed
        if isinstance(since, datetime):
            since_ms = int(since.timestamp() * 1000)
        else:
            since_ms = since
            
        try:
            # Fetch OHLCV data from the exchange
            ohlcv_data = await self.client.fetch_ohlcv(
                exchange_id=self.exchange_id,
                symbol=symbol,
                timeframe=tf_str,
                since=since_ms,
                limit=limit
            )
            
            # Convert to dictionary format
            result = []
            for candle in ohlcv_data:
                result.append({
                    "timestamp": candle[0],
                    "datetime": datetime.fromtimestamp(candle[0] / 1000),
                    "open": candle[1],
                    "high": candle[2],
                    "low": candle[3],
                    "close": candle[4],
                    "volume": candle[5]
                })
                
            self.logger.info(
                f"Retrieved {len(result)} {tf_str} candles for {symbol} from {self.exchange_id}"
            )
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV data for {symbol}: {str(e)}")
            return []
            
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current ticker data for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            Dictionary with ticker data
        """
        if not self.client or not self.client.is_connected:
            await self.connect()
            
        try:
            ticker = await self.client.fetch_ticker(
                exchange_id=self.exchange_id,
                symbol=symbol
            )
            
            self.logger.info(f"Retrieved ticker for {symbol} from {self.exchange_id}")
            return ticker
            
        except Exception as e:
            self.logger.error(f"Error fetching ticker for {symbol}: {str(e)}")
            return {}