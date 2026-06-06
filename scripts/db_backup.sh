#!/usr/bin/env bash
# Nightly encrypted backup of the local ggbot Postgres.
# Cron: 30 4 * * * /home/sev/ggbot/scripts/db_backup.sh   (04:30 UTC — clear of the
# 03:00 snapshot-retention job and 00:00 Stripe meter job)
#
# - pg_dump -Fc (compressed custom format), integrity-verified with pg_restore -l
# - gpg-symmetric encrypted with /home/sev/.ggbot_backup_key (SEPARATE from .env so a
#   single-file leak never yields both dumps and the keys that decrypt their contents)
# - retention: 7 daily + Sunday dumps kept 28 days
# - weekly R2 offsite: Sundays, if an rclone remote named 'r2' is configured
# - any failure emits a loguru-format ERROR line into logs/ggbot.log, which the
#   error-alerts service forwards to Telegram
set -uo pipefail

BACKUP_DIR=/home/sev/backups/ggbot-db
KEYFILE=/home/sev/.ggbot_backup_key
APP_LOG=/home/sev/ggbot/logs/ggbot.log
ENVFILE=/home/sev/ggbot/.env
STAMP=$(date -u +%Y%m%d)
DOW=$(date -u +%u)   # 7 = Sunday
OUT="$BACKUP_DIR/ggbot-$STAMP.dump"

alert() {
    # loguru-compatible ERROR line -> picked up by error-alerts -> Telegram
    echo "$(date -u '+%Y-%m-%d %H:%M:%S') | ERROR    | scripts.db_backup:run:1 - $1" >> "$APP_LOG"
}

mkdir -p "$BACKUP_DIR" && chmod 700 "$BACKUP_DIR"

# DB DSN from .env (DATABASE_URL)
DSN=$(grep -E '^DATABASE_URL=' "$ENVFILE" | head -1 | cut -d= -f2-)
[ -n "$DSN" ] || { alert "DB backup failed: DATABASE_URL not found in .env"; exit 1; }

# backup key must exist (created at provision time; 0600)
[ -r "$KEYFILE" ] || { alert "DB backup failed: $KEYFILE missing/unreadable"; exit 1; }

# 1. dump (nice/ionice to stay off the hot path)
if ! nice -n 19 ionice -c3 pg_dump -Fc --no-sync -d "$DSN" -f "$OUT" 2>/tmp/db_backup_err.txt; then
    alert "DB backup failed: pg_dump error: $(head -c 200 /tmp/db_backup_err.txt)"
    rm -f "$OUT"; exit 1
fi

# 2. integrity check — a dump that exits 0 is not proven restorable until its TOC parses
if ! pg_restore -l "$OUT" >/dev/null 2>/tmp/db_backup_err.txt; then
    alert "DB backup failed: pg_restore -l integrity check failed: $(head -c 200 /tmp/db_backup_err.txt)"
    rm -f "$OUT"; exit 1
fi

# 3. encrypt + remove plaintext
if ! gpg --batch --yes --symmetric --cipher-algo AES256 \
        --passphrase-file "$KEYFILE" -o "$OUT.gpg" "$OUT" 2>/tmp/db_backup_err.txt; then
    alert "DB backup failed: gpg encryption failed: $(head -c 200 /tmp/db_backup_err.txt)"
    rm -f "$OUT" "$OUT.gpg"; exit 1
fi
rm -f "$OUT"
chmod 600 "$OUT.gpg"

# 4. retention: daily kept 7 days; Sunday dumps kept 28 days
find "$BACKUP_DIR" -name 'ggbot-*.dump.gpg' -mtime +28 -delete
find "$BACKUP_DIR" -name 'ggbot-*.dump.gpg' -mtime +7 ! -newermt "$(date -u -d 'last sunday' +%Y-%m-%d)" -print | while read -r f; do
    # keep if it was made on a Sunday, else delete
    fdate=$(basename "$f" | sed -E 's/ggbot-([0-9]{8}).*/\1/')
    if [ "$(date -u -d "$fdate" +%u)" != "7" ]; then rm -f "$f"; fi
done

# 5. weekly offsite to Cloudflare R2 (Sundays; requires `rclone config` remote named 'r2')
if [ "$DOW" = "7" ]; then
    if command -v rclone >/dev/null 2>&1 && rclone listremotes 2>/dev/null | grep -q '^r2:'; then
        if ! nice -n 19 rclone copy "$OUT.gpg" r2:ggbot-db-backups/ 2>/tmp/db_backup_err.txt; then
            alert "DB backup: R2 offsite sync FAILED: $(head -c 200 /tmp/db_backup_err.txt)"
        fi
    else
        alert "DB backup: R2 offsite NOT CONFIGURED (rclone remote 'r2' missing) — backups are single-box"
    fi
fi

echo "$(date -u '+%Y-%m-%d %H:%M:%S') | INFO     | scripts.db_backup:run:1 - DB backup OK: $(basename "$OUT.gpg") ($(du -h "$OUT.gpg" | cut -f1))" >> "$APP_LOG"
exit 0
