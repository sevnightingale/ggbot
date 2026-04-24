-- 2026-04-24: Extend arena_agents_v2 with token/subaccount state
--
-- token_address: $GG-style token contract on Base, populated from
--   https://api.acp.virtuals.io/agents/wallet/{wallet} → chains[0].tokenAddress
--   once the user tokenizes their agent. Acts as the "is tokenized" flag for
--   modal gating — untokenized agents can't receive leaderboard deliverables.
--
-- hl_subaccount_address: DGClaw exposes this opportunistically during active
--   trading via the Railway backend (/users/{wallet}/account). Capturing it
--   powers v2 close-sync from HL fills, mirroring the v1 arena_sync path.

ALTER TABLE arena_agents_v2
  ADD COLUMN IF NOT EXISTS token_address TEXT,
  ADD COLUMN IF NOT EXISTS hl_subaccount_address TEXT;

CREATE INDEX IF NOT EXISTS idx_arena_agents_v2_token_address
  ON arena_agents_v2(token_address)
  WHERE token_address IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_arena_agents_v2_hl_subaccount
  ON arena_agents_v2(hl_subaccount_address)
  WHERE hl_subaccount_address IS NOT NULL;
