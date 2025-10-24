# Status Check Script

Comprehensive platform status check for ggbots. Queries the Supabase database for real-time metrics.

## Usage

### Display Full Status Report
```bash
source .venv/bin/activate
python scripts/status_check.py
```

This shows:
- **User Statistics**: Total users, Pro vs Free, subscription status
- **Bot Statistics**: Total bots, active/inactive breakdown, paper vs live mode
- **Trading Activity**: All-time trades, win/loss stats, recent activity (24h/7d/30d)
- **Open Positions**: Current positions, exposure, unrealized P&L
- **Account Balances**: Average, min, max paper trading balances
- **Top Symbols**: Most popular trading pairs by bot count
- **Decision Activity**: Recent AI decisions (24h) by action type
- **System Health**: Recent activity indicator

### Update ACTIVE.md Automatically
```bash
source .venv/bin/activate
python scripts/status_check.py --update
```

This will:
1. Display the full status report
2. Update the header section of ACTIVE.md with current metrics
3. Update the "Last Updated" date
4. Update user count and active bot count

**Note**: Only the header is updated (first 6 lines). All other content in ACTIVE.md is preserved.

### Quiet Mode (for Monitoring/Cron)
```bash
source .venv/bin/activate
python scripts/status_check.py --quiet
```

Outputs a single line summary:
```
2025-10-22 16:04:54 | Users: 256 | Active Bots: 57 | Trades (24h): 271 | Open Positions: 26
```

Useful for:
- Cron jobs
- System monitoring dashboards
- Log aggregation
- Quick status checks

## Metrics Collected

### User Metrics
- Total registered users
- Pro users (ggbase subscription tier)
- Free users
- Active subscribers (paid and not expired)
- Users with at least one bot

### Bot Metrics
- Total bots created (all time)
- Active bots (state = 'active')
- Inactive bots (state = 'inactive')
- Breakdown by trading mode (paper vs live)
- Average bots per user

### Trading Metrics
- Total trades (all time)
- Win/loss breakdown
- Platform-wide win rate
- Total P&L across all accounts
- Recent activity (24h, 7d, 30d)

### Position Metrics
- Current open positions
- Unique symbols being traded
- Total exposure (sum of position sizes)
- Unrealized P&L

### Account Metrics
- Average paper trading balance
- Lowest balance (still active)
- Highest balance

### Activity Metrics
- Top 10 most popular symbols (by active bot count)
- Decision activity (24h) by action type (enter/exit/wait)
- Average confidence scores per action
- Recent extractions (last hour) for health check

## Example Output

```
================================================================================
GGBOTS PLATFORM STATUS CHECK
Generated: 2025-10-22 15:58:06 UTC
================================================================================

📊 USER STATISTICS
--------------------------------------------------------------------------------
Total Users: 256
  Pro Users (ggbase): 5 (2 active subscriptions)
  Free Users: 251
Users with Bots: 250 (97.7%)

🤖 BOT STATISTICS
--------------------------------------------------------------------------------
Total Bots Created: 376
  Active: 57 (15.2%)
    Paper: 57
    Live: 0
  Inactive: 319
Avg Bots per User: 1.5

💹 TRADING ACTIVITY
--------------------------------------------------------------------------------
Total Trades (All Time): 3,202
  Wins: 1,009
  Losses: 2,193
  Platform Win Rate: 31.51%
  Total P&L: $-9,331.25

Recent Activity:
  Last 24 hours: 273 trades
  Last 7 days: 1521 trades
  Last 30 days: 3155 trades

📍 OPEN POSITIONS
--------------------------------------------------------------------------------
Open Positions: 22
Unique Symbols: 3
Total Exposure: $30,367.16
Unrealized P&L: $324.91

💰 ACCOUNT BALANCES (Paper Trading)
--------------------------------------------------------------------------------
Average Balance: $9,937.90
Lowest Balance: $6,463.96
Highest Balance: $10,421.75

🔥 TOP TRADING SYMBOLS (Active Bots)
--------------------------------------------------------------------------------
Symbol          Bots
-------------------------
BTC/USDT        44
BNB/USDT        3
SOL/USDT        2

🧠 DECISION ACTIVITY (24h)
--------------------------------------------------------------------------------
Action       Count      Avg Confidence
----------------------------------------
wait         2577       56.8%
enter        275        63.5%
exit         149        74.2%

💚 SYSTEM HEALTH
--------------------------------------------------------------------------------
Decisions (last hour): 134
Status: 🟢 HEALTHY
================================================================================
```

## Integration

### Cron Job (Optional)
Run automated checks every 6 hours and log results:

```bash
# Add to crontab: crontab -e
0 */6 * * * cd /home/sev/ggbot && source .venv/bin/activate && python scripts/status_check.py --quiet >> logs/status_checks.log 2>&1
```

### Manual Update Before Releases
Before major releases or when updating documentation:

```bash
cd /home/sev/ggbot
source .venv/bin/activate
python scripts/status_check.py --update
git add ACTIVE.md
git commit -m "Update platform metrics in ACTIVE.md"
```

## Notes

- **Read-Only**: This script only reads from the database (SELECT queries only)
- **Safe to Run**: Can be run as frequently as needed without impacting production
- **Database Connection**: Uses the same `core.common.db` infrastructure as the rest of the platform
- **Error Handling**: Includes comprehensive error handling with stack traces
- **Comparison to X-Bot**: More detailed than the daily X-bot tweet (which only shows basic counts)

## Comparison: X-Bot vs Status Check

| Metric | X-Bot Daily Tweet | Status Check Script |
|--------|-------------------|---------------------|
| User Count | ✅ | ✅ |
| Active Bots | ✅ | ✅ |
| Total Trades | ✅ | ✅ |
| Symbols Tracked | ✅ | ✅ Top 10 Breakdown |
| Open Positions | ✅ | ✅ + Exposure + P&L |
| Win Rate | ❌ | ✅ |
| Recent Activity | ❌ | ✅ (24h/7d/30d) |
| Trading Mode Split | ❌ | ✅ |
| Subscription Stats | ❌ | ✅ |
| Decision Activity | ❌ | ✅ |
| Account Balances | ❌ | ✅ |
| System Health | ❌ | ✅ |

The status check script is designed for **internal monitoring and documentation updates**, while the X-bot focuses on **public-facing marketing metrics**.
