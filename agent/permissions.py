"""
Agent Access Control & Permissions

Manages which users can access autonomous trading agents.

Phase 1: Manual whitelist (environment variable)
Future: Subscription tier-based access control

NOTE: This module is standalone - no imports from main ggbot codebase.
Agent service runs in separate venv and communicates via HTTP/DB/Redis.
"""

import os
from typing import Set
from loguru import logger


def get_whitelisted_user_ids() -> Set[str]:
    """
    Get set of user IDs allowed to use agents.

    Reads from AGENT_WHITELIST_USER_ID environment variable.
    Supports single ID or comma-separated list.

    Returns:
        Set[str]: User IDs allowed to access agents

    Examples:
        AGENT_WHITELIST_USER_ID="user-123"
        AGENT_WHITELIST_USER_ID="user-123,user-456,user-789"
    """
    whitelist_str = os.getenv("AGENT_WHITELIST_USER_ID", "")
    if not whitelist_str:
        return set()

    # Split by comma, strip whitespace, filter empty
    user_ids = {uid.strip() for uid in whitelist_str.split(",") if uid.strip()}
    return user_ids


def is_agent_enabled(user_id: str) -> bool:
    """
    Check if user has access to autonomous trading agents.

    Phase 1: Checks manual whitelist from environment variable
    Future: Check subscription tier, feature flags, etc.

    Args:
        user_id: User ID to check

    Returns:
        bool: True if user can access agents, False otherwise
    """
    whitelisted_users = get_whitelisted_user_ids()

    if not whitelisted_users:
        logger.warning(
            "No agent whitelist configured (AGENT_WHITELIST_USER_ID not set). "
            "Agent access disabled for all users."
        )
        return False

    enabled = user_id in whitelisted_users

    if enabled:
        logger.info(
            f"Agent access granted for user",
            user_id=user_id
        )
    else:
        logger.debug(
            f"Agent access denied for user (not in whitelist)",
            user_id=user_id
        )

    return enabled


def check_agent_access(user_id: str) -> None:
    """
    Check agent access and raise exception if denied.

    Use this in API endpoints to enforce access control.

    Args:
        user_id: User ID to check

    Raises:
        PermissionError: If user does not have agent access

    Example:
        ```python
        @app.post("/api/v2/agent/create")
        async def create_agent(user_id: str):
            check_agent_access(user_id)  # Raises if denied
            # ... proceed with agent creation
        ```
    """
    if not is_agent_enabled(user_id):
        raise PermissionError(
            "Autonomous trading agents are not available for your account. "
            "Contact support for access."
        )


# Future expansion: subscription-based access control
# def is_agent_enabled(user_id: str) -> bool:
#     """Check if user's subscription tier includes agent access."""
#     profile = get_user_profile(user_id)
#     return profile.can_use_agents  # @property on UserProfile class
