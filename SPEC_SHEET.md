ggbots Platform Spec Sheet
Overview
Purpose:
ggbots is a platform for creating, customizing, and deploying autonomous AI trading agents for cryptocurrency pairs across multiple exchanges, with a primary focus on centralized exchanges (CEXs) for the MVP. The platform utilizes a hybrid architecture combining Bubble.io for frontend/user management and a dedicated backend for agent operations, providing users with an intuitive no-code interface to configure their trading agents while maintaining powerful backend processing capabilities.

The system provides a modular architecture where users can customize data extraction sources, trading strategies, risk parameters, and target exchanges, leveraging Model Context Protocols (MCPs) for standardized indicator calculations and exchange interactions. It automates data extraction, trade decision‑making, JSON structuring, trade execution, and lifecycle management, with separate scaling considerations for the Bubble.io frontend and the agent processing backend.

The first milestone in development is a reference agent implementation that demonstrates core functionality, followed by the Platform MVP that integrates Bubble.io for user management and configuration. This Spec Sheet outlines the technical architecture, codebase structure, database design, API integration, dependencies, and recommended development practices, with particular emphasis on the hybrid Bubble.io architecture and MCP integration for improved efficiency and scalability.

1. Technical Architecture
1.1 Hybrid Architecture Overview
The ggbots platform employs a hybrid architecture with two main components:

Frontend (Bubble.io):
- User interface and dashboard
- User registration and authentication
- Agent configuration interface
- Trading agent monitoring
- Strategy marketplace (future)
- Subscription and billing management

Backend (Custom Server):
- REST API endpoints for Bubble.io integration
- User authentication and ID validation
- Core agent processing modules
- Database for agent data and trade records
- MCP integrations for technical analysis and exchange interactions

This hybrid approach leverages Bubble.io's strengths in rapid UI development, user management, and permissions, while maintaining a powerful custom backend for the compute-intensive agent operations.

1.2 API Integration
API Layer:
- RESTful API: JSON-based API endpoints for all backend functionality
- Authentication: JWT or token-based authentication using Bubble-generated user IDs
- Endpoints: Configuration, monitoring, execution, and data retrieval
- Versioning: API version control to ensure backward compatibility

User ID Flow:
- Bubble.io generates unique user IDs during registration
- These IDs are passed with all API requests to the backend
- Backend uses these IDs for data isolation and user-specific operations
- All database records are associated with the appropriate user ID

1.3 Core Modules
Extraction Module
Purpose:
Automate data gathering from multiple sources including TradingView (ggShot signals), leverage the Crypto Indicators MCP for comprehensive technical analysis, and retrieve real‑time prices from configured exchanges for precise trade entries.
Key Components:
DataSource Interface:
Abstract interface that all data providers implement, allowing users to select their preferred data sources.
Implementations: TradingViewDataSource, CryptoIndicatorsMCPDataSource, CCXTMCPDataSource, YFinanceDataSource (as fallback)
IndicatorComputer Interface:
Abstraction for technical indicator calculation with implementations for different providers.
Implementations: CryptoIndicatorsMCP, PandasTAIndicators (as fallback)

Key Points:
Browser‑Use (Playwright):
Functions: login(), navigateToChart(), configureIndicators(), extractDOMData().
Session Persistence: Maintains a persistent BrowserContext to reduce CAPTCHA triggers.
Uses TinyLlama-1.1B-Chat with Browser-use for headful login to TradingView
ChatGPT 4o (Vision):
Primary method for ggShot signal extraction via screenshot parsing of canvas-based chart data, with DOM parsing as a fallback if Vision is inefficient.
MCP-Powered Technical Analysis:
Crypto Indicators MCP: Provides 50+ technical indicators and trading strategies through a standardized interface.
Fallback Systems: yfinance and pandas-ta maintained as fallback options and for validation during MCP testing.
Real‑Time Price Monitoring:
Query exchange APIs via CCXT MCP every 5 minutes for current market prices.
Ensures final trade decisions use fresh prices.
Timeframe‑Aligned Extraction:
Triggers data extraction immediately after each candle closes (e.g., every 15m).
Multi‑Timeframe Capability:
Even within a single‑pair MVP, code allows referencing multiple timeframes (e.g., 4h, 1h, 15m).
Resource Management:
Limit Playwright browser contexts to 1 for memory efficiency on a 2 GB/1 vCPU VM.
Leverage MCPs to reduce computational load on the VM.

