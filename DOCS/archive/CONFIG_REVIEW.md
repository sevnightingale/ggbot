# Configuration System: Comprehensive Technical Review

**Date**: 2025-11-10
**Status**: Critical Issues Identified
**Severity**: Medium-High (Functional but fragile)

---

## Executive Summary

The ggbots configuration system uses a **hybrid storage approach**: critical metadata as PostgreSQL columns, flexible settings in JSONB. While functional, the system has accumulated **significant technical debt** including:

1. **373 bots use legacy `autonomous_trading` type, only 1 uses new `scheduled_trading` name**
2. **Shallow merge on updates risks losing nested config fields** (extraction, decision, trading)
3. **Two parallel config systems** (ConfigService vs ConfigRepository) with divergent validation
4. **Agent configs bypass all validation** - can be created with invalid/missing fields
5. **Inconsistent terminology** between frontend/backend creates confusion

**Database verification confirms**: Clean schema (no actual field duplication), but naming inconsistency and code fragmentation create maintenance burden and data loss risk.

---

## 1. Database Schema Architecture

### 1.1 Production Schema (Verified 2025-11-10)

**`configurations` table**:
```sql
CREATE TABLE configurations (
    -- Primary identifiers
    config_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL,

    -- Table columns (queryable, indexed)
    config_type         VARCHAR(50) NOT NULL,          -- ✅ Table column ONLY
    config_name         VARCHAR(100) DEFAULT NULL,     -- ✅ Table column ONLY
    state               TEXT NOT NULL DEFAULT 'inactive',
    trading_mode        VARCHAR(20) DEFAULT 'paper',   -- ✅ Table column ONLY
    symphony_agent_id   VARCHAR(255) DEFAULT NULL,

    -- JSONB blob (flexible schema)
    config_data         JSONB NOT NULL,

    -- Timestamps
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**JSONB structure (`config_data`)**:
```json
{
  "schema_version": "2.1",
  "selected_pair": "BTC/USDT",
  "extraction": { /* market data config */ },
  "decision": { /* AI decision config */ },
  "trading": { /* position sizing, risk mgmt */ },
  "llm_config": { /* LLM provider settings */ },
  "telegram_integration": { /* Telegram config */ },
  "agent_strategy": { /* Only for agent type */ }
}
```

### 1.2 Field Storage Decision Matrix

| Field | Column | JSONB | Rationale |
|-------|--------|-------|-----------|
| `config_type` | ✅ | ❌ | Enables SQL filtering: `WHERE config_type = 'agent'` |
| `config_name` | ✅ | ❌ | User-facing, needs search/sort |
| `state` | ✅ | ❌ | Critical for scheduler: `WHERE state = 'active'` |
| `trading_mode` | ✅ | ❌ | Routes execution (paper/symphony/aster) |
| `symphony_agent_id` | ✅ | ❌ | Live trading integration ID |
| `selected_pair` | ❌ | ✅ | Bot-specific, changes frequently |
| `extraction` | ❌ | ✅ | Complex nested object |
| `decision` | ❌ | ✅ | Complex nested object |
| `trading` | ❌ | ✅ | Complex nested object |
| `llm_config` | ❌ | ✅ | User-specific LLM settings |
| `agent_strategy` | ❌ | ✅ | Large text field, agent-only |

**Verification Query Results** (2025-11-10):
```
Total configs: 378
Configs with JSONB config_type: 1  ← Legacy data
Non-null JSONB config_type: 1
```

✅ **GOOD**: No systematic duplication. Only 1 legacy config has `config_type` in JSONB.

---

## 2. The Three Bot Types (config_type)

### 2.1 Production Distribution

**Verified from database**:
```
autonomous_trading:  373 bots  ← 98.7% use LEGACY name
scheduled_trading:     1 bot   ← 0.3% use NEW name
signal_validation:     3 bots
agent:                 1 bot
```

### 2.2 Type Definitions & Usage

| Type | Legacy Name | New Name | Frontend Display | Purpose |
|------|-------------|----------|------------------|---------|
| **Standard Bot** | `autonomous_trading` | `scheduled_trading` | "Scheduled Trading" | Scheduled extraction+decision cycle |
| **Signal Validator** | `signal_validation` | `signal_validation` | "Signal Validation" | Validate ggShot signals |
| **Agent** | `agent` | `agent` | "Agentic" | Autonomous AI agent |

### 2.3 Critical Naming Inconsistency ⚠️

**Backend defaults** (`ggbot.py` line 110, `config_service.py` line 29):
```python
config_type: str = "autonomous_trading"  # ⚠️ OLD NAME
```

**Frontend defaults** (`frontend/types/index.ts` line 49):
```typescript
export type ConfigType = 'scheduled_trading' | 'signal_validation' | 'agent'  // ⚠️ NEW NAME
```

**Impact**:
- Frontend creates bots with `scheduled_trading`
- Backend defaults to `autonomous_trading`
- **373 production bots stuck on old name**
- Validation logic must handle BOTH names
- Documentation uses `scheduled_trading` but code uses `autonomous_trading`

**Recommendation**: **Choose ONE canonical name and migrate all bots**

### 2.4 Type-Specific Validation Logic

**Agent validation bypass** (`config_service.py` lines 129-134):
```python
def validate(self) -> List[str]:
    """Validate configuration based on type."""
    errors = []

    if self.config_type == "agent":
        # Agent configs can be created WITHOUT agent_strategy initially
        # Strategy is built during strategy_definition mode
        # selected_pair optional (agent can trade multiple pairs)
        # extraction/decision/llm_config optional
        return errors  # ⚠️ RETURNS EMPTY - NO VALIDATION AT ALL

    # Standard bot validation
    if not self.selected_pair:
        errors.append("selected_pair is required")

    if not self.extraction:
        errors.append("extraction is required for non-agent configs")

    # Decision validation (not for signal_validation)
    if self.config_type != "signal_validation":
        if not self.decision:
            errors.append("decision is required")
