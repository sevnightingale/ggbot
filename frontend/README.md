# GGBot Frontend

A Next.js 14 frontend application for managing autonomous AI trading agents. Built with TypeScript, Tailwind CSS, and designed with a brutalist aesthetic for serious traders.

## 🌟 Overview

The GGBot frontend provides a comprehensive dashboard for configuring, monitoring, and controlling autonomous trading agents. The interface is built around the three-agent system: **Extraction**, **Decision**, and **Trading** agents that work together to execute your trading strategy.

### Key Features

- **Agent Configuration**: Intuitive forms for configuring each of the three trading agents
- **Real-time Monitoring**: Live trade display and performance metrics with 30-second polling
- **Bot Control**: Start/stop autonomous trading mode with safety controls
- **Visual Flow**: Animated agent visualization showing data flow and configuration status
- **Responsive Design**: Desktop-optimized with mobile compatibility

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
│   │   ├── AgentCircle.tsx      # Clickable agent status circles
│   │   ├── AgentFlowVisualization.tsx  # SVG flow diagram
│   │   ├── BotControlPanel.tsx  # Start/stop/test controls
│   │   ├── FlowLine.tsx         # Animated SVG flow lines
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

### Color Palette

The interface uses a brutalist design with minimal colors:

- **Primary**: Charcoal (#161618) backgrounds
- **Text**: Bone (#e3e5e6) for high contrast readability
- **Agent Colors**:
  - Extraction: Blue (#38a1c7)
  - Decision: Green (#2cbe77)
  - Trading: Orange (#be6a47)

### Typography

- **Headlines**: Kanit Bold for impact
- **Body**: Inter for readability
- **UI Elements**: System fonts with careful spacing

### Animation

CSS-only animations for performance:
- **Agent Glow**: Configured agents pulse with their respective colors
- **Flow Lines**: Animated dashed lines show data movement
- **Respects `prefers-reduced-motion`** for accessibility

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

1. **Click agent circle** → Opens tabbed configuration modal
2. **Navigate tabs** → Configure different aspects
3. **Real-time validation** → Immediate feedback on settings
4. **Save configuration** → Updates backend via API
5. **Status indicator** → Circle shows configured/partial/unconfigured state

## 📊 Monitoring Dashboard

### Trade Display
- **Live table** with symbol, side, entry price, current P&L
- **30-second polling** for real-time updates
- **Click trades** for detailed reasoning (future feature)

### Performance Metrics
- **P&L chart** with configurable time periods (1d, 7d, 30d)
- **Key metrics**: Total P&L, win rate, total trades, return percentage
- **Visual indicators** for winning/losing positions

### Bot Control
- **Status display**: Running/stopped with last activity timestamp
- **Configuration status**: Shows which agents are properly configured
- **Controls**: Start/stop autonomous mode, manual test runs
- **Safety checks**: Prevents starting with incomplete configuration

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

Zustand store handles:
- **Configuration state** for all three agents
- **Live trade data** with polling updates
- **Performance metrics** with period selection
- **UI state** for modals and loading states
- **Error handling** with user-friendly messages

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
- [x] Agent flow visualization with clickable circles
- [x] Status indicators with glow animations
- [x] Tabbed configuration modals for all three agents
- [x] Complete configuration forms:
  - [x] Extraction: Symbols, timeframes, indicators (78 available)
  - [x] Decision: Strategy templates, LLM settings, risk guidelines
  - [x] Trading: Exchange setup, risk sliders, execution rules

#### Dashboard
- [x] Bot control panel with start/stop functionality
- [x] Live trade table with polling updates
- [x] Performance chart with Recharts
- [x] Real-time status monitoring

#### User Experience
- [x] Loading states and error handling
- [x] Form validation and user feedback
- [x] Empty states for no data scenarios
- [x] CSS animations with reduced-motion support

### 🔄 Partially Implemented

#### API Integration
- [x] All endpoints defined and typed
- [x] State management connected to API calls
- [x] Configuration save/load functionality
- [ ] **Real backend testing** (ready but untested)

#### Visual Polish
- [x] Basic animations for agent glow and flow
- [ ] **Smooth transitions** between states
- [ ] **Loading skeletons** for better perceived performance

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

This frontend provides a solid foundation for the GGBot autonomous trading system, with room for growth as the product evolves from prototype to production.