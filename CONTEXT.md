
● GGBot Webhook System - Detailed Implementation

  Architecture Overview

  We implemented a 3-tier autonomous webhook chain that creates a
  fully automated trading pipeline. The system uses HTTP webhooks
  for inter-service communication, enabling each module to trigger
   the next in sequence.

  Webhook Chain Flow

  🔄 Extraction Webhook → 🧠 Decision Webhook → ⚡ Trading Webhook

  1. Extraction Webhook

  Endpoint: POST /extraction/webhooks/trigger-extraction

  Purpose: Start the autonomous pipeline by extracting fresh
  market data

  Implementation Details:
  - Pre-extraction Monitoring: Calls
  setup_pre_extraction_monitoring() to refresh account state from
  exchange before extraction
  - Background Processing: Uses FastAPI BackgroundTasks to run
  extraction asynchronously
  - MCP Integration: Extracts indicators via MCP (Model Context
  Protocol) from crypto indicators server
  - Data Storage: Stores extracted indicator data in PostgreSQL
  database
  - Auto-Chaining: After successful extraction, automatically
  triggers the Decision webhook

  Key Logic:
  # 1. Setup fresh account monitoring
  monitoring_result = await
  setup_pre_extraction_monitoring(user_id, config_id)

  # 2. Run extraction in background
  background_tasks.add_task(run_extraction_task, extraction_id,
  user_id, symbols, timeframes, config_id)

  # 3. Auto-trigger decision after completion
  if data_points > 0:
      await trigger_decision_webhook(user_id, symbols, timeframes,
   config_id)

  2. Decision Webhook

  Endpoint: POST /decision/webhooks/trigger-decision

  Purpose: Analyze market data and generate trading decisions with
   fresh account context

  Implementation Details:
  - Fresh Account Sync: Calls setup_account_monitoring() to get
  latest exchange positions before making decisions
  - Mode Detection: Automatically determines NEW_TRADE vs
  MANAGE_TRADE based on active database trades
  - LLM Integration: Uses decision engine with DeepSeek LLM to
  analyze market data and generate trading intents
  - Database Storage: Stores decisions in account_states table for
   historical tracking
  - Auto-Chaining: If decision is actionable (not "no_action"),
  automatically triggers Trading webhook

  Key Logic:
  # 1. Fresh account monitoring
  monitoring_result = await setup_account_monitoring(user_id,
  config_id)

  # 2. Auto mode detection with fresh data
  with get_db_connection() as conn:
      cur.execute("SELECT COUNT(*) FROM trades WHERE user_id = %s 
  AND config_id = %s AND trade_status = 'open'")
      active_trades = cur.fetchone()[0]
      actual_mode = "MANAGE_TRADE" if active_trades > 0 else
  "NEW_TRADE"

  # 3. Generate decision
  intent = await run_decision_process(user_id, config_id, symbol,
  timeframes)

  # 4. Auto-trigger trading if actionable
  if action not in ["no_action", "hold", "wait"]:
      await trigger_trading_webhook(user_id, intent, decision_id)

  3. Trading Webhook

  Endpoint: POST /trading/webhooks/execute-trade

  Purpose: Execute trades with proper position sizing and
  comprehensive verification

  Implementation Details:
  - Position Sizing: Implements confidence-based position sizing
  (exactly like direct API)
  - Account State Integration: Gets fresh account balance for risk
   calculations
  - Risk Management: Applies leverage, risk percentage, and
  position size limits
  - Trade Execution: Uses TradingEngine with CCXT MCP for actual
  trade execution
  - Post-Trade Verification: Comprehensive verification including
  exchange sync and audit trail validation
  - Strategy Runs Verification: Checks that strategy_runs audit
  trail was created by trading engine

  Key Logic:
  # 1. Get account state for position sizing
  account_state = await get_account_state(engine.user_id,
  exchange_name)

  # 2. Calculate position size from confidence (SAME AS DIRECT 
  API)
  standardized_balance =
  _standardize_account_balance(account_state)
  position_calc = calculate_position_from_confidence(
      confidence=confidence,
      account_balance_usd=account_balance_usd,
      default_leverage=default_leverage,
      min_position_usd=min_position_usd,
      max_position_usd=max_position_usd
  )

  # 3. Execute trade
  result = await engine.process_decision_intent(intent_data)

  # 4. Comprehensive post-trade verification
  if result.get("status") == "success":
      await asyncio.sleep(5)  # Position settlement
      verification_result = await verify_trade_execution(user_id,
  config_id)
      strategy_runs_verified = await
  verify_strategy_runs_webhook(trade_id, config_id)

  Webhook Communication Protocol

  Standard Webhook Payload:
  {
    "user_id": "00000000-0000-0000-0000-000000000001",
    "config_id": "a93de31b-9b8a-42e3-827d-c31e580f5f36",
    "symbols": ["BTC/USDT"],
    "timeframes": ["15m"]
  }

  Auto-Chaining Implementation:
  Each webhook calls the next via HTTP POST with proper timeout
  handling:
  async with httpx.AsyncClient(timeout=120.0) as client:
      response = await client.post(next_webhook_url, json=payload)

  Timing Coordination

  - 2-second delay after extraction before triggering decision
  - 1-second delay after decision before triggering trading
  - 5-second delay after trading before verification (matches
  new_trade.py)

  Verification & Audit Trail

  The system creates a complete audit trail:
  1. Extraction: Indicator data stored in market_data table
  2. Decision: Decision records stored in account_states table
  3. Trading: Strategy_runs entries created by trading engine with
   trade_id linkage
  4. Verification: Exchange position sync and trade lifecycle
  management

  Error Handling

  - Database Errors: Proper UUID handling for config_id
  - HTTP Timeouts: 120-second timeouts for webhook calls
  - Exchange Errors: Graceful fallback if monitoring fails
  - Logging: Comprehensive logging at each step for debugging

  Key Differences from Direct API

  - Autonomous: No manual intervention required between steps
  - Fresh State: Each step refreshes account state from exchange
  - Comprehensive: Includes all verification logic from
  new_trade.py test
  - Auditable: Complete trail of decisions and executions

  This webhook system enables fully autonomous trading where a
  single trigger (extraction webhook) results in complete market
  analysis, decision making, trade execution, and verification -
  all without human intervention.
