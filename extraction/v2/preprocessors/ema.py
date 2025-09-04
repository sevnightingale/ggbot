"""
EMA (Exponential Moving Average) Preprocessor.

Advanced EMA preprocessing with responsiveness analysis, trend detection,
and comparison with SMA for enhanced signal quality assessment.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePreprocessor


class EMAPreprocessor(BasePreprocessor):
    """Advanced EMA preprocessor with professional-grade responsiveness analysis."""
    
    def preprocess(self, ema: pd.Series, prices: pd.Series = None, sma: pd.Series = None,
                  length: int = 20, **kwargs) -> Dict[str, Any]:
        """
        Advanced EMA preprocessing with comprehensive responsiveness analysis.
        
        EMA gives more weight to recent prices, making it more responsive than SMA.
        This responsiveness can provide earlier signals but also more false signals.
        
        Args:
            ema: EMA values
            prices: Price series for position analysis (optional)
            sma: SMA values for comparison (optional)
            length: EMA calculation period
            
        Returns:
            Dictionary with comprehensive EMA analysis
        """
        if len(ema) < 5:
            return {"error": "Insufficient data for EMA analysis"}
        
        current_ema = float(ema.iloc[-1])
        current_price = float(prices.iloc[-1]) if prices is not None else None
        
        # Trend analysis
        trend_analysis = self._analyze_ema_trend(ema)
        
        # Responsiveness analysis
        responsiveness_analysis = self._analyze_ema_responsiveness(ema)
        
        # Price-EMA relationship
        price_relationship = {}
        if prices is not None:
            price_relationship = self._analyze_price_ema_relationship(prices, ema)
        
        # EMA-SMA comparison
        ema_sma_comparison = {}
        if sma is not None:
            ema_sma_comparison = self._analyze_ema_sma_comparison(ema, sma, prices)
        
        # Crossover analysis
        crossover_analysis = {}
        if prices is not None:
            crossover_analysis = self._analyze_price_ema_crossovers(prices, ema)
        
        # Signal quality assessment
        signal_quality = self._assess_ema_signal_quality(ema, responsiveness_analysis)
        
        # Support/resistance analysis
        support_resistance = self._analyze_ema_support_resistance(ema, prices)
        
        # Signal generation
        signals = self._generate_ema_signals(current_ema, current_price, trend_analysis, 
                                           price_relationship, crossover_analysis, signal_quality)
        
        # Confidence calculation
        confidence = self._calculate_ema_confidence(ema, trend_analysis, responsiveness_analysis, signal_quality)
        
        return {
            "indicator": "EMA",
            "current": {
                "ema_value": round(current_ema, 4),
                "price": round(current_price, 4) if current_price else None,
                "price_distance": round(current_price - current_ema, 4) if current_price else None,
                "price_distance_pct": round(((current_price - current_ema) / current_ema) * 100, 3) if current_price else None,
                "timestamp": datetime.now().isoformat()
            },
            "trend": trend_analysis,
            "responsiveness": responsiveness_analysis,
            "price_relationship": price_relationship,
            "ema_sma_comparison": ema_sma_comparison,
            "crossovers": crossover_analysis,
            "signal_quality": signal_quality,
            "support_resistance": support_resistance,
            "signals": signals,
            "confidence": confidence,
            "summary": self._generate_ema_summary(current_ema, current_price, trend_analysis, responsiveness_analysis)
        }
    
    def _analyze_ema_trend(self, ema: pd.Series) -> Dict[str, Any]:
        """Analyze EMA trend characteristics."""
        # Short, medium, long term trends
        short_trend = self._calculate_ema_trend_direction(ema, 2)  # More responsive
        medium_trend = self._calculate_ema_trend_direction(ema, 5)
        long_trend = self._calculate_ema_trend_direction(ema, 10) if len(ema) >= 10 else "insufficient_data"
        
        # Trend consistency (EMAs should be more volatile)
        trend_consistency = self._calculate_ema_trend_consistency(ema)
        
        # Trend strength
        slope = self._calculate_velocity(ema, 3)  # Shorter period for EMA
        trend_strength = min(1.0, abs(slope) / (ema.std() * 0.15)) if ema.std() > 0 else 0
        
        # Acceleration (EMA should show momentum changes faster)
        acceleration = self._calculate_acceleration(ema, 5)
        
        # Overall trend consensus
        trends = [t for t in [short_trend, medium_trend, long_trend] if t not in ["insufficient_data", "sideways"]]
        if trends:
            bullish_count = sum(1 for t in trends if t == "bullish")
            bearish_count = sum(1 for t in trends if t == "bearish")
            
            if bullish_count > bearish_count:
                consensus = "bullish"
            elif bearish_count > bullish_count:
                consensus = "bearish"
            else:
                consensus = "mixed"
        else:
            consensus = "sideways"
        
        return {
            "short_term": short_trend,
            "medium_term": medium_trend,
            "long_term": long_trend,
            "consensus": consensus,
            "strength": round(trend_strength, 3),
            "consistency": round(trend_consistency, 3),
            "slope": round(slope, 6),
            "acceleration": round(acceleration, 6)
        }
    
    def _calculate_ema_trend_direction(self, ema: pd.Series, periods: int) -> str:
        """Calculate EMA trend direction (more sensitive thresholds)."""
        if len(ema) < periods + 1:
            return "insufficient_data"
        
        start_value = ema.iloc[-(periods + 1)]
        end_value = ema.iloc[-1]
        
        change_pct = ((end_value - start_value) / start_value) * 100 if start_value != 0 else 0
        
        # Lower thresholds for EMA due to higher responsiveness
        if change_pct > 0.1:
            return "bullish"
        elif change_pct < -0.1:
            return "bearish"
        else:
            return "sideways"
    
    def _calculate_ema_trend_consistency(self, ema: pd.Series) -> float:
        """Calculate EMA trend consistency (expect lower consistency due to responsiveness)."""
        if len(ema) < 8:
            return 0.5
        
        # Look at direction changes over recent periods (shorter for EMA)
        recent_ema = ema.iloc[-8:]
        changes = recent_ema.diff().dropna()
        
        if len(changes) == 0:
            return 0.5
        
        positive_changes = sum(1 for x in changes if x > 0)
        negative_changes = sum(1 for x in changes if x < 0)
        total_changes = len(changes)
        
        max_directional = max(positive_changes, negative_changes)
        return max_directional / total_changes if total_changes > 0 else 0.5
    
    def _analyze_ema_responsiveness(self, ema: pd.Series) -> Dict[str, Any]:
        """Analyze EMA responsiveness characteristics."""
        if len(ema) < 5:
            return {}
        
        # Rate of change analysis
        ema_changes = ema.diff().dropna()
        avg_change = ema_changes.abs().mean()
        max_change = ema_changes.abs().max()
        
        # Volatility of the EMA itself
        ema_volatility = ema.std()
        ema_mean = ema.mean()
        relative_volatility = ema_volatility / ema_mean if ema_mean > 0 else 0
        
        # Direction change frequency
        direction_changes = 0
        prev_direction = None
        
        for change in ema_changes:
            current_direction = "up" if change > 0 else "down" if change < 0 else "flat"
            if prev_direction and current_direction != prev_direction and current_direction != "flat":
                direction_changes += 1
            prev_direction = current_direction
        
        change_frequency = direction_changes / len(ema_changes) if len(ema_changes) > 0 else 0
        
        # Responsiveness score (higher = more responsive)
        responsiveness_score = min(1.0, (relative_volatility * 10 + change_frequency) / 2)
        
        return {
            "avg_change": round(avg_change, 6),
            "max_change": round(max_change, 6),
            "relative_volatility": round(relative_volatility, 6),
            "direction_changes": direction_changes,
            "change_frequency": round(change_frequency, 3),
            "responsiveness_score": round(responsiveness_score, 3),
            "responsiveness_rating": self._rate_responsiveness(responsiveness_score)
        }
    
    def _rate_responsiveness(self, score: float) -> str:
        """Rate EMA responsiveness level."""
        if score > 0.7:
            return "very_high"
        elif score > 0.5:
            return "high"
        elif score > 0.3:
            return "moderate"
        elif score > 0.1:
            return "low"
        else:
            return "very_low"
    
    def _analyze_price_ema_relationship(self, prices: pd.Series, ema: pd.Series) -> Dict[str, Any]:
        """Analyze price position relative to EMA."""
        current_price = prices.iloc[-1]
        current_ema = ema.iloc[-1]
        
        # Current position
        if current_price > current_ema:
            position = "above"
        elif current_price < current_ema:
            position = "below" 
        else:
            position = "at_level"
        
        # Distance analysis
        distance = current_price - current_ema
        distance_pct = (distance / current_ema) * 100
        
        # Historical position analysis
        above_periods = sum(1 for i in range(len(prices)) if prices.iloc[i] > ema.iloc[i])
        below_periods = len(prices) - above_periods
        total_periods = len(prices)
        
        # Average distance from EMA
        distances = prices - ema
        avg_distance = distances.mean()
        avg_distance_pct = (avg_distance / ema.mean()) * 100
        
        return {
            "position": position,
            "distance": round(distance, 4),
            "distance_pct": round(distance_pct, 3),
            "above_ema_pct": round((above_periods / total_periods) * 100, 1),
            "below_ema_pct": round((below_periods / total_periods) * 100, 1),
            "avg_distance": round(avg_distance, 4),
            "avg_distance_pct": round(avg_distance_pct, 3)
        }
    
    def _analyze_ema_sma_comparison(self, ema: pd.Series, sma: pd.Series, prices: pd.Series = None) -> Dict[str, Any]:
        """Compare EMA vs SMA characteristics."""
        if len(ema) != len(sma):
            return {"error": "EMA and SMA series lengths must match"}
        
        current_ema = ema.iloc[-1]
        current_sma = sma.iloc[-1]
        
        # Current relationship
        if current_ema > current_sma:
            ema_sma_position = "ema_above_sma"
        elif current_ema < current_sma:
            ema_sma_position = "ema_below_sma"
        else:
            ema_sma_position = "ema_equals_sma"
        
        # Spread analysis
        spread = ema - sma
        current_spread = spread.iloc[-1]
        avg_spread = spread.mean()
        spread_volatility = spread.std()
        
        # Responsiveness comparison
        ema_changes = ema.diff().dropna().abs().mean()
        sma_changes = sma.diff().dropna().abs().mean()
        responsiveness_ratio = ema_changes / sma_changes if sma_changes > 0 else 1
        
        # Signal timing analysis
        signal_timing = {}
        if prices is not None:
            signal_timing = self._analyze_ema_sma_signal_timing(prices, ema, sma)
        
        return {
            "position": ema_sma_position,
            "current_spread": round(current_spread, 4),
            "avg_spread": round(avg_spread, 4),
            "spread_volatility": round(spread_volatility, 4),
            "responsiveness_ratio": round(responsiveness_ratio, 3),
            "signal_timing": signal_timing
        }
    
    def _analyze_ema_sma_signal_timing(self, prices: pd.Series, ema: pd.Series, sma: pd.Series) -> Dict[str, Any]:
        """Analyze timing differences between EMA and SMA signals."""
        # Find crossovers for both
        ema_crossovers = []
        sma_crossovers = []
        
        for i in range(1, len(prices)):
            # EMA crossovers
            if ((prices.iloc[i-1] <= ema.iloc[i-1] and prices.iloc[i] > ema.iloc[i]) or
                (prices.iloc[i-1] >= ema.iloc[i-1] and prices.iloc[i] < ema.iloc[i])):
                cross_type = "bullish" if prices.iloc[i] > ema.iloc[i] else "bearish"
                ema_crossovers.append({"index": i, "type": cross_type})
            
            # SMA crossovers  
            if ((prices.iloc[i-1] <= sma.iloc[i-1] and prices.iloc[i] > sma.iloc[i]) or
                (prices.iloc[i-1] >= sma.iloc[i-1] and prices.iloc[i] < sma.iloc[i])):
                cross_type = "bullish" if prices.iloc[i] > sma.iloc[i] else "bearish"
                sma_crossovers.append({"index": i, "type": cross_type})
        
        # Calculate average timing difference
        timing_differences = []
        for ema_cross in ema_crossovers:
            # Find nearest SMA crossover of same type
            nearest_sma = min(sma_crossovers, 
                            key=lambda x: abs(x["index"] - ema_cross["index"]) if x["type"] == ema_cross["type"] else float('inf'),
                            default=None)
            if nearest_sma:
                timing_diff = ema_cross["index"] - nearest_sma["index"]
                timing_differences.append(timing_diff)
        
        avg_timing_advantage = np.mean(timing_differences) if timing_differences else 0
        
        return {
            "ema_crossovers": len(ema_crossovers),
            "sma_crossovers": len(sma_crossovers),
            "avg_timing_advantage": round(avg_timing_advantage, 2),  # Negative = EMA earlier
            "timing_interpretation": "EMA leads" if avg_timing_advantage < -0.5 else "SMA leads" if avg_timing_advantage > 0.5 else "Similar timing"
        }
    
    def _analyze_price_ema_crossovers(self, prices: pd.Series, ema: pd.Series) -> Dict[str, Any]:
        """Analyze price crossovers with EMA."""
        crossovers = []
        
        for i in range(1, min(15, len(prices))):  # Shorter lookback for EMA
            prev_price = prices.iloc[-(i+1)]
            curr_price = prices.iloc[-i]
            prev_ema = ema.iloc[-(i+1)]
            curr_ema = ema.iloc[-i]
            
            # Bullish crossover
            if prev_price <= prev_ema and curr_price > curr_ema:
                crossovers.append({
                    "type": "bullish_crossover",
                    "periods_ago": i,
                    "price": round(curr_price, 4),
                    "ema_value": round(curr_ema, 4),
                    "strength": abs(curr_price - curr_ema) / curr_ema
                })
            
            # Bearish crossover
            elif prev_price >= prev_ema and curr_price < curr_ema:
                crossovers.append({
                    "type": "bearish_crossover",
                    "periods_ago": i,
                    "price": round(curr_price, 4),
                    "ema_value": round(curr_ema, 4),
                    "strength": abs(curr_price - curr_ema) / curr_ema
                })
        
        return {
            "recent_crossovers": crossovers[:5],
            "latest_crossover": crossovers[0] if crossovers else None,
            "crossover_frequency": len(crossovers) / min(15, len(prices)) if len(prices) > 0 else 0
        }
    
    def _assess_ema_signal_quality(self, ema: pd.Series, responsiveness_analysis: Dict) -> Dict[str, Any]:
        """Assess quality of EMA signals."""
        # Signal reliability based on responsiveness
        responsiveness_score = responsiveness_analysis.get("responsiveness_score", 0.5)
        
        # High responsiveness can mean more false signals
        if responsiveness_score > 0.7:
            signal_quality = "high_frequency_low_reliability"
        elif responsiveness_score > 0.4:
            signal_quality = "balanced"
        else:
            signal_quality = "low_frequency_high_reliability"
        
        # Noise level assessment
        change_frequency = responsiveness_analysis.get("change_frequency", 0)
        if change_frequency > 0.6:
            noise_level = "high"
        elif change_frequency > 0.3:
            noise_level = "moderate"
        else:
            noise_level = "low"
        
        return {
            "signal_quality": signal_quality,
            "noise_level": noise_level,
            "recommended_use": self._get_ema_usage_recommendation(signal_quality, noise_level)
        }
    
    def _get_ema_usage_recommendation(self, quality: str, noise: str) -> str:
        """Get recommendation for EMA usage based on signal quality."""
        if quality == "high_frequency_low_reliability":
            return "Use with confirmation indicators, good for scalping"
        elif quality == "balanced":
            return "Good for general trend following with moderate filters"
        else:
            return "Reliable for position trading, slower signals"
    
    def _analyze_ema_support_resistance(self, ema: pd.Series, prices: pd.Series = None) -> Dict[str, Any]:
        """Analyze EMA as dynamic support/resistance."""
        if prices is None:
            return {"no_price_data": True}
        
        # EMA tends to provide weaker S/R than SMA due to responsiveness
        touches = []
        bounces = []
        
        # Tighter touch threshold for EMA
        touch_threshold = 0.003  # 0.3%
        
        for i in range(1, len(prices)):
            price = prices.iloc[i]
            ema_val = ema.iloc[i]
            prev_price = prices.iloc[i-1]
            
            # Check for EMA touch
            if abs(price - ema_val) / ema_val <= touch_threshold:
                touches.append({
                    "index": i,
                    "periods_ago": len(prices) - 1 - i,
                    "price": price,
                    "ema_value": ema_val
                })
                
                # Check for bounce
                if i < len(prices) - 2:
                    next_price = prices.iloc[i+1]
                    
                    # Support bounce
                    if prev_price < ema_val and next_price > price:
                        bounces.append({
                            "type": "support_bounce",
                            "index": i,
                            "periods_ago": len(prices) - 1 - i,
                            "strength": abs(next_price - price) / price
                        })
                    
                    # Resistance bounce
                    elif prev_price > ema_val and next_price < price:
                        bounces.append({
                            "type": "resistance_bounce",
                            "index": i,
                            "periods_ago": len(prices) - 1 - i,
                            "strength": abs(price - next_price) / price
                        })
        
        # Success rate
        success_rate = (len(bounces) / len(touches)) if len(touches) > 0 else 0
        
        return {
            "total_touches": len(touches),
            "successful_bounces": len(bounces),
            "success_rate": round(success_rate, 3),
            "recent_touches": touches[-5:] if touches else [],
            "recent_bounces": bounces[-3:] if bounces else [],
            "effectiveness": "high" if success_rate > 0.5 else "medium" if success_rate > 0.25 else "low"
        }
    
    def _generate_ema_signals(self, ema_value: float, price: Optional[float],
                             trend_analysis: Dict, price_relationship: Dict,
                             crossover_analysis: Dict, signal_quality: Dict) -> List[Dict[str, Any]]:
        """Generate EMA trading signals."""
        signals = []
        
        # Trend-based signals
        consensus = trend_analysis.get("consensus", "mixed")
        trend_strength = trend_analysis.get("strength", 0)
        acceleration = trend_analysis.get("acceleration", 0)
        
        if consensus == "bullish" and trend_strength > 0.4:  # Lower threshold for EMA
            confidence = 0.6 + (trend_strength * 0.2)
            if acceleration > 0:
                confidence += 0.1  # Bonus for acceleration
            
            signals.append({
                "type": "ema_trend_buy",
                "strength": "medium",
                "reason": f"Bullish EMA trend with {trend_strength:.2f} strength",
                "confidence": min(0.9, confidence)
            })
        
        elif consensus == "bearish" and trend_strength > 0.4:
            confidence = 0.6 + (trend_strength * 0.2)
            if acceleration < 0:
                confidence += 0.1
            
            signals.append({
                "type": "ema_trend_sell",
                "strength": "medium",
                "reason": f"Bearish EMA trend with {trend_strength:.2f} strength",
                "confidence": min(0.9, confidence)
            })
        
        # Crossover signals (with quality adjustment)
        if crossover_analysis:
            latest_crossover = crossover_analysis.get("latest_crossover")
            if latest_crossover and latest_crossover["periods_ago"] <= 2:  # Very recent for EMA
                crossover_type = latest_crossover["type"]
                signal_type = "buy_signal" if "bullish" in crossover_type else "sell_signal"
                
                # Adjust confidence based on signal quality
                base_confidence = 0.7
                quality = signal_quality.get("signal_quality", "balanced")
                if quality == "high_frequency_low_reliability":
                    base_confidence = 0.5  # Lower confidence due to noise
                elif quality == "low_frequency_high_reliability":
                    base_confidence = 0.8  # Higher confidence
                
                signals.append({
                    "type": signal_type,
                    "strength": "medium",
                    "reason": f"Recent EMA {crossover_type.replace('_', ' ')}",
                    "confidence": base_confidence
                })
        
        # Responsiveness-based signals
        if price and price_relationship:
            distance_pct = abs(price_relationship.get("distance_pct", 0))
            
            # EMA signals trigger at smaller distances due to responsiveness
            if distance_pct > 2:  # Lower threshold than SMA
                position = price_relationship.get("position")
                if position == "above":
                    signals.append({
                        "type": "ema_pullback_opportunity",
                        "strength": "low",
                        "reason": f"Price {distance_pct:.1f}% above responsive EMA",
                        "confidence": 0.4
                    })
                elif position == "below":
                    signals.append({
                        "type": "ema_bounce_opportunity",
                        "strength": "low",
                        "reason": f"Price {distance_pct:.1f}% below responsive EMA",
                        "confidence": 0.4
                    })
        
        return signals
    
    def _calculate_ema_confidence(self, ema: pd.Series, trend_analysis: Dict, 
                                 responsiveness_analysis: Dict, signal_quality: Dict) -> float:
        """Calculate EMA analysis confidence."""
        confidence_factors = []
        
        # Data quantity factor
        data_factor = min(1.0, len(ema) / 25)  # Shorter requirement for EMA
        confidence_factors.append(data_factor)
        
        # Trend strength factor
        trend_strength = trend_analysis.get("strength", 0.5)
        confidence_factors.append(trend_strength)
        
        # Signal quality factor
        quality = signal_quality.get("signal_quality", "balanced")
        if quality == "low_frequency_high_reliability":
            quality_factor = 0.8
        elif quality == "balanced":
            quality_factor = 0.7
        else:  # high_frequency_low_reliability
            quality_factor = 0.5
        confidence_factors.append(quality_factor)
        
        # Responsiveness factor (moderate responsiveness is best)
        responsiveness = responsiveness_analysis.get("responsiveness_score", 0.5)
        if 0.3 <= responsiveness <= 0.6:
            resp_factor = 0.8  # Sweet spot
        else:
            resp_factor = 0.6
        confidence_factors.append(resp_factor)
        
        return round(np.mean(confidence_factors), 3)
    
    def _generate_ema_summary(self, ema_value: float, price: Optional[float],
                             trend_analysis: Dict, responsiveness_analysis: Dict) -> str:
        """Generate human-readable EMA summary."""
        consensus = trend_analysis.get("consensus", "mixed")
        trend_strength = trend_analysis.get("strength", 0)
        responsiveness_rating = responsiveness_analysis.get("responsiveness_rating", "moderate")
        
        summary = f"EMA {ema_value:.4f} - {consensus} trend"
        
        if trend_strength > 0.5:
            summary += f" (strength: {trend_strength:.2f})"
        
        summary += f", {responsiveness_rating} responsiveness"
        
        if price:
            distance_pct = ((price - ema_value) / ema_value) * 100
            summary += f", price {distance_pct:+.1f}%"
        
        return summary