# ggbot Forge Architecture

## CONTEXT

The Forge represents a complete architectural rethink of the ggbot dashboard, built from first principles with elegance and simplicity as core values. Rather than inheriting the complex patterns from the legacy dashboard (600+ line botStore, global state management, data transformation layers), the Forge adopts a clean, local-first approach.

### Design Philosophy
- **Data Foundation First**: Establish rock-solid API integration and real-time flows before any UI concerns
- **Local State Elegance**: Direct API types, no transformations, single source of truth per page
- **Progressive Layering**: Build in phases - foundation, then design system, then components
- **Component Separation**: Break monolithic config editing into focused, reusable components
- **Multi-Bot Native**: Designed for `selectedConfigId` switching from day one

### Why Forge vs Dashboard Evolution
The dashboard had accumulated architectural debt that made elegant evolution impossible. The Forge starts fresh with lessons learned, avoiding the complexity traps while maintaining all functional requirements. This clean slate approach enables the modern UX improvements (dark/light mode, responsive design) that would be difficult to retrofit.

### Key Architectural Decisions Made
- **No data transformation** - Use `BotConfiguration` API types directly, eliminated mapping layer
- **Local state only** - Rejected global Zustand store patterns, everything lives in page component  
- **SSE over WebSocket** - Migrated from complex WebSocket to simple Server-Sent Events
- **API client reuse** - Leverage existing `apiClient` with proper authentication vs custom fetch
- **Multi-bot from day one** - `selectedConfigId` pattern prevents single-bot limitations
- **Centralized config updates** - Single update function handles all config changes for separated components

### Critical Implementation Notes
- Fixed `BotConfiguration` interface missing `state` field that API actually returns
- SSE filtering by `config_id` prevents data leakage between bots
- Start/stop API responses include `next_run` for immediate countdown display
- Bot switching clears operational state (positions, decisions) but preserves config data
- All real-time updates (execution phases, positions, account balances) come via SSE stream

## CURRENT

### Overview
The Forge is a single-page application that replaces the dashboard with an elegant, local state architecture. It manages multiple bot configurations with seamless switching between them via `selectedConfigId`.

### Data Architecture
- **Local state only** - No global store, all state lives in the Forge page component
- **Direct API types** - Uses `BotConfiguration` from API client without transformation
- **Multi-bot native** - Loads all user configurations, tracks selected one via `selectedConfigId`
- **Centralized state pattern** - All bots stored in `allBots[]`, selected bot computed dynamically

### Authentication Flow
1. Check Supabase auth on page load
2. Extract user ID from session
3. Redirect to login if not authenticated

### Configuration Data Flow
1. User lands on forge
2. Call `apiClient.listConfigs()` to get all user configurations
3. If configurations exist: Load all into `allBots[]`, select first via `selectedConfigId`
4. If no configurations exist: Auto-create default RSI bot, set as selected
5. Bot switching updates `selectedConfigId`, all page content keys off selected bot

### Real-Time Updates
1. Establish SSE connection to dashboard stream
2. Reconnect when `selectedBot` changes to ensure clean state
3. Filter incoming data for currently selected bot's `config_id`
4. Update local state for:
   - Execution status (extraction → decision → trading phases)
   - Live positions with P&L updates
   - Recent AI decisions with confidence scores
   - Paper trading account balances and metrics
   - Next run timing for countdown

### Bot Control Actions
1. Start bot: API call to `/api/v2/bot/{selectedConfigId}/start`
2. Stop bot: API call to `/api/v2/bot/{selectedConfigId}/stop`
3. Update selected bot state in `allBots[]` array optimistically
4. Extract `next_run` from API response for immediate countdown display
5. Real-time updates confirm state changes via SSE

### Bot Switching UI
- Bot selector appears when multiple bots exist
- Shows bot names with active status indicators (green dot)
- Clicking switches `selectedConfigId` and updates all page content
- SSE reconnects to filter data for newly selected bot

### Current Status
- ✅ Multi-bot architecture implemented
- ✅ API integration working (listConfigs, createConfig, start/stop)
- ✅ SSE filtering by selected bot
- ✅ Bot switching UI functional
- ⏳ Phase 1 data foundation complete, ready for Phase 2

## PLANS

### Elegant Config State Architecture

#### Centralized State Management
- Forge page maintains single source of truth for all `BotConfiguration` objects
- `selectedConfigId` state determines which bot is currently active
- Generic update function handles all configuration changes for selected bot
- Dirty state tracking to detect unsaved changes
- Single save operation overwrites entire configuration for selected bot

