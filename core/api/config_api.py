"""
Configuration Management API

Provides endpoints for creating, updating, and managing trading strategy configurations.
Includes template-based creation for demo purposes and permission management.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from core.common.logger import logger
from core.common.db import get_db_connection
from core.common.config import DEFAULT_USER_ID


# API Router
router = APIRouter(prefix="/api/configs", tags=["Configuration"])


# Request/Response Models
class StrategyTemplate(BaseModel):
    """Template for creating a new strategy configuration."""
    template: str = Field(..., description="Template name: rsi, macd, manual, momentum, bollinger")
    symbol: str = Field(default="BTC/USDT", description="Trading symbol")
    risk_level: str = Field(default="medium", description="Risk level: low, medium, high")
    user_id: str = Field(default=DEFAULT_USER_ID, description="User UUID")
    config_name: Optional[str] = Field(None, description="Custom name for the strategy")


class ConfigUpdate(BaseModel):
    """Update request for configuration."""
    config_name: Optional[str] = None
    strategy: Optional[str] = None
    risk_guidelines: Optional[str] = None
    additional_context: Optional[str] = None


class ConfigPermissions(BaseModel):
    """Configuration permissions."""
    editable: bool
    is_flagship: bool
    config_type: str
    owner_id: str


class ConfigResponse(BaseModel):
    """Configuration response with details."""
    config_id: str
    config_name: Optional[str] = None
    config_type: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    editable: bool
    is_flagship: bool
    instance_name: Optional[str] = None
    paper_balance: float = 10000.0


# Strategy Templates
STRATEGY_TEMPLATES = {
    "rsi": {
        "name": "RSI Momentum Strategy",
        "type": "rsi_momentum",
        "strategy": "Trade based on RSI oversold/overbought conditions. Enter long when RSI < 30 and showing reversal signs, enter short when RSI > 70 with bearish divergence. Use 15m and 1h timeframes for confirmation.",
        "risk_guidelines": "Max position size 5% of capital. Max leverage 3x. Stop loss at 2% per trade. Take profit at 4-6% or when RSI reaches opposite extreme.",
        "additional_context": "Focus on major support/resistance levels. Avoid trading during low volume periods. Best performance in ranging markets."
    },
    "macd": {
        "name": "MACD Trend Following",
        "type": "macd_trend",
        "strategy": "Follow MACD crossovers for trend entries. Enter long on MACD line crossing above signal line with positive histogram. Enter short on bearish crossover. Confirm with price action above/below 50 EMA.",
        "risk_guidelines": "Max position size 4% of capital. Max leverage 5x. Trailing stop loss at 3%. Take profit in stages: 30% at 3%, 40% at 5%, 30% at 8%.",
        "additional_context": "Works best in trending markets. Avoid choppy/ranging conditions. Pay attention to divergences for potential reversals."
    },
    "manual": {
        "name": "Manual Trading Bot",
        "type": "manual_signals",
        "strategy": "Execute trades based on manual analysis and external signals. Wait for high-confidence setups with clear risk/reward ratios. Focus on price action and volume confirmation.",
        "risk_guidelines": "Max position size 3% of capital. Max leverage 2x. Fixed stop loss at 1.5%. Take profit at minimum 1:2 risk/reward ratio.",
        "additional_context": "Conservative approach prioritizing capital preservation. Only trade A+ setups with multiple confirmations."
    },
    "momentum": {
        "name": "Momentum Breakout Strategy",
        "type": "momentum_breakout",
        "strategy": "Trade momentum breakouts from consolidation zones. Enter on volume spike above resistance or below support. Use ATR for volatility-based position sizing. Hold winners, cut losers quickly.",
        "risk_guidelines": "Max position size 6% of capital. Max leverage 4x. ATR-based stop loss (1.5x ATR). Take profit at 3x ATR or next major level.",
        "additional_context": "Best in high volatility periods. Scale into positions on confirmation. Use volume as primary confirmation indicator."
    },
    "bollinger": {
        "name": "Bollinger Bands Mean Reversion",
        "type": "bollinger_reversion",
        "strategy": "Trade bounces from Bollinger Band extremes. Enter long at lower band with RSI oversold, enter short at upper band with RSI overbought. Target middle band or opposite band.",
        "risk_guidelines": "Max position size 4% of capital. Max leverage 3x. Stop loss outside bands by 0.5%. Take profit at middle band (50%) and opposite band (50%).",
        "additional_context": "Works best in ranging markets with clear boundaries. Avoid during strong trends. Combine with volume analysis for better entries."
    }
}


@router.post("/create-from-template", response_model=ConfigResponse)
async def create_strategy_from_template(request: StrategyTemplate):
    """
    Create a new strategy configuration from a template.
    
    This endpoint:
    1. Creates a new configuration with template settings
    2. Creates configuration ready for new Hummingbot API integration
    3. Returns configuration details for frontend
    """
    try:
        # Validate template
        if request.template not in STRATEGY_TEMPLATES:
            raise HTTPException(400, f"Invalid template: {request.template}")
        
        template = STRATEGY_TEMPLATES[request.template]
        
        # Generate config_id
        config_id = str(uuid.uuid4())
        
        # Create config name if not provided
        config_name = request.config_name or f"{template['name']} - {request.symbol}"
        
        # Adjust risk parameters based on risk_level
        risk_multiplier = {"low": 0.5, "medium": 1.0, "high": 1.5}.get(request.risk_level, 1.0)
        
        # Build configuration data
        config_data = {
            "user_id": request.user_id,
            "decision": {
                "llm_provider": "deepseek",
                "strategy": template["strategy"],
                "risk_guidelines": template["risk_guidelines"],
                "additional_context": template["additional_context"]
            },
            "trading": {
                "exchange": "binance_paper",
                "symbol": request.symbol,
                "risk_rules": {
                    "max_position_size_pct": 0.05 * risk_multiplier,
                    "max_leverage": 3 * risk_multiplier,
                    "stop_loss_pct": 0.02,
                    "take_profit_pct": 0.05
                }
            },
            "extraction": {
                "sources": {
                    "crypto_indicators_mcp": {
                        "enabled": True,
                        "indicators": ["RSI_15m", "RSI_1h", "MACD_1h", "BollingerBands_1h", "ATR_1h", "VWAP_1h"]
                    }
                }
            }
        }
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Insert configuration
            cur.execute("""
                INSERT INTO configurations (config_id, user_id, config_name, config_type, config_data, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING created_at, updated_at
            """, (config_id, request.user_id, config_name, template["type"], psycopg2.extras.Json(config_data)))
            
            timestamps = cur.fetchone()
            created_at, updated_at = timestamps
            
            # Note: Instance mapping will be handled by new Hummingbot API integration
            
            conn.commit()
            
            logger.bind(module="config_api").info(
                f"Created config {config_id} from template {request.template} for user {request.user_id}"
            )
            
            return ConfigResponse(
                config_id=config_id,
                config_name=config_name,
                config_type=template["type"],
                user_id=request.user_id,
                created_at=created_at,
                updated_at=updated_at,
                editable=True,  # Template configs are editable
                is_flagship=False
            )
            
    except Exception as e:
        logger.bind(module="config_api").error(f"Failed to create config from template: {e}")
        raise HTTPException(500, f"Failed to create configuration: {str(e)}")


@router.put("/{config_id}")
async def update_config(config_id: str, updates: ConfigUpdate):
    """
    Update a configuration if it's editable.
    
    Flagship configurations (like ggShot) cannot be edited.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Check if config exists and is editable
            cur.execute("""
                SELECT config_type, config_data 
                FROM configurations 
                WHERE config_id = %s
            """, (config_id,))
            
            config = cur.fetchone()
            if not config:
                raise HTTPException(404, "Configuration not found")
            
            config_type, config_data = config
            
            # Check if this is a flagship config (non-editable)
            if config_type in ["ggshot", "ggshot_production"]:
                raise HTTPException(403, "Flagship ggBot cannot be edited")
            
            # Apply updates to config_data
            if updates.config_name is not None:
                cur.execute("""
                    UPDATE configurations 
                    SET config_name = %s, updated_at = NOW()
                    WHERE config_id = %s
                """, (updates.config_name, config_id))
            
            if any([updates.strategy, updates.risk_guidelines, updates.additional_context]):
                # Update decision configuration
                if "decision" not in config_data:
                    config_data["decision"] = {}
                
                if updates.strategy is not None:
                    config_data["decision"]["strategy"] = updates.strategy
                if updates.risk_guidelines is not None:
                    config_data["decision"]["risk_guidelines"] = updates.risk_guidelines
                if updates.additional_context is not None:
                    config_data["decision"]["additional_context"] = updates.additional_context
                
                cur.execute("""
                    UPDATE configurations 
                    SET config_data = %s, updated_at = NOW()
                    WHERE config_id = %s
                """, (psycopg2.extras.Json(config_data), config_id))
            
            conn.commit()
            
            logger.bind(module="config_api").info(f"Updated config {config_id}")
            
            return {"status": "success", "message": "Configuration updated"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.bind(module="config_api").error(f"Failed to update config {config_id}: {e}")
        raise HTTPException(500, f"Failed to update configuration: {str(e)}")


@router.get("/{config_id}")
async def get_single_config(config_id: str):
    """
    Get a single configuration by config_id.
    
    Returns the complete config_data JSONB for the specified configuration.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    c.config_id,
                    c.config_name,
                    c.config_type,
                    c.user_id,
                    c.config_data,
                    c.created_at,
                    c.updated_at
                FROM configurations c
                WHERE c.config_id = %s
            """, (config_id,))
            
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Configuration not found")
            
            config_id, config_name, config_type, user_id, config_data, created_at, updated_at = row
            
            # Determine if config is editable
            is_flagship = config_type in ["ggshot", "ggshot_production"]
            
            return {
                "config_id": str(config_id),
                "config_name": config_name,
                "config_type": config_type,
                "user_id": str(user_id),
                "config_data": config_data,
                "created_at": created_at,
                "updated_at": updated_at,
                "editable": not is_flagship,
                "is_flagship": is_flagship
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.bind(module="config_api").error(f"Failed to get config {config_id}: {e}")
        raise HTTPException(500, f"Failed to get configuration: {str(e)}")


@router.get("/{config_id}/permissions", response_model=ConfigPermissions)
async def get_config_permissions(config_id: str):
    """
    Get permissions for a configuration.
    
    Returns whether the config is editable and if it's a flagship bot.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT config_type, user_id
                FROM configurations
                WHERE config_id = %s
            """, (config_id,))
            
            config = cur.fetchone()
            if not config:
                raise HTTPException(404, "Configuration not found")
            
            config_type, user_id = config
            
            # Determine if config is editable
            is_flagship = config_type in ["ggshot", "ggshot_production"]
            editable = not is_flagship
            
            return ConfigPermissions(
                editable=editable,
                is_flagship=is_flagship,
                config_type=config_type,
                owner_id=str(user_id)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.bind(module="config_api").error(f"Failed to get permissions for {config_id}: {e}")
        raise HTTPException(500, f"Failed to get permissions: {str(e)}")


@router.get("/user/{user_id}", response_model=List[ConfigResponse])
async def get_user_configs(user_id: str):
    """
    Get all configurations for a user.
    """
    try:
        configs = []
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    c.config_id,
                    c.config_name,
                    c.config_type,
                    c.user_id,
                    c.created_at,
                    c.updated_at
                FROM configurations c
                WHERE c.user_id = %s
                ORDER BY c.created_at DESC
            """, (user_id,))
            
            rows = cur.fetchall()
            
            for row in rows:
                config_id, config_name, config_type, user_id, created_at, updated_at = row
                
                is_flagship = config_type in ["ggshot", "ggshot_production"]
                
                configs.append(ConfigResponse(
                    config_id=str(config_id),
                    config_name=config_name,
                    config_type=config_type,
                    user_id=str(user_id),
                    created_at=created_at,
                    updated_at=updated_at,
                    editable=not is_flagship,
                    is_flagship=is_flagship,
                    instance_name=instance_name,
                    paper_balance=float(balance) if balance else 10000.0
                ))
        
        return configs
        
    except Exception as e:
        logger.bind(module="config_api").error(f"Failed to get configs for user {user_id}: {e}")
        raise HTTPException(500, f"Failed to get configurations: {str(e)}")


@router.delete("/{config_id}")
async def delete_config(config_id: str):
    """
    Delete a configuration if it's not a flagship bot.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Check if config exists and is deletable
            cur.execute("""
                SELECT config_type 
                FROM configurations 
                WHERE config_id = %s
            """, (config_id,))
            
            config = cur.fetchone()
            if not config:
                raise HTTPException(404, "Configuration not found")
            
            config_type = config[0]
            
            # Check if this is a flagship config (non-deletable)
            if config_type in ["ggshot", "ggshot_production"]:
                raise HTTPException(403, "Flagship ggBot cannot be deleted")
            
            # Note: Instance cleanup will be handled by new Hummingbot API integration
            
            # Delete configuration
            cur.execute("DELETE FROM configurations WHERE config_id = %s", (config_id,))
            
            conn.commit()
            
            logger.bind(module="config_api").info(f"Deleted config {config_id}")
            
            return {"status": "success", "message": "Configuration deleted"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.bind(module="config_api").error(f"Failed to delete config {config_id}: {e}")
        raise HTTPException(500, f"Failed to delete configuration: {str(e)}")


# Import required for database operations
import psycopg2
import psycopg2.extras