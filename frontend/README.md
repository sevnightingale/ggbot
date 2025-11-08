# ggbots Frontend - Forge Architecture

**Next.js 15 + TypeScript + Tailwind CSS + Supabase + Real-time SSE**

---

## 🚀 Current Status: PRODUCTION READY - FORGE ARCHITECTURE

### **✅ FORGE - COMPLETE AUTONOMOUS TRADING PLATFORM**
- **Architecture**: Clean local-state design with SSE real-time updates
- **Multi-Bot Management**: Native support for unlimited trading agents per user
- **Configuration System**: Complete sandboxed editing with premium feature gating
- **Authentication**: Full Supabase integration with permission-based access control
- **Real-time Data**: Live positions, decisions, and account tracking via Server-Sent Events
- **Permission System**: Comprehensive premium feature gatekeeping for monetization

### **✅ AUTHENTICATION & LANDING SYSTEM**
- **Landing Pages**: Modern marketing site with new-landing ready for deployment
- **Auth Flow**: Email/password signup → verification → dashboard access
- **Protected Routes**: Server-side session guards with automatic redirects
- **Permission Gates**: Subscription tier-based feature access control

---

## 🏗 Architecture Overview

### **Current Page Structure**
```
Production Pages:
├── /forge                    # Main application (Forge architecture)
├── /new-landing             # Modern landing page (ready to replace /landing)
├── /login                   # Supabase authentication (login)
├── /signup                  # Supabase authentication (signup)
└── /auth/callback           # Email verification handler

Legacy/Archive (Moved to /archive/):
├── frontend-dashboard       # Deprecated WebSocket-based dashboard
├── frontend-landing-components # Old landing page components
└── frontend-store          # Archived Zustand botStore complexity
```

### **Forge Architecture (Production)**
```
/forge/components/
├── layout/                  # Application shell
│   ├── Header.tsx          # Branding, theme toggle, user profile
│   ├── BotRail.tsx         # Multi-bot sidebar with management
│   ├── TabNavigation.tsx   # Monitor/Configure tab switching
│   ├── MobileNav.tsx       # Mobile responsive navigation
│   └── UserProfile.tsx     # Profile dropdown with subscription status
│
├── monitor/                 # Real-time operational dashboard
│   ├── ActivationBar.tsx   # Bot status/control with agent pipeline visualization
│   └── PositionsTable.tsx  # Live trading positions with real-time P&L
│
├── configure/               # Bot configuration system
│   ├── SaveConfigBar.tsx   # Bot type toggle + save/cancel with change tracking
│   ├── ConfigTabs.tsx      # Sub-navigation (Market Data | Signals | Strategy | Trade Settings)
│   ├── MarketDataSelector.tsx # Technical indicator selection with premium gates
│   ├── SignalsConfiguration.tsx # External signal sources (ggShot, Discord, etc.)
│   ├── StrategyEditor.tsx  # AI prompt editing with LLM provider selection
│   └── TradeSettings.tsx   # Position sizing, risk management, Telegram integration
│
└── shared/                  # Reusable components
    ├── ThemeToggle.tsx     # Dark/light mode switching
    ├── EmptyState.tsx      # Guidance for empty states
    └── LoadingSkeleton.tsx # Loading placeholders

/components/                 # Global components
├── tv-timeline.tsx         # TradingView activity timeline with P&L chart, markers, live status
├── bottom-sheet.tsx        # Framer Motion slide-up drawer for activity details
├── HelpWidget.tsx          # Floating help widget with Telegram community invite
├── SymbolSelector.tsx      # Symbol dropdown with search (141 validated pairs)
├── UpgradeModal.tsx        # Stripe checkout modal with monthly/annual pricing toggle
└── ValidationMessage.tsx   # Error/warning message component with icons

/components/ui/              # shadcn UI components
├── dialog.tsx              # Radix UI Dialog wrapper for modals
├── button.tsx              # Button component with variants
├── card.tsx                # Card layout component
├── badge.tsx               # Badge/pill component
└── input.tsx               # Input field component

/lib/                        # Core utilities
├── permissions.tsx         # Permission context with subscription checks
├── permission-gate.tsx     # Component for gating premium features
├── useTradeValidation.ts   # Trading settings validation hook
├── api.ts                  # API client with Stripe methods
├── theme.tsx               # Dark/light theme provider
└── supabase.ts             # Supabase client setup
```

---

## 🎯 Forge Architecture Highlights

### **Local State Design**
- **No Global Store**: Direct API types, no transformation layers
- **Multi-Bot Native**: `selectedConfigId` pattern with seamless switching
- **SSE Real-time**: Server-Sent Events replace complex WebSocket patterns
- **Sandboxed Editing**: Configuration changes isolated from operational display

