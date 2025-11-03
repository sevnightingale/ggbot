# Activity Timeline - Consolidated Planning Document

**Status**: Ready for Implementation
**Timeline**: 7-10 days
**Prerequisites**: Canvas viewer already built at `/view/[config_id]` with mock data

---

## Executive Summary

Transform the existing Canvas-based Activity Timeline viewer into a production-ready feature that visualizes the complete lifecycle of bot/agent trading activities. This consolidates previous "Trade Timeline" and "Agent Activity" concepts into one unified system powered by a single `activities` table.

**Key Innovation**: Every bot action becomes a clickable icon on the performance chart. Click a trade to see its entire story - from market analysis to entry decision to monitoring to exit - all highlighted and grouped together.

**Competition Focus**: The initial implementation includes special features for the Aster Vibe Trading Competition submission:
- **"View Configuration" modal**: Shows the agent's full strategy definition conversation + final strategy (demonstrates transparency and reasoning)
- **Active Positions section**: Displays current open positions at the bottom of the timeline (provides real-time proof of live trading)
- These features will be submitted alongside the activity timeline to showcase a single agent live trading on AsterDEX

---

## Vision

### What We're Building

A **universal activity visualization system** that works for ALL config types:
- ✅ Agentic bots (autonomous AI agents)
- ✅ Scheduled bots (traditional time-based trading)
- ✅ Signal validation bots (ggShot integration)

### Core Features

**1. Interactive Performance Chart**
- Balance/equity curve with overlaid activity icons
- Zoom levels: 1h, 4h, 1d, 1w, All
- Drag/pan scrolling through time
- Icon grouping at zoomed-out views

**2. Trade Lifecycle Linking**
- All activities related to a trade share `trade_id`
- Click trade icon → highlights all related activities + filters side panel
- Visual connection showing: Market Query → Entry Decision → Monitoring → Exit
- Full narrative of "why this trade happened and how it played out"

**3. Rich Activity Details**
- Side panel with expandable cards
- Activity-specific rendering (market data tabs, trade details, agent reasoning)
- Markdown support for analysis/observations
- Real-time updates via SSE

**4. Universal Data Model**
- One `activities` table for everything
- Consistent activity types across bot types
- Simple API: `GET /activities?config_id=X`

---

## Database Architecture

### Unified `activities` Table

```sql
CREATE TABLE activities (
    activity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID NOT NULL REFERENCES configurations(config_id),
    user_id UUID NOT NULL,

    -- Classification
    activity_type TEXT NOT NULL,
    -- Common types across all bot types:
    --   'market_query' - Data extraction/query
    --   'decision_made' - AI decision (enter/wait/exit)
    --   'trade_entry_long' - Long position opened
    --   'trade_entry_short' - Short position opened
    --   'trade_exit' - Position closed
    --   'agent_wait' - Agent waiting period
    --   'analysis' - Market analysis (agent)
    --   'reasoning' - Decision reasoning (agent)
    --   'observation' - Trade observation/learning
    --   'strategy_updated' - Strategy modification
    --   'position_adjusted' - Position size/SL/TP change

    activity_source TEXT NOT NULL,
    -- Values: 'agent_tool', 'scheduled_bot', 'signal_validation', 'system_event', 'user_action'

    -- Content
    summary TEXT NOT NULL,        -- Brief title for timeline icon (50 chars max)
    details JSONB NOT NULL,       -- Full structured data (activity-type specific)

    -- Optional Linking (NULL if not applicable)
    trade_id UUID,                -- Links to paper_trades.trade_id or live_trades.batch_id
    trade_type TEXT,              -- 'paper' | 'live' | 'aster' (if trade_id is set)
    decision_id UUID,             -- Links to decisions.decision_id (if activity is a decision)
    related_symbol TEXT,          -- Optional symbol context (e.g., "BTC/USDT")

    -- Display Metadata
    priority INT DEFAULT 2 CHECK (priority IN (1,2,3)),
    -- Priority mapping (controls GROUPING behavior, not visibility):
    --   1 = Never consolidate (trades, critical actions) - Each activity shows as separate icon
    --   2 = Can consolidate (analysis, queries, decisions) - Group by type within time windows
    --   Note: All activity types always visible at all zoom levels (grouped, not hidden)

    importance INT DEFAULT 5 CHECK (importance BETWEEN 1 AND 10),
    -- User-facing filtering (1=low, 10=critical)
    -- Allows users to filter timeline: "Show only importance >= 7"

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Performance Indexes
    CONSTRAINT idx_activities_config_time_pk PRIMARY KEY (config_id, created_at DESC, activity_id),
    INDEX idx_activities_trade (trade_id) WHERE trade_id IS NOT NULL,
    INDEX idx_activities_type (config_id, activity_type, created_at DESC),
    INDEX idx_activities_priority (config_id, priority, created_at DESC),
    INDEX idx_activities_decision (decision_id) WHERE decision_id IS NOT NULL
);

-- Row Level Security
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;

CREATE POLICY activities_user_isolation ON activities
    FOR ALL USING (user_id = auth.uid());
```

### Why This Design?

**Simplicity**: One table, one query, no joins needed for timeline
**Flexibility**: JSONB `details` field accommodates any activity type
**Performance**: Primary key optimized for time-range queries
**Linking**: Optional foreign keys enable trade lifecycle grouping
**Universal**: Works for agents, scheduled bots, signal validation equally

---

## Implementation Phases

### Phase 1: Database & Infrastructure (2-3 days)

#### Task 1.1: Create `activities` Table
- [ ] Write migration: `database/migrations/create_activities_table.sql`
- [ ] Add indexes for performance
- [ ] Enable RLS policy
- [ ] Run migration in Supabase
- [ ] Test basic INSERT/SELECT operations

#### Task 1.2: Activity Insertion Helper
**File**: `core/common/activity_logger.py`

