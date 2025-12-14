"""
Admin Dashboard API Endpoints

Internal admin endpoints for platform management.
Restricted to ADMIN_USER_ID only.
"""

import os
import json
import subprocess
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.auth.supabase_auth import AuthenticatedUser, get_current_user_v2
from core.common.db import get_db_connection
from core.common.logger import logger

router = APIRouter(prefix="/api/v2/admin", tags=["admin"])

# Admin user ID from environment
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "00000000-0000-0000-0000-000000000000")


# =============================================================================
# Admin Auth Dependency
# =============================================================================

async def require_admin(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> AuthenticatedUser:
    """
    Require admin user for endpoint access.

    Security: JWT auth happens FIRST via get_current_user_v2,
    then we check if user_id matches ADMIN_USER_ID.
    """
    if current_user.user_id != ADMIN_USER_ID:
        logger.warning(f"Admin access denied for user {current_user.user_id}")
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# =============================================================================
# Request/Response Models
# =============================================================================

class UserProfileUpdate(BaseModel):
    """User profile update request."""
    subscription_tier: Optional[str] = None
    subscription_status: Optional[str] = None
    paid_data_points: Optional[List[str]] = None


class ConfigUpdate(BaseModel):
    """Configuration update request."""
    state: Optional[str] = None
    config_name: Optional[str] = None
    trading_mode: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = None


# =============================================================================
# Platform Stats Endpoint
# =============================================================================

@router.get("/stats")
async def get_platform_stats(
    admin: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """Get comprehensive platform statistics."""
    stats = {}

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # User statistics
            cur.execute("""
                SELECT
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN subscription_tier = 'ggbase' THEN 1 END) as pro_users,
                    COUNT(CASE WHEN subscription_tier = 'usage_based' THEN 1 END) as usage_based_users,
                    COUNT(CASE WHEN subscription_tier = 'free' OR subscription_tier IS NULL THEN 1 END) as free_users,
                    COUNT(CASE WHEN subscription_status = 'active' AND subscription_tier != 'free' THEN 1 END) as active_subscribers
                FROM user_profiles
            """)
            user_data = cur.fetchone()
            stats['users'] = {
                'total': user_data[0],
                'pro': user_data[1],
                'usage_based': user_data[2],
                'free': user_data[3],
                'active_subscribers': user_data[4]
            }

            # Bot statistics
            cur.execute("""
                SELECT
                    COUNT(*) as total_bots,
                    COUNT(CASE WHEN state = 'active' THEN 1 END) as active_bots,
                    COUNT(CASE WHEN state = 'inactive' THEN 1 END) as inactive_bots,
                    COUNT(DISTINCT user_id) as users_with_bots
                FROM configurations
            """)
            bot_data = cur.fetchone()
            stats['bots'] = {
                'total': bot_data[0],
                'active': bot_data[1],
                'inactive': bot_data[2],
                'users_with_bots': bot_data[3]
            }

            # Trading mode breakdown for active bots
            cur.execute("""
                SELECT trading_mode, COUNT(*) as count
                FROM configurations
                WHERE state = 'active'
                GROUP BY trading_mode
            """)
            mode_data = cur.fetchall()
            stats['bots']['by_mode'] = {row[0] or 'paper': row[1] for row in mode_data}

            # Trading activity from paper_accounts
            cur.execute("""
                SELECT
                    COALESCE(SUM(total_trades), 0) as total_trades,
                    COALESCE(SUM(win_trades), 0) as win_trades,
                    COALESCE(SUM(loss_trades), 0) as loss_trades,
                    ROUND(COALESCE(SUM(total_pnl), 0)::numeric, 2) as total_pnl
                FROM paper_accounts
            """)
            trade_data = cur.fetchone()
            total_trades = trade_data[0] or 0
            win_trades = trade_data[1] or 0
            stats['trading'] = {
                'total_trades': total_trades,
                'win_trades': win_trades,
                'loss_trades': trade_data[2] or 0,
                'win_rate': round(win_trades / total_trades * 100, 2) if total_trades > 0 else 0,
                'total_pnl': float(trade_data[3] or 0)
            }

            # Recent activity
            cur.execute("""
                SELECT COUNT(*) FROM paper_trades WHERE opened_at > NOW() - INTERVAL '24 hours'
            """)
            stats['trading']['trades_24h'] = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(*) FROM paper_trades WHERE opened_at > NOW() - INTERVAL '7 days'
            """)
            stats['trading']['trades_7d'] = cur.fetchone()[0]

            # Open positions
            cur.execute("""
                SELECT
                    COUNT(*) as open_positions,
                    ROUND(COALESCE(SUM(size_usd), 0)::numeric, 2) as total_exposure,
                    ROUND(COALESCE(SUM(unrealized_pnl), 0)::numeric, 2) as unrealized_pnl
                FROM paper_trades
                WHERE status = 'open'
            """)
            position_data = cur.fetchone()
            stats['positions'] = {
                'open': position_data[0],
                'total_exposure': float(position_data[1] or 0),
                'unrealized_pnl': float(position_data[2] or 0)
            }

            # Decisions last hour (health check)
            cur.execute("""
                SELECT COUNT(*) FROM decisions WHERE created_at > NOW() - INTERVAL '1 hour'
            """)
            decisions_1h = cur.fetchone()[0]
            stats['health'] = {
                'decisions_last_hour': decisions_1h,
                'status': 'healthy' if decisions_1h > 0 else 'low_activity'
            }

    return {"success": True, "stats": stats}


# =============================================================================
# Services Endpoint (PM2, VM, Redis)
# =============================================================================

@router.get("/services")
async def get_services_status(
    admin: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """Get PM2 services, VM resources, and Redis status."""
    result = {
        "pm2_services": [],
        "vm": {},
        "redis": {"status": "unknown", "memory": "N/A"}
    }

    # PM2 Services
    try:
        pm2_result = subprocess.run(
            ['pm2', 'jlist'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if pm2_result.returncode == 0:
            services = json.loads(pm2_result.stdout)
            for svc in services:
                pm2_env = svc.get('pm2_env', {})
                monit = svc.get('monit', {})

                # Calculate uptime
                uptime_ms = pm2_env.get('pm_uptime', 0)
                if uptime_ms:
                    uptime_seconds = (datetime.now().timestamp() * 1000 - uptime_ms) / 1000
                    uptime_str = _format_uptime(uptime_seconds)
                else:
                    uptime_str = "N/A"

                result["pm2_services"].append({
                    "name": svc.get('name', 'unknown'),
                    "status": pm2_env.get('status', 'unknown'),
                    "cpu": monit.get('cpu', 0),
                    "memory_mb": round(monit.get('memory', 0) / (1024 * 1024), 1),
                    "uptime": uptime_str,
                    "restarts": pm2_env.get('restart_time', 0)
                })
    except Exception as e:
        logger.error(f"Failed to get PM2 status: {e}")

    # VM Resources
    try:
        # Disk
        df_result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
        if df_result.returncode == 0:
            lines = df_result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                result["vm"]["disk"] = {
                    "total": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "percent": parts[4]
                }

        # Memory
        free_result = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
        if free_result.returncode == 0:
            lines = free_result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                result["vm"]["memory"] = {
                    "total": parts[1],
                    "used": parts[2],
                    "free": parts[3] if len(parts) > 3 else "N/A"
                }

        # CPU Load
        uptime_result = subprocess.run(['uptime'], capture_output=True, text=True, timeout=5)
        if uptime_result.returncode == 0 and 'load average:' in uptime_result.stdout:
            load_part = uptime_result.stdout.split('load average:')[1].strip()
            loads = [l.strip() for l in load_part.split(',')]
            result["vm"]["cpu_load"] = {
                "1m": loads[0] if len(loads) > 0 else "0.00",
                "5m": loads[1] if len(loads) > 1 else "0.00",
                "15m": loads[2] if len(loads) > 2 else "0.00"
            }
    except Exception as e:
        logger.error(f"Failed to get VM resources: {e}")

    # Redis
    try:
        ping_result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True, timeout=2)
        if ping_result.returncode == 0 and 'PONG' in ping_result.stdout:
            result["redis"]["status"] = "connected"

            mem_result = subprocess.run(['redis-cli', 'info', 'memory'], capture_output=True, text=True, timeout=2)
            if mem_result.returncode == 0:
                for line in mem_result.stdout.split('\n'):
                    if line.startswith('used_memory_human:'):
                        result["redis"]["memory"] = line.split(':')[1].strip()
                        break
        else:
            result["redis"]["status"] = "disconnected"
    except Exception as e:
        result["redis"]["status"] = "error"
        logger.error(f"Failed to get Redis status: {e}")

    return {"success": True, "services": result}


def _format_uptime(seconds: float) -> str:
    """Format uptime in human-readable format."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds/60)}m"
    elif seconds < 86400:
        return f"{int(seconds/3600)}h {int((seconds%3600)/60)}m"
    else:
        return f"{int(seconds/86400)}d {int((seconds%86400)/3600)}h"


# =============================================================================
# Logs Summary Endpoint
# =============================================================================

@router.get("/logs/summary")
async def get_logs_summary(
    admin: AuthenticatedUser = Depends(require_admin),
    hours: int = Query(default=24, ge=1, le=168)
) -> Dict[str, Any]:
    """Get log level counts for the specified time period."""
    log_file = "/home/sev/ggbot/logs/ggbot.log"

    counts = {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0, "DEBUG": 0}
    cutoff_time = datetime.now() - timedelta(hours=hours)

    try:
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    # Parse timestamp from log line: "2025-12-04 20:42:24 | INFO | ..."
                    if ' | ' not in line:
                        continue

                    parts = line.split(' | ')
                    if len(parts) < 2:
                        continue

                    timestamp_str = parts[0].strip()
                    level = parts[1].strip()

                    # Parse timestamp
                    try:
                        log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        if log_time < cutoff_time:
                            continue
                    except ValueError:
                        continue

                    # Count by level
                    if level in counts:
                        counts[level] += 1

                except Exception:
                    continue

    except FileNotFoundError:
        return {"success": True, "logs": {"error": "Log file not found"}, "hours": hours}
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        return {"success": False, "error": str(e)}

    return {
        "success": True,
        "logs": counts,
        "hours": hours,
        "total": sum(counts.values())
    }


# =============================================================================
# Billing Endpoint
# =============================================================================

@router.get("/billing")
async def get_billing_overview(
    admin: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """Get billing and token usage overview."""
    billing = {}

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Overall billing stats (last 30 days)
            cur.execute("""
                SELECT
                    COUNT(*) as total_activities,
                    COUNT(*) FILTER (WHERE provider_cost_usd IS NOT NULL) as llm_activities,
                    COALESCE(SUM(provider_cost_usd), 0) as total_provider_cost,
                    COALESCE(SUM(platform_cost_usd), 0) as total_platform_cost,
                    COALESCE(SUM(input_tokens), 0) as total_input_tokens,
                    COALESCE(SUM(output_tokens), 0) as total_output_tokens,
                    COALESCE(SUM(reasoning_tokens), 0) as total_reasoning_tokens,
                    COUNT(*) FILTER (WHERE stripe_reported = false AND platform_cost_usd IS NOT NULL) as unreported_count,
                    COALESCE(SUM(platform_cost_usd) FILTER (WHERE stripe_reported = false), 0) as unreported_amount,
                    MAX(stripe_reported_at) as last_report_time
                FROM activities
                WHERE created_at > NOW() - INTERVAL '30 days'
            """)
            row = cur.fetchone()

            billing['period'] = '30_days'
            billing['total_activities'] = row[0]
            billing['llm_activities'] = row[1]
            billing['provider_cost'] = round(float(row[2] or 0), 4)
            billing['platform_cost'] = round(float(row[3] or 0), 4)
            billing['markup_earned'] = round(float(row[3] or 0) - float(row[2] or 0), 4)
            billing['total_input_tokens'] = row[4]
            billing['total_output_tokens'] = row[5]
            billing['total_reasoning_tokens'] = row[6]
            billing['unreported_count'] = row[7]
            billing['unreported_amount'] = round(float(row[8] or 0), 4)
            billing['last_report_time'] = row[9].isoformat() if row[9] else None

            # Top users by cost
            cur.execute("""
                SELECT
                    a.user_id,
                    COALESCE(SUM(a.platform_cost_usd), 0) as total_cost,
                    COUNT(*) as activity_count
                FROM activities a
                WHERE a.created_at > NOW() - INTERVAL '30 days'
                AND a.platform_cost_usd IS NOT NULL
                GROUP BY a.user_id
                ORDER BY total_cost DESC
                LIMIT 10
            """)
            billing['top_users'] = [
                {"user_id": row[0], "cost": round(float(row[1]), 4), "activities": row[2]}
                for row in cur.fetchall()
            ]

    return {"success": True, "billing": billing}


# =============================================================================
# User Management Endpoints
# =============================================================================

@router.get("/users")
async def list_users(
    admin: AuthenticatedUser = Depends(require_admin),
    search: Optional[str] = Query(default=None, min_length=1),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0)
) -> Dict[str, Any]:
    """List users with optional email search."""
    users = []

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Build query - join with auth.users for email
            if search:
                cur.execute("""
                    SELECT
                        up.user_id,
                        au.email,
                        up.subscription_tier,
                        up.subscription_status,
                        au.created_at as joined_at,
                        au.last_sign_in_at,
                        (SELECT COUNT(*) FROM configurations WHERE user_id = up.user_id) as bot_count,
                        (SELECT COALESCE(SUM(total_trades), 0) FROM paper_accounts pa
                         JOIN configurations c ON c.config_id = pa.config_id
                         WHERE c.user_id = up.user_id) as total_trades
                    FROM user_profiles up
                    JOIN auth.users au ON au.id = up.user_id
                    WHERE au.email ILIKE %s
                    ORDER BY au.last_sign_in_at DESC NULLS LAST
                    LIMIT %s OFFSET %s
                """, (f"%{search}%", limit, offset))
            else:
                cur.execute("""
                    SELECT
                        up.user_id,
                        au.email,
                        up.subscription_tier,
                        up.subscription_status,
                        au.created_at as joined_at,
                        au.last_sign_in_at,
                        (SELECT COUNT(*) FROM configurations WHERE user_id = up.user_id) as bot_count,
                        (SELECT COALESCE(SUM(total_trades), 0) FROM paper_accounts pa
                         JOIN configurations c ON c.config_id = pa.config_id
                         WHERE c.user_id = up.user_id) as total_trades
                    FROM user_profiles up
                    JOIN auth.users au ON au.id = up.user_id
                    ORDER BY au.last_sign_in_at DESC NULLS LAST
                    LIMIT %s OFFSET %s
                """, (limit, offset))

            for row in cur.fetchall():
                users.append({
                    "user_id": row[0],
                    "email": row[1],
                    "subscription_tier": row[2] or "free",
                    "subscription_status": row[3] or "active",
                    "joined_at": row[4].isoformat() if row[4] else None,
                    "last_sign_in": row[5].isoformat() if row[5] else None,
                    "bot_count": row[6],
                    "total_trades": row[7]
                })

            # Get total count
            if search:
                cur.execute("""
                    SELECT COUNT(*) FROM user_profiles up
                    JOIN auth.users au ON au.id = up.user_id
                    WHERE au.email ILIKE %s
                """, (f"%{search}%",))
            else:
                cur.execute("SELECT COUNT(*) FROM user_profiles")
            total = cur.fetchone()[0]

    return {
        "success": True,
        "users": users,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: str,
    admin: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """Get detailed user information including configs and accounts."""
    user = None

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get user profile with auth info
            cur.execute("""
                SELECT
                    up.user_id,
                    au.email,
                    up.subscription_tier,
                    up.subscription_status,
                    up.subscription_expires_at,
                    up.stripe_customer_id,
                    up.stripe_subscription_id,
                    up.paid_data_points,
                    up.telegram_user_id,
                    up.telegram_username,
                    au.created_at as joined_at,
                    au.last_sign_in_at,
                    up.created_at as profile_created,
                    up.updated_at as profile_updated
                FROM user_profiles up
                JOIN auth.users au ON au.id = up.user_id
                WHERE up.user_id = %s
            """, (user_id,))

            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")

            user = {
                "user_id": row[0],
                "email": row[1],
                "subscription_tier": row[2] or "free",
                "subscription_status": row[3] or "active",
                "subscription_expires_at": row[4].isoformat() if row[4] else None,
                "stripe_customer_id": row[5],
                "stripe_subscription_id": row[6],
                "paid_data_points": row[7] or [],
                "telegram_user_id": row[8],
                "telegram_username": row[9],
                "joined_at": row[10].isoformat() if row[10] else None,
                "last_sign_in": row[11].isoformat() if row[11] else None,
                "profile_created": row[12].isoformat() if row[12] else None,
                "profile_updated": row[13].isoformat() if row[13] else None
            }

            # Get user's configurations with token usage
            cur.execute("""
                SELECT
                    c.config_id,
                    c.config_name,
                    c.config_type,
                    c.state,
                    c.trading_mode,
                    c.created_at,
                    c.updated_at,
                    c.config_data,
                    COALESCE(SUM(a.input_tokens), 0) as total_input_tokens,
                    COALESCE(SUM(a.output_tokens), 0) as total_output_tokens,
                    COALESCE(SUM(a.provider_cost_usd), 0) as provider_cost,
                    COALESCE(SUM(a.platform_cost_usd), 0) as platform_cost,
                    COUNT(a.activity_id) FILTER (WHERE a.provider_cost_usd IS NOT NULL) as llm_calls
                FROM configurations c
                LEFT JOIN activities a ON a.config_id = c.config_id AND a.provider_cost_usd IS NOT NULL
                WHERE c.user_id = %s
                GROUP BY c.config_id
                ORDER BY c.updated_at DESC
            """, (user_id,))

            configs = []
            for row in cur.fetchall():
                configs.append({
                    "config_id": row[0],
                    "config_name": row[1],
                    "config_type": row[2],
                    "state": row[3],
                    "trading_mode": row[4],
                    "created_at": row[5].isoformat() if row[5] else None,
                    "updated_at": row[6].isoformat() if row[6] else None,
                    "config_data": row[7],
                    "token_usage": {
                        "input_tokens": row[8],
                        "output_tokens": row[9],
                        "provider_cost": round(float(row[10] or 0), 4),
                        "platform_cost": round(float(row[11] or 0), 4),
                        "llm_calls": row[12]
                    }
                })
            user["configurations"] = configs

            # Get paper accounts
            cur.execute("""
                SELECT
                    pa.account_id,
                    pa.config_id,
                    c.config_name,
                    pa.initial_balance,
                    pa.current_balance,
                    pa.total_pnl,
                    pa.total_trades,
                    pa.win_trades,
                    pa.loss_trades,
                    pa.open_positions
                FROM paper_accounts pa
                JOIN configurations c ON c.config_id = pa.config_id
                WHERE pa.user_id = %s
                ORDER BY pa.updated_at DESC
            """, (user_id,))

            accounts = []
            for row in cur.fetchall():
                total_trades = row[6] or 0
                win_trades = row[7] or 0
                accounts.append({
                    "account_id": row[0],
                    "config_id": row[1],
                    "config_name": row[2],
                    "initial_balance": float(row[3] or 10000),
                    "current_balance": float(row[4] or 10000),
                    "total_pnl": float(row[5] or 0),
                    "total_trades": total_trades,
                    "win_trades": win_trades,
                    "loss_trades": row[8] or 0,
                    "win_rate": round(win_trades / total_trades * 100, 2) if total_trades > 0 else 0,
                    "open_positions": row[9] or 0
                })
            user["paper_accounts"] = accounts

    return {"success": True, "user": user}


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    update: UserProfileUpdate,
    admin: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """Update user profile fields."""
    updates = []
    params = []

    if update.subscription_tier is not None:
        valid_tiers = ['free', 'usage_based', 'ggbase', 'pro']
        if update.subscription_tier not in valid_tiers:
            raise HTTPException(status_code=400, detail=f"Invalid tier. Must be one of: {valid_tiers}")
        updates.append("subscription_tier = %s")
        params.append(update.subscription_tier)

    if update.subscription_status is not None:
        valid_statuses = ['active', 'canceled', 'past_due', 'incomplete']
        if update.subscription_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        updates.append("subscription_status = %s")
        params.append(update.subscription_status)

    if update.paid_data_points is not None:
        updates.append("paid_data_points = %s")
        params.append(update.paid_data_points)

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    updates.append("updated_at = NOW()")
    params.append(user_id)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                UPDATE user_profiles
                SET {', '.join(updates)}
                WHERE user_id = %s
                RETURNING user_id, subscription_tier, subscription_status, paid_data_points
            """, params)

            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")

            conn.commit()

            return {
                "success": True,
                "user": {
                    "user_id": row[0],
                    "subscription_tier": row[1],
                    "subscription_status": row[2],
                    "paid_data_points": row[3]
                }
            }


# =============================================================================
# Configuration Management Endpoints
# =============================================================================

@router.get("/users/{user_id}/configs")
async def get_user_configs(
    user_id: str,
    admin: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """Get all configurations for a user."""
    configs = []

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.config_id,
                    c.config_name,
                    c.config_type,
                    c.state,
                    c.trading_mode,
                    c.created_at,
                    c.updated_at,
                    c.config_data
                FROM configurations c
                WHERE c.user_id = %s
                ORDER BY c.updated_at DESC
            """, (user_id,))

            for row in cur.fetchall():
                configs.append({
                    "config_id": row[0],
                    "config_name": row[1],
                    "config_type": row[2],
                    "state": row[3],
                    "trading_mode": row[4],
                    "created_at": row[5].isoformat() if row[5] else None,
                    "updated_at": row[6].isoformat() if row[6] else None,
                    "config_data": row[7]
                })

    return {"success": True, "configs": configs}


@router.patch("/configs/{config_id}")
async def update_config(
    config_id: str,
    update: ConfigUpdate,
    admin: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """Update configuration fields."""
    updates = []
    params = []

    if update.state is not None:
        valid_states = ['active', 'inactive']
        if update.state not in valid_states:
            raise HTTPException(status_code=400, detail=f"Invalid state. Must be one of: {valid_states}")
        updates.append("state = %s")
        params.append(update.state)

    if update.config_name is not None:
        updates.append("config_name = %s")
        params.append(update.config_name)

    if update.trading_mode is not None:
        valid_modes = ['paper', 'symphony', 'aster']
        if update.trading_mode not in valid_modes:
            raise HTTPException(status_code=400, detail=f"Invalid mode. Must be one of: {valid_modes}")
        updates.append("trading_mode = %s")
        params.append(update.trading_mode)

    if update.config_data is not None:
        # Validate against BotConfig model
        try:
            from core.config.models import BotConfig
            BotConfig(**update.config_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid config_data: {str(e)}")
        updates.append("config_data = %s")
        params.append(json.dumps(update.config_data))

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    updates.append("updated_at = NOW()")
    params.append(config_id)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                UPDATE configurations
                SET {', '.join(updates)}
                WHERE config_id = %s
                RETURNING config_id, config_name, state, trading_mode, config_data
            """, params)

            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Configuration not found")

            conn.commit()

            return {
                "success": True,
                "config": {
                    "config_id": row[0],
                    "config_name": row[1],
                    "state": row[2],
                    "trading_mode": row[3],
                    "config_data": row[4]
                }
            }


# =============================================================================
# Bot Control Endpoints
# =============================================================================

@router.post("/bots/{config_id}/start")
async def admin_start_bot(
    config_id: str,
    admin: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """Start a bot (admin override - no ownership check)."""
    # Import here to avoid circular imports
    from core.scheduler import scheduler_manager

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get config details
            cur.execute("""
                SELECT user_id, config_name, config_type, state, trading_mode,
                       config_data->>'decision'->>'analysis_frequency' as frequency
                FROM configurations
                WHERE config_id = %s
            """, (config_id,))

            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Configuration not found")

            user_id, config_name, config_type, current_state, trading_mode, frequency = row

            if current_state == 'active':
                return {"success": True, "message": "Bot is already active"}

            # Update state to active
            cur.execute("""
                UPDATE configurations
                SET state = 'active', updated_at = NOW()
                WHERE config_id = %s
            """, (config_id,))
            conn.commit()

            # Schedule the bot
            try:
                scheduler_manager.schedule_bot(config_id, user_id, frequency or '1h')
                logger.info(f"Admin started bot {config_id} ({config_name})")
            except Exception as e:
                logger.error(f"Failed to schedule bot {config_id}: {e}")
                # Revert state
                cur.execute("UPDATE configurations SET state = 'inactive' WHERE config_id = %s", (config_id,))
                conn.commit()
                raise HTTPException(status_code=500, detail=f"Failed to start bot: {str(e)}")

    return {
        "success": True,
        "message": f"Bot '{config_name}' started",
        "config_id": config_id
    }


@router.post("/bots/{config_id}/stop")
async def admin_stop_bot(
    config_id: str,
    admin: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """Stop a bot (admin override - no ownership check)."""
    from core.scheduler import scheduler_manager

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get config details
            cur.execute("""
                SELECT config_name, state
                FROM configurations
                WHERE config_id = %s
            """, (config_id,))

            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Configuration not found")

            config_name, current_state = row

            if current_state == 'inactive':
                return {"success": True, "message": "Bot is already inactive"}

            # Remove scheduled jobs
            try:
                scheduler_manager.remove_bot_jobs(config_id)
            except Exception as e:
                logger.warning(f"Failed to remove scheduler jobs for {config_id}: {e}")

            # Update state to inactive
            cur.execute("""
                UPDATE configurations
                SET state = 'inactive', updated_at = NOW()
                WHERE config_id = %s
            """, (config_id,))
            conn.commit()

            logger.info(f"Admin stopped bot {config_id} ({config_name})")

    return {
        "success": True,
        "message": f"Bot '{config_name}' stopped",
        "config_id": config_id
    }


@router.post("/bots/{config_id}/reset-account")
async def admin_reset_account(
    config_id: str,
    admin: AuthenticatedUser = Depends(require_admin)
) -> Dict[str, Any]:
    """Reset paper trading account to $10,000 (admin override)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Check if account exists
            cur.execute("""
                SELECT account_id, current_balance, total_pnl
                FROM paper_accounts
                WHERE config_id = %s
            """, (config_id,))

            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Paper account not found for this config")

            old_balance = row[1]
            old_pnl = row[2]

            # Reset account
            cur.execute("""
                UPDATE paper_accounts
                SET current_balance = 10000.00,
                    initial_balance = 10000.00,
                    total_pnl = 0.00,
                    total_trades = 0,
                    win_trades = 0,
                    loss_trades = 0,
                    open_positions = 0,
                    last_reset_at = NOW(),
                    updated_at = NOW()
                WHERE config_id = %s
            """, (config_id,))

            # Close any open positions
            cur.execute("""
                UPDATE paper_trades
                SET status = 'closed', closed_at = NOW(), close_reason = 'admin_reset'
                WHERE config_id = %s AND status = 'open'
            """, (config_id,))

            conn.commit()

            logger.info(f"Admin reset account for config {config_id}: ${old_balance} -> $10,000")

    return {
        "success": True,
        "message": "Account reset to $10,000",
        "previous_balance": float(old_balance or 0),
        "previous_pnl": float(old_pnl or 0)
    }


# =============================================================================
# Bot Performance Comparison Endpoint
# =============================================================================

@router.get("/bots/equity-comparison")
async def get_equity_comparison(
    admin: AuthenticatedUser = Depends(require_admin),
    user_id: Optional[str] = Query(default=None),
    hours: int = Query(default=72, ge=1, le=720)  # Default 3 days, max 30 days
) -> Dict[str, Any]:
    """
    Get equity performance comparison for paper trading bots.

    Returns time-series equity data (current_balance + unrealized_pnl)
    for all active paper trading bots.

    Note: current_balance already includes margin_used.
    """
    # If no user_id specified, use admin's user_id
    target_user_id = user_id or admin.user_id

    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get equity snapshots for all active paper bots
            cur.execute("""
                SELECT
                    c.config_id,
                    c.config_name,
                    s.timestamp,
                    COALESCE(s.current_balance, 0) +
                    COALESCE(s.unrealized_pnl, 0) as total_equity,
                    s.total_pnl,
                    s.total_trades,
                    s.win_rate,
                    s.open_positions
                FROM account_snapshots s
                JOIN configurations c ON s.config_id = c.config_id
                WHERE c.user_id = %s
                AND c.trading_mode = 'paper'
                AND c.state = 'active'
                AND s.timestamp >= %s
                ORDER BY c.config_name, s.timestamp ASC
            """, (target_user_id, cutoff_time))

            rows = cur.fetchall()

            # Group by bot
            bots_data = {}
            for row in rows:
                config_id = row[0]
                config_name = row[1]
                timestamp = row[2]
                total_equity = float(row[3])
                total_pnl = float(row[4] or 0)
                total_trades = row[5] or 0
                win_rate = float(row[6] or 0)
                open_positions = row[7] or 0

                if config_id not in bots_data:
                    bots_data[config_id] = {
                        "config_id": config_id,
                        "config_name": config_name,
                        "data_points": [],
                        "current_equity": total_equity,
                        "current_pnl": total_pnl,
                        "total_trades": total_trades,
                        "win_rate": win_rate,
                        "open_positions": open_positions
                    }

                # Add data point
                bots_data[config_id]["data_points"].append({
                    "timestamp": timestamp.isoformat(),
                    "equity": total_equity
                })

                # Update current values (last snapshot)
                bots_data[config_id]["current_equity"] = total_equity
                bots_data[config_id]["current_pnl"] = total_pnl
                bots_data[config_id]["total_trades"] = total_trades
                bots_data[config_id]["win_rate"] = win_rate
                bots_data[config_id]["open_positions"] = open_positions

            # Convert to list and sort by current equity descending
            bots_list = list(bots_data.values())
            bots_list.sort(key=lambda x: x["current_equity"], reverse=True)

    return {
        "success": True,
        "user_id": target_user_id,
        "hours": hours,
        "bots": bots_list
    }
