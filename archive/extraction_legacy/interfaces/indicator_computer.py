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
