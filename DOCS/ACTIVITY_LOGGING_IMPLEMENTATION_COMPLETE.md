# Activity Logging Implementation - COMPLETE

**Date**: 2025-11-04
**Status**: ✅ Implementation Complete - Ready for Testing

---

## Changes Implemented

### 1. ✅ MCP Tools Fixed (`agent/mcp_server.py`)

**Added trading_mode detection:**
- `AgentContext` now includes `trading_mode` field
- `set_agent_context()` fetches trading_mode from database on startup
- `execute_trade` tool uses `agent_context.trading_mode` (line 368)
- `close_position` tool uses `agent_context.trading_mode` (line 599)
- `save_strategy_and_exit` tool now logs activities (line 1026-1038)

**Impact**: Agent trades now log with correct `trade_type='aster'` instead of hardcoded `'paper'`

**File**: `agent/mcp_server.py`
**Lines Changed**: 44, 50-77, 368, 599, 1026-1038

---

### 2. ✅ Agent Runner Updated (`agent/run_agent.py`)

**Made set_agent_context async:**
- Updated call to `await set_agent_context()` (line 89)

**Impact**: Agent initializes with trading_mode from database

**File**: `agent/run_agent.py`
**Line Changed**: 89

---

### 3. ✅ Aster Service Activity Logging (`trading/live/aster_service_v3.py`)

**Added activity logging import:**
```python
from core.common.activity_logger import log_activity_safe
```

**Trade Entry Logging** (lines 550-591):
- After successful trade execution
- Fetches entry price from LivePriceService
- Logs `trade_entry_long` or `trade_entry_short`
- Includes: symbol, entry_price, quantity, size_usd, leverage, SL/TP prices, confidence
- `trade_type='aster'`
- `activity_source='aster_service'`
- Priority 1, Importance 9

**Manual Close Logging** (lines 918-963):
- After successful position closure
- Fetches P&L from Aster API
- Logs `trade_win` or `trade_loss` based on P&L
- Includes: symbol, pnl, pnl_pct, quantity, close_reason
- `trade_type='aster'`
- `activity_source='aster_service'`
- Priority 1, Importance 9

**Added `_get_order_status()` method** (lines 1005-1049):
- Queries Aster API for order status
- Returns order info with 'status' field
- Used by monitoring service

**Impact**: ALL Aster trades now logged (entries and manual closes)

**Files**: `trading/live/aster_service_v3.py`
**Lines Changed**: 44 (import), 550-591 (entry), 918-963 (close), 1005-1049 (status check)

---

### 4. ✅ TP/SL Order Monitoring Service (NEW)

**File**: `scripts/monitor_aster_orders.py` (NEW - 385 lines)

**Purpose**: Monitor open Aster trades for TP/SL order fills

**Features**:
- Polls every 30 seconds
- Queries all open Aster trades with TP/SL orders
- Checks order status via Aster API
- On FILLED:
  - Marks trade closed in database
  - Fetches P&L from Aster API
  - Logs activity: `trade_win` or `trade_loss`
  - `activity_source='aster_monitor'`
  - `close_reason='stop_loss'` or `'take_profit'`

**Architecture**:
- Async/await for non-blocking operations
- Graceful error handling (logs but continues)
- Activity logging failures don't crash monitor
- Configurable check interval (default 30s)

**PM2 Integration**:
- Runs as background service
- Logs to `logs/aster-monitor-{date}.log`
- 30-day log rotation

---

## Deployment Instructions

### Step 1: Start TP/SL Monitor Service

```bash
cd /home/sev/ggbot
source .venv/bin/activate

# Start monitor as PM2 service
pm2 start scripts/monitor_aster_orders.py \
  --name monitor-aster-orders \
  --interpreter python3 \
  --log logs/aster-monitor.log \
  --error logs/aster-monitor-error.log

# Verify it's running
pm2 status
pm2 logs monitor-aster-orders --lines 20
```

### Step 2: Restart ggAster Agent

