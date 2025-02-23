ggbot Spec Sheet
Overview
Purpose:
ggbot is an autonomous AI trading agent focused on a single crypto pair (e.g., BTC/USD) on Gains Network’s gTrade platform. It automates data extraction, trade decision‑making, JSON structuring, trade execution, and lifecycle management in a resource‑constrained environment (2 GB RAM, 1 vCPU). This Spec Sheet outlines the technical architecture, codebase structure, database design, dependencies, and recommended development practices.
1. Technical Architecture
1.1 Modules
Extraction Module
Purpose: Automate data gathering from TradingView (ggShot signals) and compute technical indicators (e.g., RSI, MACD) using real‑time price data from Gains Network’s diamond contract on Base L2.
Key Points:
Browser‑Use (Playwright): Uses login(), navigateToChart(), configureIndicators(), extractDOMData().
Session Persistence: Maintains a persistent BrowserContext to reduce CAPTCHA triggers.
ChatGPT 4o (Vision): Handles screenshot parsing if DOM scraping fails.
TA‑Lib Integration: Computes indicators (e.g., RSI, MACD) every 5 minutes based on gTrade price data.
Timeframe‑Aligned Extraction: Triggers ggShot extraction right after each candle closes (e.g., every 15m).
Multi‑Timeframe Capability (Future Use): Even within a single‑pair MVP, code should allow referencing multiple timeframes (like 4h, 1h, or 15m) to strengthen decisions later.
Resource Management: Limit to one Playwright browser context to conserve RAM and CPU.
Decision Module
Purpose: Analyze extracted data, maintain active trade oversight, and decide on opening, adjusting, or closing positions using a reasoning LLM (e.g., DeepSeek R1).
Key Points:
LLM Integration: Processes signals from ggShot, RSI, MACD, and trade history from the Trades Module.
Sample Prompt Usage: Instructs the LLM to consider pair/timeframe signals, RSI, MACD trends, and trade history, returning an action (open, adjust, close) with a confidence score.
Ongoing Monitoring: Evaluates active positions every 5 minutes for partial closes or updated stop‑losses.
Confidence Scores & Reasoning: Each decision includes a numerical confidence level and textual reasoning stored in the database.
LLM Fallback Logic: If the LLM is unavailable (e.g., outage), revert to a minimal “no new trade” or “manual hold” strategy to avoid system stalls.
Structuring Module
Purpose: Convert high‑level trade actions into validated JSON commands suitable for Gains Network’s diamond contract.
Key Points:
Schema Enforcement: Uses jsonschema to validate fields like pairIndex, collateralAmount, leverage.
Risk Filtering: Dynamically queries gTrade’s contract for max leverage (e.g., getMaxLeverage(pairIndex)); falls back to local config for limits if on‑chain retrieval fails.
Final JSON Output: Produces contract‑compatible objects (e.g., { "pairIndex": 1, "leverage": 3, ... }).
Trades Module
Purpose: Maintain a detailed record of trades—both active and closed—including chat logs, confidence scores, partial closes, and final outcomes.
Key Points:
Trade Records & History: Creates a new record when a trade opens, logs each adjustment, and stores final results upon closure.
Chat History Management: Appends the LLM’s reasoning to a reasoning_log field.
Database Fields: Includes confidence_score, timeframe, reasoning_log, and partial_close events.
On‑Chain Execution Module
Purpose: Securely interact with gTrade’s diamond contract on Base L2, handling wallet management, transaction signing, and event monitoring.
Key Points:
Coinbase AgentKit: Provides wallet integration, signTransaction(), sendTransaction(), and event monitoring.
Diamond Contract Integration: Uses facet selectors (e.g., openPosition(), closePosition(), getPrice(), getPositionInfo()).
Event Monitoring: Listens for confirmations, liquidations; includes fallback polling if websockets fail.
Batch API Calls: Minimizes overhead by aggregating multiple Gains Network queries where possible.

