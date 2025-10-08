"""
Paper Trading API Endpoints

Provides REST API endpoints for paper trading dashboard integration.
Uses SupabasePaperTradingService for data access.
"""

import os
from typing import Dict, List, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from dotenv import load_dotenv
import psycopg2.extras

from core.common.logger import logger
from trading.paper.supabase_service import SupabasePaperTradingService
from core.auth.supabase_auth import get_current_user_v2, AuthenticatedUser

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/api/v2/bot", tags=["paper_trading"])


@router.get("/{config_id}/metrics")
async def get_paper_trading_metrics(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Get paper trading performance metrics for a bot configuration.
    
    Returns:
        - profit_loss_data: Array of daily P&L points for charting
        - trade_stats: Comprehensive trading statistics
    """
    try:
        service = SupabasePaperTradingService()
        
        # Get account summary
        account_summary = await service.get_account_summary(config_id)
        if "error" in account_summary:
            # No account exists yet - return empty metrics
            return {
                "status": "success",
                "config_id": config_id,
                "metrics": {
                    "profit_loss_data": [],
                    "trade_stats": {
                        "totalTrades": 0,
                        "winCount": 0,
                        "lossCount": 0,
                        "neutralCount": 0,
                        "winRate": 0.0,
                        "lossRate": 0.0,
                        "neutralRate": 0.0,
                        "avgProfitPerTrade": 0.0,
                        "avgLossPerTrade": 0.0,
                        "totalProfit": 0.0,
                        "avgTradeDuration": "0m"
                    }
                }
            }
        
        # Get trade history for P&L calculation
        trade_history = await service.get_trade_history(config_id, limit=1000)
        
        # Calculate profit/loss data points (daily aggregation)
        profit_loss_data = _calculate_daily_pnl(trade_history)
        
        # Calculate detailed trade statistics
        trade_stats = _calculate_trade_statistics(trade_history, account_summary)
        
        return {
            "status": "success",
            "config_id": config_id,
            "metrics": {
                "profit_loss_data": profit_loss_data,
                "trade_stats": trade_stats,
                "account_balance": account_summary.get("current_balance", 0.0),
                "total_pnl": account_summary.get("total_pnl", 0.0),
                "initial_balance": account_summary.get("initial_balance", 10000.0)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get paper trading metrics for {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/{config_id}/positions")
async def get_paper_trading_positions(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Get live paper trading positions for a bot configuration.
    
    Returns formatted positions for dashboard display.
    """
    try:
        service = SupabasePaperTradingService()
        
        # Get open positions
        positions = await service.get_open_positions(config_id)
        
        # Format positions for dashboard
        formatted_positions = []
        for pos in positions:
            # Calculate current P&L and other metrics
            entry_price = float(pos["entry_price"])
            current_price = float(pos.get("current_price", entry_price))
            size_usd = float(pos["size_usd"])
            side = pos["side"]
            
            # Calculate P&L with leverage
            leverage = int(pos.get("leverage", 1))
            size_contracts = size_usd / entry_price
            if side == "long":
                pnl = (current_price - entry_price) * size_contracts * leverage
            else:
                pnl = (entry_price - current_price) * size_contracts * leverage
            
            # Calculate time in trade
            opened_at = datetime.fromisoformat(pos["opened_at"].replace('Z', '+00:00'))
            time_in_trade = _format_time_duration(datetime.now() - opened_at)
            
            formatted_positions.append({
                "id": pos["trade_id"],
                "symbol": pos["symbol"],
                "direction": side.upper(),
                "pnl": round(pnl, 2),
                "positionSize": round(size_usd, 2),
                "entryPrice": round(entry_price, 2),
                "currentPrice": round(current_price, 2),
                "timeInTrade": time_in_trade,
                "leverage": pos.get("leverage", 1),
                "confidence": round((pos.get("confidence_score", 0.0) or 0.0) * 100, 1),
                "reasoning_text": "Paper trading position",  # Could enhance with decision data
                "volume_analysis": "Real-time Hummingbot data",
                "signal_timeframe": "1h"
            })
        
        return {
            "status": "success",
            "config_id": config_id,
            "positions": formatted_positions
        }
        
    except Exception as e:
        logger.error(f"Failed to get paper trading positions for {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get positions: {str(e)}")


@router.get("/{config_id}/trades")
async def get_paper_trading_trades(
    config_id: str,
    limit: int = 100,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Get paper trading trade history for a bot configuration.
    
    Returns formatted closed trades for dashboard display.
    """
    try:
        service = SupabasePaperTradingService()
        
        # Get trade history
        trades = await service.get_trade_history(config_id, limit=limit)
        
        # Format trades for dashboard (only closed trades)
        formatted_trades = []
        for trade in trades:
            if trade["status"] == "closed":
                entry_price = float(trade["entry_price"])
                size_usd = float(trade["size_usd"])
                pnl = float(trade.get("realized_pnl", 0.0))
                
                formatted_trades.append({
                    "symbol": trade["symbol"],
                    "direction": trade["side"].upper(),
                    "pnl": round(pnl, 2),
                    "positionSize": round(size_usd, 2),
                    "entryPrice": round(entry_price, 2),
                    "closePrice": round(float(trade.get("current_price", entry_price)), 2),
                    "openedAt": trade["opened_at"],
                    "closedAt": trade.get("closed_at"),
                    "confidence": round((trade.get("confidence_score", 0.0) or 0.0) * 100, 1)
                })
        
        return {
            "status": "success",
            "config_id": config_id,
            "trades": formatted_trades,
            "count": len(formatted_trades)
        }
        
    except Exception as e:
        logger.error(f"Failed to get paper trading trades for {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trades: {str(e)}")


@router.get("/{config_id}/account")
async def get_paper_trading_account(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Get paper trading account summary for a bot configuration.
    
    Returns account balance, statistics, and performance metrics.
    """
    try:
        service = SupabasePaperTradingService()
        
        # Get account summary
        account_summary = await service.get_account_summary(config_id)
        
        if "error" in account_summary:
            return {
                "status": "success",
                "config_id": config_id,
                "account": {
                    "initial_balance": 10000.0,
                    "current_balance": 10000.0,
                    "total_pnl": 0.0,
                    "open_positions": 0,
                    "total_trades": 0,
                    "win_trades": 0,
                    "loss_trades": 0,
                    "win_rate": 0.0,
                    "total_return_pct": 0.0
                }
            }
        
        # Calculate additional metrics
        initial_balance = account_summary.get("initial_balance", 10000.0)
        current_balance = account_summary.get("current_balance", 10000.0)
        total_pnl = account_summary.get("total_pnl", 0.0)
        
        # Total return percentage
        total_return_pct = ((current_balance + total_pnl - initial_balance) / initial_balance * 100) if initial_balance > 0 else 0.0
        
        return {
            "status": "success",
            "config_id": config_id,
            "account": {
                "initial_balance": initial_balance,
                "current_balance": current_balance,
                "total_pnl": total_pnl,
                "open_positions": account_summary.get("open_positions", 0),
                "total_trades": account_summary.get("total_trades", 0),
                "win_trades": account_summary.get("win_trades", 0),
                "loss_trades": account_summary.get("loss_trades", 0),
                "win_rate": account_summary.get("win_rate", 0.0),
                "total_return_pct": round(total_return_pct, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get paper trading account for {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get account: {str(e)}")


@router.post("/{config_id}/positions/{trade_id}/close")
async def close_paper_position(
    config_id: str,
    trade_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Manually close an open paper trading position.

    Args:
        config_id: Bot configuration ID
        trade_id: Trade ID to close
        current_user: Authenticated user from JWT token

    Returns:
        - status: "success" or "failed"
        - close_price: Price at which position was closed
        - realized_pnl: Final P&L with correct leverage calculation
        - close_reason: "manual"
    """
    try:
        service = SupabasePaperTradingService()

        # Close the position at current market price
        result = await service.close_position(
            trade_id=trade_id,
            reason="manual",
            close_price=None  # Will use current market price
        )

        if result.get("status") == "closed":
            logger.info(f"Manual close: trade {trade_id} for user {current_user.user_id}, config {config_id}")
            return {
                "status": "success",
                "trade_id": trade_id,
                "close_price": result.get("close_price"),
                "realized_pnl": result.get("pnl"),
                "close_reason": "manual",
                "message": "Position closed successfully"
            }
        else:
            # Failed to close
            error_reason = result.get("reason", "Unknown error")
            logger.warning(f"Failed to close trade {trade_id}: {error_reason}")
            raise HTTPException(status_code=400, detail=f"Failed to close position: {error_reason}")

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error closing position {trade_id} for config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error closing position: {str(e)}")


# Helper functions

def _calculate_daily_pnl(trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate daily P&L aggregation for charting."""
    daily_pnl = {}
    
    for trade in trades:
        if trade["status"] == "closed" and trade.get("closed_at"):
            try:
                # Parse close date
                close_date = datetime.fromisoformat(trade["closed_at"].replace('Z', '+00:00')).date()
                date_str = close_date.strftime("%Y-%m-%d")
                
                # Aggregate P&L by day
                pnl = float(trade.get("realized_pnl", 0.0))
                if date_str in daily_pnl:
                    daily_pnl[date_str] += pnl
                else:
                    daily_pnl[date_str] = pnl
            except Exception as e:
                logger.warning(f"Failed to parse trade date: {e}")
                continue
    
    # Convert to array format for charting
    result = []
    cumulative_pnl = 0.0
    
    # Sort by date
    for date_str in sorted(daily_pnl.keys()):
        cumulative_pnl += daily_pnl[date_str]
        result.append({
            "date": date_str,
            "profit": round(cumulative_pnl, 2),
            "daily_pnl": round(daily_pnl[date_str], 2)
        })
    
    return result


def _calculate_trade_statistics(trades: List[Dict[str, Any]], account_summary: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate comprehensive trade statistics."""
    closed_trades = [t for t in trades if t["status"] == "closed"]
    
    if not closed_trades:
        return {
            "totalTrades": 0,
            "winCount": 0,
            "lossCount": 0,
            "neutralCount": 0,
            "winRate": 0.0,
            "lossRate": 0.0,
            "neutralRate": 0.0,
            "avgProfitPerTrade": 0.0,
            "avgLossPerTrade": 0.0,
            "totalProfit": 0.0,
            "avgTradeDuration": "0m"
        }
    
    # Categorize trades
    wins = [t for t in closed_trades if float(t.get("realized_pnl", 0.0)) > 0]
    losses = [t for t in closed_trades if float(t.get("realized_pnl", 0.0)) < 0]
    neutrals = [t for t in closed_trades if float(t.get("realized_pnl", 0.0)) == 0]
    
    total_trades = len(closed_trades)
    win_count = len(wins)
    loss_count = len(losses)
    neutral_count = len(neutrals)
    
    # Calculate percentages
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0.0
    loss_rate = (loss_count / total_trades * 100) if total_trades > 0 else 0.0
    neutral_rate = (neutral_count / total_trades * 100) if total_trades > 0 else 0.0
    
    # Calculate average P&L
    total_profit = sum(float(t.get("realized_pnl", 0.0)) for t in closed_trades)
    avg_profit = (sum(float(t.get("realized_pnl", 0.0)) for t in wins) / len(wins)) if wins else 0.0
    avg_loss = (sum(float(t.get("realized_pnl", 0.0)) for t in losses) / len(losses)) if losses else 0.0
    
    # Calculate average trade duration
    durations = []
    for trade in closed_trades:
        if trade.get("opened_at") and trade.get("closed_at"):
            try:
                opened = datetime.fromisoformat(trade["opened_at"].replace('Z', '+00:00'))
                closed = datetime.fromisoformat(trade["closed_at"].replace('Z', '+00:00'))
                duration = closed - opened
                durations.append(duration.total_seconds() / 60)  # Convert to minutes
            except Exception:
                continue
    
    avg_duration_minutes = sum(durations) / len(durations) if durations else 0
    avg_duration_str = _format_time_duration(timedelta(minutes=avg_duration_minutes))
    
    return {
        "totalTrades": total_trades,
        "winCount": win_count,
        "lossCount": loss_count,
        "neutralCount": neutral_count,
        "winRate": round(win_rate, 1),
        "lossRate": round(loss_rate, 1),
        "neutralRate": round(neutral_rate, 1),
        "avgProfitPerTrade": round(avg_profit, 2),
        "avgLossPerTrade": round(abs(avg_loss), 2),  # Show as positive
        "totalProfit": round(total_profit, 2),
        "avgTradeDuration": avg_duration_str
    }


def _format_time_duration(delta: timedelta) -> str:
    """Format timedelta as human-readable string."""
    total_minutes = int(delta.total_seconds() // 60)

    if total_minutes < 60:
        return f"{total_minutes}m"
    elif total_minutes < 1440:  # Less than 24 hours
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
    else:  # Days
        days = total_minutes // 1440
        hours = (total_minutes % 1440) // 60
        return f"{days}d {hours}h" if hours > 0 else f"{days}d"


@router.get("/{config_id}/trade-history-with-decisions")
async def get_trade_history_with_decisions(
    config_id: str,
    limit: int = 50,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Get closed trade history with decision data joined.
    Respects account reset filtering - only returns trades after last reset.

    Returns:
        - trades: List of closed trades with decision confidence and reasoning
        - total_count: Number of trades returned
    """
    try:
        from core.common.db import get_db_connection

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Query closed trades with decision data, filtering by last_reset_at
                query = """
                    SELECT
                        pt.trade_id,
                        pt.symbol,
                        pt.side,
                        pt.entry_price,
                        pt.size_usd,
                        pt.leverage,
                        pt.realized_pnl,
                        pt.close_reason,
                        pt.opened_at,
                        pt.closed_at,
                        pt.confidence_score,
                        d.decision_id,
                        d.action,
                        d.confidence as decision_confidence,
                        d.reasoning
                    FROM paper_trades pt
                    LEFT JOIN decisions d ON pt.decision_id = d.decision_id
                    LEFT JOIN paper_accounts pa ON pt.config_id = pa.config_id
                    WHERE pt.config_id = %s
                      AND pt.user_id = %s
                      AND pt.status = 'closed'
                      AND pt.closed_at > COALESCE(pa.last_reset_at, '1970-01-01'::timestamptz)
                    ORDER BY pt.closed_at DESC
                    LIMIT %s
                """

                cur.execute(query, (config_id, current_user.user_id, limit))
                trades = cur.fetchall()

                # Format trades for frontend
                formatted_trades = []
                for trade in trades:
                    formatted_trades.append({
                        "trade_id": trade["trade_id"],
                        "symbol": trade["symbol"],
                        "side": trade["side"],
                        "entry_price": float(trade["entry_price"]),
                        "size_usd": float(trade["size_usd"]),
                        "leverage": int(trade["leverage"]),
                        "realized_pnl": float(trade["realized_pnl"]) if trade["realized_pnl"] is not None else 0.0,
                        "close_reason": trade["close_reason"],
                        "opened_at": trade["opened_at"].isoformat() if trade["opened_at"] else None,
                        "closed_at": trade["closed_at"].isoformat() if trade["closed_at"] else None,
                        "confidence_score": float(trade["confidence_score"]) if trade["confidence_score"] is not None else None,
                        "decision_id": trade["decision_id"],
                        "action": trade["action"],
                        "decision_confidence": float(trade["decision_confidence"]) if trade["decision_confidence"] is not None else None,
                        "reasoning": trade["reasoning"]
                    })

                return {
                    "status": "success",
                    "config_id": config_id,
                    "trades": formatted_trades,
                    "total_count": len(formatted_trades)
                }

    except Exception as e:
        logger.error(f"Failed to get trade history with decisions for {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trade history: {str(e)}")


@router.get("/{config_id}/confidence-analysis")
async def get_confidence_analysis(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Get confidence distribution analysis for winning vs losing trades.
    Returns confidence buckets: 5-35, 35-45, 45-55, 55-65, 65-95

    Returns:
        - confidence_distribution: Win/loss counts for each confidence bucket
        - summary_stats: Average confidence for wins vs losses
    """
    try:
        from core.common.db import get_db_connection

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Query closed trades with confidence scores, filtering by last_reset_at
                query = """
                    SELECT
                        pt.trade_id,
                        pt.realized_pnl,
                        pt.confidence_score,
                        CASE
                            WHEN pt.confidence_score < 0.35 THEN '5-35'
                            WHEN pt.confidence_score < 0.45 THEN '35-45'
                            WHEN pt.confidence_score < 0.55 THEN '45-55'
                            WHEN pt.confidence_score < 0.65 THEN '55-65'
                            ELSE '65-95'
                        END as confidence_bucket,
                        CASE
                            WHEN pt.realized_pnl > 0 THEN 'win'
                            ELSE 'loss'
                        END as outcome
                    FROM paper_trades pt
                    LEFT JOIN paper_accounts pa ON pt.config_id = pa.config_id
                    WHERE pt.config_id = %s
                      AND pt.user_id = %s
                      AND pt.status = 'closed'
                      AND pt.confidence_score IS NOT NULL
                      AND pt.closed_at > COALESCE(pa.last_reset_at, '1970-01-01'::timestamptz)
                """

                cur.execute(query, (config_id, current_user.user_id))
                trades = cur.fetchall()

                if not trades:
                    # No trades yet - return empty distribution
                    return {
                        "status": "success",
                        "config_id": config_id,
                        "confidence_distribution": {
                            "5-35": {"wins": 0, "losses": 0},
                            "35-45": {"wins": 0, "losses": 0},
                            "45-55": {"wins": 0, "losses": 0},
                            "55-65": {"wins": 0, "losses": 0},
                            "65-95": {"wins": 0, "losses": 0}
                        },
                        "summary_stats": {
                            "avg_confidence_wins": 0.0,
                            "avg_confidence_losses": 0.0,
                            "total_wins": 0,
                            "total_losses": 0
                        }
                    }

                # Initialize buckets
                buckets = {
                    "5-35": {"wins": 0, "losses": 0},
                    "35-45": {"wins": 0, "losses": 0},
                    "45-55": {"wins": 0, "losses": 0},
                    "55-65": {"wins": 0, "losses": 0},
                    "65-95": {"wins": 0, "losses": 0}
                }

                # Track confidence scores for averaging
                win_confidences = []
                loss_confidences = []

                # Aggregate data
                for trade in trades:
                    bucket = trade["confidence_bucket"]
                    outcome = trade["outcome"]
                    confidence = float(trade["confidence_score"])

                    if outcome == "win":
                        buckets[bucket]["wins"] += 1
                        win_confidences.append(confidence)
                    else:
                        buckets[bucket]["losses"] += 1
                        loss_confidences.append(confidence)

                # Calculate averages
                avg_win_confidence = sum(win_confidences) / len(win_confidences) if win_confidences else 0.0
                avg_loss_confidence = sum(loss_confidences) / len(loss_confidences) if loss_confidences else 0.0

                return {
                    "status": "success",
                    "config_id": config_id,
                    "confidence_distribution": buckets,
                    "summary_stats": {
                        "avg_confidence_wins": round(avg_win_confidence * 100, 1),  # Convert to percentage
                        "avg_confidence_losses": round(avg_loss_confidence * 100, 1),  # Convert to percentage
                        "total_wins": len(win_confidences),
                        "total_losses": len(loss_confidences)
                    }
                }

    except Exception as e:
        logger.error(f"Failed to get confidence analysis for {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get confidence analysis: {str(e)}")