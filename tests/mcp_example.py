"""
Example script demonstrating the use of MCP clients.

This script provides examples of how to use both the CCXT MCP client and
the Crypto Indicators MCP client to fetch market data and compute technical indicators.
"""

import os
import sys
import asyncio
import pandas as pd
from datetime import datetime, timedelta

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from core.common.logger import logger
from core.mcp.ccxt import CCXTMCPClient
from core.mcp.indicators import IndicatorsMCPClient
from extraction.sources.ccxt_mcp import CCXTMCPDataSource
from extraction.sources.indicators_mcp import IndicatorsMCPDataSource


async def demo_ccxt_mcp():
    """Demonstrate basic CCXT MCP client functionality."""
    print("\n=== CCXT MCP Client Demo ===")
    
    # Initialize CCXT MCP client
    client = CCXTMCPClient()
    
    try:
        # Connect to CCXT MCP server
        session = await client.connect()
        print("Connected to CCXT MCP server")
        
        # Get supported exchanges
        exchange_ids = await client.get_exchange_ids()
        print(f"Supported exchanges: {', '.join(exchange_ids[:10])}... (total: {len(exchange_ids)})")
        
        # Fetch ticker data for BTC/USDT on Binance
        ticker = await client.fetch_ticker('binance', 'BTC/USDT')
        print(f"BTC/USDT ticker on Binance:")
        print(f"  Last price: {ticker.get('last')}")
        print(f"  24h high: {ticker.get('high')}")
        print(f"  24h low: {ticker.get('low')}")
        print(f"  24h volume: {ticker.get('volume')}")
        
        # Fetch OHLCV data for BTC/USDT on Binance
        ohlcv = await client.fetch_ohlcv('binance', 'BTC/USDT', timeframe='1h', limit=5)
        print(f"\nRecent BTC/USDT hourly candles on Binance:")
        for candle in ohlcv:
            candle_time = datetime.fromtimestamp(candle[0] / 1000).strftime('%Y-%m-%d %H:%M')
            print(f"  {candle_time}: Open={candle[1]}, High={candle[2]}, Low={candle[3]}, Close={candle[4]}, Volume={candle[5]}")
    
    except Exception as e:
        print(f"Error in CCXT MCP demo: {str(e)}")
    
    finally:
        # Disconnect from CCXT MCP server
        await client.disconnect()
        print("Disconnected from CCXT MCP server")


async def demo_indicators_mcp():
    """Demonstrate basic Crypto Indicators MCP client functionality."""
    print("\n=== Crypto Indicators MCP Client Demo ===")
    
    # Sample price data for demonstrations
    sample_prices = [
        100.0, 102.0, 104.0, 103.0, 105.0, 107.0, 108.0, 107.0, 105.0, 104.0,
        103.0, 104.0, 105.0, 106.0, 107.0, 106.0, 105.0, 104.0, 103.0, 102.0,
        101.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0
    ]
    
    # Initialize Indicators MCP client
    client = IndicatorsMCPClient()
    
    try:
        # Connect to Indicators MCP server
        session = await client.connect()
        print("Connected to Crypto Indicators MCP server")
        
        # Get available indicators
        indicators = await client.get_available_indicators()
        print(f"Available indicators: {', '.join(indicators)}")
        
        # Calculate RSI
        rsi_result = await client.calculate_rsi(sample_prices, period=14)
        print(f"\nRSI (period=14):")
        print(f"  Last 5 values: {rsi_result['values'][-5:]}")
        
        # Calculate MACD
        macd_result = await client.calculate_macd(
            sample_prices, 
            fast_period=12, 
            slow_period=26, 
            signal_period=9
        )
        print(f"\nMACD:")
        print(f"  Last MACD line value: {macd_result['macdLine'][-1]}")
        print(f"  Last signal line value: {macd_result['signalLine'][-1]}")
        print(f"  Last histogram value: {macd_result['histogram'][-1]}")
        
        # Calculate Bollinger Bands
        bb_result = await client.calculate_bollinger_bands(
            sample_prices, 
            period=20, 
            std_dev=2.0
        )
        print(f"\nBollinger Bands (period=20, stdDev=2.0):")
        print(f"  Last upper band value: {bb_result['upperBand'][-1]}")
        print(f"  Last middle band value: {bb_result['middleBand'][-1]}")
        print(f"  Last lower band value: {bb_result['lowerBand'][-1]}")
    
    except Exception as e:
        print(f"Error in Crypto Indicators MCP demo: {str(e)}")
    
    finally:
        # Disconnect from Indicators MCP server
        await client.disconnect()
        print("Disconnected from Crypto Indicators MCP server")


async def demo_data_sources():
    """Demonstrate the use of MCP-based DataSource implementations."""
    print("\n=== MCP DataSource Integration Demo ===")
    
    # Define date range for historical data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)  # Last 24 hours
    
    try:
        # Initialize CCXT MCP DataSource
        ccxt_ds = CCXTMCPDataSource(exchange_id='binance')
        print("Initialized CCXT MCP DataSource")
        
        # Fetch historical data
        print(f"Fetching historical data for BTC/USDT (1h) from Binance via CCXT MCP...")
        df = ccxt_ds.get_historical_data(
            symbol='BTC/USDT',
            timeframe='1h',
            start_date=start_date,
            end_date=end_date
        )
        print(f"Retrieved {len(df)} candles")
        
        if not df.empty:
            print("\nSample data:")
            print(df.head(3))
            
            # Convert to database format
            db_entries = ccxt_ds.to_database_format(
                df=df,
                symbol='BTC/USDT',
                timeframe='1h'
            )
            print(f"\nConverted to {len(db_entries)} database entries")
        
        # Initialize Indicators MCP DataSource
        print("\nInitializing Indicators MCP DataSource...")
        indicators_ds = IndicatorsMCPDataSource()
        
        # Since the Indicators MCP DataSource requires price data from another source,
        # we'll create a sample DataFrame to demonstrate
        
        # Create asyncio event loop for async calls
        loop = asyncio.get_event_loop()
        
        if not df.empty:
            print("Computing indicators using Indicators MCP...")
            
            # Call the async compute_indicators method
            df_with_indicators = loop.run_until_complete(
                indicators_ds.compute_indicators(
                    df=df,
                    indicators=[
                        {'name': 'rsi', 'params': {'period': 14}},
                        {'name': 'macd', 'params': {}},
                        {'name': 'bollingerBands', 'params': {}}
                    ]
                )
            )
            
            print("\nSample data with indicators:")
            print(df_with_indicators.head(3))
            
            # Convert to database format
            db_entries = indicators_ds.to_database_format(
                df=df_with_indicators,
                symbol='BTC/USDT',
                timeframe='1h'
            )
            print(f"\nConverted to {len(db_entries)} database entries")
    
    except Exception as e:
        print(f"Error in MCP DataSource demo: {str(e)}")


async def main():
    """Main function to run all demos."""
    try:
        await demo_ccxt_mcp()
        await demo_indicators_mcp()
        await demo_data_sources()
    except Exception as e:
        print(f"Error in main: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())