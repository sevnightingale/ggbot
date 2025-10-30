"""Signals data adapters."""

from .ggshot_adapter import GGShotAdapter

# Create instance for dynamic loading by gateway
ggshot_adapter = GGShotAdapter()

__all__ = ['GGShotAdapter', 'ggshot_adapter']
