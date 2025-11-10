"""
Test the new canonical schemas.py with real production data.
"""

from core.common.db import get_db_connection
from core.config.schemas import (
    BotConfiguration,
    validate_config_data,
    normalize_config_type,
    ConfigType,
    TradingMode
)
import json

def test_schemas():
    """Test schemas with real production configs."""
    print("=== Testing Canonical Schemas ===\n")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Test each config type
            for config_type in ['autonomous_trading', 'agent', 'signal_validation']:
                print(f"\n{'='*70}")
                print(f"Testing config_type: {config_type}")
                print('='*70)

                cur.execute("""
                    SELECT
                        config_id,
                        user_id,
                        config_name,
                        config_type,
                        config_data,
                        state,
                        trading_mode,
                        symphony_agent_id,
                        created_at,
                        updated_at
                    FROM configurations
                    WHERE config_type = %s
                    LIMIT 1
                """, (config_type,))

                row = cur.fetchone()
                if not row:
                    print(f"  ⚠️  No configs found for type: {config_type}\n")
                    continue

                # Build config dict
                config_dict = {
                    'config_id': str(row[0]),
                    'user_id': str(row[1]),
                    'config_name': row[2] or 'Untitled Bot',
                    'config_type': row[3],
                    'config_data': row[4],
                    'state': row[5],
                    'trading_mode': row[6] or 'paper',
                    'symphony_agent_id': row[7],
                    'created_at': row[8].isoformat() if row[8] else '',
                    'updated_at': row[9].isoformat() if row[9] else ''
                }

                print(f"\n  Config: {config_dict['config_name']}")
                print(f"  Type: {config_dict['config_type']}")
                print(f"  Mode: {config_dict['trading_mode']}")
                print(f"  JSONB keys: {list(config_dict['config_data'].keys())}")

                # Test 1: Validate config_data only
                print("\n  Test 1: Validate config_data...")
                try:
                    validated_data = validate_config_data(
                        config_dict['config_type'],
                        config_dict['config_data']
                    )
                    print(f"  ✅ config_data validation passed")
                    print(f"     Type: {type(validated_data).__name__}")
                except Exception as e:
                    print(f"  ❌ config_data validation failed: {e}")
                    continue

                # Test 2: Validate complete BotConfiguration
                print("\n  Test 2: Validate complete BotConfiguration...")
                try:
                    # Use validated config_data from Test 1
                    config_dict_with_validated = config_dict.copy()
                    config_dict_with_validated['config_data'] = validated_data.model_dump()

                    bot_config = BotConfiguration(**config_dict_with_validated)
                    print(f"  ✅ BotConfiguration validation passed")
                    print(f"     Config ID: {bot_config.config_id}")
                    print(f"     Type: {bot_config.config_type}")
                    print(f"     State: {bot_config.state}")
                except Exception as e:
                    print(f"  ❌ BotConfiguration validation failed: {e}")
                    continue

                # Test 3: Serialize back to dict
                print("\n  Test 3: Serialize back to dict...")
                try:
                    serialized = bot_config.model_dump()
                    print(f"  ✅ Serialization passed")
                    print(f"     Keys: {list(serialized.keys())}")
                except Exception as e:
                    print(f"  ❌ Serialization failed: {e}")

    print("\n" + "="*70)
    print("Testing complete!")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_schemas()
