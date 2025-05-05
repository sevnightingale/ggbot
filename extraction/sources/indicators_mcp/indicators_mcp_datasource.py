"""
Crypto Indicators MCP data source implementation.

This module provides a DataSource implementation for the Crypto Indicators MCP,
allowing extraction of technical indicators computed by the Crypto Indicators MCP server.
"""

import os
import json
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from core.mcp.indicators import IndicatorsMCPClient
from extraction.interfaces.data_source import DataSource


class IndicatorsMCPDataSource(DataSource):
    """
    Data source for technical indicators computed by the Crypto Indicators MCP.
    
    This data source connects to the Crypto Indicators MCP server to compute
    technical indicators based on historical price data.
    """
    
    def __init__(self, user_id: str = DEFAULT_USER_ID):
        """
        Initialize the Indicators MCP data source.
        
        Args:
            user_id: User ID to associate with this data source
        """
        self.user_id = user_id
        self._log = logger.bind(user_id=user_id)
        self.mcp_client = None
    
    async def _ensure_client_connected(self) -> None:
        """
        Ensure the MCP client is connected.
        """
        if not self.mcp_client:
            self.mcp_client = IndicatorsMCPClient(user_id=self.user_id)
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
        Get historical data with technical indicators from the MCP.
        
        Note: This method requires price data from another source, which is then
        enriched with indicators from the Crypto Indicators MCP. In a typical usage,
        you would first fetch prices from another source, then pass them to this
        method to add indicators.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe (e.g., '15m', '1h', '4h', '1d')
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            DataFrame containing historical data with technical indicators
            
        Raises:
            ValueError: If no price data is provided or connection to MCP fails
        """
        self._log.info(f"Fetching indicator data for {symbol} {timeframe}")
        
        # For the Indicators MCP, we need price data from another source
        # This is usually handled by the ExtractionManager by combining multiple sources
        # For now, we'll return an empty DataFrame and log a message
        
        self._log.warning(
            "The Indicators MCP data source requires price data from another source. "
            "Use a combined approach where prices are fetched first, then enriched with indicators."
        )
        
        # Return an empty DataFrame with the expected columns
        return pd.DataFrame(
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
    
    async def compute_indicators(
        self,
        df: pd.DataFrame,
        indicators: Optional[List[Dict[str, Any]]] = None
    ) -> pd.DataFrame:
        """
        Compute technical indicators for the given price data using the MCP.
        
        Args:
            df: DataFrame containing price data with at least 'close' column
            indicators: Optional list of indicators to compute, each as a dict with
                       'name' and optional 'params'
                       
        Returns:
            DataFrame with added indicator columns
            
        Raises:
            ValueError: If required price data is missing or MCP connection fails
        """
        if df.empty:
            self._log.warning("Empty DataFrame provided, cannot compute indicators")
            return df
        
        if 'close' not in df.columns:
            raise ValueError("DataFrame must contain a 'close' column")
        
        # Default indicators if none provided
        if not indicators:
            indicators = [
                {'name': 'rsi', 'params': {'period': 14}},
                {'name': 'macd', 'params': {'fastPeriod': 12, 'slowPeriod': 26, 'signalPeriod': 9}},
                {'name': 'bollingerBands', 'params': {'period': 20, 'stdDev': 2.0}}
            ]
        
        try:
            # Ensure MCP client is connected
            await self._ensure_client_connected()
            
            # Extract close prices as a list
            close_prices = df['close'].tolist()
            
            # Create a copy of the DataFrame to add indicators to
            result_df = df.copy()
            
            # Compute each requested indicator
            for indicator in indicators:
                name = indicator['name'].lower()
                params = indicator.get('params', {})
                
                if name == 'rsi':
                    period = params.get('period', 14)
                    rsi_result = await self.mcp_client.calculate_rsi(
                        prices=close_prices,
                        period=period
                    )
                    result_df[f'rsi_{period}'] = pd.Series(rsi_result['values'])
                    
                elif name == 'macd':
                    fast_period = params.get('fastPeriod', 12)
                    slow_period = params.get('slowPeriod', 26)
                    signal_period = params.get('signalPeriod', 9)
                    
                    macd_result = await self.mcp_client.calculate_macd(
                        prices=close_prices,
                        fast_period=fast_period,
                        slow_period=slow_period,
                        signal_period=signal_period
                    )
                    
                    result_df['macd_line'] = pd.Series(macd_result['macdLine'])
                    result_df['macd_signal'] = pd.Series(macd_result['signalLine'])
                    result_df['macd_histogram'] = pd.Series(macd_result['histogram'])
                    
                elif name == 'bollingerbands' or name == 'bollinger_bands':
                    period = params.get('period', 20)
                    std_dev = params.get('stdDev', 2.0)
                    
                    bb_result = await self.mcp_client.calculate_bollinger_bands(
                        prices=close_prices,
                        period=period,
                        std_dev=std_dev
                    )
                    
                    result_df['bb_upper'] = pd.Series(bb_result['upperBand'])
                    result_df['bb_middle'] = pd.Series(bb_result['middleBand'])
                    result_df['bb_lower'] = pd.Series(bb_result['lowerBand'])
                    
                else:
                    self._log.warning(f"Unknown indicator: {name}")
            
            return result_df
            
        except Exception as e:
            self._log.error(f"Error computing indicators: {str(e)}")
            raise ValueError(f"Error computing indicators: {str(e)}")
    
    def to_database_format(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        user_id: str = DEFAULT_USER_ID,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Convert DataFrame with indicators to database format.
        
        Args:
            df: DataFrame containing price and indicator data
            symbol: Trading pair symbol
            timeframe: Timeframe
            user_id: User ID to associate with the data
            **kwargs: Additional keyword arguments
            
        Returns:
            List of dictionaries in database format
        """
        if df.empty:
            return []
        
        indicator_columns = [
            col for col in df.columns if col not in 
            ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        ]
        
        data_entries = []
        
        for _, row in df.iterrows():
            # Create indicators dictionary
            indicators = {}
            for col in indicator_columns:
                if pd.notna(row[col]):
                    indicators[col] = float(row[col])
            
            # Create entry
            entry = {
                'user_id': user_id,
                'symbol': symbol,
                'timeframe': timeframe,
                'source': 'indicators_mcp',
                'data_type': 'indicators',
                'indicators': indicators,
                'raw_data': {},
                'updated_at': datetime.now()
            }
            
            data_entries.append(entry)
        
        return data_entries