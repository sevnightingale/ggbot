"""
Technical Indicators package.

This package contains implementations of the IndicatorComputer interface
for calculating various technical indicators based on price data.
"""

from .pandas_ta_indicators import PandasTAIndicators

__all__ = ['PandasTAIndicators']