"""
Log Cleanup Service for GGBot

Provides centralized log file cleanup with 7-day retention policy
to prevent disk space issues from accumulating log files.
"""

import os
import glob
import time
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any
from core.common.logger import logger


class LogCleanupService:
    """Service to clean up old log files across the ggbot system."""

    def __init__(self, retention_days: int = 7):
        """
        Initialize log cleanup service.

        Args:
            retention_days: Number of days to keep log files
        """
        self.retention_days = retention_days
        self.cutoff_timestamp = time.time() - (retention_days * 24 * 3600)

        # Define all log locations to clean up
        self.log_locations = [
            # Application logs
            "/home/sev/ggbot/logs/",
            "/home/sev/ggbot/ggshot/logs/",

            # PM2 logs
            "/home/sev/.pm2/logs/",

            # Extraction results (already has cleanup but include for completeness)
            "/home/sev/ggbot/extraction_results/"
        ]

        # Patterns for log files to clean up
        self.log_patterns = [
            "*.log",
            "*.log.*",
            "*.out",
            "*.err",
            "*.json"  # For extraction results
        ]

    async def cleanup_all_logs(self) -> Dict[str, Any]:
        """
        Clean up all log files older than retention period.

        Returns:
            Dict with cleanup statistics
        """
        stats = {
            "total_files_deleted": 0,
            "total_space_freed": 0,
            "locations_cleaned": [],
            "errors": [],
            "cleanup_time": datetime.now(timezone.utc).isoformat()
        }

        logger.bind(service="log_cleanup").info(
            f"🧹 Starting log cleanup with {self.retention_days}-day retention"
        )

        for location in self.log_locations:
            try:
                location_stats = await self._cleanup_location(location)
                stats["total_files_deleted"] += location_stats["files_deleted"]
                stats["total_space_freed"] += location_stats["space_freed"]
                stats["locations_cleaned"].append({
                    "location": location,
                    **location_stats
                })
            except Exception as e:
                error_msg = f"Failed to cleanup {location}: {str(e)}"
                stats["errors"].append(error_msg)
                logger.bind(service="log_cleanup").error(error_msg)

        # Log summary
        logger.bind(service="log_cleanup").info(
            f"✅ Log cleanup completed: "
            f"{stats['total_files_deleted']} files deleted, "
            f"{stats['total_space_freed'] / (1024*1024):.2f} MB freed"
        )

        return stats

    async def _cleanup_location(self, location: str) -> Dict[str, Any]:
        """
        Clean up logs in a specific location.

        Args:
            location: Path to clean up

        Returns:
            Dict with cleanup statistics for this location
        """
        location_path = Path(location)
        if not location_path.exists():
            return {"files_deleted": 0, "space_freed": 0, "files_found": 0}

        stats = {"files_deleted": 0, "space_freed": 0, "files_found": 0}

        # Find all log files matching our patterns
        for pattern in self.log_patterns:
            for filepath in location_path.glob(pattern):
                if filepath.is_file():
                    stats["files_found"] += 1

                    try:
                        # Check if file is older than retention period
                        if filepath.stat().st_mtime < self.cutoff_timestamp:
                            # Skip files that are currently being written to
                            if self._is_file_in_use(filepath):
                                continue

                            file_size = filepath.stat().st_size
                            filepath.unlink()

                            stats["files_deleted"] += 1
                            stats["space_freed"] += file_size

                    except Exception as e:
                        logger.bind(service="log_cleanup").warning(
                            f"⚠️ Could not delete {filepath}: {str(e)}"
                        )

        if stats["files_deleted"] > 0:
            logger.bind(service="log_cleanup").info(
                f"📁 {location}: {stats['files_deleted']}/{stats['files_found']} files deleted, "
                f"{stats['space_freed'] / (1024*1024):.2f} MB freed"
            )

        return stats

    def _is_file_in_use(self, filepath: Path) -> bool:
        """
        Check if a file is currently being written to.

        Args:
            filepath: Path to check

        Returns:
            True if file appears to be in active use
        """
        try:
            # Check if file was modified very recently (last 5 minutes)
            recent_threshold = time.time() - (5 * 60)  # 5 minutes
            if filepath.stat().st_mtime > recent_threshold:
                return True

            # Check for common active log file patterns
            filename = filepath.name.lower()
            if any(active_pattern in filename for active_pattern in [
                "ggbot-out.log",  # Active PM2 stdout
                "ggbot-error.log",  # Active PM2 stderr
                "ggbot.log",  # Active application log
                "orchestrator.log"  # Active orchestrator log
            ]) and not any(archive_pattern in filename for archive_pattern in [
                ".gz", ".zip", ".bz2", "-1", "-2", "-3"  # Archived versions
            ]):
                return True

            return False

        except Exception:
            # If we can't determine, err on the side of caution
            return True

    async def cleanup_extraction_results(self) -> int:
        """
        Clean up old extraction results using existing mechanism.

        Returns:
            Number of files deleted
        """
        try:
            from extraction.v2.file_storage import ExtractionResultStorage

            # Use default user_id for cleanup (affects all users)
            storage = ExtractionResultStorage("cleanup-service")
            deleted_count = storage.cleanup_old_files(days_to_keep=self.retention_days)

            logger.bind(service="log_cleanup").info(
                f"🗂️ Extraction results: {deleted_count} files cleaned up"
            )

            return deleted_count

        except Exception as e:
            logger.bind(service="log_cleanup").error(
                f"❌ Failed to cleanup extraction results: {str(e)}"
            )
            return 0

    async def get_log_disk_usage(self) -> Dict[str, Any]:
        """
        Get current disk usage statistics for all log locations.

        Returns:
            Dict with usage statistics
        """
        usage_stats = {
            "total_size_mb": 0,
            "total_files": 0,
            "locations": [],
            "scan_time": datetime.now(timezone.utc).isoformat()
        }

        for location in self.log_locations:
            location_path = Path(location)
            if not location_path.exists():
                continue

            location_stats = {"path": location, "size_mb": 0, "files": 0}

            for pattern in self.log_patterns:
                for filepath in location_path.glob(pattern):
                    if filepath.is_file():
                        try:
                            size = filepath.stat().st_size
                            location_stats["size_mb"] += size / (1024 * 1024)
                            location_stats["files"] += 1
                        except Exception:
                            continue

            usage_stats["locations"].append(location_stats)
            usage_stats["total_size_mb"] += location_stats["size_mb"]
            usage_stats["total_files"] += location_stats["files"]

        return usage_stats


# Global service instance
log_cleanup_service = LogCleanupService(retention_days=7)


async def run_daily_cleanup():
    """Run daily log cleanup - can be called from scheduler."""
    return await log_cleanup_service.cleanup_all_logs()


if __name__ == "__main__":
    # Manual cleanup execution
    async def main():
        stats = await log_cleanup_service.cleanup_all_logs()
        print(f"Cleanup completed: {stats}")

        usage = await log_cleanup_service.get_log_disk_usage()
        print(f"Current usage: {usage['total_size_mb']:.2f} MB in {usage['total_files']} files")

    asyncio.run(main())