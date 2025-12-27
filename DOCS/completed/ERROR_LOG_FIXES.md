# Error Log Investigation & Fix Plan

---
COMPLETED: 2025-12-27
CHANGELOG_ENTRY: ## 2025-12-27 - Error Log Fixes
TODO_SECTION: Error Log Investigation
---

**Created**: 2025-12-27
**Status**: COMPLETED

---

## Summary of Issues Found

| Issue | Severity | Frequency | Impact |
|-------|----------|-----------|--------|
| binance_funding adapter path | HIGH | Every 30 min | BTC/ETH funding rates failing |
| BinanceWebsocketQueueOverflow | MEDIUM | Every 30 min | Possible missed candle data |
| Redis cache TTL for higher timeframes | MEDIUM | Continuous | 4h/1d/1w timeframes have no data |

---

## Issue 1: binance_funding Adapter Path Resolution

### Root Cause

The `_adapter_name_to_module()` function in `gateway.py:268-307` maps adapter names to module paths based on keyword patterns. The function lacks a pattern for `funding` or `derivatives`, so it defaults to `market_data`:

```python
# Current code (gateway.py:286-305)
if 'websocket' in snake_case or 'rest' in snake_case or 'ccxt' in snake_case:
    category = 'market_data'
elif 'twitter' in snake_case or 'reddit' in snake_case or 'telegram' in snake_case:
    category = 'sentiment'
# ... other patterns ...
else:
    # Default to market_data  ← binance_funding falls here!
    category = 'market_data'
```

**Flow**:
1. YAML: `adapter: binance_funding`
2. Gateway converts: `binance_funding` → `market_intelligence.adapters.market_data.binance_funding`
3. Import fails: file is actually at `market_intelligence.adapters.derivatives.binance_funding`

### Proposed Fix

Add `funding` and `derivatives` to the pattern matching in `gateway.py`:

```python
# Add before the else clause (around line 301)
elif 'funding' in snake_case or 'derivatives' in snake_case:
    category = 'derivatives'
```

**File**: `market_intelligence/gateway.py:301`

**Non-breaking**: Yes - only adds new pattern, doesn't change existing behavior

---

## Issue 2: BinanceWebsocketQueueOverflow

### Root Cause

The `BinanceSocketManager` uses a default `max_queue_size=100`. With 700 streams (100 symbols × 7 timeframes), especially when:
- Multiple candles close simultaneously (e.g., every hour: 5m, 15m, 30m, 1h all close)
- Market volatility causes rapid updates
- Processing in `_handle_kline_message` can't keep up

The queue fills to 100 messages and overflows, raising `BinanceWebsocketQueueOverflow`.

**Current code** (`websocket_market_data_service.py:237`):
```python
self.socket_manager = BinanceSocketManager(self.binance_client)  # Uses default max_queue_size=100
```

### Proposed Fix

Increase `max_queue_size` to handle burst traffic:

```python
# Change line 237 to:
self.socket_manager = BinanceSocketManager(
    self.binance_client,
    max_queue_size=1000  # Increased from default 100
)
```

**Rationale**:
- 700 streams × burst of 2-3 messages = ~2000 messages possible during candle close events
- 1000 provides 10x buffer without excessive memory usage
- Each message is ~500 bytes, so 1000 queue = ~500KB max

**File**: `core/services/websocket_market_data_service.py:237`

**Non-breaking**: Yes - only increases queue capacity

---

## Issue 3: Redis Cache TTL for Higher Timeframes

### Root Cause

The WebSocket service uses a **fixed 1-hour TTL** for all candle data (`websocket_market_data_service.py:185-189` and `:389-393`):

```python
await self.redis_client.setex(
    key,
    3600,  # 1 hour TTL - same for all timeframes!
    pickle.dumps(candles)
)
```

