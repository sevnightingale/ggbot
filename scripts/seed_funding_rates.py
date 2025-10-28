#!/usr/bin/env python3
"""
Seed database with funding rate data source and data points.

This script adds:
- 1 new data source: crypto_derivatives
- 2 new data points: BTC funding rate, ETH funding rate

Part of Market Intelligence Phase 1: Free Quick Wins
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.common.db import get_db_connection
from core.common.logger import logger

log = logger.bind(script="seed_funding_rates")


def seed_funding_rates():
    """Seed crypto_derivatives data source and funding rate data points."""

    log.info("Starting funding rates database seeding...")

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Step 1: Insert crypto_derivatives data source
                log.info("Inserting crypto_derivatives data source...")
                cur.execute("""
                    INSERT INTO data_sources (name, display_name, description, enabled, requires_premium)
                    VALUES (
                        'crypto_derivatives',
                        'Crypto Derivatives',
                        'Perpetual futures funding rates and leverage metrics showing long/short positioning. Extreme funding rates indicate overleveraged positions and potential liquidation cascades.',
                        TRUE,
                        FALSE
                    )
                    ON CONFLICT (name) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        description = EXCLUDED.description,
                        enabled = EXCLUDED.enabled,
                        updated_at = NOW()
                    RETURNING source_id, name, display_name
                """)

                result = cur.fetchone()
                source_id, name, display_name = result
                log.info(f"✅ Data source created/updated: {display_name} (ID: {source_id})")

                # Step 2: Insert BTC funding rate
                log.info("Inserting BTC funding rate data point...")
                cur.execute("""
                    INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
                    VALUES (
                        %s,
                        'btc_funding_rate',
                        'BTC Funding Rate',
                        'Binance perpetual futures funding rate for BTC/USDT. Positive rates indicate long-heavy positioning (longs pay shorts), negative rates indicate short-heavy positioning. Extreme rates (>±1%%) signal overleveraged positions and liquidation risk.',
                        ARRAY['funding_rate_btc']::TEXT[],
                        FALSE,
                        TRUE,
                        0
                    )
                    ON CONFLICT (source_id, name) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        description = EXCLUDED.description,
                        config_values = EXCLUDED.config_values,
                        enabled = EXCLUDED.enabled,
                        sort_order = EXCLUDED.sort_order,
                        updated_at = NOW()
                    RETURNING data_point_id, display_name
                """, (source_id,))

                point_id, point_name = cur.fetchone()
                log.info(f"✅ Data point created/updated: {point_name} (ID: {point_id})")

                # Step 3: Insert ETH funding rate
                log.info("Inserting ETH funding rate data point...")
                cur.execute("""
                    INSERT INTO data_points (source_id, name, display_name, description, config_values, requires_premium, enabled, sort_order)
                    VALUES (
                        %s,
                        'eth_funding_rate',
                        'ETH Funding Rate',
                        'Binance perpetual futures funding rate for ETH/USDT. Positive rates indicate long-heavy positioning, negative rates indicate short-heavy positioning. Useful for detecting overcrowded trades and potential reversals.',
                        ARRAY['funding_rate_eth']::TEXT[],
                        FALSE,
                        TRUE,
                        1
                    )
                    ON CONFLICT (source_id, name) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        description = EXCLUDED.description,
                        config_values = EXCLUDED.config_values,
                        enabled = EXCLUDED.enabled,
                        sort_order = EXCLUDED.sort_order,
                        updated_at = NOW()
                    RETURNING data_point_id, display_name
                """, (source_id,))

                point_id, point_name = cur.fetchone()
                log.info(f"✅ Data point created/updated: {point_name} (ID: {point_id})")

                # Commit changes
                conn.commit()

                # Step 4: Verify insertion
                log.info("Verifying insertion...")
                cur.execute("""
                    SELECT
                        ds.name as source_name,
                        ds.display_name as source_display,
                        ds.enabled as source_enabled,
                        ds.requires_premium as source_premium,
                        dp.name as point_name,
                        dp.display_name as point_display,
                        dp.config_values,
                        dp.enabled as point_enabled,
                        dp.requires_premium as point_premium
                    FROM data_sources ds
                    JOIN data_points dp ON ds.source_id = dp.source_id
                    WHERE ds.name = 'crypto_derivatives'
                    ORDER BY dp.sort_order
                """)

                rows = cur.fetchall()
                log.info(f"\n{'='*80}")
                log.info("DATABASE SEEDING SUCCESSFUL!")
                log.info(f"{'='*80}")
                log.info(f"Data Source: {rows[0][1]}")
                log.info(f"Enabled: {rows[0][2]}, Premium: {rows[0][3]}")
                log.info(f"\nData Points:")
                for row in rows:
                    log.info(f"  - {row[5]}: {row[6]} (enabled={row[7]}, premium={row[8]})")
                log.info(f"{'='*80}\n")

                log.info("✅ Funding rates successfully seeded!")
                log.info("Next steps:")
                log.info("  1. Test adapter: python scripts/test_funding_adapter.py")
                log.info("  2. Check frontend: Data should auto-populate in MarketDataSelector")
                log.info("  3. Integrate into decision engine")

                return True

    except Exception as e:
        log.error(f"❌ Failed to seed funding rates: {e}")
        raise


if __name__ == "__main__":
    seed_funding_rates()
