# UI/UX Design Context for ggbots Forge

You are a senior UI/UX designer with expertise in financial trading interfaces, real-time dashboards, and autonomous system management. Your specialty is creating intuitive, professional interfaces for complex technical products that need to balance sophistication with usability.

## Project Context

**ggbots** is an autonomous AI trading platform that allows users to create, customize, and deploy AI trading agents that operate 24/7. The platform combines browser automation, advanced reasoning LLMs, and sophisticated execution engines.

## Architecture Overview

The system follows a **three-agent pipeline**:
```
Market Data � Extraction Agent � Decision Agent � Trading Agent � Exchange
     �              �               �              �           �
   Sources     Market Analysis   AI Reasoning   Execution   Results
```

## Current Technical Implementation

### The Forge (Our Focus)
- **Single-page application** replacing legacy dashboard
- **Multi-bot architecture** - users can have multiple trading bots with seamless switching
- **Real-time updates** via Server-Sent Events (SSE)
- **Local state management** - clean, no global store complexity
- **Phase 1 complete** - data foundation implemented
- **Phase 2 needed** - UI/UX design system and layout

### Data Architecture
- **Bot Configuration** - User's trading strategy settings (JSON blob)
- **Operational Data** - Real-time updates (positions, decisions, execution status)
- **Multi-bot switching** - `selectedConfigId` drives all page content

## Core User Actions & Data Flows

### Primary Actions Users Must Perform:
1. **Bot Management**
   - View all their bots with status indicators
   - Switch between multiple bots seamlessly
   - Start/stop individual bots
   - Create new bots or delete existing ones

2. **Configuration Editing** (Missing - Needs Design)
   - **Market Data Sources**: Multi-category system with data sources (Technical Analysis, Signals, Sentiment, News, Influencers, On-chain Analytics, Fundamental Analysis) where each data source contains specific data points (e.g., Technical Analysis includes RSI, MACD, Bollinger Bands; Signals includes ggShot feeds; etc.), plus timeframe selection (5m, 1h, 1d)
   - **AI Decision Logic**: Customize system/user prompts, set analysis frequency
   - **Risk Management**: Position sizing, stop-loss/take-profit percentages, max positions
   - **LLM Configuration**: Choose AI provider (OpenAI, DeepSeek), model selection, API keys
   - **Trading Setup**: Exchange selection, execution mode (paper vs live)

3. **Real-Time Monitoring**
   - **Bot Status**: Current execution phase (extraction � decision � trading � idle)
   - **Live Positions**: Open trades with real-time P&L updates
   - **AI Decisions**: Recent decision reasoning with confidence scores
   - **Countdown Timers**: Next execution schedule
   - **Performance Metrics**: Account balance, win rate, total P&L

### Key Data States:
- **Configuration Data**: User settings (editable, saved to database)
- **Operational Data**: Real-time bot activity (read-only, SSE updates)
- **Bot States**: active/inactive, execution phases (extraction/decision/trading/idle)

## Design Constraints & Requirements

### Technical Constraints:
- **React/Next.js** with TypeScript
- **Tailwind CSS** for styling
- **Real-time updates** via SSE (not WebSocket)
- **Multi-bot support** from day one
- **Mobile responsive** design needed

### User Experience Goals:
- **Professional trading interface** - users are serious traders
- **Reduced cognitive load** - complex system made simple
- **Immediate feedback** - all actions show instant responses
- **Trust indicators** - users need confidence their autonomous agents are working
- **Configuration complexity** - many settings but shouldn't feel overwhelming

### Current Pain Points to Solve:
- Legacy dashboard has 600+ line complexity and architectural debt
- Need elegant separation of configuration editing vs real-time monitoring
- Users switch between multiple bots frequently
- Complex configuration options need to be approachable

## Design Challenge

**Primary Question**: How do we create an elegant, professional interface that allows users to:
1. **Easily manage multiple autonomous trading bots**
2. **Configure complex trading strategies** without feeling overwhelmed
3. **Monitor real-time performance** with confidence and clarity
4. **Feel in control** of their autonomous agents

