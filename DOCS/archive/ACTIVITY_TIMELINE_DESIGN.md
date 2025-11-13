# Activity Timeline Viewer - Design Document

**Purpose:** Public view-only page showcasing bot/agent trading activity overlaid on performance chart
**Route:** `/view/[config_id]`
**Target:** Vibe Trading Competition submission - needs to be visually impressive and innovative
**Status:** Design phase - seeking architectural guidance

---

## 🎯 Core Vision

Create an **interactive performance chart** where every bot/agent action is a **clickable icon** positioned at the exact moment it occurred. Users can zoom in/out to see more/less detail, scroll through time, and click activities to see full context.

### The "Aha!" Moment

Traditional trading dashboards show *what happened* (trades, P&L). This shows *why it happened* (the bot's thought process, data queries, decisions). You can literally see the relationship between:
- Agent querying RSI data → price movement → trade entry
- Multiple "wait" decisions → patience → profitable exit
- Strategy updates → improved performance

---

## 🎨 Visual Design Concept

### Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  [ggbots logo]    Bot Name: "RSI Scalper v2"    [Share]│
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Performance: +12.5%  │  Trades: 47  │  Win Rate: 68% │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Zoom: [1h] [4h] [1d] [1w] [All]         📅 Jan 21    │
│                                                         │
│  $10,500 ┤                    ╭─── 📊📊🔴              │
│          │                ╭───╯  🔴 💭                  │
│  $10,250 ┤            ╭───╯ 💭 📊                       │
│          │        ╭───╯  📊 💭                          │
│  $10,000 ┤────🟢───╯ 📊💭 📊                            │
│          │                                             │
│          └─────────────────────────────────────────    │
│           2:00 PM    3:00 PM    4:00 PM    5:00 PM    │
│                                                         │
│  🟢 Entry  🔴 Exit  💭 Decision  📊 Data Query         │
│  🔄 Adjust  ⏱️ Wait  📝 Note  🔧 Strategy Update      │
│                                                         │
│  ◄ Earlier          [Jump to Now]          Later ►     │
│                                                         │
└─────────────────────────────────────────────────────────┘
        ← Swipe/Drag to scroll through time →
```

---

## 🎭 User Interactions

### Primary Interactions

1. **Zoom Level Selection**
   - Buttons: `1h`, `4h`, `1d`, `1w`, `All`
   - Changes time window visible
   - Affects icon density (more zoom = more icons)
   - Smooth animation between zoom levels

2. **Time Scrolling**
   - Desktop: Click/drag chart left-right
   - Mobile: Swipe gestures
   - Arrow buttons for precise navigation
   - "Jump to Now" button to return to present
   - Date indicator shows current view position

3. **Activity Clicking**
   - Click/tap any icon → centered modal opens
   - Modal shows full activity details
   - If grouped activities → accordion list
   - Close modal with X, ESC key, or click outside

4. **Legend Interaction** (Optional enhancement)
   - Click legend items to filter/highlight activity types
   - "Show only trades" mode
   - "Hide low-priority activities" toggle

### Mobile-Specific

- **Pinch-to-zoom**: Change zoom level naturally
- **Swipe**: Horizontal scroll through time
- **Tap**: Open activity detail
- **Long-press**: Show quick preview tooltip

---

## 📊 Chart Architecture Options

### Option 1: Recharts with Custom Layers
**Approach:** Use Recharts for line/area chart, overlay custom SVG layer for activity icons

**Pros:**
- Recharts handles axis scaling, tooltips, responsive sizing
- Full control over icon positioning via custom layer
- Good TypeScript support
- Relatively simple to implement

**Cons:**
- May need custom logic for icon grouping
- Performance could be issue with 1000+ icons
- Scroll/zoom interactions need custom implementation

**Best for:** Rapid prototyping, getting to MVP quickly

---

### Option 2: Visx (Low-Level D3 React Wrapper)
**Approach:** Build custom chart using Visx primitives (scales, axes, paths) + React components for icons

**Pros:**
- More control than Recharts
- Better performance for complex interactions
- Scales well to large datasets
- Great for custom scroll/zoom behavior

**Cons:**
- Steeper learning curve
- More code to write
- Need to handle more edge cases manually

**Best for:** Production app with complex requirements

---

### Option 3: Pure D3 with React Wrapper
**Approach:** D3 handles all chart logic, React wraps it and manages data

**Pros:**
- Maximum control and performance
- D3's zoom/pan built-in
- Industry standard for complex visualizations
- Best for smooth animations

**Cons:**
- Mixing D3 and React lifecycle can be tricky
- Most complex to implement
- Longer development time

**Best for:** When polish and performance are critical

---

### Option 4: Lightweight Charts (TradingView Library)
**Approach:** Use TradingView's lightweight-charts library for candlestick-style chart, overlay markers

**Pros:**
- Built for financial data
- Excellent performance
- Professional trading UI feel
- Great zoom/pan out of the box

**Cons:**
- Less flexible for custom visualizations
- Marker customization may be limited
- Might be overkill for line chart

**Best for:** If we want traditional trading chart aesthetic

---

### Option 5: Canvas-Based Custom Solution
**Approach:** Draw entire chart to Canvas, use React for UI layer (modals, controls)

**Pros:**
- Best performance for huge datasets (10k+ points)
- Smooth animations at 60fps
- Full control over rendering

**Cons:**
- Most work to implement
- Accessibility challenges
- Harder to make responsive

**Best for:** Extreme performance requirements

---

## 🎨 Activity Type System

### Templatable Activity Definition

```typescript
interface ActivityDefinition {
  type: string              // 'trade_entry_long', 'market_query', etc.
  priority: 1 | 2 | 3       // Determines visibility at zoom levels
  icon: string              // Emoji or icon name
  color: string             // Hex color for icon/badge
  label: string             // Human-readable name
  description: string       // Short description for tooltip
}
```

### Example Activity Types (Mockable)

**Priority 1: Always Visible**
- `trade_entry_long` - 🟢 Long Entry
- `trade_entry_short` - 🔴 Short Entry
- `trade_exit` - ⬛ Position Closed
- `position_adjusted` - 🔄 Position Modified

**Priority 2: Medium Zoom**
- `decision_made` - 💭 AI Decision
- `market_query` - 📊 Data Queried
- `agent_wait` - ⏱️ Waiting Period

**Priority 3: High Zoom Only**
- `observation_recorded` - 📝 Trade Note
- `strategy_updated` - 🔧 Strategy Change
- `agent_reasoning` - 💡 Agent Thought

### Activity Grouping Logic

When multiple activities occur in same time bucket:

**Visual Representation Options:**
1. **Stacked Icons** - Icons physically stack vertically
2. **Badge Counter** - Single icon with "5" badge
3. **Grouped Icon** - Special "multiple activities" icon
4. **Color Blend** - Blended color representing mix of activities

**On Click:**
- Modal shows list of all activities in that group
- Each activity is an accordion item
- Can expand individual activities for details

---

## 🎯 Zoom Level Behavior

### Visibility Rules

| Zoom Level | Time Window | Icon Spacing | Grouping Threshold | Visible Priorities |
|------------|-------------|--------------|-------------------|-------------------|
| **1h**     | 60 minutes  | ~5min apart  | None (all individual) | All (1,2,3) |
| **4h**     | 4 hours     | ~20min apart | 10min buckets     | High + Medium (1,2) |
| **1d**     | 24 hours    | ~1hr apart   | 1hr buckets       | High only (1) |
| **1w**     | 7 days      | ~4hr apart   | 4hr buckets       | Critical (trades) |
| **All**    | Full history | ~1day apart | 1day buckets      | Trades only |

### Grouping Strategy

```
If activities_in_bucket.length > 1:
  If all same type:
    Show single icon with count badge
  Else:
    Show highest priority icon with "mixed" indicator

On click grouped activity:
  Show modal with sorted list:
    - Priority 1 activities first
    - Then Priority 2
    - Then Priority 3
    - Within priority, sort by time ascending
```

---

## 📱 Responsive Design

### Desktop (>768px)
- Full width chart with side margins
- Legend below chart
- Keyboard shortcuts (arrow keys for scroll, +/- for zoom)
- Hover tooltips on icons

### Tablet (768px - 1024px)
- Slightly smaller chart
- Legend on side or below
- Touch + mouse support

### Mobile (<768px)
- Full-width chart
- Vertical layout (stats above chart)
- Legend collapsed by default (tap to expand)
- Touch-optimized icon sizes (44x44px minimum)
- Bottom sheet modal (not centered)

---

## 🎭 Modal Design

### Single Activity Modal

```
┌──────────────────────────────────────────┐
│  🟢 Long Entry - Jan 21, 2:17 PM      ✕ │
├──────────────────────────────────────────┤
│                                          │
│  Symbol: BTC/USDT                        │
│  Entry Price: $42,150                    │
│  Position Size: $5,000 (10x leverage)    │
│  Stop Loss: $41,800 (-5%)                │
│  Take Profit: $43,200 (+10%)             │
│                                          │
│  Confidence: 75%                         │
│                                          │
│  ─── Reasoning ───                       │
│  "RSI 1h at 32 (oversold). Strong       │
│  volume confirmation. Funding rate       │
│  declining. DXY showing weakness.        │
│  All signals align for long entry."      │
│                                          │
│  ─── Market Data Context ───             │
│  [Expandable section showing all data    │
│   points that were available at this     │
│   moment - optional enhancement]         │
│                                          │
└──────────────────────────────────────────┘
```

### Grouped Activities Modal

```
┌──────────────────────────────────────────┐
│  5 Activities - Jan 21, 2:15-2:20 PM  ✕ │
├──────────────────────────────────────────┤
│                                          │
│  [▼] 🟢 Long Entry (2:17 PM)            │
│      Entry: $42,150, Size: $5,000...    │
│                                          │
│  [▼] 📊 Market Data Query (2:16 PM)     │
│      Queried: RSI, MACD, Funding...     │
│                                          │
│  [▼] 💭 Decision: Enter (2:15 PM)       │
│      Confidence: 75%                     │
│                                          │
│  [▼] 📊 Market Data Query (2:14 PM)     │
│      Queried: RSI, Volume               │
│                                          │
│  [▼] 💭 Decision: Wait (2:10 PM)        │
│      "Need more confirmation..."         │
│                                          │
└──────────────────────────────────────────┘
```

---

## 🎨 Visual Polish Ideas

### Balance Line Enhancements
- **Green gradient** when above starting balance
- **Red gradient** when below starting balance
- **Glow effect** on line for premium feel
- **Smooth curves** (monotone interpolation)

### Icon Rendering
- **Drop shadow** for depth
- **Pulse animation** when new activity arrives (real-time)
- **Scale on hover** (desktop)
- **Connected lines** between related activities (entry → exit)

### Background
- **Subtle grid** for time reference
- **Day/night zones** (different background tint)
- **Volatility bands** (optional: show price volatility as shaded area)

### Transitions
- **Smooth zoom** animation (300ms ease-out)
- **Scroll inertia** (momentum scrolling)
- **Icon fade in/out** as zoom changes
- **Modal slide up** (mobile) or fade in (desktop)

---

## 🚀 Competition Submission Angle

### Why This Wins

1. **Innovation**: No one shows trading activity this way
2. **Transparency**: Full audit trail of bot behavior
3. **Educational**: Visual learning - see what works
4. **Beautiful**: Clean, modern, premium design
5. **Interactive**: Engaging, not just static charts

### Demo Strategy

**Show progression:**
1. Start at "All" view - show full bot history at a glance
2. Zoom to "1d" - point out critical trades
3. Zoom to "1h" - show agent's thought process
4. Click trade entry - show full context and reasoning
5. Scroll back - show bot learning over time

**Key talking points:**
- "Every decision the bot makes is visible"
- "You can see exactly why it entered this trade"
- "Notice how it waits patiently here? That's the agent being strategic"
- "This isn't a black box - it's full transparency"

---

## 🎯 Mock Data Structure

For initial development without real backend:

```typescript
interface MockActivityLog {
  activities: Array<{
    id: string
    timestamp: string // ISO format
    type: string // from ActivityDefinition
    priority: 1 | 2 | 3
    data: {
      // Type-specific fields
      // For entry: symbol, price, size, sl, tp, reasoning
      // For query: data_points, results, reason
      // For wait: duration, reasoning
    }
  }>

  balanceTimeseries: Array<{
    timestamp: string
    balance: number
  }>

  metadata: {
    botName: string
    startingBalance: number
    currentBalance: number
    totalTrades: number
    winRate: number
    performance: number // percentage
  }
}
```

**Example timeline scenario to mock:**
- Bot starts at $10,000
- Day 1: Makes 3 trades (2 wins, 1 loss) → $10,300
- Day 2: Patience - lots of "wait" decisions, only 1 trade → $10,450
- Day 3: Active - 5 trades including strategy update → $10,750
- Day 4: 2 trades, solid performance → $11,250

This gives variety of activities to visualize.

---

## 🤔 Open Design Questions

### Chart Library Choice
**Question:** Which approach balances speed-to-market with quality?
- Recharts = fastest but potentially limiting?
- Visx = middle ground?
- D3 = most powerful but slowest?
- Something else entirely?

### Icon Density Management
**Question:** How to handle extremely dense activity periods?
- Always group if >X per bucket?
- Let icons overlap with z-index?
- Show heatmap intensity instead?

### Performance Line Style
**Question:** Simple line, area chart, or candlestick?
- Line = cleanest, shows trend
- Area = visually heavier, shows magnitude better
- Candlestick = traditional trading, but overkill for balance?

### Activity Click Behavior
**Question:** Modal, side panel, or inline expansion?
- Modal = focused but blocks chart
- Side panel = keeps chart visible but splits attention
- Inline = subtle but can shift chart layout

### Real-time Updates
**Question:** How to handle live trading bot?
- Auto-scroll to follow bot?
- "New activity" notification?
- Pause mode to freeze view?

### Color Scheme
**Question:** Match existing ggbots brand or optimize for readability?
- Current charcoal/bone palette?
- High-contrast for chart clarity?
- Customizable themes?

---

## 🎨 Suggested Color Palette

### Chart Colors
- **Balance Line**: `#10b981` (green-500) for positive, `#f43f5e` (rose-500) for negative
- **Grid Lines**: `#36363d` (charcoal-600, 20% opacity)
- **Background**: `#161618` (charcoal-900)
- **Text**: `#e3e5e6` (bone-200)

### Activity Icon Colors
- **Entry Long**: `#10b981` (emerald-400)
- **Entry Short**: `#f43f5e` (rose-400)
- **Exit**: `#6b7280` (gray-500)
- **Decision**: `#8b5cf6` (violet-500)
- **Data Query**: `#3b82f6` (blue-500)
- **Wait**: `#64748b` (slate-500)
- **Observation**: `#94a3b8` (slate-400)
- **Strategy**: `#a855f7` (purple-500)

---

## 🎯 Success Metrics (For Iteration)

After initial version, measure:
- **Engagement**: Average time on page
- **Interactions**: Click-through rate on activities
- **Comprehension**: Do users understand bot behavior?
- **Delight**: Subjective feedback on "wow factor"

---

## 🚦 Implementation Phases (High Level)

### Phase 1: Static Prototype
- Fixed zoom level (4h)
- Mock data
- Basic line chart + icons
- Simple click → modal

### Phase 2: Core Interactions
- Zoom level switching
- Time scrolling
- Activity grouping
- Responsive design

### Phase 3: Polish
- Animations
- Mobile gestures
- Visual enhancements
- Performance optimization

### Phase 4: Real Data
- Backend integration
- Real-time updates
- Proper authentication
- Production deployment

---

## 📝 Notes for Design Review

This is a complex visualization that needs to balance:
- **Information density** vs **clarity**
- **Interactivity** vs **simplicity**
- **Innovation** vs **familiarity**
- **Beauty** vs **performance**

The goal is to create something that:
1. Makes judges go "wow, I've never seen this"
2. Clearly demonstrates bot transparency
3. Works beautifully on mobile
4. Can scale to production with real users

**Key question for design reviewers:** What's the best architectural approach for a smooth, performant, beautiful chart with complex interactions?

---

**Document Version:** 1.0
**Created:** 2025-01-30
**Purpose:** Design specification for external review and refinement
