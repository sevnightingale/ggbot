"""
Extraction Module API

Provides REST endpoints for triggering market data extraction,
checking extraction status, and retrieving extracted data.
"""
import asyncio
import os
import uuid
import httpx
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from core.common.logging_config import logger
from core.common.config import DEFAULT_USER_ID
from core.common.db import get_db_connection
from extraction.extraction_main import ExtractionManager

app = FastAPI(title="Extraction API", version="1.0.0")

# In-memory storage for extraction status (in production, use Redis or DB)
extraction_status: Dict[str, Dict] = {}


class ExtractionRequest(BaseModel):
    user_id: str = DEFAULT_USER_ID
    symbols: Optional[List[str]] = None
    timeframes: Optional[List[str]] = None
    config_id: Optional[str] = "default"
    custom_mode: Optional[str] = None


class ExtractionResponse(BaseModel):
    status: str
    extraction_id: str
    message: str


class ExtractionStatusResponse(BaseModel):
    extraction_id: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    data_points_extracted: int = 0
    errors: List[str] = []


class MarketDataRequest(BaseModel):
    symbol: str
    timeframe: str
    data_type: str = "indicator_values"


class WebhookRequest(BaseModel):
    user_id: str = DEFAULT_USER_ID
    config_id: Optional[str] = "default"  # Use "default" or specific config_id
    symbols: Optional[List[str]] = None
    timeframes: Optional[List[str]] = None
    triggered_by: Optional[str] = None
    custom_mode: Optional[str] = None


async def trigger_decision_webhook(user_id: str, symbols: List[str], timeframes: List[str], config_id: str = "default", custom_mode: Optional[str] = None):
    """
    Trigger Decision API after successful extraction (Webhook pattern).
    """
    try:
        # Call Decision webhook to analyze the freshly extracted data
        async with httpx.AsyncClient(timeout=60.0) as client:
            webhook_payload = {
                "user_id": user_id,
                "config_id": config_id,  # Pass through the extraction config_id
                "symbol": symbols[0] if symbols else "BTC/USDT",
                "timeframes": timeframes
            }
            
            # Add custom_mode if provided (for ggShot signal validation)
            if custom_mode:
                webhook_payload["custom_mode"] = custom_mode
            
            # Call the decision webhook endpoint
            decision_webhook_url = os.getenv("DECISION_WEBHOOK_URL", "http://localhost:8000/decision/webhooks/trigger-decision")
            response = await client.post(
                decision_webhook_url,
                json=webhook_payload
            )
            
            if response.status_code == 200:
                decision_result = response.json()
                logger.bind(user_id=user_id).info(
                    f"Successfully triggered decision analysis: {decision_result['decision_id']}"
                )
                return decision_result
            else:
                logger.bind(user_id=user_id).warning(
                    f"Decision webhook failed: {response.status_code} - {response.text}"
                )
                
    except Exception as e:
        logger.bind(user_id=user_id).error(f"Decision webhook error: {str(e)}")
        # Don't fail extraction if webhook fails
        return None


async def setup_pre_extraction_monitoring(user_id: str, config_id: str) -> Optional[Dict[str, Any]]:
    """
    Setup account monitoring before extraction (like new_trade.py setup_monitoring).
    Ensures fresh account state before data extraction.
    """
    logger.bind(user_id=user_id).info("Setting up pre-extraction account monitoring...")
    
    try:
        # Get credentials from environment
        api_key = os.getenv('EXCHANGE_API')
        secret = os.getenv('EXCHANGE_SECRET')
        
        if not api_key or not secret:
            logger.bind(user_id=user_id).warning("Exchange credentials not found - proceeding without pre-extraction monitoring")
            return None
        
        # Import monitoring service
        from core.monitoring.service import AccountMonitoringService
        
        credentials = {
            'apiKey': api_key,
            'secret': secret
        }
        
        monitor = AccountMonitoringService(
            user_id=user_id,
            config_id=config_id,
            exchange_name="bitmex",
            credentials=credentials,
            testnet=True
        )
        
        # Create exchange client and update account state
        try:
            monitor.exchange = await monitor._create_exchange_client()
            
            logger.bind(user_id=user_id).info("Updating account state before extraction...")
            result = await monitor._update_account_state()
            
            logger.bind(user_id=user_id).info("✓ Pre-extraction monitoring completed")
            logger.bind(user_id=user_id).info(f"  - Position sync: {result['position_sync_performed']}")
            
            return result
            
        finally:
            # Close exchange connection
            if hasattr(monitor, 'exchange') and monitor.exchange:
                await monitor.exchange.close()
                monitor.exchange = None
            
    except Exception as e:
        logger.bind(user_id=user_id).warning(f"Pre-extraction monitoring failed: {e}")
        logger.bind(user_id=user_id).info("Proceeding with extraction anyway")
        return None


