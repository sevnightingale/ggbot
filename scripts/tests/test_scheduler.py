"""
Unit tests for the scheduler utilities.

Tests timing functions, cron generation, and Redis key formatting.
"""

import pytest
from datetime import datetime, timezone
from core.scheduler.utils import (
    cron_for,
    last_closed_close_ts,
    get_misfire_grace_time,
    format_redis_idempotency_key,
    get_redis_ttl_for_timeframe,
    TIMEFRAME_SECONDS
)


class TestCronGeneration:
    """Test cron trigger generation for different timeframes."""
    
    def test_cron_for_5m(self):
        """Test 5-minute cron trigger."""
        trigger = cron_for("5m")
        assert trigger.fields[4].expressions[0].step == 5  # minute every 5
        assert trigger.fields[5].expressions[0].value == 30  # second 30
    
    def test_cron_for_15m(self):
        """Test 15-minute cron trigger."""
        trigger = cron_for("15m")
        # Should fire at 0, 15, 30, 45 minutes
        minute_values = [expr.value for expr in trigger.fields[4].expressions]
        assert set(minute_values) == {0, 15, 30, 45}
        assert trigger.fields[5].expressions[0].value == 30  # second 30
    
    def test_cron_for_1h(self):
        """Test 1-hour cron trigger."""
        trigger = cron_for("1h")
        assert trigger.fields[4].expressions[0].value == 0  # minute 0
        assert trigger.fields[5].expressions[0].value == 30  # second 30
    
    def test_cron_for_1d(self):
        """Test 1-day cron trigger."""
        trigger = cron_for("1d")
        assert trigger.fields[3].expressions[0].value == 0  # hour 0
        assert trigger.fields[4].expressions[0].value == 0  # minute 0
        assert trigger.fields[5].expressions[0].value == 30  # second 30
    
    def test_cron_for_invalid_timeframe(self):
        """Test invalid timeframe raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported timeframe"):
            cron_for("invalid")


class TestCloseTimestampCalculation:
    """Test last closed candle timestamp calculation."""
    
    @pytest.mark.parametrize("timeframe,expected_offset", [
        ("5m", 300),    # 5 minutes
        ("15m", 900),   # 15 minutes
        ("30m", 1800),  # 30 minutes
        ("1h", 3600),   # 1 hour
        ("4h", 14400),  # 4 hours
        ("1d", 86400),  # 1 day
    ])
    def test_last_closed_close_ts_alignment(self, timeframe, expected_offset):
        """Test that close timestamps are properly aligned to timeframe boundaries."""
        # Test with various times
        test_times = [
            datetime(2025, 9, 8, 14, 32, 30, tzinfo=timezone.utc),  # Random time
            datetime(2025, 9, 8, 0, 0, 0, tzinfo=timezone.utc),     # Midnight
            datetime(2025, 9, 8, 12, 15, 45, tzinfo=timezone.utc),  # Quarter past noon
        ]
        
        for test_time in test_times:
            close_ts = last_closed_close_ts(timeframe, test_time)
            
            # Verify the timestamp is aligned to the timeframe boundary
            assert close_ts % expected_offset == 0, f"Timestamp {close_ts} not aligned to {expected_offset}s boundary"
            
            # Verify the close timestamp is before or equal to the test time
            assert close_ts <= int(test_time.timestamp()), f"Close timestamp {close_ts} is after test time"
    
    def test_last_closed_close_ts_specific_examples(self):
        """Test specific examples to verify correct boundary calculation."""
        # 14:32:30 UTC with 15m timeframe should give 14:30:00 (last completed 15m candle)
        test_time = datetime(2025, 9, 8, 14, 32, 30, tzinfo=timezone.utc)
        close_ts = last_closed_close_ts("15m", test_time)
        expected_close = datetime(2025, 9, 8, 14, 30, 0, tzinfo=timezone.utc)
        assert close_ts == int(expected_close.timestamp())
        
        # 14:00:00 UTC with 1h timeframe should give 14:00:00 (boundary case)
        test_time = datetime(2025, 9, 8, 14, 0, 0, tzinfo=timezone.utc)
        close_ts = last_closed_close_ts("1h", test_time)
        expected_close = datetime(2025, 9, 8, 14, 0, 0, tzinfo=timezone.utc)
        assert close_ts == int(expected_close.timestamp())
    
    def test_last_closed_close_ts_invalid_timeframe(self):
        """Test invalid timeframe raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported timeframe"):
            last_closed_close_ts("invalid")


