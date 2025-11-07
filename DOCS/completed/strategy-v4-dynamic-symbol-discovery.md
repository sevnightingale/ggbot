---
COMPLETED: 2025-11-07
CHANGELOG_ENTRY: ## 2025-11-07 - Strategy v4: Dynamic Symbol Discovery
TODO_SECTION: Agent Strategy Updates
---

# Strategy v4: Dynamic Symbol Discovery

## Overview

Updated the autonomous trading agent strategy from hardcoded 7-pair monitoring to dynamic symbol discovery based on recent ggshot signal activity. This makes the agent adaptive to market conditions and automatically filters symbols based on trading mode (AsterDEX/Symphony/Paper).

## Version History

- **v1**: Initial strategy (7 hardcoded pairs)
- **v2**: Market data flexibility improvements
- **v3**: Position management discretion added
- **v4**: Dynamic symbol discovery (this document)

---

## Changes Made (2025-11-07)

### 1. **Pairs Monitored**

**OLD (v3):**
```
PAIRS MONITORED: BTCUSDT, ETHUSDT, ADAUSDT, AAVEUSDT, APEUSDT, WLDUSDT, SOLUSDT
```

**NEW (v4):**
```
PAIRS MONITORED: Dynamic - determined by recent ggshot signal activity (last 2 days),
filtered to your trading mode (AsterDEX-compatible for live trading)
```

**Impact:**
- Not locked to 7 hardcoded pairs
- Follows where signal activity is happening
- Auto-adapts to AsterDEX/Symphony/Paper mode
- If 15 pairs have signals → agent considers 15
- If 3 pairs → agent considers 3

---

### 2. **Opportunity Identification Workflow**

**OLD (v3):**
```markdown
### OPPORTUNITY IDENTIFICATION (ggshot Foundation)

**Signal Processing:**
1. Query ggshot for all 7 pairs, capturing all available timeframes (5m, 30m, 1h, 4h)
2. Map directional bias across timeframes - higher TF (4h/1h) = macro bias, lower TF (30m/5m) = entry timing
3. Identify alignment: stronger opportunities when multiple TFs align in same direction
4. **CRITICAL:** ggshot signals provide DIRECTION and BIAS, not exact price levels once old
   - **Signal Age <1 day:** Entry zones, SL, TP levels are relevant - use them
   - **Signal Age >1 day:** Direction/trend remains valid, but price levels are STALE - calculate fresh levels from current price
```

**NEW (v4):**
```markdown
### OPPORTUNITY IDENTIFICATION (Dynamic Symbol Discovery)

**Step 1: Discover Active Symbols (each cycle)**
```
query_market_data({
    "categories": {"trading_signals": ["ggshot"]},
    "scan_days": 2
})
```
This returns symbols with recent ggshot signals, automatically filtered to your trading mode (Aster/Symphony/Paper).

**Step 2: Query Full Signal History (for active symbols only)**
For each symbol from Step 1, query all timeframes:
```
query_market_data({
    "symbol": "BTCUSDT",
    "categories": {"trading_signals": ["ggshot"]}
})
```

**Signal Processing:**
1. Map directional bias across timeframes - higher TF (4h/1h) = macro bias, lower TF (30m/5m) = entry timing
2. Identify alignment: stronger opportunities when multiple TFs align in same direction
3. **CRITICAL:** ggshot signals provide DIRECTION and BIAS, not exact price levels once old
   - **Signal Age <1 day:** Entry zones, SL, TP levels are relevant - use them
   - **Signal Age >1 day:** Direction/trend remains valid, but price levels are STALE - calculate fresh levels from current price

**Benefits of Dynamic Discovery:**
- Not locked to 7 hardcoded pairs
- Follows where signal activity is happening
- Adapts to market conditions automatically
- Only queries symbols with recent activity (efficient)
```

---

### 3. **Per-Cycle Process**

**OLD (v3):**
```markdown
**Per-Cycle Process:**
1. Query ggshot for all 7 pairs
2. For each pair with active signal: Review core technicals (RSI, OBV, VWAP)
3. Query additional market data if needed for conviction/context
4. Close positions that hit TP or SL (mandatory)
5. Identify 1-2 best opportunities for entry
6. **CALCULATE FRESH SL/TP FROM CURRENT PRICE** (critical for old signals)
7. **VALIDATE R/R >= 1:1 before entering**
8. Execute if conviction + R/R threshold met
9. Record observation after closing each trade
10. Use wait_for tool to pause before next cycle
```

