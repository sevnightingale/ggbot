# Trade Timeline Feature - Complete Design Document

## Overview

The Trade Timeline is a comprehensive view of a trade's complete lifecycle, showing:
1. **Market Data Context** - What the AI saw before entering
2. **Trade Entry** - Opening decision + trade execution details
3. **Trade Management** - All monitoring decisions during trade lifetime
4. **Trade Exit** - Closing decision + trade closure details

This feature enables transparency, education, and advanced analytics for trade performance analysis.

---

## Vision & User Experience

### Timeline Modal Design

```
┌────────────────────────────────────────────────────┐
│         Trade Timeline: BTC/USDT LONG             ✕│
├────────────────────────────────────────────────────┤
│                                                    │
│  1️⃣ 📊 MARKET DATA CONTEXT                        │
│     [▼] Multi-timeframe analysis (expandable)     │
│     ├─ 5m: RSI 68.4, Bullish MACD crossover       │
│     ├─ 1h: Strong uptrend, overbought warning     │
│     ├─ 4h: Key support at $41,800                 │
│     └─ Volume: 1.2M (above average)               │
│                                                    │
│  2️⃣ 🟢 TRADE ENTRY (Jan 21, 2:15 PM)              │
│     [▼] Decision + Execution                      │
│     ├─ Action: LONG                               │
│     ├─ Confidence: 75%                            │
│     ├─ Entry Price: $42,150                       │
│     ├─ Position Size: $5,000 (10x leverage)       │
│     ├─ Stop Loss: $41,800                         │
│     ├─ Take Profit: $43,200                       │
│     └─ Reasoning: "Bullish MACD crossover on 1h   │
│        timeframe combined with strong volume..."   │
│                                                    │
│  3️⃣ 👁️ TRADE MANAGEMENT (3h 27m duration)         │
│     [▼] 12 monitoring decisions                   │
│     ├─ 2:30 PM: "Wait - position favorable"       │
│     ├─ 2:45 PM: "Wait - trend intact"             │
│     ├─ 3:00 PM: "Wait - approaching TP"           │
│     └─ ... [Show all 12 decisions]                │
│                                                    │
│  4️⃣ 🔴 TRADE EXIT (Jan 21, 5:42 PM)               │
│     [▼] Decision + Execution                      │
│     ├─ Trigger: Take Profit Hit                   │
│     ├─ Exit Price: $43,200                        │
│     ├─ P&L: +$125.50 (+2.5%)                      │
│     ├─ Duration: 3h 27m                           │
│     └─ Reasoning: "TP target reached, securing    │
│        profit as planned"                         │
└────────────────────────────────────────────────────┘
```

### Access Points

1. **From Decision Cards** (DecisionFeed)
   - "View Timeline" button on enter/exit decisions
   - Links to trade if one was executed

2. **From Trade Dots** (PerformanceChart)
   - Click dot → Trade popover → "View Full Timeline" button

3. **From Trade History Modal**
   - Each trade row has timeline icon/button

4. **From Positions Table**
   - Active trades show "View Timeline" for in-progress view

---

## Current Data Model

### What We Have

#### `decisions` Table
```sql
decision_id       UUID PRIMARY KEY
config_id         UUID (which bot)
user_id           UUID
symbol            TEXT (e.g., BTC/USDT)
action            TEXT ('enter', 'wait', 'exit')
confidence        DECIMAL (0.0-1.0)
reasoning         TEXT (LLM explanation)
prompt            TEXT (FULL market data + user strategy)
decision_data     JSONB (raw LLM response)
created_at        TIMESTAMP
```

**Key Points:**
- ✅ Contains full market data in `prompt` field
- ✅ Stores AI reasoning
- ✅ Has action type (enter/wait/exit)
- ❌ No link to which trade it's managing

