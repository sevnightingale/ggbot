"""
End-to-End Tests for GGBot V2 Orchestrator

Tests the complete V2 orchestrator flow with Supabase integration.
"""

import pytest
import asyncio
import os
import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

# Import the V2 orchestrator
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from ggbot import app, orchestrator
from core.services.config_service import ConfigService, BotConfigV2
from core.services.user_service import UserService
from core.auth.supabase_auth import AuthenticatedUser, get_current_user_v2


class TestV2Orchestrator:
    """Test suite for V2 orchestrator functionality."""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        return AuthenticatedUser(
            user_id="test-user-123",
            email="test@example.com",
            claims={"sub": "test-user-123", "email": "test@example.com"}
        )
    
    @pytest.fixture
    def sample_config(self):
        """Sample bot configuration."""
        return {
            "config_name": "Test Bot V2",
            "selected_pair": "BTC/USDT",
            "extraction": {
                "timeframe": "1h",
                "limit": 100,
                "connector": "kucoin",
                "indicators": ["RSI", "MACD", "EMA", "SMA"]
            },
            "decision": {
                "system_prompt": "You are a test trading bot analyzing {SYMBOL}.",
                "user_prompt": "Based on the market data, should I ENTER, WAIT, or EXIT? Provide your decision with confidence level."
            },
            "trading": {
                "execution_mode": "paper",
                "position_sizing": {
                    "method": "confidence_based",
                    "fixed_amount_usd": 100
                },
                "risk_management": {
                    "max_positions": 3,
                    "default_stop_loss_percent": 3.0
                }
            }
        }
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "GGBot V2 Orchestrator"
        assert data["version"] == "2.0.0"
        assert "features" in data
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_config_service_operations(self):
        """Test configuration service CRUD operations."""
        config_service = ConfigService()
        user_id = "test-user-123"
        
        # Test create config
        config_data = {
            "selected_pair": "BTC/USDT",
            "extraction": {"indicators": ["RSI"]},
            "decision": {
                "system_prompt": "Test system prompt",
                "user_prompt": "Test user prompt"
            },
            "trading": {"execution_mode": "paper"}
        }
        
        with patch('core.common.db.get_db_connection') as mock_db:
            # Mock database operations
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Test create
            config = await config_service.create_config(
                user_id=user_id,
                config_name="Test Config",
                config_data=config_data
            )
            
            assert config is not None
            assert config.user_id == user_id
            assert config.config_name == "Test Config"
            assert config.selected_pair == "BTC/USDT"
    
    @pytest.mark.asyncio
    async def test_orchestrator_extraction_phase(self):
        """Test orchestrator extraction phase."""
        # Mock the extraction engine
        with patch('extraction.v2.extraction_engine.ExtractionEngineV2') as mock_extraction:
            mock_engine = AsyncMock()
            mock_extraction.return_value = mock_engine
            
            # Mock successful extraction result
            mock_engine.extract_for_symbol.return_value = {
                "status": "success",
                "result": {
                    "symbol": "BTC/USDT",
                    "indicators": {
                        "RSI": 45.5,
                        "MACD": {"macd": 0.02, "signal": 0.01},
                        "EMA": 50000.0
                    },
                    "ohlcv_summary": {
                        "latest_price": 50000.0
                    }
                }
            }
            
            # Create test config
            config = BotConfigV2(
                config_id="test-config-123",
                user_id="test-user-123",
                config_name="Test Config",
                selected_pair="BTC/USDT",
                extraction={"timeframe": "1h", "limit": 100},
                decision={"system_prompt": "test", "user_prompt": "test"},
                trading={"execution_mode": "paper"}
            )
            
            # Test extraction
            result = await orchestrator._run_extraction_v2(
                config=config,
                user_id="test-user-123",
                indicators=["RSI", "MACD", "EMA"]
            )
            
            assert result["status"] == "success"
            assert "indicators" in result["result"]
            mock_engine.extract_for_symbol.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_orchestrator_decision_phase(self):
        """Test orchestrator decision phase with LLM integration."""
        # Mock LLM service
        with patch('core.services.llm_service.LLMService') as mock_llm_service:
            mock_service = AsyncMock()
            mock_llm_service.return_value = mock_service
            
            # Mock LLM client
            mock_client = AsyncMock()
            mock_service.get_llm_client.return_value = mock_client
            
            # Mock LLM response
            mock_client.generate_completion.return_value = {
                "status": "success",
                "content": "Decision: ENTER\nConfidence: 75%\nReasoning: RSI indicates oversold condition.",
                "usage": {"total_tokens": 100}
            }
            
            # Set up orchestrator with mocked service
            orchestrator.llm_service = mock_service
            
            # Create test config
            config = BotConfigV2(
                config_id="test-config-123",
                user_id="test-user-123",
                config_name="Test Config",
                selected_pair="BTC/USDT",
                extraction={},
                decision={
                    "system_prompt": "You are analyzing {SYMBOL}",
                    "user_prompt": "Make a decision based on {MARKET_DATA}"
                },
                trading={"execution_mode": "paper"}
            )
            
            # Mock extraction result
            extraction_result = {
                "status": "success",
                "result": {
                    "indicators": {"RSI": 25.5},
                    "ohlcv_summary": {"latest_price": 50000}
                }
            }
            
            # Test decision
            result = await orchestrator._run_decision_v2(
                config=config,
                user_id="test-user-123",
                extraction_result=extraction_result
            )
            
            assert result["status"] == "success"
            assert result["action"] == "enter"
            assert result["confidence"] == 0.75
            assert "reasoning" in result
    
    @pytest.mark.asyncio
    async def test_full_orchestration_cycle(self):
        """Test complete orchestration cycle (integration test)."""
        # This would require more extensive mocking or a test database
        # For now, we'll test the orchestration structure
        
        with patch.multiple(
            orchestrator,
            _run_extraction_v2=AsyncMock(return_value={
                "status": "success",
                "result": {"indicators": {"RSI": 30}}
            }),
            _run_decision_v2=AsyncMock(return_value={
                "status": "success",
                "action": "enter",
                "confidence": 0.8
            }),
            _run_trading_v2=AsyncMock(return_value={
                "status": "success",
                "trade_id": "test-trade-123"
            })
        ):
            # Mock config service
            with patch.object(orchestrator.config_service, 'get_config') as mock_get_config:
                mock_config = BotConfigV2(
                    config_id="test-config-123",
                    user_id="test-user-123",
                    config_name="Test Config",
                    selected_pair="BTC/USDT",
                    extraction={"indicators": ["RSI"]},
                    decision={"system_prompt": "test", "user_prompt": "test"},
                    trading={"execution_mode": "paper"}
                )
                mock_get_config.return_value = mock_config
                
                # Mock indicator service
                with patch.object(orchestrator.indicator_service, 'get_user_available_indicators') as mock_indicators:
                    mock_indicators.return_value = [
                        {"name": "RSI", "requires_premium": False}
                    ]
                    
                    # Run orchestration
                    result = await orchestrator.run_autonomous_cycle(
                        config_id="test-config-123",
                        user_id="test-user-123"
                    )
                    
                    assert result.status == "success"
                    assert result.config_id == "test-config-123"
                    assert result.extraction_result is not None
                    assert result.decision_result is not None
                    assert result.trading_result is not None
                    assert result.execution_time_ms > 0


