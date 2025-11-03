# TODO.md - ggbots Implementation Plan

## 🏆 **URGENT - AsterDEX Live Trading Integration** [ASTER.md]

**Timeline**: 7-8 days - Win $50k ASTER token prize in Vibe Trading Competition
**Status**: Phase 1 Complete - Live Trading Operational ✅

**See**: [DOCS/ASTER.md](DOCS/ASTER.md) for complete technical architecture and design

**Competition Context**: AsterDEX is running a trading competition with $50,000 in ASTER tokens for highest volume trader. ggbots' autonomous 24/7 AI trading is perfectly positioned to win.

**Integration Approach**: Follow proven Symphony.io pattern with minimal code changes:
- Same orchestrator routing (`trading_mode: 'aster'`)
- Same trade intent interface
- Same credential management (Vault)
- Same frontend display logic

### **Phase 1: Service Foundation** (Days 1-2)

**Goal**: Core trading execution working

- [x] **AsterDEX Service Implementation** (`trading/live/aster_service_v3.py`)
  - [x] Create `AsterDEXV3LiveTradingService` class with Symphony-style interface
  - [x] Implement Web3 ECDSA signature generation (v3 API)
  - [x] Implement `execute_trade_intent()` method
  - [x] Add symbol validation using standardizer
  - [x] Add idempotency protection (decision_id uniqueness)
  - [x] Test live trade execution (BTC-USDT: OPEN + CLOSE successful)
  - [ ] Add SL/TP conditional order creation (STOP_MARKET, TAKE_PROFIT_MARKET)
  - [ ] Add leverage management (currently defaults to 10x)

- [x] **Symbol Standardization** (`core/symbols/standardizer.py`)
  - [x] Add `to_aster()` method (BTC-USDT → BTCUSDT)
  - [x] Add `from_aster()` method (BTCUSDT → BTC-USDT)
  - [x] Add `is_aster_compatible()` method
  - [x] Cross-reference 33 compatible symbols from 142 total

- [ ] **Vault Integration** (`core/auth/vault_utils.py`)
  - [ ] Add `get_aster_credential(user_id)` method
  - [ ] Add `store_aster_credential(user_id, api_key, api_secret)` method
  - [ ] Add `delete_aster_credential(user_id)` method
  - [ ] Test credential encryption/decryption

- [x] **Database Schema** (`database/migrations/`)
  - [x] Extend `live_trades` table with `provider` field (VARCHAR 20, DEFAULT 'symphony')
  - [x] Backfill existing trades: `UPDATE live_trades SET provider = 'symphony'`
  - [x] Add `stop_loss_order_id` and `take_profit_order_id` fields (nullable)
  - [x] Add provider-aware indexes (`idx_live_trades_provider`, `idx_live_trades_provider_open`)
  - [x] Execute migration in Supabase
  - [ ] Fix `decision_id` foreign key (make nullable for test trades)

### **Phase 2: Position Management** (Days 3-4) ✅

**Goal**: Query positions, close trades, get account status

- [x] **Query Endpoints Implementation**
  - [x] Implement `_get_position_risk()` (GET /fapi/v3/positionRisk)
  - [x] Implement `_get_account_balance()` (GET /fapi/v3/balance)
  - [x] Add response transformation to standard format
  - [x] Test with live credentials

- [x] **Close Position Functionality**
  - [x] Implement market close via `_place_market_order()`
  - [x] Test position close (BTC-USDT closed successfully)
  - [ ] Add SL/TP order cancellation before close
  - [ ] Update `live_trades.closed_at` timestamp via `close_position(batch_id, user_id)`

- [ ] **Error Handling**
  - [ ] Add rate limit tracking and backoff logic
  - [ ] Implement circuit breaker at 80% rate limit
  - [ ] Add retry logic with exponential backoff
  - [ ] Handle common API errors gracefully (-1121, -2010, etc.)

### **Phase 3: Orchestrator Integration** (Day 5) ✅

**Goal**: Connect AsterDEX service to main trading pipeline

- [x] **Orchestrator Changes** (`ggbot.py`)
  - [x] Import `AsterDEXV3LiveTradingService`
  - [x] Initialize `self.aster_trading` in `__init__()`
  - [x] Add `'aster'` routing to `_run_trading_v2()`
  - [x] Test routing with live service
  - [x] Verify no impact on existing paper/Symphony flows

- [x] **Dynamic Position Sizing** (`trading/live/aster_service_v3.py`)
  - [x] Implement `_calculate_weight()` with account balance query
  - [x] Respect bot config (ACCOUNT_PERCENTAGE, CONFIDENCE_BASED, FIXED_USD)
  - [x] Add safety caps (95% of available balance)
  - [x] Validate minimum quantities (0.001 BTC)
  - [x] Test with $9.84 account balance

- [x] **Agent Position Size Overrides** (Full Stack Implementation)
  - [x] Add override support to all trading services (Aster, Paper, Symphony)
  - [x] Create `/api/v2/agent/execute-trade` endpoint with override params
  - [x] Update agent API client to pass `size_usd` and `leverage` params
  - [x] Wire up agent MCP tool with override parameters
  - [x] Add comprehensive validation and safety checks

- [ ] **Configuration Support** (`core/config/models.py`)
  - [x] Add `'aster'` to trading_mode options (already supports via string field)
  - [ ] Add `aster_account_id` optional field
  - [ ] Update BotConfigV2 validation for aster mode
  - [ ] Test config creation/loading

- [ ] **API Endpoints** (`ggbot.py` or `api/aster.py`)
  - [x] Add `POST /api/v2/agent/execute-trade` (agent trade execution with overrides)
  - [ ] Add `POST /api/v2/aster/setup` (store credentials)
  - [ ] Add `GET /api/v2/aster/status` (check connection)
  - [ ] Add `POST /api/v2/aster/disconnect` (remove credentials)
  - [ ] Add `GET /api/v2/positions/aster/{config_id}` (query positions)
  - [ ] Add `POST /api/v2/positions/aster/{order_id}/close` (close position)
  - [ ] Add `GET /api/v2/account/aster/{config_id}` (account metrics)
  - [ ] Add `POST /api/v2/config/duplicate-as-aster` (duplicate bot)
  - [ ] Test all endpoints with Postman/curl

### **Phase 4: Frontend Integration** (Day 6)

**Goal**: UI for credential setup and aster mode selection

- [ ] **Settings Modal** (`frontend/app/forge/components/settings/`)
  - [ ] Add "AsterDEX" tab to Settings modal
  - [ ] Add API Key + Secret input fields
  - [ ] Add "Test Connection" button (calls /api/v2/aster/status)
  - [ ] Add "Disconnect" button with confirmation
  - [ ] Show connection status indicator

