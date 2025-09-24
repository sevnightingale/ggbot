CONTEXT
When evaluating the ggShot signal provided in the External Signal section, use the 3 pillar, timeframe aware, dynamic confidence scoring strategy and framework outlined below.

If any data point is 'null' or 'N/A' due to a calculation failure, explicitly note the missing data in your REASONING output and proceed with analysis based on remaining indicators.

Using the market data analysis provided above, focus on these key indicators:
Regime: Aroon BBWidth TRIX ADX MACD zero line and histogram momentum
Risks and Context: RSI Donchian PercentB ATR SMA EMA price distance pct
Confirmation: Volume on signal TF 30 period average last completed candle VWAP Vortex MFI

TIMEFRAME GUIDANCE
The provided ggShot signal includes a specific timeframe T
Prioritize T when assessing market data and building confidence especially for confirmation metrics volume VWAP Vortex MFI
Use higher timeframes than T to assess market regime trend versus range and momentum quality Prefer 1h 4h and 1d as available for regime context Very low TF regimes for example 5m are not reliable for regime
Lower timeframes than T may be skimmed for micro structure only They do not drive regime or major confidence adjustments

CONFIDENCE CONSTRUCTION anchor and adjust bounded
Follow this order strictly:
1. Select baseline from Pillar 1.
2. Add/subtract Pillar 2 (cap |0.20|).
3. Add/subtract Pillar 3 (cap |0.25|).
4. Subtract red flags (cap 0.15).
5. Apply data quality penalties.
6. Clamp to 0.05-0.95.
Cite the exact values and timeframes used. Be decisive; do not rationalize weak signals. Respect red flags without overrides.

PILLAR 1 MARKET REGIME baseline
Goal Determine if the broader environment is trend friendly for the signals direction
Inputs Aroon BBWidth bandwidth TRIX slope ADX strength direction MACD zero line position and histogram momentum
Focus on higher TFs to judge regime and optionally reference T for timing Choose one band and justify it with values and TFs
0.60 to 0.70 clear trend with signal at least two of Aroon trend align TRIX rising ADX strong or developing MACD above zero with increasing histogram BBWidth at or above median
0.50 to 0.60 trend present but mixed quality one or two warn
0.35 to 0.45 ranging or low momentum Aroon range BBWidth weak TRIX flat or down MACD at or below zero with weakening histogram
0.25 to 0.35 counter trend Aroon or TRIX against MACD below zero while signal is long or the reverse
Flag missing or stale regime inputs or low data quality or low data quality

PILLAR 2 RISKS AND CONTEXT adjustment cap 0.20
Goal Avoid chasing extension ensure room to run and sane volatility
Inputs RSI on T plus nearby higher TFs Donchian on T PercentB on T ATR on T SMA EMA price distance pct on T
Redundancy guard RSI PercentB Donchian room and SMA EMA distance all measure extension In a single decision apply only the single strongest effect from this group do not double count
Adjustment guide pick within ranges and cite values
Supportive momentum without extremes and adequate room to opposite structure or band plus 0.04 to plus 0.10
Mixed or mild extension on any used TF minus 0.02 to minus 0.06
Severe extension against the signal for example PercentB near the wrong band RSI extreme tiny Donchian room or large SMA EMA distance minus 0.06 to minus 0.12
ATR high relative to its distribution unless explicitly a breakout continuation thesis minus 0.02 to minus 0.05
Flag missing or stale inputs when relevant

PILLAR 3 CONFIRMATION adjustment cap 0.25
Goal Demand real participation in the signals direction
Inputs Volume on T versus 30 period average last completed candle VWAP side Vortex on T MFI on T
Adjustment guide cite actual ratios and values
Volume greater than or equal to 100 percent above average plus 0.12 to plus 0.20
Volume 30 percent to 100 percent above average plus 0.05 to plus 0.12
Volume more than 25 percent below average minus 0.08 to minus 0.15
VWAP favorable side by more than 1 percent plus 0.02 to plus 0.04 unfavorable by more than 1 percent minus 0.02 to minus 0.04
Vortex aligned VI plus greater than VI minus for longs reverse for shorts plus 0.01 to plus 0.03 misaligned minus 0.01 to minus 0.03
MFI divergence about 20 points or more against direction minus 0.05 to minus 0.10
Flag missing or stale inputs when relevant

