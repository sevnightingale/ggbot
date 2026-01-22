# Telegram Publishing - Platform Bot Implementation

**Status**: 🟡 READY TO IMPLEMENT
**Created**: 2026-01-21
**Complexity**: Medium (~6-8 hours)
**Priority**: P2 - Feature completion

---

## Overview

Enable multi-user Telegram signal publishing using the **Platform Bot Model**: ggbots maintains `@ggFilter_Bot`, users add it to their channels, and we publish signals on their behalf.

**Current State**: Infrastructure exists but is non-functional due to missing bot command handler and broken permission gates.

---

## Problem Statement

Users cannot set up Telegram publishing because:
1. **No `/chatid` command** - Bot doesn't respond to commands, users can't get their channel ID
2. **Broken permission gate** - Frontend shows config to everyone instead of paid users only
3. **Only signal_validation bots** - `scheduled_trading` bots don't trigger publishing
4. **Silent failures** - No feedback when publishing fails (tier check, bot not admin, etc.)

---

## Architecture Decision

**Platform Bot Model** (Selected):
- ggbots maintains `@ggFilter_Bot` (token in `GG_FILTER_TOKEN` env var)
- Users add bot to their Telegram channel/group
- Users grant bot "Post Messages" admin permission
- Users get channel ID via `/chatid` command
- Platform publishes signals to user channels via bot

**Benefits**:
- Simple for users (no bot creation)
- Consistent branding
- Centralized control

**Trade-offs**:
- All signals appear from ggbots bot
- Users must trust platform with channel access

---

## Implementation Plan

### Phase 1: Bot Command Handler (2-3 hours)

**Goal**: Make `@ggFilter_Bot` respond to `/start` and `/chatid` commands.

**New File**: `signals/telegram_bot_handler.py`

```python
# Telegram bot handler for @ggFilter_Bot
# Responds to /start and /chatid commands
# Uses python-telegram-bot library (async)
```

**Commands to Implement**:
| Command | Response |
|---------|----------|
| `/start` | Welcome message explaining how to set up signal publishing |
| `/chatid` | Returns the current chat/channel ID for configuration |
| `/help` | Shows available commands |

**PM2 Service**: Add new service `telegram-bot` to `ecosystem.config.js`

**User Action Required**:
- [ ] Confirm `@ggFilter_Bot` exists on Telegram
- [ ] Confirm bot token in `GG_FILTER_TOKEN` env var is correct
- [ ] Share current bot settings (if any) from BotFather

**Files to Create/Modify**:
- `signals/telegram_bot_handler.py` (NEW) - Command handler service
- `ecosystem.config.js` - Add telegram-bot PM2 service
- `requirements.txt` - Add `python-telegram-bot>=21.0` if not present

---

### Phase 2: Frontend Permission Fix (30 min)

**Goal**: Gate Telegram publishing config behind proper permission check.

**Current Bug** (`frontend/lib/permissions.tsx:103-117`):
```typescript
switch (feature) {
  case 'bot_activation': return userProfile.can_activate_bots
  case 'agents': return userProfile.can_use_agents
  case 'ggshot': return userProfile.paid_data_points.includes('ggshot')
  default: return true  // ← telegram_publishing falls here, always returns true!
}
```

**Fix**: Add explicit case for `telegram_publishing`:
```typescript
case 'telegram_publishing':
  return userProfile.can_publish_telegram_signals
```

**Backend Permission** (`core/domain/user_profile.py`):
- `can_publish_telegram_signals` already exists and returns `True` for `can_activate_bots` users
- This gates it to paid users (usage_based, prepaid, pro tiers)

**Files to Modify**:
- `frontend/lib/permissions.tsx` - Add telegram_publishing case

---

### Phase 3: Extend to Scheduled Trading Bots (2-3 hours)

**Goal**: Allow `scheduled_trading` bots to publish signals, not just `signal_validation`.

**Current Flow** (signal_validation only):
```
ggShot Signal → listener_service → orchestrator → decision → _publish_signal_if_approved()
```

**New Flow** (all bot types):
```
Bot Execution → decision → if telegram_enabled → publish_trading_signal()
```

**Implementation**:

1. **New publishing function** for trading decisions (not signal validation):
   ```python
   async def publish_trading_decision(
       config_id: str,
       user_id: str,
       symbol: str,
       action: str,  # "enter" | "exit" | "wait"
       direction: str,  # "LONG" | "SHORT"
       confidence: float,
       reasoning: str
   ) -> bool
   ```

2. **Hook into orchestrator** after successful trade execution:
   - `_run_autonomous_trading_cycle()` in `ggbot.py`
   - Only publish "enter" decisions that result in trades
   - Optionally publish "exit" decisions

3. **Message format** for trading decisions:
   ```
   🤖 [Bot Name] Signal

   Action: ENTER LONG
   Symbol: BTC/USDT
   Confidence: 78%

   Reasoning: RSI oversold at 28, bullish divergence on 4H...

   ⚠️ This is AI-generated. Not financial advice.
   ```

**Files to Modify**:
- `signals/publishing_service.py` - Add `publish_trading_decision()` function
- `ggbot.py` - Hook publishing into `_run_autonomous_trading_cycle()`

---

### Phase 4: Error Handling & UX (1 hour)

**Goal**: Clear feedback when publishing fails.

**Failure Scenarios**:
| Scenario | Current Behavior | Desired Behavior |
|----------|------------------|------------------|
| User not subscribed | Silent fail | "Telegram publishing requires a subscription" |
| Bot not admin in channel | Silent fail | "Bot lacks permission. Make it admin with 'Post Messages'" |
| Invalid channel ID | Silent fail | "Channel not found. Check your channel ID" |
| Rate limited | Silent fail | "Too many messages. Try again in X seconds" |

**Implementation**:
1. Return structured errors from `publish_signal_to_telegram()`
2. Update test endpoint to return specific error messages
3. Frontend displays error in alert (currently just shows generic error)

**Files to Modify**:
- `signals/publishing_service.py` - Return structured errors
- `ggbot.py` - Update test endpoint response
- `frontend/.../TradeSettings.tsx` - Better error display

---

### Phase 5: Testing & Documentation (1 hour)

**Manual Testing Checklist**:
- [ ] `/start` command returns welcome message
- [ ] `/chatid` in channel returns correct ID
- [ ] `/chatid` in group returns correct ID
- [ ] `/chatid` in private chat returns correct ID
- [ ] Non-subscriber sees "Premium Feature Locked"
- [ ] Subscriber can enable toggle and enter channel ID
- [ ] Test message sends successfully
- [ ] Test message fails gracefully if bot not admin
- [ ] Bot execution triggers Telegram publish (scheduled_trading)
- [ ] Signal validation triggers Telegram publish (signal_validation)

**Documentation Updates**:
- [ ] Update frontend instructions if bot name changes
- [ ] Add troubleshooting section to help docs

---

## File Summary

| File | Action | Description |
|------|--------|-------------|
| `signals/telegram_bot_handler.py` | CREATE | Bot command handler service |
| `ecosystem.config.js` | MODIFY | Add telegram-bot PM2 service |
| `frontend/lib/permissions.tsx` | MODIFY | Fix permission gate |
| `signals/publishing_service.py` | MODIFY | Add trading decision publisher, structured errors |
| `ggbot.py` | MODIFY | Hook publishing into trading cycle |
| `frontend/.../TradeSettings.tsx` | MODIFY | Better error display |

---

## User Actions Required

Before implementation can begin:

1. **Verify Bot Exists**
   - Open Telegram and search for `@ggFilter_Bot`
   - Confirm it's our bot (check with BotFather if unsure)

2. **Verify Bot Token**
   - Check `.env` for `GG_FILTER_TOKEN`
   - Test token: `curl https://api.telegram.org/bot<TOKEN>/getMe`
   - Should return bot info JSON

3. **Check BotFather Settings**
   - Go to @BotFather → /mybots → select @ggFilter_Bot
   - Check if "Group Privacy" is disabled (needed to see /chatid in groups)
   - Share current settings screenshot if possible

4. **Decide on Message Branding**
   - Should signals include ggbots logo/branding?
   - Should signals include disclaimer?
   - Should signals link back to ggbots.ai?

---

## Dependencies

- `python-telegram-bot>=21.0` - Async Telegram bot library
- `GG_FILTER_TOKEN` env var - Bot token from BotFather

---

## Success Criteria

1. Users can get channel ID via `/chatid` command
2. Only paid users see Telegram config (not locked)
3. Test message sends successfully to user channel
4. Scheduled trading bots publish entry signals
5. Clear error messages on failure

---

## Rollback Plan

If issues arise:
1. Stop `telegram-bot` PM2 service
2. Revert permission gate to `default: return true`
3. Feature becomes non-functional but app remains stable

---

## Future Enhancements (Out of Scope)

- [ ] User-defined message templates
- [ ] Publish exit signals (with P&L)
- [ ] Daily performance summaries
- [ ] Multi-channel support per bot
- [ ] Rate limiting per user
