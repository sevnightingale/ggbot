# common/config.py
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file at project root
dotenv_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# General settings
ENV = os.getenv("ENV", "development")

# Gains Network Settings
GAINS_NETWORK_RPC_URL = os.getenv("GAINS_NETWORK_RPC_URL", "")
GAINS_DIAMOND_ADDRESS = os.getenv("GAINS_DIAMOND_ADDRESS", "")

# Database settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ggbot")
DB_USER = os.getenv("DB_USER", "ggbot_user")
DB_PASS = os.getenv("DB_PASS", "ggbot123")

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# TradingView Credentials (Optional, if using scraping)
TVIEW_USERNAME = os.getenv("TVIEW_USERNAME", "")
TVIEW_PASSWORD = os.getenv("TVIEW_PASSWORD", "")

# LLM API Keys per module
EXTRACTION_LLM_API_KEY = os.getenv("EXTRACTION_LLM_API_KEY", "")
DECISION_LLM_API_KEY = os.getenv("DECISION_LLM_API_KEY", "")
STRUCTURING_LLM_API_KEY = os.getenv("STRUCTURING_LLM_API_KEY", "")

# Legacy LLM API Key (for backward compatibility)
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# Redis (Optional)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

# Default user ID for multi-user support
DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000001")

# Steel browser API
STEEL_API_KEY = os.getenv("STEEL_API_KEY", "")

# Configuration file path (for MVP file-based config)
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "default_config.json"

def load_user_config(user_id=None, config_type=None):
    """
    Load user configuration from file (MVP approach).
    In the future, this will be replaced with database-backed configuration.
    
    Args:
        user_id: The user's ID (defaults to DEFAULT_USER_ID)
        config_type: Optional configuration type to filter (e.g., 'extraction', 'decision')
        
    Returns:
        Dictionary containing the user's configuration
    """
    user_id = user_id or DEFAULT_USER_ID
    
    try:
        with open(DEFAULT_CONFIG_PATH, 'r') as f:
            config = json.load(f)
            
        # Verify this config is for the requested user
        if config.get('user_id') != user_id:
            print(f"Warning: Config file is for user {config.get('user_id')} but requested {user_id}")
            
        # Return specific section if requested
        if config_type and config_type in config:
            return config[config_type]
            
        return config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading configuration: {e}")
        return {}