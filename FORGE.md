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

#### Phase 1: Data Foundation
- Verify all API endpoints work correctly
- Test SSE streams and real-time filtering
- Implement multi-bot switching with `selectedConfigId`
- Ensure local state patterns are robust
- Complete centralized state management architecture

#### Phase 2: Layout & Design System
- Implement dark/light mode toggle and theming system
- Design responsive layout structure and component containers
- Create skeleton/empty state components for all major sections
- Establish consistent spacing, typography, and color systems
- Build navigation and bot switching UI shell
- Focus on UX improvements over existing dashboard

#### Phase 3: Component Integration
- Import and adapt elegant existing components (GGBot, FloatingActions)
- Build new separated config components using centralized state
- Wire components to data foundation progressively
- Implement component-specific functionality one section at a time
- Maintain elegance through selective reuse vs rebuild decisions