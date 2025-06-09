# APP.md – ggbots Frontend Architecture & UI Scope

## 🧠 Overview

The **ggbots app interface** is a clean, performant control environment where users build, configure, monitor, and scale fully autonomous AI trading agents (ggbots).

It prioritizes **clarity, performance, and trust**, built around a core metaphor: your ggbot is a system composed of three intelligent agents—Extraction, Decision, and Trading—each essential, modular, and visualized as part of a lightweight, functional interface.

The dashboard provides essential transparency into your ggbot's intelligence, showing not just what it trades, but why it acted—without overwhelming detail.

---

## 🧭 Design Principles

- **Page-based navigation.** Clean routes for bot overview, individual bot details, and configuration.
- **Performance first.** Fast loading, smooth interactions, no unnecessary complexity.
- **Functional visualization.** Agent metaphor serves understanding, not aesthetics.
- **Essential transparency.** Clear reasoning for trades without information overload.
- **Test before deploy.** Manual test runs build confidence before autonomous operation.
- **Desktop-optimized, mobile-compatible.** Built for traders who use desktop but graceful on mobile.

---

## 🧱 UI Structure

### 🧠 Main Views

#### 📋 Bot Overview Page (`/app`)

List of all user ggbots with basic status and performance.

##### Components:
- **Bot Cards:** Simple grid showing each bot's name, status, and recent P&L
- **Create New Bot:** Plus button to create new ggbot
- **Quick Actions:** Start/stop scheduler from overview

#### 🤖 Individual Bot Page (`/bot/:id`)

##### 🔝 Top Area: Agent Status & Configuration

Visual layout showing the three-agent system with subtle animation effects.

##### Components:
- **Agent Configuration Visual:**
  - Three circular agent nodes arranged in triangle formation
  - Each node shows agent name and status
  - **Glow Effects**: Configured agents pulse with their color (blue/green/orange)
  - **Flow Animation**: Animated SVG lines show data flow from agents to central ggbot
  - Click any agent circle → opens configuration modal
  
- **Bot Control Panel:**
  - Bot name and current status
  - Start/Stop autonomous mode
  - Manual test run button
  - Emergency stop (prominent when live)

##### Navigation:
- **Breadcrumb:** My Bots > Bot Name
- **Bot Selector:** Dropdown to switch between bots (when multiple exist)
- **Top Menu:** Minimal hamburger menu for settings, docs, profile

---

### 📊 Performance Area: Bot Intelligence Output

Two-column layout below agent status showing current state and history.

##### Left Panel: Active Trades
- Current positions from `/dashboard/{user_id}/trades` endpoint
- Simple table: Symbol, Side, Entry, Current, P&L, Time
- **Click trade → Trade Detail Modal** (lightweight reasoning view)
- Polling updates every 30s (no WebSocket in v1)
- Clear visual indicators: green (winning), red (losing)

##### Right Panel: Performance Overview
- Data from `/dashboard/{user_id}/performance` endpoint
- Simple P&L chart using Recharts
- Essential metrics only:
  - Total P&L (absolute and percentage)
  - Win rate
  - Total trades
- Period selector: 1d, 7d, 30d
- Polling updates every 60s

---

## 💡 Trade Reasoning (Lightweight)

### Simple Trade Explanation

Clicking any trade opens a clean modal with essential reasoning:

```
[BTC/USD SHORT - Entry: $105,405 | P&L: +$178]

Trigger: RSI overbought (72.3) + MACD bearish divergence
Decision: Short position, 65% confidence
Execution: 10,000 contracts @ $105,405
Stop Loss: $107,000 | Take Profit: $104,500
```

Focused on answering "why did it trade?" without overwhelming detail.

---

## 🔧 Agent Configuration System

### Interaction Pattern

The three agent circles in the main dashboard are clickable elements that open configuration modals:

**Agent Circle Design:**
- Circular icons with agent names inside
- Color-coded borders/glow effects (blue/green/orange)
- Status indicators:
  - ✓ Fully configured (green check)
  - ⚠️ Partially configured (yellow warning)
  - ⚙️ Not configured (gray gear)
- Hover states for visual feedback
- Entire circle is clickable to open configuration

### Individual Agent Configuration Modals

Each agent has its own modal with tabbed navigation for easy editing:

#### 🔵 Extraction Agent Modal (Blue accent)
Via `GET/PUT /agent/api/config/{user_id}/extraction`:

**Tab 1: Symbols**
- Multi-select dropdown with search functionality
- Popular pairs displayed at top
- Real-time symbol validation

**Tab 2: Timeframes**
- Checkbox grid layout (15m, 1h, 4h, 1d)
- Visual indication of selected timeframes

**Tab 3: Data Sources**
- Toggle switches for each source type
- Expandable configuration per source:
  - **Indicators MCP**: Multi-select from 78 technical indicators
  - **TradingView**: Strategy name input field (future)
  - **News/Sentiment**: Source selection (future)
- Source-specific settings appear when enabled

#### 🟢 Decision Agent Modal (Green accent)
Via `GET/PUT /agent/api/config/{user_id}/decision`:

**Tab 1: Strategy**
- Large textarea with syntax highlighting
- Strategy template examples
- Character/word count indicator