- [ ] **Trading Mode Selection** (`frontend/app/forge/components/configure/`)
  - [ ] Add "AsterDEX Live" option to trading mode selector
  - [ ] Show AsterDEX badge in bot rail (orange/purple color)
  - [ ] Disable AsterDEX option if credentials not configured
  - [ ] Add tooltip explaining AsterDEX mode

- [ ] **Dashboard Display** (`frontend/app/forge/components/monitor/`)
  - [ ] Add SSE enrichment for `trading_mode === 'aster'`
  - [ ] Route close button to `/api/v2/positions/aster/`
  - [ ] Show "Track on AsterDEX" for balance (like Symphony)
  - [ ] Add AsterDEX icon/badge to active positions

- [ ] **Duplicate Bot Flow**
  - [ ] Add "Deploy AsterDEX Version" button (like Symphony)
  - [ ] Show confirmation modal with warning
  - [ ] Create new bot with `trading_mode='aster'`
  - [ ] Navigate to new bot config

### **Phase 5: Testing & Validation** (Day 7)

**Goal**: Production-ready, all tests passing

- [ ] **Unit Tests**
  - [ ] Test signature generation with known examples
  - [ ] Test symbol conversion (all 141 pairs)
  - [ ] Test order parameter formatting
  - [ ] Test error handling logic
  - [ ] All unit tests passing (pytest)

- [ ] **Integration Tests**
  - [ ] Test API connection (ping, time, exchangeInfo)
  - [ ] Test authentication with testnet credentials
  - [ ] Test account balance query
  - [ ] Test order placement on testnet
  - [ ] Test position query on testnet
  - [ ] Test order cancellation on testnet

- [ ] **End-to-End Tests**
  - [ ] Create aster bot via frontend
  - [ ] Setup credentials via Settings modal
  - [ ] Execute 1 manual trade cycle
  - [ ] Verify order on AsterDEX platform
  - [ ] Close position via dashboard
  - [ ] Verify audit trail in aster_trades table
  - [ ] Run autonomous bot for 1 hour
  - [ ] Verify all trades logged correctly

- [ ] **Production Validation**
  - [ ] Test with real credentials (small amounts)
  - [ ] Execute 10 trades successfully
  - [ ] Verify SL/TP conditional orders work
  - [ ] Test error scenarios (insufficient balance, invalid symbol)
  - [ ] Monitor rate limiting (no 429 errors)
  - [ ] Verify no impact on paper/Symphony trading

### **Phase 6: Competition Launch** (Day 8+)

**Goal**: Compete for $50k prize

- [ ] **Competition Strategy**
  - [ ] Create 5-10 aster bots (multi-symbol)
  - [ ] Configure for high-frequency trading (5m interval)
  - [ ] Set moderate leverage (3-5x)
  - [ ] Enable tight SL/TP for quick exits
  - [ ] Activate all bots simultaneously

- [ ] **Monitoring & Optimization**
  - [ ] Monitor total volume daily
  - [ ] Track competition leaderboard ranking
  - [ ] Optimize strategies based on performance
  - [ ] Adjust position sizes for max volume
  - [ ] Monitor balance stability (>80% starting capital)

- [ ] **Risk Management**
  - [ ] Set max position size to 1% of balance per bot
  - [ ] Monitor total exposure across all bots
  - [ ] Set balance alert at -20% drawdown
  - [ ] Emergency stop all bots if needed
  - [ ] Daily balance reconciliation

### **Success Metrics**

- ✅ Zero authentication errors in production
- ✅ <1% failed trade rate
- ✅ Sub-2s trade execution latency
- ✅ 100% audit trail accuracy
- ✅ Top 10 competition ranking (volume)
- ✅ $50k prize won (stretch goal)

**Next Steps**: Start with Phase 1 - Service Foundation (Days 1-2)

### **Phase 7: Post-Competition Cleanup** (After Competition)

**Goal**: Update Symphony service for consistency with provider pattern

- [ ] **Symphony Service Update** (`trading/live/symphony_service.py`)
  - [ ] Update `_save_trade_record()` to include `provider='symphony'` in INSERT
  - [ ] Update trade queries to use `WHERE provider='symphony'`
  - [ ] Test Symphony trades still save/query correctly
  - [ ] Verify backward compatibility with existing trades
  - [ ] Update any hardcoded table queries in `get_open_positions()`

**Note**: This is non-urgent cleanup. Symphony works fine without this change due to DEFAULT value, but explicit is better than implicit.

---

## 📊 **Activity Timeline Integration** ✅ COMPLETE

**Status**: Agent activity logging operational (2025-11-03)
**See**: [DOCS/todo/ACTIVITY_TIMELINE.md](DOCS/todo/ACTIVITY_TIMELINE.md) for implementation details

**Completed**:
- ✅ Activities table with RLS, indexes, priority-based grouping
- ✅ Activity logger helper (`core/common/activity_logger.py`)
- ✅ Agent MCP tool integration (log_activity + auto-logging in 6 tools)
- ✅ 3 API endpoints (activities, balance-series, metadata)
- ✅ Aster P&L integration (queries `/fapi/v3/userTrades`, combines with paper trades)
- ✅ Frontend Activity Timeline with real data, 10s polling, React hooks compliance
- ✅ UI refinements (trade_win/loss icons, live status indicator, dynamic layout)

**Next Steps**:
- Agent needs to run and create activities for full timeline visualization
- Add scheduled bot activity logging (orchestrator integration)
- Optional: Trade lifecycle linking, "View Configuration" modal for competition
- Active Positions section at bottom of timeline
- Submission-ready view page for Aster Vibe Trading Competition

### **Phase 1: Database & Infrastructure** (2-3 days)
- [ ] Create unified `activities` table (replaces separate `agent_activities` concept)
- [ ] Add indexes for performance (config_id, created_at, trade_id, priority)
- [ ] Enable RLS policy for user isolation
- [ ] Create `log_activity()` helper function (`core/common/activity_logger.py`)
- [ ] Test basic INSERT/SELECT operations

### **Phase 2: Orchestrator Integration** (2-3 days)
- [ ] **Scheduled Bot Logging** (`ggbot.py`)
  - [ ] Log market_query activities after extraction
  - [ ] Log decision_made activities after decision engine
  - [ ] Log trade_entry_long/short on position open
  - [ ] Log trade_exit on position close
- [ ] **Agent Tool Logging** (`agent/mcp_server.py`)
  - [ ] Update query_market_data to auto-log
  - [ ] Update execute_trade to auto-log
  - [ ] Update close_position to auto-log
  - [ ] Update wait_for to auto-log
  - [ ] Add new log_activity tool for explicit logging
