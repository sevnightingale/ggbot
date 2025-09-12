# Data Architecture & SSE Implementation Plan

**Created**: 2025-09-12  
**Purpose**: Clean up the data flow mess and implement unified SSE architecture

---

## Current Data Flow Problems

### 1. **WebSocket Chaos**
- 7+ different WebSocket message types sent every 7 seconds
- Race conditions between immediate (`bot_state_changed`) and periodic (`bot_statuses_update`) messages  
- Complex monitoring service with multiple concurrent loops
- Messages overwriting each other, breaking bot activation UX

### 2. **Inconsistent Database Access**
- **Most code uses direct PostgreSQL**: `get_db_connection()` + raw SQL
- **Some code uses Supabase SDK**: `supabase.from('table').select()`
- This is stupid and confusing - pick ONE approach

### 3. **Scattered Data Sources**
- **Database**: Bot configs, positions, decisions, metrics
- **APScheduler**: Next run times, job existence  
- **Redis**: Execution state, idempotency keys
- **In-memory**: Real-time execution phases during bot runs
- **Paper Trading Service**: Position prices, account summaries

---

## New Architecture: Server-Sent Events (SSE)

### **Core Principle**: One Stream, All Data
Replace 7+ WebSocket message types with **single SSE stream** containing everything the frontend needs.

### **Update Frequencies**
- **Position updates**: Every 3 seconds (background service for SL/TP)
- **Dashboard updates**: Every 5 seconds (SSE stream)
- **Bot execution status**: Real-time during 60-90 second cycles
- **Other data**: As needed, no artificial delays

---

## Data Flow Architecture

### **Background Services** (Always Running)
```python
# Critical infrastructure - runs 24/7
class BackgroundServices:
    async def position_monitor(self):
        """Update position prices every 3 seconds for SL/TP execution"""
        while True:
            await update_all_position_prices()  # Via paper trading service
            await asyncio.sleep(3)
    
    async def bot_scheduler(self):
        """APScheduler + Redis idempotency - existing system"""
        pass
```

### **SSE Data Stream** (Frontend Updates)
```python
@app.get("/api/dashboard-stream/{user_id}")
async def dashboard_stream(user_id: str):
    """Single unified data stream for all dashboard components"""
    
    async def generate_updates():
        while True:
            # Get all data in ONE optimized query
            data = await get_unified_dashboard_data(user_id)
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(5)  # Every 5 seconds
```

---

## Database Access Standardization

### **Decision: Use Direct PostgreSQL Pattern**
Based on existing codebase analysis:
- ✅ **90% of code already uses this**: `get_db_connection()` + raw SQL
- ✅ **Better for complex queries**: More control over joins and performance  
- ✅ **Team familiarity**: Existing patterns and knowledge
- ❌ **Abandon Supabase SDK**: Remove inconsistent dual-approach

### **Query Pattern**
```python
async def get_data(user_id: str):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT ... FROM ... WHERE user_id = %s", (user_id,))
            return cur.fetchall()
```

---

## Unified Dashboard Data Structure

### **Single Query Strategy**
```sql
WITH bot_configs AS (
    SELECT c.config_id, c.user_id, c.config_name, c.state, c.config_data
    FROM configurations c
    WHERE c.user_id = %s AND c.state != 'archived'
),
open_positions AS (
    SELECT pt.config_id, pt.trade_id, pt.symbol, pt.side, pt.size_usd, 
           pt.entry_price, pt.current_price, pt.unrealized_pnl, pt.opened_at
    FROM paper_trades pt
    INNER JOIN bot_configs bc ON pt.config_id = bc.config_id
    WHERE pt.status = 'open'
),
recent_decisions AS (
    SELECT d.config_id, d.decision_id, d.symbol, d.action, d.confidence, 
           d.reasoning, d.created_at
    FROM decisions d
    INNER JOIN bot_configs bc ON d.config_id = bc.config_id
    WHERE d.created_at > NOW() - INTERVAL '2 hours'
    ORDER BY d.created_at DESC
    LIMIT 20
),
account_summaries AS (
    SELECT pa.config_id, pa.current_balance, pa.total_pnl, 
           pa.total_trades, pa.win_trades
    FROM paper_accounts pa
    INNER JOIN bot_configs bc ON pa.config_id = bc.config_id
)
SELECT 
    json_build_object(
        'bots', (SELECT json_agg(bc.*) FROM bot_configs bc),
        'positions', (SELECT json_agg(op.*) FROM open_positions op),  
        'decisions', (SELECT json_agg(rd.*) FROM recent_decisions rd),
        'accounts', (SELECT json_agg(ac.*) FROM account_summaries ac),
        'timestamp', NOW()
    )
```