**NEW (v4):**
```markdown
**Per-Cycle Process:**
1. **Discover active symbols** - Scan ggshot for symbols with signals from last 2 days (auto-filtered to your trading mode)
2. **Query full signal history** - For active symbols only, get all timeframes and signal details
3. For each symbol with signals: Review core technicals (RSI, OBV, VWAP)
4. Query additional market data if needed for conviction/context
5. Close positions that hit TP or SL (mandatory)
6. Identify 1-2 best opportunities for entry
7. **CALCULATE FRESH SL/TP FROM CURRENT PRICE** (critical for old signals)
8. **VALIDATE R/R >= 1:1 before entering**
9. Execute if conviction + R/R threshold met
10. Record observation after closing each trade
11. Use wait_for tool to pause before next cycle
```

---

### 4. **Other Strategy Changes (Non-Dynamic Discovery)**

These changes were also made during the v3 → v4 transition:

#### Leverage Range
- **OLD**: 7-17x
- **NEW**: 5-20x
- **Reason**: More flexibility for varying conviction levels

#### Check Frequency (Searching)
- **OLD**: 15-30 minutes
- **NEW**: 15-60 minutes
- **Reason**: Wider range for market-adaptive timing

#### Check Frequency (Holding Positions)
- **OLD**: 30-60 minutes
- **NEW**: 5-30 minutes
- **Reason**: More attentive monitoring when positions are open

#### Position Management
- **ADDED**: "Full discretion to close anytime - TP/SL are guidelines, not handcuffs"
- **Reason**: Agent can close early if sees reversal risk or wants to lock profits

#### Market Data Usage
- **UPDATED**: References MCP tool system dynamically instead of hardcoded list
- **Reason**: Evergreen as tools evolve

#### SL/TP Calculation
- **EMPHASIZED**: Always calculate from CURRENT PRICE, not stale ggshot levels
- **Reason**: Critical bug fix - agent was sometimes using old signal levels

---

## Technical Implementation

### MCP Tool Enhancement: `query_market_data` Scan Mode

**Tool**: `/home/sev/ggbot/agent/mcp_server.py`

Added scan mode to `query_market_data` tool:

```python
# NEW: Scan mode - omit symbol parameter
{
    "categories": {"trading_signals": ["ggshot"]},
    "scan_days": 2
}
```

**What it does:**
1. Queries database for ggshot signals from last N days
2. Reads agent's trading mode from `config_data->trading_mode`
3. Filters symbols based on trading mode:
   - `aster` → Only AsterDEX-compatible symbols
   - `symphony` → Only Symphony-compatible symbols
   - `paper` → All symbols
4. Returns list of active symbols with signal counts and timestamps

**Implementation details:**
- Uses `UniversalSymbolStandardizer.is_aster_compatible()` for filtering
- Queries `market_data` table with `data_source='trading_signals'`
- Filters on `data_points->'ggshot_signal'->>'direction' IS NOT NULL`
- Groups by symbol, counts signals, returns most recent first

---

## Testing Results

**Test Date**: 2025-11-07 11:18

**Scan Results (2 days):**
- Total symbols with signals: 4 (BTC/USDT, KNC/USDT, LQTY/USDT, RVN/USDT)
- Aster-compatible: 1 (BTC/USDT only)
- Agent behavior: Correctly queried only BTC/USDT

**Scan Results (7 days):**
- Total symbols with signals: 24
- Aster-compatible: 2 (BTC/USDT, SEI/USDT)

**Agent Execution:**
1. ✅ Scanned for active symbols
2. ✅ Discovered BTC/USDT (Aster-compatible)
3. ✅ Queried full ggshot history for BTC/USDT
4. ✅ Built conviction with RSI/OBV/VWAP across multiple timeframes
5. ✅ Correctly identified fresh (5m) vs stale (1h, 4h, 30m) signals
6. ✅ Calculated SL/TP from CURRENT PRICE ($100,165), not stale levels
7. ✅ Validated R/R: 1.10:1 (PASS)
8. ✅ Executed trade successfully (Batch ID: 7513193159)

---

## Files Modified

