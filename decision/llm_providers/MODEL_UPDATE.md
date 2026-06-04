# LLM Model Update Workflow

**Purpose**: Systematic process for updating OpenRouter model selections across the platform.
**Owner**: User tells Claude Code which models to update; this doc defines the exact steps.

---

## Quick Start

Tell Claude Code:
> "Read `decision/llm_providers/MODEL_UPDATE.md` and update [model] [tier] to [new OpenRouter model ID]"

Or for research first:
> "Read `decision/llm_providers/MODEL_UPDATE.md` and research what's available for [provider] on OpenRouter, then recommend updates"

---

## Current Model Roster (21 combinations)

| Model | Economy | Standard | Premium |
|-------|---------|----------|---------|
| **Grok** | `x-ai/grok-4.3` | `x-ai/grok-4.3` | `x-ai/grok-4.20` |
| **DeepSeek** | `deepseek/deepseek-chat` | `deepseek/deepseek-v3.2` | `deepseek/deepseek-r1` |
| **Gemini** | `google/gemini-2.0-flash-001` | `google/gemini-2.5-pro` | `google/gemini-3-pro-preview` |
| **Claude** | `anthropic/claude-haiku-4.5` | `anthropic/claude-sonnet-4.6` | `anthropic/claude-opus-4.6` |
| **GPT** | `openai/gpt-4.1-mini` | `openai/gpt-5` | `openai/gpt-5-pro` |
| **Kimi** | `moonshotai/kimi-k2` | `moonshotai/kimi-k2.5` | `moonshotai/kimi-k2.5` |
| **Qwen** | `qwen/qwen-turbo` | `qwen/qwen-plus` | `qwen/qwen3-max` |

**Last updated**: 2026-06-04 (Grok all tiers — grok-3-mini/grok-4-fast/grok-4.20-beta delisted from OpenRouter)

---

## Research Phase

Before updating any model, gather this info from OpenRouter:

1. **Visit the model page**: `https://openrouter.ai/{provider}/{model-id}`
2. **Record these fields**:
   - OpenRouter model ID (e.g., `moonshotai/kimi-k2.5`)
   - Input price per 1M tokens
   - Output price per 1M tokens
   - Context window (tokens)
   - Reasoning support (does it accept `reasoning.effort` parameter?)
   - Temperature support (does it accept `temperature` parameter?)

3. **Check provider page** for all available models: `https://openrouter.ai/{provider}`

### Tier Assignment Guidelines

- **Economy**: Cheapest/fastest variant. Mini/flash/turbo models. No reasoning effort sent.
- **Standard**: Balanced quality/cost. Current-gen flagship. Reasoning effort = `medium`.
- **Premium**: Best quality available. Reasoning effort = `high`. May be same model as standard (differentiated by reasoning effort only — this is fine, Gemini does this).

---

## Update Checklist

### Step 1: Code — `decision/llm_providers/openrouter_provider.py`

Three dictionaries to update:

**A. `MODEL_TIER_MAP`** — The primary routing table.
```python
# Example: updating kimi standard
('kimi', 'standard'): 'moonshotai/kimi-k2.5',
```

**B. `MODEL_MAP`** — Legacy fallback (maps to standard tier).
```python
'kimi': 'moonshotai/kimi-k2.5',
```

**C. `REASONING_SUPPORTED`** — Add new model ID if it supports `reasoning.effort`.
```python
'moonshotai/kimi-k2.5',
```
Remove old model IDs that are no longer referenced by any tier.

**D. `TEMPERATURE_SUPPORTED`** — Add new model ID if it supports `temperature`.
```python
'moonshotai/kimi-k2.5',
```
Remove old model IDs that are no longer referenced by any tier.

### Step 2: Database — `llm_models` table

Update the model's DB row. The DB stores **standard tier** pricing (used for cost estimates in frontend).

```sql
UPDATE llm_models SET
    openrouter_model_id = 'moonshotai/kimi-k2.5',
    pricing_input_per_1m = 0.60,
    pricing_output_per_1m = 3.00,
    max_context_tokens = 262144,
    context_display = '262K',
    description = 'MoonshotAI models. Economy: Kimi K2 | Standard: Kimi K2.5 | Premium: Kimi K2.5 (high reasoning). [Brief capability note].',
    updated_at = NOW()
WHERE model_id = 'kimi';
```

**Important**: The `description` field format is:
```
[Provider] models. Economy: [Name] | Standard: [Name] | Premium: [Name]. [Brief note].
```
This text is shown to users in the frontend model selector.

### Step 3: Update This File

Update the "Current Model Roster" table above with the new model IDs.
Add an entry to the Update History below.

### Step 4: Restart Server

The model map is loaded at import time. Requires ggbot restart:
```bash
pm2 restart ggbot
```

### Step 5: Verify

After restart, check logs for a bot using the updated model:
```bash
pm2 logs ggbot --lines 50 | grep "Initialized OpenRouter"
```

Expected log: `Initialized OpenRouter provider - model: kimi, tier: standard → moonshotai/kimi-k2.5`

---

## What Does NOT Need Updating

- **Frontend code** — reads model info from `llm_models` DB table dynamically
- **Billing** — uses OpenRouter's actual `usage.cost` from each response, not DB pricing
- **Config schemas** — model IDs are internal; user configs store `model: "kimi"` not the OpenRouter ID
- **Tests** — no model-specific tests exist

---

## Adding a Completely New Model Family

If adding a new provider (e.g., "mistral") rather than updating existing tiers:

1. All steps above, plus:
2. Add 3 entries to `MODEL_TIER_MAP` (economy/standard/premium)
3. Add 1 entry to `MODEL_MAP` (standard tier)
4. Add model IDs to `REASONING_SUPPORTED` / `TEMPERATURE_SUPPORTED` as appropriate
5. `INSERT INTO llm_models` with new `model_id`, pricing, context, sort_order
6. Frontend model selector will pick it up automatically from DB

---

## Update History

| Date | Model | Tiers Changed | Old → New | Reason |
|------|-------|---------------|-----------|--------|
| 2026-06-04 | Grok | All | `grok-3-mini`, `grok-4-fast`, `grok-4.20-beta` → `grok-4.3` (eco+std), `grok-4.20` (premium) | All three delisted; grok-4-fast 404s ("deprecated, switch to 4.3"). 4.3: $1.25/$2.50, 1M ctx. 4.20 stable: $1.25/$2.50, 2M ctx. Economy=4.3 without reasoning effort. |
| 2026-03-26 | Claude | Standard, Premium | `claude-sonnet-4.5`, `claude-opus-4.5` → `claude-sonnet-4.6`, `claude-opus-4.6` | Gen upgrade. Opus 4.6 gets 1M context (was 200K). Same pricing. |
| 2026-03-26 | Grok | Premium | `grok-4` → `grok-4.20-beta` | New flagship. $2/$6 (was $3/$15). 2M context (was 256K). |
| 2026-01-27 | Kimi | Standard, Premium | `kimi-k2-0905`, `kimi-k2-thinking` → `kimi-k2.5` | K2.5 launch: multimodal SOTA, reasoning support, gen upgrade |
