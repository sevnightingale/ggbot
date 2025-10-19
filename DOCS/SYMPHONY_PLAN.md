# Symphony.io Live Trading - Elegant Integration Plan

**Philosophy**: Symphony owns positions, ggbots owns decisions. Thin wrapper, not feature duplication.

**Timeline**: 8 days to production-ready MVP (Day 0-7)

**Status**: Planning → Implementation

**Symbol Support**: 100 Symphony-compatible symbols (out of 141 ggbots symbols)

**Design Philosophy**: Lean MVP with minimal database schema, idempotency protection, and Symphony as source of truth.

---

## Key Design Decisions

✅ **Minimal Database Schema**: 5-field `live_trades` table (batch_id, config_id, decision_id, timestamps) - no status tracking, Symphony is source of truth
✅ **Idempotency Protection**: `UNIQUE(decision_id)` constraint prevents double-trades on network timeouts
✅ **Single Index**: Only index `config_id` for main query pattern ("get trades for this bot")
✅ **Smart Account Collected**: Stored for future balance display feature, clearly explained to users as "not required for trading"
✅ **3-Second Settlement**: Wait after trade submission, query final state, ensures entryPrice > 0
✅ **No Upfront Validation**: Let Symphony reject trades with informative errors ($5 minimum, 1.1x leverage, etc.)

---

## Core Principles

1. **Symphony is Source of Truth**: All position data lives in Symphony, we query on-demand
2. **Minimal Database**: Only track what we need to link decisions → executions
3. **No Feature Duplication**: Don't re-implement Symphony's risk management, monitoring, balance tracking
4. **Fast to Market**: Ship minimal MVP, iterate based on real user feedback
5. **Clean Separation**: We make decisions, Symphony executes
6. **Locked Trading Mode**: Paper vs Live is set at bot creation, never changes (staging → production pattern)

---

## Architecture Overview

```
AI Decision Engine (ggbots)
    ↓
Trading Router (mode check)
    ↓
Symphony Service (thin wrapper)
    ↓
Symphony API (position lifecycle)
```

**Data Flow**:
- **Open Trade**: Decision → Symphony API → Save batch_id → Return
- **View Positions**: Query Symphony API → Enrich with decision context → Display
- **Close Trade**: Get batch_id → Symphony API → Update closed timestamp

**Storage**: We only store `(batch_id, config_id, decision_id, timestamps)` - everything else from Symphony.

---

## Key Implementation Details (Verified via API Testing)

### Symbol Support
- **100 Symphony-compatible symbols** out of 141 ggbots symbols
- Source: `core/services/websocket_market_data_service.py::SYMBOLS`
- **Symbol conversion**: Uses existing `UniversalSymbolStandardizer`
  - `BTC-USDT` (platform) → `BTC` (Symphony API)
  - `SOL` (Symphony response) → `SOL-USDT` (platform)
- **Registry extended**: Added `symphony` and `symphony_compatible` fields

### API Response Field Mapping (Real Data)
Symphony API returns different field names than expected:
```python
# Symphony Response Structure
{
    "asset": "SOL",        # NOT "symbol"
    "isLong": true,        # NOT "side"
    "entryPrice": 123.45,  # camelCase
    "currentPrice": 125.67,
    "pnlUSD": 12.34,       # camelCase
    # ... other fields
}
```
Service must convert these to platform format.

