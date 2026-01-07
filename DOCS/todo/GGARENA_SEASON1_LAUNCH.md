# ggArena Season 1 Launch Plan

**Status**: 🔴 CRITICAL - Launch tweet tomorrow (Jan 8), Season 1 starts Jan 21
**Target**: Public open competition with $2,500 prize pool
**Duration**: 21 days (Jan 21 12:00 UTC → Feb 11 12:00 UTC)

---

## Verified Assumptions

### Infrastructure (Confirmed)
- **arena.ggbots.ai** - Live, configured in `frontend/next.config.ts` rewrites
- **is_public_performance** - Boolean column exists in `configurations` table (default: false)
- **Reset endpoint** - `/api/v2/bot/{config_id}/reset-account` exists, resets to $10k
- **Public API endpoints** - All working in `api/public.py`

### Current State
- 7 prototype bots with `is_public_performance = true` (Sev's test bots)
- Competition dates hardcoded in `frontend/app/arena/page.tsx` (Dec 18 - Jan 8)
- No registration UI exists yet
- No bulk reset mechanism for competition start

### Business Rules
- Users must subscribe to usage-based plan to activate bots
- Only active bots can compete (prevents free-rider registrations)
- Winning criteria: Highest equity after 21 days
- Prize pool: $2,500 in USX on Scroll
- Top 3 also get funded live trading on Symphony (~$500 each TBD)

---

## Competition Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  NOW → JAN 21                                                       │
│  Registration Phase                                                 │
│  - Users create bots, configure strategies                          │
│  - Click "Enter Arena" to register (sets is_public_performance)     │
│  - Must have active subscription + bot in 'active' state            │
│  - Registered bots appear on arena page as "registered"             │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│  JAN 21 12:00 UTC                                                   │
│  Competition Start                                                  │
│  - Admin triggers bulk reset script                                 │
│  - All registered bots reset to $10,000 paper balance               │
│  - Open positions closed, stats cleared, history preserved          │
│  - Competition clock starts                                         │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│  JAN 21 → FEB 11 (21 days)                                          │
│  Competition Running                                                │
│  - Live leaderboard updates                                         │
│  - No new registrations allowed (or allowed with fresh $10k?)       │
│  - Bots execute per their configured frequency                      │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│  FEB 11 12:00 UTC                                                   │
│  Competition End                                                    │
│  - Final standings locked                                           │
│  - Prize distribution                                               │
│  - Top 3 get live trading funding on Symphony                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Arena Page Redesign

### Current Structure
```
[Header]
[Hero: "The ggArena" - 7 AI agents compete...]
[Performance Chart]
[Bot Leaderboard with expandable cards]
[CTA Footer]
```

### Proposed Structure
```
[Header with countdown to Jan 21]

┌─────────────────────────────────────────────────────────────────────┐
│  SEASON 1 HERO SECTION                                              │
│  🏆 Season 1 Launches January 21st                                  │
│  $2,500 Prize Pool · 21 Days · Top 3 Get Live Funding               │
│                                                                     │
│  [COUNTDOWN TIMER: 13d 14h 22m 15s]                                 │
│                                                                     │
│  [CREATE YOUR GGBOT]          [VIEW RULES]                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  TRAINING GROUND / PROTOTYPE SECTION                                │
│  📊 See What's Possible                                             │
│  These prototype bots showcase the variety of strategies            │
│  you can build. Study their performance and create your own.        │
│                                                                     │
│  [Existing leaderboard + charts - reframed as examples]             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  REGISTERED COMPETITORS (Once registrations open)                   │
│  🎯 X bots registered for Season 1                                  │
│  [List of registered bots - names, avatars, symbols]                │
└─────────────────────────────────────────────────────────────────────┘

[CTA Footer - unchanged]
```

### Copy Updates Needed
- Hero title: "The ggArena" → "ggArena Season 1"
- Hero subtitle: Update to reflect public competition
- Add prize pool prominently ($2,500)
- Add dates (Jan 21 - Feb 11)
- Add countdown timer component
- Reframe existing bots as "Training Ground" / "Prototypes"
- Update footer CTA

---

## Registration Mechanism

### User Flow
1. User has bot configured and active (subscribed)
2. On bot config page or arena page, sees "Enter Arena" button
3. Clicks button → confirmation modal explaining:
   - Account will be reset to $10k on Jan 21
   - Must keep bot active during competition
   - Winning criteria
4. Confirms → `is_public_performance` set to true
5. Bot appears on arena page as "registered"

### Backend Implementation
```python
# New endpoint: POST /api/v2/bot/{config_id}/arena/register
async def register_for_arena(config_id: str, current_user: User):
    # 1. Verify user owns bot
    # 2. Verify bot is active (state = 'active')
    # 3. Verify user has active subscription
    # 4. Set is_public_performance = true
    # 5. Return success
```

### Frontend Implementation
- Add "Enter Arena" button to bot config page (when eligible)
- Add registration modal with confirmation
- Show "Registered for Season 1" badge on registered bots
- Arena page shows count of registered competitors

---

## Bulk Reset Script

### Purpose
On Jan 21 12:00 UTC, reset all registered bots to $10,000.

### Implementation
```python
# scripts/arena_reset.py
async def reset_arena_bots():
    """Reset all is_public_performance=true bots to $10k."""
    # 1. Get all configs with is_public_performance = true
    # 2. For each: call reset_account()
    # 3. Log results
    # 4. Send notification (email/telegram)
```

### Considerations
- Should be idempotent (safe to run multiple times)
- Log all resets for audit trail
- Consider adding `arena_season` column for future seasons
- May want `arena_registered_at` timestamp

---

## Open Questions

1. **Late registrations**: Can users register after Jan 21? If so, do they start fresh or disadvantaged?
   - Recommendation: Allow with fresh $10k, but clearly mark "joined late"

2. **Prototype bots in Season 1**: Should Sev's 7 prototype bots compete?
   - Option A: Yes, they're legit competitors
   - Option B: No, keep them as "examples" separate from competition
   - Recommendation: Option A (more competitors = better)

3. **Deactivation during competition**: What if user deactivates their bot mid-competition?
   - Recommendation: Keep on leaderboard but mark as "inactive", no new trades

4. **Multiple bots per user**: Can one user have multiple bots competing?
   - Recommendation: Yes, but each needs its own subscription costs

---

## Files to Modify

### Critical (Tonight)
- `frontend/app/arena/page.tsx` - Hero section, countdown, copy updates
- `frontend/app/arena/layout.tsx` - Meta tags update
- `ggbot.py` - Add `/api/v2/bot/{config_id}/arena/register` endpoint
- `frontend/components/` - Arena registration modal

### High Priority (Before Jan 21)
- `scripts/arena_reset.py` - Bulk reset script (new file)
- `frontend/components/nav/` - Add ggArena link + banner
- `frontend/app/forge/` - Add "Enter Arena" button to bot config

### Database (Optional)
- Add `arena_registered_at` timestamp column
- Add `arena_season` column for future seasons

---

## Timeline

### Jan 7 (Tonight)
- [ ] Update arena page copy (Season 1 framing)
- [ ] Add countdown timer component
- [ ] Add "Training Ground" section for prototype bots
- [ ] Create registration endpoint (backend)
- [ ] Create registration modal (frontend)
- [ ] Add ggArena to navbar
- [ ] Fix critical polish items

### Jan 8 (Tomorrow)
- [ ] Post launch tweet + video
- [ ] Monitor registrations
- [ ] Draft email announcement

### Jan 8-20
- [ ] Polish items
- [ ] Community engagement
- [ ] Create bulk reset script
- [ ] Test reset on staging

### Jan 21 12:00 UTC
- [ ] Execute bulk reset
- [ ] Announce competition start
- [ ] Monitor first 24 hours

---

## Success Metrics

- **Registrations**: Target 20+ bots by Jan 21
- **Engagement**: Daily active viewers on arena page
- **Conversions**: Users who create bots after visiting arena
- **Retention**: Registered users who stay active through competition
