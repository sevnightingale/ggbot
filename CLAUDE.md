# GGBot Development Guide

## Commands
- Setup: `pip install -r requirements.txt`
- Run test: `python -m tests.test_name`
- Run extraction: `python extraction/run_extraction.py`

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