# Technical Indicator Preprocessor System

## Overview

The preprocessor system transforms raw technical indicator values into rich, contextual market state analysis for the Decision Engine. Rather than generating trading signals, preprocessors provide sophisticated **market state descriptions** that enable the Decision LLM to make holistic, context-aware trading decisions.

## Philosophy: Analysis, Not Signals

### ❌ What We Don't Do (Anti-Pattern)
```python
# BAD: Preprocessors making trading decisions
{
  "signals": [
    {"type": "buy_signal", "confidence": 0.7},
    {"type": "sell_signal", "confidence": 0.8}
  ]
}
```

### ✅ What We Do (Correct Pattern)
```python
# GOOD: Rich market state description
{
  "indicator": "RSI",
  "context": {"trend": "rising", "velocity": 0.73},
  "levels": {"current_zone": "overbought"},
  "patterns": {"divergence": {...}, "reversal": {...}},
  "summary": "RSI at 73.2, rising strongly"
}
```

**Why?** The Decision LLM is sophisticated enough to interpret multiple indicators holistically. Pre-generated signals create conflicting micro-decisions that confuse the LLM rather than helping it.

## Data Flow Architecture

```
Raw Indicators → Preprocessors → Market State Analysis → Decision LLM → Trading Signals
     (Math)         (Context)        (Stored)           (AI)         (Actions)
```

1. **Raw Indicators**: pandas-ta calculates RSI=73.2, MACD=0.45, etc.
2. **Preprocessors**: Add context, patterns, zone analysis, trend direction
3. **Storage**: `market_data.data_points.indicators` in Supabase
4. **Decision LLM**: Interprets all indicators together to make trading decisions

## Standardized Output Schema

All preprocessors follow this consistent structure for LLM clarity:

```python
{
  "indicator": "RSI",                    # Indicator name
  "current": {                           # Current state
    "value": 73.2,
    "timestamp": "2025-01-15T10:30:00Z"
  },
  "context": {                           # Trend, momentum, volatility
    "trend": {"direction": "rising", "strength": 0.68},
    "velocity": 0.73,
    "volatility": 2.1
  },
  "levels": {                            # Zones, thresholds, crossovers
    "current_zone": "overbought",
    "key_levels": [30, 50, 70],
    "recent_crossovers": [...]
  },
  "patterns": {                          # Detected formations
    "divergence": {...},
    "reversal": {...},
    "momentum": {...}
  },
  "extremes": {                          # Recent highs/lows
    "recent_high": {"value": 85.2, "periods_ago": 3}
  },
  "summary": "RSI at 73.2, rising strongly"  # Human-readable
}
```

## Production Safety Requirements

### Critical Error Handling

**1. NaN Protection**
```python
# Always clean input data first
clean = rsi_values.dropna()
if len(clean) < 5:
    return {"error": "Insufficient data"}
current = float(clean.iloc[-1])  # Never use raw tail
```

**2. Zero-Division Guards**
```python
# Protect all calculations
width = max(upper - lower, 1e-12)
denom = middle if abs(middle) > 1e-12 else 1e-12
```

**3. Scale-Independent Thresholds**
```python
# Normalize by data standard deviation
data_std = clean.std() + 1e-12
normalized_slope = slope / data_std
threshold = 0.5  # Standard deviations, not raw units
```

**4. UTC Timestamps**
```python
from datetime import datetime, timezone
"timestamp": datetime.now(timezone.utc).isoformat()
```

### Base Class Integration

All preprocessors inherit from `BasePreprocessor` which provides:

- **NaN-safe utilities**: `_calculate_velocity()`, `_analyze_trend()`
- **Pattern detection**: `_find_peaks()`, `_find_troughs()` with volatility scaling
- **Zone analysis**: `_analyze_zones()` with configurable thresholds
- **Statistical helpers**: `_calculate_position_rank()`, `_find_recent_extremes()`

**Usage Pattern:**
```python
class RSIPreprocessor(BasePreprocessor):
    def preprocess(self, rsi_values, prices=None, **kwargs):
        clean = rsi_values.dropna()
        trend_analysis = self._analyze_trend(clean)      # Base class method
        peaks = self._find_peaks(clean, prominence=0.5)  # Volatility-scaled
        # ... rest of analysis
```

## Indicator-Specific Implementations

### RSI Preprocessor
- **Zone Analysis**: Overbought (70+), oversold (30-), neutral
- **Pattern Detection**: Double tops/bottoms, divergences, momentum
- **Context**: MA5/MA10 trend, velocity, acceleration

### Bollinger Bands Preprocessor  
- **Position Analysis**: %B calculation, band position classification
- **Squeeze Detection**: Bandwidth compression, expansion potential
- **Band Touches**: Upper/lower band interaction patterns
- **Volatility Analysis**: Bandwidth percentile, expansion/contraction cycles

### ADX Preprocessor
- **Trend Strength**: Weak (<20), strong (25+), very strong (40+), extreme (60+)
- **Directional Analysis**: +DI/-DI crossovers, directional bias, spread analysis
- **Momentum Quality**: ADX slope interpretation, acceleration patterns

