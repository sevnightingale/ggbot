# Activity Log Export

---
COMPLETED: 2026-04-07
CHANGELOG_ENTRY: ## 2026-04-07 - Activity Log Export (Forge → Download)
TODO_SECTION: Activity Log Export
---

**Status**: ✅ SHIPPED (2026-04-07)
**Owner**: Sev
**Origin**: User request — enable large-scale review/analysis of bot activity timelines (2026-04-07)
**Scope**: Single bot, owner-only, JSON download

---

## Problem

Users can see their bot's activity timeline in the TVTimeline component (Forge Monitor tab), but there is no way to pull that data out for offline review, spreadsheet analysis, notebook exploration, or long-range pattern hunting. The existing `GET /api/v2/activities/{config_id}` endpoint hard-caps at 1000 rows and flattens the schema for the timeline viewer's rendering needs — making it unusable as an export source for any bot past p90 (>2,363 activities).

## Goal

Let a bot owner download a compressed JSON file containing every activity row for their bot within a selected time range (up to 90 days), including full LLM prompts and account-state snapshots, in a format suitable for analysis tooling.

## Non-Goals

- Multi-bot / account-wide export (single bot only)
- Public export (owner-only, no admin fallback needed)
- CSV format (JSON only — nested `details` JSONB doesn't flatten cleanly)
- Streaming response (in-memory build is fine for the ~25 MB worst case)
- Billing or LLM cost/token data in export (excluded by design — users shouldn't debate costs)
- Background job + signed URL (direct download is simpler at current scale)

---

## Production Scale Context (2026-04-07)

| Metric | Value |
|--------|-------|
| Total rows in `activities` | 141,643 |
| Table size | 421 MB |
| Avg row size | ~957 bytes |
| Bot p50 | 7 activities |
| Bot p90 | 2,363 activities |
| Bot p99 | 8,849 activities |
| Bot max | 16,388 activities |

**Per-bot export size estimate**: p99 bot with full prompts ~= 15-25 MB uncompressed, ~3-5 MB gzipped. Well within single-response territory.

**Activity type breakdown**:
- `llm_thought` (47.6%) — carries full LLM prompts in `details.prompt`
- `market_query` (47.5%) — carries extraction payloads in `details`
- `trade_entry` / `trade_exit` (2.2% each)
- Other: `strategy_updated`, `bot_created`, `arena_*`, `deposit`, `withdrawal`

---

## Design Decisions

### Scope: Single bot, owner-only
- One `config_id` per export request
- Authenticated user must own the config (`config.user_id == session.user.id`)
- No admin fallback — not needed per user feedback
- Public `/view/{config_id}` viewers do NOT see the export button

### Time range: Required, capped at 90 days
- Modal enforces both `start_time` and `end_time` before enabling Download
- Max range = 90 days (both UI and backend validate)
- Quick presets: "Last 24h", "Last 7 days", "Last 30 days", "Last 90 days"
- No "all time" option — the 90-day cap is the ceiling

### Columns: 16 of 26 (billing/tokens stripped)

**Included**:
- Identity: `activity_id`, `config_id`
- Classification: `activity_type`, `activity_source`
- Content: `summary`, `details` (full JSONB, full prompts passed through as-is)
- Linkage: `trade_id`, `trade_type`, `decision_id`, `related_symbol`
- Ranking: `importance`, `created_at`
- Account state: `account_balance`, `account_pnl`, `total_equity`

**Excluded** (billing/token-related):
- `provider`, `model`, `thinking_mode`
- `input_tokens`, `output_tokens`, `reasoning_tokens`
- `provider_cost_usd`, `platform_cost_usd`
- `stripe_reported`, `stripe_reported_at`
- `user_id` (internal, not useful for export consumer)

**Note**: The `details` JSONB passes through untransformed. If any future activity type starts storing token counts or costs inside `details`, those will leak through — not scrubbed deep. Document this in the endpoint docstring.

### Format: JSON + gzip
- Single `application/json` response body
- `Content-Encoding: gzip` — browser decompresses transparently on download
- `Content-Disposition: attachment; filename="..."` — triggers save dialog

### Response structure

```json
{
  "export_metadata": {
    "config_id": "b523154c-2d2e-4a67-991a-af380994e645",
    "bot_name": "RSI Scalper v2",
    "exported_at": "2026-04-07T10:45:00.000Z",
    "start_time": "2026-03-01T00:00:00.000Z",
    "end_time": "2026-04-07T10:45:00.000Z",
    "row_count": 2363
  },
  "activities": [
    {
      "activity_id": "uuid",
      "config_id": "uuid",
      "activity_type": "llm_thought",
      "activity_source": "decision_engine",
      "summary": "Evaluated BTC/USDT long opportunity",
      "details": { "prompt": "...", "response": "...", "reasoning": "..." },
      "trade_id": null,
      "trade_type": null,
      "decision_id": "uuid",
      "related_symbol": "BTC/USDT",
      "importance": 7,
      "created_at": "2026-04-07T10:23:15.234Z",
      "account_balance": 10234.50,
      "account_pnl": 234.50,
      "total_equity": 10234.50
    }
    // ... more rows
  ]
}
```

### Filename convention
`{bot_name_slug}_activities_{start_date}_to_{end_date}.json.gz`

Example: `rsi-scalper-v2_activities_2026-03-01_to_2026-04-07.json.gz`

**Slug rules**: lowercase, alphanumeric + hyphens, max 40 chars, fallback to `bot_{short_config_id}` if name is empty.

---

## Implementation

### Backend: `api/activities.py`

**New endpoint**: `GET /api/v2/activities/{config_id}/export`

**Query params**:
| Name | Type | Required | Validation |
|------|------|----------|------------|
| `start_time` | ISO timestamp | Yes | Valid ISO-8601 |
| `end_time` | ISO timestamp | Yes | Valid ISO-8601, > start_time, ≤ now |

**Auth**: `Depends(get_current_user_v2)` — injects `AuthenticatedUser`

**Flow**:
1. Parse/validate `start_time` and `end_time` (return 400 on invalid)
2. Enforce 90-day max range (return 400 if `end_time - start_time > 90 days`)
3. Query `configurations` WHERE `config_id = %s` — fetch `user_id`, `config_name`
4. Verify `config.user_id == session.user.id` (return 403 if not)
5. Query `activities` WHERE `config_id = %s AND created_at >= %s AND created_at <= %s ORDER BY created_at ASC` — uses existing `idx_activities_config_billing(config_id, created_at)` index
6. Transform each row to the 16-field dict (drop billing/token cols)
7. Build `{export_metadata, activities}` dict
8. Serialize to JSON with `json.dumps(..., default=str)` (handles datetime, UUID, Decimal)
9. `gzip.compress(json_bytes)`
10. Return `fastapi.Response` with:
    - `content=gzipped_bytes`
    - `media_type="application/json"`
    - Headers: `Content-Encoding: gzip`, `Content-Disposition: attachment; filename="..."`

**Estimated LOC**: ~90 lines (endpoint + helper for slug + helper for row transform)

**Error responses**:
- `400` — missing/invalid time params, range >90 days, end_time before start_time
- `401` — no auth token
- `403` — config not owned by user
- `404` — config not found
- `500` — query or serialization failure (log and return generic message)

### Frontend: `frontend/components/ActivityExportModal.tsx` (NEW)

**Props**:
```typescript
interface ActivityExportModalProps {
  isOpen: boolean
  onClose: () => void
  configId: string
  botName: string
  botCreatedAt: string  // earliest possible start_time (if within 90-day cap)
}
```

**State**:
- `startTime: string` (datetime-local format)
- `endTime: string` (datetime-local format)
- `isDownloading: boolean`
- `error: string | null`

**Layout**:
- Modal backdrop + centered card (match existing `AddCreditsModal` / `BetModal` styling — brass borders, carbon background)
- Title: "Export Activity Log"
- Subtitle: `"{botName}"`
- Quick presets row: 4 buttons — "Last 24h" · "Last 7 days" · "Last 30 days" · "Last 90 days"
- Two `<input type="datetime-local">` fields labeled "From" and "To"
- Max range validator: disable Download button + show inline error if range > 90 days
- "Download" button (brass, disabled when invalid) + "Cancel" button
- Loading state: spinner on Download button while fetch is in flight

**Download handler**:
```typescript
async function handleDownload() {
  setIsDownloading(true)
  try {
    const session = await supabase.auth.getSession()
    const token = session.data.session?.access_token
    const url = `/api/v2/activities/${configId}/export?start_time=${encodeURIComponent(startTime)}&end_time=${encodeURIComponent(endTime)}`

    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` }
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || 'Export failed')
    }

    // Let browser handle download via Content-Disposition
    const blob = await response.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    // Extract filename from Content-Disposition
    const disposition = response.headers.get('Content-Disposition') || ''
    const filenameMatch = disposition.match(/filename="(.+?)"/)
    link.download = filenameMatch?.[1] || `${configId}_activities.json.gz`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)

    onClose()
  } catch (e) {
    setError(e.message)
  } finally {
    setIsDownloading(false)
  }
}
```

**Estimated LOC**: ~140 lines

### Frontend: `frontend/components/tv-timeline.tsx` (MODIFY)

**Changes**:
1. Import `ActivityExportModal` and download icon (likely `ArrowDownTrayIcon` from `@heroicons/react/24/outline` — check existing imports first)
2. Add state: `const [isExportModalOpen, setIsExportModalOpen] = useState(false)`
3. Determine "can export" — owner check: hide button if `variant === 'standalone'` (public view) OR if current user doesn't own the config. Need to thread `isOwner: boolean` prop or check session + config ownership.
4. Add button in top-right of chart container (line 1026):
   ```tsx
   {isOwner && (
     <button
       onClick={() => setIsExportModalOpen(true)}
       className="absolute top-3 right-3 p-1.5 rounded-md border transition-colors"
       style={{ borderColor: VIBE.hair, color: VIBE.ivory }}
       title="Export activity log"
       aria-label="Export activity log"
     >
       <ArrowDownTrayIcon className="w-4 h-4" />
     </button>
   )}
   ```
5. Render modal at end of component:
   ```tsx
   <ActivityExportModal
     isOpen={isExportModalOpen}
     onClose={() => setIsExportModalOpen(false)}
     configId={configId}
     botName={metadata?.botName || 'Bot'}
     botCreatedAt={metadata?.createdAt || new Date().toISOString()}
   />
   ```

**Owner check strategy**: Add an `isOwner?: boolean` prop to `TimelineProps`. Callers in Forge pass `true`, `/view/{config_id}` standalone callers pass `false` (or omit — defaults to `false`).

**Caller updates**:
- `frontend/app/forge/...` — wherever TVTimeline is rendered in the Monitor tab → pass `isOwner={true}` (user is always looking at own bots in Forge)
- `frontend/app/view/[config_id]/page.tsx` — leave as-is (defaults to `false`)

**Estimated LOC**: ~30 lines of changes to `tv-timeline.tsx`, +1 line in Forge caller

---

## Testing Plan

### Backend (manual curl test before PR)

```bash
# Happy path — owner, valid range
curl -H "Authorization: Bearer $TOKEN" \
  "https://ggbots-api.nightingale.business/api/v2/activities/$CONFIG_ID/export?start_time=2026-03-01T00:00:00Z&end_time=2026-04-07T10:00:00Z" \
  -o export.json.gz
