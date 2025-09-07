"""
Configuration Service for V2 Orchestrator

Provides user-isolated configuration management with Supabase integration.
Handles bot configuration CRUD operations with proper user context.
"""

import uuid
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from core.common.db import get_db_connection
from core.common.logger import logger
from core.domain import UserProfile


class BotConfigV2:
    """Bot configuration model for V2 orchestrator."""
    
    def __init__(
        self,
        config_id: str,
        user_id: str,
        config_name: str,
        selected_pair: str,
        extraction: Dict[str, Any],
        decision: Dict[str, Any], 
        trading: Dict[str, Any],
        telegram_integration: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.config_id = config_id
        self.user_id = user_id
        self.config_name = config_name
        self.selected_pair = selected_pair
        self.extraction = extraction
        self.decision = decision
        self.trading = trading
        self.telegram_integration = telegram_integration or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "config_id": self.config_id,
            "user_id": self.user_id,
            "config_name": self.config_name,
            "selected_pair": self.selected_pair,
            "extraction": self.extraction,
            "decision": self.decision,
            "trading": self.trading,
            "telegram_integration": self.telegram_integration,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BotConfigV2':
        """Create from dictionary loaded from database."""
        return cls(
            config_id=data["config_id"],
            user_id=data["user_id"],
            config_name=data.get("config_name", "Untitled Bot"),
            selected_pair=data["selected_pair"],
            extraction=data["extraction"],
            decision=data["decision"],
            trading=data["trading"],
            telegram_integration=data.get("telegram_integration", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.selected_pair:
            errors.append("selected_pair is required")
        
        # Support both old (indicators) and new (selected_data_sources) structure
        if "selected_data_sources" in self.extraction:
            # New structure validation
            data_sources = self.extraction.get("selected_data_sources", {})
            has_valid_data_points = False
            
            for source_name, source_config in data_sources.items():
                if isinstance(source_config, dict) and source_config.get("data_points"):
                    has_valid_data_points = True
                    break
            
            if not has_valid_data_points:
                errors.append("extraction.selected_data_sources must contain at least one data source with data_points")
        elif "indicators" in self.extraction:
            # Legacy structure validation
            if not self.extraction.get("indicators"):
                errors.append("extraction.indicators is required")
        else:
            errors.append("extraction must contain either 'selected_data_sources' or 'indicators'")
        
        if not self.decision.get("system_prompt"):
            errors.append("decision.system_prompt is required")
        
        if not self.decision.get("user_prompt"):
            errors.append("decision.user_prompt is required")
        
        return errors


class ConfigService:
    """Service for managing bot configurations with user isolation."""
    
    def __init__(self):
        self._log = logger.bind(component="config_service")
    
    async def create_config(
        self,
        user_id: str,
        config_name: str,
        config_data: Dict[str, Any]
    ) -> Optional[BotConfigV2]:
        """
        Create a new bot configuration for user.
        
        Args:
            user_id: User ID from auth
            config_name: User-friendly name for the configuration
            config_data: Configuration dictionary
            
        Returns:
            BotConfigV2 instance if successful, None otherwise
        """
        try:
            config_id = str(uuid.uuid4())
            
            # Create config object
            config = BotConfigV2(
                config_id=config_id,
                user_id=user_id,
                config_name=config_name,
                selected_pair=config_data.get("selected_pair", "BTC/USDT"),
                extraction=config_data.get("extraction", {}),
                decision=config_data.get("decision", {}),
                trading=config_data.get("trading", {}),
                telegram_integration=config_data.get("telegram_integration", {})
            )
            
            # Validate configuration
            errors = config.validate()
            if errors:
                self._log.error(f"Configuration validation failed: {errors}")
                return None
            
            # Store in database
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Generate unique config_type by appending timestamp for multiple configs per user
                    import time
                    unique_config_type = f"autonomous_trading_{int(time.time())}"
                    
                    cur.execute("""
                        INSERT INTO configurations 
                        (config_id, user_id, config_type, config_name, config_data, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    """, (
                        config_id,
                        user_id,
                        unique_config_type,
                        config_name,
                        json.dumps(config.to_dict())
                    ))
                conn.commit()
            
            self._log.info(f"Created config {config_id} for user {user_id}")
            return config
            
        except Exception as e:
            self._log.error(f"Failed to create config: {e}")
            return None
    
    async def get_config(
        self,
        config_id: str,
        user_id: str
    ) -> Optional[BotConfigV2]:
        """
        Get bot configuration by ID with user access validation.
        
        Args:
            config_id: Configuration ID
            user_id: User ID for access validation
            
        Returns:
            BotConfigV2 instance if found and accessible, None otherwise
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT config_data, created_at, updated_at
                        FROM configurations
                        WHERE config_id = %s AND user_id = %s
                    """, (config_id, user_id))
                    
                    result = cur.fetchone()
                    if not result:
                        return None
                    
                    config_data = json.loads(result[0]) if isinstance(result[0], str) else result[0]
                    
                    # Ensure config has required fields
                    if "config_id" not in config_data:
                        config_data["config_id"] = config_id
                    if "user_id" not in config_data:
                        config_data["user_id"] = user_id
                    if "created_at" not in config_data and result[1]:
                        config_data["created_at"] = result[1].isoformat()
                    if "updated_at" not in config_data and result[2]:
                        config_data["updated_at"] = result[2].isoformat()
                    
                    return BotConfigV2.from_dict(config_data)
                    
        except Exception as e:
            self._log.error(f"Failed to get config {config_id}: {e}")
            return None
    
    async def list_configs(self, user_id: str) -> List[BotConfigV2]:
        """
        List all configurations for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of BotConfigV2 instances
        """
        try:
            configs = []
            
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT config_id, config_name, config_data, created_at, updated_at
                        FROM configurations
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                    """, (user_id,))
                    
                    for row in cur.fetchall():
                        config_id, config_name, config_data, created_at, updated_at = row
                        
                        if isinstance(config_data, str):
                            config_data = json.loads(config_data)
                        
                        # Ensure required fields
                        config_data["config_id"] = config_id
                        config_data["user_id"] = user_id
                        if config_name and "config_name" not in config_data:
                            config_data["config_name"] = config_name
                        if created_at:
                            config_data["created_at"] = created_at.isoformat()
                        if updated_at:
                            config_data["updated_at"] = updated_at.isoformat()
                        
                        configs.append(BotConfigV2.from_dict(config_data))
            
            self._log.info(f"Listed {len(configs)} configs for user {user_id}")
            return configs
            
        except Exception as e:
            self._log.error(f"Failed to list configs for user {user_id}: {e}")
            return []
    
    async def update_config(
        self,
        config_id: str,
        user_id: str,
        config_data: Dict[str, Any],
        config_name: Optional[str] = None
    ) -> Optional[BotConfigV2]:
        """
        Update bot configuration with user access validation.
        
        Args:
            config_id: Configuration ID
            user_id: User ID for access validation
            config_data: Updated configuration data
            config_name: Optional updated name
            
        Returns:
            Updated BotConfigV2 instance if successful, None otherwise
        """
        try:
            # Get existing config to validate access
            existing_config = await self.get_config(config_id, user_id)
            if not existing_config:
                self._log.warning(f"Config {config_id} not found for user {user_id}")
                return None
            
            # Create updated config
            updated_config = BotConfigV2(
                config_id=config_id,
                user_id=user_id,
                config_name=config_name or existing_config.config_name,
                selected_pair=config_data.get("selected_pair", existing_config.selected_pair),
                extraction=config_data.get("extraction", existing_config.extraction),
                decision=config_data.get("decision", existing_config.decision),
                trading=config_data.get("trading", existing_config.trading),
                telegram_integration=config_data.get("telegram_integration", existing_config.telegram_integration),
                created_at=existing_config.created_at,
                updated_at=datetime.now()
            )
            
            # Validate updated configuration
            errors = updated_config.validate()
            if errors:
                self._log.error(f"Updated configuration validation failed: {errors}")
                return None
            
            # Update in database
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE configurations
                        SET config_name = %s, config_data = %s, updated_at = NOW()
                        WHERE config_id = %s AND user_id = %s
                    """, (
                        updated_config.config_name,
                        json.dumps(updated_config.to_dict()),
                        config_id,
                        user_id
                    ))
                conn.commit()
            
            self._log.info(f"Updated config {config_id} for user {user_id}")
            return updated_config
            
        except Exception as e:
            self._log.error(f"Failed to update config {config_id}: {e}")
            return None
    
    async def delete_config(
        self,
        config_id: str,
        user_id: str
    ) -> bool:
        """
        Delete bot configuration with user access validation.
        
        Args:
            config_id: Configuration ID
            user_id: User ID for access validation
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Verify config exists and user has access
            existing_config = await self.get_config(config_id, user_id)
            if not existing_config:
                self._log.warning(f"Config {config_id} not found for user {user_id}")
                return False
            
            # Delete from database
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM configurations
                        WHERE config_id = %s AND user_id = %s
                    """, (config_id, user_id))
                    
                    if cur.rowcount == 0:
                        return False
                        
                conn.commit()
            
            self._log.info(f"Deleted config {config_id} for user {user_id}")
            return True
            
        except Exception as e:
            self._log.error(f"Failed to delete config {config_id}: {e}")
            return False
    
    async def create_default_config(
        self,
        user_id: str,
        config_name: str = "Default Trading Bot"
    ) -> Optional[BotConfigV2]:
        """
        Create a default configuration for new users.
        
        Args:
            user_id: User ID
            config_name: Name for the default config
            
        Returns:
            BotConfigV2 instance if successful, None otherwise
        """
        default_config_data = {
            "selected_pair": "BTC/USDT",
            "extraction": {
                "data_sources": {
                    "technical_analysis": ["RSI", "MACD", "EMA", "SMA"]
                },
                "timeframe": "1h",
                "limit": 200
            },
            "decision": {
                "analysis_frequency": "1h",
                "system_prompt": "You are an expert cryptocurrency trader analyzing {SYMBOL} at current price {CURRENT_PRICE}. Your analysis is based on the following market data:\n\n{MARKET_DATA}\n\nProvide clear, reasoned responses about trading actions. Format your response with clear sections for Decision, Confidence, and Reasoning.",
                "user_prompt": "My trading strategy:\nEnter when RSI is oversold below 30 and MACD shows bullish crossover. Avoid during high volatility periods.\n\nCurrent market analysis:\n{MARKET_DATA}\n\nDecision: Based on the above data, should I ENTER, WAIT, or EXIT this position?"
            },
            "trading": {
                "execution_mode": "paper",
                "leverage": 1,
                "position_sizing": {
                    "method": "confidence_based",
                    "fixed_amount_usd": 100,
                    "account_percent": 5.0,
                    "max_position_percent": 10.0
                },
                "risk_management": {
                    "max_positions": 5,
                    "default_stop_loss_percent": 3.0,
                    "default_take_profit_percent": 6.0,
                    "max_daily_loss_usd": 500
                }
            },
            "telegram_integration": {
                "publisher": {
                    "enabled": False,
                    "confidence_threshold": 0.7,
                    "include_reasoning": True
                }
            }
        }
        
        return await self.create_config(user_id, config_name, default_config_data)


# Convenience instance
config_service = ConfigService()