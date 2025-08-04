│ │ Comprehensive Config-ID Integration & Database Architecture Plan                      │ │
│ │                                                                                       │ │
│ │ 🔍 Current State Analysis                                                             │ │
│ │                                                                                       │ │
│ │ ggBot Database (PostgreSQL on port 5432)                                              │ │
│ │                                                                                       │ │
│ │ What it tracks:                                                                       │ │
│ │ - configurations: User configs with config_id, JSON blobs for                         │ │
│ │ extraction/decision/trading settings                                                  │ │
│ │ - trades: Comprehensive trade lifecycle with config_id, TP/SL, confidence scores      │ │
│ │ - strategy_runs: Decision audit trail with reasoning, parent/child relationships      │ │
│ │ - trade_orders: Individual orders that compose trades                                 │ │
│ │ - market_data: Extracted indicators and prices                                        │ │
│ │ - account_states: Exchange account monitoring                                         │ │
│ │                                                                                       │ │
│ │ Hummingbot Database (PostgreSQL on port 5434)                                         │ │
│ │                                                                                       │ │
│ │ What it tracks:                                                                       │ │
│ │ - bot_runs: Bot deployment history with instance_name, strategy configs               │ │
│ │ - orders: All order details with exchange order IDs                                   │ │
│ │ - trades: Individual fills with exact prices and fees                                 │ │
│ │ - position_snapshots: Real-time position state from exchange                          │ │
│ │ - funding_payments: Perpetual funding costs                                           │ │
│ │ - account_states/token_states: Account balances per connector                         │ │
│ │                                                                                       │ │
│ │ Key Observations                                                                      │ │
│ │                                                                                       │ │
│ │ 1. No config_id in Hummingbot - Uses instance_name and bot_name instead               │ │
│ │ 2. Different trade concepts - ggBot tracks positions, Hummingbot tracks fills         │ │
│ │ 3. Hummingbot has deployment tracking - bot_runs table perfect for instance           │ │
│ │ management                                                                            │ │
│ │ 4. Both track account states - But for different purposes                             │ │
│ │                                                                                       │ │
│ │ 🎯 Proposed Architecture: Clear Separation of Concerns                                │ │
│ │                                                                                       │ │
│ │ Design Principle: One-Way Data Flow                                                   │ │
│ │                                                                                       │ │
│ │ Hummingbot DB → Read-Only Access → ggBot DB → Analytics/Dashboard                     │ │
│ │                                                                                       │ │
│ │ What Lives Where:                                                                     │ │
│ │                                                                                       │ │
│ │ ggBot Database (Decision & Analytics)                                                 │ │
│ │                                                                                       │ │
│ │ - Master config management (configurations table)                                     │ │
│ │ - Decision audit trail (strategy_runs)                                                │ │
│ │ - User management (users, sessions)                                                   │ │
│ │ - High-level trade tracking (trades table for positions)                              │ │
│ │ - Analytics & reporting (aggregated from Hummingbot data)                             │ │
│ │                                                                                       │ │
│ │ Hummingbot Database (Execution & Real-Time)                                           │ │
│ │                                                                                       │ │
│ │ - Order execution details (orders, trades)                                            │ │
│ │ - Real-time position state (position_snapshots)                                       │ │
│ │ - Exchange-specific data (funding_payments)                                           │ │
│ │ - Bot deployment records (bot_runs)                                                   │ │
│ │ - Paper trading balances (account_states/token_states)                                │ │
│ │                                                                                       │ │
│ │ 📋 Implementation Plan                                                                │ │
│ │                                                                                       │ │
│ │ Phase 1: Config System Foundation                                                     │ │
│ │                                                                                       │ │
│ │ 1.1 Enhanced Configuration Management                                                 │ │
│ │                                                                                       │ │
│ │ # core/config/config_manager.py                                                       │ │
│ │ class ConfigManager:                                                                  │ │
│ │     """Central config management with config_id as primary key."""                    │ │
│ │                                                                                       │ │
│ │     async def create_config(self, user_id: str, config_type: str, config_data: dict)  │ │
│ │ -> str:                                                                               │ │
│ │         """Create new config and return config_id."""                                 │ │
│ │         config_id = str(uuid.uuid4())                                                 │ │
│ │         # Store in ggbot.configurations table                                         │ │
│ │         return config_id                                                              │ │
│ │                                                                                       │ │
│ │     async def get_config(self, config_id: str) -> dict:                               │ │
│ │         """Retrieve config by config_id."""                                           │ │
│ │         # Query ggbot.configurations table                                            │ │
│ │         pass                                                                          │ │
│ │                                                                                       │ │
│ │ 1.2 Config-to-Instance Mapping                                                        │ │
│ │                                                                                       │ │
│ │ # trading/services/instance_manager.py                                                │ │
│ │ class HummingbotInstanceManager:                                                      │ │
│ │     """Maps config_id to Hummingbot bot instances."""                                 │ │
│ │                                                                                       │ │
│ │     def get_instance_name(self, user_id: str, config_id: str) -> str:                 │ │
│ │         """Generate consistent instance name from config_id."""                       │ │
│ │         # Format: ggbot-{user_id[:8]}-{config_id[:8]}                                 │ │
│ │         return f"ggbot-{user_id[:8]}-{config_id[:8]}"                                 │ │
│ │                                                                                       │ │
│ │     async def ensure_bot_instance(self, user_id: str, config_id: str) -> dict:        │ │
│ │         """Create or retrieve existing bot instance."""                               │ │
│ │         instance_name = self.get_instance_name(user_id, config_id)                    │ │
│ │                                                                                       │ │
│ │         # Check Hummingbot bot_runs table for existing instance                       │ │
│ │         existing = await self._check_existing_instance(instance_name)                 │ │
│ │         if existing:                                                                  │ │
│ │             return existing                                                           │ │
│ │                                                                                       │ │
│ │         # Create new instance with paper trading account                              │ │
│ │         return await self._create_paper_instance(instance_name, config_id)            │ │
│ │                                                                                       │ │
│ │ Phase 2: Database Integration Strategy                                                │ │
│ │                                                                                       │ │
│ │ 2.1 Read-Only Sync Service                                                            │ │
│ │                                                                                       │ │
│ │ # core/sync/hummingbot_sync.py                                                        │ │
│ │ class HummingbotDataSync:                                                             │ │
│ │     """One-way sync from Hummingbot DB to ggBot DB."""                                │ │
│ │                                                                                       │ │
│ │     def __init__(self):                                                               │ │
│ │         self.hb_conn = create_engine("postgresql://...@localhost:5434/hummingbot")    │ │
│ │         self.gg_conn = create_engine("postgresql://...@localhost:5432/ggbot")         │ │
│ │                                                                                       │ │
│ │     async def sync_bot_trades(self, instance_name: str, config_id: str):              │ │
│ │         """Sync trades from Hummingbot to ggBot for analytics."""                     │ │
│ │         # 1. Query Hummingbot orders/trades for instance                              │ │
│ │         hb_trades = await self._get_hummingbot_trades(instance_name)                  │ │
│ │                                                                                       │ │
│ │         # 2. Transform to ggBot trade format                                          │ │
│ │         for hb_trade in hb_trades:                                                    │ │
│ │             gg_trade = {                                                              │ │
│ │                 'config_id': config_id,                                               │ │
│ │                 'exchange': hb_trade.connector_name,                                  │ │
│ │                 'symbol': hb_trade.trading_pair,                                      │ │
│ │                 'entry_price': hb_trade.price,                                        │ │
│ │                 # ... map other fields                                                │ │
│ │             }                                                                         │ │
│ │                                                                                       │ │
│ │         # 3. Update ggBot trades table (upsert)                                       │ │
│ │         await self._upsert_ggbot_trades(gg_trades)                                    │ │
│ │                                                                                       │ │
│ │     async def sync_account_balances(self, instance_name: str):                        │ │
│ │         """Sync paper trading balances from Hummingbot."""                            │ │
│ │         # Query Hummingbot account_states/token_states                                │ │
│ │         # Update ggBot account monitoring table                                       │ │
│ │         pass                                                                          │ │
│ │                                                                                       │ │
│ │ 2.2 Position Reconciliation                                                           │ │
│ │                                                                                       │ │
│ │ class PositionReconciler:                                                             │ │
│ │     """Reconcile Hummingbot positions with ggBot trades."""                           │ │
│ │                                                                                       │ │
│ │     async def reconcile_position(self, config_id: str, instance_name: str):           │ │
│ │         # 1. Get current position from Hummingbot position_snapshots                  │ │
│ │         hb_position = await self._get_hummingbot_position(instance_name)              │ │
│ │                                                                                       │ │
│ │         # 2. Get ggBot trade record                                                   │ │
│ │         gg_trade = await self._get_ggbot_trade(config_id)                             │ │
│ │                                                                                       │ │
│ │         # 3. Update ggBot with real-time data                                         │ │
│ │         gg_trade.mark_price = hb_position.mark_price                                  │ │
│ │         gg_trade.unrealized_pnl = hb_position.unrealized_pnl                          │ │
│ │                                                                                       │ │
│ │         # 4. Create strategy_run audit entry                                          │ │
│ │         await self._create_audit_entry(config_id, "POSITION_UPDATE", hb_position)     │ │
│ │                                                                                       │ │
│ │ Phase 3: Paper Trading Account Management                                             │ │
│ │                                                                                       │ │
│ │ 3.1 Paper Account Initialization                                                      │ │
│ │                                                                                       │ │
│ │ class PaperTradingManager:                                                            │ │
│ │     """Manage paper trading accounts per config_id."""                                │ │
│ │                                                                                       │ │
│ │     INITIAL_BALANCE = 10000  # $10,000 USDT per config                                │ │
│ │                                                                                       │ │
│ │     async def initialize_paper_account(self, instance_name: str, config_id: str):     │ │
│ │         """Initialize paper trading account for config."""                            │ │
│ │         # Create account_state in Hummingbot DB                                       │ │
│ │         account_state = {                                                             │ │
│ │             'account_name': f'paper_{instance_name}',                                 │ │
│ │             'connector_name': 'binance_paper_trade',                                  │ │
│ │             'timestamp': datetime.utcnow()                                            │ │
│ │         }                                                                             │ │
│ │                                                                                       │ │
│ │         # Create token_state with initial balance                                     │ │
│ │         token_state = {                                                               │ │
│ │             'token': 'USDT',                                                          │ │
│ │             'units': self.INITIAL_BALANCE,                                            │ │
│ │             'available_units': self.INITIAL_BALANCE                                   │ │
│ │         }                                                                             │ │
│ │                                                                                       │ │
│ │         await self._create_hummingbot_account(account_state, token_state)             │ │
│ │                                                                                       │ │
│ │     async def reset_paper_account(self, config_id: str):                              │ │
│ │         """Reset paper account to initial balance."""                                 │ │
│ │         instance_name = self._get_instance_name(config_id)                            │ │
│ │         # Reset token_states in Hummingbot DB                                         │ │
│ │         await self._reset_balance(instance_name, self.INITIAL_BALANCE)                │ │
│ │                                                                                       │ │
│ │ Phase 4: Strategy Testing Infrastructure                                              │ │
│ │                                                                                       │ │
│ │ 4.1 Config-Based Strategy Deployment                                                  │ │
│ │                                                                                       │ │
│ │ class StrategyDeployer:                                                               │ │
│ │     """Deploy strategies with config_id mapping."""                                   │ │
│ │                                                                                       │ │
│ │     async def deploy_strategy(self, config_id: str, signal: dict):                    │ │
│ │         # 1. Get config and instance                                                  │ │
│ │         config = await self.config_manager.get_config(config_id)                      │ │
│ │         instance_name = self.instance_manager.get_instance_name(                      │ │
│ │             config['user_id'], config_id                                              │ │
│ │         )                                                                             │ │
│ │                                                                                       │ │
│ │         # 2. Ensure bot instance exists                                               │ │
│ │         await self.instance_manager.ensure_bot_instance(                              │ │
│ │             config['user_id'], config_id                                              │ │
│ │         )                                                                             │ │
│ │                                                                                       │ │
│ │         # 3. Create Position Executor with consistent naming                          │ │
│ │         controller_config = {                                                         │ │
│ │             'controller_name': 'position_executor',                                   │ │
│ │             'instance_name': instance_name,                                           │ │
│ │             'connector_name': 'binance_paper_trade',                                  │ │
│ │             # ... signal parameters                                                   │ │
│ │         }                                                                             │ │
│ │                                                                                       │ │
│ │         # 4. Deploy via Hummingbot API                                                │ │
│ │         result = await self.hummingbot_api.deploy_controller(controller_config)       │ │
│ │                                                                                       │ │
│ │         # 5. Create bot_run record in Hummingbot DB                                   │ │
│ │         await self._create_bot_run(instance_name, config_id, controller_config)       │ │
│ │                                                                                       │ │
│ │         # 6. Create strategy_run in ggBot DB for audit                                │ │
│ │         await self._create_strategy_run(config_id, signal, result)                    │ │
│ │                                                                                       │ │
│ │ 4.2 Performance Tracking                                                              │ │
│ │                                                                                       │ │
│ │ class PerformanceTracker:                                                             │ │
│ │     """Track performance per config_id."""                                            │ │
│ │                                                                                       │ │
│ │     async def get_config_performance(self, config_id: str):                           │ │
│ │         """Get aggregated performance for a config."""                                │ │
│ │         instance_name = self._get_instance_name(config_id)                            │ │
│ │                                                                                       │ │
│ │         # Query Hummingbot for:                                                       │ │
│ │         # - Current positions (position_snapshots)                                    │ │
│ │         # - Trade history (orders/trades)                                             │ │
│ │         # - Account balance (account_states)                                          │ │
│ │                                                                                       │ │
│ │         # Calculate metrics:                                                          │ │
│ │         # - Total P&L                                                                 │ │
│ │         # - Win rate                                                                  │ │
│ │         # - Average trade duration                                                    │ │
│ │         # - Current exposure                                                          │ │
│ │                                                                                       │ │
│ │         return {                                                                      │ │
│ │             'config_id': config_id,                                                   │ │
│ │             'total_pnl': total_pnl,                                                   │ │
│ │             'open_positions': open_positions,                                         │ │
│ │             'account_balance': current_balance,                                       │ │
│ │             'performance_metrics': metrics                                            │ │
│ │         }                                                                             │ │
│ │                                                                                       │ │
│ │ 🔧 Key Implementation Details                                                         │ │
│ │                                                                                       │ │
│ │ 1. Instance Naming Convention                                                         │ │
│ │                                                                                       │ │
│ │ Format: ggbot-{user_id[:8]}-{config_id[:8]}                                           │ │
│ │ Example: ggbot-a1b2c3d4-e5f6g7h8                                                      │ │
│ │                                                                                       │ │
│ │ Benefits:                                                                             │ │
│ │ - Consistent across restarts                                                          │ │
│ │ - Easy to identify in logs                                                            │ │
│ │ - Maps directly to config_id                                                          │ │
│ │                                                                                       │ │
│ │ 2. Database Connection Strategy                                                       │ │
│ │                                                                                       │ │
│ │ # Use read-only connection to Hummingbot DB                                           │ │
│ │ hb_engine = create_engine(                                                            │ │
│ │     "postgresql://readonly_user:pass@localhost:5434/hummingbot",                      │ │
│ │     pool_pre_ping=True,                                                               │ │
│ │     echo=False                                                                        │ │
│ │ )                                                                                     │ │
│ │                                                                                       │ │
│ │ # Full access to ggBot DB                                                             │ │
│ │ gg_engine = create_engine(                                                            │ │
│ │     "postgresql://ggbot:pass@localhost:5432/ggbot",                                   │ │
│ │     pool_pre_ping=True,                                                               │ │
│ │     echo=True                                                                         │ │
│ │ )                                                                                     │ │
│ │                                                                                       │ │
│ │ 3. Sync Frequency                                                                     │ │
│ │                                                                                       │ │
│ │ - Real-time: Position updates every 30 seconds (monitoring service)                   │ │
│ │ - Near real-time: Trade fills within 5 seconds (webhook from Hummingbot)              │ │
│ │ - Batch: Performance metrics every 5 minutes                                          │ │
│ │ - On-demand: Account balance on request                                               │ │
│ │                                                                                       │ │
│ │ 4. Error Handling                                                                     │ │
│ │                                                                                       │ │
│ │ - If Hummingbot DB unavailable: Use cached data from ggBot DB                         │ │
│ │ - If sync fails: Log error, retry with exponential backoff                            │ │
│ │ - If instance missing: Auto-recreate from config                                      │ │
│ │                                                                                       │ │
│ │ 📊 Benefits of This Architecture                                                      │ │
│ │                                                                                       │ │
│ │ 1. Clean Separation: Each database has clear responsibilities                         │ │
│ │ 2. Single Source of Truth: Config in ggBot, execution in Hummingbot                   │ │
│ │ 3. Scalability: Can add more Hummingbot instances without schema changes              │ │
│ │ 4. Auditability: Full decision trail in strategy_runs                                 │ │
│ │ 5. Resilience: Can reconstruct state from either database                             │ │
│ │ 6. Testing Isolation: Each config gets isolated paper trading environment             │ │
│ │                                                                                       │ │
│ │ 🚀 Implementation Priority                                                            │ │
│ │                                                                                       │ │
│ │ Week 1: Foundation                                                                    │ │
│ │ 1. Implement ConfigManager with config_id management                                  │ │
│ │ 2. Create HummingbotInstanceManager for consistent naming                             │ │
│ │ 3. Set up read-only access to Hummingbot DB                                           │ │
│ │                                                                                       │ │
│ │ Week 2: Integration                                                                   │ │
│ │ 1. Build HummingbotDataSync service                                                   │ │
│ │ 2. Implement PaperTradingManager                                                      │ │
│ │ 3. Create position reconciliation logic                                               │ │
│ │                                                                                       │ │
│ │ Week 3: Testing                                                                       │ │
│ │ 1. Deploy test configs with different strategies                                      │ │
│ │ 2. Verify isolation between configs                                                   │ │
│ │ 3. Test performance tracking                                                          │ │
│ │ 4. Validate audit trail completeness                                                  │ │
│ │                                                                                       │ │
│ │ Success Metrics:                                                                      │ │
│ │ - ✅ Each config_id maps to one Hummingbot instance                                    │ │
│ │ - ✅ Paper accounts maintain separate $10k balances                                    │ │
│ │ - ✅ Full audit trail from decision to execution                                       │ │
│ │ - ✅ Dashboard shows real-time positions per config                                    │ │
│ │ - ✅ Can reset paper accounts without affecting others    
























