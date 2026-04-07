# Arena Sync Closes — Close Backfill from HL Fills

**Status**: ✅ COMPLETE (2026-04-07)
**Commit**: `08991ed fix: arena — backfill exits from HL fills (server-side closes were silent)`
**Module doc**: [trading/virtuals/README.md](../../trading/virtuals/README.md) § "Close Backfill from HL Fills"
**Changelog**: [CHANGELOG.md § 2026-04-07](../../CHANGELOG.md)

---

## Problem

DGClaw arena positions can close through 5 paths. Four of them produce an ACP
job and fire `arena_sync.mirror_close_to_arena`, which logs an `arena_exit`
activity. The fifth — **DGClaw's own server-side TP/SL execution** — does not,
because DGClaw monitors the levels itself and executes directly on Hyperliquid.
The position simply disappears from Railway with no trace in our DB.

Evidence on ggbot-004 at the time of implementation: 4 round-trip trades on
Hyperliquid, only 3 matching `arena_exit` activities. The Apr 5 22:02 BTC close
at $67,651 (`oid=371386016564`) was completely invisible.

## Solution

Pure backend backfill, no frontend changes:

1. **Schema** (`database/migrations/add_hl_subaccount_to_arena_agents.sql`) —
   new `arena_agents.hl_subaccount_address VARCHAR(42)` column + partial index.
2. **Opportunistic capture** in `api/virtuals_arena.py:get_arena_status()` —
   when `claw_api.get_dgclaw_account()` returns a populated `hl_subaccount`
   (only during active positions), persist it with an
   `UPDATE ... WHERE hl_subaccount_address IS NULL` guard. System self-heals:
   every agent gets captured on its next active trade. ggbot-004 seeded
   directly via SQL because its gap was known.
3. **Sync function** `sync_closes_from_hl()` in
   `trading/virtuals/arena_sync.py` — queries `Info.user_fills_by_time` for
   the last 7 days, filters to Close fills, groups partial fills by
   `(coin, 5s bucket, dir)`, dedups by `hl_order_id` (primary) and
   `(pair, created_at ± 60s)` (secondary, for legacy rows from other close
   paths that don't carry the HL oid), and inserts with `created_at` set to
   the historical fill time so rows slot into TVTimeline at the right
   position.
4. **Invocation** from the same `/status` endpoint, awaited inline, wrapped in
   try/except. Redis 60s throttle
   (`arena:sync_closes_last_run:{agent_id}`) keeps the poll path cheap —
   real HL queries fire at most once per minute per modal session.
5. **No frontend work** — both the DegenArenaModal
   (`degen-arena-modal.tsx:21`) and TVTimeline (`tv-timeline.tsx:806`)
   already poll every 10 seconds, so new rows land in the UI automatically.

## Approach Rejected

An earlier planning pass proposed a user-facing "Sync Closes" button in the
modal, a new `POST /sync-closes` endpoint, a `syncArenaCloses(configId)` API
method, a custom `arena-activities-updated` event, and a listener in
TVTimeline. All of it turned out to be unnecessary once the existing 10s
poll loops on the modal and the timeline were taken into account. The
implemented version is ~60% less code and zero frontend churn.

## Verification

End-to-end against production data before code left the repo:

- Migration applied, column + partial index present
- `ggbot-004` seeded, `hl_subaccount_address` populated
- First sync run: inserted exactly 1 row (Apr 5 22:02:55 close,
  `oid=371386016564`, `close_reason='dgclaw_server_side'`, historical
  `created_at`)
- Run 2 (throttle active): returned 0
- Run 3 (throttle cleared, dedup by oid): returned 0
- `hl_sync` row count stable at 1 after 3 runs
- Redis TTL on throttle key: 60s as expected
- Final `arena_exit` breakdown for Technician: `arena_sync=3`,
  `claw_arena=1`, `arena_reconciler=1`, `hl_sync=1`

## Files Touched

| File | Change |
|---|---|
| `database/migrations/add_hl_subaccount_to_arena_agents.sql` | NEW — column + partial index |
| `core/auth/vault_utils.py` | SELECT extended to return `hl_subaccount_address` in `VaultManager.get_arena_credential_by_config` |
| `trading/virtuals/arena_sync.py` | NEW `sync_closes_from_hl()` function alongside the existing close-mirroring code |
| `api/virtuals_arena.py` | `get_arena_status()` — opportunistic capture + invocation of `sync_closes_from_hl` |

## Follow-Ups

- Every other assigned agent (Denis's 10 + admin) self-heals on their next
  active DGClaw position. No backfill script needed.
- If live close paths (`arena_sync`, `claw_arena`, `arena_reconciler`) ever
  start recording `hl_order_id` in their details, the secondary
  `(pair, ±60s)` dedup becomes a no-op and can be removed.
