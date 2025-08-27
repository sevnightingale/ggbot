# Paper Trading Engine Integration Plan

## Overview
Build a custom paper trading engine that uses Hummingbot API for real-time market data while implementing our own execution and portfolio management logic. The engine will integrate seamlessly with the existing Decision Module's trade intent structure.

## Current Architecture Assessment

### Existing Components (Validated)
- **Decision Module**: Generates trade intents with confidence scoring, stop/take profit levels
- **Symbol Standardizer**: `core.symbols.standardizer.UniversalSymbolStandardizer` - handles 141 pairs
- **Database Schema**: PostgreSQL with user/config isolation via `user_id` and `config_id`
- **Hummingbot API**: Operational on port 8888 with market data endpoints
- **Trade Intent Structure**: Well-defined format from `decision.engine._create_intent()`

### Decision Module Integration Points
The Decision Module already generates trade intents with this structure:
```python
intent = {
    'decision_id': str,
    'user_id': str,
    'config_id': str,
    'symbol': str,  # Internal format: 'BTC/USDT'
    'action': str,  # 'long', 'short', 'no_action'
    'confidence': float,  # 0.0-1.0
    'stop_loss_price': float,  # Optional
    'take_profit_price': float,  # Optional
    'reasoning': str,
    'exchange': str,  # Currently 'bitmex'
    'llm_decision': str  # Raw LLM response
}
```

## Architecture Components

### 1. Market Data Service
**Purpose**: Real-time market data from Hummingbot API for accurate paper trade execution

**Implementation**: `trading/paper/market_data.py`
- **Primary Source**: Hummingbot API on localhost:8888
- **Exchange**: KuCoin connector (supports all 141 pairs)
- **Authentication**: HTTP Basic Auth using `HBOT_USERNAME` and `HBOT_PASSWORD` from .env

**Key Endpoints**:
```python
POST /market-data/prices
Request: {"connector_name": "kucoin", "trading_pairs": ["BTC-USDT"]}
Response: {"BTC-USDT": {"last": 45000.0, "bid": 44950.0, "ask": 45050.0}}

POST /market-data/order-book  
Request: {"connector_name": "kucoin", "trading_pair": "BTC-USDT"}
Response: {"bids": [...], "asks": [...], "timestamp": 1234567890}

GET /connectors/kucoin/trading-rules?trading_pairs=BTC-USDT
Response: {"BTC-USDT": {"min_order_size": 0.00001, "price_step": 0.01}}
```

**Symbol Conversion**:
- Decision Module uses: `BTC/USDT` 
- Hummingbot API expects: `BTC-USDT`
- Use `standardizer.normalize(symbol, "ccxt", "hummingbot")`

### 2. Database Schema Extensions

**New Tables** (Migration required):

