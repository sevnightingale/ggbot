"""
DataSource Interface

This module defines the abstract interface that all data sources must implement.
Data sources are responsible for fetching market data (price, volume, etc.) from
various providers like YFinance, TradingView, or exchange APIs.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Union
import pandas as pd


class DataSource(ABC):
    """
    Abstract base class for all data source implementations.
    
    A DataSource is responsible for fetching market data for a specific trading pair
    and timeframe from a particular provider (YFinance, TradingView, exchange API, etc.).
    """
    
    @abstractmethod
    def get_historical_data(self, symbol: str, timeframe: str, 
                           start_date: Optional[datetime] = None, 
                           end_date: Optional[datetime] = None,
                           limit: Optional[int] = None) -> pd.DataFrame:
        """
        Fetch historical OHLCV (Open, High, Low, Close, Volume) data.
        
        Args:
            symbol: The trading pair symbol (e.g., 'BTC-USD')
            timeframe: The timeframe for the data (e.g., '15m', '1h', '4h', '1d')
            start_date: The start date for the data (optional)
            end_date: The end date for the data (optional)
            limit: Maximum number of data points to fetch (optional)
            
        Returns:
            A pandas DataFrame with OHLCV data and DatetimeIndex
        """
        pass
    
    @abstractmethod
    def get_latest_data(self, symbol: str, timeframe: str, 
                        limit: int = 1) -> pd.DataFrame:
        """
        Fetch the most recent OHLCV data points.
        
        Args:
            symbol: The trading pair symbol (e.g., 'BTC-USD')
            timeframe: The timeframe for the data (e.g., '15m', '1h', '4h', '1d')
            limit: Number of most recent data points to fetch (default: 1)
            
        Returns:
            A pandas DataFrame with the most recent OHLCV data
        """
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """
        Get the current price for a symbol.
        
        Args:
            symbol: The trading pair symbol (e.g., 'BTC-USD')
            
        Returns:
            The current price as a float
        """
        pass
    
    @abstractmethod
    def get_supported_timeframes(self) -> List[str]:
        """
        Get a list of timeframes supported by this data source.
        
        Returns:
            A list of supported timeframe strings (e.g., ['1m', '5m', '15m', '1h', '4h', '1d'])
        """
        pass
    
    @abstractmethod
    def get_supported_symbols(self) -> List[str]:
        """
        Get a list of symbols supported by this data source.
        
        Returns:
            A list of supported symbol strings
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """
        Get the name of this data source.
        
        Returns:
            The name of the data source (e.g., 'yfinance', 'tradingview', 'binance')
        """
        pass
    
    def to_database_format(self, df: pd.DataFrame, symbol: str, 
                          timeframe: str, user_id: str) -> List[Dict]:
        """
        Convert a DataFrame of OHLCV data to a format suitable for database storage.
        
        Args:
            df: The DataFrame containing OHLCV data
            symbol: The trading pair symbol
            timeframe: The timeframe of the data
            user_id: The user ID to associate with this data
            
        Returns:
            A list of dictionaries, each representing a row to insert in the database
        """
        result = []
        source_name = self.get_source_name()
        
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Handle multi-index columns (like from yfinance)
        if isinstance(df.columns, pd.MultiIndex):
            # Recent versions of yfinance return columns with structure:
            # MultiIndex([('Open', 'BTC-USD'),
            #             ('High', 'BTC-USD'),
            #             ('Low', 'BTC-USD'),
            #             ...])
            
            # Simplify to use only the first level (the price type)
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        
        # Ensure we have the required columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in DataFrame")
        
        for timestamp, row in df.iterrows():
            # Convert row to a standard format
            try:
                raw_data = {
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': float(row['Volume'])
                }
                
                # Add any additional columns that might be present
                for col in row.index:
                    if col not in required_columns:
                        # Skip non-numeric columns
                        try:
                            if pd.notnull(row[col]):
                                raw_data[str(col).lower()] = float(row[col])
                        except (ValueError, TypeError):
                            # Skip non-numeric values
                            pass
            except Exception as e:
                raise ValueError(f"Error converting row to database format: {str(e)}, row: {row}")
            
            data_entry = {
                'user_id': user_id,
                'source': source_name,
                'symbol': symbol,
                'timeframe': timeframe,
                'data_type': 'price_data',
                'raw_data': raw_data,
                'indicators': {},  # Will be filled by IndicatorComputer
                'updated_at': timestamp.to_pydatetime()
            }
            
            result.append(data_entry)
            
        return result
