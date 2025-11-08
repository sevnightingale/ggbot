2025-11-08 17:14:13.352 | INFO     | __main__:__init__:75 - Initializing TradingAgent: config_id=bb2560fd-b053-464f-8a58-8e254e4d36fa, mode=strategy_definition
2025-11-08 17:14:13.446 | INFO     | agent.service_client:__init__:50 - Initialized GGBotAPIClient for user 00000000-0000-0000-0000-000000000000, base_url: http://localhost:8000
2025-11-08 17:14:13.480 | INFO     | agent.mcp_server:set_agent_context:74 - Agent context set: config_id=bb2560fd-b053-464f-8a58-8e254e4d36fa, user_id=00000000-0000-0000-0000-000000000000, trading_mode=aster
2025-11-08 17:14:13.480 | INFO     | __main__:initialize:94 - Agent initialized successfully
2025-11-08 17:14:13.481 | INFO     | agent.mcp_server:create_mcp_server:1305 - Creating MCP server with 12 trading tools
2025-11-08 17:14:13.481 | DEBUG    | agent.mcp_server:create_mcp_server:1308 - 📚 MCP TOOLS BEING REGISTERED:
2025-11-08 17:14:13.482 | DEBUG    | agent.mcp_server:create_mcp_server:1309 -    1. query_market_data - Query market data across 7 categories
2025-11-08 17:14:13.482 | DEBUG    | agent.mcp_server:create_mcp_server:1310 -    2. get_current_price - Get current price for a symbol
2025-11-08 17:14:13.482 | DEBUG    | agent.mcp_server:create_mcp_server:1311 -    3. execute_trade - Execute a trade
2025-11-08 17:14:13.482 | DEBUG    | agent.mcp_server:create_mcp_server:1312 -    4. get_positions - Get open trading positions
2025-11-08 17:14:13.483 | DEBUG    | agent.mcp_server:create_mcp_server:1313 -    5. get_account_status - Get account balance, statistics, and open orders
2025-11-08 17:14:13.483 | DEBUG    | agent.mcp_server:create_mcp_server:1314 -    6. close_position - Close an open position
2025-11-08 17:14:13.483 | DEBUG    | agent.mcp_server:create_mcp_server:1315 -    7. cancel_order - Cancel a specific open order (TP/SL/Limit)
2025-11-08 17:14:13.483 | DEBUG    | agent.mcp_server:create_mcp_server:1316 -    8. update_strategy - Update trading strategy
2025-11-08 17:14:13.483 | DEBUG    | agent.mcp_server:create_mcp_server:1317 -    9. wait_for - Pause execution
2025-11-08 17:14:13.483 | DEBUG    | agent.mcp_server:create_mcp_server:1318 -    10. record_trade_observation - Record trade learnings
2025-11-08 17:14:13.483 | DEBUG    | agent.mcp_server:create_mcp_server:1319 -    11. query_trade_observations - Query past observations
2025-11-08 17:14:13.483 | DEBUG    | agent.mcp_server:create_mcp_server:1320 -    12. save_strategy_and_exit - Save strategy and exit
2025-11-08 17:14:13.483 | INFO     | agent.mcp_server:create_mcp_server:1342 - MCP server created successfully with 12 tools
2025-11-08 17:14:13.483 | INFO     | __main__:run:310 - ================================================================================
2025-11-08 17:14:13.484 | INFO     | __main__:run:311 - 📚 MCP TOOL DESCRIPTIONS BEING SENT TO AGENT:
2025-11-08 17:14:13.484 | INFO     | __main__:run:312 - ================================================================================
2025-11-08 17:14:13.485 | INFO     | __main__:run:320 - ✅ MCP Server initialized with 12 tools:
2025-11-08 17:14:13.485 | INFO     | __main__:run:321 -    1. query_market_data - Market data across 7 categories with 32+ data points
2025-11-08 17:14:13.485 | INFO     | __main__:run:322 -    2. get_current_price - Real-time WebSocket price lookup
2025-11-08 17:14:13.486 | INFO     | __main__:run:323 -    3. execute_trade - Execute trades with required SL/TP
2025-11-08 17:14:13.486 | INFO     | __main__:run:324 -    4. get_positions - Query open positions (paper/aster/symphony)
2025-11-08 17:14:13.486 | INFO     | __main__:run:325 -    5. get_account_status - Balance and performance metrics
2025-11-08 17:14:13.487 | INFO     | __main__:run:326 -    6. close_position - Manually close positions
2025-11-08 17:14:13.487 | INFO     | __main__:run:327 -    7. cancel_order - Cancel TP/SL orders (paper/aster)
2025-11-08 17:14:13.487 | INFO     | __main__:run:328 -    8. update_strategy - Update strategy (experimental mode)
2025-11-08 17:14:13.487 | INFO     | __main__:run:329 -    9. wait_for - Control timing (max 24h)
2025-11-08 17:14:13.487 | INFO     | __main__:run:330 -   10. record_trade_observation - Post-trade reflection
2025-11-08 17:14:13.487 | INFO     | __main__:run:331 -   11. query_trade_observations - Search past learnings
2025-11-08 17:14:13.487 | INFO     | __main__:run:332 -   12. save_strategy_and_exit - Save strategy and exit
2025-11-08 17:14:13.488 | INFO     | __main__:run:333 - 
  All tools will be available to agent via MCP protocol.
2025-11-08 17:14:13.488 | INFO     | __main__:run:339 - ================================================================================
2025-11-08 17:14:13.488 | DEBUG    | __main__:run:343 - 📋 SYSTEM PROMPT:
================================================================================

You are an autonomous trading agent. Execute trades, manage positions, and learn from outcomes.

CURRENT MODE: strategy_definition
STRATEGY: # Autonomous Trading Strategy - BTC Momentum Trading

**Symbol:** BTC/USDT only
**Philosophy:** Use ggShot's multi-timeframe momentum signals as directional foundation. Layer market intelligence to assess regime, build conviction, and time entries. Trade actively with asymmetric risk management - quick to lock profits, reluctant to exit at loss without data invalidation.

---

## Understanding ggShot Multi-Timeframe Dynamics

**ggShot is a momentum indicator with timeframe sensitivity:**

```
5m  � Flips first (most sensitive, noise-prone)
30m � Confirms short-term momentum if trend continues
1h  � Trend establishing, more reliable
4h  � Strong trend, highest conviction
```

**How to Read Signals:**

- **4h/1h = Market Regime:** These establish the broader directional bias
- **30m/5m = Entry Timing:** These show shorter-term momentum shifts
- **Alignment Context:** When multiple timeframes point the same direction, it indicates momentum consistency. When they diverge, it signals either early reversal or counter-trend action.
- **Timeframe Flips:** Lower timeframes flip first. If a lower TF flips against higher TFs then flips back to align, this can signal a strong continuation entry point.

**Note:** Multi-TF alignment provides context and timing insight, but conviction comes from layering additional market data - volume, regime indicators, technicals, and risk/reward structure.

**Price Action Context:**
- ggShot has an underlying trendline (not visible real-time)
- Price often bounces off trendline or key structural levels
- Old ggShot targets become new support/resistance zones

---

## Trade Types & Timeframe Strategy

**Your approach should adapt based on regime and timeframe alignment:**

### Ranging Markets → Shorter Timeframe Trades
When regime indicators show consolidation (low ADX, contracted BBWidth, flat TRIX), price is bouncing between levels rather than trending.

**Strategy:**
- Focus on lower timeframes (5m, 30m) for both entry and targets
- Tighter SL/TP spreads - aim for quick 1-1.5R moves
- Exit at key levels (VWAP, Donchian bands) rather than waiting for trend targets
- Smaller position sizes - ranges can break either direction
- Hold duration: Minutes to hours

### Counter-Trend Setups → Quick Reversals
When lower timeframes oppose higher timeframe bias - you're catching a rebound within a larger trend.

**Strategy:**
- Use the reversal timeframe (30m, 5m) for entry and exit decisions
- Tight stops - you're fading the larger trend
- Take profits quickly at first resistance - don't wait for higher TF targets
- Reduced position size - higher risk
- Hold duration: Quick in, quick out

### Trend Continuation → Wider Targets
When entering WITH the higher timeframe trend, especially at pullbacks where lower TF shows reversal.

