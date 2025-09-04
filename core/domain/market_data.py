"""
MarketData Domain Model

Represents market data with universal extraction caching and freshness management.
Supports the universal extraction service where data is extracted once per symbol
and served to all users with 30-second freshness requirements.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List
from decimal import Decimal

from .models.value_objects import Symbol


class DataSource(Enum):
    """Supported market data sources - maps to Supabase data_sources table."""
    # Core data sources from Supabase data_sources table
    TECHNICAL_ANALYSIS = "75f6030b-117e-4178-9bfc-5d1c244ccb96"  # Technical Analysis (enabled)
    SIGNALS_GROUP_CHATS = "3e849fc2-8d37-4b05-a7db-0a198c4b7152"  # Signals in Group Chats (enabled)
    FUNDAMENTAL_ANALYSIS = "2e651a43-2856-41f1-8826-152ab19f9f39"  # Fundamental Analysis (disabled)
    SOCIAL_SENTIMENT = "047f40a1-0328-4325-b520-a0395ed1a97d"  # Sentiment & Trends on Social Media (disabled)
    INFLUENCER_KOL = "c764994d-97bc-45a4-afd8-fd7e6cc02927"  # Influencer/Key Opinion Leaders (disabled)
    NEWS_REGULATORY = "21b303d2-3351-4100-ae8f-7f3629540aa2"  # News & Regulatory Actions (disabled)
    ONCHAIN_ANALYTICS = "2b7b5878-1657-4ecc-b6e6-1a14d62fe2f9"  # On-Chain Analytics (disabled)
    
    # Legacy source types (backwards compatibility)
    HUMMINGBOT_API = "hummingbot_api"
    PANDAS_TA = "pandas_ta"


# Remove DataType enum - replaced by data_source UUID reference


class DataFreshness(Enum):
    """Data freshness levels."""
    FRESH = "fresh"          # < 30 seconds old
    ACCEPTABLE = "acceptable" # 30-60 seconds old  
    STALE = "stale"          # > 60 seconds old
    EXPIRED = "expired"      # > 5 minutes old


@dataclass(frozen=True)
class Indicator:
    """Value object representing a single technical indicator."""
    name: str              # e.g., "RSI", "MACD", "BollingerBands"
    timeframe: str         # e.g., "5m", "1h", "1d"
    value: Any            # Indicator value (number, dict, etc.)
    calculation_time: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def indicator_key(self) -> str:
        """Get standardized indicator key (e.g., 'RSI_1h')."""
        return f"{self.name}_{self.timeframe}"
    
    @property
    def age_seconds(self) -> float:
        """Get age of indicator in seconds."""
        return (datetime.now() - self.calculation_time).total_seconds()
    
    def is_fresh(self, max_age_seconds: int = 30) -> bool:
        """Check if indicator is fresh enough for trading decisions."""
        return self.age_seconds <= max_age_seconds
    
    def get_freshness_level(self) -> DataFreshness:
        """Get freshness level of this indicator."""
        age = self.age_seconds
        if age <= 30:
            return DataFreshness.FRESH
        elif age <= 60:
            return DataFreshness.ACCEPTABLE
        elif age <= 300:  # 5 minutes
            return DataFreshness.STALE
        else:
            return DataFreshness.EXPIRED


@dataclass(frozen=True) 
class VolumeData:
    """Value object for volume analysis data."""
    current_volume: Decimal
    average_volume: Decimal
    volume_ratio: Decimal
    timeframe: str
    period_used: int
    timestamp: datetime
    
    @property
    def volume_increase_pct(self) -> Decimal:
        """Get volume increase percentage above average."""
        return (self.volume_ratio - Decimal('1.0')) * Decimal('100')
    
    @property
    def confidence_level(self) -> str:
        """Get volume confidence level based on ggShot criteria."""
        pct = float(self.volume_increase_pct)
        if pct < 10:
            return "Insignificant"
        elif pct < 30:
            return "Easy Confirmation"
        elif pct < 60:
            return "Good Confirmation" 
        elif pct < 100:
            return "Strong Confirmation"
        else:
            return "Very Strong Momentum"


@dataclass(frozen=True)
class PriceData:
    """Value object for current price information."""
    symbol: Symbol
    price: Decimal
    timestamp: datetime
    source: DataSource
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None
    
    @property
    def age_seconds(self) -> float:
        """Get age of price data in seconds."""
        return (datetime.now() - self.timestamp).total_seconds()
    
    def is_fresh(self, max_age_seconds: int = 30) -> bool:
        """Check if price is fresh enough."""
        return self.age_seconds <= max_age_seconds
    
    @property
    def spread(self) -> Optional[Decimal]:
        """Get bid-ask spread if available."""
        if self.bid and self.ask:
            return self.ask - self.bid
        return None


@dataclass
class MarketDataSnapshot:
    """
    Entity representing a complete market data snapshot for a symbol.
    
    Contains all indicators, price data, and volume analysis for a specific symbol
    and timestamp. Supports universal extraction caching where one snapshot
    serves multiple users.
    
    V2 Schema Updates:
    - data_source now maps to Supabase data_sources UUIDs
    - Removed data_type (redundant with data_source)
    - Enhanced for 21 advanced technical analysis preprocessors
    """
    id: str
    symbol: Symbol
    data_source: DataSource
    extracted_at: datetime
    
    # Core data
    indicators: Dict[str, Indicator] = field(default_factory=dict)
    price_data: Optional[PriceData] = None
    volume_data: Optional[VolumeData] = None
    
    # Raw data for debugging/audit
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    # Extraction metadata
    extraction_config: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: Optional[int] = None
    
    def __post_init__(self):
        """Validate market data after initialization."""
        if not self.id:
            # Generate ID from symbol and timestamp
            timestamp_str = self.extracted_at.strftime("%Y%m%d_%H%M%S")
            self.id = f"{self.symbol.value}_{timestamp_str}"
    
    @property
    def age_seconds(self) -> float:
        """Get age of this market data snapshot in seconds."""
        return (datetime.now() - self.extracted_at).total_seconds()
    
    @property
    def freshness_level(self) -> DataFreshness:
        """Get overall freshness level of this snapshot."""
        age = self.age_seconds
        if age <= 30:
            return DataFreshness.FRESH
        elif age <= 60:
            return DataFreshness.ACCEPTABLE
        elif age <= 300:
            return DataFreshness.STALE
        else:
            return DataFreshness.EXPIRED
    
    def is_fresh_enough(self, max_age_seconds: int = 30) -> bool:
        """Check if snapshot is fresh enough for decision making."""
        return self.age_seconds <= max_age_seconds
    
    def get_indicator(self, name: str, timeframe: str = "1h") -> Optional[Indicator]:
        """Get a specific indicator by name and timeframe."""
        key = f"{name}_{timeframe}"
        return self.indicators.get(key)
    
    def get_indicators_by_timeframe(self, timeframe: str) -> Dict[str, Indicator]:
        """Get all indicators for a specific timeframe."""
        return {
            key: indicator 
            for key, indicator in self.indicators.items() 
            if indicator.timeframe == timeframe
        }
    
    def get_available_timeframes(self) -> List[str]:
        """Get all available timeframes in this snapshot."""
        return list(set(indicator.timeframe for indicator in self.indicators.values()))
    
    def add_indicator(self, indicator: Indicator) -> None:
        """Add an indicator to this snapshot."""
        self.indicators[indicator.indicator_key] = indicator
    
    def add_indicators(self, indicators: List[Indicator]) -> None:
        """Add multiple indicators to this snapshot."""
        for indicator in indicators:
            self.add_indicator(indicator)
    
    def get_summary_for_llm(self) -> Dict[str, Any]:
        """Get a summary suitable for LLM prompts."""
        timeframes = {}
        
        # Group indicators by timeframe
        for indicator in self.indicators.values():
            tf = indicator.timeframe
            if tf not in timeframes:
                timeframes[tf] = {
                    'indicators': {},
                    'freshness': indicator.get_freshness_level().value
                }
            
            # Simplify indicator value for LLM
            if isinstance(indicator.value, dict) and 'summary' in indicator.value:
                value = indicator.value['summary']
            elif isinstance(indicator.value, (int, float, Decimal)):
                value = float(indicator.value)
            else:
                value = str(indicator.value)
            
            timeframes[tf]['indicators'][indicator.name] = value
        
        summary = {
            'symbol': self.symbol.value,
            'extracted_at': self.extracted_at.isoformat(),
            'freshness': self.freshness_level.value,
            'timeframes': timeframes
        }
        
        # Add price data if available
        if self.price_data:
            summary['current_price'] = {
                'price': float(self.price_data.price),
                'timestamp': self.price_data.timestamp.isoformat(),
                'source': self.price_data.source.value
            }
        
        # Add volume data if available
        if self.volume_data:
            summary['volume_analysis'] = {
                'current_volume': float(self.volume_data.current_volume),
                'volume_ratio': float(self.volume_data.volume_ratio),
                'confidence_level': self.volume_data.confidence_level,
                'timeframe': self.volume_data.timeframe
            }
        
        return summary
    
    def needs_refresh(self, max_age_seconds: int = 30) -> bool:
        """Check if this snapshot needs to be refreshed."""
        return not self.is_fresh_enough(max_age_seconds)
    
    @classmethod
    def create_technical_indicators_snapshot(
        cls,
        symbol: Symbol,
        indicators: List[Indicator],
        source: DataSource = DataSource.TECHNICAL_ANALYSIS
    ) -> 'MarketDataSnapshot':
        """Factory method for technical indicators snapshot with V2 schema."""
        snapshot = cls(
            id="",  # Will be generated in __post_init__
            symbol=symbol,
            data_source=source,
            extracted_at=datetime.now()
        )
        
        snapshot.add_indicators(indicators)
        return snapshot
    
    @classmethod
    def create_price_snapshot(
        cls,
        symbol: Symbol,
        price_data: PriceData
    ) -> 'MarketDataSnapshot':
        """Factory method for price data snapshot with V2 schema."""
        return cls(
            id="",
            symbol=symbol,
            data_source=price_data.source,
            extracted_at=datetime.now(),
            price_data=price_data
        )