│ │ Database Architecture Analysis & Recommendations                                      │ │
│ │                                                                                       │ │
│ │ 🔍 Current State Assessment                                                           │ │
│ │                                                                                       │ │
│ │ ggBot Database (ACTUAL Current State)                                                 │ │
│ │                                                                                       │ │
│ │ What's Actually Implemented:                                                          │ │
│ │ - ✅ configurations: 9 configs, mostly ggshot_test types with config_id                │ │
│ │ - ✅ strategy_runs: 21 records - decision audit trail (THIS IS VALUABLE)               │ │
│ │ - ✅ trades: 21 legacy trades from trading-legacy module                               │ │
│ │ - ✅ users, sessions: User management working                                          │ │
│ │ - ✅ market_data: Extraction data storage                                              │ │
│ │ - ✅ ggshot_filter: ggShot signal filtering logs                                       │ │
│ │                                                                                       │ │
│ │ Legacy Trading Tables (Can Be Replaced):                                              │ │
│ │ - trades - 21 records from old CCXT system                                            │ │
│ │ - trade_orders - Individual order tracking                                            │ │
│ │ - account_states, position_snapshots, etc. - Duplicating what Hummingbot does better  │ │
│ │                                                                                       │ │
│ │ Hummingbot Database Capabilities                                                      │ │
│ │                                                                                       │ │
│ │ What Hummingbot Already Provides:                                                     │ │
│ │ - ✅ Comprehensive order tracking - orders, trades, fills                              │ │
│ │ - ✅ Real-time position state - position_snapshots with mark prices, PnL               │ │
│ │ - ✅ Account management - account_states, token_states for paper trading               │ │
│ │ - ✅ Bot deployment tracking - bot_runs with instance names                            │ │
│ │ - ✅ Fee tracking - funding_payments, trade fees                                       │ │
│ │                                                                                       │ │
│ │ 💡 Key Insights & Recommendations                                                     │ │
│ │                                                                                       │ │
│ │ 1. Direct Query Strategy - YES, This Makes Sense!                                     │ │
│ │                                                                                       │ │
│ │ Why duplicate data when we can query Hummingbot directly?                             │ │
│ │                                                                                       │ │
│ │ Advantages:                                                                           │ │
│ │ - ✅ Single source of truth for trade execution data                                   │ │
│ │ - ✅ Real-time accuracy - no sync lag or consistency issues                            │ │
│ │ - ✅ Reduced complexity - no sync services to maintain                                 │ │
│ │ - ✅ Leverage Hummingbot's expertise - they handle order lifecycle better than we      │ │
│ │ could                                                                                 │ │
│ │                                                                                       │ │
│ │ Implementation:                                                                       │ │
│ │ // Frontend queries both databases                                                    │ │
│ │ const tradeData = await Promise.all([                                                 │ │
│ │   queryGGBot('SELECT * FROM strategy_runs WHERE config_id = ?'), // Decision context  │ │
│ │   queryHummingbot('SELECT * FROM position_snapshots WHERE account_name = ?') //       │ │
│ │ Execution state                                                                       │ │
│ │ ]);                                                                                   │ │
│ │                                                                                       │ │
│ │ 2. Clean Database Separation                                                          │ │
│ │                                                                                       │ │
│ │ ggBot Database - "Decision & Context Layer"                                           │ │
│ │                                                                                       │ │
│ │ Keep These Tables:                                                                    │ │
│ │ - ✅ users, sessions - User management                                                 │ │
│ │ - ✅ configurations - Our core config system with config_id                            │ │
│ │ - ✅ strategy_runs - Decision audit trail (CRITICAL for compliance)                    │ │
│ │ - ✅ market_data - Extracted indicators                                                │ │
│ │ - ✅ ggshot_filter - Signal filtering logs                                             │ │
│ │                                                                                       │ │
│ │ Add New Table:                                                                        │ │
│ │ -- Map config_id to Hummingbot instance                                               │ │
│ │ CREATE TABLE config_instances (                                                       │ │
│ │     config_id UUID REFERENCES configurations(config_id),                              │ │
│ │     instance_name VARCHAR NOT NULL, -- e.g., "ggbot-user123-conf456"                  │ │
│ │     hummingbot_account VARCHAR NOT NULL, -- e.g., "paper_ggbot_user123_conf456"       │ │
│ │     created_at TIMESTAMP DEFAULT NOW(),                                               │ │
│ │     status VARCHAR DEFAULT 'active', -- active, disabled, archived                    │ │
│ │     UNIQUE(config_id),                                                                │ │
│ │     UNIQUE(instance_name)                                                             │ │
│ │ );                                                                                    │ │
│ │                                                                                       │ │
│ │ Remove These Tables (Clean Transition):                                               │ │
│ │ - ❌ trades - Replace with Hummingbot position_snapshots queries                       │ │
│ │ - ❌ trade_orders - Use Hummingbot orders table                                        │ │
│ │ - ❌ account_states, position_snapshots - Hummingbot has better versions               │ │
│ │                                                                                       │ │
│ │ Hummingbot Database - "Execution & Real-Time Layer"                                   │ │
│ │                                                                                       │ │
│ │ Query These Tables:                                                                   │ │
│ │ - ✅ bot_runs - Instance deployment tracking                                           │ │
│ │ - ✅ orders, trades - Order execution details                                          │ │
│ │ - ✅ position_snapshots - Real-time position state                                     │ │
│ │ - ✅ account_states, token_states - Paper trading balances                             │ │
│ │                                                                                       │ │
│ │ 3. Implementation Strategy                                                            │ │
│ │                                                                                       │ │
│ │ Frontend Data Access Pattern                                                          │ │
│ │                                                                                       │ │
│ │ class TradingDataService {                                                            │ │
│ │     async getConfigPerformance(configId: string) {                                    │ │
│ │         // 1. Get context from ggBot                                                  │ │
│ │         const context = await this.ggbot.query(`                                      │ │
│ │             SELECT sr.*, c.config_name, ci.instance_name, ci.hummingbot_account       │ │
│ │             FROM strategy_runs sr                                                     │ │
│ │             JOIN configurations c ON sr.config_id = c.config_id                       │ │
│ │             JOIN config_instances ci ON sr.config_id = ci.config_id                   │ │
│ │             WHERE sr.config_id = $1                                                   │ │
│ │         `, [configId]);                                                               │ │
│ │                                                                                       │ │
│ │         // 2. Get execution data from Hummingbot                                      │ │
│ │         const performance = await this.hummingbot.query(`                             │ │
│ │             SELECT ps.*, acc.token_states                                             │ │
│ │             FROM position_snapshots ps                                                │ │
│ │             JOIN account_states acc ON ps.account_name = acc.account_name             │ │
│ │             WHERE ps.account_name = $1                                                │ │
│ │         `, [context.hummingbot_account]);                                             │ │
│ │                                                                                       │ │
│ │         return { context, performance };                                              │ │
│ │     }                                                                                 │ │
│ │ }                                                                                     │ │
│ │                                                                                       │ │
│ │ Config-to-Instance Mapping                                                            │ │
│ │                                                                                       │ │
│ │ class ConfigInstanceManager:                                                          │ │
│ │     def get_instance_name(self, user_id: str, config_id: str) -> str:                 │ │
│ │         return f"ggbot-{user_id[:8]}-{config_id[:8]}"                                 │ │
│ │                                                                                       │ │
│ │     def get_account_name(self, user_id: str, config_id: str) -> str:                  │ │
│ │         return f"paper_ggbot_{user_id[:8]}_{config_id[:8]}"                           │ │
│ │                                                                                       │ │
│ │     async def ensure_mapping(self, config_id: str):                                   │ │
│ │         # Check if mapping exists in config_instances                                 │ │
│ │         existing = await self._get_mapping(config_id)                                 │ │
│ │         if not existing:                                                              │ │
│ │             # Create new mapping                                                      │ │
│ │             instance_name = self.get_instance_name(user_id, config_id)                │ │
│ │             account_name = self.get_account_name(user_id, config_id)                  │ │
│ │             await self._create_mapping(config_id, instance_name, account_name)        │ │
│ │                                                                                       │ │
│ │ 4. Migration Plan                                                                     │ │
│ │                                                                                       │ │
│ │ Phase 1: Clean Slate (Immediate)                                                      │ │
│ │                                                                                       │ │
│ │ -- 1. Create config_instances mapping table                                           │ │
│ │ CREATE TABLE config_instances (...);                                                  │ │
│ │                                                                                       │ │
│ │ -- 2. Drop legacy trading tables (clean transition)                                   │ │
│ │ DROP TABLE trades CASCADE;                                                            │ │
│ │ DROP TABLE trade_orders CASCADE;                                                      │ │
│ │ DROP TABLE account_states CASCADE;                                                    │ │
│ │ DROP TABLE position_snapshots CASCADE;                                                │ │
│ │ -- Keep: users, configurations, strategy_runs, market_data, ggshot_filter             │ │
│ │                                                                                       │ │
│ │ -- 3. Add read-only user to Hummingbot DB                                             │ │
│ │ -- (Already exists in Hummingbot setup)                                               │ │
│ │                                                                                       │ │
│ │ Phase 2: Frontend Updates                                                             │ │
│ │                                                                                       │ │
│ │ // Update dashboard to query both databases                                           │ │
│ │ // Replace trade queries with position_snapshot queries                               │ │
│ │ // Keep strategy_runs for decision audit trail                                        │ │
│ │                                                                                       │ │
│ │ Phase 3: Strategy Deployment                                                          │ │
│ │                                                                                       │ │
│ │ async def deploy_strategy(config_id: str, signal: dict):                              │ │
│ │     # 1. Ensure config-to-instance mapping                                            │ │
│ │     mapping = await self.config_manager.ensure_mapping(config_id)                     │ │
│ │                                                                                       │ │
│ │     # 2. Deploy to Hummingbot using instance_name                                     │ │
│ │     result = await self.hummingbot.deploy_controller({                                │ │
│ │         'instance_name': mapping.instance_name,                                       │ │
│ │         'account_name': mapping.hummingbot_account,                                   │ │
│ │         # ... signal parameters                                                       │ │
│ │     })                                                                                │ │
│ │                                                                                       │ │
│ │     # 3. Log decision in ggBot strategy_runs                                          │ │
│ │     await self.ggbot.create_strategy_run({                                            │ │
│ │         'config_id': config_id,                                                       │ │
│ │         'decision_data': signal,                                                      │ │
│ │         'scenario': 'TRADE_ENTRY'                                                     │ │
│ │     })                                                                                │ │
│ │                                                                                       │ │
│ │ 🎯 Recommended Architecture                                                           │ │
│ │                                                                                       │ │
│ │ Data Flow:                                                                            │ │
│ │                                                                                       │ │
│ │ 1. Signal arrives → Decision Module creates strategy_run (ggBot)                      │ │
│ │ 2. Trade executes → Hummingbot handles orders/positions (Hummingbot)                  │ │
│ │ 3. Dashboard queries → Both databases for complete picture                            │ │
│ │ 4. Analytics → Aggregate from both sources                                            │ │
│ │                                                                                       │ │
│ │ Benefits:                                                                             │ │
│ │                                                                                       │ │
│ │ - ✅ Simpler architecture - No sync complexity                                         │ │
│ │ - ✅ Real-time accuracy - Direct queries to source of truth                            │ │
│ │ - ✅ Clean separation - Decision context vs execution data                             │ │
│ │ - ✅ Audit compliance - strategy_runs maintains decision trail                         │ │
│ │ - ✅ Easy testing - Each config_id = isolated Hummingbot instance                      │ │
│ │                                                                                       │ │
│ │ Frontend Query Pattern:                                                               │ │
│ │                                                                                       │ │
│ │ // Get complete trading view for a config                                             │ │
│ │ const data = await Promise.all([                                                      │ │
│ │     // Decision context from ggBot                                                    │ │
│ │     getStrategyRuns(configId),                                                        │ │
│ │     getConfigDetails(configId),                                                       │ │
│ │                                                                                       │ │
│ │     // Execution data from Hummingbot                                                 │ │
│ │     getCurrentPositions(instanceName),                                                │ │
│ │     getTradeHistory(instanceName),                                                    │ │
│ │     getAccountBalance(accountName)                                                    │ │
│ │ ]);                                                                                   │ │
│ │                                                                                       │ │
│ │ ✅ Final Recommendation                                                                │ │
│ │                                                                                       │ │
│ │ YES - Query Hummingbot directly instead of duplicating data!                          │ │
│ │                                                                                       │ │
│ │ Keep in ggBot:                                                                        │ │
│ │ - User/config management                                                              │ │
│ │ - Decision audit trail (strategy_runs)                                                │ │
│ │ - Config-to-instance mapping                                                          │ │
│ │ - Extracted market data                                                               │ │
│ │                                                                                       │ │
│ │ Query from Hummingbot:                                                                │ │
│ │ - Trade execution details                                                             │ │
│ │ - Real-time positions                                                                 │ │
│ │ - Account balances                                                                    │ │
│ │ - Order history                                                                       │ │
│ │                                                                                       │ │
│ │ Clean transition: Drop legacy trade tables, create config_instances mapping, update   │ │
│ │ frontend to query both databases.   