```bash
# Check current agent status
pm2 list | grep agent

# Restart agent to load trading_mode fixes
pm2 restart agent-bb2560fd-b053-464f-8a58-8e254e4d36fa

# Verify agent startup
pm2 logs agent-bb2560fd-b053-464f-8a58-8e254e4d36fa --lines 30

# Look for:
# "Agent context set: config_id=..., user_id=..., trading_mode=aster"
```

### Step 3: Clean Up Orphaned Trades

```bash
# Check orphaned trades
source .venv/bin/activate
python3 <<'EOF'
from core.common.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT batch_id, symbol, created_at, closed_at
            FROM live_trades
            WHERE config_id = 'bb2560fd-b053-464f-8a58-8e254e4d36fa'
            AND provider = 'aster'
            ORDER BY created_at DESC
        """)

        print("Aster Trades:")
        for row in cur.fetchall():
            status = "CLOSED" if row[3] else "OPEN"
            print(f"  {row[0][:20]} | {row[1]:10} | {status:8} | {row[2]}")
EOF

# If trades 7215356800 and 7209663812 are still open but shouldn't be,
# manually mark them closed (they may have filled while monitoring was down)
```

---

## Testing Checklist

### ✅ Test 1: Agent Opens Trade

1. **Wait for agent to open new position**
2. **Check activities table:**
   ```sql
   SELECT activity_type, summary, trade_type, activity_source
   FROM activities
   WHERE config_id = 'bb2560fd-b053-464f-8a58-8e254e4d36fa'
   ORDER BY created_at DESC
   LIMIT 5;
   ```
3. **Expected**: See `trade_entry_long/short` with `trade_type='aster'` and `activity_source IN ('agent_tool', 'aster_service')`
4. **Check Timeline**: Activity icon should appear on timeline

### ✅ Test 2: Agent Closes Trade Manually

1. **Wait for agent to close position manually**
2. **Check activities table** (same query as above)
3. **Expected**: See `trade_win` or `trade_loss` with `trade_type='aster'` and `activity_source IN ('agent_tool', 'aster_service')`
4. **Check Timeline**: Closure activity (green/red arrow) should appear

### ✅ Test 3: TP Order Triggers

1. **Wait for TP to trigger** (or manually move market to TP price)
2. **Check monitor logs:**
   ```bash
   pm2 logs monitor-aster-orders --lines 50 | grep "Take Profit"
   ```
3. **Expected**: See "Take Profit FILLED for trade {batch_id}"
4. **Check activities table** (same query)
5. **Expected**: See `trade_win` with `activity_source='aster_monitor'` and `close_reason='take_profit'`
6. **Check Timeline**: TP closure should appear

### ✅ Test 4: SL Order Triggers

1. **Wait for SL to trigger** (or manually move market to SL price)
2. **Check monitor logs** (same as Test 3)
3. **Expected**: See "Stop Loss FILLED for trade {batch_id}"
4. **Check activities table** (same query)
5. **Expected**: See `trade_loss` with `activity_source='aster_monitor'` and `close_reason='stop_loss'`
6. **Check Timeline**: SL closure should appear

### ✅ Test 5: Balance Chart Updates

1. **Open Timeline**: `/view/{config_id}`
2. **Check balance series API:**
   ```bash
   curl "http://localhost:8000/api/v2/activities/bb2560fd-b053-464f-8a58-8e254e4d36fa/balance-series" \
     -H "Authorization: Bearer {token}"
   ```
3. **Expected**: Balance points include Aster trade P&L
4. **Check Chart**: Equity line should move with trades

### ✅ Test 6: Timeline Rendering

1. **Open Timeline**: `/view/bb2560fd-b053-464f-8a58-8e254e4d36fa`
2. **Verify All Activity Types Visible**:
   - 🔵 Long entries (blue triangle up)
   - 🔴 Short entries (red triangle down)
   - 🟢 Trade wins (green up arrow)
   - 🔴 Trade losses (red down arrow)
   - 🟡 Strategy updates (gold wrench)
   - 🔵 Market queries (blue bar chart)
   - ⚪ Agent waits (gray clock)
   - 💜 Agent thoughts (purple bubble)
3. **Click activities** - Details panel should open
4. **Zoom controls** - 1h/4h/1d/1w/All should work

