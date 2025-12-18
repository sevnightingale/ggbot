# The Technician - Strategy Prompt Analysis

**Analysis Date**: 2025-12-18
**Config ID**: `8f9ecc45-2561-42f7-b47c-f003000316b8`

---

## 📋 Full Prompt Review

### Strengths of Current Prompt

**1. Clear Identity** ✅
> "You are The Technician — an active, confident technical trader operating on 5-minute charts."

- Strong persona, confident tone
- Sets expectation for activity (good for arena)
- "Flow state" concept is compelling

**2. Explicit Action Bias** ✅
> "You are expected to trade actively. Most sessions should produce opportunities. Passing is for genuine noise, not mild uncertainty."

- Directly counters over-conservative behavior
- "passing every session isn't discipline — it's fear" = strong guidance
- This is WORKING - bot trades 6.4x/day vs other bots at 0

**3. Clear Confidence Framework** ✅
- 0.70+: Clean setup
- 0.55-0.70: Proceed with awareness
- <0.55: Pass

**4. Structure-Based SL/TP** ✅ (Intent)
> "Always suggest specific prices based on structure, not arbitrary percentages."
> "Stop loss: Place at nearest structural invalidation point"
> "Take profit: Target next structural level"

**5. Nuanced Decision-Making** ✅
> "You're not a rule-following algorithm... Sometimes a setup looks right but feels wrong. Trust that."

- Encourages intuition + indicators
- Allows flexibility vs rigid rules

---

## 🚨 Critical Misalignment: Prompt vs Reality

### Issue #1: SL/TP Not Being Applied

**What Prompt Says:**
> "Always suggest specific prices based on structure, not arbitrary percentages."

**What Actually Happens:**
```
LONG Entry: $86,539
Stop Loss:  $82,212  (5% below - ARBITRARY)
Take Profit: $95,193 (10% above - ARBITRARY)
```

**Evidence**: ALL 45 recent trades use 5%/10% defaults from config, NOT structural levels.

**Impact**:
- Wide stops (5% = $4,327 on $86k BTC) allow massive drawdowns
- Wide targets (10%) rarely hit on 5m timeframe
- Bot's structural analysis is being IGNORED
- Average hold: 55 minutes before "position_management" closes

**Root Cause**: System is applying config defaults AFTER decision, overriding LLM's suggestions.

---

### Issue #2: Exit Decisions Below Own Threshold

**What Prompt Says:**
- 0.55-0.70: "Proceed with awareness"
- <0.55: "Pass. This is noise."

**What Actually Happens:**
- Exit decisions: 48% average confidence
- 13 exits < 50% confidence
- 26 exits in 50-60% range (borderline)

**The Bot Knows It's Uncertain:**
Sample exit reasoning at 45% confidence:
> "However, momentum is mixed... potential reversal but not confirmed..."

**Impact**: Bot is making exit decisions it KNOWS are below threshold, then they don't execute anyway.

---

### Issue #3: Position Management Override

**What Prompt Implies:**
Bot should manage positions via its own exit decisions based on momentum/structure.

**What Actually Happens:**
- 45/46 trades closed by "position_management" (97.8%)
- 0/39 exit decisions actually execute (0%)
- Average hold: 11 candles (55 minutes)
- LLM exits ignored completely

**Result**: The entire position management strategy in the prompt is bypassed.

---

### Issue #4: 5m Frequency May Be Too Fast

**What Prompt Says:**
> "You trade in flow state. Decisive, not hesitant."

**What Actually Happens:**
- 937 decisions per day
- 95.6% are "wait" (895/937)
- 4.4% are actionable (42/937)
- 6.4 trades executed per day

**Analysis**:
- "Flow state" requires pattern recognition over time
- 5m = constant noise, hard to establish flow
- Bot IS decisive when it acts (62% confidence)
- But 937 decisions/day is exhausting, not flowing

**Comparison to Other Bots**:
- The Compass (1d): 1 decision/day
- The Arbiter (4h): 6 decisions/day
- The Contrarian (1h): 24 decisions/day
- The Technician (5m): 937 decisions/day ← outlier!

---

## 🎯 What's Working vs Not Working

### Working Well ✅

**1. Active Trading Philosophy**
- Bot trades 6.4x/day (vs 0 for other bots)
- Prompt's "expected to trade actively" is effective
- Action bias prevents analysis paralysis

**2. Indicator Hierarchy**
- Primary/Secondary/Tertiary structure is clear
- Bot consistently checks MACD, RSI first in reasoning
- Zoom out to 1h/4h for context works

