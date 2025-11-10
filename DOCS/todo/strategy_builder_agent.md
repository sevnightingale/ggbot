# Strategy Builder Agent - Shared Service Architecture

**Created**: 2025-11-08
**Status**: Planning
**Target**: Phase 1 - Separate builder from execution

---

## 🎯 Overview

### Current Problem

The agent has two modes (`strategy_definition` and `autonomous`) running as a single service per bot. This creates several issues:

1. **Confusing UX**: Mode switching requires stopping/starting PM2 services
2. **Resource Waste**: Each user needs a dedicated PM2 service just to chat about strategy
3. **Limited Scope**: Builder only helps with `agent_strategy`, can't configure scheduled bots
4. **Poor Separation**: Same 12 tools available in both modes, relies on prompt engineering to prevent execution

### Proposed Solution

**Split into two distinct agent types:**

1. **Strategy Builder Service** (shared, multi-user)
   - Single PM2 service serves all users concurrently
   - Helps configure agent strategies AND scheduled bot configs
   - NO trading execution capabilities (tool-level enforcement)
   - Always available via frontend chat interface
   - Session persistence per user

2. **Autonomous Trading Agents** (dedicated, per-bot)
   - One PM2 service per active bot (unchanged from current)
   - Started only when user clicks "Activate"
   - Executes trades 24/7 using saved strategy
   - NO configuration capabilities (execution only)

---

## 📐 Architecture Overview

### High-Level Design

```
Frontend Chat Interface
    ↓
WebSocket Connection (WSS)
    ↓
Strategy Builder Service (PM2: "strategy-builder")
    ↓
ClaudeSDKClient (single instance, multi-session)
    ↓
Builder MCP Tools (6 tools - configuration only)
    ↓
Database (strategy_builder_sessions table)


Separate Flow:

User Clicks "Activate"
    ↓
PM2 Start: agent-{config_id}
    ↓
ClaudeSDKClient (resume=session_id)
    ↓
Execution MCP Tools (9 tools - trading only)
    ↓
Database (trading_agent_sessions table)
```

### Key Differences from Current Architecture

| Aspect | Current | Proposed |
|--------|---------|----------|
| **Builder** | One PM2 per user | Single shared PM2 service |
| **Session Management** | 1:1 config_id → session_id | N:1 user_id → session_id, pooled |
| **Tool Access** | All 12 tools in both modes | Builder: 6 tools, Executor: 9 tools |
| **Startup** | User must start PM2 to chat | Always available, instant chat |
| **Scope** | Agent strategies only | Agent + scheduled bot configs |
| **Mode Switching** | PM2 restart required | No switching, separate services |

---

## 🗄️ Database Schema Changes

### New Table: `strategy_builder_sessions`

Tracks active chat sessions with the shared builder service.

**Schema:**
```sql
CREATE TABLE strategy_builder_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    config_id UUID REFERENCES configurations(config_id) ON DELETE SET NULL,
    builder_session_id VARCHAR(255),  -- Claude SDK session ID
    context_type VARCHAR(50) NOT NULL,  -- 'agent_strategy', 'scheduled_config', 'new_bot'
    last_active_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes for lookups
    INDEX idx_builder_sessions_user (user_id),
    INDEX idx_builder_sessions_config (config_id),
    INDEX idx_builder_sessions_active (last_active_at)
);
```

**Field Descriptions:**
- `session_id`: Internal UUID for tracking
- `user_id`: Which user owns this session
- `config_id`: Which bot they're configuring (null if creating new bot)
- `builder_session_id`: Claude SDK session ID (for resumption)
- `context_type`: What they're working on (determines available tools/prompts)
- `last_active_at`: For idle timeout and cleanup
- `created_at`: Session creation timestamp
- `updated_at`: Last modification timestamp

### Rename Existing Table: `agent_sessions` → `trading_agent_sessions`

Clarify that these sessions are for trading execution only.

**Migration:**
```sql
-- Rename table
ALTER TABLE agent_sessions RENAME TO trading_agent_sessions;

-- Add comment for clarity
COMMENT ON TABLE trading_agent_sessions IS 'Session persistence for autonomous trading agents (execution only)';
```

