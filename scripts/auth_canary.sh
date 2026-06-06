#!/usr/bin/env bash
# Supabase auth canary — keeps the free-tier project active (7-day inactivity pause guard)
# and detects two failure modes that would silently break logins:
#   1. project paused / restricted (non-200, restriction message)
#   2. JWT signing-key migration to asymmetric keys (JWKS keys array becomes non-empty —
#      backend verifies HS256 with SUPABASE_JWT_SECRET and would 401 every user)
# Cron: 0 8 * * 1,4  (Mon+Thu 08:00 UTC — twice weekly stays well inside the 7-day pause window)
# Alerts via loguru-format ERROR line -> logs/ggbot.log -> error-alerts -> Telegram.
set -u
APP_LOG=/home/sev/ggbot/logs/ggbot.log
URL="https://ciinauxtnkweyebyhucl.supabase.co/auth/v1/.well-known/jwks.json"

alert() {
    echo "$(date -u '+%Y-%m-%d %H:%M:%S') | ERROR    | scripts.auth_canary:run:1 - $1" >> "$APP_LOG"
}

BODY=$(curl -s --max-time 15 "$URL")
CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$URL")

if [ "$CODE" != "200" ]; then
    alert "Supabase auth canary FAILED: HTTP $CODE from JWKS endpoint — logins may be broken (paused/restricted?). Body: $(echo "$BODY" | head -c 150)"
    exit 0
fi
if echo "$BODY" | grep -q "exceed_db_size_quota\|restricted"; then
    alert "Supabase auth canary: project RESTRICTED — $(echo "$BODY" | head -c 150)"
    exit 0
fi
# keys array non-empty => project migrated to asymmetric JWT signing => HS256 verify breaks
if echo "$BODY" | grep -qE '"keys"\s*:\s*\[\s*\{'; then
    alert "Supabase auth canary: JWKS now serves ASYMMETRIC signing keys — backend HS256 verification (SUPABASE_JWT_SECRET) will reject logins. Make verify_jwt_token JWKS-aware NOW."
    exit 0
fi
exit 0
