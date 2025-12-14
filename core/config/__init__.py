"""
Configuration module for GGBot.

Contains configuration models, repository, and utilities for managing
bot configurations across the platform.
"""

from .models import (
    BotConfig,
    ExecutionMode,
    TradingConfig,
    PositionSizingConfig,
    RiskManagementConfig,
    create_default_config,
    load_config_from_dict,
    config_to_dict
)
from .repository import ConfigRepository, config_repo

__all__ = [
    # Models
    "BotConfig",
    "ExecutionMode",
    "TradingConfig",
    "PositionSizingConfig",
    "RiskManagementConfig",

    # Utilities
    "create_default_config",
    "load_config_from_dict",
    "config_to_dict",

    # Repository
    "ConfigRepository",
    "config_repo",
]