"""
Backfill deposit/withdrawal activities from Hyperliquid ledger history.

One-time script that queries the full ledger history for each user with
a Hyperliquid wallet and creates deposit/withdrawal activity records
for any transfers not already logged.

Usage:
    python -m scripts.backfill_deposit_activities
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from hyperliquid.info import Info
from hyperliquid.utils import constants

from core.common.db import get_db_connection
from core.common.logger import logger


def backfill():
    log = logger.bind(script="backfill_deposits")
    info = Info(constants.MAINNET_API_URL, skip_ws=True)

    # Get all users with Hyperliquid wallets and their live config
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT up.user_id, up.hyperliquid_wallet_address, c.config_id
                FROM user_profiles up
                JOIN configurations c ON c.user_id = up.user_id
                WHERE up.hyperliquid_wallet_address IS NOT NULL
                  AND c.trading_mode = 'hyperliquid'
                  AND c.state != 'archived'
            """)
            users = cur.fetchall()

    log.info(f"Found {len(users)} users with Hyperliquid wallets")

    total_inserted = 0

    for user_id, wallet, config_id in users:
        log.info(f"Processing user {user_id[:8]}... wallet {wallet[:8]}...")

        try:
            # Query full ledger history (startTime=0 = all time)
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            ledger_updates = info.user_non_funding_ledger_updates(wallet, 0, now_ms)

            transfers = []
            for entry in ledger_updates:
                delta = entry.get("delta", {})
                ledger_type = delta.get("type", "")

                if ledger_type not in ("deposit", "withdraw"):
                    continue

                tx_hash = entry.get("hash", "")
                amount_str = delta.get("usdc", "0")
                amount = abs(float(amount_str))
                # Use the entry time if available, fallback to nonce
                entry_time = entry.get("time", 0)

                if amount == 0 or not tx_hash:
                    continue

                transfers.append({
                    'type': ledger_type,
                    'amount': amount,
                    'tx_hash': tx_hash,
                    'time_ms': entry_time,
                })

            log.info(f"  Found {len(transfers)} transfers in ledger")

            # Check which ones are already logged
            inserted = 0
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    for transfer in transfers:
                        # Dedup by tx_hash in details
                        cur.execute("""
                            SELECT 1 FROM activities
                            WHERE config_id = %s
                              AND activity_type IN ('deposit', 'withdrawal')
                              AND details->>'tx_hash' = %s
                            LIMIT 1
                        """, (config_id, transfer['tx_hash']))

                        if cur.fetchone():
                            continue

                        activity_type = 'deposit' if transfer['type'] == 'deposit' else 'withdrawal'
                        amount = transfer['amount']
                        summary = f"Deposited ${amount:.2f} USDC" if activity_type == 'deposit' else f"Withdrew ${amount:.2f} USDC"

                        # Convert millisecond timestamp to datetime
                        if transfer['time_ms'] > 0:
                            created_at = datetime.fromtimestamp(transfer['time_ms'] / 1000, tz=timezone.utc)
                        else:
                            created_at = datetime.now(timezone.utc)

                        cur.execute("""
                            INSERT INTO activities
                            (config_id, user_id, activity_type, activity_source, summary, details,
                             importance, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            config_id,
                            user_id,
                            activity_type,
                            'hyperliquid_backfill',
                            summary,
                            '{"amount_usdc": ' + str(amount) + ', "tx_hash": "' + transfer['tx_hash'] + '", "ledger_type": "' + transfer['type'] + '"}',
                            8,
                            created_at,
                        ))
                        inserted += 1

                    conn.commit()

            total_inserted += inserted
            log.info(f"  Inserted {inserted} new activities")

        except Exception as e:
            log.error(f"  Failed for user {user_id[:8]}...: {e}")

    log.info(f"Backfill complete. Total inserted: {total_inserted}")


if __name__ == "__main__":
    backfill()
