# TODO.md - ggbots Implementation Plan

## 🟡 **IN PROGRESS - Symphony.io Live Trading Integration** (Days 0-6 Complete - 2025-01-19)

**Status**: Backend & Frontend production-ready. Initial testing successful - trade queries and metrics need updates.

- [x] **Symbol System Extension**
  - [x] Extend `core/symbols/registry.py` with Symphony format support
  - [x] Add `"symphony": "BTC"` field to 100 compatible symbols
  - [x] Add `"symphony_compatible": true/false` boolean to all symbols
  - [x] Add `to_symphony()` and `from_symphony()` methods to standardizer
  - [x] Add `is_symphony_compatible()` check method

- [x] **Premium Feature Configuration** (Day 1 Complete - 2025-01-19)
  - [x] Add 'live_trading' to permissions system (`frontend/lib/permissions.tsx`)
  - [x] Implement `can_use_live_trading()` permission check in backend (`core/domain/user_profile.py`)
  - [x] Expose permission in `/api/v2/me` and `/api/v2/profile/me` endpoints
  - [x] Document permission pattern in CLAUDE.md

- [x] **Settings Modal & Account Connection** (Day 1 Complete - 2025-01-19)
  - [x] Create `SettingsModal.tsx` component with Symphony section
  - [x] Add Symphony API key input field with format validation
  - [x] Add smart account address input (with tooltip: "Used for future balance features")
  - [x] Implement connection status UI (connected/disconnected states)
  - [x] Add Settings menu item to UserProfile dropdown (top position)
  - [ ] Create Symphony connection status endpoint (Day 4 - Backend APIs)

- [x] **Database Schema Changes** (Day 2 Complete - 2025-01-19)
  - [x] Extend `user_profiles` table: Add `symphony_vault_id` and `symphony_smart_account` columns
  - [x] Extend `configurations` table: Add `symphony_agent_id` and `trading_mode` columns
  - [x] Create `live_trades` table (minimal schema: batch_id, config_id, decision_id, timestamps)
  - [x] Add idempotency constraint: `UNIQUE(decision_id)`
  - [x] Create indexes on `config_id` and open positions (2 indexes)
  - [x] Verify migration in production database

- [x] **Vault Integration** (Day 2 Complete - 2025-01-19)
  - [x] Extend `VaultManager` with `store_symphony_credential()` method
  - [x] Add `get_symphony_credential()` method for retrieving API keys
  - [x] Add `delete_symphony_credential()` method for cleanup (also disables live bots)
  - [x] Add convenience wrapper functions for Symphony credentials
  - [ ] Test vault encryption/decryption flow with Symphony credentials (Day 4 - API endpoints)

- [x] **Symphony Service Implementation** (Day 3 Complete - 2025-01-19)
  - [x] Create `trading/live/symphony_service.py` with thin wrapper class
  - [x] Implement `execute_trade_intent()` with 3-second settlement wait
  - [x] Add idempotency check before Symphony API calls (decision_id uniqueness)
  - [x] Implement symbol conversion using UniversalSymbolStandardizer
  - [x] Add `/agent/batch-open` integration with proper field mapping
  - [x] Implement `close_position()` method with `/agent/batch-close`
  - [x] Implement `get_open_positions()` with field mapping (asset→symbol, isLong→side)
  - [x] Add error handling for Symphony API rejections
  - [x] Implement weight calculation using existing position sizing logic (account_percent & confidence_based)

- [x] **Orchestrator Integration** (Day 3 Complete - 2025-01-19)
  - [x] Add Symphony service to ggbot.py imports and initialization
  - [x] Modify `_run_trading_v2()` to route based on `trading_mode`
  - [x] Implement trading router (paper vs live mode switch)
  - [x] Add position management integration for live mode (close position routing)
  - [x] Query live_trades vs paper_trades based on trading_mode

- [x] **API Endpoints** (Day 4 Complete - 2025-01-19)
  - [x] Create `POST /api/v2/symphony/setup` (store credentials with format validation)
  - [x] Create `GET /api/v2/symphony/status` (check connection status)
  - [x] Create `POST /api/v2/symphony/disconnect` (remove credentials & disable live bots)
  - [x] Create `GET /api/v2/positions/live/{config_id}` (query Symphony positions)
  - [x] Create `POST /api/v2/positions/live/{batch_id}/close` (close live position with ownership check)
  - [x] Create `POST /api/v2/config/duplicate-as-live` (duplicate paper bot with validation)

