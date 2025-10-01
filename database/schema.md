# GGBot Database Schema

**Version**: V1 Private Beta  
**Database**: Supabase PostgreSQL  
**Last Updated**: 2025-01-03  

## Overview

GGBot uses a comprehensive database schema designed for multi-user autonomous trading with subscription-based premium features. All tables implement Row Level Security (RLS) for data isolation.

## Architecture Principles

- **Multi-User Isolation**: RLS policies ensure users only access their own data
- **Premium Feature Gating**: Subscription-based access to advanced features
- **Audit Trail**: Complete decision and trading history for transparency
- **Dynamic Configuration**: Database-driven indicator and data source management
- **Secure Credential Storage**: Encrypted API keys via Supabase Vault

---

## Core Tables

### Authentication & User Management

#### `user_profiles`
Extends Supabase auth.users with business model fields

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `user_id` | UUID | NO | - | Primary key, references auth.users(id) |
| `subscription_tier` | subscription_tier | YES | 'free' | Subscription level (free, ggbase) |
| `subscription_status` | subscription_status | YES | 'active' | Status (active, cancelled, past_due) |
| `subscription_expires_at` | TIMESTAMPTZ | YES | - | Subscription expiration timestamp |
| `stripe_customer_id` | VARCHAR(100) | YES | - | Stripe customer identifier |
| `stripe_subscription_id` | VARCHAR(100) | YES | - | Stripe subscription identifier |
| `telegram_user_id` | BIGINT | YES | - | Telegram user ID for bot integration |
| `telegram_username` | VARCHAR(50) | YES | - | Telegram username |
| `telegram_chat_id` | BIGINT | YES | - | Telegram chat ID for notifications |
| `monthly_signal_count` | INTEGER | YES | 0 | Usage tracking for analytics |
| `paid_data_points` | TEXT[] | YES | ARRAY[]::TEXT[] | Premium data points user has access to |
| `created_at` | TIMESTAMPTZ | YES | NOW() | Account creation timestamp |
| `updated_at` | TIMESTAMPTZ | YES | NOW() | Last profile update timestamp |

**RLS**: Users can only access their own profile  
**Indexes**: subscription_tier+status, stripe_customer_id, telegram_user_id

#### `user_llm_credentials`
Encrypted LLM API key storage via Supabase Vault

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | gen_random_uuid() | Primary key |
| `user_id` | UUID | NO | - | References auth.users(id) |
| `credential_name` | TEXT | NO | - | User-defined name ("GPT-4 Production") |
| `provider` | TEXT | NO | - | LLM provider (openai, deepseek, anthropic) |
| `vault_secret_id` | UUID | NO | - | Supabase Vault secret reference |
| `created_at` | TIMESTAMPTZ | YES | NOW() | Credential creation timestamp |
| `updated_at` | TIMESTAMPTZ | YES | NOW() | Last update timestamp |

**Constraints**: UNIQUE(user_id, credential_name), CHECK provider IN ('openai', 'deepseek', 'anthropic')  
**RLS**: Users can only access their own credentials  
**Indexes**: user_id, (user_id, provider)

---

### Bot Configuration & Management

#### `configurations`
User bot configurations (inherited from existing system)

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `config_id` | UUID | NO | - | Primary key |
| `user_id` | UUID | NO | - | References auth.users(id) |
| `config_type` | VARCHAR(50) | YES | - | Configuration type |
| `config_name` | VARCHAR(100) | YES | - | User-defined configuration name |
| `config_data` | JSONB | YES | - | Configuration parameters |
| `created_at` | TIMESTAMPTZ | YES | NOW() | Configuration creation |
| `updated_at` | TIMESTAMPTZ | YES | NOW() | Last configuration update |

**RLS**: Users can only access their own configurations  
**Indexes**: user_id, config_type

