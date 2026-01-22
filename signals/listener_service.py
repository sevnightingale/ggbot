#!/usr/bin/env python3
"""
Generic Signal Listener Service

A PM2-managed service that maintains persistent connections to signal sources
and routes signals to appropriate user configurations for validation.

Supports pluggable signal sources with ggShot as the first implementation.
"""

import asyncio
import aiohttp
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable, Any, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass

# Add project root to path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from core.common.logger import logger
from core.common.db import get_db_connection


@dataclass
class SignalData:
    """Standardized signal data structure."""
    source: str              # 'ggshot', 'tradingview', etc.
    symbol: str             # 'BTC/USDT'
    direction: str          # 'LONG', 'SHORT'
    timeframe: str          # '1h', '4h', etc.
    confidence: float       # Source's confidence (0.0-1.0)
    entry_zone: Dict        # {'low': float, 'high': float, 'mid': float}
    stop_loss: float        # Stop loss price
    take_profit: float      # Primary take profit
    reasoning: str          # Signal reasoning/analysis
    raw_message: str        # Original signal text
    metadata: Dict          # Source-specific data
    timestamp: datetime     # Signal generation time


class SignalSource(ABC):
    """Abstract base class for signal sources."""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.logger = logger.bind(signal_source=source_name)
        self.is_running = False
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the signal source. Returns True if successful."""
        pass
    
    @abstractmethod
    async def listen(self, signal_handler: Callable[[SignalData], None]) -> None:
        """Start listening for signals and call handler for each signal."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Clean shutdown of the signal source."""
        pass


