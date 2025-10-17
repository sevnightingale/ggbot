You are an expert cryptocurrency trader analyzing market opportunities. Your job is to identify potential trading opportunities based on current market conditions and your configured trading strategy.

## MARKET DATA ANALYSIS
Here is comprehensive technical analysis across all 7 timeframes (5m, 15m, 30m, 1h, 4h, 1d, 1w) for BTC/USDT at current price $105,169.70:

MARKET ANALYSIS FOR BTC/USDT
Current Price: $105,287.20
Timeframes Available: 15m, 1d, 1h, 1w, 30m, 4h, 5m

=== 15M TIMEFRAME ===
  dc:
    Current: {'price': 105287.2, 'timestamp': '2025-10-17T14:55:56.470920+00:00', 'channel_width': 3122.99, 'lower_channel': 103528.23, 'upper_channel': 106651.22, 'middle_channel': 105089.725, 'price_position_pct': 56.3}
    Summary: Donchian: Price 105287.2000 (56.3%), Width 3122.9900
    Trend: strength: neutral, position_pct: 56.3, utilization_rating: low, channel_utilization: 0.294
    Length: 20.0
    Consolidation: price_range: 0.0, price_range_pct: 0.0, width_threshold: 2740.1671, is_consolidation: False, breakout_potential: low, consolidation_periods: 0.0
    Position: {'position': 'middle_third', 'position_pct': 56.3, 'distance_to_lower': 1758.97, 'distance_to_upper': 1364.02, 'distance_to_middle': 197.475}
    Support Resistance: {'lower': {'breaks': 0.0, 'bounces': 0.0, 'touches': 0.0, 'bounce_rate': 0.0}, 'upper': {'breaks': 0.0, 'bounces': 5.0, 'touches': 10.0, 'bounce_rate': 0.5}, 'middle': {'breaks': 0.0, 'bounces': 5.0, 'touches': 11.0, 'bounce_rate': 0.455}}
    Patterns: breakouts, width_analysis, turtle_patterns
    Quality: data_quality: {'total_periods': 81.0, 'width_corrections': 0.0, 'valid_data_percentage': 81.0}, calculation_notes: Donchian analysis based on 81 aligned data points with period 20

  adx:
    Current: {'adx': 24.69, 'plus_di': 17.1, 'minus_di': 21.86, 'timestamp': '2025-10-17T14:55:56.275788+00:00'}
    Summary: ADX 24.7 - Developing trend with bearish bias (4.8)
    Description: Developing trend
    Strength_Value: 24.69
    Trend_Strength: developing
    Trend_Evolution: stable
    Directional_Bias: bearish
    Directional_Strength: 4.77
    Weak Threshold: 20.0
    Current Strength: developing
    Strong Threshold: 25.0
    Extreme Threshold: 60.0
    Very Strong Threshold: 40.0

  atr:
    Current: {'value': 682.420403, 'timestamp': '2025-10-17T14:55:56.518344+00:00'}
    Summary: ATR 682.420403 - high volatility (86th percentile)
    Trend: strength: 0.008, velocity: 1.222106, direction: rising, consistency: 0.5, acceleration: -2.331295, interpretation: volatility_stable
    Breakout: breakout_setup: 0.0, squeeze_periods: 0.0, squeeze_detected: 0.0, expansion_potential: 0.0, recent_volatility_change_pct: 2.38
    Relative: regime: elevated_volatility, comparisons: {'5p_avg': 0.66, '10p_avg': 6.58, '20p_avg': 11.02, '50p_avg': 44.68}, regime_ratio: 1.447
    Cycles: {'cycle_detected': 0.0}
    Stop Loss: {'stop_levels': {'1.0x_atr': {'distance': 682.420403, 'long_stop': 104604.779597, 'short_stop': 105969.620403, 'distance_pct': 0.648}, '1.5x_atr': {'distance': 1023.630604, 'long_stop': 104263.569396, 'short_stop': 106310.830604, 'distance_pct': 0.972}, '2.0x_atr': {'distance': 1364.840806, 'long_stop': 103922.359194, 'short_stop': 106652.040806, 'distance_pct': 1.296}, '2.5x_atr': {'distance': 1706.051007, 'long_stop': 103581.148993, 'short_stop': 106993.251007, 'distance_pct': 1.62}, '3.0x_atr': {'distance': 2047.261209, 'long_stop': 103239.938791, 'short_stop': 107334.461209, 'distance_pct': 1.944}}, 'current_price': 105287.2, 'recommended_stop': {'distance': 1706.051007, 'long_stop': 103581.148993, 'short_stop': 106993.251007, 'distance_pct': 1.62}, 'recommended_multiplier': 2.5}
    Volatility: {'statistical': {'max': 838.096969, 'min': 283.516869, 'std': 144.903979, 'mean': 506.533064}, 'current_level': 'high', 'percentile_rank': 86.0, 'relative_to_mean': 34.72, 'relative_to_price_pct': 0.648}
    Quality: clarity: 1.00, consistency: 0.01, data_quality: 0.43

  bbw:
    Current: {'width': 2.04, 'timestamp': '2025-10-17T14:55:56.540520+00:00'}
    Summary: BB Width 2.04% - below average volatility (53th percentile) - WEAK SQUEEZE (2p)
    Trend: strength: 0.023, velocity: -0.035, direction: stable, acceleration: -0.061
    Breakout: potential: moderate, recent_change: -0.108, setup_quality: poor_setup, potential_score: 0.4, change_direction: contracting
    Expansion: cycle_stage: unclear, recent_peak: None, max_expansion: 2.04, recent_trough: None, cycle_position: unclear, expansion_peaks: 0.0, contraction_troughs: 0.0, avg_expansion_height: 2.04
    Cycles: {'total_cycles': 0.0, 'avg_cycle_length': None, 'expanding_time_pct': 33.3, 'contracting_time_pct': 66.7}
    Squeeze: {'is_squeeze': 1.0, 'squeeze_periods': 2.0, 'squeeze_quality': 'weak', 'squeeze_frequency': 0.642, 'squeeze_intensity': 0.0, 'squeeze_threshold': 2.04}
    Volatility: {'level': 'below_average', 'statistics': {'max': 5.72, 'min': 0.62, 'std': 1.55, 'mean': 2.25}, 'percentile_rank': 53.1, 'relative_to_mean': -9.15}
    Quality: clarity: 0.13, consistency: 0.02, data_quality: 0.41

  cci:
    Current: {'value': 14.51, 'timestamp': '2025-10-17T14:55:55.983519+00:00'}
    Summary: CCI at 14.5
    Length: 20.0
    Momentum: velocity: -6.84, volatility: 109.08, acceleration: 19.64, recent_range: 92.75, trend_strength: 0.342, trend_direction: falling, momentum_interpretation: falling_momentum
    Zero_Line: zero_crossings: 9.0, current_position: above, distance_from_zero: 14.51, time_above_zero_pct: 46.9, time_below_zero_pct: 53.1
    Oversold: {'level': -100.0, 'status': 'above', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'extreme_reading': False, 'time_percentage': 19.8}
    Overbought: {'level': 100.0, 'status': 'below', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'extreme_reading': False, 'time_percentage': 13.6}
    Zone: neutral
    Neutral Bias: bullish
    Quality: data_quality: {'total_periods': 81.0, 'recent_volatility': 30.568, 'valid_data_percentage': 81.0}, calculation_notes: CCI analysis based on 81 valid data points with period 20

  ema:
    Current: {'price': 105287.2, 'ema_value': 105465.2411, 'timestamp': '2025-10-17T14:55:56.384802+00:00', 'price_distance': -178.0411, 'price_distance_pct': -0.169}
    Summary: EMA 105465.2411 - falling trend, low responsiveness, price -0.2%
    Length: 20.0
    Responsiveness: avg_change: 63.85215, max_change: 226.443475, change_frequency: 0.175, direction_changes: 14.0, relative_volatility: 0.011912, responsiveness_score: 0.147, responsiveness_rating: low
    Signal_Quality: noise_level: low, signal_quality: low_frequency_high_reliability, recommended_use: Reliable for position trading, slower signals
    Trend: {'slope': -31.672207, 'strength': 0.165, 'consensus': 'falling', 'long_term': 'falling', 'short_term': 'sideways', 'consistency': 0.857, 'medium_term': 'sideways', 'acceleration': -8.886833}
    Price Relationship: {'distance': -178.0411, 'position': 'below', 'avg_distance': -431.032, 'distance_pct': -0.169, 'above_ema_pct': 34.6, 'below_ema_pct': 65.4, 'avg_distance_pct': -0.401}
    Support Resistance: {'success_rate': 0.486, 'effectiveness': 'medium', 'total_touches': 35.0, 'recent_bounces': [{'type': 'resistance_bounce', 'index': 67.0, 'strength': 0.0017416011055266377, 'periods_ago': 13.0}, {'type': 'support_bounce', 'index': 75.0, 'strength': 0.0048322044169820085, 'periods_ago': 5.0}, {'type': 'resistance_bounce', 'index': 77.0, 'strength': 0.0033522232442755604, 'periods_ago': 3.0}], 'recent_touches': [{'index': 75.0, 'price': 105326.67, 'ema_value': 105547.63691220447, 'periods_ago': 5.0}, {'index': 76.0, 'price': 105835.63, 'ema_value': 105575.06482532786, 'periods_ago': 4.0}, {'index': 77.0, 'price': 105419.59, 'ema_value': 105560.25769910617, 'periods_ago': 3.0}, {'index': 79.0, 'price': 105206.37, 'ema_value': 105483.98224348598, 'periods_ago': 1.0}, {'index': 80.0, 'price': 105287.2, 'ema_value': 105465.2410774397, 'periods_ago': 0.0}], 'successful_bounces': 17.0}
    Patterns: crossovers
    Quality: data_quality: {'had_sma': 0.0, 'had_prices': 1.0, 'has_price_data': 1.0, 'aligned_periods': 81.0, 'has_sma_comparison': 0.0, 'original_ema_periods': 100.0, 'valid_data_percentage': 81.0}, calculation_notes: EMA analysis based on 81 aligned data points with period 20

  mfi:
    Current: {'value': 39.99, 'timestamp': '2025-10-17T14:55:56.044345+00:00'}
    Summary: MFI at 40.0 (neutral, falling money flow), selling pressure
    Length: 14.0
    Position_Rank: percentile: 0.0, interpretation: extremely_low
    Zone: neutral
    Money Flow: {'pressure': 'selling', 'consistency': 1.0, 'flow_quality': 'low_quality_flow', 'cycle_analysis': {'cycle_detected': 0.0}, 'pressure_strength': 0.2, 'volume_confirmation': 'strong'}
    Patterns: momentum
    Quality: data_quality: {'had_prices': 1.0, 'original_periods': {'mfi': 100.0, 'prices': 100.0}, 'core_analysis_periods': 87.0, 'divergence_aligned_periods': 87.0}, calculation_notes: MFI analysis based on 87 core periods, divergence on 87 aligned periods

  obv:
    Current: {'value': -8903.79, 'timestamp': '2025-10-17T14:55:56.544175+00:00'}
    Summary: OBV -8904 - bullish trend (strong, 0.68), accumulation detected
    Length: 14.0
    Relative: max_obv: 1842.42, min_obv: -12250.76, position: lower_range, position_percentile: 23.7
    Trend: {'strength': 0.681, 'velocity': 230.8, 'consensus': 'bullish', 'long_term': 'sideways', 'short_term': 'bullish', 'consistency': 0.556, 'medium_term': 'bullish'}
    Accumulation: {'overall_phase': 'accumulation_phase', 'phase_strength': 'strong', 'timeframe_analysis': {'5p': {'score': 'strong_accumulation', 'change_pct': 2.62}, '10p': {'score': 'strong_accumulation', 'change_pct': 2.4}, '20p': {'score': 'strong_accumulation', 'change_pct': 16.72}}}
    Patterns: flow, momentum
    Quality: data_quality: {'had_prices': 1.0, 'had_volumes': 1.0, 'cleaned_periods': 100.0, 'original_periods': {'obv': 100.0, 'prices': 100.0, 'volumes': 100.0}}, calculation_notes: OBV analysis based on 100 periods with length 14

  roc:
    Current: {'value': -0.297, 'timestamp': '2025-10-17T14:55:56.072449+00:00', 'value_pct': '-0.30%'}
    Summary: ROC -0.30% - very_weak negative momentum
    Trend: slope: 0.042, strength: 0.021, direction: sideways, consistency: 0.506
    Length: 10.0
    Momentum: strength: 0.2969107981629751, direction: negative, evolution: decelerating, persistence: 1.0, strength_level: very_weak
    Velocity: velocity: 0.042, acceleration: 0.617, interpretation: stable_momentum
    Calculation_Periods: 90.0
    Extremes: {'condition': 'neutral', 'current_streak': 0.0, 'oversold_time_pct': 10.0, 'oversold_threshold': -2.09, 'overbought_time_pct': 2.2, 'overbought_threshold': 1.2, 'extreme_oversold_threshold': -4.56, 'extreme_overbought_threshold': 3.66}
    Zero Line: {'position': 'below_zero', 'above_zero_pct': 40.0, 'below_zero_pct': 60.0, 'recent_crosses': [{'type': 'bearish_zero_cross', 'value': -0.462, 'periods_ago': 6.0}], 'total_crossings': 14.0, 'crossing_frequency': 0.156}
    Patterns: double_pattern
    Quality: data_quality: {'had_prices': 1.0, 'clean_periods': 90.0, 'original_periods': 90.0, 'calculation_periods': 10.0, 'valid_data_percentage': 100.0}, calculation_notes: ROC analysis based on 90 periods with length=10

  rsi:
    Current: {'value': 45.65, 'timestamp': '2025-10-17T14:55:55.873042+00:00'}
    Summary: RSI at 45.6
    Ma5: 46.05
    Ma10: 44.9
    Trend: strength: 0.039, velocity: -0.223, direction: sideways, acceleration: -0.412
    Volatility: 13.165
    Neutral: {'level': 50.0, 'status': 'below', 'distance': -4.35}
    Oversold: {'level': 30.0, 'status': 'far_above', 'periods_in_zone': 0.0, 'time_percentage': 19.8}
    Overbought: {'level': 70.0, 'status': 'far_below', 'periods_in_zone': 0.0, 'time_percentage': 0.0}
    Quality: data_quality: {'total_periods': 86.0, 'recent_volatility': 3.273, 'valid_data_percentage': 86.0}, calculation_notes: RSI analysis based on 86 valid data points

  sma:
    Current: {'price': 105287.2, 'sma_value': 105316.8335, 'timestamp': '2025-10-17T14:55:56.413321+00:00', 'price_distance': -29.6335, 'price_distance_pct': -0.028}
    Summary: SMA 105316.8335 - bearish trend, price below (-0.0%)
    Slope: alignment: aligned, direction: upward, acceleration: 7.67275, long_term_slope: 9.58815, short_term_slope: 14.122667, medium_term_slope: 19.7421
    Trend: slope: 19.7421, strength: 0.148, consensus: bearish, long_term: bearish, short_term: sideways, consistency: 0.667, medium_term: sideways
    Length: 20.0
    Quality: smoothness: 0.988, trend_clarity: 0.875, responsiveness: 0.066, overall_quality: 0.931
    Smoothing_Factor: 0.0952
    Current Level: 105316.8335
    Trend Direction: bearish
    Price Relationship: {'distance': -29.6335, 'position': 'below', 'distance_pct': -0.028, 'above_sma_pct': 43.2, 'below_sma_pct': 56.8, 'position_changes': 10, 'position_stability': 0.875}
    Support Resistance: {'success_rate': 0.449, 'effectiveness': 'medium', 'total_touches': 49.0, 'recent_bounces': [{'type': 'resistance_bounce', 'index': 71.0, 'strength': 0.00272005061827346, 'periods_ago': 9.0}, {'type': 'resistance_bounce', 'index': 72.0, 'strength': 0.004115598991555677, 'periods_ago': 8.0}, {'type': 'resistance_bounce', 'index': 77.0, 'strength': 0.0033522232442755604, 'periods_ago': 3.0}], 'recent_touches': [{'index': 75.0, 'price': 105326.67, 'sma_value': 105218.12299999999, 'periods_ago': 5.0}, {'index': 77.0, 'price': 105419.59, 'sma_value': 105274.4655, 'periods_ago': 3.0}, {'index': 78.0, 'price': 105066.2, 'sma_value': 105272.5815, 'periods_ago': 2.0}, {'index': 79.0, 'price': 105206.37, 'sma_value': 105279.041, 'periods_ago': 1.0}, {'index': 80.0, 'price': 105287.2, 'sma_value': 105316.8335, 'periods_ago': 0.0}], 'successful_bounces': 22.0}
    Patterns: crossovers, slope_direction, trend_alignment
    Quality: data_quality: {'had_prices': 1.0, 'aligned_periods': 81.0, 'original_periods': 81.0, 'calculation_periods': 20.0, 'valid_data_percentage': 100.0}, calculation_notes: SMA analysis based on 81 periods with length=20

  macd:
    Current: {'macd': -238.789, 'signal': -305.4909, 'histogram': 66.7019, 'timestamp': '2025-10-17T14:55:55.915822+00:00'}
    Summary: MACD rising trend with increasing momentum
    Histogram: {'acceleration': -5.0023, 'histogram_strength': 66.70191979448339, 'momentum_direction': 'decreasing', 'zero_crossings_recent': 0.0}
    Zero Line: {'current_position': 'below', 'distance_from_zero': 238.789, 'time_above_zero_pct': 28.4, 'time_below_zero_pct': 71.6}
    Patterns: crossovers
    Quality: data_quality: {'aligned_periods': 67.0, 'original_periods': {'macd': 100.0, 'prices': 100.0, 'signal': 100.0, 'histogram': 100.0}, 'valid_data_percentage': 67.0}, calculation_notes: MACD analysis based on 67 aligned data points
    Legacy Trend: bullish

  psar:
    Current: {'price': 105287.2, 'distance': -1321.6598, 'timestamp': '2025-10-17T14:55:56.354348+00:00', 'psar_value': 106608.8598, 'distance_percentage': -1.255}
    Summary: PSAR 106608.8598 - bearish trend for 2 periods, 1.26% from price. Recent reversal 2p ago
    Trend: trend_periods: 2.0, trend_strength: 1.0, current_direction: bearish, trend_consistency: 0.8, strength_interpretation: very_strong
    Length: 14.0
    Distance: max_distance: 2681.036, min_distance: -2933.9291, average_distance: -198.4006, current_absolute: -1321.6598, distance_volatility: 1244.2574, current_relative_pct: -1.255, distance_interpretation: wide_distance
    Acceleration: velocity: 640.093543, acceleration: 830.305486, rate_of_change_5p: 1.914, acceleration_interpretation: accelerating_upward
    Calculation_Periods: 99.0
    Trend Direction: unknown
    Stop Distance Pct: 1.255
    Current Stop Level: 106608.8598
    Patterns: signal_analysis
    Quality: stop_loss: {'stop_type': 'trailing_stop', 'performance': {'total_tests': 88.0, 'successful_stops': 72.0, 'effectiveness_rate': 0.818}, 'stop_distance': 1321.6598, 'recommendation': 'reasonable_stop', 'stop_distance_pct': 1.255, 'current_stop_level': 106608.8598}, data_quality: {'aligned_periods': 99.0, 'had_high_low_data': 1.0, 'calculation_periods': 14.0}, calculation_notes: Parabolic SAR analysis based on 99 aligned periods

  trix:
    Current: {'trix': -0.036871, 'signal': 105287.2, 'histogram': -105287.236871, 'timestamp': '2025-10-17T14:55:56.216075+00:00'}
    Summary: TRIX -0.036871 - moderate bearish momentum, histogram -105287.236871 (below zero)
    Trend: strength: 0.095, velocity: 0.002907, direction: sideways, acceleration: -0.002416
    Momentum: direction: bearish, persistence: 1.0, strength_level: moderate
    Volatility: 0.04529
    Zero Line: {'position': 'below_zero', 'above_zero_pct': 23.3, 'below_zero_pct': 76.7, 'recent_crossings': []}
    Signal Line: {'latest_crossover': None, 'recent_crossovers': [], 'crossover_frequency': 0.0}
    Quality: data_quality: {'had_prices': 0.0, 'had_signal': 1.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'acceleration': 4.0, 'turning_points': 14.0}, 'aligned_periods': 86.0}, calculation_notes: TRIX analysis based on 86 aligned periods with length=14

  vwap:
    Current: {'price': 105287.2, 'timestamp': '2025-10-17T14:55:56.565470+00:00', 'vwap_value': 105956.2969, 'price_distance': -669.0969, 'price_distance_pct': -0.631}
    Summary: VWAP 105956.2969, price below (-0.6%) - slightly undervalued
    Trend: strength: 0.009, velocity: -13.895872, direction: sideways, smoothness: 0.988
    Anchored: momentum: -13.895872, reset_detected: False, behavior_quality: stable, direction_consistency: 0.778
    Fair_Value: assessment: slightly_undervalued, distance_pct: -0.631, reversion_tendency: low
    Volatility: 669.295
    Volume_Profile: volume_bias: below_vwap, avg_volume_above: 279.52, avg_volume_below: 526.46, near_vwap_volume_pct: 29.9, above_vwap_volume_pct: 15.0, below_vwap_volume_pct: 85.0, institutional_activity: high
    Price Position: {'bias': 'bearish', 'current': 'below', 'above_vwap_pct': 25.0, 'below_vwap_pct': 75.0, 'position_changes': 12.0}
    Deviation Bands: {'lower_1std': 105287.0019, 'lower_2std': 104617.7068, 'upper_1std': 106625.5919, 'upper_2std': 107294.8869, 'current_position': 'within_1std', 'std_devs_from_vwap': -1.0}
    Patterns: volume_clustering
    Quality: data_quality: {'had_volumes': 1.0, 'aligned_periods': 100.0, 'volume_profile_available': 1.0, 'support_resistance_touches': 25.0}, calculation_notes: VWAP analysis based on 100 aligned price/VWAP periods

  aroon:
    Current: {'aroon_up': 0.0, 'timestamp': '2025-10-17T14:55:56.136405+00:00', 'aroon_down': 92.86, 'oscillator': -92.86}
    Summary: Aroon Up: 0.0, Down: 92.9 - strong_downtrend for 2 periods (strong bearish)
    Trend: separation: 92.86, current_trend: strong_downtrend, trend_quality: poor, trend_duration: 2.0, trend_strength: 0.929, trend_consistency: 0.2
    Strength: up_momentum: -7.14, up_evolution: falling, down_momentum: 30.95, down_evolution: rising, aroon_up_strength: very_weak, combined_strength: very_strong, dominant_indicator: aroon_down, aroon_down_strength: very_strong
    Parallel_Movement: correlation: -0.518, movement_type: moderate_negative_correlation, interpretation: Some opposition in indicator movement
    Crossovers: {'latest_crossover': {'type': 'bearish_crossover', 'location': 'mid_levels', 'strength': 92.85714285714286, 'up_value': 7.14, 'down_value': 100.0, 'periods_ago': 2.0}, 'recent_crossovers': [{'type': 'bearish_crossover', 'location': 'mid_levels', 'strength': 92.85714285714286, 'up_value': 7.14, 'down_value': 100.0, 'periods_ago': 2.0}], 'crossover_frequency': 'low'}
    Oscillator: {'zone': 'strong_bearish', 'velocity': -38.1, 'acceleration': -53.57, 'current_value': -92.86, 'zero_crossings': 6.0, 'time_above_zero_pct': 47.7, 'time_below_zero_pct': 52.3, 'oscillator_interpretation': 'strong_bearish_momentum'}
    Patterns: extreme_readings
    Quality: clarity: 0.93, consistency: 0.20, data_quality: 0.43

  vortex:
    Current: {'spread': -0.1556, 'vi_plus': 0.9366, 'dominant': 'VI-', 'vi_minus': 1.0922, 'timestamp': '2025-10-17T14:55:56.164461+00:00'}
    Summary: Vortex VI+ 0.937, VI- 1.092 - VI minus dominant (+0.156), bearish crossover 2p ago
    Trend: strength: 0.162, velocity: -0.14151, direction: falling, acceleration: -0.161733
    Dominance: current: VI_minus, strength: 0.1556, persistence: 0.4
    Volatility: 0.4256
    One Line: {'recent_crosses': {'plus_crosses': [{'type': 'downward_cross', 'value': 0.9857, 'periods_ago': 2.0}, {'type': 'upward_cross', 'value': 1.0372, 'periods_ago': 7.0}, {'type': 'downward_cross', 'value': 0.983, 'periods_ago': 8.0}], 'minus_crosses': [{'type': 'upward_cross', 'value': 1.0516, 'periods_ago': 2.0}, {'type': 'downward_cross', 'value': 0.9535, 'periods_ago': 7.0}, {'type': 'upward_cross', 'value': 1.0093, 'periods_ago': 8.0}]}, 'vi_plus_vs_one': 'below', 'vi_minus_vs_one': 'above', 'plus_above_one_pct': 51.2, 'minus_above_one_pct': 58.1}
    Vi Crossovers: [{'type': 'bearish_crossover', 'vi_plus': 0.9857, 'strength': 0.066, 'vi_minus': 1.0516, 'periods_ago': 2.0, 'crossover_level': 1.0187}, {'type': 'bullish_crossover', 'vi_plus': 1.0372, 'strength': 0.084, 'vi_minus': 0.9535, 'periods_ago': 7.0, 'crossover_level': 0.9954}, {'type': 'bearish_crossover', 'vi_plus': 0.983, 'strength': 0.026, 'vi_minus': 1.0093, 'periods_ago': 8.0, 'crossover_level': 0.9962}]
    Key Level Crosses: [{'level': 1.0, 'strength': 0.014295752194776523, 'direction': 'down', 'periods_ago': 2.0}, {'level': 1.0, 'strength': 0.03723133510819965, 'direction': 'up', 'periods_ago': 7.0}, {'level': 1.0, 'strength': 0.016967983779406115, 'direction': 'down', 'periods_ago': 8.0}]
    Patterns: compression, parallel_movement
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'persistence': 5.0, 'crossover_scan': 14.0}, 'aligned_periods': 86.0}, calculation_notes: Vortex analysis based on 86 aligned VI+/VI- periods

  stochastic:
    Current: {'spread': -5.21, 'd_percent': 36.48, 'k_percent': 31.28, 'timestamp': '2025-10-17T14:55:55.938731+00:00'}
    Summary: Stochastic %K: 31.3, %D: 36.5. Bearish Crossover 4p ago
    Trend: momentum: strong_bearish_acceleration, velocity: -7.06, k_direction: falling, acceleration: -11.15
    Volatility: 28.18
    Spread_Momentum: 7.42
    Neutral: {'bias': 'bearish', 'level': 50.0, 'distance_from_50': -18.72}
    Oversold: {'level': 20.0, 'status': 'above', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'time_percentage': 25.3}
    Overbought: {'level': 80.0, 'status': 'below', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'time_percentage': 14.5}
    Patterns: momentum
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'aligned_periods': 83.0, 'valid_data_percentage': 95.4}, calculation_notes: Stochastic analysis based on 83 aligned K/D periods

  williams_r:
    Current: {'value': -57.78, 'timestamp': '2025-10-17T14:55:55.960851+00:00'}
    Summary: Williams %R at -57.8, strong upward acceleration
    Trend: strength: 0.17, velocity: 11.191, direction: falling, acceleration: 7.987
    Momentum: volatility: 29.34, recent_range: 49.87, interpretation: strong_upward_acceleration
    Volatility: 29.335
    Neutral: {'bias': 'bearish', 'level': -50.0, 'distance_from_50': -7.78}
    Oversold: {'level': -80.0, 'status': 'above', 'exit_analysis': {'latest_exit': {'strength': 0.5891331957828114, 'exit_level': -68.22, 'periods_ago': 2.0}, 'recent_exits': [{'strength': 0.5891331957828114, 'exit_level': -68.22, 'periods_ago': 2.0}]}, 'streak_length': 0.0, 'time_percentage': 28.7}
    Overbought: {'level': -20.0, 'status': 'below', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'time_percentage': 14.9}
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'acceleration': 4.0, 'position_rank': 14.0}, 'aligned_periods': 87.0}, calculation_notes: Williams %R analysis based on 87 periods with length=14

  bollinger_bands:
    Current: {'lower': 104241.1245, 'upper': 106392.5425, 'middle': 105316.8335, 'bandwidth': 2.0428, 'percent_b': 0.4862}

=== 1D TIMEFRAME ===
  dc:
    Current: {'price': 105257.54, 'timestamp': '2025-10-17T14:56:13.812441+00:00', 'channel_width': 24199.63, 'lower_channel': 102000.0, 'upper_channel': 126199.63, 'middle_channel': 114099.815, 'price_position_pct': 13.5}
    Summary: Donchian: Price 105257.5400 (13.5%), Width 24199.6300
    Trend: strength: strong_downward, position_pct: 13.5, utilization_rating: medium, channel_utilization: 0.746
    Length: 20.0
    Consolidation: price_range: 0.0, price_range_pct: 0.0, width_threshold: 10877.6576, is_consolidation: False, breakout_potential: low, consolidation_periods: 0.0
    Position: {'position': 'near_lower', 'position_pct': 13.5, 'distance_to_lower': 3257.54, 'distance_to_upper': 20942.09, 'distance_to_middle': 8842.275}
    Support Resistance: {'lower': {'breaks': 0.0, 'bounces': 0.0, 'touches': 0.0, 'bounce_rate': 0.0}, 'upper': {'breaks': 0.0, 'bounces': 2.0, 'touches': 2.0, 'bounce_rate': 1.0}, 'middle': {'breaks': 0.0, 'bounces': 0.0, 'touches': 0.0, 'bounce_rate': 0.0}}
    Patterns: breakouts, width_analysis, turtle_patterns
    Quality: data_quality: {'total_periods': 181.0, 'width_corrections': 0.0, 'valid_data_percentage': 90.5}, calculation_notes: Donchian analysis based on 181 aligned data points with period 20

  adx:
    Current: {'adx': 32.75, 'plus_di': 13.9, 'minus_di': 38.89, 'timestamp': '2025-10-17T14:56:13.752329+00:00'}
    Summary: ADX 32.7 - Strong trending market with bearish bias (25.0)
    Description: Strong trending market
    Strength_Value: 32.75
    Trend_Strength: strong
    Trend_Evolution: stable
    Directional_Bias: bearish
    Directional_Strength: 24.99
    Weak Threshold: 20.0
    Current Strength: strong
    Strong Threshold: 25.0
    Extreme Threshold: 60.0
    Very Strong Threshold: 40.0
    Patterns: di_patterns

  atr:
    Current: {'value': 4340.465548, 'timestamp': '2025-10-17T14:56:13.823935+00:00'}
    Summary: ATR 4340.465548 - extremely high volatility (100th percentile)
    Trend: strength: 0.059, velocity: 23.840903, direction: rising, consistency: 0.75, acceleration: -548.345661, interpretation: volatility_stable
    Breakout: breakout_setup: 0.0, squeeze_periods: 0.0, squeeze_detected: 0.0, expansion_potential: 0.0, recent_volatility_change_pct: 4.07
    Relative: regime: high_volatility, comparisons: {'5p_avg': 2.25, '10p_avg': 9.37, '20p_avg': 32.95, '50p_avg': 50.23}, regime_ratio: 1.502
    Cycles: {'recent_peaks': 6.0, 'cycle_detected': 1.0, 'cycle_position': 'post_peak_contraction', 'recent_troughs': 3.0, 'avg_expansion_cycle': 34.2, 'avg_contraction_cycle': 53.0}
    Stop Loss: {'stop_levels': {'1.0x_atr': {'distance': 4340.465548, 'long_stop': 100917.074452, 'short_stop': 109598.005548, 'distance_pct': 4.124}, '1.5x_atr': {'distance': 6510.698322, 'long_stop': 98746.841678, 'short_stop': 111768.238322, 'distance_pct': 6.185}, '2.0x_atr': {'distance': 8680.931096, 'long_stop': 96576.608904, 'short_stop': 113938.471096, 'distance_pct': 8.247}, '2.5x_atr': {'distance': 10851.16387, 'long_stop': 94406.37613, 'short_stop': 116108.70387, 'distance_pct': 10.309}, '3.0x_atr': {'distance': 13021.396644, 'long_stop': 92236.143356, 'short_stop': 118278.936644, 'distance_pct': 12.371}}, 'current_price': 105257.54, 'recommended_stop': {'distance': 10851.16387, 'long_stop': 94406.37613, 'short_stop': 116108.70387, 'distance_pct': 10.309}, 'recommended_multiplier': 2.5}
    Volatility: {'statistical': {'max': 4340.465548, 'min': 2150.652345, 'std': 405.782091, 'mean': 2903.345153}, 'current_level': 'extremely_high', 'percentile_rank': 99.5, 'relative_to_mean': 49.5, 'relative_to_price_pct': 4.124}
    Quality: clarity: 1.00, consistency: 0.06, data_quality: 0.93

  bbw:
    Current: {'width': 19.15, 'timestamp': '2025-10-17T14:56:13.830111+00:00'}
    Summary: BB Width 19.15% - high volatility (92th percentile)
    Trend: strength: 0.089, velocity: 0.426, direction: stable, acceleration: 0.67
    Breakout: potential: low, recent_change: 1.695, setup_quality: poor_setup, potential_score: 0.2, change_direction: expanding
    Expansion: cycle_stage: unclear, recent_peak: None, max_expansion: 19.15, recent_trough: None, cycle_position: unclear, expansion_peaks: 0.0, contraction_troughs: 0.0, avg_expansion_height: 19.15
    Cycles: {'total_cycles': 0.0, 'avg_cycle_length': None, 'expanding_time_pct': 38.7, 'contracting_time_pct': 61.3}
    Squeeze: {'is_squeeze': 0.0, 'squeeze_periods': 0.0, 'squeeze_quality': 'weak', 'squeeze_frequency': 0.425, 'squeeze_intensity': 0.0, 'squeeze_threshold': 8.46}
    Volatility: {'level': 'high', 'statistics': {'max': 24.41, 'min': 2.73, 'std': 4.78, 'mean': 11.77}, 'percentile_rank': 92.3, 'relative_to_mean': 62.79}
    Quality: clarity: 1.00, consistency: 0.09, data_quality: 0.91

  cci:
    Current: {'value': -138.75, 'timestamp': '2025-10-17T14:56:13.684200+00:00'}
    Summary: CCI at -138.8 (oversold for 2 periods), strong falling momentum
    Length: 20.0
    Momentum: velocity: -29.33, volatility: 109.24, acceleration: 36.04, recent_range: 237.79, trend_strength: 1.0, trend_direction: falling, momentum_interpretation: strong_falling_momentum
    Zero_Line: zero_crossings: 13.0, current_position: below, distance_from_zero: 138.75, time_above_zero_pct: 62.4, time_below_zero_pct: 37.6
    Oversold: {'level': -100.0, 'status': 'in_zone', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 2.0, 'extreme_reading': False, 'time_percentage': 13.3}
    Overbought: {'level': 100.0, 'status': 'below', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'extreme_reading': False, 'time_percentage': 26.0}
    Zone: oversold
    Neutral Bias: bearish
    Quality: data_quality: {'total_periods': 181.0, 'recent_volatility': 72.925, 'valid_data_percentage': 90.5}, calculation_notes: CCI analysis based on 181 valid data points with period 20

  ema:
    Current: {'price': 105257.54, 'ema_value': 114264.9813, 'timestamp': '2025-10-17T14:56:13.793629+00:00', 'price_distance': -9007.4413, 'price_distance_pct': -7.883}
    Summary: EMA 114264.9813 - falling trend (strength: 0.57), moderate responsiveness, price -7.9%
    Length: 20.0
    Responsiveness: avg_change: 344.84987, max_change: 981.927861, change_frequency: 0.117, direction_changes: 21.0, relative_volatility: 0.080279, responsiveness_score: 0.46, responsiveness_rating: moderate
    Signal_Quality: noise_level: low, signal_quality: balanced, recommended_use: Good for general trend following with moderate filters
    Trend: {'slope': -744.385046, 'strength': 0.57, 'consensus': 'falling', 'long_term': 'falling', 'short_term': 'falling', 'consistency': 1.0, 'medium_term': 'falling', 'acceleration': -385.581938}
    Price Relationship: {'distance': -9007.4413, 'position': 'below', 'avg_distance': 1656.3283, 'distance_pct': -7.883, 'above_ema_pct': 65.7, 'below_ema_pct': 34.3, 'avg_distance_pct': 1.528}
    Support Resistance: {'success_rate': 0.375, 'effectiveness': 'medium', 'total_touches': 8.0, 'recent_bounces': [{'type': 'resistance_bounce', 'index': 39.0, 'strength': 0.015193425498213644, 'periods_ago': 141.0}, {'type': 'resistance_bounce', 'index': 44.0, 'strength': 0.00645331248625765, 'periods_ago': 136.0}, {'type': 'support_bounce', 'index': 118.0, 'strength': 0.0002074447357851904, 'periods_ago': 62.0}], 'recent_touches': [{'index': 117.0, 'price': 117342.05, 'ema_value': 117512.59778635675, 'periods_ago': 63.0}, {'index': 118.0, 'price': 117380.66, 'ema_value': 117500.0322828942, 'periods_ago': 62.0}, {'index': 119.0, 'price': 117405.01, 'ema_value': 117490.98254166618, 'periods_ago': 61.0}, {'index': 141.0, 'price': 112065.23, 'ema_value': 111855.06544087043, 'periods_ago': 39.0}, {'index': 142.0, 'price': 111546.39, 'ema_value': 111825.66777983516, 'periods_ago': 38.0}], 'successful_bounces': 3.0}
    Patterns: crossovers
    Quality: data_quality: {'had_sma': 0.0, 'had_prices': 1.0, 'has_price_data': 1.0, 'aligned_periods': 181.0, 'has_sma_comparison': 0.0, 'original_ema_periods': 200.0, 'valid_data_percentage': 90.5}, calculation_notes: EMA analysis based on 181 aligned data points with period 20

  mfi:
    Current: {'value': 33.33, 'timestamp': '2025-10-17T14:56:13.706707+00:00'}
    Summary: MFI at 33.3 (neutral, falling money flow), selling pressure
    Length: 14.0
    Position_Rank: percentile: 0.0, interpretation: extremely_low
    Zone: neutral
    Money Flow: {'pressure': 'selling', 'consistency': 1.0, 'flow_quality': 'low_quality_flow', 'cycle_analysis': {'cycle_detected': 0.0}, 'pressure_strength': 0.333, 'volume_confirmation': 'strong'}
    Patterns: momentum
    Quality: data_quality: {'had_prices': 1.0, 'original_periods': {'mfi': 200.0, 'prices': 200.0}, 'core_analysis_periods': 187.0, 'divergence_aligned_periods': 187.0}, calculation_notes: MFI analysis based on 187 core periods, divergence on 187 aligned periods

  obv:
    Current: {'value': 261287.82, 'timestamp': '2025-10-17T14:56:13.831696+00:00'}
    Summary: OBV 261288 - bearish trend (strong, 1.00), distribution detected
    Length: 14.0
    Relative: max_obv: 522701.91, min_obv: -19741.06, position: middle_range, position_percentile: 51.8
    Trend: {'strength': 1.0, 'velocity': -18409.41, 'consensus': 'bearish', 'long_term': 'bearish', 'short_term': 'bearish', 'consistency': 0.778, 'medium_term': 'bearish'}
    Accumulation: {'overall_phase': 'distribution_phase', 'phase_strength': 'strong', 'timeframe_analysis': {'5p': {'score': 'strong_distribution', 'change_pct': -30.49}, '10p': {'score': 'strong_distribution', 'change_pct': -40.92}, '20p': {'score': 'strong_distribution', 'change_pct': -21.53}}}
    Patterns: flow, momentum
    Quality: data_quality: {'had_prices': 1.0, 'had_volumes': 1.0, 'cleaned_periods': 200.0, 'original_periods': {'obv': 200.0, 'prices': 200.0, 'volumes': 200.0}}, calculation_notes: OBV analysis based on 200 periods with length 14

  roc:
    Current: {'value': -13.249, 'timestamp': '2025-10-17T14:56:13.710905+00:00', 'value_pct': '-13.25%'}
    Summary: ROC -13.25% - very_strong negative momentum, oversold (4p)
    Trend: slope: -1.866, strength: 0.933, direction: falling, consistency: 0.55
    Length: 10.0
    Momentum: strength: 13.249006143838097, direction: negative, evolution: decelerating, persistence: 1.0, strength_level: very_strong
    Velocity: velocity: -1.866, acceleration: 0.278, interpretation: decelerating_momentum
    Calculation_Periods: 190.0
    Extremes: {'condition': 'oversold', 'current_streak': 4.0, 'oversold_time_pct': 4.7, 'oversold_threshold': -6.32, 'overbought_time_pct': 8.4, 'overbought_threshold': 10.14, 'extreme_oversold_threshold': -18.66, 'extreme_overbought_threshold': 22.48}
    Zero Line: {'position': 'below_zero', 'above_zero_pct': 62.1, 'below_zero_pct': 37.9, 'recent_crosses': [{'type': 'bearish_zero_cross', 'value': -1.117, 'periods_ago': 8.0}], 'total_crossings': 20.0, 'crossing_frequency': 0.105}
    Quality: data_quality: {'had_prices': 1.0, 'clean_periods': 190.0, 'original_periods': 190.0, 'calculation_periods': 10.0, 'valid_data_percentage': 100.0}, calculation_notes: ROC analysis based on 190 periods with length=10

  rsi:
    Current: {'value': 33.68, 'timestamp': '2025-10-17T14:56:13.622900+00:00'}
    Summary: RSI at 33.7, falling
    Ma5: 40.63
    Ma10: 45.59
    Trend: strength: 0.265, velocity: -3.462, direction: falling, acceleration: 7.158
    Volatility: 10.959
    Neutral: {'level': 50.0, 'status': 'below', 'distance': -16.32}
    Oversold: {'level': 30.0, 'status': 'above', 'periods_in_zone': 0.0, 'time_percentage': 0.0}
    Overbought: {'level': 70.0, 'status': 'far_below', 'periods_in_zone': 0.0, 'time_percentage': 15.6}
    Quality: data_quality: {'total_periods': 186.0, 'recent_volatility': 9.948, 'valid_data_percentage': 93.0}, calculation_notes: RSI analysis based on 186 valid data points

  sma:
    Current: {'price': 105257.54, 'sma_value': 116475.066, 'timestamp': '2025-10-17T14:56:13.801644+00:00', 'price_distance': -11217.526, 'price_distance_pct': -9.631}
    Summary: SMA 116475.0660 - bullish trend, price below (-9.6%)
    Slope: alignment: mixed, direction: downward, acceleration: -88.68525, long_term_slope: 29.5046, short_term_slope: -67.645, medium_term_slope: -11.7036
    Trend: slope: -11.7036, strength: 0.013, consensus: bullish, long_term: bullish, short_term: sideways, consistency: 0.556, medium_term: sideways
    Length: 20.0
    Quality: smoothness: 0.918, trend_clarity: 0.833, responsiveness: 0.281, overall_quality: 0.876
    Smoothing_Factor: 0.0952
    Current Level: 116475.066
    Trend Direction: bullish
    Price Relationship: {'distance': -11217.526, 'position': 'below', 'distance_pct': -9.631, 'above_sma_pct': 62.4, 'below_sma_pct': 37.6, 'position_changes': 19, 'position_stability': 0.894}
    Support Resistance: {'success_rate': 0.389, 'effectiveness': 'medium', 'total_touches': 18.0, 'recent_bounces': [{'type': 'support_bounce', 'index': 111.0, 'strength': 0.024314831629991648, 'periods_ago': 69.0}, {'type': 'resistance_bounce', 'index': 119.0, 'strength': 0.010033302667407396, 'periods_ago': 61.0}, {'type': 'support_bounce', 'index': 140.0, 'strength': 0.008349039125823953, 'periods_ago': 40.0}], 'recent_touches': [{'index': 140.0, 'price': 111137.34, 'sma_value': 111577.76550000001, 'periods_ago': 40.0}, {'index': 141.0, 'price': 112065.23, 'sma_value': 111537.37999999998, 'periods_ago': 39.0}, {'index': 142.0, 'price': 111546.39, 'sma_value': 111401.1375, 'periods_ago': 38.0}, {'index': 162.0, 'price': 114311.96, 'sma_value': 114078.75, 'periods_ago': 18.0}, {'index': 163.0, 'price': 114048.93, 'sma_value': 114083.1965, 'periods_ago': 17.0}], 'successful_bounces': 7.0}
    Patterns: crossovers, slope_direction, trend_alignment
    Quality: data_quality: {'had_prices': 1.0, 'aligned_periods': 181.0, 'original_periods': 181.0, 'calculation_periods': 20.0, 'valid_data_percentage': 100.0}, calculation_notes: SMA analysis based on 181 periods with length=20

  macd:
    Current: {'macd': -1592.8738, 'signal': -3.9931, 'histogram': -1588.8807, 'timestamp': '2025-10-17T14:56:13.636869+00:00'}
    Summary: MACD falling trend with decreasing momentum
    Histogram: {'acceleration': -262.687, 'histogram_strength': 1588.8806872877828, 'momentum_direction': 'decreasing', 'zero_crossings_recent': 1.0}
    Zero Line: {'current_position': 'below', 'distance_from_zero': 1592.8738, 'time_above_zero_pct': 77.8, 'time_below_zero_pct': 22.2}
    Patterns: crossovers
    Quality: data_quality: {'aligned_periods': 167.0, 'original_periods': {'macd': 200.0, 'prices': 200.0, 'signal': 200.0, 'histogram': 200.0}, 'valid_data_percentage': 83.5}, calculation_notes: MACD analysis based on 167 aligned data points
    Legacy Trend: bearish

  psar:
    Current: {'price': 105257.54, 'distance': -17750.7767, 'timestamp': '2025-10-17T14:56:13.776905+00:00', 'psar_value': 123008.3167, 'distance_percentage': -16.864}
    Summary: PSAR 123008.3167 - bearish trend for 8 periods, 16.86% from price
    Trend: trend_periods: 8.0, trend_strength: 1.0, current_direction: bearish, trend_consistency: 0.8, strength_interpretation: very_strong
    Length: 14.0
    Distance: max_distance: 12245.1029, min_distance: -17750.7767, average_distance: 854.3841, current_absolute: -17750.7767, distance_volatility: 6416.6377, current_relative_pct: -16.864, distance_interpretation: very_wide_distance
    Acceleration: velocity: -437.550499, acceleration: 46.036607, rate_of_change_5p: -1.417, acceleration_interpretation: decelerating_downward
    Calculation_Periods: 199.0
    Trend Direction: unknown
    Stop Distance Pct: 16.864
    Current Stop Level: 123008.3167
    Patterns: signal_analysis
    Quality: stop_loss: {'stop_type': 'trailing_stop', 'performance': {'total_tests': 82.0, 'successful_stops': 40.0, 'effectiveness_rate': 0.488}, 'stop_distance': 17750.7767, 'recommendation': 'very_wide_stop', 'stop_distance_pct': 16.864, 'current_stop_level': 123008.3167}, data_quality: {'aligned_periods': 199.0, 'had_high_low_data': 1.0, 'calculation_periods': 14.0}, calculation_notes: Parabolic SAR analysis based on 199 aligned periods

  trix:
    Current: {'trix': 0.005022, 'signal': 105257.54, 'histogram': -105257.534978, 'timestamp': '2025-10-17T14:56:13.742282+00:00'}
    Summary: TRIX 0.005022 - weak bullish momentum, histogram -105257.534978 (above zero)
    Trend: strength: 0.13, velocity: -0.050371, direction: falling, acceleration: -0.023726
    Momentum: direction: bullish, persistence: 1.0, strength_level: weak
    Volatility: 0.235886
    Zero Line: {'position': 'above_zero', 'above_zero_pct': 79.0, 'below_zero_pct': 18.3, 'recent_crossings': []}
    Signal Line: {'latest_crossover': None, 'recent_crossovers': [], 'crossover_frequency': 0.0}
    Patterns: histogram_momentum
    Quality: data_quality: {'had_prices': 0.0, 'had_signal': 1.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'acceleration': 4.0, 'turning_points': 14.0}, 'aligned_periods': 186.0}, calculation_notes: TRIX analysis based on 186 aligned periods with length=14

  vwap:
    Current: {'price': 105257.54, 'timestamp': '2025-10-17T14:56:13.840498+00:00', 'vwap_value': 106008.59, 'price_distance': -751.05, 'price_distance_pct': -0.708}
    Summary: VWAP 106008.5900, price below (-0.7%) - slightly undervalued
    Trend: strength: 0.156, velocity: -2752.31, direction: falling, smoothness: 0.899
    Anchored: momentum: -2752.31, reset_detected: False, behavior_quality: choppy, direction_consistency: 0.518
    Fair_Value: assessment: slightly_undervalued, distance_pct: -0.708, reversion_tendency: high
    Volatility: 685.2312
    Volume_Profile: volume_bias: above_vwap, avg_volume_above: 18692.56, avg_volume_below: 17503.2, near_vwap_volume_pct: 48.5, above_vwap_volume_pct: 58.6, below_vwap_volume_pct: 41.4, institutional_activity: high
    Price Position: {'bias': 'bearish', 'current': 'below', 'above_vwap_pct': 57.0, 'below_vwap_pct': 43.0, 'position_changes': 93.0}
    Deviation Bands: {'lower_1std': 105323.3588, 'lower_2std': 104638.1275, 'upper_1std': 106693.8212, 'upper_2std': 107379.0525, 'current_position': 'below_1std', 'std_devs_from_vwap': -1.1}
    Patterns: volume_clustering
    Quality: data_quality: {'had_volumes': 1.0, 'aligned_periods': 200.0, 'volume_profile_available': 1.0, 'support_resistance_touches': 89.0}, calculation_notes: VWAP analysis based on 200 aligned price/VWAP periods

  aroon:
    Current: {'aroon_up': 21.43, 'timestamp': '2025-10-17T14:56:13.728057+00:00', 'aroon_down': 50.0, 'oscillator': -28.57}
    Summary: Aroon Up: 21.4, Down: 50.0 - sideways trend (bearish)
    Trend: separation: 28.57, current_trend: sideways, trend_quality: poor, trend_duration: 8.0, trend_strength: 0.286, trend_consistency: 0.8
    Strength: up_momentum: -7.14, up_evolution: falling, down_momentum: -7.14, down_evolution: falling, aroon_up_strength: weak, combined_strength: moderate, dominant_indicator: aroon_down, aroon_down_strength: moderate
    Parallel_Movement: correlation: 0.302, movement_type: moderate_positive_correlation, interpretation: Some coordination in indicator movement
    Crossovers: {'latest_crossover': {'type': 'bearish_crossover', 'location': 'high_levels', 'strength': 28.57142857142857, 'up_value': 71.43, 'down_value': 100.0, 'periods_ago': 8.0}, 'recent_crossovers': [{'type': 'bearish_crossover', 'location': 'high_levels', 'strength': 28.57142857142857, 'up_value': 71.43, 'down_value': 100.0, 'periods_ago': 8.0}], 'crossover_frequency': 'low'}
    Oscillator: {'zone': 'bearish', 'velocity': 0.0, 'acceleration': 0.0, 'current_value': -28.57, 'zero_crossings': 12.0, 'time_above_zero_pct': 61.3, 'time_below_zero_pct': 38.7, 'oscillator_interpretation': 'bearish_weakening'}
    Quality: clarity: 0.29, consistency: 0.80, data_quality: 0.93

  vortex:
    Current: {'spread': -0.4225, 'vi_plus': 0.7813, 'dominant': 'VI-', 'vi_minus': 1.2038, 'timestamp': '2025-10-17T14:56:13.732484+00:00'}
    Summary: Vortex VI+ 0.781, VI- 1.204 - VI minus dominant (+0.422), bearish crossover 4p ago
    Trend: strength: 0.327, velocity: -0.14721, direction: falling, acceleration: -0.103568
    Dominance: current: VI_minus, strength: 0.4225, persistence: 0.8
    Volatility: 0.293
    One Line: {'recent_crosses': {'plus_crosses': [{'type': 'downward_cross', 'value': 0.9603, 'periods_ago': 4.0}, {'type': 'upward_cross', 'value': 1.0077, 'periods_ago': 7.0}, {'type': 'downward_cross', 'value': 0.8918, 'periods_ago': 8.0}], 'minus_crosses': [{'type': 'upward_cross', 'value': 1.073, 'periods_ago': 3.0}]}, 'vi_plus_vs_one': 'below', 'vi_minus_vs_one': 'above', 'plus_above_one_pct': 68.8, 'minus_above_one_pct': 36.6}
    Vi Crossovers: [{'type': 'bearish_crossover', 'vi_plus': 0.9603, 'strength': 0.031, 'vi_minus': 0.9912, 'periods_ago': 4.0, 'crossover_level': 0.9757}]
    Key Level Crosses: [{'level': 1.0, 'strength': 0.03971881797986587, 'direction': 'down', 'periods_ago': 4.0}, {'level': 1.0, 'strength': 0.0077336160546379595, 'direction': 'up', 'periods_ago': 7.0}, {'level': 1.0, 'strength': 0.10815663987340263, 'direction': 'down', 'periods_ago': 8.0}]
    Patterns: directional_momentum
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'persistence': 5.0, 'crossover_scan': 14.0}, 'aligned_periods': 186.0}, calculation_notes: Vortex analysis based on 186 aligned VI+/VI- periods

  stochastic:
    Current: {'spread': -10.34, 'd_percent': 35.43, 'k_percent': 25.09, 'timestamp': '2025-10-17T14:56:13.656053+00:00'}
    Summary: Stochastic %K: 25.1, %D: 35.4. Bearish Crossover 3p ago
    Trend: momentum: strong_bearish_acceleration, velocity: -10.15, k_direction: falling, acceleration: -8.36
    Volatility: 26.607
    Spread_Momentum: -2.01
    Neutral: {'bias': 'bearish', 'level': 50.0, 'distance_from_50': -24.91}
    Oversold: {'level': 20.0, 'status': 'above', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'time_percentage': 8.2}
    Overbought: {'level': 80.0, 'status': 'below', 'exit_analysis': {'latest_exit': {'strength': 0.16589379938974885, 'exit_level': 76.68212401220502, 'periods_ago': 9.0}, 'recent_exits': [{'strength': 0.16589379938974885, 'exit_level': 76.68212401220502, 'periods_ago': 9.0}]}, 'streak_length': 0.0, 'time_percentage': 37.7}
    Patterns: momentum
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'aligned_periods': 183.0, 'valid_data_percentage': 97.9}, calculation_notes: Stochastic analysis based on 183 aligned K/D periods

  williams_r:
    Current: {'value': -86.54, 'timestamp': '2025-10-17T14:56:13.661098+00:00'}
    Summary: Williams %R at -86.5 (oversold for 1 periods), strong downward acceleration
    Trend: strength: 0.279, velocity: -11.376, direction: falling, acceleration: -20.718
    Momentum: volatility: 28.27, recent_range: 70.08, interpretation: strong_downward_acceleration
    Volatility: 28.271
    Neutral: {'bias': 'bearish', 'level': -50.0, 'distance_from_50': -36.54}
    Oversold: {'level': -80.0, 'status': 'in_zone', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 1.0, 'time_percentage': 12.3}
    Overbought: {'level': -20.0, 'status': 'below', 'exit_analysis': {'latest_exit': {'strength': 0.29048451724616875, 'exit_level': -25.81, 'periods_ago': 9.0}, 'recent_exits': [{'strength': 0.29048451724616875, 'exit_level': -25.81, 'periods_ago': 9.0}]}, 'streak_length': 0.0, 'time_percentage': 36.9}
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'acceleration': 4.0, 'position_rank': 14.0}, 'aligned_periods': 187.0}, calculation_notes: Williams %R analysis based on 187 periods with length=14

  bollinger_bands:
    Current: {'lower': 105320.9074, 'upper': 127629.2246, 'middle': 116475.066, 'bandwidth': 19.1529, 'percent_b': -0.0028}

