# ggbot Spec Sheet

## Overview

### Purpose
ggbot is an autonomous AI trading agent focused on a single crypto pair (e.g., BTC/USD) on Gains Network’s gTrade platform. It automates:

- Data extraction
- Trade decision-making
- JSON structuring
- Trade execution
- Lifecycle management  

All within a resource-constrained environment (2 GB RAM, 1 vCPU).

---

# 1. Technical Architecture

### 1.1 Modules

#### **Extraction Module**
**Purpose:** Automate data gathering from TradingView (ggShot signals) and compute technical indicators (RSI, MACD) using real-time price data from Gains Network’s diamond contract on Base L2.

**Key Points:**
- **Browser-Use (Playwright):** `login()`, `navigateToChart()`, `configureIndicators()`, `extractDOMData()`.
- **Session Persistence:** Maintains `BrowserContext` to reduce CAPTCHA triggers.
- **ChatGPT 4o (Vision):** Handles screenshot parsing if DOM scraping fails.
- **TA-Lib Integration:** Computes indicators (RSI, MACD) every 5 minutes.
- **Timeframe-Aligned Extraction:** Triggers ggShot extraction right after each candle closes.
- **Multi-Timeframe Capability (Future Use):** Code allows referencing multiple timeframes (e.g., 4h, 1h, 15m).
- **Resource Management:** Single Playwright browser context to conserve RAM and CPU.

---

#### **Decision Module**
**Purpose:** Analyze extracted data, maintain active trade oversight, and decide on opening, adjusting, or closing positions using a reasoning LLM (e.g., DeepSeek R1).

**Key Points:**
- **LLM Integration:** Processes signals from ggShot, RSI, MACD, and trade history.
- **Prompt Usage:** Instructs LLM to consider all signals and return an action (open, adjust, close) with confidence scores.
- **Ongoing Monitoring:** Evaluates active positions every 5 minutes.
- **LLM Fallback Logic:** Reverts to “no new trade” or “manual hold” strategy if LLM is unavailable.

---

#### **Structuring Module**
**Purpose:** Convert high-level trade actions into validated JSON commands suitable for Gains Network’s diamond contract.

**Key Points:**
- **Schema Enforcement:** Uses `jsonschema` to validate fields (`pairIndex`, `collateralAmount`, `leverage`).
- **Risk Filtering:** Queries `getMaxLeverage(pairIndex)` from gTrade’s contract.
- **Final JSON Output:** Produces contract-compatible objects.

---

#### **Trades Module**
**Purpose:** Maintain a detailed record of trades—both active and closed—including chat logs, confidence scores, partial closes, and final outcomes.

**Key Points:**
- **Trade Records & History:** Logs each trade, adjustments, and final results.
- **Chat History Management:** Appends LLM’s reasoning to a `reasoning_log` field.
- **Database Fields:** `confidence_score`, `timeframe`, `reasoning_log`, and `partial_close` events.

---

#### **On-Chain Execution Module**
**Purpose:** Securely interact with gTrade’s diamond contract on Base L2, handling wallet management, transaction signing, and event monitoring.

**Key Points:**
- **Coinbase AgentKit:** Provides `signTransaction()`, `sendTransaction()`, and event monitoring.
- **Diamond Contract Integration:** Uses facet selectors (`openPosition()`, `closePosition()`, etc.).
- **Event Monitoring:** Listens for confirmations and liquidations.

---

### 1.2 Inter-Module Interactions

#### **Data Flow**
1. **Extraction Module** → Stores ggShot signals, TA indicators, and price data in the database.
2. **Decision Module** → Pulls relevant data to generate a new/updated trade action.
3. **Structuring Module** → Validates and formats the action into JSON.
4. **On-Chain Execution Module** → Signs and submits the JSON command.
5. **Trades Module** → Logs trade lifecycle.

#### **Communication**
- PostgreSQL stores signals, trades, logs, etc.
- Redis or in-memory caching for frequently accessed data.

#### **Resource Management**
- **Single browser context**
- **Minimal concurrency**
- **Batched API queries**

---

# 2. Codebase Structure


