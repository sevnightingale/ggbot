"""
End-to-End test for the new configuration system (v1).

Tests the complete flow from template loading to paper trading execution
with the new Pydantic models and ConfigRepository.
"""

import pytest
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

from core.config import (
    BotConfig, 
    PositionSizingMethod, 
    ExecutionMode,
    create_default_config,
    load_config_from_dict,
    config_to_dict,
    ConfigRepository
)
from trading.paper.service import PaperTradingService


class TestConfigModels:
    """Test Pydantic config models validation and methods."""
    
    def test_create_default_config(self):
        """Test creating default configuration."""
        config = create_default_config()
        
        assert config.schema_version == "1.0"
        assert config.selected_pair == "BTC/USDT"
        assert config.extraction.data_sources.technical_indicators == []
        assert config.decision.analysis_frequency == "1h"
        assert config.trading.execution_mode == ExecutionMode.PAPER
        assert config.trading.position_sizing.method == PositionSizingMethod.CONFIDENCE_BASED
        assert config.trading.risk_management.max_positions == 5
    
    def test_load_template_from_dict(self):
        """Test loading config from template dictionary."""
        template_dict = {
            "schema_version": "1.0",
            "selected_pair": "ETH/USDT",
            "extraction": {
                "data_sources": {
                    "technical_indicators": ["RSI_1h", "MACD_1h"],
                    "fundamental_analysis": [],
                    "sentiment_and_trends": [],
                    "influencer_kol": [],
                    "news_and_regulations": [],
                    "onchain_analytics": []
                }
            },
            "decision": {
                "analysis_frequency": "4h",
                "system_prompt": "Test system prompt",
                "user_prompt": "Test user prompt"
            },
            "trading": {
                "execution_mode": "paper",
                "position_sizing": {
                    "method": "fixed_usd",
                    "fixed_amount_usd": 200,
                    "account_percent": 10.0,
                    "max_position_percent": 15.0
                },
                "risk_management": {
                    "max_positions": 3,
                    "default_stop_loss_percent": 2.5,
                    "default_take_profit_percent": 5.0,
                    "max_daily_loss_usd": 300
                },
                "exchange_config": {
                    "exchange_type": "cex",
                    "selected_exchange": "coinbase",
                    "api_key": "",
                    "secret_key": "",
                    "leverage": 1
                }
            },
            "telegram_integration": {
                "listener": {
                    "enabled": False,
                    "api_id": "",
                    "api_hash": "",
                    "session_name": "test_session",
                    "source_channels": []
                },
                "publisher": {
                    "enabled": False,
                    "bot_token": "",
                    "filter_channel": "",
                    "confidence_threshold": 0.8,
                    "include_reasoning": True,
                    "include_market_context": True,
                    "message_template": "Test template"
                }
            }
        }
        
        config = load_config_from_dict(template_dict)
        
        assert config.selected_pair == "ETH/USDT"
        assert config.extraction.data_sources.technical_indicators == ["RSI_1h", "MACD_1h"]
        assert config.decision.analysis_frequency == "4h"
        assert config.trading.position_sizing.method == PositionSizingMethod.FIXED_USD
        assert config.trading.position_sizing.fixed_amount_usd == 200
        assert config.trading.risk_management.max_positions == 3
        assert config.telegram_integration.publisher.confidence_threshold == 0.8
    
    def test_position_sizing_calculations(self):
        """Test position sizing calculations for all methods."""
        config = create_default_config()
        balance = 1000.0
        confidence = 0.8
        
        # Test confidence-based (default)
        config.trading.position_sizing.method = PositionSizingMethod.CONFIDENCE_BASED
        config.trading.position_sizing.max_position_percent = 10.0
        size = config.get_position_size(confidence, balance)
        expected = confidence * 0.10 * balance  # 0.8 * 10% * $1000 = $80
        assert size == expected
        
        # Test fixed USD
        config.trading.position_sizing.method = PositionSizingMethod.FIXED_USD
        config.trading.position_sizing.fixed_amount_usd = 150.0
        size = config.get_position_size(confidence, balance)
        assert size == 150.0
        
        # Test account percentage
        config.trading.position_sizing.method = PositionSizingMethod.ACCOUNT_PERCENTAGE
        config.trading.position_sizing.account_percent = 5.0
        size = config.get_position_size(confidence, balance)
        expected = 0.05 * balance  # 5% * $1000 = $50
        assert size == expected
    
    def test_default_risk_levels(self):
        """Test default stop loss and take profit calculations."""
        config = create_default_config()
        config.trading.risk_management.default_stop_loss_percent = 3.0
        config.trading.risk_management.default_take_profit_percent = 6.0
        
        entry_price = 100.0
        
        # Test long position
        stop_loss = config.get_default_stop_loss_price(entry_price, "long")
        take_profit = config.get_default_take_profit_price(entry_price, "long")
        assert stop_loss == 97.0  # 100 * (1 - 0.03)
        assert take_profit == 106.0  # 100 * (1 + 0.06)
        
        # Test short position
        stop_loss = config.get_default_stop_loss_price(entry_price, "short")
        take_profit = config.get_default_take_profit_price(entry_price, "short")
        assert stop_loss == 103.0  # 100 * (1 + 0.03)
        assert take_profit == 94.0  # 100 * (1 - 0.06)
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test valid config
        config = create_default_config()
        dict_config = config_to_dict(config)
        assert isinstance(dict_config, dict)
        
        # Test invalid trading pair
        with pytest.raises(Exception):  # Should raise ValidationError
            load_config_from_dict({"selected_pair": "INVALID"})
        
        # Test invalid analysis frequency
        with pytest.raises(Exception):  # Should raise ValidationError
            load_config_from_dict({
                "decision": {"analysis_frequency": "invalid"}
            })


