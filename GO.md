# GO.md - Claude Code Onboarding Procedure

**Purpose**: Standard onboarding protocol for fresh Claude Code instances working on the ggbots platform.

---

## 📋 Onboarding Checklist

When a user says "read GO.md" or similar, follow this procedure:

### Step 1: Read Core Documentation (in order)

Read these four files to understand the project:

1. **README.md** - Platform architecture and overview
2. **ACTIVE.md** - Current production status and operational reference
3. **TODO.md** - Current tasks and development roadmap
4. **CHANGELOG.md** - Complete history of features and improvements

### Step 2: Provide Brief Assessment

After reading all four files, provide a **brief assessment** (1-2 paragraphs) covering:

- **Production Status**: Current system health, user count, active features
- **Recent Progress**: Last 1-2 major completions from CHANGELOG.md
- **Current Focus**: What's in progress or next priority from TODO.md
- **Architecture State**: Any notable technical details or blockers

Keep it concise - this is a "state of the union" snapshot, not a detailed report.

### Step 3: Ask What To Work On

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

### TodoWrite Usage (CRITICAL)

- **Use TodoWrite tool for ANY multi-step task** (3+ steps or non-trivial complexity)
- **Mark todos as in_progress** BEFORE starting work on them
- **Mark todos as completed** IMMEDIATELY after finishing (don't batch completions)
- **Add new todos** when discovering additional work during implementation
- **Exactly ONE todo in_progress** at any time (not less, not more)

### When Work is Completed

When a significant feature/fix is done:

1. **Update CHANGELOG.md**:
   - Add entry under appropriate date (create new date section if needed)
   - Use consistent format: **Feature Name** + bullet list of changes
   - Include files changed, performance metrics, impact notes
   - Keep entries factual and concise

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

- **Update ACTIVE.md header**: "Last Updated" date and system status
- **Update user counts**: "225+ users, 100+ bots" if numbers change significantly
- **Update service status**: PM2 services, infrastructure, background tasks

---

## 💡 Development Workflow Reminders

- **Always activate virtual environment**: `cd /home/sev/ggbot && source .venv/bin/activate`
- **Never hardcode credentials**: Use .env variables only
- **Check before running tests**: Always confirm with user before test execution
- **Frontend deployment**: Changes deploy via git push to Vercel (no localhost for user testing)
- **Use TodoWrite proactively**: Break down complex tasks, track progress visibly

---

## 🎯 Quick Reference

**Project Type**: Autonomous AI trading platform (ggbots.ai)
**Architecture**: Three-agent pipeline (Extraction → Decision → Trading)
**Production**: Live with 225+ users, 100+ active bots
**Current Phase**: Symphony live trading integration + UX polish

**Key Technologies**:
- Backend: Python, FastAPI, APScheduler, PostgreSQL (Supabase), Redis
- Frontend: Next.js, TypeScript, Vercel deployment
- Trading: Paper trading engine + Symphony.io live trading integration
- AI: GPT-5, Claude Opus 4, DeepSeek R1, XAI Grok (frontier reasoning models)

---

**When in doubt, refer back to this file or ask the user for clarification. Documentation hygiene is critical for long-term project maintainability.**
