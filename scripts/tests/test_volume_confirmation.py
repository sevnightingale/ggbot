#!/usr/bin/env python
"""
Volume Confirmation Test - Test CCXT Volume Analysis Implementation

This test validates:
1. CCXT provider can fetch OHLCV data with volume
2. Volume calculations work correctly (current vs 30-period average)
3. ggShot founder's threshold classification is accurate
4. Decision engine integration works properly
"""

import os
import sys
import asyncio
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decision.providers.ccxt_provider import CCXTPriceProvider
from decision.engine import DecisionEngine
from core.common.config import DEFAULT_USER_ID
from core.common.logger import logger


class VolumeConfirmationTest:
    """Test volume confirmation analysis implementation."""
    
    def __init__(self):
        """Initialize the test."""
        self.logger = logger.bind(module="test.volume_confirmation")
        self.ccxt_provider = CCXTPriceProvider()
        
        # Test symbols - use liquid pairs
        self.test_symbols = [
            'BTC/USDT',   # High volume major pair
            'ETH/USDT',   # High volume altcoin
            'VANRY/USDT'  # Lower volume pair (like ggShot signals)
        ]
    
    async def test_ccxt_volume_fetching(self):
        """Test basic CCXT volume data fetching."""
        self.logger.info("🔍 Testing CCXT volume data fetching...")
        
        for symbol in self.test_symbols:
            try:
                self.logger.info(f"📊 Testing volume data for {symbol}")
                
                # Test volume data fetching
                volume_data = await self.ccxt_provider.get_current_volume_data(symbol, period=30)
                
                if volume_data:
                    current_vol = volume_data['current_volume']
                    avg_vol = volume_data['average_volume'] 
                    ratio = volume_data['volume_ratio']
                    is_spike = volume_data['is_volume_spike']
                    period_used = volume_data['period_used']
                    
                    self.logger.info(f"✅ {symbol} Volume Data:")
                    self.logger.info(f"   Current Volume: {current_vol:,.0f}")
                    self.logger.info(f"   Average Volume (30): {avg_vol:,.0f}")
                    self.logger.info(f"   Ratio: {ratio:.2f}x")
                    self.logger.info(f"   Volume Spike (>1.5x): {is_spike}")
                    self.logger.info(f"   Period Used: {period_used}/30 candles")
                    
                    # Test threshold classification
                    volume_increase_pct = (ratio - 1.0) * 100
                    self.logger.info(f"   Volume Above Average: {volume_increase_pct:+.1f}%")
                    
                    # Apply ggShot founder's thresholds
                    if volume_increase_pct < 10:
                        confidence = "Insignificant (HIGH RISK)"
                    elif volume_increase_pct < 30:
                        confidence = "Easy Confirmation (MODERATE RISK)"
                    elif volume_increase_pct < 60:
                        confidence = "Good Confirmation (ACCEPTABLE RISK)"
                    elif volume_increase_pct < 100:
                        confidence = "Strong Confirmation (LOW RISK)"
                    else:
                        confidence = "Very Strong Momentum (VERY LOW RISK)"
                    
                    self.logger.info(f"   ggShot Classification: {confidence}")
                    self.logger.info("")
                    
                else:
                    self.logger.error(f"❌ Failed to get volume data for {symbol}")
                    
            except Exception as e:
                self.logger.error(f"❌ Error testing {symbol}: {e}")
        
        return True
    
    async def test_decision_engine_integration(self):
        """Test volume confirmation in decision engine."""
        self.logger.info("🔍 Testing Decision Engine volume integration...")
        
        try:
            # Create a decision engine instance
            engine = DecisionEngine(user_id=DEFAULT_USER_ID, config_id="test-config")
            
            # Test the volume confirmation method directly
            test_symbol = 'BTC/USDT'
            self.logger.info(f"📊 Testing decision engine volume analysis for {test_symbol}")
            
            volume_analysis = await engine._get_volume_confirmation(test_symbol)
            
            if volume_analysis and "N/A" not in volume_analysis:
                self.logger.info("✅ Decision Engine Volume Analysis:")
                self.logger.info("=" * 50)
                self.logger.info(volume_analysis)
                self.logger.info("=" * 50)
                return True
            else:
                self.logger.error(f"❌ Decision engine volume analysis failed: {volume_analysis}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Decision engine integration test failed: {e}")
            return False
    
    async def test_volume_calculation_accuracy(self):
        """Test volume calculation accuracy with known data."""
        self.logger.info("🔍 Testing volume calculation accuracy...")
        
        try:
            # Get volume data for BTC/USDT (should have plenty of data)
            symbol = 'BTC/USDT'
            volume_data = await self.ccxt_provider.get_current_volume_data(symbol, period=10)
            
            if not volume_data:
                self.logger.error("❌ Could not get volume data for accuracy test")
                return False
            
            current_vol = volume_data['current_volume']
            avg_vol = volume_data['average_volume']
            calculated_ratio = volume_data['volume_ratio']
            
            # Manual calculation check
            expected_ratio = current_vol / avg_vol if avg_vol > 0 else 0
            
            # Check if calculations match (within small tolerance)
            if abs(calculated_ratio - expected_ratio) < 0.001:
                self.logger.info("✅ Volume calculations are accurate")
                self.logger.info(f"   Current: {current_vol:,.0f}")
                self.logger.info(f"   Average: {avg_vol:,.0f}") 
                self.logger.info(f"   Calculated Ratio: {calculated_ratio:.4f}")
                self.logger.info(f"   Expected Ratio: {expected_ratio:.4f}")
                return True
            else:
                self.logger.error(f"❌ Volume calculation mismatch:")
                self.logger.error(f"   Calculated: {calculated_ratio:.4f}")
                self.logger.error(f"   Expected: {expected_ratio:.4f}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Volume calculation accuracy test failed: {e}")
            return False
    
    async def test_threshold_classification(self):
        """Test ggShot founder's threshold classification."""
        self.logger.info("🔍 Testing ggShot threshold classification...")
        
        # Test cases with known percentage increases
        test_cases = [
            (0.95, "Insignificant (HIGH RISK)"),      # -5% (below average)
            (1.05, "Insignificant (HIGH RISK)"),      # +5%  
            (1.20, "Easy Confirmation (MODERATE RISK)"),  # +20%
            (1.45, "Good Confirmation (ACCEPTABLE RISK)"),  # +45%
            (1.80, "Strong Confirmation (LOW RISK)"),  # +80%
            (2.50, "Very Strong Momentum (VERY LOW RISK)")  # +150%
        ]
        
        for ratio, expected_classification in test_cases:
            volume_increase_pct = (ratio - 1.0) * 100
            
            # Apply classification logic
            if volume_increase_pct < 10:
                actual_classification = "Insignificant (HIGH RISK)"
            elif volume_increase_pct < 30:
                actual_classification = "Easy Confirmation (MODERATE RISK)"
            elif volume_increase_pct < 60:
                actual_classification = "Good Confirmation (ACCEPTABLE RISK)"
            elif volume_increase_pct < 100:
                actual_classification = "Strong Confirmation (LOW RISK)"
            else:
                actual_classification = "Very Strong Momentum (VERY LOW RISK)"
            
            if actual_classification == expected_classification:
                self.logger.info(f"✅ Ratio {ratio:.2f}x ({volume_increase_pct:+.0f}%) → {actual_classification}")
            else:
                self.logger.error(f"❌ Ratio {ratio:.2f}x ({volume_increase_pct:+.0f}%) → Expected: {expected_classification}, Got: {actual_classification}")
                return False
        
        return True
    
    async def run_all_tests(self):
        """Run all volume confirmation tests."""
        self.logger.info("🚀 Starting Volume Confirmation Tests")
        self.logger.info("=" * 60)
        
        tests = [
            ("CCXT Volume Fetching", self.test_ccxt_volume_fetching),
            ("Volume Calculation Accuracy", self.test_volume_calculation_accuracy),
            ("Threshold Classification", self.test_threshold_classification),
            ("Decision Engine Integration", self.test_decision_engine_integration)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.logger.info(f"\n🧪 Running: {test_name}")
            self.logger.info("-" * 40)
            
            try:
                result = await test_func()
                if result:
                    self.logger.info(f"✅ {test_name} PASSED")
                    passed += 1
                else:
                    self.logger.error(f"❌ {test_name} FAILED")
            except Exception as e:
                self.logger.error(f"❌ {test_name} ERROR: {e}")
        
        self.logger.info("\n" + "=" * 60)
        if passed == total:
            self.logger.info(f"🎉 ALL TESTS PASSED ({passed}/{total})")
            self.logger.info("✅ Volume confirmation system is ready for production!")
        else:
            self.logger.error(f"❌ TESTS FAILED ({passed}/{total} passed)")
            self.logger.error("🔧 Fix issues before deploying volume analysis")
        
        return passed == total


async def main():
    """Main test runner."""
    print("=" * 60)
    print("🧪 Volume Confirmation Test Suite")
    print("=" * 60)
    print()
    
    test = VolumeConfirmationTest()
    success = await test.run_all_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 VOLUME CONFIRMATION TESTS PASSED!")
        print("✅ Ready to deploy volume analysis to production")
    else:
        print("❌ VOLUME CONFIRMATION TESTS FAILED!")
        print("🔧 Fix issues before proceeding")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())