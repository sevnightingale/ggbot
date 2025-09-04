"""
Keltner Channels Preprocessor.

Advanced Keltner Channels preprocessing with volatility-based channel analysis,
price position assessment, and breakout detection.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePreprocessor


class KeltnerChannelsPreprocessor(BasePreprocessor):
    """Advanced Keltner Channels preprocessor with professional-grade channel analysis."""
    
    def preprocess(self, upper_channel: pd.Series, middle_channel: pd.Series, 
                  lower_channel: pd.Series, prices: pd.Series, **kwargs) -> Dict[str, Any]:
        """
        Advanced Keltner Channels preprocessing with comprehensive channel analysis.
        
        Keltner Channels use ATR-based volatility bands around an EMA centerline,
        providing dynamic support/resistance levels and trend analysis.
        
        Args:
            upper_channel: Upper Keltner Channel values
            middle_channel: Middle Keltner Channel (EMA) values
            lower_channel: Lower Keltner Channel values
            prices: Price series for position analysis (required)
            
        Returns:
            Dictionary with comprehensive Keltner Channels analysis
        """
        if len(upper_channel) < 5 or len(prices) < 5:
            return {"error": "Insufficient data for Keltner Channels analysis"}
        
        current_price = float(prices.iloc[-1])
        current_upper = float(upper_channel.iloc[-1])
        current_middle = float(middle_channel.iloc[-1])
        current_lower = float(lower_channel.iloc[-1])
        
        # Position analysis
        position_analysis = self._analyze_price_position(prices, upper_channel, middle_channel, lower_channel)
        
        # Channel width analysis
        width_analysis = self._analyze_channel_width(upper_channel, middle_channel, lower_channel)
        
        # Trend analysis
        trend_analysis = self._analyze_keltner_trend(middle_channel, prices)
        
        # Breakout analysis
        breakout_analysis = self._analyze_keltner_breakouts(prices, upper_channel, lower_channel)
        
        # Support/resistance analysis
        support_resistance = self._analyze_channel_support_resistance(prices, upper_channel, middle_channel, lower_channel)
        
        # Squeeze analysis
        squeeze_analysis = self._analyze_keltner_squeeze(upper_channel, lower_channel, middle_channel)
        
        # Signal generation
        signals = self._generate_keltner_signals(current_price, current_upper, current_middle, current_lower,
                                               position_analysis, breakout_analysis, squeeze_analysis)
        
        # Confidence calculation
        confidence = self._calculate_keltner_confidence(prices, position_analysis, width_analysis)
        
        return {
            "indicator": "Keltner_Channels",
            "current": {
                "price": round(current_price, 4),
                "upper_channel": round(current_upper, 4),
                "middle_channel": round(current_middle, 4),
                "lower_channel": round(current_lower, 4),
                "channel_width": round((current_upper - current_lower) / current_middle * 100, 2),
                "price_position_pct": round(((current_price - current_lower) / (current_upper - current_lower)) * 100, 1),
                "timestamp": datetime.now().isoformat()
            },
            "position": position_analysis,
            "width": width_analysis,
            "trend": trend_analysis,
            "breakouts": breakout_analysis,
            "support_resistance": support_resistance,
            "squeeze": squeeze_analysis,
            "signals": signals,
            "confidence": confidence,
            "summary": self._generate_keltner_summary(current_price, current_upper, current_middle, 
                                                    current_lower, position_analysis, squeeze_analysis)
        }
    
    def _analyze_price_position(self, prices: pd.Series, upper: pd.Series, 
                               middle: pd.Series, lower: pd.Series) -> Dict[str, Any]:
        """Analyze price position within Keltner Channels."""
        current_price = prices.iloc[-1]
        current_upper = upper.iloc[-1]
        current_middle = middle.iloc[-1]
        current_lower = lower.iloc[-1]
        
        # Position calculation (0-100 scale)
        if current_upper != current_lower:
            position_pct = ((current_price - current_lower) / (current_upper - current_lower)) * 100
        else:
            position_pct = 50
        
        # Position classification
        if position_pct > 100:
            position = "above_upper"
        elif position_pct > 80:
            position = "near_upper"
        elif position_pct > 60:
            position = "upper_channel"
        elif position_pct > 40:
            position = "middle_channel"
        elif position_pct > 20:
            position = "lower_channel"
        elif position_pct >= 0:
            position = "near_lower"
        else:
            position = "below_lower"
        
        # Distance from middle
        distance_from_middle = current_price - current_middle
        distance_pct = (distance_from_middle / current_middle) * 100
        
        # Historical position analysis
        position_history = self._analyze_position_history(prices, upper, middle, lower)
        
        return {
            "position": position,
            "position_pct": round(position_pct, 1),
            "distance_from_middle": round(distance_from_middle, 4),
            "distance_from_middle_pct": round(distance_pct, 3),
            "history": position_history
        }
    
    def _analyze_position_history(self, prices: pd.Series, upper: pd.Series, 
                                 middle: pd.Series, lower: pd.Series) -> Dict[str, Any]:
        """Analyze historical price position within channels."""
        if len(prices) < 20:
            return {"insufficient_data": True}
        
        positions = []
        for i in range(len(prices)):
            price = prices.iloc[i]
            upper_val = upper.iloc[i]
            middle_val = middle.iloc[i]
            lower_val = lower.iloc[i]
            
            if upper_val != lower_val:
                pos_pct = ((price - lower_val) / (upper_val - lower_val)) * 100
            else:
                pos_pct = 50
                
            positions.append(pos_pct)
        
        positions = pd.Series(positions)
        
        # Time in different zones
        above_upper = sum(1 for pos in positions if pos > 100)
        below_lower = sum(1 for pos in positions if pos < 0)
        upper_half = sum(1 for pos in positions if 50 <= pos <= 100)
        lower_half = sum(1 for pos in positions if 0 <= pos < 50)
        
        total_periods = len(positions)
        
        return {
            "above_upper_pct": round((above_upper / total_periods) * 100, 1),
            "below_lower_pct": round((below_lower / total_periods) * 100, 1),
            "upper_half_pct": round((upper_half / total_periods) * 100, 1),
            "lower_half_pct": round((lower_half / total_periods) * 100, 1),
            "avg_position": round(positions.mean(), 1),
            "position_volatility": round(positions.std(), 1)
        }
    
    def _analyze_channel_width(self, upper: pd.Series, middle: pd.Series, lower: pd.Series) -> Dict[str, Any]:
        """Analyze Keltner Channel width characteristics."""
        width = (upper - lower) / middle * 100
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
            width_level = "wide"
        elif current_width > mean_width:
            width_level = "above_average"
        elif current_width < mean_width - std_width:
            width_level = "narrow"
        else:
            width_level = "below_average"
        
        # Width trend
        width_velocity = self._calculate_velocity(width, 3)
        width_trend = "expanding" if width_velocity > 0.1 else "contracting" if width_velocity < -0.1 else "stable"
        
        return {
            "current_width": round(current_width, 2),
            "width_level": width_level,
            "percentile": round(width_percentile, 1),
            "trend": width_trend,
            "velocity": round(width_velocity, 3),
            "statistics": {
                "mean": round(mean_width, 2),
                "std": round(std_width, 2),
                "max": round(max_width, 2),
                "min": round(min_width, 2)
            }
        }
    
    def _analyze_keltner_trend(self, middle: pd.Series, prices: pd.Series) -> Dict[str, Any]:
        """Analyze trend using Keltner middle line."""
        current_middle = middle.iloc[-1]
        current_price = prices.iloc[-1]
        
        # Middle line trend
        middle_slope = self._calculate_velocity(middle, 5)
        
        if middle_slope > 0.001:
            middle_trend = "rising"
        elif middle_slope < -0.001:
            middle_trend = "falling"
        else:
            middle_trend = "flat"
        
        # Price vs middle
        price_vs_middle = "above" if current_price > current_middle else "below"
        
        # Trend strength
        trend_strength = min(1.0, abs(middle_slope) / (middle.std() * 0.1)) if middle.std() > 0 else 0
        
        return {
            "middle_trend": middle_trend,
            "middle_slope": round(middle_slope, 6),
            "price_vs_middle": price_vs_middle,
            "trend_strength": round(trend_strength, 3)
        }
    
    def _analyze_keltner_breakouts(self, prices: pd.Series, upper: pd.Series, lower: pd.Series) -> Dict[str, Any]:
        """Analyze breakouts from Keltner Channels."""
        breakouts = []
        
        for i in range(1, min(15, len(prices))):
            prev_price = prices.iloc[-(i+1)]
            curr_price = prices.iloc[-i]
            prev_upper = upper.iloc[-(i+1)]
            curr_upper = upper.iloc[-i]
            prev_lower = lower.iloc[-(i+1)]
            curr_lower = lower.iloc[-i]
            
            # Upward breakout
            if prev_price <= prev_upper and curr_price > curr_upper:
                breakouts.append({
                    "type": "upward_breakout",
                    "periods_ago": i,
                    "price": round(curr_price, 4),
                    "channel_level": round(curr_upper, 4),
                    "strength": (curr_price - curr_upper) / curr_upper
                })
            
            # Downward breakout
            elif prev_price >= prev_lower and curr_price < curr_lower:
                breakouts.append({
                    "type": "downward_breakout",
                    "periods_ago": i,
                    "price": round(curr_price, 4),
                    "channel_level": round(curr_lower, 4),
                    "strength": (curr_lower - curr_price) / curr_lower
                })
        
        return {
            "recent_breakouts": breakouts[:5],
            "latest_breakout": breakouts[0] if breakouts else None,
            "breakout_frequency": len(breakouts) / min(15, len(prices)) if len(prices) > 0 else 0
        }
    
    def _analyze_channel_support_resistance(self, prices: pd.Series, upper: pd.Series, 
                                          middle: pd.Series, lower: pd.Series) -> Dict[str, Any]:
        """Analyze channels as support/resistance."""
        touches = {"upper": [], "middle": [], "lower": []}
        bounces = {"upper": [], "middle": [], "lower": []}
        
        # Touch threshold
        touch_threshold = 0.005  # 0.5%
        
        for i in range(1, len(prices)):
            price = prices.iloc[i]
            prev_price = prices.iloc[i-1]
            
            upper_val = upper.iloc[i]
            middle_val = middle.iloc[i]
            lower_val = lower.iloc[i]
            
            # Check touches and bounces for each level
            levels = [
                ("upper", upper_val),
                ("middle", middle_val),
                ("lower", lower_val)
            ]
            
            for level_name, level_val in levels:
                if abs(price - level_val) / level_val <= touch_threshold:
                    touches[level_name].append({
                        "index": i,
                        "periods_ago": len(prices) - 1 - i,
                        "price": price
                    })
                    
                    # Check for bounce
                    if i < len(prices) - 2:
                        next_price = prices.iloc[i+1]
                        
                        # Support bounce
                        if prev_price > level_val and next_price > price:
                            bounces[level_name].append({
                                "type": "support_bounce",
                                "periods_ago": len(prices) - 1 - i,
                                "strength": abs(next_price - price) / price
                            })
                        # Resistance bounce
                        elif prev_price < level_val and next_price < price:
                            bounces[level_name].append({
                                "type": "resistance_bounce",
                                "periods_ago": len(prices) - 1 - i,
                                "strength": abs(price - next_price) / price
                            })
        
        # Calculate effectiveness for each level
        effectiveness = {}
        for level in ["upper", "middle", "lower"]:
            total_touches = len(touches[level])
            successful_bounces = len(bounces[level])
            success_rate = (successful_bounces / total_touches) if total_touches > 0 else 0
            
            effectiveness[level] = {
                "touches": total_touches,
                "bounces": successful_bounces,
                "success_rate": round(success_rate, 3),
                "recent_touches": touches[level][-3:],
                "recent_bounces": bounces[level][-2:]
            }
        
        return effectiveness
    
    def _analyze_keltner_squeeze(self, upper: pd.Series, lower: pd.Series, middle: pd.Series) -> Dict[str, Any]:
        """Analyze Keltner Channel squeeze conditions."""
        width = (upper - lower) / middle * 100
        current_width = width.iloc[-1]
        
        # Squeeze threshold (20-period low width)
        if len(width) >= 20:
            squeeze_threshold = width.rolling(20).min().iloc[-1]
        else:
            mean_width = width.mean()
            std_width = width.std()
            squeeze_threshold = mean_width - std_width
        
        # Squeeze detection
        is_squeeze = current_width <= squeeze_threshold * 1.05
        
        # Squeeze duration
        squeeze_periods = 0
        if is_squeeze:
            for i in range(len(width) - 1, -1, -1):
                if width.iloc[i] <= squeeze_threshold * 1.05:
                    squeeze_periods += 1
                else:
                    break
        
        return {
            "is_squeeze": is_squeeze,
            "squeeze_periods": squeeze_periods,
            "squeeze_threshold": round(squeeze_threshold, 2),
            "current_width": round(current_width, 2),
            "squeeze_intensity": round((squeeze_threshold - current_width) / squeeze_threshold * 100, 2) if is_squeeze else 0
        }
    
    def _generate_keltner_signals(self, price: float, upper: float, middle: float, lower: float,
                                position_analysis: Dict, breakout_analysis: Dict, 
                                squeeze_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate Keltner Channels signals."""
        signals = []
        
        # Position-based signals
        position = position_analysis.get("position", "middle_channel")
        position_pct = position_analysis.get("position_pct", 50)
        
        if position == "above_upper":
            signals.append({
                "type": "upward_breakout_signal",
                "strength": "strong",
                "reason": f"Price above upper Keltner Channel ({position_pct:.1f}%)",
                "confidence": 0.8
            })
        elif position == "below_lower":
            signals.append({
                "type": "downward_breakout_signal",
                "strength": "strong",
                "reason": f"Price below lower Keltner Channel ({position_pct:.1f}%)",
                "confidence": 0.8
            })
        
        # Breakout signals
        latest_breakout = breakout_analysis.get("latest_breakout")
        if latest_breakout and latest_breakout["periods_ago"] <= 2:
            breakout_type = latest_breakout["type"]
            signal_type = "breakout_buy" if "upward" in breakout_type else "breakout_sell"
            
            signals.append({
                "type": signal_type,
                "strength": "medium",
                "reason": f"Recent {breakout_type.replace('_', ' ')} from Keltner Channel",
                "confidence": 0.7
            })
        
        # Squeeze signals
        if squeeze_analysis.get("is_squeeze", False):
            squeeze_periods = squeeze_analysis.get("squeeze_periods", 0)
            
            signals.append({
                "type": "squeeze_setup",
                "strength": "medium",
                "reason": f"Keltner squeeze for {squeeze_periods} periods - breakout pending",
                "confidence": 0.6
            })
        
        # Mean reversion signals
        if position in ["near_upper", "near_lower"]:
            if position == "near_upper":
                signals.append({
                    "type": "mean_reversion_sell",
                    "strength": "low",
                    "reason": "Price near upper Keltner Channel - potential pullback",
                    "confidence": 0.5
                })
            else:
                signals.append({
                    "type": "mean_reversion_buy",
                    "strength": "low",
                    "reason": "Price near lower Keltner Channel - potential bounce",
                    "confidence": 0.5
                })
        
        return signals
    
    def _calculate_keltner_confidence(self, prices: pd.Series, position_analysis: Dict, 
                                    width_analysis: Dict) -> float:
        """Calculate Keltner Channels analysis confidence."""
        confidence_factors = []
        
        # Data quantity factor
        data_factor = min(1.0, len(prices) / 30)
        confidence_factors.append(data_factor)
        
        # Position clarity factor
        position_pct = position_analysis.get("position_pct", 50)
        if position_pct > 90 or position_pct < 10:
            position_factor = 0.9  # Very clear position
        elif position_pct > 80 or position_pct < 20:
            position_factor = 0.7
        else:
            position_factor = 0.6
        confidence_factors.append(position_factor)
        
        # Channel width factor
        width_level = width_analysis.get("width_level", "average")
        if width_level in ["wide", "narrow"]:
            width_factor = 0.8  # Clear width signals
        else:
            width_factor = 0.6
        confidence_factors.append(width_factor)
        
        # Historical data factor
        history = position_analysis.get("history", {})
        if not history.get("insufficient_data", False):
            history_factor = 0.8
        else:
            history_factor = 0.6
        confidence_factors.append(history_factor)
        
        return round(np.mean(confidence_factors), 3)
    
    def _generate_keltner_summary(self, price: float, upper: float, middle: float, lower: float,
                                position_analysis: Dict, squeeze_analysis: Dict) -> str:
        """Generate human-readable Keltner Channels summary."""
        position = position_analysis.get("position", "middle").replace("_", " ")
        position_pct = position_analysis.get("position_pct", 50)
        width = (upper - lower) / middle * 100
        
        summary = f"Keltner: Price {price:.4f} ({position}, {position_pct:.1f}%)"
        summary += f", Width {width:.2f}%"
        
        if squeeze_analysis.get("is_squeeze", False):
            squeeze_periods = squeeze_analysis.get("squeeze_periods", 0)
            summary += f" - SQUEEZE ({squeeze_periods}p)"
        
        return summary