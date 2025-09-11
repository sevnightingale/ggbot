# Dashboard V2 Implementation Plan

**Version**: 1.0  
**Date**: 2025-09-11  
**Status**: Implementation Plan  
**Scope**: Complete dashboard rebuild using existing components  

## Executive Summary

Build a new dashboard that properly orchestrates existing components (GGBot.tsx, GGBotConfig.tsx, FloatingActionButtons.tsx) with real-time APScheduler integration, WebSocket state management, and proper countdown timers. Focus on the missing pieces rather than rebuilding existing functionality.

## Core Principle

**Orchestrate, Don't Recreate**: Use existing 25,000-line GGBotConfig.tsx, mature FloatingActionButtons.tsx, and proven GGBot.tsx components. Build the missing infrastructure to make them work together properly.

---

## Phase 1: Foundation Architecture

### Step 1.1: Create Dashboard-V2 Structure
**Goal**: Establish clean page structure with proper component orchestration
**Location**: `frontend/app/dashboard-v2/`

**Tasks**:
- Create minimal coordination page (target: <150 lines)
- Set up three-column desktop layout with GGBot carousel center-focused
- Add error boundaries for each section
- Implement bot selection state management
- Connect existing components with proper props
- Design for desktop-first, mobile responsive implementation comes in Phase 7

### Step 1.2: Custom Hooks Development
**Goal**: Create data integration layer between backend systems and existing components

**Required Hooks**:
- `useSchedulerStatus()` - Query APScheduler for active jobs and next run times
- `useCountdownTimer()` - Live countdown calculation for idle bots
- `useBotStatus()` - Combine database state + scheduler status + WebSocket updates
- `useBotMetrics()` - Performance data fetching for PerformancePanel
- `useBotActivity()` - Live activity data for ActivityPanel

### Step 1.3: Component Integration Points
**Goal**: Define clean interfaces between existing components and new infrastructure

**Integration Requirements**:
- GGBot.tsx receives real-time status and countdown messages
- FloatingActionButtons.tsx triggers scheduler enable/disable
- GGBotConfig.tsx saves configurations and triggers bot updates
- All components receive proper error states and loading indicators

---

## Phase 2: Real-Time Infrastructure

### Step 2.1: APScheduler Integration
**Goal**: Connect frontend to backend scheduler system for live countdown timers

**Backend Enhancements**:
- Enhance `/api/v2/scheduler/status` endpoint with per-bot information
- Ensure start/stop endpoints update both database and APScheduler
- Return next run times in all bot-related API responses

**Frontend Integration**:
- Query scheduler status on page load and every 30 seconds
- Calculate live countdowns for idle bots
- Display "Next run in 3m47s" messages in GGBot components

### Step 2.2: WebSocket State Coordination
**Goal**: Ensure WebSocket updates properly feed into existing GGBot component states

**State Flow Requirements**:
- WebSocket messages update bot status in real-time
- GGBot.tsx receives proper phase values (idle, extraction, decision, trading, inactive)
- Execution messages replace countdown timers during active phases
- State transitions trigger CSS animations in existing component

### Step 2.3: Multi-Source Truth Resolution
**Goal**: Create single authoritative state source from database + scheduler + WebSocket

**Priority System**:
- WebSocket status (highest priority - real-time execution)
- APScheduler status (medium priority - scheduled state)
- Database state (lowest priority - persistent state)
- Handle conflicts and race conditions gracefully

---

## Phase 3: Missing Components

### Step 3.1: PerformancePanel Component
**Goal**: Left column metrics display with independent error handling

**Requirements**:
- Paper trading account summary
- Profit/loss charts using existing Recharts
- Trade statistics and performance metrics
- Independent data fetching with fallback states
- No dependency on bot selection for basic metrics

### Step 3.2: ActivityPanel Component  
**Goal**: Right column live activity display

**Requirements**:
- Real-time positions table
- Decision history with modal integration
- Live updates via WebSocket or polling
- Connection to existing decision modal functionality
- Graceful handling of no-data states

### Step 3.3: Enhanced Error Boundaries
**Goal**: Prevent component failures from crashing entire dashboard

**Requirements**:
- Individual error boundaries for each major section
- Specific error messages per component type
- Retry mechanisms for recoverable failures
- Fallback UI that maintains basic functionality

