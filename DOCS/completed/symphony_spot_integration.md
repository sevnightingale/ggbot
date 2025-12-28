# Symphony Spot Trading Integration Plan

## Overview

Symphony has launched spot trading support on Monad testnet. This enables token swaps (not perpetuals) for chains that don't support perp trading yet.

**Key Differences from Perps:**
- **Endpoint**: `/agent/swap` (not `/agent/batch-open`)
- **Parameters**: `tokenIn`/`tokenOut` (not `symbol` + `action`)
- **Trading Type**: Spot swaps (not leveraged perps)
- **Chains**: Monad testnet initially
- **Collateral**: MON token as base asset

## MON (Monad) Details

- **Name**: Monad
- **Type**: Layer 1 blockchain (new)
- **SID**: 10056
- **Trading**: Spot only (no perps available)
- **Status**: Testnet active, eligible for trading rewards
- **Recommended Collateral**: Start with $MON as collateral asset

## Symphony API Endpoints

### 1. Token Price (Public - No Auth)
**Endpoint**: `GET /token/price`

**Use Cases**:
- Get real-time USD prices for any Symphony token
- Resolve Symphony Identifiers (SIDs) - e.g., MON = 10056
- Validate token existence before swapping
- Calculate P&L for spot swaps

**Parameters**:
```json
{
  "input": "MON",      // Token symbol or contract address
  "chainId": 143       // Monad = 143
}
```

**Response**:
```json
{
  "status": "success",
  "price": 0.0044708,  // USD price
  "sid": 10056,        // Symphony Identifier
  "chainId": 143
}
```

**Test Script**: `trading/live/symphony_price_test.py`

---

### 2. Spot Swap (Requires Auth)
**Endpoint**: `POST /agent/swap`

**Parameters**:
```json
{
  "agentId": "uuid",
  "tokenIn": "MON",
  "tokenOut": "USDC",
  "weight": 5.0,               // % of tokenIn balance to swap
  "intentOptions": {
    "desiredProtocol": "kuru"  // Optional
  }
}
```

**Response**:
```json
{
  "message": "Swap submitted",
  "batchId": "uuid",
  "successful": 1,
  "failed": 0,
  "results": [...]
}
```

---

## Integration Phases

### Phase 1: Testing (Current)

**Goal**: Validate Symphony APIs work with our setup

**Steps**:
1. ✅ Run `trading/live/symphony_price_test.py` (public endpoint)
2. ✅ Verify MON SID = 10056
3. ✅ Get current MON/USDC prices
4. 🔄 Run `trading/live/symphony_swap_test.py` (requires auth)
5. 🔄 Test MON → USDC swap (1% of balance)
6. 🔄 Test USDC → MON swap (reverse)
7. 🔄 Verify batchId tracking works

**Test Scripts**:
- `/home/sev/ggbot/trading/live/symphony_price_test.py` (no auth)
- `/home/sev/ggbot/trading/live/symphony_swap_test.py` (needs API key)

**Required Env Vars** (for swap test only):
```bash
SYMPHONY_API_KEY=your_key_here
SYMPHONY_AGENT_ID=your_agent_id_here
```

**Success Criteria**:
- ✅ Price endpoint returns valid MON/USDC prices
- ✅ SID resolution works (MON = 10056)
- ✅ Swap executes successfully (if you have testnet MON)
- ✅ Returns valid batchId
- ✅ Can track swap in Symphony dashboard
- ✅ Transaction appears on Monad explorer

---

### Phase 2: Symbol Registry Addition

**Goal**: Add MON to the universal symbol system

**File**: `core/symbols/registry.py`

**New Entry**:
```python
"mon": {
    "base": "MON",
    "quote": "USDT",  # Or "USDC" if that's the quote
    "ggshot": None,  # MON not on ggShot yet
    "ccxt": "MON/USDT",  # Standard format
    "hummingbot": "MON-USDT",
    "platform": "MON-USDT",
    "symphony": "MON",  # For spot swaps
    "symphony_compatible": False,  # No perps
    "symphony_spot_compatible": True,  # NEW FLAG for spot
    "aster_compatible": False,
    "coingecko_id": "monad",  # TBD - check if listed
    "websocket_cached": False,  # Not on Binance WebSocket
    "sid": 10056,  # Symphony ID
    "chain": "monad",  # L1 identifier
},
```

**Standardizer Updates**:
- Add `is_symphony_spot_compatible()` method
- Add `get_symphony_sid()` method for SID lookups

