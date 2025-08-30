"""
Repository layer for GGBot domain models.

Repositories provide clean abstraction over data persistence, handling both
database operations and external API integrations. They follow the Repository
pattern to isolate domain logic from infrastructure concerns.
"""

from .account_repository import AccountRepository

__all__ = [
    "AccountRepository",
]