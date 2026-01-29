---
name: Supabase Database Query
description: Query the ggbots Supabase PostgreSQL database for bot configurations, trading performance, positions, and analytics. Use when analyzing bot performance, debugging issues, checking user data, or generating reports. Works with tables like configurations, paper_accounts, paper_trades, and decisions.
allowed-tools: Bash
---

# Supabase Database Query

Query the production ggbots Supabase database using the existing connection infrastructure. This Skill provides safe, read-heavy database access for analytics, debugging, and monitoring.

## Quick Start

All database queries should use the existing `core.common.db.get_db_connection()` context manager:

```python
from core.common.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM configurations WHERE user_id = %s", (user_id,))
        results = cur.fetchall()
```

## Execution Methods

### ✅ RECOMMENDED: Heredoc Syntax (Best for complex queries)

**USE THIS METHOD** for queries with f-strings, formatting, or multiple lines:

```bash
source .venv/bin/activate && python3 <<'EOF'
from core.common.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM configurations')
        count = cur.fetchone()[0]
        print(f"Total bots: {count}")  # F-strings work perfectly!
EOF
```

**Why heredoc?**
- ✅ No shell escaping issues with `{}` or quotes
- ✅ F-strings work without errors
- ✅ Multi-line code is readable
- ✅ Complex formatting just works

### ⚠️ AVOID: Inline python3 -c (Causes escaping issues)

**DO NOT USE** for complex queries:

```bash
# ❌ WRONG - Will fail with f-strings
python3 -c "print(f'{'value':<10}')"  # SyntaxError or bad substitution

# ⚠️ OK for simple queries only (no f-strings, no complex formatting)
python3 -c "from core.common.db import get_db_connection; print('simple')"
```

**Why avoid?**
- ❌ Bash expands `{}` as shell variables before Python sees them
- ❌ Nested quotes cause escaping nightmares
- ❌ F-strings break with "bad substitution" errors

### 🔧 FALLBACK: Temporary Python Script

For very complex queries, create a temporary file:

```bash
cat > /tmp/query.py <<'EOF'
from core.common.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM configurations LIMIT 5')
        for row in cur.fetchall():
            print(f"Config: {row[0]}")
EOF

source .venv/bin/activate && python /tmp/query.py
rm /tmp/query.py
```

## Database Schema

### Core Tables

#### **configurations** - Bot configurations
```
config_id         uuid         PRIMARY KEY
user_id           uuid         NOT NULL
config_type       varchar      NOT NULL
config_name       varchar      Nullable (display name)
config_data       jsonb        NOT NULL (bot settings)
state             text         NOT NULL ('active' | 'inactive')
created_at        timestamp
updated_at        timestamp
```

**config_data structure**: `{trading, decision, extraction, llm_config, selected_pair, schema_version, telegram_integration}`

#### **paper_accounts** - Paper trading accounts (1 per config_id)
```
account_id        uuid         PRIMARY KEY
config_id         uuid         UNIQUE, FK to configurations
user_id           uuid         NOT NULL
initial_balance   numeric      Default 10000.00
current_balance   numeric      Current USD balance
total_pnl         numeric      Cumulative P&L
open_positions    integer      Count of open trades
total_trades      integer      Total trade count
win_trades        integer      Winning trades count
loss_trades       integer      Losing trades count
last_reset_at     timestamp    Last account reset
created_at        timestamp
updated_at        timestamp
```

#### **paper_trades** - Individual paper trades
```
trade_id          uuid         PRIMARY KEY
account_id        uuid         FK to paper_accounts
config_id         uuid         FK to configurations
user_id           uuid         NOT NULL
decision_id       uuid         Nullable, links to decisions
symbol            varchar      e.g., 'BTC/USDT'
side              varchar      'long' | 'short'
entry_price       numeric      Entry price
current_price     numeric      Current/last price
size_usd          numeric      Position size in USD
leverage          integer      1-100
unrealized_pnl    numeric      Live P&L (if open)
realized_pnl      numeric      Final P&L (if closed)
status            varchar      'open' | 'closed'
stop_loss         numeric      SL price
take_profit       numeric      TP price
confidence_score  numeric      0.0-1.0 from decision
margin_used       numeric      Margin locked
liquidation_price numeric      Auto-liquidation price
opened_at         timestamp
closed_at         timestamp    Nullable
close_reason      varchar      'take_profit' | 'stop_loss' | 'manual' | 'liquidation'
```

#### **decisions** - AI decision audit trail
```
decision_id       uuid         PRIMARY KEY
user_id           uuid         NOT NULL
config_id         uuid         Nullable
symbol            varchar      Trading pair
action            varchar      'long' | 'short' | 'exit' | 'wait'
status            varchar      Decision status
confidence        numeric      0.0-1.0
reasoning         text         LLM explanation
prompt            text         Full prompt sent to LLM
decision_data     jsonb        Additional metadata
parent_decision_id uuid        For trade management decisions
created_at        timestamp
```