#### `bot_telegram_channels`
Per-bot Telegram signal publishing configuration

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `config_id` | UUID | NO | - | Primary key, references configurations(config_id) |
| `telegram_chat_id` | BIGINT | NO | - | Telegram channel/chat ID for signals |
| `channel_name` | VARCHAR(100) | YES | - | Human-readable channel name |
| `enabled` | BOOLEAN | YES | TRUE | Whether signal publishing is active |
| `created_at` | TIMESTAMPTZ | YES | NOW() | Channel setup timestamp |
| `updated_at` | TIMESTAMPTZ | YES | NOW() | Last channel update |

**RLS**: Users can only access channels for their own configurations  
**Indexes**: enabled, telegram_chat_id

---

### Dynamic Data Management

#### `data_sources`
Available extraction data sources with premium gating

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `source_id` | UUID | NO | gen_random_uuid() | Primary key |
| `name` | VARCHAR(50) | NO | - | Internal source identifier |
| `display_name` | VARCHAR(100) | NO | - | User-friendly display name |
| `description` | TEXT | YES | - | Source description and capabilities |
| `enabled` | BOOLEAN | YES | TRUE | Whether source is currently available |
| `requires_premium` | BOOLEAN | YES | FALSE | Premium subscription requirement |
| `created_at` | TIMESTAMPTZ | YES | NOW() | Source addition timestamp |
| `updated_at` | TIMESTAMPTZ | YES | NOW() | Last source update |

**Constraints**: UNIQUE(name)  
**RLS**: Authenticated users can read enabled sources  
**Indexes**: enabled

**Current Data Sources**:
- 🟢 🆓 Technical Analysis - Core technical indicators
- 🟢 💎 Signals in Group Chats - ggShot premium signals  
- 🔴 💎 Fundamental Analysis - (Future premium feature)
- 🔴 💎 Sentiment & Trends on Social Media - (Future premium)
- 🔴 💎 Influencer/Key Opinion Leaders - (Future premium)
- 🔴 💎 News & Regulatory Actions - (Future premium)
- 🔴 💎 On-Chain Analytics - (Future premium)

#### `data_points`
Specific indicators/signals within each data source with configuration values

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `data_point_id` | UUID | NO | gen_random_uuid() | Primary key |
| `source_id` | UUID | NO | - | References data_sources(source_id) |
| `name` | VARCHAR(50) | NO | - | Internal identifier (RSI, MACD, ggShot) |
| `display_name` | VARCHAR(100) | NO | - | User-friendly display name |
| `description` | TEXT | YES | - | Data point description and use case |
| `config_values` | TEXT[] | NO | - | Values for config_data JSONB (e.g., ["RSI_5m", "RSI_15m"]) |
| `requires_premium` | BOOLEAN | YES | FALSE | Premium subscription requirement |
| `enabled` | BOOLEAN | YES | TRUE | Whether data point is available |
| `sort_order` | INTEGER | YES | 0 | Display ordering preference |
| `created_at` | TIMESTAMPTZ | YES | NOW() | Data point addition timestamp |
| `updated_at` | TIMESTAMPTZ | YES | NOW() | Last data point update |

**Constraints**: UNIQUE(source_id, name)  
**RLS**: All users can read enabled data points  
**Indexes**: (source_id, enabled, sort_order), (requires_premium, enabled)

**Current Data Points**:
- **Technical Analysis (21 total)**:
  - **Momentum (10)**: RSI, MACD, Stochastic, Williams %R, CCI, MFI, ROC, Aroon, Vortex, TRIX
  - **Trend (4)**: ADX, Parabolic SAR, EMA, SMA  
  - **Volatility (5)**: Bollinger Bands, Keltner Channels, Donchian, ATR, BB Width
  - **Volume (2)**: OBV, VWAP
- **Signals in Group Chats (1 total)**:
  - **ggShot**: Premium AI-filtered trading signals (requires premium)

---

### Trading Pipeline

