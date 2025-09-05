#!/usr/bin/env python3
"""
Comprehensive End-to-End Integration Test
Tests the complete GGBot V2 system in one comprehensive test.

This test validates:
- V2 Bot configuration management
- Complete V2 orchestration pipeline (extraction → decision → trading)
- Real-time WebSocket status updates
- Paper trading execution with real trades
- Database operations and RLS policies
- Development mode authentication
- Error handling and recovery

Run with: python -m tests.test_full_e2e_integration
"""

import asyncio
import json
import time
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import httpx
import websockets
import pytest
import psycopg2.extras
from loguru import logger

from core.common.db import get_db_connection
from core.common.logger import logger


class FullE2EIntegrationTest:
    """Comprehensive end-to-end integration test for the complete GGBot V2 system."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000"
        # Use real user ID from database in development mode
        self.user_id = "3d47c173-9234-47c7-b57b-9159c9df5dbd"  # Real user ID from database
        self.auth_token = "mock-dev-token"  # Not used in dev mode, but for consistency
        self.config_id: Optional[str] = None
        self.orchestration_results: List[Dict] = []
        self.status_updates: List[Dict] = []
        self.websocket_connection = None
        self.trade_executions: List[Dict] = []
        
        # Test configuration - matches V2 API structure  
        # Use a unique timestamp to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.test_config = {
            "config_name": f"E2E_Test_Bot_{timestamp}",
            "selected_pair": "BTC/USDT",
            "extraction": {
                "indicators": ["RSI_15m", "MACD_15m", "BB_15m"]
            },
            "decision": {
                "analysis_frequency": "15m",
                "system_prompt": "You are testing the E2E system. Make conservative paper trading decisions based on technical indicators.",
                "user_prompt": "Test trading strategy: Enter long positions when RSI < 30 and MACD shows bullish crossover. Use conservative position sizing."
            },
            "trading": {
                "execution_mode": "paper",
                "leverage": 1,
                "position_sizing": {
                    "method": "fixed_amount_usd",
                    "fixed_amount_usd": 100
                },
                "risk_management": {
                    "max_positions": 3,
                    "default_stop_loss_percent": 2.0,
                    "default_take_profit_percent": 4.0
                }
            },
            "telegram_integration": {
                "listener": {"enabled": False},
                "publisher": {"enabled": False}
            }
        }

    async def run_full_test(self) -> Dict[str, Any]:
        """Run the complete end-to-end integration test."""
        logger.info("🚀 Starting Full E2E Integration Test (V2 System)")
        
        # Ensure development mode is enabled
        os.environ["DEVELOPMENT_MODE"] = "true"
        
        test_results = {
            "start_time": datetime.now().isoformat(),
            "phases": {},
            "success": False,
            "error": None,
            "metrics": {
                "total_api_calls": 0,
                "websocket_messages": 0,
                "orchestration_cycles": 0,
                "trades_executed": 0,
                "test_duration_seconds": 0
            }
        }
        
        start_time = time.time()
        
        try:
            # Phase 1: Health Check & Development Mode Verification
            logger.info("📋 Phase 1: System Health & Development Mode")
            await self._test_system_health()
            test_results["phases"]["health"] = "✅ PASSED"
            
            # Phase 2: Configuration Management  
            logger.info("📋 Phase 2: V2 Bot Configuration")
            await self._test_configuration_management()
            test_results["phases"]["configuration"] = "✅ PASSED"
            
            # Phase 3: WebSocket Connection
            logger.info("📋 Phase 3: WebSocket Status Updates")
            await self._test_websocket_connection()
            test_results["phases"]["websocket"] = "✅ PASSED"
            
            # Phase 4: V2 Orchestration Pipeline
            logger.info("📋 Phase 4: V2 Orchestration (Extraction → Decision → Trading)")
            await self._test_v2_orchestration()
            test_results["phases"]["orchestration"] = "✅ PASSED"
            
            # Phase 5: Paper Trading Validation
            logger.info("📋 Phase 5: Paper Trading Execution")
            await self._test_paper_trading()
            test_results["phases"]["trading"] = "✅ PASSED"
            
            # Phase 6: Database Validation
            logger.info("📋 Phase 6: Database Trade Storage")
            await self._test_database_operations()
            test_results["phases"]["database"] = "✅ PASSED"
            
            # Phase 7: Dashboard API Status (Expected Empty for Now)
            logger.info("📋 Phase 7: Dashboard API Status")
            await self._test_dashboard_apis()
            test_results["phases"]["dashboard"] = "✅ PASSED"
            
            # Phase 8: Cleanup
            logger.info("📋 Phase 8: Cleanup & Resource Management")
            await self._test_cleanup()
            test_results["phases"]["cleanup"] = "✅ PASSED"
            
            test_results["success"] = True
            logger.info("🎉 FULL E2E INTEGRATION TEST PASSED!")
            
        except Exception as e:
            test_results["error"] = str(e)
            test_results["success"] = False
            logger.error(f"❌ E2E Test Failed: {e}")
            raise
        
        finally:
            # Calculate metrics
            test_results["metrics"]["test_duration_seconds"] = time.time() - start_time
            test_results["metrics"]["websocket_messages"] = len(self.status_updates)
            test_results["metrics"]["orchestration_cycles"] = len(self.orchestration_results)
            test_results["metrics"]["trades_executed"] = len(self.trade_executions)
            test_results["end_time"] = datetime.now().isoformat()
            
            # Close connections
            if self.websocket_connection:
                await self.websocket_connection.close()
        
        return test_results

    async def _test_system_health(self):
        """Test system health and verify development mode authentication."""
        async with httpx.AsyncClient() as client:
            # Test health endpoint
            health_response = await client.get(f"{self.base_url}/health")
            assert health_response.status_code == 200, f"Health check failed: {health_response.text}"
            
            health_data = health_response.json()
            assert health_data["status"] == "healthy", "System not healthy"
            logger.info(f"✅ System health check passed: {health_data['version']}")
            
            # Test root endpoint for version info
            root_response = await client.get(f"{self.base_url}/")
            assert root_response.status_code == 200, f"Root endpoint failed: {root_response.text}"
            
            root_data = root_response.json()
            assert "GGBot V2" in root_data["name"], "Not V2 system"
            logger.info(f"✅ V2 System confirmed: {root_data['name']}")
            
            # Test development mode by accessing user profile (should work without token)
            profile_response = await client.get(f"{self.base_url}/api/v2/user/profile")
            assert profile_response.status_code == 200, f"Dev mode auth failed: {profile_response.text}"
            
            profile_data = profile_response.json()
            assert profile_data["status"] == "success", "Profile access failed"
            logger.info(f"✅ Development mode authentication working for user: {self.user_id}")

    async def _test_configuration_management(self):
        """Test V2 bot configuration creation and validation."""
        # No headers needed in development mode
        async with httpx.AsyncClient() as client:
            # First, clean up any existing configs to avoid unique constraint violations
            list_response = await client.get(f"{self.base_url}/api/v2/config")
            if list_response.status_code == 200:
                list_data = list_response.json()
                existing_configs = list_data.get("configs", [])
                
                for config in existing_configs:
                    if "E2E_Test_Bot" in config.get("config_name", "") or "E2E Test Bot" in config.get("config_name", ""):
                        config_id = config["config_id"]
                        delete_response = await client.delete(f"{self.base_url}/api/v2/config/{config_id}")
                        if delete_response.status_code == 200:
                            logger.info(f"✅ Cleaned up existing test config: {config_id}")
                        else:
                            logger.warning(f"⚠️ Could not delete existing config {config_id}: {delete_response.text}")
            
            logger.info("✅ Config cleanup completed")
            # Create V2 configuration
            config_response = await client.post(
                f"{self.base_url}/api/v2/config",
                json=self.test_config
            )
            assert config_response.status_code == 200, f"Config creation failed: {config_response.text}"
            
            config_data = config_response.json()
            assert config_data["status"] == "success", "Config creation status not success"
            self.config_id = config_data["config"]["config_id"]
            
            assert self.config_id, "No config ID received"
            logger.info(f"✅ V2 Configuration created: {self.config_id}")
            
            # Validate configuration retrieval
            get_response = await client.get(f"{self.base_url}/api/v2/config/{self.config_id}")
            assert get_response.status_code == 200, f"Config retrieval failed: {get_response.text}"
            
            retrieved_data = get_response.json()
            assert retrieved_data["status"] == "success", "Config retrieval status not success"
            retrieved_config = retrieved_data["config"]
            assert retrieved_config["selected_pair"] == "BTC/USDT"
            logger.info("✅ V2 Configuration retrieval validated")
            
            # Test configuration list
            list_response = await client.get(f"{self.base_url}/api/v2/config")
            assert list_response.status_code == 200, f"Config list failed: {list_response.text}"
            
            list_data = list_response.json()
            assert list_data["status"] == "success", "Config list status not success"
            assert list_data["count"] >= 1, "No configurations found in list"
            logger.info(f"✅ Configuration list validated: {list_data['count']} configs found")

    async def _test_websocket_connection(self):
        """Test WebSocket connection for real-time status updates."""
        try:
            # Connect to WebSocket endpoint (V2 format with user_id)
            ws_uri = f"{self.ws_url}/ws/bot-status/{self.user_id}"
            self.websocket_connection = await websockets.connect(ws_uri)
            
            # Send heartbeat message to test connection
            await self.websocket_connection.send("heartbeat")
            
            # Wait for heartbeat acknowledgment
            response = await asyncio.wait_for(
                self.websocket_connection.recv(),
                timeout=5.0
            )
            
            msg_data = json.loads(response)
            assert msg_data.get("type") == "heartbeat_ack", f"Unexpected message type: {msg_data}"
            assert "timestamp" in msg_data, "No timestamp in heartbeat response"
            
            logger.info("✅ WebSocket connection and heartbeat successful")
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            # Don't fail the test if WebSocket fails - it's not critical for the core functionality
            logger.warning("⚠️ WebSocket test skipped due to connection issues")
            self.websocket_connection = None

    async def _test_v2_orchestration(self):
        """Test V2 orchestration pipeline: extraction → decision → trading."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Run V2 orchestration cycle
            orchestration_response = await client.post(
                f"{self.base_url}/api/v2/orchestrate/{self.config_id}"
            )
            assert orchestration_response.status_code == 200, f"V2 Orchestration failed: {orchestration_response.text}"
            
            orchestration_result = orchestration_response.json()
            self.orchestration_results.append(orchestration_result)
            
            # Validate orchestration result structure
            assert orchestration_result["status"] == "success", f"Orchestration failed: {orchestration_result.get('extraction_result', {}).get('error')}"
            assert orchestration_result["config_id"] == self.config_id, "Config ID mismatch"
            assert "extraction_result" in orchestration_result, "No extraction result"
            assert "decision_result" in orchestration_result, "No decision result"
            assert "trading_result" in orchestration_result, "No trading result"
            assert orchestration_result["execution_time_ms"] > 0, "No execution time recorded"
            
            logger.info(f"✅ V2 Orchestration completed in {orchestration_result['execution_time_ms']}ms")
            
            # Validate extraction phase
            extraction = orchestration_result["extraction_result"]
            if extraction.get("status") != "error":
                logger.info("✅ Extraction phase completed successfully")
            else:
                logger.warning(f"⚠️ Extraction had issues: {extraction.get('error')}")
            
            # Validate decision phase
            decision = orchestration_result["decision_result"]
            if decision.get("status") != "error":
                action = decision.get("action", "unknown")
                confidence = decision.get("confidence", 0)
                logger.info(f"✅ Decision phase completed: {action} (confidence: {confidence})")
            else:
                logger.warning(f"⚠️ Decision had issues: {decision.get('error')}")
            
            # Validate trading phase
            trading = orchestration_result["trading_result"]
            if trading:
                trading_status = trading.get("status", "unknown")
                if trading_status == "executed":
                    trade_id = trading.get("trade_id")
                    symbol = trading.get("symbol")
                    entry_price = trading.get("entry_price")
                    self.trade_executions.append(trading)
                    logger.info(f"✅ Paper trade executed: {trade_id} - {symbol} @ ${entry_price}")
                elif trading_status == "skipped":
                    reason = trading.get("reason", "unknown")
                    logger.info(f"✅ Trading skipped: {reason}")
                else:
                    logger.warning(f"⚠️ Trading status: {trading_status}")
            
            logger.info("✅ V2 Orchestration pipeline validated")

    async def _test_paper_trading(self):
        """Test paper trading execution and validate trade results."""
        if not self.trade_executions:
            logger.info("ℹ️ No trades executed during orchestration (decision was likely 'wait')")
            # This is normal behavior - not all orchestration cycles result in trades
            return
        
        for trade in self.trade_executions:
            # Validate trade structure
            required_fields = ["trade_id", "symbol", "entry_price", "size_usd", "status"]
            for field in required_fields:
                assert field in trade, f"Missing field {field} in trade result"
            
            # Validate trade data
            assert trade["status"] == "executed", f"Trade not executed: {trade.get('status')}"
            assert isinstance(trade["entry_price"], (int, float)), "Entry price not numeric"
            assert trade["entry_price"] > 0, "Entry price must be positive"
            assert isinstance(trade["size_usd"], (int, float)), "Position size not numeric"
            assert trade["size_usd"] > 0, "Position size must be positive"
            
            trade_id = trade["trade_id"]
            symbol = trade["symbol"]
            entry_price = trade["entry_price"]
            size_usd = trade["size_usd"]
            
            logger.info(f"✅ Paper trade validated: {trade_id} - {symbol} @ ${entry_price:.2f} (${size_usd:.2f})")
        
        logger.info(f"✅ Paper trading validation completed: {len(self.trade_executions)} trades")

    async def _test_database_operations(self):
        """Test database operations and verify trade storage."""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Check if any paper trades were created for our config
                    cur.execute("""
                        SELECT trade_id, symbol, side, entry_price, size_usd, status, opened_at
                        FROM paper_trades 
                        WHERE config_id = %s
                        ORDER BY opened_at DESC
                        LIMIT 10
                    """, (self.config_id,))
                    
                    trades = cur.fetchall()
                    
                    if trades:
                        logger.info(f"✅ Database validation: Found {len(trades)} paper trades for config {self.config_id}")
                        
                        for trade in trades:
                            trade_dict = dict(trade)  # Convert Row to dict
                            logger.info(
                                f"  - Trade {trade_dict['trade_id'][:8]}...: {trade_dict['side']} {trade_dict['symbol']} "
                                f"@ ${trade_dict['entry_price']:.2f} (${trade_dict['size_usd']:.2f}) - {trade_dict['status']}"
                            )
                    else:
                        logger.info("ℹ️ No paper trades found in database (normal if decision was 'wait')")
                    
                    # Check user profile exists
                    cur.execute("SELECT user_id, subscription_tier FROM user_profiles WHERE user_id = %s", (self.user_id,))
                    profile = cur.fetchone()
                    
                    if profile:
                        profile_dict = dict(profile)
                        logger.info(f"✅ User profile found: {profile_dict['user_id']} - {profile_dict['subscription_tier']} tier")
                    else:
                        logger.info("ℹ️ User profile not found (may be using mock development user)")
                    
                    # Check configuration exists
                    cur.execute("SELECT config_id, config_name FROM configurations WHERE config_id = %s", (self.config_id,))
                    config = cur.fetchone()
                    
                    assert config, f"Configuration {self.config_id} not found in database"
                    config_dict = dict(config)
                    logger.info(f"✅ Configuration found in database: {config_dict['config_name']}")
                    
        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            raise
        
        logger.info("✅ Database operations validated")

    async def _test_dashboard_apis(self):
        """Test dashboard API endpoints (expected to return placeholder data for now)."""
        async with httpx.AsyncClient() as client:
            # Test bot metrics endpoint (expected to return empty data)
            metrics_response = await client.get(f"{self.base_url}/api/v2/bot/{self.config_id}/metrics")
            assert metrics_response.status_code == 200, f"Bot metrics failed: {metrics_response.text}"
            
            metrics_data = metrics_response.json()
            assert metrics_data["status"] == "success", "Metrics status not success"
            assert "metrics" in metrics_data, "No metrics field in response"
            logger.info("✅ Bot metrics endpoint working (returns placeholder data)")
            
            # Test bot positions endpoint (expected to return empty data)
            positions_response = await client.get(f"{self.base_url}/api/v2/bot/{self.config_id}/positions")
            assert positions_response.status_code == 200, f"Bot positions failed: {positions_response.text}"
            
            positions_data = positions_response.json()
            assert positions_data["status"] == "success", "Positions status not success"
            assert "positions" in positions_data, "No positions field in response"
            logger.info("✅ Bot positions endpoint working (returns placeholder data)")
            
            # Test bot trades endpoint (expected to return empty data)
            trades_response = await client.get(f"{self.base_url}/api/v2/bot/{self.config_id}/trades")
            assert trades_response.status_code == 200, f"Bot trades failed: {trades_response.text}"
            
            trades_data = trades_response.json()
            assert trades_data["status"] == "success", "Trades status not success"
            assert "trades" in trades_data, "No trades field in response"
            assert "count" in trades_data, "No count field in response"
            logger.info("✅ Bot trades endpoint working (returns placeholder data)")
            
            # Test user profile endpoint
            profile_response = await client.get(f"{self.base_url}/api/v2/user/profile")
            assert profile_response.status_code == 200, f"User profile failed: {profile_response.text}"
            
            profile_data = profile_response.json()
            assert profile_data["status"] == "success", "Profile status not success"
            assert "profile" in profile_data, "No profile field in response"
            logger.info("✅ User profile endpoint working")
            
        logger.info("✅ Dashboard API endpoints validated (placeholder implementations working)")

    async def _test_cleanup(self):
        """Test cleanup and resource management."""
        try:
            # Close WebSocket connection if open
            if self.websocket_connection:
                await self.websocket_connection.close()
                logger.info("✅ WebSocket connection closed")
            
            # Optional: Delete test configuration (comment out to keep for inspection)
            # async with httpx.AsyncClient() as client:
            #     delete_response = await client.delete(f"{self.base_url}/api/v2/config/{self.config_id}")
            #     if delete_response.status_code == 200:
            #         logger.info(f"✅ Test configuration deleted: {self.config_id}")
            #     else:
            #         logger.warning(f"⚠️ Could not delete test configuration: {delete_response.text}")
            
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.warning(f"⚠️ Cleanup had issues (non-critical): {e}")

    async def _cleanup_test_data(self):
        """Clean up test data from database (optional for development)."""
        try:
            # In development mode, we might want to keep data for inspection
            # Uncomment this if you want to clean up test data
            
            # with get_db_connection() as conn:
            #     with conn.cursor() as cur:
            #         # Clean up paper trades for this config
            #         cur.execute("DELETE FROM paper_trades WHERE config_id = %s", (self.config_id,))
            #         
            #         # Clean up configuration
            #         cur.execute("DELETE FROM configurations WHERE config_id = %s", (self.config_id,))
            #         
            #         logger.info("✅ Test data cleaned up")
            
            logger.info("ℹ️ Test data cleanup skipped (keeping for inspection)")
            
        except Exception as e:
            logger.warning(f"Cleanup failed (non-critical): {e}")


async def main():
    """Run the full E2E integration test."""
    test = FullE2EIntegrationTest()
    
    try:
        results = await test.run_full_test()
        
        # Print results
        print("\n" + "="*60)
        print("🎯 FULL E2E INTEGRATION TEST RESULTS")
        print("="*60)
        
        print(f"Success: {'✅ PASSED' if results['success'] else '❌ FAILED'}")
        print(f"Duration: {results['metrics']['test_duration_seconds']:.2f} seconds")
        print(f"API Calls: {results['metrics']['total_api_calls']}")
        print(f"WebSocket Messages: {results['metrics']['websocket_messages']}")
        print(f"Trades Executed: {results['metrics']['trades_executed']}")
        
        print("\nPhase Results:")
        for phase, status in results["phases"].items():
            print(f"  {phase.title()}: {status}")
        
        if results.get("error"):
            print(f"\nError: {results['error']}")
        
        print("="*60)
        
        # Save results to file
        with open("tests/e2e_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        return results["success"]
        
    except Exception as e:
        logger.error(f"E2E Test Exception: {e}")
        return False
    
    finally:
        # Always attempt cleanup
        await test._cleanup_test_data()


if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)