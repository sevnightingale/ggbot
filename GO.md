# GO.md - Claude Code Onboarding Procedure

**Purpose**: Standard onboarding protocol for fresh Claude Code instances working on the ggbots platform.

---

## 📋 Onboarding Checklist

When a user says "read GO.md" or similar, follow this procedure:

### Step 1: Run Status Check Script (with auto-update)

Get fresh, accurate platform metrics and auto-update documentation:

```bash
source .venv/bin/activate && python scripts/status_check.py --update
```

This will:
- Query current user count and subscription breakdown
- Query active bot count and trading mode split
- Query recent trading activity (24h/7d/30d)
- Query open positions and system health
- Query top trading symbols and decision activity
- **Auto-update ACTIVE.md** with current stats
- **Auto-update README.md** with current database schema

Use these **real-time numbers** in your assessment instead of relying on potentially outdated documentation.

**Important**: The `--update` flag ensures README.md always has the current database schema, so you never have to guess column names.

### Step 2: Read Core Documentation (in order)

Read these four files to understand the project:

1. **README.md** - Platform architecture and overview
2. **ACTIVE.md** - Current production status and operational reference
3. **TODO.md** - Current tasks and development roadmap
4. **CHANGELOG.md** - Complete history of features and improvements

### Step 3: Provide Brief Assessment

After reading all four files, provide a **brief assessment** (1-2 paragraphs) covering:

- **Production Status**: Current system health, user count, active features
- **Recent Progress**: Last 1-2 major completions from CHANGELOG.md
- **Current Focus**: What's in progress or next priority from TODO.md
- **Architecture State**: Any notable technical details or blockers

Keep it concise - this is a "state of the union" snapshot, not a detailed report.

**Important**: Use the real-time metrics from Step 1's status check in your assessment, not the numbers in the documentation (which may be outdated).

### Step 4: Ask What To Work On

Present the current priorities from TODO.md and ask:

> "What would you like to work on from the TODO list? We have:
>
> 🟡 **IN PROGRESS**: [current in-progress items]
>
> 🔴 **HIGH PRIORITY**: [high priority items]
>
> 🟠 **MEDIUM PRIORITY**: [medium priority items]
>
> Which area would you like to focus on?"

---

## 🔄 During Development: Documentation Maintenance

As you work with the user, **maintain documentation discipline**:

### TODO.md Maintenance (CRITICAL)

As you work on tasks, **keep TODO.md updated in real-time**:

