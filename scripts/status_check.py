#!/usr/bin/env python3
"""
Comprehensive platform status check script for ggbots.
Queries Supabase database for metrics to update ACTIVE.md.

Usage:
    python scripts/status_check.py              # Display status only
    python scripts/status_check.py --update     # Update ACTIVE.md header
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.common.db import get_db_connection


def get_business_metrics():
    """Query database for business/investor metrics: revenue, funnel, engagement, LTV."""
    metrics = {}

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # ----- REVENUE: monthly breakdown -----
            cur.execute("""
                SELECT
                    TO_CHAR(created_at, 'YYYY-MM') as month,
                    COUNT(*) as llm_calls,
                    ROUND(COALESCE(SUM(platform_cost_usd), 0)::numeric, 2) as revenue,
                    ROUND(COALESCE(SUM(provider_cost_usd), 0)::numeric, 2) as cost,
                    COUNT(DISTINCT user_id) as paying_users
                FROM activities
                WHERE platform_cost_usd IS NOT NULL AND platform_cost_usd > 0
                GROUP BY month
                ORDER BY month
            """)
            monthly = []
            total_revenue = 0
            total_cost = 0
            for row in cur.fetchall():
                rev = float(row[2] or 0)
                cost = float(row[3] or 0)
                total_revenue += rev
                total_cost += cost
                monthly.append({
                    'month': row[0], 'llm_calls': row[1],
                    'revenue': rev, 'cost': cost,
                    'margin': round(rev - cost, 2), 'paying_users': row[4]
                })
            metrics['revenue_monthly'] = monthly
            metrics['revenue_total'] = round(total_revenue, 2)
            metrics['cost_total'] = round(total_cost, 2)
            metrics['margin_total'] = round(total_revenue - total_cost, 2)
            metrics['margin_pct'] = round((total_revenue - total_cost) / total_revenue * 100, 1) if total_revenue > 0 else 0

            # Revenue MTD + projected
            cur.execute("""
                SELECT
                    ROUND(COALESCE(SUM(platform_cost_usd), 0)::numeric, 2) as mtd_rev,
                    COUNT(DISTINCT user_id) as mtd_users,
                    EXTRACT(day FROM NOW()) as days_elapsed
                FROM activities
                WHERE platform_cost_usd > 0
                AND created_at >= DATE_TRUNC('month', NOW())
            """)
            row = cur.fetchone()
            mtd_rev = float(row[0] or 0)
            days_elapsed = max(float(row[1] or 1), 1)
            days_in_month = float(row[2] or 1)
            metrics['revenue_mtd'] = mtd_rev
            metrics['revenue_projected'] = round(mtd_rev / max(days_in_month, 1) * 30, 2)
            metrics['mtd_paying_users'] = int(row[1] or 0)

            # Last 30d revenue (MRR proxy)
            cur.execute("""
                SELECT
                    ROUND(COALESCE(SUM(platform_cost_usd), 0)::numeric, 2),
                    COUNT(DISTINCT user_id)
                FROM activities
                WHERE platform_cost_usd > 0
                AND created_at > NOW() - INTERVAL '30 days'
            """)
            row = cur.fetchone()
            metrics['revenue_30d'] = float(row[0] or 0)
            metrics['paying_users_30d'] = row[1] or 0

            # ----- CONVERSION FUNNEL -----
            cur.execute("""
                SELECT
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN user_id IN (
                        SELECT DISTINCT user_id FROM configurations
                    ) THEN 1 END) as created_bot,
                    COUNT(CASE WHEN user_id IN (
                        SELECT DISTINCT user_id FROM configurations WHERE state = 'active'
                    ) THEN 1 END) as active_bot,
                    COUNT(CASE WHEN user_id IN (
                        SELECT DISTINCT user_id FROM decisions
                    ) THEN 1 END) as ran_bot,
                    COUNT(CASE WHEN subscription_tier IN ('prepaid', 'usage_based', 'pro') THEN 1 END) as paid
                FROM user_profiles
            """)
            row = cur.fetchone()
            total = row[0] or 1
            metrics['funnel'] = {
                'total_users': row[0],
                'created_bot': row[1], 'created_bot_pct': round(row[1] / total * 100, 1),
                'active_bot': row[2], 'active_bot_pct': round(row[2] / total * 100, 1),
                'ran_bot': row[3], 'ran_bot_pct': round(row[3] / total * 100, 1),
                'paid': row[4], 'paid_pct': round(row[4] / total * 100, 1),
            }

            # ----- COHORT CONVERSION: post-monetization (Jan 2026+) -----
            cur.execute("""
                SELECT
                    TO_CHAR(u.created_at, 'YYYY-MM') as month,
                    COUNT(*) as signups,
                    COUNT(CASE WHEN u.subscription_tier IN ('prepaid', 'usage_based', 'pro') THEN 1 END) as paid
                FROM user_profiles u
                WHERE u.created_at >= '2026-01-01'
                GROUP BY month
                ORDER BY month
            """)
            cohorts = []
            total_signups_post = 0
            total_paid_post = 0
            for row in cur.fetchall():
                signups = row[1]
                paid = row[2]
                total_signups_post += signups
                total_paid_post += paid
                cohorts.append({
                    'month': row[0], 'signups': signups, 'paid': paid,
                    'conversion_pct': round(paid / signups * 100, 1) if signups > 0 else 0
                })
            metrics['cohorts'] = cohorts
            metrics['post_monetization_signups'] = total_signups_post
            metrics['post_monetization_paid'] = total_paid_post
            metrics['post_monetization_conversion_pct'] = round(
                total_paid_post / total_signups_post * 100, 1
            ) if total_signups_post > 0 else 0

            # ----- ENGAGEMENT: DAU/WAU/MAU -----
            cur.execute("""
                SELECT
                    COUNT(DISTINCT CASE
                        WHEN d.created_at > NOW() - INTERVAL '1 day' THEN d.user_id END) as dau,
                    COUNT(DISTINCT CASE
                        WHEN d.created_at > NOW() - INTERVAL '7 days' THEN d.user_id END) as wau,
                    COUNT(DISTINCT CASE
                        WHEN d.created_at > NOW() - INTERVAL '30 days' THEN d.user_id END) as mau
                FROM decisions d
            """)
            row = cur.fetchone()
            dau, wau, mau = row[0], row[1], row[2]
            metrics['engagement'] = {
                'dau': dau, 'wau': wau, 'mau': mau,
                'dau_wau_pct': round(dau / wau * 100, 1) if wau > 0 else 0,
                'dau_mau_pct': round(dau / mau * 100, 1) if mau > 0 else 0,
            }

            # ----- RETENTION: users signed up 30+ days ago -----
            cur.execute("""
                WITH old_users AS (
                    SELECT user_id FROM user_profiles
                    WHERE created_at < NOW() - INTERVAL '30 days'
                )
                SELECT
                    COUNT(*) as cohort_size,
                    COUNT(CASE WHEN ou.user_id IN (
                        SELECT DISTINCT user_id FROM decisions
                        WHERE created_at > NOW() - INTERVAL '7 days'
                    ) THEN 1 END) as active_7d,
                    COUNT(CASE WHEN ou.user_id IN (
                        SELECT DISTINCT user_id FROM decisions
                        WHERE created_at > NOW() - INTERVAL '30 days'
                    ) THEN 1 END) as active_30d
                FROM old_users ou
            """)
            row = cur.fetchone()
            cohort_size = row[0] or 1
            metrics['retention'] = {
                'cohort_size': row[0],
                'active_7d': row[1], 'active_7d_pct': round(row[1] / cohort_size * 100, 1),
                'active_30d': row[2], 'active_30d_pct': round(row[2] / cohort_size * 100, 1),
            }

            # ----- LTV by tier -----
            cur.execute("""
                SELECT
                    u.subscription_tier,
                    COUNT(DISTINCT u.user_id) as users,
                    ROUND(COALESCE(SUM(user_totals.user_total), 0)::numeric, 2) as total_revenue,
                    ROUND(COALESCE(AVG(user_totals.user_total), 0)::numeric, 2) as avg_ltv,
                    ROUND(COALESCE(MAX(user_totals.user_total), 0)::numeric, 2) as max_ltv
                FROM user_profiles u
                LEFT JOIN LATERAL (
                    SELECT COALESCE(SUM(platform_cost_usd), 0) as user_total
                    FROM activities
                    WHERE user_id = u.user_id AND platform_cost_usd > 0
                ) user_totals ON TRUE
                WHERE u.subscription_tier IN ('prepaid', 'usage_based', 'pro')
                GROUP BY u.subscription_tier
                ORDER BY total_revenue DESC
            """)
            ltv_tiers = []
            total_ltv_all = 0
            total_paid_users = 0
            for row in cur.fetchall():
                ltv_tiers.append({
                    'tier': row[0], 'users': row[1],
                    'total_revenue': float(row[2]), 'avg_ltv': float(row[3]), 'max_ltv': float(row[4])
                })
                total_ltv_all += float(row[2])
                total_paid_users += row[1]
            metrics['ltv'] = ltv_tiers
            metrics['avg_ltv_all'] = round(total_ltv_all / total_paid_users, 2) if total_paid_users > 0 else 0

            # ----- POWER USERS: active 4+ of last 8 weeks -----
            cur.execute("""
                WITH weekly_activity AS (
                    SELECT user_id, DATE_TRUNC('week', created_at) as week
                    FROM decisions
                    WHERE created_at > NOW() - INTERVAL '8 weeks'
                    GROUP BY user_id, week
                )
                SELECT COUNT(*) FROM (
                    SELECT user_id
                    FROM weekly_activity
                    GROUP BY user_id
                    HAVING COUNT(DISTINCT week) >= 4
                ) power
            """)
            metrics['power_users'] = cur.fetchone()[0]

            # ----- LIVE TRADING: Hyperliquid summary -----
            cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM user_profiles WHERE hyperliquid_wallet_address IS NOT NULL) as hl_connected,
                    (SELECT COUNT(*) FROM configurations WHERE trading_mode = 'hyperliquid' AND state = 'active') as hl_active,
                    (SELECT COUNT(*) FROM live_trades) as total_trades,
                    (SELECT COUNT(*) FROM live_trades WHERE closed_at IS NOT NULL) as closed_trades,
                    (SELECT ROUND(COALESCE(SUM(realized_pnl), 0)::numeric, 2) FROM live_trades) as total_pnl,
                    (SELECT ROUND(COALESCE(SUM(size_usd), 0)::numeric, 2) FROM live_trades) as total_volume
            """)
            row = cur.fetchone()
            metrics['live_trading'] = {
                'hl_connected': row[0], 'hl_active_bots': row[1],
                'total_trades': row[2], 'closed_trades': row[3],
                'total_pnl': float(row[4] or 0), 'total_volume': float(row[5] or 0)
            }

            # ----- GROWTH: monthly signups -----
            cur.execute("""
                SELECT TO_CHAR(created_at, 'YYYY-MM') as month, COUNT(*) as signups
                FROM user_profiles
                WHERE created_at IS NOT NULL
                GROUP BY month ORDER BY month
            """)
            metrics['growth'] = [{'month': row[0], 'signups': row[1]} for row in cur.fetchall()]

    return metrics