1. **Agent Strategy** (`configurations.config_data->agent_strategy`):
   - Updated via `/home/sev/ggbot/core/common/db.py`
   - Version: 3 → 4
   - Timestamp: 2025-11-07

2. **MCP Tool** (`/home/sev/ggbot/agent/mcp_server.py`):
   - Lines 84-115: Updated tool description to document scan mode
   - Lines 170-236: Added scan mode implementation
   - Lines 182-194: Reads trading mode from config_data
   - Lines 203-221: Filters symbols based on trading mode

3. **Logging** (`/home/sev/ggbot/agent/run_agent.py`):
   - Lines 219-234: Added logging to capture full MCP tool descriptions on startup
   - **Note**: Not yet tested in production

---

## Rollback Instructions

If you need to revert to v3 (hardcoded 7 pairs):

### Option 1: Database Update (Quick)

```python
from core.common.db import get_db_connection
import json

config_id = 'bb2560fd-b053-464f-8a58-8e254e4d36fa'

# Use the OLD strategy content from below
old_strategy_content = """...[see "Old Strategy (v3)" section below]..."""

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT config_data FROM configurations WHERE config_id = %s
        """, (config_id,))

        config_data = cur.fetchone()[0]
        config_data['agent_strategy']['content'] = old_strategy_content
        config_data['agent_strategy']['version'] = 3

        cur.execute("""
            UPDATE configurations
            SET config_data = %s
            WHERE config_id = %s
        """, (json.dumps(config_data), config_id))

        conn.commit()
```

### Option 2: Disable Scan Mode (Keep Tool, Revert Strategy)

Just update the strategy to explicitly list 7 pairs without changing the MCP tool code. The scan mode will remain available but unused.

---

## Old Strategy (v3) - Complete Text

```markdown
## AUTONOMOUS TRADING STRATEGY: Multi-Pair Opportunity-Based Trading

**PAIRS MONITORED:** BTCUSDT, ETHUSDT, ADAUSDT, AAVEUSDT, APEUSDT, WLDUSDT, SOLUSDT

**CORE PHILOSOPHY:**
Use ggshot signals as opportunity scanners to identify directional bias across multiple timeframes. Layer in technical analysis and market intelligence to build conviction. Trade actively with proper risk management, and learn from every outcome.

---

### MARKET DATA & INTELLIGENCE

**Dynamic Market Data Access:**

You have access to market data through the `query_market_data` MCP tool. On startup, you received the complete tool description including all available categories and data points.

**Core Foundation (use by default):**
- **RSI** - Divergences, overextensions, multi-TF trend
- **OBV** (Volume) - Accumulation/distribution, flow analysis
- **VWAP** - Dynamic support/resistance, standard deviations

**Dynamic Intelligence Layer:**
- **Don't limit yourself to RSI/OBV/VWAP** - these are foundational, not exclusive
- **Check your MCP tool descriptions** - you have access to 7 categories of market data (technical analysis, macro economics, sentiment/social, derivatives/leverage, on-chain analytics, news/regulatory, trading signals)
- **Query any data point freely** when it adds conviction, context, confirmation, or invalidation
- **Examples of when to query additional data:**
  - Building conviction on a new setup
  - Validating divergences or breakouts
  - Checking macro/sentiment context before large positions
  - Understanding current volatility regime
  - Seeking confirmation or invalidation of a thesis

**Philosophy:** Use market data dynamically as a professional trader would. The tool system is your toolkit - use whatever helps you make better decisions.

---

### OPPORTUNITY IDENTIFICATION (ggshot Foundation)

**Signal Processing:**
1. Query ggshot for all 7 pairs, capturing all available timeframes (5m, 30m, 1h, 4h)
2. Map directional bias across timeframes - higher TF (4h/1h) = macro bias, lower TF (30m/5m) = entry timing
3. Identify alignment: stronger opportunities when multiple TFs align in same direction
4. **CRITICAL:** ggshot signals provide DIRECTION and BIAS, not exact price levels once old
   - **Signal Age <1 day:** Entry zones, SL, TP levels are relevant - use them
   - **Signal Age >1 day:** Direction/trend remains valid, but price levels are STALE - calculate fresh levels from current price

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

**Leverage Range:** 5-20x (scales with conviction and volatility)
- **High Conviction:** 15-20x leverage
- **Medium Conviction:** 10-15x leverage
- **Lower Conviction:** 5-10x leverage

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
Entry: $100,000 (CURRENT PRICE)
SL: $98,000 (2% away from CURRENT PRICE)
TP: $104,000 (4% away from CURRENT PRICE - gives 2:1 R/R)

Position size = $30 / 0.02 = $1,500 notional
Leverage: 10x
Margin required: $150
```

