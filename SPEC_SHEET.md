ggbots Platform Spec Sheet
Overview
Purpose:ggbots is a platform for creating, customizing, and deploying autonomous AI trading agents for cryptocurrency pairs across multiple exchanges, with a primary focus on centralized exchanges (CEXs) for the MVP. The platform utilizes a hybrid architecture combining Bubble.io for frontend/user management and a dedicated backend for agent operations, providing users with an intuitive no-code interface to configure their trading agents while maintaining powerful backend processing capabilities.
The system provides a modular architecture where users can configure three agents: Extraction, Decision, and Trading. The Extraction Agent gathers market data from sources like TradingView (using Browser-Use), Indicators MCP, and yfinance. The Decision Agent analyzes this data using a reasoning LLM and a trading strategy from the config to make trade decisions. The Trading Agent executes these decisions via the CCXT MCP, monitors active trades, and provides updates back to the Decision Agent.
The first milestone in development is a reference agent implementation that demonstrates core functionality, followed by the Platform MVP that integrates Bubble.io for user management and configuration. This Spec Sheet outlines the technical architecture, codebase structure, database design, API integration, dependencies, and recommended development practices, with particular emphasis on the hybrid Bubble.io architecture and MCP integration for improved efficiency and scalability.

1. Technical Architecture
1.1 Hybrid Architecture Overview
The ggbots platform employs a hybrid architecture with two main components:

Frontend (Bubble.io):  

User interface and dashboard  
User registration and authentication  
Agent configuration interface  
Trading agent monitoring  
Strategy marketplace (future)  
Subscription and billing management


Backend (Custom Server):  

REST API endpoints for Bubble.io integration  
User authentication and ID validation  
Core agent processing modules  
Database for agent data and trade records  
MCP integrations for technical analysis and exchange interactions



This hybrid approach leverages Bubble.io's strengths in rapid UI development and user management while maintaining a powerful custom backend for compute-intensive agent operations.
1.2 API Integration
API Layer:  

RESTful API: JSON-based API endpoints for all backend functionality  
Authentication: JWT or token-based authentication using Bubble-generated user IDs  
Endpoints: Configuration, monitoring, execution, and data retrieval  
Versioning: API version control to ensure backward compatibility

User ID Flow:  

Bubble.io generates unique user IDs during registration  
These IDs are passed with all API requests to the backend  
Backend uses these IDs for data isolation and user-specific operations  
All database records are associated with the appropriate user ID

1.3 Core Modules
Extraction Module
Purpose:Gather market data from TradingView (using Browser-Use), Indicators MCP, yfinance, and real-time price data from the configured exchange for precise trade entries.
Key Components:  

DataSource Interface: Abstract interface that all data providers implement, allowing users to select their preferred data sources.  
Implementations: TradingViewDataSource, CryptoIndicatorsMCPDataSource, CCXTMCPDataSource, YFinanceDataSource (as fallback)


IndicatorComputer Interface: Abstraction for technical indicator calculation with implementations for different providers.  
Implementations: CryptoIndicatorsMCP, PandasTAIndicators (as fallback)



Key Points:  

Browser-Use (Playwright): Handles login, navigation, and data extraction from TradingView for ggShot signals. Maintains a persistent BrowserContext to reduce CAPTCHA triggers.  
MCP-Powered Technical Analysis: Crypto Indicators MCP provides 50+ technical indicators and trading strategies through a standardized interface.  
Fallback Systems: yfinance and pandas-ta maintained as fallback options and for validation during MCP testing.  
Real-Time Price Monitoring: Query exchange APIs via CCXT MCP every 5 minutes for current market prices.  
Timeframe-Aligned Extraction: Triggers data extraction immediately after each candle closes (e.g., every 15m).  
Multi-Timeframe Capability: Supports referencing multiple timeframes (e.g., 4h, 1h, 15m).  
Resource Management: Limits Playwright browser contexts to 1 for memory efficiency on a 2 GB/1 vCPU VM.

Decision Module
Purpose:Analyze market data from the Extraction Agent using a reasoning LLM and a trading strategy from the config to decide on opening, adjusting, or closing trades. Monitor active trades and adjust decisions based on updates from the Trading Agent.
Key Components:  

