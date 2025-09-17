# TODO.md - ggbots Implementation Plan

**Status**: ✅ **Core V2 pipeline operational with ggShot integration!** - Scheduler working, signal flow fixed, multi-timeframe extraction working. Focus now on testing and polish.

## 🚨 **HIGHEST PRIORITY - Frontend Polish & Landing Page**

**Timeline**: 2 days - Complete frontend modernization

- [ ] **Polish and deploy new landing page**
  - [ ] Complete /new-landing page polish and final touches
  - [ ] Archive existing /landing page to /legacy-landing
  - [ ] Rename /new-landing to /landing for main ggbots.ai URL
  - [ ] Update routing and middleware for new landing page
  - [ ] Test deployment on Vercel with new routing

- [ ] **Remove legacy dashboard and clean up frontend directory**
  - [ ] Archive /dashboard directory (legacy WebSocket-based dashboard)
  - [ ] Remove botStore.ts and related WebSocket complexity
  - [ ] Clean up unused components and dependencies
  - [ ] Update navigation and routing to use /forge as primary app
  - [ ] Simplify directory structure to focus on /landing and /forge

## 🔧 **HIGH PRIORITY - ggShot Signal Polish**

**Timeline**: 1 day - Fix remaining signal integration issues

- [ ] **Fix manual trigger signal context**
  - [ ] Fix "Run Once" button to include signal context in decision prompts
  - [ ] Test manual signal validation with proper ggShot signal data

- [ ] **Production signal pipeline testing**
  - [ ] Test end-to-end: ggShot signal → filter → decision → Telegram publish
  - [ ] Verify multi-user signal isolation and premium access
  - [ ] Test signal processing performance under load
  - [ ] Monitor signal latency and accuracy

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

- [ ] **Review decimal precision for crypto pricing**
  - [ ] Audit all price display components across frontend (Forge positions table, metrics, etc.)
  - [ ] Ensure backend API returns appropriate decimal precision for small-cap cryptos
  - [ ] Update price formatting to handle micro-prices (e.g., $0.000001234 for meme coins)
  - [ ] Verify extraction/decision/trading systems handle high-precision decimals correctly
  - [ ] Test with various crypto price ranges (BTC ~$100k vs SHIB ~$0.000024)
  - [ ] Implement dynamic decimal places based on price magnitude

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

## 🧪 **COMPREHENSIVE TESTING SUITES**

**Timeline**: 1-2 weeks - Validate system reliability and coverage

- [ ] **Symbol Coverage Testing**
  - [ ] Test all 140+ crypto symbols for KuCoin data availability
  - [ ] Identify symbols missing on KuCoin exchange
  - [ ] Document symbol mapping issues and fallback strategies
  - [ ] Test symbol extraction success rates across all timeframes
  - [ ] Create symbol blacklist for unsupported pairs

- [ ] **Technical Analysis Testing**
  - [ ] Test all 21 indicator preprocessors individually
  - [ ] Validate indicator calculations against reference implementations
  - [ ] Test multi-timeframe indicator consistency
  - [ ] Performance benchmarking for indicator calculations
  - [ ] Edge case testing (low volume, missing data, extreme values)

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