**3. Setup Classification**
- 4 setup types defined (Trend, Breakout, Structure, Exhaustion)
- Bot identifies these correctly in reasoning
- Winning trades show "trend continuation" language

**4. Confidence Calibration**
- Enters at 62% average (above 0.55 threshold)
- Bot rarely trades <55% confidence
- Framework is being followed

### Not Working ❌

**1. Exit Execution**
- 0% of exit decisions execute
- Prompt's position management strategy is dead code
- Bot makes thoughtful exits that get ignored

**2. SL/TP Structural Levels**
- Prompt says "nearest structural invalidation"
- Reality: 5%/10% arbitrary defaults
- Bot's structural analysis wasted

**3. "Passing is Fear" Philosophy**
- Prompt encourages action
- But 5m frequency means 95% still waits
- "Most sessions should produce opportunities" but each 5m "session" is too short

**4. Exit Confidence**
- Exits at 48% average (below 0.55 threshold)
- Violates bot's own rules
- Suggests uncertainty about when to close

---

## 💡 Recommended Prompt Changes

### Change #1: Acknowledge Exit Execution Issue

**Add to prompt (temporary):**
```markdown
## Exit Execution Note

Currently, your exit decisions are not being executed by the system. Trades are being
closed automatically after approximately 11 candles. Until this is fixed, focus your
analysis on HIGH-QUALITY ENTRIES that can withstand automatic exits.

For exits: Still analyze whether position should close, but know that you're providing
guidance for future improvements, not immediate execution.
```

**Rationale**: Be honest about system limitations, adjust strategy accordingly.

---

### Change #2: Strengthen Exit Confidence

**Current:** "0.55-0.70 confidence: Proceed with awareness"

**Revised:**
```markdown
## Exit Confidence Requirements

Because exits require acting against your original conviction, they demand higher certainty:

- **ENTRY**: 0.55+ to act (you're initiating based on opportunity)
- **EXIT**: 0.65+ to act (you're abandoning a position you believed in)

Exit confidence below 0.65 means: "I'm uncertain, let it run."
```

**Rationale**: Exits at 48% are too tentative. Raise the bar.

---

### Change #3: Adjust Frequency Philosophy

**Current:** "5-minute charts... flow state... decisive, not hesitant"

**Option A - Keep 5m, Reframe:**
```markdown
You operate on 5-minute charts, but you don't trade every candle. In a typical 24-hour day,
you'll evaluate ~288 candles but only trade 3-5 high-quality setups (1-2% hit rate).

Your edge is patience WITHIN high frequency. Most traders on 5m overtrade. You wait for
the 1-2% that matter.
```

**Option B - Move to 15m (Recommended):**
```markdown
You operate on 15-minute charts — fast enough to catch intraday moves, slow enough for
quality signals to develop. In a typical day, you'll evaluate ~96 candles and trade 3-5
setups (3-5% hit rate).

This is your sweet spot: Not day-trading noise (5m), not slow macro (4h), but active
technical trading with breathing room.
```

**Rationale**: Reframe expectations around realistic hit rates.

---

### Change #4: Remove SL/TP Structural Language (Until Fixed)

**Current:** "Always suggest specific prices based on structure, not arbitrary percentages."

**Revised:**
```markdown
## Stop Loss & Take Profit

The system currently applies default risk parameters:
- Stop Loss: 5% from entry
- Take Profit: 10% from entry

While these aren't ideal, they're consistent. Structure your entries knowing these
parameters will apply. A 5% stop with 5x leverage = 25% of margin at risk, so position
size is already conservative.

In your reasoning, you can still note key structural levels (for transparency and future
improvements), but know that defaults will apply.
```

**Rationale**: Don't promise what the system can't deliver. Be realistic.

---

### Change #5: Clarify "Active" Definition

**Add section:**
```markdown
## What "Active" Means

You're expected to trade, not sit idle. But "active" doesn't mean:
- ❌ Taking every 0.55+ confidence signal (that's 100+ trades/month)
- ❌ Trading out of boredom when setups are marginal
- ❌ Lowering standards to hit a quota

"Active" means:
- ✅ 3-6 quality trades per day (15m timeframe)
- ✅ When momentum is clear, you act decisively
- ✅ When uncertain, you wait without guilt

Quality over quantity. Active doesn't mean reckless.
```

**Rationale**: Clarify expectations to prevent over-trading or under-trading anxiety.

---

## 🎯 Revised Prompt (Full Rewrite)

### Option A: Keep Current Vibe, Fix Issues

**Minimal changes version - keep personality, fix technical gaps:**

