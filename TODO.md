# TODO.md - ggbots Implementation Plan

**Status**: ✅ **Core V2 pipeline fully operational!** - Scheduler working, APScheduler executing trades, SSE streaming, dashboard functional. Ready for production polish and ggShot integration.

## 🚨 **HIGHEST PRIORITY - ggShot Signal Integration**

**Timeline**: 1-2 days - Critical for production revenue stream

- [ ] **Re-integrate ggShot filter service** 
  - [ ] Restore `signals/listener_service.py` and `signals/publishing_service.py` 
  - [ ] Update PM2 configuration to start signal services
  - [ ] Test signal filtering pipeline with live ggShot data
  - [ ] Verify premium user gating through subscription system

- [ ] **Enable signal validation mode**
  - [ ] Test signal_validation vs autonomous_trading config modes
  - [ ] Verify V2 orchestrator processes ggShot signals correctly
  - [ ] Test decision engine with signal validation prompts
  - [ ] Confirm Telegram publishing integration works

- [ ] **Production signal pipeline testing**
  - [ ] Test end-to-end: ggShot signal → filter → decision → Telegram publish
  - [ ] Verify multi-user signal isolation and premium access
  - [ ] Test signal processing performance under load
  - [ ] Monitor signal latency and accuracy

## 🚨 **CRITICAL BUGS - ggbot.py Production Blockers**

**Timeline**: IMMEDIATE - These will crash production usage

- [ ] **Fix NameError in trading path** (BLOCKER)
  - [ ] Import `get_db_connection` in `_run_trading_v2` function
  - [ ] Test position closing functionality doesn't crash

- [ ] **Fix broken `/api/v2/bot/{config_id}/trades` endpoint** (BLOCKER)
  - [ ] Use `psycopg2.extras.RealDictCursor` instead of default tuple cursor
  - [ ] Test trades endpoint returns proper data structure

- [ ] **Fix extraction data not passed to decision engine** (BLOCKER)
  - [ ] Pass `extraction_result` into `DecisionEngineV2.make_decision()`
  - [ ] Update decision engine signature to accept extraction data
  - [ ] Test that decisions use real market data context

## 🔧 **HIGH PRIORITY - ggbot.py Production Fixes**

**Timeline**: 1 day - Must fix before production deployment

- [ ] **Fix scheduler state checks**
  - [ ] Replace `scheduler.running` with `scheduler.state == STATE_RUNNING`
  - [ ] Import `from apscheduler.schedulers.base import STATE_RUNNING`

- [ ] **Fix hard-coded log path**
  - [ ] Use `LOG_PATH = os.getenv("GGBOT_LOG_PATH", "/var/log/ggbot/orchestrator.log")`
  - [ ] Ensure log directory exists before logging

- [ ] **Fix Telethon session coupling**
  - [ ] Point session files to env-driven writable directory
  - [ ] Validate `TG_API_ID/HASH` on boot and degrade gracefully

- [ ] **Remove artificial sleeps from hot path**
  - [ ] Remove `await asyncio.sleep(7)` and `await asyncio.sleep(3)` from orchestrator
  - [ ] Or gate behind feature flag for UI demo mode

## 🔧 **HIGH PRIORITY - Frontend Decision Display**

**Timeline**: 1 day - Decision updates not showing in carousel

- [ ] **Fix recent decisions not updating**
  - [ ] Debug why second decision (position management) doesn't appear in carousel
  - [ ] Ensure SSE stream includes latest decisions
  - [ ] Test decision display updates in real-time

- [ ] **Fix signal-validation SSE parity**
  - [ ] Ensure signal-validation shows all phases: extracting → deciding → trading → completed
  - [ ] Keep phases consistent across all modes

## 🎨 **HIGH PRIORITY - UI Polish & Configuration**

**Timeline**: 1 day - Fix color scheme and configuration issues

- [ ] **Fix color system and font readability**
  - [ ] Fix unreadable text in active positions section (light mode)
  - [ ] Add proper profit/loss color scheme (green for profit, red for loss)
  - [ ] Ensure all text has proper contrast in both light and dark modes
  - [ ] Polish font colors across all dashboard components

- [ ] **Verify Stop Loss / Take Profit functionality**
  - [ ] Check if SL/TP is being read from configuration properly
  - [ ] Verify trade monitoring triggers TP/SL execution
  - [ ] Test automated position closing at profit/loss targets

- [ ] **Fix default configuration timeframes**
  - [ ] Ensure all 7 timeframes (5m, 15m, 30m, 1h, 4h, 1d, 1w) are added to default config_data
  - [ ] Update configuration templates to include complete timeframe set
  - [ ] Test multi-timeframe extraction works with all timeframes

