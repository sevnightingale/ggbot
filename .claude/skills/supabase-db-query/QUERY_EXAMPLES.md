# Supabase Database Query Examples

Comprehensive examples for common ggbots database queries. All examples use `core.common.db.get_db_connection()`.

## Performance Analysis

### Bot Win Rate Leaderboard

Find the best performing bots by win rate (minimum 10 trades):

```python
from core.common.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                c.config_name,
                c.config_id,
                c.config_data->>'selected_pair' as symbol,
                pa.total_trades,
                pa.win_trades,
                pa.loss_trades,
                ROUND((pa.win_trades::numeric / NULLIF(pa.total_trades, 0)) * 100, 2) as win_rate_pct,
                ROUND(pa.total_pnl, 2) as total_pnl,
                ROUND(pa.total_pnl / NULLIF(pa.total_trades, 0), 2) as avg_pnl_per_trade
            FROM paper_accounts pa
            JOIN configurations c ON pa.config_id = c.config_id
            WHERE pa.total_trades >= 10
            ORDER BY win_rate_pct DESC, total_pnl DESC
            LIMIT 20
        """)

        print("Top Performing Bots:")
        print(f"{'Name':<30} {'Symbol':<12} {'Trades':<8} {'Win Rate':<10} {'Total P&L':<12} {'Avg/Trade':<10}")
        print("-" * 100)

        for row in cur.fetchall():
            name = row[0] or "Unnamed"
            symbol = row[2] or "N/A"
            print(f"{name:<30} {symbol:<12} {row[3]:<8} {row[6]}%{'':<6} ${row[7]:<11} ${row[8]}")
```

### User Performance Summary

Get trading performance for a specific user:

```python
user_id = "your-user-uuid-here"

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(DISTINCT c.config_id) as total_bots,
                COUNT(DISTINCT CASE WHEN c.state = 'active' THEN c.config_id END) as active_bots,
                COALESCE(SUM(pa.total_trades), 0) as total_trades,
                COALESCE(SUM(pa.win_trades), 0) as total_wins,
                COALESCE(SUM(pa.total_pnl), 0) as total_pnl,
                COUNT(DISTINCT CASE WHEN pt.status = 'open' THEN pt.trade_id END) as open_positions
            FROM configurations c
            LEFT JOIN paper_accounts pa ON c.config_id = pa.config_id
            LEFT JOIN paper_trades pt ON c.config_id = pt.config_id AND pt.status = 'open'
            WHERE c.user_id = %s
        """, (user_id,))

        result = cur.fetchone()
        print(f"User Performance Summary:")
        print(f"  Total Bots: {result[0]}")
        print(f"  Active Bots: {result[1]}")
        print(f"  Total Trades: {result[2]}")
        print(f"  Win Trades: {result[3]}")
        print(f"  Win Rate: {(result[3]/result[2]*100 if result[2] > 0 else 0):.2f}%")
        print(f"  Total P&L: ${result[4]:.2f}")
        print(f"  Open Positions: {result[5]}")
```

## Trading Position Analysis

### Current Open Positions

View all currently open positions across the platform:

```python
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                pt.symbol,
                pt.side,
                pt.entry_price,
                pt.current_price,
                pt.size_usd,
                pt.leverage,
                pt.unrealized_pnl,
                pt.stop_loss,
                pt.take_profit,
                pt.confidence_score,
                pt.opened_at,
                c.config_name,
                EXTRACT(EPOCH FROM (NOW() - pt.opened_at))/3600 as hours_open
            FROM paper_trades pt
            JOIN configurations c ON pt.config_id = c.config_id
            WHERE pt.status = 'open'
            ORDER BY pt.opened_at DESC
            LIMIT 50
        """)

        print("Currently Open Positions:")
        for row in cur.fetchall():
            pnl = float(row[6]) if row[6] else 0
            pnl_color = "+" if pnl >= 0 else ""
            print(f"{row[0]:<12} {row[1]:<6} Entry: ${row[2]:>10.2f} Current: ${row[3]:>10.2f} "
                  f"P&L: {pnl_color}${pnl:>8.2f} Size: ${row[4]:>10.2f} "
                  f"Leverage: {row[5]}x Open: {row[12]:.1f}h")
```

### Position Risk Analysis

Identify high-risk positions (high leverage, close to stop loss, or large size):

```python
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                pt.symbol,
                pt.side,
                pt.leverage,
                pt.size_usd,
                pt.entry_price,
                pt.current_price,
                pt.stop_loss,
                pt.unrealized_pnl,
                pt.liquidation_price,
                c.config_name,
                -- Distance to stop loss as percentage
                CASE
                    WHEN pt.side = 'long' AND pt.stop_loss IS NOT NULL THEN
                        ROUND(((pt.current_price - pt.stop_loss) / pt.current_price) * 100, 2)
                    WHEN pt.side = 'short' AND pt.stop_loss IS NOT NULL THEN
                        ROUND(((pt.stop_loss - pt.current_price) / pt.current_price) * 100, 2)
                    ELSE NULL
                END as distance_to_sl_pct
            FROM paper_trades pt
            JOIN configurations c ON pt.config_id = c.config_id
            WHERE pt.status = 'open'
            AND (
                pt.leverage > 10  -- High leverage
                OR pt.size_usd > 5000  -- Large position
                OR ABS(pt.unrealized_pnl) > 100  -- Significant unrealized P&L
            )
            ORDER BY pt.leverage DESC, pt.size_usd DESC
        """)

        print("High Risk Positions:")
        for row in cur.fetchall():
            print(f"{row[0]} {row[1]} | Leverage: {row[2]}x | Size: ${row[3]:.2f} | "
                  f"P&L: ${float(row[7]) if row[7] else 0:.2f} | "
                  f"Distance to SL: {row[10]:.2f}% | Bot: {row[9]}")
```

## Decision & Trade Correlation

### Execution Rate Analysis

See how many decisions actually result in trades:

```python
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                d.action,
                COUNT(DISTINCT d.decision_id) as total_decisions,
                COUNT(DISTINCT t.trade_id) as executed_trades,
                ROUND((COUNT(DISTINCT t.trade_id)::numeric / NULLIF(COUNT(DISTINCT d.decision_id), 0)) * 100, 2) as execution_rate,
                AVG(d.confidence) as avg_confidence
            FROM decisions d
            LEFT JOIN paper_trades t ON d.decision_id = t.decision_id
            WHERE d.created_at > NOW() - INTERVAL '7 days'
            AND d.action IN ('long', 'short', 'exit')
            GROUP BY d.action
            ORDER BY total_decisions DESC
        """)

        print("Decision Execution Rates (Last 7 Days):")
        print(f"{'Action':<10} {'Decisions':<12} {'Executed':<12} {'Exec Rate':<12} {'Avg Confidence':<15}")
        print("-" * 70)

        for row in cur.fetchall():
            print(f"{row[0]:<10} {row[1]:<12} {row[2]:<12} {row[3]}%{'':<8} {float(row[4]):.2f}")
```

### Confidence vs Performance

Analyze if higher confidence decisions lead to better outcomes:

```python
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                CASE
                    WHEN d.confidence >= 0.8 THEN 'High (0.8-1.0)'
                    WHEN d.confidence >= 0.6 THEN 'Medium (0.6-0.8)'
                    ELSE 'Low (0.0-0.6)'
                END as confidence_bucket,
                COUNT(*) as trade_count,
                SUM(CASE WHEN t.realized_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                ROUND((SUM(CASE WHEN t.realized_pnl > 0 THEN 1 ELSE 0 END)::numeric / COUNT(*)) * 100, 2) as win_rate,
                ROUND(AVG(t.realized_pnl), 2) as avg_pnl,
                ROUND(SUM(t.realized_pnl), 2) as total_pnl
            FROM paper_trades t
            JOIN decisions d ON t.decision_id = d.decision_id
            WHERE t.status = 'closed'
            AND t.realized_pnl IS NOT NULL
            GROUP BY confidence_bucket
            ORDER BY
                CASE confidence_bucket
                    WHEN 'High (0.8-1.0)' THEN 1
                    WHEN 'Medium (0.6-0.8)' THEN 2
                    ELSE 3
                END
        """)

        print("Confidence vs Performance:")
        for row in cur.fetchall():
            print(f"{row[0]:<20} Trades: {row[1]:<6} Win Rate: {row[3]}% "
                  f"Avg P&L: ${row[4]} Total: ${row[5]}")
```

## Symbol & Market Analysis

### Most Traded Symbols

Find which symbols are most actively traded:

```python
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                symbol,
                COUNT(*) as total_trades,
                SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_positions,
                SUM(CASE WHEN status = 'closed' AND realized_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                ROUND((SUM(CASE WHEN status = 'closed' AND realized_pnl > 0 THEN 1 ELSE 0 END)::numeric /
                       NULLIF(SUM(CASE WHEN status = 'closed' THEN 1 END), 0)) * 100, 2) as win_rate,
                ROUND(SUM(CASE WHEN status = 'closed' THEN realized_pnl ELSE 0 END), 2) as total_pnl
            FROM paper_trades
            GROUP BY symbol
            ORDER BY total_trades DESC
            LIMIT 20
        """)

        print("Most Traded Symbols:")
        print(f"{'Symbol':<12} {'Total':<8} {'Open':<8} {'Win Rate':<12} {'Total P&L':<12}")
        print("-" * 60)

        for row in cur.fetchall():
            print(f"{row[0]:<12} {row[1]:<8} {row[2]:<8} {row[4]}%{'':<8} ${row[5]}")
```

### Long vs Short Performance by Symbol

Compare long vs short performance for top symbols:

```python
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                symbol,
                side,
                COUNT(*) as trades,
                ROUND(AVG(realized_pnl), 2) as avg_pnl,
                ROUND(SUM(realized_pnl), 2) as total_pnl,
                ROUND((SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END)::numeric / COUNT(*)) * 100, 2) as win_rate
            FROM paper_trades
            WHERE status = 'closed'
            AND symbol IN (
                SELECT symbol
                FROM paper_trades
                GROUP BY symbol
                ORDER BY COUNT(*) DESC
                LIMIT 5
            )
            GROUP BY symbol, side
            ORDER BY symbol, side
        """)

        print("Long vs Short Performance (Top 5 Symbols):")
        current_symbol = None
        for row in cur.fetchall():
            if row[0] != current_symbol:
                if current_symbol is not None:
                    print()
                current_symbol = row[0]
                print(f"\n{row[0]}:")

            print(f"  {row[1].upper():<6} Trades: {row[2]:<6} Win Rate: {row[5]}% "
                  f"Avg: ${row[3]} Total: ${row[4]}")
```

## User & Subscription Queries

### Active Users by Subscription Tier

```python
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                COALESCE(subscription_tier, 'unknown') as tier,
                COUNT(*) as user_count,
                COUNT(CASE WHEN subscription_expires_at > NOW() OR subscription_tier = 'prepaid' THEN 1 END) as active_subscribers,
                SUM((
                    SELECT COUNT(*)
                    FROM configurations c
                    WHERE c.user_id = user_profiles.user_id
                    AND c.state = 'active'
                )) as total_active_bots
            FROM user_profiles
            GROUP BY tier
            ORDER BY user_count DESC
        """)

        print("Users by Subscription Tier:")
        for row in cur.fetchall():
            print(f"{row[0]:<15} Users: {row[1]:<6} Active Subs: {row[2]:<6} Active Bots: {row[3] or 0}")
```

## Time-Based Analysis

### Trading Activity by Hour

See when trades are most active:

```python
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                EXTRACT(HOUR FROM opened_at) as hour,
                COUNT(*) as trades_opened,
                ROUND(AVG(confidence_score), 2) as avg_confidence
            FROM paper_trades
            WHERE opened_at > NOW() - INTERVAL '7 days'
            GROUP BY hour
            ORDER BY hour
        """)

        print("Trading Activity by Hour (Last 7 Days):")
        for row in cur.fetchall():
            hour = int(row[0])
            count = row[1]
            bar = "█" * (count // 10)  # Visual bar chart
            print(f"{hour:02d}:00 | {bar} ({count} trades, avg conf: {row[2]})")
```

### Daily Performance Trends

```python
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                DATE(closed_at) as trade_date,
                COUNT(*) as trades_closed,
                SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
                ROUND((SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END)::numeric / COUNT(*)) * 100, 2) as win_rate,
                ROUND(SUM(realized_pnl), 2) as daily_pnl
            FROM paper_trades
            WHERE status = 'closed'
            AND closed_at > NOW() - INTERVAL '30 days'
            GROUP BY DATE(closed_at)
            ORDER BY trade_date DESC
            LIMIT 30
        """)

        print("Daily Performance (Last 30 Days):")
        print(f"{'Date':<12} {'Trades':<8} {'Wins':<6} {'Win Rate':<10} {'Daily P&L':<12}")
        print("-" * 60)

        for row in cur.fetchall():
            print(f"{row[0]}{'':<4} {row[1]:<8} {row[2]:<6} {row[3]}%{'':<6} ${row[4]}")
```

## Configuration Analysis

### Bot Configuration Distribution

See what LLM providers and timeframes are most popular:

```python
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                config_data->'llm_config'->>'provider' as llm_provider,
                config_data->'extraction'->>'timeframe' as timeframe,
                COUNT(*) as bot_count,
                COUNT(CASE WHEN state = 'active' THEN 1 END) as active_count
            FROM configurations
            WHERE config_data IS NOT NULL
            GROUP BY llm_provider, timeframe
            ORDER BY bot_count DESC
            LIMIT 20
        """)

        print("Bot Configuration Popularity:")
        print(f"{'LLM Provider':<20} {'Timeframe':<12} {'Total':<8} {'Active':<8}")
        print("-" * 60)

        for row in cur.fetchall():
            provider = row[0] or "default"
            timeframe = row[1] or "N/A"
            print(f"{provider:<20} {timeframe:<12} {row[2]:<8} {row[3]:<8}")
```

## Export Data for Analysis

Save query results to CSV for external analysis:

```python
import csv
from core.common.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                t.trade_id,
                t.symbol,
                t.side,
                t.entry_price,
                t.current_price,
                t.size_usd,
                t.leverage,
                t.realized_pnl,
                t.opened_at,
                t.closed_at,
                t.close_reason,
                d.confidence,
                d.action
            FROM paper_trades t
            LEFT JOIN decisions d ON t.decision_id = d.decision_id
            WHERE t.status = 'closed'
            AND t.closed_at > NOW() - INTERVAL '30 days'
            ORDER BY t.closed_at DESC
        """)

        # Write to CSV
        with open('trades_export.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['trade_id', 'symbol', 'side', 'entry_price', 'exit_price',
                           'size_usd', 'leverage', 'pnl', 'opened_at', 'closed_at',
                           'close_reason', 'confidence', 'decision_action'])
            writer.writerows(cur.fetchall())

        print(f"Exported {cur.rowcount} trades to trades_export.csv")
```
