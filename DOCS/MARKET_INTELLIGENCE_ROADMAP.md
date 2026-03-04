# Market Intelligence Expansion Roadmap

**Purpose**: Strategic prioritization of 156 researched data sources for ggbots AI trading agents.

**Context**: We have comprehensive OHLCV + technical indicators. This document identifies the highest-leverage gaps to fill next.

---

## Executive Summary

**Current System Status**:
- ✅ **Database Infrastructure**: `data_sources` and `data_points` tables deployed and operational
- ✅ **UI Complete**: MarketDataSelector component with tabs, search, premium gates
- ✅ **Backend API**: `/api/v2/data-sources-with-points` serving from database
- ✅ **Domain Models**: DataSource, DataPoint, DataSourceWithPoints classes
- ✅ **Config Storage**: `config_data` JSONB in configurations table stores user selections
- ✅ **Universal Data Layer**: Gateway, adapters, catalog system ready for extension

**Current Data Coverage**: 22/156 data points (14%)

**Populated Data Sources**:
1. ✅ **Technical Analysis** (21 data points) - RSI, MACD, Bollinger, ADX, Stochastic, Williams %R, CCI, MFI, ROC, Aroon, Vortex, TRIX, Parabolic SAR, EMA, SMA, Keltner Channels, Donchian, ATR, BB Width, OBV, VWAP
2. ✅ **Signals in Group Chats** (1 data point) - ggShot premium signals
3. ⏳ **Fundamental Analysis** - Coming soon (tab exists, no data points)
4. ⏳ **Sentiment & Trends** - Coming soon (tab exists, no data points)
5. ⏳ **News & Regulations** - Coming soon (tab exists, no data points)
6. ⏳ **On-Chain Analytics** - Coming soon (tab exists, no data points)

**Core Platform Data** (separate from data_sources system):
- ✅ OHLCV multi-timeframe (WebSocket + Binance REST)
- ✅ Market structure analysis (7 timeframes: 5m, 15m, 30m, 1h, 4h, 1d, 1w)

**Critical Gaps**: 5 categories blocking major trading edge
1. **Crypto On-Chain Intelligence** (8 data points) - Whale behavior, exchange flows, funding rates
2. **Sentiment & Social** (4 data points) - Twitter, Reddit, narrative tracking
3. **News & Catalysts** (4 data points) - Real-time crypto news, regulatory events
4. **Macro Context** (6 data points) - VIX, DXY, Fed policy, risk regimes
5. **Crypto Derivatives** (5 data points) - Perp funding, liquidations, OI

---

## Data Acquisition Strategy

We will use **three methods** to acquire market intelligence data, chosen based on cost, ease of implementation, and data availability:

### **Method 1: Direct API Integration** (Preferred for free/easy sources)

**When to use**: Free or low-cost APIs with good documentation and no authentication barriers.

**How it works**:
1. Create adapter in `market_intelligence/adapters/` (e.g., `BinanceFundingAdapter`)
2. Create catalog YAML in `market_intelligence/catalog/data_types/`
3. Insert into `data_sources` and `data_points` database tables
4. Automatically appears in frontend UI

**Examples**:
- Binance Funding Rates API (free, no auth)
- FRED Macro Data API (free, simple API key)
- DefiLlama TVL API (free, no auth)
- CoinGecko Price API (free tier generous)

**Effort**: Low (30min - 2hrs per source)

---

### **Method 2: Grok Web Search** (For data on the web without APIs)

**When to use**: Data is publicly available on websites but no clean API exists, or APIs are rate-limited/expensive.

**How it works**:
1. Use Grok API with web search tool enabled
2. Prompt Grok to search web and extract structured data
3. Parse Grok's response into standardized format
4. Cache results in Redis (longer TTL since web scraping is slower)

**Examples**:
- VIX index current value (if CBOE API blocked)
- Crypto fear/greed index
- Whale alert notifications from websites
- News headlines from aggregator sites
- Social sentiment scores from public dashboards

**Effort**: Medium (1-3hrs per source, need to test Grok tool use)

**Advantages**:
- No API keys needed
- Works for any data visible on public web
- Grok handles parsing and extraction
- One adapter works for many sources

**Limitations**:
- Slower than direct APIs (2-5s per query)
- Higher cost (Grok API usage)
- Less reliable (web structure changes)

---

### **Method 3: Browser-Use Automation** (For paywalled/gated sources)

**When to use**: High-value data behind login walls, paywalls, or CAPTCHAs.

