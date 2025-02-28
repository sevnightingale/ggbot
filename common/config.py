# common/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

# LLM API Key
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# Redis (Optional)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

# Default user ID for multi-user support
DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000001")
