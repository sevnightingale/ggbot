# Activity Logging Complete Map - ggbots Platform

**Generated**: 2025-11-04
**Purpose**: Comprehensive mapping of all activity types, logging paths, queries, and rendering

---

## 1. Activity Type Definitions

### Current: 11 Activity Types (from `core/common/activity_logger.py`)

| Activity Type | Priority | Grouping | Purpose | Status |
|---------------|----------|----------|---------|--------|
| `trade_entry_long` | 1 | Never | Trade opened (long position) | ✅ Logged |
| `trade_entry_short` | 1 | Never | Trade opened (short position) | ✅ Logged |
| `trade_win` | 1 | Never | Trade closed with profit | ⚠️ Partial |
| `trade_loss` | 1 | Never | Trade closed with loss | ⚠️ Partial |
| `strategy_updated` | 1 | Never | Agent strategy modified | ✅ Logged |
| `market_query` | 2 | Can group | Market data fetched | ✅ Logged |
| `agent_wait` | 2 | Can group | Agent waiting/sleeping | ✅ Logged |
| `observation_recorded` | 2 | Can group | Post-trade reflection | ✅ Logged |
| `analysis` | 2 | Can group | Agent thoughts/reasoning | ✅ Logged |
| `reasoning` | 2 | Can group | Agent reasoning | ❌ Unused |
| `plan` | 2 | Can group | Agent planning | ❌ Unused |

**Total**: 11 types, 9 in use, 2 unused

---

## 2. Activity Logging Paths (WHERE Activities Are Created)

### A. Agent MCP Tools (`agent/mcp_server.py`)

| Tool | Activity Type | Lines | Trade Type Detection | Notes |
|------|---------------|-------|---------------------|-------|
| `query_market_data` | `market_query` | 197-211 | N/A | ✅ Working |
| `execute_trade` | `trade_entry_{side}` | 344-390 | ✅ FIXED (line 368) | Uses `agent_context.trading_mode` |
| `close_position` | `trade_win/loss` | 574-620 | ✅ FIXED (line 599) | Uses `agent_context.trading_mode` |
| `update_strategy` | `strategy_updated` | 655-668 | N/A | ✅ Working |
| `wait_for` | `agent_wait` | 720-732 | N/A | ✅ Working |
| `record_trade_observation` | `observation_recorded` | 805-820 | N/A | ✅ Working |
| `save_strategy_and_exit` | `strategy_updated` | 1026-1038 | N/A | ✅ ADDED |
| `get_current_price` | None | - | N/A | Correct (too frequent) |
| `get_positions` | None | - | N/A | Correct (too frequent) |
| `get_account_status` | None | - | N/A | Correct (too frequent) |
| `query_trade_observations` | None | - | N/A | Correct (internal query) |

**Coverage**: 7/11 tools log activities (64%)

### B. Agent Direct Logging (`agent/run_agent.py`)

| Location | Activity Type | Lines | Notes |
|----------|---------------|-------|-------|
| Agent streaming responses | `analysis` | Multiple | Logs agent thoughts directly via Redis |

**Note**: Agent logs `analysis` type directly when streaming thoughts, NOT via MCP tools.

### C. Trading Services

#### Paper Trading (`trading/paper/supabase_service.py`)
| Method | Activity Type | Status | Issue |
|--------|---------------|--------|-------|
| `execute_trade_intent()` | `trade_entry_{side}` | ❌ **MISSING** | Scheduled bots have no visibility |
| `close_position()` | `trade_win/loss` | ❌ **MISSING** | Manual closes not logged |

#### Aster Live Trading (`trading/live/aster_service_v3.py`)
| Method | Activity Type | Status | Issue |
|--------|---------------|--------|-------|
| `execute_trade_intent()` (~line 540) | `trade_entry_{side}` | ❌ **MISSING** | No logging when Aster trade opens |
| `close_position()` (line 804-886) | `trade_win/loss` | ❌ **MISSING** | Manual API closes not logged |
| TP order fill | `trade_win/loss` | ❌ **MISSING** | No monitoring system |
| SL order fill | `trade_win/loss` | ❌ **MISSING** | No monitoring system |

