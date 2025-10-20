"""
Position Manager for Paper Trading

Advanced position tracking, risk management, and P&L analytics for paper trading.
Handles portfolio-level calculations and position correlations.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor

from core.common.db import get_db_connection
from core.common.logger import logger
from .live_price_service import LivePriceService


@dataclass
class PositionSummary:
    """Summary of a single position"""
    trade_id: str
    symbol: str
    side: str
    entry_price: float
    current_price: float
    size_usd: float
    size_contracts: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    confidence_score: float
    opened_at: datetime
    age_hours: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class PortfolioSummary:
    """Summary of entire portfolio"""
    config_id: str
    total_balance: float
    available_balance: float
    total_pnl: float  # Total realized + unrealized P&L (dollar amount)
    unrealized_pnl: float
    open_positions: int
    position_value: float
    portfolio_return_pct: float  # Total P&L as percentage of initial balance
    current_pnl: float  # Sum of unrealized P&L from currently open positions
    win_rate: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    sharpe_ratio: Optional[float] = None


class PositionManager:
    """
    Advanced position management for paper trading.
    
    Provides portfolio-level analytics, risk monitoring, and position optimization.
    """
    
    def __init__(self):
        self.price_service = LivePriceService()
    
    def _get_db_connection(self):
        """Get database connection using unified connection manager"""
        return get_db_connection()
    
    async def get_position_summary(self, trade_id: str) -> Optional[PositionSummary]:
        """
        Get detailed summary for a single position.
        
        Args:
            trade_id: Trade ID to analyze
            
        Returns:
            PositionSummary with current status and metrics
        """
        try:
            with self._get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM paper_trades 
                        WHERE trade_id = %s AND status = 'open'
                    """, (trade_id,))
                    
                    trade = cur.fetchone()
                    if not trade:
                        return None
                    
                    # Get current price
                    market_price = await self.price_service.get_current_price(trade["symbol"])
                    current_price = market_price.mid
                    
                    # Calculate metrics
                    entry_price = float(trade["entry_price"])
                    size_usd = float(trade["size_usd"])
                    leverage = int(trade.get("leverage", 1))  # Get leverage from trade
                    # Calculate size in contracts from USD size
                    size_contracts = size_usd / entry_price

                    # Calculate P&L (size_usd is already the full leveraged position)
                    if trade["side"] == "long":
                        unrealized_pnl = (current_price - entry_price) * size_contracts
                    else:  # short
                        unrealized_pnl = (entry_price - current_price) * size_contracts
                    
                    unrealized_pnl_pct = (unrealized_pnl / size_usd) * 100
                    
                    # Calculate age
                    opened_at = trade["opened_at"]
                    if isinstance(opened_at, str):
                        opened_at = datetime.fromisoformat(opened_at.replace('Z', '+00:00'))
                    
                    age_hours = (datetime.now(timezone.utc) - opened_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                    
                    return PositionSummary(
                        trade_id=trade["trade_id"],
                        symbol=trade["symbol"],
                        side=trade["side"],
                        entry_price=entry_price,
                        current_price=current_price,
                        size_usd=size_usd,
                        size_contracts=size_contracts,
                        unrealized_pnl=unrealized_pnl,
                        unrealized_pnl_pct=unrealized_pnl_pct,
                        confidence_score=float(trade["confidence_score"]) if trade["confidence_score"] else 0.0,
                        opened_at=opened_at,
                        age_hours=age_hours,
                        stop_loss=float(trade["stop_loss"]) if trade["stop_loss"] else None,
                        take_profit=float(trade["take_profit"]) if trade["take_profit"] else None
                    )
                    
        except Exception as e:
            logger.error(f"Failed to get position summary for {trade_id}: {e}")
            return None
    
    async def get_portfolio_summary(self, config_id: str) -> PortfolioSummary:
        """
        Get comprehensive portfolio summary.
        
        Args:
            config_id: Configuration ID
            
        Returns:
            PortfolioSummary with all portfolio metrics
        """
        try:
            with self._get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get account info
                    cur.execute("""
                        SELECT * FROM paper_accounts 
                        WHERE config_id = %s
                    """, (config_id,))
                    
                    account = cur.fetchone()
                    if not account:
                        raise ValueError(f"No paper account found for config {config_id}")

                    # Get last reset timestamp for filtering trades
                    last_reset_at = account.get("last_reset_at")

                    # Get open positions
                    cur.execute("""
                        SELECT * FROM paper_trades
                        WHERE config_id = %s AND status = 'open'
                    """, (config_id,))

                    open_positions = cur.fetchall()

                    # Calculate unrealized P&L for open positions
                    total_unrealized_pnl = 0.0
                    total_position_value = 0.0

                    if open_positions:
                        # Get current prices for all symbols
                        symbols = list(set(pos["symbol"] for pos in open_positions))
                        prices = await self.price_service.get_multiple_prices(symbols)

                        for pos in open_positions:
                            if pos["symbol"] in prices:
                                current_price = prices[pos["symbol"]].mid
                                entry_price = float(pos["entry_price"])
                                size_usd = float(pos["size_usd"])
                                leverage = int(pos.get("leverage", 1))  # Get leverage from position
                                # Calculate size in contracts from USD size
                                size_contracts = size_usd / entry_price

                                # Calculate P&L (size_usd is already the full leveraged position)
                                if pos["side"] == "long":
                                    pnl = (current_price - entry_price) * size_contracts
                                else:
                                    pnl = (entry_price - current_price) * size_contracts

                                total_unrealized_pnl += pnl
                                total_position_value += current_price * size_contracts

                    # Get closed trades for analytics (only since last reset)
                    if last_reset_at:
                        cur.execute("""
                            SELECT realized_pnl, closed_at FROM paper_trades
                            WHERE config_id = %s AND status = 'closed' AND closed_at > %s
                            ORDER BY closed_at DESC
                        """, (config_id, last_reset_at))
                    else:
                        # No reset yet, get all closed trades
                        cur.execute("""
                            SELECT realized_pnl, closed_at FROM paper_trades
                            WHERE config_id = %s AND status = 'closed'
                            ORDER BY closed_at DESC
                        """, (config_id,))
                    
                    closed_trades = cur.fetchall()
                    
                    # Calculate win/loss statistics
                    wins = [float(t["realized_pnl"]) for t in closed_trades if float(t["realized_pnl"]) > 0]
                    losses = [float(t["realized_pnl"]) for t in closed_trades if float(t["realized_pnl"]) <= 0]
                    
                    win_rate = len(wins) / len(closed_trades) * 100 if closed_trades else 0
                    avg_win = sum(wins) / len(wins) if wins else 0
                    avg_loss = sum(losses) / len(losses) if losses else 0
                    largest_win = max(wins) if wins else 0
                    largest_loss = min(losses) if losses else 0

                    # Calculate current P&L (unrealized P&L from open positions)
                    # This shows aggregate P&L of active trades
                    current_pnl = total_unrealized_pnl

                    # Portfolio metrics
                    total_balance = float(account["current_balance"]) + total_position_value
                    available_balance = float(account["current_balance"])
                    total_pnl = float(account["total_pnl"]) + total_unrealized_pnl
                    initial_balance = float(account["initial_balance"])
                    # Portfolio return = total P&L as percentage of initial balance
                    portfolio_return_pct = (total_pnl / initial_balance) * 100 if initial_balance > 0 else 0
                    
                    return PortfolioSummary(
                        config_id=config_id,
                        total_balance=total_balance,
                        available_balance=available_balance,
                        total_pnl=total_pnl,
                        unrealized_pnl=total_unrealized_pnl,
                        open_positions=len(open_positions),
                        position_value=total_position_value,
                        portfolio_return_pct=portfolio_return_pct,
                        current_pnl=current_pnl,
                        win_rate=win_rate,
                        avg_win=avg_win,
                        avg_loss=avg_loss,
                        largest_win=largest_win,
                        largest_loss=largest_loss,
                        sharpe_ratio=None  # Could calculate if we had daily returns
                    )
                    
        except Exception as e:
            logger.error(f"Failed to get portfolio summary for {config_id}: {e}")
            raise
    
    async def get_position_risk_metrics(self, config_id: str) -> Dict[str, Any]:
        """
        Calculate risk metrics for current positions.
        
        Args:
            config_id: Configuration ID
            
        Returns:
            Dictionary with various risk metrics
        """
        try:
            portfolio = await self.get_portfolio_summary(config_id)
            
            with self._get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get open positions
                    cur.execute("""
                        SELECT symbol, side, size_usd, unrealized_pnl, confidence_score
                        FROM paper_trades 
                        WHERE config_id = %s AND status = 'open'
                    """, (config_id,))
                    
                    positions = cur.fetchall()
                    
                    if not positions:
                        return {
                            "total_exposure": 0.0,
                            "exposure_percentage": 0.0,
                            "concentration_risk": 0.0,
                            "largest_position_pct": 0.0,
                            "positions_at_risk": 0,
                            "drawdown_risk": 0.0
                        }
                    
                    # Calculate exposure metrics
                    position_sizes = [float(pos["size_usd"]) for pos in positions]
                    total_exposure = sum(position_sizes)
                    exposure_percentage = (total_exposure / portfolio.total_balance) * 100
                    
                    # Concentration risk (largest position as % of portfolio)
                    largest_position = max(position_sizes)
                    largest_position_pct = (largest_position / portfolio.total_balance) * 100
                    
                    # Count positions with negative P&L > 5%
                    positions_at_risk = sum(1 for pos in positions if float(pos["unrealized_pnl"]) < -float(pos["size_usd"]) * 0.05)
                    
                    # Symbol concentration (Herfindahl index)
                    symbol_exposure = {}
                    for pos in positions:
                        symbol = pos["symbol"]
                        size = float(pos["size_usd"])
                        symbol_exposure[symbol] = symbol_exposure.get(symbol, 0) + size
                    
                    # Calculate concentration index
                    total_value = sum(symbol_exposure.values())
                    concentration_risk = sum((exposure / total_value) ** 2 for exposure in symbol_exposure.values())
                    
                    # Potential drawdown (if all positions hit -10%)
                    max_potential_loss = total_exposure * 0.10
                    drawdown_risk = (max_potential_loss / portfolio.total_balance) * 100
                    
                    return {
                        "total_exposure": total_exposure,
                        "exposure_percentage": exposure_percentage,
                        "concentration_risk": concentration_risk,
                        "largest_position_pct": largest_position_pct,
                        "positions_at_risk": positions_at_risk,
                        "drawdown_risk": drawdown_risk,
                        "symbol_count": len(symbol_exposure),
                        "symbol_exposure": symbol_exposure
                    }
                    
        except Exception as e:
            logger.error(f"Failed to calculate risk metrics for {config_id}: {e}")
            return {"error": str(e)}
    
    async def get_performance_analytics(self, config_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get detailed performance analytics.
        
        Args:
            config_id: Configuration ID
            days: Number of days to analyze
            
        Returns:
            Performance analytics dictionary
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            with self._get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get closed trades in period
                    cur.execute("""
                        SELECT symbol, side, realized_pnl, confidence_score, 
                               EXTRACT(EPOCH FROM (closed_at - opened_at))/3600 as duration_hours,
                               opened_at, closed_at
                        FROM paper_trades 
                        WHERE config_id = %s AND status = 'closed' AND closed_at >= %s
                        ORDER BY closed_at
                    """, (config_id, cutoff_date))
                    
                    trades = cur.fetchall()
                    
                    if not trades:
                        return {"message": f"No trades in the last {days} days"}
                    
                    # Basic statistics
                    pnls = [float(t["realized_pnl"]) for t in trades]
                    wins = [pnl for pnl in pnls if pnl > 0]
                    losses = [pnl for pnl in pnls if pnl <= 0]
                    
                    total_pnl = sum(pnls)
                    win_rate = (len(wins) / len(trades)) * 100
                    avg_trade = total_pnl / len(trades)
                    
                    # Confidence score analysis
                    high_conf_trades = [t for t in trades if float(t["confidence_score"] or 0) >= 0.7]
                    high_conf_pnl = sum(float(t["realized_pnl"]) for t in high_conf_trades)
                    high_conf_win_rate = (sum(1 for t in high_conf_trades if float(t["realized_pnl"]) > 0) / len(high_conf_trades) * 100) if high_conf_trades else 0
                    
                    # Symbol performance
                    symbol_stats = {}
                    for trade in trades:
                        symbol = trade["symbol"]
                        pnl = float(trade["realized_pnl"])
                        
                        if symbol not in symbol_stats:
                            symbol_stats[symbol] = {"trades": 0, "pnl": 0, "wins": 0}
                        
                        symbol_stats[symbol]["trades"] += 1
                        symbol_stats[symbol]["pnl"] += pnl
                        if pnl > 0:
                            symbol_stats[symbol]["wins"] += 1
                    
                    # Add win rates
                    for symbol in symbol_stats:
                        stats = symbol_stats[symbol]
                        stats["win_rate"] = (stats["wins"] / stats["trades"]) * 100
                    
                    # Time-based analysis
                    durations = [float(t["duration_hours"]) for t in trades]
                    avg_duration = sum(durations) / len(durations)
                    
                    # Quick trades (<1 hour) vs long trades (>24 hours)
                    quick_trades = [t for t in trades if float(t["duration_hours"]) < 1]
                    long_trades = [t for t in trades if float(t["duration_hours"]) > 24]
                    
                    quick_pnl = sum(float(t["realized_pnl"]) for t in quick_trades)
                    long_pnl = sum(float(t["realized_pnl"]) for t in long_trades)
                    
                    return {
                        "period_days": days,
                        "total_trades": len(trades),
                        "total_pnl": total_pnl,
                        "win_rate": win_rate,
                        "avg_trade_pnl": avg_trade,
                        "avg_win": sum(wins) / len(wins) if wins else 0,
                        "avg_loss": sum(losses) / len(losses) if losses else 0,
                        "best_trade": max(pnls),
                        "worst_trade": min(pnls),
                        "avg_duration_hours": avg_duration,
                        "confidence_analysis": {
                            "high_confidence_trades": len(high_conf_trades),
                            "high_confidence_pnl": high_conf_pnl,
                            "high_confidence_win_rate": high_conf_win_rate
                        },
                        "symbol_performance": dict(sorted(symbol_stats.items(), key=lambda x: x[1]["pnl"], reverse=True)),
                        "duration_analysis": {
                            "quick_trades": len(quick_trades),
                            "quick_trades_pnl": quick_pnl,
                            "long_trades": len(long_trades),
                            "long_trades_pnl": long_pnl
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get performance analytics for {config_id}: {e}")
            return {"error": str(e)}
    
    async def suggest_position_adjustments(self, config_id: str) -> List[Dict[str, Any]]:
        """
        Suggest position adjustments based on current portfolio state.
        
        Args:
            config_id: Configuration ID
            
        Returns:
            List of suggested adjustments
        """
        suggestions = []
        
        try:
            # Get current positions
            with self._get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT trade_id, symbol, side, size_usd, unrealized_pnl, 
                               confidence_score, opened_at, stop_loss, take_profit
                        FROM paper_trades 
                        WHERE config_id = %s AND status = 'open'
                    """, (config_id,))
                    
                    positions = cur.fetchall()
            
            # Get risk metrics
            risk_metrics = await self.get_position_risk_metrics(config_id)
            
            # Suggestion 1: Close positions with large unrealized losses
            for pos in positions:
                pnl = float(pos["unrealized_pnl"])
                size = float(pos["size_usd"])
                loss_pct = (pnl / size) * 100 if size > 0 else 0
                
                if loss_pct < -15:  # >15% loss
                    suggestions.append({
                        "type": "close_position",
                        "trade_id": pos["trade_id"],
                        "symbol": pos["symbol"],
                        "reason": f"Large unrealized loss: {loss_pct:.1f}%",
                        "priority": "high"
                    })
            
            # Suggestion 2: Take profits on positions with large gains
            for pos in positions:
                pnl = float(pos["unrealized_pnl"])
                size = float(pos["size_usd"])
                gain_pct = (pnl / size) * 100 if size > 0 else 0
                
                if gain_pct > 20 and not pos["take_profit"]:  # >20% gain without take profit
                    suggestions.append({
                        "type": "set_take_profit",
                        "trade_id": pos["trade_id"],
                        "symbol": pos["symbol"],
                        "reason": f"Large unrealized gain: {gain_pct:.1f}% - consider taking partial profits",
                        "priority": "medium"
                    })
            
            # Suggestion 3: Reduce exposure if too high
            if risk_metrics.get("exposure_percentage", 0) > 80:
                suggestions.append({
                    "type": "reduce_exposure",
                    "reason": f"High portfolio exposure: {risk_metrics['exposure_percentage']:.1f}%",
                    "priority": "high"
                })
            
            # Suggestion 4: Address concentration risk
            if risk_metrics.get("concentration_risk", 0) > 0.5:  # Highly concentrated
                suggestions.append({
                    "type": "diversify",
                    "reason": "High concentration risk - consider diversifying across more symbols",
                    "priority": "medium"
                })
            
            # Suggestion 5: Set stop losses for positions without them
            for pos in positions:
                if not pos["stop_loss"]:
                    pnl = float(pos["unrealized_pnl"])
                    size = float(pos["size_usd"])
                    if pnl < -size * 0.05:  # Position down >5% without stop loss
                        suggestions.append({
                            "type": "set_stop_loss",
                            "trade_id": pos["trade_id"],
                            "symbol": pos["symbol"],
                            "reason": "Position declining without stop loss protection",
                            "priority": "medium"
                        })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to generate position suggestions for {config_id}: {e}")
            return [{"type": "error", "reason": str(e)}]


# Convenience functions
async def get_portfolio_overview(config_id: str) -> Dict[str, Any]:
    """Get comprehensive portfolio overview"""
    manager = PositionManager()
    portfolio = await manager.get_portfolio_summary(config_id)
    risk_metrics = await manager.get_position_risk_metrics(config_id)
    
    return {
        "portfolio": portfolio.__dict__,
        "risk_metrics": risk_metrics
    }