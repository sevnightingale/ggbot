# Onboarding Revamp - Typeform-Style Bot Creation

**Status**: 🔵 PLANNING
**Complexity**: Medium (~2-3 days)
**Priority**: High - First impression for new users

---

## Problem Statement

Current new user experience is poor:
1. User lands on `/forge` → automatic "Default ggbot" created with bad RSI strategy
2. No guidance, no personalization, no investment in the bot
3. BotCreationModal is too simple (just name + trading mode)
4. Strategy Advisor exists but isn't integrated into creation flow
5. Users have no idea what's happening or how anything works

## Solution

Transform BotCreationModal into a Typeform-style guided experience:
- One step at a time (not vertical form)
- Arrow navigation between steps
- Description-based strategy generation via LLM
- 3 archetype templates for quick start
- "Create & Test Run" triggers one free execution
- New users see modal immediately (non-closable until first bot created)

---

## User Flow

### New User (0 bots)
1. Lands on `/forge`
2. Modal auto-opens, X button hidden with tooltip "Create your first bot to continue"
3. Goes through 5-step flow
4. Creates bot → first run executes automatically
5. Sees bot in Monitor tab with alert "Bot created!"
6. Wants to run again → paywall

### Existing User
1. Clicks "+" in BotRail
2. Same 5-step flow (but modal is closable)
3. Creates bot → first run executes
4. Bot added to their collection

---

## Typeform Modal Steps

### Step 1: Name
```
┌─────────────────────────────────────────────────────┐
│ [●○○○○]                                   Step 1/5  │
├─────────────────────────────────────────────────────┤
│                                                     │
│   What should we call your ggbot?                   │
│                                                     │
│   ┌─────────────────────────────────────────────┐   │
│   │ ggbot 1                                     │   │ ← Pre-filled default
│   └─────────────────────────────────────────────┘   │
│                                                     │
│                                          [Next →]   │
└─────────────────────────────────────────────────────┘
```
- Default: "ggbot {n}" where n = existingBotCount + 1
- User can customize
- Validation: non-empty

### Step 2: Trading Mode
```
┌─────────────────────────────────────────────────────┐
│ [●●○○○]                                   Step 2/5  │
├─────────────────────────────────────────────────────┤
│                                                     │
│   How will your bot trade?                          │
│                                                     │
│   ┌─────────────────────────────────────────────┐   │
│   │ ⚡ Paper Trading                      [●]   │   │ ← Default selected
│   │    Practice with $10k virtual money         │   │
│   └─────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────┐   │
│   │ 🚀 Symphony Live                      [ ]   │   │
│   │    Real trades via Symphony.io              │   │
│   └─────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────┐   │
│   │ 🤖 AsterDEX                          [ ]   │   │
│   │    Real trades on AsterDEX                  │   │
│   └─────────────────────────────────────────────┘   │
│                                                     │
│                                [← Back]  [Next →]   │
└─────────────────────────────────────────────────────┘
```
- Default: Paper Trading
- Symphony/Aster require connection (show "Not connected" warning if needed)
- Symphony shows Agent ID input when selected

### Step 3: Symbol & Timeframe
```
┌─────────────────────────────────────────────────────┐
│ [●●●○○]                                   Step 3/5  │
├─────────────────────────────────────────────────────┤
│                                                     │
│   What will your bot trade?                         │
│                                                     │
│   Symbol                                            │
│   ┌─────────────────────────────────────────────┐   │
│   │ BTC/USDT                              [▼]   │   │ ← Default
│   └─────────────────────────────────────────────┘   │
│                                                     │
│   Analysis Frequency                                │
│   ┌─────────────────────────────────────────────┐   │
│   │ Every 1 hour                          [▼]   │   │ ← Default
│   └─────────────────────────────────────────────┘   │
│                                                     │
│                                [← Back]  [Next →]   │
└─────────────────────────────────────────────────────┘
```
- Symbol: Dropdown with search (141 pairs)
- Timeframe: 5m, 15m, 30m, 1h (default), 4h, 1d, 1w

