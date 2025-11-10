# Current LLM Integration Architecture

**Created**: 2025-11-10
**Purpose**: Document existing LLM provider system before OpenRouter migration

---

## Overview

The platform uses a **factory pattern** with **4 separate LLM provider implementations** that all conform to the `LLMProvider` abstract base class.

---

## Architecture Components

### 1. Base Interface (`decision/llm_providers/base.py`)

**Abstract Class**: `LLMProvider`

```python
class LLMProvider(ABC):
    def __init__(self, api_key: str, model: str = None, **kwargs):
        self.api_key = api_key
        self.model = model
        self.kwargs = kwargs

    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        custom_mode: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Returns:
            Tuple[str, Dict[str, Any]]: (response_text, metadata)
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass
```

### 2. Provider Implementations

#### **OpenAIProvider** (`decision/llm_providers/openai_provider.py`)
- **Endpoint**: `/responses` (GPT-5 Responses API)
- **Default Model**: `gpt-5`
- **Timeout**: 300s (extended for reasoning)
- **Retries**: 3 attempts with exponential backoff
- **Special Features**:
  - Chain-of-Thought (CoT) passing via `previous_response_id`
  - Reasoning effort: "high"
  - Returns reasoning_summary and reasoning_tokens
- **Response Format**:
  ```python
  {
      "model": "gpt-5",
      "usage": {
          "output_tokens_details": {
              "reasoning_tokens": 1500
          },
          "total_tokens": 3000
      },
      "latency": 12.5,
      "reasoning_effort": "high",
      "verbosity": "medium",
      "response_id": "resp_xxx",  # For CoT passing
      "reasoning_summary": [...],
      "finish_reason": "completed"
  }
  ```

#### **AnthropicProvider** (`decision/llm_providers/anthropic_provider.py`)
- **Endpoint**: `/messages`
- **Default Model**: `claude-opus-4-1-20250805`
- **Timeout**: 200s
- **Retries**: 3 attempts
- **Headers**: Requires `anthropic-version: 2023-06-01`
- **Special Features**:
  - System prompt passed separately (not in messages array)
  - Max tokens: 16384
  - Custom DecimalEncoder for JSON serialization
- **Response Format**:
  ```python
  {
      "model": "claude-opus-4-1-20250805",
      "usage": {
          "input_tokens": 1200,
          "output_tokens": 450
      },
      "latency": 8.2,
      "temperature": 0.7,
      "finish_reason": "end_turn"
  }
  ```

#### **DeepSeekProvider** (`decision/llm_providers/deepseek_provider.py`)
- **Endpoint**: `/chat/completions` (OpenAI-compatible)
- **Default Model**: `deepseek-reasoner`
- **Timeout**: 200s
- **Retries**: 3 attempts
- **Response Format**:
  ```python
  {
      "model": "deepseek-reasoner",
      "usage": {
          "prompt_tokens": 800,
          "completion_tokens": 300,
          "total_tokens": 1100
      },
      "latency": 6.5,
      "temperature": 0.7,
      "finish_reason": "stop"
  }
  ```

#### **XAIProvider** (`decision/llm_providers/xai_provider.py`)
- **Endpoint**: `/chat/completions` (OpenAI-compatible)
- **Default Model**: `grok-4-fast-non-reasoning` (basic) or `grok-4-fast-reasoning` (frontier)
- **Default provider**: Maps to 'xai' when user selects 'default'

### 3. Factory (`decision/llm_providers/factory.py`)

**Function**: `get_llm_provider(provider_name, api_key, model, **kwargs)`

**Mappings**:
```python
'default' → XAIProvider (grok-4-fast-non-reasoning)
'deepseek' → DeepSeekProvider (deepseek-reasoner)
'openai' | 'gpt' | 'gpt4' | 'gpt5' → OpenAIProvider (gpt-5)
'anthropic' | 'claude' → AnthropicProvider (claude-opus-4-1-20250805)
'xai' | 'grok' → XAIProvider (grok-4-fast-reasoning or grok-4-fast-non-reasoning)
```

**Available Providers**: `['default', 'deepseek', 'openai', 'anthropic', 'xai']`

### 4. API Key Management (`core/services/llm_key_service.py`)

**Service**: `LLMKeyService`