```python
from core.common.db import get_db_connection
import json
from typing import Optional, Dict, Any

async def log_activity(
    config_id: str,
    user_id: str,
    activity_type: str,
    activity_source: str,
    summary: str,
    details: Dict[str, Any],
    trade_id: Optional[str] = None,
    trade_type: Optional[str] = None,
    decision_id: Optional[str] = None,
    related_symbol: Optional[str] = None,
    priority: int = 2,
    importance: int = 5
) -> str:
    """
    Universal activity logger for all bot types.

    Returns: activity_id
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO activities
                (config_id, user_id, activity_type, activity_source, summary, details,
                 trade_id, trade_type, decision_id, related_symbol, priority, importance)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING activity_id
            """, (
                config_id, user_id, activity_type, activity_source, summary,
                json.dumps(details), trade_id, trade_type, decision_id,
                related_symbol, priority, importance
            ))
            activity_id = cur.fetchone()[0]
            conn.commit()
            return activity_id

# Activity type to priority mapping
# Priority controls GROUPING behavior:
#   1 = Never consolidate (each activity = separate icon, no time-based grouping)
#   2 = Can consolidate (group by type within time buckets, show count badge)
ACTIVITY_PRIORITY = {
    # Priority 1 - Never consolidate (always show individually)
    'trade_entry_long': 1,
    'trade_entry_short': 1,
    'trade_exit': 1,
    'position_adjusted': 1,
    'strategy_updated': 1,

    # Priority 2 - Can consolidate (group by type + time)
    'market_query': 2,
    'decision_made': 2,
    'analysis': 2,
    'reasoning': 2,
    'agent_wait': 2,
    'observation': 2,
    'observation_recorded': 2,
    'plan': 2,
}
```

**Checklist**:
- [ ] Create `core/common/activity_logger.py`
- [ ] Implement `log_activity()` function
- [ ] Add activity type → priority mapping
- [ ] Add error handling and validation
- [ ] Write unit tests for activity insertion

---

### Phase 2: Orchestrator Integration (2-3 days)

#### Task 2.1: Scheduled Bot Activity Logging
**File**: `ggbot.py` (V2 Orchestrator)

```python
from core.common.activity_logger import log_activity, ACTIVITY_PRIORITY

async def _run_extraction_v2(config, user_id):
    """Log market query activity"""
    result = await extraction_engine.extract(...)

    # Log extraction activity
    await log_activity(
        config_id=config.config_id,
        user_id=user_id,
        activity_type='market_query',
        activity_source='scheduled_bot',
        summary=f"Queried {symbol}: {len(result['indicators'])} indicators",
        details={
            'symbol': symbol,
            'timeframe': config.extraction.timeframe,
            'indicators': result['indicators'],
            'market_intelligence': result.get('market_intelligence', {}),
            'extraction_time_ms': result.get('processing_time_ms')
        },
        related_symbol=symbol,
        priority=ACTIVITY_PRIORITY['market_query'],
        importance=6
    )

    return result

async def _run_decision_v2(config, user_id, extraction_result):
    """Log decision activity"""
    decision = await decision_engine.make_decision(...)

    # Log decision activity
    await log_activity(
        config_id=config.config_id,
        user_id=user_id,
        activity_type='decision_made',
        activity_source='scheduled_bot',
        summary=f"{decision['action'].upper()}: {decision['reasoning'][:50]}...",
        details={
            'action': decision['action'],
            'confidence': decision['confidence'],
            'reasoning': decision['reasoning'],
            'symbol': symbol,
            'active_trade_context': decision.get('active_trade')
        },
        decision_id=decision['decision_id'],
        trade_id=decision.get('active_trade_id'),  # If managing existing trade
        trade_type=config.trading_mode,
        related_symbol=symbol,
        priority=ACTIVITY_PRIORITY['decision_made'],
        importance=7
    )

    return decision

async def _run_trading_v2(config, user_id, decision_result):
    """Log trade execution activities"""
    if decision_result['action'] == 'enter':
        trade_result = await trading_service.execute_trade(decision_result)

        # Log trade entry
        await log_activity(
            config_id=config.config_id,
            user_id=user_id,
            activity_type=f"trade_entry_{decision_result['side']}",
            activity_source='scheduled_bot',
            summary=f"Opened {decision_result['side']} {symbol} at ${trade_result['entry_price']}",
            details={
                'symbol': symbol,
                'side': decision_result['side'],
                'entry_price': trade_result['entry_price'],
                'size_usd': trade_result['size_usd'],
                'leverage': trade_result.get('leverage', 1),
                'stop_loss': trade_result.get('stop_loss'),
                'take_profit': trade_result.get('take_profit'),
                'confidence': decision_result['confidence']
            },
            trade_id=trade_result['trade_id'],
            trade_type=config.trading_mode,
            decision_id=decision_result['decision_id'],
            related_symbol=symbol,
            priority=1,  # High priority - always visible
            importance=9
        )

    elif decision_result['action'] == 'exit':
        close_result = await trading_service.close_position(...)

        # Log trade exit
        await log_activity(
            config_id=config.config_id,
            user_id=user_id,
            activity_type='trade_exit',
            activity_source='scheduled_bot',
            summary=f"Closed {symbol}: {'+' if close_result['pnl'] > 0 else ''}{close_result['pnl']:.2f} ({close_result['pnl_pct']:.1f}%)",
            details={
                'symbol': symbol,
                'exit_price': close_result['exit_price'],
                'pnl': close_result['pnl'],
                'pnl_pct': close_result['pnl_pct'],
                'duration_minutes': close_result['duration_minutes'],
                'close_reason': close_result['close_reason']
            },
            trade_id=close_result['trade_id'],
            trade_type=config.trading_mode,
            decision_id=decision_result['decision_id'],
            related_symbol=symbol,
            priority=1,
            importance=9
        )
```

**Checklist**:
- [ ] Add activity logging to `_run_extraction_v2()`
- [ ] Add activity logging to `_run_decision_v2()`
- [ ] Add activity logging to `_run_trading_v2()` (entry + exit)
- [ ] Test with real scheduled bot execution
- [ ] Verify activities appear in database

---

#### Task 2.2: Agent Tool Activity Logging
**File**: `agent/mcp_server.py`

