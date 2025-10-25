# Market Intelligence Expansion Roadmap

**Purpose**: Strategic prioritization of 156 researched data sources for ggbots AI trading agents.

**Context**: We have comprehensive OHLCV + technical indicators. This document identifies the highest-leverage gaps to fill next.

---

## Executive Summary

**Current Coverage**: 7/156 data points (~4.5%)
- ✅ OHLCV multi-timeframe
- ✅ Technical indicators (RSI, MACD, Bollinger, 20+ via pandas-ta)
- ✅ Market structure (support/resistance, trend detection)
- ✅ Volume analysis
- ✅ Momentum oscillators

**Critical Gaps**: 5 categories blocking major trading edge
1. **Crypto On-Chain Intelligence** (8 data points) - Whale behavior, exchange flows, funding rates
2. **Sentiment & Social** (4 data points) - Twitter, Reddit, narrative tracking
3. **News & Catalysts** (4 data points) - Real-time crypto news, regulatory events
4. **Macro Context** (6 data points) - VIX, DXY, Fed policy, risk regimes
5. **Crypto Derivatives** (5 data points) - Perp funding, liquidations, OI

---

## Priority Framework

### Tier 0: What We Have ✅ (7 data points)

| Category | Data Points | Status | Source |
|----------|-------------|--------|--------|
| Price/Volume/Technicals | OHLCV multi-timeframe | ✅ Implemented | WebSocket + Binance REST |
| Price/Volume/Technicals | Market Structure (HH/HL/LH/LL) | ✅ Implemented | Derived from OHLCV |
| Price/Volume/Technicals | Momentum (RSI/MACD/ROC) | ✅ Implemented | pandas-ta library |
| Price/Volume/Technicals | Volatility (ATR/Bollinger) | ✅ Implemented | pandas-ta library |
| Price/Volume/Technicals | Volume Profile / VWAP | ✅ Implemented | pandas-ta library |
| Price/Volume/Technicals | Breadth Divergences (RS vs Index) | ✅ Implemented | Multi-symbol analysis |
| Technical Indicators | 20+ additional indicators | ✅ Implemented | pandas-ta library |

**Strength**: Excellent technical foundation
**Weakness**: Zero context, narrative, or "why" behind moves

---

## Tier 1: Critical Missing Intelligence (27 data points)

### 🔴 **A. Crypto On-Chain Intelligence** (8 points) - HIGHEST LEVERAGE

**Why Critical**: Transparent blockchain data = unfair information advantage. See what whales do BEFORE price moves.

| # | Data Point | Trading Value | Implementation | Cost | Source |
|---|-----------|---------------|----------------|------|--------|
| 64 | Exchange Reserves & Net Flows | Accumulation vs distribution signal | Easy | Free-$100/mo | Glassnode/CryptoQuant APIs |
| 65 | Whale Wallet Activity | Smart money positioning | Medium | $100-500/mo | Nansen, Arkham |
| 66 | Active Addresses/Network Usage | Adoption trend, demand proxy | Easy | Free-$100/mo | On-chain explorers |
| 67 | Stablecoin Supply & Dominance | Dry powder for pumps, rotation signal | Easy | Free | DefiLlama, CoinGecko |
| 68 | Funding Rates, OI, Long/Short | Overleveraged positioning, squeeze risk | **Easy** | **FREE** | **Binance/Bybit APIs** |
| 69 | Token Unlocks & Vesting | Supply overhang event risk | Easy | Free | TokenUnlocks.app |
| 70 | TVL & Cross-Chain Flows | Capital rotation, narrative momentum | Easy | Free | DefiLlama API |
| 71 | Dev Activity/Governance | Ecosystem vitality | Medium | Free | GitHub API, Snapshot |

**Quick Win**: #68 Funding Rates - FREE, already have exchange connections, 30min implementation

**ROI Calculation**:
- Funding rate extremes predict squeezes (>+1% = overleveraged longs = liquidation cascade risk)
- Whale accumulation at lows often precedes 20-30% pumps
- Exchange outflows (self-custody) reduce selling pressure

