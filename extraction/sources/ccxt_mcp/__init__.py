"""
CCXT MCP data source package.

This package provides a DataSource implementation for the CCXT MCP,
enabling the extraction of market data from cryptocurrency exchanges.
"""

from extraction.sources.ccxt_mcp.ccxt_mcp_datasource import CCXTMCPDataSource

__all__ = ['CCXTMCPDataSource']