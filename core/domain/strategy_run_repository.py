"""
StrategyRun Repository

Provides data access for strategy runs with context retrieval methods.
Handles decision context preservation for position management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import json

from core.common.db import get_db_connection
from core.common.logger import logger
from .strategy_run import StrategyRun, DecisionScenario, DecisionOutcome, DecisionContext
from .models.value_objects import Symbol, Confidence


class StrategyRunRepository:
    """Repository for strategy run data access."""
    
    def save(self, strategy_run: StrategyRun) -> None:
        """Save a strategy run to the database."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO strategy_runs (
                        strategy_run_id, trade_id, config_id, confidence_score,
                        reasoning_log, decision_data, scenario, created_at,
                        stop_loss_price, take_profit_price
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    strategy_run.strategy_run_id,
                    strategy_run.trade_id,
                    strategy_run.config_id,
                    strategy_run.confidence.score,  # Fixed: use .score not .value
                    strategy_run.reasoning_log,
                    json.dumps(strategy_run.decision_context.to_dict()),
                    strategy_run.scenario.value,
                    strategy_run.created_at,
                    strategy_run.stop_loss_price,
                    strategy_run.take_profit_price
                ))
                conn.commit()
        
        logger.info(f"Saved strategy run {strategy_run.strategy_run_id} for scenario {strategy_run.scenario.value}")
    
    def get_by_id(self, strategy_run_id: str) -> Optional[StrategyRun]:
        """Get a strategy run by ID."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT strategy_run_id, trade_id, config_id, confidence_score,
                           reasoning_log, decision_data, scenario, created_at,
                           stop_loss_price, take_profit_price
                    FROM strategy_runs
                    WHERE strategy_run_id = %s
                """, (strategy_run_id,))
                
                row = cur.fetchone()
                if not row:
                    return None
                
                return self._row_to_strategy_run(row)
    
    def get_by_trade_id(self, trade_id: str) -> List[StrategyRun]:
        """Get all strategy runs for a specific trade."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT strategy_run_id, trade_id, config_id, confidence_score,
                           reasoning_log, decision_data, scenario, created_at,
                           stop_loss_price, take_profit_price
                    FROM strategy_runs
                    WHERE trade_id = %s
                    ORDER BY created_at ASC
                """, (trade_id,))
                
                return [self._row_to_strategy_run(row) for row in cur.fetchall()]
    
    def get_entry_decision(self, trade_id: str) -> Optional[StrategyRun]:
        """Get the original entry decision for a trade."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT strategy_run_id, trade_id, config_id, confidence_score,
                           reasoning_log, decision_data, scenario, created_at,
                           stop_loss_price, take_profit_price
                    FROM strategy_runs
                    WHERE trade_id = %s 
                    AND scenario = %s
                    ORDER BY created_at ASC
                    LIMIT 1
                """, (trade_id, DecisionScenario.OPPORTUNITY_ANALYSIS.value))
                
                row = cur.fetchone()
                if not row:
                    return None
                
                return self._row_to_strategy_run(row)
    
    def get_by_scenario(self, config_id: str, scenario: DecisionScenario, 
                       limit: int = 10) -> List[StrategyRun]:
        """Get recent strategy runs for a specific scenario."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT strategy_run_id, trade_id, config_id, confidence_score,
                           reasoning_log, decision_data, scenario, created_at,
                           stop_loss_price, take_profit_price
                    FROM strategy_runs
                    WHERE config_id = %s AND scenario = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (config_id, scenario.value, limit))
                
                return [self._row_to_strategy_run(row) for row in cur.fetchall()]
    
    def get_position_management_context(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """Get complete context for position management decisions."""
        entry_decision = self.get_entry_decision(trade_id)
        if not entry_decision:
            return None
        
        # Get all management decisions for this trade
        management_decisions = []
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT strategy_run_id, confidence_score, reasoning_log, 
                           decision_data, created_at
                    FROM strategy_runs
                    WHERE trade_id = %s 
                    AND scenario = %s
                    ORDER BY created_at ASC
                """, (trade_id, DecisionScenario.POSITION_MANAGEMENT.value))
                
                for row in cur.fetchall():
                    management_decisions.append({
                        'strategy_run_id': row[0],
                        'confidence': float(row[1]) if row[1] else 0.0,
                        'reasoning': row[2] or '',
                        'decision_data': row[3] or {},
                        'timestamp': row[4]
                    })
        
        return {
            'entry_decision': {
                'strategy_run_id': entry_decision.strategy_run_id,
                'confidence': entry_decision.confidence.value,
                'reasoning': entry_decision.reasoning_log,
                'context': entry_decision.decision_context.to_dict(),
                'outcome': entry_decision.outcome.value,
                'timestamp': entry_decision.created_at
            },
            'management_history': management_decisions,
            'total_management_decisions': len(management_decisions)
        }
    
    def get_recent_by_config(self, config_id: str, limit: int = 20) -> List[StrategyRun]:
        """Get recent strategy runs for a config."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT strategy_run_id, trade_id, config_id, confidence_score,
                           reasoning_log, decision_data, scenario, created_at,
                           stop_loss_price, take_profit_price
                    FROM strategy_runs
                    WHERE config_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (config_id, limit))
                
                return [self._row_to_strategy_run(row) for row in cur.fetchall()]
    
    def get_performance_stats(self, config_id: str, 
                            days: int = 30) -> Dict[str, Any]:
        """Get performance statistics for a config."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        scenario,
                        COUNT(*) as total_decisions,
                        AVG(confidence_score) as avg_confidence,
                        MIN(confidence_score) as min_confidence,
                        MAX(confidence_score) as max_confidence
                    FROM strategy_runs
                    WHERE config_id = %s 
                    AND created_at >= NOW() - INTERVAL '%s days'
                    GROUP BY scenario
                """, (config_id, days))
                
                stats = {}
                for row in cur.fetchall():
                    scenario = row[0]
                    stats[scenario] = {
                        'total_decisions': row[1],
                        'avg_confidence': float(row[2]) if row[2] else 0.0,
                        'min_confidence': float(row[3]) if row[3] else 0.0,
                        'max_confidence': float(row[4]) if row[4] else 0.0
                    }
                
                return stats
    
    def _row_to_strategy_run(self, row) -> StrategyRun:
        """Convert database row to StrategyRun entity."""
        # Parse decision context from JSONB
        decision_data = row[5] if row[5] else {}
        decision_context = DecisionContext.from_dict(decision_data)
        
        # Extract symbol from decision context (fallback to unknown)
        symbol_str = decision_data.get('symbol', 'UNKNOWN/USD')
        symbol = Symbol.from_string(symbol_str)
        
        return StrategyRun(
            strategy_run_id=row[0],
            trade_id=row[1],
            config_id=row[2],
            scenario=DecisionScenario(row[6]),
            outcome=self._infer_outcome_from_context(decision_data),
            confidence=Confidence(score=Decimal(str(row[3])) if row[3] else Decimal('0.5')),  # Fixed
            symbol=symbol,
            reasoning_log=row[4] or '',
            decision_context=decision_context,
            created_at=row[7],
            stop_loss_price=float(row[8]) if row[8] is not None else None,
            take_profit_price=float(row[9]) if row[9] is not None else None
        )
    
    def _infer_outcome_from_context(self, decision_data: Dict[str, Any]) -> DecisionOutcome:
        """Infer decision outcome from context data."""
        # Try to get outcome from decision data
        if 'outcome' in decision_data:
            try:
                return DecisionOutcome(decision_data['outcome'])
            except ValueError:
                pass
        
        # Try to infer from action
        action = decision_data.get('action', '').lower()
        if action == 'long':
            return DecisionOutcome.ENTER_LONG
        elif action == 'short':
            return DecisionOutcome.ENTER_SHORT
        elif action == 'hold':
            return DecisionOutcome.HOLD_POSITION
        elif action == 'close':
            return DecisionOutcome.CLOSE_POSITION
        elif action in ['no_action', 'wait']:
            return DecisionOutcome.NO_ACTION
        else:
            # Default fallback
            return DecisionOutcome.NO_ACTION


# Global repository instance
strategy_run_repo = StrategyRunRepository()