# Frontend Performance & React Query Implementation

**Created**: 2026-01-26
**Status**: 🟡 IN PROGRESS
**Assigned**: CC-A (Snappiness Session)
**Coordination**: See `CONTEXT.md` for cross-session coordination with CC-B (USX Staking)

---

## Problem Statement

### Arena Page Sluggishness
- `/api/v2/public/arena/performance` returns large payload (33 bots × 21 days × data points)
- No caching - every page visit re-fetches
- Recharts renders 33 lines with thousands of data points

### Forge Page Sluggishness
- 20+ `useState` hooks on single page (`forge/page.tsx`)
- No server state caching - re-fetches on every visit
- SSE updates cause cascading re-renders
- Bot switching shows stale data briefly

### Root Causes
1. **No server state management** - Raw `fetch()` calls with manual `useState`
2. **No response caching** - Backend returns fresh data every time
3. **Heavy chart rendering** - Too many data points for smooth performance

---

## Solution Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Root Layout                                                │
│  └── QueryClientProvider (@tanstack/react-query)            │
│      └── ThemeProvider                                      │
│          └── {children}                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Arena Page                                                 │
│  └── useArenaPerformance() hook (React Query)               │
│      └── Cached response (30s staleTime)                    │
│      └── Backend Redis cache (30-60s TTL)                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Forge Page                                                 │
│  └── useBots() hook (React Query)                           │
│  └── useDataSources() hook (React Query, 5min staleTime)    │
│  └── useUserProfile() hook (React Query)                    │
│  └── SSE updates → queryClient.setQueryData()               │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Foundation (~1 hour)

**Install Dependencies**:
```bash
cd frontend && npm install @tanstack/react-query
```

**Create Providers** (`frontend/lib/providers.tsx`):
```typescript
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  // Create QueryClient in state to avoid recreation on re-renders
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30 * 1000,        // 30 seconds
        gcTime: 5 * 60 * 1000,       // 5 minutes (formerly cacheTime)
        refetchOnWindowFocus: false,  // Disable aggressive refetching
        retry: 1,                     // Only retry once on failure
      },
    },
  }))

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
```

**Wrap App** (`frontend/app/layout.tsx`):
```typescript
import { Providers } from '@/lib/providers'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}
```

**Success Criteria**:
- [ ] Dependencies installed
- [ ] Providers.tsx created
- [ ] Layout wrapped
- [ ] App loads without errors

---

### Phase 2: Arena Performance (~1-2 hours)

**Backend: Add Redis Caching** (`api/public.py`):
```python
import redis
import json

redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
ARENA_CACHE_KEY = "arena:performance"
ARENA_CACHE_TTL = 60  # 60 seconds

@router.get("/arena/performance")
async def get_arena_performance(hours: int = Query(default=504)):
    # Try cache first
    cached = redis_client.get(ARENA_CACHE_KEY)
    if cached:
        logger.info("Arena performance: cache hit")
        return json.loads(cached)

    # ... existing query logic ...

    # Cache result
    redis_client.setex(ARENA_CACHE_KEY, ARENA_CACHE_TTL, json.dumps(result))
    return result
```

**Frontend: Create Arena Query Hook** (`frontend/lib/queries.ts`):
```typescript
import { useQuery } from '@tanstack/react-query'

export function useArenaPerformance(hours: number = 504) {
  return useQuery({
    queryKey: ['arena', 'performance', hours],
    queryFn: async () => {
      const res = await fetch(`/api/v2/public/arena/performance?hours=${hours}`)
      if (!res.ok) throw new Error('Failed to fetch arena data')
      return res.json()
    },
    staleTime: 30 * 1000,  // 30 seconds
  })
}
```

**Update Arena Page** (`frontend/app/arena/page.tsx`):
```typescript
// Replace useState + useEffect with useQuery
const { data, isLoading, error, refetch } = useArenaPerformance()
```

**Success Criteria**:
- [ ] Redis cache implemented (60s TTL)
- [ ] useArenaPerformance hook created
- [ ] Arena page converted to use hook
- [ ] Page load feels instant on revisit

---

### Phase 3: Forge Page - useBots() (~2-3 hours)

