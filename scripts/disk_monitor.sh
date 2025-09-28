#!/bin/bash

# Disk Space Monitoring Script for ggbot
# Checks for disk space issues and large log files

set -e

# Configuration
MAX_LOG_SIZE_MB=100
DISK_USAGE_THRESHOLD=80
LOG_FILE="/home/sev/ggbot/logs/disk_monitor.log"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to check disk usage
check_disk_usage() {
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')

    if [ "$usage" -gt "$DISK_USAGE_THRESHOLD" ]; then
        echo -e "${RED}WARNING: Disk usage at ${usage}%${NC}"
        log "WARNING: Disk usage at ${usage}%"
        return 1
    else
        echo -e "${GREEN}OK: Disk usage at ${usage}%${NC}"
        log "OK: Disk usage at ${usage}%"
        return 0
    fi
}

# Function to check PM2 log sizes
check_pm2_logs() {
    local warning_found=0

    echo "Checking PM2 log sizes..."
    for log_file in /home/sev/.pm2/logs/*.log; do
        if [ -f "$log_file" ]; then
            local size_mb=$(du -m "$log_file" | cut -f1)
            if [ "$size_mb" -gt "$MAX_LOG_SIZE_MB" ]; then
                echo -e "${YELLOW}WARNING: $log_file is ${size_mb}MB${NC}"
                log "WARNING: $log_file is ${size_mb}MB"
                warning_found=1
            fi
        fi
    done

    if [ "$warning_found" -eq 0 ]; then
        echo -e "${GREEN}OK: All PM2 logs under ${MAX_LOG_SIZE_MB}MB${NC}"
        log "OK: All PM2 logs under ${MAX_LOG_SIZE_MB}MB"
    fi

    return $warning_found
}

# Function to check application logs
check_app_logs() {
    local warning_found=0

    echo "Checking application log sizes..."
    for log_file in /home/sev/ggbot/logs/*.log; do
        if [ -f "$log_file" ]; then
            local size_mb=$(du -m "$log_file" | cut -f1)
            if [ "$size_mb" -gt "$MAX_LOG_SIZE_MB" ]; then
                echo -e "${YELLOW}WARNING: $log_file is ${size_mb}MB${NC}"
                log "WARNING: $log_file is ${size_mb}MB"
                warning_found=1
            fi
        fi
    done

    if [ "$warning_found" -eq 0 ]; then
        echo -e "${GREEN}OK: All app logs under ${MAX_LOG_SIZE_MB}MB${NC}"
        log "OK: All app logs under ${MAX_LOG_SIZE_MB}MB"
    fi

    return $warning_found
}

# Function to check Next.js cache
check_nextjs_cache() {
    local cache_dir="/home/sev/ggbot/frontend/.next/cache"

    if [ -d "$cache_dir" ]; then
        local size_mb=$(du -sm "$cache_dir" | cut -f1)
        if [ "$size_mb" -gt 200 ]; then
            echo -e "${YELLOW}WARNING: Next.js cache is ${size_mb}MB${NC}"
            log "WARNING: Next.js cache is ${size_mb}MB"
            return 1
        else
            echo -e "${GREEN}OK: Next.js cache is ${size_mb}MB${NC}"
            log "OK: Next.js cache is ${size_mb}MB"
        fi
    else
        echo -e "${GREEN}OK: Next.js cache directory not found${NC}"
        log "OK: Next.js cache directory not found"
    fi

    return 0
}

# Function to check system logs for attack patterns
check_system_logs() {
    local warning_found=0

    echo "Checking system log sizes..."

    # Check btmp (failed logins) - requires sudo but may fail silently
    if [ -f "/var/log/btmp" ]; then
        local btmp_size_mb=$(sudo du -m /var/log/btmp 2>/dev/null | cut -f1)
        if [ -z "$btmp_size_mb" ]; then
            btmp_size_mb="unknown"
            echo -e "${YELLOW}WARNING: Cannot read btmp size (sudo required)${NC}"
            log "WARNING: Cannot read btmp size (sudo required)"
            warning_found=1
        elif [ "$btmp_size_mb" -gt 50 ] 2>/dev/null; then
            echo -e "${YELLOW}WARNING: btmp (failed logins) is ${btmp_size_mb}MB${NC}"
            log "WARNING: btmp (failed logins) is ${btmp_size_mb}MB"
            warning_found=1
        else
            echo -e "${GREEN}OK: btmp is ${btmp_size_mb}MB${NC}"
            log "OK: btmp is ${btmp_size_mb}MB"
        fi
    fi

    # Check auth.log
    if [ -f "/var/log/auth.log" ]; then
        local auth_size_mb=$(sudo du -m /var/log/auth.log 2>/dev/null | cut -f1)
        if [ -z "$auth_size_mb" ]; then
            auth_size_mb="unknown"
            echo -e "${YELLOW}WARNING: Cannot read auth.log size (sudo required)${NC}"
            log "WARNING: Cannot read auth.log size (sudo required)"
            warning_found=1
        elif [ "$auth_size_mb" -gt 20 ] 2>/dev/null; then
            echo -e "${YELLOW}WARNING: auth.log is ${auth_size_mb}MB${NC}"
            log "WARNING: auth.log is ${auth_size_mb}MB"
            warning_found=1
        else
            echo -e "${GREEN}OK: auth.log is ${auth_size_mb}MB${NC}"
            log "OK: auth.log is ${auth_size_mb}MB"
        fi
    fi

    return $warning_found
}

# Function to check fail2ban status
check_fail2ban() {
    if sudo systemctl is-active --quiet fail2ban; then
        local banned_count=$(sudo fail2ban-client status sshd 2>/dev/null | grep "Currently banned" | awk '{print $4}' || echo "0")
        echo -e "${GREEN}OK: Fail2ban is running (${banned_count} IPs banned)${NC}"
        log "OK: Fail2ban is running (${banned_count} IPs banned)"
        return 0
    else
        echo -e "${RED}ERROR: Fail2ban is not running${NC}"
        log "ERROR: Fail2ban is not running"
        return 1
    fi
}

# Function to check PM2 logrotate status
check_pm2_logrotate() {
    if pm2 list | grep -q "pm2-logrotate.*online"; then
        echo -e "${GREEN}OK: PM2 logrotate is running${NC}"
        log "OK: PM2 logrotate is running"
        return 0
    else
        echo -e "${RED}ERROR: PM2 logrotate is not running${NC}"
        log "ERROR: PM2 logrotate is not running"
        return 1
    fi
}

# Main execution
main() {
    echo "=== ggbot Disk Space Monitor ==="
    log "=== Disk Space Monitor Started ==="

    local exit_code=0

    # Run all checks
    check_disk_usage || exit_code=1
    check_pm2_logs || exit_code=1
    check_app_logs || exit_code=1
    check_nextjs_cache || exit_code=1
    check_system_logs || exit_code=1
    check_fail2ban || exit_code=1
    check_pm2_logrotate || exit_code=1

    echo "=== Monitor Complete ==="
    log "=== Disk Space Monitor Complete (exit code: $exit_code) ==="

    exit $exit_code
}

# Run main function
main "$@"