def print_business_report(metrics):
    """Print formatted business metrics report."""
    print("\n💰 REVENUE")
    print("-" * 80)
    print(f"{'Month':<10} {'Revenue':<12} {'Cost':<12} {'Margin':<12} {'Users':<8}")
    print("-" * 54)
    for m in metrics['revenue_monthly']:
        print(f"{m['month']:<10} ${m['revenue']:<11} ${m['cost']:<11} ${m['margin']:<11} {m['paying_users']:<8}")
    print(f"{'TOTAL':<10} ${metrics['revenue_total']:<11} ${metrics['cost_total']:<11} ${metrics['margin_total']:<11}")
    print(f"\nMargin: {metrics['margin_pct']}%")
    print(f"MTD Revenue: ${metrics['revenue_mtd']} (projected: ${metrics['revenue_projected']})")
    print(f"Last 30d: ${metrics['revenue_30d']} from {metrics['paying_users_30d']} users")
    print(f"Avg LTV (paid users): ${metrics['avg_ltv_all']}")

    f = metrics['funnel']
    print("\n📊 CONVERSION FUNNEL")
    print("-" * 80)
    print(f"Total Users:     {f['total_users']}")
    print(f"Created Bot:     {f['created_bot']} ({f['created_bot_pct']}%)")
    print(f"Ran a Bot:       {f['ran_bot']} ({f['ran_bot_pct']}%)")
    print(f"Has Active Bot:  {f['active_bot']} ({f['active_bot_pct']}%)")
    print(f"Became Paid:     {f['paid']} ({f['paid_pct']}%)")

    print(f"\nPost-Monetization (Jan 2026+): {metrics['post_monetization_signups']} signups → {metrics['post_monetization_paid']} paid ({metrics['post_monetization_conversion_pct']}%)")
    for c in metrics['cohorts']:
        print(f"  {c['month']}: {c['signups']} signups → {c['paid']} paid ({c['conversion_pct']}%)")

    e = metrics['engagement']
    print("\n👥 ENGAGEMENT")
    print("-" * 80)
    print(f"DAU: {e['dau']}  WAU: {e['wau']}  MAU: {e['mau']}")
    print(f"DAU/WAU: {e['dau_wau_pct']}%  DAU/MAU: {e['dau_mau_pct']}%")
    print(f"Power Users (4+/8wk): {metrics['power_users']}")

    r = metrics['retention']
    print(f"\nRetention (users 30d+ old): {r['cohort_size']} total → {r['active_7d']} active 7d ({r['active_7d_pct']}%), {r['active_30d']} active 30d ({r['active_30d_pct']}%)")

    lt = metrics['live_trading']
    print("\n⚡ LIVE TRADING (Hyperliquid)")
    print("-" * 80)
    print(f"Connected: {lt['hl_connected']}  Active Bots: {lt['hl_active_bots']}  Trades: {lt['total_trades']}  Volume: ${lt['total_volume']:,.2f}  P&L: ${lt['total_pnl']:,.2f}")


