# TODO.md - GGBot V1 Private Beta Launch

## Phase 1: Infrastructure Foundation (Supabase Migration) ✅ COMPLETE

- ✅ sev: Create new Supabase project and obtain API keys/connection string
- ✅ sev: Enable MFA on Supabase organization account
- ✅ sev: Set up Supabase environment variables in .env file (anon key for frontend, service key for backend)
- ✅ claude: Create database migration scripts for all existing tables with RLS policies
- ✅ claude: Add user_id and config_id columns to all relevant tables
- ✅ claude: Implement Row Level Security policies for multi-user isolation using auth.uid() pattern
- ✅ claude: Enable SSL enforcement for Postgres connections in Supabase settings
- ✅ claude: Update database connection in core/common/db.py to use Supabase
- ✅ claude: Create Supabase auth helper utilities in core/auth/

## Phase 2: Extraction Accuracy Testing (Proof-of-Concept Approach)

**Strategy**: Build alternative Hummingbot API + pandas-ta extraction and see if it "just works"

- claude: Install pandas-ta library
- claude: Create proof-of-concept RSI test using Hummingbot API + pandas-ta pipeline
- claude: Compare alternative RSI output with current MCP RSI output
- sev: Review results and make decision: expand alternative approach or fix MCP system
- claude: Implement chosen extraction approach based on test results

## Phase 2.5: Business Model Architecture (New - Post-Pivot)

### Critical Decision Research
- ✅ sev: Decide LLM API key storage approach (user-level named credentials + config selection, Supabase Vault encryption)
- ✅ sev: Define subscription enforcement strategy (Simple Free/Signals tiers, basic Stripe, no usage-based pricing)
- ✅ sev: Choose signal publishing approach (Action-only signals per bot, BUY/SELL only, no "wait" spam)
- ✅ sev: Design Telegram integration architecture (One channel per bot config, no confidence filtering)
- ✅ sev: Define security requirements for user API key encryption (Supabase Vault with RLS policies)

### Business Setup Required (Blockers)
- ⚠️ sev: Set up Stripe account and define pricing ($X/month for Signals tier)
- ⚠️ sev: Configure Supabase Vault (enable extension, test encrypted key storage)
- ⚠️ sev: Define exact Stripe webhook events needed for subscription management
- ✅ sev: Telegram bot already exists (ggshot infrastructure can be adapted)

### Database Schema Updates
- claude: Enable Supabase Vault extension (after sev configures Vault access)
- claude: Add subscription_tier enum ('free', 'signals') and subscription_status to Supabase
- claude: Create user_profiles table with Stripe integration fields
- claude: Create user_llm_credentials table with Supabase Vault integration
- claude: Create bot_telegram_channels table for per-bot channel mapping
- claude: Create stripe_webhooks table for event tracking
- claude: Implement Supabase Vault API key storage/retrieval utilities
- claude: Add Row Level Security policies for all new tables

### LLM Client Abstraction
- claude: Create subscription-aware LLM client factory with Vault integration (Free vs Signals only)
- claude: Implement user named credential lookup and validation
- claude: Add hosted vs user credential routing logic (simplified for two tiers)
- claude: Create basic usage tracking for analytics

### Subscription Middleware
- claude: Create @requires_subscription decorator for clean feature gating
- claude: Implement subscription checking middleware for API endpoints
- claude: Add standardized error responses for subscription requirements

### Telegram Bot Infrastructure (Will be handled in Phase 9 ggShot integration)
- ✅ Existing: ggshot/ggshot_publisher.py has Telegram bot infrastructure
- Note: Will adapt existing GGShotPublisher for per-bot channel publishing in Phase 9
- Note: Current bot uses GG_FILTER_TOKEN and FILTER_CHANNEL_ID env vars

### Frontend Integration
- claude: Add subscription tier display to user dashboard (Free vs Signals)
- claude: Create named LLM credential management interface ("My API Keys" section)
- claude: Implement LLM credential selection dropdown in bot configuration
- claude: Implement per-bot Telegram channel setup workflow
- claude: Create pricing page with Stripe integration
- claude: Add subscription upgrade flow (Free → Signals)
- claude: Create subscription-gated feature flags in UI

### Stripe Integration (New)
- sev: Set up Stripe account and get API keys
- claude: Implement Stripe subscription creation for Signals tier
- claude: Create webhook handler for subscription events
- claude: Add subscription management endpoints (upgrade/cancel)
- claude: Implement subscription status checking middleware

## Phase 3: Backend Authentication & Config API

- claude: Update core/api/config_api.py to use Supabase auth middleware
- claude: Add user_id extraction from JWT tokens in API endpoints
- claude: Implement proper CRUD endpoints for bot configurations
- claude: Add bot lifecycle endpoints (start/stop/pause) in config API
- claude: Create bot status tracking table and endpoints
- claude: Implement config-specific data isolation in all repositories
- claude: Update market_data_repository to filter by config_id

## Phase 4: Orchestrator Implementation

- claude: Create core/orchestrator.py with GGBotOrchestrator class
- claude: Implement run_autonomous_cycle method with database polling
- claude: Add _wait_for_fresh_indicators with 70% completion threshold
- claude: Implement partial completion handling logic
- claude: Create extraction service wrapper for config-based extraction
- claude: Integrate DecisionEngineV2 into orchestrator flow
- claude: Add real-time status updates via Supabase channels
- claude: Implement error handling and retry logic in orchestrator
- claude: Create orchestrator scheduling mechanism

## Phase 5: Frontend Authentication

- claude: Install Supabase JS client in frontend/package.json
- claude: Create auth context provider with Supabase auth
- sev: Set up Google OAuth app in Google Cloud Console and add credentials to Supabase
- sev: Set up GitHub OAuth app in GitHub Developer settings and add credentials to Supabase
- claude: Implement login/signup pages with Supabase Auth UI (email/password + magic links + Google + GitHub)
- claude: Add protected route wrapper for authenticated pages
- claude: Ensure frontend uses only anon/publishable keys, never service keys
- claude: Implement logout functionality and session management
- claude: Add user profile state management

## Phase 6: Dashboard Implementation

- claude: Duplicate frontend/app/demo to frontend/app/dashboard
- claude: Remove all mock data constants from dashboard/page.tsx
- claude: Remove demo state variables and demo logic
- claude: Implement selectedConfigId state management
- claude: Create Supabase real-time subscriptions for bot updates
- claude: Connect dashboard cards to real API endpoints
- claude: Update trade tables to fetch from paper_trades table
- claude: Implement bot selector in GGBot circle component
- claude: Add loading states and error handling
- claude: Implement localStorage persistence for selectedConfigId

## Phase 7: Frontend-Backend Integration

- claude: Align BotConfig TypeScript interface with backend model
- claude: Update frontend API calls to include auth headers
- claude: Implement real-time WebSocket to Supabase channel migration
- claude: Connect bot start/stop controls to backend endpoints
- claude: Implement config creation form with real API
- claude: Add performance metrics fetching from strategy_runs
- claude: Update position tracking to use real positions table

## Phase 8: Testing & Validation

- sev: Test user signup and login flow
- sev: Test bot configuration creation
- claude: Create tests/test_user_flow.py for auth testing
- claude: Implement test_autonomous_trading_cycle end-to-end test
- sev: Test dashboard bot switching functionality
- sev: Validate real-time updates are working
- claude: Test multi-user data isolation
- sev: Test paper trading execution flow

## Phase 9: ggShot Integration Cleanup

- sev: Design user permission system for ggShot indicator access (premium/locked feature)
- sev: Plan Telegram signal listener integration with config_id-based architecture
- sev: Define Signal Validation mode requirements vs current custom signal handling
- claude: Update extraction module to support Signal Validation mode properly
- claude: Create user permission checks in config API for ggShot indicator
- claude: Create ggshot/config_converter.py for signal to config conversion
- claude: Update ggshot to use standard BotConfig model
- claude: Integrate ggshot with orchestrator flow using Signal Validation mode
- claude: Remove custom ggshot database tables and migrate to standard domain models
- claude: Adapt existing ggshot/ggshot_publisher.py for per-bot channel publishing
- claude: Update Telegram publishing to use bot_telegram_channels table instead of hardcoded channel
- claude: Update ggshot PM2 configuration
- sev: Test ggshot signal validation with new flow and permission system

## Phase 10: Cleanup & Polish

- claude: Remove all remaining demo hardcoded values
- claude: Clean up legacy code and unused files
- claude: Add comprehensive error boundaries
- claude: Implement proper logging throughout
- sev: Review mobile responsiveness of dashboard
- claude: Add user feedback messages for all actions
- sev: Final testing of complete user journey
- sev: Deploy to staging environment for beta testing