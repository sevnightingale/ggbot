# ggbots Platform Database Structure

This directory contains database migration scripts for the ggbots platform. The database is designed to support a multi-user trading agent platform where users can configure and deploy trading agents for various cryptocurrency pairs across multiple exchanges.

## Multi-User Architecture

The ggbots platform is designed to support multiple users, each able to create and manage multiple autonomous trading bots. The database schema supports this with the following approach:

- **User Management**: User accounts will be managed through the custom Next.js frontend, with UUIDs stored in the `user_id` field of our tables
- **Configuration Flow**: Trading agent configurations are created in the frontend interface and sent to the backend via API, where they are stored in the `configurations` table
- **Multiple Agent Support**: Users can create multiple trading agents (bots) by grouping configurations using the `config_name` field
- **Authentication**: Authentication system will be implemented to handle user identification and secure API access

## Migration Scripts

- `0001_create_tables.sql`: Initial schema creation (sessions, trades, logs)
- `0002_add_user_id.sql`: Adds multi-user support with users table and foreign key constraints
- `0003_create_market_data.sql`: Creates the market_data table for storing price and indicator data
- `0004_update_schema_for_platform.sql`: Updates schema to support platform architecture (configurations table, additional fields)
- `0005_additional_improvements.sql`: Adds data_type column to market_data, config_name to configurations, and config_id to trades
- `0006_update_configuration_constraint.sql`: Updates unique constraint on configurations table to support multiple named configurations
- `0007_update_market_data_schema.sql`: Updates market_data schema for better data organization
- `0008_update_market_data_constraint.sql`: Changes unique constraint to allow historical data storage
- `0009_add_account_monitoring.sql`: Adds account_states table for exchange account monitoring
- `0010_add_constraints_and_indexes.sql`: Adds position reconciliation and performance indexes
- `0011_add_data_integrity_constraints.sql`: Adds comprehensive data integrity constraints and reconciliation logging
- `0012_universal_trade_lifecycle.sql`: **MAJOR MIGRATION** - Transforms phantom-trade system to universal position-based trade lifecycle system
- `0013_enhanced_trade_lifecycle.sql`: Adds config_id integration, TP/SL tracking, strategy metadata, and backward compatibility
- `0014_create_ggshot_filter_table.sql`: Creates ggshot_filter table for logging all ggShot signal filter decisions
- `2025-06-30_add_config_id_to_market_data.sql`: Adds config_id column to market_data table for configuration-driven extraction system
- **2025-08-03_config_instances.sql**: ⭐ Creates config_instances table for mapping configurations to Hummingbot instances (Phase 1 paper trading)

## Database Schema

### users
Stores user information for multi-user support with demo access capabilities.

| Column      | Type            | Description                            |
|-------------|-----------------|----------------------------------------|
| user_id     | UUID            | Primary Key                            |
| username    | VARCHAR         | User's username (nullable for email-only signups) |
| email       | VARCHAR         | User's email address (nullable, unique) |
| created_at  | TIMESTAMP       | Account creation timestamp             |
| last_login  | TIMESTAMP       | Last login timestamp                   |
| demo_access | BOOLEAN         | Demo access flag (default: true)      |

**Indexes:**
- Primary Key on `user_id`
- Unique constraint on `email` (users_email_unique)
- Index on `email` for fast lookups (idx_users_email)

**Constraints:**
- `check_username_or_email`: Ensures either username OR email is provided (supports email-only demo signups)

**Demo Integration (2025-08-03):**
- Added support for email-only user registration for hackathon demo
- Users can sign up with just email address (no password required)
- Default user `00000000-0000-0000-0000-000000000001` updated with demo access

### sessions
Stores session information for TradingView access and other authenticated services.

