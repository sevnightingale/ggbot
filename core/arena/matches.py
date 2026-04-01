"""
Dojo Matches — Match lifecycle for 1v1 competitive trading.

Handles: challenge creation, match start (with instance configs + paper accounts),
completion (composite scoring + Elo update), forfeit, and the scheduler job
that drives the lifecycle state machine.

v1: House Bot challenges only. User-vs-user adds accept/reject flow later.

Match states: pending → active → completed | cancelled | forfeit
"""

import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

from core.common.db import get_db_connection, db_fetch_one, db_fetch_all, db_execute
from core.common.logger import logger
from core.arena.elo import (
    FORMAT_DURATIONS, DEFAULT_ELO,
    calculate_composite_score, update_elo, record_elo_change, _get_k_factor,
)

_log = logger.bind(component="dojo_matches")

MATCH_INITIAL_EQUITY = 10000.0

# How long a pending challenge stays open before expiring (user-vs-user future)
CHALLENGE_EXPIRY_HOURS = 24


# ─── Lock Check ─────────────────────────────────────────────────────────────

def is_dojo_locked(config_id: str) -> bool:
    """Check if a bot has an active Dojo match. Used by lock guards."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM dojo_matches
                    WHERE status = 'active'
                      AND (challenger_config_id = %s OR opponent_config_id = %s)
                )
            """, (config_id, config_id))
            return cur.fetchone()[0]


# ─── Entry Gate ─────────────────────────────────────────────────────────────

