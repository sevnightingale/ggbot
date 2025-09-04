-- Migration 011: Fix RLS syntax for proper optimization
-- The (select auth.uid()) syntax needs to be written correctly
-- Date: 2025-01-04

BEGIN;

-- =====================================================
-- STEP 1: Drop policies and recreate with correct syntax
-- =====================================================

-- User-specific table policies
DROP POLICY IF EXISTS "Users can only access their own configurations" ON configurations;
DROP POLICY IF EXISTS "Users can only access their own decisions" ON decisions;  
DROP POLICY IF EXISTS "Users can only access their own market data" ON market_data;
DROP POLICY IF EXISTS "Users can only access their own paper accounts" ON paper_accounts;
DROP POLICY IF EXISTS "Users can only access their own paper trades" ON paper_trades;
DROP POLICY IF EXISTS "Users can only access their own paper orders" ON paper_orders;
DROP POLICY IF EXISTS "Users can only access their own logs and system logs" ON logs;
DROP POLICY IF EXISTS "Users can only access their own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can only access their own LLM credentials" ON user_llm_credentials;
DROP POLICY IF EXISTS "Users can only access their own bot channels" ON bot_telegram_channels;

-- =====================================================
-- STEP 2: Create policies with optimized auth.uid() calls
-- =====================================================

-- Method: Use subquery to ensure auth.uid() is evaluated once
CREATE POLICY "Users can only access their own configurations" ON configurations
    FOR ALL USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can only access their own decisions" ON decisions
    FOR ALL USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can only access their own market data" ON market_data
    FOR ALL USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can only access their own paper accounts" ON paper_accounts
    FOR ALL USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can only access their own paper trades" ON paper_trades
    FOR ALL USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can only access their own paper orders" ON paper_orders
    FOR ALL USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can only access their own profile" ON user_profiles
    FOR ALL USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can only access their own LLM credentials" ON user_llm_credentials
    FOR ALL USING (user_id = (SELECT auth.uid()));

-- Bot channels policy (through config relationship)
CREATE POLICY "Users can only access their own bot channels" ON bot_telegram_channels
    FOR ALL USING (
        config_id IN (
            SELECT config_id FROM configurations 
            WHERE user_id = (SELECT auth.uid())
        )
    );

-- Logs policy - users see their own logs OR system logs with null user_id
CREATE POLICY "Users can access their own logs and system logs" ON logs
    FOR SELECT USING (
        user_id = (SELECT auth.uid()) OR 
        user_id IS NULL
    );

COMMIT;

-- =====================================================
-- Verification
-- =====================================================

-- Check if policies are now optimized
SELECT 
    tablename,
    policyname,
    CASE 
        WHEN qual LIKE '%auth.uid()%' AND qual NOT LIKE '%(SELECT auth.uid())%' THEN '❌ NOT OPTIMIZED'
        WHEN qual LIKE '%(SELECT auth.uid())%' THEN '✅ OPTIMIZED'
        ELSE '? CHECK MANUALLY'
    END as optimization_status,
    qual as policy_definition
FROM pg_policies 
WHERE schemaname = 'public'
  AND tablename IN ('configurations', 'decisions', 'market_data', 'paper_accounts', 'paper_trades', 'paper_orders', 'user_profiles', 'user_llm_credentials', 'bot_telegram_channels', 'logs')
ORDER BY tablename, policyname;