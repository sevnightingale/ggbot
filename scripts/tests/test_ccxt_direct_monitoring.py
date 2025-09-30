#!/usr/bin/env python
"""
Test script to verify direct CCXT connection to BitMEX testnet for account monitoring.

This test uses CCXT library directly (not through MCP) to:
1. Connect to BitMEX testnet
2. Fetch account balance
3. Fetch open positions
4. Display the raw data format
5. Calculate key metrics like equity and available margin

This will help us understand the data structure before building the monitoring service.
"""

import os
import json
import asyncio
from datetime import datetime
from pprint import pprint
import ccxt.async_support as ccxt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_bitmex_direct_connection():
    """Test direct CCXT connection to BitMEX testnet."""
    
    print("=" * 80)
    print("BitMEX Direct CCXT Connection Test")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Get credentials from environment
    api_key = os.environ.get('EXCHANGE_API')
    api_secret = os.environ.get('EXCHANGE_SECRET')
    
    if not api_key or not api_secret:
        print("ERROR: Missing EXCHANGE_API or EXCHANGE_SECRET environment variables")
        return
    
    print(f"API Key: {api_key[:8]}... (hidden)")
    print(f"Secret: {'*' * 8} (hidden)")
    print()
    
    # Create BitMEX exchange instance with testnet enabled
    exchange = ccxt.bitmex({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {
            'testnet': True  # Use testnet
        }
    })
    
    try:
        print("1. Testing connection and loading markets...")
        await exchange.load_markets()
        print(f"✓ Connected to {exchange.name} testnet")
        print(f"✓ Loaded {len(exchange.markets)} markets")
        print()
        
        # Fetch account balance
        print("2. Fetching account balance...")
        balance = await exchange.fetch_balance()
        
        print("Raw balance data:")
        print("-" * 40)
        pprint(balance)
        print()
        
        # Extract key balance information
        if 'info' in balance:
            print("Balance summary:")
            print("-" * 40)
            if 'BTC' in balance:
                btc_balance = balance['BTC']
                print(f"BTC Total: {btc_balance.get('total', 0)}")
                print(f"BTC Free: {btc_balance.get('free', 0)}")
                print(f"BTC Used: {btc_balance.get('used', 0)}")
            
            # BitMEX often returns balance info in a different structure
            if isinstance(balance.get('info'), list) and len(balance['info']) > 0:
                # Find XBt (Bitcoin) balance
                btc_info = None
                for info in balance['info']:
                    if info.get('currency') == 'XBt':
                        btc_info = info
                        break
                
                if btc_info:
                    print(f"Wallet Balance: {btc_info.get('walletBalance', 0) / 100000000} BTC")
                    print(f"Margin Balance: {btc_info.get('marginBalance', 0) / 100000000} BTC")
                    print(f"Available Margin: {btc_info.get('availableMargin', 0) / 100000000} BTC")
                    print(f"Unrealised PNL: {btc_info.get('unrealisedPnl', 0) / 100000000} BTC")
                    print(f"Margin Used %: {btc_info.get('marginUsedPcnt', 0) * 100}%")
        print()
        
        # Fetch open positions
        print("3. Fetching open positions...")
        positions = await exchange.fetch_positions()
        
        print(f"Found {len(positions)} positions")
        print("-" * 40)
        
        if positions:
            for i, position in enumerate(positions):
                print(f"\nPosition {i + 1}:")
                print(f"  Symbol: {position.get('symbol')}")
                print(f"  Side: {position.get('side')}")
                print(f"  Contracts: {position.get('contracts')}")
                print(f"  Entry Price: {position.get('entryPrice')}")
                print(f"  Mark Price: {position.get('markPrice')}")
                print(f"  Unrealized PNL: {position.get('unrealizedPnl')}")
                print(f"  Percentage: {position.get('percentage')}%")
                print(f"  Margin Mode: {position.get('marginMode')}")
                
            print("\nRaw position data (first position):")
            print("-" * 40)
            pprint(positions[0])
        else:
            print("No open positions found")
        print()
        
        # Test specific position fetch
        print("4. Testing position fetch for BTC/USD...")
        try:
            # Try different symbol formats
            symbols_to_try = ['BTC/USD', 'BTC/USD:BTC', 'XBTUSD']
            btc_position = None
            
            for symbol in symbols_to_try:
                try:
                    btc_positions = await exchange.fetch_positions([symbol])
                    if btc_positions:
                        btc_position = btc_positions[0]
                        print(f"✓ Found BTC position using symbol: {symbol}")
                        break
                except Exception as e:
                    print(f"✗ Failed with symbol {symbol}: {str(e)}")
            
            if btc_position:
                print("\nBTC Position details:")
                print(f"  Contracts: {btc_position.get('contracts')}")
                print(f"  Notional: {btc_position.get('notional')}")
                print(f"  Liquidation Price: {btc_position.get('liquidationPrice')}")
        except Exception as e:
            print(f"Error fetching specific position: {e}")
        print()
        
        # Calculate account metrics
        print("5. Calculating account metrics...")
        print("-" * 40)
        
        # Get total equity (balance + unrealized PNL)
        total_balance = balance.get('BTC', {}).get('total', 0)
        
        # Convert unrealized PNL from string to float if needed
        unrealized_pnl = 0
        for pos in positions:
            pnl = pos.get('unrealizedPnl', 0)
            if isinstance(pnl, str):
                try:
                    pnl = float(pnl)
                except ValueError:
                    pnl = 0
            unrealized_pnl += pnl
        
        print(f"Total Balance: {total_balance} BTC")
        print(f"Total Unrealized PNL: {unrealized_pnl} BTC")
        print(f"Estimated Equity: {total_balance + unrealized_pnl} BTC")
        
        # Check for open orders
        print("5.5. Checking for open orders...")
        print("-" * 40)
        try:
            open_orders = await exchange.fetch_open_orders('BTC/USD:BTC')
            print(f"Found {len(open_orders)} open orders for BTC/USD")
            for order in open_orders:
                print(f"  Order {order['id']}: {order['side']} {order['amount']} @ {order['price']}")
        except Exception as e:
            print(f"Error fetching open orders: {e}")
        print()
        
        # Save raw data for analysis
        print("\n6. Saving raw data to file...")
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'exchange': 'bitmex_testnet',
            'balance': balance,
            'positions': positions,
            'metrics': {
                'total_balance': total_balance,
                'unrealized_pnl': unrealized_pnl,
                'equity': total_balance + unrealized_pnl,
                'position_count': len(positions)
            }
        }
        
        output_file = 'bitmex_account_data.json'
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        print(f"✓ Saved raw data to {output_file}")
        
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close the exchange connection
        await exchange.close()
        print("\n✓ Connection closed")


