#!/usr/bin/env python
"""
Simple End-to-End Trading Flow Test

This test combines the successful patterns from test_llm_validation_service.py 
and test_execution_service_simple.py in the simplest possible way:

1. LLM generates tool calls from intent (like test_llm_validation_service.py)
2. Validate tool calls (like test_llm_validation_service.py)  
3. Execute validated tool calls directly (like test_execution_service_simple.py)
4. Verify position creation
"""

import os
import sys
import asyncio
import uuid
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set environment variables
os.environ["TESTNET"] = "1"
os.environ["EXCHANGE_NAME"] = "bitmex"

# Load environment variables for API keys
load_dotenv()

from core.common.logger import logger
from trading.engine_services.model.config import EngineConfig
from trading.engine_services.service.llm_service import LLMService
from trading.engine_services.service.validation_service import ValidationService
from trading.compiler import TradeCompiler
from trading.exchanges.ccxt_mcp import CCXTMCPAdapter
from core.mcp.ccxt import CCXTMCPClient
from trading.exchanges.bitmex.exchange_guide_testnet import get_exchange_guide_text
from core.monitoring.service import AccountMonitoringService
from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure minimal logging
import logging
logger.configure(handlers=[{"sink": sys.stdout, "level": logging.INFO}])


async def get_real_tools_from_mcp(mcp_client):
    """Get real tools from MCP server (copied from working test)."""
    try:
        # Get tools directly from MCP session
        tools = await mcp_client.session.get_tools()
        
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
        tool_names = [t['name'] for t in formatted_tools]
        logger.info(f"Available tools: {tool_names}")
        
        return formatted_tools
    except Exception as e:
        logger.error(f"Error getting real tools schema: {e}")
        raise


async def close_all_positions(ccxt_adapter):
    """Close all open positions (copied from working test)."""
    try:
        logger.info("Checking for existing positions...")
        positions = await ccxt_adapter.fetch_positions()
        
        if positions:
            logger.info(f"Found {len(positions)} positions, closing them...")
            for position in positions:
                if not isinstance(position, dict):
                    continue
                    
                symbol = position.get("symbol")
                contracts = float(position.get("contracts", 0) or 0)
                
                if abs(contracts) > 0:
                    side = "sell" if contracts > 0 else "buy"
                    logger.info(f"Closing position for {symbol} with {contracts} contracts (side: {side})")
                    
                    try:
                        close_result = await ccxt_adapter.create_order(
                            symbol=symbol,
                            order_type="market",
                            side=side,
                            amount=abs(contracts),
                            params={"reduceOnly": True}
                        )
                        logger.info(f"Position closed: {json.dumps(close_result)}")
                    except Exception as e:
                        logger.error(f"Error closing position: {e}")
        else:
            logger.info("No existing positions found")
    except Exception as e:
        logger.error(f"Error checking positions: {e}")


async def check_position_exists(ccxt_adapter, symbol="BTC/USD:BTC"):
    """Check if a position exists (copied from working test)."""
    try:
        positions = await ccxt_adapter.fetch_positions()
        
        for position in positions:
            if position.get("symbol") == symbol:
                contracts = float(position.get("contracts", 0))
                if abs(contracts) > 0:
                    return position
        
        return None
    except Exception as e:
        logger.error(f"Error checking position: {e}")
        return None


