# CHANGELOG - ggbots Platform

Complete history of features, fixes, and improvements. For current status see ACTIVE.md, upcoming work see TODO.md.

**WRITING STYLE**: Telegraphic style. Omit articles (a, an, the). Include file references, technical accuracy. Target 3-8 lines recent entries, 1-3 lines older entries.

---

## 2026-01-30 - SEO Infrastructure + Blog Launch

**Purpose**: Complete SEO foundation and launch blog with first cornerstone article.

**Documentation**: [frontend/SEO.md](frontend/SEO.md)

**Technical SEO** (`frontend/app/`):
- `sitemap.ts` - Dynamic sitemap with all pages + blog posts
- `robots.ts` - Crawl rules blocking /forge, /admin, /settings
- `layout.tsx` - Full OG, Twitter cards, keywords, canonical URLs
- `landing/page.tsx` - JSON-LD SoftwareApplication schema
- `opengraph-image.png`, `twitter-image.png` - Generated via Playwright (1200×630)
- `arena/opengraph-image.png` - Competition-specific social image

**PWA Icons** (`frontend/public/`):
- `icon-192.png`, `icon-512.png` - Android home screen
- `apple-touch-icon.png` - iOS home screen (180×180)
- `manifest.json` - Updated with brand colors (#0b0b0c, #c1a87d)

**Blog Infrastructure** (`frontend/`):
- `lib/blog.ts` - Post loading, frontmatter parsing, BlogPosting schema generation
- `app/blog/page.tsx` - Blog index with post listing
- `app/blog/[slug]/page.tsx` - Individual posts with SSG
- `app/blog/layout.tsx` - Blog layout with ThemeProvider
- `app/feed.xml/route.ts` - RSS feed auto-generated from posts
- `content/blog/what-is-vibe-trading.mdx` - First cornerstone (~3,200 words)

**OG Image Generation** (`frontend/scripts/`):
- `og-image-template.html`, `og-image-arena.html` - Editable HTML templates
- `generate_og_image.py` - Playwright-based screenshot generator
- Brand colors from VIBE.md (#c1a87d brass, #0b0b0c obsidian)

**Landing Page Updates**:
- Header: Removed Privacy/Terms (Google verified), added Blog link
- Footer: Added "Learn" section with Blog + ggArena links

---

## 2026-01-30 - Performance: Remove UX Delays + Refactor Planning

**Purpose**: Quick win for API performance, revised refactor plan addressing root cause.

**ggbot.py Performance Fix**:
- Removed 6 artificial `asyncio.sleep()` calls from orchestrator (13s total per cycle)
- `_run_autonomous_trading_cycle()`: removed 3s + 7s + 3s delays
- `_run_signal_validation_cycle()`: removed 3s + 7s + 3s delays
- SSE phase updates still fire instantly, just no artificial pauses between them

**Refactor Planning** (`DOCS/todo/ORCHESTRATOR_REFACTOR.md`):
- NEW planning doc supersedes over-engineered API_EXTRACTION_REFACTOR.md
- Root cause analysis: psycopg2 sync DB is primary bottleneck, not process architecture
- Phased approach: Quick wins → Scheduler separation → Async DB → Code organization
- Scale considerations: Current (35 bots) → Near-term (200) → Long-term (1000+)

**TODO.md Updated**:
- Compressed 7-phase plan to 4 focused phases
- Added success metrics table (current vs target)
- Marked Phase 1 (quick wins) complete

---

## 2026-01-30 - Landing Page Quick Wins + Webapp Testing Skill

**Purpose**: Improve landing page conversion via social proof, CTAs, and design system compliance. Add Playwright-based testing capability.

**New Components** (`frontend/components/new-landing/`):
- `SocialProof.tsx` (NEW) - ggArena banner + live stats (470+ bots, 5.9K trades, 86K decisions)
- Replaced Arcade demo embed (outdated, confusing CTA)

**Landing Page Updates** (`frontend/components/new-landing/*.tsx`):
- Process.tsx - Added CTA "Build your first bot in 2 minutes"
- Features.tsx - Added CTA "Watch live bots compete", removed shadows
- Hero.tsx - Removed brass glow shadow
- Pricing.tsx - Removed all shadow effects
- PersonalStory.tsx - Removed shadow, cleaner button
- FAQ.tsx - Contact CTA → Telegram community link with icon
- Header.tsx - Added "Sign Up" link alongside "Launch App"
- Footer.tsx - Fixed stretched logo via object-contain

**Webapp Testing Skill** (`.claude/skills/webapp-testing/`):
- Downloaded from anthropics/skills repo
- Installed Playwright + Chromium browser
- Added `screenshot_url.py` script for visual verification
- Can now take screenshots of deployed pages for review

**Activity Modal** (`frontend/components/activity-modal.tsx`):
- Upgraded to standardized `lg` sizing (576→672px desktop)
- Replaced inline styles with Tailwind classes matching modal.tsx standards

---

## 2026-01-30 - Enriched Preprocessor Summaries (Option A)

**Purpose**: Surface rich indicator signals (divergence, crossovers, squeeze, acceleration) in LLM-readable summaries. Token-neutral approach - signals appear only when detected.

**Updated All 21 Preprocessors** (`extraction/v2/preprocessors/`):
- Momentum: RSI, Stochastic, CCI, MFI, Williams %R, ROC - Added divergence, crossovers, acceleration, failure swings
- Trend: MACD, ADX, EMA, SMA, PSAR, Aroon, Vortex, Trix - Added crossovers, DI signals, reversals, zero-line crosses
- Volatility: ATR, BBands, BBWidth, Keltner, Donchian - Added squeeze detection, breakouts, consolidation patterns
- Volume: OBV, VWAP - Added accumulation/distribution, divergence, mean reversion signals

**Enriched Summary Format**:
```
Before: "RSI at 73.2, overbought for 7 periods"
After:  "RSI=73.2, overbought (7p). ⚠️ BEARISH DIVERGENCE. Momentum decelerating"
```

**Design Principles**:
- Conditional signals: Only appear when actually detected (keeps summaries lean)
- Consistent emoji markers: `✓` bullish/confirmation, `⚠️` warning/bearish
- Token-neutral: ~same token count when no special signals present

**Background**: Audit found ALL 21 preprocessors compute rich data (divergence in 12, crossover in 8, squeeze in 5) but summaries only showed basic values. Option A chosen over Option B (compact format for LLMs) due to 5x token cost difference.

---

## 2026-01-29 - Rei Compact Format + Behavior Prompt

**Purpose**: Reduce Rei payload size (~22KB → ~7KB) via compact indicator format + timeframe filtering. Align behavior prompt with Rei Core learning principles.

**Compact Format Implementation** (`extraction/v2/preprocessors/`):
- `base.py` - Added `to_compact()` method to BasePreprocessor with universal schema
- `compact_config.py` (NEW) - `REI_INDICATOR_TIMEFRAMES` dict + `get_timeframes_for_indicator()`
- All 21 preprocessors - Indicator-specific `to_compact()` implementations

**Universal Compact Schema** (~400 bytes vs ~2KB full output):
```python
{value, value_secondary, value_tertiary, velocity, rank, zone, zone_periods, trend,
 crossover_type, crossover_periods_ago, patterns[], analysis, indicator, timeframe, timestamp}
```

**Timeframe Filtering** (per indicator type):
- Momentum oscillators: 15m, 1h, 4h, 1d
- Trend indicators: 1h, 4h, 1d
- Volatility indicators: 1h, 4h, 1d
- Volume indicators: 1h, 4h

**Rei Engine Updates** (`decision/rei_engine.py`):
- `_convert_to_compact_indicators()` - Filters by configured timeframes, calls `to_compact()`
- Payload log: "Consulting Rei for BTC/USDT decision (payload ~7014 bytes)"

**Strategy File** (`trading/strategies/rei_core.md` - NEW):
- Separate Description + Behavior Prompt sections for Rei Factory copy/paste
- Follows Rei doc principles: teach relationships not rules, no prescriptive thresholds
- Documents all 33 data points (21 technical + 12 market intelligence)

**Working Doc**: `DOCS/REI_COMPACT_PROGRESS.md` - Implementation tracker (21/21 complete)

**Test Results**: "The Nightingale" - 7KB payload, Rei responded "wait @ 65% confidence"

---

## 2026-01-28 - Rei Scheduled Bot Engine (Experimental)

**Purpose**: Alternative decision engine using Rei Core (reilabs.org) instead of OpenRouter LLMs. Replaces agent-based Rei integration that failed due to Claude overriding Rei signals.

**New Files**:
- `decision/rei_engine.py` - ReiDecisionEngine + report_trade_outcome_to_rei() feedback function
- `DOCS/REI_DOCS.md` - Rei platform documentation (from reilabs.org)

**Schema Changes** (`core/config/schemas.py`, `core/services/config_service.py`):
- Added `rei_enabled: bool = False` to ScheduledTradingConfigData
- Added `rei_enabled` attribute to BotConfigV2 class + from_dict() loader

**Orchestrator Routing** (`ggbot.py:_run_decision_v2()`):
- Checks `config.rei_enabled` flag
- Routes to ReiDecisionEngine instead of DecisionEngineV2
- Fetches open positions + account balance for Rei context

**Feedback Loop** (`trading/paper/supabase_service.py`):
- On trade close, checks if bot is rei_enabled
- Reports outcome to Rei: symbol, side, P&L, duration, close reason
- Enables inference-time learning (Rei improves from outcomes)

**Activity Logging** (`decision/rei_engine.py`):
- Logs as `llm_thought` (not `rei_decision`) for frontend compatibility
- Formats Rei's key_signals/warnings/reasoning into KEY_SIGNAL/SUMMARY/RISK sections
- Sets `provider='rei'`, `model='rei-core'`, zero cost (external billing)

**Test Bot**: "The Nightingale" (config_id: `4060437e-b39e-4c51-a2a9-b35cf698ed64`) - BTC/USDT paper

**Doc Updates**: `ACTIVE.md` (Rei section under Trading Modes), `decision/README.md` (full Rei section)

---

## 2026-01-28 - Kimi K2.5 Model Update + LLM Update Workflow

**Kimi Model Upgrade** (`decision/llm_providers/openrouter_provider.py`):
- Standard tier: `kimi-k2-0905` → `kimi-k2.5` (multimodal SOTA, agent swarm)
- Premium tier: `kimi-k2-thinking` → `kimi-k2.5` (same model, high reasoning effort)
- Economy tier: unchanged (`kimi-k2`)
- Updated `REASONING_SUPPORTED`, `TEMPERATURE_SUPPORTED`, `MODEL_MAP`, `MODEL_TIER_MAP`
- DB `llm_models` table: pricing $0.60/$3.00, context 262K, description updated

**LLM Model Update Workflow** (`decision/llm_providers/MODEL_UPDATE.md` - NEW):
- Systematic process: Research → Code → DB → Restart → Verify
- Current 21-combination roster table (7 models × 3 tiers)
- Checklist for all touch points (code + DB)
- Update history with this Kimi change as first entry

**Documentation** (`CLAUDE.md`):
- Added "Updating LLM models/tiers" → `decision/llm_providers/MODEL_UPDATE.md` to quick reference table

---

## 2026-01-27 - Forge React Query + Arena Podium Fixes

**Forge Page React Query** (`frontend/lib/queries.ts`, `frontend/app/forge/page.tsx`):
- `useDataSources()` - 10min staleTime, replaces manual fetch-on-mount
- `useBotList()` - Initial load with auto-retry + window focus refetch
- `useLatestActivity(configId)` - 30s refetchInterval, replaces manual setInterval polling
- `useConfigUsage()`, `useForgeQueryClient()` helpers for future SSE cache integration
- Removed ~60 lines manual fetch/poll/retry boilerplate from page.tsx

**Arena Podium Fixes** (`frontend/components/arena/Top3Chart.tsx`, `ArenaWithStaking.tsx`):
- Refresh button uses `isFetching` (not `isLoading`) — spinner now animates on refetch
- Top 3 legend inline on desktop (saves vertical space), stacked on mobile
- Chart height: 200/280px → 220/300px for breathing room

---

## 2026-01-27 - Frontend Performance & Arena Redesign

**Planning Doc**: [DOCS/completed/FRONTEND_PERFORMANCE_REACT_QUERY.md](DOCS/completed/FRONTEND_PERFORMANCE_REACT_QUERY.md)

**React Query Integration** (`frontend/lib/`):
- `providers.tsx` - QueryClientProvider at root level (30s staleTime, 5min gcTime)
- `queries.ts` - `useArenaPerformance()` hook with type-safe ArenaBot interface
- `layout.tsx` - Wrapped app with Providers
- Bundle overhead: ~12KB gzipped, benefits all pages

**Backend Redis Caching** (`api/public.py`):
- `/api/v2/public/arena/performance` - 60s TTL cache
- Double-layer caching: Redis (60s) + React Query (30s) = instant revisits
- Log cache hits/misses for monitoring

**Arena Page Redesign** (`frontend/components/arena/`):
- `Sparkline.tsx` - Pure SVG sparklines (~50 data points, no library)
- `Top3Chart.tsx` - lightweight-charts podium chart (3 lines only, gold/silver/dark-brass)
- Replaced 30-line Recharts spaghetti → eliminated "page unresponsive"
- Responsive `BotEquityChart` - SVG viewBox scales to container width
- Bundle: 212KB → 168KB first load JS (44KB reduction)

**Mobile Improvements**:
- Sparklines in leaderboard rows (desktop), expanded cards (mobile)
- Three-column stats layout in expanded cards (Performance/Strategy/Risk)
- Removed duplicate sparkline stacking issue

---

## 2026-01-27 - USX Arena Betting (Full Stack)

**Planning Doc**: [DOCS/todo/USX_STAKING_MODAL.md](DOCS/todo/USX_STAKING_MODAL.md)

**Web3 Dependencies** (`frontend/package.json`):
- wagmi v2, viem v2, @rainbow-me/rainbowkit v2 (wagmi v3 incompatible with RainbowKit, downgraded)
- Web3 code scoped to Arena page only (lazy-loaded, ~65KB savings for other pages)

**BetModal** (`frontend/components/arena/BetModal.tsx`):
- Full betting flow: wallet connect → amount input → approve → deposit → record
- Reads USX decimals from contract (not hardcoded)
- Refs (stepRef, parsedAmountRef, addressRef) prevent stale closures in useEffect chains
- Error handling: wallet rejection, on-chain tx failure, separate error states per step
- 6 granular steps: idle → approving → waitApproval → depositing → waitDeposit → recording → complete
- Retry mechanism with wagmi reset(), "Try again" button on error
- Shows sUSX preview, 15-day cooldown warning, Scrollscan tx link on success

**Arena Card CTA** (`frontend/components/arena/ArenaWithStaking.tsx`):
- "Bet on This Bot" button in expanded bot cards with Coins icon
- Side-by-side equity chart (60%) + performance stats (40%) on desktop, stacked on mobile
- Strategy + Risk Management in 2-col grid below

**Backend** (`ggbot.py`):
- `POST /api/v2/arena/pledge` - Now public (no auth), wallet_address = identity
- Validates wallet address format (0x, 42 chars) and tx_hash format (0x, 66 chars)
- `arena_pledges.user_id` now nullable (ALTER TABLE migration applied)

**Frontend Setup** (`frontend/lib/`):
- `wagmi-config.ts` - Scroll chain config with WalletConnect Project ID (Vercel env var)
- `contracts.ts` - USX/sUSX addresses + ERC20/ERC4626 ABIs
- `api.ts` - `recordArenaPledge()` uses regular fetch (no auth required)

---

## 2026-01-23 - Market Data Intelligence Update

**Planning Doc**: [DOCS/completed/MARKET_DATA_INTELLIGENCE_UPDATE.md](DOCS/completed/MARKET_DATA_INTELLIGENCE_UPDATE.md)

**ggShot Soft Disable**:
- Disabled `data_points.ggshot` and `data_sources.trading_signals` in database (`enabled=false`)
- Removed Signals tab from frontend (`ConfigTabs.tsx`, `ConfigureLayout.tsx`)
- Updated `orchestrator.py:_check_permission()` to validate `enabled` flag
- Updated agent MCP tool docstrings to remove ggshot references
- Reason: signals 90+ days stale, confusing bots

**Astrology Indicators** (`market_intelligence/adapters/agentic/grok_agentic.py`):
- Added `lunar_phase` prompt template (moon phase, waxing/waning, next Full/New Moon)
- Added `mercury_status` prompt template (retrograde status, other retrogrades)
- Added catalog mappings (`catalog_mapping.py`) with 12hr/24hr TTLs
- Seeded database under `sentiment_social` category
- Updated `agent/mcp_server.py` and `agent/README.md` with new data points
- Cost: ~$0.005/lunar query, ~$0.001/mercury query

---

## 2026-01-23 - Onboarding Tour & Strategy Advisor UX

**Frontend Onboarding Tour** (`components/OnboardingTour.tsx` - NEW):
- 5-step tutorial overlay triggered after first bot creation
- Auto-navigates between Monitor/Configure tabs to show key features
- Border highlight only (no darkening overlay), pointer-events pass-through
- "Skip tutorial" link, keyboard nav (←/→/Esc), localStorage persistence
- Steps: Activity Timeline → Configure Tab → Strategy Advisor → Config Tabs → Wrap-up

**Strategy Advisor Buttons** (`components/StrategyAdvisorPanel.tsx`):
- Added "Explain Strategy" button (MessageCircle icon) - sends prompt for strategy explanation
- Renamed "Create Strategy" → "Update Strategy" (Wand2 icon) - post-creation context
- "Analyze Performance" only shows after bot has closed trades
- Updated empty state text based on trade history

**Tour Integration** (`app/forge/page.tsx`):
- `ONBOARDING_STEPS` array with `onEnter` callbacks for tab navigation
- Triggers 1.5s after first bot creation
- `data-tour` attributes: activity-timeline, configure-tab, strategy-advisor, config-tabs

**Bot Creation Modal** (`app/forge/components/modals/BotCreationModal.tsx`):
- Improved description placeholder with bullet examples
- Visual "or choose a proven strategy" separator between custom/archetypes

**Supporting Changes**:
- `TabNavigation.tsx` - Added `data-tour="configure-tab"` attribute
- `ConfigureLayout.tsx` - Added `data-tour="config-tabs"` wrapper

---

## 2026-01-22 - Rei Integration Hardening

**Related Doc**: [DOCS/completed/REI_AGENT_INTEGRATION.md](DOCS/completed/REI_AGENT_INTEGRATION.md)

**Problem**: Claude (Opus 4.5) was overriding Rei's EXIT signals with independent analysis. One incident: Rei said EXIT at +$144 profit, Claude held → position closed at -$246 loss. ~$400 swing from override.

**Model Change** (`.env`):
- Switched from `claude-opus-4-5-20251101` to `claude-haiku-4-5-20250929`
- Haiku follows instructions more faithfully, less "I have a better idea" behavior

**System Prompt Hardening** (`agent/run_agent.py:232-299`):
- Added explicit rules: "You are a robot. Rei says X, you do X."
- Forbidden phrases: "My Assessment", "despite Rei", "however, I think"
- EXIT has NO threshold - when Rei says out, agent exits immediately
- ENTER requires ≥50% confidence (wait for conviction)

**Confidence-Based Position Sizing**:
- Size = confidence × max_position (e.g., 70% confidence = 70% of max size)
- Higher conviction = larger bet, lower conviction = smaller bet

**Rei Timeout Fix** (`agent/mcp_server.py:1553`):
- Increased timeout 60s → 180s for large market data payload (~15-20KB)
- Was causing connection errors during consult_rei_for_decision

**Documentation**: Updated `agent/README.md` with decision logic table, thresholds, sizing formula.

---

## 2026-01-22 - Telegram Publishing (Platform Bot)

**Planning Doc**: [DOCS/completed/TELEGRAM_PUBLISHING.md](DOCS/completed/TELEGRAM_PUBLISHING.md)

**Bot Command Handler** (`signals/telegram_bot_handler.py`):
- New PM2 service `telegram-bot` - long polling for Telegram commands
- `/start` - welcome message with setup instructions
- `/chatid` - returns group ID for configuration
- `/help` - command reference

**Publishing Service** (`signals/publishing_service.py`):
- Fixed tier check: all paid tiers (usage_based, ggbase, pro) not just ggbase
- Entry notifications: bot name, action (📈 LONG / 📉 SHORT), confidence, reasoning
- Exit notifications: P&L display (✅ +$X / ❌ -$X), duration, close reason icons
- `publish_exit_to_telegram()` - new function for trade exits

**Orchestrator Integration** (`ggbot.py:744-820`):
- `_should_publish_signal()` - only publishes on trade entries (long/short), not waits
- `_trigger_signal_publishing()` - enriches with bot_name, symbol, config_type

**Trade Exit Hooks**:
- `trading/paper/supabase_service.py:624-649` - paper trade exits
- `trading/live/symphony_service.py:532-560` - Symphony live exits
- Skips `account_reset` reason to avoid spam

**Frontend** (`TradeSettings.tsx`, `permissions.tsx`):
- Updated instructions: "channel" → "group" (groups support /chatid)
- Fixed permission gate: `telegram_publishing` case added
- Fixed API URL: relative → absolute backend URL

---

## 2026-01-21 - ggArena Season 1 Launch

**Planning Doc**: [DOCS/completed/GGARENA_SEASON1_LAUNCH.md](DOCS/completed/GGARENA_SEASON1_LAUNCH.md)

**Launch Execution** (12:00 UTC):
- Ran `scripts/arena_reset.py --execute` → 14 bots reset to $10k, 5 positions closed
- Added `arena_registered_at` timestamp column to configurations table
- Backfilled 12 existing arena registrations

**Arena Page Polish** (`frontend/app/arena/page.tsx`):
- Hardcoded chart to 504 hours (21 days) for competition duration
- Removed time range dropdown selector
- Season badge shows "Season One · 🔴 LIVE" with pulsing red dot when competition active
- Countdown timer hidden when live (replaced by LIVE badge)
- Reordered sections: Hero → Chart → Leaderboard → How It Works → Footer

**Backend: Competition Start Filter** (`api/public.py:18-71`):
- `COMPETITION_START = datetime(2026, 1, 21, 12, 0, 0, tzinfo=timezone.utc)`
- Arena performance API now filters data from competition start, not rolling window
- Chart shows only post-reset data

**Late Registration Support** (`ggbot.py:3929-3961`):
- Registration endpoint now resets account to $10k if competition already started
- Returns `account_reset: true` flag in response
- Frontend modal shows immediate reset confirmation

**Bug Fixes**:
- `frontend/app/forge/page.tsx`: Skip API calls for temp IDs (optimistic placeholders during duplication)
- `market_intelligence/adapters/derivatives/binance_funding.py`: Increased timeout 30s → 60s

---

## 2026-01-21 - Unified Modal System

**Planning Doc**: [DOCS/completed/UNIFIED_MODAL_SYSTEM.md](DOCS/completed/UNIFIED_MODAL_SYSTEM.md)

**Problem**: 8 modals using 3 different systems (Radix Dialog, custom, Framer Motion). Inconsistent backdrops (`/50` to `/80`), borders (`rounded-lg` to `rounded-2xl`), sizing (no responsive scaling), broken `dark:` prefixes in SettingsModal.

**Solution**: Unified `Modal` component with Framer Motion, responsive sizing, full-screen mobile, CSS variables.

**New Component** (`frontend/components/ui/modal.tsx`):
- `Modal`, `ModalHeader`, `ModalBody`, `ModalFooter`, `ModalTitle`, `ModalDescription`
- Size variants: `sm`, `md`, `lg`, `xl`, `full` with responsive breakpoints
- Focus trap, focus restoration, ARIA attributes for accessibility
- Portal rendering (escapes parent containers), scroll lock
- `preventClose` prop for forced modals (onboarding)

**Migrated Modals**:
- `AddCreditsModal.tsx` → `size="sm"`, simplified structure
- `UpgradeModal.tsx` → `size="sm"`, multi-view with back navigation
- `ArenaRegistrationModal.tsx` → `size="sm"`, success state handling
- `BotCreationModal.tsx` → `size="xl"`, `preventClose={forceOpen}`
- `SettingsModal.tsx` → `size="lg"`, fixed all `dark:` prefixes to CSS variables
- `RiskAcknowledgmentModal.tsx` → `size="lg"`, converted from custom implementation

**activity-modal.tsx**: Minimal changes (kept custom navigation features):
- Removed gold border (`border-2 border-[var(--accent)]` → `border border-[var(--border)]`)
- Standardized z-index (`z-40` → `z-50`)
- Preserved: touch swipe, chevron navigation, counter display, arrow key navigation

**Skipped**: `TradeHistoryModal.tsx` (no UI trigger currently)

---

## 2026-01-21 - Prepaid Tier Implementation

**Planning Doc**: [DOCS/completed/PREPAID_TIER.md](DOCS/completed/PREPAID_TIER.md)

**Problem**: Credit pack buyers on `usage_based` tier with metered billing → confusion. Users expect prepaid behavior (bot stops when empty), actual behavior was metered billing with credits as discounts (potential overage charges).

**Solution**: Separate `prepaid` tier using existing `ggbase` enum value (0 users, no migration needed).

**Domain Model** (`core/domain/user_profile.py`):
- `PREPAID = "ggbase"` enum value, `is_prepaid_tier`, `requires_credit_check` properties
- `can_activate_bots` now includes PREPAID tier

**Pre-LLM Credit Check** (`decision/engine_v2.py:161-247`):
- `InsufficientCreditsError` exception blocks LLM calls when credits exhausted
- `_check_prepaid_credits()` called before every decision
- Fail-closed: Stripe API errors block rather than allow

**Activity Logging** (`core/common/activity_logger.py:277-295`):
- `stripe_reported` parameter added to `log_llm_activity()`
- Prepaid users: `stripe_reported=True` immediately (never enters meter queue)

**Meter Reporter** (`billing/stripe_meter_reporter.py:33-65`):
- JOIN filter excludes `ggbase` tier from unreported usage query
- Defense in depth: even if activity logged incorrectly, won't be metered

**Usage Monitor** (`core/monitoring/usage_monitor.py:118-155`):
- Tier-specific handling: PREPAID=hard block, USAGE_BASED=soft warn
- Prepaid-specific email notifications (no overage messaging)

**Checkout Flows** (`ggbot.py:4377-4414, 4569-4627, 4822-4849`):
- Stripe credit purchase: payment mode only (no subscription)
- Crypto credit purchase: sets `ggbase` tier for free users
- Webhook: free→prepaid on credit purchase, existing paid users keep tier

**Frontend** (`frontend/lib/permissions.tsx:8`):
- Added `ggbase` to `subscription_tier` type union

**Migration**: 6 existing credit pack users migrated from `usage_based` to `ggbase`, Stripe subscriptions cancelled.

---

## 2026-01-20 - Onboarding Revamp & Free Test Runs

**Planning Doc**: [DOCS/completed/ONBOARDING_REVAMP.md](DOCS/completed/ONBOARDING_REVAMP.md)

**Problem**: Poor new user experience - auto-created "Default ggbot" with bad RSI strategy, no guidance.

**BotCreationModal Typeform Redesign** (`frontend/.../BotCreationModal.tsx`):
- 5-step typeform-style flow: Name → Mode → Symbol/Timeframe → Strategy → Model
- 3 archetype templates: Contrarian (mean-reversion), Compass (macro), Arbiter (confluence)
- Description-based strategy generation via Claude Haiku
- Progress bar with arrow navigation, step indicators
- Auto-opens for users with 0 bots, non-closable until first bot created

**Archetype System** (`frontend/lib/archetypes.ts`):
- Full trading strategies with Identity, Entry/Exit Conditions, Confidence Thresholds
- Each archetype includes extraction config (indicators, timeframes, market intelligence)
- `getArchetypeConfig()`, `getArchetypeSummaries()` helpers

**Strategy Generation Endpoint** (`api/assistant.py:776-920`):
- `POST /api/v2/assistant/generate-strategy` - One-shot LLM call
- Platform-aware prompt with 21 technical indicators + market intelligence sources
- Outputs structured strategy matching archetype format

**Free Test Runs System**:
- `first_run_used` boolean - Creation auto-run (free, doesn't count)
- `free_runs_remaining` integer (default 3) - Manual "Run Once" clicks per bot
- Backend permission bypass in orchestrate (`ggbot.py:355-386`)
- `decrement_free_runs()` method (`core/services/config_service.py:746-786`)
- SSE includes both fields (`core/sse/dashboard_data.py:87,193-194`)

**Run Once Button UI** (`frontend/.../ActivationBar.tsx:143-244`):
- Shows "(3 free)" → "(2 free)" → "(1 free)" for non-subscribers
- Grays out with tooltip when exhausted
- Optimistic local state update (`frontend/app/forge/page.tsx:785-793`)

**Legacy Permission Gating Removed** (`frontend/.../StrategyEditor.tsx`):
- All AI models available to everyone (Grok, Claude, Gemini, DeepSeek, GPT, Kimi, Qwen)
- All analysis frequencies available (5m, 15m, 30m, 1h, 4h, 1d, 1w)
- Reasoning Tier selector (Economy/Standard/Premium) visible to all
- Removed Crown icons, UpgradeModal from model selection

**Dialog Component Enhancement** (`frontend/components/ui/dialog.tsx:23-52`):
- Added `hideCloseButton?: boolean` prop to DialogContent
- Used by BotCreationModal to show only custom X button with tooltip

---

## 2026-01-16 - Rei Agent Integration

**Planning Doc**: [DOCS/completed/REI_AGENT_INTEGRATION.md](DOCS/completed/REI_AGENT_INTEGRATION.md)

**Architecture**: Claude (orchestrator) + Rei (brain) hybrid. Claude handles execution/timing/tools, Rei handles reasoning/learning/pattern recognition. Enables persistent learning at inference time.

**Rei Service Client** (`core/services/rei_service.py`):
- Async HTTP client for Rei API (`api.reilabs.org`)
- `chat_completion()` with JSON response format, retry/backoff
- Auth via `REI_01_UNIT_SECRET` env var

**MCP Tools** (`agent/mcp_server.py:1305-1700`):
- `query_market_data_for_rei` - Fetches 21 technicals + 11 intel, stores in session buffer
- `consult_rei_for_decision` - Sends data to Rei, returns action/confidence/TP/SL
- `report_trade_outcome_to_rei` - Sends closed trade results for Rei learning

**Configuration** (`core/config/schemas.py`):
- Added `rei_enabled: bool` to AgentConfigData

**System Prompt** (`agent/run_agent.py:232-279`):
- Conditional Rei section when `rei_enabled=true`
- Rei-specific EXECUTION LOOP: query_market_data_for_rei → consult_rei → execute/wait → report_outcome
- "CRITICAL: Rei is your decision maker. Do NOT analyze charts yourself."

**Session Buffer** (`agent/session_buffer.py`):
- Already existed; used to pass ~15-20KB market data between tool calls without Claude carrying JSON

**Data Flow**:
1. Claude calls `query_market_data_for_rei(BTC, 4h)` → stores 32 data points in buffer
2. Claude calls `consult_rei_for_decision(positions, balance)` → Rei analyzes, returns JSON
3. Claude executes trade or waits based on Rei's confidence (60% threshold)
4. When trade closes → `report_trade_outcome_to_rei()` for learning feedback

**Verified Data**: 21/21 technical indicators received, 8/11 market intel (missing: eth_funding_rate, btc_tvl, whale_activity)

**Test Bot**: "The Nightingale" (config_id: 5b77d429-5da4-4d69-8aba-50d916e4b6b8) running with Rei integration

---

## 2026-01-16 - Frontend Usage Display

**Continuation of**: [DOCS/completed/USAGE_BILLING_TRACKING.md](DOCS/completed/USAGE_BILLING_TRACKING.md)

**API Client Methods** (`frontend/lib/api.ts:644-679`):
- `getUsageSummary()` - Fetches `/api/v2/usage/me` for UserProfile display
- `getConfigUsage()` - Fetches `/api/v2/usage/config/{id}` for per-bot costs

**UserProfile Usage Display** (`frontend/.../UserProfile.tsx:34-38, 71-90, 200-235`):
- Adaptive display based on billing model
- Credit pack users: Shows Credits / Used / Balance breakdown
- Metered users: Shows "This week: $X.XX" (weekly billing cycle)
- Low balance warning (amber text when balance < $5)

**ActivationBar Daily Cost** (`frontend/.../ActivationBar.tsx:76-120, 179-193`):
- Fetches per-bot usage on mount + 5-minute refresh interval
- Day 1 of month: Shows "$X.XX today"
- Day 2+: Shows "~$X.XX/day" average (period_usage / days_elapsed)
- Displayed next to countdown timer with Coins icon

---

## 2026-01-15 - Real-Time Usage Tracking & Billing Hardening

**Planning Doc**: [DOCS/completed/USAGE_BILLING_TRACKING.md](DOCS/completed/USAGE_BILLING_TRACKING.md)

**Redis Usage Counters** (`decision/engine_v2.py:880-895`):
- Added real-time Redis INCRBYFLOAT on every LLM call
- Keys: `usage:user:{id}:{YYYY-MM}`, `usage:config:{id}:{YYYY-MM}`, `usage:config:{id}:{YYYY-MM-DD}`
- Daily keys have 90-day TTL for historical queries
- Non-blocking: Redis failures don't break billing (activities table is source of truth)

**Usage Monitor** (`core/monitoring/usage_monitor.py`):
- New UsageMonitor class integrated into account-monitor PM2 service
- Checks credit balances every 60s for users with active bots
- Auto-pauses bots when credits depleted (updates DB + Redis pub/sub)
- Caches usage summaries every 5min for fast API reads
- Low balance warning at <20% remaining or <$5

**Usage API Endpoints** (`api/usage.py`, `ggbot.py:303,311`):
- `GET /api/v2/usage/me` - User summary (cached or live)
- `GET /api/v2/usage/config/{config_id}` - Per-bot usage
- `GET /api/v2/usage/breakdown` - All bots breakdown
- `GET /api/v2/usage/history/{config_id}` - Daily history (90 days)

**Idempotency Fixes**:
- Stripe meter reporter (`billing/stripe_meter_reporter.py:113-125`): Added `identifier` param
- NOWPayments webhook (`ggbot.py:4710-4721`): Redis-based order deduplication

**Scripts**:
- `scripts/backfill_usage_counters.py` - One-time Redis backfill from activities table

**Documentation**:
- `billing/README.md` - Comprehensive billing module documentation

---

## 2026-01-13 - Frontend Snappiness Phase 1

**Optimistic Updates** (`frontend/app/forge/page.tsx`):
- `handleDeleteBot`: Instant removal → API → rollback on error
- `handleDuplicateBot`: Temp placeholder → API → replace with real ID
- `handleRenameBot`: Instant name change → API → rollback on error
- `handleResetAccount`: Instant $10k + "Resetting..." → API → "Account reset" or rollback

**SaveStatusContext Extension** (`frontend/lib/contexts/SaveStatusContext.tsx`):
- Added `globalMessage` state for custom operation feedback
- `registerSave(id, message?)` / `completeSave(id, message?)` now accept optional messages
- SaveStatusIndicator displays custom text instead of "Saving..."/"Saved"

**Skeleton Loading States** (`frontend/app/forge/page.tsx`):
- Replaced "Loading forge..." text with skeleton grid (header + BotRail + main content)
- Replaced "Loading permissions..." text with same skeleton layout
- Uses existing LoadingSkeleton component (text, card, circle variants)

**Bot Switching Skeleton** (`frontend/app/forge/page.tsx`):
- Added `isBotSwitching` state, triggered in `handleBotSelection`
- Monitor tab shows skeleton cards during bot switch (500ms timeout)
- Prevents stale data flash when switching between bots (SSE push delay)

**UX Impact**: Delete/duplicate/rename now feel instant (0ms perceived latency vs 200-500ms before). Bot switching shows skeleton instead of stale data.

---

## 2026-01-13 - Market Intelligence Cost Optimization + ggArena Reset Script

**Market Intelligence Fixes** (`market_intelligence/`):
- Fixed cache key bug: All Grok queries shared same key `intel:grok_agentic:{symbol}` (literal) → now `intel:grok:{query_type}:{symbol}`
- Updated model: `grok-4-fast` → `grok-4-1-fast` (current XAI model)
- Extended TTLs: VIX/DXY 15min→4hr, Twitter 30min→4hr, News 10min→2hr, Whale 30min→2hr, TVL 1hr→6hr
- Added legacy category aliases: `on_chain`→`onchain_analytics`, `sentiment`→`sentiment_social`, `news`→`news_regulatory`, etc.
- Updated cost estimate: Input $0.50→$0.20/1M, Output $2.00→$0.50/1M, Live Search $0.025/source
- Expected savings: $50/week → ~$7-10/week (80-86% reduction)

**ggArena Reset Script** (`scripts/arena_reset.py`):
- Bulk reset all arena-registered bots (`is_public_performance=true`) to $10k
- Dry-run by default, `--execute` flag for actual reset, `--notify` for notifications
- Tested on The Technician (verified $7,233→$10,000 reset)

**Landing Page Privacy Links** (`frontend/components/new-landing/Header.tsx`):
- Added Privacy/Terms links next to logo in header (Google OAuth requirement)
- Desktop: subtle `text-xs text-ivory/40` links
- Mobile: added to hamburger menu with separator

---

## 2026-01-13 - Bot Performance Analysis Framework + Platform Defaults

**Bot Analysis Methodology** (`trading/ANALYSIS.md`):
- New documentation: 10-step analysis methodology for evaluating bot performance
- Covers: baseline metrics, confidence calibration, close reason analysis, indicator correlation
- Includes SQL query patterns, common pitfalls (sample size, survivorship bias, market regime)
- Example analysis flow based on Contrarian bot deep-dive (44 trades)

**Contrarian v2 Strategy** (`NOTE.md`):
- Data-driven strategy revision based on 44-trade analysis
- Key findings: long_oversold 91.7% WR, ADX>35 55.6% WR (danger zone), funding rates 53.8% WR (removed)
- Added mandatory direction alignment, ADX hard block at 35, exit logic fix ("oscillators normalizing" = hold, not exit)
- Simplified data points: removed funding rates, MACD, OBV, Aroon

**Default SL/TP Update** (`core/config/models.py:107-108`, `frontend/app/forge/page.tsx`, `frontend/app/forge/components/configure/TradeSettings.tsx`):
- Changed platform defaults from 5%/10% to 1.5%/3% (price movement)
- Analysis showed actual trades move 0.3-2.3%, old defaults never triggered
- Tighter safety net: 15% position loss at SL vs 50% previously (with 10x leverage)

**LLM Models Display Names** (`llm_models` table):
- Updated all 7 models to show tier variants in description
- Format: "Economy: X | Standard: Y | Premium: Z"
- Clarifies that tier selection changes actual model (e.g., Claude Premium = Opus 4.5)

**Activity Logging Enhancement** (`decision/engine_v2.py:806-807, 853-855`):
- Added `openrouter_model` and `reasoning_tier` to activity details JSON
- Enables audit verification: confirm Claude Premium actually called claude-opus-4.5
- Billing accuracy unchanged (uses OpenRouter's actual cost), adds human auditability

---

## 2026-01-13 - Strategy Advisor Fixes

**Strategy Advisor f-string Bug** (`api/assistant.py:338-341`):
- Fixed "Invalid format specifier ' Ellipsis, "extraction": Ellipsis'" error
- Cause: Unescaped `{...}` in system prompt f-string — Python interpreted `...` (Ellipsis) as format specifier
- Fix: Escaped curly braces as `{{...}}` in JSON example lines 339-340

**StrategyAdvisorPanel Auto-Scroll** (`frontend/components/StrategyAdvisorPanel.tsx:123-136, 478-480`):
- Added `useRef` for messages container, `useEffect` to auto-scroll on new messages
- Uses `scrollTop = scrollHeight` on container (not `scrollIntoView`) to prevent page scroll
- `requestAnimationFrame` ensures DOM painted before scrolling

---

## 2026-01-08 - Credit Packs & Crypto Payments

**Planning Doc**: [DOCS/completed/CREDIT_PACKS.md](DOCS/completed/CREDIT_PACKS.md)

**Credit Packs System** (`ggbot.py:4380-4800`):
- `GET /api/v2/credits/balance` - Returns Stripe credit balance (available_usd, ledger_usd)
- `POST /api/v2/credits/purchase` - Stripe Checkout for credit packs; auto-creates subscription for free users
- `POST /api/v2/credits/crypto-checkout` - Creates NOWPayments invoice with dynamic amounts
- `POST /api/v2/webhooks/nowpayments` - IPN handler with HMAC-SHA512 signature verification
- Updated `handle_checkout_completed` to create Stripe Credit Grants on payment success
- Helper functions: `get_stripe_customer_id()`, `has_usage_based_subscription()`

**Frontend Components** (`frontend/components/`):
- `CreditPicker.tsx` - Amount selector ($10/$25/$50/$100) + Card/Crypto payment toggle
- `AddCreditsModal.tsx` - Modal wrapper for existing subscribers to add credits
- `UpgradeModal.tsx` - Added payment mode chooser: "Pay as you go" vs "Prepay credits"
- `UserProfile.tsx` - Credit balance display in dropdown, "Add Credits" button for usage_based users
- `/credits/success/page.tsx` - Success page after credit purchase

**API Client** (`frontend/lib/api.ts`):
- `getCreditBalance()` - Fetch user's credit balance
- `purchaseCredits(amountCents)` - Create Stripe checkout for credits
- `purchaseCreditsCrypto(amountCents)` - Create NOWPayments invoice

**Integration Notes**:
- Stripe Credit Grants apply automatically to metered billing invoices
- NOWPayments IPN sends webhooks: waiting → confirming → sending → finished
- Credits created on `finished` status; signature verified with HMAC-SHA512
- IPN Callback URL: `https://ggbots-api.nightingale.business/api/v2/webhooks/nowpayments`

---

## 2026-01-07 - ggArena Season 1 Launch Prep

**Arena Page UX Overhaul** (`frontend/app/arena/page.tsx`):
- Performance fix: Extracted countdown timer to isolated component (was re-rendering entire page every second including heavy Recharts)
- Removed ArenaTimeline component (lightweight-charts) from expanded cards — was causing lag on expand
- Restructured bot details: Strategy + Risk Management cards, Market Intelligence section
- Hero copy sharpened: "Your AI vs theirs. 21 days. Winner takes all." + "Top 3 get real capital to trade live."
- Added 4-step "How It Works" section: Build → Subscribe → Enter → Win
- Merged "Training Ground" + "The Archetypes" into single "Leaderboard" section
- Footer CTA: Added prize breakdown (🥇$1,500 / 🥈$700 / 🥉$300) + deadline urgency
- Progress bar hidden until competition starts (was showing confusing "Day 0")
- Varied CTAs: "Create Your ggbot" (header) / "Enter the Arena" (hero) / "Start Building" (footer)
- All CTA links updated to app.ggbots.ai (direct to app, not landing)

**Navigation & Polish** (CC Instance B):
- Arena link added to Header navbar (`Header.tsx`)
- Dismissible Season 1 announcement banner below header (`forge/page.tsx`)
- Social links (X, Telegram) added to header with inline SVG icons
- Removed floating HelpWidget, social links now in header
- Removed "Free" tier labels from bot creation modal (`BotCreationModal.tsx`)
- Fixed light mode theme issues: StrategyAdvisorPanel button text, BotImageUpload icon colors
- Fixed empty state message: "Setting up your ggbot" → "Create your first ggbot"
- Added landing page footer with Terms, Privacy links + social icons (`new-landing/Footer.tsx`)

**Duplicate & Reset Button Fixes** (`api.ts`, `page.tsx`):
- Duplicate: Added `config_type` to `createConfig` API call (422 error fix)
- Reset: Added immediate `setAccounts` update after reset (UI now reflects $10k balance instantly)

**Arena Page Redesign** (`frontend/app/arena/page.tsx`):
- Season 1 hero section: badge, $2,500 prize pool, countdown timer to Jan 21 12:00 UTC
- Updated dates from prototype (Dec 18 - Jan 8) to Season 1 (Jan 21 - Feb 11)
- "Training Ground" framing for 7 prototype bots as examples
- Countdown timer with live seconds update, hydration-safe with `mounted` check

**Registration Mechanism** (`ggbot.py:3842-3943`):
- `POST /api/v2/bot/{config_id}/arena/register` - validates bot active + user subscribed, sets `is_public_performance = true`
- `POST /api/v2/bot/{config_id}/arena/unregister` - removes bot from competition
- Eligibility: must have active subscription + bot in 'active' state

**Frontend Registration Flow** (`frontend/components/arena-registration-modal.tsx`, `ActivationBar.tsx`):
- Registration modal with competition details, dates, prize info, account reset warning
- "Enter Arena" button in ActivationBar (paper trading bots only)
- "In Arena" badge shows when bot registered (`is_public_performance = true`)
- Added `is_public_performance` to `BotConfiguration` interface (`lib/api.ts`)

**Infrastructure** (also this session):
- Fixed 502 timeout issue: nginx proxy_read_timeout 300s, proxy_buffering off for SSE
- Increased APScheduler jitter 15s → 30s to spread bot execution load

---

## 2026-01-06 - Reasoning Tier Fix + Billing Accuracy + Upgrade Modal Redesign

**Reasoning Tier Bug** (`core/config/schemas.py`, `core/config/models.py`):
- `LLMConfig` Pydantic model missing `reasoning_tier` field → silently dropped on config load
- Bots configured economy/premium all ran as standard tier
- Added field with validator, backward compat with `thinking_mode`

**Billing Fix** (`decision/engine_v2.py:816-831`):
- Was using static `llm_models` table pricing (standard tier only)
- Economy users overcharged ~3x, premium users undercharged ~6x
- Now uses actual OpenRouter cost from `usage['cost']` + 70% markup
- Fallback to calculated cost if actual unavailable

**Upgrade Modal Redesign** (`frontend/components/UpgradeModal.tsx`, `ActivationBar.tsx`):
- Netflix-style checkout: bot name, value prop, cost estimate, trust bullets
- Bot-specific pricing based on model + tier + frequency
- Real cost data from production testing all 21 model+tier combinations
- Test script: `scripts/test_model_tier_costs.py`

**Extraction Fix** (`ggbot.py:580-610`):
- `_extract_indicators_from_config()` was collecting ALL data_points from ALL sources
- Market intelligence points (btc_funding_rate, etc.) passed to technical indicator calculator → warnings
- Fixed to only extract from `technical_analysis` source

---

## 2026-01-04 - Strategy Advisor Performance Analysis

Universal bot performance analysis engine. Surfaces hidden patterns users couldn't see manually.

**Backend** (`core/services/performance_analyzer.py`):
- Basic stats: WR, R:R ratio, breakeven WR, P&L
- Direction breakdown: long vs short performance
- Universal pattern extraction from market_query (technical + sentiment + volume)
- Pattern combination analysis: 2-pattern combos, confirmation vs risk patterns
- Timeframe alignment: multi-TF correlation with outcomes
- Exit reasoning classification: thesis_complete, trend_override, capitulation
- Confidence calibration: expected vs actual win rates per bucket
- Claude Haiku LLM synthesis for actionable recommendations
- Exit analysis caveat: LLM instructed early exits may have avoided worse losses (no counterfactual data)

**API**: `/api/v2/assistant/analyze/{config_id}` - returns full analysis with AI insights

**Frontend** (`StrategyAdvisorPanel.tsx`):
- Two buttons: "Create Strategy" (always), "Analyze Performance" (when bot has closed trades)
- Uses `/api/v2/bot/{config_id}/account` to check trade count
- Inline analysis report with stats, patterns, critical issues, positive edges, recommendations
- "Discuss with Strategy Advisor" sends report summary to chat for follow-up discussion

---

## 2026-01-04 - Activity Modal Redesign

Replaced bottom-sheet with centered modal for activity details. New `activity-modal.tsx` component with carousel navigation (swipe mobile, arrows desktop). Type-specific formatters for trade_entry, trade_exit, llm_thought, market_query. Fixed Framer Motion transform conflict by using flexbox centering wrapper. Updated all 3 decision prompts with structured REASONING format (KEY_SIGNAL, SUPPORTING, RISK, SUMMARY) - frontend parses with graceful fallback.

---

## 2025-12-28 - Symphony Position Display Fix

**Root Cause**: SSE dashboard returned NULL for Symphony positions, enrichment function existed but never called

**Fixes Applied**:
- symphony_service.py: Added collateralAmount, pnlPercentage, liquidationPrice, status fields
- symphony_adapter.py: Calculates margin_used from sum of position collateral fields
- dashboard_data.py: Enabled `_enrich_live_positions_and_accounts()`, fixed source filter 'symphony' (was 'live')
- PositionsTable.tsx: Added 'symphony' source type, close button routing

---

## 2025-12-27 - Error Log Fixes

- **binance_funding Adapter**: gateway.py lacked derivatives category pattern → added `elif 'funding' in snake_case`
- **WebSocket Queue Overflow**: Increased max_queue_size 100→1000 (700 streams overwhelmed default)
- **Redis TTL**: Timeframe-aware TTL for 4h/1d/1w (was 1h TTL < candle interval) → TIMEFRAME_TTL mapping
- **Minor**: KC indicator alias, volume log wording fix

---

## 2025-12-27 - Arena Activity Timeline + TradeSettings Fix

- **Arena Timeline**: 3 public endpoints (balance-series, activities, metadata), lazy-loaded timeline in expanded accordion
- **TradeSettings Fix**: Nested object data loss on save → added spread operator for position_sizing
- **TP/SL Labels**: "Stop Loss (%)" → "Stop Loss (price drop %)", added leverage P&L explanation

---

## 2025-12-19 - ggArena Bot Strategy Tuning

7 arena bots prepared for competition. Created `trading/strategies/*.md`. Revised prompts with action bias (0.55+ threshold vs 0.75+), removed paralysis language. Key insight: 4/5 Technician losers = longs against bearish 1H regime → added regime gating.

## 2025-12-18 - Bot Profile Images + Arena Enhancements

**Full Documentation**: [DOCS/completed/2024-12-18_bot_avatars_arena_enhancements.md](DOCS/completed/2024-12-18_bot_avatars_arena_enhancements.md)

## 2025-12-17 - Bot Image Upload + Arena Page + TV Timeline Dual-Mode

- **Image Upload**: Fixed name preservation, SSE query, frontend sync
- **Arena**: Public leaderboard /arena, Recharts multi-line, 21-day competition, no auth
- **TV Timeline**: Dual-mode (Activity/Performance), timeframe aggregation (5M/1H/4H/1D)
- **Bot Limit Removed**: Dropped PostgreSQL trigger, frontend 10-bot limit removed

---

## 2025-12-15 - Account Metrics Standardization

**Full Documentation**: [DOCS/completed/2025-12-10_position_sizing_simplification.md](DOCS/completed/2025-12-10_position_sizing_simplification.md)

Major refactor: Created `core/domain/metrics_calculator.py` as single source of truth for all account metrics. Eliminated 6 duplicate formula implementations → 1. Added total_equity column to activities table. Updated API responses with comprehensive account metrics. Added Account Metrics Glossary to README.md.

---

## 2025-12-14 - Admin Dashboard Equity Fix + Bot Comparison

- **Equity Fix**: Removed margin_used from calculation (was double-counting) → `current_balance + unrealized_pnl`
- **Bot Comparison**: GET /api/v2/admin/bots/equity-comparison, Recharts line chart, profile images, time selectors

---

## 2025-12-10 - Position Sizing Simplification (BREAKING)

**Full Documentation**: [DOCS/completed/2025-12-10_position_sizing_simplification.md](DOCS/completed/2025-12-10_position_sizing_simplification.md)

Removed position sizing methods, simplified to confidence-based only. Deleted PositionSizingMethod enum, renamed max_position_percent → max_margin_percent. New defaults: leverage 5x, max_margin 20%, SL 5%, TP 10%.

## 2025-12-10 - Frontend/Backend Validation Mismatch + Stop Loss Inversion Fix

- **Validation**: Backend le=25 vs Frontend max=100 → increased backend limit, added frontend validation
- **Stop Loss Inversion**: Parser extracted Bollinger Band values as SL/TP → added directional validation, removed LLM SL/TP fields from prompts, config defaults always apply

---

## 2025-12-05 - Admin Dashboard + Signal Filtering + Strategy Advisor

**Full Documentation**: [DOCS/completed/ADMIN_DASHBOARD.md](DOCS/todo/ADMIN_DASHBOARD.md)

- **Admin Dashboard**: /admin with 13 endpoints (stats, services, billing, users, bot control)
- **Signal Filtering**: Symphony bots only receive 100 compatible symbols (42 filtered)
- **Strategy Advisor**: Character creation UX, 4-scenario framework, reasoning tier system (economy/standard/premium)
- **Strategy Unification**: Agent bots now use same ConfigureLayout as scheduled bots
- **Resend Fix**: Added 600ms delay between sync and send (rate limit)
- **Grok Timeouts**: Query-specific timeouts (NFP 300s, Twitter 180s, VIX 120s)

---

## 2025-12-04 - Unified Config Saving + Symphony Win Rate Fix

**Full Documentation**: [DOCS/completed/UNIFIED_CONFIG_SAVING.md](DOCS/completed/UNIFIED_CONFIG_SAVING.md)

- Batched config save: 40+ API calls → 1, 5s debounce, dirty field tracking
- Symphony win_rate: Divided by 100 (was overflow NUMERIC(5,4))

---

## 2025-11-30 - Activity Timeline Data Visibility

Market query activities now log exact LLM prompt data. Frontend bottom sheet shows formatted sections. Fixed llm_thought field name (reasoning→thought). ggShot config enforcement (only fetch if enabled in bot config).

---

## 2025-11-23 - Balance Tracking + API Fixes

- **Balance**: Fixed race condition (log after update), removed duplicate logging, added total_pnl to Redis
- **API**: Added missing fields to GET /config/{id} (state, trading_mode, symphony_agent_id, updated_at)
- **Frontend**: TypeScript fixes, theme-adaptive colors
- **Auto-Save**: Fixed missing config_name/config_type params overwriting bot names

---

## 2025-11-20 - Legal + Trading Mode Refactor + AsterDEX

**Full Documentation**: [DOCS/completed/trading-mode-refactor.md](DOCS/completed/trading-mode-refactor.md)

- **Legal**: Terms, Privacy, signup disclaimer, risk modal for live trading
- **Trading Mode**: execution_mode removed, single source trading_mode column
- **AsterDEX**: 1,394-line aster_service_v3.py, Web3 signatures, 33 compatible symbols
- **Market Maker**: Avellaneda-Stoikov engine for Kuru DEX (~900 lines experimental)

---

## 2025-11-19 - Strategy Advisor Auto-Save

Replaced floating modal + SaveConfigBar with always-visible 500px panel. Auto-save with 1s debounce, optimistic updates, rollback on error. Added SaveStatusContext for global status coordination.

---

## 2025-11-16 - Universal AI Assistant + Metered Billing + Critical Fixes

**Full Documentation**: [DOCS/completed/METERED_BILLING_IMPLEMENTATION.md](DOCS/completed/METERED_BILLING_IMPLEMENTATION.md)

- **AI Assistant**: `/api/v2/assistant/chat` with 3 tools, Claude Haiku function calling, bottom sheet modal
- **Metered Billing**: Stripe Billing Meters operational, weekly invoicing, $0.107734 first period
- **OpenRouter Migration**: 7 providers, 14 variants, llm_models table
- **ActivationBar**: Replaced pipeline ticker with activity-based status + KPIs
- **Critical Fixes**: WebSocket cache 3→100 candles, SSL connection pooling (5-20 conn)

---

## 2025-11-15 - Snapshot Timeline + Activities Overhaul + Account Monitoring

**Full Documentation**: [DOCS/completed/snapshot_timeline_workstream1_complete.md](DOCS/completed/snapshot_timeline_workstream1_complete.md)

- Snapshot-optimized chart, time-based X-axis, activities-only query
- Activities logging overhaul: llm_thought standalone, auto trade_entry/exit, 1%→95% visibility
- Universal Account Monitoring: PM2 service, 5s checks, 5min snapshots, adapter pattern
- Symphony mode migration: trading_mode='live'→'symphony'

---

## 2025-11-13 - Metered Billing Infrastructure + Agent/RLS/Aster Fixes

Core billing w/ daily reporting, tier architecture (FREE/USAGE_BASED/PRO). LLM Pricing Service (70% markup). RLS secured activities/agent_sessions/llm_models. Aster: proper sizing, income API (26 missing trades recovered).

---

## 2025-11-11 - Confidence Sizing + OpenRouter UI

Tested confidence-based sizing paper/symphony/aster. Formula: margin = confidence × max_margin × balance. Model selection UI: 7 models, colored logos, thinking toggle. Tailwind dark mode theme system.

---

## 2025-11-10 - Config System Cleanup v2.2 + 5 Critical Fixes

373 bots migrated autonomous_trading→scheduled_trading. Deleted execution_mode JSONB. 5 fixes: Config save 404, SSE missing config_type, OpenRouter enum, timeline race, Aster metrics zero.

---

## 2025-11-08 - Agent Session Resumption + Timeline in Forge

Agents survive crashes via Claude SDK session resumption (80-90% context loss reduction). Replaced DecisionFeed+PerformanceChart with full-width TVTimeline.

---

## 2025-11-07 - TradingView Timeline + Agent Strategy v4

Professional TradingView Lightweight Charts: line chart 700+ points, markers (trades, queries, thoughts, waits), bottom sheet. Agent dynamic symbol discovery via ggshot scan.

---

## 2025-11-06 - Ceremonial Brutalism Rebrand

Obsidian/ivory/brass palette, Bodoni Moda/Space Grotesk/IBM Plex Mono typography. 56 emojis→Lucide icons. 18 files modified.

---

## 2025-11-03 - Agent Phase 4c Autonomous + Activity Timeline

24/7 autonomous trading live, 13+ min tested. Activities table 14 cols, 7 indexes, activity logger, 3 endpoints.

---

## 2025-11-02 - AsterDEX Integration Phase 1

142 ggbot vs 140 Aster → 33 compatible (23.2%). aster_service_v3.py Web3 ECDSA auth. Full trade cycle tested.

---

## 2025-11-01 - Agent Phase 3 + Maintenance Mode

Live autonomous trading operational. Maintenance mode: 59 bots deactivated, 24 positions closed ($186.88 P&L).

---

## 2025-10-30 - Activity Timeline Viewer

Canvas timeline /view/[config_id], 850 lines, 60fps. Drag pan, zoom levels.

---

## 2025-10-28 - Market Intelligence LIVE

8 Grok sources LIVE: VIX, DXY, CPI, NFP, BTC TVL, whale, Twitter, news. $195/mo platform cost. Parallel 160s→30s (5.3x).

---

## 2025-10-27 - Intelligence Orchestrator

orchestrator.py (260 lines), GrokAgenticAdapter. 7 categories, 24 data points.

---

## 2025-10-26 - ggShot Universal Data

878 signals backfilled 60 days. Multi-timeframe, dual mode (push validation + pull autonomous).

---

## 2025-10-24 - Hybrid Price Service + Symphony Dashboard

142 symbols: WebSocket (100 <1ms) + REST fallback (42 ~100ms). SSE fetches Symphony parallel.

---

## 2025-10-19 - Symphony Integration + Universal Data Layer

Vault encrypted storage, symphony_service.py. 100/141 symbols compatible. MarketIntelligence gateway 3x-3000x faster.

---

## 2025-10-11 - Resend Email

189/261 users synced, welcome emails on signup.

---

## 2025-10-04 - Trading Fixes

Manual close button, trade settings validation. Position sizing FIXED, P&L FIXED (removed double leverage). Account reset: 92 deactivated.

---

## 2025-10-03 - LLM Performance

GPT-5 Responses API, PRO 200s timeout. Extraction parallel ~60s saved.

---

## 2025-10-01 - Stripe Monetization

$29/mo Pro 14-day trial, annual $279/yr. 4 webhook events, billing portal. EARLY50 coupon.

---

## Earlier (Pre-Oct 2025)

- **Scheduler**: APScheduler, zero-drift candles, Redis idempotency, 5m-1d multi-timeframe
- **Signal Validation**: ggShot AI confidence, premium gating, Telegram publishing
- **Paper Trading**: WebSocket prices (sub-ms), $10k isolated, 3s monitoring, liquidation
- **Core V2**: Frontend SSE real-time, decision carousel, Vercel Analytics
- **Disk Crisis (Sept 27)**: Docker log 26GB freed, batch SQL 99% reduction
- **Multi-Exchange (Sept 19)**: 5 exchanges failover

---

**Documentation**: See README.md (architecture), ACTIVE.md (production status), TODO.md (roadmap)
