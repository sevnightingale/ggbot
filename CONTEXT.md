2025-11-08 16:44:57 | INFO     | decision.engine_v2:_call_llm:1131 - LLM RESPONSE:
ACTION: long  
CONFIDENCE: 0.700  
REASONING: The trading strategy specifies entering long if RSI on the 1h timeframe is below 50. The provided 1h RSI is 44.9, which is below 50, triggering a long entry signal. Volume confirmation is insignificant (0.14x average, -86.2% below), indicating weak momentum and reducing overall confidence, but the strategy relies solely on the RSI condition without volume requirements. ggShot signals show mixed bias (2 LONG vs 2 SHORT), providing no strong alignment, but the strategy does not incorporate external signals.  
STOP_LOSS: null  
TAKE_PROFIT: null
2025-11-08 16:44:57 | INFO     | decision.engine_v2:_call_llm:1140 - LLM call completed with metadata
2025-11-08 16:44:57 | INFO     | decision.engine_v2:_save_decision_to_db:673 - Decision saved to database
2025-11-08 16:44:57 | INFO     | ggbot:_run_decision_v2:934 - V2 Decision completed: long with confidence 0.7
2025-11-08 16:45:00 | INFO     | __main__:_handle_kline_message:363 - 📊 Stats: 100 received, 100 stored, 0 errors
2025-11-08 16:45:00 | INFO     | __main__:_handle_kline_message:363 - 📊 Stats: 200 received, 200 stored, 0 errors
2025-11-08 16:45:00 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 5300 stored
2025-11-08 16:45:01 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-08 16:45:01 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 0 open positions
2025-11-08 16:45:04 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 5400 stored
2025-11-08 16:45:04 | INFO     | trading.live.aster_service_v3:execute_trade_intent:324 - Executing AsterDEX v3 live trade: LONG BTC/USDT (confidence=0.700)
2025-11-08 16:45:04 | INFO     | trading.live.aster_service_v3:execute_trade_intent:370 - Symbol detected as ccxt format: BTC/USDT → BTCUSDT
2025-11-08 16:45:04 | INFO     | trading.live.aster_service_v3:_calculate_weight:202 - Querying AsterDEX account balance for position sizing...
2025-11-08 16:45:04 | WARNING  | trading.live.aster_service_v3:_calculate_weight:221 - No USDT equity, using minimum quantity
2025-11-08 16:45:04 | INFO     | trading.live.aster_service_v3:execute_trade_intent:478 - Applied default stop loss: $99717.53
2025-11-08 16:45:04 | INFO     | trading.live.aster_service_v3:execute_trade_intent:485 - Applied default take profit: $104805.16
2025-11-08 16:45:05 | INFO     | trading.live.aster_service_v3:_place_market_order:650 - Market order successful: {'orderId': 7629859617, 'symbol': 'BTCUSDT', 'status': 'NEW', 'clientOrderId': 'CvHIn22cbEFhNt9EgzfHMj', 'price': '0', 'avgPrice': '0.0000', 'origQty': '0.001', 'executedQty': '0', 'cumQty': '0', 'cumQuote': '0', 'timeInForce': 'GTC', 'type': 'MARKET', 'reduceOnly': False, 'closePosition': False, 'side': 'BUY', 'positionSide': 'BOTH', 'stopPrice': '0', 'workingType': 'CONTRACT_PRICE', 'priceProtect': False, 'origType': 'MARKET', 'updateTime': 1762620305208, 'newChainData': {'hash': '0xdbe3f70368c5faf04fa1139b235e1770ee8f4b9a9411036c5700d945d46b731f'}}
2025-11-08 16:45:05 | INFO     | trading.live.aster_service_v3:execute_trade_intent:506 - Market order placed: 7629859617
2025-11-08 16:45:05 | ERROR    | trading.live.aster_service_v3:_place_stop_loss_order:698 - Stop-loss order failed: 400 - {"code":-1111,"msg":"Precision is over the maximum defined for this asset."}
2025-11-08 16:45:05 | INFO     | __main__:_monitor_log_file:172 - 📥 New error detected, processing...
2025-11-08 16:45:05 | INFO     | __main__:_process_error_line:224 - ✉️  Sending alert to Telegram...
2025-11-08 16:45:05 | INFO     | trading.live.aster_service_v3:execute_trade_intent:517 - Stop-loss order response: None
2025-11-08 16:45:05 | WARNING  | trading.live.aster_service_v3:execute_trade_intent:522 - Stop-loss order failed or returned no orderId
2025-11-08 16:45:05 | ERROR    | trading.live.aster_service_v3:_place_take_profit_order:742 - Take-profit order failed: 400 - {"code":-1111,"msg":"Precision is over the maximum defined for this asset."}
2025-11-08 16:45:05 | INFO     | trading.live.aster_service_v3:execute_trade_intent:533 - Take-profit order response: None
2025-11-08 16:45:05 | WARNING  | trading.live.aster_service_v3:execute_trade_intent:538 - Take-profit order failed or returned no orderId
2025-11-08 16:45:05 | INFO     | trading.live.aster_service_v3:execute_trade_intent:541 - Waiting 2s for trade to settle...
2025-11-08 16:45:06 | INFO     | __main__:_process_error_line:236 - ✅ Alert sent: ERROR in trading.live.aster_service_v3:_place_stop_loss_order:698
2025-11-08 16:45:06 | INFO     | __main__:_monitor_log_file:172 - 📥 New error detected, processing...
2025-11-08 16:45:06 | INFO     | __main__:_process_error_line:224 - ✉️  Sending alert to Telegram...
2025-11-08 16:45:06 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 1 open positions
2025-11-08 16:45:06 | INFO     | trading.live.aster_service_v3:get_open_positions:819 - Found 1 open positions
2025-11-08 16:45:06 | INFO     | __main__:_process_error_line:236 - ✅ Alert sent: ERROR in trading.live.aster_service_v3:_place_take_profit_order:742
2025-11-08 16:45:06 | INFO     | ggbot:generate:1430 - SSE stream cancelled for user 00000000-0000-0000-0000-000000000000
2025-11-08 16:45:07 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 5500 stored
2025-11-08 16:45:07 | INFO     | trading.live.aster_service_v3:_save_live_trade_record:767 - Saved AsterDEX trade record: 7629859617 for BTC/USDT
2025-11-08 16:45:07 | INFO     | trading.live.aster_service_v3:execute_trade_intent:593 - Activity logged for trade 7629859617
2025-11-08 16:45:07 | INFO     | ggbot:_run_trading_v2:1102 - V2 AsterDEX live trade completed: success for BTC/USDT
2025-11-08 16:45:10 | INFO     | ggbot:_run_autonomous_trading_cycle:422 - V2 autonomous cycle completed in 18236ms
2025-11-08 16:45:12 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 5600 stored
2025-11-08 16:45:17 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 5700 stored
2025-11-08 16:45:22 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 5800 stored
2025-11-08 16:45:26 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 5900 stored
2025-11-08 16:45:30 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 6000 stored
2025-11-08 16:45:34 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 6100 stored
2025-11-08 16:45:39 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 6200 stored
2025-11-08 16:45:44 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 6300 stored
2025-11-08 16:45:50 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 6400 stored
2025-11-08 16:45:56 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 6500 stored
2025-11-08 16:46:02 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 6600 stored
2025-11-08 16:46:06 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 6700 stored
2025-11-08 16:46:08 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 6800 stored
2025-11-08 16:46:13 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 6900 stored
2025-11-08 16:46:18 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 7000 stored
2025-11-08 16:46:23 | INFO     | __main__:_store_live_candle:430 - 📍 Live candles: 7100 stored
2025-11-08 16:46:26 | INFO     | ggbot:dashboard_stream:1445 - Starting SSE dashboard stream for user 00000000-0000-0000-0000-000000000000
2025-11-08 16:46:26 | INFO     | ggbot:generate:1402 - SSE generate function started for user 00000000-0000-0000-0000-000000000000
2025-11-08 16:46:27 | INFO     | core.services.config_service:list_configs:401 - Listed 4 configs for user 00000000-0000-0000-0000-000000000000