- [ ] Test with real bot/agent execution
- [ ] Verify activities appear in database with correct linking

### **Phase 3: API Endpoints** (1-2 days)
- [ ] Create `api/activities.py` with 3 endpoints:
  - [ ] `GET /api/v2/activities/{config_id}` - Get all activities with filters
  - [ ] `GET /api/v2/activities/{config_id}/balance-series` - Equity curve data
  - [ ] `GET /api/v2/activities/{config_id}/metadata` - Bot stats for header
- [ ] Add query filters (time range, activity types, trade_id, importance)
- [ ] Register router in ggbot.py
- [ ] Test with Postman/curl
- [ ] Verify auth and ownership checks

### **Phase 4: Frontend Integration** (2-3 days)
- [ ] **Replace Mock Data** (`ActivityTimelineViewer.tsx`)
  - [ ] Remove generateMockActivityLog()
  - [ ] Add API calls to three endpoints
  - [ ] Add loading/error/empty states
  - [ ] Implement 10s polling for real-time updates
- [ ] **Trade Lifecycle Highlighting**
  - [ ] Add selectedTradeId state
  - [ ] Highlight icons with glow effect when trade selected
  - [ ] Draw connection lines between related activities
  - [ ] Filter side panel to show trade narrative
- [ ] **Enhanced Side Panel**
  - [ ] Create TradeNarrativePanel component
  - [ ] Group activities by phase (entry → monitoring → exit)
  - [ ] Show trade outcome (P&L, duration)
  - [ ] Expandable cards for activity details
- [ ] Test with real data from test bot

### **Phase 5: Testing & Polish** (1-2 days)
- [ ] End-to-end testing with scheduled bot
- [ ] End-to-end testing with agent bot
- [ ] Test trade lifecycle clicking and highlighting
- [ ] Test zoom levels (icons appear/disappear correctly)
- [ ] Test empty state, loading state, error state
- [ ] Test performance with 100+ activities
- [ ] Mobile responsive testing
- [ ] Edge cases (long timelines, no exit yet, etc.)

### **Phase 6: Competition Features** (1-2 days)
- [ ] **View Configuration Modal**
  - [ ] Track conversation history in `agent/run_agent.py` during strategy definition
  - [ ] Save `conversation_history` array in `config_data.agent_strategy`
  - [ ] Create `ConfigurationModal.tsx` with two-column layout (conversation + strategy)
  - [ ] Add "View Configuration" button to view page (left of "Jump to Now")
  - [ ] Test modal displays conversation + strategy correctly
- [ ] **Active Positions Section**
  - [ ] Add `PositionsTable` component to bottom of view page
  - [ ] Style with proper spacing and borders
  - [ ] Test with open/empty positions
- [ ] **Competition Testing**
  - [ ] Test full page with live agent `d13d5536-2498-4f27-b2bc-e4f98958e1d8`
  - [ ] Verify page renders on mobile/tablet
  - [ ] Take screenshots for submission materials
  - [ ] Verify public access (no auth required)

**Success Metrics**:
- ✅ Unified activities table capturing all bot/agent actions
- ✅ Timeline displays real activities with correct icons/timestamps
- ✅ Trade clicking highlights all related activities
- ✅ Side panel shows rich details and trade narratives
- ✅ Real-time updates via polling (10s interval)
- ✅ All bot types (agents, scheduled, signal validation) supported
- ✅ Canvas performance smooth at 60fps
- ✅ Competition features: View Configuration modal + Active Positions section

---

## 🤖 **HIGH PRIORITY - Autonomous Trading Agent** [AGENT.md]

**Timeline**: 1-2 weeks - Enable fully autonomous AI trading agents using Claude Agent SDK

**See**: [DOCS/todo/AGENT.md](DOCS/todo/AGENT.md) for complete architecture and design decisions

**Vision**: Transform ggbots from bot platform (scheduled execution) to agent infrastructure (autonomous AI decision-making)

**Status**: Phase 3 complete (11 tools working), Phase 3.5 complete (full config integration)

**Key Features**:
- **Two-phase system**: Conversation Mode → Autonomous Mode
- **Two personalities**: Guided (user-defined strategy) vs Experimental (agent-evolving strategy)
- **Minimal DB changes**: 1 field + 1 table
- **7 tools**: Market data, trading, positions, account, wait, update_strategy, record_learning
- **Context-based compaction**: Auto-reload at 150k tokens
- **Single agent per user** (initially)

### **Phase 1: Database & Foundation** (1 day)

**Goal**: Database schema changes, project setup

**Architecture Decision**: Agent runs as **separate microservice** with isolated venv to avoid dependency conflicts.
- Agent uses `.venv-agent/` (isolated dependencies)
- Main ggbot uses `.venv/` (unchanged)
- Communication: HTTP API + direct DB/Redis access
- Deployment: PM2 process with interpreter path to `.venv-agent/bin/python`

- [x] **Database Changes**
  - [x] Add `created_by TEXT DEFAULT 'decision_engine_v2'` column to `decisions` table
  - [x] Create `agent_memory` table (id, config_id, user_id, memory_type, content, importance, created_at)
  - [x] Migration executed successfully in Supabase
  - [x] Verified paper close endpoint exists: `POST /api/v2/paper/{config_id}/positions/{trade_id}/close`

- [x] **Project Setup**
  - [x] Create `agent/` directory structure (5 stub files)
  - [x] Create `requirements-agent.txt` with isolated dependencies
  - [x] Create `scripts/setup_agent_venv.sh` for venv setup
  - [x] Update `.env.example` with agent configuration
  - [x] Redis already running (verified in ACTIVE.md)
  - [x] Run `./scripts/setup_agent_venv.sh` to create agent venv
  - [x] Test agent venv installation (Claude Agent SDK imported successfully)
  - [x] Configure `.env` with ANTHROPIC_API_KEY and AGENT_WHITELIST_USER_ID
  - [x] Add `.venv-agent/` to `.gitignore`

**Phase 1 Status**: ✅ **COMPLETE**

### **Phase 2: MCP Server & Tools** (2-3 days)

**Goal**: Build 9 MCP tools, implement trade observations model

- [x] **Database Migration**
  - [x] Replace `agent_memory` with `trade_observations` table (post-trade reflection model)
  - [x] Migration executed in Supabase, verified with 13 columns, 8 indexes, RLS enabled

- [x] **API Endpoints** (`api/agent.py`)
  - [x] 7 existing endpoints + 2 new: `POST /agent/trade-observations`, `POST /agent/trade-observations/query`

