# Paper Trading Engine

**Supabase-Integrated Paper Trading System with Dashboard Integration**

The paper trading engine provides realistic trading simulation using real-time market data from Hummingbot API while implementing our own execution and portfolio management logic via Supabase. Each strategy (config_id) gets an isolated $10,000 paper trading account with professional-grade risk management and real-time dashboard integration.

## Recent Updates (October 2025)

**Major architectural update**: The paper trading system has been migrated from direct PostgreSQL to Supabase integration with full dashboard connectivity and real-time data display.

### Key Changes Made:

**Paper Trading Engine 2.0 (October 2025):**
1. **Leverage Calculation Fix**: P&L now correctly applies leverage multiplier (5x leverage = 5x gains/losses)
2. **Margin-Based Reservations**: Account reserves margin (position_size/leverage + fees) instead of full position size
3. **Margin Release Fix**: Positions now release the correct reserved amount via new `margin_used` field
4. **Manual Position Close**: Users can manually close positions via API and frontend button
5. **Multi-Exchange Fallback**: Automatic failover across 5 exchanges for market data reliability
6. **Position Monitoring**: Real-time 3-second price updates with batch SQL optimization (99% reduction in API calls)

**Earlier Updates (September 2025):**
1. **Fixed Money Class**: Now properly handles negative amounts for trading losses (critical bug fix)
2. **Supabase Migration**: Complete migration from direct PostgreSQL to Supabase REST API
3. **Schema Alignment**: Cleaned up field mismatches between service and database schema
4. **Configuration Fix**: Fixed validation system to work with existing config types
5. **Dashboard Integration**: Full API endpoints and frontend components for real-time data

## Architecture Overview

```
Decision Module → Supabase Paper Trading Service → Hummingbot Market Data → Supabase DB
                          ↓                              ↓                     ↓
                  Trade Execution                  Real Prices         Position Tracking
                          ↓                              ↓                     ↓
                   Portfolio Mgmt                 7-sec Updates         P&L Calculation
                          ↓                              ↓                     ↓
              Dashboard API Endpoints ← REST API ← Background Monitor → Real-time UI
```

## Core Components

### MarketDataAdapter (`trading/paper/market_data.py`)
Real-time market data integration with Hummingbot API.

**Features:**
- **KuCoin Connector**: Primary exchange for all 141 supported cryptocurrency pairs
- **Symbol Conversion**: Automatic translation between internal (`BTC/USDT`) and Hummingbot (`BTC-USDT`) formats
- **Price Caching**: 30-second TTL for efficient API usage
- **Realistic Spreads**: 0.05% bid/ask spread simulation for paper trading
- **Batch Processing**: Multiple symbol price fetching for performance

**Key Methods:**
```python
# Get current market price with bid/ask spread
price = await adapter.get_current_price('BTC/USDT')
# Returns: MarketPrice(bid=111036.95, ask=111148.05, mid=111092.50)

# Get trading rules (min order size, tick size, etc.)
rules = await adapter.get_trading_rules('BTC/USDT')

# Batch price fetching for multiple symbols
prices = await adapter.get_multiple_prices(['BTC/USDT', 'ETH/USDT'])
```

### SupabasePaperTradingService (`trading/paper/supabase_service.py`)
**NEW**: Supabase-integrated core execution engine for paper trades.

### PaperTradingService (`trading/paper/service.py`)  
**LEGACY**: Original PostgreSQL-based service (kept for reference).

**Features:**
- **Account Management**: Isolated $10k account per config_id
- **Confidence-Based Sizing**: Position size = confidence × max_position_size (10% of balance)
- **Realistic Fees**: 0.06% taker fee on all trades
- **Risk Limits**: Max 5 positions, 10x leverage, position limits
- **Automated Risk Management**: Stop loss and take profit execution

**Trade Lifecycle:**
1. **Intent Processing**: Accepts Decision Module trade intents
2. **Market Data**: Fetches current price from Hummingbot API
3. **Position Sizing**: Calculates size based on confidence score
4. **Execution**: Creates paper trade with realistic fill prices
5. **Monitoring**: Real-time P&L updates every 7 seconds
6. **Risk Management**: Automatic stop/take profit execution

**Key Methods (Supabase Service):**
```python
# Initialize Supabase service
from trading.paper.supabase_service import SupabasePaperTradingService
service = SupabasePaperTradingService()

# Execute trade from Decision Module intent
result = await service.execute_trade_intent(intent_dict)
# Returns: {"status": "executed", "trade_id": "uuid", "size_usd": 650.0}

# Close position manually or via triggers
result = await service.close_position(trade_id, reason='manual')

# Update all position prices (called by background task)
updated_count = await service.update_position_prices(config_id)

# Get account summary for dashboard
summary = await service.get_account_summary(config_id)

# Get open positions for dashboard  
positions = await service.get_open_positions(config_id)

# Get trade history
trades = await service.get_trade_history(config_id, limit=100)
```

