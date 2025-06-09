"""
Decision Module API

Provides REST endpoints for generating trading decisions,
retrieving decision history, and managing the decision engine.
"""
import asyncio
import os
import uuid
import httpx
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.common.logging_config import logger
from core.common.config import DEFAULT_USER_ID
from core.common.db import get_db_connection
from decision.decision_main import run_decision_process
from core.monitoring.service import AccountMonitoringService
from trading.lifecycle_manager import TradeLifecycleManager

app = FastAPI(title="Decision API", version="1.0.0")

# In-memory storage for decision tracking (in production, use Redis or DB)
decision_cache: Dict[str, Dict] = {}


async def setup_account_monitoring(user_id: str, config_id: str) -> Optional[Dict[str, Any]]:
    """
    Initialize account monitoring and update account state before decision.
    Same logic as new_trade.py setup_monitoring().
    """
    logger.bind(user_id=user_id).info("Setting up account monitoring for decision...")
    
    try:
        # Get credentials from environment
        api_key = os.getenv('EXCHANGE_API')
        secret = os.getenv('EXCHANGE_SECRET')
        
        if not api_key or not secret:
            logger.bind(user_id=user_id).warning("Exchange credentials not found - proceeding with database-only mode")
            return None
        
        # Create monitoring service with proper parameters
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
            
            # Update account state and reconcile trades
            logger.bind(user_id=user_id).info("Updating account state from exchange...")
            result = await monitor._update_account_state()
            
            logger.bind(user_id=user_id).info("✓ Account monitoring completed")
            logger.bind(user_id=user_id).info(f"  - Position sync: {result['position_sync_performed']}")
            logger.bind(user_id=user_id).info(f"  - Trades: {result['trades_opened']} opened, {result['trades_updated']} updated, {result['trades_closed']} closed")
            
            return result
            
        finally:
            # Close exchange connection
            if hasattr(monitor, 'exchange') and monitor.exchange:
                await monitor.exchange.close()
                monitor.exchange = None
            
    except Exception as e:
        logger.bind(user_id=user_id).warning(f"Account monitoring setup failed: {e}")
        logger.bind(user_id=user_id).info("Proceeding with database-only mode")
        return None


class DecisionRequest(BaseModel):
    user_id: str = DEFAULT_USER_ID
    config_id: Optional[str] = None  # Config ID for universal trade lifecycle
    mode: str = "auto"  # "auto", "NEW_TRADE", or "MANAGE_TRADE"
    symbol: Optional[str] = None
    timeframes: Optional[List[str]] = None
    config_name: str = "default"  # Configuration name to use (legacy)


class WebhookRequest(BaseModel):
    user_id: str = DEFAULT_USER_ID
    config_id: str = "a93de31b-9b8a-42e3-827d-c31e580f5f36"  # Same UUID as new_trade.py
    symbol: Optional[str] = None
    timeframes: Optional[List[str]] = None


class DecisionResponse(BaseModel):
    decision_id: str
    mode: str
    intent: Dict[str, Any]
    reasoning: str
    created_at: str


class DecisionHistoryItem(BaseModel):
    decision_id: str
    mode: str
    intent: Dict[str, Any]
    reasoning: str
    trade_id: Optional[str] = None
    outcome: Optional[str] = None
    created_at: str


async def trigger_trading_webhook(user_id: str, intent: Dict[str, Any], decision_id: str):
    """
    Trigger Trading API after successful decision generation (Webhook pattern).
    """
    try:
        # Only trigger trading for actionable intents
        action = intent.get("action", "")
        
        if action not in ["no_action", "hold", "wait"]:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Call the trading webhook endpoint
                trading_webhook_url = os.getenv("TRADING_WEBHOOK_URL", "http://localhost:8000/trading/webhooks/execute-trade")
                response = await client.post(
                    trading_webhook_url,
                    json=intent
                )
                
                if response.status_code == 200:
                    trade_result = response.json()
                    logger.bind(user_id=user_id).info(
                        f"Successfully triggered trade execution: {trade_result.get('trade_id', 'N/A')}"
                    )
                    return trade_result
                else:
                    logger.bind(user_id=user_id).warning(
                        f"Trading webhook failed: {response.status_code} - {response.text}"
                    )
        else:
            logger.bind(user_id=user_id).info(
                f"No trading action needed for decision: {action}"
            )
                    
    except Exception as e:
        logger.bind(user_id=user_id).error(f"Trading webhook error: {str(e)}")
        # Don't fail decision if webhook fails
        return None


