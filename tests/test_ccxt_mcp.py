#!/usr/bin/env python
"""
Test script for the CCXT MCP.

This script tests connectivity and functionality of the CCXT MCP,
including fetching market data and using dynamic credentials.
"""

import os
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from pprint import pprint

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mcp.ccxt import CCXTMCPClient
from core.config.providers.env_credential_provider import EnvCredentialProvider
from core.mcp.dynamic_account import DynamicAccountManager


class TestCCXTMCP:
    """Test case for the CCXT MCP."""
    
    def __init__(self):
        self.client = None
        self.exchange_id = os.environ.get("EXCHANGE_NAME", "bitmex").lower()
        
        # Check if environment variables are set
        if not os.environ.get("EXCHANGE_API") or not os.environ.get("EXCHANGE_SECRET"):
            raise EnvironmentError(
                "EXCHANGE_API and EXCHANGE_SECRET environment variables must be set"
            )
    
    async def setup(self):
        """Set up the test by connecting to the MCP."""
        print(f"Connecting to CCXT MCP for exchange {self.exchange_id}...")
        
        # Create CCXT client with environment credentials
        self.client = CCXTMCPClient(exchange_id=self.exchange_id)
        await self.client.connect()
        print("Connected successfully!")
    
    async def teardown(self):
        """Clean up by disconnecting from the MCP."""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            print("Disconnected from CCXT MCP")
    
    async def test_exchange_list(self):
        """Test getting the list of available exchanges."""
        print("\n=== Testing Exchange List ===")
        exchanges = await self.client.get_exchange_ids()
        print(f"Available exchanges: {', '.join(exchanges[:10])}...")
        assert len(exchanges) > 0, "No exchanges returned from MCP"
        assert self.exchange_id in exchanges, f"{self.exchange_id} not found in exchange list"
    
    async def test_ticker(self):
        """Test fetching ticker data."""
        print("\n=== Testing Ticker Fetch ===")
        symbol = "BTC/USDT"
        print(f"Fetching ticker for {symbol} on {self.exchange_id}...")
        
        try:
            ticker = await self.client.fetch_ticker(self.exchange_id, symbol)
            
            print("Ticker data:")
            for key in ['last', 'bid', 'ask', 'high', 'low', 'volume']:
                if key in ticker:
                    print(f"{key}: {ticker[key]}")
            
            assert 'last' in ticker, "Ticker doesn't contain 'last' price"
            assert ticker['last'] > 0, "Last price should be positive"
        except Exception as e:
            print(f"Error fetching ticker: {str(e)}")
            # Try alternative symbol if needed
            if "symbol" in str(e).lower():
                print("Trying alternative symbol...")
                alternative_symbol = "BTC/USD"
                print(f"Fetching ticker for {alternative_symbol} on {self.exchange_id}...")
                ticker = await self.client.fetch_ticker(self.exchange_id, alternative_symbol)
                print(f"Success with {alternative_symbol}")
                for key in ['last', 'bid', 'ask', 'high', 'low', 'volume']:
                    if key in ticker:
                        print(f"{key}: {ticker[key]}")
            else:
                raise
    
    async def test_ohlcv(self):
        """Test fetching OHLCV data."""
        print("\n=== Testing OHLCV Fetch ===")
        symbol = "BTC/USDT"
        timeframe = "1h"
        limit = 10
        
        print(f"Fetching {limit} {timeframe} candles for {symbol} on {self.exchange_id}...")
        
        try:
            ohlcv = await self.client.fetch_ohlcv(
                self.exchange_id, 
                symbol, 
                timeframe=timeframe,
                limit=limit
            )
            
            print(f"Fetched {len(ohlcv)} candles")
            if len(ohlcv) > 0:
                # Display the first and last candle
                print("\nFirst candle:")
                first_candle = ohlcv[0]
                print(f"Time: {datetime.fromtimestamp(first_candle[0]/1000).strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"O: {first_candle[1]}, H: {first_candle[2]}, L: {first_candle[3]}, C: {first_candle[4]}, V: {first_candle[5]}")
                
                print("\nLast candle:")
                last_candle = ohlcv[-1]
                print(f"Time: {datetime.fromtimestamp(last_candle[0]/1000).strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"O: {last_candle[1]}, H: {last_candle[2]}, L: {last_candle[3]}, C: {last_candle[4]}, V: {last_candle[5]}")
            
            assert len(ohlcv) > 0, "No OHLCV data returned"
            assert len(ohlcv[0]) == 6, "OHLCV data should have 6 elements per candle"
        except Exception as e:
            print(f"Error fetching OHLCV: {str(e)}")
            # Try alternative symbol if needed
            if "symbol" in str(e).lower():
                print("Trying alternative symbol...")
                alternative_symbol = "BTC/USD"
                print(f"Fetching OHLCV for {alternative_symbol} on {self.exchange_id}...")
                ohlcv = await self.client.fetch_ohlcv(
                    self.exchange_id, 
                    alternative_symbol, 
                    timeframe=timeframe,
                    limit=limit
                )
                print(f"Success with {alternative_symbol}")
                print(f"Fetched {len(ohlcv)} candles")
            else:
                raise
    
    async def test_credential_provider(self):
        """Test the credential provider system."""
        print("\n=== Testing Credential Provider ===")
        
        # Create credential provider
        provider = EnvCredentialProvider()
        
        # Get credentials
        credentials = provider.get_credentials(self.exchange_id)
        options = provider.get_exchange_options(self.exchange_id)
        
        # Check credentials (mask for display)
        api_key = credentials.get('apiKey', '')
        secret = credentials.get('secret', '')
        
        print(f"API Key: {api_key[:5]}...{api_key[-3:] if len(api_key) > 8 else ''}")
        print(f"Secret: {secret[:5]}...{secret[-3:] if len(secret) > 8 else ''}")
        print(f"Options: {options}")
        
        assert api_key == os.environ.get("EXCHANGE_API"), "API key doesn't match environment variable"
        assert secret == os.environ.get("EXCHANGE_SECRET"), "Secret doesn't match environment variable"
    
    async def test_dynamic_account(self):
        """Test the dynamic account manager."""
        print("\n=== Testing Dynamic Account Manager ===")
        
        # Create manager
        manager = DynamicAccountManager()
        
        # Create config file
        config_path = manager.create_config_file(self.exchange_id)
        print(f"Created dynamic config at: {config_path}")
        
        # Read and display file (with secrets masked)
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Mask secrets for display
        for account in config.get("accounts", []):
            if "apiKey" in account and account["apiKey"]:
                api_key = account["apiKey"]
                account["apiKey"] = f"{api_key[:5]}...{api_key[-3:] if len(api_key) > 8 else ''}"
            if "secret" in account and account["secret"]:
                secret = account["secret"]
                account["secret"] = f"{secret[:5]}...{secret[-3:] if len(secret) > 8 else ''}"
        
        print("Dynamic config contents:")
        print(json.dumps(config, indent=2))
        
        assert os.path.exists(config_path), "Config file should exist"
        assert len(config.get("accounts", [])) > 0, "Config should contain at least one account"
        
        # Clean up
        if os.path.exists(config_path):
            os.remove(config_path)
            print(f"Removed dynamic config file: {config_path}")
    
    async def test_client_with_dynamic_config(self):
        """Test CCXT client with dynamic configuration."""
        print("\n=== Testing CCXT Client with Dynamic Configuration ===")
        
        # Create client with dynamic credentials
        client = CCXTMCPClient(exchange_id=self.exchange_id)
        await client.connect()
        
        print(f"Connected to CCXT MCP using dynamic config")
        print(f"Config path: {client.config_path}")
        
        # Test basic functionality
        exchanges = await client.get_exchange_ids()
        print(f"Available exchanges: {len(exchanges)}")
        assert self.exchange_id in exchanges, f"{self.exchange_id} should be in exchange list"
        
        # Clean up
        await client.disconnect()
        print("Disconnected client")
        
        # Clean up config file
        if os.path.exists(client.config_path) and 'ccxt-config-' in client.config_path:
            os.remove(client.config_path)
            print(f"Removed dynamic config file: {client.config_path}")

    async def run_all_tests(self):
        """Run all the tests."""
        try:
            await self.setup()
            
            # Run tests
            await self.test_exchange_list()
            await self.test_ticker()
            await self.test_ohlcv()
            await self.test_credential_provider()
            await self.test_dynamic_account()
            await self.test_client_with_dynamic_config()
            
            print("\n=== All tests completed successfully! ===")
        except Exception as e:
            print(f"\n=== Test failed: {str(e)} ===")
            raise
        finally:
            await self.teardown()


async def main():
    """Main entry point."""
    tester = TestCCXTMCP()
    await tester.run_all_tests()


if __name__ == "__main__":
    # Check environment variables
    if not os.environ.get("EXCHANGE_NAME") or \
       not os.environ.get("EXCHANGE_API") or \
       not os.environ.get("EXCHANGE_SECRET"):
        print("Error: EXCHANGE_NAME, EXCHANGE_API and EXCHANGE_SECRET must be set in environment.")
        sys.exit(1)
    
    print("Running CCXT MCP tests...")
    asyncio.run(main())