---

## Phase 4: Data Layer Integration

### Step 4.1: API Client Enhancement
**Goal**: Replace Promise.all anti-pattern with resilient data fetching

**Requirements**:
- Individual error handling per API endpoint
- Retry logic with exponential backoff
- Partial data display when some endpoints fail
- Loading states per data section rather than global loading

### Step 4.2: State Management Optimization
**Goal**: Optimize Zustand store for real-time updates

**Requirements**:
- Minimize re-renders through proper state structure
- Implement optimistic updates for user actions
- Cache frequently accessed data with TTL
- Handle WebSocket disconnections gracefully

### Step 4.3: Performance Optimization
**Goal**: Ensure dashboard performs well with multiple bots and real-time updates

**Requirements**:
- Memoize expensive calculations in custom hooks
- Implement virtual scrolling for large bot lists
- Optimize WebSocket message handling frequency
- Monitor and prevent memory leaks in countdown timers

---

## Phase 5: Testing & Validation

### Step 5.1: Integration Testing
**Goal**: Verify end-to-end functionality across all systems

**Test Scenarios**:
- Page load with multiple bots in different states
- Bot start/stop triggering scheduler changes
- Real-time execution with state transitions
- WebSocket disconnection and reconnection
- API failures and recovery mechanisms

### Step 5.2: User Experience Validation
**Goal**: Ensure dashboard meets user expectations for real-time trading interface

**Validation Criteria**:
- Countdown timers accurate to within 1 second
- State transitions smooth and immediate
- No data loss during component errors
- Responsive design works on all screen sizes
- Performance acceptable with 10+ active bots

### Step 5.3: Performance Testing
**Goal**: Validate system performance under realistic load

**Performance Targets**:
- Page load complete in <2 seconds
- WebSocket state updates reflected in <500ms
- Countdown timer updates without visible lag
- Memory usage stable during extended sessions

---

## Phase 6: Migration Strategy

### Step 6.1: Parallel Development
**Goal**: Build dashboard-v2 alongside existing dashboard for safe testing

**Approach**:
- Develop at `/dashboard-v2` route for testing
- Use feature flags to control access during development
- Allow easy switching between old and new versions
- Maintain data compatibility between versions

### Step 6.2: User Testing & Feedback
**Goal**: Validate new dashboard with real usage before full migration

**Testing Process**:
- Beta testing with subset of users
- Collect feedback on real-time features
- Performance monitoring in production environment
- Iterative improvements based on user feedback

### Step 6.3: Full Migration
**Goal**: Replace old dashboard completely

**Migration Steps**:
- Update all navigation links to new dashboard
- Redirect old `/dashboard` route to new version
- Archive old dashboard code as `dashboard-legacy`
- Clean up unused dependencies and components
- Update documentation and user guides

---

## Success Metrics

### Technical Objectives
- [ ] Countdown timers working with real APScheduler data
- [ ] WebSocket state transitions using full CSS animation system
- [ ] Individual component error handling prevents dashboard crashes
- [ ] API resilience with graceful degradation
- [ ] Real-time updates with <500ms latency

### User Experience Objectives
- [ ] Clear visual indication of bot activity status
- [ ] Accurate countdown timers showing next execution
- [ ] Smooth animations during state transitions
- [ ] Reliable real-time updates during bot execution
- [ ] Intuitive navigation and bot management

### Performance Objectives
- [ ] Page load time <2 seconds with multiple bots
- [ ] Memory usage stable during extended sessions
- [ ] Desktop layout optimized for trading workflows
- [ ] WebSocket connection reliability >99%
- [ ] State synchronization accuracy 100%

---

## Implementation Priority

**Week 1**: Phase 1 - Foundation architecture with existing component integration
**Week 2**: Phase 2 - Real-time infrastructure and countdown timers  
**Week 3**: Phase 3 & 4 - Missing components and data layer optimization
**Week 4**: Phase 5 & 6 - Testing, validation, and migration
**Week 5**: Phase 7 - Mobile responsive design and drawer system

**Critical Path**: APScheduler integration → Countdown timers → WebSocket state coordination → Component orchestration → Mobile responsive design

---

## Phase 7: Mobile Responsive Design

### Step 7.1: Mobile Layout Architecture
**Goal**: Transform three-column desktop layout into mobile-optimized experience with slide-in drawers
**Timeline**: After all core functionality is working and tested

