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


def format_schema_markdown(schema):
    """Format database schema as markdown for README.md with comprehensive metadata."""
    lines = [
        "## 📊 Database Schema",
        "",
        "**Auto-generated schema reference** - Updated automatically by `scripts/status_check.py`",
        "",
        "**For architectural context and design decisions**, see [DOCS/DATABASE_CONTEXT.md](DOCS/DATABASE_CONTEXT.md).",
        "",
        f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "---",
        ""
    ]

    # Sort tables alphabetically
    for table_name in sorted(schema.keys()):
        table_data = schema[table_name]
        columns = table_data['columns']
        primary_keys = table_data['primary_keys']
        foreign_keys = table_data['foreign_keys']
        indexes = table_data['indexes']
        unique_constraints = table_data['unique_constraints']

        lines.append(f"### `{table_name}` ({len(columns)} columns)")
        lines.append("")

        # Primary Keys
        if primary_keys:
            pk_str = ", ".join([f"`{pk}`" for pk in primary_keys])
            lines.append(f"**Primary Key**: {pk_str}")
            lines.append("")

        # Foreign Keys
        if foreign_keys:
            lines.append("**Foreign Keys**:")
            for fk in foreign_keys:
                lines.append(f"- `{fk['column']}` → `{fk['foreign_table']}({fk['foreign_column']})`")
            lines.append("")

        # Indexes
        if indexes:
            lines.append("**Indexes**:")
            for idx in indexes:
                # Use columns field from new structure
                if 'columns' in idx:
                    lines.append(f"- `{idx['name']}` on ({idx['columns']})")
                else:
                    lines.append(f"- `{idx['name']}`")
            lines.append("")

        # Unique Constraints
        if unique_constraints:
            uc_str = ", ".join([f"`{uc}`" for uc in unique_constraints])
            lines.append(f"**Unique Constraints**: {uc_str}")
            lines.append("")

        # Column table
        lines.append("| Column | Type | Nullable | Default |")
        lines.append("|--------|------|----------|---------|")

        for col in columns:
            nullable = "✓" if col['nullable'] else ""
            default = str(col['default'])[:30] if col['default'] else ""
            lines.append(f"| `{col['name']}` | {col['type']} | {nullable} | {default} |")

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
    """Format domain models as markdown for README.md."""
    if not domain_models:
        return ""

    lines = [
        "## 🎯 Domain Models & Business Logic",
        "",
        "**Note**: Domain models add business logic, validation, and computed properties on top of database tables.",
        "",
        "**For schema design context**, see [DOCS/DATABASE_CONTEXT.md](DOCS/DATABASE_CONTEXT.md).",
        "",
        "---",
        ""
    ]

    for model in domain_models:
        lines.append(f"### `{model['class_name']}` (core/domain/{model['file']})")
        lines.append("")

        # Add docstring if exists
        if model['docstring']:
            # First line of docstring as purpose
            first_line = model['docstring'].split('\n')[0].strip()
            lines.append(f"**Purpose**: {first_line}")
            lines.append("")

        # Fields
        if model['fields']:
            lines.append("**Fields**:")
            for field in model['fields'][:10]:  # Limit to first 10 fields
                lines.append(f"- `{field['name']}: {field['type']}`")
            if len(model['fields']) > 10:
                lines.append(f"- ... and {len(model['fields']) - 10} more fields")
            lines.append("")

        # Properties (business logic)
        if model['properties']:
            lines.append("**Business Logic (@property methods)**:")
            for prop in model['properties']:
                if prop['doc']:
                    lines.append(f"- `{prop['name']}` - {prop['doc']}")
                else:
                    lines.append(f"- `{prop['name']}`")
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
    """Format BotConfig structure as markdown."""
    if not botconfig:
        return ""

    lines = [
        "## ⚙️ Configuration Structure (config_data JSONB)",
        "",
        "**Canonical source**: `core/config/models.py` (BotConfig Pydantic model)",
        "",
        "**Auto-generated** - Updated automatically by `scripts/status_check.py`",
        "",
        f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "---",
        ""
    ]

    # Add docstring if exists
    if botconfig['docstring']:
        first_para = botconfig['docstring'].split('\n\n')[0].strip()
        lines.append(f"**Purpose**: {first_para}")
        lines.append("")

    # Add fields table
    lines.append("### Configuration Fields")
    lines.append("")
    lines.append("| Field | Type | Default | Description |")
    lines.append("|-------|------|---------|-------------|")

    for field in botconfig['fields']:
        default_str = str(field['default']) if field['default'] is not None else ""
        if len(default_str) > 40:
            default_str = default_str[:37] + "..."
        desc_str = field['description'] if field['description'] else ""
        if len(desc_str) > 60:
            desc_str = desc_str[:57] + "..."

        lines.append(f"| `{field['name']}` | {field['type']} | {default_str} | {desc_str} |")

    lines.append("")
    lines.append("**Full validation rules**: See `core/config/models.py` for complete Pydantic model with field validators.")
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


def update_active_md(stats):
    """Update ACTIVE.md with current statistics."""
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
        f"- **Pro Users (ggbase)**: {stats['pro_users']} ({stats['active_subscribers']} active subscriptions)",
        f"- **Free Users**: {stats['free_users']}",
        f"- **Users with Bots**: {stats['users_with_bots']} ({stats['users_with_bots']/stats['total_users']*100:.1f}%)",
        "",
        "### Bot Statistics",
        f"- **Total Bots**: {stats['total_bots']}",
        f"- **Active Bots**: {stats['active_bots']} ({stats['active_bots']/stats['total_bots']*100:.1f}%)",
        f"  - Paper Trading: {stats['active_paper_bots']}",
        f"  - Live Trading: {stats['active_live_bots']}",
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
            print("UPDATING DOCUMENTATION...")
            print("=" * 80)
            print()

            # Update ACTIVE.md with stats
            update_active_md(stats)

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
