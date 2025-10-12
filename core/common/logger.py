# common/logger.py
import sys
from loguru import logger
from core.common.config import LOG_LEVEL, DEFAULT_USER_ID

# Remove the default handler to customize our logging format
logger.remove()

# Configure Loguru logging without user_id requirement for now
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>",
    level=LOG_LEVEL
)

logger.add(
    "logs/ggbot.log",
    rotation="5 MB",
    retention="7 days",
    level=LOG_LEVEL,
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | "
           "{level: <8} | "
           "{name}:{function}:{line} - {message}"
)

if __name__ == "__main__":
    # Bind default user_id if none is provided during logging.
    logger.bind(user_id=DEFAULT_USER_ID).info("Logger initialized successfully.")