=== 1H TIMEFRAME ===
  dc:
    Current: {'price': 105327.14, 'timestamp': '2025-10-17T14:55:47.985662+00:00', 'channel_width': 5711.77, 'lower_channel': 103528.23, 'upper_channel': 109240.0, 'middle_channel': 106384.115, 'price_position_pct': 31.5}
    Summary: Donchian: Price 105327.1400 (31.5%), Width 5711.7700
    Trend: strength: moderate_downward, position_pct: 31.5, utilization_rating: medium, channel_utilization: 0.674
    Length: 20.0
    Consolidation: price_range: 0.0, price_range_pct: 0.0, width_threshold: 3411.4917, is_consolidation: False, breakout_potential: low, consolidation_periods: 0.0
    Position: {'position': 'lower_third', 'position_pct': 31.5, 'distance_to_lower': 1798.91, 'distance_to_upper': 3912.86, 'distance_to_middle': 1056.975}
    Support Resistance: {'lower': {'breaks': 0.0, 'bounces': 0.0, 'touches': 0.0, 'bounce_rate': 0.0}, 'upper': {'breaks': 0.0, 'bounces': 2.0, 'touches': 2.0, 'bounce_rate': 1.0}, 'middle': {'breaks': 0.0, 'bounces': 1.0, 'touches': 1.0, 'bounce_rate': 1.0}}
    Patterns: breakouts, width_analysis, turtle_patterns
    Quality: data_quality: {'total_periods': 131.0, 'width_corrections': 0.0, 'valid_data_percentage': 87.3}, calculation_notes: Donchian analysis based on 131 aligned data points with period 20

  adx:
    Current: {'adx': 49.34, 'plus_di': 12.85, 'minus_di': 33.88, 'timestamp': '2025-10-17T14:55:47.780531+00:00'}
    Summary: ADX 49.3 - Very strong trend with bearish bias (21.0)
    Description: Very strong trend
    Strength_Value: 49.34
    Trend_Strength: very_strong
    Trend_Evolution: stable
    Directional_Bias: bearish
    Directional_Strength: 21.03
    Weak Threshold: 20.0
    Current Strength: very_strong
    Strong Threshold: 25.0
    Extreme Threshold: 60.0
    Very Strong Threshold: 40.0

  atr:
    Current: {'value': 1102.050556, 'timestamp': '2025-10-17T14:55:48.043113+00:00'}
    Summary: ATR 1102.050556 - extremely high volatility (99th percentile)
    Trend: strength: 0.103, velocity: 9.054221, direction: rising, consistency: 0.75, acceleration: -3.486615, interpretation: volatility_stable
    Breakout: breakout_setup: 0.0, squeeze_periods: 0.0, squeeze_detected: 0.0, expansion_potential: 0.0, recent_volatility_change_pct: 9.6
    Relative: regime: elevated_volatility, comparisons: {'5p_avg': 3.66, '10p_avg': 10.68, '20p_avg': 12.21, '50p_avg': 21.35}, regime_ratio: 1.214
    Cycles: {'recent_peaks': 5.0, 'cycle_detected': 1.0, 'cycle_position': 'post_peak_contraction', 'recent_troughs': 4.0, 'avg_expansion_cycle': 31.8, 'avg_contraction_cycle': 37.3}
    Stop Loss: {'stop_levels': {'1.0x_atr': {'distance': 1102.050556, 'long_stop': 104225.089444, 'short_stop': 106429.190556, 'distance_pct': 1.046}, '1.5x_atr': {'distance': 1653.075834, 'long_stop': 103674.064166, 'short_stop': 106980.215834, 'distance_pct': 1.569}, '2.0x_atr': {'distance': 2204.101112, 'long_stop': 103123.038888, 'short_stop': 107531.241112, 'distance_pct': 2.093}, '2.5x_atr': {'distance': 2755.12639, 'long_stop': 102572.01361, 'short_stop': 108082.26639, 'distance_pct': 2.616}, '3.0x_atr': {'distance': 3306.151668, 'long_stop': 102020.988332, 'short_stop': 108633.291668, 'distance_pct': 3.139}}, 'current_price': 105327.14, 'recommended_stop': {'distance': 2755.12639, 'long_stop': 102572.01361, 'short_stop': 108082.26639, 'distance_pct': 2.616}, 'recommended_multiplier': 2.5}
    Volatility: {'statistical': {'max': 1102.050556, 'min': 707.236012, 'std': 87.75771, 'mean': 872.570262}, 'current_level': 'extremely_high', 'percentile_rank': 99.3, 'relative_to_mean': 26.3, 'relative_to_price_pct': 1.046}
    Quality: clarity: 1.00, consistency: 0.10, data_quality: 0.68

  bbw:
    Current: {'width': 6.05, 'timestamp': '2025-10-17T14:55:48.088355+00:00'}
    Summary: BB Width 6.05% - high volatility (96th percentile)
    Trend: strength: 0.061, velocity: 0.092, direction: stable, acceleration: -0.273
    Breakout: potential: low, recent_change: 0.173, setup_quality: poor_setup, potential_score: 0.2, change_direction: expanding
    Expansion: cycle_stage: unclear, recent_peak: None, max_expansion: 6.05, recent_trough: None, cycle_position: unclear, expansion_peaks: 0.0, contraction_troughs: 0.0, avg_expansion_height: 6.05
    Cycles: {'total_cycles': 0.0, 'avg_cycle_length': None, 'expanding_time_pct': 41.2, 'contracting_time_pct': 58.8}
    Squeeze: {'is_squeeze': 0.0, 'squeeze_periods': 0.0, 'squeeze_quality': 'weak', 'squeeze_frequency': 0.679, 'squeeze_intensity': 0.0, 'squeeze_threshold': 4.18}
    Volatility: {'level': 'high', 'statistics': {'max': 6.47, 'min': 1.11, 'std': 1.52, 'mean': 3.32}, 'percentile_rank': 96.2, 'relative_to_mean': 82.4}
    Quality: clarity: 1.00, consistency: 0.06, data_quality: 0.66

  cci:
    Current: {'value': -84.58, 'timestamp': '2025-10-17T14:55:47.519552+00:00'}
    Summary: CCI at -84.6
    Length: 20.0
    Momentum: velocity: 6.76, volatility: 115.9, acceleration: 74.67, recent_range: 220.84, trend_strength: 0.338, trend_direction: rising, momentum_interpretation: rising_momentum
    Zero_Line: zero_crossings: 17.0, current_position: below, distance_from_zero: 84.58, time_above_zero_pct: 44.3, time_below_zero_pct: 55.7
    Oversold: {'level': -100.0, 'status': 'above', 'exit_analysis': {'latest_exit': {'strength': 4.546620489016107, 'exit_level': -95.4533795109839, 'periods_ago': 3.0}, 'recent_exits': [{'strength': 4.546620489016107, 'exit_level': -95.4533795109839, 'periods_ago': 3.0}]}, 'streak_length': 0.0, 'extreme_reading': False, 'time_percentage': 29.0}
    Overbought: {'level': 100.0, 'status': 'below', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'extreme_reading': False, 'time_percentage': 13.7}
    Zone: neutral
    Neutral Bias: bearish
    Patterns: hook, level_rejection
    Quality: data_quality: {'total_periods': 131.0, 'recent_volatility': 75.928, 'valid_data_percentage': 87.3}, calculation_notes: CCI analysis based on 131 valid data points with period 20

  ema:
    Current: {'price': 105327.14, 'ema_value': 106926.4298, 'timestamp': '2025-10-17T14:55:47.917751+00:00', 'price_distance': -1599.2898, 'price_distance_pct': -1.496}
    Summary: EMA 106926.4298 - falling trend (strength: 0.58), low responsiveness, price -1.5%
    Length: 20.0
    Responsiveness: avg_change: 98.813882, max_change: 355.785527, change_frequency: 0.177, direction_changes: 23.0, relative_volatility: 0.016905, responsiveness_score: 0.173, responsiveness_rating: low
    Signal_Quality: noise_level: low, signal_quality: low_frequency_high_reliability, recommended_use: Reliable for position trading, slower signals
    Trend: {'slope': -166.152766, 'strength': 0.584, 'consensus': 'falling', 'long_term': 'falling', 'short_term': 'falling', 'consistency': 1.0, 'medium_term': 'falling', 'acceleration': 205.210313}
    Price Relationship: {'distance': -1599.2898, 'position': 'below', 'avg_distance': -316.3408, 'distance_pct': -1.496, 'above_ema_pct': 41.2, 'below_ema_pct': 58.8, 'avg_distance_pct': -0.282}
    Support Resistance: {'success_rate': 0.611, 'effectiveness': 'high', 'total_touches': 36.0, 'recent_bounces': [{'type': 'resistance_bounce', 'index': 95.0, 'strength': 0.003264633949606134, 'periods_ago': 35.0}, {'type': 'support_bounce', 'index': 101.0, 'strength': 0.0029089584710460204, 'periods_ago': 29.0}, {'type': 'resistance_bounce', 'index': 104.0, 'strength': 0.005909930920335033, 'periods_ago': 26.0}], 'recent_touches': [{'index': 101.0, 'price': 111146.31, 'ema_value': 111216.41645936818, 'periods_ago': 29.0}, {'index': 102.0, 'price': 111469.63, 'ema_value': 111240.53203466644, 'periods_ago': 28.0}, {'index': 103.0, 'price': 111404.72, 'ema_value': 111256.16898374583, 'periods_ago': 27.0}, {'index': 104.0, 'price': 111519.07, 'ema_value': 111281.20717577003, 'periods_ago': 26.0}, {'index': 119.0, 'price': 109176.74, 'ema_value': 109296.31107271889, 'periods_ago': 11.0}], 'successful_bounces': 22.0}
    Patterns: crossovers
    Quality: data_quality: {'had_sma': 0.0, 'had_prices': 1.0, 'has_price_data': 1.0, 'aligned_periods': 131.0, 'has_sma_comparison': 0.0, 'original_ema_periods': 150.0, 'valid_data_percentage': 87.3}, calculation_notes: EMA analysis based on 131 aligned data points with period 20

  mfi:
    Current: {'value': 24.59, 'timestamp': '2025-10-17T14:55:47.575853+00:00'}
    Summary: MFI at 24.6, selling pressure
    Length: 14.0
    Position_Rank: percentile: 85.7, interpretation: high
    Zone: neutral
    Money Flow: {'pressure': 'selling', 'consistency': 0.5, 'flow_quality': 'low_quality_flow', 'cycle_analysis': {'cycle_detected': 0.0}, 'pressure_strength': 0.508, 'volume_confirmation': 'strong'}
    Patterns: momentum
    Quality: data_quality: {'had_prices': 1.0, 'original_periods': {'mfi': 150.0, 'prices': 150.0}, 'core_analysis_periods': 137.0, 'divergence_aligned_periods': 137.0}, calculation_notes: MFI analysis based on 137 core periods, divergence on 137 aligned periods

  obv:
    Current: {'value': -8073.47, 'timestamp': '2025-10-17T14:55:48.090359+00:00'}
    Summary: OBV -8073 - bullish trend (strong, 1.00), distribution detected
    Length: 14.0
    Relative: max_obv: 15834.08, min_obv: -14462.74, position: lower_range, position_percentile: 21.1
    Trend: {'strength': 1.0, 'velocity': 1277.86, 'consensus': 'bullish', 'long_term': 'bearish', 'short_term': 'bullish', 'consistency': 0.667, 'medium_term': 'bullish'}
    Accumulation: {'overall_phase': 'distribution_phase', 'phase_strength': 'strong', 'timeframe_analysis': {'5p': {'score': 'strong_accumulation', 'change_pct': 25.54}, '10p': {'score': 'strong_distribution', 'change_pct': -659.21}, '20p': {'score': 'strong_distribution', 'change_pct': -385.46}}}
    Patterns: flow, momentum
    Quality: data_quality: {'had_prices': 1.0, 'had_volumes': 1.0, 'cleaned_periods': 150.0, 'original_periods': {'obv': 150.0, 'prices': 150.0, 'volumes': 150.0}}, calculation_notes: OBV analysis based on 150 periods with length 14

  roc:
    Current: {'value': -3.181, 'timestamp': '2025-10-17T14:55:47.591730+00:00', 'value_pct': '-3.18%'}
    Summary: ROC -3.18% - strong negative momentum, oversold (6p)
    Trend: slope: -0.094, strength: 0.047, direction: sideways, consistency: 0.504
    Length: 10.0
    Momentum: strength: 3.180629790657468, direction: negative, evolution: decelerating, persistence: 1.0, strength_level: strong
    Velocity: velocity: -0.094, acceleration: 0.469, interpretation: stable_momentum
    Calculation_Periods: 140.0
    Extremes: {'condition': 'oversold', 'current_streak': 6.0, 'oversold_time_pct': 10.0, 'oversold_threshold': -2.83, 'overbought_time_pct': 8.6, 'overbought_threshold': 2.02, 'extreme_oversold_threshold': -6.47, 'extreme_overbought_threshold': 5.66}
    Zero Line: {'position': 'below_zero', 'above_zero_pct': 42.1, 'below_zero_pct': 57.9, 'recent_crosses': [{'type': 'bearish_zero_cross', 'value': -1.017, 'periods_ago': 9.0}], 'total_crossings': 22.0, 'crossing_frequency': 0.157}
    Quality: data_quality: {'had_prices': 1.0, 'clean_periods': 140.0, 'original_periods': 140.0, 'calculation_periods': 10.0, 'valid_data_percentage': 100.0}, calculation_notes: ROC analysis based on 140 periods with length=10

  rsi:
    Current: {'value': 34.49, 'timestamp': '2025-10-17T14:55:47.380931+00:00'}
    Summary: RSI at 34.5
    Ma5: 32.72
    Ma10: 30.83
    Trend: strength: 0.097, velocity: 0.11, direction: sideways, acceleration: 4.375
    Volatility: 12.945
    Neutral: {'level': 50.0, 'status': 'below', 'distance': -15.51}
    Oversold: {'level': 30.0, 'status': 'above', 'periods_in_zone': 0.0, 'time_percentage': 8.8}
    Overbought: {'level': 70.0, 'status': 'far_below', 'periods_in_zone': 0.0, 'time_percentage': 5.9}
    Quality: data_quality: {'total_periods': 136.0, 'recent_volatility': 5.874, 'valid_data_percentage': 90.7}, calculation_notes: RSI analysis based on 136 valid data points

  sma:
    Current: {'price': 105327.14, 'sma_value': 107108.5355, 'timestamp': '2025-10-17T14:55:47.936585+00:00', 'price_distance': -1781.3955, 'price_distance_pct': -1.663}
    Summary: SMA 107108.5355 - bearish trend (strong), price below (-1.7%)
    Slope: alignment: aligned, direction: downward, acceleration: 179.8305, long_term_slope: -222.611, short_term_slope: -160.869167, medium_term_slope: -182.9499
    Trend: slope: -182.9499, strength: 0.955, consensus: bearish, long_term: bearish, short_term: bearish, consistency: 1.0, medium_term: bearish
    Length: 20.0
    Quality: smoothness: 0.983, trend_clarity: 0.877, responsiveness: 0.091, overall_quality: 0.93
    Smoothing_Factor: 0.0952
    Current Level: 107108.5355
    Trend Direction: bearish
    Price Relationship: {'distance': -1781.3955, 'position': 'below', 'distance_pct': -1.663, 'above_sma_pct': 45.8, 'below_sma_pct': 54.2, 'position_changes': 15, 'position_stability': 0.885}
    Support Resistance: {'success_rate': 0.587, 'effectiveness': 'medium', 'total_touches': 46.0, 'recent_bounces': [{'type': 'resistance_bounce', 'index': 104.0, 'strength': 0.005909930920335033, 'periods_ago': 26.0}, {'type': 'resistance_bounce', 'index': 105.0, 'strength': 0.0029826808587407857, 'periods_ago': 25.0}, {'type': 'support_bounce', 'index': 118.0, 'strength': 0.0018699132454589801, 'periods_ago': 12.0}], 'recent_touches': [{'index': 104.0, 'price': 111519.07, 'sma_value': 111119.75349999999, 'periods_ago': 26.0}, {'index': 105.0, 'price': 110860.0, 'sma_value': 111103.41449999998, 'periods_ago': 25.0}, {'index': 106.0, 'price': 110529.34, 'sma_value': 111057.6435, 'periods_ago': 24.0}, {'index': 118.0, 'price': 108972.97, 'sma_value': 109506.5305, 'periods_ago': 12.0}, {'index': 119.0, 'price': 109176.74, 'sma_value': 109436.1575, 'periods_ago': 11.0}], 'successful_bounces': 27.0}
    Patterns: crossovers, slope_direction, trend_alignment
    Quality: data_quality: {'had_prices': 1.0, 'aligned_periods': 131.0, 'original_periods': 131.0, 'calculation_periods': 20.0, 'valid_data_percentage': 100.0}, calculation_notes: SMA analysis based on 131 periods with length=20

  macd:
    Current: {'macd': -1258.2764, 'signal': -1164.8473, 'histogram': -93.4291, 'timestamp': '2025-10-17T14:55:47.419313+00:00'}
    Summary: MACD falling trend with decreasing momentum
    Histogram: {'acceleration': 39.7441, 'histogram_strength': 93.42910361153145, 'momentum_direction': 'increasing', 'zero_crossings_recent': 1.0}
    Zero Line: {'current_position': 'below', 'distance_from_zero': 1258.2764, 'time_above_zero_pct': 29.1, 'time_below_zero_pct': 70.9}
    Patterns: crossovers
    Quality: data_quality: {'aligned_periods': 117.0, 'original_periods': {'macd': 150.0, 'prices': 150.0, 'signal': 150.0, 'histogram': 150.0}, 'valid_data_percentage': 78.0}, calculation_notes: MACD analysis based on 117 aligned data points
    Legacy Trend: bearish

  psar:
    Current: {'price': 105327.14, 'distance': -1770.5089, 'timestamp': '2025-10-17T14:55:47.872932+00:00', 'psar_value': 107097.6489, 'distance_percentage': -1.681}
    Summary: PSAR 107097.6489 - bearish trend for 9 periods, 1.68% from price
    Trend: trend_periods: 9.0, trend_strength: 0.92, current_direction: bearish, trend_consistency: 0.9, strength_interpretation: very_strong
    Length: 14.0
    Distance: max_distance: 7581.43, min_distance: -4235.0514, average_distance: 91.6856, current_absolute: -1770.5089, distance_volatility: 2320.2116, current_relative_pct: -1.681, distance_interpretation: normal_distance
    Acceleration: velocity: -338.1565, acceleration: -115.03713, rate_of_change_5p: -1.302, acceleration_interpretation: accelerating_downward
    Calculation_Periods: 149.0
    Trend Direction: unknown
    Stop Distance Pct: 1.681
    Current Stop Level: 107097.6489
    Patterns: clustering, signal_analysis
    Quality: stop_loss: {'stop_type': 'trailing_stop', 'performance': {'total_tests': 122.0, 'successful_stops': 89.0, 'effectiveness_rate': 0.73}, 'stop_distance': 1770.5089, 'recommendation': 'reasonable_stop', 'stop_distance_pct': 1.681, 'current_stop_level': 107097.6489}, data_quality: {'aligned_periods': 149.0, 'had_high_low_data': 1.0, 'calculation_periods': 14.0}, calculation_notes: Parabolic SAR analysis based on 149 aligned periods

  trix:
    Current: {'trix': -0.16235, 'signal': 105327.14, 'histogram': -105327.30235, 'timestamp': '2025-10-17T14:55:47.725974+00:00'}
    Summary: TRIX -0.162350 - very_strong bearish momentum, histogram -105327.302350 (below zero)
    Trend: strength: 0.099, velocity: -0.0045, direction: sideways, acceleration: 0.007902
    Momentum: direction: bearish, persistence: 1.0, strength_level: very_strong
    Volatility: 0.070113
    Zero Line: {'position': 'below_zero', 'above_zero_pct': 28.7, 'below_zero_pct': 70.6, 'recent_crossings': []}
    Signal Line: {'latest_crossover': None, 'recent_crossovers': [], 'crossover_frequency': 0.0}
    Quality: data_quality: {'had_prices': 0.0, 'had_signal': 1.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'acceleration': 4.0, 'turning_points': 14.0}, 'aligned_periods': 136.0}, calculation_notes: TRIX analysis based on 136 aligned periods with length=14

  vwap:
    Current: {'price': 105327.14, 'timestamp': '2025-10-17T14:55:48.125389+00:00', 'vwap_value': 105917.5889, 'price_distance': -590.4489, 'price_distance_pct': -0.557}
    Summary: VWAP 105917.5889, price below (-0.6%) - slightly undervalued
    Trend: strength: 0.067, velocity: -35.547422, direction: sideways, smoothness: 0.981
    Anchored: momentum: -35.547422, reset_detected: False, behavior_quality: choppy, direction_consistency: 0.557
    Fair_Value: assessment: slightly_undervalued, distance_pct: -0.557, reversion_tendency: low
    Volatility: 959.7567
    Volume_Profile: volume_bias: below_vwap, avg_volume_above: 1096.0, avg_volume_below: 1328.89, near_vwap_volume_pct: 40.0, above_vwap_volume_pct: 38.7, below_vwap_volume_pct: 61.3, institutional_activity: high
    Price Position: {'bias': 'bearish', 'current': 'below', 'above_vwap_pct': 43.3, 'below_vwap_pct': 56.7, 'position_changes': 25.0}
    Deviation Bands: {'lower_1std': 104957.8321, 'lower_2std': 103998.0754, 'upper_1std': 106877.3456, 'upper_2std': 107837.1023, 'current_position': 'within_1std', 'std_devs_from_vwap': -0.62}
    Patterns: volume_clustering
    Quality: data_quality: {'had_volumes': 1.0, 'aligned_periods': 150.0, 'volume_profile_available': 1.0, 'support_resistance_touches': 47.0}, calculation_notes: VWAP analysis based on 150 aligned price/VWAP periods

  aroon:
    Current: {'aroon_up': 21.43, 'timestamp': '2025-10-17T14:55:47.659306+00:00', 'aroon_down': 71.43, 'oscillator': -50.0}
    Summary: Aroon Up: 21.4, Down: 71.4 - strong_downtrend for 24 periods (strong bearish)
    Trend: separation: 50.0, current_trend: strong_downtrend, trend_quality: fair, trend_duration: 24.0, trend_strength: 0.5, trend_consistency: 1.0
    Strength: up_momentum: -7.14, up_evolution: falling, down_momentum: -7.14, down_evolution: falling, aroon_up_strength: weak, combined_strength: strong, dominant_indicator: aroon_down, aroon_down_strength: strong
    Parallel_Movement: correlation: 0.32, movement_type: moderate_positive_correlation, interpretation: Some coordination in indicator movement
    Crossovers: {'latest_crossover': None, 'recent_crossovers': [], 'crossover_frequency': 'low'}
    Oscillator: {'zone': 'strong_bearish', 'velocity': 0.0, 'acceleration': -32.14, 'current_value': -50.0, 'zero_crossings': 10.0, 'time_above_zero_pct': 39.0, 'time_below_zero_pct': 61.0, 'oscillator_interpretation': 'strong_bearish_slowing'}
    Quality: clarity: 0.50, consistency: 1.00, data_quality: 0.68

  vortex:
    Current: {'spread': -0.4112, 'vi_plus': 0.7766, 'dominant': 'VI-', 'vi_minus': 1.1878, 'timestamp': '2025-10-17T14:55:47.677224+00:00'}
    Summary: Vortex VI+ 0.777, VI- 1.188 - VI minus dominant (+0.411)
    Trend: strength: 0.04, velocity: -0.028539, direction: sideways, acceleration: -0.111676
    Dominance: current: VI_minus, strength: 0.4112, persistence: 1.0
    Volatility: 0.3167
    One Line: {'recent_crosses': {'plus_crosses': [], 'minus_crosses': []}, 'vi_plus_vs_one': 'below', 'vi_minus_vs_one': 'above', 'plus_above_one_pct': 41.2, 'minus_above_one_pct': 61.8}
    Vi Crossovers: []
    Key Level Crosses: []
    Patterns: parallel_movement
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'persistence': 5.0, 'crossover_scan': 14.0}, 'aligned_periods': 136.0}, calculation_notes: Vortex analysis based on 136 aligned VI+/VI- periods

  stochastic:
    Current: {'spread': 0.72, 'd_percent': 33.88, 'k_percent': 34.6, 'timestamp': '2025-10-17T14:55:47.444845+00:00'}
    Summary: Stochastic %K: 34.6, %D: 33.9. Bullish Crossover 5p ago
    Trend: momentum: bullish_momentum, velocity: 2.12, k_direction: rising, acceleration: -0.48
    Volatility: 27.476
    Spread_Momentum: -6.98
    Neutral: {'bias': 'bearish', 'level': 50.0, 'distance_from_50': -15.4}
    Oversold: {'level': 20.0, 'status': 'above', 'exit_analysis': {'latest_exit': {'strength': 0.5177490223404208, 'exit_level': 30.354980446808415, 'periods_ago': 3.0}, 'recent_exits': [{'strength': 0.5177490223404208, 'exit_level': 30.354980446808415, 'periods_ago': 3.0}]}, 'streak_length': 0.0, 'time_percentage': 23.3}
    Overbought: {'level': 80.0, 'status': 'below', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'time_percentage': 19.5}
    Patterns: squeeze, momentum
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'aligned_periods': 133.0, 'valid_data_percentage': 97.1}, calculation_notes: Stochastic analysis based on 133 aligned K/D periods

  williams_r:
    Current: {'value': -68.51, 'timestamp': '2025-10-17T14:55:47.468067+00:00'}
    Summary: Williams %R at -68.5
    Trend: strength: 0.066, velocity: -0.204, direction: sideways, acceleration: -6.91
    Momentum: volatility: 29.45, recent_range: 51.7, interpretation: sideways_momentum
    Volatility: 29.451
    Neutral: {'bias': 'bearish', 'level': -50.0, 'distance_from_50': -18.51}
    Oversold: {'level': -80.0, 'status': 'above', 'exit_analysis': {'latest_exit': {'strength': 0.07126162292950226, 'exit_level': -78.57, 'periods_ago': 5.0}, 'recent_exits': [{'strength': 0.07126162292950226, 'exit_level': -78.57, 'periods_ago': 5.0}]}, 'streak_length': 0.0, 'time_percentage': 23.4}
    Overbought: {'level': -20.0, 'status': 'below', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'time_percentage': 21.2}
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'acceleration': 4.0, 'position_rank': 14.0}, 'aligned_periods': 137.0}, calculation_notes: Williams %R analysis based on 137 periods with length=14

  bollinger_bands:
    Current: {'lower': 103865.8711, 'upper': 110351.1999, 'middle': 107108.5355, 'bandwidth': 6.0549, 'percent_b': 0.2253}

