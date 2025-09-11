"""
Configuration repository for structured access to bot configurations.

This repository replaces direct JSONB access throughout the codebase with type-safe,
validated configuration management using Pydantic models.
"""

import json
import os
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from pydantic import ValidationError

from .models import BotConfig, load_config_from_dict, config_to_dict, create_default_config
from core.common.db import get_db_connection
from core.common.logger import logger


class ConfigRepository:
    """
    Repository for managing bot configurations with type safety and validation.
    
    Provides structured access to configurations stored in the database while
    maintaining backward compatibility with existing JSONB access patterns.
    """
    
    def __init__(self):
        """Initialize the configuration repository."""
        self.template_cache: Dict[str, BotConfig] = {}
    
    def get_config(self, config_id: str, user_id: str) -> Optional[BotConfig]:
        """
        Get a bot configuration by config_id and user_id.
        
        Args:
            config_id: Configuration ID
            user_id: User ID for access control
            
        Returns:
            BotConfig instance or None if not found
            
        Raises:
            ValidationError: If stored configuration is invalid
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT config_data, config_name, config_type, updated_at
                        FROM configurations 
                        WHERE config_id = %s AND user_id = %s
                    """, (config_id, user_id))
                    
                    result = cur.fetchone()
                    if not result:
                        logger.bind(user_id=user_id).warning(f"Configuration not found: {config_id}")
                        return None
                    
                    config_data, config_name, config_type, updated_at = result
                    
                    # Load and validate configuration
                    try:
                        config = load_config_from_dict(config_data)
                        logger.bind(user_id=user_id).debug(f"Loaded config {config_id} successfully")
                        return config
                    except ValidationError as e:
                        logger.bind(user_id=user_id).error(f"Invalid configuration {config_id}: {e}")
                        # For now, return a default config to prevent breaking existing functionality
                        # In production, you might want to handle this differently
                        return self.get_default_config_for_type(config_type)
                        
        except Exception as e:
            logger.bind(user_id=user_id).error(f"Error loading configuration {config_id}: {e}")
            return None
    
    def save_config(self, config_id: str, user_id: str, config: BotConfig, 
                   config_name: Optional[str] = None, config_type: Optional[str] = None) -> bool:
        """
        Save a bot configuration to the database.
        
        Args:
            config_id: Configuration ID
            user_id: User ID
            config: BotConfig instance to save
            config_name: Optional config name (for display)
            config_type: Optional config type (autonomous_trading, signal_validation)
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            config_dict = config_to_dict(config)
            
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if config exists
                    cur.execute("""
                        SELECT config_id FROM configurations 
                        WHERE config_id = %s AND user_id = %s
                    """, (config_id, user_id))
                    
                    exists = cur.fetchone() is not None
                    
                    if exists:
                        # Update existing configuration
                        update_fields = ["config_data = %s", "updated_at = CURRENT_TIMESTAMP"]
                        params = [config_dict]
                        
                        if config_name is not None:
                            update_fields.append("config_name = %s")
                            params.append(config_name)
                        
                        if config_type is not None:
                            update_fields.append("config_type = %s")
                            params.append(config_type)
                        
                        params.extend([config_id, user_id])
                        
                        cur.execute(f"""
                            UPDATE configurations 
                            SET {', '.join(update_fields)}
                            WHERE config_id = %s AND user_id = %s
                        """, params)
                    else:
                        # Insert new configuration
                        cur.execute("""
                            INSERT INTO configurations (config_id, user_id, config_type, config_data, config_name, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """, (config_id, user_id, config_type or "autonomous_trading", config_dict, config_name))
                    
                    conn.commit()
                    action = "Updated" if exists else "Created"
                    logger.bind(user_id=user_id).info(f"{action} configuration {config_id}")
                    return True
                    
        except Exception as e:
            logger.bind(user_id=user_id).error(f"Error saving configuration {config_id}: {e}")
            return False
    
    def create_config_from_template(self, user_id: str, config_type: str = "autonomous_trading", 
                                   config_name: Optional[str] = None) -> Optional[str]:
        """
        Create a new configuration from template.
        
        Args:
            user_id: User ID
            config_type: Configuration type (autonomous_trading, signal_validation)
            config_name: Optional display name for the config
            
        Returns:
            New config_id if successful, None otherwise
        """
        try:
            # Generate new config_id
            config_id = str(uuid.uuid4())
            
            # Load template and customize for config type
            template = self.load_template()
            
            # Customize template based on config_type
            if config_type == "signal_validation":
                # For signal validation, use different default prompts
                template.decision.system_prompt = (
                    "You are executing the Four-Pillar Validation Framework for {SYMBOL} at {CURRENT_PRICE}. "
                    "PHASE 1 (Pillar-scoring judgment): Choose values strictly within each pillar's numeric range. "
                    "PHASE 2 (Math): Sum the scores. If total <0.05 set to 0.05; if >0.95 set to 0.95. "
                    "Market Data:\n{MARKET_DATA}\n"
                    "Focus on identifying clean technical setups and avoiding rationalization of conflicting signals."
                )
                template.decision.user_prompt = (
                    "Signal validation criteria:\n"
                    "Accept signals that align with overall trend and show confluence across multiple indicators.\n"
                    "Current market analysis:\n{MARKET_DATA}\n"
                    "Decision: Should this signal be ACCEPTED, REJECTED, or require ADDITIONAL_ANALYSIS?"
                )
            
            # Save the new configuration
            display_name = config_name or f"New {config_type.replace('_', ' ').title()} Bot"
            success = self.save_config(config_id, user_id, template, display_name, config_type)
            
            if success:
                logger.bind(user_id=user_id).info(f"Created new config {config_id} from template")
                return config_id
            else:
                return None
                
        except Exception as e:
            logger.bind(user_id=user_id).error(f"Error creating config from template: {e}")
            return None
    
    def list_user_configs(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all configurations for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of configuration metadata (without full config_data)
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT config_id, config_name, config_type, created_at, updated_at
                        FROM configurations 
                        WHERE user_id = %s
                        ORDER BY updated_at DESC
                    """, (user_id,))
                    
                    configs = []
                    for row in cur.fetchall():
                        configs.append({
                            "config_id": row[0],
                            "config_name": row[1],
                            "config_type": row[2],
                            "created_at": row[3].isoformat() if row[3] else None,
                            "updated_at": row[4].isoformat() if row[4] else None
                        })
                    
                    return configs
                    
        except Exception as e:
            logger.bind(user_id=user_id).error(f"Error listing configurations: {e}")
            return []
    
    def delete_config(self, config_id: str, user_id: str) -> bool:
        """
        Delete a configuration.
        
        Args:
            config_id: Configuration ID to delete
            user_id: User ID for access control
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM configurations 
                        WHERE config_id = %s AND user_id = %s
                    """, (config_id, user_id))
                    
                    deleted = cur.rowcount > 0
                    conn.commit()
                    
                    if deleted:
                        logger.bind(user_id=user_id).info(f"Deleted configuration {config_id}")
                    else:
                        logger.bind(user_id=user_id).warning(f"Configuration not found for deletion: {config_id}")
                    
                    return deleted
                    
        except Exception as e:
            logger.bind(user_id=user_id).error(f"Error deleting configuration {config_id}: {e}")
            return False
    
    def load_template(self, version: str = "1.0") -> BotConfig:
        """
        Load configuration template from file.
        
        Args:
            version: Template version to load
            
        Returns:
            BotConfig instance loaded from template
        """
        if version in self.template_cache:
            return self.template_cache[version].copy(deep=True)
        
        try:
            # Find template file - handle version format properly 
            # For "1.0" -> "1", for "2.1" -> "2_1", etc.
            if '.' in version:
                major, minor = version.split('.', 1)
                version_suffix = major if minor == '0' else f"{major}_{minor}"
            else:
                version_suffix = version
            template_path = Path(__file__).parents[1] / "config" / f"template_v{version_suffix}.json"
            
            if not template_path.exists():
                logger.warning(f"Template file not found: {template_path}")
                # Fallback to default config
                config = create_default_config()
                self.template_cache[version] = config
                return config.copy(deep=True)
            
            # Load template from file
            with open(template_path, 'r') as f:
                template_data = json.load(f)
            
            config = load_config_from_dict(template_data)
            self.template_cache[version] = config
            logger.info(f"Loaded template v{version} from {template_path}")
            
            return config.copy(deep=True)
            
        except Exception as e:
            logger.error(f"Error loading template v{version}: {e}")
            # NO FALLBACK - fail explicitly instead of masquerading failure
            raise RuntimeError(f"Failed to load template v{version}: {e}. Fix the template or provide valid config data.")
    
    def get_default_config_for_type(self, config_type: str) -> BotConfig:
        """
        Get a default configuration for a specific type.
        
        Args:
            config_type: Configuration type
            
        Returns:
            Default BotConfig instance
        """
        config = self.load_template()
        
        # Customize based on type
        if config_type == "signal_validation":
            # Apply signal validation defaults
            config.decision.system_prompt = (
                "You are executing the Four-Pillar Validation Framework for {SYMBOL} at {CURRENT_PRICE}."
            )
        
        return config
    
    def validate_config(self, config_dict: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate a configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary to validate
            
        Returns:
            (is_valid, error_message) tuple
        """
        try:
            load_config_from_dict(config_dict)
            return True, None
        except ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {str(e)}"


# Global repository instance
config_repo = ConfigRepository()


# Convenience functions for backward compatibility
def get_configuration(user_id: str, config_id: str) -> Optional[BotConfig]:
    """
    Get configuration by user_id and config_id.
    
    This function provides backward compatibility with existing get_configuration calls.
    """
    return config_repo.get_config(config_id, user_id)


def save_configuration(user_id: str, config_id: str, config: BotConfig, 
                      config_name: Optional[str] = None, config_type: Optional[str] = None) -> bool:
    """
    Save configuration.
    
    This function provides a simple interface for saving configurations.
    """
    return config_repo.save_config(config_id, user_id, config, config_name, config_type)