"""
Williams %R Preprocessor.

Advanced Williams %R preprocessing with zone analysis, momentum tracking,
and pattern recognition for overbought/oversold conditions.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePreprocessor


class WilliamsRPreprocessor(BasePreprocessor):
    """Advanced Williams %R preprocessor with professional-grade analysis."""
    
    def preprocess(self, williams_r: pd.Series, prices: pd.Series = None, 
                  length: int = 14, **kwargs) -> Dict[str, Any]:
        """
        Advanced Williams %R preprocessing with comprehensive analysis.
        
        Williams %R oscillates between 0 and -100, where values closer to 0 
        indicate overbought conditions and values closer to -100 indicate oversold.
        
        Args:
            williams_r: Williams %R values
            prices: Price series for divergence analysis (optional)
            length: Williams %R calculation period
            
        Returns:
            Dictionary with comprehensive Williams %R analysis
        """
        if len(williams_r) < 5:
            return {"error": "Insufficient data for Williams %R analysis"}
        
        current_wr = float(williams_r.iloc[-1])
        
        # Zone analysis (-20/-80 levels for Williams %R)
        zone_analysis = self._analyze_wr_zones(williams_r)
        
        # Momentum analysis
        momentum_analysis = self._analyze_wr_momentum(williams_r)
        
        # Pattern analysis
        pattern_analysis = self._analyze_wr_patterns(williams_r)
        
        # Position rank analysis
        position_rank = self._calculate_position_rank(williams_r, lookback=20)
        
        # Divergence analysis
        divergence = None
        if prices is not None:
            divergence = self._detect_wr_divergence(williams_r, prices)
        
        # Signal generation
        signals = self._generate_wr_signals(current_wr, zone_analysis, momentum_analysis)
        
        # Confidence calculation
        confidence = self._calculate_wr_confidence(williams_r, zone_analysis, momentum_analysis)
        
        return {
            "indicator": "Williams_R",
            "current": {
                "value": round(current_wr, 2),
                "timestamp": datetime.now().isoformat()
            },
            "zones": zone_analysis,
            "momentum": momentum_analysis,
            "patterns": pattern_analysis,
            "position_rank": {
                "percentile": round(position_rank, 1),
                "interpretation": self._interpret_position_rank(position_rank)
            },
            "divergence": divergence,
            "signals": signals,
            "confidence": confidence,
            "summary": self._generate_wr_summary(current_wr, zone_analysis, momentum_analysis)
        }
    
    def _analyze_wr_zones(self, williams_r: pd.Series) -> Dict[str, Any]:
        """Analyze Williams %R overbought/oversold zones."""
        current_wr = williams_r.iloc[-1]
        
        # Williams %R zones: -20 (overbought), -80 (oversold)
        if current_wr >= -20:
            current_zone = "overbought"
        elif current_wr <= -80:
            current_zone = "oversold" 
        else:
            current_zone = "neutral"
        
        # Streak analysis
        ob_streak = self._calculate_zone_streak(williams_r, -20, "above")
        os_streak = self._calculate_zone_streak(williams_r, -80, "below")
        
        # Time percentage analysis
        total_periods = len(williams_r)
        ob_periods = sum(1 for v in williams_r if v >= -20)
        os_periods = sum(1 for v in williams_r if v <= -80)
        
        # Exit analysis
        ob_exit = self._analyze_zone_exits(williams_r, -20, "above")
        os_exit = self._analyze_zone_exits(williams_r, -80, "below")
        
        return {
            "current_zone": current_zone,
            "overbought": {
                "level": -20,
                "status": "in_zone" if current_wr >= -20 else "below",
                "streak_length": ob_streak,
                "time_percentage": round((ob_periods / total_periods) * 100, 1),
                "exit_analysis": ob_exit
            },
            "oversold": {
                "level": -80,
                "status": "in_zone" if current_wr <= -80 else "above",
                "streak_length": os_streak,
                "time_percentage": round((os_periods / total_periods) * 100, 1),
                "exit_analysis": os_exit
            },
            "neutral_bias": "bullish" if current_wr > -50 else "bearish"
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
        """Analyze recent exits from zones."""
        exits = []
        
        for i in range(1, min(10, len(values))):
            prev_val = values.iloc[-(i+1)]
            curr_val = values.iloc[-i]
            
            if direction == "above":
                if prev_val >= threshold and curr_val < threshold:
                    exits.append({
                        "periods_ago": i,
                        "exit_level": curr_val,
                        "strength": abs(curr_val - threshold)
                    })
            else:  # below
                if prev_val <= threshold and curr_val > threshold:
                    exits.append({
                        "periods_ago": i,
                        "exit_level": curr_val,
                        "strength": abs(curr_val - threshold)
                    })
        
        return {
            "recent_exits": exits[:3],
            "latest_exit": exits[0] if exits else None
        }
    
    def _analyze_wr_momentum(self, williams_r: pd.Series) -> Dict[str, Any]:
        """Analyze Williams %R momentum characteristics."""
        if len(williams_r) < 5:
            return {}
        
        velocity = self._calculate_velocity(williams_r, 3)
        acceleration = self._calculate_acceleration(williams_r, 6)
        
        # Mean reversion potential
        recent_range = williams_r.iloc[-10:].max() - williams_r.iloc[-10:].min()
        volatility = williams_r.std()
        
        return {
            "velocity": round(velocity, 2),
            "acceleration": round(acceleration, 2),
            "recent_range": round(recent_range, 2),
            "volatility": round(volatility, 2),
            "momentum_interpretation": self._interpret_wr_momentum(velocity, acceleration)
        }
    
    def _interpret_wr_momentum(self, velocity: float, acceleration: float) -> str:
        """Interpret Williams %R momentum characteristics."""
        if velocity > 5 and acceleration > 0:
            return "strong_upward_acceleration"
        elif velocity > 5:
            return "strong_upward_momentum"
        elif velocity < -5 and acceleration < 0:
            return "strong_downward_acceleration"
        elif velocity < -5:
            return "strong_downward_momentum"
        elif abs(velocity) < 1:
            return "sideways_momentum"
        else:
            return f"{'upward' if velocity > 0 else 'downward'}_momentum"
    
    def _analyze_wr_patterns(self, williams_r: pd.Series) -> Dict[str, Any]:
        """Analyze Williams %R patterns and formations."""
        patterns = {}
        
        if len(williams_r) >= 10:
            recent_values = williams_r.iloc[-10:]
            
            # Failure swing pattern (similar to RSI)
            failure_swing = self._detect_failure_swing(recent_values)
            if failure_swing:
                patterns["failure_swing"] = failure_swing
        
        return patterns
    
    def _detect_failure_swing(self, values: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect Williams %R failure swing patterns."""
        if len(values) < 8:
            return None
        
        # Look for bullish failure swing (double bottom above -80)
        recent_lows = []
        for i in range(1, len(values) - 1):
            if values.iloc[i] < values.iloc[i-1] and values.iloc[i] < values.iloc[i+1]:
                recent_lows.append({"index": i, "value": values.iloc[i]})
        
        if len(recent_lows) >= 2:
            last_low = recent_lows[-1]
            prev_low = recent_lows[-2]
            
            # Bullish failure swing: second low higher than first, both above -80
            if (last_low["value"] > prev_low["value"] and 
                last_low["value"] > -80 and prev_low["value"] > -80):
                return {
                    "type": "bullish_failure_swing",
                    "confidence": 0.7,
                    "description": "Double bottom above oversold level"
                }
        
        return None
    
    def _detect_wr_divergence(self, williams_r: pd.Series, prices: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect Williams %R-price divergence patterns."""
        if len(williams_r) < 15 or len(prices) < 15:
            return None
        
        recent_periods = 10
        wr_recent = williams_r.iloc[-recent_periods:]
        price_recent = prices.iloc[-recent_periods:]
        
        # Find peaks and troughs
        wr_peaks = self._find_peaks(wr_recent, prominence=5)
        wr_troughs = self._find_troughs(wr_recent, prominence=5)
        price_peaks = self._find_peaks(price_recent)
        price_troughs = self._find_troughs(price_recent)
        
        # Bearish divergence: price higher highs, Williams %R lower highs
        if len(wr_peaks) >= 2 and len(price_peaks) >= 2:
            latest_wr_peak = wr_peaks[-1]
            prev_wr_peak = wr_peaks[-2]
            latest_price_peak = price_peaks[-1]
            prev_price_peak = price_peaks[-2]
            
            if (latest_price_peak["value"] > prev_price_peak["value"] and 
                latest_wr_peak["value"] < prev_wr_peak["value"]):
                return {
                    "type": "bearish_divergence",
                    "confidence": 0.7,
                    "description": "Price making higher highs while Williams %R making lower highs"
                }
        
        # Bullish divergence: price lower lows, Williams %R higher lows
        if len(wr_troughs) >= 2 and len(price_troughs) >= 2:
            latest_wr_trough = wr_troughs[-1]
            prev_wr_trough = wr_troughs[-2]
            latest_price_trough = price_troughs[-1]
            prev_price_trough = price_troughs[-2]
            
            if (latest_price_trough["value"] < prev_price_trough["value"] and
                latest_wr_trough["value"] > prev_wr_trough["value"]):
                return {
                    "type": "bullish_divergence",
                    "confidence": 0.7,
                    "description": "Price making lower lows while Williams %R making higher lows"
                }
        
        return None
    
    def _generate_wr_signals(self, wr_value: float, zone_analysis: Dict, momentum_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate Williams %R trading signals."""
        signals = []
        
        # Overbought zone signals
        if zone_analysis["current_zone"] == "overbought":
            if zone_analysis["overbought"]["streak_length"] > 3:
                signals.append({
                    "type": "sell_signal",
                    "strength": "strong",
                    "reason": f"Williams %R in overbought zone for {zone_analysis['overbought']['streak_length']} periods",
                    "confidence": 0.8
                })
        
        # Oversold zone signals
        elif zone_analysis["current_zone"] == "oversold":
            if zone_analysis["oversold"]["streak_length"] > 3:
                signals.append({
                    "type": "buy_signal", 
                    "strength": "strong",
                    "reason": f"Williams %R in oversold zone for {zone_analysis['oversold']['streak_length']} periods",
                    "confidence": 0.8
                })
        
        # Exit signals from extreme zones
        ob_exit = zone_analysis["overbought"]["exit_analysis"]["latest_exit"]
        if ob_exit and ob_exit["periods_ago"] <= 2:
            signals.append({
                "type": "sell_weakening",
                "strength": "medium",
                "reason": f"Recent exit from overbought zone {ob_exit['periods_ago']} periods ago",
                "confidence": 0.6
            })
        
        os_exit = zone_analysis["oversold"]["exit_analysis"]["latest_exit"]
        if os_exit and os_exit["periods_ago"] <= 2:
            signals.append({
                "type": "buy_weakening",
                "strength": "medium", 
                "reason": f"Recent exit from oversold zone {os_exit['periods_ago']} periods ago",
                "confidence": 0.6
            })
        
        return signals
    
    def _calculate_wr_confidence(self, williams_r: pd.Series, zone_analysis: Dict, momentum_analysis: Dict) -> float:
        """Calculate Williams %R analysis confidence."""
        confidence_factors = []
        
        # Data quantity factor
        data_factor = min(1.0, len(williams_r) / 30)
        confidence_factors.append(data_factor)
        
        # Zone clarity factor
        current_wr = williams_r.iloc[-1]
        if current_wr >= -20 or current_wr <= -80:
            confidence_factors.append(0.8)  # High confidence in extreme zones
        else:
            confidence_factors.append(0.6)  # Medium confidence in neutral zone
        
        # Momentum consistency factor
        if "velocity" in momentum_analysis:
            velocity_strength = min(1.0, abs(momentum_analysis["velocity"]) / 10)
            confidence_factors.append(velocity_strength)
        
        return round(np.mean(confidence_factors), 3)
    
    def _generate_wr_summary(self, wr_value: float, zone_analysis: Dict, momentum_analysis: Dict) -> str:
        """Generate human-readable Williams %R summary."""
        summary = f"Williams %R at {wr_value:.1f}"
        
        # Add zone information
        zone = zone_analysis["current_zone"]
        if zone != "neutral":
            streak = zone_analysis[zone]["streak_length"] 
            if streak > 0:
                summary += f" ({zone} for {streak} periods)"
            else:
                summary += f" ({zone})"
        
        # Add momentum information
        if "momentum_interpretation" in momentum_analysis:
            momentum = momentum_analysis["momentum_interpretation"]
            if "strong" in momentum:
                summary += f", {momentum.replace('_', ' ')}"
        
        return summary