**Example Decision Improvement**:
- **Before**: "BTC technicals bullish, enter long"
- **After**: "BTC technicals bullish BUT funding rate +2.1% (extreme), whale wallets distributing -$500M to exchanges → SKIP (overleveraged, distribution)"

---

### 🟠 **B. Market Sentiment & Social Intelligence** (4 points) - HIGH LEVERAGE

**Why Critical**: Crypto is narrative-driven. Retail sentiment predicts meme pumps, contrarian signals at extremes.

| # | Data Point | Trading Value | Implementation | Cost | Source |
|---|-----------|---------------|----------------|------|--------|
| 23 | VIX & Term Structure | Risk-on/risk-off macro regime | Easy | **FREE** | CBOE public data |
| 24 | AAII/Sentiment Surveys | Retail sentiment extremes | Easy | Free | AAII public data |
| 25 | News Headline Sentiment | Narrative tone tracking | Medium | $0-500/mo | CryptoPanic, Finnhub |
| 26 | Social Topic Sentiment & Frequency | Hype cycle detection, meme timing | Medium | $100-500/mo | Twitter API, Reddit API |

**Quick Win**: #23 VIX - FREE, public API, 15min implementation

**ROI Calculation**:
- VIX >30 = risk-off (crypto sells off with equities)
- Social sentiment extremes (95+ bullish) = contrarian short signal
- Narrative velocity spikes catch early meme pumps (10x in days)

**Example Decision Improvement**:
- **Before**: "SOL breaking resistance, enter long"
- **After**: "SOL breaking resistance BUT Twitter mentions spiked 400% (late hype), Reddit sentiment 98/100 euphoric → FADE (exhaustion signal)"

---

### 🟡 **C. News & Catalysts** (4 points) - HIGH LEVERAGE

**Why Critical**: Crypto reacts violently to catalysts. Regulatory news, hacks, ETF approvals move markets 20%+ in minutes.

| # | Data Point | Trading Value | Implementation | Cost | Source |
|---|-----------|---------------|----------------|------|--------|
| 19 | Real-time Headlines & Tags | Catalyst awareness, event trading | Easy | $0-200/mo | CryptoPanic API, Finnhub |
| 20 | Earnings Dates/Results | (N/A for crypto - skip) | - | - | - |
| 21 | M&A/Regulatory/FDA | Regulatory announcements, exchange listings | Medium | $0-200/mo | CryptoPanic, Benzinga |
| 22 | Management Changes/Product Launches | (Limited crypto relevance - skip) | - | - | - |

**Quick Win**: #19 Real-time Headlines - CryptoPanic has FREE tier, 30min implementation

**ROI Calculation**:
- SEC approval news = 15-30% pump in minutes
- Exchange hack news = 10-20% dump immediately
- Regulatory clarity = multi-day trend catalyst

**Example Decision Improvement**:
- **Before**: "BTC MACD bullish crossover, enter long"
- **After**: "BTC MACD bullish BUT breaking news: SEC lawsuit against major exchange → EXIT all positions (regulatory risk-off)"

---

### 🟢 **D. Macro Context & Risk Regimes** (6 points) - MEDIUM-HIGH LEVERAGE

**Why Critical**: Crypto correlates 0.7+ with SPY/QQQ. Fed policy, risk appetite drive crypto trends.

| # | Data Point | Trading Value | Implementation | Cost | Source |
|---|-----------|---------------|----------------|------|--------|
| 43 | Inflation (CPI/PCE) | Fed policy path, rate expectations | Easy | **FREE** | BLS, FRED API |
| 44 | Employment (NFP, Claims) | Economic health, Fed reaction function | Easy | **FREE** | BLS, FRED API |
| 45 | Growth (GDP, ISM/PMI) | Cycle phase, risk appetite | Easy | **FREE** | BEA, ISM, FRED API |
| 46 | Policy (FOMC, Dot Plot, Minutes) | Discount rate, liquidity regime | Easy | **FREE** | Fed website, FRED |
| 48 | Yield Curve (2s10s), Real Yields | Risk regime, equity correlation | Easy | **FREE** | FRED API |
| 61 | DXY & Major Crosses | Dollar strength = crypto pressure | Easy | **FREE** | Alpha Vantage, FRED |

