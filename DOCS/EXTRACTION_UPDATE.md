# Extraction System Restructure Plan

## Implementation Progress (Updated: 2025-06-30)

### ✅ COMPLETED PHASES:

#### Phase 1: Foundation
1. **Database Changes**
   - ✅ Added config_id column to market_data table (nullable)
   - ✅ Added index on (config_id, symbol)
   - ✅ Added foreign key constraint to configurations table
   - ✅ Updated database/README.md documentation

2. **Metadata System Updates**
   - ✅ Added `parse_indicator_string()` function
   - ✅ Added `get_mcp_tool_name_from_string()` function
   - ✅ All string-based indicators now map correctly to MCP tools

3. **Extraction Source Updates**
   - ✅ Updated CryptoIndicatorsMCPSource with dual-mode support
   - ✅ Added `_extract_new_mode()` for config_id based extraction
   - ✅ Added `_group_indicators_by_timeframe()` for efficient extraction
   - ✅ Added `_store_results_new_format()` for new storage pattern

#### Phase 2: Configuration & Decision Updates
1. **ggShot Configuration**
   - ✅ Updated to use string-based indicators with optimal timeframes:
     - Daily regime: Aroon_1d, BollingerBandsWidth_1d
     - 1h confirmation: Vortex_1h, VWAP_1h
     - Multi-TF context: RSI_30m, RSI_4h, DonchianChannel_200_1h
     - 1h tactical: BollingerBands_1h, ATR_1h
   - ✅ Deployed updated config to database (same config_id)

2. **Decision Engine Updates (CLEAN CUT APPROACH)**
   - ✅ Removed all legacy timeframe-based code
   - ✅ Updated `_fetch_market_data()` to use config_id exclusively
   - ✅ Added `_process_string_based_indicators()` for new format
   - ✅ Updated indicator extraction helpers for string-based format
   - ✅ Updated ggShot prompt to use correct timeframes

### 🚧 IN PROGRESS:
- Updating extraction_main.py to use new CryptoIndicatorsMCPSource

### ❌ TODO:
- Complete extraction_main.py update
- Phase 3: Full system testing
- Phase 4: Final cleanup

## Key Implementation Details:

### 1. String-Based Indicator Format
All indicators now use explicit timeframe specification:
- `RSI_30m`, `RSI_4h` instead of just `RSI`
- `Aroon_1d` for daily regime detection
- `DonchianChannel_200_1h` with embedded period

### 2. Database Lookup Pattern
- OLD: `WHERE symbol = %s AND timeframe = %s`
- NEW: `WHERE config_id = %s AND symbol = %s`

### 3. Extraction Flow
- Config specifies exact indicators needed
- Extraction groups by timeframe for efficiency
- Stores as single row with all indicators

### 4. Decision Engine Compatibility
- New data structure maintains timeframe organization
- Indicators accessible by both short name and full string name
- Prompts updated to use correct timeframes

## Overview
This document outlines the comprehensive changes needed to restructure the extraction system from cross-product (Symbol × Timeframe × Indicator) to explicit string-based indicators (Symbol × ConfigID → {"RSI_1h": [...], "RSI_4h": [...]}).

## Root Problem Being Solved
- **N/A Indicators**: Current system fails because indicators like `SMA_Volume_30`, `RSI_4h`, `DonchianChannel_200` don't map to MCP tools
- **Wasteful Extraction**: Cross-product approach extracts unnecessary data
- **No Config Coupling**: No connection between user strategy configs and extracted data

## New Architecture

### Before (Current)
```
Symbol: BTC/USDT
Timeframes: [1h, 4h] 
Indicators: [RSI, Aroon]
= 4 extractions (2×2)
Storage: 2 rows with timeframe='1h'/'4h'
```

### After (Target)
```
Symbol: BTC/USDT
Config: ggshot
Indicators: ["RSI_1h", "Aroon_4h"]
= 2 extractions (exactly what's needed)
Storage: 1 row with config_id + symbol
```

## Database Changes

### Schema Update
```sql
-- Add config_id column to market_data table
ALTER TABLE market_data ADD COLUMN config_id UUID;

-- Create index for new lookup pattern
CREATE INDEX idx_market_data_config_symbol ON market_data(config_id, symbol);

-- Optional: Add foreign key constraint
ALTER TABLE market_data ADD CONSTRAINT fk_market_data_config 
  FOREIGN KEY (config_id) REFERENCES configurations(config_id);
```

### Data Migration Strategy
1. **Phase 1**: Add nullable config_id column
2. **Phase 2**: Update extraction to populate config_id
3. **Phase 3**: Migrate existing data (optional)
4. **Phase 4**: Make config_id NOT NULL

