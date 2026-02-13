# common/logger.py
import sys
from loguru import logger
from core.common.config import LOG_LEVEL, DEFAULT_USER_ID


def _build_context_tag(record):
    """Build optional context tag from bound extra fields.

    Renders [run=abc123,cfg=b09a8d0e,uid=12345678] between
    the location and message when fields are present.
    Keeps log lines clean when no context is bound.
    """
    extra = record["extra"]
    parts = []
    if extra.get("run_id"):
        parts.append(f"run={extra['run_id']}")
    if extra.get("config_id"):
        parts.append(f"cfg={str(extra['config_id'])[:8]}")
    if extra.get("user_id"):
        parts.append(f"uid={str(extra['user_id'])[:8]}")
    return f" [{','.join(parts)}]" if parts else ""


def _format_console(record):
    """Dynamic format for stdout with optional context tag and colors."""
    tag = _build_context_tag(record)
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"
        + tag +
        " - <level>{message}</level>\n"
        "{exception}"
    )


def _format_file(record):
    """Dynamic format for log file with optional context tag (no colors)."""
    tag = _build_context_tag(record)
    return (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line}"
        + tag +
        " - {message}\n"
        "{exception}"
    )


# Remove the default handler to customize our logging format
logger.remove()

# Console handler with color
logger.add(
    sys.stdout,
    format=_format_console,
    level=LOG_LEVEL
)

# File handler with rotation
logger.add(
    "logs/ggbot.log",
    rotation="5 MB",
    retention="7 days",
    level=LOG_LEVEL,
    compression="zip",
    format=_format_file
)

if __name__ == "__main__":
    # Bind default user_id if none is provided during logging.
    logger.bind(user_id=DEFAULT_USER_ID).info("Logger initialized successfully.")
