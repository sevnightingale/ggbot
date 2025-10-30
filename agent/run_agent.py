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

MARKET DATA STRATEGY:
- Use query_market_data tool to access technical indicators, macro data, sentiment, and signals
- The tool will show you all available categories and data points
- Query strategically - combine 2-3 data sources for context (e.g., RSI + funding rates + sentiment)
- Each query costs credits, so plan your checks instead of constant monitoring
- Technical indicators are fastest (free), macro/sentiment data may take longer (API calls)

CRITICAL: Use EXACT data point names from tool documentation:
- "twitter_sentiment" NOT "twitter" or "sentiment"
- "ggshot" NOT "ggshot_signals"
- "btc_funding_rate" NOT "funding_rate"
DO NOT abbreviate or modify data point names - they must match exactly.

Be disciplined, patient, and cost-conscious.
        """

        return prompt  # Return plain string, not dict

    async def run(self):
        """
        Main agent entry point.

        Routes to appropriate mode:
        - strategy_definition: Interactive chat to build strategy
        - autonomous: 24/7 trading with no user interaction
        """
        try:
            # Create MCP server
            mcp_server = create_mcp_server()

            # Create options
            options = ClaudeAgentOptions(
                model=os.getenv("AGENT_MODEL", "claude-haiku-4-5-20251001"),
                mcp_servers={"trading": mcp_server},
                allowed_tools=[
                    "mcp__trading__query_market_data",
                    "mcp__trading__get_current_price",  # NEW: Lightweight price check
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
                disallowed_tools=[
                    "Task", "Bash", "Read", "Write", "Edit", "Glob", "Grep",
                    "WebFetch", "WebSearch", "SlashCommand", "Skill", "TodoWrite",
                    "ExitPlanMode", "NotebookEdit", "BashOutput", "KillShell",
                    "AskUserQuestion", "ListMcpResourcesTool", "ReadMcpResourceTool"
                ],
                system_prompt=self._build_system_prompt(),
                max_turns=100
            )

            # Start client and route to appropriate mode
            async with ClaudeSDKClient(options=options) as client:
                logger.info(f"Agent started in {self.mode} mode")

                if self.mode == "strategy_definition":
                    await self._run_strategy_definition(client)
                else:  # autonomous
                    await self._run_autonomous(client)

        except Exception as e:
            logger.error(f"Agent error: {e}")
            raise
        finally:
            if self.api_client:
                await self.api_client.close()
            if self.redis_client:
                await self.redis_client.aclose()

    async def _run_strategy_definition(self, client: ClaudeSDKClient):
        """
        Strategy Definition Mode: Interactive conversation to build strategy.

        Pattern:
        1. Agent greets user
        2. User sends messages via Redis queue
        3. Agent responds via query/receive_response pattern
        4. When ready, agent calls request_autonomous_mode tool
        5. User confirms → save strategy, exit
        """
        logger.info("Starting strategy definition mode")

        # Initial greeting
        await client.query("Hello! I'm ready to help you build your trading strategy. What are your goals?")

        # Process initial greeting
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        logger.info(f"Agent: {block.text}")
                        await self.redis_client.rpush(
                            f"agent:{self.config_id}:responses",
                            json.dumps({
                                "type": "agent_message",
                                "text": block.text,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        )

        # Main conversation loop
        logger.info("Waiting for user messages...")
        while True:
            # Block until user sends message
            message_data = await self.redis_client.blpop(
                f"agent:{self.config_id}:messages",
                timeout=0  # Block indefinitely
            )

            if message_data:
                _, user_message_bytes = message_data
                user_message_json = json.loads(user_message_bytes.decode('utf-8'))
                user_text = user_message_json.get("text", "")

                logger.info(f"User: {user_text}")

                # Send to agent
                await client.query(user_text)

                # Collect response
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                logger.info(f"Agent: {block.text}")
                                await self.redis_client.rpush(
                                    f"agent:{self.config_id}:responses",
                                    json.dumps({
                                        "type": "agent_message",
                                        "text": block.text,
                                        "timestamp": datetime.utcnow().isoformat()
                                    })
                                )

                # Check if mode switch was requested (would be in Redis flag)
                mode_switch_pending = await self.redis_client.get(
                    f"agent:{self.config_id}:mode_switch_pending"
                )
                if mode_switch_pending:
                    logger.info("Mode switch requested - waiting for user confirmation")

                    # Wait for user's confirmation (1 or 2)
                    confirmation_data = await self.redis_client.blpop(
                        f"agent:{self.config_id}:messages",
                        timeout=0  # Block indefinitely
                    )

                    if confirmation_data:
                        _, confirmation_bytes = confirmation_data
                        confirmation_json = json.loads(confirmation_bytes.decode('utf-8'))
                        user_choice = confirmation_json.get("text", "").strip()

                        if user_choice == "1":
                            # CONFIRM - Save strategy and exit
                            logger.info("User confirmed autonomous mode - saving strategy")

                            # Retrieve strategy from Redis
                            pending_strategy = await self.redis_client.get(
                                f"agent:{self.config_id}:pending_strategy"
                            )

                            if pending_strategy:
                                strategy_text = pending_strategy.decode('utf-8')

                                # Save to database
                                await self._save_strategy(strategy_text)

                                # Send confirmation message
                                await self.redis_client.rpush(
                                    f"agent:{self.config_id}:responses",
                                    json.dumps({
                                        "type": "agent_message",
                                        "text": "✅ Strategy saved! Exiting strategy definition mode.\n\nTo start autonomous trading, restart with:\npython agent/run_agent.py --config-id={} --mode=autonomous".format(self.config_id),
                                        "timestamp": datetime.utcnow().isoformat()
                                    })
                                )

                                # Clean up Redis
                                await self.redis_client.delete(
                                    f"agent:{self.config_id}:mode_switch_pending",
                                    f"agent:{self.config_id}:pending_strategy"
                                )

                                logger.info("Strategy saved successfully - exiting")
                                break
                            else:
                                logger.error("No pending strategy found in Redis")

                        elif user_choice == "2":
                            # REVISE - Clear flag and continue conversation
                            logger.info("User chose to revise strategy - continuing conversation")

                            # Clear flags
                            await self.redis_client.delete(
                                f"agent:{self.config_id}:mode_switch_pending",
                                f"agent:{self.config_id}:pending_strategy"
                            )

                            # Send to agent
                            await client.query("The user wants to revise the strategy. Let's continue refining it.")

                            # Collect response
                            async for message in client.receive_response():
                                if isinstance(message, AssistantMessage):
                                    for block in message.content:
                                        if isinstance(block, TextBlock):
                                            logger.info(f"Agent: {block.text}")
                                            await self.redis_client.rpush(
                                                f"agent:{self.config_id}:responses",
                                                json.dumps({
                                                    "type": "agent_message",
                                                    "text": block.text,
                                                    "timestamp": datetime.utcnow().isoformat()
                                                })
                                            )
                        else:
                            # Invalid choice - ask again
                            logger.warning(f"Invalid confirmation choice: {user_choice}")
                            await self.redis_client.rpush(
                                f"agent:{self.config_id}:responses",
                                json.dumps({
                                    "type": "agent_message",
                                    "text": "Please reply with '1' to CONFIRM or '2' to REVISE the strategy.",
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                            )

    async def _save_strategy(self, strategy_content: str):
        """Save strategy to database config_data.agent_strategy"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get current config_data
                    cur.execute("""
                        SELECT config_data FROM configurations
                        WHERE config_id = %s AND user_id = %s
                    """, (self.config_id, self.user_id))

                    row = cur.fetchone()
                    if not row:
                        logger.error("Config not found for saving strategy")
                        return

                    config_data = row[0] or {}

                    # Update agent_strategy
                    config_data['agent_strategy'] = {
                        "content": strategy_content,
                        "autonomously_editable": False,  # Default to guided mode
                        "version": 1,
                        "last_updated_at": datetime.utcnow().isoformat(),
                        "last_updated_by": "user",
                        "performance_log": []
                    }

                    # Save back to database
                    cur.execute("""
                        UPDATE configurations
                        SET config_data = %s, updated_at = NOW()
                        WHERE config_id = %s AND user_id = %s
                    """, (json.dumps(config_data), self.config_id, self.user_id))

                    conn.commit()
                    logger.info(f"Strategy saved to config {self.config_id}")

        except Exception as e:
            logger.error(f"Failed to save strategy: {e}")
            raise

    async def _run_autonomous(self, client: ClaudeSDKClient):
        """
        Autonomous Mode: 24/7 trading with NO user interaction.

        Pattern:
        1. Agent starts with strategy loaded
        2. Uses receive_messages() indefinitely
        3. Agent uses tools (query_market_data, execute_trade, wait_for, etc.)
        4. All actions logged to database
        5. To stop: User kills process (Ctrl+C or PM2 stop)
        6. To chat: User restarts in strategy_definition mode
        """
        logger.info("Starting autonomous trading mode")

        strategy = self.config.get('config_data', {}).get('agent_strategy', {}).get('content', 'Undefined')
        logger.info(f"Strategy: {strategy}")

        # Initial prompt to start autonomous loop
        await client.query(f"""
You are now in autonomous trading mode.

Your strategy:
{strategy}

Begin autonomous execution:
1. Check your current account status and positions
2. Analyze market data for your trading pair
3. Execute your strategy (trade, close, or wait)
4. Use wait_for() to control timing - be patient
5. Record trade observations after closing positions
6. Repeat forever

Start now.
""")

        # Process indefinitely
        async for message in client.receive_messages():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        # Log all agent activity
                        logger.info(f"Agent: {block.text}")

            # Check for compaction
            if hasattr(message, 'type') and getattr(message, 'type', None) == 'system':
                if hasattr(message, 'subtype') and getattr(message, 'subtype', None) == 'compact_boundary':
                    logger.info("Context compaction occurred")
                    # Phase 4: Inject fresh trading context here


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