- [x] **Service Client** (`agent/service_client.py`)
  - [x] HTTP client with retry logic for all 9 endpoints (market data, trading, positions, account, strategy, observations)

- [x] **MCP Server Tools** (`agent/mcp_server.py`)
  - [x] 9 tools implemented: query_market_data, execute_trade, get_positions, get_account_status, close_position, update_strategy, wait_for, record_trade_observation, query_trade_observations
  - [x] Module-level AgentContext for single-agent testing
  - [x] MCP server tested and verified (9 tools registered)

**Phase 2 Status**: ✅ **COMPLETE**

### **Phase 3: Agent Runner** (2-3 days) - ✅ **COMPLETE**

**Goal**: Build conversation + autonomous modes, test end-to-end

**Status**: All 9 tools operational, agent ready for autonomous trading. Auth deadlock resolved via simplified service authentication.

- [x] **TradingAgent Class** (`agent/run_agent.py`)
  - [x] Simplified architecture: Separate strategy_definition and autonomous modes (no dual tasks)
  - [x] Initialize ClaudeSDKClient with MCP server
  - [x] Build single system prompt with mode/strategy context injection
  - [x] Added 32 data points documentation (7 categories) to system prompt
  - [x] Redis queue integration (messages and responses)
  - [x] Strategy definition mode: Simple query/response loop via Redis
  - [x] Autonomous mode: Pure `receive_messages()` infinite loop
  - [x] Mode switching logic: Detects flag, handles user confirmation "1" (save)/"2" (revise)
  - [x] Strategy persistence: Saves to `config_data.agent_strategy` in database
  - [ ] Compaction context injection (deferred to Phase 4 - SDK auto-compacts at 95%)

- [x] **Message Queue Integration**
  - [x] Redis queue for user → agent messages: `agent:{config_id}:messages`
  - [x] Redis queue for agent → user responses: `agent:{config_id}:responses`
  - [x] Removed dual-task complexity after SDK stream conflicts

- [x] **MCP Tools** - All 10 tools operational ✅
  - [x] Added `request_autonomous_mode` tool (10 tools total)
  - [x] Updated `query_market_data` tool to use category-based structure (7 categories, 32 data points)
  - [x] Fixed dict parameter parsing (JSON string handling)
  - [x] Added tool sandboxing with `disallowed_tools` (restricts agent to trading-only operations)
  - [x] Tool Status (9/9 working):
    - ✅ `query_market_data` - 32 data points across 7 categories
    - ✅ `execute_trade` - Opens positions with SL/TP
    - ✅ `get_positions` - Returns all open positions
    - ✅ `close_position` - Closes trades with realized P&L
    - ✅ `get_account_status` - Account balance & performance metrics
    - ✅ `wait_for` - Agent timing control (up to 24 hours)
    - ✅ `update_strategy` - Strategy modification (when autonomously_editable=true)
    - ✅ `record_trade_observation` - Post-trade reflection logging
    - ✅ `query_trade_observations` - Search past learnings
    - ✅ `request_autonomous_mode` - Mode switching with user confirmation

- [x] **API Endpoints** (`api/agent.py`) - All 8 endpoints operational ✅
  - [x] All 8 endpoints exist and registered in ggbot.py
  - [x] Orchestrator supports `data_points_override` for dynamic queries
  - [x] Simplified service authentication (removed `Depends()` complexity)
  - [x] Fixed `get_configuration()` positional argument bug
  - [x] Added JSON serialization for numpy/pandas objects
  - [x] Fixed paper trading method signatures (`get_open_positions`, `close_position`)
  - [x] Fixed SQL column names (`current_price` vs `exit_price`)
  - [x] Fixed request body structure for `record_trade_observation`

- [x] **Service Client** (`agent/service_client.py`)
  - [x] Complete rewrite with service authentication
  - [x] Sends `Authorization: Bearer {SERVICE_KEY}` header
  - [x] Sends `X-Service-Auth: agent-runner` header
  - [x] All methods send `params={"user_id": self.user_id}` query parameter
  - [x] Proper retry logic with exponential backoff

- [x] **Backend Authentication** - Production-safe service auth ✅
  - [x] Replaced complex `Depends(get_service_or_user_auth)` with simple `validate_agent_service_auth()`
  - [x] Synchronous header validation (no async dependency chain)
  - [x] Resolved FastAPI event loop deadlock
  - [x] All endpoints tested and working without timeout

- [x] **Model Configuration**
  - [x] Model selected: `claude-haiku-4-5-20251001` for testing ($1/$5 per MTok)
  - [ ] Test token usage and performance with Haiku
  - [ ] Note: Upgrade to `claude-sonnet-4-5-20250929` for production ($3/$15 per MTok)

- [x] **CLI Testing Interface**
  - [x] Rewrote `agent/chat.py` with concurrent tasks for real-time responses
  - [x] Uses `aioconsole.ainput()` for non-blocking input
  - [x] Response monitor shows agent messages immediately

- [x] **End-to-End Testing** - ✅ Live testing successful!
  - [x] All 11 tools verified working (2025-11-01)
  - [x] Test: Conversation mode → strategy confirmation → autonomous mode switch
  - [x] Test: Guided mode agent executes user-defined strategy (in progress - agent running live)
  - [ ] Test: Experimental mode agent updates its own strategy (requires autonomously_editable=true)
  - [ ] Test: Agent runs for 1+ hours autonomously with wait_for (in progress - 90min wait active)
  - [ ] Test: Compaction triggers (SDK auto-compacts at 95%)
  - [ ] Verify all decisions logged with `created_by='agent'`
  - [ ] Verify trade_observations records created

- [x] **System Prompt Refinements** (2025-11-01)
  - [x] Made strategy-neutral (removed prescriptive trading advice)
  - [x] Added experience-based branching (beginner vs advanced onboarding)
  - [x] Added full data source listing (32 data points, 7 categories)
  - [x] Added timeframe documentation (7 timeframes for technical indicators)
  - [x] Files: agent/run_agent.py, agent/mcp_server.py

- [x] **Bug Fixes** (2025-11-01)
  - [x] Fixed .env port mismatch (API_BASE_URL: 8002 → 8000)
  - [x] Fixed record_trade_observation JSON parsing (handles freeform text strings)

**Phase 3 Status**: ✅ **COMPLETE** - Live autonomous trading operational!

### **Phase 4: Frontend Integration & Activity Timeline** (2-3 weeks)

**Status**: Planning Complete - Ready for Implementation
**See**: [DOCS/todo/AGENT_P4.md](DOCS/todo/AGENT_P4.md) for complete technical specification