### Step 4: Strategy Description
```
┌─────────────────────────────────────────────────────┐
│ [●●●●○]                                   Step 4/5  │
├─────────────────────────────────────────────────────┤
│                                                     │
│   Describe how you want your bot to trade           │
│                                                     │
│   ┌─────────────────────────────────────────────┐   │
│   │ A patient bot that waits for extreme fear   │   │
│   │ or greed, then fades the crowd...           │   │
│   │                                             │   │
│   │                                             │   │
│   └─────────────────────────────────────────────┘   │
│                                                     │
│   Or start with a proven archetype:                 │
│                                                     │
│   [The Contrarian]  [The Compass]  [The Arbiter]   │
│                                                     │
│                                [← Back]  [Next →]   │
└─────────────────────────────────────────────────────┘
```
- Textarea for free-form description
- Clicking archetype: applies full config, skips to final step
- If description provided: LLM generates strategy on submit

### Step 5: AI Model
```
┌─────────────────────────────────────────────────────┐
│ [●●●●●]                                   Step 5/5  │
├─────────────────────────────────────────────────────┤
│                                                     │
│   Choose your bot's AI brain                        │
│                                                     │
│   [Grok●] [Claude] [GPT] [Gemini] [DeepSeek] ...   │
│                                                     │
│   Reasoning Tier                                    │
│   ○ Economy  ● Standard  ○ Premium                  │
│   Fast & cheap   Balanced   Deep thinking           │
│                                                     │
│   💡 Estimated: ~$0.02/decision                     │
│                                                     │
│                     [← Back]  [Create & Test Run]   │
└─────────────────────────────────────────────────────┘
```
- Model grid with logos (reuse from StrategyEditor)
- Reasoning tier selector (no permission gating - that's legacy)
- Cost estimate based on selections
- Final button: "Create & Test Run"

---

## Backend Changes

### 1. New Endpoint: Strategy Generation

**`POST /api/v2/assistant/generate-strategy`**

```python
class GenerateStrategyRequest(BaseModel):
    description: str
    symbol: str = "BTC/USDT"
    timeframe: str = "1h"

class GenerateStrategyResponse(BaseModel):
    user_prompt: str  # Full trading strategy
    success: bool
    error: str | None = None
```

**Implementation** (`api/assistant.py`):
- Use Claude Haiku (cheap, fast)
- System prompt: "You are a trading strategy translator. Convert the user's description into a detailed trading strategy."
- Include symbol and timeframe context
- Output: Complete `user_prompt` text ready for decision engine

**Example Input/Output:**
```
Input: "A cautious bot that buys when everyone is scared and RSI is oversold"

Output: "You are a mean-reversion trader operating on 1-hour BTC/USDT charts.
You look for extreme fear conditions combined with technical oversold signals.

ENTRY CONDITIONS (Long):
- RSI below 30 (oversold)
- Sentiment indicators showing fear
- Price at or below lower Bollinger Band

ENTRY CONDITIONS (Short):
- RSI above 70 (overbought)
- Sentiment indicators showing greed
- Price at or above upper Bollinger Band

CONFIDENCE:
- 0.70+ when multiple indicators align
- 0.55-0.70 when partial alignment
- Pass below 0.55

RISK MANAGEMENT:
- Stop loss: Beyond recent swing high/low
- Take profit: Mean (20 EMA or middle Bollinger Band)"
```

### 2. Database: Add `first_run_used` Column

```sql
ALTER TABLE configurations ADD COLUMN first_run_used BOOLEAN DEFAULT FALSE;
```

### 3. Modify Orchestrate Endpoint

**`POST /api/v2/orchestrate/{config_id}`** (`ggbot.py`):

```python
# After loading config, before permission check:
config = await config_service.get_config(config_id, user_id)
user_profile = await user_service.get_profile(user_id)

# Allow first run for free users
if not user_profile.can_activate_bots:
    if not config.first_run_used:
        # Allow this one free run
        # Mark as used AFTER successful execution
        pass
    else:
        # Block - already used first run
        raise HTTPException(
            status_code=403,
            detail="Subscribe to run your bot again. Your first test run has been used."
        )

# ... execute normally ...

# On success, mark first run as used
if not config.first_run_used:
    await config_service.mark_first_run_used(config_id)
```

### 4. Remove Model Permission Gating (Legacy Cleanup)

**Files to update:**
- `frontend/app/forge/components/configure/StrategyEditor.tsx`
  - Remove `canAccess('premium_llms')` checks
  - Allow all users to select any model
- `frontend/lib/permissions.tsx`
  - Remove `premium_llms` feature if not used elsewhere

---

## Frontend Changes

### 1. BotCreationModal Refactor

**File**: `frontend/app/forge/components/modals/BotCreationModal.tsx`

**New State:**
```typescript
// Step tracking
const [currentStep, setCurrentStep] = useState(1)
const totalSteps = 5

// Form data
const [botName, setBotName] = useState('')
const [tradingMode, setTradingMode] = useState<TradingMode>('paper')
const [symphonyAgentId, setSymphonyAgentId] = useState('')
const [symbol, setSymbol] = useState('BTC/USDT')
const [timeframe, setTimeframe] = useState('1h')
const [description, setDescription] = useState('')
const [selectedArchetype, setSelectedArchetype] = useState<string | null>(null)
const [llmModel, setLlmModel] = useState('grok')
const [reasoningTier, setReasoningTier] = useState<'economy' | 'standard' | 'premium'>('standard')

// Loading states
const [isGenerating, setIsGenerating] = useState(false)
const [isCreating, setIsCreating] = useState(false)
```

**Step Navigation:**
```typescript
const canProceed = () => {
  switch (currentStep) {
    case 1: return botName.trim().length > 0
    case 2: return tradingMode !== null && (tradingMode !== 'symphony' || symphonyAgentId.trim())
    case 3: return symbol && timeframe
    case 4: return description.trim().length > 0 || selectedArchetype
    case 5: return llmModel
    default: return false
  }
}

const handleNext = () => {
  if (currentStep < totalSteps && canProceed()) {
    // If archetype selected on step 4, skip to final
    if (currentStep === 4 && selectedArchetype) {
      setCurrentStep(5)
    } else {
      setCurrentStep(prev => prev + 1)
    }
  }
}

const handleBack = () => {
  if (currentStep > 1) {
    setCurrentStep(prev => prev - 1)
  }
}
```

**Archetype Click Handler:**
```typescript
const archetypes = [
  { id: 'contrarian', name: 'The Contrarian', description: 'Mean-reversion trader that fades extremes' },
  { id: 'compass', name: 'The Compass', description: 'Macro regime trader following global trends' },
  { id: 'arbiter', name: 'The Arbiter', description: 'Confluence trader weighing all evidence' },
]

const handleArchetypeClick = (archetypeId: string) => {
  setSelectedArchetype(archetypeId)
  setDescription('') // Clear description since using template
  setCurrentStep(5) // Jump to final step
}
```

**Submit Handler:**
```typescript
const handleCreate = async () => {
  setIsCreating(true)

  try {
    let userPrompt: string
    let extractionConfig: object

    if (selectedArchetype) {
      // Use archetype config
      const config = getArchetypeConfig(selectedArchetype)
      userPrompt = config.userPrompt
      extractionConfig = config.extraction
    } else {
      // Generate from description
      setIsGenerating(true)
      const result = await apiClient.generateStrategy(description, symbol, timeframe)
      setIsGenerating(false)

      if (!result.success) {
        throw new Error(result.error || 'Failed to generate strategy')
      }

      userPrompt = result.user_prompt
      extractionConfig = getDefaultExtraction(timeframe)
    }

    // Build full config
    const configData = {
      schema_version: '2.1',
      config_type: 'scheduled_trading',
      trading_mode: tradingMode,
      symphony_agent_id: tradingMode === 'symphony' ? symphonyAgentId : undefined,
      selected_pair: symbol,
      extraction: extractionConfig,
      decision: {
        analysis_frequency: timeframe,
        user_prompt: userPrompt,
        system_prompt: DEFAULT_SYSTEM_PROMPT,
      },
      llm_config: {
        provider: 'openrouter',
        model: llmModel,
        reasoning_tier: reasoningTier,
        thinking_mode: reasoningTier === 'premium',
        use_platform_keys: true,
        use_own_key: false,
      },
      trading: {
        leverage: 5,
        position_sizing: { max_margin_percent: 20.0 },
        risk_management: {
          default_stop_loss_percent: 1.5,
          default_take_profit_percent: 3.0,
        },
      },
    }

    // Create bot
    const newBot = await apiClient.createConfig(botName, configData)

    // Trigger first run
    try {
      await apiClient.triggerBotManually(newBot.config_id)
    } catch (runError) {
      console.warn('First run failed:', runError)
      // Don't fail creation if first run fails
    }

    // Close modal, notify parent
    onConfirm(newBot)
    onOpenChange(false)

  } catch (error) {
    console.error('Failed to create bot:', error)
    // Show error toast
  } finally {
    setIsCreating(false)
    setIsGenerating(false)
  }
}
```

### 2. Parent Page Changes

**File**: `frontend/app/forge/page.tsx`

**Auto-open for new users:**
```typescript
// After bots load
useEffect(() => {
  if (!loading && user && allBots.length === 0) {
    setBotCreationModalOpen(true)
  }
}, [loading, user, allBots.length])
```

**Modal cannot close for new users:**
```typescript
<BotCreationModal
  open={botCreationModalOpen}
  onOpenChange={(open) => {
    // Only allow close if user has at least one bot
    if (!open && allBots.length === 0) {
      return // Prevent closing
    }
    setBotCreationModalOpen(open)
  }}
  forceOpen={allBots.length === 0}
  // ... other props
/>
```

**Success alert after creation:**
```typescript
const handleBotCreated = (newBot: BotConfiguration) => {
  setAllBots(prev => [...prev, newBot])
  setSelectedConfigId(newBot.config_id)
  setBotCreationModalOpen(false)

  // Show success alert (use your standard alert pattern)
  showAlert({
    type: 'success',
    message: `${newBot.config_name} created! Watch it analyze the market...`
  })
}
```

### 3. API Client Addition

**File**: `frontend/lib/api.ts`

```typescript
async generateStrategy(
  description: string,
  symbol: string = 'BTC/USDT',
  timeframe: string = '1h'
): Promise<{ user_prompt: string; success: boolean; error?: string }> {
  const response = await this.authenticatedFetch(
    `${this.baseUrl}/api/v2/assistant/generate-strategy`,
    {
      method: 'POST',
      body: JSON.stringify({ description, symbol, timeframe }),
    }
  )
  return response.json()
}
```

### 4. Archetype Configs

**File**: `frontend/lib/archetypes.ts` (NEW)

```typescript
export interface ArchetypeConfig {
  id: string
  name: string
  shortDescription: string
  userPrompt: string
  extraction: {
    selected_data_sources: {
      technical_analysis: { data_points: string[]; timeframes: string[] }
      market_intelligence?: { data_points: string[] }
    }
  }
  defaultTimeframe: string
}

export const ARCHETYPES: Record<string, ArchetypeConfig> = {
  contrarian: {
    id: 'contrarian',
    name: 'The Contrarian',
    shortDescription: 'Mean-reversion trader that fades extremes',
    userPrompt: `You are The Contrarian - a mean-reversion trader...`, // Full text from trading/strategies/the_contrarian.md
    extraction: {
      selected_data_sources: {
        technical_analysis: {
          data_points: ['RSI', 'Stochastic', 'CCI', 'Bollinger Bands', 'EMA', 'ATR', 'MACD', 'OBV', 'ADX', 'Aroon', 'VWAP'],
          timeframes: ['1h']
        },
        market_intelligence: {
          data_points: ['twitter_sentiment', 'btc_funding_rate', 'eth_funding_rate']
        }
      }
    },
    defaultTimeframe: '1h'
  },
  compass: {
    id: 'compass',
    name: 'The Compass',
    shortDescription: 'Macro regime trader following global trends',
    userPrompt: `You are The Compass - a macro regime trader...`, // Full text
    extraction: {
      selected_data_sources: {
        technical_analysis: {
          data_points: ['EMA', 'SMA', 'ADX', 'Aroon', 'MACD', 'RSI', 'Bollinger Bands', 'OBV', 'ATR'],
          timeframes: ['1d']
        },
        market_intelligence: {
          data_points: ['VIX', 'DXY', 'CPI', 'NFP', 'btc_funding_rate', 'eth_funding_rate', 'twitter_sentiment']
        }
      }
    },
    defaultTimeframe: '1d'
  },
  arbiter: {
    id: 'arbiter',
    name: 'The Arbiter',
    shortDescription: 'Confluence trader weighing all evidence',
    userPrompt: `You are The Arbiter - a confluence trader...`, // Full text
    extraction: {
      selected_data_sources: {
        technical_analysis: {
          data_points: ['ADX', 'Aroon', 'EMA', 'SMA', 'PSAR', 'MACD', 'RSI', 'Stochastic', 'CCI', 'Bollinger Bands', 'ATR', 'OBV', 'VWAP'],
          timeframes: ['4h']
        },
        market_intelligence: {
          data_points: ['twitter_sentiment', 'btc_funding_rate', 'eth_funding_rate', 'whale_activity', 'btc_tvl', 'crypto_news']
        }
      }
    },
    defaultTimeframe: '4h'
  }
}

export const getArchetypeConfig = (id: string): ArchetypeConfig | null => {
  return ARCHETYPES[id] || null
}
```

---

## Implementation Phases

### Phase 1: Backend (~3-4 hours)
- [ ] Add `first_run_used` column to configurations table
- [ ] Create `POST /api/v2/assistant/generate-strategy` endpoint
- [ ] Modify orchestrate endpoint for first-run permission bypass
- [ ] Test endpoint with various descriptions

### Phase 2: Frontend - Modal Structure (~4-5 hours)
- [ ] Refactor BotCreationModal to step-based structure
- [ ] Implement step navigation (Next/Back)
- [ ] Add progress indicator
- [ ] Style each step's content
- [ ] Handle validation per step

### Phase 3: Frontend - Integration (~3-4 hours)
- [ ] Create archetypes.ts with full configs
- [ ] Implement archetype button handlers
- [ ] Add strategy generation API call
- [ ] Integrate model selector (reuse from StrategyEditor)
- [ ] Handle loading states during generation

### Phase 4: Frontend - New User Flow (~2-3 hours)
- [ ] Auto-open modal for users with 0 bots
- [ ] Hide X button with tooltip for new users
- [ ] Add success alert after creation
- [ ] Trigger first run on creation
- [ ] Test complete flow

### Phase 5: Cleanup (~1-2 hours)
- [ ] Remove model permission gating from StrategyEditor
- [ ] Remove `premium_llms` from permissions if unused
- [ ] Update any related tests
- [ ] Manual testing of all flows

---

## Success Metrics

| Metric | Before | Target |
|--------|--------|--------|
| New user completes first bot | Unknown (no tracking) | >80% |
| Time to first bot creation | ~10s (auto-created junk) | ~2-3 min (intentional) |
| First bot has meaningful strategy | 0% (RSI default) | 100% |
| User understands what bot does | Low | High |

---

## Rollback Plan

If issues arise:
1. Revert modal changes, restore old BotCreationModal
2. Keep `first_run_used` column (benign)
3. Keep generate-strategy endpoint (unused is fine)

---

## Open Questions (Resolved)

1. ~~Run once permissions~~ → First run free (Option A)
2. ~~Strategy generation~~ → LLM endpoint
3. ~~Which archetypes~~ → Contrarian, Compass, Arbiter
4. ~~Image upload~~ → Skip for now
5. ~~Model permissions~~ → Remove gating (legacy)
6. ~~Modal style~~ → Typeform (one step at a time)
