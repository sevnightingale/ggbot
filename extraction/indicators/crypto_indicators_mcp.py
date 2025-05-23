"""
CryptoIndicatorsMCP implementation.

This module provides an IndicatorComputer implementation that uses the Crypto Indicators MCP
to calculate technical indicators for price data.
"""

import json
import asyncio
import pandas as pd
from typing import Dict, List, Any

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from core.mcp.indicators import IndicatorsMCPClient
from extraction.interfaces.indicator_computer import IndicatorComputer


class CryptoIndicatorsMCP(IndicatorComputer):
    """
    IndicatorComputer implementation that uses the Crypto Indicators MCP
    to calculate technical indicators.
    
    This replaces the pandas-ta based indicator calculations with MCP-based
    calculations, leveraging the standardized MCP interface for indicator computation.
    """
    
    def __init__(self, user_id=DEFAULT_USER_ID, exchange_name="binance"):
        """
        Initialize the CryptoIndicatorsMCP calculator.
        
        Args:
            user_id: User ID to associate with this indicator computer
            exchange_name: Name of the exchange to use for data (default: binance)
        """
        self.user_id = user_id
        self.exchange_name = exchange_name
        self.mcp_client = None
        self._log = logger.bind(user_id=user_id, component="CryptoIndicatorsMCP")
        
        # Define the indicators and their parameters
        self.indicator_params = {
            'RSI_14': {'period': 14},
            'MACD_12_26_9': {'fastPeriod': 12, 'slowPeriod': 26, 'signalPeriod': 9},
            'BB_20_2': {'period': 20, 'stdDev': 2.0},
            'SMA_20': {'period': 20},
            'SMA_50': {'period': 50},
            'SMA_200': {'period': 200},
            'EMA_9': {'period': 9},
            'EMA_21': {'period': 21},
            'EMA_55': {'period': 55}
        }
        
    async def _ensure_client_connected(self):
        """
        Ensure the MCP client is connected.
        
        Creates a new client if one doesn't exist, or reconnects an existing client.
        """
        if not self.mcp_client:
            self._log.info(f"Creating new Indicators MCP client for {self.exchange_name}")
            self.mcp_client = IndicatorsMCPClient(
                user_id=self.user_id,
                exchange_name=self.exchange_name
            )
            await self.mcp_client.connect()
        elif not self.mcp_client.is_connected:
            self._log.info(f"Reconnecting existing Indicators MCP client")
            await self.mcp_client.connect()
    
    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for the given price data.
        
        This is a synchronous wrapper that runs the async computation in a new event loop.
        
        Args:
            df: DataFrame containing OHLCV price data
            
        Returns:
            DataFrame with added indicator columns
        """
        self._log.info("Computing indicators using Crypto Indicators MCP")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Run the async computation in the event loop
            return loop.run_until_complete(self._compute_indicators_async(df))
        finally:
            # Clean up the event loop
            loop.close()
    
    async def _compute_indicators_async(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Asynchronously calculate technical indicators via the MCP.
        
        Args:
            df: DataFrame containing OHLCV price data
            
        Returns:
            DataFrame with added indicator columns
        """
        if df.empty:
            self._log.warning("Empty DataFrame provided, cannot compute indicators")
            return df
            
        # Ensure the required columns exist
        required_columns = self.get_required_columns()
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            self._log.error(f"Missing required columns: {missing}")
            return df
            
        try:
            # Ensure the MCP client is connected
            await self._ensure_client_connected()
            
            # Create a copy of the DataFrame
            result_df = df.copy()
            
            # Extract prices for indicators - handle both capitalized and lowercase column names
            close_prices = df['Close'].tolist() if 'Close' in df.columns else df['close'].tolist()
            
            # Add symbol information for MCP tool calls
            # Try to extract symbol from DataFrame or use a default
            symbol = "BTC/USDT"  # Default symbol

            # Try different ways to get the symbol from the DataFrame
            if 'Symbol' in df.columns and len(df) > 0:
                symbol = df['Symbol'].iloc[0]
            elif 'symbol' in df.columns and len(df) > 0:
                symbol = df['symbol'].iloc[0]

            # Convert symbol format from yfinance (BTC-USD) to MCP (BTC/USDT) if needed
            if '-' in symbol:
                base, quote = symbol.split('-')
                # Map USD to USDT for proper exchange processing
                quote = 'USDT' if quote == 'USD' else quote
                symbol = f"{base}/{quote}"
                self._log.info(f"Converted symbol from yfinance format to MCP format: {symbol}")
            
            # Same for timeframe
            timeframe = "1h"  # Default timeframe
            if 'Timeframe' in df.columns and len(df) > 0:
                timeframe = df['Timeframe'].iloc[0]
            elif 'timeframe' in df.columns and len(df) > 0:
                timeframe = df['timeframe'].iloc[0]
            
            self._log.info(f"Calculating indicators for {symbol} on {timeframe} timeframe")
            
            # Calculate RSI
            try:
                rsi_period = self.indicator_params['RSI_14']['period']
                self._log.info(f"Calculating RSI with period={rsi_period}")
                rsi_result = await self.mcp_client.calculate_rsi(
                    prices=close_prices,
                    period=rsi_period,
                    symbol=symbol,
                    timeframe=timeframe
                )
                
                # Handle different possible response formats
                if isinstance(rsi_result, dict):
                    if 'values' in rsi_result:
                        result_df['RSI_14'] = pd.Series(rsi_result['values'], index=df.index)
                    elif 'content' in rsi_result and len(rsi_result['content']) > 0:
                        # Parse JSON from content if it's in that format
                        content_text = rsi_result['content'][0].get('text', '')
                        if content_text:
                            try:
                                content_data = json.loads(content_text)
                                result_df['RSI_14'] = pd.Series(content_data, index=df.index)
                            except json.JSONDecodeError:
                                self._log.warning(f"Failed to parse RSI response: {content_text}")
                elif isinstance(rsi_result, str):
                    # Try to parse a JSON string
                    try:
                        rsi_data = json.loads(rsi_result)
                        if isinstance(rsi_data, dict) and 'values' in rsi_data:
                            result_df['RSI_14'] = pd.Series(rsi_data['values'], index=df.index)
                    except json.JSONDecodeError:
                        self._log.warning(f"Failed to parse RSI string response: {rsi_result[:100]}...")
            except Exception as e:
                self._log.error(f"Error calculating RSI: {str(e)}")
            
            # Calculate MACD
            try:
                fast_period = self.indicator_params['MACD_12_26_9']['fastPeriod']
                slow_period = self.indicator_params['MACD_12_26_9']['slowPeriod']
                signal_period = self.indicator_params['MACD_12_26_9']['signalPeriod']
                
                self._log.info(f"Calculating MACD with fast={fast_period}, slow={slow_period}, signal={signal_period}")
                macd_result = await self.mcp_client.calculate_macd(
                    prices=close_prices,
                    fast_period=fast_period,
                    slow_period=slow_period,
                    signal_period=signal_period,
                    symbol=symbol,
                    timeframe=timeframe
                )
                
                # Process MACD result
                if isinstance(macd_result, dict):
                    # Different possible key names in the response
                    macd_line_key = next((k for k in ['macdLine', 'macd', 'macd_line'] if k in macd_result), None)
                    signal_line_key = next((k for k in ['signalLine', 'signal', 'signal_line'] if k in macd_result), None)
                    histogram_key = next((k for k in ['histogram', 'hist'] if k in macd_result), None)
                    
                    if macd_line_key:
                        result_df['MACD_Line'] = pd.Series(macd_result[macd_line_key], index=df.index)
                    if signal_line_key:
                        result_df['MACD_Signal'] = pd.Series(macd_result[signal_line_key], index=df.index)
                    if histogram_key:
                        result_df['MACD_Histogram'] = pd.Series(macd_result[histogram_key], index=df.index)
                elif isinstance(macd_result, str):
                    # Try to parse a JSON string
                    try:
                        macd_data = json.loads(macd_result)
                        # Handle different possible key structures
                        if isinstance(macd_data, dict):
                            macd_line_key = next((k for k in ['macdLine', 'macd', 'macd_line'] if k in macd_data), None)
                            signal_line_key = next((k for k in ['signalLine', 'signal', 'signal_line'] if k in macd_data), None)
                            histogram_key = next((k for k in ['histogram', 'hist'] if k in macd_data), None)
                            
                            if macd_line_key:
                                result_df['MACD_Line'] = pd.Series(macd_data[macd_line_key], index=df.index)
                            if signal_line_key:
                                result_df['MACD_Signal'] = pd.Series(macd_data[signal_line_key], index=df.index)
                            if histogram_key:
                                result_df['MACD_Histogram'] = pd.Series(macd_data[histogram_key], index=df.index)
                    except json.JSONDecodeError:
                        self._log.warning(f"Failed to parse MACD string response: {macd_result[:100]}...")
            except Exception as e:
                self._log.error(f"Error calculating MACD: {str(e)}")
            
            # Calculate Bollinger Bands
            try:
                bb_period = self.indicator_params['BB_20_2']['period']
                bb_stddev = self.indicator_params['BB_20_2']['stdDev']
                
                self._log.info(f"Calculating Bollinger Bands with period={bb_period}, stdDev={bb_stddev}")
                bb_result = await self.mcp_client.calculate_bollinger_bands(
                    prices=close_prices,
                    period=bb_period,
                    std_dev=bb_stddev,
                    symbol=symbol,
                    timeframe=timeframe
                )
                
                # Process Bollinger Bands result
                if isinstance(bb_result, dict):
                    upper_key = next((k for k in ['upperBand', 'upper', 'upper_band'] if k in bb_result), None)
                    middle_key = next((k for k in ['middleBand', 'middle', 'middle_band', 'sma'] if k in bb_result), None)
                    lower_key = next((k for k in ['lowerBand', 'lower', 'lower_band'] if k in bb_result), None)
                    
                    if upper_key:
                        result_df['BB_Upper'] = pd.Series(bb_result[upper_key], index=df.index)
                    if middle_key:
                        result_df['BB_Middle'] = pd.Series(bb_result[middle_key], index=df.index)
                    if lower_key:
                        result_df['BB_Lower'] = pd.Series(bb_result[lower_key], index=df.index)
                elif isinstance(bb_result, str):
                    # Try to parse a JSON string
                    try:
                        bb_data = json.loads(bb_result)
                        if isinstance(bb_data, dict):
                            upper_key = next((k for k in ['upperBand', 'upper', 'upper_band'] if k in bb_data), None)
                            middle_key = next((k for k in ['middleBand', 'middle', 'middle_band', 'sma'] if k in bb_data), None)
                            lower_key = next((k for k in ['lowerBand', 'lower', 'lower_band'] if k in bb_data), None)
                            
                            if upper_key:
                                result_df['BB_Upper'] = pd.Series(bb_data[upper_key], index=df.index)
                            if middle_key:
                                result_df['BB_Middle'] = pd.Series(bb_data[middle_key], index=df.index)
                            if lower_key:
                                result_df['BB_Lower'] = pd.Series(bb_data[lower_key], index=df.index)
                    except json.JSONDecodeError:
                        self._log.warning(f"Failed to parse BB string response: {bb_result[:100]}...")
            except Exception as e:
                self._log.error(f"Error calculating Bollinger Bands: {str(e)}")
            
            # Calculate SMAs
            for param_name, params in self.indicator_params.items():
                if param_name.startswith('SMA_'):
                    try:
                        period = params['period']
                        self._log.info(f"Calculating SMA with period={period}")
                        sma_result = await self.mcp_client.calculate_sma(
                            prices=close_prices,
                            period=period,
                            symbol=symbol,
                            timeframe=timeframe
                        )
                        
                        # Process SMA result
                        if isinstance(sma_result, dict) and 'values' in sma_result:
                            result_df[param_name] = pd.Series(sma_result['values'], index=df.index)
                        elif isinstance(sma_result, str):
                            # Try to parse a JSON string
                            try:
                                sma_data = json.loads(sma_result)
                                if isinstance(sma_data, dict) and 'values' in sma_data:
                                    result_df[param_name] = pd.Series(sma_data['values'], index=df.index)
                            except json.JSONDecodeError:
                                self._log.warning(f"Failed to parse SMA string response: {sma_result[:100]}...")
                    except Exception as e:
                        self._log.error(f"Error calculating SMA_{period}: {str(e)}")
            
            # Calculate EMAs
            for param_name, params in self.indicator_params.items():
                if param_name.startswith('EMA_'):
                    try:
                        period = params['period']
                        self._log.info(f"Calculating EMA with period={period}")
                        ema_result = await self.mcp_client.calculate_ema(
                            prices=close_prices,
                            period=period,
                            symbol=symbol,
                            timeframe=timeframe
                        )
                        
                        # Process EMA result
                        if isinstance(ema_result, dict) and 'values' in ema_result:
                            result_df[param_name] = pd.Series(ema_result['values'], index=df.index)
                        elif isinstance(ema_result, str):
                            # Try to parse a JSON string
                            try:
                                ema_data = json.loads(ema_result)
                                if isinstance(ema_data, dict) and 'values' in ema_data:
                                    result_df[param_name] = pd.Series(ema_data['values'], index=df.index)
                            except json.JSONDecodeError:
                                self._log.warning(f"Failed to parse EMA string response: {ema_result[:100]}...")
                    except Exception as e:
                        self._log.error(f"Error calculating EMA_{period}: {str(e)}")
            
            self._log.info(f"Indicator calculation complete - calculated {len(result_df.columns) - len(df.columns)} indicators")
            
            return result_df
            
        except Exception as e:
            self._log.error(f"Error during indicator calculation process: {str(e)}")
            # Return the original DataFrame if any error occurs
            return df
        finally:
            # Ensure we clean up the MCP client
            if self.mcp_client and self.mcp_client.is_connected:
                try:
                    await self.mcp_client.disconnect()
                    self._log.info("Disconnected from Indicators MCP server")
                except Exception as e:
                    self._log.error(f"Error disconnecting from MCP: {str(e)}")
    
    def get_indicator_names(self) -> List[str]:
        """Get a list of all indicators that this computer can calculate."""
        return list(self.indicator_params.keys()) + ['MACD_Line', 'MACD_Signal', 'MACD_Histogram', 
                                                   'BB_Upper', 'BB_Middle', 'BB_Lower']
    
    def get_indicator_parameters(self) -> Dict[str, Dict[str, Any]]:
        """Get the parameters used for each indicator."""
        return self.indicator_params
    
    def get_required_columns(self) -> List[str]:
        """Get the required columns from the DataFrame for computing indicators."""
        return ['Open', 'High', 'Low', 'Close', 'Volume']