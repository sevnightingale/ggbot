# GGBotConfig Component - Implementation Plan

**Status**: Phase 7 Complete - Config Component Overhaul Required  
**Priority**: High - Critical for user onboarding and bot management  
**Estimated Timeline**: 9-13 hours focused development  

---

## **🚨 Current State Problems**

### **1. Configuration Structure Misalignment**
- **Current**: Component uses simple `Set<string>` for indicators like `['RSI', 'MACD']`
- **Reality**: Config template expects `['RSI_5m', 'RSI_15m', 'MACD_1h']` format
- **Database**: Has sophisticated `indicators` table with metadata, categories, premium flags

### **2. No Backend Integration**
- **Save function**: Just `console.log()` - no API calls
- **Load function**: No loading from V2 API endpoints  
- **Static data**: Hardcoded arrays instead of database queries

### **3. Missing Premium/Permission System**
- **No subscription checking**: Doesn't know if user has premium access
- **No indicator gating**: Shows all indicators regardless of user permissions
- **No dynamic loading**: Should load available indicators from database

---

## **🎯 Required Major Changes**

### **A. State Management Overhaul**
**Current state structure** needs complete redesign to match `template_v1.json`:

```typescript
// CURRENT (Wrong)
const [selectedIndicators, setSelectedIndicators] = useState<Set<string>>(new Set(['RSI', 'MACD']))

// NEEDED (Correct)
const [configData, setConfigData] = useState({
  selected_pair: "BTC/USDT",
  extraction: {
    data_sources: {
      technical_indicators: ["RSI_5m", "RSI_15m", "MACD_1h"],
      // ... other sources
    }
  },
  decision: {
    analysis_frequency: "1h",
    system_prompt: "...",
    user_prompt: "..."
  },
  trading: {
    execution_mode: "paper",
    leverage: 1,
    position_sizing: { /*...*/ },
    risk_management: { /*...*/ }
  }
})
```

### **B. Dynamic Data Sources Loading**
Replace hardcoded arrays with API calls:

```typescript
// Load data sources with points from database
const [dataSourcesWithPoints, setDataSourcesWithPoints] = useState([])
const [userProfile, setUserProfile] = useState(null)

useEffect(() => {
  // Call V2 API: /api/v2/data-sources-with-points
  // Call V2 API: /api/v2/user/profile  
  // Filter available data points by user's paid_data_points
}, [])
```

### **C. Save/Load Integration**
```typescript
const handleSave = async () => {
  if (isEditingExisting) {
    // PUT /api/v2/config/{config_id}
    await updateConfig(bot.config_id, configData)
  } else {
    // POST /api/v2/config
    await createConfig(configData)
  }
}

const handleLoad = async () => {
  // GET /api/v2/config/{config_id}
  const config = await getConfig(bot.config_id)
  setConfigData(config.config_data)
}
```

---

## **🔧 Implementation Scope**

### **Phase A: Data Structure Alignment** (2-3 hours)
1. **Replace component state** to match `template_v1.json` structure
2. **Update form sections** to work with nested config object
3. **Fix indicator selection** to use timeframe-specific format

**Key Tasks:**
- Replace individual state variables with single `configData` object
- Update all form inputs to read/write from nested config structure
- Align indicator format: `"RSI"` → `["RSI_5m", "RSI_15m", "RSI_1h"]`
- Update trading parameters to match schema exactly

### **Phase B: Dynamic Data Loading** (3-4 hours)  
1. **Create data sources API service** to fetch from `/api/v2/data-sources-with-points`
2. **Implement premium checking** - disable premium data points for users without access
3. **Load trading pairs** from exchange API or static comprehensive list
4. **Add loading states** and error handling

**Key Tasks:**
- Replace hardcoded `technicalIndicators` with data_sources/data_points API data
- Add premium-aware data point selection UI (check user.paid_data_points)
- Implement loading skeletons for dynamic content  
- Add error boundaries and retry mechanisms

### **Phase C: Save/Load Functionality** (2-3 hours)
1. **Implement save logic** - create vs update detection
2. **Add form validation** against config schema
3. **Connect to V2 API endpoints** for config CRUD
4. **Add success/error feedback** for user actions

**Key Tasks:**
- Replace `console.log()` save with real API calls
- Add config validation using BotConfigV2 schema
- Implement optimistic updates with rollback
- Add success toasts and error handling

### **Phase D: UX Improvements** (2-3 hours)
1. **Premium indicators** - show locked state with upgrade CTA
2. **Config templates** - preset configurations for common strategies
3. **Form sections** - better organization and progressive disclosure
4. **Real-time validation** - immediate feedback on config changes

**Key Tasks:**
- Design premium indicator lock UI with upgrade prompts
- Add template selection (RSI, MACD, Manual, etc.)
- Improve form navigation and section management
- Add inline validation with helpful error messages

---

## **🏗 Architecture Decisions Needed**

### **1. Edit vs Create Mode**
```typescript
interface GGBotConfigProps {
  bot: Bot | null          // null = create mode, bot = edit mode
  isOpen: boolean
  onClose: () => void
  onSave?: (config: BotConfigV2) => void  // Callback when config saved
}

// Usage patterns:
// Create new: <GGBotConfig bot={null} ... />
// Edit existing: <GGBotConfig bot={selectedBot} ... />
// Copy config: <GGBotConfig bot={copyFromBot} mode="copy" ... />
```

