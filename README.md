# ggbots Platform

**Autonomous AI Trading Agents That Trade Like You**

ggbots is a production-ready platform for creating, customizing, and deploying fully autonomous AI trading agents. The platform combines real-time market intelligence, advanced reasoning LLMs, and professional-grade execution engines to enable traders to "train an AI to trade like you" - capturing their unique strategies, insights, and decision-making patterns in an autonomous system that operates 24/7.

---

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
- **Universal Data Layer**: Catalog-driven market intelligence with WebSocket-first architecture (3x-3000x faster)
- **Real-time WebSocket cache**: Binance WebSocket streaming 100 symbols × 7 timeframes
- **Technical indicators**: Pure Python pandas-ta integration (RSI, MACD, 20+ professional indicators)
- **ggShot Signals**: Premium signal context for autonomous trading (permission-gated via paid_data_points)
- **Multi-timeframe analysis**: 5m, 15m, 30m, 1h, 4h, 1d with consolidated data
- **Supabase database storage**: Real-time updates with orchestrator integration

**🧠 [Decision Agent](decision/)** - AI-Powered Trading Intelligence
- **GPT-5 Integration**: High-effort reasoning via OpenAI Responses API
- **Real-time price feeds**: Live WebSocket prices (sub-millisecond access, ~1s freshness)
- **Template-based prompts**: Opportunity analysis, signal validation, position management
- **Multi-mode operation**: New trade discovery + Active trade management
- **User customization**: Natural language strategy definition with config integration
- **Risk-aware decisions**: Confidence scoring and position sizing algorithms

**⚡ [Trading Agent](trading/)** - Precision Execution Engine
- **Paper Trading Engine** - Professional-grade simulation with real market data
- **Live Trading Engine** - Symphony.io integration for real-money execution (100 compatible symbols)
- **AsterDEX Integration** - Decentralized futures trading with Web3 authentication (33 compatible symbols, up to 20x leverage)
- **Dynamic Position Sizing** - Real-time account balance queries with config-based calculations
- **Agent Override Support** - Autonomous agents can control position size and leverage independently
- **Isolated accounts** - $10,000 starting balance per strategy configuration
- **Real-time monitoring** - 3-second price updates with automatic TP/SL execution
- **Risk enforcement** with portfolio limits, exposure tracking, and emergency controls
- **Multi-exchange support** with Symphony.io and AsterDEX integrations

---

## 📁 Codebase Structure

The ggbot repository is organized into the following top-level directories:

| Directory | Purpose | Status | Key Files |
|-----------|---------|--------|-----------|
| **agent/** | Autonomous trading agent foundation (MCP server, tools, chat) | 🟡 In Development | run_agent.py, mcp_server.py, service_client.py |
| **api/** | API endpoints for agent operations | ✅ Active | agent.py, paper_trading.py, symbols.py |
| **core/** | Core business logic (auth, config, domain, services) | ✅ Active | 16 subdirectories |
| **decision/** | AI decision engine with V2 template system | ✅ Active | README.md, prompts/, engine_v2.py |
| **extraction/** | Market data extraction with 21 preprocessors | ✅ Active | v2/ with README.md |
| **trading/** | Paper & live trading execution engines | ✅ Active | README.md, paper/, live/ |
| **frontend/** | Next.js Forge application | ✅ Active | README.md, app/forge/ |
| **market_intelligence/** | Market data orchestrator (32 data points, 7 categories) | ✅ Active | README.md, orchestrator.py |
| **signals/** | Signal processing, Telegram publishing, ggShot parser | ✅ Active | listener_service.py, ggshot_parser.py |
| **database/** | Schema, migrations, and database utilities | ✅ Active | README.md, migrations/ |
| **tests/** | Integration and unit testing suite | ✅ Active | test_trading_flow_simple.py |
| **scripts/** | Utility scripts (status checks, maintenance, testing) | ✅ Active | status_check.py, maintenance_*.py |
| **x_bot/** | Twitter bot for platform status updates | ✅ Active | Platform tweets at @ggbots_ai |
| **archive/** | Legacy code preserved for reference | 🔒 Archived | 15 archived directories (includes ggshot/) |

**Note**: The `agent/` directory contains the foundation for fully autonomous AI trading agents (Phase 3 - MCP server and tools operational, frontend integration in progress). See [TODO.md](TODO.md) for agent development roadmap.

---

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
│  │ WebSocket   │ Monitoring  │ Config Mgmt │ Database    │     │
│  │ Prices      │ & Alerts    │             │ (Supabase)  │     │
└──┴─────────────┴─────────────┴─────────────┴─────────────┴─────┘
```

### **[Core Infrastructure](core/)**

**🔧 [Data Integration](extraction/v2/)** - Direct API Connections
- **Universal Data Layer**: Catalog-driven market intelligence gateway with WebSocket caching (3x faster extractions)
- **Intelligence Orchestrator**: Config-driven data routing for 150+ data sources without code bloat
- **Live Price Feeds**: Real-time prices via Binance WebSocket (sub-millisecond access, ~1s updates)
- **pandas-ta Library**: 20+ technical indicators with pure Python processing
- **Supabase Database**: Real-time data storage and retrieval

**⏰ [Autonomous Scheduler](core/scheduler/)** - V2 Orchestrator Integration
- **APScheduler integration** in ggbot.py for zero-drift execution
- **Multi-timeframe support**: 5m, 15m, 30m, 1h, 4h, 1d with candle alignment
- **Startup reconciliation** automatically restores active bots from Supabase
- **Real-time WebSocket updates** with countdown timers and execution status

**🎯 [Symbol Standardization](core/symbols/)** - Universal Trading Pair Management
- **141 trading pairs** with comprehensive format support across all systems (100 Symphony-compatible for live trading)
- **Multi-format conversion**: ggShot (`BTCUSDT`) ↔ CCXT (`BTC/USDT`) ↔ Symphony (`BTC`)
- **Validation and suggestions** for format errors and unsupported symbols

**📊 Monitoring & Observability**
- **Position tracking** via database queries with real-time P&L
- **Performance analytics** with comprehensive trade lifecycle tracking
- **Health checks** via API endpoints and WebSocket status broadcasts
- **Email notifications** via Resend integration (welcome emails, trade alerts ready)

**⚙️ [Configuration Management](core/config/)**
- **JSON blob configuration system** with template-based setup
- **Config-ID architecture** with multi-user isolation
- **State persistence** for autonomous bot management

### **[Frontend Platform](frontend/)**

**Professional Next.js 15 application** deployed at **app.ggbots.ai** featuring:

**Forge** - Main Production Interface (`/forge`):
- **Multi-bot management** with intuitive bot rail and configuration switching
- **Real-time monitoring** with SSE streams, performance charts, and position tables
- **Configuration wizard** with market data selection, strategy editor, and trade settings
- **Subscription system** with Stripe integration and premium feature gates
- **Activity Timeline Viewer** (`/view/[config_id]`) - Canvas-based trade visualization (mock data, demo)

**Core Components** (~10 major components):
- Layout: Header, BotRail, TabNavigation, UserProfile with subscription badge
- Monitoring: ActivationBar, MetricsBar, DecisionFeed, PositionsTable with real-time P&L
- Configuration: ConfigTabs, MarketDataSelector, StrategyEditor, TradeSettings, SaveConfigBar
- Shared: UpgradeModal, SymbolSelector, DuplicateAsLiveModal

**Technical Architecture**:
- **Server Components** with Supabase auth and JWT token-based API access
- **Direct API integration** using `BotConfiguration` types without transformation layers
- **SSE Streams** for real-time updates (dashboard-stream) with countdown timers
- **Vercel deployment** with automatic git-based CI/CD

## Production Features

### Live Production Systems

**🎯 [ggShot Signal Integration](signals/)** - Dual-Mode Signal Processing
- **Signal validation mode**: Real-time push-based validation with Telegram publishing
- **Autonomous trading mode**: Pull-based signal context alongside technical indicators
- **Service-to-service authentication** with secure signal routing
- **AI confidence evaluation** of external trading signals with strategy alignment
- **Multi-timeframe signals**: Latest signal per timeframe (30m, 1h, 4h, 5m)
- **Premium business model** with subscription-based access (paid_data_points gating)
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
- **Real-time WebSocket prices** from Binance (sub-millisecond Redis access, ~1s updates)
- **Professional simulation** - Live prices, realistic spreads, accurate fees (0.06% taker)
- **Isolated accounts** - $10,000 starting balance per strategy configuration
- **Automated risk management** - 3-second monitoring with auto TP/SL execution
- **Complete audit trail** - Full trade lifecycle tracking and performance analytics
- **Live trading** - Symphony.io integration for real-money execution (100 compatible symbols)

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

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.10.12 | Core backend language |
| **FastAPI** | 0.115.12 | REST API framework |
| **APScheduler** | 3.11.0 | Autonomous bot scheduling |
| **pandas-ta** | 0.3.14b0 | Technical indicators (21 preprocessors) |
| **PostgreSQL** | Remote (Supabase) | Main application database |
| **Redis** | 6379 | WebSocket cache, queues, idempotency |
| **asyncpg** | 0.29.0 | Async PostgreSQL driver |
| **psycopg2-binary** | 2.9.10 | Sync PostgreSQL driver |
| **loguru** | 0.7.3 | Structured logging |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 15.3.3 | React framework with App Router |
| **React** | 19.0.0 | UI library |
| **TypeScript** | 5.x | Type safety |
| **Tailwind CSS** | 3.4.17 | Styling framework |
| **Supabase** | 2.57.0 | Auth & Database client |
| **Zustand** | 5.0.7 | State management |
| **Recharts** | 2.15.4 | Performance charts |
| **Vercel** | - | Production deployment |

### AI/LLM Providers
| Provider | Integration | Models |
|----------|-------------|--------|
| **Anthropic** | 0.49.0 | Claude Haiku 4.5, Sonnet 4.5, Opus 4 |
| **OpenAI** | 1.70.0 | GPT-4, GPT-5 (Responses API) |
| **XAI** | 1.3.1 | Grok 4 (Agentic API for market intelligence) |
| **Google** | 2.1.2 | Gemini models |
| **DeepSeek** | - | R1 reasoning model |

### Trading & Data
| Service | Purpose | Status |
|---------|---------|--------|
| **Symphony.io** | Live trading execution | ✅ 100 symbols supported |
| **Binance** | Real-time WebSocket prices | ✅ market-data-ws service |
| **CCXT** | Multi-exchange library | ✅ 4.4.80 |
| **Stripe** | Subscription payments | ✅ 11.1.0 |

### Infrastructure
| Service | Purpose | Access |
|---------|---------|--------|
| **PM2** | Process management | 5 services (ggbot, market-data-ws, signal-listener, x-bot, error-alerts) |
| **Supabase** | PostgreSQL + Auth | Remote managed service |
| **Redis** | Cache + Queues | Local (port 6379) |
| **Vercel** | Frontend hosting | Production deployment |

---

## 📚 Module Documentation

The ggbot repository includes 7 comprehensive module READMEs with detailed technical documentation:

| Module | Lines | Contents |
|--------|-------|----------|
| **[extraction/v2/README.md](extraction/v2/README.md)** | 845 | 21 preprocessors, 12x performance, API docs |
| **[market_intelligence/README.md](market_intelligence/README.md)** | 1154 | 32 data points, 7 categories, orchestrator architecture |
| **[decision/README.md](decision/README.md)** | 525 | V2 template system, 3 modes, webhook integration |
| **[trading/README.md](trading/README.md)** | 723 | Paper & live trading, Symphony integration |
| **[frontend/README.md](frontend/README.md)** | 488 | Forge architecture, subscription system |


---

## 📊 Database & Configuration Reference

**For current database schema, domain models, and configuration structure**, see **[ACTIVE.md](ACTIVE.md)**:
- **Database Schema**: Comprehensive schema with PK/FK/indexes/constraints (auto-updated)
- **Domain Models**: Business logic and @property methods (auto-updated)
- **Configuration Structure**: config_data JSONB fields from BotConfig model (auto-updated)

**For database design decisions and WHY**, see **[DOCS/DATABASE_CONTEXT.md](DOCS/DATABASE_CONTEXT.md)**.

---

## 🗄️ Repository Layer (Data Access)

Repositories provide the data access layer, mapping domain models to database tables.

| Repository | Database Table | Domain Model | Purpose |
|------------|----------------|--------------|---------|
| `PositionRepository` | `paper_trades` | `Position` | Trading position lifecycle (save, update, close, query open positions) |
| `MarketDataRepository` | `market_data` | `MarketDataSnapshot` | Store/retrieve market intelligence and indicator data |
| `AccountRepository` | `paper_accounts` | `Account` | Paper trading account balance and performance tracking |
| `ConfigRepository` | `configurations` | `BotConfig` | Bot configuration management and persistence |

**Location**: `core/domain/*_repository.py` and `core/config/repository.py`

---

## 📂 core/ Directory Structure

The `core/` directory contains shared infrastructure used by all agents and modules:

| Subdirectory | Purpose | Key Files |
|--------------|---------|-----------|
| `core/common/` | Database connections, logging, utilities | `db.py`, `logger.py`, `config.py` |
| `core/services/` | Shared services (LLM, user, pricing) | `llm_service.py`, `user_service.py`, `websocket_market_data_service.py` |
| `core/domain/` | Domain models, repositories, business logic | `position.py`, `decision.py`, `user_profile.py`, `*_repository.py` |
| `core/config/` | Configuration management (Pydantic models) | `models.py` (BotConfig), `repository.py` |
| `core/scheduler/` | APScheduler integration for autonomous execution | Bot scheduling and candle alignment |
| `core/symbols/` | Trading pair standardization | Multi-format conversion (CCXT ↔ ggShot ↔ Symphony) |
| `core/auth/` | Authentication and authorization | User authentication, service auth |
| `core/credentials/` | Credential management | LLM API keys, exchange credentials |
| `core/email_templates/` | Email templates | Resend integration templates |
| `core/integrations/` | External service integrations | Third-party API wrappers |
| `core/mcp/` | MCP (Model Context Protocol) tools | Agent tool definitions |
| `core/monitoring/` | System monitoring and observability | Health checks, metrics |
| `core/sse/` | Server-Sent Events | Real-time updates to frontend |

---