#### **user_profiles** - User metadata
```
user_id           uuid         PRIMARY KEY
email             varchar      User email
subscription_tier varchar      'free' | 'prepaid' | 'usage_based' | 'pro'
subscription_expires_at timestamp Nullable
created_at        timestamp
```

## Common Query Patterns

### 1. Bot Performance Analysis

**Top performing bots by win rate**:
```python
cur.execute("""
    SELECT
        c.config_name,
        c.config_id,
        pa.total_trades,
        pa.win_trades,
        ROUND((pa.win_trades::numeric / NULLIF(pa.total_trades, 0)) * 100, 2) as win_rate,
        pa.total_pnl
    FROM paper_accounts pa
    JOIN configurations c ON pa.config_id = c.config_id
    WHERE pa.total_trades >= 5  -- Minimum trades for significance
    ORDER BY win_rate DESC
    LIMIT 10
""")
```

**Active bots by user**:
```python
cur.execute("""
    SELECT user_id, COUNT(*) as active_bots
    FROM configurations
    WHERE state = 'active'
    GROUP BY user_id
    ORDER BY active_bots DESC
""")
```

### 2. Trading Analytics

**Open positions summary**:
```python
cur.execute("""
    SELECT
        symbol,
        side,
        COUNT(*) as position_count,
        SUM(size_usd) as total_exposure,
        AVG(confidence_score) as avg_confidence
    FROM paper_trades
    WHERE status = 'open'
    GROUP BY symbol, side
    ORDER BY total_exposure DESC
""")
```

**Recent closed trades with P&L**:
```python
cur.execute("""
    SELECT
        t.symbol,
        t.side,
        t.entry_price,
        t.current_price as exit_price,
        t.realized_pnl,
        t.close_reason,
        t.opened_at,
        t.closed_at,
        c.config_name
    FROM paper_trades t
    JOIN configurations c ON t.config_id = c.config_id
    WHERE t.status = 'closed'
    ORDER BY t.closed_at DESC
    LIMIT 20
""")
```

### 3. Decision Analysis

**Recent decisions by action type**:
```python
cur.execute("""
    SELECT
        action,
        COUNT(*) as count,
        AVG(confidence) as avg_confidence
    FROM decisions
    WHERE created_at > NOW() - INTERVAL '24 hours'
    GROUP BY action
    ORDER BY count DESC
""")
```

**Decision → Trade correlation**:
```python
cur.execute("""
    SELECT
        d.decision_id,
        d.symbol,
        d.action,
        d.confidence,
        t.trade_id,
        t.status,
        t.realized_pnl
    FROM decisions d
    LEFT JOIN paper_trades t ON d.decision_id = t.decision_id
    WHERE d.created_at > NOW() - INTERVAL '7 days'
    AND d.action IN ('long', 'short')
    ORDER BY d.created_at DESC
""")
```

### 4. User & Subscription Queries

**User subscription tiers**:
```python
cur.execute("""
    SELECT
        subscription_tier,
        COUNT(*) as user_count,
        COUNT(CASE WHEN subscription_expires_at > NOW() THEN 1 END) as active_subs
    FROM user_profiles
    GROUP BY subscription_tier
""")
```

**Active users with bot count**:
```python
cur.execute("""
    SELECT
        u.email,
        u.subscription_tier,
        COUNT(CASE WHEN c.state = 'active' THEN 1 END) as active_bots,
        COUNT(c.config_id) as total_bots
    FROM user_profiles u
    LEFT JOIN configurations c ON u.user_id = c.user_id
    GROUP BY u.user_id, u.email, u.subscription_tier
    ORDER BY active_bots DESC
""")
```

## Best Practices

### ✅ DO

1. **Always use the connection context manager**
   ```python
   with get_db_connection() as conn:
       with conn.cursor() as cur:
           # queries here
   ```

2. **Use parameterized queries to prevent SQL injection**
   ```python
   cur.execute("SELECT * FROM configurations WHERE user_id = %s", (user_id,))
   ```

3. **Filter by user_id for security**
   ```python
   # When querying user-specific data
   cur.execute("SELECT * FROM paper_trades WHERE user_id = %s", (user_id,))
   ```

4. **Use JSONB operators for config_data**
   ```python
   # Access nested JSON fields
   cur.execute("""
       SELECT config_id, config_data->>'selected_pair' as symbol
       FROM configurations
       WHERE config_data->>'selected_pair' = %s
   """, ('BTC/USDT',))
   ```

