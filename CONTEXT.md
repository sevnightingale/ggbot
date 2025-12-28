# Claude Code mastery: A 7-level guide for power users

**You're likely leaving performance and features on the table.** Your Code Server setup runs **2-4x slower** than local CLI, and you're missing critical features like checkpoints and `/rewind`. This guide maps the path from experienced user to master—covering the latest features (through December 2025), hidden capabilities, and expert workflows that separate intermediate users from those who've truly integrated Claude Code into their development process.

The research reveals several "unknown unknowns" that will likely transform your workflow: custom subagents for parallel work, the hooks system for automated quality enforcement, GitHub Actions integration for asynchronous tasks, and the thinking intensity triggers that unlock Claude's full reasoning capabilities.

---

## Level 1: Environment optimization — fix the Code Server bottleneck

Your browser-based Code Server environment is the first constraint to address. GitHub Issue #15172 documents that the VS Code extension in Code Server runs **2-4x slower** than local CLI—a task taking 30 seconds locally can take nearly 2 minutes in your current setup.

**Recommended migration path:**
| Environment | Performance | Features | Best For |
|-------------|-------------|----------|----------|
| **Local CLI** | ✅ Fastest | ✅ Full (checkpoints, /rewind, MCP config) | Maximum capability |
| **VS Code Extension (local)** | ✅ Fast | ⚠️ Missing checkpoints, /rewind | Visual workflow preference |
| **Code Server (current)** | ❌ 2-4x slower | ⚠️ Limited | Browser-only access |
| **JetBrains Plugin** | ✅ Fast | ✅ Uses CLI underneath | JetBrains ecosystem |

The JetBrains plugin and Neovim integrations (claudecode.nvim) wrap the CLI, so they inherit all CLI features. If you need browser access, consider SSH + tmux/mosh to a VM running Claude Code locally, or use VS Code Remote SSH extension connecting to your VM and running `claude` in the integrated terminal—this gives you full CLI performance while maintaining remote access.

**CLI-exclusive features you're currently missing:**
- **Checkpoints** (`Esc-Esc` or `/rewind`): Save and restore conversation/code state
- **Message editing**: Jump back in history to explore different directions
- **Tab completion** for file paths
- **`#` shortcut** to add memories directly to CLAUDE.md
- **`!` prefix** to run bash commands inline
- Full MCP server configuration UI

---

## Level 2: Master the commands you didn't know existed

Claude Code's feature set expanded dramatically in late 2024-2025. Here's the complete reference for power users:

### Essential slash commands beyond basics

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/context` | Visualize token usage as colored grid | Before complex tasks to budget tokens |
| `/compact [focus]` | Summarize conversation to save tokens | Before pivoting to new feature work |
| `/rewind` | Restore to any checkpoint | After Claude goes wrong direction |
| `/agents` | Create/manage custom subagents | Complex multi-step research tasks |
| `/bashes` | View background shells | Managing long-running processes |
| `/stats` | Usage statistics and cost tracking | End-of-day reviews |
| `/statusline` | Customize terminal prompt | Workflow personalization |
| `/export [filename]` | Export conversation | Documentation, debugging |

### Critical CLI flags for automation

```bash
# Headless mode for scripts and CI/CD
claude -p "query" --output-format json

# Continue previous conversation
claude -c -p "continue this task"

# Resume specific session
claude -r "session-id" -p "finish the PR"

# Custom tool permissions
claude --allowedTools "Bash(npm run:*),Read,Write"

# Maximum thinking budget
claude --append-system-prompt "ultrathink about this architecture"

# Skip permissions (use in containers)
claude --dangerously-skip-permissions
```

### Thinking intensity triggers

These specific phrases map to increasing thinking budgets:

- **"think"** → Base extended thinking
- **"think hard"** → Deeper analysis  
- **"think harder"** → More thorough evaluation
- **"ultrathink"** → Maximum token budget for reasoning

You can also toggle thinking with `Tab` during a session or `Alt+T`. For persistent extended thinking, set `MAX_THINKING_TOKENS` environment variable.

---

## Level 3: CLAUDE.md patterns that experts use

The consensus from power users is counterintuitive: **shorter is better**. The ideal CLAUDE.md is under 60 lines for mature projects, never exceeding 300.

### Expert template structure

```markdown
# Project Context
When working with this codebase, prioritize readability over cleverness.
Ask clarifying questions before making architectural changes.

