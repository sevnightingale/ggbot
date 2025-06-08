-- NUCLEAR RESET: Complete wipe of trading and account data
-- This will remove all trades, positions, and account states to start fresh

-- 1. Delete all trades (phantom and real)
DELETE FROM trades WHERE user_id = '00000000-0000-0000-0000-000000000001';

-- 2. Delete all account states (outdated monitoring data)
DELETE FROM account_states WHERE user_id = '00000000-0000-0000-0000-000000000001';

-- 3. Delete all market data (can be regenerated)
DELETE FROM market_data WHERE user_id = '00000000-0000-0000-0000-000000000001';

-- 4. Delete any position reconciliation data
DELETE FROM position_reconciliation WHERE user_id = '00000000-0000-0000-0000-000000000001';

-- 5. Reset auto-increment sequences if needed
-- (PostgreSQL doesn't auto-increment UUIDs but reset any counters)

-- 6. Verify clean state
SELECT 'trades' as table_name, COUNT(*) as remaining_records FROM trades WHERE user_id = '00000000-0000-0000-0000-000000000001'
UNION ALL
SELECT 'account_states', COUNT(*) FROM account_states WHERE user_id = '00000000-0000-0000-0000-000000000001'
UNION ALL  
SELECT 'market_data', COUNT(*) FROM market_data WHERE user_id = '00000000-0000-0000-0000-000000000001';

-- Expected result: All counts should be 0