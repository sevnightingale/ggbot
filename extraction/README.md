# Extraction Module

The Extraction Module automates data gathering from multiple sources including TradingView (ggShot signals), fetches and computes historical indicators using yfinance + pandas‑ta, and retrieves real‑time prices from configured exchanges.

## Structure

- `interfaces/`: Abstract interfaces that define how data sources and indicator computation should work
- `sources/`: Data source implementations
  - `tradingview/`: TradingView-specific extraction code
  - `exchange_api/`: Direct exchange API data collection
  - `third_party/`: Third-party data provider integrations
- `indicators/`: Technical indicator computation implementations
- `extraction_main.py`: Main entry point for the extraction process

## Key Components

- **DataSource Interface**: Abstract interface for all data sources
- **IndicatorComputer Interface**: Abstraction for technical indicator calculation

## Current Implementation

For the MVP, we primarily use TradingView for ggShot signals and yfinance/pandas-ta for additional technical indicators.