**Goal**: Two-column strategy definition interface + real-time activity visualization

#### **Key Architecture Decisions**:
- ✅ Tool-based activity logging (new `log_activity` tool + auto-logging from existing tools)
- ✅ Unified `agent_activities` table for timeline events
- ✅ "Agentic" config type in Forge (Scheduled Trading | Signal Validation | Agentic)
- ✅ AgentConfigurator component: chat (left) + strategy display (right)
- ✅ Activity Timeline connects to real data (not mock)
- ✅ Local state design, SSE + Redis polling for real-time updates

#### **Phase 4a: Strategy Definition UI** (Week 1-2) - ✅ **COMPLETE** (2025-11-03)
- [x] Config type selection redesign (3-button selector with permissions)
- [x] AgentConfigurator component with two-column layout
- [x] Chat interface with Redis queue integration
- [x] Strategy confirmation flow + display
- [x] Auto-start agent in strategy_definition mode
- [x] Redis polling (2s interval) for agent responses
- [x] Backend API endpoints (start, stop, message, poll-response, status)
- [x] Updated request_autonomous_mode tool with show_confirm_button flag
- [x] Renamed "Autonomous Trading" → "Scheduled Trading" (config type cleanup)
- [x] **Bot Creation Modal** - Moved type selection from Configure to creation flow
  - [x] Created `BotCreationModal.tsx` with 3 bot types (Scheduled/Signal/Agentic)
  - [x] Permission gating per type (Free/Pro/Whitelist)
  - [x] Integrated with BotRail and MobileNav
  - [x] Updated `createDefaultBot()` to accept botType parameter
  - [x] Agentic bots created with minimal config (agent defines strategy via chat)
- [x] **SaveConfigBar Refactor** - Converted to static type display
  - [x] Removed 3-button type selector
  - [x] Added static type badge display (icon + label)
  - [x] Kept Save/Cancel/Reset buttons for scheduled_trading & signal_validation
- [x] **Agentic Bot State Machine** - 4-state UI flow
  - [x] State 1: No strategy, inactive → "Start Strategy Discussion" button
  - [x] State 2: Has strategy, inactive → Strategy display + "Refine Strategy" button
  - [x] State 3: Has strategy, active → Strategy display + disabled button (must deactivate first)
  - [x] State 4: Agent running → Chat interface with AgentConfigurator
- [x] **Strategy Editing Flow** - Context-aware conversation
  - [x] Added `handleStartStrategyDiscussion()` handler
  - [x] Auto-sends existing strategy as context when refining
  - [x] Starts agent in strategy_definition mode
  - [x] Waits for agent greeting then polls responses
- [x] **Autonomously Editable Setting** - User choice during confirmation
  - [x] Added checkbox to AgentConfigurator confirmation UI
  - [x] Updated `handleConfirmStrategy()` to send JSON: `{confirm: true, autonomously_editable: boolean}`
  - [x] Backend `run_agent.py` parses JSON and saves setting to database
  - [x] Backward compatible with old "1"/"2" format
- [ ] ActivationBar integration for agentic mode (deferred - not needed for strategy definition)
- [ ] "Begin Strategy Discussion" button for editing (DONE - integrated into state machine)

#### **Phase 4b: Activity Timeline Integration** (Week 2-3)

**Note**: Activity Timeline has been consolidated into a universal feature that works for ALL bot types (agents, scheduled, signal validation).

**See**: [DOCS/todo/ACTIVITY_TIMELINE.md](DOCS/todo/ACTIVITY_TIMELINE.md) for complete implementation plan

- [ ] This section moved to standalone "Activity Timeline Integration" section below

**Testing with existing agent**: config_id `d13d5536-2498-4f27-b2bc-e4f98958e1d8`

#### **Phase 4c: Autonomous Mode Launch Flow** (Day 3) - ✅ **COMPLETE** (2025-11-03)

**Goal**: Remove confirmation friction, enable clean strategy-to-autonomous transition

- [x] **Removed Confirmation Flow**
  - [x] Replaced `request_autonomous_mode` tool with `save_strategy_and_exit`
  - [x] Tool saves strategy directly to database and exits (no user confirmation needed)
  - [x] Tool deletes own PM2 process to prevent auto-restart loop
  - [x] Agent exits cleanly after strategy definition complete

- [x] **Frontend Routing Fixes**
  - [x] Fixed activation button to route agents to `/api/v2/agent/{id}/start?mode=autonomous`
  - [x] Fixed stop button to route agents to `/api/v2/agent/{id}/stop`
  - [x] Fixed config_type check (was checking `config_data.config_type`, now checks `config_type` column)
  - [x] Activate/Deactivate buttons now work for agent configs

- [x] **System Prompt Improvements**
  - [x] Fixed f-string syntax error (escaped curly braces in examples)
  - [x] Added explicit rules for ggshot category placement (trading_signals, NOT technical_analysis)
  - [x] Added category name validation guidance

- [x] **Autonomous Mode Validation**
  - [x] Agent runs autonomously with 5-minute monitoring cycles
  - [x] Disciplined decision-making (waits for ALL entry conditions)
  - [x] Proper tool usage (query_market_data, get_current_price, wait_for)
  - [x] Professional analysis with data tables and reasoning

**Phase 4c Status**: ✅ **COMPLETE** - Agents can now autonomously trade 24/7!

### **Phase 5: Production Deployment** (1-2 days) - 🟡 **IN PROGRESS**

**Goal**: Deploy, monitor, document

- [x] **Deployment** - Core infrastructure operational
  - [x] Agent code deployed to production
  - [x] PM2 service working (agents spawn via `/api/v2/agent/{id}/start`)
  - [x] Environment variables configured (.venv-agent, ANTHROPIC_API_KEY)
  - [x] Redis message queues operational (messages, responses, history)
  - [x] Agent startup/shutdown/restart tested and working
  - [ ] Lifecycle management improvements (cleanup on delete, restart policies)

- [ ] **Monitoring**
  - [ ] Agent-specific logging (mode, tokens, strategy version)
  - [ ] Track tool call frequency
  - [ ] Monitor compaction events
  - [ ] Alert on agent failures/errors
  - [ ] Track strategy performance by mode (guided vs experimental)

- [ ] **Documentation**
  - [ ] Agent usage guide (`agent/README.md`)
  - [ ] Example strategies (conservative, aggressive, experimental)
  - [ ] Troubleshooting guide
  - [ ] API documentation for agent endpoints

### **Future Enhancements** (Post-Launch)

- [ ] **Multi-Agent Support**
  - [ ] Multiple agents per user
  - [ ] Agent coordination and position awareness
  - [ ] Portfolio-level risk management

