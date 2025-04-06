# Execution Module

The Execution Module securely interacts with configured exchange APIs or contracts, handling wallet management, transaction signing, and event monitoring.

## Structure

- `interfaces/`: Abstract interfaces for exchanges and authentication strategies
- `exchanges/`: Exchange adapter implementations
  - `gtrade/`: Gains Network gTrade integration
  - `binance/`: Binance exchange integration
  - `custom/`: Template for custom exchange adapters
- `auth/`: Authentication strategy implementations
- `execution_main.py`: Main entry point for trade execution

## Key Components

- **Exchange Interface**: Abstract base class for all exchange adapters
- **AuthenticationStrategy Interface**: Abstraction for different authentication methods

## Current Implementation

For the MVP, we primarily interact with Gains Network's gTrade platform using Coinbase AgentKit for wallet management.