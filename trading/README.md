# GGBot Trading Module

## Overview

The Trading Module is responsible for executing trades based on decisions (intents) received from the Decision Module. It implements a service-oriented architecture to handle:

- Connecting to cryptocurrency exchanges via CCXT MCP
- Processing trading intents from the Decision Module
- Using LLMs to convert intents into executable commands
- Validating and applying risk controls to proposed trades
- Mapping standardized symbols to exchange-specific formats
- Executing validated trades on exchanges
- Monitoring positions for stop-loss/take-profit conditions
- Providing feedback on trade status and execution

## Architecture

The Trading Module follows a service-oriented architecture with clear separation of concerns:

### 1. TradingEngine

The central facade that orchestrates the overall trading flow:
- Receives intents from the Decision Module
- Coordinates between specialized services
- Maintains connection to exchange adapter
- Provides a simple, consistent API to other modules

### 2. Services

#### LLMService
- Handles all interactions with LLM providers
- Creates prompts based on trading intents
- Parses LLM responses into structured tool calls
- Provides error handling and retry logic for LLM API calls

#### ValidationService
- Validates proposed tool calls against exchange schemas
- Integrates with TradeCompiler for risk checks
- Maps standardized symbols to exchange-specific formats
- Enforces leverage and position size limits

#### ExecutionService
- Executes validated tool calls on exchanges
- Handles order creation and management
- Provides execution results and confirmations
- Focuses primarily on trade execution, not monitoring

#### PositionMonitor
- Uses direct CCXT connections for reliable position monitoring
- Implements deterministic monitoring independent of LLM
- Provides real-time position status, PnL, and margin data
- Handles exchange-specific position data formats

### 3. Core Components

#### TradeCompiler
- Validates and finalizes trade parameters
- Applies exchange-specific adjustments and constraints
- Maps standardized symbols to exchange-specific formats
- Enforces risk limits and trading rules

#### CCXTMCPAdapter
- Connects to the CCXT MCP server
- Provides a unified interface for trade execution
- Handles connection lifecycle and credential management
- Implements exchange-specific symbol mapping

#### DirectCCXTAdapter
- Connects directly to CCXT library for trade monitoring
- Bypasses MCP for reliable, deterministic data retrieval
- Uses the same symbol mapping system as MCP adapter
- Optimized for frequent monitoring calls

#### TradeManager
- Tracks active positions and their status
- Uses direct CCXT connections for reliable monitoring
- Monitors for stop-loss and take-profit conditions
- Maintains trade history and statistics

### 4. Models

Structured data models using Pydantic for typed validation:
- ToolCall: Represents an exchange operation requested by the LLM
- ValidatedToolCall: A validated tool call ready for execution
- Trade: Represents an active trade with its metadata
- Event: Events for monitoring and notification

## Exchange Support

### Current Implementation: BitMEX

The Trading Module currently has full support for BitMEX testnet and production environments:

#### Implemented CCXT MCP Tools
- **Position Management**: `fetch_positions`, `close_position`, `set_leverage`
- **Order Creation**: `create_limit_order`, `create_market_buy_order`, `create_market_sell_order`, `create_stop_order`, `create_reduce_only_order`
- **Order Management**: `cancel_order`, `edit_order`, `fetch_open_orders`
- **Account Management**: `fetch_balance`, `fetch_orders`
- **Market Data**: `fetch_markets`, `fetch_ticker`, `fetch_ohlcv`, `fetch_order_book`

#### BitMEX-Specific Configuration
1. **Symbol Mapping**: Standard symbols (BTC/USD) are mapped to BitMEX format (BTC/USD:BTC)
2. **Authentication**: Uses API key and secret with testnet sandbox mode
3. **Position Handling**: Supports BitMEX's contract-based position system
4. **Leverage**: Supports BitMEX leverage settings (1x to 100x)

#### Testing Status
✅ **ExecutionService Test**: Successfully tested order execution and position monitoring
✅ **MCP Server Integration**: All 18 tools registered and functional
✅ **Position Tracking**: Real-time position data retrieval working
✅ **Order Execution**: Market and limit orders executing successfully on testnet

### Adding Support for New Exchanges

The Trading Module uses a **Universal MCP Server** approach for supporting multiple exchanges:

#### Implementation Strategy
1. **Single CCXT MCP Server**: One server handles all exchanges using `exchange_id` parameter
2. **Exchange-Specific Logic**: Each tool contains conditional logic for different exchanges
3. **Unified Interface**: Same tool signatures work across all exchanges
4. **Symbol Mapping**: Exchange-specific symbol conversions handled transparently

#### Steps to Add a New Exchange

**1. Research Exchange Capabilities**
```bash
# Generate exchange capability reports
python -m tests.list_ccxt_direct_methods --exchange=binance
python -m tests.check_exchange_capabilities --exchange=binance
```

**2. Update Symbol Mappings**
```python
# Add to core/mcp/servers/ccxt_mcp_server.py
EXCHANGE_SYMBOL_MAP = {
    'bitmex': {
        'BTC/USD': 'BTC/USD:BTC',
        # ... existing BitMEX mappings
    },
    'binance': {  # New exchange
        'BTC/USD': 'BTCUSDT',
        'ETH/USD': 'ETHUSDT',
        # ... Binance-specific mappings
    }
}
```

**3. Handle Exchange-Specific Features**
- Update tool implementations to handle exchange differences
- Add exchange-specific parameter handling
- Implement exchange-specific error handling
- Handle different precision requirements

**4. Create Exchange-Specific Tests**
- Adapt existing test templates for new exchange
- Test exchange-specific features (leverage, positions, etc.)
- Verify testnet/sandbox functionality