**No schema changes needed** - existing structure is correct:
- `config_id` (PK): One trading agent per bot
- `session_id`: Claude SDK session ID
- `last_active_at`: Health monitoring
- `created_at`, `updated_at`: Timestamps

---

## 🛠️ Backend Implementation

### 1. Builder Service Architecture

**New File: `agent/builder_service.py`**

**Responsibilities:**
- Manage concurrent user chat sessions
- Route messages to correct SDK session
- Handle session creation/resumption
- Enforce idle timeout (15 min default)
- Clean up stale sessions

**Core Components:**

**Session Pool Manager**
- In-memory cache of active sessions: `Dict[user_id, (client, last_active)]`
- Idle timeout check every 5 minutes
- Lazy session creation (create on first message)
- Session resumption from database on reconnect

**Message Router**
- WebSocket handler receives `{user_id, message}`
- Lookup or create session for user
- Query SDK with user's session: `await client.query(message, session_id=user_session_id)`
- Stream responses back via WebSocket
- Update `last_active_at` on each message

**Session Lifecycle:**
1. User opens chat → WebSocket connects
2. Check database for existing `builder_session_id`
3. If found: Resume via `ClaudeAgentOptions(resume=builder_session_id)`
4. If new: Create client, capture session_id from init message, save to DB
5. User sends messages → route to their session
6. Idle >15 min → close client, keep session_id in DB
7. User returns → resume from DB

**Key Difference from Trading Agents:**
- Trading agents: One `ClaudeSDKClient` per PM2 process, resume in `ClaudeAgentOptions`
- Builder service: **One** `ClaudeSDKClient` shared, concurrent sessions via `query(session_id=...)` OR session pooling with ephemeral clients

**SDK Compatibility Note:**
Current SDK version uses `ClaudeAgentOptions(resume=session_id)`, NOT `query(session_id=...)`. If SDK doesn't support multi-session via query parameter, use **session pooling** pattern:
- Create ephemeral `ClaudeSDKClient` per active user
- Pool clients with TTL (15 min idle)
- Resume from DB when client expires

### 2. Builder MCP Tools

**New File: `agent/builder_mcp_server.py`**

**Tool Set (6 tools):**

1. **`query_market_data`** (from existing)
   - Purpose: Show available data sources for strategy building
   - Scopes: All 7 categories (educational)
   - No changes needed

2. **`get_current_price`** (from existing, OPTIONAL)
   - Purpose: Validate price ranges during config
   - Use case: "Is BTC at $100k reasonable for entry zone?"
   - Minimal changes

3. **`update_bot_config`** (NEW - expanded from `update_strategy`)
   - Purpose: Update any part of `config_data`
   - Parameters:
     - `config_id`: Which bot to update
     - `config_section`: 'agent_strategy', 'extraction', 'decision', 'trading'
     - `updates`: Dict of field changes
     - `validation`: Check if config is executable before saving
   - Validation: Ensure required fields present per config_section
   - Returns: Updated config, validation errors

4. **`validate_bot_config`** (NEW)
   - Purpose: Check if configuration is valid without saving
   - Parameters:
     - `config_type`: 'agent', 'scheduled'
     - `config_data`: Full or partial config
   - Returns: Validation results, missing fields, data availability checks

5. **`query_trade_observations`** (from existing)
   - Purpose: Review past learnings when refining strategy
   - No changes needed

6. **`get_supported_symbols`** (NEW)
   - Purpose: Show which symbols are available for trading
   - Parameters: `trading_mode` ('paper', 'aster', 'symphony')
   - Returns: List of symbols with metadata (liquidity, exchange, etc.)

**Removed from Builder:**
- ❌ `execute_trade` - Trading execution
- ❌ `get_positions` - Position monitoring
- ❌ `get_account_status` - Account balance
- ❌ `close_position` - Position closing
- ❌ `cancel_order` - Order management
- ❌ `wait_for` - Timing control (builder is request/response)
- ❌ `record_trade_observation` - Post-trade reflection (execution-time only)
- ❌ `update_strategy` - Replaced by `update_bot_config`
- ❌ `save_strategy_and_exit` - No longer needed (no mode switching)

