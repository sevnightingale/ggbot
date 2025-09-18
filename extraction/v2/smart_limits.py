"""
Smart period limits for technical indicators based on research.

Simple lookup-based system that implements the research findings
from DOCS/RESEARCH.md with minimal complexity.
"""


def get_smart_limit(indicator: str, timeframe: str) -> int:
    """
    Get optimal candle limit for indicator+timeframe based on research.

    Full implementation of research matrix from DOCS/RESEARCH.md
    covering all 21 indicators across 7 timeframes.

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
        "bollinger": "bbands",
        "bb_width": "bbwidth",
        "parabolic_sar": "psar",
        "sar": "psar",
        "rate_of_change": "roc",
        "momentum": "roc",
        "dc": "donchian",
        "donchian_channels": "donchian",
        "kc": "keltner",
        "keltner_channels": "keltner"
    }
    indicator = aliases.get(indicator, indicator)

    # Full research matrix implementation
    # Based on Summary Matrix from DOCS/RESEARCH.md lines 970-991

    research_matrix = {
        # Core Oscillators
        "rsi": {
            "1h": 100, "2h": 100, "4h": 100, "6h": 100,
            "12h": 100, "1d": 100, "1w": 100
        },
        "stochastic": {
            "1h": 80, "2h": 80, "4h": 100, "6h": 100,
            "12h": 100, "1d": 100, "1w": 100
        },
        "williams_r": {
            "1h": 80, "2h": 80, "4h": 100, "6h": 100,
            "12h": 100, "1d": 100, "1w": 100
        },
        "cci": {
            "1h": 100, "2h": 100, "4h": 100, "6h": 100,
            "12h": 100, "1d": 100, "1w": 100
        },
        "mfi": {
            "1h": 100, "2h": 100, "4h": 100, "6h": 100,
            "12h": 100, "1d": 100, "1w": 100
        },

        # Trend Indicators
        "sma": {
            "1h": 100, "2h": 100, "4h": 100, "6h": 100,
            "12h": 100, "1d": 150, "1w": 150
        },
        "ema": {
            "1h": 100, "2h": 100, "4h": 100, "6h": 100,
            "12h": 100, "1d": 100, "1w": 100
        },
        "macd": {
            "1h": 150, "2h": 150, "4h": 150, "6h": 150,
            "12h": 150, "1d": 200, "1w": 200
        },
        "adx": {
            "1h": 100, "2h": 100, "4h": 100, "6h": 100,
            "12h": 100, "1d": 100, "1w": 100
        },
        "aroon": {
            "1h": 100, "2h": 100, "4h": 100, "6h": 100,
            "12h": 100, "1d": 100, "1w": 100
        },

        # Volatility Indicators
        "atr": {
            "1h": 100, "2h": 100, "4h": 100, "6h": 100,
            "12h": 100, "1d": 100, "1w": 100
        },
        "bbands": {
            "1h": 100, "2h": 100, "4h": 100, "6h": 100,
            "12h": 120, "1d": 150, "1w": 150
        },
        "bbwidth": {
            "1h": 100, "2h": 100, "4h": 100, "6h": 100,
            "12h": 120, "1d": 150, "1w": 150
        },
        "keltner": {
            "1h": 100, "2h": 100, "4h": 100, "6h": 100,
            "12h": 100, "1d": 100, "1w": 100
        },
        "donchian": {
            "1h": 100, "2h": 100, "4h": 100, "6h": 100,
            "12h": 100, "1d": 100, "1w": 100
        },

        # Volume Indicators
        "obv": {
            "1h": 80, "2h": 80, "4h": 100, "6h": 100,
            "12h": 100, "1d": 100, "1w": 100
        },
        "vwap": {
            "1h": 120, "2h": 120, "4h": 120, "6h": None,
            "12h": None, "1d": None, "1w": None
        },

        # Advanced Indicators
        "trix": {
            "1h": 100, "2h": 100, "4h": 100, "6h": 120,
            "12h": 120, "1d": 120, "1w": 120
        },
        "psar": {
            "1h": 60, "2h": 60, "4h": 80, "6h": 80,
            "12h": 100, "1d": 100, "1w": 100
        },
        "roc": {
            "1h": 80, "2h": 80, "4h": 60, "6h": 60,
            "12h": 60, "1d": 60, "1w": 60
        },
        "vortex": {
            "1h": 80, "2h": 80, "4h": 80, "6h": 80,
            "12h": 80, "1d": 80, "1w": 80
        }
    }

    # Look up exact research recommendation
    if indicator in research_matrix:
        timeframe_limits = research_matrix[indicator]
        if timeframe in timeframe_limits:
            limit = timeframe_limits[timeframe]
            # None means indicator not applicable to this timeframe
            if limit is None:
                return 100  # Fallback for inapplicable combinations
            return limit

    # Fallback for unknown indicators
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