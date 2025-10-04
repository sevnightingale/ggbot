# X Bot Strategy & Planning

## Overview
Automated X (Twitter) bot for @ggbots_ai to increase visibility, engagement, and showcase ggbots trading platform capabilities.

**Current Tier:** Free (500 writes/month, 100 reads/month)

**Deployment Strategy:** Separate PM2 service running independently from main ggbot orchestrator

**Status:** 🟢 **LIVE IN PRODUCTION** (deployed 2025-10-04)

---

## 🚀 Deployment Status

**Production Service:**
- **PM2 Process:** `x-bot` (process #6)
- **Status:** Online and running
- **Memory:** ~7MB
- **Account:** @ggbots_ai
- **First Tweet:** 2025-10-04 (Tweet ID: 1974523110713126946)

**Active Features:**
- ✅ Daily platform status tweets (9:00 AM UTC)
- ✅ Real-time database metrics (active bots, users, trades, symbols, open positions)
- ✅ Automatic authentication and error handling
- ✅ APScheduler integration with job monitoring

**Files Deployed:**
- `x_bot/bot.py` - Main service with scheduler
- `x_bot/utils/x_client.py` - Tweepy API wrapper
- `x_bot/schedulers/platform_status.py` - Daily status tweet logic
- `ecosystem.config.js` - PM2 configuration (x-bot service)

---

## X API v2 Technical Details

### Current Free Tier Limits (Official)
- **Monthly Write Limit:** 500 posts/month (user-level)
- **Monthly Read Limit:** 100 requests/month (app-level)
- **App IDs:** 1
- **Limitations:**
  - No filtered stream access (requires Pro tier at $5,000/month)
  - Cannot use like/follow endpoints (removed Aug 2024)
  - Limited read access makes real-time mention monitoring impractical
  - Best suited for write-only use cases (scheduled posts, announcements)

### Key API Endpoints We'll Use

**1. POST /2/tweets** (Create Tweet)
- **Purpose:** Post tweets, replies
- **Authentication:** OAuth 1.0a User Context (what we set up)
- **Rate Limit (Free):** No specific 15-min window limit documented for free tier
- **Monthly Cap:** 500 posts total
- **Payload Example:**
  ```json
  {
    "text": "Your tweet content here",
    "reply": {
      "in_reply_to_tweet_id": "1234567890"  // For replies
    }
  }
  ```

**2. GET /2/users/:id/tweets** (User Timeline)
- **Purpose:** Fetch recent tweets from specific accounts (for targeted replies)
- **Authentication:** OAuth 1.0a, OAuth 2.0, or Bearer Token
- **Rate Limit (Free):** Unknown 15-min limit, but counted against 100/month cap
- **Parameters:**
  - `max_results`: 5-100 (default 10)
  - `since_id`: Only return tweets after this ID (critical for avoiding duplicates)
  - `tweet.fields`: Specify what data to include
- **Usage:** 1 request = 1 tweet fetch (even if returns multiple tweets)

**3. GET /2/users/:id/mentions** (NOT VIABLE ON FREE TIER)
- **Purpose:** Get tweets mentioning your account
- **Problem:** Would require too many reads for real-time monitoring
- **Alternative:** Use targeted replies strategy instead

### Authentication Flow
- **OAuth 1.0a User Context** (what we configured)
- Required for `POST /2/tweets` (bearer tokens NOT supported for writes)
- Uses 4-legged OAuth with consumer key/secret + access token/secret
- Already configured in `.env`

### Rate Limit Headers
Every API response includes:
- `X-Rate-Limit-Limit`: Total requests allowed in window
- `X-Rate-Limit-Remaining`: Requests left in current window
- `X-Rate-Limit-Reset`: Unix timestamp when limit resets

**Critical:** Must track these to avoid 429 errors (Too Many Requests)

### Error Handling Requirements
- **429 Too Many Requests:** Wait until `X-Rate-Limit-Reset` time
- **503 Service Unavailable:** Exponential backoff (start with 1 min, double each retry)
- **401 Unauthorized:** Token expired/invalid - log and alert
- **403 Forbidden:** Permissions issue - check app settings

---

## Strategy 1: Targeted Account Replies (Free Tier)

### Concept
Daily engagement with curated list of influential accounts by replying to their latest tweets.

### Mechanics
- **Frequency:** 3 replies/day
- **Monthly Usage:** ~90 reads + ~90 writes (well within free tier)
- **Target List:** Curated list of relevant accounts (trading influencers, market analysts, etc.)
- **Selection:** Rotate through list, max 1 reply per account per week
- **Timing:** Space out throughout day (e.g., 9am, 2pm, 8pm UTC)

### Implementation Notes
- Store list of target accounts with metadata (username, last_replied_date, category)
- Fetch latest tweet: `GET /2/users/:id/tweets` (limit=1)
- AI analyzes tweet content for relevance before replying
- Generate contextual reply using LLM (GPT-4, Claude, or DeepSeek)
- Track reply history to avoid duplicate/spam behavior
- Quality filter: Only reply if tweet is relevant to trading/markets/analysis

### Target Account Categories
- Crypto traders/analysts
- Market commentators
- Trading tool developers
- DeFi thought leaders
- Technical analysis experts
- **(User to provide initial list)**

---

## Strategy 2: Scheduled Trade Announcements

### Concept
Automatically tweet when ggbot makes trade decisions - real-time transparency of bot performance.

### What to Tweet
**Entry Signals:**
```
📈 LONG $SYMBOL @ $PRICE
Confidence: 85%
Timeframe: 4h
Position size: 2% account
Indicators: RSI oversold + bullish divergence
#trading #ggbots
```

**Exit Signals:**
```
🎯 CLOSED $SYMBOL @ $PRICE
Entry: $ENTRY_PRICE
P&L: +12.4% (+$247)
Hold time: 14h 32m
#ggbots
```

### Integration Points
**Option A: Hook into Decision Agent**
- Monitor `decision/engine_v2.py` decision output
- When decision = "BUY" or "SELL", trigger tweet
- Parse decision_result for relevant data (symbol, confidence, reasoning)

**Option B: Hook into Trading Agent**
- Monitor `trading/paper/supabase_service.py`
- When trade executes, pull from `paper_trades` table
- Tweet on entry and exit events

**Option C: Webhook from ggbot.py orchestrator**
- Add X bot notification step in pipeline
- After `_run_trading_v2()`, check if trade executed
- Format and send tweet

### Data to Include
- Symbol/ticker
- Entry/exit price
- Position size or % of account
- Confidence score (from decision agent)
- Key indicators/reasoning (brief)
- P&L (for exits)
- Hold time (for exits)
- Relevant hashtags

### Frequency Considerations
- **Conservative:** Only tweet high-confidence trades (>70%)
- **Active trading:** Could generate 5-15 tweets/day depending on bot activity
- **Monthly cap:** 500 writes allows plenty of room
- **User preference:** Configurable filter (min confidence, position size threshold, etc.)

---

## Strategy 3: General Scheduled Content

### Daily Market Analysis (Once per day)
**Time:** 9:00 AM UTC (market open-ish)
**Content Ideas:**
- Top movers in watchlist
- Market sentiment summary
- Key levels to watch for major pairs
- Volatility analysis

**Example:**
```
📊 Market Pulse - Oct 4, 2025

🔥 Trending: $BTC testing resistance at $67.2k
📉 Weakness: $ETH down 3.2%, breaking support
⚡ High volatility: $SOL 15% daily range

Top setups being monitored...
#markets #trading
```

**Data Source:**
- Pull from extraction agent (`extraction/v2/indicators.py`)
- Aggregate multiple symbols from user's watchlist
- Use LLM to summarize key patterns

---

### Weekly Performance Summary (Once per week)
**Time:** Sunday 8:00 PM UTC
**Content:**
```
📈 Week in Review

Trades executed: 12
Win rate: 75% (9W-3L)
Best trade: $SOL +24.3%
Avg hold time: 18h
Total P&L: +8.7%

Best performing strategy: Momentum breakouts
#ggbots #trading
```

**Data Source:**
- Query `paper_trades` table for past 7 days
- Calculate aggregate stats
- Highlight best/worst trades

---

### Educational/Insights Content (2-3x per week)
**Time:** Variable (afternoon/evening)
**Content Ideas:**
- Trading psychology tips
- Indicator explanations
- Market structure lessons
- Risk management principles
- Automation benefits

**Example:**
```
💡 Trading Insight

Why position sizing matters:
✅ Risk 1-2% per trade max
✅ Allows for drawdowns without blowing up
✅ Compounds gains over time

Even with 60% win rate, poor sizing = rekt
Our bots use dynamic sizing based on confidence scores.
```

**Generation:**
- Pre-written templates with variables
- LLM-generated insights (rotate topics)
- Could tie to recent market events

---

### Platform Updates/Features (As needed)
**Frequency:** Irregular (when new features launch)
**Content:**
```
🚀 New Feature Alert

ggbots now supports multi-timeframe confirmation!

Our decision engine analyzes:
- 1h trend
- 4h momentum
- 1d structure

= Higher quality signals, fewer false breakouts

Try it: ggbots.ai
```

---

## LLM Integration Strategy

### LLM Provider Options
1. **OpenAI GPT-4** (already in use for decision agent)
   - Pros: High quality, consistent
   - Cons: Cost (~$0.01 per tweet with context)

2. **DeepSeek** (already integrated)
   - Pros: Cost-effective, fast
   - Cons: May need more prompt engineering

3. **Claude** (Anthropic)
   - Pros: Great for nuanced writing, brand voice
   - Cons: Not yet integrated

### Use Cases for LLM

**1. Trade Announcement Formatting**
- Input: Raw decision/trade data (JSON)
- Output: Formatted tweet with context
- Prompt: "Format this trade data into an engaging tweet under 280 chars..."

**2. Targeted Reply Generation**
- Input: Target account's tweet text
- Output: Relevant, non-spammy reply
- Prompt: "Generate a thoughtful reply to this trading tweet. Be helpful and relevant to ggbots market analysis capabilities..."

**3. Market Analysis Summarization**
- Input: Multiple indicator outputs, price data
- Output: Concise market summary
- Prompt: "Summarize these market conditions in 2-3 sentences for traders..."

**4. Educational Content Generation**
- Input: Topic/theme
- Output: Complete tweet with insight
- Prompt: "Write an educational tweet about [risk management/indicators/psychology]..."

### Implementation Pattern
```python
from decision.llm_providers.openai_provider import OpenAIProvider
# or DeepSeekProvider, AnthropicProvider

async def generate_tweet(tweet_type: str, data: dict) -> str:
    llm = OpenAIProvider()

    prompt = get_prompt_for_type(tweet_type)
    context = format_data_for_llm(data)

    response = await llm.generate(
        prompt=f"{prompt}\n\nData: {context}",
        max_tokens=100,  # Keep tweets concise
        temperature=0.7  # Balanced creativity
    )

    # Validate length (280 char limit)
    tweet = response[:280]

    return tweet
```

### Prompt Templates (Draft)

**Trade Entry:**
```
You are @ggbots_ai, an AI trading bot. Generate an engaging tweet announcing a new trade entry.

Format:
- Emoji indicator (📈 for long, 📉 for short)
- Symbol and entry price
- Key reasoning (1 line max)
- Confidence score
- Relevant hashtags

Keep under 280 characters. Be professional but engaging.

Trade data: {data}
```

**Market Analysis:**
```
You are @ggbots_ai. Summarize current market conditions based on technical analysis.

Include:
- Top 2-3 notable price movements
- Key levels or patterns
- Brief sentiment assessment

Style: Informative, data-driven, no hype
Length: Under 280 characters

Analysis data: {data}
```

**Targeted Reply:**
```
You are @ggbots_ai, an AI trading analysis platform. Generate a thoughtful reply to this tweet.

Guidelines:
- Be helpful and relevant
- Reference specific points from the original tweet
- Relate to ggbots capabilities when appropriate (but don't force it)
- No spam, no generic replies
- Professional tone

Original tweet: {tweet_text}
Author: @{username}

Reply:
```

---

## Separate Service Architecture (RECOMMENDED)

### Why Separate Service?
1. **Isolation:** X bot won't affect ggbot.py performance (runs in own process)
2. **Independent scaling:** Can restart X bot without touching trading operations
3. **Simpler debugging:** Logs are separate, easier to troubleshoot
4. **Different lifecycles:** X bot is event-driven + scheduled, ggbot.py is continuous trading
5. **Resource management:** Each service has dedicated memory/CPU allocation

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                         Supabase Database                        │
│  (paper_trades, decisions, x_bot_tweets, x_bot_state, etc.)     │
└─────────────────────────────────────────────────────────────────┘
         ▲                              ▲
         │ Writes trades                │ Reads trades
         │ Writes decisions             │ Writes tweets
         │                              │ Reads/writes state
         │                              │
┌────────┴──────────┐         ┌─────────┴────────────┐
│   ggbot.py        │         │   x_bot/bot.py       │
│   (PM2: ggbot)    │         │   (PM2: x-bot)       │
├───────────────────┤         ├──────────────────────┤
│ - Extraction      │         │ - APScheduler        │
│ - Decision        │         │ - Tweepy Client      │
│ - Trading         │         │ - LLM Generator      │
│ - WebSocket       │         │ - Rate Limiter       │
│                   │         │ - Trade Monitor      │
└───────────────────┘         └──────────────────────┘
                                       │
                                       ▼
                              ┌────────────────┐
                              │  X API v2      │
                              │  (@ggbots_ai)  │
                              └────────────────┘
```

### Communication Pattern: Database Polling

**X bot monitors Supabase for new trades/decisions rather than direct integration**

**How Trade Announcements Work:**
1. ggbot.py executes trade → writes to `paper_trades` table with `tweeted: false`
2. X bot polls `paper_trades` every 60 seconds: `SELECT * FROM paper_trades WHERE tweeted = false`
3. X bot finds new trade → generates tweet → posts to X
4. X bot updates: `UPDATE paper_trades SET tweeted = true, tweet_id = '...' WHERE id = ...`
5. Logs to `x_bot_tweets` table for tracking

**Advantages:**
- ✅ Loose coupling (services don't directly depend on each other)
- ✅ X bot can be down without affecting trading
- ✅ Easy to replay/re-tweet if needed (just set `tweeted = false`)
- ✅ No HTTP calls between services (just database queries)

**Disadvantages:**
- ⏱️ Slight delay (up to 60 seconds) before tweet after trade
- 🔄 Requires polling loop (minimal overhead)

### Alternative: WebSocket Notifications (Future)

Could use ggbot.py's WebSocket server for real-time notifications:

```python
# In ggbot.py - after trade execution
await websocket_manager.broadcast({
    'type': 'new_trade',
    'trade_id': trade.id,
    'symbol': trade.symbol,
    'action': trade.action
})

# In x_bot/bot.py - WebSocket client
async def listen_for_trades():
    async with websockets.connect('ws://localhost:8000/ws') as ws:
        async for message in ws:
            data = json.loads(message)
            if data['type'] == 'new_trade':
                await handle_trade_tweet(data['trade_id'])
```

**Advantages:**
- ✅ Real-time (sub-second latency)
- ✅ No polling overhead

**Disadvantages:**
- ❌ Tighter coupling (X bot must connect to ggbot.py)
- ❌ More complex error handling (reconnection logic)
- ❌ X bot crash = missed notifications (unless queued)

**Recommendation:** Start with database polling (simpler), upgrade to WebSocket if real-time is critical

---

## PM2 Deployment & Process Management

### Service Configuration

**New PM2 Ecosystem File:** `ecosystem.config.js`
```javascript
module.exports = {
  apps: [
    {
      name: 'ggbot',
      script: 'ggbot.py',
      interpreter: '/home/sev/ggbot/.venv/bin/python',
      cwd: '/home/sev/ggbot',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO'
      },
      error_file: 'logs/ggbot-error.log',
      out_file: 'logs/ggbot-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    },
    {
      name: 'x-bot',
      script: 'x_bot/bot.py',
      interpreter: '/home/sev/ggbot/.venv/bin/python',
      cwd: '/home/sev/ggbot',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO',
        X_BOT_ENABLED: 'true'  // Killswitch
      },
      error_file: 'logs/x-bot-error.log',
      out_file: 'logs/x-bot-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    }
  ]
};
```

### PM2 Commands

```bash
# Start both services
pm2 start ecosystem.config.js

# Start only X bot
pm2 start ecosystem.config.js --only x-bot

# View status
pm2 status

# View logs (real-time)
pm2 logs x-bot
pm2 logs ggbot

# Restart after code changes
pm2 restart x-bot
pm2 restart ggbot

# Stop X bot (emergency killswitch)
pm2 stop x-bot

# Monitor resource usage
pm2 monit

# Save PM2 config (persist after reboot)
pm2 save
pm2 startup  # Generate startup script
```

### Startup Sequence

**When VPS boots:**
1. PM2 startup script runs (configured with `pm2 startup`)
2. Loads saved process list (`pm2 save`)
3. Starts `ggbot` process (main orchestrator)
4. Starts `x-bot` process (X bot)
5. Both services connect to Supabase
6. X bot initializes APScheduler with cron jobs
7. Both services running independently

**Dependency handling:**
- X bot doesn't wait for ggbot (no dependency)
- If ggbot crashes, X bot continues (scheduled tweets still work)
- If X bot crashes, ggbot unaffected

### Logging Strategy

**Separate log files:**
```
logs/
├── ggbot.log           # Main orchestrator (existing)
├── ggbot-error.log     # PM2 stderr for ggbot
├── ggbot-out.log       # PM2 stdout for ggbot
├── x-bot.log           # X bot application logs (we'll create this)
├── x-bot-error.log     # PM2 stderr for x-bot
└── x-bot-out.log       # PM2 stdout for x-bot
```

**Logging format in x_bot/bot.py:**
```python
from core.common.logger import logger  # Reuse existing ggbot logger

# All X bot logs use context
logger.bind(service="x-bot").info("Starting X bot scheduler")
logger.bind(service="x-bot", tweet_type="trade_entry").info(f"Tweeted trade {trade_id}")
logger.bind(service="x-bot").error(f"API error: {error}")
```

**Benefits:**
- Consistent logging format across services
- Easy to filter: `grep "x-bot" logs/ggbot.log`
- Centralized log rotation (already configured)

---

## X Bot Implementation Details

### Main Bot File: `x_bot/bot.py`

**Core Structure:**
```python
#!/usr/bin/env python3
"""
X Bot for @ggbots_ai
Runs as separate PM2 service, monitors trades and posts scheduled content.
"""

import asyncio
import os
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from core.common.logger import logger
from core.common.db import get_db_connection
from x_bot.utils.x_client import XClient
from x_bot.generators.tweet_generator import TweetGenerator
from x_bot.schedulers import (
    trade_announcer,
    daily_analysis,
    weekly_summary,
    account_replies
)

load_dotenv()

class XBot:
    def __init__(self):
        self.logger = logger.bind(service="x-bot")
        self.x_client = XClient()  # Tweepy wrapper
        self.tweet_gen = TweetGenerator()  # LLM-powered generation
        self.scheduler = AsyncIOScheduler()
        self.enabled = os.getenv('X_BOT_ENABLED', 'true').lower() == 'true'

    async def start(self):
        """Initialize and start the X bot service."""
        if not self.enabled:
            self.logger.warning("X bot disabled via X_BOT_ENABLED env var")
            return

        self.logger.info("Starting X bot for @ggbots_ai")

        # Test authentication
        if not await self.x_client.test_auth():
            self.logger.error("X API authentication failed - stopping")
            return

        # Register scheduled jobs
        self._register_jobs()

        # Start scheduler
        self.scheduler.start()
        self.logger.info("X bot scheduler started successfully")

        # Keep running
        try:
            await asyncio.Event().wait()  # Run forever
        except KeyboardInterrupt:
            self.logger.info("Shutting down X bot")
            self.scheduler.shutdown()

    def _register_jobs(self):
        """Register all scheduled jobs."""

        # Trade monitoring - check every minute for new trades
        self.scheduler.add_job(
            trade_announcer.check_and_tweet_trades,
            trigger=IntervalTrigger(minutes=1),
            id='trade_monitor',
            name='Monitor new trades',
            kwargs={'x_client': self.x_client, 'tweet_gen': self.tweet_gen}
        )

        # Daily market analysis - 9:00 AM UTC
        self.scheduler.add_job(
            daily_analysis.post_daily_analysis,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_analysis',
            name='Daily market analysis',
            kwargs={'x_client': self.x_client, 'tweet_gen': self.tweet_gen}
        )

        # Weekly summary - Sunday 8:00 PM UTC
        self.scheduler.add_job(
            weekly_summary.post_weekly_summary,
            trigger=CronTrigger(day_of_week='sun', hour=20, minute=0),
            id='weekly_summary',
            name='Weekly performance summary',
            kwargs={'x_client': self.x_client, 'tweet_gen': self.tweet_gen}
        )

        # Targeted replies - 9 AM, 2 PM, 8 PM UTC (3x/day)
        self.scheduler.add_job(
            account_replies.post_targeted_replies,
            trigger=CronTrigger(hour='9,14,20', minute=0),
            id='targeted_replies',
            name='Targeted account replies',
            kwargs={'x_client': self.x_client, 'tweet_gen': self.tweet_gen}
        )

        self.logger.info("Registered 4 scheduled jobs")

if __name__ == "__main__":
    bot = XBot()
    asyncio.run(bot.start())
```

### How Schedulers Work

**Example: `x_bot/schedulers/trade_announcer.py`**

```python
"""
Trade announcement scheduler.
Polls paper_trades table for new entries/exits and tweets them.
"""

from core.common.logger import logger
from core.common.db import get_db_connection

async def check_and_tweet_trades(x_client, tweet_gen):
    """
    Check for un-tweeted trades and announce them.
    Called every minute by APScheduler.
    """
    log = logger.bind(service="x-bot", scheduler="trade_announcer")

    try:
        # Query for un-tweeted trades
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, symbol, action, entry_price, quantity,
                           confidence, status, created_at
                    FROM paper_trades
                    WHERE tweeted = false
                    AND created_at > NOW() - INTERVAL '5 minutes'
                    ORDER BY created_at ASC
                    LIMIT 5
                """)
                trades = cur.fetchall()

        if not trades:
            return  # No new trades to tweet

        log.info(f"Found {len(trades)} un-tweeted trades")

        for trade in trades:
            trade_id = trade[0]

            # Generate tweet content using LLM
            tweet_text = await tweet_gen.generate_trade_entry_tweet({
                'symbol': trade[1],
                'action': trade[2],
                'price': trade[3],
                'quantity': trade[4],
                'confidence': trade[5]
            })

            # Post to X
            tweet_id = await x_client.post_tweet(tweet_text)

            if tweet_id:
                # Mark as tweeted
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE paper_trades
                            SET tweeted = true, tweet_id = %s
                            WHERE id = %s
                        """, (tweet_id, trade_id))
                        conn.commit()

                # Log to x_bot_tweets table
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO x_bot_tweets
                            (tweet_id, tweet_type, content, related_trade_id)
                            VALUES (%s, %s, %s, %s)
                        """, (tweet_id, 'trade_entry', tweet_text, trade_id))
                        conn.commit()

                log.info(f"Tweeted trade {trade_id}: {tweet_id}")
            else:
                log.error(f"Failed to tweet trade {trade_id}")

    except Exception as e:
        log.error(f"Error in trade announcer: {e}")
```

**Key Points:**
- Runs every minute via `IntervalTrigger(minutes=1)`
- Queries database for `tweeted = false`
- Only processes trades from last 5 minutes (avoid tweeting old trades on restart)
- Limits to 5 trades per run (rate limit safety)
- Updates database after successful tweet
- Logs all actions for debugging

### State Management

**Using `x_bot_state` table to track quotas:**

```python
# x_bot/utils/state_manager.py

from core.common.db import get_db_connection
import json

def get_state(key: str, default=None):
    """Get state value from database."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT state_value FROM x_bot_state WHERE state_key = %s",
                (key,)
            )
            result = cur.fetchone()
            return result[0] if result else default

