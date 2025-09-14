# ggbot Forge Architecture

## CONTEXT

The Forge represents a complete architectural rethink of the ggbot dashboard, built from first principles with elegance and simplicity as core values. Rather than inheriting the complex patterns from the legacy dashboard (600+ line botStore, global state management, data transformation layers), the Forge adopts a clean, local-first approach.

### Design Philosophy
- **Data Foundation First**: Establish rock-solid API integration and real-time flows before any UI concerns
- **Local State Elegance**: Direct API types, no transformations, single source of truth per page
- **Progressive Layering**: Build in phases - foundation, then design system, then components
- **Component Separation**: Break monolithic config editing into focused, reusable components
- **Multi-Bot Native**: Designed for `selectedConfigId` switching from day one

### Why Forge vs Dashboard Evolution
The dashboard had accumulated architectural debt that made elegant evolution impossible. The Forge starts fresh with lessons learned, avoiding the complexity traps while maintaining all functional requirements. This clean slate approach enables the modern UX improvements (dark/light mode, responsive design) that would be difficult to retrofit.

### Key Architectural Decisions Made
- **No data transformation** - Use `BotConfiguration` API types directly, eliminated mapping layer
- **Local state only** - Rejected global Zustand store patterns, everything lives in page component  
- **SSE over WebSocket** - Migrated from complex WebSocket to simple Server-Sent Events
- **API client reuse** - Leverage existing `apiClient` with proper authentication vs custom fetch
- **Multi-bot from day one** - `selectedConfigId` pattern prevents single-bot limitations
- **Centralized config updates** - Single update function handles all config changes for separated components

### Critical Implementation Notes
- Fixed `BotConfiguration` interface missing `state` field that API actually returns
- SSE filtering by `config_id` prevents data leakage between bots
- Start/stop API responses include `next_run` for immediate countdown display
- Bot switching clears operational state (positions, decisions) but preserves config data
- All real-time updates (execution phases, positions, account balances) come via SSE stream

### Progressive Duplication Strategy (Current Implementation Approach)
The Forge follows a **progressive duplication strategy** rather than attempting to refactor the legacy MonitorContent:
1. **Build proper components** (ActivationBar, MetricsBar, PositionsTable, DecisionFeed) with clean architecture
2. **Intentional duplication** - Both new components AND legacy MonitorContent show same data during transition
3. **Preserve existing functionality** - Legacy system continues working while new components are built
4. **Complete replacement** - Once all functionality is replicated, delete entire MonitorContent component
This approach minimizes risk while enabling architectural evolution and maintains a working system throughout development.

