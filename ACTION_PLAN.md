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

3. Implement Logging and Configuration Management
[x] Install the loguru library for centralized logging across all modules.
[x] Develop a logger.py in the common/ directory to handle logging with levels (DEBUG, INFO, ERROR) and include user_id context.
[x] Configure logging to capture key events, including trade actions, exchange errors, and module-specific messages.
[x] Develop a config.py in the common/ directory to centralize environment variable loading and application settings.
[x] Ensure that all modules use the centralized logger and configuration for consistency.
[ ] Create the Configuration Management Layer in the config/ directory with interfaces and providers for user configurations.
[ ] Implement FileConfigProvider for the MVP to store configurations in JSON files.
[ ] Define schema validation for user configurations to ensure they meet system requirements.

4. Develop the Extraction Module with Interfaces
- [x] Install Playwright, Browser-use, and steel-sdk for browser automation and set up a persistent BrowserContext to maintain session state.
- [x] Develop extraction.py TEST script (test if login to trading view, access chart is valid by having agent check current price)
- [x] Improve extraction.py to test navigating ggShot settings, extracting indicator data for 1 timeframe
- [x] Expand extraction.py prompt to include multiple time-frames (15min, 1hr, 4hr)
- [x] Draft and refine the prompt for the extraction agent—clearly instruct ChatGPT 4o on what to extract from the ggShot indicator, including trend signals, TP levels, SL, and any additional context.
- [x] Extract ggShot signals via ChatGPT 4o Vision (primary method, not fallback) by capturing TradingView chart screenshots and analyzing them.
- [ ] Define DataSource interface in extraction/interfaces/ directory
- [ ] Implement TradingViewDataSource as the first implementation of DataSource
- [ ] Define IndicatorComputer interface in extraction/interfaces/ directory
- [ ] Implement PandasTAIndicators using yfinance and pandas-ta
- [ ] Refactor existing extraction code to follow the new interface architecture
- [ ] Add function to store extraction output in database with user_id association
- [ ] Duplicate tasks for multiple time-frames
- [ ] Add re-login function in case sessions expires
- [ ] Fetch **historical market data** using `yfinance` (for the same pair/timeframes tracked in TradingView).
- [ ] Calculate technical indicators (e.g., RSI, MACD, Bollinger Bands) using `pandas-ta` on the DataFrames returned by `yfinance`.
- [ ] Query exchange price feeds (starting with Gains Network's diamond contract) **every 5 minutes** for real-time prices.
- [ ] Store extracted **price context data** (recent highs/lows, momentum, volatility) in the database to provide historical market awareness for the Decision Module.
- [ ] Schedule the extraction process to trigger right after each candle closes based on the configured timeframe.
- [ ] Implement concurrency limits to ensure only **one or two browser instances** run at a time to avoid overloading the VM.
- [ ] Store extracted signals, technical indicators, and price data in the `market_data` table, keyed by user_id, pair, source, and timeframe.
- [ ] Regularly monitor for any TradingView anti-bot measures and adjust stealth techniques as needed.

5. Develop the Decision Module with Strategy Interface
[ ] Define Strategy interface in decision/interfaces/ directory
[ ] Implement GGShotStrategy as the first implementation of Strategy
[ ] Define LLMProvider interface in decision/interfaces/ directory
[ ] Implement initial providers (DeepSeekProvider, GPT4oProvider, etc.)
[ ] Develop a prompt template system for each strategy
[ ] Implement logic to query the database every 5 minutes for the latest extracted data and any active trade information, filtered by user_id.
[ ] Use the configured LLM to generate trade decisions (open, adjust, close) along with confidence scores and reasoning.
[ ] Implement monitoring logic to re-evaluate active trades every 5 minutes and decide on adjustments or closures.
[ ] Implement fallback logic to handle scenarios where the LLM is unavailable.
[ ] Store the LLM's decisions, confidence scores, and reasoning in the database for each evaluation cycle, associated with the user_id.

6. Develop the Structuring Module with Exchange Command Interface
[ ] Define ExchangeCommand interface in structuring/interfaces/ directory
[ ] Implement GTradeCommand as the first implementation
[ ] Install the jsonschema library to enforce schema validation for trade commands.
[ ] Define a JSON schema for each supported exchange format
[ ] Implement logic to parse the high-level trade recommendations from the Decision Module.
[ ] Validate the trade actions against the JSON schema and enforce risk parameters from user configuration.
[ ] Query exchange APIs to retrieve dynamic risk parameters (e.g., max leverage for the pair).
[ ] Implement fallback logic to use local configuration limits if on-chain queries fail.
[ ] Construct the final command for the trade action, ensuring it matches the exchange's requirements.

7. Develop the Trades Module with Trade Record Interface
[ ] Define TradeRecord interface in trades/interfaces/ directory
[ ] Implement exchange-specific trade record implementations
[ ] Implement CRUD operations to create new trade records when a trade is opened, update records for adjustments, and close records when a trade is finalized.
[ ] Log the LLM's reasoning and confidence scores in the reasoning_log field for each trade update.
[ ] Track partial close events and other adjustments in the trade record.
[ ] Provide a function to retrieve relevant trade history and context for the Decision Module.
[ ] Ensure all database operations include user_id for proper data isolation.

8. Develop the Execution Module (renamed from On-Chain) with Exchange Interface
[ ] Define Exchange interface in execution/interfaces/ directory
[ ] Implement GTradeExchange as the first implementation
[ ] Define AuthenticationStrategy interface in execution/interfaces/ directory
[ ] Implement necessary authentication strategies (AgentKitStrategy for blockchain, APIKeyStrategy for centralized exchanges)
[ ] Integrate Coinbase AgentKit for secure wallet management and transaction signing for blockchain exchanges.
[ ] Use Web3.py or Ethers.js to interact with Gains Network's diamond contract on Base L2.
[ ] Implement functions to sign and submit trade commands using the validated JSON from the Structuring Module.
[ ] Set up event monitoring to listen for exchange events (e.g., trade confirmations, liquidations).
[ ] Implement fallback polling logic with exponential backoff to check trade statuses if events fail.
[ ] Batch API calls to exchanges to minimize overhead and optimize resource usage.
[ ] Update the trade records in the database with transaction hashes, statuses, and any exchange events.

9. Implement Inter-Module Communication
[ ] Create communication flow between Configuration Management Layer and all modules.
[ ] Ensure the Extraction Module stores data in the database for access by the Decision Module.
[ ] Implement logic for the Decision Module to retrieve data from the database and pass decisions to the Structuring Module.
[ ] Enable the Structuring Module to send validated commands to the Execution Module.
[ ] Allow the Execution Module to update trade statuses in the database, which the Trades Module can then log.
[ ] Use in-memory caching (e.g., Redis) for frequently accessed data like recent price updates to reduce database load.

10. Test Individual Modules
[ ] Write unit tests for the Extraction Module to validate data source implementations and indicator computation.
[ ] Write unit tests for the Decision Module to validate strategy implementations and LLM provider integration.
[ ] Write unit tests for the Structuring Module to validate command generation and risk filtering.
[ ] Write unit tests for the Trades Module to confirm proper trade record management and logging.
[ ] Write unit tests for the Execution Module to verify exchange interactions and authentication strategies.
[ ] Write unit tests for the Configuration Management Layer to validate configuration providers and schema validation.
[ ] Conduct integration tests to ensure modules communicate correctly.
[ ] Perform stress tests to simulate peak loads and ensure the system remains stable on the VM.

11. Conduct End-to-End Testing
[ ] Implement a dry-run mode that simulates the entire pipeline without executing real transactions.
[ ] Set up testnet or paper trading environments for each supported exchange for safe testing.
[ ] Validate the complete workflow, from data extraction to trade execution, using test data and simulated trades.
[ ] Conduct a light load test on the Extraction Module to confirm resource usage remains within limits.
[ ] Test multi-timeframe and multi-exchange scenarios to ensure proper handling.

12. MVP Deployment and Monitoring
[ ] Create a default config.json for personal use with preferred settings.
[ ] Use Docker to containerize the application and deploy it on the VM.
[ ] Set up continuous monitoring for system performance, resource usage, and critical alerts.
[ ] Regularly review logs and performance metrics to ensure the system operates within resource constraints.
[ ] Implement cost assessment to monitor LLM API usage, transaction fees, and VM expenses.
[ ] Harden security by refining authentication handling and restricting environment variable access.

13. Platform Development Preparation (Future Phase)
[ ] Design the frontend UI for the configuration interface.
[ ] Implement user authentication and management system.
[ ] Develop the DatabaseConfigProvider for storing configurations in the database.
[ ] Create a strategy marketplace architecture for sharing trading strategies.
[ ] Plan for containerized microservices architecture to support scaling.
[ ] Design the webhook/notification system for trade alerts and system status.
[ ] Prepare documentation for API endpoints to enable third-party integrations.

14. Post-Launch Adjustments and Monitoring
[ ] Begin with minimal trades to monitor system behavior and trade outcomes.
[ ] Refine trade parameters (e.g., stop-loss, leverage) based on real-world performance.
[ ] Stay updated on exchange API changes to adapt the system as needed.
[ ] Monitor database performance and optimize queries as data volume grows.
[ ] Add support for additional exchanges based on user feedback.
[ ] Refine and expand the available strategies with performance tracking.