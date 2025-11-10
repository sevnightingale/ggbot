# Configuration Architecture Proposal

**Date**: 2025-11-10
**Status**: Proposal
**Goal**: Single source of truth with elegant type-specific validation

---

## The Problem

Currently we have **4 separate definitions** of config structure with **scattered validation logic**. Changes require updating multiple files, and frontend/backend can drift.

## The Solution: Pydantic Discriminated Unions

Use **Pydantic V2** with discriminated unions to define bot configs once, with type-specific validation built into the models.

---

## Proposed Architecture

### 1. Single Source of Truth: `core/config/schemas.py`

```python
"""
Canonical bot configuration schemas using Pydantic V2.
This is the ONLY place where config structure is defined.
TypeScript types are auto-generated from these models.
"""

from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional, Literal, Union
from enum import Enum

# ============================================================================
# Enums (shared across all types)
# ============================================================================

class ConfigType(str, Enum):
    """Bot configuration types."""
    SCHEDULED_TRADING = "scheduled_trading"
    SIGNAL_VALIDATION = "signal_validation"
    AGENT = "agent"

class TradingMode(str, Enum):
    """Trading execution modes."""
    PAPER = "paper"
    SYMPHONY = "symphony"  # Canonical name (not "live")
    ASTER = "aster"

# ============================================================================
# Common Config Components (used by all types)
# ============================================================================

class TradingConfig(BaseModel):
    """Trading execution settings."""
    leverage: int = Field(ge=1, le=100, default=20)
    position_sizing: dict  # Could be further structured
    risk_management: dict

class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: str = Field(default="default")
    model: Optional[str] = None
    use_platform_keys: bool = True
    use_own_key: bool = False

class TelegramIntegrationConfig(BaseModel):
    """Telegram listener/publisher configuration."""
    listener: dict
    publisher: dict

# ============================================================================
# Extraction/Decision Configs (bot-specific)
# ============================================================================

class ExtractionConfig(BaseModel):
    """Market data extraction configuration."""
    selected_data_sources: dict  # Technical analysis, signals, etc.

class DecisionConfig(BaseModel):
    """AI decision-making configuration."""
    system_prompt: str
    user_prompt: str
    analysis_frequency: Optional[str] = None

class AgentStrategy(BaseModel):
    """Agent strategy content (for agent configs only)."""
    content: str
    autonomously_editable: bool = False
    version: int = 1
    last_updated_at: Optional[str] = None
    last_updated_by: Optional[Literal["user", "agent"]] = "user"
    performance_log: list = Field(default_factory=list)

# ============================================================================
# Base Config (common fields for all types)
# ============================================================================

class BaseConfigData(BaseModel):
    """Common fields for all bot configurations."""
    schema_version: str = Field(default="2.1")
    trading: TradingConfig
    llm_config: Optional[LLMConfig] = Field(default_factory=LLMConfig)
    telegram_integration: Optional[TelegramIntegrationConfig] = None

# ============================================================================
# Type-Specific Configs (discriminated by config_type)
# ============================================================================

class ScheduledTradingConfigData(BaseConfigData):
    """
    Standard scheduled trading bot.

    Requirements:
    - Must have selected_pair (single symbol)
    - Must have extraction config (data sources)
    - Must have decision config (AI prompts)
    """
    config_type: Literal[ConfigType.SCHEDULED_TRADING] = ConfigType.SCHEDULED_TRADING
    selected_pair: str = Field(min_length=3, description="Trading symbol (e.g., BTC/USDT)")
    extraction: ExtractionConfig
    decision: DecisionConfig

    @field_validator('extraction')
    def validate_extraction(cls, v):
        """Ensure at least one data source is configured."""
        if not v.selected_data_sources:
            raise ValueError("extraction.selected_data_sources required")
        return v

class SignalValidationConfigData(BaseConfigData):
    """
    Signal validation bot (validates ggShot signals).

    Requirements:
    - Must have selected_pair
    - Must have extraction config
    - Decision config is OPTIONAL (uses signal directly)
    """
    config_type: Literal[ConfigType.SIGNAL_VALIDATION] = ConfigType.SIGNAL_VALIDATION
    selected_pair: str = Field(min_length=3)
    extraction: ExtractionConfig
    decision: Optional[DecisionConfig] = None  # ← Optional for signal validation

class AgentConfigData(BaseConfigData):
    """
    Autonomous agent bot.

    Requirements:
    - All extraction/decision/selected_pair are OPTIONAL
    - Agent can trade multiple symbols dynamically
    - Agent strategy can be built after creation

    Minimum validation:
    - Must have valid trading config
    """
    config_type: Literal[ConfigType.AGENT] = ConfigType.AGENT
    selected_pair: Optional[str] = None  # ← Optional, agent can trade multiple
    extraction: Optional[ExtractionConfig] = None
    decision: Optional[DecisionConfig] = None
    agent_strategy: Optional[AgentStrategy] = None

    @field_validator('trading')
    def validate_trading(cls, v):
        """Ensure minimum trading config for agents."""
        if not v.leverage or v.leverage < 1:
            raise ValueError("trading.leverage must be >= 1")
        if not v.position_sizing:
            raise ValueError("trading.position_sizing required")
        return v

# ============================================================================
# Discriminated Union (THE source of truth)
# ============================================================================

ConfigData = Union[
    ScheduledTradingConfigData,
    SignalValidationConfigData,
    AgentConfigData
]

# Pydantic automatically routes to correct model based on config_type field!

# ============================================================================
# Complete Bot Configuration (table + JSONB)
# ============================================================================

class BotConfiguration(BaseModel):
    """
    Complete bot configuration combining table columns and JSONB data.

    Table columns: config_id, user_id, config_name, config_type,
                   state, trading_mode, symphony_agent_id
    JSONB blob: config_data (one of the discriminated ConfigData types)
    """
    # Table columns
    config_id: str
    user_id: str
    config_name: str
    config_type: ConfigType  # ← Enum enforces valid values
    state: Literal["active", "inactive", "archived"] = "inactive"
    trading_mode: TradingMode = TradingMode.PAPER
    symphony_agent_id: Optional[str] = None
    created_at: str
    updated_at: str

    # JSONB data (discriminated union)
    config_data: ConfigData  # ← Automatically validates based on config_type

    @field_validator('config_data')
    def validate_config_type_match(cls, v, info):
        """Ensure config_data type matches table config_type."""
        table_type = info.data.get('config_type')
        if table_type == ConfigType.SCHEDULED_TRADING and not isinstance(v, ScheduledTradingConfigData):
            raise ValueError("config_type mismatch")
        # Similar for other types
        return v

# ============================================================================
# API Request Models (create/update)
# ============================================================================

class ConfigCreateRequest(BaseModel):
    """API request to create a new bot configuration."""
    config_name: str = Field(min_length=1, max_length=100)
    config_type: ConfigType
    trading_mode: TradingMode = TradingMode.PAPER
    symphony_agent_id: Optional[str] = None
    config_data: ConfigData  # ← Discriminated union validates type-specific fields

class ConfigUpdateRequest(BaseModel):
    """
    API request to update bot configuration.

    All fields optional (partial updates).
    Deep merge happens in service layer.
    """
    config_name: Optional[str] = Field(None, min_length=1, max_length=100)
    config_type: Optional[ConfigType] = None
    config_data: Optional[dict] = None  # ← Partial update dict, merged in service

# ============================================================================
# Usage Examples
# ============================================================================

"""
# Creating a scheduled trading bot
request = ConfigCreateRequest(
    config_name="BTC Scalper",
    config_type=ConfigType.SCHEDULED_TRADING,
    trading_mode=TradingMode.PAPER,
    config_data=ScheduledTradingConfigData(
        selected_pair="BTC/USDT",
        extraction=ExtractionConfig(...),
        decision=DecisionConfig(...),
        trading=TradingConfig(leverage=20)
    )
)
# Pydantic validates: selected_pair required, extraction required, decision required ✅

# Creating an agent bot
agent_request = ConfigCreateRequest(
    config_name="Autonomous Agent",
    config_type=ConfigType.AGENT,
    trading_mode=TradingMode.PAPER,
    config_data=AgentConfigData(
        selected_pair=None,  # ← OK for agents
        extraction=None,     # ← OK for agents
        decision=None,       # ← OK for agents
        trading=TradingConfig(leverage=20)
    )
)
# Pydantic validates: Only trading config required ✅

# Invalid config (Pydantic catches at creation time)
bad_request = ConfigCreateRequest(
    config_name="Bad Bot",
    config_type=ConfigType.SCHEDULED_TRADING,
    config_data=ScheduledTradingConfigData(
        selected_pair=None,  # ❌ Required for scheduled trading
        extraction=None,     # ❌ Required
        decision=None,       # ❌ Required
        trading=TradingConfig(leverage=20)
    )
)
# Raises ValidationError before reaching database ✅
"""
```

