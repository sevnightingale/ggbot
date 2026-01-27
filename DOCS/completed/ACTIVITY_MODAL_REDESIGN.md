# Activity Modal Redesign

**Status**: PLANNING
**Created**: 2025-12-28
**Complexity**: Medium (~4-6 hours)

---

## Problem Statement

The current bottom sheet for activity details is poor UX:
- Text displayed as unformatted blob (1400+ characters)
- No navigation between activities (must close and click another marker)
- Mobile-unfriendly layout
- LLM reasoning output is unstructured, making it hard to scan

## Solution Overview

Replace bottom sheet with a proper centered modal featuring:
1. Carousel/swipe navigation through activities in time order
2. Better text formatting with structured sections
3. Mobile-first design (full-screen takeover on mobile, slide-over on desktop)
4. Improved LLM output instructions for structured reasoning

---

## User Flow

```
Current:
  Click marker → Bottom sheet slides up → Wall of text → Close → Click another marker

Proposed:
  Click marker → Modal opens (centered, full attention)
                 ← [Prev] [timestamp] [Next] →
                 Swipe or arrows to navigate timeline
                 Well-formatted structured content
                 [X] to close and return to chart
```

---

## Technical Components

### Part A: Modal Component Redesign

**File**: `frontend/components/activity-modal.tsx` (new, replaces bottom-sheet usage)

**Structure**:
```tsx
<ActivityModal
  isOpen={boolean}
  activities={Activity[]}
  currentIndex={number}
  onClose={() => void}
  onNavigate={(index: number) => void}
>
  <ModalHeader>
    <NavigationArrows />
    <Timestamp />
    <CloseButton />
  </ModalHeader>

  <ModalContent>
    <ActivityTypeIcon />
    <FormattedContent />  // Structured based on activity_type
  </ModalContent>

  <SwipeHandler />  // For mobile gesture support
</ActivityModal>
```

**Features**:
- Keyboard navigation (←/→ arrows, Escape to close)
- Touch swipe on mobile (react-swipeable or similar)
- Preload adjacent activities for smooth transitions
- Activity type-specific formatting

### Part B: Activity Type Formatters

Different activity types need different display formats:

**`llm_thought`**:
```
┌─────────────────────────────────────────┐
│ 🧠 Decision Analysis                    │
│ BTC/USDT @ $87,830                      │
├─────────────────────────────────────────┤
│ ACTION: WAIT                            │
│ CONFIDENCE: 40%                         │
├─────────────────────────────────────────┤
│ KEY SIGNAL                              │
│ 1H MACD rising but 5M MACD falling      │
│                                         │
│ SUPPORTING                              │
│ • RSI 47.4 in healthy range             │
│ • Stochastic bullish crossover          │
│                                         │
│ RISK                                    │
│ OBV bearish, volume below average       │
│                                         │
│ SUMMARY                                 │
│ Waiting for 5M momentum to align with   │
│ bullish 1H tide before entry.           │
└─────────────────────────────────────────┘
```

**`trade_entry`**:
```
┌─────────────────────────────────────────┐
│ 📈 Trade Opened                         │
│ LONG BTC/USDT                           │
├─────────────────────────────────────────┤
│ Entry: $87,830.00                       │
│ Size: $1,600 (5x leverage)              │
│ Confidence: 65%                         │
├─────────────────────────────────────────┤
│ Stop Loss: $83,438 (-5%)                │
│ Take Profit: $96,613 (+10%)             │
└─────────────────────────────────────────┘
```

**`trade_exit`**:
```
┌─────────────────────────────────────────┐
│ 📉 Trade Closed                         │
│ LONG BTC/USDT                           │
├─────────────────────────────────────────┤
│ Entry: $87,830.00 → Exit: $88,267.10    │
│ P&L: +$33.90 (+0.5%)                    │
│ Duration: 45 minutes                    │
│ Close Reason: Position Management       │
└─────────────────────────────────────────┘
```

**`market_query`**:
```
┌─────────────────────────────────────────┐
│ 📊 Market Data Query                    │
│ opportunity_analysis @ $87,830          │
├─────────────────────────────────────────┤
│ Timeframes: 5m, 15m, 30m, 1h, 4h, 1d    │
│ Indicators: 21                          │
│ Data Age: 5.4 seconds                   │
├─────────────────────────────────────────┤
│ [▼ Technical Analysis]   (collapsible)  │
│ [▼ Volume Confirmation]  (collapsible)  │
└─────────────────────────────────────────┘
```