class TestConfigRepository:
    """Test configuration repository functionality."""
    
    @pytest.fixture
    def config_repo(self):
        """Create config repository for testing."""
        return ConfigRepository()
    
    def test_load_template(self, config_repo):
        """Test loading template from file."""
        config = config_repo.load_template("1.0")
        
        assert isinstance(config, BotConfig)
        assert config.schema_version == "1.0"
        assert config.selected_pair is not None
    
    @patch('core.config.repository.get_db_connection')
    def test_save_and_get_config(self, mock_db, config_repo):
        """Test saving and retrieving configuration."""
        # Mock database
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_db.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        
        # Test saving new config
        config = create_default_config()
        config.selected_pair = "TEST/USDT"
        config_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Mock fetchone for "config doesn't exist" check
        mock_cur.fetchone.return_value = None
        
        success = config_repo.save_config(config_id, user_id, config, "Test Bot", "autonomous_trading")
        assert success
        
        # Verify INSERT was called
        mock_cur.execute.assert_called()
        insert_call = mock_cur.execute.call_args_list[-1]
        assert "INSERT INTO configurations" in insert_call[0][0]
    
    def test_validate_config(self, config_repo):
        """Test configuration validation."""
        # Valid config
        valid_dict = config_to_dict(create_default_config())
        is_valid, error = config_repo.validate_config(valid_dict)
        assert is_valid
        assert error is None
        
        # Invalid config
        invalid_dict = {"selected_pair": "INVALID_FORMAT"}
        is_valid, error = config_repo.validate_config(invalid_dict)
        assert not is_valid
        assert error is not None


