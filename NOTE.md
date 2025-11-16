page-c801754c3dbaac7f.js:1 Cannot set data: 
{hasLineSeries: true, dataLength: 0}
page-c801754c3dbaac7f.js:1 useEffect running 
{configId: '84d2b5d2-5985-4bbb-acbd-04bd541051c9', hasContainer: true, hasSession: true}
page-c801754c3dbaac7f.js:1 Creating chart with dimensions: 
{width: 898, height: 598}
page-c801754c3dbaac7f.js:1 Chart created: true
page-c801754c3dbaac7f.js:1 Line series created: true
page-c801754c3dbaac7f.js:1 About to call fetchData...
page-c801754c3dbaac7f.js:1 fetchData starting... 
{configId: '84d2b5d2-5985-4bbb-acbd-04bd541051c9', hasSession: true}
page-c801754c3dbaac7f.js:1 Fetching from API...
page-c801754c3dbaac7f.js:1 Setting up polling interval...
page-c801754c3dbaac7f.js:1 🔄 Switched to bot: 84d2b5d2-5985-4bbb-acbd-04bd541051c9 ggbot 3
page-c801754c3dbaac7f.js:1 🔄 Poll skipped: 
{selectedConfigId: '84d2b5d2-5985-4bbb-acbd-04bd541051c9', configType: undefined, userId: '00000000-0000-0000-0000-000000000000'}
page-c801754c3dbaac7f.js:1 
 GET https://app.ggbots.ai/api/v2/snapshots/84d2b5d2-5985-4bbb-acbd-04bd541051c9/balance-series 500 (Internal Server Error)
page-c801754c3dbaac7f.js:1 API responses: 
{balanceOk: false, balanceStatus: 500, activitiesOk: true, activitiesStatus: 200, metadataOk: true, …}
684-96a35eafa40ce8c6.js:1 API errors: 
{balanceError: '{"status":"error","error":"SSL connection has been closed unexpectedly\\n","status_code":500}', activitiesError: '{"status":"success","activities":[{"id":"0fc88dbd-…,"trade_id":null,"trade_type":null}}],"count":11}', metadataError: '{"status":"success","metadata":{"bot_name":"ggbot …,"createdAt":"2025-11-13T12:43:39.538904+00:00"}}'}

684-96a35eafa40ce8c6.js:1 Error fetching timeline data: Error: Failed to fetch timeline data
    at e (page-c801754c3dbaac7f.js:1:69741)


> ggbot errors:
🟠 ERROR

Time: 2025-11-16 00:16:00
Location: __main__:_start_websocket_streams:278

Message:
⚠️ Connection silent for 60s (uptime: 14.4min) - reconnecting

> ggbot errors:
🟠 ERROR

Time: 2025-11-16 00:19:52
Location: core.auth.vault_utils:get_symphony_credential:318

Message:
Failed to retrieve Symphony credential: SSL connection has been closed unexpectedly

> ggbot errors:
🟠 ERROR

Time: 2025-11-16 00:19:52
Location: trading.live.symphony_service:get_account_metrics:570

Message:
No Symphony credentials for user 00000000-0000-0000-0000-000000000000

> ggbot errors:
🟠 ERROR

Time: 2025-11-16 00:20:09
Location: trading.live.symphony_service:get_account_metrics:627

Message:
Failed to get Symphony account metrics: SSL connection has been closed unexpectedly

> ggbot errors:
🟠 ERROR

Time: 2025-11-16 00:25:32
Location: core.sse.dashboard_data:get_unified_dashboard_data:68

Message:
Failed to get unified dashboard data for user 00000000-0000-0000-0000-000000000000: SSL connection has been closed unexpectedly

> ggbot errors:
🟠 ERROR

Time: 2025-11-16 00:27:57
Location: trading.paper.supabase_service:_batch_update_positions_sql:792

Message:
❌ Batch SQL update failed: SSL connection has been closed unexpectedly

> ggbot errors:
🟠 ERROR

Time: 2025-11-16 00:31:00
Location: __main__:_start_websocket_streams:278

Message:
⚠️ Connection silent for 60s (uptime: 15.0min) - reconnecting
