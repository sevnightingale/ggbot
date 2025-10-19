# Hummingbot Integration Map - Visual Summary

## Current Architecture (Before Redis)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GGBot Orchestrator (ggbot.py)                   │
│                                                                          │
│  _extraction_engines = {                                                │
│    "user_1": ExtractionEngineV2(...),  ← One per user                  │
│    "user_2": ExtractionEngineV2(...),                                   │
│  }                                                                       │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ _run_extraction_v2()
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────────────┐
│            ExtractionEngineV2 (extraction/v2/extraction_engine.py)      │
│                                                                          │
│  Components:                                                             │
│  • HummingbotDataClient (1 instance per engine)                         │
│  • TechnicalIndicators (pandas-ta)                                      │
│  • SupabaseStorage (DB persistence)                                     │
│                                                                          │
│  Flow:                                                                   │
│  1. extract_for_symbol(symbol, indicators, timeframe, limit)            │
│  2. await data_client.get_candles_with_fallback()  ← KEY CALL           │
│  3. indicators.calculate_multiple(df, indicators)                       │
│  4. supabase_storage.store_extraction_result()                          │
└────────────────────────┬────────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────────────┐
│        HummingbotDataClient (extraction/v2/data_client.py)              │
│                                                                          │
│  async def get_candles_with_fallback(symbol, timeframe, limit):         │
│    exchanges = ["binance", "kucoin", "gate_io", "ascend_ex", "okx"]    │
│    for exchange in exchanges:                                           │
│      try:                                                                │
│        return await get_candles(symbol, timeframe, limit, exchange)     │
│      except:                                                             │
│        continue  # Try next exchange                                    │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ HTTP POST
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────────────┐
│              Hummingbot API (localhost:8888)                            │
│                                                                          │
│  POST /market-data/candles                                              │
│  {                                                                       │
│    "connector_name": "kucoin",                                          │
│    "trading_pair": "BTC-USDT",                                          │
│    "interval": "1h",                                                    │
│    "max_records": 200                                                   │
│  }                                                                       │
│                                                                          │
│  Returns: [                                                             │
│    {"timestamp": 1756843200.0, "open": 110805.6, ...},                 │
│    ...                                                                   │
│  ]                                                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Proposed Architecture (With Redis Service)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    GGBot Orchestrator (no changes)                      │
└────────────────────────┬────────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────────────┐
│            ExtractionEngineV2 (no changes required)                     │
└────────────────────────┬────────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────────────┐
│        HummingbotDataClient (MODIFIED - add Redis check)                │
│                                                                          │
│  async def get_candles(symbol, timeframe, limit, connector):            │
│                                                                          │
│    # 1. CHECK REDIS CACHE FIRST ← NEW                                   │
│    cache_key = f"candles:{connector}:{symbol}:{timeframe}"              │
│    cached_df = await redis_client.get(cache_key)                        │
│                                                                          │
│    if cached_df and is_fresh(cached_df, timeframe):                     │
│      return cached_df.tail(limit)  # CACHE HIT ✅                       │
│                                                                          │
│    # 2. FALLBACK TO HUMMINGBOT (cache miss or stale)                    │
│    df = await _fetch_from_hummingbot(...)                               │
│    return df                                                             │
└──────────────┬──────────────────────────────────────────┬───────────────┘
               │ Cache miss                                │ Cache hit (90%+)
               ↓                                           ↓
┌──────────────────────────────┐           ┌──────────────────────────────┐
│   Hummingbot API             │           │   Redis Cache                │
│   (10% of requests)          │           │   (90% of requests)          │
└──────────────────────────────┘           └──────────────┬───────────────┘
                                                           │ Updated by...
                                                           ↓
