Here are the **20 highest-value pandas-ta indicators** I’d prioritize (broad coverage of trend, momentum, volatility, and volume; robust across assets/timeframes). For each, I note **how pros actually use it**, then exactly **what to engineer** so your models get signal, not just raw prints.

---

1. **RSI (Relative Strength Index)** — momentum/OB/OS + divergence. Pros watch 30/70 (or 20/80 in strong trends), failure swings, and divergence. ([Investopedia][1])
   **Preprocess features:**

* Current RSI; distance to 50 (bull/bear regime).
* Most recent RSI peak/trough value **and** bars since it occurred.
* Time since last cross of 30/70; count of consecutive bars >70 or <30.
* Bullish/bearish price–RSI divergence flag (last N swings).
* RSI slope/acceleration over 3–5 bars.

2. **MACD (12/26/9)** — momentum/trend; signal/zero-line crosses; histogram turns & divergence. ([Investopedia][2], [ChartSchool][3])
   **Preprocess features:**

* MACD–signal spread; last time it crossed zero.
* Histogram peak/trough age and size; first derivative sign change (early momentum shift).
* Divergence flag vs price on last two swing highs/lows.
* “Regime” (MACD>0 uptrend, <0 downtrend) duration in bars.

3. **Stochastic (%K/%D)** — range momentum; OB/OS 80/20; %K/%D crosses; divergence. ([Investopedia][4])
   **Preprocess features:**

* %K, %D and their spread; latest cross direction & bars since.
* Overbought/oversold streak length; exits from OB/OS.
* Divergence flag with price.
* %K position rank within last N bars (percentile).

4. **Bollinger Bands (20,2)** — volatility expansion/“walk the band”/squeezes. ([Investopedia][5])
   **Preprocess features:**

* %B and BandWidth; BandWidth z-score vs 6-month median (squeeze).
* Touch/close outside band count over last N bars.
* Breakout bar body% when exiting a squeeze; follow-through (1–3 bars).
* Price distance to middle band in ATRs.

5. **ATR (Average True Range)** — volatility sizing/stops; breakout context. ([Investopedia][6])
   **Preprocess features:**

* ATR and ATR% (ATR/close).
* ATR trend (rising/falling) over 14 bars.
* Volatility stop levels (close ± k\*ATR) and distance from price.
* “Volatility regime” bucket (e.g., ATR% quintile).

6. **ADX / DMI (+DI/−DI)** — trend strength & direction filters; >25 means real trend. ([Investopedia][7])
   **Preprocess features:**

* ADX value & slope; time spent >25 (or >40 for strong).
* +DI−−DI spread; last +DI/−DI cross & bars since.
* Composite “trend-quality” score: (ADX rising) AND (price making HH/HL or LL/LH).
* Whipsaw risk flag: low ADX (<20) + rangebound.

7. **MFI (Money Flow Index)** — RSI with volume; OB/OS 80/20; divergence. ([Investopedia][8])
   **Preprocess features:**

* MFI level; time since last 80/20 cross; streak above 80/below 20.
* MFI vs price divergence flag.
* “Confirmation” flag: price breakout + rising MFI over last N bars.

8. **OBV (On-Balance Volume)** — participation/accumulation; trend confirmation & divergence. ([ChartSchool][9], [Investopedia][10])
   **Preprocess features:**

* OBV slope over 10 bars; break of OBV trendline.
* Divergence with price at last swing high/low.
* OBV above/below its EMA; bars since cross.
* Volume-thrust event: max 3-day OBV change in 3 months.

9. **VWAP (and Anchored VWAP)** — intraday execution benchmark; dynamic S/R; anchored to events. ([Investopedia][11], [alphatrends.net][12])
   **Preprocess features:**

* Price–VWAP distance (bps) and z-score (session).
* Time above/below session VWAP; flips count.
* Anchored VWAPs from major swing highs/lows/earnings gaps; distance & confluence count.
* First touch/reject outcome stats after open.

10. **Supertrend** — ATR-based trend overlay; flips on volatility-adjusted breaks. ([Investopedia][13], [Zerodha][14])
    **Preprocess features:**

* Supertrend direction; bars since last flip; flip frequency last 60 bars.
* Price distance to line in ATRs; “near-flip” (<0.2 ATR).
* False-flip filter: require ADX>25 at flip (flag).
* Consecutive closes beyond line.

11. **Ichimoku Cloud** — full-stack trend/momentum/S-R: Tenkan/Kijun crosses, price vs cloud, Chikou confirmation, cloud twist. ([Investopedia][15])
    **Preprocess features:**

