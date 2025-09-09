# Decision Engine Prompt Templates

This directory contains the hardcoded prompt structures for each decision type in the V2 engine.

## Design Philosophy

- **User Simplicity**: Users only configure their trading strategy (no template variables)
- **Full Context**: LLM always receives comprehensive market data across all timeframes
- **Flexible Targeting**: Users can reference specific timeframes in their strategy
- **Consistent Quality**: System controls prompt structure for optimal results

## Template Structure

Each prompt follows this pattern:

1. **Role Definition**: Clear explanation of the task
2. **Market Data**: Full 7-timeframe technical analysis
3. **Volume Analysis**: Current volume confirmation data
4. **Position Context** (position management only): Current position details
5. **User Strategy**: The user's configured trading approach
6. **Task Instructions**: How to use strategy with provided data
7. **Output Format**: Standardized response structure

## Template Variables

All templates receive these variables:
- `symbol`: Trading pair (e.g., "BTC/USDT")
- `current_price`: Formatted price (e.g., "$45,123.45")
- `market_data`: Multi-timeframe technical indicators
- `volume_analysis`: Volume confirmation with confidence levels
- `user_strategy`: User's configured trading strategy text

**Position Management Only:**
- `position_data`: Current position performance and original context

**Signal Validation Only:**
- `signal_context`: External signal details to validate

## Usage

These templates are loaded by the decision engine and populated with real-time data before being sent to the LLM.

```python
from decision.prompts.opportunity_analysis import build_opportunity_analysis_prompt

prompt = build_opportunity_analysis_prompt(
    symbol="BTC/USDT",
    current_price="$45,123.45",
    market_data=formatted_indicators,
    volume_analysis=volume_confirmation,
    user_strategy="Use 15min RSI > 70 and 1hr MACD confirmation..."
)
```

## File Descriptions

- `signal_validation.py`: Validates external signals (ggShot, Telegram)
- `opportunity_analysis.py`: Finds new trading opportunities autonomously
- `position_management.py`: Manages existing positions (hold vs close)

Each file contains a single `build_*_prompt()` function that returns the complete prompt string.