def check_entry_gate(config_id: str, user_id: str) -> Dict[str, Any]:
    """
    Validate whether a bot can enter a Dojo match.

    Checks:
    1. Config exists, is owned by user, is active
    2. Paper mode (no live bots in Dojo)
    3. No open positions
    4. Not already locked in an active match
    5. Not a House Bot (they're opponents, not challengers — for now)

    Returns: {'eligible': True} or {'eligible': False, 'reason': '...'}
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get config
            cur.execute("""
                SELECT state, config_data->>'selected_pair',
                       COALESCE(trading_mode, 'paper'), is_house_bot
                FROM configurations
                WHERE config_id = %s AND user_id = %s
            """, (config_id, user_id))
            row = cur.fetchone()

            if not row:
                return {'eligible': False, 'reason': 'Bot not found'}

            state, _, trading_mode, is_house_bot = row

            if state != 'active':
                return {'eligible': False, 'reason': 'Bot must be active to enter a match'}

            if trading_mode != 'paper':
                return {'eligible': False, 'reason': 'Only paper bots can enter the Dojo'}

            if is_house_bot:
                return {'eligible': False, 'reason': 'House Bots cannot challenge — they are opponents'}

            # Check open positions
            cur.execute("""
                SELECT COUNT(*) FROM paper_trades
                WHERE config_id = %s AND status = 'open'
            """, (config_id,))
            if cur.fetchone()[0] > 0:
                return {'eligible': False, 'reason': 'Close all open positions before entering a match'}

            # Check lock
            cur.execute("""
                SELECT id FROM dojo_matches
                WHERE status = 'active'
                  AND (challenger_config_id = %s OR opponent_config_id = %s)
                LIMIT 1
            """, (config_id, config_id))
            if cur.fetchone():
                return {'eligible': False, 'reason': 'Bot is already in an active match'}

            # Check pending challenges too
            cur.execute("""
                SELECT id FROM dojo_matches
                WHERE status = 'pending'
                  AND challenger_config_id = %s
                LIMIT 1
            """, (config_id,))
            if cur.fetchone():
                return {'eligible': False, 'reason': 'Bot has a pending challenge'}

            return {'eligible': True}


# ─── Challenge ──────────────────────────────────────────────────────────────

def create_challenge(
    challenger_config_id: str,
    opponent_config_id: str,
    match_format: str,
    user_id: str,
) -> Dict[str, Any]:
    """
    Create a challenge. House Bot opponents auto-accept and auto-start.

    For user-vs-user (future): creates pending challenge with expiry.
    """
    if match_format not in FORMAT_DURATIONS:
        return {'error': f'Invalid format: {match_format}'}

    # Validate entry gate
    gate = check_entry_gate(challenger_config_id, user_id)
    if not gate['eligible']:
        return {'error': gate['reason']}

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get opponent info
            cur.execute("""
                SELECT user_id, is_house_bot, state,
                       COALESCE(trading_mode, 'paper')
                FROM configurations
                WHERE config_id = %s
            """, (opponent_config_id,))
            opponent = cur.fetchone()

            if not opponent:
                return {'error': 'Opponent bot not found'}

            opponent_user_id, is_house_bot, opponent_state, opponent_mode = opponent

            if opponent_state != 'active':
                return {'error': 'Opponent bot is not active'}

            if opponent_mode != 'paper':
                return {'error': 'Opponent must be a paper bot'}

            # Check opponent isn't already in an active match
            cur.execute("""
                SELECT id FROM dojo_matches
                WHERE status = 'active'
                  AND (challenger_config_id = %s OR opponent_config_id = %s)
                LIMIT 1
            """, (opponent_config_id, opponent_config_id))
            if cur.fetchone():
                return {'error': 'Opponent is already in an active match'}

            match_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)

            if is_house_bot:
                # House Bot: auto-accept, start immediately
                cur.execute("""
                    INSERT INTO dojo_matches (
                        id, format, status,
                        challenger_config_id, opponent_config_id,
                        challenger_user_id, opponent_user_id,
                        accepted_at, starts_at
                    ) VALUES (%s, %s, 'pending', %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    match_id, match_format,
                    challenger_config_id, opponent_config_id,
                    user_id, str(opponent_user_id),
                    now, now,
                ))
                conn.commit()

                # Start the match immediately
                result = start_match(match_id)
                if 'error' in result:
                    return result

                _log.info(
                    f"House Bot challenge: match={match_id[:8]} "
                    f"challenger={challenger_config_id[:8]} vs opponent={opponent_config_id[:8]} "
                    f"format={match_format}"
                )
                return {'match_id': match_id, 'status': 'active', 'auto_started': True}

            else:
                # User-vs-user: pending with expiry (future)
                expires_at = now + timedelta(hours=CHALLENGE_EXPIRY_HOURS)
                cur.execute("""
                    INSERT INTO dojo_matches (
                        id, format, status,
                        challenger_config_id, opponent_config_id,
                        challenger_user_id, opponent_user_id,
                        challenge_expires_at
                    ) VALUES (%s, %s, 'pending', %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    match_id, match_format,
                    challenger_config_id, opponent_config_id,
                    user_id, str(opponent_user_id),
                    expires_at,
                ))
                conn.commit()

                _log.info(
                    f"User challenge created: match={match_id[:8]} "
                    f"challenger={challenger_config_id[:8]} → opponent={opponent_config_id[:8]}"
                )
                return {'match_id': match_id, 'status': 'pending'}


# ─── Start Match ────────────────────────────────────────────────────────────

def start_match(match_id: str) -> Dict[str, Any]:
    """
    Transition a match from pending to active.

    Creates match instance configs (config_type='dojo_match') and their
    paper accounts ($10k each). Snapshots both original configs.

    Match instances are lightweight configs — they have no scheduler jobs
    and are filtered out of the bot rail by the config_type guard.
    The paper trading system uses them purely as account containers.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get match
            cur.execute("""
                SELECT format, status,
                       challenger_config_id, opponent_config_id,
                       challenger_user_id, opponent_user_id
                FROM dojo_matches
                WHERE id = %s
            """, (match_id,))
            match = cur.fetchone()

            if not match:
                return {'error': 'Match not found'}

            match_format, status, c_config_id, o_config_id, c_user_id, o_user_id = match

            if status != 'pending':
                return {'error': f'Match is {status}, cannot start'}

            duration_days = FORMAT_DURATIONS[match_format]
            now = datetime.now(timezone.utc)
            ends_at = now + timedelta(days=duration_days)

            # Snapshot both configs
            c_snapshot = _snapshot_config(cur, c_config_id)
            o_snapshot = _snapshot_config(cur, o_config_id)

            # Get current Elo ratings
            cur.execute(
                "SELECT COALESCE(elo_rating, %s) FROM configurations WHERE config_id = %s",
                (DEFAULT_ELO, c_config_id)
            )
            c_elo = cur.fetchone()[0]
            cur.execute(
                "SELECT COALESCE(elo_rating, %s) FROM configurations WHERE config_id = %s",
                (DEFAULT_ELO, o_config_id)
            )
            o_elo = cur.fetchone()[0]

            # Create match instance configs (minimal shells for paper account tracking)
            c_instance_id = _create_match_instance(cur, c_config_id, c_user_id, match_id, 'challenger')
            o_instance_id = _create_match_instance(cur, o_config_id, o_user_id, match_id, 'opponent')

            # Create paper accounts for match instances
            _create_match_paper_account(cur, c_instance_id, c_user_id)
            _create_match_paper_account(cur, o_instance_id, o_user_id)

            # Update match record
            cur.execute("""
                UPDATE dojo_matches SET
                    status = 'active',
                    challenger_instance_id = %s,
                    opponent_instance_id = %s,
                    challenger_config_snapshot = %s,
                    opponent_config_snapshot = %s,
                    challenger_elo_before = %s,
                    opponent_elo_before = %s,
                    starts_at = COALESCE(starts_at, %s),
                    ends_at = %s
                WHERE id = %s
            """, (
                c_instance_id, o_instance_id,
                json.dumps(c_snapshot), json.dumps(o_snapshot),
                c_elo, o_elo,
                now, ends_at, match_id,
            ))
            conn.commit()

    _log.info(
        f"Match started: {match_id[:8]} format={match_format} "
        f"ends_at={ends_at.isoformat()} "
        f"instances=({c_instance_id[:8]}, {o_instance_id[:8]})"
    )
    return {
        'match_id': match_id,
        'status': 'active',
        'starts_at': now.isoformat(),
        'ends_at': ends_at.isoformat(),
        'challenger_instance_id': c_instance_id,
        'opponent_instance_id': o_instance_id,
    }


# ─── Complete Match ─────────────────────────────────────────────────────────

def complete_match(match_id: str) -> Dict[str, Any]:
    """
    Complete a match: snapshot equity, score, update Elo, archive instances.

    Called by the scheduler when ends_at has passed, or manually.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT format, status,
                       challenger_config_id, opponent_config_id,
                       challenger_instance_id, opponent_instance_id,
                       challenger_elo_before, opponent_elo_before,
                       starts_at, ends_at
                FROM dojo_matches
                WHERE id = %s
            """, (match_id,))
            match = cur.fetchone()

            if not match:
                return {'error': 'Match not found'}

            (match_format, status, c_config_id, o_config_id,
             c_instance_id, o_instance_id,
             c_elo_before, o_elo_before,
             starts_at, ends_at) = match

            if status != 'active':
                return {'error': f'Match is {status}, cannot complete'}

            now = datetime.now(timezone.utc)

            # Snapshot final equity from match instance paper accounts
            c_equity = _get_instance_equity(cur, c_instance_id)
            o_equity = _get_instance_equity(cur, o_instance_id)

            # Calculate composite scores over the match window
            # Use instance config IDs — trades were mirrored to these accounts
            c_score = calculate_composite_score(
                c_instance_id, starts_at, now, match_format, MATCH_INITIAL_EQUITY
            )
            o_score = calculate_composite_score(
                o_instance_id, starts_at, now, match_format, MATCH_INITIAL_EQUITY
            )

    # Elo update (on original configs, not instances)
    k_c = _get_k_factor(c_config_id)
    k_o = _get_k_factor(o_config_id)
    new_c_elo, new_o_elo = update_elo(
        c_elo_before, o_elo_before,
        c_score['composite_score'], o_score['composite_score'],
        k_c, k_o,
    )

    # Determine winner
    if c_score['composite_score'] > o_score['composite_score']:
        winner_id = c_config_id
        c_reason, o_reason = 'match_win', 'match_loss'
    elif o_score['composite_score'] > c_score['composite_score']:
        winner_id = o_config_id
        c_reason, o_reason = 'match_loss', 'match_win'
    else:
        winner_id = None
        c_reason = o_reason = 'match_draw'

    result_details = {
        'challenger': c_score,
        'opponent': o_score,
        'format': match_format,
        'duration_days': FORMAT_DURATIONS[match_format],
    }

    # Write results + archive
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE dojo_matches SET
                    status = 'completed',
                    challenger_end_equity = %s,
                    opponent_end_equity = %s,
                    challenger_composite_score = %s,
                    opponent_composite_score = %s,
                    winner_config_id = %s,
                    challenger_elo_after = %s,
                    opponent_elo_after = %s,
                    result_details = %s,
                    completed_at = %s
                WHERE id = %s
            """, (
                c_equity, o_equity,
                c_score['composite_score'], o_score['composite_score'],
                winner_id,
                new_c_elo, new_o_elo,
                json.dumps(result_details), now, match_id,
            ))
            conn.commit()

    # Record Elo changes on original bots
    record_elo_change(c_config_id, c_elo_before, new_c_elo, c_reason,
                      match_id=match_id, details={'composite_score': c_score['composite_score']})
    record_elo_change(o_config_id, o_elo_before, new_o_elo, o_reason,
                      match_id=match_id, details={'composite_score': o_score['composite_score']})

    # Archive match instance configs
    _archive_match_instances(c_instance_id, o_instance_id)

    _log.info(
        f"Match completed: {match_id[:8]} "
        f"winner={'draw' if not winner_id else winner_id[:8]} "
        f"scores=({c_score['composite_score']:.4f} vs {o_score['composite_score']:.4f}) "
        f"elo=({c_elo_before}→{new_c_elo}, {o_elo_before}→{new_o_elo})"
    )

    return {
        'match_id': match_id,
        'status': 'completed',
        'winner_config_id': winner_id,
        'challenger_score': c_score,
        'opponent_score': o_score,
        'elo_changes': {
            'challenger': {'before': c_elo_before, 'after': new_c_elo},
            'opponent': {'before': o_elo_before, 'after': new_o_elo},
        },
    }


# ─── Forfeit ────────────────────────────────────────────────────────────────

def forfeit_match(match_id: str, forfeiting_user_id: str) -> Dict[str, Any]:
    """
    Forfeit an active match. The opponent wins by default.

    Elo adjusts as if the forfeit side scored 0.0 and opponent scored 1.0.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT format, status,
                       challenger_config_id, opponent_config_id,
                       challenger_user_id, opponent_user_id,
                       challenger_instance_id, opponent_instance_id,
                       challenger_elo_before, opponent_elo_before
                FROM dojo_matches
                WHERE id = %s
            """, (match_id,))
            match = cur.fetchone()

            if not match:
                return {'error': 'Match not found'}

            (match_format, status, c_config_id, o_config_id,
             c_user_id, o_user_id,
             c_instance_id, o_instance_id,
             c_elo_before, o_elo_before) = match

            if status != 'active':
                return {'error': f'Match is {status}, cannot forfeit'}

            # Determine who forfeited
            if forfeiting_user_id == c_user_id:
                winner_id = o_config_id
                loser_config_id = c_config_id
            elif forfeiting_user_id == o_user_id:
                winner_id = c_config_id
                loser_config_id = o_config_id
            else:
                return {'error': 'You are not a participant in this match'}

            now = datetime.now(timezone.utc)

    # Elo: forfeit = score 0.0 vs 1.0
    k_c = _get_k_factor(c_config_id)
    k_o = _get_k_factor(o_config_id)

    if winner_id == o_config_id:
        # Challenger forfeited
        new_c_elo, new_o_elo = update_elo(c_elo_before, o_elo_before, 0.0, 1.0, k_c, k_o)
        c_reason, o_reason = 'match_forfeit', 'match_win'
    else:
        # Opponent forfeited
        new_c_elo, new_o_elo = update_elo(c_elo_before, o_elo_before, 1.0, 0.0, k_c, k_o)
        c_reason, o_reason = 'match_win', 'match_forfeit'

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE dojo_matches SET
                    status = 'forfeit',
                    winner_config_id = %s,
                    challenger_elo_after = %s,
                    opponent_elo_after = %s,
                    result_details = %s,
                    completed_at = %s
                WHERE id = %s
            """, (
                winner_id,
                new_c_elo, new_o_elo,
                json.dumps({'forfeit_by': forfeiting_user_id}),
                now, match_id,
            ))
            conn.commit()

    record_elo_change(c_config_id, c_elo_before, new_c_elo, c_reason,
                      match_id=match_id, details={'forfeit': True})
    record_elo_change(o_config_id, o_elo_before, new_o_elo, o_reason,
                      match_id=match_id, details={'forfeit': True})

    # Archive instances
    if c_instance_id and o_instance_id:
        _archive_match_instances(c_instance_id, o_instance_id)

    _log.info(
        f"Match forfeited: {match_id[:8]} by user={forfeiting_user_id[:8]} "
        f"winner={winner_id[:8]} "
        f"elo=({c_elo_before}→{new_c_elo}, {o_elo_before}→{new_o_elo})"
    )

    return {
        'match_id': match_id,
        'status': 'forfeit',
        'winner_config_id': winner_id,
        'forfeited_by': forfeiting_user_id,
    }


