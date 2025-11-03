"""
Agent API Endpoints

Provides thin API wrappers for autonomous trading agents to orchestrate trading operations.
Agents control the trading flow by calling individual components (extraction, execution, etc.)

Architecture:
- Agent orchestrates via these endpoints (doesn't call main orchestrator)
- Endpoints are thin wrappers around existing services
- No config pollution - dynamic params are in-memory only
- Works with both paper and live trading
"""

import os
import json
import time
import subprocess
import redis
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
from fastapi import APIRouter, HTTPException, Header, Query, Body, Depends
from pydantic import BaseModel
from dotenv import load_dotenv

from core.common.logger import logger
from core.auth.supabase_auth import AuthenticatedUser, get_current_user_v2
from core.config.config_main import get_configuration
from core.common.db import get_db_connection
from core.symbols.standardizer import UniversalSymbolStandardizer
from trading.paper.supabase_service import SupabasePaperTradingService
from extraction.v2.extraction_engine import ExtractionEngineV2

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/api/v2/agent", tags=["agent"])

# Redis client for agent message queue
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)


# ============================================================================
# SIMPLIFIED SERVICE AUTHENTICATION
# ============================================================================

def validate_agent_service_auth(
    authorization: Optional[str],
    x_service_auth: Optional[str]
) -> None:
    """
    Simple synchronous service authentication for agent endpoints.
    Raises HTTPException if validation fails.
    """
    # Check service header
    if x_service_auth != 'agent-runner':
        logger.error(f"Invalid service header: {x_service_auth}")
        raise HTTPException(status_code=401, detail="Invalid service authentication")

    # Check authorization header
    if not authorization or not authorization.startswith('Bearer '):
        logger.error("Missing or invalid authorization header")
        raise HTTPException(status_code=401, detail="Missing authorization token")

    # Validate service key
    token = authorization.replace('Bearer ', '')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not service_key or token != service_key:
        logger.error("Service token mismatch")
        raise HTTPException(status_code=401, detail="Invalid service token")

    # Success - no return value needed
    logger.debug("Agent service authenticated successfully")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class QueryMarketDataRequest(BaseModel):
    """Request for querying market data (technical + intelligence)"""
    config_id: str
    symbol: str
    indicators: Optional[List[str]] = None  # Technical indicators override
    data_sources: Optional[Dict[str, List[str]]] = None  # Market intelligence override
    timeframe: str = "1h"


class ExecuteTradeRequest(BaseModel):
    """Request for executing a trade directly"""
    config_id: str
    symbol: str
    side: str  # "long" or "short"
    confidence: float = 0.7
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    decision_id: Optional[str] = None


class UpdateStrategyRequest(BaseModel):
    """Request for updating agent strategy"""
    strategy_content: str
    updated_by: str = "agent"  # "agent" or "user"


class RecordTradeObservationRequest(BaseModel):
    """Request for recording post-trade reflection"""
    config_id: str
    trade_id: str
    observation_type: str  # "win_analysis" or "loss_analysis"
    what_went_well: Optional[str] = None
    what_went_wrong: Optional[str] = None
    predictive_data_points: Optional[Dict[str, str]] = None  # {"vix": "low volatility helped"}
    decision_review: Optional[str] = None
    importance: int = 5  # 1-10


class QueryTradeObservationsRequest(BaseModel):
    """Request for querying trade observations"""
    config_id: str
    symbol: Optional[str] = None
    observation_type: Optional[str] = None  # "win_analysis" or "loss_analysis"
    min_importance: Optional[int] = None
    limit: int = 10


# ============================================================================
# 1. QUERY MARKET DATA (Unified: Technical + Intelligence)
# ============================================================================

