"""
Test script to verify snapshot values are captured in activity logging.

Tests:
1. Activity logging captures snapshot values when snapshot exists
2. Activity logging handles NULL gracefully when no snapshot exists
3. Both log_activity() and log_llm_activity() capture snapshot values
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.common.db import get_db_connection
from core.common.activity_logger import log_activity, log_llm_activity, get_latest_snapshot
import uuid
from datetime import datetime, timedelta


def test_get_latest_snapshot():
    """Test 1: get_latest_snapshot() retrieves recent snapshot correctly"""
    print("\n=== TEST 1: get_latest_snapshot() ===")

    # Use an existing config that has snapshots
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Find a config with recent snapshots
            cur.execute("""
                SELECT DISTINCT config_id
                FROM account_snapshots
                WHERE timestamp > NOW() - INTERVAL '1 hour'
                LIMIT 1
            """)
            result = cur.fetchone()

            if not result:
                print("⚠️  No recent snapshots found, creating test data...")
                # Create test config and snapshot
                test_user_id = str(uuid.uuid4())
                test_config_id = str(uuid.uuid4())

                cur.execute("""
                    INSERT INTO configurations (config_id, user_id, config_type, config_data, state)
                    VALUES (%s, %s, 'scheduled_trading', '{"test": true}', 'inactive')
                """, (test_config_id, test_user_id))

                cur.execute("""
                    INSERT INTO account_snapshots
                    (config_id, user_id, trading_mode, current_balance, total_pnl, timestamp)
                    VALUES (%s, %s, 'paper', 10500.50, 500.50, NOW())
                """, (test_config_id, test_user_id))

                conn.commit()
                config_id = test_config_id
            else:
                config_id = str(result[0])

    # Test get_latest_snapshot()
    snapshot = get_latest_snapshot(config_id)

    if snapshot:
        print(f"✅ Snapshot found for config {config_id[:8]}...")
        print(f"   Balance: ${snapshot['current_balance']}")
        print(f"   P&L: ${snapshot['total_pnl']}")
        return config_id
    else:
        print(f"❌ No snapshot found for config {config_id[:8]}...")
        return None


def test_activity_with_snapshot(config_id):
    """Test 2: log_activity() captures snapshot values"""
    print("\n=== TEST 2: log_activity() with snapshot ===")

    # Get user_id for the config
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM configurations WHERE config_id = %s", (config_id,))
            user_id = str(cur.fetchone()[0])

    # Log an activity
    activity_id = log_activity(
        config_id=config_id,
        user_id=user_id,
        activity_type="market_query",
        activity_source="test_script",
        summary="Test activity with snapshot",
        details={"test": True, "timestamp": datetime.now().isoformat()},
        related_symbol="BTC/USDT",
        importance=5
    )

    print(f"✅ Activity logged: {activity_id}")

    # Verify snapshot values were captured
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT account_balance, account_pnl, activity_type, summary
                FROM activities
                WHERE activity_id = %s
            """, (activity_id,))
            result = cur.fetchone()

            if result:
                balance, pnl, act_type, summary = result
                print(f"✅ Activity retrieved:")
                print(f"   Type: {act_type}")
                print(f"   Summary: {summary}")
                print(f"   Account Balance: ${balance if balance else 'NULL'}")
                print(f"   Account P&L: ${pnl if pnl else 'NULL'}")

                if balance is not None and pnl is not None:
                    print("✅ PASS: Snapshot values captured successfully!")
                    return True
                else:
                    print("❌ FAIL: Snapshot values are NULL")
                    return False
            else:
                print("❌ FAIL: Activity not found")
                return False


