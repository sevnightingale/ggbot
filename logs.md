\(.venv) sev@ggbot-vm:~/ggbot$ pm2 logs
[TAILING] Tailing last 15 lines for [all] processes (change the value with --lines option)
/home/sev/.pm2/pm2.log last 15 lines:
/home/sev/.pm2/logs/ggbot-out.log last 15 lines:
/home/sev/.pm2/logs/ggbot-error.log last 15 lines:
0|ggbot  | 2025-09-08 16:33:53 +00:00: INFO:     connection closed
0|ggbot  | 2025-09-08 16:33:54 +00:00: 2025-09-08 16:33:54 | INFO     | core.services.config_service:list_configs:327 - Listed 1 configs for user 3d47c173-9234-47c7-b57b-9159c9df5dbd
0|ggbot  | 2025-09-08 16:33:54 +00:00: INFO:     27.125.250.251:0 - "GET /api/v2/config HTTP/1.1" 200 OK
0|ggbot  | 2025-09-08 16:33:55 +00:00: 2025-09-08 16:33:55 | INFO     | core.services.config_service:list_configs:327 - Listed 1 configs for user 3d47c173-9234-47c7-b57b-9159c9df5dbd
0|ggbot  | 2025-09-08 16:33:55 +00:00: INFO:     27.125.250.251:0 - "GET /api/v2/config HTTP/1.1" 200 OK
0|ggbot  | 2025-09-08 16:33:55 +00:00: 2025-09-08 16:33:55 | INFO     | core.services.config_service:list_configs:327 - Listed 1 configs for user 3d47c173-9234-47c7-b57b-9159c9df5dbd
0|ggbot  | 2025-09-08 16:33:55 +00:00: INFO:     27.125.250.251:0 - "GET /api/v2/config HTTP/1.1" 200 OK
0|ggbot  | 2025-09-08 16:33:55 +00:00: INFO:     27.125.250.251:0 - "GET /api/v2/bot/04b4a272-8303-4770-a536-6d210b9defba/metrics HTTP/1.1" 200 OK
0|ggbot  | 2025-09-08 16:33:55 +00:00: INFO:     27.125.250.251:0 - "GET /api/v2/bot/04b4a272-8303-4770-a536-6d210b9defba/trades HTTP/1.1" 200 OK
0|ggbot  | 2025-09-08 16:33:55 +00:00: INFO:     27.125.250.251:0 - "GET /api/v2/bot/04b4a272-8303-4770-a536-6d210b9defba/positions HTTP/1.1" 200 OK
0|ggbot  | 2025-09-08 16:33:55 +00:00: INFO:     ('27.125.250.251', 0) - "WebSocket /ws/bot-status/3d47c173-9234-47c7-b57b-9159c9df5dbd" [accepted]
0|ggbot  | 2025-09-08 16:33:55 +00:00: INFO:     connection open
0|ggbot  | 2025-09-08 16:34:06 +00:00: INFO:     27.125.250.251:0 - "GET /api/v2/user/profile HTTP/1.1" 200 OK
0|ggbot  | 2025-09-08 16:34:06 +00:00: INFO:     27.125.250.251:0 - "GET /api/v2/data-sources-with-points HTTP/1.1" 200 OK
0|ggbot  | 2025-09-08 16:34:06 +00:00: INFO:     27.125.250.251:0 - "GET /api/v2/user/llm-credentials HTTP/1.1" 200 OK
0|ggbot  | 2025-09-08 16:34:06 +00:00: INFO:     27.125.250.251:0 - "GET /api/v2/config/04b4a272-8303-4770-a536-6d210b9defba HTTP/1.1" 200 OK
0|ggbot  | 2025-09-08 16:34:17 +00:00: 2025-09-08 16:34:17 | INFO     | core.services.config_service:update_config:398 - Updated config 04b4a272-8303-4770-a536-6d210b9defba for user 3d47c173-9234-47c7-b57b-9159c9df5dbd
0|ggbot  | 2025-09-08 16:34:17 +00:00: INFO:     27.125.250.251:0 - "PUT /api/v2/config/04b4a272-8303-4770-a536-6d210b9defba HTTP/1.1" 200 OK
0|ggbot  | 2025-09-08 16:34:17 +00:00: 2025-09-08 16:34:17 | INFO     | core.services.config_service:list_configs:327 - Listed 1 configs for user 3d47c173-9234-47c7-b57b-9159c9df5dbd
0|ggbot  | 2025-09-08 16:34:17 +00:00: INFO:     27.125.250.251:0 - "GET /api/v2/config HTTP/1.1" 200 OK
0|ggbot  | 2025-09-08 16:34:39 +00:00: INFO:     27.125.250.225:0 - "POST /api/v2/bot/04b4a272-8303-4770-a536-6d210b9defba/start HTTP/1.1" 200 OK
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | ggbot:run_autonomous_cycle:186 - Starting V2 autonomous cycle for config 04b4a272-8303-4770-a536-6d210b9defba
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.preprocessor:__init__:27 - Initialized TechnicalAnalysisPreprocessor with 21 indicators: rsi, macd, stochastic, williams_r, cci, mfi, adx, psar, aroon, atr, bbands, obv, sma, ema, roc, vwap, trix, vortex, bbwidth, keltner, donchian
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.indicators:__init__:33 - Initialized with advanced preprocessing enabled
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:__init__:66 - Initialized ExtractionEngineV2 with advanced preprocessing, database storage
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | ggbot:_run_extraction_v2:456 - Extracting 1 indicators for BTC/USDT (5m)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:93 - Extracting 1 indicators for BTC/USDT (5m)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:connect:69 - Connected to Hummingbot API
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:get_candles:111 - Fetching 200 5m candles for BTC/USDT from kucoin
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:get_candles:137 - ✅ Retrieved 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:disconnect:76 - Disconnected from Hummingbot API
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:103 - ✅ Fetched 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | ERROR    | extraction.v2.supabase_storage:store_extraction_result:148 - ❌ Failed to store market data for BTC/USDT: Object of type UUID is not JSON serializable
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:158 - ✅ Extraction complete for BTC/USDT (stored to 2 systems)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | ggbot:_run_extraction_v2:472 - ✅ V2 Extraction completed for BTC/USDT (5m)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | ggbot:_run_extraction_v2:456 - Extracting 1 indicators for BTC/USDT (15m)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:93 - Extracting 1 indicators for BTC/USDT (15m)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:connect:69 - Connected to Hummingbot API
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:get_candles:111 - Fetching 200 15m candles for BTC/USDT from kucoin
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:get_candles:137 - ✅ Retrieved 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:disconnect:76 - Disconnected from Hummingbot API
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:103 - ✅ Fetched 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | ERROR    | extraction.v2.supabase_storage:store_extraction_result:148 - ❌ Failed to store market data for BTC/USDT: Object of type UUID is not JSON serializable
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:158 - ✅ Extraction complete for BTC/USDT (stored to 2 systems)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | ggbot:_run_extraction_v2:472 - ✅ V2 Extraction completed for BTC/USDT (15m)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | ggbot:_run_extraction_v2:456 - Extracting 1 indicators for BTC/USDT (30m)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:93 - Extracting 1 indicators for BTC/USDT (30m)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:connect:69 - Connected to Hummingbot API
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:get_candles:111 - Fetching 200 30m candles for BTC/USDT from kucoin
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:get_candles:137 - ✅ Retrieved 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:disconnect:76 - Disconnected from Hummingbot API
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:103 - ✅ Fetched 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | ERROR    | extraction.v2.supabase_storage:store_extraction_result:148 - ❌ Failed to store market data for BTC/USDT: Object of type UUID is not JSON serializable
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:158 - ✅ Extraction complete for BTC/USDT (stored to 2 systems)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | ggbot:_run_extraction_v2:472 - ✅ V2 Extraction completed for BTC/USDT (30m)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | ggbot:_run_extraction_v2:456 - Extracting 1 indicators for BTC/USDT (1h)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:93 - Extracting 1 indicators for BTC/USDT (1h)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:connect:69 - Connected to Hummingbot API
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:get_candles:111 - Fetching 200 1h candles for BTC/USDT from kucoin
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:get_candles:137 - ✅ Retrieved 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:disconnect:76 - Disconnected from Hummingbot API
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:103 - ✅ Fetched 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | ERROR    | extraction.v2.supabase_storage:store_extraction_result:148 - ❌ Failed to store market data for BTC/USDT: Object of type UUID is not JSON serializable
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:158 - ✅ Extraction complete for BTC/USDT (stored to 2 systems)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | ggbot:_run_extraction_v2:472 - ✅ V2 Extraction completed for BTC/USDT (1h)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | ggbot:_run_extraction_v2:456 - Extracting 1 indicators for BTC/USDT (4h)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:93 - Extracting 1 indicators for BTC/USDT (4h)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:connect:69 - Connected to Hummingbot API
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:get_candles:111 - Fetching 200 4h candles for BTC/USDT from kucoin
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:get_candles:137 - ✅ Retrieved 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:disconnect:76 - Disconnected from Hummingbot API
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:103 - ✅ Fetched 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | ERROR    | extraction.v2.supabase_storage:store_extraction_result:148 - ❌ Failed to store market data for BTC/USDT: Object of type UUID is not JSON serializable
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:158 - ✅ Extraction complete for BTC/USDT (stored to 2 systems)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | ggbot:_run_extraction_v2:472 - ✅ V2 Extraction completed for BTC/USDT (4h)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | ggbot:_run_extraction_v2:456 - Extracting 1 indicators for BTC/USDT (1d)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:93 - Extracting 1 indicators for BTC/USDT (1d)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:connect:69 - Connected to Hummingbot API
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:get_candles:111 - Fetching 200 1d candles for BTC/USDT from kucoin
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:get_candles:137 - ✅ Retrieved 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:disconnect:76 - Disconnected from Hummingbot API
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:103 - ✅ Fetched 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | ERROR    | extraction.v2.supabase_storage:store_extraction_result:148 - ❌ Failed to store market data for BTC/USDT: Object of type UUID is not JSON serializable
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:158 - ✅ Extraction complete for BTC/USDT (stored to 2 systems)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | ggbot:_run_extraction_v2:472 - ✅ V2 Extraction completed for BTC/USDT (1d)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | ggbot:_run_extraction_v2:456 - Extracting 1 indicators for BTC/USDT (1w)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:93 - Extracting 1 indicators for BTC/USDT (1w)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:connect:69 - Connected to Hummingbot API
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:get_candles:111 - Fetching 200 1w candles for BTC/USDT from kucoin
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:get_candles:137 - ✅ Retrieved 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.data_client:disconnect:76 - Disconnected from Hummingbot API
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:103 - ✅ Fetched 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | ERROR    | extraction.v2.supabase_storage:store_extraction_result:148 - ❌ Failed to store market data for BTC/USDT: Object of type UUID is not JSON serializable
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:158 - ✅ Extraction complete for BTC/USDT (stored to 2 systems)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | ggbot:_run_extraction_v2:472 - ✅ V2 Extraction completed for BTC/USDT (1w)
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | ggbot:_run_extraction_v2:492 - V2 Multi-timeframe extraction completed: 7/7 successful
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | decision.engine_v2:__init__:62 - DecisionEngineV2 initialized
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | ERROR    | core.config.repository:get_config:70 - Invalid configuration 04b4a272-8303-4770-a536-6d210b9defba: 1 validation error for BotConfig
0|ggbot  | 2025-09-08 16:35:30 +00:00: config_type
0|ggbot  | 2025-09-08 16:35:30 +00:00:   Extra inputs are not permitted [type=extra_forbidden, input_value='autonomous_trading', input_type=str]
0|ggbot  | 2025-09-08 16:35:30 +00:00:     For further information visit https://errors.pydantic.dev/2.11/v/extra_forbidden
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | core.config.repository:load_template:299 - Loaded template v1.0 from /home/sev/ggbot/core/config/template_v1.json
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | decision.engine_v2:initialize:72 - Configuration loaded
0|ggbot  | 2025-09-08 16:35:30 +00:00: 2025-09-08 16:35:30 | INFO     | decision.engine_v2:_get_fresh_market_data:274 - Retrieved multi-timeframe market data for decision
0|ggbot  | 2