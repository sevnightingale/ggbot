"""
Trading Agent Runner (Phase 3)

Main entry point for autonomous trading agent using Claude Agent SDK.

Architecture:
- Streaming mode with two async tasks (agent loop + user interrupts)
- Redis queue for user messages: agent:{config_id}:messages
- Redis queue for responses: agent:{config_id}:responses
- MCP tools for trading operations
- Auto-compaction at 95% token usage

Usage:
    python agent/run_agent.py --config-id=abc123 --mode=strategy_definition
    python agent/run_agent.py --config-id=abc123 --mode=autonomous
"""

import os
import sys
import argparse
import asyncio
import json
from typing import Optional, Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
import redis.asyncio as redis
from dotenv import load_dotenv

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock

from agent.mcp_server import create_mcp_server, set_agent_context
from agent.service_client import GGBotAPIClient
from core.common.db import get_db_connection

# Load environment
load_dotenv()


class TradingAgent:
    """
    Autonomous trading agent with two modes:
    - strategy_definition: Interactive strategy building with user
    - autonomous: 24/7 trading loop with self-directed timing
    """

    def __init__(self, config_id: str, user_id: str, mode: str):
        self.config_id = config_id
        self.user_id = user_id
        self.mode = mode
        self.redis_client: Optional[redis.Redis] = None
        self.api_client: Optional[GGBotAPIClient] = None
        self.config: Optional[Dict[str, Any]] = None

        logger.info(f"Initializing TradingAgent: config_id={config_id}, mode={mode}")

    async def initialize(self):
        """Load config and initialize clients"""
        # Load config from database
        self.config = await self._load_config()
        if not self.config:
            raise ValueError(f"Config {self.config_id} not found")

        # Initialize Redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = await redis.from_url(redis_url)

        # Initialize API client
        self.api_client = GGBotAPIClient(user_id=self.user_id)

        # Set agent context for MCP tools
        set_agent_context(self.config_id, self.user_id, self.api_client)

        logger.info("Agent initialized successfully")

    async def _load_config(self) -> Optional[Dict[str, Any]]:
        """Load bot configuration from database"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT config_id, user_id, config_data, config_name
                        FROM configurations
                        WHERE config_id = %s AND user_id = %s
                    """, (self.config_id, self.user_id))

                    row = cur.fetchone()
                    if not row:
                        return None

                    return {
                        "config_id": str(row[0]),
                        "user_id": str(row[1]),
                        "config_data": row[2],
                        "config_name": row[3]
                    }
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return None

    def _build_system_prompt(self) -> Dict[str, Any]:
        """Build system prompt with mode and strategy context"""
        strategy_content = self.config.get("config_data", {}).get("agent_strategy", {}).get("content", "Not yet defined")
        autonomously_editable = self.config.get("config_data", {}).get("agent_strategy", {}).get("autonomously_editable", False)

        # Single system prompt, agent adapts based on context
        prompt = f"""
You are an autonomous trading agent. Execute trades, manage positions, and learn from outcomes.

CURRENT MODE: {self.mode}
STRATEGY: {strategy_content}
AUTONOMOUSLY_EDITABLE: {autonomously_editable}

TRADING PHILOSOPHY:
- Execute strategy faithfully
- Always set stop loss and take profit (REQUIRED for safety)
- Use wait_for() tool to control your timing - be patient
- After entering trade with SL/TP, you can wait hours
- Query market data strategically (each query costs credits)

PATIENCE & TIMING:
- Markets need time to develop. Don't overthink or overquery.
- Use wait_for() strategically:
  - Volatile markets: 15-30 minutes
  - Normal conditions: 1-2 hours
  - Position running well: 4-6 hours
  - Waiting for macro event: up to 24 hours

COST CONSCIOUSNESS:
- Each market data query costs credits. Query with purpose.
- Plan your checks instead of constant monitoring.

MODE-SPECIFIC BEHAVIOR:
- strategy_definition: Help user build strategy through conversation. Ask questions, suggest data points, guide to clear strategy. Use request_autonomous_mode tool when ready.
- autonomous: Execute strategy 24/7. Check positions → query data → decide → act (trade/close/wait) → repeat forever.

TRADE MANAGEMENT:
- Can adjust TP if conviction increases
- Close early if invalidation signal appears
- Record trade observations after closing (what worked/failed)

STRATEGY UPDATES:
- If AUTONOMOUSLY_EDITABLE=true: Can update strategy based on learnings
- If AUTONOMOUSLY_EDITABLE=false: Must request user approval for changes

Be disciplined, patient, and cost-conscious.
        """

        return {
            "type": "append",
            "preset": "claude_code",
            "append": prompt
        }

    async def run(self):
        """Main agent loop with two async tasks"""
        try:
            # Create MCP server
            mcp_server = create_mcp_server()

            # Create options
            options = ClaudeAgentOptions(
                model=os.getenv("AGENT_MODEL", "claude-haiku-4-5-20251001"),
                mcp_servers={"trading": mcp_server},
                allowed_tools=[
                    "mcp__trading__query_market_data",
                    "mcp__trading__execute_trade",
                    "mcp__trading__get_positions",
                    "mcp__trading__get_account_status",
                    "mcp__trading__close_position",
                    "mcp__trading__update_strategy",
                    "mcp__trading__wait_for",
                    "mcp__trading__record_trade_observation",
                    "mcp__trading__query_trade_observations",
                    "mcp__trading__request_autonomous_mode"
                ],
                system_prompt=self._build_system_prompt(),
                max_turns=100
            )

            # Start client and run tasks
            async with ClaudeSDKClient(options=options) as client:
                logger.info(f"Agent started in {self.mode} mode")

                # Initial prompt based on mode
                if self.mode == "strategy_definition":
                    await client.query("Hello! I'm ready to help you build your trading strategy. What are your goals?")
                else:  # autonomous
                    await client.query(f"""
Starting autonomous trading mode.

Strategy: {self.config.get('config_data', {}).get('agent_strategy', {}).get('content', 'Undefined')}

Begin the autonomous loop:
1. Check current positions and account
2. Analyze market conditions
3. Execute trades or wait based on strategy
                    """)

                # Run two parallel tasks
                agent_task = asyncio.create_task(self._process_agent_loop(client))
                interrupt_task = asyncio.create_task(self._handle_user_messages(client))

                await asyncio.gather(agent_task, interrupt_task)

        except Exception as e:
            logger.error(f"Agent error: {e}")
            raise
        finally:
            if self.api_client:
                await self.api_client.close()
            if self.redis_client:
                await self.redis_client.aclose()

    async def _process_agent_loop(self, client: ClaudeSDKClient):
        """
        Task 1: Process agent's messages in autonomous loop

        Uses receive_messages() which streams indefinitely.
        Agent uses tools, sleeps via wait_for(), trades forever.
        """
        try:
            async for message in client.receive_messages():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            # Log agent's thinking
                            logger.info(f"Agent: {block.text}")

                            # Push to Redis for user visibility
                            await self.redis_client.rpush(
                                f"agent:{self.config_id}:responses",
                                json.dumps({
                                    "type": "agent_message",
                                    "text": block.text,
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                            )

                # Check for compaction
                if hasattr(message, 'type') and message.get('type') == 'system':
                    if message.get('subtype') == 'compact_boundary':
                        logger.info("Compaction occurred")
                        # Phase 4: Will inject fresh context here

        except Exception as e:
            logger.error(f"Agent loop error: {e}")

    async def _handle_user_messages(self, client: ClaudeSDKClient):
        """
        Task 2: Poll Redis queue and interrupt agent when user sends messages

        Allows user to send messages at any time.
        Agent responds immediately by interrupting current execution.
        """
        try:
            while True:
                # Poll Redis queue with 1 second timeout
                message_data = await self.redis_client.blpop(
                    f"agent:{self.config_id}:messages",
                    timeout=1
                )

                if message_data:
                    _, user_message_bytes = message_data
                    user_message = user_message_bytes.decode('utf-8')

                    logger.info(f"User interrupt: {user_message}")

                    # Interrupt agent's current execution
                    await client.interrupt()

                    # Send user's message
                    await client.query(user_message)

                    # Collect response using receive_response()
                    # (stops at ResultMessage, unlike receive_messages())
                    response_parts = []
                    async for message in client.receive_response():
                        if isinstance(message, AssistantMessage):
                            for block in message.content:
                                if isinstance(block, TextBlock):
                                    response_parts.append(block.text)

                    # Push full response to Redis
                    full_response = "\n".join(response_parts)
                    await self.redis_client.rpush(
                        f"agent:{self.config_id}:responses",
                        json.dumps({
                            "type": "user_response",
                            "text": full_response,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    )

                    logger.info("User message processed")

                # Small sleep to prevent tight loop
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"User message handler error: {e}")


async def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Run autonomous trading agent")
    parser.add_argument(
        "--config-id",
        required=True,
        help="Bot configuration ID"
    )
    parser.add_argument(
        "--mode",
        choices=["strategy_definition", "autonomous"],
        required=True,
        help="Agent mode: strategy_definition or autonomous"
    )

    args = parser.parse_args()

    # Get user_id from config
    # For now, we'll load it from the config lookup
    # In production, this would come from environment or API
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id FROM configurations WHERE config_id = %s
            """, (args.config_id,))
            row = cur.fetchone()
            if not row:
                logger.error(f"Config {args.config_id} not found")
                sys.exit(1)
            user_id = str(row[0])

    # Create and run agent
    agent = TradingAgent(
        config_id=args.config_id,
        user_id=user_id,
        mode=args.mode
    )

    await agent.initialize()
    await agent.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Agent crashed: {e}")
        sys.exit(1)
