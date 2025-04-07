1. Set Up the Development Environment
[x] Provision a DigitalOcean droplet with 2 GB RAM and 1 vCPU for development and deployment.
[x] Install Docker and Docker Compose on the droplet to ensure consistent environments.
[x] Install code-server on the droplet to enable browser-based development using VSCode.
[x] Configure code-server with secure authentication and SSL for safe remote access.
[x] Install Git on the droplet and create a new repository on GitHub for version control.
[x] Clone the repository to the droplet and set up the project structure with directories for each module: extraction/, decision/, structuring/, trades/, execution/ (renamed from onchain/), common/, and config/ (new).
[x] Create a .gitignore file to exclude unnecessary files (e.g., .env, logs, caches).
[x] Write a README.md with setup instructions, including how to connect to code-server from a local browser.
[x] Set up a Python virtual environment within the project directory to manage dependencies.
[x] Create requirements.txt listing core dependencies (Playwright, Web3.py, yfinance, pandas‑ta, jsonschema, loguru, etc.).
[x] Create a .env.example file to specify environment variables (e.g., API keys, RPC URLs) with blank or mocked values, noting that .env is for prototyping only.

2. Configure the Database
[x] Install PostgreSQL on the droplet or use a Docker container for the database.
[x] Create a new database named ggbot in PostgreSQL.
[x] Define the schema for the users table: user_id (UUID, Primary Key), username (VARCHAR), email (VARCHAR), created_at (TIMESTAMP), last_login (TIMESTAMP).
[x] Define the schema for the sessions table: session_id (UUID, Primary Key), user_id (UUID, FK to users), cookie_data (JSONB), created_at (TIMESTAMP), expires_at (TIMESTAMP).
[x] Define the schema for the configurations table: config_id (UUID, Primary Key), user_id (UUID, FK to users), config_type (VARCHAR), config_data (JSONB), created_at (TIMESTAMP), updated_at (TIMESTAMP).
[x] Define the schema for the trades table: trade_id (UUID, Primary Key), user_id (UUID, FK to users), exchange (VARCHAR), pair (VARCHAR), timeframe (VARCHAR), collateral_amount (NUMERIC), leverage (INTEGER), stop_loss (NUMERIC), take_profit (NUMERIC), confidence_score (NUMERIC), reasoning_log (TEXT), trade_status (VARCHAR), created_at (TIMESTAMP), closed_at (TIMESTAMP), profit_loss (NUMERIC).
[x] Define the schema for the market_data table: data_id (UUID, Primary Key), user_id (UUID, FK to users), source (VARCHAR), pair (VARCHAR), timeframe (VARCHAR), indicators (JSONB), raw_data (JSONB), timestamp (TIMESTAMP).
[x] Define the schema for the logs table: log_id (SERIAL, Primary Key), user_id (UUID, FK to users), module (VARCHAR), log_level (VARCHAR), message (TEXT), timestamp (TIMESTAMP).
[x] Implement indexes on sessions.expires_at, trades.user_id + trades.created_at, market_data.user_id + market_data.pair + market_data.timeframe + market_data.timestamp.
[x] Write migration scripts to create and maintain the database schema consistently.

3. Implement Logging and Common Utilities
[x] Install the loguru library for centralized logging across all modules.
[x] Develop a logger.py in the common/ directory to handle logging with levels (DEBUG, INFO, ERROR) and include user_id context.
[x] Configure logging to capture key events, including trade actions, exchange errors, and module-specific messages.
[x] Develop a config.py in the common/ directory to centralize environment variable loading and application settings.
[x] Ensure that all modules use the centralized logger and configuration for consistency.

4. Develop Core Extraction Module with yfinance and pandas-ta
[x] Install Playwright, Browser-use, and steel-sdk for browser automation and set up a persistent BrowserContext to maintain session state.
[x] Develop extraction.py TEST script (test if login to trading view, access chart is valid by having agent check current price)
[x] Improve extraction.py to test navigating ggShot settings, extracting indicator data for 1 timeframe
[x] Expand extraction.py prompt to include multiple time-frames (15min, 1hr, 4hr)
[x] Draft and refine the prompt for the extraction agent—clearly instruct ChatGPT 4o on what to extract from the ggShot indicator, including trend signals, TP levels, SL, and any additional context.
[x] Extract ggShot signals via ChatGPT 4o Vision (primary method, not fallback) by capturing TradingView chart screenshots and analyzing them.
[x] Install yfinance and pandas-ta packages
[x] Define DataSource interface in extraction/interfaces/ directory
[x] Define IndicatorComputer interface in extraction/interfaces/ directory
[x] Implement YFinanceDataSource as the primary testing data source
[x] Fetch BTC-USD historical data for multiple timeframes (15m, 1h, 4h, 1d)
[x] Implement logic to fetch only new data since last update
[x] Update market_data table schema to support storing raw data and indicators
[x] Store raw price data (OHLCV) in the market_data table
[x] Implement PandasTAIndicators for technical analysis
[x] Calculate common indicators (SMA, EMA, RSI, MACD, Bollinger Bands)
[x] Store calculated indicators in JSON format in the database
[x] Create a data extraction scheduler to update data every 15 minutes
[x] Create extraction_main.py and scheduled_extraction.py for automated data collection
[x] Add function to store extraction output in database with user_id association
[x] Implement database queries to retrieve latest market data for decision module
[x] Create shell script for running scheduled extraction through cron jobs
[x] Implement initialization and incremental update modes for efficient data collection
[] test and fix any bugs with extraction process

