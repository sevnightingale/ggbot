# Database Architecture & Design Context

This document explains the **why** behind our database schema design decisions.

**For the current schema**, see auto-generated section in [README.md](../README.md#-database-schema).

---

## Core Design Principles

### Multi-User Isolation
**Why**: Platform supports multiple users with independent trading strategies and complete data isolation.

**How**:
- Every table has `user_id` column (foreign key to Supabase auth.users)
- Config-ID architecture: `configurations` table with `config_id` UUID
- All queries filter by `user_id` to prevent data leakage
- Row-Level Security (RLS) enabled on Supabase for additional protection

**Tables**: `configurations`, `paper_accounts`, `paper_trades`, `decisions`, `live_trades`, `user_profiles`

---

### Config-ID Architecture (Multi-Bot Per User)
**Why**: Users need to run multiple independent bots with different strategies, symbols, and risk settings.

**How**:
- `configurations` table stores bot configuration as JSONB
- Each config has unique `config_id` UUID
- `paper_accounts` table has 1:1 relationship with `config_id` (isolated $10k accounts)
- Trades, decisions, and positions all link to `config_id` for attribution

**Benefit**:
- Users can run BTC scalping bot + ETH swing bot simultaneously
- Each bot has independent P&L tracking and performance analytics
- Easy to duplicate configs for testing strategy variations

---

### Paper vs Live Trading Separation
**Why**: Clear boundary between simulation and real money trading with different execution responsibilities.

**How**:
- **Paper trading**: `paper_trades` table in our database, full control of simulation
- **Live trading**: `live_trades` table with minimal tracking, Symphony.io handles execution
- `trading_mode` column in configurations ('paper' | 'live')

**Rationale**:
- Paper trading needs rich simulation (TP/SL execution, unrealized P&L, position monitoring)
- Live trading delegates to Symphony.io API - we only track batch_id for linkage
- Different fee models, execution speeds, and risk management needs

**Tables**: `paper_trades` (22 columns), `live_trades` (5 columns)

---

### JSONB Configuration Pattern
**Why**: Flexible bot configuration without schema migrations for every new setting or feature.

**How**: `configurations.config_data` JSONB column stores:
- `selected_pair` - trading symbol (BTCUSDT, ETHUSDT, etc.)
- `timeframe` - 5m, 15m, 30m, 1h, 4h, 1d
- `stop_loss_pct`, `take_profit_pct` - risk management
- `max_position_size_pct` - position sizing limit
- `user_strategy` - natural language strategy definition
- `selected_data_sources` - array of market intelligence data point IDs
- `agent_strategy` - autonomous agent strategy (if config_type='agent')
- `autonomously_editable` - whether agent can modify its own strategy

**Benefits**:
- Add new config fields without migrations (just update frontend + backend validation)
- Easy to version configs (store old config_data on updates)
- Allows per-bot customization without new tables
- Forward-compatible with new features (old bots ignore new fields)

---

### Decisions as Audit Trail
**Why**: Full transparency into AI decision-making process for trust, debugging, and improvement.

**How**: `decisions` table captures every AI decision with:
- `action` - wait, long, short, close
- `confidence` - 0.0 to 1.0 score from LLM
- `reasoning` - full AI explanation in natural language
- `prompt` - exact prompt sent to LLM (for debugging)
- `decision_data` - JSONB with market context (prices, indicators, signals)
- `created_by` - 'decision_engine_v2' | 'agent' (tracks decision source)
- `parent_decision_id` - links monitoring decisions to original entry decision

**Use Cases**:
- Users review why AI made each decision (transparency)
- Debug incorrect decisions by examining prompt + reasoning
- Improve prompts based on historical reasoning patterns
- Future analytics: confidence calibration, indicator correlation, pattern analysis

**Future**: Trade Timeline feature will link entry decision → monitoring decisions → exit decision for full lifecycle view.

---

### Market Intelligence Catalog Pattern
**Why**: Support 150+ data sources without code bloat, schema changes, or hardcoded adapters.

**How**:
- `data_sources` table - catalog of providers (ggShot, Grok, Binance, CoinGecko, etc.)
- `data_points` table - specific metrics per source (VIX, funding rate, whale activity, Twitter sentiment)
- `config_values` ARRAY - parameters for each data point (e.g., ["BTCUSDT", "ETHUSDT"])
- `requires_premium` flag - paywall gating for business model

**Benefits**:
- Add new data sources via INSERT, not code changes
- Frontend queries catalog to build UI dynamically (no hardcoded lists)
- Easy to gate premium data behind subscription tiers
- Intelligence Orchestrator routes based on catalog metadata
- Scales to 150+ data sources without performance degradation

**Tables**: `data_sources`, `data_points`

---

### Agent Trade Observations (Post-Trade Learning)
**Why**: Autonomous agents need to learn from outcomes and build "memory" of successful/failed patterns.

**How**: `trade_observations` table stores post-trade reflections:
- `observation_type` - 'win_analysis' | 'loss_analysis' | 'pattern_recognition'
- `what_went_well` / `what_went_wrong` - structured reflection
- `predictive_data_points` - JSONB of indicators that predicted outcome
- `decision_review` - agent's analysis of decision quality
- `importance` - 1-10 score for retrieval prioritization
- `trade_pnl` - outcome for correlation analysis
- `trade_duration_minutes` - time in market

**Agent Workflow**:
1. Agent executes trade
2. Trade closes (TP/SL/manual)
3. Agent analyzes outcome, logs observation
4. Before next trade, agent queries past observations for similar market conditions
5. Agent incorporates learnings into decision-making

**Benefit**: Compound learning over time (unlike stateless LLM calls that forget everything).

---

## Removed Legacy Tables (August 2025)

### Why we removed: `trades`, `trade_orders`, `sessions`, `instrument_metadata`

**Problem**: Original design mixed paper trading with live trading in same tables, causing:
- Confusion over which trades were real vs simulated
- Complex queries filtering by "is_paper" flags
- Hummingbot integration conflicts (duplicate position tracking)

**Solution**:
- Paper trading → `paper_trades` (our database, full simulation)
- Live trading → Symphony.io database (they handle execution, we track batch_id)
- Removed `sessions` table (TradingView session management moved to in-memory)
- Removed `instrument_metadata` (Symphony.io provides via API)

**Benefit**:
- Clean separation, no confusion
- Simpler queries (no filtering needed)
- Single source of truth for each trading mode

---

## Table-Specific Design Decisions

### `user_profiles` - Subscription & Business Model
**Why**: Extends Supabase auth.users with business model integration.

**Key Fields**:
- `subscription_tier` - FREE (paper only, bring your own LLM keys) vs GGBASE (hosted LLM, Telegram signals)
- `stripe_customer_id` / `stripe_subscription_id` - payment integration
- `paid_data_points` - array of premium data point IDs user has purchased
- `symphony_vault_id` / `symphony_smart_account` - live trading wallet linkage

**Business Logic**: See `core/domain/user_profile.py` for @property methods:
- `can_use_premium_features` - gates premium data sources
- `can_publish_telegram_signals` - signal validation publishing permission
- `can_use_live_trading` - Symphony live trading access

---

### `paper_accounts` - Isolated Per-Bot Accounts
**Why**: Each bot needs independent $10k starting balance for fair performance comparison.

**Key Fields**:
- `config_id` - 1:1 relationship with bot configuration
- `initial_balance` / `current_balance` - always starts at $10,000
- `total_pnl` - cumulative profit/loss
- `total_trades` / `win_trades` / `loss_trades` - performance metrics
- `last_reset_at` - allows users to reset account to $10k

**Design**: No shared pool - each bot is isolated sandbox for strategy testing.

---

### `paper_trades` - Rich Simulation Tracking
**Why**: Paper trading needs comprehensive position tracking for realistic simulation.

**22 columns include**:
- Entry tracking: `entry_price`, `size_usd`, `leverage`, `opened_at`
- Exit tracking: `current_price`, `closed_at`, `close_reason` (TP/SL/manual)
- Risk management: `stop_loss`, `take_profit`, `liquidation_price`
- P&L: `unrealized_pnl`, `realized_pnl`, `margin_used`
- Attribution: `decision_id`, `confidence_score`

**Why so detailed**: Enables Trade Timeline feature (entry → management → exit full lifecycle).

---

### `decisions` - AI Decision Audit Log
**Why**: Capture every AI reasoning step for transparency and debugging.

**Key Fields**:
- `prompt` - exact text sent to LLM (OpenAI, Anthropic, DeepSeek, etc.)
- `reasoning` - AI's natural language explanation
- `decision_data` - JSONB with market context (indicator values, signal data, etc.)
- `created_by` - tracks whether decision came from decision_engine_v2 or autonomous agent
- `parent_decision_id` - links monitoring decisions to entry decisions

**Future**: Confidence calibration analysis (did 0.8 confidence really mean 80% win rate?).

---

### `configurations` - Bot Configuration Store
**Why**: Central registry of all user bots with flexible JSONB config.

**Key Fields**:
- `config_type` - 'autonomous' (normal bot) | 'signal_validation' (ggShot validator) | 'agent' (autonomous agent)
- `state` - 'active' | 'inactive' (for scheduler)
- `trading_mode` - 'paper' | 'live'
- `config_data` - JSONB with all bot settings
- `symphony_agent_id` - for live trading linkage

**Design**: One table for all bot types, differentiated by `config_type`. Simpler than separate tables per type.

---

## Performance Optimizations

### Indexes
**Current indexes** (queried automatically by status_check.py):
- **Composite indexes** on (user_id, config_id) for fast per-bot queries
- **Timestamp indexes** on created_at, opened_at for time-based filtering
- **Status indexes** on paper_trades.status for active/closed position filtering
- **Foreign key indexes** for join performance

### Query Patterns
**Most common queries**:
1. Get all active bots for user: `SELECT * FROM configurations WHERE user_id = ? AND state = 'active'`
2. Get open positions for bot: `SELECT * FROM paper_trades WHERE config_id = ? AND status = 'open'`
3. Get recent decisions: `SELECT * FROM decisions WHERE config_id = ? ORDER BY created_at DESC LIMIT 10`

**Why these patterns**: Dashboard real-time updates via SSE streams require fast per-user, per-bot queries.

### Future Partitioning
**When to partition**:
- `decisions` table will grow large (1M+ rows) - partition by created_at (monthly)
- `paper_trades` table - partition by closed_at for archival (keep last 6 months hot)

**Not yet needed**: Current volumes (~10k trades, ~100k decisions) perform well with indexes.

---

## Migration Strategy

### Philosophy
**Forward-only migrations** - never destructive, always preserve data.

### Process
1. Write migration SQL in `database/migrations/`
2. Test locally on Supabase dev project
3. Run in production via Supabase Dashboard SQL editor
4. Verify with `status_check.py --update` (auto-updates README.md)
5. Commit migration file to git for historical reference

### Example Migrations
- `agent_phase1.sql` - Added `created_by` column to decisions, created `agent_memory` table (later replaced)
- `agent_trade_observations.sql` - Replaced `agent_memory` with `trade_observations` (post-trade learning model)

---

## Security & Access Control

### Row-Level Security (RLS)
**Supabase RLS policies** on all user tables:
- Users can only SELECT/INSERT/UPDATE rows where `user_id = auth.uid()`
- Service accounts (agent-runner, ggbot orchestrator) use service role key to bypass RLS
- No risk of user A seeing user B's data

### Service Authentication
**Backend services** access database via:
- `SERVICE_KEY` environment variable (Supabase service role key)
- `get_db_connection()` helper in `core/common/db.py`
- No user-facing API endpoints expose service key

---

## Data Flow Examples

### Autonomous Bot Execution Flow
1. APScheduler triggers bot execution (ggbot.py)
2. **Extraction V2**: Query market data, store in `market_data` table
3. **Decision Engine**: LLM analyzes data, creates entry in `decisions` table
4. **Trading Engine**: If action=long/short, create entry in `paper_trades`, deduct from `paper_accounts.current_balance`
5. **Position Monitoring**: Every 3 seconds, check TP/SL, update `unrealized_pnl`
6. **Close Trade**: When TP/SL hit, update `paper_trades.status='closed'`, `realized_pnl`, update `paper_accounts.total_pnl`

### Agent Trade Observation Flow
1. Agent executes trade (creates `paper_trades` entry)
2. Trade closes (TP/SL/manual)
3. Agent calls `record_trade_observation` tool
4. Entry created in `trade_observations` table with reflection
5. Before next trade, agent calls `query_trade_observations` tool
6. Past learnings inform current decision

---

## Future Enhancements

### Planned Schema Changes
- **Trade Timeline**: Add `exit_decision_id` to `paper_trades` and `live_trades` for full lifecycle tracking
- **Multi-Model Support**: Add `model_used` column to decisions (GPT-4, Claude Opus, DeepSeek R1)
- **Cost Tracking**: Add `llm_cost_usd` column to decisions for budget management

### Analytics Tables (Future)
- `strategy_performance` - aggregated metrics per user strategy template
- `indicator_correlation` - which indicators predict wins/losses
- `confidence_calibration` - does 0.8 confidence = 80% win rate?

---

**For current schema reference**, see auto-generated section in [README.md](../README.md#-database-schema).

**For domain model business logic**, see auto-generated section in [README.md](../README.md#-domain-models--business-logic).
