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
        extraction: Optional[Dict[str, Any]] = None,
        decision: Optional[Dict[str, Any]] = None,
        trading: Optional[Dict[str, Any]] = None,
        config_type: str = "autonomous_trading",
        schema_version: str = "2.1",
        llm_config: Optional[Dict[str, Any]] = None,
        telegram_integration: Optional[Dict[str, Any]] = None,
        agent_strategy: Optional[Dict[str, Any]] = None,
        state: str = "inactive",
        trading_mode: str = "paper",
        symphony_agent_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.config_id = config_id
        self.user_id = user_id
        self.config_name = config_name
        self.selected_pair = selected_pair
        self.extraction = extraction or {}
        self.decision = decision or {}
        self.trading = trading or {}
        self.config_type = config_type
        self.schema_version = schema_version
        self.llm_config = llm_config or {"provider": "default", "use_platform_keys": True, "use_own_key": False}
        self.telegram_integration = telegram_integration or {}
        self.agent_strategy = agent_strategy
        self.state = state
        self.trading_mode = trading_mode
        self.symphony_agent_id = symphony_agent_id
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response - returns complete BotConfiguration structure."""
        return {
            "config_id": self.config_id,
            "user_id": self.user_id,
            "config_name": self.config_name,
            "config_type": self.config_type,
            "state": self.state,
            "trading_mode": self.trading_mode,
            "symphony_agent_id": self.symphony_agent_id,
            "config_data": {
                "schema_version": self.schema_version,
                "selected_pair": self.selected_pair,
                "extraction": self.extraction,
                "decision": self.decision,
                "trading": self.trading,
                "llm_config": self.llm_config,
                "telegram_integration": self.telegram_integration,
                "agent_strategy": self.agent_strategy,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def to_jsonb(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage - returns raw config_data JSONB structure.

        Note: config_type is stored in the table field, not in JSONB to avoid duplication.
        """
        config_data = {
            "schema_version": self.schema_version,
            "selected_pair": self.selected_pair,
            "extraction": self.extraction,
            "decision": self.decision,
            "trading": self.trading,
            "llm_config": self.llm_config,
            "telegram_integration": self.telegram_integration,
        }
        # Only include agent_strategy if it exists (not None)
        if self.agent_strategy is not None:
            config_data["agent_strategy"] = self.agent_strategy
        return config_data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BotConfigV2':
        """Create from dictionary loaded from database."""
        return cls(
            config_id=data["config_id"],
            user_id=data["user_id"],
            config_name=data.get("config_name", "Untitled Bot"),
            selected_pair=data["selected_pair"],
            extraction=data.get("extraction"),
            decision=data.get("decision"),
            trading=data.get("trading"),
            config_type=data.get("config_type", "autonomous_trading"),
            schema_version=data.get("schema_version", "2.1"),
            llm_config=data.get("llm_config", {"provider": "deepseek", "use_platform_keys": True, "use_own_key": False}),
            telegram_integration=data.get("telegram_integration", {}),
            agent_strategy=data.get("agent_strategy"),
            state=data.get("state", "inactive"),
            trading_mode=data.get("trading_mode", "paper"),
            symphony_agent_id=data.get("symphony_agent_id"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []

        # Agent configs have different validation requirements
        if self.config_type == "agent":
            # Agent configs can be created WITHOUT agent_strategy initially
            # Strategy is built during strategy_definition mode, then saved
            # selected_pair is also optional (agent can trade multiple pairs)
            # extraction/decision/llm_config are optional for agents
            return errors

        # For non-agent configs, selected_pair is required
        if not self.selected_pair:
            errors.append("selected_pair is required")

        # Standard bot validation (for autonomous_trading and signal_validation)
        # Support both old (indicators) and new (selected_data_sources) structure
        if not self.extraction:
            errors.append("extraction is required for non-agent configs")
        elif "selected_data_sources" in self.extraction:
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

        # Decision validation (only for standard bots, not signal_validation)
        if self.config_type != "signal_validation":
            if not self.decision:
                errors.append("decision is required for autonomous_trading configs")
            elif not self.decision.get("system_prompt"):
                errors.append("decision.system_prompt is required")
            elif not self.decision.get("user_prompt"):
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
                config_type=config_data.get("config_type", "autonomous_trading"),
                selected_pair=config_data.get("selected_pair", "BTC/USDT"),
                extraction=config_data.get("extraction"),
                decision=config_data.get("decision"),
                trading=config_data.get("trading"),
                schema_version=config_data.get("schema_version", "2.1"),
                agent_strategy=config_data.get("agent_strategy"),
                llm_config=config_data.get("llm_config", {"provider": "deepseek", "use_platform_keys": True, "use_own_key": False}),
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
                    cur.execute("""
                        INSERT INTO configurations
                        (config_id, user_id, config_type, config_name, config_data, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    """, (
                        config_id,
                        user_id,
                        config.config_type,  # Use actual config_type from BotConfigV2
                        config_name,
                        json.dumps(config.to_jsonb())
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
                        SELECT config_data, created_at, updated_at, config_type, trading_mode, symphony_agent_id
                        FROM configurations
                        WHERE config_id = %s AND user_id = %s
                    """, (config_id, user_id))

                    result = cur.fetchone()
                    if not result:
                        return None

                    config_data = json.loads(result[0]) if isinstance(result[0], str) else result[0]
                    db_config_type = result[3] or "autonomous_trading"  # Use config_type from database
                    trading_mode = result[4] or "paper"
                    symphony_agent_id = result[5]
                    
                    # Handle nested config_data structure
                    if "config_data" in config_data:
                        # New nested structure - extract the inner config_data
                        inner_config = config_data["config_data"]
                        flattened_config = {
                            "config_id": config_id,
                            "user_id": user_id,
                            "config_name": config_data.get("config_name", "Untitled Bot"),
                            "selected_pair": inner_config.get("selected_pair", "BTC/USDT"),
                            "extraction": inner_config.get("extraction", {}),
                            "decision": inner_config.get("decision", {}),
                            "trading": inner_config.get("trading", {}),
                            "config_type": db_config_type,  # Use database value
                            "schema_version": inner_config.get("schema_version", "2.1"),
                            "llm_config": inner_config.get("llm_config", {"provider": "deepseek", "use_platform_keys": True, "use_own_key": False}),
                            "telegram_integration": inner_config.get("telegram_integration", {}),
                            "trading_mode": trading_mode,
                            "symphony_agent_id": symphony_agent_id,
                            "created_at": result[1].isoformat() if result[1] else None,
                            "updated_at": result[2].isoformat() if result[2] else None
                        }
                    else:
                        # Legacy flat structure - ensure required fields
                        flattened_config = config_data.copy()
                        if "config_id" not in flattened_config:
                            flattened_config["config_id"] = config_id
                        if "user_id" not in flattened_config:
                            flattened_config["user_id"] = user_id
                        # Always use database config_type and Symphony fields
                        flattened_config["config_type"] = db_config_type
                        flattened_config["trading_mode"] = trading_mode
                        flattened_config["symphony_agent_id"] = symphony_agent_id
                        if "created_at" not in flattened_config and result[1]:
                            flattened_config["created_at"] = result[1].isoformat()
                        if "updated_at" not in flattened_config and result[2]:
                            flattened_config["updated_at"] = result[2].isoformat()

                    return BotConfigV2.from_dict(flattened_config)
                    
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
                        SELECT config_id, config_name, config_data, created_at, updated_at, state, config_type,
                               trading_mode, symphony_agent_id
                        FROM configurations
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                    """, (user_id,))

                    for row in cur.fetchall():
                        config_id, config_name, config_data, created_at, updated_at, state, db_config_type, trading_mode, symphony_agent_id = row

                        if isinstance(config_data, str):
                            config_data = json.loads(config_data)

                        # Extract config_data structure and flatten for from_dict
                        if "config_data" in config_data:
                            # New nested structure - extract the inner config_data
                            inner_config = config_data["config_data"]
                            flattened_config = {
                                "config_id": config_id,
                                "user_id": user_id,
                                "config_name": config_name or config_data.get("config_name", "Untitled Bot"),
                                "selected_pair": inner_config.get("selected_pair", "BTC/USDT"),
                                "extraction": inner_config.get("extraction", {}),
                                "decision": inner_config.get("decision", {}),
                                "trading": inner_config.get("trading", {}),
                                "config_type": db_config_type or "autonomous_trading",
                                "schema_version": inner_config.get("schema_version", "2.1"),
                                "llm_config": inner_config.get("llm_config", {"provider": "deepseek", "use_platform_keys": True, "use_own_key": False}),
                                "telegram_integration": inner_config.get("telegram_integration", {}),
                                "state": state or "inactive",
                                "trading_mode": trading_mode or "paper",
                                "symphony_agent_id": symphony_agent_id,
                                "created_at": created_at.isoformat() if created_at else None,
                                "updated_at": updated_at.isoformat() if updated_at else None
                            }
                        else:
                            # Legacy flat structure - use as is
                            flattened_config = config_data.copy()
                            flattened_config["config_id"] = config_id
                            flattened_config["user_id"] = user_id
                            if config_name and "config_name" not in flattened_config:
                                flattened_config["config_name"] = config_name
                            flattened_config["state"] = state or "inactive"
                            flattened_config["config_type"] = db_config_type or "autonomous_trading"
                            flattened_config["trading_mode"] = trading_mode or "paper"
                            flattened_config["symphony_agent_id"] = symphony_agent_id
                            if created_at:
                                flattened_config["created_at"] = created_at.isoformat()
                            if updated_at:
                                flattened_config["updated_at"] = updated_at.isoformat()

                        configs.append(BotConfigV2.from_dict(flattened_config))
            
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
        config_name: Optional[str] = None,
        config_type: Optional[str] = None
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
                config_type=config_type or existing_config.config_type,
                selected_pair=config_data.get("selected_pair", existing_config.selected_pair),
                extraction=config_data.get("extraction", existing_config.extraction),
                decision=config_data.get("decision", existing_config.decision),
                trading=config_data.get("trading", existing_config.trading),
                schema_version=config_data.get("schema_version", existing_config.schema_version),
                llm_config=config_data.get("llm_config", existing_config.llm_config),
                telegram_integration=config_data.get("telegram_integration", existing_config.telegram_integration),
                trading_mode=existing_config.trading_mode,  # Preserve trading mode (paper vs live)
                symphony_agent_id=existing_config.symphony_agent_id,  # Preserve Symphony agent ID
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
                        SET config_name = %s, config_data = %s, config_type = %s, updated_at = NOW()
                        WHERE config_id = %s AND user_id = %s
                    """, (
                        updated_config.config_name,
                        json.dumps(updated_config.to_jsonb()),
                        updated_config.config_type,
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
    
    async def set_bot_state(
        self,
        config_id: str,
        user_id: str,
        state: str
    ) -> bool:
        """
        Update the state field for a bot configuration.
        
        Args:
            config_id: Configuration ID
            user_id: User ID for access validation
            state: New state ('active' or 'inactive')
            
        Returns:
            True if successful, False otherwise
        """
        if state not in ['active', 'inactive']:
            self._log.error(f"Invalid state: {state}. Must be 'active' or 'inactive'")
            return False
            
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE configurations 
                        SET state = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE config_id = %s AND user_id = %s
                    """, (state, config_id, user_id))
                    
                    if cur.rowcount > 0:
                        conn.commit()
                        self._log.info(f"Updated config {config_id} state to {state}")
                        return True
                    else:
                        self._log.warning(f"No config found to update: {config_id}")
                        return False
                        
        except Exception as e:
            self._log.error(f"Failed to set bot state for {config_id}: {e}")
            return False
    
    async def get_bot_state(
        self,
        config_id: str,
        user_id: str
    ) -> Optional[str]:
        """
        Get the current state of a bot configuration.
        
        Args:
            config_id: Configuration ID
            user_id: User ID for access validation
            
        Returns:
            Current state ('active' or 'inactive') or None if not found
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT state 
                        FROM configurations 
                        WHERE config_id = %s AND user_id = %s
                    """, (config_id, user_id))
                    
                    result = cur.fetchone()
                    return result[0] if result else None
                    
        except Exception as e:
            self._log.error(f"Failed to get bot state for {config_id}: {e}")
            return None


# Convenience instance
config_service = ConfigService()