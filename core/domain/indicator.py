"""
Indicator Domain Model

Represents technical indicators and data sources with premium gating.
Enables dynamic indicator management and subscription-based feature access.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
import uuid


class IndicatorCategory(Enum):
    """Technical indicator categories for organization."""
    MOMENTUM = "momentum"
    TREND = "trend"  
    VOLUME = "volume"
    VOLATILITY = "volatility"
    CUSTOM = "custom"


class IndicatorStatus(Enum):
    """Indicator quality and availability status."""
    BETA = "beta"          # New indicator, may have issues
    STABLE = "stable"      # Tested and reliable
    DEPRECATED = "deprecated"  # Being phased out
    DISABLED = "disabled"  # Temporarily unavailable


@dataclass
class Indicator:
    """
    Technical indicator entity with premium gating and metadata.
    
    Enables dynamic indicator management without frontend code changes.
    """
    
    indicator_id: str
    name: str  # Internal identifier (e.g., "RSI")
    display_name: str  # User-friendly name (e.g., "RSI (Relative Strength Index)")
    category: IndicatorCategory
    status: IndicatorStatus = IndicatorStatus.STABLE
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Optional metadata
    description: Optional[str] = None
    requires_premium: bool = False
    default_params: Optional[Dict[str, Any]] = None
    sort_order: int = 0
    
    def __post_init__(self):
        """Validate indicator after initialization."""
        if not self.indicator_id:
            self.indicator_id = str(uuid.uuid4())
        
        if not self.name or not self.display_name:
            raise ValueError("Indicator name and display_name are required")
    
    @property
    def is_available(self) -> bool:
        """Check if indicator is available for use."""
        return self.enabled and self.status != IndicatorStatus.DISABLED
    
    @property
    def is_stable(self) -> bool:
        """Check if indicator is stable and production-ready."""
        return self.status == IndicatorStatus.STABLE
    
    @property
    def is_beta(self) -> bool:
        """Check if indicator is in beta testing."""
        return self.status == IndicatorStatus.BETA
    
    @property
    def is_deprecated(self) -> bool:
        """Check if indicator is deprecated."""
        return self.status == IndicatorStatus.DEPRECATED
    
    @property
    def is_premium(self) -> bool:
        """Check if indicator requires premium subscription."""
        return self.requires_premium
    
    @property
    def is_free(self) -> bool:
        """Check if indicator is available on free tier."""
        return not self.requires_premium
    
    @property
    def has_default_params(self) -> bool:
        """Check if indicator has default parameters configured."""
        return self.default_params is not None
    
    def get_default_param(self, param_name: str, default_value: Any = None) -> Any:
        """Get a specific default parameter value."""
        if not self.default_params:
            return default_value
        return self.default_params.get(param_name, default_value)
    
    def is_accessible_to_user(self, user_is_premium: bool) -> bool:
        """Check if indicator is accessible to user based on subscription."""
        if not self.is_available:
            return False
        
        if self.is_premium and not user_is_premium:
            return False
            
        return True
    
    def update_status(self, status: IndicatorStatus) -> None:
        """Update indicator status with timestamp."""
        self.status = status
        self.updated_at = datetime.now()
    
    def enable(self) -> None:
        """Enable indicator."""
        self.enabled = True
        self.updated_at = datetime.now()
    
    def disable(self) -> None:
        """Disable indicator."""
        self.enabled = False
        self.updated_at = datetime.now()
    
    def make_premium(self) -> None:
        """Convert indicator to premium-only."""
        self.requires_premium = True
        self.updated_at = datetime.now()
    
    def make_free(self) -> None:
        """Convert indicator to free tier."""
        self.requires_premium = False
        self.updated_at = datetime.now()
    
    @classmethod
    def create_momentum_indicator(
        cls,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        default_params: Optional[Dict[str, Any]] = None,
        requires_premium: bool = False,
        sort_order: int = 0
    ) -> 'Indicator':
        """Factory method for momentum indicators."""
        return cls(
            indicator_id=str(uuid.uuid4()),
            name=name,
            display_name=display_name,
            category=IndicatorCategory.MOMENTUM,
            description=description,
            default_params=default_params,
            requires_premium=requires_premium,
            sort_order=sort_order
        )
    
    @classmethod
    def create_trend_indicator(
        cls,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        default_params: Optional[Dict[str, Any]] = None,
        requires_premium: bool = False,
        sort_order: int = 0
    ) -> 'Indicator':
        """Factory method for trend indicators."""
        return cls(
            indicator_id=str(uuid.uuid4()),
            name=name,
            display_name=display_name,
            category=IndicatorCategory.TREND,
            description=description,
            default_params=default_params,
            requires_premium=requires_premium,
            sort_order=sort_order
        )
    
    @classmethod
    def create_volume_indicator(
        cls,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        default_params: Optional[Dict[str, Any]] = None,
        requires_premium: bool = False,
        sort_order: int = 0
    ) -> 'Indicator':
        """Factory method for volume indicators."""
        return cls(
            indicator_id=str(uuid.uuid4()),
            name=name,
            display_name=display_name,
            category=IndicatorCategory.VOLUME,
            description=description,
            default_params=default_params,
            requires_premium=requires_premium,
            sort_order=sort_order
        )
    
    @classmethod  
    def create_volatility_indicator(
        cls,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        default_params: Optional[Dict[str, Any]] = None,
        requires_premium: bool = False,
        sort_order: int = 0
    ) -> 'Indicator':
        """Factory method for volatility indicators."""
        return cls(
            indicator_id=str(uuid.uuid4()),
            name=name,
            display_name=display_name,
            category=IndicatorCategory.VOLATILITY,
            description=description,
            default_params=default_params,
            requires_premium=requires_premium,
            sort_order=sort_order
        )


@dataclass
class DataSource:
    """
    Data source entity representing extraction source capabilities.
    
    Manages data source availability and premium access requirements.
    """
    
    source_id: str
    name: str  # Internal identifier (e.g., "technical_analysis")
    display_name: str  # User-friendly name (e.g., "Technical Analysis")
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Optional metadata
    description: Optional[str] = None
    requires_premium: bool = False
    
    def __post_init__(self):
        """Validate data source after initialization."""
        if not self.source_id:
            self.source_id = str(uuid.uuid4())
        
        if not self.name or not self.display_name:
            raise ValueError("Data source name and display_name are required")
    
    @property
    def is_available(self) -> bool:
        """Check if data source is available for use."""
        return self.enabled
    
    @property
    def is_premium(self) -> bool:
        """Check if data source requires premium subscription."""
        return self.requires_premium
    
    @property
    def is_free(self) -> bool:
        """Check if data source is available on free tier."""
        return not self.requires_premium
    
    def is_accessible_to_user(self, user_is_premium: bool) -> bool:
        """Check if data source is accessible to user based on subscription."""
        if not self.is_available:
            return False
        
        if self.is_premium and not user_is_premium:
            return False
            
        return True
    
    def enable(self) -> None:
        """Enable data source."""
        self.enabled = True
        self.updated_at = datetime.now()
    
    def disable(self) -> None:
        """Disable data source."""
        self.enabled = False
        self.updated_at = datetime.now()
    
    def make_premium(self) -> None:
        """Convert data source to premium-only."""
        self.requires_premium = True
        self.updated_at = datetime.now()
    
    def make_free(self) -> None:
        """Convert data source to free tier."""
        self.requires_premium = False
        self.updated_at = datetime.now()


@dataclass
class UserIndicatorAccess:
    """
    User access grant for premium indicators.
    
    Manages individual user access to premium indicators beyond subscription.
    """
    
    user_id: str
    indicator_id: str
    granted_at: datetime = field(default_factory=datetime.now)
    granted_by: str = "subscription"  # "subscription", "manual", "trial"
    expires_at: Optional[datetime] = None  # NULL = permanent
    
    @property
    def is_expired(self) -> bool:
        """Check if access grant has expired."""
        return (
            self.expires_at is not None and
            self.expires_at <= datetime.now()
        )
    
    @property
    def is_permanent(self) -> bool:
        """Check if access grant is permanent."""
        return self.expires_at is None
    
    @property
    def is_active(self) -> bool:
        """Check if access grant is currently active."""
        return not self.is_expired