Strategy Interface: Abstract base class for all trading strategies.  
Implementations: MCPIndicatorsStrategy, GGShotStrategy, MovingAverageStrategy, RSIStrategy, CustomStrategy


LLMProvider Interface: Abstraction for different LLM services.  
Implementations: DeepSeekProvider, GPT4oProvider, Claude3Provider, LocalLLMProvider



Key Points:  

LLM Integration: Processes market data, MCP-computed indicators, and trade history using a reasoning LLM (e.g., DeepSeek R1, GPT-4o).  
MCP Indicator Integration: Incorporates Crypto Indicators MCP signals into strategy decision-making.  
Strategy Selection: Users can select from pre-built strategies or create custom ones via configuration.  
Ongoing Monitoring: Evaluates active positions every 5 minutes, adjusting based on Trading Agent updates.  
Confidence Scores & Reasoning: Each decision includes a numerical confidence score and textual reasoning stored in the database.  
LLM Fallback Logic: Reverts to a minimal "no new trade" or "hold" strategy if the LLM is unavailable.

Trading Module
Purpose:Structure trade decisions into exchange-specific commands using the CCXT MCP, execute trades on the configured exchange, monitor active trades, and provide updates back to the Decision Agent.
Key Components:  

interfaces.py: Defines interfaces for exchange commands, trade records, and authentication strategies.  
models/: Implementations of trade records for different exchange types.  
exchanges/: Exchange adapter implementations, including CCXT MCP integration.  
engine.py: Main trading engine that structures commands, executes trades, and monitors positions.  
lifecycle.py: Manages the full lifecycle of trades, from entry to exit.

Key Points:  

Intent Translation: Converts high-level LLM decisions into standardized intent objects compatible with CCXT MCP.  
CCXT MCP Integration: Routes commands and execution through the CCXT MCP for standardized exchange interactions.  
Schema Enforcement: Uses jsonschema to validate commands before and after MCP processing.  
Risk Filtering: Dynamically queries exchange APIs via CCXT for limits (e.g., max leverage); falls back to local config if retrieval fails.  
Exchange Event Monitoring: Listens for confirmations and liquidations; includes fallback polling if websockets fail.  
Batch API Calls: Minimizes overhead by grouping exchange queries through CCXT.

Configuration Management Layer
Purpose:Manage user-specific settings for each module, enabling customization without code changes, including MCP-specific configuration.
Key Components:  

interfaces.py: Defines the ConfigurationProvider interface.  
providers.py: Implementations for configuration sources (e.g., FileConfigProvider, DatabaseConfigProvider).  
validators.py: Ensures user configurations meet system requirements and are secure.  
config.py: Handles MCP-specific settings and connections.

Key Points:  

MVP Implementation: Simple config.json file defining settings for each module, including MCP server connections.  
Future Implementation: Web-based UI for adjusting configurations, stored in the database.  
Configuration Categories: Data Sources, Trading Strategies, Risk Parameters, Exchange Connections, LLM Settings, MCP Connections.  
MCP-Specific Configuration:  
Crypto Indicators MCP settings (exchange, timeframes, indicator selections)  
CCXT MCP settings (exchange selection, API keys, authentication)



1.4 Inter-Module Interactions & Data Flow
Bubble.io to Backend Flow:  

User Configuration: User configures agent via Bubble.io interface → Configuration sent to backend API → Configuration Manager processes and applies settings.  
Data Retrieval: User requests data via dashboard → API request to backend → Backend retrieves and returns data → Bubble.io displays results.  
Authentication: User logs in via Bubble.io → Auth token generated → Token used for all subsequent API requests.

Backend Core Modules Flow:  

Extraction Agent: Stores extracted market data in the database, associating with user_id.  
Decision Agent: Pulls relevant data, analyzes it with the LLM and strategy, and generates trade decisions.  
Trading Agent: Structures and executes trades via CCXT MCP, monitors positions, and updates the Decision Agent.

MCP Communication:  

