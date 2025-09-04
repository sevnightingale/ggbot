"""
Base preprocessor class with common utilities for all technical indicators.

This module provides shared functionality used across all indicator preprocessors,
including mathematical utilities, pattern detection, and signal generation helpers.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from core.common.logger import logger


class BasePreprocessor:
    """
    Base class providing common functionality for all indicator preprocessors.
    
    Contains shared mathematical utilities, pattern detection algorithms,
    and signal generation helpers used across different technical indicators.
    """
    
    def __init__(self):
        """Initialize base preprocessor with logging."""
        self._log = logger.bind(component="preprocessor_base")
    
    # ==================================================================================
    # MATHEMATICAL UTILITIES
    # ==================================================================================
    
    def _calculate_velocity(self, values: pd.Series, periods: int = 3) -> float:
        """Calculate velocity (rate of change) over specified periods."""
        if len(values) < periods + 1:
            return 0.0
        
        current = values.iloc[-1]
        previous = values.iloc[-(periods + 1)]
        return (current - previous) / periods
    
    def _calculate_acceleration(self, values: pd.Series, periods: int = 6) -> float:
        """Calculate acceleration (change in velocity)."""
        if len(values) < periods + 3:
            return 0.0
        
        recent_velocity = self._calculate_velocity(values.iloc[-3:], 2)
        past_velocity = self._calculate_velocity(values.iloc[-(periods+3):-(periods)], 2)
        
        return recent_velocity - past_velocity
    
    def _analyze_trend(self, values: pd.Series, periods: List[int] = [5, 10, 20]) -> Dict[str, Any]:
        """Sophisticated trend analysis using multiple timeframes."""
        if len(values) < max(periods):
            return {"direction": "unknown", "strength": 0, "confidence": 0}
        
        trends = {}
        for period in periods:
            if len(values) >= period:
                recent = values.iloc[-period:].values
                slope = np.polyfit(range(len(recent)), recent, 1)[0]
                trends[f"ma{period}"] = slope
        
        # Weighted trend calculation
        if trends:
            weighted_trend = sum(slope * (1/period) for period, slope in 
                               [(int(k[2:]), v) for k, v in trends.items()]) / sum(1/p for p in periods if len(values) >= p)
            
            direction = "rising" if weighted_trend > 0.1 else "falling" if weighted_trend < -0.1 else "sideways"
            strength = min(abs(weighted_trend), 1.0)
            
            # Confidence based on trend consistency
            trend_consistency = 1 - np.std(list(trends.values())) / (np.mean(np.abs(list(trends.values()))) + 0.001)
            confidence = max(0, min(1, trend_consistency))
            
            return {
                "direction": direction,
                "strength": strength,
                "confidence": confidence,
                "trends_by_period": trends
            }
        
        return {"direction": "unknown", "strength": 0, "confidence": 0}
    
    # ==================================================================================
    # PATTERN DETECTION UTILITIES
    # ==================================================================================
    
    def _find_peaks(self, values: pd.Series, prominence: float = 2) -> List[Dict[str, Any]]:
        """Find peaks in a series."""
        peaks = []
        values_array = values.values
        
        for i in range(1, len(values_array) - 1):
            if (values_array[i] > values_array[i-1] and 
                values_array[i] > values_array[i+1] and
                values_array[i] - min(values_array[i-1], values_array[i+1]) >= prominence):
                peaks.append({
                    "index": i,
                    "value": values_array[i],
                    "periods_ago": len(values) - 1 - i
                })
        
        return peaks
    
    def _find_troughs(self, values: pd.Series, prominence: float = 2) -> List[Dict[str, Any]]:
        """Find troughs in a series.""" 
        troughs = []
        values_array = values.values
        
        for i in range(1, len(values_array) - 1):
            if (values_array[i] < values_array[i-1] and
                values_array[i] < values_array[i+1] and  
                max(values_array[i-1], values_array[i+1]) - values_array[i] >= prominence):
                troughs.append({
                    "index": i,
                    "value": values_array[i],
                    "periods_ago": len(values) - 1 - i
                })
        
        return troughs
    
    def _find_recent_extremes(self, values: pd.Series, lookback: int = 20) -> Dict[str, Any]:
        """Find recent extreme values with significance analysis."""
        lookback = min(lookback, len(values))
        recent_values = values.iloc[-lookback:]
        
        high_idx = recent_values.idxmax()
        low_idx = recent_values.idxmin()
        
        high_value = recent_values[high_idx]
        low_value = recent_values[low_idx]
        
        # Calculate periods ago
        high_periods_ago = len(values) - 1 - values.index.get_loc(high_idx)
        low_periods_ago = len(values) - 1 - values.index.get_loc(low_idx)
        
        # Significance calculation
        current = values.iloc[-1]
        high_significance = min(1.0, abs(high_value - current) / (np.std(recent_values) + 0.001))
        low_significance = min(1.0, abs(low_value - current) / (np.std(recent_values) + 0.001))
        
        return {
            "high_value": high_value,
            "high_periods_ago": high_periods_ago,
            "high_significance": high_significance,
            "low_value": low_value,
            "low_periods_ago": low_periods_ago,
            "low_significance": low_significance
        }
    
    # ==================================================================================
    # ZONE ANALYSIS UTILITIES
    # ==================================================================================
    
    def _analyze_zones(self, values: pd.Series, upper_threshold: float, lower_threshold: float) -> Dict[str, Any]:
        """Analyze time spent in different zones."""
        current = values.iloc[-1]
        
        # Current zone
        if current >= upper_threshold:
            current_zone = "overbought"
        elif current <= lower_threshold:
            current_zone = "oversold"
        else:
            current_zone = "neutral"
        
        # Time analysis
        total_periods = len(values)
        overbought_periods = sum(1 for v in values if v >= upper_threshold)
        oversold_periods = sum(1 for v in values if v <= lower_threshold)
        
        # Current streak analysis
        periods_overbought = 0
        periods_oversold = 0
        
        for i in range(len(values) - 1, -1, -1):
            if current_zone == "overbought" and values.iloc[i] >= upper_threshold:
                periods_overbought += 1
            elif current_zone == "oversold" and values.iloc[i] <= lower_threshold:
                periods_oversold += 1
            else:
                break
        
        return {
            "current_zone": current_zone,
            "overbought_status": self._get_zone_status(current, upper_threshold, "above"),
            "oversold_status": self._get_zone_status(current, lower_threshold, "below"),
            "periods_overbought": periods_overbought,
            "periods_oversold": periods_oversold,
            "overbought_percentage": round((overbought_periods / total_periods) * 100, 1),
            "oversold_percentage": round((oversold_periods / total_periods) * 100, 1)
        }
    
    def _get_zone_status(self, value: float, threshold: float, direction: str) -> str:
        """Get descriptive zone status."""
        diff = abs(value - threshold)
        
        if direction == "above":
            if value > threshold:
                return "far_above" if diff > 15 else "above"
            else:
                return "far_below" if diff > 15 else "below"
        else:  # below
            if value < threshold:
                return "far_below" if diff > 15 else "below"
            else:
                return "far_above" if diff > 15 else "above"
    
    # ==================================================================================
    # CROSSOVER AND LEVEL ANALYSIS
    # ==================================================================================
    
    def _analyze_key_levels(self, values: pd.Series, levels: List[float]) -> Dict[str, Any]:
        """Analyze interaction with key levels."""
        crossovers = []
        
        for level in levels:
            # Find recent crossovers
            for i in range(1, min(10, len(values))):
                prev_val = values.iloc[-(i+1)]
                curr_val = values.iloc[-i]
                
                if prev_val <= level < curr_val:
                    crossovers.append({
                        "level": level,
                        "direction": "up",
                        "periods_ago": i,
                        "strength": abs(curr_val - level)
                    })
                elif prev_val >= level > curr_val:
                    crossovers.append({
                        "level": level,
                        "direction": "down", 
                        "periods_ago": i,
                        "strength": abs(curr_val - level)
                    })
        
        # Sort by recency
        crossovers.sort(key=lambda x: x["periods_ago"])
        
        return {
            "recent_crossovers": crossovers[:5],
            "current_level_distances": {level: round(values.iloc[-1] - level, 2) for level in levels}
        }
    
    # ==================================================================================
    # CONFIDENCE AND QUALITY METRICS
    # ==================================================================================
    
    def _calculate_analysis_confidence(self, values: pd.Series, trend: Dict, patterns: Dict) -> float:
        """Calculate overall confidence in the analysis."""
        confidence_factors = []
        
        # Data quantity factor
        data_factor = min(1.0, len(values) / 50)  # Full confidence with 50+ periods
        confidence_factors.append(data_factor)
        
        # Trend confidence
        confidence_factors.append(trend.get("confidence", 0.5))
        
        # Pattern confidence
        if patterns:
            pattern_confidences = [p.get("confidence", 0.5) for p in patterns.values() if isinstance(p, dict)]
            if pattern_confidences:
                confidence_factors.append(np.mean(pattern_confidences))
        
        # Data volatility factor (lower volatility = higher confidence)
        volatility = np.std(values) / np.mean(values) if np.mean(values) != 0 else 1
        volatility_factor = max(0.3, min(1.0, 1 - volatility))
        confidence_factors.append(volatility_factor)
        
        return round(np.mean(confidence_factors), 3)
    
    # ==================================================================================
    # POSITION AND RANK ANALYSIS
    # ==================================================================================
    
    def _calculate_position_rank(self, values: pd.Series, lookback: int = 20) -> float:
        """Calculate position rank within last N bars (percentile)."""
        lookback = min(lookback, len(values))
        recent_values = values.iloc[-lookback:]
        current = values.iloc[-1]
        
        rank = (recent_values < current).sum() / len(recent_values) * 100
        return rank
    
    def _interpret_position_rank(self, rank: float) -> str:
        """Interpret position rank percentile."""
        if rank >= 90:
            return "extremely_high"
        elif rank >= 75:
            return "high" 
        elif rank >= 60:
            return "above_average"
        elif rank >= 40:
            return "average"
        elif rank >= 25:
            return "below_average"
        elif rank >= 10:
            return "low"
        else:
            return "extremely_low"