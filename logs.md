0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | ggbot:run_autonomous_cycle:186 - Starting V2 autonomous cycle for config 04b4a272-8303-4770-a536-6d210b9defba
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.preprocessor:__init__:27 - Initialized TechnicalAnalysisPreprocessor with 21 indicators: rsi, macd, stochastic, williams_r, cci, mfi, adx, psar, aroon, atr, bbands, obv, sma, ema, roc, vwap, trix, vortex, bbwidth, keltner, donchian
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.indicators:__init__:33 - Initialized with advanced preprocessing enabled
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:__init__:66 - Initialized ExtractionEngineV2 with advanced preprocessing, database storage
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | ggbot:_run_extraction_v2:456 - Extracting 1 indicators for BTC/USDT (5m)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:93 - Extracting 1 indicators for BTC/USDT (5m)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:connect:69 - Connected to Hummingbot API
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:get_candles:111 - Fetching 200 5m candles for BTC/USDT from kucoin
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:get_candles:137 - ✅ Retrieved 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:disconnect:76 - Disconnected from Hummingbot API
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:103 - ✅ Fetched 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | ERROR    | extraction.v2.supabase_storage:store_extraction_result:144 - ❌ Failed to store market data for BTC/USDT: Object of type UUID is not JSON serializable
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:158 - ✅ Extraction complete for BTC/USDT (stored to 2 systems)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | ggbot:_run_extraction_v2:472 - ✅ V2 Extraction completed for BTC/USDT (5m)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | ggbot:_run_extraction_v2:456 - Extracting 1 indicators for BTC/USDT (15m)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:93 - Extracting 1 indicators for BTC/USDT (15m)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:connect:69 - Connected to Hummingbot API
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:get_candles:111 - Fetching 200 15m candles for BTC/USDT from kucoin
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:get_candles:137 - ✅ Retrieved 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:disconnect:76 - Disconnected from Hummingbot API
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:103 - ✅ Fetched 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | ERROR    | extraction.v2.supabase_storage:store_extraction_result:144 - ❌ Failed to store market data for BTC/USDT: Object of type UUID is not JSON serializable
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:158 - ✅ Extraction complete for BTC/USDT (stored to 2 systems)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | ggbot:_run_extraction_v2:472 - ✅ V2 Extraction completed for BTC/USDT (15m)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | ggbot:_run_extraction_v2:456 - Extracting 1 indicators for BTC/USDT (30m)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:93 - Extracting 1 indicators for BTC/USDT (30m)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:connect:69 - Connected to Hummingbot API
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:get_candles:111 - Fetching 200 30m candles for BTC/USDT from kucoin
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:get_candles:137 - ✅ Retrieved 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:disconnect:76 - Disconnected from Hummingbot API
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:103 - ✅ Fetched 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | ERROR    | extraction.v2.supabase_storage:store_extraction_result:144 - ❌ Failed to store market data for BTC/USDT: Object of type UUID is not JSON serializable
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:158 - ✅ Extraction complete for BTC/USDT (stored to 2 systems)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | ggbot:_run_extraction_v2:472 - ✅ V2 Extraction completed for BTC/USDT (30m)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | ggbot:_run_extraction_v2:456 - Extracting 1 indicators for BTC/USDT (1h)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:93 - Extracting 1 indicators for BTC/USDT (1h)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:connect:69 - Connected to Hummingbot API
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:get_candles:111 - Fetching 200 1h candles for BTC/USDT from kucoin
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:get_candles:137 - ✅ Retrieved 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:disconnect:76 - Disconnected from Hummingbot API
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:103 - ✅ Fetched 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | ERROR    | extraction.v2.supabase_storage:store_extraction_result:144 - ❌ Failed to store market data for BTC/USDT: Object of type UUID is not JSON serializable
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:158 - ✅ Extraction complete for BTC/USDT (stored to 2 systems)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | ggbot:_run_extraction_v2:472 - ✅ V2 Extraction completed for BTC/USDT (1h)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | ggbot:_run_extraction_v2:456 - Extracting 1 indicators for BTC/USDT (4h)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:93 - Extracting 1 indicators for BTC/USDT (4h)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:connect:69 - Connected to Hummingbot API
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:get_candles:111 - Fetching 200 4h candles for BTC/USDT from kucoin
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:get_candles:137 - ✅ Retrieved 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:disconnect:76 - Disconnected from Hummingbot API
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:103 - ✅ Fetched 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | ERROR    | extraction.v2.supabase_storage:store_extraction_result:144 - ❌ Failed to store market data for BTC/USDT: Object of type UUID is not JSON serializable
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:158 - ✅ Extraction complete for BTC/USDT (stored to 2 systems)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | ggbot:_run_extraction_v2:472 - ✅ V2 Extraction completed for BTC/USDT (4h)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | ggbot:_run_extraction_v2:456 - Extracting 1 indicators for BTC/USDT (1d)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:93 - Extracting 1 indicators for BTC/USDT (1d)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:connect:69 - Connected to Hummingbot API
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:get_candles:111 - Fetching 200 1d candles for BTC/USDT from kucoin
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:get_candles:137 - ✅ Retrieved 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:disconnect:76 - Disconnected from Hummingbot API
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:103 - ✅ Fetched 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | ERROR    | extraction.v2.supabase_storage:store_extraction_result:144 - ❌ Failed to store market data for BTC/USDT: Object of type UUID is not JSON serializable
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:158 - ✅ Extraction complete for BTC/USDT (stored to 2 systems)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | ggbot:_run_extraction_v2:472 - ✅ V2 Extraction completed for BTC/USDT (1d)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | ggbot:_run_extraction_v2:456 - Extracting 1 indicators for BTC/USDT (1w)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:93 - Extracting 1 indicators for BTC/USDT (1w)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:connect:69 - Connected to Hummingbot API
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:get_candles:111 - Fetching 200 1w candles for BTC/USDT from kucoin
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:get_candles:137 - ✅ Retrieved 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.data_client:disconnect:76 - Disconnected from Hummingbot API
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:103 - ✅ Fetched 200 candles for BTC/USDT
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | ERROR    | extraction.v2.supabase_storage:store_extraction_result:144 - ❌ Failed to store market data for BTC/USDT: Object of type UUID is not JSON serializable
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:158 - ✅ Extraction complete for BTC/USDT (stored to 2 systems)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | ggbot:_run_extraction_v2:472 - ✅ V2 Extraction completed for BTC/USDT (1w)
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | ggbot:_run_extraction_v2:492 - V2 Multi-timeframe extraction completed: 7/7 successful
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | decision.engine_v2:__init__:62 - DecisionEngineV2 initialized
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | ERROR    | core.config.repository:get_config:70 - Invalid configuration 04b4a272-8303-4770-a536-6d210b9defba: 6 validation errors for BotConfig
0|ggbot  | 2025-09-08 09:30:30 +00:00: user_id
0|ggbot  | 2025-09-08 09:30:30 +00:00:   Extra inputs are not permitted [type=extra_forbidden, input_value='3d47c173-9234-47c7-b57b-9159c9df5dbd', input_type=str]
0|ggbot  | 2025-09-08 09:30:30 +00:00:     For further information visit https://errors.pydantic.dev/2.11/v/extra_forbidden
0|ggbot  | 2025-09-08 09:30:30 +00:00: config_id
0|ggbot  | 2025-09-08 09:30:30 +00:00:   Extra inputs are not permitted [type=extra_forbidden, input_value='04b4a272-8303-4770-a536-6d210b9defba', input_type=str]
0|ggbot  | 2025-09-08 09:30:30 +00:00:     For further information visit https://errors.pydantic.dev/2.11/v/extra_forbidden
0|ggbot  | 2025-09-08 09:30:30 +00:00: created_at
0|ggbot  | 2025-09-08 09:30:30 +00:00:   Extra inputs are not permitted [type=extra_forbidden, input_value='2025-09-08T09:22:27.195325', input_type=str]
0|ggbot  | 2025-09-08 09:30:30 +00:00:     For further information visit https://errors.pydantic.dev/2.11/v/extra_forbidden
0|ggbot  | 2025-09-08 09:30:30 +00:00: updated_at
0|ggbot  | 2025-09-08 09:30:30 +00:00:   Extra inputs are not permitted [type=extra_forbidden, input_value='2025-09-08T09:22:27.195327', input_type=str]
0|ggbot  | 2025-09-08 09:30:30 +00:00:     For further information visit https://errors.pydantic.dev/2.11/v/extra_forbidden
0|ggbot  | 2025-09-08 09:30:30 +00:00: config_data
0|ggbot  | 2025-09-08 09:30:30 +00:00:   Extra inputs are not permitted [type=extra_forbidden, input_value={'trading': {'leverage': ...market_context': True}}}, input_type=dict]
0|ggbot  | 2025-09-08 09:30:30 +00:00:     For further information visit https://errors.pydantic.dev/2.11/v/extra_forbidden
0|ggbot  | 2025-09-08 09:30:30 +00:00: config_name
0|ggbot  | 2025-09-08 09:30:30 +00:00:   Extra inputs are not permitted [type=extra_forbidden, input_value='New ggbot', input_type=str]
0|ggbot  | 2025-09-08 09:30:30 +00:00:     For further information visit https://errors.pydantic.dev/2.11/v/extra_forbidden
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | ERROR    | core.config.repository:load_template:304 - Error loading template v1.0: 1 validation error for BotConfig
0|ggbot  | 2025-09-08 09:30:30 +00:00: config_type
0|ggbot  | 2025-09-08 09:30:30 +00:00:   Extra inputs are not permitted [type=extra_forbidden, input_value='autonomous_trading', input_type=str]
0|ggbot  | 2025-09-08 09:30:30 +00:00:     For further information visit https://errors.pydantic.dev/2.11/v/extra_forbidden
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | decision.engine_v2:initialize:72 - Configuration loaded
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | INFO     | decision.engine_v2:_get_fresh_market_data:274 - Retrieved multi-timeframe market data for decision
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | ERROR    | decision.engine_v2:make_decision:107 - Unexpected decision error: 'NoneType' object has no attribute 'format'
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | ERROR    | ggbot:_run_decision_v2:547 - V2 Decision failed: Decision making failed: 'NoneType' object has no attribute 'format'
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | ERROR    | ggbot:_run_autonomous_trading_cycle:260 - V2 autonomous cycle failed: 1 validation error for OrchestrationResult
0|ggbot  | 2025-09-08 09:30:30 +00:00: config_id
0|ggbot  | 2025-09-08 09:30:30 +00:00:   Input should be a valid string [type=string_type, input_value=UUID('04b4a272-8303-4770-a536-6d210b9defba'), input_type=UUID]
0|ggbot  | 2025-09-08 09:30:30 +00:00:     For further information visit https://errors.pydantic.dev/2.11/v/string_type
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | ERROR    | ggbot:run_autonomous_cycle:206 - V2 orchestration failed: 1 validation error for OrchestrationResult
0|ggbot  | 2025-09-08 09:30:30 +00:00: config_id
0|ggbot  | 2025-09-08 09:30:30 +00:00:   Input should be a valid string [type=string_type, input_value=UUID('04b4a272-8303-4770-a536-6d210b9defba'), input_type=UUID]
0|ggbot  | 2025-09-08 09:30:30 +00:00:     For further information visit https://errors.pydantic.dev/2.11/v/string_type
0|ggbot  | 2025-09-08 09:30:30 +00:00: 2025-09-08 09:30:30 | ERROR    | ggbot:run_once:686 - Execution failed for 3d47c173-9234-47c7-b57b-9159c9df5dbd:04b4a272-8303-4770-a536-6d210b9defba:5m:1757323800: 500: Orchestration failed: 1 validation error for OrchestrationResult
0|ggbot  | 2025-09-08 09:30:30 +00:00: config_id
0|ggbot  | 2025-09-08 09:30:30 +00:00:   Input should be a valid string [type=string_type, input_value=UUID('04b4a272-8303-4770-a536-6d210b9defba'), input_type=UUID]
0|ggbot  | 2025-09-08 09:30:30 +00:00:     For further information visit https://errors.pydantic.dev/2.11/v/string_type
0|ggbot  | 2025-09-08 09:35:30 +00:00: 