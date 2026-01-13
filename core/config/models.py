"""
Pydantic models for GGBot configuration system.

These models provide type safety, validation, and defaults for the new config schema.
They replace direct JSONB access throughout the codebase.
"""

from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ExecutionMode(str, Enum):
    """Trading execution mode enumeration."""
    PAPER = "paper"
    LIVE = "live"


class DataSourcesConfig(BaseModel):
    """Data sources configuration for extraction module."""
    technical_indicators: List[str] = Field(default_factory=list, description="Timeframe-specific technical indicators")
    fundamental_analysis: List[str] = Field(default_factory=list, description="Fundamental analysis data sources")
    sentiment_and_trends: List[str] = Field(default_factory=list, description="Sentiment and trend data sources")
    influencer_kol: List[str] = Field(default_factory=list, description="Influencer/KOL data sources")
    news_and_regulations: List[str] = Field(default_factory=list, description="News and regulatory data sources")
    onchain_analytics: List[str] = Field(default_factory=list, description="On-chain analytics data sources")

    @field_validator('technical_indicators')
    @classmethod
    def validate_technical_indicators(cls, v):
        """Validate technical indicator format (e.g., RSI_1h, MACD_5m)."""
        import re
        pattern = r'^[A-Z][a-zA-Z%]*_[0-9]+[mhdw]$'
        for indicator in v:
            if not re.match(pattern, indicator):
                raise ValueError(f"Invalid technical indicator format: {indicator}. Expected format: INDICATOR_TIMEFRAME (e.g., RSI_1h)")
        return v


class ExtractionConfig(BaseModel):
    """Extraction module configuration."""
    data_sources: DataSourcesConfig = Field(default_factory=DataSourcesConfig, description="Data source configuration")


class DecisionConfig(BaseModel):
    """Decision module configuration."""
    analysis_frequency: str = Field(default="1h", description="How often to run decision analysis")
    system_prompt: Optional[str] = Field(None, description="System prompt template with placeholders")
    user_prompt: Optional[str] = Field(None, description="User strategy prompt template with placeholders")

    @field_validator('analysis_frequency')
    @classmethod
    def validate_analysis_frequency(cls, v):
        """Validate analysis frequency format."""
        valid_frequencies = ["5m", "15m", "30m", "1h", "4h", "1d", "1w", "signal_driven", "agent_driven"]
        if v not in valid_frequencies:
            raise ValueError(f"Invalid analysis frequency: {v}. Must be one of {valid_frequencies}")
        return v


class LLMProvider(str, Enum):
    """LLM provider enumeration."""
    DEFAULT = "default"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    ANTHROPIC = "anthropic"
    XAI = "xai"
    OPENROUTER = "openrouter"


class LLMConfig(BaseModel):
    """LLM configuration for decision making."""
    provider: LLMProvider = Field(default=LLMProvider.DEFAULT, description="LLM provider selection")
    model: Optional[str] = Field(default="default", description="Specific model to use for the provider")
    reasoning_tier: Optional[str] = Field(default="standard", description="Reasoning tier: economy, standard, or premium")
    thinking_mode: bool = Field(default=False, description="DEPRECATED: Use reasoning_tier instead")
    use_platform_keys: bool = Field(default=True, description="Use platform-managed API keys vs user's own keys")
    use_own_key: bool = Field(default=False, description="Use user's own API keys instead of platform keys")
    openai_api_key: Optional[str] = Field(None, description="User's OpenAI API key (encrypted in vault)")
    deepseek_api_key: Optional[str] = Field(None, description="User's DeepSeek API key (encrypted in vault)")
    anthropic_api_key: Optional[str] = Field(None, description="User's Anthropic API key (encrypted in vault)")

    @field_validator('reasoning_tier')
    @classmethod
    def validate_reasoning_tier(cls, v):
        valid_tiers = ['economy', 'standard', 'premium', None]
        if v not in valid_tiers:
            raise ValueError(f"reasoning_tier must be one of {valid_tiers}")
        return v or 'standard'

    @field_validator('openai_api_key', 'deepseek_api_key', 'anthropic_api_key')
    @classmethod
    def validate_api_key_format(cls, v):
        """Validate API key format."""
        if v is not None and not v.startswith('sk-'):
            raise ValueError("API keys must start with 'sk-'")
        return v


class PositionSizingConfig(BaseModel):
    """Position sizing configuration - confidence-based only."""
    max_margin_percent: float = Field(20.0, ge=1.0, le=100.0, description="Max margin % when confidence=1.0")


