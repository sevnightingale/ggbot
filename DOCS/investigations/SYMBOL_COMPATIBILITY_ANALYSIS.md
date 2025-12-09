# Symbol Compatibility Analysis: ggShot vs Symphony

**Date**: 2025-12-05

---

## 📊 The Numbers

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total ggShot signals** | 142 | 100% |
| **Symphony-compatible** | 100 | 70.4% |
| **Symphony-incompatible** | 42 | 29.6% |

### Overlap
- **100 symbols** work with BOTH ggShot and Symphony ✅
- **42 symbols** work with ggShot but NOT Symphony 🚫

---

## 🏗️ Architecture: Universal Symbol Standardizer

### Location
`core/symbols/registry.py` - Centralized symbol compatibility database

### Structure
Each symbol has multiple format mappings + compatibility flags:

```python
"knc": {
    "base": "KNC",
    "quote": "USDT",
    "ggshot": "KNCUSDT",           # ggShot format (no separator)
    "ccxt": "KNC/USDT",            # CCXT format (slash)
    "hummingbot": "KNC-USDT",      # Hummingbot format (dash)
    "platform": "KNC-USDT",        # Platform standard (dash)
    "symphony": None,              # ❌ No Symphony mapping
    "symphony_compatible": False,  # ❌ Not tradeable on Symphony
    "aster_compatible": False,     # ❌ Not tradeable on AsterDEX
    "websocket_cached": False      # No WebSocket price caching
}
```

vs. compatible symbol:

```python
"btc": {
    "base": "BTC",
    "quote": "USDT",
    "ggshot": "BTCUSDT",
    "ccxt": "BTC/USDT",
    "hummingbot": "BTC-USDT",
    "platform": "BTC-USDT",
    "symphony": "BTC",             # ✅ Symphony format
    "symphony_compatible": True,   # ✅ Can trade on Symphony
    "aster_compatible": True,      # ✅ Can trade on AsterDEX
    "websocket_cached": True       # WebSocket cached
}
```

---

## 🚫 42 Symphony-Incompatible Symbols

These ggShot signals will fail on Symphony trading mode:

1. ACH/USDT
2. ALPHA/USDT
3. AXS/USDT
4. BAKE/USDT
5. BAL/USDT
6. BAND/USDT
7. BEL/USDT
8. BIGTIME/USDT
9. BNT/USDT
10. CELR/USDT
11. CETUS/USDT
12. CHR/USDT
13. CHZ/USDT
14. COTI/USDT
15. CRV/USDT
16. CYBER/USDT
17. FLM/USDT
18. GTC/USDT
19. HIGH/USDT
20. HOOK/USDT
21. ICX/USDT
22. ID/USDT
23. IOST/USDT
24. KAVA/USDT
25. **KNC/USDT** ← Your bot tried to trade this
26. LEVER/USDT
27. LPT/USDT
28. LQTY/USDT
29. MATIC/USDT
30. MKR/USDT
31. NKN/USDT
32. OGN/USDT
33. ONE/USDT
34. ONT/USDT
35. RLC/USDT
36. RUNE/USDT
37. SFP/USDT
38. SKLUS/USDT
39. SUI/USDT
40. SUSHI/USDT
41. SXP/USDT
42. VANRY/USDT

---

## 🔄 How the System Works

### Signal Flow (Current Behavior)

```
1. ggShot Telegram Channel
   └─> Sends signal: "KNCUSDT LONG entry 0.2769-0.2904"

2. Signal Listener Service (signals/listener_service.py)
   └─> Parses: KNCUSDT → KNC/USDT (CCXT format)
   └─> Routes to ALL active signal_validation bots with ggshot enabled
   └─> NO symbol filtering (routes all 142 symbols)

3. Orchestrator (ggbot.py)
   └─> Receives signal with symbol: KNC/USDT
   └─> Overrides bot's selected_pair with signal symbol
   └─> Runs extraction for KNC/USDT
   └─> Runs decision for KNC/USDT
   └─> Decision: action="enter", confidence=0.58

4. Trading Execution (ggbot.py:_run_trading_v2)
   └─> Checks trading_mode: "symphony"
   └─> Routes to symphony_trading.execute_trade_intent()

5. Symphony Service (trading/live/symphony_service.py:145-150)
   └─> Calls: standardizer.is_symphony_compatible("KNC/USDT", "ccxt")
   └─> Lookup: registry['knc']['symphony_compatible'] → False
   └─> Returns: {"status": "rejected", "reason": "Symbol not compatible"}

6. Result
   └─> Trade rejected
   └─> No Symphony API call made
   └─> ~$0.50 wasted on LLM decision
```

### Code Reference

**Symphony Compatibility Check** (`trading/live/symphony_service.py:145-150`):
```python
if not self.standardizer.is_symphony_compatible(symbol, "ccxt"):
    return {
        "status": "rejected",
        "reason": f"Symbol {symbol} not compatible with Symphony",
        "batch_id": None
    }
```