### PositionManager (`trading/paper/positions.py`)
Advanced portfolio analytics and position tracking.

**Features:**
- **Portfolio Metrics**: Total P&L, win rate, exposure analysis
- **Risk Analytics**: Concentration risk, drawdown analysis, position limits
- **Performance Tracking**: Trade statistics, confidence score correlation
- **Position Suggestions**: AI-powered risk management recommendations

**Key Methods:**
```python
# Get comprehensive portfolio overview
portfolio = await manager.get_portfolio_summary(config_id)
# Returns: PortfolioSummary with balance, P&L, win rate, etc.

# Get detailed risk metrics
risk_metrics = await manager.get_position_risk_metrics(config_id)

# Performance analytics with trade breakdown
analytics = await manager.get_performance_analytics(config_id, days=30)
```

## Database Schema

### paper_accounts
Isolated trading accounts with $10,000 starting balance per config_id.
- **Isolation**: Each strategy gets independent paper account
- **Performance Tracking**: Win rate, total trades, cumulative P&L
- **Balance Management**: Real-time available balance updates

### paper_trades
Position tracking with real-time P&L calculation (V2.0 with leverage fixes).
- **Trade Lifecycle**: Open → monitoring → closed
- **Leverage Support**: Stores leverage multiplier and calculates correct P&L
- **Margin Tracking**: `margin_used` field tracks actual reserved amount for accurate release
- **Risk Management**: Stop loss and take profit levels with leveraged execution
- **Decision Integration**: Links to Decision Module via decision_id
- **Confidence Tracking**: Preserves AI confidence scores

### paper_orders
Complete audit trail of all paper orders.
- **Order Types**: Market entry, stop loss, take profit
- **Fee Tracking**: Realistic 0.06% taker fees
- **Execution Records**: Fill prices, sizes, timestamps

## API Endpoints

**UPDATED**: All endpoints now use Supabase backend and are integrated into main API at `/api/v2/bot/*`.

### Dashboard Integration (V2.0)
- `GET /api/v2/bot/{config_id}/metrics` - Performance metrics with P&L data for dashboard charts
- `GET /api/v2/bot/{config_id}/positions` - Live positions formatted for dashboard tables (with correct leverage P&L)
- `GET /api/v2/bot/{config_id}/trades` - Closed trade history for dashboard
- `GET /api/v2/bot/{config_id}/account` - Account summary and statistics
- `POST /api/v2/bot/{config_id}/positions/{trade_id}/close` - **NEW**: Manually close any open position

### Legacy Paper Trading Endpoints (if still needed)
- `POST /paper/execute` - Execute trade from Decision Module intent
- `POST /paper/close/{trade_id}` - Close position manually
- `POST /paper/update-prices` - Trigger position price updates
- `GET /paper/positions/{config_id}` - Get open positions with real-time P&L
- `GET /paper/account/{config_id}` - Get account summary and performance
- `GET /paper/history/{config_id}` - Get closed trade history
- `GET /paper/health` - Service health check and diagnostics

### Dashboard Data Format
```json
{
  "status": "success",
  "config_id": "uuid",
  "metrics": {
    "profit_loss_data": [{"date": "2025-09-09", "profit": -0.30}],
    "trade_stats": {
      "totalTrades": 5,
      "winRate": 0.0,
      "totalProfit": -0.30
    },
    "account_balance": 9900.02,
    "total_pnl": -0.18,
    "initial_balance": 10000.0
  }
}
```

## Configuration

### Environment Variables
```bash
# Paper Trading Settings
HBOT_USERNAME="sev"                    # Hummingbot API username
HBOT_PASSWORD="your_hummingbot_password"      # Hummingbot API password

# Optional Configuration  
PAPER_TRADING_URL="http://localhost:8000/paper/execute"  # Custom endpoint URL
```

### Service Configuration
```python
# PaperTradingService defaults
initial_balance = 10000.00      # $10k starting balance
max_position_pct = 0.10          # 10% max position size  
taker_fee = 0.0006              # 0.06% trading fee
max_leverage = 10               # Maximum leverage allowed
max_positions = 5               # Maximum concurrent positions
```

## Background Processing

### Position Monitoring (3-second intervals)
Automated real-time position management running as background task.

**Features:**
- **Price Updates**: Fetches current market prices every 3 seconds
- **P&L Calculation**: Updates unrealized P&L with correct leverage multiplier for all open positions
- **Risk Management**: Automatically triggers stop loss and take profit orders with leveraged P&L
- **Batch Optimization**: Single SQL query updates 100+ positions (99% reduction from individual HTTP requests)
- **Performance**: Reliable monitoring with ConnectionTerminated errors eliminated