#### `paper_trades` Table
```sql
trade_id          UUID PRIMARY KEY
decision_id       UUID (links to OPENING decision)
config_id         UUID
user_id           UUID
symbol            TEXT
side              TEXT ('long', 'short')
entry_price       DECIMAL
exit_price        DECIMAL
size_usd          DECIMAL
leverage          DECIMAL
realized_pnl      DECIMAL
opened_at         TIMESTAMP
closed_at         TIMESTAMP
close_reason      TEXT ('take_profit', 'stop_loss', 'manual', etc.)
confidence_score  DECIMAL
```

**Key Points:**
- ✅ Links to opening decision via `decision_id`
- ❌ No link to exit decision
- ❌ No link to monitoring decisions

#### `live_trades` Table
```sql
batch_id          TEXT PRIMARY KEY
decision_id       UUID (links to OPENING decision)
config_id         UUID
user_id           UUID
symphony_agent_id TEXT
created_at        TIMESTAMP
updated_at        TIMESTAMP
```

**Key Points:**
- ✅ Links to opening decision
- ❌ No exit_decision_id
- ❌ No link to monitoring decisions
- ⚠️ Minimal schema (Symphony handles actual trade data)

---

## Required Changes

### Phase 1: Database Schema Updates

#### 1.1 Extend `paper_trades` Table
```sql
-- Add exit decision link
ALTER TABLE paper_trades
ADD COLUMN exit_decision_id UUID REFERENCES decisions(decision_id);

-- Add index for performance
CREATE INDEX idx_paper_trades_exit_decision
ON paper_trades(exit_decision_id);
```

#### 1.2 Extend `live_trades` Table
```sql
-- Add exit decision link
ALTER TABLE live_trades
ADD COLUMN exit_decision_id UUID REFERENCES decisions(decision_id);

-- Add index for performance
CREATE INDEX idx_live_trades_exit_decision
ON live_trades(exit_decision_id);
```

#### 1.3 Extend `decisions` Table
```sql
-- Add trade link for reverse lookup
ALTER TABLE decisions
ADD COLUMN trade_id UUID;

-- Add trade type to distinguish paper vs live
ALTER TABLE decisions
ADD COLUMN trade_type TEXT CHECK (trade_type IN ('paper', 'live'));

-- Add indexes
CREATE INDEX idx_decisions_trade_id ON decisions(trade_id);
CREATE INDEX idx_decisions_trade_type ON decisions(trade_type);
CREATE INDEX idx_decisions_action ON decisions(action);
```

**Why `trade_id` in decisions:**
- Enables direct linking of "wait" decisions to the trade they're monitoring
- Supports efficient queries: "Get all decisions for this trade"
- Critical for analytics: "What market conditions led to wins/losses?"

---

### Phase 2: Code Changes

#### 2.1 Decision Engine Updates (`decision/engine_v2.py`)

**Current Flow:**
```python
async def make_decision(symbol, signal_data=None):
    # Makes decision
    # Saves to decisions table
    # Returns intent
```

**Updated Flow:**
```python
async def make_decision(symbol, signal_data=None, active_trade=None):
    # Makes decision
    decision_id = await self._save_decision_to_db(...)

    # NEW: Link decision to active trade if monitoring
    if active_trade and action == 'wait':
        await self._link_decision_to_trade(
            decision_id,
            active_trade.trade_id,
            active_trade.trading_mode  # 'paper' or 'live'
        )

    return intent
```

**New Method:**
```python
async def _link_decision_to_trade(
    self,
    decision_id: str,
    trade_id: str,
    trade_type: str
) -> None:
    """Link a decision to the trade it's managing."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE decisions
                SET trade_id = %s, trade_type = %s
                WHERE decision_id = %s
            """, (trade_id, trade_type, decision_id))
```

#### 2.2 Paper Trading Engine Updates (`trading/paper/`)

**Update: `execute_trade` Method**
```python
async def execute_trade(decision_result):
    trade_id = await self._open_position(...)

    # NEW: Update opening decision with trade link
    await self._link_opening_decision(
        decision_id=decision_result['decision_id'],
        trade_id=trade_id
    )

    return result
```

**Update: `close_position` Method**
```python
async def close_position(trade_id, close_reason, exit_decision_id=None):
    # Close the trade
    await self._execute_close(...)

    # NEW: Store exit decision link
    if exit_decision_id:
        await self._link_exit_decision(trade_id, exit_decision_id)

    return result
```

