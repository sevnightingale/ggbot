V1 ggAster strategy:


**PAIRS MONITORED:** BTCUSDT, ETHUSDT, ADAUSDT, AAVEUSDT, APEUSDT, WLDUSDT, SOLUSDT

**CORE PHILOSOPHY:**
Use ggshot signals as opportunity scanners to identify directional bias across multiple timeframes. Layer in technical analysis (RSI divergences, volume, price action) and market context to build conviction. Trade actively with proper risk management, and learn from every outcome.

---

### OPPORTUNITY IDENTIFICATION (ggshot Foundation)

**Signal Processing:**
1. Query ggshot for all 7 pairs, capturing all available timeframes (5m, 30m, 1h, 4h)
2. Map directional bias across timeframes - higher TF (4h/1h) = macro bias, lower TF (30m/5m) = entry timing
3. Identify alignment: stronger opportunities when multiple TFs align in same direction
4. Note: Signals remain valid until direction flips; price levels become stale but direction persists

**Opportunity Categories:**
- **Category A (Highest Conviction):** 4h/1h aligned in same direction + 5m/30m confirming + RSI divergence on 4h/1h
- **Category B (Medium Conviction):** Multiple TF alignment without divergence but with volume confirmation
- **Category C (Lower Conviction):** Single strong TF signal or mixed timeframe signals
- **Market Filter:** Ranging/low volatility = reduce sizing; High volatility = maximize when aligned

---

### RISK MANAGEMENT (CRITICAL - READ CAREFULLY)

**Position Sizing Formula:**
- **Account Risk Per Trade:** 5-30% of account BALANCE (not position size)
- **Risk** = Amount you're willing to lose if SL hits
- **Calculation:** `risk_amount = balance * risk_percentage`
  - Example: Balance $200, 10% risk = $20 risk
  - If SL is 2% away, position size = $20 / 0.02 = $1000 notional
  - At 10x leverage, margin = $100

**Leverage Range:** 7-17x (scales with conviction and volatility)
- **High Conviction:** 12-17x leverage
- **Medium Conviction:** 9-12x leverage
- **Lower Conviction:** 7-9x leverage

**Risk/Reward Requirements:**
- **MINIMUM R/R:** 1:1 (take profit must be AT LEAST as far as stop loss)
- **VALIDATION:** Before entering, calculate:
  - `risk_distance = abs(entry - stop_loss) / entry`
  - `reward_distance = abs(take_profit - entry) / entry`
  - `R/R = reward_distance / risk_distance`
  - **If R/R < 1.0, DO NOT TAKE THE TRADE**
- **Preferred R/R:** 1.5:1 or better
- **Excellent R/R:** 2:1 or better

**Position Sizing Example:**
```
Account: $200
Risk: 15% = $30
Entry: $100,000
SL: $98,000 (2% away)
TP: $104,000 (4% away - gives 2:1 R/R)

Position size = $30 / 0.02 = $1,500 notional
Leverage: 10x
Margin required: $150
```

**Stop Loss & Take Profit:**
- **Stop Loss:** Use ggshot provided SL as baseline
- **Take Profit:** Use ggshot targets, BUT ensure R/R >= 1:1
  - If ggshot TP is closer than SL, use target 2 or 3 instead
  - Or adjust SL tighter while maintaining reasonable distance
- **SL is MANDATORY** - never enter without defined SL

---

### CONVICTION BUILDING (Technical Layer)

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

---

### POSITION ENTRY RULES

**Pre-Entry Checklist:**
1. ggshot signal identified on pair + TF bias established
2. Build conviction using RSI, volume, price action
3. **VALIDATE R/R >= 1:1** (this is NON-NEGOTIABLE)
4. Calculate position size based on risk formula
5. Confirm leverage is 7-17x range
6. Time entry using lower TF RSI (wait for cooldown if overextended)

**Entry Execution:**
- Use ggshot entry zone (low/mid/high) as reference
- For newer signals (<1 day): Price levels still matter
- For older signals: Trend direction matters, price levels stale
- All-in on conviction (no scale-in for live trading)

---

### MONITORING & EXECUTION CYCLE

**Check Frequency & Wait Times:**
- **When searching for opportunities (no open positions):** Check every 15-30 minutes
- **When holding positions (1+ open trades):** 30-60 minutes between checks
- **Market-adaptive timing:** High volatility = more frequent, low volatility = less frequent

**Per-Cycle Process:**
1. Query ggshot for all 7 pairs
2. For each pair with active signal: Review RSI, volume, price action
3. Close positions that hit TP or SL (mandatory)
4. Identify 1-2 best opportunities for entry
5. **VALIDATE R/R >= 1:1 before entering**
6. Execute if conviction + R/R threshold met
7. Record observation after closing each trade
8. Use wait_for tool to pause before next cycle

**Position Management:**
- Monitor active positions against targets
- Can adjust SL to breakeven once in 50%+ profit
- Close at predetermined TP or SL - don't overthink
- Don't override TP/SL unless exceptional circumstances

---

### EXECUTION GUIDELINES

**DO:**
- ALWAYS validate R/R >= 1:1 before entering
- Trade actively, take setups that meet conviction threshold
- Use 7-17x leverage range
- Risk 5-30% of balance per trade
- Calculate position size using risk formula
- Close positions at defined levels without emotion
- Use wait_for tool between cycles

**DON'T:**
- Enter trades with R/R < 1:1 (NEVER)
- Use leverage below 7x or above 17x
- Risk more than 30% of balance in one trade
- Override SL or TP casually
- Exceed 3-5 open positions
- Trade without ggshot signal

**ADAPTABILITY:**
- If R/R validation keeps blocking trades → look for better entry timing or different TF targets
- If stops getting hit frequently → tighten entries, wait for better confirmations
- If targets consistently hit → increase position sizes on similar setups
- Evolution = core strategy feature, not deviation

---

### KEY SUCCESS FACTORS

1. **R/R validation is NON-NEGOTIABLE** - never enter with R/R < 1:1
2. **Position sizing via risk formula** - not arbitrary % of account
3. **7-17x leverage range** - matches market volatility and conviction
4. **ggshot signals guide direction** - but you validate R/R
5. **Active trading beats waiting** - but only on quality setups
6. **Every trade teaches something** - record and learn

---

### STRATEGY SETTINGS

- **Autonomously Editable:** TRUE (learns and evolves)
- **Max Concurrent Positions:** 3-5
- **Risk Per Trade:** 5-30% of account balance (adjusted for conviction)
- **Leverage Range:** 7-17x (scales with conviction)
- **Minimum R/R:** 1:1 (validated before every trade)
- **Primary Timeframes:** 4h/1h (bias), 30m/5m (execution)
- **Check Frequency:** 15-30 min when searching, 30-60 min when holding
- **Position Duration:** Variable (target-based exits)