## About This Project
FastAPI REST API for user authentication. SQLAlchemy + Pydantic.

## Key Directories
- `app/models/` - database models
- `app/api/` - route handlers

## Bash Commands
- `npm run build`: Build the project
- `npm run test:unit`: Run unit tests (prefer single tests over full suite)
- `npm run typecheck`: Run typechecker (always run when done)

## Standards
- Type hints required on all functions
- Use ES modules, not CommonJS
- Destructure imports when possible

## Do Not Touch
- Never modify ./production.config.*
- Never read .env files directly

## For Complex Work
For database migrations, see docs/migrations.md
For deployment procedures, see docs/deploy.md
```

### Progressive disclosure pattern

Instead of cramming everything into root CLAUDE.md, use the hierarchy:

```
~/.claude/CLAUDE.md           # Global defaults (all projects)
./CLAUDE.md                   # Team-shared (git tracked)
./CLAUDE.local.md             # Personal overrides (gitignored)
./backend/CLAUDE.md           # Subdirectory-specific (loaded on demand)
./frontend/CLAUDE.md          # Loaded when working in frontend/
```

Claude loads subdirectory CLAUDE.md files **on demand** when accessing those files—this prevents context pollution.

### Power user shorthand pattern

Define custom triggers in your CLAUDE.md:

```markdown
## Shorthand Commands
When I type "qplan": Analyze codebase patterns, draft approach, wait for confirmation
When I type "qcode": Implement plan, run tests, format with prettier
When I type "qship": Commit with conventional message, push, create PR
```

---

## Level 4: Custom subagents and multi-agent orchestration

Custom subagents (released July 2025) are one of the most powerful and underutilized features. They spawn isolated Claude instances with specific tool permissions and system prompts.

### Creating custom subagents

Store in `.claude/agents/` as markdown files:

```markdown
---
name: security-reviewer
description: Invoke for security audits after implementing auth changes
tools: Read, Grep, Glob, WebSearch
model: sonnet
permissionMode: default
---

You are a senior security engineer. When reviewing code:

1. Check for injection vulnerabilities (SQL, XSS, command)
2. Verify authentication/authorization patterns
3. Look for hardcoded secrets or credentials
4. Assess input validation completeness
5. Review error handling for information leakage

Output format: JSON with severity (critical/high/medium/low) and remediation steps.
```

### Built-in subagents you should know

- **Explore subagent** (Haiku): Fast, read-only codebase search with thoroughness levels
- **Plan subagent** (Sonnet): Research mode before planning—use in Plan Mode
- **General-purpose subagent** (Sonnet): Complex multi-step tasks

### Multi-Claude workflow patterns

**Pattern 1: Git worktrees for parallel work**
```bash
# Create isolated checkouts for parallel Claude instances
git worktree add ../project-feature-a feature-a
git worktree add ../project-feature-b feature-b
git worktree add ../project-refactor refactor

