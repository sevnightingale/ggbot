"""
Universal Active Bot Monitoring Service

Monitors only config_instances with status='active' and broadcasts 
real-time status updates via WebSocket. Uses existing database 
infrastructure with no schema changes required.

Key Features:
- Only monitors active bots (no background processes for inactive)
- ggShot-Pro (e249bb49-...) is always active and monitored
- Demo bots are monitored only when user activates them
- Universal architecture supports any bot type via bot handlers
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
from core.common.logger import logger


class ActiveBotMonitor:
    """
    Universal monitoring service for all active ggbots.
    
    Polls config_instances table for active bots and monitors their
    pipeline activity using bot-type specific handlers.
    """
    
    def __init__(self):
        """Initialize the active bot monitor."""
        self.active_bots: Dict[str, Dict] = {}  # config_id -> bot_info
        self.bot_handlers: Dict[str, Any] = {}  # config_id -> bot_handler
        self.websocket_manager = None  # Will be injected later
        self.running = False
        
        # Bot type factory - maps config_type to handler class
        self.bot_type_handlers = {}
        
        logger.bind(module="active_bot_monitor").info(
            "Initialized Universal Active Bot Monitor"
        )
    
    def _get_db_connection(self):
        """Get a database connection."""
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
    
    def register_bot_handler(self, bot_type: str, handler_class):
        """Register a bot type handler class."""
        self.bot_type_handlers[bot_type] = handler_class
        logger.bind(module="active_bot_monitor").info(
            f"Registered bot handler for type: {bot_type}"
        )
    
    def set_websocket_manager(self, manager):
        """Inject WebSocket manager for broadcasting."""
        self.websocket_manager = manager
    
    async def get_active_bot_configs(self) -> List[Dict[str, Any]]:
        """
        Get all active bot configurations from config_instances table.
        
        Returns:
            List[Dict]: Active bot configurations with all needed data
        """
        try:
            conn = self._get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            ci.config_id,
                            ci.instance_name,
                            ci.status,
                            ci.hummingbot_account,
                            ci.paper_balance_usd,
                            c.config_name,
                            c.config_type,
                            c.config_data,
                            c.user_id
                        FROM config_instances ci
                        JOIN configurations c ON ci.config_id = c.config_id
                        WHERE ci.status = 'active'
                        ORDER BY c.config_type, ci.config_id
                    """)
                    
                    results = cur.fetchall()
                    
                    # Convert RealDictRow to regular dict for easier handling
                    active_configs = []
                    for row in results:
                        config = dict(row)
                        # Parse config_data JSON
                        if config['config_data']:
                            try:
                                config['config_data'] = json.loads(config['config_data']) \
                                    if isinstance(config['config_data'], str) \
                                    else config['config_data']
                            except json.JSONDecodeError:
                                logger.warning(
                                    f"Failed to parse config_data for {config['config_id']}"
                                )
                                config['config_data'] = {}
                        
                        active_configs.append(config)
                    
                    logger.bind(module="active_bot_monitor").debug(
                        f"Found {len(active_configs)} active bot configurations"
                    )
                    
                    return active_configs
                    
            finally:
                conn.close()
                
        except Exception as e:
            logger.bind(module="active_bot_monitor").error(
                f"Failed to get active bot configs: {str(e)}"
            )
            return []
    
    def create_bot_handler(self, bot_config: Dict[str, Any]):
        """
        Create appropriate bot handler based on config_type.
        
        Args:
            bot_config: Bot configuration dictionary
            
        Returns:
            Bot handler instance or None if type not supported
        """
        bot_type = bot_config['config_type']
        config_id = bot_config['config_id']
        
        if bot_type in self.bot_type_handlers:
            handler_class = self.bot_type_handlers[bot_type]
            return handler_class(bot_config)
        else:
            logger.bind(module="active_bot_monitor").warning(
                f"No handler registered for bot type: {bot_type} (config: {config_id})"
            )
            return None
    
    def generate_bot_id(self, config_id: str, bot_type: str) -> str:
        """
        Generate consistent bot_id for WebSocket broadcasting.
        
        Format: {bot_type}-{config_id[:8]}
        Examples: "ggshot-e249bb49", "demo-a1b2c3d4"
        """
        return f"{bot_type}-{config_id[:8]}"
    
    async def monitor_single_bot(self, bot_config: Dict[str, Any]):
        """
        Monitor a single active bot configuration.
        
        Args:
            bot_config: Bot configuration dictionary
        """
        try:
            config_id = str(bot_config['config_id'])
            bot_type = str(bot_config['config_type'])
            user_id = str(bot_config['user_id'])
            bot_name = bot_config.get('config_name') or f"Bot {config_id[:8]}"
            
            # Create or get bot handler
            if config_id not in self.bot_handlers:
                handler = self.create_bot_handler(bot_config)
                if handler:
                    self.bot_handlers[config_id] = handler
                else:
                    # Skip bots without handlers
                    return
            
            handler = self.bot_handlers[config_id]
            
            # Detect current pipeline phase
            current_phase = await handler.detect_pipeline_phase()
            sub_phase = await handler.detect_sub_phase(current_phase)
            
            # Extract contextual data for dynamic messages
            context_data = await handler.extract_context_data()
            
            # Generate status message
            status_message = await handler.generate_status_message(
                phase=current_phase,
                sub_phase=sub_phase,
                context=context_data
            )
            
            # Create bot_id for WebSocket
            bot_id = self.generate_bot_id(config_id, bot_type)
            
            # Create status update message
            status_update = {
                "type": "bot_status_update",
                "bot_id": bot_id,
                "bot_type": bot_type,
                "config_id": config_id,
                "bot_name": bot_name,
                "user_id": user_id,
                "status": {
                    "phase": current_phase,
                    "sub_phase": sub_phase,
                    "color": self.get_phase_color(current_phase),
                    "message": status_message,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "showSpinner": current_phase in ["extraction", "decision", "trading"],
                    "context": context_data
                }
            }
            
            # Broadcast to the bot's user
            if self.websocket_manager:
                # Send to the specific user who owns this bot
                if hasattr(self.websocket_manager, 'active_connections'):
                    if user_id in self.websocket_manager.active_connections:
                        await self.websocket_manager.broadcast_to_user(user_id, status_update)
                    
                    # Also broadcast to all connected users for demo purposes
                    for connected_user_id in self.websocket_manager.active_connections:
                        await self.websocket_manager.broadcast_to_user(connected_user_id, status_update)
            
            logger.bind(module="active_bot_monitor").debug(
                f"Bot {bot_id}: {current_phase} - {status_message}"
            )
            
        except Exception as e:
            logger.bind(module="active_bot_monitor").error(
                f"Error monitoring bot {config_id}: {str(e)}"
            )
    
    def get_phase_color(self, phase: str) -> str:
        """
        Get color coding for pipeline phases.
        
        Returns:
            str: Color name for frontend styling
        """
        color_map = {
            "idle": "gray",
            "extraction": "blue", 
            "decision": "green",
            "trading": "orange"
        }
        return color_map.get(phase, "gray")
    
    async def broadcast_bot_status(self, bot_id: str, status_data: Dict[str, Any]):
        """
        Broadcast bot status to WebSocket subscribers.
        
        Args:
            bot_id: Bot identifier for channel routing
            status_data: Complete status message data
        """
        if self.websocket_manager:
            try:
                # Extract the user_id from the bot config to send to the right user
                user_id = status_data.get("status", {}).get("context", {}).get("user_id")
                
                if not user_id and "config_id" in status_data:
                    # If user_id not in context, get it from the config
                    config_id = status_data["config_id"]
                    # Find the user_id from our bot handlers or active configs
                    # For now, broadcast to all connected users
                    for connected_user_id in self.websocket_manager.active_connections:
                        await self.websocket_manager.broadcast_to_user(connected_user_id, status_data)
                else:
                    # Send to specific user
                    await self.websocket_manager.broadcast_to_user(str(user_id), status_data)
                
            except Exception as e:
                logger.bind(module="active_bot_monitor").error(
                    f"Failed to broadcast status for {bot_id}: {str(e)}"
                )
    
    async def monitor_active_bots(self):
        """
        Main monitoring loop - monitors all active bots continuously.
        
        Runs every 10 seconds and checks pipeline status for each active bot.
        """
        logger.bind(module="active_bot_monitor").info(
            "🚀 Starting universal bot monitoring loop"
        )
        
        while self.running:
            try:
                # Get current active bots
                active_configs = await self.get_active_bot_configs()
                
                if not active_configs:
                    logger.bind(module="active_bot_monitor").debug(
                        "No active bots found - waiting for activation"
                    )
                else:
                    logger.bind(module="active_bot_monitor").debug(
                        f"Monitoring {len(active_configs)} active bots"
                    )
                    
                    # Monitor each active bot
                    monitoring_tasks = []
                    for bot_config in active_configs:
                        task = self.monitor_single_bot(bot_config)
                        monitoring_tasks.append(task)
                    
                    # Run all monitoring tasks concurrently
                    if monitoring_tasks:
                        await asyncio.gather(*monitoring_tasks, return_exceptions=True)
                
                # Cleanup handlers for inactive bots
                await self.cleanup_inactive_handlers(active_configs)
                
                # Wait before next poll
                await asyncio.sleep(10)  # Monitor every 10 seconds
                
            except Exception as e:
                logger.bind(module="active_bot_monitor").error(
                    f"Error in monitoring loop: {str(e)}"
                )
                await asyncio.sleep(30)  # Longer wait on error
    
    async def cleanup_inactive_handlers(self, active_configs: List[Dict[str, Any]]):
        """
        Remove handlers for bots that are no longer active.
        
        Args:
            active_configs: List of currently active bot configurations
        """
        active_config_ids = {config['config_id'] for config in active_configs}
        
        # Remove handlers for inactive bots
        inactive_handlers = []
        for config_id in self.bot_handlers:
            if config_id not in active_config_ids:
                inactive_handlers.append(config_id)
        
        for config_id in inactive_handlers:
            del self.bot_handlers[config_id]
            logger.bind(module="active_bot_monitor").debug(
                f"Removed handler for inactive bot: {config_id[:8]}"
            )
    
    async def start_monitoring(self):
        """Start the monitoring service."""
        if self.running:
            logger.bind(module="active_bot_monitor").warning(
                "Monitoring service is already running"
            )
            return
        
        self.running = True
        logger.bind(module="active_bot_monitor").info(
            "Starting Universal Active Bot Monitor"
        )
        
        # Start monitoring loop
        await self.monitor_active_bots()
    
    async def stop_monitoring(self):
        """Stop the monitoring service."""
        logger.bind(module="active_bot_monitor").info(
            "Stopping Universal Active Bot Monitor"
        )
        
        self.running = False
        
        # Cleanup all handlers
        self.bot_handlers.clear()
        
        logger.bind(module="active_bot_monitor").info(
            "Universal Active Bot Monitor stopped"
        )


# Global instance for easy access
active_bot_monitor = ActiveBotMonitor()


# Convenience functions
async def start_bot_monitoring():
    """Start the global bot monitoring service."""
    await active_bot_monitor.start_monitoring()


async def stop_bot_monitoring():
    """Stop the global bot monitoring service."""
    await active_bot_monitor.stop_monitoring()


def register_bot_handler(bot_type: str, handler_class):
    """Register a bot type handler."""
    active_bot_monitor.register_bot_handler(bot_type, handler_class)


def set_websocket_manager(manager):
    """Set the WebSocket manager for broadcasting."""
    active_bot_monitor.set_websocket_manager(manager)