5. **Handle NULL values**
   ```python
   # Use NULLIF to avoid division by zero
   ROUND((win_trades::numeric / NULLIF(total_trades, 0)) * 100, 2) as win_rate
   ```

### ❌ DON'T

1. **Don't use string formatting for queries** (SQL injection risk)
   ```python
   # ❌ WRONG
   cur.execute(f"SELECT * FROM configurations WHERE user_id = '{user_id}'")

   # ✅ CORRECT
   cur.execute("SELECT * FROM configurations WHERE user_id = %s", (user_id,))
   ```

2. **Don't forget to commit for write operations**
   ```python
   # For INSERT/UPDATE/DELETE
   cur.execute("UPDATE configurations SET state = 'inactive' WHERE config_id = %s", (config_id,))
   conn.commit()  # Important!
   ```

3. **Don't query without limits on large tables**
   ```python
   # ❌ Can return millions of rows
   cur.execute("SELECT * FROM paper_trades")

   # ✅ Add LIMIT
   cur.execute("SELECT * FROM paper_trades LIMIT 100")
   ```

4. **Don't forget timezone handling**
   ```python
   # Use NOW() for current time in UTC
   # Timestamps are stored as 'timestamp with time zone'
   ```

## Error Handling

```python
from core.common.db import get_db_connection
from core.common.logger import logger

try:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM configurations WHERE user_id = %s", (user_id,))
            results = cur.fetchall()
except Exception as e:
    logger.error(f"Database query failed: {e}")
    # Handle error appropriately
```

## Useful Aggregations

**Platform-wide stats**:
```python
cur.execute("""
    SELECT
        (SELECT COUNT(*) FROM configurations WHERE state = 'active') as active_bots,
        (SELECT COUNT(DISTINCT user_id) FROM configurations) as total_users,
        (SELECT SUM(total_trades) FROM paper_accounts) as total_trades,
        (SELECT COUNT(*) FROM paper_trades WHERE status = 'open') as open_positions,
        (SELECT SUM(total_pnl) FROM paper_accounts) as total_pnl
""")
```

**Symbol popularity**:
```python
cur.execute("""
    SELECT
        config_data->>'selected_pair' as symbol,
        COUNT(*) as bot_count,
        COUNT(CASE WHEN state = 'active' THEN 1 END) as active_count
    FROM configurations
    WHERE config_data->>'selected_pair' IS NOT NULL
    GROUP BY symbol
    ORDER BY active_count DESC, bot_count DESC
    LIMIT 20
""")
```

## Practical Example: Complete Query with Heredoc

Here's a complete working example showing how to query profitable bots using heredoc syntax:

```bash
source .venv/bin/activate && python3 <<'EOF'
from core.common.db import get_db_connection

print('=== TOP PROFITABLE BOTS ===\n')

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                c.config_name,
                c.config_data->>'selected_pair' as symbol,
                pa.total_trades,
                pa.win_trades,
                ROUND((pa.win_trades::numeric / NULLIF(pa.total_trades, 0)) * 100, 2) as win_rate,
                ROUND(pa.total_pnl, 2) as total_pnl
            FROM paper_accounts pa
            JOIN configurations c ON pa.config_id = c.config_id
            WHERE pa.total_trades >= 5
            ORDER BY pa.total_pnl DESC
            LIMIT 10
        """)

        print(f"{'Bot Name':<30} {'Symbol':<12} {'Trades':<8} {'Win Rate':<10} {'P&L':<12}")
        print("-" * 85)

        for row in cur.fetchall():
            name = (row[0] or 'Unnamed')[:28]
            symbol = row[1] or 'N/A'
            win_rate = f"{row[4]:.1f}%" if row[4] else "N/A"
            pnl = float(row[5]) if row[5] else 0
            print(f"{name:<30} {symbol:<12} {row[2]:<8} {win_rate:<10} ${pnl:<11.2f}")
EOF
```

**This example demonstrates**:
- ✅ Heredoc syntax preventing shell escaping issues
- ✅ F-strings for formatted output
- ✅ JOIN queries across multiple tables
- ✅ JSONB field access with `->>` operator
- ✅ Parameterized queries with NULLIF for safe division
- ✅ Proper context manager usage

## Integration with Existing Code

The Skill uses the same connection method as the rest of the codebase:

- `core/common/db.py` - Connection infrastructure
- `trading/paper/supabase_service.py` - Paper trading service
- `core/config/repository.py` - Configuration management
- `extraction/v2/supabase_storage.py` - Market data storage

All queries go through the same PostgreSQL connection pool configured via `DATABASE_URL` or `SUPABASE_*` environment variables.

## Examples

See [QUERY_EXAMPLES.md](QUERY_EXAMPLES.md) for more comprehensive examples.
