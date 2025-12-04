# Unified Config Saving System

**Completed**: 2025-12-04
**Git Commit**: `e1fb466` - "Unified config saving system with batched saves + dirty tracking"

---

## Problem Statement

The frontend config saving system had multiple issues:

1. **40+ API calls in 3 minutes** - MarketDataSelector and SignalsConfiguration saved immediately on every toggle
2. **Race conditions** - Multiple components saving at different times with partial configs
3. **Frontend doesn't align** - User had to refresh page to see correct state
4. **Inconsistent patterns** - 5 different save mechanisms across components

## Solution: Unified Batched Save Architecture

### New Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         page.tsx                                 │
│                                                                  │
│   useBatchedConfigSave({ delay: 5000 })                         │
│         │                                                        │
│         ├── Accumulates all changes into queue                   │
│         ├── Tracks dirty fields                                  │
│         ├── 5 second debounce                                    │
│         └── Single batched API call                              │
│                                                                  │
│   SSE Handler                                                    │
│         └── Updates only non-dirty fields                        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
   StrategyEditor     TradeSettings    MarketDataSelector
   (controlled)       (controlled)     (controlled)

   All components just call onUpdate() - no direct API calls
```

### Key Features

1. **Batched Saves**: All config changes accumulate and save after 5s of inactivity
2. **Dirty Field Tracking**: Prevents SSE from overwriting fields user is editing
3. **Controlled Components**: All config components are now "dumb" - just render and call onChange
4. **Unified SSE Updates**: SSE updates ALL config fields (not just agent_strategy)

### Conflict Resolution

When user is editing and SSE brings external changes:
- **Dirty fields** (user editing): Preserved, user wins
- **Non-dirty fields**: Updated from SSE
- **After save completes**: Dirty tracking clears

## Files Changed

| File | Change |
|------|--------|
| `frontend/lib/hooks/useBatchedConfigSave.ts` | **NEW** - Batched save hook with dirty tracking |
| `frontend/app/forge/page.tsx` | Added hook, unified handler, updated SSE |
| `frontend/app/forge/components/configure/ConfigureLayout.tsx` | Simplified - removed local batched save |
| `frontend/app/forge/components/configure/StrategyEditor.tsx` | Removed 4 useAutoSave hooks, now controlled |
| `frontend/app/forge/components/configure/TradeSettings.tsx` | Removed debounce, now controlled |
| `frontend/app/forge/components/configure/MarketDataSelector.tsx` | Removed direct API call |
| `frontend/app/forge/components/configure/SignalsConfiguration.tsx` | Removed direct API call |

## Before vs After

| Metric | Before | After |
|--------|--------|-------|
| API calls for 40 rapid toggles | 40 | 1 |
| Save mechanisms | 5 different | 1 unified |
| useAutoSave hooks in StrategyEditor | 4 | 0 |
| SSE field coverage | agent_strategy only | All config fields |
| Conflict handling | None | Dirty field tracking |

## Testing Verification

1. **Batched saving**: Edit any field → wait 5s → single "Saved!" indicator
2. **Rapid toggles**: Toggle indicators quickly → only 1 save after idle
3. **Dirty protection**: Type in strategy while AI makes changes → your text preserved
4. **Multi-field batch**: Change strategy + toggle indicator → both in one save

## Related

- Bug report: `DOCS/BUG_REPORT_numeric_overflow_and_config_sync.md`
- Original issue: 40+ saves in 3 minutes, frontend state misalignment
