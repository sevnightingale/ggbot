# Activity Timeline - Trade Story Architecture

**Created**: 2025-11-06
**Status**: Planning Phase
**Vision**: Transform timeline from chronological activity log into causal trade narrative explorer

---

## Vision Statement

**The timeline tells the story of what the agent is thinking and doing**, making autonomous trading transparent and explorable. The equity curve shows the outcome, but the activities reveal the narrative. Each "story node" represents a complete decision arc: *"Agent gathered data → analyzed conditions → made a choice → executed → result."*

**User Journey**: Investigative exploration. User notices an interesting moment on the equity curve (big win, unexpected loss, long flat period) and clicks to understand the "why" - seeing the chain of agent thoughts, data queries, and trades that led to that outcome. The timeline feels like reviewing a chess game with annotations, not just watching dots move.

**Interaction Philosophy**: Prioritize causality over chronology. When a user clicks a trade outcome, they see the full trade lifecycle with activities linked visually - drawing connection lines so users can trace "this query informed this decision which caused this trade." The goal is to build trust and learning.

---

## Current State Assessment

### What Exists ✅

**Database Infrastructure** (Complete):
- `activities` table: 14 columns, 7 indexes, RLS enabled, trade_id linking operational
- Activity logging helper: `core/common/activity_logger.py` with `log_activity_safe()`
- 11 activity types defined with priority-based grouping (Priority 1=trades, Priority 2=analysis)

**Agent Integration** (Complete):
- 7 MCP tools auto-log activities (query_market_data, execute_trade, close_position, etc.)
- `log_activity` tool for explicit agent logging
- Trading mode detection (paper/aster/symphony)
- Trade lifecycle tracking via trade_id field

**API Layer** (Partial):
- ✅ `GET /api/v2/activities/{config_id}` - Fetch all activities with filters
- ✅ `GET /api/v2/activities/{config_id}/balance-series` - Cumulative P&L chart
- ✅ `GET /api/v2/activities/{config_id}/metadata` - Bot stats for header
- ❌ **MISSING**: `/story-nodes` endpoint for trade-centric grouping

**Frontend** (Needs Refactor):
- ✅ Timeline.jsx (432 lines): Container with API integration, filters, modals
- ✅ BalanceChartRecharts.tsx (588 lines): Recharts-based equity curve + markers
- ⚠️ Current approach: Time-clustered activity dots (86 activity groups in screenshot)
- ❌ **Gap**: No trade-centric story nodes, no lifecycle linking, no causality visualization

### What's Missing 🔴

**Critical Gaps Identified**:
1. **No story node grouping** - Activities shown as individual time-clustered dots, not trade narratives
2. **No trade lifecycle linking** - Clicking trade doesn't highlight/filter related activities
3. **No connection lines** - Visual causality (query→reasoning→trade→exit) not shown
4. **No trade narrative panel** - Side panel shows flat activity list, not phased story
5. **Scheduled bot logging** - Orchestrator doesn't log activities (only agents do)
6. **TP/SL order monitoring** - Aster automatic fills not detected/logged

---

## Architectural Pivot: Story Nodes

### Current Architecture (Time-Based)
```
Timeline.jsx
├─> Fetches: /activities (flat list)
├─> BalanceChartRecharts.tsx
│   ├─> Clusters by TIME WINDOW (1min-4hr buckets)
│   ├─> Groups ALL activities in bucket → single marker
│   └─> Badge shows count (e.g., "19 activities")
└─> Click marker → Side panel (chronological list)
```

**Problem**: User sees "19 activities at 10:30am" but can't distinguish:
- Market query that triggered entry
- Reasoning that justified the trade
- Trade execution event
- Mid-trade monitoring
- Exit decision

### New Architecture (Trade-Centric)
```
Timeline.jsx
├─> Fetches: /story-nodes (pre-grouped by trade_id)
├─> BalanceChartRecharts.tsx
│   ├─> Renders STORY NODES (not individual activities)
│   │   ├─> Each node = complete trade lifecycle
│   │   ├─> Positioned at trade entry time
│   │   ├─> Icon composite: entry glyph + phase count
│   │   └─> Color/size indicates outcome (green=win, red=loss)
│   ├─> Renders STANDALONE activities (no trade_id)
│   │   └─> Strategy updates, waits, general observations
│   └─> Activity density gradient (darker = more analysis)
└─> Click story node → Trade Narrative Panel (vertical timeline by phase)
```

**Solution**: User sees "BTC Long $110,229" story node. Click reveals:
```
┌─ Entry Analysis (3min)
│  ├─ Market query: RSI 32, MACD bearish divergence
│  ├─ Reasoning: "Oversold conditions, momentum reversal signal"
│  └─ Entry: Long BTC $110,229, SL $109,500, TP $112,000
│
├─ Position Monitoring (90min)
│  ├─ Price check: $110,450 (+0.2%)
│  ├─ Reasoning: "TP approaching, watching for resistance"
│  └─ Price check: $111,800 (+1.4%)
│
└─ Exit Decision
   ├─ TP hit: $112,000 (closed automatically)
   └─ Outcome: +$45.50 (4.1% gain)
```

---

## Implementation Plan

### Phase 1: Backend Story Nodes API (2-3 hours)

**Goal**: Create `/story-nodes` endpoint that pre-groups activities by trade lifecycle.

#### Task 1.1: Story Nodes Endpoint

**File**: `/home/sev/ggbot/api/activities.py` (add new endpoint)

```python
@router.get("/{config_id}/story-nodes")
async def get_story_nodes(
    config_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Return activities pre-grouped by trade_id for story-based rendering.

    Response format:
    {
      "story_nodes": [
        {
          "trade_id": "uuid",
          "trade_type": "aster",
          "symbol": "BTC/USDT",
          "outcome": "win",  // "win", "loss", "open"
          "pnl": 45.50,
          "pnl_pct": 4.1,
          "entry_time": "2025-11-03T10:10:00Z",
          "exit_time": "2025-11-03T14:30:00Z",  // null if open
          "duration_minutes": 260,
          "phases": {
            "pre_entry": [...],    // market_query, analysis, reasoning before entry
            "entry": {...},        // trade_entry_long/short activity
            "monitoring": [...],   // market_query, analysis during trade
            "exit": {...}          // trade_win/loss activity (null if open)
          }
        }
      ],
      "standalone_activities": [...]  // Activities with no trade_id
    }
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Query 1: Get all activities with trade_id
            cur.execute("""
                SELECT
                    activity_id, activity_type, activity_source, summary,
                    details, trade_id, trade_type, related_symbol,
                    created_at, priority, importance
                FROM activities
                WHERE config_id = %s
                  AND trade_id IS NOT NULL
                ORDER BY created_at ASC
            """, (config_id,))

            trade_activities = cur.fetchall()

            # Query 2: Get P&L for each trade from respective tables
            # ... (fetch from paper_trades or live_trades based on trade_type)

            # Group by trade_id
            trade_groups = {}
            for activity in trade_activities:
                trade_id = activity[5]
                if trade_id not in trade_groups:
                    trade_groups[trade_id] = {
                        "trade_id": trade_id,
                        "trade_type": activity[6],
                        "symbol": activity[7],
                        "activities": []
                    }
                trade_groups[trade_id]["activities"].append({
                    "activity_id": activity[0],
                    "type": activity[1],
                    "source": activity[2],
                    "summary": activity[3],
                    "details": activity[4],
                    "timestamp": activity[8].isoformat(),
                    "priority": activity[9],
                    "importance": activity[10]
                })

            # Transform into story nodes with phases
            story_nodes = []
            for trade_id, group in trade_groups.items():
                node = _build_story_node(group)  # Helper function
                story_nodes.append(node)

            # Query 3: Get standalone activities
            cur.execute("""
                SELECT
                    activity_id, activity_type, summary, details,
                    related_symbol, created_at, priority, importance
                FROM activities
                WHERE config_id = %s
                  AND trade_id IS NULL
                ORDER BY created_at ASC
            """, (config_id,))

            standalone = cur.fetchall()

            return {
                "status": "success",
                "story_nodes": story_nodes,
                "standalone_activities": [
                    {
                        "id": str(a[0]),
                        "type": a[1],
                        "summary": a[2],
                        "details": a[3],
                        "symbol": a[4],
                        "timestamp": a[5].isoformat(),
                        "priority": a[6],
                        "importance": a[7]
                    }
                    for a in standalone
                ]
            }

def _build_story_node(group: dict) -> dict:
    """
    Transform activity group into phased story node.

    Phases:
    - pre_entry: Activities before entry (market_query, analysis, reasoning)
    - entry: Trade entry activity (trade_entry_long/short)
    - monitoring: Activities during trade (market_query, analysis)
    - exit: Trade exit activity (trade_win/loss) or None if open
    """
    activities = sorted(group["activities"], key=lambda a: a["timestamp"])

    # Find entry activity (trade_entry_long or trade_entry_short)
    entry_idx = next(
        (i for i, a in enumerate(activities) if a["type"].startswith("trade_entry")),
        None
    )

    # Find exit activity (trade_win or trade_loss)
    exit_idx = next(
        (i for i, a in enumerate(activities) if a["type"] in ["trade_win", "trade_loss"]),
        None
    )

    # Split into phases
    if entry_idx is not None:
        pre_entry = activities[:entry_idx]
        entry = activities[entry_idx]

        if exit_idx is not None:
            monitoring = activities[entry_idx+1:exit_idx]
            exit_activity = activities[exit_idx]
            outcome = "win" if exit_activity["type"] == "trade_win" else "loss"
            exit_time = exit_activity["timestamp"]

            # Extract P&L from exit activity details
            pnl = exit_activity["details"].get("pnl", 0)
            pnl_pct = exit_activity["details"].get("pnl_pct", 0)
        else:
            monitoring = activities[entry_idx+1:]
            exit_activity = None
            outcome = "open"
            exit_time = None
            pnl = 0
            pnl_pct = 0
    else:
        # No entry found (shouldn't happen, but handle gracefully)
        pre_entry = activities
        entry = None
        monitoring = []
        exit_activity = None
        outcome = "unknown"
        exit_time = None
        pnl = 0
        pnl_pct = 0

    # Calculate duration
    if entry and exit_time:
        entry_time = datetime.fromisoformat(entry["timestamp"])
        exit_dt = datetime.fromisoformat(exit_time)
        duration_minutes = int((exit_dt - entry_time).total_seconds() / 60)
    else:
        duration_minutes = None

    return {
        "trade_id": group["trade_id"],
        "trade_type": group["trade_type"],
        "symbol": group["symbol"],
        "outcome": outcome,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "entry_time": entry["timestamp"] if entry else None,
        "exit_time": exit_time,
        "duration_minutes": duration_minutes,
        "phases": {
            "pre_entry": pre_entry,
            "entry": entry,
            "monitoring": monitoring,
            "exit": exit_activity
        }
    }
```

