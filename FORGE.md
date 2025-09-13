# ggbot Forge Architecture

## CURRENT

### Overview
The Forge is a single-page application that replaces the dashboard with an elegant, local state architecture. It manages one bot configuration at a time with real-time operational updates.

### Data Architecture
- **Local state only** - No global store, all state lives in the Forge page component
- **Direct API types** - Uses `BotConfiguration` from API client without transformation
- **Single bot focus** - Handles first configuration, ignores multiple bots

### Authentication Flow
1. Check Supabase auth on page load
2. Extract user ID from session
3. Redirect to login if not authenticated

### Configuration Data Flow
1. User lands on forge
2. Call `apiClient.listConfigs()` to get existing configurations
3. If configurations exist: Use first configuration directly
4. If no configurations exist: Auto-create default RSI bot via `apiClient.createConfig()`
5. Set configuration to local state as `BotConfiguration`

### Real-Time Updates
1. Establish SSE connection to dashboard stream
2. Filter incoming data for current bot's `config_id`
3. Update local state for:
   - Execution status (extraction → decision → trading phases)
   - Live positions with P&L updates
   - Recent AI decisions with confidence scores
   - Next run timing for countdown

### Bot Control Actions
1. Start bot: API call to `/api/v2/bot/{id}/start`
2. Stop bot: API call to `/api/v2/bot/{id}/stop`
3. Update local bot state optimistically
4. Real-time updates confirm state changes via SSE

### Current Limitations
- No configuration editing capability
- Single bot limitation (only shows first config)
- No conflict resolution for simultaneous edits
- SSE connection created per bot change without cleanup management

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