#### Symphony Live Trading (`trading/live/symphony_service.py`)
| Method | Activity Type | Status | Issue |
|--------|---------------|--------|-------|
| `execute_trade()` | `trade_entry_{side}` | ❌ **MISSING** | No logging |
| `close_position()` | `trade_win/loss` | ❌ **MISSING** | No logging |

### D. Decision Engine (`decision/engine_v2.py`)

| Location | Activity Type | Status | Notes |
|----------|---------------|--------|-------|
| `make_decision()` | `decision_made` (NEW) | ❌ **NOT IMPLEMENTED** | Would show AI reasoning |

### E. Extraction Engine (`extraction/v2/extraction_engine.py`)

| Location | Activity Type | Status | Notes |
|----------|---------------|--------|-------|
| `extract_for_symbol()` | `data_extraction` (NEW) | ❌ **NOT IMPLEMENTED** | Would show data gathering |

---

## 3. Critical Missing Logging Points

### 🔴 URGENT: TP/SL Order Fills (Aster)

**Problem**: When TP or SL orders trigger on Aster, there's **NO system monitoring them**.

**Current Flow**:
1. Agent opens trade → `execute_trade_intent()` creates TP/SL orders
2. TP/SL order IDs saved to `live_trades.stop_loss_order_id` / `take_profit_order_id`
3. ❌ **Nothing checks if these orders filled**
4. Trade record stays `closed_at=NULL` forever
5. Agent's `get_positions()` shows stale data
6. Timeline shows no closure activity

**Solution Required**: Background job to poll Aster order status

```python
# Needed: scripts/monitor_aster_orders.py (PM2 service)
async def check_open_orders():
    """
    Query all open trades with TP/SL orders.
    For each, check Aster order status.
    If filled, mark closed + log activity.
    """
    # Pseudo-code
    open_trades = get_open_aster_trades()
    for trade in open_trades:
        sl_status = await aster.get_order_status(trade.sl_order_id)
        tp_status = await aster.get_order_status(trade.tp_order_id)

        if sl_status == "FILLED":
            await mark_trade_closed(trade.batch_id, reason="stop_loss")
            log_activity_safe(
                activity_type='trade_loss',  # SL usually = loss
                summary=f"SL hit: {symbol} at ${sl_price}",
                trade_type='aster'
            )

        if tp_status == "FILLED":
            await mark_trade_closed(trade.batch_id, reason="take_profit")
            log_activity_safe(
                activity_type='trade_win',  # TP usually = win
                summary=f"TP hit: {symbol} at ${tp_price}",
                trade_type='aster'
            )
```

**Frequency**: Check every 30 seconds (similar to paper trading monitoring)

---

### 🔴 HIGH PRIORITY: Aster Service Activity Logging

**File**: `trading/live/aster_service_v3.py`

**Needed Additions**:

#### 1. Trade Entry Logging (line ~546, after successful order)
```python
# After line 546: symbol=symbol parameter save
# Add activity logging
from core.common.activity_logger import log_activity_safe

log_activity_safe(
    config_id=config_id,
    user_id=user_id,  # Need to add user_id to method signature
    activity_type=f"trade_entry_{side}",
    activity_source='aster_service',
    summary=f"Opened {side} {symbol} at ${entry_price:.2f}",
    details={
        'symbol': symbol,
        'side': side,
        'entry_price': entry_price,
        'size': quantity,
        'leverage': leverage,
        'stop_loss_order_id': sl_order_id,
        'take_profit_order_id': tp_order_id
    },
    trade_id=order_id,  # batch_id
    trade_type='aster',
    related_symbol=symbol,
    priority=1,
    importance=9
)
```

#### 2. Manual Close Logging (line ~870, after successful close)
```python
# After line 870: await self._mark_trade_closed(batch_id)
# Add activity logging
# Need to:
# 1. Fetch trade record to get user_id, config_id
# 2. Calculate P&L from Aster API
# 3. Log activity

trade_record = await self._get_trade_record(batch_id)
# Fetch P&L from Aster userTrades endpoint
user_trades = await self.get_user_trades(limit=100)
matched_trade = next((t for t in user_trades if str(t['id']) == batch_id), None)

if matched_trade:
    pnl = float(matched_trade.get('realizedPnl', 0))
    activity_type = 'trade_win' if pnl >= 0 else 'trade_loss'

    log_activity_safe(
        config_id=trade_record['config_id'],
        user_id=user_id,  # From method param
        activity_type=activity_type,
        activity_source='aster_service',
        summary=f"Closed {symbol}: {'+' if pnl > 0 else ''}{pnl:.2f}",
        details={
            'symbol': symbol,
            'pnl': pnl,
            'close_reason': 'manual'
        },
        trade_id=batch_id,
        trade_type='aster',
        related_symbol=symbol,
        priority=1,
        importance=9
    )
```

