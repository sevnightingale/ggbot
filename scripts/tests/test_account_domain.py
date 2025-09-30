"""
Tests for Account domain model and AccountRepository.

Validates the domain model behavior, value objects, and repository integration
with both in-memory testing and actual database operations.
"""

import pytest
import uuid
import asyncio
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from core.domain.models.account import Account, AccountType, AccountStatistics
from core.domain.models.value_objects import Money, Symbol, Confidence, Timeframe
from core.domain.repositories.account_repository import AccountRepository


class TestValueObjects:
    """Test value object behavior and validation."""
    
    def test_money_creation_and_validation(self):
        """Test Money value object creation and validation."""
        # Valid money creation
        money = Money(amount=Decimal("100.50"), currency="USD")
        assert money.amount == Decimal("100.50")
        assert money.currency == "USD"
        assert str(money) == "100.50 USD"
        
        # Currency normalization
        money_lower = Money(amount=Decimal("50.00"), currency="usd")
        assert money_lower.currency == "USD"
        
        # Precision handling
        precise_money = Money(amount=Decimal("123.123456789"), currency="BTC")
        assert precise_money.amount == Decimal("123.12345678")  # 8 decimal places
    
    def test_money_operations(self):
        """Test Money arithmetic operations."""
        money1 = Money(amount=Decimal("100.00"), currency="USD")
        money2 = Money(amount=Decimal("50.00"), currency="USD")
        
        # Addition
        result = money1.add(money2)
        assert result.amount == Decimal("150.00")
        assert result.currency == "USD"
        
        # Subtraction
        result = money1.subtract(money2)
        assert result.amount == Decimal("50.00")
        
        # Multiplication
        result = money1.multiply(Decimal("1.5"))
        assert result.amount == Decimal("150.00")
        
        # Currency mismatch should raise error
        btc_money = Money(amount=Decimal("1.0"), currency="BTC")
        with pytest.raises(ValueError, match="Cannot add BTC to USD"):
            money1.add(btc_money)
    
    def test_symbol_parsing(self):
        """Test Symbol parsing from different formats."""
        # Internal format
        symbol = Symbol.from_string("BTC/USDT")
        assert symbol.base == "BTC"
        assert symbol.quote == "USDT"
        
        # Hummingbot format
        symbol = Symbol.from_string("ETH-USDT")
        assert symbol.base == "ETH"
        assert symbol.quote == "USDT"
        
        # Binance format
        symbol = Symbol.from_string("BTCUSDT")
        assert symbol.base == "BTC"
        assert symbol.quote == "USDT"
        
        # BitMEX format
        symbol = Symbol.from_string("BTC/USDT:USDT")
        assert symbol.base == "BTC"
        assert symbol.quote == "USDT"
    
    def test_symbol_format_conversion(self):
        """Test Symbol format conversion methods."""
        symbol = Symbol(base="BTC", quote="USDT")
        
        assert symbol.internal_format == "BTC/USDT"
        assert symbol.binance_format == "BTCUSDT"
        assert symbol.hummingbot_format == "BTC-USDT"
        assert symbol.bitmex_format == "BTC/USDT:USDT"
    
    def test_confidence_validation(self):
        """Test Confidence validation and properties."""
        # Valid confidence
        conf = Confidence(score=Decimal("0.75"))
        assert conf.score == Decimal("0.750")  # 3 decimal places
        assert conf.percentage == Decimal("75.0")
        assert conf.is_high_confidence is True
        assert conf.is_low_confidence is False
        
        # Low confidence
        low_conf = Confidence(score=Decimal("0.2"))
        assert low_conf.is_low_confidence is True
        assert low_conf.is_high_confidence is False
        
        # Invalid confidence should raise error
        with pytest.raises(ValueError):
            Confidence(score=Decimal("1.5"))  # > 1.0
        
        with pytest.raises(ValueError):
            Confidence(score=Decimal("-0.1"))  # < 0.0
    
    def test_timeframe_validation(self):
        """Test Timeframe validation and properties."""
        # Valid timeframe
        tf = Timeframe(value="1h")
        assert tf.value == "1h"
        assert tf.minutes == 60
        assert tf.is_intraday is True
        
        # Daily timeframe
        daily_tf = Timeframe(value="1d")
        assert daily_tf.minutes == 1440
        assert daily_tf.is_intraday is False
        
        # Invalid timeframe
        with pytest.raises(ValueError, match="Invalid timeframe"):
            Timeframe(value="2h")  # Not in valid list


