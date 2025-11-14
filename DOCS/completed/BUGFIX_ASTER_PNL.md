# Bug Fix: Aster P&L Chart Missing Trades

**Date**: 2025-11-13
**Issue**: ggAster bot timeline showing incorrect P&L (missing 26 out of 43 trades)
**Root Cause**: Using wrong AsterDEX API endpoint
**Status**: ✅ FIXED

---

## Problem

The timeline chart was showing:
- **Displayed P&L**: $-43.52 (wrong)
- **Actual P&L**: $-5.89 (correct)
- **Missing**: 26 winning trades from Nov 4-6

Console logs showed P&L updates starting from Nov 7, skipping 4 days of trading history.

---

## Root Cause

**OLD Implementation** (api/activities.py):
```python
# Used userTrades endpoint
aster_trades_raw = await aster_service.get_user_trades(limit=1000)
```

**Problem**: `/fapi/v3/userTrades` endpoint only returns **~7 days of recent trades**:
- Returned: 17 trades from Nov 7-8
- Missing: 26 trades from Nov 4-6 (including all the winning trades!)

---

## Solution

**NEW Implementation**:
```python
# Use income history endpoint
income_records = await aster_service.get_income_history(
    income_type="REALIZED_PNL",
    start_time=int(config_created_at.timestamp() * 1000),
    limit=1000
)
```

**Why it works**: `/fapi/v3/income` endpoint provides **complete P&L history**:
- Returns all 43 P&L records from bot creation
- Includes Nov 4-6 winning trades ($37.63 peak on Nov 5)
- Accurate cumulative P&L: $-5.89

---

## Changes Made

### 1. Added `get_income_history()` method
**File**: `trading/live/aster_service_v3.py:1229-1287`

New method to query `/fapi/v3/income` endpoint with proper authentication.

### 2. Updated balance series endpoint
**File**: `api/activities.py:246-271`

Changed from `get_user_trades()` to `get_income_history()` for Aster bots.

### 3. Updated metadata endpoint
**File**: `api/activities.py:474-505`

Changed metrics calculation to use income records instead of user trades.

### 4. Restarted ggbot service
```bash
pm2 restart ggbot
```

---

## Verification

### Before Fix:
```
Total trades: 17
Cumulative P&L: $-43.52
Missing: All Nov 4-6 trades
```

### After Fix:
```
Total trades: 43
Cumulative P&L: $-5.89
Complete history: ✅ All trades from Nov 3 onwards
```

### Test Command:
```bash
python scripts/test_aster_income.py
```

---

## Impact

- ✅ Timeline chart now shows accurate P&L progression
- ✅ All 43 trades visible (not just recent 17)
- ✅ Correct win rate and performance metrics
- ✅ No breaking changes (backward compatible)

---

## Notes

- **Applies to**: Aster bots only (trading_mode = 'aster')
- **Backward compatible**: Paper and Symphony bots unaffected
- **API limit**: 1000 records (sufficient for most bots)
- **Time range**: Can query from bot creation timestamp
- **Performance**: No noticeable impact (single API call)

---

## Future Considerations

If a bot exceeds 1000 P&L records, implement pagination:
```python
# Paginated income history (if needed in future)
all_income = []
last_id = None
while True:
    batch = await get_income_history(limit=1000, from_id=last_id)
    if not batch: break
    all_income.extend(batch)
    last_id = batch[-1]['tranId']
```

Currently not needed (most bots have <100 trades).