---

### Phase 3: Spot Trading Service

**Goal**: Create dedicated service for Symphony spot swaps

**File**: `trading/live/symphony_spot_service.py` (new)

**Architecture**:
```python
class SymphonySpotTradingService:
    """
    Symphony spot trading (swaps) - separate from perp trading.

    Key differences from SymphonyLiveTradingService:
    - Uses /agent/swap endpoint (not /agent/batch-open)
    - No leverage, stop-loss, take-profit (spot only)
    - Token symbols instead of perp pairs
    - Weight is % of specific token balance (not account balance)
    """

    async def get_token_price(
        self,
        token: str,         # Symbol or address
        chain_id: int = 143 # Monad default
    ) -> Dict[str, Any]:
        """
        Get current USD price for a token via Symphony public API.

        Returns:
            {
                "status": "success",
                "price": 0.0044708,
                "sid": 10056,
                "chainId": 143
            }
        """
        pass

    async def execute_swap(
        self,
        token_in: str,      # e.g., "MON"
        token_out: str,     # e.g., "USDC" or contract address
        weight: float,      # 0-100 (% of tokenIn balance)
        agent_id: str,
        api_key: str,
        desired_protocol: str = None  # Optional: "kuru", "nadfun"
    ) -> Dict[str, Any]:
        """
        Execute token swap via Symphony.

        Uses get_token_price() to validate tokens and calculate expected output.
        """
        pass

    async def calculate_swap_pnl(
        self,
        entry_token: str,   # Token bought
        exit_token: str,    # Token sold
        amount_in: float,   # Amount of exit_token used
        amount_out: float,  # Amount of entry_token received
        chain_id: int = 143
    ) -> float:
        """
        Calculate P&L for a swap using Symphony price endpoint.

        Returns: P&L in USD
        """
        # Get current prices
        entry_price = await self.get_token_price(entry_token, chain_id)
        exit_price = await self.get_token_price(exit_token, chain_id)

        # Calculate P&L
        cost_usd = amount_in * exit_price['price']
        value_usd = amount_out * entry_price['price']
        pnl = value_usd - cost_usd

        return pnl

    async def get_swap_history(self, agent_id: str, api_key: str) -> List[Dict]:
        """Query historical swaps (if API supports it)."""
        pass
```

**Database Considerations**:
- Reuse `live_trades` table with `provider='symphony_spot'`?
- Or create new `spot_swaps` table?
- Need to track: batchId, tokenIn, tokenOut, weight, tx hash

---

### Phase 4: Bot Configuration Integration

**Goal**: Allow users to configure spot trading bots

**Questions to Answer**:

1. **Should spot trading be a separate bot type?**
   - Option A: New `config_type='spot_trading'`
   - Option B: Extend `trading_mode` to include `'symphony_spot'`
   - **Recommendation**: Option B - simpler, reuses existing infrastructure

2. **How should decision engine handle spot signals?**
   - Perps: Buy → LONG, Sell → SHORT
   - Spot: Buy → Swap USDC→MON, Sell → Swap MON→USDC
   - Need to track "inventory" (how much MON vs USDC we hold)

3. **Position sizing for spot?**
   - No leverage, so `weight` = % of token balance
   - Example: 10% confidence → swap 10% of USDC to MON

4. **Frontend changes needed?**
   - Trading mode selector: Add "Symphony Spot" option
   - Symbol selector: Show only spot-compatible symbols
   - Settings: No leverage/SL/TP fields for spot mode

---

### Phase 5: Agent Tool Integration

**Goal**: Let autonomous agents execute spot swaps

**New MCP Tool**: `execute_spot_swap`

```python
{
    "name": "execute_spot_swap",
    "description": "Execute a spot token swap on Symphony (Monad chain)",
    "input_schema": {
        "type": "object",
        "properties": {
            "token_in": {"type": "string", "description": "Token to sell (MON, USDC)"},
            "token_out": {"type": "string", "description": "Token to buy"},
            "weight_percent": {"type": "number", "description": "% of token_in balance to swap (0-100)"},
            "desired_protocol": {"type": "string", "description": "Optional: kuru, nadfun"}
        },
        "required": ["token_in", "token_out", "weight_percent"]
    }
}
```

