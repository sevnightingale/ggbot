"""
YFinance data source package.

This package provides a DataSource implementation using the yfinance library
for fetching market data from Yahoo Finance.
"""

from .yfinance_datasource import YFinanceDataSource

__all__ = ['YFinanceDataSource']