---

### 🟡 MEDIUM PRIORITY: Paper Trading Service Logging

**File**: `trading/paper/supabase_service.py`

**Needed**: Same pattern as Aster (trade entries and closures for scheduled bots)

---

## 4. Activity Query Pipeline

### A. Database Schema (`activities` table)

```sql
CREATE TABLE activities (
    activity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID NOT NULL,
    user_id UUID NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    activity_source VARCHAR(50) NOT NULL,  -- 'agent_tool', 'aster_service', 'scheduled_bot'
    summary VARCHAR(200) NOT NULL,
    details JSONB,
    trade_id UUID,                -- Links to paper_trades or live_trades
    trade_type VARCHAR(20),       -- 'paper', 'aster', 'symphony'
    decision_id UUID,
    related_symbol VARCHAR(20),
    priority INTEGER NOT NULL,    -- 1=never group, 2=can group
    importance INTEGER NOT NULL,  -- 1-10, user-facing importance
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_activities_config_time ON activities(config_id, created_at DESC);
CREATE INDEX idx_activities_type ON activities(activity_type);
CREATE INDEX idx_activities_trade ON activities(trade_id) WHERE trade_id IS NOT NULL;
```

### B. API Endpoints (`api/activities.py`)

| Endpoint | Purpose | Returns |
|----------|---------|---------|
| `GET /api/v2/activities/{config_id}` | Get all activities for timeline | Activities array |
| `GET /api/v2/activities/{config_id}/balance-series` | Get cumulative P&L chart data | Balance timeseries |
| `GET /api/v2/activities/{config_id}/metadata` | Get bot stats for header | Metrics (trades, win rate, P&L) |

**Query Filters** (activities endpoint):
- `start_time`: ISO timestamp filter
- `end_time`: ISO timestamp filter
- `activity_types`: Array of types to include
- `trade_id`: Filter by specific trade
- `min_importance`: Hide activities below threshold (1-10)
- `limit`: Max activities (default 500, max 1000)

**Balance Series Modes**:
- `mode=pnl`: Cumulative P&L from $0 (default)
- `mode=balance`: Actual account balance over time

**Data Sources** (balance series):
1. Paper trades: `paper_trades.realized_pnl`
2. Aster trades: Queries Aster API `/fapi/v3/userTrades` + maps via `live_trades` table

**Issue**: Balance series queries Aster account balance correctly ✅

---

## 5. Frontend Rendering (Timeline.jsx)

### A. Activity Type to Glyph Mapping

**File**: `frontend/components/Timeline.jsx`

```javascript
// Line 132-144: ACTIVITY_DEFS (color + labels)
const ACTIVITY_DEFS = {
  trade_entry_long:  { color: VIBE.signal, label: "Long Entry" },   // Blue
  trade_entry_short: { color: VIBE.ember,  label: "Short Entry" },  // Red
  trade_win:         { color: VIBE.signal, label: "Trade Win" },    // Blue
  trade_loss:        { color: VIBE.ember,  label: "Trade Loss" },   // Red
  strategy_updated:  { color: VIBE.brass,  label: "Strategy Update" }, // Gold
  market_query:      { color: VIBE.signal, label: "Data Query" },   // Blue
  agent_wait:        { color: VIBE.hair,   label: "Waiting" },      // Gray
  observation_recorded: { color: VIBE.hair, label: "Observation" }, // Gray
  analysis:          { color: VIBE.lilac,  label: "Agent Thoughts" }, // Purple
  reasoning:         { color: VIBE.lilac,  label: "Agent Thoughts" }, // Purple
  plan:              { color: VIBE.lilac,  label: "Agent Thoughts" }  // Purple
}

// Line 146-160: glyphIdFor() - Maps type to canvas icon
function glyphIdFor(type) {
  switch(type) {
    case 'trade_entry_long': return 'long';    // ▲ triangle up
    case 'trade_entry_short': return 'short';  // ▼ triangle down
    case 'trade_win': return 'win';            // ↑ up arrow
    case 'trade_loss': return 'loss';          // ↓ down arrow
    case 'strategy_updated': return 'strategy'; // 🔧 wrench
    case 'market_query': return 'query';       // 📊 bar chart
    case 'agent_wait': return 'wait';          // 🕐 clock
    case 'observation_recorded': return 'note'; // 📄 note
    case 'analysis': return 'think';           // 💭 bubble
    case 'reasoning': return 'think';          // 💭 bubble
    case 'plan': return 'plan';                // 💭 bubble with tail
  }
}
```