### **Real-time Data Flow**
```typescript
// SSE connection with filtered data streams
const eventSource = new EventSource(`${apiUrl}/api/v2/dashboard/stream?user_id=${userId}`)

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data)

  // Filter for currently selected bot
  if (data.config_id === selectedConfigIdRef.current) {
    setPositions(data.positions)
    setAccounts(data.accounts)
    setExecutionStatus(data.execution_status)
  }
}
```

### **Configuration Architecture**
```typescript
// Sandboxed editing pattern
const [allBots, setAllBots] = useState<BotConfiguration[]>([])
const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null)
const [editingConfig, setEditingConfig] = useState<ConfigData | null>(null)
const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

// Centralized config updates with deep merging
const updateEditingConfig = (updates: Partial<ConfigData>) => {
  setEditingConfig(prev => ({
    ...prev,
    ...updates,
    // Deep merge for nested JSONB fields
    extraction: { ...prev?.extraction, ...updates.extraction },
    decision: { ...prev?.decision, ...updates.decision },
    trading: { ...prev?.trading, ...updates.trading }
  }))
  setHasUnsavedChanges(true)
}
```

---

## 📐 Forge Page Layout Architecture

### **Container Hierarchy**

```
<div className="min-h-screen bg-[var(--bg-primary)]">
  <Header />  // Fixed height: ~64px

  {/* 12-column grid container */}
  <div className="grid max-w-7xl grid-cols-12 gap-4 px-4 py-4 min-h-[calc(100vh-64px)]">

    {/* BotRail - LEFT COLUMN (25% width on desktop) */}
    <BotRail className="col-span-12 hidden md:col-span-3 md:block" />

    {/* Main Content - RIGHT COLUMN (75% width on desktop) */}
    <main className="col-span-12 md:col-span-9 flex flex-col pb-16 md:pb-0">
      <ActivationBar />        // Height: ~80-120px (dynamic based on status)
      <TabNavigation />        // Height: ~48px

      {/* Tab Content Area */}
      <div className="flex-1 mt-4 pb-32">
        {activeTab === 'monitor' ? (
          <div className="space-y-4">
            <TVTimeline variant="embedded" />  // Height: 600px fixed
            <PositionsTable />                 // Height: Variable (auto)
          </div>
        ) : (
          <ConfigureLayout />  // Height: Variable (scrollable)
        )}
      </div>
    </main>
  </div>

  <MobileNav className="md:hidden" />  // Fixed at bottom on mobile
</div>
```

### **Width & Spacing Constraints**

```typescript
// Container widths
max-w-7xl          // 1280px maximum container width
px-4               // 16px horizontal padding (mobile)
gap-4              // 16px grid gap between columns

// Column distribution (desktop)
BotRail:    col-span-3 (3/12 = 25%)  // ~320px @ 1280px container
Main:       col-span-9 (9/12 = 75%)  // ~960px @ 1280px container

// Timeline in main content
- Full width of main column: 960px available
- Embedded height: 600px fixed
- Enough space for readable TradingView chart
```

### **Height Constraints**

```typescript
// Viewport calculations
min-h-screen                     // 100vh (full viewport)
Header:                          // ~64px
Grid container:                  // min-h-[calc(100vh-64px)]

// Main content area
pb-32                            // 128px bottom padding (for readability)
Available for content:           // ~calc(100vh - 64px - 128px - 48px)
                                 // = ~calc(100vh - 240px) accounting for tabs

// Component heights
ActivationBar:      ~80-120px (dynamic)
TabNavigation:      ~48px
TVTimeline:         600px (embedded mode)
PositionsTable:     Variable (auto, based on open positions)
```

### **Responsive Breakpoints**

```typescript
// Tailwind breakpoints
sm:   640px   // Small devices
md:   768px   // Tablets (BotRail shows, grid activates)
lg:   1024px  // Desktops
xl:   1280px  // Large desktops
2xl:  1536px  // Extra large

// Layout behavior by breakpoint
Mobile (<md):
  - BotRail: hidden (shows as bottom drawer via MobileNav)
  - Main: col-span-12 (100% width)
  - Grid: Single column, vertical stacking
  - Timeline: 600px height maintained, responsive width

Tablet (md):
  - BotRail: col-span-3 (25%, shows sidebar)
  - Main: col-span-9 (75%)
  - Grid: 12-column activated
  - Timeline: 600px height, ~75% container width

Desktop (lg+):
  - Same as tablet
  - More horizontal space for chart readability
  - Timeline benefits from wider viewport
```

### **Component Spacing Pattern**

```typescript
// Vertical rhythm
space-y-4          // 16px vertical gap between major sections (Timeline, Positions)
mt-4               // 16px margin-top for tab content
pb-32              // 128px bottom padding for scroll-past readability

// Example: Monitor tab vertical spacing
<div className="space-y-4">
  <TVTimeline />     // 600px height
  {/* 16px gap */}
  <PositionsTable /> // Variable height
  {/* 128px bottom padding for scrolling past */}
</div>
```

