# Breaking Points Analysis: Market Data Structure Change

## Executive Summary
Changing from `(symbol, timeframe)` to `(config_id, symbol)` storage will impact multiple systems. Here's a comprehensive analysis of what will break and needs updating.

## 1. Database Schema & Queries

### Current Structure Issues
- **Primary Key**: Currently uses `(user_id, symbol, timeframe, updated_at)`
- **Indexes**: Optimized for `(user_id, symbol, timeframe)` lookups
- **No config_id column**: The market_data table doesn't have a config_id field

### Breaking Points
1. **extraction/utils.py** - `store_market_data_entries()`:
   - Lines 69-83: INSERT/UPSERT uses `(user_id, symbol, timeframe, updated_at)` constraint
   - Need to change to `(user_id, config_id, symbol, updated_at)`

2. **decision/engine.py** - `_fetch_market_data()`:
   - Lines 193-202: Queries by `symbol + timeframe`
   - Loops through timeframes to fetch data
   - Assumes timeframe-based organization

3. **extraction/utils.py** - `get_latest_market_data()`:
   - Lines 127-141: Queries by `(user_id, symbol, timeframe)`
   - Used by various modules for data retrieval

## 2. Decision Module Dependencies

### Critical Breaking Points

1. **decision/engine.py - _fetch_market_data()**:
   ```python
   # Current: Lines 176-266
   for timeframe in timeframes:
       cursor.execute("""
           SELECT source, data_type, indicators, raw_data, updated_at
           FROM market_data
           WHERE user_id = %s AND symbol = %s AND timeframe = %s
       """, (self.user_id, symbol, timeframe))
   ```
   - Returns data organized by timeframe
   - Decision prompts expect this structure

2. **decision/engine.py - get_indicator_data() helper**:
   ```python
   # Lines 614-633
   # Expects data organized by timeframe
   data = market_data.get(native_timeframe, {}).get('indicators', {})
   ```
   - Hardcoded to look for indicators within timeframe buckets
   - Multi-timeframe indicators stored with suffix (e.g., "RSI_4h")

3. **ggShot Signal Validation**:
   - Lines 614-633: Extracts indicators assuming timeframe organization
   - Lines 619-623: Special handling for multi-timeframe indicators

## 3. Extraction System Issues

### Current Flow
1. **extraction/sources/crypto_indicators_mcp.py**:
   - Lines 58-141: Loops through symbols × timeframes
   - Lines 312-344: Stores one entry per symbol/timeframe combination
   - No config_id awareness

2. **Cross-Product Waste**:
   ```python
   # Current: Lines 98-140
   for symbol in symbols:
       for timeframe in timeframes:
           # Extract ALL indicators for each combination
   ```

3. **Storage Pattern**:
   - Lines 312-332: Creates separate entries for each timeframe
   - No aggregation of multi-timeframe data

## 4. API & Integration Points

### Breaking API Endpoints

1. **extraction/api.py**:
   - Lines 28-33: `ExtractionRequest` doesn't use config_id effectively
   - Lines 65-105: Webhook to decision API passes symbols/timeframes

2. **decision/api.py**:
   - Expects timeframes parameter
   - Passes timeframes to decision engine

3. **dashboard/api.py**:
   - Lines 126-141: Market data queries might need updates

## 5. Configuration System Gaps

### Current Issues
1. **No Config-to-Extraction Coupling**:
   - Configs define indicators but extraction ignores config_id
   - Cross-product extraction regardless of what config needs

2. **Indicator String Format**:
   - Current: `["RSI", "MACD", "BollingerBands"]`
   - Needed: `["RSI_1h", "RSI_4h", "MACD_1h"]`

## 6. MCP Metadata System

### Required Updates
1. **core/mcp/metadata/__init__.py**:
   - Need `parse_indicator_string()` function
   - Need `get_mcp_tool_name_from_string()` function
   - Current system can't handle "RSI_4h" format

## 7. Test Systems

### Affected Tests
- `tests/test_all_indicators_extraction.py`
- `tests/run_ggbot.py`
- `tests/test_webhook_chain.py`
- All assume current (symbol, timeframe) structure

## 8. Data Migration Challenges

### Existing Data
- All current market_data uses timeframe field meaningfully
- No way to retroactively assign config_id
- Decision engine relies on historical data structure

## 9. Hidden Dependencies

### Hardcoded Assumptions
1. **Multi-timeframe Indicators**:
   - Stored as "RSI_4h" within the signal timeframe data
   - Decision engine expects this exact format

2. **Timeframe Parameter**:
   - Used throughout the system even if becoming "mixed"
   - Database constraints require non-null timeframe

3. **Data Organization**:
   - Frontend might expect timeframe-based organization
   - Monitoring systems might query by timeframe

## 10. Risk Areas

### High Risk
1. **Data Loss**: Existing data becomes inaccessible
2. **Decision Failures**: Engine can't find indicators
3. **Extraction Loops**: Infinite extraction without proper config coupling

### Medium Risk
1. **API Compatibility**: Breaking changes for consumers
2. **Performance**: New indexes needed for (config_id, symbol)
3. **Migration Complexity**: Coordinating updates across services

### Low Risk
1. **Test Updates**: Straightforward but time-consuming
2. **Documentation**: Needs complete rewrite

## Recommended Approach

### Phase 1: Add Backwards Compatibility
1. Add nullable config_id to market_data
2. Update extraction to populate both patterns
3. Update decision to try config_id first, fall back to timeframe

### Phase 2: Gradual Migration
1. Update configs to use string indicators
2. Implement new extraction logic
3. Run parallel for validation

### Phase 3: Cutover
1. Switch decision to config_id lookups
2. Stop writing timeframe-based entries
3. Archive old data

### Phase 4: Cleanup
1. Remove timeframe dependencies
2. Update APIs to remove timeframe parameters
3. Make config_id required

## Critical Path Items

1. **Database Migration**: Add config_id column (nullable first)
2. **Metadata System**: Implement indicator string parsing
3. **Extraction Update**: Support string-based indicators
4. **Decision Update**: Support config_id lookups with fallback
5. **Storage Update**: Change constraint from (symbol, timeframe) to (config_id, symbol)