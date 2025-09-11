"""
Modular Technical Analysis Preprocessors.

This package contains individual preprocessor modules for each technical indicator,
providing professional-grade analysis with sophisticated pattern recognition,
signal generation, and confidence scoring.
"""

from .rsi import RSIPreprocessor

# Import core preprocessors with error handling
try:
    from .macd import MACDPreprocessor
except ImportError:
    MACDPreprocessor = None

try:
    from .stochastic import StochasticPreprocessor
except ImportError:
    StochasticPreprocessor = None

# Import additional preprocessors as they are implemented
try:
    from .williams_r import WilliamsRPreprocessor
except ImportError:
    WilliamsRPreprocessor = None

try:
    from .cci import CCIPreprocessor
except ImportError:
    CCIPreprocessor = None

try:
    from .mfi import MFIPreprocessor
except ImportError:
    MFIPreprocessor = None

try:
    from .adx import ADXPreprocessor
except ImportError:
    ADXPreprocessor = None

try:
    from .psar import ParabolicSARPreprocessor
except ImportError:
    ParabolicSARPreprocessor = None

try:
    from .aroon import AroonPreprocessor
except ImportError:
    AroonPreprocessor = None

try:
    from .atr import ATRPreprocessor
except ImportError:
    ATRPreprocessor = None

try:
    from .bbands import BollingerBandsPreprocessor
except ImportError:
    BollingerBandsPreprocessor = None

try:
    from .obv import OBVPreprocessor
except ImportError:
    OBVPreprocessor = None

try:
    from .sma import SMAPreprocessor
except ImportError:
    SMAPreprocessor = None

try:
    from .ema import EMAPreprocessor
except ImportError:
    EMAPreprocessor = None

try:
    from .roc import ROCPreprocessor
except ImportError:
    ROCPreprocessor = None

try:
    from .vwap import VWAPPreprocessor
except ImportError:
    VWAPPreprocessor = None

try:
    from .trix import TRIXPreprocessor
except ImportError:
    TRIXPreprocessor = None

try:
    from .vortex import VortexPreprocessor
except ImportError:
    VortexPreprocessor = None

try:
    from .bbwidth import BollingerWidthPreprocessor
except ImportError:
    BollingerWidthPreprocessor = None

try:
    from .keltner import KeltnerChannelsPreprocessor
except ImportError:
    KeltnerChannelsPreprocessor = None

try:
    from .donchian import DonchianChannelsPreprocessor
except ImportError:
    DonchianChannelsPreprocessor = None


class PreprocessorFactory:
    """Factory class for creating indicator preprocessors."""
    
    def __init__(self):
        """Initialize the preprocessor factory."""
        self._preprocessors = {}
        self._register_preprocessors()
    
    def _register_preprocessors(self):
        """Register all available preprocessors."""
        # Core preprocessors (always available)
        self._preprocessors['rsi'] = RSIPreprocessor()
        
        # Core preprocessors with safety checks
        if MACDPreprocessor:
            self._preprocessors['macd'] = MACDPreprocessor()
        
        if StochasticPreprocessor:
            self._preprocessors['stochastic'] = StochasticPreprocessor()
        
        # Optional preprocessors (if implemented)
        if WilliamsRPreprocessor:
            self._preprocessors['williams_r'] = WilliamsRPreprocessor()
        
        if CCIPreprocessor:
            self._preprocessors['cci'] = CCIPreprocessor()
        
        if MFIPreprocessor:
            self._preprocessors['mfi'] = MFIPreprocessor()
        
        if ADXPreprocessor:
            self._preprocessors['adx'] = ADXPreprocessor()
        
        if ParabolicSARPreprocessor:
            self._preprocessors['psar'] = ParabolicSARPreprocessor()
        
        if AroonPreprocessor:
            self._preprocessors['aroon'] = AroonPreprocessor()
        
        if ATRPreprocessor:
            self._preprocessors['atr'] = ATRPreprocessor()
        
        if BollingerBandsPreprocessor:
            self._preprocessors['bbands'] = BollingerBandsPreprocessor()
        
        if OBVPreprocessor:
            self._preprocessors['obv'] = OBVPreprocessor()
        
        if SMAPreprocessor:
            self._preprocessors['sma'] = SMAPreprocessor()
        
        if EMAPreprocessor:
            self._preprocessors['ema'] = EMAPreprocessor()
        
        if ROCPreprocessor:
            self._preprocessors['roc'] = ROCPreprocessor()
        
        if VWAPPreprocessor:
            self._preprocessors['vwap'] = VWAPPreprocessor()
        
        if TRIXPreprocessor:
            self._preprocessors['trix'] = TRIXPreprocessor()
        
        if VortexPreprocessor:
            self._preprocessors['vortex'] = VortexPreprocessor()
        
        if BollingerWidthPreprocessor:
            self._preprocessors['bbwidth'] = BollingerWidthPreprocessor()
        
        if KeltnerChannelsPreprocessor:
            self._preprocessors['keltner'] = KeltnerChannelsPreprocessor()
        
        if DonchianChannelsPreprocessor:
            self._preprocessors['donchian'] = DonchianChannelsPreprocessor()
    
    def get_preprocessor(self, indicator_name: str):
        """
        Get a preprocessor instance for the given indicator.
        
        Args:
            indicator_name: Name of the technical indicator
            
        Returns:
            Preprocessor instance or None if not available
        """
        return self._preprocessors.get(indicator_name.lower())
    
    def is_available(self, indicator_name: str) -> bool:
        """Check if a preprocessor is available for the given indicator."""
        return indicator_name.lower() in self._preprocessors
    
    def list_available(self) -> list:
        """List all available preprocessor indicators."""
        return list(self._preprocessors.keys())


# Global preprocessor factory instance
preprocessor_factory = PreprocessorFactory()


# Convenience functions
def get_preprocessor(indicator_name: str):
    """Get a preprocessor instance for the given indicator."""
    return preprocessor_factory.get_preprocessor(indicator_name)


def is_preprocessor_available(indicator_name: str) -> bool:
    """Check if a preprocessor is available."""
    return preprocessor_factory.is_available(indicator_name)


def list_available_preprocessors() -> list:
    """List all available preprocessors."""
    return preprocessor_factory.list_available()