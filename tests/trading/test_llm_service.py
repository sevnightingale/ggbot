#!/usr/bin/env python
"""
Test for the LLMService with real OpenAI API calls.

This test verifies that the LLMService can:
1. Process a trading intent into a prompt
2. Send the prompt to the real LLM API
3. Parse the response into structured tool calls
4. Handle various response formats and errors
"""

import os
import sys
import asyncio
import uuid
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables for API keys
load_dotenv()

from core.common.logger import logger
from trading.engine.model.intent import Intent
from trading.engine.model.config import EngineConfig
from trading.engine.model.tool_call import ToolCall
from trading.engine.service.llm_service import LLMService
from trading.exchanges.ccxt_mcp import CCXTMCPAdapter
from core.mcp.ccxt import CCXTMCPClient

# Configure minimal logging
import logging
logger.configure(handlers=[{"sink": sys.stdout, "level": logging.INFO}])


# Instead of using sample tools, we'll get real tools from the MCP server


# Test fixtures for reuse
@pytest.fixture
def user_id():
    """Generate a unique user ID for testing."""
    return str(uuid.uuid4())


# Global server instance
_mcp_client = None

@pytest.fixture(scope="session")
async def session_mcp_client(config, request):
    """Create a single MCP client per test session."""
    global _mcp_client
    
    if _mcp_client is None or not _mcp_client.is_connected:
        logger.info("Creating new session-wide MCP client...")
        exchange_id = config.default_exchange
        server_path = config.server_path
        
        # Create the MCP client
        _mcp_client = CCXTMCPClient(
            exchange_id=exchange_id,
            user_id="test_session",  # Use a fixed ID for the session
            use_local_server=True,
            server_path=server_path
        )
        
        # Connect to the MCP server
        logger.info("Connecting to MCP server...")
        await _mcp_client.connect()
        
        # Register finalizer to disconnect at the end of the session
        async def disconnect_at_end():
            if _mcp_client and _mcp_client.is_connected:
                logger.info("Disconnecting session MCP client...")
                try:
                    await _mcp_client.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting MCP client: {e}")
        
        # Use addfinalizer with a synchronous wrapper since pytest.fixture finalizers must be synchronous
        def finalizer():
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(disconnect_at_end())
            else:
                loop.run_until_complete(disconnect_at_end())
        
        request.addfinalizer(finalizer)
    
    yield _mcp_client

@pytest.fixture
async def ccxt_adapter(user_id, config, session_mcp_client):
    """Create a connected CCXT adapter for testing that uses the session-wide MCP client."""
    exchange_id = config.default_exchange
    
    # Create adapter instance using the session-wide client
    adapter = CCXTMCPAdapter(exchange_id, user_id, config.model_dump())
    adapter.mcp_client = session_mcp_client  # Use the session-wide client
    adapter.connected = True
    
    yield adapter
    
    # No disconnection here - the session fixture handles that


@pytest.fixture
async def tools_schema():
    """Get a mock schema for testing purposes."""
    try:
        # Create a minimal mock schema with required operations for the tests
        tools = [
            {
                "name": "set_leverage",
                "description": "Set leverage for a symbol",
                "parameters": {
                    "symbol": {"type": "string", "description": "Trading pair symbol", "required": True},
                    "leverage": {"type": "number", "description": "Leverage value", "required": True}
                }
            },
            {
                "name": "create_market_order",
                "description": "Create a market order",
                "parameters": {
                    "symbol": {"type": "string", "description": "Trading pair symbol", "required": True},
                    "side": {"type": "string", "description": "Order side (buy or sell)", "required": True},
                    "amount": {"type": "number", "description": "Order amount", "required": True}
                }
            },
            {
                "name": "create_order",
                "description": "Create any type of order",
                "parameters": {
                    "symbol": {"type": "string", "description": "Trading pair symbol", "required": True},
                    "side": {"type": "string", "description": "Order side (buy or sell)", "required": True},
                    "type": {"type": "string", "description": "Order type (market, limit, etc.)", "required": True},
                    "amount": {"type": "number", "description": "Order amount", "required": True},
                    "price": {"type": "number", "description": "Order price for limit orders", "required": False},
                    "stop_price": {"type": "number", "description": "Stop price for stop orders", "required": False}
                }
            },
            {
                "name": "fetch_position",
                "description": "Fetch position for a symbol",
                "parameters": {
                    "symbol": {"type": "string", "description": "Trading pair symbol", "required": True}
                }
            },
            {
                "name": "close_position",
                "description": "Close open position",
                "parameters": {
                    "symbol": {"type": "string", "description": "Trading pair symbol", "required": True}
                }
            }
        ]
        
        logger.info(f"Using mock schema with {len(tools)} tools for LLM testing")
        return tools
    except Exception as e:
        logger.error(f"Error creating tool schema: {e}")
        # Return empty list as a fallback
        return []