```python
from core.common.activity_logger import log_activity, ACTIVITY_PRIORITY

# Update existing tools to auto-log

@tool("query_market_data", ...)
async def query_market_data(args: dict[str, Any]) -> dict[str, Any]:
    result = await agent_context.api_client.query_market_data(...)

    # Auto-log activity
    await log_activity(
        config_id=agent_context.config_id,
        user_id=agent_context.user_id,
        activity_type='market_query',
        activity_source='agent_tool',
        summary=f"Queried {args['symbol']}: {', '.join(args.get('categories', {}).keys())}",
        details=result,
        related_symbol=args['symbol'],
        priority=ACTIVITY_PRIORITY['market_query'],
        importance=6
    )

    return result

@tool("execute_trade", ...)
async def execute_trade(args: dict[str, Any]) -> dict[str, Any]:
    result = await agent_context.api_client.execute_trade(...)

    # Auto-log activity
    await log_activity(
        config_id=agent_context.config_id,
        user_id=agent_context.user_id,
        activity_type=f"trade_entry_{args['side']}",
        activity_source='agent_tool',
        summary=f"Opened {args['side']} {args['symbol']} at ${result['entry_price']}",
        details={
            'size_usd': args.get('size_usd'),
            'leverage': args.get('leverage', 1),
            'stop_loss': args.get('stop_loss_price'),
            'take_profit': args.get('take_profit_price'),
            'reasoning': args.get('reasoning', '')
        },
        trade_id=result['trade_id'],
        trade_type='paper',  # TODO: Support live/aster
        related_symbol=args['symbol'],
        priority=1,
        importance=9
    )

    return result

# Add new tool: log_activity (explicit agent logging)
@tool(
    "log_activity",
    """Log your reasoning, analysis, or important thoughts for the activity timeline.

    Use this to document your decision-making process, market analysis insights,
    or strategic observations that users should see on the timeline.

    Activity types:
    - "analysis": Market analysis and interpretation
    - "reasoning": Decision-making logic and rationale
    - "observation": General observations or insights
    - "plan": Strategic planning or next steps
    """,
    {
        "activity_type": str,  # "analysis" | "reasoning" | "observation" | "plan"
        "summary": str,        # Brief title (50 chars max)
        "details": str,        # Full explanation (markdown supported)
        "related_symbol": str, # Optional symbol context
        "importance": int      # 1-10 for prioritization/filtering
    }
)
async def log_activity_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Agent explicitly logs activity for timeline visibility"""
    activity_id = await log_activity(
        config_id=agent_context.config_id,
        user_id=agent_context.user_id,
        activity_type=args['activity_type'],
        activity_source='agent_tool',
        summary=args['summary'],
        details={'markdown': args['details']},
        related_symbol=args.get('related_symbol'),
        priority=ACTIVITY_PRIORITY.get(args['activity_type'], 2),
        importance=args.get('importance', 5)
    )

    return {
        "status": "logged",
        "activity_id": activity_id,
        "summary": args['summary']
    }
```

**Checklist**:
- [ ] Update `query_market_data` to auto-log
- [ ] Update `execute_trade` to auto-log
- [ ] Update `close_position` to auto-log
- [ ] Update `wait_for` to auto-log
- [ ] Update `record_trade_observation` to auto-log
- [ ] Update `update_strategy` to auto-log
- [ ] Add new `log_activity` tool
- [ ] Test with real agent execution

---

### Phase 3: API Endpoints (1-2 days)

#### Task 3.1: Activities API
**File**: `api/activities.py` (new file)

```python
from fastapi import APIRouter, Query, Depends, HTTPException
from core.auth.dependencies import get_current_user
from core.common.db import get_db_connection

router = APIRouter(prefix="/api/v2/activities", tags=["activities"])

@router.get("/{config_id}")
async def get_activities(
    config_id: str,
    start_time: str = Query(None, description="ISO timestamp"),
    end_time: str = Query(None, description="ISO timestamp"),
    activity_types: list[str] = Query(None, description="Filter by types"),
    trade_id: str = Query(None, description="Filter by trade"),
    min_importance: int = Query(1, ge=1, le=10),
    limit: int = Query(500, ge=1, le=1000),
    user: dict = Depends(get_current_user)
):
    """
    Get all activities for a config (timeline data).

    Returns activities in reverse chronological order.
    """
    # Verify ownership
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id FROM configurations
                WHERE config_id = %s
            """, (config_id,))
            config = cur.fetchone()

            if not config or config[0] != user['id']:
                raise HTTPException(403, "Not authorized")

            # Build query
            query = """
                SELECT
                    activity_id, activity_type, activity_source, summary, details,
                    trade_id, trade_type, decision_id, related_symbol,
                    priority, importance, created_at
                FROM activities
                WHERE config_id = %s
            """
            params = [config_id]

            if start_time:
                query += " AND created_at >= %s"
                params.append(start_time)

            if end_time:
                query += " AND created_at <= %s"
                params.append(end_time)

            if activity_types:
                query += " AND activity_type = ANY(%s)"
                params.append(activity_types)

            if trade_id:
                query += " AND trade_id = %s"
                params.append(trade_id)

            query += " AND importance >= %s"
            params.append(min_importance)

            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)

            cur.execute(query, params)
            activities = cur.fetchall()

            return {
                "status": "success",
                "activities": [
                    {
                        "id": str(a[0]),
                        "timestamp": a[11].isoformat(),
                        "type": a[1],
                        "priority": a[9],
                        "data": {
                            "summary": a[3],
                            "details": a[4],
                            "symbol": a[8],
                            "importance": a[10],
                            "trade_id": str(a[5]) if a[5] else None,
                            "trade_type": a[6]
                        }
                    }
                    for a in activities
                ],
                "count": len(activities)
            }

@router.get("/{config_id}/balance-series")
async def get_balance_series(
    config_id: str,
    interval_minutes: int = Query(5, description="Balance snapshot interval"),
    user: dict = Depends(get_current_user)
):
    """Get account balance over time for equity curve."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Verify ownership
            cur.execute("""
                SELECT user_id FROM configurations WHERE config_id = %s
            """, (config_id,))
            config = cur.fetchone()

            if not config or config[0] != user['id']:
                raise HTTPException(403, "Not authorized")

            # Get account info
            cur.execute("""
                SELECT initial_balance, current_balance, created_at
                FROM paper_accounts
                WHERE config_id = %s
            """, (config_id,))
            account = cur.fetchone()

            if not account:
                return {
                    "status": "success",
                    "balance_series": [],
                    "current_balance": 10000,
                    "initial_balance": 10000
                }

            # Get all closed trades for balance reconstruction
            cur.execute("""
                SELECT closed_at, realized_pnl
                FROM paper_trades
                WHERE config_id = %s AND status = 'closed'
                ORDER BY closed_at
            """, (config_id,))
            trades = cur.fetchall()

            # Reconstruct balance over time
            initial_balance = float(account[0])
            current_balance = float(account[1])

            balance_points = [
                {
                    "timestamp": account[2].isoformat(),
                    "balance": initial_balance
                }
            ]

            running_balance = initial_balance
            for trade in trades:
                running_balance += float(trade[1])
                balance_points.append({
                    "timestamp": trade[0].isoformat(),
                    "balance": running_balance
                })

            # Add current balance
            from datetime import datetime
            balance_points.append({
                "timestamp": datetime.utcnow().isoformat(),
                "balance": current_balance
            })

            return {
                "status": "success",
                "balance_series": balance_points,
                "current_balance": current_balance,
                "initial_balance": initial_balance
            }

@router.get("/{config_id}/metadata")
async def get_timeline_metadata(
    config_id: str,
    user: dict = Depends(get_current_user)
):
    """Get bot/agent metadata for timeline header."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Verify ownership
            cur.execute("""
                SELECT user_id FROM configurations WHERE config_id = %s
            """, (config_id,))
            config = cur.fetchone()

            if not config or config[0] != user['id']:
                raise HTTPException(403, "Not authorized")

            # Get config info
            cur.execute("""
                SELECT config_name, config_type, created_at
                FROM configurations
                WHERE config_id = %s
            """, (config_id,))
            config_row = cur.fetchone()

            # Get account metrics
            cur.execute("""
                SELECT
                    current_balance,
                    initial_balance,
                    total_trades,
                    win_trades,
                    loss_trades,
                    total_pnl
                FROM paper_accounts
                WHERE config_id = %s
            """, (config_id,))
            account = cur.fetchone()

            if not account:
                # No trades yet
                win_rate = 0
                performance = 0
                current_balance = 10000
                initial_balance = 10000
                total_trades = 0
            else:
                current_balance = float(account[0])
                initial_balance = float(account[1])
                total_trades = account[2]
                win_trades = account[3]

                win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
                performance = ((current_balance - initial_balance) / initial_balance) * 100

            return {
                "status": "success",
                "metadata": {
                    "botName": config_row[0],
                    "configType": config_row[1],
                    "startingBalance": initial_balance,
                    "currentBalance": current_balance,
                    "totalTrades": total_trades,
                    "winRate": round(win_rate, 1),
                    "performance": round(performance, 2),
                    "createdAt": config_row[2].isoformat()
                }
            }
```