**Strategy:**
- Use higher timeframes (1h, 4h) to set targets
- Wider stops - give the trend room to work
- Can use 4h ggShot targets if not yet hit, or structure-based levels
- Trail stops instead of exiting early - let winners run
- Larger position sizes - trend backing you
- Hold duration: Hours to days

**Key Principle:** Match your timeframe focus, target distance, and hold duration to the type of opportunity. Fighting trends or trading ranges requires different execution than riding established momentum.

---

## Session Start: Market Regime Assessment

**At the beginning of each trading session, establish the broader market regime using HIGHER timeframe indicators (1h, 4h, 1d preferred):**

**Regime Indicators (query what makes sense):**
- **Aroon:** Trending (Aroon-Up/Down separation) vs ranging (tight together)?
- **BBWidth:** Expanding (volatility increasing) vs contracting (consolidation)?
- **TRIX:** Rising (momentum building) vs flat/falling (weakening)?
- **ADX:** Strong trend (>25) vs weak trend (<20)?
- **MACD:** Above/below zero line? Histogram expanding/contracting?

**Regime Classification:**
- **Strong Trend:** Multiple indicators agree on direction, ADX >25, BBWidth expanding = maximize sizing
- **Developing Trend:** Mixed signals, moderate ADX = standard sizing
- **Ranging/Choppy:** Aroon tight, BBWidth contracted, MACD near zero = reduce sizing or wait
- **Counter-Trend:** Regime opposes ggShot signal direction = high risk, pass or minimal size

**Purpose:** Don't fight the broader market. If regime says range and ggShot says LONG, be cautious.

---

## Building Conviction: The Layered Approach


**RSI Analysis:**
- **Divergences (HIGH SIGNAL):** Especially on 4h/1h - price makes new high/low but RSI doesn't = reversal strength
- **Overextensions:** RSI >80 or <20 on lower TFs - use to time entries
- **Use:** Lower TF RSI (5m/30m) to find optimal entry price, higher TF (4h/1h) to confirm reversal potential

**Volume Confirmation:**
- OBV trending in same direction as price = validates move
- Volume spike on entry = higher conviction
- Low volume on moves = skepticism, reduce size

**Price Action & Support/Resistance:**
- VWAP as dynamic level for reversals
- ggshot trend_line and entry zones as structural levels
- Previous targets become new support/resistance

**Dynamic Market Data Layer (use contextually):**
You have 32 data points across 7 categories available via `query_market_data`. Use intelligently based on context - query what adds conviction, confirms/invalidates your thesis, or provides necessary market context for the specific decision you're making.

**Philosophy:** These are capabilities, not checklists. Query what's relevant to the setup at hand, not everything every time.

---

## Risk Management

**Position Sizing Formula:**
```
Risk per trade: 5-30% of account balance (NOT position size)
risk_amount = balance � risk_percentage
position_size = risk_amount / (distance_to_SL / entry_price)
margin_required = position_size / leverage
```

**Leverage Scaling (5-20x range):**
- **Higher leverage (15-20x):** Strong setup - favorable regime, strong volume, solid risk/reward
- **Moderate leverage (10-15x):** Standard setup - reasonable conviction with proper structure
- **Lower leverage (5-10x):** Uncertain setup - mixed signals, weak volume, or ranging conditions

**Risk/Reward Requirement:**
- **MINIMUM:** R/R >= 1:1 (take profit distance must equal or exceed stop loss distance)
- **VALIDATION:** Always calculate before entry:
  ```
  risk_distance = abs(entry - SL) / entry
  reward_distance = abs(TP - entry) / entry
  R/R = reward_distance / risk_distance
  ```
- **If R/R < 1.0:** DO NOT TAKE THE TRADE (non-negotiable)

---

## Setting Stop Loss & Take Profit

**CRITICAL RULE:** Always calculate from CURRENT MARKET PRICE, never use stale ggShot levels.

**Stop Loss Placement (use data to be intelligent):**
1. **ATR-based:** Query ATR on signal timeframe, use 1.5-2.0� ATR for SL distance
2. **Structure-based:** Place below key support (LONG) or above resistance (SHORT)
3. **Donchian-based:** Use Donchian channel boundaries as natural stops
4. **Conviction-adjusted:** Tighter stops (1.5� ATR) for low conviction, wider (2.0-2.5� ATR) for high conviction

**Take Profit Placement:**
1. **Primary target:** 2R minimum (ensure R/R >= 1:1, prefer 1.5:1 or better)
2. **Use structure:** Opposite Donchian band, previous ggShot targets, VWAP standard deviations
3. **Multiple targets:** Consider scaling out at 1R, 2R, 3R if strong trend

**Intent Matters:**
- Your SL should have reasoning behind it (not arbitrary 2%)
- Your TP should target logical zones (not arbitrary 4%)
- Use market data queries to inform these decisions

---

## Position Management: Asymmetric Approach

**Taking Profits:**
- Locking profits is valid - markets can reverse at any time
- If you see clear reversal signs (ggShot TF flipping, volume drying up, RSI divergence), closing to protect profits is reasonable
- Trailing stops to breakeven once well into profit reduces risk
- Balance conviction in your thesis against taking profits too early - both have merit

**Closing at Loss (Requires Justification):**
- Don't close before SL without data-driven reason
- ONLY close early if **thesis is invalidated by data:**
  - ggShot higher TF flipped against you (regime changed)
  - Volume completely dried up (invalidates momentum thesis)
  - Key technical level clearly broken (structure thesis failed)
  - Major news/event changes fundamental picture
- **Philosophy:** Your SL was placed intentionally using data. Respect it unless data proves you wrong BEFORE price hits it.

**Monitoring Frequency:**
- **No positions:** Check every 30-60 minutes (patient, selective)
- **Holding positions:** Check every 10-30 minutes (attentive, ready to act)
- **Near SL/TP or high volatility:** Check every 5-15 minutes

---

## Red Flags: When to Reduce Risk or Pass

**Reduce position size by 30-50% if:**
- Counter-trend regime + weak volume (<75% average)
- Extreme RSI (>80 or <20) on signal timeframe at entry
- ATR spike (high volatility) + overextended price (far from VWAP/moving averages)
- Only 1 timeframe aligned (no confirmation from adjacent TFs)

**Pass the trade if:**
- 2+ red flags present simultaneously
- R/R < 1:1 (always pass)
- Counter-trend to strong regime without exceptional setup
- Volume extremely weak (<50% average) on confirmation

---

## Execution Cycle

**Per-Cycle Process:**
1. Check current positions first - close any at TP/SL, assess if thesis still valid
2. Query ggShot for BTC across all timeframes (5m, 30m, 1h, 4h)
3. Assess TF alignment - identify conviction level
4. If strong signal identified:
   - Assess broader regime (if first trade of session or regime unclear)
   - Check volume on signal timeframe
   - Review core technicals (RSI multi-TF, OBV, VWAP)
   - Query additional market data if needed for conviction/invalidation
5. Calculate SL/TP from CURRENT PRICE using ATR/structure
6. Validate R/R >= 1:1
7. Calculate position size via risk formula
8. Execute if conviction threshold met
9. Record observation after closing any trade
10. Use wait_for tool before next cycle (adapt to volatility)

---

## Execution Guidelines

**DO:**
- Calculate all levels (SL/TP/entry) from CURRENT PRICE
- Validate R/R >= 1:1 before every entry (non-negotiable)
- Use market data queries contextually to build conviction
- Scale leverage (5-20x) with conviction level
- Lock profits early without guilt
- Use wait_for between cycles (be patient)
- Record observations after closing trades

**DON'T:**
- Use stale ggShot price levels for SL/TP (direction only if >1 day old)
- Enter with R/R < 1:1 (NEVER)
- Close at loss without data invalidation
- Use leverage outside 5-20x range
- Risk >30% of balance in one trade
- Exceed 5 open positions
- Query every data point every cycle (be selective)

**Adaptability:**
- If R/R validation blocking trades � recalculate levels, wait for better entries
- If SL getting hit frequently � tighten entry criteria, wait for stronger confirmations
- If TP consistently hit � increase sizing on similar setups
- Evolution is expected - strategy autonomously editable

---

## Key Success Factors

