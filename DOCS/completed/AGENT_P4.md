# Agent Phase 4: Frontend Integration & Activity Timeline

**Status**: Planning Complete - Ready for Implementation
**Timeline**: 2-3 weeks
**Prerequisites**: Phase 3 Complete (11 tools operational, autonomous mode working)

---

## Executive Summary

Transform the agent experience with integrated UI for strategy definition and rich activity visualization. Two major components:

1. **AgentConfigurator**: Two-column chat interface for strategy definition mode embedded in Forge Configure tab
2. **Activity Timeline**: Real-time visualization of agent's market analysis, reasoning, and trading actions

**Key Architecture Decisions**:
- ✅ Tool-based activity logging (new `log_activity` tool + auto-logging from existing tools)
- ✅ Unified `agent_activities` table for all timeline events
- ✅ Config type integration in Forge (Scheduled Trading | Signal Validation | Agentic)
- ✅ Local state design (no Zustand), SSE + Redis polling for real-time updates
- ✅ Activity Timeline as universal visualization (will eventually replace Monitor tab)

---

## Architecture Overview

### Activity Logging System

**Philosophy**: Agent explicitly logs important activities via tools, creating structured timeline events.

#### New Tool: `log_activity`

```python
@tool(
    "log_activity",
    """Log your reasoning, analysis, or important thoughts for the activity timeline.

    Use this to document your decision-making process, market analysis insights,
    or strategic observations that users should see on the timeline.

    Activity types:
    - "analysis": Market analysis and interpretation
    - "reasoning": Decision-making logic and rationale
    - "observation": General observations or insights
    - "plan": Strategic planning or next steps
    """,
    {
        "activity_type": str,  # "analysis" | "reasoning" | "observation" | "plan"
        "summary": str,        # Brief title (50 chars max)
        "details": str,        # Full explanation (markdown supported)
        "related_symbol": str, # Optional symbol context
        "importance": int      # 1-10 for prioritization/filtering
    }
)
async def log_activity(args: dict[str, Any]) -> dict[str, Any]:
    """Agent explicitly logs activity for timeline visibility"""
```

#### Auto-Logging from Existing Tools

```python
# Automatic activity logging (transparent to agent)

query_market_data() → activity_type='market_query'
  - summary: "Queried BTC: RSI, MACD, Stochastic + macro data"
  - details: Full technical indicators + market intelligence response

execute_trade() → activity_type='trade_entry_long' | 'trade_entry_short'
  - summary: "Opened long BTC/USDT at $110,229"
  - details: {size_usd, leverage, sl, tp, reasoning}
  - related_trade_id: <trade_id>

close_position() → activity_type='trade_exit'
  - summary: "Closed BTC/USDT position: +$45.20 (+3.8%)"
  - details: {exit_price, pnl, duration, close_reason}
  - related_trade_id: <trade_id>

wait_for() → activity_type='agent_wait'
  - summary: "Waiting 90 minutes for signal convergence"
  - details: {duration_minutes, reason, next_check_at}

record_trade_observation() → activity_type='observation_recorded'
  - summary: "Trade observation: Loss analysis"
  - details: {what_went_well, what_went_wrong, predictive_data_points}

update_strategy() → activity_type='strategy_updated'
  - summary: "Strategy updated to v3"
  - details: {old_version, new_version, reason, performance_summary}
```

### Database Schema

#### New Table: `agent_activities`

```sql
CREATE TABLE agent_activities (
    activity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID NOT NULL REFERENCES configurations(config_id),
    user_id UUID NOT NULL,

    -- Activity classification
    activity_type TEXT NOT NULL,
    -- Values: 'market_query', 'trade_entry_long', 'trade_entry_short', 'trade_exit',
    --         'agent_wait', 'analysis', 'reasoning', 'observation', 'plan',
    --         'observation_recorded', 'strategy_updated', 'position_adjusted'

    activity_source TEXT NOT NULL, -- 'tool_call', 'agent_log', 'system_event'

    -- Content
    summary TEXT NOT NULL,         -- Brief title (timeline label, 50 chars)
    details JSONB NOT NULL,        -- Full structured data

    -- Context
    related_symbol TEXT,           -- Optional symbol context (e.g., "BTC/USDT")
    related_trade_id UUID,         -- Link to paper_trades if applicable
    related_decision_id UUID,      -- Link to decisions if applicable

    -- Metadata
    importance INT DEFAULT 5 CHECK (importance BETWEEN 1 AND 10),
    priority INT DEFAULT 2 CHECK (priority IN (1,2,3)),
    -- Priority mapping: 1=high (trades, critical), 2=medium (analysis, queries), 3=low (observations, waits)

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    INDEX idx_agent_activities_config (config_id, created_at DESC),
    INDEX idx_agent_activities_type (config_id, activity_type, created_at DESC),
    INDEX idx_agent_activities_importance (config_id, importance DESC, created_at DESC),
    INDEX idx_agent_activities_priority (config_id, priority, created_at DESC)
);

-- RLS policy
ALTER TABLE agent_activities ENABLE ROW LEVEL SECURITY;

CREATE POLICY agent_activities_user_isolation ON agent_activities
    FOR ALL USING (user_id = auth.uid());
```

#### Activity Type → Priority Mapping

```typescript
const ACTIVITY_PRIORITY: Record<ActivityType, Priority> = {
  // Priority 1 (High) - Trades and critical actions
  trade_entry_long: 1,
  trade_entry_short: 1,
  trade_exit: 1,
  position_adjusted: 1,
  strategy_updated: 1,

  // Priority 2 (Medium) - Analysis and decisions
  market_query: 2,
  analysis: 2,
  reasoning: 2,
  decision_made: 2,

  // Priority 3 (Low) - Background activities
  agent_wait: 3,
  observation: 3,
  observation_recorded: 3,
  plan: 3,
}
```

---

## Phase 4a: Configure Tab Integration (Week 1-2)