## Implementation Patterns

### Factory Pattern for Preprocessors
```python
# preprocessors/__init__.py
class PreprocessorFactory:
    def __init__(self):
        self._preprocessors = {
            'rsi': RSIPreprocessor(),
            'bbands': BollingerBandsPreprocessor(),
            'adx': ADXPreprocessor()
        }
    
    def get_preprocessor(self, name):
        return self._preprocessors.get(name.lower())
```

### Router Pattern for API
```python
# preprocessor.py
class TechnicalAnalysisPreprocessor:
    def preprocess_rsi(self, rsi_values, prices=None, **kwargs):
        preprocessor = get_preprocessor('rsi')
        return preprocessor.preprocess(rsi_values, prices, **kwargs)
```

### Graceful Degradation
```python
# Optional preprocessors with try/except imports
try:
    from .macd import MACDPreprocessor
except ImportError:
    MACDPreprocessor = None

# Registration with safety checks
if MACDPreprocessor:
    self._preprocessors['macd'] = MACDPreprocessor()
```

## Testing Strategy

### Unit Tests
- **NaN handling**: Feed series with NaN tails, ensure no crashes
- **Zero-division**: Test with zero/near-zero denominators
- **Edge cases**: Empty data, single values, extreme volatility

### Integration Tests
- **End-to-end flow**: Raw indicators → Preprocessors → Storage → Decision Engine
- **Schema validation**: Ensure consistent output structure
- **Performance**: Large datasets, many indicators

### Production Validation
- **Data quality monitoring**: Track NaN percentages, calculation failures
- **Output validation**: Ensure all required fields present
- **Performance metrics**: Processing time per indicator

## Migration from Legacy System

### Key Changes from JavaScript Version
1. **Removed signal generation** - No more `signals` arrays
2. **Standardized schema** - Consistent structure across indicators  
3. **Enhanced error handling** - NaN protection, zero-division guards
4. **Scale independence** - Normalized thresholds, volatility-aware prominence
5. **UTC timestamps** - Timezone-aware for global deployment

### Backward Compatibility
The storage format (`market_data.data_points.indicators`) remains unchanged:
- ✅ Top-level indicator names preserved
- ✅ JSON structure compatibility maintained  
- ✅ Decision Engine integration unaffected
- ✅ Database schema unchanged

## Adding New Preprocessors

### Integration Checklist

When adding a new technical indicator preprocessor to the system, follow these steps to ensure complete integration:

#### 1. Create Specialized Preprocessor Class
```python
# extraction/v2/preprocessors/new_indicator.py
class NewIndicatorPreprocessor(BasePreprocessor):
    def preprocess(self, indicator_data: pd.Series, prices: pd.Series = None, **kwargs):
        # Clean data first
        clean = indicator_data.dropna()
        if len(clean) < 5:
            return {"error": "Insufficient data"}
        
        # Follow analysis-only pattern (NO signals/confidence)
        return {
            "indicator": "New_Indicator",
            "current": {"value": ..., "timestamp": datetime.now(timezone.utc).isoformat()},
            "context": {...},
            "levels": {...},
            "patterns": {...},
            "evidence": {...},
            "summary": "..."
        }
```

#### 2. Register in Factory
```python
# extraction/v2/preprocessors/__init__.py
try:
    from .new_indicator import NewIndicatorPreprocessor
except ImportError:
    NewIndicatorPreprocessor = None

# In PreprocessorFactory.__init__()
if NewIndicatorPreprocessor:
    self._preprocessors['new_indicator'] = NewIndicatorPreprocessor()
```

#### 3. Add Calculation Method
```python
# extraction/v2/indicators.py
def calculate_new_indicator(self, df: pd.DataFrame, **params) -> Dict[str, Any]:
    """Calculate New Indicator using pandas-ta."""
    # Calculate using pandas-ta
    indicator_data = ta.new_indicator(df['high'], df['low'], df['close'], **params)
    
    if self.use_advanced_preprocessing:
        return self.preprocessor.preprocess_new_indicator(indicator_data, df['close'], **params)
    else:
        # Simple fallback
        return {"indicator": "New_Indicator", "current": {"value": float(indicator_data.iloc[-1])}}
```

#### 4. Update calculate_multiple Method
```python
# In TechnicalIndicators.calculate_multiple()
elif indicator.lower() == "new_indicator":
    params_filtered = {k: v for k, v in params.items() if k.startswith("new_indicator_")}
    results["new_indicator"] = self.calculate_new_indicator(df, **params_filtered)
```

#### 5. Add Router Method
```python
# extraction/v2/preprocessor.py
def preprocess_new_indicator(self, indicator_data: pd.Series, prices: pd.Series = None, **kwargs):
    """Route New Indicator preprocessing to specialized preprocessor."""
    preprocessor = get_preprocessor('new_indicator')
    if preprocessor:
        return preprocessor.preprocess(indicator_data, prices, **kwargs)
    else:
        # Simple fallback
        current_value = float(indicator_data.iloc[-1])
        return {
            "indicator": "New_Indicator",
            "current": {"value": round(current_value, 4)},
            "summary": f"New Indicator: {current_value:.4f}"
        }
```