class RiskManagementConfig(BaseModel):
    """Risk management configuration."""
    default_stop_loss_percent: Optional[float] = Field(1.5, ge=0.5, le=50.0, description="Default stop loss percentage")
    default_take_profit_percent: Optional[float] = Field(3.0, ge=0.5, le=500.0, description="Default take profit percentage")

    @field_validator('default_stop_loss_percent', 'default_take_profit_percent')
    @classmethod
    def validate_percentages(cls, v):
        """Ensure stop loss and take profit percentages are reasonable."""
        if v is not None and v <= 0:
            raise ValueError("Stop loss and take profit percentages must be positive")
        return v


class TradingConfig(BaseModel):
    """Trading module configuration."""
    execution_mode: ExecutionMode = Field(default=ExecutionMode.PAPER, description="Trading execution mode")
    leverage: int = Field(default=5, ge=1, le=100, description="Trading leverage (1x for spot, up to 100x for perpetuals)")
    position_sizing: PositionSizingConfig = Field(default_factory=PositionSizingConfig, description="Position sizing configuration")
    risk_management: RiskManagementConfig = Field(default_factory=RiskManagementConfig, description="Risk management configuration")


class TelegramListenerConfig(BaseModel):
    """Telegram listener configuration."""
    enabled: bool = Field(default=False, description="Whether listener is enabled")
    api_id: str = Field(default="", description="Telegram API ID")
    api_hash: str = Field(default="", description="Telegram API hash")
    session_name: str = Field(default="ggbot_session", description="Telegram session name")
    source_channels: List[str] = Field(default_factory=list, description="Source channels to monitor")


class TelegramPublisherConfig(BaseModel):
    """Telegram publisher configuration."""
    enabled: bool = Field(default=False, description="Whether publisher is enabled")
    filter_channel: str = Field(default="", description="Channel to publish to")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence threshold")
    include_reasoning: bool = Field(default=True, description="Include AI reasoning in messages")
    include_market_context: bool = Field(default=True, description="Include market context in messages")
    message_template: str = Field(default="🔥 {ACTION} {SYMBOL} - Confidence: {CONFIDENCE}\n{REASONING}",
                                 description="Message template with placeholders")

    class Config:
        """Allow extra fields for backward compatibility (e.g., legacy bot_token field)."""
        extra = "ignore"


class TelegramIntegrationConfig(BaseModel):
    """Telegram integration configuration."""
    listener: TelegramListenerConfig = Field(default_factory=TelegramListenerConfig, description="Listener configuration")
    publisher: TelegramPublisherConfig = Field(default_factory=TelegramPublisherConfig, description="Publisher configuration")


class AgentStrategy(BaseModel):
    """
    Agent strategy configuration for autonomous trading agents.

    Used when config_type='agent'. Stores the agent's trading strategy
    and metadata about autonomous editing permissions.
    """
    content: str = Field(default="", description="Strategy description/instructions")
    autonomously_editable: bool = Field(default=False, description="Can agent modify its own strategy")
    version: int = Field(default=1, ge=1, description="Strategy version number")
    last_updated_at: str = Field(default="", description="ISO timestamp of last update")
    last_updated_by: str = Field(default="user", description="Who last updated: 'user' or 'agent'")
    performance_log: List[Dict[str, Any]] = Field(default_factory=list, description="Historical performance by version")

    @field_validator('last_updated_by')
    @classmethod
    def validate_updated_by(cls, v):
        """Validate last_updated_by field."""
        if v not in ["user", "agent"]:
            raise ValueError("last_updated_by must be 'user' or 'agent'")
        return v


