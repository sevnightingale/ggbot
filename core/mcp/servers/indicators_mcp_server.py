#!/usr/bin/env python
"""
Indicators MCP Server for ggbots.

This server exposes technical indicators and analysis tools via MCP.
"""

import logging
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[3]))

from mcp.server.fastmcp import FastMCP

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("indicators_mcp_server")

# Create MCP server
mcp = FastMCP("CryptoIndicators")

@mcp.tool()
def calculate_rsi(prices: list[float], period: int = 14) -> dict:
    """
    Calculate Relative Strength Index (RSI) for a series of prices.
    
    Args:
        prices: List of price values
        period: Period for RSI calculation
        
    Returns:
        Dictionary containing RSI values
    """
    import numpy as np
    from indicatorts import calculate_rsi as compute_rsi
    
    logger.info(f"Executing calculate_rsi with period={period}, prices length={len(prices)}")
    
    try:
        # Convert to numpy array for indicatorts
        prices_array = np.array(prices)
        rsi_values = compute_rsi(prices_array, period)
        
        # Convert numpy values to regular floats for JSON serialization
        values = [float(val) if not np.isnan(val) else None for val in rsi_values]
        
        return {"values": values}
    except Exception as e:
        logger.error(f"Error calculating RSI: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
def calculate_macd(prices: list[float], fast_period: int = 12, 
                   slow_period: int = 26, signal_period: int = 9) -> dict:
    """
    Calculate Moving Average Convergence Divergence (MACD) for a series of prices.
    
    Args:
        prices: List of price values
        fast_period: Fast period for MACD calculation
        slow_period: Slow period for MACD calculation
        signal_period: Signal period for MACD calculation
        
    Returns:
        Dictionary containing MACD line, signal line, and histogram values
    """
    import numpy as np
    from indicatorts import calculate_macd as compute_macd
    
    logger.info(f"Executing calculate_macd with parameters: fast={fast_period}, slow={slow_period}, signal={signal_period}")
    
    try:
        # Convert to numpy array for indicatorts
        prices_array = np.array(prices)
        macd_line, signal_line, histogram = compute_macd(prices_array, fast_period, slow_period, signal_period)
        
        # Convert numpy values to regular floats for JSON serialization
        macd_values = [float(val) if not np.isnan(val) else None for val in macd_line]
        signal_values = [float(val) if not np.isnan(val) else None for val in signal_line]
        hist_values = [float(val) if not np.isnan(val) else None for val in histogram]
        
        return {
            "macdLine": macd_values,
            "signalLine": signal_values,
            "histogram": hist_values
        }
    except Exception as e:
        logger.error(f"Error calculating MACD: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
def calculate_bollinger_bands(prices: list[float], period: int = 20, std_dev: float = 2.0) -> dict:
    """
    Calculate Bollinger Bands for a series of prices.
    
    Args:
        prices: List of price values
        period: Period for moving average
        std_dev: Number of standard deviations for band width
        
    Returns:
        Dictionary containing upper, middle, and lower band values
    """
    import numpy as np
    from indicatorts import calculate_bollinger_bands as compute_bb
    
    logger.info(f"Executing calculate_bollinger_bands with period={period}, std_dev={std_dev}")
    
    try:
        # Convert to numpy array for indicatorts
        prices_array = np.array(prices)
        upper, middle, lower = compute_bb(prices_array, period, std_dev)
        
        # Convert numpy values to regular floats for JSON serialization
        upper_values = [float(val) if not np.isnan(val) else None for val in upper]
        middle_values = [float(val) if not np.isnan(val) else None for val in middle]
        lower_values = [float(val) if not np.isnan(val) else None for val in lower]
        
        return {
            "upperBand": upper_values,
            "middleBand": middle_values,
            "lowerBand": lower_values
        }
    except Exception as e:
        logger.error(f"Error calculating Bollinger Bands: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
def calculate_sma(prices: list[float], period: int = 14) -> dict:
    """
    Calculate Simple Moving Average (SMA) for a series of prices.
    
    Args:
        prices: List of price values
        period: Period for SMA calculation
        
    Returns:
        Dictionary containing SMA values
    """
    import numpy as np
    from indicatorts import calculate_sma as compute_sma
    
    logger.info(f"Executing calculate_sma with period={period}")
    
    try:
        # Convert to numpy array for indicatorts
        prices_array = np.array(prices)
        sma_values = compute_sma(prices_array, period)
        
        # Convert numpy values to regular floats for JSON serialization
        values = [float(val) if not np.isnan(val) else None for val in sma_values]
        
        return {"values": values}
    except Exception as e:
        logger.error(f"Error calculating SMA: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
def calculate_ema(prices: list[float], period: int = 14) -> dict:
    """
    Calculate Exponential Moving Average (EMA) for a series of prices.
    
    Args:
        prices: List of price values
        period: Period for EMA calculation
        
    Returns:
        Dictionary containing EMA values
    """
    import numpy as np
    from indicatorts import calculate_ema as compute_ema
    
    logger.info(f"Executing calculate_ema with period={period}")
    
    try:
        # Convert to numpy array for indicatorts
        prices_array = np.array(prices)
        ema_values = compute_ema(prices_array, period)
        
        # Convert numpy values to regular floats for JSON serialization
        values = [float(val) if not np.isnan(val) else None for val in ema_values]
        
        return {"values": values}
    except Exception as e:
        logger.error(f"Error calculating EMA: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
def analyze_with_strategy(prices: list[float], strategy: str = "trend_following", 
                          params: dict = None) -> dict:
    """
    Analyze price data using a specific strategy.
    
    Args:
        prices: List of price values
        strategy: Name of the strategy to use
        params: Optional parameters for the strategy
        
    Returns:
        Dictionary containing analysis results and signal
    """
    import numpy as np
    from indicatorts import calculate_rsi, calculate_macd, calculate_sma, calculate_ema
    
    logger.info(f"Executing analyze_with_strategy with strategy={strategy}")
    
    if params is None:
        params = {}
    
    try:
        prices_array = np.array(prices)
        
        # Default response
        result = {
            "signal": "neutral",
            "strength": 0.0,
            "reasoning": "Unable to determine a clear signal"
        }
        
        # Trend following strategy
        if strategy == "trend_following":
            short_period = params.get("short_period", 9)
            long_period = params.get("long_period", 21)
            
            short_ma = calculate_sma(prices_array, short_period)
            long_ma = calculate_sma(prices_array, long_period)
            
            # Get most recent values
            short_val = short_ma[-1]
            long_val = long_ma[-1]
            
            if short_val > long_val:
                signal = "buy"
                strength = min(1.0, (short_val / long_val - 1) * 10)
                reasoning = f"Short MA ({short_val:.2f}) is above Long MA ({long_val:.2f})"
            elif short_val < long_val:
                signal = "sell"
                strength = min(1.0, (long_val / short_val - 1) * 10)
                reasoning = f"Short MA ({short_val:.2f}) is below Long MA ({long_val:.2f})"
            else:
                signal = "neutral"
                strength = 0.0
                reasoning = "No clear trend: short and long MAs are equal"
            
            result = {
                "signal": signal,
                "strength": float(strength),
                "reasoning": reasoning
            }
        
        # RSI strategy
        elif strategy == "rsi_oversold":
            rsi_period = params.get("period", 14)
            overbought = params.get("overbought", 70)
            oversold = params.get("oversold", 30)
            
            rsi_values = calculate_rsi(prices_array, rsi_period)
            rsi_val = rsi_values[-1]
            
            if rsi_val <= oversold:
                signal = "buy"
                strength = min(1.0, (oversold - rsi_val) / 10)
                reasoning = f"RSI ({rsi_val:.2f}) is in oversold territory (below {oversold})"
            elif rsi_val >= overbought:
                signal = "sell"
                strength = min(1.0, (rsi_val - overbought) / 10)
                reasoning = f"RSI ({rsi_val:.2f}) is in overbought territory (above {overbought})"
            else:
                signal = "neutral"
                strength = 0.0
                reasoning = f"RSI ({rsi_val:.2f}) is in neutral territory"
            
            result = {
                "signal": signal,
                "strength": float(strength),
                "reasoning": reasoning
            }
            
        return result
    except Exception as e:
        logger.error(f"Error analyzing with strategy: {str(e)}")
        return {
            "signal": "error",
            "strength": 0.0,
            "reasoning": f"Error: {str(e)}"
        }

if __name__ == "__main__":
    logger.info("Starting CryptoIndicators MCP server")
    
    # Log available tools for debugging
    registered_tools = [tool.__name__ for tool in getattr(mcp, '_tools', [])]
    logger.info(f"Registered tools: {registered_tools}")
    
    # Run the server
    mcp.run(transport="stdio")