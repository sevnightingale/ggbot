# Symphony Metrics Testing

This directory contains scripts to test Symphony API integration and understand what data is available for dashboard metrics.

## Overview

The Symphony live trading integration is complete, but dashboard metrics need to be updated to handle both paper and live trading data. These test scripts help us:

1. **Explore** what data Symphony API provides
2. **Map** Symphony responses to our dashboard format
3. **Identify** gaps and workarounds needed
4. **Plan** the implementation of unified metrics

## Quick Start

### 1. Find Live Trading Bots

```bash
cd /home/sev/ggbot
source .venv/bin/activate
python scripts/find_live_bots.py
```

This will show all live trading bots with their configuration and provide test commands.

### 2. Test Symphony Metrics

```bash
python scripts/test_symphony_metrics.py \
  --user-id <USER_UUID> \
  --config-id <CONFIG_UUID>
```

This will:
- Query Symphony API with real credentials
- Extract all available metrics
- Show mapping to frontend format
- Provide recommendations

## What Symphony Provides

### Account Summary (via `/agent/all-positions`)

✅ **Available:**
- Total equity (current balance)
- Total P&L (realized + unrealized)
- Realized P&L
- Unrealized P&L
- Available balance
- Margin used
- Total volume traded
- Total fees paid
- **Total trades count** ← Dashboard needs this
- ROI percentage ← Dashboard needs this
- Closed positions count
- Liquidated positions count

❌ **NOT Available:**
- Win/loss trade breakdown
- Win rate percentage
- Historical balance snapshots (for equity curve)
- Trade close reasons

### Positions (via `/agent/positions`)

✅ **Available per position:**
- Symbol (as `asset`: "BTC", "SOL", etc.)
- Side (as `isLong`: true/false)
- Entry price
- Current price
- Position size
- Collateral amount
- Leverage
- Unrealized P&L (USD and %)
- Stop loss price
- Take profit price
- Liquidation price
- Created timestamp
- Status (Open/Closed)

## Symphony Response Examples

### Account Summary

```json
{
  "success": true,
  "data": {
    "accountSummary": {
      "totalEquity": 53.28,
      "initialCapital": 55.0,
      "totalUnrealizedPnl": 0,
      "totalRealizedPnl": -0.2,
      "totalPnl": -0.21,
      "totalFeesPaid": 0.17,
      "availableBalance": 45.29,
      "marginUsed": 7.99,
      "totalVolume": 139.75,
      "totalTrades": 1,
      "openPositionsCount": 1,
      "closedPositionsCount": 1,
      "performance": {
        "roi": -1.72,
        "roiPercent": -3.12,
        "totalTrades": 1,
        "averageTradeSize": 49.99
      }
    },
    "openPositions": [...]
  }
}
```

### Positions

```json
{
  "positions": [{
    "batchId": "uuid",
    "smartAccount": "0x...",
    "asset": "SOL",
    "isLong": true,
    "entryPrice": 203.39,
    "currentPrice": 203.43,
    "pnlUSD": 0.011,
    "pnlPercentage": 0.087,
    "collateralAmount": 12.72,
    "leverage": 2,
    "positionSize": 11.05,
    "slPrice": 0,
    "tpPrice": 0,
    "liquidationPrice": 0,
    "createdTimestamp": "2025-01-19T...",
    "status": "Open"
  }]
}
```

## Dashboard Metrics Mapping

### What We Can Calculate

| Dashboard Metric | Symphony Source | Notes |
|-----------------|-----------------|-------|
| **Current Balance** | `totalEquity` | Direct mapping ✅ |
| **Total P&L** | `totalPnl` | Direct mapping ✅ |
| **Return %** | `performance.roiPercent` | Direct mapping ✅ |
| **Total Trades** | `accountSummary.totalTrades` | Direct mapping ✅ |
| **Open Positions** | `openPositionsCount` | Direct mapping ✅ |
| **Closed Positions** | `closedPositionsCount` | Direct mapping ✅ |

### What Requires Workarounds

| Dashboard Metric | Workaround | Implementation |
|-----------------|-----------|----------------|
| **Win Rate** | Query `/agent/batches` + `/agent/batch-positions` | Iterate closed batches, count `pnlUSD > 0` |
| **Equity Curve** | Store periodic snapshots in DB | Create `live_balance_history` table |
| **Trade History** | Query all batches on demand | Cache in `live_trades_history` table |

## Implementation Plan

### Phase 1: Basic Metrics (High Priority)

**Goal:** Show current balance, P&L, and positions for live bots

**Endpoints to create:**

```python
# ggbot.py

@app.get("/api/v2/account/live/{config_id}")
async def get_live_account_metrics(config_id: str):
    """
    Get account metrics for live trading bot from Symphony.
    Returns same format as paper trading endpoint.
    """
    # 1. Load config to get user_id and symphony_agent_id
    # 2. Get Symphony credentials from Vault
    # 3. Query /agent/all-positions?userAddress={smart_account}
    # 4. Extract metrics:
    #    - current_balance = totalEquity
    #    - total_pnl = totalPnl
    #    - total_trades = totalTrades
    #    - portfolio_return_pct = performance.roiPercent
    #    - open_positions = openPositionsCount
    # 5. Return in Account format
    pass

@app.get("/api/v2/positions/live/{config_id}")
async def get_live_positions(config_id: str):
    """
    Get open positions for live trading bot from Symphony.
    Already implemented in symphony_service.get_open_positions()
    """
    pass
```

**Frontend changes:**

```typescript
// lib/api.ts

async getAccountMetrics(configId: string, tradingMode: string) {
  const endpoint = tradingMode === 'live'
    ? `/api/v2/account/live/${configId}`
    : `/api/live-position-data?config_id=${configId}`

  return this.get(endpoint)
}
```