### **Why pb-32 Bottom Padding?**

The 128px (`pb-32`) bottom padding on the main content area is intentional for **readability**:
- Allows users to scroll content past the viewport bottom
- Prevents PositionsTable from being cut off at screen edge
- Provides comfortable reading position for bottom content
- Mobile nav drawer (fixed position) doesn't overlap content

### **Mobile-Specific Behavior**

```typescript
// Mobile navigation drawer
<MobileNav className="md:hidden" />  // Only visible on mobile
- Fixed at bottom of viewport
- 70% width slide-in drawer for bot switching
- Touch gestures for closing (swipe right)
- Bottom tab triggers for opening

// Main content on mobile
- Full width (100%)
- Vertical stacking of all components
- Timeline maintains 600px height
- Responsive KPI grid (2 cols → 3 cols → 5 cols based on width)
```

---

## 🔐 Permission System & Monetization

### **Subscription Tier Architecture**
```typescript
// /lib/permissions.tsx - Complete permission context
interface PermissionContextType {
  userProfile: UserProfile | null
  loading: boolean
  canAccess: (feature: string) => boolean
  hasSubscription: (tier: 'ggbase') => boolean
  hasPaidDataPoint: (dataPoint: string) => boolean
}

// Permission gates in components
const { canAccess } = usePermissions()

// Premium LLM models
const isLocked = !canAccess('premium_llms')
<button disabled={isLocked} className={isLocked ? 'opacity-60 cursor-not-allowed' : ''}>
  {isLocked && <LockIcon />} OpenAI GPT-4
</button>

// ggShot signals
const canUseSignals = canAccess('ggshot')
<Toggle enabled={canUseSignals && isGgShotEnabled} />
```

### **Upgrade Flow (Stripe Integration)**
```typescript
// PermissionGate with UpgradeModal
import { UpgradeModal } from '@/components/UpgradeModal'

<PermissionGate feature="telegram_publishing">
  <TelegramSettings />
</PermissionGate>

// Auto-shows upgrade prompt with modal trigger:
// - Monthly/Annual pricing toggle
// - 14-day free trial messaging
// - Early adopter coupon input
// - Redirects to Stripe Checkout on confirm
```

### **Feature Gatekeeping**
- **Multiple Bots (10 vs 1)**: Requires Pro Plan subscription
- **High Frequency (5min vs 1h)**: Requires Pro Plan subscription
- **OpenAI GPT-4**: Requires `premium_llms` access (Pro Plan)
- **ggShot Signals**: Requires `ggshot` subscription (Pro Plan)
- **Telegram Publishing**: Requires `telegram_publishing` access (Pro Plan)
- **Platform LLM Keys**: Requires `platform_llm_keys` access (Pro Plan)

### **Stripe Integration**
```typescript
// API methods in /lib/api.ts
apiClient.createCheckoutSession({ plan: 'monthly', coupon: 'EARLY50' })
apiClient.createPortalSession() // For subscription management
```

**Pro Plan**: $29/month or $279/year (14-day free trial)
**Early Adopter**: 50% off for 6 months with code `EARLY50`

---

## 💻 Development & Deployment

### **Environment Setup**
```bash
# Development
cd /home/sev/ggbot/frontend
npm install
npm run dev          # http://localhost:3000

# Production Build
npm run build        # Test compilation
npm run lint         # Code quality check
```

### **Environment Variables**
```bash
# Supabase Authentication
NEXT_PUBLIC_SUPABASE_URL=https://ciinauxtnkweyebyhucl.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# V2 Backend API
NEXT_PUBLIC_V2_API_URL=https://ggbots-api.nightingale.business

# Domain Configuration
# ggbots.ai → Landing page
# app.ggbots.ai → Forge application
```

### **Deployment**
```bash
# Automatic deployment via Vercel + GitHub
git push origin main

# Vercel automatically deploys:
# - Frontend: https://ggbot-app.vercel.app
# - Production: https://app.ggbots.ai
```

---

## 🗂 Legacy Components (Archived)

### **Moved to Main Archive** (`/archive/`)
- **`frontend-dashboard/`** - WebSocket-based dashboard with Zustand complexity
- **`frontend-store/`** - Global botStore with 600+ lines and transformation layers
- **`frontend-landing-components/`** - Original landing page components

### **Unused Directories** (Consider for cleanup)
```
/components/
├── /ui/                     # Generic UI components (potentially useful)
├── /auth/                   # Authentication components (check if used)
├── /trades/                 # Trading-specific components (may overlap with Forge)
├── /charts/                 # Chart components (future integration)
└── /bot/                    # Bot-specific components (likely superseded by Forge)

/emails/                     # Email templates (keep for notifications)
/types/                      # TypeScript definitions (may have useful types)
/hooks/                      # Custom hooks (check for Forge overlap)
```