---

## Benefits of This Approach

### ✅ Single Source of Truth
- **ONE file** defines all config structures
- Frontend types auto-generated from Pydantic models
- Changes made once, propagate everywhere

### ✅ Type-Specific Validation (Elegant)
- No more `if config_type == "agent": return []` scattered logic
- Each config type is its own model with its own rules
- Pydantic automatically routes to correct model based on discriminator

### ✅ Validation at the Right Place
- **API layer**: Pydantic validates incoming requests (automatic)
- **Model layer**: Type-specific rules built into models
- **Service layer**: No manual validation needed
- **Frontend**: TypeScript types generated from Pydantic

### ✅ Prevents Invalid States
- Can't create scheduled trading bot without extraction
- Can't create agent bot without trading config
- Can't set invalid config_type or trading_mode (enums)

### ✅ Better Developer Experience
- IDE autocomplete for config fields
- Type errors caught at compile time (TypeScript) or runtime (Python)
- Clear documentation in model docstrings

---

## Migration Path

### Phase 1: Create New Models (Week 1)

**Day 1-2**: Create `core/config/schemas.py`
- [ ] Define enums (ConfigType, TradingMode)
- [ ] Define base models (TradingConfig, LLMConfig, etc.)
- [ ] Define type-specific models (ScheduledTradingConfigData, AgentConfigData, etc.)
- [ ] Define discriminated union ConfigData
- [ ] Define complete BotConfiguration model
- [ ] Write unit tests for validation

