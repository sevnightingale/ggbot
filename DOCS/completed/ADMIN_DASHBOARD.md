# Admin Dashboard - Internal Platform Management

**Created**: 2025-12-04
**Status**: Planning
**Priority**: HIGH
**Linked TODO Section**: `## 🔧 **HIGH PRIORITY - Admin Dashboard** [ADMIN_DASHBOARD.md]`
**Admin User ID**: `00000000-0000-0000-0000-000000000000`

---

## Overview

### Problem Statement

Managing the ggbots platform currently requires:
- Running `scripts/status_check.py` for metrics
- Navigating Supabase UI (clunky, slow) to find users by email
- Manual SQL queries to view user configurations
- No visibility into billing/token usage health
- No ability to quickly start/stop user bots

### Solution

Internal admin dashboard at `/admin` restricted to admin user ID:
- Platform overview with real-time stats
- User management with email search
- Direct editing of user profiles, subscription tiers, configurations
- Bot control (start/stop any bot)
- Billing health monitoring (token usage, unreported amounts)

### Key Features

1. **Platform Overview**: Stats, PM2 services, log summary, billing health
2. **User Management**: Search by email, view/edit all user data
3. **Bot Control**: Start/stop bots, view per-bot token costs
4. **Billing Verification**: Track provider vs platform costs, unreported usage

---

## Architecture

### Route Structure

```
/admin/                     → Dashboard overview
/admin/users/               → User search + list
/admin/users/[user_id]/     → User detail + edit
```

### Security Model

**Frontend** (`frontend/app/admin/layout.tsx`):
```typescript
const adminUserId = process.env.NEXT_PUBLIC_ADMIN_USER_ID
if (session.user.id !== adminUserId) {
  redirect('/forge')
}
```

**Backend** (FastAPI dependency):
```python
async def require_admin(user_id: str = Depends(get_current_user_id)):
    admin_id = os.getenv("ADMIN_USER_ID")
    if user_id != admin_id:
        raise HTTPException(403, "Admin access required")
    return user_id
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/admin/stats` | GET | Platform stats (users, bots, trades, P&L) |
| `/api/v2/admin/services` | GET | PM2 status, VM resources, Redis info |
| `/api/v2/admin/logs/summary` | GET | Log counts by level (24h) |
| `/api/v2/admin/billing` | GET | Token usage, costs, unreported amounts |
| `/api/v2/admin/users` | GET | User list with search (?search=email) |
| `/api/v2/admin/users/{user_id}` | GET | Full user detail with related data |
| `/api/v2/admin/users/{user_id}` | PATCH | Update user_profile fields |
| `/api/v2/admin/users/{user_id}/configs` | GET | User's bot configurations |
| `/api/v2/admin/configs/{config_id}` | PATCH | Update configuration (state, config_data) |
| `/api/v2/admin/bots/{config_id}/start` | POST | Start bot |
| `/api/v2/admin/bots/{config_id}/stop` | POST | Stop bot |

---

## Implementation Details

### Phase 1: Backend API (`api/admin.py`)

**Estimated Time**: 3-4 hours

#### Admin Auth Dependency

```python
import os
from fastapi import Depends, HTTPException

ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")

async def require_admin(user_id: str = Depends(get_current_user_id)):
    if not ADMIN_USER_ID or user_id != ADMIN_USER_ID:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id
```

#### Stats Endpoint

Reuse queries from `scripts/status_check.py`:
- User count, subscription breakdown
- Bot count, active/inactive split
- Trading stats (trades, win rate, P&L)
- Open positions, exposure

#### Services Endpoint

```python
async def get_services():
    # PM2 status via subprocess
    pm2_result = subprocess.run(['pm2', 'jlist'], capture_output=True, text=True)
    services = json.loads(pm2_result.stdout)

    # VM resources
    disk = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
    memory = subprocess.run(['free', '-h'], capture_output=True, text=True)

    # Redis info
    redis_info = subprocess.run(['redis-cli', 'info', 'memory'], capture_output=True, text=True)

    return {
        "pm2_services": [...],
        "vm": {"disk": ..., "memory": ..., "cpu_load": ...},
        "redis": {"status": "connected", "memory": "16.43M"}
    }
```

#### User Search

```sql
-- Search users by email (requires auth.users join)
SELECT
    up.*,
    au.email,
    au.created_at as auth_created_at,
    au.last_sign_in_at,
    (SELECT COUNT(*) FROM configurations WHERE user_id = up.user_id) as bot_count,
    (SELECT COALESCE(SUM(total_trades), 0) FROM paper_accounts pa
     JOIN configurations c ON c.config_id = pa.config_id
     WHERE c.user_id = up.user_id) as total_trades
FROM user_profiles up
JOIN auth.users au ON au.id = up.user_id
WHERE au.email ILIKE $1
ORDER BY au.last_sign_in_at DESC NULLS LAST
LIMIT 50
```