gunzip -c export.json.gz | jq '.export_metadata'
gunzip -c export.json.gz | jq '.activities | length'

# Range > 90 days → expect 400
curl -H "Authorization: Bearer $TOKEN" \
  ".../export?start_time=2025-01-01T00:00:00Z&end_time=2026-04-07T00:00:00Z"

# Not owner → expect 403
curl -H "Authorization: Bearer $OTHER_USER_TOKEN" \
  ".../export?start_time=..."

# No auth → expect 401
curl ".../export?start_time=..."

# Nonexistent config → expect 404
curl -H "Authorization: Bearer $TOKEN" ".../b0000000-.../export?..."
```

### Frontend (manual test after Vercel deploy)

- [ ] Button appears in top-right of TVTimeline in Forge Monitor tab
- [ ] Button is hidden on `/view/{config_id}` public page
- [ ] Modal opens on click, date inputs default to sensible values
- [ ] "Last 7 days" preset sets the date inputs correctly
- [ ] Range > 90 days shows inline error, Download button disabled
- [ ] End time in the future shows inline error
- [ ] Download produces a `.json.gz` file with correct filename
- [ ] Decompressed file parses as valid JSON with expected structure
- [ ] `export_metadata.row_count` matches `activities.length`
- [ ] Billing fields (`provider_cost_usd`, `platform_cost_usd`, `input_tokens`, etc.) NOT present in output
- [ ] Full LLM prompts present in `details.prompt` for `llm_thought` rows
- [ ] Loading state shows during fetch
- [ ] Error state shows on 403/404 (e.g. stale session)

### Scale sanity check

- Test against biggest bot (`b523154c-...`, 16,388 activities) with 90-day range → verify response completes, file is ~25 MB uncompressed / ~5 MB gzipped

---

## Rollout

1. Branch: `feature/activity-export`
2. Backend PR first → manual curl test against staging/prod
3. Frontend PR → Vercel preview deploy → user manual test
4. Merge both → monitor `pm2 logs ggbot` for any 500s on the new endpoint for first 24h
5. Announce via changelog entry + optional tweet from `x_bot/`

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Giant bot + 90 day range → memory spike on API | Query count first (cheap with index), reject if > 50k rows with friendly error |
| Malformed `details` JSONB breaks serialization | Wrap row transform in try/except per row, skip bad rows, log warning |
| User confused by gzipped file on Windows | Filename ends `.json.gz` — most tools (browsers, 7zip, tar) handle it. Add a one-line note in the modal: "Downloads as .json.gz — decompress to open as JSON" |
| Timezone confusion in date picker | `<input type="datetime-local">` uses browser local time. Convert to UTC ISO before sending to API. Show "UTC" label near inputs to reduce confusion. |

## Open Questions

None — all design decisions locked in during 2026-04-07 scoping discussion.

---

## Changelog Entry Template (for completion)

```markdown
## 2026-04-XX - Activity Log Export

- New endpoint `GET /api/v2/activities/{config_id}/export` — owner-only, time-range (max 90d), returns gzipped JSON
- Strips billing/token columns, passes full LLM prompts through
- New modal `ActivityExportModal.tsx` with date range + presets (24h/7d/30d/90d)
- Download button in top-right of TVTimeline chart (Forge Monitor only, hidden on public `/view`)
- Uses existing `idx_activities_config_billing(config_id, created_at)` index
```
