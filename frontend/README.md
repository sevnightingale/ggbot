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
│   ├── MetricsBar.tsx      # Portfolio KPIs (balance, P&L, win rate, positions)
│   ├── DecisionFeed.tsx    # AI decision carousel with reasoning expansion
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
    setDecisions(data.decisions)
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

## 🔐 Permission System

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

### **Feature Gatekeeping**
- **OpenAI GPT-4**: Requires `premium_llms` access
- **ggShot Signals**: Requires `ggshot` subscription
- **Telegram Publishing**: Requires `telegram_publishing` access
- **Platform LLM Keys**: Requires `platform_llm_keys` access

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

### **Theme Architecture**
```typescript
// /lib/theme.tsx - Complete dark/light mode system
const [theme, setTheme] = useState<'light' | 'dark'>('dark')

// CSS Variables (charcoal/bone palette)
[data-theme="dark"] {
  --bg-primary: #161618;      /* charcoal-900 */
  --bg-secondary: #1f1f23;    /* charcoal-800 */
  --text-primary: #e3e5e6;    /* bone-200 */
  --border: #36363d;          /* charcoal-600 */
}

[data-theme="light"] {
  --bg-primary: #f0f2f3;      /* bone-100 */
  --bg-secondary: white;
  --text-primary: #1f1f23;    /* charcoal-800 */
  --border: #d6d8da;          /* bone-300 */
}
```

### **Agent Color System**
```css
:root {
  --agent-extraction: #38a1c7;  /* Blue - data extraction */
  --agent-decision: #2cbe77;    /* Green - AI decision making */
  --agent-trading: #be6a47;     /* Orange - trade execution */
  --success: #10b981;           /* emerald-400 - Profit/success */
  --danger: #f43f5e;            /* rose-400 - Loss/error */
}
```

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
- **Trading Settings**: Position sizing, risk management, Telegram integration

### **Real-time Monitoring**
- **Live Positions**: Real-time P&L updates with color-coded performance
- **AI Decisions**: Decision carousel with expandable reasoning and confidence scores
- **Portfolio Metrics**: Balance, daily P&L, win rate, and position tracking
- **Execution Pipeline**: Visual extraction → decision → trading status tracking

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

### **Integration & Deployment**
- [x] V2 backend API integration with real-time data
- [x] Vercel deployment with custom domain routing
- [x] Environment variable configuration
- [x] Production build optimization

---

## 🎯 Next Steps

### **Landing Page Deployment**
1. **Polish new-landing page** - Complete final touches and content
2. **Replace landing routing** - Archive current landing, promote new-landing
3. **Update domain routing** - Ensure ggbots.ai routes to new landing page

### **Frontend Optimization**
1. **Component Audit** - Review unused components in `/components/`
2. **Type Consolidation** - Merge useful types from `/types/` into Forge
3. **Hook Evaluation** - Extract useful hooks from `/hooks/` for Forge use
4. **Dependency Cleanup** - Remove unused dependencies from package.json

### **Feature Enhancements**
1. **Mobile UX Polish** - Complete mobile drawer behavior for bot switching
2. **Advanced Charts** - Integrate TradingView or custom chart components
3. **Notification System** - Email/SMS alerts for bot events and performance
4. **Analytics Integration** - User behavior tracking and conversion optimization

---

**The Forge architecture represents a complete, production-ready autonomous trading platform with elegant local state management, comprehensive real-time features, and sophisticated permission-based monetization capabilities.** 🚀