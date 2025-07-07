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
        
        # Always use a valid string for EXCHANGE_NAME
        # Default to 'binance' if nothing else is specified
        env = {'EXCHANGE_NAME': self.exchange_name or 'binance'}
        
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
            # Get tools from the session
            tools = await self.session.get_tools()
            
            # Handle different possible formats for tools
            indicator_tools = []
            
            # Process the tools to extract indicator names
            if isinstance(tools, list):
                for tool in tools:
                    name = None
                    if isinstance(tool, dict):
                        name = tool.get('name')
                    elif hasattr(tool, 'name'):
                        name = tool.name
                        
                    if name and 'calculate' in name.lower():
                        indicator_tools.append(name)
            else:
                self._log.warning(f"Unexpected tools format: {type(tools)}. Attempting to extract indicators anyway.")
                # Try to iterate through tools if possible
                try:
                    for tool in tools:
                        name = getattr(tool, 'name', None) or tool.get('name', '')
                        if name and 'calculate' in name.lower():
                            indicator_tools.append(name)
                except (TypeError, AttributeError) as e:
                    self._log.error(f"Could not extract tools: {str(e)}")
            
            return indicator_tools
        except Exception as e:
            self._log.error(f"Error getting available indicators: {str(e)}")
            raise MCPError(f"Error getting available indicators: {str(e)}")
    
    async def calculate_rsi(
        self,
        prices: List[float],
        period: int = 14,
        format: str = "preprocessed"
    ) -> Dict[str, Any]:
        """
        Calculate Relative Strength Index (RSI) for a series of prices.
        
        Args:
            prices: List of closing prices
            period: Period for RSI calculation
            format: Output format ('raw' for arrays, 'preprocessed' for contextual analysis)
            
        Returns:
            Dictionary containing RSI values or preprocessed analysis
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        try:
            # Use the full name as seen in the server
            result = await self.session.call_tool(
                'calculate_relative_strength_index',
                {
                    'prices': prices,
                    'period': period,
                    'format': format
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
            # Use the full name as seen in the server
            result = await self.session.call_tool(
                'calculate_moving_average_convergence_divergence',
                {
                    'prices': prices,
                    'fast_period': fast_period,
                    'slow_period': slow_period,
                    'signal_period': signal_period
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
                'calculate_bollinger_bands',
                {
                    'prices': prices,
                    'period': period,
                    'std_dev': std_dev
                }
            )
            return result
        except Exception as e:
            self._log.error(f"Error calculating Bollinger Bands: {str(e)}")
            raise MCPError(f"Error calculating Bollinger Bands: {str(e)}")
    
    async def calculate_stochastic(
        self,
        high_prices: List[float],
        low_prices: List[float],
        close_prices: List[float],
        k_period: int = 14,
        d_period: int = 3,
        smooth_k: int = 1
    ) -> Dict[str, Any]:
        """
        Calculate Stochastic Oscillator.
        
        The Stochastic Oscillator is a momentum indicator that shows the location of the close
        relative to the high-low range over a set number of periods.
        
        Args:
            high_prices: List of high prices
            low_prices: List of low prices
            close_prices: List of closing prices
            k_period: %K period
            d_period: %D period (moving average of %K)
            smooth_k: Smoothing for %K
            
        Returns:
            Dictionary containing k_values and d_values
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        try:
            result = await self.session.call_tool(
                'calculate_stochastic_oscillator',
                {
                    'high': high_prices,
                    'low': low_prices,
                    'close': close_prices,
                    'k_period': k_period,
                    'd_period': d_period,
                    'smooth_k': smooth_k
                }
            )
            return result
        except Exception as e:
            self._log.error(f"Error calculating Stochastic: {str(e)}")
            raise MCPError(f"Error calculating Stochastic: {str(e)}")
    
    async def calculate_atr(
        self,
        high_prices: List[float],
        low_prices: List[float],
        close_prices: List[float],
        period: int = 14
    ) -> Dict[str, Any]:
        """
        Calculate Average True Range (ATR).
        
        ATR is a volatility indicator that measures market volatility by
        decomposing the entire range of an asset price for a given period.
        
        Args:
            high_prices: List of high prices
            low_prices: List of low prices
            close_prices: List of closing prices
            period: Period for calculation
            
        Returns:
            Dictionary containing ATR values
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        try:
            result = await self.session.call_tool(
                'calculate_average_true_range',
                {
                    'high': high_prices,
                    'low': low_prices,
                    'close': close_prices,
                    'period': period
                }
            )
            return result
        except Exception as e:
            self._log.error(f"Error calculating ATR: {str(e)}")
            raise MCPError(f"Error calculating ATR: {str(e)}")
    
    async def calculate_ichimoku_cloud(
        self,
        high_prices: List[float],
        low_prices: List[float],
        close_prices: List[float],
        conversion_period: int = 9,
        base_period: int = 26,
        span_period: int = 52,
        displacement: int = 26
    ) -> Dict[str, Any]:
        """
        Calculate Ichimoku Cloud.
        
        The Ichimoku Cloud is a comprehensive indicator that shows support and resistance,
        momentum, and trend direction.
        
        Args:
            high_prices: List of high prices
            low_prices: List of low prices
            close_prices: List of closing prices
            conversion_period: Conversion line period (Tenkan-sen)
            base_period: Base line period (Kijun-sen)
            span_period: Span B line period
            displacement: Displacement period
            
        Returns:
            Dictionary containing Ichimoku components
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        try:
            result = await self.session.call_tool(
                'calculate_ichimoku_cloud',
                {
                    'high': high_prices,
                    'low': low_prices,
                    'close': close_prices,
                    'conversion_period': conversion_period,
                    'base_period': base_period,
                    'span_period': span_period,
                    'displacement': displacement
                }
            )
            return result
        except Exception as e:
            self._log.error(f"Error calculating Ichimoku Cloud: {str(e)}")
            raise MCPError(f"Error calculating Ichimoku Cloud: {str(e)}")
    
    async def calculate_williams_r(
        self,
        high_prices: List[float],
        low_prices: List[float],
        close_prices: List[float],
        period: int = 14
    ) -> Dict[str, Any]:
        """
        Calculate Williams %R.
        
        Williams %R is a momentum indicator that measures overbought and oversold levels,
        similar to the Stochastic oscillator.
        
        Args:
            high_prices: List of high prices
            low_prices: List of low prices
            close_prices: List of closing prices
            period: Period for calculation
            
        Returns:
            Dictionary containing Williams %R values
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        try:
            result = await self.session.call_tool(
                'calculate_williams_r',
                {
                    'high': high_prices,
                    'low': low_prices,
                    'close': close_prices,
                    'period': period
                }
            )
            return result
        except Exception as e:
            self._log.error(f"Error calculating Williams %R: {str(e)}")
            raise MCPError(f"Error calculating Williams %R: {str(e)}")
    
    async def calculate_ema(
        self,
        prices: List[float],
        period: int = 14
    ) -> Dict[str, Any]:
        """
        Calculate Exponential Moving Average (EMA).
        
        EMA places a greater weight and significance on the most recent data points.
        
        Args:
            prices: List of prices
            period: Period for calculation
            
        Returns:
            Dictionary containing EMA values
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        try:
            result = await self.session.call_tool(
                'calculate_exponential_moving_average',
                {
                    'prices': prices,
                    'period': period
                }
            )
            return result
        except Exception as e:
            self._log.error(f"Error calculating EMA: {str(e)}")
            raise MCPError(f"Error calculating EMA: {str(e)}")
    
    async def calculate_sma(
        self,
        prices: List[float],
        period: int = 14
    ) -> Dict[str, Any]:
        """
        Calculate Simple Moving Average (SMA).
        
        SMA calculates the average of price data over a specific period.
        
        Args:
            prices: List of prices
            period: Period for calculation
            
        Returns:
            Dictionary containing SMA values
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        try:
            result = await self.session.call_tool(
                'calculate_simple_moving_average',
                {
                    'prices': prices,
                    'period': period
                }
            )
            return result
        except Exception as e:
            self._log.error(f"Error calculating SMA: {str(e)}")
            raise MCPError(f"Error calculating SMA: {str(e)}")
    
    async def calculate_parabolic_sar(
        self,
        high_prices: List[float],
        low_prices: List[float],
        acceleration: float = 0.02,
        maximum: float = 0.2
    ) -> Dict[str, Any]:
        """
        Calculate Parabolic SAR (Stop and Reverse).
        
        Parabolic SAR is a technical indicator used to determine the direction of an asset's
        momentum and potential reversal points.
        
        Args:
            high_prices: List of high prices
            low_prices: List of low prices
            acceleration: Acceleration factor
            maximum: Maximum acceleration factor
            
        Returns:
            Dictionary containing SAR values
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        try:
            result = await self.session.call_tool(
                'calculate_parabolic_sar',
                {
                    'high': high_prices,
                    'low': low_prices,
                    'acceleration': acceleration,
                    'maximum': maximum
                }
            )
            return result
        except Exception as e:
            self._log.error(f"Error calculating Parabolic SAR: {str(e)}")
            raise MCPError(f"Error calculating Parabolic SAR: {str(e)}")
            
    async def calculate_vwap(
        self,
        high_prices: List[float],
        low_prices: List[float],
        close_prices: List[float],
        volume: List[float],
        period: int = 14
    ) -> Dict[str, Any]:
        """
        Calculate Volume Weighted Average Price (VWAP).
        
        VWAP is a trading benchmark that gives the average price a security has
        traded at throughout the day, based on both volume and price.
        
        Args:
            high_prices: List of high prices
            low_prices: List of low prices
            close_prices: List of closing prices
            volume: List of volume values
            period: Period for calculation
            
        Returns:
            Dictionary containing VWAP values
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        try:
            result = await self.session.call_tool(
                'calculate_volume_weighted_average_price',
                {
                    'high': high_prices,
                    'low': low_prices,
                    'close': close_prices,
                    'volume': volume,
                    'period': period
                }
            )
            return result
        except Exception as e:
            self._log.error(f"Error calculating VWAP: {str(e)}")
            raise MCPError(f"Error calculating VWAP: {str(e)}")
    
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
            # Adjust the strategy name to include the 'calculate_' prefix and '_strategy' suffix
            strategy_tool_name = f"calculate_{strategy}_strategy"
            result = await self.session.call_tool(
                strategy_tool_name,
                inputs
            )
            return result
        except Exception as e:
            self._log.error(f"Error analyzing with strategy {strategy}: {str(e)}")
            raise MCPError(f"Error analyzing with strategy {strategy}: {str(e)}")
            
    async def call_indicator_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        use_preprocessing: bool = True
    ) -> Dict[str, Any]:
        """
        Call any indicator tool with optional preprocessing.
        
        Args:
            tool_name: Name of the MCP tool to call
            params: Parameters for the tool
            use_preprocessing: Whether to use preprocessed format (default: True)
            
        Returns:
            Dictionary containing indicator results
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        # Add format parameter if not already specified
        if 'format' not in params and use_preprocessing:
            params['format'] = 'preprocessed'
        elif 'format' not in params:
            params['format'] = 'raw'
            
        try:
            result = await self.session.call_tool(tool_name, params)
            
            # Parse JSON if the result is a string (MCP returns JSON as text)
            if isinstance(result, str):
                try:
                    import json
                    result = json.loads(result)
                except (json.JSONDecodeError, ValueError):
                    # If it's not valid JSON, return as-is
                    pass
                    
            return result
        except Exception as e:
            self._log.error(f"Error calling {tool_name}: {str(e)}")
            raise MCPError(f"Error calling {tool_name}: {str(e)}")
    
    # Helper method to find the actual tool name from a partial name
    async def find_tool_by_partial_name(self, partial_name: str) -> Optional[str]:
        """
        Find a tool by partial name match.
        
        Args:
            partial_name: Partial name to search for
            
        Returns:
            Full tool name if found, None otherwise
        """
        if not self.is_connected or not self.session:
            await self.connect()
            
        tools = await self.get_available_indicators()
        
        for tool in tools:
            if partial_name.lower() in tool.lower():
                return tool
                
        return None