### **Cleanup Recommendations**
1. **Audit `/components/ui/`** - May contain reusable components for Forge
2. **Review `/components/auth/`** - Check if used by login/signup pages
3. **Evaluate `/components/trades/` and `/components/charts/`** - Potential future integration
4. **Check `/hooks/`** - May contain useful hooks not implemented in Forge
5. **Review `/types/`** - Consolidate with Forge type definitions

---

## 🎨 Design System

**Ceremonial Brutalism** - Inspired by trade37, creating a premium, sophisticated trading environment with unified brass accents.

### **Theme Architecture**
```typescript
// /lib/theme.tsx - Complete dark/light mode system
const [theme, setTheme] = useState<'light' | 'dark'>('dark')

// CSS Variables - Ceremonial Brutalism Palette
[data-theme="dark"] {
  --bg-primary: #0b0b0c;       /* obsidian - deep black */
  --bg-secondary: #141416;     /* carbon */
  --text-primary: #edebe7;     /* ivory - warm off-white */
  --accent: #c1a87d;           /* brass - primary accent */
  --border: #2a2a2d;           /* subtle borders */
}

[data-theme="light"] {
  --bg-primary: #f8f7f4;       /* warm parchment */
  --bg-secondary: #edebe7;     /* ivory background */
  --text-primary: #1a1816;     /* near-black with warmth */
  --accent: #8a7859;           /* dark brass accent */
  --border: #c8c4bc;           /* warm gray borders */
}
```

### **Typography** (2025-11-06 Update)
```typescript
// Premium editorial fonts
Display: Bodoni Moda serif      // Headlines, dramatic impact
Sans: Space Grotesk             // Body text, geometric clarity
Mono: IBM Plex Mono            // Technical data, code
```

### **Brass Pipeline System**
```css
:root {
  --agent-extraction: #d4bc91;  /* Light brass - extraction phase */
  --agent-decision: #c1a87d;    /* Medium brass - decision phase */
  --agent-trading: #a89168;     /* Dark brass - trading phase */
  --signal: #3ca6e0;            /* Signal blue */
  --ember: #d74a1f;             /* Ember red */
  --success: #10b981;           /* Profit/success (semantic) */
  --danger: #ef4444;            /* Loss/error (semantic) */
}
```

### **Icon System** (2025-11-06 Update)
All UI uses **Lucide React** icons (56 emojis replaced):
- Professional, scalable, stroke-based icons
- Tree-shakeable (only bundles used icons)
- Customizable size, color, stroke-width
- Brass accent coloring for active/selected states

**Example:**
```tsx
import { Bot, Settings, BarChart3 } from 'lucide-react'

<Bot className="h-5 w-5 text-[var(--accent)]" />
```

### **Design Philosophy**
- **Dark Mode:** "Obsidian and metal" - deep blacks with warm brass highlights
- **Light Mode:** "Parchment and stone" - aged paper warmth with rich dark brass
- **Unified Brand:** Consistent with trade37 championship platform
- **Premium Feel:** Editorial typography + ceremonial color palette

---

## 🚀 Production Features

### **Multi-Bot Management**
- **Unlimited Bots**: Create, duplicate, rename, delete trading agents
- **Bot Switching**: Seamless switching with isolated operational data
- **Real-time Status**: Live execution status with agent pipeline visualization
- **Account Isolation**: $10k paper trading accounts per bot configuration

### **Configuration System**
- **Market Data**: 21+ technical indicators with premium feature gating
- **Signal Sources**: ggShot integration with subscription gatekeeping
- **Strategy Editor**: AI prompt templates with LLM provider selection
- **Trading Settings**: Symbol selection (141 pairs), position sizing, risk management, Telegram integration

### **Real-time Monitoring**
- **Activity Timeline**: TradingView Lightweight Charts integration with P&L evolution, interactive activity markers, and live status indicators
- **Timeline Features**: Trade entries (↑↓ arrows), market queries (○), agent thoughts (○), wait periods (○) with click-to-expand details
- **Live Status**: Pulsing colored dot showing current agent state with countdown timers ("⏸ WAITING • Next check in 2m 15s")
- **KPI Header**: Real-time Balance, P&L, Trades, Win Rate metrics integrated into timeline view
- **Bottom Sheet**: Framer Motion drawer with comprehensive activity details, preprocessed market data, and markdown-rendered analysis
- **Live Positions**: Real-time P&L updates with color-coded performance in positions table
- **Execution Pipeline**: Visual extraction → decision → trading status tracking in activation bar

### **Trading Settings Validation**
```typescript
// Real-time validation with error/warning states
import { useFieldValidation, ValidationRules } from '@/lib/useTradeValidation'
import { ValidationMessage } from '@/components/ValidationMessage'

const leverageValidation = useFieldValidation(leverage, ValidationRules.leverage)

<input
  value={leverage}
  className={leverageValidation.error ? 'border-red-500' : 'border-gray-300'}
/>
<ValidationMessage error={leverageValidation.error} warning={leverageValidation.warning} />
```