#### Multi-Bot Switching Support
- Load all user configurations, display selected one
- `selectedConfigId` drives all page content (config editing, operational data, controls)
- SSE stream filters data by currently selected `config_id`
- Switching bots clears operational state (positions, decisions, execution status)
- Config editing always targets currently selected bot
- Bot selector component for navigation between multiple bots

#### Component Separation Strategy
- **Market Data Component**: Manages data sources and technical indicators
- **Decision Component**: Handles strategy prompts and analysis frequency  
- **Risk Management Component**: Controls position sizing and risk parameters
- **LLM Configuration Component**: Manages AI provider and model settings
- **Bot State Component**: Handles active/inactive state and naming

#### Update Flow Pattern
- Each component receives focused update function for its domain
- Components update specific sections of configuration via callbacks
- All changes flow through central update function
- Immediate local state updates with dirty tracking
- Batch save overwrites database configuration

#### Multi-Field Support
- Handle JSONB `config_data` field updates (nested object changes)
- Handle top-level configuration fields (`state`, `config_name`, etc.)
- Unified update pattern for both types of changes

#### Save Strategy
- Single save button triggers complete configuration overwrite
- API call to `apiClient.updateConfig()` with entire modified configuration
- Reset dirty state on successful save
- Handle save conflicts and validation errors gracefully

#### Benefits
- Component isolation with shared state
- Simple coordination without state duplication
- Handles complex nested configuration updates
- Maintains real-time operational data separately from configuration edits
- Clean separation between configuration (user settings) and operational data (SSE updates)

### Implementation Phases

#### Phase 1: Data Foundation ✅ COMPLETE
- Verify all API endpoints work correctly
- Test SSE streams and real-time filtering
- Implement multi-bot switching with `selectedConfigId`
- Ensure local state patterns are robust
- Complete centralized state management architecture

#### Phase 2: Layout & Design System (IN PROGRESS)

**Phase 2A: Component Architecture**

```
/frontend/app/forge/components/
├── layout/
│   ├── Header.tsx           # App branding, theme toggle, user profile
│   ├── BotRail.tsx          # Left sidebar with bot list
│   ├── MobileNav.tsx        # Bottom nav for mobile
│   ├── TabNavigation.tsx    # Monitor/Configure tab switcher
│   └── UserProfile.tsx      # Profile dropdown (logout, settings, subscription)
│
├── monitor/
│   ├── ActivationBar.tsx    # Bot controls, pipeline ticker, countdown
│   ├── PipelineTicker.tsx   # Extraction→Decision→Trading visualization
│   ├── MetricsBar.tsx       # KPI cards (balance, P&L, win rate)
│   ├── PositionsTable.tsx   # Active trades with real-time P&L
│   ├── DecisionFeed.tsx     # List of AI decisions
│   └── DecisionCard.tsx     # Individual decision with expandable reasoning
│
├── configure/
│   ├── SaveConfig.tsx       # Save/Cancel bar with unsaved changes indicator
│   ├── ConfigTabs.tsx       # Sub-tabs for configuration sections
│   ├── DecisionEditor.tsx   # Strategy editing with locked sections
│   ├── MarketDataSelector.tsx # Data source/indicator selection
│   ├── RiskControls.tsx     # Position sizing, stop loss settings
│   ├── LLMConfig.tsx        # Provider selection, API keys
│   └── TradingSetup.tsx     # Exchange config (disabled for MVP)
│
└── shared/
    ├── ThemeToggle.tsx      # Sun/moon theme switcher
    ├── Toast.tsx            # Notification toasts
    ├── EmptyState.tsx       # Empty state guidance
    ├── LoadingSkeleton.tsx  # Loading placeholders
    └── Countdown.tsx        # Next run countdown timer
```

**Phase 2B: Layout Shell Implementation**
- [x] Create mobile-first responsive layout shell (header, main, sidebar)
- [x] Implement dark/light mode theming system with CSS variables and charcoal/bone palette
- [x] Add sun/moon theme toggle in header with localStorage persistence
- [x] Add user profile dropdown in header (logout, settings, subscription)
- [x] Build responsive bot rail component (hidden mobile, visible desktop)
- [x] Create mobile bottom navigation for bot switching
- [x] Establish consistent spacing scale and typography system

**Phase 2C: Core Monitor Components**
- [ ] Build ActivationBar component (sticky, shows bot status and controls)
- [ ] Create Monitor/Configure tab system replacing current layout
- [ ] Implement PipelineTicker for extraction→decision→trading visualization
- [ ] Add responsive breakpoint utilities and mobile-first styling
- [ ] Create empty state components for all major sections

