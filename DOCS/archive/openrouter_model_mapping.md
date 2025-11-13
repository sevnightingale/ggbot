# OpenRouter Model Mapping & Pricing

**Created**: 2025-11-10
**Phase**: 0.1 - Research & Validation
**Status**: ✅ Verified - All models available and working

---

## Model Name Mapping

**Format**: `internal_name` → `openrouter_model_id`

```python
MODEL_MAP = {
    # OpenAI Models
    'gpt-5': 'openai/gpt-5',
    'gpt-5-mini': 'openai/gpt-5-mini',
    'gpt-4o': 'openai/gpt-4o',
    'gpt-4': 'openai/gpt-4',

    # Anthropic Models
    'claude-opus-4': 'anthropic/claude-opus-4.1',
    'claude-opus-4-1-20250805': 'anthropic/claude-opus-4.1',  # Legacy name
    'claude-sonnet-4.5': 'anthropic/claude-sonnet-4.5',
    'claude-haiku-4.5': 'anthropic/claude-haiku-4.5',

    # DeepSeek Models
    'deepseek-reasoner': 'deepseek/deepseek-r1',
    'deepseek-chat': 'deepseek/deepseek-chat-v3.1',
    'deepseek-r1': 'deepseek/deepseek-r1',

    # xAI Models
    'grok-4': 'x-ai/grok-4',
    'grok-4-fast': 'x-ai/grok-4-fast',
    'grok-4-fast-reasoning': 'x-ai/grok-4',
    'grok-4-fast-non-reasoning': 'x-ai/grok-4-fast',

    # Default fallback
    'default': 'x-ai/grok-4-fast'
}
```

---

## Pricing (OpenRouter Base Costs)

| Model | OpenRouter ID | Input (per 1K) | Output (per 1K) | Context |
|-------|---------------|----------------|-----------------|---------|
| **GPT-5** | `openai/gpt-5` | $0.0013 | $0.0100 | 400K |
| **GPT-5 Mini** | `openai/gpt-5-mini` | $0.0003 | $0.0020 | 400K |
| **GPT-4o** | `openai/gpt-4o` | $0.0025 | $0.0100 | 128K |
| **Claude Opus 4.1** | `anthropic/claude-opus-4.1` | $0.0150 | $0.0750 | 200K |
| **Claude Sonnet 4.5** | `anthropic/claude-sonnet-4.5` | $0.0030 | $0.0150 | 1M |
| **Claude Haiku 4.5** | `anthropic/claude-haiku-4.5` | $0.0010 | $0.0050 | 200K |
| **DeepSeek R1** | `deepseek/deepseek-r1` | $0.0003 | $0.0012 | 163K |
| **DeepSeek Chat V3.1** | `deepseek/deepseek-chat-v3.1` | $0.0002 | $0.0008 | 163K |
| **Grok 4** | `x-ai/grok-4` | $0.0030 | $0.0150 | 256K |
| **Grok 4 Fast** | `x-ai/grok-4-fast` | $0.0002 | $0.0005 | 2M |

---

## Pricing with 70% Markup (What We Charge Users)

**Formula**: `user_price = openrouter_cost * 1.70`

| Model | Input (per 1K) | Output (per 1K) | Example Cost* |
|-------|----------------|-----------------|---------------|
| **GPT-5** | $0.00221 | $0.01700 | $0.09105 |
| **GPT-5 Mini** | $0.00051 | $0.00340 | $0.01955 |
| **GPT-4o** | $0.00425 | $0.01700 | $0.08075 |
| **Claude Opus 4.1** | $0.02550 | $0.12750 | $0.64600 |
| **Claude Sonnet 4.5** | $0.00510 | $0.02550 | $0.12920 |
| **Claude Haiku 4.5** | $0.00170 | $0.00850 | $0.04250 |
| **DeepSeek R1** | $0.00051 | $0.00204 | $0.01173 |
| **DeepSeek Chat V3.1** | $0.00034 | $0.00136 | $0.00782 |
| **Grok 4** | $0.00510 | $0.02550 | $0.12920 |
| **Grok 4 Fast** | $0.00034 | $0.00085 | $0.00561 |

**Example Cost**: Based on 5K input + 2K output tokens (typical decision execution)

---

## Token Tracking Format (Standardized!)

**All models return identical structure:**

```json
{
  "usage": {
    "prompt_tokens": 27,
    "completion_tokens": 8,
    "total_tokens": 35
  }
}
```

**Reasoning Models (GPT-5, DeepSeek R1) include:**

```json
{
  "usage": {
    "prompt_tokens": 22,
    "completion_tokens": 97,
    "total_tokens": 119,
    "completion_tokens_details": {
      "reasoning_tokens": 91
    }
  }
}
```

**Note**: `reasoning_tokens` are INCLUDED in `completion_tokens` (not separate).

---

## Verification Status

✅ **API Access**: Working (tested with `$OPENROUTER_API_KEY`)
✅ **Model Availability**: All models verified available
✅ **Token Tracking**: Standardized format confirmed
✅ **Completions**: Tested successfully with GPT-5, Claude Sonnet 4.5, DeepSeek R1
✅ **Pricing**: Retrieved from OpenRouter model list API

---

## Next Steps

**Phase 0.2**: Create `OpenRouterProvider` class
- Implement `LLMProvider` interface
- Use model mapping above
- Handle reasoning tokens properly
- Return standardized metadata format

**Phase 0.3**: Integration
- Update `factory.py` to add 'openrouter' option
- Update `llm_key_service.py` to include 'openrouter' mapping
- Update `__init__.py` to export OpenRouterProvider

**Phase 0.4**: Testing
- Create test script with real bot config
- Validate responses identical to current providers
- Monitor for errors

**Phase 0.5**: Migration
- Update 1-2 bot configs to use `provider: 'openrouter'`
- Run for 24 hours
- If successful, migrate all configs
