"""
Test script for YFinanceDataSource and PandasTAIndicators.

This script demonstrates how to use the YFinanceDataSource and PandasTAIndicators
classes to fetch historical data, calculate technical indicators, and prepare it
for database storage.

Usage:
    python -m extraction.test_yfinance
"""
import json
from datetime import datetime, timedelta
import pandas as pd

from common.logger import logger
from extraction.sources import YFinanceDataSource
from extraction.indicators import PandasTAIndicators


def test_yfinance_datasource():
    """Test the YFinanceDataSource implementation."""
    data_source = YFinanceDataSource()
    
    # Print supported symbols and timeframes
    print(f"Supported symbols: {data_source.get_supported_symbols()}")
    print(f"Supported timeframes: {data_source.get_supported_timeframes()}")
    
    # Test getting current price
    symbol = "BTC-USD"
    try:
        current_price = data_source.get_current_price(symbol)
        print(f"Current price of {symbol}: ${current_price:.2f}")
    except Exception as e:
        print(f"Error getting current price: {str(e)}")
    
    # Test getting historical data
    timeframe = "1d"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    try:
        df = data_source.get_historical_data(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"\nHistorical data for {symbol} ({timeframe}):")
        print(f"Shape: {df.shape}")
        print(f"Date range: {df.index[0]} to {df.index[-1]}")
        
        # Debugging column structure
        print("\nColumn structure:")
        print(f"Type: {type(df.columns)}")
        if isinstance(df.columns, pd.MultiIndex):
            print("Multi-index columns:")
            for col in df.columns:
                print(f"  {col}")
        else:
            print(f"Columns: {list(df.columns)}")
        
        print("\nFirst 5 rows:")
        print(df.head())
        
        return df
    
    except Exception as e:
        print(f"Error getting historical data: {str(e)}")
        return None


def test_pandas_ta_indicators(df):
    """Test the PandasTAIndicators implementation."""
    if df is None or df.empty:
        print("No data available for calculating indicators")
        return None
    
    # Create an indicator computer with default configuration
    indicator_computer = PandasTAIndicators()
    
    # Print the indicator names and parameters
    print("\nAvailable indicators:")
    print(indicator_computer.get_indicator_names())
    
    print("\nIndicator parameters:")
    params = indicator_computer.get_indicator_parameters()
    print(json.dumps(params, indent=2, default=str))
    
    # Calculate indicators
    try:
        result_df = indicator_computer.compute_indicators(df)
        
        print(f"\nData with indicators:")
        print(f"Shape: {result_df.shape}")
        print("\nFirst 5 rows (indicators only):")
        indicator_cols = [col for col in result_df.columns if col not in ['Open', 'High', 'Low', 'Close', 'Volume']]
        print(result_df[indicator_cols].head())
        
        return result_df
    
    except Exception as e:
        print(f"Error calculating indicators: {str(e)}")
        return None


def test_database_format(df, symbol, timeframe):
    """Test converting data to database format."""
    if df is None or df.empty:
        print("No data available for database formatting")
        return
    
    # Create data source and indicator computer
    data_source = YFinanceDataSource()
    indicator_computer = PandasTAIndicators()
    
    # Use a dummy user_id for testing
    user_id = "00000000-0000-0000-0000-000000000001"
    
    # Debug the DataFrame before conversion
    print("\nPreparing data for database format...")
    print(f"DataFrame shape: {df.shape}")
    print(f"Column structure: {type(df.columns)}")
    
    if isinstance(df.columns, pd.MultiIndex):
        print("Multi-index columns before conversion:")
        for col in df.columns:
            print(f"  {col}")
    else:
        print(f"Columns before conversion: {list(df.columns)}")
    
    # Convert to database format
    try:
        print("\nConverting to database format...")
        data_entries = data_source.to_database_format(df, symbol, timeframe, user_id)
        data_entries = indicator_computer.to_database_format(df, data_entries)
        
        print(f"\nDatabase entries ({len(data_entries)} rows):")
        print("First entry:")
        formatted_entry = json.dumps(data_entries[0], indent=2, default=str)
        print(formatted_entry)
    except Exception as e:
        print(f"Error converting to database format: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Main function to run all tests."""
    print("=== Testing YFinanceDataSource ===")
    df = test_yfinance_datasource()
    
    if df is not None:
        print("\n=== Testing PandasTAIndicators ===")
        df_with_indicators = test_pandas_ta_indicators(df)
        
        if df_with_indicators is not None:
            print("\n=== Testing Database Format Conversion ===")
            test_database_format(df_with_indicators, "BTC-USD", "1d")


if __name__ == "__main__":
    main()