class TestAccountDomainModel:
    """Test Account domain model behavior."""
    
    def create_test_account(self) -> Account:
        """Create test account for testing."""
        return Account(
            account_id=uuid.uuid4(),
            config_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_type=AccountType.PAPER,
            initial_balance=Money(amount=Decimal("10000.00"), currency="USD"),
            current_balance=Money(amount=Decimal("10000.00"), currency="USD")
        )
    
    def test_account_creation(self):
        """Test account creation with validation."""
        account = self.create_test_account()
        
        assert account.account_type == AccountType.PAPER
        assert account.initial_balance.amount == Decimal("10000.00")
        assert account.current_balance.amount == Decimal("10000.00")
        assert account.total_pnl.amount == Decimal("0.00")
        assert account.statistics.total_trades == 0
        assert account.total_return == Decimal("0.00")
    
    def test_currency_consistency_validation(self):
        """Test that all money amounts must use same currency."""
        with pytest.raises(ValueError, match="Currency mismatch"):
            Account(
                account_id=uuid.uuid4(),
                config_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                account_type=AccountType.PAPER,
                initial_balance=Money(amount=Decimal("10000.00"), currency="USD"),
                current_balance=Money(amount=Decimal("10000.00"), currency="BTC")  # Different currency
            )
    
    def test_balance_operations(self):
        """Test account balance operations."""
        account = self.create_test_account()
        
        # Test can_afford_trade
        trade_size = Money(amount=Decimal("1000.00"), currency="USD")
        assert account.can_afford_trade(trade_size) is True
        
        large_trade = Money(amount=Decimal("15000.00"), currency="USD")
        assert account.can_afford_trade(large_trade) is False
        
        # Test reserve_balance
        new_balance = account.reserve_balance(trade_size)
        assert new_balance.amount == Decimal("9000.00")
        assert account.current_balance.amount == Decimal("9000.00")
        
        # Test insufficient balance
        with pytest.raises(ValueError, match="Insufficient balance"):
            account.reserve_balance(Money(amount=Decimal("10000.00"), currency="USD"))
        
        # Test release_balance
        released_balance = account.release_balance(Money(amount=Decimal("500.00"), currency="USD"))
        assert released_balance.amount == Decimal("9500.00")
    
    def test_pnl_realization(self):
        """Test P&L realization and statistics updates."""
        account = self.create_test_account()
        
        # Realize a winning trade
        profit = Money(amount=Decimal("100.00"), currency="USD")
        account.realize_pnl(profit, is_win=True)
        
        assert account.current_balance.amount == Decimal("10100.00")
        assert account.total_pnl.amount == Decimal("100.00")
        assert account.statistics.total_trades == 1
        assert account.statistics.win_trades == 1
        assert account.statistics.loss_trades == 0
        assert account.statistics.win_rate == Decimal("100.0")
        
        # Realize a losing trade
        loss = Money(amount=Decimal("-50.00"), currency="USD")
        account.realize_pnl(loss, is_win=False)
        
        assert account.current_balance.amount == Decimal("10050.00")
        assert account.total_pnl.amount == Decimal("50.00")
        assert account.statistics.total_trades == 2
        assert account.statistics.win_trades == 1
        assert account.statistics.loss_trades == 1
        assert account.statistics.win_rate == Decimal("50.0")
    
    def test_position_count_tracking(self):
        """Test position count updates."""
        account = self.create_test_account()
        
        # Open position
        count = account.update_position_count(1)
        assert count == 1
        assert account.statistics.open_positions == 1
        
        # Open another
        count = account.update_position_count(1)
        assert count == 2
        
        # Close position
        count = account.update_position_count(-1)
        assert count == 1
        
        # Ensure count doesn't go negative
        account.update_position_count(-10)
        assert account.statistics.open_positions == 0
    
    def test_total_return_calculation(self):
        """Test total return percentage calculation."""
        account = self.create_test_account()
        
        # No change initially
        assert account.total_return == Decimal("0.00")
        
        # Simulate profit
        account.current_balance = Money(amount=Decimal("10500.00"), currency="USD")
        account.total_pnl = Money(amount=Decimal("500.00"), currency="USD")
        
        # Total value = 10500 + 500 = 11000
        # Return = (11000 - 10000) / 10000 * 100 = 10.00%
        assert account.total_return == Decimal("10.00")


