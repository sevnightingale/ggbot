# ggbots Platform

**Autonomous AI Trading Agents That Trade Like You**

ggbots is a production-ready platform for creating, customizing, and deploying fully autonomous AI trading agents. The platform combines real-time market intelligence, advanced reasoning LLMs, and professional-grade execution engines to enable traders to "train an AI to trade like you" - capturing their unique strategies, insights, and decision-making patterns in an autonomous system that operates 24/7.

**Live Production**: 258 users, 383 bots, 5,407+ trades executed

---

## 🚀 Quick Start for New Claude Code Instances

**👉 Start here**: Read **[GO.md](GO.md)** for the standard onboarding procedure. This will:
- Run automated status checks and schema updates
- Guide you through core documentation
- Provide current production metrics
- Help identify what to work on next

**For operational status**: Check **[ACTIVE.md](ACTIVE.md)** for live system resources, platform metrics, and current capabilities.

**For development tasks**: See **[TODO.md](TODO.md)** for prioritized roadmap and current work.

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
- **Isolated accounts** - $10,000 starting balance per strategy configuration
- **Real-time monitoring** - 3-second price updates with automatic TP/SL execution
- **Confidence-based sizing** - Position size = confidence × max position (10% of balance)
- **Risk enforcement** with portfolio limits, exposure tracking, and emergency controls
- **Multi-exchange support** with advanced order types via Symphony.io

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

### **[Database Layer](database/)**

**Production-ready Supabase PostgreSQL** supporting:
- **Multi-user isolation** with user_id + config_id architecture
- **Paper trading tables**: paper_accounts, paper_trades with real-time updates
- **Decision audit trail** via decisions table for full transparency
- **Migration system** for schema evolution and deployment

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

## Getting Started

### For New Claude Code Instances

**👉 Start here**: Read **[GO.md](GO.md)** for the standard onboarding procedure. This will guide you through:
- Reading core documentation in the right order
- Providing a current status assessment
- Identifying what to work on from the TODO list
- Maintaining documentation as you work

### Understanding the System

1. **Read [DOCS/OVERVIEW.md](DOCS/OVERVIEW.md)** for conceptual foundation
2. **Check [ACTIVE.md](ACTIVE.md)** for current deployment status and live operations
3. **Review [CHANGELOG.md](CHANGELOG.md)** for complete feature history and improvements
4. **Explore [DOCS/FLOW.md](DOCS/FLOW.md)** for end-to-end process flow
5. **Review individual module READMEs** for component-specific details

### Module Deep Dives

- **[extraction/v2/README.md](extraction/v2/README.md)** - Technical indicator extraction (21 preprocessors, V2 pure Python system)
- **[market_intelligence/README.md](market_intelligence/README.md)** - **Complete market intelligence architecture** (orchestrator, gateway, catalog, 32 data sources)
- **[decision/README.md](decision/README.md)** - AI reasoning and strategy execution
- **[trading/README.md](trading/README.md)** - Trade execution and position management
- **[frontend/README.md](frontend/README.md)** - User interface and platform management
- **[core/](core/)** - Shared infrastructure and utilities

### Configuration & Deployment

- **[core/config/README.md](core/config/README.md)** - System configuration and templates
- **[database/README.md](database/README.md)** - Database schema and migrations
- **[archive/hummingbot/](archive/hummingbot/)** - Legacy Hummingbot integration (deprecated Oct 2025, replaced by WebSocket prices)

### Planned Updates & Roadmap

- **[TODO.md](TODO.md)** - Current development tasks and roadmap
- **[CHANGELOG.md](CHANGELOG.md)** - Complete history of features, fixes, and improvements
- **[DOCS/CONFIG.md](DOCS/CONFIG.md)** - Config component V2 integration roadmap (Phase 8)


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
- **141 trading pair support** across major cryptocurrency exchanges (100 Symphony-compatible for live trading)
- **Real-time monitoring** with sub-second execution capabilities via Binance WebSocket
- **Automated TP/SL management** with 3-second position monitoring
- **Comprehensive analytics** with P&L tracking and performance attribution
- **Symphony.io integration** for professional-grade live trading execution

---

**ggbots represents the evolution of autonomous trading - where human expertise meets AI capabilities to create trading agents that truly understand markets, adapt to changing conditions, and execute with the precision of professional trading systems.**

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
| **[database/README.md](database/README.md)** | 567 | Complete schema, migrations, RLS |
| **[frontend/README.md](frontend/README.md)** | 488 | Forge architecture, subscription system |

**Total**: 4,302 lines of module-specific technical documentation

