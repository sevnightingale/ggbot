# Testing Plan: Confidence-Based Position Sizing

**Date:** 2025-11-10
**Purpose:** Verify execute_trade MCP tool correctly calculates position sizes across all trading modes
**Bot:** ggAster (config_id: bb2560fd-b053-464f-8a58-8e254e4d36fa)

---

## Test Configuration

**Bot Settings:**
- Position sizing method: `confidence_based`
- Max position percent: 25%
- Leverage: 20x
- Trading modes to test: Paper, AsterDEX, Symphony

**Expected Position Sizing Formula:**
```
margin = confidence × 0.25 × balance
position_size = margin × 20
```

---

## Test Cases

### Test 1: Paper Trading Mode

**Setup:**
- Switch bot to `trading_mode: paper`
- Current paper account balance: $167.40 (from database)

**Test Executions:**

| Test | Confidence | Symbol | Side | SL | TP | Expected Margin | Expected Position | Expected Risk % |
|------|-----------|--------|------|----|----|----------------|-------------------|-----------------|
| 1.1  | 0.2 | BTC/USDT | long | 95000 | 105000 | $8.37 | $167.40 | 5% |
| 1.2  | 0.5 | BTC/USDT | short | 110000 | 95000 | $20.93 | $418.50 | 12.5% |
| 1.3  | 0.8 | BTC/USDT | long | 100000 | 110000 | $33.48 | $669.60 | 20% |
| 1.4  | 1.0 | BTC/USDT | short | 110000 | 90000 | $41.85 | $837.00 | 25% |

**MCP Tool Call Example:**
```python
await execute_trade(
    symbol="BTC/USDT",
    side="long",
    confidence=0.8,
    stop_loss_price=100000,
    take_profit_price=110000
)
```

**Validation Checklist:**
- [ ] Trade executes successfully
- [ ] Position size matches expected calculation
- [ ] Margin reserved from paper account balance
- [ ] SL/TP set correctly
- [ ] Trade saved to `paper_trades` table
- [ ] Balance updated correctly

---

### Test 2: AsterDEX Mode

**Setup:**
- Switch bot to `trading_mode: aster`
- Query live AsterDEX balance (will vary)
- Use actual BTC market price

**Test Executions:**

| Test | Confidence | Symbol | Side | SL Offset | TP Offset | Notes |
|------|-----------|--------|------|-----------|-----------|-------|
| 2.1  | 0.3 | BTC/USDT | long | -2% | +3% | Low conviction |
| 2.2  | 0.6 | BTC/USDT | long | -3% | +5% | Medium conviction |
| 2.3  | 0.9 | BTC/USDT | long | -4% | +8% | High conviction |

**Dynamic Calculation (Example with $500 balance):**
```
confidence = 0.6
margin = 0.6 × 0.25 × $500 = $75
position_usd = $75 × 20 = $1,500
btc_quantity = $1,500 / current_btc_price
```

**AsterDEX-Specific Validation:**
- [ ] Queries live balance from AsterDEX API
- [ ] Converts USD position to BTC quantity correctly
- [ ] Applies minimum quantity (0.001 BTC)
- [ ] Rounds to 3 decimal places
- [ ] Validates margin doesn't exceed 95% of balance
- [ ] Trade appears on AsterDEX platform
- [ ] Leverage is 20x on exchange

---

### Test 3: Symphony Mode

**Setup:**
- Switch bot to `trading_mode: symphony`
- Symphony uses percentage-based position sizing

**Test Executions:**

| Test | Confidence | Symbol | Side | Expected Weight % | Notes |
|------|-----------|--------|------|-------------------|-------|
| 3.1  | 0.2 | BTC/USDT | long | 5% | Min risk |
| 3.2  | 0.5 | BTC/USDT | short | 12.5% | Mid risk |
| 3.3  | 1.0 | BTC/USDT | long | 25% | Max risk |

**Symphony Calculation:**
```
weight = confidence × max_position_percent
weight = 0.5 × 25% = 12.5%
```

**Symphony-Specific Validation:**
- [ ] Calculates weight percentage correctly
- [ ] Weight clamped to 0.1-100% range
- [ ] Trade appears in Symphony dashboard
- [ ] Position size matches expected % of account

---

### Test 4: Edge Cases & Validation

**Test 4.1: Insufficient Balance**
- Set very high confidence (1.0) on small account
- Expected: Trade succeeds but caps margin at 95% of balance