#### `market_data`
Market data and analysis storage (V2 schema with Supabase integration)

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | SERIAL | NO | - | Primary key |
| `user_id` | UUID | NO | - | References auth.users(id) |
| `symbol` | VARCHAR(20) | NO | - | Trading pair symbol (e.g., BTC/USDT) |
| `timeframe` | VARCHAR(10) | NO | - | Chart timeframe (5m, 15m, 1h, 4h, 1D, 1W) |
| `config_id` | UUID | YES | - | Associated configuration |
| `data_source` | UUID | YES | - | References data_sources(source_id) |
| `data_points` | JSONB | YES | - | Processed analysis results from preprocessors |
| `raw_data` | JSONB | NO | - | Raw OHLCV candle data |
| `updated_at` | TIMESTAMPTZ | YES | NOW() | Last data update |

**RLS**: Users can only access their own market data  
**Indexes**: user_id, (user_id, symbol, timeframe, updated_at), data_source

**Multi-Timeframe Storage Pattern (V2.1 - 2025-09-07)**:
- ✅ **Separate Rows Per Timeframe** - Each timeframe stored as individual record
- ✅ **Config-Based Grouping** - All timeframes for a symbol linked via `config_id`
- ✅ **Decision Engine Queries** - `SELECT * WHERE config_id = ? AND symbol = ?` returns all timeframes
- ✅ **Rich Preprocessor Data** - V2 system stores sophisticated analysis in `data_points` JSONB
- ✅ **Timeframe Organization** - Decision engine consolidates by timeframe for LLM context

**Schema Changes (V2)**:
- ✅ **Added `data_source`** - UUID foreign key to data_sources table  
- ✅ **Renamed `indicators` → `data_points`** - More generic for all analysis types
- ✅ **Removed `data_type`** - Redundant with data_source UUID reference
- ✅ **Removed legacy `source` field** - Cleaned up unnecessary column
- ✅ **Enhanced for V2 system** - Supports 21 advanced technical analysis preprocessors with dual storage
- ✅ **Multi-Timeframe Support** - Orchestrator stores 7 rows per symbol (one per timeframe)

#### `decisions`
Unified decision audit trail (replaces strategy_runs + ggshot_filter)

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `decision_id` | UUID | NO | gen_random_uuid() | Primary key |
| `user_id` | UUID | NO | - | References auth.users(id) |
| `config_id` | UUID | YES | - | Associated configuration (NULL for ggShot) |
| `symbol` | VARCHAR(20) | NO | - | Trading pair symbol |
| `action` | VARCHAR(20) | NO | - | Decision action (enter, wait, exit) |
| `status` | VARCHAR(20) | YES | - | Decision status (approved, rejected) |
| `confidence` | DECIMAL(4,3) | NO | - | AI confidence score (0.000-1.000) |
| `reasoning` | TEXT | YES | - | LLM reasoning explanation |
| `prompt` | TEXT | YES | - | Complete LLM prompt used |
| `market_data` | JSONB | YES | - | Raw indicator values used |
| `decision_data` | JSONB | YES | - | Decision-specific data |
| `parent_decision_id` | UUID | YES | - | Links related decisions |
| `created_at` | TIMESTAMPTZ | NO | NOW() | Decision timestamp |

**Constraints**: CHECK action IN ('enter', 'wait', 'exit'), CHECK status IN ('approved', 'rejected'), CHECK confidence BETWEEN 0.000 AND 1.000  
**RLS**: Users can only access their own decisions  
**Indexes**: (user_id, config_id), (action, status), (symbol, created_at DESC), parent_decision_id, confidence DESC

---

### Paper Trading Engine

#### `paper_accounts`
Isolated paper trading accounts per configuration

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `account_id` | UUID | NO | - | Primary key |
| `user_id` | UUID | NO | - | References auth.users(id) |
| `config_id` | UUID | NO | - | References configurations(config_id) UNIQUE |
| `initial_balance` | DECIMAL(20,8) | NO | 10000.0 | Starting balance |
| `current_balance` | DECIMAL(20,8) | NO | 10000.0 | Current account balance |
| `total_pnl` | DECIMAL(20,8) | NO | 0.0 | Total profit/loss |
| `open_positions` | INTEGER | NO | 0 | Number of open positions |
| `total_trades` | INTEGER | NO | 0 | Total number of trades |
| `win_trades` | INTEGER | NO | 0 | Number of winning trades |
| `loss_trades` | INTEGER | NO | 0 | Number of losing trades |
| `created_at` | TIMESTAMPTZ | YES | NOW() | Account creation |
| `updated_at` | TIMESTAMPTZ | YES | NOW() | Last balance update |

