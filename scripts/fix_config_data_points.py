#!/usr/bin/env python3
"""
Data Point Migration Script

Fixes misconfigured bot configurations:
1. Technical analysis display names → backend names (e.g., 'Bollinger Bands' → 'BB')
2. market_intelligence category → proper category structure
3. Case fixes for macro data points (e.g., 'VIX' → 'vix')

Run with: python scripts/fix_config_data_points.py [--dry-run]
"""

import sys
import json
import argparse
from typing import Dict, Any, List, Tuple
from core.common.db import get_db_connection
from core.common.logger import logger

# Technical analysis display name → backend name mappings
TECH_DISPLAY_TO_BACKEND = {
    'Bollinger Bands': 'BB',
    'Bollinger Band Width': 'BBW',
    'Williams %R': 'Williams_R',
    'Donchian Channels': 'DC',
    'Parabolic SAR': 'PSAR',
    'Keltner Channels': 'KC',
    'Stochastic Oscillator': 'Stochastic',
    'Aroon Indicator': 'Aroon',
    'Vortex Indicator': 'Vortex',
}

# Market intelligence data point → correct category mapping
MARKET_INTEL_TO_CATEGORY = {
    # Derivatives
    'btc_funding_rate': 'derivatives_leverage',
    'eth_funding_rate': 'derivatives_leverage',
    'BTC Funding Rate': 'derivatives_leverage',
    'ETH Funding Rate': 'derivatives_leverage',
    # Macro economics (also fix case)
    'VIX': 'macro_economics',
    'vix': 'macro_economics',
    'DXY': 'macro_economics',
    'dxy': 'macro_economics',
    'CPI': 'macro_economics',
    'cpi': 'macro_economics',
    'NFP': 'macro_economics',
    'nfp': 'macro_economics',
    # Sentiment
    'twitter_sentiment': 'sentiment_social',
    'Twitter Sentiment': 'sentiment_social',
    'Twitter_Sentiment': 'sentiment_social',
    # On-chain
    'whale_activity': 'onchain_analytics',
    'Whale Activity': 'onchain_analytics',
    'btc_tvl': 'onchain_analytics',
    # News
    'crypto_news': 'news_regulatory',
    'Crypto News Feed': 'news_regulatory',
    'Crypto_News_Feed': 'news_regulatory',
}

# Market intel display name → backend name (for normalization)
MARKET_INTEL_DISPLAY_TO_BACKEND = {
    'VIX': 'vix',
    'DXY': 'dxy',
    'CPI': 'cpi',
    'NFP': 'nfp',
    'BTC Funding Rate': 'btc_funding_rate',
    'ETH Funding Rate': 'eth_funding_rate',
    'Twitter Sentiment': 'twitter_sentiment',
    'Twitter_Sentiment': 'twitter_sentiment',
    'Whale Activity': 'whale_activity',
    'Crypto News Feed': 'crypto_news',
    'Crypto_News_Feed': 'crypto_news',
}


def fix_technical_analysis(data_points: List[str]) -> Tuple[List[str], List[str]]:
    """
    Fix technical analysis data points by converting display names to backend names.

    Returns:
        Tuple of (fixed_data_points, changes_made)
    """
    fixed = []
    changes = []

    for point in data_points:
        if point in TECH_DISPLAY_TO_BACKEND:
            backend_name = TECH_DISPLAY_TO_BACKEND[point]
            fixed.append(backend_name)
            changes.append(f"'{point}' → '{backend_name}'")
        else:
            fixed.append(point)

    return fixed, changes


def fix_market_intelligence(market_intel_points: List[str], existing_sources: Dict) -> Tuple[Dict, List[str]]:
    """
    Transform flat market_intelligence into proper category structure.

    Args:
        market_intel_points: List of data points from market_intelligence category
        existing_sources: Current selected_data_sources dict

    Returns:
        Tuple of (updated_sources_dict, changes_made)
    """
    changes = []

    # Build category buckets
    categories = {
        'derivatives_leverage': [],
        'macro_economics': [],
        'sentiment_social': [],
        'onchain_analytics': [],
        'news_regulatory': [],
    }

    for point in market_intel_points:
        # Determine which category this point belongs to
        category = MARKET_INTEL_TO_CATEGORY.get(point)

        if category:
            # Normalize the point name (fix case, display → backend)
            backend_name = MARKET_INTEL_DISPLAY_TO_BACKEND.get(point, point)
            categories[category].append(backend_name)
            if point != backend_name:
                changes.append(f"'{point}' → '{backend_name}' in {category}")
            else:
                changes.append(f"'{point}' moved to {category}")
        else:
            # Unknown point - log warning but don't lose data
            changes.append(f"WARNING: Unknown point '{point}' - skipped")

    # Merge into existing sources
    updated_sources = {k: v for k, v in existing_sources.items() if k != 'market_intelligence'}

    for category, points in categories.items():
        if points:
            # Deduplicate and merge with any existing points in this category
            existing_points = updated_sources.get(category, {}).get('data_points', [])
            merged_points = list(set(existing_points + points))

            updated_sources[category] = {
                'data_points': merged_points,
                'timeframes': ['5m', '15m', '30m', '1h', '4h', '1d', '1w']
            }

    return updated_sources, changes


