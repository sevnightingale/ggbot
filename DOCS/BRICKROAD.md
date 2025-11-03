# Data Points for Brickroad Partnership

## 1. Whale Wallet Clustering & Smart Money Tracking

**Why we want it:**
- See institutional accumulation/distribution before price moves
- Whale buying at market lows often precedes 20-30% pumps within days
- Identify smart money positioning during consolidation periods

**How AI agents would use it:**
- Agent detects technical breakout with low volume ’ queries whale data
- If top 50 wallets accumulated in past 48 hours ’ high confidence LONG
- If whales distributing to exchanges ’ skip trade or take opposite position
- Use as confirmation filter for technical setups

**Where it exists today:**
- Nansen ($100-500/month) - entity-labeled wallet tracking
- Arkham Intelligence (free tier + paid) - wallet clustering and labels
- Chainalysis ($500-2000/month) - institutional-grade wallet intelligence

---

## 2. Exchange Reserve Net Flows

**Why we want it:**
- Coins moving off exchanges (self-custody) = reduced selling pressure, bullish
- Large exchange inflows = potential distribution/selling pressure, bearish
- Leading indicator for accumulation vs distribution phases

**How AI agents would use it:**
- Query before entering swing trades (multi-day holds)
- If net outflows >10K BTC in 7 days ’ increases position size (supply shock signal)
- If net inflows during technical breakdown ’ confirms bearish bias
- Combine with price action: outflows + sideways price = accumulation before pump

**Where it exists today:**
- Glassnode ($100-500/month) - exchange flow data with historical context
- CryptoQuant ($100-500/month) - real-time exchange reserves and flows
- Santiment ($200-500/month) - exchange flow metrics

---

## 3. Liquidation Level Heatmaps

**Why we want it:**
- Price tends to move toward liquidation clusters (market maker behavior)
- Large liquidation walls = potential squeeze targets
- Cascading liquidations cause 10-20% moves in hours

**How AI agents would use it:**
- Agent sees funding rate extreme (>1.5%) ’ queries liquidation data
- If $2B+ liquidations clustered $500 above current price ’ enter LONG expecting hunt
- If liquidations spread thin ’ avoid leverage play
- Use to set price targets (liquidation clusters = magnets)

**Where it exists today:**
- Coinglass ($200-500/month Pro) - multi-exchange liquidation heatmaps
- Binance API (free) - estimated liquidation levels for Binance only
- Hyblock Capital ($100-300/month) - liquidation clustering analytics

---

## 4. Narrative Velocity & Topic Clustering

**Why we want it:**
- Catch meme coin pumps 24-48 hours before peak
- 400%+ mention spike = late-stage hype (fade signal)
- Early narrative detection = 10-100x opportunities

**How AI agents would use it:**
- Monitor token mention velocity across Twitter/Reddit/forums
- If mentions spike 200%+ with low price increase ’ early stage, enter
- If mentions spike 500%+ with 300% price pump ’ late stage, fade/short
- Track narrative themes (AI, gaming, DeFi) for sector rotation

**Where it exists today:**
- Santiment Pro ($500-1500/month) - ML topic modeling and social trends
- LunarCrush ($200-500/month) - social mention tracking and clustering
- Kaito AI ($300-1000/month) - crypto-native social intelligence

---

## 5. Entity-Labeled On-Chain Flows

**Why we want it:**
- See when specific institutions (Jump Trading, Alameda successors, major funds) move capital
- Protocol treasuries moving funds = insider signal
- Identify fund rotation between assets/chains

**How AI agents would use it:**
- Query when price action diverges from technicals
- If Jump Trading accumulating while price flat ’ high conviction long
- If VC fund dumping tokens ’ avoid or short
- Track smart money rotation: "funds moving from ETH to SOL" = narrative shift

**Where it exists today:**
- Nansen Pro ($500-2000/month) - entity labels for funds, protocols, exchanges
- Chainalysis ($1000-5000/month) - institutional entity tracking
- Arkham ($100-500/month paid tier) - entity identification and flow tracking

---