### Position Settlement
- **3-second wait** after `batch-open` for position to settle
- Query `/agent/batch-positions` to verify `entryPrice > 0`
- Status tracking: `pending` → `filled` → `closed`
- Handled in Symphony service layer (orchestrator doesn't know)

### Validation Strategy
- **No upfront validation** - let Symphony API reject trades
- Symphony enforces: $5 minimum, 1.1x minimum leverage
- Show Symphony's error messages to users
- Add validation in Week 2 based on real error frequency

### Smart Account
- Stored in database for future balance queries
- **NOT used in API calls** (only API key required)
- Enables future `/agent/all-positions?userAddress=X` endpoint
- **UX consideration**: Tooltip explains "Used for future balance display features. Not required for trading."

### Idempotency Strategy
- `UNIQUE(decision_id)` constraint on `live_trades` table
- Before submitting to Symphony, check if `decision_id` already has `batch_id`
- Prevents duplicate trades on network timeout → retry scenarios
- Returns `{"status": "already_executed", "batch_id": "..."}` if found

---

## User Journey: Paper → Live

### The Elegant Flow

**Phase 1: Testing with Paper Trading**
1. User creates bot: "BTC Scalper"
2. Selects "📄 Paper Trading" mode at creation
3. Configures strategy, runs for a week
4. Reviews 15 simulated trades in dashboard
5. Average P&L: +2.3% - "This looks good!"

**Phase 2: Going Live**
1. User clicks "Create Live Version" button in bot settings
2. Modal appears:
   - New bot name: "BTC Scalper (Live)" (auto-suggested)
   - Symphony Agent ID: [paste here]
   - Warning: "This bot will use real capital"
3. User creates new agent in Symphony portal
4. Pastes agent ID, clicks "Create Live Bot"
5. Result: **Two independent bots in dashboard**
   - 📄 BTC Scalper (Paper) - keeps running with history intact
   - 🔴 BTC Scalper (Live) - clean slate, ready for real trades

**Phase 3: Running & Comparing**
1. Both bots receive same market signals
2. Both execute independently (paper vs live)
3. User switches between bots in dashboard to compare:
   - Paper bot: Shows simulated positions (+$350 P&L)
   - Live bot: Shows real positions (+$28.50 P&L)
4. Same strategy, different execution - validates paper trading accuracy

**Benefits of This Approach:**
- **Clear separation**: Paper = staging, Live = production
- **Non-destructive**: Original paper bot untouched
- **Side-by-side testing**: Run both simultaneously
- **Safe by default**: Can't accidentally switch modes
- **Familiar pattern**: Like GitHub fork or software deployment

---

## Implementation Plan

### Day 0: Symbol System Extension & Premium Gating

**Objective**: Extend Universal Symbol Standardizer with Symphony format support and configure premium features.

#### Symbol System Updates (✅ COMPLETE)

**Extend `core/symbols/registry.py`**:
- ✅ Added `"symphony": "BTC"` field to all 100 compatible symbols
- ✅ Added `"symphony_compatible": true/false` boolean to all 142 symbols
- ✅ 100 Symphony-compatible symbols (from WebSocket market data service)
- ✅ 42 incompatible symbols (paper trading only)

**Extend `core/symbols/standardizer.py`** (✅ COMPLETE):
```python
# New methods added
def to_symphony(self, platform_symbol: str) -> Optional[str]:
    """Convert BTC-USDT → BTC"""

def from_symphony(self, symphony_symbol: str) -> Optional[str]:
    """Convert BTC → BTC-USDT"""

def is_symphony_compatible(self, symbol: str, format_type: str = "platform") -> bool:
    """Check if symbol supports Symphony live trading"""
```

**Usage in Symphony Service**:
```python
from core.symbols import UniversalSymbolStandardizer

standardizer = UniversalSymbolStandardizer()

# Convert platform → Symphony for API calls
platform_symbol = "BTC-USDT"
symphony_symbol = standardizer.to_symphony(platform_symbol)  # "BTC"

# Check compatibility
is_compatible = standardizer.is_symphony_compatible("BTC-USDT")  # True

# Convert Symphony response → platform format
position_symbol = standardizer.from_symphony(response["asset"])  # "SOL" → "SOL-USDT"
```

---

### Day 1: Premium Gating & Settings Modal

**Objective**: Add Symphony to premium features and create Settings modal for account connection.

#### Premium Feature Configuration

**Add to permissions system** (`/frontend/lib/permissions.tsx`):

```typescript
// Add 'live_trading' to feature descriptions (line ~75)
const descriptions: Record<string, string> = {
  'signals': 'signal trading',
  'ggshot': 'ggShot signals',
  'telegram_publishing': 'Telegram publishing',
  'premium_llms': 'premium AI models',
  'live_trading': 'live trading via Symphony.io',  // NEW
  // ... existing features
}
```

**Backend permission check**:

Add to `/ggbot.py` or permissions module:
```python
def can_use_live_trading(user_profile: dict) -> bool:
    """Check if user can create live trading bots."""
    return user_profile.get('subscription_tier') == 'ggbase'
```

---

#### Settings Modal Component

**Create**: `/frontend/components/SettingsModal.tsx`

```typescript
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useState } from 'react'
import { usePermissions } from '@/lib/permissions'
import { Crown, Link2, CheckCircle2 } from 'lucide-react'

interface SettingsModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function SettingsModal({ open, onOpenChange }: SettingsModalProps) {
  const { userProfile } = usePermissions()
  const isPro = userProfile?.subscription_tier === 'ggbase'

  const [symphonyConnected, setSymphonyConnected] = useState(false)
  const [apiKey, setApiKey] = useState('')
  const [smartAccount, setSmartAccount] = useState('')
  const [connecting, setConnecting] = useState(false)
  const [error, setError] = useState('')

  const handleConnect = async () => {
    setConnecting(true)
    setError('')

    try {
      const response = await fetch('/api/v2/symphony/setup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey, smart_account: smartAccount })
      })

      if (response.ok) {
        setSymphonyConnected(true)
        setApiKey('')  // Clear sensitive data
        // Refresh to update UI
        window.location.reload()
      } else {
        const data = await response.json()
        setError(data.message || 'Failed to connect')
      }
    } catch (e) {
      setError('Connection error. Please try again.')
    } finally {
      setConnecting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Subscription Section */}
          <section>
            <h3 className="text-sm font-medium mb-3">Subscription</h3>
            <div className="flex items-center justify-between p-4 border rounded-lg bg-[var(--bg-secondary)]">
              <div>
                <p className="font-medium">Current Plan</p>
                <div className="mt-1">
                  {isPro ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/20 px-2 py-1 text-xs font-medium text-amber-500">
                      <Crown className="h-3 w-3" />
                      Pro Plan
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 rounded-full bg-[var(--bg-tertiary)] px-2 py-1 text-xs font-medium text-[var(--text-secondary)]">
                      Free Plan
                    </span>
                  )}
                </div>
              </div>
              {isPro ? (
                <a
                  href={process.env.NEXT_PUBLIC_STRIPE_CUSTOMER_PORTAL}
                  target="_blank"
                  className="text-sm text-[var(--text-link)] hover:underline"
                >
                  Manage Billing →
                </a>
              ) : (
                <button
                  onClick={() => {/* trigger upgrade modal */}}
                  className="px-4 py-2 bg-amber-500 text-white rounded-lg text-sm font-medium hover:bg-amber-600"
                >
                  Upgrade to Pro
                </button>
              )}
            </div>
          </section>

          {/* Symphony Live Trading Section */}
          <section>
            <h3 className="text-sm font-medium mb-3">Symphony Live Trading</h3>

            {!symphonyConnected ? (
              <div className="border border-dashed rounded-lg p-6">
                <div className="flex items-start gap-3 mb-4">
                  <Link2 className="h-5 w-5 text-[var(--text-secondary)] mt-0.5" />
                  <div>
                    <p className="font-medium mb-1">Connect Symphony Account</p>
                    <p className="text-sm text-[var(--text-secondary)]">
                      Execute real trades via Symphony.io with your AI strategies
                    </p>
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Symphony API Key
                    </label>
                    <input
                      type="password"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="sk_live_..."
                      className="w-full px-3 py-2 border rounded-lg bg-[var(--bg-primary)]"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Smart Account Address
                    </label>
                    <input
                      value={smartAccount}
                      onChange={(e) => setSmartAccount(e.target.value)}
                      placeholder="0x..."
                      className="w-full px-3 py-2 border rounded-lg bg-[var(--bg-primary)]"
                    />
                    <p className="text-xs text-[var(--text-secondary)] mt-1">
                      Find in{' '}
                      <a
                        href="https://agent-portal.symphony.io"
                        target="_blank"
                        className="text-[var(--text-link)] hover:underline"
                      >
                        Symphony portal
                      </a>{' '}
                      under "My Agents"
                    </p>
                    <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                      💡 Used for future balance display features. Not required for trading.
                    </p>
                  </div>

                  {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                      {error}
                    </div>
                  )}

                  <button
                    onClick={handleConnect}
                    disabled={connecting || !apiKey || !smartAccount}
                    className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 disabled:opacity-50"
                  >
                    {connecting ? 'Connecting...' : 'Connect Account'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="border rounded-lg p-4 bg-green-50 dark:bg-green-950/20">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-medium text-green-900 dark:text-green-100 mb-1">
                      Symphony Connected
                    </p>
                    <p className="text-sm text-green-700 dark:text-green-300">
                      Smart Account: {smartAccount.slice(0, 6)}...{smartAccount.slice(-4)}
                    </p>
                  </div>
                  <button
                    onClick={() => {/* handle disconnect */}}
                    className="text-sm text-red-600 hover:underline"
                  >
                    Disconnect
                  </button>
                </div>
              </div>
            )}
          </section>
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

---

#### Add Settings to User Profile

**Update**: `/frontend/app/forge/components/layout/UserProfile.tsx`

Add "Settings" menu item before logout:

```typescript
// Around line 185, before the logout button
<button
  onClick={() => setSettingsOpen(true)}
  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] rounded-lg"
