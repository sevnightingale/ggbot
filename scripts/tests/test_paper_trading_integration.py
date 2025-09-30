"""
Test integration between Account domain model and Paper Trading Service.

Validates that the paper trading service correctly uses the Account domain model
and repository for balance management and trade execution.
"""

import asyncio
import uuid
from decimal import Decimal
from unittest.mock import patch, AsyncMock, MagicMock

from core.domain.models.account import Account, AccountType
from core.domain.models.value_objects import Money
from trading.paper.service import PaperTradingService
from core.config import BotConfig, PositionSizingMethod


class TestPaperTradingIntegration:
    """Test paper trading integration with Account domain model."""
    
    def create_test_config(self) -> BotConfig:
        """Create test configuration."""
        config = BotConfig()
        config.trading.position_sizing.method = PositionSizingMethod.FIXED_USD
        config.trading.position_sizing.fixed_amount_usd = 1000.0
        config.trading.risk_management.max_positions = 3
        return config
    
    def create_test_account(self) -> Account:
        """Create test account."""
        return Account(
            account_id=uuid.uuid4(),
            config_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_type=AccountType.PAPER,
            initial_balance=Money(amount=Decimal("10000.00"), currency="USD"),
            current_balance=Money(amount=Decimal("10000.00"), currency="USD")
        )
    
    @patch('trading.paper.service.config_repo')
    @patch('trading.paper.service.MarketDataAdapter')
    async def test_execute_trade_intent_with_domain_model(self, mock_market_data, mock_config_repo):
        """Test trade execution using Account domain model."""
        
        # Setup mocks
        service = PaperTradingService()
        
        config = self.create_test_config()
        account = self.create_test_account()
        
        mock_config_repo.get_config.return_value = config
        
        # Patch the service's account_repo instance directly
        with patch.object(service, 'account_repo') as mock_account_repo:
            mock_account_repo.get_or_create = AsyncMock(return_value=account)
            mock_account_repo.save = AsyncMock(return_value=True)
        
            # Mock market data
            mock_price = MagicMock()
            mock_price.mid = 50000.0
            mock_market_data_instance = AsyncMock()
            mock_market_data_instance.get_current_price.return_value = mock_price
            mock_market_data.return_value = mock_market_data_instance
            service.market_data = mock_market_data_instance
            
            # Mock database operations
            with patch.object(service, '_get_db_connection') as mock_db:
                mock_conn = MagicMock()
                mock_cur = MagicMock()
                mock_db.return_value.__enter__ = MagicMock(return_value=mock_conn)
                mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
                
                # Mock position limit check
                with patch.object(service, '_check_position_limits', return_value=(True, None)):
                    
                    # Create trade intent
                    intent = {
                        "config_id": str(account.config_id),
                        "user_id": str(account.user_id),
                        "symbol": "BTC/USDT",
                        "action": "long",
                        "confidence": 0.75,
                        "decision_id": str(uuid.uuid4())
                    }
                    
                    # Execute trade
                    result = await service.execute_trade_intent(intent)
                    
                    # Debug the result
                    print(f"Trade execution result: {result}")
                    
                    # Verify result
                    if result["status"] != "executed":
                        print(f"Expected 'executed', got '{result['status']}', reason: {result.get('reason', 'Unknown')}")
                    
                    assert result["status"] == "executed"
                    assert "trade_id" in result
                    
                    # Verify account operations were called
                    mock_account_repo.get_or_create.assert_called_once_with(
                        config_id=str(account.config_id),
                        user_id=str(account.user_id),
                        initial_balance=Money(amount=Decimal("10000.00"), currency="USD")
                    )
                    
                    # Verify account was saved with updated state
                    mock_account_repo.save.assert_called_once()
                    saved_account = mock_account_repo.save.call_args[0][0]
                    
                    # Account should have reserved balance for trade + fees
                    # $1000 position + ~$0.60 fees = reduced balance
                    assert saved_account.current_balance.amount < Decimal("10000.00")
                    assert saved_account.statistics.open_positions == 1
                    
                    # Database operations should have been called
                    assert mock_cur.execute.call_count >= 2  # INSERT trade + INSERT order


if __name__ == "__main__":
    # Run basic integration test
    print("Running Paper Trading + Account Domain integration test...")
    
    async def run_test():
        test = TestPaperTradingIntegration()
        
        try:
            await test.test_execute_trade_intent_with_domain_model()
            print("\n✅ Integration test passed!")
            print("   - Account domain model creation: SUCCESS")
            print("   - Paper trading service integration: SUCCESS") 
            print("   - Balance reservation logic: SUCCESS")
            print("   - Repository pattern usage: SUCCESS")
            
        except Exception as e:
            print(f"\n❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Run async test
    asyncio.run(run_test())
    
    print("\n🎉 Paper Trading + Account Domain integration complete!")
    print("\nNext steps:")
    print("   1. Run with pytest: pytest tests/test_paper_trading_integration.py")
    print("   2. Test with real database connection")
    print("   3. Update other modules to use domain models")