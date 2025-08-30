# Dashboard Page Implementation Plan

## Overview  
Create a production-ready dashboard at `/dashboard` by duplicating the demo page and refactoring it to use real user authentication (Supabase) and config_id-based state management with live data.

## Phase 1: Duplication & Cleanup

### 1.1 Duplicate Demo Page
- Copy `/app/demo/page.tsx` → `/app/dashboard/page.tsx`
- Copy all imported components to ensure independence
- Maintain the visual design and layout structure

### 1.2 Remove Demo-Specific Code
Remove the following demo artifacts:

#### Constants & Mock Data
- [ ] Remove `DEMO_USER_ID` constant
- [ ] Remove `realTradingData` object (static trade history)
- [ ] Remove hardcoded "ggbot-01" config_id references
- [ ] Remove mock profit/loss data arrays

#### Demo State Variables
- [ ] Remove `demoStarted` state
- [ ] Remove `livePositions` state (will be replaced with real data)
- [ ] Remove `expandedReasoningIds` (move to component level if needed)

#### Demo Logic
- [ ] Remove `handleDemoMessage` callback
- [ ] Remove demo-specific WebSocket message handling
- [ ] Remove simulated position creation logic
- [ ] Remove mock P&L update intervals
- [ ] Remove special casing for demo bot in FloatingActionButtons

### 1.3 Clean Component Props
- [ ] Update FloatingActionButtons to remove `demoStarted` prop
- [ ] Remove demo-specific conditionals from component interactions

## Phase 2: Config ID State Architecture

### 2.1 Core State Structure
```typescript
// Primary state in dashboard component
const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null)

// Derived state from store
const selectedBot = useBotStore(state => state.getBotById(selectedConfigId))
const userBots = useBotStore(state => state.getBotsByUser(userId))
```

### 2.2 State Flow Design
```
GGBot Circle (Selector)
    ↓
selectedConfigId (Source of Truth)
    ↓
All UI Components Subscribe:
    - GGBotConfig Panel
    - Dashboard Cards
    - Trade Tables
    - Performance Charts
    - WebSocket Subscriptions
```

### 2.3 Component Updates

#### GGBot Circle Component
- Make it the primary bot selector
- On carousel navigation: `setSelectedConfigId(bot.config_id)`
- On bot click: `setSelectedConfigId(bot.config_id)`
- Highlight/indicate which bot is selected

#### Dashboard Cards
- Subscribe to `selectedConfigId`
- Fetch metrics for selected bot only
- Update card titles to show bot name

#### Trade Tables
- Filter trades by `selectedConfigId`
- Real-time updates only for selected bot
- Clear tables when switching bots

#### Performance Charts
- Load historical data for `selectedConfigId`
- Reset chart on bot switch
- Show loading state during data fetch

## Phase 3: Data Management

### 3.1 API Integration (Supabase)
```typescript
// Fetch bot-specific data using Supabase client
const fetchBotData = async (configId: string) => {
  const [metrics, trades, positions] = await Promise.all([
    supabase.from('bot_metrics').select('*').eq('config_id', configId),
    supabase.from('paper_trades').select('*').eq('config_id', configId),
    supabase.from('positions').select('*').eq('config_id', configId)
  ])
  return { metrics, trades, positions }
}

// Use effect to reload on selection change
useEffect(() => {
  if (selectedConfigId) {
    fetchBotData(selectedConfigId)
  }
}, [selectedConfigId])
```

### 3.2 Real-time Updates (Supabase)
```typescript
// Subscribe to selected bot only using Supabase real-time
useEffect(() => {
  if (selectedConfigId) {
    const subscription = supabase
      .channel(`bot:${selectedConfigId}`)
      .on('postgres_changes', { event: '*', schema: 'public' }, handleUpdate)
      .subscribe()
    
    return () => subscription.unsubscribe()
  }
}, [selectedConfigId])
```

