User configures Extraction, Decision, and Trading Agents via Bubble.io frontend with crypto pairs, timeframes, trading strategy rules, and exchange details.
Bubble.io generates UUID for user and sends configuration to backend API.
Backend stores configuration in `configurations` table with `user_id`, `config_type` ('extraction', 'decision', 'trading'), and `config_name`.
User activates ggbot via frontend.
Backend retrieves ggbot configuration from `configurations` table using `user_id` and `config_name`.
Extraction Agent loads configuration from `configurations` table every candle close (e.g., 15m).
Extraction Agent uses Browser-Use to scrape signals from TradingView for configured pair/timeframe.
Extraction Agent connects to Indicators MCP server using async context manager and snake_case naming convention.
Extraction Agent computes technical indicators (e.g., RSI, MACD) via Indicators MCP tools, with proper connection cleanup.
Extraction Agent fetches historical data via yfinance for redundancy or custom indicators.
Extraction Agent fetches real-time price from exchange via CCXT MCP every 5 minutes using snake_case tool naming.
Extraction Agent stores signals, indicators, and price in `market_data` table with `data_type` (e.g., 'report', 'indicator_values').
Decision Agent loads configuration from `configurations` table every 5 minutes.
Decision Agent queries `market_data` table for latest signals, indicators, and price for configured pair/timeframe.
Decision Agent checks `trades` table for active trades; if none, enters "looking for new trades" state.
Decision Agent uses reasoning LLM (ex: DeepSeek R1) to analyze data (from database) + trading strategy (from config) and decide on actions (open, adjust, close trades).
Decision Agent generates a semi-structured trade intent with action, symbol, side, leverage, amount/size details, stop_loss, confidence, and reasoning.
Decision Agent sends the trade intent to the Trading Module.
Trading Agent (Engine) loads its configuration from `configurations` table upon receiving an intent or at startup.
Trading Agent (Engine) fetches API keys via CredentialProvider (EnvCredentialProvider for testing, DbCredentialProvider for production from `exchange_keys`).
Trading Agent (Engine) receives the semi-structured trade intent from the Decision Agent.
Trading Agent (Engine) provides the intent and available CCXT MCP tools to its internal LLM (Trading Agent LLM).
Trading Agent (LLM) proposes a sequence of CCXT MCP tool calls to fulfill the intent.
Trading Agent (TradeCompiler) validates the LLM-proposed tool calls against schemas, risk rules, and exchange constraints.
Trading Agent (TradeCompiler) maps symbols, finalizes parameters (e.g., precision, `clientOrderId`), and ensures correct naming conventions (e.g., snake_case for MCP).
Trading Agent (Engine) executes the *validated* tool calls via the CCXT MCP Adapter (which connects to CCXT MCP server using async context manager).
Trading Agent (Engine) records the trade details (entry, status, `decision_id`, `execution_details` including proposed/validated calls) in the `trades` table for new trades or updates existing records for adjustments/exits.
Trading Agent (TradeManager) queries exchange every 5 minutes via CCXT MCP (using validated calls) for position updates.
Trading Agent (TradeManager) updates the `trades` table with current price, P/L, and status.
Trading Agent (TradeManager) detects if stop-loss or take-profit conditions are met based on polled data and initiates an internal exit intent to the Trading Engine.
Decision Agent queries updated `trades` table (or Trading Engine's status API) every 5 minutes.
Decision Agent, if active trades exist, enters "managing active trades" state.
Decision Agent analyzes active trade status (from `trades` table/Trading Engine API) and may generate new intents to adjust or close trades.
Decision Agent saves its conversation history and reasoning logs (potentially linked to `decision_id` or `trade_id` in a separate log or within `trades` table if appropriate).
Retry MCP connection failures with exponential backoff using proper cleanup contexts to ensure resource release.
Retry data extraction failures up to 3 times with exponential backoff.
Fall back to "no trade" or retry once for LLM API failures (both Decision and Trading Agent LLMs).
Log trade execution errors, compiler rejections, and other critical issues in a dedicated `logs` table or structured logging system.
Notify Decision Agent (or a monitoring system) of significant trading errors or rejections.
Run each ggbot (or user's set of agents) in a separate process or Docker container for user isolation.
Use encrypted keys from `exchange_keys` table (or secrets manager) for production credential security.