-- Migration 012: Clean fix for RLS optimization
-- First check what exists, then fix properly
-- Date: 2025-01-04

BEGIN;

-- =====================================================
-- STEP 1: Find and drop all existing policies
-- =====================================================

-- Drop all policies that might exist (using CASCADE to be thorough)
DO $$ 
BEGIN
    -- Loop through and drop all existing policies for these tables
    FOR r IN (
        SELECT policyname, tablename 
        FROM pg_policies 
        WHERE schemaname = 'public'
        AND tablename IN ('configurations', 'decisions', 'market_data', 'paper_accounts', 'paper_trades', 'paper_orders', 'user_profiles', 'user_llm_credentials', 'bot_telegram_channels', 'logs')
    ) LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I', r.policyname, r.tablename);
    END LOOP;
END $$;

-- =====================================================
-- STEP 2: Create optimized policies with proper syntax
-- =====================================================

-- User-specific table policies with optimized auth.uid()
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
CREATE POLICY "User and system logs access" ON logs
    FOR SELECT USING (
        user_id = (SELECT auth.uid()) OR 
        user_id IS NULL
    );

-- Allow users to insert their own logs
CREATE POLICY "Users can insert their own logs" ON logs
    FOR INSERT WITH CHECK (user_id = (SELECT auth.uid()));

COMMIT;

-- =====================================================
-- Verification
-- =====================================================

-- Check the final state of policies
SELECT 
    tablename,
    policyname,
    cmd as operation,
    CASE 
        WHEN qual ~ 'auth\.uid\(\)' AND qual !~ '\(SELECT auth\.uid\(\)\)' THEN '❌ NOT OPTIMIZED'
        WHEN qual ~ '\(SELECT auth\.uid\(\)\)' THEN '✅ OPTIMIZED'
        ELSE '✅ OK'
    END as optimization_status
FROM pg_policies 
WHERE schemaname = 'public'
  AND tablename IN ('configurations', 'decisions', 'market_data', 'paper_accounts', 'paper_trades', 'paper_orders', 'user_profiles', 'user_llm_credentials', 'bot_telegram_channels', 'logs')
ORDER BY tablename, policyname;