### Agent Color System & Design Standards
- **Agent Colors**: Blue (#38a1c7) extraction, Green (#2cbe77) decision, Orange (#be6a47) trading
- **Financial Colors**: emerald-400 (profit/gains), rose-400 (loss/negative), consistent throughout
- **Container Design**: All components use `rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)]`
- **Grid Layout Architecture**: 12-column grid system with nested grids for sophisticated layouts
- **Professional Table Design**: HTML table structure with proper thead/tbody, responsive with `min-w-full`
- **Responsive Strategy**: Mobile-first with proper container spacing, not full-width expansion
- **Real Data Integration**: Components connect to live SSE streams and account data, **absolutely no mock/simulated/placeholder data**

## CURRENT

### Overview
The Forge is a single-page application that replaces the dashboard with an elegant, local state architecture. It manages multiple bot configurations with seamless switching between them via `selectedConfigId`.

### Data Architecture
- **Local state only** - No global store, all state lives in the Forge page component
- **Direct API types** - Uses `BotConfiguration` from API client without transformation
- **Multi-bot native** - Loads all user configurations, tracks selected one via `selectedConfigId`
- **Centralized state pattern** - All bots stored in `allBots[]`, selected bot computed dynamically

### Authentication Flow
1. Check Supabase auth on page load
2. Extract user ID from session
3. Redirect to login if not authenticated

### Configuration Data Flow
1. User lands on forge
2. Call `apiClient.listConfigs()` to get all user configurations
3. If configurations exist: Load all into `allBots[]`, select first via `selectedConfigId`
4. If no configurations exist: Auto-create default RSI bot, set as selected
5. Bot switching updates `selectedConfigId`, all page content keys off selected bot

### Real-Time Updates
1. Establish SSE connection to dashboard stream
2. Reconnect when `selectedBot` changes to ensure clean state
3. Filter incoming data for currently selected bot's `config_id`
4. Update local state for:
   - Execution status (extraction → decision → trading phases)
   - Live positions with P&L updates
   - Recent AI decisions with confidence scores
   - Paper trading account balances and metrics
   - Next run timing for countdown

### Bot Control Actions
1. Start bot: API call to `/api/v2/bot/{selectedConfigId}/start`
2. Stop bot: API call to `/api/v2/bot/{selectedConfigId}/stop`
3. Update selected bot state in `allBots[]` array optimistically
4. Extract `next_run` from API response for immediate countdown display
5. Real-time updates confirm state changes via SSE

### Bot Switching UI
- Bot selector appears when multiple bots exist
- Shows bot names with active status indicators (green dot)
- Clicking switches `selectedConfigId` and updates all page content
- SSE reconnects to filter data for newly selected bot

### Current Status
- ✅ **Phase 1 Complete**: Multi-bot architecture, API integration, SSE filtering, bot switching
- ✅ **Phase 2B Complete**: Layout shell with responsive design, dark/light theming, mobile nav
- ✅ **ActivationBar Complete**: Professional status/control bar with real data integration
  - Real account balance and frequency display from SSE/API data
  - Agent-specific colors for pipeline stages (blue/green/orange)
  - Braille spinner with status messages during execution
  - Responsive 3-group layout (Info, Pipeline, Controls)
  - Activate/Deactivate terminology (no more Start/Stop)
  - Proper containerized design with max-width constraints
- ✅ **BotRail Containerized**: Proper rounded container instead of full-column expansion
- ✅ **MetricsBar Complete**: Professional KPI grid with real portfolio analytics
  - Real-time SSE data integration with portfolio analytics from PositionManager
  - 2x2 grid layout (optimized for side-by-side placement with DecisionFeed)
  - Trend indicators with emerald/rose color coding for profit/loss
  - Loading skeleton states and proper TypeScript integration
- ✅ **DecisionFeed Complete**: AI decision carousel with auto-advance and expandable reasoning
  - Carousel navigation with newest-first auto-advance on new decisions
  - Expandable reasoning text (150 char truncation with show more/less)
  - Action badges and confidence scoring display
  - Real decision data integration via SSE stream
- ✅ **PositionsTable Complete**: Professional trading positions table
  - HTML table structure with proper thead/tbody and min-w-full responsive
  - Desktop table with mobile card transformation (no horizontal scroll)
  - Real-time P&L display with color coding and SL/TP levels
  - Empty state with helpful guidance when no positions exist
- ✅ **Nested Grid Layout Complete**: 2-column desktop layout with mobile stacking
  - DecisionFeed and MetricsBar side-by-side on lg+ breakpoints
  - PositionsTable full-width below the 2-column section
  - Left-aligned layout (removed mx-auto) fixes awkward centering on wide screens
  - Mobile responsive - all components stack vertically on smaller screens
- ⏳ **Ready for Legacy Cleanup**: All MonitorContent functionality now replicated

## PLANS

### Elegant Config State Architecture

#### Centralized State Management
- Forge page maintains single source of truth for all `BotConfiguration` objects
- `selectedConfigId` state determines which bot is currently active
- Generic update function handles all configuration changes for selected bot
- Dirty state tracking to detect unsaved changes
- Single save operation overwrites entire configuration for selected bot

#### Multi-Bot Switching Support
- Load all user configurations, display selected one
- `selectedConfigId` drives all page content (config editing, operational data, controls)
- SSE stream filters data by currently selected `config_id`
- Switching bots clears operational state (positions, decisions, execution status)
- Config editing always targets currently selected bot
- Bot selector component for navigation between multiple bots

#### Component Separation Strategy
- **Market Data Component**: Manages data sources and technical indicators
- **Decision Component**: Handles strategy prompts and analysis frequency  
- **Risk Management Component**: Controls position sizing and risk parameters
- **LLM Configuration Component**: Manages AI provider and model settings
- **Bot State Component**: Handles active/inactive state and naming

#### Update Flow Pattern
- Each component receives focused update function for its domain
- Components update specific sections of configuration via callbacks
- All changes flow through central update function
- Immediate local state updates with dirty tracking
- Batch save overwrites database configuration

#### Multi-Field Support
- Handle JSONB `config_data` field updates (nested object changes)
- Handle top-level configuration fields (`state`, `config_name`, etc.)
- Unified update pattern for both types of changes

#### Save Strategy
- Single save button triggers complete configuration overwrite
- API call to `apiClient.updateConfig()` with entire modified configuration
- Reset dirty state on successful save
- Handle save conflicts and validation errors gracefully

#### Benefits
- Component isolation with shared state
- Simple coordination without state duplication
- Handles complex nested configuration updates
- Maintains real-time operational data separately from configuration edits
- Clean separation between configuration (user settings) and operational data (SSE updates)

### Implementation Phases

#### Phase 1: Data Foundation ✅ COMPLETE
- Verify all API endpoints work correctly
- Test SSE streams and real-time filtering
- Implement multi-bot switching with `selectedConfigId`
- Ensure local state patterns are robust
- Complete centralized state management architecture

#### Phase 2: Layout & Design System (IN PROGRESS)

**Phase 2A: Component Architecture**

```
/frontend/app/forge/components/
├── layout/
│   ├── Header.tsx           # App branding, theme toggle, user profile
│   ├── BotRail.tsx          # Left sidebar with bot list
│   ├── MobileNav.tsx        # Bottom nav for mobile
│   ├── TabNavigation.tsx    # Monitor/Configure tab switcher
│   └── UserProfile.tsx      # Profile dropdown (logout, settings, subscription)
│
├── monitor/
│   ├── ActivationBar.tsx    # Bot controls, pipeline ticker, countdown
│   ├── PipelineTicker.tsx   # Extraction→Decision→Trading visualization
│   ├── MetricsBar.tsx       # KPI cards (balance, P&L, win rate)
│   ├── PositionsTable.tsx   # Active trades with real-time P&L
│   ├── DecisionFeed.tsx     # List of AI decisions
│   └── DecisionCard.tsx     # Individual decision with expandable reasoning
│
├── configure/
│   ├── SaveConfig.tsx       # Save/Cancel bar with unsaved changes indicator
│   ├── ConfigTabs.tsx       # Sub-tabs for configuration sections
│   ├── DecisionEditor.tsx   # Strategy editing with locked sections
│   ├── MarketDataSelector.tsx # Data source/indicator selection
│   ├── RiskControls.tsx     # Position sizing, stop loss settings
│   ├── LLMConfig.tsx        # Provider selection, API keys
│   └── TradingSetup.tsx     # Exchange config (disabled for MVP)
│
└── shared/
    ├── ThemeToggle.tsx      # Sun/moon theme switcher
    ├── Toast.tsx            # Notification toasts
    ├── EmptyState.tsx       # Empty state guidance
    ├── LoadingSkeleton.tsx  # Loading placeholders
    └── Countdown.tsx        # Next run countdown timer
```

**Phase 2B: Layout Shell Implementation** ✅ **COMPLETE**
- [x] Create mobile-first responsive layout shell (header, main, sidebar)
- [x] Implement dark/light mode theming system with CSS variables and charcoal/bone palette
- [x] Add sun/moon theme toggle in header with localStorage persistence
- [x] Add user profile dropdown in header (logout, settings, subscription)
- [x] Build responsive bot rail component (hidden mobile, visible desktop)
- [x] Create mobile bottom navigation for bot switching
- [x] Establish consistent spacing scale and typography system
- [x] **ActivationBar Implementation**: Professional bot status/control bar above tabs
  - [x] Real data integration (account balance, frequency, status messages)
  - [x] Agent-specific color system for pipeline visualization
  - [x] Braille spinner animation during execution phases
  - [x] Responsive 3-group layout with proper spacing constraints
  - [x] Containerized design matching component standards

**Phase 2C: Core Monitor Components** ✅ **COMPLETE**
- [x] Build ActivationBar component (sticky, shows bot status and controls)
- [x] Create Monitor/Configure tab system replacing current layout
- [x] Implement PipelineTicker for extraction→decision→trading visualization
- [x] Add responsive breakpoint utilities and mobile-first styling
- [x] Create empty state components for all major sections
- [x] **Build MetricsBar component** - Professional KPI grid layout
  - [x] 2x2 grid layout (optimized for side-by-side placement)
  - [x] Individual KPI cards with trend indicators (TrendingUp/TrendingDown icons)
  - [x] Color-coded values (emerald=profit, rose=loss, consistent throughout)
  - [x] Real data integration: portfolio return, daily P&L, win rate, open positions
- [x] **Create PositionsTable component** - Professional table structure
  - [x] Proper HTML table with thead/tbody structure (`min-w-full` responsive)
  - [x] Real-time P&L updates via SSE (no simulated data)
  - [x] Empty state with proper colspan and helpful guidance
  - [x] Color-coded P&L columns with +/- indicators
  - [x] Mobile card transformation (no horizontal scroll on mobile)
- [x] **Build DecisionFeed component** - AI decision history
  - [x] Carousel of recent decisions with confidence scores and actions
  - [x] Expandable reasoning pattern (150 char truncation with show more/less)
  - [x] Badge system for action types (ENTER LONG/SHORT, EXIT, WAIT)
  - [x] Real decision data only - no mock/placeholder content
  - [x] Auto-advance to newest decision when new decisions arrive
- [x] **Implement nested grid layout** - Professional dashboard structure
  - [x] 2-column top section: DecisionFeed + MetricsBar side-by-side on lg+
  - [x] Full-width sections below: PositionsTable spans complete width
  - [x] Left-aligned layout removes awkward centering on wide screens
  - [x] Mobile responsive: all components stack vertically on smaller screens
- [x] Complete progressive duplication of all MonitorContent functionality

**Phase 2D: Bot Management & Mobile UX** (FOCUSED SCOPE)
- [ ] **Bot creation and management actions**
  - [ ] "+" New bot button functionality in BotRail
  - [ ] Bot deletion/archiving capabilities
  - [ ] Bot duplication for strategy variations
  - [ ] Bot renaming interface
- [ ] **Mobile drawer behavior for bot switching**
  - [ ] Transform BotRail into mobile drawer on small screens
  - [ ] Smooth slide-in/out animations
  - [ ] Overlay background with proper z-index
  - [ ] Touch-friendly bot selection interface

#### Phase 3: Monitor Experience Enhancement

**Phase 3A: Enhanced Interactions**
- [ ] **Chart placeholder component** for future performance visualization
  - [ ] Simple bordered container matching design system
  - [ ] Clear labeling for future P&L/equity charts
  - [ ] No mock data - just container structure

**Phase 3B: Visual Polish & Responsiveness**
- [ ] **Professional color coding system**
  - [ ] Consistent profit/loss indicators throughout (emerald-400/rose-400)
  - [ ] Trend arrow icons (TrendingUp/TrendingDown) for all metrics
  - [ ] Status color consistency (success/warning/danger palette)
- [ ] **Mobile-responsive enhancements**
  - [ ] Table→card transformations for narrow screens
  - [ ] Optimized touch targets and spacing
  - [ ] Mobile-friendly decision card layouts
- [ ] **Micro-interactions and feedback**
  - [ ] Subtle hover states and transitions
  - [ ] Loading states with skeleton screens
  - [ ] Toast notifications for bot actions
  - [ ] Button press feedback and states

#### Phase 4: Configure Experience

**Phase 4A: Configuration Architecture**
- [ ] Implement centralized config update system with dirty state tracking
- [ ] Create save/publish flow with validation
- [ ] Build configuration tabs (Decision, Market Data, Risk, Trading, LLM)
- [ ] Add draft mode with auto-save functionality
- [ ] Implement configuration validation and error handling

**Phase 4B: Configuration Components**
- [ ] Build DecisionEditor with locked/editable sections
- [ ] Create MarketDataSelector with hierarchical data source structure
- [ ] Implement RiskManagement controls with preview
- [ ] Add LLMConfiguration with provider selection and testing
- [ ] Build advanced JSON editor for power users

#### Phase 5: Progressive Enhancement

  
**Phase 5A: Visual Polish & Responsiveness**
- [ ] **Professional color coding system**
  - [ ] Consistent profit/loss indicators throughout (emerald-400/rose-400)
  - [ ] Trend arrow icons (TrendingUp/TrendingDown) for all metrics
  - [ ] Status color consistency (success/warning/danger palette)
- [ ] **Mobile-responsive enhancements**
  - [ ] Table→card transformations for narrow screens
  - [ ] Optimized touch targets and spacing
  - [ ] Mobile-friendly decision card layouts
- [ ] **Micro-interactions and feedback**
  - [ ] Subtle hover states and transitions
  - [ ] Loading states with skeleton screens
  - [ ] Toast notifications for bot actions
  - [ ] Button press feedback and states

**Phase 5B: Advanced Features**
- [ ] Add test-run functionality for strategy validation
- [ ] Implement configuration versioning and diff viewer
- [ ] Create strategy templates and presets
- [ ] Add import/export configuration functionality
- [ ] Build bot duplication and cloning features

**Phase 5C: Performance & Polish**
- [ ] Optimize for multiple bots with virtualization if needed
- [ ] Add keyboard shortcuts for power users
- [ ] Implement search and filtering for decisions and trades
- [ ] Add comprehensive accessibility features
- [ ] Create comprehensive error boundaries and fallbacks

### Design System Specifications

#### Responsive Breakpoints
- **Mobile**: `< 768px` - Single column, bottom nav, drawer for bots
- **Tablet**: `768px - 1024px` - Two column, side rail visible
- **Desktop**: `1024px+` - Three column layout with expanded rail

#### Color System (Dark/Light Mode with Charcoal/Bone Palette)
```css
/* Dark Mode (Primary) */
[data-theme="dark"] {
  --bg-primary: #161618;      /* charcoal-900 */
  --bg-secondary: #1f1f23;    /* charcoal-800 */
  --bg-tertiary: #2a2a30;     /* charcoal-700 */
  --text-primary: #e3e5e6;    /* bone-200 */
  --text-secondary: #d6d8da;  /* bone-300 */
  --border: #36363d;          /* charcoal-600 */
}

/* Light Mode */
[data-theme="light"] {
  --bg-primary: #f0f2f3;      /* bone-100 */
  --bg-secondary: white;
  --bg-tertiary: #e3e5e6;     /* bone-200 */
  --text-primary: #1f1f23;    /* charcoal-800 */
  --text-secondary: #2a2a30;  /* charcoal-700 */
  --border: #d6d8da;          /* bone-300 */
}

/* Agent Colors (Same in Both Modes) */
:root {
  --agent-extraction: #38a1c7; /* Blue - data extraction */
  --agent-decision: #2cbe77;   /* Green - AI decision making */
  --agent-trading: #be6a47;    /* Orange - trade execution */
  --success: #10b981;          /* emerald-400 - Profit, success, active */
  --danger: #f43f5e;           /* rose-400 - Loss, error, inactive */
  --warning: #f97316;          /* Warning, pending */
}

/* Theme Toggle Component */
.theme-toggle {
  @apply flex h-8 w-8 items-center justify-center rounded-full border
         border-charcoal-600 bg-charcoal-800 hover:bg-charcoal-700
         transition-colors;
}
```

#### Component Architecture
- **Local state only** - No global stores, all state in page component
- **Prop drilling patterns** - Clean component contracts with focused responsibilities
- **Compound components** - Related components grouped together (e.g., `<BotRail.Item>`)
- **Mobile-first responsive** - Components adapt to screen size automatically
- **SSE integration** - Real-time updates flow through existing patterns





example SSE payload:
id: 1
event: dashboard
data: {"bots": [{"config_id": "18665f58-fb3c-4655-a648-449427be0073", "user_id": "00000000-0000-0000-0000-000000000000", "config_name": "ggShot-filter", "state": "active", "config_data": {"user_id": "00000000-0000-0000-0000-000000000000", "config_id": "18665f58-fb3c-4655-a648-449427be0073", "created_at": "2025-09-11T19:52:47.207740+00:00", "updated_at": "2025-09-12T00:17:25.217798", "config_data": {"trading": {"leverage": 1, "execution_mode": "paper", "exchange_config": {"api_key": "", "secret_key": "", "exchange_type": "cex", "selected_exchange": "binance"}, "position_sizing": {"method": "fixed_usd", "account_percent": 5, "fixed_amount_usd": 100, "max_position_percent": 10}, "risk_management": {"max_positions": 1, "max_daily_loss_usd": 500, "default_stop_loss_percent": 5, "default_take_profit_percent": 10}}, "decision": {"user_prompt": "## Pillar 0: Market Regime Analysis\nObjective: Filter out choppy/ranging markets where breakout signals frequently fail\n\nIndicators:\n- Aroon (14-period): Trend vs ranging detection\n  - Analysis: When both Aroon Up and Aroon Down are in middle range (30-70), market is consolidating. When one line is high (> 70) while the other is low (< 30), market is trending strongly\n  - Critical Flag: Both Aroon lines between 30-70 indicates HIGH RISK for ggShot signals\n- ADX (14-period): Trend strength confirmation\n  - Analysis: ADX > 25 indicates strong trending conditions, ADX < 20 suggests weak/ranging market\n  - Context: Low ADX combined with middle-range Aroon confirms dangerous ranging conditions\n\nCritical Logic: ggShot signals are designed for breakout/momentum scenarios:\n- Highest Risk: Aroon ranging (both 30-70) AND ADX < 20 (weak trend)\n- High Risk: Either Aroon ranging OR ADX < 20\n- Low Risk: Strong Aroon trend (one >70, other <30) AND ADX > 25\n\n### Pillar 1: Signal Confirmation  \nObjective: Seek confluence of evidence supporting the signal's direction\n\nIndicators:\n- RSI Multi-Timeframe Analysis:\n  - Signal timeframe RSI: Momentum confirmation for entry timing\n  - Analysis: For LONG signals, RSI 40-60 is ideal (not oversold, room to run). For SHORT signals, RSI 40-60 is also ideal\n  - Avoid: RSI extremes (>80 or <20) suggest overextension risk\n- Bollinger Band Position:\n  - Price position relative to bands confirms signal direction\n  - Analysis: For LONG signals, price approaching or touching lower band then bouncing supports upward move. For SHORT signals, price at upper band supports downward move\n  - Context: Signals in middle of bands have less directional conviction\n\n### Pillar 2: Broader Context\nObjective: Ensure trade is well-positioned and has room to run\n\nIndicators:\n- Multi-Timeframe RSI Context:\n  - Compare signal timeframe RSI with higher timeframe (4h) RSI\n  - Analysis: Higher timeframe overbought (RSI > 70) for LONG signals is a significant contradiction. Higher timeframe oversold (RSI < 30) for SHORT signals is a contradiction\n  - Ideal: Both timeframes showing non-extreme RSI (30-70 range)\n- ADX Trend Strength:\n  - Confirms we're in a trending environment suitable for breakouts\n  - Analysis: ADX > 25 provides confidence that trends can sustain. ADX > 30 is very strong trending environment\n\n### Pillar 3: Tactical Caution\nObjective: Identify immediate risks that could stop out an otherwise good setup\n\nIndicators:\n- Bollinger Band Overextension:\n  - Statistical overextension detection\n  - Analysis: Prices far outside bands (beyond +2 sigma) indicate potential overextension with higher mean reversion risk\n  - Caution: Signals when price is already beyond bands carry higher reversal risk\n- ATR Volatility Assessment:\n  - Market volatility/choppiness measurement  \n  - Analysis: Exceptionally high ATR (relative to recent periods) indicates chaotic conditions that may increase stop-loss risk\n  - Context: Very low ATR might indicate upcoming volatility expansion\n\n## Decision Framework:\n- **HIGH CONFIDENCE (0.8-1.0)**: All pillars align - trending market (Aroon + ADX), RSI in good zone, no overextension, normal volatility\n- **MEDIUM CONFIDENCE (0.6-0.8)**: 3 of 4 pillars align, minor contradictions\n- **LOW CONFIDENCE (0.4-0.6)**: 2 of 4 pillars align, significant contradictions present\n- **WAIT (0.0-0.4)**: Major contradictions or ranging market conditions detected", "system_prompt": "You are an expert cryptocurrency trader analyzing {SYMBOL} at current price {CURRENT_PRICE}. Your analysis is based on the following market data:\n\n{MARKET_DATA}\n\nProvide clear, reasoned responses about trading actions. Format your response with clear sections for Decision, Confidence, and Reasoning.", "analysis_frequency": "signal_driven"}, "extraction": {"selected_data_sources": {"influencer_kol": {"timeframes": ["1h"], "data_points": []}, "onchain_analytics": {"timeframes": ["1h"], "data_points": []}, "technical_analysis": {"timeframes": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"], "data_points": ["RSI", "Aroon", "ADX", "BB", "ATR"]}, "signals_group_chats": {"timeframes": ["15m"], "data_points": ["ggshot"]}, "fundamental_analysis": {"timeframes": ["1d"], "data_points": []}, "news_and_regulations": {"timeframes": ["1d"], "data_points": []}, "sentiment_and_trends": {"timeframes": ["1h"], "data_points": []}}}, "llm_config": {"model": "deepseek-r1", "provider": "openai", "use_own_key": false, "use_platform_keys": true}, "config_type": "signal_validation", "selected_pair": "BTC/USDT", "schema_version": "2.1", "telegram_integration": {"listener": {"api_id": "", "enabled": false, "api_hash": "", "session_name": "ggbot_session", "source_channels": []}, "publisher": {"enabled": true, "bot_token": "7320956370:AAGMatLFf_myZxmfuN7v7EwToxBter_GHW0", "filter_channel": "-1002507736579", "message_template": "\ud83d\udd25 {ACTION} {SYMBOL} - Confidence: {CONFIDENCE}\n{REASONING}", "include_reasoning": true, "confidence_threshold": 0.7, "include_market_context": true}}}, "config_name": "ggShot-filter"}, "created_at": "2025-09-11T19:52:47.20774+00:00", "updated_at": "2025-09-13T12:53:24.365841+00:00", "execution_status": null, "status_color": "green", "status_message": "Monitoring markets...", "show_spinner": false, "next_run": null, "is_scheduled": true}], "positions": [], "decisions": [], "accounts": [{"config_id": "18665f58-fb3c-4655-a648-449427be0073", "account_id": "707adc89-0aa4-4593-b85c-eb2fdf16d960", "current_balance": 9899.82, "total_pnl": -0.06, "total_trades": 1, "win_trades": 0, "loss_trades": 1, "open_positions": 1, "updated_at": "2025-09-12T04:54:26.816468+00:00", "unrealized_pnl": 0.0, "daily_pnl": 0.0, "portfolio_return_pct": -0.0006000000000000001, "total_balance": 9899.82, "available_balance": 9899.82, "position_value": 0.0, "win_rate": 0.0, "avg_win": 0, "avg_loss": -0.06, "largest_win": 0, "largest_loss": -0.06, "sharpe_ratio": null}], "timestamp": "2025-09-13T17:01:32.12644+00:00"}


note from Sev: "is this the most elegant design? clean, simple, elegant? intutive? 

Let's walk through the user journey. User lands on the landing page, they hit launch app, they get taken to the create acc page, they create an acc and login, they land in this page, we create a new default settings ggbot for the user right away so they start with one ggbot, that's inactive, btw the start/stop button, I think we should rephrase to activate/deactivate, that's more what it actually is. So the user lands in, they get a very basic ggbot with 'factory settings'. They need to know where to go, what to do intuitively. There are two types of ggbots, autonomous_trading and signal_validation. The default is autonomous trading, which has an 'analysis frequency' basically how often the bot completes the pipeline, we'll set the default to 5 minutes. So the user can 'activate' their default ggbot, which will start the timer to the next run. But we should also have a way for them to get immediate satisfaction, by clicking a manual trigger button, to force a ggbot execution run immediately, overriding the schedule. Then they see things happening, the status that gets pulled in for the ggbot can be used to display cycling messages, we want them to feel like this bot is really alive, going through the 3 processes, extraction, decision and (if the decision is to enter a trade, which for the default bot always will be) trading. Then they need to see the decision, the AI will have 'reasoning' for it's decision, every time a ggbot executes it makes a decision, but it doesn't always make a trade, a lot of the time it will just 'wait', especially when it's monitoring an active trade. So the user needs to see these decisions, that's the first thing they'll be able to really see value in is how the AI used data and a strategy to reason about the market. Then, since the default ggbot has a very simple strategy (if RSI is below 50 enter long, if above 50 enter short) it will always enter a trade on the first go, whether the user manually tiriggers that or waits the 5 minutes for it to run scheduled. so then we need to see the trade, we want a notification the trade was entered, and we always want to be able to see active trades to see how they're doing. The are active trades should be in is maybe 1-10 trades. For autonomous_trading mode it will always be max one trade for now, but for signal validation mode it might be many trades. Ok so that's the onboarding and immediate dopamine hit of seeing a ggbot work, but this will not be a successfuly ggbot, so the next thing a user needs to do is start configuring their ggbot, it needs to be intuitive for how they edit it. THere's 3 main things they can edit. 1) Extraction, aka Market Data, the data sources and data points that get fed to the decision LLM. 2) Decision - the trading strategy, we have uneditable prompt structuring that gives the LLM general instructions and provides current prices, and a 'market data' section that includes all the selected datapoints that a user configures in the extraction section, so all the user has to do is add their trading strategy. The default strategy is what I described, simply to enter a trade based on RSI being above or below 50. So they will see that in the default trading strategy. So they need to understand that this is what really makes all the difference, a ggbots success or failure is based on the data points you give it and the strategy you give it for how to interpret those data points, the decision LLM will always output an ACTION, REASONING, and CONFIDENCE. user can't change that output instruction section either. So the system prompt, general instructions, market data, and output instructions are all set for the user and uneditable, then they just add the strategy section to customize behavior. So this needs to be prominent and clear. Finally the trading settings are like position sizing, exchange connections, and telegram publishing settings. I think the biggest challenge will be how to display market data options. Right now our system is extremely basic, we only have 20 data points, which are techincal indicators inside the techincal analysis data source. but this will grow fast. We'll be quickly adding 5-10 data sources, and idk what the data points for each of those will look like yet, but they could have all sorts of options. So how to not overwelm, make those selections feel easy. idk how exactly.... oh and then comes performance, we really just need to track account balance, and a chart with change over time, profit and loss, trade statstics and such.. but pretty minimal. Ultimately people just care about whether their ggbot is making money or not. OH and right now the MVP we're laucnhing will be paper trading ONLY. So we should have an exchange connection settings area set up, with a place to add API keys and such, but it will be turned off/hidden/unclickable or something for now. All ggbots get a paper trading account with $10k immediately. so showing the ggbot's balance is also a great thing to show. 

Ultimately I want this to be clean, elegant, minalist, taking what would normally be a very complex thing of building and deploying an AI trading agent, and just making it feel effortless."