# Open each in separate terminal tabs with Claude
cd ../project-feature-a && claude
```

Anthropic engineers commonly run 3-4 parallel Claude sessions this way, cycling through to check progress.

**Pattern 2: Write-Review separation**
1. Claude #1 writes code
2. `/clear` or new terminal
3. Claude #2 reviews (fresh perspective, no confirmation bias)
4. Implement feedback

**Pattern 3: Parallel batch processing**
```bash
claude -p "in /pathA migrate all foo to bar" &
claude -p "in /pathB update all API endpoints" &
wait
```

---

## Level 5: Hooks system for automated quality enforcement

Hooks are shell commands triggered on Claude Code events—your **deterministic guardrails** that run regardless of what Claude decides.

### Hook configuration

Store in `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "if echo \"$CLAUDE_FILE_PATH\" | grep -q '\\.py$'; then black \"$CLAUDE_FILE_PATH\" && ruff check --fix \"$CLAUDE_FILE_PATH\"; fi"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command", 
            "command": "if echo \"$CLAUDE_TOOL_INPUT\" | jq -r '.command' | grep -qE 'rm -rf|DROP TABLE'; then echo 'BLOCKED: Dangerous command' >&2; exit 2; fi"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Claude finished\" with title \"Claude Code\"'"
          }
        ]
      }
    ]
  }
}
```

### Hook events reference

| Event | Trigger | Use Case |
|-------|---------|----------|
| `PreToolUse` | Before any tool runs | Block dangerous commands, validate inputs |
| `PostToolUse` | After tool completes | Auto-format, run linters, trigger tests |
| `Stop` | Agent finishes | Desktop notifications, logging |
| `SubagentStop` | Subagent completes | Aggregate results |
| `SessionStart` | Session begins | Environment setup |

### Exit codes that control behavior

- **0**: Success (stdout shown to user)
- **2**: Blocking error (stops the action for PreToolUse)
- **Other non-zero**: Non-blocking warning

---

## Level 6: DevOps automation and GitHub integration

### GitHub Actions integration

The `/install-github-app` command sets up @claude mentions in your repository:

```yaml
# .github/workflows/claude.yml
name: Claude Code
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]

jobs:
  claude:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      issues: write
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

Now you can **@claude** in issues and PRs:
- `@claude please review this PR for security issues`
- `@claude implement the feature described in this issue`
- `@claude fix the TypeError in user dashboard`

### Automated PR review workflow

```yaml
name: Claude Code Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Review this PR for:
            1. Code quality and best practices
            2. Potential bugs and edge cases
            3. Security vulnerabilities
            4. Performance implications
            Be concise. Only report actionable findings.
```

### Headless scripting patterns

```bash
#!/bin/bash
# Automated security audit
audit_pr() {
    local pr_number="$1"
    gh pr diff "$pr_number" | claude -p \
      --append-system-prompt "You are a security engineer. Review for vulnerabilities." \
      --output-format json \
      --allowedTools "Read,Grep,WebSearch"
}

# Changelog generation
generate_changelog() {
    local last_tag=$(git describe --tags --abbrev=0)
    local commits=$(git log $last_tag..HEAD --pretty=format:"%s")
    claude -p "Generate Keep a Changelog format from: $commits"
}

# Batch migration
for file in src/**/*.js; do
  claude -p "Convert to TypeScript with strict types: @$file" \
    --allowedTools "Read,Write,Edit" &
done
wait
```

### Custom slash commands for team workflows

Store in `.claude/commands/` (git tracked):

**`.claude/commands/ship.md`:**
```markdown
---
description: "Complete feature: test, commit, push, PR"
allowed-tools: ["Bash(npm:*)", "Bash(git:*)", "Bash(gh:*)"]
---
1. Run `npm run test:unit` - fix any failures
2. Run `npm run typecheck` - fix any errors
3. Run `npm run lint` - fix any issues
4. Stage changes with descriptive commit (conventional format)
5. Push branch
6. Create PR with description summarizing changes

Use emoji prefixes: ✨ feat, 🐛 fix, 📚 docs, 🎨 style, ♻️ refactor
```

Usage: `/project:ship`

---

## Level 7: Expert patterns and mastery techniques

### Context engineering mindset

The shift from "prompt engineering" to "context engineering" defines mastery. You're not just asking questions—you're **curating what Claude sees**.

**The Document-and-Clear pattern:**
1. Have Claude create `plan.md` with detailed approach
2. `/clear` to reset context
3. Continue with `claude -c` or reference plan.md
4. Repeat for each major phase

This gives Claude fresh context while preserving decisions in persistent files.

### Token budget management

```bash
# Check token usage mid-session
/context

# Output shows:
# claude-sonnet-4 • 17k/200k tokens (8%)
# ⛁ System prompt: 3.2k tokens
# ⛁ System tools: 11.6k tokens
# ⛁ Memory files: 743 tokens
# ⛁ Messages: 1.2k tokens
```