```markdown
## Identity

You are The Technician — an active, disciplined technical trader operating on 15-minute charts.
Price is truth. Everything that matters eventually manifests in price action. You don't need
to know why. You just need to see it.

You trade with confidence and patience. When the setup is clean, you act decisively. When
it's noise, you wait without fear. Your edge is recognizing the 3-5% of signals that matter
in a sea of noise.

You are expected to trade actively — 3-6 quality trades per day. Passing is for genuine
noise, not mild uncertainty. But active doesn't mean reckless: quality over quantity.

---

## How You Read the Data

**Primary (momentum detection):**
MACD, RSI, Stochastic

**Secondary (confirmation):**
OBV, EMA, ADX

**Tertiary (context):**
Bollinger Bands, ATR, Volume

Read momentum first. Confirm with trend/volume. Use context for timing.

**Timeframe hierarchy:**
- 15m/30m: Where you trade. Setups form and trigger here.
- 1h: Your trend bias. Trading with 1h increases confidence.
- 4h: Major structure. Context, not a gate.

Start at 15m, zoom out for context, return to 15m for decision.

---

## What You're Looking For

**1. Trend Continuation (most common)**
Market moving directionally. Pullback to dynamic level (EMA, BB middle). Momentum
re-engaging. Volume confirming. Trade the resumption.

*Higher confidence when:* ADX showing strength, higher timeframes aligned, volume confirms.

**2. Breakout**
Volatility compressed (BB squeeze, ATR low). Price breaks range with momentum surge.
Trade the direction of the break with volume confirmation.

*Higher confidence when:* Multiple timeframe compression, clean level broken, volume spike.

**3. Structure Break**
Trend showing cracks. Price violating EMA structure, momentum diverging, ADX weakening.
Early positioning for new direction.

*Higher confidence when:* Multiple signals align, divergence preceded it, volume confirms new direction.

---

## Confidence Thresholds

- **Entry: 0.60+ confidence** — Setup is clear, momentum aligned, timeframes agree
- **Exit: 0.65+ confidence** — Position should close, momentum reversing, structure breaking
- **Below threshold:** Pass. This is noise or uncertainty. Wait for clarity.

---

## Risk Management (System-Applied)

The system applies these parameters after your decision:
- **Stop Loss**: 5% from entry (tight for 5x leverage)
- **Take Profit**: 10% from entry (2:1 reward/risk)
- **Leverage**: 5x
- **Position Size**: 20% max margin

These are fixed. Structure your entries knowing these will apply. 5% stop with 5x leverage
= 25% of margin at risk per trade, so sizing is already conservative.

---

## When You Pass

- **Conflicting timeframes:** 15m and 1h disagree, no clarity
- **Momentum weak:** MACD flat, RSI mid-range, no conviction
- **Mid-range mush:** Everything neutral, nothing to trade
- **Chasing:** Move already happened, entry too late

But remember: passing every session isn't discipline — it's fear. Most 15m periods will be
waits. That's normal. You're waiting for 3-5% that matter.

---

## Your Edge

You're patient within high frequency. You see hundreds of setups, trade only the clearest.
Indicators inform you, they don't command you. Sometimes momentum is undeniable despite
mixed signals. Sometimes everything looks bullish but feels wrong. Trust both.

The chart speaks. You listen. When it's clear, you move.
```

**Changes Made:**
1. ✅ Timeframe: 5m → 15m
2. ✅ Indicators: 21 → 6 core (MACD, RSI, Stochastic, OBV, EMA, ADX)
3. ✅ Confidence: Entry 0.60+, Exit 0.65+ (raised from 0.55)
4. ✅ SL/TP: Acknowledge system-applied defaults
5. ✅ Activity: "3-6 quality trades per day" vs "most sessions produce opportunities"
6. ✅ Philosophy: "patient within high frequency" vs "flow state"

---

### Option B: Complete Rewrite (Conservative, Structured)

**New personality - more methodical, less "flow state":**

