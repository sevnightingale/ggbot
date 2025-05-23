# Account Monitoring System

The Account Monitoring System provides real-time tracking of exchange account balances, positions, and margin data. It uses direct CCXT connections (not MCP) for reliability and stores normalized data in the database for use by other modules.

## Architecture Overview

### Design Philosophy
- **Separation of Concerns**: Trade execution uses CCXT MCP + LLM for flexibility; monitoring uses direct CCXT for reliability
- **Exchange Agnostic**: Adapter pattern handles exchange-specific quirks
- **Real-time Risk Management**: Continuous monitoring enables informed trading decisions
- **Data Consistency**: Single source of truth in database for account state

### Key Components

```
core/monitoring/
├── __init__.py          # Module exports
├── service.py           # AccountMonitoringService (main class)
├── adapters.py          # Exchange-specific data adapters
└── README.md           # This documentation
```

## Core Classes

### AccountMonitoringService
The main monitoring service that runs continuously in the background.

```python
from core.monitoring import AccountMonitoringService

service = AccountMonitoringService(
    user_id="uuid",
    config_id="uuid", 
    exchange_name="bitmex",
    credentials={"apiKey": "...", "secret": "..."},
    monitoring_interval=30,  # seconds
    testnet=True
)

await service.start_monitoring()
# ... monitoring runs in background ...
await service.stop_monitoring()
```

**Key Features:**
- Async monitoring loop with configurable interval (default: 30 seconds)
- Automatic connection recovery on failures
- Exponential backoff on errors
- Graceful shutdown handling
- Direct database integration

### Exchange Adapters
Handle exchange-specific data format differences.

**Available Adapters:**
- `BitMEXAdapter`: Handles XBt currency, satoshi conversion, symbol mapping
- `BinanceAdapter`: Standard implementation for future use

**Adapter Interface:**
```python
class ExchangeAdapter(ABC):
    def normalize_balance(self, raw_balance: dict) -> dict
    def normalize_position(self, raw_position: dict) -> dict  
    def get_symbol_format(self, symbol: str) -> str
    def get_exchange_config(self) -> dict
```

## Data Flow

```
Exchange API → CCXT → Exchange Adapter → Normalized Data → Database
                                                              ↓
                                     Future Decision Module ←─┘
```

1. **Data Fetch**: Service calls `exchange.fetch_balance()` and `exchange.fetch_positions()`
2. **Normalization**: Exchange adapter converts to standardized format
3. **Calculation**: Service calculates equity, margins, and metrics
4. **Storage**: Data stored in `account_states` table
5. **Consumption**: Other modules query database for current state

## Database Schema

### account_states Table
```sql
CREATE TABLE account_states (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    config_id UUID NOT NULL, 
    exchange VARCHAR(50) NOT NULL,
    balance_data JSONB NOT NULL,        -- Normalized balance data
    position_data JSONB NOT NULL,       -- Normalized position array
    equity NUMERIC(20, 8) NOT NULL,     -- Total account value
    available_margin NUMERIC(20, 8),    -- Available for new trades
    used_margin NUMERIC(20, 8),         -- Currently used margin
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, config_id, exchange)
);
```

### Normalized Data Formats

**Balance Data:**
```json
{
    "total_btc": 0.64796857,
    "available_btc": 0.64796857,
    "used_btc": 0.0,
    "total_usd_value": 73432.466372,
    "currencies": {
        "BTC": {"total": 0.64796857, "free": 0.64796857, "used": 0.0},
        "USDT": {"total": 73432.466372, "free": 73432.466372, "used": 0.0}
    }
}
```

**Position Data:**
```json
[
    {
        "symbol": "BTC/USD",
        "side": "long",
        "contracts": 10000,
        "size": 10000.0,
        "entry_price": 45000.0,
        "mark_price": 46000.0,
        "liquidation_price": 40000.0,
        "unrealized_pnl": 0.0217,
        "unrealized_pnl_pct": 2.17,
        "margin_mode": "cross",
        "leverage": 100.0,
        "timestamp": 1616161616000
    }
]
```

## Exchange-Specific Handling

