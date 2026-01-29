# Rei Compact Format Implementation Progress

Tracking `to_compact()` implementation for all 21 technical indicator preprocessors.

**Goal**: Each preprocessor outputs a universal compact schema for Rei API payloads (~400 bytes vs ~2KB full output).

**Reference**: See `decision/README.md` → "Rei Decision Engine" section for schema documentation.

---

## Implementation Status

### Completed ✅

| Indicator | File | Status | Notes |
|-----------|------|--------|-------|
| RSI | `rsi.py` | ✅ Complete | Zone detection, pattern codes, crossovers |

### High Priority (Most Used) 🔴

| Indicator | File | Status | Notes |
|-----------|------|--------|-------|
| MACD | `macd.py` | ⬜ Pending | 3 values: macd, signal, histogram |
| Stochastic | `stochastic.py` | ⬜ Pending | 2 values: %K, %D |
| Bollinger Bands | `bbands.py` | ⬜ Pending | %B, bandwidth, squeeze detection |
| ADX | `adx.py` | ⬜ Pending | 3 values: adx, +DI, -DI |

### Medium Priority 🟡

| Indicator | File | Status | Notes |
|-----------|------|--------|-------|
| ATR | `atr.py` | ⬜ Pending | Volatility classification |
| EMA | `ema.py` | ⬜ Pending | Trend/price relationship |
| SMA | `sma.py` | ⬜ Pending | Trend/price relationship |
| CCI | `cci.py` | ⬜ Pending | Similar to RSI zones |
| MFI | `mfi.py` | ⬜ Pending | Similar to RSI zones |
| Williams %R | `williams_r.py` | ⬜ Pending | Similar to RSI zones |

### Lower Priority 🟢

| Indicator | File | Status | Notes |
|-----------|------|--------|-------|
| OBV | `obv.py` | ⬜ Pending | Volume trend |
| VWAP | `vwap.py` | ⬜ Pending | Price vs VWAP |
| PSAR | `psar.py` | ⬜ Pending | Trend direction, stops |
| ROC | `roc.py` | ⬜ Pending | Momentum rate |
| Aroon | `aroon.py` | ⬜ Pending | 2 values: up, down |
| Vortex | `vortex.py` | ⬜ Pending | 2 values: VI+, VI- |
| Trix | `trix.py` | ⬜ Pending | Triple smoothed momentum |
| BBWidth | `bbwidth.py` | ⬜ Pending | Squeeze detection |
| Donchian | `donchian.py` | ⬜ Pending | Channel breakouts |
| Keltner | `keltner.py` | ⬜ Pending | Channel position |

---

## Universal Compact Schema

Every `to_compact()` must return this structure:

```python
{
    "indicator": "indicator_name",  # lowercase
    "timeframe": "1h",              # from parameter
    "timestamp": "ISO8601...",      # from current.timestamp

    "value": float,                 # Primary value (required)
    "value_secondary": float|None,  # Secondary (optional)
    "value_tertiary": float|None,   # Tertiary (optional)

    "velocity": float,              # Rate of change (0 if unknown)
    "rank": float,                  # Position in range 0-1 (0 if unknown)

    "zone": str,                    # State classification
    "zone_periods": int,            # Periods in current zone
    "trend": str,                   # "rising"/"falling"/"sideways"/"unknown"

    "crossover_type": str|None,     # Recent crossover (if applicable)
    "crossover_periods_ago": int|None,

    "patterns": List[str],          # Pattern codes (empty list if none)

    "analysis": str                 # Summary text (from full output)
}
```

---

## Indicator-Specific Mapping

### Momentum Oscillators (RSI-like)
- **value**: indicator value
- **zone**: "overbought"/"oversold"/"neutral"
- **patterns**: divergence_*, momentum_*, double_top/bottom

### Multi-Component (MACD, Stochastic)
- **value**: primary line (MACD line, %K)
- **value_secondary**: signal line (%D)
- **value_tertiary**: histogram (MACD only)
- **zone**: "bullish"/"bearish" based on line relationship
- **crossover_type**: "bullish"/"bearish" crossover

