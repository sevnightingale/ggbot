#!/usr/bin/env python
"""
Test Trading Module Integration with BitMEX Testnet.

This script tests the full flow of the Trading Module by:
1. Creating a mock decision from the Decision Module
2. Processing it through the TradingEngine
3. Executing the resulting trades on BitMEX testnet
4. Verifying the position was created successfully
"""

import os
import sys
import json
import uuid
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
load_dotenv()

# Import necessary modules
from core.common.logger import logger
from trading.engine import TradingEngine
from trading.compiler import TradeCompiler
from trading.exchanges.ccxt_mcp import CCXTMCPAdapter

# Configure logging for the test
logger.configure(handlers=[{"sink": sys.stdout, "level": logging.INFO}])

# Create mock decision from Decision Module
def create_mock_decision(symbol="BTC/USD", direction="long", leverage=2):
    """
    Create a mock decision from the Decision Module.
    
    Args:
        symbol: Trading pair symbol
        direction: Trade direction ('long' or 'short')
        leverage: Leverage to use
        
    Returns:
        Mock decision dictionary
    """
    decision_id = str(uuid.uuid4())
    
    # Action is either enter_long or enter_short based on direction
    action = f"enter_{direction}"
    
    return {
        "decision_id": decision_id,
        "action": action,
        "symbol": symbol,
        "exchange": "bitmex",
        "timeframe": "15m",
        # Use very small amount for testing (0.001 BTC ≈ $50-70)
        "size_type": "fixed_contracts",
        "size_value": 1,  # Just 1 contract for testing
        "leverage": leverage,
        "stop_loss_price": 60000 if direction == "long" else 70000,  # Example SL prices
        "take_profit_price": 70000 if direction == "long" else 60000,  # Example TP prices
        "confidence": 0.85,
        "reasoning": "This is a test trade to verify the Trading Module functionality with BitMEX testnet."
    }

async def check_position_status(ccxt_adapter, symbol):
    """
    Check if a position exists for the given symbol.
    
    Args:
        ccxt_adapter: CCXT MCP adapter instance
        symbol: Symbol to check
        
    Returns:
        Position details or None if not found
    """
    try:
        # Don't try to reconnect - use existing connection
        logger.info(f"Checking positions for {symbol} using existing connection")
        
        # Map symbol before calling
        mapped_symbol = ccxt_adapter.map_symbol(symbol)
        logger.info(f"Mapped {symbol} to {mapped_symbol} for {ccxt_adapter.exchange_id}")
        
        # First, check if this exchange supports fetch_positions
        # by getting available tools and checking their names
        try:
            # Get tools to check if fetch_positions is available
            tools = await ccxt_adapter.mcp_client.session.get_tools()
            tool_names = [tool.name for tool in tools]
            
            has_fetch_positions = 'fetch_positions' in tool_names
            
            if not has_fetch_positions:
                logger.warning(f"Exchange {ccxt_adapter.exchange_id} does not support fetch_positions")
                logger.info("Available tools: " + ", ".join(tool_names[:10]))
                logger.info("Falling back to fetch_balance to check for open positions")
                
                # Use fetch_balance as fallback
                balance_result = await ccxt_adapter.mcp_client.session.call_tool('fetch_balance', {
                    'exchange_id': ccxt_adapter.exchange_id,
                    'user_id': ccxt_adapter.user_id
                })
                
                # Log received balance keys for debugging
                if isinstance(balance_result, dict):
                    logger.info(f"Balance keys: {', '.join(list(balance_result.keys())[:5])}")
                    
                    # Some exchanges include position info in the balance response
                    if 'info' in balance_result and isinstance(balance_result['info'], dict):
                        logger.info("Checking balance.info for position data")
                        # Specific exchange handling could be added here
                
                return None
            
            # If we have fetch_positions, use it
            logger.info("Exchange supports fetch_positions, calling tool")
            
            # Prepare parameters
            params = {
                'exchange_id': ccxt_adapter.exchange_id,
                'user_id': ccxt_adapter.user_id
            }
            
            if mapped_symbol:
                params['symbol'] = mapped_symbol
                
            # Call tool directly on session
            positions = await ccxt_adapter.mcp_client.session.call_tool('fetch_positions', params)
            
            # Process results
            if isinstance(positions, list):
                logger.info(f"Received {len(positions)} positions from exchange")
                
                for position in positions:
                    position_symbol = position.get("symbol", "")
                    if position_symbol == symbol or position_symbol == mapped_symbol:
                        # Position found
                        contracts = position.get("contracts", 0)
                        if contracts and abs(float(contracts)) > 0:
                            logger.info(f"Found active position for {symbol} with {contracts} contracts")
                            return position
                        else:
                            logger.info(f"Found position for {symbol} but it has 0 contracts")
                            
                # No matching position found
                logger.info(f"No position found for symbol {symbol}")
            else:
                logger.warning(f"Unexpected response from fetch_positions: {positions}")
                
            # No position found or error occurred
            return None
        except Exception as e:
            logger.warning(f"Error in position checking flow: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Error checking position status: {str(e)}")
        return None

