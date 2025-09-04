"""
Advanced Python Preprocessor for Technical Indicators.

This module provides a unified interface to the modular preprocessor system,
routing indicator requests to specialized preprocessor classes.
"""

import pandas as pd
from typing import Dict, Any

from core.common.logger import logger
from .preprocessors import get_preprocessor, is_preprocessor_available, list_available_preprocessors


class TechnicalAnalysisPreprocessor:
    """
    Advanced technical analysis preprocessor router.
    
    Routes indicator requests to specialized preprocessor modules,
    providing sophisticated analysis equivalent to the JavaScript preprocessors.
    """
    
    def __init__(self):
        """Initialize the preprocessor router."""
        self._log = logger.bind(component="ta_preprocessor")
        available_indicators = list_available_preprocessors()
        self._log.info(f"Initialized TechnicalAnalysisPreprocessor with {len(available_indicators)} indicators: {', '.join(available_indicators)}")
    
    def preprocess_rsi(self, rsi_values: pd.Series, prices: pd.Series = None, 
                      period: int = 14, **kwargs) -> Dict[str, Any]:
        """Route RSI preprocessing to specialized RSI preprocessor."""
        preprocessor = get_preprocessor('rsi')
        if preprocessor:
            return preprocessor.preprocess(rsi_values, prices, period, **kwargs)
        else:
            return {"error": "RSI preprocessor not available"}
    
    def preprocess_macd(self, macd_line: pd.Series, signal_line: pd.Series, 
                       histogram: pd.Series, prices: pd.Series = None, **kwargs) -> Dict[str, Any]:
        """Route MACD preprocessing to specialized MACD preprocessor."""
        preprocessor = get_preprocessor('macd')
        if preprocessor:
            return preprocessor.preprocess(macd_line, signal_line, histogram, prices, **kwargs)
        else:
            return {"error": "MACD preprocessor not available"}
    
    def preprocess_stochastic(self, k_percent: pd.Series, d_percent: pd.Series, 
                             prices: pd.Series = None, **kwargs) -> Dict[str, Any]:
        """Route Stochastic preprocessing to specialized Stochastic preprocessor."""
        preprocessor = get_preprocessor('stochastic')
        if preprocessor:
            return preprocessor.preprocess(k_percent, d_percent, prices, **kwargs)
        else:
            return {"error": "Stochastic preprocessor not available"}
    
    def preprocess_williams_r(self, williams_r: pd.Series, prices: pd.Series = None, 
                             length: int = 14, **kwargs) -> Dict[str, Any]:
        """Route Williams %R preprocessing to specialized Williams %R preprocessor."""
        preprocessor = get_preprocessor('williams_r')
        if preprocessor:
            return preprocessor.preprocess(williams_r, prices, length, **kwargs)
        else:
            return {"error": "Williams %R preprocessor not available"}
    
    def preprocess_cci(self, cci: pd.Series, prices: pd.Series = None, 
                      length: int = 20, **kwargs) -> Dict[str, Any]:
        """Route CCI preprocessing to specialized CCI preprocessor."""
        preprocessor = get_preprocessor('cci')
        if preprocessor:
            return preprocessor.preprocess(cci, prices, length, **kwargs)
        else:
            return {"error": "CCI preprocessor not available"}
    
    def preprocess_mfi(self, mfi: pd.Series, prices: pd.Series = None, 
                      length: int = 14, **kwargs) -> Dict[str, Any]:
        """Route MFI preprocessing to specialized MFI preprocessor."""
        preprocessor = get_preprocessor('mfi')
        if preprocessor:
            return preprocessor.preprocess(mfi, prices, length, **kwargs)
        else:
            return {"error": "MFI preprocessor not available"}
    
    # Bollinger Bands preprocessing - placeholder for future implementation
    def preprocess_bollinger_bands(self, upper: pd.Series, middle: pd.Series, lower: pd.Series,
                                  prices: pd.Series, **kwargs) -> Dict[str, Any]:
        """Route Bollinger Bands preprocessing to specialized preprocessor (future implementation)."""
        preprocessor = get_preprocessor('bollinger_bands')
        if preprocessor:
            return preprocessor.preprocess(upper, middle, lower, prices, **kwargs)
        else:
            # Simple fallback analysis for now
            current_price = float(prices.iloc[-1])
            current_upper = float(upper.iloc[-1])
            current_middle = float(middle.iloc[-1])
            current_lower = float(lower.iloc[-1])
            
            return {
                "indicator": "Bollinger_Bands",
                "current": {
                    "price": round(current_price, 4),
                    "upper": round(current_upper, 4),
                    "middle": round(current_middle, 4), 
                    "lower": round(current_lower, 4),
                    "bandwidth": round((current_upper - current_lower) / current_middle * 100, 2),
                    "percent_b": round((current_price - current_lower) / (current_upper - current_lower), 3)
                },
                "analysis": {
                    "position": self._get_bb_position(current_price, current_upper, current_middle, current_lower),
                    "squeeze": False  # Simplified
                },
                "summary": f"BB position: {self._get_bb_position(current_price, current_upper, current_middle, current_lower)}"
            }
    
    def _get_bb_position(self, price: float, upper: float, middle: float, lower: float) -> str:
        """Simple Bollinger Band position analysis."""
        if price > upper:
            return "above_upper"
        elif price < lower:
            return "below_lower"
        elif price > middle:
            return "upper_half"
        else:
            return "lower_half"
    
    def is_preprocessor_available(self, indicator: str) -> bool:
        """Check if a preprocessor is available for the given indicator."""
        return is_preprocessor_available(indicator)
    
    def list_available_preprocessors(self) -> list:
        """List all available preprocessor indicators."""
        return list_available_preprocessors()