| Column     | Type            | Description                            |
|------------|-----------------|----------------------------------------|
| session_id | UUID            | Primary Key                            |
| user_id    | UUID            | Foreign Key to users table             |
| cookie_data| JSONB           | Session cookies and authentication data|
| created_at | TIMESTAMP       | Session creation timestamp             |
| expires_at | TIMESTAMP       | Session expiration timestamp           |

**Indexes:**
- Primary Key on `session_id`
- Index on `expires_at` for session cleanup
- Foreign Key constraint on `user_id` referencing users table

### configurations
Stores user-specific configurations for each module of the platform.

| Column      | Type            | Description                            |
|-------------|-----------------|----------------------------------------|
| config_id   | UUID            | Primary Key                            |
| user_id     | UUID            | Foreign Key to users table             |
| config_type | VARCHAR         | Type of configuration (e.g., 'extraction', 'decision') |
| config_name | VARCHAR         | Optional name for the configuration    |
| config_data | JSONB           | Configuration data in JSON format      |
| created_at  | TIMESTAMP       | Creation timestamp                     |
| updated_at  | TIMESTAMP       | Last update timestamp                  |

**Indexes:**
- Primary Key on `config_id`
- Unique constraint on `(user_id, config_type)`

### config_instances ⭐ NEW
Maps configurations to Hummingbot instances for paper trading isolation. Each configuration gets its own dedicated paper trading account.

| Column            | Type            | Description                            |
|-------------------|-----------------|----------------------------------------|
| config_id         | UUID            | Primary Key, Foreign Key to configurations |
| instance_name     | VARCHAR         | Unique Hummingbot instance identifier  |
| hummingbot_account| VARCHAR         | Paper trading account name             |
| created_at        | TIMESTAMP       | Instance creation timestamp            |
| status            | VARCHAR         | Instance status (active, inactive)    |
| paper_balance_usd | DECIMAL         | Initial paper trading balance          |

**Indexes:**
- Primary Key on `config_id`
- Unique constraint on `instance_name`

**Example Entries:**
```sql
-- ggShot flagship configuration
config_id: e249bb49-0455-4596-9657-09bf9e14ca14
instance_name: ggbot-00000000-e249bb49
hummingbot_account: ggshot_paper_account
status: active
paper_balance_usd: 10000.00

-- User-created RSI strategy
config_id: a1b2c3d4-e5f6-7890-abcd-ef1234567890  
instance_name: ggbot-00000000-a1b2c3d4
hummingbot_account: paper_rsi_momentum_a1b2c3d4
status: active
paper_balance_usd: 10000.00
```

**Usage:**
- **Instance Mapping**: Each config_id maps to exactly one Hummingbot instance
- **Account Isolation**: Paper trading accounts are isolated per configuration
- **Naming Convention**: `ggbot-{user_id[:8]}-{config_id[:8]}`
- **Account Naming**: `paper_{strategy_type}_{config_id[:8]}` or custom names
- Index on `(user_id, config_type)` for efficient lookups
- Foreign Key constraint on `user_id` referencing users table

### config_instances
**NEW TABLE (2025-08-03)**: Maps configurations to Hummingbot instances for paper trading isolation.

| Column            | Type            | Description                            |
|-------------------|-----------------|----------------------------------------|
| config_id         | UUID            | Foreign Key to configurations table    |
| instance_name     | VARCHAR         | Hummingbot instance name (ggbot-user123-conf456) |
| hummingbot_account| VARCHAR         | Hummingbot account name for paper trading |
| created_at        | TIMESTAMP       | Instance creation timestamp            |
| status            | VARCHAR         | Instance status ('active', 'disabled') |
| paper_balance_usd | DECIMAL(10,2)   | Paper trading balance (default $10,000) |

**Purpose:**
- Maps each config_id to a persistent Hummingbot instance
- Enables isolated paper trading accounts per configuration
- Prevents random instance creation per trade
- Supports multi-user paper trading with account isolation

**Indexes:**
- Unique constraint on `config_id` (one instance per config)
- Unique constraint on `instance_name` (prevent name conflicts)
- Foreign Key constraint on `config_id` referencing configurations table

