-- Migration: elo_history.config_id → ON DELETE CASCADE
--
-- Why: Deleting a bot with Elo history (29 configs currently affected) raised
-- ForeignKeyViolation on elo_history_config_id_fkey. The service caught it as
-- a generic exception and returned False → endpoint returned a misleading
-- 404 "Configuration not found" when the config did exist.
--
-- Fix rationale: elo_history is a pure audit trail of rating changes; nothing
-- downstream reads it once the bot is gone. Cascading deletion is safe.
--
-- Intentionally NOT modified: arena_pledges, arena_registrations, dojo_matches.
-- Those link to on-chain stakes / competition results where orphaned config
-- references must be preserved for fund safety and prize resolution.

ALTER TABLE elo_history
    DROP CONSTRAINT IF EXISTS elo_history_config_id_fkey;

ALTER TABLE elo_history
    ADD CONSTRAINT elo_history_config_id_fkey
    FOREIGN KEY (config_id)
    REFERENCES configurations(config_id)
    ON DELETE CASCADE;