1.2 Inter‑Module Interactions
Data Flow:
Extraction Module → Stores ggShot signals, TA indicators, and price data in the database.
Decision Module → Pulls relevant data from the database (plus any active trade info from Trades Module) to generate a new or updated trade action.
Structuring Module → Validates and formats the action into JSON.
On‑Chain Execution Module → Signs and submits the JSON command to gTrade, updating trade statuses in the database.
Trades Module → Logs creation, updates, closures, and final outcomes for each trade.
Communication:
PostgreSQL is the main data persistence layer for signals, trades, logs, etc.
In‑memory caching (e.g., Redis or Python dictionaries) can store frequently accessed data (like price updates) for low‑latency reads.
Resource Management:
A single browser context, minimal concurrency, and batched Gains Network queries keep CPU and memory usage stable on a 2 GB RAM, 1 vCPU VM.

2. Codebase Structure
bash
CopyEdit
ggbot/
├── docs/                    # Architecture diagrams, design docs, change logs
├── extraction/              # Extraction Module
│   ├── browser_use/         # Playwright scripts
│   ├── vision/              # ChatGPT 4o (Vision) integration
│   ├── ta_lib/              # TA-Lib integration
│   └── extraction_main.py   # Entry point
├── decision/                # Decision & Monitoring Module
│   ├── llm_integration/     # DeepSeek R1 or similar LLM
│   ├── strategy/            # Trading strategy logic
│   └── decision_main.py     # Entry point
├── structuring/             # Structuring Module
│   ├── json_schema/         # JSON schema definitions
│   └── structuring_main.py  # Entry point
├── trades/                  # Trades Module
│   ├── trades_main.py       # Trade lifecycle management
│   └── models.py            # Database models
├── onchain/                 # On-Chain Execution Module
│   ├── agentkit/            # Coinbase AgentKit integration
│   └── onchain_main.py      # Entry point
├── common/                  # Shared utilities
│   ├── logger.py            # Centralized logging
│   ├── config.py            # Environment/config loader
│   └── utils.py             # Generic helpers
├── tests/                   # Test suites
│   ├── extraction_tests.py
│   ├── decision_tests.py
│   ├── structuring_tests.py
│   ├── trades_tests.py
│   └── onchain_tests.py
├── requirements.txt         # Dependency list
├── README.md                # Project overview & setup
└── .env.example             # Environment configuration

File Naming:
snake_case for Python files (e.g., extraction_main.py).
PascalCase for classes (e.g., TradeRecord).
Lowercase directory names with underscores if needed (e.g., decision_monitoring).

3. Database Design
3.1 Schema Definition
sessions
session_id (UUID, Primary Key)
user_id (UUID)
cookie_data (JSONB)
created_at (TIMESTAMP)
expires_at (TIMESTAMP)
trades
trade_id (UUID, Primary Key)
pair_index (VARCHAR)
timeframe (VARCHAR)
collateral_amount (NUMERIC)
leverage (INTEGER)
stop_loss (NUMERIC)
take_profit (NUMERIC)
confidence_score (NUMERIC)
reasoning_log (TEXT)
trade_status (VARCHAR)
created_at (TIMESTAMP)
logs
log_id (SERIAL, Primary Key)
module (VARCHAR)
log_level (VARCHAR)
message (TEXT)
timestamp (TIMESTAMP)
3.2 Indexing & Optimization
Indexes:
sessions.expires_at for cleanup.
trades.created_at for recent trade lookups.
Optionally index trades.pair_index + trades.timeframe if multiple timeframes/pairs are supported later.
Database Strategy:
Use partitioning if logs grow large.
Consider JSONB indexing if you store dynamic data in reasoning_log.

