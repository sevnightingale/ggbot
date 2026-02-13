Performance Overview
Win Rate

35.3%

Total P&L

$4971.36

R:R Ratio

3.29:1

Trades

34 (12W/22L)

Direction Breakdown
short
13 trades, 61.5% WR, $5938.26
long
21 trades, 19% WR, $-966.90
Critical Issues
Long trades are systematically underperforming

LONG trades show only 19% WR across 21 trades with -$966.90 P&L, while SHORT trades achieve 62% WR across 13 trades with +$5938.26 P&L. The bot is losing $46/trade on LONGs but gaining $457/trade on SHORTs. This directional bias is the primary performance drag.

Confidence calibration is severely miscalibrated

At higher confidence levels, actual win rates significantly underperform expectations: 70-75% confidence shows 33% actual vs 72% expected (-39% gap, -$883.72 P&L), and 75%+ shows 50% actual vs 88% expected (-38% gap). The model is most overconfident precisely when it should be most reliable.

Trend override exits show 0% win rate across 15 trades

Trades exited due to 'trend_override' have generated -$3,421.80 across 15 trades with 0% win rate. This is a consistent loss pattern suggesting either (a) the trend override signal is triggering too early on pullbacks, or (b) it's being applied to fundamentally bad setups.

Positive Edges
Short trades with strong bearish confluence are highly profitable

Three pattern combinations all show 100% WR across 7 trades with +$6,983.78 P&L each: (short + 1H_high_institutional_activity + 1H_strong_falling_momentum), (short + 1H_oversold + 1H_strong_falling_momentum), and (short + 1H_strong_bearish + 1H_strong_falling_momentum). These represent the bot's most reliable setups.

Risk/reward ratio supports holding through volatility

The 3.29 R:R ratio (avg win $937.36 vs avg loss $285.31) means winners are 3.3x larger than losers. With breakeven at 23.3%, only 30% win rate would be profitable. Current 35.3% WR generates $4,971.36 profit despite directional issues, suggesting good trade sizing and TP/SL discipline.

SHORT trades perform consistently across multiple timeframes

Top 5 SHORT confirmation patterns all exceed 75% WR: short_1H_strong_falling_momentum (88% WR, $6,858.74), short_5M_distribution (83% WR, $6,760.53), short_5M_strong_bearish (78% WR, $6,665.76), short_15M_distribution (75% WR, $6,495.63), and short_1H_bearish_xover (78% WR, $6,469.79). This demonstrates a robust SHORT edge across multiple setups.

Recommendations
Eliminate or pause LONG trades immediately

With 19% WR and -$966.90 P&L across 21 LONG trades versus 62% WR and +$5,938.26 for SHORTs, the directional bias is unsustainable. Every worst pattern combination involves LONG setups (e.g., long + 15M_high_institutional_activity + 5M_bearish_xover: 0% WR, -$4,248.89). Consider restricting to SHORT-only trading or requiring extreme additional confluence for LONGs.

Impact: Expected improvement: +$1,000-1,500 P&L, +20-25% overall win rate improvement to 55-60% range.

Recalibrate confidence scoring model

Apply a systematic confidence penalty or recalibrate expected win rates downward, especially above 70% confidence where actual performance lags expectations by 38-39%. Consider using a calibration factor (e.g., multiply high-confidence expectations by 0.65-0.75) or require additional confirmation signals at higher confidence levels before entry.

Impact: Prevent $1,500-2,000 in losses from false high-confidence signals and improve capital preservation for confirmed high-quality setups.

Investigate and refine trend override exit logic

The 15 'trend_override' exits with 0% WR and -$3,421.80 represent a systematic leakage pattern. Analyze recent exits to determine if: (a) trend override signals are triggering on normal pullbacks in strong trends, (b) it's being applied to weak setups that should never have been entered, or (c) the signal timing is off. Consider replacing with volatility-based stops or removing entirely for SHORT trades with institutional activity confluence.

Impact: Recovering $228/trade average from trend override losses could add $3,000-3,500 to annual P&L.

Concentrate on 1H timeframe SHORT patterns with institutional signals

The three 100% WR combinations all feature: (short direction) + (1H timeframe) + (institutional activity OR oversold OR strong bearish + strong falling momentum). These seven-trade clusters represent optimal setup geometry. Build the strategy around requiring institutional activity confirmation on the 1H timeframe before SHORT entry.

Impact: Expected win rate of 85%+ on concentrated entries, with higher average win size through reduced false signals and better risk/reward management.

Best Pattern Combinations
short + 1H_high_institutional_activity + 1H_strong_falling_momentum

7 trades, 100% WR, $6983.78

short + 1H_oversold + 1H_strong_falling_momentum

7 trades, 100% WR, $6983.78

short + 1H_strong_bearish + 1H_strong_falling_momentum

7 trades, 100% WR, $6983.78

Patterns to Avoid
long + 15M_high_institutional_activity + 5M_bearish_xover

11 trades, 0% WR, $-4248.89

long + 30M_high_institutional_activity + 5M_bearish_xover

11 trades, 0% WR, $-4248.89

long + 15M_tight_clustering + 5M_bearish_xover

10 trades, 0% WR, $-4237.15