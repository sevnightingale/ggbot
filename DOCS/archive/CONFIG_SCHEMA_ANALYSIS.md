# config_data JSONB Schema: Critical Analysis

**Date**: 2025-11-10
**Status**: Analysis & Discussion
**Goal**: Evaluate current schema structure before locking in validation architecture

---

## Current Production Schema

Based on actual production data analysis (378 configs), here's what we have:

```json
{
  "schema_version": "2.1",
  "selected_pair": "BTC/USDT",
  "extraction": { /* market data sources */ },
  "decision": { /* AI decision config */ },
  "trading": { /* execution settings */ },
  "llm_config": { /* LLM provider */ },
  "telegram_integration": { /* Telegram config */ },
  "agent_strategy": { /* only for agents */ }
}
```

---

## Field-by-Field Analysis

### 1. `schema_version` ✅ Keep

```json
"schema_version": "2.1"
```

**Current Usage**: Version string for JSONB schema
**Issues**: None - good practice
**Questions**:
- Should we use semver? (e.g., "2.1.0")
- Do we ever actually check/migrate based on this?

**Recommendation**: ✅ **Keep as-is**, ensure migration logic exists

---

### 2. `selected_pair` ⚠️ Needs Discussion

```json
"selected_pair": "BTC/USDT"
```

**Current Usage**:
- Required for scheduled_trading and signal_validation
- Optional for agents (can trade multiple symbols)

**Issues Identified**:

**Issue #1: Single Symbol Limitation**
- Standard bots can only trade ONE symbol at a time
- Users must create separate bots for BTC, ETH, SOL
- Agents can trade multiple, but standard bots can't

**Issue #2: Naming**
- "selected_pair" implies user selection from UI
- Could be "symbol" or "trading_pair"
- CCXT uses "symbol"

**Issue #3: Format Ambiguity**
- Is it "BTC/USDT" (CCXT format)?
- Or "BTCUSDT" (exchange format)?
- Do we normalize on load?

**Questions for Discussion**:
1. Should standard bots support multiple symbols? (Breaking change)
2. Should we rename to `symbol` for clarity?
3. Should we support symbol lists? `symbols: ["BTC/USDT", "ETH/USDT"]`
4. How do we handle symbol validation (is it real-time cached)?

**Recommendations**:
- **Option A (Conservative)**: Keep `selected_pair`, single symbol only
- **Option B (Future-proof)**: Add `symbols: string[]`, deprecate `selected_pair`
- **Option C (Simplify)**: Rename to `symbol` for clarity

---

### 3. `extraction` ⚠️ Needs Redesign

```json
{
  "selected_data_sources": {
    "technical_analysis": {
      "data_points": ["RSI", "MACD"],
      "timeframes": ["5m", "15m", "1h"]
    },
    "signals_group_chats": {
      "data_points": ["ggShot"],
      "timeframes": ["1h"]
    }
  }
}
```

**Issues Identified**:

**Issue #1: Naming "selected_data_sources"**
- Verbose and redundant
- Everything in extraction is "selected"
- Could just be `data_sources` or `sources`

**Issue #2: "data_points" Terminology**
- For technical_analysis: "data_points" = indicator names (RSI, MACD)
- For signals_group_chats: "data_points" = channel names (ggShot)
- Confusing - indicators vs channels vs data types
- Should be `indicators`, `channels`, etc.

**Issue #3: Timeframes on Every Source**
- Each data source has its own timeframes array
- For technical analysis, this makes sense (RSI on 5m, 15m, 1h)
- For signals, less clear (ggShot signals have their own timeframe)
- Redundant if user wants same timeframe for all sources

**Issue #4: Flat Structure, No Hierarchy**
```json
// Current (flat)
"technical_analysis": {
  "data_points": ["RSI", "MACD"]
}

// Could be more structured
"technical_analysis": {
  "indicators": {
    "RSI": { "period": 14 },
    "MACD": { "fast": 12, "slow": 26, "signal": 9 }
  }
}
```