class GGShotSignalSource(SignalSource):
    """ggShot Telegram signal source implementation."""

    def __init__(self):
        super().__init__('ggshot')
        self.api_id = int(os.getenv('TG_API_ID'))
        self.api_hash = os.getenv('TG_API_HASH')
        self.channel_name = os.getenv('GGSHOT_CHANNEL', 'GGShot_Bot')
        self.client: Optional[any] = None

        # Import ggShot parser
        from signals.ggshot_parser import GGShotParser
        self.parser = GGShotParser()

        # Database storage setup
        self._system_user_id = None
        self._signals_source_id = None

    def _get_system_user_id(self) -> str:
        """Get system user ID for storing universal signals."""
        if self._system_user_id:
            return self._system_user_id

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Try to find system user
                cur.execute("""
                    SELECT user_id FROM user_profiles
                    WHERE user_id IN (
                        SELECT id FROM auth.users WHERE email = 'system@ggbots.ai'
                    )
                    LIMIT 1
                """)
                result = cur.fetchone()
                if result:
                    self._system_user_id = str(result[0])
                    return self._system_user_id

                # Fallback: use first user
                cur.execute("""
                    SELECT user_id FROM user_profiles
                    ORDER BY created_at ASC
                    LIMIT 1
                """)
                result = cur.fetchone()
                if result:
                    self._system_user_id = str(result[0])
                    self.logger.warning(f"Using first user as system user for signals: {self._system_user_id}")
                    return self._system_user_id

                raise ValueError("No users found in database - cannot store signals")

    def _get_signals_source_id(self) -> str:
        """Get UUID of 'trading_signals' data source."""
        if self._signals_source_id:
            return self._signals_source_id

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT source_id FROM data_sources
                    WHERE name = 'trading_signals'
                """)
                result = cur.fetchone()
                if not result:
                    raise ValueError("trading_signals data source not found in database")
                self._signals_source_id = str(result[0])
                return self._signals_source_id

    def _store_signal_in_db(self, signal_data: Dict[str, Any], message_date: datetime) -> bool:
        """Store parsed signal in market_data table."""
        try:
            # Get IDs (cached after first call)
            system_user_id = self._get_system_user_id()
            signals_source_id = self._get_signals_source_id()

            # Build data_points JSONB
            data_points = {
                "ggshot_signal": {
                    "direction": signal_data['direction'],
                    "entry_zone": signal_data['entry_zone'],
                    "stop_loss": signal_data['stop_loss'],
                    "take_profit": signal_data['target_1'],
                    "targets": signal_data['targets'],
                    "confidence": signal_data.get('strategy_accuracy', 0) / 100.0 if signal_data.get('strategy_accuracy') else None,
                    "strategy_accuracy": signal_data.get('strategy_accuracy'),
                    "trend_line": signal_data.get('trend_line')
                }
            }

            # Build raw_data JSONB
            raw_data = {
                "telegram_message": signal_data.get('raw_message', ''),
                "parsed_at": signal_data.get('parsed_at'),
                "source": "telegram",
                "message_date": message_date.isoformat()
            }

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO market_data (
                            user_id, symbol, timeframe, config_id, data_source,
                            data_points, raw_data, updated_at
                        ) VALUES (
                            %s, %s, %s, NULL, %s, %s, %s, %s
                        )
                    """, (
                        system_user_id,
                        signal_data['symbol'],
                        signal_data['timeframe'],
                        signals_source_id,
                        json.dumps(data_points),
                        json.dumps(raw_data),
                        message_date
                    ))
                    conn.commit()
                    return True

        except Exception as e:
            self.logger.error(f"Error storing signal in database: {e}")
            return False

    async def initialize(self) -> bool:
        """Initialize Telegram client and test connection."""
        try:
            from telethon import TelegramClient
            
            if not self.api_id or not self.api_hash:
                self.logger.error("Missing TG_API_ID or TG_API_HASH environment variables")
                return False
            
            # Create session in project directory
            session_dir = os.path.join(PROJECT_DIR, 'sessions')
            os.makedirs(session_dir, exist_ok=True)
            session_path = os.path.join(session_dir, 'ggshot_session')
            
            self.client = TelegramClient(session_path, self.api_id, self.api_hash)
            await self.client.start()
            
            # Test channel access
            channel = await self.client.get_entity(self.channel_name)
            entity_name = getattr(channel, 'title', None) or getattr(channel, 'username', None) or str(channel.id)
            
            self.logger.info(f"Successfully connected to {entity_name} (ID: {channel.id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ggShot signal source: {e}")
            return False
    
    async def listen(self, signal_handler: Callable[[SignalData], None]) -> None:
        """Listen for ggShot signals from Telegram."""
        try:
            from telethon.events import NewMessage
            
            channel = await self.client.get_entity(self.channel_name)
            self.is_running = True
            
            @self.client.on(NewMessage(chats=channel))
            async def handle_message(event):
                try:
                    await self._process_message(event.message, signal_handler)
                except Exception as e:
                    self.logger.error(f"Error processing ggShot message: {e}")
            
            self.logger.info(f"Started listening for ggShot signals from {self.channel_name}")
            
            # Keep running until shutdown
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"ggShot listener error: {e}")
            raise
    
    async def _process_message(self, message, signal_handler: Callable[[SignalData], None]) -> None:
        """Process incoming Telegram message."""
        message_text = message.message if hasattr(message, 'message') else message
        if not message_text:
            return

        # Parse using existing ggShot parser
        signal_data = self.parser.parse_signal(message_text)

        if not signal_data:
            self.logger.debug("Message is not a valid ggShot signal")
            return

        # Store signal in database for autonomous trading use
        message_date = message.date if hasattr(message, 'date') else datetime.now(timezone.utc)
        stored = self._store_signal_in_db(signal_data, message_date)
        if stored:
            self.logger.info(f"Stored signal in DB: {signal_data['symbol']} {signal_data['direction']} ({signal_data['timeframe']})")

        # Convert to standardized SignalData format
        standardized_signal = SignalData(
            source='ggshot',
            symbol=signal_data['symbol'],
            direction=signal_data['direction'],
            timeframe=signal_data['timeframe'],
            confidence=signal_data.get('strategy_accuracy', 80) / 100.0,  # Convert to 0.0-1.0
            entry_zone=signal_data['entry_zone'],
            stop_loss=signal_data['stop_loss'],
            take_profit=signal_data['target_1'],  # Use first target
            reasoning=f"ggShot signal with {signal_data.get('strategy_accuracy', 80)}% accuracy",
            raw_message=message_text,
            metadata={
                'targets': signal_data['targets'],
                'trend_line': signal_data.get('trend_line'),
                'strategy_accuracy': signal_data.get('strategy_accuracy')
            },
            timestamp=datetime.now(timezone.utc)
        )

        self.logger.info(f"Parsed ggShot signal: {standardized_signal.symbol} {standardized_signal.direction}")

        # Call the signal handler (for signal validation routing)
        await signal_handler(standardized_signal)
    
    async def shutdown(self) -> None:
        """Shutdown ggShot signal source."""
        self.is_running = False
        if self.client:
            await self.client.disconnect()
        self.logger.info("ggShot signal source shutdown complete")


