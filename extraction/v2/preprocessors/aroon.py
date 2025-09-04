"""
Aroon Preprocessor.

Advanced Aroon preprocessing with trend identification, strength analysis,
and Aroon Up/Down oscillator pattern recognition.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePreprocessor


class AroonPreprocessor(BasePreprocessor):
    """Advanced Aroon preprocessor with professional-grade trend analysis."""
    
    def preprocess(self, aroon_up: pd.Series, aroon_down: pd.Series, 
                  prices: pd.Series = None, length: int = 14, **kwargs) -> Dict[str, Any]:
        """
        Advanced Aroon preprocessing with comprehensive trend analysis.
        
        Aroon Up measures periods since highest high, Aroon Down measures
        periods since lowest low. Values range 0-100, with high values
        indicating recent highs/lows.
        
        Args:
            aroon_up: Aroon Up values (0-100)
            aroon_down: Aroon Down values (0-100)
            prices: Price series for additional analysis (optional)
            length: Aroon calculation period
            
        Returns:
            Dictionary with comprehensive Aroon analysis
        """
        if len(aroon_up) < 5 or len(aroon_down) < 5:
            return {"error": "Insufficient data for Aroon analysis"}
        
        current_aroon_up = float(aroon_up.iloc[-1])
        current_aroon_down = float(aroon_down.iloc[-1])
        
        # Oscillator analysis
        oscillator_analysis = self._analyze_aroon_oscillator(aroon_up, aroon_down)
        
        # Trend analysis
        trend_analysis = self._analyze_aroon_trend(aroon_up, aroon_down, current_aroon_up, current_aroon_down)
        
        # Crossover analysis
        crossover_analysis = self._analyze_aroon_crossovers(aroon_up, aroon_down)
        
        # Strength analysis
        strength_analysis = self._analyze_aroon_strength(aroon_up, aroon_down)
        
        # Pattern analysis
        pattern_analysis = self._analyze_aroon_patterns(aroon_up, aroon_down)
        
        # Parallel analysis (when both indicators move together)
        parallel_analysis = self._analyze_parallel_movement(aroon_up, aroon_down)
        
        # Divergence analysis
        divergence = None
        if prices is not None:
            divergence = self._detect_aroon_divergence(aroon_up, aroon_down, prices)
        
        # Signal generation
        signals = self._generate_aroon_signals(current_aroon_up, current_aroon_down, 
                                              trend_analysis, crossover_analysis, strength_analysis)
        
        # Confidence calculation
        confidence = self._calculate_aroon_confidence(aroon_up, aroon_down, trend_analysis, strength_analysis)
        
        return {
            "indicator": "Aroon",
            "current": {
                "aroon_up": round(current_aroon_up, 2),
                "aroon_down": round(current_aroon_down, 2),
                "oscillator": round(current_aroon_up - current_aroon_down, 2),
                "timestamp": datetime.now().isoformat()
            },
            "trend": trend_analysis,
            "oscillator": oscillator_analysis,
            "crossovers": crossover_analysis,
            "strength": strength_analysis,
            "patterns": pattern_analysis,
            "parallel_movement": parallel_analysis,
            "divergence": divergence,
            "signals": signals,
            "confidence": confidence,
            "summary": self._generate_aroon_summary(current_aroon_up, current_aroon_down, 
                                                   trend_analysis, oscillator_analysis)
        }
    
    def _analyze_aroon_oscillator(self, aroon_up: pd.Series, aroon_down: pd.Series) -> Dict[str, Any]:
        """Analyze Aroon Oscillator (Aroon Up - Aroon Down)."""
        oscillator = aroon_up - aroon_down
        current_osc = oscillator.iloc[-1]
        
        # Oscillator zones
        if current_osc > 50:
            zone = "strong_bullish"
        elif current_osc > 20:
            zone = "bullish"
        elif current_osc > -20:
            zone = "neutral"
        elif current_osc > -50:
            zone = "bearish"
        else:
            zone = "strong_bearish"
        
        # Oscillator momentum
        osc_velocity = self._calculate_velocity(oscillator, 3)
        osc_acceleration = self._calculate_acceleration(oscillator, 5)
        
        # Zero line analysis
        zero_crossings = self._count_zero_crossings(oscillator)
        time_above_zero = sum(1 for v in oscillator if v > 0)
        time_below_zero = sum(1 for v in oscillator if v < 0)
        total_periods = len(oscillator)
        
        return {
            "current_value": round(current_osc, 2),
            "zone": zone,
            "velocity": round(osc_velocity, 2),
            "acceleration": round(osc_acceleration, 2),
            "zero_crossings": zero_crossings,
            "time_above_zero_pct": round((time_above_zero / total_periods) * 100, 1),
            "time_below_zero_pct": round((time_below_zero / total_periods) * 100, 1),
            "oscillator_interpretation": self._interpret_oscillator(current_osc, osc_velocity)
        }
    
    def _count_zero_crossings(self, oscillator: pd.Series) -> int:
        """Count zero line crossings in oscillator."""
        crossings = 0
        for i in range(1, len(oscillator)):
            if (oscillator.iloc[i] > 0 and oscillator.iloc[i-1] <= 0) or \
               (oscillator.iloc[i] < 0 and oscillator.iloc[i-1] >= 0):
                crossings += 1
        return crossings
    
    def _interpret_oscillator(self, current_osc: float, velocity: float) -> str:
        """Interpret oscillator position and momentum."""
        if current_osc > 50 and velocity > 0:
            return "strong_bullish_momentum"
        elif current_osc > 50:
            return "strong_bullish_slowing"
        elif current_osc > 0 and velocity > 0:
            return "bullish_strengthening"
        elif current_osc > 0:
            return "bullish_weakening"
        elif current_osc > -50 and velocity < 0:
            return "bearish_strengthening"
        elif current_osc > -50:
            return "bearish_weakening"
        elif velocity < 0:
            return "strong_bearish_momentum"
        else:
            return "strong_bearish_slowing"
    
    def _analyze_aroon_trend(self, aroon_up: pd.Series, aroon_down: pd.Series, 
                            current_up: float, current_down: float) -> Dict[str, Any]:
        """Analyze Aroon trend characteristics."""
        # Current trend determination
        if current_up > 70 and current_down < 30:
            current_trend = "strong_uptrend"
        elif current_up > current_down and current_up > 50:
            current_trend = "uptrend"
        elif current_down > 70 and current_up < 30:
            current_trend = "strong_downtrend"
        elif current_down > current_up and current_down > 50:
            current_trend = "downtrend"
        else:
            current_trend = "sideways"
        
        # Trend strength (based on separation)
        separation = abs(current_up - current_down)
        trend_strength = min(1.0, separation / 100)
        
        # Trend consistency
        trend_consistency = self._calculate_aroon_trend_consistency(aroon_up, aroon_down)
        
        # Trend duration
        trend_duration = self._calculate_aroon_trend_duration(aroon_up, aroon_down)
        
        return {
            "current_trend": current_trend,
            "trend_strength": round(trend_strength, 3),
            "trend_consistency": round(trend_consistency, 3),
            "trend_duration": trend_duration,
            "separation": round(separation, 2),
            "trend_quality": self._assess_trend_quality(current_trend, trend_strength, trend_consistency)
        }
    
    def _calculate_aroon_trend_consistency(self, aroon_up: pd.Series, aroon_down: pd.Series) -> float:
        """Calculate consistency of Aroon trend signals."""
        if len(aroon_up) < 10:
            return 0.5
        
        recent_up = aroon_up.iloc[-10:]
        recent_down = aroon_down.iloc[-10:]
        
        # Count periods where trend direction was consistent
        consistent_periods = 0
        current_trend_up = recent_up.iloc[-1] > recent_down.iloc[-1]
        
        for i in range(len(recent_up)):
            period_trend_up = recent_up.iloc[i] > recent_down.iloc[i]
            if period_trend_up == current_trend_up:
                consistent_periods += 1
        
        return consistent_periods / len(recent_up)
    
    def _calculate_aroon_trend_duration(self, aroon_up: pd.Series, aroon_down: pd.Series) -> int:
        """Calculate duration of current Aroon trend."""
        if len(aroon_up) < 2:
            return 1
        
        current_trend_up = aroon_up.iloc[-1] > aroon_down.iloc[-1]
        duration = 1
        
        for i in range(2, len(aroon_up) + 1):
            if i > len(aroon_up):
                break
            
            period_trend_up = aroon_up.iloc[-i] > aroon_down.iloc[-i]
            
            if period_trend_up == current_trend_up:
                duration += 1
            else:
                break
        
        return duration
    
    def _assess_trend_quality(self, trend: str, strength: float, consistency: float) -> str:
        """Assess overall quality of Aroon trend."""
        if "strong" in trend and strength > 0.7 and consistency > 0.8:
            return "excellent"
        elif strength > 0.6 and consistency > 0.7:
            return "good"
        elif strength > 0.4 and consistency > 0.6:
            return "fair"
        else:
            return "poor"
    
    def _analyze_aroon_crossovers(self, aroon_up: pd.Series, aroon_down: pd.Series) -> Dict[str, Any]:
        """Analyze Aroon Up/Down crossovers."""
        crossovers = []
        
        for i in range(1, min(15, len(aroon_up))):
            prev_up = aroon_up.iloc[-(i+1)]
            curr_up = aroon_up.iloc[-i]
            prev_down = aroon_down.iloc[-(i+1)]
            curr_down = aroon_down.iloc[-i]
            
            # Bullish crossover (Aroon Up crosses above Aroon Down)
            if prev_up <= prev_down and curr_up > curr_down:
                crossovers.append({
                    "type": "bullish_crossover",
                    "periods_ago": i,
                    "up_value": round(curr_up, 2),
                    "down_value": round(curr_down, 2),
                    "strength": abs(curr_up - curr_down),
                    "location": self._get_crossover_location(curr_up, curr_down)
                })
            # Bearish crossover (Aroon Up crosses below Aroon Down)
            elif prev_up >= prev_down and curr_up < curr_down:
                crossovers.append({
                    "type": "bearish_crossover",
                    "periods_ago": i,
                    "up_value": round(curr_up, 2),
                    "down_value": round(curr_down, 2),
                    "strength": abs(curr_up - curr_down),
                    "location": self._get_crossover_location(curr_up, curr_down)
                })
        
        return {
            "recent_crossovers": crossovers[:5],
            "latest_crossover": crossovers[0] if crossovers else None,
            "crossover_frequency": self._calculate_crossover_frequency(crossovers)
        }
    
    def _get_crossover_location(self, up_value: float, down_value: float) -> str:
        """Determine location of crossover."""
        avg_value = (up_value + down_value) / 2
        
        if avg_value > 70:
            return "high_levels"
        elif avg_value < 30:
            return "low_levels"
        else:
            return "mid_levels"
    
    def _calculate_crossover_frequency(self, crossovers: List[Dict]) -> str:
        """Calculate frequency of Aroon crossovers."""
        if len(crossovers) < 2:
            return "low"
        
        avg_periods_between = np.mean([crossovers[i]["periods_ago"] - crossovers[i+1]["periods_ago"] 
                                      for i in range(len(crossovers)-1)])
        
        if avg_periods_between < 5:
            return "high"
        elif avg_periods_between < 10:
            return "medium"
        else:
            return "low"
    
    def _analyze_aroon_strength(self, aroon_up: pd.Series, aroon_down: pd.Series) -> Dict[str, Any]:
        """Analyze strength characteristics of Aroon indicators."""
        current_up = aroon_up.iloc[-1]
        current_down = aroon_down.iloc[-1]
        
        # Individual strength analysis
        up_strength = self._categorize_aroon_strength(current_up)
        down_strength = self._categorize_aroon_strength(current_down)
        
        # Combined strength
        max_value = max(current_up, current_down)
        combined_strength = self._categorize_aroon_strength(max_value)
        
        # Strength momentum
        up_momentum = self._calculate_velocity(aroon_up, 3)
        down_momentum = self._calculate_velocity(aroon_down, 3)
        
        # Recent strength evolution
        recent_up = aroon_up.iloc[-5:] if len(aroon_up) >= 5 else aroon_up
        recent_down = aroon_down.iloc[-5:] if len(aroon_down) >= 5 else aroon_down
        
        up_evolution = "rising" if recent_up.iloc[-1] > recent_up.iloc[0] else "falling"
        down_evolution = "rising" if recent_down.iloc[-1] > recent_down.iloc[0] else "falling"
        
        return {
            "aroon_up_strength": up_strength,
            "aroon_down_strength": down_strength,
            "combined_strength": combined_strength,
            "up_momentum": round(up_momentum, 2),
            "down_momentum": round(down_momentum, 2),
            "up_evolution": up_evolution,
            "down_evolution": down_evolution,
            "dominant_indicator": "aroon_up" if current_up > current_down else "aroon_down"
        }
    
    def _categorize_aroon_strength(self, value: float) -> str:
        """Categorize Aroon strength level."""
        if value >= 80:
            return "very_strong"
        elif value >= 60:
            return "strong"
        elif value >= 40:
            return "moderate"
        elif value >= 20:
            return "weak"
        else:
            return "very_weak"
    
    def _analyze_aroon_patterns(self, aroon_up: pd.Series, aroon_down: pd.Series) -> Dict[str, Any]:
        """Analyze Aroon patterns and formations."""
        patterns = {}
        
        if len(aroon_up) >= 15:
            # Parallel movement pattern
            parallel = self._detect_parallel_aroon(aroon_up, aroon_down)
            if parallel:
                patterns["parallel_movement"] = parallel
            
            # Extreme readings pattern
            extreme_pattern = self._detect_extreme_readings(aroon_up, aroon_down)
            if extreme_pattern:
                patterns["extreme_readings"] = extreme_pattern
            
            # Consolidation pattern
            consolidation = self._detect_aroon_consolidation(aroon_up, aroon_down)
            if consolidation:
                patterns["consolidation"] = consolidation
        
        return patterns
    
    def _detect_parallel_aroon(self, aroon_up: pd.Series, aroon_down: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect periods where Aroon Up and Down move in parallel."""
        if len(aroon_up) < 8:
            return None
        
        recent_up = aroon_up.iloc[-8:]
        recent_down = aroon_down.iloc[-8:]
        
        # Calculate correlation between recent movements
        up_changes = recent_up.diff().dropna()
        down_changes = recent_down.diff().dropna()
        
        if len(up_changes) < 3 or len(down_changes) < 3:
            return None
        
        correlation = np.corrcoef(up_changes, down_changes)[0, 1]
        
        if not np.isnan(correlation) and abs(correlation) > 0.7:
            return {
                "type": "parallel_movement",
                "correlation": round(correlation, 3),
                "direction": "same" if correlation > 0 else "opposite",
                "description": f"Aroon indicators moving in {'same' if correlation > 0 else 'opposite'} direction"
            }
        
        return None
    
    def _detect_extreme_readings(self, aroon_up: pd.Series, aroon_down: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect extreme Aroon readings."""
        current_up = aroon_up.iloc[-1]
        current_down = aroon_down.iloc[-1]
        
        # Both indicators very high (consolidation)
        if current_up > 80 and current_down > 80:
            return {
                "type": "both_extreme_high",
                "description": "Both indicators very high, potential breakout setup"
            }
        
        # Both indicators very low (consolidation)
        elif current_up < 20 and current_down < 20:
            return {
                "type": "both_extreme_low",
                "description": "Both indicators very low, ranging market"
            }
        
        # One very high, one very low (strong trend)
        elif (current_up > 80 and current_down < 20) or (current_down > 80 and current_up < 20):
            dominant = "up" if current_up > current_down else "down"
            return {
                "type": "extreme_separation",
                "dominant": dominant,
                "description": f"Extreme separation favoring Aroon {dominant.upper()}"
            }
        
        return None
    
    def _detect_aroon_consolidation(self, aroon_up: pd.Series, aroon_down: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect Aroon consolidation patterns."""
        if len(aroon_up) < 10:
            return None
        
        recent_up = aroon_up.iloc[-10:]
        recent_down = aroon_down.iloc[-10:]
        
        # Check if both indicators have been relatively stable and close
        up_volatility = recent_up.std()
        down_volatility = recent_down.std()
        avg_separation = abs(recent_up - recent_down).mean()
        
        if up_volatility < 15 and down_volatility < 15 and avg_separation < 30:
            return {
                "type": "consolidation",
                "duration": 10,
                "avg_separation": round(avg_separation, 2),
                "description": "Consolidation pattern detected, low volatility in both indicators"
            }
        
        return None
    
    def _analyze_parallel_movement(self, aroon_up: pd.Series, aroon_down: pd.Series) -> Dict[str, Any]:
        """Analyze parallel movement characteristics."""
        if len(aroon_up) < 8:
            return {}
        
        # Calculate rolling correlation
        window = min(8, len(aroon_up))
        recent_up = aroon_up.iloc[-window:]
        recent_down = aroon_down.iloc[-window:]
        
        up_changes = recent_up.diff().dropna()
        down_changes = recent_down.diff().dropna()
        
        if len(up_changes) < 3:
            return {}
        
        correlation = np.corrcoef(up_changes, down_changes)[0, 1] if len(up_changes) == len(down_changes) else 0
        
        # Parallel movement interpretation
        if not np.isnan(correlation):
            if correlation > 0.7:
                movement_type = "strong_positive_correlation"
            elif correlation > 0.3:
                movement_type = "moderate_positive_correlation"
            elif correlation < -0.7:
                movement_type = "strong_negative_correlation"
            elif correlation < -0.3:
                movement_type = "moderate_negative_correlation"
            else:
                movement_type = "independent_movement"
        else:
            movement_type = "insufficient_data"
        
        return {
            "correlation": round(correlation, 3) if not np.isnan(correlation) else None,
            "movement_type": movement_type,
            "interpretation": self._interpret_parallel_movement(movement_type)
        }
    
    def _interpret_parallel_movement(self, movement_type: str) -> str:
        """Interpret parallel movement patterns."""
        interpretations = {
            "strong_positive_correlation": "Indicators moving together, potential consolidation",
            "moderate_positive_correlation": "Some coordination in indicator movement",
            "strong_negative_correlation": "Indicators moving opposite, strong trending potential",
            "moderate_negative_correlation": "Some opposition in indicator movement",
            "independent_movement": "Indicators moving independently",
            "insufficient_data": "Not enough data for correlation analysis"
        }
        return interpretations.get(movement_type, "Unknown movement pattern")
    
    def _detect_aroon_divergence(self, aroon_up: pd.Series, aroon_down: pd.Series, prices: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect Aroon-price divergence patterns."""
        if len(aroon_up) < 15 or len(prices) < 15:
            return None
        
        recent_periods = 10
        aroon_osc = (aroon_up - aroon_down).iloc[-recent_periods:]
        price_recent = prices.iloc[-recent_periods:]
        
        # Find peaks and troughs
        osc_peaks = self._find_peaks(aroon_osc, prominence=10)
        osc_troughs = self._find_troughs(aroon_osc, prominence=10)
        price_peaks = self._find_peaks(price_recent)
        price_troughs = self._find_troughs(price_recent)
        
        # Bearish divergence: price higher highs, Aroon oscillator lower highs
        if len(osc_peaks) >= 2 and len(price_peaks) >= 2:
            latest_osc_peak = osc_peaks[-1]
            prev_osc_peak = osc_peaks[-2]
            latest_price_peak = price_peaks[-1]
            prev_price_peak = price_peaks[-2]
            
            if (latest_price_peak["value"] > prev_price_peak["value"] and 
                latest_osc_peak["value"] < prev_osc_peak["value"]):
                return {
                    "type": "bearish_divergence",
                    "confidence": 0.7,
                    "description": "Price making higher highs while Aroon oscillator making lower highs"
                }
        
        # Bullish divergence: price lower lows, Aroon oscillator higher lows
        if len(osc_troughs) >= 2 and len(price_troughs) >= 2:
            latest_osc_trough = osc_troughs[-1]
            prev_osc_trough = osc_troughs[-2]
            latest_price_trough = price_troughs[-1]
            prev_price_trough = price_troughs[-2]
            
            if (latest_price_trough["value"] < prev_price_trough["value"] and
                latest_osc_trough["value"] > prev_osc_trough["value"]):
                return {
                    "type": "bullish_divergence",
                    "confidence": 0.7,
                    "description": "Price making lower lows while Aroon oscillator making higher lows"
                }
        
        return None
    
    def _generate_aroon_signals(self, aroon_up: float, aroon_down: float, 
                               trend_analysis: Dict, crossover_analysis: Dict, 
                               strength_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate Aroon trading signals."""
        signals = []
        
        # Trend-based signals
        current_trend = trend_analysis["current_trend"]
        trend_quality = trend_analysis["trend_quality"]
        
        if "strong" in current_trend and trend_quality in ["excellent", "good"]:
            direction = "buy" if "up" in current_trend else "sell"
            signals.append({
                "type": f"trend_{direction}_signal",
                "strength": "strong",
                "reason": f"Strong Aroon {current_trend} with {trend_quality} quality",
                "confidence": 0.8
            })
        
        # Crossover signals
        latest_crossover = crossover_analysis.get("latest_crossover")
        if latest_crossover and latest_crossover["periods_ago"] <= 3:
            crossover_type = latest_crossover["type"]
            signal_type = "buy_signal" if "bullish" in crossover_type else "sell_signal"
            
            # Higher confidence for crossovers at extreme levels
            location = latest_crossover["location"]
            confidence = 0.8 if location in ["high_levels", "low_levels"] else 0.6
            
            signals.append({
                "type": signal_type,
                "strength": "medium",
                "reason": f"Recent Aroon {crossover_type} at {location}",
                "confidence": confidence
            })
        
        # Strength-based signals
        combined_strength = strength_analysis["combined_strength"]
        if combined_strength == "very_strong":
            dominant = strength_analysis["dominant_indicator"]
            direction = "buy" if dominant == "aroon_up" else "sell"
            
            signals.append({
                "type": f"strength_{direction}_signal",
                "strength": "medium",
                "reason": f"Very strong {dominant.replace('_', ' ')} reading",
                "confidence": 0.7
            })
        
        # Consolidation signals
        if aroon_up < 50 and aroon_down < 50:
            signals.append({
                "type": "consolidation_signal",
                "strength": "low",
                "reason": "Both Aroon indicators below 50, potential consolidation",
                "confidence": 0.6
            })
        
        return signals
    
    def _calculate_aroon_confidence(self, aroon_up: pd.Series, aroon_down: pd.Series,
                                   trend_analysis: Dict, strength_analysis: Dict) -> float:
        """Calculate Aroon analysis confidence."""
        confidence_factors = []
        
        # Data quantity factor
        data_factor = min(1.0, len(aroon_up) / 30)
        confidence_factors.append(data_factor)
        
        # Trend quality factor
        trend_quality = trend_analysis.get("trend_quality", "poor")
        quality_scores = {"excellent": 0.9, "good": 0.7, "fair": 0.5, "poor": 0.3}
        confidence_factors.append(quality_scores.get(trend_quality, 0.3))
        
        # Strength consistency factor
        combined_strength = strength_analysis.get("combined_strength", "weak")
        strength_scores = {"very_strong": 0.9, "strong": 0.7, "moderate": 0.5, "weak": 0.4, "very_weak": 0.3}
        confidence_factors.append(strength_scores.get(combined_strength, 0.3))
        
        # Trend consistency factor
        trend_consistency = trend_analysis.get("trend_consistency", 0.5)
        confidence_factors.append(trend_consistency)
        
        return round(np.mean(confidence_factors), 3)
    
    def _generate_aroon_summary(self, aroon_up: float, aroon_down: float,
                               trend_analysis: Dict, oscillator_analysis: Dict) -> str:
        """Generate human-readable Aroon summary."""
        summary = f"Aroon Up: {aroon_up:.1f}, Down: {aroon_down:.1f}"
        
        # Add trend information
        current_trend = trend_analysis["current_trend"]
        if current_trend != "sideways":
            duration = trend_analysis["trend_duration"]
            summary += f" - {current_trend} for {duration} periods"
        else:
            summary += " - sideways trend"
        
        # Add oscillator zone
        osc_zone = oscillator_analysis["zone"]
        if osc_zone != "neutral":
            summary += f" ({osc_zone.replace('_', ' ')})"
        
        return summary