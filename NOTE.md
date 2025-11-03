page-fe8724943ac1b76b.js:1 🔄 Poll skipped: {selectedConfigId: null, configType: undefined, userId: undefined}
page-fe8724943ac1b76b.js:1 🔄 Poll skipped: {selectedConfigId: null, configType: undefined, userId: undefined}
page-fe8724943ac1b76b.js:1 🔄 Poll skipped: {selectedConfigId: null, configType: undefined, userId: undefined}
page-fe8724943ac1b76b.js:1 🔍 API Call: getUserProfile to https://ggbots-api.nightingale.business/api/v2/user/profile
page-fe8724943ac1b76b.js:1 🔄 Poll skipped: {selectedConfigId: null, configType: undefined, userId: '00000000-0000-0000-0000-000000000000'}
page-fe8724943ac1b76b.js:1 📡 Response status: 200 OK
page-fe8724943ac1b76b.js:1 ✅ User profile loaded: {status: 'success', profile: {…}}
page-fe8724943ac1b76b.js:1 🔍 API Call: getDataSourcesWithPoints to https://ggbots-api.nightingale.business/api/v2/data-sources-with-points
page-fe8724943ac1b76b.js:1 🔄 Switched to bot: d13d5536-2498-4f27-b2bc-e4f98958e1d8 Test Agent
page-fe8724943ac1b76b.js:1 🔄 Poll skipped: {selectedConfigId: 'd13d5536-2498-4f27-b2bc-e4f98958e1d8', configType: undefined, userId: '00000000-0000-0000-0000-000000000000'}
page-fe8724943ac1b76b.js:1 ✅ SSE connected
page-fe8724943ac1b76b.js:1 📡 Response status: 200 OK
page-fe8724943ac1b76b.js:1 ✅ Data sources loaded: {status: 'success', data_sources: Array(7), paid_data_points: Array(1), count: 7}
page-fe8724943ac1b76b.js:1 premium_llms permission check: {can_use_premium_features: true, requires_own_llm_keys: false, hasAccess: true}
page-fe8724943ac1b76b.js:1 🔧 Starting edit mode for bot: d13d5536-2498-4f27-b2bc-e4f98958e1d8
page-fe8724943ac1b76b.js:1 🔧 Bot data being loaded into editing state: {
  "config_id": "d13d5536-2498-4f27-b2bc-e4f98958e1d8",
  "user_id": "00000000-0000-0000-0000-000000000000",
  "config_name": "Test Agent",
  "config_type": "agent",
  "state": "inactive",
  "trading_mode": "aster",
  "symphony_agent_id": null,
  "config_data": {
    "schema_version": "2.1",
    "selected_pair": "BTC/USDT",
    "extraction": {},
    "decision": {},
    "trading": {
      "leverage": 1,
      "execution_mode": "paper",
      "exchange_config": {
        "exchange_type": "cex",
        "selected_exchange": "binance"
      },
      "position_sizing": {
        "method": "confidence_based",
        "max_position_percent": 10
      },
      "risk_management": {
        "max_positions": 5,
        "default_stop_loss_percent": 3,
        "default_take_profit_percent": 6
      }
    },
    "llm_config": {
      "provider": "default",
      "use_own_key": false,
      "use_platform_keys": true
    },
    "telegram_integration": {},
    "agent_strategy": {
      "content": "High-Frequency Momentum Scalping Strategy:\n- Assets: BTC + ETH with dual-asset rotation\n- Entry: 4+ signals from RSI (35-65), MACD momentum, Stochastic, funding rates (<0.05%), whale activity, twitter sentiment (≥0.55)\n- Position Size: $800-1500 per trade (8-15% of account)\n- Leverage: 2-3x on confirmed signals\n- Stop Loss: 1.5-2% below entry\n- Take Profit: Scaled exits (TP1: +2-3%, TP2: +4-6%, TP3: +8-12%)\n- Monitoring: Every 30-60 minutes, query technical + macro + on-chain data\n- Exits: Hit TP levels, strict SL discipline, signal invalidation, max 8-hour holds\n- Target Win Rate: 58-65%\n- Expected Frequency: 4-8 trades per day\n- Max Concurrent: 3-4 positions (BTC + ETH rotation)\n- Daily Target: +0.5-1.5% return",
      "version": 1,
      "last_updated_at": "2025-11-01T19:29:05.896732",
      "last_updated_by": "user",
      "performance_log": [],
      "autonomously_editable": false
    }
  },
  "created_at": "2025-10-28T18:37:54.046768+00:00",
  "updated_at": "2025-11-03T07:42:09.855441+00:00"
}
page-fe8724943ac1b76b.js:1 🔄 Starting agent response polling...
page-fe8724943ac1b76b.js:1 🔄 Poll response status: 200
page-fe8724943ac1b76b.js:1 🔄 Poll data: {status: 'no_message', timestamp: '2025-11-03T14:09:56.523333'}
page-fe8724943ac1b76b.js:1 🔄 Poll response status: 200
page-fe8724943ac1b76b.js:1 🔄 Poll data: {status: 'no_message', timestamp: '2025-11-03T14:09:58.514229'}
page-fe8724943ac1b76b.js:1 🎯 handleStartStrategyDiscussion called
page-fe8724943ac1b76b.js:1 🎯 selectedConfigId: d13d5536-2498-4f27-b2bc-e4f98958e1d8
page-fe8724943ac1b76b.js:1 🎯 user?.id: 00000000-0000-0000-0000-000000000000
page-fe8724943ac1b76b.js:1 🎯 Got auth token: yes
page-fe8724943ac1b76b.js:1 🎯 Agent status: online
page-fe8724943ac1b76b.js:1 ✅ Agent is already running
page-fe8724943ac1b76b.js:1 📤 Sending existing strategy as context...
page-fe8724943ac1b76b.js:1 📤 Message sent, status: 200
page-fe8724943ac1b76b.js:1 📤 UI state updated, waiting for agent response...
page-fe8724943ac1b76b.js:1 📤 Updated agentMessages: 1 messages
page-fe8724943ac1b76b.js:1 🔄 Poll response status: 200
page-fe8724943ac1b76b.js:1 🔄 Poll data: {status: 'no_message', timestamp: '2025-11-03T14:10:00.458237'}
page-fe8724943ac1b76b.js:1 🔄 Poll response status: 200
page-fe8724943ac1b76b.js:1 🔄 Poll data: {status: 'no_message', timestamp: '2025-11-03T14:10:02.460033'}
page-fe8724943ac1b76b.js:1 🔄 Poll response status: 200
page-fe8724943ac1b76b.js:1 🔄 Poll data: {status: 'no_message', timestamp: '2025-11-03T14:10:04.455970'}
page-fe8724943ac1b76b.js:1 🔄 Poll response status: 200