async def generate_decision_task(
    decision_id: str,
    user_id: str,
    mode: str,
    symbol: Optional[str],
    timeframes: Optional[List[str]]
):
    """Background task to generate trading decision."""
    try:
        # Update status
        decision_cache[decision_id]["status"] = "processing"
        
        # Determine mode automatically if set to "auto"
        actual_mode = mode
        if mode == "auto":
            # Check if user has active trades
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Note: For mode determination, we check all configs for the user
                    # since mode should be determined by any open positions
                    cur.execute("""
                        SELECT COUNT(*) FROM trades 
                        WHERE user_id = %s AND trade_status = 'open'
                    """, (user_id,))
                    active_trades = cur.fetchone()[0]
                    actual_mode = "MANAGE_TRADE" if active_trades > 0 else "NEW_TRADE"
        
        # Run decision process
        intent = await run_decision_process(
            user_id=user_id,
            symbol=symbol,
            timeframes=timeframes
        )
        
        # Extract reasoning from intent
        reasoning = intent.pop("reasoning", "No reasoning provided")
        
        # Note: strategy_runs entries are created by trading engine during execution
        # This matches new_trade.py flow where verify_strategy_runs() checks entries created by trading engine
        
        # Update cache
        decision_cache[decision_id].update({
            "status": "completed",
            "mode": actual_mode,
            "intent": intent,
            "reasoning": reasoning,
            "completed_at": datetime.utcnow().isoformat() + "Z"
        })
        
        logger.bind(
            user_id=user_id,
            decision_id=decision_id
        ).info(f"Decision generated: {actual_mode} - {intent.get('action')}")
        
    except Exception as e:
        logger.bind(
            user_id=user_id,
            decision_id=decision_id
        ).error(f"Decision generation failed: {str(e)}")
        
        decision_cache[decision_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat() + "Z"
        })


