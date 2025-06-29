# GGBot Development Plan

## Priority 1: Config System & Service Management Enhancements

### Multi-Config Service Management
Based on ggShot integration planning, we need a robust config-driven service management system:

#### 1. Configuration Status Management
**Database Schema Updates**:
```sql
-- Add status tracking to configurations table
ALTER TABLE configurations ADD COLUMN status VARCHAR DEFAULT 'disabled';
ALTER TABLE configurations ADD COLUMN last_started TIMESTAMP;
ALTER TABLE configurations ADD COLUMN last_stopped TIMESTAMP;
-- Values: 'enabled', 'disabled', 'paused', 'error'
```

#### 2. Decision Mode Framework
**New Decision Modes**:
- `dynamic_strategy`: Bot generates trading decisions from market analysis (current default)
  - Supports both NEW_TRADE and MANAGE_TRADE modes dynamically
  - Uses scheduled extraction (every 15 minutes)
- `signal_validation`: Bot validates external signals (ggShot, future signal sources)
  - Only operates in signal validation mode (no position management)
  - Uses event-driven extraction (triggered by signal arrival)

**System Prompt Management**:
```python
SYSTEM_PROMPTS = {
    "dynamic_new_trade": "Find new trading opportunities based on market analysis...",
    "dynamic_manage_trade": "Manage your active position based on evolving market conditions...", 
    "signal_validation": "Validate this external trading signal against current market context..."
}
```

#### 3. Universal Execution Manager
**Config-Driven Service Orchestration**:
```python
class ConfigExecutionManager:
    def __init__(self):
        self.active_services = {}  # config_id -> service_instance
        
    async def sync_configs(self):
        """Monitor database for config status changes"""
        enabled_configs = get_configs_with_status('enabled')
        
        for config in enabled_configs:
            if config.id not in self.active_services:
                if config.decision.mode == "dynamic_strategy":
                    # Start scheduler service (every 15 mins)
                    service = SchedulerService(config)
                elif config.decision.mode == "signal_validation":
                    # Start event listener service (Telegram, webhooks, etc.)
                    service = SignalListenerService(config)
                
                await service.start()
                self.active_services[config.id] = service
        
        # Stop services for disabled configs
        for config_id in list(self.active_services.keys()):
            if not is_config_enabled(config_id):
                await self.stop_config_service(config_id)
```

#### 4. API Endpoints for Config Control
```bash
# Enable/disable specific configs
POST /api/config/{config_id}/enable
POST /api/config/{config_id}/disable
POST /api/config/{config_id}/pause

# Get config status and service info
GET /api/config/{config_id}/status

# List all active configs
GET /api/configs/active
```

#### 5. Frontend Integration
- Per-config enable/disable toggles in GGBotCircle
- Service status indicators (running/stopped/error)
- Decision mode selection dropdown
- Real-time status updates via WebSocket

---

## Priority 2: Frontend Config_id Integration Plan

### Current Situation
The GGBot frontend has a sophisticated multi-bot management UI (GGBotCircle carousel) but the backend integration is broken. The core issue is that `config_id` - the primary key that links bots to their configurations, trades, and performance data - is not properly propagated through the system.

### Architecture Overview
```
Frontend (React/Next.js) � API Layer � Database (PostgreSQL)
                         �
                    Zustand Store
                         �
              GGBotCircle Component
                         �
        [Agent Cards, Trades, Performance]
```

### Database Schema Context
The `configurations` table is the heart of the multi-bot system:
- `config_id` (UUID) - Primary key, links everything
- `user_id` (UUID) - User isolation  
- `config_type` (VARCHAR) - 'extraction', 'decision', 'trading'
- `config_name` (VARCHAR) - Bot display name (e.g., 'GGBOT-01')
- `config_data` (JSONB) - Actual configuration

Trades table has `config_id` foreign key to link trades to specific bots.

### Critical Issues to Fix

#### 1. Config_id Propagation (HIGHEST PRIORITY)
**Problem**: API calls don't include config_id parameter, so all bots share the same data.

**Files to modify**:
- `/home/sev/ggbot/frontend/lib/api/client.ts` - Add config_id to all API calls
- `/home/sev/ggbot/frontend/store/bot.ts` - Pass currentBotId to API methods

**Implementation**:
```typescript
// In api/client.ts, modify getConfig():
async getConfig(module: string, configId?: string) {
  const params = new URLSearchParams()
  if (configId) params.append('config_id', configId)
  const res = await fetch(`${this.baseUrl}/agent/api/config/${this.userId}/${module}?${params}`)
  // ...
}

// In store/bot.ts, update loadConfigurations():
const [extractionResult, decisionResult, tradingResult] = await Promise.allSettled([
  api.getConfig('extraction', currentBotId),
  api.getConfig('decision', currentBotId),
  api.getConfig('trading', currentBotId)
])
```

#### 2. Bot Persistence to Database
**Problem**: New bots only exist in frontend state, not in database.

**Files to modify**:
- `/home/sev/ggbot/frontend/store/bot.ts` - createBot() method
- Backend API needs new endpoints:
  - `POST /api/config/bot` - Create new bot
  - `GET /api/config/bots` - List all bots for user
  - `DELETE /api/config/bot/{config_id}` - Delete bot

