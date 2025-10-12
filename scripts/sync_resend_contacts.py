#!/usr/bin/env python3
"""
Sync Supabase users to Resend contacts.

Usage:
    python scripts/sync_resend_contacts.py [--create-audience] [--audience-name "Name"]
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.services.resend_service import resend_service
from core.common.logger import logger


def main():
    parser = argparse.ArgumentParser(description="Sync Supabase users to Resend")
    parser.add_argument(
        "--create-audience",
        action="store_true",
        help="Create a new Resend audience before syncing"
    )
    parser.add_argument(
        "--audience-name",
        type=str,
        default="ggbots Users",
        help="Name for the audience (default: ggbots Users)"
    )
    parser.add_argument(
        "--list-audiences",
        action="store_true",
        help="List all existing audiences and exit"
    )

    args = parser.parse_args()

    # List audiences if requested
    if args.list_audiences:
        logger.info("Fetching audiences from Resend...")
        audiences = resend_service.list_audiences()

        if not audiences:
            logger.info("No audiences found")
        else:
            logger.info(f"Found {len(audiences)} audience(s):")
            for audience in audiences:
                logger.info(f"  - {audience.get('name')} (ID: {audience.get('id')})")

        return

    # Create audience if requested
    if args.create_audience:
        logger.info(f"Creating audience: {args.audience_name}")
        audience_id = resend_service.create_audience(args.audience_name)

        if audience_id:
            logger.info(f"✓ Audience created with ID: {audience_id}")
            logger.info(f"Add this to your .env file:")
            logger.info(f"RESEND_AUDIENCE_ID={audience_id}")
        else:
            logger.error("Failed to create audience")
            return

    # Check if audience is configured
    if not resend_service.default_audience_id:
        logger.error("No RESEND_AUDIENCE_ID configured in .env")
        logger.info("Please either:")
        logger.info("  1. Run with --create-audience flag")
        logger.info("  2. Set RESEND_AUDIENCE_ID in .env")
        return

    # Sync users
    logger.info(f"Starting user sync to audience: {resend_service.default_audience_id}")
    stats = resend_service.sync_all_users_to_resend()

    # Display results
    logger.info("\n" + "="*50)
    logger.info("SYNC RESULTS")
    logger.info("="*50)
    logger.info(f"Total users:     {stats['total']}")
    logger.info(f"✓ Successful:    {stats['success_count']}")
    logger.info(f"✗ Failed:        {stats['error_count']}")
    logger.info("="*50)


if __name__ == "__main__":
    main()