**Desktop Layout (Reference)**:
```
┌─────────────┬─────────────┬─────────────┐
│Performance  │ GGBot       │  Activity   │
│Panel        │ Carousel    │   Panel     │ 
│             │ [←] ○ [→]   │             │
└─────────────┴─────────────┴─────────────┘
```

**Mobile Layout Structure**:
- Single column with GGBot carousel as hero element
- Performance and Activity panels collapse into 70%-width slide-in drawers
- Bottom-positioned tabs for thumb-friendly access
- Drawer overlays with darkened background

### Step 7.2: Bottom Tab System
**Goal**: Create accessible drawer triggers styled like existing UI components

**Tab Requirements**:
- Bottom-positioned square tabs matching FloatingActionButtons styling
- Similar styling to GGBotConfig accordion modules
- Two tabs: "Performance" and "Activity"
- Stationary positioning (don't hide when drawer opens)
- Click to slide drawer, click again or tap outside to close

**Tab Positioning**:
```
┌─────────────────────────┐
│   [←]  ○ ggbot-1  [→]   │ ← GGBot carousel (always visible)
│       "Next: 3m47s"     │
│                         │
│    FloatingActionBtns   │
│                         │
├─────────────────────────┤
│ [Performance] [Activity]│ ← Bottom tabs (thumb-accessible)
└─────────────────────────┘
```

### Step 7.3: Slide-In Drawer Implementation
**Goal**: Create smooth drawer animations matching existing GGBotConfig slide behavior

**Drawer Specifications**:
- **Width**: 70% of screen (iterate from this starting point)
- **Animation**: Same slide-in effect as GGBotConfig component
- **Performance Drawer**: Slides in from left
- **Activity Drawer**: Slides in from right
- **Background**: Darkened overlay on remaining 30% of screen
- **Close Methods**: Tap outside drawer OR collapse arrow button inside drawer

**Performance Drawer (70% from left)**:
```
┌──────────────┬──────┐
│Performance   │GGBot │ ← 30% carousel still visible
│Panel         │ [←○→]│
│              │      │
│- Account     │      │
│- Charts      │      │
│- Metrics     │      │
│              │      │
│ [←] Collapse │      │ ← Arrow pointing left to close
├──────────────┼──────┤
│ [Perf] [Act] │      │ ← Bottom tabs remain accessible
└──────────────┴──────┘
```

**Activity Drawer (70% from right)**:
```
┌──────┬──────────────┐
│GGBot │   Activity   │ ← 30% carousel still visible
│ [←○→]│    Panel     │
│      │              │
│      │- Positions   │
│      │- Decisions   │
│      │- Live Data   │
│      │              │
│      │ Collapse [→] │ ← Arrow pointing right to close
├──────┼──────────────┤
│      │ [Perf] [Act] │ ← Bottom tabs remain accessible
└──────┴──────────────┘
```

### Step 7.4: Mobile-Specific Component Adaptations
**Goal**: Ensure existing components work optimally in mobile drawer format

**Component Adaptations**:
- **PerformancePanel**: Optimize for narrow width, stack charts vertically
- **ActivityPanel**: Compact table layouts, touch-friendly row heights  
- **GGBot Carousel**: Ensure touch swipe gestures work properly
- **FloatingActionButtons**: Maintain accessibility with drawers open

**Touch Interactions**:
- Swipe gestures for GGBot carousel navigation
- Touch-optimized drawer close areas
- Prevent accidental drawer triggers during carousel navigation
- Maintain FloatingActionButton accessibility

### Step 7.5: Responsive Breakpoints
**Goal**: Define clean breakpoints for layout transitions

**Breakpoint Strategy**:
- **Desktop (1024px+)**: Full three-column layout
- **Mobile (<1024px)**: Single column with drawer system
- **No tablet-specific layout initially** (can be added later)

**CSS Implementation**:
- Use CSS Grid for desktop three-column layout
- Transform to single column with positioned drawers on mobile
- Maintain existing component styling within drawers
- Leverage existing slide animations from GGBotConfig

---

This plan leverages existing mature components while building the missing real-time infrastructure to create a professional trading dashboard experience. Mobile responsive design is implemented as the final phase after all core functionality is proven and stable.