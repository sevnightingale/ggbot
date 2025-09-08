# TODO_NEW.md - GGBot V2 Updated Implementation Plan

## 🎯 **IMMEDIATE HIGH PRIORITY**

### **Phase 1: Scheduler Implementation & Paper Trading Verification**

#### **Scheduler Research & Architecture** 🕐
- [ ] **claude**: Research candle-close based scheduling vs time-based scheduling
  - Investigate market data APIs for candle close events
  - Compare APScheduler triggers vs WebSocket candle events
  - Analyze multi-exchange timing coordination (different close times)
  - Document pros/cons of each approach with recommendations
- [ ] **claude**: Design multi-user, multi-bot scheduler architecture
  - Each bot runs on independent `analysis_frequency` from config
  - Multiple bots per user run simultaneously (not staggered)
  - Handle timezone considerations and market hours
  - Plan resource management for concurrent bot executions
- [ ] **claude**: Implement APScheduler integration with V2 orchestrator
  - Add scheduler service to main API server (`ggbot.py`)
  - Create bot start/stop endpoints that add/remove scheduled jobs
  - Integrate with existing bot status WebSocket system
  - Test job persistence and recovery after server restarts
- [ ] **claude**: Test scheduler with real bot configurations
  - Verify analysis_frequency settings (5m, 15m, 30m, 1h, 4h, 1d, 1w) work correctly
  - Test multiple bots running simultaneously
  - Monitor resource usage and performance impact

#### **Paper Trading Engine Verification** 📊
- [ ] **claude**: Audit existing paper trading implementation vs README.md
  - Verify all endpoints are working: `/paper/execute`, `/paper/positions`, etc.
  - Test MarketDataAdapter connectivity to Hummingbot API
  - Confirm background position monitoring is running (7-second intervals)
  - Check database schema matches documentation
- [ ] **claude**: End-to-end paper trading test
  - Create test bot config and trigger orchestration
  - Verify decision → paper trading → database flow
  - Confirm position tracking, P&L calculation, stop/take profit execution
  - Test multiple paper accounts isolation
- [ ] **claude**: Integration with V2 orchestrator
  - Verify decision module calls correct paper trading webhook
  - Test trade intent format matches expected schema
  - Confirm confidence-based position sizing works
  - Validate risk management triggers

### **Phase 2: Dashboard Data Flow & Real-time Updates**

#### **Dashboard API Integration Audit** 📈
- [ ] **claude**: Review all 4 dashboard cards (PnL, trades, positions, performance)
  - Map each card to correct V2 API endpoints
  - Verify data transformation from API response to UI display
  - Check error handling for missing/invalid data
  - Test with real paper trading data
- [ ] **claude**: WebSocket monitoring system verification
  - Confirm bot status updates work end-to-end
  - Test real-time position updates during paper trading
  - Verify WebSocket connection reliability and reconnection
  - Check performance impact of real-time updates
- [ ] **claude**: Database query optimization
  - Review paper_trades, paper_accounts, paper_orders queries
  - Ensure proper indexing for performance
  - Test concurrent access from multiple users
  - Optimize slow queries identified in testing

### **Phase 3: ggShot Signal Processing Pipeline**

#### **Signal Validation Mode Architecture** 🔄
- [ ] **claude**: Design dynamic orchestrator API
  - Update `/api/v2/orchestrate/{config_id}` to accept config_type parameter
  - Add support for dynamic symbol/timeframe parameters (vs static config)
  - Design signal_validation vs autonomous_trading workflow differences
  - Plan backward compatibility with existing autonomous_trading configs
- [ ] **claude**: Implement signal_validation orchestrator behavior
  - Dynamic symbol: Accept symbol in API call instead of reading from config
  - Dynamic timeframes: Accept timeframes array in API call
  - Dynamic system prompt: Use signal-specific prompts vs config prompts
  - Preserve user decision context while allowing signal overrides
