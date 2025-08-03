"""
Configuration models for the Trading Engine.

These models define the configuration options for various
components of the Trading Engine, including LLM settings,
validation rules, and execution parameters.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Dict, List, Optional, Any, Union


class LLMConfig(BaseModel):
    """Configuration for LLM service."""
    model: str = Field(description="LLM model to use")
    system_prompt: str = Field(description="System prompt for LLM")
    temperature: float = Field(default=0.0, description="Temperature for LLM sampling")
    max_retries: int = Field(default=3, description="Maximum number of retries for LLM calls")
    backoff_factor: float = Field(default=1.5, description="Backoff factor for retry delays")
    api_key: Optional[str] = Field(default=None, description="API key for LLM service")
    use_mock: bool = Field(default=False, description="Whether to use mock LLM responses")


class ValidationConfig(BaseModel):
    """Configuration for validation service."""
    max_leverage: int = Field(default=50, description="Maximum allowed leverage")
    max_position_pct: float = Field(default=0.05, description="Maximum position size as % of equity")
    allowed_order_types: List[str] = Field(
        default=[
            'market', 'limit', 'stop', 'stopLimit', 
            'takeProfit', 'takeProfitLimit'
        ],
        description="Allowed order types"
    )
    min_equity_protection: float = Field(default=0.80, description="Minimum equity to protect (percentage)")
    max_contracts_per_trade: int = Field(default=1000000, description="Maximum contracts per trade")


class ExecutionConfig(BaseModel):
    """Configuration for execution service."""
    polling_interval: int = Field(default=60, description="Polling interval in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries for execution")
    backoff_factor: float = Field(default=1.5, description="Backoff factor for retry delays")


class EngineConfig(BaseModel):
    """
    Main configuration for the Trading Engine.
    
    This combines all the sub-configurations for different components
    and adds global settings.
    """
    # Sub-configs
    llm: LLMConfig = Field(default_factory=LLMConfig, description="LLM service configuration")
    validation: ValidationConfig = Field(default_factory=ValidationConfig, description="Validation service configuration")
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig, description="Execution service configuration")
    
    # Global settings
    default_exchange: str = Field(default="bitmex", description="Default exchange to use")
    use_testnet: bool = Field(default=True, description="Whether to use testnet for exchanges")
    server_path: Optional[str] = Field(default=None, description="Path to the CCXT MCP server script")
    credentials: Dict[str, Any] = Field(default_factory=dict, description="Exchange API credentials")
    risk_rules: Dict[str, Any] = Field(default_factory=dict, description="Risk management rules")
    symbol_map: Dict[str, Dict[str, str]] = Field(default_factory=dict, description="Exchange symbol mappings")

    @model_validator(mode='after')
    def process_dict_configs(self) -> 'EngineConfig':
        """
        Process sub-configurations that might be provided as dictionaries.
        This allows for easier configuration from dictionary sources.
        """
        # Convert llm dict to LLMConfig if needed
        if isinstance(self.llm, dict):
            self.llm = LLMConfig.model_validate(self.llm)
            
        # Convert validation dict to ValidationConfig if needed
        if isinstance(self.validation, dict):
            self.validation = ValidationConfig.model_validate(self.validation)
            
        # Convert execution dict to ExecutionConfig if needed
        if isinstance(self.execution, dict):
            self.execution = ExecutionConfig.model_validate(self.execution)
            
        # Ensure risk_rules exist
        if self.risk_rules is None:
            self.risk_rules = {}
            
        # Copy max_leverage and position_pct from validation to risk_rules for compatibility
        if 'max_leverage' not in self.risk_rules and hasattr(self.validation, 'max_leverage'):
            self.risk_rules['max_leverage'] = self.validation.max_leverage
            
        if 'max_risk_per_trade_pct' not in self.risk_rules and hasattr(self.validation, 'max_position_pct'):
            self.risk_rules['max_risk_per_trade_pct'] = self.validation.max_position_pct
            
        return self