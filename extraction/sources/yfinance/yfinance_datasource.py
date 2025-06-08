"""
YFinance Data Source

This module implements the DataSource interface for the Yahoo Finance API using the yfinance library.
It provides methods to fetch historical and current market data for various trading pairs and timeframes.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import yfinance as yf
import time

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from extraction.interfaces import DataSource


class YFinanceDataSource(DataSource):
    """
    Implementation of the DataSource interface using the yfinance library.
    
    This class provides methods to fetch historical and current market data from Yahoo Finance
    for various crypto and stock trading pairs. It converts Yahoo Finance intervals to our
    internal timeframe format and handles data validation and transformation.
    """
    
# This section removed as it was duplicated and replaced with TIMEFRAME_TO_INTERVAL
    
    # Maximum historical data periods for different timeframes
    # Based on yfinance limitations
    MAX_PERIODS = {
        '1m': 7,      # 7 days
        '2m': 60,     # 60 days
        '5m': 60,     # 60 days
        '15m': 60,    # 60 days
        '30m': 60,    # 60 days
        '60m': 730,   # 730 days
        '90m': 730,   # 730 days
        '1h': 730,    # 730 days (2 years)
        '2h': 730,    # 730 days
        '4h': 730,    # 730 days
        '1d': 10000,  # Max available
        '5d': 10000,  # Max available
        '1wk': 10000, # Max available
        '1mo': 10000, # Max available
        '3mo': 10000  # Max available
    }
    
    # Mapping between our timeframe format and yfinance interval format
    TIMEFRAME_TO_INTERVAL = {
        '1m': '1m',
        '2m': '2m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '60m',
        '2h': '2h',
        '4h': '4h',
        '1d': '1d',
        '1w': '1wk',
        '1mo': '1mo'
    }
    
    def __init__(self):
        """Initialize the YFinanceDataSource."""
        self._supported_symbols = [
            'BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD',
            'SOL-USD', 'DOGE-USD', 'MATIC-USD', 'DOT-USD', 'AVAX-USD'
        ]
        self._last_request_time = 0
        self._rate_limit_delay = 10.0  # 10 second delay between requests for testing to avoid rate limits
    
    def _apply_rate_limit(self):
        """Apply rate limiting between API requests."""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < self._rate_limit_delay:
            sleep_time = self._rate_limit_delay - time_since_last_request
            logger.bind(user_id=DEFAULT_USER_ID).debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
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
        interval = self.TIMEFRAME_TO_INTERVAL.get(timeframe, timeframe)
        
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
                # Use default values for days of history
                days_of_history = 60  # Default to 60 days
                
                # Respect yfinance limitations by timeframe
                # Override days_of_history if it exceeds yfinance limits
                max_days = self.MAX_PERIODS.get(timeframe, 60)
                days = min(days_of_history, max_days)
                start_date = end_date - timedelta(days=days)
                
                logger.bind(user_id=DEFAULT_USER_ID).info(
                    f"Using {days} days for {timeframe} data (max allowed: {max_days})"
                )
        
        try:
            logger.bind(user_id=DEFAULT_USER_ID).info(f"Fetching {symbol} {timeframe} data from {start_date.strftime('%Y-%m-%d %H:%M:%S')} to {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Apply rate limiting before making the request
            self._apply_rate_limit()
            
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
            # Apply rate limiting before making the request
            self._apply_rate_limit()
            
            ticker = yf.Ticker(symbol)
            
            # Use history instead of info to avoid rate limits - it's generally more reliable
            # Get the most recent day's data
            history_data = ticker.history(period='1d', interval='1m')
            
            if not history_data.empty:
                # Return the most recent close price
                return float(history_data['Close'].iloc[-1])
            
            # Fallback to daily data if minute data fails
            daily_data = ticker.history(period='2d')
            if not daily_data.empty:
                return float(daily_data['Close'].iloc[-1])
            
            # Last resort: try info API
            last_quote = ticker.info.get('regularMarketPrice')
            if last_quote:
                return float(last_quote)
            
            raise ValueError(f"No price data available for {symbol}")
        
        except Exception as e:
            logger.bind(user_id=DEFAULT_USER_ID).error(f"Error fetching current price for {symbol}: {str(e)}")
            raise ValueError(f"Unable to fetch current price for {symbol}: {str(e)}")
    
    def get_supported_timeframes(self) -> List[str]:
        """
        Get a list of timeframes supported by this data source.
        
        Returns:
            A list of supported timeframe strings
        """
        return list(self.TIMEFRAME_TO_INTERVAL.keys())
    
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