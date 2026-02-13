# HIP-3: Equities, Commodities & Indices via Hyperliquid

**Status**: PLANNED — API verification complete, ready to implement
**Created**: 2026-02-11
**Priority**: P2 — after current Hyperliquid live trading stabilizes

---

## Overview

Hyperliquid's HIP-3 protocol enables builder-deployed perpetual markets. Third-party builders (XYZ, Felix Exchange, Kinetiq Markets, dreamcash, Ventral) deploy and manage their own perp markets on top of Hyperliquid's infrastructure. These markets are invisible to the standard `meta()` call and use dex-prefixed symbols like `xyz:NVDA`.

This would make ggbots one of the first AI trading platforms to support equities and commodities via DeFi.

---

## Available Markets (verified 2026-02-11)

### XYZ Dex — $809M/day volume, $635M OI, 44 assets

| Asset | Category | 24h Volume | OI | Price | Max Lev |
|-------|----------|-----------|-----|-------|---------|
| SILVER | Commodity | $314M | $130M | $83.87 | 20x |
| XYZ100 | Index | $233M | $113M | $25,176 | 25x |
| GOLD | Commodity | $44M | $111M | $5,061 | 20x |
| NVDA | Equity | $26M | $58M | $189 | 10x |
| MU | Equity | $18M | $49M | $375 | 10x |
| COPPER | Commodity | $17M | $49M | $5.99 | 20x |
| HOOD | Equity | $15M | $6M | $78 | 10x |
| SNDK | Equity | $15M | $22M | $542 | 10x |
| TSLA | Equity | $15M | $16M | $425 | 10x |

Also: INTC, GOOGL, MSTR, AMZN, AAPL, MSFT, META, AMD, ORCL, NFLX, PLTR, COIN, EUR, JPY, CL, NATGAS, PLATINUM, BABA, RIVN, and more.

### Other Dexes

| Dex | 24h Volume | Notable Markets |
|-----|-----------|-----------------|
| cash | $155M | USA500 ($92M), SILVER, INTC, HOOD |
| km | $22M | US500 ($9M), USTECH ($4M), SILVER |
| hyna | $20M | BTC, ETH, HYPE (crypto, different leverage) |
| flx | $14M | NVDA, SILVER, TSLA, PLATINUM |
| vntl | $8M | MAG7, NUCLEAR, OPENAI, SEMIS, SPACEX |

**Total across all HIP-3 dexes: ~$1.03B 24h volume**

---

## API Verification Results

### Candle Data — Identical Format

HIP-3 candles use the same `candleSnapshot` API with `req` wrapper format. Response structure is byte-for-byte identical to standard perps:

```json
{"t": 1770710400000, "T": 1770724799999, "s": "xyz:NVDA", "i": "4h",
 "o": "191.11", "c": "191.49", "h": "191.62", "l": "190.76", "v": "11685.559", "n": 2010}
```

Same keys as standard perp BTC candle — `{t, T, s, i, o, c, h, l, v, n}`.

### Timeframe Support — All 7 Work

| Interval | Candles (7d) | Latency |
|----------|-------------|---------|
| 1m | 5,014 | 518ms |
| 5m | 2,017 | 368ms |
| 15m | 673 | 275ms |
| 30m | 337 | 198ms |
| 1h | 169 | 160ms |
| 4h | 43 | 122ms |
| 1d | 8 | 93ms |

### History Depth

- NVDA 4h, 30 days: 181 candles (back to Jan 12)
- GOLD 1d, 90 days: 52 candles (back to Dec 22)
- SILVER 1h, 30 days: 721 candles

### Margin Mode — All Isolated

ALL HIP-3 assets are `onlyIsolated: true` with either `strictIsolated` or `noCross` margin mode. Standard crypto perps (BTC, ETH) support cross margin. Our current code passes `is_cross=True` which would FAIL for HIP-3.

### Position Sizing

| Asset | szDecimals | Min Increment | Min $ | maxLeverage |
|-------|-----------|---------------|-------|-------------|
| NVDA | 3 | 0.001 | $0.19 | 10x |
| TSLA | 3 | 0.001 | $0.42 | 10x |
| GOLD | 4 | 0.0001 | $0.51 | 20x |
| SILVER | 2 | 0.01 | $0.84 | 20x |
| XYZ100 | 4 | 0.0001 | $2.51 | 25x |

Minimum notional likely ~$10 (Hyperliquid standard), not the szDecimals minimum.

