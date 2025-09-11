# TODO_V2.md - Focused Implementation Plan

**Status**: Manual testing phase - verify core functionality before automation  
**Priority**: End-to-end verification → Real-time updates → Scheduler automation


## CRITICAL - Paper Trading Foundation

- [x] Foreign key constraint issue identified (config_id exists but FK violation occurs)
- [x] Fixed service mismatch: orchestrator now uses SupabasePaperTradingService consistently
- [ ] Test complete end-to-end flow with paper trading after fix
- [x] Re-integrate 7-second position monitor from legacy API (now part of comprehensive monitoring service)  
- [ ] Confirm MarketDataAdapter connects to Hummingbot API
- [ ] Test position updates with real market data (will be tested with monitoring service)
- [ ] Verify stop loss / take profit execution (integrated into PositionMonitor)
- [ ] Confirm P&L calculations are accurate (part of MetricsCalculator)

## HIGH - End-to-End Flow Verification

- [x] Test extraction phase: market data fetching and indicators (working - all 7 timeframes)
- [x] Test decision phase: AI reasoning and trade intent generation (working - decision saved)
- [x] Test trading phase: paper trade execution and database updates (working - service mismatch fixed)
- [x] Verify WebSocket state transitions during execution phases (working - bot_status messages)
- [ ] Confirm database updates (positions, trades, accounts) (enhanced by monitoring service)


## CRITICAL - LLM Provider System (V2 Gap)

- [ ] Fix V2 decision engine LLM provider selection (currently hard-coded to OpenAI)
- [ ] Restore LLM provider factory from legacy (DeepSeek, OpenAI, Anthropic providers)
- [ ] Implement user LLM preference from config_data.llm_config
- [ ] Add subscription tier-based LLM routing:
  - [ ] Free users → DeepSeek (our API key from .env)
  - [ ] Paid users → User choice (their vault credentials OR our API keys)
- [ ] Integrate Supabase vault credential retrieval for user's own API keys
- [ ] Add proper model parameter handling (deepseek-reasoner, gpt-4o-mini, etc.)
- [ ] Test LLM provider switching and API key resolution

## HIGH - Comprehensive Monitoring Service

- [ ] Create core/monitoring/service.py - unified monitoring service
- [ ] Implement PositionMonitor (7-second intervals):
  - [ ] Update all open position prices via market data
  - [ ] Calculate unrealized P&L for all positions
  - [ ] Trigger stop loss/take profit execution
  - [ ] Broadcast position_update WebSocket messages
- [ ] Implement MetricsCalculator (30-second intervals):
  - [ ] Calculate real-time account balances and performance
  - [ ] Broadcast metrics_update WebSocket messages
- [ ] Integrate monitoring service into ggbot.py lifespan
- [ ] Extend WebSocketManager to handle multiple message types:
  - [ ] position_update, metrics_update, trade_executed, decision_made
  - [ ] Keep existing bot_status messages unchanged
- [ ] Add position price update method to SupabasePaperTradingService
- [ ] Test complete monitoring service with live data
- [ ] Verify frontend receives all real-time updates

## BACKEND - API & Database

- [ ] Audit database schema vs current implementation (paper_accounts, paper_trades)
- [ ] Test all dashboard API endpoints with real data
- [ ] Verify user isolation in paper trading system
- [ ] Add proper error handling throughout paper trading service
- [ ] Confirm Supabase vs PostgreSQL compatibility

## FRONTEND - Dashboard Issues

- [ ] Add Recharts performance charts to PerformancePanel
- [ ] Remove hard-coded bot ID from FloatingActionButtons
- [ ] Add error boundaries around dashboard panels
- [ ] Test virtual scrolling for >10 bots scenario
- [ ] Fix any remaining hard-coded values or demo data

## SCHEDULER - After Manual Testing Works

- [ ] Re-enable scheduler once manual testing is solid
- [ ] Verify reconciliation restores active bots on startup
- [ ] Test scheduler with multiple bots and timeframes
- [ ] Confirm job persistence across restarts
- [ ] Add admin controls for scheduler management

## INTEGRATION - ggShot & Production

- [ ] Verify ggShot signal processing pipeline
- [ ] Test signal_validation mode vs autonomous_trading
- [ ] Confirm premium access controls for ggShot
- [ ] Update Telegram integration for V2 orchestrator
- [ ] Test multi-user isolation and data security

## TESTING & VALIDATION

- [ ] Create comprehensive end-to-end test suite
- [ ] Test error scenarios and recovery mechanisms
- [ ] Validate performance under load (multiple bots)
- [ ] Cross-browser compatibility testing
- [ ] Mobile responsive design implementation

## CODE REFACTORING & CLEANUP

- [ ] Refactor GGBotConfig monolithic component into smaller components
  - [ ] Split into ExtractionConfig, DecisionConfig, TradingConfig components
  - [ ] Extract form state management into custom hooks
  - [ ] Separate API merge logic from UI components
  - [ ] Create reusable ConfigSection wrapper component
  - [ ] Move modal and review summary to separate components
- [ ] Move delete button from FloatingActionButtons into GGBotConfig (safety improvement)
- [ ] Clean up legacy code references throughout codebase
- [ ] Remove unused imports and dead code from V1 transition

## DEPLOYMENT READINESS

- [ ] Update documentation to reflect current implementation
- [ ] Set up proper monitoring and alerting
- [ ] Create deployment runbook
- [ ] Plan user migration strategy

---

## Current Focus: Multi-Timeframe Extraction Issue

**Status**: Core pipeline complete ✅ End-to-end flow working ✅ Next: Real-time monitoring

**Issues Resolved**:
- ✅ Database persistence (fixed - added conn.commit())
- ✅ Decision retrieval API (fixed - added RealDictCursor) 
- ✅ Multi-timeframe extraction (fixed - all 7 timeframes now processing)
- ✅ Paper trading foreign key constraint (fixed - service mismatch resolved)
- ✅ Position indexing error (fixed - added RealDictCursor to get_bot_positions)

**Core Pipeline Verified**: 
- ✅ Click ⚡ → see extraction logs for ALL 7 timeframes → decision gets multi-timeframe data → paper trade executes → database updated
- ✅ All phases complete without errors
- ✅ Multi-timeframe market data flows through the entire system

**Next Focus**: Build comprehensive monitoring service for real-time position updates and dashboard feeds.