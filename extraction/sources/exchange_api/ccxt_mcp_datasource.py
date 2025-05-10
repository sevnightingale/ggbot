"""
CCXT MCP data source implementation.

This module provides an implementation of a DataSource using the CCXT MCP
to fetch market data from cryptocurrency exchanges.

This datasource allows fetching market data such as OHLCV, current prices,
and available symbols from any cryptocurrency exchange supported by CCXT.
"""

import os
import asyncio
import pandas as pd
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
        
        # Initialize caches for symbols and timeframes
        self._symbols_cache = None
        self._timeframes_cache = None
        
    async def disconnect(self):
        """Disconnect from the CCXT MCP."""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            self.logger.info(f"Disconnected from {self.exchange_id}")
        
    async def get_historical_data(
        self, 
        symbol: str, 
        timeframe: Union[str, DataTimeframe], 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV (Open, High, Low, Close, Volume) data.
        
        Args:
            symbol: The trading pair symbol (e.g., 'BTC/USDT')
            timeframe: The timeframe for the data (e.g., '15m', '1h', '4h', '1d')
            start_date: The start date for the data (optional)
            end_date: The end date for the data (optional)
            limit: Maximum number of data points to fetch (optional)
            
        Returns:
            A pandas DataFrame with OHLCV data and DatetimeIndex
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
                DataTimeframe.HOUR_2: "2h",
                DataTimeframe.HOUR_4: "4h",
                DataTimeframe.HOUR_6: "6h",
                DataTimeframe.HOUR_8: "8h",
                DataTimeframe.HOUR_12: "12h",
                DataTimeframe.DAY_1: "1d",
                DataTimeframe.DAY_3: "3d",
                DataTimeframe.WEEK_1: "1w",
                DataTimeframe.MONTH_1: "1M",
            }.get(timeframe, "1h")
        else:
            tf_str = timeframe
            
        # Convert start_date to timestamp if provided
        since_ms = None
        if start_date:
            since_ms = int(start_date.timestamp() * 1000)
        
        # If no limit is provided but end_date is, calculate limit
        if limit is None and end_date and start_date:
            # Estimate number of candles needed based on timeframe and date range
            timeframe_minutes = {
                "1m": 1, "5m": 5, "15m": 15, "30m": 30,
                "1h": 60, "2h": 120, "4h": 240, "6h": 360, "8h": 480, "12h": 720,
                "1d": 1440, "3d": 4320, "1w": 10080, "1M": 43200
            }
            minutes = timeframe_minutes.get(tf_str, 60)
            delta = end_date - start_date
            limit = (delta.total_seconds() // 60) // minutes + 10  # Add buffer
            limit = min(1000, int(limit))  # Cap at 1000 to avoid hitting API limits
            
        try:
            # Fetch OHLCV data from the exchange
            ohlcv_data = await self.client.fetch_ohlcv(
                exchange_id=self.exchange_id,
                symbol=symbol,
                timeframe=tf_str,
                since=since_ms,
                limit=limit
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv_data,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            if df.empty:
                return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
                
            # Convert timestamp to datetime and set as index
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Rename columns to match DataSource interface convention
            df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }, inplace=True)
            
            # Filter by end_date if provided
            if end_date:
                df = df[df.index <= end_date]
                
            self.logger.info(
                f"Retrieved {len(df)} {tf_str} candles for {symbol} from {self.exchange_id}"
            )
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV data for {symbol}: {str(e)}")
            return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
            
    async def get_latest_data(self, symbol: str, timeframe: str, limit: int = 1) -> pd.DataFrame:
        """
        Fetch the most recent OHLCV data points.
        
        Args:
            symbol: The trading pair symbol (e.g., 'BTC/USDT')
            timeframe: The timeframe for the data (e.g., '15m', '1h', '4h', '1d')
            limit: Number of most recent data points to fetch (default: 1)
            
        Returns:
            A pandas DataFrame with the most recent OHLCV data
        """
        # Use the same implementation as get_historical_data but with a small limit
        return await self.get_historical_data(symbol, timeframe, limit=limit)
            
    async def get_current_price(self, symbol: str) -> float:
        """
        Get the current price for a symbol.
        
        Args:
            symbol: The trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            The current price as a float
        """
        if not self.client or not self.client.is_connected:
            await self.connect()
            
        try:
            ticker = await self.client.fetch_ticker(
                exchange_id=self.exchange_id,
                symbol=symbol
            )
            
            if 'last' in ticker and ticker['last'] is not None:
                price = float(ticker['last'])
                self.logger.info(f"Current price for {symbol} on {self.exchange_id}: {price}")
                return price
            else:
                raise ValueError(f"No 'last' price in ticker for {symbol}")
                
        except Exception as e:
            self.logger.error(f"Error fetching current price for {symbol}: {str(e)}")
            raise ValueError(f"Could not get current price for {symbol}: {str(e)}")
            
    async def get_supported_symbols(self) -> List[str]:
        """
        Get a list of symbols supported by this data source.
        
        Returns:
            A list of supported symbol strings (e.g., ['BTC/USDT', 'ETH/USDT', ...])
        """
        if not self.client or not self.client.is_connected:
            await self.connect()
            
        try:
            # If we've already fetched the symbols, return from cache
            if self._symbols_cache is not None:
                return self._symbols_cache
            
            # Try to get available markets from the exchange
            try:
                markets = await self.client.session.call_tool(
                    'loadMarkets',
                    {'exchangeId': self.exchange_id}
                )
                symbols = list(markets.keys()) if isinstance(markets, dict) else []
            except Exception:
                # Fallback to a list of common symbols
                symbols = [
                    "BTC/USDT", "ETH/USDT", "XRP/USDT", "LTC/USDT", "BCH/USDT",
                    "EOS/USDT", "BNB/USDT", "XTZ/USDT", "ADA/USDT", "LINK/USDT"
                ]
                
            self._symbols_cache = symbols
            self.logger.info(f"Found {len(symbols)} symbols on {self.exchange_id}")
            return symbols
            
        except Exception as e:
            self.logger.error(f"Error getting supported symbols: {str(e)}")
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
            
    def get_supported_timeframes(self) -> List[str]:
        """
        Get a list of timeframes supported by this data source.
        
        Returns:
            A list of supported timeframe strings (e.g., ['1m', '5m', '15m', '1h', '4h', '1d'])
        """
        # If we've cached the timeframes, return them
        if hasattr(self, '_timeframes_cache') and self._timeframes_cache is not None:
            return self._timeframes_cache
            
        # Most CCXT exchanges support these standard timeframes
        # In the future, we could fetch the exchange's specific timeframes via CCXT
        timeframes = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '1w', '1M']
        
        # Cache the timeframes for future calls
        self._timeframes_cache = timeframes
        
        return timeframes
        
    def get_source_name(self) -> str:
        """
        Get the name of this data source.
        
        Returns:
            The name of the data source
        """
        return f"ccxt_mcp_{self.exchange_id}"