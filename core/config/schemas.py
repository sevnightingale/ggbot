"""
Canonical bot configuration schemas using Pydantic.

This is the SINGLE SOURCE OF TRUTH for bot configuration validation.
All validation logic lives here. TypeScript types are generated from these models.

Schema Design Principles:
1. Type-specific validation via discriminated unions
2. Table columns separate from JSONB config_data
3. No duplication (e.g., trading_mode only in table, not JSONB)
4. Clear required vs optional fields per config type
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Optional, Union, Dict, Any, List
from enum import Enum
from datetime import datetime

# ============================================================================
# Enums (Canonical Values)
# ============================================================================

class ConfigType(str, Enum):
    """Bot configuration types."""
    SCHEDULED_TRADING = "scheduled_trading"
    SIGNAL_VALIDATION = "signal_validation"
    AGENT = "agent"

class TradingMode(str, Enum):
    """Trading execution modes."""
    PAPER = "paper"
    SYMPHONY = "symphony"  # Database stores as 'live' but canonical is 'symphony'
    ASTER = "aster"

class BotState(str, Enum):
    """Bot activation states."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

# ============================================================================
# Common Config Components (Nested Objects)
# ============================================================================

class PositionSizingConfig(BaseModel):
    """Position sizing configuration - confidence-based only."""
    max_margin_percent: float = Field(default=20.0, ge=1.0, le=100.0)

class RiskManagementConfig(BaseModel):
    """Risk management settings."""
    default_stop_loss_percent: Optional[float] = Field(None, ge=0, le=100)
    default_take_profit_percent: Optional[float] = Field(None, ge=0, le=1000)

class TradingConfig(BaseModel):
    """Trading execution settings."""
    leverage: int = Field(ge=1, le=100)
    position_sizing: PositionSizingConfig
    risk_management: RiskManagementConfig

class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: str = Field(default="default")
    model: Optional[str] = Field(default="default")
    reasoning_tier: Optional[str] = Field(default="standard", description="Reasoning tier: economy (fast/cheap), standard (balanced), premium (best quality)")
    thinking_mode: bool = Field(default=False, description="DEPRECATED: Use reasoning_tier instead. Kept for backward compatibility.")

    # Deprecated: Users can no longer bring their own keys
    use_platform_keys: bool = True
    use_own_key: bool = False

    @field_validator('reasoning_tier')
    def validate_reasoning_tier(cls, v):
        valid_tiers = ['economy', 'standard', 'premium', None]
        if v not in valid_tiers:
            raise ValueError(f"reasoning_tier must be one of {valid_tiers}")
        return v or 'standard'  # Default to standard if None

    @field_validator('provider')
    def validate_provider(cls, v):
        # Allow 'default' for backward compatibility, but should migrate to explicit
        valid_providers = ['default', 'openai', 'anthropic', 'deepseek', 'xai', 'openrouter']
        if v not in valid_providers:
            raise ValueError(f"provider must be one of {valid_providers}")
        return v

    @field_validator('model')
    def validate_model(cls, v, info):
        """Validate model based on provider."""
        provider = info.data.get('provider')

        # OpenRouter uses user-friendly model names from llm_models table
        if provider == 'openrouter':
            valid_models = ['grok', 'claude', 'gemini', 'deepseek', 'gpt', 'kimi', 'qwen']
            if v and v not in valid_models:
                raise ValueError(f"For OpenRouter, model must be one of {valid_models}")

        return v

class ExtractionConfig(BaseModel):
    """Market data extraction configuration."""
    selected_data_sources: Optional[Dict[str, Any]] = None  # ← Optional for agents

    # Legacy support (old configs used 'indicators' field)
    indicators: Optional[List[str]] = None

    @field_validator('selected_data_sources')
    def validate_data_sources(cls, v):
        # Allow empty dict for agents (they may not use extraction)
        if v is not None and not isinstance(v, dict):
            raise ValueError("selected_data_sources must be a dict")
        return v

class DecisionConfig(BaseModel):
    """AI decision-making configuration."""
    system_prompt: Optional[str] = Field(None, min_length=10)  # ← Optional for agents
    user_prompt: Optional[str] = Field(None, min_length=10)  # ← Optional for agents
    analysis_frequency: Optional[str] = None  # e.g., "1h", "5m" or "agent_driven"

class AgentStrategy(BaseModel):
    """Agent strategy content and metadata."""
    content: str = Field(min_length=10)
    autonomously_editable: bool = False
    version: int = Field(default=1, ge=1)
    last_updated_at: Optional[str] = None
    last_updated_by: Optional[Literal["user", "agent"]] = "user"
    performance_log: List[Dict[str, Any]] = Field(default_factory=list)

class TelegramIntegrationConfig(BaseModel):
    """Telegram listener/publisher configuration."""
    listener: Optional[Dict[str, Any]] = None
    publisher: Optional[Dict[str, Any]] = None

