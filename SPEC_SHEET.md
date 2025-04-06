ggbot Spec Sheet
Overview
Purpose:
ggbot is an autonomous AI trading agent platform that enables users to configure and deploy trading agents for cryptocurrency pairs across multiple exchanges, including Gains Network's gTrade platform. The system provides a modular architecture where users can customize data extraction sources, trading strategies, risk parameters, and target exchanges. It automates data extraction, trade decision‑making, JSON structuring, trade execution, and lifecycle management in a resource‑constrained environment (2 GB RAM, 1 vCPU) for the MVP, with plans to scale for multi-user deployment. This Spec Sheet outlines the technical architecture, codebase structure, database design, dependencies, and recommended development practices.

1. Technical Architecture
1.1 Modules
Extraction Module
Purpose:
Automate data gathering from multiple sources including TradingView (ggShot signals), fetch and compute historical indicators using yfinance + pandas‑ta, and retrieve real‑time prices from configured exchanges for precise trade entries.
Key Components:
DataSource Interface:
Abstract interface that all data providers implement, allowing users to select their preferred data sources.
Implementations: TradingViewDataSource, ExchangeAPIDataSource, ThirdPartyDataSource
IndicatorComputer Interface:
Abstraction for technical indicator calculation with implementations for different libraries.
Implementations: PandasTAIndicators, CustomIndicators

Key Points:
Browser‑Use (Playwright):
Functions: login(), navigateToChart(), configureIndicators(), extractDOMData().
Session Persistence: Maintains a persistent BrowserContext to reduce CAPTCHA triggers.
Uses TinyLlama-1.1B-Chat with Browser-use for headful login to TradingView
ChatGPT 4o (Vision):
Primary method for ggShot signal extraction via screenshot parsing of canvas-based chart data, with DOM parsing as a fallback if Vision is inefficient.
Historical Price Data & Technical Analysis:
yfinance: Fetch historical market data for multiple timeframes.
pandas‑ta: Computes technical indicators (RSI, MACD, EMA, Bollinger Bands, etc.) on DataFrames returned by yfinance.
Real‑Time Price Monitoring:
Query exchange APIs or contracts every 5 minutes for current market prices.
Ensures final trade decisions use fresh prices.
Timeframe‑Aligned Extraction:
Triggers data extraction immediately after each candle closes (e.g., every 15m).
Multi‑Timeframe Capability:
Even within a single‑pair MVP, code allows referencing multiple timeframes (e.g., 4h, 1h, 15m).
Resource Management:
Limit Playwright browser contexts to 1 for memory efficiency on a 2 GB/1 vCPU VM.

Decision Module
Purpose:
Analyze extracted data, maintain active trade oversight, and decide on opening, adjusting, or closing positions using configurable trading strategies and reasoning LLMs.
Key Components:
Strategy Interface:
Abstract base class for all trading strategies.
Implementations: GGShotStrategy, MovingAverageStrategy, RSIStrategy, CustomStrategy
LLMProvider Interface:
Abstraction for different LLM services.
Implementations: DeepSeekProvider, GPT4oProvider, Claude3Provider, LocalLLMProvider

Key Points:
LLM Integration:
Processes signals from configured data sources, computed indicators, and trade history.
Strategy Selection:
Users can select from pre-built strategies or create custom ones via configuration.
Ongoing Monitoring:
Evaluates active positions every 5 minutes for partial closes or updated stop‑losses.
Confidence Scores & Reasoning:
Each decision includes a numerical confidence score and textual reasoning stored in the database.
LLM Fallback Logic:
If the LLM is unavailable, revert to a minimal "no new trade" or "hold" strategy to avoid system stalls.

Structuring Module
Purpose:
Convert high‑level trade actions into validated JSON commands suitable for the target exchange API or contract.
Key Components:
ExchangeCommand Interface:
Abstract interface for different exchange-specific command formats.
Implementations: GTradeCommand, BinanceCommand, CustomExchangeCommand

Key Points:
Schema Enforcement:
Uses jsonschema to validate fields specific to each exchange format.
Risk Filtering:
Dynamically queries exchange APIs for limits (e.g., max leverage); falls back to local config for limits if retrieval fails.
User-Specific Risk Parameters:
Applies risk limits based on user configuration.
Final Command Output:
Produces exchange-compatible objects in the format required by the target exchange.

