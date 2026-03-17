Time: 2026-03-17 12:43:32
Location: trading.paper.supabase_service:get_account_summary:905

Message:
Failed to get account summary: {'message': 'invalid input syntax for type uuid: "temp-1773751410790"', 'code': '22P02', 'hint': None, 'details': None}

🟠 ERROR

Time: 2026-03-17 14:07:31
Location: core.services.rei_service:_request_with_retry:275

Message:
Rei API client error 400: {'error': 'AppError', 'details': 'error reading response body: read tcp 10.60.3.7:41270->104.18.2.115:443: read: connection reset by peer'}

🟠 ERROR

Time: 2026-03-17 14:07:31
Location: decision.rei_engine:report_trade_outcome_to_rei:582 [cfg=4060437e]

Message:
Failed to report outcome to Rei: Rei API error: Client error '400 Bad Request' for url 'https://api.reilabs.org/v1/chat/completions'

🟠 ERROR

Time: 2026-03-17 15:02:11
Location: market_intelligence.adapters.macro.coingecko_global:fetch:130

Message:
Error fetching CoinGecko global data: TimeoutError:

