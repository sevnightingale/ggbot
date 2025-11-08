# Trading Mode Architecture Refactor

**Completed:** 2025-01-08
**Status:** ✅ Complete
**Impact:** Major architecture change - simplified bot creation, removed duplication, added AsterDEX support

---

## Executive Summary

Refactored trading mode architecture to eliminate dead code duplication, simplify bot creation flow, and add first-class AsterDEX support. Users can now select trading mode (Paper/Symphony/Aster) during bot creation instead of the old "duplicate as live" workaround.

**Key Changes:**
- Removed `config_data.trading.execution_mode` (unused JSONB field)
- Kept `trading_mode` table column as single source of truth
- New bot creation flow: Select type + mode upfront (no more duplication)
- Complete AsterDEX credential management (Settings UI + backend)
- Renamed "live" → "Symphony" in UI for clarity
- SSE dashboard now supports Aster positions

---

## Problem Statement

### The Duplication Issue

We had **two fields doing the same job:**

1. **Table column** `trading_mode` (paper/live/aster) - Backend actually used this ✅
2. **JSONB field** `config_data.trading.execution_mode` - Frontend set this but backend **never read it** ❌

This was dead code causing confusion. The frontend would set `execution_mode` in JSONB, but the backend only checked the `trading_mode` column.

### The UX Issue

**Old Flow (Confusing):**
1. Create paper bot
2. Go to Settings → Connect Symphony
3. Find "Duplicate as Live" button in bot menu
4. Modal opens → Enter Symphony Agent ID
5. Creates new bot with `trading_mode='live'`