### B. Grouping Logic (Line 307-315)

```javascript
// Activities with priority=2 can be grouped by:
// - Same time bucket (rules.bucketMs, e.g., 60 seconds)
// - Same activity type
// Result: Single icon with badge count

// Priority=1 activities NEVER group (always individual icons)
```

### C. Canvas Rendering

**Zoom Levels** (Line 59-66):
- `1h`: 60-minute span, 1-minute buckets
- `4h`: 4-hour span, 10-minute buckets
- `1d`: 24-hour span, 1-hour buckets
- `1w`: 7-day span, 4-hour buckets
- `All`: Full history, 24-hour buckets

**Visual Elements**:
- Equity line: Blue line connecting balance points
- Activity icons: Circles with glyphs, stem to equity line
- Hover: Enlarged icon with details
- Click: Side panel with full activity data
- "Now" pulse: Pulsing blue dot at latest timestamp

---

## 6. Data Flow Summary

### Trade Entry Flow

```
1. AGENT CALLS execute_trade MCP tool
   ├─> MCP tool logs activity (trade_entry_long/short) ✅
   └─> Calls API /api/v2/agent/execute-trade
       └─> Routes to Aster/Paper/Symphony service
           └─> Aster service executes trade
               └─> ❌ NO ACTIVITY LOGGING HERE (missing)
```

**Result**: Agent trades get logged via MCP tool ✅, but if called directly via API it's not logged ❌

### Trade Exit Flow (Manual)

```
1. AGENT CALLS close_position MCP tool
   ├─> MCP tool logs activity (trade_win/loss) ✅
   └─> Calls API /api/v2/agent/close-position
       └─> Routes to Aster service.close_position()
           ├─> Cancels TP/SL orders
           ├─> Places market close order
           ├─> Marks trade closed in DB
           └─> ❌ NO ACTIVITY LOGGING HERE (missing)
```

**Result**: Agent closes get logged via MCP tool ✅, but if called directly via API it's not logged ❌

### Trade Exit Flow (TP/SL Automatic)

```
1. TP or SL order triggers on Aster
   └─> ❌ NO MONITORING SYSTEM
       └─> ❌ Trade stays open in DB forever
           └─> ❌ NO ACTIVITY LOGGED
               └─> ❌ Timeline shows nothing
```

**Result**: Completely broken ❌

---

## 7. Proposed New Activity Types

### Missing Types for Complete Coverage

| New Type | Priority | Purpose | Where to Log |
|----------|----------|---------|--------------|
| `decision_made` | 1 | AI decision output (long/short/wait) | `decision/engine_v2.py` |
| `data_extraction` | 2 | Extraction phase complete | `extraction/v2/extraction_engine.py` |
| `error_logged` | 1 | System errors | Orchestrator, engines |
| `config_updated` | 1 | User config changes | API config endpoints |
| `bot_cycle_start` | 2 | Scheduled execution trigger | Orchestrator |
| `position_management` | 1 | Position exit decisions (SL/TP logic) | Decision engine |
| `market_intelligence_batch` | 2 | Intelligence fetch batch | `market_intelligence/orchestrator.py` |
| `signal_received` | 2 | External signal validation | `signals/listener_service.py` |

**Total**: 8 new types proposed

### Updated Timeline.jsx Glyphs (Needed)

```javascript
// Add to glyphIdFor()
case 'decision_made': return 'think';
case 'data_extraction': return 'query';
case 'error_logged': return 'close';
case 'config_updated': return 'gear';
case 'position_management': return 'gear';
case 'bot_cycle_start': return 'gear';
case 'market_intelligence_batch': return 'query';
case 'signal_received': return 'note';
```