Trades Module
Purpose:
Maintain a detailed record of trades—both active and closed—including chat logs, confidence scores, partial closes, and final outcomes, with proper user data isolation.
Key Components:
TradeRecord Interface:
Abstraction for different trade record formats.
Implementations: GtradeTrade, BinanceTrade, GenericTrade

Key Points:
Trade Records & History:
Creates a new record when a trade opens, logs adjustments, and stores final results upon closure.
User Isolation:
Associates all records with user_id for multi-tenant support.
Chat History Management:
Appends the LLM's reasoning to a reasoning_log field.
Database Fields:
Includes user_id, confidence_score, timeframe, reasoning_log, and partial_close events.

Execution Module
Purpose:
Securely interact with configured exchange APIs or contracts, handling wallet management, transaction signing, and event monitoring.
Key Components:
Exchange Interface:
Abstract base class for all exchange adapters.
Implementations: GTradeExchange, BinanceExchange, CustomExchange
AuthenticationStrategy Interface:
Abstraction for different authentication methods.
Implementations: AgentKitStrategy, APIKeyStrategy, CustomAuthStrategy

Key Points:
Coinbase AgentKit:
Handles wallet integration for blockchain-based exchanges.
Exchange SDK Integration:
Uses appropriate SDKs or APIs for each supported exchange.
Event Monitoring:
Listens for confirmations, liquidations; includes fallback polling if websockets fail.
Batch API Calls:
Minimizes overhead by grouping exchange queries.

Configuration Management Layer
Purpose:
Manage user-specific settings for each module, enabling customization without code changes.
Key Components:
ConfigurationProvider Interface:
Abstract interface for configuration sources.
Implementations: FileConfigProvider, DatabaseConfigProvider, UIConfigProvider
ConfigurationValidator:
Ensures user configurations meet system requirements and are secure.

Key Points:
MVP Implementation:
Simple config.json file defining settings for each module.
Future Implementation:
Web-based UI for adjusting configurations, stored in database.
Configuration Categories:
Data Sources, Trading Strategies, Risk Parameters, Exchange Connections, LLM Settings.

1.2 Inter‑Module Interactions
Data Flow:
Extraction Module → Stores extracted data in the database, associating with user_id.
Decision Module → Pulls relevant data for the specified user to generate trade actions.
Structuring Module → Validates and formats the action into exchange-specific commands.
Execution Module → Executes commands on the target exchange, updating trade statuses.
Trades Module → Logs trade creation, updates, closures, and final summaries.
Configuration Flow:
Each module queries the Configuration Management Layer for user-specific settings.
Communication:
PostgreSQL is the primary data store for signals, trades, logs, etc.
In‑memory caching (Redis or Python dictionaries) for frequently accessed data.
Resource Management:
Constrain concurrency to maintain stability on the small VM during MVP phase.