**Stop Loss & Take Profit - CALCULATE FROM CURRENT PRICE:**
- **CRITICAL RULE:** Always calculate SL and TP based on CURRENT MARKET PRICE, not outdated ggshot levels
- **For Fresh Signals (<1 day old):**
  - Use ggshot provided SL and TP as baseline
  - Verify they make sense relative to current price
  - Adjust if price has moved significantly since signal generated
- **For Old Signals (>1 day old):**
  - **IGNORE ggshot price levels completely** - they're stale
  - Use ggshot DIRECTION only (LONG/SHORT bias)
  - Calculate fresh SL/TP from CURRENT PRICE:
    - **SL:** 1.5-3% away from current price (based on volatility and conviction)
    - **TP:** Ensure R/R >= 1:1, preferably 1.5:1+
    - Use technical levels (support/resistance, VWAP, recent highs/lows) for placement
- **SL is MANDATORY** - never enter without defined SL

---

### CONVICTION BUILDING (Technical Layer)

**Core Technical Analysis:**
- **RSI Analysis:** Divergences (high signal on 4h/1h), overextensions (>80 or <20), multi-TF confirmation
- **Volume Confirmation:** OBV trending with price, volume spikes, accumulation/distribution phases
- **Price Action:** VWAP as dynamic level, support/resistance, previous ggshot targets as structural levels

**Dynamic Market Intelligence (query as needed):**
- Reference your MCP tool descriptions for available data points across 7 categories
- Query any data point that adds conviction, confirmation, or context
- Use market data as a professional trader would - dynamically and intelligently

---

### POSITION ENTRY RULES

**Pre-Entry Checklist:**
1. ggshot signal identified on pair + TF bias established (direction, not necessarily price levels)
2. Build conviction using core technicals (RSI, OBV, VWAP) + any additional market data queries
3. **CALCULATE SL/TP FROM CURRENT PRICE** (not old ggshot levels if signal >1 day old)
4. **VALIDATE R/R >= 1:1** (this is NON-NEGOTIABLE)
5. Calculate position size based on risk formula using CURRENT PRICE
6. Confirm leverage is 5-20x range
7. Time entry using lower TF RSI (wait for cooldown if overextended)

**Entry Execution:**
- Use ggshot entry zone as reference ONLY if signal is fresh (<1 day)
- For older signals: Use DIRECTION (LONG/SHORT) but calculate fresh levels from CURRENT PRICE
- All-in on conviction (no scale-in for live trading)

---

### MONITORING & EXECUTION CYCLE

**Check Frequency & Wait Times:**
- **When searching for opportunities (no open positions):** Check every 15-60 minutes
  - 15-20 min during high volatility or strong signals developing
  - 30-60 min during low volatility or ranging markets
- **When holding positions (1+ open trades):** Check every 5-30 minutes
  - 5-15 min if position near TP/SL or high volatility
  - 20-30 min if position stable and within expected range
- **Market-adaptive timing:** High volatility = more frequent, low volatility = less frequent

**Per-Cycle Process:**
1. Query ggshot for all 7 pairs
2. For each pair with active signal: Review core technicals (RSI, OBV, VWAP)
3. Query additional market data if needed for conviction/context
4. Close positions that hit TP or SL (mandatory)
5. Identify 1-2 best opportunities for entry
6. **CALCULATE FRESH SL/TP FROM CURRENT PRICE** (critical for old signals)
7. **VALIDATE R/R >= 1:1 before entering**
8. Execute if conviction + R/R threshold met
9. Record observation after closing each trade
10. Use wait_for tool to pause before next cycle

**Position Management:**
- **Full discretion to close anytime** - TP/SL are guidelines, not handcuffs
- Close early if you see reversal risk, want to lock profits, or conviction changes
- Can adjust SL to breakeven once in 50%+ profit
- Trust your analysis - if something changes, act on it
- Predetermined TP/SL are targets, but market conditions evolve

---

