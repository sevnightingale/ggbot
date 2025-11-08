# TODO.md - ggbots Implementation Plan

Active tasks and planned work. See CHANGELOG.md for completed features.

---

## 🤖 **Agent - Session Persistence Testing & Monitoring**

**Status**: Session resumption implemented (2025-11-08), needs production validation

- [ ] **Test Crash Recovery**
  - [ ] Restart live agent, verify session resumption logs
  - [ ] Test compaction → crash → resume flow
  - [ ] Validate conversation memory preserved

- [ ] **Monitor Session Behavior**
  - [ ] Test session longevity (does it expire after 24 hours? 7 days?)
  - [ ] Track health monitoring (`last_active_at` updates)
  - [ ] Verify no session_id changes after compaction

- [ ] **Health Check System**
  - [ ] Implement auto-restart for hung agents (no activity >30 minutes)
  - [ ] Add alerting for agent failures
  - [ ] Track tool call frequency and errors

- [ ] **Strategy Builder UX Refinement**
  - [ ] Test real-time collaborative editing (user + agent editing same strategy)
  - [ ] Verify SSE updates push agent edits to frontend
  - [ ] Test debounced auto-save (1s delay)

---

## 🏆 **AsterDEX - Frontend Integration & Competition**

**Status**: Core trading operational, needs UI and testing for competition

### **Vault & Credentials**
- [ ] Add `get_aster_credential(user_id)` to vault_utils.py
- [ ] Add `store_aster_credential(user_id, api_key, api_secret)`
- [ ] Add `delete_aster_credential(user_id)`
- [ ] Test credential encryption/decryption

### **Frontend Integration**
- [ ] **Settings Modal**
  - [ ] Add "AsterDEX" tab to Settings modal
  - [ ] Add API Key + Secret input fields
  - [ ] Add "Test Connection" button
  - [ ] Show connection status indicator

- [ ] **Trading Mode Selection**
  - [ ] Add "AsterDEX Live" option to bot creation modal
  - [ ] Show AsterDEX badge in bot rail (orange/purple)
  - [ ] Disable if credentials not configured
  - [ ] Add tooltip explaining AsterDEX mode

- [ ] **Dashboard Display**
  - [ ] Add SSE enrichment for `trading_mode === 'aster'` (SSE already supports this, verify frontend)
  - [ ] Route close button to Aster service
  - [ ] Show "Track on AsterDEX" for balance
  - [ ] Add AsterDEX icon/badge to active positions

### **API Endpoints**
- [ ] `POST /api/v2/aster/setup` (store credentials)
- [ ] `GET /api/v2/aster/status` (check connection)
- [ ] `POST /api/v2/aster/disconnect` (remove credentials)
- [ ] `GET /api/v2/positions/aster/{config_id}` (query positions)
- [ ] `POST /api/v2/positions/aster/{order_id}/close` (close position)
- [ ] `GET /api/v2/account/aster/{config_id}` (account metrics)

### **SL/TP Improvements**
- [ ] Add SL/TP conditional order creation (STOP_MARKET, TAKE_PROFIT_MARKET)
- [ ] Add SL/TP order cancellation before close
- [ ] Add leverage management (currently defaults to 10x)

### **Error Handling**
- [ ] Add rate limit tracking and backoff logic
- [ ] Implement circuit breaker at 80% rate limit
- [ ] Add retry logic with exponential backoff
- [ ] Handle common API errors (-1121, -2010, etc.)

### **Testing & Competition**
- [ ] Execute 10 test trades successfully
- [ ] Verify SL/TP conditional orders work
- [ ] Test error scenarios (insufficient balance, invalid symbol)
- [ ] Monitor rate limiting (no 429 errors)
- [ ] Create competition strategy (high-frequency, 5-10 bots)
- [ ] Monitor leaderboard ranking and total volume

---

## 🌐 **Symphony Live Trading Integration**

**Status**: BLOCKED - Waiting for Symphony API fix

**Blocker**: Symphony `/agent/all-positions` endpoint returns 404 (documented but not implemented)

**What's Needed from Symphony Team**:
```
GET https://api.symphony.io/agent/all-positions?userAddress={WALLET_ADDRESS}
Returns: accountSummary with totalEquity, availableBalance, marginUsed
```

**Our Work (Once API Fixed - ~2.5 hours)**:
- [ ] Add `get_account_summary()` method to Symphony service
- [ ] Add Symphony branches to 5 agent endpoints
- [ ] Update system prompt with Symphony capabilities
- [ ] Test end-to-end with real credentials

See: [agent/README.md](agent/README.md) "Symphony Integration Steps" for complete guide

---

## 🧠 **Market Intelligence - Future Phases**