=== 1W TIMEFRAME ===
  dc:
    Current: {'price': 105262.93, 'timestamp': '2025-10-17T14:56:09.075982+00:00', 'channel_width': 27999.63, 'lower_channel': 98200.0, 'upper_channel': 126199.63, 'middle_channel': 112199.815, 'price_position_pct': 25.2}
    Summary: Donchian: Price 105262.9300 (25.2%), Width 27999.6300 - CONSOLIDATION (6p)
    Trend: strength: moderate_downward, position_pct: 25.2, utilization_rating: medium, channel_utilization: 0.651
    Length: 20.0
    Consolidation: price_range: 18219.38, price_range_pct: 15.93, width_threshold: 36482.023, is_consolidation: True, breakout_potential: medium, consolidation_periods: 6.0
    Position: {'position': 'lower_third', 'position_pct': 25.2, 'distance_to_lower': 7062.93, 'distance_to_upper': 20936.7, 'distance_to_middle': 6936.885}
    Support Resistance: {'lower': {'breaks': 0.0, 'bounces': 0.0, 'touches': 1.0, 'bounce_rate': 0.0}, 'upper': {'breaks': 0.0, 'bounces': 0.0, 'touches': 0.0, 'bounce_rate': 0.0}, 'middle': {'breaks': 0.0, 'bounces': 0.0, 'touches': 0.0, 'bounce_rate': 0.0}}
    Patterns: breakouts, width_analysis, turtle_patterns
    Quality: data_quality: {'total_periods': 181.0, 'width_corrections': 0.0, 'valid_data_percentage': 90.5}, calculation_notes: Donchian analysis based on 181 aligned data points with period 20

  adx:
    Current: {'adx': 20.81, 'plus_di': 21.57, 'minus_di': 20.01, 'timestamp': '2025-10-17T14:56:09.013821+00:00'}
    Summary: ADX 20.8 - Developing trend with bullish bias (1.6)
    Description: Developing trend
    Strength_Value: 20.81
    Trend_Strength: developing
    Trend_Evolution: stable
    Directional_Bias: bullish
    Directional_Strength: 1.56
    Weak Threshold: 20.0
    Current Strength: developing
    Strong Threshold: 25.0
    Extreme Threshold: 60.0
    Very Strong Threshold: 40.0
    Patterns: di_patterns

  atr:
    Current: {'value': 9335.66886, 'timestamp': '2025-10-17T14:56:09.108869+00:00'}
    Summary: ATR 9335.668860 - high volatility (92th percentile)
    Trend: strength: 0.241, velocity: 626.015875, direction: rising, consistency: 0.75, acceleration: 838.707045, interpretation: volatility_stable
    Breakout: breakout_setup: 0.0, squeeze_periods: 0.0, squeeze_detected: 0.0, expansion_potential: 0.0, recent_volatility_change_pct: 24.29
    Relative: regime: normal_volatility, comparisons: {'5p_avg': 12.92, '10p_avg': 14.16, '20p_avg': 10.43, '50p_avg': 6.02}, regime_ratio: 1.06
    Cycles: {'cycle_detected': 0.0}
    Stop Loss: {'stop_levels': {'1.0x_atr': {'distance': 9335.66886, 'long_stop': 95927.26114, 'short_stop': 114598.59886, 'distance_pct': 8.869}, '1.5x_atr': {'distance': 14003.503289, 'long_stop': 91259.426711, 'short_stop': 119266.433289, 'distance_pct': 13.303}, '2.0x_atr': {'distance': 18671.337719, 'long_stop': 86591.592281, 'short_stop': 123934.267719, 'distance_pct': 17.738}, '2.5x_atr': {'distance': 23339.172149, 'long_stop': 81923.757851, 'short_stop': 128602.102149, 'distance_pct': 22.172}, '3.0x_atr': {'distance': 28007.006579, 'long_stop': 77255.923421, 'short_stop': 133269.936579, 'distance_pct': 26.607}}, 'current_price': 105262.93, 'recommended_stop': {'distance': 23339.172149, 'long_stop': 81923.757851, 'short_stop': 128602.102149, 'distance_pct': 22.172}, 'recommended_multiplier': 2.5}
    Volatility: {'statistical': {'max': 10090.344367, 'min': 2050.040935, 'std': 2599.220987, 'mean': 5256.661495}, 'current_level': 'high', 'percentile_rank': 91.9, 'relative_to_mean': 77.6, 'relative_to_price_pct': 8.869}
    Quality: clarity: 1.00, consistency: 0.24, data_quality: 0.93

  bbw:
    Current: {'width': 20.3, 'timestamp': '2025-10-17T14:56:09.127615+00:00'}
    Summary: BB Width 20.30% - low volatility (3th percentile)
    Trend: strength: 0.019, velocity: 0.451, direction: stable, acceleration: 4.733
    Breakout: potential: high, recent_change: -0.089, setup_quality: good_setup, potential_score: 0.8, change_direction: contracting
    Expansion: cycle_stage: unclear, recent_peak: None, max_expansion: 20.3, recent_trough: None, cycle_position: unclear, expansion_peaks: 0.0, contraction_troughs: 0.0, avg_expansion_height: 20.3
    Cycles: {'total_cycles': 0.0, 'avg_cycle_length': None, 'expanding_time_pct': 41.4, 'contracting_time_pct': 58.6}
    Squeeze: {'is_squeeze': 0.0, 'squeeze_periods': 0.0, 'squeeze_quality': 'weak', 'squeeze_frequency': 0.006, 'squeeze_intensity': 0.0, 'squeeze_threshold': 18.95}
    Volatility: {'level': 'low', 'statistics': {'max': 117.33, 'min': 18.95, 'std': 24.28, 'mean': 52.19}, 'percentile_rank': 3.3, 'relative_to_mean': -61.11}
    Quality: clarity: 1.00, consistency: 0.02, data_quality: 0.91

  cci:
    Current: {'value': -63.26, 'timestamp': '2025-10-17T14:56:08.941060+00:00'}
    Summary: CCI at -63.3, strong falling acceleration
    Length: 20.0
    Momentum: velocity: -24.59, volatility: 112.54, acceleration: -67.37, recent_range: 178.01, trend_strength: 1.0, trend_direction: falling, momentum_interpretation: strong_falling_acceleration
    Zero_Line: zero_crossings: 16.0, current_position: below, distance_from_zero: 63.26, time_above_zero_pct: 63.0, time_below_zero_pct: 37.0
    Oversold: {'level': -100.0, 'status': 'above', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'extreme_reading': False, 'time_percentage': 16.0}
    Overbought: {'level': 100.0, 'status': 'below', 'exit_analysis': {'latest_exit': {'strength': 71.66632020923271, 'exit_level': 28.3336797907673, 'periods_ago': 2.0}, 'recent_exits': [{'strength': 71.66632020923271, 'exit_level': 28.3336797907673, 'periods_ago': 2.0}, {'strength': 34.799814280288686, 'exit_level': 65.20018571971131, 'periods_ago': 9.0}]}, 'streak_length': 0.0, 'extreme_reading': False, 'time_percentage': 30.9}
    Zone: neutral
    Neutral Bias: bearish
    Patterns: hook
    Quality: data_quality: {'total_periods': 181.0, 'recent_volatility': 51.972, 'valid_data_percentage': 90.5}, calculation_notes: CCI analysis based on 181 valid data points with period 20

  ema:
    Current: {'price': 105262.93, 'ema_value': 110878.248, 'timestamp': '2025-10-17T14:56:09.057601+00:00', 'price_distance': -5615.318, 'price_distance_pct': -5.064}
    Summary: EMA 110878.2480 - rising trend, very_high responsiveness, price -5.1%
    Length: 20.0
    Responsiveness: avg_change: 724.48508, max_change: 2907.532161, change_frequency: 0.078, direction_changes: 14.0, relative_volatility: 0.560877, responsiveness_score: 1.0, responsiveness_rating: very_high
    Signal_Quality: noise_level: low, signal_quality: high_frequency_low_reliability, recommended_use: Use with confirmation indicators, good for scalping
    Trend: {'slope': 359.804775, 'strength': 0.083, 'consensus': 'rising', 'long_term': 'rising', 'short_term': 'falling', 'consistency': 0.857, 'medium_term': 'rising', 'acceleration': -594.348642}
    Price Relationship: {'distance': -5615.318, 'position': 'below', 'avg_distance': 3622.9913, 'distance_pct': -5.064, 'above_ema_pct': 67.4, 'below_ema_pct': 32.6, 'avg_distance_pct': 6.996}
    Support Resistance: {'success_rate': 0.0, 'effectiveness': 'low', 'total_touches': 2.0, 'recent_bounces': [], 'recent_touches': [{'index': 57.0, 'price': 25925.55, 'ema_value': 25917.81931251646, 'periods_ago': 123.0}, {'index': 173.0, 'price': 108246.35, 'ema_value': 107986.80159696596, 'periods_ago': 7.0}], 'successful_bounces': 0.0}
    Patterns: crossovers
    Quality: data_quality: {'had_sma': 0.0, 'had_prices': 1.0, 'has_price_data': 1.0, 'aligned_periods': 181.0, 'has_sma_comparison': 0.0, 'original_ema_periods': 200.0, 'valid_data_percentage': 90.5}, calculation_notes: EMA analysis based on 181 aligned data points with period 20

  mfi:
    Current: {'value': 44.76, 'timestamp': '2025-10-17T14:56:08.952022+00:00'}
    Summary: MFI at 44.8 (neutral, falling money flow), selling pressure
    Length: 14.0
    Position_Rank: percentile: 0.0, interpretation: extremely_low
    Zone: neutral
    Money Flow: {'pressure': 'selling', 'consistency': 0.5, 'flow_quality': 'low_quality_flow', 'cycle_analysis': {'cycle_detected': 0.0}, 'pressure_strength': 0.105, 'volume_confirmation': 'weak'}
    Patterns: momentum
    Quality: data_quality: {'had_prices': 1.0, 'original_periods': {'mfi': 200.0, 'prices': 200.0}, 'core_analysis_periods': 187.0, 'divergence_aligned_periods': 187.0}, calculation_notes: MFI analysis based on 187 core periods, divergence on 187 aligned periods

  obv:
    Current: {'value': 2632410.63, 'timestamp': '2025-10-17T14:56:09.131521+00:00'}
    Summary: OBV 2632411 - bearish trend, distribution detected
    Length: 14.0
    Relative: max_obv: 5653194.89, min_obv: -5568180.81, position: upper_range, position_percentile: 73.1
    Trend: {'strength': 0.38, 'velocity': -77791.55, 'consensus': 'bearish', 'long_term': 'bearish', 'short_term': 'bearish', 'consistency': 0.667, 'medium_term': 'bearish'}
    Accumulation: {'overall_phase': 'distribution_phase', 'phase_strength': 'strong', 'timeframe_analysis': {'5p': {'score': 'strong_distribution', 'change_pct': -10.79}, '10p': {'score': 'strong_distribution', 'change_pct': -14.28}, '20p': {'score': 'strong_distribution', 'change_pct': -17.15}}}
    Patterns: flow, momentum
    Quality: data_quality: {'had_prices': 1.0, 'had_volumes': 1.0, 'cleaned_periods': 200.0, 'original_periods': {'obv': 200.0, 'prices': 200.0, 'volumes': 200.0}}, calculation_notes: OBV analysis based on 200 periods with length 14

  roc:
    Current: {'value': -11.762, 'timestamp': '2025-10-17T14:56:08.964307+00:00', 'value_pct': '-11.76%'}
    Summary: ROC -11.76% - very_strong negative momentum
    Trend: slope: -2.471, strength: 1.0, direction: falling, consistency: 0.534
    Length: 10.0
    Momentum: strength: 11.761764065102685, direction: negative, evolution: decelerating, persistence: 0.6, strength_level: very_strong
    Velocity: velocity: -2.471, acceleration: -6.754, interpretation: decelerating_momentum
    Calculation_Periods: 190.0
    Extremes: {'condition': 'neutral', 'current_streak': 0.0, 'oversold_time_pct': 3.7, 'oversold_threshold': -30.04, 'overbought_time_pct': 8.9, 'overbought_threshold': 47.01, 'extreme_oversold_threshold': -87.83, 'extreme_overbought_threshold': 104.8}
    Zero Line: {'position': 'below_zero', 'above_zero_pct': 55.8, 'below_zero_pct': 44.2, 'recent_crosses': [{'type': 'bearish_zero_cross', 'value': -11.762, 'periods_ago': 1.0}, {'type': 'bullish_zero_cross', 'value': 3.406, 'periods_ago': 3.0}, {'type': 'bearish_zero_cross', 'value': -3.237, 'periods_ago': 5.0}], 'total_crossings': 26.0, 'crossing_frequency': 0.137}
    Quality: data_quality: {'had_prices': 1.0, 'clean_periods': 190.0, 'original_periods': 190.0, 'calculation_periods': 10.0, 'valid_data_percentage': 100.0}, calculation_notes: ROC analysis based on 190 periods with length=10

  rsi:
    Current: {'value': 47.45, 'timestamp': '2025-10-17T14:56:08.915229+00:00'}
    Summary: RSI at 47.5, falling
    Ma5: 56.38
    Ma10: 57.3
    Trend: strength: 0.104, velocity: -2.697, direction: falling, acceleration: -6.846
    Volatility: 15.715
    Neutral: {'level': 50.0, 'status': 'below', 'distance': -2.55}
    Oversold: {'level': 30.0, 'status': 'far_above', 'periods_in_zone': 0.0, 'time_percentage': 8.1}
    Overbought: {'level': 70.0, 'status': 'far_below', 'periods_in_zone': 0.0, 'time_percentage': 15.6}
    Quality: data_quality: {'total_periods': 186.0, 'recent_volatility': 4.946, 'valid_data_percentage': 93.0}, calculation_notes: RSI analysis based on 186 valid data points

  sma:
    Current: {'price': 105262.93, 'sma_value': 112788.6675, 'timestamp': '2025-10-17T14:56:09.064358+00:00', 'price_distance': -7525.7375, 'price_distance_pct': -6.672}
    Summary: SMA 112788.6675 - bullish trend, price below (-6.7%)
    Slope: alignment: aligned, direction: upward, acceleration: -1047.555, long_term_slope: 968.22525, short_term_slope: 376.711, medium_term_slope: 516.0328
    Trend: slope: 516.0328, strength: 0.176, consensus: bullish, long_term: bullish, short_term: bullish, consistency: 0.889, medium_term: bullish
    Length: 20.0
    Quality: smoothness: 0.433, trend_clarity: 0.906, responsiveness: 1.0, overall_quality: 0.669
    Smoothing_Factor: 0.0952
    Current Level: 112788.6675
    Trend Direction: bullish
    Price Relationship: {'distance': -7525.7375, 'position': 'below', 'distance_pct': -6.672, 'above_sma_pct': 65.7, 'below_sma_pct': 34.3, 'position_changes': 18, 'position_stability': 0.9}
    Support Resistance: {'success_rate': 0.333, 'effectiveness': 'medium', 'total_touches': 6.0, 'recent_bounces': [{'type': 'support_bounce', 'index': 58.0, 'strength': 0.15651840150159618, 'periods_ago': 122.0}, {'type': 'resistance_bounce', 'index': 74.0, 'strength': 0.027327385952312218, 'periods_ago': 106.0}], 'recent_touches': [{'index': 73.0, 'price': 27992.57, 'sma_value': 27914.802000000003, 'periods_ago': 107.0}, {'index': 74.0, 'price': 27917.05, 'sma_value': 27973.2655, 'periods_ago': 106.0}, {'index': 126.0, 'price': 62819.91, 'sma_value': 62723.835, 'periods_ago': 54.0}, {'index': 173.0, 'price': 108246.35, 'sma_value': 107834.66299999999, 'periods_ago': 7.0}, {'index': 177.0, 'price': 112163.95, 'sma_value': 111658.5345, 'periods_ago': 3.0}], 'successful_bounces': 2.0}
    Patterns: crossovers, slope_direction, trend_alignment
    Quality: data_quality: {'had_prices': 1.0, 'aligned_periods': 181.0, 'original_periods': 181.0, 'calculation_periods': 20.0, 'valid_data_percentage': 100.0}, calculation_notes: SMA analysis based on 181 periods with length=20

  macd:
    Current: {'macd': 4148.902, 'signal': 5515.5763, 'histogram': -1366.6743, 'timestamp': '2025-10-17T14:56:08.923020+00:00'}
    Summary: MACD falling trend with decreasing momentum
    Histogram: {'acceleration': -773.4783, 'histogram_strength': 1366.6742730181104, 'momentum_direction': 'decreasing', 'zero_crossings_recent': 1.0}
    Zero Line: {'current_position': 'above', 'distance_from_zero': 4148.902, 'time_above_zero_pct': 81.4, 'time_below_zero_pct': 18.6}
    Patterns: crossovers
    Quality: data_quality: {'aligned_periods': 167.0, 'original_periods': {'macd': 200.0, 'prices': 200.0, 'signal': 200.0, 'histogram': 200.0}, 'valid_data_percentage': 83.5}, calculation_notes: MACD analysis based on 167 aligned data points
    Legacy Trend: bearish

  psar:
    Current: {'price': 105262.93, 'distance': -20936.7, 'timestamp': '2025-10-17T14:56:09.042918+00:00', 'psar_value': 126199.63, 'distance_percentage': -19.89}
    Summary: PSAR 126199.6300 - bearish trend for 2 periods, 19.89% from price. Recent reversal 2p ago
    Trend: trend_periods: 2.0, trend_strength: 1.0, current_direction: bearish, trend_consistency: 0.6, strength_interpretation: very_strong
    Length: 14.0
    Distance: max_distance: 39966.6659, min_distance: -28227.0404, average_distance: 1600.8356, current_absolute: -20936.7, distance_volatility: 13615.4263, current_relative_pct: -19.89, distance_interpretation: normal_distance
    Acceleration: velocity: 912.748317, acceleration: 1060.149131, rate_of_change_5p: 1.945, acceleration_interpretation: accelerating_upward
    Calculation_Periods: 199.0
    Trend Direction: unknown
    Stop Distance Pct: 19.89
    Current Stop Level: 126199.63
    Patterns: signal_analysis
    Quality: stop_loss: {'stop_type': 'trailing_stop', 'performance': {'total_tests': 13.0, 'successful_stops': 1.0, 'effectiveness_rate': 0.077}, 'stop_distance': 20936.7, 'recommendation': 'very_wide_stop', 'stop_distance_pct': 19.89, 'current_stop_level': 126199.63}, data_quality: {'aligned_periods': 199.0, 'had_high_low_data': 1.0, 'calculation_periods': 14.0}, calculation_notes: Parabolic SAR analysis based on 199 aligned periods

  trix:
    Current: {'trix': 0.7689, 'signal': 105262.93, 'histogram': -105262.1611, 'timestamp': '2025-10-17T14:56:09.003180+00:00'}
    Summary: TRIX 0.768900 - moderate bullish momentum, histogram -105262.161100 (above zero)
    Trend: strength: 0.022, velocity: -0.045249, direction: sideways, acceleration: -0.006507
    Momentum: direction: bullish, persistence: 1.0, strength_level: moderate
    Volatility: 1.36404
    Zero Line: {'position': 'above_zero', 'above_zero_pct': 74.7, 'below_zero_pct': 24.7, 'recent_crossings': []}
    Signal Line: {'latest_crossover': None, 'recent_crossovers': [], 'crossover_frequency': 0.0}
    Quality: data_quality: {'had_prices': 0.0, 'had_signal': 1.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'acceleration': 4.0, 'turning_points': 14.0}, 'aligned_periods': 186.0}, calculation_notes: TRIX analysis based on 186 aligned periods with length=14

  vwap:
    Current: {'price': 105262.93, 'timestamp': '2025-10-17T14:56:09.148942+00:00', 'vwap_value': 108251.6567, 'price_distance': -2988.7267, 'price_distance_pct': -2.761}
    Summary: VWAP 108251.6567, price below (-2.8%) - undervalued
    Trend: strength: 0.024, velocity: -5999.401667, direction: sideways, smoothness: 0.414
    Anchored: momentum: -5999.401667, reset_detected: False, behavior_quality: choppy, direction_consistency: 0.533
    Fair_Value: assessment: undervalued, distance_pct: -2.761, reversion_tendency: high
    Volatility: 1414.0688
    Volume_Profile: volume_bias: above_vwap, avg_volume_above: 566455.18, avg_volume_below: 524700.71, near_vwap_volume_pct: 13.0, above_vwap_volume_pct: 56.9, below_vwap_volume_pct: 43.1, institutional_activity: medium
    Price Position: {'bias': 'bearish', 'current': 'below', 'above_vwap_pct': 55.0, 'below_vwap_pct': 45.0, 'position_changes': 99.0}
    Deviation Bands: {'lower_1std': 106837.5879, 'lower_2std': 105423.5191, 'upper_1std': 109665.7255, 'upper_2std': 111079.7943, 'current_position': 'below_2std', 'std_devs_from_vwap': -2.11}
    Patterns: extreme_deviation, convergence_divergence
    Quality: data_quality: {'had_volumes': 1.0, 'aligned_periods': 200.0, 'volume_profile_available': 1.0, 'support_resistance_touches': 20.0}, calculation_notes: VWAP analysis based on 200 aligned price/VWAP periods

  aroon:
    Current: {'aroon_up': 92.86, 'timestamp': '2025-10-17T14:56:08.986421+00:00', 'aroon_down': 92.86, 'oscillator': 0.0}
    Summary: Aroon Up: 92.9, Down: 92.9 - sideways trend
    Trend: separation: 0.0, current_trend: sideways, trend_quality: poor, trend_duration: 2.0, trend_strength: 0.0, trend_consistency: 0.2
    Strength: up_momentum: 11.9, up_evolution: rising, down_momentum: 30.95, down_evolution: rising, aroon_up_strength: very_strong, combined_strength: very_strong, dominant_indicator: aroon_down, aroon_down_strength: very_strong
    Parallel_Movement: correlation: 0.042, movement_type: independent_movement, interpretation: Indicators moving independently
    Crossovers: {'latest_crossover': None, 'recent_crossovers': [], 'crossover_frequency': 'low'}
    Oscillator: {'zone': 'neutral', 'velocity': -19.05, 'acceleration': -50.0, 'current_value': 0.0, 'zero_crossings': 10.0, 'time_above_zero_pct': 59.7, 'time_below_zero_pct': 38.7, 'oscillator_interpretation': 'bearish_strengthening'}
    Patterns: extreme_readings
    Quality: clarity: 0.00, consistency: 0.20, data_quality: 0.93

  vortex:
    Current: {'spread': -0.0611, 'vi_plus': 0.9679, 'dominant': 'VI-', 'vi_minus': 1.029, 'timestamp': '2025-10-17T14:56:08.990626+00:00'}
    Summary: Vortex VI+ 0.968, VI- 1.029 - VI minus dominant (+0.061), bearish crossover 1p ago
    Trend: strength: 0.114, velocity: -0.172635, direction: falling, acceleration: -0.163978
    Dominance: current: VI_minus, strength: 0.0611, persistence: 0.2
    Volatility: 0.3594
    One Line: {'recent_crosses': {'plus_crosses': [{'type': 'downward_cross', 'value': 0.9744, 'periods_ago': 2.0}], 'minus_crosses': [{'type': 'upward_cross', 'value': 1.029, 'periods_ago': 1.0}]}, 'vi_plus_vs_one': 'below', 'vi_minus_vs_one': 'above', 'plus_above_one_pct': 60.2, 'minus_above_one_pct': 40.3}
    Vi Crossovers: [{'type': 'bearish_crossover', 'vi_plus': 0.9679, 'strength': 0.061, 'vi_minus': 1.029, 'periods_ago': 1.0, 'crossover_level': 0.9984}]
    Key Level Crosses: [{'level': 1.0, 'strength': 0.02556810285994693, 'direction': 'down', 'periods_ago': 2.0}]
    Patterns: compression
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'persistence': 5.0, 'crossover_scan': 14.0}, 'aligned_periods': 186.0}, calculation_notes: Vortex analysis based on 186 aligned VI+/VI- periods

  stochastic:
    Current: {'spread': -9.48, 'd_percent': 61.55, 'k_percent': 52.08, 'timestamp': '2025-10-17T14:56:08.928239+00:00'}
    Summary: Stochastic %K: 52.1, %D: 61.6. Bearish Crossover 1p ago
    Trend: momentum: strong_bearish_acceleration, velocity: -8.05, k_direction: falling, acceleration: -13.6
    Volatility: 28.288
    Spread_Momentum: -9.66
    Neutral: {'bias': 'bullish', 'level': 50.0, 'distance_from_50': 2.08}
    Oversold: {'level': 20.0, 'status': 'above', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'time_percentage': 16.4}
    Overbought: {'level': 80.0, 'status': 'below', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'time_percentage': 31.7}
    Patterns: momentum
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'aligned_periods': 183.0, 'valid_data_percentage': 97.9}, calculation_notes: Stochastic analysis based on 183 aligned K/D periods

  williams_r:
    Current: {'value': -86.52, 'timestamp': '2025-10-17T14:56:08.931647+00:00'}
    Summary: Williams %R at -86.5 (oversold for 1 periods), strong downward acceleration
    Trend: strength: 0.219, velocity: -37.857, direction: falling, acceleration: -45.65
    Momentum: volatility: 30.0, recent_range: 75.71, interpretation: strong_downward_acceleration
    Volatility: 30.001
    Neutral: {'bias': 'bearish', 'level': -50.0, 'distance_from_50': -36.52}
    Oversold: {'level': -80.0, 'status': 'in_zone', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 1.0, 'time_percentage': 18.2}
    Overbought: {'level': -20.0, 'status': 'below', 'exit_analysis': {'latest_exit': {'strength': 1.0, 'exit_level': -46.45, 'periods_ago': 2.0}, 'recent_exits': [{'strength': 1.0, 'exit_level': -46.45, 'periods_ago': 2.0}]}, 'streak_length': 0.0, 'time_percentage': 32.1}
    Patterns: momentum, failure_swing
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'acceleration': 4.0, 'position_rank': 14.0}, 'aligned_periods': 187.0}, calculation_notes: Williams %R analysis based on 187 periods with length=14

  bollinger_bands:
    Current: {'lower': 101341.5769, 'upper': 124235.7581, 'middle': 112788.6675, 'bandwidth': 20.2983, 'percent_b': 0.1713}