```

**❌ CRITICAL ISSUE**: Agent bots have **zero validation**
- Can be created with NULL/empty `trading` config
- Can be saved without `agent_strategy`
- No minimum validation for required fields
- **Fails at runtime instead of creation time**

**Recommendation**: Add minimum validation:
```python
if self.config_type == "agent":
    if not self.trading:
        errors.append("trading config is required even for agents")
    # agent_strategy optional during creation (built in strategy mode)
    return errors
```

---

## 3. The Three Trading Modes (trading_mode)

### 3.1 Production Distribution

**Verified from database**:
```
paper: 377 bots  ← 99.7%
aster:   1 bot   ← 0.3%
live:    0 bots  ← (Symphony bots stored as 'live')
```

### 3.2 Mode Definitions

| Mode Value | Display Name | Service Class | Symbol Support |
|------------|--------------|---------------|----------------|
| `paper` | "Paper Trading" | `SupabasePaperTradingService` | All 142 symbols |
| `live` | "Symphony" | `SymphonyLiveTradingService` | 100 symbols |
| `aster` | "AsterDEX" | `AsterDEXV3LiveTradingService` | 33 symbols |

### 3.3 Symphony/Live Naming Ambiguity ⚠️

**Database stores**: `'live'` (for Symphony bots)
**Frontend displays**: "Symphony"
**Some code expects**: `'symphony'`
**Docs refer to**: "Symphony live trading"

**Execution routing** (`ggbot.py` orchestrator):
```python
if config.trading_mode == "aster":
    service = self.aster_trading
elif config.trading_mode == "live":  # ⚠️ Expects 'live' not 'symphony'
    service = self.symphony_trading
else:
    service = self.paper_trading