### 3. Trading Agent MCP Tools

**Modified File: `agent/mcp_server.py`**

**Tool Set (9 tools):**

Keep all existing execution tools:
1. `query_market_data` - Strategy execution queries
2. `get_current_price` - Pre-trade validation
3. `execute_trade` - Open positions
4. `get_positions` - Check trades
5. `get_account_status` - Balance/performance
6. `close_position` - Exit positions
7. `cancel_order` - Clean up orders
8. `wait_for` - Timing control
9. `record_trade_observation` - Post-trade reflection (OPTIONAL - currently agent rarely uses this)

**Removed from Trading Agents:**
- ❌ `update_strategy` - Configuration is builder's job
- ❌ `query_trade_observations` - Reflection is builder's job
- ❌ `save_strategy_and_exit` - No mode switching

**Note:** If agents should record observations automatically, keep `record_trade_observation`. Otherwise, remove it and have users manually review trades via builder.

### 4. System Prompt Updates

**Builder Prompt** (`agent/builder_service.py`)

**Core Directives:**
- You are a trading strategy configuration assistant
- Help users build strategies for autonomous agents OR configure scheduled bots
- Show available data sources (7 categories, 32 data points)
- Validate configurations before saving
- YOU CANNOT EXECUTE TRADES - only configure bots

**Context-Specific Prompts:**

**For Agent Strategies:**
- Guide user through strategy definition (entry/exit/sizing/timing)
- Explain available tools and data sources
- Validate strategy is executable with available data
- Save to `config_data.agent_strategy`

**For Scheduled Bots:**
- Configure extraction (timeframe, indicators, data sources)
- Configure decision (LLM model, system prompt, logic)
- Configure trading (leverage, position sizing, risk management)
- Validate technical indicators are available

**Trading Agent Prompt** (`agent/run_agent.py`)

**Keep existing autonomous prompt** - No changes needed:
- Execute strategy 24/7
- Check positions, query markets, execute trades
- Use wait_for() for timing
- Record observations (if tool available)

**Remove `strategy_definition` mode entirely** - No longer used.

### 5. API Endpoints

#### Builder Service Endpoints

**New Router: `api/builder.py`**

**Endpoints:**

1. **`POST /api/v2/builder/connect`**
   - Initialize WebSocket connection for user
   - Parameters: `user_id`, `config_id` (optional)
   - Returns: WebSocket upgrade

2. **`GET /api/v2/builder/sessions`**
   - List user's active builder sessions
   - Parameters: `user_id`
   - Returns: Array of sessions with context_type, config_id, last_active

3. **`DELETE /api/v2/builder/sessions/{session_id}`**
   - Force end a builder session
   - Parameters: `session_id`
   - Returns: Success/failure

4. **`GET /api/v2/builder/health`**
   - Check builder service status
   - Returns: PM2 status, active sessions count, memory usage

#### Modified Agent Endpoints

**Modified File: `api/agent.py`**

**Changes:**

1. **Remove `mode` parameter from `/start` endpoint**
   - Agents only start in `autonomous` mode
   - Builder is separate service (always running)

2. **Update status endpoint** - Remove mode field
   - PM2 process is either running (autonomous) or not

3. **Add validation** - Prevent starting agent without strategy
   - Check `config_data.agent_strategy.content` exists
   - Return 400 if strategy not defined

---

## 🎨 Frontend Integration

### Chat Interface Changes

**Modified File: `frontend/app/forge/components/configure/AgentConfigurator.tsx`**

**Changes:**

1. **Remove "Start Strategy Builder" button**
   - Chat is always available (builder service always running)
   - WebSocket connects on component mount

2. **Add WebSocket connection**
   - Connect to `wss://api.ggbots.ai/v2/builder/connect`
   - Send user messages: `{user_id, config_id, message}`
   - Stream builder responses in real-time

3. **Keep strategy editing UI** (already implemented)
   - Two-column layout (chat left, strategy right)
   - Debounced auto-save (1s delay)
   - SSE updates from builder when strategy changes