Standardized interface for communication with Crypto Indicators MCP and CCXT MCP.  
Consistent data format for indicators regardless of source.

Data Storage and Security:  

Bubble.io: Stores user account data, preferences, and UI configurations with built-in security.  
Backend Database: PostgreSQL stores market data, trades, and logs.  
User Isolation: All data is associated with user_id for strict isolation.  
Caching: In-memory caching (Redis or Python dictionaries) for frequently accessed data.


2. Codebase Structure
2.1 Backend Structure
ggbots/
├── core/                     # Core platform infrastructure
│   ├── api/                  # API Layer for Bubble.io Integration
│   │   ├── __init__.py
│   │   ├── auth.py           # Authentication middleware
│   │   ├── routes/           # API endpoint routes
│   │   ├── schemas.py        # Request/response schemas
│   │   └── server.py         # API server setup
│   │
│   ├── common/               # Shared utilities
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration management
│   │   ├── db.py             # Database connection & queries
│   │   └── logger.py         # Centralized logging
│   │
│   ├── config/               # Configuration Management
│   │   ├── __init__.py
│   │   ├── default.json      # Default configuration values
│   │   ├── interfaces.py     # Configuration provider interfaces
│   │   ├── providers.py      # Configuration provider implementations
│   │   └── validators.py     # Configuration validation
│   │
│   ├── credentials/          # Secure credentials storage (gitignored)
│   │   ├── .gitignore
│   │   ├── README.md         # Instructions for setting up credentials
│   │   └── examples/         # Example credential files
│   │
│   ├── mcp/                  # MCP Integration Layer
│   │   ├── __init__.py
│   │   ├── base.py           # Base MCP client functionality
│   │   ├── indicators/       # Crypto Indicators MCP
│   │   ├── trading/          # CCXT MCP
│   │   └── config.py         # MCP configuration
│   │
│   └── utils/                # Utility scripts
│       ├── __init__.py
│       ├── browser.py        # Browser automation utilities
│       └── helpers.py        # General helper functions
│
├── decision/                 # Trading decision module
│   ├── __init__.py
│   ├── interfaces.py         # Strategy and LLM provider interfaces
│   ├── llm_providers/        # LLM implementations
│   ├── strategies/           # Trading strategy implementations
│   └── engine.py             # Main decision engine
│
├── extraction/               # Data extraction module
│   ├── __init__.py
│   ├── interfaces.py         # DataSource and IndicatorComputer interfaces
│   ├── indicators/           # Technical indicator implementations
│   ├── sources/              # Data source implementations
│   │   ├── tradingview.py    # TradingView data source
│   │   └── yfinance.py       # YFinance data source
│   └── engine.py             # Main extraction engine
│
├── trading/                  # Combined trading & trades module
│   ├── __init__.py
│   ├── interfaces.py         # Trading interfaces
│   ├── models/               # Trade record implementations
│   ├── exchanges/            # Exchange adapters
│   │   ├── __init__.py
│   │   └── ccxt_mcp.py       # CCXT MCP adapter
│   ├── engine.py             # Trading engine
│   └── lifecycle.py          # Trade lifecycle management
│
├── database/                 # Database migration scripts
│   ├── migrations/           # SQL migration files
│   └── README.md             # Database documentation
│
├── tests/                    # Test suites
│   ├── unit/                 # Unit tests for each module
│   ├── integration/          # Integration tests
│   ├── fixtures/             # Test data fixtures
│   └── conftest.py           # Test configuration
│
├── main.py                   # Application entry point
├── requirements.txt          # Dependencies
├── .env.example              # Environment variable template
├── .gitignore                # Git ignore rules
└── README.md                 # Project overview

2.2 Bubble.io Application Structure
ggbots-bubble/
├── pages/                    # Main application pages
│   ├── dashboard/            # User dashboard
│   ├── agent-config/         # Agent configuration interface
│   ├── monitoring/           # Trade monitoring and performance
│   ├── account/              # User account management
│   └── admin/                # Admin interface
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

Note: The Bubble.io structure is conceptual and will be implemented within Bubble.io's visual editor rather than as physical files.
File Naming:  

