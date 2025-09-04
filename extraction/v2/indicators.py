"""
Pure Python Technical Indicators using pandas-ta.

This module provides clean, validated technical indicator calculations
with simple preprocessing for analytical context.
"""

import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from core.common.logger import logger
from .preprocessor import TechnicalAnalysisPreprocessor


class TechnicalIndicators:
    """
    Clean technical indicator calculator using pandas-ta.
    
    Provides accurate, validated technical indicator calculations with
    simple analytical context (no complex preprocessing).
    """
    
    def __init__(self, use_advanced_preprocessing: bool = True):
        """Initialize technical indicators calculator."""
        self._log = logger.bind(component="technical_indicators")
        self.use_advanced_preprocessing = use_advanced_preprocessing
        
        if use_advanced_preprocessing:
            self.preprocessor = TechnicalAnalysisPreprocessor()
            self._log.info("Initialized with advanced preprocessing enabled")
        
        # Available indicators with their default parameters
        self.available_indicators = {
            "rsi": {"length": 14},
            "macd": {"fast": 12, "slow": 26, "signal": 9},
            "sma": {"length": 20},
            "ema": {"length": 20},
            "bollinger_bands": {"length": 20, "std": 2.0},
            "stochastic": {"k": 14, "d": 3},
            "williams_r": {"length": 14},
            "atr": {"length": 14},
            "roc": {"length": 10},
            "adx": {"length": 14},
            "cci": {"length": 20},
            "mfi": {"length": 14},
            "obv": {},  # No parameters
            "vwap": {"anchor": "D"}
        }
    
    def calculate_rsi(self, df: pd.DataFrame, length: int = 14) -> Dict[str, Any]:
        """
        Calculate RSI with simple analytical context.
        
        Args:
            df: DataFrame with OHLCV data
            length: RSI period (default: 14)
            
        Returns:
            Dictionary with RSI values and analysis
        """
        if len(df) < length + 1:
            raise ValueError(f"Need at least {length + 1} periods for RSI calculation, got {len(df)}")
        
        # Calculate RSI using pandas-ta
        rsi_series = ta.rsi(df['close'], length=length)
        
        if rsi_series is None or rsi_series.empty:
            raise ValueError("RSI calculation failed")
        
        current = float(rsi_series.iloc[-1])
        
        if self.use_advanced_preprocessing and hasattr(self, 'preprocessor'):
            # Use sophisticated preprocessing
            prices = df['close'] if 'close' in df.columns else None
            return self.preprocessor.preprocess_rsi(rsi_series, prices, length)
        else:
            # Simple analytical context (fallback)
            analysis = self._analyze_oscillator(rsi_series, 70, 30, "RSI")
            
            return {
                "indicator": "RSI",
                "period": length,
                "current": round(current, 2),
                "analysis": analysis,
                "values": rsi_series.dropna().tolist(),
                "timestamp": df['timestamp'].iloc[-1] if 'timestamp' in df.columns else datetime.now()
            }
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, Any]:
        """
        Calculate MACD with simple analytical context.
        
        Args:
            df: DataFrame with OHLCV data
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line period (default: 9)
            
        Returns:
            Dictionary with MACD values and analysis
        """
        min_periods = slow + signal
        if len(df) < min_periods:
            raise ValueError(f"Need at least {min_periods} periods for MACD calculation, got {len(df)}")
        
        # Calculate MACD using pandas-ta
        macd_result = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
        
        if macd_result is None or macd_result.empty:
            raise ValueError("MACD calculation failed")
        
        macd_line = macd_result[f'MACD_{fast}_{slow}_{signal}']
        macd_signal = macd_result[f'MACDs_{fast}_{slow}_{signal}']
        macd_histogram = macd_result[f'MACDh_{fast}_{slow}_{signal}']
        
        current_macd = float(macd_line.iloc[-1])
        current_signal = float(macd_signal.iloc[-1])
        current_histogram = float(macd_histogram.iloc[-1])
        
        # Simple MACD analysis
        bullish = current_macd > current_signal
        momentum = "increasing" if current_histogram > 0 else "decreasing"
        
        if self.use_advanced_preprocessing and hasattr(self, 'preprocessor'):
            # Use sophisticated preprocessing
            prices = df['close'] if 'close' in df.columns else None
            return self.preprocessor.preprocess_macd(macd_line, macd_signal, macd_histogram, prices)
        else:
            # Simple analysis (fallback)
            # Check for crossovers in last few periods
            recent_cross = None
            if len(macd_line) >= 2:
                prev_diff = macd_line.iloc[-2] - macd_signal.iloc[-2]
                curr_diff = current_macd - current_signal
                
                if prev_diff <= 0 < curr_diff:
                    recent_cross = "bullish_crossover"
                elif prev_diff >= 0 > curr_diff:
                    recent_cross = "bearish_crossover"
            
            return {
                "indicator": "MACD",
                "parameters": {"fast": fast, "slow": slow, "signal": signal},
                "current": {
                    "macd": round(current_macd, 4),
                    "signal": round(current_signal, 4),
                    "histogram": round(current_histogram, 4)
                },
                "analysis": {
                    "trend": "bullish" if bullish else "bearish",
                    "momentum": momentum,
                    "crossover": recent_cross,
                    "strength": abs(current_histogram)
                },
                "values": {
                    "macd": macd_line.dropna().tolist(),
                    "signal": macd_signal.dropna().tolist(),
                    "histogram": macd_histogram.dropna().tolist()
                },
                "timestamp": df['timestamp'].iloc[-1] if 'timestamp' in df.columns else datetime.now()
            }
    
    def calculate_sma(self, df: pd.DataFrame, length: int = 20) -> Dict[str, Any]:
        """Calculate Simple Moving Average."""
        if len(df) < length:
            raise ValueError(f"Need at least {length} periods for SMA calculation, got {len(df)}")
        
        sma_series = ta.sma(df['close'], length=length)
        
        if sma_series is None or sma_series.empty:
            raise ValueError("SMA calculation failed")
        
        current = float(sma_series.iloc[-1])
        current_price = float(df['close'].iloc[-1])
        
        # Simple analysis
        price_vs_sma = (current_price - current) / current * 100
        
        return {
            "indicator": "SMA",
            "period": length,
            "current": round(current, 4),
            "analysis": {
                "price_vs_sma": round(price_vs_sma, 2),
                "price_position": "above" if current_price > current else "below",
                "trend": self._determine_ma_trend(sma_series)
            },
            "values": sma_series.dropna().tolist(),
            "timestamp": df['timestamp'].iloc[-1] if 'timestamp' in df.columns else datetime.now()
        }
    
    def calculate_ema(self, df: pd.DataFrame, length: int = 20) -> Dict[str, Any]:
        """Calculate Exponential Moving Average."""
        if len(df) < length:
            raise ValueError(f"Need at least {length} periods for EMA calculation, got {len(df)}")
        
        ema_series = ta.ema(df['close'], length=length)
        
        if ema_series is None or ema_series.empty:
            raise ValueError("EMA calculation failed")
        
        current = float(ema_series.iloc[-1])
        current_price = float(df['close'].iloc[-1])
        
        # Simple analysis
        price_vs_ema = (current_price - current) / current * 100
        
        return {
            "indicator": "EMA",
            "period": length,
            "current": round(current, 4),
            "analysis": {
                "price_vs_ema": round(price_vs_ema, 2),
                "price_position": "above" if current_price > current else "below",
                "trend": self._determine_ma_trend(ema_series)
            },
            "values": ema_series.dropna().tolist(),
            "timestamp": df['timestamp'].iloc[-1] if 'timestamp' in df.columns else datetime.now()
        }
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, length: int = 20, std: float = 2.0) -> Dict[str, Any]:
        """Calculate Bollinger Bands."""
        if len(df) < length:
            raise ValueError(f"Need at least {length} periods for Bollinger Bands calculation, got {len(df)}")
        
        bb_result = ta.bbands(df['close'], length=length, std=std)
        
        if bb_result is None or bb_result.empty:
            raise ValueError("Bollinger Bands calculation failed")
        
        lower = bb_result[f'BBL_{length}_{std}']
        middle = bb_result[f'BBM_{length}_{std}']
        upper = bb_result[f'BBU_{length}_{std}']
        bandwidth = bb_result[f'BBB_{length}_{std}']
        percent_b = bb_result[f'BBP_{length}_{std}']
        
        current_price = float(df['close'].iloc[-1])
        current_lower = float(lower.iloc[-1])
        current_middle = float(middle.iloc[-1])
        current_upper = float(upper.iloc[-1])
        current_bandwidth = float(bandwidth.iloc[-1])
        current_percent_b = float(percent_b.iloc[-1])
        
        # Simple BB analysis
        position = "middle"
        if current_price > current_upper:
            position = "above_upper"
        elif current_price < current_lower:
            position = "below_lower"
        elif current_price > current_middle:
            position = "upper_half"
        else:
            position = "lower_half"
        
        squeeze = current_bandwidth < np.percentile(bandwidth.dropna(), 20)
        
        return {
            "indicator": "Bollinger_Bands",
            "parameters": {"length": length, "std": std},
            "current": {
                "lower": round(current_lower, 4),
                "middle": round(current_middle, 4),
                "upper": round(current_upper, 4),
                "bandwidth": round(current_bandwidth, 4),
                "percent_b": round(current_percent_b, 4)
            },
            "analysis": {
                "position": position,
                "squeeze": squeeze,
                "width": "narrow" if squeeze else "normal"
            },
            "values": {
                "lower": lower.dropna().tolist(),
                "middle": middle.dropna().tolist(),
                "upper": upper.dropna().tolist(),
                "bandwidth": bandwidth.dropna().tolist(),
                "percent_b": percent_b.dropna().tolist()
            },
            "timestamp": df['timestamp'].iloc[-1] if 'timestamp' in df.columns else datetime.now()
        }
    
    def calculate_stochastic(self, df: pd.DataFrame, k: int = 14, d: int = 3) -> Dict[str, Any]:
        """
        Calculate Stochastic Oscillator with advanced preprocessing.
        
        Args:
            df: DataFrame with OHLCV data
            k: %K period (default: 14)
            d: %D smoothing period (default: 3)
            
        Returns:
            Dictionary with Stochastic values and analysis
        """
        min_periods = k + d
        if len(df) < min_periods:
            raise ValueError(f"Need at least {min_periods} periods for Stochastic calculation, got {len(df)}")
        
        # Calculate Stochastic using pandas-ta
        stoch_result = ta.stoch(df['high'], df['low'], df['close'], k=k, d=d)
        
        if stoch_result is None or stoch_result.empty:
            raise ValueError("Stochastic calculation failed")
        
        k_percent = stoch_result[f'STOCHk_{k}_{d}_3']  # %K line
        d_percent = stoch_result[f'STOCHd_{k}_{d}_3']  # %D line (signal)
        
        if k_percent is None or d_percent is None:
            raise ValueError("Stochastic calculation returned None values")
        
        current_k = float(k_percent.iloc[-1])
        current_d = float(d_percent.iloc[-1])
        
        if self.use_advanced_preprocessing and hasattr(self, 'preprocessor'):
            # Use sophisticated preprocessing
            prices = df['close'] if 'close' in df.columns else None
            return self.preprocessor.preprocess_stochastic(k_percent, d_percent, prices, k=k, d=d)
        else:
            # Simple analysis (fallback)
            spread = current_k - current_d
            
            # Zone analysis
            zone = "neutral"
            if current_k >= 80:
                zone = "overbought"
            elif current_k <= 20:
                zone = "oversold"
            
            # Crossover analysis
            crossover = None
            if len(k_percent) >= 2 and len(d_percent) >= 2:
                prev_k = k_percent.iloc[-2]
                prev_d = d_percent.iloc[-2]
                
                if prev_k <= prev_d and current_k > current_d:
                    crossover = "bullish_crossover"
                elif prev_k >= prev_d and current_k < current_d:
                    crossover = "bearish_crossover"
            
            # Momentum
            k_trend = "rising" if len(k_percent) >= 3 and current_k > k_percent.iloc[-3] else "falling"
            
            return {
                "indicator": "Stochastic",
                "parameters": {"k": k, "d": d},
                "current": {
                    "k_percent": round(current_k, 2),
                    "d_percent": round(current_d, 2),
                    "spread": round(spread, 2)
                },
                "analysis": {
                    "zone": zone,
                    "crossover": crossover,
                    "k_trend": k_trend,
                    "strength": abs(spread)
                },
                "values": {
                    "k_percent": k_percent.dropna().tolist(),
                    "d_percent": d_percent.dropna().tolist()
                },
                "timestamp": df['timestamp'].iloc[-1] if 'timestamp' in df.columns else datetime.now()
            }
    
    def calculate_williams_r(self, df: pd.DataFrame, length: int = 14) -> Dict[str, Any]:
        """
        Calculate Williams %R with advanced preprocessing.
        
        Args:
            df: DataFrame with OHLCV data
            length: Williams %R period (default: 14)
            
        Returns:
            Dictionary with Williams %R values and analysis
        """
        if len(df) < length:
            raise ValueError(f"Need at least {length} periods for Williams %R calculation, got {len(df)}")
        
        # Calculate Williams %R using pandas-ta
        williams_r_series = ta.willr(df['high'], df['low'], df['close'], length=length)
        
        if williams_r_series is None or williams_r_series.empty:
            raise ValueError("Williams %R calculation failed")
        
        current_wr = float(williams_r_series.iloc[-1])
        
        if self.use_advanced_preprocessing and hasattr(self, 'preprocessor'):
            # Use sophisticated preprocessing
            prices = df['close'] if 'close' in df.columns else None
            return self.preprocessor.preprocess_williams_r(williams_r_series, prices, length)
        else:
            # Simple analysis (fallback)
            # Zone analysis
            zone = "neutral"
            if current_wr >= -20:  # Overbought (closer to 0)
                zone = "overbought"
            elif current_wr <= -80:  # Oversold (closer to -100)
                zone = "oversold"
            
            # Momentum state
            momentum_state = "bullish" if current_wr > -50 else "bearish"
            
            # Simple trend over last 5 periods
            trend = "sideways"
            if len(williams_r_series) >= 5:
                recent = williams_r_series.iloc[-5:].tolist()
                if recent[-1] > recent[0] + 5:  # Threshold for Williams %R movement
                    trend = "rising"
                elif recent[-1] < recent[0] - 5:
                    trend = "falling"
            
            return {
                "indicator": "Williams_R",
                "period": length,
                "current": {
                    "value": round(current_wr, 2)
                },
                "analysis": {
                    "zone": zone,
                    "momentum_state": momentum_state,
                    "trend": trend
                },
                "values": williams_r_series.dropna().tolist(),
                "timestamp": df['timestamp'].iloc[-1] if 'timestamp' in df.columns else datetime.now()
            }
    
    def calculate_multiple(self, df: pd.DataFrame, indicators: List[str], **params) -> Dict[str, Any]:
        """
        Calculate multiple indicators efficiently.
        
        Args:
            df: DataFrame with OHLCV data
            indicators: List of indicator names to calculate
            **params: Custom parameters for indicators
            
        Returns:
            Dictionary with results for each indicator
        """
        results = {}
        
        for indicator in indicators:
            try:
                if indicator.lower() == "rsi":
                    length = params.get("rsi_length", 14)
                    results["rsi"] = self.calculate_rsi(df, length)
                
                elif indicator.lower() == "macd":
                    fast = params.get("macd_fast", 12)
                    slow = params.get("macd_slow", 26)
                    signal = params.get("macd_signal", 9)
                    results["macd"] = self.calculate_macd(df, fast, slow, signal)
                
                elif indicator.lower() == "sma":
                    length = params.get("sma_length", 20)
                    results["sma"] = self.calculate_sma(df, length)
                
                elif indicator.lower() == "ema":
                    length = params.get("ema_length", 20)
                    results["ema"] = self.calculate_ema(df, length)
                
                elif indicator.lower() == "bollinger_bands":
                    length = params.get("bb_length", 20)
                    std = params.get("bb_std", 2.0)
                    results["bollinger_bands"] = self.calculate_bollinger_bands(df, length, std)
                
                elif indicator.lower() == "stochastic":
                    k = params.get("stoch_k", 14)
                    d = params.get("stoch_d", 3)
                    results["stochastic"] = self.calculate_stochastic(df, k, d)
                
                elif indicator.lower() == "williams_r":
                    length = params.get("williams_r_length", 14)
                    results["williams_r"] = self.calculate_williams_r(df, length)
                
                else:
                    self._log.warning(f"Indicator '{indicator}' not implemented yet")
                    
            except Exception as e:
                self._log.error(f"Error calculating {indicator}: {str(e)}")
                results[indicator] = {"error": str(e)}
        
        return results
    
    def _analyze_oscillator(self, series: pd.Series, overbought: float, oversold: float, name: str) -> Dict[str, Any]:
        """Simple oscillator analysis."""
        current = float(series.iloc[-1])
        
        # Determine zone
        zone = "neutral"
        if current >= overbought:
            zone = "overbought"
        elif current <= oversold:
            zone = "oversold"
        
        # Simple trend over last 5 periods
        if len(series) >= 5:
            recent = series.iloc[-5:].tolist()
            if recent[-1] > recent[0]:
                trend = "rising"
            elif recent[-1] < recent[0]:
                trend = "falling"
            else:
                trend = "sideways"
        else:
            trend = "unknown"
        
        return {
            "zone": zone,
            "trend": trend,
            "overbought_threshold": overbought,
            "oversold_threshold": oversold
        }
    
    def _determine_ma_trend(self, series: pd.Series, periods: int = 5) -> str:
        """Determine moving average trend direction."""
        if len(series) < periods:
            return "unknown"
        
        recent = series.iloc[-periods:].tolist()
        
        # Simple slope calculation
        if recent[-1] > recent[0] * 1.001:  # 0.1% threshold
            return "rising"
        elif recent[-1] < recent[0] * 0.999:  # 0.1% threshold
            return "falling"
        else:
            return "sideways"
    
    def get_available_indicators(self) -> List[str]:
        """Get list of available indicators."""
        return list(self.available_indicators.keys())
    
    def get_indicator_info(self, indicator: str) -> Dict[str, Any]:
        """Get information about a specific indicator."""
        if indicator.lower() not in self.available_indicators:
            return {"error": f"Indicator '{indicator}' not available"}
        
        return {
            "name": indicator.upper(),
            "default_parameters": self.available_indicators[indicator.lower()],
            "description": f"{indicator.upper()} technical indicator"
        }