### 3.3 Store Updates
Extend botStore with:
- `selectedConfigId` state
- `setSelectedBot(configId)` action
- Selectors for bot-specific data
- Cache management for bot data

## Phase 4: User Experience

### 4.1 Loading States
- Show skeleton loaders when switching bots
- Maintain previous data during load (no flash)
- Progressive data loading (cards → tables → charts)

### 4.2 Error Handling
- Handle missing config_id gracefully
- Show empty states for bots with no data
- Provide clear error messages
- Fallback to first available bot if selected is deleted

### 4.3 Persistence
- Save `selectedConfigId` to localStorage
- Restore on page refresh
- Validate saved ID still exists
- Clear on logout

## Phase 5: Authentication & Routing

### 5.1 Route Protection (Supabase Auth)
```typescript
// /app/dashboard/layout.tsx
export default function DashboardLayout({ children }) {
  const { user, isLoading } = useSupabaseAuth()
  
  if (isLoading) return <LoadingScreen />
  if (!user) return <Redirect to="/login" />
  
  return children
}
```

### 5.2 User Context (Supabase)
- Get real user ID from Supabase Auth
- Load user-specific bots using Row Level Security
- Multi-user isolation handled automatically by Supabase RLS

## Implementation Checklist

### Prerequisites
- [ ] Supabase project setup with auth configured
- [ ] Database schema with Row Level Security policies
- [ ] Remove all mock data from existing components
- [ ] BotConfig domain models integrated

### Step-by-Step Implementation
1. [ ] Create `/app/dashboard` directory
2. [ ] Copy demo page and components
3. [ ] Remove all demo-specific code
4. [ ] Implement `selectedConfigId` state
5. [ ] Update GGBot component as selector
6. [ ] Connect dashboard cards to selected bot
7. [ ] Connect trade tables to selected bot
8. [ ] Implement real data fetching
9. [ ] Set up WebSocket subscriptions
10. [ ] Add loading and error states
11. [ ] Implement persistence
12. [ ] Add authentication
13. [ ] Test bot switching thoroughly
14. [ ] Optimize performance (memoization, etc.)

## Migration Strategy

### Gradual Rollout
1. Keep demo page unchanged at `/demo`
2. Develop dashboard at `/dashboard` 
3. Test with internal users first
4. Gradually migrate users from demo to dashboard
5. Eventually deprecate demo or keep for showcase

### Shared Components
Components that can be reused without modification:
- GGBot circle (with selector enhancement)
- GGBotConfig panel
- FloatingActionButtons (minus demo props)
- Trade table components
- Chart components

Components needing refactoring:
- Dashboard cards (remove mock data)
- Status displays (real-time data)

## Success Criteria

### Functionality
- [ ] Users can select any of their bots
- [ ] All UI updates to show selected bot's data
- [ ] Real-time updates work for selected bot
- [ ] Bot switching is smooth and fast
- [ ] No demo artifacts remain

### Performance
- [ ] Bot switching < 200ms
- [ ] No unnecessary re-renders
- [ ] Efficient WebSocket subscriptions
- [ ] Proper cleanup on unmount

### User Experience
- [ ] Clear indication of selected bot
- [ ] Smooth transitions between bots
- [ ] Loading states during data fetch
- [ ] Error recovery without page refresh
- [ ] State persistence across sessions

## Notes

### Why This Approach?
1. **Clean separation**: Demo remains untouched for stability
2. **Proper architecture**: Build it right from the start
3. **Easier testing**: Can A/B test demo vs dashboard
4. **Risk mitigation**: No risk of breaking existing demo
5. **Clear mental model**: Config ID as single source of truth

### Potential Challenges
- Keeping components in sync between demo and dashboard
- Managing shared component updates
- WebSocket subscription management
- Cache invalidation on bot switch
- Performance with many bots

### Future Enhancements
- Multi-bot view (compare 2-4 bots)
- Bot grouping/folders
- Quick switcher (cmd+K style)
- Keyboard navigation between bots
- Bot search/filter in selector