>
  <Settings className="h-4 w-4" />
  Settings
</button>

{/* Add state and modal */}
const [settingsOpen, setSettingsOpen] = useState(false)

<SettingsModal open={settingsOpen} onOpenChange={setSettingsOpen} />
```

---

### Day 2: Database & Vault

#### Database Schema Changes

**Extend `users` table**:
```sql
ALTER TABLE users
ADD COLUMN symphony_vault_id UUID REFERENCES vault.secrets(id),
ADD COLUMN symphony_smart_account VARCHAR(42);
```

**Purpose**:
- One Symphony account per user
- Vault ID points to encrypted API key
- Smart account stored for future balance queries (via `/agent/all-positions` endpoint)
- **Note**: Smart account NOT used in API calls, only stored for future features

---

**Extend `configurations` table**:
```sql
ALTER TABLE configurations
ADD COLUMN symphony_agent_id VARCHAR(255),
ADD COLUMN trading_mode VARCHAR(20) DEFAULT 'paper' CHECK (trading_mode IN ('paper', 'live'));
```

**Purpose**:
- Each bot config can have its own Symphony agent
- Mode is **locked at creation** - can't be changed after bot is created
- Default to safe mode (paper)
- Live bots require `symphony_agent_id` at creation
- **Symbol restriction**: Only Symphony-compatible symbols allowed for live bots (100 out of 141)

**UX Pattern**: Paper Bot (Staging) → Duplicate as Live Bot (Production)

---

**Create `live_trades` table** (Minimal Schema):
```sql
CREATE TABLE live_trades (
    batch_id VARCHAR(255) PRIMARY KEY,
    config_id UUID NOT NULL REFERENCES configurations(config_id),
    decision_id UUID REFERENCES decisions(decision_id),
    created_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP,  -- NULL = position is open

    -- Idempotency: Prevent double-trades on network timeouts
    UNIQUE(decision_id) WHERE decision_id IS NOT NULL
);

-- Single index for main query: "get trades for this bot"
CREATE INDEX idx_live_trades_config ON live_trades(config_id);
```

**Purpose**:
- Link Symphony `batch_id` to our `decision_id` (trace AI reasoning)
- Track when positions opened/closed (simple audit trail)
- **Idempotency protection**: `decision_id` uniqueness prevents duplicate trades on retries
- **Symphony is source of truth**: No status, entry_price, P&L, or asset stored - always query Symphony API for real-time data
- Minimal surface area: 5 fields, 1 index, fewer edge cases

---

#### Vault Integration

**Extend `core/auth/vault_utils.py`**:

Add 3 methods to `VaultManager` class:

**1. Store Symphony Credentials**
```python
async def store_symphony_credential(user_id: str, api_key: str, smart_account: str) -> bool:
    """
    Store Symphony API key in Vault, save smart account in users table.
    Returns True on success.
    """
    # Create vault secret: f"symphony_{user_id}"
    # Update users.symphony_vault_id and users.symphony_smart_account
    # Log success
```

**2. Get Symphony Credentials**
```python
async def get_symphony_credential(user_id: str) -> Optional[Dict]:
    """
    Retrieve decrypted Symphony API key.
    Returns {'api_key': str, 'smart_account': str} or None.
    """
    # Query users.symphony_vault_id
    # Retrieve from vault.decrypted_secrets
    # Return with smart account
```

**3. Delete Symphony Credentials**
```python
async def delete_symphony_credential(user_id: str) -> bool:
    """
    Mark Symphony credentials as inactive (keep for audit).
    Set all user's configs to trading_mode='paper'.
    Returns True on success.
    """
    # Set symphony_vault_id = NULL
    # Update all configurations SET trading_mode='paper'
    # Log deletion
```

**Security**: Same pattern as LLM credentials - API key never logged, only in Vault.

---

### Day 3: Symphony Service

**Create `trading/live/symphony_service.py`**

#### Service Class

```python
from core.symbols import UniversalSymbolStandardizer