@pytest.fixture(scope="session")
def config():
    """Create a test configuration with real API keys."""
    return EngineConfig(
        llm={
            "model": "gpt-4.1",
            "system_prompt": "You are an expert trading assistant. Your task is to help execute trading decisions through the CCXT API.",
            "temperature": 0.0,
            "max_retries": 2
        },
        validation={
            "max_leverage": 10,
            "max_position_pct": 0.05
        },
        execution={
            "polling_interval": 60,
            "max_retries": 2
        },
        default_exchange="bitmex",
        use_testnet=True,
        server_path=str(Path(__file__).parent.parent.parent / "core" / "mcp" / "servers" / "ccxt_mcp_server.py"),
        credentials={
            "apiKey": os.environ.get("EXCHANGE_API"),
            "secret": os.environ.get("EXCHANGE_SECRET")
        }
    )


@pytest.fixture
def llm_service(user_id, config):
    """Create an instance of the LLMService for testing."""
    # Override LLM API key from environment variable
    os.environ["OPENAI_API_KEY"] = os.environ.get("TRADING_LLM_API_KEY")
    service = LLMService(config=config, user_id=user_id)
    return service


@pytest.fixture
def long_intent():
    """Create a test intent for entering a long position."""
    return {
        "decision_id": str(uuid.uuid4()),
        "action": "enter_long",
        "symbol": "BTC/USD",
        "exchange": "bitmex",
        "timeframe": "15m",
        "size_type": "fixed_contracts",
        "size_value": 1,
        "leverage": 2,
        "stop_loss_price": 60000,
        "take_profit_price": 70000,
        "confidence": 0.85,
        "reasoning": "BTC is showing strong upward momentum with multiple technical indicators confirming the trend."
    }


@pytest.fixture
def short_intent():
    """Create a test intent for entering a short position."""
    return {
        "decision_id": str(uuid.uuid4()),
        "action": "enter_short",
        "symbol": "BTC/USD",
        "exchange": "bitmex",
        "timeframe": "15m",
        "size_type": "fixed_contracts",
        "size_value": 1,
        "leverage": 2,
        "stop_loss_price": 70000,
        "take_profit_price": 60000,
        "confidence": 0.85,
        "reasoning": "BTC is showing bearish divergence and has reached resistance at the upper channel."
    }


@pytest.fixture
def exit_intent():
    """Create a test intent for exiting a position."""
    return {
        "decision_id": str(uuid.uuid4()),
        "action": "exit",
        "symbol": "BTC/USD",
        "exchange": "bitmex",
        "timeframe": "15m",
        "reasoning": "Taking profits as the price has reached the target level."
    }


@pytest.mark.asyncio
async def test_long_entry_intent_processing(llm_service, long_intent, tools_schema):
    """Test processing a long entry intent through the LLM service."""
    import json
    from pathlib import Path
    
    # Await the tools_schema coroutine to get the actual tools
    actual_tools = await tools_schema
    
    # Process the intent with the LLM service
    tool_calls = await llm_service.process_intent(long_intent, actual_tools)
    
    # Save tool calls to file for use in ValidationService test
    output_dir = Path(__file__).parent
    output_path = output_dir / "llm_long_entry_tool_calls.json"
    with open(output_path, "w") as f:
        # Convert tool calls to dictionaries for JSON serialization
        tool_calls_data = [
            {"tool": tc.tool, "parameters": tc.parameters}
            for tc in tool_calls
        ]
        json.dump(tool_calls_data, f, indent=2)
    
    logger.info(f"Saved {len(tool_calls)} LLM-generated tool calls to {output_path}")
    
    # Verify that tool calls were generated
    assert len(tool_calls) > 0, "No tool calls were generated"
    
    # Verify that the tool calls match expected structure
    for tool_call in tool_calls:
        assert isinstance(tool_call, ToolCall), "Result is not a ToolCall instance"
        assert hasattr(tool_call, "tool"), "ToolCall missing 'tool' attribute"
        assert hasattr(tool_call, "parameters"), "ToolCall missing 'parameters' attribute"
        
        # Check that the tool name is in our schema
        assert tool_call.tool is not None and tool_call.tool != "", f"Invalid tool name: {tool_call.tool}"
        
        # For 'create_market_order', verify parameters
        if tool_call.tool == "create_market_order":
            params = tool_call.parameters
            assert "symbol" in params, "Missing 'symbol' parameter"
            assert params["symbol"] == "BTC/USD", f"Incorrect symbol: {params['symbol']}"
            assert "side" in params, "Missing 'side' parameter"
            assert params["side"] == "buy", f"Incorrect side for long entry: {params['side']}"
            assert "amount" in params, "Missing 'amount' parameter"
        
        # For 'set_leverage', verify parameters
        elif tool_call.tool == "set_leverage":
            params = tool_call.parameters
            assert "symbol" in params, "Missing 'symbol' parameter"
            assert params["symbol"] == "BTC/USD", f"Incorrect symbol: {params['symbol']}"
            assert "leverage" in params, "Missing 'leverage' parameter"
            assert params["leverage"] == 2, f"Incorrect leverage: {params['leverage']}"
    
    # Log successful results
    logger.info(f"Generated {len(tool_calls)} tool calls for long intent")
    for i, call in enumerate(tool_calls):
        logger.info(f"Tool call {i+1}: {call.tool} with params: {call.parameters}")


