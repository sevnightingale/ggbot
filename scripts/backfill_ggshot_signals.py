#!/usr/bin/env python3
"""
Backfill Script: Populate market_data with Historical ggShot Signals

This script fetches the last 60 days of ggShot signals from Telegram and
stores them in the market_data table for use in autonomous trading extraction.

Usage:
    cd /home/sev/ggbot
    source .venv/bin/activate
    python scripts/backfill_ggshot_signals.py
"""

import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

# Add project root to path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from dotenv import load_dotenv
from telethon import TelegramClient
import json

# Load environment variables
load_dotenv()

# Import ggShot parser and database
from signals.ggshot_parser import GGShotParser
from core.common.db import get_db_connection
from core.common.logger import logger


class GGShotBackfiller:
    """Backfill market_data table with historical ggShot signals."""

    def __init__(self, days_back: int = 60):
        """Initialize the backfiller."""
        self.api_id = int(os.getenv('TG_API_ID'))
        self.api_hash = os.getenv('TG_API_HASH')
        self.channel_name = os.getenv('GGSHOT_CHANNEL', 'GGShot_Bot')
        self.parser = GGShotParser()
        self.days_back = days_back
        self.signals_source_id = None

        if not self.api_id or not self.api_hash:
            raise ValueError("TG_API_ID and TG_API_HASH environment variables are required")

    def _get_signals_source_id(self) -> str:
        """Get the UUID of 'signals_group_chats' data source."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT source_id FROM data_sources
                    WHERE name = 'signals_group_chats'
                """)
                result = cur.fetchone()
                if not result:
                    raise ValueError("signals_group_chats data source not found in database")
                return str(result[0])

    def _get_system_user_id(self) -> str:
        """Get or create a system user ID for universal signals."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Try to find a user with email 'system@ggbots.ai' (system account)
                cur.execute("""
                    SELECT user_id FROM user_profiles
                    WHERE user_id IN (
                        SELECT id FROM auth.users WHERE email = 'system@ggbots.ai'
                    )
                    LIMIT 1
                """)
                result = cur.fetchone()
                if result:
                    return str(result[0])

                # Fallback: use the first user in the system (for testing/development)
                # In production, you'd want to create a dedicated system user
                cur.execute("""
                    SELECT user_id FROM user_profiles
                    ORDER BY created_at ASC
                    LIMIT 1
                """)
                result = cur.fetchone()
                if result:
                    logger.warning(f"Using first user as system user for signals: {result[0]}")
                    return str(result[0])

                raise ValueError("No users found in database - cannot store signals")

    def _store_signal_in_db(self, signal_data: Dict[str, Any], message_date: datetime, system_user_id: str) -> bool:
        """
        Store a parsed signal in the market_data table.

        Args:
            signal_data: Parsed signal from GGShotParser
            message_date: Telegram message timestamp
            system_user_id: System user ID for universal signals

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Build data_points JSONB structure
            data_points = {
                "ggshot_signal": {
                    "direction": signal_data['direction'],
                    "entry_zone": signal_data['entry_zone'],
                    "stop_loss": signal_data['stop_loss'],
                    "take_profit": signal_data['target_1'],
                    "targets": signal_data['targets'],
                    "confidence": signal_data.get('strategy_accuracy', 0) / 100.0 if signal_data.get('strategy_accuracy') else None,
                    "strategy_accuracy": signal_data.get('strategy_accuracy'),
                    "trend_line": signal_data.get('trend_line')
                }
            }

            # Build raw_data JSONB structure
            raw_data = {
                "telegram_message": signal_data.get('raw_message', ''),
                "parsed_at": signal_data.get('parsed_at'),
                "source": "telegram",
                "message_date": message_date.isoformat()
            }

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Insert signal - use system_user_id and NULL config_id
                    # Multiple signals can exist for same symbol+timeframe at different times
                    cur.execute("""
                        INSERT INTO market_data (
                            user_id, symbol, timeframe, config_id, data_source,
                            data_points, raw_data, updated_at
                        ) VALUES (
                            %s, %s, %s, NULL, %s, %s, %s, %s
                        )
                    """, (
                        system_user_id,
                        signal_data['symbol'],
                        signal_data['timeframe'],
                        self.signals_source_id,
                        json.dumps(data_points),
                        json.dumps(raw_data),
                        message_date
                    ))

                    inserted = cur.rowcount > 0
                    conn.commit()

                    if inserted:
                        logger.info(f"Stored signal: {signal_data['symbol']} {signal_data['direction']} "
                                  f"({signal_data['timeframe']}) from {message_date.isoformat()}")

                    return inserted

        except Exception as e:
            logger.error(f"Error storing signal in database: {e}")
            return False

    async def backfill(self) -> Dict[str, Any]:
        """
        Fetch historical signals and populate database.

        Returns:
            Statistics dictionary with counts and results
        """
        # Get signals source ID first
        print(f"🔍 Looking up 'signals_group_chats' data source...")
        self.signals_source_id = self._get_signals_source_id()
        print(f"✅ Found data source ID: {self.signals_source_id}")

        # Get system user ID for storing signals
        print(f"🔍 Looking up system user ID...")
        system_user_id = self._get_system_user_id()
        print(f"✅ Using user ID for signals: {system_user_id}")

        # Calculate cutoff date
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days_back)
        print(f"📅 Fetching signals from {cutoff_date.strftime('%Y-%m-%d')} to now ({self.days_back} days)")

        # Connect to Telegram
        session_dir = '/home/sev/sessions'
        os.makedirs(session_dir, exist_ok=True)
        session_path = os.path.join(session_dir, 'ggshot_session')

        client = TelegramClient(session_path, self.api_id, self.api_hash)

        stats = {
            'messages_fetched': 0,
            'signals_parsed': 0,
            'signals_stored': 0,
            'signals_skipped': 0,
            'reports_skipped': 0,
            'parse_failures': 0,
            'symbols': set(),
            'timeframes': {},
            'directions': {}
        }

        try:
            print(f"\n🔌 Connecting to Telegram...")
            await client.start()

            print(f"🔍 Getting channel entity: {self.channel_name}")
            channel = await client.get_entity(self.channel_name)
            entity_name = getattr(channel, 'title', None) or getattr(channel, 'username', None) or str(channel.id)
            print(f"✅ Connected to: {entity_name} (ID: {channel.id})")

            print(f"\n📥 Fetching messages (this may take a minute)...")

            # Fetch messages in batches, stopping when we hit the cutoff date
            messages_batch_size = 100
            all_messages = []
            offset_id = 0

            while True:
                messages = await client.get_messages(
                    channel,
                    limit=messages_batch_size,
                    offset_id=offset_id
                )

                if not messages:
                    break

                # Filter messages within our date range
                in_range_messages = [m for m in messages if m.date >= cutoff_date]
                all_messages.extend(in_range_messages)

                # If we got fewer in-range messages than the batch size, we've gone past the cutoff
                if len(in_range_messages) < len(messages):
                    break

                # Update offset for next batch
                offset_id = messages[-1].id
                print(f"  Fetched {len(all_messages)} messages so far...")

                # Safety limit to avoid infinite loops
                if len(all_messages) >= 10000:
                    print(f"  ⚠️ Reached safety limit of 10,000 messages")
                    break

            stats['messages_fetched'] = len(all_messages)
            print(f"✅ Retrieved {len(all_messages)} messages from last {self.days_back} days")

            # Parse and store signals
            print(f"\n🔬 Parsing and storing signals...\n")

            for i, message in enumerate(all_messages, 1):
                if not message.message:
                    continue

                # Try to parse
                signal_data = self.parser.parse_signal(message.message)

                if signal_data:
                    stats['signals_parsed'] += 1

                    # Store in database
                    stored = self._store_signal_in_db(signal_data, message.date, system_user_id)

                    if stored:
                        stats['signals_stored'] += 1
                        stats['symbols'].add(signal_data['symbol'])

                        # Track timeframes
                        tf = signal_data['timeframe']
                        stats['timeframes'][tf] = stats['timeframes'].get(tf, 0) + 1

                        # Track directions
                        direction = signal_data['direction']
                        stats['directions'][direction] = stats['directions'].get(direction, 0) + 1

                        if i % 10 == 0 or stats['signals_stored'] % 10 == 0:
                            print(f"  [{i}/{len(all_messages)}] Stored: {signal_data['symbol']} "
                                  f"{signal_data['direction']} ({signal_data['timeframe']}) "
                                  f"- Total stored: {stats['signals_stored']}")
                    else:
                        stats['signals_skipped'] += 1

                else:
                    # Check if it's a report
                    if any(pattern in message.message.lower() for pattern in ['#report', 'daily report', 'performance', 'report on']):
                        stats['reports_skipped'] += 1
                    else:
                        stats['parse_failures'] += 1

            return stats

        finally:
            await client.disconnect()
            print(f"\n🔌 Disconnected from Telegram")

    def print_stats(self, stats: Dict[str, Any]):
        """Print backfill statistics."""
        print(f"\n" + "="*80)
        print(f"BACKFILL COMPLETE")
        print(f"="*80)
        print(f"Messages Fetched: {stats['messages_fetched']}")
        print(f"✅ Signals Parsed: {stats['signals_parsed']}")
        print(f"✅ Signals Stored in DB: {stats['signals_stored']}")
        print(f"⏭️  Signals Skipped (duplicates): {stats['signals_skipped']}")
        print(f"📊 Reports Skipped: {stats['reports_skipped']}")
        print(f"❌ Parse Failures: {stats['parse_failures']}")

        if stats['signals_stored'] > 0:
            print(f"\n" + "="*80)
            print(f"SIGNAL BREAKDOWN")
            print(f"="*80)
            print(f"Unique Symbols: {len(stats['symbols'])}")
            print(f"Symbols: {', '.join(sorted(stats['symbols']))[:200]}...")

            print(f"\nTimeframes:")
            for tf, count in sorted(stats['timeframes'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {tf}: {count}")

            print(f"\nDirections:")
            for direction, count in stats['directions'].items():
                print(f"  {direction}: {count}")

        print(f"\n✅ Historical signals are now available for autonomous trading extraction!")


async def main():
    """Main entry point."""
    try:
        print("="*80)
        print("ggShot Historical Signal Backfill")
        print("="*80)
        print()

        # Create backfiller for last 60 days
        backfiller = GGShotBackfiller(days_back=60)

        # Run backfill
        stats = await backfiller.backfill()

        # Print results
        backfiller.print_stats(stats)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
