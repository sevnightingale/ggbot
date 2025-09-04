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

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# V2 Core Components
from core.auth.supabase_auth import AuthenticatedUser, get_current_user_v2, require_premium_user_v2

# Development Mock User (TODO: Remove when Phase 5 authentication is complete)
async def get_mock_user_for_dev():
    """Mock user for Phase 7 development - replace with real auth in Phase 5."""
    return AuthenticatedUser(
        user_id="c81933d2-dd86-479d-97db-fad83465362f",  # Real Supabase user ID
        email="user@example.com",  # Placeholder email
        claims={"sub": "c81933d2-dd86-479d-97db-fad83465362f", "email": "user@example.com"}
    )
from core.services.config_service import ConfigService, BotConfigV2, config_service
from core.services.user_service import UserService, user_service
from core.services.llm_service import LLMService, llm_service
from core.services.indicator_service import IndicatorService
from core.common.logger import logger

# V2 Module Integration
from extraction.v2.extraction_engine import ExtractionEngineV2
# from decision.v2.decision_engine import DecisionEngineV2  # TODO: Create V2 decision engine
from trading.paper.service import PaperTradingService

# Domain Models  
from core.domain import Decision, DecisionAction, DecisionStatus, UserProfile, Symbol, Confidence


# Pydantic Models for API
class ConfigCreateRequest(BaseModel):
    config_name: str
    selected_pair: str = "BTC/USDT"
    extraction: Dict[str, Any]
    decision: Dict[str, Any]
    trading: Dict[str, Any]
    telegram_integration: Optional[Dict[str, Any]] = None