class BotConfig(BaseModel):
    """
    Complete GGBot configuration model.

    This is the main configuration class that encompasses all module configurations.
    Maps directly to the config_data JSONB field in the configurations table.

    Supports three config types:
    - Standard bots (config_type=NULL): Requires extraction, decision, llm_config
    - Signal validation (config_type='signal_validation'): Requires extraction only
    - Agents (config_type='agent'): Requires agent_strategy, optional extraction/decision
    """
    schema_version: str = Field(default="1.0", description="Configuration schema version")
    selected_pair: Optional[str] = Field("BTC/USDT", description="Trading pair to analyze")

    # Standard bot fields (optional for agents)
    extraction: Optional[ExtractionConfig] = Field(None, description="Extraction module configuration")
    decision: Optional[DecisionConfig] = Field(None, description="Decision module configuration")
    llm_config: Optional[LLMConfig] = Field(None, description="LLM provider and API key configuration")

    # Required for all types
    trading: TradingConfig = Field(default_factory=TradingConfig, description="Trading module configuration")
    telegram_integration: Optional[TelegramIntegrationConfig] = Field(None,
                                                          description="Telegram integration configuration")

    # Agent-specific fields (required for config_type='agent')
    agent_strategy: Optional[AgentStrategy] = Field(None, description="Agent strategy configuration")

    @field_validator('selected_pair')
    @classmethod
    def validate_trading_pair(cls, v):
        """Validate trading pair format."""
        if v and '/' not in v:
            raise ValueError(f"Invalid trading pair format: {v}. Expected format: BTC/USDT")
        return v

    def get_position_size(self, confidence: float, balance: float) -> float:
        """
        Calculate position size: margin = confidence × max_margin_percent × balance, then × leverage.

        Position sizing semantics:
        - Margin = collateral you risk (% of account based on confidence)
        - Position = margin × leverage (actual market exposure)

        Example:
        - Balance: $10,000
        - Max margin: 20%
        - Confidence: 0.8
        - Leverage: 5x
        → Margin: 0.8 × 20% × $10,000 = $1,600 (collateral risked)
        → Position: $1,600 × 5 = $8,000 (actual market exposure)

        Args:
            confidence: AI confidence score (0.0 to 1.0)
            balance: Current account balance in USD

        Returns:
            Position size in USD (margin × leverage)
        """
        sizing = self.trading.position_sizing
        leverage = self.trading.leverage

        # Calculate margin based on confidence
        max_pct = (sizing.max_margin_percent or 20.0) / 100.0
        margin = confidence * max_pct * balance

        # Position size = margin × leverage
        return margin * leverage

    def get_default_stop_loss_price(self, entry_price: float, side: str) -> Optional[float]:
        """
        Calculate default stop loss price if not specified in decision intent.
        
        Args:
            entry_price: Trade entry price
            side: Trade side ('long' or 'short')
            
        Returns:
            Stop loss price or None if not configured
        """
        stop_loss_pct = self.trading.risk_management.default_stop_loss_percent
        if not stop_loss_pct:
            return None
            
        if side == "long":
            return entry_price * (1 - stop_loss_pct / 100.0)
        elif side == "short":
            return entry_price * (1 + stop_loss_pct / 100.0)
        else:
            return None

    def get_default_take_profit_price(self, entry_price: float, side: str) -> Optional[float]:
        """
        Calculate default take profit price if not specified in decision intent.
        
        Args:
            entry_price: Trade entry price
            side: Trade side ('long' or 'short')
            
        Returns:
            Take profit price or None if not configured
        """
        take_profit_pct = self.trading.risk_management.default_take_profit_percent
        if not take_profit_pct:
            return None
            
        if side == "long":
            return entry_price * (1 + take_profit_pct / 100.0)
        elif side == "short":
            return entry_price * (1 - take_profit_pct / 100.0)
        else:
            return None

    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"  # Reject unknown fields


# Utility functions for working with configs
def create_default_config() -> BotConfig:
    """Create a default configuration with sensible defaults."""
    return BotConfig()


def load_config_from_dict(config_dict: Dict[str, Any]) -> BotConfig:
    """
    Load configuration from dictionary (e.g., from database JSONB).
    
    Handles both V1 (flat) and V2 (nested) config structures.
    Filters out database metadata fields like config_type.
    
    Args:
        config_dict: Configuration dictionary from database
        
    Returns:
        Validated BotConfig instance
        
    Raises:
        ValidationError: If configuration is invalid
    """
    # Handle V2 nested config structure
    if "config_data" in config_dict:
        # Extract the core config from the nested structure
        core_config = config_dict["config_data"].copy()
        
        # Add any top-level fields that belong in BotConfig
        if "selected_pair" in config_dict and "selected_pair" not in core_config:
            core_config["selected_pair"] = config_dict["selected_pair"]
        
        # Filter out database metadata fields from core_config
        valid_fields = {
            "schema_version", "selected_pair", "extraction", "decision",
            "llm_config", "trading", "telegram_integration", "agent_strategy"
        }
        filtered_config = {
            key: value for key, value in core_config.items()
            if key in valid_fields
        }

        return BotConfig(**filtered_config)
    else:
        # Handle V1 flat config structure - filter out metadata fields
        valid_fields = {
            "schema_version", "selected_pair", "extraction", "decision",
            "llm_config", "trading", "telegram_integration", "agent_strategy"
        }

        # Filter config_dict to only include valid BotConfig fields
        # Exclude database metadata fields like config_type
        filtered_config = {
            key: value for key, value in config_dict.items()
            if key in valid_fields
        }

        return BotConfig(**filtered_config)


def config_to_dict(config: BotConfig) -> Dict[str, Any]:
    """
    Convert configuration to dictionary for database storage.
    
    Args:
        config: BotConfig instance
        
    Returns:
        Dictionary suitable for JSONB storage
    """
    return config.dict(exclude_none=False, by_alias=False)