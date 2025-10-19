# TODO.md - ggbots Implementation Plan

## 🚀 **HIGH PRIORITY - Symphony.io Live Trading Integration**

- [x] **Symbol System Extension**
  - [x] Extend `core/symbols/registry.py` with Symphony format support
  - [x] Add `"symphony": "BTC"` field to 100 compatible symbols
  - [x] Add `"symphony_compatible": true/false` boolean to all symbols
  - [x] Add `to_symphony()` and `from_symphony()` methods to standardizer
  - [x] Add `is_symphony_compatible()` check method

- [ ] **Premium Feature Configuration**
  - [ ] Add 'live_trading' to permissions system (`frontend/lib/permissions.tsx`)
  - [ ] Implement `can_use_live_trading()` permission check in backend
  - [ ] Add Symphony to premium features list

- [ ] **Settings Modal & Account Connection**
  - [ ] Create `SettingsModal.tsx` component with Symphony section
  - [ ] Add Symphony API key input field with validation
  - [ ] Add smart account address input (with tooltip: "Used for future balance features")
  - [ ] Implement connection status UI (connected/disconnected states)
  - [ ] Add Settings menu item to UserProfile dropdown
  - [ ] Create Symphony connection status endpoint

- [ ] **Database Schema Changes**
  - [ ] Extend `users` table: Add `symphony_vault_id` and `symphony_smart_account` columns
  - [ ] Extend `configurations` table: Add `symphony_agent_id` and `trading_mode` columns
  - [ ] Create `live_trades` table (minimal schema: batch_id, config_id, decision_id, timestamps)
  - [ ] Add idempotency constraint: `UNIQUE(decision_id)`
  - [ ] Create single index on `config_id` for main query pattern

- [ ] **Vault Integration**
  - [ ] Extend `VaultManager` with `store_symphony_credential()` method
  - [ ] Add `get_symphony_credential()` method for retrieving API keys
  - [ ] Add `delete_symphony_credential()` method for cleanup
  - [ ] Test vault encryption/decryption flow with Symphony credentials

- [ ] **Symphony Service Implementation**
  - [ ] Create `trading/live/symphony_service.py` with thin wrapper class
  - [ ] Implement `execute_trade_intent()` with 3-second settlement wait
  - [ ] Add idempotency check before Symphony API calls
  - [ ] Implement symbol conversion using UniversalSymbolStandardizer
  - [ ] Add `/agent/batch-open` integration with proper field mapping
  - [ ] Implement `close_position()` method with `/agent/batch-close`
  - [ ] Implement `get_open_positions()` with field mapping (asset→symbol, isLong→side)
  - [ ] Add error handling for Symphony API rejections

- [ ] **Orchestrator Integration**
  - [ ] Add Symphony service to ggbot.py imports and initialization
  - [ ] Modify `_run_trading_v2()` to route based on `trading_mode`
  - [ ] Implement trading router (paper vs live mode switch)
  - [ ] Add position management integration for live mode
  - [ ] Pass open positions to decision engine for position_management mode

- [ ] **API Endpoints**
  - [ ] Create `POST /api/v2/symphony/setup` (store credentials, validate API key)
  - [ ] Create `GET /api/v2/symphony/status` (check connection status)
  - [ ] Create `GET /api/v2/positions/live/{config_id}` (query Symphony positions)
  - [ ] Create `POST /api/v2/positions/live/{batch_id}/close` (close position)
  - [ ] Create `POST /api/v2/config/duplicate-as-live` (duplicate paper bot as live)

- [ ] **Frontend - Duplicate as Live Flow**
  - [ ] Add "Create Live Version" button to BotManagementMenu (paper bots only)
  - [ ] Implement premium permission check before showing button
  - [ ] Check Symphony connection status before allowing live bot creation
  - [ ] Create "Create Live Version" modal with Symphony agent ID input
  - [ ] Add warning messaging: "This bot will use real capital"
  - [ ] Implement `handleCreateLiveVersion()` function
  - [ ] Auto-suggest bot name: "{Original Name} (Live)"

- [ ] **Frontend - Dashboard Updates**
  - [ ] Add 🔴 LIVE badge to bot display for live trading bots
  - [ ] Update PositionsTable to handle live positions (query different endpoint)
  - [ ] Implement position data loading based on trading_mode
  - [ ] Add confirmation dialog for closing live positions
  - [ ] Update close position handler to route to correct endpoint (paper vs live)

- [ ] **Testing & Validation**
  - [ ] Test Symphony account setup flow (API key + smart account)
  - [ ] Test paper bot duplication to live bot
  - [ ] Verify live position opening (check Symphony portal + ggbots dashboard)
  - [ ] Test manual position closing in live mode
  - [ ] Test symbol compatibility validation (100 supported symbols)
  - [ ] Test idempotency (retry on timeout doesn't create duplicate trades)
  - [ ] Test error handling (invalid API key, insufficient balance, unsupported symbol)
  - [ ] Verify live_trades table linkage (batch_id → decision_id traceability)

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