class OrchestratorClient:
    """Client for communicating with the main ggbot orchestrator."""
    
    def __init__(self):
        self.api_base = os.getenv('GGBOT_API_URL', 'http://localhost:8000')
        self.logger = logger.bind(component='orchestrator_client')
    
    async def trigger_signal_validation(
        self,
        config_id: str,
        user_id: str,
        signal_data: SignalData
    ) -> bool:
        """Trigger signal validation in the main orchestrator."""
        try:
            payload = {
                'signal_data': {
                    'source': signal_data.source,
                    'symbol': signal_data.symbol,
                    'direction': signal_data.direction,
                    'timeframe': signal_data.timeframe,
                    'confidence': signal_data.confidence,
                    'entry_zone': signal_data.entry_zone,
                    'stop_loss': signal_data.stop_loss,
                    'take_profit': signal_data.take_profit,
                    'reasoning': signal_data.reasoning,
                    'raw_message': signal_data.raw_message,
                    'metadata': signal_data.metadata,
                    'timestamp': signal_data.timestamp.isoformat()
                },
                'override_symbol': signal_data.symbol
            }

            # Use dedicated signal validation endpoint with service authentication
            url = f"{self.api_base}/api/v2/signal-validation/{config_id}"

            # Get service authentication key
            service_key = os.getenv('SUPABASE_SERVICE_KEY')
            if not service_key:
                self.logger.error("SUPABASE_SERVICE_KEY not found in environment")
                return False

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {service_key}',
                'X-Service-Auth': 'signal-listener'
            }

            params = {'user_id': user_id}  # Pass user_id as query parameter

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, params=params, timeout=60) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.logger.info(f"Signal validation triggered successfully for config {config_id}")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Signal validation failed: {response.status} - {error_text}")
                        return False

        except Exception as e:
            self.logger.error(f"Failed to trigger signal validation: {e}")
            return False


