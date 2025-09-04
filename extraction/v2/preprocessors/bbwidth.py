"""
Bollinger Band Width Preprocessor.

Advanced Bollinger Band Width preprocessing with volatility analysis,
squeeze detection, and expansion/contraction cycle tracking.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePreprocessor


class BollingerWidthPreprocessor(BasePreprocessor):
    """Advanced Bollinger Band Width preprocessor with volatility cycle analysis."""
    
    def preprocess(self, bb_width: pd.Series, prices: pd.Series = None, 
                  **kwargs) -> Dict[str, Any]:
        """
        Advanced Bollinger Band Width preprocessing with volatility analysis.
        
        BB Width = (Upper Band - Lower Band) / Middle Band * 100
        It measures volatility and helps identify squeeze/expansion cycles.
        
        Args:
            bb_width: Bollinger Band Width values
            prices: Price series for additional analysis (optional)
            
        Returns:
            Dictionary with comprehensive BB Width analysis
        """
        if len(bb_width) < 5:
            return {"error": "Insufficient data for Bollinger Band Width analysis"}
        
        current_width = float(bb_width.iloc[-1])
        
        # Volatility level analysis
        volatility_analysis = self._analyze_volatility_levels(bb_width)
        
        # Squeeze analysis
        squeeze_analysis = self._analyze_squeeze_conditions(bb_width)
        
        # Expansion analysis
        expansion_analysis = self._analyze_expansion_cycles(bb_width)
        
        # Trend analysis
        trend_analysis = self._analyze_bb_width_trend(bb_width)
        
        # Cycle analysis
        cycle_analysis = self._analyze_volatility_cycles(bb_width)
        
        # Breakout potential
        breakout_analysis = self._analyze_breakout_potential(bb_width)
        
        # Signal generation
        signals = self._generate_bb_width_signals(current_width, volatility_analysis, 
                                                squeeze_analysis, expansion_analysis)
        
        # Confidence calculation
        confidence = self._calculate_bb_width_confidence(bb_width, volatility_analysis, cycle_analysis)
        
        return {
            "indicator": "Bollinger_Width",
            "current": {
                "width": round(current_width, 2),
                "timestamp": datetime.now().isoformat()
            },
            "volatility": volatility_analysis,
            "squeeze": squeeze_analysis,
            "expansion": expansion_analysis,
            "trend": trend_analysis,
            "cycles": cycle_analysis,
            "breakout": breakout_analysis,
            "signals": signals,
            "confidence": confidence,
            "summary": self._generate_bb_width_summary(current_width, volatility_analysis, squeeze_analysis)
        }
    
    def _analyze_volatility_levels(self, bb_width: pd.Series) -> Dict[str, Any]:
        """Analyze current volatility level."""
        current_width = bb_width.iloc[-1]
        
        # Statistical analysis
        mean_width = bb_width.mean()
        std_width = bb_width.std()
        max_width = bb_width.max()
        min_width = bb_width.min()
        
        # Percentile ranking
        percentile_rank = self._calculate_position_rank(bb_width, lookback=len(bb_width))
        
        # Volatility level classification
        if current_width > mean_width + 2 * std_width:
            volatility_level = "extremely_high"
        elif current_width > mean_width + std_width:
            volatility_level = "high"
        elif current_width > mean_width:
            volatility_level = "above_average"
        elif current_width > mean_width - std_width:
            volatility_level = "below_average"
        else:
            volatility_level = "low"
        
        return {
            "level": volatility_level,
            "percentile_rank": round(percentile_rank, 1),
            "relative_to_mean": round((current_width / mean_width - 1) * 100, 2),
            "statistics": {
                "mean": round(mean_width, 2),
                "std": round(std_width, 2),
                "max": round(max_width, 2),
                "min": round(min_width, 2)
            }
        }
    
    def _analyze_squeeze_conditions(self, bb_width: pd.Series) -> Dict[str, Any]:
        """Analyze Bollinger Band squeeze conditions."""
        current_width = bb_width.iloc[-1]
        
        # Dynamic squeeze threshold (typically 20-period low)
        if len(bb_width) >= 20:
            squeeze_threshold = bb_width.rolling(20).min().iloc[-1]
        else:
            # Fallback to statistical method
            mean_width = bb_width.mean()
            std_width = bb_width.std()
            squeeze_threshold = mean_width - std_width
        
        # Squeeze detection
        is_squeeze = current_width <= squeeze_threshold * 1.05  # 5% tolerance
        
        # Squeeze duration
        squeeze_periods = 0
        if is_squeeze:
            for i in range(len(bb_width) - 1, -1, -1):
                if bb_width.iloc[i] <= squeeze_threshold * 1.05:
                    squeeze_periods += 1
                else:
                    break
        
        # Historical squeeze analysis
        total_squeeze_periods = sum(1 for width in bb_width if width <= squeeze_threshold * 1.05)
        squeeze_frequency = total_squeeze_periods / len(bb_width)
        
        return {
            "is_squeeze": is_squeeze,
            "squeeze_periods": squeeze_periods,
            "squeeze_threshold": round(squeeze_threshold, 2),
            "squeeze_intensity": round((squeeze_threshold - current_width) / squeeze_threshold * 100, 2) if is_squeeze else 0,
            "squeeze_frequency": round(squeeze_frequency, 3),
            "squeeze_quality": self._assess_squeeze_quality(squeeze_periods, current_width, squeeze_threshold)
        }
    
    def _assess_squeeze_quality(self, periods: int, current_width: float, threshold: float) -> str:
        """Assess quality of squeeze for breakout potential."""
        if periods >= 10 and current_width < threshold * 0.8:
            return "excellent"
        elif periods >= 6 and current_width < threshold * 0.9:
            return "good"
        elif periods >= 3:
            return "moderate"
        else:
            return "weak"
    
    def _analyze_expansion_cycles(self, bb_width: pd.Series) -> Dict[str, Any]:
        """Analyze volatility expansion cycles."""
        if len(bb_width) < 10:
            return {}
        
        # Find expansion peaks (volatility highs)
        peaks = self._find_peaks(bb_width, prominence=bb_width.std() * 0.5)
        
        # Find contraction troughs (volatility lows)  
        troughs = self._find_troughs(bb_width, prominence=bb_width.std() * 0.5)
        
        # Current cycle position
        current_width = bb_width.iloc[-1]
        recent_peak = peaks[-1] if peaks else None
        recent_trough = troughs[-1] if troughs else None
        
        if recent_peak and recent_trough:
            if recent_peak["index"] > recent_trough["index"]:
                cycle_position = "post_expansion"
                cycle_stage = "contracting"
            else:
                cycle_position = "post_contraction"
                cycle_stage = "expanding"
        else:
            cycle_position = "unclear"
            cycle_stage = "unclear"
        
        # Expansion statistics
        if peaks:
            avg_expansion_height = np.mean([p["value"] for p in peaks])
            max_expansion = max([p["value"] for p in peaks])
        else:
            avg_expansion_height = max_expansion = current_width
        
        return {
            "cycle_position": cycle_position,
            "cycle_stage": cycle_stage,
            "expansion_peaks": len(peaks),
            "contraction_troughs": len(troughs),
            "avg_expansion_height": round(avg_expansion_height, 2),
            "max_expansion": round(max_expansion, 2),
            "recent_peak": recent_peak,
            "recent_trough": recent_trough
        }
    
    def _analyze_bb_width_trend(self, bb_width: pd.Series) -> Dict[str, Any]:
        """Analyze BB Width trend characteristics."""
        if len(bb_width) < 5:
            return {}
        
        # Width trend
        velocity = self._calculate_velocity(bb_width, 3)
        acceleration = self._calculate_acceleration(bb_width, 5)
        
        if velocity > 0.5:
            trend_direction = "expanding"
        elif velocity < -0.5:
            trend_direction = "contracting"
        else:
            trend_direction = "stable"
        
        # Trend strength
        trend_strength = min(1.0, abs(velocity) / bb_width.std()) if bb_width.std() > 0 else 0
        
        return {
            "direction": trend_direction,
            "velocity": round(velocity, 3),
            "acceleration": round(acceleration, 3),
            "strength": round(trend_strength, 3)
        }
    
    def _analyze_volatility_cycles(self, bb_width: pd.Series) -> Dict[str, Any]:
        """Analyze complete volatility cycles."""
        if len(bb_width) < 20:
            return {"insufficient_data": True}
        
        # Find complete cycles (trough to trough or peak to peak)
        peaks = self._find_peaks(bb_width, prominence=bb_width.std() * 0.3)
        troughs = self._find_troughs(bb_width, prominence=bb_width.std() * 0.3)
        
        # Calculate cycle lengths
        if len(troughs) >= 2:
            trough_cycles = [troughs[i]["index"] - troughs[i-1]["index"] 
                           for i in range(1, len(troughs))]
            avg_cycle_length = np.mean(trough_cycles) if trough_cycles else None
        else:
            avg_cycle_length = None
        
        # Time in different phases
        total_periods = len(bb_width)
        mean_width = bb_width.mean()
        
        expanding_periods = sum(1 for w in bb_width if w > mean_width)
        contracting_periods = total_periods - expanding_periods
        
        return {
            "avg_cycle_length": round(avg_cycle_length, 1) if avg_cycle_length else None,
            "total_cycles": len(troughs) - 1 if len(troughs) > 1 else 0,
            "expanding_time_pct": round((expanding_periods / total_periods) * 100, 1),
            "contracting_time_pct": round((contracting_periods / total_periods) * 100, 1)
        }
    
    def _analyze_breakout_potential(self, bb_width: pd.Series) -> Dict[str, Any]:
        """Analyze breakout potential based on width patterns."""
        current_width = bb_width.iloc[-1]
        
        # Low volatility = high breakout potential
        mean_width = bb_width.mean()
        std_width = bb_width.std()
        
        if current_width < mean_width - std_width:
            breakout_potential = "high"
            potential_score = 0.8
        elif current_width < mean_width - 0.5 * std_width:
            breakout_potential = "medium"
            potential_score = 0.6
        elif current_width < mean_width:
            breakout_potential = "moderate"
            potential_score = 0.4
        else:
            breakout_potential = "low"
            potential_score = 0.2
        
        # Recent width change
        if len(bb_width) >= 3:
            recent_change = bb_width.iloc[-1] - bb_width.iloc[-3]
            change_direction = "expanding" if recent_change > 0 else "contracting"
        else:
            recent_change = 0
            change_direction = "stable"
        
        return {
            "potential": breakout_potential,
            "potential_score": potential_score,
            "recent_change": round(recent_change, 3),
            "change_direction": change_direction,
            "setup_quality": self._assess_breakout_setup(current_width, mean_width, std_width)
        }
    
    def _assess_breakout_setup(self, current: float, mean: float, std: float) -> str:
        """Assess quality of breakout setup."""
        if current < mean - 1.5 * std:
            return "excellent_setup"
        elif current < mean - std:
            return "good_setup"
        elif current < mean - 0.5 * std:
            return "fair_setup"
        else:
            return "poor_setup"
    
    def _generate_bb_width_signals(self, current_width: float, volatility_analysis: Dict,
                                  squeeze_analysis: Dict, expansion_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate BB Width signals."""
        signals = []
        
        # Squeeze signals
        if squeeze_analysis.get("is_squeeze", False):
            squeeze_quality = squeeze_analysis.get("squeeze_quality", "weak")
            squeeze_periods = squeeze_analysis.get("squeeze_periods", 0)
            
            if squeeze_quality in ["excellent", "good"]:
                signals.append({
                    "type": "breakout_setup",
                    "strength": "strong" if squeeze_quality == "excellent" else "medium",
                    "reason": f"{squeeze_quality.title()} squeeze setup ({squeeze_periods} periods)",
                    "confidence": 0.85 if squeeze_quality == "excellent" else 0.7
                })
        
        # Volatility level signals
        volatility_level = volatility_analysis.get("level", "average")
        percentile = volatility_analysis.get("percentile_rank", 50)
        
        if volatility_level == "extremely_high":
            signals.append({
                "type": "extreme_volatility_warning",
                "strength": "high",
                "reason": f"Extremely high volatility ({percentile:.0f}th percentile)",
                "confidence": 0.8
            })
        elif volatility_level == "low" and percentile < 20:
            signals.append({
                "type": "low_volatility_alert", 
                "strength": "medium",
                "reason": f"Low volatility environment ({percentile:.0f}th percentile) - potential breakout",
                "confidence": 0.7
            })
        
        # Expansion cycle signals
        cycle_stage = expansion_analysis.get("cycle_stage", "unclear")
        
        if cycle_stage == "expanding":
            signals.append({
                "type": "volatility_expansion",
                "strength": "low",
                "reason": "Volatility expanding from recent low",
                "confidence": 0.5
            })
        elif cycle_stage == "contracting":
            signals.append({
                "type": "volatility_contraction",
                "strength": "low",
                "reason": "Volatility contracting from recent high",
                "confidence": 0.5
            })
        
        return signals
    
    def _calculate_bb_width_confidence(self, bb_width: pd.Series, volatility_analysis: Dict, 
                                     cycle_analysis: Dict) -> float:
        """Calculate BB Width analysis confidence."""
        confidence_factors = []
        
        # Data quantity factor
        data_factor = min(1.0, len(bb_width) / 30)
        confidence_factors.append(data_factor)
        
        # Volatility clarity factor
        volatility_level = volatility_analysis.get("level", "average")
        if volatility_level in ["extremely_high", "low"]:
            clarity_factor = 0.9  # Clear signals at extremes
        elif volatility_level in ["high", "below_average"]:
            clarity_factor = 0.7
        else:
            clarity_factor = 0.6
        confidence_factors.append(clarity_factor)
        
        # Cycle data factor
        if not cycle_analysis.get("insufficient_data", False):
            cycle_factor = 0.8
        else:
            cycle_factor = 0.6
        confidence_factors.append(cycle_factor)
        
        # Statistical reliability
        percentile = volatility_analysis.get("percentile_rank", 50)
        if percentile > 80 or percentile < 20:
            stats_factor = 0.8  # High confidence at extremes
        else:
            stats_factor = 0.6
        confidence_factors.append(stats_factor)
        
        return round(np.mean(confidence_factors), 3)
    
    def _generate_bb_width_summary(self, current_width: float, volatility_analysis: Dict, 
                                  squeeze_analysis: Dict) -> str:
        """Generate human-readable BB Width summary."""
        volatility_level = volatility_analysis.get("level", "average")
        percentile = volatility_analysis.get("percentile_rank", 50)
        
        summary = f"BB Width {current_width:.2f}% - {volatility_level.replace('_', ' ')} volatility ({percentile:.0f}th percentile)"
        
        if squeeze_analysis.get("is_squeeze", False):
            squeeze_periods = squeeze_analysis.get("squeeze_periods", 0)
            squeeze_quality = squeeze_analysis.get("squeeze_quality", "weak")
            summary += f" - {squeeze_quality.upper()} SQUEEZE ({squeeze_periods}p)"
        
        return summary