async def create_test_user_and_config(user_id, config_id):
    """Create test user and config for monitoring service."""
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS)
    
    try:
        with conn.cursor() as cursor:
            # Create test user
            cursor.execute(
                "INSERT INTO users (user_id, username, email) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                (user_id, 'test_trader', 'test@trader.com')
            )
            
            # Create test configuration
            cursor.execute("""
                INSERT INTO configurations (config_id, user_id, config_type, config_name, config_data)
                VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
            """, (config_id, user_id, 'trading', 'test_trading_config', '{}'))
            
            conn.commit()
            logger.info("✓ Test user and config created")
    
    except Exception as e:
        logger.error(f"Error creating test data: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()


async def get_account_state(user_id, config_id):
    """Get latest account state from monitoring data."""
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS)
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT balance_data, position_data, equity,
                       available_margin, used_margin, updated_at
                FROM account_states
                WHERE user_id = %s AND config_id = %s AND exchange = 'bitmex'
                ORDER BY updated_at DESC
                LIMIT 1
            """
            
            cursor.execute(query, (user_id, config_id))
            row = cursor.fetchone()
            
            if row:
                # psycopg2 automatically converts JSONB to dict
                balance_data = row['balance_data']
                position_data = row['position_data']
                
                # If they're strings, parse them
                if isinstance(balance_data, str):
                    balance_data = json.loads(balance_data)
                if isinstance(position_data, str):
                    position_data = json.loads(position_data)
                
                return {
                    'balance_data': balance_data,
                    'position_data': position_data,
                    'equity': float(row['equity']),
                    'available_margin': float(row['available_margin']),
                    'used_margin': float(row['used_margin']),
                    'updated_at': row['updated_at']
                }
            
            return None
    
    finally:
        conn.close()


async def cleanup_test_data(user_id, config_id):
    """Clean up test data."""
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS)
    
    try:
        with conn.cursor() as cursor:
            # Delete in reverse order
            cursor.execute("DELETE FROM account_states WHERE user_id = %s AND config_id = %s", (user_id, config_id))
            cursor.execute("DELETE FROM configurations WHERE config_id = %s", (config_id,))
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            conn.commit()
            logger.info("✓ Test data cleaned up")
    
    except Exception as e:
        logger.error(f"Error cleaning up: {e}")
        conn.rollback()
    
    finally:
        conn.close()


async def main():
    """Simple end-to-end test with real account monitoring data."""
    logger.info("🚀 Starting Enhanced Trading Flow Test with Account Monitoring")
    
    # Generate test IDs
    user_id = str(uuid.uuid4())
    config_id = str(uuid.uuid4())
    
    # Step 0: Setup test data and start account monitoring
    logger.info("🔧 Step 0: Setting up test environment and account monitoring...")
    await create_test_user_and_config(user_id, config_id)
    
    # Create and start monitoring service
    monitoring_service = AccountMonitoringService(
        user_id=user_id,
        config_id=config_id,
        exchange_name="bitmex",
        credentials={
            'apiKey': os.environ.get('EXCHANGE_API'),
            'secret': os.environ.get('EXCHANGE_SECRET')
        },
        monitoring_interval=10,  # 10 seconds for testing
        testnet=True
    )
    
    try:
        # Start monitoring
        await monitoring_service.start_monitoring()
        logger.info("✓ Account monitoring started")
        
        # Wait for first update
        await asyncio.sleep(12)
        
        # Get real account state
        account_state = await get_account_state(user_id, config_id)
        
        if not account_state:
            logger.error("❌ No account state available - monitoring may have failed")
            return
        
        logger.info(f"💰 Current Account State:")
        logger.info(f"  Available Margin: {account_state['available_margin']:.8f} BTC")
        logger.info(f"  Equity: {account_state['equity']:.8f} BTC")
        logger.info(f"  Used Margin: {account_state['used_margin']:.8f} BTC")
        logger.info(f"  Open Positions: {len(account_state['position_data'])}")
        logger.info(f"  Last Updated: {account_state['updated_at']}")
        
        # Calculate realistic position size based on available margin
        available_margin_btc = account_state['available_margin']
        available_margin_usd = available_margin_btc * 110000  # Approximate BTC price
        
        # Use 1% of available margin for this test (conservative)
        collateral_amount = min(1000, available_margin_usd * 0.01)
        
        logger.info(f"📊 Risk Calculation:")
        logger.info(f"  Available Margin: ${available_margin_usd:.2f} USD")
        logger.info(f"  Using: ${collateral_amount:.2f} USD (1% of available)")
        
        # Test data - realistic intent using real account data
        long_intent = {
            "decision_id": str(uuid.uuid4()),
            "action": "enter_long",
            "symbol": "BTC/USD",
            "exchange": "bitmex",
            "timeframe": "15m",
            "collateral_amount": collateral_amount,  # Based on real account state
            "leverage": 10,
            "stop_loss_price": 100000,
            "take_profit_price": 120000,
            "confidence": 0.85,
            "reasoning": f"BTC trade using {collateral_amount:.2f} USD from available margin of {available_margin_usd:.2f} USD"
        }
        
        # Get exchange guide for the intent's symbol
        exchange_guide = get_exchange_guide_text(long_intent["symbol"])
        
        # Configuration
        config = EngineConfig(
            llm={
                "model": "gpt-4.1", 
                "system_prompt": f"You are an expert trading assistant. Your task is to help execute trading decisions through the CCXT API.\n\n{exchange_guide}",
                "temperature": 0.0,
                "max_retries": 2
            },
            validation={
                "max_leverage": 10,
                "max_position_pct": 0.05
            },
            execution={
                "polling_interval": 5,
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
        
        # Step 1: Connect to MCP server
        logger.info("📋 Step 1: Connecting to MCP server...")
        mcp_client = CCXTMCPClient(
            exchange_id="bitmex",
            user_id=user_id,
            use_local_server=True,
            server_path=config.server_path
        )
        await mcp_client.connect()
        
        # Step 2: Get real tools and filter to only trading-relevant ones
        logger.info("🔧 Step 2: Getting real tools from MCP server...")
        all_tools = await get_real_tools_from_mcp(mcp_client)
    
        # Filter to only the trading-relevant tools
        trading_tool_names = [
            "set_leverage",
            "create_market_buy_order",
            "create_market_sell_order", 
            "create_limit_order",
            "create_stop_order",
            "fetch_positions",
            "fetch_balance",
            "cancel_order"
        ]
        
        tools = [tool for tool in all_tools if tool['name'] in trading_tool_names]
        logger.info(f"Filtered to {len(tools)} trading-relevant tools: {[t['name'] for t in tools]}")
        
        # Step 3: Create CCXT adapter and clean positions
        logger.info("🧹 Step 3: Setting up exchange adapter and cleaning positions...")
        ccxt_adapter = CCXTMCPAdapter("bitmex", user_id, config.model_dump())
        ccxt_adapter.mcp_client = mcp_client
        ccxt_adapter.connected = True
        
        await close_all_positions(ccxt_adapter)
        await asyncio.sleep(2)
    
        # Step 4: LLM generates tool calls (from test_llm_validation_service.py)
        logger.info("🧠 Step 4: Processing intent through LLM...")
        os.environ["OPENAI_API_KEY"] = os.environ.get("TRADING_LLM_API_KEY")
        llm_service = LLMService(config=config, user_id=user_id)
        tool_calls = await llm_service.process_intent(long_intent, tools)
        
        assert len(tool_calls) > 0, "No tool calls generated by LLM"
        logger.info(f"LLM generated {len(tool_calls)} tool calls")
        
        for i, call in enumerate(tool_calls):
            logger.info(f"  Tool call {i+1}: {call.tool} with params: {call.parameters}")
        
        # Step 5: Validate tool calls (from test_llm_validation_service.py)
        logger.info("✅ Step 5: Validating tool calls...")
        trade_compiler = TradeCompiler(config.model_dump(), ccxt_adapter)
        validation_service = ValidationService(config=config.validation, trade_compiler=trade_compiler)
    
        # Use real account data for validation
        validation_context = {
            "user_id": user_id,
            "timestamp": asyncio.get_event_loop().time(),
            "equity": account_state['equity'] or account_state['available_margin'],  # Use available margin if equity is 0
            "available_margin": account_state['available_margin'],
            "existing_positions": len(account_state['position_data']),
        }
        
        validated_calls = await validation_service.validate_tool_calls(tool_calls, long_intent, validation_context)
        assert len(validated_calls) == len(tool_calls), "Not all tool calls were validated"
        logger.info(f"Validated {len(validated_calls)} tool calls")
        
        for i, call in enumerate(validated_calls):
            logger.info(f"  Validated call {i+1}: {call.tool} with params: {call.parameters}")
    
        # Step 6: Execute tool calls directly (from test_execution_service_simple.py)
        logger.info("⚡ Step 6: Executing validated tool calls...")
        execution_results = []
        
        for call in validated_calls:
            logger.info(f"Executing: {call.tool} with {call.parameters}")
            try:
                result = await ccxt_adapter.call_tool(call.tool, call.parameters)
                execution_results.append(result)
                logger.info(f"Result: {json.dumps(result, indent=2)}")
            except Exception as e:
                logger.error(f"Error executing {call.tool}: {e}")
                execution_results.append({"error": str(e)})
        
        # Step 7: Wait and verify position
        logger.info("📊 Step 7: Waiting for exchange processing...")
        await asyncio.sleep(3)
        
        logger.info("🔍 Step 8: Verifying position creation...")
        position = await check_position_exists(ccxt_adapter, "BTC/USD:BTC")
        
        if position:
            contracts = float(position.get("contracts", 0))
            logger.info(f"✅ Position found: {json.dumps(position, indent=2)}")
            assert contracts > 0, f"Expected positive contracts for long position, got {contracts}"
            logger.info(f"✅ Long position verified with {contracts} contracts")
        else:
            logger.warning("⚠️ No position found - checking execution results...")
            for i, result in enumerate(execution_results):
                logger.info(f"Execution result {i+1}: {json.dumps(result, indent=2)}")
        
        # Step 8: Clean up
        logger.info("🧹 Step 8: Cleaning up...")
        if position:
            await close_all_positions(ccxt_adapter)
            await asyncio.sleep(2)
            
            final_position = await check_position_exists(ccxt_adapter, "BTC/USD:BTC")
            if final_position is None:
                logger.info("✅ Position successfully closed")
            else:
                logger.info(f"⚠️ Position still exists: {final_position}")
        
        # Disconnect MCP
        await mcp_client.disconnect()
        
        logger.info("🎉 Enhanced Trading Flow Test with Account Monitoring Completed!")
        
        # Show final account state
        final_account_state = await get_account_state(user_id, config_id)
        if final_account_state:
            logger.info(f"📊 Final Account State:")
            logger.info(f"  Available Margin: {final_account_state['available_margin']:.8f} BTC")
            logger.info(f"  Equity: {final_account_state['equity']:.8f} BTC")
            logger.info(f"  Open Positions: {len(final_account_state['position_data'])}")
    
    finally:
        # Always stop monitoring and cleanup
        logger.info("🧹 Cleaning up monitoring service and test data...")
        await monitoring_service.stop_monitoring()
        await cleanup_test_data(user_id, config_id)


if __name__ == "__main__":
    asyncio.run(main())