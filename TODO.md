# TODO.md - ggbots Implementation Plan

Active tasks and planned work. See CHANGELOG.md for completed features.

---

## 🚨 **CRITICAL - CVE-2025-66478 Secret Rotation**

**Status**: 🔴 URGENT - Application was vulnerable for ~11 hours (Dec 4-5, 2025)
**Planning Doc**: [DOCS/todo/CVE_2025_66478_SECRET_ROTATION.md](DOCS/todo/CVE_2025_66478_SECRET_ROTATION.md)

**Vulnerability**: Next.js/React Server Components RCE (CVSS 10.0)
- Application ran vulnerable Next.js 15.3.3 during exposure window
- Upgraded to patched 15.5.7 on Dec 5, 2025
- Per advisory: "rotate any secrets it uses, starting with your most critical ones"

**Action Required**: Follow rotation checklist in priority order
- [ ] **Day 1**: CRITICAL secrets (Supabase, Auth, Trading APIs)
- [ ] **Day 1-2**: HIGH PRIORITY secrets (AI APIs, Market Data, Email)
- [ ] **Week 1**: MEDIUM PRIORITY secrets (Admin, Redis, OAuth)

See planning doc for complete provider-specific instructions and verification steps.

---

## 🎲 **USX Staking Modal - Bot Competition Betting**

**Status**: 🔵 PLANNING
**Planning Doc**: [DOCS/todo/USX_STAKING_MODAL.md](DOCS/todo/USX_STAKING_MODAL.md)
**Complexity**: Medium (~6-8 hours)

**Summary**: Gamification feature allowing users to stake USX (Scroll stablecoin) on which bot they think will win competitions. Standard Scroll staking (USX→sUSX) + simple DB record of bot choice. Competition logic deferred.

### **User Flow**
1. Click "Stake on Bot" → Modal opens
2. Connect wallet (RainbowKit)
3. Select bot to back (dropdown)
4. Enter USX amount
5. Execute 2 txs: approve + deposit to sUSX vault
6. Record stake in DB
7. User earns base yield (worst case) + prize if bot wins (best case)

### **Implementation Phases**

**Phase 1: Research & Setup** (~1 hour)
- [ ] Find USX/sUSX contract addresses on Scroll mainnet (docs.usx.capital, Scrollscan)
- [ ] Get WalletConnect Project ID (cloud.walletconnect.com)
- [ ] Install deps: `wagmi`, `viem`, `@rainbow-me/rainbowkit`, `@tanstack/react-query`
- [ ] Set up wagmi config with Scroll chain

**Phase 2: Database & Backend** (~1 hour)
- [ ] Create `usx_stakes` table (user_id, wallet_address, config_id, usx_amount, tx_hash)
- [ ] Add `POST /api/v2/usx/stake` endpoint (record stake after on-chain tx)
- [ ] Add `GET /api/v2/usx/stakes` endpoint (list user stakes)

**Phase 3: Frontend Web3 Integration** (~2-3 hours)
- [ ] Wrap app in WagmiProvider + RainbowKitProvider + QueryClientProvider
- [ ] Create contract constants (`lib/contracts.ts` with USX/sUSX addresses + ABIs)
- [ ] Build StakingModal component with wallet connect, bot selector, amount input
- [ ] Test wallet connection and balance reading

**Phase 4: On-Chain Integration** (~2-3 hours)
- [ ] Implement approve transaction (USX.approve → sUSX vault)
- [ ] Implement deposit transaction (Vault.deposit → receive sUSX)
- [ ] Add transaction waiting/success/error states
- [ ] Test on Scroll mainnet with small amounts

**Phase 5: UI Integration** (~1 hour)
- [ ] Add "Stake on Bot" trigger (location TBD)
- [ ] Integrate modal with existing UI
- [ ] End-to-end testing
- [ ] Deploy to Vercel

---

## 🎨 **Activity Modal Redesign** [ACTIVITY_MODAL_REDESIGN.md]

**Status**: 🟡 PHASE 1 COMPLETE
**Planning Doc**: [DOCS/todo/ACTIVITY_MODAL_REDESIGN.md](DOCS/todo/ACTIVITY_MODAL_REDESIGN.md)
**Complexity**: Medium (~4-6 hours)

**Problem**: Bottom sheet for activity details is poor UX - unformatted text blobs, no navigation between activities, mobile-unfriendly.

**Solution**: Replace with centered modal featuring carousel navigation through activities + structured content formatting.

### **Phase 1: Modal Component (COMPLETE)**

**Modal Navigation**:
- [x] Created `activity-modal.tsx` - new centered modal component
- [x] Swipe left/right (mobile) to navigate timeline
- [x] Arrow keys (desktop) to navigate, Escape to close
- [x] Visual swipe feedback during gesture