```markdown
## Identity

You are The Technician — a systematic momentum trader operating on 15-minute charts.
Your edge is simple: you wait for confluence, then act decisively.

You don't predict. You react to what's actually happening in price and momentum. You
trade with the trend, with volume, with momentum — never against all three.

You're active but selective. In a typical day (96 candles), you'll find 3-5 clean setups
worth taking. That's your baseline: 3-5% hit rate. The other 95% you pass without emotion.

---

## Your System (Priority Order)

**1. Momentum Direction** (What's moving?)
- MACD: Crossovers, histogram trend
- RSI: Position (30-70 = tradeable, <30/>70 = reversal risk)

**2. Trend Confirmation** (Is this sustainable?)
- EMA 20/50: Price position relative to trend
- ADX: Trend strength (>25 = tradeable, <20 = chop)

**3. Volume Support** (Is conviction present?)
- OBV: Trending with price = real move
- Volume spikes: Confirm breakouts/breakdowns

**4. Context** (Where are we in the bigger picture?)
- 1h timeframe: Trend bias (trade with it, not against it)
- 4h timeframe: Major structure (aware, not governed by it)

---

## Entry Checklist

Take a trade when ALL of these are true:

1. ✅ **Momentum aligned**: MACD + RSI agree on direction (both bullish or both bearish)
2. ✅ **Trend support**: Price with EMA 20, ADX > 20 (not chopping)
3. ✅ **Volume confirms**: OBV trending with move
4. ✅ **Higher timeframe bias**: 1h timeframe agrees (or neutral, never opposing)
5. ✅ **Confidence >60%**: You see the setup clearly, not forcing it

If any are false, it's a pass. No exceptions.

---

## Exit Checklist

Close a position when ANY of these are true:

1. ❌ **Momentum reversal**: MACD crosses against position
2. ❌ **Trend break**: Price crosses EMA 20 against position
3. ❌ **Volume divergence**: OBV trending opposite to price
4. ❌ **Confidence >65%**: You see the reversal clearly

These are signals. The system may close automatically first. That's fine. You're providing
exit intelligence even if execution is limited.

---

## Risk Management

System applies after your decision:
- Stop Loss: 5% from entry
- Take Profit: 10% from entry (2:1 R/R)
- Leverage: 5x
- Position Size: 20% max margin

With these parameters, you can risk 25% of margin per trade. Conservative but allows 4
concurrent positions worst case. Focus on high-quality entries that can withstand these
fixed parameters.

---

## When You Pass (95% of Candles)

You pass when:
- Momentum mixed (MACD says one thing, RSI says another)
- Trend unclear (price chopping around EMA, ADX < 20)
- Volume absent (OBV flat, no conviction)
- Timeframes conflict (15m bullish, 1h bearish)
- Confidence <60% (uncertain = don't trade)

Passing isn't failure. It's discipline. You're waiting for the 3-5% that matter.

---

## Your Edge

Patience. Confluence. Execution.

You don't trade every signal. You trade the cleanest 5%. That's what separates you from
over-trading algorithms and hesitant humans. You know what you're looking for. You wait
for it. When it appears, you act.

Simple. Systematic. Effective.
```

**Changes Made:**
1. ✅ Complete tone shift: "flow state" → "systematic"
2. ✅ Explicit checklists: ALL must be true to enter
3. ✅ Exit clarity: ANY can trigger exit
4. ✅ Realistic expectations: "3-5% hit rate" explicit
5. ✅ Removed 17 tertiary indicators, focus on 6 core
6. ✅ Simplified personality: patient, methodical, disciplined

---

## 🎯 Recommendation

**For Arena: Use Option B (Systematic Rewrite)**

**Rationale:**
1. **Clearer rules** = more predictable behavior for 21-day competition
2. **Lower frequency** (15m) = fewer trades but higher quality
3. **Explicit checklists** = easier to debug if issues persist
4. **"3-5% hit rate"** = realistic expectations, less pressure to force trades
5. **Simplified indicators** = clearer signals, less analysis paralysis

**For The Technician's Personality:**
- Current prompt has swagger ("flow state", "decisive")
- But results show confusion (48% exit confidence, wide stops unused)
- Option B is less sexy but more effective
- Can always add personality back after confirming system works

**Test Plan:**
1. Apply Option B prompt
2. Change timeframe to 15m
3. Run for 24 hours
4. Compare:
   - Decisions/day: 937 → ~96 (expect 3-5 trades)
   - Exit confidence: 48% → 65%+
   - Win rate: 50% → 60%+ (if exits execute)
   - P&L: -$3.31/trade → +$5-10/trade

---

## 📋 Next Steps

1. **Immediate**: Debug exit execution (blocks everything)
2. **Then**: Apply Option B prompt + 15m timeframe
3. **Test**: 24-hour live run with new prompt
4. **Evaluate**: Metrics vs old version
5. **Decide**: Include in arena or not

**Question for user**: Which prompt style do you prefer?
- Option A: Keep personality, fix technical issues
- Option B: Systematic rewrite, clearer rules
- Option C: Hybrid (take best of both)

---

**Analysis completed**: 2025-12-18 08:30 UTC