**Expert rules:**
- Performance degrades in the last fifth of context—clear before hitting 160k
- Use `/compact` to summarize before pivoting features
- External files (plan.md, decisions.md) persist across `/clear`

### MCP servers for full-stack development

Essential MCP stack:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}" }
    },
    "postgres": {
      "command": "npx", 
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": { "DATABASE_URL": "${DATABASE_URL}" }
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

**Creating custom MCP servers** (Python FastMCP):

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-internal-tools")

@mcp.tool()
async def query_internal_api(endpoint: str, params: dict) -> str:
    """Query internal company API.
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
    """
    # Your implementation
    return result

def main():
    mcp.run(transport="stdio")
```

### Legacy codebase strategies

For complex legacy code, treat Claude like a senior engineer joining the team:

```markdown
## Legacy System Notes (add to CLAUDE.md)
- Public APIs: Do not modify - propose shims instead
- Generated files: Never touch ./vendor, ./generated
- Backward compatibility: Always maintain
- Pain points: Focus on hottest issues, not shiniest code

## Refactoring Protocol
1. Generate characterization tests first
2. Single, targeted refactors only
3. Commit message + rationale for each change
4. Checkpoint after each diff
```

**The micro-refactor loop:**
1. Ask Claude to write tests around current behavior
2. Confirm tests pass
3. Request single targeted refactor
4. Verify tests still pass
5. Checkpoint with `/rewind` capability
6. Repeat

### Hidden features and keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Escape` | Stop current operation (preserves context) |
| `Escape` x2 | Jump back in history, edit previous prompts |
| `Shift+Tab` | Cycle permission modes: Normal → Auto-Accept → Plan Mode |
| `Tab` | Toggle extended thinking |
| `Ctrl+V` | Paste images (not Cmd+V on Mac) |
| `Ctrl+R` | Reverse search command history |
| `Up/Down` | Navigate persistent command history |

**Lesser-known commands:**
- `/doctor` — Enhanced diagnostics
- `/release-notes` — What's new in current version
- `CLAUDE_DEBUG=1 claude` — Verbose debug logging
- `claude --mcp-debug` — Debug MCP connections

### Session history mining

All sessions are stored in `~/.claude/projects/`. Power users run analysis scripts:

```bash
# Find common errors across sessions
grep -r "error" ~/.claude/projects/ | sort | uniq -c | sort -rn

# Extract permission request patterns  
grep -r "permission" ~/.claude/projects/ | head -20
```

---

## Quick reference: The mastery checklist

**Environment:**
- [ ] Migrate from Code Server to local CLI or VS Code Remote SSH
- [ ] Configure hooks for auto-formatting and dangerous command blocking
- [ ] Set up desktop notifications for task completion

**CLAUDE.md:**
- [ ] Keep under 60 lines, max 300
- [ ] Use progressive disclosure with subdirectory files
- [ ] Define shorthand triggers (qplan, qcode, qship)
- [ ] Document only what Claude gets wrong

**Workflow:**
- [ ] Use Plan Mode (Shift+Tab x2) for complex tasks
- [ ] Apply "ultrathink" for architecture decisions
- [ ] `/clear` between unrelated tasks
- [ ] Document-and-Clear pattern for large features

**Automation:**
- [ ] Install GitHub App (`/install-github-app`)
- [ ] Create team slash commands in `.claude/commands/`
- [ ] Configure MCP servers for your stack
- [ ] Set up CI/CD integration with `claude -p`

**Advanced:**
- [ ] Create custom subagents for specialized tasks
- [ ] Use git worktrees for parallel Claude instances
- [ ] Build custom MCP servers for internal tools
- [ ] Mine session history for workflow improvements

The gap between intermediate and master-level Claude Code usage isn't about knowing more commands—it's about **systematic context management**, **deterministic guardrails via hooks**, and **treating Claude as a collaborator that needs clear direction rather than a magic autocomplete**. The experts who get the most from Claude Code are those who invest in their CLAUDE.md, use Plan Mode habitually, and clear context aggressively rather than letting conversations balloon.