=== 30M TIMEFRAME ===
  dc:
    Current: {'price': 105140.0, 'timestamp': '2025-10-17T14:56:46.789422+00:00', 'channel_width': 5424.1, 'lower_channel': 103500.0, 'upper_channel': 108924.1, 'middle_channel': 106212.05, 'price_position_pct': 30.2}
    Summary: Donchian: Price 105140.0000 (30.2%), Width 5424.1000
    Trend: strength: moderate_downward, position_pct: 30.2, utilization_rating: low, channel_utilization: 0.414
    Length: 20.0
    Consolidation: price_range: 0.0, price_range_pct: 0.0, width_threshold: 3171.7564, is_consolidation: False, breakout_potential: low, consolidation_periods: 0.0
    Position: {'position': 'lower_third', 'position_pct': 30.2, 'distance_to_lower': 1640.0, 'distance_to_upper': 3784.1, 'distance_to_middle': 1072.05}
    Support Resistance: {'lower': {'breaks': 0.0, 'bounces': 2.0, 'touches': 3.0, 'bounce_rate': 0.667}, 'upper': {'breaks': 0.0, 'bounces': 2.0, 'touches': 4.0, 'bounce_rate': 0.5}, 'middle': {'breaks': 0.0, 'bounces': 4.0, 'touches': 7.0, 'bounce_rate': 0.571}}
    Patterns: breakouts, width_analysis, turtle_patterns
    Quality: data_quality: {'total_periods': 81.0, 'width_corrections': 0.0, 'valid_data_percentage': 81.0}, calculation_notes: Donchian analysis based on 81 aligned data points with period 20

  adx:
    Current: {'adx': 35.44, 'plus_di': 15.41, 'minus_di': 27.59, 'timestamp': '2025-10-17T14:56:46.714607+00:00'}
    Summary: ADX 35.4 - Strong trending market with bearish bias (12.2)
    Description: Strong trending market
    Strength_Value: 35.44
    Trend_Strength: strong
    Trend_Evolution: stable
    Directional_Bias: bearish
    Directional_Strength: 12.18
    Weak Threshold: 20.0
    Current Strength: strong
    Strong Threshold: 25.0
    Extreme Threshold: 60.0
    Very Strong Threshold: 40.0

  atr:
    Current: {'value': 863.250139, 'timestamp': '2025-10-17T14:56:46.806224+00:00'}
    Summary: ATR 863.250139 - high volatility (99th percentile)
    Trend: strength: 0.206, velocity: 22.58037, direction: rising, consistency: 0.75, acceleration: -23.471123, interpretation: volatility_stable
    Breakout: breakout_setup: 0.0, squeeze_periods: 0.0, squeeze_detected: 0.0, expansion_potential: 0.0, recent_volatility_change_pct: 8.02
    Relative: regime: elevated_volatility, comparisons: {'5p_avg': 4.81, '10p_avg': 6.68, '20p_avg': 23.05, '50p_avg': 21.82}, regime_ratio: 1.218
    Cycles: {'cycle_detected': 0.0}
    Stop Loss: {'stop_levels': {'1.0x_atr': {'distance': 863.250139, 'long_stop': 104276.749861, 'short_stop': 106003.250139, 'distance_pct': 0.821}, '1.5x_atr': {'distance': 1294.875208, 'long_stop': 103845.124792, 'short_stop': 106434.875208, 'distance_pct': 1.232}, '2.0x_atr': {'distance': 1726.500278, 'long_stop': 103413.499722, 'short_stop': 106866.500278, 'distance_pct': 1.642}, '2.5x_atr': {'distance': 2158.125347, 'long_stop': 102981.874653, 'short_stop': 107298.125347, 'distance_pct': 2.053}, '3.0x_atr': {'distance': 2589.750416, 'long_stop': 102550.249584, 'short_stop': 107729.750416, 'distance_pct': 2.463}}, 'current_price': 105140.0, 'recommended_stop': {'distance': 2158.125347, 'long_stop': 102981.874653, 'short_stop': 107298.125347, 'distance_pct': 2.053}, 'recommended_multiplier': 2.5}
    Volatility: {'statistical': {'max': 863.250139, 'min': 493.754682, 'std': 109.81404, 'mean': 655.445663}, 'current_level': 'high', 'percentile_rank': 98.8, 'relative_to_mean': 31.7, 'relative_to_price_pct': 0.821}
    Quality: clarity: 1.00, consistency: 0.21, data_quality: 0.43

  bbw:
    Current: {'width': 4.65, 'timestamp': '2025-10-17T14:56:46.810680+00:00'}
    Summary: BB Width 4.65% - above average volatility (76th percentile)
    Trend: strength: 0.258, velocity: -0.49, direction: contracting, acceleration: -0.425
    Breakout: potential: low, recent_change: -0.996, setup_quality: poor_setup, potential_score: 0.2, change_direction: contracting
    Expansion: cycle_stage: unclear, recent_peak: None, max_expansion: 4.65, recent_trough: None, cycle_position: unclear, expansion_peaks: 0.0, contraction_troughs: 0.0, avg_expansion_height: 4.65
    Cycles: {'total_cycles': 0.0, 'avg_cycle_length': None, 'expanding_time_pct': 38.3, 'contracting_time_pct': 61.7}
    Squeeze: {'is_squeeze': 0.0, 'squeeze_periods': 0.0, 'squeeze_quality': 'weak', 'squeeze_frequency': 0.556, 'squeeze_intensity': 0.0, 'squeeze_threshold': 1.54}
    Volatility: {'level': 'above_average', 'statistics': {'max': 6.88, 'min': 0.95, 'std': 1.9, 'mean': 2.76}, 'percentile_rank': 76.5, 'relative_to_mean': 68.19}
    Quality: clarity: 0.99, consistency: 0.26, data_quality: 0.41

  cci:
    Current: {'value': -53.37, 'timestamp': '2025-10-17T14:56:46.598778+00:00'}
    Summary: CCI at -53.4
    Length: 20.0
    Momentum: velocity: -0.69, volatility: 110.24, acceleration: -41.51, recent_range: 108.48, trend_strength: 0.035, trend_direction: falling, momentum_interpretation: sideways_momentum
    Zero_Line: zero_crossings: 8.0, current_position: below, distance_from_zero: 53.37, time_above_zero_pct: 33.3, time_below_zero_pct: 66.7
    Oversold: {'level': -100.0, 'status': 'above', 'exit_analysis': {'latest_exit': {'strength': 50.797919792986775, 'exit_level': -49.202080207013225, 'periods_ago': 8.0}, 'recent_exits': [{'strength': 50.797919792986775, 'exit_level': -49.202080207013225, 'periods_ago': 8.0}]}, 'streak_length': 0.0, 'extreme_reading': False, 'time_percentage': 27.2}
    Overbought: {'level': 100.0, 'status': 'below', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'extreme_reading': False, 'time_percentage': 13.6}
    Zone: neutral
    Neutral Bias: bearish
    Quality: data_quality: {'total_periods': 81.0, 'recent_volatility': 34.045, 'valid_data_percentage': 81.0}, calculation_notes: CCI analysis based on 81 valid data points with period 20

  ema:
    Current: {'price': 105140.0, 'ema_value': 105956.9565, 'timestamp': '2025-10-17T14:56:46.753129+00:00', 'price_distance': -816.9565, 'price_distance_pct': -0.771}
    Summary: EMA 105956.9565 - falling trend, low responsiveness, price -0.8%
    Length: 20.0
    Responsiveness: avg_change: 80.458422, max_change: 283.837346, change_frequency: 0.125, direction_changes: 10.0, relative_volatility: 0.015369, responsiveness_score: 0.139, responsiveness_rating: low
    Signal_Quality: noise_level: low, signal_quality: low_frequency_high_reliability, recommended_use: Reliable for position trading, slower signals
    Trend: {'slope': -74.167589, 'strength': 0.294, 'consensus': 'falling', 'long_term': 'falling', 'short_term': 'falling', 'consistency': 1.0, 'medium_term': 'falling', 'acceleration': -17.366584}
    Price Relationship: {'distance': -816.9565, 'position': 'below', 'avg_distance': -610.707, 'distance_pct': -0.771, 'above_ema_pct': 29.6, 'below_ema_pct': 70.4, 'avg_distance_pct': -0.558}
    Support Resistance: {'success_rate': 0.484, 'effectiveness': 'medium', 'total_touches': 31.0, 'recent_bounces': [{'type': 'resistance_bounce', 'index': 54.0, 'strength': 0.003730534146332499, 'periods_ago': 26.0}, {'type': 'support_bounce', 'index': 56.0, 'strength': 0.0006203536566451831, 'periods_ago': 24.0}, {'type': 'resistance_bounce', 'index': 59.0, 'strength': 0.0014684557352374309, 'periods_ago': 21.0}], 'recent_touches': [{'index': 59.0, 'price': 108958.0, 'ema_value': 108795.20217591486, 'periods_ago': 21.0}, {'index': 60.0, 'price': 108798.0, 'ema_value': 108795.46863535154, 'periods_ago': 20.0}, {'index': 61.0, 'price': 108834.3, 'ema_value': 108799.16686055616, 'periods_ago': 19.0}, {'index': 73.0, 'price': 106261.1, 'ema_value': 106499.80380585813, 'periods_ago': 7.0}, {'index': 78.0, 'price': 105829.9, 'ema_value': 106146.16789185221, 'periods_ago': 2.0}], 'successful_bounces': 15.0}
    Patterns: crossovers
    Quality: data_quality: {'had_sma': 0.0, 'had_prices': 1.0, 'has_price_data': 1.0, 'aligned_periods': 81.0, 'has_sma_comparison': 0.0, 'original_ema_periods': 100.0, 'valid_data_percentage': 81.0}, calculation_notes: EMA analysis based on 81 aligned data points with period 20

  mfi:
    Current: {'value': 33.4, 'timestamp': '2025-10-17T14:56:46.624038+00:00'}
    Summary: MFI at 33.4, selling pressure
    Length: 14.0
    Position_Rank: percentile: 78.6, interpretation: high
    Zone: neutral
    Money Flow: {'pressure': 'selling', 'consistency': 0.75, 'flow_quality': 'low_quality_flow', 'cycle_analysis': {'cycle_detected': 0.0}, 'pressure_strength': 0.332, 'volume_confirmation': 'strong'}
    Patterns: momentum
    Quality: data_quality: {'had_prices': 1.0, 'original_periods': {'mfi': 100.0, 'prices': 100.0}, 'core_analysis_periods': 87.0, 'divergence_aligned_periods': 87.0}, calculation_notes: MFI analysis based on 87 core periods, divergence on 87 aligned periods

  obv:
    Current: {'value': -1973.77, 'timestamp': '2025-10-17T14:56:46.812034+00:00'}
    Summary: OBV -1974 - bullish trend (strong, 0.98), accumulation detected
    Length: 14.0
    Relative: max_obv: 1149.81, min_obv: -2668.22, position: near_low, position_percentile: 18.2
    Trend: {'strength': 0.984, 'velocity': 91.32, 'consensus': 'bullish', 'long_term': 'bullish', 'short_term': 'bullish', 'consistency': 0.556, 'medium_term': 'bullish'}
    Accumulation: {'overall_phase': 'accumulation_phase', 'phase_strength': 'strong', 'timeframe_analysis': {'5p': {'score': 'strong_accumulation', 'change_pct': 22.16}, '10p': {'score': 'strong_accumulation', 'change_pct': 26.03}, '20p': {'score': 'strong_distribution', 'change_pct': -147.37}}}
    Patterns: flow, momentum
    Quality: data_quality: {'had_prices': 1.0, 'had_volumes': 1.0, 'cleaned_periods': 100.0, 'original_periods': {'obv': 100.0, 'prices': 100.0, 'volumes': 100.0}}, calculation_notes: OBV analysis based on 100 periods with length 14

  roc:
    Current: {'value': 0.575, 'timestamp': '2025-10-17T14:56:46.628594+00:00', 'value_pct': '+0.58%'}
    Summary: ROC +0.58% - weak positive momentum
    Trend: slope: 0.089, strength: 0.045, direction: sideways, consistency: 0.506
    Length: 10.0
    Momentum: strength: 0.5752898929199302, direction: positive, evolution: accelerating, persistence: 0.6, strength_level: weak
    Velocity: velocity: 0.089, acceleration: -0.558, interpretation: stable_momentum
    Calculation_Periods: 90.0
    Extremes: {'condition': 'neutral', 'current_streak': 0.0, 'oversold_time_pct': 12.2, 'oversold_threshold': -2.56, 'overbought_time_pct': 0.0, 'overbought_threshold': 1.39, 'extreme_oversold_threshold': -5.53, 'extreme_overbought_threshold': 4.36}
    Zero Line: {'position': 'above_zero', 'above_zero_pct': 43.3, 'below_zero_pct': 56.7, 'recent_crosses': [{'type': 'bullish_zero_cross', 'value': 0.575, 'periods_ago': 1.0}, {'type': 'bearish_zero_cross', 'value': -0.033, 'periods_ago': 2.0}, {'type': 'bullish_zero_cross', 'value': 0.307, 'periods_ago': 4.0}], 'total_crossings': 19.0, 'crossing_frequency': 0.211}
    Quality: data_quality: {'had_prices': 1.0, 'clean_periods': 90.0, 'original_periods': 90.0, 'calculation_periods': 10.0, 'valid_data_percentage': 100.0}, calculation_notes: ROC analysis based on 90 periods with length=10

  rsi:
    Current: {'value': 39.22, 'timestamp': '2025-10-17T14:56:46.545441+00:00'}
    Summary: RSI at 39.2
    Ma5: 40.15
    Ma10: 37.59
    Trend: strength: 0.039, velocity: -0.413, direction: sideways, acceleration: -8.094
    Volatility: 9.483
    Neutral: {'level': 50.0, 'status': 'below', 'distance': -10.78}
    Oversold: {'level': 30.0, 'status': 'far_above', 'periods_in_zone': 0.0, 'time_percentage': 12.8}
    Overbought: {'level': 70.0, 'status': 'far_below', 'periods_in_zone': 0.0, 'time_percentage': 0.0}
    Quality: data_quality: {'total_periods': 86.0, 'recent_volatility': 7.622, 'valid_data_percentage': 86.0}, calculation_notes: RSI analysis based on 86 valid data points

  sma:
    Current: {'price': 105140.0, 'sma_value': 105830.9, 'timestamp': '2025-10-17T14:56:46.757187+00:00', 'price_distance': -690.9, 'price_distance_pct': -0.653}
    Summary: SMA 105830.9000 - bearish trend (strong), price below (-0.7%)
    Slope: alignment: aligned, direction: downward, acceleration: -39.9375, long_term_slope: -175.4955, short_term_slope: -181.465, medium_term_slope: -180.412
    Trend: slope: -180.412, strength: 1.0, consensus: bearish, long_term: bearish, short_term: bearish, consistency: 1.0, medium_term: bearish
    Length: 20.0
    Quality: smoothness: 0.985, trend_clarity: 0.838, responsiveness: 0.073, overall_quality: 0.911
    Smoothing_Factor: 0.0952
    Current Level: 105830.9
    Trend Direction: bearish
    Price Relationship: {'distance': -690.9, 'position': 'below', 'distance_pct': -0.653, 'above_sma_pct': 32.1, 'below_sma_pct': 67.9, 'position_changes': 10, 'position_stability': 0.875}
    Support Resistance: {'success_rate': 0.561, 'effectiveness': 'medium', 'total_touches': 41.0, 'recent_bounces': [{'type': 'resistance_bounce', 'index': 59.0, 'strength': 0.0014684557352374309, 'periods_ago': 21.0}, {'type': 'resistance_bounce', 'index': 61.0, 'strength': 0.004147589500736521, 'periods_ago': 19.0}, {'type': 'resistance_bounce', 'index': 62.0, 'strength': 0.005189933098302408, 'periods_ago': 18.0}], 'recent_touches': [{'index': 59.0, 'price': 108958.0, 'sma_value': 108445.23999999999, 'periods_ago': 21.0}, {'index': 60.0, 'price': 108798.0, 'sma_value': 108452.405, 'periods_ago': 20.0}, {'index': 61.0, 'price': 108834.3, 'sma_value': 108498.53, 'periods_ago': 19.0}, {'index': 62.0, 'price': 108382.9, 'sma_value': 108508.175, 'periods_ago': 18.0}, {'index': 78.0, 'price': 105829.9, 'sma_value': 106208.58, 'periods_ago': 2.0}], 'successful_bounces': 23.0}
    Patterns: crossovers, slope_direction, trend_alignment
    Quality: data_quality: {'had_prices': 1.0, 'aligned_periods': 81.0, 'original_periods': 81.0, 'calculation_periods': 20.0, 'valid_data_percentage': 100.0}, calculation_notes: SMA analysis based on 81 periods with length=20

  macd:
    Current: {'macd': -745.5856, 'signal': -833.5641, 'histogram': 87.9786, 'timestamp': '2025-10-17T14:56:46.562459+00:00'}
    Summary: MACD rising trend with increasing momentum. Recent bullish_crossover 5p ago
    Histogram: {'acceleration': -2.5663, 'histogram_strength': 87.97857389176295, 'momentum_direction': 'decreasing', 'zero_crossings_recent': 1.0}
    Zero Line: {'current_position': 'below', 'distance_from_zero': 745.5856, 'time_above_zero_pct': 11.9, 'time_below_zero_pct': 88.1}
    Patterns: crossovers
    Quality: data_quality: {'aligned_periods': 67.0, 'original_periods': {'macd': 100.0, 'prices': 100.0, 'signal': 100.0, 'histogram': 100.0}, 'valid_data_percentage': 67.0}, calculation_notes: MACD analysis based on 67 aligned data points
    Legacy Trend: bullish

  psar:
    Current: {'price': 105140.0, 'distance': 1231.5188, 'timestamp': '2025-10-17T14:56:46.736582+00:00', 'psar_value': 103908.4812, 'distance_percentage': 1.171}
    Summary: PSAR 103908.4812 - bullish trend for 8 periods, 1.17% from price
    Trend: trend_periods: 8.0, trend_strength: 0.916, current_direction: bullish, trend_consistency: 0.8, strength_interpretation: very_strong
    Length: 14.0
    Distance: max_distance: 2761.1, min_distance: -3580.2132, average_distance: -240.9457, current_absolute: 1231.5188, distance_volatility: 1550.0695, current_relative_pct: 1.171, distance_interpretation: normal_distance
    Acceleration: velocity: 56.005512, acceleration: -5.892586, rate_of_change_5p: 0.218, acceleration_interpretation: decelerating_upward
    Calculation_Periods: 99.0
    Trend Direction: unknown
    Stop Distance Pct: 1.171
    Current Stop Level: 103908.4812
    Patterns: signal_analysis
    Quality: stop_loss: {'stop_type': 'trailing_stop', 'performance': {'total_tests': 85.0, 'successful_stops': 64.0, 'effectiveness_rate': 0.753}, 'stop_distance': 1231.5188, 'recommendation': 'reasonable_stop', 'stop_distance_pct': 1.171, 'current_stop_level': 103908.4812}, data_quality: {'aligned_periods': 99.0, 'had_high_low_data': 1.0, 'calculation_periods': 14.0}, calculation_notes: Parabolic SAR analysis based on 99 aligned periods

  trix:
    Current: {'trix': -0.117955, 'signal': 105140.0, 'histogram': -105140.117955, 'timestamp': '2025-10-17T14:56:46.696514+00:00'}
    Summary: TRIX -0.117955 - very_strong bearish momentum, histogram -105140.117955 (below zero)
    Trend: strength: 0.015, velocity: 0.003293, direction: sideways, acceleration: 0.003574
    Momentum: direction: bearish, persistence: 1.0, strength_level: very_strong
    Volatility: 0.045923
    Zero Line: {'position': 'below_zero', 'above_zero_pct': 14.0, 'below_zero_pct': 79.1, 'recent_crossings': []}
    Signal Line: {'latest_crossover': None, 'recent_crossovers': [], 'crossover_frequency': 0.0}
    Quality: data_quality: {'had_prices': 0.0, 'had_signal': 1.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'acceleration': 4.0, 'turning_points': 14.0}, 'aligned_periods': 86.0}, calculation_notes: TRIX analysis based on 86 aligned periods with length=14

  vwap:
    Current: {'price': 105140.0, 'timestamp': '2025-10-17T14:56:46.841663+00:00', 'vwap_value': 106127.6257, 'price_distance': -987.6257, 'price_distance_pct': -0.931}
    Summary: VWAP 106127.6257, price below (-0.9%) - slightly undervalued
    Trend: strength: 0.043, velocity: -78.365741, direction: sideways, smoothness: 0.985
    Anchored: momentum: -78.365741, reset_detected: False, behavior_quality: choppy, direction_consistency: 0.687
    Fair_Value: assessment: slightly_undervalued, distance_pct: -0.931, reversion_tendency: medium
    Volatility: 930.2129
    Volume_Profile: volume_bias: below_vwap, avg_volume_above: 132.75, avg_volume_below: 216.94, near_vwap_volume_pct: 52.5, above_vwap_volume_pct: 24.8, below_vwap_volume_pct: 75.2, institutional_activity: high
    Price Position: {'bias': 'bearish', 'current': 'below', 'above_vwap_pct': 35.0, 'below_vwap_pct': 65.0, 'position_changes': 18.0}
    Deviation Bands: {'lower_1std': 105197.4128, 'lower_2std': 104267.1999, 'upper_1std': 107057.8386, 'upper_2std': 107988.0515, 'current_position': 'below_1std', 'std_devs_from_vwap': -1.06}
    Patterns: volume_clustering
    Quality: data_quality: {'had_volumes': 1.0, 'aligned_periods': 100.0, 'volume_profile_available': 1.0, 'support_resistance_touches': 41.0}, calculation_notes: VWAP analysis based on 100 aligned price/VWAP periods

  aroon:
    Current: {'aroon_up': 50.0, 'timestamp': '2025-10-17T14:56:46.662111+00:00', 'aroon_down': 35.71, 'oscillator': 14.29}
    Summary: Aroon Up: 50.0, Down: 35.7 - sideways trend
    Trend: separation: 14.29, current_trend: sideways, trend_quality: poor, trend_duration: 1.0, trend_strength: 0.143, trend_consistency: 0.1
    Strength: up_momentum: 16.67, up_evolution: rising, down_momentum: -7.14, down_evolution: falling, aroon_up_strength: moderate, combined_strength: moderate, dominant_indicator: aroon_up, aroon_down_strength: weak
    Parallel_Movement: correlation: -0.471, movement_type: moderate_negative_correlation, interpretation: Some opposition in indicator movement
    Crossovers: {'latest_crossover': {'type': 'bullish_crossover', 'location': 'mid_levels', 'strength': 14.285714285714292, 'up_value': 50.0, 'down_value': 35.71, 'periods_ago': 1.0}, 'recent_crossovers': [{'type': 'bullish_crossover', 'location': 'mid_levels', 'strength': 14.285714285714292, 'up_value': 50.0, 'down_value': 35.71, 'periods_ago': 1.0}], 'crossover_frequency': 'low'}
    Oscillator: {'zone': 'neutral', 'velocity': 23.81, 'acceleration': 25.0, 'current_value': 14.29, 'zero_crossings': 9.0, 'time_above_zero_pct': 41.9, 'time_below_zero_pct': 58.1, 'oscillator_interpretation': 'bullish_strengthening'}
    Quality: clarity: 0.14, consistency: 0.10, data_quality: 0.43

  vortex:
    Current: {'spread': -0.1099, 'vi_plus': 0.9299, 'dominant': 'VI-', 'vi_minus': 1.0398, 'timestamp': '2025-10-17T14:56:46.665434+00:00'}
    Summary: Vortex VI+ 0.930, VI- 1.040 - VI minus dominant (+0.110)
    Trend: strength: 0.252, velocity: 0.070571, direction: rising, acceleration: 0.059774
    Dominance: current: VI_minus, strength: 0.1099, persistence: 1.0
    Volatility: 0.3091
    One Line: {'recent_crosses': {'plus_crosses': [], 'minus_crosses': []}, 'vi_plus_vs_one': 'below', 'vi_minus_vs_one': 'above', 'plus_above_one_pct': 37.2, 'minus_above_one_pct': 67.4}
    Vi Crossovers: []
    Key Level Crosses: []
    Patterns: compression
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'persistence': 5.0, 'crossover_scan': 14.0}, 'aligned_periods': 86.0}, calculation_notes: Vortex analysis based on 86 aligned VI+/VI- periods

  stochastic:
    Current: {'spread': 3.1, 'd_percent': 54.19, 'k_percent': 57.29, 'timestamp': '2025-10-17T14:56:46.577771+00:00'}
    Summary: Stochastic %K: 57.3, %D: 54.2. Bullish Crossover 3p ago
    Trend: momentum: bullish_momentum, velocity: 3.45, k_direction: rising, acceleration: 2.65
    Volatility: 26.739
    Spread_Momentum: -3.14
    Neutral: {'bias': 'bullish', 'level': 50.0, 'distance_from_50': 7.29}
    Oversold: {'level': 20.0, 'status': 'above', 'exit_analysis': {'latest_exit': {'strength': 0.33990365499727276, 'exit_level': 26.798073099945455, 'periods_ago': 8.0}, 'recent_exits': [{'strength': 0.33990365499727276, 'exit_level': 26.798073099945455, 'periods_ago': 8.0}]}, 'streak_length': 0.0, 'time_percentage': 26.5}
    Overbought: {'level': 80.0, 'status': 'below', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'time_percentage': 10.8}
    Patterns: momentum
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'aligned_periods': 83.0, 'valid_data_percentage': 95.4}, calculation_notes: Stochastic analysis based on 83 aligned K/D periods

  williams_r:
    Current: {'value': -47.05, 'timestamp': '2025-10-17T14:56:46.591244+00:00'}
    Summary: Williams %R at -47.1, strong downward acceleration
    Trend: strength: 0.123, velocity: -7.771, direction: rising, acceleration: -6.01
    Momentum: volatility: 28.91, recent_range: 59.5, interpretation: strong_downward_acceleration
    Volatility: 28.907
    Neutral: {'bias': 'bullish', 'level': -50.0, 'distance_from_50': 2.95}
    Oversold: {'level': -80.0, 'status': 'above', 'exit_analysis': {'latest_exit': {'strength': 0.09192394906680619, 'exit_level': -78.16, 'periods_ago': 9.0}, 'recent_exits': [{'strength': 0.09192394906680619, 'exit_level': -78.16, 'periods_ago': 9.0}]}, 'streak_length': 0.0, 'time_percentage': 28.7}
    Overbought: {'level': -20.0, 'status': 'below', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'time_percentage': 17.2}
    Patterns: failure_swing
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'acceleration': 4.0, 'position_rank': 14.0}, 'aligned_periods': 87.0}, calculation_notes: Williams %R analysis based on 87 periods with length=14

  bollinger_bands:
    Current: {'lower': 103372.1354, 'upper': 108289.6646, 'middle': 105830.9, 'bandwidth': 4.6466, 'percent_b': 0.3595}

