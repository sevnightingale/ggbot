#!/usr/bin/env python3
"""
Test script for log cleanup functionality.

This script tests the log cleanup service and provides a way to manually
run log cleanup or check current log usage.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the parent directory to sys.path so we can import ggbot modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import after path modification
from core.services.log_cleanup_service import log_cleanup_service
from core.common.logger import logger


async def test_log_usage():
    """Display current log disk usage."""
    print("=" * 60)
    print("🔍 CURRENT LOG DISK USAGE")
    print("=" * 60)

    try:
        usage_stats = await log_cleanup_service.get_log_disk_usage()

        print(f"📊 Total log usage: {usage_stats['total_size_mb']:.2f} MB")
        print(f"📁 Total files: {usage_stats['total_files']}")
        print(f"⏰ Scanned at: {usage_stats['scan_time']}")
        print()

        print("📂 By Location:")
        for location in usage_stats['locations']:
            if location['files'] > 0:
                print(f"   {location['path']}: {location['size_mb']:.2f} MB ({location['files']} files)")

    except Exception as e:
        print(f"❌ Error getting usage stats: {e}")
        return False

    return True


async def test_log_cleanup():
    """Test the log cleanup functionality."""
    print("\n" + "=" * 60)
    print("🧹 TESTING LOG CLEANUP")
    print("=" * 60)

    try:
        # Show usage before cleanup
        print("📋 Log usage BEFORE cleanup:")
        usage_before = await log_cleanup_service.get_log_disk_usage()
        print(f"   Total: {usage_before['total_size_mb']:.2f} MB ({usage_before['total_files']} files)")

        # Run cleanup
        print("\n🚀 Running log cleanup...")
        cleanup_stats = await log_cleanup_service.cleanup_all_logs()

        # Show results
        print(f"✅ Cleanup completed!")
        print(f"   Files deleted: {cleanup_stats['total_files_deleted']}")
        print(f"   Space freed: {cleanup_stats['total_space_freed'] / (1024*1024):.2f} MB")

        if cleanup_stats['errors']:
            print(f"   Errors: {len(cleanup_stats['errors'])}")
            for error in cleanup_stats['errors']:
                print(f"      - {error}")

        # Show detailed location results
        print("\n📂 By Location:")
        for location_result in cleanup_stats['locations_cleaned']:
            if location_result['files_deleted'] > 0:
                print(f"   {location_result['location']}: "
                      f"{location_result['files_deleted']} files deleted, "
                      f"{location_result['space_freed'] / (1024*1024):.2f} MB freed")

        # Show usage after cleanup
        print("\n📋 Log usage AFTER cleanup:")
        usage_after = await log_cleanup_service.get_log_disk_usage()
        print(f"   Total: {usage_after['total_size_mb']:.2f} MB ({usage_after['total_files']} files)")

        # Calculate savings
        space_saved = usage_before['total_size_mb'] - usage_after['total_size_mb']
        files_removed = usage_before['total_files'] - usage_after['total_files']
        print(f"\n💾 Net result: {space_saved:.2f} MB freed, {files_removed} files removed")

    except Exception as e:
        print(f"❌ Error during cleanup test: {e}")
        return False

    return True


async def test_extraction_cleanup():
    """Test the extraction results cleanup."""
    print("\n" + "=" * 60)
    print("🗂️ TESTING EXTRACTION RESULTS CLEANUP")
    print("=" * 60)

    try:
        deleted_count = await log_cleanup_service.cleanup_extraction_results()
        print(f"✅ Extraction cleanup completed: {deleted_count} files deleted")

    except Exception as e:
        print(f"❌ Error during extraction cleanup test: {e}")
        return False

    return True


async def main():
    """Main test function."""
    print("🔧 GGBot Log Cleanup Test Script")
    print(f"⚙️ Using {log_cleanup_service.retention_days}-day retention policy")

    # Test current usage
    success = await test_log_usage()
    if not success:
        sys.exit(1)

    # Test cleanup functionality
    success = await test_log_cleanup()
    if not success:
        sys.exit(1)

    # Test extraction cleanup
    success = await test_extraction_cleanup()
    if not success:
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print()
    print("📝 Notes:")
    print("   - Log cleanup runs daily at 3:00 AM via APScheduler")
    print("   - Initial cleanup runs on application startup")
    print("   - PM2 logs now have built-in rotation (10MB, 7 files)")
    print("   - Application logs use loguru retention (7 days)")
    print("   - Script can be run manually anytime for cleanup")


if __name__ == "__main__":
    asyncio.run(main())