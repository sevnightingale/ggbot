-- Migration: add arena_agents_v2 table for ACP v2 direct-HL architecture
--
-- In v1, `arena_agents` was a pool of pre-created DGClaw-owned bots that we
-- assigned to configs on demand. The bot still traded via its own `trading_mode`
-- (paper/hyperliquid) and trades were mirrored to DGClaw via a job queue.
--
-- In v2, the Virtuals agent *is* the Hyperliquid trader — one wallet, one path,
-- no mirror. Each `trading_mode='virtuals'` config owns exactly one row in
-- arena_agents_v2, which holds the Privy wallet identity + all three vault
-- references the orchestrator needs to sign and trade.
--
-- Credential columns:
--   - signer_private_key_vault_id  (REQUIRED)
--       P-256 signer key registered as delegated signer on the Privy wallet.
--       Used by acp-node sidecar to authenticate every Privy action
--       (userSetAbstraction, approveAgent, withdraw3, sendCalls, etc.).
--
--   - hl_api_wallet_key_vault_id   (set after /authorize-hl-api-wallet)
--       Plain secp256k1 private key authorized on HL to trade on the agent
--       wallet's behalf. Used by hyperliquid_service for every market order.
--       Cannot withdraw — protocol-enforced.
--
--   - dgclaw_api_key_vault_id      (set after /join-leaderboard, optional)
--       Claw-side API key returned by the join_leaderboard ACP job. Used for
--       DGClaw-side queries only; trades flow through HL directly in v2.
--
-- Status lifecycle: provisioning → active → retired.
-- The unique-active index prevents two active v2 agents on the same config.

CREATE TABLE IF NOT EXISTS arena_agents_v2 (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    config_id uuid REFERENCES configurations(config_id) ON DELETE RESTRICT,

    -- Virtuals identity
    virtuals_agent_id text NOT NULL,
    agent_name text NOT NULL,
    agent_wallet_address varchar(42) NOT NULL,
    wallet_id text NOT NULL,                          -- Privy wallet ID

    -- Vault references
    signer_private_key_vault_id uuid NOT NULL,
    hl_api_wallet_key_vault_id uuid,
    dgclaw_api_key_vault_id uuid,

    -- Optional forum wiring for AI Council reasoning posts
    dgclaw_forum_thread_id text,

    -- Lifecycle
    status text NOT NULL DEFAULT 'provisioning'
        CHECK (status IN ('provisioning', 'active', 'retired')),

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE (virtuals_agent_id)
);

CREATE INDEX IF NOT EXISTS idx_arena_v2_user
    ON arena_agents_v2(user_id);

CREATE INDEX IF NOT EXISTS idx_arena_v2_config
    ON arena_agents_v2(config_id)
    WHERE config_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_arena_v2_config_active
    ON arena_agents_v2(config_id)
    WHERE config_id IS NOT NULL AND status = 'active';

CREATE INDEX IF NOT EXISTS idx_arena_v2_wallet
    ON arena_agents_v2(agent_wallet_address);
