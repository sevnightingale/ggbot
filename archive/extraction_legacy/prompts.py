# ggbot/extraction/prompts.py
EXTRACTION_TASK = (
    "Navigate to the TradingView chart for BTC/USD on Coinbase at https://www.tradingview.com/chart/HiWAe2vQ/?symbol=COINBASE%3ABTCUSD. "
    "Wait for the chart to fully load and confirm that the GG-Shøt indicator title is visible beneath the chart title, Buy and Sell buttons, and the active ticker symbol in the top-left corner. "
    "If the GG-Shøt indicator is not visible, search for 'GG-Shøt' in the indicators list, add it, and wait for it to appear. "
    "Move the mouse cursor over the GG-Shøt indicator title until a row of icons appears. "
    "Identify the gear icon positioned to the right of the 'eye' (hide) icon and to the left of the 'trash' (remove indicator) icon, then click this gear icon to open the GG-Shøt settings panel. "
    "Wait for a pop-up window labeled 'GG-Shøt' to appear. If it does not appear, repeat the gear icon click. "
    "In this pop-up, click the 'Inputs' tab if it is not already active. "
    "Locate the 'Strategy' dropdown field, click it to expand the list, and select 'UNIVERSAL/USDT - 15M | Short-Term' as the new timeframe. "
    "Click anywhere on the chart to close the GG-Shøt settings panel. "
    "Next, update the TradingView chart's timeframe to match the indicator. Click the current chart timeframe beneath the ticker symbol in the top-left corner, open the dropdown menu, and select '15m' to synchronize it with the GG-Shøt indicator. "
    "Verify that both the GG-Shøt indicator label and the chart timeframe selector now display '15m'. "
    "Once the chart timeframe is confirmed, stop navigating and visually review the chart as follows: "

    "**Central Price Chart (White Candles & GG-Shøt Trendline):** "
    "- Observe the **white candles** in the center of the chart to get a sense of recent price action and overall market structure. "
    "- Look for the **GG-Shøt trendline**, which will be either **green for a Long signal** or **red for a Short signal**. "
    "- Check the last 10 candles for any **blue triangles** above or below the bars, representing **TP/TP2 signals** or **bounce signals**. "
    "- Note these observations: "
    "  - What color is the **trendline** (green or red)? "
    "  - Is the price bouncing off of the trendline, breaking through it, or far away from it? "
    "  - Are there any **blue triangles** near the last 5 candles? "

    "**Right-Side Labels (Take Profit & Stop Loss):** "
    "- Look along the **right edge** of the chart for **yellow labels** reading 'GG-Shøt: Take Profit'. List each of the four TP prices from 1-4. "
    "- Check for a **purple label** reading 'GG-Shøt: Trailing Stop Loss' and note its price. "
    "- Look for a **red or green label** reading 'GG-Shøt: Trend Line' (matching the center trendline color) and note its price if present. "
    "- Summarize these findings: "
    "  - Which **take profit levels** (yellow labels) are displayed? "
    "  - Is there a **trailing stop loss** (purple label), and at what price? "
    "  - What is the **trend line label** price? "

    "After reviewing the chart, compile your observations into a **technical analysis report** summarizing the chart’s state. Include: "
    "- The **current GG-Shøt trend color** (green for Long or red for Short). "
    "- The **presence** (or absence) of **blue triangles** in the last 10 candles. "
    "- Any **yellow take profit labels** and **their prices** (if visible). "
    "- Any **purple trailing stop loss label** and its price (if visible). "
    "- Any **trend line label** price on the right (if noted). "
    "- A brief overall assessment of the market structure based on the white candles. "
    "Keep your report clear and concise, avoiding unnecessary repetition. Once complete, use the `done` action to return this paragraph as plain text."
)

# Test task for ggShot indicator analysis
TEST_TASK = (
    "Navigate to the TradingView chart for BTC/USD on Coinbase at https://www.tradingview.com/chart/HiWAe2vQ/?symbol=COINBASE%3ABTCUSD. "
    "Wait for the chart to load fully. "
    "Visually inspect the GG-Shot indicator overlaid on the chart, and take note of any signals, trendlines, or other relevant indicators visible on the chart. "
    "Once noted, use the done action to complete the task."
)