# ─── Scheduler Job ──────────────────────────────────────────────────────────

async def process_dojo_matches():
    """
    Scheduler job (every 5 minutes). Drives the match lifecycle:
    1. Start matches whose starts_at has arrived (user-vs-user future path)
    2. Complete matches whose ends_at has passed
    3. Expire pending challenges past their expiry time
    """
    import asyncio

    now = datetime.now(timezone.utc)
    actions = 0

    # 1. Complete expired active matches
    rows = await db_fetch_all("""
        SELECT id FROM dojo_matches
        WHERE status = 'active' AND ends_at <= %s
    """, (now,))

    for row in rows:
        try:
            await asyncio.to_thread(complete_match, str(row[0]))
            actions += 1
        except Exception as e:
            _log.error(f"Failed to complete match {row[0]}: {e}")

    # 2. Start accepted matches whose starts_at has arrived
    # (For House Bot matches this happens immediately in create_challenge,
    #  but user-vs-user matches may have a scheduled start time)
    rows = await db_fetch_all("""
        SELECT id FROM dojo_matches
        WHERE status = 'pending'
          AND accepted_at IS NOT NULL
          AND starts_at <= %s
    """, (now,))

    for row in rows:
        try:
            await asyncio.to_thread(start_match, str(row[0]))
            actions += 1
        except Exception as e:
            _log.error(f"Failed to start match {row[0]}: {e}")

    # 3. Expire stale pending challenges
    rows = await db_fetch_all("""
        SELECT id FROM dojo_matches
        WHERE status = 'pending'
          AND accepted_at IS NULL
          AND challenge_expires_at <= %s
    """, (now,))

    if rows:
        await db_execute("""
            UPDATE dojo_matches SET status = 'cancelled'
            WHERE status = 'pending'
              AND accepted_at IS NULL
              AND challenge_expires_at <= %s
        """, (now,))
        actions += len(rows)

    if actions > 0:
        _log.info(f"Dojo lifecycle: {actions} actions processed")


