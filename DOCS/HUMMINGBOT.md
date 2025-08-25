# Hummingbot Integration Plan

**Date**: 2025-08-21  
**Status**: Fresh Start - API + Script V2 Approach  
**Priority**: High - ggShot paper trading ready for production

## 🎯 **Approach: Official API Integration + Custom Script V2**

Following official Hummingbot documentation exactly, with clean break from legacy integration. Combines source installation (for Script V2 development) with official HTTP API integration (for stable communication).

### **Architecture Overview**
```
ggShot Signal → ggbot API Client → Hummingbot API → Script V2 → Paper Trading
     ↓              ↓                   ↓             ↓          ↓
Decision Agent  HTTP Calls        Account Mgmt   ggShot Logic  Real Execution
```

## 🚀 **Implementation Phases**

### **Phase 1: Core Setup**
**Goal**: ggShot signals execute as paper trades

#### **Infrastructure Setup**

**🧑‍💻 Sev Tasks** (Interactive/System-level):

**Step 1: System Dependencies** (from any directory) DONE
```bash
# Can be run from anywhere - installs system-wide packages
sudo apt update && sudo apt upgrade -y && sudo apt install -y build-essential
```

**Step 2: Install Miniconda** (from home directory) DONE
```bash
# Navigate to home directory for clean installation
cd ~
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
# Follow interactive prompts:
# - Accept license terms
# - Accept default installation location (/home/sev/miniconda3)
# - Choose YES to initialize conda in .bashrc
# - Restart terminal after installation completes
```

**Step 3: Clone Hummingbot** (separate from ggbot project) DONE
```bash
# IMPORTANT: Clone outside of /home/sev/ggbot to avoid conflicts
cd ~  # Go to home directory (/home/sev)
git clone https://github.com/hummingbot/hummingbot.git
cd hummingbot  # Now in /home/sev/hummingbot
```

**Step 4: Hummingbot Installation** (inside hummingbot directory)
```bash
# Must be inside /home/sev/hummingbot for these commands
pwd  # Should show /home/sev/hummingbot
./install  # Interactive conda environment creation
conda activate hummingbot  # Activate the environment
./compile  # Compile Hummingbot (takes 2-3 minutes)
```

**Step 5: Initial Configuration** (interactive setup)
```bash
# Still inside /home/sev/hummingbot
./start
# Interactive prompts will ask for:
# - Security password (remember this!)
# - Paper trading setup
# - Exchange connector configuration
```

**Step 6: Set Up Hummingbot API** (optional - can be Docker or source-based)
```bash
# Option A: Use existing Hummingbot source with API mode
cd /home/sev/hummingbot
# Configure for API mode if needed

# Option B: Separate Hummingbot API installation (Docker)
cd ~
git clone https://github.com/hummingbot/hummingbot-api
cd hummingbot-api
./setup.sh
./run.sh
```

**🤖 Claude Tasks** (Integration Development):
```bash
# Will work from /home/sev/ggbot directory
# Building HTTP API client for ggbot → Hummingbot communication
cd /home/sev/ggbot
# Create trading/hummingbot_api_client.py and Script V2
```

#### **Directory Structure After Setup**
```
/home/sev/
├── ggbot/                         # Your existing platform (PRIMARY WORK AREA)
│   ├── main_api.py
│   ├── decision/
│   ├── extraction/
│   └── (new) trading/hummingbot_api_client.py  # HTTP API integration
├── hummingbot/                    # Hummingbot source installation
│   ├── hummingbot/               # Source code
│   ├── conf/                     # Configuration files
│   ├── logs/                     # Hummingbot logs
│   └── scripts/ggbot_strategy.py # ONE custom Script V2 file
├── hummingbot-api/               # Optional: Separate API installation
│   └── (Docker-based API server)
└── miniconda3/                   # Conda installation
```

**Key Points:**
- **90% of work happens in `/home/sev/ggbot`** (HTTP API client)
- **Minimal `/home/sev/hummingbot` access** (just one Script V2 file)
- **Clean separation** between ggbot platform and Hummingbot

#### **Integration Strategy**

**🤖 Claude Tasks** (Code Development):
- **HTTP API Client**: Create `hummingbot_api_client.py` in ggbot/trading/
- **Script V2 Development**: Create `ggbot_strategy.py` in /home/sev/hummingbot/scripts/
- **Market Data Service**: Symbol normalization ("solana" → "SOL-USDT")  
- **Same Endpoints**: Keep `/webhooks/execute-trade` for seamless Decision Module integration

