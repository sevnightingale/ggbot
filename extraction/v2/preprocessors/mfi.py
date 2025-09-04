"""
MFI (Money Flow Index) Preprocessor.

Advanced MFI preprocessing with volume-weighted momentum analysis, 
overbought/oversold detection, and money flow pattern recognition.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePreprocessor


class MFIPreprocessor(BasePreprocessor):
    """Advanced MFI preprocessor with professional-grade analysis."""
    
    def preprocess(self, mfi: pd.Series, prices: pd.Series = None, 
                  length: int = 14, **kwargs) -> Dict[str, Any]:
        """
        Advanced MFI preprocessing with comprehensive volume-weighted analysis.
        
        MFI oscillates between 0-100, incorporating volume in its calculation.
        Values above 80 indicate overbought, below 20 indicate oversold.
        
        Args:
            mfi: MFI values
            prices: Price series for divergence analysis (optional)
            length: MFI calculation period
            
        Returns:
            Dictionary with comprehensive MFI analysis
        """
        if len(mfi) < 5:
            return {"error": "Insufficient data for MFI analysis"}
        
        current_mfi = float(mfi.iloc[-1])
        
        # Zone analysis (80/20 levels for MFI)
        zone_analysis = self._analyze_mfi_zones(mfi)
        
        # Momentum analysis
        momentum_analysis = self._analyze_mfi_momentum(mfi)
        
        # Money flow analysis
        money_flow_analysis = self._analyze_money_flow_characteristics(mfi)
        
        # Pattern analysis
        pattern_analysis = self._analyze_mfi_patterns(mfi)
        
        # Position rank analysis
        position_rank = self._calculate_position_rank(mfi, lookback=20)
        
        # Divergence analysis
        divergence = None
        if prices is not None:
            divergence = self._detect_mfi_divergence(mfi, prices)
        
        # Signal generation
        signals = self._generate_mfi_signals(current_mfi, zone_analysis, momentum_analysis, money_flow_analysis)
        
        # Confidence calculation
        confidence = self._calculate_mfi_confidence(mfi, zone_analysis, momentum_analysis)
        
        return {
            "indicator": "MFI",
            "current": {
                "value": round(current_mfi, 2),
                "timestamp": datetime.now().isoformat()
            },
            "zones": zone_analysis,
            "momentum": momentum_analysis,
            "money_flow": money_flow_analysis,
            "patterns": pattern_analysis,
            "position_rank": {
                "percentile": round(position_rank, 1),
                "interpretation": self._interpret_position_rank(position_rank)
            },
            "divergence": divergence,
            "signals": signals,
            "confidence": confidence,
            "summary": self._generate_mfi_summary(current_mfi, zone_analysis, momentum_analysis, money_flow_analysis)
        }
    
    def _analyze_mfi_zones(self, mfi: pd.Series) -> Dict[str, Any]:
        """Analyze MFI overbought/oversold zones."""
        current_mfi = mfi.iloc[-1]
        
        # MFI zones: 80 (overbought), 20 (oversold)
        if current_mfi >= 80:
            current_zone = "overbought"
        elif current_mfi <= 20:
            current_zone = "oversold"
        else:
            current_zone = "neutral"
        
        # Streak analysis
        ob_streak = self._calculate_zone_streak(mfi, 80, "above")
        os_streak = self._calculate_zone_streak(mfi, 20, "below")
        
        # Time percentage analysis
        total_periods = len(mfi)
        ob_periods = sum(1 for v in mfi if v >= 80)
        os_periods = sum(1 for v in mfi if v <= 20)
        
        # Exit analysis
        ob_exit = self._analyze_zone_exits(mfi, 80, "above")
        os_exit = self._analyze_zone_exits(mfi, 20, "below")
        
        # Extreme readings (beyond 90/10)
        extreme_high = current_mfi >= 90
        extreme_low = current_mfi <= 10
        
        return {
            "current_zone": current_zone,
            "overbought": {
                "level": 80,
                "status": "in_zone" if current_mfi >= 80 else "below",
                "streak_length": ob_streak,
                "time_percentage": round((ob_periods / total_periods) * 100, 1),
                "exit_analysis": ob_exit,
                "extreme_reading": extreme_high
            },
            "oversold": {
                "level": 20,
                "status": "in_zone" if current_mfi <= 20 else "above",
                "streak_length": os_streak,
                "time_percentage": round((os_periods / total_periods) * 100, 1),
                "exit_analysis": os_exit,
                "extreme_reading": extreme_low
            },
            "neutral_bias": "bullish" if current_mfi > 50 else "bearish"
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
    
    def _analyze_mfi_momentum(self, mfi: pd.Series) -> Dict[str, Any]:
        """Analyze MFI momentum characteristics."""
        if len(mfi) < 5:
            return {}
        
        velocity = self._calculate_velocity(mfi, 3)
        acceleration = self._calculate_acceleration(mfi, 6)
        
        # Smoothness analysis (MFI should be smoother than RSI due to volume weighting)
        volatility = mfi.std()
        recent_range = mfi.iloc[-10:].max() - mfi.iloc[-10:].min()
        
        # Momentum strength
        momentum_strength = min(1.0, abs(velocity) / 10)
        
        return {
            "velocity": round(velocity, 2),
            "acceleration": round(acceleration, 2),
            "volatility": round(volatility, 2),
            "recent_range": round(recent_range, 2),
            "momentum_strength": round(momentum_strength, 3),
            "momentum_interpretation": self._interpret_mfi_momentum(velocity, acceleration)
        }
    
    def _interpret_mfi_momentum(self, velocity: float, acceleration: float) -> str:
        """Interpret MFI momentum characteristics."""
        if velocity > 5 and acceleration > 0:
            return "strong_money_inflow_acceleration"
        elif velocity > 5:
            return "strong_money_inflow"
        elif velocity < -5 and acceleration < 0:
            return "strong_money_outflow_acceleration"
        elif velocity < -5:
            return "strong_money_outflow"
        elif abs(velocity) < 1:
            return "balanced_money_flow"
        else:
            return f"{'money_inflow' if velocity > 0 else 'money_outflow'}_momentum"
    
    def _analyze_money_flow_characteristics(self, mfi: pd.Series) -> Dict[str, Any]:
        """Analyze specific money flow characteristics."""
        if len(mfi) < 10:
            return {}
        
        current_mfi = mfi.iloc[-1]
        
        # Money flow pressure analysis
        pressure = "buying" if current_mfi > 50 else "selling"
        pressure_strength = abs(current_mfi - 50) / 50  # 0-1 scale
        
        # Consistency analysis (how consistently money flows in one direction)
        recent_values = mfi.iloc[-5:]
        consistency = self._calculate_flow_consistency(recent_values)
        
        # Volume-price relationship strength
        # Higher MFI values suggest strong volume backing price moves
        volume_confirmation = "strong" if current_mfi > 60 or current_mfi < 40 else "weak"
        
        # Money flow cycles
        cycle_analysis = self._analyze_money_flow_cycles(mfi)
        
        return {
            "pressure": pressure,
            "pressure_strength": round(pressure_strength, 3),
            "consistency": round(consistency, 3),
            "volume_confirmation": volume_confirmation,
            "cycle_analysis": cycle_analysis,
            "flow_quality": self._assess_flow_quality(current_mfi, pressure_strength, consistency)
        }
    
    def _calculate_flow_consistency(self, values: pd.Series) -> float:
        """Calculate consistency of money flow direction."""
        if len(values) < 3:
            return 0.5
        
        changes = values.diff().dropna()
        if len(changes) == 0:
            return 0.5
        
        # Count directional consistency
        positive_changes = sum(1 for x in changes if x > 0)
        negative_changes = sum(1 for x in changes if x < 0)
        total_changes = len(changes)
        
        # Return consistency ratio (0.5 = neutral, 1.0 = all same direction)
        if total_changes == 0:
            return 0.5
        
        max_directional = max(positive_changes, negative_changes)
        return max_directional / total_changes
    
    def _analyze_money_flow_cycles(self, mfi: pd.Series) -> Dict[str, Any]:
        """Analyze money flow cycles and patterns."""
        if len(mfi) < 15:
            return {"cycle_detected": False}
        
        # Look for cyclical patterns in money flow
        recent_values = mfi.iloc[-15:]
        
        # Find peaks and troughs
        peaks = self._find_peaks(recent_values, prominence=5)
        troughs = self._find_troughs(recent_values, prominence=5)
        
        cycle_detected = len(peaks) >= 2 or len(troughs) >= 2
        
        if cycle_detected:
            # Calculate average cycle length
            if len(peaks) >= 2:
                peak_distances = [peaks[i]["index"] - peaks[i-1]["index"] for i in range(1, len(peaks))]
                avg_cycle = np.mean(peak_distances) if peak_distances else None
            elif len(troughs) >= 2:
                trough_distances = [troughs[i]["index"] - troughs[i-1]["index"] for i in range(1, len(troughs))]
                avg_cycle = np.mean(trough_distances) if trough_distances else None
            else:
                avg_cycle = None
            
            return {
                "cycle_detected": True,
                "avg_cycle_length": round(avg_cycle, 1) if avg_cycle else None,
                "recent_peaks": len(peaks),
                "recent_troughs": len(troughs)
            }
        
        return {"cycle_detected": False}
    
    def _assess_flow_quality(self, current_mfi: float, pressure_strength: float, consistency: float) -> str:
        """Assess overall money flow quality."""
        if pressure_strength > 0.6 and consistency > 0.7:
            return "high_quality_flow"
        elif pressure_strength > 0.4 and consistency > 0.6:
            return "medium_quality_flow"
        else:
            return "low_quality_flow"
    
    def _analyze_mfi_patterns(self, mfi: pd.Series) -> Dict[str, Any]:
        """Analyze MFI patterns and formations."""
        patterns = {}
        
        if len(mfi) >= 15:
            # Double top/bottom patterns
            double_pattern = self._detect_double_patterns(mfi)
            if double_pattern:
                patterns["double_pattern"] = double_pattern
            
            # Money flow exhaustion pattern
            exhaustion_pattern = self._detect_money_flow_exhaustion(mfi)
            if exhaustion_pattern:
                patterns["exhaustion"] = exhaustion_pattern
        
        return patterns
    
    def _detect_double_patterns(self, mfi: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect double top/bottom patterns in MFI."""
        if len(mfi) < 12:
            return None
        
        recent_values = mfi.iloc[-12:]
        peaks = self._find_peaks(recent_values, prominence=5)
        troughs = self._find_troughs(recent_values, prominence=5)
        
        # Double top pattern
        if len(peaks) >= 2:
            last_peak = peaks[-1]
            prev_peak = peaks[-2]
            
            # Check if peaks are roughly equal and in overbought territory
            if (abs(last_peak["value"] - prev_peak["value"]) < 5 and 
                last_peak["value"] > 70 and prev_peak["value"] > 70):
                return {
                    "type": "double_top",
                    "confidence": 0.7,
                    "description": f"Double top at MFI {last_peak['value']:.1f} level"
                }
        
        # Double bottom pattern
        if len(troughs) >= 2:
            last_trough = troughs[-1]
            prev_trough = troughs[-2]
            
            # Check if troughs are roughly equal and in oversold territory
            if (abs(last_trough["value"] - prev_trough["value"]) < 5 and 
                last_trough["value"] < 30 and prev_trough["value"] < 30):
                return {
                    "type": "double_bottom",
                    "confidence": 0.7,
                    "description": f"Double bottom at MFI {last_trough['value']:.1f} level"
                }
        
        return None
    
    def _detect_money_flow_exhaustion(self, mfi: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect money flow exhaustion patterns."""
        if len(mfi) < 8:
            return None
        
        recent_values = mfi.iloc[-8:]
        current_mfi = mfi.iloc[-1]
        
        # Bullish exhaustion: prolonged high MFI starting to decline
        if current_mfi > 80:
            high_periods = sum(1 for v in recent_values if v > 80)
            if high_periods >= 4:
                # Check if showing signs of decline
                velocity = self._calculate_velocity(recent_values.iloc[-3:], 2)
                if velocity < -2:
                    return {
                        "type": "bullish_exhaustion",
                        "confidence": 0.6,
                        "description": f"Money flow exhaustion after {high_periods} periods above 80"
                    }
        
        # Bearish exhaustion: prolonged low MFI starting to rise
        elif current_mfi < 20:
            low_periods = sum(1 for v in recent_values if v < 20)
            if low_periods >= 4:
                # Check if showing signs of recovery
                velocity = self._calculate_velocity(recent_values.iloc[-3:], 2)
                if velocity > 2:
                    return {
                        "type": "bearish_exhaustion",
                        "confidence": 0.6,
                        "description": f"Money flow exhaustion after {low_periods} periods below 20"
                    }
        
        return None
    
    def _detect_mfi_divergence(self, mfi: pd.Series, prices: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect MFI-price divergence patterns."""
        if len(mfi) < 15 or len(prices) < 15:
            return None
        
        recent_periods = 10
        mfi_recent = mfi.iloc[-recent_periods:]
        price_recent = prices.iloc[-recent_periods:]
        
        # Find peaks and troughs
        mfi_peaks = self._find_peaks(mfi_recent, prominence=5)
        mfi_troughs = self._find_troughs(mfi_recent, prominence=5)
        price_peaks = self._find_peaks(price_recent)
        price_troughs = self._find_troughs(price_recent)
        
        # Bearish divergence: price higher highs, MFI lower highs
        if len(mfi_peaks) >= 2 and len(price_peaks) >= 2:
            latest_mfi_peak = mfi_peaks[-1]
            prev_mfi_peak = mfi_peaks[-2]
            latest_price_peak = price_peaks[-1]
            prev_price_peak = price_peaks[-2]
            
            if (latest_price_peak["value"] > prev_price_peak["value"] and 
                latest_mfi_peak["value"] < prev_mfi_peak["value"]):
                return {
                    "type": "bearish_divergence",
                    "confidence": 0.75,  # Higher confidence than RSI due to volume component
                    "description": "Price making higher highs while money flow weakening"
                }
        
        # Bullish divergence: price lower lows, MFI higher lows
        if len(mfi_troughs) >= 2 and len(price_troughs) >= 2:
            latest_mfi_trough = mfi_troughs[-1]
            prev_mfi_trough = mfi_troughs[-2]
            latest_price_trough = price_troughs[-1]
            prev_price_trough = price_troughs[-2]
            
            if (latest_price_trough["value"] < prev_price_trough["value"] and
                latest_mfi_trough["value"] > prev_mfi_trough["value"]):
                return {
                    "type": "bullish_divergence",
                    "confidence": 0.75,  # Higher confidence than RSI due to volume component
                    "description": "Price making lower lows while money flow strengthening"
                }
        
        return None
    
    def _generate_mfi_signals(self, mfi_value: float, zone_analysis: Dict, 
                             momentum_analysis: Dict, money_flow_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate MFI trading signals."""
        signals = []
        
        # Extreme zone signals
        if zone_analysis["overbought"]["extreme_reading"]:
            signals.append({
                "type": "strong_sell_signal",
                "strength": "strong",
                "reason": f"MFI at extreme overbought level {mfi_value:.1f} with volume confirmation",
                "confidence": 0.85
            })
        elif zone_analysis["oversold"]["extreme_reading"]:
            signals.append({
                "type": "strong_buy_signal",
                "strength": "strong",
                "reason": f"MFI at extreme oversold level {mfi_value:.1f} with volume confirmation",
                "confidence": 0.85
            })
        
        # Money flow quality signals
        if money_flow_analysis.get("flow_quality") == "high_quality_flow":
            flow_type = money_flow_analysis["pressure"]
            signals.append({
                "type": f"{flow_type}_pressure_signal",
                "strength": "medium",
                "reason": f"High quality {flow_type} pressure with volume confirmation",
                "confidence": 0.7
            })
        
        # Zone exit signals
        ob_exit = zone_analysis["overbought"]["exit_analysis"]["latest_exit"]
        if ob_exit and ob_exit["periods_ago"] <= 2:
            signals.append({
                "type": "overbought_exit",
                "strength": "medium",
                "reason": f"Money flow exited overbought zone {ob_exit['periods_ago']} periods ago",
                "confidence": 0.65
            })
        
        os_exit = zone_analysis["oversold"]["exit_analysis"]["latest_exit"]
        if os_exit and os_exit["periods_ago"] <= 2:
            signals.append({
                "type": "oversold_exit",
                "strength": "medium",
                "reason": f"Money flow exited oversold zone {os_exit['periods_ago']} periods ago",
                "confidence": 0.65
            })
        
        return signals
    
    def _calculate_mfi_confidence(self, mfi: pd.Series, zone_analysis: Dict, momentum_analysis: Dict) -> float:
        """Calculate MFI analysis confidence."""
        confidence_factors = []
        
        # Data quantity factor
        data_factor = min(1.0, len(mfi) / 30)
        confidence_factors.append(data_factor)
        
        # Zone clarity factor (MFI zones are more reliable due to volume weighting)
        current_mfi = mfi.iloc[-1]
        if current_mfi >= 80 or current_mfi <= 20:
            confidence_factors.append(0.85)  # Higher than RSI due to volume
        else:
            confidence_factors.append(0.65)
        
        # Momentum consistency factor
        if "momentum_strength" in momentum_analysis:
            confidence_factors.append(momentum_analysis["momentum_strength"])
        
        # Volume confirmation factor (MFI inherently includes volume)
        confidence_factors.append(0.8)  # Higher base confidence due to volume weighting
        
        return round(np.mean(confidence_factors), 3)
    
    def _generate_mfi_summary(self, mfi_value: float, zone_analysis: Dict, 
                             momentum_analysis: Dict, money_flow_analysis: Dict) -> str:
        """Generate human-readable MFI summary."""
        summary = f"MFI at {mfi_value:.1f}"
        
        # Add zone information
        zone = zone_analysis["current_zone"]
        if zone != "neutral":
            streak = zone_analysis[zone]["streak_length"]
            if streak > 0:
                summary += f" ({zone} for {streak} periods)"
            else:
                summary += f" ({zone})"
        
        # Add money flow pressure
        pressure = money_flow_analysis.get("pressure", "balanced")
        if pressure != "balanced":
            summary += f", {pressure} pressure"
        
        # Add flow quality
        flow_quality = money_flow_analysis.get("flow_quality", "")
        if "high_quality" in flow_quality:
            summary += " - HIGH QUALITY FLOW"
        
        return summary