```

**Impact**:
- Frontend must map "Symphony" → "live" during creation
- User confusion about what "live" means
- Code comments explain Symphony → live mapping

**Recommendation**: **Settle on canonical term**:
- Option A: Database uses `'symphony'`, rename from `'live'`
- Option B: Frontend uses "Live (Symphony)", keep `'live'`

---

## 4. Data Flow Architecture

### 4.1 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER (Frontend)                              │
│  1. BotCreationModal collects: name, type, mode, symphony_id  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              apiClient.createConfig()                           │
│  POST /api/v2/config                                           │
│  Body: {                                                        │
│    config_name: "My Bot",                                      │
│    config_type: "scheduled_trading",  ← Frontend default       │
│    trading_mode: "paper",                                      │
│    symphony_agent_id: null,                                    │
│    trading: { /* ... */ },                                     │
│    extraction: { /* ... */ },                                  │
│    decision: { /* ... */ }                                     │
│  }                                                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│         ggbot.py: POST /api/v2/config                          │
│  1. Parse ConfigCreateRequest (Pydantic)                       │
│  2. Default: config_type = "autonomous_trading" ← Backend      │
│  3. Call ConfigService.create_config()                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│     ConfigService.create_config()                              │
│  1. Create BotConfigV2 instance                                │
│  2. Validate via config.validate()  ← Type-specific logic     │
│  3. Convert to JSONB via config.to_jsonb()                     │
│  4. INSERT INTO configurations                                 │
│     SET config_name = %s,  ← Table column                      │
│         config_type = %s,  ← Table column                      │
│         trading_mode = %s, ← Table column                      │
│         config_data = %s   ← JSONB blob                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              PostgreSQL configurations table                    │
│  Stores table columns + JSONB separately                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼ (When loading)
┌─────────────────────────────────────────────────────────────────┐
│     ConfigService.get_config()                                 │
│  1. SELECT config_name, config_data, config_type, ...          │
│  2. Parse row, flatten nested structure                        │
│  3. BotConfigV2.from_dict() creates instance                   │
│  4. Return to API endpoint                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│       GET /api/v2/config/{id} returns JSON                     │
│  {                                                              │
│    config_id: "uuid",                                          │
│    config_name: "My Bot",  ← From table column                │
│    config_type: "autonomous_trading",  ← From table column     │
│    trading_mode: "paper",  ← From table column                 │
│    state: "inactive",                                          │
│    config_data: {  ← Nested JSONB                              │
│      schema_version: "2.1",                                    │
│      selected_pair: "BTC/USDT",                                │
│      extraction: { /* ... */ },                                │
│      decision: { /* ... */ },                                  │
│      trading: { /* ... */ }                                    │
│    }                                                            │
│  }                                                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Frontend State (forge/page.tsx)                   │
│  const allBots: BotConfiguration[] = [...api response]         │
│  const selectedBot = allBots.find(...)                         │
│                                                                 │
│  Conditional rendering based on selectedBot.config_type:       │
│  - agent         → <AgentConfigurator />                       │
│  - other         → <ConfigureLayout /> + <SaveConfigBar />     │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Update Flow (Where Data Loss Occurs)

```
┌─────────────────────────────────────────────────────────────────┐
│   Frontend: User edits extraction settings                     │
│   handleStrategyChange() calls:                                │
│   apiClient.updateConfig(config_id, {                          │
│     agent_strategy: { content: "new text" }  ← PARTIAL UPDATE  │
│   })                                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│        PUT /api/v2/config/{id}                                 │
│  ConfigUpdateRequest: All fields Optional[...]                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│     ConfigService.update_config()                              │
│  1. Load existing_config from DB                               │
│  2. Create updated_config with:                                │
│     extraction = config_data.get("extraction",                 │
│                                   existing_config.extraction)  │
│     ⚠️ SHALLOW REPLACEMENT - loses nested fields if partial    │
│                                                                 │
│  3. Deep merge ONLY for agent_strategy:                        │
│     if "agent_strategy" in config_data:                        │
│       merged = {**existing.agent_strategy,                     │
│                 **config_data["agent_strategy"]}  ← Fixed!     │
│                                                                 │
│  4. UPDATE configurations SET config_data = ...                │
└─────────────────────────────────────────────────────────────────┘
```

**❌ DATA LOSS RISK**: If frontend sends `{ extraction: { indicators: [...] } }`, the entire `extraction.selected_data_sources` field is lost because of shallow merge.

**✅ FIXED FOR**: `agent_strategy` (as of 2025-11-10)
**❌ NOT FIXED FOR**: `extraction`, `decision`, `trading`, `llm_config`, `telegram_integration`

---

## 5. The Two Config Systems Problem

### 5.1 System 1: ConfigService + BotConfigV2

**Location**: `core/services/config_service.py`
**Used by**: V2 orchestrator (`ggbot.py`), all `/api/v2/config` endpoints
**Model**: Plain Python class with manual methods

```python
class BotConfigV2:
    """Dataclass-style config model."""
    def __init__(self, config_id, user_id, config_name, selected_pair, ...):
        self.config_id = config_id
        self.config_name = config_name
        # ... 18 fields

    def validate(self) -> List[str]:
        """Manual validation with type-specific logic."""
        # Returns list of error strings

    def to_jsonb(self) -> Dict[str, Any]:
        """Convert to JSONB for database storage."""
        # Returns only config_data fields (not table columns)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to full dict for API response."""
        # Returns all fields including table columns

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BotConfigV2':
        """Load from database result."""
