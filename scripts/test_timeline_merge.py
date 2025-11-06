#!/usr/bin/env python3
"""
Test script to explore merging balance-series with activities for timeline chart.

This script:
1. Fetches balance-series (P&L snapshots at trade closes)
2. Fetches all activities (thoughts, signals, trades, etc.)
3. Merges them chronologically with carry-forward P&L
4. Shows what the final chart data would look like

Usage:
    source .venv/bin/activate
    python scripts/test_timeline_merge.py <config_id>
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
import aiohttp

# Load environment variables
load_dotenv()

# ANSI colors for pretty output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}\n")


def print_success(msg: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_error(msg: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_info(key: str, value: Any):
    """Print key-value pair"""
    print(f"{Colors.CYAN}{key:40}{Colors.END}: {Colors.BOLD}{value}{Colors.END}")


async def fetch_balance_series(config_id: str) -> List[Dict]:
    """Fetch balance series (P&L snapshots)"""
    print_section("FETCHING BALANCE SERIES")

    # In production this would use auth token
    # For now just test the endpoint structure
    url = f"http://localhost:8000/api/v2/activities/{config_id}/balance-series"
    params = {"mode": "pnl"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print_error(f"Balance series API returned {resp.status}: {error_text}")
                    return []

                data = await resp.json()
                balance_series = data.get('balance_series', [])

                print_success(f"Fetched {len(balance_series)} balance points")

                if balance_series:
                    print(f"\n{Colors.YELLOW}Sample balance point:{Colors.END}")
                    print_info("  Keys", list(balance_series[0].keys()))
                    print_info("  Timestamp", balance_series[0].get('timestamp'))
                    print_info("  Balance", balance_series[0].get('balance'))

                return balance_series

    except Exception as e:
        print_error(f"Failed to fetch balance series: {e}")
        return []


async def fetch_activities(config_id: str) -> List[Dict]:
    """Fetch all activities"""
    print_section("FETCHING ACTIVITIES")

    url = f"http://localhost:8000/api/v2/activities/{config_id}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print_error(f"Activities API returned {resp.status}: {error_text}")
                    return []

                data = await resp.json()
                activities = data.get('activities', [])

                print_success(f"Fetched {len(activities)} activities")

                # Show activity type breakdown
                type_counts = {}
                for activity in activities:
                    activity_type = activity.get('type', 'unknown')
                    type_counts[activity_type] = type_counts.get(activity_type, 0) + 1

                print(f"\n{Colors.YELLOW}Activity type breakdown:{Colors.END}")
                for activity_type, count in sorted(type_counts.items()):
                    print_info(f"  {activity_type}", count)

                if activities:
                    print(f"\n{Colors.YELLOW}Sample activity:{Colors.END}")
                    print_info("  Keys", list(activities[0].keys()))
                    print_info("  Type", activities[0].get('type'))
                    print_info("  Timestamp", activities[0].get('timestamp'))

                return activities

    except Exception as e:
        print_error(f"Failed to fetch activities: {e}")
        return []


def merge_timeline_data(balance_series: List[Dict], activities: List[Dict]) -> List[Dict]:
    """
    Merge balance series with activities using carry-forward logic.

    Returns list of chart points with:
    - timestamp: ISO timestamp
    - value: P&L value (carried forward)
    - type: activity type
    - data: original activity data
    """
    print_section("MERGING DATA")

    # Create lookup map of balance by timestamp
    balance_map = {}
    for point in balance_series:
        timestamp = point['timestamp']
        balance = point['balance']
        balance_map[timestamp] = balance
        print(f"{Colors.CYAN}Balance point:{Colors.END} {timestamp[:19]} -> ${balance:.2f}")

    # Sort all activities by timestamp
    sorted_activities = sorted(activities, key=lambda x: x['timestamp'])

    # Carry forward P&L through activities
    chart_points = []
    current_pnl = 0.0  # Start at 0 for P&L mode

    print(f"\n{Colors.YELLOW}Merging chronologically:{Colors.END}\n")

    for activity in sorted_activities:
        timestamp = activity['timestamp']
        activity_type = activity.get('type', 'unknown')

        # Check if this activity has a balance point
        if timestamp in balance_map:
            current_pnl = balance_map[timestamp]
            marker = f"{Colors.GREEN}[P&L UPDATE]{Colors.END}"
        else:
            marker = f"{Colors.BLUE}[CARRY FWD]{Colors.END}"

        chart_point = {
            'timestamp': timestamp,
            'value': current_pnl,
            'type': activity_type,
            'data': activity
        }

        chart_points.append(chart_point)

        # Print sample
        if len(chart_points) <= 10 or timestamp in balance_map:
            print(f"{marker} {timestamp[:19]} | {activity_type:20} | P&L: ${current_pnl:8.2f}")

    print_success(f"\nCreated {len(chart_points)} chart points from {len(activities)} activities")

    return chart_points


def analyze_time_spacing(chart_points: List[Dict]):
    """Analyze time spacing between points"""
    print_section("TIME SPACING ANALYSIS")

    if len(chart_points) < 2:
        print_error("Not enough points to analyze spacing")
        return

    time_diffs = []
    for i in range(len(chart_points) - 1):
        t1 = datetime.fromisoformat(chart_points[i]['timestamp'].replace('Z', '+00:00'))
        t2 = datetime.fromisoformat(chart_points[i+1]['timestamp'].replace('Z', '+00:00'))
        diff_seconds = (t2 - t1).total_seconds()
        time_diffs.append(diff_seconds)

    avg_diff = sum(time_diffs) / len(time_diffs)
    min_diff = min(time_diffs)
    max_diff = max(time_diffs)

    print_info("Total points", len(chart_points))
    print_info("Average spacing", f"{avg_diff:.1f} seconds ({avg_diff/60:.1f} minutes)")
    print_info("Min spacing", f"{min_diff:.1f} seconds ({min_diff/60:.1f} minutes)")
    print_info("Max spacing", f"{max_diff:.1f} seconds ({max_diff/3600:.1f} hours)")

    # Show first few gaps
    print(f"\n{Colors.YELLOW}First 5 time gaps:{Colors.END}")
    for i in range(min(5, len(time_diffs))):
        t1 = chart_points[i]['timestamp'][:19]
        t2 = chart_points[i+1]['timestamp'][:19]
        gap = time_diffs[i]
        print(f"  {t1} → {t2}: {gap:.0f}s ({gap/60:.1f}m)")


async def main():
    """Run the test"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║              TIMELINE DATA MERGE TEST SCRIPT                               ║")
    print("║  Testing merge of balance-series + activities for TradingView chart       ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")

    # Get config_id from command line
    if len(sys.argv) < 2:
        print_error("Usage: python scripts/test_timeline_merge.py <config_id>")
        print(f"\n{Colors.YELLOW}Example:{Colors.END}")
        print("  python scripts/test_timeline_merge.py bb2560fd-b053-464f-8a58-8e254e4d36fa")
        sys.exit(1)

    config_id = sys.argv[1]
    print_info("Testing config", config_id)

    # Fetch both datasets
    balance_series = await fetch_balance_series(config_id)
    activities = await fetch_activities(config_id)

    if not balance_series:
        print_error("No balance series data - cannot proceed")
        return

    if not activities:
        print_error("No activities data - cannot proceed")
        return

    # Merge the data
    chart_points = merge_timeline_data(balance_series, activities)

    # Analyze time spacing
    analyze_time_spacing(chart_points)

    # Summary
    print_section("SUMMARY")
    print_info("Balance points (P&L changes)", len(balance_series))
    print_info("Total activities", len(activities))
    print_info("Final chart points", len(chart_points))
    print_info("Ratio", f"{len(chart_points) / len(balance_series):.1f}x more points")

    print(f"\n{Colors.GREEN}✓ Test completed successfully!{Colors.END}")
    print(f"\n{Colors.YELLOW}Next steps:{Colors.END}")
    print("  1. Review the data structures above")
    print("  2. Verify carry-forward logic is correct")
    print("  3. Implement in tv-timeline.tsx component")


if __name__ == '__main__':
    asyncio.run(main())
