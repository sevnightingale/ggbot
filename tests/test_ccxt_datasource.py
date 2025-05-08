"""
Test script for the CCXT MCP data source.

This script demonstrates how to use the CCXT MCP data source to fetch
market data from cryptocurrency exchanges using environment-based credentials.
"""

import os
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from pprint import pprint

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extraction.sources.exchange_api.ccxt_mcp_datasource import CCXTMCPDataSource
from extraction.interfaces.data_source import DataTimeframe


async def fetch_and_display_ticker(datasource, symbol):
    """Fetch and display ticker data for a symbol."""
    print(f"\n=== Fetching ticker for {symbol} ===")
    ticker = await datasource.get_ticker(symbol)
    
    if ticker:
        # Display a subset of the ticker data
        print(f"Last Price: {ticker.get('last')}")
        print(f"Bid/Ask: {ticker.get('bid')}/{ticker.get('ask')}")
        print(f"24h Volume: {ticker.get('quoteVolume')} {symbol.split('/')[1]}")
        print(f"24h Change: {ticker.get('percentage')}%")
    else:
        print(f"Failed to retrieve ticker for {symbol}")


async def fetch_and_display_ohlcv(datasource, symbol, timeframe, limit=10):
    """Fetch and display OHLCV data for a symbol."""
    print(f"\n=== Fetching {timeframe} OHLCV for {symbol} (last {limit} candles) ===")
    candles = await datasource.get_ohlcv(symbol, timeframe, limit=limit)
    
    if candles:
        # Display the candles in a table format
        print(f"{'Date/Time':<20} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<15}")
        print("-" * 80)
        
        for candle in candles[-5:]:  # Show only the last 5 candles for brevity
            dt = candle['datetime']
            print(f"{dt.strftime('%Y-%m-%d %H:%M'):<20} "
                  f"{candle['open']:<10.2f} "
                  f"{candle['high']:<10.2f} "
                  f"{candle['low']:<10.2f} "
                  f"{candle['close']:<10.2f} "
                  f"{candle['volume']:<15.2f}")
    else:
        print(f"Failed to retrieve OHLCV data for {symbol}")


async def main():
    """Run the CCXT MCP data source test."""
    print("=== CCXT MCP Data Source Test ===")
    
    # Check environment variables
    missing_vars = []
    for var in ["EXCHANGE_NAME", "EXCHANGE_API", "EXCHANGE_SECRET"]:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please ensure these variables are set in the .env file or environment.")
        return
    
    # Get exchange ID from environment
    exchange_id = os.environ.get("EXCHANGE_NAME", "").lower()
    print(f"Using exchange: {exchange_id}")
    
    # Define test symbols
    # Note: These might need to be adjusted based on the exchange
    symbols = ["BTC/USDT", "ETH/USDT"]
    
    try:
        # Create and connect to the data source
        async with CCXTMCPDataSource(exchange_id=exchange_id) as datasource:
            print(f"Successfully connected to {exchange_id}")
            
            # List available symbols (placeholder in our implementation)
            available_symbols = await datasource.get_available_symbols()
            print(f"\nAvailable symbols: {', '.join(available_symbols[:5])}...")
            
            # Test fetching ticker data
            for symbol in symbols:
                await fetch_and_display_ticker(datasource, symbol)
            
            # Test fetching OHLCV data with different timeframes
            for tf in [DataTimeframe.MINUTE_5, DataTimeframe.HOUR_1, DataTimeframe.DAY_1]:
                await fetch_and_display_ohlcv(datasource, symbols[0], tf)
            
    except Exception as e:
        print(f"Error testing CCXT data source: {str(e)}")
    
    print("\nCCXT MCP Data Source Test Completed")


if __name__ == "__main__":
    asyncio.run(main())