# ============================================================================
# Type-Specific Config Data (Discriminated Union)
# ============================================================================

class ScheduledTradingConfigData(BaseModel):
    """
    Standard scheduled trading bot.

    Requirements:
    - Must have selected_pair (single symbol)
    - Must have extraction config with data sources
    - Must have decision config with prompts
    - Must have trading config
    """
    config_type: Literal["scheduled_trading"] = "scheduled_trading"
    schema_version: str = "2.1"

    # Required fields for scheduled trading
    selected_pair: str = Field(min_length=3, description="Trading symbol (e.g., BTC/USDT)")
    extraction: ExtractionConfig
    decision: DecisionConfig
    trading: TradingConfig

    # Optional fields
    llm_config: Optional[LLMConfig] = Field(default_factory=LLMConfig)
    telegram_integration: Optional[TelegramIntegrationConfig] = None

    # Rei integration (inference-time learning decision engine)
    rei_enabled: bool = False

    # Must NOT have agent_strategy
    agent_strategy: None = None

    @field_validator('extraction')
    def validate_extraction_required(cls, v):
        """Scheduled trading must have data sources."""
        if not v.selected_data_sources:
            raise ValueError("extraction.selected_data_sources required for scheduled_trading")
        return v

    @field_validator('decision')
    def validate_decision_required(cls, v):
        """Scheduled trading must have prompts."""
        if not v.system_prompt:
            raise ValueError("decision.system_prompt required for scheduled_trading")
        if not v.user_prompt:
            raise ValueError("decision.user_prompt required for scheduled_trading")
        return v

class SignalValidationConfigData(BaseModel):
    """
    Signal validation bot (validates external signals like ggShot).

    Requirements:
    - Must have selected_pair
    - Must have extraction config
    - Decision config is OPTIONAL (uses signal directly)
    """
    config_type: Literal["signal_validation"] = "signal_validation"
    schema_version: str = "2.1"

    # Required fields
    selected_pair: str = Field(min_length=3)
    extraction: ExtractionConfig
    trading: TradingConfig

    # Optional fields
    decision: Optional[DecisionConfig] = None  # ← Optional for signal validation
    llm_config: Optional[LLMConfig] = Field(default_factory=LLMConfig)
    telegram_integration: Optional[TelegramIntegrationConfig] = None

    # Must NOT have agent_strategy
    agent_strategy: None = None

class AgentConfigData(BaseModel):
    """
    Autonomous agent bot.

    Requirements:
    - Must have trading config (minimum validation)
    - All extraction/decision/selected_pair are OPTIONAL
    - Agent can trade multiple symbols dynamically
    - Agent strategy can be built after creation
    """
    config_type: Literal["agent"] = "agent"
    schema_version: str = "2.1"

    # Optional fields (agents are flexible)
    selected_pair: Optional[str] = None  # ← Agents can trade multiple symbols
    extraction: Optional[ExtractionConfig] = None
    decision: Optional[DecisionConfig] = None

    # Required fields
    trading: TradingConfig  # ← Agents MUST have trading config

    # Optional fields
    llm_config: Optional[LLMConfig] = Field(default_factory=LLMConfig)
    telegram_integration: Optional[TelegramIntegrationConfig] = None
    agent_strategy: Optional[AgentStrategy] = None  # Can be None initially

    # Rei integration (inference-time learning)
    rei_enabled: bool = False  # Enable Rei Core for enhanced reasoning

    @field_validator('trading')
    def validate_trading(cls, v):
        """Ensure agent has valid trading config."""
        if not v.leverage or v.leverage < 1:
            raise ValueError("trading.leverage must be >= 1 for agents")
        if not v.position_sizing:
            raise ValueError("trading.position_sizing required for agents")
        if not v.risk_management:
            raise ValueError("trading.risk_management required for agents")
        return v

# ============================================================================
# Discriminated Union (THE Source of Truth)
# ============================================================================

ConfigData = Union[
    ScheduledTradingConfigData,
    SignalValidationConfigData,
    AgentConfigData
]

# Pydantic automatically:
# 1. Looks at config_type field
# 2. Routes to correct model
# 3. Validates using that model's rules
# 4. Returns rich error messages if validation fails

# ============================================================================
# Complete Bot Configuration (Table + JSONB)
# ============================================================================

class BotConfiguration(BaseModel):
    """
    Complete bot configuration combining table columns and JSONB data.

    Table Columns:
    - config_id, user_id, config_name, config_type, state
    - trading_mode, symphony_agent_id
    - created_at, updated_at

    JSONB Blob:
    - config_data (one of the discriminated ConfigData types)
    """
    # Table columns
    config_id: str
    user_id: str
    config_name: str
    config_type: ConfigType
    state: BotState = BotState.INACTIVE
    trading_mode: TradingMode = TradingMode.PAPER
    symphony_agent_id: Optional[str] = None
    created_at: str  # ISO format timestamp
    updated_at: str  # ISO format timestamp

    # JSONB data (automatically validated by discriminated union)
    config_data: ConfigData

    @field_validator('symphony_agent_id')
    def validate_symphony_agent_id(cls, v, info):
        """Symphony mode requires agent ID."""
        trading_mode = info.data.get('trading_mode')
        if trading_mode == TradingMode.SYMPHONY and not v:
            raise ValueError("symphony_agent_id required when trading_mode=symphony")
        return v

    @model_validator(mode='after')
    def validate_config_type_consistency(self):
        """Ensure config_data type matches table config_type."""
        if self.config_type.value != self.config_data.config_type:
            raise ValueError(
                f"config_type mismatch: table has '{self.config_type.value}', "
                f"config_data has '{self.config_data.config_type}'"
            )
        return self

# ============================================================================
# API Request Models
# ============================================================================

class ConfigCreateRequest(BaseModel):
    """API request to create a new bot configuration."""
    config_name: str = Field(min_length=1, max_length=100)
    config_type: ConfigType
    trading_mode: TradingMode = TradingMode.PAPER
    symphony_agent_id: Optional[str] = None
    config_data: ConfigData  # ← Discriminated union validates type-specific fields

    @field_validator('symphony_agent_id')
    def validate_symphony_agent_id(cls, v, info):
        """Symphony mode requires agent ID."""
        if info.data.get('trading_mode') == TradingMode.SYMPHONY and not v:
            raise ValueError("symphony_agent_id required for symphony trading mode")
        return v

    @model_validator(mode='after')
    def validate_config_type_match(self):
        """Ensure config_data type matches config_type."""
        if self.config_type.value != self.config_data.config_type:
            raise ValueError(
                f"config_type mismatch: request has '{self.config_type.value}', "
                f"config_data has '{self.config_data.config_type}'"
            )
        return self

class ConfigUpdateRequest(BaseModel):
    """
    API request to update bot configuration.

    All fields optional for partial updates.
    Service layer performs deep merge on JSONB fields.
    """
    config_name: Optional[str] = Field(None, min_length=1, max_length=100)
    config_type: Optional[ConfigType] = None
    config_data: Optional[Dict[str, Any]] = None  # Partial update dict

    # Note: trading_mode and symphony_agent_id updates should be rare/restricted
    # Changing trading mode requires different credentials/setup

# ============================================================================
# Response Models
# ============================================================================

class ConfigListResponse(BaseModel):
    """Response for listing user configs."""
    configs: List[BotConfiguration]
    total: int

class ConfigResponse(BaseModel):
    """Response for single config operations."""
    config: BotConfiguration
    message: Optional[str] = None

# ============================================================================
# Validation Helpers
# ============================================================================

def validate_config_data(config_type: str, config_data: Dict[str, Any]) -> ConfigData:
    """
    Validate config_data dictionary against type-specific schema.

    Args:
        config_type: Bot type (scheduled_trading, signal_validation, agent)
        config_data: Raw JSONB data dictionary

    Returns:
        Validated ConfigData instance (correct type based on discriminator)

    Raises:
        ValidationError: If validation fails

    Example:
        >>> data = {"config_type": "agent", "trading": {...}}
        >>> validated = validate_config_data("agent", data)
        >>> isinstance(validated, AgentConfigData)
        True
    """
    # Ensure config_type in JSONB matches table config_type
    # (use table config_type as source of truth)
    config_data = config_data.copy()  # Don't mutate input
    config_data['config_type'] = config_type

    # Validate using discriminated union
    if config_type == "scheduled_trading":
        return ScheduledTradingConfigData(**config_data)
    elif config_type == "signal_validation":
        return SignalValidationConfigData(**config_data)
    elif config_type == "agent":
        return AgentConfigData(**config_data)
    else:
        raise ValueError(f"Unknown config_type: {config_type}")

def normalize_config_type(config_type: str) -> str:
    """
    Normalize config_type to canonical name.

    Args:
        config_type: Raw config type

    Returns:
        Canonical config type name (no-op after v2.2 migration)
    """
    return config_type

# ============================================================================
# Schema Version Management
# ============================================================================

CURRENT_SCHEMA_VERSION = "2.2"

SCHEMA_MIGRATIONS = {
    "2.0": "Initial V2 schema with selected_data_sources",
    "2.1": "Added agent_strategy support, LLM config improvements",
    "2.2": "Removed duplication: execution_mode, exchange_config, provider; migrated autonomous_trading → scheduled_trading",
    # "3.0": "Simplify to data_sources, strategy, trade_settings (future)",
}

def get_schema_version(config_data: Dict[str, Any]) -> str:
    """Get schema version from config_data, default to 2.1."""
    return config_data.get('schema_version', CURRENT_SCHEMA_VERSION)
