"""
Crypto Indicators MCP client module.

This module provides a specialized client for connecting to the Crypto Indicators MCP
server, which enables computation of technical indicators for cryptocurrency data.
"""

import os
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from core.common.config import DEFAULT_USER_ID
from core.common.logger import logger
from core.mcp.client import MCPClient
from core.mcp.exceptions import MCPError
from core.mcp.session import MCPSession
from core.mcp.config import get_mcp_config, get_indicators_mcp_script_path


class IndicatorsMCPClient(MCPClient):
    """
    Client for interacting with the Crypto Indicators MCP server.
    
    This client provides specialized functionality for:
    - Computing technical indicators (RSI, MACD, etc.)
    - Analyzing price data with various strategies
    - Generating trading signals
    """
    
    def __init__(
        self,
        script_path: Optional[str] = None,
        exchange_name: Optional[str] = None,
        user_id: Optional[str] = None,
        connection_timeout: int = 30
    ):
        """
        Initialize the Crypto Indicators MCP client.
        
        Args:
            script_path: Path to the Crypto Indicators MCP script
            exchange_name: Name of the exchange to use for data
            user_id: User ID to associate with this client
            connection_timeout: Timeout in seconds for connection attempts
        """
        self.user_id = user_id or DEFAULT_USER_ID
        
        # Get config from configuration system
        mcp_config = get_mcp_config('indicators', self.user_id)
        
        # Use provided script_path or get from configuration
        self.script_path = script_path or mcp_config.get('script_path')
        
        # If still not set, use default
        if not self.script_path:
            self.script_path = os.path.join(
                str(Path(__file__).parents[1]),  # core directory
                'mcp', 'servers', 'crypto-indicators-mcp', 'index.js'
            )
            
        # Use provided exchange_name or get from configuration
        self.exchange_name = exchange_name or mcp_config.get('exchange_name', 'binance')
        
        # Ensure the script file exists
        if not os.path.exists(self.script_path):
            raise FileNotFoundError(
                f"Crypto Indicators MCP script not found at {self.script_path}"
            )
        
        command = 'node'
        args = [self.script_path]
        env = {'EXCHANGE_NAME': exchange_name}
        
        super().__init__(
            server_name='Crypto Indicators',
            command=command,
            args=args,
            env=env,
            user_id=self.user_id,
            connection_timeout=connection_timeout
        )
        
        self._log = logger.bind(user_id=self.user_id)
    
    async def get_available_indicators(self) -> List[str]:
        """
        Get a list of all available technical indicators.
        
        Returns:
            List of indicator names
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        try:
            tools = await self.session.get_tools()
            indicator_tools = [
                tool['name'] for tool in tools 
                if tool.get('name') and 'calculate' in tool.get('name', '').lower()
            ]
            return indicator_tools
        except Exception as e:
            self._log.error(f"Error getting available indicators: {str(e)}")
            raise MCPError(f"Error getting available indicators: {str(e)}")
    
    async def calculate_rsi(
        self,
        prices: List[float],
        period: int = 14
    ) -> Dict[str, Any]:
        """
        Calculate Relative Strength Index (RSI) for a series of prices.
        
        Args:
            prices: List of closing prices
            period: Period for RSI calculation
            
        Returns:
            Dictionary containing RSI values
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        try:
            result = await self.session.call_tool(
                'calculateRSI',
                {
                    'prices': prices,
                    'period': period
                }
            )
            return result
        except Exception as e:
            self._log.error(f"Error calculating RSI: {str(e)}")
            raise MCPError(f"Error calculating RSI: {str(e)}")
    
    async def calculate_macd(
        self,
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Dict[str, Any]:
        """
        Calculate Moving Average Convergence Divergence (MACD) for a series of prices.
        
        Args:
            prices: List of closing prices
            fast_period: Fast period for MACD calculation
            slow_period: Slow period for MACD calculation
            signal_period: Signal period for MACD calculation
            
        Returns:
            Dictionary containing MACD line, signal line, and histogram values
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        try:
            result = await self.session.call_tool(
                'calculateMACD',
                {
                    'prices': prices,
                    'fastPeriod': fast_period,
                    'slowPeriod': slow_period,
                    'signalPeriod': signal_period
                }
            )
            return result
        except Exception as e:
            self._log.error(f"Error calculating MACD: {str(e)}")
            raise MCPError(f"Error calculating MACD: {str(e)}")
    
    async def calculate_bollinger_bands(
        self,
        prices: List[float],
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, Any]:
        """
        Calculate Bollinger Bands for a series of prices.
        
        Args:
            prices: List of closing prices
            period: Period for moving average calculation
            std_dev: Number of standard deviations for bands
            
        Returns:
            Dictionary containing upper band, middle band, and lower band values
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        try:
            result = await self.session.call_tool(
                'calculateBollingerBands',
                {
                    'prices': prices,
                    'period': period,
                    'stdDev': std_dev
                }
            )
            return result
        except Exception as e:
            self._log.error(f"Error calculating Bollinger Bands: {str(e)}")
            raise MCPError(f"Error calculating Bollinger Bands: {str(e)}")
    
    async def analyze_with_strategy(
        self,
        prices: List[float],
        strategy: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze price data using a specific strategy.
        
        Args:
            prices: List of closing prices
            strategy: Name of the strategy to use
            params: Optional parameters for the strategy
            
        Returns:
            Dictionary containing strategy analysis results
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        inputs = {
            'prices': prices,
            'strategy': strategy
        }
        
        if params:
            inputs.update(params)
            
        try:
            result = await self.session.call_tool(
                'analyzeWithStrategy',
                inputs
            )
            return result
        except Exception as e:
            self._log.error(f"Error analyzing with strategy {strategy}: {str(e)}")
            raise MCPError(f"Error analyzing with strategy {strategy}: {str(e)}")