- **Check off items** `[ ]` → `[x]` IMMEDIATELY when completed (don't batch)
- **Add new items** when discovering additional work during implementation
- **Move completed sections** to CHANGELOG.md when an entire feature/phase is done
- **Update status indicators** (🟡 IN PROGRESS, 🔴 HIGH PRIORITY, etc.) as priorities shift
- **Keep it current**: TODO.md should always reflect actual work state

### When Work is Completed

When a significant feature/fix is done:

1. **Update CHANGELOG.md** (COMPRESSED FORMAT):
   - Add entry under date: `## YYYY-MM-DD - Brief Title`
   - Use **ultra-concise bullet points** - sacrifice grammar for brevity
   - Format: `- **Category**: What changed, key metric, files`
   - Example: `- **Tool**: get_current_price - Sub-ms WebSocket lookup with REST fallback`
   - NO paragraphs, NO explanations, NO narrative - ONLY essential facts
   - Include: files changed, performance numbers, bug root cause (1 line max)
   - Target: 3-8 bullets per entry, NOT 20+ line paragraphs

2. **Update TODO.md**:
   - Move completed checkbox items from TODO → CHANGELOG
   - Remove fully completed sections
   - Keep TODO.md focused on forward-looking tasks only

3. **Update ACTIVE.md** (if applicable):
   - Update "Current Development Focus" if priorities shift
   - Update service status, ports, or production features if changed
   - Keep ACTIVE.md as lean operational reference

### When Production Status Changes

If the user mentions deployment, new user counts, or system changes:

- **Run status check script**: `python scripts/status_check.py --update` to auto-update ACTIVE.md header
- **Update user counts**: Use real numbers from status check (not guesses)
- **Update service status**: PM2 services, infrastructure, background tasks

### Planning Document Lifecycle

For significant TODO items (multi-day work, complex features), maintain planning documents in DOCS/:

**When to Create a Planning Doc:**
- TODO sections with >3 day timeline
- Complex features requiring architectural decisions
- Work involving multiple systems or significant refactoring
- When user explicitly requests planning/design phase

**Linking TODO Sections to Planning Docs:**
- Add `[doc-name.md]` suffix to TODO section titles
- Example: `## 🤖 **HIGH PRIORITY - Autonomous Trading Agent** [AGENT.md]`
- Planning doc lives in `DOCS/todo/doc-name.md` (implicit path)
- Update TODO.md section to include: `**See**: [DOCS/todo/AGENT.md](DOCS/todo/AGENT.md) for complete architecture`

**During Active Work:**
- Keep planning doc in `DOCS/todo/` as single source of truth
- Update planning doc as you learn and pivot (don't create new versions)
- Add "REVISION HISTORY" section at top if major pivots occur
- Document key architectural decisions and trade-offs as you go

**On Completion:**
1. **Add completion metadata** to top of planning doc:
   ```markdown
   ---
   COMPLETED: YYYY-MM-DD
   CHANGELOG_ENTRY: ## YYYY-MM-DD - Brief Title
   TODO_SECTION: [Original TODO section name]
   ---
   ```
2. **Move planning doc**: `DOCS/todo/doc-name.md` → `DOCS/completed/doc-name.md`
3. **Update CHANGELOG.md** with completion entry (compressed format, as usual)
4. **Update TODO.md**: Remove completed section or mark complete
5. **Archive context**: Completed doc preserves all decisions and pivots for future reference

**Benefits:**
- **Traceability**: Know which planning doc supports which TODO item
- **Reduced clutter**: Active vs historical planning docs are separated
- **Preserved context**: Architectural decisions don't get lost
- **Clean pivots**: Planning docs evolve in place, show full journey

---

## ⚠️ Common Pitfalls

**Database Schema**:
- ❌ DON'T propose new tables without checking ACTIVE.md database section first
- ❌ DON'T assume you need a new table for new data types
- ✅ DO check if `market_data` table can handle it (see Database Architecture Philosophy in ACTIVE.md)
- ✅ DO follow existing `data_sources` + `data_points` metadata pattern

**Architecture Patterns**:
- ❌ DON'T reinvent existing patterns - ask user first if unsure
- ✅ DO check ACTIVE.md for existing system architecture before proposing solutions

---

## 💡 Development Workflow Reminders

- **Always activate virtual environment**: `cd /home/sev/ggbot && source .venv/bin/activate`
- **Never hardcode credentials**: Use .env variables only
- **Check before running tests**: Always confirm with user before test execution
- **Frontend deployment**: Changes deploy via git push to Vercel (no localhost for user testing)
- **Update TODO.md as you work**: Check off items immediately, keep it current with actual progress

---

## 🎯 Quick Reference

**Project Type**: Autonomous AI trading platform (ggbots.ai)
**Architecture**: Three-agent pipeline (Extraction → Decision → Trading)
**Production**: Live with 256+ users, 57+ active bots (run status check for latest)
**Current Phase**: Symphony live trading polish + UX improvements

**Key Technologies**:
- Backend: Python, FastAPI, APScheduler, PostgreSQL (Supabase), Redis
- Frontend: Next.js, TypeScript, Vercel deployment
- Trading: Paper trading engine + Symphony.io live trading integration
- AI: GPT-5, Claude Opus 4, DeepSeek R1, XAI Grok (frontier reasoning models)

---

**When in doubt, refer back to this file or ask the user for clarification. Documentation hygiene is critical for long-term project maintainability.**