**Checklist**:
- [ ] Add `/story-nodes` endpoint to `api/activities.py`
- [ ] Implement `_build_story_node()` helper for phased grouping
- [ ] Add P&L queries for paper_trades and live_trades tables
- [ ] Test endpoint with agent config (bb2560fd-b053-464f-8a58-8e254e4d36fa)
- [ ] Verify phasing logic with real trade data

---

### Phase 2: Frontend Story Node Rendering (3-4 hours)

**Goal**: Replace time-clustered dots with trade story nodes on chart.

#### Task 2.1: Add Story Node Fetching

**File**: `/home/sev/ggbot/frontend/components/Timeline.jsx`

```javascript
// Add to useEffect data fetching (line 122-181)
const [activitiesRes, balanceSeriesRes, metadataRes, strategyRes, storyNodesRes] = await Promise.all([
  fetch(`/api/v2/activities/${configId}`, { headers }),
  fetch(`/api/v2/activities/${configId}/balance-series?mode=balance`, { headers }),
  fetch(`/api/v2/activities/${configId}/metadata`, { headers }),
  fetch(`/api/v2/configs/${configId}/strategy`, { headers }).catch(() => null),
  fetch(`/api/v2/activities/${configId}/story-nodes`, { headers })  // NEW
]);

// Update state structure
setLog({
  activities: activities.activities || [],
  storyNodes: storyNodes.story_nodes || [],           // NEW
  standaloneActivities: storyNodes.standalone_activities || [],  // NEW
  balanceTimeseries: balanceSeries.balance_series || [],
  metadata: { /* ... */ }
});
```

#### Task 2.2: Story Node Rendering in Chart

**File**: `/home/sev/ggbot/frontend/components/BalanceChartRecharts.tsx`

