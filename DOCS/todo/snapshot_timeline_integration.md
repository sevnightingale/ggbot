# Snapshot-Based Timeline Chart Integration

**Date**: 2025-11-14
**Status**: Planning
**Objective**: Replace inefficient API-based timeline chart with snapshot-based system for better performance and proper time axis

---

## Problem Statement

**Current System Issues:**
1. **API Calls on Every Poll**: Backend calls Symphony/Aster APIs every 10 seconds to reconstruct P&L
2. **Misleading Time Axis**: Chart doesn't have proper time spacing - activities appear equally spaced regardless of actual time gaps
3. **Performance**: Slow, wastes API quota, adds latency

**Current Behavior:**
- Timeline chart queries `/api/v2/activities/{config_id}/balance-series` which makes API calls
- Chart plots activities as points with reconstructed P&L from trade history
- No true continuous balance visibility between activities

---

## Solution Architecture

### **Core Concept**

**Activities carry snapshot values** - When logging an activity, capture the most recent snapshot balance/P&L:

```python
# When logging activity
latest_snapshot = get_latest_snapshot(config_id)

log_activity(
    config_id=config_id,
    activity_type="trade_entry_long",
    summary="Opened BTC long",
    details={...},
    account_balance=latest_snapshot.current_balance,  # NEW
    account_pnl=latest_snapshot.total_pnl  # NEW
)
```

**Chart combines snapshots + activities** - Both contribute to timeline:
```
10:00am → $100 (snapshot)
10:03am → $100 (activity, carries 10:00am value)
10:05am → $110 (snapshot, JUMP!)
10:07am → $110 (activity, carries 10:05am value)
10:10am → $105 (snapshot, JUMP!)
```

**Visual Result**: Step-function chart with proper time X-axis
- Horizontal during activities (carry last snapshot value)
- Vertical jumps at 5-minute intervals (new snapshot)
- Activities appear at exact timestamps
- All points clickable

---

## Workstream 1: Activities Table Enhancement

**Assigned to**: CC Instance 1

### **Database Migration**

**Add columns to activities table:**
```sql
-- Add new columns
ALTER TABLE activities
ADD COLUMN account_balance NUMERIC(20, 8),
ADD COLUMN account_pnl NUMERIC(20, 8);

-- Add index for chart queries
CREATE INDEX idx_activities_chart_data
ON activities(config_id, created_at, account_balance);

-- Add comment
COMMENT ON COLUMN activities.account_balance IS
'Balance from most recent account snapshot at activity creation time';

COMMENT ON COLUMN activities.account_pnl IS
'Total P&L from most recent account snapshot at activity creation time';
```

**Migration file location**: `database/migrations/add_snapshot_values_to_activities.sql`

### **Activity Logging Updates**

**Helper function to get latest snapshot:**
```python
# core/services/activity_service.py or similar

def get_latest_snapshot(config_id: str) -> Optional[AccountSnapshot]:
    """Get most recent account snapshot for a config (within last 10 minutes)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT current_balance, total_pnl
                FROM account_snapshots
                WHERE config_id = %s
                  AND timestamp > NOW() - INTERVAL '10 minutes'
                ORDER BY timestamp DESC
                LIMIT 1
            """, (config_id,))
            result = cur.fetchone()

            if result:
                return {
                    'current_balance': float(result[0]) if result[0] else None,
                    'total_pnl': float(result[1]) if result[1] else None
                }
            return None
```

**Code locations to update** (search for `INSERT INTO activities`):

1. **core/services/activity_logger.py** (if exists) - Main logging utility
2. **agent/mcp_server.py** - Agent activity logging
3. **ggbot.py** - Orchestrator activity logging
4. **decision/engine_v2.py** - Decision logging
5. **trading/paper/supabase_service.py** - Trade execution logging
6. **trading/live/symphony_service.py** - Symphony trade logging
7. **trading/live/aster_service_v3.py** - Aster trade logging