async def test_monitoring_loop():
    """Test a simple monitoring loop that updates every 10 seconds."""
    
    print("\n" + "=" * 80)
    print("Testing Monitoring Loop (3 iterations, 10 seconds apart)")
    print("=" * 80)
    
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
        await exchange.load_markets()
        
        for i in range(3):
            print(f"\n--- Update {i + 1} at {datetime.now().isoformat()} ---")
            
            # Fetch balance
            balance = await exchange.fetch_balance()
            btc_total = balance.get('BTC', {}).get('total', 0)
            
            # Fetch positions
            positions = await exchange.fetch_positions()
            
            print(f"BTC Balance: {btc_total}")
            print(f"Open Positions: {len(positions)}")
            
            if positions:
                for pos in positions:
                    print(f"  - {pos['symbol']}: {pos['contracts']} contracts, "
                          f"PNL: {pos.get('unrealizedPnl', 0)}")
            
            if i < 2:  # Don't sleep after last iteration
                print(f"\nWaiting 10 seconds...")
                await asyncio.sleep(10)
        
        print("\n✓ Monitoring loop test completed")
        
    except Exception as e:
        print(f"ERROR in monitoring loop: {e}")
    
    finally:
        await exchange.close()


async def main():
    """Run all tests."""
    # Test basic connection and data fetching
    await test_bitmex_direct_connection()
    
    # Run monitoring loop test automatically (comment out if not needed)
    # await test_monitoring_loop()
    
    print("\n✓ All tests completed")


if __name__ == "__main__":
    asyncio.run(main())