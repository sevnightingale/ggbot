2025-11-10 23:04:38 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 24000 stored
2025-11-10 23:04:39 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-10 23:04:40 | INFO     | ggbot:run_autonomous_cycle:320 - Starting V2 autonomous cycle for config 4260c26f-7de2-4944-953b-919db22d725a
2025-11-10 23:04:40 | INFO     | ggbot:run_autonomous_cycle:326 - 🔍 DEBUG: config.config_type = 'scheduled_trading', signal_data present = False
2025-11-10 23:04:40 | INFO     | market_intelligence.catalog:load_all:75 - Loaded 4 catalog entries from /home/sev/ggbot/market_intelligence/catalog/data_types
2025-11-10 23:04:40 | INFO     | extraction.v2.universal_data_client:__init__:30 - UniversalDataClient initialized with MarketIntelligence gateway
2025-11-10 23:04:40 | INFO     | extraction.v2.preprocessor:__init__:27 - Initialized TechnicalAnalysisPreprocessor with 21 indicators: rsi, macd, stochastic, williams_r, cci, mfi, adx, psar, aroon, atr, bbands, obv, sma, ema, roc, vwap, trix, vortex, bbwidth, keltner, donchian
2025-11-10 23:04:40 | INFO     | extraction.v2.indicators:__init__:33 - Initialized with advanced preprocessing enabled
2025-11-10 23:04:40 | INFO     | extraction.v2.extraction_engine:__init__:67 - Initialized ExtractionEngineV2 with advanced preprocessing, database storage
2025-11-10 23:04:40 | INFO     | ggbot:_run_extraction_v2:765 - Extracting 1 indicators for BTC/USDT across 1 timeframes in parallel
2025-11-10 23:04:40 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:104 - Smart limits: using 100 candles (vs 200 static), saving 50.0%
2025-11-10 23:04:40 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:107 - Extracting 1 indicators for BTC/USDT (1h) with 100 candles
2025-11-10 23:04:40 | INFO     | extraction.v2.universal_data_client:get_candles_with_fallback:88 - Fetching 100 1h candles for BTC/USDT via MarketIntelligence
2025-11-10 23:04:40 | INFO     | market_intelligence.cache.redis_cache:connect:38 - Redis cache connected
2025-11-10 23:04:40 | INFO     | market_intelligence.gateway:query:116 - Cache hit for ohlcv: mi:candles:BTC/USDT:1h:200 (2ms)
2025-11-10 23:04:40 | INFO     | extraction.v2.universal_data_client:get_candles_with_fallback:111 - ✅ Retrieved 100 candles for BTC/USDT from cache (cached) in 2ms
2025-11-10 23:04:40 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:118 - ✅ Fetched 100 candles for BTC/USDT
2025-11-10 23:04:40 | INFO     | extraction.v2.supabase_storage:store_extraction_result:141 - ✅ Stored market data for BTC/USDT (1h) - Record ID: 441487
2025-11-10 23:04:40 | INFO     | extraction.v2.extraction_engine:extract_for_symbol:174 - ✅ Extraction complete for BTC/USDT (stored to 2 systems)
2025-11-10 23:04:40 | INFO     | ggbot:_run_extraction_v2:790 - ✅ V2 Extraction completed for BTC/USDT (1h)
2025-11-10 23:04:41 | INFO     | market_intelligence.adapters.signals.ggshot_adapter:fetch:180 - Fetched 4 ggShot signals for BTC/USDT: ['1h', '30m', '4h', '5m']
2025-11-10 23:04:41 | INFO     | ggbot:_run_extraction_v2:832 - ✅ Fetched ggShot signals for BTC/USDT: 4 timeframes (1h, 30m, 4h, 5m)
2025-11-10 23:04:41 | INFO     | ggbot:_run_extraction_v2:875 - V2 Multi-timeframe extraction completed: 1/1 successful
2025-11-10 23:04:44 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-10 23:04:44 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 24100 stored
2025-11-10 23:04:44 | INFO     | decision.engine_v2:__init__:73 - DecisionEngineV2 initialized
2025-11-10 23:04:44 | INFO     | core.services.llm_key_service:get_api_key:50 - Using platform API key
2025-11-10 23:04:44 | INFO     | decision.llm_providers.openrouter_provider:__init__:92 - Initialized OpenRouter provider - model: grok → x-ai/grok-4-fast, thinking: False
2025-11-10 23:04:44 | INFO     | decision.engine_v2:_initialize_llm_provider:150 - LLM provider initialized successfully
2025-11-10 23:04:44 | INFO     | decision.engine_v2:initialize:87 - Configuration and LLM provider loaded
2025-11-10 23:04:44 | INFO     | decision.engine_v2:make_decision:185 - 🔍 DECISION DEBUG: config_type='scheduled_trading', signal_data present=False, signal_data type=<class 'NoneType'>
2025-11-10 23:04:44 | INFO     | decision.engine_v2:make_decision:198 - 🔍 DECISION DEBUG: Autonomous trading mode: Checking for existing positions (config_type=scheduled_trading, signal_data=False)
2025-11-10 23:04:44 | INFO     | decision.engine_v2:_get_active_position:1505 - Found active position for BTC/USDT: short $600.00, P&L: $0.48
2025-11-10 23:04:44 | INFO     | decision.engine_v2:_handle_autonomous_trading:273 - Routing to position management for existing short position in BTC/USDT
2025-11-10 23:04:45 | INFO     | decision.engine_v2:_get_fresh_market_data:392 - Retrieved multi-timeframe market data for decision
2025-11-10 23:04:45 | INFO     | decision.engine_v2:_get_volume_confirmation:1568 - Volume analysis for BTC/USDT (1h, 35 periods): -57.6% above average (Insignificant)
2025-11-10 23:04:48 | INFO     | decision.llm_providers.openrouter_provider:generate_response:193 - Generated response in 3.69s, tokens: 1417
2025-11-10 23:04:48 | INFO     | decision.engine_v2:_call_llm:1130 - 🤖 Response received from Decision LLM
2025-11-10 23:04:48 | INFO     | decision.engine_v2:_call_llm:1131 - LLM RESPONSE:
ACTION: wait
CONFIDENCE: 0.600
REASONING: The trading strategy dictates entering short when 1H RSI is above 50, which triggered the original entry at RSI 56.9. Current 1H RSI remains at 56.9 (above 50), so the short signal persists and the position still aligns with the strategy. The market has evolved minimally since entry (price down slightly to $106,015.99 from $106,101.05, with +0.1% unrealized P&L), and no strategy-based exit condition is met as RSI has not dropped below 50. Volume confirmation is weak (0.42x average on 1H), but the strategy relies solely on 1H RSI for signals, not volume, so this does not override holding the position.
STOP_LOSS: $109,284.08
TAKE_PROFIT: $99,734.99
2025-11-10 23:04:48 | INFO     | decision.engine_v2:_call_llm:1140 - LLM call completed with metadata
2025-11-10 23:04:48 | INFO     | decision.engine_v2:_save_position_decision_to_db:1703 - Position management decision saved to database
2025-11-10 23:04:48 | INFO     | ggbot:_run_decision_v2:934 - V2 Decision completed: wait with confidence 0.6
2025-11-10 23:04:49 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-10 23:04:50 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 24200 stored
2025-11-10 23:04:54 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 24300 stored
2025-11-10 23:04:54 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-10 23:04:58 | INFO     | core.monitoring.service:_position_monitor:82 - 📊 Monitoring 1 configs with open positions
2025-11-10 23:04:58 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 24400 stored
2025-11-10 23:04:58 | INFO     | ggbot:_run_autonomous_trading_cycle:422 - V2 autonomous cycle completed in 18246ms
2025-11-10 23:05:00 | INFO     | __main__:_handle_kline_message:363 - 📊 Stats: 900 received, 900 stored, 0 errors
2025-11-10 23:05:00 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-10 23:05:01 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 24500 stored
2025-11-10 23:05:05 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 24600 stored
2025-11-10 23:05:05 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-10 23:05:10 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-10 23:05:12 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 24700 stored
2025-11-10 23:05:16 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-10 23:05:19 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 24800 stored
2025-11-10 23:05:21 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-10 23:05:24 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 24900 stored
2025-11-10 23:05:26 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-10 23:05:28 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 25000 stored
2025-11-10 23:05:32 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-10 23:05:32 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 25100 stored
2025-11-10 23:05:37 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-10 23:05:39 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 25200 stored
2025-11-10 23:05:42 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-10 23:05:45 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 25300 stored
2025-11-10 23:05:47 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-10 23:05:50 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 25400 stored
2025-11-10 23:05:53 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-10 23:05:56 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 25500 stored
2025-11-10 23:05:58 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-10 23:05:59 | INFO     | core.monitoring.service:_position_monitor:82 - 📊 Monitoring 1 configs with open positions
2025-11-10 23:06:02 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 25600 stored
2025-11-10 23:06:03 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