**New Methods:**
```python
async def _link_opening_decision(
    self,
    decision_id: str,
    trade_id: str
) -> None:
    """Link opening decision to trade."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE decisions
                SET trade_id = %s, trade_type = 'paper'
                WHERE decision_id = %s
            """, (trade_id, decision_id))

async def _link_exit_decision(
    self,
    trade_id: str,
    exit_decision_id: str
) -> None:
    """Link exit decision to trade."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE paper_trades
                SET exit_decision_id = %s
                WHERE trade_id = %s
            """, (exit_decision_id, trade_id))

            cur.execute("""
                UPDATE decisions
                SET trade_id = %s, trade_type = 'paper'
                WHERE decision_id = %s
            """, (trade_id, exit_decision_id))
```

#### 2.3 Live Trading Engine Updates (`trading/live/symphony_service.py`)

**Same pattern as paper trading:**
```python
async def execute_trade_intent(decision_result):
    batch_id = await self._open_symphony_position(...)

    # NEW: Link opening decision
    await self._link_opening_decision(
        decision_id=decision_result['decision_id'],
        batch_id=batch_id
    )

async def close_position(batch_id, exit_decision_id=None):
    await self._close_symphony_position(...)

    # NEW: Link exit decision
    if exit_decision_id:
        await self._link_exit_decision(batch_id, exit_decision_id)
```

#### 2.4 Orchestrator Updates (`ggbot.py`)

**Update: `_run_trading_v2` Method**
```python
async def _run_trading_v2(config, user_id, decision_result):
    # Check if decision has active trade context
    active_trade = await self._get_active_trade(config.config_id, symbol)

    # Execute trade
    if decision_result['action'] == 'enter':
        result = await trading_service.execute_trade(decision_result)
    elif decision_result['action'] == 'exit' and active_trade:
        # NEW: Pass exit decision ID
        result = await trading_service.close_position(
            active_trade.trade_id,
            close_reason='ai_decision',
            exit_decision_id=decision_result['decision_id']
        )

    return result
```

**New Method:**
```python
async def _get_active_trade(self, config_id: str, symbol: str):
    """Get active trade for this bot/symbol if exists."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Check trading mode
            trading_mode = await self._get_trading_mode(config_id)

            if trading_mode == 'paper':
                cur.execute("""
                    SELECT * FROM paper_trades
                    WHERE config_id = %s
                    AND symbol = %s
                    AND status = 'open'
                    LIMIT 1
                """, (config_id, symbol))
            else:
                cur.execute("""
                    SELECT * FROM live_trades
                    WHERE config_id = %s
                    AND status = 'open'
                    LIMIT 1
                """, (config_id,))

            return cur.fetchone()
```

---

### Phase 3: API Endpoints

#### New Endpoint: Get Trade Timeline
```python
@app.get("/api/v2/trade/{trade_id}/timeline")
async def get_trade_timeline(
    trade_id: str,
    trade_type: str = 'paper',  # or 'live'
    user: User = Depends(get_current_user)
):
    """
    Get complete timeline for a trade.

    Returns:
    {
      "trade": {...},
      "entry_decision": {...},
      "monitoring_decisions": [...],
      "exit_decision": {...}
    }
    """
    # Verify ownership
    trade = await get_trade(trade_id, trade_type)
    if trade.user_id != user.id:
        raise HTTPException(403)

    # Get entry decision
    entry_decision = await get_decision(trade.decision_id)

    # Get monitoring decisions (via trade_id link)
    monitoring_decisions = await get_decisions_by_trade(trade_id)

    # Get exit decision
    exit_decision = None
    if trade.exit_decision_id:
        exit_decision = await get_decision(trade.exit_decision_id)

    return {
        "trade": trade,
        "entry_decision": entry_decision,
        "monitoring_decisions": monitoring_decisions,
        "exit_decision": exit_decision,
        "market_data": parse_market_data_from_prompt(entry_decision.prompt)
    }
```

---