### Goal: Add "Agentic" config type with chat interface for strategy definition

### Implementation Tasks

#### Task 1: Config Type Selection Redesign

**File**: `frontend/app/forge/components/configure/SaveConfigBar.tsx`

**Changes**:
```typescript
// Replace binary toggle with 3-button selector
const CONFIG_TYPES = [
  {
    value: 'scheduled_trading',
    label: 'Scheduled Trading',
    description: 'Automated trading on fixed schedule',
    icon: '⏰',
    permission: null // Free tier
  },
  {
    value: 'signal_validation',
    label: 'Signal Validation',
    description: 'Validate external signals with AI',
    icon: '✓',
    permission: 'signal_validation' // Paid tier
  },
  {
    value: 'agentic',
    label: 'Agentic',
    description: 'Autonomous AI agent with conversation',
    icon: '🤖',
    permission: 'agentic' // Whitelisted only (for now)
  }
]

// Permission gating logic
const { canAccess } = usePermissions()
const whitelistUserId = process.env.NEXT_PUBLIC_WHITELIST_USER_ID

const isAllowed = (permission: string | null) => {
  if (!permission) return true // Free tier
  if (permission === 'agentic') {
    return userProfile?.user_id === whitelistUserId
  }
  return canAccess(permission)
}

// UI: Three buttons with lock icons
{CONFIG_TYPES.map(type => {
  const allowed = isAllowed(type.permission)
  return (
    <button
      key={type.value}
      disabled={!allowed}
      className={cn(
        "px-4 py-2 rounded-lg border transition-all",
        configType === type.value
          ? "bg-emerald-500 text-white border-emerald-500"
          : "border-bone-300 dark:border-charcoal-600",
        !allowed && "opacity-50 cursor-not-allowed"
      )}
      onClick={() => setConfigType(type.value)}
    >
      <span className="text-lg mr-2">{type.icon}</span>
      {type.label}
      {!allowed && <LockIcon className="ml-2" />}
    </button>
  )
})}
```

**Checklist**:
- [ ] Replace toggle with 3-button selector
- [ ] Add permission checks (free/paid/whitelisted)
- [ ] Show lock icon + tooltip for disabled options
- [ ] Update state management at page level
- [ ] Test permission gates with different user tiers

---

#### Task 2: AgentConfigurator Component

**File**: `frontend/app/forge/components/configure/AgentConfigurator.tsx`

**Architecture**: Two-column layout
- **Left**: Chat interface (messages, input, send button)
- **Right**: Strategy display (empty until confirmed)

**Component Structure**:
```typescript
export default function AgentConfigurator({
  configId,
  isActive,
  currentStrategy
}: AgentConfiguratorProps) {

  // State
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false)
  const [isStrategyConfirmed, setIsStrategyConfirmed] = useState(false)
  const [showConfirmButton, setShowConfirmButton] = useState(false)

  // Redis polling for agent responses
  useEffect(() => {
    if (!configId || isActive) return

    const pollInterval = setInterval(async () => {
      const response = await fetch(`/api/v2/agent/${configId}/poll-response`)
      if (response.ok) {
        const data = await response.json()
        if (data.message) {
          setMessages(prev => [...prev, {
            role: 'agent',
            content: data.message,
            timestamp: new Date().toISOString()
          }])
          setIsWaitingForResponse(false)

          // Detect confirmation request
          if (data.message.includes('Proceed with this strategy?')) {
            setShowConfirmButton(true)
          }
        }
      }
    }, 2000) // Poll every 2 seconds

    return () => clearInterval(pollInterval)
  }, [configId, isActive])

  // Send message
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isWaitingForResponse) return

    // Add user message
    setMessages(prev => [...prev, {
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    }])

    // Push to Redis queue
    await fetch(`/api/v2/agent/${configId}/message`, {
      method: 'POST',
      body: JSON.stringify({ message: inputValue })
    })

    setInputValue('')
    setIsWaitingForResponse(true)
  }

  // Confirm strategy
  const handleConfirmStrategy = async () => {
    await handleSendMessage() // Send "1" or confirmation
    setShowConfirmButton(false)
    setIsStrategyConfirmed(true)
    // Wait for strategy to populate from backend
  }

  return (
    <div className="grid grid-cols-2 gap-6 h-[600px]">
      {/* Left Column: Chat Interface */}
      <div className="flex flex-col border rounded-xl overflow-hidden">
        {/* Chat header */}
        <div className="px-4 py-3 border-b bg-charcoal-800">
          <div className="flex items-center gap-2">
            <div className="text-xl">🤖</div>
            <div>
              <div className="font-medium">Strategy Definition</div>
              <div className="text-xs text-bone-400">
                {isStrategyConfirmed ? 'Strategy Confirmed' : 'Conversation Mode'}
              </div>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <EmptyState
              icon="💬"
              title="Start Strategy Discussion"
              description="Chat with the agent to define your trading strategy"
            />
          )}
          {messages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} />
          ))}
          {isWaitingForResponse && <TypingIndicator />}
        </div>

        {/* Input area */}
        {!isStrategyConfirmed && (
          <div className="p-4 border-t">
            {showConfirmButton ? (
              <button
                onClick={handleConfirmStrategy}
                className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium"
              >
                ✓ Confirm Strategy
              </button>
            ) : (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Type your message..."
                  className="flex-1 px-4 py-2 rounded-lg border"
                  disabled={isWaitingForResponse}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isWaitingForResponse}
                  className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg disabled:opacity-50"
                >
                  Send
                </button>
              </div>
            )}
          </div>
        )}

        {isStrategyConfirmed && (
          <div className="p-4 border-t bg-emerald-500/10">
            <div className="text-sm text-emerald-600 dark:text-emerald-400">
              ✓ Strategy confirmed. Activate the agent to begin autonomous trading.
            </div>
          </div>
        )}
      </div>

      {/* Right Column: Strategy Display */}
      <div className="border rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b bg-charcoal-800">
          <div className="font-medium">Strategy</div>
        </div>

        <div className="p-4 overflow-y-auto h-[calc(600px-57px)]">
          {!currentStrategy ? (
            <EmptyState
              icon="📋"
              title="No Strategy Yet"
              description="Strategy will appear here after confirmation"
            />
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown>{currentStrategy.content}</ReactMarkdown>

              <div className="mt-4 pt-4 border-t text-xs text-bone-500">
                <div>Version: {currentStrategy.version}</div>
                <div>Last updated: {new Date(currentStrategy.last_updated_at).toLocaleString()}</div>
                <div>Autonomously editable: {currentStrategy.autonomously_editable ? 'Yes' : 'No'}</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
```