┌─────────────────────────────────────────────────────────────────────────┐
│         Market Data Service (NEW - PM2 background process)              │
│                                                                          │
│  Infinite loop (every 7 seconds):                                       │
│                                                                          │
│  for symbol in ALL_SYMBOLS:  # 141 symbols                              │
│    for timeframe in ["5m", "15m", "30m", "1h", "4h", "1d"]:            │
│      for exchange in ["binance", "kucoin", "okx", "gate_io", ...]:     │
│                                                                          │
│        # Fetch candles via Hummingbot                                   │
│        df = await hbot_client.get_candles(symbol, timeframe, 200, ex)   │
│                                                                          │
│        # Store in Redis with TTL                                        │
│        cache_key = f"candles:{exchange}:{symbol}:{timeframe}"           │
│        ttl = get_ttl_for_timeframe(timeframe)  # 10min to 48hr         │
│        await redis_client.setex(cache_key, ttl, serialize(df))          │
│                                                                          │
│        await asyncio.sleep(0.05)  # Stagger to avoid rate limits       │
│                                                                          │
│  # Sleep until next cycle                                               │
│  await asyncio.sleep(7)                                                 │
└─────────────────────────┬───────────────────────────────────────────────┘
                          │ Continuous updates
                          ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         Redis (localhost:6379)                          │
│                                                                          │
│  Key Structure:                                                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ candles:binance:BTC/USDT:1h → DataFrame (200 candles) TTL:2hr  │    │
│  │ candles:kucoin:BTC/USDT:15m → DataFrame (200 candles) TTL:30m  │    │
│  │ candles:okx:ETH/USDT:4h     → DataFrame (200 candles) TTL:8hr  │    │
│  │ ...                                                              │    │
│  │ Total: ~846 keys (141 symbols × 6 timeframes)                   │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  Memory Usage: ~300-500MB (compressed DataFrames)                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## API Call Reduction Visualization

### Before Redis (10 concurrent bots, same symbol/timeframe):

```
Bot 1 ──┐
Bot 2 ──┤
Bot 3 ──┤
Bot 4 ──┼──> 10 separate calls ──> Hummingbot API
Bot 5 ──┤
Bot 6 ──┤
Bot 7 ──┤
Bot 8 ──┤
Bot 9 ──┤
Bot 10 ─┘

Result: 10 API calls, 10× network traffic
```

### After Redis (10 concurrent bots, same symbol/timeframe):

```
Bot 1 ──┐
Bot 2 ──┤
Bot 3 ──┤
Bot 4 ──┼──> 10 cache reads ──> Redis (instant)
Bot 5 ──┤
Bot 6 ──┤
Bot 7 ──┤
Bot 8 ──┤
Bot 9 ──┤
Bot 10 ─┘

Background Service ──> 1 API call every 7s ──> Hummingbot API

Result: 0 API calls from bots, 90%+ reduction in Hummingbot load
```

---

## Data Flow Timeline (1-Hour Candle Example)

```
Time: 14:00:00 UTC (candle close)
│
├─ 14:00:30 UTC (30s delay)
│  │
│  ├─ Market Data Service: Fetch BTC/USDT 1h from Hummingbot
│  │  └─ Store in Redis: candles:kucoin:BTC/USDT:1h
│  │     TTL: 2 hours
│  │
│  ├─ APScheduler: Trigger bot executions
│  │  └─ All 1h bots start their cycles
│  │
│  └─ ExtractionEngineV2: Request BTC/USDT 1h candles
│     ├─ HummingbotDataClient.get_candles()
│     │  ├─ Check Redis: CACHE HIT ✅
│     │  └─ Return DataFrame (no API call)
│     │
│     ├─ Calculate indicators (RSI, MACD, etc.)
│     └─ Store to Supabase
│
├─ 14:00:35 UTC - Bot 1 completes extraction (5 seconds)
├─ 14:00:36 UTC - Bot 2 completes extraction (6 seconds)
├─ ...
│
├─ 14:00:07 UTC (7s cycle)
│  └─ Market Data Service: Update all cached candles
│     ├─ BTC/USDT 1h (no change yet - same candle)
│     ├─ ETH/USDT 1h (no change)
│     └─ ... all symbols/timeframes
│
├─ ...
│
├─ 15:00:30 UTC (next hour)
│  ├─ Market Data Service: Fetch fresh candles
│  │  └─ Redis now has NEW candle (14:00-15:00)
│  │
│  └─ Bots execute with fresh data
│
└─ ...
```

---

## File Dependency Tree

