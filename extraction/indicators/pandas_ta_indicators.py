"""
Pandas-TA Indicators Implementation

This module implements the IndicatorComputer interface using the pandas-ta library
for calculating various technical indicators based on OHLCV data.
"""
from typing import Dict, List, Any
import pandas as pd
import pandas_ta as ta

from common.logger import logger
from common.config import DEFAULT_USER_ID
from extraction.interfaces import IndicatorComputer


class PandasTAIndicators(IndicatorComputer):
    """
    Implementation of the IndicatorComputer interface using pandas-ta.
    
    This class calculates technical indicators like SMA, EMA, RSI, MACD, and Bollinger Bands
    using the pandas-ta library. It can be configured with different parameters for each indicator.
    """
    
    def __init__(self, config: Dict[str, Dict[str, Any]] = None):
        """
        Initialize the PandasTAIndicators with optional custom configuration.
        
        Args:
            config: Optional dictionary with indicator configurations.
                   If not provided, default configurations will be used.
                   
                   Example:
                   {
                       'sma': {'windows': [20, 50, 200]},
                       'ema': {'windows': [9, 21, 55]},
                       'rsi': {'length': 14},
                       'macd': {'fast': 12, 'slow': 26, 'signal': 9},
                       'bbands': {'length': 20, 'std': 2}
                   }
        """
        # Default configuration
        self._default_config = {
            'sma': {'windows': [20, 50, 200]},
            'ema': {'windows': [9, 21, 55]},
            'rsi': {'length': 14},
            'macd': {'fast': 12, 'slow': 26, 'signal': 9},
            'bbands': {'length': 20, 'std': 2}
        }
        
        # Use provided config or default
        self._config = config if config else self._default_config
        
        # Validate the configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate the configuration and ensure it has the required parameters."""
        required_indicators = ['sma', 'ema', 'rsi', 'macd', 'bbands']
        
        for indicator in required_indicators:
            if indicator not in self._config:
                logger.bind(user_id=DEFAULT_USER_ID).warning(f"Missing configuration for {indicator}, using defaults")
                self._config[indicator] = self._default_config[indicator]
        
        # Validate SMA configuration
        if 'windows' not in self._config['sma'] or not self._config['sma']['windows']:
            logger.bind(user_id=DEFAULT_USER_ID).warning("Invalid SMA configuration, using defaults")
            self._config['sma'] = self._default_config['sma']
        
        # Validate EMA configuration
        if 'windows' not in self._config['ema'] or not self._config['ema']['windows']:
            logger.bind(user_id=DEFAULT_USER_ID).warning("Invalid EMA configuration, using defaults")
            self._config['ema'] = self._default_config['ema']
        
        # Validate RSI configuration
        if 'length' not in self._config['rsi']:
            logger.bind(user_id=DEFAULT_USER_ID).warning("Invalid RSI configuration, using defaults")
            self._config['rsi'] = self._default_config['rsi']
        
        # Validate MACD configuration
        required_macd_params = ['fast', 'slow', 'signal']
        if not all(param in self._config['macd'] for param in required_macd_params):
            logger.bind(user_id=DEFAULT_USER_ID).warning("Invalid MACD configuration, using defaults")
            self._config['macd'] = self._default_config['macd']
        
        # Validate Bollinger Bands configuration
        required_bbands_params = ['length', 'std']
        if not all(param in self._config['bbands'] for param in required_bbands_params):
            logger.bind(user_id=DEFAULT_USER_ID).warning("Invalid Bollinger Bands configuration, using defaults")
            self._config['bbands'] = self._default_config['bbands']
    
    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for the given price data.
        
        Args:
            df: A pandas DataFrame containing OHLCV data
                (must have columns: Open, High, Low, Close, Volume)
            
        Returns:
            A pandas DataFrame with the original data plus calculated indicators
        """
        # Ensure we have the required columns
        required_columns = self.get_required_columns()
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Copy the DataFrame to avoid modifying the original
        result_df = df.copy()
        
        try:
            # Calculate SMA for each window
            for window in self._config['sma']['windows']:
                result_df[f'SMA_{window}'] = ta.sma(result_df['Close'], length=window)
            
            # Calculate EMA for each window
            for window in self._config['ema']['windows']:
                result_df[f'EMA_{window}'] = ta.ema(result_df['Close'], length=window)
            
            # Calculate RSI
            rsi_length = self._config['rsi']['length']
            result_df[f'RSI_{rsi_length}'] = ta.rsi(result_df['Close'], length=rsi_length)
            
            # Calculate MACD
            macd_config = self._config['macd']
            try:
                macd_result = ta.macd(
                    result_df['Close'],
                    fast=macd_config['fast'],
                    slow=macd_config['slow'],
                    signal=macd_config['signal']
                )
                
                # Check if macd_result is not None
                if macd_result is not None and not macd_result.empty:
                    # Rename MACD columns for clarity
                    macd_result.columns = [
                        f"MACD_{macd_config['fast']}_{macd_config['slow']}",
                        f"MACDh_{macd_config['fast']}_{macd_config['slow']}",
                        f"MACDs_{macd_config['fast']}_{macd_config['slow']}"
                    ]
                    result_df = pd.concat([result_df, macd_result], axis=1)
                else:
                    logger.bind(user_id=DEFAULT_USER_ID).warning("MACD calculation returned empty result")
            except Exception as e:
                logger.bind(user_id=DEFAULT_USER_ID).warning(f"Error calculating MACD: {str(e)}")
            
            # Calculate Bollinger Bands
            bbands_config = self._config['bbands']
            try:
                bbands_result = ta.bbands(
                    result_df['Close'],
                    length=bbands_config['length'],
                    std=bbands_config['std']
                )
                
                # Check if bbands_result is not None
                if bbands_result is not None and not bbands_result.empty:
                    # Rename Bollinger Bands columns for clarity
                    bb_length = bbands_config['length']
                    bb_std = bbands_config['std']
                    bbands_result.columns = [
                        f"BBL_{bb_length}_{bb_std}",
                        f"BBM_{bb_length}_{bb_std}",
                        f"BBU_{bb_length}_{bb_std}",
                        f"BBB_{bb_length}_{bb_std}",
                        f"BBP_{bb_length}_{bb_std}"
                    ]
                    result_df = pd.concat([result_df, bbands_result], axis=1)
                else:
                    logger.bind(user_id=DEFAULT_USER_ID).warning("Bollinger Bands calculation returned empty result")
            except Exception as e:
                logger.bind(user_id=DEFAULT_USER_ID).warning(f"Error calculating Bollinger Bands: {str(e)}")
            
            return result_df
        
        except Exception as e:
            logger.bind(user_id=DEFAULT_USER_ID).error(f"Error computing indicators: {str(e)}")
            # Return the original DataFrame if there's an error
            return df
    
    def get_indicator_names(self) -> List[str]:
        """
        Get a list of all indicators that this computer can calculate.
        
        Returns:
            A list of indicator names
        """
        indicator_names = []
        
        # SMA indicators
        for window in self._config['sma']['windows']:
            indicator_names.append(f"SMA_{window}")
        
        # EMA indicators
        for window in self._config['ema']['windows']:
            indicator_names.append(f"EMA_{window}")
        
        # RSI indicator
        rsi_length = self._config['rsi']['length']
        indicator_names.append(f"RSI_{rsi_length}")
        
        # MACD indicators
        macd_config = self._config['macd']
        indicator_names.extend([
            f"MACD_{macd_config['fast']}_{macd_config['slow']}",
            f"MACDh_{macd_config['fast']}_{macd_config['slow']}",
            f"MACDs_{macd_config['fast']}_{macd_config['slow']}"
        ])
        
        # Bollinger Bands indicators
        bbands_config = self._config['bbands']
        bb_length = bbands_config['length']
        bb_std = bbands_config['std']
        indicator_names.extend([
            f"BBL_{bb_length}_{bb_std}",
            f"BBM_{bb_length}_{bb_std}",
            f"BBU_{bb_length}_{bb_std}",
            f"BBB_{bb_length}_{bb_std}",
            f"BBP_{bb_length}_{bb_std}"
        ])
        
        return indicator_names
    
    def get_indicator_parameters(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the parameters used for each indicator.
        
        Returns:
            A dictionary mapping indicator names to their parameters
        """
        return self._config
    
    def get_required_columns(self) -> List[str]:
        """
        Get the required columns from the DataFrame for computing indicators.
        
        Returns:
            A list of required column names
        """
        return ['Open', 'High', 'Low', 'Close', 'Volume']