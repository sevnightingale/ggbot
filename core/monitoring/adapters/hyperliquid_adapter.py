"""
Hyperliquid Account Adapter

Queries Hyperliquid Info API (user_state + user_fills) to create account snapshots.
Uses per-user wallet credentials from Supabase Vault.

Key differences from Symphony/Aster:
- Hyperliquid provides FULL account data (balance, margin, positions, P&L)
- user_state.marginSummary.accountValue = total equity
- user_fills provides trade history with closedPnl for realized P&L
- Positions are account-wide (shared across all bots for same wallet)
"""

import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Set, Dict, List

from hyperliquid.info import Info
from hyperliquid.utils import constants

from core.domain.account_snapshot import AccountAdapter, AccountSnapshot
from core.common.db import get_db_connection
from core.common.logger import logger


class HyperliquidAccountAdapter(AccountAdapter):
    """Adapter for fetching Hyperliquid account state from Info API."""

    def __init__(self):
        self._log = logger.bind(adapter="hyperliquid_account")
        self._info = Info(constants.MAINNET_API_URL, skip_ws=True)
        self._position_cache: Dict[str, Set[str]] = {}  # config_id -> set of hl_symbols with open positions
        self._logged_closes: Set[str] = set()  # Track already-logged fill hashes
        self._logged_transfers: Set[str] = set()  # Track already-logged deposit/withdrawal tx hashes
        # Cache wallet address per user_id to avoid repeated Vault lookups
        self._wallet_cache: Dict[str, str] = {}  # user_id -> wallet_address

    async def _get_wallet_address(
        self,
        user_id: str,
        trading_mode: str = 'hyperliquid',
        config_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Get wallet address from cache or Vault. CredentialResolver picks the
        right wallet based on trading_mode: personal HL wallet for 'hyperliquid'
        mode, Privy agent wallet for 'virtuals' mode.

        Cache key includes config_id so a user's personal HL wallet never
        collides with their virtuals agent wallets.
        """
        cache_key = f"{user_id}:{config_id or '-'}"
        if cache_key in self._wallet_cache:
            return self._wallet_cache[cache_key]

        try:
            from core.auth.vault_utils import resolve_hl_credentials
            credentials = await resolve_hl_credentials(trading_mode, user_id, config_id)
            if not credentials:
                return None
            wallet = credentials['wallet_address']
            self._wallet_cache[cache_key] = wallet
            return wallet
        except Exception as e:
            self._log.error(
                f"Failed to get HL wallet for user={user_id} mode={trading_mode}: {e}"
            )
            return None

    async def get_current_snapshot(self, config_id: str) -> Optional[AccountSnapshot]:
        """
        Get current Hyperliquid account state from Info API.

        Queries user_state for account balance, margin, and positions.
        Cross-references positions with live_trades to attribute to this config.
        """
        try:
            # Get user_id, trading_mode, and selected_pair from config
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT user_id, config_data->>'selected_pair', trading_mode "
                        "FROM configurations WHERE config_id = %s",
                        (config_id,)
                    )
                    result = cur.fetchone()
                    if not result:
                        self._log.warning(f"Config {config_id} not found")
                        return None
                    user_id = str(result[0])
                    selected_pair = result[1]
                    trading_mode = result[2] or 'hyperliquid'

            # Get wallet address — virtuals bots read from arena_agents_v2,
            # hyperliquid bots read from user_profiles (same adapter, different creds).
            wallet = await self._get_wallet_address(user_id, trading_mode, config_id)
            if not wallet:
                self._log.warning(f"No Hyperliquid wallet for user {user_id}")
                return None

            # Query Hyperliquid user_state (account + positions)
            user_state = self._info.user_state(wallet)
            margin = user_state.get("marginSummary", {})

            account_value = Decimal(str(margin.get("accountValue", 0)))
            total_margin_used = Decimal(str(margin.get("totalMarginUsed", 0)))
            total_ntl_pos = Decimal(str(margin.get("totalNtlPos", 0)))
            total_raw_usd = Decimal(str(margin.get("totalRawUsd", 0)))
            withdrawable = Decimal(str(user_state.get("withdrawable", 0)))

            # Parse positions from user_state
            all_positions = user_state.get("assetPositions", [])
            open_hl_positions = []
            total_unrealized_pnl = Decimal('0')
            total_position_value = Decimal('0')
            bot_position_value = Decimal('0')
            bot_unrealized_pnl = Decimal('0')
            bot_margin_used = Decimal('0')
            bot_open_count = 0

            # Get this bot's tracked symbols from live_trades (open AND closed)
            # Must include closed trades so fills still match for realized P&L
            bot_symbols = set()
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT DISTINCT symbol FROM live_trades
                            WHERE config_id = %s AND provider = 'hyperliquid'
                        """, (config_id,))
                        for row in cur.fetchall():
                            bot_symbols.add(row[0])
            except Exception as e:
                self._log.warning(f"Failed to query bot symbols: {e}")

            # Convert bot symbols to HL format for matching
            from core.symbols.standardizer import UniversalSymbolStandardizer
            standardizer = UniversalSymbolStandardizer()
            bot_hl_symbols = set()
            for sym in bot_symbols:
                hl_sym = standardizer.to_hyperliquid(sym, "platform") if "-" in sym else sym
                if hl_sym:
                    bot_hl_symbols.add(hl_sym)

            for pos_wrapper in all_positions:
                pos = pos_wrapper.get("position", {})
                szi = Decimal(str(pos.get("szi", 0)))
                if szi == 0:
                    continue

                coin = pos.get("coin", "")
                pos_value = abs(Decimal(str(pos.get("positionValue", 0))))
                pos_pnl = Decimal(str(pos.get("unrealizedPnl", 0)))
                pos_margin = Decimal(str(pos.get("marginUsed", 0)))

                total_unrealized_pnl += pos_pnl
                total_position_value += pos_value
                open_hl_positions.append(coin)

                # Track bot-specific position data
                if coin in bot_hl_symbols:
                    bot_position_value += pos_value
                    bot_unrealized_pnl += pos_pnl
                    bot_margin_used += pos_margin
                    bot_open_count += 1

            # Get trade stats from live_trades (realized_pnl stored per-trade)
            total_trades = 0
            win_trades = 0
            loss_trades = 0
            realized_pnl = Decimal('0')

            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT COUNT(*),
                                   COALESCE(SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END), 0),
                                   COALESCE(SUM(CASE WHEN realized_pnl <= 0 AND closed_at IS NOT NULL THEN 1 ELSE 0 END), 0),
                                   COALESCE(SUM(realized_pnl), 0)
                            FROM live_trades
                            WHERE config_id = %s AND provider = 'hyperliquid'
                              AND closed_at IS NOT NULL AND realized_pnl IS NOT NULL
                        """, (config_id,))
                        row = cur.fetchone()
                        if row:
                            closed_count = row[0]
                            win_trades = int(row[1])
                            loss_trades = int(row[2])
                            realized_pnl = Decimal(str(row[3]))

                        # Total trades includes open ones
                        cur.execute("""
                            SELECT COUNT(*) FROM live_trades
                            WHERE config_id = %s AND provider = 'hyperliquid'
                        """, (config_id,))
                        total_trades = cur.fetchone()[0]

            except Exception as e:
                self._log.warning(f"Failed to compute trade stats for {config_id}: {e}")

            # Calculate derived metrics
            win_rate = Decimal(str(win_trades)) / Decimal(str(max(win_trades + loss_trades, 1)))
            total_pnl = realized_pnl + bot_unrealized_pnl

            avg_win = None
            avg_loss = None
            largest_win = None
            largest_loss = None
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT realized_pnl FROM live_trades
                            WHERE config_id = %s AND provider = 'hyperliquid'
                              AND closed_at IS NOT NULL AND realized_pnl IS NOT NULL
                        """, (config_id,))
                        trade_pnls = [Decimal(str(r[0])) for r in cur.fetchall()]
                        wins = [p for p in trade_pnls if p > 0]
                        losses = [p for p in trade_pnls if p < 0]
                        if wins:
                            avg_win = sum(wins) / len(wins)
                            largest_win = max(wins)
                        if losses:
                            avg_loss = sum(losses) / len(losses)
                            largest_loss = min(losses)
            except Exception:
                pass

            # Build snapshot
            # Single live bot model: the Hyperliquid account balance IS this bot's balance.
            # HL accountValue already INCLUDES unrealized PnL, so we subtract it out
            # to get the cash-only balance. This way the universal formula
            # total_equity = current_balance + unrealized_pnl works correctly
            # (same as paper where current_balance is cash-only).
            cash_balance = account_value - bot_unrealized_pnl
            snapshot = AccountSnapshot(
                snapshot_id=None,
                config_id=config_id,
                user_id=user_id,
                trading_mode='hyperliquid',
                timestamp=datetime.now(timezone.utc),
                current_balance=cash_balance,
                available_balance=withdrawable,
                margin_used=bot_margin_used if bot_margin_used > 0 else None,
                total_pnl=total_pnl,
                realized_pnl=realized_pnl,
                unrealized_pnl=bot_unrealized_pnl,
                total_trades=total_trades,
                win_trades=win_trades,
                loss_trades=loss_trades,
                win_rate=win_rate,
                open_positions=bot_open_count,
                position_value=bot_position_value,
                total_exposure=total_position_value,  # Account-wide exposure
                avg_win=avg_win,
                avg_loss=avg_loss,
                largest_win=largest_win,
                largest_loss=largest_loss,
                raw_data={
                    'source': 'hyperliquid_info_api',
                    'account_value': float(account_value),
                    'total_raw_usd': float(total_raw_usd),
                    'withdrawable': float(withdrawable),
                    'total_margin_used': float(total_margin_used),
                    'total_ntl_pos': float(total_ntl_pos),
                    'all_positions_count': len(open_hl_positions),
                    'bot_positions_count': bot_open_count,
                    'bot_symbols': list(bot_hl_symbols),
                }
            )

            # Detect and log position closes
            await self._detect_and_log_closes(config_id, user_id, wallet, bot_hl_symbols)

            # Detect and log deposits/withdrawals
            await self._detect_and_log_transfers(config_id, user_id, wallet)

            return snapshot

        except Exception as e:
            self._log.error(f"Failed to get Hyperliquid snapshot for {config_id}: {e}")
            return None

    async def _detect_and_log_closes(
        self,
        config_id: str,
        user_id: str,
        wallet: str,
        bot_hl_symbols: Set[str]
    ):
        """
        Detect closed Hyperliquid positions via user_fills.

        Checks recent fills for "Close Long" / "Close Short" events on
        symbols tracked by this bot. Aggregates partial fills by timestamp
        before logging a single trade_exit activity per close.

        Skips logging if hyperliquid_service already logged a trade_exit
        for the same trade_id within the last 60 seconds (cross-source dedup).
        """
        from collections import defaultdict
        from core.common.activity_logger import log_activity_safe
        from core.symbols.standardizer import UniversalSymbolStandardizer

        try:
            # Check fills from last hour (monitor runs every 5s, so this catches everything)
            one_hour_ago = int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp() * 1000)
            fills = self._info.user_fills_by_time(wallet, one_hour_ago)

            standardizer = UniversalSymbolStandardizer()

            # Aggregate partial fills by (coin, fill_time) to get full trade P&L
            # A single market_close() can produce multiple fills at the same timestamp
            AggFill = Dict  # type alias for clarity
            aggregated: Dict[tuple, AggFill] = defaultdict(lambda: {
                'total_pnl': 0.0, 'total_size': 0.0, 'weighted_price': 0.0,
                'hashes': [], 'oids': set(), 'side': '', 'coin': ''
            })

            for fill in fills:
                fill_hash = fill.get("hash", "")
                if fill_hash in self._logged_closes:
                    continue

                coin = fill.get("coin", "")
                fill_dir = fill.get("dir", "")
                closed_pnl = float(fill.get("closedPnl", 0))

                if coin not in bot_hl_symbols:
                    continue
                if "Close" not in fill_dir:
                    continue
                if closed_pnl == 0:
                    continue

                fill_price = float(fill.get("px", 0))
                fill_size = float(fill.get("sz", 0))
                fill_time = fill.get("time", 0)
                side = "long" if "Long" in fill_dir else "short"

                key = (coin, fill_time)
                agg = aggregated[key]
                agg['total_pnl'] += closed_pnl
                agg['total_size'] += fill_size
                agg['weighted_price'] += fill_price * fill_size
                agg['hashes'].append(fill_hash)
                agg['oids'].add(str(fill.get('oid', '')))
                agg['side'] = side
                agg['coin'] = coin

            # Process each aggregated close
            for (coin, fill_time), agg in aggregated.items():
                total_pnl = agg['total_pnl']
                total_size = agg['total_size']
                side = agg['side']
                avg_exit_price = agg['weighted_price'] / total_size if total_size > 0 else 0.0
                size_usd = total_size * avg_exit_price if total_size > 0 else 0.0

                platform_symbol = standardizer.from_hyperliquid(coin) or f"{coin}-USDT"

                # Look up batch_id + entry data + SL/TP order IDs from live_trades
                batch_id = None
                trade_created_at = None
                sl_order_id = None
                tp_order_id = None
                try:
                    with get_db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                SELECT batch_id, created_at, stop_loss_order_id, take_profit_order_id
                                FROM live_trades
                                WHERE config_id = %s AND provider = 'hyperliquid'
                                  AND symbol = %s
                                ORDER BY COALESCE(closed_at, created_at) DESC
                                LIMIT 1
                            """, (config_id, platform_symbol))
                            result = cur.fetchone()
                            if result:
                                batch_id = result[0]
                                trade_created_at = result[1]
                                sl_order_id = str(result[2]) if result[2] else None
                                tp_order_id = str(result[3]) if result[3] else None
                except Exception:
                    pass

                # Cross-source dedup: skip if service already logged exit for this trade
                if batch_id:
                    try:
                        with get_db_connection() as conn:
                            with conn.cursor() as cur:
                                cur.execute("""
                                    SELECT 1 FROM activities
                                    WHERE trade_id = %s
                                      AND activity_type = 'trade_exit'
                                      AND activity_source = 'hyperliquid_service'
                                      AND created_at > NOW() - INTERVAL '60 seconds'
                                    LIMIT 1
                                """, (batch_id,))
                                if cur.fetchone():
                                    # Service already logged this close — mark hashes and skip
                                    for h in agg['hashes']:
                                        self._logged_closes.add(h)
                                    self._log.debug(
                                        f"Skipping duplicate close for {platform_symbol} "
                                        f"(already logged by service)"
                                    )
                                    continue
                    except Exception:
                        pass

                # Compute entry price from aggregated fill data
                entry_price = 0.0
                pnl_pct = (total_pnl / size_usd * 100) if size_usd > 0 else 0.0
                if total_size > 0 and avg_exit_price > 0:
                    if side == "long":
                        entry_price = avg_exit_price - (total_pnl / total_size)
                    else:
                        entry_price = avg_exit_price + (total_pnl / total_size)

                # Compute duration
                duration_seconds = 0.0
                if trade_created_at:
                    try:
                        if isinstance(trade_created_at, str):
                            trade_created_at = datetime.fromisoformat(trade_created_at.replace('Z', '+00:00'))
                        if trade_created_at.tzinfo is None:
                            trade_created_at = trade_created_at.replace(tzinfo=timezone.utc)
                        duration_seconds = (datetime.now(timezone.utc) - trade_created_at).total_seconds()
                    except Exception:
                        pass

                pnl_display = f"{'+' if total_pnl > 0 else ''}{total_pnl:.2f}"

                # Write P&L to live_trades (source of truth for snapshots)
                if batch_id:
                    try:
                        with get_db_connection() as conn:
                            with conn.cursor() as cur:
                                cur.execute("""
                                    UPDATE live_trades
                                    SET closed_at = COALESCE(closed_at, NOW()),
                                        exit_price = %s, realized_pnl = %s
                                    WHERE batch_id = %s AND provider = 'hyperliquid'
                                      AND realized_pnl IS NULL
                                """, (round(avg_exit_price, 2), total_pnl, batch_id))
                                conn.commit()
                    except Exception as e:
                        self._log.warning(f"Failed to write P&L to live_trades: {e}")

                # Infer close_reason from SL/TP order IDs vs fill oids
                inferred_close_reason = 'auto'
                fill_oids = agg['oids']
                if sl_order_id and sl_order_id in fill_oids:
                    inferred_close_reason = 'stop_loss'
                elif tp_order_id and tp_order_id in fill_oids:
                    inferred_close_reason = 'take_profit'

                log_activity_safe(
                    config_id=config_id,
                    user_id=user_id,
                    activity_type='trade_exit',
                    activity_source='hyperliquid_monitor',
                    summary=f"Closed {platform_symbol}: ${pnl_display} ({pnl_pct:+.1f}%)",
                    details={
                        'symbol': platform_symbol,
                        'side': side,
                        'entry_price': entry_price,
                        'exit_price': avg_exit_price,
                        'pnl': total_pnl,
                        'pnl_pct': pnl_pct,
                        'size_usd': size_usd,
                        'close_reason': inferred_close_reason,
                        'duration_seconds': duration_seconds,
                        'fill_count': len(agg['hashes']),
                        'fill_time_ms': fill_time,
                        'source': 'position_monitor'
                    },
                    trade_id=batch_id,
                    trade_type='hyperliquid',
                    related_symbol=platform_symbol,
                    importance=9
                )

                # Mirror close to arena (fire-and-forget)
                try:
                    from trading.virtuals.arena_sync import mirror_close_to_arena
                    asyncio.create_task(mirror_close_to_arena(
                        config_id=config_id,
                        symbol=platform_symbol,
                        close_reason=inferred_close_reason,
                        user_id=user_id,
                    ))
                except Exception:
                    pass

                # Mirror close to Dojo match accounts (fire-and-forget)
                try:
                    from core.arena.dojo_mirror import mirror_close_to_dojo
                    asyncio.create_task(mirror_close_to_dojo(
                        config_id=config_id,
                        symbol=platform_symbol,
                        close_reason=inferred_close_reason,
                    ))
                except Exception:
                    pass

                for h in agg['hashes']:
                    self._logged_closes.add(h)
                self._log.info(
                    f"Logged close for {platform_symbol}: {pnl_display} "
                    f"({len(agg['hashes'])} fills aggregated)"
                )

        except Exception as e:
            self._log.warning(f"Failed to detect Hyperliquid closes for {config_id}: {e}")

    async def _detect_and_log_transfers(
        self,
        config_id: str,
        user_id: str,
        wallet: str
    ):
        """
        Detect deposits/withdrawals via user_non_funding_ledger_updates.

        Checks ledger updates from last hour for deposit/withdraw events.
        Deduplicates via self._logged_transfers keyed by tx hash.
        Logs each new transfer as a deposit or withdrawal activity.
        """
        from core.common.activity_logger import log_activity_safe

        try:
            one_hour_ago_ms = int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp() * 1000)
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

            ledger_updates = self._info.user_non_funding_ledger_updates(wallet, one_hour_ago_ms, now_ms)

            for entry in ledger_updates:
                delta = entry.get("delta", {})
                ledger_type = delta.get("type", "")

                if ledger_type not in ("deposit", "withdraw"):
                    continue

                tx_hash = entry.get("hash", "")
                if not tx_hash or tx_hash in self._logged_transfers:
                    continue

                amount_str = delta.get("usdc", "0")
                amount = abs(float(amount_str))

                if amount == 0:
                    continue

                if ledger_type == "deposit":
                    activity_type = "deposit"
                    summary = f"Deposited ${amount:.2f} USDC"
                else:
                    activity_type = "withdrawal"
                    summary = f"Withdrew ${amount:.2f} USDC"

                log_activity_safe(
                    config_id=config_id,
                    user_id=user_id,
                    activity_type=activity_type,
                    activity_source='hyperliquid',
                    summary=summary,
                    details={
                        'amount_usdc': amount,
                        'tx_hash': tx_hash,
                        'ledger_type': ledger_type,
                    },
                    importance=8
                )

                self._logged_transfers.add(tx_hash)
                self._log.info(
                    f"Logged {activity_type} for {wallet[:8]}...: ${amount:.2f} USDC"
                )

        except Exception as e:
            self._log.warning(f"Failed to detect transfers for {config_id}: {e}")

    async def supports_balance(self) -> bool:
        """Hyperliquid provides full account balance data."""
        return True