**RLS**: Users can only access their own accounts  
**Indexes**: user_id, config_id

#### `paper_trades`
Paper trading execution records

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `trade_id` | UUID | NO | - | Primary key |
| `user_id` | UUID | NO | - | References auth.users(id) |
| `account_id` | UUID | NO | - | References paper_accounts(account_id) |
| `config_id` | UUID | NO | - | References configurations(config_id) |
| `decision_id` | UUID | YES | - | References decisions(decision_id) |
| `symbol` | VARCHAR(20) | NO | - | Trading pair |
| `side` | VARCHAR(10) | NO | - | Trade direction (buy, sell) |
| `entry_price` | DECIMAL(20,8) | NO | - | Entry execution price |
| `current_price` | DECIMAL(20,8) | YES | - | Current market price |
| `size_usd` | DECIMAL(20,8) | NO | - | Position size in USD |
| `leverage` | INTEGER | NO | 1 | Leverage multiplier |
| `unrealized_pnl` | DECIMAL(20,8) | YES | - | Current unrealized P&L |
| `realized_pnl` | DECIMAL(20,8) | YES | - | Realized P&L when closed |
| `status` | VARCHAR(20) | NO | 'open' | Trade status (open, closed) |
| `stop_loss` | DECIMAL(20,8) | YES | - | Stop loss price |
| `take_profit` | DECIMAL(20,8) | YES | - | Take profit price |
| `confidence_score` | DECIMAL(4,3) | YES | - | AI confidence for trade |
| `opened_at` | TIMESTAMPTZ | NO | NOW() | Trade opening timestamp |
| `closed_at` | TIMESTAMPTZ | YES | - | Trade closing timestamp |

**RLS**: Users can only access their own trades  
**Indexes**: user_id, config_id, account_id, symbol, created_at

#### `paper_orders`
Paper trading order execution records

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `order_id` | UUID | NO | - | Primary key |
| `user_id` | UUID | NO | - | References auth.users(id) |
| `trade_id` | UUID | NO | - | References paper_trades(trade_id) |
| `order_type` | VARCHAR(20) | NO | - | Order type (market, limit, stop) |
| `side` | VARCHAR(10) | NO | - | Order side (buy, sell) |
| `filled_price` | DECIMAL(20,8) | NO | - | Executed fill price |
| `size` | DECIMAL(20,8) | NO | - | Order size |
| `fees` | DECIMAL(20,8) | NO | 0.0 | Trading fees |
| `filled_at` | TIMESTAMPTZ | NO | NOW() | Order fill timestamp |

**RLS**: Users can only access their own orders  
**Indexes**: user_id, config_id, account_id, symbol, status

#### `paper_trading_summary`
Performance analytics and summaries

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `summary_id` | UUID | NO | - | Primary key |
| `user_id` | UUID | NO | - | References auth.users(id) |
| `config_id` | UUID | NO | - | References configurations(config_id) |
| `account_id` | UUID | NO | - | References paper_accounts(account_id) |
| `period_start` | TIMESTAMPTZ | NO | - | Summary period start |
| `period_end` | TIMESTAMPTZ | NO | - | Summary period end |
| `total_pnl` | DECIMAL(20,8) | NO | - | Total profit/loss |
| `total_trades` | INTEGER | NO | - | Number of trades |
| `win_rate` | DECIMAL(5,4) | YES | - | Win percentage |
| `created_at` | TIMESTAMPTZ | YES | NOW() | Summary generation |

**RLS**: Users can only access their own summaries  
**Indexes**: user_id, config_id, account_id

---

### Business Model & Payments

