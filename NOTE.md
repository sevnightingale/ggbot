# Autonomous Trading Strategy - BTC Momentum Trading

**Symbol:** BTC/USDT only
**Philosophy:** Use ggShot's multi-timeframe momentum signals as directional foundation. Layer market intelligence to assess regime, build conviction, and time entries. Trade actively with asymmetric risk management - quick to lock profits, reluctant to exit at loss without data invalidation.

--

## Understanding ggShot Multi-Timeframe Dynamics

**ggShot is a momentum indicator with timeframe sensitivity:**

```
5m  � Flips first (most sensitive, noise-prone)
30m � Confirms short-term momentum if trend continues
1h  � Trend establishing, more reliable
4h  � Strong trend, highest conviction
```

**How to Read Signals:**

- **4h/1h = Market Regime:** These establish the broader directional bias
- **30m/5m = Entry Timing:** These show shorter-term momentum shifts
- **Alignment Context:** When multiple timeframes point the same direction, it indicates momentum consistency. When they diverge, it signals either early reversal or counter-trend action.
- **Timeframe Flips:** Lower timeframes flip first. If a lower TF flips against higher TFs then flips back to align, this can signal a strong continuation entry point.

**Note:** Multi-TF alignment provides context and timing insight, but conviction comes from layering additional market data - volume, regime indicators, technicals, and risk/reward structure.

**Price Action Context:**
- ggShot has an underlying trendline (not visible real-time)
- Price often bounces off trendline or key structural levels
- Old ggShot targets become new support/resistance zones

---

## Trade Types & Timeframe Strategy

**Your approach should adapt based on regime and timeframe alignment:**

### Ranging Markets → Shorter Timeframe Trades
When regime indicators show consolidation (low ADX, contracted BBWidth, flat TRIX), price is bouncing between levels rather than trending.

**Strategy:**
- Focus on lower timeframes (5m, 30m) for both entry and targets
- Tighter SL/TP spreads - aim for quick 1-1.5R moves
- Exit at key levels (VWAP, Donchian bands) rather than waiting for trend targets
- Smaller position sizes - ranges can break either direction
- Hold duration: Minutes to hours

### Counter-Trend Setups → Quick Reversals
When lower timeframes oppose higher timeframe bias - you're catching a rebound within a larger trend.

**Strategy:**
- Use the reversal timeframe (30m, 5m) for entry and exit decisions
- Tight stops - you're fading the larger trend
- Take profits quickly at first resistance - don't wait for higher TF targets
- Reduced position size - higher risk
- Hold duration: Quick in, quick out

### Trend Continuation → Wider Targets
When entering WITH the higher timeframe trend, especially at pullbacks where lower TF shows reversal.

**Strategy:**
- Use higher timeframes (1h, 4h) to set targets
- Wider stops - give the trend room to work
- Can use 4h ggShot targets if not yet hit, or structure-based levels
- Trail stops instead of exiting early - let winners run
- Larger position sizes - trend backing you
- Hold duration: Hours to days

**Key Principle:** Match your timeframe focus, target distance, and hold duration to the type of opportunity. Fighting trends or trading ranges requires different execution than riding established momentum.

---

## Session Start: Market Regime Assessment

**At the beginning of each trading session, establish the broader market regime using HIGHER timeframe indicators (1h, 4h, 1d preferred):**

**Regime Indicators (query what makes sense):**
- **Aroon:** Trending (Aroon-Up/Down separation) vs ranging (tight together)?
- **BBWidth:** Expanding (volatility increasing) vs contracting (consolidation)?
- **TRIX:** Rising (momentum building) vs flat/falling (weakening)?
- **ADX:** Strong trend (>25) vs weak trend (<20)?
- **MACD:** Above/below zero line? Histogram expanding/contracting?

**Regime Classification:**
- **Strong Trend:** Multiple indicators agree on direction, ADX >25, BBWidth expanding = maximize sizing
- **Developing Trend:** Mixed signals, moderate ADX = standard sizing
- **Ranging/Choppy:** Aroon tight, BBWidth contracted, MACD near zero = reduce sizing or wait
- **Counter-Trend:** Regime opposes ggShot signal direction = high risk, pass or minimal size

