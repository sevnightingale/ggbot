(.venv) sev@ggbot-vm:~/ggbot$ python tests/mcp_example.py

=== CCXT MCP Client Demo ===
2025-05-05 04:57:38 | INFO     | User: 00000000-0000-0000-0000-000000000001 | core.config.config_main:get_configuration:45 - Retrieved configuration from database for user 00000000-0000-0000-0000-000000000001
2025-05-05 04:57:38 | WARNING  | User: 00000000-0000-0000-0000-000000000001 | core.mcp.config:get_mcp_config:46 - No configuration found for ccxt MCP
2025-05-05 04:57:38 | INFO     | User: 00000000-0000-0000-0000-000000000001 | core.mcp.client:connect:73 - Connecting to CCXT MCP server
2025-05-05 04:57:38 | ERROR    | User: 00000000-0000-0000-0000-000000000001 | core.mcp.client:connect:106 - Failed to connect to CCXT MCP server: 1 validation error for StdioServerParameters
command
  Input should be a valid string [type=string_type, input_value=['ccxt-mcp', '--config', ...fig/ccxt-accounts.json'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.10/v/string_type
Error in CCXT MCP demo: Failed to connect to CCXT MCP server: 1 validation error for StdioServerParameters
command
  Input should be a valid string [type=string_type, input_value=['ccxt-mcp', '--config', ...fig/ccxt-accounts.json'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.10/v/string_type
Disconnected from CCXT MCP server

=== Crypto Indicators MCP Client Demo ===
2025-05-05 04:57:38 | INFO     | User: 00000000-0000-0000-0000-000000000001 | core.config.config_main:get_configuration:45 - Retrieved configuration from database for user 00000000-0000-0000-0000-000000000001
2025-05-05 04:57:38 | WARNING  | User: 00000000-0000-0000-0000-000000000001 | core.mcp.config:get_mcp_config:46 - No configuration found for indicators MCP
2025-05-05 04:57:38 | INFO     | User: 00000000-0000-0000-0000-000000000001 | core.mcp.client:connect:73 - Connecting to Crypto Indicators MCP server
2025-05-05 04:57:38 | ERROR    | User: 00000000-0000-0000-0000-000000000001 | core.mcp.client:connect:106 - Failed to connect to Crypto Indicators MCP server: 2 validation errors for StdioServerParameters
command
  Input should be a valid string [type=string_type, input_value=['node', '/home/sev/ggbot...ndicators-mcp/index.js'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.10/v/string_type
env.EXCHANGE_NAME
  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
    For further information visit https://errors.pydantic.dev/2.10/v/string_type
Error in Crypto Indicators MCP demo: Failed to connect to Crypto Indicators MCP server: 2 validation errors for StdioServerParameters
command
  Input should be a valid string [type=string_type, input_value=['node', '/home/sev/ggbot...ndicators-mcp/index.js'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.10/v/string_type
env.EXCHANGE_NAME
  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
    For further information visit https://errors.pydantic.dev/2.10/v/string_type
Disconnected from Crypto Indicators MCP server

=== MCP DataSource Integration Demo ===
Error in MCP DataSource demo: Can't instantiate abstract class CCXTMCPDataSource with abstract methods get_current_price, get_latest_data, get_source_name, get_supported_symbols, get_supported_timeframes
(.venv) sev@ggbot-vm:~/ggbot$ 