**Issue #5: Legacy "indicators" Structure Still Exists**
- Old configs have `extraction.indicators` (legacy)
- New configs have `extraction.selected_data_sources` (new)
- We're supporting both, adding complexity

**Questions for Discussion**:
1. Should we remove legacy `indicators` support? (Migration needed)
2. Should each data source type have its own structure?
   - `technical_analysis: { indicators: {...}, timeframes: [...] }`
   - `signals: { channels: [...] }`
   - `news: { keywords: [...], sources: [...] }`
3. Should timeframes be global or per-source?
4. Do we need indicator parameters (RSI period, MACD settings)?

**Recommendations**:
```json
// Proposed structure
"extraction": {
  "timeframes": ["5m", "15m", "1h"],  // ← Global default timeframes
  "sources": {
    "technical_analysis": {
      "indicators": ["RSI", "MACD", "EMA"],  // ← Renamed from data_points
      "timeframes": ["1h"]  // ← Override global (optional)
    },
    "signals": {
      "channels": ["ggShot"],  // ← Renamed from data_points
      "validation_mode": true
    },
    "news": {
      "enabled": true,
      "keywords": ["Bitcoin", "regulation"]
    }
  }
}
```

---

### 4. `decision` ⚠️ Needs Clarity

```json
{
  "system_prompt": "You are an expert trader...",
  "user_prompt": "if RSI below 50 enter long...",
  "analysis_frequency": "1h"
}
```

**Issues Identified**:

**Issue #1: analysis_frequency Placement**
- Is this an extraction frequency or decision frequency?
- Extraction happens on schedule, then decision runs
- Should this be `extraction.frequency` instead?
- Or top-level `schedule.frequency`?

**Issue #2: Prompt Structure**
- Two separate prompts (system + user)
- LLM receives: `[{system: ...}, {user: ...}]`
- Could be clearer what each is for

**Issue #3: Agents Don't Use This**
- Agents have their own strategy in `agent_strategy`
- But agents still have a `decision` object (empty)
- Should agents have `decision: null`?

**Questions for Discussion**:
1. Should `analysis_frequency` move to top-level `schedule` object?
2. Should we rename prompts for clarity?
   - `system_instructions` / `trading_strategy`
   - `context` / `strategy`
3. Should agents have decision config at all?

**Recommendations**:
```json
// Option A: Keep prompts, move frequency
"schedule": {
  "frequency": "1h",
  "enabled": true
},
"decision": {
  "system_instructions": "You are an expert trader...",
  "strategy": "if RSI below 50 enter long..."
}

// Option B: Merge into single strategy
"decision": {
  "strategy": {
    "instructions": "...",
    "rules": "..."
  }
}
```

---

### 5. `trading` ❌ Has Serious Issues

```json
{
  "leverage": 1,
  "execution_mode": "paper",  // ⚠️ DUPLICATE
  "exchange_config": {  // ⚠️ LEGACY
    "api_key": "",
    "secret_key": "",
    "exchange_type": "cex",
    "selected_exchange": "binance"
  },
  "position_sizing": {
    "method": "fixed_usd",
    "account_percent": 5,
    "fixed_amount_usd": 100,
    "max_position_percent": 10
  },
  "risk_management": {
    "max_positions": 1,
    "max_daily_loss_usd": 500,
    "default_stop_loss_percent": 5,
    "default_take_profit_percent": 10
  }
}
```

**Issues Identified**:

**Issue #1: 🚨 execution_mode DUPLICATION 🚨**
```
Table column: trading_mode = 'paper' | 'symphony' | 'aster'
JSONB field:  trading.execution_mode = 'paper' | 'live' | 'aster'
```

**This is a CRITICAL ISSUE**:
- `trading_mode` in table column is source of truth
- `trading.execution_mode` in JSONB is redundant
- They can diverge and cause bugs
- **Production query**: All 378 configs have this duplication