@app.post("/api/decision/analyze", response_model=DecisionResponse)
async def analyze_market(request: DecisionRequest):
    """
    Analyze market data and generate a trading decision.
    
    The mode can be:
    - "auto": Automatically determine based on active positions
    - "NEW_TRADE": Force looking for new trade opportunities
    - "MANAGE_TRADE": Force managing existing positions
    """
    decision_id = str(uuid.uuid4())
    
    try:
        # Use provided config_id or resolve from config_name
        if request.config_id:
            config_id = request.config_id
        else:
            # Fallback to config_name resolution for backward compatibility
            from decision.utils import get_config_id_by_name
            config_id = get_config_id_by_name(request.user_id, request.config_name)
            if not config_id:
                raise HTTPException(status_code=404, detail=f"Configuration '{request.config_name}' not found")
        
        # Determine mode automatically if set to "auto"
        actual_mode = request.mode
        if request.mode == "auto":
            # Check if user has active trades for this specific config
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) FROM trades 
                        WHERE user_id = %s AND config_id = %s AND trade_status = 'open'
                    """, (request.user_id, config_id))
                    active_trades = cur.fetchone()[0]
                    actual_mode = "MANAGE_TRADE" if active_trades > 0 else "NEW_TRADE"
        
        # Run decision process synchronously (like working test)
        intent = await run_decision_process(
            user_id=request.user_id,
            config_id=config_id,  # Use resolved config_id
            symbol=request.symbol or "BTC/USDT",  # Default symbol like working test
            timeframes=request.timeframes or ["15m", "1h", "4h"]  # Default timeframes like working test
        )
        
        # Extract reasoning from intent
        reasoning = intent.get("reasoning", "No reasoning provided")
        
        # Note: Audit trail is handled by trading engine in strategy_runs table
        
        # Cache the decision
        decision_cache[decision_id] = {
            "decision_id": decision_id,
            "status": "completed",
            "mode": actual_mode,
            "intent": intent,
            "reasoning": reasoning,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "user_id": request.user_id
        }
        
        logger.bind(
            user_id=request.user_id,
            decision_id=decision_id
        ).info(f"Decision generated: {actual_mode} - {intent.get('action')}")
        
        # Trigger Trading webhook after successful decision (Pipeline Pattern)  
        # Only trigger for actionable decisions, skip no_action  
        action = intent.get("action", "")
        if action != "no_action":
            await trigger_trading_webhook(request.user_id, intent, decision_id)
        
        return DecisionResponse(
            decision_id=decision_id,
            mode=actual_mode,
            intent=intent,
            reasoning=reasoning,
            created_at=decision_cache[decision_id]["created_at"]
        )
        
    except Exception as e:
        logger.bind(
            user_id=request.user_id,
            decision_id=decision_id
        ).error(f"Decision generation failed: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Decision generation failed: {str(e)}"
        )


@app.get("/api/decision/history/{user_id}")
async def get_decision_history(
    user_id: str,
    limit: int = 10,
    offset: int = 0,
    status: Optional[str] = None
):
    """Get decision history for a user."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Query account_states for decisions (temporary)
            query = """
                SELECT state_data, created_at
                FROM account_states
                WHERE user_id = %s
                  AND state_data->>'type' = 'decision'
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            
            cur.execute(query, (user_id, limit, offset))
            results = cur.fetchall()
            
            decisions = []
            for state_data, created_at in results:
                decision = DecisionHistoryItem(
                    decision_id=state_data.get("decision_id", "unknown"),
                    mode=state_data.get("mode", "unknown"),
                    intent=state_data.get("intent", {}),
                    reasoning=state_data.get("reasoning", ""),
                    trade_id=state_data.get("trade_id"),
                    outcome=state_data.get("outcome"),
                    created_at=created_at.isoformat() + "Z"
                )
                decisions.append(decision)
            
            # Get total count
            cur.execute("""
                SELECT COUNT(*)
                FROM account_states
                WHERE user_id = %s
                  AND state_data->>'type' = 'decision'
            """, (user_id,))
            total = cur.fetchone()[0]
    
    return {
        "decisions": decisions,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/api/decision/current/{user_id}")
async def get_current_decision(user_id: str):
    """Get the most recent decision for active trade management."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get latest decision
            cur.execute("""
                SELECT state_data, created_at
                FROM account_states
                WHERE user_id = %s
                  AND state_data->>'type' = 'decision'
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))
            
            result = cur.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="No decisions found")
            
            state_data, created_at = result
            
            # Get active trade info if in MANAGE_TRADE mode
            active_trade = None
            if state_data.get("mode") == "MANAGE_TRADE":
                # Note: This shows the most recent active trade across all configs for the user
                # Could be enhanced to filter by specific config if needed
                cur.execute("""
                    SELECT 
                        trade_id, symbol, entry_price, 
                        unrealized_pnl
                    FROM trades
                    WHERE user_id = %s AND trade_status = 'open'
                    ORDER BY opened_at DESC
                    LIMIT 1
                """, (user_id,))
                
                trade_result = cur.fetchone()
                if trade_result:
                    trade_id, symbol, entry_price, pnl = trade_result
                    active_trade = {
                        "trade_id": str(trade_id),
                        "symbol": symbol,
                        "entry_price": float(entry_price) if entry_price else None,
                        "current_price": None,  # Current price can be fetched from mark_price if needed
                        "unrealized_pnl": float(pnl) if pnl else 0
                    }
    
    return {
        "decision_id": state_data.get("decision_id", "unknown"),
        "mode": state_data.get("mode", "unknown"),
        "original_reasoning": state_data.get("reasoning", ""),
        "current_analysis": state_data.get("intent", {}).get("analysis", ""),
        "active_trade": active_trade,
        "created_at": created_at.isoformat() + "Z"
    }


@app.get("/api/decision/status/{decision_id}")
async def get_decision_status(decision_id: str):
    """Get the status of a decision generation request."""
    if decision_id not in decision_cache:
        raise HTTPException(status_code=404, detail="Decision ID not found")
    
    return decision_cache[decision_id]


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "decision-api",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# Cleanup old decision cache periodically
async def cleanup_old_decisions():
    """Remove decision cache older than 1 hour."""
    while True:
        await asyncio.sleep(3600)  # Run every hour
        cutoff = datetime.utcnow() - timedelta(hours=1)
        
        to_remove = []
        for decision_id, data in decision_cache.items():
            created_at = datetime.fromisoformat(data["created_at"].rstrip("Z"))
            if created_at < cutoff:
                to_remove.append(decision_id)
        
        for decision_id in to_remove:
            del decision_cache[decision_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old decision cache entries")


@app.on_event("startup")
async def startup_event():
    """Start background cleanup task."""
    asyncio.create_task(cleanup_old_decisions())


@app.post("/webhooks/trigger-decision")
async def webhook_trigger_decision(request: WebhookRequest):
    """
    Webhook endpoint to trigger decision analysis.
    
    This endpoint implements the full decision logic from new_trade.py including:
    - Fresh account monitoring and position sync
    - Automatic mode detection (NEW_TRADE vs MANAGE_TRADE)
    - Proper config_id handling
    """
    try:
        logger.bind(user_id=request.user_id).info(
            f"🧠 Decision webhook triggered for config {request.config_id}"
        )
        
        # Step 1: Setup account monitoring to get fresh data (like new_trade.py)
        monitoring_result = await setup_account_monitoring(request.user_id, request.config_id)
        if monitoring_result:
            logger.bind(user_id=request.user_id).info("Account state refreshed from exchange")
        else:
            logger.bind(user_id=request.user_id).info("Using database-only mode for decision")
        
        # Step 2: Determine mode automatically with fresh data (like new_trade.py)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM trades 
                    WHERE user_id = %s AND config_id = %s AND trade_status = 'open'
                """, (request.user_id, request.config_id))
                active_trades = cur.fetchone()[0]
                actual_mode = "MANAGE_TRADE" if active_trades > 0 else "NEW_TRADE"
        
        logger.bind(user_id=request.user_id).info(
            f"🎯 Mode detected: {actual_mode} (found {active_trades} active trades for config {request.config_id})"
        )
        
        # Step 3: Run decision process using the webhook config_id (like new_trade.py)
        intent = await run_decision_process(
            user_id=request.user_id,
            config_id=request.config_id,
            symbol=request.symbol or "BTC/USDT",
            timeframes=request.timeframes or ["15m", "1h", "4h"]
        )
        
        # Generate decision ID for tracking
        decision_id = str(uuid.uuid4())
        reasoning = intent.get("reasoning", "No reasoning provided")
        
        logger.bind(user_id=request.user_id).info(
            f"✅ Decision completed: {intent.get('action')} (confidence: {intent.get('confidence', 'N/A')})"
        )
        
        # Note: strategy_runs entries are created by trading engine during execution (like new_trade.py)
        # This ensures trade_id is available and creates proper audit trail
        
        # Note: Audit trail will be created by trading engine in strategy_runs table
        logger.bind(user_id=request.user_id).info(f"💭 Decision completed, audit trail will be created during trade execution")
        
        # Rate limiting delay before triggering trading (coordination)
        await asyncio.sleep(1)
        
        # Step 4: Trigger trading webhook if actionable (same logic as API endpoint)
        action = intent.get("action", "")
        if action not in ["no_action", "hold", "wait"]:
            logger.bind(user_id=request.user_id).info(f"🚀 Triggering trading webhook for action: {action}")
            await trigger_trading_webhook(request.user_id, intent, decision_id)
        else:
            logger.bind(user_id=request.user_id).info(f"ℹ️ No trading action needed: {action}")
        
        return {
            "status": "completed",
            "decision_id": decision_id,
            "mode": actual_mode,
            "action": intent.get("action"),
            "confidence": intent.get("confidence"),
            "message": f"Decision generated via webhook ({actual_mode} mode)",
            "user_id": request.user_id,
            "config_id": request.config_id,
            "monitoring_performed": monitoring_result is not None
        }
        
    except Exception as e:
        logger.bind(user_id=request.user_id).error(
            f"❌ Webhook decision failed: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Decision webhook failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.environ.get("DECISION_API_PORT", "5002"))
    host = os.environ.get("DECISION_API_HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port)