Decision Module
Purpose:
Analyze extracted data from all sources (including MCP-provided indicators), maintain active trade oversight, and decide on opening, adjusting, or closing positions using configurable trading strategies and reasoning LLMs.
Key Components:
Strategy Interface:
Abstract base class for all trading strategies.
Implementations: MCPIndicatorsStrategy, GGShotStrategy, MovingAverageStrategy, RSIStrategy, CustomStrategy
LLMProvider Interface:
Abstraction for different LLM services.
Implementations: DeepSeekProvider, GPT4oProvider, Claude3Provider, LocalLLMProvider

Key Points:
LLM Integration:
Processes signals from configured data sources, MCP-computed indicators, and trade history.
MCP Indicator Integration:
Incorporates Crypto Indicators MCP signals into strategy decision-making.
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
Convert high‑level trade actions into validated JSON commands suitable for the target exchange API, leveraging the CCXT MCP for CEX-specific formatting.
Key Components:
ExchangeCommand Interface:
Abstract interface for different exchange-specific command formats.
Implementations: CCXTMCPCommand (primary for CEXs), GTradeCommand (for future DEX support)
CCXT MCP Integration:
Routes commands through the CCXT MCP for standardized exchange interactions.

Key Points:
Intent Translation:
Converts high-level LLM decisions into standardized intent objects compatible with CCXT MCP.
CCXT MCP Processing:
Offloads exchange-specific command formatting to the CCXT MCP.
Schema Enforcement:
Uses jsonschema to validate fields before and after MCP processing.
Risk Filtering:
Dynamically queries exchange APIs via CCXT for limits (e.g., max leverage); falls back to local config for limits if retrieval fails.
User-Specific Risk Parameters:
Applies risk limits based on user configuration.
Final Command Output:
Produces exchange-compatible objects in the format required by the target exchange via CCXT MCP.

Trades Module
Purpose:
Maintain a detailed record of trades—both active and closed—including chat logs, confidence scores, partial closes, and final outcomes, with proper user data isolation and source attribution for MCP-initiated trades.
Key Components:
TradeRecord Interface:
Abstraction for different trade record formats.
Implementations: CEXTrade (via CCXT MCP), GtradeTrade (for future DEX support), GenericTrade

Key Points:
Trade Records & History:
Creates a new record when a trade opens, logs adjustments, and stores final results upon closure.
Source Attribution:
Tags trades with their source (e.g., 'ccxt-mcp', 'indicators-mcp') for performance tracking.
User Isolation:
Associates all records with user_id for multi-tenant support.
Chat History Management:
Appends the LLM's reasoning to a reasoning_log field.
Database Fields:
Includes user_id, confidence_score, timeframe, reasoning_log, source_tag, and partial_close events.

Execution Module
Purpose:
Securely interact with configured exchange APIs, primarily using the CCXT MCP for CEX interactions in the MVP phase, with future support for DEXs.
Key Components:
Exchange Interface:
Abstract base class for all exchange adapters.
Implementations: CCXTExchange (primary for CEXs), GTradeExchange (for future DEX support)
AuthenticationStrategy Interface:
Abstraction for different authentication methods.
Implementations: CCXTAuthStrategy (for CEXs), AgentKitStrategy (for future DEX support)

