"""
Diagnostic script to test WebSocket market data service manually.
This will help identify where the live price storage is failing.
"""

import asyncio
import os
import pickle
from datetime import datetime
import redis.asyncio as redis
from binance import AsyncClient, BinanceSocketManager
from dotenv import load_dotenv

load_dotenv()


async def test_websocket_live_candles():
    """Test WebSocket kline streaming and live candle storage."""
    print("=" * 80)
    print("WebSocket Market Data Service Diagnostic")
    print("=" * 80)

    # Connect to Redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_client = redis.from_url(redis_url, decode_responses=False)
    await redis_client.ping()
    print(f"✅ Redis connected: {redis_url}")

    # Connect to Binance
    binance_client = await AsyncClient.create()
    print("✅ Binance client created")

    # Create socket manager
    socket_manager = BinanceSocketManager(binance_client)

    # Subscribe to BTC/USDT 5m kline (most active)
    stream_name = "btcusdt@kline_5m"
    print(f"\n📡 Subscribing to {stream_name}...")

    socket = socket_manager.multiplex_socket([stream_name])

    message_count = 0
    live_candle_count = 0
    closed_candle_count = 0

    async with socket as stream:
        print("✅ WebSocket connected - waiting for messages...")
        print("\nMonitoring for 30 seconds...\n")

        start_time = datetime.now()

        while (datetime.now() - start_time).total_seconds() < 30:
            try:
                msg = await asyncio.wait_for(stream.recv(), timeout=5.0)
                message_count += 1

                # Extract kline data
                if 'data' in msg and 'k' in msg['data']:
                    kline = msg['data']['k']
                    symbol = kline['s']
                    timeframe = kline['i']
                    is_closed = kline['x']
                    close_price = float(kline['c'])

                    if not is_closed:
                        # This is a LIVE candle - should be stored
                        live_candle_count += 1

                        # Attempt to store it
                        candle = {
                            'timestamp': int(kline['t']),
                            'open': float(kline['o']),
                            'high': float(kline['h']),
                            'low': float(kline['l']),
                            'close': float(kline['c']),
                            'volume': float(kline['v'])
                        }

                        # Store with slash format
                        symbol_slash = f"{symbol[:-4]}/{symbol[-4:]}"
                        key = f"price:live:{symbol_slash}"

                        await redis_client.setex(
                            key,
                            60,  # 60 second TTL
                            pickle.dumps(candle)
                        )

                        print(f"[{datetime.now().strftime('%H:%M:%S')}] LIVE CANDLE: {symbol_slash} {timeframe} - ${close_price:.2f} -> Stored at {key}")

                        # Verify it was stored
                        stored = await redis_client.get(key)
                        if stored:
                            print(f"  ✅ Verified: Key exists in Redis with TTL {await redis_client.ttl(key)}s")
                        else:
                            print(f"  ❌ ERROR: Key NOT found in Redis!")
                    else:
                        # Closed candle
                        closed_candle_count += 1
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] CLOSED CANDLE: {symbol} {timeframe} - ${close_price:.2f}")

            except asyncio.TimeoutError:
                print("  (No message received in last 5 seconds)")
                continue
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                import traceback
                traceback.print_exc()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total messages received: {message_count}")
    print(f"Live candles (unclosed): {live_candle_count}")
    print(f"Closed candles: {closed_candle_count}")

    # Check Redis for live price keys
    print("\nChecking Redis for price:live:* keys...")
    keys = []
    async for key in redis_client.scan_iter(match="price:live:*"):
        keys.append(key.decode('utf-8'))

    print(f"Found {len(keys)} live price keys in Redis:")
    for key in keys[:10]:  # Show first 10
        ttl = await redis_client.ttl(key)
        print(f"  - {key} (TTL: {ttl}s)")

    # Cleanup
    await binance_client.close_connection()
    await redis_client.close()

    print("\n✅ Diagnostic complete")


if __name__ == "__main__":
    asyncio.run(test_websocket_live_candles())
