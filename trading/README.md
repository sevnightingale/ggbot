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

#### TradeLifecycleManager
- **Position-Based Trade Sync**: Automatically creates/updates/closes trades based on exchange positions
- **TP/SL Order Tracking**: Monitors reduce-only orders and closes trades when they execute
- **Complete Trade Lifecycle**: Manages trades from entry through TP/SL exit with full audit trails
- **Config-ID Integration**: Associates all trades with specific trading configurations
- **Real-time Order Status**: Tracks order fills and automatically updates trade exit prices

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

## Strategy Metadata Tracking

The Trading Module implements a comprehensive **decision audit trail** system through the `strategy_runs` table, capturing the complete context of every trading decision from entry to exit.

### Decision Lifecycle Tracking

Every decision made by the Decision Module is tracked through three key scenarios:

#### 1. TRADE_ENTRY
- **When**: New trade is opened
- **Captures**: 
  - Original decision reasoning and confidence score
  - Entry conditions (price, stop loss, take profit)
  - Market context at time of entry
  - Execution details and order information
- **Links**: Associates with config_id and decision_id

#### 2. TRADE_MANAGEMENT  
- **When**: Active trade is adjusted (moving stops, taking partial profits)
- **Captures**:
  - Adjustment reasoning and new parameters
  - Current market conditions vs original thesis
  - Execution details of adjustment orders
- **Links**: References original TRADE_ENTRY strategy_run as parent

#### 3. TRADE_EXIT
- **When**: Trade is closed (TP hit, SL triggered, manual exit)
- **Captures**:
  - Exit reasoning and final outcome
  - Exit price and P&L details
  - Whether original thesis was validated
- **Links**: References original TRADE_ENTRY strategy_run as parent

### Data Structure

```sql
strategy_runs:
- strategy_run_id (UUID): Unique identifier
- trade_id (UUID): Links to trades table
- config_id (UUID): Links to trading configuration
- decision_id (UUID): Links to specific decision
- scenario ('TRADE_ENTRY'|'TRADE_MANAGEMENT'|'TRADE_EXIT')
- parent_strategy_run_id (UUID): Links to original entry decision
- confidence_score (0.0-1.0): AI confidence level
- reasoning_log (TEXT): Natural language reasoning
- decision_data (JSONB): Structured decision context
- created_at (TIMESTAMP): Decision timestamp
```

### Example Decision Chain

```
Initial Decision: "90% confident BTC will bounce from support"
├── TRADE_ENTRY strategy_run
│   ├── reasoning: "Strong bullish divergence on RSI"
│   ├── confidence: 0.90
│   └── decision_data: {entry_conditions, market_context}
│
├── TRADE_MANAGEMENT strategy_run (parent → TRADE_ENTRY)
│   ├── reasoning: "Moving SL to breakeven as target approached"
│   └── decision_data: {adjustments, current_thesis_status}
│
└── TRADE_EXIT strategy_run (parent → TRADE_ENTRY)
    ├── reasoning: "Take profit hit, thesis validated"
    └── decision_data: {exit_conditions, final_outcome}
```

### Benefits

1. **Learning & Optimization**: Analyze which decision patterns lead to successful trades
2. **Strategy Validation**: Track whether AI confidence scores correlate with outcomes
3. **Trade Management Context**: Decision Module can review original reasoning when managing trades
4. **Performance Analytics**: Rich data for backtesting and strategy refinement
5. **Audit Trail**: Complete record of all trading decisions for compliance and analysis

### Implementation

Strategy metadata is automatically created by the `TradeManager` class:
- **Entry**: When `create_trade()` is called after successful execution
- **Management**: When `_execute_adjustment()` processes trade modifications
- **Exit**: When `_execute_exit()` closes positions

The system maintains parent-child relationships between decisions, enabling analysis of complete trade lifecycles and decision chains.

## TP/SL Order Tracking & Automated Trade Management

The Trading Module implements **comprehensive TP/SL order tracking** that automatically manages trade lifecycles from entry through exit.

### Real-Time Order Monitoring

The monitoring system continuously tracks all orders associated with active trades:

#### **1. Order Detection & Classification**
- **Fetches open orders** from exchanges every monitoring cycle (30s default)
- **Identifies reduce-only orders** automatically based on exchange-specific patterns
- **Classifies TP vs SL orders** using order type, trigger prices, and execution instructions
- **Links orders to trades** automatically for complete lifecycle tracking

#### **2. Exchange-Specific Detection**

**BitMEX Order Detection:**
- `reduceOnly: true` flag detection
- `execInst: "Close"` instruction recognition
- `stopPx` trigger price identification
- Stop order type classification

