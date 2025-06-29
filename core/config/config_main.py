# config/config_main.py

import json
import uuid
from pathlib import Path
from core.common.config import DEFAULT_USER_ID
from core.common.db import get_db_connection, save_configuration
from core.common.logger import logger

def get_configuration(user_id=None, config_type=None, config_name=None, config_id=None):
    """
    Get configuration for a user from the database.
    Falls back to file-based configuration if not found in database.
    
    Args:
        user_id: The user ID to get configuration for (defaults to DEFAULT_USER_ID)
        config_type: Optional type of configuration to retrieve (e.g., 'extraction', 'decision')
        config_name: Optional name of the configuration
        config_id: Optional specific config ID to retrieve
        
    Returns:
        Dictionary containing the configuration
    """
    user_id = user_id or DEFAULT_USER_ID
    log = logger.bind(user_id=user_id)
    
    # Try to get from database first
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # First try to get unified user config
                if config_id:
                    cur.execute("""
                        SELECT config_data 
                        FROM configurations 
                        WHERE user_id = %s AND config_id = %s
                    """, [user_id, config_id])
                else:
                    cur.execute("""
                        SELECT config_data 
                        FROM configurations 
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, [user_id])
                
                result = cur.fetchone()
                
                if result:
                    # Found unified config
                    unified_config = result[0]
                    log.info(f"Retrieved unified configuration from database for user {user_id}")
                    
                    # If a specific module config_type was requested, extract it
                    if config_type and config_type != 'user':
                        if config_type in unified_config:
                            return unified_config[config_type]
                        else:
                            log.error(f"Config type '{config_type}' not found in unified config")
                            return {}
                    return unified_config
                else:
                    log.error(f"No unified configuration found for user {user_id}")
                    return {}
    except Exception as e:
        log.error(f"Error retrieving configuration from database: {e}")
    
    # Fall back to file-based configuration
    log.info(f"Falling back to file-based configuration for user {user_id}")
    config_file = Path(__file__).parent / "default_config.json"
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        if config_type:
            return config.get(config_type, {})
        return config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log.error(f"Error loading file-based configuration: {e}")
        return {}
        
def set_configuration(user_id, config_type, config_data, config_name=None):
    """
    Save configuration to the database.
    
    Args:
        user_id: The user ID to save configuration for
        config_type: Type of configuration (e.g., 'extraction', 'decision')
        config_data: Configuration data to save (must be JSON serializable)
        config_name: Optional name for the configuration
        
    Returns:
        Boolean indicating success or failure
    """
    log = logger.bind(user_id=user_id)
    
    try:
        config_id = save_configuration(user_id, config_type, config_data, config_name)
        if config_id:
            log.info(f"Saved configuration {config_type}{' - ' + config_name if config_name else ''} for user {user_id}")
            return True
        return False
    except Exception as e:
        log.error(f"Error saving configuration to database: {e}")
        return False

# Import configuration from file to database for the default user (useful for initial setup)
def import_default_config_to_db():
    """
    Import the default configuration file into the database for the default user.
    Useful for initial setup.
    
    Returns:
        Boolean indicating success or failure
    """
    log = logger.bind(user_id=DEFAULT_USER_ID)
    config_file = Path(__file__).parent / "default_config.json"
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        # Import each section as a separate configuration type
        success = True
        for config_type, config_data in config.items():
            if config_type != "user_id":  # Skip the user_id key
                # Save as both default (no name) and named "default" configurations
                default_success = set_configuration(DEFAULT_USER_ID, config_type, config_data)
                named_success = set_configuration(DEFAULT_USER_ID, config_type, config_data, "default")
                
                if not (default_success and named_success):
                    success = False
                    
        log.info(f"Default configuration imported to database: {'success' if success else 'partial failure'}")
        return success
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log.error(f"Error importing default configuration: {e}")
        return False

if __name__ == "__main__":
    # If run directly, import default configuration to database
    import_default_config_to_db()