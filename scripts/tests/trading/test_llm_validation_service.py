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
from trading.engine.model.tool_call import ToolCall, ValidatedToolCall
from trading.engine.service.llm_service import LLMService
from trading.engine.service.validation_service import ValidationService, ValidationError
from trading.compiler import TradeCompiler
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
async def real_tools_schema(session_mcp_client):
    """Get the actual tools schema from the MCP server."""
    try:
        # Get tools directly from MCP session
        tools = await session_mcp_client.session.get_tools()
        
        # Format tools for the LLM
        formatted_tools = []
        for tool in tools:
            tool_info = {
                "name": tool.name,
                "description": tool.description,
                "parameters": {}
            }
            
            # Parse parameters from schema
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                schema = tool.inputSchema
                if 'properties' in schema:
                    params = {}
                    required = schema.get('required', [])
                    
                    for param_name, param_info in schema['properties'].items():
                        params[param_name] = {
                            "type": param_info.get('type', 'string'),
                            "description": param_info.get('description', ''),
                            "required": param_name in required
                        }
                    
                    tool_info['parameters'] = params
            
            formatted_tools.append(tool_info)
            
        logger.info(f"Retrieved {len(formatted_tools)} real tools from MCP server")
        
        # Log tool names for debugging
        tool_names = [t['name'] for t in formatted_tools]
        logger.info(f"Available tools: {tool_names}")
        
        return formatted_tools
    except Exception as e:
        logger.error(f"Error getting real tools schema: {e}")
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
async def trade_compiler(config, ccxt_adapter):
    """Create a TradeCompiler instance for testing."""
    # Need to await the ccxt_adapter since it's an async generator
    adapter = await ccxt_adapter
    
    # Now use the resolved adapter
    compiler = TradeCompiler(config.model_dump(), adapter)
    return compiler

@pytest.fixture
async def validation_service(config, trade_compiler):
    """Create a ValidationService instance for testing."""
    # Need to await the trade_compiler since it's an async fixture
    compiler = await trade_compiler
    
    # ValidationService expects a ValidationConfig, but we have an EngineConfig
    # Extract the validation config from the engine config
    validation_config = config.validation
    
    service = ValidationService(
        config=validation_config,
        trade_compiler=compiler
    )
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
async def test_long_entry_intent_processing(llm_service, long_intent, real_tools_schema):
    """Test processing a long entry intent through the LLM service."""
    import json
    from pathlib import Path
    
    # Await the tools_schema coroutine to get the actual tools
    actual_tools = await real_tools_schema
    
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
async def test_short_entry_intent_processing(llm_service, short_intent, real_tools_schema):
    """Test processing a short entry intent through the LLM service."""
    import json
    from pathlib import Path
    
    # Await the tools_schema coroutine to get the actual tools
    actual_tools = await real_tools_schema
    
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
async def test_exit_intent_processing(llm_service, exit_intent, real_tools_schema):
    """Test processing an exit intent through the LLM service."""
    # Await the tools_schema coroutine to get the actual tools
    actual_tools = await real_tools_schema
    
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
async def test_parameter_normalization(llm_service, long_intent, real_tools_schema):
    """Test the parameter normalization functionality for handling quoted keys."""
    # Await the tools_schema coroutine to get the actual tools
    actual_tools = await real_tools_schema
    
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