- [ ] **claude**: ggShot signal format conversion
  - Recreate ggshot/README.md workflow using base configs + signal_validation mode
  - Convert ggShot signals to standard orchestrator API calls
  - Map ggShot signal types to decision prompts and timeframes
  - Handle ggShot confidence scores and reasoning
- [ ] **claude**: Telegram listener integration
  - Update telegram listener to trigger signal_validation orchestrator calls
  - Design signal routing: which signals go to which user configs
  - Implement signal filtering and user subscription management
  - Test end-to-end: Telegram → Signal Processing → Orchestrator → Trading

#### **ggShot Premium Access Control** 🔐
- [ ] **claude**: Verify paid_data_points UI logic in GGBotConfig
  - Confirm ggShot data source shows as locked for free users
  - Test users with paid_data_points = ['ggshot'] can access ggShot
  - Implement proper upgrade prompts for ggShot access
- [ ] **claude**: Backend access control validation
  - Add ggShot access validation to data sources endpoint
  - Ensure signal_validation configs require proper permissions
  - Test access control across different subscription tiers

---

## 🎯 **MEDIUM PRIORITY**

### **Phase 4: Core UX Improvements**

#### **Top Navigation System** 🧭
- [ ] **claude**: Design and implement top navigation bar
  - Logo placement (ggbots.ai branding)
  - Profile dropdown with user info
  - Account settings page
  - Logout functionality
  - Responsive hamburger menu for mobile
- [ ] **claude**: Create profile/account settings pages
  - User profile information and editing
  - Subscription tier display and management
  - LLM credential management interface
  - Email/password change functionality

#### **Production Features**
- [ ] **claude**: Turn on actual ggbot paper trading demonstration
  - Create demo bot configuration with realistic settings
  - Start bot and document full trading cycle
  - Capture screenshots/video of live trading
  - Verify P&L updates, position management, trade history
- [ ] **claude**: Landing page redesign implementation
  - Implement new design assets and layout
  - Update copy and messaging for V2 features
  - Add demo/preview functionality
  - Optimize for conversion and onboarding

---

## 🎯 **LOWER PRIORITY (Polish & Optimization)**

### **Phase 5: Real-time Status System** 📡
#### **Status Message Research & Design**
- [ ] **claude**: Review current orchestration logs to identify status update points
- [ ] **claude**: Design 4-5 word status messages for each phase:
  - `inactive` → "Bot stopped"
  - `idle` → "Ready to trade" 
  - `extraction` → "Analyzing market data"
  - `decision` → "Making trade decision" 
  - `trading` → "Executing trade"
- [ ] **claude**: Define status update trigger points in V2 orchestrator

#### **Supabase Real-time Implementation** 
- [ ] **claude**: Create `bot_status` table in Supabase with RLS policies
- [ ] **claude**: Add status update calls to V2 orchestrator (`ggbot.py`)
- [ ] **claude**: Implement Supabase real-time subscriptions in frontend botStore
- [ ] **claude**: Update GGBot component to animate status changes
- [ ] **claude**: Test real-time status flow: Orchestrator → Database → Frontend

#### **WebSocket Alternative (If Supabase real-time doesn't work)**
- [ ] **claude**: Add WebSocket endpoint to V2 backend (`ggbot.py`)
- [ ] **claude**: Integrate WebSocket status broadcasting in orchestrator
- [ ] **claude**: Update frontend WebSocket connection to use V2 backend
- [ ] **claude**: Test WebSocket status flow end-to-end

### **Phase 6: Comprehensive Testing & Documentation** 📋

#### **End-to-End Testing**
- [ ] **claude**: Create `tests/test_complete_user_lifecycle.py`
  - User signup → email verification → login
  - Create first bot configuration (autonomous_trading)  
  - Start bot → orchestration → extraction → decision → trading
  - Real-time status updates throughout
  - View results in dashboard
  - Stop bot
- [ ] **claude**: Test Signal Validation lifecycle (if ggShot access available)
- [ ] **claude**: Test premium feature gating for free vs paid users
- [ ] **claude**: Validate all API endpoints with real authentication
- [ ] **claude**: Test error handling and recovery scenarios