- [ ] **Enhanced Learning**
  - [ ] Automatic learning promotion (agent_memory → config_data)
  - [ ] Learning importance auto-scoring
  - [ ] Strategy template library from successful experimental agents

- [ ] **Advanced Interaction**
  - [ ] Mid-trade explanations ("Why did you enter here?")
  - [ ] Strategy refinement via conversation while autonomous
  - [ ] Real-time reasoning display in dashboard

- [ ] **Model Flexibility**
  - [ ] Per-agent model selection (Haiku for budget, Sonnet for premium, Opus for specialized)
  - [ ] Cost tracking per agent
  - [ ] Model performance comparison dashboard

---

## 🧠 **HIGH PRIORITY - Market Intelligence Expansion**

**Timeline**: 4-6 weeks - Add contextual data to improve AI decision quality

**See**: [DOCS/MARKET_INTELLIGENCE_ROADMAP.md](DOCS/MARKET_INTELLIGENCE_ROADMAP.md) for complete roadmap

**Current State**:
- ✅ Infrastructure complete (data_sources/data_points tables, UI, API)
- ✅ 7 categories finalized (Technical Analysis, Trading Signals, On-Chain, Derivatives & Leverage, Sentiment & Social, News & Regulatory, Macro Economics)
- ✅ 7/7 data sources populated (Technical Analysis: 21, Trading Signals: 1, Derivatives & Leverage: 2, Macro: 4, On-Chain: 2, Sentiment: 1, News: 1 = **32 total**)
- ✅ Intelligence Orchestrator **PRODUCTION READY** (`market_intelligence/orchestrator.py`) - parallel query execution, custom TTL per data point
- ✅ **GrokAgenticAdapter PRODUCTION DEPLOYED** - ONE universal adapter handles 8 data sources via XAI's agentic API (web search, X search, code execution)
- ✅ 8 new Grok data points **LIVE IN PRODUCTION** (VIX, DXY, CPI, NFP, BTC TVL, whale activity, Twitter sentiment, crypto news) - all FREE tier
- ✅ Decision engine integration complete (formatting methods, prompt updates, real bot tested)
- ✅ Tested production: All 8 data points working, parallel execution ~30s, comprehensive AI reasoning
- ✅ **PHASE 1 COMPLETE** - $195/month platform cost ($0.76/user/month at 257 users, $0.20/user at 1000 users)

### **Phase 1: Grok-Powered Intelligence** (COMPLETE - Ready for Production) - $160-240/month platform cost

**Goal**: Add 7 contextual data points via 3 acquisition methods (Direct API, Grok Search, Browser-Use)

**New Data Source: Derivatives & Leverage** (2 points) - ✅ COMPLETE
- [x] Create `BinanceFundingAdapter` for perpetual funding rates
- [x] Create catalog YAML: `funding_rate.yaml`
- [x] Seed database: INSERT 1 data_source + 2 data_points (BTC, ETH)
- [x] Test: Fetch BTC/ETH funding rates from Binance API (tested live: BTC 0.0026%, ETH 0.0063%)

**New Data Sources via GrokAgenticAdapter** (8 points) - ✅ **PRODUCTION DEPLOYED**
- [x] Create `GrokAgenticAdapter` - universal adapter with 8 prompt templates (VIX, DXY, CPI, NFP, Twitter, news, TVL, whales)
- [x] Create catalog YAML: `grok_agentic.yaml` with query_type parameter support
- [x] Update `catalog_mapping.py` with 8 new entries + custom cache TTL per data point (10min to 24hrs)
- [x] Test all 8 query types - ✅ SUCCESS (total cost $0.11, all queries working)
- [x] Install xai-sdk (v1.3.1) - supports agentic tool calling with streaming
- [x] **Seed database**: INSERT 4 data_sources + 8 data_points (all FREE tier)
- [x] Fix gateway adapter routing for `agentic` category
- [x] Fix ggShot adapter data source name (`signals_group_chats` → `trading_signals`)
- [x] Fix cache key KeyError (missing `name` in format context)
- [x] Fix Redis protobuf serialization (citations + tool_calls conversion)

**Intelligence Orchestrator Implementation** - ✅ **PRODUCTION DEPLOYED**
- [x] Build `IntelligenceOrchestrator` class (market_intelligence/orchestrator.py) - 260 lines, config-driven routing
- [x] Implement config parsing (read selected_data_sources from config) - `_parse_config_sources()`
- [x] Create data_point → catalog mapping logic (catalog_mapping.py) - hardcoded dict, 12 entries (2 funding + 8 Grok + 2 signals)
- [x] Add funding rates to orchestrator routing - ✅ Working via mapping
- [x] Add `data_points_override` parameter for agent dynamic queries
- [x] Implement parallel query execution - ✅ 5.3x speedup (160s → 30s)
- [x] Update `ggbot.py` to call orchestrator - ✅ Hybrid approach (technicals via old way, market intel via orchestrator)
- [x] Write comprehensive tests - 16/16 unit tests passing (tests/test_orchestrator.py)
- [ ] Migrate ggShot to use orchestrator (FUTURE - keep hardcoded for now, low risk approach)

**Decision Engine Integration** - ✅ **PRODUCTION DEPLOYED**
- [x] Add market intelligence formatting methods to decision engine - 6 methods (_format_derivatives_data, _format_macro_data, etc.)
- [x] Update prompts to include market intelligence section - opportunity_analysis.py updated
- [x] Add `market_intelligence` parameter to make_decision() - ✅ Flows from extraction → decision
- [x] Test end-to-end with real bot - ✅ Comprehensive AI reasoning with all 8 data points

**Expected Impact**: +30-40% trading edge (avoid overleveraged setups, macro-aware decisions)

---

### **Phase 2: Premium On-Chain** (Week 3-4) - $100-500/month

- [ ] Whale wallet tracking (Nansen via Browser-Use OR Arkham API)
- [ ] Exchange reserves & flows (Glassnode/CryptoQuant)
- [ ] Active addresses & network health (on-chain explorers)
- [ ] Token unlocks calendar (TokenUnlocks.app)
- [ ] Dev activity metrics (GitHub API)

---

### **Phase 3: Sentiment & Social** (Week 5-6) - $100-500/month

- [ ] Twitter/X sentiment analysis (Twitter API + NLP)
- [ ] Reddit crypto sentiment (Reddit API + NLP)
- [ ] Narrative velocity tracking (topic modeling)

---

### **Phase 4: Advanced Intelligence** (Week 7-10) - $200-1000/month

