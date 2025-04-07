#!/bin/bash
# Script to run the scheduled extraction process

# Change to the project directory
cd /home/sev/ggbot

# Activate the Python virtual environment
source .venv/bin/activate

# Check if initialization flag exists
INIT_FLAG="/home/sev/ggbot/extraction/.initialized"

# If initialization hasn't been done yet, run it
if [ ! -f "$INIT_FLAG" ]; then
    echo "Running initial data extraction..."
    python -m extraction.scheduled_extraction --init
    
    # Create the initialization flag file
    touch "$INIT_FLAG"
    echo "Initialization complete and flag created"
else
    # Otherwise just update with new data
    echo "Running regular data update..."
    python -m extraction.scheduled_extraction --update
    
    # Always recalculate indicators on all data to ensure they're accurate
    echo "Recalculating indicators on all historical data..."
    python -m extraction.scheduled_extraction --indicators
fi

# Deactivate the virtual environment
deactivate