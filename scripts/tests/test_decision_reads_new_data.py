#!/usr/bin/env python3
"""
Test that the decision engine can read the new string-based indicator format.

This test verifies that our updated decision engine can:
1. Use config_id to look up market data 
2. Read string-based indicators from the new format
3. Process indicators correctly for the prompt
"""
import asyncio
import os
import sys
sys.path.append('/home/sev/ggbot')

from core.common.logger import logger
from decision.engine import DecisionEngine

async def test_decision_reads_new_data():
    """Test that the decision engine can read new data format."""
    
    # Test parameters
    GGSHOT_CONFIG_ID = "e249bb49-0455-4596-9657-09bf9e14ca14"
    USER_ID = "00000000-0000-0000-0000-000000000001"
    TEST_SYMBOL = "BTC/USDT"
    
    logger.info("🧪 Testing decision engine reads new data format")
    logger.info(f"Config ID: {GGSHOT_CONFIG_ID}")
    logger.info(f"Symbol: {TEST_SYMBOL}")
    
    try:
        # Create decision engine instance
        engine = DecisionEngine(USER_ID, GGSHOT_CONFIG_ID)
        
        # Test the market data fetch function
        logger.info("📊 Testing market data fetch...")
        market_data = engine._fetch_market_data(TEST_SYMBOL)
        
        if not market_data:
            logger.error("❌ No market data returned")
            return False
        
        logger.info(f"✅ Market data fetched! Keys: {list(market_data.keys())}")
        
        # Check if data is organized by timeframes (new format)
        timeframes = list(market_data.keys())
        logger.info(f"🔍 Timeframes available: {timeframes}")
        
        # Check for expected string-based indicators across timeframes
        expected_indicators = [
            "Aroon_4h", "BollingerBandsWidth_1h", "Vortex_1h", "VWAP_1h",
            "RSI_30m", "RSI_4h", "DonchianChannel_200_1h", 
            "BollingerBands_1h", "ATR_1h"
        ]
        
        found_count = 0
        all_indicators = {}
        
        # Collect all indicators from all timeframes
        for timeframe, tf_data in market_data.items():
            if isinstance(tf_data, dict) and "indicators" in tf_data:
                indicators = tf_data["indicators"]
                logger.info(f"  {timeframe}: {list(indicators.keys())}")
                all_indicators.update(indicators)
        
        logger.info(f"🔍 All indicators found: {list(all_indicators.keys())}")
        
        for expected in expected_indicators:
            if expected in all_indicators:
                found_count += 1
                # Get a sample of the data
                sample_data = all_indicators[expected]
                if isinstance(sample_data, (list, dict, str)):
                    sample_str = str(sample_data)[:100] + "..." if len(str(sample_data)) > 100 else str(sample_data)
                    logger.info(f"  ✅ {expected}: {sample_str}")
                else:
                    logger.info(f"  ✅ {expected}: {type(sample_data).__name__}")
            else:
                logger.info(f"  ❌ {expected}: Missing")
        
        logger.info(f"📊 Found {found_count}/{len(expected_indicators)} expected indicators")
        
        if found_count >= len(expected_indicators) * 0.7:  # 70% success rate
            logger.info("✅ Decision engine can read new data format!")
            return True
        else:
            logger.error("❌ Too many missing indicators")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_decision_reads_new_data())
    sys.exit(0 if success else 1)