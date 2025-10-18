#!/usr/bin/env python3
"""
Migration script to fix invalid config values that don't meet Pydantic validation.

Fixes:
1. max_position_percent < 1.0 -> set to 1.0
2. max_position_percent > 25.0 -> set to 25.0
3. max_positions < 1 -> set to 1
4. max_positions > 20 -> set to 20
5. max_daily_loss_usd > 5000 -> set to 5000
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from core.common.db import get_db_connection
from core.common.logger import logger


def fix_configs():
    """Fix all invalid configs in database."""
    fixed_count = 0
    total_count = 0

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get all configs
            cur.execute("SELECT config_id, config_data FROM configurations")
            configs = cur.fetchall()
            total_count = len(configs)

            logger.info(f"Checking {total_count} configurations...")

            for config_id, config_data in configs:
                modified = False

                # Fix max_position_percent
                if 'trading' in config_data and 'position_sizing' in config_data['trading']:
                    pos_sizing = config_data['trading']['position_sizing']

                    if 'max_position_percent' in pos_sizing:
                        old_val = pos_sizing['max_position_percent']

                        if old_val < 1.0:
                            pos_sizing['max_position_percent'] = 1.0
                            logger.info(f"Config {config_id[:8]}: max_position_percent {old_val} -> 1.0")
                            modified = True
                        elif old_val > 25.0:
                            pos_sizing['max_position_percent'] = 25.0
                            logger.info(f"Config {config_id[:8]}: max_position_percent {old_val} -> 25.0")
                            modified = True

                # Fix max_positions and max_daily_loss_usd
                if 'trading' in config_data and 'risk_management' in config_data['trading']:
                    risk_mgmt = config_data['trading']['risk_management']

                    if 'max_positions' in risk_mgmt:
                        old_val = risk_mgmt['max_positions']

                        if old_val < 1:
                            risk_mgmt['max_positions'] = 1
                            logger.info(f"Config {config_id[:8]}: max_positions {old_val} -> 1")
                            modified = True
                        elif old_val > 20:
                            risk_mgmt['max_positions'] = 20
                            logger.info(f"Config {config_id[:8]}: max_positions {old_val} -> 20")
                            modified = True

                    if 'max_daily_loss_usd' in risk_mgmt:
                        old_val = risk_mgmt['max_daily_loss_usd']

                        if old_val is not None and old_val > 5000:
                            risk_mgmt['max_daily_loss_usd'] = 5000
                            logger.info(f"Config {config_id[:8]}: max_daily_loss_usd {old_val} -> 5000")
                            modified = True

                # Update if modified
                if modified:
                    cur.execute("""
                        UPDATE configurations
                        SET config_data = %s, updated_at = NOW()
                        WHERE config_id = %s
                    """, (json.dumps(config_data), config_id))
                    fixed_count += 1

            if fixed_count > 0:
                conn.commit()
                logger.info(f"✅ Fixed {fixed_count} out of {total_count} configurations")
            else:
                logger.info(f"✅ All {total_count} configurations are valid!")

    return fixed_count


if __name__ == "__main__":
    logger.info("Starting config validation fix...")
    fixed = fix_configs()
    logger.info(f"Migration complete: {fixed} configs fixed")
    sys.exit(0)