```typescript
// Add StoryNode interface
interface StoryNode {
  trade_id: string;
  trade_type: string;
  symbol: string;
  outcome: 'win' | 'loss' | 'open';
  pnl: number;
  pnl_pct: number;
  entry_time: string;
  exit_time: string | null;
  duration_minutes: number | null;
  phases: {
    pre_entry: Activity[];
    entry: Activity;
    monitoring: Activity[];
    exit: Activity | null;
  };
}

// Update props
interface BalanceChartRechartsProps {
  balanceData: BalancePoint[];
  storyNodes: StoryNode[];              // NEW: Replace activities
  standaloneActivities: Activity[];    // NEW: Non-trade activities
  onStoryNodeClick?: (node: StoryNode) => void;
}

// Replace clusteredMarkers logic with story node markers
const storyNodeMarkers = useMemo(() => {
  return storyNodes.map(node => {
    const entryTime = new Date(node.entry_time).getTime();
    const balance = interpolateBalance(entryTime);

    // Composite icon: Entry glyph + phase count badge
    const phaseCount =
      node.phases.pre_entry.length +
      (node.phases.entry ? 1 : 0) +
      node.phases.monitoring.length +
      (node.phases.exit ? 1 : 0);

    return {
      time: entryTime,
      balance,
      node,  // Full story node
      color: node.outcome === 'win' ? VIBE.signal :
             node.outcome === 'loss' ? VIBE.ember :
             VIBE.brass,  // open
      phaseCount,
      icon: node.phases.entry?.type === 'trade_entry_long' ? 'long' : 'short'
    };
  });
}, [storyNodes, interpolateBalance]);

// Render story nodes as composite markers
<Scatter
  data={storyNodeMarkers}
  dataKey="balance"
  shape={(props: unknown) => {
    const { cx, cy, payload } = props as {
      cx?: number;
      cy?: number;
      payload?: StoryNodeMarker;
    };
    if (!cx || !cy || !payload) return <g />;

    const size = payload.node.outcome === 'open' ? 32 : 28;  // Larger for open trades
    const halfSize = size / 2;

    return (
      <g
        onClick={() => handleStoryNodeClick(payload.node)}
        style={{ cursor: 'pointer' }}
        className="hover:opacity-80 transition-opacity"
      >
        {/* Background circle with outcome color */}
        <circle
          cx={cx}
          cy={cy}
          r={halfSize}
          fill={VIBE.carbon}
          stroke={payload.color}
          strokeWidth={payload.node.outcome === 'open' ? 3 : 2}
        />

        {/* Entry icon (long/short triangle) */}
        <foreignObject
          x={cx - halfSize / 2}
          y={cy - halfSize / 2}
          width={halfSize}
          height={halfSize}
          style={{ pointerEvents: 'none' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%' }}>
            {payload.icon === 'long' ? Svg.Long(payload.color) : Svg.Short(payload.color)}
          </div>
        </foreignObject>

        {/* Phase count badge */}
        <circle
          cx={cx + halfSize - 4}
          cy={cy - halfSize + 4}
          r={10}
          fill={VIBE.brass}
          stroke={VIBE.carbon}
          strokeWidth={2}
        />
        <text
          x={cx + halfSize - 4}
          y={cy - halfSize + 4}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={VIBE.obsidian}
          fontSize={10}
          fontWeight="bold"
        >
          {payload.phaseCount}
        </text>

        {/* Outcome indicator (for closed trades) */}
        {payload.node.outcome !== 'open' && (
          <>
            <circle
              cx={cx - halfSize + 4}
              cy={cy + halfSize - 4}
              r={8}
              fill={payload.node.outcome === 'win' ? VIBE.signal : VIBE.ember}
              stroke={VIBE.carbon}
              strokeWidth={1.5}
            />
            <text
              x={cx - halfSize + 4}
              y={cy + halfSize - 4}
              textAnchor="middle"
              dominantBaseline="middle"
              fill={VIBE.carbon}
              fontSize={11}
              fontWeight="bold"
            >
              {payload.node.outcome === 'win' ? '↑' : '↓'}
            </text>
          </>
        )}
      </g>
    );
  }}
/>

// Add standalone activity markers (same as before, but separate dataset)
<Scatter
  data={standaloneActivityMarkers}
  dataKey="balance"
  shape={(props) => renderStandaloneActivity(props)}
/>
```

**Checklist**:
- [ ] Update Timeline.jsx to fetch `/story-nodes`
- [ ] Pass storyNodes + standaloneActivities to BalanceChartRecharts
- [ ] Implement composite story node marker rendering
- [ ] Add outcome indicator (up/down arrow badge)
- [ ] Keep standalone activities as separate scatter dataset
- [ ] Test with real story nodes from API