---

## Activity Sources Reference

| Activity Source | Description | Logs When |
|-----------------|-------------|-----------|
| `agent_tool` | MCP tool calls | Agent uses MCP tools (execute_trade, close_position, etc.) |
| `aster_service` | Aster service direct | API calls to Aster service (non-MCP path) |
| `aster_monitor` | TP/SL monitor | Background monitor detects order fills |
| `agent` | Agent streaming | Agent streams analysis/thoughts via Redis |

**Important**: Both `agent_tool` and `aster_service` can log the same event (e.g., trade entry). The MCP tool logs it when agent calls the tool, and the service logs it when executing the actual trade. This is intentional - if one fails, the other still logs.

---

## Monitoring Commands

### Check PM2 Services
```bash
pm2 status
pm2 logs monitor-aster-orders --lines 50
pm2 logs agent-bb2560fd-b053-464f-8a58-8e254e4d36fa --lines 50
```

### Check Activity Counts
```bash
source .venv/bin/activate
python3 <<'EOF'
from core.common.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                activity_type,
                activity_source,
                trade_type,
                COUNT(*) as count
            FROM activities
            WHERE config_id = 'bb2560fd-b053-464f-8a58-8e254e4d36fa'
            GROUP BY activity_type, activity_source, trade_type
            ORDER BY count DESC
        """)

        print("Activity Summary:")
        print(f"{'Type':25} {'Source':20} {'Trade Type':12} {'Count':>6}")
        print("-" * 70)
        for row in cur.fetchall():
            print(f"{row[0]:25} {row[1]:20} {row[2] or 'N/A':12} {row[3]:6}")
EOF
```

### Check Open Trades
```bash
source .venv/bin/activate
python3 <<'EOF'
from core.common.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                batch_id,
                symbol,
                stop_loss_order_id,
                take_profit_order_id,
                created_at
            FROM live_trades
            WHERE config_id = 'bb2560fd-b053-464f-8a58-8e254e4d36fa'
            AND provider = 'aster'
            AND closed_at IS NULL
            ORDER BY created_at DESC
        """)

        print("Open Aster Trades:")
        for row in cur.fetchall():
            print(f"  Batch: {row[0]}")
            print(f"  Symbol: {row[1]}")
            print(f"  SL Order: {row[2]}")
            print(f"  TP Order: {row[3]}")
            print(f"  Opened: {row[4]}")
            print()
EOF
```

---

## Known Issues & Future Enhancements

### Known Issues
- None currently identified

### Future Enhancements
1. **Scheduled Bot Logging** (P1 - separate task)
   - Add activity logging to paper trading service
   - Add activity logging to Symphony service
2. **Decision Logging** (P1)
   - Log `decision_made` activity in decision engine
   - Shows AI reasoning before trades
3. **WebSocket Activity Streaming** (P2)
   - Real-time activity push vs 10s polling
4. **Activity Search & Filter** (P2)
   - UI search by symbol, date, type
5. **Activity Analytics** (P3)
   - Heatmaps, pattern detection

---

## Rollback Instructions

If issues occur, rollback:

```bash
# Stop monitor
pm2 stop monitor-aster-orders
pm2 delete monitor-aster-orders

# Revert code changes
cd /home/sev/ggbot
git checkout agent/mcp_server.py
git checkout agent/run_agent.py
git checkout trading/live/aster_service_v3.py
rm scripts/monitor_aster_orders.py

# Restart agent
pm2 restart agent-bb2560fd-b053-464f-8a58-8e254e4d36fa
```

---

## Success Criteria

✅ **Implementation Complete When**:
1. Agent trades appear on timeline (entry + exit)
2. TP/SL automatic closures appear on timeline
3. Balance chart updates with Aster P&L
4. Monitor service runs without errors
5. All activity types render correctly
6. Click interactions work (details panel)

---

**Next Steps**: Follow Deployment Instructions → Run Testing Checklist → Monitor for 24 hours

**Documentation**: See `DOCS/ACTIVITY_LOGGING_COMPLETE_MAP.md` for comprehensive reference
