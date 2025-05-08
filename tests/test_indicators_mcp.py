#!/usr/bin/env python
"""
Test script for the Crypto Indicators MCP.

This script tests connectivity and functionality of the Crypto Indicators MCP,
including calculating various technical indicators and comparing results with pandas-ta.
"""

import os
import asyncio
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from pprint import pprint

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mcp.indicators import IndicatorsMCPClient
from extraction.indicators.pandas_ta_indicators import PandasTaIndicators


class TestIndicatorsMCP:
    """Test case for the Crypto Indicators MCP."""
    
    def __init__(self):
        self.client = None
        self.sample_prices = None
        self.load_sample_data()
    
    def load_sample_data(self):
        """Load sample price data for testing."""
        # Generate sample price data if it doesn't exist
        if not os.path.exists('tests/test_prices.json'):
            # Generate a simple price series with some trend and volatility
            np.random.seed(42)  # For reproducibility
            base = 10000.0
            price = base
            prices = []
            for i in range(100):
                # Add a slight upward trend with random noise
                change = np.random.normal(0.001, 0.02)
                price *= (1 + change)
                prices.append(price)
            
            # Save to file for future tests
            with open('tests/test_prices.json', 'w') as f:
                json.dump(prices, f)
            
            self.sample_prices = prices
        else:
            # Load existing sample data
            with open('tests/test_prices.json', 'r') as f:
                self.sample_prices = json.load(f)
    
    async def setup(self):
        """Set up the test by connecting to the MCP."""
        print("Connecting to Crypto Indicators MCP...")
        self.client = IndicatorsMCPClient()
        await self.client.connect()
        print("Connected successfully!")
    
    async def teardown(self):
        """Clean up by disconnecting from the MCP."""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            print("Disconnected from Crypto Indicators MCP")
    
    async def test_available_indicators(self):
        """Test getting available indicators from the MCP."""
        print("\n=== Testing Available Indicators ===")
        indicators = await self.client.get_available_indicators()
        print(f"Available indicators: {indicators}")
        assert len(indicators) > 0, "No indicators returned from MCP"
    
    async def test_rsi(self):
        """Test calculating RSI using the MCP and compare with pandas-ta."""
        print("\n=== Testing RSI Calculation ===")
        
        # Calculate RSI using MCP
        print("Calculating RSI using MCP...")
        mcp_rsi = await self.client.calculate_rsi(self.sample_prices, period=14)
        
        # Calculate RSI using pandas-ta
        print("Calculating RSI using pandas-ta...")
        df = pd.DataFrame({"close": self.sample_prices})
        pandas_ta_indicators = PandasTaIndicators()
        pandas_ta_rsi = pandas_ta_indicators.calculate_rsi(df, period=14)
        
        # Compare results
        mcp_last = mcp_rsi['values'][-1] if 'values' in mcp_rsi else None
        pandas_last = pandas_ta_rsi['RSI_14'].dropna().iloc[-1] if 'RSI_14' in pandas_ta_rsi else None
        
        print(f"MCP RSI (last value): {mcp_last:.2f}")
        print(f"pandas-ta RSI (last value): {pandas_last:.2f}")
        
        if mcp_last is not None and pandas_last is not None:
            # Check if values are close (within 1%)
            diff = abs(mcp_last - pandas_last) / pandas_last
            print(f"Difference: {diff:.4f} ({diff*100:.2f}%)")
            assert diff < 0.01, f"RSI values differ significantly: {mcp_last:.2f} vs {pandas_last:.2f}"
    
    async def test_macd(self):
        """Test calculating MACD using the MCP and compare with pandas-ta."""
        print("\n=== Testing MACD Calculation ===")
        
        # Calculate MACD using MCP
        print("Calculating MACD using MCP...")
        mcp_macd = await self.client.calculate_macd(
            self.sample_prices, 
            fast_period=12,
            slow_period=26,
            signal_period=9
        )
        
        # Calculate MACD using pandas-ta
        print("Calculating MACD using pandas-ta...")
        df = pd.DataFrame({"close": self.sample_prices})
        pandas_ta_indicators = PandasTaIndicators()
        pandas_ta_macd = pandas_ta_indicators.calculate_macd(
            df, 
            fast_period=12,
            slow_period=26,
            signal_period=9
        )
        
        # Compare results (just the MACD line for simplicity)
        mcp_last = mcp_macd['macdLine'][-1] if 'macdLine' in mcp_macd else None
        pandas_last = pandas_ta_macd['MACD_12_26_9'].dropna().iloc[-1] if 'MACD_12_26_9' in pandas_ta_macd else None
        
        print(f"MCP MACD line (last value): {mcp_last:.2f}")
        print(f"pandas-ta MACD line (last value): {pandas_last:.2f}")
        
        if mcp_last is not None and pandas_last is not None:
            # Check if values are close (within 1%)
            diff = abs(mcp_last - pandas_last) / (abs(pandas_last) + 1e-10)  # Avoid division by zero
            print(f"Difference: {diff:.4f} ({diff*100:.2f}%)")
            assert diff < 0.01, f"MACD values differ significantly: {mcp_last:.2f} vs {pandas_last:.2f}"
    
    async def test_bollinger_bands(self):
        """Test calculating Bollinger Bands using the MCP and compare with pandas-ta."""
        print("\n=== Testing Bollinger Bands Calculation ===")
        
        # Calculate Bollinger Bands using MCP
        print("Calculating Bollinger Bands using MCP...")
        mcp_bb = await self.client.calculate_bollinger_bands(
            self.sample_prices, 
            period=20,
            std_dev=2.0
        )
        
        # Calculate Bollinger Bands using pandas-ta
        print("Calculating Bollinger Bands using pandas-ta...")
        df = pd.DataFrame({"close": self.sample_prices})
        pandas_ta_indicators = PandasTaIndicators()
        pandas_ta_bb = pandas_ta_indicators.calculate_bollinger_bands(
            df, 
            period=20,
            std_dev=2.0
        )
        
        # Compare results (middle band for simplicity)
        mcp_last = mcp_bb['middleBand'][-1] if 'middleBand' in mcp_bb else None
        pandas_last = pandas_ta_bb['BBM_20_2.0'].dropna().iloc[-1] if 'BBM_20_2.0' in pandas_ta_bb else None
        
        print(f"MCP BB middle band (last value): {mcp_last:.2f}")
        print(f"pandas-ta BB middle band (last value): {pandas_last:.2f}")
        
        if mcp_last is not None and pandas_last is not None:
            # Check if values are close (within 1%)
            diff = abs(mcp_last - pandas_last) / pandas_last
            print(f"Difference: {diff:.4f} ({diff*100:.2f}%)")
            assert diff < 0.01, f"Bollinger Band values differ significantly: {mcp_last:.2f} vs {pandas_last:.2f}"
    
    async def test_strategy(self):
        """Test analyzing price data with a strategy."""
        print("\n=== Testing Strategy Analysis ===")
        
        try:
            result = await self.client.analyze_with_strategy(
                self.sample_prices,
                strategy="trendFollowing",
                params={
                    "shortPeriod": 9,
                    "longPeriod": 21
                }
            )
            
            print("Strategy analysis result:")
            print(f"Signal: {result.get('signal')}")
            print(f"Strength: {result.get('strength')}")
            print(f"Reasoning: {result.get('reasoning')}")
            
            assert 'signal' in result, "Strategy analysis should return a signal"
            assert result['signal'] in ['buy', 'sell', 'neutral'], f"Invalid signal: {result.get('signal')}"
        except Exception as e:
            print(f"Strategy analysis test failed: {str(e)}")
            raise

    async def run_all_tests(self):
        """Run all the tests."""
        try:
            await self.setup()
            
            # Run tests
            await self.test_available_indicators()
            await self.test_rsi()
            await self.test_macd()
            await self.test_bollinger_bands()
            await self.test_strategy()
            
            print("\n=== All tests completed successfully! ===")
        except Exception as e:
            print(f"\n=== Test failed: {str(e)} ===")
            raise
        finally:
            await self.teardown()


async def main():
    """Main entry point."""
    tester = TestIndicatorsMCP()
    await tester.run_all_tests()


if __name__ == "__main__":
    print("Running Crypto Indicators MCP tests...")
    asyncio.run(main())