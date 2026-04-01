"""
GGBot V2 Orchestrator - API Server

FastAPI API server for the ggbots platform. Handles HTTP/SSE endpoints,
authentication, billing, and bot lifecycle. Bot execution runs in separate
ggbot_scheduler process.
"""

# stdlib
import asyncio
import json
import os
import re
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

# third-party
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request, Query, Header
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, field_serializer
import psycopg2.extras
import stripe
import uvicorn

# local — scheduler utilities (calculate_next_run replaces live scheduler queries)
from core.scheduler.utils import calculate_next_run, extract_timeframe_from_config

# local — auth, SSE
from core.auth.supabase_auth import AuthenticatedUser, get_current_user_v2, require_premium_user_v2
from core.sse import get_unified_dashboard_data

class ServiceUser:
    """Represents an authenticated service."""
    def __init__(self, service_name: str):
        self.service_name = service_name

service_calls = defaultdict(list)

async def get_service_user(request: Request):
    """Authenticate service-to-service requests."""
    auth_header = request.headers.get('authorization', '')
    service_header = request.headers.get('x-service-auth', '')

    # Allow multiple trusted services
    allowed_services = ['signal-listener', 'agent-runner']

    if not auth_header.startswith('Bearer ') or service_header not in allowed_services:
        raise HTTPException(status_code=401, detail="Service authentication required")

    # Rate limiting per service
    now = time.time()
    calls = service_calls[service_header]
    service_calls[service_header] = [t for t in calls if now - t < 60]

    # Different rate limits per service (agent-runner needs higher limit)
    rate_limit = 600 if service_header == 'agent-runner' else 120  # 10 req/sec vs 2 req/sec
    if len(service_calls[service_header]) >= rate_limit:
        raise HTTPException(status_code=429, detail="Service rate limit exceeded")

    service_calls[service_header].append(now)

    token = auth_header.split(' ')[1]
    service_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not service_key or token != service_key:
        raise HTTPException(status_code=401, detail="Invalid service token")

    return ServiceUser(service_name=service_header)

async def get_mock_user_for_dev():
    """Mock user for development."""
    return AuthenticatedUser(
        user_id="00000000-0000-0000-0000-000000000000",
        email="user@example.com",
        claims={"sub": "00000000-0000-0000-0000-000000000000", "email": "user@example.com"}
    )

# local — services
from core.services.config_service import ConfigService, BotConfigV2, config_service
from core.services.user_service import UserService, user_service
from core.services.llm_service import LLMService, llm_service
from core.services.indicator_service import IndicatorService
from core.common.logger import logger as base_logger
from core.domain import Decision, DecisionAction, DecisionStatus, UserProfile, Symbol, Confidence

DEMO_MODE = os.getenv("GGBOT_DEMO_MODE", "false").lower() == "true"

logger = base_logger

# Constants
PAPER_INITIAL_BALANCE = 10000.0
CREDIT_PURCHASE_MIN_CENTS = 500      # $5
CREDIT_PURCHASE_MAX_CENTS = 50000    # $500
API_BASE_URL = os.getenv("API_BASE_URL", "https://ggbots-api.nightingale.business")


def _check_dojo_lock(config_id: str) -> None:
    """Raise 400 if bot is locked in an active Dojo match."""
    from core.arena.matches import is_dojo_locked
    if is_dojo_locked(config_id):
        raise HTTPException(
            status_code=400,
            detail="Bot is locked for an active Dojo match. Forfeit to unlock."
        )


class ConfigCreateRequest(BaseModel):
    config_name: str
    schema_version: str = "2.1"
    config_type: str = "scheduled_trading"
    trading_mode: str = "paper"  # 'paper' | 'hyperliquid'
    selected_pair: Optional[str] = "BTC/USDT"  # Optional for agents
    extraction: Optional[Dict[str, Any]] = None  # Optional for agents and signal_validation
    decision: Optional[Dict[str, Any]] = None  # Optional for agents
    trading: Dict[str, Any]  # Always required
    llm_config: Optional[Dict[str, Any]] = None  # Optional for agents
    telegram_integration: Optional[Dict[str, Any]] = None
    agent_strategy: Optional[Dict[str, Any]] = None  # For agent-type configs


class ConfigUpdateRequest(BaseModel):
    config_name: Optional[str] = None
    schema_version: Optional[str] = None
    config_type: Optional[str] = None
    trading_mode: Optional[str] = None  # Allow updating trading mode
    profile_image_url: Optional[str] = None  # Bot avatar image URL
    selected_pair: Optional[str] = None
    extraction: Optional[Dict[str, Any]] = None
    decision: Optional[Dict[str, Any]] = None
    trading: Optional[Dict[str, Any]] = None
    llm_config: Optional[Dict[str, Any]] = None
    telegram_integration: Optional[Dict[str, Any]] = None
    agent_strategy: Optional[Dict[str, Any]] = None


class SignalOrchestrationRequest(BaseModel):
    signal_data: Optional[Dict[str, Any]] = None
    override_symbol: Optional[str] = None


# Orchestrator and result types (extracted to their own module)
from core.orchestrator.orchestrator import GGBotOrchestrator, OrchestrationResult, serialize_numpy_types


# FastAPI lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    logger.info("🚀 Starting GGBot V2 Orchestrator")
    
    # Initialize monitoring service variables
    monitoring_service = None
    monitoring_task = None
    
    # Startup tasks
    try:
        # Test database connectivity with a valid UUID
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 as test")
                cur.fetchone()
        logger.info("✅ Database connectivity verified")
        
        # Test LLM service
        # await llm_service.test_hosted_keys()
        logger.info("✅ LLM service initialized")


        # NOTE: APScheduler now runs in separate ggbot_scheduler process.
        # Bot scheduling is handled there via DB reconciliation loop.
        logger.info("Scheduler runs in separate process (ggbot_scheduler)")

        # Start monitoring service (positions only - no WebSocket spam!)
        from core.monitoring.service import MonitoringService
        monitoring_service = MonitoringService()
        monitoring_task = asyncio.create_task(monitoring_service.start())
        logger.info("Monitoring service started")

        logger.info("GGBot V2 API ready")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown tasks
    logger.info("Shutting down GGBot V2 API")

    # Shutdown monitoring service
    if monitoring_service and monitoring_task:
        await monitoring_service.stop()
        if not monitoring_task.done():
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Monitoring service stopped")


# Create FastAPI app
app = FastAPI(
    title="GGBot V2 Orchestrator",
    description="Unified orchestrator for autonomous AI trading with Supabase integration",
    version="2.0.0",
    lifespan=lifespan
)

# Include API routers
from api.paper_trading import router as paper_trading_router
from api.agent import router as agent_router
from api.activities import router as activities_router
from api.snapshots import router as snapshots_router
from api.assistant import router as assistant_router
from api.admin import router as admin_router
from api.public import router as public_router
from api.usage import router as usage_router
from api.virtuals_arena import router as virtuals_arena_router
app.include_router(paper_trading_router)
app.include_router(agent_router)
app.include_router(activities_router)
app.include_router(snapshots_router)
app.include_router(assistant_router)
app.include_router(admin_router)
app.include_router(public_router)
app.include_router(usage_router)
app.include_router(virtuals_arena_router)


# Orchestrator instance (used by "Run Now" and signal validation endpoints)
orchestrator = GGBotOrchestrator()

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "GGBot V2 Orchestrator",
        "version": "2.0.0",
        "status": "operational",
        "features": [
            "Supabase authentication",
            "Multi-user isolation",
            "Subscription-aware LLM clients",
            "Dynamic indicator management",
            "V2 module integration (in progress)"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0"
    }


@app.get("/api/dashboard-stream")
async def dashboard_stream(
    request: Request,
    token: str = None
):
    """
    Server-Sent Events stream for unified dashboard data.
    
    Provides real-time updates for:
    - Bot configurations and status
    - Open positions and P&L
    - Recent decisions (5 per bot)
    - Account summaries
    
    Updates every 5 seconds with proper SSE headers and heartbeat.
    
    Authentication via:
    - Query parameter: ?token=<jwt_token>
    - Authorization header: Bearer <jwt_token>
    """
    import time
    from core.auth.supabase_auth import AuthMiddleware
    
    # Get token from query param or Authorization header
    auth_token = token
    if not auth_token:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            auth_token = auth_header.split(" ", 1)[1]
    
    if not auth_token:
        raise HTTPException(status_code=401, detail="Authentication required: provide token query param or Authorization header")
    
    # Authenticate the token
    try:
        current_user = await AuthMiddleware.authenticate_request(f"Bearer {auth_token}")
    except HTTPException as e:
        raise HTTPException(status_code=403, detail=f"Authentication failed: {e.detail}")
    
    async def generate():
        event_id = 0
        heartbeat_counter = 0
        logger.info(f"SSE generate function started for user {current_user.user_id}")
        try:
            while True:
                try:
                    # Get unified dashboard data for authenticated user
                    data = await get_unified_dashboard_data(current_user.user_id)
                    event_id += 1
                    heartbeat_counter += 1

                    # Send dashboard update event
                    yield f"id: {event_id}\n"
                    yield f"event: dashboard\n"
                    yield f"data: {json.dumps(data, default=str)}\n\n"

                    # Send heartbeat every 10 seconds (2 iterations)
                    if heartbeat_counter % 2 == 0:
                        yield f":keepalive {int(time.time())}\n\n"

                    await asyncio.sleep(5)  # 5-second update interval
                    
                except Exception as e:
                    logger.error(f"SSE data generation error for user {current_user.user_id}: {e}")
                    # Send error event
                    yield f"event: error\n"
                    yield f"data: {json.dumps({'message': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"
                    await asyncio.sleep(5)  # Wait before retrying
                    
        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for user {current_user.user_id}")
            return
        except Exception as e:
            logger.error(f"SSE stream error for user {current_user.user_id}: {e}")
            yield f"event: error\n"
            yield f"data: {json.dumps({'message': 'Stream terminated', 'error': str(e)})}\n\n"

    # Set proper SSE headers
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "text/event-stream",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"  # Prevent nginx buffering
    }
    
    logger.info(f"Starting SSE dashboard stream for user {current_user.user_id}")
    return StreamingResponse(generate(), headers=headers, media_type="text/event-stream")


# Configuration Management Endpoints
@app.post("/api/v2/config")
async def create_config(
    request: ConfigCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Create a new bot configuration with specified trading mode."""
    # Extract fields that go in table columns, not JSONB
    request_data = request.dict(exclude={"config_name", "trading_mode"})
    config_type = request_data.pop("config_type", "scheduled_trading")
    trading_mode = request.trading_mode

    # Validate trading mode
    if trading_mode not in ["paper", "hyperliquid"]:
        raise HTTPException(status_code=400, detail="Invalid trading_mode. Must be 'paper' or 'hyperliquid'")

    # NOTE: No subscription check here — users can CREATE live trading bots on any tier.
    # The real gate is bot ACTIVATION (start_bot endpoint) which checks can_activate_bots.
    # Free users get test runs per bot regardless of trading mode.

    # Hyperliquid: block direct creation — use "Promote to Live" instead
    if trading_mode == "hyperliquid":
        raise HTTPException(
            status_code=400,
            detail="Use 'Promote to Live' to set up live trading. Create a paper bot first, then promote it."
        )

    # Validate symbol has real-time price data (WebSocket cached)
    selected_pair = request_data.get("selected_pair")
    if selected_pair:
        from core.symbols.registry import is_websocket_cached, get_websocket_cached_count

        if not is_websocket_cached(selected_pair, format_type="ccxt"):
            cached_count = get_websocket_cached_count()
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Symbol {selected_pair} requires real-time price data for trading. "
                    f"Please choose from {cached_count} available symbols with WebSocket price feeds. "
                    f"This ensures fast position monitoring and reliable trade execution."
                )
            )

        # Check symbol compatibility with trading mode
        if trading_mode == "hyperliquid":
            from core.symbols import UniversalSymbolStandardizer
            standardizer = UniversalSymbolStandardizer()
            if not standardizer.is_hyperliquid_compatible(selected_pair, "ccxt"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Symbol {selected_pair} is not compatible with Hyperliquid trading."
                )

    # Add config_type back to config_data for BotConfigV2 constructor
    request_data["config_type"] = config_type

    config = await config_service.create_config(
        user_id=current_user.user_id,
        config_name=request.config_name,
        config_data=request_data,
        trading_mode=trading_mode,
    )

    if not config:
        raise HTTPException(status_code=400, detail="Failed to create configuration")

    # Only create paper account for paper trading mode
    if trading_mode == "paper":
        try:
            from trading.paper.supabase_service import SupabasePaperTradingService
            trading_service = SupabasePaperTradingService()
            account = await trading_service.get_or_create_paper_account(
                config_id=config.config_id,
                user_id=current_user.user_id
            )
            logger.info(f"Created paper account {account.account_id} for new config {config.config_id}")
        except Exception as e:
            logger.error(f"Failed to create paper account for config {config.config_id}: {e}")
            # Don't fail the config creation - account can be created later

    # Create initial account_snapshot for timeline and metrics
    # Paper starts at $10,000, live modes start at $0 (will sync from exchange)
    initial_balance = PAPER_INITIAL_BALANCE if trading_mode == "paper" else 0.0
    try:
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO account_snapshots (
                        config_id, user_id, trading_mode,
                        current_balance, available_balance, margin_used,
                        total_pnl, realized_pnl, unrealized_pnl,
                        total_trades, win_trades, loss_trades, open_positions
                    ) VALUES (
                        %s, %s, %s,
                        %s, %s, 0,
                        0, 0, 0,
                        0, 0, 0, 0
                    )
                """, (
                    config.config_id, current_user.user_id, trading_mode,
                    initial_balance, initial_balance
                ))
                conn.commit()
        logger.info(f"Created initial account_snapshot for config {config.config_id} (balance=${initial_balance})")
    except Exception as e:
        logger.error(f"Failed to create initial account_snapshot for config {config.config_id}: {e}")
        # Non-critical - account monitor will create snapshot on next cycle

    logger.bind(user_id=current_user.user_id).info(
        f"Created {trading_mode} bot '{request.config_name}' (config_id={config.config_id})"
    )

    # Log bot_created activity for timeline
    from core.common.activity_logger import log_activity_safe
    log_activity_safe(
        config_id=config.config_id,
        user_id=current_user.user_id,
        activity_type='bot_created',
        activity_source='user_action',
        summary=f"Created {trading_mode} bot: {request.config_name}",
        details={
            'config_name': request.config_name,
            'config_type': config_type,
            'trading_mode': trading_mode,
            'selected_pair': request_data.get('selected_pair'),
        },
        related_symbol=request_data.get('selected_pair'),
        importance=8  # High importance for lifecycle event
    )

    return {
        "status": "success",
        "config": config.to_dict()
    }


@app.get("/api/v2/config")
async def list_configs(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """List all configurations for the current user, with arena registration status."""
    configs = await config_service.list_configs(current_user.user_id)
    config_dicts = [config.to_dict() for config in configs]

    # Enrich with arena registration data
    config_ids = [c['config_id'] for c in config_dicts]
    if config_ids:
        from core.arena.seasons import SEASONS, get_season_phase
        arena_map = {}
        try:
            from core.common.db import get_db_connection
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT config_id, season_id, registered_at
                        FROM arena_registrations
                        WHERE config_id = ANY(%s) AND unregistered_at IS NULL
                    """, (config_ids,))
                    for row in cur.fetchall():
                        cid = str(row[0])
                        sid = row[1]
                        phase = get_season_phase(sid)
                        season = SEASONS.get(sid, {})
                        arena_map[cid] = {
                            "season_id": sid,
                            "season_name": season.get('name', f'Season {sid}'),
                            "registered_at": row[2].isoformat() if row[2] else None,
                            "is_locked": phase in ('registration', 'competition'),
                            "can_unregister": phase == 'registration',
                        }
        except Exception:
            pass  # Non-critical enrichment

        for c in config_dicts:
            c['arena_registration'] = arena_map.get(c['config_id'])

        # Enrich with dojo data (elo_rating, dojo_visible, lock state)
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT config_id, elo_rating, dojo_visible
                        FROM configurations
                        WHERE config_id = ANY(%s)
                    """, (config_ids,))
                    for row in cur.fetchall():
                        cid = str(row[0])
                        for c in config_dicts:
                            if c['config_id'] == cid:
                                c['elo_rating'] = row[1] or 1200
                                c['dojo_visible'] = row[2] if row[2] is not None else True

                    # Active matches for lock state
                    cur.execute("""
                        SELECT
                            CASE WHEN challenger_config_id = ANY(%s) THEN challenger_config_id
                                 ELSE opponent_config_id END AS config_id,
                            id, format, ends_at,
                            CASE WHEN challenger_config_id = ANY(%s)
                                 THEN (SELECT config_name FROM configurations WHERE config_id = opponent_config_id)
                                 ELSE (SELECT config_name FROM configurations WHERE config_id = challenger_config_id)
                            END AS opponent_name
                        FROM dojo_matches
                        WHERE status = 'active'
                          AND (challenger_config_id = ANY(%s) OR opponent_config_id = ANY(%s))
                    """, (config_ids, config_ids, config_ids, config_ids))

                    dojo_lock_map = {}
                    for row in cur.fetchall():
                        cid = str(row[0])
                        if cid not in dojo_lock_map:
                            dojo_lock_map[cid] = []
                        dojo_lock_map[cid].append({
                            'match_id': str(row[1]),
                            'format': row[2],
                            'ends_at': row[3].isoformat() if row[3] else None,
                            'opponent_name': row[4],
                        })

                    for c in config_dicts:
                        active = dojo_lock_map.get(c['config_id'], [])
                        c['dojo_locked'] = len(active) > 0
                        c['dojo_matches_active'] = active
        except Exception:
            pass  # Non-critical enrichment

    return {
        "status": "success",
        "configs": config_dicts,
        "count": len(config_dicts)
    }


