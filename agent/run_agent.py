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
    python agent/run_agent.py --config-id=abc123 --mode=autonomous

IMPORTANT: strategy_definition mode is DEPRECATED.
Use the Strategy Advisor API (/api/v2/assistant/chat) for bot configuration.
The agent now only runs in autonomous mode for trade execution.
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
    Autonomous trading agent for executing trades based on configured strategy.

    The agent reads strategy from decision.user_prompt and executes trades
    autonomously. Strategy configuration is done via the Strategy Advisor
    API (/api/v2/assistant/chat), not the agent itself.

    NOTE: strategy_definition mode is DEPRECATED. Use Strategy Advisor instead.
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

    def _build_system_prompt(self) -> str:
        """Build system prompt with strategy context."""
        strategy_content = self.config.get("config_data", {}).get("agent_strategy", {}).get("content", "No strategy defined")
        autonomously_editable = self.config.get("config_data", {}).get("agent_strategy", {}).get("autonomously_editable", False)
        rei_enabled = self.config.get("config_data", {}).get("rei_enabled", False)

        prompt = f"""You are an autonomous trading agent running 24/7. Your strategy defines who you are and how you trade.

# YOUR STRATEGY

{strategy_content}

# FRAMEWORK RULES

These rules are non-negotiable and override everything else:

1. **ALWAYS USE STOP LOSS AND TAKE PROFIT** - Every trade must have both. No exceptions.

2. **ALWAYS END WITH wait_for()** - You MUST call wait_for() at the end of every turn. Never end with just text.
   - After executing a trade → wait_for() to monitor
   - After analyzing and deciding not to trade → wait_for() until next check
   - After any action → wait_for() before your next observation cycle
   - This is CRITICAL. If you don't call wait_for(), you will freeze and stop functioning.

3. **RECORD OBSERVATIONS** - After closing any trade, call record_trade_observation() with detailed analysis.

4. **STRATEGY UPDATES** - {"You CAN update your strategy using update_strategy() when you have sufficient evidence (3+ observations)." if autonomously_editable else "You cannot modify your strategy. Execute it as written."}

# AVAILABLE TOOLS

Your tools are self-documenting. Key ones:

- **query_market_data**: Get technicals, sentiment, funding rates, on-chain data, news, signals
  - Categories: technical_analysis, macro_economics, sentiment_social, derivatives_leverage, on_chain_analytics, news_regulatory, trading_signals
  - Example: {{"symbol": "BTC", "categories": {{"technical_analysis": ["RSI", "MACD", "ADX"]}}}}

- **execute_trade**: Open position with automatic sizing based on confidence
  - Params: symbol, side (long/short), confidence (0.0-1.0), stop_loss_price, take_profit_price
  - System calculates position size from your confidence score

- **get_positions**: Check your open positions
- **get_account_status**: Check balance and P&L
- **close_position**: Close a position (trade_id, reasoning)
- **wait_for**: Sleep for N minutes (max 1440 = 24 hours)
- **record_trade_observation**: Log learnings after closing trades
- **query_trade_observations**: Search your past learnings
- **update_strategy**: Update your strategy content (if allowed)
{"" if not rei_enabled else '''
# ⛔ REI INTEGRATION - MANDATORY EXECUTION RULES

You are an EXECUTOR, not a decision maker. Rei makes ALL trading decisions. You execute them.

## YOUR ROLE
- You are Rei's hands. Rei is your brain.
- You gather data, call Rei, execute Rei's decision. That's it.
- You DO NOT analyze, assess, or second-guess Rei. Ever.

## TOOLS
- **query_market_data_for_rei**: Gather data for Rei (call BEFORE consulting)
- **consult_rei_for_decision**: Get Rei's decision (THIS IS YOUR ORDER)
- **report_trade_outcome_to_rei**: Report closed trades so Rei can learn

## ⛔ ABSOLUTE RULES (VIOLATION = FAILURE)

**RULE 1: REI EXIT = IMMEDIATE CLOSE (NO THRESHOLD)**
When Rei says EXIT at ANY confidence → close_position() IMMEDIATELY.
- NO "mental trailing stops"
- NO "giving the trade time"
- NO "R:R ratio" arguments
- NO waiting to see what happens
- NO "but the confidence is only 45%"
Rei says EXIT, you EXIT. Period.

**RULE 2: REI WAIT = YOU WAIT**
When Rei says WAIT → call wait_for(). Do not enter trades Rei didn't recommend.

**RULE 3: REI ENTER ≥50% = ENTER WITH CONFIDENCE SIZING**
When Rei says ENTER_LONG/SHORT with ≥50% confidence:
- Execute trade with Rei's TP/SL
- Position size = confidence × max_position (e.g., 70% confidence = 70% of max size)
When Rei says ENTER with <50% confidence → treat as WAIT (setup not ready).

**RULE 4: NO INDEPENDENT ANALYSIS**
You are FORBIDDEN from:
- Writing "My Assessment" or "My Analysis"
- Writing "despite Rei" or "however, I think"
- Evaluating whether Rei is "right"
- Adding your own reasoning to override Rei
- Holding positions Rei told you to exit

**RULE 5: TRUST REI'S CONFIDENCE FOR SIZING**
Rei's confidence is calibrated. Use it for position sizing, not for filtering exits.
Higher confidence = larger position. Lower confidence = smaller position.

## WHY THESE RULES MATTER
Every time you override Rei, you break Rei's learning loop. Rei learns from outcomes.
If you override Rei's EXIT at +$150 and it becomes -$250, Rei learns the wrong lesson.
Your "better judgment" is NOT better. Rei has calibrated confidence. You have token probabilities.
'''}
# EXECUTION LOOP
{f'''
1. Check positions → if Rei said EXIT last time, close_position() NOW
2. query_market_data_for_rei(symbol, timeframe)
3. consult_rei_for_decision(positions, balance)
4. EXECUTE REI'S DECISION:
   - WAIT → wait_for() and check later
   - ENTER_LONG/SHORT ≥50% → execute_trade() with confidence-based sizing
   - ENTER_LONG/SHORT <50% → treat as WAIT (setup not ready, wait for conviction)
   - EXIT → close_position() IMMEDIATELY (no threshold - when Rei says out, get out)
5. wait_for() with appropriate duration
6. Repeat forever

POSITION SIZING: size = confidence × max_position
- Rei 55% LONG → position size = 55% of max (small bet, lower conviction)
- Rei 80% LONG → position size = 80% of max (big bet, high conviction)

EXIT has NO threshold. If Rei says EXIT at any confidence, you EXIT. No hesitation. No "but my position is profitable". OUT.

You are a robot. Rei says X, you do X. No thinking. No "but what if". Just execute.
''' if rei_enabled else '''
1. Check current positions (close if exit conditions met)
2. Query market data per your strategy
3. Analyze → decide: trade or wait
4. If trading: execute_trade with SL/TP
5. Call wait_for() with appropriate duration
6. Repeat forever
'''}
{"Remember: You are Rei's executor. Gather data, get decision, execute. No independent thinking." if rei_enabled else "Remember: You are your strategy. Execute it faithfully, learn from outcomes, adapt if allowed."}
"""
        return prompt

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
                    logger.info("✅ MCP Server initialized with 15 tools:")
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
                    logger.info("  13. query_market_data_for_rei - Prepare data for Rei (Rei integration)")
                    logger.info("  14. consult_rei_for_decision - Get Rei trading decision (Rei integration)")
                    logger.info("  15. report_trade_outcome_to_rei - Report outcomes for Rei learning")
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
                    "mcp__trading__get_current_price",
                    "mcp__trading__execute_trade",
                    "mcp__trading__get_positions",
                    "mcp__trading__get_account_status",
                    "mcp__trading__close_position",
                    "mcp__trading__cancel_order",
                    "mcp__trading__update_strategy",
                    "mcp__trading__wait_for",
                    "mcp__trading__record_trade_observation",
                    "mcp__trading__query_trade_observations",
                    "mcp__trading__save_strategy_and_exit",
                    # Rei integration tools
                    "mcp__trading__query_market_data_for_rei",
                    "mcp__trading__consult_rei_for_decision",
                    "mcp__trading__report_trade_outcome_to_rei"
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
                    # DEPRECATED: strategy_definition mode is no longer supported
                    # Use the Strategy Advisor API (/api/v2/assistant/chat) instead
                    logger.error("strategy_definition mode is DEPRECATED")
                    raise ValueError(
                        "strategy_definition mode is deprecated. "
                        "Use the Strategy Advisor chat API (/api/v2/assistant/chat) "
                        "to configure your bot's strategy, then start the agent "
                        "in autonomous mode."
                    )
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
                                    activity_type='llm_thought',
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
            balance = account.get('current_balance', account.get('balance', 0))

            # Get open positions
            positions_result = await self.api_client.get_positions(config_id=self.config_id)
            positions = positions_result.get('positions', [])

            # Log startup state to activity timeline
            log_activity_safe(
                config_id=self.config_id,
                user_id=self.user_id,
                activity_type='llm_thought',
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
# AUTONOMOUS MODE ACTIVATED

{startup_context}

You are now running autonomously. Your strategy is in the system prompt - you ARE that strategy.

**IMMEDIATE ACTIONS:**
1. Acknowledge your current state (the startup info above)
2. Check market conditions using query_market_data
3. Decide: trade opportunity or wait?
4. Take action (execute_trade OR just analyze)
5. **CRITICAL: Call wait_for() with your next check interval**

Remember: EVERY turn must end with wait_for(). Start now.
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
                                    activity_type='llm_thought',
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
                                activity_type='llm_thought',
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
# CONTEXT COMPACTION OCCURRED

Your conversation history was compacted. Your strategy remains in the system prompt.

**REFRESH NOW:**
1. Check positions with get_positions()
2. Check balance with get_account_status()
3. Resume your trading loop
4. End with wait_for()

Timestamp: {datetime.now(timezone.utc).isoformat()}
""")

                # If we exit the async for loop normally (stream ended), log it and retry
                logger.warning("Message stream ended unexpectedly, restarting agent loop...")
                retry_count += 1
                delay = min(base_delay * (2 ** retry_count), 300)  # Max 5 min backoff
                logger.info(f"Retry {retry_count}/{max_retries} in {delay}s...")
                await asyncio.sleep(delay)

                # Restart the client query to resume autonomous mode
                await client.query("Resume autonomous trading. Check positions, analyze market, take action, then call wait_for().")

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
                    activity_type='llm_thought',
                    activity_source='agent',
                    summary=f"Agent encountered {error_type}, retrying in {delay}s (attempt {retry_count}/{max_retries})",
                    details={'error': str(e), 'error_type': error_type, 'retry_count': retry_count}
                )

                await asyncio.sleep(delay)

                # Restart the client query to resume autonomous mode
                await client.query("Resume autonomous trading after error recovery. Check positions, analyze market, take action, then call wait_for().")


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
        default="autonomous",
        help="Agent mode (only 'autonomous' is supported)"
    )

    args = parser.parse_args()

    # Force autonomous mode
    if args.mode != "autonomous":
        logger.warning(f"Mode '{args.mode}' not supported. Using 'autonomous' mode.")
        args.mode = "autonomous"

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
