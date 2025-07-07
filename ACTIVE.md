# 🚀 ACTIVE - GGBots System Status

**Last Updated**: 2025-06-29  
**System Health**: 🟢 Operational

---

## 📊 System Overview

### Core Services (PM2)
| Service | Status | CPU | Memory | Uptime | Purpose |
|---------|--------|-----|---------|---------|---------|
| ggbots-api | 🟢 Online | 100%* | 321MB | 31h | Main API server (FastAPI) |
| ccxt-mcp-server | 🟢 Online | 0% | 59MB | 3D | Crypto price/data provider |
| ggshot-filter | 🟢 Online | 0% | 66MB | 31h | Signal filtering service |

*CPU issue being addressed - see Active Issues

### Database
- **PostgreSQL**: Running on localhost
- **Tables**: market_data, trades, configurations, account_monitoring, etc.
- **Health**: ✅ Operational

---

## 🔄 Background Tasks & Scheduled Jobs

### Always Running
1. **WebSocket Updates** (`dashboard_api.py`)
   - Frequency: Every 30 seconds
   - Purpose: Push position updates to connected dashboard clients
   - Status: ✅ Fixed - only runs when connections exist

2. **Process Cleanup** (`agent_control_api.py`)
   - Frequency: Every 5 minutes (was 60s)
   - Purpose: Clean up terminated trading/extraction/decision processes
   - Status: ✅ Fixed - only runs when processes exist

3. **Old Status Cleanup** (`extraction/api.py`)
   - Frequency: Every hour
   - Purpose: Clean up extraction statuses older than 24 hours
   - Status: ✅ Low impact

4. **Decision Cache Cleanup** (`decision/api.py`)
   - Frequency: Every hour
   - Purpose: Clean up decision cache older than 24 hours
   - Status: ✅ Low impact

### Scheduled Jobs (When Enabled)
- **Autonomous Trading**: Currently DISABLED
- **Scheduled Extractions**: Currently DISABLED

---

## 🎯 Current Focus

### Critical Issue - Indicator Value Parsing
**Status**: 🔴 **CRITICAL BUG IDENTIFIED**
- **Problem**: LLM misreading complex JSON arrays from MCP server
- **Impact**: Wrong signal assessments (e.g., Aroon Down: 100→35.71, Vortex VI-: 0.072→1.164)
- **Root Cause**: MCP returns raw arrays, LLM can't reliably extract current values
- **Solution**: Adding smart preprocessing to crypto-indicators MCP server

### Live Production Service
**ggShot Signal Filtering** 
- Status: ⚠️ ACTIVE but with parsing errors affecting accuracy
- Processing: ~10-12 signals/day with 10 technical indicators
- Publishing: High-confidence signals to Telegram (≥0.50)
- Latest: 4-Pillar Framework deployed, but indicator parsing needs fix

### Active Tasks
1. **MCP Preprocessing** - Adding intelligent preprocessing to return contextual indicator data
2. **API CPU Usage** - Fixed, pending restart to apply
3. **Signal Accuracy** - Fix parsing to improve 4-pillar validation accuracy

---

## 🏗️ What We Just Completed

**4-Pillar Framework Implementation** ✅
- Replaced simple RSI with 10-indicator analysis
- Market regime detection (Aroon/BBW)
- Volume confirmation (SMA_Volume_30/Vortex/VWAP)
- Multi-timeframe context (RSI + RSI_4h)
- Risk assessment (Bollinger Bands/ATR)
- Custom system prompts for ggShot mode
- Graduated confidence scoring (0.00-1.00)

## 🎯 Next Steps
1. **Test with real signals** - Restart servers and monitor
2. **Tune confidence threshold** - Based on signal quality
3. **Performance metrics** - Track 4-pillar vs old RSI accuracy

---

## 📈 Performance Metrics

### ggShot Performance
- Framework: 4-Pillar validation (NEW)
- Indicators: 10 (was 1)
- Processing time: ~55 seconds
- Confidence threshold: 0.50

### System Resources
- API: 321MB (high CPU fixed, needs restart)
- CCXT MCP: 59MB stable
- ggShot: 66MB stable

---

## 🔧 Maintenance Notes

### Recent Changes
- 2025-06-29: **Major**: Implemented 4-Pillar validation framework
- 2025-06-29: Fixed BollingerBandsWidth MCP bug
- 2025-06-29: Added Aroon indicator (replaced unavailable ADX)
- 2025-06-28: Fixed agent cleanup frequency (60s → 300s)
- 2025-06-26: Deployed ggShot service to PM2

### Monitoring Commands
```bash
# Check service status
pm2 list
pm2 monit

# View logs
pm2 logs ggbots-api
pm2 logs ggshot-filter

# Check system resources
htop
df -h

# Database connections
psql -U ggbots -d ggbots -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## 🚨 Emergency Contacts

- **System**: Ubuntu VM on personal infrastructure
- **Database**: PostgreSQL (local)
- **External Services**:
  - Telegram API (ggShot signals)
  - DeepSeek API (LLM validation)
  - Multiple crypto exchanges (CCXT)

---

*This file should be updated regularly to reflect the current system state*