**Pattern to apply:**
```python
# Before (old)
cur.execute("""
    INSERT INTO activities (config_id, activity_type, summary, details, ...)
    VALUES (%s, %s, %s, %s, ...)
""", (config_id, activity_type, summary, details, ...))

# After (new)
snapshot = get_latest_snapshot(config_id)
cur.execute("""
    INSERT INTO activities (config_id, activity_type, summary, details,
                           account_balance, account_pnl, ...)
    VALUES (%s, %s, %s, %s, %s, %s, ...)
""", (config_id, activity_type, summary, details,
      snapshot['current_balance'] if snapshot else None,
      snapshot['total_pnl'] if snapshot else None,
      ...))
```

### **Testing Checklist**

- [ ] Migration runs successfully (test on local DB first)
- [ ] Index created correctly
- [ ] Activity logging captures snapshot values
- [ ] NULL values handled gracefully (no snapshot available)
- [ ] Verify snapshot values match expectations (spot check)
- [ ] Check performance impact (should be minimal - single indexed query)

---

## Workstream 2: Chart Integration

**Assigned to**: CC Instance 2

### **Backend: New Snapshot Endpoint**

**Create new file**: `api/snapshots.py`

```python
"""
Snapshot-based timeline endpoints.

Efficient alternative to activities endpoints that make API calls.
Uses account_snapshots table for performance.
"""

from fastapi import APIRouter, HTTPException
from typing import List
from core.common.db import get_db_connection

router = APIRouter(prefix="/api/v2/snapshots", tags=["snapshots"])


@router.get("/{config_id}/balance-series")
async def get_snapshot_balance_series(config_id: str):
    """
    Get balance/P&L timeline from snapshots + activities.

    Returns unified timeline combining:
    - 5-minute snapshots (continuous background)
    - Activities with snapshot values (exact timestamps)

    Response format matches /api/v2/activities/{config_id}/balance-series
    for drop-in frontend compatibility.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Verify config exists
                cur.execute("""
                    SELECT trading_mode, created_at FROM configurations
                    WHERE config_id = %s
                """, (config_id,))
                config = cur.fetchone()

                if not config:
                    raise HTTPException(status_code=404, detail="Config not found")

                trading_mode = config[0]
                config_created = config[1]

                # Get snapshots
                cur.execute("""
                    SELECT timestamp,
                           COALESCE(current_balance, total_pnl) as balance
                    FROM account_snapshots
                    WHERE config_id = %s
                    ORDER BY timestamp ASC
                """, (config_id,))
                snapshots = cur.fetchall()

                # Get activities with snapshot values
                cur.execute("""
                    SELECT created_at,
                           COALESCE(account_balance, account_pnl) as balance
                    FROM activities
                    WHERE config_id = %s
                      AND (account_balance IS NOT NULL OR account_pnl IS NOT NULL)
                    ORDER BY created_at ASC
                """, (config_id,))
                activities = cur.fetchall()

        # Combine into timeline
        timeline = []

        # Add snapshots
        for snap in snapshots:
            timeline.append({
                "timestamp": snap[0].isoformat(),
                "balance": float(snap[1]) if snap[1] else 0
            })

        # Add activities
        for act in activities:
            timeline.append({
                "timestamp": act[0].isoformat(),
                "balance": float(act[1]) if act[1] else 0
            })

        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'])

        # Calculate current and initial balance
        current_balance = timeline[-1]['balance'] if timeline else 0
        initial_balance = timeline[0]['balance'] if timeline else 0

        # Handle Symphony (balance = NULL, show P&L)
        mode = "pnl" if trading_mode == "symphony" else "balance"

        return {
            "status": "success",
            "balance_series": timeline,
            "current_balance": current_balance,
            "initial_balance": initial_balance,
            "mode": mode
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Register router in ggbot.py:**
```python
from api import snapshots
app.include_router(snapshots.router)
```

### **Frontend: Update tv-timeline.tsx**

**Change data fetching (lines ~285-289):**
```typescript
// OLD
const [balanceSeriesRes, activitiesRes, metadataRes] = await Promise.all([
  fetch(`/api/v2/activities/${configId}/balance-series?mode=pnl`, { headers }),
  fetch(`/api/v2/activities/${configId}`, { headers }),
  fetch(`/api/v2/activities/${configId}/metadata`, { headers }),
]);

