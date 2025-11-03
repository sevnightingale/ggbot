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

# Configure detailed agent logging to file
# IMPORTANT: Only configure logger here (not in mcp_server.py or service_client.py)
# to avoid duplicate log entries
logger.add(
    "/home/sev/ggbot/logs/agent-debug.log",
    rotation="10 MB",
    retention="3 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    backtrace=True,
    diagnose=True
)

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock, ResultMessage

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

FRAMEWORK RULES:
- Execute the strategy faithfully - it is your source of truth
- Always set stop loss and take profit (REQUIRED for safety)
- Record trade observations after closing positions (what worked/failed)
- Use wait_for() tool to control your timing as the strategy specifies

MODE-SPECIFIC BEHAVIOR:

strategy_definition: Help user build a complete strategy for YOU to execute autonomously.

  START by assessing:
  1. User's experience level (beginner/intermediate/advanced)
  2. Whether they have a strategy in mind already

  THEN branch:
  - If inexperienced/no strategy: Show available data sources (7 categories, 32 data points).
    Explain how indicators work and guide them toward proven patterns. Be educational.
  - If experienced/has strategy: Validate feasibility with your available data.
    Check if you can execute their strategy, suggest alternatives if gaps exist.

  ALWAYS ground in reality:
  - Only suggest strategies using data you actually have access to
  - Be specific about what you CAN and CANNOT do
  - Make rules testable and executable

  MUST define before switching to autonomous:
  - Entry conditions (specific, testable)
  - Exit conditions (SL/TP minimum)
  - Position sizing rules
  - Monitoring frequency

  Use save_strategy_and_exit when strategy is finalized to save it and exit.

autonomous: Execute the strategy 24/7 without user interaction.
  - Check positions first (close if exit conditions met)
  - Query market data as strategy specifies
  - Execute trades when entry conditions met
  - Use wait_for() between checks as strategy defines
  - Record observations after closing trades

STRATEGY UPDATES:
- If AUTONOMOUSLY_EDITABLE=true: Can update strategy based on learnings using update_strategy tool
- If AUTONOMOUSLY_EDITABLE=false: Cannot modify strategy - execute it as written

AVAILABLE DATA SOURCES:
Use query_market_data tool with these EXACT categories and data point names:

CATEGORIES:
- technical_analysis: RSI, MACD, Stochastic, Williams_R, CCI, MFI, ADX, PSAR, Aroon, ATR, BB, OBV, SMA, EMA, ROC, VWAP, TRIX, Vortex, BBWidth, Keltner, Donchian
- macro_economics: vix, dxy, cpi, nfp
- sentiment_social: twitter_sentiment
- derivatives_leverage: btc_funding_rate, eth_funding_rate
- on_chain_analytics: btc_tvl, whale_activity
- news_regulatory: crypto_news
- trading_signals: ggshot

CRITICAL RULES:
1. ggshot is a TRADING SIGNAL, NOT a technical indicator
   ✅ CORRECT: {{"trading_signals": ["ggshot"]}}
   ❌ WRONG: {{"technical_analysis": ["ggshot"]}}

2. Use EXACT names (case-insensitive but complete):
   - "twitter_sentiment" NOT "twitter" or "sentiment"
   - "ggshot" NOT "ggshot_signals"
   - "btc_funding_rate" NOT "funding_rate"

3. Category names must be EXACT:
   - "trading_signals" NOT "signals" or "trading_signal"

