"""
Signals Package

Generic signal processing framework for ggbots platform.
Supports multiple signal sources with pluggable architecture.
"""

from .listener_service import SignalListenerService, SignalData, SignalSource

__all__ = [
    'SignalListenerService',
    'SignalData', 
    'SignalSource'
]