class SignalListenerService:
    """Main service that coordinates all signal sources."""
    
    def __init__(self):
        self.signal_sources = {
            'ggshot': GGShotSignalSource()
        }
        self.orchestrator_client = OrchestratorClient()
        self.logger = logger.bind(service='signal_listener')
        self.running = False
        
    async def start(self):
        """Start the signal listener service."""
        self.logger.info("🚀 Starting Signal Listener Service")
        
        try:
            # Initialize all enabled signal sources
            enabled_sources = []
            for source_name, source in self.signal_sources.items():
                if await self._is_source_enabled(source_name):
                    if await source.initialize():
                        enabled_sources.append((source_name, source))
                        self.logger.info(f"✅ {source_name} signal source initialized")
                    else:
                        self.logger.error(f"❌ Failed to initialize {source_name} signal source")
                else:
                    self.logger.info(f"⏭️ {source_name} signal source disabled")
            
            if not enabled_sources:
                self.logger.error("No signal sources enabled. Service will exit.")
                return
            
            self.running = True
            
            # Start listening tasks for all enabled sources
            tasks = []
            for source_name, source in enabled_sources:
                task = asyncio.create_task(
                    source.listen(self._handle_signal),
                    name=f"{source_name}_listener"
                )
                tasks.append(task)
            
            self.logger.info(f"🎧 Listening on {len(tasks)} signal sources")
            
            # Run until all tasks complete or service is stopped
            try:
                await asyncio.gather(*tasks)
            except asyncio.CancelledError:
                self.logger.info("Signal listener tasks cancelled")
                
        except Exception as e:
            self.logger.error(f"Signal listener service error: {e}")
            raise
        finally:
            await self._shutdown()
    
    async def _is_source_enabled(self, source_name: str) -> bool:
        """Check if a signal source is enabled via configuration."""
        try:
            # For now, only ggShot is enabled if environment variables are present
            if source_name == 'ggshot':
                return bool(os.getenv('TG_API_ID') and os.getenv('TG_API_HASH'))
            
            # Future sources can check their own configuration
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking if {source_name} is enabled: {e}")
            return False
    
    async def _handle_signal(self, signal_data: SignalData) -> None:
        """Handle incoming signal from any source."""
        try:
            self.logger.info(f"📡 Received {signal_data.source} signal: {signal_data.symbol} {signal_data.direction}")

            # Find user configurations that want this signal type (filtered by symbol compatibility)
            target_configs = await self._get_signal_subscribers(signal_data.source, signal_data.symbol)

            if not target_configs:
                self.logger.info(f"No subscribers found for {signal_data.source} signals with symbol {signal_data.symbol}")
                return

            self.logger.info(f"🎯 Routing signal to {len(target_configs)} user configurations")
            
            # Trigger signal validation for each interested configuration
            success_count = 0
            for config_id, user_id in target_configs:
                success = await self.orchestrator_client.trigger_signal_validation(
                    config_id=config_id,
                    user_id=user_id,
                    signal_data=signal_data
                )
                if success:
                    success_count += 1
                else:
                    self.logger.warning(f"Failed to trigger validation for config {config_id}")
            
            self.logger.info(f"✅ Signal routed successfully to {success_count}/{len(target_configs)} configurations")
            
        except Exception as e:
            self.logger.error(f"Error handling signal: {e}")
            traceback.print_exc()
    
    async def _get_signal_subscribers(self, signal_source: str, signal_symbol: str) -> List[Tuple[str, str]]:
        """
        Find user configurations that want signals from this source.

        Filters by symbol compatibility based on trading mode:
        - Symphony bots: Only receive symphony-compatible symbols
        - Paper bots: Receive all symbols
        - AsterDEX bots: Only receive aster-compatible symbols
        """
        try:
            # Import standardizer for symbol compatibility checks
            from core.symbols import UniversalSymbolStandardizer
            standardizer = UniversalSymbolStandardizer()

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Query for users with signal_validation configs wanting this signal source
                    # Now include trading_mode to filter by symbol compatibility
                    cur.execute("""
                        SELECT DISTINCT c.config_id, c.user_id, c.config_data, c.trading_mode
                        FROM configurations c
                        JOIN user_profiles up ON c.user_id = up.user_id
                        WHERE c.config_type = 'signal_validation'
                          AND c.state = 'active'
                          AND (
                            c.config_data->'extraction'->'selected_data_sources' ? 'trading_signals'
                            OR c.config_data->'config_data'->'extraction'->'selected_data_sources' ? 'trading_signals'
                          )
                          AND %s = ANY(up.paid_data_points)
                          AND up.subscription_tier = 'prepaid'
                          AND up.subscription_status = 'active'
                    """, (signal_source,))

                    results = cur.fetchall()
                    self.logger.info(f"🔍 Found {len(results)} active signal_validation configs for signal_source '{signal_source}'")

                    # Filter results by signal source subscription AND symbol compatibility
                    subscribers = []
                    for row in results:
                        config_id, user_id, config_data, trading_mode = row[0], row[1], row[2], row[3]

                        # Handle nested config_data structure (same as publishing service)
                        if "config_data" in config_data:
                            inner_config = config_data["config_data"]
                            extraction_config = inner_config.get('extraction', {}).get('selected_data_sources', {})
                        else:
                            extraction_config = config_data.get('extraction', {}).get('selected_data_sources', {})

                        signals_config = extraction_config.get('trading_signals', {})
                        data_points = signals_config.get('data_points', [])

                        # Check if this signal source is in the data points (e.g., "ggshot")
                        if signal_source not in data_points:
                            self.logger.debug(f"Config {config_id} does not subscribe to {signal_source}")
                            continue

                        # Check symbol compatibility based on trading mode
                        if trading_mode == 'symphony':
                            # Symphony bots only get symphony-compatible symbols
                            is_compatible = standardizer.is_symphony_compatible(signal_symbol, "ccxt")
                            if not is_compatible:
                                self.logger.info(
                                    f"🚫 Skipping Symphony bot {config_id}: {signal_symbol} not Symphony-compatible"
                                )
                                continue
                        elif trading_mode == 'aster':
                            # AsterDEX bots only get aster-compatible symbols
                            is_compatible = standardizer.is_aster_compatible(signal_symbol, "ccxt")
                            if not is_compatible:
                                self.logger.info(
                                    f"🚫 Skipping AsterDEX bot {config_id}: {signal_symbol} not AsterDEX-compatible"
                                )
                                continue
                        # Paper mode: accepts all symbols (no filtering)

                        subscribers.append((config_id, user_id))
                        self.logger.info(
                            f"✅ Config {config_id} subscribed to {signal_source} signals "
                            f"(mode: {trading_mode}, symbol: {signal_symbol})"
                        )

                    self.logger.info(
                        f"📊 Filtered to {len(subscribers)} compatible subscribers for {signal_symbol} "
                        f"(out of {len(results)} total configs)"
                    )

                    return subscribers
                    
        except Exception as e:
            self.logger.error(f"Failed to get signal subscribers: {e}")
            return []
    
    async def _shutdown(self):
        """Shutdown all signal sources."""
        self.running = False
        self.logger.info("🔄 Shutting down signal sources...")
        
        for source_name, source in self.signal_sources.items():
            try:
                await source.shutdown()
                self.logger.info(f"✅ {source_name} source shutdown complete")
            except Exception as e:
                self.logger.error(f"Error shutting down {source_name}: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check endpoint for monitoring."""
        return {
            'status': 'healthy' if self.running else 'stopped',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'sources': {
                name: {
                    'enabled': await self._is_source_enabled(name),
                    'running': source.is_running if hasattr(source, 'is_running') else False
                }
                for name, source in self.signal_sources.items()
            }
        }


async def main():
    """Main entry point for the signal listener service."""
    service = SignalListenerService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        traceback.print_exc()
    finally:
        logger.info("🔄 Signal Listener Service shutdown complete")


if __name__ == "__main__":
    # Set up logging for the service
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the service
    asyncio.run(main())