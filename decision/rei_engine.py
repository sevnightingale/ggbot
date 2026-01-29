"""
Rei Decision Engine - Routes trading decisions through Rei Core instead of OpenRouter LLMs.

Rei provides inference-time learning: it evolves reasoning patterns from trade outcomes
without retraining. Each call is self-contained (no session context in API), but Rei's
conceptual learning persists across sessions.

Key constraints from Rei docs:
- Each API call must be self-contained (include ALL context)
- Never feed previous Rei outputs back (causes reasoning corruption)
- Float64 numerical precision preserved (no tokenization loss)
- response_format=json_object for structured output

Usage:
    engine = ReiDecisionEngine(config_id, user_id)
    result = await engine.make_decision(
        symbol="BTC/USDT",
        extraction_result={...},
        open_positions=[...],
        account_balance=10000.0
    )
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from core.common.logger import logger
from core.services.rei_service import ReiService, ReiServiceError
from extraction.v2.preprocessors.compact_config import (
    get_timeframes_for_indicator,
    REI_INDICATOR_TIMEFRAMES,
)
from extraction.v2.preprocessors import get_preprocessor


class ReiDecisionEngine:
    """
    Decision engine that routes through Rei Core API instead of OpenRouter LLMs.

    Designed as a drop-in replacement for DecisionEngineV2.make_decision() output format.
    The extraction and trading stages remain unchanged.
    """

    # Rei API timeout — large payloads (~15-20KB market data) need time
    REI_TIMEOUT = 180.0
    REI_TEMPERATURE = 0.45  # Low for consistent trading decisions
    REI_MAX_TOKENS = 2000

    def __init__(self, config_id: str, user_id: str):
        self.config_id = config_id
        self.user_id = user_id
        self._log = logger.bind(config_id=config_id, component="rei_decision_engine")

    async def make_decision(
        self,
        symbol: str,
        extraction_result: Dict[str, Any],
        open_positions: Optional[List[Dict[str, Any]]] = None,
        account_balance: Optional[float] = None,
        market_intelligence: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send market data to Rei and get a trading decision.

        Args:
            symbol: Trading symbol (e.g., "BTC/USDT")
            extraction_result: Full extraction result from V2 pipeline
            open_positions: List of open position dicts from paper_trades
            account_balance: Current account balance in USD
            market_intelligence: Market intel dict (also in extraction_result)

        Returns:
            Decision intent dict matching DecisionEngineV2 output format:
            {
                'action': 'enter_long'|'enter_short'|'exit'|'wait',
                'confidence': float,
                'reasoning': str,
                'symbol': str,
                'config_id': str,
                'decision_id': str,  # generated
                'stop_loss_price': float|None,
                'take_profit_price': float|None,
                'timestamp': str,
                'decision_type': str,
                'user_id': str,
            }
        """
        rei_secret = os.getenv("REI_01_UNIT_SECRET")
        if not rei_secret:
            self._log.error("REI_01_UNIT_SECRET not set")
            return self._create_error_result("Rei not configured: REI_01_UNIT_SECRET missing")

        try:
            # Build self-contained payload for Rei
            payload = self._build_rei_payload(
                symbol=symbol,
                extraction_result=extraction_result,
                open_positions=open_positions,
                account_balance=account_balance,
                market_intelligence=market_intelligence,
            )

            self._log.info(f"Consulting Rei for {symbol} decision (payload ~{len(json.dumps(payload))} bytes)")

            # Call Rei API
            rei = ReiService(agent_secret_key=rei_secret, timeout=self.REI_TIMEOUT)
            try:
                response = await rei.chat_completion(
                    messages=[{
                        "role": "user",
                        "content": json.dumps(payload)
                    }],
                    response_format={"type": "json_object"},
                    temperature=self.REI_TEMPERATURE,
                    max_tokens=self.REI_MAX_TOKENS,
                )
            finally:
                await rei.close()

            # Parse Rei's JSON response
            decision = self._parse_rei_response(response.content)

            # Build standard decision result
            result = self._build_decision_result(symbol, decision)

            self._log.info(
                f"Rei decision: {result['action']} @ {result['confidence']:.0%} confidence"
                f" | TP={result.get('take_profit_price')} SL={result.get('stop_loss_price')}"
            )

            # Store decision in database
            decision_id = await self._store_decision(symbol, result)
            result['decision_id'] = decision_id

            return result

        except ReiServiceError as e:
            self._log.error(f"Rei API error: {e}")
            return self._create_error_result(f"Rei API error: {e}")
        except Exception as e:
            self._log.error(f"Rei decision failed: {e}")
            return self._create_error_result(f"Rei decision failed: {e}")

    def _build_rei_payload(
        self,
        symbol: str,
        extraction_result: Dict[str, Any],
        open_positions: Optional[List[Dict[str, Any]]],
        account_balance: Optional[float],
        market_intelligence: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build self-contained JSON payload for Rei.

        Sends raw numerical data — no prose, no LLM articulation.
        Rei preserves Float64 precision (unlike LLMs which tokenize numbers).

        Uses compact format for indicators to stay under ~30KB payload limit.
        Only includes timeframes configured in REI_INDICATOR_TIMEFRAMES per indicator.
        """
        # Convert indicators to compact format (filters by configured timeframes)
        compact_indicators = self._convert_to_compact_indicators(extraction_result)

        # Market intelligence — strip debug metadata (_meta, tool_calls, citations)
        intel = market_intelligence or extraction_result.get('market_intelligence', {})
        intel = self._strip_meta_fields(intel)
        intel = self._sanitize_numeric_data(intel)

        # Format open positions as concise data (not full DB rows)
        positions_summary = self._summarize_positions(open_positions)

        return {
            "task": "trading_decision",
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "account_balance_usd": account_balance,
            "current_positions": positions_summary,
            "market_data": {
                "indicators": compact_indicators,
                "market_intelligence": intel,
            },
            "instructions": (
                "Analyze this market data and return a JSON trading decision. "
                "Each indicator has: value (primary), value_secondary, value_tertiary, "
                "velocity (rate of change), zone (state), trend, patterns (list of codes). "
                "Return: action (long/short/wait/close), confidence (0-1), reasoning, "
                "key_signals, warnings, take_profit (price), stop_loss (price)."
            ),
        }

    def _convert_to_compact_indicators(
        self,
        extraction_result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Convert full indicator outputs to compact format for Rei.

        Filters indicators by configured timeframes (REI_INDICATOR_TIMEFRAMES)
        and converts each to compact format using preprocessor.to_compact().

        Args:
            extraction_result: Full extraction result with timeframes/indicators

        Returns:
            List of compact indicator dicts
        """
        compact_list = []

        # extraction_result has nested timeframe structure
        timeframes_data = extraction_result.get('timeframes', {})

        if not timeframes_data and 'indicators' in extraction_result:
            # Flat structure - single timeframe
            timeframes_data = {'default': {'indicators': extraction_result['indicators']}}

        for tf_key, tf_data in timeframes_data.items():
            if not isinstance(tf_data, dict) or 'indicators' not in tf_data:
                continue

            indicators = tf_data.get('indicators', {})

            for indicator_name, indicator_data in indicators.items():
                if not isinstance(indicator_data, dict):
                    continue

                # Normalize indicator name
                indicator_lower = indicator_name.lower()

                # Check if this timeframe is configured for this indicator
                configured_tfs = get_timeframes_for_indicator(indicator_lower)
                if tf_key not in configured_tfs and tf_key != 'default':
                    # Skip - this timeframe not configured for this indicator
                    continue

                # Try to get preprocessor for compact conversion
                preprocessor = get_preprocessor(indicator_lower)

                if preprocessor and hasattr(preprocessor, 'to_compact'):
                    try:
                        compact = preprocessor.to_compact(indicator_data, tf_key)
                        compact_list.append(compact)
                    except Exception as e:
                        self._log.warning(
                            f"Compact conversion failed for {indicator_name}/{tf_key}: {e}"
                        )
                        # Fallback: include sanitized original (but smaller)
                        compact_list.append(self._fallback_compact(
                            indicator_name, tf_key, indicator_data
                        ))
                else:
                    # No compact converter - use fallback
                    compact_list.append(self._fallback_compact(
                        indicator_name, tf_key, indicator_data
                    ))

        self._log.debug(f"Converted {len(compact_list)} indicators to compact format")
        return compact_list

    def _fallback_compact(
        self,
        indicator_name: str,
        timeframe: str,
        indicator_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Fallback compact conversion for indicators without to_compact() method.

        Extracts essential values into universal compact schema.
        """
        current = indicator_data.get('current', {})

        # Try to find primary value
        value = current.get('value')
        if value is None:
            # Try common field names
            for key in ['macd', 'adx', 'k_percent', 'price', 'atr', 'percent_b']:
                if key in current:
                    value = current.get(key)
                    break

        # Try to find secondary/tertiary values
        value_secondary = current.get('signal') or current.get('d_percent') or current.get('upper_band')
        value_tertiary = current.get('histogram') or current.get('lower_band')

        return {
            "indicator": indicator_name.lower(),
            "timeframe": timeframe,
            "timestamp": current.get('timestamp'),
            "value": self._safe_float(value),
            "value_secondary": self._safe_float(value_secondary),
            "value_tertiary": self._safe_float(value_tertiary),
            "velocity": 0.0,
            "rank": 0.0,
            "zone": indicator_data.get('zone', {}).get('current_zone', 'unknown')
                    if isinstance(indicator_data.get('zone'), dict)
                    else 'unknown',
            "zone_periods": 0,
            "trend": indicator_data.get('trend', {}).get('direction', 'unknown')
                     if isinstance(indicator_data.get('trend'), dict)
                     else 'unknown',
            "crossover_type": None,
            "crossover_periods_ago": None,
            "patterns": [],
            "analysis": indicator_data.get('summary', ''),
        }

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float, handling None and numpy types."""
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _strip_meta_fields(self, data: Any) -> Any:
        """
        Recursively strip '_meta' debug fields from market intelligence data.
        These contain tool_calls, citations, etc. that bloat the payload without
        adding decision-making value.
        """
        if isinstance(data, dict):
            return {
                k: self._strip_meta_fields(v)
                for k, v in data.items()
                if k not in ['_meta', 'metadata', 'raw_data']
            }
        elif isinstance(data, list):
            return [self._strip_meta_fields(item) for item in data]
        else:
            return data

    def _sanitize_numeric_data(self, data: Any) -> Any:
        """
        Recursively sanitize numeric data to remove NaN/Infinity values.
        These are not valid JSON and will cause 400 Bad Request errors.
        """
        import math

        if isinstance(data, dict):
            return {k: self._sanitize_numeric_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_numeric_data(item) for item in data]
        elif isinstance(data, float):
            if math.isnan(data) or math.isinf(data):
                return None  # Replace invalid floats with None
            return data
        else:
            return data

    def _summarize_positions(self, positions: Optional[List[Dict[str, Any]]]) -> str:
        """Summarize open positions for Rei context."""
        if not positions:
            return "No open positions"

        parts = []
        for pos in positions:
            side = pos.get('side', 'unknown')
            entry = pos.get('entry_price', 0)
            current = pos.get('current_price', 0)
            pnl = pos.get('unrealized_pnl', 0)
            size = pos.get('size_usd', 0)
            leverage = pos.get('leverage', 1)
            parts.append(
                f"{side.upper()} entry=${entry}, current=${current}, "
                f"pnl=${pnl:+.2f}, size=${size}, leverage={leverage}x"
            )
        return "; ".join(parts)

    def _parse_rei_response(self, content: str) -> Dict[str, Any]:
        """Parse Rei's JSON response, with fallback for malformed output."""
        try:
            decision = json.loads(content)
        except json.JSONDecodeError:
            self._log.warning(f"Rei returned non-JSON response: {content[:200]}")
            decision = {
                "action": "wait",
                "confidence": 0.0,
                "reasoning": f"Rei returned non-JSON: {content[:200]}",
                "key_signals": [],
                "warnings": ["Response was not valid JSON"],
            }
        return decision

    def _build_decision_result(self, symbol: str, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Rei's response into standard decision_result format."""
        action = decision.get("action", "wait")

        # Normalize action names to platform standard: long, short, wait, close
        action_map = {
            "enter_long": "long",
            "long": "long",
            "buy": "long",
            "enter_short": "short",
            "short": "short",
            "sell": "short",
            "exit": "close",
            "close": "close",
            "wait": "wait",
            "hold": "wait",
            "no_action": "wait",
        }
        normalized_action = action_map.get(action.lower(), "wait")

        confidence = decision.get("confidence", 0.0)
        # Clamp confidence to [0, 1]
        confidence = max(0.0, min(1.0, float(confidence)))

        return {
            'decision_id': None,  # Will be set after DB insert
            'user_id': self.user_id,
            'config_id': self.config_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'decision_type': 'rei_decision',
            'symbol': symbol,
            'action': normalized_action,
            'confidence': confidence,
            'reasoning': decision.get("reasoning", "No reasoning provided"),
            'stop_loss_price': decision.get("stop_loss"),
            'take_profit_price': decision.get("take_profit"),
            'decision_data': {
                'key_signals': decision.get("key_signals", []),
                'warnings': decision.get("warnings", []),
                'rei_raw_action': action,  # preserve original action name
            },
        }

    async def _store_decision(self, symbol: str, result: Dict[str, Any]) -> str:
        """Store Rei decision in decisions table and log activity."""
        import uuid
        from core.common.db import get_db_connection

        decision_id = str(uuid.uuid4())

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO decisions (
                            decision_id, user_id, config_id, symbol, action,
                            confidence, reasoning, decision_data, created_by
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        decision_id,
                        self.user_id,
                        self.config_id,
                        symbol,
                        result['action'],
                        result['confidence'],
                        result['reasoning'],
                        json.dumps(result.get('decision_data', {})),
                        'rei_decision_engine',
                    ))
                conn.commit()
        except Exception as e:
            self._log.error(f"Failed to store Rei decision: {e}")
            # Non-fatal — decision can still be acted on

        # Log activity as llm_thought so frontend displays it correctly
        try:
            from core.common.activity_logger import log_llm_activity_safe

            # Format reasoning with key_signals and warnings for frontend display
            # LLMThoughtContent parses KEY_SIGNAL/SUPPORTING/RISK/SUMMARY sections
            key_signals = result.get('decision_data', {}).get('key_signals', [])
            warnings = result.get('decision_data', {}).get('warnings', [])
            reasoning = result.get('reasoning', '')

            thought_parts = []
            if key_signals:
                thought_parts.append(f"KEY_SIGNAL: {'; '.join(str(s) for s in key_signals)}")
            if reasoning:
                thought_parts.append(f"SUMMARY: {reasoning}")
            if warnings:
                thought_parts.append(f"RISK: {'; '.join(str(w) for w in warnings)}")

            thought_text = '\n'.join(thought_parts) if thought_parts else reasoning

            log_llm_activity_safe(
                config_id=self.config_id,
                user_id=self.user_id,
                activity_source='rei_decision_engine',
                summary=f"Analyzed {symbol}: {result['action'].upper()} (confidence: {result['confidence']:.0%})",
                details={
                    'thought': thought_text,
                    'confidence': result['confidence'],
                    'action': result['action'],
                    'symbol': symbol,
                    'stop_loss_price': result.get('stop_loss_price'),
                    'take_profit_price': result.get('take_profit_price'),
                },
                provider='rei',
                model='rei-core',
                input_tokens=0,
                output_tokens=0,
                provider_cost_usd=0.0,
                platform_cost_usd=0.0,
                related_symbol=symbol,
                importance=8,
                stripe_reported=True,  # Rei costs are external, never bill through Stripe
            )
        except Exception as e:
            self._log.error(f"Failed to log Rei activity: {e}")

        return decision_id

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create error result matching expected format."""
        return {
            'action': 'wait',
            'confidence': 0.0,
            'error': error_message,
            'config_id': self.config_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'reasoning': f'Error: {error_message}',
        }


async def report_trade_outcome_to_rei(
    config_id: str,
    symbol: str,
    side: str,
    entry_price: float,
    exit_price: float,
    pnl_usd: float,
    pnl_percent: float,
    duration_hours: float,
    close_reason: str,
) -> bool:
    """
    Report a closed trade outcome to Rei for learning.

    Called from trading service after a trade closes on a rei_enabled bot.
    Sends RAW FACTS only — never includes Rei's previous output (causes
    reasoning corruption per Rei docs).

    Returns:
        True if reported successfully, False otherwise
    """
    log = logger.bind(config_id=config_id, component="rei_feedback")

    rei_secret = os.getenv("REI_01_UNIT_SECRET")
    if not rei_secret:
        log.warning("REI_01_UNIT_SECRET not set, skipping outcome report")
        return False

    outcome = "WIN" if pnl_usd > 0 else "LOSS" if pnl_usd < 0 else "BREAKEVEN"

    # Raw facts only — no previous Rei output
    feedback = f"""TRADE OUTCOME REPORT

Symbol: {symbol}
Side: {side.upper()}
Result: {outcome}

Entry Price: ${entry_price:,.2f}
Exit Price: ${exit_price:,.2f}
P&L: ${pnl_usd:+,.2f} ({pnl_percent:+.2f}%)

Duration: {duration_hours:.1f} hours
Close Reason: {close_reason}

Learn from this outcome. Strengthen patterns that led to winning trades. Weaken patterns that led to losing trades."""

    try:
        rei = ReiService(agent_secret_key=rei_secret, timeout=60.0)
        try:
            await rei.chat_completion(
                messages=[{"role": "user", "content": feedback}],
                temperature=0.3,  # Low for learning
                max_tokens=500,
            )
        finally:
            await rei.close()

        log.info(f"Reported {outcome} to Rei: {symbol} {side} ${pnl_usd:+,.2f}")
        return True

    except ReiServiceError as e:
        log.error(f"Failed to report outcome to Rei: {e}")
        return False
    except Exception as e:
        log.error(f"Unexpected error reporting to Rei: {e}")
        return False