| **Directory/File**          | **Description**                                       |
|----------------------------|-------------------------------------------------------|
| `ggbot/`                   | Root project directory                               |
| `├── docs/`                | Architecture diagrams, design docs, change logs     |
| `├── extraction/`          | **Extraction Module**                               |
| `│   ├── browser_use/`     | Playwright scripts                                  |
| `│   ├── vision/`          | ChatGPT 4o (Vision) integration                     |
| `│   ├── ta_lib/`          | TA-Lib integration                                  |
| `│   └── extraction_main.py` | Entry point for extraction module                 |
| `├── decision/`            | **Decision & Monitoring Module**                    |
| `│   ├── llm_integration/` | DeepSeek R1 or similar LLM integration              |
| `│   ├── strategy/`        | Trading strategy logic                              |
| `│   └── decision_main.py` | Entry point for decision module                     |
| `├── structuring/`         | **Structuring Module**                              |
| `│   ├── json_schema/`     | JSON schema definitions                             |
| `│   └── structuring_main.py` | Entry point for structuring module               |
| `├── trades/`              | **Trades Module**                                   |
| `│   ├── trades_main.py`   | Trade lifecycle management                          |
| `│   └── models.py`        | Database models                                     |
| `├── onchain/`             | **On-Chain Execution Module**                       |
| `│   ├── agentkit/`        | Coinbase AgentKit integration                       |
| `│   └── onchain_main.py`  | Entry point for on-chain execution module           |
| `├── common/`              | **Shared utilities**                                |
| `│   ├── logger.py`        | Centralized logging                                |
| `│   ├── config.py`        | Environment/config loader                          |
| `│   └── utils.py`         | Generic helper functions                           |
| `├── tests/`               | Test suites for different modules                   |
| `├── requirements.txt`     | Dependency list                                     |
| `├── README.md`            | Project overview & setup instructions               |
| `└── .env.example`         | Environment configuration template                  |


# 3. Database Design

## 3.1 Schema Definition

### **sessions**
| Column       | Type       |
|-------------|-----------|
| session_id  | UUID (PK) |
| user_id     | UUID      |
| cookie_data | JSONB     |
| created_at  | TIMESTAMP |
| expires_at  | TIMESTAMP |

### **trades**
| Column            | Type       |
|------------------|-----------|
| trade_id        | UUID (PK) |
| pair_index      | VARCHAR   |
| timeframe       | VARCHAR   |
| collateral_amount | NUMERIC   |
| leverage        | INTEGER   |
| stop_loss       | NUMERIC   |
| take_profit     | NUMERIC   |
| confidence_score | NUMERIC   |
| reasoning_log   | TEXT      |
| trade_status    | VARCHAR   |
| created_at      | TIMESTAMP |

### **logs**
| Column    | Type        |
|----------|------------|
| log_id   | SERIAL (PK) |
| module   | VARCHAR    |
| log_level | VARCHAR    |
| message  | TEXT       |
| timestamp | TIMESTAMP |

---

# 4. Dependencies & Libraries

- **Browser Automation:** Playwright  
- **Image Processing/OCR:** ChatGPT 4o (Vision), Tesseract (fallback)  
- **LLM Integration:** DeepSeek R1 or equivalent  
- **JSON Validation:** `jsonschema`  
- **Blockchain Interaction:** Coinbase AgentKit, Web3.py/Ethers.js  
- **TA Libraries:** TA-Lib  
- **Logging & Monitoring:** `loguru`  
- **Environment Management:** `python-dotenv`  
- **Database:** PostgreSQL, Redis (optional)  
- **Containerization:** Docker  

---

# 5. Development Environment Setup

### **Required Tools**
- **IDE:** `code-server` (remote) or VSCode/PyCharm  
- **Version Control:** Git  
- **Containerization:** Docker  
- **Build Tools:** Makefile or npm scripts  

---

# 6. Security Considerations

- **Data Encryption:** Encrypt sensitive data.  
- **Authentication:** Implement if GUI/admin panel is added.  
- **Wallet Security:** Use secure key handling.  
- **Rate Limiting:** Prevent overload.  

---

# 7. Testing & Validation

- **Unit Testing:** Module-level validation.  
- **Integration Testing:** Ensuring correct data flow.  
- **E2E Testing:** Simulating trades in dry-run mode.  
- **Stress Testing:** Evaluating VM performance.  

---

# Conclusion

ggbot is designed for a **single-pair MVP** on Gains Network’s gTrade with:

- **Timeframe-aligned extraction** (e.g., 15m candles).  
- **LLM-driven decision logic** with fallback strategies.  
- **Robust JSON structuring** and risk filtering.  
- **Secure contract interactions** via Coinbase AgentKit.  
- **Optimized for a low-resource environment** (2 GB RAM, 1 vCPU).  
