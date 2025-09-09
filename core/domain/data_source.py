"""
Data Source and Data Point Domain Models

Represents the reference data structure for frontend UI population.
Data sources contain data points, which map to config_data JSONB values.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class DataSource:
    """
    Data source entity for categorizing extraction sources.
    
    Examples: "Technical Analysis", "Signals in Group Chats", etc.
    """
    
    source_id: str
    name: str  # Internal identifier: "technical_analysis", "signals_group_chats"
    display_name: str  # User-friendly: "Technical Analysis", "Signals in Group Chats"
    enabled: bool = True
    requires_premium: bool = False
    sort_order: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate data source after initialization."""
        if not self.source_id or not self.name or not self.display_name:
            raise ValueError("source_id, name, and display_name are required")


@dataclass
class DataPoint:
    """
    Data point entity representing specific indicators/signals within a data source.
    
    Contains config_values array that maps to what gets stored in config_data JSONB.
    """
    
    data_point_id: str
    source_id: str  # References DataSource.source_id
    name: str  # Internal identifier: "RSI", "MACD", "ggShot"
    display_name: str  # User-friendly: "RSI (Relative Strength Index)"
    config_values: list[str]  # Values for config_data: ["RSI_5m", "RSI_15m", ...]
    enabled: bool = True
    requires_premium: bool = False
    sort_order: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate data point after initialization."""
        if not all([self.data_point_id, self.source_id, self.name, self.display_name]):
            raise ValueError("data_point_id, source_id, name, and display_name are required")
        if not self.config_values:
            raise ValueError("config_values cannot be empty")
    
    @property
    def is_premium(self) -> bool:
        """Check if this data point requires premium access."""
        return self.requires_premium
    
    @property
    def is_available(self) -> bool:
        """Check if this data point is available for use."""
        return self.enabled
    
    def get_config_values_for_timeframes(self, timeframes: list[str]) -> list[str]:
        """
        Get config values filtered by specific timeframes.
        
        Args:
            timeframes: List of timeframes like ["5m", "15m", "1h"]
            
        Returns:
            Filtered config values matching the timeframes
        """
        if not timeframes:
            return self.config_values.copy()
        
        filtered = []
        for timeframe in timeframes:
            matching = [cv for cv in self.config_values if cv.endswith(f"_{timeframe}")]
            filtered.extend(matching)
        
        return filtered
    
    @classmethod
    def create_technical_indicator(
        cls,
        source_id: str,
        name: str,
        display_name: str,
        timeframes: list[str] = None,
        description: str = None,
        requires_premium: bool = False,
        sort_order: int = 0
    ) -> 'DataPoint':
        """
        Factory method to create technical indicator data point.
        
        Args:
            source_id: ID of the technical analysis data source
            name: Indicator name (RSI, MACD, etc.)
            display_name: User-friendly name
            timeframes: List of timeframes, defaults to standard set
            description: Optional description
            requires_premium: Whether this indicator requires premium access
            sort_order: Display order
        """
        if timeframes is None:
            timeframes = ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        
        config_values = [f"{name}_{tf}" for tf in timeframes]
        
        return cls(
            data_point_id=str(uuid.uuid4()),
            source_id=source_id,
            name=name,
            display_name=display_name,
            config_values=config_values,
            description=description,
            requires_premium=requires_premium,
            sort_order=sort_order
        )
    
    @classmethod
    def create_signal_data_point(
        cls,
        source_id: str,
        name: str,
        display_name: str,
        description: str = None,
        requires_premium: bool = True,
        sort_order: int = 0
    ) -> 'DataPoint':
        """
        Factory method to create signal-based data point.
        
        Args:
            source_id: ID of the signals data source
            name: Signal name (ggShot, etc.)
            display_name: User-friendly name
            description: Optional description
            requires_premium: Whether this signal requires premium access
            sort_order: Display order
        """
        return cls(
            data_point_id=str(uuid.uuid4()),
            source_id=source_id,
            name=name,
            display_name=display_name,
            config_values=[name],  # Signals typically use single value
            description=description,
            requires_premium=requires_premium,
            sort_order=sort_order
        )


@dataclass
class DataSourceWithPoints:
    """
    Composite entity containing a data source with its associated data points.
    
    Used for frontend API responses that need the full hierarchy.
    """
    
    source: DataSource
    data_points: list[DataPoint] = field(default_factory=list)
    
    def get_available_points(self) -> list[DataPoint]:
        """Get only enabled data points."""
        return [dp for dp in self.data_points if dp.is_available]
    
    def get_premium_points(self) -> list[DataPoint]:
        """Get premium data points."""
        return [dp for dp in self.data_points if dp.is_premium]
    
    def get_free_points(self) -> list[DataPoint]:
        """Get free (non-premium) data points."""
        return [dp for dp in self.data_points if not dp.is_premium]
    
    def filter_by_user_access(self, paid_data_points: list[str]) -> list[DataPoint]:
        """
        Filter data points by user's premium access.
        
        Args:
            paid_data_points: List of data point names user has access to
            
        Returns:
            List of data points user can access (free + paid ones they have)
        """
        accessible = []
        for dp in self.get_available_points():
            if not dp.is_premium or dp.name in paid_data_points:
                accessible.append(dp)
        return accessible