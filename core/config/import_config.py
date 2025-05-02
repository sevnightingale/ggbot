# config/import_config.py
# Script to import default configuration into the database

from core.config.config_main import import_default_config_to_db
from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID

if __name__ == "__main__":
    log = logger.bind(user_id=DEFAULT_USER_ID)
    log.info("Starting import of default configuration to database...")
    success = import_default_config_to_db()
    if success:
        log.info("Successfully imported default configuration to database")
    else:
        log.error("Failed to import default configuration to database")