#!/usr/bin/env python3
"""
Test script to verify YFinance price source works reliably with rate limiting.
"""

import sys
import os
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extraction.sources.yfinance.yfinance_datasource import YFinanceDataSource
from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID


def test_yfinance_comprehensive():
    """Test YFinance data source comprehensively with rate limiting."""
    print("=== Comprehensive YFinance Test ===")
    
    yf_source = YFinanceDataSource()
    
    # Test symbols
    test_symbols = ['BTC-USD', 'ETH-USD']
    
    success_count = 0
    total_tests = 0
    
    for symbol in test_symbols:
        print(f"\nTesting {symbol}:")
        
        # Test 1: Current price
        print("  1. Testing current price...")
        try:
            start_time = time.time()
            price = yf_source.get_current_price(symbol)
            end_time = time.time()
            
            print(f"     ✓ Current price: ${price:,.2f}")
            print(f"     ✓ Request time: {end_time - start_time:.2f} seconds")
            success_count += 1
            
        except Exception as e:
            print(f"     ✗ ERROR: {str(e)}")
        
        total_tests += 1
        
        # Test 2: Latest data (15m)
        print("  2. Testing latest 15m data...")
        try:
            start_time = time.time()
            latest_data = yf_source.get_latest_data(symbol, '15m', limit=3)
            end_time = time.time()
            
            if not latest_data.empty:
                latest_close = latest_data['Close'].iloc[-1]
                print(f"     ✓ Latest 15m close: ${latest_close:,.2f}")
                print(f"     ✓ Data points: {len(latest_data)}")
                print(f"     ✓ Request time: {end_time - start_time:.2f} seconds")
                success_count += 1
            else:
                print("     ✗ No latest data available")
            
        except Exception as e:
            print(f"     ✗ ERROR: {str(e)}")
        
        total_tests += 1
        
        # Test 3: Historical data (1h)
        print("  3. Testing historical 1h data...")
        try:
            start_time = time.time()
            hist_data = yf_source.get_historical_data(symbol, '1h', limit=5)
            end_time = time.time()
            
            if not hist_data.empty:
                print(f"     ✓ Historical data points: {len(hist_data)}")
                print(f"     ✓ Date range: {hist_data.index[0]} to {hist_data.index[-1]}")
                print(f"     ✓ Request time: {end_time - start_time:.2f} seconds")
                success_count += 1
            else:
                print("     ✗ No historical data available")
            
        except Exception as e:
            print(f"     ✗ ERROR: {str(e)}")
        
        total_tests += 1
        
        print(f"  Symbol {symbol} tests: {success_count}/{total_tests} passed")
    
    print(f"\n=== Test Summary ===")
    print(f"Total tests: {total_tests}")
    print(f"Successful tests: {success_count}")
    print(f"Success rate: {(success_count/total_tests)*100:.1f}%" if total_tests > 0 else "No tests run")
    
    if success_count == total_tests:
        print("✓ All tests passed! YFinance with rate limiting is working reliably.")
    elif success_count > total_tests * 0.8:
        print("⚠ Most tests passed. Rate limiting is helping but may need adjustment.")
    else:
        print("✗ Many tests failed. Rate limiting may not be sufficient.")
    
    return success_count == total_tests


def test_rate_limiting_effectiveness():
    """Test that rate limiting is actually working."""
    print("\n=== Rate Limiting Effectiveness Test ===")
    
    yf_source = YFinanceDataSource()
    
    print("Making 3 consecutive requests to test rate limiting...")
    
    times = []
    for i in range(3):
        print(f"Request {i+1}:")
        start_time = time.time()
        
        try:
            price = yf_source.get_current_price('BTC-USD')
            end_time = time.time()
            request_time = end_time - start_time
            times.append(request_time)
            
            print(f"  ✓ Price: ${price:,.2f}")
            print(f"  ✓ Time: {request_time:.2f} seconds")
            
        except Exception as e:
            print(f"  ✗ ERROR: {str(e)}")
            times.append(0)
    
    print("\nRate limiting analysis:")
    if len(times) >= 2:
        avg_time = sum(times) / len(times)
        print(f"  Average request time: {avg_time:.2f} seconds")
        
        if avg_time >= 2.5:  # Should be close to our 3-second rate limit
            print("  ✓ Rate limiting is working effectively")
            return True
        else:
            print("  ⚠ Rate limiting may not be applied consistently")
            return False
    else:
        print("  ✗ Insufficient data to analyze rate limiting")
        return False


def main():
    """Run all tests."""
    print("Testing YFinance with Rate Limiting")
    print("=" * 50)
    
    # Test comprehensive functionality
    comprehensive_success = test_yfinance_comprehensive()
    
    # Wait before rate limiting test
    time.sleep(2)
    
    # Test rate limiting effectiveness
    rate_limit_success = test_rate_limiting_effectiveness()
    
    # Final summary
    print("\n" + "=" * 50)
    print("FINAL RESULTS:")
    print(f"✓ Comprehensive tests: {'PASS' if comprehensive_success else 'FAIL'}")
    print(f"✓ Rate limiting: {'EFFECTIVE' if rate_limit_success else 'NEEDS ADJUSTMENT'}")
    
    if comprehensive_success and rate_limit_success:
        print("\n🎉 YFinance is working reliably with proper rate limiting!")
        print("Ready for production use in the price comparison system.")
    else:
        print("\n⚠ YFinance needs further adjustments before reliable use.")


if __name__ == "__main__":
    main()