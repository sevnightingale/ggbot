# ggbots Platform Codebase Structure

This document outlines the proposed codebase structure for the ggbots platform, focusing on a cleaner, highly consolidated organization with MCP integration.

## Design Principles

1. **Modularity**: Clear separation of concerns
2. **Consistency**: Standardized naming and patterns
3. **Simplicity**: Minimal top-level directories with clear purpose
4. **MCP-Friendly**: Designed for easy integration with Model Context Protocols

## Proposed Structure

```
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
```

## Key Changes from Current Structure

1. **Consolidated Core Infrastructure**:
   - Created a `core/` directory containing all platform infrastructure components
   - Moved `api/`, `common/`, `config/`, `credentials/`, `mcp/`, and `utils/` under this umbrella
   - Cleaner top-level directory structure

2. **Combined Trading & Trades**:
   - Merged `trades/` and `trading/` into a single `trading/` module
   - Handles both trade execution via MCPs and trade lifecycle management
   - Eliminates duplication and simplifies the trading flow

3. **Standardized Interfaces**:
   - Moved interfaces to the top level of each module as `interfaces.py`
   - Consistent naming patterns across all modules

4. **Simplified Organization**:
   - Flattened deeply nested directories
   - Consolidated duplicate files (e.g., cookies, prompts)
   - Dedicated `core/credentials/` folder for secure storage

5. **MCP Integration**:
   - Centralized all MCP clients in `core/mcp/`
   - Structured for easy integration with Crypto Indicators and CCXT MCPs

6. **API Layer for Bubble.io**:
   - Added dedicated `core/api/` module for Bubble.io integration
   - Clear separation of API concerns

7. **Improved Testing Structure**:
   - Organized tests by type (unit, integration)
   - Added fixtures directory for test data

## Migration Approach

1. Create the new directory structure, starting with the `core/` directory
2. Move common, config, and utility files to their respective locations under `core/`
3. Consolidate `trades/` and `trading/` functionality into the new `trading/` module
4. Set up the MCP integration framework in `core/mcp/`
5. Update imports and references
6. Test each module after migration
7. Remove old directories once migration is complete

## Implications for Developers

1. **Imports**: Update import statements to reflect the new structure
2. **MCP Integration**: Implement MCP clients following the consistent pattern in `core/mcp/`
3. **Trading Logic**: Update trading code to work with the consolidated `trading/` module

This structure significantly simplifies maintenance, reduces redundancy, and provides a clear path for integrating MCPs into the codebase.