* Price vs cloud (above/inside/below) and cloud thickness (spans distance).
* Tenkan–Kijun cross direction/recency; “strong/weak” (relative to cloud).
* Chikou above/below price 26 back; confirmation flag.
* Future cloud twist within next N bars.

12. **EMA/SMA Crossovers (e.g., 50/200 “golden/death” cross)** — regime/confirmation. ([Investopedia][16])
    **Preprocess features:**

* Current cross state; bars since cross; slope of slow MA at cross.
* Price distance to each MA; “stacking” (fast>mid>slow).
* Pullback depth to rising MA (percent retracement).
* Failed cross flags (cross + immediate uncross ≤10 bars).

13. **Donchian Channels** — breakout/trend following (Turtle-style). ([Investopedia][17], [ChartSchool][18])
    **Preprocess features:**

* Distance to 20-bar high/low; days since new breakout.
* Breakout confirmation: close beyond band by >x% and rising volume.
* Post-breakout max adverse excursion to opposite band.
* “Channel squeeze” (upper-lower width in ATRs) percentile.

14. **Keltner Channels** — ATR-based envelopes; breakout + squeeze with BB. ([ChartSchool][19], [StockCharts][20])
    **Preprocess features:**

* Close vs upper/lower channel; time outside channel.
* KC width (in ATRs) vs median; BB-inside-KC squeeze flag & bars since “fired.”
* Breakout body% when clearing channel; follow-through return.

15. **Parabolic SAR** — trend trailing stops; flips indicate possible reversals; works best in trends. ([Investopedia][21])
    **Preprocess features:**

* Current SAR side; distance in ATRs; acceleration factor used.
* Bars since last flip; flip frequency (whipsaw risk).
* Whether price tagged SAR this bar; intrabar penetration flag.
* Confluence with MA/structure at flip (yes/no).

16. **CCI (Commodity Channel Index)** — mean-reversion extremes (+100/−100) & cycles. ([Investopedia][22])
    **Preprocess features:**

* CCI level; time outside ±100; re-entry events.
* Divergence with price; CCI cycle length via zero-cross spacing.
* CCI percentile vs 1-year distribution.

17. **ROC (Rate of Change / Momentum)** — zero-line crosses; extremes; divergence. ([ChartSchool][23])
    **Preprocess features:**

* ROC value; last zero cross & bars since.
* Max/min ROC in last N bars; mean-reversion distance to median.
* ROC vs return next k bars (rolling calibration feature).

18. **Aroon / Aroon Oscillator** — time-since-high/low; trend emergence/decay. ([ChartSchool][24])
    **Preprocess features:**

* Aroon Up/Down; oscillator value; time spent >+50 or <−50.
* “Fresh trend” flag: Aroon Up>90 with Down<10 (or inverse).
* Bars since last 25-period HH/LL (raw Donchian timing).

19. **Chaikin Money Flow (CMF)** — volume-weighted accumulation; confirm/deny trend strength. ([ChartSchool][25])
    **Preprocess features:**

* CMF level; streak above 0 (accumulation) or below 0 (distribution).
* Breakout + positive CMF confirmation flag.
* CMF divergence with price; CMF vs MFI agreement flag.

20. **Williams %R** — momentum extremes; responsive OB/OS; failure swings. ([Investopedia][26])
    **Preprocess features:**

* %R level; time in OB (>-20) / OS (<-80); first close back inside.
* Failure swing patterns (HH in price, lower high in %R, etc.).
* %R percentile vs last N bars; cross of −50 (momentum tilt).

---

### Why these 20?

They’re **battle-tested, complementary, and interpretable**: momentum (RSI, MACD, Stoch, %R, ROC), **trend** (ADX/DMI, MA crosses, Donchian, Ichimoku, Supertrend, PSAR), **volatility** (ATR, Bollinger, Keltner), and **volume/flow** (OBV, CMF, MFI, VWAP). That mix minimizes redundancy and overfitting while covering how pros actually decide: **trend present? momentum aligned? volatility regime? real participation?** (pandas-ta covers all of these). ([GitHub][27])

---

### Implementation notes (opinionated)

* **Always add recency & regime context** (bars since signal, how long in regime). Static values are near-useless.
* **Normalize distances in ATRs** so features transfer across assets.
* **Prefer event flags over thresholds** (e.g., “exited OB after 10-bar stay” beats “RSI=71”).
* **Divergence detection** (price vs momentum/volume) is high value if you anchor it to recent swing points, not every tick.
* **Squeeze → expansion** states (BB/KC/ATR) deserve first-class features; most big moves start there. ([ChartSchool][28])