### trades
**ENHANCED SCHEMA (Migration 0012 + 0013)**: Position-based trade tracking with decision module compatibility.

| Column             | Type            | Description                            |
|--------------------|-----------------|----------------------------------------|
| trade_id           | UUID            | Primary Key                            |
| user_id            | UUID            | Foreign Key to users table             |
| account_id         | VARCHAR         | Account identifier (default: 'main')   |
| exchange           | VARCHAR         | Exchange name (e.g., 'bitmex')         |
| symbol             | VARCHAR         | Trading pair (e.g., 'BTC/USD')         |
| side               | VARCHAR         | Position side: 'long'/'short' (NULL for net exchanges like BitMEX) |
| trade_status       | VARCHAR         | Trade status: 'open' or 'closed'       |
| size_contracts     | DECIMAL(20,8)   | Position size in contracts (single source of truth) |
| entry_price        | DECIMAL(20,8)   | VWAP entry price (calculated from trade_orders) |
| mark_price         | DECIMAL(20,8)   | Current market price (updated frequently) |
| unrealized_pnl     | DECIMAL(20,8)   | Current unrealized P&L                 |
| realized_pnl       | DECIMAL(20,8)   | Final P&L when closed                  |
| total_fees         | DECIMAL(20,8)   | Sum of fees from trade_orders          |
| opened_at          | TIMESTAMP       | Trade open timestamp                   |
| closed_at          | TIMESTAMP       | Trade close timestamp                  |
| last_updated       | TIMESTAMP       | Last position update timestamp         |
| config_id          | UUID            | Foreign Key to configurations table (Migration 0013) |
| leverage           | INTEGER         | Leverage used for this trade (Migration 0013) |
| collateral_amount  | DECIMAL(20,8)   | Collateral amount in base currency (Migration 0013) |
| stop_loss          | DECIMAL(20,8)   | Stop loss price level (Migration 0013) |
| take_profit        | DECIMAL(20,8)   | Take profit price level (Migration 0013) |
| confidence_score   | NUMERIC(3,2)    | Decision confidence score 0.0-1.0 (Migration 0013) |
| reasoning_log      | TEXT            | Decision reasoning for audit trail (Migration 0013) |

**Key Design Principles:**
- **Position-driven lifecycle**: Exchange position changes drive trade state (open/update/close)
- **Universal exchange support**: Configurable position keys (net vs hedge mode)
- **Order precision**: Detailed order tracking in separate `trade_orders` table
- **Single source of truth**: `size_contracts` is authoritative position size

**Indexes:**
- Primary Key on `trade_id`
- Index on `(user_id, exchange, trade_status)` for active trades (partial index WHERE trade_status = 'open')
- Index on `(user_id, exchange, symbol, side, trade_status)` for position key lookups
- Unique constraint on `(user_id, account_id, exchange, symbol, side)` for position uniqueness
- Foreign Key constraint on `user_id` referencing users table

**Position Key Strategy:**
- **Net exchanges (BitMEX)**: key = `(user_id, account_id, exchange, symbol)` (side = NULL)
- **Hedge exchanges (Binance)**: key = `(user_id, account_id, exchange, symbol, side)`

### trade_orders
**ENHANCED TABLE (Migration 0012 + 0013)**: Order-level details with TP/SL tracking.

