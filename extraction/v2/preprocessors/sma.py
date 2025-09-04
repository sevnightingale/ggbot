"""
SMA (Simple Moving Average) Preprocessor.

Advanced SMA preprocessing with trend analysis, support/resistance detection,
and multi-timeframe moving average relationships.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePreprocessor


class SMAPreprocessor(BasePreprocessor):
    """Advanced SMA preprocessor with professional-grade trend analysis."""
    
    def preprocess(self, sma: pd.Series, prices: pd.Series = None, 
                  length: int = 20, **kwargs) -> Dict[str, Any]:
        """
        Advanced SMA preprocessing with comprehensive trend analysis.
        
        SMA is a lagging indicator that smooths price action to identify trend direction.
        It acts as dynamic support/resistance and trend confirmation.
        
        Args:
            sma: SMA values
            prices: Price series for position analysis (optional)
            length: SMA calculation period
            
        Returns:
            Dictionary with comprehensive SMA analysis
        """
        if len(sma) < 5:
            return {"error": "Insufficient data for SMA analysis"}
        
        current_sma = float(sma.iloc[-1])
        current_price = float(prices.iloc[-1]) if prices is not None else None
        
        # Trend analysis
        trend_analysis = self._analyze_sma_trend(sma)
        
        # Price-SMA relationship
        price_relationship = {}
        if prices is not None:
            price_relationship = self._analyze_price_sma_relationship(prices, sma)
        
        # Support/Resistance analysis
        support_resistance = self._analyze_support_resistance(sma, prices)
        
        # Slope analysis
        slope_analysis = self._analyze_sma_slope(sma)
        
        # Crossover analysis
        crossover_analysis = {}
        if prices is not None:
            crossover_analysis = self._analyze_price_sma_crossovers(prices, sma)
        
        # Moving average quality
        quality_analysis = self._analyze_ma_quality(sma)
        
        # Signal generation
        signals = self._generate_sma_signals(current_sma, current_price, trend_analysis, 
                                           price_relationship, crossover_analysis)
        
        # Confidence calculation
        confidence = self._calculate_sma_confidence(sma, trend_analysis, quality_analysis)
        
        return {
            "indicator": "SMA",
            "current": {
                "sma_value": round(current_sma, 4),
                "price": round(current_price, 4) if current_price else None,
                "price_distance": round(current_price - current_sma, 4) if current_price else None,
                "price_distance_pct": round(((current_price - current_sma) / current_sma) * 100, 3) if current_price else None,
                "timestamp": datetime.now().isoformat()
            },
            "trend": trend_analysis,
            "price_relationship": price_relationship,
            "support_resistance": support_resistance,
            "slope": slope_analysis,
            "crossovers": crossover_analysis,
            "quality": quality_analysis,
            "signals": signals,
            "confidence": confidence,
            "summary": self._generate_sma_summary(current_sma, current_price, trend_analysis, price_relationship)
        }
    
    def _analyze_sma_trend(self, sma: pd.Series) -> Dict[str, Any]:
        """Analyze SMA trend characteristics."""
        current_sma = sma.iloc[-1]
        
        # Short, medium, long term trends
        short_trend = self._calculate_ma_trend_direction(sma, 3)
        medium_trend = self._calculate_ma_trend_direction(sma, 8)
        long_trend = self._calculate_ma_trend_direction(sma, 15) if len(sma) >= 15 else "insufficient_data"
        
        # Trend consistency
        trend_consistency = self._calculate_ma_trend_consistency(sma)
        
        # Trend strength (based on slope steepness)
        slope = self._calculate_velocity(sma, 5)
        trend_strength = min(1.0, abs(slope) / (sma.std() * 0.1)) if sma.std() > 0 else 0
        
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
            "slope": round(slope, 6)
        }
    
    def _calculate_ma_trend_direction(self, ma: pd.Series, periods: int) -> str:
        """Calculate trend direction over specified periods."""
        if len(ma) < periods + 1:
            return "insufficient_data"
        
        start_value = ma.iloc[-(periods + 1)]
        end_value = ma.iloc[-1]
        
        change_pct = ((end_value - start_value) / start_value) * 100 if start_value != 0 else 0
        
        if change_pct > 0.2:
            return "bullish"
        elif change_pct < -0.2:
            return "bearish"
        else:
            return "sideways"
    
    def _calculate_ma_trend_consistency(self, ma: pd.Series) -> float:
        """Calculate consistency of moving average trend."""
        if len(ma) < 10:
            return 0.5
        
        # Look at direction changes over recent periods
        recent_ma = ma.iloc[-10:]
        changes = recent_ma.diff().dropna()
        
        if len(changes) == 0:
            return 0.5
        
        positive_changes = sum(1 for x in changes if x > 0)
        negative_changes = sum(1 for x in changes if x < 0)
        total_changes = len(changes)
        
        # Consistency is when most changes go in same direction
        max_directional = max(positive_changes, negative_changes)
        return max_directional / total_changes if total_changes > 0 else 0.5
    
    def _analyze_price_sma_relationship(self, prices: pd.Series, sma: pd.Series) -> Dict[str, Any]:
        """Analyze price position relative to SMA."""
        current_price = prices.iloc[-1]
        current_sma = sma.iloc[-1]
        
        # Current position
        if current_price > current_sma:
            position = "above"
        elif current_price < current_sma:
            position = "below"
        else:
            position = "at_level"
        
        # Distance analysis
        distance = current_price - current_sma
        distance_pct = (distance / current_sma) * 100
        
        # Historical position analysis
        above_periods = sum(1 for i in range(len(prices)) if prices.iloc[i] > sma.iloc[i])
        below_periods = len(prices) - above_periods
        total_periods = len(prices)
        
        # Recent position changes
        position_changes = 0
        prev_position = "above" if prices.iloc[0] > sma.iloc[0] else "below"
        
        for i in range(1, len(prices)):
            curr_position = "above" if prices.iloc[i] > sma.iloc[i] else "below"
            if curr_position != prev_position:
                position_changes += 1
            prev_position = curr_position
        
        return {
            "position": position,
            "distance": round(distance, 4),
            "distance_pct": round(distance_pct, 3),
            "above_sma_pct": round((above_periods / total_periods) * 100, 1),
            "below_sma_pct": round((below_periods / total_periods) * 100, 1),
            "position_changes": position_changes,
            "position_stability": round(1 - (position_changes / total_periods), 3)
        }
    
    def _analyze_support_resistance(self, sma: pd.Series, prices: pd.Series = None) -> Dict[str, Any]:
        """Analyze SMA as dynamic support/resistance."""
        if prices is None:
            return {"no_price_data": True}
        
        # Find touches and bounces off SMA
        touches = []
        bounces = []
        
        # Define touch as price within 0.5% of SMA
        touch_threshold = 0.005
        
        for i in range(1, len(prices)):
            price = prices.iloc[i]
            sma_val = sma.iloc[i]
            prev_price = prices.iloc[i-1]
            
            # Check if price touched SMA
            if abs(price - sma_val) / sma_val <= touch_threshold:
                touches.append({
                    "index": i,
                    "periods_ago": len(prices) - 1 - i,
                    "price": price,
                    "sma_value": sma_val
                })
                
                # Check for bounce (reversal after touch)
                if i < len(prices) - 2:
                    next_price = prices.iloc[i+1]
                    
                    # Support bounce (price was below, touched, then moved up)
                    if prev_price < sma_val and next_price > price:
                        bounces.append({
                            "type": "support_bounce",
                            "index": i,
                            "periods_ago": len(prices) - 1 - i,
                            "strength": abs(next_price - price) / price
                        })
                    
                    # Resistance bounce (price was above, touched, then moved down)
                    elif prev_price > sma_val and next_price < price:
                        bounces.append({
                            "type": "resistance_bounce",
                            "index": i,
                            "periods_ago": len(prices) - 1 - i,
                            "strength": abs(price - next_price) / price
                        })
        
        # Calculate success rate
        total_touches = len(touches)
        successful_bounces = len(bounces)
        success_rate = (successful_bounces / total_touches) if total_touches > 0 else 0
        
        return {
            "total_touches": total_touches,
            "successful_bounces": successful_bounces,
            "success_rate": round(success_rate, 3),
            "recent_touches": touches[-5:] if touches else [],
            "recent_bounces": bounces[-3:] if bounces else [],
            "effectiveness": "high" if success_rate > 0.6 else "medium" if success_rate > 0.3 else "low"
        }
    
    def _analyze_sma_slope(self, sma: pd.Series) -> Dict[str, Any]:
        """Analyze SMA slope characteristics."""
        if len(sma) < 5:
            return {}
        
        # Calculate slope over different periods
        slope_3 = self._calculate_velocity(sma, 3)
        slope_5 = self._calculate_velocity(sma, 5)
        slope_10 = self._calculate_velocity(sma, 10) if len(sma) >= 10 else None
        
        # Acceleration
        acceleration = self._calculate_acceleration(sma, 5)
        
        # Slope classification
        if slope_5 > 0.001:
            slope_direction = "upward"
        elif slope_5 < -0.001:
            slope_direction = "downward"
        else:
            slope_direction = "flat"
        
        # Slope consistency (are short and long term slopes aligned?)
        slope_alignment = "aligned" if slope_10 and (slope_5 * slope_10 > 0) else "mixed"
        
        return {
            "short_term_slope": round(slope_3, 6),
            "medium_term_slope": round(slope_5, 6),
            "long_term_slope": round(slope_10, 6) if slope_10 else None,
            "acceleration": round(acceleration, 6),
            "direction": slope_direction,
            "alignment": slope_alignment
        }
    
    def _analyze_price_sma_crossovers(self, prices: pd.Series, sma: pd.Series) -> Dict[str, Any]:
        """Analyze price crossovers with SMA."""
        crossovers = []
        
        for i in range(1, min(20, len(prices))):
            prev_price = prices.iloc[-(i+1)]
            curr_price = prices.iloc[-i]
            prev_sma = sma.iloc[-(i+1)]
            curr_sma = sma.iloc[-i]
            
            # Bullish crossover (price crosses above SMA)
            if prev_price <= prev_sma and curr_price > curr_sma:
                crossovers.append({
                    "type": "bullish_crossover",
                    "periods_ago": i,
                    "price": round(curr_price, 4),
                    "sma_value": round(curr_sma, 4),
                    "strength": abs(curr_price - curr_sma) / curr_sma
                })
            
            # Bearish crossover (price crosses below SMA)
            elif prev_price >= prev_sma and curr_price < curr_sma:
                crossovers.append({
                    "type": "bearish_crossover",
                    "periods_ago": i,
                    "price": round(curr_price, 4),
                    "sma_value": round(curr_sma, 4),
                    "strength": abs(curr_price - curr_sma) / curr_sma
                })
        
        return {
            "recent_crossovers": crossovers[:5],
            "latest_crossover": crossovers[0] if crossovers else None,
            "crossover_frequency": len(crossovers) / min(20, len(prices)) if len(prices) > 0 else 0
        }
    
    def _analyze_ma_quality(self, sma: pd.Series) -> Dict[str, Any]:
        """Analyze quality characteristics of the moving average."""
        if len(sma) < 10:
            return {}
        
        # Smoothness (lower volatility = smoother)
        sma_volatility = sma.std()
        sma_mean = sma.mean()
        smoothness = 1 - (sma_volatility / sma_mean) if sma_mean > 0 else 0
        
        # Responsiveness (how quickly it changes)
        recent_changes = sma.diff().dropna().abs().mean()
        responsiveness = min(1.0, recent_changes / (sma_mean * 0.01)) if sma_mean > 0 else 0
        
        # Trend clarity (consistent direction)
        direction_changes = 0
        prev_direction = None
        
        for change in sma.diff().dropna():
            current_direction = "up" if change > 0 else "down" if change < 0 else "flat"
            if prev_direction and current_direction != prev_direction and current_direction != "flat":
                direction_changes += 1
            prev_direction = current_direction
        
        trend_clarity = 1 - (direction_changes / len(sma)) if len(sma) > 0 else 0
        
        return {
            "smoothness": round(smoothness, 3),
            "responsiveness": round(responsiveness, 3),
            "trend_clarity": round(trend_clarity, 3),
            "overall_quality": round((smoothness + trend_clarity) / 2, 3)
        }
    
    def _generate_sma_signals(self, sma_value: float, price: Optional[float], 
                             trend_analysis: Dict, price_relationship: Dict, 
                             crossover_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate SMA trading signals."""
        signals = []
        
        # Trend-based signals
        consensus = trend_analysis.get("consensus", "mixed")
        trend_strength = trend_analysis.get("strength", 0)
        
        if consensus == "bullish" and trend_strength > 0.5:
            signals.append({
                "type": "trend_following_buy",
                "strength": "medium",
                "reason": f"Strong bullish SMA trend (strength: {trend_strength:.2f})",
                "confidence": 0.6 + (trend_strength * 0.2)
            })
        elif consensus == "bearish" and trend_strength > 0.5:
            signals.append({
                "type": "trend_following_sell",
                "strength": "medium",
                "reason": f"Strong bearish SMA trend (strength: {trend_strength:.2f})",
                "confidence": 0.6 + (trend_strength * 0.2)
            })
        
        # Price position signals
        if price and price_relationship:
            position = price_relationship.get("position")
            distance_pct = abs(price_relationship.get("distance_pct", 0))
            
            if position == "above" and distance_pct > 3:
                signals.append({
                    "type": "extended_above_sma",
                    "strength": "low",
                    "reason": f"Price {distance_pct:.1f}% above SMA - potential pullback",
                    "confidence": 0.5
                })
            elif position == "below" and distance_pct > 3:
                signals.append({
                    "type": "extended_below_sma",
                    "strength": "low",
                    "reason": f"Price {distance_pct:.1f}% below SMA - potential bounce",
                    "confidence": 0.5
                })
        
        # Crossover signals
        if crossover_analysis:
            latest_crossover = crossover_analysis.get("latest_crossover")
            if latest_crossover and latest_crossover["periods_ago"] <= 3:
                crossover_type = latest_crossover["type"]
                signal_type = "buy_signal" if "bullish" in crossover_type else "sell_signal"
                
                signals.append({
                    "type": signal_type,
                    "strength": "medium",
                    "reason": f"Recent price {crossover_type.replace('_', ' ')} SMA",
                    "confidence": 0.7
                })
        
        return signals
    
    def _calculate_sma_confidence(self, sma: pd.Series, trend_analysis: Dict, quality_analysis: Dict) -> float:
        """Calculate SMA analysis confidence."""
        confidence_factors = []
        
        # Data quantity factor
        data_factor = min(1.0, len(sma) / 30)
        confidence_factors.append(data_factor)
        
        # Trend consistency factor
        trend_consistency = trend_analysis.get("consistency", 0.5)
        confidence_factors.append(trend_consistency)
        
        # Quality factor
        if quality_analysis:
            overall_quality = quality_analysis.get("overall_quality", 0.5)
            confidence_factors.append(overall_quality)
        else:
            confidence_factors.append(0.6)
        
        # Trend strength factor
        trend_strength = trend_analysis.get("strength", 0.5)
        confidence_factors.append(trend_strength)
        
        return round(np.mean(confidence_factors), 3)
    
    def _generate_sma_summary(self, sma_value: float, price: Optional[float], 
                             trend_analysis: Dict, price_relationship: Dict) -> str:
        """Generate human-readable SMA summary."""
        consensus = trend_analysis.get("consensus", "mixed")
        trend_strength = trend_analysis.get("strength", 0)
        
        summary = f"SMA {sma_value:.4f} - {consensus} trend"
        
        if trend_strength > 0.6:
            summary += f" (strong)"
        
        if price and price_relationship:
            position = price_relationship.get("position", "unknown")
            distance_pct = price_relationship.get("distance_pct", 0)
            
            if position in ["above", "below"]:
                summary += f", price {position} ({distance_pct:+.1f}%)"
        
        return summary