Be disciplined and execute the strategy faithfully.
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

            # Build system prompt and log it
            system_prompt = self._build_system_prompt()
            logger.debug(f"📋 SYSTEM PROMPT:\n{'='*80}\n{system_prompt}\n{'='*80}")

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
                    "mcp__trading__save_strategy_and_exit"
                ],
                disallowed_tools=[
                    "Task", "Bash", "Read", "Write", "Edit", "Glob", "Grep",
                    "WebFetch", "WebSearch", "SlashCommand", "Skill", "TodoWrite",
                    "ExitPlanMode", "NotebookEdit", "BashOutput", "KillShell",
                    "AskUserQuestion", "ListMcpResourcesTool", "ReadMcpResourceTool"
                ],
                system_prompt=system_prompt,
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
        4. When ready, agent calls save_strategy_and_exit → saves and exits
        """
        logger.info("Starting strategy definition mode - waiting for user's first message...")

        # No greeting query - let frontend send first message to avoid confusion
        # Frontend will send either:
        #   - User's existing strategy (for refinement)
        #   - User's goals (for new strategy creation)
        # Agent responds appropriately to whatever arrives first

        # Main conversation loop
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

                # LOG: User message to agent
                logger.debug(f"👤 USER MESSAGE TO AGENT: {user_text}")

                # Store user message in conversation history
                await self.redis_client.rpush(
                    f"agent:{self.config_id}:history",
                    json.dumps({
                        "role": "user",
                        "content": user_text,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                )

                # Send to agent
                await client.query(user_text)

                # Collect response
                async for message in client.receive_response():
                    # LOG: Full message structure
                    logger.debug(f"🤖 AGENT MESSAGE RECEIVED: {message}")

                    response_text = None
                    is_final = False

                    # Handle AssistantMessage (streaming responses with TextBlocks)
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                response_text = block.text
                        # Don't store streaming messages to history (ResultMessage will have the final version)
                        is_final = False

                    # Handle ResultMessage (final consolidated response)
                    elif isinstance(message, ResultMessage):
                        response_text = message.result
                        is_final = True  # This is the final version, store to history

                    if response_text:
                        logger.info(f"Agent: {response_text[:200]}...")
                        logger.debug(f"🤖 AGENT TEXT: {response_text}")

                        # Only push to queues for final ResultMessage (not streaming AssistantMessage)
                        if is_final:
                            response_data = {
                                "type": "agent_message",
                                "text": response_text,
                                "timestamp": datetime.utcnow().isoformat()
                            }

                            # Push to response queue for polling
                            await self.redis_client.rpush(
                                f"agent:{self.config_id}:responses",
                                json.dumps(response_data)
                            )

                            # Store in conversation history
                            await self.redis_client.rpush(
                                f"agent:{self.config_id}:history",
                                json.dumps({
                                    "role": "agent",
                                    "content": response_text,
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                            )

                            # Log agent thought as activity for timeline
                            try:
                                from core.common.activity_logger import log_activity

                                # Create a short summary from first line or first 50 chars
                                summary = response_text.split('\n')[0][:50]
                                if len(response_text.split('\n')[0]) > 50:
                                    summary += "..."

                                # log_activity is synchronous, no await needed
                                log_activity(
                                    config_id=self.config_id,
                                    user_id=self.user_id,
                                    activity_type='analysis',
                                    activity_source='agent_tool',
                                    summary=summary,
                                    details={'thought': response_text},
                                    priority=2,
                                    importance=5
                                )
                            except Exception as e:
                                logger.error(f"Failed to log agent thought activity: {e}")

                # Check if agent saved strategy and wants to exit
                strategy_saved = await self.redis_client.get(
                    f"agent:{self.config_id}:strategy_saved_exit"
                )
                if strategy_saved:
                    logger.info("Strategy saved - agent exiting strategy definition mode")

                    # Clean up Redis flag
                    await self.redis_client.delete(f"agent:{self.config_id}:strategy_saved_exit")

                    # Exit loop
                    break


    async def _save_strategy(self, strategy_content: str, autonomously_editable: bool = False):
        """
        Save strategy to database config_data.agent_strategy

        Args:
            strategy_content: Strategy text content
            autonomously_editable: Whether agent can modify its own strategy
        """
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

                    # Get current version if updating existing strategy
                    current_version = config_data.get('agent_strategy', {}).get('version', 0)

                    # Update agent_strategy
                    config_data['agent_strategy'] = {
                        "content": strategy_content,
                        "autonomously_editable": autonomously_editable,
                        "version": current_version + 1,
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
            # Handle AssistantMessage (streaming responses with TextBlocks)
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        # Log all agent activity
                        logger.info(f"Agent: {block.text}")

            # Handle ResultMessage (final consolidated response)
            elif isinstance(message, ResultMessage):
                logger.info(f"Agent: {message.result}")

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