### Part C: LLM Output Format Improvement

**File**: `decision/prompts/opportunity_analysis.py` (and other prompt files)

**Current**:
```
REASONING: [Explain how your strategy interprets the current market data...]
```

**Proposed**:
```
## OUTPUT FORMAT
ACTION: [long/short/wait]
CONFIDENCE: [0.000-1.000]

REASONING:
- KEY_SIGNAL: [Primary indicator/pattern driving this decision, max 15 words]
- SUPPORTING: [1-2 confirming factors, max 20 words each]
- RISK: [Main concern or counter-signal, max 15 words]
- SUMMARY: [One sentence decision logic, max 25 words]
```

**Parser Update**: `decision/engine_v2.py`
- Parse structured REASONING sections
- Store as structured JSON in `details.thought`
- Fallback to raw text if parsing fails

### Part D: Integration with TV-Timeline

**File**: `frontend/components/tv-timeline.tsx`

Changes:
1. Remove bottom-sheet import and usage
2. Add ActivityModal component
3. Pass full activities array (not just clicked one)
4. Track currentIndex state for navigation
5. Handle marker click → set index and open modal

---

## Implementation Phases

### Phase 1: Modal Component (~2 hours)
- [ ] Create `activity-modal.tsx` with basic structure
- [ ] Implement keyboard navigation (arrows, escape)
- [ ] Add mobile swipe support
- [ ] Style with VIBE.md compliance (brass accents, ceremonial brutalism)
- [ ] Add animation (slide in from bottom on mobile, fade on desktop)

### Phase 2: Activity Formatters (~1.5 hours)
- [ ] Create formatter functions for each activity type
- [ ] `formatLLMThought()` - structured reasoning display
- [ ] `formatTradeEntry()` - entry details card
- [ ] `formatTradeExit()` - exit with P&L display
- [ ] `formatMarketQuery()` - collapsible data sections
- [ ] Handle unknown activity types gracefully

### Phase 3: LLM Output Restructure (~1 hour)
- [ ] Update `opportunity_analysis.py` output format
- [ ] Update `signal_validation.py` output format
- [ ] Update `position_management.py` output format
- [ ] Update parser in `engine_v2.py` to handle structured format
- [ ] Add fallback for unstructured responses

### Phase 4: TV-Timeline Integration (~1 hour)
- [ ] Replace bottom-sheet with ActivityModal in tv-timeline.tsx
- [ ] Manage activities array and currentIndex state
- [ ] Wire up marker clicks to modal navigation
- [ ] Test full flow: click marker → modal → navigate → close

### Phase 5: Testing & Polish (~0.5 hours)
- [ ] Test on mobile viewport
- [ ] Test keyboard navigation
- [ ] Test with various activity types
- [ ] Verify existing functionality not broken

---

## Files to Modify

| File | Changes |
|------|---------|
| `frontend/components/activity-modal.tsx` | NEW - Modal component |
| `frontend/components/tv-timeline.tsx` | Replace bottom-sheet, add modal |
| `frontend/components/bottom-sheet.tsx` | DELETE or deprecate |
| `decision/prompts/opportunity_analysis.py` | Structured output format |
| `decision/prompts/signal_validation.py` | Structured output format |
| `decision/prompts/position_management.py` | Structured output format |
| `decision/engine_v2.py` | Parse structured reasoning |

---

## Dependencies

- Consider `react-swipeable` for mobile gestures (or native touch handlers)
- Framer-motion already in project for animations

---

## Success Criteria

1. Users can navigate between activities without closing modal
2. LLM reasoning is scannable in <5 seconds
3. Works smoothly on mobile (swipe gestures)
4. Works with keyboard on desktop (arrow keys)
5. All existing functionality preserved

---

## Open Questions

1. Should we preload activity content or fetch on navigation?
2. Do we want infinite scroll or bounded navigation?
3. Should clicking a chart area (not marker) close the modal?

---

## Related Files

- Current bottom-sheet: `frontend/components/bottom-sheet.tsx`
- TV-Timeline: `frontend/components/tv-timeline.tsx`
- Activity types defined in: `frontend/app/forge/components/monitor/ActivationBar.tsx`