```

**Validation example**:
```python
if self.config_type == "agent":
    return []  # No validation
elif self.config_type == "signal_validation":
    # Skip decision validation
else:
    # Full validation for autonomous_trading
```

### 5.2 System 2: ConfigRepository + BotConfig (Pydantic)

**Location**: `core/config/models.py`, `core/config/repository.py`
**Used by**: Template system, some legacy code paths
**Model**: Pydantic BaseModel with automatic validation

```python
class BotConfig(BaseModel):
    """Pydantic config model with automatic validation."""
    schema_version: str = Field(default="1.0")
    selected_pair: Optional[str] = Field("BTC/USDT")
    extraction: Optional[ExtractionConfig] = None
    decision: Optional[DecisionConfig] = None
    trading: TradingConfig = Field(default_factory=TradingConfig)
    llm_config: Optional[LLMConfig] = None
    telegram_integration: Optional[TelegramIntegrationConfig] = None
    agent_strategy: Optional[AgentStrategy] = None

    # Pydantic automatically validates types, required fields, etc.
```

### 5.3 Architectural Problems

**❌ Issue 1: Divergent Validation**
- `BotConfigV2.validate()` has custom type-specific logic
- `BotConfig` Pydantic validation is type-agnostic
- **Different rules = inconsistent behavior**

**❌ Issue 2: Redundant Code**
- Both models define same fields
- Both serialize to/from database
- Maintenance burden: change one, must change the other

**❌ Issue 3: Unclear Ownership**
- ConfigService uses BotConfigV2
- ConfigRepository uses BotConfig
- **Which is canonical?**

**❌ Issue 4: Dead Code Risk**
- ConfigRepository seems unused by V2 orchestrator
- Template system uses ConfigRepository
- **Is it legacy or active?**

### 5.4 Recommendation

**Option A: Unify on Pydantic**
- Migrate ConfigService to use `BotConfig` Pydantic models
- Add type-specific validation via Pydantic validators
- Deprecate `BotConfigV2` class
- **Pro**: Type safety, automatic validation, less code
- **Con**: Major refactor, must update all orchestrator code

**Option B: Keep Separate, Document Boundaries**
- ConfigService (BotConfigV2) for runtime operations
- ConfigRepository (BotConfig) for templates only
- Clearly document which is used where
- Ensure validation parity between both
- **Pro**: No breaking changes, clear boundaries
- **Con**: Maintenance burden continues

---

## 6. Frontend Integration Issues

### 6.1 TypeScript Type Definition

**`BotConfiguration` interface** (`frontend/lib/api.ts` lines 99-110):
```typescript
export interface BotConfiguration {
  config_id: string
  user_id: string
  config_name: string
  config_type: string                    // ← From table column
  config_data: ConfigData                // ← JSONB blob
  state: 'active' | 'inactive'
  trading_mode?: 'paper' | 'live' | 'aster'  // ⚠️ Optional but should be required
  symphony_agent_id?: string
  created_at: string
  updated_at: string
}
```

**`ConfigData` interface** (`frontend/lib/api.ts` lines 7-97):
```typescript
export interface ConfigData {
  schema_version: string
  config_type?: string  // ⚠️ DUPLICATE - exists in parent BotConfiguration
  selected_pair: string
  extraction?: { /* ... */ }
  decision?: { /* ... */ }
  llm_config?: { /* ... */ }
  agent_strategy?: {
    content: string
    autonomously_editable?: boolean
    version?: number
    last_updated_at?: string
    last_updated_by?: 'user' | 'agent'
    performance_log?: Array<Record<string, unknown>>
  }
  trading: { /* ... */ }
  telegram_integration: { /* ... */ }
}
```

**⚠️ Issue 1: config_type duplication**
- Exists in `BotConfiguration.config_type` (from table)
- Also defined in `ConfigData.config_type` (optional, from JSONB)
- **Database reality**: Only 1/378 configs have JSONB config_type
- **Risk**: Future code might populate JSONB field, creating confusion

**⚠️ Issue 2: trading_mode optional**
- Marked as `Optional` in TypeScript
- But backend defaults to `'paper'` (never NULL)
- Frontend should treat as required

### 6.2 Split Editing State Problem

**Forge page state** (`frontend/app/forge/page.tsx` lines 74-81):
```typescript
// Two separate editing states
const [editingConfigData, setEditingConfigData] = useState<ConfigData | null>(null)  // JSONB
const [editingTableFields, setEditingTableFields] = useState<{
  config_name?: string
  config_type?: string
} | null>(null)  // Table columns

