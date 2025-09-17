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
data: {"bots": [{"config_id": "18665f58-fb3c-4655-a648-449427be0073", "user_id": "3d47c173-9234-47c7-b57b-9159c9df5dbd", "config_name": "ggShot-filter", "state": "inactive", "config_data": {"user_id": "3d47c173-9234-47c7-b57b-9159c9df5dbd", "config_id": "18665f58-fb3c-4655-a648-449427be0073", "created_at": "2025-09-11T19:52:47.207740+00:00", "updated_at": "2025-09-12T00:17:25.217798", "config_data": {"trading": {"leverage": 1, "execution_mode": "paper", "exchange_config": {"api_key": "", "secret_key": "", "exchange_type": "cex", "selected_exchange": "binance"}, "position_sizing": {"method": "fixed_usd", "account_percent": 5, "fixed_amount_usd": 100, "max_position_percent": 10}, "risk_management": {"max_positions": 1, "max_daily_loss_usd": 500, "default_stop_loss_percent": 5, "default_take_profit_percent": 10}}, "decision": {"user_prompt": "## Pillar 0: Market Regime Analysis\nObjective: Filter out choppy/ranging markets where breakout signals frequently fail\n\nIndicators:\n- Aroon (14-period): Trend vs ranging detection\n  - Analysis: When both Aroon Up and Aroon Down are in middle range (30-70), market is consolidating. When one line is high (> 70) while the other is low (< 30), market is trending strongly\n  - Critical Flag: Both Aroon lines between 30-70 indicates HIGH RISK for ggShot signals\n- ADX (14-period): Trend strength confirmation\n  - Analysis: ADX > 25 indicates strong trending conditions, ADX < 20 suggests weak/ranging market\n  - Context: Low ADX combined with middle-range Aroon confirms dangerous ranging conditions\n\nCritical Logic: ggShot signals are designed for breakout/momentum scenarios:\n- Highest Risk: Aroon ranging (both 30-70) AND ADX < 20 (weak trend)\n- High Risk: Either Aroon ranging OR ADX < 20\n- Low Risk: Strong Aroon trend (one >70, other <30) AND ADX > 25\n\n### Pillar 1: Signal Confirmation  \nObjective: Seek confluence of evidence supporting the signal's direction\n\nIndicators:\n- RSI Multi-Timeframe Analysis:\n  - Signal timeframe RSI: Momentum confirmation for entry timing\n  - Analysis: For LONG signals, RSI 40-60 is ideal (not oversold, room to run). For SHORT signals, RSI 40-60 is also ideal\n  - Avoid: RSI extremes (>80 or <20) suggest overextension risk\n- Bollinger Band Position:\n  - Price position relative to bands confirms signal direction\n  - Analysis: For LONG signals, price approaching or touching lower band then bouncing supports upward move. For SHORT signals, price at upper band supports downward move\n  - Context: Signals in middle of bands have less directional conviction\n\n### Pillar 2: Broader Context\nObjective: Ensure trade is well-positioned and has room to run\n\nIndicators:\n- Multi-Timeframe RSI Context:\n  - Compare signal timeframe RSI with higher timeframe (4h) RSI\n  - Analysis: Higher timeframe overbought (RSI > 70) for LONG signals is a significant contradiction. Higher timeframe oversold (RSI < 30) for SHORT signals is a contradiction\n  - Ideal: Both timeframes showing non-extreme RSI (30-70 range)\n- ADX Trend Strength:\n  - Confirms we're in a trending environment suitable for breakouts\n  - Analysis: ADX > 25 provides confidence that trends can sustain. ADX > 30 is very strong trending environment\n\n### Pillar 3: Tactical Caution\nObjective: Identify immediate risks that could stop out an otherwise good setup\n\nIndicators:\n- Bollinger Band Overextension:\n  - Statistical overextension detection\n  - Analysis: Prices far outside bands (beyond +2 sigma) indicate potential overextension with higher mean reversion risk\n  - Caution: Signals when price is already beyond bands carry higher reversal risk\n- ATR Volatility Assessment:\n  - Market volatility/choppiness measurement  \n  - Analysis: Exceptionally high ATR (relative to recent periods) indicates chaotic conditions that may increase stop-loss risk\n  - Context: Very low ATR might indicate upcoming volatility expansion\n\n## Decision Framework:\n- **HIGH CONFIDENCE (0.8-1.0)**: All pillars align - trending market (Aroon + ADX), RSI in good zone, no overextension, normal volatility\n- **MEDIUM CONFIDENCE (0.6-0.8)**: 3 of 4 pillars align, minor contradictions\n- **LOW CONFIDENCE (0.4-0.6)**: 2 of 4 pillars align, significant contradictions present\n- **WAIT (0.0-0.4)**: Major contradictions or ranging market conditions detected", "system_prompt": "You are an expert cryptocurrency trader analyzing {SYMBOL} at current price {CURRENT_PRICE}. Your analysis is based on the following market data:\n\n{MARKET_DATA}\n\nProvide clear, reasoned responses about trading actions. Format your response with clear sections for Decision, Confidence, and Reasoning.", "analysis_frequency": "signal_driven"}, "extraction": {"selected_data_sources": {"influencer_kol": {"timeframes": ["1h"], "data_points": []}, "onchain_analytics": {"timeframes": ["1h"], "data_points": []}, "technical_analysis": {"timeframes": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"], "data_points": ["RSI", "Aroon", "ADX", "BB", "ATR"]}, "signals_group_chats": {"timeframes": ["15m"], "data_points": ["ggshot"]}, "fundamental_analysis": {"timeframes": ["1d"], "data_points": []}, "news_and_regulations": {"timeframes": ["1d"], "data_points": []}, "sentiment_and_trends": {"timeframes": ["1h"], "data_points": []}}}, "llm_config": {"model": "deepseek-r1", "provider": "openai", "use_own_key": false, "use_platform_keys": true}, "config_type": "signal_validation", "selected_pair": "BTC/USDT", "schema_version": "2.1", "telegram_integration": {"listener": {"api_id": "", "enabled": false, "api_hash": "", "session_name": "ggbot_session", "source_channels": []}, "publisher": {"enabled": true, "bot_token": "7320956370:AAGMatLFf_myZxmfuN7v7EwToxBter_GHW0", "filter_channel": "-1002507736579", "message_template": "\ud83d\udd25 {ACTION} {SYMBOL} - Confidence: {CONFIDENCE}\n{REASONING}", "include_reasoning": true, "confidence_threshold": 0.7, "include_market_context": true}}}, "config_name": "ggShot-filter"}, "created_at": "2025-09-11T19:52:47.20774+00:00", "updated_at": "2025-09-13T12:31:17.858437+00:00", "execution_status": null, "status_color": "gray", "status_message": "Bot inactive", "show_spinner": false, "next_run": null, "is_scheduled": false}], "positions": [], "decisions": [], "accounts": [{"config_id": "18665f58-fb3c-4655-a648-449427be0073", "account_id": "707adc89-0aa4-4593-b85c-eb2fdf16d960", "current_balance": 9899.82, "total_pnl": -0.06, "total_trades": 1, "win_trades": 0, "loss_trades": 1, "open_positions": 1, "updated_at": "2025-09-12T04:54:26.816468+00:00"}], "timestamp": "2025-09-13T12:31:18.004147+00:00"}


● Looking at the issue, we have a disconnect between the new Forge architecture (local
  state only) and the old dashboard's data fetching patterns.

  🔍 The Disconnect:

  Old Dashboard Pattern:

  The old GGBotConfig component directly fetched data sources from APIs:
  - Used React hooks to fetch data sources on component mount
  - Had loading states and error handling built-in
  - Fetched data points dynamically from the backend

  New Forge Pattern:

  The Forge follows local state only architecture:
  - All data comes down from the parent (page.tsx)
  - Components are pure/stateless - they only receive props
  - No direct API calls from child components

  🎯 The Missing Piece:

  page.tsx should be fetching data sources alongside the other data it already fetches:

  // In page.tsx - alongside existing fetches:
  const [allBots, setAllBots] = useState<BotConfiguration[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [positions, setPositions] = useState<Position[]>([])
  const [decisions, setDecisions] = useState<Decision[]>([])

  // MISSING:
  const [dataSources, setDataSources] = useState<DataSource[]>([])

  Then pass it down to ConfigureLayout → MarketDataSelector.

  🔧 The Fix:

  1. Add data sources state to page.tsx
  2. Fetch data sources in the same useEffect where we fetch configurations
  3. Pass data sources down through the component tree:
  page.tsx → ConfigureLayout → MarketDataSelector

  🤔 Why this wasn't obvious:

  The old GGBotConfig was a monolithic component that handled its own data fetching.
  The new Forge architecture separates concerns - data fetching happens at the top
  level, pure components receive props.

  Should I implement the data sources fetching in page.tsx? We need to:
  1. Add dataSources state to page.tsx
  2. Fetch from the API (probably /api/data-sources or similar)
  3. Pass it down as props through ConfigureLayout to MarketDataSelector



---

## 🛠️ Database Fix Required - Bot Creation Constraint Issue

**Problem**: Users can't create multiple bots due to restrictive database constraint `idx_configurations_user_type` that only allows one bot per config_type per user.

**Solution**: Run this SQL in Supabase SQL Editor to enable 7 bots total per user:

```sql
-- Remove the restrictive per-type constraint
DROP INDEX IF EXISTS idx_configurations_user_type;

-- Create a function to check bot limit
CREATE OR REPLACE FUNCTION check_user_bot_limit()
RETURNS TRIGGER AS $$
BEGIN
  IF (SELECT COUNT(*) FROM configurations WHERE user_id = NEW.user_id) > 7 THEN
    RAISE EXCEPTION 'User cannot have more than 7 bots total';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to enforce the limit
DROP TRIGGER IF EXISTS trigger_check_user_bot_limit ON configurations;
CREATE TRIGGER trigger_check_user_bot_limit
  BEFORE INSERT ON configurations
  FOR EACH ROW
  EXECUTE FUNCTION check_user_bot_limit();
```

**What this fixes:**
- ✅ Users can create multiple autonomous_trading bots
- ✅ Users can create multiple signal_validation bots
- ✅ Maximum 7 total bots per user (reasonable limit)
- ✅ New bots appear immediately without page refresh
- ✅ No data loss - existing bots unchanged



id: 6
event: dashboard
data: {"bots": [{"config_id": "b998e272-27fa-41b8-8a1e-a3b23fc88066", "user_id": "55307c6c-cc12-44d0-8e0a-040ed94bf71c", "config_name": "Default ggbot", "config_type": "autonomous_trading", "state": "active", "config_data": {"schema_version": "2.1", "config_type": "autonomous_trading", "selected_pair": "BTC/USDT", "extraction": {"selected_data_sources": {"technical_analysis": {"timeframes": ["1h"], "data_points": ["RSI"]}}}, "decision": {"user_prompt": "if RSI 1hr below 50 enter long, if above enter short", "system_prompt": "You are an expert cryptocurrency trader. Analyze the provided market data and provide clear, reasoned responses about trading actions. Format your response with clear sections for Decision, Confidence, and Reasoning.", "analysis_frequency": "5m"}, "trading": {"leverage": 1, "execution_mode": "paper", "exchange_config": {"api_key": "", "secret_key": "", "exchange_type": "cex", "selected_exchange": "binance"}, "position_sizing": {"method": "fixed_usd", "account_percent": 5, "fixed_amount_usd": 100, "max_position_percent": 10}, "risk_management": {"max_positions": 1, "max_daily_loss_usd": 500, "default_stop_loss_percent": 5, "default_take_profit_percent": 10}}, "llm_config": {"model": "deepseek-reasoner", "provider": "deepseek", "use_own_key": false, "use_platform_keys": true}, "telegram_integration": {}}, "created_at": "2025-09-16T08:02:50.830902+00:00", "updated_at": "2025-09-16T14:49:21.794394+00:00", "execution_status": null, "status_color": "green", "status_message": "Monitoring markets...", "show_spinner": false, "next_run": "2025-09-16T16:25:30Z", "is_scheduled": true}, {"config_id": "0121eef2-d70a-4680-b785-e5f7aa4b81b6", "user_id": "55307c6c-cc12-44d0-8e0a-040ed94bf71c", "config_name": "ggbot 2", "config_type": "autonomous_trading", "state": "inactive", "config_data": {"schema_version": "2.1", "config_type": "autonomous_trading", "selected_pair": "BTC/USDT", "extraction": {"selected_data_sources": {"technical_analysis": {"timeframes": ["1h"], "data_points": ["RSI"]}}}, "decision": {"user_prompt": "if RSI 1hr below 50 enter long, if above enter short", "system_prompt": "You are an expert cryptocurrency trader. Analyze the provided market data and provide clear, reasoned responses about trading actions. Format your response with clear sections for Decision, Confidence, and Reasoning.", "analysis_frequency": "1h"}, "trading": {"leverage": 1, "execution_mode": "paper", "exchange_config": {"api_key": "", "secret_key": "", "exchange_type": "cex", "selected_exchange": "binance"}, "position_sizing": {"method": "fixed_usd", "account_percent": 5, "fixed_amount_usd": 100, "max_position_percent": 10}, "risk_management": {"max_positions": 1, "max_daily_loss_usd": 500, "default_stop_loss_percent": 5, "default_take_profit_percent": 10}}, "llm_config": {"model": "deepseek-reasoner", "provider": "deepseek", "use_own_key": false, "use_platform_keys": true}, "telegram_integration": {}}, "created_at": "2025-09-16T14:52:16.303577+00:00", "updated_at": "2025-09-16T14:52:18.242817+00:00", "execution_status": null, "status_color": "gray", "status_message": "Bot inactive", "show_spinner": false, "next_run": null, "is_scheduled": false}], "positions": [], "decisions": [], "accounts": [{"config_id": "b998e272-27fa-41b8-8a1e-a3b23fc88066", "account_id": "5df492a1-28fb-4406-abaa-032775fbcd51", "current_balance": 10000.0, "total_pnl": 0.0, "total_trades": 0, "win_trades": 0, "loss_trades": 0, "open_positions": 0, "updated_at": "2025-09-16T08:02:51.347896+00:00", "unrealized_pnl": 0.0, "daily_pnl": 0.0, "portfolio_return_pct": 0.0, "total_balance": 10000.0, "available_balance": 10000.0, "position_value": 0.0, "win_rate": 0, "avg_win": 0, "avg_loss": 0, "largest_win": 0, "largest_loss": 0, "sharpe_ratio": null}, {"config_id": "0121eef2-d70a-4680-b785-e5f7aa4b81b6", "account_id": "2771a0a6-e60c-4f07-984c-4b69b7d85a18", "current_balance": 10000.0, "total_pnl": 0.0, "total_trades": 0, "win_trades": 0, "loss_trades": 0, "open_positions": 0, "updated_at": "2025-09-16T14:52:17.851983+00:00", "unrealized_pnl": 0.0, "daily_pnl": 0.0, "portfolio_return_pct": 0.0, "total_balance": 10000.0, "available_balance": 10000.0, "position_value": 0.0, "win_rate": 0, "avg_win": 0, "avg_loss": 0, "largest_win": 0, "largest_loss": 0, "sharpe_ratio": null}], "timestamp": "2025-09-16T16:20:36.958181+00:00"}

:keepalive 1758039637

id: 7
event: dashboard
data: {"bots": [{"config_id": "b998e272-27fa-41b8-8a1e-a3b23fc88066", "user_id": "55307c6c-cc12-44d0-8e0a-040ed94bf71c", "config_name": "Default ggbot", "config_type": "autonomous_trading", "state": "active", "config_data": {"schema_version": "2.1", "config_type": "autonomous_trading", "selected_pair": "BTC/USDT", "extraction": {"selected_data_sources": {"technical_analysis": {"timeframes": ["1h"], "data_points": ["RSI"]}}}, "decision": {"user_prompt": "if RSI 1hr below 50 enter long, if above enter short", "system_prompt": "You are an expert cryptocurrency trader. Analyze the provided market data and provide clear, reasoned responses about trading actions. Format your response with clear sections for Decision, Confidence, and Reasoning.", "analysis_frequency": "5m"}, "trading": {"leverage": 1, "execution_mode": "paper", "exchange_config": {"api_key": "", "secret_key": "", "exchange_type": "cex", "selected_exchange": "binance"}, "position_sizing": {"method": "fixed_usd", "account_percent": 5, "fixed_amount_usd": 100, "max_position_percent": 10}, "risk_management": {"max_positions": 1, "max_daily_loss_usd": 500, "default_stop_loss_percent": 5, "default_take_profit_percent": 10}}, "llm_config": {"model": "deepseek-reasoner", "provider": "deepseek", "use_own_key": false, "use_platform_keys": true}, "telegram_integration": {}}, "created_at": "2025-09-16T08:02:50.830902+00:00", "updated_at": "2025-09-16T14:49:21.794394+00:00", "execution_status": null, "status_color": "green", "status_message": "Monitoring markets...", "show_spinner": false, "next_run": "2025-09-16T16:25:30Z", "is_scheduled": true}, {"config_id": "0121eef2-d70a-4680-b785-e5f7aa4b81b6", "user_id": "55307c6c-cc12-44d0-8e0a-040ed94bf71c", "config_name": "ggbot 2", "config_type": "autonomous_trading", "state": "inactive", "config_data": {"schema_version": "2.1", "config_type": "autonomous_trading", "selected_pair": "BTC/USDT", "extraction": {"selected_data_sources": {"technical_analysis": {"timeframes": ["1h"], "data_points": ["RSI"]}}}, "decision": {"user_prompt": "if RSI 1hr below 50 enter long, if above enter short", "system_prompt": "You are an expert cryptocurrency trader. Analyze the provided market data and provide clear, reasoned responses about trading actions. Format your response with clear sections for Decision, Confidence, and Reasoning.", "analysis_frequency": "1h"}, "trading": {"leverage": 1, "execution_mode": "paper", "exchange_config": {"api_key": "", "secret_key": "", "exchange_type": "cex", "selected_exchange": "binance"}, "position_sizing": {"method": "fixed_usd", "account_percent": 5, "fixed_amount_usd": 100, "max_position_percent": 10}, "risk_management": {"max_positions": 1, "max_daily_loss_usd": 500, "default_stop_loss_percent": 5, "default_take_profit_percent": 10}}, "llm_config": {"model": "deepseek-reasoner", "provider": "deepseek", "use_own_key": false, "use_platform_keys": true}, "telegram_integration": {}}, "created_at": "2025-09-16T14:52:16.303577+00:00", "updated_at": "2025-09-16T14:52:18.242817+00:00", "execution_status": null, "status_color": "gray", "status_message": "Bot inactive", "show_spinner": false, "next_run": null, "is_scheduled": false}], "positions": [], "decisions": [], "accounts": [{"config_id": "b998e272-27fa-41b8-8a1e-a3b23fc88066", "account_id": "5df492a1-28fb-4406-abaa-032775fbcd51", "current_balance": 10000.0, "total_pnl": 0.0, "total_trades": 0, "win_trades": 0, "loss_trades": 0, "open_positions": 0, "updated_at": "2025-09-16T08:02:51.347896+00:00", "unrealized_pnl": 0.0, "daily_pnl": 0.0, "portfolio_return_pct": 0.0, "total_balance": 10000.0, "available_balance": 10000.0, "position_value": 0.0, "win_rate": 0, "avg_win": 0, "avg_loss": 0, "largest_win": 0, "largest_loss": 0, "sharpe_ratio": null}, {"config_id": "0121eef2-d70a-4680-b785-e5f7aa4b81b6", "account_id": "2771a0a6-e60c-4f07-984c-4b69b7d85a18", "current_balance": 10000.0, "total_pnl": 0.0, "total_trades": 0, "win_trades": 0, "loss_trades": 0, "open_positions": 0, "updated_at": "2025-09-16T14:52:17.851983+00:00", "unrealized_pnl": 0.0, "daily_pnl": 0.0, "portfolio_return_pct": 0.0, "total_balance": 10000.0, "available_balance": 10000.0, "position_value": 0.0, "win_rate": 0, "avg_win": 0, "avg_loss": 0, "largest_win": 0, "largest_loss": 0, "sharpe_ratio": null}], "timestamp": "2025-09-16T16:20:42.098767+00:00"}