@app.put("/api/v2/config/{config_id}/dojo-visibility")
async def toggle_dojo_visibility(
    config_id: str,
    body: Dict[str, Any],
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Toggle dojo_visible flag for a bot configuration."""
    visible = body.get("dojo_visible")
    if visible is None:
        raise HTTPException(status_code=400, detail="dojo_visible is required")

    from core.common.db import get_db_connection
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE configurations
                SET dojo_visible = %s, updated_at = CURRENT_TIMESTAMP
                WHERE config_id = %s AND user_id = %s
                RETURNING config_id
            """, (bool(visible), config_id, str(current_user.user_id)))
            result = cur.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Configuration not found")
            conn.commit()

    return {"status": "success", "dojo_visible": bool(visible)}


@app.get("/api/v2/dojo/elo-history/{config_id}")
async def get_elo_history(
    config_id: str,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get Elo rating history for a bot."""
    from core.common.db import get_db_connection
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Verify ownership
            cur.execute(
                "SELECT config_id FROM configurations WHERE config_id = %s AND user_id = %s",
                (config_id, str(current_user.user_id))
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Configuration not found")

            cur.execute("""
                SELECT id, elo_before, elo_after, change, reason, match_id, details, created_at
                FROM elo_history
                WHERE config_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (config_id, limit, offset))

            history = []
            for row in cur.fetchall():
                history.append({
                    "id": str(row[0]),
                    "elo_before": row[1],
                    "elo_after": row[2],
                    "change": row[3],
                    "reason": row[4],
                    "match_id": str(row[5]) if row[5] else None,
                    "details": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                })

            cur.execute("SELECT COUNT(*) FROM elo_history WHERE config_id = %s", (config_id,))
            total = cur.fetchone()[0]

    return {"status": "success", "history": history, "total": total}


# ─── Dojo Match Endpoints ────────────────────────────────────────────────────