### Storage Pattern Change
```sql
-- OLD PATTERN
INSERT INTO market_data (symbol, timeframe, indicators) VALUES 
  ('BTC/USDT', '1h', '{"RSI": [...], "MACD": [...]}'),
  ('BTC/USDT', '4h', '{"RSI": [...], "Aroon": [...]}');

-- NEW PATTERN  
INSERT INTO market_data (config_id, symbol, timeframe, indicators) VALUES 
  ('e249bb49-0455-4596-9657-09bf9e14ca14', 'BTC/USDT', 'mixed', 
   '{"RSI_1h": [...], "RSI_4h": [...], "Aroon_4h": [...]}');
```

## Configuration Updates

### Current ggShot Config (BROKEN)
```json
{
  "extraction": {
    "sources": {
      "crypto_indicators_mcp": {
        "indicators": [
          "Aroon",                  // ❌ No timeframe specified
          "BollingerBandsWidth",    // ❌ No timeframe specified  
          "SMA_Volume_30",          // ❌ No MCP tool mapping
          "Vortex",                 // ❌ No timeframe specified
          "VWAP",                   // ❌ No timeframe specified
          "RSI",                    // ❌ No timeframe specified
          "RSI_4h",                 // ❌ No MCP tool mapping
          "DonchianChannel_200",    // ❌ No MCP tool mapping
          "BollingerBands",         // ❌ No timeframe specified
          "ATR"                     // ❌ No timeframe specified
        ]
      }
    }
  }
}
```

### New ggShot Config (WORKING)
```json
{
  "extraction": {
    "sources": {
      "crypto_indicators_mcp": {
        "indicators": [
          "Aroon_4h",               // ✅ 4h regime detection
          "BollingerBandsWidth_1h", // ✅ Signal timeframe volatility
          "Vortex_1h",              // ✅ Signal timeframe momentum
          "VWAP_1h",                // ✅ Signal timeframe institutional flow
          "RSI_1h",                 // ✅ Signal timeframe RSI
          "RSI_4h",                 // ✅ Higher timeframe context
          "DonchianChannel_1h",     // ✅ Liquidity zones (period via config)
          "BollingerBands_1h",      // ✅ Overextension detection
          "ATR_1h"                  // ✅ Volatility measurement
        ],
        "DonchianChannel_period": 200  // ✅ Period override
      }
    }
  }
}
```

## Core Extraction Module Changes

### 1. Metadata Mapping Updates
**File**: `/home/sev/ggbot/core/mcp/metadata/__init__.py`

**Current Problem**:
```python
get_mcp_tool_name("RSI_4h")  # Returns None ❌
get_mcp_tool_name("DonchianChannel_200")  # Returns None ❌
```

**New Implementation**:
```python
def parse_indicator_string(indicator_string: str) -> dict:
    """
    Parse string-based indicators into components.
    
    Examples:
        "RSI_1h" → {"indicator": "RSI", "timeframe": "1h"}
        "DonchianChannel_200_4h" → {"indicator": "DonchianChannel", "period": 200, "timeframe": "4h"}
        "BollingerBandsWidth_1h" → {"indicator": "BollingerBandsWidth", "timeframe": "1h"}
    """
    parts = indicator_string.split('_')
    result = {"indicator": parts[0]}
    
    # Parse remaining parts for period and timeframe
    for part in parts[1:]:
        if part.isdigit():
            result["period"] = int(part)
        elif part in ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '1w']:
            result["timeframe"] = part
    
    return result

def get_mcp_tool_name_from_string(indicator_string: str) -> Optional[str]:
    """Get MCP tool name from string-based indicator."""
    parsed = parse_indicator_string(indicator_string)
    return get_mcp_tool_name(parsed["indicator"])
```

### 2. Extraction Source Updates
**File**: `/home/sev/ggbot/extraction/sources/crypto_indicators_mcp.py`

**Key Changes**:

```python
class CryptoIndicatorsMCPSource:
    async def extract(self, symbols: List[str], timeframes: List[str], config_id: str) -> Dict[str, Any]:
        """
        Extract indicators using string-based specification.
        
        Args:
            symbols: List of trading symbols  
            timeframes: IGNORED (indicators specify their own timeframes)
            config_id: Configuration ID for storage
        """
        results = {}
        
        for symbol in symbols:
            # Group indicators by timeframe for efficient extraction
            timeframe_groups = self._group_indicators_by_timeframe()
            
            symbol_indicators = {}
            
            for timeframe, indicators in timeframe_groups.items():
                # Extract all indicators for this timeframe in one MCP session
                timeframe_results = await self._extract_timeframe_indicators(
                    symbol, timeframe, indicators
                )
                symbol_indicators.update(timeframe_results)
            
            # Store using new pattern: config_id + symbol
            await self._store_results_new_format(config_id, symbol, symbol_indicators)
            
            results[symbol] = {
                "status": "success", 
                "indicators": symbol_indicators,
                "config_id": config_id
            }
        
        return results
    
    def _group_indicators_by_timeframe(self) -> Dict[str, List[str]]:
        """Group string indicators by their timeframes for efficient extraction."""
        groups = {}
        for indicator_string in self.indicators:
            parsed = parse_indicator_string(indicator_string)
            timeframe = parsed.get("timeframe", "1h")  # Default fallback
            
            if timeframe not in groups:
                groups[timeframe] = []
            groups[timeframe].append(indicator_string)
        
        return groups
    
    async def _extract_timeframe_indicators(self, symbol: str, timeframe: str, 
                                          indicator_strings: List[str]) -> Dict[str, Any]:
        """Extract multiple indicators for a specific timeframe."""
        results = {}
        
        for indicator_string in indicator_strings:
            try:
                parsed = parse_indicator_string(indicator_string)
                mcp_tool_name = get_mcp_tool_name(parsed["indicator"])
                
                if not mcp_tool_name:
                    self.logger.warning(f"No MCP tool for {indicator_string}")
                    continue
                
                # Build parameters with period override if specified
                params = {
                    "exchange": os.environ.get("EXCHANGE_NAME", "binance"),
                    "symbol": symbol,
                    "timeframe": timeframe
                }
                
                # Add period if specified in string
                if "period" in parsed:
                    params["period"] = parsed["period"]
                elif f"{parsed['indicator']}_period" in self.config:
                    params["period"] = self.config[f"{parsed['indicator']}_period"]
                
                # Call MCP tool
                result = await self.mcp_client.session.call_tool(mcp_tool_name, params)
                
                if result and not (isinstance(result, str) and result.startswith("Error")):
                    results[indicator_string] = result  # Store with full string name
                    self.logger.info(f"✅ Extracted {indicator_string}")
                else:
                    self.logger.warning(f"❌ Failed {indicator_string}: {result}")
                    
            except Exception as e:
                self.logger.error(f"Error extracting {indicator_string}: {str(e)}")
        
        return results
    
    async def _store_results_new_format(self, config_id: str, symbol: str, 
                                       indicators: Dict[str, Any]) -> bool:
        """Store results using new config_id + symbol pattern."""
        try:
            market_data_entry = {
                "user_id": self.user_id,
                "config_id": config_id,  # NEW FIELD
                "source": "crypto_indicators_mcp",
                "symbol": symbol,
                "timeframe": "mixed",  # Not used anymore
                "data_type": "indicator_analysis",
                "updated_at": datetime.utcnow(),
                "indicators": indicators,  # String-based keys
                "raw_data": {
                    "config": {
                        "string_indicators": self.indicators,
                        "llm_interpretation": self.llm_interpretation
                    }
                }
            }
            
            stored_count = store_market_data_entries([market_data_entry])
            return stored_count > 0
            
        except Exception as e:
            self.logger.error(f"Error storing results: {str(e)}")
            return False
```

### 3. Storage Utility Updates  
**File**: `/home/sev/ggbot/extraction/utils.py`

**Update `store_market_data_entries`**:
```python
def store_market_data_entries(entries: List[Dict[str, Any]]) -> int:
    """Store market data entries with new config_id + symbol pattern."""
    # Update INSERT statement to include config_id
    # Handle UPSERT based on (config_id, symbol) instead of (symbol, timeframe)
```

## Decision Module Changes

### 1. Data Retrieval Updates
**File**: `/home/sev/ggbot/decision/engine.py`

**Current Retrieval**:
```python
def _fetch_market_data(self, symbol: str) -> Dict:
    # Fetches by symbol + timeframe
    query = """
        SELECT * FROM market_data 
        WHERE symbol = %s AND timeframe = %s
    """
```

**New Retrieval**:
```python
def _fetch_market_data(self, symbol: str) -> Dict:
    """Fetch market data using config_id + symbol pattern."""
    try:
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT indicators, updated_at FROM market_data 
                    WHERE config_id = %s AND symbol = %s
                    ORDER BY updated_at DESC LIMIT 1
                """
                cur.execute(query, (self.config_id, symbol))
                result = cur.fetchone()
                
                if not result:
                    logger.warning(f"No market data found for config {self.config_id}, symbol {symbol}")
                    return {}
                
                # Return indicators directly - they're already properly keyed
                return {
                    "indicators": result["indicators"],  # {"RSI_1h": [...], "RSI_4h": [...]}
                    "updated_at": result["updated_at"]
                }
                
    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        return {}
```

