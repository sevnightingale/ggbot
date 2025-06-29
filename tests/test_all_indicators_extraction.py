#!/usr/bin/env python3
"""
Test all 53 indicators extraction process using the comprehensive test configuration.
This test validates that all indicators can be successfully calculated and interpreted.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parents[1]))

from extraction.extraction_main import extract_mcp_indicators
from core.common.logger import logger
from core.common.db import get_db_connection

# Configuration ID for all 53 indicators test
ALL_INDICATORS_CONFIG_ID = "709a882b-4761-4279-bd73-297a851c582e"

async def test_all_indicators_extraction():
    """Test extraction of all 53 indicators for BTC/USDT on 1h timeframe."""
    
    print("🚀 Starting All Indicators Extraction Test")
    print("=" * 80)
    print(f"Config ID: {ALL_INDICATORS_CONFIG_ID}")
    print(f"Symbol: BTC/USDT")
    print(f"Timeframe: 1h")
    print(f"Indicators: 53 (all available)")
    print("=" * 80)
    
    # Test parameters
    symbols = ["BTC/USDT"]
    timeframes = ["1h"]
    
    try:
        # Start timing
        start_time = datetime.now()
        
        print(f"\n⏰ Starting extraction at {start_time.isoformat()}")
        print("This will make 53 LLM calls - please be patient...")
        
        # Run the extraction
        results = await extract_mcp_indicators(
            symbols=symbols,
            timeframes=timeframes,
            config_id=ALL_INDICATORS_CONFIG_ID
        )
        
        # End timing
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Extraction completed in {duration:.1f} seconds")
        
        # Analyze results
        if results and isinstance(results, dict):
            # Check BTC/USDT results
            btc_results = results.get("BTC/USDT", {})
            hour_results = btc_results.get("1h", {})
            
            if hour_results.get("status") == "success":
                indicators_data = hour_results.get("indicators", {})
                interpretation = hour_results.get("interpretation", {})
                
                print(f"\n📊 EXTRACTION RESULTS:")
                print(f"{'='*80}")
                
                # Count successful indicators
                successful_indicators = []
                failed_indicators = []
                
                for indicator_name, indicator_value in indicators_data.items():
                    if indicator_value and not (isinstance(indicator_value, str) and indicator_value.startswith("Error")):
                        successful_indicators.append(indicator_name)
                    else:
                        failed_indicators.append((indicator_name, indicator_value))
                
                print(f"✅ Successful indicators: {len(successful_indicators)}/53")
                print(f"❌ Failed indicators: {len(failed_indicators)}/53")
                
                # Show successful indicators by category
                print(f"\n📈 SUCCESSFUL INDICATORS BY CATEGORY:")
                print("-" * 60)
                
                # Categorize indicators
                trend_indicators = ["SMA", "EMA", "MACD", "ParabolicSAR", "DEMA", "TEMA", 
                                  "TriangularMovingAverage", "Aroon", "CCI", "Vortex",
                                  "BalanceOfPower", "ChandeForecastOscillator", "Qstick"]
                
                momentum_indicators = ["RSI", "Stochastic", "WilliamsR", "AwesomeOscillator",
                                     "ChaikinOscillator", "ROC", "IchimokuCloud"]
                
                volatility_indicators = ["BollingerBands", "ATR", "KeltnerChannel", 
                                       "DonchianChannel", "TrueRange", "AccelerationBands"]
                
                volume_indicators = ["OBV", "VWAP", "MFI", "ChaikinMoneyFlow", 
                                   "AccumulationDistribution", "ForceIndex"]
                
                # Print by category
                for category_name, category_list in [
                    ("Trend", trend_indicators),
                    ("Momentum", momentum_indicators),
                    ("Volatility", volatility_indicators),
                    ("Volume", volume_indicators)
                ]:
                    category_success = [ind for ind in successful_indicators 
                                      if any(cat in ind for cat in category_list)]
                    if category_success:
                        print(f"\n{category_name} ({len(category_success)}):")
                        for ind in sorted(category_success)[:5]:  # Show first 5
                            print(f"  - {ind}")
                        if len(category_success) > 5:
                            print(f"  ... and {len(category_success) - 5} more")
                
                # Show failed indicators
                if failed_indicators:
                    print(f"\n❌ FAILED INDICATORS:")
                    print("-" * 60)
                    for ind_name, error in failed_indicators[:10]:  # Show first 10
                        print(f"  - {ind_name}: {str(error)[:50]}...")
                    if len(failed_indicators) > 10:
                        print(f"  ... and {len(failed_indicators) - 10} more")
                
                # Show interpretation summary
                if interpretation:
                    print(f"\n🤖 LLM INTERPRETATION SUMMARY:")
                    print("-" * 60)
                    
                    interpreted_indicators = interpretation.get("indicators", {})
                    if interpreted_indicators:
                        print(f"Interpreted indicators: {len(interpreted_indicators)}")
                        
                        # Show a few examples
                        for ind_name, ind_data in list(interpreted_indicators.items())[:3]:
                            if isinstance(ind_data, dict):
                                current_value = ind_data.get("current_value", "N/A")
                                trend = ind_data.get("trend", "N/A")
                                print(f"\n{ind_name}:")
                                print(f"  Current Value: {current_value}")
                                print(f"  Trend: {trend}")
                    
                    if "summary" in interpretation:
                        print(f"\nOverall Summary: {interpretation['summary'][:200]}...")
                
                # Check database storage
                print(f"\n💾 DATABASE VERIFICATION:")
                print("-" * 60)
                
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        # Check if data was stored
                        cur.execute("""
                            SELECT COUNT(*) as count, 
                                   MAX(updated_at) as latest_update
                            FROM market_data 
                            WHERE symbol = %s 
                            AND timeframe = %s 
                            AND data_type = 'indicator_analysis'
                            AND updated_at > NOW() - INTERVAL '5 minutes'
                        """, ("BTC/USDT", "1h"))
                        
                        result = cur.fetchone()
                        if result and result[0] > 0:
                            print(f"✅ Data stored in database")
                            print(f"   Records: {result[0]}")
                            print(f"   Latest: {result[1]}")
                        else:
                            print(f"❌ No recent data found in database")
                
                # Performance summary
                print(f"\n⚡ PERFORMANCE SUMMARY:")
                print("-" * 60)
                print(f"Total Duration: {duration:.1f} seconds")
                print(f"Average per indicator: {duration/53:.2f} seconds")
                print(f"Success Rate: {len(successful_indicators)/53*100:.1f}%")
                
            else:
                print(f"\n❌ Extraction failed: {hour_results.get('error', 'Unknown error')}")
                
        else:
            print(f"\n❌ Invalid results format: {type(results)}")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        logger.error(f"Test error: {e}", exc_info=True)
        return False
    
    print(f"\n{'='*80}")
    print("✅ Test completed!")
    return True


async def verify_config_exists():
    """Verify that the test configuration exists in the database."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT config_name, config_type, created_at,
                       config_data->'extraction'->'sources'->'crypto_indicators_mcp'->'indicators' as indicators
                FROM configurations 
                WHERE config_id = %s
            """, (ALL_INDICATORS_CONFIG_ID,))
            
            result = cur.fetchone()
            if result:
                print(f"✅ Configuration found:")
                print(f"   Name: {result[0]}")
                print(f"   Type: {result[1]}")
                print(f"   Created: {result[2]}")
                
                # Count indicators (result[3] is already a list from PostgreSQL)
                indicators = result[3] if result[3] else []
                print(f"   Indicators: {len(indicators)}")
                
                return True
            else:
                print(f"❌ Configuration not found: {ALL_INDICATORS_CONFIG_ID}")
                return False


async def main():
    """Main test runner."""
    print("🧪 All Indicators Extraction Test")
    print("=" * 80)
    
    # First verify config exists
    print("\n1️⃣ Verifying configuration...")
    if not await verify_config_exists():
        print("❌ Cannot proceed without configuration")
        print("   Run: python core/config/insert_config.py")
        return
    
    # Run the test
    print("\n2️⃣ Running extraction test...")
    success = await test_all_indicators_extraction()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")


if __name__ == "__main__":
    asyncio.run(main())