async def run_extraction_task(extraction_id: str, user_id: str, symbols: Optional[List[str]], timeframes: Optional[List[str]], config_id: Optional[str] = "default", custom_mode: Optional[str] = None):
    """Background task to run extraction."""
    try:
        # Update status to running
        extraction_status[extraction_id]["status"] = "running"
        
        # Setup pre-extraction monitoring (like new_trade.py setup_monitoring)
        monitoring_result = await setup_pre_extraction_monitoring(user_id, config_id)
        if monitoring_result:
            logger.bind(user_id=user_id).info("Account state refreshed before extraction")
        else:
            logger.bind(user_id=user_id).info("Proceeding with extraction without fresh monitoring")
        
        # Use the direct function like the working test
        from extraction.extraction_main import extract_mcp_indicators
        
        # Handle symbol/timeframe selection based on mode
        if custom_mode == 'ggshot':
            # For ggShot mode, ALWAYS use the symbols/timeframes from the webhook (ggShot signals)
            # Never fall back to config for ggShot signals
            if not symbols or not timeframes:
                raise ValueError("ggShot mode requires explicit symbols and timeframes from signal")
            logger.bind(user_id=user_id).info(f"ggShot mode: Using dynamic symbols={symbols}, timeframes={timeframes}")
        else:
            # Standard mode: Use provided symbols/timeframes or get from config
            if not symbols or not timeframes:
                from core.config.config_main import get_configuration
                if config_id:
                    # Use specific config_id
                    user_config = get_configuration(user_id=user_id, config_id=config_id) or {}
                    extraction_config = user_config.get('extraction', {})
                else:
                    # Fallback to legacy method
                    extraction_config = get_configuration(user_id, 'extraction') or {}
                symbols = symbols or extraction_config.get('symbols', ['BTC/USDT'])
                timeframes = timeframes or extraction_config.get('timeframes', ['15m', '1h'])
                logger.bind(user_id=user_id).info(f"Standard mode: Using symbols={symbols}, timeframes={timeframes}")
        
        # Run extraction using the same function as working test
        results = await extract_mcp_indicators(
            symbols=symbols,
            timeframes=timeframes,
            user_id=user_id,
            use_llm=True,
            llm_model="gpt-4o-mini",
            config_id=config_id
        )
        
        # Count data points from extract_mcp_indicators structure
        data_points = 0
        if isinstance(results, dict) and "error" not in results:
            for symbol, symbol_results in results.items():
                if isinstance(symbol_results, dict):
                    for timeframe, timeframe_result in symbol_results.items():
                        if isinstance(timeframe_result, dict) and timeframe_result.get('status') == 'success':
                            data_points += 1
        
        # Update status to completed
        extraction_status[extraction_id].update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "data_points_extracted": data_points
        })
        
        logger.bind(
            user_id=user_id,
            extraction_id=extraction_id
        ).info(f"Extraction completed with {data_points} data points")
        
        # Trigger Decision webhook immediately after successful extraction (Pipeline Pattern)
        if data_points > 0:
            logger.bind(user_id=user_id).info("⏱️ Triggering decision webhook after extraction...")
            await trigger_decision_webhook(user_id, symbols, timeframes, config_id, custom_mode)
        else:
            logger.bind(user_id=user_id).warning("No data extracted, skipping decision webhook")
        
    except Exception as e:
        logger.bind(
            user_id=user_id,
            extraction_id=extraction_id
        ).error(f"Extraction failed: {str(e)}")
        
        extraction_status[extraction_id].update({
            "status": "failed",
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "errors": [str(e)]
        })


@app.post("/api/extraction/run", response_model=ExtractionResponse)
async def trigger_extraction(request: ExtractionRequest, background_tasks: BackgroundTasks):
    """
    Trigger market data extraction for specified symbols and timeframes.
    
    If symbols/timeframes are not provided, uses the user's configuration.
    """
    extraction_id = str(uuid.uuid4())
    
    # Initialize status tracking
    extraction_status[extraction_id] = {
        "extraction_id": extraction_id,
        "status": "pending",
        "started_at": datetime.utcnow().isoformat() + "Z",
        "completed_at": None,
        "data_points_extracted": 0,
        "errors": []
    }
    
    # Add background task
    background_tasks.add_task(
        run_extraction_task,
        extraction_id,
        request.user_id,
        request.symbols,
        request.timeframes,
        request.config_id,
        request.custom_mode
    )
    
    # Calculate expected data points
    symbols_count = len(request.symbols) if request.symbols else 2  # Default from config
    timeframes_count = len(request.timeframes) if request.timeframes else 2  # Default from config
    
    return ExtractionResponse(
        status="started",
        extraction_id=extraction_id,
        message=f"Extraction started for {symbols_count} symbols across {timeframes_count} timeframes"
    )