@router.post("/query-market-data")
async def query_market_data(
    request_body: QueryMarketDataRequest,
    user_id: str = Query(...),
    authorization: str = Header(None),
    x_service_auth: str = Header(None, alias="x-service-auth")
) -> Dict[str, Any]:
    """
    Query market data with optional dynamic overrides.

    If no indicators/data_sources provided, uses config defaults.
    Dynamic params are in-memory only (config not modified).

    Examples:
    - Technical only: {"symbol": "BTCUSDT", "indicators": ["RSI"]}
    - Intelligence only: {"symbol": "BTCUSDT", "data_sources": {"macro_economics": ["vix"]}}
    - Both: Provide both indicators and data_sources
    - Config defaults: Just provide symbol (no overrides)
    """
    validate_agent_service_auth(authorization, x_service_auth)

    try:
        config = get_configuration(user_id=user_id, config_id=request_body.config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Normalize symbol to CCXT format (BTC/USDT) using UniversalSymbolStandardizer
        # ExtractionEngineV2 expects CCXT format internally
        standardizer = UniversalSymbolStandardizer()
        symbol = request_body.symbol

        if symbol:
            # Detect format and normalize to CCXT format
            if '/' in symbol:
                # Already in CCXT format like "BTC/USDT"
                normalized = symbol
            elif 'USDT' in symbol or 'USD' in symbol:
                # Has pair like "BTCUSDT" or "BTC-USDT" - normalize to CCXT
                # Try platform first, then ggshot
                normalized = standardizer.to_ccxt(symbol)
                if not normalized:
                    # Try ggshot format (BTCUSDT)
                    normalized = standardizer.normalize(symbol, "ggshot", "ccxt")
                if not normalized:
                    # Fallback: manually add separator
                    base = symbol.replace('USDT', '').replace('USD', '').replace('-', '')
                    normalized = f"{base}/USDT"
            else:
                # Simple symbol like "BTC" - convert symphony → platform → ccxt
                platform_format = standardizer.from_symphony(symbol)
                if platform_format:
                    normalized = standardizer.to_ccxt(platform_format)
                else:
                    # Fallback: manually construct CCXT format
                    normalized = f"{symbol.upper()}/USDT"

            symbol = normalized
            logger.debug(f"Normalized symbol: {request_body.symbol} -> {symbol} (CCXT format)")

        result = {}

        # Query technical indicators
        if request_body.indicators or not request_body.data_sources:
            extraction_engine = ExtractionEngineV2(user_id=user_id)

            # Use override or config defaults
            indicators = request_body.indicators or config.get('extraction', {}).get('indicators', ['RSI'])

            # Normalize indicator names to UPPERCASE
            indicators = [ind.upper() for ind in indicators]

            tech_result = await extraction_engine.extract_for_symbol(
                symbol=symbol,  # Use normalized symbol
                indicators=indicators,
                timeframe=request_body.timeframe,
                config_id=request_body.config_id
            )

            # Convert numpy/pandas objects to JSON-serializable format
            import numpy as np
            import pandas as pd

            def make_serializable(obj):
                """Recursively convert numpy/pandas objects to JSON-serializable types"""
                if isinstance(obj, (np.integer, np.floating)):
                    return float(obj)
                elif isinstance(obj, np.bool_):
                    return bool(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, pd.Series):
                    return obj.to_dict()
                elif isinstance(obj, pd.DataFrame):
                    return obj.to_dict(orient='records')
                elif isinstance(obj, dict):
                    return {k: make_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [make_serializable(item) for item in obj]
                else:
                    return obj

            result['technicals'] = make_serializable(tech_result)

        # Query market intelligence
        if request_body.data_sources or not request_body.indicators:
            try:
                from market_intelligence.orchestrator import fetch_market_intelligence

                intel_result = await fetch_market_intelligence(
                    config=config,
                    user_id=user_id,
                    symbol=symbol,  # Use normalized symbol
                    data_points_override=request_body.data_sources  # Dynamic override
                )
                result['market_intelligence'] = intel_result
            except ImportError:
                logger.warning("Market intelligence orchestrator not available yet")
                result['market_intelligence'] = {"status": "not_available"}
            except TypeError as e:
                # Orchestrator doesn't support data_points_override yet
                logger.warning(f"Orchestrator modification pending: {e}")
                result['market_intelligence'] = {"status": "pending_modification"}

        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Market data query failed: {e}", user_id=user_id)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}", user_id=user_id)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 1B. GET CURRENT PRICE (Lightweight price check)
# ============================================================================

@router.get("/current-price/{symbol}")
async def get_current_price(
    symbol: str,
    user_id: str = Query(...),
    authorization: str = Header(None),
    x_service_auth: str = Header(None, alias="x-service-auth")
) -> Dict[str, Any]:
    """
    Get current price for a symbol (lightweight, fast).

    Uses WebSocket cache for 100 symbols (sub-ms), falls back to REST API.
    Returns just the current price without indicators - useful for quick
    price checks before executing trades.

    Example: GET /api/v2/agent/current-price/BTCUSDT
    """
    validate_agent_service_auth(authorization, x_service_auth)

    try:
        from trading.paper.hybrid_price_service import HybridPriceService

        # Normalize symbol to CCXT format (same logic as query_market_data)
        standardizer = UniversalSymbolStandardizer()

        if '/' in symbol:
            # Already in CCXT format
            internal_symbol = symbol
        elif 'USDT' in symbol or 'USD' in symbol:
            # Has pair - normalize to CCXT
            internal_symbol = standardizer.to_ccxt(symbol)
            if not internal_symbol:
                internal_symbol = standardizer.normalize(symbol, "ggshot", "ccxt")
            if not internal_symbol:
                # Fallback
                base = symbol.replace('USDT', '').replace('USD', '').replace('-', '')
                internal_symbol = f"{base}/USDT"
        else:
            # Simple symbol - convert via standardizer
            platform_format = standardizer.from_symphony(symbol)
            if platform_format:
                internal_symbol = standardizer.to_ccxt(platform_format)
            else:
                internal_symbol = f"{symbol.upper()}/USDT"

        logger.debug(f"Normalized symbol for price: {symbol} -> {internal_symbol} (CCXT format)")

        # Get price from hybrid service (WebSocket first, REST fallback)
        price_service = HybridPriceService()
        try:
            market_price = await price_service.get_current_price(internal_symbol)

            return {
                "status": "success",
                "symbol": symbol,
                "current_price": market_price.mid,
                "bid": market_price.bid,
                "ask": market_price.ask,
                "spread_percent": ((market_price.ask - market_price.bid) / market_price.mid) * 100,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "websocket_cache" if price_service.stats["websocket_hits"] > 0 else "binance_rest"
            }

        finally:
            # Cleanup
            if price_service.redis_client:
                await price_service.redis_client.aclose()
            if price_service.binance_client:
                await price_service.binance_client.close_connection()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current price for {symbol}: {e}", user_id=user_id)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 2. EXECUTE TRADE (Direct execution, agent already decided)
# ============================================================================

@router.post("/execute-trade")
async def execute_trade(
    request: ExecuteTradeRequest,
    user_id: str = Query(...),
    authorization: str = Header(None),
    x_service_auth: str = Header(None, alias="x-service-auth")
) -> Dict[str, Any]:
    """
    Execute trade directly (agent has already made the decision).
    No extraction or decision logic - just execute the trade.
    """
    validate_agent_service_auth(authorization, x_service_auth)

    try:
        # Verify config exists
        config = get_configuration(user_id=user_id, config_id=request.config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Build trade intent
        intent = {
            "config_id": request.config_id,
            "user_id": user_id,
            "symbol": request.symbol,
            "action": request.side,  # "long" or "short"
            "confidence": request.confidence,
            "stop_loss_price": request.stop_loss_price,
            "take_profit_price": request.take_profit_price,
            "decision_id": request.decision_id
        }

        # Execute via paper trading service
        # TODO: Add live trading support when config.trading_mode == "live"
        paper_trading = SupabasePaperTradingService()
        result = await paper_trading.execute_trade_intent(intent)

        logger.info(
            f"Agent executed trade: {request.symbol} {request.side}",
            user_id=user_id,
            config_id=request.config_id
        )

        return {
            "status": "success",
            "trade": result,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Trade execution failed: {e}", user_id=user_id)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 3. GET POSITIONS (Works for paper and live)
# ============================================================================

@router.get("/positions/{config_id}")
async def get_positions(
    config_id: str,
    user_id: str = Query(...),
    authorization: str = Header(None),
    x_service_auth: str = Header(None, alias="x-service-auth")
) -> Dict[str, Any]:
    """
    Get open positions for config (paper or live).
    """
    validate_agent_service_auth(authorization, x_service_auth)

    try:
        config = get_configuration(user_id=user_id, config_id=config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        trading_mode = config.get('trading_mode', 'paper')

        if trading_mode == 'paper':
            paper_trading = SupabasePaperTradingService()
            positions = await paper_trading.get_open_positions(config_id)
        else:
            # TODO: Live trading positions via Symphony
            raise HTTPException(status_code=501, detail="Live trading positions not implemented yet")

        return {
            "status": "success",
            "positions": positions,
            "trading_mode": trading_mode,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Get positions failed: {e}", user_id=user_id)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 4. GET ACCOUNT STATUS
# ============================================================================

@router.get("/account/{config_id}")
async def get_account_status(
    config_id: str,
    user_id: str = Query(...),
    authorization: str = Header(None),
    x_service_auth: str = Header(None, alias="x-service-auth")
) -> Dict[str, Any]:
    """
    Get account summary with performance metrics.
    """
    validate_agent_service_auth(authorization, x_service_auth)

    try:
        config = get_configuration(user_id=user_id, config_id=config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        trading_mode = config.get('trading_mode', 'paper')

        if trading_mode == 'paper':
            paper_trading = SupabasePaperTradingService()
            account = await paper_trading.get_account_summary(config_id)
        else:
            # TODO: Live account via Symphony
            raise HTTPException(status_code=501, detail="Live account status not implemented yet")

        return {
            "status": "success",
            "account": account,
            "trading_mode": trading_mode,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Get account failed: {e}", user_id=user_id)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 5. CLOSE POSITION
# ============================================================================

@router.post("/positions/{trade_id}/close")
async def close_position(
    trade_id: str,
    config_id: str = Body(..., embed=True),
    user_id: str = Query(...),
    authorization: str = Header(None),
    x_service_auth: str = Header(None, alias="x-service-auth")
) -> Dict[str, Any]:
    """
    Close an open position.
    """
    validate_agent_service_auth(authorization, x_service_auth)

    try:
        config = get_configuration(user_id=user_id, config_id=config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        trading_mode = config.get('trading_mode', 'paper')

        if trading_mode == 'paper':
            paper_trading = SupabasePaperTradingService()
            result = await paper_trading.close_position(trade_id=trade_id)
        else:
            # TODO: Close live position via Symphony
            raise HTTPException(status_code=501, detail="Live position closing not implemented yet")

        logger.info(
            f"Agent closed position: {trade_id}",
            user_id=user_id,
            config_id=config_id
        )

        return {
            "status": "success",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Close position failed: {e}", user_id=user_id)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 6. UPDATE STRATEGY (Agent modifies its own strategy)
# ============================================================================

@router.patch("/config/{config_id}/strategy")
async def update_strategy(
    config_id: str,
    request: UpdateStrategyRequest,
    user_id: str = Query(...),
    authorization: str = Header(None),
    x_service_auth: str = Header(None, alias="x-service-auth")
) -> Dict[str, Any]:
    """
    Update agent strategy in config.

    Only allowed if autonomously_editable=true OR updated_by="user".
    Increments version number and logs performance.
    """
    validate_agent_service_auth(authorization, x_service_auth)

    try:
        config = get_configuration(user_id=user_id, config_id=config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Check if agent is allowed to modify strategy
        agent_strategy = config.get('config_data', {}).get('agent_strategy', {})
        autonomously_editable = agent_strategy.get('autonomously_editable', False)

        if not autonomously_editable and request.updated_by == "agent":
            raise HTTPException(
                status_code=403,
                detail="Agent cannot modify strategy (autonomously_editable=false)"
            )

        # Update strategy with version increment
        current_version = agent_strategy.get('version', 0)
        new_strategy = {
            "content": request.strategy_content,
            "autonomously_editable": autonomously_editable,
            "version": current_version + 1,
            "last_updated_at": datetime.utcnow().isoformat(),
            "last_updated_by": request.updated_by,
            "performance_log": agent_strategy.get('performance_log', [])
        }

        # Update config in database
        config['config_data']['agent_strategy'] = new_strategy

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE configurations
                    SET config_data = %s,
                        updated_at = NOW()
                    WHERE config_id = %s AND user_id = %s
                """, (json.dumps(config['config_data']), config_id, user_id))
                conn.commit()

        logger.info(
            f"Agent strategy updated (v{new_strategy['version']})",
            user_id=user_id,
            config_id=config_id,
            updated_by=request.updated_by
        )

        return {
            "status": "success",
            "strategy": new_strategy,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update strategy failed: {e}", user_id=user_id)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 7. RECORD TRADE OBSERVATION (Post-trade reflection)
# ============================================================================

@router.post("/trade-observations")
async def record_trade_observation(
    request: RecordTradeObservationRequest,
    user_id: str = Query(...),
    authorization: str = Header(None),
    x_service_auth: str = Header(None, alias="x-service-auth")
) -> Dict[str, Any]:
    """
    Record post-trade reflection (what worked, what didn't, which data points were predictive).

    Agent calls this after closing a position to reflect on the trade outcome.
    """
    validate_agent_service_auth(authorization, x_service_auth)

    try:
        # Validate observation type
        valid_types = ["win_analysis", "loss_analysis"]
        if request.observation_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid observation_type. Must be one of: {valid_types}"
            )

        # Validate importance
        if not 1 <= request.importance <= 10:
            raise HTTPException(
                status_code=400,
                detail="Importance must be between 1 and 10"
            )

        # Get trade details for context
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Verify trade exists and belongs to user
                cur.execute("""
                    SELECT symbol, realized_pnl,
                           EXTRACT(EPOCH FROM (closed_at - opened_at))/60 as duration_minutes
                    FROM paper_trades
                    WHERE trade_id = %s AND user_id = %s
                """, (request.trade_id, user_id))

                trade = cur.fetchone()
                if not trade:
                    raise HTTPException(status_code=404, detail="Trade not found")

                symbol, pnl, duration = trade

                # Insert observation
                cur.execute("""
                    INSERT INTO trade_observations
                        (config_id, user_id, trade_id, observation_type,
                         what_went_well, what_went_wrong, predictive_data_points,
                         decision_review, trade_pnl, trade_duration_minutes, importance)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING observation_id, created_at
                """, (
                    request.config_id,
                    user_id,
                    request.trade_id,
                    request.observation_type,
                    request.what_went_well,
                    request.what_went_wrong,
                    json.dumps(request.predictive_data_points) if request.predictive_data_points else None,
                    request.decision_review,
                    pnl,
                    int(duration) if duration else None,
                    request.importance
                ))
                result = cur.fetchone()
                conn.commit()

        logger.info(
            f"Trade observation recorded: {request.observation_type}",
            user_id=user_id,
            config_id=request.config_id,
            trade_id=request.trade_id,
            importance=request.importance
        )

        return {
            "status": "success",
            "observation_id": str(result[0]),
            "created_at": result[1].isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Record trade observation failed: {e}", user_id=user_id)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 8. QUERY TRADE OBSERVATIONS (Search past learnings)
# ============================================================================

@router.post("/trade-observations/query")
async def query_trade_observations(
    request: QueryTradeObservationsRequest,
    user_id: str = Query(...),
    authorization: str = Header(None),
    x_service_auth: str = Header(None, alias="x-service-auth")
) -> Dict[str, Any]:
    """
    Query trade observations for learning and strategy refinement.

    Agent can search past observations to learn from previous trades.
    User + agent can review patterns together to improve strategy.
    """
    validate_agent_service_auth(authorization, x_service_auth)

    try:
        # Build dynamic query
        query = """
            SELECT
                o.observation_id,
                o.trade_id,
                o.observation_type,
                o.what_went_well,
                o.what_went_wrong,
                o.predictive_data_points,
                o.decision_review,
                o.trade_pnl,
                o.trade_duration_minutes,
                o.importance,
                o.created_at,
                t.symbol,
                t.side,
                t.entry_price,
                t.current_price
            FROM trade_observations o
            JOIN paper_trades t ON o.trade_id = t.trade_id
            WHERE o.config_id = %s AND o.user_id = %s
        """
        params = [request.config_id, user_id]

        # Add optional filters
        if request.symbol:
            query += " AND t.symbol = %s"
            params.append(request.symbol)

        if request.observation_type:
            query += " AND o.observation_type = %s"
            params.append(request.observation_type)

        if request.min_importance:
            query += " AND o.importance >= %s"
            params.append(request.min_importance)

        # Order by importance and recency
        query += " ORDER BY o.importance DESC, o.created_at DESC LIMIT %s"
        params.append(request.limit)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

        # Format results
        observations = []
        for row in rows:
            observations.append({
                "observation_id": str(row[0]),
                "trade_id": str(row[1]),
                "observation_type": row[2],
                "what_went_well": row[3],
                "what_went_wrong": row[4],
                "predictive_data_points": row[5],
                "decision_review": row[6],
                "trade_pnl": float(row[7]) if row[7] else None,
                "trade_duration_minutes": row[8],
                "importance": row[9],
                "created_at": row[10].isoformat(),
                "symbol": row[11],
                "side": row[12],
                "entry_price": float(row[13]) if row[13] else None,
                "current_price": float(row[14]) if row[14] else None
            })

        logger.info(
            f"Queried {len(observations)} trade observations",
            user_id=user_id,
            config_id=request.config_id
        )

        return {
            "status": "success",
            "observations": observations,
            "count": len(observations),
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query trade observations failed: {e}", user_id=user_id)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AGENT LIFECYCLE MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/{config_id}/start")
async def start_agent(
    config_id: str,
    mode: str = Query(..., description="strategy_definition | autonomous"),
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Start agent process via PM2.

    Args:
        config_id: Configuration ID
        mode: Agent mode ('strategy_definition' or 'autonomous')
        current_user: Authenticated user from JWT token

    Returns:
        Status of agent startup
    """

    try:
        # Check if already running
        pm2_list = subprocess.run(
            ['pm2', 'jlist'],
            capture_output=True,
            text=True,
            check=True
        )
        processes = json.loads(pm2_list.stdout)

        agent_name = f"agent-{config_id}"
        existing = next((p for p in processes if p['name'] == agent_name), None)

        if existing and existing['pm2_env']['status'] == 'online':
            logger.info(f"Agent already running: {agent_name}")
            return {
                "status": "already_running",
                "message": "Agent is already active",
                "agent_name": agent_name
            }

        # Start via PM2
        cmd = [
            'pm2', 'start',
            'agent/run_agent.py',
            '--name', agent_name,
            '--interpreter', '.venv-agent/bin/python',
            '--',
            '--config-id', config_id,
            '--mode', mode
        ]

        subprocess.run(cmd, cwd='/home/sev/ggbot', check=True)

        logger.info(
            f"Agent started successfully",
            config_id=config_id,
            mode=mode,
            agent_name=agent_name
        )

        return {
            "status": "started",
            "config_id": config_id,
            "mode": mode,
            "agent_name": agent_name,
            "timestamp": datetime.utcnow().isoformat()
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start agent: {e}", config_id=config_id)
        raise HTTPException(status_code=500, detail=f"PM2 command failed: {e}")
    except Exception as e:
        logger.error(f"Agent start failed: {e}", config_id=config_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{config_id}/stop")
async def stop_agent(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Stop agent process gracefully.

    Args:
        config_id: Configuration ID
        current_user: Authenticated user from JWT token

    Returns:
        Status of agent shutdown
    """

    try:
        agent_name = f"agent-{config_id}"

        # Stop PM2 process
        subprocess.run(['pm2', 'stop', agent_name], check=False)
        subprocess.run(['pm2', 'delete', agent_name], check=False)

        # Clear Redis queues
        redis_client.delete(f"agent:{config_id}:messages")
        redis_client.delete(f"agent:{config_id}:responses")

        logger.info(f"Agent stopped successfully", config_id=config_id, agent_name=agent_name)

        return {
            "status": "stopped",
            "config_id": config_id,
            "agent_name": agent_name,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Agent stop failed: {e}", config_id=config_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{config_id}/message")
async def send_message_to_agent(
    config_id: str,
    message: str = Body(..., embed=True),
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Push message to Redis queue for agent to receive.

    Args:
        config_id: Configuration ID
        message: Message text to send to agent
        current_user: Authenticated user from JWT token

    Returns:
        Confirmation of message sent
    """

    try:
        if not message or not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Format message as JSON (same as chat.py)
        message_data = json.dumps({
            "type": "user_message",
            "text": message.strip(),
            "timestamp": datetime.utcnow().isoformat()
        })

        # Push to Redis queue (agent polls from left with blpop)
        redis_client.lpush(f"agent:{config_id}:messages", message_data)

        logger.info(
            f"Message sent to agent",
            config_id=config_id,
            message_preview=message[:50]
        )

        return {
            "status": "sent",
            "message": message.strip(),
            "config_id": config_id,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send message failed: {e}", config_id=config_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{config_id}/poll-response")
async def poll_agent_response(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Poll for agent response from Redis queue (non-blocking).

    Args:
        config_id: Configuration ID
        current_user: Authenticated user from JWT token

    Returns:
        Agent response if available, or no_message status
    """

    try:
        # Non-blocking pop from right (agent pushes to left)
        response = redis_client.rpop(f"agent:{config_id}:responses")

        if response:
            # Try to parse as JSON (for structured responses)
            try:
                response_data = json.loads(response)
                return {
                    "status": "success",
                    **response_data,  # Include all fields from agent (message, show_confirm_button, etc.)
                    "timestamp": datetime.utcnow().isoformat()
                }
            except json.JSONDecodeError:
                # Plain text response
                return {
                    "status": "success",
                    "message": response,
                    "timestamp": datetime.utcnow().isoformat()
                }
        else:
            return {
                "status": "no_message",
                "timestamp": datetime.utcnow().isoformat()
            }

    except Exception as e:
        logger.error(f"Poll response failed: {e}", config_id=config_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{config_id}/status")
async def get_agent_status(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Get current agent status (running/stopped, mode, uptime).

    Args:
        config_id: Configuration ID
        current_user: Authenticated user from JWT token

    Returns:
        Agent status information
    """

    try:
        agent_name = f"agent-{config_id}"

        # Get PM2 process list
        pm2_list = subprocess.run(
            ['pm2', 'jlist'],
            capture_output=True,
            text=True,
            check=True
        )
        processes = json.loads(pm2_list.stdout)

        agent = next((p for p in processes if p['name'] == agent_name), None)

        if not agent:
            return {
                "status": "inactive",
                "config_id": config_id,
                "agent_name": agent_name,
                "mode": None,
                "uptime": None,
                "timestamp": datetime.utcnow().isoformat()
            }

        pm2_env = agent.get('pm2_env', {})
        status = pm2_env.get('status', 'unknown')

        # Parse mode from command-line args (e.g., ['--config-id', 'abc', '--mode', 'strategy_definition'])
        args = pm2_env.get('args', [])
        mode = None
        if '--mode' in args:
            mode_index = args.index('--mode')
            if mode_index + 1 < len(args):
                mode = args[mode_index + 1]

        return {
            "status": status,  # 'online', 'stopped', 'errored', etc.
            "config_id": config_id,
            "agent_name": agent_name,
            "mode": mode,
            "uptime": pm2_env.get('pm_uptime'),
            "restarts": pm2_env.get('restart_time', 0),
            "cpu": agent.get('monit', {}).get('cpu', 0),
            "memory": agent.get('monit', {}).get('memory', 0),
            "timestamp": datetime.utcnow().isoformat()
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get agent status: {e}", config_id=config_id)
        raise HTTPException(status_code=500, detail=f"PM2 command failed: {e}")
    except Exception as e:
        logger.error(f"Get agent status failed: {e}", config_id=config_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{config_id}/conversation-history")
async def get_conversation_history(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Get conversation history for reconnecting to running agent.

    Args:
        config_id: Configuration ID
        current_user: Authenticated user from JWT token

    Returns:
        List of conversation messages with role, content, and timestamp
    """

    try:
        # Get all messages from history list
        history_raw = redis_client.lrange(f"agent:{config_id}:history", 0, -1)

        # Parse JSON messages
        messages = []
        for msg in history_raw:
            try:
                parsed = json.loads(msg)
                messages.append(parsed)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse history message: {msg}")
                continue

        logger.info(
            f"Fetched conversation history",
            config_id=config_id,
            message_count=len(messages)
        )

        return {
            "status": "success",
            "messages": messages,
            "count": len(messages),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Get conversation history failed: {e}", config_id=config_id)
        raise HTTPException(status_code=500, detail=str(e))