=== 4H TIMEFRAME ===
  dc:
    Current: {'price': 105198.64, 'timestamp': '2025-10-17T14:56:15.077933+00:00', 'channel_width': 10084.12, 'lower_channel': 103528.23, 'upper_channel': 113612.35, 'middle_channel': 108570.29, 'price_position_pct': 16.6}
    Summary: Donchian: Price 105198.6400 (16.6%), Width 10084.1200 - CONSOLIDATION (1p)
    Trend: strength: strong_downward, position_pct: 16.6, utilization_rating: medium, channel_utilization: 0.615
    Length: 20.0
    Consolidation: price_range: 0.0, price_range_pct: 0.0, width_threshold: 10137.2963, is_consolidation: True, breakout_potential: low, consolidation_periods: 1.0
    Position: {'position': 'near_lower', 'position_pct': 16.6, 'distance_to_lower': 1670.41, 'distance_to_upper': 8413.71, 'distance_to_middle': 3371.65}
    Support Resistance: {'lower': {'breaks': 0.0, 'bounces': 0.0, 'touches': 0.0, 'bounce_rate': 0.0}, 'upper': {'breaks': 0.0, 'bounces': 1.0, 'touches': 6.0, 'bounce_rate': 0.167}, 'middle': {'breaks': 0.0, 'bounces': 1.0, 'touches': 1.0, 'bounce_rate': 1.0}}
    Patterns: breakouts, width_analysis, turtle_patterns
    Quality: data_quality: {'total_periods': 131.0, 'width_corrections': 0.0, 'valid_data_percentage': 87.3}, calculation_notes: Donchian analysis based on 131 aligned data points with period 20

  adx:
    Current: {'adx': 46.6, 'plus_di': 8.02, 'minus_di': 33.91, 'timestamp': '2025-10-17T14:56:14.956922+00:00'}
    Summary: ADX 46.6 - Very strong trend with bearish bias (25.9)
    Description: Very strong trend
    Strength_Value: 46.6
    Trend_Strength: very_strong
    Trend_Evolution: stable
    Directional_Bias: bearish
    Directional_Strength: 25.89
    Weak Threshold: 20.0
    Current Strength: very_strong
    Strong Threshold: 25.0
    Extreme Threshold: 60.0
    Very Strong Threshold: 40.0
    Patterns: di_patterns

  atr:
    Current: {'value': 1969.869524, 'timestamp': '2025-10-17T14:56:15.116281+00:00'}
    Summary: ATR 1969.869524 - high volatility (85th percentile)
    Trend: strength: 0.132, velocity: 66.025425, direction: rising, consistency: 0.5, acceleration: -50.039831, interpretation: volatility_stable
    Breakout: breakout_setup: 0.0, squeeze_periods: 0.0, squeeze_detected: 0.0, expansion_potential: 0.0, recent_volatility_change_pct: 8.97
    Relative: regime: normal_volatility, comparisons: {'5p_avg': 4.18, '10p_avg': 6.97, '20p_avg': 5.19, '50p_avg': 1.17}, regime_ratio: 1.012
    Cycles: {'cycle_detected': 0.0}
    Stop Loss: {'stop_levels': {'1.0x_atr': {'distance': 1969.869524, 'long_stop': 103228.770476, 'short_stop': 107168.509524, 'distance_pct': 1.873}, '1.5x_atr': {'distance': 2954.804285, 'long_stop': 102243.835715, 'short_stop': 108153.444285, 'distance_pct': 2.809}, '2.0x_atr': {'distance': 3939.739047, 'long_stop': 101258.900953, 'short_stop': 109138.379047, 'distance_pct': 3.745}, '2.5x_atr': {'distance': 4924.673809, 'long_stop': 100273.966191, 'short_stop': 110123.313809, 'distance_pct': 4.681}, '3.0x_atr': {'distance': 5909.608571, 'long_stop': 99289.031429, 'short_stop': 111108.248571, 'distance_pct': 5.618}}, 'current_price': 105198.64, 'recommended_stop': {'distance': 4924.673809, 'long_stop': 100273.966191, 'short_stop': 110123.313809, 'distance_pct': 4.681}, 'recommended_multiplier': 2.5}
    Volatility: {'statistical': {'max': 2661.695336, 'min': 678.095911, 'std': 501.014289, 'mean': 1378.244038}, 'current_level': 'high', 'percentile_rank': 85.3, 'relative_to_mean': 42.93, 'relative_to_price_pct': 1.873}
    Quality: clarity: 1.00, consistency: 0.13, data_quality: 0.68

  bbw:
    Current: {'width': 8.78, 'timestamp': '2025-10-17T14:56:15.134981+00:00'}
    Summary: BB Width 8.78% - above average volatility (82th percentile)
    Trend: strength: 0.245, velocity: 0.817, direction: expanding, acceleration: 0.396
    Breakout: potential: low, recent_change: 1.762, setup_quality: poor_setup, potential_score: 0.2, change_direction: expanding
    Expansion: cycle_stage: unclear, recent_peak: None, max_expansion: 8.78, recent_trough: None, cycle_position: unclear, expansion_peaks: 0.0, contraction_troughs: 0.0, avg_expansion_height: 8.78
    Cycles: {'total_cycles': 0.0, 'avg_cycle_length': None, 'expanding_time_pct': 36.6, 'contracting_time_pct': 63.4}
    Squeeze: {'is_squeeze': 0.0, 'squeeze_periods': 0.0, 'squeeze_quality': 'weak', 'squeeze_frequency': 0.366, 'squeeze_intensity': 0.0, 'squeeze_threshold': 4.9}
    Volatility: {'level': 'above_average', 'statistics': {'max': 16.7, 'min': 2.02, 'std': 3.34, 'mean': 6.61}, 'percentile_rank': 81.7, 'relative_to_mean': 32.88}
    Quality: clarity: 0.65, consistency: 0.24, data_quality: 0.66

  cci:
    Current: {'value': -169.84, 'timestamp': '2025-10-17T14:56:14.782321+00:00'}
    Summary: CCI at -169.8 (oversold for 7 periods), strong falling momentum
    Length: 20.0
    Momentum: velocity: -13.27, volatility: 132.95, acceleration: 45.29, recent_range: 126.69, trend_strength: 0.664, trend_direction: falling, momentum_interpretation: strong_falling_momentum
    Zero_Line: zero_crossings: 6.0, current_position: below, distance_from_zero: 169.84, time_above_zero_pct: 48.1, time_below_zero_pct: 51.9
    Oversold: {'level': -100.0, 'status': 'in_zone', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 7.0, 'extreme_reading': False, 'time_percentage': 22.1}
    Overbought: {'level': 100.0, 'status': 'below', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'extreme_reading': False, 'time_percentage': 26.0}
    Zone: oversold
    Neutral Bias: bearish
    Quality: data_quality: {'total_periods': 131.0, 'recent_volatility': 48.605, 'valid_data_percentage': 87.3}, calculation_notes: CCI analysis based on 131 valid data points with period 20

  ema:
    Current: {'price': 105198.64, 'ema_value': 109635.4582, 'timestamp': '2025-10-17T14:56:15.028210+00:00', 'price_distance': -4436.8182, 'price_distance_pct': -4.047}
    Summary: EMA 109635.4582 - falling trend (strength: 0.71), low responsiveness, price -4.0%
    Length: 20.0
    Responsiveness: avg_change: 229.037707, max_change: 881.68253, change_frequency: 0.108, direction_changes: 14.0, relative_volatility: 0.039207, responsiveness_score: 0.25, responsiveness_rating: low
    Signal_Quality: noise_level: low, signal_quality: low_frequency_high_reliability, recommended_use: Reliable for position trading, slower signals
    Trend: {'slope': -483.840896, 'strength': 0.709, 'consensus': 'falling', 'long_term': 'falling', 'short_term': 'falling', 'consistency': 1.0, 'medium_term': 'falling', 'acceleration': -106.075527}
    Price Relationship: {'distance': -4436.8182, 'position': 'below', 'avg_distance': -205.1656, 'distance_pct': -4.047, 'above_ema_pct': 47.3, 'below_ema_pct': 52.7, 'avg_distance_pct': -0.177}
    Support Resistance: {'success_rate': 0.429, 'effectiveness': 'medium', 'total_touches': 7.0, 'recent_bounces': [{'type': 'support_bounce', 'index': 16.0, 'strength': 0.0027233336723074745, 'periods_ago': 114.0}, {'type': 'support_bounce', 'index': 17.0, 'strength': 0.016552381055959086, 'periods_ago': 113.0}, {'type': 'resistance_bounce', 'index': 108.0, 'strength': 0.014466075056874425, 'periods_ago': 22.0}], 'recent_touches': [{'index': 75.0, 'price': 122884.14, 'ema_value': 122626.98266537114, 'periods_ago': 55.0}, {'index': 81.0, 'price': 122737.57, 'ema_value': 122604.6523230546, 'periods_ago': 49.0}, {'index': 102.0, 'price': 114958.8, 'ema_value': 114836.92870690749, 'periods_ago': 28.0}, {'index': 103.0, 'price': 114821.12, 'ema_value': 114835.42311577345, 'periods_ago': 27.0}, {'index': 108.0, 'price': 115166.0, 'ema_value': 114898.38444078722, 'periods_ago': 22.0}], 'successful_bounces': 3.0}
    Patterns: crossovers
    Quality: data_quality: {'had_sma': 0.0, 'had_prices': 1.0, 'has_price_data': 1.0, 'aligned_periods': 131.0, 'has_sma_comparison': 0.0, 'original_ema_periods': 150.0, 'valid_data_percentage': 87.3}, calculation_notes: EMA analysis based on 131 aligned data points with period 20

  mfi:
    Current: {'value': 19.02, 'timestamp': '2025-10-17T14:56:14.819679+00:00'}
    Summary: MFI at 19.0 (oversold for 4 periods), selling pressure - HIGH QUALITY FLOW
    Length: 14.0
    Position_Rank: percentile: 14.3, interpretation: low
    Zone: oversold
    Money Flow: {'pressure': 'selling', 'consistency': 0.75, 'flow_quality': 'high_quality_flow', 'cycle_analysis': {'cycle_detected': 0.0}, 'pressure_strength': 0.62, 'volume_confirmation': 'strong'}
    Patterns: momentum, formations
    Quality: data_quality: {'had_prices': 1.0, 'original_periods': {'mfi': 150.0, 'prices': 150.0}, 'core_analysis_periods': 137.0, 'divergence_aligned_periods': 137.0}, calculation_notes: MFI analysis based on 137 core periods, divergence on 137 aligned periods

  obv:
    Current: {'value': -41124.99, 'timestamp': '2025-10-17T14:56:15.140016+00:00'}
    Summary: OBV -41125 - bearish trend, distribution detected
    Length: 14.0
    Relative: max_obv: 65618.7, min_obv: -49487.63, position: near_low, position_percentile: 7.3
    Trend: {'strength': 0.032, 'velocity': 101.21, 'consensus': 'bearish', 'long_term': 'bearish', 'short_term': 'bullish', 'consistency': 0.667, 'medium_term': 'bearish'}
    Accumulation: {'overall_phase': 'distribution_phase', 'phase_strength': 'strong', 'timeframe_analysis': {'5p': {'score': 'strong_accumulation', 'change_pct': 6.29}, '10p': {'score': 'strong_distribution', 'change_pct': -50.6}, '20p': {'score': 'strong_distribution', 'change_pct': -82.53}}}
    Patterns: flow, momentum
    Quality: data_quality: {'had_prices': 1.0, 'had_volumes': 1.0, 'cleaned_periods': 150.0, 'original_periods': {'obv': 150.0, 'prices': 150.0, 'volumes': 150.0}}, calculation_notes: OBV analysis based on 150 periods with length 14

  roc:
    Current: {'value': -5.024, 'timestamp': '2025-10-17T14:56:14.835839+00:00', 'value_pct': '-5.02%'}
    Summary: ROC -5.02% - very_strong negative momentum
    Trend: slope: -0.862, strength: 0.431, direction: falling, consistency: 0.525
    Length: 10.0
    Momentum: strength: 5.023903228579002, direction: negative, evolution: decelerating, persistence: 1.0, strength_level: very_strong
    Velocity: velocity: -0.862, acceleration: 0.99, interpretation: decelerating_momentum
    Calculation_Periods: 140.0
    Extremes: {'condition': 'neutral', 'current_streak': 0.0, 'oversold_time_pct': 6.4, 'oversold_threshold': -5.04, 'overbought_time_pct': 4.3, 'overbought_threshold': 4.62, 'extreme_oversold_threshold': -12.28, 'extreme_overbought_threshold': 11.87}
    Zero Line: {'position': 'below_zero', 'above_zero_pct': 54.3, 'below_zero_pct': 45.7, 'recent_crosses': [{'type': 'bearish_zero_cross', 'value': -2.052, 'periods_ago': 9.0}], 'total_crossings': 15.0, 'crossing_frequency': 0.107}
    Quality: data_quality: {'had_prices': 1.0, 'clean_periods': 140.0, 'original_periods': 140.0, 'calculation_periods': 10.0, 'valid_data_percentage': 100.0}, calculation_notes: ROC analysis based on 140 periods with length=10

  rsi:
    Current: {'value': 28.17, 'timestamp': '2025-10-17T14:56:14.714467+00:00'}
    Summary: RSI at 28.2. Oversold for 3 periods
    Ma5: 31.46
    Ma10: 34.56
    Trend: strength: 0.084, velocity: -3.347, direction: sideways, acceleration: 1.923
    Volatility: 18.141
    Neutral: {'level': 50.0, 'status': 'below', 'distance': -21.83}
    Oversold: {'level': 30.0, 'status': 'below', 'periods_in_zone': 3.0, 'time_percentage': 11.8}
    Overbought: {'level': 70.0, 'status': 'far_below', 'periods_in_zone': 0.0, 'time_percentage': 22.1}
    Quality: data_quality: {'total_periods': 136.0, 'recent_volatility': 5.206, 'valid_data_percentage': 90.7}, calculation_notes: RSI analysis based on 136 valid data points

  sma:
    Current: {'price': 105198.64, 'sma_value': 110157.8095, 'timestamp': '2025-10-17T14:56:15.042891+00:00', 'price_distance': -4959.1695, 'price_distance_pct': -4.502}
    Summary: SMA 110157.8095 - bearish trend (strong), price below (-4.5%)
    Slope: alignment: aligned, direction: downward, acceleration: -37.73125, long_term_slope: -301.2241, short_term_slope: -397.905, medium_term_slope: -366.0822
    Trend: slope: -366.0822, strength: 0.758, consensus: bearish, long_term: bearish, short_term: bearish, consistency: 1.0, medium_term: bearish
    Length: 20.0
    Quality: smoothness: 0.958, trend_clarity: 0.946, responsiveness: 0.204, overall_quality: 0.952
    Smoothing_Factor: 0.0952
    Current Level: 110157.8095
    Trend Direction: bearish
    Price Relationship: {'distance': -4959.1695, 'position': 'below', 'distance_pct': -4.502, 'above_sma_pct': 48.1, 'below_sma_pct': 51.9, 'position_changes': 6, 'position_stability': 0.954}
    Support Resistance: {'success_rate': 0.312, 'effectiveness': 'medium', 'total_touches': 16.0, 'recent_bounces': [{'type': 'resistance_bounce', 'index': 78.0, 'strength': 0.010283278996966938, 'periods_ago': 52.0}, {'type': 'resistance_bounce', 'index': 109.0, 'strength': 0.01564396475770922, 'periods_ago': 21.0}, {'type': 'support_bounce', 'index': 113.0, 'strength': 0.0036801916640693123, 'periods_ago': 17.0}], 'recent_touches': [{'index': 105.0, 'price': 114180.0, 'sma_value': 114023.58700000001, 'periods_ago': 25.0}, {'index': 109.0, 'price': 113500.0, 'sma_value': 113053.78, 'periods_ago': 21.0}, {'index': 112.0, 'price': 112900.43, 'sma_value': 113077.76499999998, 'periods_ago': 18.0}, {'index': 113.0, 'price': 112613.7, 'sma_value': 113094.45, 'periods_ago': 17.0}, {'index': 114.0, 'price': 113028.14, 'sma_value': 113156.19700000001, 'periods_ago': 16.0}], 'successful_bounces': 5.0}
    Patterns: crossovers, slope_direction, trend_alignment
    Quality: data_quality: {'had_prices': 1.0, 'aligned_periods': 131.0, 'original_periods': 131.0, 'calculation_periods': 20.0, 'valid_data_percentage': 100.0}, calculation_notes: SMA analysis based on 131 periods with length=20

  macd:
    Current: {'macd': -2097.9039, 'signal': -1650.5756, 'histogram': -447.3283, 'timestamp': '2025-10-17T14:56:14.736786+00:00'}
    Summary: MACD falling trend with decreasing momentum
    Histogram: {'acceleration': -38.7167, 'histogram_strength': 447.3283067865798, 'momentum_direction': 'decreasing', 'zero_crossings_recent': 2.0}
    Zero Line: {'current_position': 'below', 'distance_from_zero': 2097.9039, 'time_above_zero_pct': 53.0, 'time_below_zero_pct': 47.0}
    Patterns: crossovers
    Quality: data_quality: {'aligned_periods': 117.0, 'original_periods': {'macd': 150.0, 'prices': 150.0, 'signal': 150.0, 'histogram': 150.0}, 'valid_data_percentage': 78.0}, calculation_notes: MACD analysis based on 117 aligned data points
    Legacy Trend: bearish

  psar:
    Current: {'price': 105198.64, 'distance': -4213.7928, 'timestamp': '2025-10-17T14:56:15.000575+00:00', 'psar_value': 109412.4328, 'distance_percentage': -4.006}
    Summary: PSAR 109412.4328 - bearish trend for 20 periods, 4.01% from price
    Trend: trend_periods: 20.0, trend_strength: 1.0, current_direction: bearish, trend_consistency: 1.0, strength_interpretation: very_strong
    Length: 14.0
    Distance: max_distance: 11677.8865, min_distance: -10033.8963, average_distance: 409.07, current_absolute: -4213.7928, distance_volatility: 4194.0716, current_relative_pct: -4.006, distance_interpretation: wide_distance
    Acceleration: velocity: -822.56218, acceleration: -642.157976, rate_of_change_5p: -2.734, acceleration_interpretation: accelerating_downward
    Calculation_Periods: 149.0
    Trend Direction: unknown
    Stop Distance Pct: 4.006
    Current Stop Level: 109412.4328
    Patterns: extended_trend, signal_analysis
    Quality: stop_loss: {'stop_type': 'trailing_stop', 'performance': {'total_tests': 90.0, 'successful_stops': 58.0, 'effectiveness_rate': 0.644}, 'stop_distance': 4213.7928, 'recommendation': 'very_wide_stop', 'stop_distance_pct': 4.006, 'current_stop_level': 109412.4328}, data_quality: {'aligned_periods': 149.0, 'had_high_low_data': 1.0, 'calculation_periods': 14.0}, calculation_notes: Parabolic SAR analysis based on 149 aligned periods

  trix:
    Current: {'trix': -0.210333, 'signal': 105198.64, 'histogram': -105198.850333, 'timestamp': '2025-10-17T14:56:14.930301+00:00'}
    Summary: TRIX -0.210333 - strong bearish momentum, histogram -105198.850333 (below zero)
    Trend: strength: 0.053, velocity: -0.015407, direction: sideways, acceleration: -0.007607
    Momentum: direction: bearish, persistence: 1.0, strength_level: strong
    Volatility: 0.180652
    Zero Line: {'position': 'below_zero', 'above_zero_pct': 44.9, 'below_zero_pct': 52.9, 'recent_crossings': []}
    Signal Line: {'latest_crossover': None, 'recent_crossovers': [], 'crossover_frequency': 0.0}
    Quality: data_quality: {'had_prices': 0.0, 'had_signal': 1.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'acceleration': 4.0, 'turning_points': 14.0}, 'aligned_periods': 136.0}, calculation_notes: TRIX analysis based on 136 aligned periods with length=14

  vwap:
    Current: {'price': 105198.64, 'timestamp': '2025-10-17T14:56:15.173424+00:00', 'vwap_value': 105979.4568, 'price_distance': -780.8168, 'price_distance_pct': -0.737}
    Summary: VWAP 105979.4568, price below (-0.7%) - slightly undervalued
    Trend: strength: 0.152, velocity: -641.546805, direction: falling, smoothness: 0.955
    Anchored: momentum: -641.546805, reset_detected: False, behavior_quality: choppy, direction_consistency: 0.544
    Fair_Value: assessment: slightly_undervalued, distance_pct: -0.737, reversion_tendency: high
    Volatility: 840.9832
    Volume_Profile: volume_bias: below_vwap, avg_volume_above: 3207.86, avg_volume_below: 4156.84, near_vwap_volume_pct: 44.1, above_vwap_volume_pct: 44.9, below_vwap_volume_pct: 55.1, institutional_activity: high
    Price Position: {'bias': 'bearish', 'current': 'below', 'above_vwap_pct': 51.3, 'below_vwap_pct': 48.7, 'position_changes': 60.0}
    Deviation Bands: {'lower_1std': 105138.4735, 'lower_2std': 104297.4903, 'upper_1std': 106820.44, 'upper_2std': 107661.4232, 'current_position': 'within_1std', 'std_devs_from_vwap': -0.93}
    Patterns: volume_clustering, convergence_divergence
    Quality: data_quality: {'had_volumes': 1.0, 'aligned_periods': 150.0, 'volume_profile_available': 1.0, 'support_resistance_touches': 61.0}, calculation_notes: VWAP analysis based on 150 aligned price/VWAP periods

  aroon:
    Current: {'aroon_up': 7.14, 'timestamp': '2025-10-17T14:56:14.888026+00:00', 'aroon_down': 92.86, 'oscillator': -85.71}
    Summary: Aroon Up: 7.1, Down: 92.9 - strong_downtrend for 19 periods (strong bearish)
    Trend: separation: 85.71, current_trend: strong_downtrend, trend_quality: excellent, trend_duration: 19.0, trend_strength: 0.857, trend_consistency: 1.0
    Strength: up_momentum: -2.38, up_evolution: falling, down_momentum: 0.0, down_evolution: falling, aroon_up_strength: very_weak, combined_strength: very_strong, dominant_indicator: aroon_down, aroon_down_strength: very_strong
    Parallel_Movement: correlation: -0.111, movement_type: independent_movement, interpretation: Indicators moving independently
    Crossovers: {'latest_crossover': None, 'recent_crossovers': [], 'crossover_frequency': 'low'}
    Oscillator: {'zone': 'strong_bearish', 'velocity': -2.38, 'acceleration': -10.71, 'current_value': -85.71, 'zero_crossings': 5.0, 'time_above_zero_pct': 48.5, 'time_below_zero_pct': 50.7, 'oscillator_interpretation': 'strong_bearish_momentum'}
    Patterns: extreme_readings
    Quality: clarity: 0.86, consistency: 1.00, data_quality: 0.68

  vortex:
    Current: {'spread': -0.5073, 'vi_plus': 0.7334, 'dominant': 'VI-', 'vi_minus': 1.2407, 'timestamp': '2025-10-17T14:56:14.900068+00:00'}
    Summary: Vortex VI+ 0.733, VI- 1.241 - VI minus dominant (+0.507)
    Trend: strength: 0.11, velocity: -0.033273, direction: falling, acceleration: 0.03904
    Dominance: current: VI_minus, strength: 0.5073, persistence: 1.0
    Volatility: 0.4427
    One Line: {'recent_crosses': {'plus_crosses': [], 'minus_crosses': []}, 'vi_plus_vs_one': 'below', 'vi_minus_vs_one': 'above', 'plus_above_one_pct': 50.7, 'minus_above_one_pct': 52.2}
    Vi Crossovers: []
    Key Level Crosses: []
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'persistence': 5.0, 'crossover_scan': 14.0}, 'aligned_periods': 136.0}, calculation_notes: Vortex analysis based on 136 aligned VI+/VI- periods

  stochastic:
    Current: {'spread': -1.55, 'd_percent': 14.69, 'k_percent': 13.14, 'timestamp': '2025-10-17T14:56:14.751995+00:00'}
    Summary: Stochastic %K: 13.1, %D: 14.7 (oversold for 6 periods). Bearish Crossover 1p ago
    Trend: momentum: sideways_momentum, velocity: -0.4, k_direction: falling, acceleration: 5.25
    Volatility: 28.387
    Spread_Momentum: -2.57
    Neutral: {'bias': 'bearish', 'level': 50.0, 'distance_from_50': -36.86}
    Oversold: {'level': 20.0, 'status': 'in_zone', 'exit_analysis': {'latest_exit': {'strength': 0.34946516224893376, 'exit_level': 26.989303244978675, 'periods_ago': 8.0}, 'recent_exits': [{'strength': 0.34946516224893376, 'exit_level': 26.989303244978675, 'periods_ago': 8.0}]}, 'streak_length': 6.0, 'time_percentage': 18.0}
    Overbought: {'level': 80.0, 'status': 'below', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'time_percentage': 26.3}
    Patterns: squeeze
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'aligned_periods': 133.0, 'valid_data_percentage': 97.1}, calculation_notes: Stochastic analysis based on 133 aligned K/D periods

  williams_r:
    Current: {'value': -83.28, 'timestamp': '2025-10-17T14:56:14.756400+00:00'}
    Summary: Williams %R at -83.3 (oversold for 1 periods), strong upward acceleration
    Trend: strength: 0.013, velocity: 7.79, direction: sideways, acceleration: 3.374
    Momentum: volatility: 29.66, recent_range: 42.49, interpretation: strong_upward_acceleration
    Volatility: 29.659
    Neutral: {'bias': 'bearish', 'level': -50.0, 'distance_from_50': -33.28}
    Oversold: {'level': -80.0, 'status': 'in_zone', 'exit_analysis': {'latest_exit': {'strength': 0.07853772522804406, 'exit_level': -78.43, 'periods_ago': 2.0}, 'recent_exits': [{'strength': 0.07853772522804406, 'exit_level': -78.43, 'periods_ago': 2.0}, {'strength': 0.4144227893328619, 'exit_level': -71.71, 'periods_ago': 4.0}, {'strength': 1.0, 'exit_level': -56.37, 'periods_ago': 8.0}]}, 'streak_length': 1.0, 'time_percentage': 20.4}
    Overbought: {'level': -20.0, 'status': 'below', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'time_percentage': 27.7}
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'acceleration': 4.0, 'position_rank': 14.0}, 'aligned_periods': 137.0}, calculation_notes: Williams %R analysis based on 137 periods with length=14

  bollinger_bands:
    Current: {'lower': 105320.2678, 'upper': 114995.3512, 'middle': 110157.8095, 'bandwidth': 8.7829, 'percent_b': -0.0126}