@app.get("/api/extraction/status/{extraction_id}", response_model=ExtractionStatusResponse)
async def get_extraction_status(extraction_id: str):
    """Get the status of an extraction job."""
    if extraction_id not in extraction_status:
        raise HTTPException(status_code=404, detail="Extraction ID not found")
    
    return ExtractionStatusResponse(**extraction_status[extraction_id])


@app.get("/api/extraction/latest/{user_id}")
async def get_latest_market_data(
    user_id: str,
    symbol: str,
    timeframe: str,
    data_type: str = "indicator_values"
):
    """
    Get the latest market data for a specific symbol and timeframe.
    
    Args:
        user_id: User ID
        symbol: Trading symbol (e.g., "BTC/USDT")
        timeframe: Timeframe (e.g., "15m", "1h")
        data_type: Type of data ("indicator_values" or "indicator_analysis")
    """
    # Get database connection
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Query for latest data
            cur.execute("""
                SELECT raw_data, updated_at
                FROM market_data
                WHERE user_id = %s
                  AND symbol = %s
                  AND timeframe = %s
                  AND data_type = %s
                  AND updated_at > %s
                ORDER BY updated_at DESC
                LIMIT 1
            """, (
                user_id,
                symbol,
                timeframe,
                data_type,
                datetime.utcnow() - timedelta(hours=24)  # Only last 24 hours
            ))
            
            result = cur.fetchone()
            
            if not result:
                raise HTTPException(
                    status_code=404,
                    detail=f"No recent data found for {symbol} {timeframe}"
                )
            
            raw_data, updated_at = result
            
            # Parse the data based on type
            if data_type == "indicator_values":
                # Return raw indicator data
                return {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "data": raw_data.get("indicators", {}),
                    "created_at": updated_at.isoformat() + "Z"
                }
            else:
                # Return analysis text including interpretation  
                return {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "data": {
                        "indicators": raw_data.get("indicators", {}),
                        "interpretation": raw_data.get("interpretation", {})
                    },
                    "analysis": raw_data.get("interpretation", {}).get("analysis", ""),
                    "created_at": updated_at.isoformat() + "Z"
                }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "extraction-api",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# Cleanup old extraction status periodically
async def cleanup_old_status():
    """Remove extraction status older than 1 hour."""
    while True:
        await asyncio.sleep(3600)  # Run every hour
        cutoff = datetime.utcnow() - timedelta(hours=1)
        
        to_remove = []
        for extraction_id, status in extraction_status.items():
            started_at = datetime.fromisoformat(status["started_at"].rstrip("Z"))
            if started_at < cutoff:
                to_remove.append(extraction_id)
        
        for extraction_id in to_remove:
            del extraction_status[extraction_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old extraction statuses")


@app.on_event("startup")
async def startup_event():
    """Start background cleanup task."""
    asyncio.create_task(cleanup_old_status())


@app.post("/webhooks/trigger-extraction")
async def webhook_trigger_extraction(request: WebhookRequest, background_tasks: BackgroundTasks):
    """
    Webhook endpoint to trigger extraction.
    
    This endpoint accepts a standard webhook payload and triggers market data extraction.
    Returns immediately with status while processing happens in background.
    """
    extraction_id = str(uuid.uuid4())
    
    # Initialize status tracking
    extraction_status[extraction_id] = {
        "extraction_id": extraction_id,
        "status": "pending",
        "started_at": datetime.utcnow().isoformat() + "Z",
        "completed_at": None,
        "data_points_extracted": 0,
        "errors": []
    }
    
    # Add background task
    background_tasks.add_task(
        run_extraction_task,
        extraction_id,
        request.user_id,
        request.symbols,
        request.timeframes,
        request.config_id,  # Use the webhook config_id
        request.custom_mode  # Pass through custom_mode for ggShot signals
    )
    
    logger.bind(user_id=request.user_id).info(
        f"Webhook triggered extraction for config {request.config_id}"
    )
    
    return {
        "status": "triggered",
        "extraction_id": extraction_id,
        "message": "Extraction triggered via webhook",
        "user_id": request.user_id,
        "config_id": request.config_id
    }


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.environ.get("EXTRACTION_API_PORT", "5001"))
    host = os.environ.get("EXTRACTION_API_HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port)