### Phase 4: Frontend Implementation

#### 4.1 New Component: `TradeTimelineModal.tsx`

```tsx
interface TradeTimelineModalProps {
  tradeId: string
  tradeType: 'paper' | 'live'
  isOpen: boolean
  onClose: () => void
}

export function TradeTimelineModal({
  tradeId,
  tradeType,
  isOpen,
  onClose
}: TradeTimelineModalProps) {
  const [timeline, setTimeline] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isOpen) return

    const loadTimeline = async () => {
      const data = await apiClient.getTradeTimeline(tradeId, tradeType)
      setTimeline(data)
      setLoading(false)
    }

    loadTimeline()
  }, [isOpen, tradeId, tradeType])

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="timeline">
          <TimelineSection
            title="Market Data Context"
            data={timeline.market_data}
          />
          <TimelineSection
            title="Trade Entry"
            decision={timeline.entry_decision}
            trade={timeline.trade}
          />
          <TimelineSection
            title="Trade Management"
            decisions={timeline.monitoring_decisions}
          />
          <TimelineSection
            title="Trade Exit"
            decision={timeline.exit_decision}
            trade={timeline.trade}
          />
        </div>
      )}
    </Modal>
  )
}
```

#### 4.2 Update API Client (`lib/api.ts`)

```typescript
async getTradeTimeline(
  tradeId: string,
  tradeType: 'paper' | 'live' = 'paper'
) {
  return this.authenticatedFetch(
    `/api/v2/trade/${tradeId}/timeline?trade_type=${tradeType}`
  )
}
```

#### 4.3 Add Timeline Triggers

**In TradeDetailPopover:**
```tsx
<button onClick={() => setTimelineOpen(true)}>
  View Full Timeline →
</button>

<TradeTimelineModal
  tradeId={trade.trade_id}
  tradeType={trade.trading_mode || 'paper'}
  isOpen={timelineOpen}
  onClose={() => setTimelineOpen(false)}
/>
```

**In PerformanceChart (trade dots):**
```tsx
onClick={(trade) => {
  setSelectedTrade(trade)
  setTimelineOpen(true)
}}
```

**In DecisionFeed cards:**
```tsx
{decision.action === 'enter' && decision.trade_id && (
  <button onClick={() => openTimeline(decision.trade_id)}>
    View Trade Timeline
  </button>
)}
```

---

## Implementation Phases

### Phase 1: Foundation (2-3 days)
- ✅ Database schema migrations (both paper_trades and live_trades)
- ✅ Add indexes for performance
- ✅ Test migrations on production

### Phase 2: Backend Integration (3-4 days)
- ✅ Update decision engine to link decisions to trades
- ✅ Update paper trading engine (opening + exit linking)
- ✅ Update live trading engine (Symphony integration)
- ✅ Update orchestrator to pass active trade context
- ✅ Add `/api/v2/trade/{trade_id}/timeline` endpoint

### Phase 3: Frontend Component (2-3 days)
- ✅ Create TradeTimelineModal component
- ✅ Design timeline UI (expandable sections)
- ✅ Add access points (trade dots, decision cards, positions table)
- ✅ Parse and format market data for display

### Phase 4: Testing & Polish (2 days)
- ✅ Test with existing trades (should handle NULL exit_decision_id gracefully)
- ✅ Test with new trades (verify full linking works)
- ✅ Test both paper and live trades
- ✅ Add loading states, error handling
- ✅ Mobile responsive design

**Total Estimated Time: 9-12 days**

---

## Query Patterns

### Get Complete Timeline (With Full Linking)
```sql
-- Get trade with all decisions
SELECT
  t.*,
  e.decision_id as entry_decision_id,
  e.reasoning as entry_reasoning,
  e.confidence as entry_confidence,
  e.prompt as market_data,
  x.decision_id as exit_decision_id,
  x.reasoning as exit_reasoning,
  x.confidence as exit_confidence
FROM paper_trades t
LEFT JOIN decisions e ON t.decision_id = e.decision_id
LEFT JOIN decisions x ON t.exit_decision_id = x.decision_id
WHERE t.trade_id = $1;

-- Get all monitoring decisions for this trade
SELECT * FROM decisions
WHERE trade_id = $1
AND action = 'wait'
ORDER BY created_at ASC;
```

