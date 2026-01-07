"""
Performance Analyzer Service

Universal bot performance analysis that works for any ggbot configuration.
Extracts patterns from market data, correlates with trade outcomes, and
generates actionable insights.

Key capabilities:
- Basic stats: win rate, R:R ratio, P&L, breakeven WR
- Universal pattern extraction from all data types
- Pattern combination analysis (confirmation vs risk patterns)
- Timeframe alignment and cross-domain correlations
- Exit reasoning classification
- Confidence calibration analysis
"""

import os
import re
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from itertools import combinations
from typing import Dict, List, Optional, Set, Tuple, Any

import anthropic

from core.common.db import get_db_connection
from core.common.logger import logger


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class BasicStats:
    """Core trading statistics."""
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    risk_reward_ratio: float = 0.0
    breakeven_winrate: float = 0.0
    total_pnl: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0


@dataclass
class DirectionStats:
    """Per-direction (long/short) statistics."""
    side: str
    trades: int = 0
    wins: int = 0
    win_rate: float = 0.0
    avg_pnl: float = 0.0
    total_pnl: float = 0.0


@dataclass
class PatternOutcome:
    """Outcome statistics for a single pattern or pattern combination."""
    pattern: str
    trades: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl: float = 0.0

    @property
    def win_rate(self) -> float:
        if self.trades == 0:
            return 0.0
        return self.wins / self.trades

    @property
    def avg_pnl(self) -> float:
        if self.trades == 0:
            return 0.0
        return self.total_pnl / self.trades


@dataclass
class ConfidenceBucket:
    """Confidence calibration bucket."""
    range_label: str
    min_conf: float
    max_conf: float
    trades: int = 0
    wins: int = 0
    total_pnl: float = 0.0

    @property
    def actual_win_rate(self) -> float:
        if self.trades == 0:
            return 0.0
        return self.wins / self.trades

    @property
    def expected_win_rate(self) -> float:
        """Midpoint of confidence range as expected WR."""
        return (self.min_conf + self.max_conf) / 2

    @property
    def calibration_gap(self) -> float:
        """Difference between expected and actual WR."""
        return self.expected_win_rate - self.actual_win_rate


@dataclass
class ExitClassification:
    """Exit reasoning classification."""
    exit_type: str
    trades: int = 0
    wins: int = 0
    total_pnl: float = 0.0

    @property
    def win_rate(self) -> float:
        if self.trades == 0:
            return 0.0
        return self.wins / self.trades

    @property
    def avg_pnl(self) -> float:
        if self.trades == 0:
            return 0.0
        return self.total_pnl / self.trades


