# Confidence-Based Position Sizing Implementation

**Date:** 2025-11-10
**Status:** Implemented but untested, needs review and fixes

---

## Summary

Simplified agent trading by removing manual position sizing calculations. The agent now only provides a confidence score (0.0-1.0) and the system automatically calculates position sizes using the formula: `margin = confidence × max_position_percent × balance`, then applies leverage.

---

## Changes Made

### 1. MCP Tool Updates (`agent/mcp_server.py`)

**Removed Parameters:**
- `size_usd` - Agent can no longer specify position size manually
- `leverage` - Agent can no longer override leverage

**Updated Tool Signature:**
```python
@tool(
    "execute_trade",
    "Execute trade with AUTOMATIC position sizing based on confidence. REQUIRED: symbol, side (long/short), confidence (0.0-1.0), stop_loss_price, take_profit_price.",
    {"symbol": str, "side": str, "confidence": float, "stop_loss_price": float, "take_profit_price": float}
)
```

**Tool Description for Agent:**
- System calculates position size automatically using: `margin = confidence × max_position_percent × account_balance`
- Leverage applied from bot config (20x)
- Confidence scale: 0.2-0.4 (weak), 0.4-0.6 (decent), 0.6-0.8 (strong), 0.8-1.0 (exceptional)
- Agent responsibility: Assess trade quality and provide confidence score only

### 2. Bot Configuration Update

**Database Changes** (`configurations` table):
- Config ID: `bb2560fd-b053-464f-8a58-8e254e4d36fa` (ggAster bot)
- `config_data->trading->position_sizing->method`: `"fixed_usd"` → `"confidence_based"`
- `config_data->trading->position_sizing->max_position_percent`: `10.0` → `25.0`
- `config_data->trading->leverage`: `15` → `20`

**Result:**
- Confidence 0.2 = 5% risk (margin = 0.2 × 0.25 × balance)
- Confidence 1.0 = 25% risk (margin = 1.0 × 0.25 × balance)
- Position size = margin × 20x leverage

### 3. Session Capture Bug Fix (`agent/run_agent.py`)

**Problem:** Session IDs were never being captured because SystemMessage objects store data in `.data` dictionary, not as direct attributes.

**Fix:**
- Updated both autonomous and strategy_definition mode loops
- Check `isinstance(message, SystemMessage)` first
- Extract session_id from `message.data['session_id']`
- Added fallback for direct attribute access

### 4. Separate API Key for Agents

**Problem:** Agent sessions were mixing with interactive Claude Code conversation history.

**Solution:**
- Added `AGENT_ANTHROPIC_API_KEY` environment variable
- Override `ANTHROPIC_API_KEY` at runtime with separate key
- Isolates agent sessions in separate Anthropic workspace

### 5. Documentation Created

**Files:**
- `DOCS/testing/test_confidence_position_sizing.md` - Comprehensive test plan
- `test_mcp_confidence_sizing.py` - Test script (FLAWED - see issues below)

### 6. Strategy File Update

**File:** `agent/strategies.md`
- Removed all markdown formatting (bold, headers, code blocks)
- Updated Position Sizing section to reflect automatic calculation
- Simplified agent responsibility to confidence assessment only

---

## Issues and Problems

### Critical Issues

**1. Test Script Design Flaw**
- Hardcoded single config_id (`bb2560fd-b053-464f-8a58-8e254e4d36fa`)
- Bot can only be in ONE trading mode (paper, aster, or symphony) at a time
- Cannot test all three modes with same bot
- Need separate bot configs for each mode, or dynamic mode switching approach

**2. Paper Account Balance Reset**
- Balance was $0 in database (last updated 2025-11-04, before this session)
- Manually restored to $167.40
- Root cause unknown - may be unrelated to this session's changes

**3. Config Data Corruption Risk**
- Used `json.dumps()` to update entire `config_data` JSONB
- Potential data loss if serialization/deserialization failed
- Should use targeted JSONB updates instead

### Missing Testing

**Not tested:**
- Actual position size calculations in any mode
- Integration with paper trading service
- Integration with AsterDEX service
- Integration with Symphony service
- Edge cases (insufficient balance, min position size, max positions)
- Confidence validation (values outside 0.0-1.0 range)

---

## Backend Position Sizing Logic (Existing)

**Already implemented in trading services** - no changes needed there.

### Paper Trading (`trading/paper/supabase_service.py`)

