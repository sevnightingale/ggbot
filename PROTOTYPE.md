# GGBot Autonomous Prototype Implementation Plan

## Overview

This document serves as a comprehensive roadmap for completing the GGBot autonomous trading prototype. The infrastructure testing is complete and successful - we've validated the entire pipeline from extraction through trade execution. Now we need to add the orchestration layer to enable 24/7 autonomous operation.

## Current State Assessment

### What's Complete
- **Full API Infrastructure**: All module APIs (Extraction, Decision, Trading, Dashboard, Agent Control) are implemented and tested
- **Database Architecture**: Universal Trade Lifecycle system with position tracking, TP/SL monitoring, and strategy metadata
- **Module Integration**: MCP connections, LLM decision making, exchange adapters all working
- **Successful E2E Test**: Successfully executed a 10,000 contract trade on BitMEX testnet via new_trade.py
  - Trade executed with proper entry price ($105,405.90), TP ($108,000), and SL ($103,000)
  - Position currently open and profitable (+$1.78 BTC unrealized P&L)
  - Database perfectly synchronized with exchange reality
  - TP/SL orders active and being monitored

### What's Needed
- **Webhook Chain**: Connect modules to trigger automatically
- **Scheduling System**: Enable 24/7 autonomous operation
- **Configuration Management**: API/UI for managing multiple strategies
- **Dashboard Interface**: Visual monitoring and control
- **Production Deployment**: Consolidated deployment strategy

### Known Issues to Address
- **Position Sizing Calibration**: Current system shows position sizes in contracts but actual USD value differs from expectations
  - 10,000 BTC/USDT:USDT contracts = ~$1,057 USD (not $10,000 as LLM assumes)
  - Need to calibrate position sizing logic to match exchange contract specifications
  - Priority: Medium (system works safely but position sizes are smaller than intended)

## Architecture Overview

### Autonomous Operation Flow
```
APScheduler (15m) → Extraction → Webhook → Decision → Webhook → Trading
                                                                    ↓
APScheduler (30s) ← Monitoring ← Database ← Trade Execution ←─────┘
```

### Key Design Principles
- **Event-Driven**: Webhooks chain modules together automatically
- **APScheduler Integration**: Python-native scheduling within the application
- **Single Process**: All components run in one unified service
- **Real-Time Updates**: WebSocket connections for live dashboard updates
- **Configuration-Driven**: Multiple strategies running in parallel

## Implementation Roadmap

### Phase 1: Webhook Infrastructure ✅ **COMPLETE**

#### Objective
Enable automatic module chaining through simple HTTP webhooks

#### Implementation Status: **✅ FULLY IMPLEMENTED AND TESTED**

**1.1 Add Webhook Endpoints to Each Module** ✅
- Extraction Module: `/webhooks/trigger-extraction` endpoint ✅
- Decision Module: `/webhooks/trigger-decision` endpoint ✅
- Trading Module: `/webhooks/execute-trade` endpoint ✅
- Standard payload with user_id, config_id, symbols, timeframes ✅
- Immediate response with extraction_id/decision_id/trade_id ✅

**1.2 Implement Webhook Calling Logic** ✅
- Extraction completion (90-second delay) → Decision webhook ✅
- Decision completion (actionable intent) → Trading webhook ✅
- Async HTTP client with 60-120 second timeouts ✅
- Comprehensive error handling and logging ✅

**1.3 Configure Webhook URLs** ✅
- Environment variables for service discovery ✅
- Default localhost URLs for development ✅
- Production-ready URL configuration ✅

#### **Key Implementation Details:**
- **90-Second Delay**: Extraction waits 90 seconds for all indicators to complete before triggering decision
- **Fresh Account State**: Each webhook refreshes exchange data for accurate decision-making
- **Auto-Mode Detection**: Decision automatically detects NEW_TRADE vs MANAGE_TRADE based on active positions
- **Comprehensive Verification**: Trading webhook includes full exchange sync and audit trail validation
- **Symbol Consistency**: BTC/USDT passed through entire chain for data compatibility