**How it works**:
1. Store credentials in Supabase Vault (encrypted)
2. Launch headless browser session with Browser-Use
3. AI navigates to login page, fills credentials
4. AI navigates to data page, extracts via vision + scraping
5. Returns structured data

**Examples**:
- Nansen whale tracking (requires $100/mo subscription)
- Glassnode premium metrics
- TradingView premium indicators
- Discord/Telegram group signals (private channels)

**Effort**: High (4-8hrs per source, credentials management)

**Advantages**:
- Access to premium data without enterprise APIs
- One subscription shared across all users
- AI handles complex navigation

**Limitations**:
- Slowest method (10-30s per query)
- Requires credential storage
- Risk of account bans if detected
- Most maintenance overhead

---

### **Decision Matrix: Which Method to Use**

| Source | Free? | Has API? | Behind Login? | **Method** | Priority |
|--------|-------|----------|---------------|------------|----------|
| Binance Funding Rates | ✅ Yes | ✅ Yes | ❌ No | **Direct API** | Phase 1 |
| FRED Macro Data | ✅ Yes | ✅ Yes | ❌ No | **Direct API** | Phase 1 |
| VIX Index | ✅ Yes | ❌ No | ❌ No | **Grok Search** | Phase 1 |
| CryptoPanic News | ✅ Yes (tier) | ✅ Yes | ❌ No | **Direct API** | Phase 1 |
| Coinglass Liquidations | ✅ Yes | ⚠️ Unofficial | ❌ No | **Grok Search** | Phase 1 |
| Nansen Whale Tracking | ❌ No ($100/mo) | ❌ No | ✅ Yes | **Browser-Use** | Phase 2 |
| Twitter Sentiment | ⚠️ Limited | ✅ Yes | ⚠️ Partial | **Direct API** → Grok | Phase 3 |
| Reddit Sentiment | ✅ Yes | ✅ Yes | ❌ No | **Direct API** | Phase 3 |

**Phase 1 Strategy**: Use 60% Direct API, 40% Grok Search. Avoid Browser-Use until proven valuable.

---

## Priority Framework

### Tier 0: What We Have ✅ (22 data points)

**Infrastructure (Complete)**:
- ✅ `data_sources` table with 6 categories (2 populated, 4 empty)
- ✅ `data_points` table with 22 indicators
- ✅ Frontend UI: MarketDataSelector + SignalsConfiguration components
- ✅ Backend API: `/api/v2/data-sources-with-points`
- ✅ User config storage: `config_data` JSONB
- ✅ Universal Data Layer: Gateway + adapter system

**Data Source 1: Technical Analysis** (21 data points) - ✅ **Fully Populated**

| Category | Indicators | Status |
|----------|-----------|--------|
| Momentum (10) | RSI, MACD, Stochastic, Williams %R, CCI, MFI, ROC, Aroon, Vortex, TRIX | ✅ Live |
| Trend (4) | ADX, Parabolic SAR, EMA, SMA | ✅ Live |
| Volatility (5) | Bollinger Bands, Keltner Channels, Donchian, ATR, BB Width | ✅ Live |
| Volume (2) | OBV, VWAP | ✅ Live |

**Data Source 2: Signals in Group Chats** (1 data point) - ✅ **Fully Populated**

| Signal | Status | Premium |
|--------|--------|---------|
| ggShot | ✅ Live | 💎 Yes |

**Data Source 3-6: Empty Shells** (0 data points) - ⏳ **Coming Soon**

| Source | Status | UI Tab |
|--------|--------|---------|
| Fundamental Analysis | ⏳ Planned | ✅ Exists |
| Sentiment & Trends on Social Media | ⏳ Planned | ✅ Exists |
| News & Regulatory Actions | ⏳ Planned | ✅ Exists |
| On-Chain Analytics | ⏳ Planned | ✅ Exists |

**Core Platform Data** (not in data_sources system):
- ✅ OHLCV multi-timeframe via Universal Data Layer
- ✅ WebSocket cache (100 symbols × 7 timeframes)
- ✅ Binance REST fallback

**Strength**: Excellent technical foundation + infrastructure ready for expansion
**Weakness**: Zero context, narrative, or "why" behind moves (no sentiment, on-chain, macro, news)

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

**9 data points across 3 new data sources, ~11-15 hours work**

**Implementation Steps Per Data Point**:
1. Create Universal Data Layer adapter (or use GrokSearchAdapter)
2. Create catalog YAML for data type
3. Insert row into `data_sources` table (if new category)
4. Insert row(s) into `data_points` table
5. Test adapter fetch
6. **UI automatically updates** (no frontend work needed)

