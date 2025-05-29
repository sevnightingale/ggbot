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

from core.common.logger import logger
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


async def trigger_decision_webhook(user_id: str, symbols: List[str], timeframes: List[str]):
    """
    Trigger Decision API after successful extraction (Webhook pattern).
    """
    try:
        # Call Decision API to analyze the freshly extracted data
        async with httpx.AsyncClient(timeout=60.0) as client:
            decision_payload = {
                "user_id": user_id,
                "mode": "auto",  # Let decision module determine if NEW_TRADE or MANAGE_TRADE
                "symbol": symbols[0] if symbols else None,
                "timeframes": timeframes
            }
            
            # Call the combined API endpoint
            api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
            response = await client.post(
                f"{api_base}/decision/api/decision/analyze",
                json=decision_payload
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


async def run_extraction_task(extraction_id: str, user_id: str, symbols: Optional[List[str]], timeframes: Optional[List[str]]):
    """Background task to run extraction."""
    try:
        # Update status to running
        extraction_status[extraction_id]["status"] = "running"
        
        # Use the direct function like the working test
        from extraction.extraction_main import extract_mcp_indicators
        
        # Use provided symbols/timeframes or get from config
        if not symbols or not timeframes:
            from core.config.config_main import get_configuration
            extraction_config = get_configuration(user_id, 'extraction') or {}
            symbols = symbols or extraction_config.get('symbols', ['BTC/USDT'])
            timeframes = timeframes or extraction_config.get('timeframes', ['15m', '1h'])
        
        # Run extraction using the same function as working test
        results = await extract_mcp_indicators(
            symbols=symbols,
            timeframes=timeframes,
            user_id=user_id,
            use_llm=True,
            llm_model="gpt-4o-mini"
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
        
        # Trigger Decision webhook after successful extraction (Pipeline Pattern)
        # TEMPORARILY DISABLED for testing
        # if data_points > 0:
        #     await trigger_decision_webhook(user_id, symbols, timeframes)
        
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
        request.timeframes
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


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.environ.get("EXTRACTION_API_PORT", "5001"))
    host = os.environ.get("EXTRACTION_API_HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port)