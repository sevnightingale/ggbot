# Unified Account Monitoring System

**Date**: 2025-11-14
**Status**: ✅ Operational in production

---

## Overview

Unified monitoring service that tracks account state (balance, P&L, positions) for **all trading modes** (paper, Symphony, AsterDEX) with consistent storage and interfaces.

**Problem Solved**: Previously, only paper trading had dedicated monitoring. Symphony and Aster data was queried on-demand from APIs with no historical tracking. The frontend (tv-timeline) made inefficient direct API calls every time.

**Solution**: Universal Account Monitor service that:
- Monitors all trading modes at same cadence (5-second checks)
- Stores snapshots in unified `account_snapshots` table
- Provides historical time-series data for charts
- Single source of truth for account state

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│     Universal Account Monitor Service (PM2)             │
│     core/monitoring/universal_account_monitor.py        │
│     5s monitoring loop, 5min heartbeat snapshots        │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┬──────────────┐
        │                     │              │
   ┌────▼────┐          ┌────▼────┐   ┌────▼────┐
   │  Paper  │          │Symphony │   │  Aster  │
   │ Adapter │          │ Adapter │   │ Adapter │
   └────┬────┘          └────┬────┘   └────┬────┘
        │                    │              │
   ┌────▼────────┐     ┌────▼───────┐ ┌───▼─────────┐
   │paper_       │     │Symphony    │ │AsterDEX     │
   │accounts     │     │API         │ │API          │
   │(DB)         │     │            │ │             │
   └─────────────┘     └────────────┘ └─────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │account_snapshots │
                    │  (unified DB)    │
                    └──────────────────┘
