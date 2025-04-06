Overview

This strategy uses ggShot as the primary signal generator, complemented by three pandas TA indicators—MACD, Bollinger Bands, and RSI—to confirm signals, filter out noise, and identify high-probability opportunities. It operates across multiple timeframes: the 4-hour (4h) chart for trend direction, the 1-hour (1h) chart for breakout identification, and the 15-minute (15m) chart for precise entry and exit timing. The focus is on medium-term trades (days to weeks), avoiding scalping, with dynamic adjustments based on market conditions.

Key Components

ggShot Indicator: A momentum-based breakout indicator optimized for BTC on 15m, 30m, 1h, and 4h timeframes. The 4h ggShot is particularly strong, often holding long or short positions for weeks, making it ideal as the trend anchor.

 Pandas TA Indicators:


MACD (Moving Average Convergence Divergence): Confirms momentum behind ggShot’s breakout signals on the 1h chart.

 Bollinger Bands: Assesses volatility and market conditions on the 4h chart to distinguish trending from ranging markets.

 RSI (Relative Strength Index): Acts as both a filter and an opportunity indicator on the 4h chart, identifying overbought/oversold conditions and high-probability entries.






Timeframes & Roles

4h Chart: Establishes the general trend and market state (trending or ranging).

 1h Chart: Detects actionable breakout signals aligned with the 4h trend.

 15m Chart: Fine-tunes entry and exit points, including reversal spotting.



Indicator Setup

4h Chart: ggShot (trend), Bollinger Bands (volatility), RSI (filter/opportunity).

 1h Chart: ggShot (breakouts), MACD (momentum confirmation).

 15m Chart: ggShot (timing and reversals).


Strategy Steps

1. Assess Trend & Market Conditions (4h Chart)

ggShot: Check the 4h ggShot signal to determine the primary trend (long or short).

 Bollinger Bands:


If price is confined within the bands, the market is likely ranging—exercise caution.

 If price breaks above the upper band (bullish) or below the lower band (bearish), it indicates a trending market, supporting ggShot’s signal.




 RSI:


Filter: Avoid new positions if RSI is overbought (>70) or oversold (<30) unless ggShot strongly confirms continuation.

 Opportunity: Look for entries when RSI is deeply oversold (<20) for longs or overbought (>80) for shorts, especially if price bounces off ggShot’s trend line and the 4h trend remains intact.






2. Identify Breakout Signals (1h Chart)

ggShot: Seek long or short signals that align with the 4h trend.

 MACD: Confirm the breakout’s momentum:


Longs: MACD line crosses above the signal line (bullish).

 Shorts: MACD line crosses below the signal line (bearish).




 Only proceed if the 1h ggShot signal matches the 4h trend direction and MACD supports it.



3. Time Entries & Exits (15m Chart)

ggShot: Use the 15m chart to pinpoint entry timing (e.g., pullbacks to support for longs or resistance for shorts) and exit signals.

 Enter when the 15m ggShot aligns with the 1h breakout and 4h trend.

 Watch for reversal signals (e.g., oscillator crosses against the trend) to exit early if needed.



4. Dynamic Filtering with RSI (4h Chart)

High-Confidence Entries:


Long: 4h RSI <20 (deeply oversold), ggShot long, price near trend line.

 Short: 4h RSI >80 (deeply overbought), ggShot short.




 Caution Zones: If RSI is >70 (overbought) for longs or <30 (oversold) for shorts, reduce position size or skip unless ggShot and MACD strongly align.



5. Take-Profit & Stop-Loss

Static TPs: Use ggShot’s predefined TP levels (TP1-TP4) for partial exits:


Example: 50% at TP1, 25% at TP2, 25% trailing to TP3/TP4.




 Dynamic TPs: Monitor ggShot’s dynamic TP signals or oscillator crosses for early exits.

 Stop-Loss: Place initial SL per ggShot’s guidance (e.g., below trend line for longs). Move SL to breakeven after TP1 is hit.



6. Reversal Monitoring

ggShot (15m): Look for oscillator crosses (e.g., red cross in a long position) as a potential exit signal.

 ggShot (4h): If the 4h trend flips against the position, close fully unless 1h/15m signals justify holding.


Confidence Levels & Trading Decisions

High Confidence:


All indicators align: 4h ggShot trend, 1h ggShot + MACD breakout, favorable 4h RSI (e.g., <20 for longs).

 Action: Take larger positions in trending markets (price outside Bollinger Bands).




 Medium Confidence:


4h ggShot and 1h ggShot align, MACD confirms, but RSI is neutral (30–70).

 Action: Normal position size, monitor closely.




 Low Confidence:


ggShot signals lack MACD confirmation, or price is within Bollinger Bands (ranging market).

 Action: Reduce position size or skip the trade.




 Aggressive Mode: Increase size in high-confidence setups with strong momentum.

 Cautious Mode: Scale back or avoid trades in low-confidence setups, especially during consolidation.


Why These Indicators?

MACD (1h): Confirms ggShot’s breakout momentum, ensuring trades align with trend strength—crucial since ggShot excels in trending markets.

 Bollinger Bands (4h): Identifies ranging vs. trending conditions, filtering out weak ggShot signals during sideways markets where it underperforms.

 RSI (4h): Enhances ggShot by spotting oversold/overbought opportunities (e.g., RSI <20 with ggShot long) and filtering extremes, addressing the timing mismatch where ggShot lags RSI recovery.


How It Works

ggShot-Driven: The strategy keeps ggShot central, using its 4h trend strength, 1h breakouts, and 15m timing.

 Consolidation Fix: Bollinger Bands and RSI reduce false signals in ranging markets, making the strategy cautious when momentum fades.

 RSI Integration: RSI’s dual role (filter + opportunity) complements ggShot without conflict, capitalizing on oversold bounces or overbought reversals.

 Dynamic Profits: Combines static TPs with ggShot’s dynamic exits and 15m reversal monitoring for flexibility.