class SymphonyLiveTradingService:
    """
    Thin wrapper around Symphony API with 3-second settling wait.

    Responsibilities:
    - Open positions via /agent/batch-open (with settlement wait)
    - Close positions via /agent/batch-close
    - Query positions via /agent/positions
    - Save minimal audit trail to database

    NOT Responsible For:
    - Position monitoring (Symphony handles)
    - Balance tracking (Symphony handles)
    - Risk management (Symphony handles)
    - P&L calculation (Symphony handles)
    - Trade size validation (let Symphony reject)
    """

    def __init__(self):
        self.base_url = "https://api.symphony.io"
        self.timeout = 30
        self.standardizer = UniversalSymbolStandardizer()
```

#### Three Core Methods

**1. Execute Trade Intent (with 3-Second Settlement)**

**Signature**:
```python
async def execute_trade_intent(intent: Dict) -> Dict
```

**Input** (from orchestrator):
```python
{
    "decision_id": str,
    "user_id": str,
    "config_id": str,
    "symbol": str,           # "BTC-USDT" (platform format)
    "action": str,           # "long" or "short"
    "confidence": float,     # 0.0 - 1.0
    "stop_loss_price": Optional[float],
    "take_profit_price": Optional[float],
    "reasoning": str
}
```

**Process**:
1. **Check idempotency**: Prevent double-trades on network timeouts
   ```python
   # Check if this decision already executed
   existing = db.query("""
       SELECT batch_id FROM live_trades WHERE decision_id = %s
   """, (intent["decision_id"],))

   if existing:
       logger.warning("Trade already executed", decision_id=intent["decision_id"])
       return {"status": "already_executed", "batch_id": existing["batch_id"]}
   ```
2. Load config from database (get symphony_agent_id, leverage)
3. Get API key from Vault via `VaultManager.get_symphony_credential(user_id)`
4. **Convert symbol using standardizer**: `"BTC-USDT"` → `"BTC"`
   ```python
   symphony_symbol = self.standardizer.to_symphony(intent["symbol"])
   if not symphony_symbol:
       return {"status": "failed", "error": f"Symbol {intent['symbol']} not supported by Symphony"}
   ```
5. Calculate weight: `confidence * 100` (e.g., 0.75 → 75% of balance)
6. Build Symphony payload:
   ```python
   {
       "agentId": config.symphony_agent_id,
       "symbol": symphony_symbol,  # "BTC"
       "action": "LONG" if intent["action"] == "long" else "SHORT",
       "weight": intent["confidence"] * 100,
       "leverage": max(1.1, config.trading.leverage),  # Enforce 1.1 minimum
       "orderOptions": {
           "stopLossPrice": stop_loss_price or 0,
           "takeProfitPrice": take_profit_price or 0,
           "triggerPrice": 0
       }
   }
   ```
7. POST to `/agent/batch-open` with header `x-api-key`
8. Extract `batchId` from response
9. **Wait 3 seconds for position to settle**:
   ```python
   logger.info(f"Position submitted, waiting 3s for settlement", batch_id=batch_id)
   await asyncio.sleep(3)
   ```
10. **Query final position state**:
    ```python
    position_data = await self._get(f"/agent/batch-positions?batchId={batch_id}")
    ```
11. **Validate position filled** (check entryPrice > 0)
12. Insert into `live_trades` (minimal schema):
    ```python
    INSERT INTO live_trades (
        batch_id, config_id, decision_id, created_at
    ) VALUES (
        batch_id, config_id, decision_id, NOW()
    )
    ```
13. Return result

**Output**:
```python
{
    "status": "filled" | "pending" | "failed",
    "batch_id": str,
    "entry_price": float,  # From Symphony response
    "filled_at": datetime,
    "error": Optional[str],
    "warning": Optional[str]  # If still pending after 3s
}
```

**Error Handling**:
- Symphony API errors (400/500): Return failed status with error message (e.g., "Trade size below $5 minimum")
- Network timeout: Retry once, then fail
- Invalid credentials: Clear error for user to reconfigure
- **No upfront validation** - let Symphony reject with informative errors

---

**2. Close Position**

**Signature**:
```python
async def close_position(batch_id: str, user_id: str) -> Dict
```

**Input**:
- `batch_id`: Symphony batch ID to close
- `user_id`: For getting API key

**Process**:
1. Get API key from Vault
2. Query `live_trades` to get `config_id` (need agent_id)
3. Get `symphony_agent_id` from configurations
4. Build payload:
```python
{
    "agentId": symphony_agent_id,
    "batchId": batch_id
}
```
5. POST to `/agent/batch-close`
6. Update database:
```python
UPDATE live_trades SET closed_at = NOW() WHERE batch_id = batch_id
```
7. Return result

**Output**:
```python
{
    "status": "success" | "failed",
    "error": Optional[str]
}
```

---

**3. Get Open Positions**

**Signature**:
```python
async def get_open_positions(config_id: str, user_id: str) -> List[Dict]
```

**Input**:
- `config_id`: Which bot's positions to query
- `user_id`: For getting API key

**Process**:
1. Get API key from Vault
2. Get `symphony_agent_id` from configurations
3. GET `/agent/positions?agentId={agent_id}&status=OPEN`
4. Parse Symphony response (correct field names from real API):
   ```python
   # Symphony returns this structure
   {
       "positions": [{
           "batchId": "uuid",
           "asset": "SOL",  # NOT "symbol"
           "isLong": true,  # NOT "side"
           "entryPrice": 123.45,
           "currentPrice": 125.67,
           "pnlUSD": 12.34,
           "pnlPercentage": 1.8,
           # ... other fields
       }]
   }
   ```
5. Join with `live_trades` on `batch_id` to get `decision_id`
6. **Convert Symphony format → platform format**:
   ```python
   for pos in symphony_response["positions"]:
       # Convert asset to platform format
       platform_symbol = self.standardizer.from_symphony(pos["asset"])  # "SOL" → "SOL-USDT"

       enriched_position = {
           # Converted fields
           "symbol": platform_symbol,
           "side": "long" if pos["isLong"] else "short",

           # Direct fields (camelCase → snake_case)
           "batch_id": pos["batchId"],
           "entry_price": pos["entryPrice"],
           "current_price": pos["currentPrice"],
           "pnl_usd": pos["pnlUSD"],
           "pnl_percentage": pos["pnlPercentage"],
           "collateral_amount": pos["collateralAmount"],
           "leverage": pos["leverage"],
           "position_size": pos["positionSize"],
           "created_timestamp": pos["createdTimestamp"],
           "stop_loss_price": pos["slPrice"],
           "take_profit_price": pos["tpPrice"],
           "liquidation_price": pos["liquidationPrice"],
           "status": pos["status"],

           # From our audit trail
           "decision_id": trade_map.get(pos["batchId"], {}).get("decision_id"),
           "config_id": config_id
       }
   ```
7. Return array of positions

**Output**: `List[Dict]` - enriched position data in platform format

**Note**: Always query Symphony live (no caching). This ensures accurate P&L.

---

### Day 3: Orchestrator Integration

**Modify `ggbot.py`**

#### Import Symphony Service

```python
from trading.live.symphony_service import SymphonyLiveTradingService