const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
const [originalConfig, setOriginalConfig] = useState<BotConfiguration | null>(null)
```

**Save logic** (`page.tsx` lines 762-777):
```typescript
const saveConfigurationChanges = async () => {
  if (!selectedBot || !editingConfigData || !editingTableFields || !hasUnsavedChanges) return

  const updatedBot = await apiClient.updateConfig(
    selectedBot.config_id,
    editingConfigData,                     // JSONB blob
    editingTableFields.config_name,        // Table field
    editingTableFields.config_type         // Table field
  )

  // Must remember to merge both states
}
```

**❌ Risk**: Forgetting to include `editingTableFields` loses `config_name` changes

**Recommendation**: Unified editing model
```typescript
interface EditingState {
  // Table columns
  config_name: string
  config_type: ConfigType

  // JSONB fields
  selected_pair: string
  extraction: ExtractionConfig
  decision: DecisionConfig
  // ... etc
}

// Single editing state
const [editingState, setEditingState] = useState<EditingState | null>(null)
```

### 6.3 SSE Streaming Architecture

**Dashboard data enrichment** (`core/sse/dashboard_data.py` lines 19-77):
```python
async def get_unified_dashboard_data(user_id: str) -> Dict[str, Any]:
    """
    Get all dashboard data for a user via single optimized query.

    Combines:
    - Bot configurations (non-archived)
    - Open positions (paper + live from Symphony/Aster)
    - Recent decisions (5 per bot)
    - Account summaries with portfolio analytics
    """
