# Data Points for Brickroad Partnership

## 1. Whale Wallet Clustering & Smart Money Tracking

**Why we want it:**
- See institutional accumulation/distribution before price moves
- Whale buying at market lows often precedes 20-30% pumps within days
- Identify smart money positioning during consolidation periods

**How AI agents would use it:**
- Agent detects technical breakout with low volume → queries whale data
- If top 50 wallets accumulated in past 48 hours → high confidence LONG
- If whales distributing to exchanges → skip trade or take opposite position
- Use as confirmation filter for technical setups

**Where it exists today:**
- Nansen ($100-500/month) - entity-labeled wallet tracking
- Arkham Intelligence ($100-500/month paid tier) - wallet clustering and labels
- No free alternatives with entity labels and clustering

---

## 2. Smart Money DeFi Positioning

**Why we want it:**
- See which DeFi protocols whale wallets are using before trends emerge
- Capital flowing to Aave vs Compound = leading indicator for protocol tokens
- Whale staking behavior shows conviction levels

**How AI agents would use it:**
- Query before trading DeFi governance tokens (AAVE, UNI, CRV, etc.)
- If whales moving capital into Aave v3 → accumulate AAVE token
- Track whale yield strategies: if whales rotating from ETH staking to liquid staking → bullish for LSD tokens
- Identify emerging protocols before retail: whale capital flow = early signal

**Where it exists today:**
- Nansen Pro ($500-2000/month) - "Smart Money" wallet DeFi tracking
- Arkham ($100-500/month) - protocol interaction tracking for known entities
- No free tools provide whale-specific DeFi positioning

---

## 3. Liquidation Level Heatmaps

**Why we want it:**
- Price tends to move toward liquidation clusters (market maker behavior)
- Large liquidation walls = potential squeeze targets
- Cascading liquidations cause 10-20% moves in hours

**How AI agents would use it:**
- Agent sees funding rate extreme (>1.5%) → queries liquidation data
- If $2B+ liquidations clustered $500 above current price → enter LONG expecting hunt
- If liquidations spread thin → avoid leverage play
- Use to set price targets (liquidation clusters = magnets)

**Where it exists today:**
- Coinglass Pro ($200-500/month) - multi-exchange liquidation heatmaps with clustering analytics
- Hyblock Capital ($100-300/month) - proprietary liquidation clustering algorithms
- Free alternatives lack predictive clustering analysis

---

## 4. Narrative Velocity & Topic Clustering

**Why we want it:**
- Catch meme coin pumps 24-48 hours before peak
- 400%+ mention spike = late-stage hype (fade signal)
- Early narrative detection = 10-100x opportunities

**How AI agents would use it:**
- Monitor token mention velocity across Twitter/Reddit/forums
- If mentions spike 200%+ with low price increase → early stage, enter
- If mentions spike 500%+ with 300% price pump → late stage, fade/short
- Track narrative themes (AI, gaming, DeFi) for sector rotation

**Where it exists today:**
- Santiment Pro ($500-1500/month) - ML topic modeling and social trends
- Kaito AI ($300-1000/month) - crypto-native social intelligence with clustering
- Free tools don't provide velocity calculations or ML clustering

---

## 5. Entity-Labeled On-Chain Flows

**Why we want it:**
- See when specific institutions (Jump Trading, major funds) move capital
- Protocol treasuries moving funds = insider signal
- Identify fund rotation between assets/chains

**How AI agents would use it:**
- Query when price action diverges from technicals
- If Jump Trading accumulating while price flat → high conviction long
- If VC fund dumping tokens → avoid or short
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
- Before executing large position (>$50K) → query order book depth
- If bid/ask spread >0.5% or depth <$500K within 1% → reduce position size
- Detect walls: large buy wall at support = likely hold, large sell wall at resistance = likely rejection
- Identify spoofing: walls that appear/disappear = manipulation signal

**Where it exists today:**
- Kaiko ($300-1000/month) - institutional-grade order book analytics with spoofing detection
- Coinalyze Pro ($100-300/month) - order book heatmaps with depth analysis
- Free exchange websockets don't provide aggregation or manipulation detection

---

## 7. Options Flow & Gamma Exposure

**Why we want it:**
- Institutional traders use options for tail risk hedging
- High gamma exposure = potential for explosive moves
- Options positioning shows where smart money expects price

**How AI agents would use it:**
- Query before major volatility events (FOMC, CPI)
- If large call buying at $110K BTC → institutions expect breakout, align long
- If put/call ratio spikes >2.0 → extreme fear, contrarian long opportunity
- Track max pain price (where most options expire worthless) as price magnet

**Where it exists today:**
- Amberdata ($1000-5000/month) - options flow analytics with gamma exposure models
- Laevitas ($500-2000/month) - crypto derivatives analytics including gamma
- Deribit public API lacks processed analytics and gamma calculations

---

## 8. BTC/ETH ETF Flow Data (Same-Day Estimates)

**Why we want it:**
- Institutional money flows into crypto via ETFs
- $500M+ single-day inflow = multi-day bullish catalyst
- Official data lags 1 day - same-day estimates give edge

**How AI agents would use it:**
- Query intraday for real-time ETF flow estimates (vs next-day official data)
- If 3+ consecutive days of net inflows >$200M → increase BTC allocation
- If sudden outflow after rally → take profits, expect consolidation
- Compare BTC vs ETH flows to identify rotation

