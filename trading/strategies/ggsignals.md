# ggSignals

**Timeframe**: Variable (signal-based)
**Style**: Signal aggregator / Symphony integration
**Current Status**: INACTIVE - Symphony API integration issue (Task 3)

---

## Identity

ggSignals is a signal aggregation bot that publishes trading signals to Telegram and executes via Symphony.io live trading integration.

**Note**: This bot operates differently from the other strategy bots. It's primarily a signal publisher and live trading executor rather than a standalone decision-maker.

---

## Current Issue

- 91 enter signals generated
- 0 trades executed on Symphony side
- Suspected API integration issue (Task 3 in TODO.md)

---

## Integration Points

- **Telegram**: Signal publishing
- **Symphony.io**: Live trade execution
- **Decision Engine**: Signal generation

---

## TODO

Investigate Symphony API integration:
1. Check API call format and authentication
2. Verify order placement requests are being sent
3. Review Symphony-side logs for rejected orders
4. Confirm account permissions and balance requirements