def get_platform_stats():
    """Query database for comprehensive platform statistics."""
    stats = {}

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # User statistics
            cur.execute("""
                SELECT
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN subscription_tier = 'prepaid' THEN 1 END) as prepaid_users,
                    COUNT(CASE WHEN subscription_tier = 'free' OR subscription_tier IS NULL THEN 1 END) as free_users,
                    COUNT(CASE WHEN subscription_expires_at IS NULL AND subscription_tier = 'prepaid' THEN 1 END) as active_subscribers
                FROM user_profiles
            """)
            user_data = cur.fetchone()
            stats['total_users'] = user_data[0]
            stats['pro_users'] = user_data[1]
            stats['free_users'] = user_data[2]
            stats['active_subscribers'] = user_data[3]

            # Bot statistics
            cur.execute("""
                SELECT
                    COUNT(*) as total_bots,
                    COUNT(CASE WHEN state = 'active' THEN 1 END) as active_bots,
                    COUNT(CASE WHEN state = 'inactive' THEN 1 END) as inactive_bots,
                    COUNT(DISTINCT user_id) as users_with_bots
                FROM configurations
            """)
            bot_data = cur.fetchone()
            stats['total_bots'] = bot_data[0]
            stats['active_bots'] = bot_data[1]
            stats['inactive_bots'] = bot_data[2]
            stats['users_with_bots'] = bot_data[3]

            # Trading mode breakdown
            cur.execute("""
                SELECT
                    trading_mode as mode,
                    COUNT(*) as count
                FROM configurations
                WHERE state = 'active'
                GROUP BY trading_mode
            """)
            mode_data = cur.fetchall()
            stats['active_paper_bots'] = 0
            stats['active_symphony_bots'] = 0
            stats['active_aster_bots'] = 0
            stats['active_hyperliquid_bots'] = 0
            for row in mode_data:
                mode = row[0] or 'paper'
                if mode == 'paper':
                    stats['active_paper_bots'] = row[1]
                elif mode == 'symphony':
                    stats['active_symphony_bots'] = row[1]
                elif mode == 'aster':
                    stats['active_aster_bots'] = row[1]
                elif mode == 'hyperliquid':
                    stats['active_hyperliquid_bots'] = row[1]
            # Combined live count for backward compatibility
            stats['active_live_bots'] = stats['active_symphony_bots'] + stats['active_aster_bots'] + stats['active_hyperliquid_bots']

            # Trading activity
            cur.execute("""
                SELECT
                    SUM(total_trades) as total_trades,
                    SUM(win_trades) as win_trades,
                    SUM(loss_trades) as loss_trades,
                    ROUND(SUM(win_trades)::numeric / NULLIF(SUM(total_trades), 0) * 100, 2) as overall_win_rate,
                    ROUND(SUM(total_pnl), 2) as total_pnl
                FROM paper_accounts
            """)
            trade_data = cur.fetchone()
            stats['total_trades'] = trade_data[0] or 0
            stats['win_trades'] = trade_data[1] or 0
            stats['loss_trades'] = trade_data[2] or 0
            stats['overall_win_rate'] = trade_data[3] or 0
            stats['total_pnl'] = trade_data[4] or 0

            # Recent activity (24h)
            cur.execute("""
                SELECT COUNT(*) as trades_24h
                FROM paper_trades
                WHERE opened_at > NOW() - INTERVAL '24 hours'
            """)
            stats['trades_24h'] = cur.fetchone()[0]

            # Recent activity (7d)
            cur.execute("""
                SELECT COUNT(*) as trades_7d
                FROM paper_trades
                WHERE opened_at > NOW() - INTERVAL '7 days'
            """)
            stats['trades_7d'] = cur.fetchone()[0]

            # Recent activity (30d)
            cur.execute("""
                SELECT COUNT(*) as trades_30d
                FROM paper_trades
                WHERE opened_at > NOW() - INTERVAL '30 days'
            """)
            stats['trades_30d'] = cur.fetchone()[0]

            # Open positions
            cur.execute("""
                SELECT
                    COUNT(*) as open_positions,
                    COUNT(DISTINCT symbol) as symbols_traded,
                    ROUND(SUM(size_usd), 2) as total_exposure,
                    ROUND(SUM(unrealized_pnl), 2) as total_unrealized_pnl
                FROM paper_trades
                WHERE status = 'open'
            """)
            position_data = cur.fetchone()
            stats['open_positions'] = position_data[0]
            stats['unique_symbols'] = position_data[1]
            stats['total_exposure'] = position_data[2] or 0
            stats['unrealized_pnl'] = position_data[3] or 0

            # Top symbols
            cur.execute("""
                SELECT
                    config_data->>'selected_pair' as symbol,
                    COUNT(*) as bot_count
                FROM configurations
                WHERE state = 'active'
                AND config_data->>'selected_pair' IS NOT NULL
                GROUP BY symbol
                ORDER BY bot_count DESC
                LIMIT 10
            """)
            stats['top_symbols'] = cur.fetchall()

            # Recent decisions (24h)
            cur.execute("""
                SELECT
                    action,
                    COUNT(*) as count,
                    ROUND(AVG(confidence) * 100, 1) as avg_confidence
                FROM decisions
                WHERE created_at > NOW() - INTERVAL '24 hours'
                GROUP BY action
                ORDER BY count DESC
            """)
            stats['recent_decisions'] = cur.fetchall()

            # Service health - check for recent extractions
            cur.execute("""
                SELECT
                    COUNT(*) as extractions_1h
                FROM decisions
                WHERE created_at > NOW() - INTERVAL '1 hour'
            """)
            stats['extractions_1h'] = cur.fetchone()[0]

            # Average account balance
            cur.execute("""
                SELECT
                    ROUND(AVG(current_balance), 2) as avg_balance,
                    ROUND(MIN(current_balance), 2) as min_balance,
                    ROUND(MAX(current_balance), 2) as max_balance
                FROM paper_accounts
                WHERE current_balance > 0
            """)
            balance_data = cur.fetchone()
            stats['avg_balance'] = balance_data[0] or 0
            stats['min_balance'] = balance_data[1] or 0
            stats['max_balance'] = balance_data[2] or 0

    return stats


