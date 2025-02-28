# common/logger.py
import sys
from loguru import logger
from common.config import LOG_LEVEL, DEFAULT_USER_ID

# Remove the default handler to customize our logging format
logger.remove()

# Configure Loguru logging with user_id context
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "User: {extra[user_id]} | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>",
    level=LOG_LEVEL
)

logger.add(
    "logs/ggbot.log",
    rotation="10 MB",
    level=LOG_LEVEL,
    compression="zip",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "User: {extra[user_id]} | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>"
)

if __name__ == "__main__":
    # Bind default user_id if none is provided during logging.
    logger.bind(user_id=DEFAULT_USER_ID).info("Logger initialized successfully.")