---

### Phase 3: Trade Narrative Panel (3-4 hours)

**Goal**: Vertical timeline showing trade lifecycle phases when story node clicked.

#### Task 3.1: Trade Narrative Panel Component

**File**: `/home/sev/ggbot/frontend/components/TradeNarrativePanel.tsx` (NEW)

```typescript
'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { StoryNode } from './types';

const VIBE = { /* ... same palette ... */ };

interface TradeNarrativePanelProps {
  node: StoryNode;
  onClose: () => void;
}

export function TradeNarrativePanel({ node, onClose }: TradeNarrativePanelProps) {
  const isWin = node.outcome === 'win';
  const isOpen = node.outcome === 'open';

  return (
    <motion.aside
      initial={{ x: 560, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 560, opacity: 0 }}
      transition={{ type: 'tween', duration: 0.25 }}
      className="fixed top-0 right-0 h-full w-full sm:w-[560px] z-40"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0"
        style={{ background: 'rgba(0,0,0,0.4)' }}
        onClick={onClose}
      />

      {/* Panel */}
      <div
        className="relative ml-auto h-full w-full sm:w-[560px] overflow-hidden"
        style={{ backgroundColor: VIBE.carbon, borderLeft: `1px solid ${VIBE.hair}` }}
      >
        {/* Header */}
        <div
          className="px-5 py-4"
          style={{ borderBottom: `1px solid ${VIBE.hair}` }}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm" style={{ color: 'rgba(237,235,231,0.6)' }}>
                Trade Lifecycle
              </div>
              <div className="text-xl font-semibold" style={{ color: VIBE.ivory }}>
                {node.symbol}
              </div>
            </div>
            <button onClick={onClose} style={{ color: 'rgba(237,235,231,0.8)' }}>
              <svg viewBox="0 0 24 24" className="w-5 h-5">
                <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2"/>
              </svg>
            </button>
          </div>

          {/* Outcome Banner */}
          {!isOpen && (
            <div
              className="mt-3 p-3 rounded-lg border"
              style={{
                backgroundColor: isWin ? 'rgba(60,166,224,0.1)' : 'rgba(215,74,31,0.1)',
                borderColor: isWin ? 'rgba(60,166,224,0.3)' : 'rgba(215,74,31,0.3)',
                color: isWin ? VIBE.signal : VIBE.ember
              }}
            >
              <div className="text-2xl font-bold">
                {isWin ? '+' : ''}{node.pnl.toFixed(2)} USD
              </div>
              <div className="text-sm" style={{ opacity: 0.7 }}>
                {node.pnl_pct.toFixed(1)}% • {node.duration_minutes}min
              </div>
            </div>
          )}

          {isOpen && (
            <div className="mt-3 p-3 rounded-lg border" style={{ borderColor: VIBE.brass, backgroundColor: 'rgba(193,168,125,0.1)' }}>
              <div className="text-sm font-medium" style={{ color: VIBE.brass }}>
                🟡 Position Open
              </div>
            </div>
          )}
        </div>

        {/* Phased Timeline */}
        <div className="p-5 space-y-6 overflow-y-auto h-[calc(100%-140px)]">
          {/* Phase 1: Pre-Entry Analysis */}
          {node.phases.pre_entry.length > 0 && (
            <PhaseSection
              title="Entry Analysis"
              icon="🔍"
              activities={node.phases.pre_entry}
              timestamp={node.phases.pre_entry[0]?.timestamp}
            />
          )}

          {/* Phase 2: Entry */}
          {node.phases.entry && (
            <PhaseSection
              title="Trade Entry"
              icon={node.phases.entry.type === 'trade_entry_long' ? '▲' : '▼'}
              activities={[node.phases.entry]}
              timestamp={node.phases.entry.timestamp}
              highlight={true}
            />
          )}

          {/* Phase 3: Monitoring */}
          {node.phases.monitoring.length > 0 && (
            <PhaseSection
              title="Position Monitoring"
              icon="👁️"
              activities={node.phases.monitoring}
              timestamp={node.phases.monitoring[0]?.timestamp}
              collapsible={true}
              defaultCollapsed={node.phases.monitoring.length > 3}
            />
          )}

          {/* Phase 4: Exit */}
          {node.phases.exit && (
            <PhaseSection
              title="Trade Exit"
              icon={node.outcome === 'win' ? '📈' : '📉'}
              activities={[node.phases.exit]}
              timestamp={node.phases.exit.timestamp}
              highlight={true}
            />
          )}
        </div>
      </div>
    </motion.aside>
  );
}

interface PhaseSectionProps {
  title: string;
  icon: string;
  activities: Activity[];
  timestamp: string;
  highlight?: boolean;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

function PhaseSection({ title, icon, activities, timestamp, highlight, collapsible, defaultCollapsed }: PhaseSectionProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed ?? false);

  return (
    <section>
      {/* Phase Header */}
      <div className="flex items-center gap-2 mb-3">
        <div className="text-xl">{icon}</div>
        <div className="font-semibold" style={{ color: VIBE.ivory }}>{title}</div>
        <div className="text-xs font-mono" style={{ color: 'rgba(237,235,231,0.6)' }}>
          {new Date(timestamp).toLocaleString()}
        </div>
        {collapsible && (
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="ml-auto text-sm"
            style={{ color: VIBE.brass }}
          >
            {collapsed ? 'Expand' : 'Collapse'}
          </button>
        )}
      </div>

      {/* Activities */}
      {!collapsed && (
        <div className="space-y-2">
          {activities.map((activity, idx) => (
            <ActivityCard
              key={activity.id || idx}
              activity={activity}
              highlight={highlight}
            />
          ))}
        </div>
      )}

      {collapsed && (
        <div className="text-sm" style={{ color: 'rgba(237,235,231,0.6)' }}>
          {activities.length} {activities.length === 1 ? 'activity' : 'activities'} hidden
        </div>
      )}
    </section>
  );
}

function ActivityCard({ activity, highlight }: { activity: Activity; highlight?: boolean }) {
  return (
    <div
      className="border rounded-lg p-3"
      style={{
        borderColor: highlight ? VIBE.brass : VIBE.hair,
        backgroundColor: highlight ? 'rgba(193,168,125,0.05)' : 'transparent'
      }}
    >
      <div className="text-sm font-medium" style={{ color: VIBE.ivory }}>
        {activity.summary}
      </div>
      {activity.details && (
        <pre
          className="mt-2 text-xs font-mono whitespace-pre-wrap"
          style={{ color: 'rgba(237,235,231,0.75)' }}
        >
          {JSON.stringify(activity.details, null, 2)}
        </pre>
      )}
    </div>
  );
}
```