=== 5M TIMEFRAME ===
  dc:
    Current: {'price': 105195.2, 'timestamp': '2025-10-17T14:56:22.856333+00:00', 'channel_width': 1623.1, 'lower_channel': 104540.1, 'upper_channel': 106163.2, 'middle_channel': 105351.65, 'price_position_pct': 40.4}
    Summary: Donchian: Price 105195.2000 (40.4%), Width 1623.1000
    Trend: strength: neutral, position_pct: 40.4, utilization_rating: medium, channel_utilization: 0.629
    Length: 20.0
    Consolidation: price_range: 0.0, price_range_pct: 0.0, width_threshold: 1421.7368, is_consolidation: False, breakout_potential: low, consolidation_periods: 0.0
    Position: {'position': 'middle_third', 'position_pct': 40.4, 'distance_to_lower': 655.1, 'distance_to_upper': 968.0, 'distance_to_middle': 156.45}
    Support Resistance: {'lower': {'breaks': 0.0, 'bounces': 1.0, 'touches': 3.0, 'bounce_rate': 0.333}, 'upper': {'breaks': 0.0, 'bounces': 1.0, 'touches': 2.0, 'bounce_rate': 0.5}, 'middle': {'breaks': 0.0, 'bounces': 5.0, 'touches': 10.0, 'bounce_rate': 0.5}}
    Patterns: breakouts, width_analysis, turtle_patterns
    Quality: data_quality: {'total_periods': 81.0, 'width_corrections': 0.0, 'valid_data_percentage': 81.0}, calculation_notes: Donchian analysis based on 81 aligned data points with period 20

  adx:
    Current: {'adx': 14.02, 'plus_di': 22.13, 'minus_di': 26.1, 'timestamp': '2025-10-17T14:56:22.816930+00:00'}
    Summary: ADX 14.0 - Weak or no trend with bearish bias (4.0)
    Description: Weak or no trend
    Strength_Value: 14.02
    Trend_Strength: weak
    Trend_Evolution: stable
    Directional_Bias: bearish
    Directional_Strength: 3.97
    Weak Threshold: 20.0
    Current Strength: weak
    Strong Threshold: 25.0
    Extreme Threshold: 60.0
    Very Strong Threshold: 40.0
    Patterns: di_patterns, extreme_levels

  atr:
    Current: {'value': 414.7888, 'timestamp': '2025-10-17T14:56:22.869195+00:00'}
    Summary: ATR 414.788800 - high volatility (95th percentile)
    Trend: strength: 0.085, velocity: -2.923554, direction: falling, consistency: 0.5, acceleration: -6.492134, interpretation: volatility_stable
    Breakout: breakout_setup: 0.0, squeeze_periods: 0.0, squeeze_detected: 0.0, expansion_potential: 0.0, recent_volatility_change_pct: 4.37
    Relative: regime: normal_volatility, comparisons: {'5p_avg': -1.24, '10p_avg': 1.69, '20p_avg': 8.23, '50p_avg': 12.95}, regime_ratio: 1.129
    Cycles: {'recent_peaks': 1.0, 'cycle_detected': 1.0, 'cycle_position': 'post_trough_expansion', 'recent_troughs': 3.0, 'avg_contraction_cycle': 33.0}
    Stop Loss: {'stop_levels': {'1.0x_atr': {'distance': 414.7888, 'long_stop': 104780.4112, 'short_stop': 105609.9888, 'distance_pct': 0.394}, '1.5x_atr': {'distance': 622.1832, 'long_stop': 104573.0168, 'short_stop': 105817.3832, 'distance_pct': 0.591}, '2.0x_atr': {'distance': 829.577601, 'long_stop': 104365.622399, 'short_stop': 106024.777601, 'distance_pct': 0.789}, '2.5x_atr': {'distance': 1036.972001, 'long_stop': 104158.227999, 'short_stop': 106232.172001, 'distance_pct': 0.986}, '3.0x_atr': {'distance': 1244.366401, 'long_stop': 103950.833599, 'short_stop': 106439.566401, 'distance_pct': 1.183}}, 'current_price': 105195.2, 'recommended_stop': {'distance': 1036.972001, 'long_stop': 104158.227999, 'short_stop': 106232.172001, 'distance_pct': 0.986}, 'recommended_multiplier': 2.5}
    Volatility: {'statistical': {'max': 434.556378, 'min': 296.537801, 'std': 34.248248, 'mean': 361.001687}, 'current_level': 'high', 'percentile_rank': 95.3, 'relative_to_mean': 14.9, 'relative_to_price_pct': 0.394}
    Quality: clarity: 1.00, consistency: 0.09, data_quality: 0.43

  bbw:
    Current: {'width': 1.3, 'timestamp': '2025-10-17T14:56:22.873795+00:00'}
    Summary: BB Width 1.30% - below average volatility (47th percentile)
    Trend: strength: 0.01, velocity: -0.007, direction: stable, acceleration: -0.144
    Breakout: potential: moderate, recent_change: -0.05, setup_quality: poor_setup, potential_score: 0.4, change_direction: contracting
    Expansion: cycle_stage: unclear, recent_peak: None, max_expansion: 1.3, recent_trough: None, cycle_position: unclear, expansion_peaks: 0.0, contraction_troughs: 0.0, avg_expansion_height: 1.3
    Cycles: {'total_cycles': 0.0, 'avg_cycle_length': None, 'expanding_time_pct': 45.7, 'contracting_time_pct': 54.3}
    Squeeze: {'is_squeeze': 0.0, 'squeeze_periods': 0.0, 'squeeze_quality': 'weak', 'squeeze_frequency': 0.136, 'squeeze_intensity': 0.0, 'squeeze_threshold': 0.84}
    Volatility: {'level': 'below_average', 'statistics': {'max': 3.14, 'min': 0.74, 'std': 0.68, 'mean': 1.52}, 'percentile_rank': 46.9, 'relative_to_mean': -14.53}
    Quality: clarity: 0.32, consistency: 0.01, data_quality: 0.41

  cci:
    Current: {'value': -41.09, 'timestamp': '2025-10-17T14:56:22.763194+00:00'}
    Summary: CCI at -41.1, strong rising acceleration
    Length: 20.0
    Momentum: velocity: 10.85, volatility: 105.33, acceleration: 3.64, recent_range: 231.48, trend_strength: 0.543, trend_direction: rising, momentum_interpretation: strong_rising_acceleration
    Zero_Line: zero_crossings: 10.0, current_position: below, distance_from_zero: 41.09, time_above_zero_pct: 35.8, time_below_zero_pct: 64.2
    Oversold: {'level': -100.0, 'status': 'above', 'exit_analysis': {'latest_exit': {'strength': 26.350671784897955, 'exit_level': -73.64932821510205, 'periods_ago': 4.0}, 'recent_exits': [{'strength': 26.350671784897955, 'exit_level': -73.64932821510205, 'periods_ago': 4.0}]}, 'streak_length': 0.0, 'extreme_reading': False, 'time_percentage': 24.7}
    Overbought: {'level': 100.0, 'status': 'below', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'extreme_reading': False, 'time_percentage': 9.9}
    Zone: neutral
    Neutral Bias: bearish
    Patterns: hook
    Quality: data_quality: {'total_periods': 81.0, 'recent_volatility': 78.595, 'valid_data_percentage': 81.0}, calculation_notes: CCI analysis based on 81 valid data points with period 20

  ema:
    Current: {'price': 105195.2, 'ema_value': 105324.832, 'timestamp': '2025-10-17T14:56:22.840953+00:00', 'price_distance': -129.632, 'price_distance_pct': -0.123}
    Summary: EMA 105324.8320 - falling trend, very_low responsiveness, price -0.1%
    Length: 20.0
    Responsiveness: avg_change: 38.44894, max_change: 121.994347, change_frequency: 0.15, direction_changes: 12.0, relative_volatility: 0.002986, responsiveness_score: 0.09, responsiveness_rating: very_low
    Signal_Quality: noise_level: low, signal_quality: low_frequency_high_reliability, recommended_use: Reliable for position trading, slower signals
    Trend: {'slope': 10.522422, 'strength': 0.223, 'consensus': 'falling', 'long_term': 'falling', 'short_term': 'sideways', 'consistency': 0.714, 'medium_term': 'sideways', 'acceleration': 52.393021}
    Price Relationship: {'distance': -129.632, 'position': 'below', 'avg_distance': -99.3179, 'distance_pct': -0.123, 'above_ema_pct': 40.7, 'below_ema_pct': 59.3, 'avg_distance_pct': -0.094}
    Support Resistance: {'success_rate': 0.465, 'effectiveness': 'medium', 'total_touches': 43.0, 'recent_bounces': [{'type': 'resistance_bounce', 'index': 68.0, 'strength': 0.0022933027433645605, 'periods_ago': 12.0}, {'type': 'resistance_bounce', 'index': 69.0, 'strength': 0.0036547990665534665, 'periods_ago': 11.0}, {'type': 'support_bounce', 'index': 77.0, 'strength': 0.004691729780697808, 'periods_ago': 3.0}], 'recent_touches': [{'index': 71.0, 'price': 105417.0, 'ema_value': 105529.05386238395, 'periods_ago': 9.0}, {'index': 72.0, 'price': 105355.1, 'ema_value': 105512.4868278712, 'periods_ago': 8.0}, {'index': 77.0, 'price': 105206.4, 'ema_value': 105293.26476171991, 'periods_ago': 3.0}, {'index': 79.0, 'price': 105400.0, 'ema_value': 105338.47750335802, 'periods_ago': 1.0}, {'index': 80.0, 'price': 105195.2, 'ema_value': 105324.83202684773, 'periods_ago': 0.0}], 'successful_bounces': 20.0}
    Patterns: crossovers
    Quality: data_quality: {'had_sma': 0.0, 'had_prices': 1.0, 'has_price_data': 1.0, 'aligned_periods': 81.0, 'has_sma_comparison': 0.0, 'original_ema_periods': 100.0, 'valid_data_percentage': 81.0}, calculation_notes: EMA analysis based on 81 aligned data points with period 20

  mfi:
    Current: {'value': 44.34, 'timestamp': '2025-10-17T14:56:22.771939+00:00'}
    Summary: MFI at 44.3, selling pressure
    Length: 14.0
    Position_Rank: percentile: 28.6, interpretation: below_average
    Zone: neutral
    Money Flow: {'pressure': 'selling', 'consistency': 0.5, 'flow_quality': 'low_quality_flow', 'cycle_analysis': {'cycle_detected': 0.0}, 'pressure_strength': 0.113, 'volume_confirmation': 'weak'}
    Patterns: momentum
    Quality: data_quality: {'had_prices': 1.0, 'original_periods': {'mfi': 100.0, 'prices': 100.0}, 'core_analysis_periods': 87.0, 'divergence_aligned_periods': 87.0}, calculation_notes: MFI analysis based on 87 core periods, divergence on 87 aligned periods

  obv:
    Current: {'value': 107.93, 'timestamp': '2025-10-17T14:56:22.875224+00:00'}
    Summary: OBV 108 - bearish trend (strong, 1.00), distribution detected
    Length: 14.0
    Relative: max_obv: 391.59, min_obv: -404.38, position: upper_range, position_percentile: 64.4
    Trend: {'strength': 1.0, 'velocity': 41.97, 'consensus': 'bearish', 'long_term': 'bearish', 'short_term': 'bearish', 'consistency': 0.667, 'medium_term': 'bullish'}
    Accumulation: {'overall_phase': 'distribution_phase', 'phase_strength': 'strong', 'timeframe_analysis': {'5p': {'score': 'strong_accumulation', 'change_pct': 1532.34}, '10p': {'score': 'strong_distribution', 'change_pct': -50.09}, '20p': {'score': 'strong_distribution', 'change_pct': -61.07}}}
    Patterns: flow, momentum
    Quality: data_quality: {'had_prices': 1.0, 'had_volumes': 1.0, 'cleaned_periods': 100.0, 'original_periods': {'obv': 100.0, 'prices': 100.0, 'volumes': 100.0}}, calculation_notes: OBV analysis based on 100 periods with length 14

  roc:
    Current: {'value': -0.006, 'timestamp': '2025-10-17T14:56:22.776370+00:00', 'value_pct': '-0.01%'}
    Summary: ROC -0.01% - very_weak negative momentum
    Trend: slope: 0.228, strength: 0.114, direction: rising, consistency: 0.506
    Length: 10.0
    Momentum: strength: 0.005798407434134198, direction: negative, evolution: stable, persistence: 1.0, strength_level: very_weak
    Velocity: velocity: 0.228, acceleration: 0.024, interpretation: stable_momentum
    Calculation_Periods: 90.0
    Extremes: {'condition': 'neutral', 'current_streak': 0.0, 'oversold_time_pct': 3.3, 'oversold_threshold': -1.25, 'overbought_time_pct': 8.9, 'overbought_threshold': 0.96, 'extreme_oversold_threshold': -2.9, 'extreme_overbought_threshold': 2.62}
    Zero Line: {'position': 'below_zero', 'above_zero_pct': 32.2, 'below_zero_pct': 67.8, 'recent_crosses': [], 'total_crossings': 12.0, 'crossing_frequency': 0.133}
    Patterns: double_pattern
    Quality: data_quality: {'had_prices': 1.0, 'clean_periods': 90.0, 'original_periods': 90.0, 'calculation_periods': 10.0, 'valid_data_percentage': 100.0}, calculation_notes: ROC analysis based on 90 periods with length=10

  rsi:
    Current: {'value': 47.49, 'timestamp': '2025-10-17T14:56:22.734912+00:00'}
    Summary: RSI at 47.5, rising
    Ma5: 47.72
    Ma10: 45.74
    Trend: strength: 0.108, velocity: -0.081, direction: rising, acceleration: -1.604
    Volatility: 12.905
    Neutral: {'level': 50.0, 'status': 'below', 'distance': -2.51}
    Oversold: {'level': 30.0, 'status': 'far_above', 'periods_in_zone': 0.0, 'time_percentage': 9.3}
    Overbought: {'level': 70.0, 'status': 'far_below', 'periods_in_zone': 0.0, 'time_percentage': 2.3}
    Quality: data_quality: {'total_periods': 86.0, 'recent_volatility': 5.667, 'valid_data_percentage': 86.0}, calculation_notes: RSI analysis based on 86 valid data points

  sma:
    Current: {'price': 105195.2, 'sma_value': 105394.765, 'timestamp': '2025-10-17T14:56:22.846014+00:00', 'price_distance': -199.565, 'price_distance_pct': -0.189}
    Summary: SMA 105394.7650 - sideways trend, price below (-0.2%)
    Slope: alignment: aligned, direction: downward, acceleration: 38.5025, long_term_slope: -11.084, short_term_slope: 11.708333, medium_term_slope: -1.534
    Trend: slope: -1.534, strength: 0.043, consensus: sideways, long_term: sideways, short_term: sideways, consistency: 0.778, medium_term: sideways
    Length: 20.0
    Quality: smoothness: 0.997, trend_clarity: 0.863, responsiveness: 0.037, overall_quality: 0.93
    Smoothing_Factor: 0.0952
    Current Level: 105394.765
    Trend Direction: sideways
    Price Relationship: {'distance': -199.565, 'position': 'below', 'distance_pct': -0.189, 'above_sma_pct': 33.3, 'below_sma_pct': 66.7, 'position_changes': 10, 'position_stability': 0.875}
    Support Resistance: {'success_rate': 0.357, 'effectiveness': 'medium', 'total_touches': 56.0, 'recent_bounces': [{'type': 'resistance_bounce', 'index': 68.0, 'strength': 0.0022933027433645605, 'periods_ago': 12.0}, {'type': 'resistance_bounce', 'index': 69.0, 'strength': 0.0036547990665534665, 'periods_ago': 11.0}, {'type': 'support_bounce', 'index': 77.0, 'strength': 0.004691729780697808, 'periods_ago': 3.0}], 'recent_touches': [{'index': 74.0, 'price': 105062.4, 'sma_value': 105440.005, 'periods_ago': 6.0}, {'index': 77.0, 'price': 105206.4, 'sma_value': 105359.63999999998, 'periods_ago': 3.0}, {'index': 78.0, 'price': 105700.0, 'sma_value': 105378.1, 'periods_ago': 2.0}, {'index': 79.0, 'price': 105400.0, 'sma_value': 105402.005, 'periods_ago': 1.0}, {'index': 80.0, 'price': 105195.2, 'sma_value': 105394.76500000001, 'periods_ago': 0.0}], 'successful_bounces': 20.0}
    Patterns: crossovers, slope_direction, trend_alignment
    Quality: data_quality: {'had_prices': 1.0, 'aligned_periods': 81.0, 'original_periods': 81.0, 'calculation_periods': 20.0, 'valid_data_percentage': 100.0}, calculation_notes: SMA analysis based on 81 periods with length=20

  macd:
    Current: {'macd': -75.8027, 'signal': -75.9451, 'histogram': 0.1424, 'timestamp': '2025-10-17T14:56:22.744542+00:00'}
    Summary: MACD rising trend with increasing momentum. Recent bullish_crossover 2p ago
    Histogram: {'acceleration': -2.0812, 'histogram_strength': 0.14242770712303354, 'momentum_direction': 'decreasing', 'zero_crossings_recent': 1.0}
    Zero Line: {'current_position': 'below', 'distance_from_zero': 75.8027, 'time_above_zero_pct': 47.8, 'time_below_zero_pct': 52.2}
    Patterns: crossovers
    Quality: data_quality: {'aligned_periods': 67.0, 'original_periods': {'macd': 100.0, 'prices': 100.0, 'signal': 100.0, 'histogram': 100.0}, 'valid_data_percentage': 67.0}, calculation_notes: MACD analysis based on 67 aligned data points
    Legacy Trend: bullish

  psar:
    Current: {'price': 105195.2, 'distance': -553.2, 'timestamp': '2025-10-17T14:56:22.833108+00:00', 'psar_value': 105748.4, 'distance_percentage': -0.526}
    Summary: PSAR 105748.4000 - bearish trend for 8 periods, 0.53% from price
    Trend: trend_periods: 8.0, trend_strength: 0.693, current_direction: bearish, trend_consistency: 0.8, strength_interpretation: strong
    Length: 14.0
    Distance: max_distance: 2314.3483, min_distance: -1693.1458, average_distance: -181.2615, current_absolute: -553.2, distance_volatility: 899.5061, current_relative_pct: -0.526, distance_interpretation: normal_distance
    Acceleration: velocity: -72.720591, acceleration: -42.928973, rate_of_change_5p: -0.292, acceleration_interpretation: accelerating_downward
    Calculation_Periods: 99.0
    Trend Direction: unknown
    Stop Distance Pct: 0.526
    Current Stop Level: 105748.4
    Patterns: clustering, signal_analysis
    Quality: stop_loss: {'stop_type': 'trailing_stop', 'performance': {'total_tests': 89.0, 'successful_stops': 68.0, 'effectiveness_rate': 0.764}, 'stop_distance': 553.2, 'recommendation': 'tight_stop', 'stop_distance_pct': 0.526, 'current_stop_level': 105748.4}, data_quality: {'aligned_periods': 99.0, 'had_high_low_data': 1.0, 'calculation_periods': 14.0}, calculation_notes: Parabolic SAR analysis based on 99 aligned periods

  trix:
    Current: {'trix': -0.012411, 'signal': 105195.2, 'histogram': -105195.212411, 'timestamp': '2025-10-17T14:56:22.806726+00:00'}
    Summary: TRIX -0.012411 - weak bearish momentum, histogram -105195.212411 (below zero)
    Trend: strength: 0.041, velocity: -4.3e-05, direction: sideways, acceleration: 0.003321
    Momentum: direction: bearish, persistence: 1.0, strength_level: weak
    Volatility: 0.02687
    Zero Line: {'position': 'below_zero', 'above_zero_pct': 40.7, 'below_zero_pct': 58.1, 'recent_crossings': [{'type': 'bearish_zero_cross', 'value': -0.000289, 'periods_ago': 8.0}]}
    Signal Line: {'latest_crossover': None, 'recent_crossovers': [], 'crossover_frequency': 0.0}
    Patterns: histogram_momentum
    Quality: data_quality: {'had_prices': 0.0, 'had_signal': 1.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'acceleration': 4.0, 'turning_points': 14.0}, 'aligned_periods': 86.0}, calculation_notes: TRIX analysis based on 86 aligned periods with length=14

  vwap:
    Current: {'price': 105195.2, 'timestamp': '2025-10-17T14:56:22.886028+00:00', 'vwap_value': 105444.2947, 'price_distance': -249.0947, 'price_distance_pct': -0.236}
    Summary: VWAP 105444.2947, price below - fairly valued
    Trend: strength: 0.006, velocity: 0.252392, direction: sideways, smoothness: 0.996
    Anchored: momentum: 0.252392, reset_detected: False, behavior_quality: stable, direction_consistency: 0.717
    Fair_Value: assessment: fairly_valued, distance_pct: -0.236, reversion_tendency: low
    Volatility: 550.6086
    Volume_Profile: volume_bias: below_vwap, avg_volume_above: 49.99, avg_volume_below: 45.74, near_vwap_volume_pct: 53.5, above_vwap_volume_pct: 28.8, below_vwap_volume_pct: 71.2, institutional_activity: high
    Price Position: {'bias': 'bearish', 'current': 'below', 'above_vwap_pct': 27.0, 'below_vwap_pct': 73.0, 'position_changes': 10.0}
    Deviation Bands: {'lower_1std': 104893.686, 'lower_2std': 104343.0774, 'upper_1std': 105994.9033, 'upper_2std': 106545.512, 'current_position': 'within_1std', 'std_devs_from_vwap': -0.45}
    Patterns: volume_clustering
    Quality: data_quality: {'had_volumes': 1.0, 'aligned_periods': 100.0, 'volume_profile_available': 1.0, 'support_resistance_touches': 34.0}, calculation_notes: VWAP analysis based on 100 aligned price/VWAP periods

  aroon:
    Current: {'aroon_up': 14.29, 'timestamp': '2025-10-17T14:56:22.791093+00:00', 'aroon_down': 71.43, 'oscillator': -57.14}
    Summary: Aroon Up: 14.3, Down: 71.4 - strong_downtrend for 6 periods (strong bearish)
    Trend: separation: 57.14, current_trend: strong_downtrend, trend_quality: poor, trend_duration: 6.0, trend_strength: 0.571, trend_consistency: 0.6
    Strength: up_momentum: -7.14, up_evolution: falling, down_momentum: -7.14, down_evolution: falling, aroon_up_strength: very_weak, combined_strength: strong, dominant_indicator: aroon_down, aroon_down_strength: strong
    Parallel_Movement: correlation: 0.203, movement_type: independent_movement, interpretation: Indicators moving independently
    Crossovers: {'latest_crossover': {'type': 'bearish_crossover', 'location': 'high_levels', 'strength': 50.0, 'up_value': 50.0, 'down_value': 100.0, 'periods_ago': 6.0}, 'recent_crossovers': [{'type': 'bearish_crossover', 'location': 'high_levels', 'strength': 50.0, 'up_value': 50.0, 'down_value': 100.0, 'periods_ago': 6.0}], 'crossover_frequency': 'low'}
    Oscillator: {'zone': 'strong_bearish', 'velocity': 0.0, 'acceleration': 53.57, 'current_value': -57.14, 'zero_crossings': 8.0, 'time_above_zero_pct': 38.4, 'time_below_zero_pct': 61.6, 'oscillator_interpretation': 'strong_bearish_slowing'}
    Quality: clarity: 0.57, consistency: 0.60, data_quality: 0.43

  vortex:
    Current: {'spread': 0.0033, 'vi_plus': 1.033, 'dominant': 'VI+', 'vi_minus': 1.0298, 'timestamp': '2025-10-17T14:56:22.794652+00:00'}
    Summary: Vortex VI+ 1.033, VI- 1.030 - VI plus dominant (+0.003), bullish crossover 2p ago
    Trend: strength: 0.104, velocity: 0.063691, direction: rising, acceleration: 0.059171
    Dominance: current: VI_plus, strength: 0.0033, persistence: 0.4
    Volatility: 0.3327
    One Line: {'recent_crosses': {'plus_crosses': [{'type': 'upward_cross', 'value': 1.0232, 'periods_ago': 9.0}, {'type': 'downward_cross', 'value': 0.9813, 'periods_ago': 11.0}, {'type': 'upward_cross', 'value': 1.0512, 'periods_ago': 13.0}], 'minus_crosses': [{'type': 'upward_cross', 'value': 1.0115, 'periods_ago': 7.0}]}, 'vi_plus_vs_one': 'above', 'vi_minus_vs_one': 'above', 'plus_above_one_pct': 33.7, 'minus_above_one_pct': 67.4}
    Vi Crossovers: [{'type': 'bullish_crossover', 'vi_plus': 1.0306, 'strength': 0.021, 'vi_minus': 1.0094, 'periods_ago': 2.0, 'crossover_level': 1.02}, {'type': 'bearish_crossover', 'vi_plus': 0.8896, 'strength': 0.192, 'vi_minus': 1.0813, 'periods_ago': 6.0, 'crossover_level': 0.9854}, {'type': 'bullish_crossover', 'vi_plus': 1.0232, 'strength': 0.055, 'vi_minus': 0.9686, 'periods_ago': 9.0, 'crossover_level': 0.9959}, {'type': 'bearish_crossover', 'vi_plus': 0.972, 'strength': 0.021, 'vi_minus': 0.9932, 'periods_ago': 10.0, 'crossover_level': 0.9826}]
    Key Level Crosses: [{'level': 1.0, 'strength': 0.03058583521101177, 'direction': 'up', 'periods_ago': 2.0}, {'level': 1.0, 'strength': 0.11038383324860457, 'direction': 'down', 'periods_ago': 6.0}, {'level': 1.0, 'strength': 0.023186380383686922, 'direction': 'up', 'periods_ago': 9.0}]
    Patterns: compression, parallel_movement
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'persistence': 5.0, 'crossover_scan': 14.0}, 'aligned_periods': 86.0}, calculation_notes: Vortex analysis based on 86 aligned VI+/VI- periods

  stochastic:
    Current: {'spread': 4.66, 'd_percent': 50.28, 'k_percent': 54.93, 'timestamp': '2025-10-17T14:56:22.750961+00:00'}
    Summary: Stochastic %K: 54.9, %D: 50.3. Bullish Crossover 4p ago
    Trend: momentum: strong_bullish_acceleration, velocity: 7.1, k_direction: rising, acceleration: 14.89
    Volatility: 24.269
    Spread_Momentum: -12.66
    Neutral: {'bias': 'bullish', 'level': 50.0, 'distance_from_50': 4.93}
    Oversold: {'level': 20.0, 'status': 'above', 'exit_analysis': {'latest_exit': {'strength': 1.0, 'exit_level': 40.73275419464791, 'periods_ago': 3.0}, 'recent_exits': [{'strength': 1.0, 'exit_level': 40.73275419464791, 'periods_ago': 3.0}]}, 'streak_length': 0.0, 'time_percentage': 19.3}
    Overbought: {'level': 80.0, 'status': 'below', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'time_percentage': 9.6}
    Patterns: momentum
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'aligned_periods': 83.0, 'valid_data_percentage': 95.4}, calculation_notes: Stochastic analysis based on 83 aligned K/D periods

  williams_r:
    Current: {'value': -59.64, 'timestamp': '2025-10-17T14:56:22.755349+00:00'}
    Summary: Williams %R at -59.6, strong downward acceleration
    Trend: strength: 0.173, velocity: -15.55, direction: rising, acceleration: -16.653
    Momentum: volatility: 27.06, recent_range: 69.23, interpretation: strong_downward_acceleration
    Volatility: 27.063
    Neutral: {'bias': 'bearish', 'level': -50.0, 'distance_from_50': -9.64}
    Oversold: {'level': -80.0, 'status': 'above', 'exit_analysis': {'latest_exit': {'strength': 1.0, 'exit_level': -58.95, 'periods_ago': 4.0}, 'recent_exits': [{'strength': 1.0, 'exit_level': -58.95, 'periods_ago': 4.0}]}, 'streak_length': 0.0, 'time_percentage': 21.8}
    Overbought: {'level': -20.0, 'status': 'below', 'exit_analysis': {'latest_exit': None, 'recent_exits': []}, 'streak_length': 0.0, 'time_percentage': 11.5}
    Patterns: momentum
    Quality: data_quality: {'had_prices': 1.0, 'period_used': 14.0, 'windows_used': {'velocity': 2.0, 'divergence': 14.0, 'acceleration': 4.0, 'position_rank': 14.0}, 'aligned_periods': 87.0}, calculation_notes: Williams %R analysis based on 87 periods with length=14

  bollinger_bands:
    Current: {'lower': 104711.6871, 'upper': 106077.8429, 'middle': 105394.765, 'bandwidth': 1.2962, 'percent_b': 0.3539}

