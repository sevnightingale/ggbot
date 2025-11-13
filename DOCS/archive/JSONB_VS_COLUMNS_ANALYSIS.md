# JSONB vs Columns: Should We Flatten?

**Date**: 2025-11-10
**Question**: Should we stop using JSONB and move settings to table columns?
**Answer**: **No - but we should simplify the nested structure**

---

## TL;DR

**Keep JSONB** - it's the right tool for our use case. The problem isn't JSONB itself, it's that our nested structure has gotten too complex. Solution: **Simplify nesting + Use Pydantic for type safety + Implement deep merge**.

---

## Analysis: What Do We Actually Query?

### Current Query Patterns (Verified from Codebase)

**Fields we filter by in WHERE clauses**:
```sql
-- These are TABLE COLUMNS (correct placement)
WHERE config_id = %s       ✓
WHERE user_id = %s         ✓
WHERE state = 'active'     ✓
WHERE config_type = 'agent' ✓
WHERE trading_mode = 'paper' ✓
```

**Fields we NEVER filter by**:
```sql
-- These are in JSONB (correct placement)
WHERE selected_pair = 'BTC/USDT'     ✗ Never done
WHERE leverage = 20                  ✗ Never done
WHERE analysis_frequency = '15m'     ✗ Never done
WHERE system_prompt LIKE '%...'      ✗ Never done
```

**Reality check**:
- 378 total configs
- 12 unique symbols (selected_pair)
- 9 unique leverage values
- 6 unique analysis frequencies
- Average JSONB size: 1.2 KB (tiny!)

**Conclusion**: We load entire configs, we don't filter by nested fields. **JSONB is correct.**

---

## The REAL Problem: Complex Nesting

The issue isn't JSONB vs columns - it's that the structure has 3-4 levels of nesting:

```json
{
  "extraction": {                           // ← Level 1
    "selected_data_sources": {              // ← Level 2
      "technical_analysis": {               // ← Level 3
        "data_points": ["RSI", "MACD"],     // ← Level 4
        "timeframes": ["5m", "15m", ...]    // ← Level 4
      },
      "signals_group_chats": {...},         // ← Level 3
      "fundamental_analysis": {...}         // ← Level 3
    }
  }
}
```

**This is confusing because**:
- Hard to remember path: `config.extraction.selected_data_sources.technical_analysis.data_points`
- Hard to update: Must preserve all 4 levels during partial updates
- Hard to validate: Pydantic validation is complex for deep nesting

---

## Option 1: Flatten to Columns (NOT RECOMMENDED)

### What It Would Look Like

```sql
CREATE TABLE configurations (
    config_id UUID,
    user_id UUID,
    config_name VARCHAR,
    config_type VARCHAR,
    state TEXT,
    trading_mode VARCHAR,

    -- 50+ new columns
    selected_pair VARCHAR,
    leverage INTEGER,
    position_sizing_method VARCHAR,
    position_sizing_fixed_amount NUMERIC,
    position_sizing_max_percent NUMERIC,
    risk_max_positions INTEGER,
    risk_default_sl_percent NUMERIC,
    risk_max_daily_loss NUMERIC,
    system_prompt TEXT,
    user_prompt TEXT,
    analysis_frequency VARCHAR,
    llm_provider VARCHAR,
    llm_model VARCHAR,
    telegram_listener_enabled BOOLEAN,
    telegram_listener_api_id VARCHAR,
    telegram_publisher_bot_token VARCHAR,
    agent_strategy_content TEXT,
    agent_strategy_version INTEGER,
    -- ... 40 more columns
);
```

### ❌ Why This is BAD

1. **60-70 columns** in a single table (unmaintainable)
2. **Every new feature** requires ALTER TABLE migration
3. **No flexibility** for user-specific settings
4. **NULL everywhere** for optional features
5. **Array fields** (indicators, timeframes) become TEXT[] or comma-separated (ugly)
6. **Different configs** need different fields (scheduled vs agent)
7. **Breaking changes** every time we add a field

### Example: Adding a New Indicator

