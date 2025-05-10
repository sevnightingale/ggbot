(.venv) sev@ggbot-vm:~/ggbot$ python -m tests.test_indicators_mcp
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/sev/ggbot/tests/test_indicators_mcp.py", line 23, in <module>
    from extraction.indicators.pandas_ta_indicators import PandasTaIndicators
ImportError: cannot import name 'PandasTaIndicators' from 'extraction.indicators.pandas_ta_indicators' (/home/sev/ggbot/extraction/indicators/pandas_ta_indicators.py)
(.venv) sev@ggbot-vm:~/ggbot$ python -m tests.test_dynamic_credentials
=== Environment-Based Credential Tests ===

=== Testing EnvCredentialProvider ===
Using exchange: bitmex
Successfully retrieved credentials for bitmex
API Key: arfvF..._f4
Exchange options: {'test': True}

=== Testing DynamicAccountManager ===
Using exchange: bitmex
2025-05-08 23:20:07 | INFO     | User: system | core.mcp.dynamic_account:create_config_file:111 - Created dynamic config for bitmex at /tmp/ccxt-config-bitmex-wmjd5hfb.json
Successfully created dynamic config file at: /tmp/ccxt-config-bitmex-wmjd5hfb.json
{
  "accounts": [
    {
      "id": "bitmex-b1888e54",
      "exchangeId": "bitmex",
      "apiKey": "arfvF..._f4",
      "secret": "a8XHh...IGU",
      "description": "Dynamic Bitmex Account",
      "tag": "dynamic",
      "options": {
        "test": true
      }
    }
  ]
}

Tests completed. Next steps:
 1. Verify dynamic credential loading works as expected
 2. Update CCXTMCPClient usages to pass exchange_id directly
 3. Create a CCXT exchange data source implementation
(.venv) sev@ggbot-vm:~/ggbot$ python -m tests.test_ccxt_mcp
Running CCXT MCP tests...
Connecting to CCXT MCP for exchange bitmex...
2025-05-08 23:20:32 | INFO     | User: 00000000-0000-0000-0000-000000000001 | core.config.config_main:get_configuration:45 - Retrieved configuration from database for user 00000000-0000-0000-0000-000000000001
2025-05-08 23:20:32 | WARNING  | User: 00000000-0000-0000-0000-000000000001 | core.mcp.config:get_mcp_config:46 - No configuration found for ccxt MCP
2025-05-08 23:20:32 | INFO     | User: system | core.mcp.dynamic_account:create_config_file:111 - Created dynamic config for bitmex at /tmp/ccxt-config-bitmex-ar6orf6l.json
2025-05-08 23:20:32 | INFO     | User: 00000000-0000-0000-0000-000000000001 | core.mcp.client:connect:76 - Connecting to CCXT MCP server
Task exception was never retrieved
future: <Task finished name='Task-6' coro=<<async_generator_athrow without __name__>()> exception=RuntimeError('Attempted to exit cancel scope in a different task than it was entered in')>
  + Exception Group Traceback (most recent call last):
  |   File "/home/sev/ggbot/.venv/lib/python3.11/site-packages/anyio/_backends/_asyncio.py", line 772, in __aexit__
  |     raise BaseExceptionGroup(
  | BaseExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "/home/sev/ggbot/.venv/lib/python3.11/site-packages/mcp/client/stdio/__init__.py", line 173, in stdio_client
    |     yield read_stream, write_stream
    | GeneratorExit
    +------------------------------------

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/sev/ggbot/.venv/lib/python3.11/site-packages/mcp/client/stdio/__init__.py", line 166, in stdio_client
    async with (
  File "/home/sev/ggbot/.venv/lib/python3.11/site-packages/anyio/_backends/_asyncio.py", line 778, in __aexit__
    if self.cancel_scope.__exit__(type(exc), exc, exc.__traceback__):
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/sev/ggbot/.venv/lib/python3.11/site-packages/anyio/_backends/_asyncio.py", line 457, in __exit__
    raise RuntimeError(
RuntimeError: Attempted to exit cancel scope in a different task than it was entered in
2025-05-08 23:20:32 | ERROR    | User: 00000000-0000-0000-0000-000000000001 | core.mcp.client:connect:119 - Failed to connect to CCXT MCP server: 

=== Test failed: Failed to connect to CCXT MCP server:  ===
Traceback (most recent call last):
  File "/home/sev/ggbot/core/mcp/client.py", line 104, in connect
    await asyncio.wait_for(
  File "/usr/lib/python3.11/asyncio/tasks.py", line 484, in wait_for
    return fut.result()
           ^^^^^^^^^^^^
  File "/home/sev/ggbot/.venv/lib/python3.11/site-packages/mcp/client/session.py", line 126, in initialize
    result = await self.send_request(
             ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/sev/ggbot/.venv/lib/python3.11/site-packages/mcp/shared/session.py", line 243, in send_request
    await self._write_stream.send(JSONRPCMessage(jsonrpc_request))
  File "/home/sev/ggbot/.venv/lib/python3.11/site-packages/anyio/streams/memory.py", line 242, in send
    self.send_nowait(item)
  File "/home/sev/ggbot/.venv/lib/python3.11/site-packages/anyio/streams/memory.py", line 211, in send_nowait
    raise ClosedResourceError
anyio.ClosedResourceError

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/sev/ggbot/tests/test_ccxt_mcp.py", line 260, in <module>
    asyncio.run(main())
  File "/usr/lib/python3.11/asyncio/runners.py", line 188, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.11/asyncio/runners.py", line 120, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.11/asyncio/base_events.py", line 650, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/home/sev/ggbot/tests/test_ccxt_mcp.py", line 248, in main
    await tester.run_all_tests()
  File "/home/sev/ggbot/tests/test_ccxt_mcp.py", line 227, in run_all_tests
    await self.setup()
  File "/home/sev/ggbot/tests/test_ccxt_mcp.py", line 44, in setup
    await self.client.connect()
  File "/home/sev/ggbot/core/mcp/client.py", line 120, in connect
    raise MCPConnectionError(f"Failed to connect to {self.server_name} MCP server: {str(e)}")
core.mcp.exceptions.MCPConnectionError: Failed to connect to CCXT MCP server: 
(.venv) sev@ggbot-vm:~/ggbot$ 