# Prompt System Architecture - Complete Analysis

**Created**: 2024-12-14
**Purpose**: Comprehensive documentation of ggbots prompt generation, trade settings integration, and position management flows
**Status**: Analysis complete, ready for review and potential system improvements

---

## Table of Contents

1. [Overview](#overview)
2. [Output Format Instructions](#output-format-instructions)
3. [Trade Settings Integration](#trade-settings-integration)
4. [Position Management Mode](#position-management-mode)
5. [Complete Flow Diagrams](#complete-flow-diagrams)
6. [Key Design Insights](#key-design-insights)
7. [Potential Improvements](#potential-improvements)

---

## Overview

The ggbots prompt system uses a **three-template architecture** that routes based on execution context:

```
decision/engine_v2.py routing:
├─ NEW TRADE → opportunity_analysis.py (no active position)
├─ EXISTING POSITION → position_management.py (has active position)
└─ EXTERNAL SIGNAL → signal_validation.py (signal_data present)
```

**Key Characteristics**:
- **Single-message prompts**: Complete prompt sent as one string (not system+user split)
- **Context-driven routing**: Position state determines template selection
- **Clean separation**: LLM handles strategy, system handles risk management
- **Token optimization**: SUMMARY + CRITICAL FIELDS pattern (93% reduction: 67k → 5k tokens)

---

## Output Format Instructions

### Exact Format Requirements

The LLM receives these **exact output format instructions** at the end of every prompt:

#### Opportunity Analysis (New Trades)
```markdown
## OUTPUT FORMAT
ACTION: [long/short/wait]
CONFIDENCE: [0.000-1.000]
REASONING: [Explain how your strategy interprets the current market data and identifies this opportunity]
STOP_LOSS: [price or null]
TAKE_PROFIT: [price or null]
```

#### Position Management (Existing Positions)
```markdown
## OUTPUT FORMAT
ACTION: [close/wait]
CONFIDENCE: [0.000-1.000]
REASONING: [Explain how your strategy interprets current market data in relation to your existing position and performance]
STOP_LOSS: [price or null]
TAKE_PROFIT: [price or null]
```

### Parsing Implementation

**Location**: `decision/engine_v2.py::_parse_llm_response`

**Approach**: Flexible text-based parsing (NOT strict JSON schema)

```python
for line in response.split('\n'):
    if 'ACTION:' in line:
        action = extract_action(line)  # Standardizes: buy→long, sell→short
    elif 'CONFIDENCE:' in line:
        confidence = extract_float(line)  # Handles "0.75" or "75%"
    elif 'STOP_LOSS:' in line:
        stop_loss = extract_price(line)  # Handles null/none/price
    elif 'TAKE_PROFIT:' in line:
        take_profit = extract_price(line)
```

**Design Rationale**: Text parsing is more robust than strict JSON validation - handles LLM variations gracefully.

---

## Trade Settings Integration

### What the LLM Controls

The LLM only decides 5 fields:
1. **ACTION**: `long` | `short` | `wait` | `close`
2. **CONFIDENCE**: `0.000-1.000` (used for position sizing)
3. **REASONING**: Text explanation
4. **STOP_LOSS**: Optional price (can return `null`)
5. **TAKE_PROFIT**: Optional price (can return `null`)

### What the System Controls (Hidden from LLM)

All trade settings are applied **after** LLM decision by the trading service:

#### 1. Leverage (`config.trading.leverage`)

**Config Location**:
```json
{
  "trading": {
    "leverage": 10  // 1x to 100x
  }
}
```

**Usage**: Applied during position sizing calculation
```python
# trading/paper/supabase_service.py:334
leverage = config.trading.leverage  # e.g., 10x
margin_required = position_size_usd / leverage
```

**Not shown to LLM**: LLM has zero awareness of leverage settings.

#### 2. Position Sizing (`config.trading.position_sizing`)

**Three Methods Available**:

```python
class PositionSizingMethod(Enum):
    FIXED_USD = "fixed_usd"                    # Always trade $X
    ACCOUNT_PERCENTAGE = "account_percentage"  # Always trade Y% of balance
    CONFIDENCE_BASED = "confidence_based"      # Scale by LLM confidence
```

**Default: `confidence_based`** (most common)

**Confidence-Based Formula** (`core/config/models.py:248-256`):
```python
max_pct = (config.max_position_percent or 10.0) / 100.0  # Default: 10%
margin = confidence × max_pct × balance
position_size_usd = margin × leverage

# Example: confidence=0.75, balance=$10,000, max=10%, leverage=10x
margin = 0.75 × 0.10 × 10000 = $750
position_size_usd = 750 × 10 = $7,500 notional
```

**Config Structure**:
```json
{
  "trading": {
    "position_sizing": {
      "method": "confidence_based",
      "max_position_percent": 10.0,  // Max margin at confidence=1.0
      "fixed_amount_usd": 100.0,     // For fixed_usd method
      "account_percent": 5.0         // For account_percentage method
    },
    "leverage": 10
  }
}
```

**Safety Caps**:
- Minimum position: `$10`
- Maximum margin: `95% of balance` (5% buffer for fees)

#### 3. Stop Loss & Take Profit Defaults

**Two-Tier System**: LLM suggestion → Config defaults

**Implementation** (`trading/paper/supabase_service.py:174-187`):
```python
# Step 1: LLM suggests prices (or returns null)
llm_stop_loss = intent.get("stop_loss_price")
llm_take_profit = intent.get("take_profit_price")

# Step 2: Apply defaults if LLM didn't provide
if not llm_stop_loss and config.trading.risk_management.default_stop_loss_percent:
    default_stop = config.get_default_stop_loss_price(entry_price, side)
    intent["stop_loss_price"] = default_stop  # Apply fallback

if not llm_take_profit and config.trading.risk_management.default_take_profit_percent:
    default_tp = config.get_default_take_profit_price(entry_price, side)
    intent["take_profit_price"] = default_tp  # Apply fallback
```

**Default Calculation Logic** (`core/config/models.py:269-300`):
```python
# Config settings (defaults):
default_stop_loss_percent = 3.0   # 3%
default_take_profit_percent = 6.0  # 6%

# For LONG positions:
stop_loss_price = entry_price × (1 - stop_loss_pct/100)
take_profit_price = entry_price × (1 + take_profit_pct/100)

# For SHORT positions:
stop_loss_price = entry_price × (1 + stop_loss_pct/100)  # Reversed
take_profit_price = entry_price × (1 - take_profit_pct/100)

# Example: LONG BTC at $100,000 with 3% SL, 6% TP
# SL = 100,000 × (1 - 0.03) = $97,000
# TP = 100,000 × (1 + 0.06) = $106,000
```

**Config Structure**:
```json
{
  "trading": {
    "risk_management": {
      "default_stop_loss_percent": 3.0,
      "default_take_profit_percent": 6.0,
      "max_positions": 5,
      "max_daily_loss_usd": null
    }
  }
}
```

### Complete LLM Decision → Trade Execution Flow

```
1. LLM receives prompt (NO leverage/sizing mentioned)
   ↓
2. LLM outputs:
   ACTION: long
   CONFIDENCE: 0.75
   STOP_LOSS: 97500  ← LLM calculated this
   TAKE_PROFIT: null  ← LLM didn't provide

3. System applies trade settings:

   a) Position sizing (confidence-based):
      margin = 0.75 × 0.10 × $10,000 = $750
      leverage = 10x (from config.trading.leverage)
      position_size = $750 × 10 = $7,500

   b) Stop loss (LLM provided):
      stop_loss = $97,500  ✓ Use LLM's value

   c) Take profit (LLM didn't provide):
      default_tp_pct = 6.0% (from config)
      entry_price = $100,000
      take_profit = $100,000 × (1 + 0.06) = $106,000  ✓ Apply default

4. Execute trade with final parameters:
   - Symbol: BTC/USDT
   - Side: LONG
   - Entry: $100,000
   - Size: $7,500 (0.075 BTC)
   - Margin: $750
   - Leverage: 10x
   - SL: $97,500 (LLM suggested)
   - TP: $106,000 (system default)
```

### Design Rationale: Clean Separation of Concerns

**LLM's Job**: Trading strategy execution (when to enter, direction, confidence)
**System's Job**: Risk management (how much, leverage, default protections)

**Benefits**:
- LLM doesn't need to understand position sizing math
- Users configure risk settings once (not per strategy)
- Consistent risk management across all strategies
- Confidence score naturally scales position size
- Sophisticated strategies can suggest precise SL/TP
- Simple strategies can delegate to system defaults

---

## Position Management Mode

### Routing Logic: When Does It Trigger?

**Decision Point** (`decision/engine_v2.py:279-293`):

```python
# Every scheduled run checks for active positions FIRST
active_position = await self._get_active_position(trading_symbol, config_id)

if active_position:
    # POSITION MANAGEMENT MODE
    return await self._handle_position_management(trading_symbol, active_position)
else:
    # OPPORTUNITY ANALYSIS MODE
    return await self._handle_opportunity_analysis(trading_symbol)
```

**Key Insight**: Position-first approach prevents opening duplicate positions and ensures existing positions are managed.

### What Changes in Position Management Mode

#### 1. Different Prompt Template

**Uses**: `decision/prompts/position_management.py`
**Instead of**: `opportunity_analysis.py`

**Key Differences**:
- ❌ **Removed sections**: ggShot signals, market intelligence
- ✅ **Added section**: `CURRENT POSITION STATUS` (performance data)
- 🔄 **Output format**: `ACTION: [close/wait]` instead of `[long/short/wait]`
- 📉 **Token reduction**: ~4,000 tokens vs ~6,000 tokens (33% smaller)

#### 2. Position Data Fetching (Trading Mode-Aware)

**Paper Trading** (Database only):
```sql
SELECT
    pt.trade_id,
    pt.symbol,
    pt.side,              -- 'buy' or 'sell'
    pt.entry_price,       -- Entry price
    pt.current_price,     -- Last updated price
    pt.size_usd,          -- Position size
    pt.unrealized_pnl,    -- Current P&L
    pt.opened_at,         -- Entry timestamp
    pt.stop_loss,         -- SL price
    pt.take_profit,       -- TP price
    pt.confidence_score,  -- Original confidence
    d.reasoning as entry_reasoning,     -- Original decision reasoning
    d.confidence as entry_confidence,   -- Original confidence
    d.decision_data as entry_decision_data  -- Full original decision JSON
FROM paper_trades pt
LEFT JOIN decisions d ON pt.decision_id = d.decision_id
WHERE pt.config_id = ? AND pt.symbol = ? AND pt.status = 'open'
```

**Symphony/Aster (Live Trading)** (API + Database hybrid):
```python
# Step 1: Query database for batch_id + original decision context
SELECT batch_id, decision_id, entry_reasoning, entry_confidence
FROM live_trades
WHERE config_id = ? AND closed_at IS NULL

# Step 2: Fetch REAL position data from exchange API
live_positions = await symphony_service.get_open_positions(config_id)

# Step 3: Match batch_id and enrich with decision context
matching_position = find_position_by_batch_id(live_positions, batch_id)
matching_position['entry_reasoning'] = db_row['entry_reasoning']
matching_position['entry_confidence'] = db_row['entry_confidence']
```

**Critical Difference**: Live trading uses **real-time exchange API data** (current price, unrealized P&L) instead of database cache.

#### 3. Position Data Formatting for LLM

**Location**: `decision/engine_v2.py::_format_position_data_for_llm` (lines 655-717)

**Step 1: Calculate Performance Metrics**

```python
# P&L Percentage (direction-aware)
if side == 'long':
    pnl_percentage = ((current_price - entry_price) / entry_price) × 100
else:  # short
    pnl_percentage = ((entry_price - current_price) / entry_price) × 100

# Duration
hours_held = (now - opened_at).total_seconds() / 3600

# Performance Classification (5 categories)
if pnl_percentage > 5:      → "Strong Winner"
elif pnl_percentage > 1:    → "Winning"
elif pnl_percentage > -1:   → "Break-even"
elif pnl_percentage > -5:   → "Losing"
else:                       → "Strong Loser"
```

**Step 2: Format Position Summary** (exact text sent to LLM):

```markdown
CURRENT POSITION DETAILS:
Position Type: LONG BTC/USDT
Entry Price: $95,000.00
Current Price: $98,234.56
Position Size: $7,500.00
Unrealized P&L: $+243.26 (+3.4%)
Performance: Winning
Duration: 12.5 hours

ORIGINAL TRADE CONTEXT:
Entry Reasoning: RSI showing oversold conditions on 1h (28.5) with bullish divergence forming. Volume confirmation strong at 1.25x average. Entry aligned with user's mean reversion strategy.
Entry Confidence: 75.0%
Stop Loss: $92,500.00
Take Profit: $100,000.00
```

**Key Design Choice**: LLM sees **why it entered originally** + **current performance** = strategy continuity.

### Complete Position Management Prompt Structure

```markdown
You are an expert cryptocurrency trader managing an existing position...

## CURRENT POSITION STATUS
{Position data formatted above - 14 lines}

## MARKET DATA ANALYSIS
{SAME as opportunity analysis - multi-timeframe indicators}

## VOLUME CONFIRMATION ANALYSIS
{SAME as opportunity analysis}

## YOUR TRADING STRATEGY
{SAME user_strategy from config.decision.user_prompt}

## TASK INSTRUCTIONS
You strictly apply the user's trading strategy below...
Consider:
- How has the market evolved since your entry?
- Does your current position still align with your trading strategy?
- Should you close the position or wait based on current conditions?
- Are there any adjustments needed to stop loss or take profit levels?

## OUTPUT FORMAT
ACTION: [close/wait]  ← Different from opportunity analysis
CONFIDENCE: [0.000-1.000]
REASONING: [Explain...]
STOP_LOSS: [price or null]
TAKE_PROFIT: [price or null]
```

### Side-by-Side Comparison

| **Aspect** | **Opportunity Analysis** | **Position Management** |
|------------|-------------------------|------------------------|
| **Trigger** | No active position | Active position exists |
| **Template** | `opportunity_analysis.py` | `position_management.py` |
| **Action Options** | `long` \| `short` \| `wait` | `close` \| `wait` |
| **Position Context** | ❌ None | ✅ Performance, entry reasoning, duration |
| **ggShot Signals** | ✅ Included (if available) | ❌ Removed |
| **Market Intelligence** | ✅ Included (if available) | ❌ Removed |
| **Data Source (Paper)** | Database only | Database only |
| **Data Source (Live)** | Database only | **API + Database hybrid** |
| **Token Count** | ~6,000 tokens | ~4,000 tokens (33% reduction) |
| **Focus** | "Should I enter?" | "Should I exit?" |

---

## Complete Flow Diagrams

### Opportunity Analysis Flow (New Trades)

```
User Creates Bot Config
  ↓
Config stored in DB (configurations table)
  ↓ config_data JSONB contains:
    - decision.user_prompt (user's strategy)
    - extraction.selected_data_sources (indicators/timeframes)
    - llm_config (provider, model, reasoning_tier)
  ↓
Scheduled/Manual Trigger
  ↓
Orchestrator (ggbot.py::run_autonomous_cycle)
  ↓
Extraction Phase (extraction/v2/extraction_engine.py)
  - Fetches market data from exchanges (WebSocket cache)
  - Runs 21 preprocessors (RSI, MACD, BBands...) × 7 timeframes
  - Queries ggShot signals (if enabled + user has permission)
  - Queries market intelligence (funding rates, VIX...)
  - Stores in market_data table
  ↓
Decision Phase (decision/engine_v2.py::make_decision)
  ↓
Check for active position:
  active_position = await _get_active_position(symbol, config_id)
  ↓
No position found → Route to _handle_opportunity_analysis()
  ↓
Fetch fresh market data from database (7 timeframes)
  ↓
Format market data for LLM:
  - _format_market_data_for_llm() → SUMMARY + CRITICAL FIELDS
  - _get_volume_confirmation() → Volume ratio analysis
  - _format_ggshot_signals_for_llm() → Directional bias (optional)
  - _format_market_intelligence_for_llm() → Macro/derivatives (optional)
  ↓
Build opportunity analysis prompt:
  - Current price: $98,234.56
  - Market data: Multi-timeframe indicators
  - Volume analysis: 1.25x average
  - ggShot signals: 2 LONG vs 1 SHORT (optional)
  - Market intelligence: Funding neutral, VIX low (optional)
  - User strategy: config.decision.user_prompt
  - Output format: ACTION/CONFIDENCE/REASONING/SL/TP
  ↓
Call LLM (decision/llm_providers.py)
  - Single-message prompt (not system+user split)
  - Temperature: 0.7
  - Reasoning tier: economy/standard/premium
  ↓
Parse LLM Response (_parse_llm_response)
  - Extract ACTION, CONFIDENCE, REASONING
  - Extract STOP_LOSS, TAKE_PROFIT
  - Standardize actions (buy→long, sell→short)
  ↓
decision_result = {
  action: 'long',
  confidence: 0.75,
  reasoning: "RSI oversold...",
  stop_loss_price: 97500,
  take_profit_price: null
}
  ↓
Trading Phase (ggbot.py::_run_trading_v2)
  ↓
Route based on trading_mode:
  - paper → trading/paper/supabase_service.py
  - symphony → trading/live/symphony_service.py
  - aster → trading/live/aster_service_v3.py
  ↓
Apply trade settings (trading service):
  - Position sizing: confidence × max_pct × balance × leverage
  - Apply default SL if LLM didn't provide
  - Apply default TP if LLM didn't provide
  - Validate position limits (max_positions)
  ↓
Execute trade:
  - Symbol: BTC/USDT
  - Side: LONG
  - Entry: $100,000
  - Size: $7,500 (0.075 BTC)
  - Margin: $750
  - Leverage: 10x
  - SL: $97,000 (system default)
  - TP: $106,000 (system default)
  ↓
trading_result = {
  status: 'success',
  trade_id: '...',
  executed_price: 100000
}
```

### Position Management Flow (Active Positions)

```
Scheduled/Manual Trigger
  ↓
Orchestrator: extraction phase (fresh market data)
  ↓
Decision Engine: make_decision()
  ↓
Check for active position:
  _get_active_position(symbol, config_id)

  a) Paper mode:
     Query paper_trades WHERE status='open'
     JOIN decisions to get entry_reasoning

  b) Symphony mode:
     Query live_trades for batch_id
     Call Symphony API for real position data
     Enrich with entry_reasoning from DB
  ↓
Position found? YES → Route to _handle_position_management()
  ↓
Calculate performance metrics:
  - P&L percentage (direction-aware):
    * LONG: ((current - entry) / entry) × 100
    * SHORT: ((entry - current) / entry) × 100
  - Duration in hours: (now - opened_at) / 3600
  - Performance status:
    * >5%: "Strong Winner"
    * 1-5%: "Winning"
    * -1 to 1%: "Break-even"
    * -5 to -1%: "Losing"
    * <-5%: "Strong Loser"
  ↓
Format position data for LLM:
  CURRENT POSITION DETAILS:
    - Position Type, Entry/Current Price, Size, P&L, Performance, Duration
  ORIGINAL TRADE CONTEXT:
    - Entry Reasoning (from original decision)
    - Entry Confidence
    - Stop Loss, Take Profit
  ↓
Build position management prompt:
  - Position status section (NEW)
  - Market data section (SAME as opportunity analysis)
  - Volume analysis (SAME)
  - User strategy (SAME)
  - Output format: ACTION: [close/wait] (DIFFERENT)
  ↓
Call LLM with complete prompt
  ↓
Parse response:
  - ACTION: close or wait
  - CONFIDENCE: 0.0-1.0
  - REASONING: Why to close/hold
  - STOP_LOSS: Updated SL (optional)
  - TAKE_PROFIT: Updated TP (optional)
  ↓
Create position_management_intent:
  - If ACTION=close: Execute close via trading service
  - If ACTION=wait: Log decision, no trade execution
  - SL/TP updates: Currently NOT implemented
```

---

## Key Design Insights

### 1. Clean Separation of Concerns

**LLM Controls**:
- Strategic decisions (when to enter/exit, direction)
- Confidence level (used for position sizing)
- Optional TP/SL suggestions (can delegate to system)

**System Controls**:
- Position sizing calculations
- Leverage application
- Default risk levels (SL/TP percentages)
- Position limits enforcement

**Benefit**: Simple mental model for strategy design. LLM focuses on "am I confident?" rather than complex risk math.

### 2. Context Continuity (Entry → Exit)

Entry decision reasoning flows through to exit decisions:

```
Entry Decision → Database → Position Management Prompt
"RSI oversold, bullish divergence..." → "Original reasoning: RSI oversold..."
```

**Benefit**: LLM can evaluate "Did my entry thesis play out?" with full context.

### 3. Token Optimization for Position Management

Removing ggShot/market intelligence in position management makes sense:
- Position already exists (external signals less relevant)
- Focus on position performance vs strategy rules
- 33% token reduction = faster + cheaper decisions
- Cleaner decision-making (performance data is more actionable than external signals when managing)

### 4. Live Trading Gets Real Data

Symphony/Aster positions use **exchange API data** (not database cache):
- Current price: Live from exchange
- Unrealized P&L: Calculated by exchange
- Position size: Real position quantity

**Benefit**: Decisions based on **actual position state**, not stale data.

### 5. Position-First Decision Tree

Every run checks positions **before** analyzing new opportunities.

**Prevents**:
- Opening duplicate positions
- Forgetting about existing positions
- Analyzing new trades while in a losing position

### 6. Flexible TP/SL Delegation

LLM can:
- **Suggest specific prices**: "STOP_LOSS: 97500" (sophisticated strategies)
- **Return null**: System applies defaults (simple strategies)
- **Mix**: Suggest SL, null for TP

**Benefit**: Flexibility without complexity. Strategies don't need to calculate precise levels if they don't want to.

### 7. Confidence as Natural Position Sizing Signal

Confidence score directly scales position size in `confidence_based` mode:
- Low confidence (0.50) → 50% of max margin → smaller position
- High confidence (0.90) → 90% of max margin → larger position

**Benefit**: Creates natural risk scaling without complex instructions in prompts.

---

## Potential Improvements

### 1. Risk Context in Prompts

**Current Issue**: LLM doesn't know:
- Current leverage setting (1x vs 100x)
- Default TP/SL percentages
- Max position limits

**Potential Fix**: Add risk context section to prompts:
```markdown
## RISK MANAGEMENT SETTINGS
Current Leverage: 10x
Default Stop Loss: 3% from entry
Default Take Profit: 6% from entry
Max Concurrent Positions: 5
Position Sizing Method: Confidence-based (max 10% of balance)
```

**Benefit**: Strategies can make informed decisions knowing risk parameters.

**Trade-off**: Adds ~100 tokens per prompt.

### 2. Dynamic TP/SL Defaults

**Current Issue**: Fixed percentages (3% SL, 6% TP) apply to ALL trades regardless of:
- Volatility (BTC vs altcoins)
- Timeframe (5m scalp vs 1d swing)
- Market conditions (trending vs ranging)

**Potential Fixes**:

a) **Volatility-based defaults**:
```python
# Calculate ATR (Average True Range) from market data
atr_percentage = calculate_atr_pct(symbol, timeframe)

# Scale defaults based on volatility
default_stop_loss_pct = max(2.0, min(10.0, atr_percentage * 1.5))
default_take_profit_pct = default_stop_loss_pct * 2
```

b) **Timeframe-based defaults**:
```python
timeframe_defaults = {
    '5m': {'sl': 1.0, 'tp': 2.0},   # Tighter for scalping
    '1h': {'sl': 3.0, 'tp': 6.0},   # Current defaults
    '1d': {'sl': 5.0, 'tp': 10.0}   # Wider for swings
}
```

**Benefit**: Risk levels adapt to market conditions automatically.

### 3. SL/TP Trailing Updates

**Current Issue**: LLM can suggest updated SL/TP in position management, but system **does NOT apply updates**.

```python
# LLM outputs:
STOP_LOSS: 96000  # Updated from original 95000
TAKE_PROFIT: 102000  # Updated from original 100000

# System behavior:
if action == 'wait':
    log_decision()   # ✅ Logs
    # ❌ Does NOT update SL/TP in database
```

**Potential Fix**: Implement SL/TP update logic:
```python
if action == 'wait':
    # Update SL/TP if LLM suggested changes
    if new_stop_loss and new_stop_loss != current_stop_loss:
        update_position_stop_loss(trade_id, new_stop_loss)
        log_activity("sl_updated", {"old": current_sl, "new": new_sl})

    if new_take_profit and new_take_profit != current_take_profit:
        update_position_take_profit(trade_id, new_take_profit)
        log_activity("tp_updated", {"old": current_tp, "new": new_tp})
```

**Benefit**: Enables trailing stops and dynamic profit targets.

**Considerations**:
- Only update if LLM explicitly suggests change
- Log all updates for audit trail
- Validate new levels (SL should be tighter, TP should be favorable)

### 4. Multi-Position Portfolio Management

**Current Limitation**: Position management is **one-way** (hold → close):
- ❌ Cannot suggest "close and immediately reopen SHORT"
- ❌ Cannot suggest "add to position" (scale in)
- ❌ Cannot suggest "reduce position by 50%" (scale out)

**Potential Enhancement**: Portfolio-level decision mode:
```markdown
## OUTPUT FORMAT
ACTION: [close/hold/scale_out/scale_in/reverse]
CONFIDENCE: [0.000-1.000]
SCALE_PERCENTAGE: [0-100] (if scaling)
REASONING: [...]
```

**Benefit**: More sophisticated position management strategies.

**Trade-off**: Increases complexity significantly.

### 5. Performance Classification Granularity

**Current**: 5 categories (Strong Winner, Winning, Break-even, Losing, Strong Loser)

**Enhancement**: Add time-based context:
```python
# Consider both P&L and duration
if pnl_percentage > 5 and hours_held < 24:
    performance_status = "Quick Winner - Consider Taking Profit"
elif pnl_percentage > 5 and hours_held > 168:
    performance_status = "Long-term Winner - Strong Trend"
elif pnl_percentage < -3 and hours_held < 1:
    performance_status = "Early Loser - Wait for Thesis"
elif pnl_percentage < -3 and hours_held > 24:
    performance_status = "Extended Loser - Consider Exit"
```

**Benefit**: More nuanced guidance for position management decisions.

### 6. Feedback Loop for Default Applications

**Current Issue**: If LLM suggests `SL: null` and system applies 3% default, the LLM never learns what was actually used.

**Potential Fix**: Add feedback in subsequent position management prompts:
```markdown
ORIGINAL TRADE CONTEXT:
Entry Reasoning: RSI oversold...
Entry Confidence: 75.0%
Stop Loss: $97,000 (applied from 3% default - you returned null)
Take Profit: $106,000 (you suggested this price)
```

**Benefit**: LLM understands which decisions it made vs system defaults.

### 7. Structured Output Format

**Current**: Text-based parsing is robust but loose

**Alternative**: Use OpenAI's structured output feature (strict JSON schema):
```python
response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "trading_decision",
        "schema": {
            "type": "object",
            "properties": {
                "action": {"enum": ["long", "short", "wait"]},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "reasoning": {"type": "string"},
                "stop_loss_price": {"type": ["number", "null"]},
                "take_profit_price": {"type": ["number", "null"]}
            },
            "required": ["action", "confidence", "reasoning"]
        }
    }
}
```

**Benefit**: Guaranteed parseable responses, no text extraction errors.

**Trade-off**: Less flexibility for LLM variations, requires OpenAI (not all providers support strict schemas).

### 8. Position Context in Opportunity Analysis

**Current**: Opportunity analysis has zero awareness of account state (P&L, open positions on other symbols).

**Enhancement**: Add portfolio context to opportunity analysis:
```markdown
## ACCOUNT STATUS
Total Balance: $9,234.56
Unrealized P&L: $-123.45 (-1.2%)
Open Positions: 2 of 5 max
Total Exposure: $15,000 (1.6x balance)

Currently Active:
- LONG ETH/USDT: +$234.56 (+3.1%), 12h held
- SHORT BNB/USDT: -$358.01 (-4.7%), 36h held
```

**Benefit**: Strategies can consider portfolio risk before adding positions.

**Consideration**: Adds significant prompt complexity.

---

## Files Reference

### Core Decision Engine
- `decision/engine_v2.py` - Main decision orchestration (1900+ lines)
  - Lines 279-293: Position check routing
  - Lines 295-345: Opportunity analysis handler
  - Lines 549-609: Position management handler
  - Lines 655-717: Position data formatting
  - Lines 1622-1730: Active position fetching (paper + live)

### Prompt Templates
- `decision/prompts/opportunity_analysis.py` - New trade template (75 lines)
- `decision/prompts/position_management.py` - Position management template (56 lines)
- `decision/prompts/signal_validation.py` - External signal template (51 lines)

### Configuration Models
- `core/config/models.py` - Pydantic config models (300+ lines)
  - Lines 97-127: Position sizing config
  - Lines 113-127: Risk management config
  - Lines 226-256: Position sizing calculation
  - Lines 258-300: Default SL/TP calculation

### Trading Services
- `trading/paper/supabase_service.py` - Paper trading execution (900+ lines)
  - Lines 92-128: Position sizing calculation
  - Lines 160-187: Default SL/TP application
  - Lines 219-400: Trade execution with overrides

- `trading/live/symphony_service.py` - Symphony live trading
- `trading/live/aster_service_v3.py` - AsterDEX futures trading

### Frontend Integration
- `frontend/components/StrategyAdvisorPanel.tsx` - AI strategy assistant
- `frontend/components/configure/StrategyEditor.tsx` - Strategy input
- `api/assistant.py` - Strategy Advisor chat endpoint

---

## Conclusion

The ggbots prompt system demonstrates **production-grade LLM integration** with:

✅ **Clean architecture**: Separation of strategy (LLM) and risk (system)
✅ **Context awareness**: Position state drives template selection
✅ **Token efficiency**: 93% reduction via SUMMARY + CRITICAL FIELDS
✅ **Flexibility**: LLM can delegate or override system defaults
✅ **Continuity**: Entry reasoning preserved for exit decisions
✅ **Real data**: Live trading uses exchange API, not cache

**Areas for improvement** focus on:
- Adding risk context to prompts
- Dynamic TP/SL defaults based on volatility/timeframe
- Implementing SL/TP trailing updates
- Portfolio-level position management
- Structured output formats (if desired)

The system is **well-designed for current scale** and provides solid foundation for advanced features.
