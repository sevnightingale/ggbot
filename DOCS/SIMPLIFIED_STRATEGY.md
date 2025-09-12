# Simplified 4-Pillar ggShot Strategy

### Pillar 0: Market Regime Analysis
Objective: Filter out choppy/ranging markets where breakout signals frequently fail

Indicators:
- Aroon (14-period): Trend vs ranging detection
  - Analysis: When both Aroon Up and Aroon Down are in middle range (30-70), market is consolidating. When one line is high (> 70) while the other is low (< 30), market is trending strongly
  - Critical Flag: Both Aroon lines between 30-70 indicates HIGH RISK for ggShot signals
- ADX (14-period): Trend strength confirmation
  - Analysis: ADX > 25 indicates strong trending conditions, ADX < 20 suggests weak/ranging market
  - Context: Low ADX combined with middle-range Aroon confirms dangerous ranging conditions

Critical Logic: ggShot signals are designed for breakout/momentum scenarios:
- Highest Risk: Aroon ranging (both 30-70) AND ADX < 20 (weak trend)
- High Risk: Either Aroon ranging OR ADX < 20
- Low Risk: Strong Aroon trend (one >70, other <30) AND ADX > 25

### Pillar 1: Signal Confirmation  
Objective: Seek confluence of evidence supporting the signal's direction

Indicators:
- RSI Multi-Timeframe Analysis:
  - Signal timeframe RSI: Momentum confirmation for entry timing
  - Analysis: For LONG signals, RSI 40-60 is ideal (not oversold, room to run). For SHORT signals, RSI 40-60 is also ideal
  - Avoid: RSI extremes (>80 or <20) suggest overextension risk
- Bollinger Band Position:
  - Price position relative to bands confirms signal direction
  - Analysis: For LONG signals, price approaching or touching lower band then bouncing supports upward move. For SHORT signals, price at upper band supports downward move
  - Context: Signals in middle of bands have less directional conviction

### Pillar 2: Broader Context
Objective: Ensure trade is well-positioned and has room to run

Indicators:
- Multi-Timeframe RSI Context:
  - Compare signal timeframe RSI with higher timeframe (4h) RSI
  - Analysis: Higher timeframe overbought (RSI > 70) for LONG signals is a significant contradiction. Higher timeframe oversold (RSI < 30) for SHORT signals is a contradiction
  - Ideal: Both timeframes showing non-extreme RSI (30-70 range)
- ADX Trend Strength:
  - Confirms we're in a trending environment suitable for breakouts
  - Analysis: ADX > 25 provides confidence that trends can sustain. ADX > 30 is very strong trending environment

### Pillar 3: Tactical Caution
Objective: Identify immediate risks that could stop out an otherwise good setup

Indicators:
- Bollinger Band Overextension:
  - Statistical overextension detection
  - Analysis: Prices far outside bands (beyond +2 sigma) indicate potential overextension with higher mean reversion risk
  - Caution: Signals when price is already beyond bands carry higher reversal risk
- ATR Volatility Assessment:
  - Market volatility/choppiness measurement  
  - Analysis: Exceptionally high ATR (relative to recent periods) indicates chaotic conditions that may increase stop-loss risk
  - Context: Very low ATR might indicate upcoming volatility expansion

## Decision Framework:
- **HIGH CONFIDENCE (0.8-1.0)**: All pillars align - trending market (Aroon + ADX), RSI in good zone, no overextension, normal volatility
- **MEDIUM CONFIDENCE (0.6-0.8)**: 3 of 4 pillars align, minor contradictions
- **LOW CONFIDENCE (0.4-0.6)**: 2 of 4 pillars align, significant contradictions present
- **WAIT (0.0-0.4)**: Major contradictions or ranging market conditions detected