**Automatic Execution:**
```python
# Stop Loss Triggers
if side == "long" and current_price <= stop_loss:
    await close_position(trade_id, "stop_loss", current_price)

if side == "short" and current_price >= stop_loss:
    await close_position(trade_id, "stop_loss", current_price)

# Take Profit Triggers  
if side == "long" and current_price >= take_profit:
    await close_position(trade_id, "take_profit", current_price)

if side == "short" and current_price <= take_profit:
    await close_position(trade_id, "take_profit", current_price)
```

## Integration with Decision Module

The paper trading engine integrates seamlessly with the existing Decision Module via the webhook pattern.

### Trade Intent Flow
```python
# Decision Module generates intent
intent = {
    "decision_id": "uuid",
    "user_id": "uuid", 
    "config_id": "uuid",
    "symbol": "BTC/USDT",
    "action": "long",           # or "short"
    "confidence": 0.75,         # 0.0 to 1.0
    "stop_loss_price": 108000,  # Optional
    "take_profit_price": 115000, # Optional
    "reasoning": "Strong breakout signal with volume confirmation"
}

# Paper trading executes automatically
# Position size: 0.75 × 10% × $10k = $750
# Entry: BTC @ $111,092 (mid-price from Hummingbot API)
# Result: 0.00675 BTC position with automated risk management
```

### Decision Module Integration (IMPORTANT FOR OTHER DEVELOPERS)

**UPDATED**: Decision Module should now use the new Supabase service:

```python
# NEW: Use Supabase service directly
from trading.paper.supabase_service import SupabasePaperTradingService

async def trigger_paper_trading(intent_dict):
    service = SupabasePaperTradingService()
    result = await service.execute_trade_intent(intent_dict)
    return result

# OR: Use REST API endpoint (if preferred)
paper_trading_url = "http://localhost:8000/api/v2/bot/{config_id}/execute"
response = await client.post(paper_trading_url, json=intent)
```

**Key Changes for Decision Module Developers:**
1. **New Service Class**: Use `SupabasePaperTradingService` instead of `PaperTradingService`
2. **Money Class Fixed**: Trading losses now work properly (negative P&L supported)
3. **Config Loading Fixed**: Existing configs with `config_type: 'autonomous_trading'` now load correctly
4. **Account Creation**: Paper accounts are auto-created on first trade execution
5. **Real-time Data**: All trades immediately appear in dashboard with live P&L updates

## Symbol Support

**All 141 cryptocurrency pairs** supported through KuCoin connector:
- **Major Pairs**: BTC/USDT, ETH/USDT, SOL/USDT, etc.
- **Symbol Conversion**: Automatic format translation via UniversalSymbolStandardizer
- **Trading Rules**: Real-time min order sizes, tick sizes from Hummingbot API

## Performance Characteristics

### Resource Usage
- **Memory**: ~15KB per update cycle (flat, no accumulation)
- **API Calls**: ~514 calls/hour to Hummingbot API (localhost)
- **Database**: Simple UPDATE queries, indexed by trade_id
- **CPU**: Minimal for price comparisons and P&L calculations

### Execution Performance (V2.0)
- **Trade Execution**: <2 seconds from Decision Module intent to database
- **Position Updates**: Every 3 seconds for responsive risk management
- **Stop/Take Profit**: ≤3 second reaction time to market triggers with correct leverage
- **Batch Optimization**: 100+ positions updated in single SQL query
- **Concurrent Support**: 100+ positions across multiple strategies simultaneously

## Monitoring & Health Checks

### Service Health
```bash
# Check paper trading service health
curl http://localhost:8000/paper/health

# Response includes:
# - Market data adapter connectivity
# - Database connection status  
# - Cache statistics
# - Error diagnostics
```

### Position Monitoring
```sql
-- View real-time position summary
SELECT * FROM paper_trading_summary WHERE config_id = 'your-config-id';

-- Check background task performance
SELECT COUNT(*) as open_positions, 
       SUM(unrealized_pnl) as total_unrealized_pnl,
       AVG(confidence_score) as avg_confidence
FROM paper_trades 
WHERE status = 'open';
```

## Testing & Validation

### Connectivity Testing
```bash
# Test Hummingbot API integration
python test_hummingbot_api.py

# Expected output:
# ✅ Health Check: healthy
# ✅ Symbol Conversion: BTC/USDT → BTC-USDT  
# ✅ Price Fetching: BTC/USDT: $111,092.50
# ✅ Trading Rules: Min size 0.00001 BTC
# ✅ Multiple Prices: BTC, ETH prices fetched
```