5. Implement TradingView Extraction (Defer for Production)
[ ] Refactor existing TradingView extraction code to follow the interface architecture
[ ] Add re-login function in case session expires
[ ] Implement concurrency limits to ensure only one or two browser instances run at a time
[ ] Store extracted signals from TradingView in the market_data table
[ ] Regularly monitor for any TradingView anti-bot measures and adjust techniques

6. Develop the Decision Module with Strategy Interface
[ ] Define Strategy interface in decision/interfaces/ directory
[ ] Define LLMProvider interface in decision/interfaces/ directory
[ ] Implement DeepSeekProvider as the initial LLM provider
[ ] Create a BasicTAStrategy implementation for testing
[ ] Design a prompt template that analyzes basic technical indicators
[ ] Implement logic to query for BTC-USD market data from multiple timeframes
[ ] Implement logic to generate trade decisions with confidence scores and reasoning
[ ] Store the LLM's decisions in the database with proper user_id association
[ ] Implement a simple scheduled job to run decision making every 15 minutes
[ ] Implement fallback logic for LLM unavailability
[ ] Add monitoring logic to evaluate and log strategy performance

7. Develop the Structuring Module with Exchange Command Interface
[ ] Define ExchangeCommand interface in structuring/interfaces/ directory
[ ] Implement GTradeCommand for the Gains Network gTrade platform
[ ] Install and configure the jsonschema library for command validation
[ ] Define a JSON schema for the gTrade command format
[ ] Create a simple risk parameter configuration for testing
[ ] Implement logic to convert decision outputs into exchange-specific commands
[ ] Validate commands against schema and risk parameters
[ ] Implement fallback logic for configuration-based risk limits
[ ] Add proper logging for command generation and validation

8. Develop the Trades Module with Trade Record Interface
[ ] Define TradeRecord interface in trades/interfaces/ directory
[ ] Create GtradeTrade implementation for the Gains Network platform
[ ] Implement database operations for trade lifecycle management (create, update, close)
[ ] Ensure proper user_id association for all records
[ ] Store LLM reasoning and confidence scores with each trade record
[ ] Implement functions to retrieve active trades and history for the Decision Module
[ ] Add support for tracking trade performance metrics

9. Develop the Execution Module with Exchange Interface
[ ] Define Exchange interface in execution/interfaces/ directory
[ ] Define AuthenticationStrategy interface in execution/interfaces/ directory
[ ] Implement AgentKitStrategy for blockchain interactions
[ ] Create GTradeExchange implementation for Gains Network
[ ] Use Web3.py to interact with gTrade's diamond contract on Base L2
[ ] Implement dry-run mode for testing without actual transactions
[ ] Create functions to execute trades based on structuring module commands
[ ] Implement transaction status monitoring and event handling
[ ] Add proper error handling and retry logic for failed transactions
[ ] Update trade records with transaction details and status changes

10. Implement Inter-Module Communication
[ ] Create a simple database-centric communication flow between modules
[ ] Ensure proper data flow from Extraction → Decision → Structuring → Execution → Trades
[ ] Implement a main application entry point that coordinates module interactions
[ ] Create scheduled tasks for regular module execution (extraction, decision making)
[ ] Add proper error handling for module communication failures
[ ] Implement basic monitoring to verify data flow between modules

11. Testing and Validation
[x] Write basic tests for the YFinanceDataSource implementation
[x] Test the PandasTAIndicators implementation with sample data
[x] Create test fixtures for market data in different timeframes
[ ] Test the Decision Module with sample market data inputs
[ ] Validate Structuring Module command generation and validation
[ ] Test Trades Module CRUD operations
[ ] Implement a test mode for the Execution Module without real transactions
[ ] Create integration tests for the complete workflow
[ ] Perform basic stress testing on the VM to ensure stability

12. End-to-End Testing and Dry Run
[ ] Implement an end-to-end dry-run mode for the entire system
[ ] Set up a test configuration with conservative risk parameters
[ ] Run the complete workflow with BTC-USD data and simulated trades
[ ] Monitor system resource usage during extended testing
[ ] Validate multi-timeframe analysis works correctly
[ ] Test with simulated market conditions (trending, ranging, volatile)

13. MVP Deployment and Configuration
[x] Create baseline configuration files for personal use
[ ] Implement basic environment settings for production
[ ] Deploy the application on the DigitalOcean VM
[ ] Set up monitoring for system performance and resource usage
[ ] Create a simple dashboard for tracking trades and performance
[ ] Implement cost tracking for LLM API usage and transaction fees
[ ] Configure regular database backups

14. Configuration Management Layer (Future - After Core Modules)
[ ] Define ConfigurationProvider interface in config/interfaces/ directory
[ ] Implement FileConfigProvider for JSON file-based configuration
[ ] Design schema validation for user configurations
[ ] Create default configurations for each module
[ ] Add configuration reloading support for updates without restart
[ ] Implement basic configuration validation and error handling

15. Live Trading and Refinement
[ ] Start with minimal real trades using conservative risk parameters
[ ] Implement a system for tracking actual trade performance
[ ] Create a process for iteratively improving trading strategies
[ ] Monitor and optimize LLM prompts based on trade outcomes
[ ] Refine risk parameters based on performance data
[ ] Implement regular system health checks and reporting

16. Platform Development (Future Phase)
[ ] Design multi-user architecture and database schema updates
[ ] Create frontend UI for configuration management
[ ] Implement user authentication and account management
[ ] Develop DatabaseConfigProvider for storing configurations
[ ] Design strategy marketplace for sharing trading strategies
[ ] Implement containerized architecture for scaling
[ ] Create API documentation for third-party integrations