#### **Production Readiness Validation**
- [ ] **claude**: Test full frontend build and deployment readiness
- [ ] **claude**: Validate all environment variables are properly configured
- [ ] **claude**: Test V2 backend performance under load
- [ ] **claude**: Verify database RLS policies prevent data leakage between users

#### **API Documentation**
- [ ] **claude**: Generate complete V2 API documentation with all endpoints
- [ ] **claude**: Document authentication flow and JWT token usage
- [ ] **claude**: Update configuration schema documentation
- [ ] **claude**: Document ggShot integration and Signal Validation mode
- [ ] **claude**: Create API examples for all major workflows

#### **Architecture Documentation**
- [ ] **claude**: Update `DOCS/V2.md` with current implementation status
- [ ] **claude**: Document real-time status system architecture
- [ ] **claude**: Update `frontend/README.md` with latest features
- [ ] **claude**: Document ggShot integration approach

### **Phase 7: Code Cleanup & Optimization** 🧹
- [ ] **claude**: Methodical V1 legacy code removal
  - Audit all files for V1 references and unused imports
  - Remove old extraction/, decision/, trading/ modules (keep V2 versions)
  - Clean up unused configuration files and templates
  - Remove hardcoded demo values and mock data
  - Preserve ggshot/ for re-integration
  - Test thoroughly after each cleanup phase

### **Phase 6: Advanced UX Features** ✨
- [ ] **claude**: Typeform-style bot creation survey
  - Design multi-step wizard with progress bar
  - Break configuration into logical sections/questions
  - Add helpful explanations and tooltips
  - Implement smooth transitions and animations
  - A/B test against current configuration flow
- [ ] **claude**: Mobile responsiveness optimization
  - Redesign dashboard layout for mobile screens
  - Optimize bot circle component for touch interfaces
  - Implement mobile-friendly navigation
  - Test across different device sizes and orientations
- [ ] **claude**: Design and visibility improvements
  - Research background texture and contrast options
  - Implement light mode theme option
  - Improve visibility in high-light conditions
  - Test accessibility and readability improvements
  - Update VIBE.md with new design patterns

### **Phase 7: Small UI/UX Refinements** 🎨
- [ ] **sev**: Create list of specific UI/UX tweaks needed
- [ ] **claude**: Implement UI/UX improvements from list
  - Fix spacing, alignment, and visual inconsistencies
  - Improve button states and hover effects
  - Refine animations and transitions
  - Polish loading states and error messages

### **Phase 8: Business Model Features** 💰

#### **Stripe Integration**
- [ ] **sev**: Set up Stripe account and configure API keys
- [ ] **sev**: Define pricing for Base/Signals tier
- [ ] **claude**: Implement Stripe subscription creation endpoints
- [ ] **claude**: Create subscription management frontend pages
- [ ] **claude**: Add subscription upgrade/downgrade flows
- [ ] **claude**: Implement Stripe webhook handling for subscription events
- [ ] **claude**: Add `@requires_subscription` decorator for feature gating
- [ ] **claude**: Test subscription lifecycle end-to-end

#### **Per-Bot Telegram Publishing**
- [ ] **sev**: Research telegram bot infrastructure for per-bot channel publishing
- [ ] **sev**: Decide on existing bot reuse vs new bot creation
- [ ] **claude**: Adapt existing telegram infrastructure for multi-bot channels
- [ ] **claude**: Implement per-bot telegram channel configuration in GGBotConfig
- [ ] **claude**: Integrate telegram publishing with V2 orchestrator decisions
- [ ] **claude**: Test telegram signal publishing for Base tier users

#### **Advanced Features**
- [ ] **claude**: Add Google/GitHub OAuth social authentication
- [ ] **claude**: Add advanced bot analytics and performance tracking
- [ ] **claude**: Add comprehensive error boundaries
- [ ] **claude**: Implement proper logging throughout
- [ ] **sev**: Final testing of complete user journey
- [ ] **sev**: Deploy to staging environment for beta testing

---