snake_case for Python files (e.g., extraction_main.py).  
PascalCase for classes (e.g., TradeRecord).  
Lowercase directory names with underscores if needed (e.g., exchange_api).


3. Database Design
3.1 Hybrid Data Architecture

Bubble.io Database: User accounts, profiles, subscriptions, UI preferences, agent metadata.  
Backend PostgreSQL Database: Market data, trade records, logs, operational data.

3.2 Backend Schema Definition

users:  

user_id (UUID, PK) - Uses Bubble-generated UUID  
username (VARCHAR)  
email (VARCHAR)  
created_at (TIMESTAMP)  
last_login (TIMESTAMP)  
bubble_data (JSONB) - Additional user data from Bubble.io


api_tokens:  

token_id (UUID, PK)  
user_id (UUID, FK to users)  
token (VARCHAR)  
created_at (TIMESTAMP)  
expires_at (TIMESTAMP)  
last_used (TIMESTAMP)


agents:  

agent_id (UUID, PK)  
user_id (UUID, FK to users)  
agent_name (VARCHAR)  
agent_description (TEXT)  
status (VARCHAR) - 'active', 'paused', etc.  
created_at (TIMESTAMP)  
updated_at (TIMESTAMP)


configurations:  

config_id (UUID, PK)  
user_id (UUID, FK to users)  
agent_id (UUID, FK to agents)  
config_type (VARCHAR) - 'extraction', 'decision', 'trading', etc.  
config_name (VARCHAR)  
config_data (JSONB)  
created_at (TIMESTAMP)  
updated_at (TIMESTAMP)  
sync_status (VARCHAR) - Status of synchronization with Bubble


trades:  

trade_id (UUID, PK)  
user_id (UUID, FK to users)  
agent_id (UUID, FK to agents)  
config_id (UUID, FK to configurations)  
exchange (VARCHAR)  
pair (VARCHAR)  
timeframe (VARCHAR)  
collateral_amount (NUMERIC)  
leverage (INTEGER)  
stop_loss (NUMERIC)  
take_profit (NUMERIC)  
confidence_score (NUMERIC)  
reasoning_log (TEXT)  
source_tag (VARCHAR) - e.g., 'ccxt-mcp', 'indicators-mcp'  
trade_status (VARCHAR)  
created_at (TIMESTAMP)  
closed_at (TIMESTAMP)  
profit_loss (NUMERIC)


market_data:  

data_id (SERIAL, PK)  
user_id (UUID, FK to users)  
agent_id (UUID, FK to agents)  
source (VARCHAR)  
symbol (VARCHAR)  
timeframe (VARCHAR)  
data_type (VARCHAR)  
indicators (JSONB)  
raw_data (JSONB)  
updated_at (TIMESTAMP)


logs:  

log_id (SERIAL, PK)  
user_id (UUID, FK to users)  
agent_id (UUID, FK to agents)  
module (VARCHAR)  
log_level (VARCHAR)  
message (TEXT)  
timestamp (TIMESTAMP)


api_requests:  

request_id (UUID, PK)  
user_id (UUID, FK to users)  
endpoint (VARCHAR)  
method (VARCHAR)  
status_code (INTEGER)  
response_time (INTEGER) - in milliseconds  
timestamp (TIMESTAMP)



3.3 Indexing & Optimization
Backend Indexes:  

users.user_id  
api_tokens.user_id + api_tokens.expires_at  
api_tokens.token  
agents.user_id  
trades.user_id + trades.created_at  
trades.agent_id  
market_data.user_id + market_data.symbol + market_data.timeframe + market_data.updated_at  
logs.user_id + logs.timestamp  
api_requests.user_id + api_requests.timestamp

Bubble.io Optimization:  

Use Bubble's built-in indexing for frequently queried fields.  
Implement efficient data loading strategies for dashboards.  
Leverage Bubble's caching capabilities.

Database Strategy:  

Backend-Bubble Synchronization: Minimize data duplication; store technical data in PostgreSQL and user-facing data in Bubble.  
Partitioning: Time-based for logs and market_data; user-based for multi-tenant isolation at scale.  
Optimization: JSONB indexing on config_data and indicators, materialized views for aggregates, connection pooling, caching layer.