**Register Router in `ggbot.py`**:
```python
from api.activities import router as activities_router

app.include_router(activities_router)
```

**Checklist**:
- [ ] Create `api/activities.py`
- [ ] Implement `GET /activities/{config_id}`
- [ ] Implement `GET /activities/{config_id}/balance-series`
- [ ] Implement `GET /activities/{config_id}/metadata`
- [ ] Add query filters (time range, types, trade_id, importance)
- [ ] Register router in ggbot.py
- [ ] Test with Postman/curl
- [ ] Verify proper auth/ownership checks

---

### Phase 4: Frontend Integration (2-3 days)

**Note**: The ActivityTimelineViewer already has bucketing logic (lines 350-377), but needs updates:
- Currently groups by TIME only (all activities in a bucket → one icon)
- Need to group by TIME + TYPE (5 queries + 3 decisions → 2 icons with count badges)
- Priority 1 activities never group (trades always show individually)
- Priority 2 activities group by type within time buckets

#### Task 4.1: Replace Mock Data with API Calls
**File**: `frontend/components/ActivityTimelineViewer.tsx`

```typescript
// Replace mock data generation with real API calls
export default function ActivityTimelineViewer({ configId }: ActivityTimelineViewerProps) {
  const [log, setLog] = useState<ActivityLog | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTradeId, setSelectedTradeId] = useState<string | null>(null)

  // Fetch data on mount
  useEffect(() => {
    if (!configId) return

    const fetchData = async () => {
      try {
        setLoading(true)

        // Fetch all three endpoints in parallel
        const [activities, balanceSeries, metadata] = await Promise.all([
          fetch(`/api/v2/activities/${configId}`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
          }).then(r => r.json()),
          fetch(`/api/v2/activities/${configId}/balance-series`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
          }).then(r => r.json()),
          fetch(`/api/v2/activities/${configId}/metadata`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
          }).then(r => r.json())
        ])

        if (activities.status !== 'success') {
          throw new Error('Failed to fetch activities')
        }

        setLog({
          activities: activities.activities,
          balanceTimeseries: balanceSeries.balance_series,
          metadata: metadata.metadata
        })

        setError(null)
      } catch (err) {
        console.error('Failed to fetch activity data:', err)
        setError('Failed to load activity timeline')
      } finally {
        setLoading(false)
      }
    }

    fetchData()

    // Poll for updates every 10 seconds
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [configId])

  // Loading state
  if (loading && !log) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-charcoal-900">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500" />
          <span className="text-bone-200">Loading activity timeline...</span>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-charcoal-900">
        <div className="text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <div className="text-xl text-bone-200 mb-2">Failed to Load Timeline</div>
          <div className="text-bone-400">{error}</div>
        </div>
      </div>
    )
  }

  // Empty state
  if (!log || log.activities.length === 0) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-charcoal-900">
        <div className="text-center">
          <div className="text-4xl mb-4">📊</div>
          <div className="text-xl text-bone-200 mb-2">No Activity Yet</div>
          <div className="text-bone-400">Activities will appear here once the bot starts trading</div>
        </div>
      </div>
    )
  }

  // Rest of existing component (Canvas rendering, zoom, pan, etc.)
  // ...
}
```

**Checklist**:
- [ ] Replace mock data generation with API calls
- [ ] Add authentication headers (Bearer token)
- [ ] Add loading state with spinner
- [ ] Add error state handling
- [ ] Add empty state for no activities
- [ ] Implement polling for real-time updates (10s interval)
- [ ] Test with real data from test bot
- [ ] Verify timeline renders correctly

---

#### Task 4.2: Trade Lifecycle Highlighting
**File**: `frontend/components/ActivityTimelineViewer.tsx`