**Phase 1 Complete**: 8 Grok sources live ($195/month platform cost)

### **Phase 2: Premium On-Chain** ($100-500/month)
- [ ] Whale wallet tracking (Nansen/Arkham)
- [ ] Exchange reserves & flows (Glassnode/CryptoQuant)
- [ ] Token unlocks calendar (TokenUnlocks.app)
- [ ] Dev activity metrics (GitHub API)

### **Phase 3: Sentiment & Social** ($100-500/month)
- [ ] Twitter/X sentiment analysis (Twitter API + NLP)
- [ ] Reddit crypto sentiment (Reddit API + NLP)
- [ ] Narrative velocity tracking (topic modeling)

### **Phase 4: Advanced Intelligence** ($200-1000/month)
- [ ] Order book liquidity heatmaps (Coinalyze)
- [ ] CEX/DEX market share tracking
- [ ] Institutional flows (BTC ETF data)

---

## 🎨 **User Experience & Frontend**

### **Trading Modes Refactor** (In Progress - Other CC Instance)
- [ ] Remove `execution_mode` duplication from JSONB
- [ ] Add `trading_mode` selection to bot creation modal
- [ ] Update frontend to use table field only

### **Mobile Responsive Design**
- [ ] Transform desktop 3-column to mobile single column
- [ ] Implement 70%-width slide-in drawers
- [ ] Create bottom tab system for drawer triggers
- [ ] Add touch gestures for carousel navigation

### **Status Messaging Improvements**
- [ ] Change "next run..." to "waiting for next candle close..."
- [ ] Add explanatory tooltips for bot status states
- [ ] Improve activation/deactivation feedback

---

## 🔧 **System Improvements**

### **User Settings & API Key Management**
- [ ] Complete API key management interface for LLM credentials
- [ ] Add secure credential storage using Supabase Vault
- [ ] Implement credential validation and testing
- [ ] Support OpenAI, DeepSeek, Anthropic, XAI credentials
- [ ] Add subscription downgrade workflow

### **Trading System Completeness**
- [ ] Verify SL/TP values read from configuration properly
- [ ] Verify trade monitoring triggers TP/SL execution automatically
- [ ] Validate risk management parameters enforced
- [ ] Implement open position limits per configuration

### **System Robustness**
- [ ] Add comprehensive error boundaries to frontend
- [ ] Implement graceful API failure handling with retries
- [ ] Add circuit breakers for external service failures
- [ ] Improve logging and error taxonomy
- [ ] Plan upgrade from Node.js 18 to Node.js 20+

### **Code Quality**
- [ ] Run `ruff` + `black` for Python formatting
- [ ] Remove unused imports and clean up hygiene
- [ ] Add proper TypeScript types for signal_data structures

---

## 📚 **Documentation**

### **Missing/Incomplete READMEs**
- [ ] Create `api/README.md` (document agent endpoints)
- [ ] Create `core/config/README.md` (config system architecture)

### **README Reviews & Updates**
- [ ] Review `market_intelligence/README.md` (verify 32 data points, update cost to $195/month)
- [ ] Review `decision/README.md` (verify V2 template system)
- [ ] Review `trading/README.md` (verify WebSocket migration complete)
- [ ] Review `database/README.md` (add agent_sessions, trade_observations tables)
- [ ] Review `frontend/README.md` (verify Forge architecture)

### **Documentation Consistency**
- [ ] Ensure ACTIVE.md and module READMEs don't contradict
- [ ] Verify README.md links to all module READMEs
- [ ] Remove legacy/outdated information

---

## 🧪 **Testing & Validation**

### **Symbol Coverage**
- [ ] Test all 142 crypto symbols for data availability
- [ ] Verify WebSocket + REST fallback for all pairs
- [ ] Create symbol blacklist for unsupported pairs

### **Technical Analysis Validation**
- [ ] Test all 21 indicator preprocessors individually
- [ ] Validate calculations against reference implementations
- [ ] Edge case testing (low volume, missing data, extreme movements)

### **Load Testing**
- [ ] Test system with multiple concurrent bots
- [ ] Validate database performance under load
- [ ] Test SSE stream with many connected clients
- [ ] Cross-browser compatibility testing

### **Security**
- [ ] Audit API endpoints for vulnerabilities
- [ ] Test rate limiting and authentication flows
- [ ] Validate data isolation between users

---

## 📚 Documentation References

- **New Claude Code Instances**: `GO.md` - Start here for onboarding
- **Current Status**: `ACTIVE.md` - Production system status
- **Complete History**: `CHANGELOG.md` - All completed features and fixes
- **Architecture**: `README.md` - Platform overview
