import asyncio
from mcp.client import StdioServerParameters, stdio_client, ClientSession
import os

async def connect_to_ccxt_mcp():
    config_path = os.path.expanduser('~/ggbot/config/ccxt-accounts.json')
    params = StdioServerParameters(
        command=['ccxt-mcp', '--config', config_path]
    )
    async with stdio_client(params) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            print("Connected to CCXT MCP")

async def connect_to_crypto_indicators_mcp():
    server_path = os.path.expanduser('~/ggbot/mcp_servers/crypto-indicators-mcp/index.js')
    params = StdioServerParameters(
        command=['node', server_path],
        env={'EXCHANGE_NAME': 'binance'}
    )
    async with stdio_client(params) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            print("Connected to Crypto Indicators MCP")

async def main():
    await asyncio.gather(
        connect_to_ccxt_mcp(),
        connect_to_crypto_indicators_mcp()
    )

if __name__ == "__main__":
    asyncio.run(main())