**System Prompt Addition**:
```
You can execute spot token swaps on Monad using execute_spot_swap.
Unlike perpetuals, spot swaps:
- Have no leverage (1:1 exchange)
- Cannot go short (you must own the token)
- Require tracking inventory (how much MON vs USDC you hold)

Example strategy:
- Buy signal → Swap USDC to MON
- Sell signal → Swap MON back to USDC
```

---

## Architecture Decisions

### Separate Service vs Unified Service?

**Option 1: Separate SymphonySpotTradingService**
- ✅ Clean separation of concerns
- ✅ Easier to maintain
- ✅ Spot and perp APIs are quite different
- ❌ More code duplication

**Option 2: Extend SymphonyLiveTradingService**
- ✅ Less code duplication
- ❌ More complex branching logic
- ❌ Mixes two different trading paradigms

**Recommendation**: **Option 1** - Keep services separate. The APIs are different enough that unifying them would create complexity.

---

### Database Schema

**Option 1: Reuse `live_trades` table**
```sql
-- Add provider field to distinguish
provider: 'symphony' | 'symphony_spot' | 'aster'

-- For spot trades:
-- batch_id: Symphony swap batch ID
-- symbol: e.g., "MON-USDC" (token pair)
-- decision_id: Link to decision engine
-- No leverage, SL, TP fields (NULL for spot)
```

**Option 2: New `spot_swaps` table**
```sql
CREATE TABLE spot_swaps (
    swap_id uuid PRIMARY KEY,
    batch_id varchar(255) UNIQUE,
    config_id uuid REFERENCES configurations(config_id),
    decision_id uuid REFERENCES decisions(decision_id),
    token_in varchar(20),
    token_out varchar(20),
    weight_percent numeric,
    tx_hash varchar(66),
    explorer_url text,
    created_at timestamp,
    settled_at timestamp
);
```

**Recommendation**: **Option 1** - Reuse `live_trades` with `provider='symphony_spot'`. Simpler, consistent with existing patterns.

---

## Testing Checklist

### Phase 1 Tests
- [ ] Run `symphony_swap_test.py` successfully
- [ ] Verify swap appears in Symphony dashboard
- [ ] Check Monad explorer shows transaction
- [ ] Test error handling (invalid token, insufficient balance)
- [ ] Test protocol selection (kuru vs nadfun)

### Phase 2 Tests
- [ ] Add MON to symbol registry
- [ ] Test `standardizer.is_symphony_spot_compatible("MON-USDT")`
- [ ] Test `standardizer.get_symphony_sid("MON-USDT")` returns 10056

### Phase 3 Tests
- [ ] Create SymphonySpotTradingService
- [ ] Test execute_swap() end-to-end
- [ ] Test error handling and retries
- [ ] Test swap history queries
- [ ] Verify database records created correctly

### Phase 4 Tests
- [ ] Create spot trading bot via UI
- [ ] Execute test swap via bot
- [ ] Verify activity logging
- [ ] Test position tracking (inventory)

### Phase 5 Tests
- [ ] Agent executes spot swap successfully
- [ ] Agent tracks MON/USDC inventory correctly
- [ ] Agent makes buy/sell decisions based on signals
- [ ] Verify all tools work together

---

## Open Questions

1. **Does Symphony support querying swap history?**
   - Need to test `/agent/batches` or similar endpoint
   - Can we get swap status (pending, completed, failed)?

2. **How do we handle inventory tracking?**
   - Perps: Always start from 0 (open/close positions)
   - Spot: Need to know how much MON/USDC we currently hold
   - Query Symphony balance? Or track locally?

3. **What about gas fees?**
   - Are gas fees deducted from swap amount?
   - Need MON for gas on Monad?

4. **Protocol selection strategy?**
   - Should we default to "kuru" or let Symphony auto-route?
   - Does protocol matter for slippage/fees?

5. **Multi-chain support?**
   - Monad is first, but will Symphony add more chains?
   - Should we design for multi-chain from the start?

---

## Next Steps

1. **Now**: Run `symphony_swap_test.py` to validate API access
2. **If tests pass**: Add MON to symbol registry
3. **Then**: Create `SymphonySpotTradingService` class
4. **Finally**: Integrate with bot configuration system

**Estimated Time**:
- Phase 1 (Testing): 30 minutes
- Phase 2 (Symbol Registry): 15 minutes
- Phase 3 (Spot Service): 2-3 hours
- Phase 4 (Config Integration): 2-3 hours
- Phase 5 (Agent Integration): 1-2 hours

**Total**: ~6-9 hours for full integration