## 6. Order Book Liquidity & Depth Analysis

**Why we want it:**
- Assess slippage risk before large trades
- Thin liquidity = easy manipulation, avoid
- Detect "liquidity hunts" where market makers raid stop-losses

**How AI agents would use it:**
- Before executing large position (>$50K) ’ query order book depth
- If bid/ask spread >0.5% or depth <$500K within 1% ’ reduce position size
- Detect walls: large buy wall at support = likely hold, large sell wall at resistance = likely rejection
- Identify spoofing: walls that appear/disappear = manipulation signal

**Where it exists today:**
- Kaiko ($300-1000/month) - institutional-grade order book data
- Coinalyze Pro ($100-300/month) - order book heatmaps
- Direct exchange websockets (free) - real-time order book but no aggregation/analysis

---

## 7. Options Flow & Gamma Exposure

**Why we want it:**
- Institutional traders use options for tail risk hedging
- High gamma exposure = potential for explosive moves
- Options positioning shows where smart money expects price

**How AI agents would use it:**
- Query before major volatility events (FOMC, CPI)
- If large call buying at $110K BTC ’ institutions expect breakout, align long
- If put/call ratio spikes >2.0 ’ extreme fear, contrarian long opportunity
- Track max pain price (where most options expire worthless) as price magnet

**Where it exists today:**
- Deribit API (free basic, paid for analytics) - dominant crypto options exchange
- Amberdata ($1000-5000/month) - options flow analytics
- Laevitas ($500-2000/month) - crypto derivatives analytics including options

---

## 8. BTC/ETH ETF Flow Data (Real-Time)

**Why we want it:**
- Institutional money flows into crypto via ETFs
- $500M+ single-day inflow = multi-day bullish catalyst
- Outflows signal institutional de-risking

**How AI agents would use it:**
- Query daily before US market open (ETF data lags 1 day)
- If 3+ consecutive days of net inflows >$200M ’ increase BTC allocation
- If sudden outflow after rally ’ take profits, expect consolidation
- Compare BTC vs ETH flows to identify rotation

**Where it exists today:**
- Bloomberg Terminal ($2000+/month) - institutional-grade ETF flows
- Farside Investors (free but delayed) - daily ETF flow tracking
- Apollo (Bloomberg alternative, $500-2000/month) - ETF flow data

---

## 9. Influencer Amplification & Network Analysis

**Why we want it:**
- Detect coordinated pump campaigns when multiple influencers align
- Track which influencers have actual market-moving power
- Social graph analysis shows manipulation vs organic growth

**How AI agents would use it:**
- Monitor top 100 crypto Twitter influencers for coordinated messaging
- If 5+ influencers tweet same ticker within 2 hours ’ pump warning, fade
- Track influencer portfolio disclosures to follow smart money
- Detect engagement bot networks (fake hype)

**Where it exists today:**
- LunarCrush Pro ($200-800/month) - influencer tracking and social graphs
- Santiment ($500-1500/month) - social network analysis
- Kaito AI ($300-1000/month) - crypto influencer intelligence

---

## 10. Market Maker Inventory Signals

**Why we want it:**
- Market makers reducing inventory = liquidity crisis warning
- MM positioning shows where they expect price (they front-run)
- Inventory buildup = MM expects demand, bullish

**How AI agents would use it:**
- Query when volatility spikes >5% in 1 hour
- If MMs reducing inventory across exchanges ’ exit positions, liquidity crisis imminent
- If MMs building inventory at support level ’ confirmation of bottom
- Track MM profitability: stressed MMs = wider spreads = poor trading environment

**Where it exists today:**
- Institutional exchange partnerships (expensive, $5K-20K/month)
- Proprietary MM analytics firms (custom quotes)
- Some data available from market structure research firms like Kaiko (enterprise tier)

---

## 11. Stablecoin Issuer Mint/Burn Patterns

**Why we want it:**
- Tether minting $1B+ = fresh liquidity entering crypto (bullish)
- USDC burns = capital leaving crypto (bearish)
- Leading indicator for market liquidity conditions