**Validated Fields**:
- **Leverage**: 1-100 (⚠️ warning if >20x)
- **Stop Loss**: 1-50%
- **Take Profit**: 1-500%
- **Position Size (%)**: 0.1-100% (⚠️ warning if >50%)
- **Position Size (USD)**: 10 - account balance
- **Max Positions**: 1-50 (⚠️ warning if >10)

**Validation Behavior**:
- 🔴 **Errors**: Red borders + error message + blocks save
- 🟡 **Warnings**: Yellow borders + warning message + allows save
- ✅ **Valid**: Normal borders + no message

---

## ✅ Production Readiness Checklist

### **Core Architecture**
- [x] Forge architecture with local state design
- [x] Multi-bot management with seamless switching
- [x] Real-time SSE data streams with proper filtering
- [x] Sandboxed configuration editing with change detection
- [x] Permission system with subscription tier gatekeeping

### **Authentication & Security**
- [x] Supabase authentication with email verification
- [x] Protected routes with server-side session guards
- [x] Permission-based feature access control
- [x] API client with JWT token authentication

### **User Experience**
- [x] Responsive design with mobile navigation
- [x] Dark/light theme system with localStorage persistence
- [x] Loading states, empty states, and error boundaries
- [x] Professional design system with agent color scheme
- [x] Trading settings validation with error/warning feedback
- [x] Real-time input validation preventing invalid configurations

### **Monetization & Subscriptions**
- [x] Stripe integration (checkout, webhooks, billing portal)
- [x] Pro Plan pricing and feature differentiation
- [x] UpgradeModal with monthly/annual toggle
- [x] Subscription status display in UserProfile
- [x] Permission gates triggering upgrade flow
- [x] Early adopter coupon system

### **Integration & Deployment**
- [x] V2 backend API integration with real-time data
- [x] Vercel deployment with custom domain routing
- [x] Environment variable configuration
- [x] Production build optimization

---

## 📊 CodeScout Analysis & Recommendations

### **✅ Production Status: GOOD**
**Overall Rating**: 🟢 Production-ready with clean Forge architecture

**Recent Fixes Applied:**
- ✅ **Activity Timeline Integration** (2025-11-08): Replaced DecisionFeed + PerformanceChart with full-width TVTimeline in Monitor tab
- ✅ **Critical routing fix**: Updated middleware to redirect `app.ggbots.ai` to `/forge` instead of non-existent `/dashboard`
- ✅ **Legacy API cleanup**: Removed duplicate API client, single authenticated client architecture
- ✅ **Complete component cleanup**: All unused legacy components archived to `/archive/frontend-*`
- ✅ **Symbol validation system**: 141 supported trading pairs with dropdown + search functionality
- ✅ **Help widget integration**: Floating community support with Telegram group access
- ✅ **UX improvements**: Symbol selection moved from locked exchange section to accessible location
- ✅ **Stripe subscription system**: Complete monetization with Pro Plan ($29/mo), checkout flow, webhooks, billing portal
- ✅ **Trading settings validation**: Real-time error/warning feedback for 6 critical trading parameters

### **🔴 Critical Issues (RESOLVED)**
- **Routing Architecture**: ✅ Fixed middleware redirecting to non-existent dashboard route
- **Duplicate API Clients**: ✅ Archived legacy client, clean single API architecture
- **Legacy References**: ✅ No WebSocket, botStore, or legacy component imports remain

### **🟡 Code Quality Improvements (Medium Priority)**

#### **Component Architecture**
- **Large Component Refactoring**: Break down 970-line ForgeApp component into smaller hooks:
  ```typescript
  hooks/
    ├── useAuth.ts           // Authentication state management
    ├── useBotManagement.ts  // Bot CRUD operations and switching
    ├── useConfigEditing.ts  // Sandboxed configuration editing
    └── useRealTimeData.ts   // SSE connection and data streaming
  ```

#### **React Hook Dependencies**
- **Fix useEffect warnings**: Add missing dependencies in `/app/forge/page.tsx:414`
- **Use useCallback**: For stable function references in effect dependencies
- **Dependency optimization**: Review all useEffect hooks for proper dependency arrays

#### **Code Cleanup**
- **Test page cleanup**: Remove commented code in `/app/test/page.tsx`
- **Unused imports**: Audit for any remaining unused import statements
- **Type safety**: Add more specific types for API responses and component props

### **🟢 Code Quality Improvements (Low Priority)**

#### **Error Handling & Resilience**
- **Error boundaries**: Add React error boundaries around major components
- **SSE reconnection**: Implement automatic reconnection logic for Server-Sent Events
- **API error handling**: Enhanced error handling with user-friendly messages