**Test 4.2: Minimum Position Size**
- Use very low confidence (0.1) on small account
- Expected: Position size capped at minimum ($10 for paper)

**Test 4.3: Invalid Confidence Values**
```python
# Test confidence bounds
execute_trade(confidence=-0.1)  # Should fail/clamp to 0
execute_trade(confidence=1.5)   # Should fail/clamp to 1.0
execute_trade(confidence=0.0)   # Should execute with 0% risk (or reject?)
```

**Test 4.4: R/R Validation**
```python
# Poor R/R ratio (SL farther than TP)
execute_trade(
    confidence=0.8,
    stop_loss_price=95000,
    take_profit_price=103000  # R/R < 1:1
)
# Expected: May be rejected or warned
```

**Test 4.5: Max Positions Limit**
- Open 3 positions (max_positions = 3)
- Try to open 4th position
- Expected: Rejected with "max positions reached"

---

## Testing Methods

### Method 1: Manual MCP Tool Testing (Fastest)

**Direct Python Script:**
```python
# test_mcp_execute_trade.py
import asyncio
from agent.mcp_server import execute_trade, agent_context, AgentContext
from agent.service_client import GGBotAPIClient

async def test_confidence_sizing():
    # Setup agent context
    agent_context.config_id = "bb2560fd-b053-464f-8a58-8e254e4d36fa"
    agent_context.user_id = "00000000-0000-0000-0000-000000000000"
    agent_context.trading_mode = "paper"  # Change to test different modes
    agent_context.api_client = GGBotAPIClient(
        user_id="00000000-0000-0000-0000-000000000000",
        base_url="http://localhost:8000"
    )

    # Test case 1: Low confidence
    print("=== Test 1: Confidence 0.2 (Low) ===")
    result = await execute_trade({
        "symbol": "BTC/USDT",
        "side": "long",
        "confidence": 0.2,
        "stop_loss_price": 95000,
        "take_profit_price": 105000
    })
    print(f"Result: {result}\n")

    # Test case 2: High confidence
    print("=== Test 2: Confidence 0.8 (High) ===")
    result = await execute_trade({
        "symbol": "BTC/USDT",
        "side": "short",
        "confidence": 0.8,
        "stop_loss_price": 110000,
        "take_profit_price": 95000
    })
    print(f"Result: {result}\n")

asyncio.run(test_confidence_sizing())
```

**Run:**
```bash
cd /home/sev/ggbot
source .venv/bin/activate
python test_mcp_execute_trade.py
```

---

### Method 2: Agent Autonomous Testing

**Strategy Prompt Test:**
```markdown
TESTING MODE: Execute these test trades to verify position sizing:

1. Execute LONG BTC/USDT with confidence 0.3, SL -2%, TP +3%
2. Execute SHORT BTC/USDT with confidence 0.7, SL +3%, TP -5%
3. Report the position sizes you received

Then use get_positions to verify trades were created correctly.
```

**Monitor in logs:**
- `agent-debug.log` - Agent reasoning and tool calls
- `ggbot.log` - API execution and position sizing calculations

---

### Method 3: API Endpoint Testing

**Direct API Call:**
```bash
curl -X POST http://localhost:8000/api/v2/agent/execute-trade \
  -H "Content-Type: application/json" \
  -d '{
    "config_id": "bb2560fd-b053-464f-8a58-8e254e4d36fa",
    "user_id": "00000000-0000-0000-0000-000000000000",
    "symbol": "BTC/USDT",
    "side": "long",
    "confidence": 0.6,
    "stop_loss_price": 100000,
    "take_profit_price": 110000
  }'
```

**Check response for:**
- `trade.size_usd` - Should match expected position size
- `trade.margin_used` - Should match expected margin
- `trade.leverage` - Should be 20

---

## Database Verification Queries

### Check Paper Trades
```python
from core.common.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                trade_id,
                symbol,
                side,
                confidence_score,
                size_usd,
                margin_used,
                leverage,
                entry_price,
                stop_loss,
                take_profit
            FROM paper_trades
            WHERE config_id = %s
            AND status = 'open'
            ORDER BY opened_at DESC
            LIMIT 5
        """, ('bb2560fd-b053-464f-8a58-8e254e4d36fa',))

        for row in cur.fetchall():
            print(f"Trade: {row[1]} {row[2]}")
            print(f"  Confidence: {row[3]:.2f}")
            print(f"  Position: ${row[4]:.2f}")
            print(f"  Margin: ${row[5]:.2f}")
            print(f"  Leverage: {row[6]}x")
            print(f"  Risk %: {(row[5] / 167.40) * 100:.1f}%\n")
```

