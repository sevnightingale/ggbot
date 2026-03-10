"""
Arena Season Configuration

Season metadata as Python constants. No DB table needed —
dates don't change once set. arena_registrations table handles
per-bot registration state.
"""

from datetime import datetime, timezone
from typing import Optional


SEASONS = {
    2: {
        'name': 'Season 2',
        'season_id': 2,
        'training_start': datetime(2026, 3, 10, 0, 0, 0, tzinfo=timezone.utc),
        'registration_start': datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
        'registration_end': datetime(2026, 4, 6, 23, 59, 59, tzinfo=timezone.utc),
        'competition_start': datetime(2026, 4, 7, 0, 0, 0, tzinfo=timezone.utc),
        'competition_end': datetime(2026, 4, 28, 23, 59, 59, tzinfo=timezone.utc),
        'prize_description': 'Prize pool funded by $GG token launch. Exact amounts TBD.',
    }
}

CURRENT_SEASON_ID = 2


def get_current_season() -> dict:
    """Get the current season config."""
    return SEASONS[CURRENT_SEASON_ID]


def get_season_phase(season_id: int, now: Optional[datetime] = None) -> str:
    """
    Compute current phase for a season.

    Returns: 'training' | 'registration' | 'competition' | 'completed' | 'unknown'
    """
    season = SEASONS.get(season_id)
    if not season:
        return 'unknown'

    if now is None:
        now = datetime.now(timezone.utc)

    if now < season['registration_start']:
        return 'training'
    if now <= season['registration_end']:
        return 'registration'
    if now <= season['competition_end']:
        return 'competition'
    return 'completed'


def get_current_phase() -> str:
    """Get phase of current season."""
    return get_season_phase(CURRENT_SEASON_ID)


def is_registration_open(season_id: int, now: Optional[datetime] = None) -> bool:
    """Check if registration is currently open for a season."""
    return get_season_phase(season_id, now) == 'registration'


def is_competition_active(season_id: int, now: Optional[datetime] = None) -> bool:
    """Check if competition is currently active for a season."""
    return get_season_phase(season_id, now) == 'competition'