**Quick Win**: ALL 6 are FREE via FRED API, 1-2 hours total implementation

**ROI Calculation**:
- VIX spike >35 = sell all crypto (risk-off cascade)
- DXY strengthening = crypto pressure (inverse correlation)
- Fed pivot (rate cuts) = crypto bull catalyst

**Example Decision Improvement**:
- **Before**: "ETH consolidating, enter breakout long"
- **After**: "ETH consolidating BUT VIX spiked to 32 (fear), DXY rallying (risk-off), FOMC hawkish tomorrow → WAIT (macro headwinds)"

---

### 🔵 **E. Crypto Derivatives & Microstructure** (5 points) - MEDIUM LEVERAGE

**Why Critical**: Perp markets show leverage positioning. Liquidation cascades drive 10%+ moves in hours.

| # | Data Point | Trading Value | Implementation | Cost | Source |
|---|-----------|---------------|----------------|------|--------|
| 137 | Order Book Heatmaps & Liquidity | Liquidation hunt zones | Medium | Free-$100/mo | Exchange websockets, Coinalyze |
| 138 | Liquidation Levels & Cascades | Squeeze zones, cascade risk | Easy | **FREE** | Binance/Bybit APIs, Coinglass |
| 139 | CEX/DEX Market Share & Depth | Venue quality, slippage risk | Easy | Free | CoinGecko, DefiLlama |
| 140 | MEV Metrics & Validator Health | L2/L1 rotation signal | Hard | Free-$100/mo | Flashbots, Rated Network |
| 141 | L2 Fees/Gas & Bridge Latencies | User experience, adoption friction | Medium | Free | L2Beat, Dune Analytics |

**Quick Win**: #138 Liquidation Levels - FREE via Coinglass API, 1 hour implementation

**ROI Calculation**:
- Liquidation clusters at $94K BTC = magnet price target
- High funding + liquidation wall = squeeze setup (20%+ move potential)
- Order book imbalances predict short-term direction (1-4 hour edge)

**Example Decision Improvement**:
- **Before**: "BTC at $95K resistance, short here"
- **After**: "BTC at $95K BUT $2B liquidations at $96K (shorts), funding negative (under-leveraged) → LONG for liquidation hunt to $96K+"

---

## Tier 2: High-Value Complements (15 data points)

### 🟣 **F. Narratives & Themes** (3 points)

| # | Data Point | Cost | Source |
|---|-----------|------|--------|
| 87 | Topic Frequency & Velocity | $0-200/mo | Twitter API, LLM analysis |
| 88 | Influencer Amplification | $0-200/mo | Twitter API, social graphs |
| 89 | Narrative vs Fundamentals Divergence | $0 (derived) | Internal analysis |

**Value**: Catch meme cycles early, fade late narratives

---

### 🟤 **G. Alternative Data (Crypto-Relevant)** (7 points)

| # | Data Point | Cost | Source |
|---|-----------|------|--------|
| 79 | Credit-Card/Transaction Data | $5K-50K/mo | **Too expensive - skip** |
| 80 | Web/App Traffic & Downloads | $100-500/mo | SimilarWeb, Sensor Tower (Coinbase app, etc.) |
| 81 | Social Engagement/Influencers | $100-500/mo | Overlap with sentiment |
| 85 | Job Postings & Hiring | Free-$100/mo | LinkedIn, Indeed (crypto company hiring = growth signal) |
| 86 | Patent Filings/Citations | Free | USPTO (limited crypto relevance) |
| 145 | App Review NLP & Star Drift | $0 (scraping) | App stores (Coinbase, MetaMask reviews) |
| 148 | Foot-Traffic Geofencing | N/A | Not applicable to crypto |

