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


def get_platform_stats():
    """Query database for comprehensive platform statistics."""
    stats = {}

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # User statistics
            cur.execute("""
                SELECT
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN subscription_tier = 'ggbase' THEN 1 END) as pro_users,
                    COUNT(CASE WHEN subscription_tier = 'free' OR subscription_tier IS NULL THEN 1 END) as free_users,
                    COUNT(CASE WHEN subscription_expires_at IS NULL AND subscription_tier = 'ggbase' THEN 1 END) as active_subscribers
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
            stats['active_live_bots'] = 0
            for row in mode_data:
                mode = row[0] or 'paper'
                if mode == 'live':
                    stats['active_live_bots'] = row[1]
                else:
                    stats['active_paper_bots'] = row[1]

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
    print(f"  Pro Users (ggbase): {stats['pro_users']} ({stats['active_subscribers']} active subscriptions)")
    print(f"  Free Users: {stats['free_users']}")
    print(f"Users with Bots: {stats['users_with_bots']} ({stats['users_with_bots']/stats['total_users']*100:.1f}%)")

    print("\n🤖 BOT STATISTICS")
    print("-" * 80)
    print(f"Total Bots Created: {stats['total_bots']}")
    print(f"  Active: {stats['active_bots']} ({stats['active_bots']/stats['total_bots']*100:.1f}%)")
    print(f"    Paper: {stats['active_paper_bots']}")
    print(f"    Live: {stats['active_live_bots']}")
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


def update_active_md(stats):
    """Update ACTIVE.md with current statistics."""
    active_path = Path(__file__).parent.parent / "ACTIVE.md"

    if not active_path.exists():
        print(f"❌ ERROR: ACTIVE.md not found at {active_path}")
        return False

    # Read current ACTIVE.md
    with open(active_path, 'r') as f:
        content = f.read()

    # Update the header section (first 6 lines)
    lines = content.split('\n')

    # Find the header section and update it
    new_header = [
        "# 🚀 ACTIVE - ggbots System Status",
        "",
        f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d')} (Automated status check)",
        f"**System Health**: 🟢 Production Live ({stats['total_users']}+ users, {stats['active_bots']}+ active bots)",
        "**Project Status**: Live application with complete Stripe monetization and Symphony live trading",
        ""
    ]

    # Find where the header ends (usually at the first "---" or "##")
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
        return True
    else:
        print("⚠️  WARNING: Could not find header section to update")
        return False


def main():
    parser = argparse.ArgumentParser(description='Check ggbots platform status')
    parser.add_argument('--update', action='store_true',
                       help='Update ACTIVE.md with current stats')
    parser.add_argument('--quiet', action='store_true',
                       help='Only show summary (for cron jobs)')
    args = parser.parse_args()

    try:
        stats = get_platform_stats()

        if args.quiet:
            # Just print summary for monitoring
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                  f"Users: {stats['total_users']} | "
                  f"Active Bots: {stats['active_bots']} | "
                  f"Trades (24h): {stats['trades_24h']} | "
                  f"Open Positions: {stats['open_positions']}")
        else:
            print_status_report(stats)

        if args.update:
            print("\n" + "=" * 80)
            update_active_md(stats)
            print("=" * 80)

        return 0

    except Exception as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
