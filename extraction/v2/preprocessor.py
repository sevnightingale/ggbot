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

    def preprocess_sma(self, sma: pd.Series, prices: pd.Series = None,
                      length: int = 20, **kwargs) -> Dict[str, Any]:
        """Route SMA preprocessing to specialized SMA preprocessor."""
        preprocessor = get_preprocessor('sma')
        if preprocessor:
            return preprocessor.preprocess(sma, prices, length=length, **kwargs)
        else:
            return {"error": "SMA preprocessor not available"}

    def preprocess_ema(self, ema: pd.Series, prices: pd.Series = None,
                      length: int = 20, **kwargs) -> Dict[str, Any]:
        """Route EMA preprocessing to specialized EMA preprocessor."""
        preprocessor = get_preprocessor('ema')
        if preprocessor:
            return preprocessor.preprocess(ema, prices, length=length, **kwargs)
        else:
            return {"error": "EMA preprocessor not available"}

    def preprocess_roc(self, roc: pd.Series, prices: pd.Series = None,
                      length: int = 10, **kwargs) -> Dict[str, Any]:
        """Route ROC preprocessing to specialized ROC preprocessor."""
        preprocessor = get_preprocessor('roc')
        if preprocessor:
            return preprocessor.preprocess(roc, prices, length=length, **kwargs)
        else:
            return {"error": "ROC preprocessor not available"}

    def preprocess_psar(self, psar: pd.Series, prices: pd.Series = None,
                       high_prices: pd.Series = None, low_prices: pd.Series = None, **kwargs) -> Dict[str, Any]:
        """Route PSAR preprocessing to specialized PSAR preprocessor."""
        preprocessor = get_preprocessor('psar')
        if preprocessor:
            return preprocessor.preprocess(psar, prices, high_prices, low_prices, **kwargs)
        else:
            return {"error": "PSAR preprocessor not available"}

    def preprocess_obv(self, obv: pd.Series, prices: pd.Series = None,
                      volumes: pd.Series = None, **kwargs) -> Dict[str, Any]:
        """Route OBV preprocessing to specialized OBV preprocessor."""
        preprocessor = get_preprocessor('obv')
        if preprocessor:
            return preprocessor.preprocess(obv, prices, volumes, **kwargs)
        else:
            return {"error": "OBV preprocessor not available"}

    def preprocess_bbwidth(self, bbwidth: pd.Series, prices: pd.Series = None,
                          length: int = 20, std: float = 2.0, **kwargs) -> Dict[str, Any]:
        """Route Bollinger Band Width preprocessing to specialized preprocessor."""
        preprocessor = get_preprocessor('bbwidth')
        if preprocessor:
            return preprocessor.preprocess(bbwidth, prices, length=length, std=std, **kwargs)
        else:
            return {"error": "BBWidth preprocessor not available"}

    def preprocess_donchian(self, upper: pd.Series, middle: pd.Series, lower: pd.Series,
                           prices: pd.Series = None, length: int = 20, **kwargs) -> Dict[str, Any]:
        """Route Donchian Channels preprocessing to specialized preprocessor."""
        preprocessor = get_preprocessor('donchian')
        if preprocessor:
            return preprocessor.preprocess(upper, middle, lower, prices, length=length, **kwargs)
        else:
            return {"error": "Donchian preprocessor not available"}

    def preprocess_keltner(self, upper: pd.Series, middle: pd.Series, lower: pd.Series,
                          prices: pd.Series = None, length: int = 20, multiplier: float = 2.0, **kwargs) -> Dict[str, Any]:
        """Route Keltner Channels preprocessing to specialized preprocessor."""
        preprocessor = get_preprocessor('keltner')
        if preprocessor:
            return preprocessor.preprocess(upper, middle, lower, prices, length=length, multiplier=multiplier, **kwargs)
        else:
            return {"error": "Keltner preprocessor not available"}

    def preprocess_trix(self, trix: pd.Series, prices: pd.Series = None,
                       length: int = 14, **kwargs) -> Dict[str, Any]:
        """Route TRIX preprocessing to specialized TRIX preprocessor."""
        preprocessor = get_preprocessor('trix')
        if preprocessor:
            return preprocessor.preprocess(trix, prices, length=length, **kwargs)
        else:
            return {"error": "TRIX preprocessor not available"}

    def preprocess_vortex(self, vi_plus: pd.Series, vi_minus: pd.Series, prices: pd.Series = None,
                         length: int = 14, **kwargs) -> Dict[str, Any]:
        """Route Vortex preprocessing to specialized Vortex preprocessor."""
        preprocessor = get_preprocessor('vortex')
        if preprocessor:
            return preprocessor.preprocess(vi_plus, vi_minus, prices, length=length, **kwargs)
        else:
            return {"error": "Vortex preprocessor not available"}

    def preprocess_vwap(self, vwap: pd.Series, prices: pd.Series = None,
                       volumes: pd.Series = None, anchor: str = "D", **kwargs) -> Dict[str, Any]:
        """Route VWAP preprocessing to specialized VWAP preprocessor."""
        preprocessor = get_preprocessor('vwap')
        if preprocessor:
            return preprocessor.preprocess(vwap, prices, volumes, anchor=anchor, **kwargs)
        else:
            return {"error": "VWAP preprocessor not available"}

    # Bollinger Bands preprocessing - placeholder for future implementation
    def preprocess_bollinger_bands(self, upper: pd.Series, middle: pd.Series, lower: pd.Series,
                                  prices: pd.Series, **kwargs) -> Dict[str, Any]:
        """Route Bollinger Bands preprocessing to specialized preprocessor (future implementation)."""
        preprocessor = get_preprocessor('bbands')
        if preprocessor:
            return preprocessor.preprocess(upper, middle, lower, prices, **kwargs)
        else:
            # Simple fallback analysis for now
            current_price = float(prices.iloc[-1])
            current_upper = float(upper.iloc[-1])
            current_middle = float(middle.iloc[-1])
            current_lower = float(lower.iloc[-1])
            
            # Protect against divide-by-zero
            width = max(current_upper - current_lower, 1e-12)
            denom_mid = current_middle if abs(current_middle) > 1e-12 else 1e-12
            
            return {
                "indicator": "Bollinger_Bands",
                "current": {
                    "price": round(current_price, 4),
                    "upper": round(current_upper, 4),
                    "middle": round(current_middle, 4), 
                    "lower": round(current_lower, 4),
                    "bandwidth": round((current_upper - current_lower) / denom_mid * 100, 2),
                    "percent_b": round((current_price - current_lower) / width, 3)
                },
                "analysis": {
                    "position": self._get_bb_position(current_price, current_upper, current_middle, current_lower),
                    "squeeze": False  # Simplified
                },
                "summary": f"BB position: {self._get_bb_position(current_price, current_upper, current_middle, current_lower)}"
            }
    
    def preprocess_atr(self, atr: pd.Series, prices: pd.Series = None, 
                      length: int = 14, **kwargs) -> Dict[str, Any]:
        """Route ATR preprocessing to specialized preprocessor."""
        preprocessor = get_preprocessor('atr')
        if preprocessor:
            return preprocessor.preprocess(atr, prices, length=length, **kwargs)
        else:
            # Simple fallback analysis
            current_atr = float(atr.iloc[-1])
            return {
                "indicator": "ATR",
                "current": {
                    "value": round(current_atr, 6)
                },
                "analysis": {
                    "volatility": "normal"  # Simplified
                },
                "summary": f"ATR: {current_atr:.6f}"
            }
    
    def preprocess_adx(self, adx: pd.Series, plus_di: pd.Series, minus_di: pd.Series,
                      prices: pd.Series = None, length: int = 14, **kwargs) -> Dict[str, Any]:
        """Route ADX preprocessing to specialized preprocessor."""
        preprocessor = get_preprocessor('adx')
        if preprocessor:
            return preprocessor.preprocess(adx, plus_di, minus_di, prices, length=length, **kwargs)
        else:
            # Simple fallback analysis
            current_adx = float(adx.iloc[-1])
            current_plus_di = float(plus_di.iloc[-1])
            current_minus_di = float(minus_di.iloc[-1])
            
            return {
                "indicator": "ADX",
                "current": {
                    "adx": round(current_adx, 2),
                    "plus_di": round(current_plus_di, 2),
                    "minus_di": round(current_minus_di, 2)
                },
                "analysis": {
                    "trend_strength": "moderate" if current_adx > 25 else "weak",
                    "bias": "bullish" if current_plus_di > current_minus_di else "bearish"
                },
                "summary": f"ADX: {current_adx:.1f}, {'bullish' if current_plus_di > current_minus_di else 'bearish'} bias"
            }
    
    def preprocess_aroon(self, aroon_up: pd.Series, aroon_down: pd.Series,
                        prices: pd.Series = None, length: int = 14, **kwargs) -> Dict[str, Any]:
        """Route Aroon preprocessing to specialized preprocessor."""
        preprocessor = get_preprocessor('aroon')
        if preprocessor:
            return preprocessor.preprocess(aroon_up, aroon_down, prices, length=length, **kwargs)
        else:
            # Simple fallback analysis
            current_up = float(aroon_up.iloc[-1])
            current_down = float(aroon_down.iloc[-1])
            
            return {
                "indicator": "Aroon",
                "current": {
                    "aroon_up": round(current_up, 2),
                    "aroon_down": round(current_down, 2),
                    "oscillator": round(current_up - current_down, 2)
                },
                "analysis": {
                    "trend": "uptrend" if current_up > current_down else "downtrend",
                    "strength": "strong" if abs(current_up - current_down) > 50 else "weak"
                },
                "summary": f"Aroon Up: {current_up:.1f}, Down: {current_down:.1f}"
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