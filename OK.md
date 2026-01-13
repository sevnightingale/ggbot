# OK.md - Documentation Update Workflow

**Purpose**: Mid-session command to update documentation following proper SOP. Invoke with `@OK.md` when work is complete or at logical checkpoints.

---

## Two-Tier Documentation Strategy

### Tier 1: Core Docs (Concise, Surgical)

**Files**: `README.md`, `ACTIVE.md`, `TODO.md`, `CHANGELOG.md`

**Style**: Telegraphic. Omit articles (a, an, the). Maximum information density. No redundancy.

**Why**: Loaded at START of every session. Verbosity wastes context tokens.

| Doc | Purpose | Update Frequency |
|-----|---------|------------------|
| README.md | Architecture overview, capabilities | Rare (major features only) |
| ACTIVE.md | Current production status, services, ports | When infra changes |
| TODO.md | Active tasks, planning links | Remove completed, add new |
| CHANGELOG.md | Historical record with file references | Every completed feature |

### Tier 2: Module Docs (Detailed, Comprehensive)

**Files**: `trading/README.md`, `extraction/v2/README.md`, `decision/README.md`, `frontend/README.md`, `agent/README.md`, `market_intelligence/README.md`, etc.

**Style**: Thorough. Include examples, edge cases, implementation details.

**Why**: Only loaded when working on that module. Full context prevents mistakes. Often stale.

---

## SOP Checklist

When completing a feature or fix, execute in order:

### 1. Planning Doc Lifecycle
```
IF planning doc exists in DOCS/todo/:
  - Move to DOCS/completed/
  - Reference in CHANGELOG entry
```

### 2. TODO.md Updates
```
- REMOVE completed sections entirely (don't mark ✅ and leave)
- Add new tasks discovered during implementation
- Update status badges on in-progress work
```

### 3. CHANGELOG.md Entry
```
## YYYY-MM-DD - Feature Name

**Planning Doc**: [DOCS/completed/FEATURE.md](DOCS/completed/FEATURE.md)

**Section Name** (`file.py:line-range`):
- Bullet points, telegraphic style
- Include file references
- Technical accuracy over prose
```

### 4. Module README Updates
```
IF work touched a module significantly:
  - Update that module's README.md
  - Add new components/functions/endpoints
  - Update architecture diagrams if needed
  - Include usage examples
```

### 5. Core Doc Updates (if needed)
```
README.md - Only for major new capabilities
ACTIVE.md - Only for infrastructure/service changes
```

---

## Style Guide Quick Reference

### CHANGELOG.md (Telegraphic)
```markdown
**Good**: `GET /api/v2/credits/balance` - Returns Stripe credit balance
**Bad**: Added a new endpoint called GET /api/v2/credits/balance which returns the user's Stripe credit balance
```

### TODO.md (Status Badges)
```markdown
🔴 URGENT - Immediate action required
🟡 IN PROGRESS - Currently being worked on
🔵 PLANNING - Has planning doc, not started
⚪ BACKLOG - Future consideration
```

### Module READMEs (Detailed)
```markdown
Include:
- Architecture overview
- File structure with descriptions
- Key functions/classes with signatures
- Usage examples
- Edge cases and gotchas
- Related modules/dependencies
```

---

## File Location Reference

```
/home/sev/ggbot/
├── README.md              # Core: Architecture overview
├── ACTIVE.md              # Core: Production status
├── TODO.md                # Core: Active tasks
├── CHANGELOG.md           # Core: Historical record
├── GO.md                  # Onboarding procedure
├── OK.md                  # This file - doc update workflow
├── CLAUDE.md              # Development workflow
│
├── DOCS/
│   ├── todo/              # Planning docs for active work
│   └── completed/         # Archived planning docs
│
├── trading/README.md      # Module: Trading modes, position management
├── extraction/v2/README.md # Module: Data extraction, indicators
├── decision/README.md     # Module: Decision engine, LLM prompts
├── frontend/README.md     # Module: React components, architecture
├── agent/README.md        # Module: Agent behavior, MCP tools
└── market_intelligence/README.md # Module: Grok, news sources
```

---

## Example Invocation

User: `@OK.md` or "update docs"

Claude should:
1. Check if planning doc exists → move to completed
2. Remove completed section from TODO.md
3. Add CHANGELOG entry (telegraphic, with planning doc link)
4. Update relevant module READMEs (detailed)
5. Touch core docs only if necessary

---

**Remember**: Core docs are "hot" (read every session). Module docs are "cold" (read on-demand). Hot = efficient. Cold = complete.