```typescript
// Add trade highlighting logic
const [selectedTradeId, setSelectedTradeId] = useState<string | null>(null)

// Filter activities by selected trade
const filteredActivities = useMemo(() => {
  if (!selectedTradeId) return log.activities

  return log.activities.filter(a => a.data.trade_id === selectedTradeId)
}, [log.activities, selectedTradeId])

// Handle activity click
const handleActivityClick = (activity: ActivityItem) => {
  if (activity.data.trade_id) {
    // Trade-related activity clicked
    setSelectedTradeId(activity.data.trade_id)
    setSelected([activity]) // Also open side panel
  } else {
    // Non-trade activity
    setSelected([activity])
    setSelectedTradeId(null)
  }
}

// Visual highlighting in Canvas render
const renderActivityIcon = (item: ActivityItem, x: number, y: number) => {
  const def = ACTIVITY_DEFS[item.type]
  const isHighlighted = selectedTradeId && item.data.trade_id === selectedTradeId

  // Draw icon with highlight effect
  if (isHighlighted) {
    // Draw glow effect
    ctx.shadowColor = '#10b981'
    ctx.shadowBlur = 15
  }

  // Draw icon circle
  ctx.fillStyle = isHighlighted ? '#10b981' : def.color
  ctx.beginPath()
  ctx.arc(x, y, iconRadius, 0, Math.PI * 2)
  ctx.fill()

  // Reset shadow
  ctx.shadowBlur = 0

  // Draw emoji icon
  ctx.fillText(def.icon, x, y)
}

// Connection lines for trade lifecycle
const renderTradeConnections = () => {
  if (!selectedTradeId) return

  const tradeActivities = log.activities
    .filter(a => a.data.trade_id === selectedTradeId)
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())

  if (tradeActivities.length < 2) return

  ctx.strokeStyle = '#10b981'
  ctx.lineWidth = 2
  ctx.setLineDash([5, 5])

  for (let i = 0; i < tradeActivities.length - 1; i++) {
    const current = getIconPosition(tradeActivities[i])
    const next = getIconPosition(tradeActivities[i + 1])

    ctx.beginPath()
    ctx.moveTo(current.x, current.y)
    ctx.lineTo(next.x, next.y)
    ctx.stroke()
  }

  ctx.setLineDash([])
}
```

**Checklist**:
- [ ] Add `selectedTradeId` state
- [ ] Filter activities by trade_id when trade selected
- [ ] Highlight icons with glow effect
- [ ] Draw connection lines between related activities
- [ ] Update side panel to show trade narrative
- [ ] Add "Clear selection" button
- [ ] Test trade clicking and highlighting
- [ ] Ensure smooth visual transitions

---

#### Task 4.3: Enhanced Side Panel for Trade Lifecycle
**File**: `frontend/components/ActivityTimelineViewer.tsx` (SidePanel component)

```typescript
function SidePanel({ selected, onClose, tradeId }: SidePanelProps) {
  // If trade_id is set, show trade narrative view
  if (tradeId) {
    return <TradeNarrativePanel tradeId={tradeId} activities={selected} onClose={onClose} />
  }

  // Otherwise, show individual activity details
  return <ActivityDetailsPanel activities={selected} onClose={onClose} />
}

function TradeNarrativePanel({ tradeId, activities, onClose }) {
  // Sort activities by timestamp
  const sorted = [...activities].sort((a, b) =>
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )

  // Group by lifecycle phase
  const entry = sorted.find(a => a.type.includes('trade_entry'))
  const monitoring = sorted.filter(a => a.type === 'decision_made' || a.type === 'market_query')
  const exit = sorted.find(a => a.type === 'trade_exit')

  // Calculate trade outcome
  const pnl = exit?.data.details.pnl || 0
  const isWin = pnl > 0

  return (
    <div className="fixed right-0 top-0 h-full w-[500px] bg-charcoal-800 border-l border-white/10 shadow-2xl overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-charcoal-900 border-b border-white/10 p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-white/50">Trade Lifecycle</div>
            <div className="text-lg font-semibold text-white">
              {entry?.data.symbol}
            </div>
          </div>
          <button onClick={onClose} className="text-white/50 hover:text-white">
            ✕
          </button>
        </div>

        {/* Trade Outcome */}
        {exit && (
          <div className={cn(
            "mt-3 p-3 rounded-lg border",
            isWin
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
              : "bg-red-500/10 border-red-500/30 text-red-400"
          )}>
            <div className="text-2xl font-bold">
              {isWin ? '+' : ''}{pnl.toFixed(2)} USD
            </div>
            <div className="text-sm opacity-70">
              {exit.data.details.pnl_pct}% • {exit.data.details.duration_minutes}min
            </div>
          </div>
        )}
      </div>

      {/* Timeline Sections */}
      <div className="p-4 space-y-6">
        {/* Entry Section */}
        <section>
          <div className="flex items-center gap-2 mb-3">
            <div className="text-xl">🟢</div>
            <div className="font-semibold text-white">Trade Entry</div>
            <div className="text-xs text-white/50">
              {new Date(entry.timestamp).toLocaleString()}
            </div>
          </div>
          <ActivityCard activity={entry} expanded={true} />
        </section>

        {/* Monitoring Section */}
        {monitoring.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-3">
              <div className="text-xl">👁️</div>
              <div className="font-semibold text-white">
                Trade Management ({monitoring.length} activities)
              </div>
            </div>
            <div className="space-y-2">
              {monitoring.map(activity => (
                <ActivityCard key={activity.id} activity={activity} expanded={false} />
              ))}
            </div>
          </section>
        )}

        {/* Exit Section */}
        {exit && (
          <section>
            <div className="flex items-center gap-2 mb-3">
              <div className="text-xl">🔴</div>
              <div className="font-semibold text-white">Trade Exit</div>
              <div className="text-xs text-white/50">
                {new Date(exit.timestamp).toLocaleString()}
              </div>
            </div>
            <ActivityCard activity={exit} expanded={true} />
          </section>
        )}
      </div>
    </div>
  )
}
```

**Checklist**:
- [ ] Create `TradeNarrativePanel` component
- [ ] Group activities by lifecycle phase (entry → monitoring → exit)
- [ ] Show trade outcome prominently (P&L, win/loss)
- [ ] Render each phase with expandable cards
- [ ] Add timeline visual (vertical progress indicator)
- [ ] Test with completed and open trades
- [ ] Handle edge cases (no exit yet, no monitoring)

---

### Phase 5: Testing & Polish (1-2 days)

