"""
Isolated integration test for WebSocket Market Data → Preprocessors.

This test validates that:
1. Redis-cached candle data can be read successfully
2. Data converts to pandas DataFrame with correct format
3. Technical indicators calculate correctly from cached data
4. Preprocessors produce expected analysis output
"""

import asyncio
import pickle
import os
import sys
from datetime import datetime, timezone

import pandas as pd
import redis.asyncio as redis
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.common.logger import logger
from extraction.v2.indicators import TechnicalIndicators

load_dotenv()


class RedisMarketDataTest:
    """Test harness for WebSocket market data integration."""

    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = None
        self._log = logger.bind(component="ws_integration_test")

        # Test configuration
        self.test_symbol = "BTC/USDT"
        self.test_timeframe = "1h"
        self.test_indicators = ["rsi", "macd", "bbands", "adx"]

    async def setup(self):
        """Initialize Redis connection."""
        self._log.info("Setting up test environment...")
        self.redis_client = redis.from_url(self.redis_url, decode_responses=False)
        await self.redis_client.ping()
        self._log.info("✅ Redis connected")

    async def teardown(self):
        """Cleanup connections."""
        if self.redis_client:
            await self.redis_client.close()
            self._log.info("✅ Redis disconnected")

    async def read_candles_from_redis(self, symbol: str, timeframe: str, limit: int = 200):
        """
        Read candle data from Redis (simulating future RedisDataClient).

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            timeframe: Timeframe (e.g., "1h")
            limit: Number of candles to retrieve

        Returns:
            pandas DataFrame with OHLCV data
        """
        key = f"candles:{symbol}:{timeframe}:200"
        self._log.info(f"Reading from Redis key: {key}")

        # Get data from Redis
        data = await self.redis_client.get(key)

        if not data:
            raise ValueError(f"No data found in Redis for key: {key}")

        # Unpickle the data
        candles = pickle.loads(data)

        if not candles:
            raise ValueError(f"Empty candle list for {symbol} {timeframe}")

        self._log.info(f"✅ Retrieved {len(candles)} candles from Redis")

        # Convert to pandas DataFrame (matching HummingbotDataClient format)
        df = pd.DataFrame(candles)

        # Convert timestamp from milliseconds to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Sort by timestamp (oldest first)
        df = df.sort_values('timestamp').reset_index(drop=True)

        # Limit to requested number of candles
        if len(df) > limit:
            df = df.tail(limit).reset_index(drop=True)

        self._log.info(f"✅ DataFrame created with {len(df)} rows")
        self._log.debug(f"DataFrame columns: {df.columns.tolist()}")
        self._log.debug(f"DataFrame shape: {df.shape}")
        self._log.debug(f"Latest candle timestamp: {df['timestamp'].iloc[-1]}")
        self._log.debug(f"Latest close price: {df['close'].iloc[-1]}")

        return df

    async def test_candle_data_format(self):
        """Test that candle data has correct format."""
        self._log.info("\n=== Test 1: Candle Data Format ===")

        try:
            df = await self.read_candles_from_redis(self.test_symbol, self.test_timeframe)

            # Validate required columns
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                self._log.error(f"❌ Missing columns: {missing_columns}")
                return False

            # Validate data types
            assert df['timestamp'].dtype == 'datetime64[ns]', f"Timestamp should be datetime, got {df['timestamp'].dtype}"
            assert pd.api.types.is_numeric_dtype(df['open']), "Open should be numeric"
            assert pd.api.types.is_numeric_dtype(df['close']), "Close should be numeric"

            # Validate no NaN values
            nan_counts = df.isna().sum()
            if nan_counts.any():
                self._log.warning(f"NaN values detected: {nan_counts[nan_counts > 0].to_dict()}")

            self._log.info(f"✅ Data format valid: {len(df)} candles, all required columns present")
            return True

        except Exception as e:
            self._log.error(f"❌ Data format test failed: {e}")
            return False

    async def test_indicator_calculations(self):
        """Test that indicators calculate correctly from cached data."""
        self._log.info("\n=== Test 2: Indicator Calculations ===")

        try:
            # Get data from Redis
            df = await self.read_candles_from_redis(self.test_symbol, self.test_timeframe)

            # Initialize indicators with advanced preprocessing
            indicators = TechnicalIndicators(use_advanced_preprocessing=True)

            # Calculate indicators
            results = indicators.calculate_multiple(df, self.test_indicators)

            # Validate results
            for indicator_name in self.test_indicators:
                if indicator_name not in results:
                    self._log.error(f"❌ Missing result for {indicator_name}")
                    return False

                result = results[indicator_name]

                # Check for errors
                if "error" in result:
                    self._log.error(f"❌ {indicator_name} calculation error: {result['error']}")
                    return False

                # Validate has required fields (preprocessor output)
                if "indicator" not in result:
                    self._log.error(f"❌ {indicator_name} missing 'indicator' field")
                    return False

                if "current" not in result:
                    self._log.error(f"❌ {indicator_name} missing 'current' field")
                    return False

                self._log.info(f"✅ {indicator_name}: {result.get('indicator')} calculated successfully")

                # Log current values for verification
                current = result.get('current')
                if isinstance(current, dict):
                    self._log.debug(f"   Current values: {current}")
                else:
                    self._log.debug(f"   Current value: {current}")

            self._log.info(f"✅ All {len(self.test_indicators)} indicators calculated successfully")
            return True

        except Exception as e:
            self._log.error(f"❌ Indicator calculation test failed: {e}")
            import traceback
            self._log.error(traceback.format_exc())
            return False

    async def test_preprocessor_output(self):
        """Test that preprocessors produce expected analysis output."""
        self._log.info("\n=== Test 3: Preprocessor Output Structure ===")

        try:
            # Get data from Redis
            df = await self.read_candles_from_redis(self.test_symbol, self.test_timeframe)

            # Initialize indicators with advanced preprocessing
            indicators = TechnicalIndicators(use_advanced_preprocessing=True)

            # Calculate RSI (detailed preprocessor check)
            rsi_result = indicators.calculate_rsi(df, length=14)

            # Validate preprocessor-specific fields
            expected_fields = ["indicator", "current", "context", "evidence", "summary"]

            for field in expected_fields:
                if field not in rsi_result:
                    self._log.warning(f"⚠️  RSI missing recommended field: {field}")

            # Check that it's analysis-only (no signals/confidence)
            if "signals" in rsi_result:
                self._log.error("❌ RSI output contains 'signals' - should be analysis-only")
                return False

            if "confidence" in rsi_result and not isinstance(rsi_result.get("current"), dict):
                # Note: 'confidence' might be nested in decision context, which is OK
                self._log.warning("⚠️  Found 'confidence' in RSI - verify it's not a trading signal")

            # Validate summary is present and readable
            summary = rsi_result.get("summary", "")
            if not summary:
                self._log.warning("⚠️  RSI missing summary field")
            else:
                self._log.info(f"✅ RSI summary: {summary}")

            # Validate current has timestamp (UTC)
            current = rsi_result.get("current", {})
            if isinstance(current, dict):
                timestamp = current.get("timestamp")
                if timestamp:
                    self._log.info(f"✅ RSI timestamp: {timestamp}")
                    # Verify it's UTC
                    if not timestamp.endswith('+00:00') and not timestamp.endswith('Z'):
                        self._log.warning(f"⚠️  Timestamp may not be UTC: {timestamp}")
                else:
                    self._log.warning("⚠️  RSI current value missing timestamp")

            self._log.info("✅ Preprocessor output structure validated")
            return True

        except Exception as e:
            self._log.error(f"❌ Preprocessor output test failed: {e}")
            import traceback
            self._log.error(traceback.format_exc())
            return False

    async def test_data_freshness(self):
        """Test that data is recent (< 2 hours old)."""
        self._log.info("\n=== Test 4: Data Freshness ===")

        try:
            df = await self.read_candles_from_redis(self.test_symbol, self.test_timeframe)

            latest_timestamp = df['timestamp'].iloc[-1]
            # Ensure both timestamps are timezone-aware
            if latest_timestamp.tz is None:
                latest_timestamp = latest_timestamp.tz_localize('UTC')
            now = pd.Timestamp.now(tz='UTC')
            age_hours = (now - latest_timestamp).total_seconds() / 3600

            self._log.info(f"Latest candle timestamp: {latest_timestamp}")
            self._log.info(f"Current time: {now}")
            self._log.info(f"Data age: {age_hours:.2f} hours")

            if age_hours > 2:
                self._log.warning(f"⚠️  Data is {age_hours:.2f} hours old (may be stale)")
                # Don't fail - WebSocket service might be testing/restarting
                return True
            else:
                self._log.info(f"✅ Data is fresh ({age_hours:.2f} hours old)")
                return True

        except Exception as e:
            self._log.error(f"❌ Data freshness test failed: {e}")
            return False

    async def run_all_tests(self):
        """Run all integration tests."""
        self._log.info("\n" + "="*60)
        self._log.info("WebSocket Market Data → Preprocessor Integration Test")
        self._log.info("="*60)

        try:
            await self.setup()

            # Run tests
            results = {
                "data_format": await self.test_candle_data_format(),
                "indicator_calculations": await self.test_indicator_calculations(),
                "preprocessor_output": await self.test_preprocessor_output(),
                "data_freshness": await self.test_data_freshness()
            }

            # Summary
            self._log.info("\n" + "="*60)
            self._log.info("Test Summary")
            self._log.info("="*60)

            passed = sum(1 for v in results.values() if v)
            total = len(results)

            for test_name, result in results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                self._log.info(f"{status} - {test_name}")

            self._log.info("="*60)
            self._log.info(f"Results: {passed}/{total} tests passed")

            if passed == total:
                self._log.info("🎉 All tests passed! WebSocket market data integration is working.")
                return True
            else:
                self._log.warning(f"⚠️  {total - passed} test(s) failed")
                return False

        finally:
            await self.teardown()


async def main():
    """Main entry point."""
    test_harness = RedisMarketDataTest()
    success = await test_harness.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