**Issue #2: exchange_config is LEGACY**
- Contains hardcoded API keys (empty in production)
- Keys should be in Vault, not config
- `selected_exchange` is unused (Symphony/Aster handle exchange routing)
- `exchange_type` (cex/dex) is unused
- This entire object should be removed

**Issue #3: position_sizing Has Multiple Methods**
- `method`: "fixed_usd" | "account_percent" | "confidence_based"
- If `method = "fixed_usd"`, only `fixed_amount_usd` is used
- If `method = "confidence_based"`, only `max_position_percent` is used
- Storing all fields for all methods is confusing

**Issue #4: Provider Field in Agent Configs**
```json
"trading": {
  "provider": "aster"  // ← Only in agent configs
}
```
- Agent configs have `trading.provider` field
- Not in standard configs
- Inconsistent structure across types

**Questions for Discussion**:
1. **CRITICAL**: Remove `trading.execution_mode` entirely? (Use table column only)
2. Remove entire `exchange_config` object? (Vault handles credentials)
3. Should position_sizing be a discriminated union by method?
   ```python
   position_sizing: FixedUSD | AccountPercent | ConfidenceBased
   ```
4. Should agent `trading.provider` exist, or use table `trading_mode`?

**Recommendations**:
```json
// Proposed structure
"trading": {
  "leverage": 20,
  "position_sizing": {
    // If method = fixed_usd
    "method": "fixed_usd",
    "amount_usd": 100
  },
  // OR if method = confidence_based
  "position_sizing": {
    "method": "confidence_based",
    "max_position_percent": 25.0
  },
  "risk_management": {
    "max_positions": 3,
    "max_daily_loss_usd": 500,
    "stop_loss_percent": 5.0,
    "take_profit_percent": 10.0
  }
  // ❌ Remove: execution_mode (use table column)
  // ❌ Remove: exchange_config (use Vault)
  // ❌ Remove: provider (use table trading_mode)
}
```

---

### 6. `llm_config` ✅ Mostly Good

```json
{
  "provider": "default",
  "model": "default",
  "use_platform_keys": true,
  "use_own_key": false
}
```

**Issues Identified**:

**Issue #1: "default" is Ambiguous**
- What does `provider: "default"` mean?
- Which model is "default"?
- Should be explicit: "openai" | "anthropic" | "xai" | "deepseek"

**Issue #2: Key Management Flags**
- `use_platform_keys` and `use_own_key` are mutually exclusive
- Could be single field: `key_source: "platform" | "user"`
- Actual keys stored in Vault via `user_llm_credentials` table

**Questions for Discussion**:
1. Remove "default" provider, force explicit choice?
2. Simplify to single `key_source` field?
3. Should `model` be optional or required?

**Recommendations**:
```json
// Proposed
"llm_config": {
  "provider": "openai",  // ← No "default"
  "model": "gpt-4o",  // ← Specific model
  "key_source": "platform"  // ← Simplified from two booleans
}
```

---

### 7. `telegram_integration` ⚠️ Optional, Rarely Used

```json
{
  "listener": {
    "enabled": false,
    "api_id": "",
    "api_hash": "",
    "session_name": "",
    "source_channels": []
  },
  "publisher": {
    "enabled": false,
    "bot_token": "",
    "filter_channel": "",
    "confidence_threshold": 0.7,
    "include_reasoning": true,
    "include_market_context": false,
    "message_template": "..."
  }
}
```

**Issues Identified**:

**Issue #1: Credentials in Config**
- `api_id`, `api_hash`, `bot_token` stored in JSONB
- Should be in Vault
- Security risk if JSONB is exposed

**Issue #2: Large Empty Object**
- Most configs have empty `telegram_integration: {}`
- Adds bloat to every config
- Could be `null` if not used

**Issue #3: Two Separate Features**
- Listener: Read signals from Telegram channels
- Publisher: Post signals to Telegram
- Could be separate top-level fields

