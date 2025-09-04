-- Migration 009: Fix Supabase security warnings
-- Addresses security definer view and function search path issues
-- Date: 2025-01-04

BEGIN;

-- =====================================================
-- STEP 1: Fix function search path security issue
-- =====================================================

-- Drop and recreate update_updated_at_column function with secure search_path
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER 
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

-- Recreate triggers for automatic updated_at (they were dropped with CASCADE)
CREATE TRIGGER update_data_sources_updated_at 
    BEFORE UPDATE ON data_sources 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_points_updated_at 
    BEFORE UPDATE ON data_points 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- STEP 2: Fix paper_trading_summary security definer view
-- =====================================================

-- Drop the security definer view and recreate without SECURITY DEFINER
DROP VIEW IF EXISTS paper_trading_summary CASCADE;

-- Recreate as a regular view (users will access through RLS on underlying tables)
CREATE VIEW paper_trading_summary AS
SELECT 
    pt.user_id,
    pt.config_id,
    pt.account_id,
    DATE_TRUNC('day', pt.opened_at) as trading_date,
    COUNT(*) as total_trades,
    SUM(CASE WHEN pt.realized_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
    SUM(CASE WHEN pt.realized_pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
    COALESCE(SUM(pt.realized_pnl), 0) as total_realized_pnl,
    COALESCE(SUM(pt.unrealized_pnl), 0) as total_unrealized_pnl,
    COALESCE(SUM(pt.realized_pnl) + SUM(pt.unrealized_pnl), 0) as total_pnl,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            ROUND((SUM(CASE WHEN pt.realized_pnl > 0 THEN 1 ELSE 0 END)::numeric / COUNT(*)::numeric) * 100, 2)
        ELSE 0 
    END as win_rate_percent
FROM paper_trades pt
WHERE pt.opened_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY pt.user_id, pt.config_id, pt.account_id, DATE_TRUNC('day', pt.opened_at);

-- Enable RLS on the view (it will inherit from paper_trades table RLS)
ALTER VIEW paper_trading_summary SET (security_invoker = on);

-- =====================================================
-- STEP 3: Add RLS policy for paper_trading_summary view
-- =====================================================

-- The view inherits RLS from paper_trades, but let's ensure proper access
-- Users can only see their own trading summaries
-- (This is automatically enforced through the paper_trades table RLS policies)

COMMIT;

-- =====================================================
-- Verification
-- =====================================================

-- Verify function has correct search_path
SELECT 
    p.proname as function_name,
    p.proconfig as function_config
FROM pg_proc p 
WHERE p.proname = 'update_updated_at_column';

-- Verify view exists and is not security definer
SELECT 
    schemaname,
    viewname,
    definition
FROM pg_views 
WHERE viewname = 'paper_trading_summary';