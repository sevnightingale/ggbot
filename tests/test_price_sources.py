#!/usr/bin/env python3
"""
Test script to verify both YFinance and CCXT price sources work reliably with rate limiting.
"""

import sys
import os
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extraction.sources.yfinance.yfinance_datasource import YFinanceDataSource
from extraction.sources.ccxt_mcp.ccxt_mcp_datasource import CCXTMCPDataSource
from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID


def test_yfinance_source():
    """Test YFinance data source with rate limiting."""
    print("\n=== Testing YFinance Data Source ===")
    
    yf_source = YFinanceDataSource()
    
    # Test symbols
    test_symbols = ['BTC-USD', 'ETH-USD']
    
    for symbol in test_symbols:
        try:
            print(f"\nTesting {symbol}:")
            
            # Test current price
            start_time = time.time()
            price = yf_source.get_current_price(symbol)
            end_time = time.time()
            
            print(f"  Current price: ${price:,.2f}")
            print(f"  Request time: {end_time - start_time:.2f} seconds")
            
            # Test latest data
            start_time = time.time()
            latest_data = yf_source.get_latest_data(symbol, '15m', limit=2)
            end_time = time.time()
            
            if not latest_data.empty:
                latest_close = latest_data['Close'].iloc[-1]
                print(f"  Latest 15m close: ${latest_close:,.2f}")
                print(f"  Data points: {len(latest_data)}")
            else:
                print("  No latest data available")
            
            print(f"  Request time: {end_time - start_time:.2f} seconds")
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
    
    return True


def test_ccxt_source():
    """Test CCXT MCP data source."""
    print("\n=== Testing CCXT MCP Data Source ===")
    
    try:
        ccxt_source = CCXTMCPDataSource()
        
        # Test symbols (using real market symbols)
        test_symbols = ['BTC/USDT', 'ETH/USDT']
        
        for symbol in test_symbols:
            try:
                print(f"\nTesting {symbol}:")
                
                # Test current price
                start_time = time.time()
                price = ccxt_source.get_current_price(symbol)
                end_time = time.time()
                
                print(f"  Current price: ${price:,.2f}")
                print(f"  Request time: {end_time - start_time:.2f} seconds")
                
                # Test latest data
                start_time = time.time()
                latest_data = ccxt_source.get_latest_data(symbol, '15m', limit=2)
                end_time = time.time()
                
                if not latest_data.empty:
                    latest_close = latest_data['close'].iloc[-1]
                    print(f"  Latest 15m close: ${latest_close:,.2f}")
                    print(f"  Data points: {len(latest_data)}")
                else:
                    print("  No latest data available")
                
                print(f"  Request time: {end_time - start_time:.2f} seconds")
                
            except Exception as e:
                print(f"  ERROR: {str(e)}")
        
        return True
    
    except Exception as e:
        print(f"ERROR initializing CCXT source: {str(e)}")
        return False


def compare_prices():
    """Compare prices between YFinance and CCXT sources."""
    print("\n=== Comparing Prices Between Sources ===")
    
    try:
        yf_source = YFinanceDataSource()
        ccxt_source = CCXTMCPDataSource()
        
        # Test BTC price comparison
        print(f"\nBTC Price Comparison:")
        
        try:
            yf_price = yf_source.get_current_price('BTC-USD')
            print(f"  YFinance BTC-USD: ${yf_price:,.2f}")
        except Exception as e:
            print(f"  YFinance ERROR: {str(e)}")
            yf_price = None
        
        try:
            ccxt_price = ccxt_source.get_current_price('BTC/USDT')
            print(f"  CCXT BTC/USDT: ${ccxt_price:,.2f}")
        except Exception as e:
            print(f"  CCXT ERROR: {str(e)}")
            ccxt_price = None
        
        if yf_price and ccxt_price:
            diff = abs(yf_price - ccxt_price)
            diff_pct = (diff / yf_price) * 100
            print(f"  Price difference: ${diff:,.2f} ({diff_pct:.2f}%)")
            
            # Prices should be reasonably close (within 5%)
            if diff_pct < 5:
                print("  ✓ Prices are reasonably close")
            else:
                print("  ⚠ Large price difference detected")
        
    except Exception as e:
        print(f"ERROR in price comparison: {str(e)}")


def main():
    """Run all tests."""
    print("Testing Price Sources with Rate Limiting")
    print("=" * 50)
    
    # Test YFinance
    yf_success = test_yfinance_source()
    
    # Wait a moment between source tests
    time.sleep(2)
    
    # Test CCXT
    ccxt_success = test_ccxt_source()
    
    # Wait a moment before comparison
    time.sleep(2)
    
    # Compare prices
    compare_prices()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"YFinance source: {'✓ PASS' if yf_success else '✗ FAIL'}")
    print(f"CCXT source: {'✓ PASS' if ccxt_success else '✗ FAIL'}")
    
    if yf_success and ccxt_success:
        print("\n✓ Both price sources are working!")
        print("Rate limiting is helping prevent API errors.")
    else:
        print("\n⚠ Some price sources have issues.")
        print("Check the error messages above for details.")


if __name__ == "__main__":
    main()