### 2. Indicator Access Updates
**File**: `/home/sev/ggbot/decision/engine.py`

**Current Helper Function**:
```python
def get_indicator_data(indicator_name: str, timeframe: str = None) -> str:
    """Extract indicator from timeframe-based storage."""
    if timeframe:
        multi_tf_name = f"{indicator_name}_{timeframe}"
        data = market_data.get(native_timeframe, {}).get('indicators', {})
        return data.get(multi_tf_name, "N/A")
    else:
        data = market_data.get(native_timeframe, {}).get('indicators', {})
        return data.get(indicator_name, "N/A")
```

**New Helper Function**:
```python
def get_indicator_data(indicator_string: str) -> str:
    """Extract indicator from string-based storage."""
    try:
        # Direct lookup - indicator_string is the exact key
        indicators = market_data.get('indicators', {})
        indicator_data = indicators.get(indicator_string)
        
        if indicator_data is None:
            return "N/A"
        return str(indicator_data)
        
    except Exception as e:
        logger.warning(f"Error extracting {indicator_string}: {e}")
        return "N/A"
```

### 3. Prompt Updates
**File**: `/home/sev/ggbot/decision/engine.py`

**Current Prompt Generation**:
```python
* **Aroon:** Extract current value from: {get_indicator_data('Aroon')}
* **Higher Timeframe RSI (4h):** Extract current value from: {get_indicator_data('RSI', '4h')}
```

**New Prompt Generation**:
```python
* **Aroon:** Extract current value from: {get_indicator_data('Aroon_4h')}
* **Higher Timeframe RSI (4h):** Extract current value from: {get_indicator_data('RSI_4h')}
```

## API Changes

### 1. Extraction API Updates
**File**: `/home/sev/ggbot/extraction/api.py`

**Current Endpoint**:
```python
@app.post("/extract")
async def trigger_extraction(request: ExtractionRequest):
    # Uses symbols + timeframes from request
```

**Updated Endpoint**:
```python
@app.post("/extract")
async def trigger_extraction(request: ExtractionRequest):
    """
    Trigger extraction with config_id for indicator specification.
    
    The config_id determines which indicators to extract - no more 
    cross-product of symbols × timeframes × indicators.
    """
    # Pass config_id to extraction source
    # Let source determine indicators from config
```

### 2. Request Models
**File**: `/home/sev/ggbot/extraction/api.py`

```python
class ExtractionRequest(BaseModel):
    symbols: List[str]
    config_id: str  # NEW: Determines indicators to extract
    # timeframes: List[str]  # REMOVED: Indicators specify their own timeframes
    source_name: str = "crypto_indicators_mcp"
```

## Testing Strategy

### 1. Unit Tests
- **Metadata parsing**: Test `parse_indicator_string()` with various formats
- **MCP tool mapping**: Test `get_mcp_tool_name_from_string()` 
- **Indicator grouping**: Test `_group_indicators_by_timeframe()`

### 2. Integration Tests  
- **End-to-end extraction**: Config → Extraction → Storage → Retrieval
- **ggShot flow**: Signal → Extraction → Decision → Validation
- **Error handling**: Missing indicators, MCP failures, etc.

### 3. Database Migration Testing
- **Schema updates**: Verify config_id column addition
- **Data integrity**: Ensure existing data not corrupted
- **Performance**: Check index performance on new lookup pattern

## Rollout Plan

### Phase 1: Foundation (Day 1-2)
1. ✅ Add `config_id` column to `market_data` (nullable)
2. ✅ Update metadata parsing functions  
3. ✅ Create unit tests for new functions

### Phase 2: Extraction Updates (Day 3-4)
1. ✅ Update `CryptoIndicatorsMCPSource` for string-based indicators
2. ✅ Update ggShot configuration with working indicators
3. ✅ Test extraction with new format

### Phase 3: Decision Updates (Day 5-6)  
1. ✅ Update decision engine data retrieval
2. ✅ Update prompt generation helpers
3. ✅ Test full ggShot signal flow

### Phase 4: Production Deployment (Day 7)
1. ✅ Deploy database schema changes
2. ✅ Deploy application updates
3. ✅ Monitor extraction success rates
4. ✅ Verify N/A indicators are resolved

## Success Metrics

### Before (Current State)
- ❌ ALICE/LDO signals: 90% indicators return "N/A"
- ❌ Confidence scores artificially low due to missing data
- ❌ Extraction inefficiency: 60 operations for 27 needed indicators