RED FLAGS apply after Pillar 3 cap 0.15 total
Counter trend regime plus weak volume for example less than 0.75 times average minus 0.06 to minus 0.10
RSI T extreme or PercentB extreme against direction or SMA EMA extreme distance minus 0.04 to minus 0.08
ATR spike plus extension combo minus 0.05 to minus 0.08
If three or more red flags are present treat this as a high risk setup and reflect that in confidence and narrative

STOPS AND TAKE PROFIT consistent and data driven
STOP LOSS Prefer ATR recommended stop on T when provided otherwise use 1.0 to 1.5 times ATR T or nearest swing or Donchian mid mirror for shorts
TAKE PROFIT Stage at 1R and 2R and near the opposite band or structure once at least 1R trail by about 1.0 times ATR T
RR sanity If the nearest logical TP yields RR less than 1.2 treat this as a lower quality setup and reflect that in confidence

DATA QUALITY AND FRESHNESS
Use only the timeframes you referenced in your reasoning For any required indicator on those TFs if valid data percentage is less than 85 percent apply a small penalty for example 0.03 to 0.06 and clearly flag the issue in the reasoning Also flag any stale or missing pieces clearly







● Confidence Scoring Simulation Analysis

  Scoring Formula Recap:

  1. Pillar 1 (Regime): 0.25-0.70 baseline
  2. Pillar 2 (Risk): ±0.20 max adjustment
  3. Pillar 3 (Confirmation): ±0.25 max adjustment
  4. Red Flags: -0.15 max penalty
  5. Data Quality: -0.03 to -0.06 penalties
  6. Final Clamp: 0.05-0.95

  ---
  Scenario Simulations:

  🟢 EXCELLENT SIGNAL (High Confidence)

  - Pillar 1: 0.65 (clear trend, Aroon+TRIX+ADX aligned, MACD above zero)
  - Pillar 2: +0.08 (supportive momentum, good room to run)
  - Pillar 3: +0.18 (volume 150% above average, VWAP favorable, Vortex aligned)
  - Red Flags: 0 (none present)
  - Data Quality: -0.02 (minor data gaps)
  - Final Score: 0.65 + 0.08 + 0.18 - 0.02 = 0.89

  🟡 DECENT SIGNAL (Moderate Confidence)

  - Pillar 1: 0.55 (trend present but mixed quality)
  - Pillar 2: -0.04 (mild extension on one timeframe)
  - Pillar 3: +0.08 (volume 60% above average, VWAP neutral)
  - Red Flags: -0.05 (one flag: ATR spike)
  - Data Quality: 0 (good data)
  - Final Score: 0.55 - 0.04 + 0.08 - 0.05 = 0.54

  🔴 POOR SIGNAL (Low Confidence)

  - Pillar 1: 0.30 (counter-trend regime)
  - Pillar 2: -0.10 (severe extension, RSI extreme)
  - Pillar 3: -0.12 (volume 30% below average)
  - Red Flags: -0.12 (multiple flags: counter-trend + weak volume + extension)
  - Data Quality: -0.04 (stale regime data)
  - Final Score: 0.30 - 0.10 - 0.12 - 0.12 - 0.04 = 0.05 (clamped)

  ⚠️ MIXED SIGNAL (Borderline)

  - Pillar 1: 0.40 (ranging/low momentum)
  - Pillar 2: +0.06 (adequate room, no extension)
  - Pillar 3: +0.15 (good volume, favorable VWAP)
  - Red Flags: -0.06 (weak regime + extension combo)
  - Data Quality: -0.03 (minor gaps)
  - Final Score: 0.40 + 0.06 + 0.15 - 0.06 - 0.03 = 0.52

  ---
  Distribution Analysis:

  Expected Score Ranges:

  - 0.05-0.25: Red zone (avoid/reject) - ~15%
  - 0.25-0.45: Caution zone (low confidence) - ~25%
  - 0.45-0.65: Moderate zone (acceptable) - ~40%
  - 0.65-0.85: Strong zone (preferred) - ~18%
  - 0.85-0.95: Exceptional zone (rare) - ~2%

  Key Observations:

  1. Natural Centering: The 0.25-0.70 baseline creates a natural center around 0.47
  2. Adjustment Balance: ±0.45 total possible adjustments (0.20+0.25) vs. baseline
  range (0.45)
  3. Red Flag Impact: -0.15 max penalty can significantly downgrade signals
  4. Quality Gates: Data penalties provide important safety nets

  Behavioral Implications:

  High Standards: Most signals will score 0.45-0.65, with exceptional signals rare
  Red Flag Power: Multiple red flags can tank even decent regimes
  Volume Criticality: Pillar 3 has highest adjustment range (±0.25)
  Regime Foundation: Poor regime (0.25-0.35) very hard to rescue

  This framework should produce a conservative, quality-focused distribution that
  heavily penalizes weak setups while rewarding genuinely strong confluence.






















  {"bots": [{"config_id": "e5b43a4b-7446-43cd-bd01-3fe6eb0357b2", "user_id": "00000000-0000-0000-0000-000000000000", "config_name": "ggSignals", "config_type": "autonomous_trading", "state": "active", "config_data": {"schema_version": "2.1", "config_type": null, "selected_pair": "BTC/USDT", "extraction": {"selected_data_sources": {"technical_analysis": {"timeframes": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"], "data_points": ["Aroon", "BBW", "TRIX", "ADX", "MACD", "RSI", "DC", "BB", "ATR", "SMA", "EMA", "VWAP", "Vortex", "MFI"]}, "signals_group_chats": {"timeframes": ["15m"], "data_points": ["ggshot"]}}}, "decision": {"user_prompt": "CONTEXT\nWhen evaluating the ggShot signal provided in the External Signal section, use the 3 pillar, timeframe aware, dynamic confidence scoring strategy and framework outlined below.\n\nIf any data point is 'null' or 'N/A' due to a calculation failure, explicitly note the missing data in your REASONING output and proceed with analysis based on remaining indicators.\n\nUsing the market data analysis provided above, focus on these key indicators:\nRegime: Aroon BBWidth TRIX ADX MACD zero line and histogram momentum\nRisks and Context: RSI Donchian PercentB ATR SMA EMA price distance pct\nConfirmation: Volume on signal TF 30 period average last completed candle VWAP Vortex MFI\n\nTIMEFRAME GUIDANCE\nThe provided ggShot signal includes a specific timeframe T\nPrioritize T when assessing market data and building confidence especially for confirmation metrics volume VWAP Vortex MFI\nUse higher timeframes than T to assess market regime trend versus range and momentum quality Prefer 1h 4h and 1d as available for regime context Very low TF regimes for example 5m are not reliable for regime\nLower timeframes than T may be skimmed for micro structure only They do not drive regime or major confidence adjustments\n\nCONFIDENCE CONSTRUCTION anchor and adjust bounded\nFollow this order strictly:\n1. Select baseline from Pillar 1.\n2. Add/subtract Pillar 2 (cap |0.20|).\n3. Add/subtract Pillar 3 (cap |0.25|).\n4. Subtract red flags (cap 0.15).\n5. Apply data quality penalties.\n6. Clamp to 0.05-0.95.\nCite the exact values and timeframes used. Be decisive; do not rationalize weak signals. Respect red flags without overrides.\n\nPILLAR 1 MARKET REGIME baseline\nGoal Determine if the broader environment is trend friendly for the signals direction\nInputs Aroon BBWidth bandwidth TRIX slope ADX strength direction MACD zero line position and histogram momentum\nFocus on higher TFs to judge regime and optionally reference T for timing Choose one band and justify it with values and TFs\n0.60 to 0.70 clear trend with signal at least two of Aroon trend align TRIX rising ADX strong or developing MACD above zero with increasing histogram BBWidth at or above median\n0.50 to 0.60 trend present but mixed quality one or two warn\n0.35 to 0.45 ranging or low momentum Aroon range BBWidth weak TRIX flat or down MACD at or below zero with weakening histogram\n0.25 to 0.35 counter trend Aroon or TRIX against MACD below zero while signal is long or the reverse\nFlag missing or stale regime inputs or low data quality or low data quality\n\nPILLAR 2 RISKS AND CONTEXT adjustment cap 0.20\nGoal Avoid chasing extension ensure room to run and sane volatility\nInputs RSI on T plus nearby higher TFs Donchian on T PercentB on T ATR on T SMA EMA price distance pct on T\nRedundancy guard RSI PercentB Donchian room and SMA EMA distance all measure extension In a single decision apply only the single strongest effect from this group do not double count\nAdjustment guide pick within ranges and cite values\nSupportive momentum without extremes and adequate room to opposite structure or band plus 0.04 to plus 0.10\nMixed or mild extension on any used TF minus 0.02 to minus 0.06\nSevere extension against the signal for example PercentB near the wrong band RSI extreme tiny Donchian room or large SMA EMA distance minus 0.06 to minus 0.12\nATR high relative to its distribution unless explicitly a breakout continuation thesis minus 0.02 to minus 0.05\nFlag missing or stale inputs when relevant\n\nPILLAR 3 CONFIRMATION adjustment cap 0.25\nGoal Demand real participation in the signals direction\nInputs Volume on T versus 30 period average last completed candle VWAP side Vortex on T MFI on T\nAdjustment guide cite actual ratios and values\nVolume greater than or equal to 100 percent above average plus 0.12 to plus 0.20\nVolume 30 percent to 100 percent above average plus 0.05 to plus 0.12\nVolume more than 25 percent below average minus 0.08 to minus 0.15\nVWAP favorable side by more than 1 percent plus 0.02 to plus 0.04 unfavorable by more than 1 percent minus 0.02 to minus 0.04\nVortex aligned VI plus greater than VI minus for longs reverse for shorts plus 0.01 to plus 0.03 misaligned minus 0.01 to minus 0.03\nMFI divergence about 20 points or more against direction minus 0.05 to minus 0.10\nFlag missing or stale inputs when relevant\n\nRED FLAGS apply after Pillar 3 cap 0.15 total\nCounter trend regime plus weak volume for example less than 0.75 times average minus 0.06 to minus 0.10\nRSI T extreme or PercentB extreme against direction or SMA EMA extreme distance minus 0.04 to minus 0.08\nATR spike plus extension combo minus 0.05 to minus 0.08\nIf three or more red flags are present treat this as a high risk setup and reflect that in confidence and narrative\n\nSTOPS AND TAKE PROFIT consistent and data driven\nSTOP LOSS Prefer ATR recommended stop on T when provided otherwise use 1.0 to 1.5 times ATR T or nearest swing or Donchian mid mirror for shorts\nTAKE PROFIT Stage at 1R and 2R and near the opposite band or structure once at least 1R trail by about 1.0 times ATR T\nRR sanity If the nearest logical TP yields RR less than 1.2 treat this as a lower quality setup and reflect that in confidence\n\nDATA QUALITY AND FRESHNESS\nUse only the timeframes you referenced in your reasoning For any required indicator on those TFs if valid data percentage is less than 85 percent apply a small penalty for example 0.03 to 0.06 and clearly flag the issue in the reasoning Also flag any stale or missing pieces clearly", "system_prompt": "You are an expert cryptocurrency trader. Analyze the provided market data and provide clear, reasoned responses about trading actions. Format your response with clear sections for Decision, Confidence, and Reasoning.", "analysis_frequency": "signal_driven"}, "trading": {"leverage": 5, "execution_mode": "paper", "exchange_config": {"api_key": "", "secret_key": "", "exchange_type": "cex", "selected_exchange": "binance"}, "position_sizing": {"method": "fixed_usd", "account_percent": 5, "fixed_amount_usd": 100, "max_position_percent": 10}, "risk_management": {"max_positions": 1, "max_daily_loss_usd": 500, "default_stop_loss_percent": 5, "default_take_profit_percent": 10}}, "llm_config": {"model": "default", "provider": "default", "use_own_key": false, "use_platform_keys": true}, "telegram_integration": {"publisher": {"enabled": true, "bot_token": "7320956370:AAGMatLFf_myZxmfuN7v7EwToxBter_GHW0", "filter_channel": "-1002949374924", "message_template": "\ud83d\udd25 {ACTION} {SYMBOL} - Confidence: {CONFIDENCE}\n{REASONING}", "include_reasoning": true, "confidence_threshold": 0.7, "include_market_context": true}}}, "created_at": "2025-09-22T02:31:14.515431+00:00", "updated_at": "2025-09-23T05:38:49.38861+00:00", "execution_status": null, "status_color": "green", "status_message": "Monitoring markets and waiting for next analysis...", "show_spinner": false, "next_run": "2025-09-24T19:00:30Z", "is_scheduled": true}, {"config_id": "497380a9-eaba-4d87-8f20-6bb2ae1c1dac", "user_id": "00000000-0000-0000-0000-000000000000", "config_name": "Sev's ggbot", "config_type": "autonomous_trading", "state": "inactive", "config_data": {"schema_version": "2.1", "config_type": null, "selected_pair": "BTC/USDT", "extraction": {"selected_data_sources": {"technical_analysis": {"timeframes": ["1h"], "data_points": ["RSI"]}}}, "decision": {"user_prompt": "if RSI 1hr below 50 enter long, if above enter short", "system_prompt": "You are an expert cryptocurrency trader. Analyze the provided market data and provide clear, reasoned responses about trading actions. Format your response with clear sections for Decision, Confidence, and Reasoning.", "analysis_frequency": "1h"}, "trading": {"leverage": 1, "execution_mode": "paper", "exchange_config": {"api_key": "", "secret_key": "", "exchange_type": "cex", "selected_exchange": "binance"}, "position_sizing": {"method": "fixed_usd", "account_percent": 5, "fixed_amount_usd": 100, "max_position_percent": 10}, "risk_management": {"max_positions": 1, "max_daily_loss_usd": 500, "default_stop_loss_percent": 5, "default_take_profit_percent": 10}}, "llm_config": {"model": "default", "provider": "default", "use_own_key": false, "use_platform_keys": true}, "telegram_integration": {}}, "created_at": "2025-09-23T06:28:12.783418+00:00", "updated_at": "2025-09-23T06:33:20.075403+00:00", "execution_status": null, "status_color": "gray", "status_message": "Bot inactive", "show_spinner": false, "next_run": null, "is_scheduled": false}], "positions": [], "decisions": [], "accounts": [{"config_id": "e5b43a4b-7446-43cd-bd01-3fe6eb0357b2", "account_id": "eeac97bf-721b-4de4-94a5-796199754f46", "current_balance": 9800.57541792, "total_pnl": 0.75541792, "total_trades": 1, "win_trades": 1, "loss_trades": 0, "open_positions": 2, "updated_at": "2025-09-23T19:37:15.07038+00:00", "unrealized_pnl": 0.0, "daily_pnl": 0.75541792, "portfolio_return_pct": 0.0075541791999999995, "total_balance": 9800.57541792, "available_balance": 9800.57541792, "position_value": 0.0, "win_rate": 100.0, "avg_win": 0.75541792, "avg_loss": 0, "largest_win": 0.75541792, "largest_loss": 0, "sharpe_ratio": null}, {"config_id": "497380a9-eaba-4d87-8f20-6bb2ae1c1dac", "account_id": "b10fb816-97f7-41d0-b3ff-62ec66e2bbbc", "current_balance": 10000.0, "total_pnl": 0.0, "total_trades": 0, "win_trades": 0, "loss_trades": 0, "open_positions": 0, "updated_at": "2025-09-23T06:28:12.977826+00:00", "unrealized_pnl": 0.0, "daily_pnl": 0.0, "portfolio_return_pct": 0.0, "total_balance": 10000.0, "available_balance": 10000.0, "position_value": 0.0, "win_rate": 0, "avg_win": 0, "avg_loss": 0, "largest_win": 0, "largest_loss": 0, "sharpe_ratio": null}], "timestamp": "2025-09-24T18:34:44.847367+00:00"}