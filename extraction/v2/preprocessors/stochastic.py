"""
Stochastic Oscillator Preprocessor.

Advanced Stochastic preprocessing with %K/%D analysis, crossover detection,
overbought/oversold zone tracking, and divergence pattern recognition.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePreprocessor


class StochasticPreprocessor(BasePreprocessor):
    """Advanced Stochastic preprocessor with professional-grade analysis."""
    
    def preprocess(self, k_percent: pd.Series, d_percent: pd.Series, 
                  prices: pd.Series = None, **kwargs) -> Dict[str, Any]:
        """
        Advanced Stochastic Oscillator preprocessing with professional analysis.
        
        Based on RESEARCH.md requirements:
        - %K, %D and their spread
        - Latest cross direction & bars since
        - Overbought/oversold streak length
        - Divergence flag with price
        - %K position rank within last N bars
        
        Args:
            k_percent: %K values (fast stochastic)
            d_percent: %D values (slow stochastic, signal line)
            prices: Price series for divergence analysis (optional)
            
        Returns:
            Dictionary with comprehensive Stochastic analysis
        """
        if len(k_percent) < 5 or len(d_percent) < 5:
            return {"error": "Insufficient data for Stochastic analysis"}
        
        current_k = float(k_percent.iloc[-1])
        current_d = float(d_percent.iloc[-1])
        spread = current_k - current_d
        
        # Cross analysis
        cross_analysis = self._analyze_stoch_crossovers(k_percent, d_percent)
        
        # Zone analysis (80/20 levels for Stochastic)
        zone_analysis = self._analyze_stoch_zones(k_percent, d_percent)
        
        # Position rank analysis
        position_rank = self._calculate_position_rank(k_percent, lookback=20)
        
        # Momentum analysis
        momentum_analysis = self._analyze_stoch_momentum(k_percent, d_percent)
        
        # Divergence analysis
        divergence = None
        if prices is not None:
            divergence = self._detect_stoch_divergence(k_percent, prices)
        
        # Signal generation
        signals = self._generate_stoch_signals(current_k, current_d, cross_analysis, zone_analysis)
        
        # Confidence calculation
        confidence = self._calculate_stoch_confidence(k_percent, d_percent, cross_analysis, zone_analysis)
        
        return {
            "indicator": "Stochastic",
            "current": {
                "k_percent": round(current_k, 2),
                "d_percent": round(current_d, 2), 
                "spread": round(spread, 2),
                "timestamp": datetime.now().isoformat()
            },
            "crossovers": cross_analysis,
            "zones": zone_analysis,
            "position_rank": {
                "k_percentile": round(position_rank, 1),
                "interpretation": self._interpret_position_rank(position_rank)
            },
            "momentum": momentum_analysis,
            "divergence": divergence,
            "signals": signals,
            "confidence": confidence,
            "summary": self._generate_stoch_summary(current_k, current_d, cross_analysis, zone_analysis, position_rank)
        }
    
    def _analyze_stoch_crossovers(self, k_percent: pd.Series, d_percent: pd.Series) -> Dict[str, Any]:
        """Analyze Stochastic crossovers (%K crossing %D)."""
        crossovers = []
        
        for i in range(1, min(15, len(k_percent))):
            prev_k = k_percent.iloc[-(i+1)]
            curr_k = k_percent.iloc[-i]
            prev_d = d_percent.iloc[-(i+1)]
            curr_d = d_percent.iloc[-i]
            
            # Bullish crossover (%K crosses above %D)
            if prev_k <= prev_d and curr_k > curr_d:
                crossovers.append({
                    "type": "bullish_crossover",
                    "periods_ago": i,
                    "strength": abs(curr_k - curr_d),
                    "location": self._get_stoch_zone(curr_k)
                })
            # Bearish crossover (%K crosses below %D)
            elif prev_k >= prev_d and curr_k < curr_d:
                crossovers.append({
                    "type": "bearish_crossover", 
                    "periods_ago": i,
                    "strength": abs(curr_k - curr_d),
                    "location": self._get_stoch_zone(curr_k)
                })
        
        return {
            "recent_crossovers": crossovers[:5],
            "latest_crossover": crossovers[0] if crossovers else None,
            "bars_since_cross": crossovers[0]["periods_ago"] if crossovers else None
        }
    
    def _analyze_stoch_zones(self, k_percent: pd.Series, d_percent: pd.Series) -> Dict[str, Any]:
        """Analyze Stochastic overbought/oversold zones (80/20 levels)."""
        current_k = k_percent.iloc[-1]
        
        # Current zone determination
        if current_k >= 80:
            current_zone = "overbought"
        elif current_k <= 20:
            current_zone = "oversold"
        else:
            current_zone = "neutral"
        
        # Streak analysis - consecutive periods in zone
        ob_streak = self._calculate_zone_streak(k_percent, 80, "above")
        os_streak = self._calculate_zone_streak(k_percent, 20, "below")
        
        # Time percentage analysis
        total_periods = len(k_percent)
        ob_periods = sum(1 for v in k_percent if v >= 80)
        os_periods = sum(1 for v in k_percent if v <= 20)
        
        # Exit analysis
        ob_exit = self._analyze_zone_exits(k_percent, 80, "above")
        os_exit = self._analyze_zone_exits(k_percent, 20, "below")
        
        return {
            "current_zone": current_zone,
            "overbought": {
                "level": 80,
                "status": "in_zone" if current_k >= 80 else "below",
                "streak_length": ob_streak,
                "time_percentage": round((ob_periods / total_periods) * 100, 1),
                "exit_analysis": ob_exit
            },
            "oversold": {
                "level": 20,
                "status": "in_zone" if current_k <= 20 else "above", 
                "streak_length": os_streak,
                "time_percentage": round((os_periods / total_periods) * 100, 1),
                "exit_analysis": os_exit
            },
            "neutral_bias": "bullish" if current_k > 50 else "bearish"
        }
    
    def _calculate_zone_streak(self, values: pd.Series, threshold: float, direction: str) -> int:
        """Calculate consecutive periods in a zone."""
        streak = 0
        for i in range(len(values) - 1, -1, -1):
            if direction == "above" and values.iloc[i] >= threshold:
                streak += 1
            elif direction == "below" and values.iloc[i] <= threshold:
                streak += 1
            else:
                break
        return streak
    
    def _analyze_zone_exits(self, values: pd.Series, threshold: float, direction: str) -> Dict[str, Any]:
        """Analyze recent exits from overbought/oversold zones."""
        exits = []
        
        for i in range(1, min(10, len(values))):
            prev_val = values.iloc[-(i+1)]
            curr_val = values.iloc[-i]
            
            if direction == "above":
                if prev_val >= threshold and curr_val < threshold:
                    exits.append({
                        "periods_ago": i,
                        "exit_level": curr_val,
                        "strength": threshold - curr_val
                    })
            else:  # below
                if prev_val <= threshold and curr_val > threshold:
                    exits.append({
                        "periods_ago": i,
                        "exit_level": curr_val,
                        "strength": curr_val - threshold
                    })
        
        return {
            "recent_exits": exits[:3],
            "latest_exit": exits[0] if exits else None
        }
    
    def _analyze_stoch_momentum(self, k_percent: pd.Series, d_percent: pd.Series) -> Dict[str, Any]:
        """Analyze Stochastic momentum characteristics."""
        if len(k_percent) < 5:
            return {}
        
        # %K velocity and acceleration
        k_velocity = self._calculate_velocity(k_percent, 3)
        k_acceleration = self._calculate_acceleration(k_percent, 6)
        
        # %D smoothing effect
        spread_current = k_percent.iloc[-1] - d_percent.iloc[-1]
        spread_previous = k_percent.iloc[-2] - d_percent.iloc[-2] if len(k_percent) > 1 else 0
        spread_momentum = spread_current - spread_previous
        
        return {
            "k_velocity": round(k_velocity, 2),
            "k_acceleration": round(k_acceleration, 2),
            "spread_momentum": round(spread_momentum, 2),
            "momentum_interpretation": self._interpret_stoch_momentum(k_velocity, k_acceleration)
        }
    
    def _interpret_stoch_momentum(self, velocity: float, acceleration: float) -> str:
        """Interpret Stochastic momentum characteristics."""
        if velocity > 5 and acceleration > 0:
            return "strong_bullish_acceleration"
        elif velocity > 5:
            return "strong_bullish_momentum"
        elif velocity < -5 and acceleration < 0:
            return "strong_bearish_acceleration"
        elif velocity < -5:
            return "strong_bearish_momentum"
        elif abs(velocity) < 1:
            return "sideways_momentum"
        else:
            return f"{'bullish' if velocity > 0 else 'bearish'}_momentum"
    
    def _detect_stoch_divergence(self, k_percent: pd.Series, prices: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect Stochastic-price divergence patterns."""
        if len(k_percent) < 15 or len(prices) < 15:
            return None
        
        # Analyze recent swing highs/lows
        recent_periods = 10
        k_recent = k_percent.iloc[-recent_periods:]
        price_recent = prices.iloc[-recent_periods:]
        
        # Find recent peaks and troughs
        k_peaks = self._find_peaks(k_recent, prominence=5)
        k_troughs = self._find_troughs(k_recent, prominence=5)
        price_peaks = self._find_peaks(price_recent)
        price_troughs = self._find_troughs(price_recent)
        
        # Check for divergence patterns
        if len(k_peaks) >= 2 and len(price_peaks) >= 2:
            # Bearish divergence: price making higher highs, Stochastic making lower highs
            latest_k_peak = k_peaks[-1]
            prev_k_peak = k_peaks[-2]
            latest_price_peak = price_peaks[-1] 
            prev_price_peak = price_peaks[-2]
            
            if (latest_price_peak["value"] > prev_price_peak["value"] and 
                latest_k_peak["value"] < prev_k_peak["value"]):
                return {
                    "type": "bearish_divergence",
                    "confidence": 0.7,
                    "description": "Price making higher highs while Stochastic making lower highs"
                }
        
        if len(k_troughs) >= 2 and len(price_troughs) >= 2:
            # Bullish divergence: price making lower lows, Stochastic making higher lows
            latest_k_trough = k_troughs[-1]
            prev_k_trough = k_troughs[-2]
            latest_price_trough = price_troughs[-1]
            prev_price_trough = price_troughs[-2]
            
            if (latest_price_trough["value"] < prev_price_trough["value"] and
                latest_k_trough["value"] > prev_k_trough["value"]):
                return {
                    "type": "bullish_divergence",
                    "confidence": 0.7,
                    "description": "Price making lower lows while Stochastic making higher lows"
                }
        
        return None
    
    def _get_stoch_zone(self, value: float) -> str:
        """Get Stochastic zone description."""
        if value >= 80:
            return "overbought"
        elif value <= 20:
            return "oversold"
        else:
            return "neutral"
    
    def _generate_stoch_signals(self, k_value: float, d_value: float, 
                               cross_analysis: Dict, zone_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate actionable Stochastic signals."""
        signals = []
        
        # Crossover signals
        latest_cross = cross_analysis.get("latest_crossover")
        if latest_cross and latest_cross["periods_ago"] <= 3:
            if latest_cross["type"] == "bullish_crossover":
                strength = "strong" if latest_cross["location"] == "oversold" else "medium"
                signals.append({
                    "type": "buy_signal",
                    "strength": strength,
                    "reason": f"Bullish %K/%D crossover in {latest_cross['location']} zone",
                    "confidence": 0.8 if strength == "strong" else 0.6
                })
            else:  # bearish crossover
                strength = "strong" if latest_cross["location"] == "overbought" else "medium"
                signals.append({
                    "type": "sell_signal",
                    "strength": strength,
                    "reason": f"Bearish %K/%D crossover in {latest_cross['location']} zone", 
                    "confidence": 0.8 if strength == "strong" else 0.6
                })
        
        return signals
    
    def _calculate_stoch_confidence(self, k_percent: pd.Series, d_percent: pd.Series,
                                   cross_analysis: Dict, zone_analysis: Dict) -> float:
        """Calculate Stochastic analysis confidence."""
        confidence_factors = []
        
        # Data quantity factor
        data_factor = min(1.0, len(k_percent) / 30)
        confidence_factors.append(data_factor)
        
        # Signal clarity factor
        latest_cross = cross_analysis.get("latest_crossover")
        if latest_cross:
            cross_strength = min(1.0, latest_cross["strength"] / 20)
            confidence_factors.append(cross_strength)
        
        # Zone consistency factor
        current_k = k_percent.iloc[-1]
        if current_k >= 80 or current_k <= 20:
            confidence_factors.append(0.8)  # High confidence in extreme zones
        else:
            confidence_factors.append(0.6)  # Medium confidence in neutral zone
        
        return round(np.mean(confidence_factors), 3)
    
    def _generate_stoch_summary(self, k_value: float, d_value: float, cross_analysis: Dict,
                               zone_analysis: Dict, position_rank: float) -> str:
        """Generate human-readable Stochastic summary."""
        summary = f"Stochastic %K: {k_value:.1f}, %D: {d_value:.1f}"
        
        # Add zone information
        zone = zone_analysis["current_zone"]
        if zone != "neutral":
            streak = zone_analysis[zone]["streak_length"]
            if streak > 0:
                summary += f" ({zone} for {streak} periods)"
            else:
                summary += f" ({zone})"
        
        # Add crossover information
        latest_cross = cross_analysis.get("latest_crossover")
        if latest_cross and latest_cross["periods_ago"] <= 5:
            summary += f". {latest_cross['type'].replace('_', ' ').title()} {latest_cross['periods_ago']}p ago"
        
        return summary