**With JSONB**:
```python
# No migration needed
config_data["extraction"]["selected_data_sources"]["technical_analysis"]["data_points"].append("VWAP")
```

**With columns**:
```sql
-- Need migration for every new indicator? Or generic TEXT[] column?
ALTER TABLE configurations ADD COLUMN use_vwap BOOLEAN;
ALTER TABLE configurations ADD COLUMN vwap_period INTEGER;
```

---

## Option 2: Keep JSONB, Simplify Structure (RECOMMENDED)

### Simplify Nesting Levels

**Before** (4 levels):
```json
{
  "extraction": {
    "selected_data_sources": {
      "technical_analysis": {
        "data_points": ["RSI", "MACD"]
      }
    }
  }
}
```

**After** (2 levels):
```json
{
  "extraction": {
    "technical_indicators": ["RSI", "MACD", "EMA"],
    "signal_sources": ["ggShot"],
    "fundamental_sources": ["news", "onchain"]
  }
}
```

**Benefits**:
- Easier to understand: `config.extraction.technical_indicators`
- Easier to update: Only 2 levels to preserve
- Still flexible for new features

### Use Pydantic for Type Safety

**Define structure explicitly**:
```python
class ExtractionConfig(BaseModel):
    """Flat, clear extraction config."""
    technical_indicators: List[str] = Field(default_factory=list)
    signal_sources: List[str] = Field(default_factory=list)
    fundamental_sources: List[str] = Field(default_factory=list)
    timeframes: List[str] = Field(default=["5m", "15m", "1h", "4h", "1d"])

class TradingConfig(BaseModel):
    """Clear trading config."""
    leverage: int = Field(ge=1, le=100)
    position_sizing_method: str
    position_sizing_params: dict  # Flexible for different methods
    max_positions: int
    default_stop_loss_percent: float
    default_take_profit_percent: float
```

**Benefits**:
- Type-safe in Python and TypeScript (auto-generated)
- Clear documentation via Field descriptions
- Validation built into model
- IDE autocomplete works

### Implement Proper Deep Merge

**Current problem**:
```python
# Frontend sends partial update
{"trading": {"leverage": 25}}

# Backend does shallow merge (BAD)
config.trading = update_data.get("trading", existing.trading)
# Result: Entire trading object replaced, loses position_sizing, risk_management!
```

**Solution**:
```python
def deep_merge(base: dict, update: dict) -> dict:
    """Recursively merge dicts, preserving nested fields."""
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)  # Recurse
        else:
            result[key] = value
    return result

# Now partial updates work correctly
config.trading = deep_merge(existing.trading, update_data.get("trading", {}))
```

---

## Option 3: Hybrid (MIDDLE GROUND)

Keep JSONB but **extract frequently-displayed fields** to columns for convenience:

```sql
CREATE TABLE configurations (
    -- Current columns (keep)
    config_id UUID,
    user_id UUID,
    config_name VARCHAR,
    config_type VARCHAR,
    state TEXT,
    trading_mode VARCHAR,
    symphony_agent_id VARCHAR,

    -- Add commonly-displayed fields (optional)
    selected_pair VARCHAR,       -- Shown in bot list
    leverage INTEGER,             -- Shown in config summary

    -- Keep JSONB for everything else
    config_data JSONB,

    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**When to use this**:
- If you frequently show `selected_pair` in lists/tables
- If you want to sort by `leverage`
- If you want simple SQL reports

**Trade-off**:
- Slight duplication (field in column AND JSONB)
- Must keep them in sync
- Easier for SQL queries/reports

---

## Comparison Table

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| **Full Columns** | Simple queries, constraints | 60+ columns, rigid, migrations | ❌ Overkill |
| **Keep JSONB + Simplify** | Flexible, clean, type-safe | Need deep merge | ✅ Best |
| **Hybrid** | Best of both | Slight duplication | ⚠️ Only if needed |

---

## Real-World Examples

### Stripe (Payments)
```sql
-- Stripe stores flexible metadata in JSONB
CREATE TABLE customers (
    id VARCHAR PRIMARY KEY,
    email VARCHAR,
    metadata JSONB  -- User-defined key-value pairs
);
```

### GitHub (Repository Settings)
```sql
-- GitHub uses JSONB for repository settings
CREATE TABLE repositories (
    id BIGINT PRIMARY KEY,
    name VARCHAR,
    settings JSONB  -- Features, protections, webhooks
);
```

### Notion (Flexible Schema)
```sql
-- Notion stores page properties in JSONB
CREATE TABLE pages (
    id UUID PRIMARY KEY,
    title TEXT,
    properties JSONB  -- User-defined fields
);
```

**Pattern**: Use JSONB for **user-configurable settings** that vary widely and evolve rapidly.

---

## Recommendation: Keep JSONB, Fix the Code

### Phase 1: Simplify Structure (Week 1)

**Current**:
```json
{
  "extraction": {
    "selected_data_sources": {
      "technical_analysis": {
        "data_points": ["RSI"],
        "timeframes": ["5m"]
      }
    }
  }
}
```

**Simplified**:
```json
{
  "extraction": {
    "indicators": ["RSI", "MACD"],
    "signals": ["ggShot"],
    "timeframes": ["5m", "15m", "1h"]
  }
}
```

**Migration script**:
```python
# Flatten extraction config for all bots
for config in configs:
    old = config["extraction"]["selected_data_sources"]
    new = {
        "indicators": old.get("technical_analysis", {}).get("data_points", []),
        "signals": old.get("signals_group_chats", {}).get("data_points", []),
        "timeframes": old.get("technical_analysis", {}).get("timeframes", [])
    }
    config["extraction"] = new
```

### Phase 2: Pydantic Models (Week 2)

```python
# core/config/schemas.py
class ExtractionConfig(BaseModel):
    indicators: List[str] = []
    signals: List[str] = []
    timeframes: List[str] = ["5m", "15m", "1h", "4h", "1d"]

class TradingConfig(BaseModel):
    leverage: int = Field(ge=1, le=100)
    position_sizing_method: str
    position_sizing_params: dict
    max_positions: int
    stop_loss_percent: float
    take_profit_percent: float

class ConfigData(BaseModel):
    schema_version: str = "3.0"  # New version for flat structure
    selected_pair: str
    extraction: ExtractionConfig
    trading: TradingConfig
    # ...
```

### Phase 3: Deep Merge (Week 2)

```python
# core/services/config_service.py
def _deep_merge_config_data(
    existing: dict,
    updates: dict
) -> dict:
    """Recursively merge config updates, preserving nested fields."""
    result = existing.copy()
    for key, value in updates.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = self._deep_merge_config_data(result[key], value)
        else:
            result[key] = value
    return result

async def update_config(self, config_id, updates):
    existing = await self.get_config(config_id)
    merged = self._deep_merge_config_data(
        existing.config_data,
        updates
    )
    # Save merged config
```

---

## Why JSONB is Actually Perfect for Us

1. **We never filter by nested fields** ✅
2. **We always load entire configs** ✅
3. **Configs are user-specific** ✅
4. **Schema evolves rapidly** (new indicators, new AI models) ✅
5. **Configs are small** (1.2 KB average) ✅
6. **Different bot types need different fields** ✅

**JSONB is designed for exactly this use case.**

---

## The Real Solution

❌ Don't flatten to columns
❌ Don't add more tables
✅ **Simplify the nesting** (3-4 levels → 2 levels)
✅ **Use Pydantic for structure** (type safety)
✅ **Implement deep merge** (no data loss)
✅ **Generate TypeScript types** (frontend/backend sync)

---

## Conclusion

**Keep JSONB.** The confusion isn't from JSONB itself - it's from:
1. Too many nesting levels
2. Lack of explicit structure (Pydantic)
3. Shallow merge bugs
4. No auto-generated types

Fix those 4 things, and JSONB becomes elegant and maintainable.

**Next step**: Implement simplified flat structure with Pydantic discriminated unions (see `CONFIG_ARCHITECTURE_PROPOSAL.md`).