---

## 8. Implementation Priority

### Phase 1: URGENT (Agent Timeline Fix)

**Priority**: P0 - Blocks ggAster agent timeline
**Effort**: 4-6 hours

1. ✅ **DONE**: Fix MCP tools to detect trading_mode
2. ✅ **DONE**: Add logging to save_strategy_and_exit
3. ❌ **TODO**: Add logging to Aster service execute_trade_intent
4. ❌ **TODO**: Add logging to Aster service close_position
5. ❌ **TODO**: Build TP/SL order monitoring background job

**Files**:
- `trading/live/aster_service_v3.py` (add logging)
- `scripts/monitor_aster_orders.py` (new file)
- `agent/run_agent.py` (restart agent to load fixes)

### Phase 2: Scheduled Bot Visibility

**Priority**: P1
**Effort**: 2-3 hours

1. Add logging to paper trading service (execute + close)
2. Add logging to Symphony service (execute + close)

### Phase 3: Decision & Extraction Logging

**Priority**: P1
**Effort**: 3-4 hours

1. Add `decision_made` to decision engine
2. Add `data_extraction` to extraction engine
3. Add new types to `ACTIVITY_PRIORITY` dict
4. Update Timeline.jsx glyphs

### Phase 4: Background Jobs & Monitoring

**Priority**: P2
**Effort**: 6-8 hours

1. TP/SL order monitoring service (PM2)
2. Position monitoring for all trade types
3. Error logging integration
4. Orchestrator lifecycle logging

---

## 9. Testing Checklist

### Per Activity Type

- [ ] `trade_entry_long` - Agent opens long position → Activity appears
- [ ] `trade_entry_short` - Agent opens short position → Activity appears
- [ ] `trade_win` - Agent closes with profit → Green up arrow appears
- [ ] `trade_loss` - Agent closes with loss → Red down arrow appears
- [ ] `trade_win` - TP order fills → Activity logged automatically
- [ ] `trade_loss` - SL order fills → Activity logged automatically
- [ ] `strategy_updated` - Agent saves strategy → Gold wrench appears
- [ ] `market_query` - Agent queries data → Blue bar chart appears
- [ ] `agent_wait` - Agent waits 30min → Gray clock appears
- [ ] `observation_recorded` - Agent records learning → Gray note appears
- [ ] `analysis` - Agent streams thoughts → Purple bubble appears

### Timeline Features

- [ ] Activities appear in correct chronological order
- [ ] Priority 2 activities group by type+time
- [ ] Priority 1 activities never group
- [ ] Click activity → Side panel shows details
- [ ] Hover activity → Icon enlarges
- [ ] Balance chart updates with Aster P&L
- [ ] "Now" pulse appears at latest timestamp
- [ ] Zoom levels (1h/4h/1d/1w/All) work
- [ ] Filters show/hide activity types

---

## 10. Current Production Status

### ggAster Agent (config: bb2560fd-b053-464f-8a58-8e254e4d36fa)

**Activities Logged**: 271 total
- 156× `market_query` ✅
- 92× `analysis` ✅
- 20× `agent_wait` ✅
- 3× Other ✅

**Trades**:
- 3 Aster trades (1 closed, 2 orphaned)
- 1 closed trade: BTC SHORT @ 12:02, closed @ 13:50 with profit
- ❌ **NO trade_win activity logged** (this is the bug)
- ❌ **NO trade_entry activity from Aster service** (missing)

**Timeline Status**:
- Shows agent thoughts, queries, waits ✅
- ❌ Shows NO trades (most important events missing!)
- ❌ Balance chart flat (no trade P&L integrated)

**Root Cause**: MCP tools logging with wrong `trade_type='paper'` (now fixed ✅), but Aster service has zero logging ❌

---

## 11. Recommendations

1. **URGENT**: Implement Phase 1 (Aster service logging + TP/SL monitoring)
2. **HIGH**: Add `decision_made` logging (shows AI reasoning before trades)
3. **MEDIUM**: Add scheduled bot activity logging
4. **FUTURE**: Consider real-time activity streaming via WebSocket (vs 10s polling)

---

**Next Actions**: See TODO.md for implementation tasks