This is the biggest change. We need to:
1. Create `useBots()` hook
2. Update forge/page.tsx to use it
3. Integrate with existing SSE updates

**Create useBots Hook** (`frontend/lib/queries.ts`):
```typescript
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient, BotConfiguration } from './api'

export function useBots() {
  return useQuery({
    queryKey: ['bots'],
    queryFn: async () => {
      const result = await apiClient.listConfigs()
      return result.configs as BotConfiguration[]
    },
    staleTime: 30 * 1000,
  })
}

// Hook for SSE to update the cache directly
export function useBotsQueryClient() {
  const queryClient = useQueryClient()

  return {
    updateBots: (bots: BotConfiguration[]) => {
      queryClient.setQueryData(['bots'], bots)
    },
    invalidateBots: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] })
    },
  }
}
```

**SSE Integration Pattern**:
```typescript
// In forge/page.tsx SSE handler
const { updateBots } = useBotsQueryClient()

stream.addEventListener('dashboard', (event) => {
  const data = JSON.parse(event.data)
  if (data.bots) {
    updateBots(data.bots)  // Direct cache update, no refetch
  }
})
```

**Gradual Migration Strategy**:
1. Add `useBots()` alongside existing `allBots` state
2. Verify data matches
3. Remove old `useState` + `useEffect`
4. Update SSE to use `updateBots()`

**Success Criteria**:
- [ ] useBots() hook works
- [ ] SSE updates go through React Query
- [ ] Bot list cached between visits
- [ ] No regressions in bot switching

---

### Phase 4: Additional Hooks (~1 hour)

**useDataSources** - Long cache time, rarely changes:
```typescript
export function useDataSources() {
  return useQuery({
    queryKey: ['dataSources'],
    queryFn: () => apiClient.getDataSourcesWithPoints(),
    staleTime: 5 * 60 * 1000,  // 5 minutes
  })
}
```

**useUserProfile** - Permissions, moderate cache:
```typescript
export function useUserProfile() {
  return useQuery({
    queryKey: ['userProfile'],
    queryFn: () => apiClient.getCurrentUser(),
    staleTime: 60 * 1000,  // 1 minute
  })
}
```

---

## Files to Modify

| File | Change |
|------|--------|
| `frontend/package.json` | Add `@tanstack/react-query` |
| `frontend/lib/providers.tsx` | NEW - QueryClientProvider |
| `frontend/lib/queries.ts` | NEW - React Query hooks |
| `frontend/app/layout.tsx` | Wrap with Providers |
| `frontend/app/arena/page.tsx` | Use useArenaPerformance |
| `frontend/app/forge/page.tsx` | Use useBots (Phase 3) |
| `api/public.py` | Add Redis caching |

---

## Testing Checklist

### Arena Page
- [ ] First load fetches from API
- [ ] Second load (within 30s) uses cache
- [ ] Refresh button forces refetch
- [ ] Chart renders smoothly with 33 bots

### Forge Page (Phase 3)
- [ ] Bot list loads from cache on revisit
- [ ] SSE updates reflect immediately
- [ ] Bot switching feels instant
- [ ] No duplicate API calls
- [ ] Optimistic updates still work

### DevTools
- [ ] Install React Query DevTools for debugging
- [ ] Verify cache hits/misses

---

## Rollback Plan

If issues detected:
1. Revert `layout.tsx` to remove Providers wrapper
2. Arena page falls back to direct fetch
3. Forge page unchanged (Phase 3 not started)

React Query is additive - removing it doesn't break existing code.

---

## Success Metrics

| Metric | Before | Target |
|--------|--------|--------|
| Arena page load (revisit) | ~500ms | <100ms (cache hit) |
| Bot switching | 200-500ms flash | Instant |
| Network requests (arena) | 1 per visit | 1 per 30s max |

---

## Coordination Notes

**CC-B (USX Staking)** is working in parallel on:
- wagmi/viem/rainbowkit (scoped to Arena page only)
- PledgeModal component
- Backend pledge endpoints

**No file conflicts** - CC-A owns providers.tsx + queries.ts, CC-B owns wagmi-config.ts + contracts.ts

See `CONTEXT.md` for full coordination details.
