"""
Hummingbot Execution Adapter with LLM Normalization

Bridges ggBot's trade execution logic with Hummingbot's API, using LLM to handle
the "translation" of various trade intent formats into standardized Hummingbot calls.
"""

import os
import json
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timezone

from decision.llm_providers.factory import get_llm_provider
from core.common.logger import logger
from .market_data_service import MarketDataService

from hummingbot_api_client import Client
from hummingbot_api_client.api.trading import place_trade_trading_orders_post
from hummingbot_api_client.models import TradeRequest, TradeRequestTradeType, TradeRequestOrderType


@dataclass
class TradeIntent:
    """Standardized trade intent structure."""
    symbol: str           # "BTCUSDT"
    direction: str        # "long" | "short"
    entry_price: Decimal  # Single price or midpoint of range
    quantity: Decimal     # Position size
    stop_loss: Optional[Decimal]
    take_profit: List[Decimal]  # Multiple targets supported
    order_type: str       # "market" | "limit"
    confidence: float     # 0.0-1.0
    reasoning: str        # LLM explanation


class HummingbotExecutionAdapter:
    """
    LLM-powered adapter for converting trade intents to Hummingbot API calls.
    
    Handles:
    - ggShot signal normalization via LLM
    - Symbol format conversion
    - Position sizing from confidence
    - Hummingbot API execution
    """
    
    def __init__(self, api_url: str = "http://localhost:8088", 
                 username: str = "admin", password: str = "admin",
                 connector: str = "binance_perpetual_testnet"):
        """Initialize adapter with LLM and Hummingbot clients."""
        
        # Initialize LLM provider using existing infrastructure
        api_key = os.environ.get("TRADING_LLM_API_KEY")
        if not api_key:
            raise ValueError("TRADING_LLM_API_KEY not found in environment")
        
        self.llm = get_llm_provider(
            provider_name="deepseek",
            api_key=api_key,
            model="deepseek-reasoner"  # Better accuracy for complex normalization
        )
        
        # Initialize market data service
        self.market_data = MarketDataService(api_url, username, password, connector)
        
        # Initialize Hummingbot client
        import base64
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        self.hummingbot_client = Client(
            base_url=api_url,
            headers={"Authorization": f"Basic {encoded_credentials}"}
        )
        
        self.connector = connector
        
        logger.bind(service="hummingbot_adapter").info(
            f"HummingbotExecutionAdapter initialized with {connector}"
        )
    
    async def execute_signal(self, raw_signal: Dict[str, Any], 
                           user_id: str, config_id: str) -> Dict[str, Any]:
        """
        Execute a trading signal through the complete pipeline.
        
        Args:
            raw_signal: Raw signal data (ggShot format, API call, etc.)
            user_id: User identifier
            config_id: Configuration identifier
            
        Returns:
            Dict with execution result and trade details
        """
        try:
            # Step 1: Normalize intent via LLM
            logger.bind(service="hummingbot_adapter").info(
                f"Normalizing signal for user {user_id}, config {config_id}"
            )
            
            normalized_intent = await self._llm_normalize_intent(raw_signal)
            
            # Step 2: Validate and convert symbol
            trading_pair = self.market_data._format_trading_pair(normalized_intent.symbol)
            
            # Step 3: Calculate position size from confidence
            position_size = self._calculate_position_size(
                normalized_intent.confidence,
                normalized_intent.entry_price
            )
            
            # Step 4: Execute trade via Hummingbot API
            trade_result = await self._execute_hummingbot_trade(
                normalized_intent, trading_pair, position_size, user_id, config_id
            )
            
            logger.bind(service="hummingbot_adapter").info(
                f"Trade executed successfully: {trade_result.get('order_id', 'N/A')}"
            )
            
            return {
                "status": "success",
                "trade_intent": normalized_intent.__dict__,
                "execution_result": trade_result,
                "user_id": user_id,
                "config_id": config_id
            }
            
        except Exception as e:
            logger.error(f"Signal execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "user_id": user_id,
                "config_id": config_id
            }
    
    async def _llm_normalize_intent(self, raw_signal: Dict[str, Any]) -> TradeIntent:
        """Use LLM to normalize various signal formats into TradeIntent."""
        
        prompt = self._build_normalization_prompt(raw_signal)
        
        try:
            response, metadata = await self.llm.generate_response(
                prompt=prompt,
                temperature=0.1,  # Low temperature for consistent parsing
                custom_mode="signal_normalization"
            )
            
            # Parse LLM response
            normalized_data = self._parse_llm_response(response)
            
            # Convert to TradeIntent
            intent = TradeIntent(
                symbol=normalized_data["symbol"],
                direction=normalized_data["direction"],
                entry_price=Decimal(str(normalized_data["entry_price"])),
                quantity=Decimal("0"),  # Will be calculated later
                stop_loss=Decimal(str(normalized_data["stop_loss"])) if normalized_data.get("stop_loss") else None,
                take_profit=[Decimal(str(tp)) for tp in normalized_data.get("take_profit", [])],
                order_type=normalized_data.get("order_type", "market"),
                confidence=float(normalized_data["confidence"]),
                reasoning=normalized_data.get("reasoning", "")
            )
            
            logger.bind(service="hummingbot_adapter").info(
                f"LLM normalized signal: {intent.symbol} {intent.direction} @ {intent.entry_price}"
            )
            
            return intent
            
        except Exception as e:
            logger.error(f"LLM normalization failed: {e}")
            raise ValueError(f"Failed to normalize signal: {e}")
    
    def _build_normalization_prompt(self, raw_signal: Dict[str, Any]) -> str:
        """Build LLM prompt for signal normalization."""
        
        return f"""You are a trading signal normalizer. Convert the following raw trading signal into a standardized format.

INPUT SIGNAL:
{json.dumps(raw_signal, indent=2)}

Your task is to extract and normalize the following information:

REQUIRED OUTPUT (JSON format only):
{{
  "symbol": "BTCUSDT",           // Standard format (base + quote currency)
  "direction": "long|short",     // Trade direction
  "entry_price": 105000.0,       // Single entry price (use midpoint for ranges)
  "stop_loss": 102000.0,         // Stop loss price (calculate 2-3% if missing)
  "take_profit": [108000.0, 110000.0],  // Array of target prices
  "order_type": "market|limit",  // Order type
  "confidence": 0.85,            // Signal confidence 0.0-1.0
  "reasoning": "Used midpoint of entry zone 104289.7-106904.8..."
}}

NORMALIZATION RULES:
1. **Symbol Format**: Convert any format to standard (e.g., "solana" → "SOLUSDT", "BTC/USDT" → "BTCUSDT")
2. **Entry Ranges**: Use midpoint (e.g., "104289.7-106904.8" → 105597.25)
3. **Missing Stop Loss**: Calculate reasonable 2-3% risk level from entry price
4. **Multiple Targets**: Convert to array format
5. **Confidence Assessment**: 
   - High accuracy signals with clear levels = 0.8-0.9
   - Medium clarity signals = 0.6-0.7
   - Low clarity or missing info = 0.4-0.5
6. **Direction**: "long"/"buy" = long, "short"/"sell" = short
7. **Order Type**: Default to "market" unless specific limit price given

REASONING: Explain your normalization decisions, especially for ranges, missing data, and confidence scoring.

OUTPUT (JSON only, no additional text):"""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate LLM response."""
        try:
            # Extract JSON from response (in case LLM adds extra text)
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
            else:
                parsed = json.loads(response)
            
            # Validate required fields
            required_fields = ["symbol", "direction", "entry_price", "confidence"]
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate direction
            if parsed["direction"].lower() not in ["long", "short"]:
                raise ValueError(f"Invalid direction: {parsed['direction']}")
            
            # Validate confidence range
            confidence = float(parsed["confidence"])
            if not 0.0 <= confidence <= 1.0:
                raise ValueError(f"Confidence must be 0.0-1.0, got: {confidence}")
            
            return parsed
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from LLM: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")
    
    def _calculate_position_size(self, confidence: float, entry_price: Decimal) -> Decimal:
        """Calculate position size based on confidence score."""
        
        # Base position sizing logic (can be made configurable)
        base_usd_amount = 1000  # $1000 base position
        
        # Confidence-based multiplier
        if confidence >= 0.8:
            multiplier = 2.0    # High confidence: $2000
        elif confidence >= 0.6:
            multiplier = 1.5    # Medium confidence: $1500
        elif confidence >= 0.4:
            multiplier = 1.0    # Low confidence: $1000
        else:
            multiplier = 0.5    # Very low confidence: $500
        
        usd_amount = base_usd_amount * multiplier
        
        # Convert USD amount to quantity
        quantity = Decimal(str(usd_amount)) / entry_price
        
        logger.bind(service="hummingbot_adapter").info(
            f"Position sizing: confidence={confidence}, usd_amount=${usd_amount}, quantity={quantity}"
        )
        
        return quantity
    
    async def _execute_hummingbot_trade(self, intent: TradeIntent, trading_pair: str, 
                                      quantity: Decimal, user_id: str, config_id: str) -> Dict[str, Any]:
        """Execute trade via Hummingbot API."""
        
        try:
            # Create trade request
            trade_request = TradeRequest(
                connector_name=self.connector,
                trading_pair=trading_pair,
                trade_type=TradeRequestTradeType.BUY if intent.direction == "long" else TradeRequestTradeType.SELL,
                order_type=TradeRequestOrderType.MARKET if intent.order_type == "market" else TradeRequestOrderType.LIMIT,
                amount=float(quantity),
                price=float(intent.entry_price) if intent.order_type == "limit" else None
            )
            
            # Execute trade
            response = await place_trade_trading_orders_post.asyncio_detailed(
                client=self.hummingbot_client,
                body=trade_request
            )
            
            if response.status_code == 201:
                # Parse successful response
                trade_data = json.loads(response.content.decode())
                
                return {
                    "order_id": trade_data.get("order_id"),
                    "status": "submitted",
                    "trading_pair": trading_pair,
                    "quantity": float(quantity),
                    "price": float(intent.entry_price),
                    "side": intent.direction,
                    "connector": self.connector
                }
            else:
                error_msg = response.content.decode()
                raise Exception(f"Hummingbot API error ({response.status_code}): {error_msg}")
                
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            raise


async def test_execution_adapter():
    """Test the HummingbotExecutionAdapter with sample signals."""
    
    adapter = HummingbotExecutionAdapter()
    
    # Test ggShot format signal
    ggshot_signal = {
        "message": "📩 #BTCUSDT 1h | Mid-Term\n📈 Short Entry Zone: 104289.7-106904.8\n🎯 Target 1: 102203.9\n🎯 Target 2: 100118.1\n❌Stop-Loss: 109042.9"
    }
    
    # Test structured signal
    structured_signal = {
        "symbol": "ETHUSDT",
        "action": "long",
        "entry_price": 3800,
        "stop_loss": 3700,
        "take_profit": 4000,
        "confidence": 0.75
    }
    
    print("\n=== Testing ggShot Signal ===")
    result1 = await adapter.execute_signal(ggshot_signal, "test_user", "test_config")
    print(json.dumps(result1, indent=2, default=str))
    
    print("\n=== Testing Structured Signal ===")
    result2 = await adapter.execute_signal(structured_signal, "test_user", "test_config")
    print(json.dumps(result2, indent=2, default=str))


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_execution_adapter())