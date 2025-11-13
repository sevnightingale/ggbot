# Configuration Migration Plan

**Date**: 2025-11-10
**Status**: Ready to Execute
**Approach**: Clean break - one-shot migration

---

## Migration Decisions

Based on analysis of production data (378 configs) and schema review:

1. ✅ **Remove `trading.execution_mode` entirely** - Clean break, no backward compat
2. ✅ **Keep `selected_pair` in JSONB** - Flexible, no table column needed
3. ✅ **Migrate all 373 bots from `autonomous_trading` → `scheduled_trading`** - One shot
4. ✅ **Keep extraction structure as-is** - Defer restructure to v3.0

---

## Migration Steps

### Phase 1: Database Migration (30 minutes)

**Step 1.1: Backup Database** (5 min)
```bash
# Create backup before migration
pg_dump $DATABASE_URL > backup_pre_migration_$(date +%Y%m%d_%H%M%S).sql
```

**Step 1.2: Migrate config_type** (2 min)
```sql
-- Migrate all autonomous_trading → scheduled_trading
UPDATE configurations
SET
    config_type = 'scheduled_trading',
    updated_at = NOW()
WHERE config_type = 'autonomous_trading';

-- Verify
SELECT config_type, COUNT(*)
FROM configurations
GROUP BY config_type;

-- Expected result:
-- scheduled_trading: 374 (373 + 1 existing)
-- signal_validation: 3
-- agent: 1
```

**Step 1.3: Remove trading.execution_mode from JSONB** (5 min)
```sql
-- Remove execution_mode from all configs
UPDATE configurations
SET config_data = jsonb_set(
    config_data,
    '{trading}',
    (config_data->'trading') - 'execution_mode'
)
WHERE config_data->'trading'->'execution_mode' IS NOT NULL;

-- Verify removal
SELECT COUNT(*)
FROM configurations
WHERE config_data->'trading'->'execution_mode' IS NOT NULL;
-- Expected: 0
```

**Step 1.4: Remove trading.exchange_config from JSONB** (5 min)
```sql
-- Remove legacy exchange_config
UPDATE configurations
SET config_data = jsonb_set(
    config_data,
    '{trading}',
    (config_data->'trading') - 'exchange_config'
)
WHERE config_data->'trading'->'exchange_config' IS NOT NULL;

-- Verify removal
SELECT COUNT(*)
FROM configurations
WHERE config_data->'trading'->'exchange_config' IS NOT NULL;
-- Expected: 0
```

**Step 1.5: Remove trading.provider from agent configs** (3 min)
```sql
-- Remove provider field (only in agent configs)
UPDATE configurations
SET config_data = jsonb_set(
    config_data,
    '{trading}',
    (config_data->'trading') - 'provider'
)
WHERE config_type = 'agent'
  AND config_data->'trading'->'provider' IS NOT NULL;

-- Verify
SELECT COUNT(*)
FROM configurations
WHERE config_data->'trading'->'provider' IS NOT NULL;
-- Expected: 0
```

**Step 1.6: Update schema_version** (2 min)
```sql
-- Bump to v2.2 (clean schema)
UPDATE configurations
SET config_data = jsonb_set(
    config_data,
    '{schema_version}',
    '"2.2"'
);

-- Verify
SELECT config_data->>'schema_version', COUNT(*)
FROM configurations
GROUP BY config_data->>'schema_version';
-- Expected: All configs at "2.2"
```

**Step 1.7: Add database constraints** (5 min)
```sql
-- Enforce valid config_type values
ALTER TABLE configurations
ADD CONSTRAINT valid_config_type
CHECK (config_type IN ('scheduled_trading', 'signal_validation', 'agent'));

-- Enforce valid trading_mode values
ALTER TABLE configurations
ADD CONSTRAINT valid_trading_mode
CHECK (trading_mode IN ('paper', 'symphony', 'aster'));

-- Enforce valid state values
ALTER TABLE configurations
ADD CONSTRAINT valid_state
CHECK (state IN ('active', 'inactive', 'archived'));

-- Make trading_mode NOT NULL (has default)
ALTER TABLE configurations
ALTER COLUMN trading_mode SET NOT NULL;
```

