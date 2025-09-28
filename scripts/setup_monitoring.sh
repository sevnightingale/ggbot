#!/bin/bash

# Setup cron job for disk space monitoring

SCRIPT_PATH="/home/sev/ggbot/scripts/disk_monitor.sh"
CRON_ENTRY="0 */6 * * * $SCRIPT_PATH > /dev/null 2>&1"

echo "Setting up disk space monitoring cron job..."
echo "This will run the monitor every 6 hours"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH"; then
    echo "Monitoring cron job already exists"
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "✅ Added cron job: Monitor disk space every 6 hours"
fi

echo "Current crontab:"
crontab -l

echo ""
echo "You can also run the monitor manually with:"
echo "$SCRIPT_PATH"