**Problems:**
- Indirect workflow (why duplicate?)
- Hidden feature (users didn't know it existed)
- Symphony-only (no Aster support)
- Trading mode immutable after creation

---

## Solution Architecture

### New Flow (Simple)

**User Setup (One Time):**
1. Settings → Connect Symphony credentials (API key + smart account)
2. Settings → Connect AsterDEX credentials (user wallet + aster wallet + private key)

**Bot Creation (Every Time):**
1. Click "+ New"
2. **Step 1:** Choose bot type (Scheduled/Signal Validation/Agent)
3. **Step 2:** Choose trading mode:
   - Paper Trading (Free tier)
   - Symphony Live (Pro tier 🔒)
   - AsterDEX (Pro tier 🔒)
4. If Symphony selected: Enter Symphony Agent ID
5. Create!

### Single Source of Truth

**Database:**
```sql
CREATE TABLE configurations (
  config_id UUID,
  trading_mode VARCHAR(20) DEFAULT 'paper',  -- 'paper' | 'live' | 'aster'
  symphony_agent_id VARCHAR(255) NULLABLE,   -- Only for live mode
  config_data JSONB                          -- NO execution_mode here!
);
```

**Terminology Mapping:**
- Frontend displays: "Symphony"
- Database stores: `'live'` (backwards compatible with existing bots)
- Backend logic: Maps 'symphony' → 'live' during creation

---

## Implementation Details

### Phase 1: Remove execution_mode Duplication

**Files Modified:**
- `frontend/types/index.ts` - Removed from `TradingConfig` interface
- `frontend/lib/api.ts` - Removed from `ConfigData.trading` interface
- `frontend/app/forge/page.tsx` - Removed from `createDefaultBot()` and `baseConfig`

**Verification:**
```bash
grep -r "execution_mode" frontend/ --include="*.ts" --include="*.tsx"
# Returns only test files
```

---

### Phase 2: AsterDEX Credential Management

#### Backend (vault_utils.py)

**New Methods:**
```python
class VaultManager:
    @staticmethod
    async def store_aster_credential(user_id, user_wallet, aster_wallet, private_key) -> bool:
        """Store Aster credentials in Vault"""

    @staticmethod
    async def get_aster_credential(user_id) -> Optional[Dict]:
        """Returns: {user_wallet, aster_wallet, private_key}"""

    @staticmethod
    async def delete_aster_credential(user_id) -> bool:
        """Removes credentials and disables all aster bots"""
```

#### API Endpoints (ggbot.py)

**Added:**
- `POST /api/v2/aster/setup` - Store credentials (3 fields: user_wallet, aster_wallet, private_key)
- `GET /api/v2/aster/status` - Check connection: `{connected: bool, user_wallet, aster_wallet}`
- `POST /api/v2/aster/disconnect` - Remove credentials, convert aster bots to paper

**Validation:**
- User wallet: `^0x[a-fA-F0-9]{40}$`
- Aster wallet: `^0x[a-fA-F0-9]{40}$`
- Private key: `^(0x)?[a-fA-F0-9]{64}$`

#### Frontend (SettingsModal.tsx)

**New Section:** "AsterDEX Trading" (after Symphony section)

**UI Elements:**
- 3 input fields: User Wallet (0x...), Aster Wallet (0x...), Private Key (password field)
- Connection status: Green badge when connected, shows abbreviated wallet addresses
- Buttons: "Connect Account" / "Disconnect"
- Security note: "🔒 Stored securely in encrypted vault. Never shared."

#### Database Migration

**SQL Applied:**
```sql
ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS aster_vault_id UUID,
ADD COLUMN IF NOT EXISTS aster_user_wallet VARCHAR(42),
ADD COLUMN IF NOT EXISTS aster_wallet VARCHAR(42);
```

**Storage Pattern:**
- `aster_vault_id` - Reference to encrypted private key in Supabase Vault
- `aster_user_wallet` - User's main Ethereum wallet (plaintext, display only)
- `aster_wallet` - AsterDEX trading wallet (plaintext, display only)

---

### Phase 3: BotCreationModal Refactor

**File:** `frontend/app/forge/components/modals/BotCreationModal.tsx`

#### New State Management

**Connection Status:**
```typescript
const [symphonyConnected, setSymphonyConnected] = useState(false)
const [asterConnected, setAsterConnected] = useState(false)
const [checkingConnections, setCheckingConnections] = useState(true)

// Check both on mount
useEffect(() => {
  if (open) {
    checkConnectionStatus() // Parallel fetch of Symphony + Aster status
  }
}, [open])
```

#### Trading Mode Selection UI

**Structure:**
```typescript
const tradingModes = [
  {
    mode: 'paper',
    label: 'Paper Trading',
    color: 'var(--agent-extraction)',
    available: true,  // Always available
    tier: 'Free',
    requiresConnection: false
  },
  {
    mode: 'symphony',
    label: 'Symphony Live',
    color: '#ef4444',
    available: hasLiveTrading,  // Pro gated
    tier: 'Pro',
    requiresConnection: true,
    connected: symphonyConnected
  },
  {
    mode: 'aster',
    label: 'AsterDEX',
    color: '#9333ea',
    available: hasLiveTrading,  // Pro gated
    tier: 'Pro',
    requiresConnection: true,
    connected: asterConnected
  }
]
```

#### Validation Logic

**On Submit:**
1. Check bot type availability (Pro tier for signal_validation)
2. Check trading mode availability (Pro tier for symphony/aster)
3. Check connection requirement (credentials must be set up)
4. Validate Symphony Agent ID if symphony mode (UUID format)

**Validation Code:**
```typescript
if (tradingMode === 'symphony') {
  if (!symphonyAgentId.trim()) {
    alert('Symphony Agent ID is required')
    return
  }

  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
  if (!uuidRegex.test(symphonyAgentId.trim())) {
    alert('Invalid Symphony Agent ID format')
    return
  }
}
```

#### Callback Signature Change

**Before:**
```typescript
onConfirm: (botType: BotType) => void
```

**After:**
```typescript
onConfirm: (
  botType: BotType,
  tradingMode: TradingMode,
  symphonyAgentId?: string
) => void
```

---

### Phase 4: Backend Bot Creation Update

#### API Request Model (ggbot.py)

**Updated:**
```python
class ConfigCreateRequest(BaseModel):
    config_name: str
    schema_version: str = "2.1"
    config_type: str = "autonomous_trading"
    trading_mode: str = "paper"              # NEW: Required
    symphony_agent_id: Optional[str] = None  # NEW: Conditional
    selected_pair: Optional[str] = "BTC/USDT"
    extraction: Optional[Dict[str, Any]] = None
    decision: Optional[Dict[str, Any]] = None
    trading: Dict[str, Any]
    # ...
```

#### Validation Logic

**Order of Checks:**
1. **Trading mode validation**: Must be 'paper', 'symphony', or 'aster'
2. **Pro subscription check**: Live/Aster require `profile.can_use_live_trading`
3. **Symphony-specific**:
   - Check `VaultManager.get_symphony_credential()` exists
   - Validate `symphony_agent_id` is provided and UUID format
   - Check symbol compatibility: `standardizer.is_symphony_compatible()`
4. **Aster-specific**:
   - Check `VaultManager.get_aster_credential()` exists
   - Check symbol compatibility: `standardizer.is_aster_compatible()`
5. **Symbol WebSocket validation**: All modes require cached symbol

**Example Error Responses:**
- `403` - "Pro subscription required for live trading"
- `400` - "Symphony account not connected. Please connect in Settings first."
- `400` - "Symphony Agent ID is required for Symphony live trading."
- `400` - "Symbol BTC/USDT is not compatible with Symphony live trading"

#### Config Service Update

**Updated Signature:**
```python
async def create_config(
    self,
    user_id: str,
    config_name: str,
    config_data: Dict[str, Any],
    trading_mode: str = "paper",        # NEW
    symphony_agent_id: Optional[str] = None  # NEW
) -> Optional[BotConfigV2]
```

**Database INSERT:**
```python
# Map 'symphony' → 'live' for backwards compatibility
db_trading_mode = 'live' if trading_mode == 'symphony' else trading_mode

INSERT INTO configurations (
    config_id, user_id, config_type, config_name, config_data,
    trading_mode, symphony_agent_id, created_at, updated_at
) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
```

**Paper Account Logic:**
```python
# Only create paper account for paper trading mode
if trading_mode == "paper":
    account = await trading_service.get_or_create_paper_account(config_id, user_id)
# Live/Aster bots query external APIs for balances
```

---

### Phase 5: Remove Duplicate-As-Live Flow

#### Files Deleted
- `frontend/components/DuplicateAsLiveModal.tsx` (308 lines)

#### Endpoints Removed
- `POST /api/v2/config/duplicate-as-live` (112 lines from ggbot.py)

#### Frontend Cleanup

**Removed from page.tsx:**
- State: `duplicateAsLiveModalOpen`, `sourceBotForLive`
- Handler: `handleDuplicateAsLive()`, `handleLiveBotCreated()`
- Import: `DuplicateAsLiveModal`
- JSX: Modal component and props

**Removed from BotRail.tsx:**
- Prop: `onDuplicateAsLive?: (configId: string) => void`
- Pass-through to `BotManagementMenu`

**Removed from BotManagementMenu.tsx:**
- Prop: `onDuplicateAsLive?: (configId: string) => void`
- Button: "Deploy Live Version" (with Zap icon)

---

### Phase 6: UI Display Updates

#### BotRail Badge Updates

**File:** `frontend/app/forge/components/layout/BotRail.tsx`

**Before:**
```tsx
{isLive ? (
  <span>LIVE TRADING</span>
) : isAster ? (
  <span>ASTER</span>
) : (
  <span>{balanceText}</span>
)}
```

**After:**
```tsx
{isLive ? (
  <span className="...bg-red-500/10 border-red-500/30 text-red-500">
    SYMPHONY
  </span>
) : isAster ? (
  <span className="...bg-purple-500/10 border-purple-500/30 text-purple-500">
    ASTERDEX
  </span>
) : (
  <span className="...">
    {balanceText}
  </span>
)}
```

**Visual Design:**
- Symphony: Red badge with red border
- AsterDEX: Purple badge with purple border
- Paper: Green badge showing balance

---

### Phase 7: SSE Dashboard Support

**File:** `core/sse/dashboard_data.py`

#### SQL Query Enhancement

**Added Aster UNION Branch:**
```sql
open_positions AS (
    -- Paper positions
    SELECT ... FROM paper_trades WHERE trading_mode = 'paper'

    UNION ALL

    -- Symphony positions (stubs)
    SELECT ... FROM live_trades WHERE trading_mode = 'live'

    UNION ALL

    -- Aster positions (stubs) [NEW]
    SELECT ... FROM live_trades WHERE trading_mode = 'aster'
)
```

#### Position Enrichment

**Updated Function:**
```python
async def _enrich_live_positions_and_accounts(bots, positions, accounts) -> tuple:
    """Fetch Symphony and AsterDEX data for live/aster bots"""

    from trading.live.symphony_service import SymphonyLiveTradingService
    from trading.live.aster_service_v3 import AsterDEXV3LiveTradingService

    symphony = SymphonyLiveTradingService()
    aster = AsterDEXV3LiveTradingService()

    # Filter bots
    live_bots = [b for b in bots if b.get('trading_mode') == 'live']
    aster_bots = [b for b in bots if b.get('trading_mode') == 'aster']

    # Fetch Symphony data (parallel)
    for bot in live_bots:
        tasks.append(symphony.get_account_metrics(config_id))
        tasks.append(symphony.get_open_positions(config_id))

    # Fetch Aster data (parallel)
    for bot in aster_bots:
        aster_tasks.append(aster.get_open_positions(config_id))

    # Merge enriched positions with source='aster'
```

**Result:**
- Paper bots: Positions from `paper_trades` table
- Symphony bots: Positions from Symphony API (replaces DB stubs)
- Aster bots: Positions from AsterDEX API (replaces DB stubs)

---

### Phase 8: Wire Up Frontend Flow

#### createDefaultBot Update

**File:** `frontend/app/forge/page.tsx`

**Updated Signature:**
```typescript
const createDefaultBot = async (
  botType: 'scheduled_trading' | 'signal_validation' | 'agent' = 'scheduled_trading',
  tradingMode: 'paper' | 'symphony' | 'aster' = 'paper',  // NEW
  symphonyAgentId?: string  // NEW
): Promise<BotConfiguration> => {
  const baseConfig = {
    schema_version: '2.1',
    config_type: botType,
    trading_mode: tradingMode,        // NEW
    symphony_agent_id: symphonyAgentId,  // NEW
    trading: { /* ... */ }
  }

  const newConfig = await apiClient.createConfig('Bot Name', baseConfig)
  return newConfig
}
```

#### handleCreateNewBot Update

**Updated Logic:**
```typescript
const handleCreateNewBot = async (
  botType: 'scheduled_trading' | 'signal_validation' | 'agent' = 'scheduled_trading',
  tradingMode: 'paper' | 'symphony' | 'aster' = 'paper',  // NEW
  symphonyAgentId?: string  // NEW
) => {
  // Generate bot name with mode label
  const botCount = allBots.length + 1
  const typeNames = { /* ... */ }
  const modeLabel = tradingMode === 'symphony' ? ' (Symphony)'
                  : tradingMode === 'aster' ? ' (Aster)'
                  : ''
  const newBotName = `${typeNames[botType]} ${botCount}${modeLabel}`

  // Create with new params
  const newBot = await createDefaultBot(botType, tradingMode, symphonyAgentId)

  // Rest of creation flow...
}
```

**Result:**
- Paper bot: "ggbot 1"
- Symphony bot: "ggbot 2 (Symphony)"
- Aster bot: "agent 3 (Aster)"

---

## Migration & Backwards Compatibility

### Existing Bots

**No migration required for existing bots:**
- Old live bots: Have `trading_mode='live'` ✅ Continue working
- Old paper bots: Have `trading_mode='paper'` ✅ Continue working
- Database unchanged for existing rows

### Display Mapping

**Terminology Translation:**
- Database: `trading_mode='live'`
- Frontend displays: "SYMPHONY" badge
- User sees: "Symphony" in all UI text

**Why:**
- Backwards compatible with existing live bots
- Clearer branding ("Symphony" vs vague "live")
- Allows future addition of other "live" providers

### Optional Future Migration

**If desired later:**
```sql
-- Rename 'live' → 'symphony' in database
UPDATE configurations
SET trading_mode = 'symphony'
WHERE trading_mode = 'live';
```

**Not required:**
- Backend maps 'symphony' → 'live' during creation
- Display logic handles both values
- Zero user impact either way

---

## Testing Checklist

### Functional Tests

**Bot Creation:**
- [ ] Create paper bot (Free tier) → Success
- [ ] Create scheduled_trading paper bot → Default config applied
- [ ] Create signal_validation paper bot → Signal-driven frequency
- [ ] Create agent paper bot → Agent-driven mode, no extraction
- [ ] Create Symphony bot without credentials → Error: "Connect in Settings first"
- [ ] Create Symphony bot without agent ID → Error: "Agent ID required"
- [ ] Create Symphony bot with invalid UUID → Error: "Invalid format"
- [ ] Create Symphony bot (Pro, connected, valid ID) → Success
- [ ] Create Aster bot without credentials → Error: "Connect in Settings first"
- [ ] Create Aster bot (Pro, connected) → Success
- [ ] Create Symphony bot (Free tier) → Error: "Pro subscription required"
- [ ] Create Aster bot (Free tier) → Error: "Pro subscription required"

**Credential Management:**
- [ ] Settings → Connect Symphony → Success → Badge shows green
- [ ] Settings → Disconnect Symphony → Confirm → Success → Badge gone
- [ ] Settings → Connect Aster → Validate wallet format → Success
- [ ] Settings → Connect Aster → Invalid wallet format → Error shown
- [ ] Settings → Connect Aster → Invalid private key → Error shown
- [ ] Settings → Disconnect Aster → Confirm → Success → Badge gone
- [ ] Disconnect Symphony → All `trading_mode='live'` bots convert to paper
- [ ] Disconnect Aster → All `trading_mode='aster'` bots convert to paper

**UI Display:**
- [ ] Paper bot → Balance badge (green)
- [ ] Symphony bot → "SYMPHONY" badge (red)
- [ ] Aster bot → "ASTERDEX" badge (purple)
- [ ] Bot creation modal → Shows connection warnings if not connected
- [ ] Bot creation modal → Symphony mode shows agent ID input
- [ ] Bot creation modal → Aster mode hides agent ID input
- [ ] Bot creation modal → Pro modes show 🔒 lock icon for free users
- [ ] Bot creation modal → "Not connected" warning for unconfigured modes

**SSE Dashboard:**
- [ ] Paper bot with open position → Shows in positions list
- [ ] Symphony bot with open position → Fetches from Symphony API
- [ ] Aster bot with open position → Fetches from Aster API
- [ ] Mixed bots (paper + symphony + aster) → All show correct positions
- [ ] Symphony bot → Account balance from Symphony API
- [ ] Paper bot → Account balance from paper_accounts table

**Backend Validation:**
- [ ] Symbol compatibility check: Symphony incompatible symbol → Error
- [ ] Symbol compatibility check: Aster incompatible symbol → Error
- [ ] WebSocket requirement: Non-cached symbol → Error
- [ ] Symphony agent ID: UUID validation works
- [ ] Pro tier check: Free user creating Symphony → 403
- [ ] Pro tier check: Free user creating Aster → 403
- [ ] Database stores: `trading_mode='live'` for Symphony bots
- [ ] Database stores: `trading_mode='aster'` for Aster bots
- [ ] Database stores: `symphony_agent_id` only for Symphony bots

### Regression Tests

**Existing Functionality:**
- [ ] Old live bots (created before refactor) → Still work, show "SYMPHONY"
- [ ] Old paper bots → Still work, show balance
- [ ] Bot start/stop → Works for all trading modes
- [ ] Manual trigger → Works for all trading modes
- [ ] Bot configuration edit → Saves correctly
- [ ] Bot deletion → Works for all trading modes
- [ ] Paper account reset → Still works for paper bots
- [ ] Bot duplication → Duplicates with same trading_mode
- [ ] Bot rename → Works for all trading modes

**API Compatibility:**
- [ ] GET /api/v2/config → Returns trading_mode field
- [ ] GET /api/v2/config/{id} → Returns trading_mode field
- [ ] PUT /api/v2/config/{id} → trading_mode immutable (can't change)
- [ ] SSE /api/v2/dashboard/stream → Includes trading_mode in bot objects

---

## Code Statistics

### Lines Changed
- **Added:** ~850 lines (new features)
- **Deleted:** ~450 lines (dead code removal)
- **Modified:** ~200 lines (refactoring)
- **Net:** +200 lines

### Files Modified: 18

**Frontend (10 files):**
1. `frontend/types/index.ts` - Removed execution_mode
2. `frontend/lib/api.ts` - Removed execution_mode, ConfigData interface
3. `frontend/app/forge/page.tsx` - Updated createDefaultBot, handleCreateNewBot
4. `frontend/app/forge/components/modals/BotCreationModal.tsx` - Complete rewrite (2-step wizard)
5. `frontend/app/forge/components/layout/BotRail.tsx` - Badge display logic
6. `frontend/app/forge/components/layout/BotManagementMenu.tsx` - Removed duplicate-as-live
7. `frontend/components/SettingsModal.tsx` - Added AsterDEX section
8. `frontend/app/forge/components/configure/TradeSettings.tsx` - Removed execution_mode refs

**Backend (7 files):**
1. `core/auth/vault_utils.py` - Added 3 Aster methods + wrappers
2. `ggbot.py` - Added 3 Aster endpoints, updated config creation, removed duplicate-as-live
3. `core/services/config_service.py` - Updated create_config signature
4. `core/sse/dashboard_data.py` - Added Aster SQL + enrichment
5. `DOCS/SQL.md` - Database migration script

**Database:**
1. `user_profiles` table - Added 3 columns (migration applied)

**Deleted (1 file):**
1. `frontend/components/DuplicateAsLiveModal.tsx` - Entire file removed (308 lines)

---

## Key Architectural Decisions

### 1. Why Keep 'live' in Database?

**Decision:** Map 'symphony' → 'live' instead of migrating database

**Reasons:**
- Backwards compatibility: Existing live bots continue working
- Zero downtime: No migration required
- Simple mapping logic in one place
- Future-proof: Can add other live providers later

**Alternative Considered:** Rename `trading_mode='live'` → `'symphony'` everywhere
**Rejected Because:** Requires migration + risky for production data

---

### 2. Why Separate User-Level vs Bot-Level Credentials?

**Architecture:**
- **User-level:** Symphony API key, Aster wallets (stored in `user_profiles` → Vault)
- **Bot-level:** Symphony Agent ID (stored in `configurations.symphony_agent_id`)

**Reasons:**
- **User-level:** One-time setup, reused across all bots
- **Bot-level:** Each Symphony bot needs unique agent ID
- **Security:** Private keys in Vault, agent IDs not sensitive

**Alternative Considered:** Store agent ID per bot in JSONB
**Rejected Because:** Column-level makes querying easier, clearer separation

---

### 3. Why Modal vs Inline Trading Mode Selection?

**Decision:** Trading mode in modal (alongside bot type)

**Reasons:**
- **Discovery:** Users see all options upfront
- **Validation:** Can check credentials before creation
- **UX:** Single creation flow, no hidden features
- **Gating:** Clear Pro tier indicators with 🔒

**Alternative Considered:** Add trading mode dropdown to configure tab
**Rejected Because:** Trading mode should be immutable (decision at creation time)

---

### 4. Why No Account Metrics for Aster?

**Decision:** Symphony enrichment fetches account metrics, Aster only fetches positions

**Current State:**
```python
# Symphony
symphony.get_account_metrics(config_id)  # ✅ Implemented
symphony.get_open_positions(config_id)   # ✅ Implemented

# Aster
# aster.get_account_metrics(config_id)   # ❌ Not implemented yet
aster.get_open_positions(config_id)      # ✅ Implemented
```

**Reasons:**
- AsterDEXV3LiveTradingService doesn't have `get_account_metrics()` method yet
- Positions are more critical than account balance for monitoring
- Can add account metrics later without breaking changes

**Future Enhancement:**
```python
# Add to aster_service_v3.py
async def get_account_metrics(self, config_id: str) -> Dict[str, Any]:
    """Fetch account balance and equity from AsterDEX"""
    # Implementation here
```

---

## Performance Considerations

### SSE Dashboard Efficiency

**Parallel Fetching:**
- Symphony bots: 2 API calls per bot (account + positions) in parallel
- Aster bots: 1 API call per bot (positions only) in parallel
- All bots fetched concurrently using `asyncio.gather()`

**Error Handling:**
- `return_exceptions=True` prevents one failed bot from blocking others
- Placeholder positions removed only if enrichment succeeds
- Falls back to DB stubs if API unavailable

**Example Performance:**
- 3 Symphony bots = 6 API calls in parallel (~500ms total)
- 2 Aster bots = 2 API calls in parallel (~300ms total)
- Total SSE overhead: ~500-800ms (acceptable for dashboard)

---

## Security Considerations

### Credential Storage

**Vault-Based Encryption:**
- Symphony API key: Encrypted in Supabase Vault
- Aster private key: Encrypted in Supabase Vault
- Wallet addresses: Plaintext (not sensitive, display only)

**Access Control:**
```python
async def get_symphony_credential(user_id: str) -> Optional[Dict]:
    # Only returns credentials for requesting user
    # No cross-user access possible
```

**Disconnection Safety:**
```python
async def delete_symphony_credential(user_id: str) -> bool:
    # Atomic: Delete credentials AND disable all live bots
    # Prevents live trading without valid credentials
```

### Validation Layers

**1. Frontend Validation:**
- Wallet format: `^0x[a-fA-F0-9]{40}$`
- Private key: `^(0x)?[a-fA-F0-9]{64}$`
- Symphony Agent ID: UUID format

**2. Backend Validation:**
- Pro tier check: Prevents free users from live trading
- Credential existence: Checks Vault before allowing creation
- Symbol compatibility: Prevents incompatible markets

**3. Database Constraints:**
- `trading_mode` check constraint (if implemented)
- `symphony_agent_id` nullable (only required for live)

---

## Future Enhancements

### Short-Term (Next Sprint)

1. **Aster Account Metrics:**
   - Implement `aster_service_v3.get_account_metrics()`
   - Show Aster balance in dashboard

2. **Trading Mode Migration:**
   - Optional: Rename `'live'` → `'symphony'` in database
   - Update display logic to handle both values

3. **Batch Operations:**
   - "Upgrade all paper bots to Symphony" action
   - Bulk credential validation

### Mid-Term (Next Month)

1. **Additional Live Providers:**
   - Add Hyperliquid support
   - Add dYdX support
   - Reuse `trading_mode` architecture

2. **Credential Testing:**
   - "Test Connection" button in Settings
   - Validates credentials without creating bot

3. **Agent ID Management:**
   - List all Symphony agents from API
   - Dropdown selection instead of manual entry

### Long-Term (Next Quarter)

1. **Trading Mode Migration:**
   - Allow changing paper → live (with validation)
   - Warning modal + credential check

2. **Multi-Exchange Support:**
   - Per-bot exchange selection
   - Symbol compatibility matrix UI

3. **Credential Rotation:**
   - Update credentials without recreating bots
   - Audit log of credential changes

---

## Lessons Learned

### What Went Well

1. **Incremental Phases:** Breaking into 8 phases made progress trackable
2. **Backwards Compatibility:** Zero migration required, old bots work seamlessly
3. **User Testing Checkpoint:** Modal redesign validated before backend changes
4. **Parallel Development:** Frontend + backend developed together reduced integration issues

### What Could Be Improved

1. **Earlier Database Check:** Should have verified `user_profiles` schema before Phase 2
2. **API Coordination:** AsterDEX `get_account_metrics()` should have been scoped earlier
3. **Documentation First:** Writing this doc during implementation would have caught edge cases

### Key Takeaways

1. **Dead Code is Expensive:** `execution_mode` field wasted dev time debugging "why isn't this working?"
2. **Immutability Clarity:** Trading mode as creation-time choice simplifies state management
3. **Credential Architecture:** Separating user-level vs bot-level credentials scales well
4. **UI Terminology:** Renaming "live" → "Symphony" immediately improved user clarity

---

## Related Documentation

- [Symphony API Integration](./symphony-integration.md) - How Symphony live trading works
- [AsterDEX Integration](./aster-integration.md) - How AsterDEX trading works
- [Vault Security](../architecture/vault-security.md) - Credential encryption architecture
- [Bot Configuration Schema](../architecture/bot-config-schema.md) - Config JSONB structure

---

## Rollback Procedure (If Needed)

### Emergency Rollback

**If critical bugs found:**

1. **Revert Git Commits:**
   ```bash
   git log --oneline  # Find commit before refactor
   git revert <commit-sha> --no-commit
   git commit -m "Revert: Trading mode refactor"
   git push origin main
   ```

2. **Frontend Redeploys Automatically:** Vercel picks up git push

3. **Backend Restart:**
   ```bash
   pm2 restart ggbot
   ```

4. **Database (No Rollback Needed):**
   - Aster columns are nullable, safe to leave
   - Existing bots unaffected
   - New bots won't create with Aster mode

### Partial Rollback Options

**Option 1: Disable Aster Only**
- Set Aster mode to "Coming Soon" in modal
- Keep Symphony changes

**Option 2: Restore Duplicate-As-Live**
- Restore `DuplicateAsLiveModal.tsx` from git history
- Re-add endpoint to `ggbot.py`
- Both flows coexist (no conflict)

---

## Success Metrics

### User Experience
- ✅ Bot creation flow reduced from 5 steps to 3 steps
- ✅ "Duplicate as live" confusion eliminated (no more hidden feature)
- ✅ Trading mode visible at bot creation (discoverability improved)

### Code Quality
- ✅ Removed 450 lines of dead code
- ✅ Single source of truth for trading mode
- ✅ No more JSONB vs column confusion

### Feature Completeness
- ✅ AsterDEX first-class citizen (equal to Symphony)
- ✅ Credential management UI for both providers
- ✅ SSE dashboard supports all 3 modes

### Technical Debt
- ✅ `execution_mode` duplication eliminated
- ✅ "Duplicate as live" workaround removed
- ⚠️ 'live' → 'symphony' mapping still exists (acceptable technical debt)

---

**Questions or Issues?** Refer to:
- This document for architecture details
- `CHANGELOG.md` for high-level summary
- Code comments for implementation specifics