**Standardizer Check** (`core/symbols/standardizer.py:91-96`):
```python
def is_symphony_compatible(self, symbol: str, format_type: str = "platform") -> bool:
    """Check if symbol is compatible with Symphony.io live trading"""
    symbol_data = self.get_all_formats(symbol, format_type)
    if not symbol_data:
        return False
    return symbol_data.get("symphony_compatible", False)
```

---

## 💡 Solution Options

### Option 1: Signal-Level Filtering (RECOMMENDED)

**Where**: Signal listener service (`signals/listener_service.py:469-534`)

**Change**: Filter signals by trading mode compatibility before routing

**Logic**:
```python
async def _get_signal_subscribers(self, signal_source: str, signal_symbol: str):
    # Get all signal_validation bots
    # For each bot:
    #   - Check bot's trading_mode
    #   - If trading_mode == 'symphony':
    #       - Check if signal_symbol is symphony_compatible
    #       - Skip if incompatible
    #   - If trading_mode == 'paper':
    #       - Accept all symbols
    return filtered_subscribers
```

**Pros**:
- ✅ No wasted LLM calls (~$0.50 per rejected signal)
- ✅ Cleaner logs (no rejection noise)
- ✅ Symphony bots only process tradeable signals
- ✅ Paper bots still get all 142 signals

**Cons**:
- ⚠️ Symphony bots blind to ~29% of signals (acceptable tradeoff)
- ⚠️ Requires code change (30 minutes)

**Implementation**:
1. Add `signal_symbol` parameter to `_get_signal_subscribers()`
2. Query bot `trading_mode` from database
3. Check symbol compatibility for live modes
4. Filter subscriber list before routing

---

### Option 2: Accept Gracefully (CURRENT BEHAVIOR)

**Where**: Keep as-is, accept rejections

**Logic**: Route all signals, let Symphony service reject incompatible ones

**Pros**:
- ✅ No code changes
- ✅ Bot sees all signals (AI is aware)
- ✅ Already implemented

**Cons**:
- ❌ Wastes ~29% of LLM calls ($0.50 each)
- ❌ Noisy logs (rejection spam)
- ❌ False sense of activity (bot "working" but not trading)

**Cost Analysis**:
- ggShot sends ~10 signals/day
- ~3 signals/day incompatible (29%)
- $0.50/decision × 3 rejections = **$1.50/day wasted**
- **$45/month** wasted on impossible trades

---

### Option 3: Multi-Mode Fallback

**Where**: Trading execution layer (`ggbot.py:_run_trading_v2`)

**Logic**: Try Symphony, fallback to paper if rejected due to symbol

**Implementation**:
```python
if trading_mode == 'symphony':
    result = await symphony_trading.execute_trade_intent(intent)

    if result['status'] == 'rejected' and 'not compatible' in result['reason']:
        # Fallback to paper for this trade
        logger.info(f"Symbol incompatible with Symphony, using paper mode for {symbol}")
        result = await paper_trading.execute_trade_intent(intent)
```

**Pros**:
- ✅ Best of both worlds
- ✅ Symphony trades execute when possible
- ✅ Incompatible symbols trade in paper mode
- ✅ No signals missed

**Cons**:
- ⚠️ Mixed-mode accounting (hard to track P&L)
- ⚠️ Confusing UX (is this a live or paper bot?)
- ⚠️ Still wastes LLM on incompatible symbols

---

### Option 4: Separate Bots by Mode

**Setup**: Run 2 signal_validation bots:
1. **Symphony Bot**: Only major coins (BTC, ETH, SOL, etc.)
2. **Paper Bot**: All 142 symbols for testing

**Logic**: Frontend lets user choose trading mode when creating bot

**Pros**:
- ✅ Clear separation of concerns
- ✅ Symphony for real money, paper for testing
- ✅ No code changes needed

**Cons**:
- ⚠️ User manages 2 bots
- ⚠️ More complex setup
- ⚠️ Still need filtering (Symphony bot still receives incompatible signals)

---

## 🎯 Recommended Approach

**Implement Option 1: Signal-Level Filtering**

### Why This is Best:
1. **Cost Savings**: Saves $45/month in wasted LLM calls
2. **Clean UX**: No rejection spam in logs
3. **Correct Behavior**: Symphony bots only see tradeable signals
4. **Flexibility**: Paper bots still get all signals

### Implementation Plan:
1. Modify `signals/listener_service.py`:
   - Add symbol parameter to `_get_signal_subscribers()`
   - Query bot `trading_mode` from configurations table
   - Check `standardizer.is_symphony_compatible()` for Symphony bots
   - Filter out incompatible symbols before routing

2. Estimated Time: 30 minutes

3. Testing:
   - Send BTC signal → should route to Symphony bot
   - Send KNC signal → should NOT route to Symphony bot
   - Send KNC signal → should route to paper bots

---

## 📚 Related Documentation

- **Symbol Registry**: `core/symbols/registry.py`
- **Standardizer**: `core/symbols/standardizer.py`
- **Signal Listener**: `signals/listener_service.py`
- **Symphony Service**: `trading/live/symphony_service.py`
- **Trading README**: `trading/README.md` (line 187-191)

---

**Decision**: Implement filtering? Switch to paper mode? Or something else?
