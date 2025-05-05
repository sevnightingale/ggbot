"""
MCP configuration utility module.

This module provides functions for working with MCP configuration settings,
including retrieving MCP settings from the configuration system and managing
MCP-specific settings.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

from core.common.config import DEFAULT_USER_ID
from core.common.logger import logger
from core.config.config_main import get_configuration


def get_mcp_config(
    mcp_type: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get configuration for a specific MCP type.
    
    Args:
        mcp_type: Type of MCP ('ccxt' or 'indicators')
        user_id: Optional user ID to get configuration for
        
    Returns:
        Dictionary containing MCP configuration
        
    Raises:
        ValueError: If MCP type is not recognized
    """
    user_id = user_id or DEFAULT_USER_ID
    log = logger.bind(user_id=user_id)
    
    if mcp_type not in ['ccxt', 'indicators']:
        raise ValueError(f"Unknown MCP type: {mcp_type}")
    
    # Get MCP config from main configuration
    config = get_configuration(user_id=user_id)
    mcp_config = config.get('mcp', {}).get(mcp_type, {})
    
    if not mcp_config:
        log.warning(f"No configuration found for {mcp_type} MCP")
        
    # Resolve paths relative to project root
    if 'config_path' in mcp_config and not os.path.isabs(mcp_config['config_path']):
        project_root = Path(__file__).parents[2]  # ggbot root directory
        mcp_config['config_path'] = os.path.join(
            str(project_root),
            mcp_config['config_path']
        )
    
    if 'script_path' in mcp_config and not os.path.isabs(mcp_config['script_path']):
        project_root = Path(__file__).parents[2]  # ggbot root directory
        mcp_config['script_path'] = os.path.join(
            str(project_root),
            mcp_config['script_path']
        )
    
    return mcp_config


def is_mcp_enabled(
    mcp_type: str,
    user_id: Optional[str] = None
) -> bool:
    """
    Check if a specific MCP type is enabled in the configuration.
    
    Args:
        mcp_type: Type of MCP ('ccxt' or 'indicators')
        user_id: Optional user ID to check configuration for
        
    Returns:
        Boolean indicating if the MCP is enabled
    """
    try:
        config = get_mcp_config(mcp_type, user_id)
        return config.get('enabled', False)
    except ValueError:
        return False


def get_ccxt_mcp_exchange_id(
    user_id: Optional[str] = None
) -> str:
    """
    Get the default exchange ID for CCXT MCP.
    
    Args:
        user_id: Optional user ID to get configuration for
        
    Returns:
        Default exchange ID from configuration
    """
    config = get_mcp_config('ccxt', user_id)
    return config.get('default_exchange', 'binance')


def get_indicators_mcp_script_path(
    user_id: Optional[str] = None
) -> str:
    """
    Get the script path for Indicators MCP.
    
    Args:
        user_id: Optional user ID to get configuration for
        
    Returns:
        Script path from configuration
    """
    config = get_mcp_config('indicators', user_id)
    default_path = os.path.join(
        str(Path(__file__).parents[2]),  # ggbot root directory
        'mcp_servers', 'crypto-indicators-mcp', 'index.js'
    )
    return config.get('script_path', default_path)