4. Dependencies & Libraries
4.1 External Libraries
Backend Components:  

API Framework: FastAPI, uvicorn, pydantic, python-jose  
Browser Automation: Browser-Use (built on Playwright) for TradingView analysis  
MCPs: Crypto Indicators MCP, CCXT MCP  
Historical Data & TA: yfinance, pandas-ta (fallback)  
LLM Integration: DeepSeek R1, GPT-4o, Claude 3  
JSON Validation: jsonschema  
Database: PostgreSQL, SQLAlchemy, Alembic, Redis  
Logging & Monitoring: loguru, prometheus_client, Grafana (optional)  
Environment Management: python-dotenv  
Containerization: Docker, Docker Compose

Frontend Components (Bubble.io):  

Bubble.io Core: Bubble.io platform, Responsive Design plugin  
API Integration: API Connector plugin, Toolbox plugin  
Data Visualization: Chart.js plugin, Data Visualization plugin  
Payment Processing: Stripe plugin, PayPal plugin (optional)  
User Management: Auth0 plugin (optional), Email plugin  
Design Elements: Bootstrap (optional), Custom CSS, Icon sets

4.2 Versioning & Compatibility

Semantic Versioning: MAJOR.MINOR.PATCH for modules and system  
Dependency Management: Pin versions in requirements.txt  
Containerization: Docker with multi-stage builds


5. Development Environment Setup
5.1 Required Tools

IDE/Editor: code-server (remote) or local VSCode/PyCharm  
Version Control: Git (GitHub/GitLab)  
Containerization: Docker  
Build Tools: Makefile or npm scripts

5.2 Environment Configuration

Configuration Files: .env.example, core/common/config.py for variables (API keys, endpoints)  
Setup Documentation: README.md with steps for repo cloning, dependency installation, Docker usage  
Local Testing: Optional Docker Compose for PostgreSQL and Redis


6. Security Considerations
6.1 Data Protection

User Data Isolation: Strict database-level isolation using user_id foreign keys  
Data at Rest: Encrypt sensitive values or store them in a vault  
Data in Transit: Use HTTPS/TLS for all API communications  
Secrets Management: Avoid committing private keys to version control; use .env for prototyping

6.2 Access Control

Authentication: Required for all user interactions  
Authorization: Users can only access their own data and configurations  
Exchange API Security: Store API keys securely with appropriate access restrictions  
Rate Limiting: Protect from malicious or accidental overload


7. Testing & Validation
7.1 Testing Strategy

Unit Testing: Validate core logic in Extraction, Decision, and Trading modules  
Component Testing: Test interfaces and implementations independently  
Integration Testing: Confirm seamless data flow across modules  
End-to-End (E2E) Testing: Dry-run mode simulating trades without real exchange calls  
Stress Testing: Ensure stability on a 2 GB, 1 vCPU VM

7.2 Test Environments

Testnet/Paper Trading: Use exchange test environments or paper trading modes  
Continuous Integration (CI): GitHub Actions or GitLab CI for automated testing


8. Additional Considerations
8.1 Logging & Monitoring

Centralized Logging: Send logs to a single sink (e.g., Graylog, ELK) and alert on critical events  
Resource Monitoring: Use htop or Docker stats to monitor concurrency/memory usage

8.2 Documentation & Version Control

In-Code Documentation: Docstrings (PEP-257) and thorough comments  
Interface Documentation: Clear documentation for all interfaces  
Versioning: Maintain a changelog, adopt feature branches, and merge to main when stable


Conclusion
This updated Spec Sheet outlines a comprehensive hybrid architecture for the ggbots platform, combining Bubble.io for frontend/user management with a custom backend for agent operations. The platform leverages Model Context Protocols (MCPs) for standardized indicator calculations and exchange interactions, providing users with an intuitive no-code interface to configure their trading agents. The development approach starts with a reference agent implementation, followed by the Platform MVP with Bubble.io integration, focusing on centralized exchanges (CEXs) initially, with plans for decentralized exchange (DEX) support in future phases.


