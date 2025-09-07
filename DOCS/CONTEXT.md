🧪 GGBot V2 API Test Suite
Auth Status
✅ Logged in as: sevnightingale@gmail.com

🔑 User ID: 3d47c173-9234-47c7-b57b-9159c9df5dbd

📝 Token: Present

Quick Tests
List ConfigsCreate Test ConfigGet ProfileGet Data Sources
Test Results
List Configs
✅ Status: 200

View Response
{
  "status": "success",
  "configs": [
    {
      "config_id": "2820200a-e011-4c08-b907-922277617ce2",
      "user_id": "3d47c173-9234-47c7-b57b-9159c9df5dbd",
      "config_name": "E2E_Test_Bot_20250905_111854",
      "selected_pair": "BTC/USDT",
      "extraction": {
        "indicators": [
          "RSI_15m",
          "MACD_15m",
          "BB_15m"
        ]
      },
      "decision": {
        "user_prompt": "Test trading strategy: Enter long positions when RSI < 30 and MACD shows bullish crossover. Use conservative position sizing.",
        "system_prompt": "You are testing the E2E system. Make conservative paper trading decisions based on technical indicators.",
        "analysis_frequency": "15m"
      },
      "trading": {
        "leverage": 1,
        "execution_mode": "paper",
        "position_sizing": {
          "method": "fixed_amount_usd",
          "fixed_amount_usd": 100
        },
        "risk_management": {
          "max_positions": 3,
          "default_stop_loss_percent": 2,
          "default_take_profit_percent": 4
        }
      },
      "telegram_integration": {
        "listener": {
          "enabled": false
        },
        "publisher": {
          "enabled": false
        }
      },
      "created_at": "2025-09-05T11:18:55.097973+00:00",
      "updated_at": "2025-09-05T11:18:55.097973+00:00"
    }
  ],
  "count": 1
}
Create Config
✅ Status: 400

View Response
{
  "status": "error",
  "error": "Failed to create configuration",
  "status_code": 400
}
User Profile
✅ Status: 200

View Response
{
  "status": "success",
  "profile": {
    "user_id": "3d47c173-9234-47c7-b57b-9159c9df5dbd",
    "subscription_tier": "free",
    "subscription_status": "active",
    "can_use_premium_features": false,
    "requires_own_llm_keys": true,
    "can_publish_telegram_signals": false
  }
}
Data Sources
✅ Status: 200

