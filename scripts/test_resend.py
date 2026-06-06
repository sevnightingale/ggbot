#!/usr/bin/env python3
"""
Test Resend service functionality.

Usage:
    python scripts/test_resend.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.services.resend_service import resend_service
from core.common.logger import logger


def test_audience_operations():
    """Test audience creation and retrieval."""
    logger.info("\n" + "="*50)
    logger.info("TEST: Audience Operations")
    logger.info("="*50)

    # List existing audiences
    logger.info("\n1. Listing existing audiences...")
    audiences = resend_service.list_audiences()
    logger.info(f"Found {len(audiences)} audience(s)")

    for audience in audiences:
        logger.info(f"  - {audience.get('name')} (ID: {audience.get('id')})")

    if resend_service.default_audience_id:
        logger.info(f"\n2. Default audience configured: {resend_service.default_audience_id}")
    else:
        logger.warning("\n2. No default audience configured in .env")


def test_contact_operations():
    """Test contact create/read/update/delete."""
    logger.info("\n" + "="*50)
    logger.info("TEST: Contact Operations")
    logger.info("="*50)

    if not resend_service.default_audience_id:
        logger.error("Cannot test contacts without RESEND_AUDIENCE_ID configured")
        return

    test_email = "test@example.com"

    # Create contact
    logger.info(f"\n1. Creating test contact: {test_email}")
    success = resend_service.add_contact(
        email=test_email,
        first_name="Test",
        last_name="User"
    )
    logger.info(f"Result: {'✓ Success' if success else '✗ Failed'}")

    # Get contact
    logger.info(f"\n2. Retrieving contact: {test_email}")
    contact = resend_service.get_contact(test_email)
    if contact:
        logger.info(f"✓ Found contact: {contact.get('email')}")
    else:
        logger.warning("✗ Contact not found")

    # Update contact
    logger.info(f"\n3. Updating contact: {test_email}")
    success = resend_service.update_contact(
        email=test_email,
        first_name="Updated"
    )
    logger.info(f"Result: {'✓ Success' if success else '✗ Failed'}")

    # Delete contact
    logger.info(f"\n4. Deleting test contact: {test_email}")
    success = resend_service.remove_contact(test_email)
    logger.info(f"Result: {'✓ Success' if success else '✗ Failed'}")


def test_user_sync():
    """Test syncing a single user."""
    logger.info("\n" + "="*50)
    logger.info("TEST: User Sync")
    logger.info("="*50)

    if not resend_service.default_audience_id:
        logger.error("Cannot test sync without RESEND_AUDIENCE_ID configured")
        return

    # Get a test user from database
    from core.common.db import get_db_connection

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, email
                FROM user_profiles
                WHERE email IS NOT NULL
                LIMIT 1
            """)
            result = cur.fetchone()

    if not result:
        logger.warning("No users found in database to test sync")
        return

    user_id, email = result
    logger.info(f"\n1. Syncing user: {email}")

    success = resend_service.sync_user_to_resend(
        user_id=str(user_id),
        email=email
    )

    logger.info(f"Result: {'✓ Success' if success else '✗ Failed'}")


def main():
    """Run all tests."""
    logger.info("="*50)
    logger.info("RESEND SERVICE TEST SUITE")
    logger.info("="*50)

    try:
        test_audience_operations()
        test_contact_operations()
        test_user_sync()

        logger.info("\n" + "="*50)
        logger.info("ALL TESTS COMPLETE")
        logger.info("="*50)

    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
