"""
Bot Types Module

Contains bot-specific handlers for different bot types.
Each handler implements the BaseBotHandler interface with
custom logic for pipeline detection and status messaging.
"""

from .base_bot import BaseBotHandler
from .ggshot_bot import GGShotBotHandler

__all__ = ['BaseBotHandler', 'GGShotBotHandler']