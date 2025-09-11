# TODO_V2.md - Focused Implementation Plan

**Status**: Core pipeline operational ✅ - Backend monitoring COMPLETE ✅ - Frontend WebSocket integration COMPLETE ✅  
**Priority**: Restart frontend server → Test real-time updates → LLM provider system → Scheduler automation


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
- [x] Verify WebSocket state transitions during execution phases (working - complete bot_status flow)
- [x] Test complete manual trigger flow (working - extraction → decision → trading → completed)
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

## HIGH - Full WebSocket Monitoring Service (Backend Complete ✅)

**WebSocket Infrastructure Verified ✅ - Backend monitoring service COMPLETE ✅**

- [x] Fix manual trigger to broadcast bot_status WebSocket messages
- [x] Create core/monitoring/service.py - unified monitoring service ✅
- [x] Implement PositionMonitor (7-second intervals) ✅:
  - [x] Update all open position prices via market data ✅
  - [x] Calculate unrealized P&L for all positions ✅
  - [x] Trigger stop loss/take profit execution ✅
  - [x] Broadcast position_update WebSocket messages ✅
- [x] Implement metrics and scheduler monitoring ✅:
  - [x] scheduler_status → WebSocket every 7s ✅
  - [x] bot_metrics → WebSocket every 7s ✅
- [x] Extend WebSocketManager to handle multiple message types ✅:
  - [x] position_update, metrics_update, scheduler_update ✅
  - [x] Keep existing bot_status messages unchanged ✅
- [x] Integrate monitoring service into ggbot.py lifespan ✅
- [x] Set up separate logging for monitoring service ✅
- [x] Add decisions broadcasting to complete activity data (eliminate useBotActivity polling) ✅

## IMMEDIATE FIXES - Current Execution Issues

- [x] Add 7-second delay between extraction and decision phases for better UX
- [x] Fix datetime serialization error in decision engine (_save_position_decision_to_db)
- [x] Fix Pydantic numpy.int64 serialization error in OrchestrationResult
- [x] Fix missing 'trading' and 'completed' WebSocket messages for complete UI state flow
- [x] Fix 504 Gateway Timeout errors preventing manual trigger execution

## IMMEDIATE - Complete WebSocket Integration Testing

**Backend broadcasting ALL data ✅ - Frontend handlers implemented ✅ - Testing pending**

### Backend - Decisions Broadcasting COMPLETE ✅
- [x] Add `_get_recent_decisions()` method to monitoring service ✅
- [x] Include decisions in metrics monitoring loop ✅
- [x] Broadcast `decisions_update` messages every 7 seconds ✅
- [x] Test decisions appear in WebSocket stream ✅

### Frontend - WebSocket Handler Integration COMPLETE ✅ 
- [x] Update frontend to handle all new WebSocket message types:
  - [x] position_update messages in botStore.ts ✅
  - [x] metrics_update messages in botStore.ts ✅
  - [x] scheduler_update messages in botStore.ts ✅
  - [x] decisions_update messages in botStore.ts ✅
- [x] Remove frontend setInterval polling hooks:
  - [x] Remove `setInterval(fetchSchedulerStatus, 30000)` from useSchedulerStatus.ts ✅
  - [x] Remove `setInterval(() => fetchActivity(botId), 30000)` from useBotActivity.ts ✅
- [x] Add new store methods to botStore.ts:
  - [x] updateBotPositions(configId, positions) ✅
  - [x] updateBotMetrics(configId, metrics) ✅
  - [x] updateSchedulerStatus(schedulerStatus) ✅
  - [x] updateBotDecisions(configId, decisions) ✅
- [x] Update hooks to read from store instead of HTTP APIs ✅

### Testing - Frontend Server Restart Required
- [ ] **RESTART FRONTEND SERVER** - Changes need to take effect
- [ ] Verify HTTP polling stops (no more `get_bot_decisions` in logs)
- [ ] Test real-time dashboard updates every 7 seconds
- [ ] Confirm position P&L updates in real-time
- [ ] Verify scheduler status updates without polling
- [ ] Test decisions appear immediately in activity panel

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
- ✅ Pydantic numpy.int64 serialization (fixed - custom serializer in OrchestrationResult)
- ✅ 504 Gateway Timeout errors (fixed - serialization now working)
- ✅ Missing WebSocket state transitions (fixed - complete extraction → decision → trading → completed flow)

**Core Pipeline Verified**: 
- ✅ Click ⚡ → see extraction logs for ALL 7 timeframes → decision gets multi-timeframe data → paper trade executes → database updated
- ✅ All phases complete without errors, full WebSocket flow working
- ✅ Multi-timeframe market data flows through the entire system
- ✅ Manual trigger fully operational with proper UI feedback

**Backend Monitoring COMPLETE**: Real-time position updates, metrics, scheduler data, AND decisions streaming via WebSocket every 7 seconds. Separate log files: `orchestrator.log` (business logic), `monitoring.log` (background tasks), `ggbot.log` (system). ✅

**Frontend WebSocket Integration COMPLETE**: All hooks updated to use store data, HTTP polling removed, WebSocket handlers implemented for all 4 message types. ✅

**Next Focus**: Restart frontend server to activate changes, then test complete real-time dashboard experience.

**Expected Result**: Once frontend restarts, `get_bot_decisions` HTTP polling will stop and dashboard will update every 7 seconds via WebSocket instead of 30-second polling.