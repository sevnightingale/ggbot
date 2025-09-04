"""
MACD (Moving Average Convergence Divergence) Preprocessor.

Advanced MACD preprocessing with sophisticated analysis including crossover detection,
histogram analysis, zero line behavior, and divergence pattern recognition.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePreprocessor


class MACDPreprocessor(BasePreprocessor):
    """Advanced MACD preprocessor with professional-grade analysis."""
    
    def preprocess(self, macd_line: pd.Series, signal_line: pd.Series, 
                  histogram: pd.Series, prices: pd.Series = None, **kwargs) -> Dict[str, Any]:
        """
        Advanced MACD preprocessing with sophisticated analysis.
        
        Args:
            macd_line: MACD line values
            signal_line: Signal line values
            histogram: MACD histogram values
            prices: Price series for divergence analysis (optional)
            
        Returns:
            Dictionary with comprehensive MACD analysis
        """
        if len(macd_line) < 5:
            return {"error": "Insufficient data for MACD analysis"}
        
        current_macd = float(macd_line.iloc[-1])
        current_signal = float(signal_line.iloc[-1])
        current_histogram = float(histogram.iloc[-1])
        
        # Crossover analysis
        crossover_analysis = self._analyze_macd_crossovers(macd_line, signal_line)
        
        # Histogram analysis
        histogram_analysis = self._analyze_histogram(histogram)
        
        # Divergence analysis
        divergence = None
        if prices is not None:
            divergence = self._detect_macd_price_divergence(macd_line, prices)
        
        # Trend strength
        trend_strength = self._analyze_macd_trend_strength(macd_line, signal_line, histogram)
        
        # Zero line analysis
        zero_line_analysis = self._analyze_zero_line_behavior(macd_line)
        
        return {
            "indicator": "MACD",
            "current": {
                "macd": round(current_macd, 4),
                "signal": round(current_signal, 4),
                "histogram": round(current_histogram, 4),
                "timestamp": datetime.now().isoformat()
            },
            "trend": {
                "direction": "bullish" if current_macd > current_signal else "bearish",
                "strength": trend_strength["strength"],
                "momentum": histogram_analysis["momentum_direction"],
                "acceleration": histogram_analysis["acceleration"]
            },
            "crossovers": crossover_analysis,
            "histogram": histogram_analysis,
            "zero_line": zero_line_analysis,
            "divergence": divergence,
            "signals": self._generate_macd_signals(current_macd, current_signal, current_histogram, crossover_analysis),
            "confidence": trend_strength["confidence"],
            "summary": self._generate_macd_summary(
                current_macd, current_signal, current_histogram, 
                crossover_analysis, trend_strength
            )
        }
    
    def _analyze_macd_crossovers(self, macd_line: pd.Series, signal_line: pd.Series) -> Dict[str, Any]:
        """Analyze MACD crossovers."""
        crossovers = []
        
        for i in range(1, min(20, len(macd_line))):
            prev_macd = macd_line.iloc[-(i+1)]
            curr_macd = macd_line.iloc[-i]
            prev_signal = signal_line.iloc[-(i+1)]
            curr_signal = signal_line.iloc[-i]
            
            # Bullish crossover
            if prev_macd <= prev_signal and curr_macd > curr_signal:
                crossovers.append({
                    "type": "bullish_crossover",
                    "periods_ago": i,
                    "strength": abs(curr_macd - curr_signal)
                })
            # Bearish crossover  
            elif prev_macd >= prev_signal and curr_macd < curr_signal:
                crossovers.append({
                    "type": "bearish_crossover",
                    "periods_ago": i,
                    "strength": abs(curr_macd - curr_signal)
                })
        
        return {
            "recent_crossovers": crossovers[:3],
            "latest_crossover": crossovers[0] if crossovers else None
        }
    
    def _analyze_histogram(self, histogram: pd.Series) -> Dict[str, Any]:
        """Analyze MACD histogram for momentum insights."""
        if len(histogram) < 3:
            return {}
        
        current = histogram.iloc[-1]
        previous = histogram.iloc[-2]
        
        momentum_direction = "increasing" if current > previous else "decreasing"
        acceleration = current - previous
        
        # Histogram zero crossings
        zero_crossings = 0
        for i in range(1, min(10, len(histogram))):
            if (histogram.iloc[-i] > 0 and histogram.iloc[-(i+1)] <= 0) or \
               (histogram.iloc[-i] < 0 and histogram.iloc[-(i+1)] >= 0):
                zero_crossings += 1
        
        return {
            "momentum_direction": momentum_direction,
            "acceleration": round(acceleration, 4),
            "zero_crossings_recent": zero_crossings,
            "histogram_strength": abs(current)
        }
    
    def _analyze_zero_line_behavior(self, macd_line: pd.Series) -> Dict[str, Any]:
        """Analyze MACD behavior around zero line."""
        current = macd_line.iloc[-1]
        
        # Time above/below zero
        above_zero = sum(1 for v in macd_line if v > 0)
        below_zero = sum(1 for v in macd_line if v < 0)
        total = len(macd_line)
        
        return {
            "current_position": "above" if current > 0 else "below",
            "distance_from_zero": round(abs(current), 4),
            "time_above_zero_pct": round((above_zero / total) * 100, 1),
            "time_below_zero_pct": round((below_zero / total) * 100, 1)
        }
    
    def _analyze_macd_trend_strength(self, macd: pd.Series, signal: pd.Series, histogram: pd.Series) -> Dict[str, Any]:
        """Analyze MACD trend strength."""
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        current_histogram = histogram.iloc[-1]
        
        # Basic strength calculation
        strength = 0.5  # Default moderate strength
        
        # Enhance strength based on histogram
        if abs(current_histogram) > np.std(histogram.dropna()):
            strength = 0.7
        
        # Confidence based on signal clarity
        confidence = min(1.0, abs(current_macd - current_signal) / (np.std(macd.dropna()) + 0.001))
        confidence = max(0.3, min(0.8, confidence))
        
        return {
            "strength": strength,
            "confidence": confidence
        }
    
    def _detect_macd_price_divergence(self, macd: pd.Series, prices: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect MACD-price divergence."""
        if len(macd) < 15 or len(prices) < 15:
            return None
        
        # Look for divergence patterns
        recent_periods = 10
        macd_recent = macd.iloc[-recent_periods:]
        price_recent = prices.iloc[-recent_periods:]
        
        # Find peaks and troughs
        macd_peaks = self._find_peaks(macd_recent, prominence=5)
        macd_troughs = self._find_troughs(macd_recent, prominence=5)
        price_peaks = self._find_peaks(price_recent)
        price_troughs = self._find_troughs(price_recent)
        
        # Bearish divergence: price higher highs, MACD lower highs
        if len(macd_peaks) >= 2 and len(price_peaks) >= 2:
            latest_macd_peak = macd_peaks[-1]
            prev_macd_peak = macd_peaks[-2]
            latest_price_peak = price_peaks[-1]
            prev_price_peak = price_peaks[-2]
            
            if (latest_price_peak["value"] > prev_price_peak["value"] and
                latest_macd_peak["value"] < prev_macd_peak["value"]):
                return {
                    "type": "bearish_divergence",
                    "confidence": 0.7,
                    "description": "Price making higher highs while MACD making lower highs"
                }
        
        # Bullish divergence: price lower lows, MACD higher lows
        if len(macd_troughs) >= 2 and len(price_troughs) >= 2:
            latest_macd_trough = macd_troughs[-1]
            prev_macd_trough = macd_troughs[-2]
            latest_price_trough = price_troughs[-1]
            prev_price_trough = price_troughs[-2]
            
            if (latest_price_trough["value"] < prev_price_trough["value"] and
                latest_macd_trough["value"] > prev_macd_trough["value"]):
                return {
                    "type": "bullish_divergence",
                    "confidence": 0.7,
                    "description": "Price making lower lows while MACD making higher lows"
                }
        
        return None
    
    def _generate_macd_signals(self, macd: float, signal: float, histogram: float, 
                              crossovers: Dict) -> List[Dict[str, Any]]:
        """Generate MACD signals."""
        signals = []
        
        # Crossover signals
        if crossovers["latest_crossover"]:
            crossover = crossovers["latest_crossover"]
            if crossover["periods_ago"] <= 2:  # Recent crossover
                signals.append({
                    "type": f"{crossover['type']}_signal",
                    "strength": "high" if crossover["strength"] > 100 else "medium",
                    "reason": f"Recent MACD {crossover['type']} {crossover['periods_ago']} periods ago",
                    "confidence": min(1.0, crossover["strength"] / 200)
                })
        
        # Histogram momentum signals
        if histogram > 0 and macd > signal:
            signals.append({
                "type": "momentum_continuation",
                "strength": "medium",
                "reason": "MACD above signal with positive histogram momentum",
                "confidence": 0.6
            })
        
        return signals
    
    def _generate_macd_summary(self, macd: float, signal: float, histogram: float,
                              crossovers: Dict, trend_strength: Dict) -> str:
        """Generate MACD summary."""
        trend = "bullish" if macd > signal else "bearish"
        momentum = "increasing" if histogram > 0 else "decreasing"
        
        summary = f"MACD {trend} trend with {momentum} momentum"
        
        if crossovers["latest_crossover"] and crossovers["latest_crossover"]["periods_ago"] <= 5:
            crossover = crossovers["latest_crossover"]
            summary += f". Recent {crossover['type']} {crossover['periods_ago']}p ago"
        
        return summary