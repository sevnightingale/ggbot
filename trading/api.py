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

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from core.common.db import get_db_connection
from core.mcp.exceptions import MCPError
from trading.engine import TradingEngine


# Request/Response Models
class TradingIntent(BaseModel):
    """
    Semi-structured trading intent from Decision Module.
    
    Note: We use flexible typing here because the Trading LLM will interpret
    variations in field values. Strict validation happens at the tool call level,
    not at the intent input level.
    """
    decision_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str = Field(..., description="Trading action (e.g., 'enter_long', 'go long', 'buy')")
    symbol: str = Field(..., description="Trading symbol (e.g., 'BTC/USD', 'Bitcoin')")
    exchange: Optional[str] = Field(default="bitmex", description="Exchange name")
    timeframe: Optional[str] = Field(default="15m", description="Timeframe for analysis")
    collateral_amount: Optional[float] = Field(None, description="Collateral amount in USD")
    leverage: Optional[float] = Field(None, description="Leverage to use")
    stop_loss_price: Optional[float] = Field(None, description="Stop loss price")
    take_profit_price: Optional[float] = Field(None, description="Take profit price")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")
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


# Global state for trading engines (per user)
trading_engines: Dict[str, TradingEngine] = {}


async def get_account_state(user_id: str, exchange: str = "bitmex") -> Optional[Dict[str, Any]]:
    """
    Get latest account state from monitoring data.
    
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
                    'equity': float(equity) if equity else 0,
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


async def create_trading_engine(user_id: str) -> TradingEngine:
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
    
    # Configuration for the trading engine
    config = {
        "llm": {
            "model": "gpt-4",
            "system_prompt": f"You are an expert trading assistant. Your task is to help execute trading decisions through the CCXT API.\n\n{exchange_guide}",
            "temperature": 0.0,
            "max_retries": 2
        },
        "validation": {
            "max_leverage": 10,
            "max_position_pct": 0.05
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
        
        # Step 3: Adjust position sizing based on available margin (like working test)
        if account_state['available_margin'] > 0 and intent_data.get('collateral_amount'):
            # Convert BTC margin to USD (approximate conversion)
            btc_price_estimate = 110000  # Rough estimate, could be made dynamic
            available_margin_usd = account_state['available_margin'] * btc_price_estimate
            
            requested_amount = intent_data['collateral_amount']
            max_safe_amount = available_margin_usd * 0.5  # Use max 50% of available margin
            
            if requested_amount > max_safe_amount:
                adjusted_amount = max_safe_amount
                logger.bind(user_id=engine.user_id).warning(
                    f"Adjusting position size from ${requested_amount:.2f} to ${adjusted_amount:.2f} "
                    f"based on available margin (${available_margin_usd:.2f})"
                )
                intent_data['collateral_amount'] = adjusted_amount
                intent_data['reasoning'] += f" [Adjusted from ${requested_amount:.2f} to ${adjusted_amount:.2f} due to margin limits]"
        
        # Step 4: Add account state to intent for validation context
        intent_data['_account_state'] = account_state
        
        # Step 5: Process through the trading engine
        result = await engine.process_decision_intent(intent_data)
        
        # Map engine response to API response
        if result.get("status") == "success":
            return ExecutionResponse(
                status="success",
                trade_id=result.get("trade_id"),
                data=result.get("execution_result"),
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


if __name__ == "__main__":
    main()