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

- [x] **Live Trading System Polish** (Complete - 2025-10-24)
  - [x] Update trade query endpoints to support live_trades table
  - [x] Fix metrics calculations to include live trades (SSE enrichment)
  - [x] Ensure positions display correctly for live bots
  - [x] Update dashboard stats to aggregate paper + live trades
  - [x] Update PositionsTable to handle live trading data format
  - [x] Integrate Symphony data into SSE dashboard stream
  - [ ] Test P&L calculations with live trade data
  - [ ] Verify close reason tracking in live_trades

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

## 📊 **MEDIUM-LOW PRIORITY - Trade Timeline Feature**

**Timeline**: 9-12 days - Complete trade lifecycle visualization and analytics foundation

**See**: [DOCS/TRADE_TIMELINE.md](DOCS/TRADE_TIMELINE.md) for complete design specification

### Overview
Comprehensive trade lifecycle view showing Market Data → Entry Decision → Trade Management → Exit Decision, enabling transparency and advanced analytics.

### Phase 1: Database Schema (2-3 days)
- [ ] Add `exit_decision_id` to `paper_trades` table
- [ ] Add `exit_decision_id` to `live_trades` table
- [ ] Add `trade_id` to `decisions` table (reverse lookup)
- [ ] Add `trade_type` ('paper'/'live') to `decisions` table
- [ ] Create indexes for performance
- [ ] Write and test migration scripts
- [ ] Deploy schema changes to production

### Phase 2: Backend Integration (3-4 days)
- [ ] Update Decision Engine V2
  - [ ] Add `active_trade` parameter to `make_decision()`
  - [ ] Implement `_link_decision_to_trade()` method
  - [ ] Link "wait" decisions to active trades
- [ ] Update Paper Trading Engine
  - [ ] Link opening decision to trade on entry
  - [ ] Store exit_decision_id on close
  - [ ] Update `execute_trade()` method
  - [ ] Update `close_position()` method
- [ ] Update Live Trading Engine (Symphony)
  - [ ] Link opening decision to live_trades
  - [ ] Store exit_decision_id on Symphony close
  - [ ] Update Symphony service methods
- [ ] Update Orchestrator (ggbot.py)
  - [ ] Pass active_trade context to decision engine
  - [ ] Pass exit_decision_id when closing positions
  - [ ] Implement `_get_active_trade()` helper

### Phase 3: API Endpoints (1 day)
- [ ] Create `GET /api/v2/trade/{trade_id}/timeline` endpoint
  - [ ] Support both paper and live trades
  - [ ] Verify ownership/permissions
  - [ ] Return entry decision, monitoring decisions, exit decision
  - [ ] Parse and return formatted market data
- [ ] Update API client (frontend/lib/api.ts)
  - [ ] Add `getTradeTimeline(tradeId, tradeType)` method

### Phase 4: Frontend Component (2-3 days)
- [ ] Create `TradeTimelineModal.tsx` component
  - [ ] 4-section timeline UI (Market Data, Entry, Management, Exit)
  - [ ] Expandable/collapsible sections
  - [ ] Loading and error states
  - [ ] Mobile responsive design
- [ ] Add Timeline triggers to existing components
  - [ ] "View Timeline" in TradeDetailPopover
  - [ ] Timeline icon in PerformanceChart trade dots
  - [ ] Timeline button in DecisionFeed cards
  - [ ] Timeline option in Trade History Modal
- [ ] Market data formatting component
  - [ ] Parse multi-timeframe data from prompt
  - [ ] Format indicators for readability
  - [ ] Highlight critical signals

### Phase 5: Testing & Polish (2 days)
- [ ] Test with existing trades (NULL exit_decision_id handling)
- [ ] Test with new trades (verify full linking)
- [ ] Test paper and live trades separately
- [ ] Verify monitoring decisions link correctly
- [ ] Test Timeline modal on mobile
- [ ] Add fallback queries for old trades without links

### Future Analytics Capabilities
- [ ] Win/loss pattern analysis by market conditions
- [ ] Confidence calibration analysis
- [ ] Indicator effectiveness correlation
- [ ] Monitoring frequency vs outcomes
- [ ] Multi-timeframe analysis effectiveness

---

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


---

## 📚 Documentation References

- **New Claude Code Instances**: `GO.md` - Start here for onboarding procedure
- **Current Status**: `ACTIVE.md` - Production system status and operational reference
- **Complete History**: `CHANGELOG.md` - All completed features, fixes, and improvements
- **Architecture**: `README.md` - Platform overview and getting started guide