#### Task 3.2: Integrate Trade Narrative Panel

**File**: `/home/sev/ggbot/frontend/components/Timeline.jsx`

```javascript
const [selectedStoryNode, setSelectedStoryNode] = useState(null);

// Pass callback to BalanceChartRecharts
<BalanceChartRecharts
  balanceData={log.balanceTimeseries}
  storyNodes={log.storyNodes}
  standaloneActivities={log.standaloneActivities}
  onStoryNodeClick={(node) => setSelectedStoryNode(node)}
/>

// Render Trade Narrative Panel
<AnimatePresence>
  {selectedStoryNode && (
    <TradeNarrativePanel
      node={selectedStoryNode}
      onClose={() => setSelectedStoryNode(null)}
    />
  )}
</AnimatePresence>
```

**Checklist**:
- [ ] Create TradeNarrativePanel.tsx component
- [ ] Implement PhaseSection with collapsible logic
- [ ] Add outcome banner (win/loss P&L, open status)
- [ ] Integrate panel into Timeline.jsx
- [ ] Test with closed trade (show all phases + outcome)
- [ ] Test with open trade (show pre_entry + entry + monitoring, no exit)
- [ ] Test collapsing monitoring phase (>3 activities)

---

### Phase 4: Connection Lines & Highlighting (2-3 hours)

**Goal**: Visual causality - draw lines connecting phases within a story node.

#### Task 4.1: Connection Lines in Chart

**File**: `/home/sev/ggbot/frontend/components/BalanceChartRecharts.tsx`

