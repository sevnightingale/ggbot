1. Set Up the Development Environments
[BACKEND SETUP]
[x] Provision a DigitalOcean droplet with 4 GB RAM and 2 vCPU for development and deployment.
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

[BUBBLE.IO SETUP]
[x] Create a Bubble.io account and initialize a new application for the ggbots platform.
[] Set up the basic application structure with core pages (dashboard, configuration, monitoring).
[ ] Configure the database schema in Bubble for user management and agent configurations.
[ ] Install required plugins (API Connector, Responsive Design, Data Visualization, etc.).
[ ] Create initial user workflow for registration and login.
[ ] Set up API connector configuration for future backend integration.

2. Configure the Backend Database
[x] Install PostgreSQL on the droplet or use a Docker container for the database.
[x] Create a new database named ggbots in PostgreSQL.


3. Implement Backend API and Common Utilities
[x] Install the loguru library for centralized logging across all modules.
[x] Develop a logger.py in the common/ directory to handle logging with levels (DEBUG, INFO, ERROR) and include user_id context.
[x] Configure logging to capture key events, including trade actions, exchange errors, and module-specific messages.
[x] Develop a config.py in the common/ directory to centralize environment variable loading and application settings.
[x] Ensure that all modules use the centralized logger and configuration for consistency.

[ ] Set up FastAPI framework for the backend API server.
[ ] Implement authentication middleware for validating Bubble.io user tokens.
[ ] Create basic API endpoint structure (configuration, data, agent control, status).
[ ] Implement request/response serialization and validation with Pydantic.
[ ] Set up basic error handling and request logging for API endpoints.
[ ] Create utilities for Bubble.io user ID validation and handling.
[ ] Develop testing framework for API endpoints.

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
[x] test and fix any bugs with extraction process

5. Integrate Crypto Indicators MCP for Technical Analysis
[x] Install and configure Crypto Indicators MCP according to documentation
[ ] Create CryptoIndicatorsMCPDataSource implementation following the DataSource interface
[ ] Implement methods to fetch and calculate indicators via the MCP
[ ] Add support for 50+ technical indicators provided by the MCP
[ ] Create comparison tests between pandas-ta and MCP calculations for validation
[ ] Store MCP-calculated indicators in the market_data table
[ ] Update scheduled extraction jobs to use the MCP
[ ] Configure MCP integration in the configuration system

6. Implement TradingView Extraction (Defer for Production)
[ ] Refactor existing TradingView extraction code to follow the interface architecture
[ ] Add re-login function in case session expires
[ ] Implement concurrency limits to ensure only one or two browser instances run at a time
[ ] Store extracted signals from TradingView in the market_data table
[ ] Regularly monitor for any TradingView anti-bot measures and adjust techniques

7. Develop the Decision Module with Strategy Interface
[ ] Define Strategy interface in decision/interfaces/ directory
[ ] Define LLMProvider interface in decision/interfaces/ directory
[ ] Implement DeepSeekProvider as the initial LLM provider
[ ] Create MCPIndicatorsStrategy implementation that leverages MCP signals
[ ] Create a BasicTAStrategy implementation for testing and fallback
[ ] Design a prompt template that incorporates MCP indicator signals
[ ] Implement logic to query for BTC-USD market data from multiple timeframes
[ ] Implement logic to generate trade decisions with confidence scores and reasoning
[ ] Store the LLM's decisions in the database with proper user_id association
[ ] Implement a simple scheduled job to run decision making every 15 minutes
[ ] Implement fallback logic for LLM unavailability
[ ] Add monitoring logic to evaluate and log strategy performance

8. Integrate CCXT MCP for Exchange Interactions
[x] Install and configure CCXT MCP according to documentation
[x] Implement credential provider system for dynamic credential management
[ ] Define ExchangeCommand interface in structuring/interfaces/ directory with CCXT MCP support
[ ] Implement CCXTMCPCommand as the primary command formatter for CEXs
[ ] Install and configure the jsonschema library for command validation
[ ] Create standardized intent objects compatible with CCXT MCP
[ ] Implement logic to send intent objects to CCXT MCP for command formatting
[ ] Define JSON schemas for validation before and after MCP processing
[ ] Create a simple risk parameter configuration for testing
[ ] Implement risk limits and validation logic
[ ] Add proper logging for command generation and validation

9. Develop the Trades Module with Trade Record Interface
[ ] Define TradeRecord interface in trades/interfaces/ directory
[ ] Create CEXTrade implementation for centralized exchanges via CCXT MCP
[ ] Implement source attribution tagging (e.g., 'ccxt-mcp', 'indicators-mcp')
[ ] Implement database operations for trade lifecycle management (create, update, close)
[ ] Ensure proper user_id association for all records
[ ] Store LLM reasoning and confidence scores with each trade record
[ ] Implement functions to retrieve active trades and history for the Decision Module
[ ] Add support for tracking trade performance metrics by source

10. Develop the Execution Module with Exchange Interface
[ ] Define Exchange interface in execution/interfaces/ directory
[ ] Define AuthenticationStrategy interface in execution/interfaces/ directory
[ ] Design database schema for securely storing user exchange API credentials
[ ] Implement encryption system for storing credentials in the database
[ ] Create database credential provider implementation for production use
[ ] Add credential rotation and management functionality
[ ] Implement CCXTAuthStrategy for CEX interactions via CCXT MCP
[ ] Create CCXTExchange implementation for routing commands to the CCXT MCP
[ ] Implement exchange-specific API key and authentication management
[ ] Implement dry-run mode for testing without actual transactions
[ ] Create functions to execute trades based on structuring module commands
[ ] Implement status monitoring and event handling for CEX trades
[ ] Add proper error handling and retry logic for failed transactions
[ ] Update trade records with transaction details and status changes

