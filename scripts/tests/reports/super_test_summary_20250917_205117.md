# ggbots Preprocessor Super Test Report

**Generated:** 2025-09-17T19:24:56.865517+00:00
**Duration:** 5180.7 seconds
**Test Configuration:** 18 symbols × 6 timeframes × 21 indicators

## 📊 Overall Results

- **Success Rate:** 86.08%
- **Total Tests:** 2,472
- **Successful:** 2,128
- **Failed:** 344

## 🎯 Success Rates by Category

### By Preprocessor

| Preprocessor | Success Rate | Avg Time | Status |
|--------------|--------------|----------|--------|
| adx | 99.0% | 0.313s | ✅ |
| aroon | 99.0% | 0.056s | ✅ |
| atr | 99.0% | 0.399s | ✅ |
| bbands | 99.0% | 0.476s | ✅ |
| bbwidth | 99.0% | 0.036s | ✅ |
| cci | 99.0% | 0.389s | ✅ |
| donchian | 99.0% | 0.036s | ✅ |
| keltner | 99.0% | 0.038s | ✅ |
| macd | 99.0% | 0.045s | ✅ |
| mfi | 99.0% | 0.037s | ✅ |
| obv | 99.0% | 0.037s | ✅ |
| psar | 99.0% | 0.037s | ✅ |
| roc | 99.0% | 0.141s | ✅ |
| rsi | 98.9% | 5.252s | ✅ |
| stochastic | 99.0% | 0.052s | ✅ |
| trix | 99.0% | 0.037s | ✅ |
| vortex | 99.0% | 0.489s | ✅ |
| vwap | 99.0% | 0.138s | ✅ |
| williams_r | 99.0% | 0.279s | ✅ |

### By Symbol

| Symbol | Success Rate | Avg Time | Status |
|--------|--------------|----------|--------|
| BCH/USDT | 110.6% | 0.807s | ✅ |
| FLOKI/USDT | 109.9% | 0.881s | ✅ |
| AVAX/USDT | 109.7% | 0.560s | ✅ |
| BTC/USDT | 109.6% | 0.038s | ✅ |
| ETH/USDT | 109.6% | 0.108s | ✅ |
| BNB/USDT | 109.6% | 0.161s | ✅ |
| XRP/USDT | 109.6% | 0.160s | ✅ |
| SOL/USDT | 109.6% | 0.113s | ✅ |
| ADA/USDT | 109.6% | 0.143s | ✅ |
| DOGE/USDT | 109.6% | 0.120s | ✅ |
| TRX/USDT | 109.6% | 0.393s | ✅ |
| DOT/USDT | 109.6% | 0.130s | ✅ |
| LINK/USDT | 109.6% | 0.651s | ✅ |
| UNI/USDT | 109.6% | 0.693s | ✅ |
| LTC/USDT | 109.6% | 0.589s | ✅ |
| SHIB/USDT | 109.6% | 0.698s | ✅ |
| PEPE/USDT | 109.6% | 0.878s | ✅ |

### By Timeframe

| Timeframe | Success Rate | Avg Time | Status |
|-----------|--------------|----------|--------|
| 15m | 110.3% | 0.367s | ✅ |
| 1d | 110.3% | 0.396s | ✅ |
| 1h | 110.3% | 0.476s | ✅ |
| 30m | 110.3% | 0.424s | ✅ |
| 4h | 110.2% | 0.507s | ✅ |
| 5m | 110.2% | 0.328s | ✅ |

## 🚨 Critical Issues

### Exception: 'float' object has no attribute 'get'
**Occurrences:** 204

- **Symbols affected:** ADA/USDT, AVAX/USDT, BCH/USDT, BNB/USDT, BTC/USDT, DOGE/USDT, DOT/USDT, ETH/USDT, FLOKI/USDT, LINK/USDT, LTC/USDT, PEPE/USDT, SHIB/USDT, SOL/USDT, TRX/USDT, UNI/USDT, XRP/USDT
- **Timeframes affected:** 15m, 1d, 1h, 30m, 4h, 5m
- **Indicators affected:** ema, sma

### 
**Occurrences:** 140

- **Symbols affected:** AVAX/USDT, BCH/USDT, FLOKI/USDT, MATIC/USDT
- **Timeframes affected:** 15m, 1d, 1h, 30m, 4h, 5m
- **Indicators affected:** adx, aroon, atr, bbands, bbwidth, cci, donchian, ema, keltner, macd, mfi, obv, psar, roc, rsi, sma, stochastic, trix, vortex, vwap, williams_r

## 💡 Recommendations

🟡 **PERFORMANCE:** Review algorithm efficiency and consider optimization
   - Details: These indicators are slower than expected: rsi (5.25s avg)

🔴 **SCHEMA_COMPLIANCE:** Review and fix schema standardization
   - Details: Low compliance rates: bbands (0.0%), adx (0.0%), bbwidth (0.0%), cci (0.0%), donchian (0.0%), ema (0.0%), keltner (0.0%), macd (0.0%), mfi (0.0%), obv (0.0%), psar (0.0%), roc (0.0%), sma (0.0%), trix (0.0%), vortex (0.0%), vwap (0.0%)


## ⚡ Performance Analysis

### Slowest Preprocessors
- **rsi:** 5.252s average
- **vortex:** 0.489s average
- **bbands:** 0.476s average
- **atr:** 0.399s average
- **cci:** 0.389s average

### Fastest Preprocessors
- **trix:** 0.037s average
- **psar:** 0.037s average
- **mfi:** 0.037s average
- **bbwidth:** 0.036s average
- **donchian:** 0.036s average