Key Points:
CCXT MCP Integration:
Primary method for interacting with CEX APIs, handling dozens of exchanges through a standardized interface.
CEX Prioritization:
Routes trading commands primarily through the CCXT MCP for the MVP phase.
Coinbase AgentKit:
Reserved for future DEX support, handling wallet integration for blockchain-based exchanges.
Exchange Event Monitoring:
Listens for confirmations, liquidations; includes fallback polling if websockets fail.
Batch API Calls:
Minimizes overhead by grouping exchange queries through CCXT.

Configuration Management Layer
Purpose:
Manage user-specific settings for each module, enabling customization without code changes, including MCP-specific configuration.
Key Components:
ConfigurationProvider Interface:
Abstract interface for configuration sources.
Implementations: FileConfigProvider, DatabaseConfigProvider, UIConfigProvider
ConfigurationValidator:
Ensures user configurations meet system requirements and are secure.
MCPConfigurationManager:
Handles MCP-specific settings and connections.

Key Points:
MVP Implementation:
Simple config.json file defining settings for each module, including MCP server connections.
Future Implementation:
Web-based UI for adjusting configurations, stored in database.
Configuration Categories:
Data Sources, Trading Strategies, Risk Parameters, Exchange Connections, LLM Settings, MCP Connections.
MCP-Specific Configuration:
Crypto Indicators MCP settings (exchange, timeframes, indicator selections)
CCXT MCP settings (exchange selection, API keys, authentication)

1.4 Inter‑Module Interactions & Data Flow
Bubble.io to Backend Flow:
- User Configuration: User configures agent via Bubble.io interface → Configuration sent to backend API → Configuration Manager processes and applies settings
- Data Retrieval: User requests data via dashboard → API request to backend → Backend retrieves and returns data → Bubble.io displays results
- Authentication: User logs in via Bubble.io → Auth token generated → Token used for all subsequent API requests

Backend Core Modules Flow:
- Extraction Module → Stores extracted data from ggShot, TradingView, and Indicators MCP in the database, associating with Bubble-generated user_id
- Decision Module → Pulls relevant data for the specified user, including MCP-calculated indicators, to generate trade actions
- Structuring Module → Sends LLM intent to CCXT MCP for exchange-specific command formatting, then validates the resulting commands
- Execution Module → Routes commands to CCXT MCP for CEX execution, updating trade statuses
- Trades Module → Logs trade creation, updates, closures, and final summaries, tagging trades with their source (e.g., 'ccxt-mcp')

Configuration Flow:
- Bubble.io UI: User configures agent settings via intuitive interface
- API Transfer: Configuration sent to backend via API with user ID
- Backend Processing: Configuration Management Layer validates and applies settings
- Module Distribution: Each module queries the Configuration Management Layer for user-specific settings, including MCP-specific configurations

MCP Communication:
- Standardized interface for communication with Crypto Indicators MCP and CCXT MCP
- Consistent data format for indicators regardless of source (direct calculation or MCP-provided)

Data Storage and Security:
- Bubble.io: Stores user account data, preferences, and UI configurations with built-in security
- Backend Database: PostgreSQL is the primary data store for signals, trades, logs, etc.
- User Isolation: All data is associated with Bubble-generated user IDs for strict isolation
- Caching: In‑memory caching (Redis or Python dictionaries) for frequently accessed data

Resource Management:
- Backend Scaling: Initially constrained concurrency during reference implementation, expanding for platform MVP
- Load Distribution: Separate considerations for Bubble.io scaling and backend processing
- Efficiency: Leverage MCPs to reduce computational load for technical analysis and exchange interactions

