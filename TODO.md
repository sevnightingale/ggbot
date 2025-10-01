# TODO.md - ggbots Implementation Plan

**Status**: ✅ **Core V2 + Monetization Complete!** - Scheduler, signal flow, multi-timeframe extraction, SSE updates all working. Stripe subscription system fully integrated ($29/mo Pro Plan with 14-day trial). Trading validation implemented. Focus now on remaining trading features and mobile polish.

## 🔧 **HIGH PRIORITY - Trading System Completeness**

**Timeline**: 2-3 days - Core trading functionality verification and enhancement

- [x] **Manual Position Management** ✅ COMPLETE
  - [x] Add "Close Position" button to active trades in PositionsTable
  - [x] Implement API endpoint: `POST /api/v2/bot/{config_id}/positions/{trade_id}/close`
  - [x] Update paper trading service to handle manual position closure
  - [x] Test manual close functionality with real-time SSE updates

- [ ] **Stop Loss / Take Profit Verification**
  - [ ] Check if SL/TP values are being read from configuration properly
  - [ ] Verify trade monitoring triggers TP/SL execution automatically
  - [ ] Test automated position closing at profit/loss targets
  - [ ] Ensure SL/TP levels display correctly in positions table

- [x] **Trading Settings Validation** ✅ COMPLETE
  - [x] Frontend validation with real-time error/warning feedback
  - [x] Leverage (1-100, warning >20x), Stop Loss (1-50%), Take Profit (1-500%)
  - [x] Position sizing (0.1-100%, warning >50%), Max positions (1-50, warning >10)
  - [x] Red borders for errors (blocking), yellow borders for warnings (non-blocking)
  - [ ] Test position sizing calculations match configuration
  - [ ] Validate risk management parameters are enforced
  - [ ] Implement open position limits per user/bot configuration

- [x] **Volume Analysis Fixes** ✅ COMPLETE
  - [x] Debug volume analysis broken in technical indicators
  - [x] Fix volume data not appearing in decision prompts
  - [x] Test volume-based signal validation
  - [x] Verify volume metrics in market analysis formatting

## 🚀 **HIGH PRIORITY - Self-Service Account Reset Feature**

**Timeline**: 1-2 days - User-controlled paper account resets
**Status**: Default bot cleanup complete (92 bots deactivated, 83 users affected)

- [x] **Default Bot Cleanup** ✅ COMPLETE (2025-10-01)
  - [x] Deactivated 92 active default strategy bots (pattern: "RSI 1hr below 50%enter long%")
  - [x] Verified 22 custom strategy bots remain active
  - [x] No forced account resets - V2.0 leverage fixes work with existing accounts

- [ ] **Reset Trading Account Button**
  - [ ] Add "Reset Account" option to bot 3-dot dropdown menu (alongside Rename/Delete)
  - [ ] Implement backend endpoint: `POST /api/v2/bot/{config_id}/reset-account`
  - [ ] Reset logic: Close all open positions, reset balance to $10k, clear trade history, preserve bot config
  - [ ] Add confirmation modal: "This will close all positions and reset your account to $10,000. This cannot be undone."
  - [ ] Test reset functionality with active positions and historical trades
  - [ ] Add success toast notification after reset completes

- [ ] **User Communication**
  - [ ] Email encouraging users to try reset feature for clean V2.0 accounting
  - [ ] Optional: Add banner promoting account reset for fresh start with leverage fixes
  - [ ] Monitor user feedback channels (Telegram community, support tickets)

## 🔧 **HIGH PRIORITY - User Settings & API Key Management**

**Timeline**: 1-2 days - Critical for user onboarding and self-service

- [ ] **Complete User Settings Page**
  - [ ] Finish API key management interface for LLM credentials
  - [ ] Add secure credential storage using Supabase Vault
  - [ ] Implement credential validation and testing functionality
  - [ ] Add interface for managing multiple API keys per provider

- [ ] **LLM Provider Management**
  - [ ] Support OpenAI, DeepSeek, Anwhythropic, and XAI credential management
  - [ ] Add credential naming and organization features
  - [ ] Implement credential usage tracking and validation
  - [ ] Test credential encryption/decryption flow

- [ ] **Subscription & Profile Management**
  - [x] Display current subscription tier and status (Pro/Free badges in UserProfile)
  - [x] Add subscription upgrade interface (UpgradeModal with Stripe Checkout)
  - [x] Add subscription management interface (Stripe Customer Portal)
  - [ ] Implement downgrade workflow (cancellation flow)
  - [ ] Implement user profile settings (Telegram integration, preferences)
  - [ ] Add account settings and preferences management

