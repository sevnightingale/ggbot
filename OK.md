# OK.md - Documentation Update Workflow

**Purpose**: Mid-session command to update documentation. Invoke with `@OK.md` when work is complete or at logical checkpoints.

---

## Core Principle: Index-Driven Review

Every documentation update starts by reviewing README.md's index tables against the session's changes. This catches stale references that accumulate when docs are only updated "when necessary."

---

## SOP Checklist

Execute in order. Each step may produce zero changes — that's fine. The review itself is the value.

### 1. Review README.md Index

Read the following sections in README.md and compare against this session's work:

| Section | What to check |
|---------|---------------|
| **Codebase Structure table** | New directories? Changed purposes? Status changes? |
| **Architecture diagrams** | New services? Changed data flows? |
| **Core Agent descriptions** | New capabilities? Deprecated integrations? |
| **Tech Stack tables** | New providers? Version bumps? Removed dependencies? |
| **Trading & Data table** | New exchanges? Changed statuses? |
| **Infrastructure table** | PM2 services added/removed? Service counts? |
| **Module Documentation table** | New READMEs? Changed line counts? |

**Update README.md** for anything that's wrong or missing. This is the entry point for every new CC instance — stale info here cascades into bad assumptions.

### 2. Update Module READMEs

Walk the module docs table in README.md. For each module touched this session:

- Read its README.md
- Update architecture, file lists, key functions, usage examples
- Add new components/endpoints/patterns
- Remove deprecated content
- Module docs are "cold" (loaded on-demand) so be thorough — include edge cases, gotchas, examples

### 3. Update CLAUDE.md

Check and update:

| Section | What to check |
|---------|---------------|
| **Documentation Quick Reference table** | New module docs? Changed topic mappings? |
| **Development Guidelines** | New code patterns worth documenting? |
| **Database Access** | New tables, new access patterns? |
| **Two-Process Architecture** | Service changes? |
| **Permission System Pattern** | New permissions? |
| **Troubleshooting** | New common issues discovered? |

### 4. CHANGELOG.md Entry

```markdown
## YYYY-MM-DD - Feature/Fix Name

**Section Name** (`file.py:line-range`):
- Telegraphic style, omit articles
- Include file references, technical accuracy
- 3-8 lines for recent work
```

If a planning doc exists in `DOCS/todo/`, move it to `DOCS/completed/` and reference in the entry.

### 5. TODO.md

- Remove completed sections entirely (don't leave crossed-out items)
- Add new tasks discovered during implementation
- Update status badges on in-progress work

### 6. ACTIVE.md

Only if services/infrastructure changed (new PM2 process, new port, schema change). Usually auto-updated by `status_check.py`.

---

## Two-Tier Documentation Strategy

### Tier 1: Core Docs — "Hot" (loaded every session)

**Files**: `README.md`, `ACTIVE.md`, `TODO.md`, `CHANGELOG.md`, `CLAUDE.md`

**Style**: Telegraphic. Omit articles. Maximum information density. No redundancy.

**Why**: Loaded at START of every session. Verbosity wastes context tokens.

### Tier 2: Module Docs — "Cold" (loaded on-demand)

**Files**: `trading/README.md`, `extraction/v2/README.md`, `decision/README.md`, `frontend/README.md`, `agent/README.md`, `market_intelligence/README.md`, `trading/virtuals/README.md`, etc.

**Style**: Thorough. Include examples, edge cases, implementation details.

**Why**: Only loaded when working on that module. Full context prevents mistakes.

---

## Style Guide Quick Reference

### CHANGELOG.md (Telegraphic)
```markdown
Good: `GET /api/v2/credits/balance` — returns Stripe credit balance
Bad:  Added a new endpoint called GET /api/v2/credits/balance which returns the user's Stripe credit balance
```

### TODO.md (Status Badges)
```markdown
🔴 URGENT — Immediate action required
🟡 IN PROGRESS — Currently being worked on
🔵 PLANNED — Has planning doc, not started
⚪ BACKLOG — Future consideration
```

---

## File Location Reference

```
/home/sev/ggbot/
├── README.md              # Core: Architecture overview + INDEX
├── ACTIVE.md              # Core: Production status (auto-updated)
├── TODO.md                # Core: Active tasks
├── CHANGELOG.md           # Core: Historical record
├── CLAUDE.md              # Core: Development patterns + doc reference
├── GO.md                  # Onboarding procedure
├── OK.md                  # This file — doc update workflow
│
├── DOCS/
│   ├── todo/              # Planning docs for active work
│   └── completed/         # Archived planning docs
│
├── trading/README.md           # Module: Trading modes, Hyperliquid
├── trading/virtuals/README.md  # Module: DGClaw arena, ACP, claw API
├── extraction/v2/README.md     # Module: Data extraction, indicators
├── decision/README.md          # Module: Decision engine, LLM prompts
├── frontend/README.md          # Module: React components, architecture
├── agent/README.md             # Module: Agent behavior, MCP tools
├── market_intelligence/README.md # Module: MI orchestrator, adapters
└── billing/README.md           # Module: Stripe, credits, metered billing
```

---

**Remember**: The README.md index is the source of truth. If it's wrong, every new CC instance starts with wrong assumptions. Review it first, every time.
