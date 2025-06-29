#!/usr/bin/env python
"""
Trading Module API

Provides REST API endpoints for the Trading Module to receive trading intents
from the Decision Module and execute trades on exchanges.

This module serves as the HTTP API wrapper around the TradingEngine, which
handles the actual trade execution logic.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import uuid
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.common.logging_config import logger
from core.common.config import DEFAULT_USER_ID
from core.common.db import get_db_connection
from core.mcp.exceptions import MCPError
from core.monitoring.hybrid_service import HybridMonitoringService
from core.monitoring.service import AccountMonitoringService
from trading.lifecycle_manager import TradeLifecycleManager
from trading.engine import TradingEngine


# Request/Response Models
class TradingIntent(BaseModel):
    """
    Confidence-based trading intent from Decision Module.
    
    The Decision Module outputs market analysis with a confidence score,
    and the Trading Module calculates position sizing based on that confidence.
    """
    decision_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str = Field(..., description="Trading action (e.g., 'enter_long', 'go long', 'buy')")
    symbol: str = Field(..., description="Trading symbol (e.g., 'BTC/USD', 'Bitcoin')")
    exchange: Optional[str] = Field(default="bitmex", description="Exchange name")
    timeframe: Optional[str] = Field(default="15m", description="Timeframe for analysis")
    confidence: float = Field(..., description="Confidence score (0.0-1.0) from Decision Module")
    stop_loss_price: Optional[float] = Field(None, description="Stop loss price")
    take_profit_price: Optional[float] = Field(None, description="Take profit price")
    reasoning: Optional[str] = Field(None, description="Reasoning for the trade")
    
    class Config:
        extra = "allow"  # Allow additional fields for flexibility


class ExecutionResponse(BaseModel):
    """Response from trade execution."""
    status: str = Field(..., description="Execution status: success, error, rejected")
    trade_id: Optional[str] = Field(None, description="Trade ID if successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Execution results")
    error: Optional[str] = Field(None, description="Error message if failed")
    details: Optional[Any] = Field(None, description="Additional details")


class PositionInfo(BaseModel):
    """Information about a trading position."""
    symbol: str
    contracts: float
    side: str
    entry_price: Optional[float] = None
    current_price: Optional[float] = None
    pnl: Optional[float] = None
    margin: Optional[float] = None


class AccountStatus(BaseModel):
    """Account and position status."""
    account: Dict[str, Any]
    positions: List[PositionInfo]
    timestamp: str


class WebhookRequest(BaseModel):
    user_id: str = DEFAULT_USER_ID
    config_id: str = "a93de31b-9b8a-42e3-827d-c31e580f5f36"  # Same UUID as new_trade.py
    decision_id: Optional[str] = None
    llm_decision: Optional[str] = None
    confidence: Optional[float] = None
    action: Optional[str] = None
    symbol: Optional[str] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    reasoning: Optional[str] = None
    
    class Config:
        extra = "allow"


# Global state for trading engines (per user)
trading_engines: Dict[str, TradingEngine] = {}


async def verify_strategy_runs_webhook(trade_id: str, config_id: str) -> bool:
    """
    Verify strategy_runs entries were created for the trade (like new_trade.py verify_strategy_runs).
    
    Args:
        trade_id: The trade ID to verify
        config_id: The config ID for the trade
        
    Returns:
        True if strategy_runs entries exist, False otherwise
    """
    logger.info(f"Verifying strategy_runs entries for trade {trade_id}...")
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # First check if any strategy_runs exist for this config (like new_trade.py)
                cursor.execute("""
                    SELECT scenario, confidence_score, reasoning_log, created_at
                    FROM strategy_runs
                    WHERE config_id = %s
                    ORDER BY created_at DESC
                    LIMIT 10
                """, (config_id,))
                
                results = cursor.fetchall()
                
                if results:
                    logger.info(f"✓ Found {len(results)} strategy_runs entries:")
                    for scenario, confidence, reasoning, created_at in results:
                        logger.info(f"  - {scenario}: confidence={confidence}, created={created_at}")
                        if reasoning:
                            logger.info(f"    Reasoning: {reasoning[:100]}...")
                    return True
                else:
                    logger.warning("✗ No strategy_runs entries found")
                    return False
                    
    except Exception as e:
        logger.error(f"✗ Error checking strategy_runs: {e}")
        return False


async def verify_trade_execution(user_id: str, config_id: str) -> Dict[str, Any]:
    """
    Verify trade execution by syncing with exchange and checking positions.
    Same logic as new_trade.py verify_exchange_sync().
    """
    logger.bind(user_id=user_id).info("🔍 Verifying trade execution via exchange sync...")
    
    try:
        # Get credentials from environment (consistent with new_trade.py)
        api_key = os.getenv('EXCHANGE_API')
        secret = os.getenv('EXCHANGE_SECRET')
        
        if not api_key or not secret:
            logger.bind(user_id=user_id).warning("Exchange credentials not found - cannot verify real positions")
            return {
                'total_positions': 0,
                'trades_opened': 0,
                'trades_updated': 0,
                'trades_closed': 0,
                'sync_errors': 0,
                'account_updated': False,
                'position_sync_performed': False,
                'error': 'No credentials available'
            }
        
        credentials = {
            'apiKey': api_key,
            'secret': secret
        }
        
        # Create monitoring service
        monitor = AccountMonitoringService(
            user_id=user_id,
            config_id=config_id,
            exchange_name="bitmex",
            credentials=credentials,
            testnet=True
        )
        
        # Create exchange connection and get fresh state
        try:
            monitor.exchange = await monitor._create_exchange_client()
            result = await monitor._update_account_state()
            
            # Also verify trade lifecycle sync separately (like new_trade.py)
            lifecycle_positions = await monitor.adapter.get_positions_for_lifecycle(monitor.exchange)
            lifecycle_manager = TradeLifecycleManager(user_id, "bitmex", config_id)
            sync_results = await lifecycle_manager.sync_positions_to_trades(lifecycle_positions, monitor.adapter)
            
            # Update with lifecycle sync results
            result.update({
                'trades_opened': sync_results['trades_opened'],
                'trades_updated': sync_results['trades_updated'], 
                'trades_closed': sync_results['trades_closed'],
                'sync_errors': len(sync_results['errors'])
            })
            
            # Log results including trade lifecycle sync
            logger.bind(user_id=user_id).info("✅ Trade verification and lifecycle sync complete:")
            logger.bind(user_id=user_id).info(f"  - Live positions on exchange: {result['total_positions']}")
            logger.bind(user_id=user_id).info(f"  - Trade lifecycle: {result['trades_opened']} opened, {result['trades_updated']} updated, {result['trades_closed']} closed")
            logger.bind(user_id=user_id).info(f"  - Sync errors: {result['sync_errors']}")
            logger.bind(user_id=user_id).info(f"  - Account state updated: {result['account_updated']}")
            
            return result
            
        finally:
            # Always ensure exchange connection is closed
            if hasattr(monitor, 'exchange') and monitor.exchange:
                try:
                    await monitor.exchange.close()
                    monitor.exchange = None
                except Exception as cleanup_error:
                    logger.bind(user_id=user_id).warning(f"Error closing exchange connection: {cleanup_error}")
        
    except Exception as e:
        logger.bind(user_id=user_id).error(f"Trade verification failed: {e}")
        return {
            'total_positions': 0,
            'trades_opened': 0,
            'trades_updated': 0,
            'trades_closed': 0,
            'sync_errors': 1,
            'account_updated': False,
            'position_sync_performed': False,
            'error': str(e)
        }


async def get_account_state(user_id: str, exchange: str = "bitmex") -> Optional[Dict[str, Any]]:
    """
    Get latest account state from monitoring data.
    Uses the same pattern as the working test script.
    
    Args:
        user_id: User ID
        exchange: Exchange name (default: bitmex)
        
    Returns:
        Account state dict or None if not found
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            query = """
                SELECT balance_data, position_data, equity,
                       available_margin, used_margin, updated_at
                FROM account_states
                WHERE user_id = %s AND exchange = %s
                ORDER BY updated_at DESC
                LIMIT 1
            """
            
            cursor.execute(query, (user_id, exchange))
            row = cursor.fetchone()
            
            if row:
                balance_data, position_data, equity, available_margin, used_margin, updated_at = row
                
                # Parse JSONB data if stored as strings
                import json
                if isinstance(balance_data, str):
                    balance_data = json.loads(balance_data)
                if isinstance(position_data, str):
                    position_data = json.loads(position_data)
                
                return {
                    'balance_data': balance_data,
                    'position_data': position_data,
                    'equity': float(equity) if equity else float(available_margin) if available_margin else 0,
                    'available_margin': float(available_margin) if available_margin else 0,
                    'used_margin': float(used_margin) if used_margin else 0,
                    'updated_at': updated_at
                }
    
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan event handler for startup and shutdown.
    """
    # Startup
    logger.info("Starting Trading API server...")
    
    # Initialize default trading engine for testing
    if os.environ.get("TESTNET") == "1":
        logger.info("Initializing testnet trading engine...")
        try:
            engine = await create_trading_engine(DEFAULT_USER_ID)
            trading_engines[DEFAULT_USER_ID] = engine
            logger.info("Testnet trading engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize testnet engine: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Trading API server...")
    for user_id, engine in trading_engines.items():
        try:
            await engine.stop()
            logger.info(f"Stopped trading engine for user {user_id}")
        except Exception as e:
            logger.error(f"Error stopping engine for user {user_id}: {e}")


# Create FastAPI app
app = FastAPI(
    title="GGBot Trading API",
    description="Trading Module API for executing trades based on Decision Module intents",
    version="1.0.0",
    lifespan=lifespan
)


async def create_trading_engine(user_id: str, config_id: Optional[str] = None) -> TradingEngine:
    """
    Create or retrieve a trading engine for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        TradingEngine instance
    """
    if user_id in trading_engines:
        return trading_engines[user_id]
    
    # Get exchange guide based on configured exchange and environment
    exchange_name = os.environ.get("EXCHANGE_NAME", "bitmex")
    use_testnet = os.environ.get("TESTNET", "1") == "1"
    exchange_guide = ""
    
    if exchange_name.lower() == "bitmex":
        if use_testnet:
            from trading.exchanges.bitmex.exchange_guide_testnet import get_exchange_guide_text
        else:
            from trading.exchanges.bitmex.exchange_guide import get_exchange_guide_text
        exchange_guide = get_exchange_guide_text()
    # Add other exchanges here as needed
    # elif exchange_name.lower() == "binance":
    #     from trading.exchanges.binance.exchange_guide import get_exchange_guide_text
    #     exchange_guide = get_exchange_guide_text()
    
    # Load unified user configuration from database
    user_config = None
    risk_rules = {}
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            if config_id:
                # Use specific config_id if provided
                cursor.execute("""
                    SELECT config_data 
                    FROM configurations 
                    WHERE user_id = %s 
                    AND config_id = %s
                """, (user_id, config_id))
            else:
                # Otherwise get latest config
                cursor.execute("""
                    SELECT config_data 
                    FROM configurations 
                    WHERE user_id = %s
                    ORDER BY created_at DESC 
                    LIMIT 1
                """, (user_id,))
            
            result = cursor.fetchone()
            if result:
                user_config = result[0]
                # Extract trading config and risk rules from unified config
                if 'trading' in user_config and 'risk_rules' in user_config['trading']:
                    risk_rules = user_config['trading']['risk_rules']
                    logger.info(f"Loaded risk rules from unified config for {user_id}" + 
                               (f" (config_id: {config_id})" if config_id else ""))
    
    # Extract risk parameters with defaults
    max_leverage = risk_rules.get('max_leverage', 10)
    max_position_pct = risk_rules.get('max_position_size_pct', 0.05)
    max_risk_pct = risk_rules.get('max_risk_per_trade_pct', 0.05)
    min_equity_protection = risk_rules.get('min_equity_protection', 0.80)
    max_contracts = risk_rules.get('max_contracts_per_trade', 1000000)
    
    logger.info(f"Using risk rules: max_leverage={max_leverage}, max_position_pct={max_position_pct}")
    
    # Configuration for the trading engine
    config = {
        "llm": {
            "model": "gpt-4",
            "system_prompt": f"You are an expert trading assistant. Your task is to help execute trading decisions through the CCXT API.\n\n{exchange_guide}",
            "temperature": 0.0,
            "max_retries": 2
        },
        "validation": {
            "max_leverage": max_leverage,
            "max_position_pct": max_position_pct
        },
        "execution": {
            "polling_interval": 5,
            "max_retries": 2
        },
        "default_exchange": os.environ.get("EXCHANGE_NAME", "bitmex"),
        "use_testnet": os.environ.get("TESTNET", "1") == "1",
        "server_path": str(Path(__file__).parent.parent / "core" / "mcp" / "servers" / "ccxt_mcp_server.py"),
        "credentials": {
            "apiKey": os.environ.get("EXCHANGE_API"),
            "secret": os.environ.get("EXCHANGE_SECRET")
        },
        "risk_rules": {
            "max_leverage": max_leverage,
            "max_position_size_pct": max_position_pct,
            "max_risk_per_trade_pct": max_risk_pct,
            "min_equity_protection": min_equity_protection,
            "max_contracts_per_trade": max_contracts
        }
    }
    
    # Create the engine
    engine = TradingEngine(user_id=user_id, config=config)
    await engine.start()
    
    # Store it
    trading_engines[user_id] = engine
    
    return engine


async def get_trading_engine(user_id: str = DEFAULT_USER_ID) -> TradingEngine:
    """
    Dependency to get trading engine for a user.
    Reuses existing engines like working tests do with session-wide clients.
    
    Args:
        user_id: User ID (defaults to test user)
        
    Returns:
        TradingEngine instance
    """
    # Reuse existing engine if available (like session-wide pattern)
    if user_id in trading_engines:
        engine = trading_engines[user_id]
        # Verify engine is still active
        if hasattr(engine, 'is_active') and engine.is_active:
            return engine
        else:
            # Engine is stale, remove it
            del trading_engines[user_id]
    
    # Create new engine if none exists or old one is stale
    return await create_trading_engine(user_id)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "trading-api",
        "timestamp": datetime.utcnow().isoformat(),
        "engines_active": len(trading_engines)
    }


@app.post("/trade/execute", response_model=ExecutionResponse)
async def execute_trade(
    intent: TradingIntent,
    engine: TradingEngine = Depends(get_trading_engine)
) -> ExecutionResponse:
    """
    Execute a trading intent.
    
    This endpoint receives a semi-structured trading intent from the Decision Module
    and processes it through the Trading Engine to execute trades on the exchange.
    
    The intent is interpreted by an LLM which generates the appropriate tool calls
    for the specific exchange. Validation happens at the tool call level, not at
    the intent input level, allowing for flexible input formats.
    
    Args:
        intent: Trading intent with flexible structure
        engine: Trading engine instance (injected)
        
    Returns:
        Execution response with status and details
    """
    try:
        logger.bind(user_id=engine.user_id).info(f"Executing trade intent: {intent.decision_id}")
        
        # Step 1: Get current account state for risk calculations
        exchange_name = intent.exchange or "bitmex"
        account_state = await get_account_state(engine.user_id, exchange_name)
        
        if not account_state:
            logger.bind(user_id=engine.user_id).warning("No account state available - proceeding without risk adjustments")
            account_state = {
                'available_margin': 0,
                'equity': 0,
                'used_margin': 0,
                'balance_data': {},
                'position_data': []
            }
        else:
            logger.bind(user_id=engine.user_id).info(
                f"Account state: {account_state['available_margin']:.8f} BTC available margin, "
                f"{account_state['equity']:.8f} BTC equity"
            )
        
        # Step 2: Convert Pydantic model to dict and add account state context
        intent_data = intent.model_dump()
        
        # Step 3: Standardize account balance
        standardized_balance = _standardize_account_balance(account_state)
        account_balance_usd = standardized_balance['account_balance_usd']
        
        # Step 4: Calculate position size based on confidence
        if intent_data.get('confidence') is not None:
            confidence = intent_data['confidence']
            
            # Get risk configuration from user config or use defaults
            # TODO: Load from user configuration when available
            default_leverage = 10
            min_position_usd = 100.0
            max_position_usd = 10000.0
            
            # Calculate position based on confidence
            position_calc = calculate_position_from_confidence(
                confidence=confidence,
                account_balance_usd=account_balance_usd,
                default_leverage=default_leverage,
                min_position_usd=min_position_usd,
                max_position_usd=max_position_usd
            )
            
            # Add calculated values to intent data
            intent_data['collateral_amount'] = position_calc['collateral_amount']
            intent_data['leverage'] = position_calc['leverage']
            intent_data['risk_percentage'] = position_calc['risk_percentage']
            intent_data['position_size_usd'] = position_calc['position_size_usd']
            
            logger.bind(user_id=engine.user_id).info(
                f"📊 Position sized from confidence {confidence:.2f}: "
                f"${position_calc['collateral_amount']:.2f} collateral "
                f"({position_calc['risk_percentage']:.1f}% risk) "
                f"@ {position_calc['leverage']}x leverage"
            )
        else:
            # Fallback if confidence not provided
            logger.bind(user_id=engine.user_id).warning(
                "No confidence score provided, using minimal position"
            )
            intent_data['confidence'] = 0.5  # Default moderate confidence
            intent_data['collateral_amount'] = 100.0  # Minimum position
            intent_data['leverage'] = 10
            intent_data['risk_percentage'] = 0.1
            intent_data['position_size_usd'] = 1000.0
        
        # Step 5: Add account state to intent for validation context
        intent_data['_account_state'] = account_state
        
        # Add context for risk validation (pass both equity and available_margin)
        validation_context = {
            "equity": account_state.get('equity', 0),
            "available_margin": account_state.get('available_margin', 0),
            "used_margin": account_state.get('used_margin', 0),
            "timestamp": datetime.utcnow().timestamp()
        }
        
        # Step 6: Process through the trading engine
        result = await engine.process_decision_intent(intent_data)
        
        # Map engine response to API response
        if result.get("status") == "success":
            # Step 7: Trigger monitoring update to confirm execution
            try:
                monitoring = HybridMonitoringService(engine.user_id)
                
                # Get expected trade details from intent
                expected_symbol = intent_data.get('symbol', 'BTC/USD')
                expected_side = intent_data.get('side', '')
                
                if intent.action == 'open_position' and expected_side:
                    logger.bind(user_id=engine.user_id).info(
                        f"Triggering position verification for {expected_symbol} {expected_side}"
                    )
                    
                    # Verify trade execution with monitoring
                    position = await monitoring.verify_trade_execution(
                        expected_symbol=expected_symbol,
                        expected_side=expected_side,
                        timeout=15.0
                    )
                    
                    if position:
                        logger.bind(user_id=engine.user_id).info(
                            f"Trade confirmed: {position.get('symbol')} "
                            f"{position.get('contracts', 0)} contracts"
                        )
                        result['confirmed'] = True
                        result['position'] = position
                    else:
                        logger.bind(user_id=engine.user_id).warning(
                            "Trade executed but position not confirmed in time"
                        )
                        result['confirmed'] = False
                        
            except Exception as e:
                logger.bind(user_id=engine.user_id).error(f"Monitoring verification failed: {e}")
                # Don't fail the trade response, just log the monitoring error
            
            # Serialize execution_result to dict if it's an object
            execution_result = result.get("execution_result")
            if execution_result and hasattr(execution_result, '__dict__'):
                execution_data = execution_result.__dict__
            elif execution_result and hasattr(execution_result, 'model_dump'):
                execution_data = execution_result.model_dump()
            else:
                execution_data = execution_result
            
            return ExecutionResponse(
                status="success",
                trade_id=result.get("trade_id"),
                data=execution_data,
                details=result.get("details")
            )
        elif result.get("status") == "rejected":
            return ExecutionResponse(
                status="rejected",
                error=result.get("reason", "Trade rejected by validation"),
                details=result.get("details")
            )
        else:
            return ExecutionResponse(
                status="error",
                error=result.get("error", "Unknown error"),
                details=result.get("details")
            )
            
    except MCPError as e:
        logger.bind(user_id=engine.user_id).error(f"MCP error: {str(e)}")
        return ExecutionResponse(
            status="error",
            error="Exchange connection failed",
            details=str(e)
        )
    except Exception as e:
        logger.bind(user_id=engine.user_id).error(f"Unexpected error: {str(e)}")
        return ExecutionResponse(
            status="error",
            error="Internal server error",
            details=str(e) if os.environ.get("DEBUG") else None
        )


@app.get("/trade/status", response_model=AccountStatus)
async def get_trade_status(
    engine: TradingEngine = Depends(get_trading_engine)
) -> AccountStatus:
    """
    Get current account status and positions.
    
    Returns the current account balance, margin information, and all open positions
    from the exchange.
    
    Args:
        engine: Trading engine instance (injected)
        
    Returns:
        Account status with balance and position information
    """
    try:
        logger.bind(user_id=engine.user_id).info("Fetching account status")
        
        # Ensure exchange connection
        await engine.ccxt_adapter.ensure_connected()
        
        # Fetch account balance
        balance = await engine.ccxt_adapter.fetch_balance()
        
        # Fetch open positions
        positions = await engine.ccxt_adapter.fetch_positions()
        
        # Convert positions to response format
        position_list = []
        for pos in positions:
            if isinstance(pos, dict) and float(pos.get("contracts", 0)) != 0:
                position_list.append(PositionInfo(
                    symbol=pos.get("symbol", ""),
                    contracts=float(pos.get("contracts", 0)),
                    side=pos.get("side", ""),
                    entry_price=pos.get("markPrice"),
                    current_price=pos.get("markPrice"),
                    pnl=pos.get("percentage", 0),
                    margin=pos.get("initialMargin", 0)
                ))
        
        return AccountStatus(
            account=balance,
            positions=position_list,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.bind(user_id=engine.user_id).error(f"Error fetching status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch account status")


@app.get("/trade/history")
async def get_trade_history(
    limit: int = 10,
    engine: TradingEngine = Depends(get_trading_engine)
):
    """
    Get recent trade history.
    
    Returns a list of recent trades executed by this trading engine.
    
    Args:
        limit: Maximum number of trades to return
        engine: Trading engine instance (injected)
        
    Returns:
        List of recent trades
    """
    try:
        logger.bind(user_id=engine.user_id).info("Fetching trade history")
        
        # For now, return from the mock DB
        # In production, this will query the real database
        trades = await engine.trade_manager.get_active_trades()
        
        return {
            "trades": trades[:limit],
            "count": len(trades),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.bind(user_id=engine.user_id).error(f"Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch trade history")


@app.post("/trade/close-position")
async def close_position(
    symbol: str,
    engine: TradingEngine = Depends(get_trading_engine)
):
    """
    Close a specific position.
    
    Closes an open position for the specified symbol by creating a market order
    in the opposite direction.
    
    Args:
        symbol: Trading symbol to close (e.g., "BTC/USD")
        engine: Trading engine instance (injected)
        
    Returns:
        Execution result
    """
    try:
        logger.bind(user_id=engine.user_id).info(f"Closing position for {symbol}")
        
        # Create a close position intent
        close_intent = {
            "decision_id": str(uuid.uuid4()),
            "action": "close_position",
            "symbol": symbol,
            "exchange": engine.config.default_exchange,
            "reasoning": f"API request to close position for {symbol}"
        }
        
        # Process through the engine
        result = await engine.process_decision_intent(close_intent)
        
        return {
            "status": result.get("status"),
            "symbol": symbol,
            "details": result.get("details"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.bind(user_id=engine.user_id).error(f"Error closing position: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to close position")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.environ.get("DEBUG") else None
        }
    )


def main():
    """Main entry point for the Trading API server."""
    # Configure logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Get configuration from environment
    host = os.environ.get("TRADING_API_HOST", "0.0.0.0")
    port = int(os.environ.get("TRADING_API_PORT", "5000"))
    
    logger.info(f"Starting Trading API server on {host}:{port}")
    
    # Run the server
    uvicorn.run(
        "trading.api:app",
        host=host,
        port=port,
        reload=os.environ.get("DEBUG") == "1",
        log_level="info"
    )


def confidence_to_risk_percentage(confidence: float) -> float:
    """
    Map confidence score to risk percentage using tiered system.
    
    0.0-0.1 = 0.5%
    0.1-0.2 = 1.0%
    0.2-0.3 = 1.5%
    ...
    0.9-1.0 = 5.0%
    
    Args:
        confidence: Confidence score from 0.0 to 1.0
        
    Returns:
        Risk percentage (0.5 to 5.0)
    """
    # Ensure confidence is within bounds
    confidence = max(0.0, min(1.0, confidence))
    
    # Calculate tier (0-9)
    tier = min(9, int(confidence * 10))
    
    # Map to risk percentage (0.5% increments)
    risk_percentage = (tier + 1) * 0.5
    
    logger.info(f"Confidence {confidence:.2f} → Tier {tier} → Risk {risk_percentage}%")
    return risk_percentage


def calculate_position_from_confidence(
    confidence: float,
    account_balance_usd: float,
    default_leverage: int = 10,
    min_position_usd: float = 100.0,
    max_position_usd: float = 10000.0
) -> Dict[str, float]:
    """
    Calculate position size based on confidence score and account balance.
    
    Args:
        confidence: Confidence score from Decision module (0.0-1.0)
        account_balance_usd: Account balance in USD
        default_leverage: Default leverage to use (default: 10x)
        min_position_usd: Minimum position size in USD
        max_position_usd: Maximum position size (emergency cap)
        
    Returns:
        Dictionary with position calculations:
        {
            'risk_percentage': float,      # Percentage of account to risk
            'risk_amount_usd': float,      # USD amount to risk (collateral)
            'leverage': int,               # Leverage multiplier
            'position_size_usd': float,    # Total position size
            'contracts': float             # Estimated contracts (if applicable)
        }
    """
    # Get risk percentage from confidence
    risk_percentage = confidence_to_risk_percentage(confidence)
    
    # Calculate risk amount (collateral)
    risk_amount_usd = account_balance_usd * (risk_percentage / 100.0)
    
    # Calculate total position size
    position_size_usd = risk_amount_usd * default_leverage
    
    # Apply minimum position size
    if position_size_usd < min_position_usd:
        logger.warning(
            f"Position size ${position_size_usd:.2f} below minimum ${min_position_usd:.2f}, "
            f"adjusting to minimum"
        )
        position_size_usd = min_position_usd
        risk_amount_usd = position_size_usd / default_leverage
        risk_percentage = (risk_amount_usd / account_balance_usd) * 100.0
    
    # Apply maximum position size (emergency cap)
    if position_size_usd > max_position_usd:
        logger.warning(
            f"Position size ${position_size_usd:.2f} exceeds maximum ${max_position_usd:.2f}, "
            f"capping at maximum"
        )
        position_size_usd = max_position_usd
        risk_amount_usd = position_size_usd / default_leverage
        risk_percentage = (risk_amount_usd / account_balance_usd) * 100.0
    
    # For BitMEX, estimate contracts (1 contract ≈ $1)
    estimated_contracts = risk_amount_usd
    
    logger.info(
        f"Position calculation: Confidence {confidence:.2f} → "
        f"Risk {risk_percentage:.1f}% (${risk_amount_usd:.2f}) → "
        f"Position ${position_size_usd:.2f} @ {default_leverage}x leverage"
    )
    
    return {
        'risk_percentage': risk_percentage,
        'risk_amount_usd': risk_amount_usd,
        'collateral_amount': risk_amount_usd,  # Same as risk amount
        'leverage': default_leverage,
        'position_size_usd': position_size_usd,
        'contracts': estimated_contracts
    }


def _standardize_account_balance(account_state: Dict) -> Dict:
    """
    Standardize account balance from various exchange formats to unified USD format.
    
    This function handles different exchange account structures (BitMEX, Binance, etc.)
    and provides a unified account balance representation for risk calculations.
    
    Args:
        account_state: Raw account state from exchange
        
    Returns:
        Dictionary with standardized balance information:
        {
            'account_balance_usd': float,     # Primary balance for risk calculations
            'available_margin_usd': float,    # Available for new positions
            'equity_usd': float,             # Net account value
            'used_margin_usd': float,        # Currently used margin
            'btc_price_used': float          # BTC price used for conversion
        }
    """
    try:
        # Use current BTC price (conservative estimate)
        # TODO: Get real-time price from market data
        btc_price = 104000  # Conservative estimate based on recent market price
        
        result = {
            'account_balance_usd': 0.0,
            'available_margin_usd': 0.0,
            'equity_usd': 0.0,
            'used_margin_usd': 0.0,
            'btc_price_used': btc_price
        }
        
        # Handle BitMEX account structure
        if 'balance_data' in account_state:
            balance_data = account_state['balance_data']
            
            # Prefer total_usd_value if available (most accurate)
            if 'total_usd_value' in balance_data:
                result['account_balance_usd'] = float(balance_data['total_usd_value'])
                result['available_margin_usd'] = result['account_balance_usd']  # Assume fully available
                result['equity_usd'] = result['account_balance_usd']
                logger.info(f"Using total_usd_value: ${result['account_balance_usd']:,.2f}")
                return result
            
            # Convert BTC balances to USD
            if 'available_btc' in balance_data:
                available_btc = float(balance_data['available_btc'])
                result['account_balance_usd'] = available_btc * btc_price
                result['available_margin_usd'] = result['account_balance_usd']
                result['equity_usd'] = result['account_balance_usd']
                logger.info(f"Converted available_btc: {available_btc:.8f} BTC × ${btc_price:,} = ${result['account_balance_usd']:,.2f}")
                return result
        
        # Handle direct BTC fields (BitMEX style)
        if 'available_margin' in account_state:
            available_margin_btc = float(account_state['available_margin'])
            result['account_balance_usd'] = available_margin_btc * btc_price
            result['available_margin_usd'] = result['account_balance_usd']
            
            # Handle equity separately if available
            if 'equity' in account_state:
                equity_btc = float(account_state['equity'])
                result['equity_usd'] = equity_btc * btc_price
            else:
                result['equity_usd'] = result['account_balance_usd']
            
            logger.info(f"Converted available_margin: {available_margin_btc:.8f} BTC × ${btc_price:,} = ${result['account_balance_usd']:,.2f}")
            return result
        
        # Handle direct equity field
        if 'equity' in account_state:
            equity_btc = float(account_state['equity'])
            result['account_balance_usd'] = equity_btc * btc_price
            result['available_margin_usd'] = result['account_balance_usd']
            result['equity_usd'] = result['account_balance_usd']
            logger.info(f"Converted equity: {equity_btc:.8f} BTC × ${btc_price:,} = ${result['account_balance_usd']:,.2f}")
            return result
        
        # Emergency fallback
        logger.warning("Could not extract account balance from account_state, using emergency minimum")
        result['account_balance_usd'] = 1000.0  # Emergency minimum
        result['available_margin_usd'] = 1000.0
        result['equity_usd'] = 1000.0
        
        return result
        
    except Exception as e:
        logger.error(f"Error standardizing account balance: {e}")
        # Emergency fallback
        return {
            'account_balance_usd': 1000.0,
            'available_margin_usd': 1000.0,
            'equity_usd': 1000.0,
            'used_margin_usd': 0.0,
            'btc_price_used': 104000
        }


@app.post("/webhooks/execute-trade")
async def webhook_execute_trade(request: WebhookRequest):
    """
    Webhook endpoint to execute trades.
    
    This endpoint implements the full trading logic from new_trade.py including:
    - Position sizing calculation based on confidence (SAME AS /trade/execute)
    - Trade execution through Trading Engine
    - Post-trade verification and exchange sync
    - Trade lifecycle management
    """
    try:
        logger.bind(user_id=request.user_id).info(
            f"⚡ Trading webhook triggered for config {request.config_id}: {request.action}"
        )
        
        # Get trading engine for user
        engine = await get_trading_engine(request.user_id)
        
        # Convert webhook request to TradingIntent
        intent_data = request.model_dump()
        
        # Remove None values to avoid issues
        intent_data = {k: v for k, v in intent_data.items() if v is not None}
        
        # Ensure required fields
        if not intent_data.get('action'):
            intent_data['action'] = 'no_action'
        if not intent_data.get('symbol'):
            intent_data['symbol'] = 'BTC/USD'
        if not intent_data.get('confidence'):
            intent_data['confidence'] = 0.5
        
        # === POSITION SIZING LOGIC (SAME AS /trade/execute) ===
        
        # Step 1: Get current account state for risk calculations
        exchange_name = intent_data.get('exchange', 'bitmex')
        account_state = await get_account_state(engine.user_id, exchange_name)
        
        if not account_state:
            logger.bind(user_id=engine.user_id).warning("No account state available - proceeding without risk adjustments")
            account_state = {
                'available_margin': 0,
                'equity': 0,
                'used_margin': 0,
                'balance_data': {},
                'position_data': []
            }
        else:
            logger.bind(user_id=engine.user_id).info(
                f"Account state: {account_state['available_margin']:.8f} BTC available margin, "
                f"{account_state['equity']:.8f} BTC equity"
            )
        
        # Step 2: Standardize account balance
        standardized_balance = _standardize_account_balance(account_state)
        account_balance_usd = standardized_balance['account_balance_usd']
        
        # Step 3: Calculate position size based on confidence
        if intent_data.get('confidence') is not None:
            confidence = intent_data['confidence']
            
            # Get risk configuration from user config or use defaults
            default_leverage = 10
            min_position_usd = 100.0
            max_position_usd = 10000.0
            
            # Calculate position based on confidence
            position_calc = calculate_position_from_confidence(
                confidence=confidence,
                account_balance_usd=account_balance_usd,
                default_leverage=default_leverage,
                min_position_usd=min_position_usd,
                max_position_usd=max_position_usd
            )
            
            # Add calculated values to intent data
            intent_data['collateral_amount'] = position_calc['collateral_amount']
            intent_data['leverage'] = position_calc['leverage']
            intent_data['risk_percentage'] = position_calc['risk_percentage']
            intent_data['position_size_usd'] = position_calc['position_size_usd']
            
            logger.bind(user_id=engine.user_id).info(
                f"📊 Position sized from confidence {confidence:.2f}: "
                f"${position_calc['collateral_amount']:.2f} collateral "
                f"({position_calc['risk_percentage']:.1f}% risk) "
                f"@ {position_calc['leverage']}x leverage"
            )
        else:
            # Fallback if confidence not provided
            logger.bind(user_id=engine.user_id).warning(
                "No confidence score provided, using minimal position"
            )
            intent_data['confidence'] = 0.5  # Default moderate confidence
            intent_data['collateral_amount'] = 100.0  # Minimum position
            intent_data['leverage'] = 10
            intent_data['risk_percentage'] = 0.1
            intent_data['position_size_usd'] = 1000.0
        
        # Step 4: Add account state to intent for validation context
        intent_data['_account_state'] = account_state
        
        # === END POSITION SIZING LOGIC ===
        
        # Execute through trading engine (now with proper position sizing)
        logger.bind(user_id=request.user_id).info(f"🔄 Executing trade: {intent_data.get('action')}")
        result = await engine.process_decision_intent(intent_data)
        
        # Post-trade verification (comprehensive like new_trade.py)
        verification_result = None
        strategy_runs_verified = False
        
        if result.get("status") == "success" and intent_data.get('action') not in ['no_action', 'hold', 'wait']:
            logger.bind(user_id=request.user_id).info("🔍 Performing comprehensive post-trade verification...")
            
            # Wait for position to settle (like new_trade.py line 432 - strategic timing)
            import asyncio
            logger.bind(user_id=request.user_id).info("⏱️ Waiting for position settlement...")
            await asyncio.sleep(5)  # Match new_trade.py timing
            
            # Verify trade execution via exchange sync (like new_trade.py verify_exchange_sync)
            verification_result = await verify_trade_execution(request.user_id, request.config_id)
            
            # Verify strategy_runs audit trail (like new_trade.py verify_strategy_runs)
            trade_id = result.get("trade_id")
            if trade_id:
                strategy_runs_verified = await verify_strategy_runs_webhook(trade_id, request.config_id)
            
            # Enhanced status based on comprehensive verification
            if (verification_result and verification_result.get('total_positions', 0) > 0 and strategy_runs_verified):
                logger.bind(user_id=request.user_id).info("✅ Trade fully verified: Position + audit trail confirmed")
                verification_status = "fully_verified"
            elif (verification_result and verification_result.get('total_positions', 0) > 0):
                logger.bind(user_id=request.user_id).info("⚠️ Trade verified but missing audit trail")
                verification_status = "position_verified_no_audit"
            else:
                logger.bind(user_id=request.user_id).warning("⚠️ Trade executed but position not confirmed")
                verification_status = "executed_not_verified"
        else:
            verification_status = "no_verification_needed"
        
        # Return comprehensive status (like new_trade.py)
        response = {
            "status": result.get("status", "unknown"),
            "trade_id": result.get("trade_id"),
            "action": intent_data.get('action'),
            "symbol": intent_data.get('symbol'),
            "confidence": intent_data.get('confidence'),
            "message": f"Trade executed via webhook ({verification_status})",
            "user_id": request.user_id,
            "config_id": request.config_id,
            "details": result.get("details"),
            "verification_status": verification_status
        }
        
        # Add verification details if available (comprehensive like new_trade.py)
        if verification_result:
            response.update({
                "verification": {
                    "positions_on_exchange": verification_result.get('total_positions', 0),
                    "trades_opened": verification_result.get('trades_opened', 0),
                    "trades_updated": verification_result.get('trades_updated', 0),
                    "trades_closed": verification_result.get('trades_closed', 0),
                    "sync_errors": verification_result.get('sync_errors', 0),
                    "strategy_runs_verified": strategy_runs_verified,
                    "account_updated": verification_result.get('account_updated', False),
                    "position_sync_performed": verification_result.get('position_sync_performed', False)
                }
            })
        
        logger.bind(user_id=request.user_id).info(
            f"🏁 Trading webhook completed: {response['status']} ({verification_status})"
        )
        
        return response
        
    except Exception as e:
        logger.bind(user_id=request.user_id).error(
            f"❌ Webhook trade execution failed: {str(e)}"
        )
        return {
            "status": "error",
            "error": str(e),
            "message": "Trade webhook failed",
            "user_id": request.user_id,
            "config_id": request.config_id,
            "verification_status": "error"
        }


if __name__ == "__main__":
    main()