def print_status_report(stats):
    """Print formatted status report to console."""
    print("=" * 80)
    print("GGBOTS PLATFORM STATUS CHECK")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 80)

    print("\n📊 USER STATISTICS")
    print("-" * 80)
    print(f"Total Users: {stats['total_users']}")
    print(f"  Prepaid Users: {stats['pro_users']} ({stats['active_subscribers']} active subscriptions)")
    print(f"  Free Users: {stats['free_users']}")
    print(f"Users with Bots: {stats['users_with_bots']} ({stats['users_with_bots']/stats['total_users']*100:.1f}%)")

    print("\n🤖 BOT STATISTICS")
    print("-" * 80)
    print(f"Total Bots Created: {stats['total_bots']}")
    print(f"  Active: {stats['active_bots']} ({stats['active_bots']/stats['total_bots']*100:.1f}%)")
    print(f"    Paper: {stats['active_paper_bots']}")
    print(f"    Symphony: {stats['active_symphony_bots']}")
    print(f"    Aster: {stats['active_aster_bots']}")
    print(f"    Hyperliquid (Live): {stats['active_hyperliquid_bots']}")
    print(f"  Inactive: {stats['inactive_bots']}")
    print(f"Avg Bots per User: {stats['total_bots']/stats['users_with_bots']:.1f}")

    print("\n💹 TRADING ACTIVITY")
    print("-" * 80)
    print(f"Total Trades (All Time): {stats['total_trades']:,}")
    print(f"  Wins: {stats['win_trades']:,}")
    print(f"  Losses: {stats['loss_trades']:,}")
    print(f"  Platform Win Rate: {stats['overall_win_rate']}%")
    print(f"  Total P&L: ${stats['total_pnl']:,.2f}")
    print(f"\nRecent Activity:")
    print(f"  Last 24 hours: {stats['trades_24h']} trades")
    print(f"  Last 7 days: {stats['trades_7d']} trades")
    print(f"  Last 30 days: {stats['trades_30d']} trades")

    print("\n📍 OPEN POSITIONS")
    print("-" * 80)
    print(f"Open Positions: {stats['open_positions']}")
    print(f"Unique Symbols: {stats['unique_symbols']}")
    print(f"Total Exposure: ${stats['total_exposure']:,.2f}")
    print(f"Unrealized P&L: ${stats['unrealized_pnl']:,.2f}")

    print("\n💰 ACCOUNT BALANCES (Paper Trading)")
    print("-" * 80)
    print(f"Average Balance: ${stats['avg_balance']:,.2f}")
    print(f"Lowest Balance: ${stats['min_balance']:,.2f}")
    print(f"Highest Balance: ${stats['max_balance']:,.2f}")

    print("\n🔥 TOP TRADING SYMBOLS (Active Bots)")
    print("-" * 80)
    print(f"{'Symbol':<15} {'Bots':<8}")
    print("-" * 25)
    for symbol, count in stats['top_symbols']:
        print(f"{symbol:<15} {count:<8}")

    print("\n🧠 DECISION ACTIVITY (24h)")
    print("-" * 80)
    print(f"{'Action':<12} {'Count':<10} {'Avg Confidence':<15}")
    print("-" * 40)
    for action, count, confidence in stats['recent_decisions']:
        print(f"{action:<12} {count:<10} {confidence}%")

    print("\n💚 SYSTEM HEALTH")
    print("-" * 80)
    print(f"Decisions (last hour): {stats['extractions_1h']}")
    health_status = "🟢 HEALTHY" if stats['extractions_1h'] > 0 else "🟡 LOW ACTIVITY"
    print(f"Status: {health_status}")

    print("\n" + "=" * 80)
    print("\nSUGGESTED ACTIVE.md UPDATE:")
    print("-" * 80)
    print(f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"**System Health**: 🟢 Production Live ({stats['total_users']}+ users, {stats['active_bots']}+ active bots)")
    print(f"**Project Status**: Live application with complete Stripe monetization and Symphony live trading")
    print("-" * 80)


def get_database_schema():
    """Query complete database schema from Supabase with comprehensive metadata."""
    schema = {}

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get all tables in public schema
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]

            # For each table, get comprehensive schema info
            for table in tables:
                # Get columns with types
                cur.execute("""
                    SELECT
                        column_name,
                        data_type,
                        character_maximum_length,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = %s
                    ORDER BY ordinal_position
                """, (table,))

                columns = []
                for row in cur.fetchall():
                    col_name, data_type, max_len, nullable, default = row

                    # Format type with length if applicable
                    if max_len and data_type in ('character varying', 'character'):
                        type_str = f"{data_type}({max_len})"
                    else:
                        type_str = data_type

                    columns.append({
                        'name': col_name,
                        'type': type_str,
                        'nullable': nullable == 'YES',
                        'default': default
                    })

                # Get primary key columns
                cur.execute("""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.table_schema = 'public'
                    AND tc.table_name = %s
                    AND tc.constraint_type = 'PRIMARY KEY'
                    ORDER BY kcu.ordinal_position
                """, (table,))
                primary_keys = [row[0] for row in cur.fetchall()]

                # Get foreign keys
                cur.execute("""
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS foreign_table,
                        ccu.column_name AS foreign_column
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.table_schema = 'public'
                    AND tc.table_name = %s
                    AND tc.constraint_type = 'FOREIGN KEY'
                """, (table,))
                foreign_keys = [
                    {'column': row[0], 'foreign_table': row[1], 'foreign_column': row[2]}
                    for row in cur.fetchall()
                ]

                # Get indexes (Supabase may have restricted pg_catalog access)
                indexes = []
                try:
                    cur.execute("""
                        SELECT
                            i.relname as index_name,
                            a.attname as column_name
                        FROM pg_class t
                        JOIN pg_index ix ON t.oid = ix.indrelid
                        JOIN pg_class i ON i.oid = ix.indexrelid
                        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                        WHERE t.relname = %s
                        AND i.relname NOT LIKE '%%_pkey'
                        ORDER BY i.relname, a.attnum
                    """, (table,))

                    # Group by index name
                    current_index = None
                    current_cols = []
                    for row in cur.fetchall():
                        if len(row) >= 2:
                            idx_name = row[0]
                            col_name = row[1]
                            if current_index != idx_name:
                                if current_index:
                                    indexes.append({'name': current_index, 'columns': ', '.join(current_cols)})
                                current_index = idx_name
                                current_cols = [col_name]
                            else:
                                current_cols.append(col_name)
                    if current_index:
                        indexes.append({'name': current_index, 'columns': ', '.join(current_cols)})
                except Exception:
                    # Indexes are optional - continue without them
                    indexes = []

                # Get unique constraints (excluding PKs)
                cur.execute("""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.table_schema = 'public'
                    AND tc.table_name = %s
                    AND tc.constraint_type = 'UNIQUE'
                    ORDER BY kcu.ordinal_position
                """, (table,))
                unique_constraints = [row[0] for row in cur.fetchall()]

                schema[table] = {
                    'columns': columns,
                    'primary_keys': primary_keys,
                    'foreign_keys': foreign_keys,
                    'indexes': indexes,
                    'unique_constraints': unique_constraints
                }

    return schema


def _compact_type(type_str):
    """Shorten SQL type names for compact schema output."""
    replacements = {
        'timestamp with time zone': 'timestamptz',
        'timestamp without time zone': 'timestamp',
        'character varying': 'varchar',
        'boolean': 'bool',
        'integer': 'int',
        'USER-DEFINED': 'enum',
    }
    for old, new in replacements.items():
        type_str = type_str.replace(old, new)
    return type_str


def _is_boring_default(default_str, col_type):
    """Check if a default value is standard/obvious and can be omitted."""
    if not default_str:
        return True
    boring = [
        'gen_random_uuid()', 'uuid_generate_v4()', 'now()',
        "nextval(", "0", "0.00", "false", "0.00)",
        "ARRAY[]",
    ]
    for b in boring:
        if b in default_str:
            return True
    return False


def format_schema_markdown(schema):
    """Format database schema as compact markdown. Convention: ? = nullable, =val for non-obvious defaults."""
    lines = [
        "## 📊 Database Schema",
        "",
        "**Auto-generated** by `scripts/status_check.py` | "
        f"**Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} | "
        "**Design decisions**: [DOCS/DATABASE_CONTEXT.md](DOCS/DATABASE_CONTEXT.md)",
        "",
        "**Conventions**: `?` = nullable, `=value` = non-obvious default, standard defaults (uuid, now(), 0, false) omitted",
        "",
        "---",
        ""
    ]

    for table_name in sorted(schema.keys()):
        table_data = schema[table_name]
        columns = table_data['columns']
        primary_keys = table_data['primary_keys']
        foreign_keys = table_data['foreign_keys']
        indexes = table_data['indexes']
        unique_constraints = table_data['unique_constraints']

        # Header line: table name, col count, PK, FKs, unique constraints
        header_parts = [f"### {table_name} ({len(columns)} cols)"]
        if primary_keys:
            header_parts.append(f"PK: {','.join(primary_keys)}")
        if foreign_keys:
            fk_strs = [f"{fk['column']}→{fk['foreign_table']}" for fk in foreign_keys]
            header_parts.append(f"FK: {', '.join(fk_strs)}")
        if unique_constraints:
            header_parts.append(f"UQ: {','.join(unique_constraints)}")
        lines.append(' | '.join(header_parts))

        # Indexes on one line (skip deprecated)
        active_indexes = [idx for idx in indexes if not idx['name'].startswith('_deprecated')]
        if active_indexes:
            idx_strs = [f"{idx['name']}({idx.get('columns', '')})" for idx in active_indexes]
            idx_line = "Idx: " + ", ".join(idx_strs)
            # Wrap if too long
            if len(idx_line) > 200:
                idx_line = idx_line[:197] + "..."
            lines.append(idx_line)

        # Columns as compact inline list
        col_parts = []
        for col in columns:
            col_type = _compact_type(col['type'])
            nullable = '?' if col['nullable'] else ''
            default_str = str(col['default']) if col['default'] else ''

            # Only show non-obvious defaults
            default_suffix = ''
            if not _is_boring_default(default_str, col_type):
                # Clean up default string
                # Strip SQL casts and quotes
                import re
                clean_default = re.sub(r"::\w+(\[\])?", "", default_str)
                clean_default = clean_default.strip("'")
                if len(clean_default) > 20:
                    clean_default = clean_default[:17] + "..."
                default_suffix = f"={clean_default}"

            col_parts.append(f"{col['name']} {col_type}{nullable}{default_suffix}")

        # Join columns, wrap at ~120 chars per line
        col_line = ""
        for part in col_parts:
            if col_line and len(col_line) + len(part) + 2 > 120:
                lines.append(col_line)
                col_line = part
            else:
                col_line = col_line + ", " + part if col_line else part
        if col_line:
            lines.append(col_line)

        lines.append("")

    lines.append("---")
    lines.append("")

    return '\n'.join(lines)


def get_domain_models():
    """Parse domain models from core/domain/ directory using AST."""
    import ast
    import inspect
    from pathlib import Path

    domain_models = []
    domain_path = Path(__file__).parent.parent / "core" / "domain"

    # List of domain model files to parse
    model_files = [
        'user_profile.py',
        'decision.py',
        'position.py',
        'market_data.py',
        'data_source.py',
    ]

    for file_name in model_files:
        file_path = domain_path / file_name
        if not file_path.exists():
            continue

        try:
            with open(file_path, 'r') as f:
                source = f.read()

            tree = ast.parse(source)

            # Find dataclasses and their properties
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's a dataclass
                    is_dataclass = any(
                        isinstance(dec, ast.Name) and dec.id == 'dataclass'
                        or isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id == 'dataclass'
                        for dec in node.decorator_list
                    )

                    if not is_dataclass:
                        continue

                    # Extract class docstring
                    docstring = ast.get_docstring(node) or ""

                    # Extract fields from annotations
                    fields = []
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            field_name = item.target.id
                            # Get type annotation as string
                            type_str = ast.unparse(item.annotation) if hasattr(ast, 'unparse') else ''
                            fields.append({'name': field_name, 'type': type_str})

                    # Extract @property methods
                    properties = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            is_property = any(
                                isinstance(dec, ast.Name) and dec.id == 'property'
                                for dec in item.decorator_list
                            )
                            if is_property:
                                prop_doc = ast.get_docstring(item) or ""
                                properties.append({'name': item.name, 'doc': prop_doc})

                    if fields:  # Only add if it has fields
                        domain_models.append({
                            'class_name': node.name,
                            'file': file_name,
                            'docstring': docstring,
                            'fields': fields,
                            'properties': properties
                        })
        except Exception as e:
            print(f"⚠️  Warning: Could not parse {file_name}: {e}")
            continue

    return domain_models


def format_domain_models_markdown(domain_models):
    """Format domain models as compact markdown."""
    if not domain_models:
        return ""

    lines = [
        "## 🎯 Domain Models & Business Logic",
        "",
        "Business logic on top of DB tables. See [DOCS/DATABASE_CONTEXT.md](DOCS/DATABASE_CONTEXT.md) for design decisions.",
        "",
        "---",
        ""
    ]

    for model in domain_models:
        # Header with purpose
        purpose = ""
        if model['docstring']:
            purpose = f" — {model['docstring'].split(chr(10))[0].strip()}"
        lines.append(f"### {model['class_name']} (core/domain/{model['file']}){purpose}")

        # Fields as inline list
        if model['fields']:
            field_strs = [f"{f['name']}: {f['type']}" for f in model['fields']]
            field_line = "Fields: " + ", ".join(field_strs)
            # Wrap long field lines
            if len(field_line) > 150:
                field_line = field_line[:147] + "..."
            lines.append(field_line)

        # Properties as inline list with brief docs
        if model['properties']:
            prop_strs = []
            for prop in model['properties']:
                doc = prop['doc'].split('\n')[0].strip() if prop['doc'] else ""
                # Truncate long docs
                if len(doc) > 60:
                    doc = doc[:57] + "..."
                prop_strs.append(f"`{prop['name']}` ({doc})" if doc else f"`{prop['name']}`")
            lines.append("@property: " + " | ".join(prop_strs))

        lines.append("")

    lines.append("---")
    lines.append("")

    return '\n'.join(lines)