### Band Indicators (BB, Keltner, Donchian)
- **value**: %B or position metric
- **value_secondary**: bandwidth
- **zone**: "above_upper"/"upper_half"/"lower_half"/"below_lower"
- **patterns**: squeeze_*, walk_upper/lower

### Trend Indicators (ADX, Aroon, Vortex)
- **value**: primary (ADX, Aroon oscillator, VI+)
- **value_secondary**: directional+ (Aroon Up, VI-)
- **value_tertiary**: directional- (Aroon Down)
- **zone**: "strong_trend"/"weak_trend"/"bullish"/"bearish"

### Volume Indicators (OBV, VWAP)
- **value**: indicator value
- **zone**: "accumulation"/"distribution"/"neutral" (OBV) or "above"/"below" (VWAP)

---

## Pattern Codes Reference

```python
# Divergence
"divergence_bullish"      # Price lower low, indicator higher low
"divergence_bearish"      # Price higher high, indicator lower high

# Momentum
"momentum_strong_up"      # Strong upward momentum
"momentum_strong_down"    # Strong downward momentum
"momentum_rising"         # Moderate upward
"momentum_falling"        # Moderate downward

# Crossovers
"crossover_bullish"       # Bullish signal
"crossover_bearish"       # Bearish signal

# Zone events
"entering_overbought"     # Just entered OB
"exiting_overbought"      # Just left OB
"entering_oversold"       # Just entered OS
"exiting_oversold"        # Just left OS

# Volatility
"squeeze_active"          # Low volatility compression
"squeeze_firing"          # Breakout from squeeze
"volatility_expanding"    # Bands widening
"volatility_contracting"  # Bands narrowing

# Formations
"double_top"              # Two peaks at similar level
"double_bottom"           # Two troughs at similar level
"failure_swing"           # Failed new high/low
```

---

## Test Validation

Run after each implementation:
```bash
python scripts/tests/test_compact_preprocessors.py
```

Test checks:
1. All implemented preprocessors have `to_compact()` method
2. Output matches universal schema
3. All values are JSON-serializable (no numpy types)
4. Size is under 600 bytes per indicator
5. Pattern codes are from approved list

---

## Implementation Template

```python
def to_compact(self, full_output: dict, timeframe: str) -> dict:
    """Convert full output to universal compact format."""
    import numpy as np

    if "error" in full_output:
        return {
            "indicator": "indicator_name",
            "timeframe": timeframe,
            "timestamp": None,
            "value": None, "value_secondary": None, "value_tertiary": None,
            "velocity": 0.0, "rank": 0.0,
            "zone": "error", "zone_periods": 0, "trend": "unknown",
            "crossover_type": None, "crossover_periods_ago": None,
            "patterns": [],
            "analysis": full_output.get("error", "Unknown error")
        }

    # Helper for numpy conversion
    def to_native(val):
        if val is None: return None
        if isinstance(val, (np.integer,)): return int(val)
        if isinstance(val, (np.floating,)): return float(val)
        return val

    current = full_output.get("current", {})
    # ... extract indicator-specific values ...

    return {
        "indicator": "indicator_name",
        "timeframe": timeframe,
        "timestamp": current.get("timestamp"),
        "value": ...,
        "value_secondary": ...,
        "value_tertiary": ...,
        "velocity": ...,
        "rank": ...,
        "zone": ...,
        "zone_periods": to_native(...),
        "trend": ...,
        "crossover_type": ...,
        "crossover_periods_ago": to_native(...),
        "patterns": self._extract_pattern_codes(full_output.get("patterns", {})),
        "analysis": full_output.get("summary", "")
    }
```

---

## Progress Log

| Date | Indicator | Author | Notes |
|------|-----------|--------|-------|
| 2026-01-29 | RSI | Claude | Initial implementation with full pattern support |

---

*Last updated: 2026-01-29*
