# Bug Report: Numeric Field Overflow & Config Sync Issues

**Date**: 2025-12-01
**Reporter**: Claude Code (Session investigating Symphony integration)
**Priority**: HIGH

---

## Issue 1: Numeric Field Overflow in account_snapshots

### Error Message
```
ERROR | __main__:_save_snapshot:298 - Failed to save snapshot for 82d3b829-b1fd-49e6-b8d4-b9506a7f6d0d: numeric field overflow
DETAIL:  A field with precision 5, scale 4 must round to an absolute value less than 10^1.
```

### Root Cause
**Data type mismatch between Symphony service and database schema.**

The `account_snapshots.win_rate` column is defined as `NUMERIC(5,4)`:
- Max value: **9.9999**
- Min value: **-9.9999**

But the Symphony service returns win_rate as a **percentage (0-100)**:

**File**: `trading/live/symphony_service.py` (around line 626)
```python
win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
```

This returns `60.0` for 60% win rate, which exceeds the 9.9999 limit.

### Code Flow
```
symphony_service.get_account_metrics()
    → Returns: {'win_rate': 60.0, ...}  # PERCENTAGE (0-100)

symphony_adapter.get_current_snapshot()
    → Line 55: win_rate = Decimal(str(metrics.get('win_rate', 0)))  # Takes raw value
    → Creates AccountSnapshot with win_rate=60.0

universal_account_monitor._save_snapshot()
    → Tries to INSERT into account_snapshots
    → PostgreSQL rejects: NUMERIC(5,4) cannot hold 60.0
```

### Comparison with Paper Trading
Paper adapter correctly calculates win_rate as a **decimal (0-1)**:

**File**: `core/monitoring/adapters/paper_adapter.py` (line 58)
```python
win_rate = Decimal(win_trades) / Decimal(total_trades) if total_trades > 0 else Decimal('0')
```
Returns `0.60` for 60% win rate - fits in NUMERIC(5,4).

### Solution Options

**Option A: Fix Symphony Service (Recommended)**
Change `symphony_service.py` to return decimal like paper trading:
```python
# Before
win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0

# After
win_rate = (win_count / total_trades) if total_trades > 0 else 0
```
*Note*: This may affect other consumers of this data (check dashboard, SSE stream).

**Option B: Fix Symphony Adapter**
Divide by 100 in the adapter:
```python
# Before
win_rate = Decimal(str(metrics.get('win_rate', 0)))

# After
raw_rate = metrics.get('win_rate', 0)
win_rate = Decimal(str(raw_rate / 100)) if raw_rate else Decimal('0')
```

**Option C: Alter Database Schema**
Change column to `NUMERIC(6,4)` to allow 0-100:
```sql
ALTER TABLE account_snapshots ALTER COLUMN win_rate TYPE NUMERIC(6,4);
```
*Note*: This breaks consistency with paper_adapter expectations.

### Affected Configs
Any Symphony (live trading) bot with win_rate >= 10%:
- Config: `82d3b829-b1fd-49e6-b8d4-b9506a7f6d0d`
- Error occurs every ~5 minutes during account monitoring

---

## Issue 2: Config Auto-Save Intermittent / Frontend Cache Issues

### User Report
> "the config auto saving is intermittent sometimes it works sometimes it doesn't and the frontend doesn't align, like I need to refresh the page sometimes, something is getting cached in the browser or something"

### Observations from Logs
Config `8463397e-b0b0-4f94-a0d1-615624bc5e16` had **40+ update_config calls in 3 minutes**:
```
2025-12-01 14:29:09 | INFO | core.services.config_service:update_config:495 - Updated config 8463397e...
2025-12-01 14:29:09 | INFO | core.services.config_service:update_config:495 - Updated config 8463397e...
2025-12-01 14:29:09 | INFO | core.services.config_service:update_config:495 - Updated config 8463397e...
... (continues for 40+ entries over ~3 minutes)
```

### Possible Causes to Investigate

#### 1. Frontend Debouncing Issue
- Auto-save may be triggering on every keystroke instead of debounced
- Check: `frontend/` components for config editing
- Look for: onChange handlers, debounce implementations

#### 2. Optimistic Updates Not Syncing
- Frontend may show optimistic update but backend save fails silently
- Check: API response handling in frontend
- Look for: Error handling in config save mutations