**Where it exists today:**
- Bloomberg Terminal ($2000+/month) - but may not distribute via Brickroad
- Specialized ETF analytics firms with intraday estimation models ($500-2000/month)
- Farside Investors is free but delayed 1 day (no intraday estimates)

---

## 9. Influencer Amplification & Network Analysis

**Why we want it:**
- Detect coordinated pump campaigns when multiple influencers align
- Track which influencers have actual market-moving power
- Social graph analysis shows manipulation vs organic growth

**How AI agents would use it:**
- Monitor top 100 crypto Twitter influencers for coordinated messaging
- If 5+ influencers tweet same ticker within 2 hours → pump warning, fade
- Track influencer portfolio disclosures to follow smart money
- Detect engagement bot networks (fake hype)

**Where it exists today:**
- LunarCrush Pro ($200-800/month) - influencer tracking and social graphs
- Kaito AI ($300-1000/month) - crypto influencer intelligence with network analysis
- Free tools don't provide coordination detection or bot analysis

---

## 10. Wallet Profitability Tracking & Copy Trading Signals

**Why we want it:**
- Follow wallets with proven track records (>70% win rate)
- See what profitable traders are buying before pumps
- Inverse losing wallets (contrarian signal)

**How AI agents would use it:**
- Identify top 100 most profitable wallets by realized PnL
- When profitable wallet cluster accumulates a token → investigate for entry
- Track whale wallet historical win rates: 80%+ win rate = higher weight signal
- Inverse retail wallets: if losing wallets buying → fade or short

**Where it exists today:**
- Nansen "Smart Money" ($500-2000/month) - wallet PnL tracking
- Arkham ($100-500/month) - wallet performance metrics
- Debank Pro ($200-500/month) - wallet profitability analytics

---

## 11. Token Holder Concentration & Distribution Changes

**Why we want it:**
- Increasing concentration = whales accumulating, bullish
- Decreasing concentration = distribution to retail, late stage
- Sharp concentration changes precede major moves

**How AI agents would use it:**
- Query before entering swing trades (multi-day holds)
- If top 10 holders increasing % ownership over 30 days → accumulation signal
- If Gini coefficient increasing (more concentrated) during price decline → smart money buying dip
- If concentration dropping during rally → distribution, exit signal

**Where it exists today:**
- Santiment ($500-1500/month) - holder distribution metrics with concentration tracking
- Glassnode ($300-800/month paid tiers) - supply distribution analytics
- IntoTheBlock ($200-500/month) - holder concentration changes

---

## 12. Protocol Revenue & Fee Analytics (Processed)

**Why we want it:**
- Protocol revenue = fundamental value for governance tokens
- Revenue acceleration = undervalued opportunity
- Fee decline = warning signal before price reflects

**How AI agents would use it:**
- Query before trading DeFi governance tokens
- If Uniswap 30-day fees up 50% but token flat → accumulate UNI
- Compare revenue to market cap: high revenue growth + low valuation = value opportunity
- Track revenue trends vs price: revenue growing but price declining = accumulation zone

**Where it exists today:**
- Token Terminal ($300-1000/month) - protocol economics with revenue analytics
- DefiLlama Pro ($200-500/month) - processed fee and revenue data
- Messari Pro ($500-2000/month) - protocol financial metrics

---

## 13. Crypto Proxy Equity Options Flow (COIN, MSTR, MARA)

**Why we want it:**
- Institutional traders often position in equities before crypto
- MSTR options activity = leveraged BTC exposure signal
- Coinbase options = crypto volatility expectations

**How AI agents would use it:**
- Query before major BTC moves
- If MSTR call buying surges → institutions expect BTC rally, align long
- If COIN put buying increases → expect crypto volatility or decline
- Use equity options as leading indicator (trade before crypto retail reacts)

**Where it exists today:**
- SpotGamma ($200-500/month) - equity options flow with gamma exposure
- FlowAlgo ($200-400/month) - unusual options activity alerts
- Bloomberg Terminal ($2000+/month) - but likely won't distribute via Brickroad

---

## 14. Institutional Crypto Exposure Survey Data

**Why we want it:**
- Survey data from family offices, RIAs, hedge funds on crypto allocation
- Increasing allocation = demand coming, decreasing = distribution ahead
- Sentiment gauge at institutional level (not retail)

**How AI agents would use it:**
- Query quarterly or monthly for allocation trend changes
- If institutions increasing crypto allocation from 2% → 5% → demand surge coming
- If allocation declining despite price rally → smart money exiting, warning signal
- Use as macro positioning indicator (combine with ETF flows)

**Where it exists today:**
- Fidelity Digital Assets surveys (sometimes public, but delayed)
- Bitwise/Coinbase institutional surveys (proprietary distribution)
- Research firms aggregating prime broker data ($500-2000/month for processed reports)

---

## 15. Credit Spreads & Risk Appetite Index (Processed for Crypto)

**Why we want it:**
- Credit spreads widening = institutional risk-off before crypto feels it
- Leading indicator for crypto volatility (1-3 day lead time)
- Shows when "risk-on" environment is deteriorating

**How AI agents would use it:**
- Query daily before major position changes
- If HY-IG credit spread widens >50bps in 3 days → reduce crypto exposure
- If credit spreads tightening for 2+ weeks + crypto flat → accumulation opportunity
- Use as filter: widening spreads = avoid new longs, only shorts/cash

**Where it exists today:**
- Bloomberg Terminal ($2000+/month) - unlikely for Brickroad
- Boutique risk analytics firms processing credit data for crypto correlation ($300-1000/month)
- Fred API has raw data (free) but lacks processed crypto correlation analysis
