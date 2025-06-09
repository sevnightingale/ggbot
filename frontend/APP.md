# APP.md – ggbots Frontend Architecture & UI Scope

## 🧠 Overview

The **ggbots app interface** is a clean, immersive, single-screen control environment where users build, configure, monitor, and scale fully autonomous AI trading agents (ggbots).

It prioritizes **clarity, agency, and visual feedback**, built around a core metaphor: your ggbot is a system composed of three intelligent agents—Extraction, Decision, and Trading—each essential, modular, and visualized as part of an animated, interactive layout.

The dashboard provides complete transparency into your ggbot's intelligence, showing not just what it trades, but exactly how it thinks and why it acts.

---

## 🧭 Design Principles

- **Everything on one screen.** All interaction is scoped to a single immersive dashboard.
- **No sidebar. No tabs.** A minimalist top-right menu handles navigation.
- **Cinematic flow.** A central ggbot hub with orbiting agent nodes and animated state changes.
- **Full transparency.** Every trade reveals the complete decision-making process.
- **Test before deploy.** Manual test runs build confidence before autonomous operation.
- **Responsive-first.** Works seamlessly across desktop and mobile.

---

## 🧱 UI Structure

### 🧠 Main View: ggbot Dashboard

#### 🔝 Top Area: ggbot Configurator

The top 2/3 of the screen contains a **central ggbot hub** with orbiting agent icons and control elements.

##### Components:
- **Center Circle:** "Your ggbot"  
  - Title/Label: customizable  
  - Visual state: inactive (gray), active (glowing), live (pulsing)
  - Shows current scheduler state (autonomous on/off)
- **Orbiting Agent Circles:**
  - Extraction Agent (Blue) - Market data & indicators
  - Decision Agent (Green) - Strategy & analysis
  - Trading Agent (Orange) - Execution & risk management
  - Clickable → opens modal configuration flow
  - Visual states: inactive (gray), configured (colored), live (pulsing/glowing)
  - Live activity indicators during processing
- **Connecting Lines:** Thin visual links from each agent to the center bot  
  - Animate glow once active  
  - Pulse during data flow between agents

##### Control Elements:
- **Deploy Button:** Appears once all agents configured
  - "Test Run" - Execute one cycle manually (calls extraction webhook once)
  - "Go Live" - Start autonomous operation (scheduler start)
- **Status Indicator:** Shows scheduler state and next run time
- **Emergency Stop:** Prominent button to halt all trading (scheduler stop)

##### Future: Multi-Bot Support
- Currently single ggbot (one config_id: a93de31b-9b8a-42e3-827d-c31e580f5f36)
- Future: carousel arrows to switch between multiple configs
- Each bot would have independent settings and performance tracking

---

### 📊 Bottom Area: ggbot Intelligence Output

The lower 1/3 of the screen shows active outputs for the currently selected bot.

##### Left Panel: Trade History
- Live trade list from `/dashboard/{user_id}/trades` endpoint
- Columns: Symbol, Side, Entry, Current/Exit, P&L, Status, Time
- **Click trade → Intelligence Trail Modal** (detailed breakdown)
- Real-time updates via WebSocket (`/ws/dashboard/{user_id}`)
- Visual indicators: green (winning), red (losing), yellow (active)

##### Right Panel: Performance Metrics  
- Data from `/dashboard/{user_id}/performance` endpoint
- Live P&L graph with daily breakdown
- Key metrics displayed:
  - Total P&L and percentage
  - Win rate (winning/total trades)
  - Average win vs average loss
  - Profit factor
  - Max drawdown
- Period selector: 1d, 7d, 30d, all
- Real-time balance updates

---

## 💡 Trade Intelligence Trail

### The Complete Story Behind Every Trade

Clicking any trade opens a modal revealing the full decision process:

```
[BTC/USD SHORT - Entry: $105,405 | P&L: +$178]

📊 EXTRACTION (What I Saw)
└─ 2025-01-20 14:30:00
   ├─ RSI: 72.3 (Overbought) 
   ├─ MACD: Bearish divergence
   └─ Analysis: "Strong overbought conditions with momentum weakening..."

🧠 DECISION (What I Thought)  
└─ Confidence: 65%
   ├─ Strategy: "RSI > 50, entering SHORT position"
   ├─ Risk: "Stop at resistance: $107,000"
   └─ Target: "Support level: $104,500"

⚡ EXECUTION (What I Did)
└─ Orders Placed:
   ├─ Market Sell: 10,000 contracts @ $105,405 ✓
   ├─ Stop Loss: Buy 10,000 @ $107,000 (Active)
   └─ Take Profit: Buy 10,000 @ $104,500 (Active)
```

This transparency builds trust and helps users understand and improve their strategies.

---

## 🔧 Agent Configuration Modals

### Extraction Agent (Blue)
Via `GET/PUT /agent/api/config/{user_id}/extraction`:
- **Symbols**: Multi-select for trading pairs (BTC/USDT, ETH/USDT, etc.)
- **Timeframes**: Checkboxes (15m, 1h, 4h, 1d)
- **Indicators**: Toggle list (RSI, MACD, Bollinger Bands, etc.)
- **Advanced**: LLM interpretation on/off

### Decision Agent (Green)  
Via `GET/PUT /agent/api/config/{user_id}/decision`:
- **Strategy**: Large text area for natural language strategy
- **Risk Guidelines**: Max position size, leverage limits, drawdown rules
- **LLM Provider**: Dropdown (DeepSeek, OpenAI, etc.)
- **Additional Context**: Optional preferences and style notes

### Trading Agent (Orange)
Via `GET/PUT /agent/api/config/{user_id}/trading`:
- **Risk Rules**: 
  - Max leverage slider (1-100x)
  - Position size % of capital
  - Max contracts per trade
- **Exchange**: Currently BitMEX (future: multi-exchange)
- **Safety**: Min equity protection percentage

---

## 🌐 Navigation

### 📎 Top-Right Menu Icon
- 3-bar hamburger icon
- Expands into a clean overlay menu

**Menu Items:**
- My ggbot (returns to dashboard)
- Settings (API keys via environment)
- Docs (link to documentation)
- Profile / Logout

**Future Menu Items:**
- My ggbots (when multi-bot supported)
- Discover (subscribe to other bots)
- Analytics (aggregate performance)

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
- `WS /ws/dashboard/{user_id}` - Real-time updates

**Testing:**
- `POST /extraction/webhooks/trigger-extraction` - Manual test run

---

## 🧩 Component Architecture

| Component               | Description | API Integration |
|------------------------|-------------|-----------------|
| `AgentNode`            | Visual agent circles with config state | Config API GET |
| `GGBotCore`            | Central hub showing bot state | Scheduler status |
| `AgentConfigModal`     | Configuration forms for each agent | Config API GET/PUT |
| `TradeTable`           | Live trade list with click actions | Dashboard trades API |
| `TradeDetailModal`     | Full intelligence trail view | Multiple endpoints |
| `PerformanceChart`     | Real-time P&L and metrics | Dashboard performance API |
| `ControlPanel`         | Test/Deploy/Stop buttons | Scheduler & webhook APIs |
| `TopNavMenu`           | Minimal navigation overlay | N/A |

---

## 🌀 Implementation Roadmap

### Phase 1: Core Dashboard
1. Agent visualization with configuration state
2. Basic config modals for all three agents
3. Deploy/Stop functionality via scheduler API
4. Trade list with real-time updates
5. Performance metrics display

### Phase 2: Intelligence Layer
1. Trade detail modal with full decision trail
2. Extraction data visualization
3. Decision reasoning display
4. Order status tracking

### Phase 3: Enhanced UX
1. Test run functionality
2. Live activity indicators on agents
3. Smooth animations and transitions
4. Mobile responsive design
5. Error handling and user feedback

### Phase 4: Future Features
1. Multi-bot carousel support
2. Strategy templates
3. Advanced analytics
4. Social/marketplace features

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