@dataclass
class PerformanceReport:
    """Complete performance analysis report."""
    config_id: str
    config_name: str
    analysis_timestamp: datetime
    trade_count: int

    # Core stats
    basic_stats: BasicStats = field(default_factory=BasicStats)
    direction_stats: List[DirectionStats] = field(default_factory=list)

    # Pattern analysis
    confirmation_patterns: List[PatternOutcome] = field(default_factory=list)
    risk_patterns: List[PatternOutcome] = field(default_factory=list)
    best_combinations: List[PatternOutcome] = field(default_factory=list)
    worst_combinations: List[PatternOutcome] = field(default_factory=list)

    # Timeframe analysis
    tf_alignment_stats: List[PatternOutcome] = field(default_factory=list)

    # Confidence calibration
    confidence_buckets: List[ConfidenceBucket] = field(default_factory=list)

    # Exit analysis
    exit_classifications: List[ExitClassification] = field(default_factory=list)

    # Synthesized insights (populated by LLM)
    critical_issues: List[Dict[str, str]] = field(default_factory=list)
    positive_edges: List[Dict[str, str]] = field(default_factory=list)
    recommendations: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for API response."""
        return {
            "config_id": self.config_id,
            "config_name": self.config_name,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "trade_count": self.trade_count,
            "basic_stats": {
                "total_trades": self.basic_stats.total_trades,
                "wins": self.basic_stats.wins,
                "losses": self.basic_stats.losses,
                "win_rate": round(self.basic_stats.win_rate * 100, 1),
                "avg_win": round(self.basic_stats.avg_win, 2),
                "avg_loss": round(self.basic_stats.avg_loss, 2),
                "risk_reward_ratio": round(self.basic_stats.risk_reward_ratio, 2),
                "breakeven_winrate": round(self.basic_stats.breakeven_winrate * 100, 1),
                "total_pnl": round(self.basic_stats.total_pnl, 2),
                "largest_win": round(self.basic_stats.largest_win, 2),
                "largest_loss": round(self.basic_stats.largest_loss, 2),
            },
            "direction_stats": [
                {
                    "side": ds.side,
                    "trades": ds.trades,
                    "wins": ds.wins,
                    "win_rate": round(ds.win_rate * 100, 1),
                    "avg_pnl": round(ds.avg_pnl, 2),
                    "total_pnl": round(ds.total_pnl, 2),
                }
                for ds in self.direction_stats
            ],
            "confirmation_patterns": [
                {
                    "pattern": p.pattern,
                    "trades": p.trades,
                    "win_rate": round(p.win_rate * 100, 1),
                    "total_pnl": round(p.total_pnl, 2),
                }
                for p in self.confirmation_patterns[:10]
            ],
            "risk_patterns": [
                {
                    "pattern": p.pattern,
                    "trades": p.trades,
                    "win_rate": round(p.win_rate * 100, 1),
                    "total_pnl": round(p.total_pnl, 2),
                }
                for p in self.risk_patterns[:10]
            ],
            "best_combinations": [
                {
                    "pattern": p.pattern,
                    "trades": p.trades,
                    "win_rate": round(p.win_rate * 100, 1),
                    "total_pnl": round(p.total_pnl, 2),
                }
                for p in self.best_combinations[:10]
            ],
            "worst_combinations": [
                {
                    "pattern": p.pattern,
                    "trades": p.trades,
                    "win_rate": round(p.win_rate * 100, 1),
                    "total_pnl": round(p.total_pnl, 2),
                }
                for p in self.worst_combinations[:10]
            ],
            "tf_alignment_stats": [
                {
                    "pattern": p.pattern,
                    "trades": p.trades,
                    "win_rate": round(p.win_rate * 100, 1),
                    "total_pnl": round(p.total_pnl, 2),
                }
                for p in self.tf_alignment_stats
            ],
            "confidence_calibration": [
                {
                    "range": cb.range_label,
                    "trades": cb.trades,
                    "actual_win_rate": round(cb.actual_win_rate * 100, 1),
                    "expected_win_rate": round(cb.expected_win_rate * 100, 1),
                    "calibration_gap": round(cb.calibration_gap * 100, 1),
                    "total_pnl": round(cb.total_pnl, 2),
                }
                for cb in self.confidence_buckets
            ],
            "exit_classifications": [
                {
                    "type": ec.exit_type,
                    "trades": ec.trades,
                    "win_rate": round(ec.win_rate * 100, 1),
                    "avg_pnl": round(ec.avg_pnl, 2),
                    "total_pnl": round(ec.total_pnl, 2),
                }
                for ec in self.exit_classifications
            ],
            "insights": {
                "critical_issues": self.critical_issues,
                "positive_edges": self.positive_edges,
                "recommendations": self.recommendations,
            }
        }


# =============================================================================
# Pattern Extraction
# =============================================================================

class PatternExtractor:
    """Extracts trading patterns from market query data."""

    @staticmethod
    def extract_technical_patterns(tech_text: Optional[str]) -> Set[str]:
        """
        Extract all detected patterns from technical analysis text.

        Returns patterns in format: {timeframe}_{pattern_name}
        e.g., "1H_overbought", "4H_divergence", "15M_bullish_xover"
        """
        if not tech_text:
            return set()

        patterns = set()

        # Split by timeframe sections
        tf_sections = re.split(r'===\s*(\d+[mhdwMHDW])\s*===', tech_text)

        current_tf = None
        for section in tf_sections:
            # Check if this is a timeframe marker
            if re.match(r'^\d+[mhdwMHDW]$', section, re.IGNORECASE):
                current_tf = section.upper()
                continue

            if not current_tf:
                continue

            section_lower = section.lower()

            # Extract explicit "Patterns:" fields
            pattern_matches = re.findall(r'Patterns?:\s*([^\n]+)', section, re.IGNORECASE)
            for match in pattern_matches:
                for p in match.split(','):
                    p = p.strip().lower().replace(' ', '_')
                    if p and p not in ['none', '']:
                        patterns.add(f'{current_tf}_{p}')

            # Extract divergences
            div_matches = re.findall(r'Divergence:\s*([^\n]+)', section, re.IGNORECASE)
            for match in div_matches:
                patterns.add(f'{current_tf}_divergence_{match.strip().lower().replace(" ", "_")}')

            # Extract key conditions
            if 'overbought' in section_lower:
                patterns.add(f'{current_tf}_overbought')
            if 'oversold' in section_lower:
                patterns.add(f'{current_tf}_oversold')
            if 'bullish crossover' in section_lower:
                patterns.add(f'{current_tf}_bullish_xover')
            if 'bearish crossover' in section_lower:
                patterns.add(f'{current_tf}_bearish_xover')
            if 'strong_uptrend' in section_lower or 'strong bullish' in section_lower:
                patterns.add(f'{current_tf}_strong_bullish')
            if 'strong_downtrend' in section_lower or 'strong bearish' in section_lower:
                patterns.add(f'{current_tf}_strong_bearish')
            if 'accumulation' in section_lower:
                patterns.add(f'{current_tf}_accumulation')
            if 'distribution' in section_lower:
                patterns.add(f'{current_tf}_distribution')
            if re.search(r'macd.*rising|rising.*macd', section_lower):
                patterns.add(f'{current_tf}_macd_rising')
            if re.search(r'macd.*falling|falling.*macd', section_lower):
                patterns.add(f'{current_tf}_macd_falling')

        return patterns

    @staticmethod
    def extract_sentiment_patterns(intel_text: Optional[str]) -> Set[str]:
        """Extract patterns from market intelligence (sentiment, funding)."""
        if not intel_text:
            return set()

        patterns = set()

        # Twitter sentiment
        signal_match = re.search(r'Signal:\s*(\w+)', intel_text)
        if signal_match:
            patterns.add(f'twitter_{signal_match.group(1).lower()}')

        # Sentiment score buckets
        score_match = re.search(r'Sentiment Score:\s*([\d.-]+)', intel_text)
        if score_match:
            score = float(score_match.group(1))
            if score > 0.3:
                patterns.add('sentiment_bullish')
            elif score < -0.3:
                patterns.add('sentiment_bearish')
            else:
                patterns.add('sentiment_neutral')

        # Funding rates
        btc_fund = re.search(r'BTC Funding Rate.*?([\d.-]+)%.*?\((\w+)\)', intel_text, re.DOTALL)
        if btc_fund:
            patterns.add(f'funding_{btc_fund.group(2).lower()}')
            rate = float(btc_fund.group(1))
            if rate > 0.05:
                patterns.add('funding_high')
            elif rate < -0.01:
                patterns.add('funding_negative')

        return patterns

    @staticmethod
    def extract_volume_patterns(volume_text: Optional[str]) -> Set[str]:
        """Extract patterns from volume confirmation."""
        if not volume_text:
            return set()

        patterns = set()

        # Volume ratio
        ratio_match = re.search(r'Volume Ratio:\s*([\d.]+)x', volume_text)
        if ratio_match:
            ratio = float(ratio_match.group(1))
            if ratio > 1.5:
                patterns.add('volume_high')
            elif ratio < 0.8:
                patterns.add('volume_low')
            else:
                patterns.add('volume_normal')

        # Confirmation level
        conf_match = re.search(r'Confirmation Level:\s*([^\n-]+)', volume_text)
        if conf_match:
            level = conf_match.group(1).strip().lower()
            if 'strong' in level:
                patterns.add('volume_strong_confirm')
            elif 'weak' in level:
                patterns.add('volume_weak_confirm')

        return patterns

    @classmethod
    def extract_all_patterns(
        cls,
        tech_text: Optional[str],
        intel_text: Optional[str],
        volume_text: Optional[str]
    ) -> Set[str]:
        """Extract all patterns from all data sources."""
        patterns = set()
        patterns.update(cls.extract_technical_patterns(tech_text))
        patterns.update(cls.extract_sentiment_patterns(intel_text))
        patterns.update(cls.extract_volume_patterns(volume_text))
        return patterns


# =============================================================================
# Exit Classification
# =============================================================================

class ExitClassifier:
    """Classifies exit reasoning into categories."""

    @staticmethod
    def classify_exit(exit_reasoning: Optional[str], pnl: float) -> str:
        """
        Classify exit reasoning into one of:
        - thesis_complete: Original setup played out
        - profit_take: Taking profit for other reasons
        - thesis_invalid: Setup no longer valid
        - trend_override: Trend too strong, capitulated
        - stop_loss: Hit stop loss
        - take_profit: Hit take profit
        - unknown: Can't determine
        """
        if not exit_reasoning:
            return "unknown"

        text = exit_reasoning.lower()

        if pnl > 0:
            # Profitable exits
            if any(phrase in text for phrase in [
                "lock in", "secure", "mean-reverted",
                "no longer at extremes", "overextension has diminished",
                "indicators no longer"
            ]):
                return "thesis_complete"
            else:
                return "profit_take"
        else:
            # Loss exits
            if any(phrase in text for phrase in [
                "adx", "strengthening", "accelerating",
                "trend is not exhausting"
            ]) and any(phrase in text for phrase in [">30", "strong"]):
                return "trend_override"
            elif any(phrase in text for phrase in [
                "avoid further losses", "risk management"
            ]):
                return "capitulation"
            elif any(phrase in text for phrase in [
                "no longer aligns", "setup no longer", "doesn't meet"
            ]):
                return "thesis_invalid"
            else:
                return "other_loss"


# =============================================================================
# Performance Analyzer
# =============================================================================

class PerformanceAnalyzer:
    """
    Analyzes bot trading performance and generates insights.

    Usage:
        analyzer = PerformanceAnalyzer(config_id)
        report = await analyzer.analyze()
    """

    MIN_TRADES_FOR_ANALYSIS = 10
    MIN_TRADES_FOR_PATTERN = 3

    def __init__(self, config_id: str):
        self.config_id = config_id
        self.pattern_extractor = PatternExtractor()
        self.exit_classifier = ExitClassifier()

    async def analyze(self, include_llm_insights: bool = True) -> PerformanceReport:
        """Run full performance analysis and return report."""

        # Get config info
        config_name = await self._get_config_name()

        # Get trade data with market queries
        trades = await self._get_trades_with_market_data()

        if len(trades) < self.MIN_TRADES_FOR_ANALYSIS:
            logger.bind(config_id=self.config_id).info(
                f"Insufficient trades for analysis: {len(trades)}"
            )
            return PerformanceReport(
                config_id=self.config_id,
                config_name=config_name,
                analysis_timestamp=datetime.utcnow(),
                trade_count=len(trades),
            )

        # Build report
        report = PerformanceReport(
            config_id=self.config_id,
            config_name=config_name,
            analysis_timestamp=datetime.utcnow(),
            trade_count=len(trades),
        )

        # Calculate all analyses
        report.basic_stats = self._calculate_basic_stats(trades)
        report.direction_stats = self._calculate_direction_stats(trades)
        report.confidence_buckets = self._calculate_confidence_calibration(trades)
        report.exit_classifications = await self._classify_exits(trades)

        # Pattern analysis
        pattern_results = self._analyze_patterns(trades)
        report.confirmation_patterns = pattern_results['confirmation']
        report.risk_patterns = pattern_results['risk']
        report.best_combinations = pattern_results['best_combos']
        report.worst_combinations = pattern_results['worst_combos']
        report.tf_alignment_stats = pattern_results['tf_alignment']

        # LLM synthesis (optional)
        if include_llm_insights:
            await self._synthesize_insights(report)

        logger.bind(
            config_id=self.config_id,
            trade_count=len(trades)
        ).info("Performance analysis completed")

        return report

    async def _get_config_name(self) -> str:
        """Get configuration name."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT config_name FROM configurations WHERE config_id = %s",
                        (self.config_id,)
                    )
                    result = cur.fetchone()
                    return result[0] if result else "Unknown Bot"
        except Exception as e:
            logger.error(f"Failed to get config name: {e}")
            return "Unknown Bot"

    async def _get_trades_with_market_data(self) -> List[Dict]:
        """
        Get all closed trades with their preceding market query data.
        """
        trades = []

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get trades with market data
                    cur.execute("""
                        WITH closed_trades AS (
                            SELECT
                                trade_id, side, realized_pnl, confidence_score,
                                opened_at, closed_at, close_reason
                            FROM paper_trades
                            WHERE config_id = %s AND status = 'closed'
                        )
                        SELECT
                            t.trade_id, t.side, t.realized_pnl, t.confidence_score,
                            t.opened_at, t.closed_at, t.close_reason,
                            entry_mq.details->'formatted_data'->>'technical_analysis' as entry_tech,
                            entry_mq.details->'formatted_data'->>'market_intelligence' as entry_intel,
                            entry_mq.details->'formatted_data'->>'volume_confirmation' as entry_volume,
                            exit_thought.details->>'thought' as exit_reasoning,
                            exit_thought.details->>'confidence' as exit_confidence
                        FROM closed_trades t
                        LEFT JOIN LATERAL (
                            SELECT details
                            FROM activities
                            WHERE config_id = %s
                              AND activity_type = 'market_query'
                              AND created_at <= t.opened_at
                            ORDER BY created_at DESC
                            LIMIT 1
                        ) entry_mq ON true
                        LEFT JOIN LATERAL (
                            SELECT details
                            FROM activities
                            WHERE config_id = %s
                              AND activity_type = 'llm_thought'
                              AND created_at <= t.closed_at
                              AND created_at >= t.closed_at - INTERVAL '5 minutes'
                            ORDER BY created_at DESC
                            LIMIT 1
                        ) exit_thought ON true
                        ORDER BY t.opened_at
                    """, (self.config_id, self.config_id, self.config_id))

                    for row in cur.fetchall():
                        (trade_id, side, pnl, conf, opened, closed, close_reason,
                         entry_tech, entry_intel, entry_volume,
                         exit_reasoning, exit_conf) = row

                        # Extract patterns
                        patterns = self.pattern_extractor.extract_all_patterns(
                            entry_tech, entry_intel, entry_volume
                        )

                        trades.append({
                            'trade_id': trade_id,
                            'side': side,
                            'pnl': float(pnl) if pnl else 0.0,
                            'win': float(pnl) > 0 if pnl else False,
                            'confidence': float(conf) if conf else None,
                            'opened_at': opened,
                            'closed_at': closed,
                            'close_reason': close_reason,
                            'patterns': patterns,
                            'exit_reasoning': exit_reasoning,
                            'exit_confidence': float(exit_conf) if exit_conf else None,
                        })

        except Exception as e:
            logger.error(f"Failed to get trades with market data: {e}")

        return trades

    def _calculate_basic_stats(self, trades: List[Dict]) -> BasicStats:
        """Calculate basic trading statistics."""
        stats = BasicStats()

        if not trades:
            return stats

        stats.total_trades = len(trades)

        wins = [t for t in trades if t['win']]
        losses = [t for t in trades if not t['win']]

        stats.wins = len(wins)
        stats.losses = len(losses)
        stats.win_rate = stats.wins / stats.total_trades if stats.total_trades > 0 else 0

        win_pnls = [t['pnl'] for t in wins]
        loss_pnls = [t['pnl'] for t in losses]

        stats.avg_win = sum(win_pnls) / len(win_pnls) if win_pnls else 0
        stats.avg_loss = sum(loss_pnls) / len(loss_pnls) if loss_pnls else 0

        if stats.avg_loss != 0:
            stats.risk_reward_ratio = abs(stats.avg_win / stats.avg_loss)
            stats.breakeven_winrate = 1 / (1 + stats.risk_reward_ratio)

        stats.total_pnl = sum(t['pnl'] for t in trades)
        stats.largest_win = max(win_pnls) if win_pnls else 0
        stats.largest_loss = min(loss_pnls) if loss_pnls else 0

        return stats

    def _calculate_direction_stats(self, trades: List[Dict]) -> List[DirectionStats]:
        """Calculate per-direction statistics."""
        direction_data = defaultdict(lambda: {'trades': [], 'wins': 0, 'pnl': 0})

        for trade in trades:
            side = trade['side']
            direction_data[side]['trades'].append(trade)
            if trade['win']:
                direction_data[side]['wins'] += 1
            direction_data[side]['pnl'] += trade['pnl']

        stats = []
        for side, data in direction_data.items():
            count = len(data['trades'])
            ds = DirectionStats(
                side=side,
                trades=count,
                wins=data['wins'],
                win_rate=data['wins'] / count if count > 0 else 0,
                avg_pnl=data['pnl'] / count if count > 0 else 0,
                total_pnl=data['pnl'],
            )
            stats.append(ds)

        return sorted(stats, key=lambda x: x.total_pnl, reverse=True)

    def _calculate_confidence_calibration(self, trades: List[Dict]) -> List[ConfidenceBucket]:
        """Calculate confidence calibration buckets."""
        buckets = [
            ConfidenceBucket("50-55%", 0.50, 0.55),
            ConfidenceBucket("55-60%", 0.55, 0.60),
            ConfidenceBucket("60-65%", 0.60, 0.65),
            ConfidenceBucket("65-70%", 0.65, 0.70),
            ConfidenceBucket("70-75%", 0.70, 0.75),
            ConfidenceBucket("75%+", 0.75, 1.00),
        ]

        for trade in trades:
            conf = trade['confidence']
            if conf is None:
                continue

            for bucket in buckets:
                if bucket.min_conf <= conf < bucket.max_conf or \
                   (bucket.max_conf == 1.0 and conf >= bucket.min_conf):
                    bucket.trades += 1
                    if trade['win']:
                        bucket.wins += 1
                    bucket.total_pnl += trade['pnl']
                    break

        # Filter out empty buckets
        return [b for b in buckets if b.trades > 0]

    async def _classify_exits(self, trades: List[Dict]) -> List[ExitClassification]:
        """Classify all trade exits."""
        classifications = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0})

        for trade in trades:
            exit_type = self.exit_classifier.classify_exit(
                trade['exit_reasoning'], trade['pnl']
            )
            classifications[exit_type]['trades'] += 1
            if trade['win']:
                classifications[exit_type]['wins'] += 1
            classifications[exit_type]['pnl'] += trade['pnl']

        result = []
        for exit_type, data in classifications.items():
            ec = ExitClassification(
                exit_type=exit_type,
                trades=data['trades'],
                wins=data['wins'],
                total_pnl=data['pnl'],
            )
            result.append(ec)

        return sorted(result, key=lambda x: x.total_pnl, reverse=True)

    def _analyze_patterns(self, trades: List[Dict]) -> Dict[str, List[PatternOutcome]]:
        """
        Analyze pattern correlations with outcomes.

        Returns:
            Dict with keys: confirmation, risk, best_combos, worst_combos, tf_alignment
        """
        # Single pattern outcomes
        pattern_outcomes = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0})

        # Pattern combination outcomes
        combo_outcomes = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0})

        # TF alignment outcomes
        alignment_outcomes = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0})

        for trade in trades:
            side = trade['side']
            patterns = trade['patterns']
            win = trade['win']
            pnl = trade['pnl']

            # Record single pattern outcomes
            for pattern in patterns:
                key = f"{side}_{pattern}"
                pattern_outcomes[key]['pnl'] += pnl
                if win:
                    pattern_outcomes[key]['wins'] += 1
                else:
                    pattern_outcomes[key]['losses'] += 1

            # Record 2-pattern combinations
            sorted_patterns = sorted(patterns)
            for combo in combinations(sorted_patterns, 2):
                key = f"{side} + {combo[0]} + {combo[1]}"
                combo_outcomes[key]['pnl'] += pnl
                if win:
                    combo_outcomes[key]['wins'] += 1
                else:
                    combo_outcomes[key]['losses'] += 1

            # TF alignment analysis
            bullish_tfs = sum(1 for p in patterns if any(
                x in p for x in ['overbought', 'strong_bullish', 'accumulation', 'bullish_xover']
            ))
            bearish_tfs = sum(1 for p in patterns if any(
                x in p for x in ['oversold', 'strong_bearish', 'distribution', 'bearish_xover']
            ))

            if bullish_tfs >= 3:
                key = f"{side} + 3+ TF bullish alignment"
                alignment_outcomes[key]['pnl'] += pnl
                if win:
                    alignment_outcomes[key]['wins'] += 1
                else:
                    alignment_outcomes[key]['losses'] += 1

            if bearish_tfs >= 3:
                key = f"{side} + 3+ TF bearish alignment"
                alignment_outcomes[key]['pnl'] += pnl
                if win:
                    alignment_outcomes[key]['wins'] += 1
                else:
                    alignment_outcomes[key]['losses'] += 1

            if bullish_tfs >= 2 and bearish_tfs >= 2:
                key = f"{side} + TF conflict (mixed signals)"
                alignment_outcomes[key]['pnl'] += pnl
                if win:
                    alignment_outcomes[key]['wins'] += 1
                else:
                    alignment_outcomes[key]['losses'] += 1

        # Convert to PatternOutcome objects
        def to_pattern_outcomes(data: Dict, min_trades: int = 3) -> List[PatternOutcome]:
            outcomes = []
            for pattern, stats in data.items():
                total = stats['wins'] + stats['losses']
                if total >= min_trades:
                    outcomes.append(PatternOutcome(
                        pattern=pattern,
                        trades=total,
                        wins=stats['wins'],
                        losses=stats['losses'],
                        total_pnl=stats['pnl'],
                    ))
            return outcomes

        single_outcomes = to_pattern_outcomes(pattern_outcomes, self.MIN_TRADES_FOR_PATTERN)
        combo_results = to_pattern_outcomes(combo_outcomes, self.MIN_TRADES_FOR_PATTERN)
        alignment_results = to_pattern_outcomes(alignment_outcomes, 2)

        # Split into confirmation vs risk patterns
        confirmation = [p for p in single_outcomes if p.win_rate >= 0.55 and p.total_pnl > 0]
        risk = [p for p in single_outcomes if p.win_rate < 0.45 or p.total_pnl < -50]

        # Sort by P&L
        confirmation.sort(key=lambda x: x.total_pnl, reverse=True)
        risk.sort(key=lambda x: x.total_pnl)

        # Best and worst combinations
        best_combos = sorted(combo_results, key=lambda x: x.total_pnl, reverse=True)[:15]
        worst_combos = sorted(combo_results, key=lambda x: x.total_pnl)[:15]

        return {
            'confirmation': confirmation[:20],
            'risk': risk[:20],
            'best_combos': best_combos,
            'worst_combos': worst_combos,
            'tf_alignment': alignment_results,
        }

    async def _synthesize_insights(self, report: PerformanceReport) -> None:
        """
        Use Claude Haiku to synthesize analysis into actionable insights.

        Populates report.critical_issues, report.positive_edges, and report.recommendations.
        """
        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            # Build analysis summary for LLM
            analysis_summary = self._build_analysis_summary(report)

            prompt = f"""You are analyzing a trading bot's performance. Based on the following analysis data, provide actionable insights.

## ANALYSIS DATA
{analysis_summary}

## INSTRUCTIONS
Analyze this data and provide:

1. CRITICAL ISSUES (1-3): Problems that are significantly hurting performance. Be specific with numbers.
2. POSITIVE EDGES (1-3): What's working well that should be preserved or expanded.
3. RECOMMENDATIONS (2-4): Specific, actionable changes to improve performance.

IMPORTANT: For exit analysis, be cautious about recommending changes to early exit behavior. We only see P&L at exit time - we cannot know if holding longer would have hit TP (better) or SL (worse). Early exits with losses may have actually avoided larger losses. Frame exit observations as patterns to investigate, not definitive problems to fix.

For each item, provide:
- "title": Brief title (5-10 words)
- "detail": Specific explanation with numbers from the data
- "impact": Expected impact if addressed/maintained

## OUTPUT FORMAT
Return valid JSON:
{{
  "critical_issues": [{{"title": "...", "detail": "...", "impact": "..."}}],
  "positive_edges": [{{"title": "...", "detail": "...", "impact": "..."}}],
  "recommendations": [{{"title": "...", "detail": "...", "impact": "..."}}]
}}

Focus on the most impactful findings. Reference specific patterns, percentages, and P&L values."""

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response
            response_text = response.content[0].text

            # Try to extract and parse JSON
            try:
                # First try: direct parse
                insights = json.loads(response_text)
            except json.JSONDecodeError:
                # Second try: extract JSON from markdown code block
                json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response_text)
                if json_match:
                    insights = json.loads(json_match.group(1))
                else:
                    # Third try: find any JSON object
                    json_match = re.search(r'(\{[^{}]*"critical_issues"[\s\S]*\})', response_text)
                    if json_match:
                        # Clean up common issues
                        json_str = json_match.group(1)
                        # Remove trailing commas before closing brackets
                        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
                        insights = json.loads(json_str)
                    else:
                        raise ValueError("Could not find valid JSON in response")

            report.critical_issues = insights.get('critical_issues', [])
            report.positive_edges = insights.get('positive_edges', [])
            report.recommendations = insights.get('recommendations', [])

            logger.bind(config_id=self.config_id).info("LLM insights synthesized")

        except Exception as e:
            logger.bind(config_id=self.config_id).error(f"Failed to synthesize insights: {e}")
            # Provide fallback insights based on data
            self._generate_fallback_insights(report)

    def _build_analysis_summary(self, report: PerformanceReport) -> str:
        """Build a text summary of the analysis for LLM consumption."""
        lines = []

        # Basic stats
        bs = report.basic_stats
        lines.append(f"## BASIC STATS")
        lines.append(f"- Total Trades: {bs.total_trades}")
        lines.append(f"- Win Rate: {bs.win_rate*100:.1f}% (breakeven: {bs.breakeven_winrate*100:.1f}%)")
        lines.append(f"- R:R Ratio: {bs.risk_reward_ratio:.2f}")
        lines.append(f"- Total P&L: ${bs.total_pnl:.2f}")
        lines.append(f"- Avg Win: ${bs.avg_win:.2f}, Avg Loss: ${bs.avg_loss:.2f}")

        # Direction stats
        lines.append(f"\n## DIRECTION BREAKDOWN")
        for ds in report.direction_stats:
            lines.append(f"- {ds.side.upper()}: {ds.trades} trades, {ds.win_rate*100:.0f}% WR, ${ds.total_pnl:.2f} P&L")

        # Confidence calibration
        lines.append(f"\n## CONFIDENCE CALIBRATION")
        for cb in report.confidence_buckets:
            gap = cb.calibration_gap * 100
            if abs(gap) > 10:
                lines.append(f"- {cb.range_label}: actual {cb.actual_win_rate*100:.0f}% vs expected {cb.expected_win_rate*100:.0f}% (gap: {gap:+.0f}%), ${cb.total_pnl:.2f}")

        # Exit classifications
        lines.append(f"\n## EXIT ANALYSIS")
        lines.append("(NOTE: Early exits may have avoided worse losses - we cannot know counterfactual outcomes)")
        for ec in report.exit_classifications:
            lines.append(f"- {ec.exit_type}: {ec.trades} trades, {ec.win_rate*100:.0f}% WR, ${ec.total_pnl:.2f}")

        # Best patterns
        if report.confirmation_patterns:
            lines.append(f"\n## BEST CONFIRMATION PATTERNS")
            for p in report.confirmation_patterns[:5]:
                lines.append(f"- {p.pattern}: {p.trades} trades, {p.win_rate*100:.0f}% WR, ${p.total_pnl:.2f}")

        # Worst patterns
        if report.risk_patterns:
            lines.append(f"\n## RISK PATTERNS (avoid)")
            for p in report.risk_patterns[:5]:
                lines.append(f"- {p.pattern}: {p.trades} trades, {p.win_rate*100:.0f}% WR, ${p.total_pnl:.2f}")

        # Best combinations
        if report.best_combinations:
            lines.append(f"\n## BEST PATTERN COMBINATIONS")
            for p in report.best_combinations[:3]:
                lines.append(f"- {p.pattern}: {p.trades} trades, {p.win_rate*100:.0f}% WR, ${p.total_pnl:.2f}")

        # Worst combinations
        if report.worst_combinations:
            lines.append(f"\n## WORST PATTERN COMBINATIONS")
            for p in report.worst_combinations[:3]:
                lines.append(f"- {p.pattern}: {p.trades} trades, {p.win_rate*100:.0f}% WR, ${p.total_pnl:.2f}")

        # TF alignment
        if report.tf_alignment_stats:
            lines.append(f"\n## TIMEFRAME ALIGNMENT")
            for p in report.tf_alignment_stats:
                lines.append(f"- {p.pattern}: {p.trades} trades, {p.win_rate*100:.0f}% WR, ${p.total_pnl:.2f}")

        return "\n".join(lines)

    def _generate_fallback_insights(self, report: PerformanceReport) -> None:
        """Generate basic insights without LLM if synthesis fails."""
        bs = report.basic_stats

        # Check for overconfidence
        for cb in report.confidence_buckets:
            if cb.calibration_gap > 0.2 and cb.trades >= 3:
                report.critical_issues.append({
                    "title": f"Overconfidence at {cb.range_label}",
                    "detail": f"Expected {cb.expected_win_rate*100:.0f}% WR but achieved {cb.actual_win_rate*100:.0f}%",
                    "impact": f"${abs(cb.total_pnl):.0f} lost to overconfident trades"
                })

        # Note: We don't flag exit types as critical issues because we lack counterfactual data.
        # Early exits may have avoided larger losses - we only see P&L at exit time.

        # Add positive edge for best direction
        if report.direction_stats:
            best = report.direction_stats[0]
            if best.total_pnl > 0:
                report.positive_edges.append({
                    "title": f"{best.side.upper()} trades performing well",
                    "detail": f"{best.trades} trades at {best.win_rate*100:.0f}% WR",
                    "impact": f"${best.total_pnl:.0f} profit from {best.side} trades"
                })


# =============================================================================
# Public API
# =============================================================================

async def analyze_bot_performance(config_id: str, include_llm_insights: bool = True) -> PerformanceReport:
    """
    Analyze a bot's trading performance.

    Args:
        config_id: Bot configuration ID
        include_llm_insights: Whether to synthesize insights using LLM (default: True)

    Returns:
        PerformanceReport with all analysis results
    """
    analyzer = PerformanceAnalyzer(config_id)
    return await analyzer.analyze(include_llm_insights=include_llm_insights)