2. Codebase Structure 
2.1 Backend Structure
ggbots-backend/
├── .env                      # Environment configuration (sensitive, ignored in Git)
├── .env.example              # Example environment config (safe for Git)
├── .gitignore                # Git ignore rules
├── .venv/                    # Python virtual environment (for dependency isolation)
├── README.md                 # Project overview & setup instructions
│
├── api/                      # API Layer for Bubble.io Integration
│   ├── auth.py               # Authentication and user validation
│   ├── routes/               # API endpoint routes
│   │   ├── config_routes.py  # Configuration API endpoints
│   │   ├── data_routes.py    # Data retrieval endpoints
│   │   ├── agent_routes.py   # Agent control endpoints
│   │   └── status_routes.py  # Status and monitoring endpoints
│   ├── serializers/          # Request/response serialization
│   ├── validators/           # Input validation
│   └── api_main.py           # API server entry point
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
│   ├── api/                  # API documentation
│   └── bubble/               # Bubble.io integration documentation
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
├── logs/                     # Log files (e.g., from loguru)
│   └── ggbots.log
│
├── mcp/                      # MCP Integration
│   ├── crypto_indicators/    # Crypto Indicators MCP integration
│   ├── ccxt/                 # CCXT MCP integration
│   └── mcp_base.py           # Base MCP communication utilities
│
├── models/                   # Local LLM model files (if used)
│   ├── tinyllama-quantized.gguf  # Quantized GGUF model for login
│
├── execution/                # Execution Module
│   ├── interfaces/           # Exchange and Authentication interfaces
│   ├── exchanges/            # Exchange adapter implementations
│   │   ├── ccxt/             # CCXT MCP integration for CEXs
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
│   ├── api_tests.py          # API integration tests
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
    ├── bubble_sync/          # Bubble.io configuration synchronization
    ├── validators/           # Configuration validation logic
    └── config_main.py        # Configuration management entry point

2.2 Bubble.io Application Structure
ggbots-bubble/
├── pages/                    # Main application pages
│   ├── dashboard/            # User dashboard
│   ├── agent-config/         # Agent configuration interface
│   ├── monitoring/           # Trade monitoring and performance
│   ├── account/              # User account management
│   └── admin/                # Admin interface (for platform operators)
│
├── api-connections/          # Backend API connection configurations
│   ├── auth/                 # Authentication endpoints
│   ├── config/               # Configuration endpoints
│   ├── data/                 # Data retrieval endpoints
│   └── control/              # Agent control endpoints
│
├── workflows/                # Bubble workflow configurations
│   ├── user-management/      # Registration, login, account management
│   ├── agent-creation/       # Trading agent setup and configuration
│   ├── monitoring/           # Performance monitoring and notifications
│   └── billing/              # Subscription and payment processing
│
├── database/                 # Bubble database schema
│   ├── users/                # User data structure
│   ├── agents/               # Agent configurations
│   ├── subscriptions/        # Subscription data
│   └── preferences/          # User preferences
│
└── plugins/                  # Bubble plugins used
    ├── api-connector/        # API integration plugins
    ├── charting/             # Trading chart visualization
    ├── payments/             # Payment processing
    └── notifications/        # User notifications

Note: The Bubble.io structure is conceptual and will be implemented within the Bubble.io platform's visual editor rather than as physical files.

File Naming:
snake_case for Python files (e.g., extraction_main.py).
PascalCase for classes (e.g., TradeRecord).
Lowercase directory names with underscores if needed (e.g., exchange_api).

3. Database Design
3.1 Hybrid Data Architecture

Bubble.io Database:
- User accounts and authentication
- User profile information
- Subscription and billing data
- UI preferences and settings
- Agent configuration metadata
- Access control and permissions

Backend PostgreSQL Database:
- Technical data for agent operations
- Market data and indicators
- Trade records and performance
- Operational logs and monitoring
- Agent execution details

3.2 Backend Schema Definition
Using Existing Schema with Bubble.io Integration:

users (Existing - Updated)
user_id (UUID, PK) - Will use Bubble-generated UUID
username (VARCHAR) - Username from Bubble.io
email (VARCHAR) - Email from Bubble.io
created_at (TIMESTAMP)
last_login (TIMESTAMP)
bubble_data (JSONB) - Additional user data from Bubble.io (new field)