**Tab 2: LLM Settings**
- Provider dropdown (DeepSeek, OpenAI)
- Model selection based on provider
- API key validation

**Tab 3: Context**
- Additional trading preferences
- Market behavior notes
- Personal trading style inputs

#### 🟠 Trading Agent Modal (Orange accent)
Via `GET/PUT /agent/api/config/{user_id}/trading`:

**Tab 1: Exchange**
- Exchange selection dropdown
- API credential inputs
- Connection test button with live feedback

**Tab 2: Risk Management**
- **Position Sizing**: Percentage slider with live preview
- **Leverage Control**: Max leverage slider (1x-100x)
- **Loss Limits**: Daily loss limit, max drawdown
- **Safety Rules**: 
  - Stop loss configuration
  - Min equity protection threshold
  - Max contracts per trade
- Visual risk calculator showing impact

**Tab 3: Execution Rules**
- Order type preferences
- Timing constraints
- Slippage tolerance

### Modal UX Features

**Common Elements Across All Modals:**
- Modal header with agent name and color accent
- Horizontal tab navigation with completion indicators
- Progress bar showing overall configuration status
- Contextual help tooltips on complex fields
- Live validation with error messages
- Save/Cancel buttons with loading states
- Keyboard navigation support (Tab, Enter, Esc)

**Smart Behaviors:**
- Tabs show ✓ when properly configured
- Dependencies highlighted (e.g., Decision shows selected symbols from Extraction)
- Unsaved changes warning on modal close
- Auto-save draft functionality
- Configuration import/export for backup

---

## 🌐 Navigation

### 📎 Simple Top Navigation
- Minimal hamburger menu
- Clean overlay (not sidebar)

**Menu Items:**
- My Bots (returns to overview)
- Settings
- Docs
- Profile

**Future Additions:**
- Analytics
- Community features

---

## 🚀 API Integration Map

### Core Endpoints Used:

**Configuration Management:**
- `GET /agent/api/config/{user_id}/{module}` - Load current configs
- `PUT /agent/api/config/{user_id}/{module}` - Save config changes

**Scheduler Control:**
- `POST /agent/api/scheduler/start` - Go live (autonomous mode)
- `POST /agent/api/scheduler/stop` - Stop autonomous trading
- `GET /agent/api/scheduler/status` - Check if running

**Dashboard Data:**
- `GET /dashboard/api/dashboard/{user_id}/trades` - Trade list  
- `GET /dashboard/api/dashboard/{user_id}/performance` - Metrics
- Polling every 30-60s (no WebSocket in v1)

**Testing:**
- `POST /extraction/webhooks/trigger-extraction` - Manual test run

---

## 🧩 Component Architecture

| Component               | Description | API Integration |
|------------------------|-------------|-----------------|
| `AgentStatusBar`       | Three-section status display | Config API GET |
| `BotControlPanel`      | Start/stop/test controls | Scheduler API |
| `ConfigModal`          | Tabbed configuration interface | Config API GET/PUT |
| `TradeTable`           | Simple trade list | Dashboard trades API |
| `TradeDetailModal`     | Lightweight trade reasoning | Trade details |
| `PerformanceChart`     | Basic P&L chart (Recharts) | Dashboard performance API |
| `BotCard`              | Overview page bot cards | Dashboard summary |
| `TopNavMenu`           | Minimal hamburger navigation | N/A |

---

## 🌀 Implementation Roadmap

### Phase 1: Core Pages & Navigation
1. Bot overview page with list/grid of bots
2. Individual bot detail pages with agent status
3. Basic routing and navigation
4. Start/stop scheduler functionality

### Phase 2: Configuration & Trading
1. Single modal for agent configuration
2. Trade list with polling updates
3. Basic P&L chart
4. Manual test run functionality

### Phase 3: Trade Intelligence
1. Simple trade detail modal with reasoning
2. Performance metrics and history
3. Error handling and loading states
4. Mobile responsive improvements

### Phase 4: Enhancement & Scale
1. Multi-bot management
2. Advanced performance analytics
3. Community features (if validated)
4. Performance optimizations

---

## 🎨 Technical Stack Recommendation

**Frontend Framework:** Next.js 14+ with TypeScript
- App Router for modern React patterns
- Server components for performance
- Built-in API routes if needed

**Styling:** Tailwind CSS
- Rapid development with utility classes
- Dark theme support (charcoal/bone palette)
- Animation utilities for agent states

**State Management:** Zustand or Context API
- Lightweight for single-page app
- Real-time data synchronization
- WebSocket integration

**Data Fetching:** TanStack Query + Native WebSocket
- Automatic refetching and caching
- Optimistic updates
- Real-time position updates

**Charts:** Recharts or Lightweight Charts
- Performance-focused
- Real-time updates
- Customizable styling

**Deployment:** Vercel
- Seamless Next.js integration
- Global CDN
- Preview deployments

---

## ✅ Success Criteria

The dashboard succeeds when users feel they are:
1. **In Control** - Clear configuration and deployment process
2. **Informed** - Complete visibility into bot decisions
3. **Confident** - Test before deploy, emergency stops
4. **Engaged** - Beautiful animations and real-time updates
5. **Empowered** - Their strategy, automated and transparent

No traditional dashboards.  
No confusing interfaces.  
Just **your intelligence, amplified.**