- [ ] **Improve user messaging clarity**
  - [ ] Change 'next run...' to 'waiting for next candle close...' in frontend
  - [ ] Make it clear why bot doesn't trigger immediately after activation
  - [ ] Update status messages to be more user-friendly

## 🔧 **MEDIUM PRIORITY - Backend Polish**

**Timeline**: 1-2 days - Code quality and robustness

- [ ] **Action mapping defensiveness**
  - [ ] Log unknown `decision_result["action"]` values
  - [ ] Include action string and decision_id in metrics for debugging

- [ ] **Type accuracy for signal_data**
  - [ ] Replace `Dict` annotation with proper `TypedDict`/`dataclass`
  - [ ] Fix `.symbol` access on dict objects

- [ ] **Error taxonomy improvement**
  - [ ] Replace broad `except Exception` with specific DB/Redis/Telegram exceptions
  - [ ] Add circuit breaker for Redis idempotency failures

- [ ] **Import hygiene**
  - [ ] Remove unused imports (`uuid`, `BackgroundTasks`, `JSONResponse`)
  - [ ] Run `ruff` + `black` for code formatting

## ✅ **COMPLETED - Dashboard Enhancement**

**Status**: DONE - Dashboard sophistication restored and working

- [x] **Rich position display** - 7-column table with P&L, expandable AI reasoning
- [x] **Performance charts** - Recharts integration with cumulative P&L and balance visualization
- [x] **Decision intelligence** - Detail modals with full reasoning and market context
- [x] **Advanced metrics** - Max drawdown, Sharpe ratio, profit factor calculations
- [x] **Light/Dark theme system** - CSS variable swapping with neumorphic design

## ✅ **COMPLETED - LLM Provider System**

**Status**: DONE - LLM provider switching implemented and working

- [x] **V2 decision engine LLM provider selection** - Factory pattern with DeepSeek, OpenAI, Anthropic
- [x] **User LLM preferences** - Config-driven provider selection with subscription tiers
- [x] **API key resolution** - Supabase vault integration for user credentials
- [x] **Provider testing** - Model parameter handling and fallback logic verified

## 🔧 **MEDIUM PRIORITY - Frontend Polish**

**Timeline**: 2-3 days - UX improvements and error handling

- [ ] **Error boundaries and resilience**
  - [ ] Add error boundaries around dashboard panels
  - [ ] Implement graceful API failure handling
  - [ ] Create retry mechanisms for recoverable errors
  - [ ] Add fallback UI for component failures

- [ ] **Component improvements**
  - [ ] Remove hard-coded bot ID from FloatingActionButtons
  - [ ] Add virtual scrolling for >10 bots scenario
  - [ ] Fix any remaining hard-coded values or demo data
  - [ ] Optimize performance for large bot lists

## 📱 **LOW PRIORITY - Mobile Responsive Design**

**Timeline**: 1-2 weeks - Complete mobile experience

- [ ] **Mobile layout architecture**
  - [ ] Transform three-column desktop to single column mobile
  - [ ] Implement 70%-width slide-in drawers
  - [ ] Create bottom tab system for drawer triggers
  - [ ] Add touch gestures for carousel navigation

- [ ] **Mobile-specific adaptations**
  - [ ] Optimize components for narrow screen widths
  - [ ] Touch-friendly interaction zones
  - [ ] Performance optimization for mobile devices

## 🔧 **ONGOING - System Maintenance**

- [ ] **Config data integrity**
  - [ ] Investigate frontend config save process issues
  - [ ] Fix decision data saving to database
  - [ ] Test complete config save/load cycle

- [ ] **Testing and validation**
  - [ ] Create comprehensive end-to-end test suite
  - [ ] Validate performance under load (multiple bots)
  - [ ] Cross-browser compatibility testing

- [ ] **Deployment readiness**
  - [ ] Update documentation to reflect current implementation
  - [ ] Set up proper monitoring and alerting
  - [ ] Create deployment runbook

---

## 🎯 **UPDATED COMPLETION TIMELINE**

**IMMEDIATE (Today)**: Fix 3 critical production blockers in ggbot.py (NameError, trades endpoint, extraction data)
**Day 1-2**: ggShot signal integration + Fix decision display issue + Production polish
**Day 3-4**: Mobile responsive design improvements
**Week 2+**: Advanced features and optimizations

**Current Focus**: Fix production blockers → Enable ggShot revenue stream → Polish remaining issues