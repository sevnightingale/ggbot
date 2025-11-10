# OpenRouter Integration Guide

**Created**: 2025-11-10
**Source**: Context7 OpenRouter Documentation
**Purpose**: Guide for migrating from direct LLM APIs to OpenRouter

---

## What is OpenRouter?

**OpenRouter is a unified API gateway for 200+ LLM models across multiple providers.**

- Single API endpoint for all models
- OpenAI-compatible API format
- Standardized token tracking and cost reporting
- Automatic fallback routing
- Transparent pricing

---

## Key Integration Details

### 1. Authentication

**Bearer Token** via Authorization header:

```python
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}
```

**Environment Variable**:
```bash
OPENROUTER_API_KEY=sk_or_v1_xxxxx
```

### 2. Base URL

**Standard Endpoint**:
```
https://openrouter.ai/api/v1
```

**Chat Completions**:
```
POST https://openrouter.ai/api/v1/chat/completions
```

### 3. Model Name Format

**Format**: `provider/model-name`

**Examples**:
- `openai/gpt-4`
- `openai/gpt-5` (if available)
- `anthropic/claude-opus-4`
- `anthropic/claude-sonnet-4.5`
- `deepseek/deepseek-chat`
- `x-ai/grok-beta`

**Note**: Need to verify exact model names via OpenRouter's model list API.

### 4. Request Format (OpenAI-Compatible)

```python
import requests

url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "openai/gpt-4",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.7,
    "max_tokens": 2000
}

response = requests.post(url, headers=headers, json=payload)
result = response.json()
```

### 5. Response Format (OpenAI-Compatible)

```json
{
  "id": "chatcmpl-xxxxx",
  "object": "chat.completion",
  "created": 1700000000,
  "model": "openai/gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 10,
    "total_tokens": 20
  }
}
```

### 6. Token Tracking ✅ (Standardized!)

**Basic Usage** (included by default):
```json
{
  "usage": {
    "prompt_tokens": 194,
    "completion_tokens": 2,
    "total_tokens": 196
  }
}
```

**Enhanced Usage** (with cost tracking):
```python
payload = {
    "model": "openai/gpt-4",
    "messages": [...],
    "usage": {
        "include": True  # Request enhanced usage info
    }
}
```

**Enhanced Response**:
```json
{
  "usage": {
    "prompt_tokens": 194,
    "completion_tokens": 2,
    "total_tokens": 196,
    "cost": 0.95,  // Total cost in USD!
    "cost_details": {
      "upstream_inference_cost": 19
    },
    "prompt_tokens_details": {
      "cached_tokens": 0,
      "audio_tokens": 0
    },
    "completion_tokens_details": {
      "reasoning_tokens": 0
    }
  }
}
```

**🎉 This is huge**: OpenRouter can return the cost directly! We might not even need our pricing table.

### 7. Pricing Information

**Model List API**:
```python
url = "https://openrouter.ai/api/v1/models"
headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}

response = requests.get(url, headers=headers)
models = response.json()
```

**Model Object Format**:
```json
{
  "id": "anthropic/claude-sonnet-4",
  "name": "Anthropic: Claude Sonnet 4",
  "pricing": {
    "prompt": "0.000008",      // USD per token (string to avoid float issues)
    "completion": "0.000024",  // USD per token
    "image": "0",
    "request": "0"
  },
  "context_length": 1000000,
  "max_output_length": 128000
}
```

**Important**: Pricing is returned as **strings** (not floats) to avoid precision issues.

### 8. OpenAI SDK Integration

**Can use official OpenAI SDK** with custom base_url:

```python
import openai

openai.api_base = "https://openrouter.ai/api/v1"
openai.api_key = OPENROUTER_API_KEY

response = openai.ChatCompletion.create(
    model="openai/gpt-4",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

reply = response.choices[0].message
```

Or modern async OpenAI client:

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