**Step 1.8: Verify Migration** (3 min)
```sql
-- Final verification query
SELECT
    'config_type' as check_name,
    config_type,
    COUNT(*) as count
FROM configurations
GROUP BY config_type

UNION ALL

SELECT
    'trading_mode' as check_name,
    trading_mode,
    COUNT(*) as count
FROM configurations
GROUP BY trading_mode

UNION ALL

SELECT
    'schema_version' as check_name,
    config_data->>'schema_version',
    COUNT(*) as count
FROM configurations
GROUP BY config_data->>'schema_version';

-- Check for any remaining legacy fields
SELECT
    'execution_mode_removed' as check_name,
    'none' as value,
    COUNT(*) as count
FROM configurations
WHERE config_data->'trading'->'execution_mode' IS NOT NULL

UNION ALL

SELECT
    'exchange_config_removed' as check_name,
    'none' as value,
    COUNT(*) as count
FROM configurations
WHERE config_data->'trading'->'exchange_config' IS NOT NULL;
```

### Phase 2: Update Backend Schema (1 hour)

**Step 2.1: Update core/config/schemas.py** (15 min)

```python
# Remove from enums
class ConfigType(str, Enum):
    SCHEDULED_TRADING = "scheduled_trading"
    SIGNAL_VALIDATION = "signal_validation"
    AGENT = "agent"
    # ❌ REMOVED: AUTONOMOUS_TRADING = "autonomous_trading"

# Remove from TradingConfig
class TradingConfig(BaseModel):
    leverage: int = Field(ge=1, le=100)
    position_sizing: PositionSizingConfig
    risk_management: RiskManagementConfig
    # ❌ REMOVED: execution_mode, exchange_config, provider

# Remove legacy AutonomousTradingConfigData class entirely

# Update discriminated union
ConfigData = Union[
    ScheduledTradingConfigData,
    SignalValidationConfigData,
    AgentConfigData
    # ❌ REMOVED: AutonomousTradingConfigData
]

# Update schema version
CURRENT_SCHEMA_VERSION = "2.2"

SCHEMA_MIGRATIONS = {
    "2.0": "Initial V2 schema with selected_data_sources",
    "2.1": "Added agent_strategy support, LLM config improvements",
    "2.2": "Removed duplication: execution_mode, exchange_config, provider",
    # "3.0": "Simplify to data_sources, strategy, trade_settings (future)",
}
```

**Step 2.2: Update ConfigService** (15 min)

```python
# core/services/config_service.py

# Remove any references to autonomous_trading
# Remove execution_mode handling
# Remove exchange_config handling

# Update validation logic (now using Pydantic schemas)
from core.config.schemas import validate_config_data, ConfigData

async def create_config(self, ...):
    # Validate using Pydantic
    validated_data = validate_config_data(config_type, config_data)
    # ... save to database
```

**Step 2.3: Update API Endpoints** (15 min)

```python
# ggbot.py

from core.config.schemas import (
    ConfigCreateRequest,
    ConfigUpdateRequest,
    ConfigResponse,
    ConfigListResponse
)

# Update create endpoint
@app.post("/api/v2/config", response_model=ConfigResponse)
async def create_config(
    request: ConfigCreateRequest,  # ← Pydantic validates automatically
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    # No manual validation needed - Pydantic handles it
    config = await config_service.create_config(...)
    return ConfigResponse(config=config)
```

**Step 2.4: Search and Replace** (15 min)