### Verify Position Sizing Calculation
```python
# Expected vs Actual comparison
balance = 167.40
max_pct = 25.0
leverage = 20

for trade in trades:
    expected_margin = trade.confidence * (max_pct / 100) * balance
    expected_position = expected_margin * leverage

    margin_match = abs(trade.margin_used - expected_margin) < 0.01
    position_match = abs(trade.size_usd - expected_position) < 0.01

    print(f"Confidence {trade.confidence}:")
    print(f"  Expected margin: ${expected_margin:.2f} | Actual: ${trade.margin_used:.2f} | Match: {margin_match}")
    print(f"  Expected position: ${expected_position:.2f} | Actual: ${trade.size_usd:.2f} | Match: {position_match}")
```

---

## Success Criteria

### ✅ Pass Conditions

**Paper Trading:**
- [ ] Position sizes match formula within $0.01
- [ ] Margin reserved from balance correctly
- [ ] All trades saved to database with correct leverage
- [ ] Balance updates reflect margin usage

**AsterDEX:**
- [ ] Queries live balance successfully
- [ ] Converts USD → BTC quantity correctly
- [ ] Respects minimum quantity (0.001)
- [ ] Trades appear on AsterDEX platform
- [ ] Leverage is 20x on exchange

**Symphony:**
- [ ] Weight percentage calculated correctly
- [ ] Trades appear in Symphony dashboard
- [ ] Position sizing matches confidence scale

**Edge Cases:**
- [ ] Insufficient balance handled gracefully
- [ ] Minimum position size enforced
- [ ] Invalid confidence values rejected/clamped
- [ ] Max positions limit respected

---

## Debugging Tips

**If position size is wrong:**
1. Check bot config: `SELECT config_data->'trading' FROM configurations WHERE config_id = '...'`
2. Check method is `confidence_based`
3. Check `max_position_percent` is 25.0
4. Check `leverage` is 20
5. Add debug logging in `BotConfig.get_position_size()`

**If trade fails:**
1. Check logs: `tail -f logs/agent-debug.log logs/ggbot.log`
2. Check balance is sufficient
3. Check SL/TP are valid prices
4. Check symbol format is correct
5. Verify trading mode is active

**If MCP tool errors:**
1. Check agent context is set correctly
2. Verify API client is initialized
3. Check network connectivity to API
4. Verify config_id and user_id are valid

---

## Rollback Plan

**If testing reveals issues:**

1. **Revert MCP tool changes:**
   ```bash
   git checkout agent/mcp_server.py
   pm2 restart agent-bb2560fd-b053-464f-8a58-8e254e4d36fa
   ```

2. **Revert bot config:**
   ```python
   config_data['trading']['position_sizing']['method'] = 'fixed_usd'
   config_data['trading']['leverage'] = 15
   # UPDATE configurations...
   ```

3. **Close test positions:**
   ```python
   # Close all open paper trades for this config
   # Or manually via UI
   ```

---

## Next Steps After Testing

**If all tests pass:**
- [ ] Update documentation with new position sizing behavior
- [ ] Update agent strategy prompt to remove old position sizing logic
- [ ] Consider implementing Phase 3 enhancements (curves, thresholds)
- [ ] Roll out to other bots (scheduled, etc.)

**If issues found:**
- [ ] Document specific failures
- [ ] Determine root cause
- [ ] Fix and re-test
- [ ] Consider rollback if critical

---

## Test Execution Log

**Date:** _____
**Tester:** _____
**Mode:** Paper / AsterDEX / Symphony

| Test ID | Status | Actual Position | Expected Position | Notes |
|---------|--------|----------------|-------------------|-------|
| 1.1 | ⬜ Pass / ❌ Fail | $ | $ | |
| 1.2 | ⬜ Pass / ❌ Fail | $ | $ | |
| 1.3 | ⬜ Pass / ❌ Fail | $ | $ | |
| 1.4 | ⬜ Pass / ❌ Fail | $ | $ | |

**Overall Result:** ⬜ Pass / ❌ Fail / ⚠️ Partial

**Issues Found:**
-
-

**Recommendations:**
-
-
