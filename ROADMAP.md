# ggbots Roadmap

Forward-looking direction for the platform. Live today: paper trading and Hyperliquid direct (live) execution at [ggbots.ai](https://ggbots.ai).

## Trading & Instruments

- **Hyperliquid HIP-3 instruments** — expand beyond crypto perps into equities, commodities, and indices. Research and API verification complete; rollout planned alongside live user growth.
- **LLM-driven SL/TP, phase 2** — mid-trade stop-loss and take-profit management. Phase 1 (SL/TP set on entry) is live in both paper and live trading; phase 2 lets the decision engine adjust stops on open positions as conditions evolve.

## Intelligence

- **Market-intelligence expansion** — order-block detection, on-chain heatmaps, order-book depth analysis, and richer sentiment signals layered into the existing 36-data-point catalog.
- **Bot memory v2** — opt-in, LLM-writable persistent observations carried across trading cycles, so agents build context about a market over time instead of reasoning from scratch each cycle.

## Frontend

- **React Query completion** — SSE-cache integration, profile and mutation hooks for snappier optimistic UI.
- **Dashboard redesign** — refreshed Forge monitoring and configuration experience.