If you want, I can generate **pandas-ta preprocessor code** that outputs exactly these fields in a tidy feature matrix for your pipeline.

[1]: https://www.investopedia.com/articles/active-trading/042114/overbought-or-oversold-use-relative-strength-index-find-out.asp?utm_source=chatgpt.com "RSI Indicator: Buy and Sell Signals"
[2]: https://www.investopedia.com/articles/forex/05/macddiverge.asp?utm_source=chatgpt.com "How to Trade the MACD"
[3]: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/macd-histogram?utm_source=chatgpt.com "MACD-Histogram - ChartSchool - StockCharts.com"
[4]: https://www.investopedia.com/articles/technical/073001.asp?utm_source=chatgpt.com "What Is the Stochastic Oscillator and How Is It Used?"
[5]: https://www.investopedia.com/terms/b/bollingerbands.asp?utm_source=chatgpt.com "Understanding Bollinger Bands: A Key Technical Analysis ..."
[6]: https://www.investopedia.com/terms/a/atr.asp?utm_source=chatgpt.com "Average True Range (ATR) Formula, What It Means, and ..."
[7]: https://www.investopedia.com/terms/d/dmi.asp?utm_source=chatgpt.com "Directional Movement Index (DMI) Formula, Calculations ..."
[8]: https://www.investopedia.com/terms/m/mfi.asp?utm_source=chatgpt.com "Money Flow Index (MFI): Definition and Uses - Investopedia"
[9]: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/on-balance-volume-obv?utm_source=chatgpt.com "On Balance Volume (OBV) - ChartSchool - StockCharts.com"
[10]: https://www.investopedia.com/articles/active-trading/021115/uncover-market-sentiment-onbalance-volume-obv.asp?utm_source=chatgpt.com "On-Balance Volume Reveals Market Player Strategy"
[11]: https://www.investopedia.com/terms/v/vwap.asp?utm_source=chatgpt.com "Volume-Weighted Average Price (VWAP): Definition and ..."
[12]: https://alphatrends.net/anchored-vwap/?utm_source=chatgpt.com "Anchored VWAP"
[13]: https://www.investopedia.com/supertrend-indicator-7976167?utm_source=chatgpt.com "Supertrend Indicator: What It Is and How It Works"
[14]: https://zerodha.com/varsity/chapter/supplementary-notes-1/?utm_source=chatgpt.com "Other indicators – Varsity by Zerodha"
[15]: https://www.investopedia.com/terms/i/ichimokuchart.asp?utm_source=chatgpt.com "Ichimoku Kinko Hyo Indicator & FIve Components Explained"
[16]: https://www.investopedia.com/ask/answers/121114/what-difference-between-golden-cross-and-death-cross-pattern.asp?utm_source=chatgpt.com "Golden Cross vs. Death Cross: What's the Difference?"
[17]: https://www.investopedia.com/terms/d/donchianchannels.asp?utm_source=chatgpt.com "Understanding Donchian Channels: Formula, Calculation, ..."
[18]: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/price-channels?utm_source=chatgpt.com "Price Channels - ChartSchool - StockCharts.com"
[19]: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/keltner-channels?utm_source=chatgpt.com "Keltner Channels - ChartSchool - StockCharts.com"
[20]: https://articles.stockcharts.com/article/articles-chartwatchers-2008-08-using-keltner-channels/?utm_source=chatgpt.com "USING KELTNER CHANNELS"
[21]: https://www.investopedia.com/trading/introduction-to-parabolic-sar/?utm_source=chatgpt.com "Introduction to the Parabolic SAR"
[22]: https://www.investopedia.com/investing/timing-trades-with-commodity-channel-index/?utm_source=chatgpt.com "Timing Trades With the Commodity Channel Index"
[23]: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/rate-of-change-roc?utm_source=chatgpt.com "Rate of Change (ROC) - ChartSchool - StockCharts.com"
[24]: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/aroon?utm_source=chatgpt.com "Aroon - ChartSchool - StockCharts.com"
[25]: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/chaikin-money-flow-cmf?utm_source=chatgpt.com "Chaikin Money Flow (CMF) - ChartSchool - StockCharts.com"
[26]: https://www.investopedia.com/terms/w/williamsr.asp?utm_source=chatgpt.com "Williams %R: Definition, Formula, Uses, and Limitations"
[27]: https://github.com/xgboosted/pandas-ta-classic?utm_source=chatgpt.com "xgboosted/pandas-ta-classic: Technical Analysis Indicators"
[28]: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/ttm-squeeze?utm_source=chatgpt.com "TTM Squeeze - ChartSchool - StockCharts.com"