async def main():
    """Main test function."""
    # Create a unique user ID for this test run using a proper UUID
    # This resolves the PostgreSQL error: "invalid input syntax for type uuid"
    user_id = str(uuid.uuid4())
    
    # Get exchange credentials from environment variables
    exchange_id = os.environ.get("EXCHANGE_NAME", "bitmex")
    api_key = os.environ.get("EXCHANGE_API")
    api_secret = os.environ.get("EXCHANGE_SECRET")
    
    if not api_key or not api_secret:
        logger.error("EXCHANGE_API and EXCHANGE_SECRET must be set in .env")
        return False
    
    logger.info(f"Starting Trading Module test with BitMEX testnet as user {user_id}")
    logger.info(f"Using exchange: {exchange_id}")
    
    # Create configuration
    server_path = str(Path(__file__).parent.parent / "core" / "mcp" / "servers" / "ccxt_mcp_server.py")
    
    config = {
        "use_mock_llm": False,  # Use real LLM API calls
        "default_exchange": exchange_id,
        "use_testnet": True,  # Use BitMEX testnet, following research recommendations
        "server_path": server_path,  # Explicit server path for the CCXT MCP server
        "risk_rules": {
            "max_leverage": 10,
            "max_risk_per_trade_pct": 0.05  # 5% of equity
        },
        # Add explicit credentials here to avoid potential missing fields issues
        "credentials": {
            "apiKey": api_key,
            "secret": api_secret
        },
        # Add LLM config for new structure
        "llm": {
            "model": "gpt-4.1",
            "system_prompt": "You are an expert trading assistant. Your task is to help execute trading decisions through the CCXT API.",
            "temperature": 0.0,
            "max_retries": 3
        },
        # Add validation config
        "validation": {
            "max_leverage": 10,
            "max_position_pct": 0.05
        },
        # Add execution config
        "execution": {
            "polling_interval": 60,
            "max_retries": 3
        }
    }
    
    # Set environment variables for CCXT MCP
    os.environ["EXCHANGE_NAME"] = exchange_id
    os.environ["EXCHANGE_API"] = api_key
    os.environ["EXCHANGE_SECRET"] = api_secret
    
    # Create components (but don't connect yet)
    ccxt_adapter = None
    trading_engine = None
    result = None
    success = False
    
    try:
        # IMPORTANT: Follow the pattern from simplified_llm_mcp_test.py
        # Create a single MCP client instance that will be reused
        from core.mcp.ccxt import CCXTMCPClient
        
        # Create the MCP client with explicit server path
        mcp_client = CCXTMCPClient(
            exchange_id=exchange_id,
            user_id=user_id,
            use_local_server=True,
            server_path=server_path
        )
        
        # Connect once at the beginning
        logger.info("Connecting to MCP server directly...")
        await mcp_client.connect()
        logger.info("Successfully connected to MCP server")
        
        # Create adapter without having it make its own connection
        # We'll provide the already connected client
        ccxt_adapter = CCXTMCPAdapter(exchange_id, user_id, config)
        ccxt_adapter.mcp_client = mcp_client  # Use the existing connection
        ccxt_adapter.connected = True  # Mark as already connected
        
        # Create trading engine
        logger.info("Creating TradingEngine...")
        trading_engine = TradingEngine(user_id, config)
        
        # Replace components with our test instances
        trading_engine.ccxt_adapter = ccxt_adapter
        
        # Create mock decision
        mock_decision = create_mock_decision()
        symbol = mock_decision.get("symbol")
        direction = "long" if mock_decision.get("action") == "enter_long" else "short"
        
        logger.info(f"Created mock decision with ID {mock_decision['decision_id']}")
        logger.info(f"Decision: {direction} {symbol}")
        
        # Check for existing positions before the test
        logger.info("Checking for existing positions before test...")
        existing_position = await check_position_status(ccxt_adapter, symbol)
        
        if existing_position and abs(existing_position.get("contracts", 0)) > 0:
            logger.warning(f"Position already exists for {symbol}. Consider closing it before testing.")
            logger.info(f"Existing position: {json.dumps(existing_position, indent=2)}")
        else:
            logger.info(f"No existing position found for {symbol}. Good to proceed.")
        
        # Process the decision using structured concurrency pattern
        logger.info("Processing mock decision through TradingEngine...")
        
        try:
            # Add debug function to trace through response handling
            if hasattr(trading_engine.llm_service, 'llm_client'):
                # Enhanced debug handlers
                if hasattr(trading_engine.llm_service.llm_client, 'chat') and \
                   hasattr(trading_engine.llm_service.llm_client.chat, 'completions') and \
                   hasattr(trading_engine.llm_service.llm_client.chat.completions, 'create'):
                
                    orig_create_completions = trading_engine.llm_service.llm_client.chat.completions.create
                    
                    def debug_wrapped_completions(*args, **kwargs):
                        logger.info("Creating OpenAI completion with original client...")
                        response = orig_create_completions(*args, **kwargs)
                        logger.info(f"Response type: {type(response)}")
                        logger.info(f"Response dir: {dir(response)}")
                        logger.info(f"Response has 'choices'? {hasattr(response, 'choices')}")
                        
                        if hasattr(response, 'choices') and len(response.choices) > 0:
                            first_choice = response.choices[0]
                            logger.info(f"First choice type: {type(first_choice)}")
                            logger.info(f"First choice dir: {dir(first_choice)}")
                            logger.info(f"First choice has 'message'? {hasattr(first_choice, 'message')}")
                            
                            if hasattr(first_choice, 'message'):
                                message = first_choice.message
                                logger.info(f"Message type: {type(message)}")
                                logger.info(f"Message dir: {dir(message)}")
                                logger.info(f"Message has 'content'? {hasattr(message, 'content')}")
                                
                                if hasattr(message, 'content'):
                                    content = message.content
                                    logger.info(f"Content type: {type(content)}")
                                    logger.info(f"Content (truncated): {content[:100]}...")
                        
                        return response
                    
                    # Replace the method with our debug wrapper
                    trading_engine.llm_service.llm_client.chat.completions.create = debug_wrapped_completions
                    
            # Log that we're making a real LLM API call
            logger.info("Processing decision intent with real LLM API call - this may take a few seconds...")
            
            # Use explicit try/except to catch any errors
            start_time = datetime.now()
            result = await trading_engine.process_decision_intent(mock_decision)
            elapsed_time = datetime.now() - start_time
            
            logger.info(f"LLM processing completed in {elapsed_time.total_seconds():.2f} seconds")
        except ValueError as e:
            if "Invalid format specifier" in str(e):
                logger.error(f"String formatting error in process_decision_intent: {e}")
                # This is likely related to the BTC/USD string formatting issue
                # Return an error result
                result = {
                    "status": "error",
                    "decision_id": mock_decision["decision_id"],
                    "message": f"String formatting error: {str(e)}"
                }
            else:
                # Re-raise other ValueError exceptions
                raise
        except Exception as e:
            logger.error(f"Error processing decision intent with LLM: {e}", exc_info=True)
            # Return a generic error result
            result = {
                "status": "error",
                "decision_id": mock_decision["decision_id"],
                "message": f"LLM processing error: {str(e)}"
            }
        
        # Log the result
        logger.info(f"Process result: {json.dumps(result, indent=2)}")
        
        if result.get('status') == 'success':
            logger.info("Decision processed successfully!")
            trade_id = result.get('trade_id')
            
            # Wait a moment for the exchange to process the order
            logger.info("Waiting 5 seconds for the exchange to process...")
            await asyncio.sleep(5)
            
            # Check if position was created
            logger.info("Checking if position was created...")
            position = await check_position_status(ccxt_adapter, symbol)
            
            if position and abs(position.get("contracts", 0)) > 0:
                logger.info("Position created successfully!")
                logger.info(f"Position details: {json.dumps(position, indent=2)}")
                
                # Log key position details
                contracts = position.get("contracts", 0)
                side = "long" if contracts > 0 else "short"
                entry_price = position.get("entryPrice", "unknown")
                
                logger.info(f"Created {side} position with {abs(contracts)} contracts at {entry_price}")
                success = True
            else:
                logger.error("Position not found after trade execution!")
        else:
            logger.error(f"Decision processing failed: {result.get('message', 'Unknown error')}")
    
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
    
    finally:
        # Clean up connections - follow the pattern from simplified_llm_mcp_test.py
        logger.info("Cleaning up resources...")
        
        # Clean up MCP client properly
        if 'mcp_client' in locals() and mcp_client is not None:
            logger.info("Disconnecting from CCXT MCP server...")
            try:
                await mcp_client.disconnect()
                logger.info("Successfully disconnected from CCXT MCP server")
            except Exception as e:
                logger.error(f"Error during MCP client disconnect: {str(e)}")
        
        logger.info("Test completed.")
        return success