#### Task 5.1: End-to-End Testing

**Test Scenarios**:
- [ ] Create new scheduled bot, activate, wait for activities to appear
- [ ] Verify market queries show up with correct details
- [ ] Verify decisions appear with reasoning
- [ ] Verify trades appear with entry/exit activities
- [ ] Test trade clicking → highlighting → side panel narrative
- [ ] Test zoom levels (activities appear/disappear correctly)
- [ ] Test real-time updates (poll interval working)
- [ ] Test empty state (new bot with no activities)
- [ ] Test loading state (slow API response)
- [ ] Test error state (API failure)

**Agent Testing**:
- [ ] Test with existing agent `d13d5536-2498-4f27-b2bc-e4f98958e1d8`
- [ ] Verify agent market queries appear
- [ ] Verify agent explicit logs (analysis/reasoning) appear
- [ ] Verify agent wait periods show correctly
- [ ] Test agent trade execution activities

**Edge Cases**:
- [ ] Very long timeline (1000+ activities)
- [ ] Trade with no monitoring decisions
- [ ] Open trade (no exit yet)
- [ ] Multiple trades on same symbol
- [ ] Activities with long descriptions (text overflow)
- [ ] Canvas performance with 100+ icons visible
- [ ] Mobile responsive design

---

## API Contract Summary

### GET `/api/v2/activities/{config_id}`
**Query Params**:
- `start_time` (optional): ISO timestamp
- `end_time` (optional): ISO timestamp
- `activity_types` (optional): List of types to filter
- `trade_id` (optional): Filter by specific trade
- `min_importance` (default: 1): Hide low importance
- `limit` (default: 500): Max activities

**Response**:
```json
{
  "status": "success",
  "activities": [
    {
      "id": "uuid",
      "timestamp": "2025-11-03T10:30:00Z",
      "type": "trade_entry_long",
      "priority": 1,
      "data": {
        "summary": "Opened long BTC/USDT at $110,229",
        "details": { /* type-specific data */ },
        "symbol": "BTC/USDT",
        "importance": 9,
        "trade_id": "uuid",
        "trade_type": "paper"
      }
    }
  ],
  "count": 47
}
```

### GET `/api/v2/activities/{config_id}/balance-series`
**Response**:
```json
{
  "status": "success",
  "balance_series": [
    { "timestamp": "2025-11-01T00:00:00Z", "balance": 10000 },
    { "timestamp": "2025-11-01T14:23:00Z", "balance": 10125.50 }
  ],
  "current_balance": 10125.50,
  "initial_balance": 10000
}
```

### GET `/api/v2/activities/{config_id}/metadata`
**Response**:
```json
{
  "status": "success",
  "metadata": {
    "botName": "RSI Scalper v2",
    "configType": "scheduled_trading",
    "startingBalance": 10000,
    "currentBalance": 10125.50,
    "totalTrades": 12,
    "winRate": 66.7,
    "performance": 1.26,
    "createdAt": "2025-11-01T00:00:00Z"
  }
}
```

---

## Activity Type Reference

### Universal Types (All Bot Types)

| Type | Priority | Description | Details Schema |
|------|----------|-------------|----------------|
| `market_query` | 2 | Market data extraction | `{ symbol, timeframe, indicators, market_intelligence }` |
| `decision_made` | 2 | AI decision (enter/wait/exit) | `{ action, confidence, reasoning, symbol }` |
| `trade_entry_long` | 1 | Long position opened | `{ symbol, entry_price, size_usd, leverage, sl, tp }` |
| `trade_entry_short` | 1 | Short position opened | Same as above |
| `trade_exit` | 1 | Position closed | `{ symbol, exit_price, pnl, pnl_pct, duration, close_reason }` |
| `position_adjusted` | 1 | SL/TP/size changed | `{ symbol, old_values, new_values, reason }` |

### Agent-Specific Types

| Type | Priority | Description | Details Schema |
|------|----------|-------------|----------------|
| `agent_wait` | 3 | Agent waiting period | `{ duration_minutes, reason, next_check_at }` |
| `analysis` | 2 | Market analysis | `{ markdown, symbol }` |
| `reasoning` | 2 | Decision reasoning | `{ markdown, decision_type }` |
| `observation` | 3 | General observation | `{ markdown }` |
| `plan` | 3 | Strategic plan | `{ markdown, timeframe }` |
| `strategy_updated` | 1 | Strategy modification | `{ old_version, new_version, changes }` |
| `observation_recorded` | 3 | Trade observation saved | `{ trade_id, what_went_well, what_went_wrong }` |

---

## Success Metrics

**Phase 1 (Database)**:
- [ ] `activities` table created with proper indexes
- [ ] RLS policy enforces user isolation
- [ ] `log_activity()` helper works correctly
- [ ] Migration runs without errors

**Phase 2 (Logging)**:
- [ ] Scheduled bots log all pipeline activities
- [ ] Agent tools auto-log all actions
- [ ] Activities appear in database with correct data
- [ ] Priority and importance values are accurate

**Phase 3 (API)**:
- [ ] All three endpoints return correct data
- [ ] Query filters work properly
- [ ] Auth/ownership checks prevent unauthorized access
- [ ] API performance is acceptable (<500ms)

**Phase 4 (Frontend)**:
- [ ] Mock data replaced with real API calls
- [ ] Loading/error/empty states work
- [ ] Real-time polling updates timeline smoothly
- [ ] Trade lifecycle highlighting works
- [ ] Side panel shows correct details
- [ ] Canvas performance is smooth (60fps)

**Phase 5 (Polish)**:
- [ ] All test scenarios pass
- [ ] Edge cases handled gracefully
- [ ] Mobile responsive design works
- [ ] No console errors or warnings
- [ ] Timeline ready for production use

**Phase 6 (Competition)**:
- [ ] Conversation history saves correctly during strategy definition
- [ ] "View Configuration" button positioned correctly (left of "Jump to Now")
- [ ] ConfigurationModal displays conversation + strategy
- [ ] Active Positions section shows at bottom with proper styling
- [ ] Full page tested with live agent for competition submission
- [ ] Page renders correctly on mobile/tablet
- [ ] Screenshots taken for competition materials

---

## Phase 6: Competition Features (1-2 days)

**Goal**: Add "View Configuration" modal and Active Trades section for Aster Competition submission

