-- Database Migration SQL for AsterDEX Credential Storage
-- Add columns to user_profiles table

ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS aster_vault_id UUID,
ADD COLUMN IF NOT EXISTS aster_user_wallet VARCHAR(42),
ADD COLUMN IF NOT EXISTS aster_wallet VARCHAR(42);

COMMENT ON COLUMN user_profiles.aster_vault_id IS 'Reference to Supabase Vault secret containing AsterDEX private key';
COMMENT ON COLUMN user_profiles.aster_user_wallet IS 'User main Ethereum wallet address (0x...)';
COMMENT ON COLUMN user_profiles.aster_wallet IS 'AsterDEX trading wallet address (agent-controlled, 0x...)';
