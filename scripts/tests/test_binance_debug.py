#!/usr/bin/env python3
"""
Quick Binance diagnostic test to understand the exact failure reasons.
"""

import asyncio
import sys
import os
import traceback

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from decision.providers.ccxt_provider import CCXTPriceProvider

async def test_binance_specifically():
    """Test Binance specifically with detailed error reporting"""
    provider = CCXTPriceProvider()
    
    test_symbols = ['CHZ/USDT', 'BTC/USDT', 'ETH/USDT', 'ADA/USDT']
    
    print("🔍 BINANCE DIAGNOSTIC TEST")
    print("=" * 50)
    
    for symbol in test_symbols:
        print(f"\n🧪 Testing {symbol} on Binance:")
        
        try:
            # Get mapped symbol
            binance_map = provider.EXCHANGE_SYMBOL_MAPS.get('binance', {})
            mapped_symbol = binance_map.get(symbol)
            print(f"   Mapping: {symbol} → {mapped_symbol}")
            
            if not mapped_symbol:
                print(f"   ❌ No mapping found")
                continue
            
            # Try to get exchange client
            print(f"   Creating Binance client...")
            exchange = await provider._get_exchange_client('binance')
            if not exchange:
                print(f"   ❌ Failed to create exchange client")
                continue
            
            print(f"   ✅ Exchange client created")
            
            # Try to load markets
            print(f"   Loading markets...")
            await exchange.load_markets()
            print(f"   ✅ Markets loaded: {len(exchange.markets)} total")
            
            # Check if symbol exists
            if mapped_symbol not in exchange.markets:
                print(f"   ❌ Symbol {mapped_symbol} not found in markets")
                print(f"   📋 Available similar symbols: {[s for s in exchange.markets.keys() if 'CHZ' in s][:5]}")
            else:
                print(f"   ✅ Symbol {mapped_symbol} found in markets")
                
                # Try to fetch ticker
                print(f"   Fetching ticker...")
                ticker = await exchange.fetch_ticker(mapped_symbol)
                price = ticker.get('last')
                
                if price and price > 0:
                    print(f"   ✅ SUCCESS: Price = ${price}")
                else:
                    print(f"   ❌ Invalid price: {price}")
            
            # Close connection
            await exchange.close()
            
        except Exception as e:
            print(f"   ❌ EXCEPTION: {type(e).__name__}: {str(e)}")
            print(f"   📋 Full traceback:")
            traceback.print_exc()
    
    # Cleanup
    await provider.cleanup()

if __name__ == "__main__":
    asyncio.run(test_binance_specifically())