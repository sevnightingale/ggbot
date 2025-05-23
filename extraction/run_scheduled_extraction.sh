#!/bin/bash
# Script to run the scheduled extraction process

# Change to the project directory
cd /home/sev/ggbot

# Activate the Python virtual environment
source .venv/bin/activate

# Parse arguments and collect them to pass to Python script
PYTHON_ARGS=""

for arg in "$@"; do
  case $arg in
    --init|--force|--update|--check-db|--indicators)
      PYTHON_ARGS="$PYTHON_ARGS $arg"
      shift
      ;;
    --symbols=*|--timeframes=*|--llm-model=*)
      PYTHON_ARGS="$PYTHON_ARGS $arg"
      shift
      ;;
  esac
done

# Default symbol and timeframe (using exchange format for direct MCP usage)
DEFAULT_SYMBOLS="BTC/USDT"
DEFAULT_TIMEFRAMES="1d 4h 1h 15m"
DEFAULT_LLM_MODEL="gpt-4o-mini"

# Run the extraction script with MCP indicators calculation
echo "Running MCP indicators extraction with LLM integration..."
python -m extraction.scheduled_extraction --indicators $PYTHON_ARGS --symbols $DEFAULT_SYMBOLS --timeframes $DEFAULT_TIMEFRAMES --llm-model $DEFAULT_LLM_MODEL

echo "Extraction complete!"

# Deactivate the virtual environment
deactivate