**Value**: Leading indicators for protocol adoption, exchange health

---

### ⚫ **H. Intermarket Relationships** (5 points)

| # | Data Point | Cost | Source |
|---|-----------|------|--------|
| 52 | Equities vs Bonds (SPY/TLT) | **FREE** | Alpha Vantage, Yahoo Finance |
| 53 | Dollar vs Commodities (DXY vs Oil) | **FREE** | FRED, Alpha Vantage |
| 54 | Gold vs Real Yields | **FREE** | FRED, Gold API |
| 55 | Semis vs Cyclicals/Industrials | **FREE** | SOX, XLI tracking |
| Crypto | BTC Correlation to SPY/QQQ | **FREE** | Derived from price data |

**Value**: Understand crypto's position in risk spectrum, predict rotation

---

## Implementation Tiers

### 🚀 **Phase 1: Free Quick Wins (Week 1-2)** - $0/month

**7 data points, ~6-8 hours work**

1. ✅ **Funding Rates** (Binance/Bybit API) - 30min
2. ✅ **Liquidation Levels** (Coinglass API) - 1hr
3. ✅ **VIX** (CBOE public data) - 15min
4. ✅ **Macro Indicators** (FRED API: CPI, NFP, DXY, Yields) - 2hrs
5. ✅ **Stablecoin Supply** (DefiLlama API) - 30min
6. ✅ **TVL & Cross-Chain Flows** (DefiLlama) - 1hr
7. ✅ **Real-time News Headlines** (CryptoPanic free tier) - 1hr

**Impact**: Decision agent now has:
- Leverage positioning context (funding rates)
- Macro regime awareness (VIX, DXY, Fed policy)
- Catalyst awareness (news)
- Capital flow visibility (TVL, stablecoins)

**Cost**: $0
**Time**: 6-8 hours
**Trading Edge**: +30-40% (avoids overleveraged setups, catches macro regime shifts, aware of catalysts)

---

### 📈 **Phase 2: Premium On-Chain ($100-500/mo)** - (Week 3-4)

**5 data points, ~10-12 hours work**

8. 🐋 **Whale Wallet Tracking** (Nansen Lite $100/mo OR free Arkham API) - 4hrs
9. 📊 **Exchange Reserves & Flows** (Glassnode free tier OR CryptoQuant $100/mo) - 3hrs
10. 👥 **Active Addresses & Network Health** (On-chain explorers, free) - 2hrs
11. 🔓 **Token Unlocks** (TokenUnlocks.app API, free) - 1hr
12. 🏗️ **Dev Activity** (GitHub API, free) - 2hrs

**Impact**: See smart money accumulation/distribution before moves

**Cost**: $100-500/mo (can start with free tiers)
**Time**: 10-12 hours
**Trading Edge**: +20-30% (front-run whale moves, avoid supply dumps)

---

### 🎯 **Phase 3: Sentiment & Social ($100-500/mo)** - (Week 5-6)

**3 data points, ~12-16 hours work**

13. 🐦 **Twitter/X Sentiment** (Twitter API $100/mo + NLP) - 8hrs
14. 📱 **Reddit Crypto Sentiment** (Reddit API free + NLP) - 4hrs
15. 📈 **Narrative Velocity Tracking** (Topic modeling on news/social) - 4hrs

**Impact**: Catch meme cycles early, fade euphoria extremes

**Cost**: $100-500/mo
**Time**: 12-16 hours
**Trading Edge**: +15-25% (early meme detection, contrarian timing)

---

### 🔬 **Phase 4: Advanced Intelligence ($200-1000/mo)** - (Week 7-10)

**7 data points, ~20-25 hours work**

