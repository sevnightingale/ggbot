"""
Utility functions for the Decision Module.

This module contains helper functions used across the decision module.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional
from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
from core.common.logger import logger


def get_config_id_by_name(user_id: str, config_name: str) -> Optional[str]:
    """
    Get the configuration ID by user ID and config name.
    
    Args:
        user_id (str): UUID of the user
        config_name (str): Name of the configuration
        
    Returns:
        Optional[str]: Configuration ID if found, None otherwise
    """
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        cursor_factory=RealDictCursor
    )
    
    try:
        cursor = conn.cursor()
        # Look for unified user config
        cursor.execute("""
            SELECT config_id 
            FROM configurations 
            WHERE user_id = %s 
            AND config_name = %s
        """, (user_id, config_name))
        
        result = cursor.fetchone()
        if result:
            logger.bind(user_id=user_id).info(
                f"Found config_id {result['config_id']} for config_name '{config_name}'"
            )
            return result['config_id']
        else:
            logger.bind(user_id=user_id).warning(
                f"No configuration found for user {user_id} with name '{config_name}'"
            )
            return None
            
    finally:
        conn.close()