# In __init__
self.symphony_trading = SymphonyLiveTradingService()
```

#### Modify `_run_trading_v2()` Method

**Current Logic**: Always calls `paper_trading.execute_trade_intent()`

**New Logic** (add after line 832):

```python
async def _run_trading_v2(self, config, user_id, decision_result):
    # ... existing validation ...

    # Build trading intent (existing code)
    trading_intent = {...}

    # NEW: Route based on trading mode
    if config.trading_mode == "live":
        # Validate Symphony setup
        if not config.symphony_agent_id:
            self._log.error("Live trading enabled but no Symphony agent configured",
                          user_id=user_id, config_id=config.config_id)
            return {"status": "error", "message": "Configure Symphony agent first"}

        # Execute via Symphony
        result = await self.symphony_trading.execute_trade_intent(trading_intent)
        self._log.info("Live trade executed", user_id=user_id,
                      config_id=config.config_id, batch_id=result.get('batch_id'))
    else:
        # Default to paper trading
        result = await self.paper_trading.execute_trade_intent(trading_intent)
        self._log.info("Paper trade executed", user_id=user_id,
                      config_id=config.config_id, trade_id=result.get('trade_id'))

    return result
```

**That's it.** Both services return same structure, rest of orchestrator unchanged.

---

#### Position Management Integration

**For `position_management` mode**:

When decision engine analyzes positions and suggests closing:

```python
# In _run_trading_v2, handle close actions
if decision_result.get('action') == 'close':
    position_identifier = decision_result.get('position_id')  # batch_id or trade_id

    if config.trading_mode == "live":
        # Close via Symphony
        result = await self.symphony_trading.close_position(
            batch_id=position_identifier,
            user_id=user_id
        )
    else:
        # Close paper position
        result = await self.paper_trading.close_position(
            trade_id=position_identifier,
            reason="position_management"
        )

    return result
```

**Decision Engine Changes**: Need to pass open positions as context.

In orchestrator, before calling decision engine:
```python
if config.decision_mode == "position_management":
    # Get open positions based on mode
    if config.trading_mode == "live":
        open_positions = await self.symphony_trading.get_open_positions(config.config_id, user_id)
    else:
        open_positions = await self.paper_trading.get_open_positions(config.config_id)

    # Pass to decision engine as context
    decision_context['open_positions'] = open_positions
```

Decision engine can then suggest closing specific positions.

---

### Day 4: API Endpoints

**Add to `ggbot.py` FastAPI routes**

#### Endpoint 1: Symphony Account Setup

```python
@app.post("/api/v2/symphony/setup")
async def setup_symphony_account(
    api_key: str,
    smart_account: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Store Symphony credentials for user.
    Validates API key by testing /agent/positions call.
    """
    user_id = current_user['user_id']

    # Validate inputs
    if not api_key.startswith('sk_'):
        raise HTTPException(400, "Invalid API key format")

    if not re.match(r'^0x[a-fA-F0-9]{40}$', smart_account):
        raise HTTPException(400, "Invalid Ethereum address")

    # Test credentials (call Symphony API)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.symphony.io/agent/positions",
                headers={"x-api-key": api_key},
                params={"agentId": "test"}  # Will fail but validates key format
            ) as resp:
                # Even 404 is OK, just means valid key
                if resp.status in [200, 404]:
                    # Valid key
                    pass
                elif resp.status == 401:
                    raise HTTPException(401, "Invalid Symphony API key")
    except Exception as e:
        raise HTTPException(500, f"Failed to validate credentials: {str(e)}")

    # Store in Vault
    success = await VaultManager.store_symphony_credential(user_id, api_key, smart_account)

    if success:
        return {"status": "success", "smart_account": smart_account}
    else:
        raise HTTPException(500, "Failed to store credentials")
```

**What this does**:
- User submits API key + smart account address
- We validate format and test the key
- Store in Supabase Vault (encrypted)
- Return success

**Frontend calls this from**: Settings page "Connect Symphony Account" button

---

#### Endpoint 2: Get Symphony Status

```python
@app.get("/api/v2/symphony/status")
async def get_symphony_status(current_user: dict = Depends(get_current_user)):
    """
    Check if user has Symphony connected.
    Returns connection status without exposing API key.
    """
    user_id = current_user['user_id']

    # Query users table
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT symphony_vault_id, symphony_smart_account
                FROM users WHERE user_id = %s
            """, (user_id,))
            result = cur.fetchone()

    if result and result[0]:  # Has vault_id
        return {
            "connected": True,
            "smart_account": result[1]
        }
    else:
        return {"connected": False}