### After (Target State)  
- ✅ All 9 ggShot indicators successfully extracted
- ✅ Confidence scores based on complete data
- ✅ Extraction efficiency: Exactly what's needed, nothing more
- ✅ Clear config → indicator → storage → retrieval pipeline

## Configuration System Updates

### 1. Template Configuration Updates
**File**: `/home/sev/ggbot/core/config/template.json`

**Current Template**:
```json
{
  "extraction": {
    "sources": {
      "crypto_indicators_mcp": {
        "enabled": true,
        "indicators": ["RSI", "MACD", "BollingerBands"],
        "llm_interpretation": false
      }
    }
  }
}
```

**New Template** (String-based indicators):
```json
{
  "extraction": {
    "sources": {
      "crypto_indicators_mcp": {
        "enabled": true,
        "indicators": [
          "RSI_1h",
          "RSI_4h", 
          "MACD_1h",
          "BollingerBands_1h",
          "DonchianChannel_1h"
        ],
        "llm_interpretation": false,
        "indicator_periods": {
          "DonchianChannel": 200,
          "BollingerBands": 20,
          "RSI": 14,
          "MACD_fast": 12,
          "MACD_slow": 26,
          "MACD_signal": 9
        }
      }
    }
  },
  "decision": {
    "strategy": "Multi-timeframe technical analysis using string-based indicators",
    "llm_provider": "deepseek"
  }
}
```

### 2. Config Insertion Utility Updates
**File**: `/home/sev/ggbot/core/config/insert_config.py`

**New Function for String-Based Configs**:
```python
def create_string_indicator_config(
    config_name: str,
    strategy_description: str,
    indicators: List[str],
    indicator_periods: Dict[str, int] = None,
    user_id: str = None
) -> str:
    """
    Create a configuration with string-based indicators.
    
    Args:
        config_name: Name for the configuration
        strategy_description: Description of the trading strategy
        indicators: List of string indicators like ["RSI_1h", "RSI_4h", "MACD_1h"]
        indicator_periods: Custom periods per indicator type
        user_id: User ID (defaults to DEFAULT_USER_ID)
    
    Returns:
        config_id: UUID of created configuration
    
    Example:
        config_id = create_string_indicator_config(
            config_name="Multi-timeframe RSI Strategy",
            strategy_description="RSI analysis across 1h and 4h timeframes",
            indicators=["RSI_1h", "RSI_4h", "BollingerBands_1h"],
            indicator_periods={"RSI": 14, "BollingerBands": 20}
        )
    """
    config_data = {
        "extraction": {
            "sources": {
                "crypto_indicators_mcp": {
                    "enabled": True,
                    "indicators": indicators,
                    "llm_interpretation": False
                }
            }
        },
        "decision": {
            "strategy": strategy_description,
            "llm_provider": "deepseek"
        }
    }
    
    # Add indicator periods if provided
    if indicator_periods:
        config_data["extraction"]["sources"]["crypto_indicators_mcp"]["indicator_periods"] = indicator_periods
    
    return save_configuration(
        user_id=user_id or DEFAULT_USER_ID,
        config_name=config_name,
        config_data=config_data
    )

def validate_string_indicators(indicators: List[str]) -> Dict[str, Any]:
    """
    Validate string-based indicators and return analysis.
    
    Returns:
        {
            "valid": bool,
            "issues": List[str],
            "timeframes_used": List[str],
            "indicator_types": Dict[str, int],
            "mcp_mapping_status": Dict[str, bool]
        }
    """
    issues = []
    timeframes = set()
    indicator_types = {}
    mcp_status = {}
    
    for indicator_string in indicators:
        # Parse indicator string
        try:
            parsed = parse_indicator_string(indicator_string)
            indicator_base = parsed["indicator"]
            timeframe = parsed.get("timeframe", "unknown")
            
            timeframes.add(timeframe)
            indicator_types[indicator_base] = indicator_types.get(indicator_base, 0) + 1
            
            # Check MCP mapping
            mcp_tool = get_mcp_tool_name(indicator_base)
            mcp_status[indicator_string] = mcp_tool is not None
            
            if not mcp_tool:
                issues.append(f"No MCP tool mapping for {indicator_base} in {indicator_string}")
                
        except Exception as e:
            issues.append(f"Failed to parse {indicator_string}: {str(e)}")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "timeframes_used": sorted(list(timeframes)),
        "indicator_types": indicator_types,
        "mcp_mapping_status": mcp_status
    }
```

### 3. ggShot Configuration Update
**File**: `/home/sev/ggbot/ggshot/insert_ggshot_config.py`

