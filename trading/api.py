#!/usr/bin/env python
"""
New Hummingbot-based Trading Module API

Provides REST API endpoints for executing trades via Hummingbot integration.
Replaces the legacy CCXT-based trading system with a clean, modern interface.

Same endpoints as legacy system but completely different backend implementation.
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

# Add hummingbot client to path for API client imports
sys.path.insert(0, str(Path(__file__).parent.parent / "hummingbot" / "client"))

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from trading.services import HummingbotExecutionAdapter, TradeIntent
from trading.hummingbot_api import router as hummingbot_router


# Request/Response Models (Same as legacy for compatibility)
class TradingIntent(BaseModel):
    """
    Confidence-based trading intent from Decision Module.
    
    The Decision Module outputs market analysis with a confidence score,
    and the Trading Module calculates position sizing based on that confidence.
    """
    decision_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str = Field(..., description="Trading action (e.g., 'enter_long', 'go long', 'buy')")
    symbol: str = Field(..., description="Trading symbol (e.g., 'BTC/USD', 'Bitcoin')")
    exchange: Optional[str] = Field(default="binance_perpetual_testnet", description="Exchange connector")
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
    """Webhook request from Decision Module."""
    user_id: str = DEFAULT_USER_ID
    config_id: str = Field(..., description="Configuration ID (no longer hardcoded)")
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


# Global adapter instance
execution_adapter = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global execution_adapter
    
    # Startup
    logger.bind(service="trading_api").info("Starting Hummingbot Trading API...")
    
    try:
        # Initialize execution adapter
        execution_adapter = HummingbotExecutionAdapter()
        logger.bind(service="trading_api").info("HummingbotExecutionAdapter initialized")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize trading API: {e}")
        raise
    finally:
        # Shutdown
        logger.bind(service="trading_api").info("Shutting down trading API...")


# Create FastAPI app
app = FastAPI(
    title="Hummingbot Trading API",
    description="Hummingbot-based trading execution engine",
    version="2.0.0",
    lifespan=lifespan
)

# Include Hummingbot monitoring endpoints
app.include_router(hummingbot_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Hummingbot Trading API",
        "version": "2.0.0", 
        "status": "running",
        "backend": "hummingbot"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    global execution_adapter
    
    if execution_adapter is None:
        raise HTTPException(status_code=503, detail="Execution adapter not initialized")
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "backend": "hummingbot",
        "adapter_ready": execution_adapter is not None
    }


@app.post("/webhooks/execute-trade")
async def webhook_execute_trade(request: WebhookRequest):
    """
    Webhook endpoint to execute trades via Hummingbot.
    
    Same endpoint as legacy system but completely new backend:
    - Uses HummingbotExecutionAdapter instead of TradingEngine
    - LLM normalization for signal processing
    - Direct PositionExecutor creation via Hummingbot API
    - Paper trading by default
    
    Maintains compatibility with Decision Module expectations.
    """
    global execution_adapter
    
    if execution_adapter is None:
        raise HTTPException(status_code=503, detail="Execution adapter not initialized")
    
    try:
        logger.bind(service="trading_api").info(
            f"Processing webhook trade for user {request.user_id}, config {request.config_id}"
        )
        
        # Convert webhook request to raw signal format
        raw_signal = {
            "decision_id": request.decision_id,
            "llm_decision": request.llm_decision,
            "action": request.action,
            "symbol": request.symbol,
            "confidence": request.confidence,
            "stop_loss_price": request.stop_loss_price,
            "take_profit_price": request.take_profit_price,
            "reasoning": request.reasoning
        }
        
        # Execute via HummingbotExecutionAdapter
        result = await execution_adapter.execute_signal(
            raw_signal=raw_signal,
            user_id=request.user_id,
            config_id=request.config_id
        )
        
        if result["status"] == "success":
            return ExecutionResponse(
                status="success",
                trade_id=result["execution_result"].get("order_id"),
                data=result,
                details="Trade executed via Hummingbot"
            )
        else:
            return ExecutionResponse(
                status="error",
                error=result.get("error", "Unknown execution error"),
                details=result
            )
            
    except Exception as e:
        logger.error(f"Webhook execution failed: {e}")
        return ExecutionResponse(
            status="error",
            error=str(e),
            details={"exception_type": type(e).__name__}
        )


@app.post("/trade/execute")
async def execute_trade(request: TradingIntent):
    """
    Direct trade execution endpoint.
    
    Alternative endpoint for structured trade requests.
    """
    global execution_adapter
    
    if execution_adapter is None:
        raise HTTPException(status_code=503, detail="Execution adapter not initialized")
    
    try:
        logger.bind(service="trading_api").info(
            f"Processing direct trade execution: {request.symbol} {request.action}"
        )
        
        # Convert TradingIntent to raw signal format
        raw_signal = {
            "decision_id": request.decision_id,
            "action": request.action,
            "symbol": request.symbol,
            "confidence": request.confidence,
            "stop_loss_price": request.stop_loss_price,
            "take_profit_price": request.take_profit_price,
            "reasoning": request.reasoning,
            "exchange": request.exchange,
            "timeframe": request.timeframe
        }
        
        # Use DEFAULT_USER_ID and a generated config_id for direct trades
        config_id = str(uuid.uuid4())
        
        # Execute via HummingbotExecutionAdapter
        result = await execution_adapter.execute_signal(
            raw_signal=raw_signal,
            user_id=DEFAULT_USER_ID,
            config_id=config_id
        )
        
        if result["status"] == "success":
            return ExecutionResponse(
                status="success",
                trade_id=result["execution_result"].get("order_id"),
                data=result,
                details="Trade executed via Hummingbot"
            )
        else:
            return ExecutionResponse(
                status="error",
                error=result.get("error", "Unknown execution error"),
                details=result
            )
            
    except Exception as e:
        logger.error(f"Direct trade execution failed: {e}")
        return ExecutionResponse(
            status="error",
            error=str(e),
            details={"exception_type": type(e).__name__}
        )


@app.get("/status")
async def get_status():
    """
    Get trading system status.
    
    Returns basic status information about the Hummingbot integration.
    """
    global execution_adapter
    
    return {
        "system": "hummingbot_trading",
        "version": "2.0.0",
        "adapter_ready": execution_adapter is not None,
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": [
            "/webhooks/execute-trade",
            "/trade/execute", 
            "/status",
            "/health"
        ]
    }


if __name__ == "__main__":
    # Development server
    import argparse
    
    parser = argparse.ArgumentParser(description="Hummingbot Trading API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    uvicorn.run(
        "trading.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )