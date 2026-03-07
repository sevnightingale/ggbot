# CVE-2025-66478 Secret Rotation Checklist

## Overview

**Vulnerability**: CVE-2025-66478 (React Server Components RCE)
**CVSS Score**: 10.0 (Critical)
**Exposure Window**: Dec 4, 2025 1:00 PM PT → Dec 5, 2025 ~12:00 AM PT (~11 hours)
**Status**: Application patched (Next.js 15.5.7), secrets need rotation

## Why Rotation is Required

The vulnerability allowed remote code execution, meaning an attacker could potentially have:
- Accessed environment variables in memory
- Read .env files from the filesystem
- Intercepted API calls and credentials
- Executed arbitrary code with application permissions

**Per the security advisory**: "If your application was online and unpatched as of December 4th, 2025 at 1:00 PM PT, we strongly encourage you to rotate any secrets it uses, starting with your most critical ones."

---

## Rotation Priority

### 🔴 **CRITICAL - Rotate Immediately** (Day 1)

1. **Supabase Credentials**
   - [ ] Supabase Service Role Key (full database access)
     - Location: Backend `.env` → `SUPABASE_SERVICE_ROLE_KEY`
     - Action: Generate new service role key in Supabase dashboard → Settings → API
     - Impact: Requires backend restart
   - [ ] Supabase Anon Key (public client key)
     - Location: Frontend `.env.local` → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
     - Action: Generate new anon key in Supabase dashboard
     - Impact: Requires frontend rebuild + redeploy
   - [ ] Database Password (if using direct PostgreSQL)
     - Location: Backend `.env` → `DATABASE_URL` connection string
     - Action: Reset password in Supabase → Database → Settings
     - Impact: Update all services using direct DB connections

2. **Authentication Secrets**
   - [ ] NextAuth Secret
     - Location: Frontend `.env.local` → `NEXTAUTH_SECRET`
     - Action: Generate new secret: `openssl rand -base64 32`
     - Impact: All users logged out, must re-authenticate
   - [ ] JWT Signing Keys
     - Location: Backend `.env` → `JWT_SECRET` (if separate from Supabase)
     - Action: Generate new key, update signing logic
     - Impact: All existing tokens invalidated

3. **Trading Platform Credentials**
   - [ ] Symphony API Credentials
     - Location: Backend `.env` → `SYMPHONY_API_KEY`, `SYMPHONY_PRIVATE_KEY`
     - Action: Regenerate in Symphony dashboard
     - Impact: Live trading halted until updated
   - [ ] AsterDEX API Credentials
     - Location: Backend `.env` → `ASTER_API_KEY`, `ASTER_SECRET_KEY`
     - Action: Regenerate in AsterDEX account settings
     - Impact: Live trading halted until updated

---

### 🟡 **HIGH PRIORITY** (Day 1-2)

4. **AI/LLM API Keys**
   - [ ] Anthropic API Key (Claude)
     - Location: Backend `.env` → `ANTHROPIC_API_KEY`
     - Action: Create new API key in Anthropic Console → API Keys
     - Note: Delete old key after rotation
     - Impact: All agent/decision services restart required
   - [ ] Grok API Key (X.AI)
     - Location: Backend `.env` → `GROK_API_KEY`
     - Action: Regenerate in X.AI/Grok dashboard
     - Impact: Market intelligence data extraction may pause

5. **Market Data Providers**
   - [ ] Alpaca API Credentials (if used)
     - Location: Backend `.env` → `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`
     - Action: Regenerate in Alpaca dashboard → Account → API Keys
     - Impact: Market data feed interruption
   - [ ] Other Market Data Keys
     - Location: Check `.env` for any `*_API_KEY` related to market data
     - Action: Rotate through respective provider dashboards

6. **Email Service**
   - [ ] Resend API Key
     - Location: Backend `.env` → `RESEND_API_KEY`
     - Action: Create new API key in Resend dashboard → API Keys
     - Impact: Email notifications temporarily unavailable

---

### 🟢 **MEDIUM PRIORITY** (Week 1)

7. **Admin Access**
   - [ ] Admin User ID (if considered sensitive)
     - Location: `.env` → `ADMIN_USER_ID`, `NEXT_PUBLIC_ADMIN_USER_ID`
     - Action: Consider creating new admin account, transfer ownership
     - Impact: Admin dashboard access changes

8. **Session Store**
   - [ ] Redis Password (if authentication enabled)
     - Location: Backend `.env` → `REDIS_PASSWORD` or connection URL
     - Action: Update Redis configuration with new password
     - Impact: All cached sessions cleared