### End-to-End Testing (UPDATED)
```bash
# Test Supabase service directly
python test_supabase_paper_service.py

# Test API endpoints
python test_paper_trading_api.py

# Test trade execution with real data
curl -X POST http://localhost:8000/api/v2/bot/{config_id}/execute \
  -H "Content-Type: application/json" \
  -d '{
    "config_id": "04b4a272-8303-4770-a536-6d210b9defba",
    "user_id": "00000000-0000-0000-0000-000000000000",
    "symbol": "BTC/USDT",
    "action": "long",
    "confidence": 0.75
  }'

# Check dashboard data
curl http://localhost:8000/api/v2/bot/{config_id}/metrics
curl http://localhost:8000/api/v2/bot/{config_id}/positions  
curl http://localhost:8000/api/v2/bot/{config_id}/account
```

### Current Testing Status (October 2025 - V2.0)
**✅ WORKING (Paper Trading Engine 2.0)**:
- Trade execution with correct leverage calculations (5x = 5x gains/losses)
- Margin-based balance reservations (position_size/leverage + fees)
- Manual position closing via API and frontend
- Account creation and accurate P&L tracking
- Supabase database integration with `margin_used` field
- Dashboard API endpoints with leveraged P&L display
- Background position monitoring (3-second intervals, batch SQL optimization)
- Stop loss and take profit execution with correct leverage
- Multi-exchange fallback (5 exchanges: kucoin→binance→okx→gate_io→ascend_ex)

**✅ TESTED (V2.0)**:
- Leverage P&L calculations: 5x leverage correctly multiplies gains/losses
- Margin reservations: $700 position at 5x reserves $140.84 (not $704.20)
- Position closing: Releases correct margin amount via `margin_used` field
- Balance reconciliation: All trades maintain correct balances with fees
- Manual close functionality: API and frontend button working
- Multiple test scenarios: 1x to 20x leverage all calculate correctly

## Production Deployment

### Startup Sequence (V2.0)
1. **Supabase Setup**: Ensure paper_accounts, paper_trades, paper_orders tables exist (with `margin_used` field)
2. **Environment Setup**: Configure SUPABASE_URL, SUPABASE_SERVICE_KEY, HBOT credentials
3. **Service Health**: Verify Supabase and Hummingbot API connectivity
4. **Background Task**: Position monitoring running at 3-second intervals with batch optimization
5. **API Endpoints**: Dashboard routes available at `/api/v2/bot/*` with leverage-corrected P&L

### Position Monitoring (ACTIVE)
**STATUS**: ✅ Running in production with batch SQL optimization

The position monitoring system updates all open positions every 3 seconds:
```python
# Automatically runs every 3 seconds as background task
updated_count = await service.update_position_prices()  # Updates all open positions
# Uses batch SQL: 100 positions = 1 query (99% reduction from 100 HTTP requests)
```

**Features**:
- Real-time P&L updates with correct leverage multiplier
- Automatic SL/TP execution
- Batch SQL optimization for reliability
- Multi-exchange price fallback

### Monitoring
- **Position Updates**: Logged every ~30 seconds (consolidated logging)
- **Trade Events**: Stop/take profit executions logged immediately
- **Health Checks**: Service diagnostics via `/paper/health`
- **Performance**: Cache statistics and update metrics tracked

### Scaling Considerations
- **Multi-Strategy**: Each config_id gets isolated paper account
- **Resource Limits**: 7-second updates scale well to 100+ positions
- **API Rate Limits**: Hummingbot API (localhost) handles 500+ calls/hour easily
- **Database Performance**: Optimized indexes for position lookups

---

## Paper Trading Engine 2.0 Summary

The paper trading engine provides **professional-grade simulation** with real market data, automated risk management, and comprehensive performance analytics.

### V2.0 Key Improvements:
- ✅ **Accurate Leverage**: 5x leverage now shows 5x gains/losses (previously showed 1x)
- ✅ **Correct Margin**: Reserves position_size/leverage + fees (previously reserved full position size)
- ✅ **Manual Control**: Users can close positions anytime via frontend button
- ✅ **Reliable Monitoring**: 3-second updates with batch SQL (99% reduction in API calls)
- ✅ **Multi-Exchange**: Automatic failover across 5 exchanges for market data

### Upcoming: Database Reset
All paper accounts will be reset to $10,000 as part of the V2.0 launch to ensure accurate simulation with the corrected leverage calculations. Bots with custom strategies will remain active; default strategy bots will be deactivated for user reconfiguration.

---

The paper trading engine integrates seamlessly with the ggbots platform while maintaining complete isolation between strategies and realistic trading conditions that prepare users for real trading.