#### **Test Results:**
- **Successful E2E Test**: Complete autonomous pipeline validated on BitMEX testnet
- **Timing**: 2.5-minute full pipeline execution (90s extraction + 1.5min decision/trading)
- **Trade Execution**: Proper SHORT position based on RSI > 50 strategy rule
- **Audit Trail**: Complete strategy_runs verification and database sync
- **Risk Management**: Confidence-based position sizing and TP/SL placement

### Phase 2: APScheduler Integration ✅ **COMPLETE**

#### Objective
Replace manual triggering with automated scheduling system for single-config autonomous operation

#### Implementation Status: **✅ FULLY IMPLEMENTED AND TESTED**

**2.1 Create Scheduling Service** ✅
- Scheduler service: `core/scheduling/scheduler.py`
- APScheduler with AsyncIO scheduler integrated into main_api.py
- Memory-based job store for prototype simplicity

**2.2 Define Single-Config Schedule Job** ✅
- Extraction job: Runs every 15 minutes, triggers default config webhook chain
- Uses same proven webhook flow: Extraction → Decision → Trading
- Monitoring continues via existing AccountMonitoringService (every 30s)

**2.3 Frontend-Controlled Job Management** ✅
- Start/stop autonomous mode via Agent Control API endpoints
- `/agent/scheduler/start` - Begin autonomous trading
- `/agent/scheduler/stop` - Stop autonomous trading  
- `/agent/scheduler/status` - Check current scheduler state
- API server stays running when scheduler stops

**2.4 Integration with Main API** ✅
- Scheduler initialized within main_api.py but starts in stopped state
- Frontend controls autonomous mode independently of API server
- Graceful shutdown handling preserves API availability
- Single config approach for prototype simplicity

#### **Key Implementation Details:**
- **Single Config Focus**: Uses existing default config (a93de31b-9b8a-42e3-827d-c31e580f5f36)
- **Proven Webhook Chain**: Same 90s extraction + decision + trading flow validated in Phase 1
- **Frontend Control**: Autonomous trading can be started/stopped without affecting API
- **Simplified Architecture**: No multi-config complexity, focus on getting autonomous operation working

#### **Test Results:**
- **Autonomous Operation**: 15-minute scheduled extraction triggers complete pipeline
- **Frontend Control**: Start/stop functionality working via Agent Control API
- **Resource Management**: API server independent of scheduler state
- **Integration**: Seamless with existing webhook infrastructure


### Phase 3: Configuration Management System

#### Objective
Enable multiple trading strategies to run in parallel

#### Implementation Steps

**3.1 Configuration API Endpoints**
- GET `/api/configs/list` - List all configurations
- POST `/api/configs/create` - Create new configuration
- PUT `/api/configs/{id}/update` - Update configuration
- POST `/api/configs/{id}/toggle` - Enable/disable configuration
- DELETE `/api/configs/{id}` - Delete configuration

**3.2 Configuration Templates**
- Pre-built strategy templates (conservative, aggressive, scalping)
- Indicator selection presets
- Risk management profiles

**3.3 Configuration Validation**
- Validate all required fields present
- Check risk parameters are within safe limits
- Verify exchange credentials (without exposing them)

**3.4 Active Configuration Management**
- Track which configurations are currently active
- Ensure scheduler only processes active configs
- Handle configuration changes without restart (live reload)
- **Frontend Integration**: Dashboard can create/edit indicators, strategies, and risk parameters via API
- **Address Position Sizing Issue**: Update contract-to-USD calculations for accurate position sizing

### Phase 4: Unified Deployment Strategy

#### Objective
Consolidate all services into a single deployable unit

#### Implementation Steps

**4.1 Service Consolidation**
- All APIs run through main_api.py
- MCP servers managed by PM2
- Single entry point for entire system

**4.2 Process Management**
- PM2 configuration for all services
- Automatic restart on failure
- Log aggregation and rotation

**4.3 Environment Configuration**
- Single .env file for all settings
- Environment-specific overrides
- Secure credential management

**4.4 Health Monitoring**
- Unified health check endpoint
- Service dependency verification
- Database connection monitoring
- MCP server availability checks

### Phase 5: Basic Dashboard Implementation

#### Objective
Create minimal UI for monitoring and control

#### Implementation Steps

**5.1 Dashboard Backend**
- Serve static HTML/JS files via FastAPI
- WebSocket endpoint already exists
- RESTful APIs already implemented

