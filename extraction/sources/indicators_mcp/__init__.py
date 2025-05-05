"""
Crypto Indicators MCP data source package.

This package provides a DataSource implementation for the Crypto Indicators MCP,
enabling the extraction of technical indicators computed by the MCP server.
"""

from extraction.sources.indicators_mcp.indicators_mcp_datasource import IndicatorsMCPDataSource

__all__ = ['IndicatorsMCPDataSource']