View Response
{
  "status": "success",
  "data_sources": [
    {
      "source_id": "905ab59b-01e7-47c4-b870-d819ac787bef",
      "name": "technical_analysis",
      "display_name": "Technical Analysis",
      "description": "Core technical indicators for market analysis",
      "enabled": true,
      "requires_premium": false,
      "sort_order": 1,
      "data_points": [
        {
          "data_point_id": "c46c2927-8876-4b13-a5f7-85d9ebd9b073",
          "name": "RSI",
          "display_name": "RSI (Relative Strength Index)",
          "description": "Momentum oscillator measuring speed and magnitude of price changes",
          "config_values": [
            "RSI_5m",
            "RSI_15m",
            "RSI_30m",
            "RSI_1h",
            "RSI_4h",
            "RSI_1d",
            "RSI_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 1,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "c3742cf6-8aee-43a7-aaad-26ad375e957b",
          "name": "MACD",
          "display_name": "MACD (Moving Average Convergence Divergence)",
          "description": "Trend-following momentum indicator",
          "config_values": [
            "MACD_5m",
            "MACD_15m",
            "MACD_30m",
            "MACD_1h",
            "MACD_4h",
            "MACD_1d",
            "MACD_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 2,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "acbc08cd-111c-4204-bc86-44bb96c292bd",
          "name": "Stochastic",
          "display_name": "Stochastic Oscillator",
          "description": "Momentum indicator comparing closing price to price range",
          "config_values": [
            "STOCH_5m",
            "STOCH_15m",
            "STOCH_30m",
            "STOCH_1h",
            "STOCH_4h",
            "STOCH_1d",
            "STOCH_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 3,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "a128744f-cb40-4f3f-bf4d-134f367a7f11",
          "name": "Williams_R",
          "display_name": "Williams %R",
          "description": "Momentum indicator measuring overbought/oversold levels",
          "config_values": [
            "WILLR_5m",
            "WILLR_15m",
            "WILLR_30m",
            "WILLR_1h",
            "WILLR_4h",
            "WILLR_1d",
            "WILLR_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 4,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "647c43ce-4afd-4ee4-965a-d9cf44244b92",
          "name": "CCI",
          "display_name": "CCI (Commodity Channel Index)",
          "description": "Momentum oscillator measuring price deviation from average",
          "config_values": [
            "CCI_5m",
            "CCI_15m",
            "CCI_30m",
            "CCI_1h",
            "CCI_4h",
            "CCI_1d",
            "CCI_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 5,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "9111b570-8021-49f1-9a7a-79771d53aa21",
          "name": "MFI",
          "display_name": "MFI (Money Flow Index)",
          "description": "Volume-weighted momentum indicator",
          "config_values": [
            "MFI_5m",
            "MFI_15m",
            "MFI_30m",
            "MFI_1h",
            "MFI_4h",
            "MFI_1d",
            "MFI_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 6,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "1f9a09e2-2505-4152-80cd-8095f3ad4d13",
          "name": "ROC",
          "display_name": "ROC (Rate of Change)",
          "description": "Momentum oscillator measuring percentage change",
          "config_values": [
            "ROC_5m",
            "ROC_15m",
            "ROC_30m",
            "ROC_1h",
            "ROC_4h",
            "ROC_1d",
            "ROC_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 7,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "40d042a5-7f1a-4155-a1c7-d6efe32fd642",
          "name": "Aroon",
          "display_name": "Aroon Indicator",
          "description": "Trend indicator identifying trend changes",
          "config_values": [
            "AROON_5m",
            "AROON_15m",
            "AROON_30m",
            "AROON_1h",
            "AROON_4h",
            "AROON_1d",
            "AROON_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 8,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "26fbbdab-d08c-4dfa-80fd-f7b13d638ffd",
          "name": "Vortex",
          "display_name": "Vortex Indicator",
          "description": "Oscillator identifying trend reversals",
          "config_values": [
            "VI_5m",
            "VI_15m",
            "VI_30m",
            "VI_1h",
            "VI_4h",
            "VI_1d",
            "VI_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 9,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "63bfc998-ed0f-426c-9b5b-c3b5f8a88e43",
          "name": "TRIX",
          "display_name": "TRIX",
          "description": "Triple exponential moving average oscillator",
          "config_values": [
            "TRIX_5m",
            "TRIX_15m",
            "TRIX_30m",
            "TRIX_1h",
            "TRIX_4h",
            "TRIX_1d",
            "TRIX_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 10,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "1a168c0b-6a92-4808-8752-86b615c2ad4c",
          "name": "ADX",
          "display_name": "ADX (Average Directional Index)",
          "description": "Trend strength indicator",
          "config_values": [
            "ADX_5m",
            "ADX_15m",
            "ADX_30m",
            "ADX_1h",
            "ADX_4h",
            "ADX_1d",
            "ADX_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 11,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "d445bc61-5f2a-485b-bf2e-a63408fb40c2",
          "name": "PSAR",
          "display_name": "Parabolic SAR",
          "description": "Trend-following indicator showing potential reversal points",
          "config_values": [
            "PSAR_5m",
            "PSAR_15m",
            "PSAR_30m",
            "PSAR_1h",
            "PSAR_4h",
            "PSAR_1d",
            "PSAR_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 12,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "448eb93d-1bea-490a-869e-e231f185cbeb",
          "name": "EMA",
          "display_name": "EMA (Exponential Moving Average)",
          "description": "Trend-following moving average giving more weight to recent prices",
          "config_values": [
            "EMA_5m",
            "EMA_15m",
            "EMA_30m",
            "EMA_1h",
            "EMA_4h",
            "EMA_1d",
            "EMA_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 13,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "b505550f-4eb5-4ca0-990c-284f9ba8a97d",
          "name": "SMA",
          "display_name": "SMA (Simple Moving Average)",
          "description": "Basic trend-following moving average",
          "config_values": [
            "SMA_5m",
            "SMA_15m",
            "SMA_30m",
            "SMA_1h",
            "SMA_4h",
            "SMA_1d",
            "SMA_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 14,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "573fa84d-f5d1-4e8b-b272-2e42b6af5db8",
          "name": "BB",
          "display_name": "Bollinger Bands",
          "description": "Volatility bands around moving average",
          "config_values": [
            "BB_5m",
            "BB_15m",
            "BB_30m",
            "BB_1h",
            "BB_4h",
            "BB_1d",
            "BB_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 15,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "eb26889b-e54e-4069-bc9d-cb7785f9a9fd",
          "name": "KC",
          "display_name": "Keltner Channels",
          "description": "Volatility-based envelope indicator",
          "config_values": [
            "KC_5m",
            "KC_15m",
            "KC_30m",
            "KC_1h",
            "KC_4h",
            "KC_1d",
            "KC_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 16,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "0bc9b808-e3e6-4d87-b6ea-b2e6b1e81376",
          "name": "DC",
          "display_name": "Donchian Channels",
          "description": "Price channel indicator based on highest high and lowest low",
          "config_values": [
            "DC_5m",
            "DC_15m",
            "DC_30m",
            "DC_1h",
            "DC_4h",
            "DC_1d",
            "DC_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 17,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "d69d6546-a6e4-405f-afd0-4b57acaa165e",
          "name": "ATR",
          "display_name": "ATR (Average True Range)",
          "description": "Volatility indicator measuring price movement",
          "config_values": [
            "ATR_5m",
            "ATR_15m",
            "ATR_30m",
            "ATR_1h",
            "ATR_4h",
            "ATR_1d",
            "ATR_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 18,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "a17c1340-15e0-43cd-95c8-b18ec1204106",
          "name": "BBW",
          "display_name": "Bollinger Band Width",
          "description": "Measures the width between Bollinger Bands",
          "config_values": [
            "BBW_5m",
            "BBW_15m",
            "BBW_30m",
            "BBW_1h",
            "BBW_4h",
            "BBW_1d",
            "BBW_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 19,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "3551096a-8b63-435d-901a-9a80e0bc0ef3",
          "name": "OBV",
          "display_name": "OBV (On-Balance Volume)",
          "description": "Volume-based momentum indicator",
          "config_values": [
            "OBV_5m",
            "OBV_15m",
            "OBV_30m",
            "OBV_1h",
            "OBV_4h",
            "OBV_1d",
            "OBV_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 20,
          "has_access": true,
          "is_locked": false
        },
        {
          "data_point_id": "a304fce3-2c98-4594-bb74-73b577695c27",
          "name": "VWAP",
          "display_name": "VWAP (Volume Weighted Average Price)",
          "description": "Volume-weighted average price indicator",
          "config_values": [
            "VWAP_5m",
            "VWAP_15m",
            "VWAP_30m",
            "VWAP_1h",
            "VWAP_4h",
            "VWAP_1d",
            "VWAP_1w"
          ],
          "requires_premium": false,
          "enabled": true,
          "sort_order": 21,
          "has_access": true,
          "is_locked": false
        }
      ]
    },
    {
      "source_id": "556e0a48-8f57-4c46-a537-ad645ceb21b3",
      "name": "signals_group_chats",
      "display_name": "Signals in Group Chats",
      "description": "Premium AI-filtered trading signals from monitored channels",
      "enabled": true,
      "requires_premium": true,
      "sort_order": 2,
      "data_points": [
        {
          "data_point_id": "335c2e67-89b8-4f5f-94ec-d7a055c6e007",
          "name": "ggShot",
          "display_name": "ggShot Premium Signals",
          "description": "AI-filtered premium trading signals from 140+ cryptocurrency pairs with confidence scoring",
          "config_values": [
            "ggShot"
          ],
          "requires_premium": true,
          "enabled": true,
          "sort_order": 1,
          "has_access": false,
          "is_locked": true
        }
      ]
    }
  ],
  "user_paid_points": [],
  "count": 2
}