| Column             | Type            | Description                            |
|--------------------|-----------------|----------------------------------------|
| id                 | SERIAL          | Primary Key                            |
| trade_id           | UUID            | Foreign Key to trades table            |
| exchange           | VARCHAR         | Exchange name for better joins         |
| symbol             | VARCHAR         | Trading pair for better joins          |
| exchange_order_id  | VARCHAR         | Exchange-assigned order ID             |
| client_order_id    | VARCHAR         | Our trade_id when exchange supports it |
| order_type         | VARCHAR         | Order type: 'market', 'limit', 'stop' |
| side               | VARCHAR         | Order side: 'buy', 'sell'              |
| price              | DECIMAL(20,8)   | Order price                            |
| size               | DECIMAL(20,8)   | Order size                             |
| filled_size        | DECIMAL(20,8)   | Actually filled size                   |
| fee                | DECIMAL(20,8)   | Trading fee                            |
| fee_currency       | VARCHAR         | Fee currency                           |
| status             | VARCHAR         | Order status: 'open', 'filled', 'canceled' |
| filled_at          | TIMESTAMP       | Fill timestamp                         |
| created_at         | TIMESTAMP       | Order creation timestamp               |
| is_risk_order      | BOOLEAN         | True if this is a TP/SL order (Migration 0013) |
| risk_type          | VARCHAR(10)     | 'TP' or 'SL' for risk orders (Migration 0013) |

**Purpose:**
- Enables precise VWAP calculation from multiple fills
- Tracks fees for accurate P&L computation
- Supports partial fill scenarios and order tracking
- Maintains order history for audit and analysis

**Indexes:**
- Primary Key on `id`
- Index on `trade_id` for joining with trades
- Index on `(exchange, exchange_order_id)` for order lookups
- Unique constraint on `(exchange, exchange_order_id)` to prevent duplicates
- Foreign Key constraint on `trade_id` referencing trades table

### strategy_runs
**NEW TABLE (Migration 0013)**: Tracks decision context and strategy metadata for trades.

| Column                 | Type            | Description                            |
|------------------------|-----------------|----------------------------------------|
| strategy_run_id        | UUID            | Primary Key                            |
| trade_id               | UUID            | Foreign Key to trades table            |
| config_id              | UUID            | Foreign Key to configurations table    |
| decision_id            | UUID            | Link to decision that triggered this   |
| leverage               | INTEGER         | Leverage setting for this strategy run |
| confidence_score       | NUMERIC(3,2)    | Strategy confidence score (0.0-1.0)    |
| reasoning_log          | TEXT            | Detailed reasoning for the decision    |
| decision_data          | JSONB           | Full decision context and parameters   |
| scenario               | VARCHAR(50)     | 'TRADE_ENTRY', 'TRADE_MANAGEMENT', 'TRADE_EXIT' |
| parent_strategy_run_id | UUID            | Links management decisions to original entry |
| created_at             | TIMESTAMP       | Strategy run creation timestamp        |

**Purpose:**
- Captures the "why" behind trading decisions
- Enables decision audit trails and performance analysis
- Provides context for trade management scenarios
- Links related decisions (entry → management → exit)

**Indexes:**
- Primary Key on `strategy_run_id`
- Index on `trade_id` for trade lookups
- Index on `config_id` for configuration analysis
- Index on `scenario` for decision type queries
- Index on `parent_strategy_run_id` for decision chains
- Foreign Key constraints on `trade_id` and `config_id`

### instrument_metadata
**NEW TABLE (Migration 0012)**: Exchange-specific contract specifications.

| Column                | Type            | Description                            |
|-----------------------|-----------------|----------------------------------------|
| id                    | SERIAL          | Primary Key                            |
| exchange              | VARCHAR         | Exchange name                          |
| symbol                | VARCHAR         | Trading pair symbol                    |
| contract_value        | DECIMAL(20,8)   | Contract value (1.0 for BitMEX BTC/USD) |
| contract_currency     | VARCHAR         | Contract currency ('USD', 'BTC', etc.) |
| tick_size             | DECIMAL(20,8)   | Minimum price increment                |
| lot_size              | DECIMAL(20,8)   | Minimum size increment                 |
| supports_hedge_mode   | BOOLEAN         | Whether exchange supports hedge mode   |
| default_position_mode | VARCHAR         | Default mode: 'net' or 'hedge'        |
| active                | BOOLEAN         | Whether instrument is active           |
| updated_at            | TIMESTAMP       | Last update timestamp                  |