# ─── Query Helpers ──────────────────────────────────────────────────────────

def get_active_matches(config_id: str) -> List[Dict[str, Any]]:
    """Get active matches for a config (as challenger or opponent)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    m.id, m.format, m.status,
                    m.challenger_config_id, m.opponent_config_id,
                    c_cfg.config_name AS challenger_name,
                    o_cfg.config_name AS opponent_name,
                    o_cfg.is_house_bot AS opponent_is_house_bot,
                    m.starts_at, m.ends_at, m.created_at
                FROM dojo_matches m
                JOIN configurations c_cfg ON c_cfg.config_id = m.challenger_config_id
                JOIN configurations o_cfg ON o_cfg.config_id = m.opponent_config_id
                WHERE m.status IN ('pending', 'active')
                  AND (m.challenger_config_id = %s OR m.opponent_config_id = %s)
                ORDER BY m.created_at DESC
            """, (config_id, config_id))
            rows = cur.fetchall()

            return [{
                'match_id': str(r[0]),
                'format': r[1],
                'status': r[2],
                'challenger_config_id': str(r[3]),
                'opponent_config_id': str(r[4]),
                'challenger_name': r[5],
                'opponent_name': r[6],
                'opponent_is_house_bot': r[7],
                'starts_at': r[8].isoformat() if r[8] else None,
                'ends_at': r[9].isoformat() if r[9] else None,
                'created_at': r[10].isoformat() if r[10] else None,
            } for r in rows]