```

**Single CTE-based query** (lines 84-174):
```python
cur.execute("""
    WITH bot_configs AS (
        SELECT
            config_id,
            config_name,           -- ← Table column
            config_type,           -- ← Table column
            trading_mode,          -- ← Table column
            symphony_agent_id,     -- ← Table column
            config_data,           -- ← JSONB blob
            state,
            created_at,
            updated_at
        FROM configurations
        WHERE user_id = %s AND state != 'archived'
    ),
    -- ... more CTEs for positions, decisions, accounts
""", (user_id,))
```

**Enhancement pipeline**:
1. Load base config from database
2. Add Redis execution status (`_enhance_bot_with_runtime_data`)
3. Fetch Symphony/Aster positions in parallel (`_enrich_live_positions_and_accounts`)
4. Calculate portfolio analytics (`_enhance_accounts_with_portfolio_data`)
5. Stream to frontend via SSE

**✅ Good**: Single optimized query, parallel enrichment
**✅ Good**: Properly separates table columns from JSONB
**⚠️ Watch**: Complex enhancement logic could fail silently

---

## 7. Critical Issues Summary

### 7.1 High Severity

**1. Naming Inconsistency: autonomous_trading vs scheduled_trading**
```
Production: 373 bots = "autonomous_trading" (98.7%)
Production:   1 bot  = "scheduled_trading"  (0.3%)
Backend defaults to: "autonomous_trading"
Frontend defaults to: "scheduled_trading"
```

**Impact**:
- New bots created with different type than existing bots
- Validation must handle both names
- User confusion about bot types
- Documentation mismatch with reality

**Fix Priority**: **HIGH** - Migrate all bots to canonical name

**2. Shallow Merge Data Loss Risk**

**Current behavior**:
```python
# If frontend sends: {"extraction": {"indicators": ["RSI"]}}
# Backend does: extraction = update_data.get("extraction", existing.extraction)
# Result: ENTIRE extraction object replaced, losing selected_data_sources
```

**Impact**:
- Partial updates to nested objects lose sibling fields
- Frontend must always send COMPLETE objects
- Agent strategy updates FIXED (2025-11-10)
- Other fields still vulnerable

**Fix Priority**: **HIGH** - Implement recursive deep merge

**3. Agent Validation Bypass**

**Current code**:
```python
if self.config_type == "agent":
    return []  # No validation at all
```

**Impact**:
- Agents can be created with NULL trading config
- Agents can be created without agent_strategy
- Runtime errors instead of creation-time validation
- Security/stability risk

**Fix Priority**: **MEDIUM** - Add minimum validation

### 7.2 Medium Severity

**4. Two Config Systems (ConfigService vs ConfigRepository)**

**Impact**:
- Divergent validation rules
- Code duplication
- Maintenance burden
- Unclear ownership

**Fix Priority**: **MEDIUM** - Unify or clearly document boundaries

**5. Symphony/Live Terminology Inconsistency**

```
Database:  'live'
Frontend:  "Symphony"
Some code: 'symphony'
```

**Impact**:
- User confusion
- Mapping logic required
- Documentation ambiguity

**Fix Priority**: **MEDIUM** - Choose canonical term

### 7.3 Low Severity

**6. TypeScript config_type Duplication**

**Issue**: `config_type` defined in both `BotConfiguration` and optional in `ConfigData`

**Impact**:
- Potential confusion
- Risk of JSONB field being populated in future

**Fix Priority**: **LOW** - Remove from ConfigData interface

**7. Split Frontend Editing State**

**Issue**: Separate state for table columns vs JSONB

**Impact**:
- Easy to forget merging during save
- Code complexity

**Fix Priority**: **LOW** - Unified editing model

---

## 8. Technical Debt Inventory

### 8.1 Incomplete Migration

**autonomous_trading → scheduled_trading**

**Status**: Started but not completed
- Backend defaults to old name
- Frontend uses new name
- 373 production bots on old name
- No migration script exists

**Recommendation**:
```sql
-- Option A: Migrate to new name
UPDATE configurations
SET config_type = 'scheduled_trading'
WHERE config_type = 'autonomous_trading';

-- Option B: Rollback to old name (simpler)
-- Update frontend TypeScript to use 'autonomous_trading'
-- Update backend validation to only accept old name
-- Document "autonomous_trading" as canonical
```

### 8.2 Missing Database Constraints

**No table constraints on enum fields**:
```sql
-- Current: Any string allowed
config_type VARCHAR(50) NOT NULL

-- Recommended: Enforce valid values
ALTER TABLE configurations
ADD CONSTRAINT valid_config_type
CHECK (config_type IN ('autonomous_trading', 'signal_validation', 'agent'));

ALTER TABLE configurations
ADD CONSTRAINT valid_trading_mode
CHECK (trading_mode IN ('paper', 'live', 'aster'));