**Purpose:**
- Normalizes contract specifications across exchanges
- Enables universal position calculations
- Supports exchange adapter configuration
- Pre-populated with BitMEX BTC/USD metadata for testing

**Indexes:**
- Primary Key on `id`
- Index on `(exchange, symbol)` for lookups
- Unique constraint on `(exchange, symbol)` to prevent duplicates

### market_data
Stores market data including indicators and price data for different pairs and timeframes.

| Column     | Type            | Description                            |
|------------|-----------------|----------------------------------------|
| id         | SERIAL          | Primary Key                            |
| user_id    | UUID            | Foreign Key to users table             |
| config_id  | UUID            | Foreign Key to configurations table (nullable) |
| source     | VARCHAR         | Data source (e.g., 'tradingview', 'yfinance', 'crypto_indicators_mcp') |
| symbol     | VARCHAR         | Trading pair symbol                    |
| timeframe  | VARCHAR         | Timeframe (e.g., '15m', '1h', '4h')    |
| data_type  | VARCHAR         | Type of data (e.g., 'price_data', 'report', 'sentiment', 'indicator_analysis') |
| indicators | JSONB           | Technical indicators in JSON format    |
| raw_data   | JSONB           | Raw price/chart data in JSON format    |
| updated_at | TIMESTAMP       | Timestamp of the data point            |

**IMPORTANT FIELD NAMING CLARIFICATION**:
- The `indicators` field contains the actual raw indicator data from sources like MCP
- The `raw_data` field is misleadingly named - it contains metadata like LLM interpretation and configuration, NOT the raw indicator values
- For crypto_indicators_mcp source: 
  - `indicators`: Contains `{"configured_indicators": [...], "results": {actual MCP indicator data}}`
  - `raw_data`: Contains `{"interpretation": LLM analysis, "llm_model": model name, "config": {...}}`
- The decision engine accesses raw indicator data via `row['raw_data']['indicators']` due to internal data copying

**Indexes:**
- Primary Key on `id`
- Unique constraint on `(user_id, symbol, timeframe, updated_at)` to allow multiple data points per timeframe
- Index on `(user_id, symbol, timeframe, updated_at)` for efficient retrieval
- Index on `(config_id, symbol)` for config-based data retrieval (new extraction pattern)
- Foreign Key constraint on `user_id` referencing users table
- Foreign Key constraint on `config_id` referencing configurations table

**Important Note**: Migration `0008_update_market_data_constraint.sql` changes the unique constraint to allow multiple entries per user-symbol-timeframe combination with different timestamps. This is necessary for storing historical data points needed for calculating technical indicators like MACD and Bollinger Bands that require multiple data points.

### account_states
Stores real-time account state from exchange monitoring for each user.

| Column           | Type            | Description                            |
|------------------|-----------------|----------------------------------------|
| id               | SERIAL          | Primary Key                            |
| user_id          | UUID            | Foreign Key to users table             |
| exchange         | VARCHAR         | Exchange name (e.g., 'bitmex')         |
| balance_data     | JSONB           | Account balance information            |
| position_data    | JSONB           | Current open positions                 |
| equity           | NUMERIC         | Total account equity                   |
| available_margin | NUMERIC         | Available margin for trading           |
| used_margin      | NUMERIC         | Currently used margin                  |
| updated_at       | TIMESTAMP       | Last update timestamp                  |

**Indexes:**
- Primary Key on `id`
- Index on `(user_id, updated_at)` for efficient latest state retrieval
- Foreign Key constraint on `user_id` referencing users table


### logs
Stores application logs with user context for debugging and monitoring.