**Questions for Discussion**:
1. Move credentials to Vault?
2. Allow `telegram_integration: null` if unused?
3. Split into `telegram_listener` and `telegram_publisher`?

**Recommendations**:
```json
// If not used
"telegram_integration": null

// If used
"telegram_integration": {
  "listener": {
    "enabled": true,
    "source_channels": ["@cryptosignals"],
    // Credentials in Vault, referenced by user_id
  },
  "publisher": {
    "enabled": true,
    "filter_channel": "@mytrades",
    "confidence_threshold": 0.7
    // Bot token in Vault
  }
}
```

---

### 8. `agent_strategy` ✅ Good Structure

```json
{
  "content": "You are an autonomous trading agent...",
  "autonomously_editable": false,
  "version": 1,
  "last_updated_at": "2025-11-10T10:30:00Z",
  "last_updated_by": "user",
  "performance_log": []
}
```

**Issues Identified**: None significant

**Possible Improvements**:
- Could add `created_at` timestamp
- `performance_log` structure undefined (empty arrays in production)

**Recommendations**: ✅ Keep as-is, maybe add `created_at`

---

## Fields That Should NOT Be in JSONB

Based on analysis, these fields should **remain as table columns** (not JSONB):

✅ **Already table columns (correct)**:
- `config_id` - Primary key
- `user_id` - Owner
- `config_name` - User-facing name
- `config_type` - Bot type (scheduled/signal/agent)
- `state` - Active/inactive/archived
- `trading_mode` - Paper/symphony/aster ← **Use this, not JSONB field**
- `symphony_agent_id` - Symphony integration ID
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

❌ **Should NOT be added to JSONB**:
- Anything requiring SQL filtering/indexing
- Anything frequently queried across all configs
- User credentials (use Vault)

---

## Proposed JSONB Schema (Clean Version)

```json
{
  // ========================================
  // Meta
  // ========================================
  "schema_version": "2.2",

  // ========================================
  // Scheduling (for scheduled bots)
  // ========================================
  "schedule": {
    "frequency": "1h",  // ← Moved from decision.analysis_frequency
    "enabled": true
  },

  // ========================================
  // Symbol(s)
  // ========================================
  "symbol": "BTC/USDT",  // ← Renamed from selected_pair
  // OR for future multi-symbol:
  // "symbols": ["BTC/USDT", "ETH/USDT"],

  // ========================================
  // Market Data Extraction
  // ========================================
  "extraction": {
    "timeframes": ["5m", "15m", "1h", "4h"],  // ← Global default
    "sources": {
      "technical_analysis": {
        "indicators": ["RSI", "MACD", "EMA"],  // ← Renamed from data_points
        "timeframes": ["1h"]  // ← Override (optional)
      },
      "signals": {
        "channels": ["ggShot"]  // ← Renamed from data_points
      },
      "news": {
        "enabled": false
      }
      // Future: Add more sources
    }
  },

  // ========================================
  // AI Decision Config
  // ========================================
  "decision": {
    "system_instructions": "You are an expert trader...",
    "strategy": "if RSI below 50 enter long..."
  },

  // ========================================
  // Trading Execution
  // ========================================
  "trading": {
    "leverage": 20,
    "position_sizing": {
      "method": "confidence_based",
      "max_position_percent": 25.0
    },
    "risk_management": {
      "max_positions": 3,
      "max_daily_loss_usd": 500,
      "stop_loss_percent": 5.0,
      "take_profit_percent": 10.0
    }
    // ❌ REMOVED: execution_mode (use table column trading_mode)
    // ❌ REMOVED: exchange_config (use Vault)
    // ❌ REMOVED: provider (use table trading_mode)
  },

  // ========================================
  // LLM Configuration
  // ========================================
  "llm_config": {
    "provider": "openai",  // ← No "default", must be explicit
    "model": "gpt-4o",
    "key_source": "platform"  // ← Simplified from two booleans
  },

  // ========================================
  // Telegram Integration (optional)
  // ========================================
  "telegram_integration": null,  // ← null if not used
  // OR if used:
  // "telegram_integration": {
  //   "listener": { /* ... */ },
  //   "publisher": { /* ... */ }
  // },

  // ========================================
  // Agent Strategy (agents only)
  // ========================================
  "agent_strategy": {
    "content": "...",
    "autonomously_editable": false,
    "version": 1,
    "created_at": "2025-11-10T10:00:00Z",
    "last_updated_at": "2025-11-10T10:30:00Z",
    "last_updated_by": "user",
    "performance_log": []
  }
}
```