9. **Third-Party Integrations**
   - [ ] Any OAuth Client Secrets
     - Location: Check `.env` for `*_CLIENT_SECRET`
     - Action: Regenerate in respective OAuth provider dashboards
   - [ ] Webhook Secrets
     - Location: Check `.env` for `*_WEBHOOK_SECRET`
     - Action: Update webhook configurations with new secrets

---

## Rotation Procedure

### Step 1: Inventory
```bash
# List all environment variables (NEVER commit this output)
cd /home/sev/ggbot
grep -E "KEY|SECRET|PASSWORD|TOKEN" .env 2>/dev/null | cut -d'=' -f1
cd frontend
grep -E "KEY|SECRET|PASSWORD|TOKEN" .env.local 2>/dev/null | cut -d'=' -f1
```

### Step 2: Generate New Secrets
Use secure random generation:
```bash
# For general secrets (32 bytes)
openssl rand -base64 32

# For hex secrets (64 characters)
openssl rand -hex 32

# For UUID-style secrets
uuidgen
```

### Step 3: Update Credentials

**Backend (.env)**:
1. Create backup: `cp .env .env.backup.$(date +%Y%m%d)`
2. Update secrets in `.env` file
3. Restart services: `pm2 restart ggbot`

**Frontend (.env.local)**:
1. Update secrets in `.env.local`
2. Rebuild: `npm run build`
3. Deploy to Vercel (push to git)

### Step 4: Verify Services
```bash
# Check backend health
curl http://localhost:8001/health

# Check PM2 services
pm2 status

# Check logs for auth errors
pm2 logs ggbot --lines 50 | grep -i "auth\|error"
```

### Step 5: Monitor
- Watch for authentication failures
- Monitor trading execution (verify API credentials work)
- Check email delivery (test Resend)
- Verify AI agent responses (test Anthropic/Grok keys)

---

## Provider-Specific Instructions

### Supabase
1. Login to https://supabase.com/dashboard
2. Select `ggbots` project
3. Navigate to **Settings** → **API**
4. Click **Reset** next to service_role and anon keys
5. Copy new keys immediately (shown only once)
6. Update `.env` and `.env.local`

### Anthropic
1. Login to https://console.anthropic.com
2. Navigate to **API Keys**
3. Click **Create Key**
4. Name it: `ggbots-prod-$(date +%Y%m%d)`
5. Copy key immediately
6. Delete old key after verifying new one works

### Symphony
1. Contact Symphony support or check dashboard
2. Request API key rotation
3. Verify wallet address remains associated
4. Test with small trade before full deployment

### AsterDEX
1. Login to AsterDEX dashboard
2. Navigate to API settings
3. Revoke old API key
4. Generate new key pair
5. Update competition registration if needed

### Resend
1. Login to https://resend.com/dashboard
2. Navigate to **API Keys**
3. Create new key: `ggbots-prod-$(date +%Y%m%d)`
4. Copy key immediately
5. Delete old key after verification

---

## Verification Tests

After rotation, run these checks:

```bash
# Backend API test
curl -H "Authorization: Bearer <USER_JWT>" http://localhost:8001/api/v2/me

# Database connectivity
python -c "from core.common.db import get_db_connection; print('DB OK')"

# AI service test (in Python REPL)
from anthropic import Anthropic
client = Anthropic()
print(client.messages.create(model="claude-3-5-haiku-20241022", max_tokens=10, messages=[{"role":"user","content":"hi"}]))

# Trading API test (paper mode)
# Execute one test trade through frontend
```

---

## Timeline

- **Day 0 (Today)**: Create checklist ✓
- **Day 1**: Rotate CRITICAL secrets (Supabase, Auth, Trading)
- **Day 2**: Rotate HIGH PRIORITY secrets (AI APIs, Market Data, Email)
- **Week 1**: Rotate MEDIUM PRIORITY secrets (Admin, Redis, OAuth)
- **Week 2**: Full security audit, verify no issues

---

## Notes

- **DO NOT** commit actual secret values to git
- **DO NOT** share secrets in Slack/Discord
- **DO** use password manager for secure storage
- **DO** verify each service works before moving to next
- **DO** keep this checklist updated as you complete items

---

## Post-Rotation

Once complete:
- [ ] Document rotation dates in internal security log
- [ ] Update team on any breaking changes (user logout, etc.)
- [ ] Schedule next security review (3 months)
- [ ] Archive old credentials securely (encrypted backup)
- [ ] Update monitoring/alerting with new credential fingerprints

---

**Last Updated**: 2025-12-12
**Status**: Ready for execution
**Owner**: System Administrator