### BitMEX Testnet
- **Currency**: Uses 'XBt' instead of 'BTC'
- **Units**: Values in satoshis (÷ 100,000,000 for BTC)
- **Symbols**: BTC/USD becomes BTC/USD:BTC
- **Positions**: Always returns position objects (even with 0 contracts)
- **PNL**: Unrealized PNL comes as string, needs conversion
- **Margin**: Cross margin enforced for multi-asset accounts

**BitMEX Adapter Features:**
```python
# Symbol mapping
adapter.get_symbol_format("BTC/USD")  # → "BTC/USD:BTC"

# Balance normalization  
raw_balance = {"XBt": {"total": 64796857}}  # satoshis
normalized = adapter.normalize_balance(raw_balance)
# → {"total_btc": 0.64796857, ...}

# Position filtering
raw_position = {"contracts": 0, "symbol": "BTC/USD:BTC"}
normalized = adapter.normalize_position(raw_position)  
# → None (filters out 0-contract positions)
```

### Future Exchanges
Adding new exchanges requires implementing the `ExchangeAdapter` interface:

```python
class NewExchangeAdapter(ExchangeAdapter):
    def normalize_balance(self, raw_balance):
        # Convert exchange format to standard format
        pass
        
    def normalize_position(self, raw_position):
        # Convert exchange format to standard format  
        pass
        
    def get_symbol_format(self, symbol):
        # Convert BTC/USD to exchange format
        pass
```

## Usage Examples

### Basic Monitoring
```python
from core.monitoring import AccountMonitoringService

# Create service
service = AccountMonitoringService(
    user_id="00000000-0000-0000-0000-000000000001",
    config_id="11111111-1111-1111-1111-111111111111",
    exchange_name="bitmex",
    credentials={
        'apiKey': 'your_api_key',
        'secret': 'your_secret'
    },
    testnet=True
)

# Start monitoring
await service.start_monitoring()

# Get current state
state = await service.get_latest_state()
print(f"Available margin: {state['available_margin']} BTC")
print(f"Open positions: {len(state['position_data'])}")

# Stop monitoring
await service.stop_monitoring()
```

### Integration with Trading Logic
```python
async def check_account_before_trade(user_id, config_id):
    """Check account state before executing trade."""
    
    # Query latest account state
    conn = psycopg2.connect(...)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT equity, available_margin, position_data 
        FROM account_states 
        WHERE user_id = %s AND config_id = %s
        ORDER BY updated_at DESC LIMIT 1
    """, (user_id, config_id))
    
    row = cursor.fetchone()
    if not row:
        raise Exception("No account data available")
    
    equity, available_margin, positions = row
    
    # Risk checks
    if available_margin < 0.01:  # Need at least 0.01 BTC margin
        raise Exception("Insufficient margin")
    
    if len(positions) >= 5:  # Max 5 concurrent positions
        raise Exception("Too many open positions")
    
    return {
        'can_trade': True,
        'available_margin': available_margin,
        'position_count': len(positions)
    }
```

## Configuration

### Environment Variables
The service uses the database configuration from `core.common.config`:

```python
# From .env or defaults
DB_HOST = "localhost"
DB_PORT = "5432" 
DB_NAME = "ggbot"
DB_USER = "ggbot_user"
DB_PASS = "ggbot123"
```

### Monitoring Intervals
- **Default**: 30 seconds (good balance of freshness vs API limits)
- **Testing**: 10 seconds (for rapid testing)
- **Production**: 60+ seconds (for high-volume trading)

### Exchange Configuration
```python
EXCHANGE_CONFIG = {
    "bitmex": {
        "btc_key": "XBt",
        "btc_divisor": 100000000,
        "has_testnet": True,
        "position_always_returned": True,
        "unrealized_pnl_type": "string"
    }
}
```

## Error Handling

### Automatic Recovery
- **Connection Failures**: Automatic reconnection with exponential backoff
- **API Rate Limits**: Built-in rate limiting via CCXT
- **Data Errors**: Graceful handling of malformed responses
- **Database Issues**: Transaction rollback and retry logic