---

## Critical Changes Summary

### 🚨 MUST FIX (Breaking)

1. **Remove `trading.execution_mode`** - Use table `trading_mode` only
2. **Remove `trading.exchange_config`** - Legacy, credentials in Vault
3. **Rename `selected_pair` → `symbol`** - Clearer terminology

### ⚠️ SHOULD FIX (Improve)

4. **Rename `extraction.selected_data_sources` → `extraction.sources`**
5. **Rename `data_points` → type-specific names** (`indicators`, `channels`)
6. **Move `decision.analysis_frequency` → `schedule.frequency`**
7. **Simplify `llm_config`** - Remove "default", single `key_source`

### ✅ NICE TO HAVE (Optional)

8. Allow `telegram_integration: null` instead of empty object
9. Add `agent_strategy.created_at` timestamp
10. Support multiple symbols: `symbols: string[]`

---

## Migration Strategy

### Phase 1: Remove Duplicates (Week 1)

**1.1 Remove trading.execution_mode**
```sql
-- Verify all configs have trading_mode column
SELECT COUNT(*) FROM configurations WHERE trading_mode IS NULL;

-- Remove JSONB field
UPDATE configurations
SET config_data = config_data - 'trading' ||
  jsonb_build_object('trading', (config_data->'trading') - 'execution_mode')
WHERE config_data->'trading'->'execution_mode' IS NOT NULL;
```

**1.2 Remove trading.exchange_config**
```sql
UPDATE configurations
SET config_data = config_data - 'trading' ||
  jsonb_build_object('trading', (config_data->'trading') - 'exchange_config')
WHERE config_data->'trading'->'exchange_config' IS NOT NULL;
```

**1.3 Update schema_version**
```sql
UPDATE configurations
SET config_data = jsonb_set(config_data, '{schema_version}', '"2.2"');
```

### Phase 2: Rename Fields (Week 2)

**2.1 Rename selected_pair → symbol**
```sql
UPDATE configurations
SET config_data = config_data - 'selected_pair' ||
  jsonb_build_object('symbol', config_data->'selected_pair')
WHERE config_data->>'selected_pair' IS NOT NULL;
```

**2.2 Restructure extraction** (more complex, needs careful migration)

### Phase 3: Update Code (Week 3)

- Update backend models to expect new schema
- Update frontend types
- Remove legacy field support
- Update validation logic

---

## Questions for Decision

Before we finalize the schema:

1. **Symbol field**: Keep `selected_pair`, rename to `symbol`, or support multiple `symbols`?

2. **extraction structure**: Go with proposed `sources` + type-specific names, or keep current?

3. **schedule**: Create top-level `schedule` object, or keep `analysis_frequency` in decision?

4. **telegram_integration**: Allow `null` for unused configs, or keep empty object?

5. **Breaking changes**: Do all at once, or incremental with backward compatibility?

6. **Legacy support**: How long should we support old schema_version configs?

---

## Next Steps

1. **Review this analysis** - Agree on which changes to make
2. **Prioritize changes** - What's critical vs nice-to-have?
3. **Write migration plan** - Detailed SQL + code changes
4. **Update validation architecture** - Use clean schema in Pydantic models
5. **Test thoroughly** - Ensure no data loss during migration

---

**This is a critical foundation decision - once we lock in the schema structure, we'll generate validation from it.**