@pytest.mark.asyncio
async def test_llm_to_validation_flow(llm_service, config, session_mcp_client, long_intent):
    """
    Test the complete flow from LLM generating tool calls to validation service validating them.
    This test uses real tools from the MCP server to ensure compatibility.
    """
    # 0. Ensure we have a connected MCP client
    logger.info("Getting MCP client for test...")
    mcp_client = await anext(session_mcp_client)
    
    # 1. Get real tools from MCP server
    logger.info("Getting real tools schema from MCP server...")
    try:
        # Get tools directly from MCP session
        tools = await mcp_client.session.get_tools()
        
        # Format tools for the LLM
        real_tools = []
        for tool in tools:
            tool_info = {
                "name": tool.name,
                "description": tool.description,
                "parameters": {}
            }
            
            # Parse parameters from schema
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                schema = tool.inputSchema
                if 'properties' in schema:
                    params = {}
                    required = schema.get('required', [])
                    
                    for param_name, param_info in schema['properties'].items():
                        params[param_name] = {
                            "type": param_info.get('type', 'string'),
                            "description": param_info.get('description', ''),
                            "required": param_name in required
                        }
                    
                    tool_info['parameters'] = params
            
            real_tools.append(tool_info)
            
        logger.info(f"Retrieved {len(real_tools)} real tools from MCP server")
        
        # Log tool names for debugging
        tool_names = [t['name'] for t in real_tools]
        logger.info(f"Available tools: {tool_names}")
        
    except Exception as e:
        logger.error(f"Error getting real tools schema: {e}")
        # Return empty list as a fallback
        real_tools = []
    
    # 2. Pass real tools to LLM and generate tool calls
    logger.info("Generating tool calls with LLM using real MCP tools...")
    tool_calls = await llm_service.process_intent(long_intent, real_tools)
    
    # Verify that tool calls were generated
    assert len(tool_calls) > 0, "No tool calls were generated by LLM"
    
    # Log the generated tool calls
    logger.info(f"LLM generated {len(tool_calls)} tool calls using real MCP tools:")
    for i, call in enumerate(tool_calls):
        logger.info(f"Tool call {i+1}: {call.tool} with params: {call.parameters}")
    
    # 3. Manually create the validation service with properly resolved adapter
    logger.info("Creating adapter and validation service directly...")
    
    # Create the adapter (not using the fixture)
    exchange_id = config.default_exchange
    user_id = "test_direct"
    
    # Create adapter instance using the session-wide client
    adapter = CCXTMCPAdapter(exchange_id, user_id, config.model_dump())
    adapter.mcp_client = mcp_client  # Use the session-wide client
    adapter.connected = True
    
    # Create the trade compiler
    trade_compiler = TradeCompiler(config.model_dump(), adapter)
    
    # Extract validation config
    validation_config = config.validation
    
    # Create validation service
    validation_service = ValidationService(
        config=validation_config,
        trade_compiler=trade_compiler
    )
    
    # 4. Prepare validation context
    context = {
        "user_id": "test_user",
        "timestamp": asyncio.get_event_loop().time(),
        "equity": 10000,  # Mock equity for risk checks
    }
    
    # 5. Pass tool calls to validation service
    try:
        logger.info("Validating LLM-generated tool calls...")
        validated_calls = await validation_service.validate_tool_calls(tool_calls, long_intent, context)
        
        # 6. Verify validation was successful
        assert len(validated_calls) == len(tool_calls), "Not all tool calls were validated"
        
        # Check that each call was properly validated
        for i, call in enumerate(validated_calls):
            assert isinstance(call, ValidatedToolCall), f"Call {i} is not a ValidatedToolCall instance"
            assert hasattr(call, "original_call"), f"Call {i} missing reference to original"
            
            # Log the validated calls
            logger.info(f"Validated call {i+1}: {call.tool} with params: {call.parameters}")
            
            # Print with super high visibility for capture
            print("\n\n====== VALIDATED TOOL CALL ======")
            print(f"TOOL: {call.tool}")
            print(f"PARAMS: {call.parameters}")
            print("==================================\n\n")
            
            # Check if symbol was mapped correctly for this exchange
            if "symbol" in call.parameters:
                original_symbol = tool_calls[i].parameters.get("symbol")
                mapped_symbol = call.parameters.get("symbol")
                if original_symbol and mapped_symbol and original_symbol != mapped_symbol:
                    logger.info(f"Symbol mapping: {original_symbol} → {mapped_symbol}")
                    
        logger.info("LLM-to-Validation flow completed successfully!")
        
    except ValidationError as e:
        # If validation fails, it might be because the LLM generated invalid tool calls
        # Log the error and print suggestions for fixing the test
        logger.error(f"Validation failed with error: {e}")
        logger.info("Suggestions to fix this test:")
        logger.info("1. Check if the LLM is generating tool calls that match the actual MCP tools")
        logger.info("2. If needed, provide better prompt guidance to the LLM")
        logger.info("3. You may need to check what tools are actually available in the MCP server")
        
        # Re-raise to fail the test
        raise


if __name__ == "__main__":
    # Run the tests
    pytest.main(["-xvs", __file__])