def get_match_history(config_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """Get completed/forfeited matches for a config, most recent first."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    m.id, m.format, m.status,
                    m.challenger_config_id, m.opponent_config_id,
                    c_cfg.config_name AS challenger_name,
                    o_cfg.config_name AS opponent_name,
                    m.winner_config_id,
                    m.challenger_composite_score, m.opponent_composite_score,
                    m.challenger_elo_before, m.challenger_elo_after,
                    m.opponent_elo_before, m.opponent_elo_after,
                    m.starts_at, m.completed_at,
                    m.result_details
                FROM dojo_matches m
                JOIN configurations c_cfg ON c_cfg.config_id = m.challenger_config_id
                JOIN configurations o_cfg ON o_cfg.config_id = m.opponent_config_id
                WHERE m.status IN ('completed', 'forfeit')
                  AND (m.challenger_config_id = %s OR m.opponent_config_id = %s)
                ORDER BY m.completed_at DESC
                LIMIT %s OFFSET %s
            """, (config_id, config_id, limit, offset))
            rows = cur.fetchall()

            return [{
                'match_id': str(r[0]),
                'format': r[1],
                'status': r[2],
                'challenger_config_id': str(r[3]),
                'opponent_config_id': str(r[4]),
                'challenger_name': r[5],
                'opponent_name': r[6],
                'winner_config_id': str(r[7]) if r[7] else None,
                'challenger_score': float(r[8]) if r[8] is not None else None,
                'opponent_score': float(r[9]) if r[9] is not None else None,
                'challenger_elo': {'before': r[10], 'after': r[11]},
                'opponent_elo': {'before': r[12], 'after': r[13]},
                'starts_at': r[14].isoformat() if r[14] else None,
                'completed_at': r[15].isoformat() if r[15] else None,
                'result_details': r[16],
            } for r in rows]