**5. Update Adapter Logic**
```python
# Add exchange-specific logic to trading/exchanges/ccxt_mcp.py
if self.exchange_id.lower() == 'binance':
    # Binance-specific handling
elif self.exchange_id.lower() == 'coinbase':
    # Coinbase-specific handling
```

#### Exchange Considerations
- **Position Support**: Not all exchanges support positions (spot vs derivatives)
- **Order Types**: Different supported order types per exchange
- **Authentication**: Different API key formats and signature methods
- **Rate Limits**: Exchange-specific rate limiting requirements
- **Precision**: Different precision requirements for prices and quantities

## Exchange-Agnostic Design

The Trading Module implements an exchange-agnostic architecture:

1. **Standardized Symbols**: Uses standard market symbols (e.g., "BTC/USD") throughout the codebase and in LLM interactions

2. **Symbol Mapping**: Automatically maps standard symbols to exchange-specific formats (e.g., "BTC/USD:BTC" for BitMEX) during validation

3. **Abstraction Layer**: Both adapters (MCP and direct CCXT) abstract exchange-specific details and provide a unified interface

4. **Parameter Normalization**: Handles differences in parameter naming and formatting between exchanges

This approach allows adding new exchanges with minimal code changes, primarily by updating the symbol mapping dictionaries. The hybrid approach (MCP+LLM for execution, direct CCXT for monitoring) provides an optimal balance of flexibility and reliability.

## Testing Strategy

The Trading Module follows a comprehensive testing approach:

### Current Testing Status

**Phase 1: Component Testing** ✅ **COMPLETED**
- ✅ LLMService: Individual testing with real LLM API calls
- ✅ ValidationService: Testing with real exchange constraints
- ✅ ExecutionService: Testing with BitMEX testnet order execution

**Phase 2: MCP Server Integration** ✅ **COMPLETED**
- ✅ CCXT MCP Server: 18 tools implemented and tested
- ✅ Position Management: fetch_positions, close_position, set_leverage
- ✅ Order Management: create_limit_order, cancel_order, edit_order
- ✅ Real Exchange Integration: Successfully executing orders on BitMEX testnet

**Phase 3: End-to-End Testing** 🔄 **IN PROGRESS**
- ⏳ Complete trading flow from decision intent to execution
- ⏳ LLM integration with MCP tools
- ⏳ Full pipeline testing with real trading scenarios

**Phase 4: Production Integration** 📋 **PLANNED**
- 📋 Database integration for trade persistence
- 📋 API endpoint development
- 📋 Direct CCXT monitoring implementation

### Testing Approach

1. **Component Testing**: Individual testing of LLMService, ValidationService, and ExecutionService
   - Each component is tested with real external services but isolated from other components
   - Uses BitMEX testnet for all exchange interactions

2. **End-to-End Flow Testing**: Testing the complete flow from intent to execution
   - Validates translation of intent to executable tool calls
   - Tests the actual execution on testnet
   - Focuses primarily on the trade execution pathway

3. **Monitoring Testing**: Separate testing for position monitoring
   - Tests direct CCXT adapter for position data retrieval
   - Validates proper data collection and formatting
   - Ensures reliable notification of position changes

4. **Integration Testing**: Tests the entire module's integration with other modules
   - Verifies proper data flow between Decision and Trading modules
   - Tests database interactions for trade persistence
   - Validates API endpoint functionality

## Future Improvements

### Database Integration
- Implement persistent storage for trades and positions
- Track trade history and performance metrics
- Store execution results and audit logs
- Enable historical analysis and reporting

### User Configuration Management
- Create a configuration management system
- Allow per-user customization of risk parameters
- Store user preferences for trading behavior
- Implement configuration validation and versioning

### Enhanced Credential Handling
- Implement secure credential storage with encryption
- Support multiple exchange accounts per user
- Add credential rotation and expiration handling
- Develop credential verification and validation

### Performance Optimizations
- Add caching for frequently accessed exchange data
- Implement batched operations for exchange interactions
- Optimize LLM prompt creation and parsing
- Reduce unnecessary API calls to exchanges

### Advanced Risk Management
- Implement portfolio-level risk assessment
- Add adaptive position sizing based on volatility
- Create multi-level stop-loss strategies
- Develop drawdown protection mechanisms

## To-Do Items

### 1. Complete End-to-End Trading Flow Tests ⏳ **CURRENT PRIORITY**
- Integrate LLM service with MCP tools in full pipeline test
- Test complete flow from decision intent to order execution
- Verify proper execution of market and limit orders with LLM integration
- Ensure trade validation works correctly with exchange constraints
- Implement proper test cleanup to avoid leaving open positions

### 2. Add Direct CCXT Trade Monitoring 📋 **NEXT**
- Implement DirectCCXTAdapter for reliable position data
- Create PositionMonitor class using direct CCXT connections
- Develop methods for fetching complete position information
- Implement standardized response format compatible with existing code
- Create monitoring tests to verify functionality

### 3. Integrate with Database 📋 **PLANNED**
- Update schema to store trade execution details
- Create data models for trades and positions
- Implement persistence layer for all trading activity
- Add historical trade tracking and performance metrics
- Ensure proper association with user accounts

### 4. Create API Endpoints 📋 **PLANNED**
- Develop endpoint for receiving trading intents from Decision Module
- Create endpoints for triggering the trading execution workflow
- Add endpoints for position monitoring and status updates
- Implement trade history and performance retrieval endpoints
- Add authentication and user permission validation

### 5. Exchange Expansion 📋 **FUTURE**
- Add support for Binance (spot and futures)
- Add support for Coinbase Pro
- Implement exchange capability detection
- Create exchange-specific test suites