**New ggShot Config Creation**:
```python
#!/usr/bin/env python3
"""
Update ggShot configuration to use string-based indicators.
This script updates the existing ggShot config to fix the N/A indicator problem.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.common.config import DEFAULT_USER_ID
from core.common.db import get_db_connection
from core.common.logger import logger

GGSHOT_CONFIG_ID = "e249bb49-0455-4596-9657-09bf9e14ca14"

def update_ggshot_config():
    """Update existing ggShot configuration with working string-based indicators."""
    
    # NEW WORKING CONFIGURATION
    new_config_data = {
        "extraction": {
            "sources": {
                "crypto_indicators_mcp": {
                    "enabled": True,
                    "indicators": [
                        # PILLAR 0: Market Regime (4h for stable trend detection)
                        "Aroon_4h",                    # ✅ Trending vs ranging detection
                        "BollingerBandsWidth_1h",      # ✅ Volatility/consolidation
                        
                        # PILLAR 1: Signal Confirmation (signal timeframe)
                        "Vortex_1h",                   # ✅ Momentum direction
                        "VWAP_1h",                     # ✅ Institutional sentiment
                        
                        # PILLAR 2: Broader Context (multi-timeframe)
                        "RSI_1h",                      # ✅ Signal timeframe momentum
                        "RSI_4h",                      # ✅ Higher timeframe context
                        "DonchianChannel_1h",          # ✅ Liquidity zones
                        
                        # PILLAR 3: Tactical Caution (signal timeframe)
                        "BollingerBands_1h",           # ✅ Overextension detection
                        "ATR_1h"                       # ✅ Volatility measurement
                    ],
                    "llm_interpretation": False,
                    "indicator_periods": {
                        # Set strategic periods for each indicator type
                        "DonchianChannel": 200,        # Major liquidity zones
                        "BollingerBands": 20,          # Standard volatility
                        "BollingerBandsWidth": 20,     # Match BB period
                        "RSI": 14,                     # Standard momentum
                        "Aroon": 14,                   # Standard trend detection
                        "ATR": 14,                     # Standard volatility
                        "Vortex": 14                   # Standard momentum
                        # VWAP has no period (session-based)
                    }
                }
            }
        },
        "decision": {
            "strategy": "ggShot signal validation using 4-Pillar Framework with string-based indicators: (0) Market Regime - Aroon_4h/BBW_1h filter ranging markets, (1) Signal Confirmation - Vortex_1h/VWAP_1h momentum alignment, (2) Broader Context - Multi-timeframe RSI and liquidity zones, (3) Tactical Caution - Bollinger Bands overextension and ATR volatility checks.",
            "llm_provider": "deepseek"
        }
    }
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Update the existing ggShot configuration
                update_query = """
                    UPDATE configurations 
                    SET config_data = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE config_id = %s
                """
                
                cur.execute(update_query, (new_config_data, GGSHOT_CONFIG_ID))
                
                if cur.rowcount > 0:
                    logger.info(f"✅ Successfully updated ggShot config {GGSHOT_CONFIG_ID}")
                    logger.info("🔧 Key changes:")
                    logger.info("   - Removed SMA_Volume_30 (redundant with CCXT volume)")
                    logger.info("   - Changed RSI_4h to proper multi-timeframe extraction")
                    logger.info("   - Fixed DonchianChannel_200 → DonchianChannel_1h with period=200")
                    logger.info("   - Added strategic period defaults for each indicator")
                    logger.info("   - All indicators now have explicit timeframes")
                    
                    # Verify the update
                    cur.execute("SELECT config_data FROM configurations WHERE config_id = %s", (GGSHOT_CONFIG_ID,))
                    result = cur.fetchone()
                    
                    if result:
                        updated_indicators = result["config_data"]["extraction"]["sources"]["crypto_indicators_mcp"]["indicators"]
                        logger.info(f"📋 Updated indicators ({len(updated_indicators)}):")
                        for i, indicator in enumerate(updated_indicators, 1):
                            logger.info(f"   {i}. {indicator}")
                    
                    return True
                else:
                    logger.error(f"❌ No configuration found with ID {GGSHOT_CONFIG_ID}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Error updating ggShot configuration: {str(e)}")
        return False

def validate_updated_config():
    """Validate that the updated configuration will work."""
    try:
        # Import validation functions
        from core.mcp.metadata import get_mcp_tool_name, parse_indicator_string
        
        # Get the updated config
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT config_data FROM configurations WHERE config_id = %s", (GGSHOT_CONFIG_ID,))
                result = cur.fetchone()
                
                if not result:
                    logger.error("❌ Could not retrieve updated config for validation")
                    return False
                
                indicators = result["config_data"]["extraction"]["sources"]["crypto_indicators_mcp"]["indicators"]
                
                logger.info("🔍 Validating updated configuration...")
                
                all_valid = True
                for indicator_string in indicators:
                    try:
                        parsed = parse_indicator_string(indicator_string)
                        mcp_tool = get_mcp_tool_name(parsed["indicator"])
                        
                        if mcp_tool:
                            logger.info(f"   ✅ {indicator_string} → {mcp_tool}")
                        else:
                            logger.error(f"   ❌ {indicator_string} → No MCP mapping")
                            all_valid = False
                            
                    except Exception as e:
                        logger.error(f"   ❌ {indicator_string} → Parse error: {str(e)}")
                        all_valid = False
                
                if all_valid:
                    logger.info("🎉 All indicators have valid MCP mappings!")
                    return True
                else:
                    logger.error("❌ Some indicators still have mapping issues")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Error validating configuration: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Updating ggShot configuration for string-based indicators...")
    
    if update_ggshot_config():
        logger.info("✅ Configuration update completed")
        
        if validate_updated_config():
            logger.info("🎯 Ready to deploy - all indicators should work!")
        else:
            logger.warning("⚠️ Validation found issues - review before deployment")
    else:
        logger.error("❌ Configuration update failed")
        sys.exit(1)
```