**Connection Flow:**
1. User navigates to Configure page
2. WebSocket connects to builder service
3. Builder loads or creates session for user
4. User types message → sent via WebSocket
5. Builder streams response → displayed in chat
6. Builder calls `update_bot_config` → strategy updates → SSE → frontend refreshes

### Activation Flow Changes

**Modified File: `frontend/app/forge/page.tsx`**

**Changes:**

1. **"Activate Agent" button validation**
   - Check if `agent_strategy.content` exists before allowing activation
   - Show error if strategy undefined: "Please define a strategy first"

2. **Remove mode selection**
   - "Activate" always starts in `autonomous` mode
   - No builder mode option (builder is separate service)

3. **Status display**
   - Show "Builder Available" badge (always online)
   - Show "Agent Running" badge (only when autonomous PM2 active)

---

## 🧹 Cleanup of Existing Agent

### Files to Modify

#### `agent/run_agent.py`

**Removals:**

1. **Remove mode parameter** (lines 66-73, 393-540)
   - Delete `--mode` CLI argument
   - Delete `self.mode` attribute
   - Delete `_run_strategy_definition()` method
   - Delete mode routing logic

2. **Remove builder tools** (lines 352-369)
   - Remove from `allowed_tools`: `update_strategy`, `query_trade_observations`, `save_strategy_and_exit`
   - Keep execution tools only

3. **Remove mode-specific system prompts** (lines 216-262)
   - Delete "MODE-SPECIFIC BEHAVIOR" section
   - Keep only autonomous execution prompt

4. **Simplify initialization**
   - Always load session from `trading_agent_sessions` table
   - No mode checks

**Additions:**

1. **Rename session table reference**
   - Change `agent_sessions` → `trading_agent_sessions` in SQL queries

2. **Add strategy validation on startup**
   - Check `config_data.agent_strategy.content` exists
   - Exit with clear error if missing strategy

#### `agent/mcp_server.py`

**Removals:**

1. **Delete builder-specific tools:**
   - `update_strategy` (lines 890-955)
   - `save_strategy_and_exit` (lines 1194-1291)

2. **Update tool registration** (lines 1323-1339)
   - Remove deleted tools from registration list
   - Update count from 12 → 9 tools

**Modifications:**

1. **Make `record_trade_observation` OPTIONAL**
   - Add note in docstring: "Typically used in post-trade analysis via builder, not during execution"
   - Consider removing if agents don't use it autonomously

#### `api/agent.py`

**Removals:**

1. **Remove mode parameter from start endpoint** (lines 1051-1123)
   - Remove `mode: str = Query(...)` parameter
   - Always start with `--mode autonomous` hardcoded

2. **Remove mode from status endpoint** (lines 1266-1334)
   - Delete mode parsing from PM2 args
   - Remove mode field from response

**Additions:**

1. **Add strategy validation in start endpoint**
   - Query `config_data.agent_strategy.content` before starting
   - Raise 400 error if strategy missing:
     ```
     "Cannot start agent: Strategy not defined. Please configure strategy via Strategy Builder first."
     ```

2. **Update PM2 command** (line 1096)
   - Remove `--mode` flag entirely
   - Simplify to: `pm2 start agent/run_agent.py --name agent-{config_id} -- --config-id {config_id}`

### Files to Delete

None - all existing files are reused.

### Files to Create

1. **`agent/builder_service.py`** - Main builder service
2. **`agent/builder_mcp_server.py`** - Builder tool definitions
3. **`api/builder.py`** - Builder API endpoints
4. **`scripts/migrations/add_builder_sessions_table.sql`** - Database migration

---

## 🔄 Migration Plan

### Phase 1: Create Builder Service (No Breaking Changes)

**Goal:** Deploy builder alongside existing agent, test with new bots.

**Steps:**

1. **Database Migration**
   - Create `strategy_builder_sessions` table
   - Rename `agent_sessions` → `trading_agent_sessions`
   - Migration is backward-compatible (existing agents unaffected)