11. Implement Inter-Module Communication
[ ] Create a simple database-centric communication flow between modules
[ ] Ensure proper data flow from Extraction → Decision → Structuring → Execution → Trades
[ ] Configure MCP-specific communication patterns and data formats
[ ] Implement a main application entry point that coordinates module interactions
[ ] Create scheduled tasks for regular module execution (extraction, decision making)
[ ] Add proper error handling for module communication failures
[ ] Implement basic monitoring to verify data flow between modules, including MCP interactions

12. Testing and Validation
[x] Write basic tests for the YFinanceDataSource implementation
[x] Test the PandasTAIndicators implementation with sample data
[x] Create test fixtures for market data in different timeframes
[ ] Implement tests for Crypto Indicators MCP calculations and compare with pandas-ta results
[ ] Test CCXT MCP command generation and formatting
[ ] Test the Decision Module with sample market data inputs from multiple sources
[ ] Validate Structuring Module command generation and validation with CCXT MCP
[ ] Test Trades Module CRUD operations with source attribution
[ ] Implement a test mode for the Execution Module without real transactions
[ ] Create integration tests for the complete workflow with MCPs
[ ] Perform basic stress testing on the VM to ensure stability with MCP processes

13. End-to-End Testing and Dry Run
[ ] Implement an end-to-end dry-run mode for the entire system with MCP integration
[ ] Set up a test configuration with conservative risk parameters for CEX trading
[ ] Run the complete workflow with BTC-USD data and simulated trades via CCXT MCP
[ ] Monitor system resource usage during extended testing, including MCP processes
[ ] Validate multi-timeframe analysis works correctly with Crypto Indicators MCP
[ ] Test with simulated market conditions (trending, ranging, volatile)
[ ] Compare performance between MCP and traditional approaches

14. MVP Deployment and Configuration
[x] Create baseline configuration files for personal use
[ ] Configure MCP server connections in the environment settings
[ ] Implement basic environment settings for production
[ ] Deploy the application with MCP servers on the DigitalOcean VM
[ ] Set up monitoring for system performance and resource usage
[ ] Create a simple dashboard for tracking trades and performance
[ ] Implement cost tracking for LLM API usage and transaction fees
[ ] Configure regular database backups

15. Bubble.io Frontend Development
[ ] Finalize core Bubble.io application design and navigation flow
[ ] Implement user registration and authentication flows
[ ] Create agent configuration interface with intuitive UI elements
[ ] Build dashboard for monitoring agent performance and trades
[ ] Develop visualizations for key trading metrics and indicators
[ ] Implement account management and subscription handling
[ ] Set up notification system for important agent events

16. API and Bubble.io Integration
[ ] Finalize API specification documentation for all endpoints
[ ] Create comprehensive Bubble.io-to-backend integration flows
[ ] Implement user profile synchronization between Bubble.io and backend
[ ] Configure API connectors in Bubble.io for all backend endpoints
[ ] Create workflows for data retrieval and display in Bubble.io
[ ] Set up authentication flow (login, token generation, validation)
[ ] Implement robust error handling between systems
[ ] Test end-to-end workflows from Bubble.io to backend and back

17. Configuration Management Layer Implementation
[ ] Define ConfigurationProvider interface in config/interfaces/ directory
[ ] Implement BubbleConfigProvider for Bubble.io configuration synchronization
[ ] Implement FileConfigProvider as fallback or for testing
[ ] Implement MCPConfigurationManager for MCP-specific settings
[ ] Design schema validation for user configurations
[ ] Create default configurations for each module, including MCP settings
[ ] Implement secure credential management in the configuration system
[ ] Create API endpoints for adding, updating, and deleting exchange credentials
[ ] Add credential validation against exchange APIs before storing
[ ] Implement audit logging for credential access and modifications
[ ] Add configuration reloading support for updates without restart
[ ] Implement basic configuration validation and error handling
[ ] Build API endpoints for managing configurations
[ ] Test configuration changes from Bubble.io UI to backend modules

18. Platform Launch and Initial User Onboarding
[ ] Complete end-to-end testing of the platform
[ ] Create user documentation and tutorials
[ ] Set up initial subscription tiers and pricing
[ ] Implement analytics for user activity and platform usage
[ ] Develop onboarding flows for new users
[ ] Create demo agents for new users to explore
[ ] Establish support channels and FAQs
[ ] Launch beta program for initial users

19. Live Trading and Refinement
[ ] Start with minimal real trades on CEXs using conservative risk parameters
[ ] Implement a system for tracking actual trade performance and source attribution
[ ] Create a process for iteratively improving trading strategies
[ ] Monitor and optimize LLM prompts based on trade outcomes
[ ] Compare performance between MCP-based and traditional approaches
[ ] Refine risk parameters based on performance data
[ ] Implement regular system health checks and reporting
[ ] Develop user feedback mechanisms for strategy improvements

20. Performance Optimization
[ ] Analyze API response times and backend resource usage
[ ] Optimize MCP server configurations for the VM environment
[ ] Implement caching for frequent MCP and API requests
[ ] Create fallback procedures for service disruptions
[ ] Develop monitoring tools for system-wide performance metrics
[ ] Implement automatic scaling of resources based on usage patterns
[ ] Optimize Bubble.io workflows for performance

21. Platform Growth and Expansion
[ ] Expand exchange support through CCXT MCP
[ ] Develop advanced strategy templates for users
[ ] Implement advanced visualization and reporting tools
[ ] Add DEX support via AgentKit or custom MCPs
[ ] Design strategy marketplace for sharing trading strategies
[ ] Implement containerized architecture for scaling with separate MCP containers
[ ] Create API documentation for third-party integrations and custom MCP development
[ ] Develop affiliate and referral programs for user growth