### **2. Premium Data Point UI Pattern**
```typescript
// How to show locked data points?
<DataPointOption 
  dataPoint={dataPoint}
  isLocked={dataPoint.requires_premium && !userProfile.paid_data_points.includes(dataPoint.name)}
  onUpgrade={() => showUpgradeModal(dataPoint.name)}
  description={dataPoint.description}
  configValues={dataPoint.config_values}
/>

// Premium data point display:
// 🔒 ggShot Premium Signals (Premium)
//    [Upgrade to Signals] button
```

### **3. Config Validation Strategy**
```typescript
// Progressive validation approach:
interface ValidationResult {
  isValid: boolean
  errors: Record<string, string[]>
  warnings: Record<string, string[]>
}

// Validate as user types:
const validateConfigSection = (section: string, data: any): ValidationResult
const validateFullConfig = (config: ConfigData): ValidationResult

// UI feedback:
// ✅ Valid sections: green checkmark
// ⚠️ Warning sections: yellow warning icon  
// ❌ Invalid sections: red error icon with details
```

---

## **📋 Critical Dependencies**

### **Backend APIs Needed** (Implementation Status):
- ✅ `GET /api/v2/data-sources-with-points` - Available data sources and points (ready to implement)
- ✅ `GET /api/v2/user/profile` - User profile with paid_data_points (exists)
- ✅ `GET /api/v2/config/{id}` - Load existing config (exists)
- ✅ `PUT /api/v2/config/{id}` - Update config (exists)  
- ✅ `POST /api/v2/config` - Create new config (exists)

### **Frontend Services Needed**:
```typescript
// services/ConfigService.ts
class ConfigService {
  async createConfig(configData: ConfigData): Promise<BotConfigV2>
  async updateConfig(configId: string, configData: ConfigData): Promise<BotConfigV2>
  async getConfig(configId: string): Promise<BotConfigV2>
  async validateConfig(configData: ConfigData): Promise<ValidationResult>
}

// services/DataSourceService.ts  
class DataSourceService {
  async getDataSourcesWithPoints(): Promise<DataSourceWithPoints[]>
  async getUserProfile(userId: string): Promise<UserProfile>
  filterByUserAccess(dataPoints: DataPoint[], userPaidPoints: string[]): DataPoint[]
}

// services/ValidationService.ts
class ValidationService {
  validateConfigSchema(config: any): ValidationResult
  validateDataPointSelection(dataPoints: string[], available: DataPoint[]): ValidationResult
  validateTradingParams(trading: TradingConfig): ValidationResult
}
```

---

## **⏱ Detailed Timeline**

### **Phase A: Data Alignment** (2-3 hours)
- **Hour 1**: Replace component state structure with `configData` object
- **Hour 2**: Update all form inputs to use nested config paths
- **Hour 3**: Fix indicator format and test basic form functionality

### **Phase B: Dynamic Loading** (3-4 hours)
- **Hour 1-2**: Create API services and integrate indicator loading
- **Hour 2-3**: Implement permission checking and premium indicator UI
- **Hour 3-4**: Add loading states, error handling, and user feedback

### **Phase C: Save/Load** (2-3 hours)
- **Hour 1**: Implement create vs edit mode detection and API integration
- **Hour 2**: Add config validation and error handling
- **Hour 3**: Test full save/load cycle with real backend

### **Phase D: UX Polish** (2-3 hours)
- **Hour 1**: Design and implement premium indicator lock UI
- **Hour 2**: Add config templates and preset selection
- **Hour 3**: Improve form navigation, validation feedback, and user guidance

---

## **🧪 Testing Strategy**

### **Unit Testing**
```typescript
// ConfigService tests
describe('ConfigService', () => {
  test('creates new config with valid data')
  test('updates existing config')
  test('handles validation errors properly')
  test('manages optimistic updates')
})

// Component tests  
describe('GGBotConfig', () => {
  test('loads existing config in edit mode')
  test('starts empty in create mode')
  test('shows premium indicators as locked for free users')
  test('validates config before save')
})
```

### **Integration Testing**
- **Create flow**: Empty form → fill data → save → verify in database
- **Edit flow**: Load config → modify → save → verify changes
- **Permission flow**: Free user sees locked indicators → upgrade prompt
- **Error handling**: Network failures, validation errors, server errors

---

## **📝 Implementation Notes**

### **Critical Considerations**
1. **Backward Compatibility**: Old configs may not match new schema - need migration strategy
2. **User Experience**: Don't overwhelm users - progressive disclosure of advanced options  
3. **Performance**: Lazy load indicator details, cache user permissions
4. **Error Recovery**: Allow saving partial configs as drafts, auto-save functionality

### **Success Criteria**
- ✅ User can create new bot configurations using real V2 schema
- ✅ Config form reflects actual database structure and permissions
- ✅ Premium features are properly gated with upgrade prompts
- ✅ Save/load works seamlessly with V2 backend APIs
- ✅ Form validation prevents invalid configurations
- ✅ User experience is intuitive and guides users through complex config options

---

## **🚀 Next Steps**

1. **Start with Phase A** - Data structure alignment (foundational)
2. **Create ConfigService** - Centralized API integration  
3. **Test each phase** - Don't proceed until current phase works
4. **Get user feedback** - Test with real user workflows
5. **Iterate and polish** - Refine based on actual usage patterns

**This refactor will transform the config component from a mock interface into a fully functional bot configuration system integrated with the V2 backend.**