"""
RSI (Relative Strength Index) Preprocessor.

Advanced RSI preprocessing with sophisticated analysis including zone tracking,
pattern recognition, divergence detection, and professional signal generation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePreprocessor


class RSIPreprocessor(BasePreprocessor):
    """Advanced RSI preprocessor with professional-grade analysis."""
    
    def preprocess(self, rsi_values: pd.Series, prices: pd.Series = None, 
                  period: int = 14, **kwargs) -> Dict[str, Any]:
        """
        Advanced RSI preprocessing with sophisticated analysis.
        
        Replicates the 357-line JavaScript RSI preprocessor functionality.
        
        Args:
            rsi_values: RSI time series values
            prices: Price series for divergence analysis (optional)
            period: RSI calculation period
            
        Returns:
            Dictionary with comprehensive RSI analysis
        """
        if len(rsi_values) < 5:
            return {"error": "Insufficient data for RSI analysis"}
        
        current = float(rsi_values.iloc[-1])
        
        # Advanced trend analysis
        trend_analysis = self._analyze_trend(rsi_values)
        
        # Velocity and momentum
        velocity = self._calculate_velocity(rsi_values)
        acceleration = self._calculate_acceleration(rsi_values)
        
        # Zone analysis
        zone_analysis = self._analyze_zones(rsi_values, 70, 30)
        
        # Pattern recognition
        patterns = self._detect_rsi_patterns(rsi_values, prices)
        
        # Level analysis
        level_analysis = self._analyze_key_levels(rsi_values, [30, 50, 70])
        
        # Recent extremes
        extremes = self._find_recent_extremes(rsi_values)
        
        # Generate sophisticated summary
        summary = self._generate_rsi_summary(
            current, trend_analysis, extremes, zone_analysis, patterns
        )
        
        return {
            "indicator": "RSI",
            "period": period,
            "current": {
                "value": round(current, 2),
                "timestamp": datetime.now().isoformat()
            },
            "trend": {
                "direction": trend_analysis["direction"],
                "strength": round(trend_analysis["strength"], 3),
                "velocity": round(velocity, 3),
                "acceleration": round(acceleration, 3),
                "confidence": trend_analysis["confidence"]
            },
            "zones": {
                "current_zone": zone_analysis["current_zone"],
                "overbought": {
                    "level": 70,
                    "status": zone_analysis["overbought_status"],
                    "periods_in_zone": zone_analysis["periods_overbought"],
                    "time_percentage": zone_analysis["overbought_percentage"]
                },
                "oversold": {
                    "level": 30,
                    "status": zone_analysis["oversold_status"],
                    "periods_in_zone": zone_analysis["periods_oversold"],
                    "time_percentage": zone_analysis["oversold_percentage"]
                },
                "neutral": {
                    "distance_from_50": round(current - 50, 2),
                    "bias": "bullish" if current > 50 else "bearish"
                }
            },
            "extremes": {
                "recent_high": {
                    "value": round(extremes["high_value"], 2),
                    "periods_ago": extremes["high_periods_ago"],
                    "significance": extremes["high_significance"]
                },
                "recent_low": {
                    "value": round(extremes["low_value"], 2),
                    "periods_ago": extremes["low_periods_ago"],
                    "significance": extremes["low_significance"]
                }
            },
            "levels": level_analysis,
            "patterns": patterns,
            "signals": self._generate_rsi_signals(current, trend_analysis, zone_analysis, patterns),
            "summary": summary,
            "confidence": self._calculate_analysis_confidence(rsi_values, trend_analysis, patterns),
            "raw_values": rsi_values.dropna().tolist()
        }
    
    def _detect_rsi_patterns(self, rsi_values: pd.Series, prices: pd.Series = None) -> Dict[str, Any]:
        """Detect RSI patterns and formations."""
        patterns = {}
        
        # Reversal patterns
        reversal = self._detect_reversal_pattern(rsi_values)
        if reversal:
            patterns["reversal"] = reversal
        
        # Momentum patterns
        momentum = self._detect_momentum_pattern(rsi_values)
        if momentum:
            patterns["momentum"] = momentum
        
        # Divergence patterns (if prices provided)
        if prices is not None and len(prices) == len(rsi_values):
            divergence = self._detect_rsi_divergence(rsi_values, prices)
            if divergence:
                patterns["divergence"] = divergence
        
        return patterns
    
    def _detect_reversal_pattern(self, values: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect potential reversal patterns."""
        if len(values) < 5:
            return None
        
        recent = values.iloc[-5:].values
        current = recent[-1]
        
        # Look for double tops/bottoms in overbought/oversold zones
        if current > 70:  # Overbought zone
            peaks = []
            for i in range(1, len(recent) - 1):
                if recent[i] > recent[i-1] and recent[i] > recent[i+1]:
                    peaks.append((i, recent[i]))
            
            if len(peaks) >= 2:
                return {
                    "type": "double_top_reversal",
                    "confidence": 0.7,
                    "description": f"Potential bearish reversal pattern in overbought zone"
                }
        
        elif current < 30:  # Oversold zone
            troughs = []
            for i in range(1, len(recent) - 1):
                if recent[i] < recent[i-1] and recent[i] < recent[i+1]:
                    troughs.append((i, recent[i]))
            
            if len(troughs) >= 2:
                return {
                    "type": "double_bottom_reversal",
                    "confidence": 0.7,
                    "description": f"Potential bullish reversal pattern in oversold zone"
                }
        
        return None
    
    def _detect_momentum_pattern(self, values: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect momentum patterns."""
        if len(values) < 10:
            return None
        
        velocity = self._calculate_velocity(values)
        acceleration = self._calculate_acceleration(values)
        
        if abs(velocity) > 5:  # Strong momentum threshold
            return {
                "type": f"strong_{'bullish' if velocity > 0 else 'bearish'}_momentum",
                "velocity": round(velocity, 3),
                "acceleration": round(acceleration, 3),
                "confidence": min(1.0, abs(velocity) / 10),
                "description": f"Strong {'bullish' if velocity > 0 else 'bearish'} momentum detected"
            }
        
        return None
    
    def _detect_rsi_divergence(self, rsi_values: pd.Series, prices: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect RSI-price divergence."""
        if len(rsi_values) < 20 or len(prices) < 20:
            return None
        
        # Look at recent trends
        recent_periods = 10
        rsi_recent = rsi_values.iloc[-recent_periods:]
        price_recent = prices.iloc[-recent_periods:]
        
        # Calculate trend slopes
        rsi_slope = np.polyfit(range(len(rsi_recent)), rsi_recent.values, 1)[0]
        price_slope = np.polyfit(range(len(price_recent)), price_recent.values, 1)[0]
        
        # Check for divergence
        if rsi_slope > 0.5 and price_slope < -0.1:  # RSI rising, price falling
            return {
                "type": "bullish_divergence",
                "confidence": 0.6,
                "rsi_slope": round(rsi_slope, 3),
                "price_slope": round(price_slope, 6),
                "description": "RSI showing strength while price weakening - potential bullish divergence"
            }
        elif rsi_slope < -0.5 and price_slope > 0.1:  # RSI falling, price rising
            return {
                "type": "bearish_divergence", 
                "confidence": 0.6,
                "rsi_slope": round(rsi_slope, 3),
                "price_slope": round(price_slope, 6),
                "description": "RSI showing weakness while price rising - potential bearish divergence"
            }
        
        return None
    
    def _generate_rsi_signals(self, current: float, trend: Dict, zones: Dict, patterns: Dict) -> List[Dict[str, Any]]:
        """Generate actionable RSI signals."""
        signals = []
        
        # Overbought/Oversold signals
        if current > 70 and trend["direction"] == "falling":
            signals.append({
                "type": "sell_signal",
                "strength": "medium",
                "reason": "RSI overbought and turning down",
                "confidence": 0.7
            })
        
        if current < 30 and trend["direction"] == "rising":
            signals.append({
                "type": "buy_signal", 
                "strength": "medium",
                "reason": "RSI oversold and turning up",
                "confidence": 0.7
            })
        
        # Pattern-based signals
        if "reversal" in patterns:
            pattern = patterns["reversal"]
            signals.append({
                "type": "reversal_warning",
                "strength": "high" if pattern["confidence"] > 0.7 else "medium",
                "reason": pattern["description"],
                "confidence": pattern["confidence"]
            })
        
        return signals
    
    def _generate_rsi_summary(self, current: float, trend: Dict, extremes: Dict, 
                             zones: Dict, patterns: Dict) -> str:
        """Generate human-readable RSI summary."""
        summary = f"RSI at {current:.1f}"
        
        # Add trend info
        if trend["direction"] != "sideways":
            strength = "strongly" if trend["strength"] > 0.7 else ""
            summary += f", {trend['direction']} {strength}".strip()
        
        # Add recent extreme context
        if extremes["high_periods_ago"] <= 10:
            summary += f" (recent high: {extremes['high_value']:.1f} {extremes['high_periods_ago']}p ago)"
        
        # Add zone info
        if zones["current_zone"] != "neutral":
            if zones["periods_overbought"] > 0:
                summary += f". Overbought for {zones['periods_overbought']} periods"
            elif zones["periods_oversold"] > 0:
                summary += f". Oversold for {zones['periods_oversold']} periods"
        
        # Add pattern info
        if "momentum" in patterns:
            summary += f". {patterns['momentum']['description']}"
        
        return summary