api_tokens (New)
token_id (UUID, PK)
user_id (UUID, FK to users table)
token (VARCHAR)
created_at (TIMESTAMP)
expires_at (TIMESTAMP)
last_used (TIMESTAMP)

agents (New)
agent_id (UUID, PK)
user_id (UUID, FK to users table)
agent_name (VARCHAR)
agent_description (TEXT)
status (VARCHAR) - 'active', 'paused', etc.
created_at (TIMESTAMP)
updated_at (TIMESTAMP)

configurations (Existing - Updated)
config_id (UUID, PK)
user_id (UUID, FK to users table)
agent_id (UUID, FK to agents table) - For users with multiple agents
config_type (VARCHAR) - 'extraction', 'decision', 'execution', etc.
config_name (VARCHAR)
config_data (JSONB)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
sync_status (VARCHAR) - Status of synchronization with Bubble (new field)

trades (Existing - Updated)
trade_id (UUID, PK)
user_id (UUID, FK to users table)
agent_id (UUID, FK to agents table) - For users with multiple agents (new field)
config_id (UUID, FK to configurations table)
exchange (VARCHAR)
pair (VARCHAR)
timeframe (VARCHAR)
collateral_amount (NUMERIC)
leverage (INTEGER)
stop_loss (NUMERIC)
take_profit (NUMERIC)
confidence_score (NUMERIC)
reasoning_log (TEXT)
source_tag (VARCHAR) - e.g., 'ccxt-mcp', 'indicators-mcp' (new field)
trade_status (VARCHAR)
created_at (TIMESTAMP)
closed_at (TIMESTAMP)
profit_loss (NUMERIC)

market_data (Existing - Updated)
data_id (SERIAL, PK)
user_id (UUID, FK to users table)
agent_id (UUID, FK to agents table) - For users with multiple agents (new field)
source (VARCHAR)
symbol (VARCHAR)
timeframe (VARCHAR)
data_type (VARCHAR)
indicators (JSONB)
raw_data (JSONB)
updated_at (TIMESTAMP)

logs (Existing - Updated)
log_id (SERIAL, PK)
user_id (UUID, FK to users table)
agent_id (UUID, FK to agents table) - For users with multiple agents (new field)
module (VARCHAR)
log_level (VARCHAR)
message (TEXT)
timestamp (TIMESTAMP)

api_requests (New)
request_id (UUID, PK)
user_id (UUID, FK to users table)
endpoint (VARCHAR)
method (VARCHAR)
status_code (INTEGER)
response_time (INTEGER) - in milliseconds
timestamp (TIMESTAMP)

3.3 Indexing & Optimization
Backend Indexes:
users.user_id for quick user lookup.
api_tokens.user_id + api_tokens.expires_at for efficient token validation.
api_tokens.token for token lookup during authentication.
agents.user_id for filtering user's agents.
trades.user_id + trades.created_at for quick access to a user's recent trades.
trades.agent_id for filtering by specific agent.
market_data.user_id + market_data.symbol + market_data.timeframe + market_data.updated_at for efficient data retrieval.
logs.user_id + logs.timestamp for user-specific log retrieval.
api_requests.user_id + api_requests.timestamp for API usage monitoring.

Bubble.io Optimization:
Use Bubble's built-in indexing for frequently queried fields.
Implement efficient data loading strategies for dashboards.
Leverage Bubble's caching capabilities for frequently accessed data.

Database Strategy:
Backend-Bubble Synchronization:
- Minimize data duplication between systems
- Store technical data in PostgreSQL and user-facing data in Bubble
- Implement efficient data synchronization strategies

Partitioning:
- Time-based partitioning for logs and market_data as they grow
- User-based partitioning for multi-tenant isolation at scale

Optimization:
- JSONB indexing on configuration_data and indicators for complex queries
- Materialized views for frequently accessed aggregate data
- Connection pooling for efficient API request handling
- Caching layer for frequently accessed data