| Column     | Type            | Description                            |
|------------|-----------------|----------------------------------------|
| log_id     | SERIAL          | Primary Key                            |
| user_id    | UUID            | Foreign Key to users table             |
| module     | VARCHAR         | Module generating the log              |
| log_level  | VARCHAR         | Log level (INFO, WARNING, ERROR)       |
| message    | TEXT            | Log message                            |
| timestamp  | TIMESTAMP       | Log timestamp                          |

**Indexes:**
- Primary Key on `log_id`
- Foreign Key constraint on `user_id` referencing users table

## Data Type Values for market_data Table

The `data_type` column in the `market_data` table helps the system interpret different types of data stored in the JSONB fields. Common values include:

- **indicator_values**: Structured technical indicator data with key-value pairs (e.g., `{"RSI": 70, "MACD": 1.2}`)
- **report**: Unstructured text reports like TradingView ggShot signals (e.g., `{"report": "Strong buy signal, TP 50000, SL 48000"}`)
- **sentiment**: Sentiment analysis results (e.g., `{"score": 0.8, "keywords": ["bullish", "news"]}`)
- **news**: News analysis or summaries (e.g., `{"date": "2023-10-01", "source": "CoinDesk", "summary": "Bitcoin rallies due to ETF approval rumors"}`)
- **mixed**: Combination of different data types

## JSONB Data Storage Examples

### TradingView ggShot (data_type: 'report')
```json
{
  "report": "Strong buy signal with TP at 50000 and SL at 48000"
}
```

### Technical Indicators (data_type: 'indicator_values')
```json
{
  "RSI": 70,
  "MACD": 1.2,
  "Bollinger_upper": 50000,
  "Bollinger_lower": 48000
}
```

### Sentiment Analysis (data_type: 'sentiment')
```json
{
  "score": 0.8,
  "keywords": ["bullish", "news"]
}
```

## Data Isolation

The database is designed with multi-user support in mind. All tables include a `user_id` column with a foreign key reference to the users table, ensuring proper data isolation between users. This enables the platform to safely handle multiple users without data leakage or interference.

## User IDs and Authentication

### Default Development User
For the initial development phase, a default user with the UUID `00000000-0000-0000-0000-000000000001` is created. All operations during this phase are associated with this default user.

### Future User Integration
For the production platform phase:
1. The authentication system will generate a UUID for each user upon registration
2. This UUID will be passed to our backend API via secure headers or tokens
3. Our backend uses this UUID as the `user_id` value in all database tables
4. All database operations are associated with the user's UUID
5. The API layer ensures that users can only access their own data

This approach maintains the database's existing structure and foreign key relationships. No additional tables or fields are needed beyond the existing schema, as it was originally designed with multi-user support in mind.

## Database Views and Helper Functions

### Schema Alignment (Post-Migration)
**COMPLETED**: All modules now use the direct trades table schema.

The database schema has been fully aligned across all modules:

| Database Field     | Purpose                                    |
|--------------------|-------------------------------------------|
| trade_status       | Trade status ('open', 'closed')          |
| symbol             | Trading pair symbol (e.g., 'BTC/USD')    |
| opened_at          | Trade creation timestamp                  |
| unrealized_pnl     | Current P&L                              |
| decision_id        | Stored in strategy_runs (not trades)     |

**Changes Applied:**
- Removed `trades_legacy` compatibility view 
- All code updated to use direct trades table
- `decision_id` moved to strategy_runs for proper audit trail
- Field naming standardized across all modules

**Usage:**
```sql
-- All modules now query trades table directly
SELECT * FROM trades 
WHERE user_id = %s AND trade_status = 'open';
```

## Universal Trade Lifecycle System (Migration 0012)

The database now implements a **universal trade lifecycle management system** that replaced the previous phantom-trade reconciliation approach. Key features:

### Core Principles
- **Exchange as Single Source of Truth**: Position data from exchange drives all trade state changes
- **Position-Based Lifecycle**: One trade record per exchange position (eliminates phantom trades)
- **Universal Exchange Support**: Configurable adapters for net vs hedge positioning modes
- **Order-Level Precision**: Separate order tracking for accurate VWAP and P&L calculation