**Priority System**:
1. **User's Personal API Key** (encrypted in Supabase Vault via `user_llm_credentials` table)
2. **Platform API Key** (from environment variables)
3. **Error** if neither available

**Environment Variables**:
```bash
OPENAI_API_KEY=sk_...
DEEPSEEK_API_KEY=sk_...
ANTHROPIC_API_KEY=sk_...
XAI_API_KEY=xai_...
```

**User Key Storage**:
- Encrypted using Supabase Vault: `vault.create_secret(api_key)`
- Retrieved using: `vault.decrypt_secret(vault_secret_id)`
- Table: `user_llm_credentials` (user_id, provider, credential_name, vault_secret_id)

---

## Usage Patterns

### Decision Engine (`decision/engine_v2.py`)

**Initialization**:
```python
class DecisionEngineV2:
    async def _initialize_llm_provider(self) -> None:
        # Get config
        llm_config = self.config.llm_config  # e.g., {'provider': 'openai', 'model': 'gpt-5'}
        provider_name = llm_config.get('provider', 'default')
        model_name = llm_config.get('model', None)

        # Get API key (user's or platform's)
        api_key = await LLMKeyService.get_api_key(self.user_id, provider_name)

        # Create provider instance
        self.llm_provider = get_llm_provider(
            provider_name=provider_name,
            api_key=api_key,
            model=model_name
        )
```

**Usage**:
```python
# Generate decision
response_text, metadata = await self.llm_provider.generate_response(
    prompt=prompt,
    temperature=0.7,
    custom_mode="ggshot"  # or "trade_management" or None
)

# metadata contains:
# - model: str
# - usage: dict (provider-specific format)
# - latency: float
# - finish_reason: str
# - provider-specific fields (reasoning_tokens, response_id, etc.)

# Currently: metadata is logged but NOT stored for token tracking
logger.info(f"Generated response, tokens={metadata.get('usage', {}).get('total_tokens', 'unknown')}")
```

### Agents (`agent/run_agent.py`)

**Agents use Claude SDK directly** (NOT our LLM providers):
```python
from claude_agent_sdk import ClaudeSDKClient

# Agent initialization uses Claude SDK
client = ClaudeSDKClient(
    api_key=os.getenv("ANTHROPIC_API_KEY_AGENTS"),  # Separate agent key
    model="claude-sonnet-4.5",
    ...
)
```

**Note**: Agent LLM calls do NOT go through our provider abstraction, so they won't be affected by OpenRouter migration unless we also migrate the Claude SDK configuration.

---

## Custom Modes (System Prompts)

All providers support 3 custom modes via `custom_mode` parameter:

### 1. `custom_mode="ggshot"`
```
"You are a quantitative trading analyst executing the Four-Pillar Validation Framework.
PHASE 1 (Pillar-scoring judgment): Choose values strictly within each pillar's numeric range.
PHASE 2 (Math): Sum the scores. If total <0.05 set to 0.05; if >0.95 set to 0.95.
NO further edits, rescaling, or overrides after Phase 2..."
```

### 2. `custom_mode="trade_management"`
```
"You are an expert cryptocurrency trader managing active positions. Your role is to
analyze current market conditions and make decisions about existing trades: hold,
adjust, or close positions..."
```

### 3. `custom_mode=None` (default)
```
"You are an expert cryptocurrency trader analyzing market data and making trading decisions.
Provide clear, reasoned responses about trading actions."
```

---

## Token Usage (Current State)

### ❌ **No Token Tracking Currently**

**What happens now**:
1. LLM provider returns metadata with usage info
2. Decision engine logs it: `logger.info(f"tokens={metadata['usage']['total_tokens']}")`
3. **Nothing is stored in database**
4. **No billing/metering exists**

**Usage Format Differences**:
- **OpenAI**: `usage.total_tokens`, `usage.output_tokens_details.reasoning_tokens`
- **Anthropic**: `usage.input_tokens`, `usage.output_tokens`
- **DeepSeek**: `usage.prompt_tokens`, `usage.completion_tokens`, `usage.total_tokens`
- **XAI**: Similar to DeepSeek (OpenAI-compatible)

---

## Integration Points for OpenRouter Migration

### Where LLM Providers Are Used

