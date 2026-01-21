# Unified Modal System

**Status**: 🔵 PLANNED
**Complexity**: Medium (~6-8 hours)
**Priority**: Medium - UX consistency improvement

---

## Problem

The frontend has 8 different modals with inconsistent implementations:

| Modal | System | Width | Issues |
|-------|--------|-------|--------|
| SettingsModal | Radix Dialog | `max-w-2xl` | Uses `dark:` prefix (broken with data-theme) |
| UpgradeModal | Radix Dialog | `max-w-sm` | Tiny on large screens |
| AddCreditsModal | Radix Dialog | `max-w-sm` | Tiny on large screens |
| ArenaRegistrationModal | Radix Dialog | `max-w-md` | No responsive scaling |
| BotCreationModal | Radix Dialog | `max-w-2xl` | Custom close button handling |
| RiskAcknowledgmentModal | Custom | `max-w-2xl` | Different backdrop (`/70`), no animation |
| TradeHistoryModal | Custom | `max-w-6xl` | Different backdrop (`/50`), `rounded-2xl` |
| activity-modal | Framer Motion | `500px` | Gold border (inconsistent), good animation |

**Inconsistencies**:
- 3 different modal systems (Radix, custom, Framer Motion)
- Backdrop opacity varies (`/50`, `/60`, `/70`, `/80`)
- Border radius varies (`rounded-lg`, `rounded-xl`, `rounded-2xl`)
- Background color split (`--bg-primary` vs `--bg-secondary`)
- No responsive scaling (modals look tiny on ultrawides)
- Mobile handling inconsistent (only activity-modal has touch support)

---

## Solution

Create a unified `Modal` component with:
- Framer Motion animations (from activity-modal)
- Responsive widths that scale with screen size
- Full-screen takeover on mobile (below 640px)
- Consistent visual treatment following VIBE.md
- Proper CSS variable usage (no `dark:` prefixes)

---

## Design Decisions

1. **Animation**: Framer Motion - fade backdrop + scale/fade modal
2. **Backdrop**: `bg-black/60 backdrop-blur-sm` (standardized)
3. **Border**: `border-[var(--border)]` (remove gold border from activity-modal)
4. **Radius**: `rounded-xl` (standardized)
5. **Background**: `--bg-secondary` (modals float above page)
6. **Mobile**: Full-screen takeover below `sm` breakpoint (640px)

---

## Component API

### Size Variants (Responsive)
```tsx
const SIZES = {
  sm:   'sm:max-w-md  lg:max-w-lg',     // 448→512px (focused actions)
  md:   'sm:max-w-lg  lg:max-w-xl',     // 512→576px (detail views)
  lg:   'sm:max-w-xl  lg:max-w-2xl',    // 576→672px (forms, settings)
  xl:   'sm:max-w-2xl lg:max-w-3xl',    // 672→768px (wizards)
  full: 'sm:max-w-4xl lg:max-w-6xl',    // 896→1152px (data tables)
}
```

### Sub-components
- `Modal` - Main wrapper with Framer Motion
- `ModalHeader` - Title, description, close button
- `ModalBody` - Scrollable content area
- `ModalFooter` - Action buttons

### Props
```tsx
interface ModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  preventClose?: boolean  // For forced modals (onboarding)
  children: React.ReactNode
}
```

---

## Migration Map

| Current Modal | New Size | Special Handling |
|---------------|----------|------------------|
| AddCreditsModal | `sm` | Simple migration |
| UpgradeModal | `sm` | Simple migration |
| ArenaRegistrationModal | `sm` | Simple migration |
| SettingsModal | `lg` | Fix `dark:` prefixes |
| RiskAcknowledgmentModal | `lg` | Convert from custom |
| BotCreationModal | `xl` | Handle `preventClose` |
| TradeHistoryModal | `full` | Convert from custom |
| activity-modal | `md` | Keep unique nav features, remove gold border |

---

## Implementation Phases

### Phase 1: Create Base Component
- [ ] Create `components/ui/modal.tsx` with Framer Motion
- [ ] Implement size variants and responsive behavior
- [ ] Test with simple example

### Phase 2: Migrate Simple Modals
- [ ] `AddCreditsModal.tsx` → size `sm`
- [ ] `UpgradeModal.tsx` → size `sm`
- [ ] `ArenaRegistrationModal.tsx` → size `sm`

### Phase 3: Migrate Complex Modals
- [ ] `SettingsModal.tsx` → size `lg`, fix `dark:` prefixes
- [ ] `RiskAcknowledgmentModal.tsx` → size `lg`
- [ ] `BotCreationModal.tsx` → size `xl`, `preventClose`

### Phase 4: Migrate Data-Heavy Modals
- [ ] `TradeHistoryModal.tsx` → size `full`
- [ ] `activity-modal.tsx` → size `md`, keep navigation features

### Phase 5: Cleanup
- [ ] Remove unused Radix Dialog imports
- [ ] Update/deprecate `components/ui/dialog.tsx`

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `components/ui/modal.tsx` | **CREATE** |
| `components/AddCreditsModal.tsx` | Migrate |
| `components/UpgradeModal.tsx` | Migrate |
| `components/arena-registration-modal.tsx` | Migrate |
| `components/SettingsModal.tsx` | Migrate + fix theme |
| `components/RiskAcknowledgmentModal.tsx` | Migrate |
| `app/forge/components/modals/BotCreationModal.tsx` | Migrate |
| `app/forge/components/monitor/TradeHistoryModal.tsx` | Migrate |
| `components/activity-modal.tsx` | Update |

---

## Verification

1. **Build**: `cd frontend && npm run build` - no TypeScript errors
2. **Responsive**: Test each modal at 375px (mobile), 768px (tablet), 1920px+ (desktop)
3. **Theme**: Toggle light/dark mode - all modals render correctly
4. **Animation**: Smooth fade + scale on open/close
5. **Keyboard**: Escape closes (except preventClose modals)
6. **Backdrop**: Click outside closes (except preventClose)
7. **Mobile**: Full-screen on small devices

---

## Related Files
- `frontend/VIBE.md` - Design system reference
- `frontend/components/ui/dialog.tsx` - Current Radix Dialog (may deprecate)
