"""
Core type definitions for the Universal Data Layer.

This module defines all data structures used throughout the market intelligence
system, including query parameters, responses, and catalog definitions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import pandas as pd


class QueryFormat(Enum):
    """Output format modes for market intelligence queries."""
    RAW = "raw"  # Unprocessed data from adapter
    ANALYSIS = "analysis"  # Structured with metadata and insights
    LLM = "llm"  # Natural language optimized for agents


@dataclass
class QueryParams:
    """
    Standardized query parameters passed to adapters.

    Provides dictionary-like access to parameters while maintaining
    type safety and validation.
    """
    params: Dict[str, Any]

    def get(self, key: str, default: Any = None) -> Any:
        """Get parameter value with optional default."""
        return self.params.get(key, default)

    def __getattr__(self, name: str) -> Any:
        """Allow attribute access to parameters."""
        if name == 'params':
            return self.__dict__['params']
        return self.params.get(name)

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        return self.params[key]

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        return key in self.params


@dataclass
class AdapterResponse:
    """
    Standardized response format from data adapters.

    All adapters must return this structure to ensure consistency
    across the system.
    """
    data: Any  # The actual payload (DataFrame, dict, list, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Source info, timestamps, etc.
    confidence: float = 1.0  # Data quality score (0.0-1.0)
    related_queries: List[str] = field(default_factory=list)  # Suggested follow-up queries

    def __post_init__(self):
        """Validate confidence score."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


@dataclass
class MarketDataResponse:
    """
    Standardized response from MarketIntelligence gateway.

    This is what consumers receive after querying the gateway.
    """
    # Core fields
    data_type: str
    query_params: Dict[str, Any]
    timestamp: datetime

    # Data payload (varies by type)
    data: Any  # DataFrame for OHLCV, dict for sentiment, list for news

    # Agent-friendly fields
    summary: str = ""  # Natural language summary
    key_insights: List[str] = field(default_factory=list)  # Bullet points
    confidence: float = 1.0  # Data quality/freshness (0-1)
    signals: List[Dict[str, Any]] = field(default_factory=list)  # Actionable signals if any

    # Metadata
    source: str = ""  # Which adapter provided the data
    latency_ms: float = 0.0  # Query execution time
    from_cache: bool = False  # Whether result came from cache

    # Related queries (for discovery)
    related: List[str] = field(default_factory=list)


@dataclass
class CacheConfig:
    """Cache configuration from catalog."""
    backend: str  # redis | postgres | memory
    ttl: int  # Seconds until expiration
    key_pattern: str  # Template with {param} placeholders


@dataclass
class SourceConfig:
    """Source configuration from catalog."""
    adapter: str  # Adapter class name
    priority: int  # Lower = higher priority
    cost: float = 0.0  # Cost per query in USD
    rate_limit: Optional[int] = None  # Requests per minute
    required_env: List[str] = field(default_factory=list)  # Required env vars


@dataclass
class ParamSchema:
    """Parameter schema from catalog."""
    type: str  # string, integer, number, boolean, array, object
    required: bool = False
    default: Any = None
    description: str = ""
    enum: Optional[List[Any]] = None  # Valid values
    min: Optional[Union[int, float]] = None  # Minimum value (for numbers)
    max: Optional[Union[int, float]] = None  # Maximum value (for numbers)
    items: Optional[Dict[str, Any]] = None  # Schema for array items
    properties: Optional[Dict[str, Any]] = None  # Schema for object properties


@dataclass
class AgentFormat:
    """Agent formatting configuration from catalog."""
    summary_template: str = ""  # Jinja2 template for summary
    insights: List[str] = field(default_factory=list)  # Template for insights


@dataclass
class DataQuality:
    """Data quality targets from catalog."""
    latency_target_ms: Optional[int] = None
    freshness_target_seconds: Optional[int] = None
    confidence_scoring: bool = True


