# Hummingbot-API Deprecation

**Date**: 2025-10-20
**Status**: Deprecated and Archived
**Replaced By**: Live Price Service + Universal Data Layer

---

## Summary

The Hummingbot-API integration has been deprecated and replaced with a simpler, more efficient architecture using the existing WebSocket market data service and Redis caching.

## Why Deprecated?

1. **Overkill for Simple Price Feeds**: Running a full Hummingbot Docker stack just to get current prices was unnecessarily complex
2. **Resource Intensive**: 3 Docker containers (hummingbot-api, postgres, emqx) consuming 200MB+ RAM
3. **Redundant Architecture**: We already had real-time market data streaming via WebSocket service
4. **Simpler Alternative**: Live candles from WebSocket provide sub-second price updates without additional infrastructure

## Migration Path

### What Was Removed

**Code Files** (archived in `archive/hummingbot/`):
- `trading/paper/market_data.py` - MarketDataAdapter class (469 lines)
- `extraction/v2/data_client.py` - HummingbotDataClient class (302 lines)
- `scripts/fix_hummingbot_network.sh` - Docker network fix script
- `DOCS/HBOT_API.md` - API documentation

**Infrastructure**:
- Hummingbot API Docker container (port 8888)
- PostgreSQL database for Hummingbot (port 5433)
- EMQX message broker (ports 1883+)

**Environment Variables**:
- `HBOT_USERNAME` - Removed from ecosystem.config.js
- `HBOT_PASSWORD` - Removed from ecosystem.config.js

### What Was Added

**New Files**:
- `trading/paper/live_price_service.py` - LivePriceService class (~200 lines)
- `core/services/websocket_market_data_service.py` - Enhanced to store live candles

**Architecture**:
- WebSocket service now stores both closed candles (200-window) AND current/live candles
- Redis key pattern: `price:live:{symbol}` (e.g., `price:live:BTC/USDT`)
- Updates every ~1 second as trades happen on Binance
- Sub-millisecond Redis access vs 800ms+ REST API calls

## Code Changes

### Paper Trading Service

**Before**:
```python
from .market_data import MarketDataAdapter

self.market_data = MarketDataAdapter()
market_price = await self.market_data.get_current_price(symbol)
```

**After**:
```python
from .live_price_service import LivePriceService

self.price_service = LivePriceService()
market_price = await self.price_service.get_current_price(symbol)
```

### Decision Engine

**Before**:
```python
from trading.paper.market_data import MarketDataAdapter

adapter = MarketDataAdapter()
market_price = await adapter.get_current_price_with_fallback(symbol)
```

**After**:
```python
from trading.paper.live_price_service import LivePriceService

price_service = LivePriceService()
market_price = await price_service.get_current_price(symbol)
```

## Performance Comparison

| Metric | Hummingbot-API | Live Price Service |
|--------|----------------|-------------------|
| **Latency** | 800ms+ (REST API) | <1ms (Redis cache) |
| **Update Frequency** | 30s cache | ~1 second (real-time) |
| **Infrastructure** | 3 Docker containers | 0 (reuses WebSocket service) |
| **Memory Usage** | ~200MB | ~0MB (shared with WebSocket) |
| **Complexity** | High (authentication, Docker, MQTT) | Low (direct Redis access) |

## Benefits

✅ **Faster**: Sub-millisecond price access vs 800ms+ API calls
✅ **Simpler**: Zero additional infrastructure needed
✅ **Real-time**: ~1 second updates vs 30 second cache
✅ **Reliable**: No Docker containers to fail or restart
✅ **Efficient**: Reuses existing WebSocket streams

## Rollback Instructions

If needed, rollback is straightforward:

1. **Restore archived files**:
```bash
cp archive/hummingbot/market_data.py trading/paper/
cp archive/hummingbot/data_client.py extraction/v2/
```

2. **Restore ecosystem.config.js**:
```bash
git checkout HEAD -- ecosystem.config.js
```

3. **Start Docker containers**:
```bash
docker start hummingbot-api
docker start hummingbot-postgres
docker start emqx
```

4. **Restart services**:
```bash
pm2 restart ggbot
```

## Notes

- The extraction system already migrated to Universal Data Layer (OHLCV via WebSocket)
- This completes the migration - no hummingbot-api dependencies remain
- Docker containers can be safely stopped and removed after testing

---

**Migration Completed**: 2025-10-20
**Tested**: Pending production validation
**Next Steps**: Stop and remove hummingbot Docker containers after 48h of stable operation
