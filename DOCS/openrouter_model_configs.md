# OpenRouter Model Configurations

**Created**: 2025-11-10
**Purpose**: Define parameter settings for 14 model variants (7 models × 2 thinking modes)

---

## Model Configuration Strategy

### Thinking Mode Differences

| Setting | Standard Mode | Thinking Mode |
|---------|--------------|---------------|
| `max_tokens` | 2048 | 8192 |
| `reasoning.effort` | N/A | `high` |
| `temperature` | 0.7 | 0.7 |
| Use Case | Fast decisions | Complex analysis |
| Cost Multiplier | 1x | ~2-3x |

---

## Model Configurations

### 1. Grok (x-ai/grok-4-fast)

**Standard Mode:**
```json
{
  "model": "x-ai/grok-4-fast",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**Thinking Mode:**
```json
{
  "model": "x-ai/grok-4-fast",
  "temperature": 0.7,
  "max_tokens": 8192,
  "reasoning": {"effort": "high"}
}
```

**Supported Parameters:**
- ✅ temperature, max_tokens, top_p, reasoning, include_reasoning
- ✅ response_format, seed, structured_outputs
- ✅ logprobs, top_logprobs, tools, tool_choice

**Pricing**: $0.20/M input, $0.50/M output

---

### 2. Claude (anthropic/claude-sonnet-4.5)

**Standard Mode:**
```json
{
  "model": "anthropic/claude-sonnet-4.5",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**Thinking Mode:**
```json
{
  "model": "anthropic/claude-sonnet-4.5",
  "temperature": 0.7,
  "max_tokens": 8192,
  "reasoning": {"effort": "high"}
}
```

**Supported Parameters:**
- ✅ temperature, max_tokens, top_p, top_k, reasoning, include_reasoning
- ✅ stop, tools, tool_choice

**Pricing**: $3.00/M input, $15.00/M output

---

### 3. Gemini (google/gemini-2.5-pro)

**Standard Mode:**
```json
{
  "model": "google/gemini-2.5-pro",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**Thinking Mode:**
```json
{
  "model": "google/gemini-2.5-pro",
  "temperature": 0.7,
  "max_tokens": 8192,
  "reasoning": {"effort": "high"}
}
```

**Supported Parameters:**
- ✅ temperature, max_tokens, top_p, reasoning, include_reasoning
- ✅ response_format, seed, stop, structured_outputs
- ✅ tools, tool_choice

**Pricing**: $1.25/M input, $10.00/M output

---

### 4. DeepSeek (deepseek/deepseek-chat-v3.1)

**Standard Mode:**
```json
{
  "model": "deepseek/deepseek-chat-v3.1",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**Thinking Mode:**
```json
{
  "model": "deepseek/deepseek-chat-v3.1",
  "temperature": 0.7,
  "max_tokens": 8192,
  "reasoning": {"effort": "high"}
}
```

**Supported Parameters:**
- ✅ temperature, max_tokens, top_p, top_k, min_p, reasoning, include_reasoning
- ✅ frequency_penalty, presence_penalty, repetition_penalty
- ✅ response_format, seed, stop, structured_outputs
- ✅ logit_bias, logprobs, top_logprobs, tools, tool_choice

**Pricing**: $0.20/M input, $0.80/M output

---

### 5. GPT (openai/gpt-5)

**Standard Mode:**
```json
{
  "model": "openai/gpt-5",
  "max_tokens": 2048
}
```

**Thinking Mode:**
```json
{
  "model": "openai/gpt-5",
  "max_tokens": 8192,
  "reasoning": {"effort": "high"}
}
```

**Note**: GPT-5 does NOT support `temperature` or `top_p` parameters!

**Supported Parameters:**
- ✅ max_tokens, reasoning, include_reasoning
- ✅ response_format, seed, structured_outputs
- ✅ tools, tool_choice

**Pricing**: $1.25/M input, $10.00/M output

---

### 6. Kimi (moonshotai/kimi-k2-thinking)

**Standard Mode:**
```json
{
  "model": "moonshotai/kimi-k2-thinking",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**Thinking Mode:**
```json
{
  "model": "moonshotai/kimi-k2-thinking",
  "temperature": 0.7,
  "max_tokens": 8192,
  "reasoning": {"effort": "high"}
}
```

**Supported Parameters:**
- ✅ temperature, max_tokens, top_p, top_k, min_p, reasoning, include_reasoning
- ✅ frequency_penalty, presence_penalty, repetition_penalty
- ✅ response_format, seed, stop, structured_outputs
- ✅ logit_bias, logprobs, top_logprobs, tools, tool_choice

**Pricing**: $0.60/M input, $2.50/M output

---

### 7. Qwen (qwen/qwen3-max)

**Standard Mode:**
```json
{
  "model": "qwen/qwen3-max",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**Thinking Mode:**
```json
{
  "model": "qwen/qwen3-max",
  "temperature": 0.7,
  "max_tokens": 4096
}
```

**Note**: Qwen does NOT support `reasoning` parameters! Thinking mode just uses higher max_tokens.

**Supported Parameters:**
- ✅ temperature, max_tokens, top_p, presence_penalty
- ✅ response_format, seed, tools, tool_choice

**Pricing**: $1.20/M input, $6.00/M output

---

## Implementation Notes

### Temperature Setting
- **Standard**: 0.7 for all models (except GPT-5 which doesn't support it)
- **Rationale**: Balanced between creativity and consistency for trading decisions

### Max Tokens
- **Standard Mode**: 2048 tokens
  - Sufficient for typical trading decisions
  - Keeps costs reasonable
- **Thinking Mode**: 8192 tokens (4096 for Qwen)
  - Allows extended reasoning chains
  - Higher quality analysis
  - Cost increases proportionally

### Reasoning Configuration
- **Effort Level**: `high` for all thinking modes
- **Models Supporting Reasoning**: Grok, Claude, Gemini, DeepSeek, GPT, Kimi
- **Qwen Alternative**: Uses higher max_tokens only (no reasoning param)

### Special Cases
1. **GPT-5**: No temperature/top_p support
2. **Qwen**: No reasoning parameter support
3. **DeepSeek/Kimi**: Most comprehensive parameter support (19 params each)

---

## Cost Implications

### Thinking Mode Cost Multipliers (Estimated)

| Model | Standard | Thinking | Multiplier |
|-------|----------|----------|------------|
| Grok | $0.002 | $0.006 | 3x |
| DeepSeek | $0.003 | $0.008 | 2.7x |
| Kimi | $0.008 | $0.022 | 2.75x |
| Qwen | $0.018 | $0.036 | 2x |
| Gemini | $0.026 | $0.078 | 3x |
| GPT | $0.026 | $0.078 | 3x |
| Claude | $0.045 | $0.135 | 3x |

**Note**: Multipliers are estimates based on increased token usage. Actual costs depend on prompt complexity.

---

## Recommended Default

**For new users:**
- Model: `grok` (cheapest, 2M context)
- Thinking: `false` (standard mode)
- Cost: ~$0.002 per decision

**For premium performance:**
- Model: `claude` or `gpt` (highest quality)
- Thinking: `true` (thinking mode enabled)
- Cost: ~$0.08-$0.14 per decision