**5.2 Core Dashboard Features**
- System status overview (modules, scheduler, connections)
- Active positions display with real-time P&L
- Trade history with decision reasoning
- Start/stop controls for autonomous mode
- Configuration selector and editor

**5.3 Real-Time Updates**
- WebSocket connection for live data
- Position updates every 30 seconds
- Module status notifications
- Trade execution alerts

### Phase 6: Testing & Validation

#### Objective
Ensure autonomous operation works reliably

#### Implementation Steps

**6.1 Component Testing**
- Test each webhook endpoint individually
- Verify scheduler job execution
- Validate configuration CRUD operations
- Test position sizing calculations with real exchange data

**6.2 Integration Testing**
- Full pipeline test: Schedule → Extract → Decide → Trade
- Multi-configuration parallel execution
- Error recovery scenarios
- Webhook chain failure handling

**6.3 Autonomous Operation Test**
- 24-hour continuous run on testnet
- Monitor for memory leaks or performance degradation
- Verify all trades are properly tracked
- Ensure TP/SL orders execute correctly
- **Success Criteria**: System runs autonomously without manual intervention

### Phase 7: Strategy Development & Optimization

#### Objective
Begin experimenting with real trading strategies

#### Implementation Steps

**7.1 Strategy Library Development**
- Create various strategy configurations
- Test different indicator combinations
- Experiment with risk parameters
- Document what works and what doesn't

**7.2 Performance Analysis**
- Review decision reasoning logs
- Analyze win/loss patterns
- Identify optimal market conditions
- Refine strategy parameters

**7.3 Continuous Improvement**
- A/B test different strategies
- Track performance metrics
- Iterate on successful patterns
- Build personal trading style into AI

## Key Technologies

### APScheduler over Cron
We've chosen APScheduler instead of cron jobs for several critical advantages:
- **Integrated with Application**: Runs within the Python process, sharing database connections and state
- **Dynamic Control**: Start/stop/modify schedules programmatically via API
- **Better Error Handling**: Built-in retry logic and misfire handling
- **Cross-Platform**: Works on any OS, not just Unix/Linux
- **Configuration-Driven**: Easy to manage multiple schedules for different configs

### Webhook Architecture
- Simple HTTP POST requests between module APIs
- Each module knows how to trigger the next in the chain
- Lightweight payload with user_id, config_id, and context
- Fire-and-forget pattern for prototype (no complex retry logic)

### Single Process Architecture
- main_api.py serves as the central orchestrator
- All module APIs mounted as sub-applications
- Shared database connections and state
- Unified logging and monitoring

## Critical Success Factors

### Autonomous Operation
- System must run 24/7 without manual intervention
- Automatic recovery from transient failures
- Clear audit trail of all decisions and actions
- Real-time visibility into system state

### Multi-Strategy Support
- Multiple configurations running in parallel
- Independent decision making per configuration
- Shared monitoring and risk management
- Performance tracking per strategy

### Safety and Control
- Emergency stop functionality
- Per-configuration pause/resume
- Risk limits enforced at multiple levels
- Clear alerting for anomalies

## Next Steps After Prototype

Once the autonomous prototype is running successfully:

1. **Frontend Development** (separate documentation)
   - User interface for configuration management
   - Real-time dashboard with charts and metrics
   - Mobile-responsive design
   - Integration with backend APIs

2. **Strategy Optimization**
   - Backtesting framework
   - Strategy performance analytics
   - A/B testing different approaches
   - Machine learning enhancements

3. **Production Hardening**
   - Multi-user support
   - Enhanced security (API keys, encryption)
   - Horizontal scaling
   - Disaster recovery

4. **Platform Features**
   - Strategy marketplace
   - Social trading features
   - Advanced risk management
   - Multi-exchange support

## Development Philosophy

This prototype is designed to:
- **Validate the concept**: Prove that AI agents can trade effectively
- **Learn what works**: Discover which strategies and indicators perform best
- **Iterate quickly**: Make changes without complex deployments
- **Build confidence**: Start with testnet, move to small real positions
- **Have fun**: Experiment with different trading ideas and see immediate results

The goal is to create a working system that can evolve into a production platform while maintaining the flexibility to experiment and learn along the way.