**Context**: The Activity Timeline view page (`/view/[config_id]`) will be submitted to the Aster Vibe Trading Competition, showcasing a single agent live trading on AsterDEX. These features add transparency and completeness to the submission.

### Task 6.1: View Configuration Button & Modal

**Purpose**: Show the agent's full strategy definition conversation + final strategy in a modal. Demonstrates the agent's onboarding process, reasoning, and strategic thinking to competition judges.

#### Backend: Save Conversation History

**File**: `agent/run_agent.py`

Update the `request_autonomous_mode` tool response handling to capture and save conversation history:

```python
# In strategy_definition mode, when agent calls request_autonomous_mode:

async def _handle_request_autonomous_mode(self, tool_result: dict):
    """Handle request_autonomous_mode tool call and save conversation history"""

    # Get conversation history from SDK
    conversation_history = []

    # Extract messages from Redis or SDK context
    # Format: [{"role": "user", "content": "...", "timestamp": "..."}, ...]
    messages_key = f"agent:{self.config_id}:messages"
    responses_key = f"agent:{self.config_id}:responses"

    # Build conversation from Redis history (already has all messages)
    # Or extract from SDK if available

    # For now, we'll capture from the Redis queues we've been using
    # This is a simplified approach - ideally the SDK would provide this

    strategy_data = {
        "content": tool_result["strategy_content"],
        "version": 1,
        "autonomously_editable": tool_result.get("autonomously_editable", False),
        "conversation_history": self._build_conversation_history(),  # NEW
        "created_at": datetime.utcnow().isoformat(),
        "last_updated_at": datetime.utcnow().isoformat()
    }

    # Save to database
    await self._save_strategy(strategy_data)

def _build_conversation_history(self) -> list[dict]:
    """
    Build conversation history from Redis or session state.

    Returns: [
        {"role": "agent", "content": "...", "timestamp": "..."},
        {"role": "user", "content": "...", "timestamp": "..."},
        ...
    ]
    """
    # Implementation note: This will need to track messages during the conversation
    # For now, we can reconstruct from the messages that led to strategy confirmation
    # In production, we'd want to track this explicitly during the conversation

    history = []

    # Option 1: Track messages in memory during strategy_definition mode
    # Option 2: Store incremental messages in Redis with timestamps
    # Option 3: Extract from SDK conversation state if available

    # For MVP, we'll add message tracking to the strategy_definition mode loop

    return history
```

**Simplified Approach for MVP**:

Add message tracking to `agent/run_agent.py` in strategy_definition mode:

```python
class TradingAgent:
    def __init__(self, ...):
        # ... existing code ...
        self.conversation_history = []  # NEW: Track messages during conversation

    async def _strategy_definition_mode(self):
        """Strategy definition mode with conversation tracking"""

        while True:
            # Wait for user message
            message = await self._wait_for_message()

            # Track user message
            self.conversation_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Send to agent
            response = await self.client.send_message(message)

            # Track agent response
            self.conversation_history.append({
                "role": "agent",
                "content": response,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Push response to Redis
            await self._push_response(response)

            # Check if agent requested autonomous mode
            if self._check_autonomous_request(response):
                # Save strategy with conversation history
                await self._save_strategy_with_history()
                break
```

#### Frontend: Configuration Modal Component

**File**: `frontend/components/ConfigurationModal.tsx` (NEW)

```typescript
import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { Modal } from '@/components/ui/Modal'

interface Message {
  role: 'user' | 'agent'
  content: string
  timestamp: string
}

interface AgentStrategy {
  content: string
  version: number
  autonomously_editable: boolean
  conversation_history: Message[]
  created_at: string
  last_updated_at: string
}

interface ConfigurationModalProps {
  configId: string
  isOpen: boolean
  onClose: () => void
}

export function ConfigurationModal({ configId, isOpen, onClose }: ConfigurationModalProps) {
  const [strategy, setStrategy] = useState<AgentStrategy | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isOpen) return

    const fetchConfig = async () => {
      try {
        setLoading(true)
        const response = await fetch(`/api/v2/config/${configId}`, {
          headers: { 'Authorization': `Bearer ${getToken()}` }
        })
        const data = await response.json()

        if (data.config?.agent_strategy) {
          setStrategy(data.config.agent_strategy)
        }
      } catch (err) {
        console.error('Failed to fetch configuration:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchConfig()
  }, [isOpen, configId])

  if (!strategy) {
    return null // Only show for agentic configs with strategy
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="large">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-bone-100">Agent Configuration</h2>
          <button
            onClick={onClose}
            className="text-bone-400 hover:text-bone-200 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Two-column layout */}
        <div className="grid grid-cols-2 gap-6">
          {/* Left: Conversation History */}
          <div className="border border-white/10 rounded-xl overflow-hidden bg-charcoal-800">
            <div className="px-4 py-3 border-b border-white/10 bg-charcoal-900">
              <div className="flex items-center gap-2">
                <div className="text-xl">💬</div>
                <div className="font-medium text-bone-100">Strategy Definition Conversation</div>
              </div>
            </div>

            <div className="p-4 space-y-4 max-h-[600px] overflow-y-auto">
              {strategy.conversation_history?.length === 0 ? (
                <div className="text-center text-bone-500 py-8">
                  No conversation history available
                </div>
              ) : (
                strategy.conversation_history?.map((msg, idx) => (
                  <MessageBubble key={idx} message={msg} />
                ))
              )}
            </div>
          </div>

          {/* Right: Final Strategy */}
          <div className="border border-white/10 rounded-xl overflow-hidden bg-charcoal-800">
            <div className="px-4 py-3 border-b border-white/10 bg-charcoal-900">
              <div className="flex items-center gap-2">
                <div className="text-xl">🎯</div>
                <div className="font-medium text-bone-100">Agent Strategy</div>
              </div>
            </div>

            <div className="p-4 overflow-y-auto max-h-[600px]">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown>{strategy.content}</ReactMarkdown>
              </div>

              {/* Metadata */}
              <div className="mt-6 pt-4 border-t border-white/10 space-y-2 text-xs text-bone-500">
                <div className="flex justify-between">
                  <span>Version:</span>
                  <span className="font-mono">{strategy.version}</span>
                </div>
                <div className="flex justify-between">
                  <span>Created:</span>
                  <span className="font-mono">
                    {new Date(strategy.created_at).toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Autonomously Editable:</span>
                  <span className={strategy.autonomously_editable ? "text-green-400" : "text-bone-400"}>
                    {strategy.autonomously_editable ? 'Yes' : 'No'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  )
}

// Message bubble component
function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`
        max-w-[85%] px-4 py-2 rounded-lg
        ${isUser
          ? 'bg-emerald-500 text-white'
          : 'bg-charcoal-700 text-bone-200'
        }
      `}>
        <div className="whitespace-pre-wrap">{message.content}</div>
        <div className="text-xs opacity-60 mt-1">
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}
```

