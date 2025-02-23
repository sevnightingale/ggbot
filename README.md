# ggbot
Autonomous AI Trading Agent

**Description**  
ggbot is an autonomous AI trading agent that operates on Gains Network’s gTrade platform, implementing a five‑module architecture to orchestrate data extraction, AI‑driven decision making, JSON command structuring, trade lifecycle management, and on‑chain execution—all on a resource‑constrained VM.

---

## Architecture Overview

This project is structured into five primary modules:

1. **Extraction Module (`extraction/`)**  
   - Scrapes chart data (e.g., from TradingView), computes technical indicators, and gathers real-time price data from Gains Network.

2. **Decision & Monitoring Module (`decision/`)**  
   - Uses a reasoning LLM to analyze signals and decide on trade actions (open, adjust, or close).

3. **Structuring Module (`structuring/`)**  
   - Validates and converts the LLM’s high-level recommendations into strict JSON commands for Gains Network’s contracts.

4. **Trades Module (`trades/`)**  
   - Manages the database records for trades, including updates, closures, and historical logs.

5. **On‑Chain Execution Module (`onchain/`)**  
   - Interacts with Gains Network’s diamond contract on Base L2, handling wallet management, transaction signing, and on‑chain event monitoring.

A `common/` folder holds shared utilities like logging and configuration, while `docs/` and `tests/` store documentation and tests.

---

## Repository Structure

ggbot/ ├── docs/ # Documentation & reference ├── extraction/ # Extraction Module ├── decision/ # Decision & Monitoring Module ├── structuring/ # Structuring Module ├── trades/ # Trades Module ├── onchain/ # On-Chain Execution Module ├── common/ # Shared utilities (logger, config, etc.) ├── tests/ # Tests for each module ├── .gitignore ├── requirements.txt ├── README.md └── .env.example # Sample environment variables (e.g., API keys, RPC URLs)

yaml
Copy
Edit

---

## Installation & Setup

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/sevnightingale/ggbot.git
   cd ggbot
(Optional) Create a Python Virtual Environment

bash
Copy
Edit
python3 -m venv .venv
source .venv/bin/activate
This keeps dependencies isolated on your system.

Install Dependencies

bash
Copy
Edit
pip install -r requirements.txt
(Run this after requirements.txt is populated with the necessary libraries.)

Configure Environment Variables

Copy .env.example to .env:
bash
Copy
Edit
cp .env.example .env
Open .env and add your secrets (API keys, RPC URLs, private keys, etc.).
Do not commit your .env to version control.
Run or Develop

Each module (extraction, decision, structuring, trades, onchain) will have a main entry point or script for execution.
Tests are stored in the tests/ folder.
Key Project Documents
Master Plan: High-level vision and goals.
Pipeline: Detailed workflow for data extraction, decision-making, and on-chain execution.
Spec Sheet: Technical architecture and codebase structure.
Action Plan: Step-by-step tasks for building and deploying ggbot.
Contributing
Branch off main for any new feature or bug fix.
Commit changes with clear messages.
Push to GitHub and create a Pull Request.
Review and merge once approved.
License
No license has been chosen yet for ggbot.