4. Dependencies & Libraries
4.1 External Libraries
Browser Automation:
Browser‑Use (Playwright).
Image Processing/OCR:
ChatGPT 4o (Vision); fallback to Tesseract if needed.
LLM Integration:
DeepSeek R1 or similar advanced reasoning model.
JSON Validation:
jsonschema.
Blockchain Interaction:
Coinbase AgentKit for secure wallet management, signing.
Web3.py/Ethers.js for Gains Network contract calls.
TA Libraries:
TA‑Lib for computing RSI, MACD, etc.
Logging & Monitoring:
loguru (Python) or similar.
Environment Management:
python‑dotenv or equivalent.
4.2 Versioning & Compatibility
Semantic Versioning:
MAJOR.MINOR.PATCH for modules and the overall system.
Dependency Management:
Strict version pinning in requirements.txt.
Containerization:
Docker (multi‑stage builds) for consistent environments.

5. Development Environment Setup
5.1 Required Tools
IDE/Editor:
code‑server (remote) or local VSCode/PyCharm.
Version Control:
Git (GitHub/GitLab).
Containerization:
Docker for dev and production.
Build Tools:
Makefile or npm scripts for common tasks.
5.2 Environment Configuration
Configuration Files:
.env.example and config.py for essential variables (API keys, Gains Network endpoints).
Setup Documentation:
Step‑by‑step in README.md for repository cloning, dependency installation, Docker usage.
Local Testing:
Optional Docker Compose to run PostgreSQL, local blockchain, or other dependencies.

6. Security Considerations
6.1 Data Protection
Data at Rest:
Encrypt sensitive data or store in a vault.
Data in Transit:
Force HTTPS/TLS for LLM and Gains Network interactions.
Secrets Management:
Keep private keys out of version control; store in .env only for prototyping.
6.2 Access Control
Authentication:
Implement user authentication if a GUI or admin panel is introduced.
Wallet Security:
Use Coinbase AgentKit’s secure key handling in production.
Rate Limiting & Validation:
Prevent malicious or accidental system overload.

7. Testing & Validation
7.1 Testing Strategy
Unit Testing:
Validate each module in isolation (extraction, decision, structuring, trades, onchain).
Integration Testing:
Confirm correct data flow across modules.
End‑to‑End (E2E) Testing:
Run a dry‑run mode simulating trades without sending actual on‑chain transactions.
Stress Testing:
Ensure the 2 GB, 1 vCPU VM can handle peak extraction and LLM calls.
7.2 Test Environments
Testnet Integration:
Gains Network’s test deployment on Base L2 or a local blockchain (Hardhat).
Continuous Integration (CI):
Use GitHub Actions, GitLab CI, etc., for automated testing.

8. Additional Considerations
8.1 Logging & Monitoring
Centralized Logging:
Send logs to a single sink, alert on critical failures.
Resource Monitoring:
Tools like htop or Docker stats to verify concurrency levels and memory usage.
8.2 Documentation & Version Control
In‑Code Documentation:
Docstrings (PEP‑257) and comments for clarity.
Versioning:
Maintain a changelog, adopt feature branches, and merge to main once stable.

9. List of Dependencies
Browser-Use (Playwright-based)
ChatGPT 4o (Vision)
Tesseract (Optional fallback)
LangChain
DeepSeek R1 (or equivalent reasoning LLM)
jsonschema
Coinbase AgentKit
Web3.py (or Ethers.js)
TA-Lib
loguru
python-dotenv
PostgreSQL
Redis (or Python dictionaries, optional)
Docker
code-server
Git

Conclusion
This Spec Sheet defines a five‑module architecture (Extraction, Decision, Structuring, Trades, On‑Chain Execution) tuned for a single‑pair MVP on Gains Network’s gTrade. It highlights:
Timeframe‑aligned data extraction (e.g., 15m candles).
LLM‑driven decision logic with a fallback strategy in case of outages.
Robust JSON structuring and risk filtering.
Secure interaction with a diamond contract on Base L2 via Coinbase AgentKit.
Comprehensive trade lifecycle management in the Trades Module.
By limiting concurrency to a single browser context and batching Gains Network API calls, ggbot remains efficient and stable on a low‑resource VM while retaining the flexibility to expand to multiple pairs or timeframes in the future.

