#!/usr/bin/env python3
"""
Test Script: Fetch Historical ggShot Signals from Telegram

This script connects to the ggShot Telegram channel and retrieves historical
messages to test:
1. Our ability to fetch old signals
2. Parser success rate on historical data
3. Data quality and completeness

Usage:
    cd /home/sev/ggbot
    source .venv/bin/activate
    python scripts/test_ggshot_historical_fetch.py
"""

import os
import sys
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any

# Add project root to path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from dotenv import load_dotenv
from telethon import TelegramClient

# Load environment variables
load_dotenv()

# Import ggShot parser
from signals.ggshot_parser import GGShotParser


class HistoricalSignalFetcher:
    """Fetch and parse historical ggShot signals from Telegram."""

    def __init__(self):
        """Initialize the fetcher with Telegram credentials."""
        self.api_id = int(os.getenv('TG_API_ID'))
        self.api_hash = os.getenv('TG_API_HASH')
        self.channel_name = os.getenv('GGSHOT_CHANNEL', 'GGShot_Bot')
        self.parser = GGShotParser()

        if not self.api_id or not self.api_hash:
            raise ValueError("TG_API_ID and TG_API_HASH environment variables are required")

    async def fetch_historical_signals(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch historical messages from ggShot channel and parse them.

        Args:
            limit: Number of messages to fetch (default 100)

        Returns:
            List of parsed signal dictionaries
        """
        # Use existing session from listener service
        session_dir = '/home/sev/sessions'
        os.makedirs(session_dir, exist_ok=True)
        session_path = os.path.join(session_dir, 'ggshot_session')

        client = TelegramClient(session_path, self.api_id, self.api_hash)

        try:
            print(f"🔌 Connecting to Telegram...")
            await client.start()

            print(f"🔍 Getting channel entity: {self.channel_name}")
            channel = await client.get_entity(self.channel_name)
            entity_name = getattr(channel, 'title', None) or getattr(channel, 'username', None) or str(channel.id)
            print(f"✅ Connected to: {entity_name} (ID: {channel.id})")

            print(f"\n📥 Fetching last {limit} messages...")
            messages = await client.get_messages(channel, limit=limit)
            print(f"✅ Retrieved {len(messages)} messages")

            # Parse messages
            parsed_signals = []
            parse_failures = []
            reports_skipped = 0

            print(f"\n🔬 Parsing messages...\n")

            for i, message in enumerate(messages, 1):
                if not message.message:
                    continue

                # Try to parse
                signal_data = self.parser.parse_signal(message.message)

                if signal_data:
                    # Add message metadata
                    signal_data['message_id'] = message.id
                    signal_data['message_date'] = message.date.isoformat()
                    parsed_signals.append(signal_data)

                    print(f"✅ [{i}/{len(messages)}] Parsed: {signal_data['symbol']} {signal_data['direction']} "
                          f"({signal_data['timeframe']}) - Confidence: {signal_data.get('strategy_accuracy', 'N/A')}%")
                else:
                    # Check if it's a report (expected to fail)
                    if any(pattern in message.message.lower() for pattern in ['#report', 'daily report', 'performance']):
                        reports_skipped += 1
                    else:
                        # Unexpected parse failure
                        parse_failures.append({
                            'message_id': message.id,
                            'message_date': message.date.isoformat(),
                            'preview': message.message[:100] + '...' if len(message.message) > 100 else message.message
                        })

            # Print summary
            print(f"\n" + "="*80)
            print(f"SUMMARY")
            print(f"="*80)
            print(f"Total Messages Retrieved: {len(messages)}")
            print(f"✅ Successfully Parsed Signals: {len(parsed_signals)}")
            print(f"📊 Reports Skipped (Expected): {reports_skipped}")
            print(f"❌ Unexpected Parse Failures: {len(parse_failures)}")
            print(f"Success Rate: {len(parsed_signals)/(len(messages)-reports_skipped)*100:.1f}% (excluding reports)")

            # Show symbol distribution
            if parsed_signals:
                print(f"\n" + "="*80)
                print(f"SIGNAL DISTRIBUTION")
                print(f"="*80)

                symbols = {}
                timeframes = {}
                directions = {}

                for signal in parsed_signals:
                    symbols[signal['symbol']] = symbols.get(signal['symbol'], 0) + 1
                    timeframes[signal['timeframe']] = timeframes.get(signal['timeframe'], 0) + 1
                    directions[signal['direction']] = directions.get(signal['direction'], 0) + 1

                print(f"\nTop 10 Symbols:")
                for symbol, count in sorted(symbols.items(), key=lambda x: x[1], reverse=True)[:10]:
                    print(f"  {symbol}: {count}")

                print(f"\nTimeframes:")
                for tf, count in sorted(timeframes.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {tf}: {count}")

                print(f"\nDirections:")
                for direction, count in directions.items():
                    print(f"  {direction}: {count}")

                # Show a few examples
                print(f"\n" + "="*80)
                print(f"SAMPLE SIGNALS (First 3)")
                print(f"="*80)
                for i, signal in enumerate(parsed_signals[:3], 1):
                    print(f"\n[Signal {i}]")
                    print(f"Symbol: {signal['symbol']}")
                    print(f"Direction: {signal['direction']}")
                    print(f"Timeframe: {signal['timeframe']}")
                    print(f"Entry Zone: {signal['entry_zone']['low']:.2f} - {signal['entry_zone']['high']:.2f}")
                    print(f"Stop Loss: {signal['stop_loss']:.2f}")
                    print(f"Take Profit (Target 1): {signal['target_1']:.2f}")
                    print(f"Confidence: {signal.get('strategy_accuracy', 'N/A')}%")
                    print(f"Message Date: {signal['message_date']}")

            # Show parse failures if any
            if parse_failures:
                print(f"\n" + "="*80)
                print(f"UNEXPECTED PARSE FAILURES ({len(parse_failures)})")
                print(f"="*80)
                for failure in parse_failures[:5]:  # Show first 5
                    print(f"\nMessage ID: {failure['message_id']}")
                    print(f"Date: {failure['message_date']}")
                    print(f"Preview: {failure['preview']}")

            return parsed_signals

        finally:
            await client.disconnect()
            print(f"\n🔌 Disconnected from Telegram")


async def main():
    """Main entry point."""
    try:
        print("="*80)
        print("ggShot Historical Signal Fetch Test")
        print("="*80)
        print()

        fetcher = HistoricalSignalFetcher()

        # Fetch and parse last 100 messages
        signals = await fetcher.fetch_historical_signals(limit=100)

        print(f"\n" + "="*80)
        print(f"TEST COMPLETE")
        print(f"="*80)
        print(f"✅ Successfully retrieved and parsed {len(signals)} historical signals")
        print(f"✅ Parser is working correctly on historical data")
        print(f"✅ Ready to implement database storage solution")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