```

### Database Schema

**Table**: `account_snapshots`

```sql
CREATE TABLE account_snapshots (
    snapshot_id UUID PRIMARY KEY,
    config_id UUID NOT NULL,
    user_id UUID NOT NULL,
    trading_mode VARCHAR(20) NOT NULL,  -- 'paper', 'symphony', 'aster'
    timestamp TIMESTAMPTZ NOT NULL,

    -- Balance
    current_balance NUMERIC(20, 8),      -- NULL for Symphony (API doesn't provide yet)
    available_balance NUMERIC(20, 8),
    margin_used NUMERIC(20, 8),

    -- P&L
    total_pnl NUMERIC(20, 8) NOT NULL,
    realized_pnl NUMERIC(20, 8),
    unrealized_pnl NUMERIC(20, 8),

    -- Performance
    total_trades INTEGER NOT NULL,
    win_trades INTEGER NOT NULL,
    loss_trades INTEGER NOT NULL,
    win_rate NUMERIC(5, 4),

    -- Positions
    open_positions INTEGER NOT NULL,
    position_value NUMERIC(20, 8),
    total_exposure NUMERIC(20, 8),

    -- Advanced metrics
    avg_win NUMERIC(20, 8),
    avg_loss NUMERIC(20, 8),
    largest_win NUMERIC(20, 8),
    largest_loss NUMERIC(20, 8),
    sharpe_ratio NUMERIC(10, 4),
    max_drawdown NUMERIC(20, 8),

    -- Metadata
    raw_data JSONB,                      -- Original API response for debugging
    balance_change_pct NUMERIC(10, 4),
    is_heartbeat BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL
);
```

**Indexes**:
- `idx_snapshots_config_time` - Fast lookups by bot
- `idx_snapshots_user_time` - Fast lookups by user
- `idx_snapshots_mode_time` - Fast lookups by trading mode
- `idx_snapshots_heartbeat` - Filter heartbeat vs change snapshots
- `idx_snapshots_latest` - Fast latest snapshot queries

---

## Adapter Pattern

### Paper Account Adapter
**Source**: `core/monitoring/adapters/paper_adapter.py`

**Data Source**: Queries `paper_accounts` and `paper_trades` tables directly

**Provides**:
- ✅ Current balance
- ✅ Total P&L (realized + unrealized)
- ✅ Trade statistics (win rate, avg win/loss)
- ✅ Position metrics

### Symphony Account Adapter
**Source**: `core/monitoring/adapters/symphony_adapter.py`

**Data Source**: Symphony API via `SymphonyLiveTradingService`

**API Calls**:
- `symphony.get_account_metrics(config_id)` - P&L and trade stats
- `symphony.get_open_positions(config_id)` - Position data

**Provides**:
- ❌ Current balance (API doesn't provide yet - pending Symphony dev)
- ✅ Total P&L
- ✅ Trade statistics
- ✅ Position metrics

**Note**: 1 Symphony wallet = 1 bot (or multiple bots share 1 wallet if desired)

### Aster Account Adapter
**Source**: `core/monitoring/adapters/aster_adapter.py`

**Data Source**: AsterDEX API via `AsterDEXV3LiveTradingService`

**API Calls**:
1. **`GET /fapi/v3/account`** - Account-wide balance and positions
   - Returns: `totalWalletBalance`, `totalUnrealizedProfit`, `availableBalance`, `positions[]`
2. **`GET /fapi/v3/income`** - Historical P&L and trade data
   - Returns: Income records with `REALIZED_PNL` entries for calculating trade stats

**Provides**:
- ✅ Current balance (USDT + USDC combined)
- ✅ Total P&L (realized + unrealized)
- ✅ Trade statistics (from income history)
- ✅ Position metrics (from account positions array)

**Note**: 1 Aster wallet = 1 bot (or multiple bots share 1 wallet if desired). API returns account-wide data, which is correct behavior.

---

## Monitoring Logic

### Check Frequency
- **Monitoring loop**: Every 5 seconds
- **Snapshot storage**: On-change OR 5-minute heartbeat

### Storage Triggers
Snapshots are saved when:
1. **Position opened/closed** - Immediate snapshot
2. **Balance changed >0.1%** - Significant balance movement
3. **5-minute heartbeat** - Even if no change (for gap detection)

### Storage Efficiency

| Frequency | Storage/Day | Storage/Month | Storage/Year |
|-----------|-------------|---------------|--------------|
| **Current (on-change + heartbeat)** | ~600 KB | ~18 MB | ~220 MB |
| Every 3 seconds (alternative) | 173 MB | 5.2 GB | 62 GB |

**Current approach**: ~220 MB/year at current scale (258 users, 4 active bots)

---

## PM2 Service Configuration

**Service**: `account-monitor`
**Script**: `core/monitoring/universal_account_monitor.py`
**Memory Limit**: 300 MB
**Auto-restart**: Enabled

```javascript
{
  name: 'account-monitor',
  script: '/home/sev/ggbot/core/monitoring/universal_account_monitor.py',
  interpreter: '/home/sev/ggbot/.venv/bin/python',
  cwd: '/home/sev/ggbot',
  instances: 1,
  exec_mode: 'fork',
  autorestart: true,
  max_memory_restart: '300M',
  env: {
    PYTHONPATH: '/home/sev/ggbot',
    DATABASE_URL: process.env.DATABASE_URL,
    SUPABASE_URL: process.env.SUPABASE_URL,
    SUPABASE_SERVICE_KEY: process.env.SUPABASE_SERVICE_KEY,
    REDIS_URL: process.env.REDIS_URL,
    ASTER_API_KEY: process.env.ASTER_API_KEY,
    ASTER_API_SECRET: process.env.ASTER_API_SECRET
  }
}
```

**Management**:
```bash
pm2 status account-monitor
pm2 logs account-monitor
pm2 restart account-monitor
```

---

## Critical Fixes Applied

### 1. ConfigService Method Name Error
**Issue**: `'ConfigService' object has no attribute 'update_state'`
**Location**: `ggbot.py:350`
**Fix**: Changed `update_state()` to `set_bot_state()`
**Impact**: Bot execution permission checks now work correctly

### 2. Kimi K2 Thinking Model Blank Response
**Issue**: Thinking models (Kimi K2, DeepSeek R1) put response in `reasoning` field instead of `content` field
**Location**: `decision/llm_providers/openrouter_provider.py`
**Fix**: Added fallback to check `message.reasoning` when `content` is empty
**Impact**: Thinking models now work correctly, no more blank responses

### 3. Redis WebSocket Timezone Error
**Issue**: `Cannot subtract tz-naive and tz-aware datetime-like objects`
**Location**: `market_intelligence/adapters/market_data/redis_websocket.py:90`
**Fix**: Added `utc=True` parameter to `pd.to_datetime()`
**Impact**: Redis WebSocket adapter works without timezone errors

### 4. Aster Adapter Using Wrong API Endpoints
**Issue**: Adapter was calculating P&L incorrectly from wrong data sources
**Location**: `core/monitoring/adapters/aster_adapter.py`
**Fix**: Changed to use `/fapi/v3/account` + `/fapi/v3/income` endpoints
**Impact**: Aster snapshots now show correct balance and P&L from API

---

## Current Status

### Production Metrics
- **Active Bots**: 2-3 (1-2 paper, 1 aster)
- **Snapshots Stored**: 31 (as of 2025-11-14 11:08:25 UTC)
- **Monitoring Frequency**: 5-second checks
- **Storage Frequency**: 5-minute heartbeats
- **Service Uptime**: 100% since 10:12:58 UTC

### Latest Snapshots (2025-11-14 11:08:25 UTC)

**Paper Bot (1f5280ff - ggShot)**:
- Balance: $10,000.00
- Total P&L: $0.00
- Open Positions: 0
- Total Trades: 0

**Aster Bot (bb2560fd - ggAster)**:
- Balance: -$29.03
- Total P&L: -$60.99 (realized)
- Unrealized P&L: $0
- Open Positions: 0
- Total Trades: 18

### Service Health
```
✅ account-monitor    online    300MB memory
✅ ggbot              online    250MB memory
✅ market-data-ws     online    163MB memory
✅ signal-listener    online    63MB memory
✅ x-bot              online    44MB memory
✅ error-alerts       online    34MB memory
```

---

## Benefits Achieved

### Before
- ❌ Only paper trading had monitoring
- ❌ Symphony/Aster queried on-demand only
- ❌ No historical data for Symphony/Aster
- ❌ Frontend made direct API calls (inefficient)
- ❌ Different code paths for each mode
- ❌ Inconsistent data shapes

### After
- ✅ All modes monitored at same 5s cadence
- ✅ Historical time-series data for ALL modes
- ✅ Unified storage in single table
- ✅ Clean adapter pattern architecture
- ✅ Efficient on-change + heartbeat storage
- ✅ Single source of truth for account state
- ✅ Ready for unified API endpoints

---

## Next Steps

### Phase 1: API Endpoints (Recommended Next)
Create unified REST API endpoints:

```
GET /api/v2/account/{config_id}/current
GET /api/v2/account/{config_id}/history?period=24h&interval=5m
GET /api/v2/account/{config_id}/balance-series
```

**Benefits**:
- Frontend queries database instead of direct API calls
- Consistent interface for all trading modes
- Faster response times (database vs API)
- Historical data available for charts

### Phase 2: Frontend Integration
Update tv-timeline component to use new unified endpoints:
- Replace direct Aster API calls with `/api/v2/account/{config_id}/balance-series`
- Remove inefficient P&L calculation logic
- Use cached snapshot data

### Phase 3: Legacy Cleanup
Once validated, remove:
- Old monitoring logic in `core/monitoring/service.py` (if no longer needed)
- Direct API call patterns in frontend
- Duplicate data fetching code paths

### Phase 4: Symphony Balance Support
When Symphony API adds balance endpoint:
- Update `SymphonyAccountAdapter.supports_balance()` to return `True`
- Add balance extraction from Symphony API response
- Snapshots will automatically include balance data

---

## File Locations

### Core Services
- **Monitor Service**: `core/monitoring/universal_account_monitor.py`
- **Domain Model**: `core/domain/account_snapshot.py`

### Adapters
- **Paper**: `core/monitoring/adapters/paper_adapter.py`
- **Symphony**: `core/monitoring/adapters/symphony_adapter.py`
- **Aster**: `core/monitoring/adapters/aster_adapter.py`
- **Index**: `core/monitoring/adapters/__init__.py`

### Database
- **Migration**: `database/migrations/add_account_snapshots_table.sql`

### Configuration
- **PM2 Config**: `ecosystem.config.js` (account-monitor service)

---

## Query Examples

### Get Latest Snapshot for Bot
```sql
SELECT *
FROM account_snapshots
WHERE config_id = 'bb2560fd-b053-464f-8a58-8e254e4d36fa'
ORDER BY timestamp DESC
LIMIT 1;
```

### Get Balance History (24h, 5min intervals)
```sql
SELECT timestamp, current_balance, total_pnl, unrealized_pnl
FROM account_snapshots
WHERE config_id = 'bb2560fd-b053-464f-8a58-8e254e4d36fa'
  AND timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp ASC;
```

### Get All User Bots Current State
```sql
SELECT DISTINCT ON (config_id)
    config_id,
    trading_mode,
    current_balance,
    total_pnl,
    open_positions,
    timestamp
FROM account_snapshots
WHERE user_id = 'd4356014-0359-4b25-9936-a1d38db4db7c'
ORDER BY config_id, timestamp DESC;
```

### Compare Performance Across Modes
```sql
SELECT
    trading_mode,
    COUNT(DISTINCT config_id) as num_bots,
    AVG(total_pnl) as avg_pnl,
    AVG(win_rate) as avg_win_rate
FROM (
    SELECT DISTINCT ON (config_id)
        trading_mode, config_id, total_pnl, win_rate
    FROM account_snapshots
    ORDER BY config_id, timestamp DESC
) latest
GROUP BY trading_mode;
```

---

## Troubleshooting

### No Snapshots Being Created
```bash
# Check service is running
pm2 status account-monitor

# Check logs for errors
pm2 logs account-monitor --lines 50

# Verify active bots exist
psql $DATABASE_URL -c "SELECT config_id, config_name, trading_mode, state FROM configurations WHERE state = 'active';"
```

### Aster API Connection Issues
```bash
# Check Aster credentials are set
echo $ASTER_API_KEY
echo $ASTER_API_SECRET

# Test Aster API connection manually
source .venv/bin/activate
python -c "from trading.live.aster_service_v3 import AsterDEXV3LiveTradingService; import asyncio; print(asyncio.run(AsterDEXV3LiveTradingService()._get_account_balance()))"
```

### High Storage Usage
```sql
-- Check snapshot count
SELECT trading_mode, COUNT(*)
FROM account_snapshots
GROUP BY trading_mode;

-- Check storage size
SELECT pg_size_pretty(pg_total_relation_size('account_snapshots'));

-- Implement retention policy if needed (keep 90 days)
DELETE FROM account_snapshots
WHERE timestamp < NOW() - INTERVAL '90 days'
  AND is_heartbeat = true;  -- Only delete heartbeats, keep change events
```

---

## Technical Notes

### Why Account-Wide Data is Correct
- **Aster/Symphony**: 1 wallet = 1 bot (or multiple bots can share 1 wallet)
- If user wants multiple bots, they set up additional wallets
- Adapter queries account-wide data from `/fapi/v3/account` which is correct behavior
- Each config_id maps to a wallet, snapshot stores wallet state

### Why Paper Uses Database Instead of API
- Paper trading is internal, no external API
- All data stored in `paper_accounts` and `paper_trades` tables
- Direct SQL query is faster and more efficient than API abstraction

### Adapter Pattern Extensibility
To add a new trading mode:
1. Create new adapter class implementing `AccountAdapter` interface
2. Implement `get_current_snapshot()` method
3. Implement `supports_balance()` method
4. Add adapter to `adapters` dict in `UniversalAccountMonitor.__init__()`
5. Add trading mode to `CHECK` constraint in database schema

---

**Document Version**: 1.0
**Last Updated**: 2025-11-14 11:30:00 UTC
**Status**: Production operational, all systems nominal
