-- Migration 013: Final RLS optimization fix
-- Fixed syntax for policy cleanup and recreation
-- Date: 2025-01-04

BEGIN;

-- =====================================================
-- STEP 1: Drop all existing policies manually
-- =====================================================

-- Drop all known policies that might exist
DROP POLICY IF EXISTS "Users can only access their own configurations" ON configurations;
DROP POLICY IF EXISTS "Users can only access their own decisions" ON decisions;  
DROP POLICY IF EXISTS "Users can only access their own market data" ON market_data;
DROP POLICY IF EXISTS "Users can only access their own paper accounts" ON paper_accounts;
DROP POLICY IF EXISTS "Users can only access their own paper trades" ON paper_trades;
DROP POLICY IF EXISTS "Users can only access their own paper orders" ON paper_orders;
DROP POLICY IF EXISTS "Users can only access their own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can only access their own LLM credentials" ON user_llm_credentials;
DROP POLICY IF EXISTS "Users can only access their own bot channels" ON bot_telegram_channels;

-- Drop all variations of logs policies
DROP POLICY IF EXISTS "Users can access their own logs and system logs" ON logs;
DROP POLICY IF EXISTS "User and system logs access" ON logs;
DROP POLICY IF EXISTS "Users can insert their own logs" ON logs;
DROP POLICY IF EXISTS "Users can only access their own logs" ON logs;
DROP POLICY IF EXISTS "System logs are accessible to authenticated users" ON logs;

-- =====================================================
-- STEP 2: Create optimized policies with proper syntax
-- =====================================================

-- User-specific table policies with optimized auth.uid()
CREATE POLICY "optimized_configurations_access" ON configurations
    FOR ALL USING (user_id = (SELECT auth.uid()));

CREATE POLICY "optimized_decisions_access" ON decisions
    FOR ALL USING (user_id = (SELECT auth.uid()));

CREATE POLICY "optimized_market_data_access" ON market_data
    FOR ALL USING (user_id = (SELECT auth.uid()));

CREATE POLICY "optimized_paper_accounts_access" ON paper_accounts
    FOR ALL USING (user_id = (SELECT auth.uid()));

CREATE POLICY "optimized_paper_trades_access" ON paper_trades
    FOR ALL USING (user_id = (SELECT auth.uid()));

CREATE POLICY "optimized_paper_orders_access" ON paper_orders
    FOR ALL USING (user_id = (SELECT auth.uid()));

CREATE POLICY "optimized_user_profiles_access" ON user_profiles
    FOR ALL USING (user_id = (SELECT auth.uid()));

CREATE POLICY "optimized_llm_credentials_access" ON user_llm_credentials
    FOR ALL USING (user_id = (SELECT auth.uid()));

-- Bot channels policy (through config relationship)
CREATE POLICY "optimized_bot_channels_access" ON bot_telegram_channels
    FOR ALL USING (
        config_id IN (
            SELECT config_id FROM configurations 
            WHERE user_id = (SELECT auth.uid())
        )
    );

-- Logs policy - users see their own logs OR system logs with null user_id
CREATE POLICY "optimized_logs_select" ON logs
    FOR SELECT USING (
        user_id = (SELECT auth.uid()) OR 
        user_id IS NULL
    );

-- Allow users to insert their own logs
CREATE POLICY "optimized_logs_insert" ON logs
    FOR INSERT WITH CHECK (user_id = (SELECT auth.uid()));

COMMIT;

-- =====================================================
-- Verification - Check all policies are optimized
-- =====================================================

SELECT 
    tablename,
    policyname,
    cmd as operation,
    CASE 
        WHEN qual ~ 'auth\.uid\(\)' AND qual !~ 'SELECT auth\.uid\(\)' THEN '❌ NOT OPTIMIZED'
        WHEN qual ~ 'SELECT auth\.uid\(\)' THEN '✅ OPTIMIZED'
        WHEN qual ~ 'auth\.role\(\)' AND qual !~ 'SELECT auth\.role\(\)' THEN '⚠️ ROLE NOT OPTIMIZED'
        ELSE '✅ OK'
    END as optimization_status
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;