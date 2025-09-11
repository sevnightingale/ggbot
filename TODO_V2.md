# TODO_V2.md - Focused Implementation Plan

**Status**: Manual testing phase - verify core functionality before automation  
**Priority**: End-to-end verification → Real-time updates → Scheduler automation

## IMMEDIATE - Manual Testing Setup

- [ ] Add manual trigger button (⚡) to FloatingActionButtons  
- [ ] Disable scheduler temporarily for manual testing
- [ ] Re-integrate 7-second position monitor from legacy API
- [ ] Test manual orchestrator flow: click ⚡ → watch logs → verify database

## CRITICAL - Paper Trading Foundation

- [ ] Verify paper trading service is working (PaperTradingService vs SupabasePaperTradingService)
- [ ] Confirm MarketDataAdapter connects to Hummingbot API
- [ ] Test position updates with real market data
- [ ] Verify stop loss / take profit execution
- [ ] Confirm P&L calculations are accurate

## HIGH - End-to-End Flow Verification

- [ ] Test extraction phase: market data fetching and indicators
- [ ] Test decision phase: AI reasoning and trade intent generation  
- [ ] Test trading phase: paper trade execution and database updates
- [ ] Verify WebSocket state transitions during execution phases
- [ ] Confirm database updates (positions, trades, accounts)

## MEDIUM - Real-Time Updates

- [ ] Fix WebSocket state broadcasting during orchestrator execution
- [ ] Add debug logging to WebSocket connections and broadcasts
- [ ] Verify frontend receives state updates during bot runs
- [ ] Test position updates reflecting in dashboard UI
- [ ] Confirm P&L updates in real-time

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

## Current Focus: Manual Testing Phase

**Goal**: Verify the core ggbot process works end-to-end before worrying about automation, real-time updates, or polish features.

**Success Criteria**: 
- Click ⚡ → see extraction logs → see decision logs → see paper trade execute → see database update → see P&L change
- All phases complete without errors
- Real market data flows through the entire system
- WebSocket states update in UI during execution

**Next Step**: Add manual trigger button to start debugging the core flow.