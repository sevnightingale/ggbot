# TODO.md - ggbots Implementation Plan

**Status**: Core V2 pipeline operational, WebSocket monitoring complete, ready for ggShot integration and dashboard enhancements

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

## 🔧 **HIGH PRIORITY - Backend API Gaps** 

**Timeline**: 1-2 days - Required for complete dashboard functionality

- [ ] **Fix API endpoint implementations**
  - [ ] `GET /api/v2/bot/{id}/metrics` - Add paper_accounts database query
  - [ ] `GET /api/v2/bot/{id}/positions` - Add paper_trades open positions query  
  - [ ] `GET /api/v2/bot/{id}/trades` - Add trade history query
  - [ ] `GET /api/v2/scheduler/status` - Fix response format (`jobs` → `active_jobs`)

- [ ] **Test API endpoints with real data**
  - [ ] Verify metrics endpoint returns proper account summaries
  - [ ] Confirm positions endpoint shows live P&L data
  - [ ] Test trade history with pagination support
  - [ ] Validate user isolation across all endpoints

## 🎨 **HIGH PRIORITY - Dashboard Enhancement**

**Timeline**: 3-5 days - Restore dashboard sophistication from old version

- [ ] **Restore rich position display**
  - [ ] 7-column position table (P&L, Symbol, Size, Dir, Entry, Price, Time)
  - [ ] Expandable AI reasoning with confidence scores
  - [ ] Show leverage, stop loss, take profit levels
  - [ ] Display time in trade and position details

- [ ] **Implement performance charts**
  - [ ] Add Recharts integration to PerformancePanel
  - [ ] Create cumulative P&L chart from trade history
  - [ ] Add account balance over time visualization
  - [ ] Show trade distribution and win/loss ratios

- [ ] **Restore decision intelligence**
  - [ ] Decision detail modal with full reasoning
  - [ ] Market data context display
  - [ ] LLM prompt and parameters view
  - [ ] Confidence breakdown and signal analysis

- [ ] **Advanced metrics calculation**
  - [ ] Max drawdown calculation from balance history
  - [ ] Sharpe ratio from return series
  - [ ] Profit factor (gross profit / gross loss)
  - [ ] Win/loss streaks and trade distribution

## 🔧 **MEDIUM PRIORITY - LLM Provider System**

**Timeline**: 2-3 days - User flexibility and cost optimization

- [ ] **Fix V2 decision engine LLM provider selection**
  - [ ] Restore LLM provider factory (DeepSeek, OpenAI, Anthropic)
  - [ ] Implement user LLM preference from config_data.llm_config
  - [ ] Add subscription tier-based routing (free → DeepSeek, paid → user choice)
  - [ ] Integrate Supabase vault credential retrieval for user API keys

- [ ] **Test LLM provider switching**
  - [ ] Verify model parameter handling (deepseek-reasoner, gpt-4o-mini)
  - [ ] Test API key resolution and fallback logic
  - [ ] Validate decision quality across different providers

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

**Week 1**: ggShot integration (1-2 days) + Backend APIs (1-2 days) + Dashboard enhancement start  
**Week 2**: Dashboard enhancement completion + LLM provider system  
**Week 3**: Frontend polish + Testing and validation  
**Week 4+**: Mobile responsive design (as needed)

**Focus**: Get ggShot revenue stream operational, then enhance dashboard to match old sophistication level