**🧑‍💻 Sev Tasks** (Configuration):
- **Exchange Setup**: Configure paper trading connectors in Hummingbot
- **API Setup**: Start Hummingbot API server (port 8000 or custom)
- **Script Deployment**: Install ggbot_strategy.py and test with `start --script`
- **Credentials**: Configure exchange API keys (sandbox/testnet initially)

#### **Success Criteria**
- [ ] Hummingbot running with paper trading enabled
- [ ] Hummingbot API server responding (http://localhost:8000/health)
- [ ] Script V2 deployed and executable via `start --script ggbot_strategy.py`
- [ ] Single ggShot signal executes paper trade via HTTP API integration
- [ ] Position tracking via Hummingbot API endpoints
- [ ] No changes needed to Decision Module

### **Phase 2: Multi-User & Symbol Support**
**Goal**: Full ggShot integration with 140+ trading pairs

#### **Market Data Service Implementation**
**🤖 Claude Tasks** (Code Development):
```python
class MarketDataService:
    """Symbol normalization for ggShot → exchange format"""
    
    async def normalize_symbol(self, ggshot_symbol: str) -> str:
        # "solana" → "SOL-USDT", "cardano" → "ADA-USDT" 
        return self.symbol_mappings.get(ggshot_symbol.lower())
    
    async def get_trading_rules(self, pair: str) -> dict:
        # Cache tick_size, step_size, min_notional from Hummingbot
        pass
```

**🧑‍💻 Sev Tasks** (Configuration & Testing):
- **Exchange Configuration**: Set up multiple exchange connectors in Hummingbot
- **Symbol Validation**: Test symbol mappings across different exchanges
- **Performance Testing**: Monitor resource usage with multiple concurrent strategies

#### **User Account Management**
**🤖 Claude Tasks** (Code Development):
- **API Account Management**: Use Hummingbot API endpoints for user account isolation
- **Configuration Management**: Separate API calls per user configuration
- **Data Isolation**: Query separation via API account management

**🧑‍💻 Sev Tasks** (Setup & Security):
- **API Authentication**: Set up secure Hummingbot API authentication
- **Account Creation**: Configure multiple accounts via API endpoints
- **Monitoring Setup**: Configure separate API monitoring per config

#### **Success Criteria**  
- [ ] All 140+ ggShot symbols supported
- [ ] Multiple users trading independently via separate API accounts
- [ ] Performance tracking per configuration via API endpoints

### **Phase 3: Production Features**
**Goal**: Production-ready with advanced strategic management

#### **Enhanced Trading Capabilities**
**🤖 Claude Tasks** (Advanced Development):
- **Strategic Trade Management**: AI-driven position adjustments and portfolio balancing
- **Risk Management Engine**: Dynamic position sizing based on market conditions
- **Performance Analytics**: Advanced P&L tracking and strategy optimization
- **Real-time Monitoring**: Enhanced position tracking and alert systems

**🧑‍💻 Sev Tasks** (Production Setup):
- **Live Trading Preparation**: Exchange credential management for real accounts
- **Security Hardening**: Production-grade API key storage and access controls
- **Monitoring Infrastructure**: Set up alerting and performance dashboards
- **Backup & Recovery**: Strategy data backup and disaster recovery procedures

#### **Future Extensibility**
**Potential Enhancements** (Future Considerations):
- **Custom Connector Development**: Ability to add new exchange connectors (e.g., Gains Network DEX) if needed
- **Advanced Order Types**: Implementation of complex trading strategies
- **Cross-Exchange Arbitrage**: Multi-exchange strategy coordination

## 🏗️ **Key Architecture Decisions**

### **Database Strategy: Dual System**
- **ggBot Database**: User management, configurations, decision audit (strategy_runs)
- **Hummingbot Database**: Trade execution, position tracking, order management
- **Sync Service**: Real-time bridging for frontend display

### **API Integration Pattern**
```python
# ggbot/trading/hummingbot_api_client.py - HTTP API integration
from hummingbot_api_client import HummingbotAPIClient

class GGBotHummingbotClient:
    """HTTP API client for ggBot → Hummingbot communication"""
    
    def __init__(self):
        self.client = HummingbotAPIClient(
            base_url="http://localhost:8000",
            username="admin", 
            password="admin"
        )
    
    async def execute_ggshot_signal(self, config_id: str, signal: dict):
        """Execute ggShot trading signal via HTTP API"""
        trading_pair = self.normalize_symbol(signal['symbol'])
        amount = self.calculate_position_size(signal['confidence'])
        
        # HTTP API call to Hummingbot
        order = await self.client.trading.place_order(
            account_name=f"paper_{config_id[:8]}",
            connector_name="binance_paper_trade",
            trading_pair=trading_pair,
            trade_type="BUY" if signal['direction'] == 'long' else "SELL",
            amount=amount,
            order_type="MARKET"
        )
        
        return order
```

### **Script V2 Pattern**
```python
# /home/sev/hummingbot/scripts/ggbot_strategy.py - Custom Script V2
from hummingbot.strategy.strategy_v2_base import StrategyV2Base

class GGBotStrategy(StrategyV2Base):
    """Script V2 for ggShot signal execution"""
    
    def __init__(self):
        super().__init__()
        self.signal_queue = asyncio.Queue()
    
    async def on_tick(self):
        """Process queued ggShot signals"""
        if not self.signal_queue.empty():
            signal = await self.signal_queue.get()
            await self.execute_signal(signal)
    
    async def execute_signal(self, signal: dict):
        """Execute ggShot trading signal within Hummingbot"""
        # Signal comes from HTTP API, executes within Hummingbot
        pass
```

### **Symbol Normalization Strategy**
```python
# Preserved from legacy plan - still highly relevant
SYMBOL_MAPPINGS = {
    "solana": "SOL-USDT",
    "cardano": "ADA-USDT", 
    "bitcoin": "BTC-USDT",
    # ... 140+ mappings
}
```

### **Position Sizing Strategy**
```python
# Preserved confidence-based risk allocation
def confidence_to_risk_percentage(confidence: float) -> float:
    if confidence >= 0.8: return 0.05    # 5% risk for high confidence
    elif confidence >= 0.6: return 0.03  # 3% risk for medium confidence  
    elif confidence >= 0.4: return 0.02  # 2% risk for low confidence
    else: return 0.01                    # 1% minimum risk
```

## 🔧 **Technical Implementation**

### **Core Components**

#### **1. HTTP API Integration Bridge** 
```python
# /trading/hummingbot_api_client.py - HTTP API integration layer
import asyncio
from hummingbot_api_client import HummingbotAPIClient

class HummingbotAPIBridge:
    """Bridge between ggBot and Hummingbot via HTTP API"""
    
    def __init__(self):
        self.client = HummingbotAPIClient(
            base_url="http://localhost:8000",
            username="admin",
            password="admin"
        )
    
    async def execute_signal(self, user_config: str, signal: dict):
        """Execute ggShot signal via Hummingbot HTTP API"""
        # 1. Normalize symbol
        pair = await self.normalize_symbol(signal['symbol'])
        
        # 2. Calculate position size from confidence
        size = self.calculate_position_size(signal['confidence'])
        
        # 3. Execute via HTTP API
        order = await self.client.trading.place_order(
            account_name=f"paper_{user_config[:8]}",
            connector_name="binance_paper_trade",
            trading_pair=pair,
            trade_type="BUY" if signal['direction'] == 'long' else "SELL",
            amount=size,
            order_type="MARKET"
        )
        
        return {"status": "success", "order_id": order.get('order_id')}

# FastAPI endpoint (unchanged interface for Decision Module)
@app.post("/webhooks/execute-trade")
async def execute_trade(request: TradeRequest):
    result = await hummingbot_api_bridge.execute_signal(
        user_config=request.config_id,
        signal=request.dict()
    )
    return result
```

#### **2. API Account Management**
```python
class APIAccountManager:
    """Maps ggBot configs to Hummingbot API accounts"""
    
    def __init__(self, api_client):
        self.client = api_client
        self.user_accounts = {}
    
    async def create_user_account(self, config_id: str, user_config: dict):
        """Create isolated account for user config via API"""
        account_name = f"paper_{config_id[:8]}"
        
        # Create account via HTTP API
        account = await self.client.accounts.add_account(
            account_name=account_name
        )
        
        # Add exchange credentials
        await self.client.accounts.add_credential(
            account_name=account_name,
            connector_name="binance_paper_trade",
            credentials={"api_key": "paper_key", "secret": "paper_secret"}
        )
        
        self.user_accounts[config_id] = account_name
        return account_name
    
    def get_user_account(self, config_id: str):
        """Get existing account name for user"""
        return self.user_accounts.get(config_id, f"paper_{config_id[:8]}")
```

#### **3. Performance Tracking**
```python
class APIPerformanceTracker:
    """Track performance via Hummingbot HTTP API"""
    
    def __init__(self, api_client, account_manager):
        self.client = api_client
        self.account_manager = account_manager
    
    async def get_config_performance(self, config_id: str) -> dict:
        """Get performance metrics for user configuration via API"""
        account_name = self.account_manager.get_user_account(config_id)
        
        if not account_name:
            return {"error": "Account not found"}
        
        # Get portfolio state via HTTP API
        portfolio = await self.client.portfolio.get_state()
        
        # Get trade history via HTTP API  
        # Note: API endpoints may vary - check official documentation
        trades = await self.client.trading.get_trades(account_name=account_name)
        orders = await self.client.trading.get_orders(account_name=account_name)
        
        # Calculate metrics from API data
        total_pnl = sum(trade.get('profit_loss', 0) for trade in trades)
        winning_trades = [t for t in trades if t.get('profit_loss', 0) > 0]
        
        return {
            "total_pnl": total_pnl,
            "trade_count": len(trades),
            "win_rate": len(winning_trades) / len(trades) if trades else 0,
            "active_orders": len([o for o in orders if o.get('status') == 'open']),
            "account_name": account_name
        }
```

## 📊 **Integration with Existing System**

### **Preserved Components**
- **Decision Module**: No changes needed - same webhook endpoints
- **Frontend APIs**: Same endpoints, but query Hummingbot for trade data
- **User Management**: Existing user/config system unchanged
- **Audit Trail**: Keep strategy_runs for decision tracking

### **Replaced Components**  
- **CCXT MCP**: Replaced with Hummingbot HTTP API
- **Custom Trading Engine**: Replaced with Hummingbot API execution
- **Manual TP/SL**: Replaced with Hummingbot automatic position management

### **Enhanced Components**
- **Monitoring**: Real-time position tracking vs 30-second polling
- **Risk Management**: Professional-grade execution with built-in safeguards
- **Multi-Exchange**: Native support for 50+ exchanges

## 🎯 **Success Metrics**

### **Core Functionality Targets**
- [ ] ggShot signals → paper trades in <60 seconds via HTTP API
- [ ] Zero execution failures due to integration issues
- [ ] Position sizing calculated correctly from confidence
- [ ] Basic P&L tracking functional via Hummingbot API endpoints

### **Multi-User Platform Targets**
- [ ] All 140+ ggShot symbols supported
- [ ] 5+ users trading simultaneously via separate API accounts
- [ ] Performance tracking per configuration via API queries
- [ ] Resource usage <80% of available system capacity

### **Production Readiness Targets**  
- [ ] Strategic trade management operational via Script V2
- [ ] Live trading infrastructure ready (credentials, security)
- [ ] <2 second HTTP API call latency
- [ ] >99% system uptime for extended periods
- [ ] Comprehensive monitoring and alerting functional via API

## 🔄 **Migration Strategy**

### **Clean Break Approach**
1. **Complete Removal**: Existing integration fully deleted (✅ Done)
2. **Fresh Installation**: Follow official docs exactly
3. **Minimal Integration**: Start with single signal test
4. **Incremental Expansion**: Add features iteratively

### **Risk Mitigation**
- **Version Pinning**: Use specific Hummingbot releases, avoid development branch for production
- **API Stability**: Use official HTTP API endpoints only (no internal imports)
- **Source Control**: Track all customizations in version control for reproducibility
- **Rollback Plan**: Maintain clean system snapshots before major changes
- **Gradual Rollout**: Start with paper trading only, progressive live trading deployment

## 🚀 **Next Steps**

### **Foundation Phase**
**🧑‍💻 Sev Tasks** (System Setup):
1. Install system dependencies and Miniconda
2. Complete Hummingbot source installation and first-time setup
3. Configure paper trading connectors
4. Set up basic strategy configuration

**🤖 Claude Tasks** (Integration Development):
1. Build HTTP API client for ggBot integration (`trading/hummingbot_api_client.py`)
2. Create custom Script V2 (`/home/sev/hummingbot/scripts/ggbot_strategy.py`)
3. Implement symbol normalization service
4. Test single ggShot signal execution via API

### **Scale Phase**  
**🧑‍💻 Sev Tasks** (Configuration & Testing):
1. Configure multiple exchange connectors 
2. Set up isolated strategy instances for different configs
3. Performance monitoring and resource optimization
4. Security and credential management setup

**🤖 Claude Tasks** (Platform Development):
1. Implement multi-user API account management
2. Build performance tracking via API endpoints
3. Create advanced position sizing algorithms
4. Develop monitoring and alerting systems via API

### **Production Phase**
**🧑‍💻 Sev Tasks** (Production Setup):
1. Live trading infrastructure preparation
2. Security hardening and backup procedures
3. Production monitoring setup
4. Comprehensive testing with real market conditions

**🤖 Claude Tasks** (Advanced Features):
1. Strategic trade management capabilities
2. Advanced analytics and reporting
3. Risk management enhancements
4. Performance optimization and scaling

---

**Result**: Clean, API-based Hummingbot integration that preserves ggBot's strengths while leveraging battle-tested execution infrastructure. HTTP API integration ensures stability and upgradability, while Script V2 enables custom ggShot logic. Ready for ggShot production deployment with clear scaling path to multi-user platform.