#### **Performance Optimizations**
- **Component memoization**: Add React.memo for expensive components
- **API response caching**: Implement intelligent caching for configuration data
- **Bundle optimization**: Code splitting for new-landing components

#### **Developer Experience**
- **Type definitions**: More specific TypeScript interfaces for complex data structures
- **Component documentation**: JSDoc comments for complex component props
- **Testing setup**: Unit tests for critical Forge components

### **🎯 Implementation Priorities**

#### **High Priority (Week 1)**
1. **Component refactoring** - Extract hooks from large ForgeApp component
2. **useEffect dependencies** - Fix React hook warnings
3. **Error boundaries** - Add resilience to component failures

#### **Medium Priority (Week 2-3)**
1. **SSE improvements** - Reconnection logic and error handling
2. **Type safety** - Enhanced TypeScript coverage
3. **Performance optimization** - Component memoization and caching

#### **Low Priority (Month 2)**
1. **Advanced charts** - TradingView integration for performance visualization
2. **Mobile UX polish** - Complete mobile drawer behavior for bot switching
3. **Analytics integration** - User behavior tracking and conversion optimization
4. **Notification system** - Email/SMS alerts for bot events and performance

### **🔒 Security & Compliance Status**
- ✅ **No hardcoded secrets** - All credentials use environment variables
- ✅ **Proper authentication** - Supabase session management implemented correctly
- ✅ **API security** - Bearer token authentication with JWT validation
- ✅ **Permission gates** - Subscription-based feature access control

---

## 📊 TradingView Activity Timeline

### **Overview**

The Activity Timeline provides professional-grade trading analytics using TradingView Lightweight Charts v4.2.0. It displays P&L evolution over time with interactive markers for all agent activities, live status indicators, and comprehensive market data insights.

**Dual-Mode Component**:
- **Standalone**: `aster.ggbots.ai` → `/view/{config_id}` (full viewport, 100vh - 280px)
- **Embedded**: `/forge` Monitor tab (fixed 600px height, full width)

**Integration** (2025-11-08): Timeline replaced DecisionFeed + PerformanceChart in Forge Monitor tab, consolidating KPIs, P&L chart, and activity history into single comprehensive view.

### **Architecture**

```typescript
/components/
├── tv-timeline.tsx          # Main timeline component (870 lines)
│                            # - variant prop: 'standalone' | 'embedded'
│                            # - Self-contained: own data fetching, polling
└── bottom-sheet.tsx         # Activity detail drawer (100 lines)

/app/view/[config_id]/       # Standalone route
└── page.tsx                 # <TVTimeline variant="standalone" />

/app/forge/page.tsx          # Embedded in Monitor tab
└── Monitor tab              # <TVTimeline variant="embedded" />
```

### **Key Features**

