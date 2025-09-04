"""
Bollinger Bands Preprocessor.

Advanced Bollinger Bands preprocessing with squeeze analysis, bandwidth tracking,
%B position analysis, and volatility breakout detection.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePreprocessor


class BollingerBandsPreprocessor(BasePreprocessor):
    """Advanced Bollinger Bands preprocessor with professional-grade analysis."""
    
    def preprocess(self, upper_band: pd.Series, middle_band: pd.Series, lower_band: pd.Series,
                  prices: pd.Series, **kwargs) -> Dict[str, Any]:
        """
        Advanced Bollinger Bands preprocessing with comprehensive analysis.
        
        Args:
            upper_band: Upper Bollinger Band values
            middle_band: Middle Bollinger Band values (SMA)
            lower_band: Lower Bollinger Band values  
            prices: Price series for position analysis
            
        Returns:
            Dictionary with comprehensive Bollinger Bands analysis
        """
        if len(upper_band) < 5 or len(prices) < 5:
            return {"error": "Insufficient data for Bollinger Bands analysis"}
        
        current_price = float(prices.iloc[-1])
        current_upper = float(upper_band.iloc[-1])
        current_middle = float(middle_band.iloc[-1])
        current_lower = float(lower_band.iloc[-1])
        
        # Position analysis (%B calculation)
        position_analysis = self._analyze_price_position(prices, upper_band, middle_band, lower_band)
        
        # Bandwidth analysis
        bandwidth_analysis = self._analyze_bandwidth(upper_band, middle_band, lower_band)
        
        # Squeeze analysis
        squeeze_analysis = self._analyze_squeeze_conditions(upper_band, lower_band, middle_band)
        
        # Band touching analysis
        band_touch_analysis = self._analyze_band_touches(prices, upper_band, lower_band)
        
        # Volatility analysis
        volatility_analysis = self._analyze_volatility_patterns(upper_band, lower_band, middle_band)
        
        # Trend analysis
        trend_analysis = self._analyze_trend_with_bands(prices, middle_band)
        
        # Pattern analysis
        pattern_analysis = self._analyze_bollinger_patterns(prices, upper_band, middle_band, lower_band)
        
        # Signal generation
        signals = self._generate_bollinger_signals(current_price, current_upper, current_middle, current_lower,
                                                  position_analysis, squeeze_analysis, band_touch_analysis)
        
        # Confidence calculation
        confidence = self._calculate_bollinger_confidence(position_analysis, bandwidth_analysis, squeeze_analysis)
        
        return {
            "indicator": "Bollinger_Bands",
            "current": {
                "price": round(current_price, 4),
                "upper_band": round(current_upper, 4),
                "middle_band": round(current_middle, 4),
                "lower_band": round(current_lower, 4),
                "bandwidth": round((current_upper - current_lower) / current_middle * 100, 2),
                "percent_b": round((current_price - current_lower) / (current_upper - current_lower), 3),
                "timestamp": datetime.now().isoformat()
            },
            "position": position_analysis,
            "bandwidth": bandwidth_analysis,
            "squeeze": squeeze_analysis,
            "band_touches": band_touch_analysis,
            "volatility": volatility_analysis,
            "trend": trend_analysis,
            "patterns": pattern_analysis,
            "signals": signals,
            "confidence": confidence,
            "summary": self._generate_bollinger_summary(current_price, current_upper, current_middle, 
                                                       current_lower, position_analysis, squeeze_analysis)
        }
    
    def _analyze_price_position(self, prices: pd.Series, upper_band: pd.Series, 
                               middle_band: pd.Series, lower_band: pd.Series) -> Dict[str, Any]:
        """Analyze price position relative to Bollinger Bands."""
        current_price = prices.iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_middle = middle_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        
        # %B calculation
        percent_b = (current_price - current_lower) / (current_upper - current_lower)
        
        # Position classification
        if percent_b > 1.0:
            position = "above_upper"
        elif percent_b > 0.8:
            position = "near_upper"
        elif percent_b > 0.5:
            position = "upper_half"
        elif percent_b > 0.2:
            position = "lower_half"
        elif percent_b >= 0:
            position = "near_lower"
        else:
            position = "below_lower"
        
        # %B momentum
        if len(prices) >= 5:
            prev_percent_b = ((prices.iloc[-5] - lower_band.iloc[-5]) / 
                             (upper_band.iloc[-5] - lower_band.iloc[-5]))
            percent_b_change = percent_b - prev_percent_b
        else:
            percent_b_change = 0
        
        # Distance from middle
        distance_from_middle = current_price - current_middle
        distance_pct = (distance_from_middle / current_middle) * 100
        
        # Position history analysis
        position_history = self._analyze_position_history(prices, upper_band, middle_band, lower_band)
        
        return {
            "percent_b": round(percent_b, 3),
            "position": position,
            "percent_b_change_5p": round(percent_b_change, 3),
            "distance_from_middle": round(distance_from_middle, 4),
            "distance_from_middle_pct": round(distance_pct, 3),
            "position_history": position_history
        }
    
    def _analyze_position_history(self, prices: pd.Series, upper_band: pd.Series, 
                                 middle_band: pd.Series, lower_band: pd.Series) -> Dict[str, Any]:
        """Analyze historical price position within bands."""
        if len(prices) < 20:
            return {"insufficient_data": True}
        
        # Calculate %B for all periods
        percent_b_series = (prices - lower_band) / (upper_band - lower_band)
        
        # Time spent in different zones
        above_upper = sum(1 for b in percent_b_series if b > 1.0)
        below_lower = sum(1 for b in percent_b_series if b < 0.0)
        upper_half = sum(1 for b in percent_b_series if 0.5 <= b <= 1.0)
        lower_half = sum(1 for b in percent_b_series if 0.0 <= b < 0.5)
        
        total_periods = len(percent_b_series)
        
        return {
            "above_upper_pct": round((above_upper / total_periods) * 100, 1),
            "below_lower_pct": round((below_lower / total_periods) * 100, 1),
            "upper_half_pct": round((upper_half / total_periods) * 100, 1),
            "lower_half_pct": round((lower_half / total_periods) * 100, 1),
            "avg_percent_b": round(percent_b_series.mean(), 3),
            "percent_b_volatility": round(percent_b_series.std(), 3)
        }
    
    def _analyze_bandwidth(self, upper_band: pd.Series, middle_band: pd.Series, lower_band: pd.Series) -> Dict[str, Any]:
        """Analyze Bollinger Band bandwidth."""
        bandwidth = (upper_band - lower_band) / middle_band * 100
        current_bandwidth = bandwidth.iloc[-1]
        
        # Bandwidth statistics
        mean_bandwidth = bandwidth.mean()
        std_bandwidth = bandwidth.std()
        max_bandwidth = bandwidth.max()
        min_bandwidth = bandwidth.min()
        
        # Bandwidth percentile
        bandwidth_percentile = self._calculate_position_rank(bandwidth, lookback=len(bandwidth))
        
        # Bandwidth trend
        bandwidth_velocity = self._calculate_velocity(bandwidth, 3)
        
        # Bandwidth classification
        if current_bandwidth > mean_bandwidth + std_bandwidth:
            bandwidth_level = "high"
        elif current_bandwidth > mean_bandwidth:
            bandwidth_level = "above_average"
        elif current_bandwidth < mean_bandwidth - std_bandwidth:
            bandwidth_level = "low"
        else:
            bandwidth_level = "below_average"
        
        return {
            "current": round(current_bandwidth, 2),
            "level": bandwidth_level,
            "percentile": round(bandwidth_percentile, 1),
            "velocity": round(bandwidth_velocity, 3),
            "statistics": {
                "mean": round(mean_bandwidth, 2),
                "std": round(std_bandwidth, 2),
                "max": round(max_bandwidth, 2),
                "min": round(min_bandwidth, 2)
            },
            "trend": "expanding" if bandwidth_velocity > 0.1 else "contracting" if bandwidth_velocity < -0.1 else "stable"
        }
    
    def _analyze_squeeze_conditions(self, upper_band: pd.Series, lower_band: pd.Series, middle_band: pd.Series) -> Dict[str, Any]:
        """Analyze Bollinger Band squeeze conditions."""
        bandwidth = (upper_band - lower_band) / middle_band * 100
        current_bandwidth = bandwidth.iloc[-1]
        
        # Squeeze threshold (typically 20-period low bandwidth)
        if len(bandwidth) >= 20:
            squeeze_threshold = bandwidth.rolling(20).min().iloc[-1]
            is_squeeze = current_bandwidth <= squeeze_threshold * 1.05  # 5% tolerance
        else:
            # Fallback: use statistical method
            mean_bandwidth = bandwidth.mean()
            std_bandwidth = bandwidth.std()
            squeeze_threshold = mean_bandwidth - std_bandwidth
            is_squeeze = current_bandwidth <= squeeze_threshold
        
        # Squeeze duration
        squeeze_periods = 0
        if is_squeeze:
            for i in range(len(bandwidth) - 1, -1, -1):
                if bandwidth.iloc[i] <= squeeze_threshold * 1.05:
                    squeeze_periods += 1
                else:
                    break
        
        # Post-squeeze expansion potential
        if squeeze_periods > 0:
            expansion_potential = min(1.0, squeeze_periods / 10)  # Max at 10 periods
        else:
            expansion_potential = 0.0
        
        # Recent bandwidth change
        if len(bandwidth) >= 5:
            recent_change = ((bandwidth.iloc[-1] / bandwidth.iloc[-5]) - 1) * 100
        else:
            recent_change = 0.0
        
        return {
            "is_squeeze": is_squeeze,
            "squeeze_periods": squeeze_periods,
            "squeeze_threshold": round(squeeze_threshold, 2),
            "expansion_potential": round(expansion_potential, 3),
            "recent_bandwidth_change_pct": round(recent_change, 2),
            "squeeze_quality": self._assess_squeeze_quality(squeeze_periods, current_bandwidth, squeeze_threshold)
        }
    
    def _assess_squeeze_quality(self, periods: int, current_bw: float, threshold: float) -> str:
        """Assess quality of squeeze for breakout potential."""
        if periods >= 8 and current_bw < threshold * 0.9:
            return "excellent"
        elif periods >= 5 and current_bw < threshold:
            return "good"
        elif periods >= 3:
            return "moderate"
        else:
            return "weak"
    
    def _analyze_band_touches(self, prices: pd.Series, upper_band: pd.Series, lower_band: pd.Series) -> Dict[str, Any]:
        """Analyze price touches of upper and lower bands."""
        touches = []
        
        # Define touch as price within 1% of band
        touch_threshold = 0.01
        
        for i in range(len(prices)):
            price = prices.iloc[i]
            upper = upper_band.iloc[i]
            lower = lower_band.iloc[i]
            
            # Upper band touch
            if abs(price - upper) / upper <= touch_threshold:
                touches.append({
                    "index": i,
                    "type": "upper",
                    "price": price,
                    "band_value": upper,
                    "periods_ago": len(prices) - 1 - i
                })
            
            # Lower band touch
            elif abs(price - lower) / lower <= touch_threshold:
                touches.append({
                    "index": i,
                    "type": "lower",
                    "price": price,
                    "band_value": lower,
                    "periods_ago": len(prices) - 1 - i
                })
        
        # Recent touches (last 10 periods)
        recent_touches = [t for t in touches if t["periods_ago"] <= 10]
        
        # Touch frequency analysis
        upper_touches = [t for t in touches if t["type"] == "upper"]
        lower_touches = [t for t in touches if t["type"] == "lower"]
        
        return {
            "recent_touches": recent_touches[-5:],  # Last 5 touches
            "total_touches": len(touches),
            "upper_touches": len(upper_touches),
            "lower_touches": len(lower_touches),
            "latest_touch": touches[-1] if touches else None,
            "touch_frequency": len(touches) / len(prices) if len(prices) > 0 else 0
        }
    
    def _analyze_volatility_patterns(self, upper_band: pd.Series, lower_band: pd.Series, middle_band: pd.Series) -> Dict[str, Any]:
        """Analyze volatility patterns using band width."""
        bandwidth = (upper_band - lower_band) / middle_band * 100
        
        if len(bandwidth) < 10:
            return {}
        
        # Volatility cycles
        peaks = self._find_peaks(bandwidth, prominence=bandwidth.std() * 0.5)
        troughs = self._find_troughs(bandwidth, prominence=bandwidth.std() * 0.5)
        
        # Current volatility state
        current_bw = bandwidth.iloc[-1]
        recent_peak = peaks[-1] if peaks else None
        recent_trough = troughs[-1] if troughs else None
        
        if recent_peak and recent_trough:
            if recent_peak["index"] > recent_trough["index"]:
                volatility_state = "post_expansion"
            else:
                volatility_state = "post_contraction"
        else:
            volatility_state = "unclear"
        
        # Volatility regime
        long_term_avg = bandwidth.mean()
        if current_bw > long_term_avg * 1.5:
            regime = "high_volatility"
        elif current_bw < long_term_avg * 0.5:
            regime = "low_volatility"
        else:
            regime = "normal_volatility"
        
        return {
            "current_state": volatility_state,
            "regime": regime,
            "peaks_count": len(peaks),
            "troughs_count": len(troughs),
            "regime_ratio": round(current_bw / long_term_avg, 2)
        }
    
    def _analyze_trend_with_bands(self, prices: pd.Series, middle_band: pd.Series) -> Dict[str, Any]:
        """Analyze trend using middle band (SMA) as reference."""
        current_price = prices.iloc[-1]
        current_middle = middle_band.iloc[-1]
        
        # Price vs middle band
        price_vs_middle = "above" if current_price > current_middle else "below"
        distance_pct = ((current_price - current_middle) / current_middle) * 100
        
        # Middle band slope (trend)
        if len(middle_band) >= 5:
            middle_slope = self._calculate_velocity(middle_band, 5)
            if middle_slope > 0:
                middle_trend = "rising"
            elif middle_slope < 0:
                middle_trend = "falling"
            else:
                middle_trend = "flat"
        else:
            middle_slope = 0
            middle_trend = "insufficient_data"
        
        # Trend strength
        trend_strength = min(1.0, abs(distance_pct) / 5)  # Normalize to 5% distance
        
        return {
            "price_vs_middle": price_vs_middle,
            "distance_pct": round(distance_pct, 2),
            "middle_trend": middle_trend,
            "middle_slope": round(middle_slope, 6),
            "trend_strength": round(trend_strength, 3)
        }
    
    def _analyze_bollinger_patterns(self, prices: pd.Series, upper_band: pd.Series, 
                                   middle_band: pd.Series, lower_band: pd.Series) -> Dict[str, Any]:
        """Analyze Bollinger Band patterns."""
        patterns = {}
        
        if len(prices) >= 10:
            # Walking the bands pattern
            walking_pattern = self._detect_walking_bands(prices, upper_band, lower_band)
            if walking_pattern:
                patterns["walking_bands"] = walking_pattern
            
            # Double Bollinger pattern
            double_pattern = self._detect_double_bollinger_touch(prices, upper_band, lower_band)
            if double_pattern:
                patterns["double_touch"] = double_pattern
        
        return patterns
    
    def _detect_walking_bands(self, prices: pd.Series, upper_band: pd.Series, lower_band: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect walking the bands pattern (sustained move along one band)."""
        if len(prices) < 8:
            return None
        
        recent_prices = prices.iloc[-8:]
        recent_upper = upper_band.iloc[-8:]
        recent_lower = lower_band.iloc[-8:]
        
        # Check for walking upper band
        upper_proximity = 0
        for i in range(len(recent_prices)):
            price = recent_prices.iloc[i]
            upper = recent_upper.iloc[i]
            if (price - upper) / upper > -0.05:  # Within 5% of upper band
                upper_proximity += 1
        
        # Check for walking lower band
        lower_proximity = 0
        for i in range(len(recent_prices)):
            price = recent_prices.iloc[i]
            lower = recent_lower.iloc[i]
            if (lower - price) / lower < 0.05:  # Within 5% of lower band
                lower_proximity += 1
        
        if upper_proximity >= 5:
            return {
                "type": "walking_upper_band",
                "periods": upper_proximity,
                "description": f"Price walking upper band for {upper_proximity} periods"
            }
        elif lower_proximity >= 5:
            return {
                "type": "walking_lower_band", 
                "periods": lower_proximity,
                "description": f"Price walking lower band for {lower_proximity} periods"
            }
        
        return None
    
    def _detect_double_bollinger_touch(self, prices: pd.Series, upper_band: pd.Series, lower_band: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect double touch of same band (reversal pattern)."""
        if len(prices) < 15:
            return None
        
        # Get recent band touches
        band_touches = self._analyze_band_touches(prices, upper_band, lower_band)
        recent_touches = band_touches["recent_touches"]
        
        if len(recent_touches) >= 2:
            # Check for double touch of same band
            last_two = recent_touches[-2:]
            if (last_two[0]["type"] == last_two[1]["type"] and 
                last_two[1]["periods_ago"] <= 3):
                
                return {
                    "type": f"double_{last_two[0]['type']}_touch",
                    "description": f"Double touch of {last_two[0]['type']} band",
                    "periods_between": abs(last_two[0]["periods_ago"] - last_two[1]["periods_ago"])
                }
        
        return None
    
    def _generate_bollinger_signals(self, price: float, upper: float, middle: float, lower: float,
                                   position_analysis: Dict, squeeze_analysis: Dict, 
                                   band_touch_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate Bollinger Band signals."""
        signals = []
        
        # Position-based signals
        percent_b = position_analysis["percent_b"]
        position = position_analysis["position"]
        
        if position == "above_upper":
            signals.append({
                "type": "overbought_signal",
                "strength": "medium",
                "reason": f"Price above upper band (%B: {percent_b:.2f})",
                "confidence": 0.7
            })
        elif position == "below_lower":
            signals.append({
                "type": "oversold_signal",
                "strength": "medium", 
                "reason": f"Price below lower band (%B: {percent_b:.2f})",
                "confidence": 0.7
            })
        
        # Squeeze signals
        if squeeze_analysis["is_squeeze"]:
            squeeze_quality = squeeze_analysis["squeeze_quality"]
            if squeeze_quality in ["excellent", "good"]:
                signals.append({
                    "type": "squeeze_breakout_setup",
                    "strength": "medium",
                    "reason": f"{squeeze_quality.title()} squeeze for {squeeze_analysis['squeeze_periods']} periods",
                    "confidence": 0.8 if squeeze_quality == "excellent" else 0.7
                })
        
        # Band touch signals
        latest_touch = band_touch_analysis.get("latest_touch")
        if latest_touch and latest_touch["periods_ago"] <= 2:
            touch_type = latest_touch["type"]
            signals.append({
                "type": f"{touch_type}_band_touch",
                "strength": "low",
                "reason": f"Recent {touch_type} band touch {latest_touch['periods_ago']} periods ago",
                "confidence": 0.6
            })
        
        # %B momentum signals
        percent_b_change = position_analysis["percent_b_change_5p"]
        if abs(percent_b_change) > 0.3:
            direction = "bullish" if percent_b_change > 0 else "bearish"
            signals.append({
                "type": f"percent_b_momentum_{direction}",
                "strength": "low",
                "reason": f"%B moving {direction}ly ({percent_b_change:+.2f} over 5 periods)",
                "confidence": 0.5
            })
        
        return signals
    
    def _calculate_bollinger_confidence(self, position_analysis: Dict, bandwidth_analysis: Dict, 
                                       squeeze_analysis: Dict) -> float:
        """Calculate Bollinger Bands analysis confidence."""
        confidence_factors = []
        
        # Position clarity factor
        percent_b = abs(position_analysis["percent_b"] - 0.5)  # Distance from center
        position_clarity = min(1.0, percent_b * 2)  # Max when %B is 0 or 1
        confidence_factors.append(position_clarity)
        
        # Bandwidth factor (higher bandwidth = more reliable signals)
        bandwidth_percentile = bandwidth_analysis["percentile"]
        bandwidth_factor = bandwidth_percentile / 100
        confidence_factors.append(bandwidth_factor)
        
        # Squeeze factor (squeezes increase breakout confidence)
        if squeeze_analysis["is_squeeze"]:
            squeeze_quality = squeeze_analysis["squeeze_quality"]
            quality_scores = {"excellent": 0.9, "good": 0.7, "moderate": 0.5, "weak": 0.3}
            confidence_factors.append(quality_scores.get(squeeze_quality, 0.3))
        else:
            confidence_factors.append(0.6)  # Neutral for non-squeeze
        
        return round(np.mean(confidence_factors), 3)
    
    def _generate_bollinger_summary(self, price: float, upper: float, middle: float, lower: float,
                                   position_analysis: Dict, squeeze_analysis: Dict) -> str:
        """Generate human-readable Bollinger Bands summary."""
        percent_b = position_analysis["percent_b"]
        position = position_analysis["position"]
        bandwidth = (upper - lower) / middle * 100
        
        summary = f"BB: Price {price:.4f}, %B {percent_b:.2f} ({position.replace('_', ' ')})"
        summary += f", BW {bandwidth:.2f}%"
        
        if squeeze_analysis["is_squeeze"]:
            squeeze_periods = squeeze_analysis["squeeze_periods"]
            summary += f" - SQUEEZE ({squeeze_periods}p)"
        
        return summary