- [ ] Order book liquidity heatmaps (Coinalyze)
- [ ] CEX/DEX market share tracking
- [ ] Institutional flows (BTC ETF data)
- [ ] App/exchange traffic (SimilarWeb)
- [ ] L2 gas fees & bridge flows

---

## 🎨 **HIGH PRIORITY - User Experience Polish**

- [ ] **Improve Status Messaging**
  - [ ] Change 'next run...' to 'waiting for next candle close...' in frontend
  - [ ] Update countdown messages to be more user-friendly
  - [ ] Add explanatory tooltips for bot status states
  - [ ] Improve activation/deactivation feedback messages

- [ ] **Optional Market Data Display**
  - [ ] Consider adding expandable market analysis panel to positions
  - [ ] Implement "Show Analysis" toggle for power users
  - [ ] Add hover tooltips showing key indicators that influenced decisions
  - [ ] Design market context drawer/modal for detailed technical analysis

- [ ] **Trade History Modal**
  - [ ] Add clickable "Total Trades" metric in MetricsBar
  - [ ] Implement full-screen modal with minimalist design
  - [ ] Display last 50 closed trades: Symbol, Side, P&L, Close Reason, Timestamp
  - [ ] Color-code by win/loss for quick scanning
  - [ ] Show summary stats at top: win count, loss count, win rate
  - [ ] Optional: Click individual trade to expand details (entry/exit prices, duration, confidence)

### **Phase 3: Agent SDK Integration** (Week 3)

- [ ] **Tool Generation**
  - [ ] Implement ToolGenerator (auto-generate from catalogs)
  - [ ] Create tool registry for Agent SDK
  - [ ] Add tool discovery endpoint

- [ ] **MCP Server**
  - [ ] Implement MCP server with universal query tool
  - [ ] Add data type discovery
  - [ ] Test with Claude Desktop

- [ ] **Response Formatting Enhancement**
  - [ ] Enhance LLM format mode with better templates
  - [ ] Add insight extraction logic
  - [ ] Create default templates for all data types

### **Phase 4: Scale Data Sources** (Weeks 4-8)

- [ ] **Sentiment Analysis** (Week 4)
  - [ ] Twitter/X sentiment catalog + adapter
  - [ ] Reddit sentiment catalog + adapter
  - [ ] LunarCrush aggregated sentiment catalog + adapter

- [ ] **News & Events** (Week 5)
  - [ ] Crypto news aggregator catalog + adapter
  - [ ] Google News API catalog + adapter

- [ ] **On-Chain Data** (Week 5)
  - [ ] Glassnode (exchange flows) catalog + adapter
  - [ ] Etherscan (blockchain metrics) catalog + adapter

- [ ] **Fundamentals** (Week 6)
  - [ ] SEC EDGAR filings catalog + adapter
  - [ ] Alpha Vantage fundamentals catalog + adapter
  - [ ] Financial Modeling Prep catalog + adapter

- [ ] **Macro & Economic** (Week 7)
  - [ ] FRED (Federal Reserve data) catalog + adapter
  - [ ] BLS (Bureau of Labor Statistics) catalog + adapter
  - [ ] Treasury data catalog + adapter

- [ ] **Options & Derivatives** (Week 8)
  - [ ] Options flow aggregators catalog + adapter
  - [ ] Unusual options activity catalog + adapter
  - [ ] Put/call ratios catalog + adapter

### **Benefits Delivered**

- **Immediate**: 3x faster extractions (WebSocket cache vs REST polling)
- **Scalability**: Add 150+ data sources in weeks instead of years
- **Agent-Ready**: AI agents as first-class consumers via auto-generated tools
- **Zero Breaking Changes**: Backward compatible migration with feature flag

## 🔧 **MEDIUM PRIORITY - Paper Trading Engine Modernization** ✅ **COMPLETE**

**Status**: Migration from Hummingbot to WebSocket live prices completed October 2025 (see CHANGELOG.md).

**Implementation Details**:
- Paper trading now uses `LivePriceService` (WebSocket-first, REST fallback)
- Sub-millisecond Redis access for 100 WebSocket-cached symbols
- REST API fallback with 5s caching for remaining 42 symbols
- All 142 symbols supported with intelligent tiering
- Hummingbot archived to `archive/hummingbot/`

---

## 🔧 **MEDIUM - Trading System Completeness**

**Timeline**: 2-3 days - Core trading functionality verification and enhancement

- [ ] **Stop Loss / Take Profit Verification**
  - [ ] Check if SL/TP values are being read from configuration properly
  - [ ] Verify trade monitoring triggers TP/SL execution automatically
  - [ ] Test automated position closing at profit/loss targets
  - [ ] Ensure SL/TP levels display correctly in positions table

- [ ] **Risk Management Enforcement**
  - [ ] Validate risk management parameters are enforced
  - [ ] Implement open position limits per user/bot configuration

- [ ] **User Communication (Account Reset)**
  - [ ] Email encouraging users to try reset feature for clean V2.0 accounting
  - [ ] Optional: Add banner promoting account reset for fresh start with leverage fixes
  - [ ] Monitor user feedback channels (Telegram community, support tickets)

## 🔧 **HEDIUM PRIORITY - User Settings & API Key Management**

**Timeline**: 1-2 days - Critical for user onboarding and self-service

- [ ] **Complete User Settings Page**
  - [ ] Finish API key management interface for LLM credentials
  - [ ] Add secure credential storage using Supabase Vault
  - [ ] Implement credential validation and testing functionality
  - [ ] Add interface for managing multiple API keys per provider

- [ ] **LLM Provider Management**
  - [ ] Support OpenAI, DeepSeek, Anwhythropic, and XAI credential management
  - [ ] Add credential naming and organization features
  - [ ] Implement credential usage tracking and validation
  - [ ] Test credential encryption/decryption flow

- [ ] **Subscription & Profile Management**
  - [ ] Implement downgrade workflow (cancellation flow)
  - [ ] Implement user profile settings (Telegram integration, preferences)
  - [ ] Add account settings and preferences management


## 🔧 **MEDIUM PRIORITY - System Robustness**

**Timeline**: 2-3 days - Code quality, error handling, and reliability

- [ ] **Database Schema Optimization**
  - [ ] Remove unused `market_data` column from decisions table schema
  - [ ] Implement market data parsing utilities for future analysis needs
  - [ ] Add database indexes for performance optimization
  - [ ] Clean up any remaining schema inconsistencies

- [ ] **Error Handling & Resilience**
  - [ ] Add comprehensive error boundaries to frontend components
  - [ ] Implement graceful API failure handling with retries
  - [ ] Add circuit breakers for external service failures
  - [ ] Improve logging and error taxonomy (replace broad exceptions)