```typescript
// Add selectedStoryNodeId state
const [selectedStoryNodeId, setSelectedStoryNodeId] = useState<string | null>(null);

// Handle click
const handleStoryNodeClick = (node: StoryNode) => {
  setSelectedStoryNodeId(node.trade_id);
  if (onStoryNodeClick) onStoryNodeClick(node);
};

// Render connection lines as custom overlay
const ConnectionLinesOverlay = () => {
  if (!selectedStoryNodeId) return null;

  const selectedNode = storyNodes.find(n => n.trade_id === selectedStoryNodeId);
  if (!selectedNode) return null;

  // Get all activity timestamps in this trade
  const timestamps = [
    ...selectedNode.phases.pre_entry.map(a => new Date(a.timestamp).getTime()),
    selectedNode.phases.entry ? new Date(selectedNode.phases.entry.timestamp).getTime() : null,
    ...selectedNode.phases.monitoring.map(a => new Date(a.timestamp).getTime()),
    selectedNode.phases.exit ? new Date(selectedNode.phases.exit.timestamp).getTime() : null
  ].filter(Boolean);

  // Draw curved lines connecting each timestamp
  return (
    <svg className="absolute inset-0 pointer-events-none">
      <defs>
        <linearGradient id="connectionGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={VIBE.signal} stopOpacity={0.3} />
          <stop offset="100%" stopColor={VIBE.brass} stopOpacity={0.6} />
        </linearGradient>
      </defs>
      {timestamps.map((time, idx) => {
        if (idx === timestamps.length - 1) return null;

        const nextTime = timestamps[idx + 1];
        const balance1 = interpolateBalance(time);
        const balance2 = interpolateBalance(nextTime);

        // Convert to chart coordinates
        const x1 = mapTimeToChartX(time);
        const y1 = mapBalanceToChartY(balance1);
        const x2 = mapTimeToChartX(nextTime);
        const y2 = mapBalanceToChartY(balance2);

        return (
          <line
            key={idx}
            x1={x1}
            y1={y1}
            x2={x2}
            y2={y2}
            stroke="url(#connectionGradient)"
            strokeWidth={2}
            strokeDasharray="5,5"
            opacity={0.7}
          />
        );
      })}
    </svg>
  );
};

// Render overlay above chart
<div className="relative h-full">
  <ResponsiveContainer width="100%" height="100%">
    {/* Existing chart */}
  </ResponsiveContainer>
  <ConnectionLinesOverlay />
</div>
```

**Checklist**:
- [ ] Add selectedStoryNodeId state
- [ ] Implement ConnectionLinesOverlay component
- [ ] Map timestamps to chart coordinates
- [ ] Draw dashed gradient lines between phases
- [ ] Test highlighting with multiple story nodes
- [ ] Clear selection when clicking outside

---

### Phase 5: Polish & Testing (2-3 hours)

**Goal**: Production-ready timeline with all features working smoothly.

#### Task 5.1: Edge Cases & Error Handling

**Test Scenarios**:
- [ ] Trade with no pre-entry analysis (agent enters immediately)
- [ ] Trade with no monitoring (agent exits right after entry)
- [ ] Open trade (no exit phase yet)
- [ ] Multiple trades on same symbol
- [ ] Very long monitoring phase (50+ activities)
- [ ] Standalone activities only (no trades yet)
- [ ] Empty timeline (new bot)

#### Task 5.2: Performance Optimization

- [ ] Memoize story node transformations
- [ ] Optimize connection line rendering (only selected trade)
- [ ] Add virtual scrolling to Trade Narrative Panel
- [ ] Test with 100+ story nodes (6 months of trading)

#### Task 5.3: Mobile Responsiveness

- [ ] Story node markers scale correctly on small screens
- [ ] Trade Narrative Panel full-width on mobile
- [ ] Connection lines visible/hidden based on viewport
- [ ] Touch gestures for pan/zoom

---

## Success Metrics

**Phase 1 (Backend)**:
- [ ] `/story-nodes` endpoint returns properly grouped trades
- [ ] Phasing logic correctly splits pre_entry/entry/monitoring/exit
- [ ] P&L data accurate from paper_trades and live_trades
- [ ] Standalone activities separate from story nodes

**Phase 2 (Story Nodes)**:
- [ ] Chart shows story node markers, not individual activity dots
- [ ] Composite icons display: entry glyph + phase count badge
- [ ] Outcome indicators show win/loss (up/down arrow)
- [ ] Standalone activities render separately

**Phase 3 (Narrative Panel)**:
- [ ] Vertical timeline shows all phases in order
- [ ] Outcome banner displays P&L for closed trades
- [ ] Collapsible monitoring section works
- [ ] Activities display readable details

