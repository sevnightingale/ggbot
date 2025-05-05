"""
CCXT MCP data source implementation.

This module provides a DataSource implementation for the CCXT MCP,
allowing extraction of market data from cryptocurrency exchanges via the CCXT MCP server.
"""

import os
import json
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from core.mcp.ccxt import CCXTMCPClient
from extraction.interfaces.data_source import DataSource


class CCXTMCPDataSource(DataSource):
    """
    Data source for market data from cryptocurrency exchanges via CCXT MCP.
    
    This data source connects to the CCXT MCP server to fetch market data
    from various cryptocurrency exchanges.
    """
    
    def __init__(
        self,
        exchange_id: str = 'binance',
        account_id: Optional[str] = None,
        user_id: str = DEFAULT_USER_ID
    ):
        """
        Initialize the CCXT MCP data source.
        
        Args:
            exchange_id: ID of the exchange to use (e.g., 'binance', 'kucoin')
            account_id: Optional account ID for authenticated requests
            user_id: User ID to associate with this data source
        """
        self.exchange_id = exchange_id
        self.account_id = account_id
        self.user_id = user_id
        self._log = logger.bind(user_id=user_id)
        self.mcp_client = None
        
        # Map of timeframe strings to milliseconds for OHLCV requests
        self.timeframe_ms = {
            '1m': 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '30m': 30 * 60 * 1000,
            '1h': 60 * 60 * 1000,
            '4h': 4 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
            '1w': 7 * 24 * 60 * 60 * 1000
        }
    
    async def _ensure_client_connected(self) -> None:
        """
        Ensure the MCP client is connected.
        """
        if not self.mcp_client:
            self.mcp_client = CCXTMCPClient(user_id=self.user_id)
            await self.mcp_client.connect()
        elif not self.mcp_client.is_connected:
            await self.mcp_client.connect()
    
    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data from the exchange via CCXT MCP.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe (e.g., '15m', '1h', '4h', '1d')
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            DataFrame containing historical OHLCV data
            
        Raises:
            ValueError: If timeframe is not supported or connection to MCP fails
        """
        self._log.info(
            f"Fetching {timeframe} OHLCV data for {symbol} from {self.exchange_id} "
            f"({start_date} to {end_date})"
        )
        
        if timeframe not in self.timeframe_ms:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        # Convert datetime to timestamp in milliseconds
        since = int(start_date.timestamp() * 1000)
        until = int(end_date.timestamp() * 1000)
        
        # Create asyncio event loop for async calls
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Ensure MCP client is connected
            loop.run_until_complete(self._ensure_client_connected())
            
            # Calculate number of candles needed
            timeframe_duration_ms = self.timeframe_ms[timeframe]
            max_limit = 1000  # Most exchanges limit to 1000 candles per request
            
            all_candles = []
            current_since = since
            
            while current_since < until:
                # Fetch candles
                candles = loop.run_until_complete(
                    self.mcp_client.fetch_ohlcv(
                        exchange_id=self.exchange_id,
                        symbol=symbol,
                        timeframe=timeframe,
                        since=current_since,
                        limit=max_limit,
                        account_id=self.account_id
                    )
                )
                
                if not candles:
                    break
                    
                all_candles.extend(candles)
                
                # Update since for next batch
                last_timestamp = candles[-1][0]
                current_since = last_timestamp + timeframe_duration_ms
                
                # Avoid rate limits
                loop.run_until_complete(asyncio.sleep(0.5))
            
            # Convert to DataFrame
            if all_candles:
                df = pd.DataFrame(
                    all_candles, 
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                
                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                # Filter to requested date range
                df = df[
                    (df['timestamp'] >= pd.Timestamp(start_date)) & 
                    (df['timestamp'] <= pd.Timestamp(end_date))
                ]
                
                return df
            else:
                self._log.warning(f"No data found for {symbol} {timeframe}")
                return pd.DataFrame(
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                
        except Exception as e:
            self._log.error(
                f"Error fetching historical data for {symbol} {timeframe}: {str(e)}"
            )
            raise ValueError(
                f"Error fetching historical data for {symbol} {timeframe}: {str(e)}"
            )
        finally:
            loop.close()
    
    def to_database_format(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        user_id: str = DEFAULT_USER_ID,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Convert DataFrame to database format.
        
        Args:
            df: DataFrame containing OHLCV data
            symbol: Trading pair symbol
            timeframe: Timeframe
            user_id: User ID to associate with the data
            **kwargs: Additional keyword arguments
            
        Returns:
            List of dictionaries in database format
        """
        if df.empty:
            return []
        
        data_entries = []
        
        for _, row in df.iterrows():
            # Create raw_data dictionary
            raw_data = {
                'timestamp': row['timestamp'].isoformat(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume'])
            }
            
            # Create entry
            entry = {
                'user_id': user_id,
                'symbol': symbol,
                'timeframe': timeframe,
                'source': f'ccxt_mcp_{self.exchange_id}',
                'data_type': 'ohlcv',
                'raw_data': raw_data,
                'indicators': {},
                'updated_at': datetime.now()
            }
            
            data_entries.append(entry)
        
        return data_entries