---

**New Data Source: Crypto Derivatives** (2 data points)

| # | Data Point | Method | Effort | Database Work |
|---|-----------|--------|--------|---------------|
| 1 | **BTC Funding Rate** | Direct API | 1hr | Insert: 1 source + 1 point |
| 2 | **ETH Funding Rate** | Direct API | 20min | Insert: 1 point (reuse source) |

**Adapter**: `BinanceFundingAdapter` → `market_intelligence/adapters/crypto_derivatives/binance_funding.py`
**Catalog**: `market_intelligence/catalog/data_types/derivatives/funding_rate.yaml`
**API**: `https://fapi.binance.com/fapi/v1/premiumIndex`

---

**New Data Source: Macro Context** (6 data points)

| # | Data Point | Method | Effort | Database Work |
|---|-----------|--------|--------|---------------|
| 3 | **VIX Index** | Grok Search | 1hr | Insert: 1 source + 1 point |
| 4 | **DXY (Dollar Index)** | Direct API (FRED) | 30min | Insert: 1 point |
| 5 | **CPI (Inflation)** | Direct API (FRED) | 30min | Insert: 1 point |
| 6 | **NFP (Jobs Report)** | Direct API (FRED) | 30min | Insert: 1 point |
| 8 | **USDT.D (USDT Dominance)** | Direct API (CoinGecko) | 1-2hr | Insert: 1 point |
| 9 | **MOVE Index (Bond Volatility)** | Grok Search | 1hr | Insert: 1 point |

**Adapter Option A**: `FredApiAdapter` for #4-6 (requires free API key)
**Adapter Option B**: `GrokSearchAdapter` for #3, #9 (no API keys)
**Adapter C**: `CoinGeckoAdapter` for #8 (free, no auth, `global` endpoint)
**Catalog**: `market_intelligence/catalog/data_types/macro/` (6 YAML files)

**#8 USDT.D Details** *(Community-requested by Denis @ Buidler Labs)*:
- USDT dominance = USDT market cap / total crypto market cap
- Rising USDT.D = money rotating into stables (risk-off, bearish crypto)
- Falling USDT.D = money rotating into crypto (risk-on, bullish)
- API: `https://api.coingecko.com/api/v3/global` → `market_cap_percentage.usdt`
- Alternative: Binance `USDT.D` chart data or TradingView

**#9 MOVE Index Details** *(Community-requested by Denis @ Buidler Labs)*:
- ICE BofA MOVE Index = US Treasury bond market implied volatility
- Analogous to VIX but for bonds. High MOVE (>120) = bond stress = risk-off cascade
- Crypto correlation: MOVE spike → institutional deleveraging → crypto sells off
- No free API — use Grok web search (same pattern as VIX)
- Previously listed as "skip" — reclassified as relevant per community feedback

---

**Expand Existing: On-Chain Analytics** (1 data point)

| # | Data Point | Method | Effort | Database Work |
|---|-----------|--------|--------|---------------|
| 7 | **BTC TVL on DeFi** | Direct API | 1hr | Insert: 1 point (source exists) |

**Adapter**: `DefiLlamaAdapter` → `market_intelligence/adapters/onchain/defillama.py`
**Catalog**: `market_intelligence/catalog/data_types/onchain/tvl.yaml`
**API**: `https://api.llama.fi/v2/chains`

---

**Total Phase 1 Work**:
- 4 new adapters (BinanceFunding, Grok/FRED, DefiLlama, CoinGecko)
- 9 catalog YAML files
- 3 INSERT into data_sources
- 9 INSERT into data_points
- **0 frontend changes** (UI auto-populates from database)

**Impact**: Decision agent now has:
- Leverage positioning context (funding rates)
- Macro regime awareness (VIX, DXY, inflation, jobs, MOVE)
- Capital flow visibility (DeFi TVL)
- Crypto rotation signal (USDT.D)

**Cost**: $0
**Time**: 11-15 hours
**Trading Edge**: +30-40% (avoids overleveraged setups, catches macro regime shifts, detects crypto rotation)

---

### 🔧 **Phase 1.5: Structural Analysis & Decision Enrichment** - $0/month

**Community-requested** (Denis @ Buidler Labs, Telegram, 2026-03-01)

**2 features, ~6-9 hours work**

---