1. **Multi-TF ggShot analysis** - alignment strength determines conviction
2. **Volume confirmation** - demand real participation, not low-volume noise
3. **Regime awareness** - don't fight strong counter-trends
4. **Intelligent SL/TP** - use ATR/structure, calculate from current price
5. **R/R discipline** - never enter <1:1, always validate
6. **Asymmetric exits** - quick to take profits, slow to take losses (unless data invalidates)
7. **Dynamic market data** - use contextually, not ritually
8. **Patient execution** - wait for quality setups with conviction

---

## Strategy Settings

- **Symbol:** BTC/USDT only
- **Autonomously Editable:** TRUE (learns and evolves)
- **Risk Per Trade:** 5-30% of balance (scaled by conviction)
- **Leverage Range:** 5-20x (scaled by conviction)
- **Minimum R/R:** 1:1 (validated before every trade)
- **Max Positions:** 3-5
- **Primary Timeframes:** 4h/1h (regime), 30m/5m (timing)
- **Check Frequency:** 30-60 min searching, 10-30 min holding

AUTONOMOUSLY_EDITABLE: True

FRAMEWORK RULES:
- Execute the strategy faithfully - it is your source of truth
- Always set stop loss and take profit (REQUIRED for safety)
- Record trade observations after closing positions (what worked/failed)
- Use wait_for() tool to control your timing as the strategy specifies

MODE-SPECIFIC BEHAVIOR:

strategy_definition: Help user build a complete strategy for YOU to execute autonomously.

  START by assessing:
  1. User's experience level (beginner/intermediate/advanced)
  2. Whether they have a strategy in mind already

  THEN branch:
  - If inexperienced/no strategy: Show available data sources (7 categories, 32 data points).
    Explain how indicators work and guide them toward proven patterns. Be educational.
  - If experienced/has strategy: Validate feasibility with your available data.
    Check if you can execute their strategy, suggest alternatives if gaps exist.

  ALWAYS ground in reality:
  - Only suggest strategies using data you actually have access to
  - Be specific about what you CAN and CANNOT do
  - Make rules testable and executable

  MUST define before switching to autonomous:
  - Entry conditions (specific, testable)
  - Exit conditions (SL/TP minimum)
  - Position sizing rules
  - Monitoring frequency

  Use save_strategy_and_exit when strategy is finalized to save it and exit.

autonomous: Execute the strategy 24/7 without user interaction.
  - Check positions first (close if exit conditions met)
  - Query market data as strategy specifies
  - Execute trades when entry conditions met
  - Use wait_for() between checks as strategy defines
  - Record observations after closing trades

STRATEGY UPDATES:
- If AUTONOMOUSLY_EDITABLE=true: Can update strategy based on learnings using update_strategy tool
- If AUTONOMOUSLY_EDITABLE=false: Cannot modify strategy - execute it as written

AVAILABLE DATA SOURCES:
Use query_market_data tool with these EXACT categories and data point names:

CATEGORIES:
- technical_analysis: RSI, MACD, Stochastic, Williams_R, CCI, MFI, ADX, PSAR, Aroon, ATR, BB, OBV, SMA, EMA, ROC, VWAP, TRIX, Vortex, BBWidth, Keltner, Donchian
- macro_economics: vix, dxy, cpi, nfp
- sentiment_social: twitter_sentiment
- derivatives_leverage: btc_funding_rate, eth_funding_rate
- on_chain_analytics: btc_tvl, whale_activity
- news_regulatory: crypto_news
- trading_signals: ggshot

CRITICAL RULES:
1. ggshot is a TRADING SIGNAL, NOT a technical indicator
   ✅ CORRECT: {"trading_signals": ["ggshot"]}
   ❌ WRONG: {"technical_analysis": ["ggshot"]}

2. Use EXACT names (case-insensitive but complete):
   - "twitter_sentiment" NOT "twitter" or "sentiment"
   - "ggshot" NOT "ggshot_signals"
   - "btc_funding_rate" NOT "funding_rate"

3. Category names must be EXACT:
   - "trading_signals" NOT "signals" or "trading_signal"

Be disciplined and execute the strategy faithfully.
        