class TestV2Authentication:
    """Test V2 authentication and authorization."""
    
    def test_unauthenticated_request(self):
        """Test that unauthenticated requests are rejected."""
        client = TestClient(app)
        
        response = client.get("/api/v2/config")
        assert response.status_code == 401
    
    def test_invalid_token(self):
        """Test invalid JWT token handling."""
        client = TestClient(app)
        
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v2/config", headers=headers)
        assert response.status_code == 401


class TestV2ConfigEndpoints:
    """Test V2 configuration API endpoints."""
    
    @pytest.fixture
    def mock_auth_user(self):
        """Mock authenticated user for dependency injection."""
        return AuthenticatedUser(
            user_id="test-user-123",
            email="test@example.com", 
            claims={}
        )
    
    def test_create_config_endpoint(self, mock_auth_user, sample_config):
        """Test config creation endpoint."""
        client = TestClient(app)
        
        # Mock the authentication dependency
        app.dependency_overrides[get_current_user_v2] = lambda: mock_auth_user
        
        try:
            with patch('core.services.config_service.config_service.create_config') as mock_create:
                mock_config = BotConfigV2(
                    config_id="test-config-123",
                    user_id="test-user-123",
                    config_name=sample_config["config_name"],
                    selected_pair=sample_config["selected_pair"],
                    extraction=sample_config["extraction"],
                    decision=sample_config["decision"],
                    trading=sample_config["trading"]
                )
                mock_create.return_value = mock_config
                
                response = client.post("/api/v2/config", json=sample_config)
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert "config" in data
                
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])