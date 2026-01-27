# CONTEXT.md - Cross-Session Coordination

**Purpose**: Coordination between two Claude Code instances working in parallel.

---

## Current Situation (2026-01-26)

We're doing two related pieces of work:

1. **Frontend Snappiness** - React Query integration to fix sluggish UI
2. **USX Staking Modal** - wagmi/viem for Scroll blockchain integration (Arena page only)

**Architecture Decision**: Web3 dependencies are **scoped to Arena page only** to avoid bloating the rest of the app. React Query goes at root level (useful everywhere).

---

## Elegant Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Root Layout (all pages)                                    │
│  └── QueryClientProvider (React Query - ~12KB)              │
│      └── ThemeProvider                                      │
│          └── {children}                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Arena Page ONLY (lazy-loaded, ~65KB)                       │
│  └── WagmiProvider + RainbowKitProvider                     │
│      └── ArenaContent + PledgeModal                         │
└─────────────────────────────────────────────────────────────┘
```

**Why scoped?**
- Forge page stays lean (only +12KB for React Query)
- Users who never visit Arena don't load Web3 code
- Users visiting Arena but not staking can still avoid modal load
- Clean separation of concerns

---

## Work Split

### CC-A (Snappiness Session) - React Query + Performance
**Focus**: Frontend performance improvements

Tasks:
- [ ] Install `@tanstack/react-query`
- [ ] Create `frontend/lib/providers.tsx` (QueryClientProvider only)
- [ ] Wrap app in providers in layout.tsx
- [ ] Create `frontend/lib/queries.ts` with React Query hooks
- [ ] Convert forge/page.tsx to use useQuery for bots, dataSources
- [ ] Add Redis cache to `/api/v2/public/arena/performance` (30-60s TTL)
- [ ] Test arena page and bot switching feel snappy

### CC-B (USX Session) - Web3 Staking
**Focus**: Arena-scoped Web3 integration for pledging

Tasks:
- [ ] Install wagmi, viem, @rainbow-me/rainbowkit (Arena scope only)
- [ ] Create `frontend/lib/wagmi-config.ts` with Scroll chain config
- [ ] Create `frontend/lib/contracts.ts` with USX/sUSX addresses + ABIs
- [ ] Create `frontend/components/arena/ArenaWithStaking.tsx` (provider wrapper)
- [ ] Update `frontend/app/arena/page.tsx` to lazy-load ArenaWithStaking
- [ ] Create `arena_pledges` table in database
- [ ] Add `POST /api/v2/arena/pledge` endpoint
- [ ] Add `GET /api/v2/arena/pledges` endpoint
- [ ] Build `PledgeModal.tsx` component (see design section below)
- [ ] Test on Scroll mainnet

---

## Arena Page Architecture (for CC-B)

```typescript
// frontend/app/arena/page.tsx
import dynamic from 'next/dynamic'

// Lazy-load Web3-enabled arena (wagmi/rainbowkit only load here)
const ArenaWithStaking = dynamic(
  () => import('@/components/arena/ArenaWithStaking'),
  {
    ssr: false,  // Web3 needs client-side only
    loading: () => <ArenaLoadingSkeleton />
  }
)

export default function ArenaPage() {
  return <ArenaWithStaking />
}
```

```typescript
// frontend/components/arena/ArenaWithStaking.tsx
'use client'

import { WagmiProvider } from 'wagmi'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RainbowKitProvider } from '@rainbow-me/rainbowkit'
import { wagmiConfig } from '@/lib/wagmi-config'
import '@rainbow-me/rainbowkit/styles.css'

// Separate QueryClient for Web3 (doesn't conflict with root)
const web3QueryClient = new QueryClient()

