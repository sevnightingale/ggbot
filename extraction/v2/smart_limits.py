"""
Smart period limits for technical indicators based on research.

Simple lookup-based system that implements the research findings
from DOCS/RESEARCH.md with minimal complexity.
"""


def get_smart_limit(indicator: str, timeframe: str) -> int:
    """
    Get optimal candle limit for indicator+timeframe based on research.

    Args:
        indicator: Indicator name (e.g., "rsi", "macd")
        timeframe: Timeframe (e.g., "1h", "4h", "1d")

    Returns:
        Optimal number of candles to fetch
    """
    # Normalize indicator name
    indicator = indicator.lower().strip()

    # Handle aliases
    aliases = {
        "bollinger_bands": "bbands",
        "bb": "bbands",
        "bb_width": "bbwidth",
        "parabolic_sar": "psar",
        "rate_of_change": "roc"
    }
    indicator = aliases.get(indicator, indicator)

    # MACD - the heavy hitter (needs more data for EMA convergence)
    if indicator == "macd":
        return 150 if timeframe in ["1h", "2h", "4h", "6h", "12h"] else 200

    # PSAR - scales up with timeframe
    elif indicator == "psar":
        if timeframe in ["1h", "2h"]:
            return 60
        elif timeframe in ["4h", "6h"]:
            return 80
        else:
            return 100

    # Fast oscillators - lighter on intraday
    elif indicator in ["stochastic", "williams_r", "obv"]:
        return 80 if timeframe in ["1h", "2h"] else 100

    # Consistent light indicators
    elif indicator in ["roc", "vortex"]:
        return 80

    # VWAP - intraday only, slightly heavier
    elif indicator == "vwap":
        return 120 if timeframe in ["1h", "2h", "4h"] else 100

    # Bollinger variants - scale up for daily+
    elif indicator in ["bbands", "bbwidth"]:
        if timeframe in ["12h"]:
            return 120
        elif timeframe in ["1d", "1w"]:
            return 150
        else:
            return 100

    # TRIX - scale up for longer timeframes
    elif indicator == "trix":
        return 120 if timeframe in ["6h", "12h", "1d", "1w"] else 100

    # SMA - slightly more for daily+
    elif indicator == "sma":
        return 150 if timeframe in ["1d", "1w"] else 100

    # Standard for most indicators (RSI, CCI, MFI, EMA, ADX, Aroon, ATR, etc.)
    else:
        return 100


def get_batch_limit(indicators: list, timeframe: str) -> int:
    """
    Get the maximum limit needed for a batch of indicators.
    Used when fetching data once for multiple indicators.

    Args:
        indicators: List of indicator names
        timeframe: Timeframe

    Returns:
        Maximum limit across all indicators
    """
    return max(get_smart_limit(indicator, timeframe) for indicator in indicators)


def get_efficiency_report(indicators: list, timeframe: str) -> dict:
    """
    Show efficiency gains vs static 200 limit.

    Args:
        indicators: List of indicators
        timeframe: Timeframe

    Returns:
        Dictionary with savings information
    """
    smart_limit = get_batch_limit(indicators, timeframe)
    static_limit = 200

    savings = static_limit - smart_limit
    savings_percent = (savings / static_limit * 100) if static_limit > 0 else 0

    return {
        "timeframe": timeframe,
        "indicators": len(indicators),
        "smart_limit": smart_limit,
        "static_limit": static_limit,
        "candles_saved": savings,
        "percent_reduction": round(savings_percent, 1)
    }