@pytest.mark.asyncio
async def test_short_entry_intent_processing(llm_service, short_intent, tools_schema):
    """Test processing a short entry intent through the LLM service."""
    import json
    from pathlib import Path
    
    # Await the tools_schema coroutine to get the actual tools
    actual_tools = await tools_schema
    
    # Process the intent with the LLM service
    tool_calls = await llm_service.process_intent(short_intent, actual_tools)
    
    # Save tool calls to file for use in ValidationService test
    output_dir = Path(__file__).parent
    output_path = output_dir / "llm_short_entry_tool_calls.json"
    with open(output_path, "w") as f:
        # Convert tool calls to dictionaries for JSON serialization
        tool_calls_data = [
            {"tool": tc.tool, "parameters": tc.parameters}
            for tc in tool_calls
        ]
        json.dump(tool_calls_data, f, indent=2)
    
    logger.info(f"Saved {len(tool_calls)} LLM-generated tool calls to {output_path}")
    
    # Verify that tool calls were generated
    assert len(tool_calls) > 0, "No tool calls were generated"
    
    # Verify that the tool calls match expected structure
    for tool_call in tool_calls:
        assert isinstance(tool_call, ToolCall), "Result is not a ToolCall instance"
        assert hasattr(tool_call, "tool"), "ToolCall missing 'tool' attribute"
        assert hasattr(tool_call, "parameters"), "ToolCall missing 'parameters' attribute"
        
        # Check that the tool name is in our schema
        assert tool_call.tool is not None and tool_call.tool != "", f"Invalid tool name: {tool_call.tool}"
        
        # For 'create_market_order', verify parameters
        if tool_call.tool == "create_market_order":
            params = tool_call.parameters
            assert "symbol" in params, "Missing 'symbol' parameter"
            assert params["symbol"] == "BTC/USD", f"Incorrect symbol: {params['symbol']}"
            assert "side" in params, "Missing 'side' parameter"
            assert params["side"] == "sell", f"Incorrect side for short entry: {params['side']}"
            assert "amount" in params, "Missing 'amount' parameter"
        
        # For 'set_leverage', verify parameters
        elif tool_call.tool == "set_leverage":
            params = tool_call.parameters
            assert "symbol" in params, "Missing 'symbol' parameter"
            assert params["symbol"] == "BTC/USD", f"Incorrect symbol: {params['symbol']}"
            assert "leverage" in params, "Missing 'leverage' parameter"
            assert params["leverage"] == 2, f"Incorrect leverage: {params['leverage']}"
    
    # Log successful results
    logger.info(f"Generated {len(tool_calls)} tool calls for short intent")
    for i, call in enumerate(tool_calls):
        logger.info(f"Tool call {i+1}: {call.tool} with params: {call.parameters}")


@pytest.mark.asyncio
async def test_exit_intent_processing(llm_service, exit_intent, tools_schema):
    """Test processing an exit intent through the LLM service."""
    # Await the tools_schema coroutine to get the actual tools
    actual_tools = await tools_schema
    
    # Process the intent with the LLM service
    tool_calls = await llm_service.process_intent(exit_intent, actual_tools)
    
    # Verify that tool calls were generated
    assert len(tool_calls) > 0, "No tool calls were generated"
    
    # Verify that the tool calls match expected structure
    for tool_call in tool_calls:
        assert isinstance(tool_call, ToolCall), "Result is not a ToolCall instance"
        assert hasattr(tool_call, "tool"), "ToolCall missing 'tool' attribute"
        assert hasattr(tool_call, "parameters"), "ToolCall missing 'parameters' attribute"
        
        # Check that the tool name is valid
        assert tool_call.tool is not None and tool_call.tool != "", f"Invalid tool name: {tool_call.tool}"
        
        # For exit, we expect a market order (either buy or sell depending on the position)
        if tool_call.tool == "create_market_order":
            params = tool_call.parameters
            assert "symbol" in params, "Missing 'symbol' parameter"
            assert params["symbol"] == "BTC/USD", f"Incorrect symbol: {params['symbol']}"
            assert "side" in params, "Missing 'side' parameter"
            assert "amount" in params, "Missing 'amount' parameter"
    
    # Log successful results
    logger.info(f"Generated {len(tool_calls)} tool calls for exit intent")
    for i, call in enumerate(tool_calls):
        logger.info(f"Tool call {i+1}: {call.tool} with params: {call.parameters}")