def get_botconfig_structure():
    """Parse BotConfig structure from core/config/models.py using AST."""
    import ast
    from pathlib import Path

    config_file = Path(__file__).parent.parent / "core" / "config" / "models.py"

    if not config_file.exists():
        return None

    try:
        with open(config_file, 'r') as f:
            source = f.read()

        tree = ast.parse(source)

        # Find BotConfig class
        botconfig_fields = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'BotConfig':
                # Extract docstring
                docstring = ast.get_docstring(node) or ""

                # Extract fields from annotations
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        field_name = item.target.id

                        # Get type annotation
                        type_str = ast.unparse(item.annotation) if hasattr(ast, 'unparse') else ''

                        # Try to extract Field() default and description
                        default_value = None
                        description = ""

                        if item.value and isinstance(item.value, ast.Call):
                            # Check if it's a Field() call
                            if (isinstance(item.value.func, ast.Name) and item.value.func.id == 'Field') or \
                               (isinstance(item.value.func, ast.Attribute) and item.value.func.attr == 'Field'):
                                # Extract keyword arguments
                                for keyword in item.value.keywords:
                                    if keyword.arg == 'default':
                                        if isinstance(keyword.value, ast.Constant):
                                            default_value = keyword.value.value
                                        else:
                                            default_value = ast.unparse(keyword.value) if hasattr(ast, 'unparse') else '...'
                                    elif keyword.arg == 'description':
                                        if isinstance(keyword.value, ast.Constant):
                                            description = keyword.value.value
                        elif item.value:
                            # Direct assignment (not Field())
                            if isinstance(item.value, ast.Constant):
                                default_value = item.value.value
                            elif isinstance(item.value, ast.Call):
                                default_value = ast.unparse(item.value) if hasattr(ast, 'unparse') else '...'

                        botconfig_fields.append({
                            'name': field_name,
                            'type': type_str,
                            'default': default_value,
                            'description': description
                        })

                return {
                    'docstring': docstring,
                    'fields': botconfig_fields
                }

        return None
    except Exception as e:
        print(f"⚠️  Warning: Could not parse BotConfig: {e}")
        return None


def format_botconfig_markdown(botconfig):
    """Format BotConfig structure as compact markdown."""
    if not botconfig:
        return ""

    lines = [
        "## ⚙️ Configuration Structure (config_data JSONB)",
        "",
        f"Source: `core/config/models.py` | Auto-generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        ""
    ]

    # Fields as compact list
    for field in botconfig['fields']:
        default_str = f"={field['default']}" if field['default'] is not None else ""
        desc_str = f" — {field['description']}" if field['description'] else ""
        lines.append(f"- `{field['name']}`: {field['type']}{default_str}{desc_str}")

    lines.append("")
    lines.append("---")
    lines.append("")

    return '\n'.join(lines)


