-- Migration 010: Optimize RLS performance issues
-- Fixes auth.uid() initplan issues, removes duplicate policies, and cleans up indexes
-- Date: 2025-01-04

BEGIN;

-- =====================================================
-- STEP 1: Drop all existing RLS policies for recreation
-- =====================================================

-- User-specific tables
DROP POLICY IF EXISTS "Users can only access their own configurations" ON configurations;
DROP POLICY IF EXISTS "Users can only access their own decisions" ON decisions;  
DROP POLICY IF EXISTS "Users can only access their own market data" ON market_data;
DROP POLICY IF EXISTS "Users can only access their own paper accounts" ON paper_accounts;
DROP POLICY IF EXISTS "Users can only access their own paper trades" ON paper_trades;
DROP POLICY IF EXISTS "Users can only access their own paper orders" ON paper_orders;
DROP POLICY IF EXISTS "Users can only access their own logs" ON logs;
DROP POLICY IF EXISTS "Users can only access their own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can only access their own LLM credentials" ON user_llm_credentials;
DROP POLICY IF EXISTS "Users can only access their own bot channels" ON bot_telegram_channels;

-- Reference tables (multiple policies issue)
DROP POLICY IF EXISTS "Authenticated users can read enabled data sources" ON data_sources;
DROP POLICY IF EXISTS "Service role full access data sources" ON data_sources;
DROP POLICY IF EXISTS "Authenticated users can read enabled data points" ON data_points;
DROP POLICY IF EXISTS "Service role full access data points" ON data_points;

-- Logs table (multiple policies issue)
DROP POLICY IF EXISTS "System logs are accessible to authenticated users" ON logs;

-- =====================================================
-- STEP 2: Recreate optimized RLS policies with (select auth.uid())
-- =====================================================

-- User-specific table policies (optimized with select)
CREATE POLICY "Users can only access their own configurations" ON configurations
    FOR ALL USING (user_id = (select auth.uid()));

CREATE POLICY "Users can only access their own decisions" ON decisions
    FOR ALL USING (user_id = (select auth.uid()));

CREATE POLICY "Users can only access their own market data" ON market_data
    FOR ALL USING (user_id = (select auth.uid()));

CREATE POLICY "Users can only access their own paper accounts" ON paper_accounts
    FOR ALL USING (user_id = (select auth.uid()));

CREATE POLICY "Users can only access their own paper trades" ON paper_trades
    FOR ALL USING (user_id = (select auth.uid()));

CREATE POLICY "Users can only access their own paper orders" ON paper_orders
    FOR ALL USING (user_id = (select auth.uid()));

CREATE POLICY "Users can only access their own profile" ON user_profiles
    FOR ALL USING (user_id = (select auth.uid()));

CREATE POLICY "Users can only access their own LLM credentials" ON user_llm_credentials
    FOR ALL USING (user_id = (select auth.uid()));

-- Bot channels policy (through config relationship)
CREATE POLICY "Users can only access their own bot channels" ON bot_telegram_channels
    FOR ALL USING (
        config_id IN (
            SELECT config_id FROM configurations 
            WHERE user_id = (select auth.uid())
        )
    );

-- Logs policy - simplified to single policy (users see their own logs OR system logs with null user_id)
CREATE POLICY "Users can access their own logs and system logs" ON logs
    FOR SELECT USING (
        user_id = (select auth.uid()) OR 
        user_id IS NULL
    );

-- =====================================================
-- STEP 3: Reference tables - single optimized policies
-- =====================================================

-- Data sources - single policy combining authenticated and service role access
CREATE POLICY "Read enabled data sources" ON data_sources
    FOR SELECT USING (
        enabled = true AND (
            (select auth.role()) = 'authenticated' OR 
            (select auth.role()) = 'service_role'
        )
    );

-- Data points - single policy combining authenticated and service role access  
CREATE POLICY "Read enabled data points" ON data_points
    FOR SELECT USING (
        enabled = true AND (
            (select auth.role()) = 'authenticated' OR 
            (select auth.role()) = 'service_role'
        )
    );

-- Service role policies for management operations
CREATE POLICY "Service role manages data sources" ON data_sources
    FOR ALL USING ((select auth.role()) = 'service_role');

CREATE POLICY "Service role manages data points" ON data_points
    FOR ALL USING ((select auth.role()) = 'service_role');

-- =====================================================
-- STEP 4: Fix duplicate indexes
-- =====================================================

-- Drop duplicate index on paper_accounts (keep the unique constraint one)
DROP INDEX IF EXISTS idx_paper_accounts_config;
-- Keep paper_accounts_config_id_key (unique constraint index)

-- =====================================================
-- STEP 5: Add missing optimized indexes for common queries
-- =====================================================

-- Optimize common user-based queries
CREATE INDEX IF NOT EXISTS idx_configurations_user_id ON configurations(user_id);
CREATE INDEX IF NOT EXISTS idx_decisions_user_id_created ON decisions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_market_data_user_symbol_timeframe ON market_data(user_id, symbol, timeframe, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_paper_trades_user_status ON paper_trades(user_id, status, opened_at DESC);

COMMIT;

-- =====================================================
-- Verification queries
-- =====================================================

-- Check RLS policies are optimized
SELECT 
    schemaname,
    tablename,
    policyname,
    CASE 
        WHEN qual LIKE '%auth.uid()%' THEN '❌ NEEDS OPTIMIZATION'
        WHEN qual LIKE '%(select auth.uid())%' THEN '✅ OPTIMIZED'
        ELSE '? UNKNOWN'
    END as optimization_status
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- Check for multiple policies per table/role/action
SELECT 
    tablename,
    COUNT(*) as policy_count,
    CASE WHEN COUNT(*) > 1 THEN '⚠️ MULTIPLE POLICIES' ELSE '✅ SINGLE POLICY' END as status
FROM pg_policies 
WHERE schemaname = 'public' 
  AND cmd = 'SELECT'
GROUP BY tablename, roles
HAVING COUNT(*) > 1
ORDER BY tablename;