#### 3. SSE Stream Conflicts
- Dashboard SSE stream may be pushing stale config state
- Frontend receives old data and overwrites local state
- Check: `core/sse/dashboard_data.py` for config data in stream

#### 4. Browser Cache / Service Worker
- Next.js may be caching API responses
- Check: Cache-Control headers on `/api/v2/configurations/*` endpoints
- Look for: Service worker registration, stale-while-revalidate patterns

#### 5. Race Conditions in Config Service
- Multiple concurrent updates may cause last-write-wins issues
- Check: `core/services/config_service.py` for locking/versioning
- The 40+ rapid updates in logs suggest frontend is spamming saves

### Files to Investigate

**Backend**:
- `core/services/config_service.py` - `update_config()` function
- `ggbot.py` - Config update API endpoints
- `core/sse/dashboard_data.py` - SSE stream data

**Frontend**:
- `frontend/app/forge/` - Bot configuration UI
- `frontend/lib/api-client.ts` - API calls
- `frontend/hooks/` - Any useConfig or similar hooks
- `frontend/components/` - Config form components

### Suggested Investigation Steps

1. **Check if saves are actually succeeding**:
   ```sql
   SELECT updated_at, config_data->>'updated_field'
   FROM configurations
   WHERE config_id = '8463397e-b0b0-4f94-a0d1-615624bc5e16'
   ORDER BY updated_at DESC;
   ```

2. **Add response logging to frontend**:
   - Log the response from config save API calls
   - Check if errors are being swallowed

3. **Check for debouncing in frontend**:
   - Search for `debounce`, `throttle`, `useDebouncedCallback`
   - Verify auto-save delay is appropriate (300-500ms minimum)

4. **Check SSE stream for config data**:
   - Does dashboard stream include config state?
   - Could stale stream data overwrite user edits?

5. **Test with Network tab**:
   - Open browser DevTools → Network
   - Make config change
   - Verify single PUT/PATCH request (not multiple)
   - Check response status and body

---

## Database Schema Reference

### account_snapshots Columns with Precision Constraints
```
win_rate           NUMERIC(5,4)   -- Max 9.9999 - THE PROBLEM
sharpe_ratio       NUMERIC(10,4)  -- Max 999999.9999
balance_change_pct NUMERIC(10,4)  -- Max 999999.9999
```

### Full Schema
```sql
CREATE TABLE account_snapshots (
    snapshot_id uuid PRIMARY KEY,
    config_id uuid NOT NULL,
    user_id uuid NOT NULL,
    trading_mode varchar,
    timestamp timestamptz,
    current_balance numeric(20,8),
    available_balance numeric(20,8),
    margin_used numeric(20,8),
    total_pnl numeric(20,8),
    realized_pnl numeric(20,8),
    unrealized_pnl numeric(20,8),
    total_trades integer,
    win_trades integer,
    loss_trades integer,
    win_rate numeric(5,4),          -- PROBLEM: Can only hold 0-9.9999
    open_positions integer,
    position_value numeric(20,8),
    total_exposure numeric(20,8),
    avg_win numeric(20,8),
    avg_loss numeric(20,8),
    largest_win numeric(20,8),
    largest_loss numeric(20,8),
    sharpe_ratio numeric(10,4),
    max_drawdown numeric(20,8),
    raw_data jsonb,
    balance_change_pct numeric(10,4),
    is_heartbeat boolean,
    created_at timestamptz
);
```

---

## Quick Fix for Immediate Relief

Apply this to `symphony_adapter.py` to prevent crashes while proper fix is implemented:

```python
# Line 55 - Add division by 100 if value > 1
raw_rate = metrics.get('win_rate', 0)
# Symphony returns 0-100 percentage, DB expects 0-1 decimal
win_rate = Decimal(str(raw_rate / 100)) if raw_rate > 1 else Decimal(str(raw_rate))
```

This handles both formats safely (percentage or decimal).

---

## Related Files

| File | Purpose |
|------|---------|
| `trading/live/symphony_service.py` | Source of win_rate calculation |
| `core/monitoring/adapters/symphony_adapter.py` | Adapter that passes win_rate to snapshot |
| `core/monitoring/adapters/paper_adapter.py` | Reference for correct decimal format |
| `core/monitoring/universal_account_monitor.py` | Where INSERT fails (line 298) |
| `core/services/config_service.py` | Config update service |
| `ggbot.py` | API endpoints |

---

*Report generated by Claude Code during Symphony Agentic Funds integration session.*
