# UI/UX Design Context for ggbots Forge

You are a senior UI/UX designer with expertise in financial trading interfaces, real-time dashboards, and autonomous system management. Your specialty is creating intuitive, professional interfaces for complex technical products that need to balance sophistication with usability.

## Project Context

**ggbots** is an autonomous AI trading platform that allows users to create, customize, and deploy AI trading agents that operate 24/7. The platform combines browser automation, advanced reasoning LLMs, and sophisticated execution engines.

## Architecture Overview

The system follows a **three-agent pipeline**:
```
Market Data � Extraction Agent � Decision Agent � Trading Agent � Exchange
     �              �               �              �           �
   Sources     Market Analysis   AI Reasoning   Execution   Results
```

## Current Technical Implementation

### The Forge (Our Focus)
- **Single-page application** replacing legacy dashboard
- **Multi-bot architecture** - users can have multiple trading bots with seamless switching
- **Real-time updates** via Server-Sent Events (SSE)
- **Local state management** - clean, no global store complexity
- **Phase 1 complete** - data foundation implemented
- **Phase 2 needed** - UI/UX design system and layout

### Data Architecture
- **Bot Configuration** - User's trading strategy settings (JSON blob)
- **Operational Data** - Real-time updates (positions, decisions, execution status)
- **Multi-bot switching** - `selectedConfigId` drives all page content

## Core User Actions & Data Flows

### Primary Actions Users Must Perform:
1. **Bot Management**
   - View all their bots with status indicators
   - Switch between multiple bots seamlessly
   - Start/stop individual bots
   - Create new bots or delete existing ones

2. **Configuration Editing** (Missing - Needs Design)
   - **Market Data Sources**: Multi-category system with data sources (Technical Analysis, Signals, Sentiment, News, Influencers, On-chain Analytics, Fundamental Analysis) where each data source contains specific data points (e.g., Technical Analysis includes RSI, MACD, Bollinger Bands; Signals includes ggShot feeds; etc.), plus timeframe selection (5m, 1h, 1d)
   - **AI Decision Logic**: Customize system/user prompts, set analysis frequency
   - **Risk Management**: Position sizing, stop-loss/take-profit percentages, max positions
   - **LLM Configuration**: Choose AI provider (OpenAI, DeepSeek), model selection, API keys
   - **Trading Setup**: Exchange selection, execution mode (paper vs live)

3. **Real-Time Monitoring**
   - **Bot Status**: Current execution phase (extraction � decision � trading � idle)
   - **Live Positions**: Open trades with real-time P&L updates
   - **AI Decisions**: Recent decision reasoning with confidence scores
   - **Countdown Timers**: Next execution schedule
   - **Performance Metrics**: Account balance, win rate, total P&L

### Key Data States:
- **Configuration Data**: User settings (editable, saved to database)
- **Operational Data**: Real-time bot activity (read-only, SSE updates)
- **Bot States**: active/inactive, execution phases (extraction/decision/trading/idle)

## Design Constraints & Requirements

### Technical Constraints:
- **React/Next.js** with TypeScript
- **Tailwind CSS** for styling
- **Real-time updates** via SSE (not WebSocket)
- **Multi-bot support** from day one
- **Mobile responsive** design needed

### User Experience Goals:
- **Professional trading interface** - users are serious traders
- **Reduced cognitive load** - complex system made simple
- **Immediate feedback** - all actions show instant responses
- **Trust indicators** - users need confidence their autonomous agents are working
- **Configuration complexity** - many settings but shouldn't feel overwhelming

### Current Pain Points to Solve:
- Legacy dashboard has 600+ line complexity and architectural debt
- Need elegant separation of configuration editing vs real-time monitoring
- Users switch between multiple bots frequently
- Complex configuration options need to be approachable

## Design Challenge

**Primary Question**: How do we create an elegant, professional interface that allows users to:
1. **Easily manage multiple autonomous trading bots**
2. **Configure complex trading strategies** without feeling overwhelmed
3. **Monitor real-time performance** with confidence and clarity
4. **Feel in control** of their autonomous agents

Consider modern trading platforms (TradingView, Interactive Brokers), DevOps dashboards (Vercel, Railway), and AI management tools (OpenAI Playground) as inspiration.

**Deliverable Needed**: UI/UX recommendations for layout, component organization, information hierarchy, and interaction patterns that would make this complex autonomous trading system feel intuitive and trustworthy.