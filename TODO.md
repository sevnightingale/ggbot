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

## 🔧 **REMAINING ggbot.py Issues**

**Timeline**: Low priority - Nice to have improvements

- [ ] **Fix Telethon session coupling**
  - [ ] Point session files to env-driven writable directory
  - [ ] Validate `TG_API_ID/HASH` on boot and degrade gracefully

## 🔧 **HIGH PRIORITY - Frontend Decision Display**

**Timeline**: 1 day - Decision updates not showing in carousel

- [ ] **Fix recent decisions not updating**
  - [ ] Debug why second decision (position management) doesn't appear in carousel
  - [ ] Ensure SSE stream includes latest decisions
  - [ ] Test decision display updates in real-time


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

## 🎯 **COMPLETION TIMELINE**

**IMMEDIATE**: ggShot signal integration (core ggbot.py issues resolved)
**Day 1-2**: ggShot signal integration + Fix decision display issue + Production polish
**Day 3-4**: Mobile responsive design improvements
**Week 2+**: Advanced features and optimizations

**Current Focus**: Fix production blockers → Enable ggShot revenue stream → Polish remaining issues