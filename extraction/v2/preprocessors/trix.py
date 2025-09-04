"""
TRIX Preprocessor.

Advanced TRIX preprocessing with triple exponential smoothing analysis,
momentum turning points detection, and signal line crossover analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePreprocessor


class TRIXPreprocessor(BasePreprocessor):
    """Advanced TRIX preprocessor with professional-grade momentum analysis."""
    
    def preprocess(self, trix: pd.Series, trix_signal: pd.Series = None, 
                  prices: pd.Series = None, length: int = 14, **kwargs) -> Dict[str, Any]:
        """
        Advanced TRIX preprocessing with comprehensive momentum analysis.
        
        TRIX is a momentum oscillator that uses triple exponential smoothing
        to filter out short-term price movements and identify longer-term trends.
        
        Args:
            trix: TRIX line values (percentage rate of change of triple EMA)
            trix_signal: TRIX signal line (optional, EMA of TRIX)
            prices: Price series for divergence analysis (optional)
            length: TRIX calculation period
            
        Returns:
            Dictionary with comprehensive TRIX analysis
        """
        if len(trix) < 5:
            return {"error": "Insufficient data for TRIX analysis"}
        
        current_trix = float(trix.iloc[-1])
        current_signal = float(trix_signal.iloc[-1]) if trix_signal is not None else None
        
        # Momentum analysis
        momentum_analysis = self._analyze_trix_momentum(trix)
        
        # Zero line analysis
        zero_line_analysis = self._analyze_trix_zero_line(trix)
        
        # Signal line analysis
        signal_line_analysis = {}
        if trix_signal is not None:
            signal_line_analysis = self._analyze_trix_signal_crossovers(trix, trix_signal)
        
        # Turning points analysis
        turning_points = self._analyze_trix_turning_points(trix)
        
        # Smoothness analysis (TRIX should be smooth due to triple smoothing)
        smoothness_analysis = self._analyze_trix_smoothness(trix)
        
        # Trend strength analysis
        trend_analysis = self._analyze_trix_trend_strength(trix)
        
        # Divergence analysis
        divergence = None
        if prices is not None:
            divergence = self._detect_trix_price_divergence(trix, prices)
        
        # Histogram analysis (if signal line available)
        histogram_analysis = {}
        if trix_signal is not None:
            histogram_analysis = self._analyze_trix_histogram(trix, trix_signal)
        
        # Signal generation
        signals = self._generate_trix_signals(current_trix, current_signal, momentum_analysis, 
                                            zero_line_analysis, signal_line_analysis)
        
        # Confidence calculation
        confidence = self._calculate_trix_confidence(trix, momentum_analysis, smoothness_analysis)
        
        return {
            "indicator": "TRIX",
            "current": {
                "trix": round(current_trix, 6),
                "signal": round(current_signal, 6) if current_signal is not None else None,
                "histogram": round(current_trix - current_signal, 6) if current_signal is not None else None,
                "timestamp": datetime.now().isoformat()
            },
            "momentum": momentum_analysis,
            "zero_line": zero_line_analysis,
            "signal_line": signal_line_analysis,
            "turning_points": turning_points,
            "smoothness": smoothness_analysis,
            "trend": trend_analysis,
            "divergence": divergence,
            "histogram": histogram_analysis,
            "signals": signals,
            "confidence": confidence,
            "summary": self._generate_trix_summary(current_trix, current_signal, momentum_analysis, zero_line_analysis)
        }
    
    def _analyze_trix_momentum(self, trix: pd.Series) -> Dict[str, Any]:
        """Analyze TRIX momentum characteristics."""
        current_trix = trix.iloc[-1]
        
        # Momentum direction
        if current_trix > 0:
            momentum_direction = "bullish"
        elif current_trix < 0:
            momentum_direction = "bearish"
        else:
            momentum_direction = "neutral"
        
        # Momentum strength (TRIX values are typically small due to triple smoothing)
        momentum_strength = abs(current_trix)
        
        # Momentum strength classification
        trix_std = trix.std()
        if momentum_strength > trix_std * 2:
            strength_level = "very_strong"
        elif momentum_strength > trix_std:
            strength_level = "strong"
        elif momentum_strength > trix_std * 0.5:
            strength_level = "moderate"
        else:
            strength_level = "weak"
        
        # Momentum acceleration
        trix_velocity = self._calculate_velocity(trix, 3)
        trix_acceleration = self._calculate_acceleration(trix, 5)
        
        # Momentum persistence
        persistence = self._calculate_trix_momentum_persistence(trix)
        
        return {
            "direction": momentum_direction,
            "strength": round(momentum_strength, 6),
            "strength_level": strength_level,
            "velocity": round(trix_velocity, 6),
            "acceleration": round(trix_acceleration, 6),
            "persistence": round(persistence, 3)
        }
    
    def _calculate_trix_momentum_persistence(self, trix: pd.Series) -> float:
        """Calculate persistence of TRIX momentum direction."""
        if len(trix) < 5:
            return 0.5
        
        recent_trix = trix.iloc[-5:]
        current_direction = "positive" if trix.iloc[-1] > 0 else "negative"
        
        same_direction = sum(1 for val in recent_trix if 
                           (val > 0 and current_direction == "positive") or 
                           (val < 0 and current_direction == "negative"))
        
        return same_direction / len(recent_trix)
    
    def _analyze_trix_zero_line(self, trix: pd.Series) -> Dict[str, Any]:
        """Analyze TRIX behavior around zero line."""
        current_trix = trix.iloc[-1]
        
        # Position relative to zero
        if current_trix > 0:
            position = "above_zero"
        elif current_trix < 0:
            position = "below_zero"
        else:
            position = "at_zero"
        
        # Time above/below zero
        above_zero = sum(1 for val in trix if val > 0)
        below_zero = sum(1 for val in trix if val < 0)
        total = len(trix)
        
        # Zero line crossings
        crossings = []
        for i in range(1, min(15, len(trix))):
            prev_trix = trix.iloc[-(i+1)]
            curr_trix = trix.iloc[-i]
            
            # Bullish zero crossing
            if prev_trix <= 0 and curr_trix > 0:
                crossings.append({
                    "type": "bullish_zero_cross",
                    "periods_ago": i,
                    "value": round(curr_trix, 6)
                })
            # Bearish zero crossing
            elif prev_trix >= 0 and curr_trix < 0:
                crossings.append({
                    "type": "bearish_zero_cross",
                    "periods_ago": i,
                    "value": round(curr_trix, 6)
                })
        
        return {
            "position": position,
            "above_zero_pct": round((above_zero / total) * 100, 1),
            "below_zero_pct": round((below_zero / total) * 100, 1),
            "recent_crossings": crossings[:5],
            "latest_crossing": crossings[0] if crossings else None
        }
    
    def _analyze_trix_signal_crossovers(self, trix: pd.Series, trix_signal: pd.Series) -> Dict[str, Any]:
        """Analyze TRIX signal line crossovers."""
        crossovers = []
        
        for i in range(1, min(15, len(trix))):
            prev_trix = trix.iloc[-(i+1)]
            curr_trix = trix.iloc[-i]
            prev_signal = trix_signal.iloc[-(i+1)]
            curr_signal = trix_signal.iloc[-i]
            
            # Bullish crossover (TRIX crosses above signal)
            if prev_trix <= prev_signal and curr_trix > curr_signal:
                crossovers.append({
                    "type": "bullish_crossover",
                    "periods_ago": i,
                    "trix_value": round(curr_trix, 6),
                    "signal_value": round(curr_signal, 6),
                    "strength": abs(curr_trix - curr_signal)
                })
            # Bearish crossover (TRIX crosses below signal)
            elif prev_trix >= prev_signal and curr_trix < curr_signal:
                crossovers.append({
                    "type": "bearish_crossover",
                    "periods_ago": i,
                    "trix_value": round(curr_trix, 6),
                    "signal_value": round(curr_signal, 6),
                    "strength": abs(curr_trix - curr_signal)
                })
        
        return {
            "recent_crossovers": crossovers[:5],
            "latest_crossover": crossovers[0] if crossovers else None,
            "crossover_frequency": len(crossovers) / min(15, len(trix)) if len(trix) > 0 else 0
        }
    
    def _analyze_trix_turning_points(self, trix: pd.Series) -> Dict[str, Any]:
        """Analyze TRIX turning points (peaks and troughs)."""
        if len(trix) < 10:
            return {}
        
        # Find peaks and troughs with appropriate prominence for TRIX
        trix_std = trix.std()
        prominence = max(trix_std * 0.1, 0.000001)  # Very small prominence for TRIX
        
        peaks = self._find_peaks(trix, prominence=prominence)
        troughs = self._find_troughs(trix, prominence=prominence)
        
        # Recent turning points
        recent_peaks = [p for p in peaks if len(trix) - 1 - p["index"] <= 10]
        recent_troughs = [t for t in troughs if len(trix) - 1 - t["index"] <= 10]
        
        # Latest turning point
        latest_peak = peaks[-1] if peaks else None
        latest_trough = troughs[-1] if troughs else None
        
        if latest_peak and latest_trough:
            if latest_peak["index"] > latest_trough["index"]:
                latest_turning_point = {
                    "type": "peak",
                    "value": round(latest_peak["value"], 6),
                    "periods_ago": len(trix) - 1 - latest_peak["index"]
                }
            else:
                latest_turning_point = {
                    "type": "trough", 
                    "value": round(latest_trough["value"], 6),
                    "periods_ago": len(trix) - 1 - latest_trough["index"]
                }
        else:
            latest_turning_point = None
        
        return {
            "total_peaks": len(peaks),
            "total_troughs": len(troughs),
            "recent_peaks": recent_peaks,
            "recent_troughs": recent_troughs,
            "latest_turning_point": latest_turning_point
        }
    
    def _analyze_trix_smoothness(self, trix: pd.Series) -> Dict[str, Any]:
        """Analyze TRIX smoothness characteristics."""
        if len(trix) < 5:
            return {}
        
        # TRIX should be very smooth due to triple exponential smoothing
        trix_changes = trix.diff().dropna()
        
        # Smoothness metrics
        avg_change = trix_changes.abs().mean()
        max_change = trix_changes.abs().max()
        volatility = trix.std()
        mean_trix = abs(trix.mean())
        
        # Relative smoothness
        relative_volatility = volatility / mean_trix if mean_trix > 0 else 0
        
        # Direction changes (should be infrequent for smooth indicator)
        direction_changes = 0
        prev_direction = None
        
        for change in trix_changes:
            current_direction = "up" if change > 0 else "down" if change < 0 else "flat"
            if prev_direction and current_direction != prev_direction and current_direction != "flat":
                direction_changes += 1
            prev_direction = current_direction
        
        change_frequency = direction_changes / len(trix_changes) if len(trix_changes) > 0 else 0
        
        # Smoothness score (lower is smoother)
        smoothness_score = 1 - min(1.0, change_frequency + relative_volatility)
        
        return {
            "avg_change": round(avg_change, 8),
            "max_change": round(max_change, 8),
            "relative_volatility": round(relative_volatility, 6),
            "direction_changes": direction_changes,
            "change_frequency": round(change_frequency, 3),
            "smoothness_score": round(smoothness_score, 3),
            "smoothness_rating": self._rate_smoothness(smoothness_score)
        }
    
    def _rate_smoothness(self, score: float) -> str:
        """Rate TRIX smoothness level."""
        if score > 0.8:
            return "very_smooth"
        elif score > 0.6:
            return "smooth"
        elif score > 0.4:
            return "moderately_smooth"
        elif score > 0.2:
            return "choppy"
        else:
            return "very_choppy"
    
    def _analyze_trix_trend_strength(self, trix: pd.Series) -> Dict[str, Any]:
        """Analyze TRIX trend strength."""
        current_trix = trix.iloc[-1]
        
        # Trend direction based on TRIX
        if current_trix > 0:
            trend_direction = "bullish"
        elif current_trix < 0:
            trend_direction = "bearish"
        else:
            trend_direction = "neutral"
        
        # Trend strength based on TRIX magnitude
        trix_std = trix.std()
        normalized_strength = abs(current_trix) / trix_std if trix_std > 0 else 0
        trend_strength = min(1.0, normalized_strength)
        
        # Trend consistency
        trend_consistency = self._calculate_trix_trend_consistency(trix)
        
        return {
            "direction": trend_direction,
            "strength": round(trend_strength, 3),
            "consistency": round(trend_consistency, 3),
            "quality": self._assess_trend_quality(trend_strength, trend_consistency)
        }
    
    def _calculate_trix_trend_consistency(self, trix: pd.Series) -> float:
        """Calculate TRIX trend consistency."""
        if len(trix) < 5:
            return 0.5
        
        # Look at recent TRIX values
        recent_trix = trix.iloc[-5:]
        current_direction = "positive" if trix.iloc[-1] > 0 else "negative"
        
        consistent_periods = sum(1 for val in recent_trix if
                               (val > 0 and current_direction == "positive") or
                               (val < 0 and current_direction == "negative"))
        
        return consistent_periods / len(recent_trix)
    
    def _assess_trend_quality(self, strength: float, consistency: float) -> str:
        """Assess overall trend quality."""
        if strength > 0.7 and consistency > 0.8:
            return "excellent"
        elif strength > 0.5 and consistency > 0.6:
            return "good"
        elif strength > 0.3 and consistency > 0.4:
            return "fair"
        else:
            return "poor"
    
    def _detect_trix_price_divergence(self, trix: pd.Series, prices: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect TRIX-price divergence patterns."""
        if len(trix) < 15 or len(prices) < 15:
            return None
        
        recent_periods = 10
        trix_recent = trix.iloc[-recent_periods:]
        price_recent = prices.iloc[-recent_periods:]
        
        # Find peaks and troughs
        trix_std = trix.std()
        prominence = max(trix_std * 0.1, 0.000001)
        
        trix_peaks = self._find_peaks(trix_recent, prominence=prominence)
        trix_troughs = self._find_troughs(trix_recent, prominence=prominence)
        price_peaks = self._find_peaks(price_recent)
        price_troughs = self._find_troughs(price_recent)
        
        # Bullish divergence: price lower lows, TRIX higher lows
        if len(trix_troughs) >= 2 and len(price_troughs) >= 2:
            latest_trix_trough = trix_troughs[-1]
            prev_trix_trough = trix_troughs[-2]
            latest_price_trough = price_troughs[-1]
            prev_price_trough = price_troughs[-2]
            
            if (latest_price_trough["value"] < prev_price_trough["value"] and
                latest_trix_trough["value"] > prev_trix_trough["value"]):
                return {
                    "type": "bullish_divergence",
                    "confidence": 0.8,  # Higher confidence for TRIX due to smoothing
                    "description": "Price making lower lows while TRIX making higher lows - strong reversal signal"
                }
        
        # Bearish divergence: price higher highs, TRIX lower highs
        if len(trix_peaks) >= 2 and len(price_peaks) >= 2:
            latest_trix_peak = trix_peaks[-1]
            prev_trix_peak = trix_peaks[-2]
            latest_price_peak = price_peaks[-1]
            prev_price_peak = price_peaks[-2]
            
            if (latest_price_peak["value"] > prev_price_peak["value"] and 
                latest_trix_peak["value"] < prev_trix_peak["value"]):
                return {
                    "type": "bearish_divergence",
                    "confidence": 0.8,  # Higher confidence for TRIX due to smoothing
                    "description": "Price making higher highs while TRIX making lower highs - strong reversal signal"
                }
        
        return None
    
    def _analyze_trix_histogram(self, trix: pd.Series, trix_signal: pd.Series) -> Dict[str, Any]:
        """Analyze TRIX histogram (TRIX - Signal)."""
        histogram = trix - trix_signal
        current_histogram = histogram.iloc[-1]
        
        # Histogram direction
        histogram_direction = "positive" if current_histogram > 0 else "negative"
        
        # Histogram momentum
        hist_velocity = self._calculate_velocity(histogram, 3)
        
        # Zero line crossings
        zero_crossings = 0
        for i in range(1, len(histogram)):
            if ((histogram.iloc[i] > 0 and histogram.iloc[i-1] <= 0) or 
                (histogram.iloc[i] < 0 and histogram.iloc[i-1] >= 0)):
                zero_crossings += 1
        
        return {
            "current_value": round(current_histogram, 6),
            "direction": histogram_direction,
            "momentum": round(hist_velocity, 6),
            "zero_crossings": zero_crossings,
            "momentum_interpretation": self._interpret_histogram_momentum(hist_velocity)
        }
    
    def _interpret_histogram_momentum(self, velocity: float) -> str:
        """Interpret TRIX histogram momentum."""
        if velocity > 0.00001:
            return "expanding"
        elif velocity < -0.00001:
            return "contracting"
        else:
            return "stable"
    
    def _generate_trix_signals(self, current_trix: float, current_signal: Optional[float],
                              momentum_analysis: Dict, zero_line_analysis: Dict,
                              signal_line_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate TRIX trading signals."""
        signals = []
        
        # Zero line signals
        position = zero_line_analysis.get("position", "at_zero")
        latest_crossing = zero_line_analysis.get("latest_crossing")
        
        if latest_crossing and latest_crossing["periods_ago"] <= 3:
            crossing_type = latest_crossing["type"]
            signal_type = "buy_signal" if "bullish" in crossing_type else "sell_signal"
            
            signals.append({
                "type": signal_type,
                "strength": "strong",
                "reason": f"Recent TRIX {crossing_type.replace('_', ' ')} {latest_crossing['periods_ago']} periods ago",
                "confidence": 0.8  # High confidence for TRIX due to smoothing
            })
        
        # Signal line crossover signals
        if signal_line_analysis and current_signal is not None:
            latest_crossover = signal_line_analysis.get("latest_crossover")
            if latest_crossover and latest_crossover["periods_ago"] <= 2:
                crossover_type = latest_crossover["type"]
                signal_type = "buy_signal" if "bullish" in crossover_type else "sell_signal"
                
                signals.append({
                    "type": signal_type,
                    "strength": "medium",
                    "reason": f"TRIX {crossover_type.replace('_', ' ')} signal line",
                    "confidence": 0.7
                })
        
        # Momentum-based signals
        momentum_direction = momentum_analysis.get("direction", "neutral")
        strength_level = momentum_analysis.get("strength_level", "weak")
        persistence = momentum_analysis.get("persistence", 0.5)
        
        if momentum_direction != "neutral" and strength_level in ["strong", "very_strong"] and persistence > 0.7:
            signal_type = "momentum_buy" if momentum_direction == "bullish" else "momentum_sell"
            
            signals.append({
                "type": signal_type,
                "strength": "medium",
                "reason": f"Strong {momentum_direction} TRIX momentum with high persistence",
                "confidence": 0.6
            })
        
        return signals
    
    def _calculate_trix_confidence(self, trix: pd.Series, momentum_analysis: Dict, 
                                  smoothness_analysis: Dict) -> float:
        """Calculate TRIX analysis confidence."""
        confidence_factors = []
        
        # Data quantity factor
        data_factor = min(1.0, len(trix) / 25)  # TRIX needs less data due to smoothing
        confidence_factors.append(data_factor)
        
        # Momentum persistence factor
        persistence = momentum_analysis.get("persistence", 0.5)
        confidence_factors.append(persistence)
        
        # Smoothness factor (smoother = more reliable for TRIX)
        if smoothness_analysis:
            smoothness_score = smoothness_analysis.get("smoothness_score", 0.5)
            confidence_factors.append(smoothness_score)
        else:
            confidence_factors.append(0.7)  # TRIX is inherently smooth
        
        # Signal clarity factor
        current_trix = abs(trix.iloc[-1])
        trix_std = trix.std()
        if current_trix > trix_std:
            clarity_factor = 0.8  # Clear signal
        else:
            clarity_factor = 0.6  # Weaker signal
        confidence_factors.append(clarity_factor)
        
        return round(np.mean(confidence_factors), 3)
    
    def _generate_trix_summary(self, current_trix: float, current_signal: Optional[float],
                              momentum_analysis: Dict, zero_line_analysis: Dict) -> str:
        """Generate human-readable TRIX summary."""
        momentum_direction = momentum_analysis.get("direction", "neutral")
        strength_level = momentum_analysis.get("strength_level", "weak")
        position = zero_line_analysis.get("position", "at_zero")
        
        summary = f"TRIX {current_trix:.6f} - {strength_level} {momentum_direction} momentum"
        
        if current_signal is not None:
            histogram = current_trix - current_signal
            summary += f", histogram {histogram:+.6f}"
        
        summary += f" ({position.replace('_', ' ')})"
        
        return summary