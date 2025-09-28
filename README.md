# ggbots Platform

**Autonomous AI Trading Agents That Trade Like You**

ggbots is a production-ready platform for creating, customizing, and deploying fully autonomous AI trading agents. The platform combines browser automation, advanced reasoning LLMs, and sophisticated execution engines to enable traders to "train an AI to trade like you" - capturing their unique strategies, insights, and decision-making patterns in an autonomous system that operates 24/7.

## Architecture Overview

The ggbots platform implements a **three-agent autonomous trading pipeline** with **autonomous scheduling** and **signal validation** capabilities:

```
Market Data → Extraction Agent → Decision Agent → Trading Agent → Exchange
     ↑              ↓               ↓              ↓           ↓
   Sources     Market Analysis   AI Reasoning   Execution   Results
     
External Signals → Signal Validation → Decision Agent → Trading Agent → Exchange
     ↑                    ↓                ↓              ↓           ↓
  ggShot/TV        4-Pillar Analysis   AI Reasoning   Execution   Results
```

### Core Agent Architecture

**🔍 [Extraction Agent](extraction/)** - Market Intelligence Gathering
- **V2 System**: 21 advanced preprocessors with pandas-ta integration (12x performance improvement)
- **Multi-exchange fallback**: Automatic failover across 5 exchanges (kucoin→binance→okx→gate_io→ascend_ex)
- **Direct Hummingbot API**: Real-time market data without MCP overhead
- **Technical indicators**: Pure Python pandas-ta integration (RSI, MACD, 20+ professional indicators)
- **Multi-timeframe analysis**: 5m, 15m, 30m, 1h, 4h, 1d with consolidated data
- **Supabase database storage**: Real-time updates with orchestrator integration

**🧠 [Decision Agent](decision/)** - AI-Powered Trading Intelligence
- **GPT-5 Integration**: High-effort reasoning via OpenAI Responses API
- **Multi-exchange price feeds**: Real-time pricing with automatic exchange fallback
- **Template-based prompts**: Opportunity analysis, signal validation, position management
- **Multi-mode operation**: New trade discovery + Active trade management
- **User customization**: Natural language strategy definition with config integration
- **Risk-aware decisions**: Confidence scoring and position sizing algorithms

**⚡ [Trading Agent](trading/)** - Precision Execution Engine
- **Paper Trading Engine** - Professional-grade simulation with real Hummingbot market data
- **Isolated accounts** - $10,000 starting balance per strategy configuration
- **Real-time monitoring** - 7-second price updates with automatic TP/SL execution
- **Confidence-based sizing** - Position size = confidence × max position (10% of balance)
- **Risk enforcement** with portfolio limits, exposure tracking, and emergency controls
- **Multi-exchange support** with advanced order types (live trading expansion planned)

## Platform Infrastructure

