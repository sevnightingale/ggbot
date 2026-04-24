-- Migration: extend configurations.valid_trading_mode CHECK to include 'virtuals'
--
-- The pre-Phase-2 passive plumbing PR added 'virtuals' to all application-layer
-- validation and UI filters but missed this database-level CHECK. Without this
-- change, any attempt to INSERT a config with trading_mode='virtuals' fails
-- with psycopg2.errors.CheckViolation, which is why Deploy Live Version has
-- been 500ing at the config-duplication step.
--
-- Idempotent: DROP IF EXISTS + re-add keeps the full enum of supported modes.

ALTER TABLE configurations
    DROP CONSTRAINT IF EXISTS valid_trading_mode;

ALTER TABLE configurations
    ADD CONSTRAINT valid_trading_mode
    CHECK (trading_mode IN ('paper', 'symphony', 'aster', 'hyperliquid', 'virtuals'));