## 🎨 **HIGH PRIORITY - User Experience Polish**

**Timeline**: 1-2 days - Polish user-facing features and messaging

- [ ] **Improve Status Messaging**
  - [ ] Change 'next run...' to 'waiting for next candle close...' in frontend
  - [ ] Update countdown messages to be more user-friendly
  - [ ] Add explanatory tooltips for bot status states
  - [ ] Improve activation/deactivation feedback messages

- [ ] **Optional Market Data Display**
  - [ ] Consider adding expandable market analysis panel to positions
  - [ ] Implement "Show Analysis" toggle for power users
  - [ ] Add hover tooltips showing key indicators that influenced decisions
  - [ ] Design market context drawer/modal for detailed technical analysis

- [ ] **Trade History Modal**
  - [ ] Add clickable "Total Trades" metric in MetricsBar
  - [ ] Implement full-screen modal with minimalist design
  - [ ] Display last 50 closed trades: Symbol, Side, P&L, Close Reason, Timestamp
  - [ ] Color-code by win/loss for quick scanning
  - [ ] Show summary stats at top: win count, loss count, win rate
  - [ ] Optional: Click individual trade to expand details (entry/exit prices, duration, confidence)

## 🚀 **MAJOR PROJECT - Market Data Expansion**

**Timeline**: 2-4 weeks - Major platform enhancement for competitive advantage

- [ ] **Market Research & Requirements**
  - [ ] Survey users for most desired data sources (sentiment, on-chain, news, etc.)
  - [ ] Research integration complexity and costs for top requested sources
  - [ ] Define data source priority roadmap based on user demand vs effort
  - [ ] Document technical requirements for new data source integrations

- [ ] **Data Source Integration Development**
  - [ ] Implement top-priority data sources (sentiment analysis, on-chain metrics, etc.)
  - [ ] Build robust data ingestion pipelines with error handling
  - [ ] Create preprocessing systems for new data types
  - [ ] Test data quality and reliability across different market conditions

- [ ] **Flagship ggbot Development**
  - [ ] Design and implement flagship bot using expanded data sources
  - [ ] Test flagship bot with comprehensive market data inputs
  - [ ] Optimize flagship bot performance and decision accuracy
  - [ ] Deploy flagship bot as premium showcase feature

- [ ] **Platform Integration**
  - [ ] Add new data sources to configuration UI
  - [ ] Implement premium gating for advanced data sources
  - [ ] Update decision prompts to incorporate new data types
  - [ ] Test multi-data-source decision making workflows

## 🔧 **MEDIUM PRIORITY - System Robustness**

**Timeline**: 2-3 days - Code quality, error handling, and reliability

- [ ] **Database Schema Optimization**
  - [ ] Remove unused `market_data` column from decisions table schema
  - [ ] Implement market data parsing utilities for future analysis needs
  - [ ] Add database indexes for performance optimization
  - [ ] Clean up any remaining schema inconsistencies

- [ ] **Error Handling & Resilience**
  - [ ] Add comprehensive error boundaries to frontend components
  - [ ] Implement graceful API failure handling with retries
  - [ ] Add circuit breakers for external service failures
  - [ ] Improve logging and error taxonomy (replace broad exceptions)

- [ ] **Node.js & Dependencies**
  - [ ] Plan upgrade from Node.js 18 to Node.js 20+ (removes Supabase warnings)
  - [ ] Update dependencies to latest compatible versions
  - [ ] Test compatibility after Node upgrade
  - [ ] Update deployment configurations for new Node version

- [ ] **Code Quality Improvements**
  - [ ] Run `ruff` + `black` for Python code formatting
  - [ ] Remove unused imports and clean up import hygiene
  - [ ] Add proper TypeScript types for signal_data structures
  - [ ] Implement defensive action mapping with unknown value logging

## 📱 **MEDIUM PRIORITY - Mobile & Frontend Polish**

**Timeline**: 2-3 days - Complete mobile experience and component improvements

- [ ] **Mobile Responsive Design**
  - [ ] Transform three-column desktop layout to single column mobile
  - [ ] Implement 70%-width slide-in drawers for navigation
  - [ ] Create bottom tab system for drawer triggers
  - [ ] Add touch gestures for carousel navigation
  - [ ] Optimize components for narrow screen widths and touch interaction

