#!/usr/bin/env python
"""
Simple test to check available methods in the direct CCXT library for BitMEX.
This helps compare what's available in the full library vs. our MCP implementation.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import ccxt
try:
    import ccxt
except ImportError:
    print("CCXT library not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ccxt"])
    import ccxt

from core.common.logger import logger

# Configure logging
import logging
logger.configure(handlers=[{"sink": sys.stdout, "level": logging.INFO}])

def main():
    """Check available methods in the standard CCXT library for BitMEX."""
    logger.info("Checking standard CCXT library methods")
    
    # Initialize BitMEX exchange
    logger.info("Initializing BitMEX exchange")
    
    # Check if we have API credentials
    api_key = os.environ.get("EXCHANGE_API")
    api_secret = os.environ.get("EXCHANGE_SECRET")
    
    if api_key and api_secret:
        logger.info("Using API credentials from environment variables")
        bitmex = ccxt.bitmex({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'test': True  # Use testnet
        })
    else:
        logger.info("No API credentials found, initializing without authentication")
        bitmex = ccxt.bitmex({
            'enableRateLimit': True,
            'test': True  # Use testnet
        })
    
    # Get all available methods
    logger.info("Getting available methods from CCXT BitMEX instance")
    
    # Filter to get just the methods, not properties or internal methods
    methods = []
    for name in dir(bitmex):
        # Skip private/internal methods
        if name.startswith('_'):
            continue
        
        # Check if it's a method (callable)
        attr = getattr(bitmex, name)
        if callable(attr):
            methods.append(name)
    
    # Sort methods
    methods.sort()
    
    # Save methods to file
    logger.info(f"Found {len(methods)} methods in CCXT BitMEX")
    
    # Print methods related to positions
    position_methods = [m for m in methods if 'position' in m.lower()]
    logger.info(f"Position-related methods: {position_methods}")
    
    # Print methods related to trades
    trade_methods = [m for m in methods if 'trade' in m.lower()]
    logger.info(f"Trade-related methods: {trade_methods}")
    
    # Print all methods
    methods_path = Path(__file__).parent / "ccxt_direct_methods.txt"
    with open(methods_path, "w") as f:
        for method in methods:
            f.write(f"{method}\n")
    logger.info(f"Saved all methods to {methods_path}")
    
    # Save has_ flags to understand capabilities
    has_flags = {}
    if hasattr(bitmex, 'has'):
        has_flags = bitmex.has
    
    has_path = Path(__file__).parent / "ccxt_bitmex_capabilities.json"
    with open(has_path, "w") as f:
        json.dump(has_flags, f, indent=2)
    logger.info(f"Saved BitMEX capabilities to {has_path}")

if __name__ == "__main__":
    main()