**Purpose:** Don't fight the broader market. If regime says range and ggShot says LONG, be cautious.

---

## Building Conviction: The Layered Approach


**RSI Analysis:**
- **Divergences (HIGH SIGNAL):** Especially on 4h/1h - price makes new high/low but RSI doesn't = reversal strength
- **Overextensions:** RSI >80 or <20 on lower TFs - use to time entries
- **Use:** Lower TF RSI (5m/30m) to find optimal entry price, higher TF (4h/1h) to confirm reversal potential

**Volume Confirmation:**
- OBV trending in same direction as price = validates move
- Volume spike on entry = higher conviction
- Low volume on moves = skepticism, reduce size

**Price Action & Support/Resistance:**
- VWAP as dynamic level for reversals
- ggshot trend_line and entry zones as structural levels
- Previous targets become new support/resistance

**Dynamic Market Data Layer (use contextually):**
You have 32 data points across 7 categories available via `query_market_data`. Use intelligently based on context - query what adds conviction, confirms/invalidates your thesis, or provides necessary market context for the specific decision you're making.

**Philosophy:** These are capabilities, not checklists. Query what's relevant to the setup at hand, not everything every time.

---

## Risk Management

**Position Sizing Formula:**
```
Risk per trade: 5-30% of account balance (NOT position size)
risk_amount = balance � risk_percentage
position_size = risk_amount / (distance_to_SL / entry_price)
margin_required = position_size / leverage
```

**Leverage Scaling (5-20x range):**
- **Higher leverage (15-20x):** Strong setup - favorable regime, strong volume, solid risk/reward
- **Moderate leverage (10-15x):** Standard setup - reasonable conviction with proper structure
- **Lower leverage (5-10x):** Uncertain setup - mixed signals, weak volume, or ranging conditions

**Risk/Reward Requirement:**
- **MINIMUM:** R/R >= 1:1 (take profit distance must equal or exceed stop loss distance)
- **VALIDATION:** Always calculate before entry:
  ```
  risk_distance = abs(entry - SL) / entry
  reward_distance = abs(TP - entry) / entry
  R/R = reward_distance / risk_distance
  ```
- **If R/R < 1.0:** DO NOT TAKE THE TRADE (non-negotiable)

---

## Setting Stop Loss & Take Profit

**CRITICAL RULE:** Always calculate from CURRENT MARKET PRICE, never use stale ggShot levels.

**Stop Loss Placement (use data to be intelligent):**
1. **ATR-based:** Query ATR on signal timeframe, use 1.5-2.0� ATR for SL distance
2. **Structure-based:** Place below key support (LONG) or above resistance (SHORT)
3. **Donchian-based:** Use Donchian channel boundaries as natural stops
4. **Conviction-adjusted:** Tighter stops (1.5� ATR) for low conviction, wider (2.0-2.5� ATR) for high conviction

**Take Profit Placement:**
1. **Primary target:** 2R minimum (ensure R/R >= 1:1, prefer 1.5:1 or better)
2. **Use structure:** Opposite Donchian band, previous ggShot targets, VWAP standard deviations
3. **Multiple targets:** Consider scaling out at 1R, 2R, 3R if strong trend

**Intent Matters:**
- Your SL should have reasoning behind it (not arbitrary 2%)
- Your TP should target logical zones (not arbitrary 4%)
- Use market data queries to inform these decisions

---

## Position Management: Asymmetric Approach

**Taking Profits:**
- Locking profits is valid - markets can reverse at any time
- If you see clear reversal signs (ggShot TF flipping, volume drying up, RSI divergence), closing to protect profits is reasonable
- Trailing stops to breakeven once well into profit reduces risk
- Balance conviction in your thesis against taking profits too early - both have merit

