"""
Opportunity Analysis Prompt Template

Used for autonomous trading when looking for new trading opportunities.
The user's trading strategy determines entry points and position sizing.
"""

def build_opportunity_analysis_prompt(
    symbol: str,
    current_price: str,
    market_data: str,
    volume_analysis: str,
    user_strategy: str,
    ggshot_signals: str = None,
    market_intelligence: str = None
) -> str:
    """Build opportunity analysis prompt with hardcoded structure."""

    # Build ggshot section if signals are available
    ggshot_section = ""
    if ggshot_signals and ggshot_signals.strip():
        ggshot_section = f"""
## GGSHOT PREMIUM SIGNALS
ggShot is a premium signal provider with proven accuracy. Here are the latest ggShot signals for {symbol}:

{ggshot_signals}

NOTE: ggShot signals provide additional context but should be validated against your own technical analysis. Consider directional agreement/disagreement across timeframes and how it aligns with your strategy.
"""

    # Build market intelligence section if available
    market_intel_section = ""
    if market_intelligence and market_intelligence.strip():
        market_intel_section = f"""
## MARKET INTELLIGENCE
Additional market context beyond technical indicators:

{market_intelligence}

NOTE: This supplemental data provides context about market conditions (funding rates, macro environment, on-chain activity, sentiment, news). Consider how these factors may impact your technical setup and strategy execution.
"""

    return f"""You are an expert cryptocurrency trader analyzing market opportunities. Your job is to identify potential trading opportunities based on current market conditions and your configured trading strategy.

## MARKET DATA ANALYSIS
Here is comprehensive technical analysis across all 7 timeframes (5m, 15m, 30m, 1h, 4h, 1d, 1w) for {symbol} at current price {current_price}:

{market_data}

## VOLUME CONFIRMATION ANALYSIS
Current volume analysis for trade confirmation:

{volume_analysis}
{ggshot_section}{market_intel_section}
## YOUR TRADING STRATEGY
{user_strategy}

## TASK INSTRUCTIONS
You strictly apply the user's trading strategy below. Do not invent additional rules or override the strategy's logic. Do not reference indicators or data not provided in the market data above. If your strategy requires indicators not available, or if market data appears stale or incomplete, mention these issues in your reasoning.

Use your trading strategy above to analyze the provided market data and identify trading opportunities. If your strategy specifies certain timeframes or indicators, focus on that data while having full context of all timeframes available.

Based on your analysis:
- Is there a trading opportunity (long/short) or should you wait?
- How confident are you in this opportunity?
- What stop loss and take profit levels align with your strategy?

Your reasoning should cite specific indicator values from the market data that triggered your strategy's rules.

## OUTPUT FORMAT
ACTION: [long/short/wait]
CONFIDENCE: [0.000-1.000]
REASONING: [Explain how your strategy interprets the current market data and identifies this opportunity]
STOP_LOSS: [price or null]
TAKE_PROFIT: [price or null]"""