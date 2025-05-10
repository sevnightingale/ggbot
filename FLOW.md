User configures Extraction, Decision, and Trading Agents via Bubble.io frontend with crypto pairs, timeframes, trading strategy rules, and exchange details 
Bubble.io generates UUID for user and sends configuration to backend API
Backend stores configuration in configurations table with user_id, config_type ('extraction', 'decision', 'trading'), and config_name
User activates ggbot via frontend
Backend retrieves ggbot configuration from configurations table using user_id and config_name
Extraction Agent loads configuration from configurations table every candle close (e.g., 15m)
Extraction Agent uses Browser-Use to scrape signals from TradingView for configured pair/timeframe
Extraction Agent connects to Indicators MCP server using async context manager and snake_case naming convention
Extraction Agent computes technical indicators (e.g., RSI, MACD) via Indicators MCP tools, with proper connection cleanup
Extraction Agent fetches historical data via yfinance for redundancy or custom indicators
Extraction Agent fetches real-time price from exchange via CCXT MCP every 5 minutes using snake_case tool naming
Extraction Agent stores signals, indicators, and price in market_data table with data_type (e.g., 'report', 'indicator_values')
Decision Agent loads configuration from configurations table every 5 minutes
Decision Agent queries market_data table for latest signals, indicators, and price for configured pair/timeframe
Decision Agent checks trades table for active trades; if none, enters "looking for new trades" state
Decision Agent uses reasoning LLM (ex: DeepSeek R1) to analyze data (from database) + trading strategy (from config) and decide on actions (open, adjust, close trades)
Decision Agent generates JSON trade command with action, symbol, side, leverage, amount, stop_loss, confidence, and reasoning
Decision Agent stores decision in trades table with config_id for new trades or updates existing records
Trading Agent loads configuration from configurations table when new trade command is generated
Trading Agent fetches API keys via CredentialProvider (EnvCredentialProvider for testing, DbCredentialProvider for production from exchange_keys)
Trading Agent generates temporary ccxt-accounts.json with API keys
Trading Agent connects to CCXT MCP server using async context manager with automatic cleanup
Trading Agent validates trade command with jsonschema
Trading Agent executes trade via CCXT MCP tools (e.g., set_leverage, create_market_buy_order) using snake_case naming
Trading Agent stores transaction ID and order details in trades table
Trading Agent queries exchange every 5 minutes via CCXT MCP for position updates (fetch_positions, fetch_open_orders)
Trading Agent updates trades table with current price, P/L, and status; marks closed trades if stop-loss or take-profit hit
Decision Agent queries updated trades table every 5 minutes; if active trades exist, enters "managing active trades" state
Decision Agent saves conversation history and reasoning logs in trades table for active trades
Decision Agent adjusts trades based on Trading Agent updates or closes trades if conditions met
Retry MCP connection failures with exponential backoff using _cleanup_contexts to ensure resource release
Retry data extraction failures up to 3 times with exponential backoff
Fall back to "no trade" or retry once for ChatGPT API failures
Log trade execution errors in logs table and notify Decision Agent to adjust parameters
Run each ggbot in a separate process or Docker container for user isolation
Use encrypted keys from exchange_keys table for production credential security