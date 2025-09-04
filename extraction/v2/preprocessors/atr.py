"""
ATR (Average True Range) Preprocessor.

Advanced ATR preprocessing with volatility analysis, trend strength assessment,
and stop-loss level recommendations based on market volatility.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePreprocessor


class ATRPreprocessor(BasePreprocessor):
    """Advanced ATR preprocessor with professional-grade volatility analysis."""
    
    def preprocess(self, atr: pd.Series, prices: pd.Series = None, 
                  length: int = 14, **kwargs) -> Dict[str, Any]:
        """
        Advanced ATR preprocessing with comprehensive volatility analysis.
        
        ATR measures market volatility by calculating the average of true ranges
        over a specified period. Higher values indicate higher volatility.
        
        Args:
            atr: ATR values
            prices: Price series for additional analysis (optional)
            length: ATR calculation period
            
        Returns:
            Dictionary with comprehensive ATR analysis
        """
        if len(atr) < 5:
            return {"error": "Insufficient data for ATR analysis"}
        
        current_atr = float(atr.iloc[-1])
        
        # Volatility analysis
        volatility_analysis = self._analyze_volatility_levels(atr, prices)
        
        # Trend analysis
        atr_trend_analysis = self._analyze_atr_trend(atr)
        
        # Volatility cycles
        cycle_analysis = self._analyze_volatility_cycles(atr)
        
        # Relative volatility analysis
        relative_analysis = self._analyze_relative_volatility(atr)
        
        # Stop loss analysis
        stop_loss_analysis = self._analyze_stop_loss_levels(atr, prices) if prices is not None else {}
        
        # Breakout analysis
        breakout_analysis = self._analyze_breakout_potential(atr)
        
        # Signal generation
        signals = self._generate_atr_signals(current_atr, volatility_analysis, atr_trend_analysis)
        
        # Confidence calculation
        confidence = self._calculate_atr_confidence(atr, volatility_analysis)
        
        return {
            "indicator": "ATR",
            "current": {
                "value": round(current_atr, 6),
                "timestamp": datetime.now().isoformat()
            },
            "volatility": volatility_analysis,
            "trend": atr_trend_analysis,
            "cycles": cycle_analysis,
            "relative": relative_analysis,
            "stop_loss": stop_loss_analysis,
            "breakout": breakout_analysis,
            "signals": signals,
            "confidence": confidence,
            "summary": self._generate_atr_summary(current_atr, volatility_analysis, atr_trend_analysis)
        }
    
    def _analyze_volatility_levels(self, atr: pd.Series, prices: pd.Series = None) -> Dict[str, Any]:
        """Analyze current volatility levels."""
        current_atr = atr.iloc[-1]
        
        # Statistical analysis
        mean_atr = atr.mean()
        std_atr = atr.std()
        max_atr = atr.max()
        min_atr = atr.min()
        
        # Percentile analysis
        percentile_rank = self._calculate_position_rank(atr, lookback=len(atr))
        
        # Volatility level classification
        if current_atr > mean_atr + 2 * std_atr:
            volatility_level = "extremely_high"
        elif current_atr > mean_atr + std_atr:
            volatility_level = "high"
        elif current_atr > mean_atr:
            volatility_level = "above_average"
        elif current_atr > mean_atr - std_atr:
            volatility_level = "below_average"
        else:
            volatility_level = "low"
        
        # Relative to price analysis
        relative_atr = None
        if prices is not None:
            current_price = prices.iloc[-1]
            relative_atr = (current_atr / current_price) * 100
        
        return {
            "current_level": volatility_level,
            "percentile_rank": round(percentile_rank, 1),
            "relative_to_mean": round((current_atr / mean_atr - 1) * 100, 2),
            "relative_to_price_pct": round(relative_atr, 3) if relative_atr is not None else None,
            "statistical": {
                "mean": round(mean_atr, 6),
                "std": round(std_atr, 6),
                "max": round(max_atr, 6),
                "min": round(min_atr, 6)
            }
        }
    
    def _analyze_atr_trend(self, atr: pd.Series) -> Dict[str, Any]:
        """Analyze ATR trend characteristics."""
        if len(atr) < 5:
            return {}
        
        # ATR velocity and acceleration
        velocity = self._calculate_velocity(atr, 3)
        acceleration = self._calculate_acceleration(atr, 6)
        
        # Trend direction
        if velocity > 0.001:
            trend_direction = "rising"
        elif velocity < -0.001:
            trend_direction = "falling"
        else:
            trend_direction = "stable"
        
        # Trend strength
        velocity_magnitude = abs(velocity)
        std_atr = atr.std()
        trend_strength = min(1.0, velocity_magnitude / (std_atr * 0.1)) if std_atr > 0 else 0
        
        # Recent trend consistency
        recent_atr = atr.iloc[-5:] if len(atr) >= 5 else atr
        consistency = self._calculate_trend_consistency(recent_atr)
        
        return {
            "direction": trend_direction,
            "velocity": round(velocity, 6),
            "acceleration": round(acceleration, 6),
            "strength": round(trend_strength, 3),
            "consistency": round(consistency, 3),
            "interpretation": self._interpret_atr_trend(trend_direction, trend_strength, consistency)
        }
    
    def _calculate_trend_consistency(self, values: pd.Series) -> float:
        """Calculate consistency of ATR trend."""
        if len(values) < 3:
            return 0.5
        
        changes = values.diff().dropna()
        if len(changes) == 0:
            return 0.5
        
        positive_changes = sum(1 for x in changes if x > 0)
        negative_changes = sum(1 for x in changes if x < 0)
        total_changes = len(changes)
        
        # Return consistency ratio
        max_directional = max(positive_changes, negative_changes)
        return max_directional / total_changes if total_changes > 0 else 0.5
    
    def _interpret_atr_trend(self, direction: str, strength: float, consistency: float) -> str:
        """Interpret ATR trend characteristics."""
        if direction == "rising" and strength > 0.7 and consistency > 0.7:
            return "volatility_expanding_strongly"
        elif direction == "rising" and strength > 0.4:
            return "volatility_expanding"
        elif direction == "falling" and strength > 0.7 and consistency > 0.7:
            return "volatility_contracting_strongly"
        elif direction == "falling" and strength > 0.4:
            return "volatility_contracting"
        else:
            return "volatility_stable"
    
    def _analyze_volatility_cycles(self, atr: pd.Series) -> Dict[str, Any]:
        """Analyze volatility cycles and patterns."""
        if len(atr) < 20:
            return {"insufficient_data": True}
        
        # Find volatility peaks and troughs
        peaks = self._find_peaks(atr, prominence=atr.std() * 0.5)
        troughs = self._find_troughs(atr, prominence=atr.std() * 0.5)
        
        # Cycle analysis
        cycle_detected = len(peaks) >= 2 or len(troughs) >= 2
        
        analysis = {"cycle_detected": cycle_detected}
        
        if cycle_detected:
            # Calculate average cycle length
            if len(peaks) >= 2:
                peak_distances = [peaks[i]["index"] - peaks[i-1]["index"] for i in range(1, len(peaks))]
                avg_peak_cycle = np.mean(peak_distances) if peak_distances else None
                analysis["avg_expansion_cycle"] = round(avg_peak_cycle, 1) if avg_peak_cycle else None
            
            if len(troughs) >= 2:
                trough_distances = [troughs[i]["index"] - troughs[i-1]["index"] for i in range(1, len(troughs))]
                avg_trough_cycle = np.mean(trough_distances) if trough_distances else None
                analysis["avg_contraction_cycle"] = round(avg_trough_cycle, 1) if avg_trough_cycle else None
            
            analysis["recent_peaks"] = len(peaks)
            analysis["recent_troughs"] = len(troughs)
            
            # Current cycle position
            current_atr = atr.iloc[-1]
            recent_peak = peaks[-1] if peaks else None
            recent_trough = troughs[-1] if troughs else None
            
            if recent_peak and recent_trough:
                if recent_peak["index"] > recent_trough["index"]:
                    # Most recent extreme was a peak
                    analysis["cycle_position"] = "post_peak_contraction"
                else:
                    # Most recent extreme was a trough  
                    analysis["cycle_position"] = "post_trough_expansion"
            
        return analysis
    
    def _analyze_relative_volatility(self, atr: pd.Series) -> Dict[str, Any]:
        """Analyze ATR relative to its own history."""
        if len(atr) < 10:
            return {}
        
        current_atr = atr.iloc[-1]
        
        # Different timeframe comparisons
        periods = [5, 10, 20, 50] if len(atr) >= 50 else [min(p, len(atr)) for p in [5, 10, 20] if p <= len(atr)]
        
        comparisons = {}
        for period in periods:
            if period <= len(atr):
                period_mean = atr.iloc[-period:].mean()
                relative_change = ((current_atr / period_mean) - 1) * 100
                comparisons[f"{period}p_avg"] = round(relative_change, 2)
        
        # Volatility regime classification
        long_term_mean = atr.iloc[-min(50, len(atr)):].mean()
        regime_ratio = current_atr / long_term_mean
        
        if regime_ratio > 1.5:
            regime = "high_volatility"
        elif regime_ratio > 1.2:
            regime = "elevated_volatility"
        elif regime_ratio < 0.5:
            regime = "low_volatility"
        elif regime_ratio < 0.8:
            regime = "suppressed_volatility"
        else:
            regime = "normal_volatility"
        
        return {
            "comparisons": comparisons,
            "regime": regime,
            "regime_ratio": round(regime_ratio, 3)
        }
    
    def _analyze_stop_loss_levels(self, atr: pd.Series, prices: pd.Series) -> Dict[str, Any]:
        """Analyze ATR-based stop loss recommendations."""
        current_atr = atr.iloc[-1]
        current_price = prices.iloc[-1]
        
        # Multiple ATR multipliers for different strategies
        multipliers = [1.0, 1.5, 2.0, 2.5, 3.0]
        stop_levels = {}
        
        for mult in multipliers:
            stop_distance = current_atr * mult
            long_stop = current_price - stop_distance
            short_stop = current_price + stop_distance
            stop_pct = (stop_distance / current_price) * 100
            
            stop_levels[f"{mult}x_atr"] = {
                "long_stop": round(long_stop, 6),
                "short_stop": round(short_stop, 6),
                "distance": round(stop_distance, 6),
                "distance_pct": round(stop_pct, 3)
            }
        
        # Recommended multiplier based on volatility regime
        volatility_level = self._get_volatility_level(atr)
        recommended_mult = self._get_recommended_multiplier(volatility_level)
        
        return {
            "current_price": round(current_price, 6),
            "stop_levels": stop_levels,
            "recommended_multiplier": recommended_mult,
            "recommended_stop": stop_levels.get(f"{recommended_mult}x_atr", {})
        }
    
    def _get_volatility_level(self, atr: pd.Series) -> str:
        """Get current volatility level classification."""
        current_atr = atr.iloc[-1]
        mean_atr = atr.mean()
        std_atr = atr.std()
        
        if current_atr > mean_atr + std_atr:
            return "high"
        elif current_atr < mean_atr - std_atr:
            return "low"
        else:
            return "normal"
    
    def _get_recommended_multiplier(self, volatility_level: str) -> float:
        """Get recommended ATR multiplier based on volatility level."""
        recommendations = {
            "low": 1.5,      # Tighter stops in low volatility
            "normal": 2.0,   # Standard stops in normal volatility
            "high": 2.5      # Wider stops in high volatility
        }
        return recommendations.get(volatility_level, 2.0)
    
    def _analyze_breakout_potential(self, atr: pd.Series) -> Dict[str, Any]:
        """Analyze breakout potential based on ATR patterns."""
        if len(atr) < 10:
            return {}
        
        current_atr = atr.iloc[-1]
        recent_atr = atr.iloc[-5:]  # Last 5 periods
        
        # Volatility squeeze detection (low ATR)
        mean_atr = atr.mean()
        std_atr = atr.std()
        
        squeeze_threshold = mean_atr - 0.5 * std_atr
        squeeze_detected = current_atr < squeeze_threshold
        
        # Expansion potential
        if squeeze_detected:
            # How long has volatility been compressed?
            squeeze_periods = 0
            for i in range(len(atr) - 1, -1, -1):
                if atr.iloc[i] < squeeze_threshold:
                    squeeze_periods += 1
                else:
                    break
            
            expansion_potential = min(1.0, squeeze_periods / 10)  # Max at 10 periods
        else:
            expansion_potential = 0.0
            squeeze_periods = 0
        
        # Recent volatility change
        if len(recent_atr) >= 2:
            recent_change = ((recent_atr.iloc[-1] / recent_atr.iloc[0]) - 1) * 100
        else:
            recent_change = 0.0
        
        return {
            "squeeze_detected": squeeze_detected,
            "squeeze_periods": squeeze_periods,
            "expansion_potential": round(expansion_potential, 3),
            "recent_volatility_change_pct": round(recent_change, 2),
            "breakout_setup": squeeze_detected and squeeze_periods >= 3
        }
    
    def _generate_atr_signals(self, current_atr: float, volatility_analysis: Dict, trend_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate ATR-based signals."""
        signals = []
        
        # Volatility level signals
        volatility_level = volatility_analysis["current_level"]
        
        if volatility_level == "extremely_high":
            signals.append({
                "type": "high_volatility_warning",
                "strength": "high",
                "reason": "ATR at extremely high levels, increased risk",
                "confidence": 0.8
            })
        elif volatility_level == "low":
            signals.append({
                "type": "low_volatility_alert",
                "strength": "medium",
                "reason": "ATR at low levels, potential breakout setup",
                "confidence": 0.7
            })
        
        # Trend signals
        if trend_analysis:
            trend_interpretation = trend_analysis.get("interpretation", "")
            
            if "expanding_strongly" in trend_interpretation:
                signals.append({
                    "type": "volatility_expansion",
                    "strength": "medium",
                    "reason": "ATR expanding strongly, momentum building",
                    "confidence": 0.7
                })
            elif "contracting_strongly" in trend_interpretation:
                signals.append({
                    "type": "volatility_contraction",
                    "strength": "medium", 
                    "reason": "ATR contracting strongly, potential squeeze",
                    "confidence": 0.7
                })
        
        # Percentile rank signals
        percentile_rank = volatility_analysis.get("percentile_rank", 50)
        
        if percentile_rank > 90:
            signals.append({
                "type": "extreme_volatility_high",
                "strength": "high",
                "reason": f"ATR in top {100-percentile_rank:.0f}% of range",
                "confidence": 0.8
            })
        elif percentile_rank < 10:
            signals.append({
                "type": "extreme_volatility_low",
                "strength": "medium",
                "reason": f"ATR in bottom {percentile_rank:.0f}% of range",
                "confidence": 0.7
            })
        
        return signals
    
    def _calculate_atr_confidence(self, atr: pd.Series, volatility_analysis: Dict) -> float:
        """Calculate ATR analysis confidence."""
        confidence_factors = []
        
        # Data quantity factor
        data_factor = min(1.0, len(atr) / 30)
        confidence_factors.append(data_factor)
        
        # Data stability factor (ATR is generally stable)
        std_atr = atr.std()
        mean_atr = atr.mean()
        stability_factor = max(0.5, min(1.0, 1.0 - (std_atr / mean_atr))) if mean_atr > 0 else 0.5
        confidence_factors.append(stability_factor)
        
        # Clear signal factor
        percentile_rank = volatility_analysis.get("percentile_rank", 50)
        if percentile_rank > 80 or percentile_rank < 20:
            signal_clarity = 0.8
        else:
            signal_clarity = 0.6
        confidence_factors.append(signal_clarity)
        
        return round(np.mean(confidence_factors), 3)
    
    def _generate_atr_summary(self, current_atr: float, volatility_analysis: Dict, trend_analysis: Dict) -> str:
        """Generate human-readable ATR summary."""
        volatility_level = volatility_analysis["current_level"]
        percentile = volatility_analysis["percentile_rank"]
        
        summary = f"ATR {current_atr:.6f} - {volatility_level.replace('_', ' ')} volatility ({percentile:.0f}th percentile)"
        
        if trend_analysis:
            interpretation = trend_analysis.get("interpretation", "")
            if interpretation != "volatility_stable":
                summary += f", {interpretation.replace('_', ' ')}"
        
        return summary