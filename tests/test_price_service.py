#!/usr/bin/env python
"""
Quick test for the new PriceService to verify it fetches real market prices.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from decision.services.price_service import PriceService
from core.common.logging_config import setup_logging, logger

async def test_price_service():
    """Test the new PriceService with real market data."""
    print("🚀 Testing PriceService...")
    
    # Initialize price service
    price_service = PriceService()
    
    # Test symbols
    test_symbols = ['BTC/USDT', 'BTC/USD', 'ETH/USDT']
    
    try:
        # Health check first
        print("\n📊 Running health check...")
        health = await price_service.health_check()
        print(f"Health status: {health['overall_status']}")
        for provider, status in health['providers'].items():
            print(f"  - {provider}: {status['status']}")
        
        if health['overall_status'] != 'healthy':
            print("⚠️ Price service not healthy, but continuing with tests...")
        
        # Test price fetching
        print(f"\n💰 Testing price fetching...")
        for symbol in test_symbols:
            try:
                print(f"\nFetching price for {symbol}...")
                price = await price_service.get_current_price(symbol)
                print(f"✅ {symbol}: ${price:,.2f}")
                
                # Also get detailed breakdown
                breakdown = await price_service.get_price_breakdown(symbol)
                print(f"   YFinance: ${breakdown['providers']['yfinance']['price']:,.2f}" if breakdown['providers']['yfinance']['price'] else "   YFinance: Failed")
                print(f"   CCXT: ${breakdown['providers']['ccxt']['price']:,.2f}" if breakdown['providers']['ccxt']['price'] else "   CCXT: Failed")
                if breakdown['validation']:
                    print(f"   Difference: {breakdown['validation']['price_difference_pct']:.2f}%")
                    print(f"   Valid: {breakdown['validation']['within_tolerance']}")
                
            except Exception as e:
                print(f"❌ Failed to get price for {symbol}: {e}")
        
        # Test supported symbols
        print(f"\n📋 Supported symbols: {len(price_service.get_supported_symbols())}")
        
        print(f"\n✅ PriceService test completed!")
        
    except Exception as e:
        print(f"❌ PriceService test failed: {e}")
        raise

if __name__ == "__main__":
    # Setup logging
    setup_logging()
    
    # Run the test
    asyncio.run(test_price_service())