**Sub-components**:

```typescript
// MessageBubble.tsx
function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div className={cn(
        "max-w-[80%] px-4 py-2 rounded-lg",
        isUser
          ? "bg-emerald-500 text-white"
          : "bg-charcoal-700 text-bone-200"
      )}>
        <div className="whitespace-pre-wrap">{message.content}</div>
        <div className="text-xs opacity-60 mt-1">
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}

// TypingIndicator.tsx
function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 text-bone-500">
      <div className="flex gap-1">
        <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{animationDelay: '0ms'}} />
        <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{animationDelay: '150ms'}} />
        <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{animationDelay: '300ms'}} />
      </div>
      <span className="text-sm">Agent is thinking...</span>
    </div>
  )
}
```

**Checklist**:
- [ ] Create AgentConfigurator.tsx component
- [ ] Build chat message list with scroll-to-bottom
- [ ] Implement Redis polling for agent responses
- [ ] Add message sending functionality
- [ ] Detect confirmation prompt and show confirm button
- [ ] Handle strategy confirmation flow
- [ ] Build strategy display with markdown rendering
- [ ] Add empty states for both columns
- [ ] Style message bubbles (user vs agent)
- [ ] Add typing indicator
- [ ] Test bidirectional messaging

---

#### Task 3: Strategy Editing Flow

**Feature**: "Begin Strategy Discussion" button for re-entering strategy definition mode

**Location**: Inside AgentConfigurator component (top-right of left column)

```typescript
// Add to AgentConfigurator component
const [showEditWarning, setShowEditWarning] = useState(false)

const handleBeginStrategyDiscussion = () => {
  if (isActive) {
    setShowEditWarning(true)
  } else {
    startNewConversation()
  }
}

const startNewConversation = async () => {
  // Clear messages
  setMessages([])
  setIsStrategyConfirmed(false)
  setShowConfirmButton(false)

  // Start agent in strategy_definition mode
  await fetch(`/api/v2/agent/${configId}/start`, {
    method: 'POST',
    body: JSON.stringify({ mode: 'strategy_definition' })
  })
}

// UI: Button in header (only when strategy exists)
{currentStrategy && (
  <button
    onClick={handleBeginStrategyDiscussion}
    disabled={isActive}
    className="px-3 py-1 text-sm border rounded-lg hover:bg-charcoal-700 disabled:opacity-50"
    title={isActive ? "Deactivate agent to edit strategy" : "Edit strategy"}
  >
    {isActive ? '🔒 Edit Strategy' : '✏️ Begin Strategy Discussion'}
  </button>
)}

// Warning modal
<Dialog open={showEditWarning} onOpenChange={setShowEditWarning}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Deactivate Agent to Edit Strategy</DialogTitle>
      <DialogDescription>
        Deactivating the agent will cause it to lose its current session context.
        The agent will need to rebuild its understanding of the market when reactivated.
      </DialogDescription>
    </DialogHeader>
    <DialogFooter>
      <button onClick={() => setShowEditWarning(false)}>Cancel</button>
      <button
        onClick={async () => {
          await fetch(`/api/v2/agent/${configId}/stop`, { method: 'POST' })
          setShowEditWarning(false)
          startNewConversation()
        }}
        className="bg-red-500 hover:bg-red-600 text-white"
      >
        Deactivate & Edit
      </button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

**Checklist**:
- [ ] Add "Begin Strategy Discussion" button
- [ ] Only enable when agent is inactive
- [ ] Show warning modal when active
- [ ] Implement deactivation flow
- [ ] Clear chat history and restart conversation
- [ ] Test full flow: activate → deactivate → edit → reactivate

---

#### Task 4: Configure Tab Container Logic

**File**: `frontend/app/forge/page.tsx`

**State Management**:
```typescript
// Add config_type to page state
const [configType, setConfigType] = useState<'scheduled_trading' | 'signal_validation' | 'agentic'>('scheduled_trading')

// Update when loading config
useEffect(() => {
  if (editingConfig) {
    setConfigType(editingConfig.config_type || 'scheduled_trading')
  }
}, [editingConfig])

