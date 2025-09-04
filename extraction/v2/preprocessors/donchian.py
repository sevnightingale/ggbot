"""
Donchian Channels Preprocessor.

Advanced Donchian Channels preprocessing with breakout analysis,
channel width assessment, and turtle trading signal detection.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePreprocessor


class DonchianChannelsPreprocessor(BasePreprocessor):
    """Advanced Donchian Channels preprocessor with breakout and turtle trading analysis."""
    
    def preprocess(self, upper_channel: pd.Series, middle_channel: pd.Series,
                  lower_channel: pd.Series, prices: pd.Series, length: int = 20, **kwargs) -> Dict[str, Any]:
        """
        Advanced Donchian Channels preprocessing with comprehensive breakout analysis.
        
        Donchian Channels are formed by the highest high and lowest low over N periods,
        creating natural support/resistance levels and breakout signals.
        
        Args:
            upper_channel: Upper Donchian Channel (highest high over N periods)
            middle_channel: Middle Donchian Channel (average of upper and lower)
            lower_channel: Lower Donchian Channel (lowest low over N periods)
            prices: Price series for analysis (required)
            length: Donchian calculation period
            
        Returns:
            Dictionary with comprehensive Donchian Channels analysis
        """
        if len(upper_channel) < 5 or len(prices) < 5:
            return {"error": "Insufficient data for Donchian Channels analysis"}
        
        current_price = float(prices.iloc[-1])
        current_upper = float(upper_channel.iloc[-1])
        current_middle = float(middle_channel.iloc[-1])
        current_lower = float(lower_channel.iloc[-1])
        
        # Position analysis
        position_analysis = self._analyze_price_position_donchian(prices, upper_channel, middle_channel, lower_channel)
        
        # Breakout analysis
        breakout_analysis = self._analyze_donchian_breakouts(prices, upper_channel, lower_channel)
        
        # Channel width analysis
        width_analysis = self._analyze_donchian_width(upper_channel, lower_channel, middle_channel)
        
        # Turtle trading signals
        turtle_signals = self._analyze_turtle_signals(prices, upper_channel, lower_channel, length)
        
        # Support/resistance analysis
        support_resistance = self._analyze_donchian_support_resistance(prices, upper_channel, middle_channel, lower_channel)
        
        # Consolidation analysis
        consolidation_analysis = self._analyze_donchian_consolidation(upper_channel, lower_channel, prices)
        
        # Trend strength analysis
        trend_analysis = self._analyze_donchian_trend_strength(prices, upper_channel, lower_channel)
        
        # Signal generation
        signals = self._generate_donchian_signals(current_price, current_upper, current_middle, current_lower,
                                                breakout_analysis, turtle_signals, consolidation_analysis)
        
        # Confidence calculation
        confidence = self._calculate_donchian_confidence(prices, breakout_analysis, width_analysis)
        
        return {
            "indicator": "Donchian_Channels",
            "current": {
                "price": round(current_price, 4),
                "upper_channel": round(current_upper, 4),
                "middle_channel": round(current_middle, 4),
                "lower_channel": round(current_lower, 4),
                "channel_width": round(current_upper - current_lower, 4),
                "price_position_pct": round(((current_price - current_lower) / (current_upper - current_lower)) * 100, 1) if current_upper != current_lower else 50,
                "timestamp": datetime.now().isoformat()
            },
            "position": position_analysis,
            "breakouts": breakout_analysis,
            "width": width_analysis,
            "turtle_signals": turtle_signals,
            "support_resistance": support_resistance,
            "consolidation": consolidation_analysis,
            "trend": trend_analysis,
            "signals": signals,
            "confidence": confidence,
            "summary": self._generate_donchian_summary(current_price, current_upper, current_middle, 
                                                     current_lower, breakout_analysis, consolidation_analysis)
        }
    
    def _analyze_price_position_donchian(self, prices: pd.Series, upper: pd.Series, 
                                       middle: pd.Series, lower: pd.Series) -> Dict[str, Any]:
        """Analyze price position within Donchian Channels."""
        current_price = prices.iloc[-1]
        current_upper = upper.iloc[-1]
        current_middle = middle.iloc[-1]
        current_lower = lower.iloc[-1]
        
        # Position calculation
        if current_upper != current_lower:
            position_pct = ((current_price - current_lower) / (current_upper - current_lower)) * 100
        else:
            position_pct = 50
        
        # Position classification
        if current_price >= current_upper:
            position = "at_upper_breakout"
        elif position_pct > 80:
            position = "near_upper"
        elif position_pct > 60:
            position = "upper_third"
        elif position_pct > 40:
            position = "middle_third"
        elif position_pct > 20:
            position = "lower_third"
        elif position_pct > 0:
            position = "near_lower"
        else:
            position = "at_lower_breakout"
        
        # Distance from edges
        distance_to_upper = current_upper - current_price
        distance_to_lower = current_price - current_lower
        
        return {
            "position": position,
            "position_pct": round(position_pct, 1),
            "distance_to_upper": round(distance_to_upper, 4),
            "distance_to_lower": round(distance_to_lower, 4),
            "distance_to_middle": round(abs(current_price - current_middle), 4)
        }
    
    def _analyze_donchian_breakouts(self, prices: pd.Series, upper: pd.Series, lower: pd.Series) -> Dict[str, Any]:
        """Analyze breakouts from Donchian Channels."""
        breakouts = []
        
        for i in range(1, min(10, len(prices))):
            curr_price = prices.iloc[-i]
            prev_price = prices.iloc[-(i+1)]
            curr_upper = upper.iloc[-i]
            curr_lower = lower.iloc[-i]
            
            # Upper breakout (price reaches new high)
            if curr_price >= curr_upper and prev_price < curr_upper:
                breakouts.append({
                    "type": "upper_breakout",
                    "periods_ago": i,
                    "price": round(curr_price, 4),
                    "channel_level": round(curr_upper, 4),
                    "strength": (curr_price - curr_upper) / curr_upper if curr_upper > 0 else 0
                })
            
            # Lower breakout (price reaches new low)  
            elif curr_price <= curr_lower and prev_price > curr_lower:
                breakouts.append({
                    "type": "lower_breakout",
                    "periods_ago": i,
                    "price": round(curr_price, 4),
                    "channel_level": round(curr_lower, 4),
                    "strength": (curr_lower - curr_price) / curr_lower if curr_lower > 0 else 0
                })
        
        # Breakout persistence (how long since last breakout)
        latest_upper = next((b for b in breakouts if b["type"] == "upper_breakout"), None)
        latest_lower = next((b for b in breakouts if b["type"] == "lower_breakout"), None)
        
        return {
            "recent_breakouts": breakouts[:5],
            "latest_breakout": breakouts[0] if breakouts else None,
            "latest_upper_breakout": latest_upper,
            "latest_lower_breakout": latest_lower,
            "breakout_frequency": len(breakouts) / min(10, len(prices)) if len(prices) > 0 else 0
        }
    
    def _analyze_donchian_width(self, upper: pd.Series, lower: pd.Series, middle: pd.Series) -> Dict[str, Any]:
        """Analyze Donchian Channel width characteristics."""
        width = upper - lower
        current_width = width.iloc[-1]
        
        # Width statistics
        mean_width = width.mean()
        std_width = width.std()
        max_width = width.max()
        min_width = width.min()
        
        # Width percentile
        width_percentile = self._calculate_position_rank(width, lookback=len(width))
        
        # Width classification
        if current_width > mean_width + std_width:
            width_level = "very_wide"
        elif current_width > mean_width:
            width_level = "wide"
        elif current_width < mean_width - std_width:
            width_level = "narrow"
        else:
            width_level = "normal"
        
        # Width trend
        width_velocity = self._calculate_velocity(width, 3)
        
        return {
            "current_width": round(current_width, 4),
            "width_level": width_level,
            "percentile": round(width_percentile, 1),
            "width_velocity": round(width_velocity, 6),
            "trend": "expanding" if width_velocity > 0 else "contracting" if width_velocity < 0 else "stable",
            "statistics": {
                "mean": round(mean_width, 4),
                "max": round(max_width, 4),
                "min": round(min_width, 4)
            }
        }
    
    def _analyze_turtle_signals(self, prices: pd.Series, upper: pd.Series, lower: pd.Series, length: int) -> Dict[str, Any]:
        """Analyze turtle trading signals based on Donchian breakouts."""
        current_price = prices.iloc[-1]
        current_upper = upper.iloc[-1]
        current_lower = lower.iloc[-1]
        
        # Turtle entry signals
        turtle_long = current_price >= current_upper  # System 1: 20-day high
        turtle_short = current_price <= current_lower  # System 1: 20-day low
        
        # Additional turtle criteria
        if len(prices) >= length * 2:
            # System 2: 55-day breakout (simulate with available data)
            extended_high = prices.iloc[-length*2:].max()
            extended_low = prices.iloc[-length*2:].min()
            
            turtle_long_s2 = current_price >= extended_high
            turtle_short_s2 = current_price <= extended_low
        else:
            turtle_long_s2 = False
            turtle_short_s2 = False
        
        # Turtle exit signals (10-day)
        if len(prices) >= 10:
            exit_high = prices.iloc[-10:].max()
            exit_low = prices.iloc[-10:].min()
            
            turtle_exit_long = current_price <= exit_low
            turtle_exit_short = current_price >= exit_high
        else:
            turtle_exit_long = False
            turtle_exit_short = False
        
        return {
            "system1": {
                "long_entry": turtle_long,
                "short_entry": turtle_short,
                "periods": length
            },
            "system2": {
                "long_entry": turtle_long_s2,
                "short_entry": turtle_short_s2,
                "periods": length * 2
            },
            "exits": {
                "long_exit": turtle_exit_long,
                "short_exit": turtle_exit_short,
                "exit_periods": 10
            }
        }
    
    def _analyze_donchian_support_resistance(self, prices: pd.Series, upper: pd.Series,
                                           middle: pd.Series, lower: pd.Series) -> Dict[str, Any]:
        """Analyze Donchian levels as support/resistance."""
        levels = {
            "upper": {"touches": 0, "bounces": 0, "breaks": 0},
            "middle": {"touches": 0, "bounces": 0, "breaks": 0},
            "lower": {"touches": 0, "bounces": 0, "breaks": 0}
        }
        
        touch_threshold = 0.002  # 0.2%
        
        for i in range(1, len(prices) - 1):
            price = prices.iloc[i]
            prev_price = prices.iloc[i-1]
            next_price = prices.iloc[i+1]
            
            upper_val = upper.iloc[i]
            middle_val = middle.iloc[i]
            lower_val = lower.iloc[i]
            
            # Check touches for each level
            level_data = [
                ("upper", upper_val),
                ("middle", middle_val), 
                ("lower", lower_val)
            ]
            
            for level_name, level_val in level_data:
                if level_val > 0 and abs(price - level_val) / level_val <= touch_threshold:
                    levels[level_name]["touches"] += 1
                    
                    # Check for bounce
                    if level_name == "upper" and prev_price < level_val and next_price < price:
                        levels[level_name]["bounces"] += 1
                    elif level_name == "lower" and prev_price > level_val and next_price > price:
                        levels[level_name]["bounces"] += 1
                    elif level_name == "middle":
                        # Middle can act as either support or resistance
                        if (prev_price < level_val and next_price > price) or (prev_price > level_val and next_price < price):
                            levels[level_name]["bounces"] += 1
                
                # Check for breaks
                if level_name == "upper" and price > level_val:
                    levels[level_name]["breaks"] += 1
                elif level_name == "lower" and price < level_val:
                    levels[level_name]["breaks"] += 1
        
        # Calculate effectiveness
        for level in levels:
            total_tests = levels[level]["touches"]
            if total_tests > 0:
                levels[level]["bounce_rate"] = round(levels[level]["bounces"] / total_tests, 3)
            else:
                levels[level]["bounce_rate"] = 0
        
        return levels
    
    def _analyze_donchian_consolidation(self, upper: pd.Series, lower: pd.Series, prices: pd.Series) -> Dict[str, Any]:
        """Analyze consolidation patterns in Donchian Channels."""
        width = upper - lower
        current_width = width.iloc[-1]
        
        # Consolidation detection (narrow channel)
        mean_width = width.mean()
        std_width = width.std()
        
        is_consolidation = current_width < mean_width - 0.5 * std_width
        
        # Consolidation duration
        consolidation_periods = 0
        if is_consolidation:
            threshold = mean_width - 0.5 * std_width
            for i in range(len(width) - 1, -1, -1):
                if width.iloc[i] < threshold:
                    consolidation_periods += 1
                else:
                    break
        
        # Price range within consolidation
        if consolidation_periods > 0:
            recent_prices = prices.iloc[-consolidation_periods:]
            price_range = recent_prices.max() - recent_prices.min()
            avg_price = recent_prices.mean()
            range_pct = (price_range / avg_price) * 100 if avg_price > 0 else 0
        else:
            price_range = 0
            range_pct = 0
        
        return {
            "is_consolidation": is_consolidation,
            "consolidation_periods": consolidation_periods,
            "width_threshold": round(mean_width - 0.5 * std_width, 4),
            "price_range": round(price_range, 4),
            "price_range_pct": round(range_pct, 2),
            "breakout_potential": "high" if consolidation_periods >= 10 else "medium" if consolidation_periods >= 5 else "low"
        }
    
    def _analyze_donchian_trend_strength(self, prices: pd.Series, upper: pd.Series, lower: pd.Series) -> Dict[str, Any]:
        """Analyze trend strength using Donchian position."""
        current_price = prices.iloc[-1]
        current_upper = upper.iloc[-1]
        current_lower = lower.iloc[-1]
        
        # Position-based trend strength
        if current_upper != current_lower:
            position_pct = ((current_price - current_lower) / (current_upper - current_lower)) * 100
        else:
            position_pct = 50
        
        # Trend classification
        if position_pct >= 80:
            trend_strength = "strong_bullish"
        elif position_pct >= 60:
            trend_strength = "moderate_bullish"
        elif position_pct <= 20:
            trend_strength = "strong_bearish"
        elif position_pct <= 40:
            trend_strength = "moderate_bearish"
        else:
            trend_strength = "neutral"
        
        # Channel utilization (how much of channel is being used)
        recent_prices = prices.iloc[-10:] if len(prices) >= 10 else prices
        recent_range = recent_prices.max() - recent_prices.min()
        channel_width = current_upper - current_lower
        
        utilization = (recent_range / channel_width) if channel_width > 0 else 0
        
        return {
            "strength": trend_strength,
            "position_pct": round(position_pct, 1),
            "channel_utilization": round(utilization, 3),
            "utilization_rating": "high" if utilization > 0.8 else "medium" if utilization > 0.5 else "low"
        }
    
    def _generate_donchian_signals(self, price: float, upper: float, middle: float, lower: float,
                                 breakout_analysis: Dict, turtle_signals: Dict, 
                                 consolidation_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate Donchian Channels signals."""
        signals = []
        
        # Breakout signals
        latest_breakout = breakout_analysis.get("latest_breakout")
        if latest_breakout and latest_breakout["periods_ago"] <= 2:
            breakout_type = latest_breakout["type"]
            signal_type = "breakout_buy" if "upper" in breakout_type else "breakout_sell"
            
            signals.append({
                "type": signal_type,
                "strength": "strong",
                "reason": f"Recent Donchian {breakout_type.replace('_', ' ')} - new {('high' if 'upper' in breakout_type else 'low')}",
                "confidence": 0.8
            })
        
        # Turtle trading signals
        system1 = turtle_signals.get("system1", {})
        if system1.get("long_entry", False):
            signals.append({
                "type": "turtle_long_entry",
                "strength": "strong", 
                "reason": f"Turtle System 1: {system1['periods']}-period high breakout",
                "confidence": 0.85
            })
        elif system1.get("short_entry", False):
            signals.append({
                "type": "turtle_short_entry",
                "strength": "strong",
                "reason": f"Turtle System 1: {system1['periods']}-period low breakout", 
                "confidence": 0.85
            })
        
        # Exit signals
        exits = turtle_signals.get("exits", {})
        if exits.get("long_exit", False):
            signals.append({
                "type": "turtle_long_exit",
                "strength": "medium",
                "reason": "Turtle exit: 10-period low reached",
                "confidence": 0.7
            })
        elif exits.get("short_exit", False):
            signals.append({
                "type": "turtle_short_exit", 
                "strength": "medium",
                "reason": "Turtle exit: 10-period high reached",
                "confidence": 0.7
            })
        
        # Consolidation breakout setup
        if consolidation_analysis.get("is_consolidation", False):
            consolidation_periods = consolidation_analysis.get("consolidation_periods", 0)
            breakout_potential = consolidation_analysis.get("breakout_potential", "low")
            
            if breakout_potential in ["high", "medium"]:
                signals.append({
                    "type": "consolidation_breakout_setup",
                    "strength": "medium" if breakout_potential == "high" else "low",
                    "reason": f"Donchian consolidation for {consolidation_periods} periods - breakout pending",
                    "confidence": 0.7 if breakout_potential == "high" else 0.5
                })
        
        # Position-based signals
        position_pct = ((price - lower) / (upper - lower)) * 100 if upper != lower else 50
        
        if position_pct > 90:
            signals.append({
                "type": "near_resistance",
                "strength": "low",
                "reason": f"Price at {position_pct:.1f}% of Donchian range - near resistance",
                "confidence": 0.4
            })
        elif position_pct < 10:
            signals.append({
                "type": "near_support",
                "strength": "low", 
                "reason": f"Price at {position_pct:.1f}% of Donchian range - near support",
                "confidence": 0.4
            })
        
        return signals
    
    def _calculate_donchian_confidence(self, prices: pd.Series, breakout_analysis: Dict, 
                                     width_analysis: Dict) -> float:
        """Calculate Donchian Channels analysis confidence."""
        confidence_factors = []
        
        # Data quantity factor (Donchian needs significant data)
        data_factor = min(1.0, len(prices) / 40)
        confidence_factors.append(data_factor)
        
        # Breakout clarity factor
        breakout_frequency = breakout_analysis.get("breakout_frequency", 0)
        if 0.1 <= breakout_frequency <= 0.3:
            breakout_factor = 0.8  # Good breakout frequency
        else:
            breakout_factor = 0.6
        confidence_factors.append(breakout_factor)
        
        # Width factor (wider channels = clearer signals)
        width_level = width_analysis.get("width_level", "normal")
        if width_level in ["very_wide", "wide"]:
            width_factor = 0.8
        elif width_level == "narrow":
            width_factor = 0.6
        else:
            width_factor = 0.7
        confidence_factors.append(width_factor)
        
        # Channel utilization factor
        width_percentile = width_analysis.get("percentile", 50)
        if width_percentile > 70 or width_percentile < 30:
            util_factor = 0.8  # Clear width extremes
        else:
            util_factor = 0.6
        confidence_factors.append(util_factor)
        
        return round(np.mean(confidence_factors), 3)
    
    def _generate_donchian_summary(self, price: float, upper: float, middle: float, lower: float,
                                 breakout_analysis: Dict, consolidation_analysis: Dict) -> str:
        """Generate human-readable Donchian Channels summary."""
        position_pct = ((price - lower) / (upper - lower)) * 100 if upper != lower else 50
        width = upper - lower
        
        summary = f"Donchian: Price {price:.4f} ({position_pct:.1f}%), Width {width:.4f}"
        
        # Add breakout information
        latest_breakout = breakout_analysis.get("latest_breakout")
        if latest_breakout and latest_breakout["periods_ago"] <= 3:
            breakout_type = latest_breakout["type"].replace("_", " ")
            periods_ago = latest_breakout["periods_ago"]
            summary += f" - {breakout_type} {periods_ago}p ago"
        
        # Add consolidation information
        if consolidation_analysis.get("is_consolidation", False):
            consolidation_periods = consolidation_analysis.get("consolidation_periods", 0)
            summary += f" - CONSOLIDATION ({consolidation_periods}p)"
        
        return summary