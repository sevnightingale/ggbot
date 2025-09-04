"""
VWAP (Volume Weighted Average Price) Preprocessor.

Advanced VWAP preprocessing with volume profile analysis, fair value assessment,
and institutional trading level detection.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePreprocessor


class VWAPPreprocessor(BasePreprocessor):
    """Advanced VWAP preprocessor with professional-grade volume analysis."""
    
    def preprocess(self, vwap: pd.Series, prices: pd.Series = None, volumes: pd.Series = None,
                  **kwargs) -> Dict[str, Any]:
        """
        Advanced VWAP preprocessing with comprehensive volume-weighted analysis.
        
        VWAP represents the average price weighted by volume, often used as a benchmark
        for institutional trading and fair value assessment.
        
        Args:
            vwap: VWAP values
            prices: Price series for position analysis (required)
            volumes: Volume series for volume profile analysis (optional)
            
        Returns:
            Dictionary with comprehensive VWAP analysis
        """
        if len(vwap) < 5:
            return {"error": "Insufficient data for VWAP analysis"}
        
        if prices is None:
            return {"error": "Price data required for VWAP analysis"}
        
        current_vwap = float(vwap.iloc[-1])
        current_price = float(prices.iloc[-1])
        
        # Price-VWAP relationship
        price_relationship = self._analyze_price_vwap_relationship(prices, vwap)
        
        # Fair value analysis
        fair_value_analysis = self._analyze_fair_value_assessment(prices, vwap)
        
        # VWAP trend analysis
        trend_analysis = self._analyze_vwap_trend(vwap)
        
        # Volume profile analysis
        volume_profile = {}
        if volumes is not None:
            volume_profile = self._analyze_volume_profile(prices, vwap, volumes)
        
        # Support/resistance analysis
        support_resistance = self._analyze_vwap_support_resistance(prices, vwap)
        
        # Deviation analysis
        deviation_analysis = self._analyze_vwap_deviations(prices, vwap)
        
        # Anchored VWAP behavior
        anchored_analysis = self._analyze_anchored_vwap_behavior(vwap)
        
        # Signal generation
        signals = self._generate_vwap_signals(current_vwap, current_price, price_relationship,
                                            fair_value_analysis, support_resistance)
        
        # Confidence calculation
        confidence = self._calculate_vwap_confidence(vwap, prices, volume_profile, trend_analysis)
        
        return {
            "indicator": "VWAP",
            "current": {
                "vwap_value": round(current_vwap, 4),
                "price": round(current_price, 4),
                "price_distance": round(current_price - current_vwap, 4),
                "price_distance_pct": round(((current_price - current_vwap) / current_vwap) * 100, 3),
                "timestamp": datetime.now().isoformat()
            },
            "price_relationship": price_relationship,
            "fair_value": fair_value_analysis,
            "trend": trend_analysis,
            "volume_profile": volume_profile,
            "support_resistance": support_resistance,
            "deviations": deviation_analysis,
            "anchored_behavior": anchored_analysis,
            "signals": signals,
            "confidence": confidence,
            "summary": self._generate_vwap_summary(current_vwap, current_price, price_relationship, fair_value_analysis)
        }
    
    def _analyze_price_vwap_relationship(self, prices: pd.Series, vwap: pd.Series) -> Dict[str, Any]:
        """Analyze price position relative to VWAP."""
        current_price = prices.iloc[-1]
        current_vwap = vwap.iloc[-1]
        
        # Current position
        if current_price > current_vwap:
            position = "above"
            bias = "bullish"
        elif current_price < current_vwap:
            position = "below"
            bias = "bearish"
        else:
            position = "at_level"
            bias = "neutral"
        
        # Distance metrics
        distance = current_price - current_vwap
        distance_pct = (distance / current_vwap) * 100
        
        # Historical position analysis
        above_periods = sum(1 for i in range(len(prices)) if prices.iloc[i] > vwap.iloc[i])
        below_periods = len(prices) - above_periods
        total_periods = len(prices)
        
        # Position changes (crossovers)
        position_changes = 0
        prev_position = "above" if prices.iloc[0] > vwap.iloc[0] else "below"
        
        for i in range(1, len(prices)):
            curr_position = "above" if prices.iloc[i] > vwap.iloc[i] else "below"
            if curr_position != prev_position:
                position_changes += 1
            prev_position = curr_position
        
        # Average distance from VWAP
        distances = prices - vwap
        avg_distance = distances.mean()
        max_distance = distances.max()
        min_distance = distances.min()
        
        return {
            "position": position,
            "bias": bias,
            "distance": round(distance, 4),
            "distance_pct": round(distance_pct, 3),
            "above_vwap_pct": round((above_periods / total_periods) * 100, 1),
            "below_vwap_pct": round((below_periods / total_periods) * 100, 1),
            "position_changes": position_changes,
            "avg_distance": round(avg_distance, 4),
            "max_distance": round(max_distance, 4),
            "min_distance": round(min_distance, 4)
        }
    
    def _analyze_fair_value_assessment(self, prices: pd.Series, vwap: pd.Series) -> Dict[str, Any]:
        """Analyze price relative to VWAP fair value."""
        current_price = prices.iloc[-1]
        current_vwap = vwap.iloc[-1]
        
        # Fair value assessment
        distance_pct = ((current_price - current_vwap) / current_vwap) * 100
        
        if distance_pct > 2:
            fair_value_assessment = "overvalued"
        elif distance_pct > 0.5:
            fair_value_assessment = "slightly_overvalued"
        elif distance_pct < -2:
            fair_value_assessment = "undervalued"
        elif distance_pct < -0.5:
            fair_value_assessment = "slightly_undervalued"
        else:
            fair_value_assessment = "fairly_valued"
        
        # Historical fair value analysis
        historical_distances = ((prices - vwap) / vwap) * 100
        
        overvalued_periods = sum(1 for d in historical_distances if d > 1)
        undervalued_periods = sum(1 for d in historical_distances if d < -1)
        fair_valued_periods = len(historical_distances) - overvalued_periods - undervalued_periods
        
        total_periods = len(historical_distances)
        
        # Reversion tendency
        reversion_analysis = self._analyze_mean_reversion_tendency(prices, vwap)
        
        return {
            "current_assessment": fair_value_assessment,
            "distance_from_fair_value_pct": round(distance_pct, 3),
            "overvalued_time_pct": round((overvalued_periods / total_periods) * 100, 1),
            "undervalued_time_pct": round((undervalued_periods / total_periods) * 100, 1),
            "fairly_valued_time_pct": round((fair_valued_periods / total_periods) * 100, 1),
            "mean_reversion": reversion_analysis
        }
    
    def _analyze_mean_reversion_tendency(self, prices: pd.Series, vwap: pd.Series) -> Dict[str, Any]:
        """Analyze tendency for prices to revert to VWAP."""
        # Look for instances where price deviated significantly and then reverted
        reversions = []
        distance_threshold = 0.02  # 2% threshold
        
        distances = (prices - vwap) / vwap
        
        for i in range(2, len(distances)):
            prev_distance = distances.iloc[i-1]
            curr_distance = distances.iloc[i]
            
            # Check for reversion from extreme levels
            if abs(prev_distance) > distance_threshold and abs(curr_distance) < abs(prev_distance) * 0.7:
                reversions.append({
                    "index": i,
                    "periods_ago": len(distances) - 1 - i,
                    "from_distance": prev_distance,
                    "to_distance": curr_distance,
                    "reversion_strength": abs(prev_distance - curr_distance)
                })
        
        # Calculate reversion statistics
        total_extreme_cases = sum(1 for d in distances if abs(d) > distance_threshold)
        reversion_cases = len(reversions)
        reversion_rate = (reversion_cases / total_extreme_cases) if total_extreme_cases > 0 else 0
        
        return {
            "reversion_rate": round(reversion_rate, 3),
            "total_reversions": reversion_cases,
            "recent_reversions": reversions[-3:] if reversions else [],
            "reversion_strength": "high" if reversion_rate > 0.6 else "medium" if reversion_rate > 0.3 else "low"
        }
    
    def _analyze_vwap_trend(self, vwap: pd.Series) -> Dict[str, Any]:
        """Analyze VWAP trend characteristics."""
        # VWAP slope
        slope = self._calculate_velocity(vwap, 5)
        
        if slope > 0.001:
            trend_direction = "rising"
        elif slope < -0.001:
            trend_direction = "falling"
        else:
            trend_direction = "flat"
        
        # Trend strength
        trend_strength = min(1.0, abs(slope) / (vwap.std() * 0.1)) if vwap.std() > 0 else 0
        
        # VWAP smoothness (should be smoother than regular prices)
        vwap_volatility = vwap.std()
        vwap_mean = vwap.mean()
        smoothness = 1 - (vwap_volatility / vwap_mean) if vwap_mean > 0 else 0
        
        return {
            "direction": trend_direction,
            "slope": round(slope, 6),
            "strength": round(trend_strength, 3),
            "smoothness": round(smoothness, 3)
        }
    
    def _analyze_volume_profile(self, prices: pd.Series, vwap: pd.Series, volumes: pd.Series) -> Dict[str, Any]:
        """Analyze volume profile around VWAP."""
        # Volume-weighted analysis
        total_volume = volumes.sum()
        
        # Volume above vs below VWAP
        above_vwap_volume = 0
        below_vwap_volume = 0
        
        for i in range(len(prices)):
            if prices.iloc[i] > vwap.iloc[i]:
                above_vwap_volume += volumes.iloc[i]
            else:
                below_vwap_volume += volumes.iloc[i]
        
        # Volume distribution
        above_volume_pct = (above_vwap_volume / total_volume) * 100
        below_volume_pct = (below_vwap_volume / total_volume) * 100
        
        # High volume periods near VWAP (institutional activity)
        near_vwap_volume = 0
        near_vwap_threshold = 0.005  # 0.5%
        
        for i in range(len(prices)):
            distance_pct = abs((prices.iloc[i] - vwap.iloc[i]) / vwap.iloc[i])
            if distance_pct <= near_vwap_threshold:
                near_vwap_volume += volumes.iloc[i]
        
        near_vwap_pct = (near_vwap_volume / total_volume) * 100
        
        # Average volume at different price levels
        avg_volume_above = above_vwap_volume / sum(1 for i in range(len(prices)) if prices.iloc[i] > vwap.iloc[i]) if any(prices.iloc[i] > vwap.iloc[i] for i in range(len(prices))) else 0
        avg_volume_below = below_vwap_volume / sum(1 for i in range(len(prices)) if prices.iloc[i] <= vwap.iloc[i]) if any(prices.iloc[i] <= vwap.iloc[i] for i in range(len(prices))) else 0
        
        return {
            "above_vwap_volume_pct": round(above_volume_pct, 1),
            "below_vwap_volume_pct": round(below_volume_pct, 1),
            "near_vwap_volume_pct": round(near_vwap_pct, 1),
            "avg_volume_above": round(avg_volume_above, 2),
            "avg_volume_below": round(avg_volume_below, 2),
            "volume_bias": "above_vwap" if above_volume_pct > below_volume_pct else "below_vwap",
            "institutional_activity": "high" if near_vwap_pct > 20 else "medium" if near_vwap_pct > 10 else "low"
        }
    
    def _analyze_vwap_support_resistance(self, prices: pd.Series, vwap: pd.Series) -> Dict[str, Any]:
        """Analyze VWAP as dynamic support/resistance."""
        touches = []
        bounces = []
        
        # VWAP touch threshold
        touch_threshold = 0.003  # 0.3%
        
        for i in range(1, len(prices)):
            price = prices.iloc[i]
            vwap_val = vwap.iloc[i]
            prev_price = prices.iloc[i-1]
            
            # Check for VWAP touch
            if abs(price - vwap_val) / vwap_val <= touch_threshold:
                touches.append({
                    "index": i,
                    "periods_ago": len(prices) - 1 - i,
                    "price": price,
                    "vwap_value": vwap_val
                })
                
                # Check for bounce
                if i < len(prices) - 2:
                    next_price = prices.iloc[i+1]
                    
                    # Support bounce
                    if prev_price < vwap_val and next_price > price:
                        bounces.append({
                            "type": "support_bounce",
                            "index": i,
                            "periods_ago": len(prices) - 1 - i,
                            "strength": abs(next_price - price) / price
                        })
                    
                    # Resistance bounce
                    elif prev_price > vwap_val and next_price < price:
                        bounces.append({
                            "type": "resistance_bounce",
                            "index": i,
                            "periods_ago": len(prices) - 1 - i,
                            "strength": abs(price - next_price) / price
                        })
        
        # Calculate effectiveness
        success_rate = (len(bounces) / len(touches)) if len(touches) > 0 else 0
        
        return {
            "total_touches": len(touches),
            "successful_bounces": len(bounces),
            "success_rate": round(success_rate, 3),
            "recent_touches": touches[-5:] if touches else [],
            "recent_bounces": bounces[-3:] if bounces else [],
            "effectiveness": "high" if success_rate > 0.5 else "medium" if success_rate > 0.25 else "low"
        }
    
    def _analyze_vwap_deviations(self, prices: pd.Series, vwap: pd.Series) -> Dict[str, Any]:
        """Analyze standard deviations from VWAP."""
        # Calculate deviations
        deviations = prices - vwap
        std_dev = deviations.std()
        
        current_deviation = deviations.iloc[-1]
        current_std_devs = current_deviation / std_dev if std_dev > 0 else 0
        
        # Standard deviation bands
        vwap_current = vwap.iloc[-1]
        upper_1std = vwap_current + std_dev
        lower_1std = vwap_current - std_dev
        upper_2std = vwap_current + 2 * std_dev
        lower_2std = vwap_current - 2 * std_dev
        
        # Current position in std dev terms
        current_price = prices.iloc[-1]
        if current_price > upper_2std:
            std_position = "above_2std"
        elif current_price > upper_1std:
            std_position = "above_1std"
        elif current_price < lower_2std:
            std_position = "below_2std"
        elif current_price < lower_1std:
            std_position = "below_1std"
        else:
            std_position = "within_1std"
        
        return {
            "current_std_devs": round(current_std_devs, 2),
            "std_position": std_position,
            "standard_deviation": round(std_dev, 4),
            "upper_1std": round(upper_1std, 4),
            "lower_1std": round(lower_1std, 4),
            "upper_2std": round(upper_2std, 4),
            "lower_2std": round(lower_2std, 4)
        }
    
    def _analyze_anchored_vwap_behavior(self, vwap: pd.Series) -> Dict[str, Any]:
        """Analyze anchored VWAP behavior patterns."""
        # VWAP should typically trend with the overall price movement
        vwap_changes = vwap.diff().dropna()
        
        # Direction consistency
        positive_changes = sum(1 for x in vwap_changes if x > 0)
        negative_changes = sum(1 for x in vwap_changes if x < 0)
        total_changes = len(vwap_changes)
        
        if total_changes > 0:
            direction_consistency = max(positive_changes, negative_changes) / total_changes
        else:
            direction_consistency = 0.5
        
        # VWAP momentum
        vwap_momentum = self._calculate_velocity(vwap, 3)
        
        # Reset behavior (if VWAP appears to have reset/anchored)
        reset_detected = self._detect_vwap_reset(vwap)
        
        return {
            "direction_consistency": round(direction_consistency, 3),
            "momentum": round(vwap_momentum, 6),
            "reset_detected": reset_detected,
            "behavior_quality": "stable" if direction_consistency > 0.7 else "choppy"
        }
    
    def _detect_vwap_reset(self, vwap: pd.Series) -> bool:
        """Detect if VWAP appears to have been reset (new session)."""
        if len(vwap) < 10:
            return False
        
        # Look for significant jumps that might indicate reset
        vwap_changes = vwap.diff().dropna()
        change_threshold = vwap.std() * 2  # 2 standard deviations
        
        significant_jumps = sum(1 for change in vwap_changes if abs(change) > change_threshold)
        
        # If we see significant jumps, might indicate resets
        return significant_jumps > 0
    
    def _generate_vwap_signals(self, vwap_value: float, price: float,
                              price_relationship: Dict, fair_value_analysis: Dict,
                              support_resistance: Dict) -> List[Dict[str, Any]]:
        """Generate VWAP trading signals."""
        signals = []
        
        # Fair value signals
        fair_value = fair_value_analysis.get("current_assessment", "fairly_valued")
        distance_pct = abs(fair_value_analysis.get("distance_from_fair_value_pct", 0))
        
        if fair_value == "overvalued" and distance_pct > 3:
            signals.append({
                "type": "mean_reversion_sell",
                "strength": "strong",
                "reason": f"Price {distance_pct:.1f}% above VWAP fair value",
                "confidence": 0.8
            })
        elif fair_value == "undervalued" and distance_pct > 3:
            signals.append({
                "type": "mean_reversion_buy",
                "strength": "strong",
                "reason": f"Price {distance_pct:.1f}% below VWAP fair value",
                "confidence": 0.8
            })
        
        # Position-based signals
        position = price_relationship.get("position", "at_level")
        bias = price_relationship.get("bias", "neutral")
        
        if position == "above" and bias == "bullish":
            signals.append({
                "type": "bullish_above_vwap",
                "strength": "medium",
                "reason": "Price trading above VWAP - bullish institutional bias",
                "confidence": 0.6
            })
        elif position == "below" and bias == "bearish":
            signals.append({
                "type": "bearish_below_vwap",
                "strength": "medium", 
                "reason": "Price trading below VWAP - bearish institutional bias",
                "confidence": 0.6
            })
        
        # Support/resistance signals
        effectiveness = support_resistance.get("effectiveness", "low")
        recent_bounces = support_resistance.get("recent_bounces", [])
        
        if recent_bounces and effectiveness in ["high", "medium"]:
            latest_bounce = recent_bounces[-1]
            if latest_bounce["periods_ago"] <= 3:
                bounce_type = latest_bounce["type"]
                signal_type = "support_bounce_buy" if "support" in bounce_type else "resistance_bounce_sell"
                
                signals.append({
                    "type": signal_type,
                    "strength": "medium",
                    "reason": f"Recent VWAP {bounce_type} {latest_bounce['periods_ago']} periods ago",
                    "confidence": 0.7 if effectiveness == "high" else 0.6
                })
        
        return signals
    
    def _calculate_vwap_confidence(self, vwap: pd.Series, prices: pd.Series,
                                  volume_profile: Dict, trend_analysis: Dict) -> float:
        """Calculate VWAP analysis confidence."""
        confidence_factors = []
        
        # Data quantity factor
        data_factor = min(1.0, len(vwap) / 30)
        confidence_factors.append(data_factor)
        
        # VWAP smoothness factor (smoother = more reliable)
        smoothness = trend_analysis.get("smoothness", 0.5)
        confidence_factors.append(smoothness)
        
        # Volume data availability
        if volume_profile:
            confidence_factors.append(0.8)  # Higher confidence with volume data
            
            # Institutional activity factor
            institutional_activity = volume_profile.get("institutional_activity", "low")
            if institutional_activity == "high":
                confidence_factors.append(0.9)
            elif institutional_activity == "medium":
                confidence_factors.append(0.7)
            else:
                confidence_factors.append(0.5)
        else:
            confidence_factors.append(0.6)  # Lower without volume data
        
        # Price-VWAP relationship clarity
        distance_pct = abs(((prices.iloc[-1] - vwap.iloc[-1]) / vwap.iloc[-1]) * 100)
        if distance_pct > 2:
            clarity_factor = 0.8  # Clear deviation
        elif distance_pct > 0.5:
            clarity_factor = 0.7
        else:
            clarity_factor = 0.6  # Near fair value
        confidence_factors.append(clarity_factor)
        
        return round(np.mean(confidence_factors), 3)
    
    def _generate_vwap_summary(self, vwap_value: float, price: float,
                              price_relationship: Dict, fair_value_analysis: Dict) -> str:
        """Generate human-readable VWAP summary."""
        position = price_relationship.get("position", "at_level")
        distance_pct = price_relationship.get("distance_pct", 0)
        fair_value = fair_value_analysis.get("current_assessment", "fairly_valued")
        
        summary = f"VWAP {vwap_value:.4f}, price {position}"
        
        if abs(distance_pct) > 0.5:
            summary += f" ({distance_pct:+.1f}%)"
        
        summary += f" - {fair_value.replace('_', ' ')}"
        
        return summary