# extraction/prompts.py
from pydantic import BaseModel

class GgShotSignals(BaseModel):
    signal: str                  # e.g., "LONG" or "SHORT"
    take_profits: list[dict]     # e.g., [{"tp1": 87500.0}, {"tp2": 88000.0}]
    trailing_stop_loss: float    # e.g., 85500.0

# Full extraction task (for later use)
EXTRACTION_TASK = (
    "If not already logged in, go to https://www.tradingview.com and log in with username 'tv_username' and password 'tv_password'. "
    "If a CAPTCHA appears, solve it to proceed. "
    "Then, navigate to the chart for BTC/USD on Coinbase at https://www.tradingview.com/chart/HiWAe2vQ/?symbol=COINBASE%3ABTCUSD. "
    "Extract the ggShot signals, including trend signals, TP levels, SL, and any additional context. "
    "Provide the output as a JSON object matching the GgShotSignals model."
)

# Test task for ggShot indicator analysis
TEST_TASK = (
    "Navigate to the TradingView chart for BTC/USD on Coinbase at https://www.tradingview.com/chart/HiWAe2vQ/?symbol=COINBASE%3ABTCUSD. "
    "Wait for the chart to load fully. "
    "Visually inspect the GG-Shot indicator overlaid on the chart, and take note of any signals, trendlines, or other relevant indicators visible on the chart. "
    "Once noted, use the done action to complete the task."
)