2. **Implement Builder Service**
   - Create `agent/builder_service.py`
   - Create `agent/builder_mcp_server.py` (6 tools)
   - Create `api/builder.py` (WebSocket endpoints)
   - Start as PM2 service: `pm2 start agent/builder_service.py --name strategy-builder`

3. **Update Frontend**
   - Add WebSocket connection to builder
   - Keep existing UI (already has chat + strategy editing)
   - Feature flag: `ENABLE_BUILDER_SERVICE` (default: false)

4. **Testing**
   - Test builder with new bot configurations
   - Verify WebSocket streaming works
   - Confirm session persistence across reconnects
   - Validate concurrent users don't interfere

### Phase 2: Clean Up Existing Agent (Breaking Change)

**Goal:** Remove mode switching from trading agents.

**Prerequisites:**
- Phase 1 deployed and stable
- All users migrated to builder service for strategy creation
- Feature flag enabled for all users

**Steps:**

1. **Modify Trading Agents**
   - Remove mode parameter from `run_agent.py`
   - Remove builder tools from `mcp_server.py`
   - Update system prompt (remove mode-specific sections)
   - Add strategy validation on startup

2. **Update API Endpoints**
   - Remove mode from `/start` and `/status`
   - Add strategy validation in `/start`

3. **Update Frontend**
   - Remove "Start Strategy Builder" button
   - Update activation flow (validate strategy exists)
   - Update status badges

4. **Communication**
   - Notify users: "Strategy Builder is now always available - no need to start/stop"
   - Update documentation in `agent/README.md`

5. **Deployment**
   - Deploy frontend changes
   - Deploy backend changes
   - Restart existing agent PM2 processes (will pick up new code)

### Phase 3: Expand Builder Scope (Enhancement)

**Goal:** Enable builder to configure scheduled bots.

**Steps:**

1. **Add scheduled bot tools**
   - `update_bot_config` supports `extraction`, `decision`, `trading` sections
   - `validate_bot_config` checks scheduled bot requirements

2. **Update builder system prompt**
   - Add guidance for configuring scheduled bots
   - Explain difference between agent vs scheduled configs

3. **Frontend Integration**
   - Enable builder chat for scheduled bot configuration pages
   - Add context detection (agent vs scheduled)

---

## 🧪 Testing Strategy

### Unit Tests

**Builder Service:**
- Session creation and resumption
- Message routing to correct session
- Idle timeout cleanup
- Concurrent session handling

**Builder Tools:**
- `update_bot_config` validation
- `validate_bot_config` for agent/scheduled configs
- `get_supported_symbols` for different trading modes

**Trading Agent:**
- Startup validation (strategy exists check)
- Tool set only includes execution tools

### Integration Tests

**Builder Chat Flow:**
1. User connects via WebSocket
2. Builder creates session, returns session_id
3. User sends message: "Help me build a BTC strategy"
4. Builder responds with guidance
5. User disconnects
6. User reconnects → session resumes

**Concurrent Users:**
1. Start 5 concurrent WebSocket connections (different users)
2. Each user sends messages simultaneously
3. Verify responses are routed correctly (no cross-contamination)
4. Check session pool cleanup after idle timeout

**Strategy Definition → Activation:**
1. User chats with builder about strategy
2. Builder calls `update_bot_config` to save strategy
3. Frontend receives SSE update, displays strategy
4. User clicks "Activate"
5. Trading agent starts, validates strategy exists
6. Agent executes trades based on strategy

### Load Testing

**Builder Service Capacity:**
- Test 50 concurrent users chatting
- Measure: Response latency, memory usage, CPU usage
- Target: <500ms response time, <2GB memory

**Session Pool Management:**
- Create 100 sessions, let 90% go idle
- Verify idle sessions cleaned up after timeout
- Verify active sessions unaffected

### Edge Cases

**Builder Service:**
- User disconnects mid-response → session preserved, resumes on reconnect
- Builder crashes → PM2 restarts, sessions resume from DB
- Database unavailable → graceful degradation (in-memory sessions only)

**Trading Agent:**
- Start without strategy defined → clear error message
- Strategy updated while agent running → agent continues with old strategy (restart required)

---

## ❓ Open Questions

### 1. SDK Multi-Session Support

