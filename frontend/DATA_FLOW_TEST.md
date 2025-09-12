# Dashboard V2 Data Flow Test

## Data Pipeline Verification

### Backend → WebSocket → Frontend Flow

#### 1. Backend (Monitoring Service)
**File:** `/home/sev/ggbot/core/monitoring/service.py`

**Metrics Payload Example:**
```python
{
    "balance": 10000.00,
    "totalPnL": 150.25,
    "totalTrades": 12,
    "winRate": 0.75,  # 75%
    "avgTrade": 12.52,
    
    # NEW Enhanced Fields
    "winTrades": 9,
    "lossTrades": 2,
    "neutralTrades": 1,
    "lossRate": 0.167,  # 16.7%
    "neutralRate": 0.083,  # 8.3%
    "avgProfitPerTrade": 5.2,  # %
    "avgLossPerTrade": -3.1,  # %
    "avgTradeDuration": "2h15m",
    "profitLossData": [
        {"date": "2024-01-01", "profit": 100.0},
        {"date": "2024-01-02", "profit": 125.5},
        {"date": "2024-01-03", "profit": 150.25}
    ]
}
```

**Position Payload Example:**
```python
{
    "id": "trade-uuid-123",
    "symbol": "BTC/USDT", 
    "side": "LONG",
    "size": 1000.0,
    "entryPrice": 45000.0,
    "currentPrice": 45500.0,
    "unrealizedPnL": 11.11,
    "timestamp": "2024-01-03T10:30:00Z",
    
    # NEW Enhanced Fields
    "timeInTrade": "2h15m",
    "confidence": 85.0,  # percentage
    "reasoning_text": "Strong bullish momentum confirmed...",
    "signal_timeframe": "5m",
    "volume_analysis": "Volume spike confirms breakout",
    "stopLoss": 44000.0,
    "takeProfit": 47000.0
}
```

#### 2. WebSocket Messages
**Message Types:**
- `position_update`: Updates live positions with P&L
- `metrics_update`: Updates account/performance metrics
- `decisions_update`: Updates recent AI decisions

#### 3. Frontend Store (`botStore.ts`)
**Transformations:** Snake_case → camelCase, field mapping, fallbacks

#### 4. React Hooks
**Files:**
- `useBotMetrics.ts`: Enhanced with all new fields + fallbacks
- `useBotActivity.ts`: Position interface updated with enhanced fields

#### 5. UI Components
**PerformancePanel.tsx:** 
- ✅ Uses `winTrades`, `lossTrades`, `neutralTrades`
- ✅ Uses `avgProfitPerTrade`, `avgLossPerTrade`
- ✅ Uses `avgTradeDuration`
- ✅ Uses `profitLossData` for Recharts

**ActivityPanel.tsx:**
- ✅ Uses `position.id` for unique keys
- ✅ Uses `position.timeInTrade` for duration display
- ✅ Uses `position.confidence` for AI analysis
- ✅ Uses `position.reasoning_text` for expandable reasoning
- ✅ Uses `signal_timeframe`, `volume_analysis` for context

## Test Checklist

### Backend Tests
- [ ] Run monitoring service in isolation
- [ ] Verify enhanced metrics calculation
- [ ] Verify position data with decision joins
- [ ] Check P&L series generation

### Frontend Tests  
- [ ] Check WebSocket message handling
- [ ] Verify data transformation in botStore
- [ ] Test hooks with mock data
- [ ] Test component rendering with enhanced data

### Integration Tests
- [ ] End-to-end: Backend → WebSocket → Frontend
- [ ] Verify real-time updates work
- [ ] Test fallback behavior with missing data
- [ ] Test with multiple bots/positions

## Expected Behaviors

1. **No Data State**: Empty charts show "No trading history yet" 
2. **Partial Data**: Components gracefully handle missing enhanced fields
3. **Real-time Updates**: Position P&L updates every 7 seconds via WebSocket
4. **Chart Data**: Historical P&L chart shows cumulative profit/loss over time
5. **AI Reasoning**: Expandable position rows show decision confidence + reasoning

## Verification Commands

```bash
# Check backend data structure
python -c "
from core.monitoring.service import MonitoringService
# ... test metrics calculation
"

# Check WebSocket messages
# Connect to WebSocket and observe message payloads

# Check frontend data flow
# Open browser dev tools, monitor store updates
```

## Data Structure Alignment

✅ **Backend** → Enhanced monitoring service with all fields
✅ **WebSocket** → Proper message routing and payload structure  
✅ **Store** → Field transformation and fallback handling
✅ **Hooks** → Updated interfaces with enhanced fields
✅ **Components** → Using correct field names with null checks

**Status: IMPLEMENTATION COMPLETE - READY FOR TESTING**