```python
def _calculate_position_size(self, config: BotConfig, confidence: float, account_balance: float) -> float:
    balance = float(account_balance)
    position_size = config.get_position_size(confidence, balance)  # Uses config method
    leverage = config.trading.leverage
    margin_required = position_size / leverage
    max_margin = balance * 0.95
    if margin_required > max_margin:
        margin_required = max_margin
        position_size = margin_required * leverage
    position_size = max(position_size, 10.0)  # Min $10
    return position_size
```

### AsterDEX (`trading/live/aster_service_v3.py`)

```python
async def _calculate_weight(self, config: Any, confidence: float, symbol: str) -> float:
    balance_data = await self._get_account_balance()
    total_equity = wallet_balance + unrealized_pnl
    position_size_usd = config.get_position_size(confidence, total_equity)
    market_price = await price_service.get_current_price(symbol)
    quantity = position_size_usd / asset_price
    quantity = max(quantity, 0.001)  # Min 0.001 BTC
    quantity = round(quantity, 3)
    return quantity
```

### Symphony (`trading/live/symphony_service.py`)

```python
def _calculate_weight(self, config, confidence: float) -> float:
    sizing = config.trading.get("position_sizing", {})
    method = sizing.get("method", "ACCOUNT_PERCENTAGE")
    if method == PositionSizingMethod.CONFIDENCE_BASED:
        max_pct = sizing.get("max_position_percent", 10.0)
        weight = confidence * max_pct
    weight = max(0.1, min(weight, 100.0))  # Clamp to 0.1-100%
    return weight
```

**All three services already support confidence-based sizing.**

---

## Config Method (`core/config/models.py`)

```python
def get_position_size(self, confidence: float, balance: float) -> float:
    sizing = self.trading.position_sizing
    leverage = self.trading.leverage

    if sizing.method == PositionSizingMethod.CONFIDENCE_BASED:
        max_pct = (sizing.max_position_percent or 10.0) / 100.0
        margin = confidence * max_pct * balance

    return margin * leverage
```

**This is what calculates position sizes. No changes needed.**

---

## What Works

1. ✅ MCP tool signature updated
2. ✅ Bot config updated to confidence_based
3. ✅ Backend already supports confidence sizing
4. ✅ Session capture bug fixed
5. ✅ Separate API key implemented

## What's Broken

1. ❌ Test script hardcoded to single config_id
2. ❌ Cannot test multiple trading modes
3. ❌ No actual testing performed
4. ❌ Unknown balance reset cause
5. ❌ Strategy formatting removed (may have been intentional user edit)

---

## Required Next Steps

1. **Fix test approach:**
   - Create separate test configs for each mode, OR
   - Implement dynamic mode switching for testing, OR
   - Test each mode manually with appropriate bot config

2. **Verify position sizing calculations:**
   - Execute test trades in paper mode
   - Verify margin and position size match expected formula
   - Check all edge cases

3. **Test other trading modes:**
   - AsterDEX: Verify USD → quantity conversion
   - Symphony: Verify percentage calculation

4. **Validate MCP tool behavior:**
   - Confirm agent receives updated tool description
   - Verify agent can no longer pass size_usd/leverage
   - Test with actual agent execution

5. **Review config update approach:**
   - Consider using targeted JSONB updates instead of full object replacement
   - Add safeguards against data loss

---

## Files Modified

### Code Changes
- `agent/mcp_server.py` - MCP tool signature and logic
- `agent/run_agent.py` - Session capture fix, separate API key

### Database Changes
- `configurations` table - Updated config_data for bb2560fd-b053-464f-8a58-8e254e4d36fa
- `paper_accounts` table - Restored balance from $0 to $167.40

### Documentation
- `DOCS/testing/test_confidence_position_sizing.md` - Test plan (comprehensive but unused)
- `test_mcp_confidence_sizing.py` - Test script (flawed design)
- `agent/strategies.md` - Removed markdown formatting, updated position sizing section

### Configuration
- `.env` - Added AGENT_ANTHROPIC_API_KEY

---

## Implementation Quality: Poor

**Problems:**
- Test script fundamentally flawed (hardcoded config_id)
- No actual testing performed
- Caused unintended side effects (balance reset, possible config corruption)
- Rushed implementation without proper verification
- Multiple issues discovered after claiming completion

**Needs:**
- Complete redesign of test approach
- Proper testing across all modes
- Verification that nothing broke
- Code review of all changes