================================================================================
2025-11-08 17:14:13.524 | INFO     | __main__:_load_session_id:138 - 📝 No existing session found - will create new one
2025-11-08 17:14:13.524 | INFO     | __main__:run:380 - 🆕 Starting fresh session
2025-11-08 17:14:16.173 | INFO     | __main__:run:386 - Agent started in strategy_definition mode
2025-11-08 17:14:27.171 | DEBUG    | agent.service_client:_retry_request:82 - Request: GET /api/v2/agent/account/bb2560fd-b053-464f-8a58-8e254e4d36fa, kwargs: {'params': {'user_id': '00000000-0000-0000-0000-000000000000'}}
2025-11-08 17:14:27.702 | DEBUG    | agent.service_client:_retry_request:84 - Response URL: http://localhost:8000/api/v2/agent/account/bb2560fd-b053-464f-8a58-8e254e4d36fa?user_id=00000000-0000-0000-0000-000000000000
2025-11-08 17:14:27.702 | DEBUG    | agent.service_client:_retry_request:85 - Response status: 200
2025-11-08 17:14:27.702 | DEBUG    | agent.service_client:_retry_request:90 - Response data: {'status': 'success', 'account': {'balance': 167.39550627, 'margin_balance': 167.39550627, 'unrealized_pnl': 0.0, 'open_positions': 0, 'open_orders': [], 'total_trades': 0, 'win_rate': 0.0, 'total_pnl': 0.0}, 'trading_mode': 'aster', 'timestamp': '2025-11-08T17:14:27.700241'}
2025-11-08 17:14:27.719 | DEBUG    | agent.service_client:_retry_request:82 - Request: GET /api/v2/agent/positions/bb2560fd-b053-464f-8a58-8e254e4d36fa, kwargs: {'params': {'user_id': '00000000-0000-0000-0000-000000000000'}}
2025-11-08 17:14:27.877 | DEBUG    | agent.service_client:_retry_request:84 - Response URL: http://localhost:8000/api/v2/agent/positions/bb2560fd-b053-464f-8a58-8e254e4d36fa?user_id=00000000-0000-0000-0000-000000000000
2025-11-08 17:14:27.878 | DEBUG    | agent.service_client:_retry_request:85 - Response status: 200
2025-11-08 17:14:27.878 | DEBUG    | agent.service_client:_retry_request:90 - Response data: {'status': 'success', 'positions': [], 'trading_mode': 'aster', 'timestamp': '2025-11-08T17:14:27.876240'}
2025-11-08 17:14:35.060 | DEBUG    | agent.mcp_server:query_market_data:156 - 🔧 query_market_data CALLED
2025-11-08 17:14:35.061 | DEBUG    | agent.mcp_server:query_market_data:157 -    Args received: {
  "symbol": "BTC",
  "categories": "{\"trading_signals\": [\"ggshot\"]}",
  "timeframe": "5m",
  "scan_days": 0
}
2025-11-08 17:14:35.061 | DEBUG    | agent.mcp_server:query_market_data:305 -    Parsed technical_indicators: []
2025-11-08 17:14:35.062 | DEBUG    | agent.mcp_server:query_market_data:306 -    Parsed intelligence_sources: {'trading_signals': ['ggshot']}
2025-11-08 17:14:35.062 | DEBUG    | agent.mcp_server:query_market_data:309 -    Calling API with symbol=BTC, indicators=[], data_sources={'trading_signals': ['ggshot']}, timeframe=5m
2025-11-08 17:14:35.062 | DEBUG    | agent.service_client:_retry_request:82 - Request: POST /api/v2/agent/query-market-data, kwargs: {'params': {'user_id': '00000000-0000-0000-0000-000000000000'}, 'json': {'config_id': 'bb2560fd-b053-464f-8a58-8e254e4d36fa', 'symbol': 'BTC', 'timeframe': '5m', 'data_sources': {'trading_signals': ['ggshot']}}}
2025-11-08 17:14:35.525 | DEBUG    | agent.service_client:_retry_request:84 - Response URL: http://localhost:8000/api/v2/agent/query-market-data?user_id=00000000-0000-0000-0000-000000000000
2025-11-08 17:14:35.526 | DEBUG    | agent.service_client:_retry_request:85 - Response status: 200
2025-11-08 17:14:35.526 | DEBUG    | agent.service_client:_retry_request:90 - Response data: {'status': 'success', 'data': {'market_intelligence': {'trading_signals': {'ggshot': {'signals': {'1h': {'direction': 'SHORT', 'entry_zone': {'low': 105718.8, 'mid': 108485.35, 'high': 111251.9}, 'stop_loss': 113123.3, 'take_profit': 103940.5, 'targets': [{'price': 103940.5, 'number': 1}, {'price': 102162.2, 'number': 2}, {'price': 100383.9, 'number': 3}, {'price': 95049.0, 'number': 4}], 'confidence': None, 'strategy_accuracy': None, 'trend_line': 111251.9, 'timestamp': '2025-11-03T16:00:18+00:00'}, '30m': {'direction': 'LONG', 'entry_zone': {'low': 112127.5, 'mid': 109957.55, 'high': 107787.6}, 'stop_loss': 107033.1, 'take_profit': 112912.4, 'targets': [{'price': 112912.4, 'number': 1}, {'price': 113697.3, 'number': 2}, {'price': 114482.2, 'number': 3}, {'price': 116836.9, 'number': 4}], 'confidence': None, 'strategy_accuracy': None, 'trend_line': 107787.6, 'timestamp': '2025-10-21T15:02:31+00:00'}, '4h': {'direction': 'SHORT', 'entry_zone': {'low': 108220.5, 'mid': 112617.55, 'high': 117014.6}, 'stop_loss': 123043.0, 'take_profit': 102645.1, 'targets': [{'price': 102645.1, 'number': 1}, {'price': 97069.8, 'number': 2}, {'price': 91494.4, 'number': 3}, {'price': 74768.4, 'number': 4}], 'confidence': None, 'strategy_accuracy': None, 'trend_line': 117014.6, 'timestamp': '2025-10-16T18:00:14+00:00'}, '5m': {'direction': 'LONG', 'entry_zone': {'low': 104211.1, 'mid': 103002.1, 'high': 101793.1}, 'stop_loss': 101589.5, 'take_profit': 104419.5, 'targets': [{'price': 104419.5, 'number': 1}, {'price': 104627.9, 'number': 2}, {'price': 104836.4, 'number': 3}, {'price': 105461.6, 'number': 4}], 'confidence': None, 'strategy_accuracy': None, 'trend_line': 101793.1, 'timestamp': '2025-11-05T18:40:09+00:00'}}, 'metadata': {'symbol': 'BTC/USDT', 'timeframes_found': ['1h', '30m', '4h', '5m'], 'latest_signal_age': '2 days ago', 'query_timestamp': '2025-11-08T17:14:35.521947+00:00'}}}}}, 'timestamp': '2025-11-08T17:14:35.524401'}
2025-11-08 17:14:35.526 | DEBUG    | agent.mcp_server:query_market_data:334 -    Response: 
🌐 Market Intelligence:
{
  "trading_signals": {
    "ggshot": {
      "signals": {
        "1h": {
          "direction": "SHORT",
          "entry_zone": {
            "low": 105718.8,
            "mid": 108485.35,
            "high": 111251.9
          },
          "stop_loss": 113123.3,
          "take_profit": 103940.5,
          "targets": [
            {
              "price": 103940.5,
              "number": 1
            },
            {
              "price": 102162.2,
              "...
2025-11-08 17:14:35.601 | DEBUG    | agent.mcp_server:query_market_data:156 - 🔧 query_market_data CALLED
2025-11-08 17:14:35.601 | DEBUG    | agent.mcp_server:query_market_data:157 -    Args received: {
  "symbol": "BTC",
  "categories": "{\"trading_signals\": [\"ggshot\"]}",
  "timeframe": "30m",
  "scan_days": 0
}
2025-11-08 17:14:35.601 | DEBUG    | agent.mcp_server:query_market_data:305 -    Parsed technical_indicators: []
2025-11-08 17:14:35.601 | DEBUG    | agent.mcp_server:query_market_data:306 -    Parsed intelligence_sources: {'trading_signals': ['ggshot']}
2025-11-08 17:14:35.602 | DEBUG    | agent.mcp_server:query_market_data:309 -    Calling API with symbol=BTC, indicators=[], data_sources={'trading_signals': ['ggshot']}, timeframe=30m
2025-11-08 17:14:35.602 | DEBUG    | agent.service_client:_retry_request:82 - Request: POST /api/v2/agent/query-market-data, kwargs: {'params': {'user_id': '00000000-0000-0000-0000-000000000000'}, 'json': {'config_id': 'bb2560fd-b053-464f-8a58-8e254e4d36fa', 'symbol': 'BTC', 'timeframe': '30m', 'data_sources': {'trading_signals': ['ggshot']}}}
2025-11-08 17:14:35.729 | DEBUG    | agent.service_client:_retry_request:84 - Response URL: http://localhost:8000/api/v2/agent/query-market-data?user_id=00000000-0000-0000-0000-000000000000
2025-11-08 17:14:35.730 | DEBUG    | agent.service_client:_retry_request:85 - Response status: 200
2025-11-08 17:14:35.730 | DEBUG    | agent.service_client:_retry_request:90 - Response data: {'status': 'success', 'data': {'market_intelligence': {'trading_signals': {'ggshot': {'signals': {'1h': {'direction': 'SHORT', 'entry_zone': {'low': 105718.8, 'mid': 108485.35, 'high': 111251.9}, 'stop_loss': 113123.3, 'take_profit': 103940.5, 'targets': [{'price': 103940.5, 'number': 1}, {'price': 102162.2, 'number': 2}, {'price': 100383.9, 'number': 3}, {'price': 95049.0, 'number': 4}], 'confidence': None, 'strategy_accuracy': None, 'trend_line': 111251.9, 'timestamp': '2025-11-03T16:00:18+00:00'}, '30m': {'direction': 'LONG', 'entry_zone': {'low': 112127.5, 'mid': 109957.55, 'high': 107787.6}, 'stop_loss': 107033.1, 'take_profit': 112912.4, 'targets': [{'price': 112912.4, 'number': 1}, {'price': 113697.3, 'number': 2}, {'price': 114482.2, 'number': 3}, {'price': 116836.9, 'number': 4}], 'confidence': None, 'strategy_accuracy': None, 'trend_line': 107787.6, 'timestamp': '2025-10-21T15:02:31+00:00'}, '4h': {'direction': 'SHORT', 'entry_zone': {'low': 108220.5, 'mid': 112617.55, 'high': 117014.6}, 'stop_loss': 123043.0, 'take_profit': 102645.1, 'targets': [{'price': 102645.1, 'number': 1}, {'price': 97069.8, 'number': 2}, {'price': 91494.4, 'number': 3}, {'price': 74768.4, 'number': 4}], 'confidence': None, 'strategy_accuracy': None, 'trend_line': 117014.6, 'timestamp': '2025-10-16T18:00:14+00:00'}, '5m': {'direction': 'LONG', 'entry_zone': {'low': 104211.1, 'mid': 103002.1, 'high': 101793.1}, 'stop_loss': 101589.5, 'take_profit': 104419.5, 'targets': [{'price': 104419.5, 'number': 1}, {'price': 104627.9, 'number': 2}, {'price': 104836.4, 'number': 3}, {'price': 105461.6, 'number': 4}], 'confidence': None, 'strategy_accuracy': None, 'trend_line': 101793.1, 'timestamp': '2025-11-05T18:40:09+00:00'}}, 'metadata': {'symbol': 'BTC/USDT', 'timeframes_found': ['1h', '30m', '4h', '5m'], 'latest_signal_age': '2 days ago', 'query_timestamp': '2025-11-08T17:14:35.521947+00:00'}}}}}, 'timestamp': '2025-11-08T17:14:35.728438'}
2025-11-08 17:14:35.730 | DEBUG    | agent.mcp_server:query_market_data:334 -    Response: 
🌐 Market Intelligence:
{
  "trading_signals": {
    "ggshot": {
      "signals": {
        "1h": {
          "direction": "SHORT",
          "entry_zone": {
            "low": 105718.8,
            "mid": 108485.35,
            "high": 111251.9
          },
          "stop_loss": 113123.3,
          "take_profit": 103940.5,
          "targets": [
            {
              "price": 103940.5,
              "number": 1
            },
            {
              "price": 102162.2,
              "...
2025-11-08 17:14:35.785 | DEBUG    | agent.mcp_server:query_market_data:156 - 🔧 query_market_data CALLED
2025-11-08 17:14:35.786 | DEBUG    | agent.mcp_server:query_market_data:157 -    Args received: {
  "symbol": "BTC",
  "categories": "{\"trading_signals\": [\"ggshot\"]}",
  "timeframe": "1h",
  "scan_days": 0
}
2025-11-08 17:14:35.786 | DEBUG    | agent.mcp_server:query_market_data:305 -    Parsed technical_indicators: []
2025-11-08 17:14:35.786 | DEBUG    | agent.mcp_server:query_market_data:306 -    Parsed intelligence_sources: {'trading_signals': ['ggshot']}
2025-11-08 17:14:35.787 | DEBUG    | agent.mcp_server:query_market_data:309 -    Calling API with symbol=BTC, indicators=[], data_sources={'trading_signals': ['ggshot']}, timeframe=1h
2025-11-08 17:14:35.787 | DEBUG    | agent.service_client:_retry_request:82 - Request: POST /api/v2/agent/query-market-data, kwargs: {'params': {'user_id': '00000000-0000-0000-0000-000000000000'}, 'json': {'config_id': 'bb2560fd-b053-464f-8a58-8e254e4d36fa', 'symbol': 'BTC', 'timeframe': '1h', 'data_sources': {'trading_signals': ['ggshot']}}}
2025-11-08 17:14:35.916 | DEBUG    | agent.service_client:_retry_request:84 - Response URL: http://localhost:8000/api/v2/agent/query-market-data?user_id=00000000-0000-0000-0000-000000000000
2025-11-08 17:14:35.916 | DEBUG    | agent.service_client:_retry_request:85 - Response status: 200
2025-11-08 17:14:35.916 | DEBUG    | agent.service_client:_retry_request:90 - Response data: {'status': 'success', 'data': {'market_intelligence': {'trading_signals': {'ggshot': {'signals': {'1h': {'direction': 'SHORT', 'entry_zone': {'low': 105718.8, 'mid': 108485.35, 'high': 111251.9}, 'stop_loss': 113123.3, 'take_profit': 103940.5, 'targets': [{'price': 103940.5, 'number': 1}, {'price': 102162.2, 'number': 2}, {'price': 100383.9, 'number': 3}, {'price': 95049.0, 'number': 4}], 'confidence': None, 'strategy_accuracy': None, 'trend_line': 111251.9, 'timestamp': '2025-11-03T16:00:18+00:00'}, '30m': {'direction': 'LONG', 'entry_zone': {'low': 112127.5, 'mid': 109957.55, 'high': 107787.6}, 'stop_loss': 107033.1, 'take_profit': 112912.4, 'targets': [{'price': 112912.4, 'number': 1}, {'price': 113697.3, 'number': 2}, {'price': 114482.2, 'number': 3}, {'price': 116836.9, 'number': 4}], 'confidence': None, 'strategy_accuracy': None, 'trend_line': 107787.6, 'timestamp': '2025-10-21T15:02:31+00:00'}, '4h': {'direction': 'SHORT', 'entry_zone': {'low': 108220.5, 'mid': 112617.55, 'high': 117014.6}, 'stop_loss': 123043.0, 'take_profit': 102645.1, 'targets': [{'price': 102645.1, 'number': 1}, {'price': 97069.8, 'number': 2}, {'price': 91494.4, 'number': 3}, {'price': 74768.4, 'number': 4}], 'confidence': None, 'strategy_accuracy': None, 'trend_line': 117014.6, 'timestamp': '2025-10-16T18:00:14+00:00'}, '5m': {'direction': 'LONG', 'entry_zone': {'low': 104211.1, 'mid': 103002.1, 'high': 101793.1}, 'stop_loss': 101589.5, 'take_profit': 104419.5, 'targets': [{'price': 104419.5, 'number': 1}, {'price': 104627.9, 'number': 2}, {'price': 104836.4, 'number': 3}, {'price': 105461.6, 'number': 4}], 'confidence': None, 'strategy_accuracy': None, 'trend_line': 101793.1, 'timestamp': '2025-11-05T18:40:09+00:00'}}, 'metadata': {'symbol': 'BTC/USDT', 'timeframes_found': ['1h', '30m', '4h', '5m'], 'latest_signal_age': '2 days ago', 'query_timestamp': '2025-11-08T17:14:35.521947+00:00'}}}}}, 'timestamp': '2025-11-08T17:14:35.915159'}
2025-11-08 17:14:35.917 | DEBUG    | agent.mcp_server:query_market_data:334 -    Response: 
🌐 Market Intelligence:
{
  "trading_signals": {
    "ggshot": {
      "signals": {
        "1h": {
          "direction": "SHORT",
          "entry_zone": {
            "low": 105718.8,
            "mid": 108485.35,
            "high": 111251.9
          },
          "stop_loss": 113123.3,
          "take_profit": 103940.5,
          "targets": [
            {
              "price": 103940.5,
              "number": 1
            },
            {
              "price": 102162.2,
              "...
2025-11-08 17:14:35.965 | DEBUG    | agent.mcp_server:query_market_data:156 - 🔧 query_market_data CALLED
2025-11-08 17:14:35.965 | DEBUG    | agent.mcp_server:query_market_data:157 -    Args received: {
  "symbol": "BTC",
  "categories": "{\"trading_signals\": [\"ggshot\"]}",
  "timeframe": "4h",
  "scan_days": 0
}
2025-11-08 17:14:35.965 | DEBUG    | agent.mcp_server:query_market_data:305 -    Parsed technical_indicators: []
2025-11-08 17:14:35.965 | DEBUG    | agent.mcp_server:query_market_data:306 -    Parsed intelligence_sources: {'trading_signals': ['ggshot']}
2025-11-08 17:14:35.965 | DEBUG    | agent.mcp_server:query_market_data:309 -    Calling API with symbol=BTC, indicators=[], data_sources={'trading_signals': ['ggshot']}, timeframe=4h
2025-11-08 17:14:35.965 | DEBUG    | agent.service_client:_retry_request:82 - Request: POST /api/v2/agent/query-market-data, kwargs: {'params': {'user_id': '00000000-0000-0000-0000-000000000000'}, 'json': {'config_id': 'bb2560fd-b053-464f-8a58-8e254e4d36fa', 'symbol': 'BTC', 'timeframe': '4h', 'data_sources': {'trading_signals': ['ggshot']}}}
2025-11-08 17:14:36.094 | DEBUG    | agent.service_client:_retry_request:84 - Response URL: http://localhost:8000/api/v2/agent/query-market-data?user_id=00000000-0000-0000-0000-000000000000
2025-11-08 17:14:36.094 | DEBUG    | agent.service_client:_retry_request:85 - Response status: 200
2025-11-08 17:14:36.095 | DEBUG    | agent.service_client:_retry_request:90 - Response data: {'status': 'success', 'data': {'market_intelligence': {'trading_signals': {'ggshot': {'signals': {'1h': {'direction': 'SHORT', 'entry_zone': {'low': 105718.8, 'mid': 108485.35, 'high': 111251.9}, 'stop_loss': 113123.3, 'take_profit': 103940.5, 'targets': [{'price': 103940.5, 'number': 1}, {'price': 102162.2, 'number': 2}, {'price': 100383.9, 'number': 3}, {'price': 95049.0, 'number': 4}], 'confidence': None, 'strategy_accuracy': None, 'trend_line': 111251.9, 'timestamp': '2025-11-03T16:00:18+00:00'}, '30m': {'direction': 'LONG', 'entry_zone': {'low': 112127.5, 'mid': 109957.55, 'high': 107787.6}, 'stop_loss': 107033.1, 'take_profit': 112912.4, 'targets': [{'price': 112912.4, 'number': 1}, {'price': 113697.3, 'number': 2}, {'price': 114482.2, 'number': 3}, {'price': 116836.9, 'number': 4}], 'confidence': None, 'strategy_accuracy': None, 'trend_line': 107787.6, 'timestamp': '2025-10-21T15:02:31+00:00'}, '4h': {'direction': 'SHORT', 'entry_zone': {'low': 108220.5, 'mid': 112617.55, 'high': 117014.6}, 'stop_loss': 123043.0, 'take_profit': 102645.1, 'targets': [{'price': 102645.1, 'number': 1}, {'price': 97069.8, 'number': 2}, {'price': 91494.4, 'number': 3}, {'price': 74768.4, 'number': 4}], 'confidence': None, 'strategy_accuracy': None, 'trend_line': 117014.6, 'timestamp': '2025-10-16T18:00:14+00:00'}, '5m': {'direction': 'LONG', 'entry_zone': {'low': 104211.1, 'mid': 103002.1, 'high': 101793.1}, 'stop_loss': 101589.5, 'take_profit': 104419.5, 'targets': [{'price': 104419.5, 'number': 1}, {'price': 104627.9, 'number': 2}, {'price': 104836.4, 'number': 3}, {'price': 105461.6, 'number': 4}], 'confidence': None, 'strategy_accuracy': None, 'trend_line': 101793.1, 'timestamp': '2025-11-05T18:40:09+00:00'}}, 'metadata': {'symbol': 'BTC/USDT', 'timeframes_found': ['1h', '30m', '4h', '5m'], 'latest_signal_age': '2 days ago', 'query_timestamp': '2025-11-08T17:14:35.521947+00:00'}}}}}, 'timestamp': '2025-11-08T17:14:36.093175'}
2025-11-08 17:14:36.095 | DEBUG    | agent.mcp_server:query_market_data:334 -    Response: 
🌐 Market Intelligence:
{
  "trading_signals": {
    "ggshot": {
      "signals": {
        "1h": {
          "direction": "SHORT",
          "entry_zone": {
            "low": 105718.8,
            "mid": 108485.35,
            "high": 111251.9
          },
          "stop_loss": 113123.3,
          "take_profit": 103940.5,
          "targets": [
            {
              "price": 103940.5,
              "number": 1
            },
            {
              "price": 102162.2,
              "...
2025-11-08 17:14:49.976 | DEBUG    | agent.mcp_server:get_current_price:398 - 🔧 get_current_price CALLED with args: {'symbol': 'BTC'}
2025-11-08 17:14:49.977 | DEBUG    | agent.service_client:_retry_request:82 - Request: GET /api/v2/agent/current-price/BTC, kwargs: {'params': {'user_id': '00000000-0000-0000-0000-000000000000'}}
2025-11-08 17:14:49.984 | DEBUG    | agent.service_client:_retry_request:84 - Response URL: http://localhost:8000/api/v2/agent/current-price/BTC?user_id=00000000-0000-0000-0000-000000000000
2025-11-08 17:14:49.985 | DEBUG    | agent.service_client:_retry_request:85 - Response status: 200
2025-11-08 17:14:49.985 | DEBUG    | agent.service_client:_retry_request:90 - Response data: {'status': 'success', 'symbol': 'BTC', 'current_price': 101648.56, 'bid': 101597.73572, 'ask': 101699.38428, 'spread_percent': 0.10000000000000143, 'timestamp': '2025-11-08T17:14:49.983239', 'source': 'websocket_cache'}
2025-11-08 17:15:01.813 | DEBUG    | agent.mcp_server:query_market_data:156 - 🔧 query_market_data CALLED
2025-11-08 17:15:01.813 | DEBUG    | agent.mcp_server:query_market_data:157 -    Args received: {
  "symbol": "BTC",
  "categories": "{\"technical_analysis\": [\"ADX\", \"TRIX\", \"BBWidth\", \"Aroon\"]}",
  "timeframe": "4h",
  "scan_days": 0
}
2025-11-08 17:15:01.814 | DEBUG    | agent.mcp_server:query_market_data:305 -    Parsed technical_indicators: ['ADX', 'TRIX', 'BBWidth', 'Aroon']
2025-11-08 17:15:01.814 | DEBUG    | agent.mcp_server:query_market_data:306 -    Parsed intelligence_sources: {}
2025-11-08 17:15:01.815 | DEBUG    | agent.mcp_server:query_market_data:309 -    Calling API with symbol=BTC, indicators=['ADX', 'TRIX', 'BBWidth', 'Aroon'], data_sources={}, timeframe=4h
2025-11-08 17:15:01.815 | DEBUG    | agent.service_client:_retry_request:82 - Request: POST /api/v2/agent/query-market-data, kwargs: {'params': {'user_id': '00000000-0000-0000-0000-000000000000'}, 'json': {'config_id': 'bb2560fd-b053-464f-8a58-8e254e4d36fa', 'symbol': 'BTC', 'timeframe': '4h', 'indicators': ['ADX', 'TRIX', 'BBWidth', 'Aroon']}}
2025-11-08 17:15:03.273 | DEBUG    | agent.service_client:_retry_request:84 - Response URL: http://localhost:8000/api/v2/agent/query-market-data?user_id=00000000-0000-0000-0000-000000000000
2025-11-08 17:15:03.273 | DEBUG    | agent.service_client:_retry_request:85 - Response status: 200
2025-11-08 17:15:03.274 | DEBUG    | agent.service_client:_retry_request:90 - Response data: {'status': 'success', 'data': {'technicals': {'status': 'success', 'result': {'symbol': 'BTC/USDT', 'timeframe': '4h', 'connector': 'kucoin', 'data_points': 100, 'limit_used': 100, 'timestamp': '2025-11-08T17:15:02.921530', 'indicators': {'adx': {'indicator': 'ADX', 'current': {'adx': 34.11, 'plus_di': 16.73, 'minus_di': 28.15, 'timestamp': '2025-11-08T17:15:02.896008+00:00'}, 'context': {'trend_strength': 'strong', 'strength_value': 34.11, 'description': 'Strong trending market', 'trend_evolution': 'stable', 'directional_bias': 'bearish', 'directional_strength': 11.42}, 'levels': {'current_strength': 'strong', 'weak_threshold': 20, 'strong_threshold': 25, 'very_strong_threshold': 40, 'extreme_threshold': 60}, 'trend_strength': {'strength_percentage': 34.1, 'strong_trend_percentage': 89.0, 'weak_trend_percentage': 1.4, 'consistency': 0.741}, 'directional': {'current_bias': 'bearish', 'directional_strength': 11.42, 'plus_di_momentum': -0.62, 'minus_di_momentum': -0.28, 'crossovers': {'recent_crossovers': [], 'latest_crossover': None}, 'spread_analysis': {'current_spread': -11.42, 'average_spread': -4.59, 'spread_volatility': 17.79, 'max_bullish_spread': 38.05, 'max_bearish_spread': -32.99, 'spread_interpretation': 'extreme_directional_bias'}, 'dominance': {'bullish_dominance_pct': 27.9, 'bearish_dominance_pct': 72.1, 'dominant_direction': 'bearish'}}, 'momentum': {'velocity': -0.78, 'acceleration': -0.21, 'slope_interpretation': 'trend_strength_stable', 'momentum_quality': 'low_quality_momentum'}, 'patterns': {}, 'position_rank': {'percentile': 0.0, 'interpretation': 'extremely_low'}, 'summary': 'ADX 34.1 - Strong trending market with bearish bias (11.4)'}, 'trix': {'indicator': 'TRIX', 'length': 14, 'current': {'trix': -0.147594, 'signal': 101648.56, 'histogram': -101648.707594, 'timestamp': '2025-11-08T17:15:02.902293+00:00'}, 'context': {'trend': {'direction': 'sideways', 'strength': 0.075, 'velocity': 0.008931, 'acceleration': -0.00315}, 'momentum': {'direction': 'bearish', 'strength_level': 'strong', 'persistence': 1.0}, 'volatility': 0.125096}, 'levels': {'zero_line': {'position': 'below_zero', 'above_zero_pct': 32.6, 'below_zero_pct': 66.3, 'recent_crossings': []}, 'signal_line': {'recent_crossovers': [], 'latest_crossover': None, 'crossover_frequency': 0.0}, 'key_levels': [0], 'recent_crossovers': []}, 'extremes': {'recent_high': {'value': -0.147594, 'periods_ago': 0.0, 'significance': 0.0}, 'recent_low': {'value': -0.267315, 'periods_ago': 18.0, 'significance': 1.0}}, 'patterns': {}, 'evidence': {'data_quality': {'aligned_periods': 86, 'had_signal': True, 'had_prices': False, 'windows_used': {'velocity': 2, 'acceleration': 4, 'turning_points': 14, 'divergence': 14}}, 'calculation_notes': 'TRIX analysis based on 86 aligned periods with length=14'}, 'summary': 'TRIX -0.147594 - strong bearish momentum, histogram -101648.707594 (below zero)'}, 'bbwidth': {'indicator': 'Bollinger_Width', 'current': {'width': 4.08, 'timestamp': '2025-11-08T17:15:02.911455+00:00'}, 'context': {'trend': {'direction': 'stable', 'velocity': 0.035, 'acceleration': 0.192, 'strength': 0.014}, 'expansion': {'cycle_position': 'unclear', 'cycle_stage': 'unclear', 'expansion_peaks': 0, 'contraction_troughs': 0, 'avg_expansion_height': 4.08, 'max_expansion': 4.08, 'recent_peak': None, 'recent_trough': None}, 'breakout': {'potential': 'medium', 'potential_score': 0.6, 'recent_change': 0.079, 'change_direction': 'expanding', 'setup_quality': 'fair_setup'}}, 'levels': {'volatility': {'level': 'below_average', 'percentile_rank': 24.7, 'relative_to_mean': -33.4, 'statistics': {'mean': 6.12, 'std': 2.47, 'max': 12.67, 'min': 2.72}}, 'squeeze': {'is_squeeze': True, 'squeeze_periods': 5, 'squeeze_threshold': 3.97, 'squeeze_intensity': -2.62, 'squeeze_frequency': 0.272, 'squeeze_quality': 'moderate'}, 'cycles': {'avg_cycle_length': None, 'total_cycles': 0, 'expanding_time_pct': 38.3, 'contracting_time_pct': 61.7}}, 'evidence': {'clarity': 0.828, 'consistency': 0.014, 'data_quality': 0.405}, 'summary': 'BB Width 4.08% - below average volatility (25th percentile) - MODERATE SQUEEZE (5p)'}, 'aroon': {'indicator': 'Aroon', 'current': {'aroon_up': 64.29, 'aroon_down': 50.0, 'oscillator': 14.29, 'timestamp': '2025-11-08T17:15:02.921467+00:00'}, 'context': {'trend': {'current_trend': 'uptrend', 'trend_strength': 0.143, 'trend_consistency': 0.3, 'trend_duration': 1, 'separation': 14.29, 'trend_quality': 'poor'}, 'strength': {'aroon_up_strength': 'strong', 'aroon_down_strength': 'moderate', 'combined_strength': 'strong', 'up_momentum': 21.43, 'down_momentum': -7.14, 'up_evolution': 'rising', 'down_evolution': 'falling', 'dominant_indicator': 'aroon_up'}, 'parallel_movement': {'correlation': 0.131, 'movement_type': 'independent_movement', 'interpretation': 'Indicators moving independently'}}, 'levels': {'oscillator': {'current_value': 14.29, 'zone': 'neutral', 'velocity': 28.57, 'acceleration': 35.71, 'zero_crossings': 6, 'time_above_zero_pct': 36.0, 'time_below_zero_pct': 64.0, 'oscillator_interpretation': 'bullish_strengthening'}, 'crossovers': {'recent_crossovers': [{'type': 'bullish_crossover', 'periods_ago': 1, 'up_value': 64.29, 'down_value': 50.0, 'strength': 14.285714285714278, 'location': 'mid_levels'}, {'type': 'bearish_crossover', 'periods_ago': 8, 'up_value': 28.57, 'down_value': 100.0, 'strength': 71.42857142857143, 'location': 'mid_levels'}, {'type': 'bullish_crossover', 'periods_ago': 11, 'up_value': 50.0, 'down_value': 7.14, 'strength': 42.85714285714286, 'location': 'low_levels'}], 'latest_crossover': {'type': 'bullish_crossover', 'periods_ago': 1, 'up_value': 64.29, 'down_value': 50.0, 'strength': 14.285714285714278, 'location': 'mid_levels'}, 'crossover_frequency': 'high'}}, 'patterns': {}, 'divergence': None, 'evidence': {'clarity': 0.143, 'consistency': 0.3, 'data_quality': 0.43}, 'summary': 'Aroon Up: 64.3, Down: 50.0 - uptrend for 1 periods'}}, 'config_id': 'bb2560fd-b053-464f-8a58-8e254e4d36fa', 'ohlcv_summary': {'latest_price': 101648.56, 'price_change_24h': 0.14910753220629738, 'volume_24h': 113911.71329, 'date_range': {'start': '2025-10-23T04:00:00', 'end': '2025-11-08T16:00:00'}}, 'storage': {'file': {'status': 'disabled', 'path': None}, 'database': {'status': 'success', 'record_id': 439907, 'symbol': 'BTC/USDT', 'timeframe': '4h', 'indicators_stored': 4, 'candles_stored': 100, 'storage_timestamp': '2025-11-08T17:15:03.270783'}}}}}, 'timestamp': '2025-11-08T17:15:03.271268'}
2025-11-08 17:15:03.274 | DEBUG    | agent.mcp_server:query_market_data:334 -    Response: 📊 Technical Indicators (4h):
{
  "status": "success",
  "result": {
    "symbol": "BTC/USDT",
    "timeframe": "4h",
    "connector": "kucoin",
    "data_points": 100,
    "limit_used": 100,
    "timestamp": "2025-11-08T17:15:02.921530",
    "indicators": {
      "adx": {
        "indicator": "ADX",
        "current": {
          "adx": 34.11,
          "plus_di": 16.73,
          "minus_di": 28.15,
          "timestamp": "2025-11-08T17:15:02.896008+00:00"
        },
        "context": {
       ...
2025-11-08 17:15:03.337 | DEBUG    | agent.mcp_server:query_market_data:156 - 🔧 query_market_data CALLED
2025-11-08 17:15:03.338 | DEBUG    | agent.mcp_server:query_market_data:157 -    Args received: {
  "symbol": "BTC",
  "categories": "{\"technical_analysis\": [\"RSI\", \"MACD\", \"OBV\", \"VWAP\"]}",
  "timeframe": "1h",
  "scan_days": 0
}
2025-11-08 17:15:03.338 | DEBUG    | agent.mcp_server:query_market_data:305 -    Parsed technical_indicators: ['RSI', 'MACD', 'OBV', 'VWAP']
2025-11-08 17:15:03.338 | DEBUG    | agent.mcp_server:query_market_data:306 -    Parsed intelligence_sources: {}
2025-11-08 17:15:03.339 | DEBUG    | agent.mcp_server:query_market_data:309 -    Calling API with symbol=BTC, indicators=['RSI', 'MACD', 'OBV', 'VWAP'], data_sources={}, timeframe=1h
2025-11-08 17:15:03.339 | DEBUG    | agent.service_client:_retry_request:82 - Request: POST /api/v2/agent/query-market-data, kwargs: {'params': {'user_id': '00000000-0000-0000-0000-000000000000'}, 'json': {'config_id': 'bb2560fd-b053-464f-8a58-8e254e4d36fa', 'symbol': 'BTC', 'timeframe': '1h', 'indicators': ['RSI', 'MACD', 'OBV', 'VWAP']}}
2025-11-08 17:15:03.634 | DEBUG    | agent.service_client:_retry_request:84 - Response URL: http://localhost:8000/api/v2/agent/query-market-data?user_id=00000000-0000-0000-0000-000000000000
2025-11-08 17:15:03.634 | DEBUG    | agent.service_client:_retry_request:85 - Response status: 200
2025-11-08 17:15:03.635 | DEBUG    | agent.service_client:_retry_request:90 - Response data: {'status': 'success', 'data': {'technicals': {'status': 'success', 'result': {'symbol': 'BTC/USDT', 'timeframe': '1h', 'connector': 'kucoin', 'data_points': 100, 'limit_used': 150, 'timestamp': '2025-11-08T17:15:03.469251', 'indicators': {'rsi': {'indicator': 'RSI', 'period': 14, 'current': {'value': 44.89, 'timestamp': '2025-11-08T17:15:03.432654+00:00'}, 'context': {'trend': {'direction': 'sideways', 'strength': 0.081, 'velocity': 0.445, 'acceleration': 0.167}, 'ma5': 44.29, 'ma10': 46.83, 'volatility': 8.532}, 'levels': {'overbought': {'level': 70, 'status': 'far_below', 'periods_in_zone': 0, 'time_percentage': 0.0}, 'oversold': {'level': 30, 'status': 'far_above', 'periods_in_zone': 0, 'time_percentage': 1.2}, 'neutral': {'level': 50, 'status': 'below', 'distance': -5.11}, 'key_levels': [30, 50, 70], 'recent_crossovers': [{'level': 50, 'direction': 'down', 'periods_ago': 6, 'strength': 6.313233346241105}]}, 'extremes': {'recent_high': {'value': 67.33, 'periods_ago': 19.0, 'significance': 1.0}, 'recent_low': {'value': 42.47, 'periods_ago': 1.0, 'significance': 0.36037046503313847}}, 'patterns': {}, 'evidence': {'data_quality': {'total_periods': 86, 'valid_data_percentage': 86.0, 'recent_volatility': 3.59}, 'calculation_notes': 'RSI analysis based on 86 valid data points'}, 'summary': 'RSI at 44.9'}, 'macd': {'indicator': 'MACD', 'current': {'macd': -98.3053, 'signal': 16.0189, 'histogram': -114.3241, 'timestamp': '2025-11-08T17:15:03.440423+00:00'}, 'trend': {'direction': 'bearish', 'strength': 0.328, 'momentum': 'increasing', 'acceleration': 13.5856}, 'patterns': {'crossovers': {'recent_crossovers': [{'type': 'bearish_crossover', 'periods_ago': 12, 'strength': 0.03, 'strength_level': 'low'}], 'latest_crossover': {'type': 'bearish_crossover', 'periods_ago': 12, 'strength': 0.03, 'strength_level': 'low'}}, 'divergence': None}, 'levels': {'zero_line': {'current_position': 'below', 'distance_from_zero': 98.3053, 'time_above_zero_pct': 50.7, 'time_below_zero_pct': 49.3}, 'histogram': {'momentum_direction': 'increasing', 'acceleration': 13.5856, 'zero_crossings_recent': 0, 'histogram_strength': 114.32411562751415}}, 'evidence': {'data_quality': {'original_periods': {'macd': 100, 'signal': 100, 'histogram': 100, 'prices': 100}, 'aligned_periods': 67, 'valid_data_percentage': 67.0}, 'calculation_notes': 'MACD analysis based on 67 aligned data points'}, 'summary': 'MACD falling trend with decreasing momentum'}, 'obv': {'indicator': 'OBV', 'current': {'value': 5764.87, 'timestamp': '2025-11-08T17:15:03.443539+00:00'}, 'context': {'length': 14, 'relative': {'position_percentile': 60.4, 'position': 'upper_range', 'max_obv': 13397.03, 'min_obv': -5874.42}}, 'levels': {'trend': {'short_term': 'bearish', 'medium_term': 'bearish', 'long_term': 'bearish', 'consensus': 'bearish', 'velocity': 55.78, 'strength': 0.143, 'consistency': 0.556}, 'accumulation': {'timeframe_analysis': {'5p': {'score': 'strong_distribution', 'change_pct': -2.71}, '10p': {'score': 'neutral', 'change_pct': -0.29}, '20p': {'score': 'strong_distribution', 'change_pct': -39.77}}, 'overall_phase': 'distribution_phase', 'phase_strength': 'moderate'}}, 'patterns': {'momentum': {'velocity': -183.46, 'acceleration': -49.4, 'momentum_type': 'accelerating_bearish', 'roc_5p': 5.08, 'roc_10p': 8.17}, 'formations': {}, 'divergence': None, 'flow': {'recent_flow': 'distribution', 'flow_efficiency': 0.049992, 'avg_up_volume': 1340.68, 'avg_down_volume': 1325.58, 'volume_bias': 'up_days', 'volume_ratio': 1.01}}, 'evidence': {'data_quality': {'original_periods': {'obv': 100, 'prices': 100, 'volumes': 100}, 'cleaned_periods': 100, 'had_prices': True, 'had_volumes': True}, 'calculation_notes': 'OBV analysis based on 100 periods with length 14'}, 'summary': 'OBV 5765 - bearish trend, distribution detected'}, 'vwap': {'indicator': 'VWAP', 'length': 14, 'current': {'vwap_value': 102315.2248, 'price': 101856.13, 'price_distance': -459.0948, 'price_distance_pct': -0.449, 'timestamp': '2025-11-08T17:15:03.455909+00:00'}, 'context': {'trend': {'direction': 'sideways', 'strength': 0.047, 'velocity': -21.555927, 'smoothness': 0.992}, 'fair_value': {'assessment': 'fairly_valued', 'distance_pct': -0.449, 'reversion_tendency': 'low'}, 'anchored': {'direction_consistency': 0.556, 'momentum': -21.555927, 'reset_detected': False, 'behavior_quality': 'choppy'}, 'volume_profile': {'above_vwap_volume_pct': 42.4, 'below_vwap_volume_pct': 57.6, 'near_vwap_volume_pct': 34.2, 'avg_volume_above': 1253.05, 'avg_volume_below': 1393.34, 'volume_bias': 'below_vwap', 'institutional_activity': 'high'}, 'volatility': 1025.8922}, 'levels': {'price_position': {'current': 'below', 'bias': 'bearish', 'above_vwap_pct': 45.0, 'below_vwap_pct': 55.0, 'position_changes': 15}, 'deviation_bands': {'current_position': 'within_1std', 'std_devs_from_vwap': -0.45, 'upper_1std': 103341.117, 'lower_1std': 101289.3326, 'upper_2std': 104367.0091, 'lower_2std': 100263.4405}, 'key_levels': [102315.2247970364], 'recent_crossovers': []}, 'extremes': {'recent_high': {'value': 102932.9923, 'periods_ago': 14.0, 'significance': 1.0}, 'recent_low': {'value': 101339.9957, 'periods_ago': 19.0, 'significance': 1.0}}, 'patterns': {'volume_clustering': {'type': 'high_institutional_activity', 'near_vwap_pct': 34.2, 'description': 'High volume clustering near VWAP - institutional activity'}}, 'evidence': {'data_quality': {'aligned_periods': 100, 'had_volumes': True, 'volume_profile_available': True, 'support_resistance_touches': 28}, 'calculation_notes': 'VWAP analysis based on 100 aligned price/VWAP periods'}, 'summary': 'VWAP 102315.2248, price below - fairly valued'}}, 'config_id': 'bb2560fd-b053-464f-8a58-8e254e4d36fa', 'ohlcv_summary': {'latest_price': 101856.13, 'price_change_24h': -0.5283254060270354, 'volume_24h': 17312.51766, 'date_range': {'start': '2025-11-04T13:00:00', 'end': '2025-11-08T16:00:00'}}, 'storage': {'file': {'status': 'disabled', 'path': None}, 'database': {'status': 'success', 'record_id': 439906, 'symbol': 'BTC/USDT', 'timeframe': '1h', 'indicators_stored': 4, 'candles_stored': 100, 'storage_timestamp': '2025-11-08T17:15:03.631572'}}}}}, 'timestamp': '2025-11-08T17:15:03.632158'}
2025-11-08 17:15:03.636 | DEBUG    | agent.mcp_server:query_market_data:334 -    Response: 📊 Technical Indicators (1h):
{
  "status": "success",
  "result": {
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "connector": "kucoin",
    "data_points": 100,
    "limit_used": 150,
    "timestamp": "2025-11-08T17:15:03.469251",
    "indicators": {
      "rsi": {
        "indicator": "RSI",
        "period": 14,
        "current": {
          "value": 44.89,
          "timestamp": "2025-11-08T17:15:03.432654+00:00"
        },
        "context": {
          "trend": {
            "direct...
2025-11-08 17:15:44.469 | INFO     | agent.mcp_server:wait_for:979 - Agent waiting 30m: Market in consolidation squeeze with conflicting signals (Aroon bullish vs MACD/OBV bearish). Stale ggShot signals (2+ days old). Waiting for volatility breakout direction and clearer setup confirmation. Strategy requires high conviction - current mixed signals don't meet threshold.