class ConfigUpdateRequest(BaseModel):
    config_name: Optional[str] = None
    selected_pair: Optional[str] = None
    extraction: Optional[Dict[str, Any]] = None
    decision: Optional[Dict[str, Any]] = None
    trading: Optional[Dict[str, Any]] = None
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
        # Test database connectivity
        test_user = await user_service.get_profile("test")
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
class GGBotOrchestrator:
    """Main orchestrator class coordinating all V2 modules."""
    
    def __init__(self):
        self.config_service = config_service
        self.llm_service = llm_service
        self.indicator_service = IndicatorService()
        self.paper_trading = PaperTradingService()
        self._log = logger.bind(component="orchestrator")
    
    async def run_autonomous_cycle(
        self,
        config_id: str,
        user_id: str
    ) -> OrchestrationResult:
        """
        Run a complete autonomous trading cycle.
        
        Args:
            config_id: Bot configuration ID
            user_id: User ID for access validation
            
        Returns:
            OrchestrationResult with execution details
        """
        start_time = datetime.now(timezone.utc)
        self._log.info(f"Starting autonomous cycle for config {config_id}")
        
        try:
            # 1. Load user configuration
            config = await self.config_service.get_config(config_id, user_id)
            if not config:
                raise HTTPException(status_code=404, detail="Configuration not found")
            
            # 2. Get user's available indicators
            user_indicators = await self.indicator_service.get_user_available_indicators(user_id)
            available_indicator_names = [ind["name"] for ind in user_indicators]
            
            # 3. Validate requested indicators against user access
            requested_indicators = config.extraction.get("indicators", [])
            if isinstance(requested_indicators, dict):
                # Handle nested indicator structure
                requested_indicators = []
                for category, indicators in config.extraction.get("data_sources", {}).items():
                    if isinstance(indicators, list):
                        requested_indicators.extend(indicators)
            
            # Filter to only allowed indicators
            allowed_indicators = [
                ind for ind in requested_indicators 
                if ind in available_indicator_names
            ]
            
            if not allowed_indicators:
                raise HTTPException(
                    status_code=403, 
                    detail="No accessible indicators found in configuration"
                )
            
            # 4. Run extraction (V2 integration placeholder)
            extraction_result = await self._run_extraction_v2(
                config, user_id, allowed_indicators
            )
            
            # 5. Run decision engine (V2 integration placeholder)
            decision_result = await self._run_decision_v2(
                config, user_id, extraction_result
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
            
            self._log.info(f"Autonomous cycle completed in {execution_time_ms}ms")
            return result
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            self._log.error(f"Autonomous cycle failed: {e}")
            return OrchestrationResult(
                status="error",
                config_id=config_id,
                extraction_result={"error": str(e)},
                decision_result=None,
                trading_result=None,
                execution_time_ms=execution_time_ms,
                timestamp=end_time.isoformat()
            )
    
    async def _run_extraction_v2(
        self,
        config: BotConfigV2,
        user_id: str,
        indicators: List[str]
    ) -> Dict[str, Any]:
        """Run V2 extraction engine."""
        try:
            # Initialize extraction engine with user context
            extraction_engine = ExtractionEngineV2(
                user_id=user_id,
                use_advanced_preprocessing=True,
                use_database_storage=True
            )
            
            # Extract indicators for the configured symbol
            result = await extraction_engine.extract_for_symbol(
                symbol=config.selected_pair,
                indicators=indicators,
                timeframe=config.extraction.get("timeframe", "1h"),
                limit=config.extraction.get("limit", 200),
                connector=config.extraction.get("connector", "kucoin"),
                config_id=config.config_id
            )
            
            self._log.info(f"V2 Extraction completed for {config.selected_pair}")
            return result
            
        except Exception as e:
            self._log.error(f"V2 Extraction failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "symbol": config.selected_pair,
                "indicators": indicators
            }
    
    async def _run_decision_v2(
        self,
        config: BotConfigV2,
        user_id: str,
        extraction_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run V2 decision engine with LLM integration."""
        try:
            # Check if extraction was successful
            if extraction_result.get("status") != "success":
                return {
                    "status": "error",
                    "error": "Extraction failed, cannot make decision",
                    "action": "wait",
                    "confidence": 0.0
                }
            
            # Get LLM client based on user subscription
            llm_client = await self.llm_service.get_llm_client(
                user_id=user_id,
                config_id=config.config_id,
                preferred_provider="openai"  # TODO: Get from config
            )
            
            if not llm_client:
                return {
                    "status": "error",
                    "error": "LLM client not available",
                    "action": "wait",
                    "confidence": 0.0
                }
            
            # Prepare decision prompt with extraction data
            market_data = extraction_result.get("result", {}).get("indicators", {})
            current_price = extraction_result.get("result", {}).get("ohlcv_summary", {}).get("latest_price", "Unknown")
            
            # Format market data for LLM
            market_data_text = self._format_market_data_for_llm(market_data)
            
            # Build prompts from config
            system_prompt = config.decision.get("system_prompt", "").format(
                SYMBOL=config.selected_pair,
                CURRENT_PRICE=current_price,
                MARKET_DATA=market_data_text
            )
            
            user_prompt = config.decision.get("user_prompt", "").format(
                SYMBOL=config.selected_pair,
                CURRENT_PRICE=current_price,
                MARKET_DATA=market_data_text
            )
            
            # Generate LLM decision
            llm_response = await llm_client.generate_completion(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=500
            )
            
            if llm_response.get("status") != "success":
                return {
                    "status": "error",
                    "error": f"LLM generation failed: {llm_response.get('error')}",
                    "action": "wait",
                    "confidence": 0.0
                }
            
            # Parse LLM response into structured decision
            decision_data = self._parse_llm_decision(llm_response.get("content", ""))
            
            # Create Decision domain object for audit trail
            decision = Decision.create_opportunity_analysis(
                user_id=user_id,
                config_id=config.config_id,
                symbol=Symbol(config.selected_pair),
                action=DecisionAction(decision_data["action"].upper()),
                confidence=Confidence(decision_data["confidence"]),
                reasoning=decision_data["reasoning"],
                prompt=f"System: {system_prompt}\n\nUser: {user_prompt}",
                market_data=market_data
            )
            
            # TODO: Store decision in decisions table
            
            self._log.info(f"V2 Decision completed: {decision_data['action']} with confidence {decision_data['confidence']}")
            return {
                "status": "success",
                "action": decision_data["action"],
                "confidence": decision_data["confidence"],
                "reasoning": decision_data["reasoning"],
                "llm_usage": llm_response.get("usage", {}),
                "decision_id": decision.decision_id
            }
            
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
        """Run V2 trading execution with paper trading."""
        try:
            # Check if decision was successful
            if decision_result.get("status") != "success":
                return {
                    "status": "skipped",
                    "reason": "Decision failed, no trading action"
                }
            
            action = decision_result.get("action", "wait")
            confidence = decision_result.get("confidence", 0.0)
            
            # Skip trading if action is wait
            if action == "wait":
                return {
                    "status": "skipped",
                    "reason": "Decision was to wait",
                    "action": action
                }
            
            # Check if trading is enabled in config
            if config.trading.get("execution_mode") != "paper":
                return {
                    "status": "error",
                    "error": "Only paper trading is supported in V2"
                }
            
            # Create trading intent for paper trading service
            trading_intent = {
                "config_id": config.config_id,
                "user_id": user_id,
                "symbol": config.selected_pair,
                "action": action,  # "enter" or "exit"
                "confidence": confidence,
                "reasoning": decision_result.get("reasoning", ""),
                "decision_id": decision_result.get("decision_id"),
                "position_sizing": config.trading.get("position_sizing", {}),
                "risk_management": config.trading.get("risk_management", {})
            }
            
            # Execute trade via paper trading service
            trade_result = await self.paper_trading.execute_trade_intent(trading_intent)
            
            self._log.info(f"V2 Trading completed: {trade_result.get('status')}")
            return trade_result
            
        except Exception as e:
            self._log.error(f"V2 Trading failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _format_market_data_for_llm(self, market_data: Dict[str, Any]) -> str:
        """Format market data dictionary for LLM consumption."""
        if not market_data:
            return "No market data available."
        
        formatted_lines = []
        for indicator, value in market_data.items():
            if isinstance(value, dict):
                # Handle nested indicator data
                for sub_key, sub_value in value.items():
                    formatted_lines.append(f"{indicator}_{sub_key}: {sub_value}")
            else:
                formatted_lines.append(f"{indicator}: {value}")
        
        return "\n".join(formatted_lines)
    
    def _parse_llm_decision(self, llm_content: str) -> Dict[str, Any]:
        """Parse LLM response into structured decision data."""
        # Simple parsing - in production this would be more sophisticated
        content = llm_content.lower()
        
        # Extract action
        action = "wait"  # Default
        if "enter" in content or "buy" in content:
            action = "enter"
        elif "exit" in content or "sell" in content:
            action = "exit"
        
        # Extract confidence (look for percentage or decimal)
        confidence = 0.5  # Default
        import re
        confidence_patterns = [
            r"confidence[:\s]*(\d+(?:\.\d+)?)%",
            r"confidence[:\s]*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)%\s*confident",
            r"(\d+(?:\.\d+)?)\s*confidence"
        ]
        
        for pattern in confidence_patterns:
            match = re.search(pattern, content)
            if match:
                conf_value = float(match.group(1))
                # Convert percentage to decimal if needed
                confidence = conf_value / 100 if conf_value > 1.0 else conf_value
                break
        
        # Ensure confidence is in valid range
        confidence = max(0.0, min(1.0, confidence))
        
        return {
            "action": action,
            "confidence": confidence,
            "reasoning": llm_content  # Keep full reasoning
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
            "can_publish_telegram_signals": profile.can_publish_telegram_signals
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
    logger.info("🧪 DEVELOPMENT MODE: Using mock authentication")
    app.dependency_overrides[get_current_user_v2] = get_mock_user_for_dev

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "ggbot:app",
        host="0.0.0.0",
        port=8001,  # Different port from main_api.py
        reload=True,
        log_level="info"
    )