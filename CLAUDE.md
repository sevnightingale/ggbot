# GGBot Development Guide

## Commands
- Setup: `pip install -r requirements.txt`
- Run test: `python -m tests.test_name`
- Run extraction: `python extraction/run_extraction.py`
- Note: When running Python commands for the ggbot project, always activate the virtual environment first. Use this sequence in the terminal as user 'sev' on the VM:
  1. Navigate to the project directory: cd /home/sev/ggbot
  2. Activate the virtual environment: source /home/sev/ggbot/.venv/bin/activate
  3. Run Python commands within the (.venv) prompt, e.g., 'python -m extraction.scheduled_extraction --update'
  The prompt should look like: (.venv) sev@ggbot-vm:~/ggbot$
  This ensures the correct Python interpreter and dependencies (e.g., yfinance, pandas-ta) are used.

## Code Style
- Imports: stdlib → third-party → local modules
- Naming: snake_case for variables/functions, PascalCase for classes, UPPER_SNAKE_CASE for constants
- Indentation: 4 spaces
- Docstrings: Triple double quotes with purpose and parameters
- Types: Follow PEP 484 type hints where possible
- Error handling: Use try/except with specific exceptions, log errors with common.logger

## Logging
- Import: `from common.logger import logger`
- Usage: `logger.bind(user_id="user_id").info("message")`
- Levels: INFO, WARNING, ERROR

## Database
- Connect via common.db utilities
- Always use context managers and close connections
- Migrations in database/ directory

## Browser Automation
- Playwright for browser automation
- Handle cookies properly (see extraction/run_extraction.py)

## Testing
- When creating test scripts, add them to the ggbot/tests/ directory.

## IMPORTANT
- You need to be methodical. Slow. Think hard. Ask questions. Don't make assumptions. We're working with very new tools with changing documentation. ANY TIME you think it might be helpful to look at the latest documenation, just say so! We'll find it for you and provide it.