### Trade Lifecycle Flow
1. **Position Detection**: Monitoring service detects new exchange position
2. **Trade Creation**: New trade record created automatically (trade_status='open')
3. **Position Updates**: Size/price changes update existing trade record
4. **Position Closure**: When position size=0, trade marked as closed with final P&L

### Schema Transformation
- **Old System**: Complex trades table with phantom trade reconciliation
- **New System**: Simple position-based trades + detailed trade_orders + instrument_metadata
- **Migration Impact**: Complete schema replacement (clean slate approach)

## Data Integrity Features

### Nuclear Reset Capability
For development and testing phases, the database supports complete data reset via the `nuclear_reset.sql` script, which safely removes all trading data while preserving the schema and constraints.

### Position-Based Trade Synchronization
The new system eliminates phantom trades through position-driven lifecycle management:
- **Real-time Position Sync**: Monitoring service polls exchange positions every 30 seconds
- **Automatic Trade Creation**: New positions automatically create trade records
- **Automatic Trade Updates**: Position size/price changes update existing trades
- **Automatic Trade Closure**: When position disappears, trade marked closed with final P&L
- **No Phantom Trades**: System only tracks actual exchange positions

### Universal Exchange Compatibility
The schema supports multiple exchange types through configurable position keys:
- **Net Positioning (BitMEX)**: Single position per symbol, side=NULL
- **Hedge Positioning (Binance)**: Separate long/short positions, side required
- **Instrument Metadata**: Exchange-specific contract specifications
- **Adapter Pattern**: Normalized position interface across all exchanges

### Performance Optimizations
Migration 0012 includes specialized indexes for:
- **Active Trade Queries**: Partial index on open trades for fast lookups
- **Position Key Lookups**: Composite index for finding trades by exchange position
- **Order Tracking**: Indexes for efficient order-to-trade mapping
- **Instrument Lookups**: Fast metadata retrieval for position calculations

## Recovery and Maintenance

### Trade Lifecycle Monitoring
Query current system state:
```sql
-- Active trades by exchange
SELECT exchange, symbol, COUNT(*) as active_trades 
FROM trades WHERE trade_status = 'open' GROUP BY exchange, symbol;

-- Recent trade activity
SELECT trade_id, exchange, symbol, size_contracts, trade_status, last_updated 
FROM trades ORDER BY last_updated DESC LIMIT 10;

-- Order tracking for a trade
SELECT exchange_order_id, side, price, filled_size, status, filled_at 
FROM trade_orders WHERE trade_id = 'your-trade-id' ORDER BY created_at;
```

### ggshot_filter
**NEW TABLE (Migration 0014)**: Logs all ggShot signal filter decisions for analysis and monitoring.

| Column                | Type            | Description                            |
|-----------------------|-----------------|----------------------------------------|
| filter_id             | UUID            | Primary Key                            |
| symbol                | VARCHAR(20)     | Trading pair symbol                    |
| signal_direction      | VARCHAR(10)     | Signal direction: 'LONG' or 'SHORT'   |
| confidence_score      | NUMERIC(4,3)    | LLM confidence score (0.000-1.000)    |
| filter_status         | VARCHAR(10)     | Filter result: 'APPROVED' or 'REJECTED' |
| reasoning_text        | TEXT            | Full LLM reasoning for the decision    |
| entry_price          | DECIMAL(20,8)   | Signal entry price (average of zone)  |
| stop_loss_price      | DECIMAL(20,8)   | Signal stop loss price                |
| take_profit_price    | DECIMAL(20,8)   | Signal take profit price (Target 1)   |
| signal_timeframe     | VARCHAR(10)     | Signal timeframe ('15m', '30m', etc.) |
| volume_analysis      | TEXT            | Volume confirmation analysis text      |
| original_signal_text | TEXT            | Original ggShot signal message         |
| full_prompt_text     | TEXT            | Complete prompt sent to decision LLM including all indicator values (for backtesting) |
| created_at           | TIMESTAMP       | Filter decision timestamp              |