def get_pm2_status():
    """Query PM2 for live service status."""
    import subprocess
    import json

    try:
        result = subprocess.run(['pm2', 'jlist'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return []

        services = json.loads(result.stdout)
        parsed = []

        for svc in services:
            # Calculate uptime
            uptime_ms = svc.get('pm2_env', {}).get('pm_uptime', 0)
            uptime_seconds = (datetime.now().timestamp() * 1000 - uptime_ms) / 1000 if uptime_ms else 0
            uptime_str = format_uptime(uptime_seconds)

            parsed.append({
                'name': svc.get('name', 'unknown'),
                'status': svc.get('pm2_env', {}).get('status', 'unknown'),
                'cpu': svc.get('monit', {}).get('cpu', 0),
                'memory': svc.get('monit', {}).get('memory', 0),
                'uptime': uptime_str,
                'restarts': svc.get('pm2_env', {}).get('restart_time', 0)
            })

        return parsed
    except Exception as e:
        print(f"⚠️  Warning: Could not get PM2 status: {e}")
        return []


def format_uptime(seconds):
    """Format uptime in human-readable format."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds/60)}m"
    elif seconds < 86400:
        return f"{int(seconds/3600)}h {int((seconds%3600)/60)}m"
    else:
        return f"{int(seconds/86400)}d {int((seconds%86400)/3600)}h"


def get_vm_resources():
    """Query VM disk, memory, and CPU usage."""
    import subprocess

    resources = {}

    try:
        # Disk usage
        df_result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
        if df_result.returncode == 0:
            lines = df_result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                resources['disk_total'] = parts[1]
                resources['disk_used'] = parts[2]
                resources['disk_percent'] = parts[4]

        # Memory usage
        free_result = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
        if free_result.returncode == 0:
            lines = free_result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                resources['mem_total'] = parts[1]
                resources['mem_used'] = parts[2]

        # CPU load averages
        uptime_result = subprocess.run(['uptime'], capture_output=True, text=True, timeout=5)
        if uptime_result.returncode == 0:
            # Parse "load average: 0.52, 0.58, 0.59"
            output = uptime_result.stdout
            if 'load average:' in output:
                load_part = output.split('load average:')[1].strip()
                loads = load_part.split(',')
                resources['cpu_load_1m'] = loads[0].strip()
                resources['cpu_load_5m'] = loads[1].strip() if len(loads) > 1 else '0.00'
                resources['cpu_load_15m'] = loads[2].strip() if len(loads) > 2 else '0.00'

        return resources
    except Exception as e:
        print(f"⚠️  Warning: Could not get VM resources: {e}")
        return {}


def get_redis_status():
    """Query Redis connectivity and memory usage."""
    import subprocess

    redis_info = {'status': 'unknown', 'memory': 'N/A'}

    try:
        # Check connectivity
        ping_result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True, timeout=2)
        if ping_result.returncode == 0 and 'PONG' in ping_result.stdout:
            redis_info['status'] = 'connected'

            # Get memory usage
            mem_result = subprocess.run(['redis-cli', 'info', 'memory'], capture_output=True, text=True, timeout=2)
            if mem_result.returncode == 0:
                for line in mem_result.stdout.split('\n'):
                    if line.startswith('used_memory_human:'):
                        redis_info['memory'] = line.split(':')[1].strip()
                        break
        else:
            redis_info['status'] = 'disconnected'
    except Exception as e:
        redis_info['status'] = 'error'
        print(f"⚠️  Warning: Could not get Redis status: {e}")

    return redis_info


def update_readme_schema(schema, domain_models=None):
    """Update README.md with current database schema and domain models."""
    readme_path = Path(__file__).parent.parent / "README.md"

    if not readme_path.exists():
        print(f"❌ ERROR: README.md not found at {readme_path}")
        return False

    # Read current README.md
    with open(readme_path, 'r') as f:
        content = f.read()

    # Generate new schema section
    new_schema = format_schema_markdown(schema)

    # Generate domain models section if provided
    domain_models_section = ""
    if domain_models:
        domain_models_section = "\n" + format_domain_models_markdown(domain_models)

    # Combine schema and domain models
    combined_content = new_schema + domain_models_section

    # Find and replace existing schema section or append
    schema_marker_start = "## 📊 Database Schema"

    if schema_marker_start in content:
        # Find start of schema section
        start_idx = content.find(schema_marker_start)

        # Find end of documentation sections
        # Look for Domain Models section first, then next ## heading
        rest_of_content = content[start_idx + len(schema_marker_start):]

        # Check if domain models section exists
        domain_marker = "\n## 🎯 Domain Models"
        if domain_marker in rest_of_content:
            # Find next section after domain models
            domain_start = rest_of_content.find(domain_marker)
            after_domain = rest_of_content[domain_start + len(domain_marker):]
            next_section = after_domain.find("\n## ")
            if next_section != -1:
                end_idx = start_idx + len(schema_marker_start) + domain_start + len(domain_marker) + next_section
            else:
                end_idx = len(content)
        else:
            # No domain models section, find next ## heading
            next_section = rest_of_content.find("\n## ")
            if next_section != -1:
                end_idx = start_idx + len(schema_marker_start) + next_section
            else:
                end_idx = len(content)

        new_content = content[:start_idx] + combined_content + content[end_idx:]
    else:
        # Append to end of file
        new_content = content.rstrip() + "\n\n" + combined_content

    # Write back to file
    with open(readme_path, 'w') as f:
        f.write(new_content)

    print(f"✅ README.md updated successfully!")
    print(f"   Database Tables: {len(schema)}")
    print(f"   Total Columns: {sum(len(table_data['columns']) for table_data in schema.values())}")
    print(f"   Primary Keys: {sum(len(table_data['primary_keys']) for table_data in schema.values())}")
    print(f"   Foreign Keys: {sum(len(table_data['foreign_keys']) for table_data in schema.values())}")
    print(f"   Indexes: {sum(len(table_data['indexes']) for table_data in schema.values())}")
    if domain_models:
        print(f"   Domain Models: {len(domain_models)}")
    return True


def update_active_md(stats, biz_metrics=None):
    """Update ACTIVE.md with current statistics and business metrics."""
    active_path = Path(__file__).parent.parent / "ACTIVE.md"

    if not active_path.exists():
        print(f"❌ ERROR: ACTIVE.md not found at {active_path}")
        return False

    # Read current ACTIVE.md
    with open(active_path, 'r') as f:
        content = f.read()

    # Calculate derived stats
    health_emoji = "🟢" if stats['extractions_1h'] > 0 else "🟡"
    health_status = "HEALTHY" if stats['extractions_1h'] > 0 else "LOW ACTIVITY"

    # Build comprehensive header with all metrics
    new_header = [
        "# 🚀 ACTIVE - ggbots System Status",
        "",
        f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} (Auto-updated by status_check.py)",
        f"**System Health**: {health_emoji} {health_status}",
        "",
        "## 📊 Live Platform Metrics",
        "",
        "### Users & Subscriptions",
        f"- **Total Users**: {stats['total_users']}",
        f"- **Prepaid Users**: {stats['pro_users']} ({stats['active_subscribers']} active subscriptions)",
        f"- **Free Users**: {stats['free_users']}",
        f"- **Users with Bots**: {stats['users_with_bots']} ({stats['users_with_bots']/stats['total_users']*100:.1f}%)",
        "",
        "### Bot Statistics",
        f"- **Total Bots**: {stats['total_bots']}",
        f"- **Active Bots**: {stats['active_bots']} ({stats['active_bots']/stats['total_bots']*100:.1f}%)",
        f"  - Paper: {stats['active_paper_bots']}",
        f"  - Symphony (Live): {stats['active_symphony_bots']}",
        f"  - Aster (DEX): {stats['active_aster_bots']}",
        f"  - Hyperliquid (Live): {stats['active_hyperliquid_bots']}",
        f"- **Inactive Bots**: {stats['inactive_bots']}",
        f"- **Avg Bots per User**: {stats['total_bots']/stats['users_with_bots']:.1f}",
        "",
        "### Trading Activity",
        f"- **Total Trades (All Time)**: {stats['total_trades']:,}",
        f"  - Wins: {stats['win_trades']:,}",
        f"  - Losses: {stats['loss_trades']:,}",
        f"  - Platform Win Rate: {stats['overall_win_rate']}%",
        f"  - Total P&L: ${stats['total_pnl']:,.2f}",
        f"- **Recent Activity**:",
        f"  - Last 24 hours: {stats['trades_24h']} trades",
        f"  - Last 7 days: {stats['trades_7d']} trades",
        f"  - Last 30 days: {stats['trades_30d']} trades",
        "",
        "### Open Positions",
        f"- **Open Positions**: {stats['open_positions']}",
        f"- **Unique Symbols**: {stats['unique_symbols']}",
        f"- **Total Exposure**: ${stats['total_exposure']:,.2f}",
        f"- **Unrealized P&L**: ${stats['unrealized_pnl']:,.2f}",
        "",
        "### Account Balances (Paper Trading)",
        f"- **Average Balance**: ${stats['avg_balance']:,.2f}",
        f"- **Lowest Balance**: ${stats['min_balance']:,.2f}",
        f"- **Highest Balance**: ${stats['max_balance']:,.2f}",
        "",
        "### Top Trading Symbols (Active Bots)",
        ""
    ]

    # Add top symbols
    for symbol, count in stats['top_symbols'][:5]:  # Top 5
        new_header.append(f"- **{symbol}**: {count} bots")

    new_header.extend([
        "",
        "### Decision Activity (24h)",
        ""
    ])

    # Add recent decisions
    for action, count, confidence in stats['recent_decisions']:
        new_header.append(f"- **{action}**: {count} decisions (avg confidence: {confidence}%)")

    new_header.extend([
        "",
        "### System Health",
        f"- **Decisions (last hour)**: {stats['extractions_1h']}",
        f"- **Status**: {health_emoji} {health_status}",
        ""
    ])

    # Add Business Metrics section if available
    if biz_metrics:
        f = biz_metrics['funnel']
        e = biz_metrics['engagement']
        new_header.extend([
            "## 💰 Business Metrics",
            "",
            "### Revenue",
            f"- **All-Time Revenue**: ${biz_metrics['revenue_total']:,.2f} (margin: ${biz_metrics['margin_total']:,.2f}, {biz_metrics['margin_pct']}%)",
            f"- **Last 30d Revenue**: ${biz_metrics['revenue_30d']:,.2f} from {biz_metrics['paying_users_30d']} users",
            f"- **Month-to-Date**: ${biz_metrics['revenue_mtd']:,.2f} (projected: ~${biz_metrics['revenue_projected']:,.2f})",
            f"- **Avg LTV (paid)**: ${biz_metrics['avg_ltv_all']:,.2f}",
            "",
            "### Conversion Funnel",
            f"- **Signup → Created Bot**: {f['created_bot_pct']}%",
            f"- **Signup → Ran Bot**: {f['ran_bot_pct']}%",
            f"- **Signup → Paid**: {f['paid_pct']}% ({f['paid']}/{f['total_users']})",
            f"- **Post-Monetization (Jan+)**: {biz_metrics['post_monetization_conversion_pct']}% ({biz_metrics['post_monetization_paid']}/{biz_metrics['post_monetization_signups']})",
            "",
            "### Engagement",
            f"- **DAU/WAU/MAU**: {e['dau']}/{e['wau']}/{e['mau']}",
            f"- **DAU/WAU Stickiness**: {e['dau_wau_pct']}%",
            f"- **Power Users (4+/8wk)**: {biz_metrics['power_users']}",
            "",
            "### Live Trading (Hyperliquid)",
            f"- **Connected Wallets**: {biz_metrics['live_trading']['hl_connected']}",
            f"- **Active Bots**: {biz_metrics['live_trading']['hl_active_bots']}",
            f"- **Total Volume**: ${biz_metrics['live_trading']['total_volume']:,.2f}",
            ""
        ])

    # Add System Resources section
    new_header.extend([
        "## 🖥️ System Resources",
        ""
    ])

    # PM2 Services
    pm2_services = get_pm2_status()
    if pm2_services:
        new_header.extend([
            "### PM2 Services",
            "",
            "| Service | Status | CPU | Memory | Uptime | Restarts |",
            "|---------|--------|-----|--------|--------|----------|"
        ])

        for svc in pm2_services:
            status_emoji = "🟢" if svc['status'] == 'online' else "🔴"
            mem_mb = svc['memory'] / (1024 * 1024)  # Convert bytes to MB
            new_header.append(
                f"| {svc['name']} | {status_emoji} {svc['status']} | {svc['cpu']}% | {mem_mb:.0f}MB | {svc['uptime']} | {svc['restarts']} |"
            )
        new_header.append("")

    # VM Resources
    vm_resources = get_vm_resources()
    if vm_resources:
        new_header.extend([
            "### VM Resources",
            ""
        ])
        if 'disk_total' in vm_resources:
            new_header.append(f"- **Disk**: {vm_resources.get('disk_used', 'N/A')} / {vm_resources.get('disk_total', 'N/A')} ({vm_resources.get('disk_percent', 'N/A')})")
        if 'mem_total' in vm_resources:
            new_header.append(f"- **Memory**: {vm_resources.get('mem_used', 'N/A')} / {vm_resources.get('mem_total', 'N/A')}")
        if 'cpu_load_1m' in vm_resources:
            new_header.append(f"- **CPU Load**: {vm_resources.get('cpu_load_1m', '0.00')} / {vm_resources.get('cpu_load_5m', '0.00')} / {vm_resources.get('cpu_load_15m', '0.00')} (1m/5m/15m)")
        new_header.append("")

    # Redis Status
    redis_status = get_redis_status()
    if redis_status:
        redis_emoji = "🟢" if redis_status['status'] == 'connected' else "🔴"
        new_header.extend([
            "### Infrastructure Services",
            "",
            f"- **Redis**: {redis_emoji} {redis_status['status']} (Memory: {redis_status['memory']})",
            f"- **Supabase PostgreSQL**: 🟢 connected (Remote managed service)",
            ""
        ])

    # Find where the header ends (first "---")
    lines = content.split('\n')
    header_end = 0
    for i, line in enumerate(lines):
        if line.strip() == "---" and i > 5:  # First --- after header
            header_end = i
            break

    if header_end > 0:
        # Reconstruct content with new header
        new_content = '\n'.join(new_header + lines[header_end:])

        # Write back to file
        with open(active_path, 'w') as f:
            f.write(new_content)

        print(f"✅ ACTIVE.md updated successfully!")
        print(f"   Users: {stats['total_users']}")
        print(f"   Active Bots: {stats['active_bots']}")
        print(f"   Total Trades: {stats['total_trades']:,}")
        print(f"   Win Rate: {stats['overall_win_rate']}%")
        return True
    else:
        print("⚠️  WARNING: Could not find header section to update")
        return False


def append_technical_docs_to_active(schema, domain_models, botconfig):
    """Append database schema, domain models, and config structure to ACTIVE.md."""
    active_path = Path(__file__).parent.parent / "ACTIVE.md"

    if not active_path.exists():
        print(f"❌ ERROR: ACTIVE.md not found at {active_path}")
        return False

    # Read current ACTIVE.md
    with open(active_path, 'r') as f:
        content = f.read()

    # Generate sections
    schema_section = format_schema_markdown(schema)
    domain_models_section = format_domain_models_markdown(domain_models) if domain_models else ""
    botconfig_section = format_botconfig_markdown(botconfig) if botconfig else ""

    # Find where to append (after the last --- marker before any existing schema section)
    # Look for schema marker to replace, or append to end
    schema_marker = "## 📊 Database Schema"

    if schema_marker in content:
        # Replace existing schema + everything after it
        schema_start = content.find(schema_marker)
        new_content = content[:schema_start] + schema_section + "\n" + domain_models_section + "\n" + botconfig_section
    else:
        # Append to end
        new_content = content.rstrip() + "\n\n" + schema_section + "\n" + domain_models_section + "\n" + botconfig_section

    # Write back
    with open(active_path, 'w') as f:
        f.write(new_content)

    print(f"✅ ACTIVE.md technical documentation updated!")
    print(f"   Database Tables: {len(schema)}")
    print(f"   Total Columns: {sum(len(table_data['columns']) for table_data in schema.values())}")
    print(f"   Primary Keys: {sum(len(table_data['primary_keys']) for table_data in schema.values())}")
    print(f"   Foreign Keys: {sum(len(table_data['foreign_keys']) for table_data in schema.values())}")
    print(f"   Indexes: {sum(len(table_data['indexes']) for table_data in schema.values())}")
    if domain_models:
        print(f"   Domain Models: {len(domain_models)}")
    if botconfig:
        print(f"   Config Fields: {len(botconfig['fields'])}")
    return True


def main():
    parser = argparse.ArgumentParser(description='Check ggbots platform status')
    parser.add_argument('--update', action='store_true',
                       help='Update ACTIVE.md with current stats')
    parser.add_argument('--quiet', action='store_true',
                       help='Only show summary (for cron jobs)')
    args = parser.parse_args()

    try:
        stats = get_platform_stats()
        biz_metrics = get_business_metrics()

        if args.quiet:
            # Just print summary for monitoring
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                  f"Users: {stats['total_users']} | "
                  f"Active Bots: {stats['active_bots']} | "
                  f"Trades (24h): {stats['trades_24h']} | "
                  f"Rev(30d): ${biz_metrics['revenue_30d']} | "
                  f"DAU/WAU/MAU: {biz_metrics['engagement']['dau']}/{biz_metrics['engagement']['wau']}/{biz_metrics['engagement']['mau']}")
        else:
            print_status_report(stats)
            print_business_report(biz_metrics)

        if args.update:
            print("\n" + "=" * 80)
            print("UPDATING DOCUMENTATION...")
            print("=" * 80)
            print()

            # Update ACTIVE.md with stats + business metrics
            update_active_md(stats, biz_metrics)

            # Query database schema
            print("\n📊 Querying database schema...")
            schema = get_database_schema()

            # Parse domain models
            print("\n🎯 Parsing domain models...")
            domain_models = get_domain_models()
            print(f"   Found {len(domain_models)} domain models")

            # Parse BotConfig structure
            print("\n⚙️  Parsing BotConfig structure...")
            botconfig = get_botconfig_structure()
            if botconfig:
                print(f"   Found {len(botconfig['fields'])} configuration fields")

            # Append schema + models + config to ACTIVE.md
            append_technical_docs_to_active(schema, domain_models, botconfig)

            print("\n" + "=" * 80)
            print("✅ All documentation updated successfully!")
            print("=" * 80)

        return 0

    except Exception as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