export function ArenaWithStaking() {
  return (
    <WagmiProvider config={wagmiConfig}>
      <QueryClientProvider client={web3QueryClient}>
        <RainbowKitProvider>
          <ArenaContent />
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  )
}
```

---

## Frontend Design Best Practices

Reference: [Claude Frontend Design Skill](https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md)

### ggbots Already Has Strong Aesthetic
- **Tone**: Ceremonial Brutalism / Guild Hall aesthetic
- **Colors**: Obsidian (#0b0b0c), Ivory (#edebe7), Brass (#c1a87d)
- **Typography**: Bodoni Moda (display), Space Grotesk (body), IBM Plex Mono (code)
- **Philosophy**: Border-based cards, no shadows, intentional restraint

### For PledgeModal - Follow Existing Patterns
- Use CSS variables: `var(--bg-primary)`, `var(--accent)`, `var(--border)`
- Match existing modal styles (see `frontend/components/ui/modal.tsx`)
- Language: "Pledge" not "Stake", "Allegiance" for commitment
- Animation: Subtle, purposeful (staggered reveals, not scattered micro-interactions)

### AVOID (per skill guidelines)
- Generic fonts (Inter, Roboto, Arial)
- Purple gradients on white
- Cookie-cutter components that don't match ggbots aesthetic
- RainbowKit default styling without theming

### DO
- Theme RainbowKit to match brass palette
- Use existing `<Modal>` component as base
- Keep transaction states in same modal (overlay, not new screens)
- Follow the 3-state flow: Input → Processing (with steps) → Success

---

## PledgeModal Design Spec (for CC-B)

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│   ⚔️  PLEDGE YOUR ALLEGIANCE                             │
│                                                          │
│   ┌────────────────────────────────────────────────┐     │
│   │  [Bot Avatar]   The Contrarian                 │     │
│   │                 +12.4% this season     ▼       │     │
│   └────────────────────────────────────────────────┘     │
│                                                          │
│   ┌────────────────────────────────────────────────┐     │
│   │  500                                    USX    │     │
│   └────────────────────────────────────────────────┘     │
│   Balance: 1,247.50 USX                      [MAX]       │
│                                                          │
│   ┌────────────────────────────────────────────────┐     │
│   │            ⚡ Pledge 500 USX                   │     │
│   └────────────────────────────────────────────────┘     │
│                                                          │
│   You'll earn sUSX yield regardless of outcome.          │
│   If your bot wins, you share the prize pool.            │
│   ⚠️  15-day cooldown to unstake                         │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Processing state** (overlay on same modal):
```
┌──────────────────────────────────────────────────────────┐
│   ⚔️  PLEDGING...                                        │
│                                                          │
│        ● Approving USX         ✓ Done                    │
│        ○ Committing pledge     ◌ Waiting                 │
│                                                          │
│        Confirm in your wallet...                         │
└──────────────────────────────────────────────────────────┘
```

---

## Database Schema (for CC-B)

```sql
CREATE TABLE arena_pledges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  wallet_address TEXT NOT NULL,
  config_id UUID REFERENCES configurations(config_id),
  usx_amount DECIMAL(20, 6) NOT NULL,
  tx_hash TEXT NOT NULL UNIQUE,  -- prevents double-recording
  pledged_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_arena_pledges_user ON arena_pledges(user_id);
CREATE INDEX idx_arena_pledges_config ON arena_pledges(config_id);
```

---

## Contract Addresses (Scroll Mainnet)

CC-B needs to research and fill in:
- USX Token: `0x...` (find on Scrollscan)
- sUSX Vault: `0x...` (find on docs.usx.capital)

**Important**: sUSX has 15-day unstaking cooldown - communicate clearly in UI.

---

## Files Each Session Touches

**CC-A (Snappiness)** - No Web3 files:
- `frontend/package.json` (add @tanstack/react-query only)
- `frontend/lib/providers.tsx` (new - QueryClientProvider only)
- `frontend/lib/queries.ts` (new)
- `frontend/app/layout.tsx` (wrap with Providers)
- `frontend/app/forge/page.tsx` (convert to useQuery)
- `api/public.py` (add Redis caching)

**CC-B (USX Staking)** - Web3 scoped to Arena:
- `frontend/package.json` (add wagmi, viem, rainbowkit)
- `frontend/lib/wagmi-config.ts` (new)
- `frontend/lib/contracts.ts` (new)
- `frontend/components/arena/ArenaWithStaking.tsx` (new - provider wrapper)
- `frontend/components/arena/PledgeModal.tsx` (new)
- `frontend/app/arena/page.tsx` (lazy-load ArenaWithStaking)
- `ggbot.py` or `api/public.py` (pledge endpoints)
- Database migration for `arena_pledges`

**No overlap** - clean separation.

---

## Status Updates

_Update this section as work progresses_

- [x] **CC-A**: React Query installed (2026-01-27)
- [x] **CC-A**: providers.tsx created (QueryClientProvider only)
- [x] **CC-A**: Layout wrapped
- [x] **CC-A**: queries.ts hooks created (useArenaPerformance)
- [x] **CC-A**: Arena Redis caching added (60s TTL)
- [x] **CC-A**: Arena page converted to use React Query
- [ ] **CC-B**: wagmi deps installed
- [ ] **CC-B**: ArenaWithStaking wrapper created
- [ ] **CC-B**: PledgeModal built
- [ ] **CC-B**: Backend endpoints done
- [ ] **Both**: Integration tested

---

## Sources

- [Claude Frontend Design Skill](https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md)
- [Improving Frontend Design Through Skills](https://claude.com/blog/improving-frontend-design-through-skills)
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)