**Question:** Does current Python SDK support `query(session_id=...)` for multiple concurrent sessions in one client?

**Research Needed:**
- Check SDK documentation for multi-session patterns
- Test if `ClaudeSDKClient` can handle concurrent sessions
- If not supported, use session pooling pattern (ephemeral clients with TTL)

**Decision Impact:**
- If YES: Single client instance, simpler architecture
- If NO: Session pooling with ephemeral clients (more complex, but proven pattern per Anthropic docs)

### 2. Session Expiration Policy

**Question:** How long should builder sessions stay alive in database?

**Options:**
- **Option A**: Keep forever (sessions are cheap, users can resume anytime)
- **Option B**: Delete after 30 days inactive
- **Option C**: Delete after 7 days inactive

**Considerations:**
- Anthropic docs don't specify session expiration guarantees
- Users may return to strategy building after weeks
- Session IDs are small (VARCHAR), storage cost negligible

**Recommendation:** Keep forever, add manual cleanup endpoint if needed.

### 3. Builder Service Scaling

**Question:** When do we need multiple builder service instances?

**Considerations:**
- Single instance handles N concurrent users
- Anthropic rate limits: RPM, ITPM, OTPM per API key
- Session state is in SDK/Anthropic backend (horizontally scalable)

**Decision Criteria:**
- If concurrent users > 100: Consider horizontal scaling
- If API rate limits hit: Add load balancing across multiple API keys

**Current Scope:** Single instance sufficient for MVP.

### 4. Should Trading Agents Record Observations?

**Question:** Should `record_trade_observation` stay in trading agent tools?

**Arguments FOR:**
- Agent can reflect immediately after closing trades (fresh context)
- Automatic documentation of learnings

**Arguments AGAINST:**
- Agents rarely use this tool currently (adds token cost)
- Users can manually review trades via builder chat
- Cleaner separation: Builder = reflection, Agent = execution

**Recommendation:** Remove from trading agents, keep observation querying in builder. Users discuss trades with builder post-execution.

### 5. Builder Access Control

**Question:** Should builder have access to other users' bots?

**Current Design:** Builder can only access `user_id`'s own configurations.

**Future Consideration:**
- Team accounts: Multiple users collaborate on same bot
- Public strategies: Users share strategies with community
- Admin tools: Support team helps debug user configs

**Current Scope:** User can only configure their own bots.

---

## 📚 References

### Existing Documentation
- `agent/README.md` - Current agent usage guide
- `DOCS/completed/agent-session-resumption-implementation.md` - Session persistence
- Anthropic SDK docs (CONTEXT.md) - Multi-session patterns

### Related Issues
- Agent mode switching confusion (current problem)
- Resource waste with per-user PM2 services (current problem)
- Limited builder scope (current limitation)

### External Resources
- Anthropic Agent SDK - Session resumption: https://docs.claude.com/en/api/agent-sdk/sessions
- Anthropic Agent SDK - Hosting patterns: https://docs.claude.com/en/api/agent-sdk/hosting

---

## 🎯 Success Metrics

### Phase 1 Success Criteria
- [ ] Builder service handles 10+ concurrent users without errors
- [ ] Session resumption works across reconnects
- [ ] Tool calls (update_bot_config) successfully save to database
- [ ] Frontend chat interface streams responses in <500ms
- [ ] Zero cross-user session contamination in testing

### Phase 2 Success Criteria
- [ ] All existing agents start without mode parameter
- [ ] Strategy validation prevents activation without defined strategy
- [ ] Frontend shows "Builder Always Available" status
- [ ] Zero user complaints about mode switching removal

### Phase 3 Success Criteria
- [ ] Builder successfully configures scheduled bots
- [ ] Validation prevents invalid extraction/decision/trading configs
- [ ] Users can switch between agent and scheduled configs in chat

### Overall Success
- **Builder availability**: 99.9% uptime (monitored via PM2 + health checks)
- **User satisfaction**: Simplified UX, no mode switching confusion
- **Resource efficiency**: 90% reduction in PM2 services (one builder vs N per user)
- **Expanded utility**: Builder helps with both agent and scheduled configs