### Error Scenarios
```python
# Network issues
consecutive_errors += 1
wait_time = min(300, interval * (2 ** consecutive_errors))
await asyncio.sleep(wait_time)

# Connection recreation after 3 failures
if consecutive_errors >= 3:
    await exchange.close()
    exchange = await self._create_exchange_client()
```

## Testing

### Test Coverage
- ✅ Direct CCXT connection to BitMEX testnet
- ✅ Balance fetching and normalization  
- ✅ Position tracking with 0-position handling
- ✅ Database storage and retrieval
- ✅ Error handling and recovery
- ✅ Lifecycle management (start/stop)

### Running Tests
```bash
# Direct CCXT test
python tests/test_ccxt_direct_monitoring.py

# Full monitoring service test  
python tests/test_account_monitoring_service.py
```

### Test Results (BitMEX Testnet)
```
Available Margin: 0.64796857 BTC (~$72,000 USD)
Open Positions: 0
Monitoring Interval: 10 seconds (test mode)
Database Updates: ✅ Successfully stored
Error Recovery: ✅ Tested with invalid credentials
```

## Performance Considerations

### Resource Usage
- **Memory**: ~50MB per monitoring instance
- **CPU**: Minimal (mostly I/O waiting)
- **Network**: ~2-3 API calls per interval
- **Database**: 1 upsert per interval per exchange

### Scaling
- **Multiple Exchanges**: One service instance per exchange
- **Multiple Users**: Separate user_id/config_id combinations
- **Rate Limits**: CCXT handles exchange-specific limits automatically

### Production Optimizations
- Use connection pooling for database
- Implement Redis caching for frequently accessed data
- Add Prometheus metrics for monitoring health
- Use async database drivers (asyncpg) for better performance

## Integration Points

### Future Decision Module
The Decision Module will query `account_states` for:
- Current equity for position sizing calculations
- Available margin before opening new trades  
- Existing positions to avoid over-concentration
- Recent PNL trends for risk adjustment

```python
# Example Decision Module integration
def calculate_position_size(symbol, risk_pct=0.02):
    state = get_latest_account_state(user_id, config_id)
    max_risk = state['equity'] * risk_pct
    # ... position sizing logic using account state
```

### Trading Module Integration
The Trading Module can use monitoring data for:
- Pre-trade risk checks
- Position conflict detection
- Margin requirement validation
- Real-time P&L tracking

## Troubleshooting

### Common Issues

**Connection Errors:**
```
ECONNREFUSED: Check API credentials and network
AUTHENTICATION_FAILED: Verify API key permissions
RATE_LIMIT_EXCEEDED: Increase monitoring interval
```

**Data Issues:**
```
Foreign Key Constraint: Ensure user exists in users table
JSON Parse Error: Check JSONB data format in database
Symbol Not Found: Verify exchange symbol format
```

**Performance Issues:**
```
Slow Updates: Check database performance and indexing
Memory Growth: Monitor for connection leaks
High CPU: Reduce monitoring frequency
```

### Debug Mode
Enable detailed logging:
```python
import logging
logger.configure(handlers=[{"sink": sys.stdout, "level": logging.DEBUG}])
```

### Monitoring Health
```sql
-- Check recent updates
SELECT exchange, updated_at, equity, available_margin
FROM account_states 
WHERE user_id = 'your-user-id'
ORDER BY updated_at DESC;

-- Check update frequency
SELECT exchange, 
       COUNT(*) as update_count,
       MAX(updated_at) - MIN(updated_at) as time_range
FROM account_states
WHERE updated_at > NOW() - INTERVAL '1 hour'
GROUP BY exchange;
```

## Future Enhancements

### Planned Features
- [ ] WebSocket support for real-time updates
- [ ] Historical account state tracking
- [ ] Performance metrics and alerting
- [ ] Multi-exchange portfolio aggregation
- [ ] Risk limit monitoring and alerts

### Extension Points
- Custom adapters for new exchanges
- Pluggable alerting systems
- Custom metrics calculations
- Integration with external monitoring tools

---

*This monitoring system provides the foundation for risk-aware automated trading by ensuring real-time visibility into account state across multiple exchanges.*