Data Age: 58 seconds

## VOLUME CONFIRMATION ANALYSIS
Current volume analysis for trade confirmation:

Timeframe: 1h | Period: 35 candles
Current Volume: 1,819 (last completed 1h candle)
Average Volume: 1,596 (35-period average)
Volume Ratio: 1.14x | Above Average: +14.0%
Confirmation Level: Easy Confirmation - Entry with risk is possible

## YOUR TRADING STRATEGY
You are an autonomous crypto trading AI. Your goal: generate consistent profits by adapting to whatever the market gives you.

PHILOSOPHY:

Don't force specific strategies. Read the market conditions and respond intelligently. Sometimes the best move is aggressive trading, sometimes it's patient accumulation, sometimes it's doing nothing.​

YOUR APPROACH:

Analyze current market data using available indicators (MACD, RSI, Stochastic, Williams %R, ADX, EMA, SMA, Bollinger Bands, VWAP, ATR, etc). Based on what you observe, decide:

What type of market is this? (Trending, ranging, volatile, quiet)

What opportunity exists right now? (Momentum, reversal, breakout, consolidation)

What's the best action? (Long, short, wait, reduce risk)

How confident are you? (High confidence = normal size, low confidence = smaller or skip)

DECISION FRAMEWORK:

Look for confluence—when multiple signals agree, that's your edge. Don't rely on single indicators. Trust patterns that repeat, not one-time setups.​

Adapt your timeframe to conditions. Fast markets need quick decisions. Slow markets allow patience. Don't trade on fixed schedules—trade when opportunities appear.​

RISK PRINCIPLES:

Never risk more than you can afford to lose on any single trade. Position sizing should reflect both opportunity quality and current market volatility.​

Use stops always, but make them intelligent—too tight kills good trades, too loose bleeds capital. Let winners run when momentum continues, cut losers when the setup breaks.​

If you're losing, reduce size and frequency. If you're winning, maintain discipline—don't over-leverage success.​

EXECUTION:

Enter trades when you have clear reasoning. Exit when that reasoning changes or targets are hit. Don't hope, don't guess—follow what the data tells you.​

Monitor constantly but don't overtrade. Just because you can trade doesn't mean you should.​

OPTIMIZATION:

Review performance regularly. What's working? What's not? Adapt your approach as markets evolve. No strategy works forever—stay flexible.​

YOUR MANDATE:

Given current market data, determine: the market state, the best opportunity, the appropriate action, position size, entry point, stop loss, profit target, and confidence level.

Make money by being smarter and more adaptable than rigid systems. Think, analyze, execute, adjust, repeat.
In it for the memes

## TASK INSTRUCTIONS
You strictly apply the user's trading strategy below. Do not invent additional rules or override the strategy's logic. Do not reference indicators or data not provided in the market data above. If your strategy requires indicators not available, or if market data appears stale or incomplete, mention these issues in your reasoning.

Use your trading strategy above to analyze the provided market data and identify trading opportunities. If your strategy specifies certain timeframes or indicators, focus on that data while having full context of all timeframes available.

Based on your analysis:
- Is there a trading opportunity (long/short) or should you wait?
- How confident are you in this opportunity?
- What stop loss and take profit levels align with your strategy?

Your reasoning should cite specific indicator values from the market data that triggered your strategy's rules.

## OUTPUT FORMAT
ACTION: [long/short/wait]
CONFIDENCE: [0.000-1.000]
REASONING: [Explain how your strategy interprets the current market data and identifies this opportunity]
STOP_LOSS: [price or null]
TAKE_PROFIT: [price or null]