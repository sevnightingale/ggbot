#!/usr/bin/env python3
"""
Configuration insertion template for the ggbot database.
Modify this script to create new configurations as needed.
"""
import asyncio
import uuid
import json
from datetime import datetime
import asyncpg
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parents[2]
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

# ========================================================================
# MODIFY THIS SECTION TO CREATE YOUR CONFIGURATION
# ========================================================================

# Configuration name (must be unique)
CONFIG_NAME = "All Indicators Test - 53"

# Configuration type
CONFIG_TYPE = "testing"  # Options: testing, production, ggshot, specialized

# Indicators to include
INDICATORS = [
    # Trend Indicators (24)
    "AbsolutePriceOscillator", "Aroon", "BalanceOfPower", "ChandeForecastOscillator",
    "CCI", "DEMA", "EMA", "MassIndex", "MACD", "MovingMax", "MovingMin", 
    "MovingSum", "ParabolicSAR", "Qstick", "KDJ", "RollingMovingAverage",
    "SMA", "SinceChange", "TEMA", "TriangularMovingAverage", 
    "TripleExponentialAverage", "TypicalPrice", "VolumeWeightedMovingAverage", "Vortex",
    
    # Momentum Indicators (9)
    "AwesomeOscillator", "ChaikinOscillator", "IchimokuCloud", "PercentagePriceOscillator",
    "PercentageVolumeOscillator", "ROC", "RSI", "Stochastic", "WilliamsR",
    
    # Volatility Indicators (11)
    "AccelerationBands", "ATR", "BollingerBands", "BollingerBandsWidth",
    "ChandelierExit", "DonchianChannel", "KeltnerChannel", "MovingStandardDeviation",
    "ProjectionOscillator", "TrueRange", "UlcerIndex",
    
    # Volume Indicators (9)
    "AccumulationDistribution", "ChaikinMoneyFlow", "EaseOfMovement", "ForceIndex",
    "MFI", "NegativeVolumeIndex", "OBV", "VolumePriceTrend", "VWAP"
]

# Symbols and timeframes
SYMBOLS = ["BTC/USDT"]
TIMEFRAMES = ["1h"]

# Decision strategy
STRATEGY = "Comprehensive technical analysis using all 53 available indicators for complete testing and validation."

# ========================================================================
# DO NOT MODIFY BELOW UNLESS YOU KNOW WHAT YOU'RE DOING
# ========================================================================

CONFIG_DATA = {
    "user_id": "00000000-0000-0000-0000-000000000001",
    "mcp": {
        "ccxt": {
            "enabled": True,
            "config_path": "core/config/ccxt-accounts.json",
            "default_exchange": "bitmex"
        },
        "indicators": {
            "enabled": True,
            "script_path": "core/mcp/servers/crypto-indicators-mcp/index.js",
            "exchange_name": "binance"
        }
    },
    "extraction": {
        "symbols": SYMBOLS,
        "timeframes": TIMEFRAMES,
        "sources": {
            "crypto_indicators_mcp": {
                "enabled": True,
                "indicators": INDICATORS,
                "use_llm_selection": False,
                "llm_interpretation": True,
                "llm_model": "gpt-4o-mini"
            },
            "tradingview": {
                "enabled": False,
                "strategy": ""
            },
            "yfinance": {
                "enabled": False
            },
            "telegram": {
                "enabled": False,
                "channels": [],
                "signal_types": [],
                "store_raw_messages": False
            },
            "news_feed": {
                "enabled": False,
                "sources": []
            }
        }
    },
    "decision": {
        "llm_provider": "default",
        "system_prompt": "",
        "strategy": STRATEGY,
        "additional_context": f"Configuration with {len(INDICATORS)} indicators for {CONFIG_TYPE} purposes"
    },
    "trading": {
        "exchange": "ccxt_mcp",
        "exchange_id": "bitmex",
        "authentication": "api_key",
        "risk_rules": {
            "max_leverage": 10,
            "max_position_size_pct": 0.03,
            "max_risk_per_trade_pct": 0.02,
            "min_equity_protection": 0.8,
            "max_contracts_per_trade": 1000000
        }
    }
}

async def insert_config():
    """Insert the configuration into the database."""
    
    # Always generate a new UUID for the config
    config_id = uuid.uuid4()
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    # Database connection using environment variables
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    
    if not all([db_host, db_port, db_name, db_user, db_pass]):
        raise ValueError("Missing required database environment variables: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS")
    
    conn = await asyncpg.connect(
        host=db_host,
        port=int(db_port),
        database=db_name,
        user=db_user,
        password=db_pass
    )
    
    try:
        # Always insert as new configuration (never update)
        await conn.execute(
            """
            INSERT INTO configurations (config_id, user_id, config_type, config_name, config_data, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            config_id,
            user_id,
            CONFIG_TYPE,
            CONFIG_NAME,
            json.dumps(CONFIG_DATA),
            datetime.utcnow(),
            datetime.utcnow()
        )
        
        print("✅ Created new configuration!")
        print(f"📋 Name: {CONFIG_NAME}")
        print(f"🆔 Type: {CONFIG_TYPE}")
        print(f"📊 Indicators: {len(INDICATORS)}")
        print(f"🎯 Symbols: {', '.join(SYMBOLS)}")
        print(f"⏱️  Timeframes: {', '.join(TIMEFRAMES)}")
        
        # Verify insertion
        result = await conn.fetchrow(
            "SELECT config_id, config_name, created_at FROM configurations WHERE config_id = $1",
            config_id
        )
        
        if result:
            print(f"\n✅ Verified: Configuration created at {result['created_at']}")
        
        print(f"\n{'='*60}")
        print("🔥 COPY THIS CONFIG ID:")
        print(f"{'='*60}")
        print(f"{config_id}")
        print(f"{'='*60}")
        
        return config_id
        
    finally:
        await conn.close()

if __name__ == "__main__":
    config_id = asyncio.run(insert_config())
    print(f"\n💡 To use this configuration:")
    print(f"   await extract_mcp_indicators(")
    print(f"       symbols={SYMBOLS},")
    print(f"       timeframes={TIMEFRAMES},")
    print(f"       config_id='{config_id}'")
    print(f"   )")
    print(f"\n⚠️  Cost warning: This will make {len(INDICATORS)} LLM calls!")