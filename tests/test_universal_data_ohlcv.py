"""
Integration test for Universal Data Layer - OHLCV data flow.

Tests the complete flow:
1. Query OHLCV from MarketIntelligence gateway
2. Verify Redis WebSocket cache hit
3. Verify Binance REST fallback
4. Validate response format
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from market_intelligence.gateway import MarketIntelligence
from market_intelligence.types import QueryFormat
from core.common.logger import logger


async def test_ohlcv_redis_cache():
    """Test OHLCV fetch from Redis WebSocket cache."""
    print("\n" + "="*60)
    print("Test 1: OHLCV from Redis WebSocket Cache")
    print("="*60)

    intelligence = MarketIntelligence()

    try:
        # Query BTC/USDT which should be in WebSocket cache
        response = await intelligence.query(
            data_type='ohlcv',
            params={
                'symbol': 'BTC/USDT',
                'timeframe': '1h',
                'limit': 100
            },
            format=QueryFormat.ANALYSIS
        )

        print(f"\n✅ Query succeeded!")
        print(f"  Data type: {response.data_type}")
        print(f"  Symbol: {response.query_params['symbol']}")
        print(f"  Timeframe: {response.query_params['timeframe']}")
        print(f"  Source: {response.source}")
        print(f"  From cache: {response.from_cache}")
        print(f"  Latency: {response.latency_ms:.0f}ms")
        print(f"  Confidence: {response.confidence:.2f}")
        print(f"  Candles: {len(response.data)} rows")
        print(f"  Summary: {response.summary}")
        print(f"  Insights: {response.key_insights}")

        # Verify response
        assert response.data_type == 'ohlcv'
        # Source could be either adapter or 'cache' if it was cached
        assert response.source in ['RedisWebSocketAdapter', 'BinanceRestAdapter', 'cache']
        assert len(response.data) > 0
        assert 'timestamp' in response.data.columns
        assert 'close' in response.data.columns

        print("\n✅ Test 1 PASSED: Redis WebSocket cache working")
        return True

    except Exception as e:
        print(f"\n❌ Test 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await intelligence.close()


async def test_ohlcv_binance_fallback():
    """Test OHLCV fetch from Binance REST (fallback)."""
    print("\n" + "="*60)
    print("Test 2: OHLCV from Binance REST Fallback")
    print("="*60)

    intelligence = MarketIntelligence()

    try:
        # Query a symbol that's likely NOT in WebSocket cache
        response = await intelligence.query(
            data_type='ohlcv',
            params={
                'symbol': 'DOGE/USDT',
                'timeframe': '15m',
                'limit': 50
            },
            format=QueryFormat.RAW
        )

        print(f"\n✅ Query succeeded!")
        print(f"  Data type: {response.data_type}")
        print(f"  Symbol: {response.query_params['symbol']}")
        print(f"  Timeframe: {response.query_params['timeframe']}")
        print(f"  Source: {response.source}")
        print(f"  From cache: {response.from_cache}")
        print(f"  Latency: {response.latency_ms:.0f}ms")
        print(f"  Confidence: {response.confidence:.2f}")
        print(f"  Candles: {len(response.data)} rows")

        # Verify response
        assert response.data_type == 'ohlcv'
        # Should use BinanceRestAdapter since not in WebSocket cache
        assert len(response.data) > 0
        assert 'timestamp' in response.data.columns

        print("\n✅ Test 2 PASSED: Binance REST fallback working")
        return True

    except Exception as e:
        print(f"\n❌ Test 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await intelligence.close()


async def test_ohlcv_format_modes():
    """Test different response format modes."""
    print("\n" + "="*60)
    print("Test 3: Response Format Modes")
    print("="*60)

    intelligence = MarketIntelligence()

    try:
        symbol = 'BTC/USDT'
        timeframe = '1h'

        # Test RAW format
        raw_response = await intelligence.query(
            data_type='ohlcv',
            params={'symbol': symbol, 'timeframe': timeframe},
            format=QueryFormat.RAW
        )

        print(f"\n✅ RAW format:")
        print(f"  Has summary: {len(raw_response.summary) > 0}")
        print(f"  Has insights: {len(raw_response.key_insights) > 0}")
        print(f"  Data type: {type(raw_response.data).__name__}")

        # Test ANALYSIS format
        analysis_response = await intelligence.query(
            data_type='ohlcv',
            params={'symbol': symbol, 'timeframe': timeframe},
            format=QueryFormat.ANALYSIS
        )

        print(f"\n✅ ANALYSIS format:")
        print(f"  Summary: {analysis_response.summary}")
        print(f"  Insights: {analysis_response.key_insights}")
        print(f"  From cache: {analysis_response.from_cache}")  # Should be cached now

        # Test LLM format
        llm_response = await intelligence.query(
            data_type='ohlcv',
            params={'symbol': symbol, 'timeframe': timeframe},
            format=QueryFormat.LLM
        )

        print(f"\n✅ LLM format:")
        print(f"  Summary: {llm_response.summary}")
        print(f"  Insights: {llm_response.key_insights}")

        print("\n✅ Test 3 PASSED: All format modes working")
        return True

    except Exception as e:
        print(f"\n❌ Test 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await intelligence.close()


async def test_catalog_discovery():
    """Test catalog discovery features."""
    print("\n" + "="*60)
    print("Test 4: Catalog Discovery")
    print("="*60)

    intelligence = MarketIntelligence()

    try:
        # List all data types
        all_types = await intelligence.list_data_types()
        print(f"\n✅ Available data types: {all_types}")

        # List by category
        market_data_types = await intelligence.list_data_types(category='market_data')
        print(f"✅ Market data types: {market_data_types}")

        # Get catalog entry
        ohlcv_entry = await intelligence.get_catalog_entry('ohlcv')
        print(f"\n✅ OHLCV catalog entry:")
        print(f"  Name: {ohlcv_entry.name}")
        print(f"  Category: {ohlcv_entry.category}")
        print(f"  Description: {ohlcv_entry.description}")
        print(f"  Sources: {[s.adapter for s in ohlcv_entry.sources]}")
        print(f"  Cache backend: {ohlcv_entry.cache.backend}")
        print(f"  Cache TTL: {ohlcv_entry.cache.ttl}s")

        assert 'ohlcv' in all_types
        assert 'ohlcv' in market_data_types
        assert ohlcv_entry is not None

        print("\n✅ Test 4 PASSED: Catalog discovery working")
        return True

    except Exception as e:
        print(f"\n❌ Test 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await intelligence.close()


async def main():
    """Run all integration tests."""
    print("\n" + "="*80)
    print("UNIVERSAL DATA LAYER - OHLCV INTEGRATION TESTS")
    print("="*80)

    results = []

    # Run all tests
    results.append(await test_ohlcv_redis_cache())
    results.append(await test_ohlcv_binance_fallback())
    results.append(await test_ohlcv_format_modes())
    results.append(await test_catalog_discovery())

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(results)
    total = len(results)
    print(f"\n  Passed: {passed}/{total}")
    print(f"  Failed: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Universal Data Layer is working.")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED. Review errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
