# SQL Migration Commands - RLS Security Fix

**Date**: 2025-11-13
**Purpose**: Fix RLS security issues + add public bot performance features

Run these commands in Supabase SQL Editor.

---

## Step 1: Add Public Performance Flag to Configurations

```sql
-- Add is_public_performance column (default private)
ALTER TABLE configurations
ADD COLUMN IF NOT EXISTS is_public_performance BOOLEAN DEFAULT FALSE;

-- Add index for filtering public bots
CREATE INDEX IF NOT EXISTS idx_configurations_public
ON configurations(is_public_performance)
WHERE is_public_performance = TRUE;

-- Add comment
COMMENT ON COLUMN configurations.is_public_performance IS
'When true, bot performance data (activities, trades, metrics) is publicly viewable without auth';
```

---

## Step 2: Fix Activities Table RLS

**Issue**: Policy exists but RLS is disabled. Anyone can query any bot's activities.

```sql
-- Enable Row Level Security on activities table
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;

-- Drop existing policy if it exists (clean slate)
DROP POLICY IF EXISTS activities_user_isolation ON activities;

-- Policy 1: Users can see their own activities
CREATE POLICY activities_user_access ON activities
FOR SELECT
USING (user_id = auth.uid());

-- Policy 2: Public can see activities for public bots (no auth required)
CREATE POLICY activities_public_access ON activities
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM configurations c
    WHERE c.config_id = activities.config_id
    AND c.is_public_performance = TRUE
  )
);

-- Service role (backend) bypasses RLS automatically - no policy needed
-- Backend writes use service_role key, which has BYPASSRLS privilege
```

---

## Step 3: Fix Agent Sessions Table RLS

**Issue**: No RLS at all. Potential exposure of Claude SDK session IDs.

```sql
-- Enable Row Level Security on agent_sessions table
ALTER TABLE agent_sessions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own agent sessions
CREATE POLICY agent_sessions_user_isolation ON agent_sessions
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM configurations c
    WHERE c.config_id = agent_sessions.config_id
    AND c.user_id = auth.uid()
  )
);

-- Backend writes bypass RLS (service_role key has BYPASSRLS)
```

---

## Step 4: LLM Models Table - Public Read-Only

**Issue**: No RLS. Reference data that should be publicly readable.

```sql
-- Enable Row Level Security on llm_models table
ALTER TABLE llm_models ENABLE ROW LEVEL SECURITY;

-- Policy: Allow public read access (all users can read model pricing/specs)
CREATE POLICY llm_models_public_read ON llm_models
FOR SELECT
USING (true);

-- No write policies - only backend (service_role) can write
```

---

## Step 5: Verify Policies Are Active

```sql
-- Check RLS status for all 3 tables
SELECT
  schemaname,
  tablename,
  rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('activities', 'agent_sessions', 'llm_models')
ORDER BY tablename;

-- Should show TRUE for all 3 tables
```

---

## Step 6: Check Existing Policies

```sql
-- View all policies on these tables
SELECT
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual,
  with_check
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('activities', 'agent_sessions', 'llm_models')
ORDER BY tablename, policyname;
```

---

## Expected Results After Migration

### Activities Table:
-  RLS enabled
-  Policy: `activities_user_access` - Users see own activities
-  Policy: `activities_public_access` - Public sees activities for public bots
-  Backend writes still work (service role bypasses RLS)

### Agent Sessions Table:
-  RLS enabled
-  Policy: `agent_sessions_user_isolation` - Users see only their sessions
-  Backend reads/writes still work (service role bypasses RLS)

### LLM Models Table:
-  RLS enabled
-  Policy: `llm_models_public_read` - All users can read
-  Backend writes still work (service role bypasses RLS)

---

## Testing Queries

### Test 1: Verify you can see your own activities
```sql
-- Run this as authenticated user in Supabase dashboard
-- Should return your activities
SELECT COUNT(*) FROM activities WHERE user_id = auth.uid();
```

### Test 2: Verify public bot activities are visible
```sql
-- First, mark a test bot as public
UPDATE configurations
SET is_public_performance = TRUE
WHERE config_id = 'YOUR_TEST_CONFIG_ID';

-- Then verify activities are visible without auth
-- (This would be tested via API endpoint, not SQL editor)
```

### Test 3: Verify isolation works
```sql
-- Try to query another user's private bot activities
-- Should return 0 rows (unless bot is public)
SELECT COUNT(*) FROM activities WHERE user_id != auth.uid();
```

---

## Rollback (if needed)

```sql
-- Disable RLS on all tables (back to current unsafe state)
ALTER TABLE activities DISABLE ROW LEVEL SECURITY;
ALTER TABLE agent_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE llm_models DISABLE ROW LEVEL SECURITY;

-- Drop policies
DROP POLICY IF EXISTS activities_user_access ON activities;
DROP POLICY IF EXISTS activities_public_access ON activities;
DROP POLICY IF EXISTS agent_sessions_user_isolation ON agent_sessions;
DROP POLICY IF EXISTS llm_models_public_read ON llm_models;

-- Remove public performance flag
ALTER TABLE configurations DROP COLUMN IF EXISTS is_public_performance;
```

---

## Notes

1. **Service Role Bypass**: All backend writes use `get_db_connection()` with service role key, which has `BYPASSRLS` privilege. Policies don't affect backend operations.

2. **Existing Policy**: The `activities_user_isolation` policy mentioned in Supabase warnings will be dropped and replaced with two separate policies (user access + public access).

3. **No Breaking Changes**: Existing functionality preserved:
   - Backend writes work identically
   - Users can still access their own data
   - Public viewing enabled for opted-in bots

4. **Frontend Changes Required**: After running SQL, you'll need to:
   - Add privacy toggle in bot settings UI
   - Create `/api/v2/arena` endpoint for public leaderboard
   - Update activities API to respect public access

5. **Backward Compatible**: All bots default to `is_public_performance = FALSE` (private). No bots become public without explicit opt-in.