// Conditional rendering in Configure tab
{activeTab === 'configure' && (
  <div className="space-y-6">
    <SaveConfigBar
      configType={configType}
      onConfigTypeChange={setConfigType}
      {...otherProps}
    />

    {configType === 'agentic' ? (
      <AgentConfigurator
        configId={selectedConfigId}
        isActive={selectedBot?.state === 'active'}
        currentStrategy={editingConfig?.agent_strategy}
      />
    ) : configType === 'signal_validation' ? (
      <SignalValidationComponents />
    ) : (
      <>
        <ConfigTabs />
        {configTab === 'market_data' && <MarketDataSelector />}
        {configTab === 'signals' && <SignalsConfiguration />}
        {configTab === 'strategy' && <StrategyEditor />}
        {configTab === 'trade_settings' && <TradeSettings />}
      </>
    )}
  </div>
)}
```

**Checklist**:
- [ ] Add configType state to page level
- [ ] Update state when loading existing config
- [ ] Conditional rendering based on config_type
- [ ] Hide ConfigTabs when config_type='agentic'
- [ ] Show only AgentConfigurator for agentic type
- [ ] Test switching between config types
- [ ] Ensure state persistence when switching bots

---

#### Task 5: Backend API Endpoints

**New Endpoints in `ggbot.py` or `api/agent.py`**:

```python
@router.post("/api/v2/agent/{config_id}/start")
async def start_agent(
    config_id: str,
    mode: str = Query(..., description="strategy_definition | autonomous")
):
    """Start agent process via PM2"""
    # Check if already running
    pm2_list = subprocess.run(['pm2', 'jlist'], capture_output=True, text=True)
    processes = json.loads(pm2_list.stdout)

    agent_name = f"agent-{config_id}"
    existing = next((p for p in processes if p['name'] == agent_name), None)

    if existing and existing['pm2_env']['status'] == 'online':
        return {"status": "already_running", "message": "Agent is already active"}

    # Start via PM2
    cmd = [
        'pm2', 'start',
        'agent/run_agent.py',
        '--name', agent_name,
        '--interpreter', '.venv-agent/bin/python',
        '--',
        '--config-id', config_id,
        '--mode', mode
    ]

    subprocess.run(cmd, cwd='/home/sev/ggbot')

    return {"status": "started", "config_id": config_id, "mode": mode}


@router.post("/api/v2/agent/{config_id}/stop")
async def stop_agent(config_id: str):
    """Stop agent process gracefully"""
    agent_name = f"agent-{config_id}"
    subprocess.run(['pm2', 'stop', agent_name])
    subprocess.run(['pm2', 'delete', agent_name])

    # Clear Redis queues
    redis_client.delete(f"agent:{config_id}:messages")
    redis_client.delete(f"agent:{config_id}:responses")

    return {"status": "stopped", "config_id": config_id}


@router.post("/api/v2/agent/{config_id}/message")
async def send_message_to_agent(
    config_id: str,
    body: dict
):
    """Push message to Redis queue for agent"""
    message = body.get('message')
    if not message:
        raise HTTPException(400, "Message required")

    redis_client.lpush(f"agent:{config_id}:messages", message)

    return {"status": "sent", "message": message}


@router.get("/api/v2/agent/{config_id}/poll-response")
async def poll_agent_response(config_id: str):
    """Poll for agent response from Redis queue"""
    # Non-blocking pop
    response = redis_client.rpop(f"agent:{config_id}:responses")

    if response:
        return {"status": "success", "message": response.decode('utf-8')}
    else:
        return {"status": "no_message"}


@router.get("/api/v2/agent/{config_id}/status")
async def get_agent_status(config_id: str):
    """Get current agent status"""
    agent_name = f"agent-{config_id}"

    pm2_list = subprocess.run(['pm2', 'jlist'], capture_output=True, text=True)
    processes = json.loads(pm2_list.stdout)

    agent = next((p for p in processes if p['name'] == agent_name), None)

    if not agent:
        return {
            "status": "inactive",
            "mode": None,
            "uptime": None
        }

    return {
        "status": agent['pm2_env']['status'],
        "mode": agent['pm2_env'].get('AGENT_MODE'),
        "uptime": agent['pm2_env']['pm_uptime'],
        "restarts": agent['pm2_env']['restart_time']
    }
```

**Checklist**:
- [ ] Implement POST /agent/{config_id}/start
- [ ] Implement POST /agent/{config_id}/stop
- [ ] Implement POST /agent/{config_id}/message
- [ ] Implement GET /agent/{config_id}/poll-response
- [ ] Implement GET /agent/{config_id}/status
- [ ] Add PM2 process management
- [ ] Test with actual PM2 commands
- [ ] Handle edge cases (already running, failed start, etc.)

---

#### Task 6: ActivationBar Integration for Agentic Mode

**File**: `frontend/app/forge/components/monitor/ActivationBar.tsx`

**Changes**:
```typescript
// Detect agentic config type
const isAgenticBot = selectedBot?.config_type === 'agentic'

// Different activation messaging
const activationLabel = isAgenticBot
  ? (isActive ? 'Deactivate Agent' : 'Activate Agent')
  : (isActive ? 'Deactivate Bot' : 'Activate Bot')

const activationMessage = isAgenticBot
  ? 'Agent will start autonomous trading based on your strategy'
  : 'Bot will run on schedule based on your timeframe settings'

// Activation handler
const handleActivate = async () => {
  if (isAgenticBot) {
    if (isActive) {
      // Show context loss warning
      if (!confirm('Deactivating will cause the agent to lose current session context. Continue?')) {
        return
      }
      await apiClient.stopAgent(selectedConfigId)
    } else {
      // Start in autonomous mode
      await apiClient.startAgent(selectedConfigId, 'autonomous')
    }
  } else {
    // Normal bot activation (existing logic)
    await apiClient.toggleBotActivation(selectedConfigId)
  }
}

// Agent status display (when active)
{isActive && isAgenticBot && agentStatus && (
  <div className="ml-4 flex items-center gap-2 text-sm">
    <StatusIndicator status={agentStatus.status} />
    <span className="text-bone-400">
      {agentStatus.status === 'waiting'
        ? `Next check in ${agentStatus.next_check_in}`
        : agentStatus.current_activity || 'Running'}
    </span>
  </div>
)}
```

**Checklist**:
- [ ] Detect agentic config type
- [ ] Update activation button label
- [ ] Show context loss warning on deactivation
- [ ] Call agent start/stop endpoints
- [ ] Display agent status (running/waiting/analyzing)
- [ ] Add countdown timer for "waiting" status
- [ ] Test activation/deactivation flow

---

## Phase 4b: Activity Timeline Integration (Week 2-3)

### Goal: Connect ActivityTimelineViewer to real agent activity data

### Implementation Tasks

#### Task 7: Agent Activity Logging Infrastructure

**Database Migration**:
```sql
-- Create agent_activities table (see schema above)
-- Run migration: database/migrations/create_agent_activities.sql
```

**MCP Server Updates** (`agent/mcp_server.py`):

```python
# Add new tool: log_activity (see spec above)