- [ ] **Frontend Component Polish**
  - [ ] Remove any remaining hard-coded values or demo data
  - [ ] Add virtual scrolling for scenarios with >10 bots
  - [ ] Optimize performance for large bot lists
  - [ ] Polish loading states and skeleton components
  - [ ] Ensure all components handle edge cases gracefully

## 🧪 **LOW PRIORITY - Testing & Validation**

**Timeline**: 1-2 weeks - Comprehensive system validation

- [ ] **Symbol Coverage Testing**
  - [ ] Test all 140+ crypto symbols for KuCoin data availability
  - [ ] Verify Hummingbot integration works for all supported pairs
  - [ ] Test symbol extraction success rates across all timeframes
  - [ ] Create symbol blacklist for unsupported pairs
  - [ ] Full end-to-end pipeline testing: extraction → decision → trading

- [ ] **Technical Analysis Validation**
  - [ ] Test all 21 indicator preprocessors individually
  - [ ] Validate indicator calculations against reference implementations
  - [ ] Test multi-timeframe indicator consistency and performance
  - [ ] Edge case testing (low volume, missing data, extreme price movements)

- [ ] **Load Testing & Performance**
  - [ ] Test system performance with multiple concurrent bots
  - [ ] Validate database performance under load
  - [ ] Test SSE stream performance with many connected clients
  - [ ] Cross-browser compatibility testing

- [ ] **Security & Reliability Testing**
  - [ ] Audit API endpoints for security vulnerabilities
  - [ ] Test rate limiting and authentication flows
  - [ ] Validate data isolation between users
  - [ ] Test backup and recovery procedures

---

## 🎯 **COMPLETION TIMELINE**

**~~IMMEDIATE (Days 1-3)~~**: ✅ **COMPLETE** - Monetization & Business Model (Stripe integration, paid tiers, premium gating)
**Days 1-2 (NEW IMMEDIATE)**: User Settings & API Key Management (critical for user onboarding)
**Days 3-4**: Trading system completeness (manual close, SL/TP verification, volume fixes)
**Days 5-6**: User experience polish (status messaging, optional market data display)
**Week 2**: System robustness (error handling, Node.js upgrade, code quality)
**Weeks 3-6**: Market Data Expansion (major project - user research → integration → flagship bot)
**Week 7+**: Mobile responsive design and comprehensive testing

**Current Focus**: ✅ Monetization DONE → User onboarding (settings) → Trading completeness → Major platform enhancement (market data expansion)

## ✅ **RECENTLY COMPLETED**

### **2025-10-01: Stripe Monetization + Trading Validation**
- ✅ **Complete Stripe Integration**: Pro Plan ($29/mo, $279/year) with 14-day free trial
- ✅ **Backend Stripe APIs**: Checkout sessions, webhook handlers (4 events), billing portal, user profile endpoint
- ✅ **Frontend Upgrade Flow**: UpgradeModal with monthly/annual toggle, PermissionGate integration
- ✅ **Subscription UI**: Pro/Free badges in UserProfile, upgrade/billing buttons, landing page pricing update
- ✅ **Early Adopter Promo**: EARLY50 coupon (50% off for 6 months), configured in Stripe
- ✅ **Trading Settings Validation**: Real-time error/warning feedback for 6 critical fields
- ✅ **Validation UX**: Red borders (errors block save), yellow borders (warnings allow save), inline messages with icons
- ✅ **Validated Fields**: Leverage, Stop Loss, Take Profit, Position Size (% and USD), Max Positions

### **Previous Completions**
- ✅ Core V2 pipeline operational (scheduler, signal flow, multi-timeframe extraction)
- ✅ Frontend SSE real-time updates working
- ✅ Decision carousel display fixed and working
- ✅ Frontend slide animations polished (removed ugly pulse/flash effects)
- ✅ Database market_data column issue resolved
- ✅ Vercel Analytics integration added
- ✅ ggShot signal integration working
- ✅ Multi-user isolation and premium access
- ✅ Profit/loss color schemes implemented
- ✅ Configuration save/load cycle working
- ✅ Paper trading accounts and metrics display

## 🎯 **SUCCESS METRICS**

**Technical Completeness**: All core trading features working (manual close, SL/TP, leverage)
**User Experience**: Intuitive interface with clear status messaging and settings management
**System Reliability**: Error handling, monitoring, and robust performance under load
**Mobile Ready**: Responsive design supporting mobile trading workflows
**Production Ready**: Comprehensive testing, monitoring, and deployment automation