#!/usr/bin/env python
"""
MCP Integration test script.

This script tests the integration of both CCXT and Indicators MCP clients,
verifying they can work together for a complete workflow.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import necessary components
from core.mcp.ccxt import CCXTMCPClient
from core.mcp.indicators import IndicatorsMCPClient
from core.common.logger import logger

# Test data
sample_prices = []  # Will be populated from OHLCV data

async def setup_test_data():
    """Fetch test data for the indicator calculations."""
    global sample_prices
    
    print("Setting up test data from CCXT...")
    
    exchange_id = "binance"
    symbol = "BTC/USDT"
    timeframe = "1h"
    limit = 50  # Get 50 candles for reliable indicator calculation
    
    ccxt_client = CCXTMCPClient()
    try:
        await ccxt_client.connect()
        print(f"Fetching OHLCV data for {symbol} on {exchange_id}...")
        candles = await ccxt_client.fetch_ohlcv(
            exchange_id, symbol, timeframe=timeframe, limit=limit
        )
        
        # Extract close prices
        sample_prices = [candle[4] for candle in candles]  # 4 = close price index
        print(f"Got {len(sample_prices)} close prices for indicator calculations")
        
        # Save to file for later use
        with open(Path(__file__).parent / "test_prices.json", "w") as f:
            json.dump(sample_prices, f)
            
        return True
    except Exception as e:
        print(f"Failed to get test data: {type(e).__name__}: {str(e)}")
        return False
    finally:
        if ccxt_client.is_connected:
            await ccxt_client.disconnect()

async def load_test_data():
    """Load test data from file if available."""
    global sample_prices
    
    data_file = Path(__file__).parent / "test_prices.json"
    if data_file.exists():
        try:
            with open(data_file, "r") as f:
                sample_prices = json.load(f)
            print(f"Loaded {len(sample_prices)} prices from file")
            return True
        except Exception as e:
            print(f"Error loading test data: {str(e)}")
            return False
    return False

async def test_indicators():
    """Test indicator calculations."""
    
    if not sample_prices or len(sample_prices) < 30:
        print("Not enough price data for indicators test")
        return False
        
    print("\nTesting crypto indicators...")
    indicators_client = IndicatorsMCPClient()
    
    try:
        await indicators_client.connect()
        
        # Calculate RSI
        print("Calculating RSI...")
        rsi_result = await indicators_client.calculate_rsi(sample_prices)
        print(f"RSI result: {rsi_result['rsi'][-5:]} (showing last 5 values)")
        
        # Calculate MACD
        print("\nCalculating MACD...")
        macd_result = await indicators_client.calculate_macd(sample_prices)
        print(f"MACD line (last 5): {macd_result['macd'][-5:]}")
        print(f"Signal line (last 5): {macd_result['signal'][-5:]}")
        print(f"Histogram (last 5): {macd_result['histogram'][-5:]}")
        
        # Calculate Bollinger Bands
        print("\nCalculating Bollinger Bands...")
        bb_result = await indicators_client.calculate_bollinger_bands(sample_prices)
        print(f"Upper band (last 5): {bb_result['upper'][-5:]}")
        print(f"Middle band (last 5): {bb_result['middle'][-5:]}")
        print(f"Lower band (last 5): {bb_result['lower'][-5:]}")
        
        return True
    except Exception as e:
        print(f"Indicators test failed: {type(e).__name__}: {str(e)}")
        return False
    finally:
        if indicators_client.is_connected:
            await indicators_client.disconnect()
            print("Disconnected from Indicators MCP server")

async def test_integration_workflow():
    """Test a complete workflow integrating both clients."""
    print("\nTesting integration workflow...")
    
    # Initialize clients
    ccxt_client = CCXTMCPClient()
    indicators_client = IndicatorsMCPClient()
    
    try:
        # Connect to both clients
        print("Connecting to both MCP services...")
        await ccxt_client.connect()
        await indicators_client.connect()
        
        # Fetch live market data
        exchange_id = "binance"
        symbol = "ETH/USDT"
        timeframe = "15m"
        limit = 30
        
        print(f"Fetching recent {timeframe} data for {symbol}...")
        candles = await ccxt_client.fetch_ohlcv(
            exchange_id, symbol, timeframe=timeframe, limit=limit
        )
        
        # Extract price data
        close_prices = [candle[4] for candle in candles]
        high_prices = [candle[2] for candle in candles]
        low_prices = [candle[3] for candle in candles]
        
        # Calculate technical indicators
        print("Calculating technical indicators...")
        rsi = await indicators_client.calculate_rsi(close_prices)
        macd = await indicators_client.calculate_macd(close_prices)
        bollinger = await indicators_client.calculate_bollinger_bands(close_prices)
        
        # Generate a sample trade signal
        latest_rsi = rsi['rsi'][-1]
        latest_macd = macd['histogram'][-1]
        latest_close = close_prices[-1]
        latest_upper_band = bollinger['upper'][-1]
        latest_lower_band = bollinger['lower'][-1]
        
        # Simple trading logic for demonstration
        signal = "HOLD"
        if latest_rsi < 30 and latest_macd > 0 and latest_close < latest_lower_band:
            signal = "BUY"
        elif latest_rsi > 70 and latest_macd < 0 and latest_close > latest_upper_band:
            signal = "SELL"
            
        print("\n----- Market Analysis -----")
        print(f"Symbol: {symbol}")
        print(f"Current price: {latest_close}")
        print(f"RSI: {latest_rsi:.2f}")
        print(f"MACD Histogram: {latest_macd:.6f}")
        print(f"BB Upper: {latest_upper_band:.2f}")
        print(f"BB Lower: {latest_lower_band:.2f}")
        print(f"Signal: {signal}")
        
        return True
    except Exception as e:
        print(f"Integration workflow failed: {type(e).__name__}: {str(e)}")
        return False
    finally:
        # Disconnect from both clients
        tasks = []
        if ccxt_client.is_connected:
            tasks.append(ccxt_client.disconnect())
        if indicators_client.is_connected:
            tasks.append(indicators_client.disconnect())
            
        if tasks:
            await asyncio.gather(*tasks)
            print("Disconnected from all MCP servers")

async def main():
    """Main function to run all tests."""
    print("Starting MCP integration tests...\n")
    
    # Load or setup test data
    if not await load_test_data():
        print("No test data found, fetching from exchange...")
        await setup_test_data()
    
    # Run tests
    indicators_success = await test_indicators()
    integration_success = await test_integration_workflow()
    
    # Print summary
    print("\n----- Test Results -----")
    print(f"Indicators test: {'PASSED' if indicators_success else 'FAILED'}")
    print(f"Integration workflow: {'PASSED' if integration_success else 'FAILED'}")
    
    # Overall result
    all_passed = all([indicators_success, integration_success])
    print("\nOverall result:", "PASSED" if all_passed else "FAILED")

if __name__ == "__main__":
    asyncio.run(main())