ALTER TABLE configurations
ADD CONSTRAINT valid_state
CHECK (state IN ('active', 'inactive', 'archived'));
```

**Impact**: Invalid values can be inserted, causing runtime errors

### 8.3 No Migration Script System

**Issue**: Schema changes done manually, no version control

**Missing**:
- `/database/migrations/` directory structure
- Up/down migration scripts
- Migration version tracking table
- Automated migration runner

**Recommendation**: Implement migration system:
```
database/migrations/
  001_add_trading_mode_column.sql
  002_add_symphony_agent_id.sql
  003_rename_autonomous_to_scheduled.sql  ← Need this
  schema_versions.sql  ← Track applied migrations
```

### 8.4 Validation Fragmentation

**Validation happens in 4 places**:
1. Frontend TypeScript type checking (compile-time)
2. Backend Pydantic request models (runtime, API layer)
3. BotConfigV2.validate() method (runtime, service layer)
4. BotConfig Pydantic validation (runtime, repository layer)

**Problem**: No single source of truth

**Recommendation**: Generate types from OpenAPI schema or shared JSON schema

---

## 9. Recommendations Roadmap

### Phase 1: Immediate Fixes (Week 1)

**1.1 Resolve Naming Inconsistency**
- [ ] Choose: `autonomous_trading` (rollback) OR `scheduled_trading` (complete migration)
- [ ] Update backend defaults to match frontend
- [ ] Migrate all 373 production bots to canonical name
- [ ] Update all documentation
- [ ] Add database constraint to enforce valid types

**1.2 Implement Deep Merge for All Config Sections**
- [x] ✅ DONE: agent_strategy deep merge (2025-11-10)
- [ ] Add recursive deep merge for: extraction, decision, trading, llm_config, telegram_integration
- [ ] Test: Partial update to nested field preserves siblings
- [ ] Document: Frontend can send partial updates safely

**1.3 Add Minimum Agent Validation**
```python
if self.config_type == "agent":
    if not self.trading:
        errors.append("trading config required")
    if not self.trading.get("leverage"):
        errors.append("trading.leverage required")
    # agent_strategy optional during creation (built in strategy mode)
    return errors
