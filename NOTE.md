Strategy Advisor
Config Helper
Performance Overview
Win Rate

63.6%

Total P&L

$1382.11

R:R Ratio

1.17:1

Trades

44 (28W/16L)

Direction Breakdown
long
17 trades, 70.6% WR, $937.20
short
27 trades, 59.3% WR, $444.92
Critical Issues
Severe confidence miscalibration in high-conviction trades

Trades marked 70-75% confidence achieved only 33% win rate (expected 72%, gap: +39%), losing $123.04. Trades marked 75%+ confidence hit 0% win rate (expected 88%, gap: +88%), losing $264.97. Combined, these two confidence buckets represent $388.01 in losses despite being marked as high-conviction. This suggests the confidence scoring mechanism is fundamentally broken at higher thresholds.

Trend override exits destroying short trade profitability

16 trades using 'trend_override' exit logic achieved 0% win rate with -$1,320.24 P&L, representing 60% of all losses despite being only 36% of trades. This exit condition is consistently wrong and appears to be cutting winners or entering losers systematically.

Short trades significantly underperforming long trades

SHORT: 27 trades, 59% WR, $444.92 P&L ($16.48/trade). LONG: 17 trades, 71% WR, $937.20 P&L ($55.13/trade). Short positions generate 3.3x less profit per trade despite having more sample size. The bot's short signal generation or risk management is materially weaker than longs.

Positive Edges
Institutional activity patterns across multiple timeframes

Five separate pattern combinations all achieve 71% win rate: long + 15M/1H/30M/4H high_institutional_activity, each generating $937.20 P&L on 17 trades. This consistency across timeframes suggests institutional activity detection is a reliable signal that compounds well with other filters.

MACD falling confirmation on long entries

long_15M_macd_falling achieves 75% WR on 16 trades with $951.74 P&L. When combined with institutional activity, the pattern maintains 75% WR. This is the single best-performing filter and appears to validate entry timing.

Thesis complete and profit take exits working perfectly

Both 'thesis_complete' (14 trades, 100% WR, $1,682.08) and 'profit_take' (14 trades, 100% WR, $1,020.27) exits achieve perfect win rates. These represent the bot's only exits with no losing trades and account for 64% of all P&L ($2,702.35 of $3,402.35 gross wins).

Recommendations
Eliminate or completely rebuild confidence scoring above 70%

Current confidence model shows a severe accuracy cliff: 55-65% confidence buckets beat expectations (+/- 18% gap, 75-80% actual), but 70%+ confidence buckets fail dramatically (33% and 0% actual vs 72-88% expected). The calibration is inverted at high thresholds. Either: (A) cap confidence scores at 65% maximum and re-weight the model, (B) audit the high-confidence signal generation (likely noise), or (C) create a separate high-confidence model with different underlying logic.

Impact: Expected recovery of $388 in immediate losses and potential 2-3% improvement to overall win rate once confidence scores reflect actual accuracy.

Immediately disable trend_override exit condition

This exit has 0% accuracy across 16 trades and is the single largest performance drag (-$1,320.24). No exit condition should have zero wins. Replace all trend_override exits with either thesis_complete or profit_take logic, which both achieve 100% accuracy. If trend detection is needed, rebuild it from scratch with 10+ historical trades of validation before deployment.

Impact: Direct P&L improvement of ~$1,320 (95% of total losses) with zero downside risk, assuming thesis_complete/profit_take replacements maintain their current 100% accuracy.

Avoid short trades with timeframe conflicts or bearish divergences

Worst performing combinations are all short trades with conflicting signals: short + 15M_divergence + 4H_strong_bullish (6 trades, 50% WR, -$511.94) and short + 15M_divergence + 30M_strong_bullish (8 trades, 38% WR, -$502.54). Together these represent -$1,014.48 in losses. Additionally, shorts with 3+ timeframe bearish alignment (8 trades, 38% WR) underperform significantly. Create a gating rule: do not take short trades when 4H timeframe shows bullish signals or when divergences conflict with higher timeframe direction.

Impact: Could eliminate ~$1,000 in known bad setups and improve short trade win rate from 59% to estimated 65-68% by filtering out the worst 14-16 short trades per cohort.

Expand best pattern combination: shorts with 15M bullish + 4H accumulation

short + 15M_strong_bullish + 4H_accumulation achieves 82% WR on 11 trades with $1,018.46 P&L—the highest win rate in the dataset. This is counter-intuitive (short with bullish signals) but highly effective. This pattern likely represents mean-reversion opportunities where institutional accumulation on 4H creates resistance that 15M bullish moves fail to break. Investigate and increase position size or frequency on this specific combination.

Impact: Increasing allocation to this 82% WR pattern could add 1-2% to overall win rate and $150-250 in P&L per 44-trade cohort if sample size can be increased from 11 to 18-20 trades.

Best Pattern Combinations
short + 15M_strong_bullish + 4H_accumulation

11 trades, 81.8% WR, $1018.46

long + 15M_high_institutional_activity + 15M_macd_falling

16 trades, 75% WR, $951.74

long + 15M_macd_falling + 1H_high_institutional_activity

16 trades, 75% WR, $951.74

Patterns to Avoid
short + 15M_divergence + 4H_strong_bullish

6 trades, 50% WR, $-511.94

short + 15M_divergence + 30M_strong_bullish

8 trades, 37.5% WR, $-502.54

short + 15M_diverging_from_vwap + 4H_strong_bullish

3 trades, 33.3% WR, $-373.34