```

**What this does**:
- Check if user has Symphony configured
- Return status for UI (show connection badge)

**Frontend calls this from**: Settings page on load, Dashboard

---

#### Endpoint 3: Get Live Positions

```python
@app.get("/api/v2/positions/live/{config_id}")
async def get_live_positions(
    config_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get open live positions for a bot config.
    Queries Symphony API in real-time.
    """
    user_id = current_user['user_id']

    # Verify user owns this config
    # ... ownership check ...

    # Query Symphony
    positions = await symphony_trading.get_open_positions(config_id, user_id)

    return {"positions": positions}
```

**What this does**:
- Query Symphony API for positions
- Enrich with decision context
- Return for dashboard display

**Frontend calls this from**: Dashboard positions table

---

#### Endpoint 4: Close Live Position

```python
@app.post("/api/v2/positions/live/{batch_id}/close")
async def close_live_position(
    batch_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Manually close a live position.
    """
    user_id = current_user['user_id']

    # Verify user owns this position
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT lt.config_id, c.user_id
                FROM live_trades lt
                JOIN configurations c ON lt.config_id = c.config_id
                WHERE lt.batch_id = %s
            """, (batch_id,))
            result = cur.fetchone()

    if not result or result[1] != user_id:
        raise HTTPException(403, "Not your position")

    # Close via Symphony
    result = await symphony_trading.close_position(batch_id, user_id)

    return result
```

**What this does**:
- User clicks "Close" button in dashboard
- Verify ownership
- Call Symphony to close
- Update our database

**Frontend calls this from**: Position detail modal "Close Position" button

---

#### Endpoint 5: Duplicate as Live Bot

```python
@app.post("/api/v2/config/duplicate-as-live")
async def duplicate_config_as_live(
    source_config_id: str,
    new_name: str,
    symphony_agent_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a live trading version of a paper bot.
    Copies all config settings but sets trading_mode='live'.
    Does NOT copy position history.
    """
    user_id = current_user['user_id']

    # Verify user owns source config
    # ... ownership check ...

    # Load source config
    source_config = await config_repo.get_config(source_config_id)

    # Create new config as copy
    new_config = {
        **source_config,
        "config_id": str(uuid.uuid4()),
        "name": new_name,
        "trading_mode": "live",
        "symphony_agent_id": symphony_agent_id,
        "created_at": datetime.now()
    }

    # Save to database
    await config_repo.save_config(new_config)

    return {
        "status": "success",
        "config_id": new_config["config_id"],
        "name": new_name,
        "trading_mode": "live"
    }
```

**What this does**:
- User clicks "Create Live Version" in paper bot settings
- Copies all strategy settings (symbols, timeframe, LLM config, risk settings)
- Sets mode to "live" and adds Symphony agent ID
- Does NOT copy paper_trades (clean slate for live bot)
- Returns new config for frontend to redirect

**Frontend calls this from**: "Create Live Version" modal submit button

---

**That's All Endpoints We Need**

5 endpoints total:
1. Setup Symphony account (store credentials)
2. Get connection status (check if configured)
3. Get live positions (display in dashboard)
4. Close position (manual close)
5. Duplicate as live bot (create live version)

Simple, focused, no bloat.

---

### Day 5: Frontend - Settings Page

**File**: `frontend/app/forge/page.tsx` (main ForgeApp component)

#### Bot Creation with Mode Selection

**Update `handleCreateNewBot` function** (currently at line ~697):

**For now, keep bot creation simple - all bots default to paper.**

Users will create live versions via duplication (see below).

---

#### "Create Live Version" in Bot Management Menu

**Update**: `/frontend/app/forge/components/layout/BotManagementMenu.tsx`

Add menu item after "Duplicate":

```typescript
const { canAccess } = usePermissions()
const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)
const [createLiveModalOpen, setCreateLiveModalOpen] = useState(false)
const [liveAgentId, setLiveAgentId] = useState('')
const [symphonyConnected, setSymphonyConnected] = useState(false)

// Check Symphony connection on mount
useEffect(() => {
  fetch('/api/v2/symphony/status')
    .then(r => r.json())
    .then(data => setSymphonyConnected(data.connected))
}, [])

// In menu dropdown (after Duplicate button):
{bot.trading_mode === 'paper' && (
  <button
    onClick={() => {
      // Check premium access first
      if (!canAccess('live_trading')) {
        setUpgradeModalOpen(true)
        return
      }

      // Check Symphony connection
      if (!symphonyConnected) {
        alert('Connect Symphony account first in Settings')
        return
      }

      setCreateLiveModalOpen(true)
    }}
    className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-[var(--bg-secondary)]"
  >
    <Zap className="h-4 w-4 text-amber-500" />
    Create Live Version
  </button>
)}

{/* Create Live Version Dialog */}
<Dialog open={createLiveModalOpen} onOpenChange={setCreateLiveModalOpen}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Create Live Trading Bot</DialogTitle>
      <DialogDescription>
        Create a copy of "{bot.config_name}" that executes real trades via Symphony.io
      </DialogDescription>
    </DialogHeader>

    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1">Symphony Agent ID</label>
        <input
          value={liveAgentId}
          onChange={(e) => setLiveAgentId(e.target.value)}
          placeholder="22b35152-f3a5-4b21-8a0f-04691c155e33"
          className="w-full px-3 py-2 border rounded-lg bg-[var(--bg-primary)]"
        />
        <p className="text-xs text-[var(--text-secondary)] mt-1">
          Create a new agent in{' '}
          <a
            href="https://agent-portal.symphony.io"
            target="_blank"
            className="text-[var(--text-link)] hover:underline"
          >
            Symphony portal
          </a>
        </p>
      </div>

      <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3">
        <p className="text-sm text-amber-900 dark:text-amber-100">⚠️ This bot will use real capital</p>
        <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
          Your paper bot will continue running unchanged
        </p>
      </div>

      <DialogFooter>
        <button
          onClick={() => setCreateLiveModalOpen(false)}
          className="px-4 py-2 border rounded-lg"
        >
          Cancel
        </button>
        <button
          onClick={() => handleCreateLiveVersion(bot.config_id, liveAgentId)}
          disabled={!liveAgentId}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg disabled:opacity-50"
        >
          Create Live Bot
        </button>
      </DialogFooter>
    </div>
  </DialogContent>