16. 📊 **Order Book Liquidity Heatmaps** (Coinalyze $200/mo) - 6hrs
17. 🌐 **CEX/DEX Market Share Tracking** (Free aggregation) - 2hrs
18. 💼 **Institutional Flows** (BTC ETF flows via public data) - 3hrs
19. 🎮 **App/Exchange Traffic** (SimilarWeb API $300/mo) - 4hrs
20. 💼 **Crypto Company Hiring** (LinkedIn/Indeed scraping) - 3hrs
21. ⛽ **L2 Gas Fees & Bridge Flows** (L2Beat, Dune) - 3hrs
22. 🏛️ **Intermarket Correlations** (SPY/BTC tracking) - 2hrs

**Impact**: Full 360° market intelligence

**Cost**: $200-1000/mo
**Time**: 20-25 hours
**Trading Edge**: +10-20% (microstructure edge, ecosystem health monitoring)

---

## Total Impact Projection

| Phase | Data Points | Cost | Time | Edge Gain | Cumulative Edge |
|-------|-------------|------|------|-----------|-----------------|
| **Current** | 7 | $0 | - | Baseline | 100% |
| **Phase 1** | +7 (14 total) | $0/mo | 6-8hrs | +30-40% | 130-140% |
| **Phase 2** | +5 (19 total) | $100-500/mo | 10-12hrs | +20-30% | 156-182% |
| **Phase 3** | +3 (22 total) | $100-500/mo | 12-16hrs | +15-25% | 179-228% |
| **Phase 4** | +7 (29 total) | $200-1000/mo | 20-25hrs | +10-20% | 197-274% |

**Realistic 6-Month Target**: 29/156 data points (18.6%), 2-3x trading edge improvement

---

## Data Not Applicable to Crypto (Skip These)

**51 data points can be safely ignored** (equity/bond/commodity specific):

- Market Internals/Breadth (A/D line, ticks) - Equity-specific
- Traditional Options Flow - Crypto has perps, not standard options
- Earnings/Transcripts - No earnings in crypto
- Credit Spreads/MOVE Index - Not applicable
- Commodities Detail (refinery, crack spreads) - Indirect at best
- REITs/Real Estate - Not applicable
- Corporate Actions (splits, dividends) - Not applicable
- Analyst Ratings - Limited crypto coverage
- Most Alternative Data (satellite, foot traffic) - Not applicable

**Remaining Addressable**: ~105 data points
**Phases 1-4 Coverage**: 29/105 = 27.6% of relevant data

---

## Recommended Starting Point

### **Week 1 Sprint: The "Context Upgrade"**

**Goal**: Give AI decision engine macro + leverage context in 8 hours

**Implementation Order**:
1. **Funding Rates** - 30 min (Binance API)
2. **VIX** - 15 min (CBOE data)
3. **DXY** - 15 min (FRED API)
4. **CryptoPanic News** - 1 hr (free tier API)
5. **DefiLlama TVL** - 30 min (API)
6. **Stablecoin Dominance** - 30 min (CoinGecko API)
7. **Liquidation Levels** - 1 hr (Coinglass API)
8. **Macro Indicators** (CPI, NFP, Yields) - 2 hrs (FRED batch)

**Decision Engine Prompt Enhancement**:
```
Current Analysis:
- Technical: {indicators}
- Market Structure: {support/resistance}

NEW Context Layer:
- Leverage: Funding rate {funding_rate}%, OI {oi_trend}
- Macro Regime: VIX {vix}, DXY {dxy_trend}, Fed Policy {policy_stance}
- Catalysts: Recent news: {top_3_headlines}
- Capital Flows: Stablecoin supply {supply_trend}, TVL {tvl_trend}
- Microstructure: Liquidations clustered at {liq_levels}

REASONING: [How does context change the technical setup?]
```

---

## Next Steps

1. **Review & Approve** this roadmap
2. **Choose Starting Phase** (recommend Phase 1 for quick wins)
3. **Create Implementation Issues** for each data source
4. **Design Universal Data Layer Extensions** (catalog YAML files, adapters)
5. **Build & Test** incrementally
6. **Measure Impact** on decision quality (backtest comparisons)

---

**Last Updated**: 2025-01-25
**Status**: Draft for review
**Owner**: Market Intelligence Expansion Project