- [ ] **Node.js & Dependencies**
  - [ ] Plan upgrade from Node.js 18 to Node.js 20+ (removes Supabase warnings)
  - [ ] Update dependencies to latest compatible versions
  - [ ] Test compatibility after Node upgrade
  - [ ] Update deployment configurations for new Node version

- [ ] **Code Quality Improvements**
  - [ ] Run `ruff` + `black` for Python code formatting
  - [ ] Remove unused imports and clean up import hygiene
  - [ ] Add proper TypeScript types for signal_data structures
  - [ ] Implement defensive action mapping with unknown value logging

## 📚 **MEDIUM-LOW PRIORITY - Documentation Completeness**

**Timeline**: 3-4 days - Complete module documentation coverage and accuracy

**Current State**: 7/10 major modules have excellent READMEs (extraction/v2, market_intelligence, decision, trading, database, frontend, ggshot)

### **Phase 1: Missing Module READMEs** (2 days)
- [ ] **Create agent/README.md**
  - [ ] Document MCP server architecture and tools
  - [ ] Explain conversation mode vs autonomous mode
  - [ ] Detail agent-orchestrator communication (Redis queues, HTTP API)
  - [ ] Include tool documentation and examples
  - [ ] Document service authentication pattern
  - [ ] Add development status: "Phase 3 - Foundation Complete, Frontend In Progress"

- [ ] **Create api/README.md** (Optional - Low Priority)
  - [ ] Document all agent-specific endpoints (9 total)
  - [ ] Include authentication patterns
  - [ ] Add request/response examples
  - [ ] Note: Most other endpoints documented in ACTIVE.md

- [ ] **Create core/config/README.md** (Optional - Medium Priority)
  - [ ] Document configuration system architecture
  - [ ] Explain config_data JSONB structure
  - [ ] Detail template-based setup
  - [ ] Include config migration patterns

### **Phase 2: Existing README Review & Updates** (1-2 days)
- [ ] **Review extraction/v2/README.md** (845 lines)
  - [ ] Verify 21 preprocessors are accurate
  - [ ] Update performance metrics if changed
  - [ ] Confirm API examples still work

- [ ] **Review market_intelligence/README.md** (1154 lines)
  - [ ] Verify 32 data points match production
  - [ ] Update cost economics section ($195/month platform cost)
  - [ ] Confirm GrokAgenticAdapter documentation is current

- [ ] **Review decision/README.md** (525 lines)
  - [ ] Verify V2 template system docs
  - [ ] Update with any prompt improvements
  - [ ] Confirm webhook integration details

- [ ] **Review trading/README.md** (723 lines)
  - [ ] Verify paper trading section accurately reflects WebSocket prices (migration complete Oct 2025)
  - [ ] Verify Symphony integration docs are current
  - [ ] Update with any position monitoring improvements

- [ ] **Review database/README.md** (567 lines)
  - [ ] Add trade_observations table documentation
  - [ ] Verify paper trading tables match schema
  - [ ] Update with any recent migrations

- [ ] **Review frontend/README.md** (488 lines)
  - [ ] Verify Forge architecture documentation
  - [ ] Remove references to "new-landing" (now integrated into /landing)
  - [ ] Update subscription system details if changed

- [ ] **Review ggshot/README.md** (384 lines)
  - [ ] Verify 4-pillar framework documentation
  - [ ] Update signal processing flow if changed

### **Phase 3: Documentation Consistency** (1 day)
- [ ] **Cross-Reference Validation**
  - [ ] Ensure ACTIVE.md and module READMEs don't contradict
  - [ ] Verify README.md links to all module READMEs
  - [ ] Update DOCS/ references as needed
  - [ ] Remove any legacy/outdated information

- [ ] **Update Main README.md**
  - [ ] Add directory structure section
  - [ ] List all 7+ module READMEs with descriptions
  - [ ] Clarify agent status (Phase 3 - Foundation Complete)
  - [ ] Update frontend section (Forge = production, landing = updated)

**Benefits**:
- **Onboarding**: New developers can quickly understand each module
- **Accuracy**: Documentation matches actual production code
- **Completeness**: No major systems undocumented
- **Maintenance**: Easier to keep docs updated with clear ownership

---

## 📱 **MEDIUM PRIORITY - Mobile & Frontend Polish**

**Timeline**: 2-3 days - Complete mobile experience and component improvements

- [ ] **Mobile Responsive Design**
  - [ ] Transform three-column desktop layout to single column mobile
  - [ ] Implement 70%-width slide-in drawers for navigation
  - [ ] Create bottom tab system for drawer triggers
  - [ ] Add touch gestures for carousel navigation
  - [ ] Optimize components for narrow screen widths and touch interaction

- [ ] **Frontend Component Polish**
  - [ ] Remove any remaining hard-coded values or demo data
  - [ ] Add virtual scrolling for scenarios with >10 bots
  - [ ] Optimize performance for large bot lists
  - [ ] Polish loading states and skeleton components
  - [ ] Ensure all components handle edge cases gracefully

## 🧪 **LOW PRIORITY - Testing & Validation**

**Timeline**: 1-2 weeks - Comprehensive system validation

- [ ] **Symbol Coverage Testing**
  - [ ] Test all 142 crypto symbols for data availability
  - [ ] Verify WebSocket + REST fallback works for all supported pairs
  - [ ] Test symbol extraction success rates across all timeframes
  - [ ] Create symbol blacklist for unsupported pairs
  - [ ] Full end-to-end pipeline testing: extraction → decision → trading

- [ ] **Technical Analysis Validation**
  - [ ] Test all 21 indicator preprocessors individually
  - [ ] Validate indicator calculations against reference implementations
  - [ ] Test multi-timeframe indicator consistency and performance
  - [ ] Edge case testing (low volume, missing data, extreme price movements)

- [ ] **Load Testing & Performance**
  - [ ] Test system performance with multiple concurrent bots
  - [ ] Validate database performance under load
  - [ ] Test SSE stream performance with many connected clients
  - [ ] Cross-browser compatibility testing

- [ ] **Security & Reliability Testing**
  - [ ] Audit API endpoints for security vulnerabilities
  - [ ] Test rate limiting and authentication flows
  - [ ] Validate data isolation between users
  - [ ] Test backup and recovery procedures

---


---

## 📚 Documentation References

- **New Claude Code Instances**: `GO.md` - Start here for onboarding procedure
- **Current Status**: `ACTIVE.md` - Production system status and operational reference
- **Complete History**: `CHANGELOG.md` - All completed features, fixes, and improvements
- **Architecture**: `README.md` - Platform overview and getting started guide