1. **Decision Engine** (`decision/engine_v2.py`)
   - Line 18: `from decision.llm_providers import get_llm_provider`
   - Line 139: `self.llm_provider = get_llm_provider(...)`
   - Line 1123: `response_text, metadata = await self.llm_provider.generate_response(...)`

2. **Signal Validation** (uses same decision engine)
   - No separate LLM integration

3. **Agents** (`agent/run_agent.py`)
   - ⚠️ **Uses Claude SDK directly, NOT our providers**
   - Would need separate migration strategy

### Files to Update for OpenRouter

**Core Provider Files**:
- `decision/llm_providers/factory.py` - Add OpenRouter option
- `decision/llm_providers/__init__.py` - Export OpenRouter provider
- Create: `decision/llm_providers/openrouter_provider.py`

**Key Management**:
- `core/services/llm_key_service.py` - Add 'openrouter' to env_var_map
- Add env var: `OPENROUTER_API_KEY=sk_...`

**Config**:
- `.env` - Add OpenRouter API key
- Bot configs allow 'openrouter' as provider

---

## Challenges for OpenRouter Migration

### 1. **Different Response Formats**
- OpenAI uses custom Responses API format (not standard chat completions)
- Would need to map OpenRouter's standard format to OpenAI's expected structure
- Or update decision engine to accept standard format

### 2. **Model Name Mapping**
Internal names → OpenRouter names:
```
'gpt-5' → 'openai/gpt-5'
'gpt-4' → 'openai/gpt-4'
'claude-opus-4-1-20250805' → 'anthropic/claude-opus-4-20250514' (?)
'deepseek-reasoner' → 'deepseek/deepseek-chat'
'grok-4-fast-reasoning' → 'x-ai/grok-beta' (?)
```

Need to verify exact OpenRouter model names.

### 3. **CoT Passing (OpenAI)**
OpenAI's `previous_response_id` for Chain-of-Thought:
- Does OpenRouter support this?
- May need to pass reasoning in conversation_history instead

### 4. **System Prompts**
- OpenAI: Prepended to input (Responses API)
- Anthropic: Separate `system` parameter
- DeepSeek/XAI: First message with `role: system`
- OpenRouter: How does it handle system prompts?

### 5. **Agent System**
Agents use Claude SDK directly (not our providers):
- Should we migrate agents to OpenRouter too?
- Or keep agents on Claude SDK and only migrate decision engine?

---

## Benefits of OpenRouter Migration

### Simplification
- **4 provider files** → **1 provider file**
- **4 different API integrations** → **1 unified API**
- **4 different response formats** → **1 standardized format**

### Standardized Token Tracking
- All models return identical `usage` object structure
- No need to handle provider-specific formats
- Easier to implement metered billing

### Easier Model Management
- Add new models without writing new provider code
- Model switching via config change (no code deployment)
- Automatic fallback if model unavailable

### Cost Transparency
- OpenRouter shows per-model costs in dashboard
- May include cost data in API response
- Easier to verify our 70% markup calculations

---

## Recommendation for Migration

### Phase 0: OpenRouter Migration Strategy

1. **Create OpenRouterProvider** (new file)
   - Implements same `LLMProvider` interface
   - Maps internal model names to OpenRouter format
   - Standardizes response format

2. **Add to Factory** (parallel to existing providers)
   - Don't delete old providers yet
   - Make OpenRouter opt-in initially
   - Test with real bot executions

3. **Migrate Decision Engine**
   - Update configs to use 'openrouter' provider
   - Validate responses identical
   - Monitor for 24 hours

4. **Decision Point: Agents**
   - Keep agents on Claude SDK? (simpler)
   - Or migrate to OpenRouter? (consistency)

5. **Deprecate Old Providers**
   - Mark as deprecated but keep code
   - Use as fallback if OpenRouter issues
   - Eventually remove after 30 days

---

## Next Steps

1. ✅ **Sign up for OpenRouter account**
2. ✅ **Verify model availability** (all our models supported?)
3. ✅ **Test token tracking** (standardized format?)
4. ✅ **Check pricing** (OpenRouter markup vs direct API)
5. ✅ **Create OpenRouterProvider** (implement interface)
6. ✅ **Test with real bot** (verify decisions identical)
7. ✅ **Add token tracking** (now easier with standard format!)
8. ✅ **Proceed to Phase 1** (metered billing)