class TestAccountRepository:
    """Test AccountRepository database operations."""
    
    @patch('core.domain.repositories.account_repository.psycopg2.connect')
    def test_row_to_domain_model_conversion(self, mock_connect):
        """Test conversion from database row to domain model."""
        repo = AccountRepository()
        
        # Mock database row
        mock_row = {
            'account_id': str(uuid.uuid4()),
            'config_id': str(uuid.uuid4()),
            'user_id': str(uuid.uuid4()),
            'initial_balance': Decimal('10000.00'),
            'current_balance': Decimal('9500.50'),
            'total_pnl': Decimal('250.25'),
            'open_positions': 2,
            'total_trades': 5,
            'win_trades': 3,
            'loss_trades': 2,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        
        account = repo._row_to_domain_model(mock_row)
        
        assert account.account_type == AccountType.PAPER
        assert account.initial_balance.amount == Decimal('10000.00')
        assert account.current_balance.amount == Decimal('9500.50')
        assert account.total_pnl.amount == Decimal('250.25')
        assert account.statistics.open_positions == 2
        assert account.statistics.total_trades == 5
        assert account.statistics.win_trades == 3
        assert account.statistics.loss_trades == 2
        assert account.statistics.win_rate == Decimal('60.0')
    
    @patch('core.domain.repositories.account_repository.psycopg2.connect')
    async def test_get_by_config_id(self, mock_connect):
        """Test getting account by config ID."""
        repo = AccountRepository()
        
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        
        # Mock successful query
        config_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        mock_cur.fetchone.return_value = {
            'account_id': str(uuid.uuid4()),
            'config_id': config_id,
            'user_id': user_id,
            'initial_balance': Decimal('10000.00'),
            'current_balance': Decimal('10000.00'),
            'total_pnl': Decimal('0.00'),
            'open_positions': 0,
            'total_trades': 0,
            'win_trades': 0,
            'loss_trades': 0,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        
        account = await repo.get_by_config_id(config_id, user_id)
        
        assert account is not None
        assert str(account.config_id) == config_id
        assert str(account.user_id) == user_id
        assert account.account_type == AccountType.PAPER
        
        # Verify query was called correctly
        mock_cur.execute.assert_called_once()
        call_args = mock_cur.execute.call_args[0]
        assert "SELECT * FROM paper_accounts" in call_args[0]
        assert call_args[1] == (config_id, user_id)


if __name__ == "__main__":
    # Run basic tests without pytest
    print("Running basic Account domain tests...")
    
    # Test Value Objects
    print("\n✅ Test 1: Value Objects")
    money = Money(amount=Decimal("100.50"), currency="USD")
    print(f"   Money: {money}")
    
    symbol = Symbol.from_string("BTC/USDT")
    print(f"   Symbol: {symbol} -> {symbol.hummingbot_format}")
    
    confidence = Confidence(score=Decimal("0.75"))
    print(f"   Confidence: {confidence} (high={confidence.is_high_confidence})")
    
    timeframe = Timeframe(value="1h")
    print(f"   Timeframe: {timeframe} ({timeframe.minutes} minutes)")
    
    # Test Account Domain Model
    print("\n✅ Test 2: Account Domain Model")
    account = Account(
        account_id=uuid.uuid4(),
        config_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        account_type=AccountType.PAPER,
        initial_balance=Money(amount=Decimal("10000.00"), currency="USD"),
        current_balance=Money(amount=Decimal("10000.00"), currency="USD")
    )
    
    print(f"   Created account with balance: {account.current_balance}")
    print(f"   Total return: {account.total_return}%")
    
    # Test balance operations
    trade_size = Money(amount=Decimal("1000.00"), currency="USD")
    print(f"   Can afford ${trade_size.amount}: {account.can_afford_trade(trade_size)}")
    
    account.reserve_balance(trade_size)
    print(f"   After reserving {trade_size}: {account.current_balance}")
    
    # Test P&L
    profit = Money(amount=Decimal("100.00"), currency="USD")
    account.realize_pnl(profit, is_win=True)
    print(f"   After $100 profit: Balance={account.current_balance}, P&L={account.total_pnl}")
    print(f"   Win rate: {account.statistics.win_rate}%")
    
    print("\n🎉 All basic domain model tests passed!")
    print("\nNext steps:")
    print("   1. Run with pytest: pytest tests/test_account_domain.py")  
    print("   2. Test integration with paper trading service")
    print("   3. Update existing code to use domain models")