### Get Timeline Without Full Linking (Fallback for Old Trades)
```sql
-- Entry decision (always linked)
SELECT * FROM decisions WHERE decision_id = $1;

-- Exit decision (fuzzy match)
SELECT * FROM decisions
WHERE config_id = $2
AND symbol = $3
AND action = 'exit'
AND created_at BETWEEN $4 AND $5
ORDER BY created_at ASC
LIMIT 1;

-- Monitoring decisions (fuzzy match)
SELECT * FROM decisions
WHERE config_id = $2
AND symbol = $3
AND action = 'wait'
AND created_at BETWEEN $6 AND $7
ORDER BY created_at ASC;
```

---

## Future Analytics Capabilities

Once full linking is in place, we can build powerful analytics:

### Win/Loss Pattern Analysis
```sql
-- Which market conditions predict winning trades?
SELECT
  t.realized_pnl > 0 as is_win,
  d.prompt::text as market_data,
  d.confidence,
  COUNT(*) as trade_count,
  AVG(t.realized_pnl) as avg_pnl
FROM paper_trades t
JOIN decisions d ON t.decision_id = d.decision_id
WHERE d.prompt LIKE '%RSI%'  -- or parse JSON for specific indicators
GROUP BY is_win, d.confidence
ORDER BY avg_pnl DESC;
```

### Monitoring Frequency vs Outcome
```sql
-- Do more monitoring decisions correlate with better outcomes?
SELECT
  t.trade_id,
  t.realized_pnl,
  COUNT(m.decision_id) as monitoring_count
FROM paper_trades t
LEFT JOIN decisions m ON t.trade_id = m.trade_id AND m.action = 'wait'
GROUP BY t.trade_id, t.realized_pnl
ORDER BY monitoring_count DESC;
```

### Confidence Calibration
```sql
-- Are high-confidence trades actually more profitable?
SELECT
  FLOOR(d.confidence * 10) / 10 as confidence_bucket,
  COUNT(*) as trade_count,
  COUNT(*) FILTER (WHERE t.realized_pnl > 0) as wins,
  AVG(t.realized_pnl) as avg_pnl
FROM paper_trades t
JOIN decisions d ON t.decision_id = d.decision_id
GROUP BY confidence_bucket
ORDER BY confidence_bucket;
```

### Market Condition Correlation
Extract indicators from `prompt` field and correlate with outcomes:
- Which RSI ranges lead to wins?
- Do MACD crossovers actually work?
- Which timeframe analysis is most predictive?
- Volume confirmation accuracy?

---

## Open Questions

1. **Symphony Position Data**
   - How do we get position details (entry/exit price, P&L) from Symphony?
   - Store in live_trades or query Symphony API on-demand?

2. **Historical Trades**
   - Should we backfill trade_id links for existing trades?
   - Or gracefully handle NULL and use fuzzy queries as fallback?

3. **Multi-Symbol Trades**
   - Can a bot trade multiple symbols simultaneously?
   - If yes, need symbol filter in active_trade queries

4. **Position Partials**
   - What if user partially closes position?
   - Multiple exit decisions for one trade?

5. **Manual Interventions**
   - User manually closes position (no exit decision)
   - Show in timeline as "Manual Close" with note?

---

## Success Metrics

Once implemented, measure:
- **User Engagement**: % of users who view timelines
- **Educational Value**: Time spent reviewing timelines
- **Trust Building**: Correlation between timeline usage and continued platform use
- **Analytics Adoption**: % of users who run custom queries on timeline data
- **Feature Requests**: What additional timeline features do users want?

---

## Related Documents

- **Database Schema**: `/database/README.md`
- **Decision Engine**: `/decision/README.md`
- **Trading Engine**: `/trading/README.md`
- **Frontend Components**: `/frontend/README.md`
- **API Endpoints**: `/DOCS/API.md`
