"""
Centralized logging configuration for GGBot.

Simple logging to ggbot.log file for easy review.
"""
import os
import sys
from pathlib import Path
from loguru import logger

def setup_logging():
    """
    Configure simple logging to ggbot.log file.
    """
    # Remove default logger
    logger.remove()
    
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Simple log file
    log_file = log_dir / "ggbot.log"
    
    # Console handler - simple format (safe for tests)
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # File handler - simple format without extra context
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )
    
    # Add console handler
    logger.add(
        sys.stdout,
        format=console_format,
        level="INFO",
        colorize=True
    )
    
    # Add file handler
    logger.add(
        str(log_file),
        format=file_format,
        level="DEBUG"
    )
    
    return str(log_file)

# Export configured logger
__all__ = ['logger', 'setup_logging']