"""
Extraction module interfaces.

This package defines the interfaces for data sources and indicator computers
that the extraction module uses to fetch and process market data.
"""

from .data_source import DataSource
from .indicator_computer import IndicatorComputer

__all__ = ['DataSource', 'IndicatorComputer']