**Note**: ggshot/README.md (384 lines) archived with legacy ggShot filtering system.

---

## 📊 Database Schema

**Auto-generated schema reference** - Updated automatically by `scripts/status_check.py`

**Last Updated**: 2025-11-01 09:00:04 UTC

---

### `bot_telegram_channels` (6 columns)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `config_id` | uuid |  |  |
| `telegram_chat_id` | bigint |  |  |
| `channel_name` | character varying(100) | ✓ |  |
| `enabled` | boolean | ✓ | true |
| `created_at` | timestamp with time zone | ✓ | now() |
| `updated_at` | timestamp with time zone | ✓ | now() |

### `configurations` (10 columns)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `config_id` | uuid |  | uuid_generate_v4() |
| `user_id` | uuid |  |  |
| `config_type` | character varying(50) |  |  |
| `config_name` | character varying(100) | ✓ |  |
| `config_data` | jsonb |  |  |
| `created_at` | timestamp with time zone |  | now() |
| `updated_at` | timestamp with time zone |  | now() |
| `state` | text |  | 'inactive'::text |
| `symphony_agent_id` | character varying(255) | ✓ |  |
| `trading_mode` | character varying(20) | ✓ | 'paper'::character varying |

### `data_points` (11 columns)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `data_point_id` | uuid |  | gen_random_uuid() |
| `source_id` | uuid |  |  |
| `name` | character varying(50) |  |  |
| `display_name` | character varying(100) |  |  |
| `description` | text | ✓ |  |
| `config_values` | ARRAY |  |  |
| `requires_premium` | boolean | ✓ | false |
| `enabled` | boolean | ✓ | true |
| `sort_order` | integer | ✓ | 0 |
| `created_at` | timestamp with time zone | ✓ | now() |
| `updated_at` | timestamp with time zone | ✓ | now() |

### `data_sources` (9 columns)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `source_id` | uuid |  | gen_random_uuid() |
| `name` | character varying(50) |  |  |
| `display_name` | character varying(100) |  |  |
| `description` | text | ✓ |  |
| `enabled` | boolean | ✓ | true |
| `requires_premium` | boolean | ✓ | false |
| `sort_order` | integer | ✓ | 0 |
| `created_at` | timestamp with time zone | ✓ | now() |
| `updated_at` | timestamp with time zone | ✓ | now() |

### `decisions` (13 columns)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `decision_id` | uuid |  | uuid_generate_v4() |
| `user_id` | uuid |  |  |
| `config_id` | uuid | ✓ |  |
| `symbol` | character varying(20) |  |  |
| `action` | character varying(20) |  |  |
| `status` | character varying(20) | ✓ |  |
| `confidence` | numeric |  |  |
| `reasoning` | text | ✓ |  |
| `prompt` | text | ✓ |  |
| `decision_data` | jsonb | ✓ |  |
| `parent_decision_id` | uuid | ✓ |  |
| `created_at` | timestamp with time zone |  | now() |
| `created_by` | text | ✓ | 'decision_engine_v2'::text |

### `live_trades` (5 columns)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `batch_id` | character varying(255) |  |  |
| `config_id` | uuid |  |  |
| `decision_id` | uuid | ✓ |  |
| `created_at` | timestamp without time zone |  | now() |
| `closed_at` | timestamp without time zone | ✓ |  |

### `logs` (6 columns)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `log_id` | integer |  | nextval('logs_log_id_seq'::reg |
| `user_id` | uuid | ✓ |  |
| `module` | character varying(100) | ✓ |  |
| `log_level` | character varying(10) |  |  |
| `message` | text |  |  |
| `timestamp` | timestamp with time zone |  | now() |

### `market_data` (9 columns)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `id` | integer |  | nextval('market_data_id_seq':: |
| `user_id` | uuid |  |  |
| `config_id` | uuid | ✓ |  |
| `symbol` | character varying(20) |  |  |
| `timeframe` | character varying(10) |  |  |
| `data_points` | jsonb | ✓ |  |
| `raw_data` | jsonb |  |  |
| `updated_at` | timestamp with time zone |  | now() |
| `data_source` | uuid | ✓ |  |

### `paper_accounts` (13 columns)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `account_id` | uuid |  | uuid_generate_v4() |
| `user_id` | uuid |  |  |
| `config_id` | uuid |  |  |
| `initial_balance` | numeric |  | 10000.00 |
| `current_balance` | numeric |  | 10000.00 |
| `total_pnl` | numeric |  | 0.00 |
| `open_positions` | integer |  | 0 |
| `total_trades` | integer |  | 0 |
| `win_trades` | integer |  | 0 |
| `loss_trades` | integer |  | 0 |
| `created_at` | timestamp with time zone |  | now() |
| `updated_at` | timestamp with time zone |  | now() |
| `last_reset_at` | timestamp with time zone | ✓ |  |