#### Integration into View Page

**File**: `frontend/app/view/[config_id]/page.tsx`

```typescript
'use client'

import { useState } from 'react'
import ActivityTimelineViewer from '@/components/ActivityTimelineViewer'
import { ConfigurationModal } from '@/components/ConfigurationModal'
import PositionsTable from '@/components/PositionsTable'

export default function ViewPage({ params }: { params: { config_id: string } }) {
  const [showConfigModal, setShowConfigModal] = useState(false)
  const configId = params.config_id

  return (
    <div className="min-h-screen bg-charcoal-900">
      {/* Activity Timeline (full screen canvas) */}
      <div className="relative">
        {/* View Configuration button - positioned next to "Jump to Now" */}
        <div className="absolute top-4 right-24 z-10">
          <button
            onClick={() => setShowConfigModal(true)}
            className="px-4 py-2 bg-charcoal-800 hover:bg-charcoal-700 text-bone-200 border border-white/10 rounded-lg font-medium shadow-lg transition-colors"
          >
            📋 View Configuration
          </button>
        </div>

        <ActivityTimelineViewer configId={configId} />
      </div>

      {/* Active Trades Section */}
      <div className="px-8 py-6 bg-charcoal-900 border-t border-white/10">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-xl font-semibold text-bone-200 mb-4">Active Positions</h2>
          <PositionsTable configId={configId} />
        </div>
      </div>

      {/* Configuration Modal */}
      <ConfigurationModal
        configId={configId}
        isOpen={showConfigModal}
        onClose={() => setShowConfigModal(false)}
      />
    </div>
  )
}
```

**Checklist**:
- [ ] Add `conversation_history` tracking to `agent/run_agent.py`
- [ ] Update `_save_strategy()` to include conversation history
- [ ] Test conversation history capture during strategy definition
- [ ] Create `ConfigurationModal.tsx` component
- [ ] Add "View Configuration" button to view page (left of "Jump to Now")
- [ ] Test modal with real agent configuration
- [ ] Verify conversation history displays correctly
- [ ] Handle empty conversation history gracefully

---

### Task 6.2: Active Trades Component

**Purpose**: Show current open positions at the bottom of the timeline view, providing real-time position status for competition judges.

#### Integration

**File**: `frontend/app/view/[config_id]/page.tsx` (already shown above)

The PositionsTable component is already built and integrated in the code above. Just need to ensure it's styled properly for the view page context.

**Additional Styling** (if needed):

```typescript
// Optional: Create a view-specific wrapper for PositionsTable
<div className="px-8 py-6 bg-charcoal-900 border-t border-white/10">
  <div className="max-w-7xl mx-auto">
    <div className="flex items-center justify-between mb-4">
      <h2 className="text-xl font-semibold text-bone-200">Active Positions</h2>
      <div className="text-sm text-bone-500">
        Real-time position tracking
      </div>
    </div>

    {/* Existing PositionsTable component */}
    <PositionsTable
      configId={configId}
      showCloseButton={false}  // Hide close button for view-only mode
      compact={true}           // Optional: compact view for bottom section
    />
  </div>
</div>
```

**Checklist**:
- [ ] Add PositionsTable to bottom of view page
- [ ] Style section with proper spacing and borders
- [ ] Test with open positions (verify real-time updates)
- [ ] Test with no open positions (empty state)
- [ ] Ensure section scrolls independently if needed
- [ ] Match styling to rest of timeline page

---

### Competition Submission Checklist

**Visual Flow for Judges**:
1. **Top**: Performance chart with activity icons (transparent trading)
2. **"View Configuration" button**: Click → see full strategy conversation (unique!)
3. **Activity Timeline**: Every decision/trade with reasoning (full transparency)
4. **Bottom**: Current open positions (live proof)

**Testing Before Submission**:
- [ ] Load view page with agent `d13d5536-2498-4f27-b2bc-e4f98958e1d8`
- [ ] Verify all activities display correctly
- [ ] Click "View Configuration" → verify conversation + strategy loads
- [ ] Verify active positions show at bottom
- [ ] Test on mobile/tablet (judges might view on different devices)
- [ ] Take screenshots for submission materials
- [ ] Verify page loads without authentication (public view)

**Why This Wins**:
- ✅ **Full Transparency**: Shows agent's thought process from onboarding to execution
- ✅ **Innovation**: Conversation history is unique - no one else shows this
- ✅ **Completeness**: Strategy + reasoning + trades + positions = full picture
- ✅ **Polish**: Beautiful, interactive, professional UI
- ✅ **Trust**: Competition judges can verify every decision

---

## Future Enhancements (Post-Launch)

- [ ] **Real-time SSE Updates**: Replace polling with Server-Sent Events
- [ ] **Activity Filtering UI**: User-facing importance slider
- [ ] **Export Timeline**: Download timeline as image/PDF
- [ ] **Playback Mode**: Replay trading day with time controls
- [ ] **Comparison View**: Compare multiple bots side-by-side
- [ ] **Activity Search**: Full-text search across all activities
- [ ] **Custom Activity Types**: User-defined activity categories
- [ ] **Activity Analytics**: Insights on activity patterns vs outcomes
- [ ] **View Configuration for Scheduled Bots**: Show readable config (not just agents)

---

## Related Documentation

- **Canvas Component**: `frontend/components/ActivityTimelineViewer.tsx` (850 lines, already built)
- **Agent Phase 4a**: `DOCS/todo/AGENT_P4.md` (Strategy definition UI - complete)
- **TODO Tracking**: `TODO.md` (High-level task tracking)

---

**Last Updated**: 2025-11-03
**Status**: Ready for Implementation
**Estimated Timeline**: 8-12 days (7-10 days core + 1-2 days competition features)