@dataclass
class CatalogEntry:
    """
    Complete catalog entry loaded from YAML.

    Represents a single data source type with all its configuration.
    """
    # Metadata
    name: str  # Unique identifier
    category: str  # Grouping (market_data, sentiment, etc.)
    description: str  # Human-readable explanation

    # Input definition
    query_params: Dict[str, ParamSchema]  # Parameter schemas

    # Source configuration
    sources: List[SourceConfig]  # Prioritized adapters

    # Caching strategy
    cache: CacheConfig

    # Output definition
    response_schema: Dict[str, Any]  # JSON Schema for validation

    # Agent integration
    agent_format: Optional[AgentFormat] = None

    # Quality & documentation
    data_quality: Optional[DataQuality] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)

    def validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate query parameters against schema.

        Returns validated params with defaults applied.
        Raises ValueError if validation fails.
        """
        validated = {}

        for param_name, schema in self.query_params.items():
            value = params.get(param_name)

            # Check required
            if schema.required and value is None:
                raise ValueError(f"Required parameter '{param_name}' is missing")

            # Apply default
            if value is None:
                value = schema.default

            # Skip further validation if still None
            if value is None:
                continue

            # Type validation
            expected_type = schema.type
            if expected_type == 'string' and not isinstance(value, str):
                raise ValueError(f"Parameter '{param_name}' must be string, got {type(value).__name__}")
            elif expected_type == 'integer' and not isinstance(value, int):
                raise ValueError(f"Parameter '{param_name}' must be integer, got {type(value).__name__}")
            elif expected_type == 'number' and not isinstance(value, (int, float)):
                raise ValueError(f"Parameter '{param_name}' must be number, got {type(value).__name__}")
            elif expected_type == 'boolean' and not isinstance(value, bool):
                raise ValueError(f"Parameter '{param_name}' must be boolean, got {type(value).__name__}")
            elif expected_type == 'array' and not isinstance(value, list):
                raise ValueError(f"Parameter '{param_name}' must be array, got {type(value).__name__}")
            elif expected_type == 'object' and not isinstance(value, dict):
                raise ValueError(f"Parameter '{param_name}' must be object, got {type(value).__name__}")

            # Enum validation
            if schema.enum and value not in schema.enum:
                raise ValueError(f"Parameter '{param_name}' must be one of {schema.enum}, got {value}")

            # Range validation
            if schema.min is not None and value < schema.min:
                raise ValueError(f"Parameter '{param_name}' must be >= {schema.min}, got {value}")
            if schema.max is not None and value > schema.max:
                raise ValueError(f"Parameter '{param_name}' must be <= {schema.max}, got {value}")

            validated[param_name] = value

        return validated

    def build_cache_key(self, params: Dict[str, Any]) -> str:
        """Build cache key from template and parameters."""
        return self.cache.key_pattern.format(**params)

    def format_for_agent(self, response: AdapterResponse, query_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Format adapter response for agent consumption using template."""
        if not self.agent_format:
            # Fallback to basic formatting
            return {
                'summary': f"Retrieved {self.name} data",
                'insights': [],
                'data': response.data
            }

        # Prepare template context with both data and params
        template_context = {}
        if isinstance(response.data, dict):
            template_context.update(response.data)
        if query_params:
            template_context.update(query_params)

        # Apply summary template
        try:
            summary = self.agent_format.summary_template.format(**template_context)
        except KeyError as e:
            # Template has missing variable, use basic summary
            summary = f"Retrieved {self.name} data (template error: missing {e})"

        # Generate insights (templates can reference response data and params)
        insights = []
        for insight_template in self.agent_format.insights:
            try:
                insight = insight_template.format(**template_context)
                insights.append(insight)
            except (KeyError, AttributeError):
                # Skip insights with template errors
                continue

        return {
            'summary': summary,
            'insights': insights,
            'data': response.data,
            'confidence': response.confidence
        }


class DataSourceError(Exception):
    """Base exception for data source errors."""
    pass


class CatalogError(Exception):
    """Exception for catalog-related errors."""
    pass


class CacheError(Exception):
    """Exception for cache-related errors."""
    pass


class AdapterError(Exception):
    """Exception for adapter-related errors."""
    pass
