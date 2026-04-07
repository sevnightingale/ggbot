-- Arena Agents: Hyperliquid Subaccount Address
-- Stores the per-agent Hyperliquid subaccount address that DGClaw uses for
-- on-chain execution. Captured opportunistically by the /status endpoint
-- whenever the DGClaw Railway backend exposes it (i.e., during an active
-- position). Used by sync_closes_from_hl() to backfill arena_exit activities
-- for DGClaw server-side TP/SL closes that never produce an ACP job.

ALTER TABLE arena_agents
  ADD COLUMN IF NOT EXISTS hl_subaccount_address VARCHAR(42);

-- Partial index: only agents where we've captured the address. Keeps the
-- index small (most agents populated, but the condition is still a clean
-- filter for future lookups by subaccount).
CREATE INDEX IF NOT EXISTS idx_arena_agents_hl_subaccount
  ON arena_agents(hl_subaccount_address)
  WHERE hl_subaccount_address IS NOT NULL;

COMMENT ON COLUMN arena_agents.hl_subaccount_address IS
  'Hyperliquid subaccount address used by DGClaw for this agent. '
  'Captured from Railway /users/{wallet}/account when an active position '
  'exposes it. Used to query Info.user_fills for close backfill.';
