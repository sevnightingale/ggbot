#!/usr/bin/env python3
"""
Test Hummingbot API connectivity and symbol conversion for paper trading.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from trading.paper.market_data import MarketDataAdapter

async def test_hummingbot_connectivity():
    print('🔌 Testing Hummingbot API connectivity...')
    
    adapter = MarketDataAdapter()
    
    # Test 1: Health check
    print('\n1. Health Check:')
    try:
        health = await adapter.health_check()
        print(f'   Status: {health["status"]}')
        print(f'   Hummingbot API: {health["hummingbot_api"]}')
        print(f'   Connector: {health["connector"]}')
        if health['errors']:
            print(f'   Errors: {health["errors"]}')
    except Exception as e:
        print(f'   ❌ Health check failed: {e}')
        return
    
    # Test 2: Symbol conversion  
    print('\n2. Symbol Conversion:')
    test_symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    for symbol in test_symbols:
        hb_symbol = adapter._convert_symbol_to_hummingbot(symbol)
        print(f'   {symbol} → {hb_symbol}')
    
    # Test 3: Price fetching
    print('\n3. Price Fetching:')
    try:
        price = await adapter.get_current_price('BTC/USDT')
        print(f'   BTC/USDT: ${price.mid:.2f} (bid: ${price.bid:.2f}, ask: ${price.ask:.2f})')
        print(f'   Timestamp: {price.timestamp}')
    except Exception as e:
        print(f'   ❌ Price fetch failed: {e}')
        return
        
    # Test 4: Trading rules
    print('\n4. Trading Rules:')
    try:
        rules = await adapter.get_trading_rules('BTC/USDT')
        print(f'   Min order size: {rules.min_order_size}')
        print(f'   Price step: {rules.price_step}')
        print(f'   Min notional: {rules.min_notional}')
    except Exception as e:
        print(f'   ❌ Trading rules failed: {e}')
        return
    
    # Test 5: Multiple symbols
    print('\n5. Multiple Price Fetch:')
    try:
        symbols = ['BTC/USDT', 'ETH/USDT']
        prices = await adapter.get_multiple_prices(symbols)
        for symbol, price_data in prices.items():
            print(f'   {symbol}: ${price_data.mid:.2f}')
    except Exception as e:
        print(f'   ❌ Multiple prices failed: {e}')
        return
        
    print('\n✅ All Hummingbot API tests passed!')

if __name__ == "__main__":
    asyncio.run(test_hummingbot_connectivity())