**Phase 2D: Enhanced Bot Rail**
- [ ] Transform current bot selector into persistent left rail
- [ ] Add basic P&L display per bot (if feasible with paper trading data)
- [ ] Implement hover states and quick actions (activate/deactivate)
- [ ] Add bot creation and management actions
- [ ] Handle mobile drawer behavior for bot switching

#### Phase 3: Monitor Experience Enhancement

**Phase 3A: Real-Time Dashboard**
- [ ] Enhance DecisionFeed with expandable reasoning cards
- [ ] Improve PositionsTable with real-time P&L updates
- [ ] Add basic performance metrics (balance, unrealized P&L)
- [ ] Implement countdown timer with next run display
- [ ] Create health/status indicators for SSE and system state

**Phase 3B: Visual Polish**
- [ ] Add micro-interactions for pipeline stage animations
- [ ] Implement toast notifications for bot actions and decisions
- [ ] Create responsive table→card transformations for mobile
- [ ] Add loading states and optimistic UI updates
- [ ] Polish empty states with helpful guidance text

#### Phase 4: Configure Experience

**Phase 4A: Configuration Architecture**
- [ ] Implement centralized config update system with dirty state tracking
- [ ] Create save/publish flow with validation
- [ ] Build configuration tabs (Decision, Market Data, Risk, Trading, LLM)
- [ ] Add draft mode with auto-save functionality
- [ ] Implement configuration validation and error handling

**Phase 4B: Configuration Components**
- [ ] Build DecisionEditor with locked/editable sections
- [ ] Create MarketDataSelector with hierarchical data source structure
- [ ] Implement RiskManagement controls with preview
- [ ] Add LLMConfiguration with provider selection and testing
- [ ] Build advanced JSON editor for power users

#### Phase 5: Progressive Enhancement

**Phase 5A: Advanced Features**
- [ ] Add test-run functionality for strategy validation
- [ ] Implement configuration versioning and diff viewer
- [ ] Create strategy templates and presets
- [ ] Add import/export configuration functionality
- [ ] Build bot duplication and cloning features

**Phase 5B: Performance & Polish**
- [ ] Optimize for multiple bots with virtualization if needed
- [ ] Add keyboard shortcuts for power users
- [ ] Implement search and filtering for decisions and trades
- [ ] Add comprehensive accessibility features
- [ ] Create comprehensive error boundaries and fallbacks

### Design System Specifications

#### Responsive Breakpoints
- **Mobile**: `< 768px` - Single column, bottom nav, drawer for bots
- **Tablet**: `768px - 1024px` - Two column, side rail visible
- **Desktop**: `1024px+` - Three column layout with expanded rail

#### Color System (Dark/Light Mode with Charcoal/Bone Palette)
```css
/* Dark Mode (Primary) */
[data-theme="dark"] {
  --bg-primary: #161618;      /* charcoal-900 */
  --bg-secondary: #1f1f23;    /* charcoal-800 */
  --bg-tertiary: #2a2a30;     /* charcoal-700 */
  --text-primary: #e3e5e6;    /* bone-200 */
  --text-secondary: #d6d8da;  /* bone-300 */
  --border: #36363d;          /* charcoal-600 */
}

/* Light Mode */
[data-theme="light"] {
  --bg-primary: #f0f2f3;      /* bone-100 */
  --bg-secondary: white;
  --bg-tertiary: #e3e5e6;     /* bone-200 */
  --text-primary: #1f1f23;    /* charcoal-800 */
  --text-secondary: #2a2a30;  /* charcoal-700 */
  --border: #d6d8da;          /* bone-300 */
}

/* Agent Colors (Same in Both Modes) */
:root {
  --agent-extraction: #38a1c7; /* Blue - data extraction */
  --agent-decision: #2cbe77;   /* Green - AI decision making */
  --agent-trading: #be6a47;    /* Orange - trade execution */
  --status-success: #10b981;   /* Profit, success, active */
  --status-danger: #ef4444;    /* Loss, error, inactive */
  --status-warning: #f97316;   /* Warning, pending */
}

/* Theme Toggle Component */
.theme-toggle {
  @apply flex h-8 w-8 items-center justify-center rounded-full border
         border-charcoal-600 bg-charcoal-800 hover:bg-charcoal-700
         transition-colors;
}
```

#### Component Architecture
- **Local state only** - No global stores, all state in page component
- **Prop drilling patterns** - Clean component contracts with focused responsibilities
- **Compound components** - Related components grouped together (e.g., `<BotRail.Item>`)
- **Mobile-first responsive** - Components adapt to screen size automatically
- **SSE integration** - Real-time updates flow through existing patterns