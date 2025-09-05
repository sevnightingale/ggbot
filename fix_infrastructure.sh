#!/bin/bash
# GGBot Infrastructure Fix Script
# Generated: 2025-09-05
# Purpose: Fix file naming, PM2, nginx, and CORS issues

echo "================================================"
echo "GGBot Infrastructure Fix - Complete Guide"
echo "================================================"
echo ""
echo "This script contains both regular and sudo commands."
echo "Run regular commands directly, sudo commands require your password."
echo ""

# ================================================
# PHASE 1: BACKUP AND FILE STRUCTURE
# ================================================
echo "PHASE 1: Backup and File Structure"
echo "-----------------------------------"
echo ""
echo "Step 1.1: Create backups (RUN THESE):"
echo "cd /home/sev/ggbot"
echo "cp main_api.py main_api_backup_$(date +%Y%m%d_%H%M%S).py"
echo "cp ggbot.py ggbot_backup_$(date +%Y%m%d_%H%M%S).py"
echo ""

echo "Step 1.2: Stop PM2 service (RUN THIS):"
echo "pm2 stop ggbot"
echo ""

echo "Step 1.3: Fix ggbot.py port configuration (AUTOMATED - will be done by Claude):"
echo "# Claude will update ggbot.py line 1076: port=8001 -> port=8000"
echo "# Claude will ensure uvicorn.run uses 'ggbot:app' not 'main_api:app'"
echo ""

# ================================================
# PHASE 2: NGINX CONFIGURATION (REQUIRES SUDO)
# ================================================
echo "PHASE 2: Nginx Configuration (REQUIRES SUDO)"
echo "---------------------------------------------"
echo ""
echo "Step 2.1: Backup nginx config (SUDO REQUIRED):"
cat << 'EOF'
sudo cp /etc/nginx/sites-available/ggbots-api /etc/nginx/sites-available/ggbots-api.backup.$(date +%Y%m%d)
EOF
echo ""

echo "Step 2.2: Create updated nginx config (SUDO REQUIRED):"
echo "# Claude will create a file at /tmp/ggbots-api-new with proper CORS"
echo "# Then you run:"
cat << 'EOF'
sudo cp /tmp/ggbots-api-new /etc/nginx/sites-available/ggbots-api
EOF
echo ""

echo "Step 2.3: Test nginx configuration (SUDO REQUIRED):"
cat << 'EOF'
sudo nginx -t
EOF
echo ""

echo "Step 2.4: Reload nginx to fix stuck worker (SUDO REQUIRED):"
cat << 'EOF'
sudo systemctl reload nginx
EOF
echo ""

echo "Optional: If reload doesn't work, restart nginx (SUDO REQUIRED):"
cat << 'EOF'
sudo systemctl restart nginx
EOF
echo ""

# ================================================
# PHASE 3: PM2 SERVICE UPDATE
# ================================================
echo "PHASE 3: PM2 Service Update"
echo "----------------------------"
echo ""

echo "Step 3.1: Delete old PM2 service (RUN THIS):"
echo "pm2 delete ggbot"
echo ""

echo "Step 3.2: Create ecosystem.config.js (AUTOMATED - will be done by Claude):"
echo "# Claude will create the PM2 ecosystem config file"
echo ""

echo "Step 3.3: Start service with new config (RUN THIS):"
echo "pm2 start ecosystem.config.js"
echo ""

echo "Step 3.4: Save PM2 configuration (RUN THIS):"
echo "pm2 save"
echo ""

echo "Step 3.5: Setup PM2 startup script (SUDO REQUIRED):"
echo "pm2 startup"
echo "# This will output a sudo command - copy and run it"
echo ""

# ================================================
# PHASE 4: VERIFICATION COMMANDS
# ================================================
echo "PHASE 4: Verification"
echo "---------------------"
echo ""

echo "Step 4.1: Check services status (RUN THESE):"
cat << 'EOF'
pm2 status
pm2 logs ggbot --lines 20
curl -s https://ggbots-api.nightingale.business/health
curl -I https://ggbots-api.nightingale.business/api/v2/config 2>&1 | grep -i "access-control"
EOF
echo ""

echo "Step 4.2: Test WebSocket connection (RUN THIS):"
cat << 'EOF'
python -c "import asyncio, websockets; asyncio.run(websockets.connect('wss://ggbots-api.nightingale.business/ws/bot-status/test').ws_client.close())" && echo "WebSocket OK" || echo "WebSocket FAILED"
EOF
echo ""

# ================================================
# PHASE 5: CLEANUP (OPTIONAL)
# ================================================
echo "PHASE 5: Cleanup (OPTIONAL - After everything works)"
echo "-----------------------------------------------------"
echo ""

echo "Step 5.1: Remove old backup files (RUN WHEN CONFIDENT):"
cat << 'EOF'
rm main_api_backup_*.py
rm ggbot_backup_*.py
rm main_api_legacy.py
rm main_api_old.py
EOF
echo ""

echo "================================================"
echo "TROUBLESHOOTING COMMANDS"
echo "================================================"
echo ""

echo "If PM2 has issues:"
cat << 'EOF'
pm2 kill  # Stop all PM2 processes
pm2 resurrect  # Restore saved processes
EOF
echo ""

echo "If nginx has issues (SUDO REQUIRED):"
cat << 'EOF'
sudo journalctl -u nginx -n 50  # Check nginx logs
sudo netstat -tlnp | grep :80  # Check port 80
sudo netstat -tlnp | grep :443  # Check port 443
EOF
echo ""

echo "If API has issues:"
cat << 'EOF'
netstat -tlnp | grep :8000  # Check if port 8000 is in use
ps aux | grep python | grep ggbot  # Check if ggbot.py is running
tail -f ~/.pm2/logs/ggbot-error.log  # Watch error logs
EOF
echo ""

echo "================================================"
echo "END OF SCRIPT"
echo "================================================"


sudo env PATH=$PATH:/usr/bin /home/sev/.npm-global/lib/node_modules/pm2/bin/pm2 startup systemd -u sev --hp /home/sev