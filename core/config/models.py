"""
Pydantic models for GGBot configuration system.

These models provide type safety, validation, and defaults for the new config schema.
They replace direct JSONB access throughout the codebase.
"""

from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class PositionSizingMethod(str, Enum):
    """Position sizing method enumeration."""
    FIXED_USD = "fixed_usd"
    ACCOUNT_PERCENTAGE = "account_percentage"
    CONFIDENCE_BASED = "confidence_based"


class ExecutionMode(str, Enum):
    """Trading execution mode enumeration."""
    PAPER = "paper"
    LIVE = "live"


class ExchangeType(str, Enum):
    """Exchange type enumeration."""
    CEX = "cex"
    DEX = "dex"


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
        valid_frequencies = ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        if v not in valid_frequencies:
            raise ValueError(f"Invalid analysis frequency: {v}. Must be one of {valid_frequencies}")
        return v


class LLMProvider(str, Enum):
    """LLM provider enumeration."""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    ANTHROPIC = "anthropic"


class LLMConfig(BaseModel):
    """LLM configuration for decision making."""
    provider: LLMProvider = Field(default=LLMProvider.OPENAI, description="LLM provider selection")
    use_platform_keys: bool = Field(default=False, description="Use platform-managed API keys vs user's own keys")
    openai_api_key: Optional[str] = Field(None, description="User's OpenAI API key (encrypted in vault)")
    deepseek_api_key: Optional[str] = Field(None, description="User's DeepSeek API key (encrypted in vault)")
    anthropic_api_key: Optional[str] = Field(None, description="User's Anthropic API key (encrypted in vault)")
    
    @field_validator('openai_api_key', 'deepseek_api_key', 'anthropic_api_key')
    @classmethod
    def validate_api_key_format(cls, v):
        """Validate API key format."""
        if v is not None and not v.startswith('sk-'):
            raise ValueError("API keys must start with 'sk-'")
        return v


class PositionSizingConfig(BaseModel):
    """Position sizing configuration."""
    method: PositionSizingMethod = Field(default=PositionSizingMethod.CONFIDENCE_BASED, description="Position sizing strategy")
    fixed_amount_usd: Optional[float] = Field(100.0, ge=10, le=10000, description="Fixed USD amount per trade")
    account_percent: Optional[float] = Field(5.0, ge=0.1, le=50.0, description="Percentage of account balance per trade")
    max_position_percent: Optional[float] = Field(10.0, ge=1.0, le=25.0, description="Max percentage when confidence=1.0")

    @field_validator('fixed_amount_usd', 'account_percent', 'max_position_percent')
    @classmethod
    def validate_positive_numbers(cls, v):
        """Ensure all percentage and amount fields are positive."""
        if v is not None and v <= 0:
            raise ValueError("Value must be positive")
        return v


class RiskManagementConfig(BaseModel):
    """Risk management configuration."""
    max_positions: int = Field(default=5, ge=1, le=20, description="Maximum concurrent positions")
    default_stop_loss_percent: Optional[float] = Field(3.0, ge=0.5, le=20.0, description="Default stop loss percentage")
    default_take_profit_percent: Optional[float] = Field(6.0, ge=0.5, le=50.0, description="Default take profit percentage")
    max_daily_loss_usd: Optional[float] = Field(None, ge=50, le=5000, description="Maximum daily loss limit")

    @field_validator('default_stop_loss_percent', 'default_take_profit_percent')
    @classmethod
    def validate_percentages(cls, v):
        """Ensure stop loss and take profit percentages are reasonable."""
        if v is not None and v <= 0:
            raise ValueError("Stop loss and take profit percentages must be positive")
        return v


class ExchangeConfig(BaseModel):
    """Exchange configuration for live trading."""
    exchange_type: ExchangeType = Field(default=ExchangeType.CEX, description="Exchange type")
    selected_exchange: Optional[str] = Field("binance", description="Selected exchange name")
    api_key: Optional[str] = Field("", description="Exchange API key (encrypted)")
    secret_key: Optional[str] = Field("", description="Exchange secret key (encrypted)")

    @field_validator('selected_exchange')
    @classmethod
    def validate_exchange_name(cls, v):
        """Validate exchange name."""
        if v:
            valid_cex = ["binance", "coinbase", "kraken", "bybit", "bitmex"]
            if v not in valid_cex:
                raise ValueError(f"Invalid exchange: {v}. Must be one of {valid_cex}")
        return v


