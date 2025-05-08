"""
Test script for environment-based credential management with CCXT MCP.

This script tests the environment credential provider implementation
for CCXT MCP, using the EXCHANGE_NAME, EXCHANGE_API, and EXCHANGE_SECRET
environment variables.
"""

import os
import json
import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config.providers.env_credential_provider import EnvCredentialProvider
from core.mcp.dynamic_account import DynamicAccountManager
from core.mcp.ccxt import CCXTMCPClient


async def test_env_credential_provider():
    """Test the environment credential provider."""
    print("\n=== Testing EnvCredentialProvider ===")
    
    # Initialize the provider
    provider = EnvCredentialProvider()
    
    # Get exchange name from environment
    exchange_id = os.environ.get("EXCHANGE_NAME", "").lower()
    if not exchange_id:
        print("EXCHANGE_NAME not set in environment.")
        return
    
    print(f"Using exchange: {exchange_id}")
    
    try:
        # Get credentials
        credentials = provider.get_credentials(exchange_id)
        print(f"Successfully retrieved credentials for {exchange_id}")
        print(f"API Key: {credentials['apiKey'][:5]}...{credentials['apiKey'][-3:]}")
        
        # Get options
        options = provider.get_exchange_options(exchange_id)
        print(f"Exchange options: {options}")
        
    except Exception as e:
        print(f"Error retrieving credentials: {str(e)}")


async def test_dynamic_account_manager():
    """Test the dynamic account manager."""
    print("\n=== Testing DynamicAccountManager ===")
    
    # Initialize the manager
    manager = DynamicAccountManager()
    
    # Get exchange name from environment
    exchange_id = os.environ.get("EXCHANGE_NAME", "").lower()
    if not exchange_id:
        print("EXCHANGE_NAME not set in environment.")
        return
    
    print(f"Using exchange: {exchange_id}")
    
    try:
        # Create config file
        config_path = manager.create_config_file(exchange_id)
        print(f"Successfully created dynamic config file at: {config_path}")
        
        # Read and display the file (with secrets partially masked)
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Mask secrets for display
        for account in config.get("accounts", []):
            if "apiKey" in account and account["apiKey"]:
                api_key = account["apiKey"]
                account["apiKey"] = f"{api_key[:5]}...{api_key[-3:]}" if len(api_key) > 8 else "[MASKED]"
            if "secret" in account and account["secret"]:
                secret = account["secret"]
                account["secret"] = f"{secret[:5]}...{secret[-3:]}" if len(secret) > 8 else "[MASKED]"
                
        # Pretty print the config
        print(json.dumps(config, indent=2))
        
    except Exception as e:
        print(f"Error creating dynamic config: {str(e)}")


async def main():
    """Run the credential provider tests."""
    print("=== Environment-Based Credential Tests ===")
    
    # Check environment variables
    missing_vars = []
    for var in ["EXCHANGE_NAME", "EXCHANGE_API", "EXCHANGE_SECRET"]:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please ensure these variables are set in the .env file or environment.")
        return
    
    # Run the tests
    await test_env_credential_provider()
    await test_dynamic_account_manager()
    
    print("\nTests completed. Next steps:")
    print(" 1. Verify dynamic credential loading works as expected")
    print(" 2. Update CCXTMCPClient usages to pass exchange_id directly")
    print(" 3. Create a CCXT exchange data source implementation")


if __name__ == "__main__":
    asyncio.run(main())