#### Billing Summary

```sql
SELECT
    COUNT(*) as total_activities,
    COUNT(*) FILTER (WHERE provider_cost_usd IS NOT NULL) as llm_activities,
    COALESCE(SUM(provider_cost_usd), 0) as total_provider_cost,
    COALESCE(SUM(platform_cost_usd), 0) as total_platform_cost,
    COUNT(*) FILTER (WHERE stripe_reported = false AND platform_cost_usd IS NOT NULL) as unreported_count,
    COALESCE(SUM(platform_cost_usd) FILTER (WHERE stripe_reported = false), 0) as unreported_amount,
    MAX(stripe_reported_at) as last_report_time
FROM activities
WHERE created_at > NOW() - INTERVAL '30 days'
```

#### Per-Bot Token Usage

```sql
SELECT
    c.config_id,
    c.config_name,
    c.state,
    c.trading_mode,
    c.config_type,
    COALESCE(SUM(a.input_tokens), 0) as total_input_tokens,
    COALESCE(SUM(a.output_tokens), 0) as total_output_tokens,
    COALESCE(SUM(a.reasoning_tokens), 0) as total_reasoning_tokens,
    COALESCE(SUM(a.provider_cost_usd), 0) as provider_cost,
    COALESCE(SUM(a.platform_cost_usd), 0) as platform_cost,
    COUNT(a.activity_id) as activity_count
FROM configurations c
LEFT JOIN activities a ON a.config_id = c.config_id
    AND a.provider_cost_usd IS NOT NULL
WHERE c.user_id = $1
GROUP BY c.config_id
ORDER BY platform_cost DESC
```

### Phase 2: Frontend Dashboard (`/admin`)

**Estimated Time**: 2 hours

#### Layout (`frontend/app/admin/layout.tsx`)

```typescript
export default async function AdminLayout({ children }) {
  const supabase = createServerClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session) redirect('/login')

  const adminUserId = process.env.NEXT_PUBLIC_ADMIN_USER_ID
  if (session.user.id !== adminUserId) {
    redirect('/forge')
  }

  return <div className="min-h-screen bg-charcoal-900">{children}</div>
}
```

#### Dashboard Page Structure

```
┌────────────────────────────────────────────────────────────┐
│ ADMIN DASHBOARD                                [Refresh]   │
├────────────────────────────────────────────────────────────┤
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────────┐ │
│ │ 259       │ │ 1         │ │ $-16,178  │ │ 🟢 Healthy  │ │
│ │ Users     │ │ Active    │ │ Total P&L │ │ 6 services  │ │
│ └───────────┘ └───────────┘ └───────────┘ └─────────────┘ │
├────────────────────────────────────────────────────────────┤
│ SERVICES                                                   │
│ ┌────────────┬────────┬─────────┬────────┬──────────────┐ │
│ │ Name       │ Status │ Memory  │ CPU    │ Restarts     │ │
│ ├────────────┼────────┼─────────┼────────┼──────────────┤ │
│ │ ggbot      │ 🟢     │ 251MB   │ 0.6%   │ 203          │ │
│ │ market-ws  │ 🟢     │ 174MB   │ 1.3%   │ 63           │ │
│ └────────────┴────────┴─────────┴────────┴──────────────┘ │
├────────────────────────────────────────────────────────────┤
│ BILLING HEALTH                                             │
│ Provider Cost (30d): $12.45                                │
│ Platform Revenue (30d): $21.17 (70% markup)                │
│ Unreported: $0.05 (3 activities)                           │
│ Last Report: 2025-12-04 00:00:00 UTC                       │
├────────────────────────────────────────────────────────────┤
│ LOGS (24h)                                                 │
│ INFO: 45,231 | WARN: 12 | ERROR: 3 | CRITICAL: 0           │
├────────────────────────────────────────────────────────────┤
│ [→ Manage Users]                                           │
└────────────────────────────────────────────────────────────┘
```

### Phase 3: User Management (`/admin/users`)

**Estimated Time**: 3-4 hours

#### User List Page

- Search input (email, debounced 500ms)
- Results table: Email, Tier, Bots, Trades, Last Active
- Click row → navigate to user detail

#### User Detail Page (`/admin/users/[user_id]`)

**Sections:**

1. **User Profile** (editable)
   - subscription_tier (dropdown: free, usage_based, ggbase)
   - subscription_status (dropdown: active, canceled, past_due)
   - paid_data_points (multi-select)
   - Stripe IDs (read-only)

2. **Configurations** (table + expand)
   - List all user's bots
   - Quick actions: Start/Stop
   - Expand → edit config_data JSON
   - Token usage per bot

3. **Paper Accounts** (read-only)
   - Balance, P&L, trades, win rate per account

4. **Recent Activity** (read-only)
   - Last 20 activities with type, cost, timestamp

