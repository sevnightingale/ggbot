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
- **Browser automation** via Playwright for TradingView signal interpretation
- **Technical indicators** via MCP servers (RSI, MACD, 20+ professional indicators)
- **Multi-source data fusion** from exchanges, news feeds, and sentiment analysis
- **Dual storage**: File system + Supabase database with real-time updates

**🧠 [Decision Agent](decision/)** - AI-Powered Trading Intelligence  
- **Advanced reasoning LLMs** (DeepSeek R1, GPT-4) for market analysis
- **Natural language strategies** that adapt dynamically to market conditions
- **Multi-mode operation**: New trade discovery + Active trade management
- **Risk-aware decision making** with confidence scoring and position sizing

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
│                   (Multi-Bot Management)                       │
├─────────────────────────────────────────────────────────────────┤
│                 Central API Orchestration                      │
│                    (main_api.py)                               │
│              ┌─────────────┬─────────────┬─────────────┐       │
│              │ Agent APIs  │ Dashboard   │ Config Mgmt │       │
│              │             │ Analytics   │             │       │
├──────────────┼─────────────┼─────────────┼─────────────┼───────┤
│              │ Extraction  │ Decision    │ Trading     │       │
│              │ Modules     │ Modules     │ Modules     │       │
├──────────────┼─────────────┼─────────────┼─────────────┼───────┤
│                   Core Infrastructure                          │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐     │
│  │ MCP Servers │ Monitoring  │ Config Mgmt │ Database    │     │
│  │             │ & Alerts    │             │ (PostgreSQL)│     │
└──┴─────────────┴─────────────┴─────────────┴─────────────┴─────┘
```

### **[Core Infrastructure](core/)**

**🔧 [MCP Servers](core/mcp/)** - Standardized Tool Integration
- **Crypto Indicators MCP**: 20 professionally preprocessed technical indicators
- **CCXT MCP Server**: Universal exchange connectivity and market data
- **Unified tool interface** for consistent agent-to-service communication

**⏰ [Autonomous Scheduler](core/scheduler/)** - Production-Ready Bot Scheduling
- **APScheduler integration** with Redis idempotency for zero-drift execution
- **Multi-timeframe support**: 5m, 15m, 30m, 1h, 4h, 1d with candle alignment
- **Startup reconciliation** automatically restores active bots
- **Real-time WebSocket updates** with next execution timestamps

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

**Production-ready PostgreSQL schema** supporting:
- **Multi-user isolation** with user_id + config_id architecture
- **Complete audit trail** via strategy_runs for decision transparency
- **Universal trade lifecycle** tracking from signal to settlement
- **Migration system** for schema evolution and deployment

### **[Frontend Platform](frontend/)**

**Professional Next.js application** featuring:
- **V2 Integration**: Dashboard connected to V2 orchestrator with Supabase auth
- **Multi-bot management** with intuitive configuration interfaces  
- **Real-time performance tracking** showing trades, P&L, and analytics
- **Brutalist design system** optimized for trading professionals
- **selectedConfigId architecture** for seamless bot switching and data management

## Production Features

### Live Production Systems

**🎯 [ggShot Signal Validation](signals/)** - V2 Production Signal Processing
- **Generic signal framework** with ggShot as first implementation
- **User-configured validation strategies** replacing hardcoded 4-pillar analysis
- **Real-time Telegram integration** with publishing to user-specified channels
- **Premium business model** gating via ggBase subscription tier
- **Complete V2 integration** using standard extraction → decision → trading pipeline

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
- **$34B+ proven Hummingbot API** for real-time market data (KuCoin connector)
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