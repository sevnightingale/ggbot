"""
Shared formatting utilities for human-readable output.
"""


def format_hours(hours: float) -> str:
    """
    Format a duration in hours as a human-readable string.

    Examples:
        0.75  -> "45m"
        5.0   -> "5h"
        26.5  -> "1d 2h"
        800.0 -> "33d"
    """
    if hours < 0:
        hours = abs(hours)

    total_minutes = int(hours * 60)

    if total_minutes < 60:
        return f"{max(total_minutes, 1)}m"
    elif total_minutes < 1440:  # < 24h
        h = total_minutes // 60
        return f"{h}h"
    elif total_minutes < 10080:  # < 7d
        days = total_minutes // 1440
        remaining_hours = (total_minutes % 1440) // 60
        return f"{days}d {remaining_hours}h" if remaining_hours > 0 else f"{days}d"
    else:  # >= 7d
        days = total_minutes // 1440
        return f"{days}d"