**Content Formatting**:
- [x] Structured display for each activity type (llm_thought, trade_entry, trade_exit, market_query)
- [x] Type-specific formatters with proper layout and styling
- [x] Trades show: entry/exit prices, P&L, duration, confidence, SL/TP
- [x] LLM thoughts: action, confidence bar, reasoning (will parse structured sections when available)
- [x] Market queries: collapsible data sections, metadata summary

**Integration**:
- [x] Integrated with tv-timeline.tsx (replaced bottom-sheet)
- [x] All activities navigable via single modal
- [x] Build passes, ready for testing

### **Phase 2: LLM Output Restructure (TODO)**

- [ ] Update prompts to output structured REASONING sections (KEY_SIGNAL, SUPPORTING, RISK, SUMMARY)
- [ ] Update parser in `decision/engine_v2.py` to extract structured sections
- [ ] Frontend already supports parsing structured format (will auto-render when available)

See planning doc for full implementation phases and file list.

---

## 📊 **Strategy Advisor Analysis** [STRATEGY_ADVISOR_ANALYSIS.md]

**Status**: 🔵 PLANNING
**Planning Doc**: [DOCS/todo/STRATEGY_ADVISOR_ANALYSIS.md](DOCS/todo/STRATEGY_ADVISOR_ANALYSIS.md)
**Complexity**: Medium-High (~8-12 hours)

**Problem**: Users have no automated way to understand why their bot wins or loses. Must manually browse activities with no statistical analysis or actionable recommendations.

**Solution**: Enhance Strategy Advisor with button prompts and automated performance analysis.

### **Strategy Advisor Button Prompts**
- [ ] Replace empty textbox with button grid
- [ ] "Create Strategy" - Existing chat flow
- [ ] "Analyze Performance" - Triggers automated analysis
- [ ] "Improve Config" - Suggests optimizations

### **Automated Analysis Engine**
- [ ] Basic stats: win rate, P&L, R:R ratio, break-even WR needed
- [ ] Direction analysis: long vs short performance
- [ ] Market data correlation: which indicator patterns predict wins/losses
- [ ] Duration analysis: hold times, big loss identification
- [ ] Confidence calibration: stated confidence vs actual win rate
- [ ] AI synthesis: generate prioritized recommendations

### **Example Output**
```
🚨 CRITICAL: Risk/Reward Inverted (0.75:1)
   Avg win $10.22 vs avg loss $13.58
   → Recommendation: Tighter stop loss (2-3%)

🚨 CRITICAL: Shorts Underperforming (18% WR)
   Longs: 37% WR, Shorts: 18% WR
   → Recommendation: Only take long positions

📊 PATTERN: 1H MACD Rising + Long = Best setup (42.9% WR)
```

See planning doc for full technical architecture and implementation phases.

---

## ⏸️ **BLOCKED - External Dependencies**

### Symphony Live Trading Integration

**Status**: BLOCKED - Waiting for Symphony API fix

**Blocker**: Symphony `/agent/all-positions` endpoint returns 404 (documented but not implemented)

**Our Work (Once API Fixed - ~2.5 hours)**:
- [ ] Add `get_account_summary()` method to Symphony service
- [ ] Add Symphony branches to 5 agent endpoints
- [ ] Update system prompt with Symphony capabilities
- [ ] Test end-to-end with real credentials

### Symphony Spot Trading - Monad (MON)

**Status**: BLOCKED - Waiting for Symphony API deployment

Both spot trading endpoints return 404 (not deployed yet):
- `GET /token/price` - Token price lookup
- `POST /agent/swap` - Execute spot swaps

All test scripts and documentation ready. See [DOCS/symphony_spot_integration.md](DOCS/symphony_spot_integration.md).

### Market Maker - Kuru Integration

**Status**: WAITING - Module complete, needs Kuru API launch

**What's Ready**:
- [x] Core Avellaneda-Stoikov engine (~900 lines)
- [x] Simulation tested (+0.20% P&L, inventory management working)
- [x] Exchange adapter interface
- [x] Kuru adapter template (needs real API docs)

**Next Steps (When Kuru Launches)**:
- [ ] Register on Kuru platform, get API credentials
- [ ] Update KuruAdapter with actual endpoints/auth
- [ ] Test with small capital ($100-200 orders, $2k capital)
- [ ] Production deployment if successful

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

## 📚 Documentation References

- **New Claude Code Instances**: `GO.md` - Start here for onboarding
- **Current Status**: `ACTIVE.md` - Production system status
- **Complete History**: `CHANGELOG.md` - All completed features and fixes
- **Architecture**: `README.md` - Platform overview
