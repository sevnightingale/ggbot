"""
GGBot V2 Orchestrator - Clean Architecture Implementation

Main orchestrator API that coordinates all V2 modules with Supabase integration.
Provides unified entry point for autonomous trading with multi-user isolation.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import json

# V2 Core Components
from core.auth.supabase_auth import AuthenticatedUser, get_current_user_v2, require_premium_user_v2

# Development Mock User (TODO: Remove when Phase 5 authentication is complete)
async def get_mock_user_for_dev():
    """Mock user for Phase 7 development - replace with real auth in Phase 5."""
    return AuthenticatedUser(
        user_id="00000000-0000-0000-0000-000000000000",  # Real Supabase user ID
        email="user@example.com",  # Placeholder email
        claims={"sub": "00000000-0000-0000-0000-000000000000", "email": "user@example.com"}
    )
from core.services.config_service import ConfigService, BotConfigV2, config_service
from core.services.user_service import UserService, user_service
from core.services.llm_service import LLMService, llm_service
from core.services.indicator_service import IndicatorService
from core.common.logger import logger

# V2 Module Integration - Complete Integration
from extraction.v2.extraction_engine import ExtractionEngineV2
from decision.engine_v2 import DecisionEngineV2
from trading.paper.service import PaperTradingService

# Domain Models  
from core.domain import Decision, DecisionAction, DecisionStatus, UserProfile, Symbol, Confidence


# Pydantic Models for API
class ConfigCreateRequest(BaseModel):
    config_name: str
    schema_version: str = "2.1"
    config_type: str = "autonomous_trading"
    selected_pair: str = "BTC/USDT"
    extraction: Dict[str, Any]
    decision: Dict[str, Any]
    trading: Dict[str, Any]
    llm_config: Dict[str, Any]
    telegram_integration: Optional[Dict[str, Any]] = None


class ConfigUpdateRequest(BaseModel):
    config_name: Optional[str] = None
    schema_version: Optional[str] = None
    config_type: Optional[str] = None
    selected_pair: Optional[str] = None
    extraction: Optional[Dict[str, Any]] = None
    decision: Optional[Dict[str, Any]] = None
    trading: Optional[Dict[str, Any]] = None
    llm_config: Optional[Dict[str, Any]] = None
    telegram_integration: Optional[Dict[str, Any]] = None


class OrchestrationResult(BaseModel):
    status: str
    config_id: str
    extraction_result: Optional[Dict[str, Any]] = None
    decision_result: Optional[Dict[str, Any]] = None
    trading_result: Optional[Dict[str, Any]] = None
    execution_time_ms: int
    timestamp: str


# FastAPI lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    logger.info("🚀 Starting GGBot V2 Orchestrator")
    
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
        
        logger.info("🟢 GGBot V2 Orchestrator ready")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown tasks
    logger.info("🔄 Shutting down GGBot V2 Orchestrator")


# Create FastAPI app
app = FastAPI(
    title="GGBot V2 Orchestrator",
    description="Unified orchestrator for autonomous AI trading with Supabase integration",
    version="2.0.0",
    lifespan=lifespan
)

# CORS handled by nginx proxy - no FastAPI CORS middleware needed

# Services
class GGBotOrchestrator:
    """Main orchestrator class coordinating all V2 modules with full integration."""
    
    def __init__(self):
        self.config_service = config_service
        self.llm_service = llm_service
        self.paper_trading = PaperTradingService()
        self._log = logger.bind(component="orchestrator")
        
        # V2 Engine instances - created per request for proper isolation
        self._extraction_engines = {}  # Cache by user_id for efficiency
        self._decision_engines = {}    # Cache by config_id
    
    async def run_autonomous_cycle(
        self,
        config_id: str,
        user_id: str
    ) -> OrchestrationResult:
        """
        Run a complete autonomous trading cycle using real V2 systems.
        
        Args:
            config_id: Bot configuration ID
            user_id: User ID for access validation
            
        Returns:
            OrchestrationResult with execution details
        """
        start_time = datetime.now(timezone.utc)
        self._log.info(f"Starting V2 autonomous cycle for config {config_id}")
        
        try:
            # 1. Load user configuration
            config = await self.config_service.get_config(config_id, user_id)
            if not config:
                raise HTTPException(status_code=404, detail="Configuration not found")
            
            # 2. Get or create V2 extraction engine
            extraction_engine = await self._get_extraction_engine(user_id)
            
            # 3. Extract indicators and timeframes from config structure
            extraction_config = config.extraction or {}
            requested_indicators = []
            timeframes = ["1h"]  # Default single timeframe
            
            # Handle new structure (selected_data_sources) 
            if "selected_data_sources" in extraction_config:
                data_sources = extraction_config.get("selected_data_sources", {})
                for source_name, source_config in data_sources.items():
                    if isinstance(source_config, dict):
                        # Get data points from this source
                        data_points = source_config.get("data_points", [])
                        requested_indicators.extend(data_points)
                        
                        # Get timeframes from this source (use first source's timeframes)
                        if not timeframes or timeframes == ["1h"]:
                            source_timeframes = source_config.get("timeframes", ["1h"])
                            if source_timeframes:
                                timeframes = source_timeframes
                                
            # Fallback to legacy structures
            elif "indicators" in extraction_config:
                requested_indicators = extraction_config["indicators"]
            else:
                # Fallback to old data_sources structure
                data_sources = extraction_config.get("data_sources", {})
                for category, indicators in data_sources.items():
                    if isinstance(indicators, list):
                        requested_indicators.extend(indicators)
            
            if not requested_indicators:
                # Default to basic indicators if none specified
                requested_indicators = ["rsi", "macd", "ema"]
            
            # 4. Run V2 extraction for all timeframes
            extraction_result = await self._run_extraction_v2(
                extraction_engine, config, user_id, requested_indicators, timeframes
            )
            
            # 5. Run V2 decision engine
            decision_result = await self._run_decision_v2(
                config_id, config, extraction_result
            )
            
            # 6. Execute trading if actionable
            trading_result = await self._run_trading_v2(
                config, user_id, decision_result
            )
            
            # Calculate execution time
            end_time = datetime.now(timezone.utc)
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            result = OrchestrationResult(
                status="success",
                config_id=config_id,
                extraction_result=extraction_result,
                decision_result=decision_result,
                trading_result=trading_result,
                execution_time_ms=execution_time_ms,
                timestamp=end_time.isoformat()
            )
            
            self._log.info(f"V2 autonomous cycle completed in {execution_time_ms}ms")
            return result
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            self._log.error(f"V2 autonomous cycle failed: {e}")
            return OrchestrationResult(
                status="error",
                config_id=config_id,
                extraction_result={"error": str(e)},
                decision_result=None,
                trading_result=None,
                execution_time_ms=execution_time_ms,
                timestamp=end_time.isoformat()
            )
    
    async def _get_extraction_engine(self, user_id: str) -> ExtractionEngineV2:
        """Get or create V2 extraction engine for user."""
        if user_id not in self._extraction_engines:
            self._extraction_engines[user_id] = ExtractionEngineV2(
                user_id=user_id,
                use_advanced_preprocessing=True,
                use_database_storage=True
            )
        return self._extraction_engines[user_id]
    
    async def _run_extraction_v2(
        self,
        extraction_engine: ExtractionEngineV2,
        config: BotConfigV2,
        user_id: str,
        indicators: List[str],
        timeframes: List[str] = ["1h"]
    ) -> Dict[str, Any]:
        """Run V2 extraction engine for multiple timeframes with proper integration."""
        try:
            # Get symbol from config
            symbol = config.selected_pair or "BTC/USDT"
            
            # Extract for all timeframes
            timeframe_results = {}
            successful_extractions = 0
            
            for timeframe in timeframes:
                self._log.info(f"Extracting {len(indicators)} indicators for {symbol} ({timeframe})")
                
                # Extract using the V2 system with all 21 preprocessors
                result = await extraction_engine.extract_for_symbol(
                    symbol=symbol,
                    indicators=indicators,
                    timeframe=timeframe,
                    limit=200,
                    connector="kucoin",
                    config_id=config.config_id
                )
                
                timeframe_results[timeframe] = result
                
                if result.get("status") == "success":
                    successful_extractions += 1
                    self._log.info(f"✅ V2 Extraction completed for {symbol} ({timeframe})")
                else:
                    self._log.error(f"❌ V2 Extraction failed for {symbol} ({timeframe}): {result.get('error')}")
            
            # Prepare consolidated result
            overall_result = {
                "status": "success" if successful_extractions > 0 else "error",
                "symbol": symbol,
                "timeframes": timeframe_results,
                "summary": {
                    "total_timeframes": len(timeframes),
                    "successful_extractions": successful_extractions,
                    "failed_extractions": len(timeframes) - successful_extractions,
                    "indicators": indicators
                }
            }
            
            if successful_extractions == 0:
                overall_result["error"] = "All timeframe extractions failed"
            
            self._log.info(f"V2 Multi-timeframe extraction completed: {successful_extractions}/{len(timeframes)} successful")
            return overall_result
            
        except Exception as e:
            self._log.error(f"V2 Multi-timeframe extraction failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "symbol": config.selected_pair or "Unknown",
                "indicators": indicators,
                "timeframes": timeframes
            }
    
    async def _get_decision_engine(self, config_id: str, user_id: str) -> DecisionEngineV2:
        """Get or create V2 decision engine for config."""
        if config_id not in self._decision_engines:
            engine = DecisionEngineV2(config_id, user_id)
            await engine.initialize()
            self._decision_engines[config_id] = engine
        return self._decision_engines[config_id]
    
    async def _run_decision_v2(
        self,
        config_id: str,
        config: BotConfigV2,
        extraction_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run V2 decision engine with full context management."""
        try:
            # Check if extraction was successful
            if extraction_result.get("status") == "error":
                return {
                    "status": "error",
                    "error": "Extraction failed, cannot make decision",
                    "action": "wait",
                    "confidence": 0.0
                }
            
            # Get or create V2 decision engine
            decision_engine = await self._get_decision_engine(config_id, config.user_id)
            
            # Get symbol from config
            symbol = config.selected_pair or "BTC/USDT"
            
            # Run decision using V2 engine with full context management
            decision_result = await decision_engine.make_decision(
                symbol=symbol,
                signal_data=None  # For autonomous trading, no signal data
            )
            
            self._log.info(f"V2 Decision completed: {decision_result.get('action')} with confidence {decision_result.get('confidence', 0)}")
            return decision_result
            
        except Exception as e:
            self._log.error(f"V2 Decision failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "action": "wait",
                "confidence": 0.0
            }
    
    async def _run_trading_v2(
        self,
        config: BotConfigV2,
        user_id: str,
        decision_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run V2 trading execution with full paper trading integration."""
        try:
            # Check if decision was successful
            if decision_result.get("status") == "error":
                return {
                    "status": "skipped",
                    "reason": "Decision failed, no trading action"
                }
            
            action = decision_result.get("action", "wait")
            confidence = decision_result.get("confidence", 0.0)
            
            # Skip trading if action is wait, no_action, or hold
            if action in ["wait", "no_action", "hold"]:
                return {
                    "status": "skipped",
                    "reason": f"Decision was to {action}",
                    "action": action
                }
            
            # Get trading config from config  
            trading_config = config.trading or {}
            symbol = config.selected_pair or "BTC/USDT"
            
            # Create comprehensive trading intent for paper trading service
            trading_intent = {
                "decision_id": decision_result.get("decision_id"),
                "user_id": user_id,
                "config_id": config.config_id,
                "symbol": symbol,
                "action": "long" if action in ["enter", "long"] else "short" if action == "short" else "close",
                "confidence": confidence,
                "stop_loss_price": decision_result.get("stop_loss_price"),
                "take_profit_price": decision_result.get("take_profit_price"),
                "reasoning": decision_result.get("reasoning", "V2 Decision Engine decision")
            }
            
            # Execute trade via paper trading service
            trade_result = await self.paper_trading.execute_trade_intent(trading_intent)
            
            self._log.info(f"V2 Trading completed: {trade_result.get('status')} for {symbol}")
            return trade_result
            
        except Exception as e:
            self._log.error(f"V2 Trading failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    


# Initialize orchestrator
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


# Configuration Management Endpoints
@app.post("/api/v2/config")
async def create_config(
    request: ConfigCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Create a new bot configuration."""
    config = await config_service.create_config(
        user_id=current_user.user_id,
        config_name=request.config_name,
        config_data=request.dict(exclude={"config_name"})
    )
    
    if not config:
        raise HTTPException(status_code=400, detail="Failed to create configuration")
    
    return {
        "status": "success",
        "config": config.to_dict()
    }


@app.get("/api/v2/config")
async def list_configs(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """List all configurations for the current user."""
    configs = await config_service.list_configs(current_user.user_id)
    
    return {
        "status": "success",
        "configs": [config.to_dict() for config in configs],
        "count": len(configs)
    }


@app.get("/api/v2/config/{config_id}")
async def get_config(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get a specific configuration."""
    config = await config_service.get_config(config_id, current_user.user_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return {
        "status": "success",
        "config": config.to_dict()
    }


@app.put("/api/v2/config/{config_id}")
async def update_config(
    config_id: str,
    request: ConfigUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Update a configuration."""
    # Filter out None values
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    config_name = update_data.pop("config_name", None)
    
    config = await config_service.update_config(
        config_id=config_id,
        user_id=current_user.user_id,
        config_data=update_data,
        config_name=config_name
    )
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found or update failed")
    
    return {
        "status": "success",
        "config": config.to_dict()
    }


@app.delete("/api/v2/config/{config_id}")
async def delete_config(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Delete a configuration."""
    success = await config_service.delete_config(config_id, current_user.user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return {
        "status": "success",
        "message": "Configuration deleted successfully"
    }


# Orchestration Endpoints
@app.post("/api/v2/orchestrate/{config_id}")
async def run_orchestration(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> OrchestrationResult:
    """Run autonomous trading cycle for a configuration."""
    result = await orchestrator.run_autonomous_cycle(config_id, current_user.user_id)
    
    if result.status == "error":
        raise HTTPException(status_code=500, detail="Orchestration failed")
    
    return result


# User Management Endpoints
@app.get("/api/v2/user/profile")
async def get_user_profile(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get current user profile."""
    profile = await current_user.load_profile()
    
    return {
        "status": "success",
        "profile": {
            "user_id": profile.user_id,
            "subscription_tier": profile.subscription_tier.value,
            "subscription_status": profile.subscription_status.value,
            "can_use_premium_features": profile.can_use_premium_features,
            "requires_own_llm_keys": profile.requires_own_llm_keys,
            "can_publish_telegram_signals": profile.can_publish_telegram_signals,
            "can_use_signal_validation": profile.can_use_signal_validation,
            "paid_data_points": profile.paid_data_points
        }
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
        user_paid_points = profile.paid_data_points if hasattr(profile, 'paid_data_points') else []
        
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
                        has_access = not point_requires_premium or point_name in user_paid_points
                        
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
                    "user_paid_points": user_paid_points,
                    "count": len(sources_list)
                }
                
    except Exception as e:
        logger.error(f"Failed to get data sources with points: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get data sources: {str(e)}")


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
        
        if provider not in ["openai", "deepseek", "anthropic"]:
            raise HTTPException(status_code=400, detail="Invalid provider. Must be one of: openai, deepseek, anthropic")
        
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


# Bot Data Endpoints for Dashboard
@app.get("/api/v2/bot/{config_id}/metrics")
async def get_bot_metrics(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get performance metrics for a bot configuration."""
    try:
        # TODO: Implement real metrics calculation from strategy_runs table
        # For now, return empty metrics structure
        return {
            "status": "success",
            "config_id": config_id,
            "metrics": {
                "profit_loss_data": [],  # Array of {date: string, profit: number}
                "trade_stats": {
                    "totalTrades": 0,
                    "winCount": 0,
                    "lossCount": 0,
                    "neutralCount": 0,
                    "winRate": 0,
                    "lossRate": 0,
                    "neutralRate": 0,
                    "avgProfitPerTrade": 0,
                    "avgLossPerTrade": 0,
                    "totalProfit": 0,
                    "avgTradeDuration": "0m"
                }
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
    """Get live positions for a bot configuration."""
    try:
        # TODO: Implement real positions query from positions/paper_trades table
        # For now, return empty positions
        return {
            "status": "success",
            "config_id": config_id,
            "positions": []  # Array of position objects
        }
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
        # TODO: Implement real trades query from paper_trades/trades table
        # For now, return empty trades
        return {
            "status": "success",
            "config_id": config_id,
            "trades": [],  # Array of trade objects
            "count": 0
        }
    except Exception as e:
        logger.error(f"Failed to get bot trades for {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bot trades")


# Bot Lifecycle Endpoints (placeholders for now)
@app.post("/api/v2/bot/{config_id}/start")
async def start_bot(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Start a bot (placeholder)."""
    # TODO: Implement bot lifecycle management
    return {
        "status": "success",
        "message": "Bot start functionality coming soon",
        "config_id": config_id
    }


@app.post("/api/v2/bot/{config_id}/stop")
async def stop_bot(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Stop a bot (placeholder)."""
    # TODO: Implement bot lifecycle management
    return {
        "status": "success",
        "message": "Bot stop functionality coming soon",
        "config_id": config_id
    }


@app.get("/api/v2/bot/{config_id}/status")
async def get_bot_status(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get bot status (placeholder)."""
    # TODO: Implement bot status tracking
    return {
        "status": "success",
        "bot_status": "stopped",
        "message": "Bot status tracking coming soon",
        "config_id": config_id
    }


# WebSocket Support for real-time bot status updates
class WebSocketManager:
    """Simple WebSocket connection manager."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
    def disconnect(self, user_id: str):
        """Remove WebSocket connection."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def broadcast_to_user(self, user_id: str, data: dict):
        """Send data to specific user."""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(data))
            except:
                # Connection closed, remove it
                self.disconnect(user_id)


# Global WebSocket manager
websocket_manager = WebSocketManager()


@app.websocket("/ws/bot-status/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time bot status updates."""
    await websocket_manager.connect(user_id, websocket)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Echo heartbeat messages
            if data == "heartbeat":
                await websocket.send_text(json.dumps({
                    "type": "heartbeat_ack", 
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                }))
    except WebSocketDisconnect:
        websocket_manager.disconnect(user_id)


# Error handlers
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


# Development Mode: Override authentication for Phase 7 testing
import os
if os.getenv("DEVELOPMENT_MODE", "false").lower() == "true":
    logger.warning("⚠️  DEVELOPMENT MODE ACTIVE: Using mock authentication - DO NOT USE IN PRODUCTION")
    app.dependency_overrides[get_current_user_v2] = get_mock_user_for_dev

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "ggbot:app",
        host="0.0.0.0",
        port=8000,  # V2 Orchestrator port (matches nginx configuration)
        reload=True,
        log_level="info"
    )