def get_match_detail(match_id: str) -> Optional[Dict[str, Any]]:
    """Get full match detail (public-safe — no user_ids exposed)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    m.id, m.format, m.status,
                    m.challenger_config_id, m.opponent_config_id,
                    c_cfg.config_name, o_cfg.config_name,
                    c_cfg.elo_rating, o_cfg.elo_rating,
                    c_cfg.is_house_bot, o_cfg.is_house_bot,
                    m.winner_config_id,
                    m.challenger_end_equity, m.opponent_end_equity,
                    m.challenger_composite_score, m.opponent_composite_score,
                    m.challenger_elo_before, m.challenger_elo_after,
                    m.opponent_elo_before, m.opponent_elo_after,
                    m.starts_at, m.ends_at, m.completed_at,
                    m.result_details
                FROM dojo_matches m
                JOIN configurations c_cfg ON c_cfg.config_id = m.challenger_config_id
                JOIN configurations o_cfg ON o_cfg.config_id = m.opponent_config_id
                WHERE m.id = %s
            """, (match_id,))
            r = cur.fetchone()

            if not r:
                return None

            return {
                'match_id': str(r[0]),
                'format': r[1],
                'status': r[2],
                'challenger': {
                    'config_id': str(r[3]),
                    'name': r[5],
                    'current_elo': r[7],
                    'is_house_bot': r[9],
                    'end_equity': float(r[12]) if r[12] is not None else None,
                    'composite_score': float(r[14]) if r[14] is not None else None,
                    'elo_before': r[16],
                    'elo_after': r[17],
                },
                'opponent': {
                    'config_id': str(r[4]),
                    'name': r[6],
                    'current_elo': r[8],
                    'is_house_bot': r[10],
                    'end_equity': float(r[13]) if r[13] is not None else None,
                    'composite_score': float(r[15]) if r[15] is not None else None,
                    'elo_before': r[18],
                    'elo_after': r[19],
                },
                'winner_config_id': str(r[11]) if r[11] else None,
                'starts_at': r[20].isoformat() if r[20] else None,
                'ends_at': r[21].isoformat() if r[21] else None,
                'completed_at': r[22].isoformat() if r[22] else None,
                'result_details': r[23],
            }