</Dialog>

{/* Upgrade Modal */}
<UpgradeModal open={upgradeModalOpen} onOpenChange={setUpgradeModalOpen} />
```

#### Create Live Version Handler

**Add to `/frontend/app/forge/page.tsx` (ForgeApp component)**:

```typescript
const handleCreateLiveVersion = async (sourceConfigId: string, agentId: string) => {
  setIsBotAction(true)

  try {
    const originalBot = allBots.find(b => b.config_id === sourceConfigId)
    if (!originalBot) return

    const newName = `${originalBot.config_name} (Live)`

    const response = await fetch('/api/v2/config/duplicate-as-live', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_config_id: sourceConfigId,
        new_name: newName,
        symphony_agent_id: agentId
      })
    })

    if (!response.ok) {
      const error = await response.json()
      alert(error.message || 'Failed to create live bot')
      return
    }

    const newBot = await response.json()

    // Add to state and select
    setAllBots(prev => [...prev, newBot])
    setSelectedConfigId(newBot.config_id)

    // Close modal
    setCreateLiveModalOpen(false)

  } catch (error) {
    console.error('Failed to create live version:', error)
    alert('Failed to create live version')
  } finally {
    setIsBotAction(false)
  }
}
```

---

#### Show Mode Badge in Bot Display

**Update**: `/frontend/app/forge/components/layout/BotRail.tsx`

Add mode badge to bot list items:

```tsx
{/* In bot list item render */}
<div className="flex items-center justify-between">
  <span className="font-medium">{bot.config_name}</span>
  {bot.trading_mode === 'live' && (
    <span className="inline-flex items-center gap-1 rounded-full bg-red-100 text-red-700 px-2 py-0.5 text-xs font-medium">
      🔴 LIVE
    </span>
  )}
</div>
```

---

### Day 6: Frontend - Dashboard

**File**: `frontend/app/forge/components/dashboard/PositionsTable.tsx`

#### Clean Bot Selector & Position Display

**Key Change**: Each bot shows ONLY its mode's positions (no mixing).

**Bot Selector Enhancement**:

Add mode badge to config selector:

```tsx
{/* Config selector with mode badges */}
<select value={selectedConfigId} onChange={(e) => setSelectedConfigId(e.target.value)}>
  {configs.map(config => (
    <option key={config.config_id} value={config.config_id}>
      {config.trading_mode === 'live' ? '🔴' : '📄'} {config.name}
    </option>
  ))}
</select>

{/* Or as a more visual selector */}
<div className="grid grid-cols-1 gap-2">
  {configs.map(config => (
    <button
      key={config.config_id}
      onClick={() => setSelectedConfigId(config.config_id)}
      className={`p-3 border rounded text-left ${selectedConfigId === config.config_id ? 'border-blue-500 bg-blue-50' : ''}`}
    >
      <div className="flex items-center justify-between">
        <span className="font-medium">{config.name}</span>
        <span className={`text-xs px-2 py-1 rounded ${
          config.trading_mode === 'live'
            ? 'bg-red-100 text-red-700'
            : 'bg-gray-100 text-gray-700'
        }`}>
          {config.trading_mode === 'live' ? '🔴 LIVE' : '📄 PAPER'}
        </span>
      </div>
    </button>
  ))}
</div>
```

**Data Loading (Simpler!)**:

```tsx
const [positions, setPositions] = useState([]);
const [selectedConfig, setSelectedConfig] = useState(null);

useEffect(() => {
  const loadPositions = async () => {
    // Load config details
    const config = configs.find(c => c.config_id === selectedConfigId);
    setSelectedConfig(config);

    // Load positions based on mode
    if (config.trading_mode === 'live') {
      // Query Symphony
      const resp = await fetch(`/api/v2/positions/live/${selectedConfigId}`);
      const data = await resp.json();
      setPositions(data.positions);
    } else {
      // Query paper (existing)
      const resp = await fetch(`/api/live-position-data?config_id=${selectedConfigId}`);
      const data = await resp.json();
      setPositions(data.positions);
    }
  };

  loadPositions();
  const interval = setInterval(loadPositions, 10000);
  return () => clearInterval(interval);
}, [selectedConfigId]);
```

**Table Rendering (Even Simpler!)**:

No mode column needed - it's implicit from selected bot:

```tsx
<table>
  <thead>
    <tr>
      <th>Symbol</th>
      <th>Side</th>
      <th>Entry</th>
      <th>Current</th>
      <th>P&L</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody>
    {positions.length === 0 ? (
      <tr>
        <td colSpan={6} className="text-center text-gray-500 py-8">
          No open positions
        </td>
      </tr>
    ) : (
      positions.map(pos => (
        <tr key={pos.batch_id || pos.trade_id}>
          <td>{pos.symbol || pos.asset}</td>
          <td>
            <span className={pos.side === 'long' || pos.isLong ? 'text-green-600' : 'text-red-600'}>
              {(pos.side || (pos.isLong ? 'long' : 'short')).toUpperCase()}
            </span>
          </td>
          <td>${pos.entry_price.toFixed(2)}</td>
          <td>${pos.current_price.toFixed(2)}</td>
          <td className={pos.pnl_usd >= 0 ? 'text-green-600' : 'text-red-600'}>
            ${pos.pnl_usd.toFixed(2)} ({pos.pnl_percentage.toFixed(2)}%)
          </td>
          <td>
            <button onClick={() => handleClose(pos)}>Close</button>
          </td>
        </tr>
      ))
    )}
  </tbody>