@app.get("/api/v2/dojo/can-enter/{config_id}")
async def dojo_can_enter(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Check if a bot is eligible to enter a Dojo match."""
    from core.arena.matches import check_entry_gate
    return check_entry_gate(config_id, current_user.user_id)


@app.post("/api/v2/dojo/challenge")
async def dojo_challenge(
    body: Dict[str, Any],
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Issue a Dojo challenge. House Bot opponents auto-accept and auto-start."""
    from core.arena.matches import create_challenge

    challenger_config_id = body.get('config_id')
    opponent_config_id = body.get('opponent_config_id')
    match_format = body.get('format', 'rapid')

    if not challenger_config_id or not opponent_config_id:
        raise HTTPException(status_code=400, detail="config_id and opponent_config_id required")

    result = create_challenge(
        challenger_config_id=challenger_config_id,
        opponent_config_id=opponent_config_id,
        match_format=match_format,
        user_id=current_user.user_id,
    )

    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@app.post("/api/v2/dojo/match/{match_id}/forfeit")
async def dojo_forfeit(
    match_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Forfeit an active Dojo match."""
    from core.arena.matches import forfeit_match

    result = forfeit_match(match_id, current_user.user_id)

    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@app.get("/api/v2/dojo/matches/{config_id}")
async def dojo_match_history(
    config_id: str,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get completed match history for a bot."""
    from core.arena.matches import get_match_history
    matches = get_match_history(config_id, limit=limit, offset=offset)
    return {"status": "success", "matches": matches}


@app.get("/api/v2/dojo/stats/{config_id}")
async def dojo_bot_stats(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get aggregate Dojo stats for a bot (wins, losses, draws)."""
    from core.arena.matches import get_bot_dojo_stats
    return get_bot_dojo_stats(config_id)


@app.get("/api/v2/dojo/active/{config_id}")
async def dojo_active_matches(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get active/pending matches for a bot."""
    from core.arena.matches import get_active_matches
    return {"status": "success", "matches": get_active_matches(config_id)}


@app.get("/api/v2/config/{config_id}")
async def get_config(
    config_id: str
) -> Dict[str, Any]:
    """Get a specific configuration (PUBLIC for competition viewing)."""
    from core.common.db import get_db_connection

    try:
        # Get config without user_id verification (public viewing)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        config_id,
                        user_id,
                        config_name,
                        config_type,
                        state,
                        trading_mode,
                        symphony_agent_id,
                        created_at,
                        updated_at,
                        config_data,
                        profile_image_url,
                        is_public_performance
                    FROM configurations
                    WHERE config_id = %s
                """, (config_id,))
                row = cur.fetchone()

                if not row:
                    raise HTTPException(status_code=404, detail="Configuration not found")

                # Extract data while connection is still open
                config = {
                    "config_id": str(row[0]),
                    "user_id": str(row[1]),
                    "config_name": row[2],
                    "config_type": row[3],
                    "state": row[4],
                    "trading_mode": row[5],
                    "symphony_agent_id": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "updated_at": row[8].isoformat() if row[8] else None,
                    "config_data": row[9],
                    "profile_image_url": row[10],
                    "is_public_performance": row[11] or False
                }

        return {
            "status": "success",
            "config": config
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve configuration: {str(e)}")


@app.get("/api/v2/configs/{config_id}/strategy")
async def get_config_strategy(
    config_id: str
) -> Dict[str, Any]:
    """
    Get agent strategy for a configuration (PUBLIC for timeline viewing).

    Used by Activity Timeline to display strategy in "View Configuration" modal.
    Returns just the agent_strategy content, or 404 if not an agent config.
    """
    from core.common.db import get_db_connection

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT config_type, config_data
                    FROM configurations
                    WHERE config_id = %s
                """, (config_id,))
                row = cur.fetchone()

                if not row:
                    raise HTTPException(status_code=404, detail="Configuration not found")

                config_type = row[0]
                config_data = row[1]

                # Check if this is an agent config
                if config_type != 'agent':
                    raise HTTPException(status_code=404, detail="Not an agent configuration")

                # Extract agent_strategy
                agent_strategy = config_data.get('agent_strategy', {})
                strategy_content = agent_strategy.get('content', '')

                if not strategy_content:
                    raise HTTPException(status_code=404, detail="No strategy defined for this agent")

                return {
                    "status": "success",
                    "strategy": strategy_content,
                    "version": agent_strategy.get('version', 1),
                    "autonomously_editable": agent_strategy.get('autonomously_editable', False),
                    "last_updated_at": agent_strategy.get('last_updated_at'),
                    "last_updated_by": agent_strategy.get('last_updated_by', 'user')
                }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy for config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve strategy: {str(e)}")


@app.put("/api/v2/config/{config_id}")
async def update_config(
    config_id: str,
    request: ConfigUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Update a configuration and automatically reschedule if active."""
    # Filter out None values
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    config_name = update_data.pop("config_name", None)
    config_type = update_data.pop("config_type", None)
    trading_mode = update_data.pop("trading_mode", None)
    profile_image_url = update_data.pop("profile_image_url", None)

    # Check Dojo lock — block strategy edits for bots in active matches
    strategy_fields_in_update = {k for k in update_data if k in {'selected_pair', 'extraction', 'decision', 'trading', 'llm_config'}}
    if strategy_fields_in_update:
        _check_dojo_lock(config_id)

    # Check arena lock — block strategy edits for registered bots
    if strategy_fields_in_update:
        from core.arena.seasons import get_season_phase
        from core.common.db import get_db_connection as _get_db
        with _get_db() as _conn:
            with _conn.cursor() as _cur:
                _cur.execute("""
                    SELECT ar.season_id FROM arena_registrations ar
                    WHERE ar.config_id = %s AND ar.unregistered_at IS NULL
                    LIMIT 1
                """, (config_id,))
                active_reg = _cur.fetchone()
                if active_reg:
                    phase = get_season_phase(active_reg[0])
                    if phase == 'registration':
                        raise HTTPException(
                            status_code=400,
                            detail="Bot is locked for ggArena Season 2. Unregister during registration week to edit your strategy."
                        )
                    elif phase == 'competition':
                        raise HTTPException(
                            status_code=400,
                            detail="Bot is locked for ggArena Season 2 competition. Strategy edits are frozen until the season ends."
                        )

    # Validate symbol has real-time price data if changing selected_pair
    selected_pair = update_data.get("selected_pair")
    if selected_pair:
        from core.symbols.registry import is_websocket_cached, get_websocket_cached_count

        if not is_websocket_cached(selected_pair, format_type="ccxt"):
            cached_count = get_websocket_cached_count()
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Symbol {selected_pair} requires real-time price data for trading. "
                    f"Please choose from {cached_count} available symbols with WebSocket price feeds. "
                    f"This ensures fast position monitoring and reliable trade execution."
                )
            )

    # Check if this is an active bot before update
    current_state = await config_service.get_bot_state(config_id, current_user.user_id)
    was_active = current_state == 'active'

    # Get old config to compare timeframes
    old_config = await config_service.get_config(config_id, current_user.user_id)
    old_timeframe = extract_timeframe_from_config(old_config.to_jsonb()) if old_config else None
    
    config = await config_service.update_config(
        config_id=config_id,
        user_id=current_user.user_id,
        config_data=update_data,
        config_name=config_name,
        config_type=config_type,
        trading_mode=trading_mode,
        profile_image_url=profile_image_url
    )

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found or update failed")

    # Log strategy_updated activity for meaningful config changes
    # Skip name-only or type-only changes (not strategy changes)
    strategy_fields = {'selected_pair', 'extraction', 'decision', 'trading', 'llm_config'}
    changed_strategy_fields = [f for f in update_data.keys() if f in strategy_fields]
    if changed_strategy_fields:
        from core.common.activity_logger import log_activity_safe
        field_labels = ', '.join(changed_strategy_fields)
        log_activity_safe(
            config_id=config_id,
            user_id=current_user.user_id,
            activity_type='strategy_updated',
            activity_source='user_action',
            summary=f"Config updated: {field_labels}",
            details={
                'changed_fields': changed_strategy_fields,
                'updates': {k: v for k, v in update_data.items() if k in strategy_fields},
            },
            importance=5
        )

    # If bot was active and timeframe changed, include reschedule info in response.
    # The scheduler process detects timeframe changes via reconcile loop.
    reschedule_info = None
    if was_active:
        new_timeframe = extract_timeframe_from_config(config.to_jsonb())

        if old_timeframe != new_timeframe:
            logger.info(f"Timeframe changed from {old_timeframe} to {new_timeframe} for active bot {config_id}")
            next_run = calculate_next_run(new_timeframe)

            reschedule_info = {
                "rescheduled": True,
                "old_timeframe": old_timeframe,
                "new_timeframe": new_timeframe,
                "next_run": next_run
            }

    response = {
        "status": "success",
        "config": config.to_dict()
    }

    if reschedule_info:
        response["schedule_update"] = reschedule_info

    return response


@app.delete("/api/v2/config/{config_id}")
async def delete_config(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Delete a configuration. Scheduler reconcile loop auto-removes orphaned jobs."""
    _check_dojo_lock(config_id)
    success = await config_service.delete_config(config_id, current_user.user_id)

    if not success:
        raise HTTPException(status_code=404, detail="Configuration not found")

    logger.info(f"Deleted config {config_id}")

    return {
        "status": "success",
        "message": "Configuration deleted successfully"
    }


# Orchestration Endpoints
@app.post("/api/v2/orchestrate/{config_id}")
async def run_orchestration(
    config_id: str,
    request: SignalOrchestrationRequest = SignalOrchestrationRequest(),
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> OrchestrationResult:
    """Run autonomous trading cycle or signal validation for a configuration."""
    _check_dojo_lock(config_id)
    try:
        result = await orchestrator.run_autonomous_cycle(
            config_id,
            current_user.user_id,
            signal_data=request.signal_data,
            override_symbol=request.override_symbol
        )
        
        if result.status == "error":
            # Extract error details from the result object
            error_detail = "Unknown orchestration error"
            if result.extraction_result and isinstance(result.extraction_result, dict):
                error_detail = result.extraction_result.get('error', error_detail)
            
            # Log the full result for debugging
            logger.error(f"Orchestration failed for config {config_id}: {error_detail}")
            logger.error(f"Full result object: {result.dict()}")
            raise HTTPException(status_code=500, detail=f"Orchestration failed: {error_detail}")
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log any unexpected exceptions
        logger.error(f"Unexpected error in orchestration endpoint for config {config_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v2/signal-validation/{config_id}")
async def run_signal_validation(
    config_id: str,
    user_id: str,
    request: SignalOrchestrationRequest,
    _: ServiceUser = Depends(get_service_user)
) -> OrchestrationResult:
    """Signal validation endpoint for service-to-service calls."""
    try:
        logger.info(f"Signal validation triggered by service for config {config_id}, user {user_id}")

        result = await orchestrator.run_autonomous_cycle(
            config_id,
            user_id,
            signal_data=request.signal_data,
            override_symbol=request.override_symbol
        )

        if result.status == "error":
            error_detail = "Unknown signal validation error"
            if result.extraction_result and isinstance(result.extraction_result, dict):
                error_detail = result.extraction_result.get('error', error_detail)

            logger.error(f"Signal validation failed for config {config_id}: {error_detail}")
            raise HTTPException(status_code=500, detail=f"Signal validation failed: {error_detail}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in signal validation for config {config_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v2/test/signal-publishing/{config_id}")
async def test_signal_publishing(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Test signal publishing functionality with mock data."""
    try:
        from signals.publishing_service import SignalPublishingService, AccessControlService

        # Check permissions first and give specific error
        access_control = AccessControlService()
        can_publish = await access_control.can_publish_signals(current_user.user_id)
        if not can_publish:
            raise HTTPException(
                status_code=403,
                detail="Telegram publishing requires an active subscription. Upgrade at ggbots.ai/pricing"
            )

        # Check telegram config exists
        telegram_config = await access_control.get_user_telegram_config(config_id)
        if not telegram_config:
            raise HTTPException(
                status_code=400,
                detail="Telegram publishing not configured. Enable it and enter your channel ID first."
            )

        # Create service and test message
        service = SignalPublishingService()

        # Send a simple test message directly
        test_message = (
            "🧪 ggbots Test Message\n\n"
            "Your Telegram publishing is configured correctly!\n\n"
            "Your bot's trading signals will appear here.\n\n"
            "🌐 https://ggbots.ai"
        )

        success = await service.telegram_bot.send_message(
            chat_id=telegram_config.chat_id,
            text=test_message
        )

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to send message. Make sure @ggFilter_Bot is admin in your channel/group with 'Post Messages' permission."
            )

        return {
            "status": "success",
            "message": "Test message sent successfully!",
            "chat_id": telegram_config.chat_id,
            "config_id": config_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signal publishing test failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Signal publishing test failed: {str(e)}")


# Symbols API Endpoints
@app.get("/api/v2/symbols/supported")
async def get_supported_symbols() -> Dict[str, Any]:
    """Get all 141 supported trading symbols."""
    try:
        from core.symbols.standardizer import UniversalSymbolStandardizer
        standardizer = UniversalSymbolStandardizer()

        # Get symbols in different formats for frontend use
        platform_symbols = standardizer.get_supported_symbols("platform")  # BTC-USDT format
        ccxt_symbols = standardizer.get_supported_symbols("ccxt")          # BTC/USDT format

        return {
            "status": "success",
            "data": {
                "platform": sorted(platform_symbols),  # For internal use
                "display": sorted(ccxt_symbols),       # For UI display (BTC/USDT looks better)
                "count": len(platform_symbols)
            }
        }

    except Exception as e:
        logger.error(f"Failed to get supported symbols: {e}")
        return {
            "status": "error",
            "data": {
                "platform": [],
                "display": [],
                "count": 0
            },
            "error": str(e)
        }


@app.get("/api/v2/symbols/search/{query}")
async def search_symbols(query: str) -> Dict[str, Any]:
    """Search symbols by base currency or partial match."""
    try:
        from core.symbols.standardizer import UniversalSymbolStandardizer
        standardizer = UniversalSymbolStandardizer()

        platform_symbols = standardizer.get_supported_symbols("platform")
        ccxt_symbols = standardizer.get_supported_symbols("ccxt")

        query = query.upper().strip()

        # Search logic
        platform_matches = []
        display_matches = []

        for platform_symbol, ccxt_symbol in zip(platform_symbols, ccxt_symbols):
            # Match base currency (BTC from BTC-USDT)
            base_currency = platform_symbol.split('-')[0]

            # Check if query matches base currency or symbol
            if (query in platform_symbol or
                query in base_currency or
                query in ccxt_symbol):
                platform_matches.append(platform_symbol)
                display_matches.append(ccxt_symbol)

        return {
            "status": "success",
            "data": {
                "query": query,
                "platform": platform_matches[:20],  # Limit results
                "display": display_matches[:20],
                "count": len(platform_matches)
            }
        }

    except Exception as e:
        logger.error(f"Failed to search symbols: {e}")
        return {
            "status": "error",
            "data": {
                "query": query,
                "platform": [],
                "display": [],
                "count": 0
            },
            "error": str(e)
        }




# User Management Endpoints
@app.get("/api/v2/user/profile")
async def get_user_profile(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get current user profile with credit info for prepaid tier."""
    profile = await current_user.load_profile()

    # Check if Hyperliquid wallet is connected (fast DB check, no external API call)
    hyperliquid_connected = False
    try:
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT hyperliquid_wallet_address IS NOT NULL FROM user_profiles WHERE user_id = %s",
                    (str(current_user.user_id),)
                )
                row = cur.fetchone()
                if row:
                    hyperliquid_connected = row[0]
    except Exception as e:
        logger.warning(f"Failed to check Hyperliquid connection status: {e}")

    # Get credit balance for paid users (needed for prepaid activation check)
    credit_balance_usd = None
    if profile.has_stripe_integration:
        credit_balance_usd = get_user_credit_balance(str(current_user.user_id))

    # Compute effective "can start bot right now" permission
    # For prepaid users: need credits > 0
    # For usage_based/pro: always allowed (they get billed)
    has_available_credits = True
    if profile.is_prepaid_tier:
        has_available_credits = credit_balance_usd is not None and credit_balance_usd > 0

    return {
        "user_id": profile.user_id,
        "subscription_tier": profile.subscription_tier.value,
        "subscription_status": profile.subscription_status.value,
        "can_use_premium_features": profile.can_use_premium_features,
        "requires_own_llm_keys": profile.requires_own_llm_keys,
        "can_publish_telegram_signals": profile.can_publish_telegram_signals,
        "can_use_signal_validation": profile.can_use_signal_validation,
        "can_use_live_trading": profile.can_use_live_trading,
        "can_activate_bots": profile.can_activate_bots,
        "can_use_agents": profile.can_use_agents,
        "paid_data_points": profile.paid_data_points,
        # Credit-related fields for prepaid tier handling
        "credit_balance_usd": credit_balance_usd,
        "has_available_credits": has_available_credits,
        # Live trading connection status
        "hyperliquid_connected": hyperliquid_connected
    }


@app.get("/api/v2/user/indicators")
async def get_user_indicators(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get indicators available to the current user."""
    indicators = await IndicatorService.get_user_available_indicators(current_user.user_id)
    
    return {
        "status": "success",
        "indicators": indicators,
        "count": len(indicators)
    }


@app.get("/api/v2/data-sources-with-points")
async def get_data_sources_with_points(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get all data sources with their data points for frontend configuration."""
    try:
        from core.common.db import get_db_connection
        
        # Get user profile to check paid data points
        profile = await current_user.load_profile()
        paid_data_points = profile.paid_data_points if hasattr(profile, 'paid_data_points') else []
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get all data sources with their data points
                cur.execute("""
                    SELECT 
                        ds.source_id,
                        ds.name as source_name,
                        ds.display_name as source_display_name,
                        ds.description as source_description,
                        ds.enabled as source_enabled,
                        ds.requires_premium as source_requires_premium,
                        ds.sort_order as source_sort_order,
                        dp.data_point_id,
                        dp.name as point_name,
                        dp.display_name as point_display_name,
                        dp.description as point_description,
                        dp.config_values,
                        dp.requires_premium as point_requires_premium,
                        dp.enabled as point_enabled,
                        dp.sort_order as point_sort_order
                    FROM data_sources ds
                    LEFT JOIN data_points dp ON ds.source_id = dp.source_id
                    WHERE ds.enabled = true AND (dp.enabled IS NULL OR dp.enabled = true)
                    ORDER BY ds.sort_order ASC, dp.sort_order ASC
                """)
                
                rows = cur.fetchall()
                
                # Group by data source
                sources_dict = {}
                for row in rows:
                    source_id = row[0]
                    
                    if source_id not in sources_dict:
                        sources_dict[source_id] = {
                            "source_id": source_id,
                            "name": row[1],
                            "display_name": row[2],
                            "description": row[3],
                            "enabled": row[4],
                            "requires_premium": row[5],
                            "sort_order": row[6],
                            "data_points": []
                        }
                    
                    # Add data point if it exists (LEFT JOIN might have nulls)
                    if row[7] is not None:  # data_point_id
                        point_requires_premium = row[12]
                        point_name = row[8]
                        
                        # Check if user has access to this data point
                        has_access = not point_requires_premium or point_name in paid_data_points
                        
                        data_point = {
                            "data_point_id": row[7],
                            "name": point_name,
                            "display_name": row[9],
                            "description": row[10],
                            "config_values": row[11],
                            "requires_premium": point_requires_premium,
                            "enabled": row[13],
                            "sort_order": row[14],
                            "has_access": has_access,
                            "is_locked": point_requires_premium and not has_access
                        }
                        
                        sources_dict[source_id]["data_points"].append(data_point)
                
                # Convert to list and sort
                sources_list = list(sources_dict.values())
                sources_list.sort(key=lambda x: x["sort_order"])
                
                for source in sources_list:
                    source["data_points"].sort(key=lambda x: x["sort_order"])
                
                return {
                    "status": "success",
                    "data_sources": sources_list,
                    "paid_data_points": paid_data_points,
                    "count": len(sources_list)
                }
                
    except Exception as e:
        logger.error(f"Failed to get data sources with points: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get data sources: {str(e)}")


@app.get("/api/v2/llm-models")
async def get_llm_models(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get all available LLM models for OpenRouter."""
    try:
        from core.common.db import get_db_connection

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get all enabled models
                cur.execute("""
                    SELECT
                        model_id,
                        display_name,
                        provider,
                        openrouter_model_id,
                        supports_thinking,
                        enabled,
                        max_context_tokens,
                        context_display,
                        pricing_input_per_1m,
                        pricing_output_per_1m,
                        cost_per_decision_standard,
                        cost_per_decision_thinking,
                        description,
                        sort_order
                    FROM llm_models
                    WHERE enabled = true
                    ORDER BY sort_order ASC
                """)

                rows = cur.fetchall()

                models = []
                for row in rows:
                    models.append({
                        "model_id": row[0],
                        "display_name": row[1],
                        "provider": row[2],
                        "openrouter_model_id": row[3],
                        "supports_thinking": row[4],
                        "enabled": row[5],
                        "max_context_tokens": row[6],
                        "context_display": row[7],
                        "pricing": {
                            "input_per_1m": float(row[8]),
                            "output_per_1m": float(row[9])
                        },
                        "cost_per_decision": {
                            "standard": float(row[10]),
                            "thinking": float(row[11])
                        },
                        "description": row[12],
                        "sort_order": row[13]
                    })

                return {
                    "status": "success",
                    "models": models,
                    "count": len(models)
                }

    except Exception as e:
        logger.error(f"Failed to get LLM models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get LLM models: {str(e)}")


# LLM Credential Management Endpoints
@app.post("/api/v2/user/llm-credentials")
async def store_llm_credential(
    request: Dict[str, str],
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Store a user's LLM API credential securely in Vault."""
    try:
        from core.auth.vault_utils import store_credential
        
        credential_name = request.get("credential_name")
        provider = request.get("provider") 
        api_key = request.get("api_key")
        
        if not all([credential_name, provider, api_key]):
            raise HTTPException(status_code=400, detail="Missing required fields: credential_name, provider, api_key")
        
        if provider not in ["openai", "deepseek", "anthropic", "xai"]:
            raise HTTPException(status_code=400, detail="Invalid provider. Must be one of: openai, deepseek, anthropic, xai")
        
        user_id = current_user.user_id
        credential_id = await store_credential(user_id, credential_name, provider, api_key)
        
        if credential_id is None:
            raise HTTPException(status_code=500, detail="Failed to store credential")
        
        return {
            "status": "success",
            "credential_id": credential_id,
            "message": f"Credential '{credential_name}' stored securely"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store LLM credential: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store credential: {str(e)}")


@app.get("/api/v2/user/llm-credentials")
async def list_llm_credentials(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """List all LLM credentials for the current user (without API keys)."""
    try:
        from core.auth.vault_utils import list_credentials
        
        user_id = current_user.user_id
        credentials = await list_credentials(user_id)
        
        return {
            "status": "success",
            "credentials": credentials,
            "count": len(credentials)
        }
        
    except Exception as e:
        logger.error(f"Failed to list LLM credentials: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list credentials: {str(e)}")


@app.get("/api/v2/user/llm-credentials/{credential_name}")
async def get_llm_credential(
    credential_name: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get a specific LLM credential (with API key for internal use only)."""
    try:
        from core.auth.vault_utils import get_credential
        
        user_id = current_user.user_id
        credential = await get_credential(user_id, credential_name)
        
        if credential is None:
            raise HTTPException(status_code=404, detail=f"Credential '{credential_name}' not found")
        
        return {
            "status": "success",
            "credential": credential
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get LLM credential: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get credential: {str(e)}")


@app.delete("/api/v2/user/llm-credentials/{credential_name}")
async def delete_llm_credential(
    credential_name: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Delete a user's LLM credential."""
    try:
        from core.auth.vault_utils import delete_credential
        
        user_id = current_user.user_id
        success = await delete_credential(user_id, credential_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Credential '{credential_name}' not found")
        
        return {
            "status": "success",
            "message": f"Credential '{credential_name}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete LLM credential: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete credential: {str(e)}")


# Billing & Usage Endpoints
@app.get("/api/v2/billing/usage")
async def get_billing_usage(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Get current billing period LLM token usage for the authenticated user.

    Returns total unreported costs and breakdown by activity type.
    """
    try:
        from core.common.db import get_db_connection

        user_id = current_user.user_id

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get total unreported usage
                cur.execute("""
                    SELECT
                        SUM(platform_cost_usd) as total_cost,
                        SUM(input_tokens) as total_input_tokens,
                        SUM(output_tokens) as total_output_tokens,
                        SUM(reasoning_tokens) as total_reasoning_tokens,
                        COUNT(*) as activity_count
                    FROM activities
                    WHERE user_id = %s
                      AND platform_cost_usd IS NOT NULL
                      AND platform_cost_usd > 0
                      AND stripe_reported = FALSE
                """, (user_id,))

                result = cur.fetchone()
                total_cost = float(result[0]) if result[0] else 0.0
                total_input = int(result[1]) if result[1] else 0
                total_output = int(result[2]) if result[2] else 0
                total_reasoning = int(result[3]) if result[3] else 0
                activity_count = int(result[4]) if result[4] else 0

                # Get breakdown by model
                cur.execute("""
                    SELECT
                        model,
                        provider,
                        thinking_mode,
                        SUM(platform_cost_usd) as cost,
                        SUM(input_tokens) as input_tokens,
                        SUM(output_tokens) as output_tokens,
                        COUNT(*) as call_count
                    FROM activities
                    WHERE user_id = %s
                      AND platform_cost_usd IS NOT NULL
                      AND platform_cost_usd > 0
                      AND stripe_reported = FALSE
                    GROUP BY model, provider, thinking_mode
                    ORDER BY cost DESC
                """, (user_id,))

                model_breakdown = []
                for row in cur.fetchall():
                    model_breakdown.append({
                        "model": row[0],
                        "provider": row[1],
                        "thinking_mode": row[2],
                        "cost_usd": float(row[3]) if row[3] else 0.0,
                        "input_tokens": int(row[4]) if row[4] else 0,
                        "output_tokens": int(row[5]) if row[5] else 0,
                        "call_count": int(row[6])
                    })

                return {
                    "status": "success",
                    "usage": {
                        "total_cost_usd": total_cost,
                        "total_input_tokens": total_input,
                        "total_output_tokens": total_output,
                        "total_reasoning_tokens": total_reasoning,
                        "activity_count": activity_count,
                        "model_breakdown": model_breakdown
                    }
                }

    except Exception as e:
        logger.error(f"Failed to get billing usage: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get billing usage: {str(e)}")


@app.get("/api/v2/billing/usage/breakdown")
async def get_billing_breakdown(
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
    config_id: Optional[str] = None,
    days: int = 30
) -> Dict[str, Any]:
    """
    Get detailed billing breakdown with optional filters.

    Query params:
        - config_id: Filter by specific bot/agent configuration
        - days: Number of days to include (default 30)
    """
    try:
        from core.common.db import get_db_connection
        from datetime import datetime, timedelta

        user_id = current_user.user_id
        start_date = datetime.utcnow() - timedelta(days=days)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Build query with optional config_id filter
                config_filter = "AND config_id = %s" if config_id else ""
                params = [user_id, start_date, config_id] if config_id else [user_id, start_date]

                # Get breakdown by bot/agent
                cur.execute(f"""
                    SELECT
                        a.config_id,
                        c.name as config_name,
                        c.config_type,
                        SUM(a.platform_cost_usd) as total_cost,
                        SUM(a.input_tokens) as input_tokens,
                        SUM(a.output_tokens) as output_tokens,
                        COUNT(*) as call_count,
                        MIN(a.created_at) as first_activity,
                        MAX(a.created_at) as last_activity
                    FROM activities a
                    LEFT JOIN configurations c ON a.config_id = c.config_id
                    WHERE a.user_id = %s
                      AND a.created_at >= %s
                      AND a.platform_cost_usd IS NOT NULL
                      AND a.platform_cost_usd > 0
                      {config_filter}
                    GROUP BY a.config_id, c.name, c.config_type
                    ORDER BY total_cost DESC
                """, params)

                bot_breakdown = []
                for row in cur.fetchall():
                    bot_breakdown.append({
                        "config_id": row[0],
                        "config_name": row[1],
                        "config_type": row[2],
                        "total_cost_usd": float(row[3]) if row[3] else 0.0,
                        "input_tokens": int(row[4]) if row[4] else 0,
                        "output_tokens": int(row[5]) if row[5] else 0,
                        "call_count": int(row[6]),
                        "first_activity": row[7].isoformat() if row[7] else None,
                        "last_activity": row[8].isoformat() if row[8] else None
                    })

                # Get daily aggregation
                cur.execute(f"""
                    SELECT
                        DATE(created_at) as date,
                        SUM(platform_cost_usd) as daily_cost,
                        SUM(input_tokens) as input_tokens,
                        SUM(output_tokens) as output_tokens,
                        COUNT(*) as call_count
                    FROM activities
                    WHERE user_id = %s
                      AND created_at >= %s
                      AND platform_cost_usd IS NOT NULL
                      AND platform_cost_usd > 0
                      {config_filter}
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """, params)

                daily_breakdown = []
                for row in cur.fetchall():
                    daily_breakdown.append({
                        "date": row[0].isoformat() if row[0] else None,
                        "cost_usd": float(row[1]) if row[1] else 0.0,
                        "input_tokens": int(row[2]) if row[2] else 0,
                        "output_tokens": int(row[3]) if row[3] else 0,
                        "call_count": int(row[4])
                    })

                return {
                    "status": "success",
                    "breakdown": {
                        "by_bot": bot_breakdown,
                        "by_day": daily_breakdown,
                        "days": days,
                        "config_id": config_id
                    }
                }

    except Exception as e:
        logger.error(f"Failed to get billing breakdown: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get billing breakdown: {str(e)}")


# =============================================================================
# Hyperliquid Live Trading Setup
# =============================================================================

@app.post("/api/v2/hyperliquid/setup")
async def setup_hyperliquid_account(
    request: Dict[str, str],
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Store Hyperliquid API wallet credentials and verify account exists.

    Request body:
        - api_wallet_key: API wallet private key (hex, with or without 0x prefix)
        - wallet_address: User's main Hyperliquid wallet address (0x...)
    """
    try:
        api_wallet_key = request.get("api_wallet_key", "").strip()
        wallet_address = request.get("wallet_address", "").strip()

        # Validate wallet address format
        if not re.match(r"^0x[a-fA-F0-9]{40}$", wallet_address):
            raise HTTPException(
                status_code=400,
                detail="Invalid wallet address. Should be a valid Ethereum address (0x...)"
            )

        # Validate private key format (with or without 0x prefix)
        if not re.match(r"^(0x)?[a-fA-F0-9]{64}$", api_wallet_key):
            raise HTTPException(
                status_code=400,
                detail="Invalid API wallet key format. Should be 64 hex characters."
            )

        # Verify account exists on Hyperliquid by querying user_state
        try:
            from hyperliquid.info import Info
            from hyperliquid.utils import constants

            info = Info(constants.MAINNET_API_URL, skip_ws=True)
            user_state = info.user_state(wallet_address)
            margin_summary = user_state.get("marginSummary", {})
            account_value = float(margin_summary.get("accountValue", 0))

            logger.bind(user_id=current_user.user_id).info(
                f"Hyperliquid account verified: ${account_value:.2f}"
            )
        except Exception as verify_err:
            logger.bind(user_id=current_user.user_id).warning(
                f"Could not verify Hyperliquid account (proceeding anyway): {verify_err}"
            )
            account_value = 0

        # Store credentials in Vault
        from core.auth.vault_utils import VaultManager
        success = await VaultManager.store_hyperliquid_credential(
            user_id=current_user.user_id,
            api_wallet_private_key=api_wallet_key,
            wallet_address=wallet_address
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to store Hyperliquid credentials"
            )

        logger.bind(user_id=current_user.user_id).info("Hyperliquid account connected successfully")

        # Auto-create live bot slot if none exists (idempotent for reconnections)
        live_config_id = None
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT config_id FROM configurations
                    WHERE user_id = %s AND trading_mode = 'hyperliquid' LIMIT 1
                """, (current_user.user_id,))
                existing = cur.fetchone()

                if existing:
                    live_config_id = str(existing[0])
                else:
                    live_config_id = str(uuid.uuid4())
                    cur.execute("""
                        INSERT INTO configurations
                        (config_id, user_id, config_type, config_name, config_data,
                         trading_mode, initial_equity, state, created_at, updated_at)
                        VALUES (%s, %s, 'scheduled_trading', %s, %s,
                                'hyperliquid', %s, 'inactive', NOW(), NOW())
                    """, (live_config_id, current_user.user_id,
                          'Your Live ggbot', json.dumps({}), account_value))
                    conn.commit()
                    logger.bind(user_id=current_user.user_id).info(
                        f"Created live bot slot {live_config_id} (equity: ${account_value:.2f})"
                    )
                    # Log bot_created activity for timeline
                    from core.common.activity_logger import log_activity_safe
                    log_activity_safe(
                        config_id=live_config_id,
                        user_id=current_user.user_id,
                        activity_type='bot_created',
                        activity_source='system',
                        summary=f"Live trading bot created (${account_value:.2f} equity)",
                        details={
                            'trading_mode': 'hyperliquid',
                            'initial_equity': float(account_value),
                        },
                        importance=7
                    )

        return {
            "status": "success",
            "message": "Hyperliquid account connected successfully",
            "account_value": account_value,
            "live_config_id": live_config_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to setup Hyperliquid account: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to setup Hyperliquid account: {str(e)}"
        )


@app.get("/api/v2/hyperliquid/status")
async def get_hyperliquid_status(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Check Hyperliquid connection status and live balance."""
    try:
        from core.auth.vault_utils import VaultManager

        credentials = await VaultManager.get_hyperliquid_credential(current_user.user_id)

        if not credentials:
            return {
                "connected": False,
                "wallet_address": None,
                "account_value": None,
                "margin_used": None,
                "open_notional": None,
                "withdrawable": None,
                "positions_count": None
            }

        wallet_address = credentials.get("wallet_address")

        # Query live balance from Hyperliquid
        try:
            from hyperliquid.info import Info
            from hyperliquid.utils import constants

            info = Info(constants.MAINNET_API_URL, skip_ws=True)
            user_state = info.user_state(wallet_address)

            margin_summary = user_state.get("marginSummary", {})
            account_value = float(margin_summary.get("accountValue", 0))
            total_margin_used = float(margin_summary.get("totalMarginUsed", 0))
            total_ntl_pos = float(margin_summary.get("totalNtlPos", 0))
            withdrawable = float(user_state.get("withdrawable", 0))

            # Count open positions
            positions = user_state.get("assetPositions", [])
            positions_count = sum(
                1 for p in positions
                if float(p.get("position", {}).get("szi", 0)) != 0
            )

            return {
                "connected": True,
                "wallet_address": wallet_address,
                "account_value": round(account_value, 2),
                "margin_used": round(total_margin_used, 2),
                "open_notional": round(total_ntl_pos, 2),
                "withdrawable": round(withdrawable, 2),
                "positions_count": positions_count
            }

        except Exception as info_err:
            logger.bind(user_id=current_user.user_id).warning(
                f"Could not query Hyperliquid balance: {info_err}"
            )
            return {
                "connected": True,
                "wallet_address": wallet_address,
                "account_value": None,
                "margin_used": None,
                "open_notional": None,
                "withdrawable": None,
                "positions_count": None
            }

    except Exception as e:
        logger.error(f"Failed to check Hyperliquid status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check Hyperliquid status: {str(e)}"
        )


@app.post("/api/v2/hyperliquid/disconnect")
async def disconnect_hyperliquid_account(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Disconnect Hyperliquid account and disable all hyperliquid trading bots.

    This will:
    - Remove Hyperliquid credentials from Vault
    - Set all user's hyperliquid bots to paper mode
    """
    try:
        from core.auth.vault_utils import VaultManager

        success = await VaultManager.delete_hyperliquid_credential(current_user.user_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to disconnect Hyperliquid account"
            )

        logger.bind(user_id=current_user.user_id).info("Hyperliquid account disconnected")

        return {
            "status": "success",
            "message": "Hyperliquid account disconnected. All hyperliquid bots have been set to paper mode."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect Hyperliquid account: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disconnect Hyperliquid account: {str(e)}"
        )


@app.post("/api/v2/hyperliquid/test-trade")
async def test_hyperliquid_trade(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Execute a minimal test trade on Hyperliquid to verify credentials work.

    Opens a tiny ETH long (0.001 ETH), waits 2s, then closes it.
    """
    try:
        import asyncio
        from trading.live.hyperliquid_service import HyperliquidLiveTradingService

        service = HyperliquidLiveTradingService()

        # Get exchange instance to verify credentials
        exchange = await service._get_exchange(current_user.user_id)
        if not exchange:
            raise HTTPException(
                status_code=400,
                detail="Hyperliquid credentials not configured. Please connect your account first."
            )

        # Set leverage to 3x cross before trading
        try:
            exchange.update_leverage(3, "ETH", is_cross=True)
            logger.bind(user_id=current_user.user_id).info("Set ETH leverage to 3x cross")
        except Exception as lev_err:
            logger.bind(user_id=current_user.user_id).warning(f"Leverage set warning (may already be set): {lev_err}")

        # Open minimal ETH long (0.01 ETH ~ $25 notional)
        test_size = 0.01
        logger.bind(user_id=current_user.user_id).info(f"Executing test trade: {test_size} ETH long")
        order_result = exchange.market_open("ETH", True, test_size, slippage=0.05)

        logger.bind(user_id=current_user.user_id).info(f"market_open response: {order_result}")

        if order_result.get("status") != "ok":
            logger.bind(user_id=current_user.user_id).error(f"Test trade open failed: {order_result}")
            return {
                "status": "failed",
                "error": f"Market order failed: {order_result}"
            }

        # Extract fill price — check for errors in statuses
        statuses = order_result.get("response", {}).get("data", {}).get("statuses", [])
        entry_price = 0
        fill_error = None
        for status in statuses:
            if "filled" in status:
                entry_price = float(status["filled"]["avgPx"])
                break
            if "error" in status:
                fill_error = status["error"]
                break

        if fill_error:
            logger.bind(user_id=current_user.user_id).error(f"Test trade fill error: {fill_error}")
            return {
                "status": "failed",
                "error": f"Order rejected: {fill_error}"
            }

        if entry_price == 0:
            logger.bind(user_id=current_user.user_id).error(f"No fill found in statuses: {statuses}")
            return {
                "status": "failed",
                "error": f"Order not filled. Statuses: {statuses}"
            }

        logger.bind(user_id=current_user.user_id).info(f"Test trade opened at ${entry_price:.2f}")

        # Wait for settlement
        await asyncio.sleep(2)

        # Close the position
        close_result = exchange.market_close("ETH")
        logger.bind(user_id=current_user.user_id).info(f"market_close response: {close_result}")

        close_status = "unknown"
        if close_result:
            close_status = close_result.get("status", "unknown")
            # Check for close errors in statuses
            close_statuses = close_result.get("response", {}).get("data", {}).get("statuses", [])
            for cs in close_statuses:
                if "error" in cs:
                    close_status = f"error: {cs['error']}"
                    break

        logger.bind(user_id=current_user.user_id).info(f"Test trade closed: {close_status}")

        return {
            "status": "success",
            "entry_price": entry_price,
            "close_status": close_status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute test trade: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute test trade: {str(e)}"
        )


@app.post("/api/v2/positions/hyperliquid/{batch_id}/close")
async def close_hyperliquid_position(
    batch_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Close a Hyperliquid position by batch_id."""
    try:
        from core.common.db import get_db_connection

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT lt.config_id, c.user_id, lt.symbol
                    FROM live_trades lt
                    JOIN configurations c ON lt.config_id = c.config_id
                    WHERE lt.batch_id = %s AND lt.provider = 'hyperliquid' AND lt.closed_at IS NULL
                """, (batch_id,))
                result = cur.fetchone()

                if not result:
                    raise HTTPException(status_code=404, detail="Position not found or already closed")

                config_id, user_id, trade_symbol = result
                if str(user_id) != current_user.user_id:
                    raise HTTPException(status_code=403, detail="Unauthorized")

        _check_dojo_lock(str(config_id))

        from trading.live.hyperliquid_service import HyperliquidLiveTradingService
        hl_service = HyperliquidLiveTradingService()
        close_result = await hl_service.close_position(batch_id, current_user.user_id)

        if close_result.get("status") != "success":
            raise HTTPException(
                status_code=500,
                detail=close_result.get("reason", "Failed to close position")
            )

        # Mirror close to arena (fire-and-forget)
        try:
            from trading.virtuals.arena_sync import mirror_close_to_arena
            asyncio.create_task(mirror_close_to_arena(
                config_id=str(config_id),
                symbol=trade_symbol,
                close_reason='manual',
                user_id=current_user.user_id,
            ))
        except Exception:
            pass

        # Mirror close to Dojo match accounts (fire-and-forget)
        try:
            from core.arena.dojo_mirror import mirror_close_to_dojo
            asyncio.create_task(mirror_close_to_dojo(
                config_id=str(config_id),
                symbol=trade_symbol,
                close_reason='manual',
            ))
        except Exception:
            pass

        return close_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to close Hyperliquid position: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to close Hyperliquid position: {str(e)}"
        )


# Bot Data Endpoints for Dashboard
@app.get("/api/v2/bot/{config_id}/metrics")
async def get_bot_metrics(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get performance metrics for a bot configuration."""
    try:
        from core.common.db import get_db_connection
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Query paper account summary
                cur.execute("""
                    SELECT initial_balance, current_balance, total_pnl, 
                           total_trades, win_trades, loss_trades
                    FROM paper_accounts 
                    WHERE config_id = %s AND user_id = %s
                """, (config_id, current_user.user_id))
                
                account = cur.fetchone()
                if not account:
                    # Return default metrics if no account exists yet
                    return {
                        "status": "success",
                        "config_id": config_id,
                        "account": {
                            "balance": PAPER_INITIAL_BALANCE,
                            "total_pnl": 0.0
                        },
                        "performance": {
                            "total_trades": 0,
                            "win_rate": 0.0,
                            "avg_trade": 0.0
                        }
                    }
                
                # Calculate additional metrics from paper_trades
                cur.execute("""
                    SELECT AVG(realized_pnl) as avg_trade,
                           COUNT(*) as closed_trades,
                           AVG(EXTRACT(EPOCH FROM (closed_at - opened_at))/3600) as avg_duration_hours
                    FROM paper_trades 
                    WHERE config_id = %s AND user_id = %s AND status = 'closed'
                """, (config_id, current_user.user_id))
                
                trade_stats = cur.fetchone()
                
                win_rate = float(account['win_trades']) / float(account['total_trades']) if account['total_trades'] > 0 else 0.0
                
                return {
                    "status": "success",
                    "config_id": config_id,
                    "account": {
                        "balance": float(account['current_balance']),
                        "total_pnl": float(account['total_pnl'])
                    },
                    "performance": {
                        "total_trades": account['total_trades'],
                        "win_trades": account['win_trades'],
                        "loss_trades": account['loss_trades'],
                        "win_rate": round(win_rate, 3),
                        "avg_trade": float(trade_stats['avg_trade'] or 0) if trade_stats else 0.0
                    }
                }
                
    except Exception as e:
        logger.error(f"Failed to get bot metrics for {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bot metrics")


@app.get("/api/v2/bot/{config_id}/positions")
async def get_bot_positions(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get live positions for a bot configuration (paper or Hyperliquid)."""
    try:
        from core.common.db import get_db_connection

        # Check trading mode
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        config_dict = config.to_jsonb() if hasattr(config, 'to_jsonb') else {}
        trading_mode = config_dict.get('trading_mode', 'paper')

        if trading_mode == 'hyperliquid':
            # Fetch positions from Hyperliquid Info API
            from trading.live.hyperliquid_service import HyperliquidLiveTradingService
            hl_service = HyperliquidLiveTradingService()
            hl_positions = await hl_service.get_open_positions(config_id, current_user.user_id)

            positions = []
            for pos in hl_positions:
                positions.append({
                    "symbol": pos.get('symbol'),
                    "side": pos.get('side'),
                    "size": float(pos.get('size', 0)) * float(pos.get('entry_price', 0)),
                    "entryPrice": float(pos.get('entry_price', 0)),
                    "currentPrice": float(pos.get('entry_price', 0)),  # Updated via SSE
                    "unrealizedPnL": float(pos.get('unrealized_pnl', 0)),
                    "liquidationPrice": float(pos.get('liquidation_price', 0)),
                    "leverage": pos.get('leverage'),
                    "marginType": pos.get('margin_type', 'cross'),
                    "source": "hyperliquid"
                })

            return {
                "status": "success",
                "config_id": config_id,
                "positions": positions
            }

        # Default: paper trading positions
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT trade_id, symbol, side, entry_price, current_price, size_usd,
                           unrealized_pnl, leverage, opened_at
                    FROM paper_trades
                    WHERE config_id = %s AND user_id = %s AND status = 'open'
                    ORDER BY opened_at DESC
                """, (config_id, current_user.user_id))

                rows = cur.fetchall()

        # Enrich with current prices from Redis (position monitor writes there)
        if rows:
            try:
                from trading.paper.supabase_service import enrich_positions_from_redis
                enrich_positions_from_redis(rows)
            except Exception:
                pass  # Fallback: use DB values

        positions = []
        for row in rows:
            side_display = "LONG" if row['side'].lower() == 'buy' else "SHORT"
            positions.append({
                "symbol": row['symbol'],
                "side": side_display,
                "size": float(row['size_usd']),
                "entryPrice": float(row['entry_price']),
                "currentPrice": float(row.get('current_price') or row['entry_price']),
                "unrealizedPnL": float(row.get('unrealized_pnl') or 0),
                "timestamp": row['opened_at'].isoformat() + "Z"
            })

        return {
            "status": "success",
            "config_id": config_id,
            "positions": positions
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get bot positions for {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bot positions")


@app.get("/api/v2/bot/{config_id}/trades")
async def get_bot_trades(
    config_id: str,
    limit: int = 100,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get trade history for a bot configuration."""
    try:
        from core.common.db import get_db_connection

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT trade_id, symbol, side, entry_price, size_usd, realized_pnl,
                           opened_at, closed_at, confidence_score, status
                    FROM paper_trades
                    WHERE config_id = %s AND user_id = %s
                    ORDER BY opened_at DESC
                    LIMIT %s
                """, (config_id, current_user.user_id, limit))
                
                trades = []
                for row in cur.fetchall():
                    trades.append({
                        "id": str(row['trade_id']),
                        "symbol": row['symbol'],
                        "side": row['side'],
                        "quantity": float(row['size_usd']),
                        "price": float(row['entry_price']),
                        "pnl": float(row['realized_pnl'] or 0),
                        "timestamp": row['opened_at'].isoformat() + "Z",
                        "closed_at": row['closed_at'].isoformat() + "Z" if row['closed_at'] else None,
                        "confidence": float(row['confidence_score'] or 0),
                        "status": row['status']
                    })
                
                return {
                    "status": "success", 
                    "config_id": config_id,
                    "trades": trades,
                    "count": len(trades)
                }
                
    except Exception as e:
        logger.error(f"Failed to get bot trades for {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bot trades")


@app.get("/api/v2/bot/{config_id}/account")
async def get_bot_account(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Get account summary for a bot configuration (paper or Hyperliquid).

    Returns comprehensive account metrics including total equity,
    performance percentage, and margin details.
    """
    try:
        from core.common.db import get_db_connection
        from core.domain.metrics_calculator import AccountMetricsCalculator
        from decimal import Decimal

        # Check trading mode
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        config_dict = config.to_jsonb() if hasattr(config, 'to_jsonb') else {}
        trading_mode = config_dict.get('trading_mode', 'paper')

        if trading_mode == 'hyperliquid':
            # Fetch account from Hyperliquid Info API
            from trading.live.hyperliquid_service import HyperliquidLiveTradingService
            hl_service = HyperliquidLiveTradingService()
            metrics = await hl_service.get_account_metrics(config_id, current_user.user_id)

            if metrics.get('status') != 'success':
                return {
                    "status": "success",
                    "config_id": config_id,
                    "account": {
                        "initial_balance": 0.0,
                        "current_balance": 0.0,
                        "available_balance": 0.0,
                        "margin_used": 0.0,
                        "total_pnl": 0.0,
                        "unrealized_pnl": 0.0,
                        "realized_pnl": 0.0,
                        "total_equity": 0.0,
                        "performance_percent": 0.0,
                        "open_positions": 0,
                        "total_trades": 0,
                        "win_trades": 0,
                        "loss_trades": 0,
                        "win_rate": 0.0,
                        "source": "hyperliquid"
                    }
                }

            account_value = metrics.get('balance', 0)
            available = metrics.get('available_balance', 0)
            unrealized_pnl = metrics.get('total_unrealized_pnl', 0)
            positions = metrics.get('positions', [])
            margin_used = account_value - available

            # Pull trade stats from latest account_snapshot (computed by adapter)
            snapshot_stats = {}
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT total_trades, win_trades, loss_trades, win_rate,
                                   realized_pnl, total_pnl
                            FROM account_snapshots
                            WHERE config_id = %s AND trading_mode = 'hyperliquid'
                            ORDER BY timestamp DESC LIMIT 1
                        """, (config_id,))
                        row = cur.fetchone()
                        if row:
                            snapshot_stats = {
                                'total_trades': row[0] or 0,
                                'win_trades': row[1] or 0,
                                'loss_trades': row[2] or 0,
                                'win_rate': float(row[3] or 0),
                                'realized_pnl': float(row[4] or 0),
                                'total_pnl': float(row[5] or 0),
                            }
            except Exception as e:
                logger.warning(f"Failed to fetch HL snapshot stats: {e}")

            # Get initial_equity + cost_basis (initial + deposits - withdrawals)
            initial_equity = None
            cost_basis = None
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT initial_equity FROM configurations WHERE config_id = %s", (config_id,))
                        row = cur.fetchone()
                        if row and row[0]:
                            initial_equity = float(row[0])

                        # Compute cost_basis from deposits/withdrawals
                        if initial_equity:
                            cur.execute("""
                                SELECT
                                    COALESCE(SUM(CASE WHEN activity_type = 'deposit' THEN (details->>'amount_usdc')::numeric ELSE 0 END), 0),
                                    COALESCE(SUM(CASE WHEN activity_type = 'withdrawal' THEN (details->>'amount_usdc')::numeric ELSE 0 END), 0)
                                FROM activities
                                WHERE config_id = %s AND activity_type IN ('deposit', 'withdrawal')
                            """, (config_id,))
                            transfer_row = cur.fetchone()
                            total_deposits = float(transfer_row[0]) if transfer_row else 0.0
                            total_withdrawals = float(transfer_row[1]) if transfer_row else 0.0
                            cost_basis = initial_equity + total_deposits - total_withdrawals
            except Exception:
                pass

            total_equity = account_value
            performance_pct = 0.0
            denominator = cost_basis or initial_equity
            if denominator and denominator > 0:
                performance_pct = ((total_equity - denominator) / denominator) * 100

            realized_pnl_val = snapshot_stats.get('realized_pnl', 0.0)
            total_pnl_val = realized_pnl_val + unrealized_pnl

            return {
                "status": "success",
                "config_id": config_id,
                "account": {
                    "initial_balance": cost_basis or initial_equity or account_value,
                    "current_balance": account_value,
                    "available_balance": available,
                    "margin_used": margin_used,
                    "total_pnl": total_pnl_val,
                    "unrealized_pnl": unrealized_pnl,
                    "realized_pnl": realized_pnl_val,
                    "total_equity": total_equity,
                    "performance_percent": performance_pct,
                    "open_positions": len(positions),
                    "total_trades": snapshot_stats.get('total_trades', 0),
                    "win_trades": snapshot_stats.get('win_trades', 0),
                    "loss_trades": snapshot_stats.get('loss_trades', 0),
                    "win_rate": snapshot_stats.get('win_rate', 0.0),
                    "source": "hyperliquid"
                }
            }

        # Default: paper trading account
        from trading.paper.supabase_service import SupabasePaperTradingService
        service = SupabasePaperTradingService()

        # Get account summary
        account_summary = await service.get_account_summary(config_id)

        if "error" in account_summary:
            return {
                "status": "success",
                "config_id": config_id,
                "account": {
                    "initial_balance": PAPER_INITIAL_BALANCE,
                    "current_balance": PAPER_INITIAL_BALANCE,
                    "available_balance": PAPER_INITIAL_BALANCE,
                    "margin_used": 0.0,
                    "total_pnl": 0.0,
                    "unrealized_pnl": 0.0,
                    "realized_pnl": 0.0,
                    "total_equity": PAPER_INITIAL_BALANCE,
                    "performance_percent": 0.0,
                    "open_positions": 0,
                    "total_trades": 0,
                    "win_trades": 0,
                    "loss_trades": 0,
                    "win_rate": 0.0
                }
            }

        # Extract base metrics
        initial_balance = Decimal(str(account_summary.get("initial_balance", PAPER_INITIAL_BALANCE)))
        current_balance = Decimal(str(account_summary.get("current_balance", PAPER_INITIAL_BALANCE)))
        total_pnl = Decimal(str(account_summary.get("total_pnl", 0.0)))

        # Get unrealized P&L from Redis (position monitor writes there), margin from DB
        unrealized_pnl = Decimal('0')
        margin_used = Decimal('0')
        try:
            from trading.paper.supabase_service import get_config_unrealized_pnl
            redis_pnl = get_config_unrealized_pnl(config_id)
            if redis_pnl is not None:
                unrealized_pnl = Decimal(str(redis_pnl))
        except Exception:
            pass  # Fall through to DB query

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if unrealized_pnl == Decimal('0'):
                    # Redis miss — fall back to DB
                    cur.execute("""
                        SELECT
                            COALESCE(SUM(unrealized_pnl), 0) as unrealized_pnl,
                            COALESCE(SUM(margin_used), 0) as margin_used
                        FROM paper_trades
                        WHERE config_id = %s AND status = 'open'
                    """, (config_id,))
                    position_data = cur.fetchone()
                    unrealized_pnl = Decimal(str(position_data[0])) if position_data else Decimal('0')
                    margin_used = Decimal(str(position_data[1])) if position_data else Decimal('0')
                else:
                    # Got PnL from Redis, still need margin_used from DB (static per position)
                    cur.execute("""
                        SELECT COALESCE(SUM(margin_used), 0) as margin_used
                        FROM paper_trades
                        WHERE config_id = %s AND status = 'open'
                    """, (config_id,))
                    margin_data = cur.fetchone()
                    margin_used = Decimal(str(margin_data[0])) if margin_data else Decimal('0')

        # Calculate metrics using centralized calculator
        total_equity = AccountMetricsCalculator.calculate_total_equity(
            current_balance,
            unrealized_pnl
        )

        available_balance = AccountMetricsCalculator.calculate_available_balance(
            current_balance,
            margin_used
        )

        realized_pnl = AccountMetricsCalculator.calculate_realized_pnl(
            total_pnl,
            unrealized_pnl
        )

        performance_percent = AccountMetricsCalculator.calculate_performance_percent(
            total_equity,
            initial_balance
        )

        return {
            "status": "success",
            "config_id": config_id,
            "account": {
                "initial_balance": float(initial_balance),
                "current_balance": float(current_balance),
                "available_balance": float(available_balance),
                "margin_used": float(margin_used),
                "total_pnl": float(total_pnl),
                "unrealized_pnl": float(unrealized_pnl),
                "realized_pnl": float(realized_pnl),
                "total_equity": float(total_equity),
                "performance_percent": float(performance_percent) if performance_percent is not None else 0.0,
                "open_positions": account_summary.get("open_positions", 0),
                "total_trades": account_summary.get("total_trades", 0),
                "win_trades": account_summary.get("win_trades", 0),
                "loss_trades": account_summary.get("loss_trades", 0),
                "win_rate": account_summary.get("win_rate", 0.0)
            }
        }

    except Exception as e:
        logger.error(f"Failed to get account for {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get account")


@app.get("/api/v2/bot/{config_id}/decisions")
async def get_bot_decisions(
    config_id: str,
    limit: int = 50,
    hours_back: int = 24,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get decision history for a bot configuration."""
    try:
        from core.common.db import get_db_connection
        
        # Validate config belongs to user
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Query decisions for this config in the last N hours, ordered by newest first
                cur.execute("""
                    SELECT 
                        decision_id,
                        symbol,
                        action,
                        status,
                        confidence,
                        reasoning,
                        prompt,
                        market_data,
                        decision_data,
                        created_at
                    FROM decisions 
                    WHERE config_id = %s 
                        AND user_id = %s
                        AND created_at >= NOW() - make_interval(hours => %s)
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (config_id, current_user.user_id, hours_back, limit))
                
                rows = cur.fetchall()
                
                # Transform database rows to API format
                decisions = []
                for row in rows:
                    decisions.append({
                        "decision_id": str(row['decision_id']),
                        "symbol": row['symbol'],
                        "action": row['action'],
                        "status": row['status'],
                        "confidence": float(row['confidence']) if row['confidence'] else 0.0,
                        "reasoning": row['reasoning'],
                        "prompt": row['prompt'],
                        "market_data": row['market_data'],
                        "decision_data": row['decision_data'],
                        "created_at": row['created_at'].isoformat() if row['created_at'] else None
                    })
                
                logger.info(f"✅ Retrieved {len(decisions)} decisions for config {config_id}")
                
                return {
                    "status": "success",
                    "config_id": config_id,
                    "decisions": decisions,
                    "count": len(decisions),
                    "filters": {
                        "limit": limit,
                        "hours_back": hours_back
                    }
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get decisions for {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get decisions")


# Agent Trade Execution Endpoint
@app.post("/api/v2/agent/execute-trade")
async def agent_execute_trade(
    request: Dict[str, Any],
    user_id: str = Query(...),
    x_service_auth: Optional[str] = Header(None, alias="X-Service-Auth")
) -> Dict[str, Any]:
    """
    Execute trade for agent with optional position sizing overrides.

    This endpoint is called by autonomous agents via MCP tools.
    Supports position size and leverage overrides for agent decision-making.

    Args:
        request: Trade execution request with:
            - config_id: Bot configuration ID
            - symbol: Trading symbol (any format accepted)
            - side: "long" or "short"
            - confidence: Optional confidence score (0.0-1.0, default 0.7)
            - stop_loss_price: Optional stop loss price
            - take_profit_price: Optional take_profit price
            - decision_id: Optional decision UUID to link
            - position_size_override: Optional position size in base asset (e.g., 0.005 BTC)
            - position_size_usd_override: Optional total position size in USD NOTIONAL (e.g., 500)
                                          Note: This is the FULL POSITION SIZE, not margin/collateral
                                          Example: 1000 with 10x leverage = $1000 position using $100 margin
            - leverage_override: Optional leverage (e.g., 15)
        user_id: User ID (passed as query param by service client)
        x_service_auth: Service authentication header

    Returns:
        Trade execution result with status, trade_id/batch_id, etc.
    """
    try:
        # Service authentication check (same as signal-listener pattern)
        if x_service_auth != "agent-runner":
            raise HTTPException(status_code=401, detail="Unauthorized service")

        # Extract required fields
        config_id = request.get("config_id")
        symbol = request.get("symbol")
        side = request.get("side")

        if not config_id or not symbol or not side:
            raise HTTPException(status_code=400, detail="Missing required fields: config_id, symbol, side")

        # Validate config belongs to user
        config = await config_service.get_config(config_id, user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Build trade intent with overrides
        intent = {
            "config_id": config_id,
            "user_id": user_id,
            "symbol": symbol,
            "action": side,  # "long" or "short"
            "confidence": request.get("confidence", 0.7),
            "stop_loss_price": request.get("stop_loss_price"),
            "take_profit_price": request.get("take_profit_price"),
            "decision_id": request.get("decision_id"),
            # Agent override parameters
            "position_size_override": request.get("position_size_override"),
            "position_size_usd_override": request.get("position_size_usd_override"),
            "leverage_override": request.get("leverage_override")
        }

        # Route to appropriate trading service based on trading_mode
        trading_mode = getattr(config, 'trading_mode', 'paper')

        if trading_mode == 'hyperliquid':
            result = await orchestrator.hyperliquid_trading.execute_trade_intent(intent)
            return {
                "status": "success",
                "message": "Trade executed on Hyperliquid",
                "trade": {
                    "batch_id": result.get("batch_id"),
                    "status": result.get("status")
                }
            }
        else:
            # Paper trading
            result = await orchestrator.paper_trading.execute_trade_intent(intent)
            return {
                "status": "success",
                "message": "Paper trade executed",
                "trade": {
                    "trade_id": result.get("trade_id"),
                    "entry_price": result.get("entry_price"),
                    "size_usd": result.get("size_usd"),
                    "status": result.get("status")
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent trade execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Trade execution failed: {str(e)}")


# Bot Lifecycle Endpoints (placeholders for now)
@app.post("/api/v2/bot/{config_id}/start")
async def start_bot(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Start a bot by scheduling its autonomous trading cycle."""
    try:
        # Get bot configuration
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # =====================================================================
        # PERMISSION CHECK: Verify user can activate bots
        # =====================================================================
        user_profile = await user_service.get_profile(current_user.user_id)
        if not user_profile.can_activate_bots:
            raise HTTPException(
                status_code=403,
                detail="Subscription required to activate bots. Please subscribe to start your bot."
            )

        # For prepaid users, also check they have available credits
        if user_profile.is_prepaid_tier:
            credit_balance = get_user_credit_balance(str(current_user.user_id))
            if credit_balance <= 0:
                logger.warning(
                    f"Blocking bot start for prepaid user {current_user.user_id} - "
                    f"no credits available (balance: ${credit_balance:.2f})"
                )
                raise HTTPException(
                    status_code=402,  # Payment Required
                    detail="Insufficient credits. Please add credits to activate your bot."
                )
        # =====================================================================

        # =====================================================================
        # CONFIG VALIDATION: Ensure bot has a trading pair configured
        # =====================================================================
        if not config.selected_pair:
            raise HTTPException(
                status_code=400,
                detail="Configure a trading pair before starting this bot."
            )
        # =====================================================================

        # =====================================================================
        # HYPERLIQUID-SPECIFIC CHECKS
        # =====================================================================
        if config.trading_mode == 'hyperliquid':
            # 1. Credential check — user must have completed Hyperliquid setup
            from core.auth.vault_utils import VaultManager
            hl_credentials = await VaultManager.get_hyperliquid_credential(current_user.user_id)
            if not hl_credentials:
                raise HTTPException(
                    status_code=400,
                    detail="Live trading not set up. Connect your wallet in Settings first."
                )

            # 2. Single live bot safety net — only one live bot per user
            from core.common.db import get_db_connection
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT config_id FROM configurations
                        WHERE user_id = %s AND trading_mode = 'hyperliquid'
                        AND state = 'active' AND config_id != %s
                    """, (str(current_user.user_id), config_id))
                    conflict = cur.fetchone()
            if conflict:
                raise HTTPException(
                    status_code=400,
                    detail="You already have an active live bot. Stop it before starting another."
                )
        # =====================================================================

        # Check if already active
        current_state = await config_service.get_bot_state(config_id, current_user.user_id)
        if current_state == 'active':
            return {
                "status": "already_active",
                "message": "Bot is already running",
                "config_id": config_id
            }
        
        # Extract timeframe from config
        config_dict = config.to_jsonb()
        timeframe = extract_timeframe_from_config(config_dict)

        # Set state to active — scheduler process detects within 10s and adds job
        success = await config_service.set_bot_state(config_id, current_user.user_id, 'active')
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update bot state")

        # Calculate next run for API response (no scheduler needed)
        if timeframe == "signal_driven":
            next_run = None
        else:
            next_run = calculate_next_run(timeframe)
        
        # 🔥 WEBSOCKET DELETED! Bot state changes will show up in SSE stream
        
        return {
            "status": "started",
            "config_id": config_id,
            "timeframe": timeframe,
            "next_run": next_run,
            "message": f"Bot scheduled for {timeframe} trading"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start bot {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start bot: {str(e)}")


@app.post("/api/v2/bot/{config_id}/stop")
async def stop_bot(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Stop a bot by setting state to inactive. Scheduler detects within 10s."""
    _check_dojo_lock(config_id)
    try:
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Check if already inactive
        current_state = await config_service.get_bot_state(config_id, current_user.user_id)
        if current_state == 'inactive':
            return {
                "status": "already_stopped",
                "message": "Bot is already stopped",
                "config_id": config_id
            }

        # Extract timeframe for response
        config_dict = config.to_jsonb()
        timeframe = extract_timeframe_from_config(config_dict)

        # Set state to inactive — scheduler process detects and removes job within 10s
        success = await config_service.set_bot_state(config_id, current_user.user_id, 'inactive')
        if not success:
            logger.warning(f"Failed to update state for bot {config_id}")

        return {
            "status": "stopped",
            "config_id": config_id,
            "timeframe": timeframe,
            "message": "Bot stopped successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop bot {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop bot: {str(e)}")


@app.post("/api/v2/bot/{config_id}/promote-to-live")
async def promote_to_live(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Promote a paper bot's strategy to the user's single live trading bot."""
    try:
        # 1. Get source config and validate
        source = await config_service.get_config(config_id, current_user.user_id)
        if not source:
            raise HTTPException(status_code=404, detail="Configuration not found")

        if source.trading_mode == 'hyperliquid':
            raise HTTPException(status_code=400, detail="This bot is already live")

        # 2. Permission check — subscription required
        profile = await user_service.get_profile(current_user.user_id)
        if not profile.can_activate_bots:
            raise HTTPException(
                status_code=403,
                detail="Subscription required to use live trading."
            )

        # 3. Find the user's live bot (created during Hyperliquid setup)
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT config_id FROM configurations
                    WHERE user_id = %s AND trading_mode = 'hyperliquid' LIMIT 1
                """, (current_user.user_id,))
                existing = cur.fetchone()

        if not existing:
            raise HTTPException(
                status_code=400,
                detail="No live trading bot found. Connect Hyperliquid in Settings first."
            )

        live_config_id = str(existing[0])

        # 4. Build config_data from source — copy strategy fields only
        live_config_data = {
            "schema_version": source.schema_version,
            "selected_pair": source.selected_pair,
            "extraction": source.extraction,
            "decision": source.decision,
            "trading": source.trading,
            "llm_config": source.llm_config,
            "telegram_integration": {},
        }

        # 5. Update the live bot's strategy
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE configurations
                    SET config_data = %s, updated_at = NOW()
                    WHERE config_id = %s AND user_id = %s
                """, (json.dumps(live_config_data), live_config_id, current_user.user_id))
                conn.commit()

        # 6. Log strategy_updated activity with version number
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM activities
                    WHERE config_id = %s AND activity_type = 'strategy_updated'
                """, (live_config_id,))
                version = cur.fetchone()[0] + 1

        from core.common.activity_logger import log_activity_safe
        log_activity_safe(
            config_id=live_config_id,
            user_id=current_user.user_id,
            activity_type='strategy_updated',
            activity_source='user_action',
            summary=f"Strategy promoted from '{source.config_name}'",
            details={
                'version': version,
                'source_config_id': config_id,
                'source_config_name': source.config_name,
                'config_snapshot': live_config_data,
                'changed_fields': ['selected_pair', 'extraction', 'decision', 'llm_config', 'trading'],
            },
            importance=8
        )

        logger.info(f"Promoted bot {config_id} to live {live_config_id} (v{version})")

        return {
            "status": "promoted",
            "live_config_id": live_config_id,
            "version": version,
            "source_config_id": config_id,
            "message": f"Strategy v{version} promoted from '{source.config_name}'"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to promote bot {config_id} to live: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to promote to live: {str(e)}")


@app.post("/api/v2/bot/{config_id}/reset-account")
async def reset_account(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Reset paper trading account to initial state.

    Closes all open positions, resets balance to $10k, clears all stats,
    but preserves trade history for analysis. Sets last_reset_at timestamp
    to distinguish current run metrics from historical data.
    """
    _check_dojo_lock(config_id)
    try:
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Initialize paper trading service
        paper_trading = SupabasePaperTradingService()

        # Execute reset
        result = await paper_trading.reset_account(config_id, current_user.user_id)

        if result['status'] == 'failed':
            raise HTTPException(status_code=500, detail=result.get('reason', 'Reset failed'))

        logger.info(f"Account reset successful for config_id={config_id}, user_id={current_user.user_id}")

        return {
            "status": "success",
            "config_id": config_id,
            "positions_closed": result.get('positions_closed', 0),
            "new_balance": result.get('new_balance', PAPER_INITIAL_BALANCE),
            "reset_at": result.get('reset_at'),
            "message": result.get('message', 'Account reset successfully')
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset account {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset account: {str(e)}")


@app.post("/api/v2/bot/{config_id}/arena/register")
async def register_for_arena(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Register a bot for ggArena Season 1 competition.

    Requirements:
    - User must own the bot
    - Bot must be in 'active' state
    - User must have active subscription (usage-based)

    Sets is_public_performance = true for the configuration.
    Account will be reset to $10k when competition starts (Jan 21).
    """
    try:
        # 1. Verify user owns this configuration
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # 2. Verify bot is active
        if config.state != 'active':
            raise HTTPException(
                status_code=400,
                detail="Bot must be active to enter the Arena. Start your bot first."
            )

        # 3. Verify user has active subscription
        profile = await user_service.get_profile(current_user.user_id)
        if not profile or not profile.can_use_premium_features:
            raise HTTPException(
                status_code=403,
                detail="Arena registration requires an active subscription."
            )

        # 4. Set is_public_performance = true and record registration time
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE configurations
                    SET is_public_performance = true,
                        arena_registered_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE config_id = %s AND user_id = %s
                """, (config_id, current_user.user_id))
                conn.commit()

        # 5. If competition has started, reset account to $10k immediately
        from datetime import datetime, timezone
        competition_start = datetime(2026, 1, 21, 12, 0, 0, tzinfo=timezone.utc)
        account_reset = False

        if datetime.now(timezone.utc) >= competition_start:
            try:
                from trading.paper.supabase_service import SupabasePaperTradingService
                paper_trading = SupabasePaperTradingService()
                reset_result = await paper_trading.reset_account(config_id, current_user.user_id)
                account_reset = reset_result.get('status') == 'success'
                logger.info(f"Late arena entry - account reset: config_id={config_id}, success={account_reset}")
            except Exception as e:
                logger.error(f"Failed to reset account for late arena entry: {e}")

        logger.info(f"Bot registered for Arena: config_id={config_id}, user_id={current_user.user_id}, account_reset={account_reset}")

        if account_reset:
            return {
                "status": "success",
                "config_id": config_id,
                "message": "You're in! Your account has been reset to $10,000. Good luck!",
                "competition_start": "2026-01-21T12:00:00Z",
                "account_reset": True
            }
        else:
            return {
                "status": "success",
                "config_id": config_id,
                "message": "Your bot is registered for ggArena Season 1! Account will be reset to $10,000 on January 21st.",
                "competition_start": "2026-01-21T12:00:00Z",
                "account_reset": False
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register bot for arena {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post("/api/v2/bot/{config_id}/arena/unregister")
async def unregister_from_arena(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Remove bot from ggArena competition.

    Sets is_public_performance = false for the configuration.
    """
    try:
        # 1. Verify user owns this configuration
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # 2. Set is_public_performance = false
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE configurations
                    SET is_public_performance = false, updated_at = CURRENT_TIMESTAMP
                    WHERE config_id = %s AND user_id = %s
                """, (config_id, current_user.user_id))
                conn.commit()

        logger.info(f"Bot unregistered from Arena: config_id={config_id}, user_id={current_user.user_id}")

        return {
            "status": "success",
            "config_id": config_id,
            "message": "Your bot has been removed from ggArena Season 1."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unregister bot from arena {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Unregistration failed: {str(e)}")


# =============================================================================
# Arena Season 2 Registration
# =============================================================================

@app.post("/api/v2/arena/season/{season_id}/register")
async def register_for_arena_s2(
    season_id: int,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Register a bot for ggArena Season 2.

    Requirements:
    - Season must be in 'registration' phase
    - User must own the bot
    - Bot must be active and in paper trading mode
    - User must have active subscription
    """
    from core.arena.seasons import SEASONS, is_registration_open

    season = SEASONS.get(season_id)
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    if not is_registration_open(season_id):
        from core.arena.seasons import get_season_phase
        phase = get_season_phase(season_id)
        if phase == 'training':
            raise HTTPException(status_code=400, detail=f"Registration opens {season['registration_start'].strftime('%B %d')}.")
        elif phase == 'competition':
            raise HTTPException(status_code=400, detail="Registration is closed. Competition is underway.")
        else:
            raise HTTPException(status_code=400, detail="Registration is closed for this season.")

    body = await request.json()
    config_id = body.get("config_id")
    if not config_id:
        raise HTTPException(status_code=400, detail="config_id is required")

    try:
        # Verify user owns config
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Must be active
        if config.state != 'active':
            raise HTTPException(status_code=400, detail="Bot must be active to enter the Arena. Start your bot first.")

        # Must be paper trading
        if config.trading_mode != 'paper':
            raise HTTPException(status_code=400, detail="Only paper trading bots can enter the Arena.")

        # Must have subscription
        profile = await user_service.get_profile(current_user.user_id)
        if not profile or not profile.can_use_premium_features:
            raise HTTPException(status_code=403, detail="Arena registration requires an active subscription.")

        # Insert registration
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO arena_registrations (season_id, config_id, user_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (season_id, config_id) DO UPDATE
                    SET unregistered_at = NULL, registered_at = NOW()
                    RETURNING id
                """, (season_id, config_id, current_user.user_id))
                reg_id = cur.fetchone()[0]
                conn.commit()

        logger.info(f"Bot registered for Arena S{season_id}: config_id={config_id}, user_id={current_user.user_id}")

        return {
            "status": "success",
            "registration_id": str(reg_id),
            "config_id": config_id,
            "season_id": season_id,
            "message": f"Your bot is registered for {season['name']}! Strategy is now locked."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register bot for arena S{season_id}: {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post("/api/v2/arena/season/{season_id}/unregister")
async def unregister_from_arena_s2(
    season_id: int,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Unregister a bot from ggArena Season 2.

    Only allowed during registration phase (not during competition).
    Soft-deletes by setting unregistered_at timestamp.
    """
    from core.arena.seasons import SEASONS, get_season_phase

    season = SEASONS.get(season_id)
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    phase = get_season_phase(season_id)
    if phase == 'competition':
        raise HTTPException(status_code=400, detail="Cannot unregister during competition. Strategy is frozen.")
    if phase == 'completed':
        raise HTTPException(status_code=400, detail="Season is completed. Cannot modify registrations.")

    body = await request.json()
    config_id = body.get("config_id")
    if not config_id:
        raise HTTPException(status_code=400, detail="config_id is required")

    try:
        # Verify user owns config
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Set unregistered_at
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE arena_registrations
                    SET unregistered_at = NOW()
                    WHERE season_id = %s AND config_id = %s AND user_id = %s AND unregistered_at IS NULL
                    RETURNING id
                """, (season_id, config_id, current_user.user_id))
                result = cur.fetchone()
                conn.commit()

        if not result:
            raise HTTPException(status_code=404, detail="No active registration found for this bot.")

        logger.info(f"Bot unregistered from Arena S{season_id}: config_id={config_id}, user_id={current_user.user_id}")

        return {
            "status": "success",
            "config_id": config_id,
            "season_id": season_id,
            "message": f"Your bot has been removed from {season['name']}. Strategy is now unlocked."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unregister bot from arena S{season_id}: {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Unregistration failed: {str(e)}")


# =============================================================================
# Arena USX Pledges (Staking on Bot Competition)
# =============================================================================

@app.post("/api/v2/arena/pledge")
async def record_arena_pledge(
    request: Request,
) -> Dict[str, Any]:
    """
    Record a USX staking pledge on an arena bot (public endpoint).

    No auth required — wallet_address is the identity.
    Called after the user completes on-chain staking (USX → sUSX vault).
    Records which bot they're backing for prize distribution.

    Request body:
    {
        "wallet_address": "0x...",
        "config_id": "uuid",
        "usx_amount": "100.50",
        "susx_amount": "95.25",  # optional
        "tx_hash": "0x..."
    }
    """
    try:
        data = await request.json()

        wallet_address = data.get('wallet_address')
        config_id = data.get('config_id')
        usx_amount = data.get('usx_amount')
        susx_amount = data.get('susx_amount')  # Optional
        tx_hash = data.get('tx_hash')

        # Validate required fields
        if not all([wallet_address, config_id, usx_amount, tx_hash]):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: wallet_address, config_id, usx_amount, tx_hash"
            )

        # Basic wallet address validation
        if not wallet_address.startswith('0x') or len(wallet_address) != 42:
            raise HTTPException(
                status_code=400,
                detail="Invalid wallet address format"
            )

        # Basic tx_hash validation
        if not tx_hash.startswith('0x') or len(tx_hash) != 66:
            raise HTTPException(
                status_code=400,
                detail="Invalid transaction hash format"
            )

        # Validate config_id is a public arena bot
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT config_id, config_name
                    FROM configurations
                    WHERE config_id = %s AND is_public_performance = true
                """, (config_id,))
                bot = cur.fetchone()

                if not bot:
                    raise HTTPException(
                        status_code=404,
                        detail="Bot not found or not in Arena competition"
                    )

                bot_name = bot[1]

                # Insert pledge record (user_id nullable for public endpoint)
                cur.execute("""
                    INSERT INTO arena_pledges
                        (wallet_address, config_id, usx_amount, susx_amount, tx_hash)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (tx_hash) DO NOTHING
                    RETURNING id
                """, (
                    wallet_address,
                    config_id,
                    usx_amount,
                    susx_amount,
                    tx_hash
                ))
                result = cur.fetchone()
                conn.commit()

                if not result:
                    # tx_hash already exists
                    logger.warning(f"Duplicate pledge tx_hash: {tx_hash}")
                    return {
                        "status": "duplicate",
                        "message": "This transaction has already been recorded"
                    }

                pledge_id = result[0]

        logger.info(
            f"Arena pledge recorded: wallet={wallet_address[:10]}..., "
            f"bot={config_id}, amount={usx_amount} USX, tx={tx_hash[:16]}..."
        )

        return {
            "status": "success",
            "pledge_id": str(pledge_id),
            "bot_name": bot_name,
            "usx_amount": usx_amount,
            "message": f"You're backing {bot_name} with {usx_amount} USX!"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record arena pledge: {e}")
        raise HTTPException(status_code=500, detail=f"Pledge recording failed: {str(e)}")


@app.get("/api/v2/arena/pledges")
async def get_user_pledges(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Get all arena pledges for the current user.

    Returns list of bots they've staked on with amounts.
    """
    try:
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        p.id,
                        p.config_id,
                        c.config_name,
                        c.profile_image_url,
                        p.usx_amount,
                        p.susx_amount,
                        p.tx_hash,
                        p.pledged_at,
                        p.unstaked_at
                    FROM arena_pledges p
                    JOIN configurations c ON p.config_id = c.config_id
                    WHERE p.user_id = %s
                    ORDER BY p.pledged_at DESC
                """, (current_user.user_id,))
                pledges = cur.fetchall()

        return {
            "status": "success",
            "pledges": [
                {
                    "id": str(row[0]),
                    "config_id": str(row[1]),
                    "bot_name": row[2],
                    "profile_image_url": row[3],
                    "usx_amount": float(row[4]),
                    "susx_amount": float(row[5]) if row[5] else None,
                    "tx_hash": row[6],
                    "pledged_at": row[7].isoformat() if row[7] else None,
                    "unstaked": row[8] is not None
                }
                for row in pledges
            ],
            "total_pledged": sum(float(row[4]) for row in pledges)
        }

    except Exception as e:
        logger.error(f"Failed to get user pledges: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch pledges: {str(e)}")


@app.get("/api/v2/scheduler/status")
async def get_scheduler_status(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get scheduler status from DB (scheduler runs in separate process)."""
    try:
        from core.common.db import get_db_connection

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Count user's active bots
                cur.execute("""
                    SELECT config_id, config_data
                    FROM configurations
                    WHERE user_id = %s AND state = 'active' AND (config_type = 'scheduled_trading' OR config_type IS NULL)
                """, (str(current_user.user_id),))
                rows = cur.fetchall()

                jobs_info = []
                for config_id, config_data in rows:
                    tf = extract_timeframe_from_config(config_data)
                    if tf and tf != 'signal_driven':
                        jobs_info.append({
                            "config_id": str(config_id),
                            "timeframe": tf,
                            "next_run": calculate_next_run(tf),
                        })

                # Total active bots across all users
                cur.execute("""
                    SELECT COUNT(*) FROM configurations
                    WHERE state = 'active' AND (config_type = 'scheduled_trading' OR config_type IS NULL)
                """)
                total_active = cur.fetchone()[0]

        return {
            "status": "success",
            "scheduler_running": True,  # Separate process managed by PM2
            "active_jobs": jobs_info,
            "job_count": len(jobs_info),
            "total_active_bots": total_active
        }

    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")


@app.post("/api/v2/scheduler/reconcile")
async def manual_reconcile(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Scheduler reconciliation happens automatically every 10s in ggbot_scheduler."""
    return {
        "status": "success",
        "message": "Reconciliation is automatic (10s interval in ggbot_scheduler process)"
    }


@app.get("/api/v2/bot/{config_id}/status")
async def get_bot_status(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get bot status derived from DB state (scheduler runs in separate process)."""
    try:
        state = await config_service.get_bot_state(config_id, current_user.user_id)
        config = await config_service.get_config(config_id, current_user.user_id)

        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        config_dict = config.to_jsonb()
        timeframe = extract_timeframe_from_config(config_dict)
        is_active = state == 'active'
        next_run = calculate_next_run(timeframe) if is_active and timeframe != 'signal_driven' else None

        return {
            "status": "success",
            "config_id": config_id,
            "bot_status": state or "inactive",
            "is_scheduled": is_active and timeframe != 'signal_driven',
            "next_run": next_run,
            "timeframe": timeframe,
            "scheduler_job_exists": is_active
        }
        
    except Exception as e:
        logger.error(f"Failed to get bot status for {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get bot status: {str(e)}")


# =============================================================================
# MARKET CONDITIONS (Sebastian AI Research Agent)
# =============================================================================

SEBASTIAN_API_KEY = os.getenv('SEBASTIAN_API_KEY')


async def verify_sebastian_auth(request: Request):
    """Authenticate Sebastian's service requests via dedicated API key."""
    auth_header = request.headers.get('authorization', '')
    if not auth_header.startswith('Bearer ') or not SEBASTIAN_API_KEY:
        raise HTTPException(status_code=401, detail="Authentication required")
    token = auth_header.split(' ', 1)[1]
    if token != SEBASTIAN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/api/v2/market-conditions/latest")
async def get_market_conditions_latest(request: Request):
    """
    Get the latest market conditions report.

    Sebastian reads this before producing the next report to maintain
    temporal context (trends, changes vs previous state).
    """
    await verify_sebastian_auth(request)

    try:
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, generated_at, schema_version, regime, domains,
                           narratives, synthesis, data_quality, raw_tables, created_at
                    FROM market_conditions
                    ORDER BY generated_at DESC
                    LIMIT 1
                """)
                row = cur.fetchone()

                if not row:
                    return {"status": "empty", "message": "No market conditions reports yet"}

                return {
                    "status": "ok",
                    "report": {
                        "id": str(row[0]),
                        "generated_at": row[1].isoformat() if row[1] else None,
                        "schema_version": row[2],
                        "regime": row[3],
                        "domains": row[4],
                        "narratives": row[5],
                        "synthesis": row[6],
                        "data_quality": row[7],
                        "raw_tables": row[8],
                        "created_at": row[9].isoformat() if row[9] else None,
                    }
                }
    except Exception as e:
        logger.error(f"Failed to get market conditions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v2/market-conditions")
async def post_market_conditions(request: Request):
    """
    Create a new market conditions report.

    Sebastian POSTs structured JSON after his daily research pass.
    The report is stored in Supabase and cached in Redis for
    fast consumption by the MI pipeline.
    """
    await verify_sebastian_auth(request)

    try:
        body = await request.json()

        # Validate required fields
        required = ['generated_at', 'regime', 'domains', 'narratives', 'synthesis']
        missing = [f for f in required if f not in body]
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing required fields: {missing}")

        # Validate regime structure
        regime = body['regime']
        if not isinstance(regime, dict) or 'overall' not in regime:
            raise HTTPException(status_code=400, detail="regime must be a dict with 'overall' key")

        # Insert into Supabase
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO market_conditions
                        (generated_at, schema_version, regime, domains, narratives,
                         synthesis, data_quality, raw_tables)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, created_at
                """, (
                    body['generated_at'],
                    body.get('schema_version', '0.1'),
                    json.dumps(body['regime']),
                    json.dumps(body['domains']),
                    json.dumps(body['narratives']),
                    body['synthesis'],
                    json.dumps(body.get('data_quality')) if body.get('data_quality') else None,
                    json.dumps(body.get('raw_tables')) if body.get('raw_tables') else None,
                ))
                result = cur.fetchone()
                conn.commit()

        report_id = str(result[0])

        # Cache in Redis for fast MI pipeline access
        try:
            import redis as sync_redis
            r = sync_redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            cache_data = {
                'generated_at': body['generated_at'],
                'schema_version': body.get('schema_version', '0.1'),
                'regime': body['regime'],
                'domains': body['domains'],
                'narratives': body['narratives'],
                'synthesis': body['synthesis'],
                'data_quality': body.get('data_quality'),
                'raw_tables': body.get('raw_tables'),
            }
            r.set('market_conditions:latest', json.dumps(cache_data, default=str), ex=86400)  # 24h TTL
            r.close()
        except Exception as e:
            logger.warning(f"Failed to cache market conditions in Redis: {e}")

        logger.info(f"Market conditions report stored: {report_id} (regime: {regime.get('overall', 'unknown')})")

        return {
            "status": "ok",
            "id": report_id,
            "created_at": result[1].isoformat() if result[1] else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store market conditions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# STRIPE INTEGRATION
# =============================================================================

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Request models
class CheckoutRequest(BaseModel):
    plan: str  # 'usage', 'monthly', or 'annual'
    coupon: Optional[str] = None


class CreditPurchaseRequest(BaseModel):
    amount_cents: int  # Amount in cents: 1000 = $10, 2500 = $25, etc.

@app.post("/api/v2/create-checkout-session")
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Create Stripe Checkout session for subscription upgrade."""

    # Map plan to price ID
    price_ids = {
        'usage': os.environ.get('STRIPE_PRICE_ID_USAGE'),
        'monthly': os.environ.get('STRIPE_PRICE_ID_MONTHLY'),
    }

    # Add annual if available
    if os.environ.get('STRIPE_PRICE_ID_ANNUAL'):
        price_ids['annual'] = os.environ['STRIPE_PRICE_ID_ANNUAL']

    if request.plan not in price_ids or not price_ids[request.plan]:
        raise HTTPException(400, f"Invalid plan: {request.plan}")

    try:
        # Get or create Stripe customer
        customer_id = await get_or_create_stripe_customer(current_user.user_id, current_user.email)

        # CRITICAL: Check if customer already has an active subscription
        # Prevents duplicate subscriptions from double-clicks or page refreshes
        existing_subs = stripe.Subscription.list(
            customer=customer_id,
            status='active',
            limit=1
        )
        if existing_subs.data:
            existing_sub = existing_subs.data[0]
            logger.bind(user_id=str(current_user.user_id)).warning(
                f"User already has active subscription {existing_sub.id}, blocking duplicate creation"
            )
            raise HTTPException(
                400,
                "You already have an active subscription. Manage it from your billing portal."
            )

        # Build line items - metered billing doesn't use quantity
        if request.plan == 'usage':
            line_items = [{'price': price_ids[request.plan]}]
        else:
            line_items = [{'price': price_ids[request.plan], 'quantity': 1}]

        # Build checkout session params
        checkout_params = {
            'customer': customer_id,
            'mode': 'subscription',
            'line_items': line_items,
            'success_url': f"{os.environ['FRONTEND_URL']}/success?session_id={{CHECKOUT_SESSION_ID}}",
            'cancel_url': f"{os.environ['FRONTEND_URL']}/forge",
            'client_reference_id': str(current_user.user_id),
            'subscription_data': {
                'metadata': {
                    'user_id': str(current_user.user_id),
                    'plan': request.plan
                }
            },
            'metadata': {
                'user_id': str(current_user.user_id)
            },
            'allow_promotion_codes': request.plan != 'usage',  # No promos for usage plan
        }

        # Add trial only for monthly/annual plans (not usage-based)
        if request.plan in ['monthly', 'annual']:
            checkout_params['subscription_data']['trial_period_days'] = 14

        # Add coupon if provided
        if request.coupon:
            checkout_params['discounts'] = [{'coupon': request.coupon}]

        # Create Stripe Checkout session
        session = stripe.checkout.Session.create(**checkout_params)

        logger.bind(user_id=str(current_user.user_id)).info(
            f"Created Stripe checkout session: {session.id} for plan: {request.plan}"
        )

        return {'checkout_url': session.url}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout: {e}")
        raise HTTPException(500, f"Payment system error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(500, "Internal server error")


@app.post("/api/v2/stripe-webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""

    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    webhook_secret = os.environ['STRIPE_WEBHOOK_SECRET']

    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        logger.error("Invalid webhook payload")
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid webhook signature")
        raise HTTPException(400, "Invalid signature")

    # Log webhook event
    logger.info(f"Received Stripe webhook: {event['type']}")

    # Handle different event types
    event_type = event['type']

    if event_type == 'checkout.session.completed':
        await handle_checkout_completed(event['data']['object'])

    elif event_type == 'customer.subscription.updated':
        await handle_subscription_updated(event['data']['object'])

    elif event_type == 'customer.subscription.deleted':
        await handle_subscription_deleted(event['data']['object'])

    elif event_type == 'invoice.payment_failed':
        await handle_payment_failed(event['data']['object'])

    return {'received': True}


@app.post("/api/v2/create-portal-session")
async def create_portal_session(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Create Stripe billing portal session."""

    from core.common.db import get_db_connection

    # Get Stripe customer ID from database
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT stripe_customer_id
                FROM user_profiles
                WHERE user_id = %s
            """, (str(current_user.user_id),))
            result = cur.fetchone()

    if not result or not result[0]:
        raise HTTPException(404, "No active subscription found. Please upgrade first.")

    customer_id = result[0]

    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{os.environ['FRONTEND_URL']}/forge",
        )

        logger.bind(user_id=str(current_user.user_id)).info(
            f"Created billing portal session for customer: {customer_id}"
        )

        return {'portal_url': session.url}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating portal session: {e}")
        raise HTTPException(500, f"Error accessing billing portal: {str(e)}")


# =============================================================================
# WEBHOOK HANDLERS
# =============================================================================

async def handle_checkout_completed(session):
    """Handle successful checkout - activate subscription and/or create credit grant."""
    from core.common.db import get_db_connection

    metadata = session.get('metadata', {})
    user_id = metadata.get('user_id')
    customer_id = session['customer']
    subscription_id = session.get('subscription')  # May be None for payment mode

    # Check if this is a credit purchase
    is_credit_purchase = metadata.get('type') == 'credit_purchase'

    if is_credit_purchase:
        # Create Stripe Credit Grant
        amount_cents = int(metadata.get('amount_cents', 0))
        if amount_cents > 0:
            try:
                stripe.billing.CreditGrant.create(
                    customer=customer_id,
                    name=f"${amount_cents / 100:.0f} Credit Pack",
                    applicability_config={
                        'scope': {'price_type': 'metered'}
                    },
                    category='paid',
                    amount={
                        'type': 'monetary',
                        'monetary': {
                            'value': amount_cents,
                            'currency': 'usd'
                        }
                    }
                )
                logger.bind(user_id=user_id).info(
                    f"Credit grant created: ${amount_cents / 100:.2f}"
                )

                # Clear credit notification state so user can receive future alerts
                from core.monitoring.usage_monitor import clear_credit_notification_state
                clear_credit_notification_state(user_id)

            except stripe.error.StripeError as e:
                logger.error(f"Failed to create credit grant: {e}")
                # Don't raise - subscription still needs to be processed

    # Handle subscription activation if present (new subscriber or regular upgrade)
    if subscription_id:
        # Get plan from subscription_data metadata
        plan = session.get('subscription_data', {}).get('metadata', {}).get('plan', 'usage')

        # Map plan to subscription tier
        tier_map = {
            'usage': 'usage_based',
            'monthly': 'pro',
            'annual': 'pro'
        }
        subscription_tier = tier_map.get(plan, 'usage_based')

        # For ongoing subscriptions, subscription_expires_at should be NULL
        # Only set expiration date when subscription is cancelled
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE user_profiles
                    SET subscription_tier = %s,
                        subscription_status = 'active',
                        stripe_customer_id = %s,
                        stripe_subscription_id = %s,
                        subscription_expires_at = NULL,
                        updated_at = NOW()
                    WHERE user_id = %s
                """, (subscription_tier, customer_id, subscription_id, user_id))
                conn.commit()

        # Set $10 billing threshold for usage-based plans to limit bad debt exposure
        # Must be set on the subscription object, not during checkout creation
        if plan == 'usage':
            try:
                stripe.Subscription.modify(
                    subscription_id,
                    billing_thresholds={'amount_gte': 1000}  # $10.00 in cents
                )
                logger.bind(user_id=user_id).info("Set $10 billing threshold on usage subscription")
            except stripe.error.StripeError as e:
                logger.warning(f"Failed to set billing threshold (non-critical): {e}")

        logger.bind(user_id=user_id).info(
            f"Subscription activated: tier={subscription_tier}, plan={plan}, Customer: {customer_id}, Subscription: {subscription_id}"
        )
    elif is_credit_purchase:
        # Payment mode (no subscription) - credit pack purchase
        # For free/expired users, upgrade them to prepaid tier
        # For existing active paid users, keep their tier (credits just add to balance)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get current tier and check if subscription is expired
                cur.execute("""
                    SELECT subscription_tier, subscription_status, subscription_expires_at
                    FROM user_profiles WHERE user_id = %s
                """, (user_id,))
                result = cur.fetchone()
                current_tier = result[0] if result else 'free'
                current_status = result[1] if result else None
                expires_at = result[2] if result else None

                # Check if subscription is expired
                from datetime import datetime, timezone
                is_expired = (
                    expires_at is not None and
                    expires_at <= datetime.now(timezone.utc)
                )

                # Upgrade to prepaid if free tier OR has expired subscription
                if current_tier == 'free' or is_expired:
                    # Upgrade to prepaid tier
                    # Clear subscription_expires_at since prepaid doesn't expire (credits do)
                    cur.execute("""
                        UPDATE user_profiles
                        SET subscription_tier = 'prepaid',
                            subscription_status = 'active',
                            subscription_expires_at = NULL,
                            stripe_customer_id = %s,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (customer_id, user_id))
                    logger.bind(user_id=user_id).info(
                        f"Upgraded to prepaid tier (was {current_tier}, expired={is_expired}): Customer: {customer_id}"
                    )
                else:
                    # Existing active paid user - just ensure customer_id is set
                    cur.execute("""
                        UPDATE user_profiles
                        SET stripe_customer_id = %s,
                            updated_at = NOW()
                        WHERE user_id = %s AND stripe_customer_id IS NULL
                    """, (customer_id, user_id))
                    logger.bind(user_id=user_id).info(
                        f"Credit purchase completed (existing {current_tier} subscriber): Customer: {customer_id}"
                    )
                conn.commit()


async def handle_subscription_updated(subscription):
    """Handle subscription updates."""
    from core.common.db import get_db_connection

    subscription_id = subscription['id']
    status = subscription['status']

    # Map Stripe status to our status
    status_map = {
        'active': 'active',
        'canceled': 'cancelled',
        'past_due': 'past_due',
        'unpaid': 'past_due',
        'incomplete': 'past_due'
    }

    our_status = status_map.get(status, 'active')

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE user_profiles
                SET subscription_status = %s,
                    updated_at = NOW()
                WHERE stripe_subscription_id = %s
            """, (our_status, subscription_id))
            conn.commit()

    logger.info(f"Subscription updated: {subscription_id}, status: {our_status}")


async def handle_subscription_deleted(subscription):
    """Handle subscription cancellation."""
    from core.common.db import get_db_connection
    from datetime import datetime

    subscription_id = subscription['id']
    cancel_at = datetime.fromtimestamp(subscription['ended_at'])

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE user_profiles
                SET subscription_tier = 'free',
                    subscription_status = 'cancelled',
                    subscription_expires_at = %s,
                    updated_at = NOW()
                WHERE stripe_subscription_id = %s
            """, (cancel_at, subscription_id))
            conn.commit()

    logger.info(f"Subscription cancelled: {subscription_id}, access until: {cancel_at}")


async def handle_payment_failed(invoice):
    """
    Handle failed payment - mark user as past_due and pause their bots.

    This is triggered by Stripe's invoice.payment_failed webhook, including
    when billing thresholds ($10 cap) trigger an invoice that fails.
    """
    from core.common.db import get_db_connection

    subscription_id = invoice['subscription']
    customer_id = invoice.get('customer')
    amount_due = invoice.get('amount_due', 0) / 100  # Convert cents to dollars

    user_id = None
    user_email = None
    paused_bots = []

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Update user status and get user_id
            cur.execute("""
                UPDATE user_profiles
                SET subscription_status = 'past_due',
                    updated_at = NOW()
                WHERE stripe_subscription_id = %s
                RETURNING user_id
            """, (subscription_id,))
            result = cur.fetchone()

            if result:
                user_id = str(result[0])

                # Pause all active bots for this user
                cur.execute("""
                    UPDATE configurations
                    SET state = 'inactive', updated_at = NOW()
                    WHERE user_id = %s AND state = 'active'
                    RETURNING config_id, config_name
                """, (user_id,))
                paused_bots = cur.fetchall()

                # Get user email for notification
                cur.execute(
                    "SELECT email FROM auth.users WHERE id = %s",
                    (user_id,)
                )
                email_result = cur.fetchone()
                user_email = email_result[0] if email_result else None

            conn.commit()

    # Log the action
    if paused_bots:
        logger.warning(
            f"⚠️ Payment failed for subscription {subscription_id}: "
            f"${amount_due:.2f} - Paused {len(paused_bots)} bots for user {user_id}"
        )

        # Notify via Redis pub/sub for real-time updates
        try:
            import redis
            redis_client = redis.from_url(
                os.getenv('REDIS_URL', 'redis://localhost:6379'),
                decode_responses=True
            )
            for config_id, config_name in paused_bots:
                redis_client.publish("bot_lifecycle", json.dumps({
                    "action": "pause",
                    "config_id": str(config_id),
                    "user_id": user_id,
                    "reason": "payment_failed"
                }))
        except Exception as e:
            logger.error(f"Failed to publish bot pause event: {e}")
    else:
        logger.warning(f"Payment failed for subscription: {subscription_id} (${amount_due:.2f})")

    # Send email notification to user
    if user_email:
        try:
            from core.services.resend_service import resend_service

            bot_names = [name or 'Unnamed Bot' for _, name in paused_bots] if paused_bots else []
            bot_list_html = "".join([f"<li>{name}</li>" for name in bot_names[:5]])
            if len(bot_names) > 5:
                bot_list_html += f"<li>...and {len(bot_names) - 5} more</li>"

            message = f"""
            <p>We were unable to process your payment of <strong>${amount_due:.2f}</strong>.</p>

            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Amount Due:</strong> ${amount_due:.2f}</p>
                <p style="margin: 5px 0;"><strong>Status:</strong> Payment Declined</p>
            </div>

            {"<p><strong>The following bots have been paused:</strong></p><ul>" + bot_list_html + "</ul>" if bot_list_html else ""}

            <p>Please update your payment method to resume your bots. Your bots will remain paused until payment is successful.</p>
            """

            resend_service.send_generic_notification(
                user_email=user_email,
                title="Payment Failed - Bots Paused",
                message=message,
                action_text="Update Payment Method",
                action_url="https://app.ggbots.ai/settings",
                notification_type="error"
            )
            logger.info(f"📧 Sent payment failed email to {user_email}")

        except Exception as e:
            logger.error(f"Failed to send payment failed email: {e}")


# =============================================================================
# CREDITS ENDPOINTS
# =============================================================================

def get_stripe_customer_id(user_id: str) -> str | None:
    """Get Stripe customer ID from database (read-only, doesn't create)."""
    from core.common.db import get_db_connection

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT stripe_customer_id
                FROM user_profiles
                WHERE user_id = %s
            """, (user_id,))
            result = cur.fetchone()

    return result[0] if result and result[0] else None


def has_usage_based_subscription(user_id: str) -> bool:
    """Check if user has an active usage_based subscription."""
    from core.common.db import get_db_connection

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT subscription_tier, subscription_status
                FROM user_profiles
                WHERE user_id = %s
            """, (user_id,))
            result = cur.fetchone()

    if not result:
        return False

    tier, status = result
    # User has usage_based subscription if tier is usage_based and status is active
    return tier == 'usage_based' and status == 'active'


def get_user_credit_balance(user_id: str) -> float:
    """
    Get user's available credit balance from Stripe.

    Returns the net balance (credits - usage) in USD.
    Used for permission checks before bot activation.
    """
    customer_id = get_stripe_customer_id(user_id)
    if not customer_id:
        return 0.0

    try:
        summary = stripe.billing.CreditBalanceSummary.retrieve(
            customer=customer_id,
            filter={
                'type': 'applicability_scope',
                'applicability_scope': {'price_type': 'metered'}
            }
        )

        if summary.balances and len(summary.balances) > 0:
            balance = summary.balances[0]
            available = balance.available_balance.monetary.value / 100 if balance.available_balance else 0
            return available
        return 0.0

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error checking credit balance for {user_id}: {e}")
        return 0.0  # Fail closed - assume no credits if we can't check


@app.get("/api/v2/credits/balance")
async def get_credit_balance(current_user: AuthenticatedUser = Depends(get_current_user_v2)):
    """Get user's credit balance from Stripe Credit Grants."""
    customer_id = get_stripe_customer_id(str(current_user.user_id))

    if not customer_id:
        return {'available_usd': 0.0, 'ledger_usd': 0.0}

    try:
        # Query Stripe Credit Balance Summary for metered price types
        summary = stripe.billing.CreditBalanceSummary.retrieve(
            customer=customer_id,
            filter={
                'type': 'applicability_scope',
                'applicability_scope': {'price_type': 'metered'}
            }
        )

        # Extract balance from response
        # Stripe returns available_balance and ledger_balance (not available/ledger)
        if summary.balances and len(summary.balances) > 0:
            balance = summary.balances[0]
            available = balance.available_balance.monetary.value / 100 if balance.available_balance else 0
            ledger = balance.ledger_balance.monetary.value / 100 if balance.ledger_balance else 0
        else:
            available = 0.0
            ledger = 0.0

        return {
            'available_usd': available,
            'ledger_usd': ledger
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error fetching credit balance: {e}")
        raise HTTPException(500, f"Error fetching credit balance: {str(e)}")


@app.post("/api/v2/credits/purchase")
async def purchase_credits(
    request: CreditPurchaseRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Create Stripe Checkout session for credit purchase.

    All credit purchases use payment mode (no subscription).
    - Free tier users → become prepaid tier
    - Existing paid users → credits add to their balance
    """
    amount_cents = request.amount_cents

    # Validate amount
    if amount_cents < CREDIT_PURCHASE_MIN_CENTS:
        raise HTTPException(400, f"Minimum credit purchase is ${CREDIT_PURCHASE_MIN_CENTS / 100:.0f}")
    if amount_cents > CREDIT_PURCHASE_MAX_CENTS:
        raise HTTPException(400, f"Maximum credit purchase is ${CREDIT_PURCHASE_MAX_CENTS / 100:.0f}")

    try:
        # Get or create Stripe customer
        customer_id = await get_or_create_stripe_customer(
            str(current_user.user_id),
            current_user.email
        )

        # Credit purchase line item (one-time payment)
        credit_line_item = {
            'price_data': {
                'currency': 'usd',
                'unit_amount': amount_cents,
                'product_data': {
                    'name': f'${amount_cents / 100:.0f} Credit Pack',
                    'description': 'Prepaid credits for ggbots usage. Never expires.'
                }
            },
            'quantity': 1
        }

        # All credit purchases use payment mode (prepaid model)
        # No metered subscription - webhook will set tier appropriately
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode='payment',
            line_items=[credit_line_item],
            success_url=f"{os.environ['FRONTEND_URL']}/credits/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.environ['FRONTEND_URL']}/forge",
            metadata={
                'user_id': str(current_user.user_id),
                'type': 'credit_purchase',
                'amount_cents': str(amount_cents)
            }
        )

        logger.bind(user_id=str(current_user.user_id)).info(
            f"Created credit purchase checkout: ${amount_cents/100:.2f}"
        )

        return {'checkout_url': session.url}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating credit checkout: {e}")
        raise HTTPException(500, f"Payment system error: {str(e)}")


@app.post("/api/v2/credits/crypto-checkout")
async def create_crypto_checkout(
    request: CreditPurchaseRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Create NOWPayments invoice for crypto credit purchase."""
    import httpx

    amount_cents = request.amount_cents

    # Validate amount
    if amount_cents < CREDIT_PURCHASE_MIN_CENTS:
        raise HTTPException(400, f"Minimum credit purchase is ${CREDIT_PURCHASE_MIN_CENTS / 100:.0f}")
    if amount_cents > CREDIT_PURCHASE_MAX_CENTS:
        raise HTTPException(400, f"Maximum credit purchase is ${CREDIT_PURCHASE_MAX_CENTS / 100:.0f}")

    amount_usd = amount_cents / 100

    api_key = os.environ.get("PAYMENTS_API_KEY")
    if not api_key:
        raise HTTPException(500, "Crypto payments not configured")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.nowpayments.io/v1/invoice",
                headers={
                    "x-api-key": api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "price_amount": amount_usd,
                    "price_currency": "usd",
                    "order_id": f"credits_{current_user.user_id}_{amount_cents}_{int(datetime.now().timestamp())}",
                    "order_description": f"${amount_usd:.0f} Credit Pack for ggbots",
                    "ipn_callback_url": f"{API_BASE_URL}/api/v2/webhooks/nowpayments",
                    "success_url": f"{os.environ['FRONTEND_URL']}/credits/success",
                    "cancel_url": f"{os.environ['FRONTEND_URL']}/forge"
                },
                timeout=30.0
            )

            if response.status_code != 200:
                logger.error(f"NOWPayments API error: {response.status_code} - {response.text}")
                raise HTTPException(500, "Crypto payment service error")

            data = response.json()

        logger.bind(user_id=str(current_user.user_id)).info(
            f"Created crypto checkout: ${amount_usd:.2f}, invoice_id={data.get('id')}"
        )

        return {"invoice_url": data["invoice_url"]}

    except httpx.RequestError as e:
        logger.error(f"NOWPayments request error: {e}")
        raise HTTPException(500, "Crypto payment service unavailable")


@app.post("/api/v2/webhooks/nowpayments")
async def nowpayments_webhook(request: Request):
    """Handle NOWPayments IPN callback - create credit grant after crypto payment."""
    import hmac
    import hashlib

    # Get IPN secret for signature verification
    ipn_secret = os.environ.get("PAYMENTS_IPN_KEY")
    if not ipn_secret:
        logger.error("PAYMENTS_IPN_KEY not configured")
        raise HTTPException(500, "Webhook not configured")

    # Verify HMAC-SHA512 signature
    signature = request.headers.get("x-nowpayments-sig")
    body = await request.body()

    try:
        body_dict = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON")

    # NOWPayments signature: HMAC-SHA512 of sorted JSON
    sorted_body = json.dumps(body_dict, separators=(',', ':'), sort_keys=True)
    expected_sig = hmac.new(
        ipn_secret.encode(),
        sorted_body.encode(),
        hashlib.sha512
    ).hexdigest()

    if signature != expected_sig:
        logger.warning("NOWPayments webhook signature mismatch")
        raise HTTPException(403, "Invalid signature")

    # Check payment status
    payment_status = body_dict.get("payment_status")
    if payment_status != "finished":
        # Payment not complete yet - acknowledge but don't process
        logger.info(f"NOWPayments webhook: status={payment_status}, ignoring")
        return {"status": "ignored", "reason": f"status is {payment_status}"}

    # Extract order_id for idempotency check
    order_id = body_dict.get("order_id", "")

    # Idempotency check - prevent duplicate credit grants on webhook retry
    import redis
    redis_client = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
    processed_key = f"nowpayments:processed:{order_id}"

    existing = redis_client.get(processed_key)
    if existing:
        logger.info(f"NOWPayments order {order_id} already processed (status={existing.decode()}), ignoring duplicate")
        return {"status": "duplicate", "order_id": order_id}

    # Mark as processing (24h TTL to handle retries)
    redis_client.setex(processed_key, 86400, "processing")

    # Extract user_id and amount from order_id
    # Format: "credits_{user_id}_{amount_cents}_{timestamp}" (4 parts with timestamp for uniqueness)
    if not order_id.startswith("credits_"):
        logger.error(f"Invalid order_id format: {order_id}")
        raise HTTPException(400, "Invalid order_id")

    parts = order_id.split("_")
    if len(parts) < 3:
        logger.error(f"Invalid order_id format: {order_id}")
        raise HTTPException(400, "Invalid order_id format")

    user_id = parts[1]
    amount_cents = int(parts[2])
    # parts[3] is optional timestamp, ignored here (used for uniqueness)

    # Get user email for Stripe customer creation
    from core.common.db import get_db_connection
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT au.email
                FROM user_profiles up
                JOIN auth.users au ON up.user_id = au.id
                WHERE up.user_id = %s
            """, (user_id,))
            result = cur.fetchone()

    if not result:
        logger.error(f"User not found: {user_id}")
        raise HTTPException(400, "User not found")

    email = result[0]

    # Get or create Stripe customer
    customer_id = await get_or_create_stripe_customer(user_id, email)

    # Check user's current tier and expiration to decide how to handle the credit purchase
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT subscription_tier, subscription_expires_at
                FROM user_profiles WHERE user_id = %s
            """, (user_id,))
            tier_result = cur.fetchone()
            current_tier = tier_result[0] if tier_result else 'free'
            expires_at = tier_result[1] if tier_result else None

    # Check if subscription is expired
    from datetime import datetime, timezone
    is_expired = (
        expires_at is not None and
        expires_at <= datetime.now(timezone.utc)
    )

    if current_tier == 'free' or is_expired:
        # Free tier or expired user buying credits via crypto → upgrade to prepaid
        # NO metered subscription - they pay upfront only
        # Clear subscription_expires_at since prepaid doesn't expire (credits do)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE user_profiles
                    SET subscription_tier = 'prepaid',
                        subscription_status = 'active',
                        subscription_expires_at = NULL,
                        stripe_customer_id = %s,
                        updated_at = NOW()
                    WHERE user_id = %s
                """, (customer_id, user_id))
                conn.commit()

        logger.bind(user_id=user_id).info(
            f"Upgraded to prepaid tier via crypto (was {current_tier}, expired={is_expired}): Customer: {customer_id}"
        )
    elif current_tier == 'prepaid':
        # Already prepaid - just add more credits (no tier change needed)
        logger.bind(user_id=user_id).info(
            f"Adding credits to existing prepaid account via crypto"
        )
    else:
        # Already on active usage_based or pro tier - credits will apply as discounts
        logger.bind(user_id=user_id).info(
            f"Adding credits to existing {current_tier} account via crypto"
        )

    # Create Stripe Credit Grant
    try:
        stripe.billing.CreditGrant.create(
            customer=customer_id,
            name=f"${amount_cents / 100:.0f} Credit Pack (Crypto)",
            applicability_config={
                'scope': {'price_type': 'metered'}
            },
            category='paid',
            amount={
                'type': 'monetary',
                'monetary': {
                    'value': amount_cents,
                    'currency': 'usd'
                }
            }
        )

        logger.bind(user_id=user_id).info(
            f"Crypto credit grant created: ${amount_cents / 100:.2f}"
        )

        # Clear credit notification state so user can receive future alerts
        from core.monitoring.usage_monitor import clear_credit_notification_state
        clear_credit_notification_state(user_id)

        # Mark as completed (30-day TTL for audit trail)
        redis_client.setex(processed_key, 86400 * 30, "completed")

    except stripe.error.StripeError as e:
        logger.error(f"Failed to create credit grant: {e}")
        raise HTTPException(500, "Failed to create credit grant")

    return {"status": "success"}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_or_create_stripe_customer(user_id: str, email: str) -> str:
    """Get existing Stripe customer ID or create new customer."""
    from core.common.db import get_db_connection

    # Check database for existing customer
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT stripe_customer_id
                FROM user_profiles
                WHERE user_id = %s
            """, (user_id,))
            result = cur.fetchone()

    if result and result[0]:
        return result[0]

    # Create new Stripe customer
    try:
        customer = stripe.Customer.create(
            email=email,
            metadata={'user_id': user_id}
        )

        # Save to database
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE user_profiles
                    SET stripe_customer_id = %s,
                        updated_at = NOW()
                    WHERE user_id = %s
                """, (customer.id, user_id))
                conn.commit()

        logger.bind(user_id=user_id).info(f"Created Stripe customer: {customer.id}")
        return customer.id

    except stripe.error.StripeError as e:
        logger.error(f"Error creating Stripe customer: {e}")
        raise


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


if os.getenv("DEVELOPMENT_MODE", "false").lower() == "true":
    logger.warning("⚠️  DEVELOPMENT MODE ACTIVE: Using mock authentication - DO NOT USE IN PRODUCTION")
    app.dependency_overrides[get_current_user_v2] = get_mock_user_for_dev

if __name__ == "__main__":
    # Disable reload in production (PM2 handles process management)
    is_dev = os.getenv("DEV_MODE", "false").lower() == "true"
    uvicorn.run(
        "ggbot:app",
        host="0.0.0.0",
        port=8000,
        reload=is_dev,
        log_level="info"
    )