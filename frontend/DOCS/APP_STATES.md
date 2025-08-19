# GGBot Frontend State Management Overview

## State Architecture

The frontend uses a combination of Zustand for global state management and React local state for component-specific UI states.

## 1. Global State (Zustand Store)

### Location: `/store/botStore.ts`

### Core State Objects

#### **Bots Map** (`Map<config_id, Bot>`)
- **Purpose**: Central repository of all bot configurations and runtime states
- **Key**: `config_id` (UUID from backend)
- **Value**: Bot object containing:
  - `config_id`: Unique identifier from backend
  - `instance_name`: Backend instance name
  - `config_type`: Type of config (ggshot/demo/production)
  - `name`: Display name (user-editable)
  - `strategy`: Trading strategy (meanrev/momentum/trend/ai)
  - `crypto`: Target cryptocurrency (BTC/ETH/SOL)
  - `riskLevel`: Risk tolerance (low/medium/high)
  - `status`: Current bot status object (see BotStatus below)
  - `isActive`: Whether bot is running
  - `createdAt`: Creation timestamp
  - `lastRun`: Last activity timestamp
  - `userId`: Owner user ID

#### **BotStatus Object**
- **Purpose**: Real-time bot operation status
- **Fields**:
  - `phase`: Current operation phase (inactive/idle/extraction/decision/trading)
  - `color`: Status indicator color (gray/blue/green/orange)
  - `message`: Human-readable status message
  - `timestamp`: Last update time
  - `showSpinner`: Whether to show loading animation
  - `context`: Optional contextual data (symbol, timeframe, PnL, etc.)

#### **Connections Map** (`Map<userId, WebSocketConnection>`)
- **Purpose**: Manage WebSocket connections per user
- **Value**: WebSocketConnection object:
  - `ws`: WebSocket instance or null
  - `isConnected`: Connection status
  - `reconnectAttempts`: Count for exponential backoff
  - `lastError`: Last error message

#### **Loading/Error States**
- `isLoading`: Global loading indicator
- `error`: Global error message

### Store Actions

#### Bot Management
- `addBot()`: Add new bot to store
- `updateBot()`: Update bot properties
- `removeBot()`: Remove bot from store
- `getBotById()`: Retrieve specific bot
- `getBotsByUser()`: Get all bots for a user
- `getActiveBots()`: Get only running bots

#### Status Management
- `updateBotStatus()`: Update bot's operational status
- `setBotActive()`: Toggle bot active state

#### WebSocket Management
- `connectWebSocket()`: Establish WebSocket connection
- `disconnectWebSocket()`: Close connection
- `subscribeToBot()`: Subscribe to bot status updates
- `isWebSocketConnected()`: Check connection status

#### API Actions
- `loadBots()`: Fetch bots from backend
- `createBot()`: Create new bot configuration
- `startBot()`: Start bot execution
- `stopBot()`: Stop bot execution
- `deleteBot()`: Delete bot configuration

## 2. Component Local States

### `/app/demo/page.tsx` - Demo Page Component

#### UI Navigation State
- **`currentBotIndex`** (number): Index of currently displayed bot in carousel
  - Purpose: Track which bot is shown in the GGBot circle
  - Range: 0 to demoBots.length (last index shows "Create New" placeholder)

#### Modal/Sheet States
- **`isConfigOpen`** (boolean): Whether GGBotConfig bottom sheet is open
  - Purpose: Control visibility of bot configuration panel
- **`selectedBot`** (Bot | null): Currently selected bot for configuration
  - Purpose: Pass bot data to GGBotConfig component
  - Note: Kept populated during close animation for smooth transition

#### Trading Display States
- **`livePositions`** (Array): Active trading positions
  - Purpose: Display real-time trading data in dashboard
  - Fields: symbol, direction, pnl, positionSize, entryPrice, currentPrice, timeInTrade, leverage, confidence, reasoning_text
- **`expandedReasoningIds`** (Set<string>): IDs of expanded trade reasoning cards
  - Purpose: Track which trade cards show full AI reasoning
- **`demoStarted`** (boolean): Whether demo bot has been started
  - Purpose: Track demo bot state separately from regular bots

### `/components/GGBotConfig.tsx` - Configuration Panel

#### Form States
- **`isEditingName`** (boolean): Whether name input is active
- **`botName`** (string): Current bot name in form
- **`hasChanges`** (boolean): Whether form has unsaved changes

#### UI States
- **`expandedSections`** (Set<string>): Which accordion sections are expanded
  - Default: ['extraction'] - Extraction agent expanded by default
- **`isVisible`** (boolean): Controls slide animation visibility
- **`isMounted`** (boolean): Controls component mounting for animation

### `/components/FloatingActionButtons.tsx`
No local state - purely presentational component that receives props

### `/components/GGBot.tsx`
No local state - displays bot data from props

## 3. WebSocket Integration

### Hook: `/hooks/useBotWebSocket.ts`

#### Purpose
Manages WebSocket lifecycle and bot data synchronization

#### Flow
1. Load bots from API on mount
2. Establish WebSocket connection
3. Subscribe to bot status updates
4. Handle reconnection with exponential backoff
5. Forward demo messages to callback

#### Message Types Handled
- `bot_status_update`: Updates bot operational status
- `demo_position_create`: Creates demo trading position
- `demo_started`: Indicates demo bot activation

## 4. Data Flow Patterns

### Bot Status Updates
1. Backend sends WebSocket message
2. `useBotWebSocket` hook receives message
3. Store's `updateBotStatus()` called
4. Components re-render via Zustand subscriptions

### User Actions
1. User clicks action button (start/stop/delete)
2. Component calls store action
3. Store makes API call
4. On success, store updates local state
5. WebSocket confirms with status update

### Configuration Changes
1. User edits in GGBotConfig
2. Local state tracks changes (`hasChanges`)
3. Save button triggers API call
4. Store updates on success
5. Component resets local state

## 5. State Synchronization

### Backend → Frontend
- Initial load via REST API (`/agent/api/bots`)
- Real-time updates via WebSocket
- Status transitions reflected in UI immediately

### Frontend → Backend
- All mutations go through API calls
- Optimistic updates applied locally
- Rollback on API failure

### Component → Store
- Components subscribe to store slices
- Zustand handles re-renders efficiently
- Selectors prevent unnecessary updates

## 6. Future State Considerations

### Planned Additions
- **Agent Configuration States**: Detailed configuration for Extraction, Decision, Trading agents
- **Performance Metrics**: Historical performance data per bot
- **Alert/Notification State**: User notifications and alerts
- **User Preferences**: UI preferences, display settings
- **Session State**: Authentication, user session data

### Optimization Opportunities
- Implement state persistence (localStorage/sessionStorage)
- Add undo/redo functionality for configuration changes
- Cache bot configurations for offline editing
- Implement optimistic updates for better UX
- Add state migration system for updates

## 7. Best Practices

### Current Implementation
- ✅ Single source of truth (Zustand store)
- ✅ Clear separation of concerns
- ✅ Type-safe state management
- ✅ Efficient re-render optimization
- ✅ Proper cleanup on unmount

### Recommendations
- Keep component state minimal and UI-focused
- Use store for shared/persistent data
- Implement proper error boundaries
- Add state debugging tools in development
- Document state shape changes