</table>
```

**Close Position Handler**:

```tsx
const handleClose = async (position) => {
  // Confirm for live positions
  if (selectedConfig.trading_mode === 'live') {
    if (!confirm('Close this LIVE position?')) return;

    await fetch(`/api/v2/positions/live/${position.batch_id}/close`, {
      method: 'POST'
    });
  } else {
    // Existing paper close logic
    await closePaperPosition(position.trade_id);
  }

  // Refresh positions
  loadPositions();
};
```

**Comparison Flow**:

User wants to compare paper vs live performance:

1. View "BTC Scalper (Paper)" → See 5 paper positions, total P&L: +$1,250
2. Switch to "BTC Scalper (Live)" → See 2 live positions, total P&L: +$45
3. Same signals, different execution/fees → Easy visual comparison

**Benefits**:
- Cleaner UI (no mode column)
- Simpler code (no merging logic)
- Clear mental model (one bot = one mode)
- Easy comparison (switch between bots)

---

### Day 7: Testing & Documentation

#### Testing

**Manual Test Flow**:
1. Create Symphony account at agent-portal.symphony.io
2. Deposit $10 USDC
3. Create agent, get API key
4. In ggbots Settings → Connect Symphony (paste key + smart account)
5. Create bot config → Set to "Live" mode → Enter agent ID
6. Start bot → Verify decision generates
7. Check Symphony portal → Position opens
8. Check ggbots dashboard → Position displays with "🔴 LIVE" badge
9. Click "Close" → Position closes in Symphony
10. Verify `live_trades` table updated

**Edge Cases to Test**:
- Invalid API key → Clear error message
- Insufficient balance → Symphony rejects, error shown
- Invalid agent ID → Symphony 404, error shown
- Network timeout → Retry logic works
- Position already closed → Close endpoint handles gracefully

**Unit Tests** (optional for MVP):
- `SymphonyService.execute_trade_intent()` - mock Symphony API
- `VaultManager.store_symphony_credential()` - vault integration
- Orchestrator routing logic - paper vs live switch

---

#### Documentation

**User Guide**: "How to Enable Live Trading"

1. Create Symphony account
2. Deposit USDC
3. Create agent
4. Connect in ggbots
5. Configure bot
6. Start trading

**Developer Notes**: Architecture decisions, why we chose thin wrapper approach

**API Reference**: Document 4 endpoints with curl examples

---

## Post-MVP Iterations

Based on user feedback, we may add:

**Week 2: Nice-to-Haves**
- Balance display (if users request it)
- Position caching (if Symphony API slow)
- Better error messages (based on actual errors seen)

**Week 3: Advanced Features**
- Multi-agent performance dashboard
- Agent creation wizard
- Position management improvements

**Week 4: Scale & Polish**
- Monitoring dashboard
- Analytics integration
- Mobile responsive design

**But for Week 1**: Ship the minimal version, get real user feedback, iterate.

---

## Success Metrics

**Week 1 (MVP Launch)**:
- [ ] 5+ users connect Symphony
- [ ] 20+ live trades executed
- [ ] <10% error rate
- [ ] Zero data loss incidents

**Week 2-4 (Iteration)**:
- [ ] 50+ users live trading
- [ ] User feedback collected
- [ ] Pain points identified
- [ ] Roadmap updated based on real usage

---

## Why This Plan is Better

**Comparison to Archive Plan**:

| Aspect | Archive Plan | This Plan |
|--------|-------------|-----------|
| **Timeline** | 3-4 weeks | 1 week |
| **Database Tables** | 2 new (20+ fields) | 1 tiny (5 fields) |
| **Code Lines** | ~1500 | ~400 |
| **API Endpoints** | 7 | 4 |
| **Dependencies** | Arbiscan, caching, cron | None |
| **Assumptions** | Many unverified | Minimal |
| **Philosophy** | Feature parity with Symphony | Thin wrapper |

**Key Simplifications**:
1. No balance tracking (Symphony portal has it)
2. No reconciliation (Symphony is source of truth)
3. No risk checks (Symphony handles this)
4. No caching (query Symphony real-time)
5. No complicated state management

**Result**: Ship faster, learn faster, iterate faster.

---

## The Elegant Path

**Week 1**: Ship minimal MVP
- Vault integration ✓
- Symphony service (3 methods) ✓
- Orchestrator routing ✓
- Settings UI ✓
- Dashboard integration ✓

**Week 2**: User feedback
- Do they ask for balance? Add it then.
- Are positions loading fast? Add caching then.
- Are errors confusing? Improve messaging then.

**Week 3+**: Iterate based on REAL usage, not assumptions.

---

## Updated Implementation Timeline

### ✅ Day 0: COMPLETE (Symbol System Extension)
- Extended `core/symbols/registry.py` with Symphony format
- Added `to_symphony()` and `from_symphony()` methods to standardizer
- Identified 100 Symphony-compatible symbols out of 141 ggbots symbols

### 🔜 Days 1-7: Implementation Phases

**Day 1**: Premium Gating & Settings Modal (Frontend + permissions)
**Day 2**: Database & Vault (Schema changes + credential storage)
**Day 3**: Symphony Service (Core API wrapper with 3-second settlement)
**Day 4**: Orchestrator Integration (Trading router + position management)
**Day 5**: API Endpoints (Setup, status, positions, close, duplicate)
**Day 6**: Frontend (Settings page + duplicate-as-live flow + dashboard)
**Day 7**: Testing & Documentation (Manual testing + edge cases + user guide)

---

**End of Plan**

This plan follows the principle: **Make it work, make it right, make it fast** - in that order.

**Day 0 Complete**: Symbol system ready for Symphony integration.
**Days 1-7**: Implementation of thin wrapper pattern with real API field mapping and 3-second settlement handling.
