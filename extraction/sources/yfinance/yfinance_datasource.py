"""
YFinance Data Source

This module implements the DataSource interface for the Yahoo Finance API using the yfinance library.
It provides methods to fetch historical and current market data for various trading pairs and timeframes.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import yfinance as yf

from common.logger import logger
from common.config import DEFAULT_USER_ID
from extraction.interfaces import DataSource


class YFinanceDataSource(DataSource):
    """
    Implementation of the DataSource interface using the yfinance library.
    
    This class provides methods to fetch historical and current market data from Yahoo Finance
    for various crypto and stock trading pairs. It converts Yahoo Finance intervals to our
    internal timeframe format and handles data validation and transformation.
    """
    
    # Mapping from our timeframe format to yfinance intervals
    TIMEFRAME_MAP = {
        '1m': '1m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '1h',
        '2h': '2h',
        '4h': '4h',
        '1d': '1d',
        '1w': '1wk',
        '1mo': '1mo'
    }
    
    # Maximum historical data periods for different timeframes
    # Based on yfinance limitations
    MAX_PERIODS = {
        '1m': 7,      # 7 days
        '5m': 60,     # 60 days
        '15m': 60,    # 60 days
        '30m': 60,    # 60 days
        '1h': 730,    # 730 days (2 years)
        '2h': 730,    # 730 days
        '4h': 730,    # 730 days
        '1d': 10000,  # Max available
        '1w': 10000,  # Max available
        '1mo': 10000  # Max available
    }
    
    def __init__(self):
        """Initialize the YFinanceDataSource."""
        self._supported_symbols = [
            'BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD',
            'SOL-USD', 'DOGE-USD', 'MATIC-USD', 'DOT-USD', 'AVAX-USD'
        ]
    
    def get_historical_data(self, symbol: str, timeframe: str,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           limit: Optional[int] = None) -> pd.DataFrame:
        """
        Fetch historical OHLCV data for the specified symbol and timeframe.
        
        Args:
            symbol: The trading pair symbol (e.g., 'BTC-USD')
            timeframe: The timeframe for the data (e.g., '15m', '1h', '4h', '1d')
            start_date: The start date for the data (optional)
            end_date: The end date for the data (optional)
            limit: Maximum number of data points to fetch (optional)
            
        Returns:
            A pandas DataFrame with OHLCV data and DatetimeIndex
            
        Raises:
            ValueError: If the symbol or timeframe is not supported
        """
        # Validate inputs
        if symbol not in self.get_supported_symbols():
            raise ValueError(f"Symbol '{symbol}' is not supported")
        
        if timeframe not in self.get_supported_timeframes():
            raise ValueError(f"Timeframe '{timeframe}' is not supported")
        
        # Convert our timeframe to yfinance interval
        interval = self.TIMEFRAME_MAP[timeframe]
        
        # Calculate start and end dates if not provided
        if not end_date:
            end_date = datetime.now()
        
        if not start_date:
            # Calculate start date based on timeframe and limit
            if limit:
                # Convert limit to timedelta based on timeframe
                if timeframe == '1m':
                    start_date = end_date - timedelta(minutes=limit)
                elif timeframe == '5m':
                    start_date = end_date - timedelta(minutes=5 * limit)
                elif timeframe == '15m':
                    start_date = end_date - timedelta(minutes=15 * limit)
                elif timeframe == '30m':
                    start_date = end_date - timedelta(minutes=30 * limit)
                elif timeframe == '1h':
                    start_date = end_date - timedelta(hours=limit)
                elif timeframe == '2h':
                    start_date = end_date - timedelta(hours=2 * limit)
                elif timeframe == '4h':
                    start_date = end_date - timedelta(hours=4 * limit)
                elif timeframe == '1d':
                    start_date = end_date - timedelta(days=limit)
                elif timeframe == '1w':
                    start_date = end_date - timedelta(weeks=limit)
                elif timeframe == '1mo':
                    start_date = end_date - timedelta(days=30 * limit)
            else:
                # Use max period based on timeframe
                days = self.MAX_PERIODS.get(timeframe, 60)
                start_date = end_date - timedelta(days=days)
        
        try:
            logger.bind(user_id=DEFAULT_USER_ID).info(f"Fetching {symbol} {timeframe} data from {start_date} to {end_date}")
            df = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                interval=interval,
                progress=False
            )
            
            # Filter empty rows and ensure we have data
            df = df.dropna(how='all')
            
            if df.empty:
                logger.bind(user_id=DEFAULT_USER_ID).warning(f"No data returned for {symbol} with timeframe {timeframe}")
                return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
            
            # Apply limit if specified
            if limit and len(df) > limit:
                df = df.tail(limit)
            
            return df
        
        except Exception as e:
            logger.bind(user_id=DEFAULT_USER_ID).error(f"Error fetching historical data for {symbol}: {str(e)}")
            return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
    
    def get_latest_data(self, symbol: str, timeframe: str, limit: int = 1) -> pd.DataFrame:
        """
        Fetch the most recent OHLCV data points.
        
        Args:
            symbol: The trading pair symbol (e.g., 'BTC-USD')
            timeframe: The timeframe for the data (e.g., '15m', '1h', '4h', '1d')
            limit: Number of most recent data points to fetch (default: 1)
            
        Returns:
            A pandas DataFrame with the most recent OHLCV data
        """
        end_date = datetime.now()
        
        # Calculate start date based on timeframe and limit to get just enough data
        if timeframe == '1m':
            start_date = end_date - timedelta(minutes=limit * 2)  # Get extra to account for potential gaps
        elif timeframe == '5m':
            start_date = end_date - timedelta(minutes=5 * limit * 2)
        elif timeframe == '15m':
            start_date = end_date - timedelta(minutes=15 * limit * 2)
        elif timeframe == '30m':
            start_date = end_date - timedelta(minutes=30 * limit * 2)
        elif timeframe == '1h':
            start_date = end_date - timedelta(hours=limit * 2)
        elif timeframe == '2h':
            start_date = end_date - timedelta(hours=2 * limit * 2)
        elif timeframe == '4h':
            start_date = end_date - timedelta(hours=4 * limit * 2)
        elif timeframe == '1d':
            start_date = end_date - timedelta(days=limit * 2)
        elif timeframe == '1w':
            start_date = end_date - timedelta(weeks=limit * 2)
        elif timeframe == '1mo':
            start_date = end_date - timedelta(days=30 * limit * 2)
        else:
            # Default to 1 day
            start_date = end_date - timedelta(days=1)
        
        df = self.get_historical_data(symbol, timeframe, start_date, end_date)
        
        # Return the most recent 'limit' rows
        if not df.empty and len(df) > limit:
            return df.tail(limit)
        return df
    
    def get_current_price(self, symbol: str) -> float:
        """
        Get the current price for a symbol.
        
        Args:
            symbol: The trading pair symbol (e.g., 'BTC-USD')
            
        Returns:
            The current price as a float
            
        Raises:
            ValueError: If the symbol is not supported or if unable to fetch the price
        """
        if symbol not in self.get_supported_symbols():
            raise ValueError(f"Symbol '{symbol}' is not supported")
        
        try:
            ticker = yf.Ticker(symbol)
            # todays_data = ticker.history(period='1d')
            
            # Check if we have data for today
            # if not todays_data.empty:
            #     return float(todays_data['Close'].iloc[-1])
            
            # If no data for today, get the last available price
            last_quote = ticker.info.get('regularMarketPrice')
            if last_quote:
                return float(last_quote)
            
            # Fallback to last closing price if quote not available
            last_close = ticker.history(period='1d')['Close'].iloc[-1]
            return float(last_close)
        
        except Exception as e:
            logger.bind(user_id=DEFAULT_USER_ID).error(f"Error fetching current price for {symbol}: {str(e)}")
            raise ValueError(f"Unable to fetch current price for {symbol}: {str(e)}")
    
    def get_supported_timeframes(self) -> List[str]:
        """
        Get a list of timeframes supported by this data source.
        
        Returns:
            A list of supported timeframe strings
        """
        return list(self.TIMEFRAME_MAP.keys())
    
    def get_supported_symbols(self) -> List[str]:
        """
        Get a list of symbols supported by this data source.
        
        Returns:
            A list of supported symbol strings
        """
        return self._supported_symbols
    
    def get_source_name(self) -> str:
        """
        Get the name of this data source.
        
        Returns:
            The name of the data source
        """
        return 'yfinance'