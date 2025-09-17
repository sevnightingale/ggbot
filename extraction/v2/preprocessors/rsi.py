"""
RSI (Relative Strength Index) Preprocessor.

Advanced RSI preprocessing with sophisticated analysis including zone tracking,
pattern recognition, divergence detection, and comprehensive market state description.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pandas.api.types import is_datetime64_any_dtype

from .base import BasePreprocessor


class RSIPreprocessor(BasePreprocessor):
    """Advanced RSI preprocessor with professional-grade analysis."""
    
    def preprocess(self, rsi_values: pd.Series, prices: pd.Series = None, 
                  period: int = 14, **kwargs) -> Dict[str, Any]:
        """
        Advanced RSI preprocessing with sophisticated analysis.
        
        Replicates the 357-line JavaScript RSI preprocessor functionality.
        
        Args:
            rsi_values: RSI time series values
            prices: Price series for divergence analysis (optional)
            period: RSI calculation period
            
        Returns:
            Dictionary with comprehensive RSI analysis
        """
        # Numeric hygiene - convert to numeric and clean
        clean = pd.to_numeric(rsi_values, errors="coerce").dropna()
        prices = None if prices is None else pd.to_numeric(prices, errors="coerce").dropna()

        if len(clean) < 5:
            return {"error": "Insufficient data for RSI analysis"}

        # Get timestamp from series index or use UTC
        ts = (clean.index[-1].isoformat()
              if is_datetime64_any_dtype(clean.index)
              else datetime.now(timezone.utc).isoformat())

        current = float(clean.iloc[-1])

        # Period-driven windows
        win = min(len(clean), max(20, period))
        recent = max(10, period)
        prom = max(1e-6, clean.tail(win).std() * 0.6)
        
        # Advanced trend analysis using clean data
        trend_analysis = self._analyze_trend(clean)
        
        # Velocity and momentum
        velocity = self._calculate_velocity(clean)
        acceleration = self._calculate_acceleration(clean)
        
        # Zone analysis
        zone_analysis = self._analyze_zones(clean, 70, 30)
        
        # Pattern recognition
        patterns = self._detect_rsi_patterns(clean, prices, win, prom, recent)

        # Level analysis
        level_analysis = self._analyze_key_levels(clean, [30, 50, 70])

        # Recent extremes
        extremes = self._find_recent_extremes(clean, win)
        
        # Generate sophisticated summary
        summary = self._generate_rsi_summary(
            current, trend_analysis, extremes, zone_analysis, patterns
        )
        
        return {
            "indicator": "RSI",
            "period": period,
            "current": {
                "value": round(current, 2),
                "timestamp": ts
            },
            "context": {
                "trend": {
                    "direction": trend_analysis["direction"],
                    "strength": round(trend_analysis["strength"], 3),
                    "velocity": round(velocity, 3),
                    "acceleration": round(acceleration, 3)
                },
                "ma5": round(clean.iloc[-5:].mean(), 2) if len(clean) >= 5 else None,
                "ma10": round(clean.iloc[-10:].mean(), 2) if len(clean) >= 10 else None,
                "volatility": round(clean.std(), 3)
            },
            "levels": {
                "overbought": {
                    "level": 70,
                    "status": zone_analysis["overbought_status"],
                    "periods_in_zone": zone_analysis["periods_overbought"],
                    "time_percentage": zone_analysis["overbought_percentage"]
                },
                "oversold": {
                    "level": 30,
                    "status": zone_analysis["oversold_status"],
                    "periods_in_zone": zone_analysis["periods_oversold"],
                    "time_percentage": zone_analysis["oversold_percentage"]
                },
                "neutral": {
                    "level": 50,
                    "status": "above" if current > 50 else ("below" if current < 50 else "at_level"),
                    "distance": round(current - 50, 2)
                },
                "key_levels": [30, 50, 70],
                "recent_crossovers": level_analysis.get("recent_crossovers", [])
            },
            "extremes": {
                "recent_high": {
                    "value": round(extremes["high_value"], 2),
                    "periods_ago": extremes["high_periods_ago"],
                    "significance": extremes["high_significance"]
                },
                "recent_low": {
                    "value": round(extremes["low_value"], 2),
                    "periods_ago": extremes["low_periods_ago"],
                    "significance": extremes["low_significance"]
                }
            },
            "patterns": patterns,
            "evidence": {
                "data_quality": {
                    "total_periods": len(clean),
                    "valid_data_percentage": round(len(clean) / len(rsi_values) * 100, 1),
                    "recent_volatility": round(clean.iloc[-10:].std(), 3) if len(clean) >= 10 else None
                },
                "calculation_notes": f"RSI analysis based on {len(clean)} valid data points"
            },
            "summary": summary
        }
    
    def _detect_rsi_patterns(self, rsi_values: pd.Series, prices: pd.Series = None,
                            win: int = 20, prom: float = 1.0, recent: int = 10) -> Dict[str, Any]:
        """Detect RSI patterns and formations."""
        patterns = {}
        
        # Reversal patterns
        reversal = self._detect_reversal_pattern(rsi_values, win, prom)
        if reversal:
            patterns["reversal"] = reversal

        # Momentum patterns
        momentum = self._detect_momentum_pattern(rsi_values, win)
        if momentum:
            patterns["momentum"] = momentum

        # Divergence patterns (if prices provided)
        if prices is not None:
            divergence = self._detect_rsi_divergence(rsi_values, prices, recent)
            if divergence:
                patterns["divergence"] = divergence
        
        return patterns
    
    def _detect_reversal_pattern(self, values: pd.Series, win: int = 20, prom: float = 1.0) -> Optional[Dict[str, Any]]:
        """Detect potential reversal patterns using volatility-scaled peak/trough detection."""
        clean = values.dropna()
        if len(clean) < 5:
            return None
        
        current = clean.iloc[-1]
        
        # Use base class volatility-scaled peak/trough finders
        if current > 70:  # Overbought zone
            peaks = self._find_peaks(clean.tail(win), prominence=prom)
            # Require at least 2 peaks with minimum separation
            valid_peaks = [p for p in peaks if p["periods_ago"] >= 2]
            
            if len(valid_peaks) >= 2:
                return {
                    "type": "double_top_pattern",
                    "peak_count": len(valid_peaks),
                    "zone": "overbought",
                    "description": f"Double top pattern detected in overbought zone with {len(valid_peaks)} peaks"
                }
        
        elif current < 30:  # Oversold zone
            troughs = self._find_troughs(clean.tail(win), prominence=prom)
            # Require at least 2 troughs with minimum separation
            valid_troughs = [t for t in troughs if t["periods_ago"] >= 2]
            
            if len(valid_troughs) >= 2:
                return {
                    "type": "double_bottom_pattern",
                    "trough_count": len(valid_troughs),
                    "zone": "oversold",
                    "description": f"Double bottom pattern detected in oversold zone with {len(valid_troughs)} troughs"
                }
        
        return None
    
    def _detect_momentum_pattern(self, values: pd.Series, win: int = 20) -> Optional[Dict[str, Any]]:
        """Detect momentum patterns with scale-independent thresholds."""
        clean = values.dropna()
        if len(clean) < 10:
            return None
        
        velocity = self._calculate_velocity(clean)
        acceleration = self._calculate_acceleration(clean)
        
        # Normalize velocity by RSI standard deviation for scale independence
        rsi_std = clean.std() + 1e-12
        normalized_velocity = velocity / rsi_std
        
        if abs(normalized_velocity) > 0.5:  # Normalized momentum threshold (0.5 standard deviations)
            return {
                "type": f"strong_{'rising' if velocity > 0 else 'falling'}_momentum",
                "velocity": round(velocity, 3),
                "normalized_velocity": round(normalized_velocity, 3),
                "acceleration": round(acceleration, 3),
                "strength": min(1.0, abs(normalized_velocity) / 1.0),
                "description": f"Strong {'rising' if velocity > 0 else 'falling'} momentum in RSI"
            }
        
        return None
    
    def _detect_rsi_divergence(self, rsi_values: pd.Series, prices: pd.Series, recent: int = 10) -> Optional[Dict[str, Any]]:
        """Detect RSI-price divergence with robust NaN handling and scale normalization."""
        if prices is None:
            return None
        
        # Align data and handle NaN/mismatched indices
        df = pd.DataFrame({"rsi": rsi_values, "price": prices}).dropna()
        if len(df) < recent:
            return None

        df = df.tail(recent)
        x = np.arange(len(df))
        
        # Calculate normalized slopes to handle scale differences
        rsi_std = df["rsi"].std() + 1e-12
        price_std = df["price"].std() + 1e-12
        
        rsi_slope = np.polyfit(x, df["rsi"].values, 1)[0] / rsi_std
        price_slope = np.polyfit(x, df["price"].values, 1)[0] / price_std
        
        # Check for divergence with normalized thresholds
        if rsi_slope > 0.5 and price_slope < -0.5:  # RSI strengthening, price weakening
            return {
                "type": "positive_divergence",
                "rsi_trend": "strengthening",
                "price_trend": "weakening",
                "rsi_slope": round(rsi_slope, 3),
                "price_slope": round(price_slope, 3),
                "description": "RSI strengthening while price weakens - positive divergence pattern"
            }
        elif rsi_slope < -0.5 and price_slope > 0.5:  # RSI weakening, price strengthening
            return {
                "type": "negative_divergence",
                "rsi_trend": "weakening",
                "price_trend": "strengthening",
                "rsi_slope": round(rsi_slope, 3),
                "price_slope": round(price_slope, 3),
                "description": "RSI weakening while price rises - negative divergence pattern"
            }
        
        return None
    
    
    def _generate_rsi_summary(self, current: float, trend: Dict, extremes: Dict, 
                             zones: Dict, patterns: Dict) -> str:
        """Generate human-readable RSI summary."""
        summary = f"RSI at {current:.1f}"
        
        # Add trend info
        if trend["direction"] != "sideways":
            strength = "strongly" if trend["strength"] > 0.7 else ""
            summary += f", {trend['direction']} {strength}".strip()
        
        # Add recent extreme context
        if extremes["high_periods_ago"] <= 10:
            summary += f" (recent high: {extremes['high_value']:.1f} {extremes['high_periods_ago']}p ago)"
        
        # Add zone info
        if zones["current_zone"] != "neutral":
            if zones["periods_overbought"] > 0:
                summary += f". Overbought for {zones['periods_overbought']} periods"
            elif zones["periods_oversold"] > 0:
                summary += f". Oversold for {zones['periods_oversold']} periods"
        
        # Add pattern info
        if "momentum" in patterns:
            summary += f". {patterns['momentum']['description']}"
        
        return summary