```sql
-- Paper trading accounts (one per config_id)  
CREATE TABLE paper_accounts (
    account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID UNIQUE REFERENCES configurations(config_id),
    user_id UUID REFERENCES users(user_id),
    initial_balance DECIMAL(20,8) DEFAULT 10000.00,
    current_balance DECIMAL(20,8),
    total_pnl DECIMAL(20,8) DEFAULT 0,
    open_positions INTEGER DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Paper trades (extends existing trades table concept)
CREATE TABLE paper_trades (
    trade_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES paper_accounts(account_id),
    config_id UUID REFERENCES configurations(config_id),
    user_id UUID REFERENCES users(user_id),
    decision_id UUID,  -- Links back to Decision Module
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- 'long' or 'short'
    entry_price DECIMAL(20,8) NOT NULL,
    current_price DECIMAL(20,8),
    size_usd DECIMAL(20,8) NOT NULL,
    size_contracts DECIMAL(20,8),
    leverage INTEGER DEFAULT 1,
    unrealized_pnl DECIMAL(20,8) DEFAULT 0,
    realized_pnl DECIMAL(20,8) DEFAULT 0,
    fees DECIMAL(20,8) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'open',  -- 'open', 'closed'
    stop_loss DECIMAL(20,8),
    take_profit DECIMAL(20,8),
    confidence_score DECIMAL(3,2),
    reasoning TEXT,
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    close_reason VARCHAR(50),  -- 'take_profit', 'stop_loss', 'manual'
    
    -- Indexes for performance
    INDEX idx_paper_trades_config_status (config_id, status),
    INDEX idx_paper_trades_symbol (symbol),
    INDEX idx_paper_trades_opened (opened_at)
);

-- Paper orders (audit trail)
CREATE TABLE paper_orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id UUID REFERENCES paper_trades(trade_id),
    order_type VARCHAR(20) NOT NULL,  -- 'market', 'stop_loss', 'take_profit'
    side VARCHAR(10) NOT NULL,  -- 'buy', 'sell'
    requested_price DECIMAL(20,8),
    filled_price DECIMAL(20,8),
    size DECIMAL(20,8) NOT NULL,
    fees DECIMAL(20,8) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'filled',  -- 'filled' (all paper orders succeed)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    filled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Design Decisions**:
- Each `config_id` gets ONE paper account with $10k starting balance
- Trades isolated per config_id for multi-strategy support  
- Links to Decision Module via `decision_id` for audit trail
- Simple fee structure (0.06% taker fee applied to all trades)

### 3. Paper Trading Engine Core

**PaperTradingService** (`trading/paper/service.py`)

**Key Methods**:
```python
class PaperTradingService:
    async def execute_trade_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Execute paper trade from Decision Module intent"""
        # 1. Validate symbol and config_id
        # 2. Get or create paper account  
        # 3. Fetch current market price from Hummingbot API
        # 4. Calculate position size based on confidence
        # 5. Apply simple fill model (mid-price execution)
        # 6. Create paper trade record
        # 7. Update account balance
        # 8. Return execution details
        
    async def close_position(self, trade_id: str, reason: str = 'manual') -> Dict[str, Any]:
        """Close paper position and calculate final P&L"""
        
    async def get_account_summary(self, config_id: str) -> Dict[str, Any]:
        """Get paper account balance and performance stats"""
        
    async def update_position_prices(self, config_id: str = None) -> int:
        """Update mark prices and unrealized P&L for open positions"""
```

**Position Sizing Logic**:
```python
# Confidence-based position sizing
max_position_usd = account_balance * 0.10  # 10% max per trade
position_size = confidence * max_position_usd

# Example: confidence=0.65, balance=$10k -> position_size=$650
```

**Fill Model (Simple)**:
- All trades execute immediately at mid-price
- Add 0.06% taker fee (realistic but simple)
- No slippage initially (can add later)
- Stop losses and take profits execute at exact trigger price

### 4. Market Data Integration

**MarketDataAdapter** (`trading/paper/market_data.py`)

```python
class MarketDataAdapter:
    def __init__(self):
        self.hummingbot_url = "http://localhost:8888"
        self.auth = HTTPBasicAuth(username, password)
        self.symbol_standardizer = UniversalSymbolStandardizer()
        self.price_cache = {}  # 5-minute TTL cache
        
    async def get_current_price(self, symbol: str) -> Dict[str, float]:
        """Get bid/ask/mid prices for symbol"""
        # Convert BTC/USDT -> BTC-USDT for Hummingbot API
        hb_symbol = self.symbol_standardizer.normalize(symbol, "ccxt", "hummingbot")
        
        # Call /market-data/prices endpoint
        response = await self._call_hummingbot_api("POST", "/market-data/prices", {
            "connector_name": "kucoin",
            "trading_pairs": [hb_symbol]
        })
        
        return {
            "bid": response[hb_symbol]["bid"],
            "ask": response[hb_symbol]["ask"], 
            "mid": (response[hb_symbol]["bid"] + response[hb_symbol]["ask"]) / 2,
            "last": response[hb_symbol]["last"]
        }
        
    async def get_trading_rules(self, symbol: str) -> Dict[str, Any]:
        """Get min order size, tick size, etc."""
```

**Caching Strategy**:
- Cache prices for 30 seconds (frequent updates)
- Cache trading rules for 1 hour (static data)
- Use symbol as cache key
- Handle cache misses gracefully

### 5. API Endpoints

**New routes in main_api.py**:

```python
@app.post("/paper/execute")
async def execute_paper_trade(intent: Dict[str, Any]):
    """Accept trade intent from Decision Module and execute paper trade"""
    service = PaperTradingService()
    result = await service.execute_trade_intent(intent)
    return result

@app.get("/paper/positions/{config_id}")  
async def get_paper_positions(config_id: str):
    """Get all open paper positions for config_id with real-time P&L"""
    service = PaperTradingService()
    # Update prices first
    await service.update_position_prices(config_id)
    # Return positions
    return await service.get_open_positions(config_id)

@app.get("/paper/account/{config_id}")
async def get_paper_account(config_id: str):
    """Get paper account summary and performance stats"""
    service = PaperTradingService() 
    return await service.get_account_summary(config_id)

@app.post("/paper/close/{trade_id}")
async def close_paper_position(trade_id: str):
    """Manually close paper position"""
    service = PaperTradingService()
    return await service.close_position(trade_id, reason='manual')
```

### 6. Integration with Decision Module

**Webhook Chain Update**:
The Decision Module already has webhook functionality. We need to:

1. **Update decision/api.py** to call paper trading after successful decision:
```python
# In trigger_trading_webhook() function
if action not in ["no_action", "hold", "wait"]:
    # Call paper trading instead of old trading module
    response = await httpx.post(
        "http://localhost:8000/paper/execute",
        json=intent
    )
```

2. **No changes needed to Decision Module core** - it already generates proper intents

### 7. Position Monitoring & Background Tasks

**Background Task** (added to main_api.py startup):
```python
async def update_paper_positions_task():
    """Background task to update paper position prices every 30 seconds"""
    while True:
        try:
            service = PaperTradingService()
            updated_count = await service.update_position_prices()
            logger.info(f"Updated {updated_count} paper positions")
        except Exception as e:
            logger.error(f"Position update failed: {e}")
        await asyncio.sleep(30)
```

**Stop Loss / Take Profit Logic**:
- Check trigger conditions during price updates
- Close positions automatically when triggered
- Record close reason in database
- Update account balance immediately

### 8. Configuration & Environment

**New Environment Variables** (.env):
```bash
# Paper Trading Configuration
PAPER_INITIAL_BALANCE=10000
PAPER_MAX_POSITION_PCT=10  # 10% of balance per trade
PAPER_TAKER_FEE=0.0006     # 0.06% fee
PAPER_ENABLE_SLIPPAGE=false # Simple fills initially

# Market Data Settings  
PAPER_PRICE_CACHE_TTL=30   # 30 seconds
PAPER_RULES_CACHE_TTL=3600 # 1 hour
```

## Implementation Plan

### Phase 1: Foundation (Day 1)
1. ✅ Create DOCS/PAPER.md planning document
2. **Create database migration** for paper trading tables
3. **Test Hummingbot API connectivity** and credentials
4. **Validate symbol conversion** for all 141 pairs using standardizer

### Phase 2: Core Engine (Day 2) 
5. **Build MarketDataAdapter** with Hummingbot API client
6. **Implement PaperTradingService** core execution logic
7. **Create paper account initialization** (one per config_id)
8. **Test simple trade execution** with mid-price fills

### Phase 3: Integration (Day 3)
9. **Add API endpoints** to main_api.py
10. **Update Decision Module** to call paper trading endpoint
11. **Implement position monitoring** background task
12. **Add stop loss/take profit** trigger logic

### Phase 4: Testing & Validation (Day 4)
13. **End-to-end testing** with existing ggShot signals
14. **Validate P&L calculations** and position tracking
15. **Test multi-config isolation** (multiple strategies)
16. **Performance testing** with high-frequency updates

## Testing Strategy

### Unit Tests
- MarketDataAdapter price fetching
- Symbol conversion edge cases
- Position sizing calculations
- P&L calculation accuracy

### Integration Tests  
- Hummingbot API connectivity and error handling
- Database operations and transactions
- Decision Module webhook chain
- Stop loss/take profit triggers

### End-to-End Tests
- Complete trade lifecycle: entry → monitoring → exit
- Multi-symbol position management
- Account balance tracking
- Performance analytics calculation

## Success Criteria

### Functional Requirements
- ✅ Accept Decision Module trade intents without modification
- ✅ Execute paper trades with real-time Hummingbot market data
- ✅ Track positions and P&L accurately  
- ✅ Handle stop loss and take profit triggers
- ✅ Support all 141 cryptocurrency pairs
- ✅ Isolate accounts per config_id

### Performance Requirements
- Position price updates within 30 seconds
- Trade execution latency < 2 seconds
- Support 10+ concurrent positions per config_id
- Handle 100+ trades per day per config_id

### Integration Requirements
- Zero changes required to Decision Module
- Compatible with existing ggShot signal flow
- Works with current symbol standardization
- Integrates with existing database schema

## Future Enhancements (Post-MVP)

### Realism Improvements
- Order book depth-based slippage calculation
- Realistic fill delays based on market conditions
- Funding costs for perpetual positions
- Liquidation logic for high leverage

### Advanced Features
- Portfolio-level risk management
- Cross-symbol correlation analysis
- Performance attribution by strategy
- Backtesting with historical data

### User Interface
- Real-time position dashboard
- P&L charts and analytics
- Trade history and performance reports
- Risk management controls

## Key Design Decisions & Rationale

### Why KuCoin Only Initially?
- Simplifies implementation (one connector)
- KuCoin supports all 141 pairs we need
- Hummingbot API already configured
- Can expand to multiple exchanges later

### Why Simple Fill Model?
- Faster implementation and testing
- Good enough for initial paper trading validation  
- Can add realistic slippage/delays later
- Focuses on core functionality first

### Why Separate Database Tables?
- Clean separation from live trading data
- Easier to reset/clear paper trading data
- Allows different schema optimizations
- Prevents accidental mixing with real trades

### Why One Account Per Config ID?
- Aligns with existing multi-strategy architecture
- Isolates different trading strategies
- Enables performance comparison
- Matches user expectations from frontend

This comprehensive plan provides a clear roadmap for implementing a production-ready paper trading engine that integrates seamlessly with the existing ggbots platform architecture.