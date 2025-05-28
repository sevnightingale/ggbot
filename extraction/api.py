"""
Extraction Module API

Provides REST endpoints for triggering market data extraction,
checking extraction status, and retrieving extracted data.
"""
import asyncio
import os
import uuid
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


async def run_extraction_task(extraction_id: str, user_id: str, symbols: Optional[List[str]], timeframes: Optional[List[str]]):
    """Background task to run extraction."""
    try:
        # Update status to running
        extraction_status[extraction_id]["status"] = "running"
        
        # Create and run extraction manager
        manager = ExtractionManager(user_id=user_id)
        
        # Override config if symbols/timeframes provided
        if symbols:
            manager.symbols = symbols
        if timeframes:
            manager.timeframes = timeframes
            
        # Run extraction
        results = await manager.run()
        
        # Count data points
        data_points = sum(len(source_results) for source_results in results.values())
        
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
                SELECT data, created_at
                FROM market_data
                WHERE user_id = %s
                  AND symbol = %s
                  AND timeframe = %s
                  AND data_type = %s
                  AND created_at > %s
                ORDER BY created_at DESC
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
            
            data, created_at = result
            
            # Parse the data based on type
            if data_type == "indicator_values":
                # Return raw indicator data
                return {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "data": data,
                    "created_at": created_at.isoformat() + "Z"
                }
            else:
                # Return analysis text
                return {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "analysis": data.get("analysis", ""),
                    "created_at": created_at.isoformat() + "Z"
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