class TradingConfig(BaseModel):
    """Trading module configuration."""
    execution_mode: ExecutionMode = Field(default=ExecutionMode.PAPER, description="Trading execution mode")
    leverage: int = Field(default=1, ge=1, le=100, description="Trading leverage (1x for spot, up to 100x for perpetuals)")
    position_sizing: PositionSizingConfig = Field(default_factory=PositionSizingConfig, description="Position sizing configuration")
    risk_management: RiskManagementConfig = Field(default_factory=RiskManagementConfig, description="Risk management configuration")
    exchange_config: ExchangeConfig = Field(default_factory=ExchangeConfig, description="Exchange configuration")


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
    bot_token: str = Field(default="", description="Telegram bot token")
    filter_channel: str = Field(default="", description="Channel to publish to")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence threshold")
    include_reasoning: bool = Field(default=True, description="Include AI reasoning in messages")
    include_market_context: bool = Field(default=True, description="Include market context in messages")
    message_template: str = Field(default="🔥 {ACTION} {SYMBOL} - Confidence: {CONFIDENCE}\n{REASONING}", 
                                 description="Message template with placeholders")


class TelegramIntegrationConfig(BaseModel):
    """Telegram integration configuration."""
    listener: TelegramListenerConfig = Field(default_factory=TelegramListenerConfig, description="Listener configuration")
    publisher: TelegramPublisherConfig = Field(default_factory=TelegramPublisherConfig, description="Publisher configuration")


class BotConfig(BaseModel):
    """
    Complete GGBot configuration model.
    
    This is the main configuration class that encompasses all module configurations.
    Maps directly to the config_data JSONB field in the configurations table.
    """
    schema_version: str = Field(default="1.0", description="Configuration schema version")
    selected_pair: Optional[str] = Field("BTC/USDT", description="Trading pair to analyze")
    
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig, description="Extraction module configuration")
    decision: DecisionConfig = Field(default_factory=DecisionConfig, description="Decision module configuration")
    llm_config: LLMConfig = Field(default_factory=LLMConfig, description="LLM provider and API key configuration")
    trading: TradingConfig = Field(default_factory=TradingConfig, description="Trading module configuration")
    telegram_integration: TelegramIntegrationConfig = Field(default_factory=TelegramIntegrationConfig, 
                                                          description="Telegram integration configuration")

    @field_validator('selected_pair')
    @classmethod
    def validate_trading_pair(cls, v):
        """Validate trading pair format."""
        if v and '/' not in v:
            raise ValueError(f"Invalid trading pair format: {v}. Expected format: BTC/USDT")
        return v

    def get_position_size(self, confidence: float, balance: float) -> float:
        """
        Calculate position size based on configuration and current parameters.
        
        Args:
            confidence: AI confidence score (0.0 to 1.0)
            balance: Current account balance in USD
            
        Returns:
            Position size in USD
        """
        sizing = self.trading.position_sizing
        
        if sizing.method == PositionSizingMethod.FIXED_USD:
            return sizing.fixed_amount_usd or 100.0
        elif sizing.method == PositionSizingMethod.ACCOUNT_PERCENTAGE:
            return balance * ((sizing.account_percent or 5.0) / 100.0)
        elif sizing.method == PositionSizingMethod.CONFIDENCE_BASED:
            max_pct = (sizing.max_position_percent or 10.0) / 100.0
            return confidence * max_pct * balance
        else:
            # Fallback to current behavior
            return confidence * 0.10 * balance

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
            
        return BotConfig(**core_config)
    else:
        # Handle V1 flat config structure - filter out metadata fields
        valid_fields = {
            "schema_version", "selected_pair", "extraction", "decision", 
            "llm_config", "trading", "telegram_integration"
        }
        
        # Filter config_dict to only include valid BotConfig fields
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