```

### Phase 2: Architecture Improvements (Week 2-3)

**2.1 Unify Config Systems**
- [ ] Decide: Migrate ConfigService to Pydantic OR deprecate ConfigRepository
- [ ] Document: Which system is canonical, when to use each
- [ ] Ensure: Validation parity between both systems
- [ ] Test: All existing code paths work with chosen system

**2.2 Frontend State Consolidation**
- [ ] Create unified `EditingState` type (table + JSONB fields)
- [ ] Refactor forge page to use single editing state
- [ ] Simplify save logic (no more merging two states)

**2.3 Add Database Constraints**
```sql
ALTER TABLE configurations
ADD CONSTRAINT valid_config_type CHECK (...),
ADD CONSTRAINT valid_trading_mode CHECK (...),
ADD CONSTRAINT valid_state CHECK (...);
```

### Phase 3: Long-term Improvements (Month 2)

**3.1 Migration System**
- [ ] Set up migration directory structure
- [ ] Create migration version tracking table
- [ ] Write migration runner script
- [ ] Backfill: Document all historical schema changes as migrations

**3.2 Type Safety**
- [ ] Generate TypeScript types from backend Pydantic models
- [ ] Shared enums for config_type, trading_mode, state
- [ ] OpenAPI schema generation for API docs

**3.3 Documentation**
- [ ] Data flow diagram (create → load → update → delete)
- [ ] Decision tree: Which config type to use?
- [ ] Examples: Correct update patterns for each field

---

## 10. File Reference

### Backend (Python)

| File | Lines | Purpose |
|------|-------|---------|
| `core/services/config_service.py` | 667 | ConfigService, BotConfigV2 model |
| `core/config/models.py` | 377 | Pydantic BotConfig models |
| `core/config/repository.py` | 369 | ConfigRepository (template system) |
| `ggbot.py` | 107-133 | API request models, endpoints |
| `core/sse/dashboard_data.py` | 444 | SSE streaming, data enrichment |

### Frontend (TypeScript)

| File | Lines | Purpose |
|------|-------|---------|
| `frontend/types/index.ts` | 135 | Core type definitions |
| `frontend/lib/api.ts` | 761 | API client, interfaces |
| `frontend/app/forge/page.tsx` | 200 | Main forge page, bot management |
| `frontend/app/forge/components/modals/BotCreationModal.tsx` | 170 | Bot creation UI |
| `frontend/app/forge/components/configure/ConfigureLayout.tsx` | - | Config tabs for standard bots |
| `frontend/app/forge/components/configure/AgentConfigurator.tsx` | - | Agent strategy builder UI |

### Documentation

| File | Relevance |
|------|-----------|
| `DOCS/DATABASE_CONTEXT.md` | Database design philosophy |
| `DOCS/completed/trading-mode-refactor.md` | Trading mode terminology (Nov 2025) |
| `CHANGELOG.md` | Feature history, naming changes |
| `README.md` | Architecture overview |
| `ACTIVE.md` | Current system status |

---

## 11. Testing Checklist

### Regression Tests Needed

**Config Creation**:
- [ ] Create autonomous_trading bot → verify config_type in DB
- [ ] Create scheduled_trading bot → verify config_type in DB
- [ ] Create signal_validation bot → verify no decision validation
- [ ] Create agent bot → verify minimal validation
- [ ] Create with trading_mode='paper' → verify mode stored
- [ ] Create with trading_mode='symphony' → verify stored as 'live'
- [ ] Create with trading_mode='aster' → verify mode stored

**Config Updates**:
- [ ] Update agent_strategy content → verify metadata preserved (version, autonomously_editable)
- [ ] Update extraction.indicators → verify extraction.selected_data_sources preserved
- [ ] Update decision.system_prompt → verify decision.user_prompt preserved
- [ ] Update trading.leverage → verify trading.position_sizing preserved
- [ ] Update config_name → verify JSONB fields unchanged
- [ ] Update config_type → verify type change allowed/blocked

**Config Loading**:
- [ ] Load config via ConfigService → verify config_name from table column
- [ ] Load config via ConfigRepository → verify same structure
- [ ] Load via API endpoint → verify response includes all fields
- [ ] Load via SSE stream → verify enrichment pipeline works

**Edge Cases**:
- [ ] Agent config with NULL agent_strategy → verify creation allowed
- [ ] Agent config with NULL selected_pair → verify creation allowed
- [ ] Signal validation with NULL decision → verify creation allowed
- [ ] Autonomous trading with NULL extraction → verify creation blocked
- [ ] Update with partial extraction → verify no data loss (after deep merge fix)

---

## 12. Conclusion

The ggbots configuration system is **functional but fragile**, with accumulated technical debt from rapid iteration:

**Strengths**:
- ✅ Clean database schema (no actual field duplication)
- ✅ Flexible JSONB for evolving config structure
- ✅ Type-specific validation logic
- ✅ SSE streaming with efficient queries

**Critical Weaknesses**:
- ❌ 373 bots stuck on legacy `autonomous_trading` name
- ❌ Shallow merge risks data loss on partial updates
- ❌ Agent configs bypass all validation
- ❌ Two parallel config systems with divergent rules
- ❌ Symphony/live terminology confusion

**Immediate Actions Required**:
1. Choose canonical name for bot types (migrate or rollback)
2. Implement deep merge for all config sections
3. Add minimum validation for agent configs
4. Add database constraints on enum fields

**Long-term Improvements**:
- Unify config systems or clearly document boundaries
- Set up migration system with version tracking
- Generate shared types from OpenAPI schema
- Consolidate validation logic

**Risk Assessment**: Medium-High
**Current Status**: Production-ready but needs debt paydown before next major feature
**Estimated Fix Time**: 2-3 weeks for Phase 1-2

---

**Document Version**: 1.0
**Last Updated**: 2025-11-10
**Author**: Claude Code (AI Assistant)
**Reviewed By**: [Pending]