- [x] **Frontend - Duplicate as Live Flow** (Days 5-6 Complete - 2025-01-19)
  - [x] Add "Duplicate as Live" button to BotManagementMenu (paper bots only)
  - [x] Implement premium permission check with upgrade prompt
  - [x] Check Symphony connection status before allowing live bot creation
  - [x] Create DuplicateAsLiveModal with Symphony agent ID input + validation
  - [x] Add warning messaging: "Live trading uses real money"
  - [x] Implement complete wiring (page.tsx → BotRail → BotManagementMenu)
  - [x] Auto-suggest bot name: "{Original Name} (Live)"
  - [x] Disable FIXED_USD position sizing for live bots (Symphony requires %)

- [x] **Frontend - Dashboard Updates** (Days 5-6 Complete - 2025-01-19)
  - [x] Add "LIVE TRADING" badge to bot cards (replaces balance display)
  - [x] Positions already isolated per bot (no dashboard changes needed)
  - [x] Trading mode locked per config (no mixing)
  - [x] Close position routing handled in orchestrator (paper vs live)

- [x] **Testing & Validation** (Initial tests complete - 2025-01-21)
  - [x] Test Symphony account setup flow (API key + smart account)
  - [x] Test paper bot duplication to live bot
  - [x] Verify live position opening (check Symphony portal + ggbots dashboard)
  - [ ] Test manual position closing in live mode
  - [ ] Test symbol compatibility validation (100 supported symbols)
  - [ ] Test idempotency (retry on timeout doesn't create duplicate trades)
  - [ ] Test error handling (invalid API key, insufficient balance, unsupported symbol)
  - [ ] Verify live_trades table linkage (batch_id → decision_id traceability)

- [ ] **Live Trading System Polish** (Current Focus - 2025-01-21)
  - [ ] Update trade query endpoints to support live_trades table
  - [ ] Fix metrics calculations to include live trades
  - [ ] Ensure positions display correctly for live bots
  - [ ] Update dashboard stats to aggregate paper + live trades
  - [ ] Test P&L calculations with live trade data
  - [ ] Verify close reason tracking in live_trades
  - [ ] Update PositionsTable to handle live trading data format

- [ ] **Documentation**
  - [ ] Create user guide: "How to Enable Live Trading"
  - [ ] Document Symphony account setup steps
  - [ ] Document "Create Live Version" workflow
  - [ ] Add API endpoint documentation with curl examples
  - [ ] Document symbol compatibility (100 vs 141 symbols)

## 🎨 **HIGH PRIORITY - User Experience Polish**

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

### **Phase 3: Agent SDK Integration** (Week 3)

- [ ] **Tool Generation**
  - [ ] Implement ToolGenerator (auto-generate from catalogs)
  - [ ] Create tool registry for Agent SDK
  - [ ] Add tool discovery endpoint

- [ ] **MCP Server**
  - [ ] Implement MCP server with universal query tool
  - [ ] Add data type discovery
  - [ ] Test with Claude Desktop

- [ ] **Response Formatting Enhancement**
  - [ ] Enhance LLM format mode with better templates
  - [ ] Add insight extraction logic
  - [ ] Create default templates for all data types

### **Phase 4: Scale Data Sources** (Weeks 4-8)

- [ ] **Sentiment Analysis** (Week 4)
  - [ ] Twitter/X sentiment catalog + adapter
  - [ ] Reddit sentiment catalog + adapter
  - [ ] LunarCrush aggregated sentiment catalog + adapter

- [ ] **News & Events** (Week 5)
  - [ ] Crypto news aggregator catalog + adapter
  - [ ] Google News API catalog + adapter

- [ ] **On-Chain Data** (Week 5)
  - [ ] Glassnode (exchange flows) catalog + adapter
  - [ ] Etherscan (blockchain metrics) catalog + adapter

- [ ] **Fundamentals** (Week 6)
  - [ ] SEC EDGAR filings catalog + adapter
  - [ ] Alpha Vantage fundamentals catalog + adapter
  - [ ] Financial Modeling Prep catalog + adapter

- [ ] **Macro & Economic** (Week 7)
  - [ ] FRED (Federal Reserve data) catalog + adapter
  - [ ] BLS (Bureau of Labor Statistics) catalog + adapter
  - [ ] Treasury data catalog + adapter

- [ ] **Options & Derivatives** (Week 8)
  - [ ] Options flow aggregators catalog + adapter
  - [ ] Unusual options activity catalog + adapter
  - [ ] Put/call ratios catalog + adapter

### **Benefits Delivered**

- **Immediate**: 3x faster extractions (WebSocket cache vs REST polling)
- **Scalability**: Add 150+ data sources in weeks instead of years
- **Agent-Ready**: AI agents as first-class consumers via auto-generated tools
- **Zero Breaking Changes**: Backward compatible migration with feature flag

## 🔧 **MEDIUM - Trading System Completeness**

**Timeline**: 2-3 days - Core trading functionality verification and enhancement

- [ ] **Stop Loss / Take Profit Verification**
  - [ ] Check if SL/TP values are being read from configuration properly
  - [ ] Verify trade monitoring triggers TP/SL execution automatically
  - [ ] Test automated position closing at profit/loss targets
  - [ ] Ensure SL/TP levels display correctly in positions table

- [ ] **Risk Management Enforcement**
  - [ ] Validate risk management parameters are enforced
  - [ ] Implement open position limits per user/bot configuration

- [ ] **User Communication (Account Reset)**
  - [ ] Email encouraging users to try reset feature for clean V2.0 accounting
  - [ ] Optional: Add banner promoting account reset for fresh start with leverage fixes
  - [ ] Monitor user feedback channels (Telegram community, support tickets)

## 🔧 **HEDIUM PRIORITY - User Settings & API Key Management**

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
  - [ ] Implement downgrade workflow (cancellation flow)
  - [ ] Implement user profile settings (Telegram integration, preferences)
  - [ ] Add account settings and preferences management


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


## ✅ **RECENTLY COMPLETED**

### **2025-10-04: Trading System Fixes + Liquidation**

**Manual Position Management** ✅ COMPLETE
- ✅ Added "Close Position" button to active trades in PositionsTable
- ✅ Implemented API endpoint: `POST /api/v2/bot/{config_id}/positions/{trade_id}/close`
- ✅ Updated paper trading service to handle manual position closure
- ✅ Tested manual close functionality with real-time SSE updates
- ✅ Fixed 401 auth errors by using apiClient instead of direct fetch
- ✅ Included paper trading router in ggbot.py to expose endpoint

**Trading Settings Validation & Position Sizing** ✅ COMPLETE
- ✅ Frontend validation with real-time error/warning feedback
- ✅ Leverage (1-100, warning >20x), Stop Loss (1-50%), Take Profit (1-500%)
- ✅ Position sizing (0.1-100%, warning >50%), Max positions (1-50, warning >10)
- ✅ Red borders for errors (blocking), yellow borders for warnings (non-blocking)
- ✅ **Position sizing FIXED**: Settings now represent MARGIN (risk), multiplied by leverage for position size
- ✅ **P&L calculation FIXED**: Removed double leverage multiplier (was showing 10x too high)
- ✅ Tested position sizing calculations match configuration

**Volume Analysis Fixes** ✅ COMPLETE
- ✅ Debugged volume analysis broken in technical indicators
- ✅ Fixed volume data not appearing in decision prompts
- ✅ Tested volume-based signal validation
- ✅ Verified volume metrics in market analysis formatting

**Liquidation System** ✅ COMPLETE (NEW)
- ✅ Automatic position liquidation when losses exceed margin (realistic leverage behavior)
- ✅ Liquidation price calculated on trade open based on margin and leverage
- ✅ Priority order: Liquidation → Stop Loss → Take Profit (matches real exchanges)
- ✅ Database schema updated with liquidation_price column
- ✅ Monitoring system checks liquidation before SL/TP

**Self-Service Account Reset Feature** ✅ COMPLETE
- ✅ Default bot cleanup (92 bots deactivated, 83 users affected)
- ✅ Verified 22 custom strategy bots remain active
- ✅ Added "Reset Account" option to bot 3-dot dropdown menu
- ✅ Implemented backend endpoint: `POST /api/v2/bot/{config_id}/reset-account`
- ✅ Reset logic: Close all positions, reset balance to $10k, clear stats, preserve bot config
- ✅ Added confirmation modal with clear warning messaging
- ✅ Tested reset functionality with active positions and historical trades
- ✅ **Metrics filtering by last_reset_at**: Win rate and stats only show post-reset trades

**Extraction Connection Stability** ✅ COMPLETE
- ✅ Fixed session race conditions in parallel timeframe extraction
- ✅ Removed problematic context manager usage causing "Session is closed" errors
- ✅ Added ensure_connected() method for shared session across parallel tasks
- ✅ Improved error message handling for empty aiohttp exceptions
- ✅ Fixed dict error response handling in get_candles method

**Subscription Management UI** ✅ COMPLETE
- ✅ Display current subscription tier and status (Pro/Free badges in UserProfile)
- ✅ Add subscription upgrade interface (UpgradeModal with Stripe Checkout)
- ✅ Add subscription management interface (Stripe Customer Portal)
- ✅ **Upgrade modal update**: Changed to FIRST100 coupon with strikethrough pricing ($29 → $14.50)
- ✅ 50% off promotion for first 100 customers clearly displayed

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