**Phase 4 (Causality)**:
- [ ] Connection lines draw between phases when trade selected
- [ ] Highlighting makes selected trade visually distinct
- [ ] Clicking story node opens narrative panel + highlights

**Phase 5 (Polish)**:
- [ ] All edge cases handled gracefully
- [ ] Performance smooth with large datasets
- [ ] Mobile responsive
- [ ] No console errors

---

## Technical Debt & Future Work

**Phase 1 Gaps (Orchestrator Logging)**:
- Scheduled bots don't log activities (only agents do)
- Need to add logging to `_run_extraction_v2()`, `_run_decision_v2()`, `_run_trading_v2()`
- Location: `/home/sev/ggbot/ggbot.py` lines ~794-900

**Phase 1 Gaps (TP/SL Monitoring)**:
- Aster automatic TP/SL fills not detected
- Need background service: `scripts/monitor_aster_orders.py` (PM2)
- Polls every 30s, logs `trade_win/loss` when orders fill

**Future Enhancements**:
- [ ] Real-time SSE updates (replace 10s polling)
- [ ] Activity search & filtering UI
- [ ] Export timeline as image/PDF
- [ ] Playback mode (time scrubber to replay day)
- [ ] Multi-bot comparison view
- [ ] Activity analytics (patterns vs outcomes)

---

## Current Implementation Fixes Needed

Based on comprehensive review, these issues must be fixed BEFORE implementing story nodes:

### 🔴 Critical Fixes

1. **Fix Strategy Endpoint** (Line 141 of Timeline.jsx)
   ```javascript
   // Wrong:
   fetch(`/api/v2/configs/${configId}/strategy`, ...)

   // Right:
   fetch(`/api/v2/activities/${configId}/strategy`, ...)
   ```

2. **Fix Activity Type Consistency**
   - Remove `trade_exit` from BalanceChartRecharts.tsx (line 116)
   - Backend uses `trade_win`/`trade_loss` (confirmed in TODO.md)

3. **Test Balance Interpolation Accuracy**
   - Current: Linear interpolation (line 217-245)
   - Issue: Assumes smooth balance changes, but trades are discrete steps
   - Solution: Use step interpolation OR ensure balance_series includes entry for every trade

### 🟠 High Priority

4. **Add 10s Polling** (Real-time updates)
   ```javascript
   useEffect(() => {
     const interval = setInterval(fetchData, 10000);
     return () => clearInterval(interval);
   }, [configId, session]);
   ```

5. **Switch to P&L Mode**
   ```javascript
   // Line 139: Change balance → pnl
   fetch(`/api/v2/activities/${configId}/balance-series?mode=pnl`, { headers })
   ```

### 🟡 Medium Priority

6. **Convert Timeline.jsx to TypeScript**
   - Rename `.jsx` → `.tsx`
   - Add proper interfaces
   - Remove JSDoc comments

7. **Persist Filter State**
   ```javascript
   const [visibleTypes, setVisibleTypes] = useLocalStorage('timeline-filters', defaultFilters);
   ```

---

## References

**Code-Scout Verification Report**: See above for comprehensive verification of:
- Activities table structure (14 columns, 7 indexes, trade_id linking)
- Agent MCP tool logging (7/11 tools log activities)
- API endpoints (3 exist, /story-nodes missing)
- Data consistency issues (TP/SL monitoring, scheduled bot logging)

**Old Documentation** (for context):
- `/home/sev/ggbot/DOCS/ACTIVITY_LOGGING_IMPLEMENTATION_COMPLETE.md` - Agent logging complete
- `/home/sev/ggbot/DOCS/ACTIVITY_LOGGING_COMPLETE_MAP.md` - Comprehensive activity map
- `/home/sev/ggbot/DOCS/todo/ACTIVITY_TIMELINE.md` - Original Canvas-based timeline plan

**Key Files**:
- Frontend: `frontend/components/Timeline.jsx` (432 lines), `BalanceChartRecharts.tsx` (588 lines)
- Backend: `api/activities.py` (3 endpoints), `core/common/activity_logger.py` (logging helper)
- Agent: `agent/mcp_server.py` (7 tools with auto-logging)
- Database: `activities` table with trade_id linking

---

**Last Updated**: 2025-11-06
**Status**: Planning Complete - Ready for Implementation
**Estimated Effort**: 12-15 hours (5 phases)
**Next Step**: Phase 1 - Backend Story Nodes API