2. Codebase Structure 
ggbot/
├── .env                      # Environment configuration (sensitive, ignored in Git)
├── .env.example              # Example environment config (safe for Git)
├── .gitignore                # Git ignore rules
├── .venv/                    # Python virtual environment (for dependency isolation)
├── README.md                 # Project overview & setup instructions
│
├── common/                   # Shared utilities
│   ├── config.py             # Configuration management
│   ├── db.py                 # Database connection & queries
│   └── logger.py             # Centralized logging
│
├── database/                 # Database migration scripts (PostgreSQL)
│   ├── 0001_create_tables.sql
│   ├── 0002_add_user_id.sql
│   └── 0003_create_market_data.sql
│
├── decision/                 # Decision & Monitoring Module
│   ├── interfaces/           # Strategy and LLM provider interfaces
│   ├── strategies/           # Trading strategy implementations
│   ├── llm_providers/        # LLM service integrations
│   └── decision_main.py      # Entry point
│
├── docs/                     # Documentation (architecture diagrams, design docs, logs)
│
├── extraction/               # Data Extraction Module
│   ├── interfaces/           # DataSource and IndicatorComputer interfaces
│   ├── sources/              # Data source implementations
│   │   ├── tradingview/      # TradingView-specific extraction code
│   │   ├── exchange_api/     # Direct exchange API data collection
│   │   └── third_party/      # Third-party data provider integrations
│   ├── indicators/           # Technical indicator implementations
│   └── extraction_main.py    # Entry point for extraction process
│
├── frontend/                 # Future React frontend for user configuration
│
├── logs/                     # Log files (e.g., from loguru)
│   └── ggbot.log
│
├── models/                   # Local LLM model files (if used)
│   ├── tinyllama-quantized.gguf  # Quantized GGUF model for login
│
├── execution/                # Execution Module (renamed from onchain)
│   ├── interfaces/           # Exchange and Authentication interfaces
│   ├── exchanges/            # Exchange adapter implementations
│   │   ├── gtrade/           # Gains Network gTrade integration
│   │   ├── binance/          # Binance exchange integration
│   │   └── custom/           # Template for custom exchange adapters
│   ├── auth/                 # Authentication strategy implementations
│   └── execution_main.py     # Entry point
│
├── requirements.txt          # Dependency list
│
├── structuring/              # Structuring Module
│   ├── interfaces/           # ExchangeCommand interface
│   ├── commands/             # Exchange-specific command implementations
│   ├── validators/           # JSON schema definitions for each exchange
│   └── structuring_main.py   # Entry point
│
├── tests/                    # Test suites
│   ├── extraction_tests.py   # Extraction module tests
│   ├── decision_tests.py     # Decision module tests
│   ├── structuring_tests.py  # Structuring module tests
│   ├── trades_tests.py       # Trades module tests
│   ├── execution_tests.py    # Execution module tests
│   └── config_tests.py       # Configuration tests
│
├── trades/                   # Trades Module
│   ├── interfaces/           # TradeRecord interface
│   ├── models/               # Exchange-specific trade record implementations
│   └── trades_main.py        # Trade lifecycle management
│
└── config/                   # Configuration Management Layer
    ├── interfaces/           # ConfigurationProvider interface
    ├── providers/            # Configuration provider implementations
    ├── validators/           # Configuration validation logic
    └── config_main.py        # Configuration management entry point

File Naming:
snake_case for Python files (e.g., extraction_main.py).
PascalCase for classes (e.g., TradeRecord).
Lowercase directory names with underscores if needed (e.g., exchange_api).

3. Database Design
3.1 Schema Definition
users
user_id (UUID, PK)
username (VARCHAR)
email (VARCHAR)
created_at (TIMESTAMP)
last_login (TIMESTAMP)

sessions
session_id (UUID, PK)
user_id (UUID, FK to users table)
cookie_data (JSONB)
created_at (TIMESTAMP)
expires_at (TIMESTAMP)

configurations
config_id (UUID, PK)
user_id (UUID, FK to users table)
config_type (VARCHAR) - 'extraction', 'decision', 'execution', etc.
config_data (JSONB)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)

trades
trade_id (UUID, PK)
user_id (UUID, FK to users table)
exchange (VARCHAR)
pair (VARCHAR)
timeframe (VARCHAR)
collateral_amount (NUMERIC)
leverage (INTEGER)
stop_loss (NUMERIC)
take_profit (NUMERIC)
confidence_score (NUMERIC)
reasoning_log (TEXT)
trade_status (VARCHAR)
created_at (TIMESTAMP)
closed_at (TIMESTAMP)
profit_loss (NUMERIC)

market_data
data_id (UUID, PK)
user_id (UUID, FK to users table)
source (VARCHAR)
pair (VARCHAR)
timeframe (VARCHAR)
indicators (JSONB)
raw_data (JSONB)
timestamp (TIMESTAMP)

logs
log_id (SERIAL, PK)
user_id (UUID, FK to users table)
module (VARCHAR)
log_level (VARCHAR)
message (TEXT)
timestamp (TIMESTAMP)

3.2 Indexing & Optimization
Indexes:
users.email for quick user lookup.
sessions.expires_at for session cleanup.
trades.user_id + trades.created_at for quick access to a user's recent trades.
market_data.user_id + market_data.pair + market_data.timeframe + market_data.timestamp for efficient data retrieval.
Database Strategy:
Partitioning if logs or market_data grow large.
Potential JSONB indexing on configuration_data and indicators for complex queries.

