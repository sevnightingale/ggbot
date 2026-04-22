-- Migration: arena_agents.assigned_config_id → FK with ON DELETE RESTRICT
--
-- Why: `arena_agents.assigned_config_id` had no FK constraint, so deleting a
-- configuration would silently leave the arena agent row pointing at a
-- non-existent config. Two orphaned rows were found in production
-- (ggbot-006, ggbot-007) and cleaned up before this migration.
--
-- Why RESTRICT not CASCADE: each arena_agents row represents an assigned
-- Virtuals lite agent whose wallet holds ACP fee reserve (Base) and whose
-- DGClaw pool balance holds live trading USDC. The agent is an external
-- asset. We must NOT delete it when a config is deleted. Users must
-- explicitly release the agent (withdraw funds, return to pool) first.
--
-- App-layer guard in ggbot.py raises a 409 with a friendly message before
-- the SQL ever runs; this FK is the defense-in-depth safety net for direct
-- SQL access or missed code paths.
--
-- Prerequisite: all orphaned rows cleaned to status='available' with NULL
-- assignment fields (see migration notes 2026-04-20).

ALTER TABLE arena_agents
    ADD CONSTRAINT arena_agents_assigned_config_id_fkey
    FOREIGN KEY (assigned_config_id)
    REFERENCES configurations(config_id)
    ON DELETE RESTRICT;