#### **1. TradingView Chart Integration**
- **Library**: TradingView Lightweight Charts v4.2.0 (NOT v5 - API breaking changes)
- **Chart Type**: Line series with brass color (#C9A962), 2px stroke width
- **Data**: P&L snapshots from trade closes + unrealized P&L carry-forward between activities
- **Y-Axis**: Formatted with `$` symbol, automatic scaling
- **X-Axis**: Time-based with automatic date formatting
- **Interaction**: Crosshair mode with dashed brass lines (#C9A962)

**Chart Configuration**:
```typescript
const chart = createChart(container, {
  layout: {
    background: { type: ColorType.Solid, color: '#1A1D23' }, // VIBE.carbon
    textColor: '#3a3a3c', // VIBE.hair
  },
  rightPriceScale: { borderColor: '#3a3a3c' },
  timeScale: { borderColor: '#3a3a3c', timeVisible: true, secondsVisible: false },
  localization: {
    priceFormatter: (price: number) => `$${price.toFixed(2)}`,
  },
  crosshair: {
    mode: 1, // Magnet to data points
    vertLine: { color: '#C9A962', width: 1, style: LineStyle.Dashed },
    horzLine: { color: '#C9A962', width: 1, style: LineStyle.Dashed },
  },
})

const lineSeries = chart.addLineSeries({
  color: '#C9A962', // VIBE.brass
  lineWidth: 2,
  priceLineVisible: false, // Hide dashed price line
})
```

#### **2. Activity Markers**

**Marker Types** (sorted chronologically, grouped by timestamp):
- **Trade Entries**:
  - Long: Green arrow up (▲, #16a34a, belowBar, size: 2)
  - Short: Red arrow down (▼, #dc2626, aboveBar, size: 2)
- **Agent Thoughts**: Brass circles (●, rgba(193,168,125,0.6), aboveBar, size: 0.5)
- **Market Queries**: Blue circles (●, rgba(60,166,224,0.5), belowBar, size: 0.5)
- **Agent Waits**: Ivory circles (●, rgba(237,235,231,0.4), belowBar, size: 0.5)

**Priority System**: When multiple activities occur at same timestamp, show single marker by priority:
1. Trade entries (long/short)
2. Agent thoughts
3. Market queries
4. Agent waits

**Critical Implementation Detail**: Markers must be sorted by time in ascending order or they disappear on zoom:
```typescript
markers.sort((a, b) => (a.time as number) - (b.time as number))
lineSeries.setMarkers(markers)
```

#### **3. Live Status Indicator**

Replaces static "ARENA STATUS • DATE" line with real-time agent status.

**Display Format**:
```
[Pulsing Dot] STATUS TEXT
```

**Status Types**:
- `⏸ WAITING • Next check in 2m 15s` (ivory dot) - countdown to next check
- `↑ LONG ENTERED • 3m ago` (green dot) - time since trade entry
- `↓ SHORT ENTERED • 1m ago` (red dot) - time since trade entry
- `📊 QUERIED MARKET • 5m ago` (blue dot) - time since query
- `💭 ANALYZING • 30s ago` (brass dot) - time since thought

**Implementation**:
```typescript
// Track latest activity
const [latestActivity, setLatestActivity] = useState<Activity | null>(null)
const [statusText, setStatusText] = useState<string>('')

// Update every second
useEffect(() => {
  if (!latestActivity) return

  const updateStatus = () => {
    const now = new Date()
    const activityTime = new Date(latestActivity.timestamp)

    // For agent_wait, show countdown
    if (latestActivity.type === 'agent_wait' && latestActivity.data.details?.next_check_at) {
      const nextCheck = new Date(String(details.next_check_at))
      const remainingMs = nextCheck.getTime() - now.getTime()
      const mins = Math.floor(remainingMs / 60000)
      const secs = Math.floor((remainingMs % 60000) / 1000)
      setStatusText(`⏸ WAITING • Next check in ${mins}m ${secs}s`)
    } else {
      // For others, show time ago
      const diffMs = now.getTime() - activityTime.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      const diffSecs = Math.floor((diffMs % 60000) / 1000)
      const timeAgo = diffMins > 0 ? `${diffMins}m ago` : `${diffSecs}s ago`
      setStatusText(`${icon} ${label} • ${timeAgo}`)
    }
  }

  updateStatus()
  const interval = setInterval(updateStatus, 1000)
  return () => clearInterval(interval)
}, [latestActivity])
```

**CSS Animation**:
```css
@keyframes statusPulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.2); }
}
```

#### **4. Interactive Hover Tooltips**

**Crosshair Detection**: Using `subscribeCrosshairMove()` to detect when user hovers near markers:
```typescript
chart.subscribeCrosshairMove((param) => {
  if (!param.time || !param.point) {
    setSelectedActivity(null)
    return
  }

  const timestamp = typeof param.time === 'number' ? param.time : parseFloat(param.time as string)
  const activities = activitiesMapRef.current.get(timestamp)

  if (activities && activities.length > 0) {
    setSelectedActivity(activities[0]) // Show first activity for tooltip
    setCrosshairPosition({ x: param.point.x, y: param.point.y })
  }
})
```

**Tooltip Content** (positioned at crosshair):
- Activity type badge with color
- Summary text (truncated to 100 chars for market queries)
- Symbol if available
- Markdown rendering for analysis/thoughts

#### **5. Bottom Sheet Detail View**

**Trigger**: Click on any marker opens bottom sheet with full details.

**Implementation**: Framer Motion slide-up drawer
```typescript
<BottomSheet
  isOpen={detailActivities.length > 0}
  onClose={() => setDetailActivities([])}
  title={detailActivities.length === 1 ? 'Activity Type' : `${detailActivities.length} Activities`}
>
  {/* Scrollable content with type-specific rendering */}
</BottomSheet>
```

**Features**:
- Drag handle at top (swipe down to dismiss on mobile)
- Max height: 80vh with overflow scroll
- Multiple activities shown as list when grouped
- Type-specific field rendering:
  - **Trade entries**: Symbol, side, entry price, leverage, confidence, SL/TP
  - **Market queries**: Timeframe, categories list, **preprocessed market data**
  - **Agent thoughts**: Markdown-rendered thought content
  - **Agent waits**: Wait duration, next check time, reason

**Market Data Display** (NEW - 2025-11-07):

Market queries now display the actual preprocessed data that agents receive:

```typescript
// Technical Indicators (brass boxes)
{details.market_data.technicals?.indicators &&
  Object.entries(indicators).map(([name, data]) => (
    <div className="p-3 rounded-lg bg-brass-10">
      <div className="font-semibold">{name}</div>
      <div>Value: {data.current.value}</div>
      <div>Trend: {data.context.trend.direction} ({data.context.trend.strength * 100}%)</div>
      <div>Patterns: {Object.keys(data.patterns).map(p => <Badge>{p}</Badge>)}</div>
    </div>
  ))
}

// Market Intelligence (blue boxes)
{details.market_data.market_intelligence &&
  Object.entries(intelligence).map(([source, data]) => (
    <div className="p-3 rounded-lg bg-signal-10">
      <div className="font-semibold">{source.toUpperCase()}</div>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  ))
}
```

This shows the **200-500 analytical fields** (trend strength, divergence patterns, momentum velocity, etc.) that influence agent decisions.

#### **6. Data Fetching & Management**

**API Endpoints**:
```typescript
// Balance series (P&L snapshots at trade closes)
GET /api/v2/activities/{config_id}/balance-series?mode=pnl

// All activities (trades, queries, thoughts, waits)
GET /api/v2/activities/{config_id}

// Bot metadata (name, status)
GET /api/v2/activities/{config_id}/metadata
```

**Data Transformation**:
1. Fetch balance series (P&L snapshots)
2. Fetch all activities (500+ items)
3. Sort activities chronologically
4. Merge with carry-forward P&L:
   ```typescript
   const chartPoints = []
   let currentPnl = 0.0

   for (const activity of sortedActivities) {
     // Update P&L if this activity has a balance point
     if (balanceMap.has(activity.timestamp)) {
       currentPnl = balanceMap.get(activity.timestamp)
     }

     chartPoints.push({
       time: timestamp,
       value: currentPnl, // Carry forward P&L
     })
   }
   ```

**Activity Grouping** (by timestamp):
```typescript
const activitiesMapRef = useRef<Map<number, Activity[]>>(new Map())

// Group activities by timestamp
const groupedByTimestamp = new Map<number, Activity[]>()
activities.forEach(activity => {
  const timestamp = Math.floor(new Date(activity.timestamp).getTime() / 1000)
  if (!groupedByTimestamp.has(timestamp)) {
    groupedByTimestamp.set(timestamp, [])
  }
  groupedByTimestamp.get(timestamp).push(activity)
})

// Create one marker per timestamp
groupedByTimestamp.forEach((activitiesAtTime, timestamp) => {
  // Priority: trades > thoughts > queries > waits
  const hasTradeLong = activitiesAtTime.some(a => a.type === 'trade_entry_long')
  if (hasTradeLong) {
    markers.push({ time: timestamp, shape: 'arrowUp', color: '#16a34a', size: 2 })
  }
  // ... etc
})
```

### **Integration with Backend**

#### **Enhanced Activity Logging** (2025-11-07)

Market query activities now capture the full preprocessed data:

**Backend** (`agent/mcp_server.py:220-234`):
```python
# Extract market data for activity logging
market_data = {}
if result.get('data', {}).get('technicals'):
    market_data['technicals'] = result['data']['technicals']
if result.get('data', {}).get('market_intelligence'):
    market_data['market_intelligence'] = result['data']['market_intelligence']

log_activity_safe(
    config_id=agent_context.config_id,
    user_id=agent_context.user_id,
    activity_type='market_query',
    details={
        'symbol': symbol,
        'categories': categories,
        'timeframe': timeframe,
        'market_data': market_data  # NEW: Full preprocessed data (200-500 fields)
    },
    related_symbol=symbol,
)
```

This enables complete transparency into agent decision-making by showing the exact data that influenced each trade.

### **Performance Considerations**

1. **Chart Initialization**: Heavy operation, only run once in useEffect
2. **Marker Updates**: Batch updates instead of individual calls
3. **Activity Grouping**: Pre-compute timestamp → activities map
4. **Memory**: Store only necessary data in refs, avoid duplicating chart data
5. **Rendering**: Use React.memo for BottomSheet to prevent unnecessary re-renders

### **Common Issues & Solutions**

**Issue**: Markers disappear when zooming in
**Solution**: Markers must be sorted by time in ascending order before calling `setMarkers()`

**Issue**: TypeScript errors with conditional rendering
**Solution**: Use ternary operators `? :` instead of `&&` for JSX conditionals to avoid `unknown` type

**Issue**: Chart doesn't resize on window change
**Solution**: Use ResizeObserver to detect container size changes and call `chart.applyOptions({ width, height })`

**Issue**: Bottom sheet not scrollable
**Solution**: Set `overflow-y-auto` on content div with max-height constraint

### **Future Enhancements**

- **Zoom to activity**: Double-click marker to zoom timeline to that time range
- **Filter by type**: Toggle visibility of different activity markers
- **Export data**: Download P&L chart as CSV or PNG
- **Annotations**: Add manual notes/markers to timeline
- **Comparison mode**: Overlay multiple bot timelines for performance comparison

---

**The Forge architecture represents a complete, production-ready autonomous trading platform with elegant local state management, comprehensive real-time features, and sophisticated permission-based monetization capabilities.** 🚀