---

## File Structure

```
Backend:
  api/admin.py                     # ~400-500 lines

Frontend:
  frontend/app/admin/
    layout.tsx                     # Admin auth check
    page.tsx                       # Dashboard overview (~200 lines)
    users/
      page.tsx                     # User search/list (~150 lines)
      [user_id]/
        page.tsx                   # User detail + edit (~400 lines)
```

---

## Environment Variables

```bash
# Backend (.env)
ADMIN_USER_ID=00000000-0000-0000-0000-000000000000

# Frontend (.env.local)
NEXT_PUBLIC_ADMIN_USER_ID=00000000-0000-0000-0000-000000000000
```

Note: This is the same as `DEFAULT_USER_ID` already used in the codebase.

---

## Database Considerations

### Accessing auth.users

Supabase `auth.users` table contains email but is in `auth` schema.

**Decision**: Use service role key for admin queries.

Security model:
```
Request → JWT Auth → user_id == ADMIN_USER_ID check → THEN use service role
```

Service role is never the first line of defense - admin user ID check happens FIRST.

### Config Data Editing - Form-Based Editor

**Decision**: Form-based editor (not raw JSON) for safer editing.

Based on `core/config/models.py` BotConfig structure:

```
BotConfig
├── schema_version: str (read-only)
├── selected_pair: dropdown (141 symbols)
├── extraction: ExtractionConfig
│   └── data_sources: DataSourcesConfig
│       ├── technical_indicators: multi-select chips
│       ├── fundamental_analysis: multi-select chips
│       ├── sentiment_and_trends: multi-select chips
│       └── ... (6 categories)
├── decision: DecisionConfig
│   ├── analysis_frequency: dropdown (5m/15m/30m/1h/4h/1d/1w)
│   ├── system_prompt: textarea
│   └── user_prompt: textarea
├── llm_config: LLMConfig
│   ├── provider: dropdown (openrouter/openai/anthropic/xai/deepseek)
│   ├── model: text input
│   └── use_platform_keys: checkbox
├── trading: TradingConfig
│   ├── leverage: number input (1-100)
│   ├── position_sizing: PositionSizingConfig
│   │   ├── method: dropdown (fixed_usd/account_percentage/confidence_based)
│   │   ├── fixed_amount_usd: number (10-10000)
│   │   ├── account_percent: number (0.1-50.0)
│   │   └── max_position_percent: number (1.0-25.0)
│   └── risk_management: RiskManagementConfig
│       ├── max_positions: number (1-20)
│       ├── default_stop_loss_percent: number (0.5-20.0)
│       ├── default_take_profit_percent: number (0.5-50.0)
│       └── max_daily_loss_usd: number (50-5000)
├── telegram_integration: TelegramIntegrationConfig (collapsible)
└── agent_strategy: AgentStrategy (for agent bots)
    ├── content: textarea
    ├── autonomously_editable: checkbox
    └── version: read-only
```

**Form UI Approach:**
- Collapsible sections for each major category
- Validation on blur (show errors inline)
- "Save Changes" button with confirmation modal
- Backend validates against Pydantic model before save
- Show Pydantic validation errors if save fails

---

## Implementation Phases

| Phase | Description | Time | Dependencies |
|-------|-------------|------|--------------|
| 1 | Backend API (`api/admin.py`) | 3-4h | None |
| 2 | Frontend Dashboard | 2h | Phase 1 |
| 3 | User List + Search | 1-2h | Phase 1 |
| 4 | User Detail + Edit | 2-3h | Phase 3 |
| 5 | Testing + Polish | 1-2h | All |

**Total Estimated Time**: 9-13 hours

---

## Confirmation Modals

**Decision**: Add confirmation modals for destructive/important actions.

| Action | Modal Text |
|--------|-----------|
| Change subscription tier | "Change {email} from {old_tier} to {new_tier}?" |
| Stop active bot | "Stop bot '{name}'? This will cancel any scheduled runs." |
| Edit config_data | "Save configuration changes to '{bot_name}'?" |
| Reset paper account | "Reset paper account to $10,000? This cannot be undone." |

**Implementation**: Simple React modal component with confirm/cancel buttons.

---

## Security Checklist

- [ ] Admin user ID check in frontend layout
- [ ] Admin user ID check in every backend endpoint
- [ ] No admin endpoints exposed without auth
- [ ] Service role only used AFTER admin check passes
- [ ] Audit log for admin actions (optional, future)
- [ ] Rate limiting on admin endpoints (optional)

---

## Future Enhancements

- **Audit logging**: Track who changed what, when
- **Multiple admins**: List of admin IDs instead of single
- **Impersonation**: View app as specific user (read-only)
- **Bulk actions**: Stop all bots, mass-update tiers
- **Alerts config**: Configure error alert thresholds
- **Export**: CSV export of users, trades, billing
