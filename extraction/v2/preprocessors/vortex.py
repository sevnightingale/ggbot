"""
Vortex Preprocessor.

Advanced Vortex preprocessing with directional movement analysis,
VI+ and VI- crossover detection, and trend strength assessment.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePreprocessor


class VortexPreprocessor(BasePreprocessor):
    """Advanced Vortex preprocessor with professional-grade directional analysis."""
    
    def preprocess(self, vi_plus: pd.Series, vi_minus: pd.Series, 
                  prices: pd.Series = None, length: int = 14, **kwargs) -> Dict[str, Any]:
        """
        Advanced Vortex preprocessing with comprehensive directional movement analysis.
        
        Vortex Indicator consists of two lines: VI+ and VI- that measure
        the relationship between closing prices and true ranges to identify
        trend changes and directional movement.
        
        Args:
            vi_plus: VI+ values (positive vortex movement)
            vi_minus: VI- values (negative vortex movement)  
            prices: Price series for additional analysis (optional)
            length: Vortex calculation period
            
        Returns:
            Dictionary with comprehensive Vortex analysis
        """
        if len(vi_plus) < 5 or len(vi_minus) < 5:
            return {"error": "Insufficient data for Vortex analysis"}
        
        current_vi_plus = float(vi_plus.iloc[-1])
        current_vi_minus = float(vi_minus.iloc[-1])
        
        # Crossover analysis
        crossover_analysis = self._analyze_vortex_crossovers(vi_plus, vi_minus)
        
        # Directional dominance analysis
        dominance_analysis = self._analyze_directional_dominance(vi_plus, vi_minus)
        
        # Spread analysis
        spread_analysis = self._analyze_vortex_spread(vi_plus, vi_minus)
        
        # Trend strength analysis
        trend_strength = self._analyze_vortex_trend_strength(vi_plus, vi_minus)
        
        # Momentum analysis
        momentum_analysis = self._analyze_vortex_momentum(vi_plus, vi_minus)
        
        # One-line analysis (threshold levels)
        one_line_analysis = self._analyze_one_line_levels(vi_plus, vi_minus)
        
        # Divergence analysis
        divergence = None
        if prices is not None:
            divergence = self._detect_vortex_price_divergence(vi_plus, vi_minus, prices)
        
        # Pattern analysis
        pattern_analysis = self._analyze_vortex_patterns(vi_plus, vi_minus)
        
        # Signal generation
        signals = self._generate_vortex_signals(current_vi_plus, current_vi_minus, crossover_analysis,
                                              dominance_analysis, trend_strength)
        
        # Confidence calculation
        confidence = self._calculate_vortex_confidence(vi_plus, vi_minus, crossover_analysis, spread_analysis)
        
        return {
            "indicator": "Vortex",
            "current": {
                "vi_plus": round(current_vi_plus, 4),
                "vi_minus": round(current_vi_minus, 4),
                "spread": round(current_vi_plus - current_vi_minus, 4),
                "dominant": "VI+" if current_vi_plus > current_vi_minus else "VI-",
                "timestamp": datetime.now().isoformat()
            },
            "crossovers": crossover_analysis,
            "dominance": dominance_analysis,
            "spread": spread_analysis,
            "trend_strength": trend_strength,
            "momentum": momentum_analysis,
            "one_line_levels": one_line_analysis,
            "divergence": divergence,
            "patterns": pattern_analysis,
            "signals": signals,
            "confidence": confidence,
            "summary": self._generate_vortex_summary(current_vi_plus, current_vi_minus, crossover_analysis, dominance_analysis)
        }
    
    def _analyze_vortex_crossovers(self, vi_plus: pd.Series, vi_minus: pd.Series) -> Dict[str, Any]:
        """Analyze VI+/VI- crossovers."""
        crossovers = []
        
        for i in range(1, min(20, len(vi_plus))):
            prev_plus = vi_plus.iloc[-(i+1)]
            curr_plus = vi_plus.iloc[-i]
            prev_minus = vi_minus.iloc[-(i+1)]
            curr_minus = vi_minus.iloc[-i]
            
            # Bullish crossover (VI+ crosses above VI-)
            if prev_plus <= prev_minus and curr_plus > curr_minus:
                crossovers.append({
                    "type": "bullish_crossover",
                    "periods_ago": i,
                    "vi_plus": round(curr_plus, 4),
                    "vi_minus": round(curr_minus, 4),
                    "strength": curr_plus - curr_minus,
                    "crossover_level": round((curr_plus + curr_minus) / 2, 4)
                })
            
            # Bearish crossover (VI+ crosses below VI-)
            elif prev_plus >= prev_minus and curr_plus < curr_minus:
                crossovers.append({
                    "type": "bearish_crossover",
                    "periods_ago": i,
                    "vi_plus": round(curr_plus, 4),
                    "vi_minus": round(curr_minus, 4),
                    "strength": curr_minus - curr_plus,
                    "crossover_level": round((curr_plus + curr_minus) / 2, 4)
                })
        
        return {
            "recent_crossovers": crossovers[:5],
            "latest_crossover": crossovers[0] if crossovers else None,
            "crossover_frequency": len(crossovers) / min(20, len(vi_plus)) if len(vi_plus) > 0 else 0
        }
    
    def _analyze_directional_dominance(self, vi_plus: pd.Series, vi_minus: pd.Series) -> Dict[str, Any]:
        """Analyze which direction is dominant."""
        current_plus = vi_plus.iloc[-1]
        current_minus = vi_minus.iloc[-1]
        
        # Current dominance
        if current_plus > current_minus:
            current_dominant = "VI_plus"
            dominance_strength = current_plus - current_minus
        else:
            current_dominant = "VI_minus"
            dominance_strength = current_minus - current_plus
        
        # Historical dominance
        plus_dominant_periods = sum(1 for i in range(len(vi_plus)) if vi_plus.iloc[i] > vi_minus.iloc[i])
        minus_dominant_periods = len(vi_plus) - plus_dominant_periods
        total_periods = len(vi_plus)
        
        # Dominance persistence
        persistence = self._calculate_dominance_persistence(vi_plus, vi_minus)
        
        # Average dominance strength
        spreads = vi_plus - vi_minus
        avg_spread = spreads.mean()
        max_spread = spreads.max()
        min_spread = spreads.min()
        
        return {
            "current_dominant": current_dominant,
            "dominance_strength": round(dominance_strength, 4),
            "vi_plus_dominant_pct": round((plus_dominant_periods / total_periods) * 100, 1),
            "vi_minus_dominant_pct": round((minus_dominant_periods / total_periods) * 100, 1),
            "persistence": round(persistence, 3),
            "avg_spread": round(avg_spread, 4),
            "max_spread": round(max_spread, 4),
            "min_spread": round(min_spread, 4)
        }
    
    def _calculate_dominance_persistence(self, vi_plus: pd.Series, vi_minus: pd.Series) -> float:
        """Calculate persistence of current dominance."""
        if len(vi_plus) < 5:
            return 0.5
        
        current_dominant = "plus" if vi_plus.iloc[-1] > vi_minus.iloc[-1] else "minus"
        recent_periods = min(5, len(vi_plus))
        
        consistent_periods = 0
        for i in range(recent_periods):
            idx = -(i + 1)
            period_dominant = "plus" if vi_plus.iloc[idx] > vi_minus.iloc[idx] else "minus"
            if period_dominant == current_dominant:
                consistent_periods += 1
        
        return consistent_periods / recent_periods
    
    def _analyze_vortex_spread(self, vi_plus: pd.Series, vi_minus: pd.Series) -> Dict[str, Any]:
        """Analyze spread between VI+ and VI-."""
        spread = vi_plus - vi_minus
        current_spread = spread.iloc[-1]
        
        # Spread statistics
        mean_spread = spread.mean()
        std_spread = spread.std()
        
        # Spread classification
        if abs(current_spread) > abs(mean_spread) + std_spread:
            spread_level = "extreme"
        elif abs(current_spread) > abs(mean_spread):
            spread_level = "elevated"
        else:
            spread_level = "normal"
        
        # Spread momentum
        spread_velocity = self._calculate_velocity(spread, 3)
        
        return {
            "current_spread": round(current_spread, 4),
            "mean_spread": round(mean_spread, 4),
            "std_spread": round(std_spread, 4),
            "spread_level": spread_level,
            "spread_momentum": round(spread_velocity, 6),
            "momentum_direction": "expanding" if spread_velocity > 0 and current_spread > 0 else "contracting" if spread_velocity < 0 and current_spread > 0 else "reversing" if spread_velocity != 0 else "stable"
        }
    
    def _analyze_vortex_trend_strength(self, vi_plus: pd.Series, vi_minus: pd.Series) -> Dict[str, Any]:
        """Analyze trend strength using Vortex indicators."""
        current_plus = vi_plus.iloc[-1] 
        current_minus = vi_minus.iloc[-1]
        
        # Trend direction
        if current_plus > current_minus:
            trend_direction = "bullish"
            strength_ratio = current_plus / current_minus if current_minus > 0 else 1
        else:
            trend_direction = "bearish"
            strength_ratio = current_minus / current_plus if current_plus > 0 else 1
        
        # Strength classification
        if strength_ratio > 1.2:
            strength_level = "strong"
        elif strength_ratio > 1.1:
            strength_level = "moderate"
        elif strength_ratio > 1.05:
            strength_level = "weak"
        else:
            strength_level = "very_weak"
        
        # Both indicators above 1.0 (strong trending market)
        both_above_one = current_plus > 1.0 and current_minus > 1.0
        
        return {
            "direction": trend_direction,
            "strength_ratio": round(strength_ratio, 4),
            "strength_level": strength_level,
            "both_above_one": both_above_one,
            "market_condition": "strong_trending" if both_above_one else "weak_trending"
        }
    
    def _analyze_vortex_momentum(self, vi_plus: pd.Series, vi_minus: pd.Series) -> Dict[str, Any]:
        """Analyze momentum of Vortex indicators."""
        if len(vi_plus) < 5:
            return {}
        
        # Individual momentum
        plus_momentum = self._calculate_velocity(vi_plus, 3)
        minus_momentum = self._calculate_velocity(vi_minus, 3)
        
        # Relative momentum
        if abs(plus_momentum) > abs(minus_momentum):
            dominant_momentum = "VI_plus"
        else:
            dominant_momentum = "VI_minus"
        
        # Momentum alignment
        if plus_momentum * minus_momentum > 0:
            momentum_alignment = "aligned"
        else:
            momentum_alignment = "divergent"
        
        return {
            "vi_plus_momentum": round(plus_momentum, 6),
            "vi_minus_momentum": round(minus_momentum, 6),
            "dominant_momentum": dominant_momentum,
            "momentum_alignment": momentum_alignment,
            "momentum_interpretation": self._interpret_momentum_alignment(momentum_alignment, plus_momentum, minus_momentum)
        }
    
    def _interpret_momentum_alignment(self, alignment: str, plus_mom: float, minus_mom: float) -> str:
        """Interpret momentum alignment patterns."""
        if alignment == "aligned":
            if plus_mom > 0 and minus_mom > 0:
                return "both_strengthening"
            elif plus_mom < 0 and minus_mom < 0:
                return "both_weakening"
            else:
                return "both_stable"
        else:
            if plus_mom > 0 and minus_mom < 0:
                return "vi_plus_strengthening_minus_weakening"
            elif plus_mom < 0 and minus_mom > 0:
                return "vi_minus_strengthening_plus_weakening"
            else:
                return "mixed_momentum"
    
    def _analyze_one_line_levels(self, vi_plus: pd.Series, vi_minus: pd.Series) -> Dict[str, Any]:
        """Analyze behavior around 1.0 threshold levels."""
        current_plus = vi_plus.iloc[-1]
        current_minus = vi_minus.iloc[-1]
        
        # Current position relative to 1.0
        plus_vs_one = "above" if current_plus > 1.0 else "below" if current_plus < 1.0 else "at"
        minus_vs_one = "above" if current_minus > 1.0 else "below" if current_minus < 1.0 else "at"
        
        # Time above 1.0
        plus_above_one = sum(1 for val in vi_plus if val > 1.0)
        minus_above_one = sum(1 for val in vi_minus if val > 1.0)
        total_periods = len(vi_plus)
        
        # Recent crossings of 1.0 level
        plus_one_crosses = self._find_level_crossings(vi_plus, 1.0)
        minus_one_crosses = self._find_level_crossings(vi_minus, 1.0)
        
        return {
            "vi_plus_vs_one": plus_vs_one,
            "vi_minus_vs_one": minus_vs_one,
            "plus_above_one_pct": round((plus_above_one / total_periods) * 100, 1),
            "minus_above_one_pct": round((minus_above_one / total_periods) * 100, 1),
            "plus_one_crosses": plus_one_crosses[-3:] if plus_one_crosses else [],
            "minus_one_crosses": minus_one_crosses[-3:] if minus_one_crosses else []
        }
    
    def _find_level_crossings(self, series: pd.Series, level: float) -> List[Dict[str, Any]]:
        """Find crossings of a specific level."""
        crossings = []
        
        for i in range(1, min(10, len(series))):
            prev_val = series.iloc[-(i+1)]
            curr_val = series.iloc[-i]
            
            # Upward crossing
            if prev_val <= level and curr_val > level:
                crossings.append({
                    "type": "upward_cross",
                    "periods_ago": i,
                    "value": round(curr_val, 4)
                })
            # Downward crossing
            elif prev_val >= level and curr_val < level:
                crossings.append({
                    "type": "downward_cross",
                    "periods_ago": i,
                    "value": round(curr_val, 4)
                })
        
        return crossings
    
    def _detect_vortex_price_divergence(self, vi_plus: pd.Series, vi_minus: pd.Series, prices: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect Vortex-price divergence patterns."""
        if len(vi_plus) < 15 or len(prices) < 15:
            return None
        
        recent_periods = 10
        # Use the dominant VI for divergence analysis
        current_plus = vi_plus.iloc[-1]
        current_minus = vi_minus.iloc[-1]
        
        if current_plus > current_minus:
            vi_series = vi_plus.iloc[-recent_periods:]
        else:
            vi_series = vi_minus.iloc[-recent_periods:]
        
        price_recent = prices.iloc[-recent_periods:]
        
        # Find peaks and troughs
        vi_peaks = self._find_peaks(vi_series, prominence=0.05)
        vi_troughs = self._find_troughs(vi_series, prominence=0.05)
        price_peaks = self._find_peaks(price_recent)
        price_troughs = self._find_troughs(price_recent)
        
        # Bullish divergence
        if len(vi_troughs) >= 2 and len(price_troughs) >= 2:
            latest_vi_trough = vi_troughs[-1]
            prev_vi_trough = vi_troughs[-2]
            latest_price_trough = price_troughs[-1]
            prev_price_trough = price_troughs[-2]
            
            if (latest_price_trough["value"] < prev_price_trough["value"] and
                latest_vi_trough["value"] > prev_vi_trough["value"]):
                return {
                    "type": "bullish_divergence",
                    "confidence": 0.7,
                    "description": "Price making lower lows while Vortex making higher lows"
                }
        
        # Bearish divergence
        if len(vi_peaks) >= 2 and len(price_peaks) >= 2:
            latest_vi_peak = vi_peaks[-1]
            prev_vi_peak = vi_peaks[-2]
            latest_price_peak = price_peaks[-1]
            prev_price_peak = price_peaks[-2]
            
            if (latest_price_peak["value"] > prev_price_peak["value"] and 
                latest_vi_peak["value"] < prev_vi_peak["value"]):
                return {
                    "type": "bearish_divergence",
                    "confidence": 0.7,
                    "description": "Price making higher highs while Vortex making lower highs"
                }
        
        return None
    
    def _analyze_vortex_patterns(self, vi_plus: pd.Series, vi_minus: pd.Series) -> Dict[str, Any]:
        """Analyze Vortex patterns and formations."""
        patterns = {}
        
        if len(vi_plus) >= 15:
            # Compression/expansion patterns
            compression = self._detect_vortex_compression(vi_plus, vi_minus)
            if compression:
                patterns["compression"] = compression
            
            # Parallel movement
            parallel = self._detect_parallel_movement(vi_plus, vi_minus)
            if parallel:
                patterns["parallel_movement"] = parallel
        
        return patterns
    
    def _detect_vortex_compression(self, vi_plus: pd.Series, vi_minus: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect compression patterns (VI+ and VI- converging)."""
        spread = (vi_plus - vi_minus).abs()
        current_spread = spread.iloc[-1]
        avg_spread = spread.mean()
        
        if current_spread < avg_spread * 0.5:
            # Look at recent trend
            recent_spread = spread.iloc[-5:]
            if recent_spread.iloc[-1] < recent_spread.iloc[0]:
                return {
                    "type": "converging_compression",
                    "current_spread": round(current_spread, 4),
                    "avg_spread": round(avg_spread, 4),
                    "description": "VI+ and VI- converging - potential breakout setup"
                }
        
        return None
    
    def _detect_parallel_movement(self, vi_plus: pd.Series, vi_minus: pd.Series) -> Optional[Dict[str, Any]]:
        """Detect parallel movement patterns."""
        if len(vi_plus) < 8:
            return None
        
        recent_plus = vi_plus.iloc[-8:]
        recent_minus = vi_minus.iloc[-8:]
        
        plus_changes = recent_plus.diff().dropna()
        minus_changes = recent_minus.diff().dropna()
        
        if len(plus_changes) >= 3 and len(minus_changes) >= 3:
            correlation = np.corrcoef(plus_changes, minus_changes)[0, 1]
            
            if not np.isnan(correlation) and abs(correlation) > 0.7:
                return {
                    "type": "parallel_movement",
                    "correlation": round(correlation, 3),
                    "direction": "same" if correlation > 0 else "opposite",
                    "description": f"VI+ and VI- moving in {'same' if correlation > 0 else 'opposite'} direction"
                }
        
        return None
    
    def _generate_vortex_signals(self, vi_plus: float, vi_minus: float,
                               crossover_analysis: Dict, dominance_analysis: Dict,
                               trend_strength: Dict) -> List[Dict[str, Any]]:
        """Generate Vortex trading signals."""
        signals = []
        
        # Crossover signals
        latest_crossover = crossover_analysis.get("latest_crossover")
        if latest_crossover and latest_crossover["periods_ago"] <= 3:
            crossover_type = latest_crossover["type"]
            signal_type = "buy_signal" if "bullish" in crossover_type else "sell_signal"
            
            # Higher confidence for crossovers above 1.0
            crossover_level = latest_crossover["crossover_level"]
            confidence = 0.8 if crossover_level > 1.0 else 0.6
            
            signals.append({
                "type": signal_type,
                "strength": "strong" if crossover_level > 1.0 else "medium",
                "reason": f"VI {crossover_type.replace('_', ' ')} at {crossover_level:.3f} level",
                "confidence": confidence
            })
        
        # Trend strength signals
        strength_level = trend_strength.get("strength_level", "weak")
        market_condition = trend_strength.get("market_condition", "weak_trending")
        trend_direction = trend_strength.get("direction", "neutral")
        
        if strength_level in ["strong", "moderate"] and market_condition == "strong_trending":
            signal_type = "trend_following_buy" if trend_direction == "bullish" else "trend_following_sell"
            
            signals.append({
                "type": signal_type,
                "strength": "medium",
                "reason": f"Strong {trend_direction} trend with both VI indicators above 1.0",
                "confidence": 0.7
            })
        
        # Dominance persistence signals
        persistence = dominance_analysis.get("persistence", 0.5)
        current_dominant = dominance_analysis.get("current_dominant", "")
        
        if persistence > 0.8:
            direction = "buy" if "plus" in current_dominant else "sell"
            signals.append({
                "type": f"dominance_{direction}_signal",
                "strength": "low",
                "reason": f"Strong {current_dominant.replace('_', ' ')} dominance persistence",
                "confidence": 0.5
            })
        
        return signals
    
    def _calculate_vortex_confidence(self, vi_plus: pd.Series, vi_minus: pd.Series,
                                   crossover_analysis: Dict, spread_analysis: Dict) -> float:
        """Calculate Vortex analysis confidence."""
        confidence_factors = []
        
        # Data quantity factor
        data_factor = min(1.0, len(vi_plus) / 25)
        confidence_factors.append(data_factor)
        
        # Crossover clarity factor
        latest_crossover = crossover_analysis.get("latest_crossover")
        if latest_crossover:
            crossover_strength = latest_crossover["strength"]
            clarity_factor = min(1.0, crossover_strength / 0.2)  # Normalize to 0.2 spread
            confidence_factors.append(clarity_factor)
        else:
            confidence_factors.append(0.5)
        
        # Spread level factor
        spread_level = spread_analysis.get("spread_level", "normal")
        if spread_level == "extreme":
            spread_factor = 0.9
        elif spread_level == "elevated":
            spread_factor = 0.7
        else:
            spread_factor = 0.6
        confidence_factors.append(spread_factor)
        
        # Indicator values factor (values around 1.0 are more reliable)
        current_plus = vi_plus.iloc[-1]
        current_minus = vi_minus.iloc[-1]
        avg_value = (current_plus + current_minus) / 2
        
        if 0.8 <= avg_value <= 1.2:
            value_factor = 0.8  # Good range
        else:
            value_factor = 0.6
        confidence_factors.append(value_factor)
        
        return round(np.mean(confidence_factors), 3)
    
    def _generate_vortex_summary(self, vi_plus: float, vi_minus: float,
                               crossover_analysis: Dict, dominance_analysis: Dict) -> str:
        """Generate human-readable Vortex summary."""
        dominant = dominance_analysis.get("current_dominant", "").replace("_", " ")
        dominance_strength = dominance_analysis.get("dominance_strength", 0)
        
        summary = f"Vortex VI+ {vi_plus:.3f}, VI- {vi_minus:.3f}"
        summary += f" - {dominant} dominant ({dominance_strength:+.3f})"
        
        # Add recent crossover info
        latest_crossover = crossover_analysis.get("latest_crossover")
        if latest_crossover and latest_crossover["periods_ago"] <= 5:
            crossover_type = latest_crossover["type"]
            periods_ago = latest_crossover["periods_ago"]
            summary += f", {crossover_type.replace('_', ' ')} {periods_ago}p ago"
        
        return summary