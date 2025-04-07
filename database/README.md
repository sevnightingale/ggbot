# ggbot Database Structure

This directory contains database migration scripts for the ggbot platform. The database is designed to support a multi-user trading agent platform where users can configure and deploy trading agents for various cryptocurrency pairs across multiple exchanges.

## Migration Scripts

- `0001_create_tables.sql`: Initial schema creation (sessions, trades, logs)
- `0002_add_user_id.sql`: Adds multi-user support with users table and foreign key constraints
- `0003_create_market_data.sql`: Creates the market_data table for storing price and indicator data
- `0004_update_schema_for_platform.sql`: Updates schema to support platform architecture (configurations table, additional fields)
- `0005_additional_improvements.sql`: Adds data_type column to market_data, config_name to configurations, and config_id to trades
- `0006_update_configuration_constraint.sql`: Updates unique constraint on configurations table to support multiple named configurations

## Database Schema

### users
Stores user information for multi-user support.

| Column     | Type            | Description                            |
|------------|-----------------|----------------------------------------|
| user_id    | UUID            | Primary Key                            |
| username   | VARCHAR         | User's username                        |
| email      | VARCHAR         | User's email address                   |
| created_at | TIMESTAMP       | Account creation timestamp             |
| last_login | TIMESTAMP       | Last login timestamp                   |

**Indexes:**
- Primary Key on `user_id`

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
- Index on `(user_id, config_type)` for efficient lookups
- Foreign Key constraint on `user_id` referencing users table

### trades
Stores information about trades executed by the platform.

| Column             | Type            | Description                            |
|--------------------|-----------------|----------------------------------------|
| trade_id           | UUID            | Primary Key                            |
| user_id            | UUID            | Foreign Key to users table             |
| config_id          | UUID            | Foreign Key to configurations table    |
| exchange           | VARCHAR         | Exchange where trade was executed      |
| pair               | VARCHAR         | Trading pair (e.g., 'BTC/USD')         |
| timeframe          | VARCHAR         | Timeframe used for analysis            |
| collateral_amount  | NUMERIC         | Amount of collateral for the trade     |
| leverage           | INTEGER         | Leverage used for the trade            |
| stop_loss          | NUMERIC         | Stop loss price                        |
| take_profit        | NUMERIC         | Take profit price                      |
| confidence_score   | NUMERIC         | Confidence score from the LLM          |
| reasoning_log      | TEXT            | Reasoning from the LLM for the trade   |
| trade_status       | VARCHAR         | Status of the trade                    |
| created_at         | TIMESTAMP       | Trade creation timestamp               |
| closed_at          | TIMESTAMP       | Trade closure timestamp                |
| profit_loss        | NUMERIC         | Profit or loss from the trade          |

**Indexes:**
- Primary Key on `trade_id`
- Index on `created_at`
- Index on `(user_id, created_at)` for user-specific trade history
- Index on `(user_id, config_id)` for configuration-specific trade history
- Foreign Key constraint on `user_id` referencing users table
- Foreign Key constraint on `config_id` referencing configurations table

### market_data
Stores market data including indicators and price data for different pairs and timeframes.

| Column     | Type            | Description                            |
|------------|-----------------|----------------------------------------|
| id         | SERIAL          | Primary Key                            |
| user_id    | UUID            | Foreign Key to users table             |
| source     | VARCHAR         | Data source (e.g., 'tradingview', 'yfinance') |
| symbol     | VARCHAR         | Trading pair symbol                    |
| timeframe  | VARCHAR         | Timeframe (e.g., '15m', '1h', '4h')    |
| data_type  | VARCHAR         | Type of data (e.g., 'price_data', 'report', 'sentiment') |
| indicators | JSONB           | Technical indicators in JSON format    |
| raw_data   | JSONB           | Raw price/chart data in JSON format    |
| updated_at | TIMESTAMP       | Timestamp of the data point            |

**Indexes:**
- Primary Key on `id`
- Unique constraint on `(user_id, symbol, timeframe, updated_at)` to allow multiple data points per timeframe
- Index on `(user_id, symbol, timeframe, updated_at)` for efficient retrieval
- Foreign Key constraint on `user_id` referencing users table

**Important Note**: Migration `0008_update_market_data_constraint.sql` changes the unique constraint to allow multiple entries per user-symbol-timeframe combination with different timestamps. This is necessary for storing historical data points needed for calculating technical indicators like MACD and Bollinger Bands that require multiple data points.

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

## Default User

For the MVP phase focusing on personal use, a default user with the UUID `00000000-0000-0000-0000-000000000001` is created. All operations during this phase are associated with this default user.