**Binance Order Detection:**
- `reduceOnly: true` flag detection
- `take_profit` and `stop_market` order types
- Exchange-specific order characteristics

### Automated Trade Closure

When TP/SL orders are filled, trades are automatically closed with complete details:

#### **Exit Price & P&L Calculation**
```sql
-- Automatic trade closure when TP/SL hits
UPDATE trades SET
    status = 'closed',
    exit_price = 105500.0,           -- Actual fill price
    exit_reason = 'Take Profit hit',  -- TP/SL classification
    realized_pnl = 1500.0,          -- Calculated P&L
    closed_at = '2025-01-22 15:30:45' -- Actual fill time
```

#### **Trade Lifecycle Example**
```
1. Entry: Market buy 1000 contracts BTC/USD at $104000
   └── Trade created with entry_price = 104000

2. TP/SL Placement: 
   ├── TP order: Sell 1000 contracts at $106000 (reduceOnly: true)
   └── SL order: Sell 1000 contracts at $102000 (reduceOnly: true)

3. Monitoring: Orders tracked in trade_orders table
   ├── is_risk_order = true
   ├── risk_type = 'TP' / 'SL'
   └── status = 'open'

4. Order Fill: TP order executes at $105500
   └── Order status updated to 'filled'

5. Trade Closure: Automatically triggered
   ├── exit_price = 105500
   ├── exit_reason = "Take Profit hit"  
   ├── realized_pnl = (105500 - 104000) * 1000 = $1,500,000
   └── status = 'closed'
```

### Database Schema Integration

The TP/SL tracking leverages the enhanced trade lifecycle schema:

#### **trade_orders Table**
```sql
- is_risk_order BOOLEAN        -- true for TP/SL orders
- risk_type VARCHAR(10)        -- 'TP', 'SL', or NULL
- status VARCHAR               -- 'open', 'filled', 'canceled'
- filled_at TIMESTAMP          -- Actual execution time
```

#### **trades Table**
```sql
- exit_price DECIMAL(20,8)     -- Actual exit price from order fill
- exit_reason VARCHAR          -- "Take Profit hit" / "Stop Loss hit"
- realized_pnl DECIMAL(20,8)   -- Calculated profit/loss
- closed_at TIMESTAMP          -- Trade closure time
```

### Performance & Reliability

#### **Monitoring Cycle Integration**
The TP/SL tracking is seamlessly integrated into the monitoring service:

1. **Position Sync** (30s): `sync_positions_to_trades()`
2. **Order Sync** (30s): `_sync_orders_to_database()`  
3. **TP/SL Check** (30s): `sync_tp_sl_orders()`

#### **Error Handling & Resilience**
- **Graceful API failures**: Order fetching errors don't break monitoring
- **Database consistency**: Transaction-based updates ensure data integrity
- **Missing data handling**: Robust logic for incomplete order information
- **Duplicate protection**: Upsert logic prevents duplicate order records

### Benefits

1. **Fully Automated**: No manual intervention required for trade management
2. **Accurate P&L**: Uses actual execution prices, not estimates
3. **Complete Audit Trail**: Every order and trade closure is logged
4. **Real-Time Updates**: 30-second monitoring cycle ensures rapid response
5. **Exchange Agnostic**: Works across BitMEX, Binance, and future exchanges
6. **Performance Optimized**: Efficient queries only check trades with active orders

This system enables **hands-off trade management** where the AI makes entry decisions and the system automatically handles exits according to the original TP/SL plan.

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

**Phase 4: Production Integration** ✅ **COMPLETED**
- ✅ Database integration for trade persistence with Universal Trade Lifecycle
- ✅ TP/SL order tracking and automated trade closure
- ✅ Direct CCXT monitoring implementation with order status sync
- ✅ Config-ID based multi-strategy support

### Testing Approach

1. **Component Testing**: Individual testing of LLMService, ValidationService, and ExecutionService
   - Each component is tested with real external services but isolated from other components
   - Uses BitMEX testnet for all exchange interactions

2. **End-to-End Flow Testing**: Testing the complete flow from intent to execution
   - Validates translation of intent to executable tool calls
   - Tests the actual execution on testnet
   - Focuses primarily on the trade execution pathway

3. **Monitoring Testing**: Comprehensive trade lifecycle testing
   - Tests direct CCXT adapter for position data retrieval
   - Validates proper data collection and formatting
   - Ensures reliable notification of position changes
   - **TP/SL Order Tracking**: Tests reduce-only order detection and trade closure
   - **Order Status Sync**: Validates real-time order status updates

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