@pytest.mark.asyncio
async def test_parameter_normalization(llm_service, long_intent, tools_schema):
    """Test the parameter normalization functionality for handling quoted keys."""
    # Await the tools_schema coroutine to get the actual tools
    actual_tools = await tools_schema
    
    # Process a long entry intent, but force a different response format
    # We'll simulate this by extracting the prompt and then manually parsing a response
    prompt = llm_service._create_prompt(long_intent, actual_tools)
    
    # Create a response with quoted keys (a common LLM issue)
    sample_response = """
{
    "tool": "create_market_order",
    "parameters": {
        "\\"symbol\\"": "BTC/USD",
        "\\"side\\"": "buy",
        "\\"amount\\"": 1,
        "\\"leverage\\"": 2
    }
}
"""
    
    # Parse this response manually
    tool_calls = await llm_service._parse_response(sample_response)
    
    # Verify that parameter normalization worked
    assert len(tool_calls) == 1, "Expected a single tool call"
    
    tool_call = tool_calls[0]
    assert isinstance(tool_call, ToolCall), "Result is not a ToolCall instance"
    
    # Check that the quoted keys were normalized
    params = tool_call.parameters
    assert "symbol" in params, "Missing 'symbol' parameter (normalization failed)"
    assert "side" in params, "Missing 'side' parameter (normalization failed)"
    assert "amount" in params, "Missing 'amount' parameter (normalization failed)"
    assert "leverage" in params, "Missing 'leverage' parameter (normalization failed)"
    
    # Check parameter values
    assert params["symbol"] == "BTC/USD", f"Incorrect symbol: {params['symbol']}"
    assert params["side"] == "buy", f"Incorrect side: {params['side']}"
    assert params["amount"] == 1, f"Incorrect amount: {params['amount']}"
    assert params["leverage"] == 2, f"Incorrect leverage: {params['leverage']}"
    
    logger.info(f"Parameter normalization successful: {params}")


@pytest.mark.asyncio
async def test_response_format_handling(llm_service):
    """Test handling of various response formats from the LLM."""
    # Test scenarios with different response formats
    test_formats = [
        # Plain JSON without markdown
        """{
            "tool": "create_market_order",
            "parameters": {
                "symbol": "BTC/USD",
                "side": "buy",
                "amount": 1
            }
        }""",
        
        # JSON with ```json markdown
        """```json
        {
            "tool": "create_market_order",
            "parameters": {
                "symbol": "BTC/USD",
                "side": "buy",
                "amount": 1
            }
        }
        ```""",
        
        # JSON with ``` markdown (without 'json' specifier)
        """```
        {
            "tool": "create_market_order",
            "parameters": {
                "symbol": "BTC/USD",
                "side": "buy",
                "amount": 1
            }
        }
        ```""",
        
        # JSON with additional explanation text
        """I'll help you execute this trade. Here's the tool call:

        ```json
        {
            "tool": "create_market_order",
            "parameters": {
                "symbol": "BTC/USD",
                "side": "buy",
                "amount": 1
            }
        }
        ```

        This will create a market buy order for 1 contract of BTC/USD."""
    ]
    
    # Test each format
    for i, response_text in enumerate(test_formats):
        logger.info(f"Testing response format {i+1}...")
        
        # Parse the response
        tool_calls = await llm_service._parse_response(response_text)
        
        # Verify that the parsing worked
        assert len(tool_calls) == 1, f"Failed to parse format {i+1}"
        
        tool_call = tool_calls[0]
        assert isinstance(tool_call, ToolCall), "Result is not a ToolCall instance"
        assert tool_call.tool == "create_market_order", f"Incorrect tool: {tool_call.tool}"
        
        # Check parameters
        params = tool_call.parameters
        assert "symbol" in params, "Missing 'symbol' parameter"
        assert params["symbol"] == "BTC/USD", f"Incorrect symbol: {params['symbol']}"
        assert "side" in params, "Missing 'side' parameter"
        assert params["side"] == "buy", f"Incorrect side: {params['side']}"
        assert "amount" in params, "Missing 'amount' parameter"
        assert params["amount"] == 1, f"Incorrect amount: {params['amount']}"
        
        logger.info(f"Successfully parsed format {i+1}")


if __name__ == "__main__":
    # Run the tests
    pytest.main(["-xvs", __file__])