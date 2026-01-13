# Bot Performance Analysis Guide

A methodology for analyzing ggbot trading performance to identify what's working, what's failing, and how to improve strategies.

---

## Overview

This guide documents how to analyze a bot's trading history to extract actionable insights. The goal is to move beyond surface metrics (win rate, P&L) to understand *why* a bot wins or loses.

**Key principle**: Look for patterns that predict outcomes, not just describe them. "63% win rate" tells you the result. "Long trades when oversold have 91% win rate" tells you what to do.

---

## Step 1: Baseline Metrics

Start with the fundamentals from `paper_accounts`:

```python
# Basic performance
SELECT
    c.config_name,
    pa.total_trades,
    pa.win_trades,
    pa.loss_trades,
    ROUND((pa.win_trades::numeric / NULLIF(pa.total_trades, 0)) * 100, 2) as win_rate,
    pa.total_pnl,
    pa.current_balance
FROM paper_accounts pa
JOIN configurations c ON pa.config_id = c.config_id
WHERE c.config_id = 'YOUR_CONFIG_ID'
```

**Minimum sample size**: 20+ trades for meaningful patterns. Below this, most analysis is noise.

---

## Step 2: Activity Breakdown

Check what the bot has been doing:

```python
SELECT
    activity_type,
    COUNT(*) as count
FROM activities
WHERE config_id = 'YOUR_CONFIG_ID'
AND created_at > NOW() - INTERVAL '30 days'
GROUP BY activity_type
ORDER BY count DESC
```

Expected types:
- `llm_thought` - Decision reasoning (should match trade count roughly)
- `market_query` - Data fetched before decisions
- `trade_entry` - Position opened
- `trade_exit` - Position closed

**Red flag**: If `llm_thought` count >> `trade_entry` count, the bot is passing on most opportunities. Check if thresholds are too strict.

---

## Step 3: Side Analysis

Compare long vs short performance:

```python
SELECT
    side,
    COUNT(*) as trades,
    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
    ROUND(SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as win_rate,
    SUM(realized_pnl) as total_pnl,
    ROUND(SUM(realized_pnl) / COUNT(*), 2) as avg_pnl_per_trade
FROM paper_trades
WHERE config_id = 'YOUR_CONFIG_ID'
AND status = 'closed'
GROUP BY side
```

**Interpretation**:
- Large disparity may indicate market regime bias (recent bull/bear market), not a fundamental edge
- Check performance by week/month before concluding one direction is "better"

---

## Step 4: Confidence Calibration

Are high-confidence trades actually better?

```python
SELECT
    FLOOR(confidence * 20) * 5 as conf_bucket,  -- 5% buckets
    COUNT(*) as trades,
    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
    ROUND(SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 1) as actual_wr
FROM paper_trades t
JOIN decisions d ON t.decision_id = d.decision_id
WHERE t.config_id = 'YOUR_CONFIG_ID'
AND t.status = 'closed'
GROUP BY conf_bucket
ORDER BY conf_bucket
```

**What to look for**:
- Does win rate increase with confidence? (It should)
- Is confidence clustered at one value? (e.g., 65% for most trades = LLM not differentiating)
- Is high confidence underperforming? (Calibration problem)

**Common issue**: LLM defaults to a "safe" confidence (60-70%) for most trades, making the score meaningless. Fix by giving explicit confidence criteria in the prompt.

---

## Step 5: Close Reason Analysis

How are trades ending?

```python
SELECT
    close_reason,
    COUNT(*) as trades,
    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
    ROUND(SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 1) as win_rate,
    SUM(realized_pnl) as total_pnl
FROM paper_trades
WHERE config_id = 'YOUR_CONFIG_ID'
AND status = 'closed'
GROUP BY close_reason
ORDER BY total_pnl DESC
```

Close reasons:
- `position_management` - LLM decided to exit
- `take_profit` - Hit TP price
- `stop_loss` - Hit SL price
- `liquidation` - Margin call

**Key insight**: If `position_management` has low win rate, the exit logic in the prompt may be flawed. Dig into the exit decision reasoning.

---

## Step 6: Entry Decision Analysis

Extract indicator values from entry reasoning to correlate with outcomes:

```python
SELECT
    t.side,
    t.realized_pnl,
    d.confidence,
    d.reasoning,
    t.opened_at
FROM paper_trades t
JOIN decisions d ON t.decision_id = d.decision_id
WHERE t.config_id = 'YOUR_CONFIG_ID'
AND t.status = 'closed'
ORDER BY t.realized_pnl DESC  -- Winners first
```

**Manual analysis**:
1. Read top 5 winners - what signals were present?
2. Read bottom 5 losers - what was different?
3. Look for patterns: indicator values, sentiment, trend strength

**Common patterns to check**:
- RSI/Stochastic/CCI values at entry
- ADX (trend strength) correlation with outcomes
- Sentiment alignment with trade direction
- Number of confirming indicators

---

## Step 7: Exit Decision Analysis

For bots using LLM exits, analyze exit reasoning:

```python
SELECT
    d.reasoning,
    d.confidence,
    d.created_at
FROM decisions d
WHERE d.config_id = 'YOUR_CONFIG_ID'
AND d.action = 'exit'
ORDER BY d.created_at DESC
LIMIT 20
```

**Categorize exits manually**:
- Thesis complete (target reached)
- Profit taking
- Trend override (exiting because trend continues)
- Risk management
- Other

**Critical finding**: If "trend override" or "oscillators normalizing" exits have poor win rates, the bot may be cutting winners early. The trade working often looks like indicators normalizing.

---

## Step 8: Indicator Value Correlation

Extract specific indicator values from LLM thoughts and correlate with outcomes:

```python
-- Get entry thoughts with outcomes
SELECT
    a.details->>'thought' as thought,
    t.side,
    t.realized_pnl
FROM activities a
JOIN paper_trades t ON a.config_id = t.config_id
    AND a.created_at BETWEEN t.opened_at - INTERVAL '10 minutes' AND t.opened_at + INTERVAL '5 minutes'
WHERE a.config_id = 'YOUR_CONFIG_ID'
AND a.activity_type = 'llm_thought'
AND t.status = 'closed'
```

Then use regex to extract values (RSI, CCI, ADX, etc.) and bucket by outcome.

**Key correlations to check**:

| Indicator | Question |
|-----------|----------|
| RSI | Do extreme values (>70, <30) predict success? |
| CCI | Do true extremes (>150, <-150) outperform moderate? |
| ADX | Is there a threshold where fading fails? |
| Sentiment | Does contrarian alignment improve win rate? |
| Oscillator count | Do more extremes = better outcomes? |

---

## Step 9: Direction Alignment Analysis

For mean-reversion strategies, check if trade direction matches indicator state:

```python
-- Conceptual query - requires parsing reasoning
-- Aligned: long when oversold, short when overbought
-- Misaligned: long when overbought, short when oversold
```

**Expected finding**: Aligned trades significantly outperform misaligned. If not, the strategy may not be mean-reversion or the bot is misinterpreting signals.

---

## Step 10: Time-Based Analysis

Check for regime changes:

```python
SELECT
    DATE_TRUNC('week', opened_at) as week,
    side,
    COUNT(*) as trades,
    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
    ROUND(SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 1) as win_rate,
    SUM(realized_pnl) as pnl
FROM paper_trades
WHERE config_id = 'YOUR_CONFIG_ID'
AND status = 'closed'
GROUP BY week, side
ORDER BY week, side
```

**What to look for**:
- Is performance consistent or driven by specific weeks?
- Did one direction dominate during certain periods?
- Are recent results different from earlier results?

**Warning**: Don't optimize for recent performance if it contradicts earlier data. Markets change.

---

## Common Pitfalls

### 1. Small Sample Size
Don't draw conclusions from <20 trades. Even 44 trades (like our analysis) has limited statistical power for subgroup analysis.

### 2. Survivorship Bias
Exits that reached profit targets had 100% win rate - but that's tautological. The question is whether the exit *logic* is good, not whether profitable exits are profitable.

### 3. No Counterfactual
"Early exits lost money" doesn't mean holding longer would have worked. Those trades might have hit stop loss for bigger losses.

### 4. Market Regime Bias
Long outperforming short may just mean the sample period was bullish. Check week-by-week before concluding.

### 5. Overfitting to Data
If you find "CCI < -147.3 has 100% win rate on Tuesdays" - that's noise, not signal. Patterns should be robust and make logical sense.

---

## What Makes a Good Insight

**Strong insight**:
- Large sample (10+ trades in category)
- Significant difference (>15% win rate difference)
- Logical mechanism (explains *why* it works)
- Consistent over time (not just one week)

**Weak insight**:
- Small sample (3-5 trades)
- Marginal difference (5% win rate difference)
- No clear mechanism
- Driven by single time period

---

## Output: Strategy Improvements

After analysis, improvements should be:

1. **Entry filters**: Block setups that historically fail (e.g., "don't fade ADX >35")
2. **Exit logic fixes**: Address systematic early exits or late exits
3. **Confidence calibration**: Give LLM explicit criteria if confidence is clustered
4. **Data simplification**: Remove indicators that add noise, not signal
5. **Direction alignment**: Enforce correct direction for strategy type

Frame improvements as guidance in the prompt, not hard calculations. The LLM should reason with the guidance, not just compute.

---

## Example Analysis Flow

1. Pull baseline metrics → "63.6% WR, +$1,382 P&L"
2. Check side breakdown → "Longs 70%, Shorts 59% - but check by week"
3. Check confidence → "65% confidence in 66% of trades - not differentiating"
4. Check close reasons → "All position_management - dig into exit reasoning"
5. Categorize exits → "trend_override exits have 43% WR vs 100% for thesis_complete"
6. Check indicator correlations → "ADX >35 has 55% WR, ADX <30 has 68% WR"
7. Check direction alignment → "Long+oversold 92% WR, Long+overbought 20% WR"
8. Synthesize → "Bot cuts winners early, trades against oscillators sometimes, fades strong trends"
9. Propose fixes → "Add ADX hard block, enforce direction alignment, fix exit logic"

---

## Tools

All queries use `core.common.db.get_db_connection()`:

```python
from core.common.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("YOUR QUERY", (params,))
        results = cur.fetchall()
```

For complex analysis with f-strings, use heredoc syntax in bash:

```bash
source .venv/bin/activate && python3 <<'EOF'
from core.common.db import get_db_connection
# Your analysis code here
EOF
```

---

## Related Documentation

- `trading/README.md` - Trading system overview
- `decision/README.md` - Decision engine and prompts
- `ACTIVE.md` - Database schema reference
- `DOCS/DATABASE_CONTEXT.md` - Database design decisions