### **Enhanced with Runtime Data**
```python
async def get_unified_dashboard_data(user_id: str) -> Dict[str, Any]:
    # Get database data (single query above)
    db_data = await get_dashboard_data_from_db(user_id)
    
    # Enhance with runtime data
    for bot in db_data['bots']:
        config_id = bot['config_id']
        
        # Add scheduler info (APScheduler + Redis)
        bot['next_run'] = get_next_run_from_scheduler(config_id)
        bot['is_scheduled'] = has_scheduler_job(config_id)  
        
        # Add execution status (Redis/memory during active execution)
        bot['execution_status'] = get_current_execution_phase(config_id)
        
        # Add enhanced status info
        bot['status_color'] = get_bot_status_color(bot['state'], bot['execution_status'])
        bot['status_message'] = get_bot_status_message(bot['state'], bot['execution_status'])
        bot['show_spinner'] = bot['execution_status'] in ['extracting', 'deciding', 'trading']
    
    return db_data
```

---

## Bot Execution Status Tracking

### **No New Database Table Needed**
Bot execution status is **ephemeral** (only lasts 60-90 seconds every 1-4 hours).

### **Status Sources**
1. **Database**: `configurations.state` ('active'/'inactive')
2. **Redis**: Current execution phase during active cycles
3. **APScheduler**: Next run times and job existence
4. **In-memory**: Real-time phase updates during execution

### **Execution Flow**
```python
async def run_autonomous_cycle(config_id, user_id):
    # Set Redis execution status
    await set_execution_phase(config_id, "extracting", "Analyzing market data...")
    extraction_result = await extract()
    await asyncio.sleep(7)  # Deliberate UX delay
    
    await set_execution_phase(config_id, "deciding", "AI processing signals...")  
    decision_result = await decide()  # Takes 30+ seconds naturally
    
    await set_execution_phase(config_id, "trading", "Executing decision...")
    trading_result = await trade()
    await asyncio.sleep(3)  # Deliberate UX delay
    
    await set_execution_phase(config_id, "completed", "Cycle completed")
    
    # Clear status after 10 seconds
    asyncio.create_task(clear_execution_phase_after_delay(config_id, 10))
```

### **Redis Key Structure**
```python
# Execution phase tracking
EXECUTION_PHASE_KEY = f"bot_execution:{config_id}:phase"
EXECUTION_MESSAGE_KEY = f"bot_execution:{config_id}:message"

# APScheduler idempotency (existing)
IDEMPOTENCY_KEY = f"bot_exec:{user_id}:{config_id}:{timeframe}:{close_ts}"
```

---

## Frontend Integration

### **Single SSE Connection**
```javascript
// Replace all WebSocket complexity with one SSE stream
const eventSource = new EventSource(`/api/dashboard-stream/${userId}`);

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    // Update all components from unified data
    updateBotList(data.bots);                    // Bot cards with status circles
    updateActivityPanel(data.positions);        // Real-time P&L (3-5 second updates)
    updatePerformancePanel(data.accounts);      // Balance, metrics
    updateRecentDecisions(data.decisions);      // Decision history
    
    // Bot status circles get real-time execution updates
    data.bots.forEach(bot => {
        updateBotCircle(bot.config_id, {
            color: bot.status_color,
            message: bot.status_message,
            showSpinner: bot.show_spinner,
            phase: bot.execution_status
        });
    });
};

// User actions still use HTTP POST
const startBot = async (botId) => {
    await fetch(`/api/v2/bot/${botId}/start`, { method: 'POST' });
    // SSE will show updated status within 5 seconds
};
```

---

## Implementation Steps

### **Phase 1: SSE Foundation**
1. ✅ Create this planning document
2. Create unified dashboard query function
3. Add SSE endpoint to `ggbot.py`
4. Test SSE with simple data