```bash
# Find all references to autonomous_trading
grep -r "autonomous_trading" --include="*.py" .

# Replace in all files
sed -i 's/autonomous_trading/scheduled_trading/g' core/**/*.py
sed -i 's/autonomous_trading/scheduled_trading/g' *.py

# Find all references to execution_mode
grep -r "execution_mode" --include="*.py" .

# Remove code that accesses config_data.trading.execution_mode
# Use trading_mode table column instead
```

### Phase 3: Update Frontend (1 hour)

**Step 3.1: Update TypeScript Types** (20 min)

```bash
# Generate TypeScript from Pydantic
cd frontend
pydantic2ts --module core.config.schemas --output types/generated/config.ts

# OR manually update types/index.ts
```

```typescript
// frontend/types/index.ts

export type ConfigType =
  | 'scheduled_trading'  // ← Only canonical name
  | 'signal_validation'
  | 'agent'
  // ❌ REMOVED: 'autonomous_trading'

export interface ConfigData {
  schema_version: string
  selected_pair: string  // ← Stays in JSONB
  extraction?: ExtractionConfig
  decision?: DecisionConfig
  trading: TradingConfig
  llm_config?: LLMConfig
  telegram_integration?: TelegramIntegrationConfig
  agent_strategy?: AgentStrategy
}

export interface TradingConfig {
  leverage: number
  position_sizing: PositionSizingConfig
  risk_management: RiskManagementConfig
  // ❌ REMOVED: execution_mode, exchange_config, provider
}
```

**Step 3.2: Update API Client** (15 min)

```typescript
// frontend/lib/api.ts

// Remove createDefaultConfigData function references to execution_mode
function createDefaultConfigData(): ConfigData {
  return {
    schema_version: "2.2",
    selected_pair: "BTC/USDT",
    trading: {
      leverage: 20,
      position_sizing: { /* ... */ },
      risk_management: { /* ... */ }
      // ❌ NO execution_mode
    },
    // ...
  }
}
```

**Step 3.3: Update UI Components** (25 min)

```bash
# Find all references in components
grep -r "autonomous_trading" frontend/

# Update displays
# "Autonomous Trading" → "Scheduled Trading"
# "autonomous_trading" → "scheduled_trading"

# Find references to execution_mode
grep -r "execution_mode" frontend/

# Remove any code reading config_data.trading.execution_mode
# Use config.trading_mode instead (from table column)
```

### Phase 4: Testing (1 hour)

**Step 4.1: Unit Tests** (20 min)

```python
# Test schema validation
def test_scheduled_trading_validation():
    valid_data = {
        "config_type": "scheduled_trading",
        "selected_pair": "BTC/USDT",
        "extraction": {...},
        "decision": {...},
        "trading": {...}
    }
    config = ScheduledTradingConfigData(**valid_data)
    assert config.config_type == "scheduled_trading"

def test_no_autonomous_trading():
    with pytest.raises(ValueError):
        config = ConfigCreateRequest(
            config_type="autonomous_trading",  # ❌ Should fail
            ...
        )

def test_no_execution_mode():
    # Ensure execution_mode is rejected
    data = {
        "config_type": "agent",
        "trading": {
            "leverage": 20,
            "execution_mode": "paper",  # ❌ Should be stripped/ignored
            ...
        }
    }
    config = AgentConfigData(**data)
    assert not hasattr(config.trading, 'execution_mode')
```

**Step 4.2: Integration Tests** (20 min)

```bash
# Test config creation
curl -X POST /api/v2/config \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "config_name": "Test Bot",
    "config_type": "scheduled_trading",
    "trading_mode": "paper",
    "config_data": {...}
  }'

# Test config loading
curl /api/v2/config/$CONFIG_ID -H "Authorization: Bearer $TOKEN"

# Verify response has no execution_mode in trading
```

**Step 4.3: Frontend Testing** (20 min)

- Create new bot via UI
- Verify bot type shows "Scheduled Trading" (not "Autonomous Trading")
- Edit existing bot configuration
- Verify no references to execution_mode in console logs
- Test bot activation/deactivation
- Verify trading_mode is used correctly for routing