response = await client.chat.completions.create(
    model="openai/gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### 9. Reasoning Tokens (for GPT-5, Claude, etc.)

**Request reasoning effort**:
```python
payload = {
    "model": "openai/gpt-5",
    "messages": [...],
    "reasoning": {
        "effort": "high",        # high, medium, low
        "max_tokens": 2000       # Limit reasoning tokens
    }
}
```

**Response includes reasoning**:
```json
{
  "choices": [{
    "message": {
      "reasoning": "...",  // Reasoning chain
      "content": "..."     // Final answer
    }
  }],
  "usage": {
    "completion_tokens_details": {
      "reasoning_tokens": 1500
    }
  }
}
```

### 10. Special Features

**Web Search** (model variants):
```python
{
    "model": "openai/o4-mini:online",  // :online suffix for web search
    "input": "What was a positive news story from today?"
}
```

**User Tracking** (for caching and analytics):
```python
{
    "model": "openai/gpt-4",
    "messages": [...],
    "user": "user_12345"  // User identifier for caching
}
```

---

## Migration Strategy for ggbots

### Current Architecture
```python
# decision/llm_providers/openai_provider.py
class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-5"):
        self.base_url = 'https://api.openai.com/v1'
        self.model = model
        # ... provider-specific logic

    async def generate_response(...) -> Tuple[str, Dict]:
        # Custom OpenAI Responses API format
        # Returns: (response_text, metadata)
```

### OpenRouter Architecture
```python
# decision/llm_providers/openrouter_provider.py
class OpenRouterProvider(LLMProvider):
    MODEL_MAP = {
        'gpt-4': 'openai/gpt-4',
        'gpt-5': 'openai/gpt-5',
        'claude-opus-4': 'anthropic/claude-opus-4',
        'deepseek-chat': 'deepseek/deepseek-chat',
        'grok-4': 'x-ai/grok-beta'
    }

    def __init__(self, api_key: str, model: str = "gpt-5"):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.model = self.MODEL_MAP.get(model, model)

    async def generate_response(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        custom_mode: Optional[str] = None
    ) -> Tuple[str, Dict]:
        # Prepare messages
        messages = []
        if custom_mode:
            system_prompt = self._get_system_prompt(custom_mode)
            messages.append({"role": "system", "content": system_prompt})

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": prompt})

        # Call OpenRouter
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=2000
        )

        # Extract response
        content = response.choices[0].message.content

        # Build metadata (standardized format!)
        metadata = {
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "finish_reason": response.choices[0].finish_reason
        }

        return content, metadata
```

### Benefits

1. **Standardized Token Tracking**:
   - All models return identical format: `{"prompt_tokens": X, "completion_tokens": Y, "total_tokens": Z}`
   - No provider-specific parsing logic needed
   - Cost data included in response!

2. **Simplified Codebase**:
   - One provider file instead of 4
   - One API integration
   - One response format

3. **Easier Token Tracking for Billing**:
   ```python
   # After OpenRouter migration
   response_text, metadata = await llm_provider.generate_response(...)

   # Standardized usage format across ALL models
   await token_tracking_service.record_usage(
       user_id=user_id,
       config_id=config_id,
       provider="openrouter",
       model=metadata['model'],  # e.g., "openai/gpt-4"
       input_tokens=metadata['usage']['prompt_tokens'],
       output_tokens=metadata['usage']['completion_tokens'],
       execution_type="decision"
   )
   ```

4. **Cost Validation**:
   - Can request `"usage": {"include": True}` to get cost from OpenRouter
   - Verify our 70% markup calculations: `our_cost = openrouter_cost * 1.70`
   - No need to maintain pricing table (can use OpenRouter's model list API)

---

## Implementation Checklist

### Phase 0.1: Research & Validation

- [ ] **Sign up for OpenRouter account**
- [ ] **Get API key** (format: `sk_or_v1_xxxxx`)
- [ ] **Verify model availability**:
  ```python
  import requests

  url = "https://openrouter.ai/api/v1/models"
  headers = {"Authorization": f"Bearer {api_key}"}

  response = requests.get(url, headers=headers)
  models = response.json()['data']

  # Check if our models are available
  model_ids = [m['id'] for m in models]
  print("GPT-4:", 'openai/gpt-4' in model_ids)
  print("GPT-5:", 'openai/gpt-5' in model_ids)
  print("Claude Opus 4:", 'anthropic/claude-opus-4' in model_ids)
  print("DeepSeek:", 'deepseek/deepseek-chat' in model_ids)
  print("Grok:", any('grok' in m for m in model_ids))
  ```

- [ ] **Test token tracking**:
  ```python
  # Test call with usage tracking
  response = requests.post(
      "https://openrouter.ai/api/v1/chat/completions",
      headers=headers,
      json={
          "model": "openai/gpt-4",
          "messages": [{"role": "user", "content": "Hello"}],
          "usage": {"include": True}
      }
  )

  # Verify usage format
  usage = response.json()['usage']
  print(f"Tokens: {usage['total_tokens']}")
  print(f"Cost: ${usage.get('cost', 'N/A')}")  # If available
  ```

- [ ] **Check pricing**:
  ```python
  # Get pricing for our models
  for model in models:
      if model['id'] in ['openai/gpt-4', 'anthropic/claude-opus-4', 'deepseek/deepseek-chat']:
          print(f"{model['id']}:")
          print(f"  Input: ${model['pricing']['prompt']} per token")
          print(f"  Output: ${model['pricing']['completion']} per token")
  ```

### Phase 0.2: Implementation

- [ ] Create `decision/llm_providers/openrouter_provider.py`
- [ ] Update `decision/llm_providers/factory.py` to add 'openrouter' option
- [ ] Update `decision/llm_providers/__init__.py` to export OpenRouterProvider
- [ ] Add `OPENROUTER_API_KEY` to `.env`
- [ ] Update `core/services/llm_key_service.py` to include 'openrouter' mapping

### Phase 0.3: Testing

- [ ] Create test script (`scripts/test_openrouter.py`)
- [ ] Test all models (6-7 models)
- [ ] Verify responses identical to direct API calls
- [ ] Test with real bot config (1 execution)
- [ ] Monitor logs for errors

### Phase 0.4: Migration

- [ ] Update 1-2 bot configs to use `provider: 'openrouter'`
- [ ] Run for 24 hours, monitor performance
- [ ] If successful: update all configs
- [ ] Mark old providers as deprecated (keep as fallback)

---

## Model Name Mapping (To Verify)

Need to check exact OpenRouter model names:

| Our Internal Name | Expected OpenRouter Name | Verified? |
|-------------------|-------------------------|-----------|
| `gpt-4` | `openai/gpt-4` | ❓ |
| `gpt-5` | `openai/gpt-5` | ❓ |
| `claude-opus-4-1-20250805` | `anthropic/claude-opus-4` | ❓ |
| `claude-sonnet-4.5` | `anthropic/claude-sonnet-4.5` | ❓ |
| `claude-haiku-4.5` | `anthropic/claude-haiku-4.5` | ❓ |
| `deepseek-reasoner` | `deepseek/deepseek-chat` | ❓ |
| `grok-4-fast-reasoning` | `x-ai/grok-beta` | ❓ |

**Action**: Query OpenRouter's model list API to get exact names.

---

## Potential Issues & Solutions

### Issue 1: OpenAI's Custom Responses API

**Problem**: We currently use OpenAI's Responses API (`/responses`) which has special features like CoT passing.

**Solution**:
- OpenRouter uses standard `/chat/completions` endpoint
- CoT passing via `previous_response_id` may not be available
- **Alternative**: Include reasoning in conversation_history manually

### Issue 2: System Prompt Handling

**Problem**: Different providers handle system prompts differently.

**Solution**:
- OpenRouter uses standard format: `{"role": "system", "content": "..."}`
- Works uniformly across all models
- ✅ This is actually better than current setup

### Issue 3: Reasoning Tokens

**Problem**: GPT-5 has special reasoning token reporting.

**Solution**:
- OpenRouter supports `reasoning` parameter
- Returns `completion_tokens_details.reasoning_tokens`
- ✅ Should work, need to test

---

## Next Steps

1. ✅ **Get OpenRouter documentation** (done)
2. **User**: Sign up for OpenRouter account
3. **User**: Share API key
4. **Claude**: Create `OpenRouterProvider` class
5. **Claude**: Test with all models
6. **Claude**: Migrate one bot config
7. **Claude**: Proceed to Phase 1 (token tracking)