### **Phase 2: Remove WebSocket Mess**
1. Comment out all WebSocket code (for rollback safety)
2. Remove monitoring service WebSocket broadcasts
3. Update bot execution flow to use Redis status
4. Test bot activation with SSE

### **Phase 3: Frontend Migration**
1. Replace WebSocket connection with SSE
2. Update all components to read from SSE data
3. Remove WebSocket message handlers
4. Test real-time updates

### **Phase 4: Cleanup**
1. Remove commented WebSocket code
2. Clean up unused monitoring methods
3. Verify all data flows work correctly
4. Update documentation

---

## Expected Benefits

### **Performance**
- **Before**: 100+ WebSocket messages/sec for 100 users
- **After**: ~20 SSE requests/sec for 100 users
- **Database**: 1 optimized query vs multiple individual queries

### **Reliability**  
- ✅ No more race conditions or message conflicts
- ✅ Predictable 5-second update cycle
- ✅ SSE auto-reconnects (better than WebSocket)
- ✅ Works better on mobile/flaky connections

### **Developer Experience**
- ✅ Single data flow to understand and debug
- ✅ Clear separation: background services vs frontend updates  
- ✅ Consistent database access pattern
- ✅ Much simpler architecture

### **User Experience**
- ✅ Bot activation works reliably (no more overwrites)
- ✅ Real-time position updates (3-5 seconds)
- ✅ Smooth execution status with deliberate UX delays
- ✅ Decisions appear immediately after completion

---

## 🎯 Implementation Status

### ✅ **PHASE 1: SSE Foundation** - **COMPLETE**
- ✅ **Unified dashboard query** with COALESCE and per-bot decision limits
- ✅ **Redis status tracking** with 120s TTL for bot execution phases  
- ✅ **SSE endpoint** at `/api/dashboard-stream` with proper headers and auth
- ✅ **Authentication via query parameters** (EventSource limitation solved)
- ✅ **Tested with real data** - streaming 2 bots, 2 decisions, 1 account successfully

### 🔥 **PHASE 2: WebSocket Destruction** - **COMPLETE**  
- ✅ **DELETED WebSocketManager class** and `/ws/bot-status/{user_id}` endpoint
- ✅ **REMOVED all websocket_manager parameters** from orchestrator methods
- ✅ **ELIMINATED 7+ WebSocket message types** (bot_status_update, bot_state_changed, etc.)
- ✅ **GUTTED monitoring service** from 800+ lines to 136 lines (positions only)
- ✅ **ADDED jitter** to position monitoring (3s + random ±0.3s)
- ✅ **Bot execution now uses Redis status** with explicit TTLs
- ✅ **All WebSocket broadcasts replaced** with Redis + SSE pattern

### ⚠️ **PHASE 3: Frontend Migration** - **IN PROGRESS**
- ✅ **SSE test page working** - proven SSE stream works in production
- ❌ **Dashboard still using old WebSocket** - failing as expected (good!)
- 🔄 **Need to create SSE frontend hook** with Last-Event-ID support  
- 🔄 **Need to update dashboard components** to read from SSE data
- 🔄 **Need to remove WebSocket handlers** from frontend

### 📋 **PHASE 4: Cleanup** - **PENDING**
- 🔄 **Remove commented WebSocket code** (after frontend migration)
- 🔄 **Clean up unused monitoring methods** 
- 🔄 **Test real-time updates end-to-end**
- 🔄 **Update documentation**

---

## 🔥 What We Destroyed:
- **1,099 lines of WebSocket complexity** deleted
- **Race conditions between message types** eliminated
- **7+ WebSocket message types** → 1 unified SSE stream
- **100+ messages/sec** → ~20 SSE requests/sec for 100 users
- **Complex concurrent loops** → simple 3-second position monitoring

## 🚀 What We Built:
- **Single SSE stream** with all dashboard data
- **Redis-based execution status** with auto-expiry
- **Unified PostgreSQL query** with proper JOINs and limits
- **Jittered position monitoring** preventing thundering herd
- **Clean, scalable architecture** ready for 100+ users

**Current Status**: Backend WebSocket destruction complete! Frontend seeing expected connection failures to deleted `/ws/bot-status/` endpoint. SSE stream working perfectly. Ready for frontend migration.

**Next**: Create SSE frontend hook and migrate dashboard components from WebSocket to SSE data.