**Problem**: Higher timeframes receive new candles less frequently:
- 5m: 12 candles/hour → TTL always refreshed
- 1h: 1 candle/hour → TTL barely refreshed
- 4h: 1 candle/4 hours → **cache expires before new candle**
- 1d: 1 candle/day → **cache expires ~23 hours before new candle**
- 1w: 1 candle/week → **cache expires ~6.9 days before new candle**

**Current state** (verified via Redis):
```
5m: 200 candles  ✓
15m: 200 candles ✓
30m: 200 candles ✓
1h: 1 candle     ⚠️ (only latest)
4h: NO DATA      ✗
1d: NO DATA      ✗
1w: NO DATA      ✗
```

### Proposed Fix

Use timeframe-aware TTL that ensures data survives between candles:

```python
# Add TTL mapping at class level (after line ~67)
TIMEFRAME_TTL = {
    '5m': 3600,      # 1 hour (12 candles in this period)
    '15m': 3600,     # 1 hour (4 candles in this period)
    '30m': 3600,     # 1 hour (2 candles in this period)
    '1h': 7200,      # 2 hours (safe buffer)
    '4h': 18000,     # 5 hours (1 candle + buffer)
    '1d': 90000,     # 25 hours (1 candle + buffer)
    '1w': 648000     # 7.5 days (1 candle + buffer)
}

# Update _fetch_and_store_historical (around line 185):
ttl = self.TIMEFRAME_TTL.get(timeframe, 3600)
await self.redis_client.setex(key, ttl, pickle.dumps(candles))

# Update _update_candle_window (around line 389):
ttl = self.TIMEFRAME_TTL.get(timeframe, 3600)
await self.redis_client.setex(key, ttl, pickle.dumps(candles))
```

**File**: `core/services/websocket_market_data_service.py`

**Non-breaking**: Yes - only changes TTL duration

---

## Implementation Plan

### Phase 1: Fix binance_funding adapter path (5 minutes)

1. Edit `market_intelligence/gateway.py`
2. Add `derivatives` category pattern at line ~301
3. Test: Restart ggbot, verify funding rate queries succeed

### Phase 2: Increase WebSocket queue size (5 minutes)

1. Edit `core/services/websocket_market_data_service.py`
2. Add `max_queue_size=1000` to BinanceSocketManager constructor
3. Restart market-data-ws: `pm2 restart market-data-ws`
4. Monitor: Check error logs for queue overflow (should disappear)

### Phase 3: Fix Redis TTL for higher timeframes (10 minutes)

1. Edit `core/services/websocket_market_data_service.py`
2. Add `TIMEFRAME_TTL` mapping
3. Update both `_fetch_and_store_historical` and `_update_candle_window`
4. Restart market-data-ws: `pm2 restart market-data-ws`
5. Verify: Check Redis after restart, confirm all timeframes have 200 candles

### Verification Steps

After all fixes:

```bash
# 1. Verify funding rate works
pm2 logs ggbot --lines 50 | grep -i "funding"

# 2. Verify no queue overflow
pm2 logs market-data-ws --lines 50 | grep -i "overflow"

# 3. Verify all timeframes cached
python -c "
import redis, pickle
r = redis.from_url('redis://localhost:6379')
for tf in ['5m', '15m', '30m', '1h', '4h', '1d', '1w']:
    key = f'ws:candles:BTC/USDT:{tf}:200'
    data = r.get(key)
    if data:
        candles = pickle.loads(data)
        print(f'{tf}: {len(candles)} candles')
    else:
        print(f'{tf}: NO DATA')
"
```

---

## Risk Assessment

| Fix | Risk | Mitigation |
|-----|------|------------|
| derivatives pattern | Very Low | Additive change, no existing behavior modified |
| Queue size increase | Low | Only increases buffer, no logic change |
| TTL increase | Low | Only extends cache lifetime, no logic change |

All fixes are backward-compatible and can be deployed without downtime.

---

## Files to Modify

1. `market_intelligence/gateway.py` - Add derivatives category pattern
2. `core/services/websocket_market_data_service.py` - Queue size + TTL fixes

**Total changes**: ~15 lines across 2 files