**How AI agents would use it:**
- Query daily to assess macro liquidity environment
- If Tether mints >$500M in 24 hours ’ expect buying pressure within 48 hours
- If USDC supply decreasing for 7+ days ’ reduce exposure, risk-off
- Compare mint/burn vs price: mints + flat price = accumulation phase

**Where it exists today:**
- Glassnode ($100-500/month) - stablecoin supply tracking
- DefiLlama (free) - stablecoin market cap data
- CryptoQuant ($100-500/month) - stablecoin flow metrics
- Direct blockchain explorers (free but requires parsing)

---

## 12. Multi-Exchange Funding Rate Divergence

**Why we want it:**
- Funding rate spread across exchanges shows arbitrage opportunities
- Divergence signals manipulation or isolated liquidation risk on one exchange
- Extreme divergence = market structure breaking down

**How AI agents would use it:**
- Compare funding rates across Binance, Bybit, OKX, Deribit
- If Binance funding +2% but others neutral ’ isolated liquidation risk, avoid Binance longs
- If all exchanges showing negative funding for 48+ hours ’ contrarian long setup
- Arbitrage detection: +1% on one exchange, -0.5% on another = opportunity

**Where it exists today:**
- Coinglass (free basic, $200-500/month Pro) - multi-exchange funding aggregation
- Direct exchange APIs (free) - Binance, Bybit, OKX all provide funding data
- Laevitas ($500-2000/month) - derivatives analytics across venues

---

## 13. DApp Traffic & User Growth

**Why we want it:**
- User growth = fundamental demand for L1/L2 tokens
- 50%+ user growth over 30 days = bullish for native token
- Declining usage = bearish signal before price reflects it

**How AI agents would use it:**
- Query before trading L1/L2 tokens (ETH, SOL, AVAX, ARB, OP)
- If Solana DApp users up 40% in 30 days ’ increases SOL allocation
- If Arbitrum users declining despite token pump ’ fade rally
- Compare user growth to token price: growth + flat price = accumulation opportunity

**Where it exists today:**
- Token Terminal ($300-1000/month) - DApp usage and protocol metrics
- DappRadar ($100-500/month) - user and transaction tracking across chains
- Dune Analytics (free + pro $300/month) - custom on-chain queries for user data

---

## 14. Crypto Company Hiring Velocity

**Why we want it:**
- Hiring surge = company expansion, bullish for ecosystem tokens
- Layoffs = contraction, bearish signal
- Leading indicator vs price (hiring precedes growth by 6-12 months)

**How AI agents would use it:**
- Track LinkedIn job postings for major protocols (Uniswap, Aave, Lido, etc.)
- If Coinbase hiring spikes 30% ’ bullish for CEX tokens and BTC/ETH
- If exchange announces layoffs ’ reduce exposure, expect bearish pressure
- Track developer hiring specifically: dev team growth = protocol improvements coming

**Where it exists today:**
- Thinknum ($200-500/month) - job posting analytics and headcount tracking
- Revelio Labs ($500-2000/month) - workforce intelligence
- Manual LinkedIn scraping (free but requires infrastructure)
- Indeed API (free tier available) - job posting data

---

## 15. Cross-Chain Capital Flows & Bridge Analytics

**Why we want it:**
- Money rotating from Ethereum to Solana = sector rotation signal
- Bridge volume spikes = trend confirmation (capital following narrative)
- Net outflows from a chain = weakening ecosystem

**How AI agents would use it:**
- Query weekly to identify capital rotation trends
- If $500M+ bridged from ETH to SOL in 7 days ’ rotate portfolio to SOL ecosystem
- If bridge volume declining on a chain despite token pump ’ distribution signal
- Track capital following narratives: bridge volume to gaming chains = gaming season

**Where it exists today:**
- Nansen ($500-2000/month) - cross-chain flow tracking
- Dune Analytics (free + $300/month pro) - bridge transaction analytics
- DefiLlama (free) - bridge volume aggregation
- L2Beat (free) - L2 bridge activity and TVL flows