## 📋 **COMPLETED ACHIEVEMENTS** ✅

### **Phase 0: Frontend-Backend Integration** ✅ **COMPLETED 2025-09-07**
- ✅ Fixed ConfigData structure alignment with V2.1 schema
- ✅ Implemented real Supabase authentication throughout
- ✅ Added proper LLM credential encryption via Supabase Vault
- ✅ Fixed config_type persistence with sliding switch UI design
- ✅ Updated all API models to support new fields (config_type, schema_version, llm_config)
- ✅ Resolved Pydantic validation dropping config fields
- ✅ Implemented neumorphic sliding switch matching VIBE.md aesthetics

---

## 🔧 **ARCHITECTURE CONSIDERATIONS**

### **Scheduler Design Decisions**
- **Candle-Close vs Time-Based**: Need to research market data APIs and timing precision
- **Multi-Bot Coordination**: Simultaneous execution may strain resources - need monitoring
- **Job Persistence**: APScheduler with database jobstore for restart recovery
- **Market Hours**: Consider crypto 24/7 vs traditional market scheduling

### **ggShot Integration Complexity**
- **Dynamic Orchestrator**: Major change from static config to dynamic signal parameters
- **Signal Routing**: Need user subscription management for signal distribution
- **Prompt Engineering**: Different system prompts for signal validation vs autonomous trading
- **Backward Compatibility**: Ensure existing autonomous_trading configs still work

### **Real-Time Data Challenges**
- **WebSocket Scaling**: Multiple users with multiple bots = many concurrent connections
- **Database Load**: Real-time position updates may impact query performance
- **State Synchronization**: Frontend state must stay in sync with backend changes
- **Error Recovery**: WebSocket disconnections need graceful handling

### **Paper Trading Validation**
- **Market Data Quality**: Verify Hummingbot API provides accurate, timely prices
- **Risk Management**: Test stop/take profit execution under various market conditions
- **Performance Isolation**: Ensure multiple paper accounts don't interfere
- **Data Consistency**: P&L calculations must match across all interfaces

---

## 📊 **SUCCESS METRICS**

### **Immediate Goals (Phase 1-3)**
- [ ] **Functional Scheduler**: Bots start/stop on schedule with correct frequency
- [ ] **Live Paper Trading**: Users can watch bots make real trades with live P&L
- [ ] **Real-Time Dashboard**: All 4 cards show live, accurate data
- [ ] **ggShot Integration**: Signal validation mode processes signals → trades

### **Medium-Term Goals (Phase 4-5)**
- [ ] **Professional UI**: Top nav, profile management, clean codebase
- [ ] **Production Demo**: Full working demo for user onboarding
- [ ] **Code Quality**: No legacy code, proper error handling, optimized queries

### **Long-Term Polish (Phase 6-7)**  
- [ ] **Mobile Optimized**: Responsive design works well on all devices
- [ ] **Accessibility**: Light mode, high contrast, readable in all conditions
- [ ] **User Experience**: Typeform flow, smooth animations, intuitive interface

---

## 🚀 **DEPLOYMENT READINESS**

### **Current Status**: ~85% Complete
- ✅ **Core Foundation**: Authentication, configuration, data structures aligned
- ✅ **Paper Trading Engine**: Built and ready for testing
- ✅ **Frontend-Backend Sync**: Config persistence and API integration working
- 🔄 **Scheduler & Real-Time**: Need implementation and verification
- ❌ **ggShot Integration**: Requires signal processing pipeline rebuild
- ❌ **Testing & Polish**: End-to-end validation and UX improvements needed

### **Go-Live Criteria**
1. **Scheduler working** - Users can start/stop bots that trade on schedule
2. **Paper trading visible** - Dashboard shows live trading activity and P&L
3. **Data flow verified** - All dashboard metrics accurate and real-time
4. **ggShot integrated** - Signal validation mode processes external signals
5. **Code clean** - No legacy code, proper error handling, production ready

**Target**: Complete Phases 1-3 for production readiness, Phases 4-7 for polish and growth.