**Day 3**: Update API Endpoints
- [ ] Update `ggbot.py` to import new models
- [ ] Replace `ConfigCreateRequest` with new version
- [ ] Keep `ConfigUpdateRequest` simple (partial updates)
- [ ] Test: Create bots of each type, verify validation

### Phase 2: Adapt ConfigService (Week 2)

**Day 1-2**: Add Conversion Methods
```python
# In ConfigService
def _pydantic_to_legacy(self, config: BotConfiguration) -> BotConfigV2:
    """Convert new Pydantic model to legacy BotConfigV2."""
    # Temporary bridge during migration

def _legacy_to_pydantic(self, config: BotConfigV2) -> BotConfiguration:
    """Convert legacy BotConfigV2 to new Pydantic model."""
    # Temporary bridge during migration
```

**Day 3-4**: Update Service Methods
- [ ] `create_config()`: Accept Pydantic models, convert to legacy internally
- [ ] `get_config()`: Load from DB, return Pydantic models
- [ ] `update_config()`: Accept Pydantic models, deep merge JSONB
- [ ] Keep legacy methods for backward compat

**Day 5**: Update Orchestrator
- [ ] `ggbot.py`: V2 orchestrator uses Pydantic models
- [ ] Remove manual validation calls (Pydantic handles it)
- [ ] Test: Full pipeline create → execute → update

### Phase 3: Generate Frontend Types (Week 3)

**Day 1**: Setup Type Generation
```bash
pip install pydantic-to-typescript
pydantic2ts --module core.config.schemas --output frontend/types/generated.ts
```

**Day 2-3**: Update Frontend
- [ ] Replace manual `ConfigData` interface with generated types
- [ ] Update `apiClient` to use generated types
- [ ] Test: Create bots from frontend, verify types match

**Day 4**: Cleanup
- [ ] Remove old `BotConfigV2` class
- [ ] Remove old `ConfigRepository` (if unused)
- [ ] Remove manual validation logic
- [ ] Update documentation

---

## Validation Flow (After Migration)

