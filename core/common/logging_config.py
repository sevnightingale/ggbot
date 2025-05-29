"""
Centralized logging configuration for GGBot.

This module configures logging to write to both console and file,
making it easier to debug issues and review logs after runs.
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

def setup_logging():
    """
    Configure logging for the entire application.
    
    Sets up:
    - Console output with colored formatting
    - File output with detailed JSON formatting for analysis
    - Automatic log rotation at 100MB
    """
    # Remove default logger
    logger.remove()
    
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"ggbot_{timestamp}.log"
    
    # Also create a "latest" symlink for easy access
    latest_log = log_dir / "ggbot_latest.log"
    
    # Console handler - simplified format, no user_id binding required
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # File handler - detailed format with all available context
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{extra} | "
        "{message}"
    )
    
    # Add console handler
    logger.add(
        sys.stdout,
        format=console_format,
        level="INFO",
        colorize=True,
        filter=lambda record: record["level"].no >= 20  # INFO and above
    )
    
    # Add file handler with JSON serialization for structured logs
    logger.add(
        str(log_file),
        format=file_format,
        level="DEBUG",  # Capture everything in file
        rotation="100 MB",  # Rotate when file reaches 100MB
        retention="7 days",  # Keep logs for 7 days
        compression="zip",  # Compress rotated logs
        serialize=False,  # Human-readable format
        enqueue=True,  # Thread-safe logging
        backtrace=True,  # Include traceback on errors
        diagnose=True  # Include variable values in tracebacks
    )
    
    # Create/update the latest symlink
    if latest_log.exists():
        latest_log.unlink()
    latest_log.symlink_to(log_file.name)
    
    # Log the startup
    logger.info(f"Logging initialized. Writing to: {log_file}")
    logger.info(f"Latest log symlink: {latest_log}")
    
    return str(log_file)

# Export configured logger
__all__ = ['logger', 'setup_logging']