"""
CCI (Commodity Channel Index) Preprocessor.

Advanced CCI preprocessing with overbought/oversold analysis, trend detection,
and momentum-based pattern recognition.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePreprocessor


class CCIPreprocessor(BasePreprocessor):
    """Advanced CCI preprocessor with professional-grade analysis."""
    
    def preprocess(self, cci: pd.Series, prices: pd.Series = None, 
                  length: int = 20, **kwargs) -> Dict[str, Any]:
        """
        Advanced CCI preprocessing with comprehensive analysis.
        
        CCI oscillates around zero, with values above +100 indicating overbought
        conditions and values below -100 indicating oversold conditions.
        
        Args:
            cci: CCI values
            prices: Price series for divergence analysis (optional)
            length: CCI calculation period
            
        Returns:
            Dictionary with comprehensive CCI analysis
        """
        if len(cci) < 5:
            return {"error": "Insufficient data for CCI analysis"}
        
        current_cci = float(cci.iloc[-1])
        
        # Zone analysis (+/-100 levels for CCI)
        zone_analysis = self._analyze_cci_zones(cci)
        
        # Momentum analysis
        momentum_analysis = self._analyze_cci_momentum(cci)
        
        # Zero line analysis
        zero_line_analysis = self._analyze_zero_line_behavior(cci)
        
        # Pattern analysis
        pattern_analysis = self._analyze_cci_patterns(cci)
        
        # Position rank analysis
        position_rank = self._calculate_position_rank(cci, lookback=20)
        
        # Divergence analysis
        divergence = None
        if prices is not None:
            divergence = self._detect_cci_divergence(cci, prices)
        
        # Signal generation
        signals = self._generate_cci_signals(current_cci, zone_analysis, momentum_analysis)
        
        # Confidence calculation
        confidence = self._calculate_cci_confidence(cci, zone_analysis, momentum_analysis)
        
        return {
            "indicator": "CCI",
            "current": {
                "value": round(current_cci, 2),
                "timestamp": datetime.now().isoformat()
            },
            "zones": zone_analysis,
            "momentum": momentum_analysis,
            "zero_line": zero_line_analysis,
            "patterns": pattern_analysis,
            "position_rank": {
                "percentile": round(position_rank, 1),
                "interpretation": self._interpret_position_rank(position_rank)
            },
            "divergence": divergence,
            "signals": signals,
            "confidence": confidence,
            "summary": self._generate_cci_summary(current_cci, zone_analysis, momentum_analysis)
        }
    
    def _analyze_cci_zones(self, cci: pd.Series) -> Dict[str, Any]:
        """Analyze CCI overbought/oversold zones."""
        current_cci = cci.iloc[-1]
        
        # CCI zones: +100 (overbought), -100 (oversold)
        if current_cci >= 100:
            current_zone = "overbought"
        elif current_cci <= -100:
            current_zone = "oversold"
        else:
            current_zone = "neutral"
        
        # Streak analysis
        ob_streak = self._calculate_zone_streak(cci, 100, "above")
        os_streak = self._calculate_zone_streak(cci, -100, "below")
        
        # Time percentage analysis
        total_periods = len(cci)
        ob_periods = sum(1 for v in cci if v >= 100)
        os_periods = sum(1 for v in cci if v <= -100)
        
        # Exit analysis
        ob_exit = self._analyze_zone_exits(cci, 100, "above")
        os_exit = self._analyze_zone_exits(cci, -100, "below")
        
        # Extreme readings analysis (beyond +/-200)
        extreme_high = current_cci >= 200
        extreme_low = current_cci <= -200
        
        return {
            "current_zone": current_zone,
            "overbought": {
                "level": 100,
                "status": "in_zone" if current_cci >= 100 else "below",
                "streak_length": ob_streak,
                "time_percentage": round((ob_periods / total_periods) * 100, 1),
                "exit_analysis": ob_exit,
                "extreme_reading": extreme_high
            },
            "oversold": {
                "level": -100,
                "status": "in_zone" if current_cci <= -100 else "above",
                "streak_length": os_streak,
                "time_percentage": round((os_periods / total_periods) * 100, 1),
                "exit_analysis": os_exit,
                "extreme_reading": extreme_low
            },
            "neutral_bias": "bullish" if current_cci > 0 else "bearish"
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
    
    def _analyze_cci_momentum(self, cci: pd.Series) -> Dict[str, Any]:
        """Analyze CCI momentum characteristics."""
        if len(cci) < 5:
            return {}
        
        velocity = self._calculate_velocity(cci, 3)
        acceleration = self._calculate_acceleration(cci, 6)
        
        # Volatility analysis
        volatility = cci.std()
        recent_range = cci.iloc[-10:].max() - cci.iloc[-10:].min()
        
        # Trend strength
        trend_direction = "bullish" if velocity > 0 else "bearish"
        trend_strength = min(1.0, abs(velocity) / 20)  # Normalize to 0-1
        
        return {
            "velocity": round(velocity, 2),
            "acceleration": round(acceleration, 2),
            "volatility": round(volatility, 2),
            "recent_range": round(recent_range, 2),
            "trend_direction": trend_direction,
            "trend_strength": round(trend_strength, 3),
            "momentum_interpretation": self._interpret_cci_momentum(velocity, acceleration)
        }
    
    def _interpret_cci_momentum(self, velocity: float, acceleration: float) -> str:
        """Interpret CCI momentum characteristics."""
        if velocity > 10 and acceleration > 0:
            return "strong_bullish_acceleration"
        elif velocity > 10:
            return "strong_bullish_momentum"
        elif velocity < -10 and acceleration < 0:
            return "strong_bearish_acceleration"
        elif velocity < -10:
            return "strong_bearish_momentum"
        elif abs(velocity) < 2:
            return "sideways_momentum"
        else:
            return f"{'bullish' if velocity > 0 else 'bearish'}_momentum"
    
    def _analyze_zero_line_behavior(self, cci: pd.Series) -> Dict[str, Any]:
        """Analyze CCI behavior around zero line."""
        current = cci.iloc[-1]
        
        # Time above/below zero
        above_zero = sum(1 for v in cci if v > 0)
        below_zero = sum(1 for v in cci if v < 0)
        total = len(cci)
        
        # Zero line crossings
        crossings = 0
        for i in range(1, len(cci)):
            if (cci.iloc[i] > 0 and cci.iloc[i-1] <= 0) or (cci.iloc[i] < 0 and cci.iloc[i-1] >= 0):
                crossings += 1
        
        return {
            "current_position": "above" if current > 0 else "below",
            "distance_from_zero": round(abs(current), 2),
            "time_above_zero_pct": round((above_zero / total) * 100, 1),
            "time_below_zero_pct": round((below_zero / total) * 100, 1),
            "zero_crossings": crossings
        }
    
    def _analyze_cci_patterns(self, cci: pd.Series) -> Dict[str, Any]:
        """Analyze CCI patterns and formations."""
        patterns = {}
        
        if len(cci) >= 15:
            # Hook pattern (CCI hooks back from extreme levels)
            hook_pattern = self._detect_cci_hooks(cci)
            if hook_pattern:
                patterns["hook"] = hook_pattern
            
            # 100/-100 rejection pattern
            rejection_pattern = self._detect_level_rejection(cci)
            if rejection_pattern:
                patterns["level_rejection"] = rejection_pattern
        
        return patterns
    
    def _detect_cci_hooks(self, cci: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect CCI hook patterns from extreme levels."""
        if len(cci) < 8:
            return None
        
        recent_values = cci.iloc[-8:]
        
        # Bullish hook: CCI drops below -100, then hooks back up
        if any(v <= -100 for v in recent_values.iloc[:-2]):
            min_idx = recent_values.argmin()
            if min_idx < len(recent_values) - 2:  # Not the last value
                min_val = recent_values.iloc[min_idx]
                current_val = recent_values.iloc[-1]
                
                if min_val <= -100 and current_val > min_val + 20:  # Significant hook up
                    return {
                        "type": "bullish_hook",
                        "confidence": 0.7,
                        "description": f"CCI hooked up from {min_val:.1f} oversold level"
                    }
        
        # Bearish hook: CCI rises above +100, then hooks back down
        if any(v >= 100 for v in recent_values.iloc[:-2]):
            max_idx = recent_values.argmax()
            if max_idx < len(recent_values) - 2:  # Not the last value
                max_val = recent_values.iloc[max_idx]
                current_val = recent_values.iloc[-1]
                
                if max_val >= 100 and current_val < max_val - 20:  # Significant hook down
                    return {
                        "type": "bearish_hook",
                        "confidence": 0.7,
                        "description": f"CCI hooked down from {max_val:.1f} overbought level"
                    }
        
        return None
    
    def _detect_level_rejection(self, cci: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect rejection at +100/-100 levels."""
        if len(cci) < 5:
            return None
        
        recent_values = cci.iloc[-5:]
        
        # Check for rejection at +100 level
        if any(95 <= v <= 105 for v in recent_values) and recent_values.iloc[-1] < 90:
            return {
                "type": "overbought_rejection",
                "confidence": 0.6,
                "description": "CCI rejected at +100 overbought level"
            }
        
        # Check for rejection at -100 level
        if any(-105 <= v <= -95 for v in recent_values) and recent_values.iloc[-1] > -90:
            return {
                "type": "oversold_rejection",
                "confidence": 0.6,
                "description": "CCI rejected at -100 oversold level"
            }
        
        return None
    
    def _detect_cci_divergence(self, cci: pd.Series, prices: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect CCI-price divergence patterns."""
        if len(cci) < 15 or len(prices) < 15:
            return None
        
        recent_periods = 10
        cci_recent = cci.iloc[-recent_periods:]
        price_recent = prices.iloc[-recent_periods:]
        
        # Find peaks and troughs
        cci_peaks = self._find_peaks(cci_recent, prominence=10)
        cci_troughs = self._find_troughs(cci_recent, prominence=10)
        price_peaks = self._find_peaks(price_recent)
        price_troughs = self._find_troughs(price_recent)
        
        # Bearish divergence: price higher highs, CCI lower highs
        if len(cci_peaks) >= 2 and len(price_peaks) >= 2:
            latest_cci_peak = cci_peaks[-1]
            prev_cci_peak = cci_peaks[-2]
            latest_price_peak = price_peaks[-1]
            prev_price_peak = price_peaks[-2]
            
            if (latest_price_peak["value"] > prev_price_peak["value"] and 
                latest_cci_peak["value"] < prev_cci_peak["value"]):
                return {
                    "type": "bearish_divergence",
                    "confidence": 0.7,
                    "description": "Price making higher highs while CCI making lower highs"
                }
        
        # Bullish divergence: price lower lows, CCI higher lows
        if len(cci_troughs) >= 2 and len(price_troughs) >= 2:
            latest_cci_trough = cci_troughs[-1]
            prev_cci_trough = cci_troughs[-2]
            latest_price_trough = price_troughs[-1]
            prev_price_trough = price_troughs[-2]
            
            if (latest_price_trough["value"] < prev_price_trough["value"] and
                latest_cci_trough["value"] > prev_cci_trough["value"]):
                return {
                    "type": "bullish_divergence",
                    "confidence": 0.7,
                    "description": "Price making lower lows while CCI making higher lows"
                }
        
        return None
    
    def _generate_cci_signals(self, cci_value: float, zone_analysis: Dict, momentum_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate CCI trading signals."""
        signals = []
        
        # Extreme zone signals
        if zone_analysis["overbought"]["extreme_reading"]:
            signals.append({
                "type": "strong_sell_signal",
                "strength": "strong",
                "reason": f"CCI at extreme overbought level {cci_value:.1f}",
                "confidence": 0.8
            })
        elif zone_analysis["oversold"]["extreme_reading"]:
            signals.append({
                "type": "strong_buy_signal",
                "strength": "strong", 
                "reason": f"CCI at extreme oversold level {cci_value:.1f}",
                "confidence": 0.8
            })
        
        # Regular zone signals with streak consideration
        elif zone_analysis["current_zone"] == "overbought":
            if zone_analysis["overbought"]["streak_length"] > 2:
                signals.append({
                    "type": "sell_signal",
                    "strength": "medium",
                    "reason": f"CCI overbought for {zone_analysis['overbought']['streak_length']} periods",
                    "confidence": 0.6
                })
        elif zone_analysis["current_zone"] == "oversold":
            if zone_analysis["oversold"]["streak_length"] > 2:
                signals.append({
                    "type": "buy_signal",
                    "strength": "medium",
                    "reason": f"CCI oversold for {zone_analysis['oversold']['streak_length']} periods", 
                    "confidence": 0.6
                })
        
        # Momentum-based signals
        if "trend_strength" in momentum_analysis and momentum_analysis["trend_strength"] > 0.7:
            if momentum_analysis["trend_direction"] == "bullish":
                signals.append({
                    "type": "momentum_buy",
                    "strength": "medium",
                    "reason": "Strong bullish CCI momentum",
                    "confidence": 0.6
                })
            else:
                signals.append({
                    "type": "momentum_sell", 
                    "strength": "medium",
                    "reason": "Strong bearish CCI momentum",
                    "confidence": 0.6
                })
        
        return signals
    
    def _calculate_cci_confidence(self, cci: pd.Series, zone_analysis: Dict, momentum_analysis: Dict) -> float:
        """Calculate CCI analysis confidence."""
        confidence_factors = []
        
        # Data quantity factor
        data_factor = min(1.0, len(cci) / 30)
        confidence_factors.append(data_factor)
        
        # Zone clarity factor
        current_cci = cci.iloc[-1]
        if abs(current_cci) >= 100:
            confidence_factors.append(0.8)  # High confidence in extreme zones
        else:
            confidence_factors.append(0.6)  # Medium confidence in neutral zone
        
        # Momentum consistency factor
        if "trend_strength" in momentum_analysis:
            confidence_factors.append(momentum_analysis["trend_strength"])
        
        # Volatility factor (lower volatility = higher confidence)
        if "volatility" in momentum_analysis:
            vol_factor = max(0.4, min(1.0, 1.0 - momentum_analysis["volatility"] / 200))
            confidence_factors.append(vol_factor)
        
        return round(np.mean(confidence_factors), 3)
    
    def _generate_cci_summary(self, cci_value: float, zone_analysis: Dict, momentum_analysis: Dict) -> str:
        """Generate human-readable CCI summary."""
        summary = f"CCI at {cci_value:.1f}"
        
        # Add zone information
        zone = zone_analysis["current_zone"]
        if zone != "neutral":
            streak = zone_analysis[zone]["streak_length"]
            if streak > 0:
                summary += f" ({zone} for {streak} periods)"
            else:
                summary += f" ({zone})"
        
        # Add extreme reading information
        if zone_analysis["overbought"]["extreme_reading"]:
            summary += " - EXTREME HIGH"
        elif zone_analysis["oversold"]["extreme_reading"]:
            summary += " - EXTREME LOW"
        
        # Add momentum information
        if "momentum_interpretation" in momentum_analysis:
            momentum = momentum_analysis["momentum_interpretation"]
            if "strong" in momentum:
                summary += f", {momentum.replace('_', ' ')}"
        
        return summary