### Phase 2: Trade History (Medium Priority)

**Goal:** Show closed trades with win/loss breakdown

**Endpoints to create:**

```python
@app.get("/api/v2/trades/live/{config_id}")
async def get_live_trade_history(config_id: str, limit: int = 50):
    """
    Get closed trade history from Symphony.
    Returns same format as paper trade history endpoint.
    """
    # 1. Query /agent/batches?agentId={agent_id}
    # 2. Filter closed batches
    # 3. For each batch, query /agent/batch-positions?batchId={id}
    # 4. Map to Trade format:
    #    - trade_id = batchId
    #    - symbol = from_symphony(asset)
    #    - side = "long" if isLong else "short"
    #    - realized_pnl = pnlUSD
    #    - close_reason = "symphony_close" (Symphony doesn't track this)
    # 5. Calculate win/loss: count where pnlUSD > 0
    # 6. Return in TradeHistory format
    pass
```

### Phase 3: Equity Curve (Low Priority)

**Goal:** Show balance over time visualization

**Database table:**

```sql
CREATE TABLE live_balance_history (
    id SERIAL PRIMARY KEY,
    config_id UUID NOT NULL REFERENCES configurations(config_id),
    balance DECIMAL(18, 8) NOT NULL,
    unrealized_pnl DECIMAL(18, 8),
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_live_balance_config_time
  ON live_balance_history(config_id, timestamp DESC);
```

**Background job:**

```python
# Add to position monitoring service or create new job
async def snapshot_live_balances():
    """Periodically snapshot Symphony account balances for equity curve."""
    # Every 1 hour:
    # 1. Get all active live bots
    # 2. Query Symphony account summary
    # 3. Insert balance snapshot to live_balance_history
    # 4. Keep last 1000 snapshots per config
    pass
```

## Testing Checklist

- [ ] Run `find_live_bots.py` to identify test bot
- [ ] Run `test_symphony_metrics.py` with live bot credentials
- [ ] Verify Symphony API responses
- [ ] Confirm metric mappings are correct
- [ ] Identify any missing data points
- [ ] Test with bot that has open positions
- [ ] Test with bot that has closed trades
- [ ] Test error handling (invalid credentials, no positions, etc.)

## Expected Output

```
================================================================================
SYMPHONY METRICS TEST - Dashboard Data Extraction
================================================================================

[1/6] Getting Symphony credentials from Vault...
✅ API key: sk_live_... (length: 64)
✅ Smart account: 0x1234...5678

[2/6] Loading bot configuration...
✅ Bot: BTC Scalper (Live)
✅ Trading mode: live
✅ Symphony agent ID: 22b35152-f3a5-4b21-8a0f-04691c155e33

[3/6] Querying Symphony /agent/positions endpoint...
✅ Retrieved 2 positions, 0 orders

📊 Positions Response:
{
  "agentId": "22b35152...",
  "positionsCount": 2,
  "positions": [...]
}

[4/6] Querying Symphony /agent/all-positions endpoint...
✅ Retrieved account summary

📊 Account Summary Response:
{
  "success": true,
  "data": {
    "accountSummary": {...},
    "openPositions": [...]
  }
}

[5/6] Extracting Dashboard Metrics...

📈 DASHBOARD METRICS:
--------------------------------------------------------------------------------
Total Equity....................... $53.28
Total P&L.......................... $-1.72
ROI Percent........................ -3.12%
Total Trades....................... 1
Open Positions Count............... 2
Win Rate........................... N/A (not provided by Symphony)

[6/6] Mapping to Frontend Format...

🎨 FRONTEND DATA STRUCTURE:
{
  "account": {
    "current_balance": 53.28,
    "total_trades": 1,
    "portfolio_return_pct": -3.12,
    ...
  },
  "positions": [...],
  "warnings": [...]
}

================================================================================
ANALYSIS & RECOMMENDATIONS
================================================================================

✅ AVAILABLE FROM SYMPHONY:
  ✓ Total equity (current balance)
  ✓ Total P&L (realized + unrealized)
  ✓ ROI percentage
  ✓ Individual position details
  ...

❌ NOT AVAILABLE FROM SYMPHONY:
  ✗ Win trades count
  ✗ Win rate percentage
  ✗ Equity curve data points
  ...

💡 RECOMMENDATIONS:
  1. For current balance: Use totalEquity from account summary
  2. For win rate: Query /agent/batches + iterate closed positions
  ...

🔧 IMPLEMENTATION PLAN:
  1. Create get_live_account_metrics() endpoint
  2. Create get_live_trade_history() endpoint
  3. Update dashboard to route based on trading_mode
  ...
```

## Next Steps

1. ✅ Test Symphony API with real credentials
2. ⏳ Implement `/api/v2/account/live/{config_id}` endpoint
3. ⏳ Update frontend to use unified account metrics API
4. ⏳ Implement trade history endpoint with win/loss calculation
5. ⏳ Add equity curve snapshot job (optional)

## Related Files

- `trading/live/symphony_service.py` - Symphony service implementation
- `frontend/app/forge/components/monitor/PerformanceChart.tsx` - Dashboard metrics display
- `frontend/app/forge/components/monitor/PositionsTable.tsx` - Positions display
- `DOCS/SYMPHONY.md` - Symphony API documentation
- `DOCS/SYMPHONY_PLAN.md` - Integration design plan

## Support

If you encounter issues:

1. Check Symphony API key is valid in Settings
2. Verify smart account address is correct
3. Ensure bot has `trading_mode = 'live'`
4. Check logs: `pm2 logs ggbot`
5. Test with Symphony portal directly
