# Decision Module Development Plan

## 1. Architecture and Interfaces

### 1.1. Strategy Interface
- Create `decision/interfaces/strategy.py` with a `Strategy` abstract base class
- Design a simple interface that takes market data and returns decisions with confidence scores and reasoning
- Ensure the interface is flexible enough to accommodate both rule-based and LLM-based strategies

### 1.2. LLM Provider Interface
- Create `decision/interfaces/llm_provider.py` with an `LLMProvider` abstract base class
- Design interface for calling different LLM APIs with standardized input/output formats
- Include methods for error handling, retry logic, and response parsing

### 1.3. Price Fetcher Interface
- Create `decision/interfaces/price_fetcher.py` with a `PriceFetcher` abstract base class
- Make live price fetching modular and swappable
- Initially implement `YFinancePriceFetcher` but design to easily swap in faster sources later (e.g., Binance API)

## 2. Implementation Components

### 2.1. DeepSeek Reasoner Integration
- Implement `DeepSeekProvider` class in `decision/llm_providers/deepseek_provider.py`
- Use the DeepSeek-R1 API endpoint with proper authentication
- Create a flexible prompt template system for trading decisions
- Include proper error handling and fallback mechanism

### 2.2. Test Trading Strategy
- Create `TestStrategy` in `decision/strategies/test_strategy.py` that uses the DeepSeek LLM
- Use only yfinance + pandas-ta indicator market data for initial testing
- Design a strategy that provides the LLM with:
  - Multi-timeframe data (15m, 1h, 4h, 1d)
  - Technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands)
  - Current market price (fetched in real-time)
  - Previous trade history and active positions (if available)
- Allow the LLM to make reasoned decisions with flexibility
- Implement risk management caps (e.g., max position size as % of capital)

### 2.3. Decision Manager
- Create `decision/decision_main.py` as the entry point
- Implement functions to fetch latest market data from the database
- Add live price fetching just before making decisions
- Create a decision loop that runs at scheduled intervals
- Implement context management for trade history preservation

## 3. Trade Context Management

### 3.1. Trade State Tracking
- Implement a simple state management system to track active trades
- Store the original decision context when entering a trade
- Maintain a conversation history with the LLM for each active trade
- Implement different prompt templates for:
  - New trade evaluation
  - Active trade management (adjust, hold, close)

### 3.2. Trade Lifecycle Support
- Create a temporary system for tracking trade state until the trades module is fully implemented
- Store trade decisions in a JSON file or simple database table
- Include entry price, position size, stop loss, take profit levels
- Add timestamp for each trade decision/update
- Ensure this data is passed to the LLM for context preservation

## 4. Prompt Engineering

- Design a system prompt that instructs the LLM about its trading role and constraints
- Create a structured user prompt template that includes:
  - Clear market data presentation across timeframes
  - Formatted technical indicators with explanations
  - Current price information
  - Active trade status (if any)
  - Request for specific outputs (decision, confidence, position size, reasoning)
- Design separate prompt templates for new trade evaluation vs. managing existing trades
- Allow for "intuition" while still maintaining some guardrails

## 5. Risk Management

- Implement configurable risk caps in the strategy layer:
  - Maximum position size as percentage of capital (e.g., 5%)
  - Maximum leverage restrictions
  - Trade frequency limits
- Store risk parameters in configuration files for easy adjustment
- Apply risk limits after the LLM makes its decision but before executing trades

## 6. Integration Points

- Connect to the database to fetch stored market data and indicators
- Add real-time price fetching just before decision making
- Prepare the output format for the structuring module
- Implement logging of all decisions and reasoning

## 7. Modularity and Customization

- Design the strategy system to be easily swappable and configurable
- Store strategy parameters in configuration files
- Allow for easy adjustment of decision thresholds and risk parameters
- Ensure the prompt system is flexible and can be updated without code changes

## 8. Testing Approach

- Create unit tests for the LLM provider and strategy implementations
- Develop test fixtures with sample market data
- Implement a dry-run mode that logs decisions without executing trades
- Add comprehensive logging to track decision quality

This plan focuses on creating a flexible, modular decision module that leverages DeepSeek's reasoning capabilities while allowing for easy customization. The approach prioritizes the ability to evolve the trading strategy over time based on performance, rather than locking into rigid rule sets. The addition of risk management safety nets, modular price fetching, and trade context preservation addresses key considerations for a robust system.