### Phase 5: Deployment (30 minutes)

**Step 5.1: Pre-Deployment Checklist**

- [ ] Database backup created
- [ ] Migration SQL scripts tested on staging
- [ ] Backend code reviewed
- [ ] Frontend build succeeds
- [ ] Unit tests pass
- [ ] Integration tests pass

**Step 5.2: Deployment Sequence**

1. **Stop active bots** (if any)
   ```sql
   UPDATE configurations SET state = 'inactive' WHERE state = 'active';
   ```

2. **Run database migrations** (Phase 1 SQL)
   ```bash
   psql $DATABASE_URL < migration_v2.2.sql
   ```

3. **Verify database migration**
   ```sql
   -- Run verification queries from Step 1.8
   ```

4. **Deploy backend**
   ```bash
   git add core/config/schemas.py core/services/config_service.py ggbot.py
   git commit -m "feat: migrate to clean config schema v2.2"
   git push
   pm2 restart ggbot
   ```

5. **Deploy frontend**
   ```bash
   cd frontend
   git add types/ lib/ app/
   git commit -m "feat: update to config schema v2.2"
   git push
   # Vercel auto-deploys
   ```

6. **Re-enable bots** (if needed)
   ```sql
   UPDATE configurations SET state = 'active' WHERE config_id IN (...);
   ```

**Step 5.3: Post-Deployment Verification**

```bash
# Check backend health
curl https://api.ggbots.ai/health

# Check config API
curl https://api.ggbots.ai/api/v2/config \
  -H "Authorization: Bearer $TOKEN"

# Verify no errors in logs
pm2 logs ggbot --lines 100

# Test bot creation via UI
# Test bot editing via UI
# Test agent strategy builder
```

---

## Rollback Plan

If migration fails:

**Step 1: Restore Database**
```bash
# Stop services
pm2 stop ggbot

# Restore from backup
psql $DATABASE_URL < backup_pre_migration_YYYYMMDD_HHMMSS.sql

# Verify restoration
psql $DATABASE_URL -c "SELECT config_type, COUNT(*) FROM configurations GROUP BY config_type;"
```

**Step 2: Revert Code**
```bash
git revert HEAD
git push
pm2 restart ggbot
```

**Step 3: Investigate**
- Review error logs
- Identify failure point
- Fix issues
- Re-test on staging
- Retry migration

---

## Success Criteria

Migration is successful when:

- ✅ All 373 `autonomous_trading` configs → `scheduled_trading`
- ✅ All `execution_mode` fields removed from JSONB
- ✅ All `exchange_config` fields removed from JSONB
- ✅ All `provider` fields removed from agent configs
- ✅ All configs at `schema_version: "2.2"`
- ✅ Database constraints added and enforced
- ✅ Backend uses new schemas, Pydantic validation works
- ✅ Frontend creates/edits configs without errors
- ✅ No references to removed fields in codebase
- ✅ All tests pass
- ✅ Bots can be created, edited, activated

---

## Timeline

- **Phase 1** (Database): 30 minutes
- **Phase 2** (Backend): 1 hour
- **Phase 3** (Frontend): 1 hour
- **Phase 4** (Testing): 1 hour
- **Phase 5** (Deployment): 30 minutes

**Total**: ~4 hours (half day)

**Recommended**: Execute during low-traffic period, with ability to rollback immediately.

---

## Next Steps

1. Review this plan
2. Create staging environment copy for testing
3. Execute Phase 1 on staging
4. Execute Phases 2-4 on staging
5. If successful, schedule production migration
6. Execute on production
7. Monitor for 24 hours post-migration

---

**Status**: Ready to execute
**Risk Level**: Medium (one-shot migration, but well-defined rollback)
**Breaking Changes**: Yes (removes legacy support)
**Backward Compatibility**: No (clean break)
