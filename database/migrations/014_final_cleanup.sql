-- Migration 014: Final cleanup of multiple policies and duplicate indexes
-- Removes overlapping policies on data_sources and data_points, fixes duplicate indexes
-- Date: 2025-01-04

BEGIN;

-- =====================================================
-- STEP 1: Fix multiple permissive policies on reference tables
-- =====================================================

-- Drop overlapping policies on data_sources
DROP POLICY IF EXISTS "Read enabled data sources" ON data_sources;
DROP POLICY IF EXISTS "Service role manages data sources" ON data_sources;

-- Drop overlapping policies on data_points  
DROP POLICY IF EXISTS "Read enabled data points" ON data_points;
DROP POLICY IF EXISTS "Service role manages data points" ON data_points;

-- Create single consolidated policies for reference tables
-- These are reference tables - everyone can read enabled items, only service role can manage

-- Data sources - single policy for read access
CREATE POLICY "reference_data_sources_read" ON data_sources
    FOR SELECT USING (enabled = true);

-- Data sources - service role can do everything
CREATE POLICY "service_manages_data_sources" ON data_sources
    FOR ALL USING (auth.role() = 'service_role');

-- Data points - single policy for read access  
CREATE POLICY "reference_data_points_read" ON data_points
    FOR SELECT USING (enabled = true);

-- Data points - service role can do everything
CREATE POLICY "service_manages_data_points" ON data_points
    FOR ALL USING (auth.role() = 'service_role');

-- =====================================================
-- STEP 2: Fix duplicate indexes
-- =====================================================

-- Drop duplicate index on configurations (keep the more specific one)
DROP INDEX IF EXISTS idx_configurations_user;
-- Keep idx_configurations_user_id

-- =====================================================
-- STEP 3: Verify clean state
-- =====================================================

COMMIT;

-- Check for any remaining multiple policies
SELECT 
    tablename,
    cmd,
    COUNT(*) as policy_count,
    array_agg(policyname) as policies
FROM pg_policies 
WHERE schemaname = 'public' 
  AND cmd = 'SELECT'
GROUP BY tablename, cmd, roles
HAVING COUNT(*) > 1
ORDER BY tablename;

-- Check final optimization status
SELECT 
    tablename,
    policyname,
    cmd,
    CASE 
        WHEN qual ~ 'auth\.uid\(\)' AND qual !~ 'SELECT auth\.uid\(\)' THEN '❌ NOT OPTIMIZED'
        WHEN qual ~ 'SELECT auth\.uid\(\)' THEN '✅ OPTIMIZED'  
        WHEN qual ~ 'auth\.role\(\)' THEN '✅ ROLE OK'
        WHEN qual = 'enabled' THEN '✅ SIMPLE'
        ELSE '✅ OK'
    END as status
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;