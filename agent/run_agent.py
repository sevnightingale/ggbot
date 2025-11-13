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
from datetime import datetime, timezone

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
    diagnose=True,
    enqueue=True,  # Thread-safe async logging
    catch=True     # Catch exceptions in logging sink
)

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock, ResultMessage, SystemMessage

from agent.mcp_server import create_mcp_server, set_agent_context
from agent.service_client import GGBotAPIClient
from core.common.db import get_db_connection
from core.common.activity_logger import log_activity_safe

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
        self.session_id: Optional[str] = None  # SDK session ID for resumption

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

        # Set agent context for MCP tools (fetches trading_mode from DB)
        await set_agent_context(self.config_id, self.user_id, self.api_client)

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

    async def _load_session_id(self) -> Optional[str]:
        """Load existing SDK session ID from database for resumption"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT session_id, last_active_at
                        FROM agent_sessions
                        WHERE config_id = %s
                    """, (self.config_id,))

                    row = cur.fetchone()
                    if row:
                        session_id, last_active_at = row
                        logger.info(f"📖 Found existing session: {session_id[:16]}... (last active: {last_active_at})")
                        return session_id
                    else:
                        logger.info("📝 No existing session found - will create new one")
                        return None
        except Exception as e:
            logger.error(f"Failed to load session ID: {e}")
            return None

    async def _save_session_id(self, session_id: str):
        """Save SDK session ID to database for future resumption"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO agent_sessions (config_id, session_id, last_active_at, created_at, updated_at)
                        VALUES (%s, %s, NOW(), NOW(), NOW())
                        ON CONFLICT (config_id)
                        DO UPDATE SET
                            session_id = EXCLUDED.session_id,
                            last_active_at = NOW(),
                            updated_at = NOW()
                    """, (self.config_id, session_id))
                    conn.commit()
            logger.info(f"💾 Saved session ID: {session_id[:16]}...")
        except Exception as e:
            logger.error(f"Failed to save session ID: {e}")

    async def _update_session_activity(self):
        """Update last_active_at timestamp for health monitoring"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE agent_sessions
                        SET last_active_at = NOW(),
                            updated_at = NOW()
                        WHERE config_id = %s
                    """, (self.config_id,))
                    conn.commit()
        except Exception as e:
            logger.warning(f"Failed to update session activity: {e}")

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

            # LOG: Tool descriptions from MCP server
            logger.info("=" * 80)
            logger.info("📚 MCP TOOL DESCRIPTIONS BEING SENT TO AGENT:")
            logger.info("=" * 80)

            # The MCP server is a dict with 'instance' key containing the actual Server object
            if isinstance(mcp_server, dict) and 'instance' in mcp_server:
                mcp_instance = mcp_server['instance']
                try:
                    # list_tools() is async and needs request context, so we can't call it here
                    # Instead, just log that 12 tools are registered (we know from debug logs above)
                    logger.info("✅ MCP Server initialized with 12 tools:")
                    logger.info("   1. query_market_data - Market data across 7 categories with 32+ data points")
                    logger.info("   2. get_current_price - Real-time WebSocket price lookup")
                    logger.info("   3. execute_trade - Execute trades with required SL/TP")
                    logger.info("   4. get_positions - Query open positions (paper/aster/symphony)")
                    logger.info("   5. get_account_status - Balance and performance metrics")
                    logger.info("   6. close_position - Manually close positions")
                    logger.info("   7. cancel_order - Cancel TP/SL orders (paper/aster)")
                    logger.info("   8. update_strategy - Update strategy (experimental mode)")
                    logger.info("   9. wait_for - Control timing (max 24h)")
                    logger.info("  10. record_trade_observation - Post-trade reflection")
                    logger.info("  11. query_trade_observations - Search past learnings")
                    logger.info("  12. save_strategy_and_exit - Save strategy and exit")
                    logger.info("\n  All tools will be available to agent via MCP protocol.")
                except Exception as e:
                    logger.warning(f"Could not introspect MCP tools: {e}")
            else:
                logger.warning("MCP server structure unexpected - tools should still work")

            logger.info("=" * 80)

            # Build system prompt and log it
            system_prompt = self._build_system_prompt()
            logger.debug(f"📋 SYSTEM PROMPT:\n{'='*80}\n{system_prompt}\n{'='*80}")

            # Load existing session for resumption (conversation persistence)
            existing_session_id = await self._load_session_id()

            # Use separate API key for agents to avoid mixing with interactive Claude Code sessions
            # SDK reads from ANTHROPIC_API_KEY env var, so we override it if AGENT_ANTHROPIC_API_KEY is set
            agent_api_key = os.getenv("AGENT_ANTHROPIC_API_KEY")
            if agent_api_key:
                os.environ["ANTHROPIC_API_KEY"] = agent_api_key
                logger.info("🔑 Using separate AGENT_ANTHROPIC_API_KEY (isolated from Claude Code sessions)")
            else:
                logger.warning("⚠️  AGENT_ANTHROPIC_API_KEY not set - will use default ANTHROPIC_API_KEY (sessions will mix with Claude Code)")

            # Create options with session resumption if available
            options_dict = {
                "model": os.getenv("AGENT_MODEL", "claude-sonnet-4-5-20250929"),
                "mcp_servers": {"trading": mcp_server},
                "allowed_tools": [
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
                "disallowed_tools": [
                    "Task", "Bash", "Read", "Write", "Edit", "Glob", "Grep",
                    "WebFetch", "WebSearch", "SlashCommand", "Skill", "TodoWrite",
                    "ExitPlanMode", "NotebookEdit", "BashOutput", "KillShell",
                    "AskUserQuestion", "ListMcpResourcesTool", "ReadMcpResourceTool"
                ],
                "system_prompt": system_prompt,
                "max_turns": 100
            }

            # Add resume parameter if we have an existing session
            if existing_session_id:
                options_dict["resume"] = existing_session_id
                logger.info(f"🔄 Resuming from session: {existing_session_id[:16]}...")
            else:
                logger.info("🆕 Starting fresh session")

            options = ClaudeAgentOptions(**options_dict)

            # Start client and route to appropriate mode
            async with ClaudeSDKClient(options=options) as client:
                logger.info(f"Agent started in {self.mode} mode")

                # Session ID will be captured in the message loop
                # (can't capture here - receive_messages() can only be iterated once)

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

        # Session capture flag
        session_captured = False

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
                    # Capture session ID from init message (happens once at startup)
                    if not session_captured:
                        # Check for SystemMessage type (SDK uses this class)
                        if isinstance(message, SystemMessage):
                            if hasattr(message, 'subtype') and message.subtype == 'init':
                                if hasattr(message, 'data') and 'session_id' in message.data:
                                    self.session_id = message.data['session_id']
                                    logger.info(f"✅ Captured session ID: {self.session_id[:16]}...")
                                    await self._save_session_id(self.session_id)
                                    session_captured = True
                        # Fallback: check for direct attributes (if SDK structure changes)
                        elif hasattr(message, 'type') and message.type == 'system':
                            if hasattr(message, 'subtype') and message.subtype == 'init':
                                if hasattr(message, 'session_id'):
                                    self.session_id = message.session_id
                                    logger.info(f"✅ Captured session ID: {self.session_id[:16]}...")
                                    await self._save_session_id(self.session_id)
                                    session_captured = True

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

        # STARTUP CHECK: Get current state before agent starts
        logger.info("Performing startup checks...")
        startup_context = ""
        try:
            # Get account status
            account_result = await self.api_client.get_account_status(config_id=self.config_id)
            account = account_result.get('account', {})
            trading_mode = account_result.get('trading_mode', 'unknown')
            balance = account.get('balance', 0)

            # Get open positions
            positions_result = await self.api_client.get_positions(config_id=self.config_id)
            positions = positions_result.get('positions', [])

            # Log startup state to activity timeline
            log_activity_safe(
                config_id=self.config_id,
                user_id=self.user_id,
                activity_type='analysis',
                activity_source='agent',
                summary=f"Agent started - Balance: ${balance:.2f}, Open positions: {len(positions)}",
                details={
                    'thought': f"Agent restarted. Current state:\n- Trading Mode: {trading_mode}\n- Balance: ${balance:.2f}\n- Open Positions: {len(positions)}",
                    'trading_mode': trading_mode,
                    'balance': balance,
                    'positions_count': len(positions)
                }
            )

            # Build context for agent
            startup_context = f"""
## STARTUP STATE (as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}):
- Trading Mode: {trading_mode.upper()}
- Account Balance: ${balance:,.2f}
- Open Positions: {len(positions)}
"""

            if positions:
                startup_context += "\n**OPEN POSITIONS:**\n"
                for pos in positions:
                    side = pos.get('side', 'unknown').upper()
                    symbol = pos.get('symbol', 'unknown')
                    entry = pos.get('entry_price', 0)
                    current = pos.get('current_price', 0)
                    pnl = pos.get('unrealized_pnl', 0)
                    pnl_pct = pos.get('unrealized_pnl_percentage', 0)
                    startup_context += f"- {symbol} {side}: Entry ${entry:.2f}, Current ${current:.2f}, P&L ${pnl:.2f} ({pnl_pct:.2f}%)\n"
            else:
                startup_context += "- No open positions (clean slate)\n"

            logger.info(f"Startup check complete: Balance=${balance:.2f}, Positions={len(positions)}")

        except Exception as e:
            logger.error(f"Startup check failed: {e}", exc_info=True)
            startup_context = "\n## STARTUP STATE: Unable to retrieve current state (check failed)\n"

        # Initial prompt to start autonomous loop
        await client.query(f"""
You are now in autonomous trading mode.
{startup_context}
Your strategy:
{strategy}

Begin autonomous execution:
1. Acknowledge your current state (positions, balance)
2. Analyze market data for opportunities
3. Execute your strategy (trade, close, or wait)
4. Use wait_for() to control timing - be patient
5. Record trade observations after closing positions
6. Repeat forever

Start now.
""")

        # Process indefinitely with retry logic
        max_retries = 10
        retry_count = 0
        base_delay = 5  # seconds
        message_count = 0  # Track messages for periodic heartbeat
        session_captured = False  # Track if we've captured session ID

        while True:  # Infinite retry loop for resilience
            try:
                async for message in client.receive_messages():
                    # DEBUG: Log ALL message types for troubleshooting
                    msg_type = type(message).__name__
                    if message_count < 5:  # Only log first 5 messages to avoid spam
                        logger.debug(f"🔍 Message received: type={msg_type}, has_type_attr={hasattr(message, 'type')}")
                        if hasattr(message, 'type'):
                            logger.debug(f"   message.type={message.type}, has_subtype={hasattr(message, 'subtype')}")
                            if hasattr(message, 'subtype'):
                                logger.debug(f"   message.subtype={message.subtype}, has_session_id={hasattr(message, 'session_id')}")

                    # Capture session ID from init message (happens once at startup)
                    if not session_captured:
                        # Check for SystemMessage type (SDK uses this class)
                        if isinstance(message, SystemMessage):
                            logger.debug(f"📋 SystemMessage instance detected: {message}")
                            if hasattr(message, 'subtype') and message.subtype == 'init':
                                if hasattr(message, 'data') and 'session_id' in message.data:
                                    self.session_id = message.data['session_id']
                                    logger.info(f"✅ Captured session ID: {self.session_id[:16]}...")
                                    await self._save_session_id(self.session_id)
                                    session_captured = True
                                else:
                                    logger.warning("⚠️ Found SystemMessage init but no session_id in data!")
                        # Fallback: check for direct attributes (if SDK structure changes)
                        elif hasattr(message, 'type') and message.type == 'system':
                            if hasattr(message, 'subtype') and message.subtype == 'init':
                                if hasattr(message, 'session_id'):
                                    self.session_id = message.session_id
                                    logger.info(f"✅ Captured session ID: {self.session_id[:16]}...")
                                    await self._save_session_id(self.session_id)
                                    session_captured = True

                    # Reset retry counter on successful message
                    retry_count = 0
                    message_count += 1

                    # Update session activity heartbeat every 10 messages
                    if message_count % 10 == 0:
                        await self._update_session_activity()

                    # Handle AssistantMessage (streaming responses with TextBlocks)
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                # Log all agent activity
                                logger.info(f"Agent: {block.text}")

                                # Save agent thoughts to activity timeline
                                log_activity_safe(
                                    config_id=self.config_id,
                                    user_id=self.user_id,
                                    activity_type='analysis',
                                    activity_source='agent',
                                    summary=block.text[:200],  # Truncate for summary
                                    details={'thought': block.text}
                                )

                    # Handle ResultMessage (final consolidated response)
                    elif isinstance(message, ResultMessage):
                        logger.info(f"Agent: {message.result}")

                        # Save agent thoughts to activity timeline (only if result is not None)
                        if message.result:
                            log_activity_safe(
                                config_id=self.config_id,
                                user_id=self.user_id,
                                activity_type='analysis',
                                activity_source='agent',
                                summary=message.result[:200],  # Truncate for summary
                                details={'thought': message.result}
                            )
                        else:
                            logger.warning("Agent returned None result, skipping activity log")

                    # Check for compaction
                    if isinstance(message, SystemMessage):
                        if message.subtype == 'compact_boundary':
                            logger.warning("🔄 Context compaction occurred - reinjecting critical state")

                            # Reinject critical trading context
                            await client.query(f"""
CONTEXT REFRESH AFTER COMPACTION:

The conversation context was just compacted. Please refresh your understanding:

1. **Check Current Positions**: Use get_positions to see if you have any open trades
2. **Check Account Balance**: Use get_account_status to see available capital
3. **Review Your Strategy**: {self.config.get('config_data', {}).get('agent_strategy', {}).get('content', 'No strategy defined')}
4. **Resume Execution**: Continue monitoring and trading according to your strategy

Current timestamp: {datetime.now(timezone.utc).isoformat()}
""")

                # If we exit the async for loop normally (stream ended), log it and retry
                logger.warning("Message stream ended unexpectedly, restarting agent loop...")
                retry_count += 1
                delay = min(base_delay * (2 ** retry_count), 300)  # Max 5 min backoff
                logger.info(f"Retry {retry_count}/{max_retries} in {delay}s...")
                await asyncio.sleep(delay)

                # Restart the client query to resume autonomous mode
                await client.query("Continue autonomous trading from where you left off.")

            except KeyboardInterrupt:
                logger.info("Agent stopped by user (KeyboardInterrupt)")
                raise
            except Exception as e:
                retry_count += 1
                error_str = str(e)

                # Detect specific error types by string matching (since we can't import anthropic)
                is_rate_limit = '429' in error_str or '529' in error_str or 'overload' in error_str.lower() or 'rate limit' in error_str.lower()
                is_api_error = any(code in error_str for code in ['500', '502', '503', '504'])

                if is_rate_limit:
                    logger.warning(f"🚦 Rate limit detected (429/529): {e}")
                    delay = 60  # Fixed 60s for rate limits
                    error_type = 'rate_limit'
                elif is_api_error:
                    logger.error(f"⚠️  API server error detected: {e}")
                    delay = min(base_delay * (2 ** retry_count), 300)  # Exponential backoff
                    error_type = 'api_server_error'
                else:
                    logger.error(f"❌ Unexpected agent loop error (retry {retry_count}/{max_retries}): {e}", exc_info=True)
                    delay = min(base_delay * (2 ** retry_count), 300)  # Exponential backoff
                    error_type = 'unknown_error'

                if retry_count >= max_retries:
                    logger.critical(f"Max retries ({max_retries}) exceeded, agent stopping")
                    raise

                logger.info(f"Retrying in {delay}s...")

                # Log retry to activity timeline
                log_activity_safe(
                    config_id=self.config_id,
                    user_id=self.user_id,
                    activity_type='analysis',
                    activity_source='agent',
                    summary=f"Agent encountered {error_type}, retrying in {delay}s (attempt {retry_count}/{max_retries})",
                    details={'error': str(e), 'error_type': error_type, 'retry_count': retry_count}
                )

                await asyncio.sleep(delay)

                # Restart the client query to resume autonomous mode
                await client.query("Continue autonomous trading. Check current positions and market state.")


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
