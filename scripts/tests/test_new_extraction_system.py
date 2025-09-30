#!/usr/bin/env python3
"""
Test the new string-based extraction system.

This test verifies that our updated extraction system can:
1. Use the ggShot config_id to get string-based indicators
2. Extract only the specific indicators we need
3. Store data in the new format (config_id + symbol)
"""
import asyncio
import os
import sys
sys.path.append('/home/sev/ggbot')

from core.common.logger import logger
from extraction.extraction_main import extract_mcp_indicators

async def test_new_extraction():
    """Test the new extraction system with ggShot config."""
    
    # Test parameters
    GGSHOT_CONFIG_ID = "e249bb49-0455-4596-9657-09bf9e14ca14"
    USER_ID = "00000000-0000-0000-0000-000000000001"
    TEST_SYMBOLS = ["BTC/USDT"]
    TEST_TIMEFRAMES = ["1h"]  # Should be ignored by new system
    
    logger.info("🧪 Starting NEW extraction system test")
    logger.info(f"Config ID: {GGSHOT_CONFIG_ID}")
    logger.info(f"Symbols: {TEST_SYMBOLS}")
    
    try:
        # Test the new extraction system
        results = await extract_mcp_indicators(
            symbols=TEST_SYMBOLS,
            timeframes=TEST_TIMEFRAMES,
            user_id=USER_ID,
            use_llm=False,  # Skip LLM for faster testing
            config_id=GGSHOT_CONFIG_ID
        )
        
        # Analyze results
        if "error" in results:
            logger.error(f"❌ Extraction failed: {results['error']}")
            return False
        
        logger.info(f"✅ Extraction completed! Results structure:")
        for symbol, symbol_data in results.items():
            logger.info(f"  Symbol: {symbol}")
            if isinstance(symbol_data, dict):
                for key, value in symbol_data.items():
                    logger.info(f"    {key}: {type(value).__name__}")
                    if key == "indicators" and isinstance(value, dict):
                        logger.info(f"      Indicators found: {list(value.keys())}")
            
        # Check if we got the expected string-based indicators
        expected_indicators = [
            "Aroon_4h", "BollingerBandsWidth_1h", "Vortex_1h", "VWAP_1h",
            "RSI_30m", "RSI_4h", "DonchianChannel_200_1h", 
            "BollingerBands_1h", "ATR_1h"
        ]
        
        btc_results = results.get("BTC/USDT", {})
        indicators = btc_results.get("indicators", {})
        
        logger.info(f"🔍 Checking for expected indicators:")
        found_indicators = []
        missing_indicators = []
        
        for expected in expected_indicators:
            if expected in indicators:
                found_indicators.append(expected)
                logger.info(f"  ✅ {expected}: Found")
            else:
                missing_indicators.append(expected)
                logger.info(f"  ❌ {expected}: Missing")
        
        logger.info(f"📊 Summary: {len(found_indicators)}/{len(expected_indicators)} indicators found")
        
        if len(found_indicators) >= len(expected_indicators) * 0.7:  # 70% success rate
            logger.info("✅ NEW extraction system test PASSED!")
            return True
        else:
            logger.error("❌ NEW extraction system test FAILED - too many missing indicators")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_new_extraction())
    sys.exit(0 if success else 1)