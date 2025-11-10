-- ============================================================================
-- Configuration Schema Migration v2.2
-- Date: 2025-11-10
--
-- This migration:
-- 1. Migrates autonomous_trading ’ scheduled_trading (373 configs)
-- 2. Removes trading.execution_mode duplication from JSONB
-- 3. Removes trading.exchange_config legacy bloat from JSONB
-- 4. Removes trading.provider from agent configs
-- 5. Updates schema_version to 2.2
-- 6. Adds database constraints
--
-- IMPORTANT: This is a one-shot migration with NO backward compatibility
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Migrate config_type (autonomous_trading ’ scheduled_trading)
-- ============================================================================

UPDATE configurations
SET
    config_type = 'scheduled_trading',
    updated_at = NOW()
WHERE config_type = 'autonomous_trading';

-- ============================================================================
-- STEP 2: Remove trading.execution_mode from JSONB
-- ============================================================================

UPDATE configurations
SET config_data = jsonb_set(
    config_data,
    '{trading}',
    (config_data->'trading') - 'execution_mode'
)
WHERE config_data->'trading'->'execution_mode' IS NOT NULL;

-- ============================================================================
-- STEP 3: Remove trading.exchange_config from JSONB
-- ============================================================================

UPDATE configurations
SET config_data = jsonb_set(
    config_data,
    '{trading}',
    (config_data->'trading') - 'exchange_config'
)
WHERE config_data->'trading'->'exchange_config' IS NOT NULL;

-- ============================================================================
-- STEP 4: Remove trading.provider from agent configs
-- ============================================================================

UPDATE configurations
SET config_data = jsonb_set(
    config_data,
    '{trading}',
    (config_data->'trading') - 'provider'
)
WHERE config_type = 'agent'
  AND config_data->'trading'->'provider' IS NOT NULL;

-- ============================================================================
-- STEP 5: Update schema_version to 2.2
-- ============================================================================

UPDATE configurations
SET config_data = jsonb_set(
    config_data,
    '{schema_version}',
    '"2.2"'
);

-- ============================================================================
-- STEP 6: Add database constraints
-- ============================================================================

-- Drop existing constraints if they exist (idempotent)
ALTER TABLE configurations DROP CONSTRAINT IF EXISTS valid_config_type;
ALTER TABLE configurations DROP CONSTRAINT IF EXISTS valid_trading_mode;
ALTER TABLE configurations DROP CONSTRAINT IF EXISTS valid_state;

-- Add constraints
ALTER TABLE configurations
ADD CONSTRAINT valid_config_type
CHECK (config_type IN ('scheduled_trading', 'signal_validation', 'agent'));

ALTER TABLE configurations
ADD CONSTRAINT valid_trading_mode
CHECK (trading_mode IN ('paper', 'symphony', 'aster'));

ALTER TABLE configurations
ADD CONSTRAINT valid_state
CHECK (state IN ('active', 'inactive', 'archived'));

-- Make trading_mode NOT NULL (has default 'paper')
ALTER TABLE configurations
ALTER COLUMN trading_mode SET NOT NULL;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify config_type distribution
SELECT 'config_type_distribution' as check_name, config_type, COUNT(*) as count
FROM configurations
GROUP BY config_type
ORDER BY count DESC;

-- Verify trading_mode distribution
SELECT 'trading_mode_distribution' as check_name, trading_mode, COUNT(*) as count
FROM configurations
GROUP BY trading_mode
ORDER BY count DESC;

-- Verify schema_version
SELECT 'schema_version' as check_name, config_data->>'schema_version' as version, COUNT(*) as count
FROM configurations
GROUP BY config_data->>'schema_version';

-- Verify no execution_mode remains
SELECT 'execution_mode_check' as check_name, COUNT(*) as remaining_count
FROM configurations
WHERE config_data->'trading'->'execution_mode' IS NOT NULL;

-- Verify no exchange_config remains
SELECT 'exchange_config_check' as check_name, COUNT(*) as remaining_count
FROM configurations
WHERE config_data->'trading'->'exchange_config' IS NOT NULL;

-- Verify no provider remains
SELECT 'provider_check' as check_name, COUNT(*) as remaining_count
FROM configurations
WHERE config_data->'trading'->'provider' IS NOT NULL;

COMMIT;