### Multi-User Platform Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                           │
│                 (Dashboard V2 + Real-time UI)                  │
├─────────────────────────────────────────────────────────────────┤
│                 V2 Orchestrator (ggbot.py)                     │
│              APScheduler + WebSocket + FastAPI                 │
│              ┌─────────────┬─────────────┬─────────────┐       │
│              │ Extraction  │ Decision    │ Trading     │       │
│              │    V2       │ Engine V2   │ Paper API   │       │
├──────────────┼─────────────┼─────────────┼─────────────┼───────┤
│                   Core Infrastructure                          │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐     │
│  │ Hummingbot  │ Monitoring  │ Config Mgmt │ Database    │     │
│  │ API         │ & Alerts    │             │ (Supabase)  │     │
└──┴─────────────┴─────────────┴─────────────┴─────────────┴─────┘
```

### **[Core Infrastructure](core/)**

**🔧 [Data Integration](extraction/v2/)** - Direct API Connections
- **Hummingbot API**: Real-time market data and price feeds (localhost:8888)
- **pandas-ta Library**: 20+ technical indicators with pure Python processing
- **Supabase Database**: Real-time data storage and retrieval

**⏰ [Autonomous Scheduler](core/scheduler/)** - V2 Orchestrator Integration
- **APScheduler integration** in ggbot.py for zero-drift execution
- **Multi-timeframe support**: 5m, 15m, 30m, 1h, 4h, 1d with candle alignment
- **Startup reconciliation** automatically restores active bots from Supabase
- **Real-time WebSocket updates** with countdown timers and execution status

**🎯 [Symbol Standardization](core/symbols/)** - Universal Trading Pair Management
- **141 trading pairs** with comprehensive format support across all systems
- **Multi-format conversion**: ggShot (`BTCUSDT`) ↔ CCXT (`BTC/USDT`) ↔ Hummingbot (`BTC-USDT`)
- **Validation and suggestions** for format errors and unsupported symbols

**📊 Monitoring & Observability**
- **Position tracking** via database queries with real-time P&L
- **Performance analytics** with comprehensive trade lifecycle tracking
- **Health checks** via API endpoints and WebSocket status broadcasts

**⚙️ [Configuration Management](core/config/)**
- **JSON blob configuration system** with template-based setup
- **Config-ID architecture** with multi-user isolation
- **State persistence** for autonomous bot management

### **[Database Layer](database/)**

**Production-ready Supabase PostgreSQL** supporting:
- **Multi-user isolation** with user_id + config_id architecture
- **Paper trading tables**: paper_accounts, paper_trades with real-time updates
- **Decision audit trail** via decisions table for full transparency
- **Migration system** for schema evolution and deployment

### **[Frontend Platform](frontend/)**

**Professional Next.js application** featuring:
- **Forge Architecture**: Clean rebuild with elegant local state patterns (see `FORGE.md`)
- **Multi-bot management** with `selectedConfigId` switching and intuitive interfaces
- **Real-time performance tracking** with SSE streams and countdown timers
- **Direct API integration** using `BotConfiguration` types without transformation layers
- **Supabase authentication** with JWT token-based API access
- **Legacy Dashboard V2**: Deprecated due to WebSocket complexity and architectural debt

## Production Features

### Live Production Systems

**🎯 [ggShot Signal Validation](signals/)** - V2 Production Signal Processing
- **Signal validation mode** integrated into V2 decision engine
- **Service-to-service authentication** with secure signal routing
- **AI confidence evaluation** of external trading signals with strategy alignment
- **Real-time Telegram integration** with publishing capabilities
- **Premium business model** with subscription-based access
- **V2 orchestrator integration** using extraction → decision → trading pipeline

**🤖 [Autonomous Scheduling](core/scheduler/)** - Production Bot Management
- **Zero-drift execution** aligned to market candle boundaries
- **Redis-based idempotency** preventing duplicate trades across restarts
- **Multi-timeframe bots** running 5m to daily cadences simultaneously
- **Real-time config updates** without service restarts

**📈 [TradingView Automation](extraction/sources/tradingview/)**
- **Browser-based chart analysis** with visual signal interpretation
- **Custom indicator integration** for proprietary trading strategies
- **Automated screenshot capture** and AI-powered chart reading
- **Session management** with cookie persistence and error recovery

### Enterprise-Grade Execution

**🏛️ [Paper Trading Engine](trading/)** (Production Ready)
- **$34B+ proven Hummingbot API** with multi-exchange fallback (5 exchanges)
- **Professional simulation** - Real prices, realistic spreads, accurate fees (0.06% taker)
- **Isolated accounts** - $10,000 starting balance per strategy configuration
- **Automated risk management** - 7-second monitoring with auto TP/SL execution
- **Complete audit trail** - Full trade lifecycle tracking and performance analytics
- **Multi-exchange connectivity** and live trading (Phase 2-3 planned)

**🛡️ [Risk Management](trading/)**
- **Position sizing algorithms** based on AI confidence scoring
- **Real-time risk monitoring** with automatic position adjustment
- **Emergency controls** with kill switches and drawdown protection
- **User-defined guardrails** for leverage, position size, and exposure limits

## Development & Testing

### **[Comprehensive Testing](tests/)**

**Modular testing architecture** with:
- **Unit tests** for individual agent components
- **Integration tests** for end-to-end pipeline validation
- **MCP server testing** for tool connectivity and reliability
- **Performance benchmarks** for execution latency and system throughput

### **[Documentation System](DOCS/)**

**Complete technical documentation** including:
- **[Architecture specifications](DOCS/SPEC.md)** with detailed system design
- **[API documentation](DOCS/API.md)** for all platform endpoints
- **[Pipeline documentation](DOCS/FLOW.md)** for end-to-end process flows

## Getting Started

### Understanding the System

1. **Read [DOCS/OVERVIEW.md](DOCS/OVERVIEW.md)** for conceptual foundation
2. **Check [DOCS/ACTIVE.md](DOCS/ACTIVE.md)** for current deployment status and live operations
3. **Explore [DOCS/FLOW.md](DOCS/FLOW.md)** for end-to-end process flow
4. **Review individual module READMEs** for component-specific details

### Module Deep Dives

- **[extraction/README.md](extraction/README.md)** - Market data gathering and processing
- **[decision/README.md](decision/README.md)** - AI reasoning and strategy execution  
- **[trading/README.md](trading/README.md)** - Trade execution and position management
- **[frontend/README.md](frontend/README.md)** - User interface and platform management
- **[core/](core/)** - Shared infrastructure and utilities

### Configuration & Deployment

- **[core/config/README.md](core/config/README.md)** - System configuration and templates
- **[database/README.md](database/README.md)** - Database schema and migrations
- **[hummingbot/README.md](hummingbot/README.md)** - Hummingbot integration setup (Phase 1 complete)

### Planned Updates & Roadmap

- **[DOCS/CONFIG.md](DOCS/CONFIG.md)** - Config component V2 integration roadmap (Phase 8)
- **[DOCS/TODO.md](DOCS/TODO.md)** - V2 architecture progress tracking (Phase 7 complete)
- **[DOCS/TRADING_UPDATE.md](DOCS/TRADING_UPDATE.md)** - Hummingbot integration roadmap (Phases 2-3)
- **[DOCS/FUTURE.md](DOCS/FUTURE.md)** - Comprehensive platform scaling and feature roadmap

## Platform Capabilities

### Multi-User Architecture
- **Config-ID based isolation** enabling multiple bots per user
- **Independent strategy execution** with isolated risk management
- **Scalable infrastructure** design (shared market data cache and microservices planned)

### Advanced AI Integration
- **Reasoning LLM pipeline** with DeepSeek R1 and GPT-4 support
- **Natural language strategy definition** for intuitive customization
- **Dynamic decision adaptation** based on real-time market conditions
- **Confidence-based position sizing** with intelligent risk allocation

### Professional Trading Features
- **140+ trading pair support** across major cryptocurrency exchanges
- **Real-time monitoring** with sub-second execution capabilities
- **Automated TP/SL management** with position tracking
- **Comprehensive analytics** with P&L tracking and performance attribution
- **Advanced order types** (TWAP, iceberg, OCO planned via Hummingbot expansion)

---

**ggbots represents the evolution of autonomous trading - where human expertise meets AI capabilities to create trading agents that truly understand markets, adapt to changing conditions, and execute with the precision of professional trading systems.**