def set_state(key: str, value):
    """Set state value in database (upsert)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO x_bot_state (state_key, state_value, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (state_key)
                DO UPDATE SET state_value = EXCLUDED.state_value,
                              updated_at = NOW()
            """, (key, json.dumps(value)))
            conn.commit()

def increment_quota(quota_type: str):
    """Increment daily/monthly quota counter."""
    current = get_state(f'{quota_type}_quota', {'count': 0, 'date': None})
    # Logic to increment and reset daily/monthly
    # ... implementation details
```

**Usage:**
```python
# Before tweeting
reads_today = get_state('reads_today', {'count': 0})['count']
if reads_today >= 3:  # Daily budget
    logger.warning("Daily read quota exceeded, skipping")
    return

# After API call
increment_quota('reads_daily')
increment_quota('reads_monthly')
```

---

## Technical Architecture

### File Structure (Proposed)
```
x_bot/
├── X_BOT.md                    # This file
├── generate_tokens.py          # Token generation (completed)
├── test_auth.py               # Auth test (completed)
├── bot.py                     # Main bot orchestrator
├── config.py                  # Configuration management
├── schedulers/
│   ├── trade_announcer.py     # Monitors trades, posts updates
│   ├── daily_analysis.py      # Daily market summary
│   ├── weekly_summary.py      # Weekly performance recap
│   └── account_replies.py     # Targeted account engagement
├── generators/
│   ├── tweet_generator.py     # LLM-powered tweet generation
│   └── prompts.py            # Prompt templates
├── utils/
│   ├── x_client.py           # Tweepy wrapper with error handling
│   ├── rate_limiter.py       # Rate limit tracking
│   └── state_manager.py      # Redis/DB state persistence
└── data/
    └── target_accounts.json   # List of accounts to engage with