def fix_legacy_categories(sources: Dict) -> Tuple[Dict, List[str]]:
    """
    Fix legacy category names and display names within them.

    Legacy categories: news, sentiment, on_chain, derivatives
    """
    changes = []

    # Category renames
    category_renames = {
        'news': 'news_regulatory',
        'news_events': 'news_regulatory',
        'sentiment': 'sentiment_social',
        'on_chain': 'onchain_analytics',
        'derivatives': 'derivatives_leverage',
    }

    updated_sources = {}

    for category, config in sources.items():
        target_category = category_renames.get(category, category)

        if category != target_category:
            changes.append(f"Category '{category}' → '{target_category}'")

        if target_category == 'technical_analysis':
            # Already handled
            updated_sources[target_category] = config
            continue

        # Fix data points within the category
        data_points = config.get('data_points', [])
        fixed_points = []

        for point in data_points:
            backend_name = MARKET_INTEL_DISPLAY_TO_BACKEND.get(point, point)
            if point != backend_name:
                changes.append(f"'{point}' → '{backend_name}'")
            fixed_points.append(backend_name)

        updated_sources[target_category] = {
            'data_points': fixed_points,
            'timeframes': config.get('timeframes', ['5m', '15m', '30m', '1h', '4h', '1d', '1w'])
        }

    return updated_sources, changes


def process_config(config_data: Dict) -> Tuple[Dict, List[str]]:
    """
    Process a single config and return the fixed version.

    Returns:
        Tuple of (fixed_config_data, all_changes_made)
    """
    all_changes = []

    # Get extraction config
    extraction = config_data.get('extraction', {})
    selected_sources = extraction.get('selected_data_sources', {})

    if not selected_sources:
        return config_data, []

    updated_sources = dict(selected_sources)

    # Fix 1: Technical analysis display names
    if 'technical_analysis' in updated_sources:
        tech_points = updated_sources['technical_analysis'].get('data_points', [])
        fixed_tech, tech_changes = fix_technical_analysis(tech_points)

        if tech_changes:
            updated_sources['technical_analysis']['data_points'] = fixed_tech
            all_changes.extend([f"[tech] {c}" for c in tech_changes])

    # Fix 2: market_intelligence category
    if 'market_intelligence' in updated_sources:
        market_intel_points = updated_sources['market_intelligence'].get('data_points', [])
        updated_sources, intel_changes = fix_market_intelligence(market_intel_points, updated_sources)
        all_changes.extend([f"[market_intel] {c}" for c in intel_changes])

    # Fix 3: Legacy category names and display names within
    updated_sources, legacy_changes = fix_legacy_categories(updated_sources)
    all_changes.extend([f"[legacy] {c}" for c in legacy_changes])

    # Build updated config
    if all_changes:
        updated_config = dict(config_data)
        updated_config['extraction'] = dict(extraction)
        updated_config['extraction']['selected_data_sources'] = updated_sources
        return updated_config, all_changes

    return config_data, []


def run_migration(dry_run: bool = True):
    """
    Run the migration on all configurations.

    Args:
        dry_run: If True, don't actually update the database
    """
    logger.info(f"Starting data point migration (dry_run={dry_run})")

    stats = {
        'total_configs': 0,
        'configs_with_issues': 0,
        'configs_fixed': 0,
        'total_changes': 0,
    }

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Fetch all configurations
            cur.execute("""
                SELECT config_id, config_name, config_data, state
                FROM configurations
                WHERE config_data IS NOT NULL
                ORDER BY created_at DESC
            """)

            rows = cur.fetchall()
            stats['total_configs'] = len(rows)

            print(f"\n{'='*80}")
            print(f"DATA POINT MIGRATION {'(DRY RUN)' if dry_run else '(LIVE)'}")
            print(f"{'='*80}")
            print(f"Total configurations to process: {len(rows)}\n")

            configs_to_update = []

            for row in rows:
                config_id = str(row[0])
                config_name = row[1] or 'Unnamed'
                config_data = row[2] if isinstance(row[2], dict) else json.loads(row[2]) if row[2] else {}
                state = row[3]

                # Process config
                fixed_config, changes = process_config(config_data)

                if changes:
                    stats['configs_with_issues'] += 1
                    stats['total_changes'] += len(changes)

                    print(f"\n{'🚨' if state == 'active' else '⚠️'} {config_name} ({config_id[:8]}...) [{state}]")
                    for change in changes:
                        print(f"   • {change}")

                    configs_to_update.append((config_id, fixed_config))

            print(f"\n{'='*80}")
            print("SUMMARY")
            print(f"{'='*80}")
            print(f"Total configs scanned: {stats['total_configs']}")
            print(f"Configs with issues:   {stats['configs_with_issues']}")
            print(f"Total changes needed:  {stats['total_changes']}")

            if not dry_run and configs_to_update:
                print(f"\n{'='*80}")
                print("APPLYING FIXES...")
                print(f"{'='*80}")

                for config_id, fixed_config in configs_to_update:
                    try:
                        cur.execute("""
                            UPDATE configurations
                            SET config_data = %s, updated_at = NOW()
                            WHERE config_id = %s
                        """, (json.dumps(fixed_config), config_id))
                        stats['configs_fixed'] += 1
                        print(f"   ✅ Fixed {config_id[:8]}...")
                    except Exception as e:
                        print(f"   ❌ Failed {config_id[:8]}...: {e}")

                conn.commit()
                print(f"\n✅ Successfully fixed {stats['configs_fixed']} configurations")
            elif dry_run and configs_to_update:
                print(f"\n⚠️  DRY RUN - No changes made. Run with --apply to fix {len(configs_to_update)} configs.")
            else:
                print("\n✅ No fixes needed!")


def main():
    parser = argparse.ArgumentParser(description='Fix misconfigured bot data points')
    parser.add_argument('--apply', action='store_true', help='Actually apply fixes (default is dry run)')
    args = parser.parse_args()

    dry_run = not args.apply
    run_migration(dry_run=dry_run)


if __name__ == '__main__':
    main()
