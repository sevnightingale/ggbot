# LLM-Driven SL/TP — Planning Doc

**Status**: PHASE 1 COMPLETE (verified in production 2026-03-21)
**Origin**: Power user feedback (DOCS/analysis/user_feedback_risk_engine.md)
**Created**: 2026-03-20

---

## Problem

All three prompt templates (opportunity_analysis, signal_validation, position_management) explicitly tell the LLM NOT to output SL/TP levels:

> "Stop loss and take profit levels are managed by your risk management configuration and will be applied automatically based on your settings."

The result: every trade uses the same fixed % SL/TP from config (e.g., -1.5% / +3%). The LLM has full market context (ATR, structure, volatility) but can't use it to set intelligent stop/take-profit levels per trade.

**Sev's perspective**: SL/TP are guardrails — the agent usually closes trades itself before hitting them. But having the agent set *and update* these levels would be an improvement.

## Current State

The **plumbing already works end-to-end**:

1. **Parser** (`engine_v2.py:1724-1752`): Already parses `STOP_LOSS:` and `TAKE_PROFIT:` from LLM output
2. **Orchestrator** (`orchestrator.py:996-997`): Already passes `stop_loss_price` and `take_profit_price` from decision result to trading intent
3. **Paper trading** (`supabase_service.py:216-226`): Uses LLM values if present, falls back to config % defaults
4. **Hyperliquid** (`hyperliquid_service.py:368-369, 480-505`): Same — LLM values first, config % fallback
5. **DecisionData model** (`decision.py:37-38`): Already has `stop_loss_price` and `take_profit_price` fields

**Only the prompts are missing the ask.**

---

## Phase 1: LLM-Driven SL/TP on Entry (Prompt-Only)

**Effort**: ~30 min | **Code changes**: 0 | **Risk**: Low

### Changes

**`decision/prompts/opportunity_analysis.py`**: ✅ DONE
- Added `STOP_LOSS: [price if applicable]` and `TAKE_PROFIT: [price if applicable]` to OUTPUT FORMAT
- Removed "Note: Stop loss and take profit levels are managed by your risk management configuration..."
- Added instruction: optional fields, defaults already configured as guardrails, only override when analysis suggests better levels

**`decision/prompts/signal_validation.py`**: ✅ DONE
- Same output format change
- Same note removal

**`decision/prompts/position_management.py`**:
- No change in Phase 1 (actions remain [close/wait])
- Phase 2 handles mid-trade updates

### Behavior After Change

| LLM outputs | What happens |
|-------------|-------------|
| `STOP_LOSS: 81450.00` | Trade uses $81,450 as SL |
| No STOP_LOSS line at all | Parser returns None → config % fallback applies silently |

Fully backwards compatible. If the LLM ignores the new fields or says "default", existing behavior is unchanged.

### Validation

- Check pm2 logs after deployment for a few cycles
- Verify SL/TP values in `decisions.decision_data` JSONB are reasonable (not hallucinated prices)
- Watch for edge cases: LLM outputting SL above entry for longs, TP below entry for longs (the parser already validates directionality at `engine_v2.py:1769+`)

---

## Phase 2: Mid-Trade SL/TP Updates (Code Required)

**Effort**: ~2-4 hours | **Risk**: Medium (touches live trading)

### Concept

Position management prompt currently outputs `[close/wait]`. Add optional `STOP_LOSS:` and `TAKE_PROFIT:` fields to the wait/hold action. When present, the system updates the stop/TP orders.

Use cases:
- Trail stop to breakeven after trade moves 1-2R in profit
- Tighten stop during high-volatility regime shifts
- Widen stop when initial placement was too aggressive but thesis remains valid

### Prompt Changes

**`decision/prompts/position_management.py`**:
- Add `STOP_LOSS: [new price, "keep", or "remove"]` and `TAKE_PROFIT: [new price, "keep", or "remove"]` to OUTPUT FORMAT
- Instruction: "If holding, you may optionally update SL/TP levels. Use 'keep' to leave unchanged."

### Code Changes

**Paper trading** (`trading/paper/supabase_service.py` or `trading/paper/positions.py`):
- New method or extension: `update_position_stops(trade_id, stop_loss, take_profit)`
- Simple UPDATE on `paper_trades` table (stop_loss, take_profit columns already exist)

**Hyperliquid** (`trading/live/hyperliquid_service.py`):
- New method: `update_trigger_orders(batch_id, user_id, new_sl, new_tp)`
- Cancel existing trigger orders (cancel logic already exists in `close_position` at lines 846-856)
- Place new trigger orders (order placement logic already exists in `execute_trade_intent` at lines 633-700)
- Update `live_trades` record with new order IDs

**Orchestrator** (`core/orchestrator/orchestrator.py`):
- After position management decision with action=wait: check for SL/TP in decision result
- If present and different from current: call update method on appropriate trading service
- Log `stop_updated` activity

**Decision engine** (`decision/engine_v2.py`):
- Parser already handles STOP_LOSS/TAKE_PROFIT — no changes needed
- May need to pass current SL/TP into position data so LLM knows what's currently set

### Risk Mitigation

- Only update if new price is directionally valid (same validation as entry)
- Rate limit: max 1 SL/TP update per cycle (natural — position management runs once per cycle)
- Log every update with old → new values for audit trail
- If cancel succeeds but new order fails: log error, position continues without that trigger order (same as if it was never set)

---

## NOT in Scope

- **Dynamic leverage from LLM** — risk preference, not per-trade tactical. Dangerous if LLM hallucinates 50x
- **Risk-per-trade sizing model** — architecturally different from confidence-based sizing. Only relevant if moving to structure-based stops as primary exit. Defer until more live users
- **Separate "Risk Engine" module** — over-engineering. LLM already has all context
- **UX changes** — no frontend work needed for either phase

---

## Files Summary

### Phase 1 (prompt-only)
| File | Change |
|------|--------|
| `decision/prompts/opportunity_analysis.py` | Add SL/TP to output format, remove "managed automatically" note |
| `decision/prompts/signal_validation.py` | Same |

### Phase 2 (code)
| File | Change |
|------|--------|
| `decision/prompts/position_management.py` | Add optional SL/TP to output format |
| `trading/paper/supabase_service.py` or `positions.py` | `update_position_stops()` method |
| `trading/live/hyperliquid_service.py` | `update_trigger_orders()` method (cancel + replace) |
| `core/orchestrator/orchestrator.py` | Handle SL/TP updates on wait/hold decisions |
| `decision/engine_v2.py` | Include current SL/TP in position data for LLM context |
