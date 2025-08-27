# Paper Trading Engine

**Hummingbot API-Integrated Paper Trading System**

The paper trading engine provides realistic trading simulation using real-time market data from Hummingbot API while implementing our own execution and portfolio management logic. Each strategy (config_id) gets an isolated $10,000 paper trading account with professional-grade risk management.

## Architecture Overview

```
Decision Module → Paper Trading API → Hummingbot Market Data → Database
                      ↓                      ↓                    ↓
                Trade Execution        Real Prices         Position Tracking
                      ↓                      ↓                    ↓
                 Portfolio Mgmt       7-sec Updates        P&L Calculation
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

### PaperTradingService (`trading/paper/service.py`)
Core execution engine for paper trades.

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

**Key Methods:**
```python
# Execute trade from Decision Module intent
result = await service.execute_trade_intent(intent_dict)
# Returns: {"status": "executed", "trade_id": "uuid", "size_usd": 650.0}

# Close position manually or via triggers
result = await service.close_position(trade_id, reason='manual')

# Update all position prices (called by background task)
updated_count = await service.update_position_prices(config_id)
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
Position tracking with real-time P&L calculation.
- **Trade Lifecycle**: Open → monitoring → closed
- **Risk Management**: Stop loss and take profit levels
- **Decision Integration**: Links to Decision Module via decision_id
- **Confidence Tracking**: Preserves AI confidence scores

### paper_orders
Complete audit trail of all paper orders.
- **Order Types**: Market entry, stop loss, take profit
- **Fee Tracking**: Realistic 0.06% taker fees
- **Execution Records**: Fill prices, sizes, timestamps

## API Endpoints

All endpoints available at `/paper/*` in main API server.

### Core Trading
- `POST /paper/execute` - Execute trade from Decision Module intent
- `POST /paper/close/{trade_id}` - Close position manually
- `POST /paper/update-prices` - Trigger position price updates

### Portfolio Management  
- `GET /paper/positions/{config_id}` - Get open positions with real-time P&L
- `GET /paper/account/{config_id}` - Get account summary and performance
- `GET /paper/history/{config_id}` - Get closed trade history

### Analytics & Health
- `GET /paper/analytics/{config_id}` - Detailed performance analytics
- `GET /paper/health` - Service health check and diagnostics

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

### Position Monitoring (7-second intervals)
Automated real-time position management running as background task.

**Features:**
- **Price Updates**: Fetches current market prices every 7 seconds
- **P&L Calculation**: Updates unrealized P&L for all open positions
- **Risk Management**: Automatically triggers stop loss and take profit orders
- **Performance**: ~15KB memory per cycle, no accumulation

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

### Decision Module Changes
Updated `trigger_trading_webhook()` to call paper trading endpoint:
```python
paper_trading_url = "http://localhost:8000/paper/execute"
response = await client.post(paper_trading_url, json=intent)
```

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

### Execution Performance
- **Trade Execution**: <2 seconds from Decision Module intent to database
- **Position Updates**: Every 7 seconds for responsive risk management
- **Stop/Take Profit**: ≤7 second reaction time to market triggers
- **Concurrent Support**: 10+ positions per strategy, multiple strategies

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

### End-to-End Testing
```bash
# Test complete Decision → Paper Trading flow
curl -X POST http://localhost:8000/decision/webhooks/trigger-decision \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "config_id": "your-config-id",
    "symbol": "BTC/USDT",
    "timeframes": ["1h"]
  }'

# Check resulting paper trade
curl http://localhost:8000/paper/positions/your-config-id
```

## Production Deployment

### Startup Sequence
1. **Database Migration**: Execute `0015_create_paper_trading_tables.sql`
2. **Environment Setup**: Configure Hummingbot API credentials
3. **Service Health**: Verify Hummingbot API connectivity
4. **Background Task**: Position monitoring starts automatically
5. **API Endpoints**: Paper trading routes available at `/paper/*`

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

The paper trading engine provides professional-grade simulation with real market data, automated risk management, and comprehensive performance analytics. It integrates seamlessly with the existing ggbots platform while maintaining complete isolation between strategies and realistic trading conditions.