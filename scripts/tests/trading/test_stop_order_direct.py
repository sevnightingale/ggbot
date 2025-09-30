#!/usr/bin/env python
"""
Test stop order creation directly with CCXT to understand the correct parameter format.
"""

import os
import asyncio
import ccxt.async_support as ccxt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_stop_order_formats():
    """Test different formats for creating stop orders on BitMEX."""
    
    # Create exchange instance
    exchange = ccxt.bitmex({
        'apiKey': os.environ.get('EXCHANGE_API'),
        'secret': os.environ.get('EXCHANGE_SECRET'),
        'enableRateLimit': True,
        'options': {
            'testnet': True
        }
    })
    
    try:
        # Test parameters
        symbol = 'BTC/USD:BTC'
        side = 'sell'
        amount = 100  # minimum for BTC
        stop_price = 100000
        
        print("Testing BitMEX stop order creation...")
        print(f"Symbol: {symbol}")
        print(f"Side: {side}")
        print(f"Amount: {amount}")
        print(f"Stop Price: {stop_price}")
        
        # Test 1: Using create_order with type='stop'
        print("\n1. Testing create_order with type='stop' and stopPrice in params:")
        try:
            order1 = await exchange.create_order(
                symbol=symbol,
                type='stop',
                side=side,
                amount=amount,
                price=None,  # No limit price for pure stop order
                params={
                    'stopPx': stop_price,  # BitMEX uses stopPx
                    'execInst': 'Close'  # Close position only
                }
            )
            print(f"Success! Order: {order1['id']}")
            # Cancel the order
            await exchange.cancel_order(order1['id'], symbol)
        except Exception as e:
            print(f"Failed: {e}")
        
        # Test 2: Using create_order with type='stop' and price parameter
        print("\n2. Testing create_order with type='stop' and price parameter:")
        try:
            order2 = await exchange.create_order(
                symbol=symbol,
                type='stop',
                side=side,
                amount=amount,
                price=stop_price,  # Use price as stop price
                params={
                    'execInst': 'Close'
                }
            )
            print(f"Success! Order: {order2['id']}")
            # Cancel the order
            await exchange.cancel_order(order2['id'], symbol)
        except Exception as e:
            print(f"Failed: {e}")
        
        # Test 3: Check if create_stop_order exists with type parameter
        print("\n3. Testing create_stop_order method with type parameter:")
        if hasattr(exchange, 'create_stop_order'):
            try:
                # CCXT's create_stop_order signature: (symbol, type, side, amount, price, stopPrice)
                print("  a) With stopPrice as positional arg:")
                order3a = await exchange.create_stop_order(
                    symbol=symbol,
                    type='market',  # stop-market order
                    side=side,
                    amount=amount,
                    price=None,     # no limit price
                    stopPrice=stop_price  # trigger price
                )
                print(f"  Success! Order: {order3a['id']}")
                await exchange.cancel_order(order3a['id'], symbol)
            except Exception as e:
                print(f"  Failed: {e}")
        else:
            print("create_stop_order method not found")
            
        # Test 4: Check the signature of create_stop_order
        print("\n4. Checking create_stop_order signature:")
        if hasattr(exchange, 'create_stop_order'):
            import inspect
            sig = inspect.signature(exchange.create_stop_order)
            print(f"  Signature: {sig}")
            print(f"  Parameters: {list(sig.parameters.keys())}")
            
    finally:
        await exchange.close()

if __name__ == "__main__":
    asyncio.run(test_stop_order_formats())