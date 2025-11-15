✅ New bot creation verified: 45be523e-9569-4811-9048-855790253fff Opus 92



 Bot data being loaded into editing state: {
  "config_id": "45be523e-9569-4811-9048-855790253fff",
  "user_id": "00000000-0000-0000-0000-000000000000",
  "config_name": "Opus 92",
  "config_type": "scheduled_trading",
  "created_at": "2025-11-14T11:34:16.186436+00:00",
  "config_data": {
    "trading": {
      "leverage": 1,
      "position_sizing": {
        "method": "fixed_usd",
        "account_percent": 5,
        "fixed_amount_usd": 100,
        "max_position_percent": 10
      },
      "risk_management": {
        "max_positions": 1,
        "max_daily_loss_usd": 500,
        "default_stop_loss_percent": 5,
        "default_take_profit_percent": 10
      }
    },
    "decision": {
      "user_prompt": "if RSI 1hr below 50 enter long, if above enter short",
      "system_prompt": "You are an expert cryptocurrency trader. Analyze the provided market data and provide clear, reasoned responses about trading actions. Format your response with clear sections for Decision, Confidence, and Reasoning.",
      "analysis_frequency": "1h"
    },
    "extraction": {
      "selected_data_sources": {
        "technical_analysis": {
          "timeframes": [
            "1h"
          ],
          "data_points": [
            "RSI"
          ]
        }
      }
    },
    "llm_config": {
      "model": "default",
      "provider": "default",
      "use_own_key": false,
      "use_platform_keys": true
    },
    "selected_pair": "BTC/USDT",
    "schema_version": "2.1",
    "telegram_integration": {
      "listener": {
        "api_id": "",
        "enabled": false,
        "api_hash": "",
        "session_name": "ggbot_session",
        "source_channels": []
      },
      "publisher": {
        "enabled": false,
        "bot_token": "",
        "filter_channel": "",
        "message_template": "🔥 {ACTION} {SYMBOL} - Confidence: {CONFIDENCE}\n{REASONING}",
        "include_reasoning": true,
        "confidence_threshold": 0.7,
        "include_market_context": true
      }
    }
  }
}