4. Dependencies & Libraries
4.1 External Libraries
Browser Automation:
Browser‑Use (Playwright)
Image Processing/OCR:
ChatGPT 4o (Vision); fallback to Tesseract if needed
Historical Data & TA:
yfinance for fetching historical market data
pandas‑ta for computing technical indicators (RSI, MACD, Bollinger Bands, etc.)
LLM Integration:
DeepSeek R1, GPT-4o, Claude 3, or equivalent reasoning models
JSON Validation:
jsonschema
Blockchain Interaction:
Coinbase AgentKit for secure wallet management/signing
Web3.py or Ethers.js for blockchain contract calls
Centralized Exchange APIs:
ccxt library for unified exchange API access
Logging & Monitoring:
loguru (Python) or similar
Environment Management:
python‑dotenv or equivalent
Database:
PostgreSQL
Redis (optional) for caching
Containerization:
Docker
Development Tools:
code‑server
Git
Frontend (Future):
React
Next.js
TailwindCSS

4.2 Versioning & Compatibility
Semantic Versioning:
Use MAJOR.MINOR.PATCH for each module and the overall system.
Dependency Management:
Pin exact versions in requirements.txt for stability.
Containerization:
Docker with multi‑stage builds for consistent builds.

5. Development Environment Setup
5.1 Required Tools
IDE/Editor:
code‑server (remote) or local VSCode/PyCharm
Version Control:
Git (GitHub/GitLab)
Containerization:
Docker for production and development
Build Tools:
Makefile or npm scripts for common tasks (build, test, lint)
5.2 Environment Configuration
Configuration Files:
.env.example and config.py for variables (API keys, endpoints)
Setup Documentation:
README.md with steps for repo cloning, dependency installation, Docker usage
Local Testing:
Optional Docker Compose for PostgreSQL, local blockchain, or other dependencies

6. Security Considerations
6.1 Data Protection
User Data Isolation:
Strict database-level isolation using user_id foreign keys.
Data at Rest:
Encrypt sensitive values or store them in a vault.
Data in Transit:
Use HTTPS/TLS for all API communications.
Secrets Management:
Avoid committing private keys to version control; .env for prototyping only.
6.2 Access Control
Authentication:
Required for any user interaction with the platform.
Authorization:
Ensure users can only access their own data and configurations.
Wallet Security:
Use Coinbase AgentKit's secure key storage for blockchain transactions.
Exchange API Security:
Store API keys securely with appropriate access restrictions.
Rate Limiting & Validation:
Protect from malicious or accidental overload.

7. Testing & Validation
7.1 Testing Strategy
Unit Testing:
Validate core logic in each module (extraction, decision, structuring, trades, execution).
Component Testing:
Test interfaces and their implementations independently.
Integration Testing:
Confirm seamless data flow across modules.
End‑to‑End (E2E) Testing:
Dry‑run mode simulating trades without real calls to exchanges.
Stress Testing:
Ensure stability on a 2 GB, 1 vCPU droplet with repeated extraction and LLM queries.
7.2 Test Environments
Testnet/Paper Trading:
Use exchange test environments or paper trading modes for real API/contract calls.
Continuous Integration (CI):
GitHub Actions, GitLab CI, or similar for automated testing.

8. Additional Considerations
8.1 Logging & Monitoring
Centralized Logging:
Send logs to a single sink (e.g., Graylog, ELK) and alert on critical events.
Resource Monitoring:
Tools like htop or Docker stats to ensure concurrency/memory usage remain within limits.
8.2 Documentation & Version Control
In‑Code Documentation:
Docstrings (PEP‑257) and thorough comments.
Interface Documentation:
Clear documentation for all interfaces and expected implementations.
Versioning:
Maintain a changelog, adopt feature branches, and merge to main when stable.

Conclusion
This Spec Sheet outlines a modular, customizable architecture for ggbot as a trading agent platform. The system is designed with clear interfaces in each module to support plugin-based customization, allowing users to select different data sources, trading strategies, and target exchanges. Key points include:

Multi-user support with proper data isolation
Flexible interface-based architecture for customization
Support for multiple exchanges beyond just Gains Network's gTrade
Configuration management for user-specific settings
Clear development roadmap from MVP to scalable platform

The MVP will focus on a single user (personal use) on a small VM, while establishing the architectural foundation for future scaling to a multi-user platform with a web-based configuration interface.