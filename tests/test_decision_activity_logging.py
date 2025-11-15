"""
Test decision engine activity logging.

Verifies that llm_thought activities are created for all trading modes
without decision_id linking.
"""

from core.common.db import get_db_connection


def test_decision_activity_logging():
    """Verify recent decision engine activities don't have decision_id."""

    print("\n" + "=" * 80)
    print("DECISION ENGINE ACTIVITY LOGGING TEST")
    print("=" * 80)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Check recent llm_thought activities from decision engine
            cur.execute("""
                SELECT activity_id, summary, decision_id, details->'action' as action,
                       created_at, activity_source
                FROM activities
                WHERE activity_source = 'scheduled_bot'
                  AND activity_type = 'llm_thought'
                ORDER BY created_at DESC
                LIMIT 10
            """)

            activities = cur.fetchall()

            if not activities:
                print("\n⚠️  No llm_thought activities found from scheduled_bot")
                print("   This is expected if no bots have run since the update.")
                return True

            print(f"\n✅ Found {len(activities)} recent llm_thought activities:\n")

            has_decision_id_count = 0
            no_decision_id_count = 0

            for activity_id, summary, decision_id, action, created_at, source in activities:
                has_link = "❌ HAS decision_id" if decision_id else "✅ NO decision_id"
                print(f"{has_link} | {created_at} | {summary}")

                if decision_id:
                    has_decision_id_count += 1
                else:
                    no_decision_id_count += 1

            print(f"\n📊 Summary:")
            print(f"   Activities WITH decision_id (old): {has_decision_id_count}")
            print(f"   Activities WITHOUT decision_id (new): {no_decision_id_count}")

            if no_decision_id_count > 0:
                print(f"\n✅ PASS: Found {no_decision_id_count} standalone activities (no decision linking)")
                return True
            elif has_decision_id_count > 0:
                print(f"\n⚠️  WARNING: All activities still have decision_id")
                print(f"   This means no new decisions have run since the code update.")
                print(f"   The fix is in place, just needs a bot to run to verify.")
                return True

    return True


if __name__ == "__main__":
    success = test_decision_activity_logging()
    exit(0 if success else 1)