```
┌─────────────────────────────────────────────────────────┐
│  Frontend sends ConfigCreateRequest                     │
│  {                                                       │
│    config_type: "scheduled_trading",                   │
│    config_data: { selected_pair: null }  ← Invalid     │
│  }                                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Pydantic Validation (Automatic)                       │
│  - Check config_type is valid enum                     │
│  - Route to ScheduledTradingConfigData model           │
│  - Validate: selected_pair is required                 │
│  - Validate: extraction is required                    │
│  - Validate: decision is required                      │
│                                                         │
│  ❌ Raises ValidationError:                             │
│     "selected_pair is required for scheduled_trading"  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  FastAPI Error Handler                                 │
│  Returns 422 Unprocessable Entity with details         │
│  {                                                       │
│    "detail": [                                          │
│      {                                                   │
│        "loc": ["config_data", "selected_pair"],        │
│        "msg": "field required",                        │
│        "type": "value_error.missing"                   │
│      }                                                   │
│    ]                                                     │
│  }                                                       │
└─────────────────────────────────────────────────────────┘

✅ Invalid config NEVER reaches database
✅ No manual validation needed in service layer
✅ Frontend gets detailed error messages
```

---

## Comparison: Before vs After

### Before (Current)

```python
# 1. Define in API layer (ggbot.py)
class ConfigCreateRequest(BaseModel):
    config_type: str = "autonomous_trading"
    selected_pair: Optional[str] = None  # ← No validation
    extraction: Optional[Dict] = None    # ← No structure

# 2. Manual validation in service layer (config_service.py)
def validate(self):
    errors = []
    if self.config_type == "agent":
        return []  # ← No validation for agents
    if not self.selected_pair:
        errors.append("selected_pair required")  # ← Manual check
    # ... 50 lines of if/elif validation logic
    return errors

# 3. Separate frontend types (lib/api.ts)
interface ConfigData {  // ← Can drift from Python
  selected_pair: string
  extraction?: any  // ← No structure
}
```

**Problems**:
- 3 definitions (API, Service, Frontend) can drift
- Manual validation scattered across services
- No type safety for nested objects
- Agents have zero validation

### After (Proposed)

```python
# Single definition (core/config/schemas.py)
class ScheduledTradingConfigData(BaseConfigData):
    config_type: Literal["scheduled_trading"] = "scheduled_trading"
    selected_pair: str  # ← Required by type definition
    extraction: ExtractionConfig  # ← Structured and validated
    decision: DecisionConfig  # ← Structured and validated

class AgentConfigData(BaseConfigData):
    config_type: Literal["agent"] = "agent"
    selected_pair: Optional[str] = None  # ← Optional by type definition

    @field_validator('trading')
    def validate_trading(cls, v):  # ← Minimum validation for agents
        if not v.leverage:
            raise ValueError("trading.leverage required")
        return v

# API layer (ggbot.py) - just uses the model
@app.post("/api/v2/config")
async def create_config(request: ConfigCreateRequest):  # ← Pydantic validates automatically
    config = await config_service.create(request)
    return config

# Service layer (config_service.py) - no manual validation
async def create(self, request: ConfigCreateRequest):
    # Pydantic already validated, just save to database
    return await self._save_to_db(request.config_data)

# Frontend (generated types)
// Auto-generated from Python Pydantic models
export type ConfigData =
  | ScheduledTradingConfigData  // selected_pair required
  | SignalValidationConfigData  // selected_pair required
  | AgentConfigData             // selected_pair optional
```

**Benefits**:
- 1 definition in Python, types generated for TypeScript
- Validation automatic via Pydantic
- Type safety for nested objects
- Agents have minimum validation
- No manual if/elif logic

---

## Alternative: Keep Current, Add Consistency

If full migration is too much, we could:

1. **Choose BotConfig (Pydantic) as canonical**
2. **Deprecate BotConfigV2** (plain Python class)
3. **Migrate ConfigService to use BotConfig**
4. **Generate TypeScript from BotConfig**
5. **Add discriminated union to existing BotConfig**

This is less elegant but lower risk.

---

## Recommendation

**Go with Discriminated Unions approach**:
- Modern Python pattern (Pydantic V2 feature)
- Clean separation of concerns
- Single source of truth
- Type-safe end-to-end
- Better DX for future development

**Estimated effort**: 3 weeks (1 week per phase)
**Risk**: Medium (requires thorough testing)
**Benefit**: High (eliminates entire class of bugs)

---

**Next Step**: Review this proposal, decide on approach, create implementation plan.