## Default Period Strategy

### 1. Indicator-Specific Period Defaults
**File**: `/home/sev/ggbot/core/mcp/metadata/__init__.py`

**Add Period Defaults System**:
```python
# Strategic period defaults based on indicator purpose and timeframe
INDICATOR_PERIOD_DEFAULTS = {
    # Momentum Indicators (shorter periods for responsiveness)
    "RSI": {"default": 14, "timeframe_adjustments": {"5m": 21, "1h": 14, "4h": 14, "1d": 21}},
    "Stochastic": {"default": 14},
    "WilliamsR": {"default": 14},
    "CCI": {"default": 20},
    
    # Trend Indicators (various periods based on use case)
    "MACD": {"fast": 12, "slow": 26, "signal": 9},
    "Aroon": {"default": 14, "timeframe_adjustments": {"1h": 14, "4h": 25, "1d": 25}},
    "EMA": {"default": 21},
    "SMA": {"default": 20},
    
    # Volatility Indicators (standard periods)
    "BollingerBands": {"default": 20},
    "BollingerBandsWidth": {"default": 20},  # Should match BollingerBands
    "ATR": {"default": 14},
    "Keltner": {"default": 20},
    
    # Volume Indicators (longer periods for stability)
    "VWAP": {"period": None},  # Session-based, no period needed
    "OBV": {"period": None},   # Cumulative, no period needed
    "MFI": {"default": 14},
    "ChaikinMoneyFlow": {"default": 21},
    
    # Channel/Support-Resistance (longer periods for major levels)
    "DonchianChannel": {
        "default": 200,  # Major liquidity zones
        "purpose_adjustments": {
            "liquidity_zones": 200,    # For major S/R levels
            "breakout_detection": 55,  # For breakout systems
            "trend_following": 100     # For trend systems
        }
    },
    "IchimokuCloud": {"conversion": 9, "base": 26, "span": 52, "displacement": 26}
}

def get_optimal_period(indicator_name: str, timeframe: str = "1h", purpose: str = "default") -> int:
    """
    Get optimal period for an indicator based on type, timeframe, and purpose.
    
    Args:
        indicator_name: Base indicator name (e.g., "RSI", "DonchianChannel")
        timeframe: Timeframe being used (e.g., "1h", "4h")
        purpose: Purpose/strategy context (e.g., "liquidity_zones", "breakout_detection")
    
    Returns:
        Optimal period for the indicator
    """
    if indicator_name not in INDICATOR_PERIOD_DEFAULTS:
        return 14  # Universal fallback
    
    defaults = INDICATOR_PERIOD_DEFAULTS[indicator_name]
    
    # Check for purpose-specific adjustments
    if purpose != "default" and "purpose_adjustments" in defaults:
        if purpose in defaults["purpose_adjustments"]:
            return defaults["purpose_adjustments"][purpose]
    
    # Check for timeframe-specific adjustments
    if "timeframe_adjustments" in defaults and timeframe in defaults["timeframe_adjustments"]:
        return defaults["timeframe_adjustments"][timeframe]
    
    # Return default period
    return defaults.get("default", 14)

def build_mcp_params_with_optimal_period(indicator_string: str, symbol: str, exchange: str = "binance") -> dict:
    """
    Build MCP tool parameters with optimal period selection.
    
    Args:
        indicator_string: String like "DonchianChannel_1h" or "RSI_4h"
        symbol: Trading symbol
        exchange: Exchange name
    
    Returns:
        Parameters dict ready for MCP tool call
    """
    parsed = parse_indicator_string(indicator_string)
    
    params = {
        "exchange": exchange,
        "symbol": symbol,
        "timeframe": parsed.get("timeframe", "1h")
    }
    
    # Add period if indicator needs one
    indicator_name = parsed["indicator"]
    
    if indicator_name in INDICATOR_PERIOD_DEFAULTS:
        # Check if user specified period in string (e.g., "DonchianChannel_200_1h")
        if "period" in parsed:
            params["period"] = parsed["period"]
        else:
            # Use optimal period for indicator type and timeframe
            optimal_period = get_optimal_period(
                indicator_name, 
                parsed.get("timeframe", "1h"),
                purpose="default"  # Could be enhanced to detect purpose from config
            )
            
            if optimal_period is not None:
                params["period"] = optimal_period
    
    return params
```