```

### Database Schema Additions

**Modify Existing Table: `paper_trades`**
```sql
-- Add columns to track tweet status
ALTER TABLE paper_trades
ADD COLUMN tweeted BOOLEAN DEFAULT false,
ADD COLUMN tweet_id VARCHAR(255);

CREATE INDEX idx_paper_trades_tweeted ON paper_trades(tweeted, created_at);
```

**New Table: `x_bot_tweets`**
```sql
CREATE TABLE x_bot_tweets (
    id SERIAL PRIMARY KEY,
    tweet_id VARCHAR(255) UNIQUE,
    tweet_type VARCHAR(50),  -- 'trade_entry', 'trade_exit', 'analysis', 'reply', etc.
    content TEXT,
    related_trade_id INTEGER REFERENCES paper_trades(id),
    engagement_likes INTEGER DEFAULT 0,
    engagement_retweets INTEGER DEFAULT 0,
    engagement_replies INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_x_bot_tweets_type ON x_bot_tweets(tweet_type);
CREATE INDEX idx_x_bot_tweets_created ON x_bot_tweets(created_at DESC);
```

**New Table: `x_bot_target_accounts`**
```sql
CREATE TABLE x_bot_target_accounts (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    account_id VARCHAR(255),  -- X user ID for API calls
    category VARCHAR(100),  -- 'trader', 'analyst', 'defi', etc.
    last_replied_at TIMESTAMP,
    last_tweet_id VARCHAR(255),  -- Track last processed tweet
    reply_count INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_target_accounts_active ON x_bot_target_accounts(active, last_replied_at);
```

**New Table: `x_bot_state`**
```sql
CREATE TABLE x_bot_state (
    id SERIAL PRIMARY KEY,
    state_key VARCHAR(100) UNIQUE NOT NULL,
    state_value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Example state entries:
-- state_key: 'quota_reads_daily', state_value: {"count": 3, "date": "2025-10-04"}
-- state_key: 'quota_writes_daily', state_value: {"count": 12, "date": "2025-10-04"}
-- state_key: 'quota_reads_monthly', state_value: {"count": 87, "month": "2025-10"}
-- state_key: 'quota_writes_monthly', state_value: {"count": 245, "month": "2025-10"}

CREATE INDEX idx_x_bot_state_key ON x_bot_state(state_key);
```

**Migration Script:** `migrations/add_x_bot_tables.sql`
Will need to be run on Supabase to add these tables.

---

## Scheduling Strategy

### Using APScheduler (Already in ggbot.py)

Could integrate into existing orchestrator or run as separate service.

**Example Schedule:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Daily market analysis
scheduler.add_job(post_daily_analysis, 'cron', hour=9, minute=0)

# Weekly performance summary
scheduler.add_job(post_weekly_summary, 'cron', day_of_week='sun', hour=20, minute=0)

# Educational content (Mon, Wed, Fri at 2pm)
scheduler.add_job(post_educational_content, 'cron', day_of_week='mon,wed,fri', hour=14, minute=0)

# Targeted replies (3x per day)
scheduler.add_job(post_targeted_replies, 'cron', hour='9,14,20', minute=0)

# Trade monitoring (continuous, checks every minute)
scheduler.add_job(check_for_new_trades, 'interval', minutes=1)
```

### Alternative: Separate Bot Process

Run X bot as independent PM2 service:
```bash
pm2 start x_bot/bot.py --name x-bot
```

Communicates with main ggbot via:
- Shared Supabase database
- WebSocket notifications
- Direct function imports

---

## Rate Limiting & Safety

### Free Tier Constraints
- **100 reads/month** = 3.3 reads/day average
- **500 writes/month** = 16.6 writes/day average

### Proposed Daily Budget
| Activity | Reads | Writes | Frequency |
|----------|-------|--------|-----------|
| Targeted replies | 3 | 3 | 3x/day |
| Trade announcements | 0 | 5-10 | As needed |
| Daily analysis | 0 | 1 | 1x/day |
| Weekly summary | 0 | 1 | 1x/week |
| Educational content | 0 | 2-3 | 2-3x/week |
| **Daily Total** | **~3** | **~8-15** | |
| **Monthly Total** | **~90** | **~240-450** | |

**Buffer:** Leaves room for unexpected usage spikes

### Safety Mechanisms
1. **Pre-flight quota check** - Don't tweet if close to monthly limit
2. **Rate limit header monitoring** - Track X-Rate-Limit-* headers
3. **Exponential backoff** - Handle 429 errors gracefully
4. **Daily usage logging** - Track actual vs projected usage
5. **Emergency killswitch** - ENV var to disable bot if needed

---

## Next Steps

### Phase 1: Foundation ✅ **COMPLETE**
- [x] OAuth setup
- [x] Authentication test
- [x] Create X_BOT.md strategy doc
- [x] Build x_client.py wrapper (error handling, rate limits)
- [x] Integrate with APScheduler
- [x] Daily platform status tweet
- [x] Deploy as PM2 service
- [ ] User provides target accounts list (for future reply feature)
- [ ] Set up database tables (optional: x_bot_tweets tracking table)

### Phase 2: Future Enhancements (Planned)
- [ ] Implement LLM tweet generation (for trade announcements)
- [ ] Create trade announcement monitor (poll paper_trades table)
- [ ] Build targeted reply system (3x/day engagement)
- [ ] Weekly performance summary tweet
- [ ] Educational content rotation
- [ ] Add state management for quota tracking

### Phase 3: Advanced Features (Backlog)
- [ ] Dashboard for X bot metrics (tweets sent, engagement, quota usage)
- [ ] A/B testing tweet formats
- [ ] Engagement analytics (likes, retweets, replies via X API)
- [ ] Iterate on prompts based on performance
- [ ] Media attachments (charts/screenshots with tweets)

---

## Decisions Made

1. **Integration:** ✅ Separate PM2 service (isolates social media from trading operations)
2. **Initial Feature:** ✅ Platform status tweets (simple, no LLM needed, showcases real metrics)
3. **Voice/Tone:** ✅ Clean and professional (no hashtags, data-focused)
4. **Deployment:** ✅ Free tier sufficient for current usage (~90 reads, ~240 writes/month projected)

## Open Questions (Future Features)

1. **LLM Choice:** Which provider for trade announcement generation? (OpenAI vs DeepSeek)
2. **Trade Filtering:** What confidence threshold for trade announcements? (>70%? >80%?)
3. **Media:** Include charts/screenshots with tweets? (would need extra implementation)
4. **Reply Policy:** How aggressive with targeted replies? Risk of being flagged as spam?
5. **Upgrade Timing:** At what point is Basic tier ($200/mo) worth it? (if replies become priority)

---

## Resources

- [X API v2 Docs](https://docs.x.com/x-api/)
- [Tweepy Documentation](https://docs.tweepy.org/)
- Current credentials: `.env` (X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET, X_BEARER_TOKEN)
- Target accounts list: *TBD - user to provide*

---

**Last Updated:** 2025-10-04

---

## Summary: How Everything Works Together

### Data Flow Example: Trade Entry Tweet

1. **ggbot.py orchestrator** runs extraction → decision → trading pipeline
2. Decision agent returns "BUY" signal with 85% confidence
3. Trading agent executes paper trade
4. Trade written to `paper_trades` table with `tweeted = false`
5. **X bot (running separately)** polls every 60 seconds
6. Finds new untweeted trade
7. Generates tweet via LLM: "📈 LONG $BTC @ $67,245 | Confidence: 85% | RSI oversold + bullish divergence"
8. Posts to X API → receives tweet_id
9. Updates `paper_trades`: `tweeted = true, tweet_id = '1234567890'`
10. Logs to `x_bot_tweets` table
11. Trade announcement live on @ggbots_ai

**Total latency:** <2 minutes from trade execution to tweet

### Operational Independence

- **ggbot.py crash:** X bot continues scheduled tweets, no trade announcements until ggbot recovers
- **X bot crash:** Trading continues normally, tweets queued in database (will post when X bot restarts)
- **Database down:** Both services fail (shared dependency)
- **X API down:** X bot handles gracefully, retries with exponential backoff

### Development Workflow

1. Make changes to X bot code (`x_bot/`)
2. Test locally: `python x_bot/bot.py`
3. Deploy: `pm2 restart x-bot`
4. Monitor: `pm2 logs x-bot`
5. Check database: `SELECT * FROM x_bot_tweets ORDER BY created_at DESC LIMIT 10`
6. Verify on X: Check @ggbots_ai timeline

**No need to touch ggbot.py at all** (unless adding new data fields to tweet)

---

**Last Updated:** 2025-10-04 (✅ Phase 1 complete - X bot deployed to production)
