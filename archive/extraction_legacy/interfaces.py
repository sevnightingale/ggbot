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
"""
IndicatorComputer Interface

This module defines the abstract interface that all indicator computers must implement.
IndicatorComputers are responsible for calculating technical indicators (SMA, EMA, RSI, etc.)
based on price data provided by DataSource implementations.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any
import pandas as pd


class IndicatorComputer(ABC):
    """
    Abstract base class for all indicator computer implementations.
    
    An IndicatorComputer is responsible for calculating technical indicators
    based on price data from DataSource implementations.
    """
    
    @abstractmethod
    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for the given price data.
        
        Args:
            df: A pandas DataFrame containing OHLCV data
                (must have columns: Open, High, Low, Close, Volume)
            
        Returns:
            A pandas DataFrame with the original data plus calculated indicators
        """
        pass
    
    @abstractmethod
    def get_indicator_names(self) -> List[str]:
        """
        Get a list of all indicators that this computer can calculate.
        
        Returns:
            A list of indicator names
        """
        pass
    
    @abstractmethod
    def get_indicator_parameters(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the parameters used for each indicator.
        
        Returns:
            A dictionary mapping indicator names to their parameters
            Example: {'SMA': {'window': 20}, 'RSI': {'length': 14}}
        """
        pass
    
    @abstractmethod
    def get_required_columns(self) -> List[str]:
        """
        Get the required columns from the DataFrame for computing indicators.
        
        Returns:
            A list of required column names (e.g., ['Open', 'High', 'Low', 'Close', 'Volume'])
        """
        pass
    
    def extract_indicators_from_dataframe(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Extract indicators from the DataFrame to a dictionary format suitable for database storage.
        
        Args:
            df: A pandas DataFrame containing OHLCV data and calculated indicators
            
        Returns:
            A dictionary mapping timestamps to indicator values
            Example: {
                '2023-01-01 00:00:00': {'SMA_20': 50000, 'RSI_14': 65},
                '2023-01-01 01:00:00': {'SMA_20': 51000, 'RSI_14': 70}
            }
        """
        result = {}
        indicator_columns = [col for col in df.columns if col not in ['Open', 'High', 'Low', 'Close', 'Volume']]
        
        for timestamp, row in df.iterrows():
            indicator_values = {}
            for col in indicator_columns:
                if pd.notnull(row[col]):
                    indicator_values[col] = float(row[col])
            
            if indicator_values:
                result[str(timestamp)] = indicator_values
        
        return result
    
    def to_database_format(self, df: pd.DataFrame, data_entries: List[Dict]) -> List[Dict]:
        """
        Update a list of data entries with calculated indicators.
        
        Args:
            df: The DataFrame containing OHLCV data and calculated indicators
            data_entries: List of data entry dictionaries to update with indicators
                (as returned by DataSource.to_database_format)
            
        Returns:
            The updated list of data entries
        """
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Handle multi-index columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        
        # Extract indicators from the DataFrame
        ohlcv_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']
        indicator_columns = [col for col in df.columns if col not in ohlcv_columns]
        
        indicators_by_timestamp = {}
        
        for timestamp, row in df.iterrows():
            timestamp_str = str(timestamp)
            indicators_by_timestamp[timestamp_str] = {}
            
            for col in indicator_columns:
                try:
                    value = row[col]
                    if pd.notnull(value):
                        indicators_by_timestamp[timestamp_str][col] = float(value)
                except (ValueError, TypeError, KeyError) as e:
                    # Skip problematic values
                    pass
        
        # Update data entries with indicators
        for entry in data_entries:
            timestamp_str = str(entry['updated_at'])
            if timestamp_str in indicators_by_timestamp:
                entry['indicators'] = indicators_by_timestamp[timestamp_str]
        
        return data_entries