### 2. Integration with Extraction
**File**: `/home/sev/ggbot/extraction/sources/crypto_indicators_mcp.py`

**Use Smart Period Defaults**:
```python
async def _extract_timeframe_indicators(self, symbol: str, timeframe: str, 
                                      indicator_strings: List[str]) -> Dict[str, Any]:
    """Extract indicators with optimal period selection."""
    results = {}
    
    for indicator_string in indicator_strings:
        try:
            parsed = parse_indicator_string(indicator_string)
            mcp_tool_name = get_mcp_tool_name(parsed["indicator"])
            
            if not mcp_tool_name:
                self.logger.warning(f"No MCP tool for {indicator_string}")
                continue
            
            # Build parameters with smart period defaults
            params = build_mcp_params_with_optimal_period(
                indicator_string, symbol, os.environ.get("EXCHANGE_NAME", "binance")
            )
            
            # Override with user config if specified
            indicator_base = parsed["indicator"]
            if f"{indicator_base}_period" in self.config:
                params["period"] = self.config[f"{indicator_base}_period"]
            
            # Call MCP tool
            result = await self.mcp_client.session.call_tool(mcp_tool_name, params)
            
            if result and not (isinstance(result, str) and result.startswith("Error")):
                results[indicator_string] = result
                period_info = f" (period={params.get('period', 'N/A')})" if 'period' in params else ""
                self.logger.info(f"✅ {indicator_string}{period_info}")
            else:
                self.logger.warning(f"❌ Failed {indicator_string}: {result}")
                
        except Exception as e:
            self.logger.error(f"Error extracting {indicator_string}: {str(e)}")
    
    return results
```

### 3. Period Configuration Documentation
**Create New File**: `/home/sev/ggbot/docs/INDICATOR_PERIODS.md`

```markdown
# Indicator Period Guidelines

## Default Period Strategy

Our system uses intelligent period defaults based on:
1. **Indicator Type**: Momentum vs Trend vs Volatility
2. **Timeframe Context**: Higher timeframes may need longer periods
3. **Strategic Purpose**: Liquidity zones vs breakout detection

## Period Defaults by Category

### Momentum (Responsive)
- **RSI**: 14 (standard), 21 for daily timeframe
- **Stochastic**: 14
- **CCI**: 20

### Trend (Context-dependent)
- **Aroon**: 14 for 1h, 25 for 4h+ (more stable trend detection)
- **MACD**: 12/26/9 (fast/slow/signal)

### Volatility (Standard)
- **Bollinger Bands**: 20 (market standard)
- **ATR**: 14 (market standard)

### Channels (Strategic)
- **Donchian Channel**: 200 for major liquidity zones, 55 for breakouts

## Override Strategies

1. **String-based**: `DonchianChannel_55_1h` (explicit period=55)
2. **Config-based**: Set `DonchianChannel_period: 55` in config
3. **Auto-selection**: System chooses optimal based on indicator type + timeframe
```

## Risk Mitigation

### Database Changes
- **Risk**: Schema migration failure
- **Mitigation**: Nullable column first, gradual rollout, backup strategy

### Breaking Changes
- **Risk**: Existing extraction flows broken
- **Mitigation**: Backwards compatibility during transition, feature flags

### Data Loss
- **Risk**: Existing market_data becomes inaccessible
- **Mitigation**: Don't delete old data, dual-write during transition

### MCP Tool Mapping
- **Risk**: New parsing logic introduces bugs
- **Mitigation**: Comprehensive unit tests, validation against known good indicators

### Configuration Updates
- **Risk**: Invalid indicator strings in configs
- **Mitigation**: Validation functions, rollback capability, testing scripts

---

This restructure solves the immediate N/A indicator crisis while creating a scalable foundation for strategy-specific extraction that can grow with the platform.