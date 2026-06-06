#!/usr/bin/env bash
# Disk-usage alert -> loguru-format ERROR into logs/ggbot.log -> error-alerts -> Telegram.
# Cron: 15 */6 * * *  (every 6h). Threshold 85%.
set -u
THRESHOLD=85
USE=$(df --output=pcent / | tail -1 | tr -dc '0-9')
if [ "$USE" -ge "$THRESHOLD" ]; then
    echo "$(date -u '+%Y-%m-%d %H:%M:%S') | ERROR    | scripts.disk_alert:run:1 - Disk usage ${USE}% >= ${THRESHOLD}% on / — Postgres writes stop at 100%. Prune backups/logs or grow disk." >> /home/sev/ggbot/logs/ggbot.log
fi
exit 0