class TestMisfireGraceTimes:
    """Test misfire grace time configuration."""
    
    @pytest.mark.parametrize("timeframe,expected_grace", [
        ("5m", 120),   # 2 minutes
        ("15m", 180),  # 3 minutes
        ("30m", 300),  # 5 minutes
        ("1h", 300),   # 5 minutes
        ("4h", 600),   # 10 minutes
        ("1d", 900),   # 15 minutes
    ])
    def test_get_misfire_grace_time(self, timeframe, expected_grace):
        """Test misfire grace times are correct for each timeframe."""
        assert get_misfire_grace_time(timeframe) == expected_grace
    
    def test_get_misfire_grace_time_invalid(self):
        """Test invalid timeframe raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported timeframe"):
            get_misfire_grace_time("invalid")


class TestRedisKeyFormatting:
    """Test Redis idempotency key formatting."""
    
    def test_format_redis_idempotency_key(self):
        """Test Redis key formatting."""
        key = format_redis_idempotency_key("user123", "config456", "15m", 1725804600)
        expected = "bot_exec:user123:config456:15m:1725804600"
        assert key == expected
    
    def test_format_redis_key_with_uuid(self):
        """Test Redis key formatting with UUID-style IDs."""
        user_id = "3d47c173-9234-47c7-b57b-9159c9df5dbd"
        config_id = "e249bb49-0455-4596-9657-09bf9e14ca14"
        key = format_redis_idempotency_key(user_id, config_id, "1h", 1725804600)
        expected = f"bot_exec:{user_id}:{config_id}:1h:1725804600"
        assert key == expected


class TestRedisTTL:
    """Test Redis TTL calculation."""
    
    @pytest.mark.parametrize("timeframe", ["5m", "15m", "30m", "1h", "4h", "1d"])
    def test_get_redis_ttl_for_timeframe(self, timeframe):
        """Test TTL calculation is reasonable for each timeframe."""
        ttl = get_redis_ttl_for_timeframe(timeframe)
        
        # TTL should be at least 1 hour
        assert ttl >= 3600
        
        # TTL should be at least 2x the timeframe duration
        timeframe_seconds = TIMEFRAME_SECONDS[timeframe]
        assert ttl >= timeframe_seconds * 2
        
        # TTL should not exceed 1 week
        assert ttl <= 7 * 24 * 3600
    
    def test_get_redis_ttl_invalid_timeframe(self):
        """Test invalid timeframe raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported timeframe"):
            get_redis_ttl_for_timeframe("invalid")


class TestTimeframeConstants:
    """Test timeframe constant definitions."""
    
    def test_timeframe_seconds_completeness(self):
        """Test that all supported timeframes have second mappings."""
        supported_timeframes = ["5m", "15m", "30m", "1h", "4h", "1d"]
        
        for tf in supported_timeframes:
            assert tf in TIMEFRAME_SECONDS
            assert TIMEFRAME_SECONDS[tf] > 0
    
    def test_timeframe_seconds_values(self):
        """Test that timeframe second values are correct."""
        assert TIMEFRAME_SECONDS["5m"] == 5 * 60
        assert TIMEFRAME_SECONDS["15m"] == 15 * 60
        assert TIMEFRAME_SECONDS["30m"] == 30 * 60
        assert TIMEFRAME_SECONDS["1h"] == 60 * 60
        assert TIMEFRAME_SECONDS["4h"] == 4 * 60 * 60
        assert TIMEFRAME_SECONDS["1d"] == 24 * 60 * 60