**Purpose:**
- Tracks all ggShot filter decisions (both approved and rejected)
- Enables confidence score distribution analysis
- Provides audit trail for filter performance
- Supports filter optimization and calibration
- Stores complete LLM prompts for backtesting and prompt analysis

**Indexes:**
- Primary Key on `filter_id`
- Index on `symbol` for symbol-specific analysis
- Index on `confidence_score` for distribution analysis
- Index on `filter_status` for approval/rejection rates
- Index on `created_at` for time-series analysis

**Usage Examples:**
```sql
-- Confidence score distribution
SELECT 
  ROUND(confidence_score, 1) as score_range,
  COUNT(*) as count,
  filter_status
FROM ggshot_filter 
GROUP BY ROUND(confidence_score, 1), filter_status 
ORDER BY score_range;

-- Filter performance by symbol
SELECT 
  symbol,
  COUNT(*) as total_signals,
  AVG(confidence_score) as avg_confidence,
  COUNT(*) FILTER (WHERE filter_status = 'APPROVED') as approved,
  COUNT(*) FILTER (WHERE filter_status = 'REJECTED') as rejected
FROM ggshot_filter 
GROUP BY symbol 
ORDER BY total_signals DESC;

-- Recent filter decisions
SELECT symbol, signal_direction, confidence_score, filter_status, created_at
FROM ggshot_filter 
ORDER BY created_at DESC 
LIMIT 10;
```

### Data Integrity Verification
```sql
-- Check for orphaned orders (should be empty)
SELECT COUNT(*) FROM trade_orders 
WHERE trade_id NOT IN (SELECT trade_id FROM trades);

-- Verify instrument metadata coverage
SELECT exchange, symbol FROM trades 
WHERE (exchange, symbol) NOT IN (SELECT exchange, symbol FROM instrument_metadata);

-- Check ggShot filter logging health
SELECT 
  DATE(created_at) as date,
  COUNT(*) as daily_signals,
  AVG(confidence_score) as avg_confidence
FROM ggshot_filter 
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at) 
ORDER BY date DESC;

-- Check config_instances for ggShot paper trading
SELECT 
  ci.config_id,
  ci.instance_name,
  ci.hummingbot_account,
  ci.status,
  ci.paper_balance_usd,
  c.config_name,
  c.config_type
FROM config_instances ci
JOIN configurations c ON ci.config_id = c.config_id
WHERE c.config_type = 'ggshot';
```

---

## 🎯 **Current Live Usage (August 2025)**

### **ggShot Paper Trading**
The config_instances table is actively used for live ggShot paper trading:

```sql
-- Live ggShot configuration mapping
SELECT * FROM config_instances 
WHERE config_id = 'e249bb49-0455-4596-9657-09bf9e14ca14';

/*
Expected result:
config_id: e249bb49-0455-4596-9657-09bf9e14ca14
instance_name: ggbot-00000000-e249bb49  
hummingbot_account: ggshot_paper_account
status: active
paper_balance_usd: 10000.00
*/
```

### **Performance Tracking Integration**
The PerformanceTracker service queries both ggBot and Hummingbot databases:
- **Strategy runs**: Decision tracking in ggBot database
- **Trade execution**: Actual trades in Hummingbot database  
- **Account mapping**: config_instances links the two systems
- **P&L calculation**: Real-time performance from actual paper trades

### **Multi-Strategy Architecture** 
Ready for template-based strategy creation:
- Each new configuration gets automatic config_instances entry
- Isolated $10k paper accounts per strategy
- Unique instance naming prevents conflicts
- Dashboard APIs provide unified performance view

The database schema supports live paper trading with real performance tracking!