# Add detailed debug function to compare with simplified test
def debug_openai_response():
    """Debug the OpenAI API response format."""
    try:
        from openai import OpenAI
        import os
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        # Get API key
        api_key = os.environ.get("TRADING_LLM_API_KEY")
        if not api_key:
            print("No API key found in TRADING_LLM_API_KEY")
            return
            
        # Create client
        print("Creating OpenAI client...")
        client = OpenAI(api_key=api_key)
        
        # Make API call - directly matching simplified_llm_mcp_test.py approach
        print("Making API call...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello world"}
            ],
            temperature=0
        )
        
        # Debug response
        print(f"Response type: {type(response)}")
        print(f"Response dir: {dir(response)}")
        print(f"Response has 'choices'? {hasattr(response, 'choices')}")
        
        if hasattr(response, 'choices') and len(response.choices) > 0:
            first_choice = response.choices[0]
            print(f"First choice type: {type(first_choice)}")
            print(f"First choice dir: {dir(first_choice)}")
            print(f"First choice has 'message'? {hasattr(first_choice, 'message')}")
            
            if hasattr(first_choice, 'message'):
                message = first_choice.message
                print(f"Message type: {type(message)}")
                print(f"Message dir: {dir(message)}")
                print(f"Message has 'content'? {hasattr(message, 'content')}")
                
                if hasattr(message, 'content'):
                    content = message.content
                    print(f"Content type: {type(content)}")
                    print(f"Content: {content}")
        
        print("Response structure check complete")
        
    except Exception as e:
        print(f"Error in debug_openai_response: {e}")

if __name__ == "__main__":
    # Import the direct debug function from engine.py
    from trading.engine import debug_openai_direct
    
    # Debug OpenAI response format first
    print("\n=== DEBUGGING OPENAI RESPONSE FORMAT (DIRECT) ===\n")
    debug_openai_direct()
    print("\n=== DEBUGGING OPENAI RESPONSE FORMAT (FROM TEST) ===\n")
    debug_openai_response()
    print("\n=== DEBUG COMPLETE, RUNNING MAIN TEST ===\n")
    
    # Run the test
    success = asyncio.run(main())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)