def test_llm_activity_with_snapshot(config_id):
    """Test 3: log_llm_activity() captures snapshot values"""
    print("\n=== TEST 3: log_llm_activity() with snapshot ===")

    # Get user_id for the config
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM configurations WHERE config_id = %s", (config_id,))
            user_id = str(cur.fetchone()[0])

    # Log an LLM activity
    activity_id = log_llm_activity(
        config_id=config_id,
        user_id=user_id,
        activity_source="test_script",
        summary="Test LLM thought with snapshot",
        details={"reasoning": "This is a test", "confidence": 0.85},
        provider="openrouter",
        model="test-model",
        input_tokens=100,
        output_tokens=50,
        provider_cost_usd=0.001,
        platform_cost_usd=0.0017,
        thinking_mode=False,
        related_symbol="BTC/USDT",
        importance=7
    )

    print(f"✅ LLM activity logged: {activity_id}")

    # Verify snapshot values were captured
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT account_balance, account_pnl, activity_type, provider, model
                FROM activities
                WHERE activity_id = %s
            """, (activity_id,))
            result = cur.fetchone()

            if result:
                balance, pnl, act_type, provider, model = result
                print(f"✅ LLM activity retrieved:")
                print(f"   Type: {act_type}")
                print(f"   Provider: {provider}")
                print(f"   Model: {model}")
                print(f"   Account Balance: ${balance if balance else 'NULL'}")
                print(f"   Account P&L: ${pnl if pnl else 'NULL'}")

                if balance is not None and pnl is not None:
                    print("✅ PASS: Snapshot values captured in LLM activity!")
                    return True
                else:
                    print("❌ FAIL: Snapshot values are NULL in LLM activity")
                    return False
            else:
                print("❌ FAIL: LLM activity not found")
                return False


def test_activity_without_snapshot():
    """Test 4: log_activity() handles NULL gracefully when no snapshot exists"""
    print("\n=== TEST 4: log_activity() without snapshot (NULL handling) ===")

    # Get a real user_id from existing data
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM configurations LIMIT 1")
            result = cur.fetchone()
            if not result:
                print("⚠️  No existing users found, skipping NULL test")
                return True
            test_user_id = str(result[0])

    # Create a test config WITHOUT a snapshot
    test_config_id = str(uuid.uuid4())

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO configurations (config_id, user_id, config_type, config_data, state)
                VALUES (%s, %s, 'scheduled_trading', '{"test": true}', 'inactive')
            """, (test_config_id, test_user_id))
            conn.commit()

    print(f"Created test config {test_config_id[:8]}... (NO snapshot)")

    # Log an activity (should handle NULL gracefully)
    try:
        activity_id = log_activity(
            config_id=test_config_id,
            user_id=test_user_id,
            activity_type="market_query",
            activity_source="test_script",
            summary="Test activity WITHOUT snapshot",
            details={"test": True, "no_snapshot": True},
            importance=5
        )

        print(f"✅ Activity logged successfully: {activity_id}")

        # Verify NULL values
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT account_balance, account_pnl
                    FROM activities
                    WHERE activity_id = %s
                """, (activity_id,))
                result = cur.fetchone()

                if result:
                    balance, pnl = result
                    if balance is None and pnl is None:
                        print("✅ PASS: NULL handling works correctly!")
                        print("   Account Balance: NULL (expected)")
                        print("   Account P&L: NULL (expected)")
                        return True
                    else:
                        print(f"❌ FAIL: Expected NULL but got balance={balance}, pnl={pnl}")
                        return False
    except Exception as e:
        print(f"❌ FAIL: Exception raised: {e}")
        return False
    finally:
        # Cleanup test config
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM configurations WHERE config_id = %s", (test_config_id,))
                conn.commit()


def main():
    print("=" * 80)
    print("SNAPSHOT ACTIVITY LOGGING TEST SUITE")
    print("=" * 80)

    results = []

    # Test 1: get_latest_snapshot()
    config_id = test_get_latest_snapshot()
    if config_id:
        results.append(("get_latest_snapshot", True))

        # Test 2: log_activity() with snapshot
        results.append(("log_activity with snapshot", test_activity_with_snapshot(config_id)))

        # Test 3: log_llm_activity() with snapshot
        results.append(("log_llm_activity with snapshot", test_llm_activity_with_snapshot(config_id)))
    else:
        results.append(("get_latest_snapshot", False))

    # Test 4: NULL handling
    results.append(("NULL handling", test_activity_without_snapshot()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Snapshot activity logging is working correctly.")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED. Review output above.")
        return 1


if __name__ == "__main__":
    exit(main())