def get_bot_dojo_stats(config_id: str) -> Dict[str, Any]:
    """Aggregate Dojo stats for a bot."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE status IN ('completed', 'forfeit')) AS total_matches,
                    COUNT(*) FILTER (WHERE winner_config_id = %s) AS wins,
                    COUNT(*) FILTER (
                        WHERE status = 'completed' AND winner_config_id IS NULL
                    ) AS draws,
                    COUNT(*) FILTER (
                        WHERE status IN ('completed', 'forfeit')
                          AND winner_config_id IS NOT NULL
                          AND winner_config_id != %s
                    ) AS losses,
                    COUNT(*) FILTER (WHERE status = 'active') AS active_matches
                FROM dojo_matches
                WHERE challenger_config_id = %s OR opponent_config_id = %s
            """, (config_id, config_id, config_id, config_id))
            r = cur.fetchone()

            return {
                'total_matches': r[0],
                'wins': r[1],
                'draws': r[2],
                'losses': r[3],
                'active_matches': r[4],
            }


# ─── Internal Helpers ───────────────────────────────────────────────────────

def _snapshot_config(cur, config_id: str) -> Dict[str, Any]:
    """Snapshot a config's strategy data for immutable match record."""
    cur.execute("""
        SELECT config_name, config_data, elo_rating
        FROM configurations
        WHERE config_id = %s
    """, (config_id,))
    row = cur.fetchone()
    if not row:
        return {}

    config_data = row[1] if isinstance(row[1], dict) else {}
    # Handle nested config_data structure
    inner = config_data.get('config_data', config_data)

    return {
        'config_name': row[0],
        'selected_pair': inner.get('selected_pair'),
        'decision': inner.get('decision'),
        'extraction': inner.get('extraction'),
        'trading': inner.get('trading'),
        'llm_config': inner.get('llm_config'),
        'elo_rating': row[2],
    }


def _create_match_instance(cur, source_config_id: str, user_id: str,
                           match_id: str, role: str) -> str:
    """
    Create a minimal config (config_type='dojo_match') as a paper account container.

    No scheduler job. Invisible in bot rail (filtered by config_type guard).
    config_data stores the match reference for traceability.
    """
    instance_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO configurations (
            config_id, user_id, config_type, config_name, state,
            config_data
        ) VALUES (%s, %s, 'dojo_match', %s, 'active', %s)
    """, (
        instance_id, user_id,
        f"Dojo Match Instance ({role})",
        json.dumps({
            'match_id': match_id,
            'source_config_id': source_config_id,
            'role': role,
            'schema_version': '2.2',
        }),
    ))
    return instance_id


def _create_match_paper_account(cur, instance_id: str, user_id: str) -> None:
    """Create a $10k paper account for a match instance."""
    cur.execute("""
        INSERT INTO paper_accounts (
            config_id, user_id, initial_balance, current_balance,
            total_pnl, open_positions, total_trades, win_trades, loss_trades
        ) VALUES (%s, %s, %s, %s, 0, 0, 0, 0, 0)
    """, (instance_id, user_id, MATCH_INITIAL_EQUITY, MATCH_INITIAL_EQUITY))


def _get_instance_equity(cur, instance_id: str) -> float:
    """Get current equity (balance + unrealized P&L) for a match instance."""
    cur.execute("""
        SELECT COALESCE(current_balance, %s) FROM paper_accounts
        WHERE config_id = %s
    """, (MATCH_INITIAL_EQUITY, instance_id))
    row = cur.fetchone()
    balance = float(row[0]) if row else MATCH_INITIAL_EQUITY

    # Add unrealized P&L from any open positions at match end
    cur.execute("""
        SELECT COALESCE(SUM(unrealized_pnl), 0) FROM paper_trades
        WHERE config_id = %s AND status = 'open'
    """, (instance_id,))
    unrealized = float(cur.fetchone()[0])

    return balance + unrealized


def _archive_match_instances(c_instance_id: str, o_instance_id: str) -> None:
    """Mark match instance configs as inactive (archived). Paper data preserved."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE configurations SET state = 'inactive', updated_at = NOW()
                    WHERE config_id IN (%s, %s) AND config_type = 'dojo_match'
                """, (c_instance_id, o_instance_id))
                conn.commit()
    except Exception as e:
        _log.warning(f"Failed to archive match instances: {e}")