### `paper_orders` (9 columns)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `order_id` | uuid |  | uuid_generate_v4() |
| `user_id` | uuid |  |  |
| `trade_id` | uuid |  |  |
| `order_type` | character varying(20) |  |  |
| `side` | character varying(10) |  |  |
| `filled_price` | numeric |  |  |
| `size` | numeric |  |  |
| `fees` | numeric |  | 0.00 |
| `filled_at` | timestamp with time zone |  | now() |

### `paper_trades` (22 columns)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `trade_id` | uuid |  | uuid_generate_v4() |
| `user_id` | uuid |  |  |
| `account_id` | uuid |  |  |
| `config_id` | uuid |  |  |
| `decision_id` | uuid | ✓ |  |
| `symbol` | character varying(20) |  |  |
| `side` | character varying(10) |  |  |
| `entry_price` | numeric |  |  |
| `current_price` | numeric | ✓ |  |
| `size_usd` | numeric |  |  |
| `leverage` | integer |  | 1 |
| `unrealized_pnl` | numeric | ✓ |  |
| `realized_pnl` | numeric | ✓ |  |
| `status` | character varying(20) |  | 'open'::character varying |
| `stop_loss` | numeric | ✓ |  |
| `take_profit` | numeric | ✓ |  |
| `confidence_score` | numeric | ✓ |  |
| `opened_at` | timestamp with time zone |  | now() |
| `closed_at` | timestamp with time zone | ✓ |  |
| `margin_used` | numeric | ✓ |  |
| `close_reason` | character varying(50) | ✓ |  |
| `liquidation_price` | numeric | ✓ |  |

### `stripe_webhooks` (11 columns)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `webhook_id` | uuid |  | gen_random_uuid() |
| `stripe_event_id` | character varying(100) |  |  |
| `event_type` | character varying(50) |  |  |
| `stripe_customer_id` | character varying(100) | ✓ |  |
| `stripe_subscription_id` | character varying(100) | ✓ |  |
| `event_data` | jsonb |  |  |
| `processed` | boolean | ✓ | false |
| `processed_at` | timestamp with time zone | ✓ |  |
| `error_message` | text | ✓ |  |
| `retry_count` | integer | ✓ | 0 |
| `created_at` | timestamp with time zone | ✓ | now() |

### `trade_observations` (13 columns)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `observation_id` | uuid |  | gen_random_uuid() |
| `config_id` | uuid |  |  |
| `user_id` | uuid |  |  |
| `trade_id` | uuid |  |  |
| `observation_type` | text |  |  |
| `what_went_well` | text | ✓ |  |
| `what_went_wrong` | text | ✓ |  |
| `predictive_data_points` | jsonb | ✓ |  |
| `decision_review` | text | ✓ |  |
| `trade_pnl` | numeric | ✓ |  |
| `trade_duration_minutes` | integer | ✓ |  |
| `importance` | integer | ✓ | 5 |
| `created_at` | timestamp with time zone | ✓ | now() |

### `user_llm_credentials` (7 columns)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `id` | uuid |  | gen_random_uuid() |
| `user_id` | uuid |  |  |
| `credential_name` | text |  |  |
| `provider` | text |  |  |
| `vault_secret_id` | uuid |  |  |
| `created_at` | timestamp with time zone | ✓ | now() |
| `updated_at` | timestamp with time zone | ✓ | now() |

### `user_profiles` (15 columns)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `user_id` | uuid |  |  |
| `subscription_tier` | USER-DEFINED | ✓ | 'free'::subscription_tier |
| `subscription_status` | USER-DEFINED | ✓ | 'active'::subscription_status |
| `subscription_expires_at` | timestamp with time zone | ✓ |  |
| `stripe_customer_id` | character varying(100) | ✓ |  |
| `stripe_subscription_id` | character varying(100) | ✓ |  |
| `telegram_user_id` | bigint | ✓ |  |
| `telegram_username` | character varying(50) | ✓ |  |
| `telegram_chat_id` | bigint | ✓ |  |
| `monthly_signal_count` | integer | ✓ | 0 |
| `created_at` | timestamp with time zone | ✓ | now() |
| `updated_at` | timestamp with time zone | ✓ | now() |
| `paid_data_points` | ARRAY | ✓ | ARRAY[]::text[] |
| `symphony_vault_id` | uuid | ✓ |  |
| `symphony_smart_account` | character varying(42) | ✓ |  |

---
