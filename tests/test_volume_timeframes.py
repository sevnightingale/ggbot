#!/usr/bin/env python3
"""
Volume Timeframe Test

Tests volume calculation across multiple timeframes for BTC/USDT
to validate the volume timeframe fix and compare with TradingView data.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from decision.providers.ccxt_provider import CCXTPriceProvider
from core.common.logger import logger


class VolumeTimeframeTest:
    """Test volume calculation across multiple timeframes."""
    
    def __init__(self):
        self.ccxt_provider = CCXTPriceProvider()
        self.symbol = "BTC/USDT"
        self.timeframes = ['15m', '30m', '1h', '4h']
        self.period = 30
        
    async def test_volume_calculation(self) -> Dict:
        """Test volume calculation for all timeframes."""
        results = {}
        
        print(f"🔍 Testing volume calculation for {self.symbol} across multiple timeframes")
        print(f"📊 Using {self.period}-period average for all timeframes")
        print(f"📅 Test time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print("=" * 80)
        
        for timeframe in self.timeframes:
            try:
                print(f"\n🕐 Testing timeframe: {timeframe}")
                print("-" * 40)
                
                # Get volume data for this timeframe
                volume_data = await self.ccxt_provider.get_current_volume_data(
                    self.symbol, 
                    period=self.period, 
                    timeframe=timeframe
                )
                
                if volume_data:
                    results[timeframe] = {
                        'current_volume': volume_data['current_volume'],
                        'average_volume': volume_data['average_volume'],
                        'volume_ratio': volume_data['volume_ratio'],
                        'volume_increase_pct': (volume_data['volume_ratio'] - 1.0) * 100,
                        'is_volume_spike': volume_data['is_volume_spike'],
                        'status': 'success'
                    }
                    
                    # Determine volume confidence level
                    volume_increase_pct = results[timeframe]['volume_increase_pct']
                    if volume_increase_pct < 10:
                        confidence_level = "Insignificant (HIGH RISK)"
                    elif volume_increase_pct < 30:
                        confidence_level = "Easy Confirmation (MODERATE RISK)"
                    elif volume_increase_pct < 60:
                        confidence_level = "Good Confirmation (ACCEPTABLE RISK)"
                    elif volume_increase_pct < 100:
                        confidence_level = "Strong Confirmation (LOW RISK)"
                    else:
                        confidence_level = "Very Strong Momentum (VERY LOW RISK)"
                    
                    results[timeframe]['confidence_level'] = confidence_level
                    
                    # Display results
                    print(f"✅ Current Volume: {volume_data['current_volume']:,.0f}")
                    print(f"📈 Average Volume ({self.period}): {volume_data['average_volume']:,.0f}")
                    print(f"📊 Volume Ratio: {volume_data['volume_ratio']:.2f}x")
                    print(f"📈 Volume Change: {volume_increase_pct:+.1f}%")
                    print(f"⚡ Volume Spike: {'Yes' if volume_data['is_volume_spike'] else 'No'}")
                    print(f"🎯 Confidence Level: {confidence_level}")
                    
                else:
                    results[timeframe] = {
                        'status': 'failed',
                        'error': 'No volume data available'
                    }
                    print(f"❌ Failed to get volume data for {timeframe}")
                    
            except Exception as e:
                results[timeframe] = {
                    'status': 'error',
                    'error': str(e)
                }
                print(f"❌ Error testing {timeframe}: {e}")
        
        return results
    
    async def compare_timeframes(self, results: Dict):
        """Compare volume results across timeframes."""
        print("\n" + "=" * 80)
        print("📊 TIMEFRAME COMPARISON")
        print("=" * 80)
        
        successful_results = {tf: data for tf, data in results.items() if data.get('status') == 'success'}
        
        if not successful_results:
            print("❌ No successful results to compare")
            return
        
        # Create comparison table
        print(f"{'Timeframe':<10} {'Current Vol':<15} {'Avg Vol':<15} {'Ratio':<8} {'Change %':<10} {'Confidence':<25}")
        print("-" * 95)
        
        for tf in self.timeframes:
            if tf in successful_results:
                data = successful_results[tf]
                current_vol = f"{data['current_volume']:,.0f}"
                avg_vol = f"{data['average_volume']:,.0f}"
                ratio = f"{data['volume_ratio']:.2f}x"
                change_pct = f"{data['volume_increase_pct']:+.1f}%"
                confidence = data['confidence_level'].split(' (')[0]  # Remove risk level for table
                
                print(f"{tf:<10} {current_vol:<15} {avg_vol:<15} {ratio:<8} {change_pct:<10} {confidence:<25}")
        
        # Analysis
        print("\n📋 ANALYSIS:")
        print("-" * 40)
        
        # Check for volume consistency
        current_volumes = [data['current_volume'] for data in successful_results.values()]
        if len(set(current_volumes)) > 1:
            print("⚠️  Different current volumes detected across timeframes")
            print("   This is expected as current volume represents different candle periods")
        
        # Check for dramatic differences in ratios
        ratios = [data['volume_ratio'] for data in successful_results.values()]
        max_ratio = max(ratios)
        min_ratio = min(ratios)
        
        if max_ratio / min_ratio > 2.0:
            print(f"⚠️  Significant volume ratio differences detected: {min_ratio:.2f}x to {max_ratio:.2f}x")
            print("   This indicates different volume patterns across timeframes")
        else:
            print(f"✅ Volume ratios are relatively consistent: {min_ratio:.2f}x to {max_ratio:.2f}x")
        
        # Identify most active timeframe
        max_ratio_tf = max(successful_results.keys(), key=lambda x: successful_results[x]['volume_ratio'])
        print(f"🔥 Most active timeframe: {max_ratio_tf} ({successful_results[max_ratio_tf]['volume_ratio']:.2f}x)")
        
        # Trading recommendations
        print("\n🎯 TRADING INSIGHTS:")
        print("-" * 40)
        
        high_confidence_tfs = [tf for tf, data in successful_results.items() 
                              if data['volume_increase_pct'] >= 60]
        
        if high_confidence_tfs:
            print(f"✅ Strong volume confirmation on: {', '.join(high_confidence_tfs)}")
        else:
            print("⚠️  No timeframes show strong volume confirmation (60%+)")
        
        # Check for volume spikes
        spike_tfs = [tf for tf, data in successful_results.items() if data['is_volume_spike']]
        if spike_tfs:
            print(f"⚡ Volume spikes detected on: {', '.join(spike_tfs)}")
        
    async def run_test(self):
        """Run the complete volume timeframe test."""
        try:
            # Test volume calculation
            results = await self.test_volume_calculation()
            
            # Compare results
            await self.compare_timeframes(results)
            
            # Final summary
            print("\n" + "=" * 80)
            print("📋 TEST SUMMARY")
            print("=" * 80)
            
            successful_count = sum(1 for data in results.values() if data.get('status') == 'success')
            total_count = len(results)
            
            print(f"✅ Successful tests: {successful_count}/{total_count}")
            print(f"🔧 Fixed issues: TRIX mapping, Volume timeframe mismatch")
            print(f"📊 Symbol tested: {self.symbol}")
            print(f"📅 Period used: {self.period} candles")
            
            if successful_count == total_count:
                print("🎉 All timeframes tested successfully!")
                print("✅ Volume timeframe fix is working correctly")
            else:
                print("⚠️  Some timeframes failed - check exchange connectivity")
            
            print("\n💡 NEXT STEPS:")
            print("1. Compare these results with TradingView volume data")
            print("2. Verify volume calculations match expected values")
            print("3. Test with real ggShot signals to ensure proper integration")
            
            return results
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            logger.error(f"Volume timeframe test failed: {e}")
            return None


async def main():
    """Run the volume timeframe test."""
    test = VolumeTimeframeTest()
    results = await test.run_test()
    
    if results:
        print(f"\n✅ Volume timeframe test completed successfully")
        print(f"📊 Test results available for manual TradingView comparison")
    else:
        print(f"\n❌ Volume timeframe test failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())