---

## Implementation Plan (POC — xyz:NVDA)

### Architecture: Option A — New Adapter, Same Pipeline

Add `HyperliquidCandleAdapter` as Priority 3 in the existing MarketIntelligence adapter cascade:

```
Bot fires (every 5m/1h/4h)
    → MarketIntelligence.query('ohlcv', {symbol: 'xyz:NVDA', timeframe: '4h'})
        → MI cache check (<1ms)
        → Priority 1: RedisWebSocketAdapter — miss, 5ms (no WS data for NVDA)
        → Priority 2: BinanceRestAdapter — fail, 76ms (Binance doesn't know xyz:NVDA)
        → Priority 3: HyperliquidCandleAdapter — SUCCESS, ~300ms
        → Cache result in MI for 3600s
    → DataFrame [timestamp, open, high, low, close, volume]
    → Technical indicators (unchanged)
    → Decision engine → Trade
```

The ~80ms "waste" from Redis+Binance failures only occurs on MI cache miss (~once/hour). After first successful fetch, MI cache serves data for subsequent requests.

### Files to Change (1 new, 5 edits)

1. **NEW** `market_intelligence/adapters/market_data/hyperliquid_candle.py`
   - Extends `DataAdapter`, implements `fetch(params) -> AdapterResponse`
   - Fast-rejects non-HIP-3 symbols via `:` check (avoids hitting HL API for crypto)
   - Calls `candleSnapshot` with `req` wrapper, converts to standard DataFrame
   - Uses `aiohttp` from base class

2. **EDIT** `market_intelligence/catalog/data_types/market_data/ohlcv.yaml`
   - Add `HyperliquidCandleAdapter` as Priority 3 source
   - Gateway auto-resolves to `market_intelligence.adapters.market_data.hyperliquid_candle`

3. **EDIT** `core/symbols/registry.py`
   - Add `nvda_xyz` entry: `platform: "xyz:NVDA"`, `ccxt: "xyz:NVDA"`, `hyperliquid: "xyz:NVDA"`, `hip3: True`, `sz_decimals: 3`, `max_leverage: 10`
   - Add `is_hip3_symbol(symbol)` helper (checks for `:` in symbol)

4. **EDIT** `ggbot.py` ~L1744-1758
   - Skip `is_websocket_cached` validation for HIP-3 symbols

5. **EDIT** `trading/paper/hybrid_price_service.py`
   - Add Strategy 4: Hyperliquid `allMids(dex=...)` for HIP-3 price lookups
   - Needed by position sizing + dashboard enrichment

6. **EDIT** `trading/live/hyperliquid_service.py`
   - `update_leverage(is_cross=False)` for HIP-3 (isolated-only)
   - Dynamic `min_quantity` from `sz_decimals` + $10 min notional floor
   - Dynamic rounding precision from `sz_decimals`

### What Does NOT Change

- Extraction engine — uses `UniversalDataClient` unchanged
- Technical indicators — identical DataFrame format
- Decision engine — same LLM pipeline
- Dashboard monitoring — `LivePriceService` fix covers it
- Telegram publishing — mode-agnostic, already works

---

## Post-POC Expansion

After xyz:NVDA validates end-to-end:

1. **Curated asset set**: Add top 10 equities + top 5 commodities + 2-3 indices to registry
2. **Frontend symbol picker**: New asset class categories (Equities, Commodities, Indices, Forex)
3. **Dynamic discovery**: Query `perpDexs` API at startup to auto-populate available HIP-3 assets
4. **Multi-dex deduplication**: Same asset on multiple dexes (NVDA on xyz, flx, km, cash) — pick most liquid
5. **Paper trading**: Enable paper trading for HIP-3 assets (currently only Hyperliquid live mode)

---

## References

- [HIP-3 Docs](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips/hip-3-builder-deployed-perpetuals)
- [FalconX: Transformational Potential of HIP-3](https://www.falconx.io/newsroom/the-transformational-potential-of-hyperliquids-hip-3)
- [Blockworks: HIP-3 brings equity perps to crypto](https://blockworks.co/news/hip-3-equity-perps)
- [Neurobro: Hyperliquid Macro Perps Giant](https://neurobro.ai/blog/market-update-2026-01-28)
- [The Defiant: Tokenized Equity Market Heats Up](https://thedefiant.io/news/defi/tokenized-equity-market-on-hyperliquid-heats-up)