**Closing at Loss (Requires Justification):**
- Don't close before SL without data-driven reason
- ONLY close early if **thesis is invalidated by data:**
  - ggShot higher TF flipped against you (regime changed)
  - Volume completely dried up (invalidates momentum thesis)
  - Key technical level clearly broken (structure thesis failed)
  - Major news/event changes fundamental picture
- **Philosophy:** Your SL was placed intentionally using data. Respect it unless data proves you wrong BEFORE price hits it.

**Monitoring Frequency:**
- **No positions:** Check every 30-60 minutes (patient, selective)
- **Holding positions:** Check every 10-30 minutes (attentive, ready to act)
- **Near SL/TP or high volatility:** Check every 5-15 minutes

---

## Red Flags: When to Reduce Risk or Pass

**Reduce position size by 30-50% if:**
- Counter-trend regime + weak volume (<75% average)
- Extreme RSI (>80 or <20) on signal timeframe at entry
- ATR spike (high volatility) + overextended price (far from VWAP/moving averages)
- Only 1 timeframe aligned (no confirmation from adjacent TFs)

**Pass the trade if:**
- 2+ red flags present simultaneously
- R/R < 1:1 (always pass)
- Counter-trend to strong regime without exceptional setup
- Volume extremely weak (<50% average) on confirmation

---

## Execution Cycle

**Per-Cycle Process:**
1. Check current positions first - close any at TP/SL, assess if thesis still valid
2. Query ggShot for BTC across all timeframes (5m, 30m, 1h, 4h)
3. Assess TF alignment - identify conviction level
4. If strong signal identified:
   - Assess broader regime (if first trade of session or regime unclear)
   - Check volume on signal timeframe
   - Review core technicals (RSI multi-TF, OBV, VWAP)
   - Query additional market data if needed for conviction/invalidation
5. Calculate SL/TP from CURRENT PRICE using ATR/structure
6. Validate R/R >= 1:1
7. Calculate position size via risk formula
8. Execute if conviction threshold met
9. Record observation after closing any trade
10. Use wait_for tool before next cycle (adapt to volatility)

---

## Execution Guidelines

**DO:**
- Calculate all levels (SL/TP/entry) from CURRENT PRICE
- Validate R/R >= 1:1 before every entry (non-negotiable)
- Use market data queries contextually to build conviction
- Scale leverage (5-20x) with conviction level
- Lock profits early without guilt
- Use wait_for between cycles (be patient)
- Record observations after closing trades

**DON'T:**
- Use stale ggShot price levels for SL/TP (direction only if >1 day old)
- Enter with R/R < 1:1 (NEVER)
- Close at loss without data invalidation
- Use leverage outside 5-20x range
- Risk >30% of balance in one trade
- Exceed 5 open positions
- Query every data point every cycle (be selective)

**Adaptability:**
- If R/R validation blocking trades � recalculate levels, wait for better entries
- If SL getting hit frequently � tighten entry criteria, wait for stronger confirmations
- If TP consistently hit � increase sizing on similar setups
- Evolution is expected - strategy autonomously editable

---

## Key Success Factors

1. **Multi-TF ggShot analysis** - alignment strength determines conviction
2. **Volume confirmation** - demand real participation, not low-volume noise
3. **Regime awareness** - don't fight strong counter-trends
4. **Intelligent SL/TP** - use ATR/structure, calculate from current price
5. **R/R discipline** - never enter <1:1, always validate
6. **Asymmetric exits** - quick to take profits, slow to take losses (unless data invalidates)
7. **Dynamic market data** - use contextually, not ritually
8. **Patient execution** - wait for quality setups with conviction

---

## Strategy Settings

- **Symbol:** BTC/USDT only
- **Autonomously Editable:** TRUE (learns and evolves)
- **Risk Per Trade:** 5-30% of balance (scaled by conviction)
- **Leverage Range:** 5-20x (scaled by conviction)
- **Minimum R/R:** 1:1 (validated before every trade)
- **Max Positions:** 3-5
- **Primary Timeframes:** 4h/1h (regime), 30m/5m (timing)
- **Check Frequency:** 30-60 min searching, 10-30 min holding