**New Preprocessor: Order Blocks (#22)**

| Feature | Details |
|---------|---------|
| **What** | ICT (Inner Circle Trader) concept — last opposite candle before a strong impulse move = institutional accumulation zone. Price tends to react (bounce/rejection) when it revisits these zones. |
| **Trading Value** | Structured support/resistance derived from real price action, not arbitrary lines. Identifies where large players likely accumulated. |
| **Implementation** | New preprocessor extending `BasePreprocessor`. Requires: (1) swing high/low detection via pivot points, (2) impulse move validation (magnitude threshold), (3) zone marking (OHLC of last opposite candle), (4) zone tracking across multiple candle updates. |
| **Statefulness** | Unlike existing preprocessors (stateless, recompute from OHLCV each cycle), order blocks must persist — a zone identified 50 candles ago remains valid until price revisits it. Options: (a) recompute from full candle history each cycle (simplest, ~100 candles sufficient), (b) Redis persistence for zones (faster, more complex). Recommend (a) for MVP. |
| **Output** | List of active order block zones: `{type: 'bullish'|'bearish', zone_high, zone_low, age_candles, impulse_magnitude, tested: bool}` |
| **Effort** | 4-6 hours |
| **File** | `extraction/v2/preprocessors/order_blocks.py` |

**Algorithm Sketch**:
```
1. Find swing highs/lows using N-bar pivot detection (e.g., 5-bar)
2. Identify impulse moves: swing-to-swing move > threshold (e.g., 2× ATR)
3. Mark order block: last opposite candle before impulse
   - Bullish OB: last bearish candle before bullish impulse (support zone)
   - Bearish OB: last bullish candle before bearish impulse (resistance zone)
4. Track zones: zone remains active until price closes through it
5. Report: nearest OB above/below current price, zone age, test count
```

---

**Enhanced Position Statefulness**

| Feature | Details |
|---------|---------|
| **What** | Enrich the decision engine's position management prompts with structured trade state data beyond the current position recap. |
| **Current State** | DecisionEngineV2 switches to `position_management` mode with position recap (entry price, side, unrealized P&L, SL/TP levels). |
| **Additions** | `bars_in_trade` (candles since entry), `max_drawdown_pct` (worst unrealized P&L during trade), `max_profit_pct` (best unrealized P&L), `time_in_position` (human-readable duration), `entry_context` (market conditions at entry from original decision reasoning). |
| **Trading Value** | LLM can make better exit decisions with temporal context (holding 2 bars vs 50 bars matters), drawdown awareness (recovering from -5% vs always green), and entry recall (why did we enter?). |
| **Implementation** | Extend position management prompt template in `decision/prompts/`. Query `paper_trades` for trade metadata, compute bars-in-trade from `opened_at` vs current time and bot frequency. |
| **Effort** | 2-3 hours |
| **Files** | `decision/engine_v2.py`, `decision/prompts/position_management.py` |

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
| **Current** | 22 | $0 | - | Baseline | 100% |
| **Phase 1** | +9 (31 total) | $0/mo | 11-15hrs | +30-40% | 130-140% |
| **Phase 1.5** | +1 preprocessor + decision enrichment | $0/mo | 6-9hrs | +10-15% | 143-161% |
| **Phase 2** | +5 (36 total) | $100-500/mo | 10-12hrs | +20-30% | 172-209% |
| **Phase 3** | +3 (39 total) | $100-500/mo | 12-16hrs | +15-25% | 198-261% |
| **Phase 4** | +7 (46 total) | $200-1000/mo | 20-25hrs | +10-20% | 218-313% |

**Realistic 6-Month Target**: 46/156 data points (30%), 2-3x trading edge improvement

**Key Insight**: We already have infrastructure + 22 data points. Phase 1 adds context (macro, funding, on-chain, USDT.D, MOVE), not more technicals. Phase 1.5 adds structural analysis (order blocks) and better exit decisions (position statefulness).

---

## Data Not Applicable to Crypto (Skip These)

**51 data points can be safely ignored** (equity/bond/commodity specific):

- Market Internals/Breadth (A/D line, ticks) - Equity-specific
- Traditional Options Flow - Crypto has perps, not standard options
- Earnings/Transcripts - No earnings in crypto
- Credit Spreads - Not applicable (MOVE Index reclassified → Phase 1 macro context)
- Commodities Detail (refinery, crack spreads) - Indirect at best
- REITs/Real Estate - Not applicable
- Corporate Actions (splits, dividends) - Not applicable
- Analyst Ratings - Limited crypto coverage
- Most Alternative Data (satellite, foot traffic) - Not applicable

**Remaining Addressable**: ~105 data points
**Phases 1-4 Coverage**: 31/105 = 29.5% of relevant data

---

## Recommended Starting Point

### **Week 1 Sprint: The "Context Upgrade"**

**Goal**: Add 9 contextual data points to AI decision engine in 11-15 hours

**Day 1-2: Setup (2-3 hours)**
- Test Grok API with web search tool
- Set up FRED API key (free, 30 seconds)
- Create GrokSearchAdapter base class
- Create FredApiAdapter base class
- Create CoinGeckoAdapter base class

**Day 3-5: Implementation (9-12 hours)**

| Order | Data Point | Adapter | Catalog | Database | Test |
|-------|-----------|---------|---------|----------|------|
| 1 | BTC Funding Rate | BinanceFunding | funding_rate.yaml | INSERT 1+1 | 15min |
| 2 | ETH Funding Rate | (reuse) | (reuse) | INSERT 1 | 10min |
| 3 | VIX Index | GrokSearch | vix.yaml | INSERT 1+1 | 30min |
| 4 | DXY Dollar Index | FredApi | dxy.yaml | INSERT 1 | 20min |
| 5 | CPI Inflation | FredApi | cpi.yaml | INSERT 1 | 20min |
| 6 | NFP Jobs Report | FredApi | nfp.yaml | INSERT 1 | 20min |
| 7 | BTC DeFi TVL | DefiLlama | tvl.yaml | INSERT 1+1 | 30min |
| 8 | USDT Dominance | CoinGecko | usdt_dominance.yaml | INSERT 1 | 1hr |
| 9 | MOVE Index | GrokSearch | move.yaml | INSERT 1 | 30min |

**Database Seeding Script**:
```sql
-- Create new data sources
INSERT INTO data_sources (name, display_name, description, requires_premium) VALUES
('crypto_derivatives', 'Crypto Derivatives', 'Perpetual futures funding rates and leverage metrics', false),
('macro_context', 'Macro Context', 'Macroeconomic indicators (VIX, DXY, CPI, NFP, MOVE, USDT.D)', false);

-- Create data points
INSERT INTO data_points (source_id, name, display_name, description, config_values) VALUES
((SELECT source_id FROM data_sources WHERE name='crypto_derivatives'),
 'btc_funding_rate', 'BTC Funding Rate', 'Binance perpetual funding rate for BTC/USDT',
 ARRAY['funding_rate_btc']),

((SELECT source_id FROM data_sources WHERE name='crypto_derivatives'),
 'eth_funding_rate', 'ETH Funding Rate', 'Binance perpetual funding rate for ETH/USDT',
 ARRAY['funding_rate_eth']);

-- (repeat for macro indicators and TVL)
```

**Decision Engine Prompt Enhancement**:
```python
# In decision/prompts/opportunity_analysis.py

CONTEXT_SECTION = """
## Market Context

### Derivatives Positioning
- BTC Funding Rate: {btc_funding_rate}% ({funding_interpretation})
- ETH Funding Rate: {eth_funding_rate}%

### Macro Environment
- VIX (Fear Index): {vix} ({risk_regime})
- MOVE (Bond Volatility): {move} ({bond_stress_level})
- DXY (Dollar Strength): {dxy} ({crypto_impact})
- CPI (Inflation): {cpi}%
- NFP (Jobs): {nfp}

### Crypto Rotation
- USDT Dominance: {usdt_d}% ({rotation_signal})

### On-Chain Flows
- BTC DeFi TVL: ${tvl_btc}B ({flow_trend})

REASONING: How does this context affect the technical setup?
```

**Result**: UI automatically shows 3 new data source tabs with 9 toggleable data points. Users configure per bot.

---

## Next Steps

1. **Review & Approve** this roadmap
2. **Choose Starting Phase** (recommend Phase 1 for quick wins)
3. **Create Implementation Issues** for each data source
4. **Design Universal Data Layer Extensions** (catalog YAML files, adapters)
5. **Build & Test** incrementally
6. **Measure Impact** on decision quality (backtest comparisons)

---

**Last Updated**: 2025-01-25 (Revised with actual system state)
**Status**: Ready for Phase 1 implementation
**Owner**: Market Intelligence Expansion Project

**Key Changes in This Revision**:
- ✅ Updated to reflect 22 existing data points (not 7)
- ✅ Added 3-method acquisition strategy (Direct API, Grok Search, Browser-Use)
- ✅ Clarified existing infrastructure (database tables, UI, API all operational)
- ✅ Revised Phase 1 to be database-driven (no frontend work needed)
- ✅ Updated effort estimates to include database seeding steps
- ✅ Added decision matrix for choosing acquisition method