// NEW
const [balanceSeriesRes, activitiesRes, metadataRes] = await Promise.all([
  fetch(`/api/v2/snapshots/${configId}/balance-series`, { headers }),  // Changed!
  fetch(`/api/v2/activities/${configId}`, { headers }),                // Unchanged
  fetch(`/api/v2/activities/${configId}/metadata`, { headers }),       // Unchanged for now
]);
```

**Simplify chart data logic (lines ~329-383):**
```typescript
// BEFORE: Complex merge with carry-forward logic
// ... 50+ lines of event merging ...

// AFTER: Simple combine and sort
const balancePoints: BalancePoint[] = balanceSeries.balance_series || [];
const activities: Activity[] = activitiesData.activities || [];

// Combine snapshots + activities into chart data
const chartData: LineData[] = balancePoints
  .map(point => ({
    time: Math.floor(new Date(point.timestamp).getTime() / 1000) as Time,
    value: point.balance
  }))
  .sort((a, b) => {
    const timeA = typeof a.time === 'number' ? a.time : parseFloat(a.time as string);
    const timeB = typeof b.time === 'number' ? b.time : parseFloat(b.time as string);
    return timeA - timeB;
  });
```

**Keep markers and activity mapping unchanged** (lines ~407-497) - this already works!

### **Testing Checklist**

- [ ] Backend endpoint returns data in correct format
- [ ] Frontend fetches from new endpoint successfully
- [ ] Chart renders with proper time spacing (verify 5-min gaps)
- [ ] Activities appear at exact timestamps
- [ ] Clicking activities opens detail sheet
- [ ] Markers show up correctly (trades, thoughts, queries)
- [ ] Hover tooltip works
- [ ] Chart performs well (no API calls during poll)
- [ ] Test with all trading modes:
  - [ ] Paper (balance should work)
  - [ ] Aster (balance should work)
  - [ ] Symphony (P&L only, balance NULL)

---

## Integration Testing

**After both workstreams complete:**

1. **Data Validation**:
   - Activities have non-NULL snapshot values
   - Snapshot values match expected timeline
   - Chart shows activities between snapshots with correct values

2. **Visual Validation**:
   - Chart has proper time X-axis (zoom in/out, check spacing)
   - Step-function appearance (flat → jump → flat)
   - Activities clickable and showing correct data

3. **Performance**:
   - No API calls during 10-second polls (check network tab)
   - Chart updates smoothly
   - No lag when clicking activities

4. **Edge Cases**:
   - Bot with no snapshots yet (new bot)
   - Bot with no activities yet
   - Long wait periods (2+ hours between activities)
   - Symphony bot (NULL balance fields)

---

## Rollback Plan

**If issues arise**, revert frontend easily:

```typescript
// In tv-timeline.tsx, change one line:
const USE_OLD_ENDPOINT = true; // Toggle here

const balanceEndpoint = USE_OLD_ENDPOINT
  ? `/api/v2/activities/${configId}/balance-series?mode=pnl`
  : `/api/v2/snapshots/${configId}/balance-series`;
```

**Database changes** are additive (new columns) - existing code continues to work.

---

## Success Criteria

✅ Chart shows proper time-based X-axis with 5-minute intervals
✅ Activities appear at exact timestamps (clickable)
✅ No API calls to Symphony/Aster during chart polls
✅ Performance improved (faster loads, less latency)
✅ Step-function visual (flat segments + vertical jumps)
✅ Works for all trading modes (paper, symphony, aster)

---

## Future Enhancements

**After this is stable:**
- Add real-time snapshot updates (WebSocket push instead of 5-min polling)
- Add balance change annotations ("Balance +$50 from trade")
- Add performance comparison view (old vs new endpoint side-by-side)
- Optimize query with materialized view if needed

---

**Document Version**: 1.0
**Last Updated**: 2025-11-14
