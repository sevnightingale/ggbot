# Decision Module

The Decision Module analyzes extracted data, maintains active trade oversight, and decides on opening, adjusting, or closing positions using configurable trading strategies and reasoning LLMs.

## Structure

- `interfaces/`: Abstract interfaces for strategies and LLM providers
- `strategies/`: Implementations of different trading strategies
- `llm_providers/`: Implementations of different LLM services
- `decision_main.py`: Main entry point for decision making

## Key Components

- **Strategy Interface**: Abstract base class for all trading strategies
- **LLMProvider Interface**: Abstraction for different LLM services

## Current Implementation

For the MVP, we use a GGShot-based strategy and DeepSeek for reasoning.