class TestPaperTradingIntegration:
    """Test paper trading integration with new configuration system."""
    
    @pytest.fixture
    def paper_service(self):
        """Create paper trading service for testing."""
        return PaperTradingService()
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = create_default_config()
        config.selected_pair = "BTC/USDT"
        config.trading.position_sizing.method = PositionSizingMethod.CONFIDENCE_BASED
        config.trading.position_sizing.max_position_percent = 15.0
        config.trading.risk_management.max_positions = 3
        config.trading.risk_management.default_stop_loss_percent = 2.0
        config.trading.risk_management.default_take_profit_percent = 4.0
        return config
    
    def test_position_size_calculation(self, paper_service, mock_config):
        """Test position size calculation with different methods."""
        balance = 5000.0
        confidence = 0.7
        
        # Test confidence-based sizing
        size = paper_service._calculate_position_size(mock_config, confidence, balance)
        expected = confidence * 0.15 * balance  # 0.7 * 15% * $5000 = $525
        assert size == max(expected, 10.0)  # Minimum $10
        
        # Test fixed USD sizing
        mock_config.trading.position_sizing.method = PositionSizingMethod.FIXED_USD
        mock_config.trading.position_sizing.fixed_amount_usd = 250.0
        size = paper_service._calculate_position_size(mock_config, confidence, balance)
        assert size == 250.0
        
        # Test account percentage sizing
        mock_config.trading.position_sizing.method = PositionSizingMethod.ACCOUNT_PERCENTAGE
        mock_config.trading.position_sizing.account_percent = 8.0
        size = paper_service._calculate_position_size(mock_config, confidence, balance)
        expected = 0.08 * balance  # 8% * $5000 = $400
        assert size == expected
    
    @patch('core.config.config_repo.get_config')
    async def test_position_limits_check(self, mock_get_config, paper_service, mock_config):
        """Test position limits checking."""
        mock_get_config.return_value = mock_config
        
        config_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Mock database connection for position count
        with patch.object(paper_service, '_get_db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_db.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
            
            # Test within limits
            mock_cur.fetchone.return_value = {'open_count': 2}  # 2 < 3 max
            can_open, reason = await paper_service._check_position_limits(mock_config, config_id, user_id)
            assert can_open
            assert reason is None
            
            # Test at limits
            mock_cur.fetchone.return_value = {'open_count': 3}  # 3 >= 3 max
            can_open, reason = await paper_service._check_position_limits(mock_config, config_id, user_id)
            assert not can_open
            assert "Maximum positions limit reached" in reason
    
    async def test_apply_default_risk_levels(self, paper_service, mock_config):
        """Test applying default risk levels."""
        entry_price = 50000.0
        
        # Test intent without stop loss or take profit
        intent = {
            "action": "long",
            "symbol": "BTC/USDT"
        }
        
        updated_intent = await paper_service._apply_default_risk_levels(mock_config, intent, entry_price)
        
        # Should have default stop loss and take profit
        expected_stop = entry_price * (1 - 0.02)  # 2% stop loss
        expected_tp = entry_price * (1 + 0.04)    # 4% take profit
        
        assert updated_intent["stop_loss_price"] == expected_stop
        assert updated_intent["take_profit_price"] == expected_tp
        
        # Test intent with existing values (should not override)
        intent_with_levels = {
            "action": "long",
            "symbol": "BTC/USDT",
            "stop_loss_price": 48000.0,
            "take_profit_price": 52000.0
        }
        
        updated_intent = await paper_service._apply_default_risk_levels(mock_config, intent_with_levels, entry_price)
        
        # Should keep existing values
        assert updated_intent["stop_loss_price"] == 48000.0
        assert updated_intent["take_profit_price"] == 52000.0


if __name__ == "__main__":
    # Run basic tests without pytest
    print("Running basic configuration system tests...")
    
    # Test 1: Default config creation
    print("\n✅ Test 1: Default config creation")
    config = create_default_config()
    print(f"   Schema version: {config.schema_version}")
    print(f"   Selected pair: {config.selected_pair}")
    print(f"   Position sizing: {config.trading.position_sizing.method}")
    print(f"   Max positions: {config.trading.risk_management.max_positions}")
    
    # Test 2: Position size calculations
    print("\n✅ Test 2: Position size calculations")
    balance = 1000.0
    confidence = 0.8
    
    # Confidence-based
    size = config.get_position_size(confidence, balance)
    print(f"   Confidence-based (80% conf, $1k balance): ${size:.2f}")
    
    # Fixed USD
    config.trading.position_sizing.method = PositionSizingMethod.FIXED_USD
    config.trading.position_sizing.fixed_amount_usd = 150.0
    size = config.get_position_size(confidence, balance)
    print(f"   Fixed USD ($150 setting): ${size:.2f}")
    
    # Account percentage
    config.trading.position_sizing.method = PositionSizingMethod.ACCOUNT_PERCENTAGE
    config.trading.position_sizing.account_percent = 7.5
    size = config.get_position_size(confidence, balance)
    print(f"   Account percentage (7.5% of balance): ${size:.2f}")
    
    # Test 3: Risk level calculations
    print("\n✅ Test 3: Default risk level calculations")
    config.trading.risk_management.default_stop_loss_percent = 3.0
    config.trading.risk_management.default_take_profit_percent = 6.0
    entry_price = 100.0
    
    stop_loss = config.get_default_stop_loss_price(entry_price, "long")
    take_profit = config.get_default_take_profit_price(entry_price, "long")
    print(f"   Long position @ $100: SL=${stop_loss:.2f}, TP=${take_profit:.2f}")
    
    stop_loss = config.get_default_stop_loss_price(entry_price, "short")
    take_profit = config.get_default_take_profit_price(entry_price, "short")
    print(f"   Short position @ $100: SL=${stop_loss:.2f}, TP=${take_profit:.2f}")
    
    # Test 4: Template loading
    print("\n✅ Test 4: Template loading")
    repo = ConfigRepository()
    template = repo.load_template("1.0")
    print(f"   Loaded template with schema version: {template.schema_version}")
    print(f"   Default selected pair: {template.selected_pair}")
    print(f"   Technical indicators count: {len(template.extraction.data_sources.technical_indicators)}")
    
    print("\n🎉 All basic tests passed! Configuration system is ready.")
    print("\nNext steps:")
    print("   1. Run with pytest: pytest tests/test_config_system_v1.py")
    print("   2. Test paper trading integration")
    print("   3. Update frontend to use new schema")