# Update existing tools to auto-log activities:

@tool("query_market_data", ...)
async def query_market_data(args: dict[str, Any]) -> dict[str, Any]:
    result = await agent_context.api_client.query_market_data(...)

    # Auto-log activity
    await log_to_activities(
        activity_type='market_query',
        activity_source='tool_call',
        summary=f"Queried {args['symbol']}: {len(args.get('categories', {}))} categories",
        details=result,
        related_symbol=args['symbol'],
        priority=2,
        importance=6
    )

    return result

@tool("execute_trade", ...)
async def execute_trade(args: dict[str, Any]) -> dict[str, Any]:
    result = await agent_context.api_client.execute_trade(...)

    # Auto-log activity
    await log_to_activities(
        activity_type=f"trade_entry_{args['side']}",
        activity_source='tool_call',
        summary=f"Opened {args['side']} {args['symbol']} at ${args['entry_price']}",
        details={
            'size_usd': args['size_usd'],
            'leverage': args.get('leverage', 1),
            'stop_loss': args['stop_loss_price'],
            'take_profit': args['take_profit_price'],
            'confidence': args.get('confidence', 0.7)
        },
        related_symbol=args['symbol'],
        related_trade_id=result['trade_id'],
        priority=1,
        importance=9
    )

    return result

# Similar updates for: close_position, wait_for, record_trade_observation, update_strategy
```

**Helper Function**:
```python
async def log_to_activities(
    activity_type: str,
    activity_source: str,
    summary: str,
    details: dict,
    related_symbol: str = None,
    related_trade_id: str = None,
    related_decision_id: str = None,
    priority: int = 2,
    importance: int = 5
):
    """Log activity to agent_activities table"""
    await db.execute("""
        INSERT INTO agent_activities
        (config_id, user_id, activity_type, activity_source, summary, details,
         related_symbol, related_trade_id, related_decision_id, priority, importance)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        agent_context.config_id,
        agent_context.user_id,
        activity_type,
        activity_source,
        summary,
        json.dumps(details),
        related_symbol,
        related_trade_id,
        related_decision_id,
        priority,
        importance
    ))
```

**Checklist**:
- [ ] Run database migration for agent_activities table
- [ ] Add log_activity tool to MCP server
- [ ] Create log_to_activities helper function
- [ ] Update query_market_data to auto-log
- [ ] Update execute_trade to auto-log
- [ ] Update close_position to auto-log
- [ ] Update wait_for to auto-log
- [ ] Update record_trade_observation to auto-log
- [ ] Update update_strategy to auto-log
- [ ] Test activity logging with real agent
- [ ] Verify activities appear in database

---

#### Task 8: Activity Timeline API Endpoints

**New Endpoints in `ggbot.py` or `api/agent.py`**:

```python
@router.get("/api/v2/agent/{config_id}/activities")
async def get_agent_activities(
    config_id: str,
    start_time: str = Query(None),
    end_time: str = Query(None),
    activity_types: list[str] = Query(None),
    min_importance: int = Query(1),
    limit: int = Query(500)
):
    """Get all activities for timeline visualization"""

    query = """
        SELECT
            activity_id, activity_type, activity_source, summary, details,
            related_symbol, related_trade_id, related_decision_id,
            priority, importance, created_at
        FROM agent_activities
        WHERE config_id = %s
    """
    params = [config_id]

    if start_time:
        query += " AND created_at >= %s"
        params.append(start_time)

    if end_time:
        query += " AND created_at <= %s"
        params.append(end_time)

    if activity_types:
        query += " AND activity_type = ANY(%s)"
        params.append(activity_types)

    query += " AND importance >= %s"
    params.append(min_importance)

    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)

    activities = await db.query(query, params)

    return {
        "status": "success",
        "activities": [
            {
                "id": a['activity_id'],
                "timestamp": a['created_at'].isoformat(),
                "type": a['activity_type'],
                "priority": a['priority'],
                "data": {
                    "summary": a['summary'],
                    "details": a['details'],
                    "symbol": a['related_symbol'],
                    "importance": a['importance']
                }
            }
            for a in activities
        ],
        "count": len(activities)
    }


@router.get("/api/v2/agent/{config_id}/balance-series")
async def get_balance_timeseries(
    config_id: str,
    start_time: str = Query(None),
    end_time: str = Query(None),
    interval_minutes: int = Query(5)
):
    """Get account balance over time for equity curve"""

    # Query paper_accounts for balance snapshots
    # For now, we'll interpolate from trade history
    # Future: Store balance snapshots in separate table

    query = """
        SELECT
            created_at,
            current_balance
        FROM paper_accounts
        WHERE config_id = %s
    """

    account = await db.query_one(query, [config_id])

    # Get all closed trades for balance reconstruction
    trades_query = """
        SELECT opened_at, closed_at, realized_pnl
        FROM paper_trades
        WHERE config_id = %s AND status = 'closed'
        ORDER BY closed_at
    """

    trades = await db.query(trades_query, [config_id])

    # Reconstruct balance over time
    initial_balance = 10000  # From paper_accounts.initial_balance
    balance_points = []

    current_balance = initial_balance
    for trade in trades:
        balance_points.append({
            "timestamp": trade['closed_at'].isoformat(),
            "balance": current_balance
        })
        current_balance += trade['realized_pnl']

    # Add current balance
    balance_points.append({
        "timestamp": datetime.utcnow().isoformat(),
        "balance": account['current_balance']
    })

    return {
        "status": "success",
        "balance_series": balance_points,
        "current_balance": account['current_balance'],
        "initial_balance": initial_balance
    }


@router.get("/api/v2/agent/{config_id}/metadata")
async def get_agent_metadata(config_id: str):
    """Get agent/bot metadata for timeline header"""

    config = await db.query_one("""
        SELECT config_name, config_type, created_at
        FROM configurations
        WHERE config_id = %s
    """, [config_id])

    account = await db.query_one("""
        SELECT
            current_balance,
            initial_balance,
            total_trades,
            win_trades,
            loss_trades,
            total_pnl
        FROM paper_accounts
        WHERE config_id = %s
    """, [config_id])

    win_rate = (account['win_trades'] / account['total_trades'] * 100) if account['total_trades'] > 0 else 0
    performance = ((account['current_balance'] - account['initial_balance']) / account['initial_balance']) * 100

    return {
        "status": "success",
        "metadata": {
            "botName": config['config_name'],
            "configType": config['config_type'],
            "startingBalance": account['initial_balance'],
            "currentBalance": account['current_balance'],
            "totalTrades": account['total_trades'],
            "winRate": round(win_rate, 1),
            "performance": round(performance, 2),
            "createdAt": config['created_at'].isoformat()
        }
    }
```

**Checklist**:
- [ ] Implement GET /agent/{config_id}/activities
- [ ] Implement GET /agent/{config_id}/balance-series
- [ ] Implement GET /agent/{config_id}/metadata
- [ ] Add query filters (time range, activity types, importance)
- [ ] Test with real agent activity data
- [ ] Optimize queries with proper indexes

---

#### Task 9: ActivityTimelineViewer Component Integration

**File**: `frontend/components/ActivityTimelineViewer.tsx`

**Changes**:
```typescript
export default function ActivityTimelineViewer({ configId }: ActivityTimelineViewerProps) {
  // Replace mock data with API calls
  const [log, setLog] = useState<ActivityLog | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch data on mount
  useEffect(() => {
    if (!configId) return

    const fetchData = async () => {
      try {
        setLoading(true)

        // Fetch all three endpoints in parallel
        const [activities, balanceSeries, metadata] = await Promise.all([
          fetch(`/api/v2/agent/${configId}/activities`).then(r => r.json()),
          fetch(`/api/v2/agent/${configId}/balance-series`).then(r => r.json()),
          fetch(`/api/v2/agent/${configId}/metadata`).then(r => r.json())
        ])

        setLog({
          activities: activities.activities,
          balanceTimeseries: balanceSeries.balance_series,
          metadata: metadata.metadata
        })

        setError(null)
      } catch (err) {
        console.error('Failed to fetch activity data:', err)
        setError('Failed to load activity timeline')
      } finally {
        setLoading(false)
      }
    }

    fetchData()

    // Poll for updates every 10 seconds
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [configId])

  // Loading state
  if (loading && !log) {
    return (
      <div className="w-full h-screen flex items-center justify-center">
        <LoadingSpinner />
        <span className="ml-3">Loading activity timeline...</span>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="w-full h-screen flex items-center justify-center">
        <EmptyState
          icon="⚠️"
          title="Failed to Load Timeline"
          description={error}
        />
      </div>
    )
  }

  // Empty state
  if (!log || log.activities.length === 0) {
    return (
      <div className="w-full h-screen flex items-center justify-center">
        <EmptyState
          icon="📊"
          title="No Activity Yet"
          description="Agent activities will appear here once it starts trading"
        />
      </div>
    )
  }

  // Rest of existing component logic...
  // (All the canvas rendering, zoom, pan, etc. stays the same)
}
```

**Checklist**:
- [ ] Replace mock data generation with API calls
- [ ] Add loading state with spinner
- [ ] Add error state handling
- [ ] Add empty state for no activities
- [ ] Implement polling for real-time updates (10s interval)
- [ ] Map API activity types to ACTIVITY_DEFS
- [ ] Test with real agent data
- [ ] Verify timeline renders correctly
- [ ] Test zoom, pan, click interactions with real data

---

#### Task 10: Side Panel Enhancement with Rich Activity Details

**File**: `frontend/components/ActivityTimelineViewer.tsx` (SidePanel component)

**Enhanced Activity Display**:
```typescript
function SidePanel({ selected, onClose }: { selected: ActivityItem[] | null; onClose: ()=>void }) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  const toggleExpand = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const renderActivityCard = (item: ActivityItem) => {
    const def = ACTIVITY_DEFS[item.type]
    const isExpanded = expandedIds.has(item.id)
    const details = item.data.details // JSONB from API

    return (
      <div key={item.id} className="rounded-xl bg-white/5 border border-white/10">
        {/* Card header */}
        <div className="p-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="text-xl">{def.icon}</div>
            <div>
              <div className="font-medium">{def.label}</div>
              <div className="text-xs text-white/60">
                {new Date(item.timestamp).toUTCString()}
              </div>
            </div>
          </div>
          {item.data.symbol && (
            <div className="text-sm text-white/70">{item.data.symbol}</div>
          )}
        </div>

        {/* Summary (always visible) */}
        <div className="px-3 pb-2 text-sm text-white/80">
          {item.data.summary}
        </div>

        {/* Details (collapsible) */}
        <div
          className={cn(
            "overflow-hidden transition-all",
            isExpanded ? "max-h-[1000px]" : "max-h-[200px]"
          )}
        >
          <div className="px-3 pb-3">
            {renderDetails(item.type, details)}
          </div>
        </div>

        {/* Expand/collapse button */}
        <button
          onClick={() => toggleExpand(item.id)}
          className="w-full py-2 text-xs text-white/50 hover:text-white/80 border-t border-white/10"
        >
          {isExpanded ? '▲ Collapse' : '▼ Expand'}
        </button>
      </div>
    )
  }

  const renderDetails = (type: ActivityType, details: any) => {
    switch (type) {
      case 'market_query':
        return <MarketQueryDetails data={details} />

      case 'analysis':
      case 'reasoning':
        return (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown>{details.markdown || details}</ReactMarkdown>
          </div>
        )

      case 'trade_entry_long':
      case 'trade_entry_short':
        return (
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-white/50">Size:</span>
              <span className="font-mono">${details.size_usd}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Leverage:</span>
              <span className="font-mono">{details.leverage}x</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Stop Loss:</span>
              <span className="font-mono text-red-400">${details.stop_loss}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Take Profit:</span>
              <span className="font-mono text-green-400">${details.take_profit}</span>
            </div>
            {details.confidence && (
              <div className="flex justify-between">
                <span className="text-white/50">Confidence:</span>
                <span className="font-mono">{(details.confidence * 100).toFixed(0)}%</span>
              </div>
            )}
          </div>
        )

      case 'trade_exit':
        return (
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-white/50">P&L:</span>
              <span className={cn(
                "font-mono font-semibold",
                details.pnl > 0 ? "text-green-400" : "text-red-400"
              )}>
                {details.pnl > 0 ? '+' : ''}${details.pnl} ({details.pnl_pct}%)
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Duration:</span>
              <span>{details.duration}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Close Reason:</span>
              <span>{details.close_reason}</span>
            </div>
          </div>
        )

      case 'agent_wait':
        return (
          <div className="text-sm text-white/70">
            <p>Duration: {details.duration_minutes} minutes</p>
            <p className="mt-2">{details.reason}</p>
          </div>
        )

      default:
        return (
          <pre className="text-xs text-white/60 overflow-x-auto">
            {JSON.stringify(details, null, 2)}
          </pre>
        )
    }
  }

  // ... rest of SidePanel component
}

// Specialized component for market data
function MarketQueryDetails({ data }: { data: any }) {
  const [activeTab, setActiveTab] = useState<'technical' | 'macro' | 'sentiment'>('technical')

  return (
    <div className="space-y-3">
      {/* Tabs */}
      <div className="flex gap-2 border-b border-white/10">
        <button
          onClick={() => setActiveTab('technical')}
          className={cn(
            "px-3 py-1 text-sm",
            activeTab === 'technical' && "border-b-2 border-emerald-500"
          )}
        >
          Technical
        </button>
        <button
          onClick={() => setActiveTab('macro')}
          className={cn(
            "px-3 py-1 text-sm",
            activeTab === 'macro' && "border-b-2 border-emerald-500"
          )}
        >
          Macro
        </button>
        <button
          onClick={() => setActiveTab('sentiment')}
          className={cn(
            "px-3 py-1 text-sm",
            activeTab === 'sentiment' && "border-b-2 border-emerald-500"
          )}
        >
          Sentiment
        </button>
      </div>

      {/* Content */}
      {activeTab === 'technical' && (
        <div className="space-y-2 text-sm">
          {data.technicals?.result?.indicators && Object.entries(data.technicals.result.indicators).map(([name, indicator]: [string, any]) => (
            <div key={name} className="flex justify-between">
              <span className="text-white/50">{name.toUpperCase()}:</span>
              <span className="font-mono">{indicator.current?.value || indicator.current?.macd}</span>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'macro' && (
        <div className="space-y-2 text-sm">
          {data.market_intelligence?.macro_economics && Object.entries(data.market_intelligence.macro_economics).map(([key, value]: [string, any]) => (
            <div key={key}>
              <div className="font-medium text-white/70">{key.toUpperCase()}</div>
              <div className="text-white/50">{value.interpretation}</div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'sentiment' && (
        <div className="space-y-2 text-sm">
          {data.market_intelligence?.sentiment_social?.twitter_sentiment && (
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-white/50">Sentiment Score:</span>
                <span className="font-mono">{data.market_intelligence.sentiment_social.twitter_sentiment.sentiment_score}</span>
              </div>
              <div className="text-white/50 text-xs">
                {data.market_intelligence.sentiment_social.twitter_sentiment.interpretation}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
```

**Checklist**:
- [ ] Add expandable/collapsible cards
- [ ] Height cap cards at 200px with expand button
- [ ] Create specialized renderers for each activity type
- [ ] Add MarketQueryDetails component with tabs
- [ ] Render markdown for analysis/reasoning types
- [ ] Format trade entries with SL/TP display
- [ ] Format trade exits with P&L coloring
- [ ] Show rich context for all activity types
- [ ] Test with real activity data
- [ ] Ensure smooth expand/collapse animations

---

#### Task 11: Real-time Updates via SSE

**Option A: Extend existing dashboard-stream**

**File**: `core/sse/dashboard_data.py`

```python
async def get_dashboard_stream_data(user_id: str):
    """Existing function - add agent activities"""

    # ... existing code for positions, decisions, accounts ...

    # Add agent activities for agentic configs
    agentic_configs = await db.query("""
        SELECT config_id FROM configurations
        WHERE user_id = %s AND config_type = 'agentic'
    """, [user_id])

    agent_activities = {}
    for config in agentic_configs:
        recent_activities = await db.query("""
            SELECT activity_id, activity_type, summary, created_at
            FROM agent_activities
            WHERE config_id = %s
            ORDER BY created_at DESC
            LIMIT 10
        """, [config['config_id']])

        agent_activities[config['config_id']] = recent_activities

    return {
        # ... existing data ...
        "agent_activities": agent_activities
    }
```

**Frontend**: Update SSE handler in ActivityTimelineViewer

```typescript
useEffect(() => {
  const eventSource = new EventSource(`/api/v2/dashboard-stream?user_id=${userId}`)

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)

    // Filter for current config
    if (data.agent_activities?.[configId]) {
      setLog(prev => ({
        ...prev,
        activities: [
          ...data.agent_activities[configId],
          ...prev.activities.filter(a =>
            !data.agent_activities[configId].some(na => na.id === a.id)
          )
        ].sort((a, b) =>
          new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        )
      }))
    }
  }

  return () => eventSource.close()
}, [userId, configId])
```

**Checklist**:
- [ ] Add agent_activities to dashboard stream data
- [ ] Filter activities by config_id in SSE handler
- [ ] Update frontend to merge new activities
- [ ] Sort by timestamp descending
- [ ] Prevent duplicates (check by activity_id)
- [ ] Test real-time activity appearance on timeline
- [ ] Verify smooth animation of new icons

---

#### Task 12: Agent Status Display

**Component**: Add to timeline header or separate status bar

```typescript
function AgentStatusBanner({ configId }: { configId: string }) {
  const [status, setStatus] = useState<AgentStatus | null>(null)

  useEffect(() => {
    // Poll every 5 seconds
    const fetchStatus = async () => {
      const res = await fetch(`/api/v2/agent/${configId}/status`)
      const data = await res.json()
      setStatus(data)
    }

    fetchStatus()
    const interval = setInterval(fetchStatus, 5000)
    return () => clearInterval(interval)
  }, [configId])

  if (!status || status.status === 'inactive') {
    return (
      <div className="px-4 py-2 rounded-lg bg-gray-500/10 border border-gray-500/30 text-gray-500">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-gray-500" />
          <span className="text-sm font-medium">Inactive</span>
        </div>
      </div>
    )
  }

  // Parse last activity from timeline data
  const currentActivity = status.current_activity || 'Running'
  const isWaiting = currentActivity.includes('Waiting')
  const nextCheckIn = status.next_check_at
    ? formatDistanceToNow(new Date(status.next_check_at))
    : null

  return (
    <div className={cn(
      "px-4 py-2 rounded-lg border",
      isWaiting
        ? "bg-yellow-500/10 border-yellow-500/30 text-yellow-500"
        : "bg-emerald-500/10 border-emerald-500/30 text-emerald-500"
    )}>
      <div className="flex items-center gap-2">
        <div className={cn(
          "w-2 h-2 rounded-full",
          isWaiting ? "bg-yellow-500" : "bg-emerald-500 animate-pulse"
        )} />
        <span className="text-sm font-medium">
          {isWaiting ? 'Waiting' : 'Running'}
        </span>
        {nextCheckIn && (
          <span className="text-xs opacity-70">
            Next check in {nextCheckIn}
          </span>
        )}
      </div>
      <div className="text-xs mt-1 opacity-70">
        {currentActivity}
      </div>
    </div>
  )
}
```

**Integration**: Add to timeline header in ActivityTimelineViewer

```typescript
// In ActivityTimelineViewer component, add to header section:
<div className="flex items-center justify-between">
  <div className="flex items-center gap-3">
    {/* Existing bot name */}
  </div>
  <div className="flex items-center gap-2">
    <AgentStatusBanner configId={configId} />
    {/* Existing metrics */}
  </div>
</div>
```

**Checklist**:
- [ ] Create AgentStatusBanner component
- [ ] Poll agent status every 5 seconds
- [ ] Show status indicator (running/waiting/inactive)
- [ ] Display current activity text
- [ ] Show countdown for "waiting" status
- [ ] Add pulsing animation for "running"
- [ ] Integrate into timeline header
- [ ] Test status transitions

---

## Success Metrics

### Phase 4a (Configure Tab):
- [ ] Users can select "Agentic" config type (with permission gates)
- [ ] AgentConfigurator displays properly with two columns
- [ ] Chat messages flow bidirectionally (user → agent → user)
- [ ] Strategy confirmation button appears at correct time
- [ ] Confirmed strategy displays in right column
- [ ] "Begin Strategy Discussion" button works for editing
- [ ] Warning modal appears when agent is active
- [ ] ActivationBar correctly activates/deactivates agents

### Phase 4b (Activity Timeline):
- [ ] agent_activities table captures all tool calls
- [ ] log_activity tool allows explicit agent logging
- [ ] API endpoints return activities, balance series, metadata
- [ ] ActivityTimelineViewer loads real data (not mock)
- [ ] Timeline shows activities with correct icons and timestamps
- [ ] Side panel displays rich details for each activity type
- [ ] Market queries show full technical + macro + sentiment data
- [ ] Real-time updates via SSE add new activities smoothly
- [ ] Agent status banner shows correct status and countdowns
- [ ] All zoom, pan, click interactions work with real data

---

## Testing Checklist

### Integration Testing:
- [ ] Create new agentic config via UI
- [ ] Complete full strategy definition conversation
- [ ] Confirm strategy and verify it saves to config_data
- [ ] Activate agent in autonomous mode
- [ ] Verify agent starts via PM2
- [ ] Monitor activity timeline for real activities
- [ ] Click activity icons and view details in side panel
- [ ] Deactivate agent and edit strategy
- [ ] Reactivate and verify new strategy is used
- [ ] Test with existing test agent (config_id: d13d5536-2498-4f27-b2bc-e4f98958e1d8)

### Edge Cases:
- [ ] Agent crashes (PM2 restart handling)
- [ ] Redis queue overflow (message limit)
- [ ] API timeout during chat (retry logic)
- [ ] Strategy confirmation fails (error handling)
- [ ] Multiple users with agents simultaneously
- [ ] Switching between bot types (scheduled → agentic)
- [ ] Empty timeline (no activities yet)
- [ ] Very long strategy text (scrolling)
- [ ] Very long activity details (expand/collapse)

---

## Related Documentation

- **Agent Phase 3**: [DOCS/todo/AGENT.md](AGENT.md) - MCP server, tools, autonomous mode
- **TODO Phase 4**: [TODO.md](../../TODO.md) - High-level task tracking
- **Frontend Architecture**: [frontend/README.md](../../frontend/README.md) - Forge patterns and state management
- **Activity Timeline Component**: [frontend/components/ActivityTimelineViewer.tsx](../../frontend/components/ActivityTimelineViewer.tsx)

---

**Last Updated**: 2025-11-02
**Status**: Ready for Implementation
**Estimated Timeline**: 2-3 weeks (overlap weeks possible with parallel work)
