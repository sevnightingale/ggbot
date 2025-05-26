# Decision Module Development Plan

The Decision Module is the brain of the ggbot system. It analyzes market data, monitors account status, interprets user-defined trading strategies, and makes intelligent trading decisions using LLMs. The module operates in two distinct modes: searching for new opportunities and managing active positions.

## Core Architecture

### Dual-Mode Operation

The Decision Module operates in two primary modes:

1. **New Trade Mode** - When no positions are active
   - Analyzes market conditions for entry opportunities
   - Evaluates against user's trading strategy
   - Considers account status and risk guidelines
   - Makes fresh decisions without historical context

2. **Trade Management Mode** - When positions are active
   - Reviews original reasoning for entering positions
   - Evaluates current market conditions against entry thesis
   - Decides whether to hold, adjust, or exit positions
   - Maintains continuity to avoid erratic behavior

### Data Flow

```
Market Data (DB) ─┐
                  ├─→ DecisionEngine → LLM → Trade Intent → Trading Module
Account State (DB)─┤
                  └─→ + Strategy Config
                      + Trade History (if active)
```

## Configuration Structure

The Decision Module uses a simple 4-field configuration stored in the database:

- **llm_provider**: Which LLM to use (e.g., "deepseek", "openai", "anthropic")
- **strategy**: Natural language description of the trading strategy
- **risk_guidelines**: Hard limits and risk management rules
- **additional_context**: Any extra information to help the LLM trade effectively

Example configuration:
```json
{
  "llm_provider": "deepseek",
  "strategy": "Trade momentum breakouts using ggshot as the primary signal. Be aggressive in trending markets, cautious in ranges. Look for confluence with RSI and MACD but don't be too rigid. Trust strong signals.",
  "risk_guidelines": "Max position size 5% of capital. Max leverage 10x. Stop trading after 3 losses in a day.",
  "additional_context": "I prefer catching big moves over frequent small trades."
}
```

## Current Implementation Status

### Completed ✅
- [x] Define Strategy and LLMProvider interfaces
- [x] Create simplified 4-field configuration structure
- [x] Update database configuration for default user
- [x] Create base LLM client abstract class
- [x] Implement DeepSeek client (using DECISION_LLM_API_KEY)
- [x] Implement OpenAI client for flexibility
- [x] Add simple factory pattern for LLM selection
- [x] Include retry logic and error handling
- [x] Implement main DecisionEngine class
- [x] Add database query methods for:
  - Latest market data by symbol/timeframe
  - Current account state
  - Active trades and their history
  - User configuration
- [x] Implement dual-mode logic:
  - Check for active trades
  - Route to appropriate decision mode
  - Maintain separate prompts for each mode
- [x] Design decision history structure for trades table
- [x] Implement methods to:
  - Store initial trade reasoning
  - Append subsequent decisions to history
  - Retrieve and format history for LLM context
- [x] Ensure decision continuity across multiple evaluations
- [x] Create system prompts that establish the LLM's role
- [x] Design new trade evaluation prompts
- [x] Design trade management prompts that include history
- [x] Format market data presentation for clarity
- [x] Structure prompts to encourage semi-structured responses
- [x] Define minimal intent structure required by Trading Module
- [x] Parse LLM responses into trade intents
- [x] Validate intents have required fields
- [x] Handle edge cases (no decision, unclear response)
- [x] Create entry point function for scheduled execution
- [x] Add logging throughout the decision process
- [x] Ensure proper error handling and fallbacks
- [x] Test with real market data from extraction module

### In Progress 🔄
- [ ] None currently

### To Be Implemented 📋
- [ ] Integration with API endpoints for production deployment
- [ ] Scheduled execution via cron or similar
- [ ] Performance optimizations for batch processing

## Technical Design Decisions

### Why Natural Language Strategies?
- Allows users to describe strategies as they naturally think
- Leverages LLM's ability to interpret nuanced instructions
- Enables "train an AI to trade like you" vision
- Avoids rigid rule structures that limit creativity

### Why Dual-Mode Architecture?
- Prevents constant position flipping
- Maintains context and original thesis
- Mimics how human traders actually manage positions
- Enables more sophisticated portfolio management

### Why Flexible LLM Provider?
- Different LLMs have different strengths
- Allows users to choose based on cost/performance
- Future-proofs against LLM API changes
- Enables easy testing with different models

## Database Integration

### Tables Used:
- **market_data**: Source for latest indicators and signals
- **account_states**: Current equity, margin, and positions
- **configurations**: User's strategy and risk settings
- **trades**: Store and retrieve decision history

### Key Queries:
1. Get latest market data for a symbol/timeframe
2. Get current account state
3. Get active trades with decision history
4. Update trade with new decision

## Testing Strategy

### Unit Tests
- Test LLM provider implementations
- Test intent parsing logic
- Test database query methods

### Integration Tests
- Test with mock market data
- Test mode switching logic
- Test decision history storage

### End-to-End Tests
- Run against real extraction data
- Verify intent format for Trading Module
- Test continuity across multiple decisions

## Future Production Enhancements

### Performance Optimizations
- [ ] Implement caching for frequently accessed data
- [ ] Add batch processing for multiple symbols
- [ ] Optimize database queries with better indexing
- [ ] Consider streaming LLM responses

### Advanced Features
- [ ] Multi-position portfolio management
- [ ] Correlation analysis between positions
- [ ] Market regime detection
- [ ] Adaptive strategy adjustments
- [ ] Performance analytics feedback loop

### Monitoring & Observability
- [ ] Prometheus metrics for decision latency
- [ ] Track decision accuracy over time
- [ ] Alert on unusual decision patterns
- [ ] Dashboard for decision history visualization

### Security & Compliance
- [ ] Audit trail for all decisions
- [ ] Encryption for sensitive strategy data
- [ ] Rate limiting for LLM API calls
- [ ] User permission levels for strategy access

## Development Guidelines

### Code Organization
- Keep LLM provider implementations minimal and focused
- Centralize database queries in DecisionEngine
- Separate prompt templates from business logic
- Use type hints throughout

### Error Handling
- Always have a fallback for LLM failures
- Log all decisions for debugging
- Gracefully handle missing data
- Never make assumptions about data availability

### Testing Approach
- Start with simple unit tests
- Mock external dependencies
- Test edge cases thoroughly
- Verify integration points carefully

## Next Steps

1. Start with LLM provider interface implementation
2. Build DecisionEngine with basic database queries
3. Implement dual-mode decision logic
4. Create comprehensive prompt templates
5. Test with real market data
6. Iterate on prompt engineering based on results

This module is designed to be the intelligent core of the ggbot system, interpreting human strategies and applying them consistently in changing market conditions.