4. Dependencies & Libraries
4.1 External Libraries

Backend Components:
API Framework:
- FastAPI for high-performance API development
- uvicorn for ASGI server
- pydantic for data validation and serialization
- python-jose for JWT authentication

Browser Automation:
- Browser‑Use (Playwright)

Image Processing/OCR:
- ChatGPT 4o (Vision); fallback to Tesseract if needed

Model Context Protocols (MCPs):
- Crypto Indicators MCP for technical analysis and indicators
- CCXT MCP for exchange interactions and trade execution

Historical Data & TA (Fallback/Validation):
- yfinance for fetching historical market data
- pandas‑ta for computing technical indicators (as fallback and validation)

LLM Integration:
- DeepSeek R1, GPT-4o, Claude 3, or equivalent reasoning models

JSON Validation:
- jsonschema

Blockchain Interaction (Future Phase):
- Coinbase AgentKit for secure wallet management/signing (reserved for DEX support)
- Web3.py or Ethers.js for blockchain contract calls (reserved for DEX support)

Centralized Exchange APIs:
- CCXT MCP for unified exchange API access

Logging & Monitoring:
- loguru (Python) for structured logging
- prometheus_client for metrics collection
- Grafana for visualization (optional)

Environment Management:
- python‑dotenv for environment variables

Database:
- PostgreSQL for backend data storage
- SQLAlchemy for ORM
- Alembic for migrations
- Redis for caching and rate limiting

Containerization:
- Docker for deployment
- Docker Compose for local development

Development Tools:
- code‑server
- Git

Frontend Components (Bubble.io):
Bubble.io Core:
- Bubble.io platform
- Responsive Design plugin

API Integration:
- API Connector plugin
- Toolbox plugin for advanced data manipulation

Data Visualization:
- Chart.js plugin
- Data Visualization plugin

Payment Processing:
- Stripe plugin
- PayPal plugin (optional)

User Management:
- Auth0 plugin (optional, for advanced authentication needs)
- Email plugin for notifications

Design Elements:
- Bootstrap for UI components (optional)
- Custom CSS for styling
- Icon sets for visual elements

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
This Spec Sheet outlines a comprehensive hybrid architecture for the ggbots platform, combining Bubble.io for frontend/user management with a custom backend for agent operations. The platform leverages Model Context Protocols (MCPs) for standardized indicator calculations and exchange interactions, providing users with an intuitive no-code interface to configure their trading agents while maintaining powerful backend processing capabilities.

Key architectural features include:

Hybrid Architecture:
- Bubble.io frontend for user management, configuration, and monitoring
- Custom backend for agent processing, data storage, and exchange interactions
- RESTful API integration between Bubble.io and backend services

Multi-user Platform from Day One:
- Built-in user management and authentication via Bubble.io
- Secure data isolation using Bubble-generated user IDs throughout the system
- Scalable infrastructure supporting multiple concurrent users

Flexible Agent Customization:
- Modular architecture with clear interfaces for each component
- Integration of Crypto Indicators MCP for technical analysis
- CCXT MCP for standardized CEX interactions
- User-configurable trading strategies and risk parameters

Technical Innovations:
- Trade source attribution for performance tracking and analysis
- Unified data format across different indicator sources
- Optimized database schema for efficient data retrieval and storage
- Comprehensive API layer for seamless Bubble-backend integration

Development Approach:
- First milestone: Reference agent implementation to validate core functionality
- Platform MVP: Integration with Bubble.io for user management and configuration
- Growth phase: Expanded features, exchange support, and strategy marketplace

The platform's development starts with a reference agent implementation to validate the core modules, followed by the Platform MVP with Bubble.io integration, focusing on centralized exchanges (CEXs) initially with plans for decentralized exchange (DEX) support in future phases. This approach accelerates time-to-market while ensuring the platform can scale with user needs and evolve with market conditions.