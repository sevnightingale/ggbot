# GGBot Frontend

A Next.js 14 frontend application for managing autonomous AI trading agents. Built with TypeScript, Tailwind CSS, and designed with a brutalist aesthetic for serious traders.

## 🌟 Overview

The GGBot frontend provides a professional, brutalist-designed dashboard for configuring, monitoring, and controlling autonomous trading agents. The interface embodies a cyber-samurai aesthetic with sharp edges, minimal color usage, and a command center feel.

### Key Features

- **Brutalist Agent Cards**: Sharp-edged rectangular cards with minimal color accents and subtle glows
- **GGBot Emblem System**: Substantial circular emblem with paper texture representing each bot
- **Carousel Navigation**: Smart multi-bot management with dynamic +/arrow navigation
- **Real-time Monitoring**: Live trade display and performance metrics with API failover
- **Bot Control Panel**: Clean start/stop and test run controls with status-aware styling
- **Inline Name Editing**: Click-to-edit bot names with immediate feedback

## 🏗️ Architecture

### Tech Stack

- **Framework**: Next.js 14 with App Router and TypeScript
- **Styling**: Tailwind CSS with custom brutalist theme
- **State Management**: Zustand for lightweight global state
- **Charts**: Recharts for performance visualization
- **Icons**: Lucide React for consistent iconography
- **Dates**: date-fns for date formatting

### Project Structure

```
frontend/
├── app/                          # Next.js App Router pages
│   ├── layout.tsx               # Global layout with navigation
│   ├── page.tsx                 # Home page (bot overview)
│   ├── globals.css              # Global styles and animations
│   └── bot/[id]/page.tsx        # Bot detail page
├── components/
│   ├── ui/                      # Base UI components
│   │   ├── PageWrapper.tsx      # Layout wrapper with navigation
│   │   └── TopNav.tsx           # Minimal hamburger navigation
│   ├── bot/                     # Bot-specific components
│   │   ├── AgentCard.tsx        # Brutalist rectangular agent cards
│   │   ├── AgentCircle.tsx      # Legacy circular design (unused)
│   │   ├── GGBotCircle.tsx      # Emblem carousel with controls
│   │   ├── AgentConfigModal.tsx # Configuration modal container
│   │   └── config/              # Agent configuration forms
│   │       ├── ExtractionConfigForm.tsx  # Symbols, timeframes, indicators
│   │       ├── DecisionConfigForm.tsx    # Strategy, LLM, risk guidelines
│   │       └── TradingConfigForm.tsx     # Exchange, risk, execution
│   ├── trades/                  # Trade monitoring components
│   │   └── TradeTable.tsx       # Live trade display
│   └── charts/                  # Performance visualization
│       └── PerformanceChart.tsx # P&L charts and metrics
├── lib/
│   ├── api/client.ts           # Typed API client
│   └── utils/cn.ts             # Tailwind class merging utility
├── store/bot.ts                # Zustand global state store
├── types/index.ts              # TypeScript type definitions
└── styles/                     # Additional styling (unused)
```

## 🎨 Design System

### Brutalist Cyber-Samurai Aesthetic

The interface embodies a command-center aesthetic with tactical precision:

- **Sharp edges**: Zero rounded corners throughout the interface
- **Minimal color usage**: Bone/gray dominant palette with selective accent usage
- **Paper texture**: Subtle background texture for tactical depth
- **High contrast**: Bold typography for readability in professional environments

### Color Palette

Strict 5-color brutalist palette:

- **Charcoal Black**: (#161618) - main background void, no texture
- **Bone White**: (#e3e5e6) - text, neutral elements, emblem
- **Agent Colors** (pure, no mixing):
  - **Extraction Blue**: (#38a1c7) - animated glow, borders, accents
  - **Decision Green**: (#2cbe77) - animated glow, borders, accents  
  - **Trading Orange**: (#be6a47) - animated glow, borders, accents
- **Paper Texture**: Applied only to containers (cards, modals, header)
- **Enhanced Contrast**: 80%+ opacity for containers, 60%+ for UI elements

### Typography

- **Headlines**: Kanit Bold for impact and command presence
- **Body**: Inter for clean readability
- **UI Elements**: Sharp, structured text hierarchy

### Visual Language

- **Rectangular geometry**: All cards and panels use sharp corners
- **Substantial elements**: GGBot emblem is large and dignified (128px)
- **Structured layout**: Grid-based system with generous spacing
- **Status rewards**: Color only appears when agents are configured

## 🔧 Configuration System

### Three-Agent Architecture

Each agent has a dedicated configuration interface:

#### 1. Extraction Agent (Blue)
- **Symbols**: Multi-select cryptocurrency pairs (BTC/USDT, ETH/USDT, etc.)
- **Timeframes**: Checkbox selection (15m, 1h, 4h, 1d)
- **Data Sources**: Toggle-based source configuration
  - **Indicators MCP**: 78+ technical indicators with LLM interpretation
  - **Future sources**: TradingView, news feeds, sentiment analysis

#### 2. Decision Agent (Green)
- **Strategy**: Natural language trading strategy description
- **LLM Settings**: Provider selection (DeepSeek, OpenAI, Anthropic)
- **Risk Guidelines**: Hard limits and safety rules
- **Context**: Additional trading style preferences

#### 3. Trading Agent (Orange)
- **Exchange**: Platform selection with API connection status
- **Risk Management**: 
  - Position sizing (% of capital)
  - Leverage limits (1x-100x)
  - Risk per trade limits
  - Emergency position caps
- **Execution Rules**: Order types, slippage tolerance, timing

### Configuration Flow

1. **Click agent card** → Opens tabbed configuration modal
2. **Navigate tabs** → Configure different aspects with real-time validation
3. **Save configuration** → Updates backend via API with error handling
4. **Status indicator** → Card shows subtle glow when configured
5. **Bot readiness** → All agents must be configured before starting

## 📊 Monitoring Dashboard

### Trade Display
- **Live table** with symbol, side, entry price, current P&L
- **30-second polling** for real-time updates
- **Click trades** for detailed reasoning (future feature)

### Performance Metrics
- **P&L chart** with configurable time periods (1d, 7d, 30d)
- **Key metrics**: Total P&L, win rate, total trades, return percentage
- **Visual indicators** for winning/losing positions

### GGBot Emblem & Control
- **Emblem carousel**: Substantial circular emblem with paper texture
- **Smart navigation**: Dynamic +/arrow buttons for multi-bot management
- **Inline name editing**: Click-to-edit bot names with immediate save/cancel
- **Status indication**: Running bots show green pulsing ring around emblem
- **Control panel**: Separate rectangular panel with Start/Stop and Test Run buttons
- **Safety validation**: Prevents starting with incomplete agent configuration

## 🔌 API Integration

### Backend Communication

The frontend connects to the GGBot backend API for:

- **Configuration Management**: `GET/PUT /agent/api/config/{user_id}/{module}`
- **Scheduler Control**: `POST /agent/api/scheduler/{start|stop|status}`
- **Trade Data**: `GET /dashboard/api/dashboard/{user_id}/trades`
- **Performance**: `GET /dashboard/api/dashboard/{user_id}/performance`
- **Test Execution**: `POST /extraction/webhooks/trigger-extraction`

### Environment Configuration

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_USER_ID=00000000-0000-0000-0000-000000000001
NEXT_PUBLIC_ENABLE_ANIMATIONS=true
NEXT_PUBLIC_POLLING_INTERVAL=30000
```

### State Management

Zustand store with robust error handling:
- **Configuration state** for all three agents with validation
- **Live trade data** with 30-second polling and API fallback to mock data
- **Performance metrics** with period selection and caching
- **Bot management** including name editing and carousel state
- **UI state** for modals, loading states, and error boundaries
- **API resilience** with timeout handling and graceful degradation

## 🚀 Development

### Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Development URLs

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000 (configure in .env.local)

### Key Commands

```bash
# Start with specific port
npm run dev -- --port 3001

# Type checking
npm run type-check

# Linting (if configured)
npm run lint
```

## 📋 Current Implementation Status

### ✅ Completed Features

#### Core Infrastructure
- [x] Next.js 14 project setup with TypeScript
- [x] Tailwind CSS configuration with custom theme
- [x] Zustand store for state management
- [x] Typed API client with error handling
- [x] Responsive layout with navigation

#### Agent System
- [x] Brutalist rectangular agent cards with sharp edges (no rounded corners)
- [x] Agent-specific glow effects with pure colors (blue/green/orange) for configured agents
- [x] Animated pulsing glow with distinct colors per agent type
- [x] Tabbed configuration modals with sharp edges throughout
- [x] Complete configuration forms:
  - [x] Extraction: Symbols, timeframes, indicators (78 available)
  - [x] Decision: Strategy templates, LLM settings, risk guidelines
  - [x] Trading: Exchange setup, risk sliders, execution rules

#### Multi-Bot Management System
- [x] Full multi-bot architecture with carousel navigation
- [x] Bot creation via + button with auto-generated names (BOT-01, BOT-02, etc.)
- [x] Bot switching with arrow navigation and state isolation
- [x] Inline bot name editing with save/cancel functionality
- [x] Bot-scoped configurations, trades, and performance data
- [x] Independent agent states per bot

#### GGBot Emblem System (Floating Design)
- [x] Large circular emblem (128px) with paper texture and shadow
- [x] Floating emblem design in negative space (no container borders)
- [x] Centered carousel navigation with properly aligned arrows
- [x] Circular icon controls (START/STOP and TEST RUN) with floating labels
- [x] Status indicator ring for running bots
- [x] Command center aesthetic with tactical spacing

#### Dashboard
- [x] Live trade table with scrollable container (max-height with overflow)
- [x] Performance chart with Recharts and period selection
- [x] Real-time status monitoring with API resilience
- [x] Brutalist styling throughout with sharp edges and minimal colors
- [x] Enhanced contrast borders (80%+ opacity for containers, 60%+ for elements)

#### User Experience & Design System
- [x] Pure 5-color brutalist palette (charcoal, bone, blue, green, orange)
- [x] Paper texture on containers only (main background remains void)
- [x] Sharp edges throughout (zero rounded corners)
- [x] Enhanced border visibility and contrast
- [x] Comprehensive error handling with API timeouts
- [x] Loading states and graceful API degradation
- [x] Form validation with real-time feedback
- [x] Empty states for no data scenarios
- [x] Respects user preferences for reduced motion

### 🔄 Partially Implemented

#### API Integration
- [x] All endpoints defined and typed
- [x] State management connected to API calls
- [x] Configuration save/load functionality
- [ ] **Real backend testing** (ready but untested)

#### Advanced Features (COMPLETED)
- [x] Bot name editing with inline save/cancel
- [x] Smart carousel navigation for multiple bots
- [x] **Multi-bot creation flow** (+ button functionality)
- [x] **Bot switching with state isolation** and data reloading
- [x] **Advanced multi-bot management** (create, switch, rename, delete)

## 📋 TODO: Completing the Prototype

### 🔥 High Priority (Required for MVP)

#### 1. Backend Integration Testing
- [ ] **Test configuration API** endpoints with real backend
- [ ] **Verify trade data** loading and display
- [ ] **Test scheduler** start/stop functionality
- [ ] **Validate error handling** for API failures
- [ ] **Test polling mechanism** with live data

#### 2. Critical Bug Fixes
- [ ] **Environment variable** validation and fallbacks
- [ ] **TypeScript strict mode** compliance
- [ ] **Form validation** edge cases
- [ ] **API error** recovery and retry logic

#### 3. Essential Features
- [ ] **Trade detail modal** for viewing decision reasoning
- [ ] **Configuration validation** before allowing bot start
- [ ] **Real-time polling** optimization (prevent API spam)
- [ ] **Connection status** indicators for API health

### 🎯 Medium Priority (Enhanced UX)

#### 4. User Experience Improvements
- [ ] **Loading skeletons** for all data loading states
- [ ] **Toast notifications** for actions (save, start/stop, errors)
- [ ] **Keyboard shortcuts** for power users (ESC to close modals)
- [ ] **Breadcrumb navigation** improvements
- [ ] **Mobile responsive** testing and fixes

#### 5. Data Display Enhancements
- [ ] **Trade history** pagination
- [ ] **Performance period** selector improvements
- [ ] **Chart tooltips** with detailed information
- [ ] **Export functionality** for trade data

#### 6. Configuration UX
- [ ] **Configuration templates** save/load
- [ ] **Form auto-save** drafts
- [ ] **Configuration validation** with helpful error messages
- [ ] **Quick setup wizard** for first-time users

### 🔮 Low Priority (Future Enhancements)

#### 7. Advanced Features
- [ ] **Multi-bot management** (currently single bot)
- [ ] **Bot overview page** with bot cards
- [ ] **Advanced charting** with technical indicators
- [ ] **WebSocket real-time** updates (replace polling)

#### 8. Developer Experience
- [ ] **Component documentation** with Storybook
- [ ] **Unit tests** for critical components
- [ ] **E2E tests** for main user flows
- [ ] **Performance monitoring** and optimization

#### 9. Production Readiness
- [ ] **Authentication system** (currently hardcoded user)
- [ ] **Multi-user support** with proper isolation
- [ ] **Security headers** and CSP configuration
- [ ] **Analytics integration** for usage tracking

## 🎯 Immediate Next Steps

### For Testing the Prototype:

1. **Start both servers**:
   ```bash
   # Backend (from ggbot root)
   cd /home/sev/ggbot
   source .venv/bin/activate
   python main_api.py
   
   # Frontend (from frontend directory)
   cd frontend
   npm run dev -- --port 3001
   ```

2. **Navigate to bot dashboard**: http://localhost:3001/bot/default

3. **Test configuration flow**:
   - Click each agent circle
   - Configure settings in each tab
   - Save configurations
   - Try to start the bot

4. **Monitor for issues**:
   - API connectivity
   - Configuration persistence
   - Error handling
   - UI responsiveness

### Critical Issues to Resolve:

1. **API Connection**: Verify backend is accessible at configured URL
2. **CORS Configuration**: Ensure backend accepts frontend requests
3. **Data Validation**: Test with real backend data structures
4. **Error Boundaries**: Handle API failures gracefully

## 📝 Notes

- **Single-user prototype**: Currently hardcoded to default user ID
- **Testnet ready**: Designed for safe testing environment
- **Extensible**: Architecture supports adding new agents and features
- **Performance focused**: Minimal dependencies, efficient rendering
- **Trader-centric**: Built for desktop use with professional trading workflow

This frontend provides a comprehensive foundation for the GGBot autonomous trading system with full multi-bot management capabilities, brutalist design system, and floating command center aesthetic. Ready for backend integration with config_id routing for production deployment.

## 🎯 Recent Major Updates (Current Session)

### Multi-Bot Architecture Implemented
- Complete bot management system with carousel navigation
- Bot creation, switching, renaming, and deletion functionality  
- Independent state isolation per bot (configs, trades, performance)
- Auto-generated bot naming (BOT-01, BOT-02, etc.)

### Enhanced Brutalist Design System
- Removed all rounded corners throughout the interface
- Implemented strict 5-color palette with pure agent colors
- Enhanced border contrast (80%+ opacity for containers)
- Paper texture applied strategically to containers only

### Floating Command Center Redesign
- Transformed GGBot emblem to floating design in negative space
- Converted rectangular buttons to circular icon controls with floating labels
- Improved carousel arrow centering with emblem midline
- Created architectural command bridge aesthetic

### Agent Glow System Overhaul
- Implemented agent-specific animated glow effects
- Pure color animations (blue/green/orange) without white washing
- Distinct pulsing animations for each agent type
- Enhanced visibility and contrast

The interface now embodies a true cyber-samurai command center with tactical precision and multi-bot management capabilities.



  Border Inventory

  1. Header/Navigation

  - TopNav.tsx:11 - border-b border-bone-200/10 (main nav bottom)
  - TopNav.tsx:32 - border border-bone-200/20 (mobile dropdown)

  2. Agent Cards

  - AgentCard.tsx:46 - border-2 border-bone-200/20 (main card)
  - AgentCard.tsx:60 - border border-bone-200/20 (status badge)
  - AgentCircle.tsx - Multiple agent-specific borders (blue/green/orange)

  3. GGBot Emblem System

  - GGBotCircle.tsx:76 - border-2 border-bone-200/20 (emblem card)
  - GGBotCircle.tsx:96 - border-2 border-bone-200 (large circle)
  - GGBotCircle.tsx:107 - border-2 border-green-400 (status ring)
  - GGBotCircle.tsx:176 - border-2 border-bone-200/20 (control panel)

  4. Trade/Performance Components

  - TradeTable.tsx:32 - border-b border-bone-200/10 (table header)
  - PerformanceChart.tsx:94 - border: '1px solid rgba(227, 229, 230, 0.2)'
  (tooltip)
  - MainDashboard.tsx:121,126 - border-2 border-bone-200/20 (containers)

  5. Modals/Popups

  - AgentConfigModal.tsx:82 - border border-bone-200/20 (main modal)
  - AgentConfigModal.tsx:85 - border-b border-bone-200/10 (header separator)
  - AgentConfigModal.tsx:86-88 - border-l-4 border-l-agents-* (accent
  borders)

  6. Configuration Forms

  - Extensive borders in all config forms (extraction, decision, trading)
  - Button borders, input borders, container borders
  - All follow border-bone-200/20 or agent-specific colors

  Color Scheme Patterns

  - Standard: border-bone-200/20 (most common)
  - Subtle: border-bone-200/10
  - Agent Colors: border-agents-extraction/decision/trading
  - Status: border-green/yellow/red-400/20
  - Emphasis: border-2 for thicker borders


  GGBot Central State Management Analysis

  Core Architecture

  The GGBotCircle component acts as the central state orchestrator for the
  entire application through the Zustand store. Here's how:

  1. Bot-as-Config-Container Model

  Each bot is essentially a container for a unique config_id that links to:
  - Database: configurations table with config_id as primary key
  - 3 Agent Configs: Each bot has extraction, decision, and trading configs
  stored under its config_id
  - Trade Data: All trades are linked via config_id
  - Performance Metrics: Calculated from trades with matching config_id

  2. State Flow Architecture

  User selects bot in GGBotCircle
      ↓
  currentBotId changes in store
      ↓
  selectBot() triggers cascade:
      → Resets all agent configs to null
      → Clears trades and performance data
      → Calls loadConfigurations()
          ↓
      API calls with config_id:
      → GET /api/config/{user_id}/extraction?config_id={currentBotId}
      → GET /api/config/{user_id}/decision?config_id={currentBotId}
      → GET /api/config/{user_id}/trading?config_id={currentBotId}
          ↓
      Components re-render with new data

  3. State Dependencies

  Agent Cards depend on:
  - currentBotId → Which configs to display
  - agentStatuses → Visual state (configured/unconfigured)
  - extractionConfig/decisionConfig/tradingConfig → Actual configuration
  data

  Trade Container depends on:
  - currentBotId → Filter trades by config_id
  - trades[] → Trade data filtered for current bot

  Performance Container depends on:
  - currentBotId → Calculate metrics for specific bot
  - performance → Aggregated data from trades with matching config_id

  4. Critical State Management Issues

  1. Missing config_id propagation: The store doesn't properly pass
  config_id to API calls
  2. Incomplete bot creation: New bots create local IDs but don't persist to
   database
  3. State isolation gaps: Bot switching clears data but doesn't reload with
   new config_id
  4. API integration incomplete: Mock data fallbacks hide the broken
  config_id flow

  5. Database Integration Points

  The configurations table structure:
  - config_id (UUID) - Links everything together
  - user_id (UUID) - User isolation
  - config_type (VARCHAR) - 'extraction', 'decision', 'trading'
  - config_name (VARCHAR) - Bot display name
  - config_data (JSONB) - Actual configuration

  6. Real Implementation Flow

  -- When user selects BOT-02:
  SELECT * FROM configurations
  WHERE user_id = '00000000-0000-0000-0000-000000000001'
  AND config_name = 'BOT-02';

  -- Returns config_id = 'abc123...'
  -- Then load all configs:
  SELECT * FROM configurations
  WHERE config_id = 'abc123...'
  AND config_type IN ('extraction', 'decision', 'trading');

  -- Load trades:
  SELECT * FROM trades
  WHERE config_id = 'abc123...';

  -- Calculate performance from those trades

  7. State Management Hierarchy

  GGBotCircle (UI Control)
      ↓
  useBotStore (Central State)
      ↓
  currentBotId (Master Key)
      ↓
  ┌─────────────┬─────────────┬──────────────┬────────────┐
  │ Agent Cards │   Trades    │ Performance  │ Scheduler  │
  │ (3 configs) │  Container  │  Container   │  Control   │
  └─────────────┴─────────────┴──────────────┴────────────┘

  The GGBotCircle is effectively the master control panel that drives the
  entire application state through bot selection, making currentBotId the
  most critical piece of state in the entire system.