**Implementation**:
```typescript
// In store/bot.ts
createBot: async (name: string) => {
  try {
    // Call API to create bot in database
    const response = await api.createBot(name)
    const newBot: Bot = {
      config_id: response.config_id, // From database
      config_name: name,
      created_at: response.created_at
    }
    // ... rest of implementation
  }
}

loadBots: async () => {
  try {
    const response = await api.getBots() // New API method
    set({ availableBots: response.bots })
    // Select first bot if none selected
    if (response.bots.length > 0 && !get().currentBotId) {
      await get().selectBot(response.bots[0].config_id)
    }
  }
}
```

#### 3. State Isolation During Bot Switching
**Problem**: selectBot() clears data but doesn't reload with new config_id.

**Files to modify**:
- `/home/sev/ggbot/frontend/store/bot.ts` - selectBot() method
- `/home/sev/ggbot/frontend/lib/api/client.ts` - Add config_id filtering to getTrades() and getPerformance()

**Implementation**:
```typescript
// In store/bot.ts
selectBot: async (botId: string) => {
  // ... existing code ...
  
  // Load configurations for the selected bot
  await get().loadConfigurations() // This now uses currentBotId
  
  // Load trades for this specific bot
  await get().loadTrades() // Modify to filter by config_id
  
  // Load performance for this bot
  await get().loadPerformance() // Modify to calculate from bot's trades
}

// In api/client.ts
async getTrades(configId?: string) {
  const params = new URLSearchParams()
  if (configId) params.append('config_id', configId)
  const res = await fetch(`${this.baseUrl}/dashboard/api/dashboard/${this.userId}/trades?${params}`)
  // ...
}
```

#### 4. API Integration & Error Handling
**Problem**: Mock data fallback hides broken integration.

**Files to modify**:
- `/home/sev/ggbot/frontend/store/bot.ts` - Remove mock fallbacks, add proper error states
- `/home/sev/ggbot/frontend/components/bot/GGBotCircle.tsx` - Show loading/error states

**Implementation**:
```typescript
// Add to BotState interface:
interface BotState {
  // ... existing fields ...
  isLoadingBots: boolean
  botsError: string | null
  isCreatingBot: boolean
  createBotError: string | null
}

// Show errors in UI instead of silently falling back to mock data
```

### Backend API Updates Required

#### 1. Bot Management Endpoints
```python
# In /home/sev/ggbot/core/api/agent_control_api.py or new bot_api.py

@app.post("/api/config/bot")
async def create_bot(user_id: str, request: CreateBotRequest):
    """Create new bot with unique config_id"""
    config_id = str(uuid.uuid4())
    # Insert into configurations table with config_name
    # Return config_id, config_name, created_at

@app.get("/api/config/bots/{user_id}")
async def get_bots(user_id: str):
    """Get all bots (distinct config_ids) for user"""
    # SELECT DISTINCT config_id, config_name, MIN(created_at) as created_at
    # FROM configurations WHERE user_id = %s
    # GROUP BY config_id, config_name

@app.delete("/api/config/bot/{config_id}")
async def delete_bot(config_id: str):
    """Delete all configurations for a bot"""
    # DELETE FROM configurations WHERE config_id = %s
```

#### 2. Config_id Filtering
Update existing endpoints to accept config_id parameter:
- `/api/config/{user_id}/{module}` - Filter by config_id
- `/api/dashboard/{user_id}/trades` - Filter by config_id  
- `/api/dashboard/{user_id}/performance` - Calculate from config_id's trades

### Testing Plan

1. **Create Bot Test**:
   - Click + button in carousel
   - Verify new bot appears in database with unique config_id
   - Verify bot persists after page refresh

2. **Bot Switching Test**:
   - Create 2 bots with different configurations
   - Switch between them
   - Verify each shows correct configs/trades/performance

3. **Delete Bot Test**:
   - Delete a bot
   - Verify removed from database
   - Verify cannot delete last bot

### Implementation Order

1. **Phase 1**: Backend API for bot CRUD operations
2. **Phase 2**: Frontend API client updates with config_id
3. **Phase 3**: Update Zustand store to use real API
4. **Phase 4**: Remove mock data fallbacks
5. **Phase 5**: Add proper loading/error states

### Key Files Reference

**Frontend**:
- `/home/sev/ggbot/frontend/components/bot/GGBotCircle.tsx` - Main carousel component
- `/home/sev/ggbot/frontend/store/bot.ts` - Zustand store with bot state
- `/home/sev/ggbot/frontend/lib/api/client.ts` - API client that needs config_id support
- `/home/sev/ggbot/frontend/types/index.ts` - TypeScript interfaces

**Backend**:
- `/home/sev/ggbot/core/api/agent_control_api.py` - Add bot management endpoints
- `/home/sev/ggbot/API.md` - Document new endpoints
- `/home/sev/ggbot/database/` - Schema already supports config_id

**Database**:
- `configurations` table - Primary storage for bots
- `trades` table - Has config_id foreign key
- Use MCP postgres tool for testing: `mcp__postgres__query`

### Success Criteria

1. Multiple bots can be created and persist in database
2. Each bot maintains separate configurations
3. Trades are correctly associated with specific bots
4. Performance metrics calculate per-bot
5. UI accurately reflects bot-specific state
6. No mock data fallbacks - real API integration

This plan provides a complete roadmap for fixing the multi-bot functionality. The config_id is the key that unlocks proper data isolation and persistence.



Additional concerns: 
  The current API endpoints seem to still be using the old
  module-based approach (/config/{user_id}/{module}) when
  the database structure has evolved to unified configs.


