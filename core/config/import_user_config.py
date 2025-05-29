#!/usr/bin/env python
"""
Import user-specific configuration to database.

This script loads the user-specific configuration from 
core/config/users/00000000-0000-0000-0000-000000000001.json
and imports it to the database, replacing any existing configurations.
"""

import json
import sys
import uuid
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extras import Json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, DEFAULT_USER_ID
from core.common.logger import logger


def import_user_config_to_db():
    """Import user-specific configuration to database."""
    
    # Path to user config file
    config_file = Path(__file__).parent / "users" / f"{DEFAULT_USER_ID}.json"
    
    if not config_file.exists():
        logger.error(f"User config file not found: {config_file}")
        return False
    
    # Load the user config
    try:
        with open(config_file, 'r') as f:
            user_config = json.load(f)
        logger.info(f"Loaded user config from {config_file}")
    except Exception as e:
        logger.error(f"Error loading user config: {e}")
        return False
    
    # Connect to database
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    
    try:
        with conn.cursor() as cursor:
            # First, delete existing configurations for this user
            cursor.execute(
                "DELETE FROM configurations WHERE user_id = %s",
                (DEFAULT_USER_ID,)
            )
            logger.info(f"Deleted existing configurations for user {DEFAULT_USER_ID}")
            
            # Now insert each config type
            config_types = ['extraction', 'decision', 'execution']
            
            for config_type in config_types:
                if config_type in user_config:
                    # Insert configuration with generated UUID
                    config_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO configurations 
                        (config_id, user_id, config_type, config_name, config_data, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    """, (
                        config_id,
                        DEFAULT_USER_ID,
                        config_type,
                        'default',
                        Json(user_config[config_type])
                    ))
                    logger.info(f"Inserted {config_type} configuration")
            
            # Also insert the MCP config as a separate type
            if 'mcp' in user_config:
                config_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO configurations 
                    (config_id, user_id, config_type, config_name, config_data, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                """, (
                    config_id,
                    DEFAULT_USER_ID,
                    'mcp',
                    'default',
                    Json(user_config['mcp'])
                ))
                logger.info("Inserted MCP configuration")
            
            # Commit the transaction
            conn.commit()
            logger.info("Successfully imported user configuration to database")
            
            # Verify the import
            cursor.execute("""
                SELECT config_type, config_name 
                FROM configurations 
                WHERE user_id = %s
                ORDER BY config_type
            """, (DEFAULT_USER_ID,))
            
            results = cursor.fetchall()
            logger.info("Configurations in database after import:")
            for config_type, config_name in results:
                logger.info(f"  - {config_type}: {config_name}")
            
            return True
            
    except Exception as e:
        logger.error(f"Error importing configuration: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    success = import_user_config_to_db()
    if success:
        print("✅ User configuration successfully imported to database")
    else:
        print("❌ Failed to import user configuration")
        sys.exit(1)