```
ggbot.py (Orchestrator)
│
├─ extraction/v2/extraction_engine.py (ExtractionEngineV2)
│  │
│  ├─ extraction/v2/data_client.py (HummingbotDataClient) ← MODIFY THIS
│  │  │
│  │  ├─ aiohttp (HTTP client)
│  │  ├─ core/common/logger.py
│  │  └─ core/symbols/standardizer.py
│  │
│  ├─ extraction/v2/indicators.py (TechnicalIndicators)
│  │  └─ pandas-ta
│  │
│  └─ extraction/v2/supabase_storage.py (SupabaseStorage)
│     └─ core/common/db.py
│
├─ decision/engine_v2.py (DecisionEngineV2)
│  │
│  └─ decision/providers/ccxt_provider.py (CCXTPriceProvider)
│     └─ ccxt (INDEPENDENT - not using Hummingbot)
│
└─ trading/paper/supabase_service.py (SupabasePaperTradingService)
   │
   └─ trading/paper/market_data.py (MarketDataAdapter)
      └─ Uses Hummingbot for PRICES (not candles)
         └─ POST /market-data/prices
```

---

## Critical Integration Points

### Point 1: HummingbotDataClient.get_candles()
**File:** `/home/sev/ggbot/extraction/v2/data_client.py`
**Line:** 83-156
**Change:** Add Redis check before Hummingbot API call
**Impact:** Zero changes to consumers (same interface)

### Point 2: Market Data Service (NEW)
**File:** `/home/sev/ggbot/core/services/market_data_service.py` (CREATE)
**Process:** PM2-managed background service
**Change:** Brand new service
**Impact:** Reduces Hummingbot API load by 90%+

### Point 3: Redis Client Singleton
**File:** `/home/sev/ggbot/core/sse/redis_status.py` (EXISTS)
**Line:** 16-26
**Change:** Reuse existing `get_redis_client()` function
**Impact:** No new infrastructure needed (Redis already in use)

---

## Symbol/Timeframe Coverage Matrix

```
                 5m    15m   30m   1h    4h    1d
BTC/USDT         ✓     ✓     ✓     ✓     ✓     ✓
ETH/USDT         ✓     ✓     ✓     ✓     ✓     ✓
SOL/USDT         ✓     ✓     ✓     ✓     ✓     ✓
...
(141 symbols)
...
ZRX/USDT         ✓     ✓     ✓     ✓     ✓     ✓

Total: 141 symbols × 6 timeframes = 846 cached datasets
```

Each dataset contains 200 candles, updated every 7 seconds.

---

## Redis Memory Calculation

```
Per DataFrame:
  • 200 candles
  • 6 columns (timestamp, open, high, low, close, volume)
  • ~64 bytes per value (float64 + timestamp)
  • Total: 200 × 6 × 64 = 76,800 bytes ≈ 75 KB (uncompressed)

Compressed (pickle or msgpack):
  • ~30 KB per DataFrame (60% compression ratio)

Total Memory:
  • 846 datasets × 30 KB = 25.38 MB (compressed)
  • With overhead: ~100-200 MB
  • Redis maxmemory recommendation: 512 MB

Conclusion: Extremely lightweight, no memory concerns.
```

---

## Testing Strategy

### Phase 1: Unit Tests
```python
# Test Redis client
test_redis_connection()
test_cache_set_get()
test_cache_expiry()

# Test HummingbotDataClient with Redis
test_cache_hit()
test_cache_miss()
test_cache_stale()
test_fallback_on_redis_failure()
```

### Phase 2: Integration Tests
```python
# Test full extraction flow
test_extraction_with_redis_cache()
test_multi_timeframe_parallel()
test_multi_bot_contention()
```

### Phase 3: Load Tests
```python
# Simulate production load
test_10_concurrent_bots()
test_100_concurrent_bots()
test_cache_hit_rate()
test_api_call_reduction()
```

### Phase 4: Production Validation
```
# Deploy to staging
- Monitor cache hit rates
- Monitor Hummingbot API load
- Monitor extraction times
- Monitor Redis memory usage

# Gradual rollout
- Start with 10% of bots
- Increase to 50% after 24h
- Full rollout after 1 week
```

---

**Document Version:** 1.0
**Companion to:** HUMMINGBOT_API_ANALYSIS.md
**Last Updated:** 2025-10-10