#### `stripe_webhooks`
Stripe event tracking for reliable subscription management

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `webhook_id` | UUID | NO | gen_random_uuid() | Primary key |
| `stripe_event_id` | VARCHAR(100) | NO | - | Stripe event ID (for idempotency) |
| `event_type` | VARCHAR(50) | NO | - | Stripe event type |
| `stripe_customer_id` | VARCHAR(100) | YES | - | Links to user_profiles |
| `stripe_subscription_id` | VARCHAR(100) | YES | - | Links to user_profiles |
| `event_data` | JSONB | NO | - | Full Stripe event payload |
| `processed` | BOOLEAN | YES | FALSE | Whether event was processed |
| `processed_at` | TIMESTAMPTZ | YES | - | Processing timestamp |
| `error_message` | TEXT | YES | - | Any processing errors |
| `retry_count` | INTEGER | YES | 0 | Processing retry attempts |
| `created_at` | TIMESTAMPTZ | YES | NOW() | Event receipt timestamp |

**Constraints**: UNIQUE(stripe_event_id)  
**RLS**: Service role access only  
**Indexes**: stripe_event_id, stripe_customer_id, stripe_subscription_id, (processed, created_at), event_type, (retry_count, processed) WHERE processed = FALSE

---

### System & Logging

#### `logs`
System logging (inherited from existing system)

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `log_id` | INTEGER | NO | - | Primary key (sequence) |
| `user_id` | UUID | YES | - | Associated user (optional) |
| `module` | VARCHAR(50) | YES | - | System module that generated log |
| `log_level` | VARCHAR(10) | NO | - | Log level (INFO, ERROR, etc.) |
| `message` | TEXT | NO | - | Log message |
| `timestamp` | TIMESTAMPTZ | NO | NOW() | Log entry timestamp |

**RLS**: Users can only access their own logs  
**Indexes**: user_id, level, created_at

---

## Custom Types

### Enums

```sql
-- Subscription management
CREATE TYPE subscription_tier AS ENUM ('free', 'ggbase');
CREATE TYPE subscription_status AS ENUM ('active', 'cancelled', 'past_due');
```

---

## Security Model

### Row Level Security (RLS)

All user-related tables implement RLS policies using `auth.uid()` for automatic multi-user isolation:

- **Direct user tables**: `WHERE auth.uid() = user_id`  
- **Configuration-based**: `WHERE config_id IN (SELECT config_id FROM configurations WHERE user_id = auth.uid())`
- **Admin tables**: Service role access only

### API Key Encryption

User LLM credentials are encrypted using Supabase Vault:
- API keys never stored in plaintext
- Vault provides automatic encryption/decryption
- Access controlled through RLS policies

---

## Migration Notes

### Breaking Changes from Previous Schema

1. **strategy_runs** → **decisions** (unified audit trail)
2. **ggshot_filter** → **decisions** (consolidated)
3. **indicators** → **data_points** (with config_values for JSONB mapping)
4. **user_indicator_access** → **user_profiles.paid_data_points** (simplified premium gating)
5. Added user_id to all existing tables for multi-user support
6. Enhanced paper trading schema with detailed tracking
7. Optimized RLS policies for performance

### Data Migration Required

- Existing configurations need user_id assignment
- strategy_runs data should be migrated to decisions table
- market_data needs config_id population

---

## Performance Considerations

### Indexing Strategy

- **User isolation**: All user-based queries indexed on user_id first
- **Time-series data**: Composite indexes with created_at/updated_at
- **Premium checks**: Indexes on requires_premium + enabled
- **Foreign key performance**: All FK relationships indexed

### Scaling Considerations

- Partition large tables (market_data, decisions) by date when needed
- Consider read replicas for analytics queries
- Archive old webhook events and logs periodically

---

**Schema Version**: 2.0.0  
**Generated**: 2025-01-04  
**Total Tables**: 13  
**Total Indexes**: 40+  
**RLS Enabled**: All user tables (performance optimized)  

REAL, LIVE, ACTUAL SUPABASE SCHEMA, THIS IS THE SOURCE OF FUCKING TRUTH:

-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.bot_telegram_channels (
  config_id uuid NOT NULL,
  telegram_chat_id bigint NOT NULL,
  channel_name character varying,
  enabled boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT bot_telegram_channels_pkey PRIMARY KEY (config_id),
  CONSTRAINT bot_telegram_channels_config_id_fkey FOREIGN KEY (config_id) REFERENCES public.configurations(config_id)
);
CREATE TABLE public.configurations (
  config_id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,
  config_type character varying NOT NULL,
  config_name character varying,
  config_data jsonb NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  state text NOT NULL DEFAULT 'inactive'::text CHECK (state = ANY (ARRAY['active'::text, 'inactive'::text])),
  CONSTRAINT configurations_pkey PRIMARY KEY (config_id),
  CONSTRAINT configurations_user_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.data_points (
  data_point_id uuid NOT NULL DEFAULT gen_random_uuid(),
  source_id uuid NOT NULL,
  name character varying NOT NULL,
  display_name character varying NOT NULL,
  description text,
  config_values ARRAY NOT NULL,
  requires_premium boolean DEFAULT false,
  enabled boolean DEFAULT true,
  sort_order integer DEFAULT 0,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT data_points_pkey PRIMARY KEY (data_point_id),
  CONSTRAINT data_points_source_id_fkey FOREIGN KEY (source_id) REFERENCES public.data_sources(source_id)
);
CREATE TABLE public.data_sources (
  source_id uuid NOT NULL DEFAULT gen_random_uuid(),
  name character varying NOT NULL UNIQUE,
  display_name character varying NOT NULL,
  description text,
  enabled boolean DEFAULT true,
  requires_premium boolean DEFAULT false,
  sort_order integer DEFAULT 0,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT data_sources_pkey PRIMARY KEY (source_id)
);
CREATE TABLE public.decisions (
  decision_id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,
  config_id uuid,
  symbol character varying NOT NULL,
  action character varying NOT NULL,
  status character varying,
  confidence numeric NOT NULL CHECK (confidence >= 0.000 AND confidence <= 1.000),
  reasoning text,
  prompt text,
  decision_data jsonb,
  parent_decision_id uuid,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT decisions_pkey PRIMARY KEY (decision_id),
  CONSTRAINT decisions_user_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id),
  CONSTRAINT decisions_config_fkey FOREIGN KEY (config_id) REFERENCES public.configurations(config_id),
  CONSTRAINT decisions_parent_fkey FOREIGN KEY (parent_decision_id) REFERENCES public.decisions(decision_id)
);
CREATE TABLE public.logs (
  log_id integer NOT NULL DEFAULT nextval('logs_log_id_seq'::regclass),
  user_id uuid,
  module character varying,
  log_level character varying NOT NULL,
  message text NOT NULL,
  timestamp timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT logs_pkey PRIMARY KEY (log_id),
  CONSTRAINT logs_user_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.market_data (
  id integer NOT NULL DEFAULT nextval('market_data_id_seq'::regclass),
  user_id uuid NOT NULL,
  config_id uuid,
  symbol character varying NOT NULL,
  timeframe character varying NOT NULL,
  data_points jsonb,
  raw_data jsonb NOT NULL,
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  data_source uuid,
  CONSTRAINT market_data_pkey PRIMARY KEY (id),
  CONSTRAINT market_data_user_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id),
  CONSTRAINT market_data_config_fkey FOREIGN KEY (config_id) REFERENCES public.configurations(config_id)
);
CREATE TABLE public.paper_accounts (
  account_id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,
  config_id uuid NOT NULL UNIQUE,
  initial_balance numeric NOT NULL DEFAULT 10000.00,
  current_balance numeric NOT NULL DEFAULT 10000.00,
  total_pnl numeric NOT NULL DEFAULT 0.00,
  open_positions integer NOT NULL DEFAULT 0,
  total_trades integer NOT NULL DEFAULT 0,
  win_trades integer NOT NULL DEFAULT 0,
  loss_trades integer NOT NULL DEFAULT 0,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT paper_accounts_pkey PRIMARY KEY (account_id),
  CONSTRAINT paper_accounts_user_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id),
  CONSTRAINT paper_accounts_config_fkey FOREIGN KEY (config_id) REFERENCES public.configurations(config_id)
);
CREATE TABLE public.paper_orders (
  order_id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,
  trade_id uuid NOT NULL,
  order_type character varying NOT NULL,
  side character varying NOT NULL,
  filled_price numeric NOT NULL,
  size numeric NOT NULL,
  fees numeric NOT NULL DEFAULT 0.00,
  filled_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT paper_orders_pkey PRIMARY KEY (order_id),
  CONSTRAINT paper_orders_user_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id),
  CONSTRAINT paper_orders_trade_fkey FOREIGN KEY (trade_id) REFERENCES public.paper_trades(trade_id)
);
CREATE TABLE public.paper_trades (
  trade_id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,
  account_id uuid NOT NULL,
  config_id uuid NOT NULL,
  decision_id uuid,
  symbol character varying NOT NULL,
  side character varying NOT NULL,
  entry_price numeric NOT NULL,
  current_price numeric,
  size_usd numeric NOT NULL,
  leverage integer NOT NULL DEFAULT 1,
  unrealized_pnl numeric,
  realized_pnl numeric,
  status character varying NOT NULL DEFAULT 'open'::character varying,
  stop_loss numeric,
  take_profit numeric,
  confidence_score numeric,
  opened_at timestamp with time zone NOT NULL DEFAULT now(),
  closed_at timestamp with time zone,
  margin_used numeric,
  close_reason character varying CHECK ((close_reason::text = ANY (ARRAY['take_profit'::character varying, 'stop_loss'::character varying, 'manual'::character varying, 'liquidation'::character varying, 'system_reset_v2'::character varying, 'position_management'::character varying]::text[])) OR close_reason IS NULL),
  CONSTRAINT paper_trades_pkey PRIMARY KEY (trade_id),
  CONSTRAINT paper_trades_user_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id),
  CONSTRAINT paper_trades_account_fkey FOREIGN KEY (account_id) REFERENCES public.paper_accounts(account_id),
  CONSTRAINT paper_trades_config_fkey FOREIGN KEY (config_id) REFERENCES public.configurations(config_id),
  CONSTRAINT paper_trades_decision_fkey FOREIGN KEY (decision_id) REFERENCES public.decisions(decision_id)
);
CREATE TABLE public.stripe_webhooks (
  webhook_id uuid NOT NULL DEFAULT gen_random_uuid(),
  stripe_event_id character varying NOT NULL UNIQUE,
  event_type character varying NOT NULL,
  stripe_customer_id character varying,
  stripe_subscription_id character varying,
  event_data jsonb NOT NULL,
  processed boolean DEFAULT false,
  processed_at timestamp with time zone,
  error_message text,
  retry_count integer DEFAULT 0,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT stripe_webhooks_pkey PRIMARY KEY (webhook_id)
);
CREATE TABLE public.user_llm_credentials (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  credential_name text NOT NULL,
  provider text NOT NULL CHECK (provider = ANY (ARRAY['openai'::text, 'deepseek'::text, 'anthropic'::text, 'xai'::text])),
  vault_secret_id uuid NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT user_llm_credentials_pkey PRIMARY KEY (id),
  CONSTRAINT user_llm_credentials_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.user_profiles (
  user_id uuid NOT NULL,
  subscription_tier USER-DEFINED DEFAULT 'free'::subscription_tier,
  subscription_status USER-DEFINED DEFAULT 'active'::subscription_status,
  subscription_expires_at timestamp with time zone,
  stripe_customer_id character varying,
  stripe_subscription_id character varying,
  telegram_user_id bigint,
  telegram_username character varying,
  telegram_chat_id bigint,
  monthly_signal_count integer DEFAULT 0,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  paid_data_points ARRAY DEFAULT ARRAY[]::text[],
  CONSTRAINT user_profiles_pkey PRIMARY KEY (user_id),
  CONSTRAINT user_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);