# V2 Decision Engine Standardization & Position Management Plan

## Current State Analysis (2025-01-09)

### V2 Prompt Types Status
1. **Signal Validation** ✅ Implemented - validates external signals (ggShot, Telegram)
2. **Opportunity Analysis** ✅ Implemented - finds new trading opportunities autonomously  
3. **Position Management** ❌ TODO - manages existing positions

## ✅ STANDARDIZATION COMPLETED (2025-01-09)

### Universal Output Format (All 3 Prompt Types)
```
ACTION: [long/short/hold/wait/close/exit]
CONFIDENCE: [0.000-1.000] 
REASONING: [explanation]
STOP_LOSS: [price or null]
TAKE_PROFIT: [price or null]
```

**Priority Order**: ACTION, CONFIDENCE, REASONING (required) → STOP_LOSS, TAKE_PROFIT (optional)

### ✅ Completed Standardization Tasks
- [x] Fix signal validation actions (`validate/reject` → `long/short/hold/wait`)
- [x] Add standardized format to opportunity analysis prompts
- [x] Update `_parse_llm_response()` for consistent parsing with multi-line reasoning
- [x] Make STOP_LOSS/TAKE_PROFIT optional in parser with null handling
- [x] Add volume analysis integration to both prompt types
- [x] Remove duplicate routing logic in decision engine

### Action Mappings by Prompt Type

| Prompt Type | Available Actions | Use Case |
|-------------|------------------|----------|
| **Signal Validation** | `long/short/hold/wait` | Validate external signals |
| **Opportunity Analysis** | `long/short/hold/wait` | Find new opportunities |
| **Position Management** | `close/exit/hold/wait` | Manage existing positions |

**Action Synonyms**: 
- Entry: `long` = `buy`, `short` = `sell`
- Hold: `hold` = `wait` 
- Exit: `close` = `exit`

## 🔄 DECISION ENGINE ROUTING REDESIGN

### Current Routing Issues
- **Double Routing**: Orchestrator routes by config_type, then decision engine re-routes by same config_type
- **Missing Position Awareness**: No check for active positions to determine opportunity vs management

### New Routing Architecture
```
ORCHESTRATOR LEVEL:
├── Signal Validation (config_type == "signal_validation" + signal_data)
└── Autonomous Trading (else)

DECISION ENGINE SUB-ROUTING:
Autonomous Trading Mode:
├── Check active positions for symbol+config_id
├── If active position exists → Position Management
└── If no active position → Opportunity Analysis
```

### Required Position Query (Supabase)
```sql
SELECT * FROM paper_trades 
WHERE config_id = %s 
  AND symbol = %s 
  AND status = 'open'
ORDER BY opened_at DESC
LIMIT 1
```

## 🔄 POSITION MANAGEMENT WORKFLOW

### Core Challenge: Trade Lifecycle Tracking

**Current Gap**: No position tracking between decisions
**Need**: Decision history context for position management

### Required Data for Position Management Prompts
1. **Current Position**: Entry price, size, direction, P&L
2. **Entry Decision**: Original reasoning, confidence, targets
3. **Market Evolution**: Price movement since entry, new technical signals
4. **Trade Performance**: Unrealized P&L, time held, risk metrics

### Position Management Additional Template Variables
- `{POSITION_DATA}` - Current position details from paper_trades
- `{ENTRY_DECISION}` - Original decision context from decisions table
- `{PERFORMANCE_METRICS}` - P&L, duration, risk metrics
- `{DECISION_HISTORY}` - Previous management decisions

## 📊 PAPER TRADING INTEGRATION PLAN

### Current Architecture Issues
- **Mixed Database Connections**: Paper trading uses direct PostgreSQL, dashboard expects Supabase
- **Missing API Endpoints**: /metrics, /positions, /trades return empty data
- **No Real-time Updates**: Dashboard lacks live position tracking

### Paper Trading Data Queries (Supabase)

#### Active Positions Query
```sql
SELECT 
  pt.trade_id,
  pt.symbol,
  pt.side,
  pt.entry_price,
  pt.current_price,
  pt.size_usd,
  pt.unrealized_pnl,
  pt.opened_at,
  pt.stop_loss,
  pt.take_profit,
  pt.confidence_score,
  d.reasoning as entry_reasoning
FROM paper_trades pt
LEFT JOIN decisions d ON pt.decision_id = d.decision_id
WHERE pt.config_id = %s 
  AND pt.status = 'open'
ORDER BY pt.opened_at DESC
```

#### Account Balance Query
```sql
SELECT 
  account_id,
  current_balance,
  total_pnl,
  open_positions,
  total_trades,
  win_trades,
  loss_trades
FROM paper_accounts 
WHERE config_id = %s
```

#### Trade History Query
```sql
SELECT 
  pt.trade_id,
  pt.symbol,
  pt.side,
  pt.entry_price,
  pt.size_usd,
  pt.realized_pnl,
  pt.opened_at,
  pt.closed_at,
  EXTRACT(EPOCH FROM (pt.closed_at - pt.opened_at))/3600 as duration_hours,
  d.confidence,
  d.reasoning
FROM paper_trades pt
LEFT JOIN decisions d ON pt.decision_id = d.decision_id
WHERE pt.config_id = %s 
  AND pt.status = 'closed'
ORDER BY pt.closed_at DESC
LIMIT %s
```

## 🛠️ IMPLEMENTATION PRIORITIES

### Phase 1: Decision Engine Routing Fix ✅ COMPLETED
- [x] Remove duplicate routing logic in decision engine
- [x] Add position check for autonomous trading sub-routing
- [x] Implement position management prompt type

### Phase 2: Paper Trading Database Migration
- [ ] Migrate PaperTradingService to Supabase client
- [ ] Replace direct psycopg2 connections
- [ ] Update AccountRepository for Supabase REST API
- [ ] Test RLS policies for multi-user isolation

### Phase 3: Dashboard API Implementation
- [ ] Implement /api/v2/bot/{config_id}/metrics endpoint
- [ ] Implement /api/v2/bot/{config_id}/positions endpoint  
- [ ] Implement /api/v2/bot/{config_id}/trades endpoint
- [ ] Add portfolio statistics and P&L aggregation

### Phase 4: Position Management Scheduler Integration
- [ ] Add position check logic to scheduler
- [ ] Implement decision type routing based on position status
- [ ] Configure position management intervals
- [ ] Test full autonomous → management → exit flow

## 💭 KEY ARCHITECTURAL DECISIONS

**Template Variables Available**: `{SYMBOL}`, `{CURRENT_PRICE}`, `{MARKET_DATA}`, `{VOLUME_ANALYSIS}`

**Trade Lifecycle States**:
- `seeking` → `entering` → `managing` → `exiting` → `closed`

**Position Check Strategy**: Query `paper_trades` table with `status = 'open'` to determine routing between opportunity analysis vs position management.

**Database Architecture**: All paper trading data flows through Supabase with proper RLS policies for multi-user isolation.

Each state needs different prompt strategies and scheduler behavior.



1) 