### EXECUTION GUIDELINES

**DO:**
- Calculate SL/TP from CURRENT PRICE, not stale ggshot levels
- ALWAYS validate R/R >= 1:1 before entering
- Query market data dynamically to build conviction
- Use 5-20x leverage range
- Risk 5-30% of balance per trade
- Calculate position size using risk formula with CURRENT PRICE
- Close positions at defined levels without emotion
- Use wait_for tool between cycles (adapt frequency to market conditions)

**DON'T:**
- Use old ggshot price levels (>1 day) for SL/TP calculation
- Enter trades with R/R < 1:1 (NEVER)
- Use leverage below 5x or above 20x
- Risk more than 30% of balance in one trade
- Override SL or TP casually
- Exceed 3-5 open positions
- Trade without ggshot directional bias

**ADAPTABILITY:**
- If R/R validation keeps blocking trades → look for better entry timing or calculate fresh levels
- If stops getting hit frequently → tighten entries, wait for better confirmations
- If targets consistently hit → increase position sizes on similar setups
- Query additional market data when uncertain or seeking confirmation
- Evolution = core strategy feature, not deviation

---

### KEY SUCCESS FACTORS

1. **Calculate SL/TP from CURRENT PRICE** - old ggshot levels are stale guidance only
2. **R/R validation is NON-NEGOTIABLE** - never enter with R/R < 1:1
3. **Position sizing via risk formula** - always use CURRENT PRICE in calculations
4. **5-20x leverage range** - matches market volatility and conviction
5. **Dynamic market data usage** - reference MCP tool descriptions, query freely
6. **ggshot signals guide DIRECTION** - but YOU calculate fresh price levels
7. **Active trading beats waiting** - but only on quality setups
8. **Every trade teaches something** - record and learn

---

### STRATEGY SETTINGS

- **Autonomously Editable:** TRUE (learns and evolves)
- **Max Concurrent Positions:** 3-5
- **Risk Per Trade:** 5-30% of account balance (adjusted for conviction)
- **Leverage Range:** 5-20x (scales with conviction)
- **Minimum R/R:** 1:1 (validated before every trade)
- **Primary Timeframes:** 4h/1h (bias), 30m/5m (execution)
- **Check Frequency:** 15-60 min when searching, 5-30 min when holding
- **Position Duration:** Variable (target-based exits)
```

---

## Performance Expectations

**Before (v3 - Hardcoded 7 Pairs):**
- Always queries all 7 pairs regardless of activity
- May spend time analyzing stale signals
- Limited to predefined symbol set

**After (v4 - Dynamic Discovery):**
- Only queries symbols with recent activity
- Focuses analysis on hot symbols
- Can trade any Aster-compatible symbol with signals
- More efficient token usage
- Better adapts to market conditions

---

## Notes

- The scan mode defaults to 2 days, but this can be adjusted via `scan_days` parameter
- Symbol compatibility is determined by `UniversalSymbolStandardizer` (142 symbols in registry, 33 Aster-compatible as of 2025-11-07)
- The MCP tool automatically handles trading mode detection without agent needing to specify
- Scan mode returns symbols sorted by most recent signal first

---

## Related Files

- Strategy stored in: `configurations.config_data->agent_strategy` (PostgreSQL JSONB)
- MCP tool implementation: `/home/sev/ggbot/agent/mcp_server.py`
- Symbol standardizer: `/home/sev/ggbot/core/symbols/standardizer.py`
- Symbol registry: `/home/sev/ggbot/core/symbols/registry.py`
- Agent runner: `/home/sev/ggbot/agent/run_agent.py`

---

## Future Improvements

Potential enhancements for v5:

1. **Configurable scan window**: Allow agent to dynamically adjust `scan_days` based on market volatility
2. **Multi-mode support**: Support trading on both Aster + Symphony simultaneously
3. **Symbol quality scoring**: Rank symbols by signal freshness, count, and conviction
4. **Historical performance**: Weight symbols by past trading success
5. **Cross-exchange opportunities**: Expand beyond single trading mode

---

## Conclusion

Strategy v4 represents a significant evolution from hardcoded symbol lists to intelligent, market-driven symbol discovery. The agent now automatically adapts to where signals are happening while respecting trading mode constraints. Initial testing shows the system working as intended, with proper symbol filtering and efficient query patterns.
