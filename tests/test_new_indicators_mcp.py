#!/usr/bin/env python
"""
Test script for the Crypto Indicators MCP client.

This script tests the connectivity and functionality of the Crypto Indicators MCP client.
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_indicators_mcp")

# Import the client
from core.mcp.indicators_client import IndicatorsMCPClient

async def main():
    """Main test function."""
    logger.info("Testing Crypto Indicators MCP client")
    
    # Create a test user ID
    user_id = "00000000-0000-0000-0000-000000000001"
    
    # Generate sample price data
    sample_prices = [
        100.0, 102.0, 104.0, 103.0, 105.0, 107.0, 105.0, 106.0, 108.0, 107.0,
        109.0, 110.0, 111.0, 112.0, 111.0, 110.0, 112.0, 114.0, 116.0, 115.0,
        117.0, 118.0, 120.0, 119.0, 121.0, 122.0, 124.0, 123.0, 125.0, 126.0
    ]
    
    # Use the client as a context manager
    async with IndicatorsMCPClient(user_id=user_id) as client:
        # Load configuration
        try:
            await client.load_config()
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load configuration: {e}")
            logger.info("Continuing with default configuration")
        
        try:
            # Get available indicators
            indicators = await client.get_available_indicators()
            logger.info(f"Available indicators: {indicators}")
            
            # Test RSI calculation
            logger.info("Testing RSI calculation")
            rsi_result = await client.calculate_rsi(sample_prices, period=14)
            logger.info(f"RSI result: {rsi_result}")
            
            # Test MACD calculation
            logger.info("Testing MACD calculation")
            macd_result = await client.calculate_macd(
                sample_prices, 
                fast_period=12, 
                slow_period=26, 
                signal_period=9
            )
            logger.info(f"MACD result: {macd_result}")
            
            # Test Bollinger Bands calculation
            logger.info("Testing Bollinger Bands calculation")
            bb_result = await client.calculate_bollinger_bands(
                sample_prices, 
                period=20, 
                std_dev=2.0
            )
            logger.info(f"Bollinger Bands result: {bb_result}")
            
            # Test strategy analysis
            logger.info("Testing strategy analysis")
            strategy_result = await client.analyze_with_strategy(
                sample_prices,
                strategy="trend_following",
                params={
                    "short_period": 9,
                    "long_period": 21
                }
            )
            logger.info(f"Strategy analysis result: {strategy_result}")
            
            logger.info("All tests completed successfully!")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            raise
        
        logger.info("Disconnecting from MCP server")

if __name__ == "__main__":
    asyncio.run(main())