#### 6. Add to Available Indicators List
```python
# In TechnicalIndicators.__init__()
self.available_indicators = {
    # ... existing indicators ...
    "new_indicator": {"param1": default_value, "param2": default_value},
}
```

### Critical Requirements

**✅ Must Have:**
- NaN handling with `.dropna()` 
- UTC timestamps: `datetime.now(timezone.utc).isoformat()`
- Zero-division guards: `denom = value if abs(value) > 1e-12 else 1e-12`
- Analysis-only output (NO signals/confidence)
- Standardized schema with `context`, `levels`, `patterns`, `evidence`
- Unit-less prominence factors for peak/trough detection: `prominence=0.5`

**❌ Must NOT Have:**
- `signals` arrays or trading recommendations
- `confidence` scores or action suggestions  
- Hard-coded thresholds (use normalized by std deviation)
- Non-UTC timestamps
- Raw pandas tail access without NaN protection

### Testing New Preprocessors

```python
# Quick validation test
def test_new_preprocessor():
    # Create test data
    test_data = pd.Series([1.0, 1.5, 2.0, 1.8, 2.2])
    
    preprocessor = NewIndicatorPreprocessor()
    result = preprocessor.preprocess(test_data)
    
    # Validate structure
    assert 'signals' not in result, "Should not have signals"
    assert 'confidence' not in result, "Should not have confidence"  
    assert 'evidence' in result, "Should have evidence"
    assert result['current']['timestamp'].endswith('+00:00'), "Should be UTC"
```

## Current Implementation Status

### Refined Preprocessors (20 Complete) ✅
**Following standardized schema with analysis-only pattern:**
- `rsi` - Relative Strength Index with zone analysis and divergence detection
- `bbands` - Bollinger Bands with squeeze detection and band positioning
- `adx` - Average Directional Index with trend strength classification
- `aroon` - Aroon oscillator with trend direction and strength analysis
- `atr` - Average True Range with volatility classification and breakout potential
- `bbwidth` - Bollinger Band Width with volatility cycle analysis
- `cci` - Commodity Channel Index with zone analysis and momentum patterns
- `donchian` - Donchian Channels with breakout analysis and trend confirmation
- `ema` - Exponential Moving Average with trend analysis and crossover detection
- `keltner` - Keltner Channels with volatility-adjusted trend analysis
- `macd` - MACD with histogram analysis and signal line crossovers
- `mfi` - Money Flow Index with volume-weighted momentum analysis
- `obv` - On-Balance Volume with accumulation/distribution patterns
- `psar` - Parabolic SAR with dynamic stop-loss and trend reversal analysis
- `roc` - Rate of Change with momentum persistence and zero-line analysis
- `sma` - Simple Moving Average with trend following and support/resistance analysis
- `stochastic` - Stochastic Oscillator with %K/%D crossover analysis and divergence detection
- `trix` - TRIX with triple exponential smoothing and zero-line momentum analysis
- `vortex` - Vortex Indicator with directional movement and VI+/VI- crossover analysis
- `vwap` - Volume Weighted Average Price with fair value assessment and volume profile analysis
- `williams_r` - Williams %R with zone analysis, momentum tracking, and failure swing detection

### Migration Progress
**21 of 21 preprocessors (100%) completed** - All refined preprocessors follow the new standards:
- ✅ Analysis-only pattern (no signals/confidence)
- ✅ UTC timestamps with timezone awareness
- ✅ NaN protection and data validation
- ✅ Zero-division guards with epsilon values
- ✅ Standardized schema structure
- ✅ Scale-independent thresholds
- ✅ BasePreprocessor inheritance

## Future Enhancements

### Additional Indicators
- **Volume Profile**: Price-volume distribution analysis
- **Market Profile**: Time-based price distribution
- **Ichimoku Cloud**: Comprehensive trend analysis system

### Advanced Features
- **Multi-timeframe analysis**: Correlation across timeframes
- **Market regime detection**: Bull/bear/sideways classification
- **Confluence scoring**: Multiple indicator agreement metrics
- **Real-time streaming**: WebSocket integration for live updates

## Best Practices

### Code Organization
```
extraction/v2/preprocessors/
├── __init__.py           # Factory and registration
├── base.py              # BasePreprocessor with utilities
├── rsi.py               # RSI-specific implementation
├── bbands.py            # Bollinger Bands implementation
├── adx.py               # ADX implementation
└── ...                  # Additional indicators
```

### Documentation Standards
- **Docstrings**: Every method with Args/Returns
- **Type hints**: All parameters and return types
- **Comments**: Complex calculations and edge cases
- **Examples**: Usage patterns for each indicator

### Performance Optimization
- **Vectorized operations**: Use pandas/numpy efficiently
- **Lazy evaluation**: Only calculate what's needed
- **Memory management**: Clean up large Series/DataFrames
- **Caching**: Reuse expensive calculations when possible

---

*This preprocessor system provides the foundation for sophisticated, AI-driven trading decisions by delivering rich market context rather than simplistic signals.*