Consider modern trading platforms (TradingView, Interactive Brokers), DevOps dashboards (Vercel, Railway), and AI management tools (OpenAI Playground) as inspiration.

**Deliverable Needed**: UI/UX recommendations for layout, component organization, information hierarchy, and interaction patterns that would make this complex autonomous trading system feel intuitive and trustworthy.



id: 1
event: dashboard
data: {"bots": [{"config_id": "18665f58-fb3c-4655-a648-449427be0073", "user_id": "00000000-0000-0000-0000-000000000000", "config_name": "ggShot-filter", "state": "inactive", "config_data": {"user_id": "00000000-0000-0000-0000-000000000000", "config_id": "18665f58-fb3c-4655-a648-449427be0073", "created_at": "2025-09-11T19:52:47.207740+00:00", "updated_at": "2025-09-12T00:17:25.217798", "config_data": {"trading": {"leverage": 1, "execution_mode": "paper", "exchange_config": {"api_key": "", "secret_key": "", "exchange_type": "cex", "selected_exchange": "binance"}, "position_sizing": {"method": "fixed_usd", "account_percent": 5, "fixed_amount_usd": 100, "max_position_percent": 10}, "risk_management": {"max_positions": 1, "max_daily_loss_usd": 500, "default_stop_loss_percent": 5, "default_take_profit_percent": 10}}, "decision": {"user_prompt": "## Pillar 0: Market Regime Analysis\nObjective: Filter out choppy/ranging markets where breakout signals frequently fail\n\nIndicators:\n- Aroon (14-period): Trend vs ranging detection\n  - Analysis: When both Aroon Up and Aroon Down are in middle range (30-70), market is consolidating. When one line is high (> 70) while the other is low (< 30), market is trending strongly\n  - Critical Flag: Both Aroon lines between 30-70 indicates HIGH RISK for ggShot signals\n- ADX (14-period): Trend strength confirmation\n  - Analysis: ADX > 25 indicates strong trending conditions, ADX < 20 suggests weak/ranging market\n  - Context: Low ADX combined with middle-range Aroon confirms dangerous ranging conditions\n\nCritical Logic: ggShot signals are designed for breakout/momentum scenarios:\n- Highest Risk: Aroon ranging (both 30-70) AND ADX < 20 (weak trend)\n- High Risk: Either Aroon ranging OR ADX < 20\n- Low Risk: Strong Aroon trend (one >70, other <30) AND ADX > 25\n\n### Pillar 1: Signal Confirmation  \nObjective: Seek confluence of evidence supporting the signal's direction\n\nIndicators:\n- RSI Multi-Timeframe Analysis:\n  - Signal timeframe RSI: Momentum confirmation for entry timing\n  - Analysis: For LONG signals, RSI 40-60 is ideal (not oversold, room to run). For SHORT signals, RSI 40-60 is also ideal\n  - Avoid: RSI extremes (>80 or <20) suggest overextension risk\n- Bollinger Band Position:\n  - Price position relative to bands confirms signal direction\n  - Analysis: For LONG signals, price approaching or touching lower band then bouncing supports upward move. For SHORT signals, price at upper band supports downward move\n  - Context: Signals in middle of bands have less directional conviction\n\n### Pillar 2: Broader Context\nObjective: Ensure trade is well-positioned and has room to run\n\nIndicators:\n- Multi-Timeframe RSI Context:\n  - Compare signal timeframe RSI with higher timeframe (4h) RSI\n  - Analysis: Higher timeframe overbought (RSI > 70) for LONG signals is a significant contradiction. Higher timeframe oversold (RSI < 30) for SHORT signals is a contradiction\n  - Ideal: Both timeframes showing non-extreme RSI (30-70 range)\n- ADX Trend Strength:\n  - Confirms we're in a trending environment suitable for breakouts\n  - Analysis: ADX > 25 provides confidence that trends can sustain. ADX > 30 is very strong trending environment\n\n### Pillar 3: Tactical Caution\nObjective: Identify immediate risks that could stop out an otherwise good setup\n\nIndicators:\n- Bollinger Band Overextension:\n  - Statistical overextension detection\n  - Analysis: Prices far outside bands (beyond +2 sigma) indicate potential overextension with higher mean reversion risk\n  - Caution: Signals when price is already beyond bands carry higher reversal risk\n- ATR Volatility Assessment:\n  - Market volatility/choppiness measurement  \n  - Analysis: Exceptionally high ATR (relative to recent periods) indicates chaotic conditions that may increase stop-loss risk\n  - Context: Very low ATR might indicate upcoming volatility expansion\n\n## Decision Framework:\n- **HIGH CONFIDENCE (0.8-1.0)**: All pillars align - trending market (Aroon + ADX), RSI in good zone, no overextension, normal volatility\n- **MEDIUM CONFIDENCE (0.6-0.8)**: 3 of 4 pillars align, minor contradictions\n- **LOW CONFIDENCE (0.4-0.6)**: 2 of 4 pillars align, significant contradictions present\n- **WAIT (0.0-0.4)**: Major contradictions or ranging market conditions detected", "system_prompt": "You are an expert cryptocurrency trader analyzing {SYMBOL} at current price {CURRENT_PRICE}. Your analysis is based on the following market data:\n\n{MARKET_DATA}\n\nProvide clear, reasoned responses about trading actions. Format your response with clear sections for Decision, Confidence, and Reasoning.", "analysis_frequency": "signal_driven"}, "extraction": {"selected_data_sources": {"influencer_kol": {"timeframes": ["1h"], "data_points": []}, "onchain_analytics": {"timeframes": ["1h"], "data_points": []}, "technical_analysis": {"timeframes": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"], "data_points": ["RSI", "Aroon", "ADX", "BB", "ATR"]}, "signals_group_chats": {"timeframes": ["15m"], "data_points": ["ggshot"]}, "fundamental_analysis": {"timeframes": ["1d"], "data_points": []}, "news_and_regulations": {"timeframes": ["1d"], "data_points": []}, "sentiment_and_trends": {"timeframes": ["1h"], "data_points": []}}}, "llm_config": {"model": "deepseek-r1", "provider": "openai", "use_own_key": false, "use_platform_keys": true}, "config_type": "signal_validation", "selected_pair": "BTC/USDT", "schema_version": "2.1", "telegram_integration": {"listener": {"api_id": "", "enabled": false, "api_hash": "", "session_name": "ggbot_session", "source_channels": []}, "publisher": {"enabled": true, "bot_token": "7320956370:AAGMatLFf_myZxmfuN7v7EwToxBter_GHW0", "filter_channel": "-1002507736579", "message_template": "\ud83d\udd25 {ACTION} {SYMBOL} - Confidence: {CONFIDENCE}\n{REASONING}", "include_reasoning": true, "confidence_threshold": 0.7, "include_market_context": true}}}, "config_name": "ggShot-filter"}, "created_at": "2025-09-11T19:52:47.20774+00:00", "updated_at": "2025-09-13T12:31:17.858437+00:00", "execution_status": null, "status_color": "gray", "status_message": "Bot inactive", "show_spinner": false, "next_run": null, "is_scheduled": false}], "positions": [], "decisions": [], "accounts": [{"config_id": "18665f58-fb3c-4655-a648-449427be0073", "account_id": "707adc89-0aa4-4593-b85c-eb2fdf16d960", "current_balance": 9899.82, "total_pnl": -0.06, "total_trades": 1, "win_trades": 0, "loss_trades": 1, "open_positions": 1, "updated_at": "2025-09-12T04:54:26.816468+00:00"}], "timestamp": "2025-09-13T12:31:18.004147+00:00"}
