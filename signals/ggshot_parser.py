"""
ggShot Signal Parser

Parses ggShot trading signals from Telegram messages into structured data.
Handles the specific format used by the ggShot indicator bot.

Expected ggShot format:
📩 #BTCUSDT 1h | Mid-Term
📈 Short Entry Zone: 104289.7-106904.8

🎯 - Strategy Accuracy:  91%
Last 5 signals:  80%
Last 10 signals:  80%
Last 20 signals:  85%

⏳ - Signal details:
Target 1:  102203.9
Target 2:  100118.1
Target 3:  98032.3
Target 4:  91774.9
_____
🧲Trend-Line: 106904.8
❌Stop-Loss: 109042.9
💡After reaching the first target you can put the rest of the position to breakeven
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from core.common.logger import logger

# ggShot signal symbols from CONTEXT.md (141 symbols)
GGSHOT_SYMBOLS = {
    '1INCHUSDT', 'AAVEUSDT', 'ACHUSDT', 'ADAUSDT', 'ALGOUSDT', 'ALICEUSDT', 'ALPHAUSDT', 'ALTUSDT',
    'ANKRUSDT', 'APEUSDT', 'API3USDT', 'APTUSDT', 'ARBUSDT', 'ARKMUSDT', 'ARUSDT', 'ASTRUSDT',
    'ATOMUSDT', 'AUCTIONUSDT', 'AVAXUSDT', 'AXSUSDT', 'BAKEUSDT', 'BALUSDT', 'BANDUSDT', 'BATUSDT',
    'BCHUSDT', 'BELUSDT', 'BIGTIMEUSDT', 'BNBUSDT', 'BNTUSDT', 'BOMEUSDT', 'BTCUSDT', 'CAKEUSDT',
    'CELRUSDT', 'CETUSUSDT', 'CFXUSDT', 'CHRUSDT', 'CHZUSDT', 'COMPUSDT', 'COTIUSDT', 'CRVUSDT',
    'CYBERUSDT', 'DASHUSDT', 'DOGEUSDT', 'DOTUSDT', 'DYDXUSDT', 'EGLDUSDT', 'ENAUSDT', 'ENSUSDT',
    'ETCUSDT', 'ETHFIUSDT', 'ETHUSDT', 'FETUSDT', 'FILUSDT', 'FLMUSDT', 'FLOWUSDT', 'GALAUSDT',
    'GMTUSDT', 'GMXUSDT', 'GRTUSDT', 'GTCUSDT', 'HBARUSDT', 'HIGHUSDT', 'HOOKUSDT', 'ICPUSDT',
    'ICXUSDT', 'IDUSDT', 'INJUSDT', 'IOSTUSDT', 'IOTXUSDT', 'JASMYUSDT', 'JTOUSDT', 'JUPUSDT',
    'KAVAUSDT', 'KNCUSDT', 'KSMUSDT', 'LDOUSDT', 'LEVERUSDT', 'LINKUSDT', 'LPTUSDT', 'LQTYUSDT',
    'LRCUSDT', 'LTCUSDT', 'MAGICUSDT', 'MANAUSDT', 'MASKUSDT', 'MATICUSDT', 'MKRUSDT', 'NEARUSDT',
    'NEOUSDT', 'NKNUSDT', 'NMRUSDT', 'NOTUSDT', 'NTRNUSDT', 'OGNUSDT', 'ONDOUSDT', 'ONEUSDT',
    'ONTUSDT', 'OPUSDT', 'ORDIUSDT', 'PENDLEUSDT', 'PEOPLEUSDT', 'PYTHUSDT', 'QTUMUSDT', 'RAREUSDT',
    'RENDERUSDT', 'RLCUSDT', 'ROSEUSDT', 'RSRUSDT', 'RUNEUSDT', 'RVNUSDT', 'SANDUSDT', 'SEIUSDT',
    'SFPUSDT', 'SKLUSUSDT', 'SNXUSDT', 'SOLUSDT', 'STORJUSDT', 'STRKUSDT', 'STXUSDT', 'SUIUSDT',
    'SUSDT', 'SUSHIUSDT', 'SXPUSDT', 'TAOUSDT', 'THETAUSDT', 'TIAUSDT', 'TRBUSDT', 'TRXUSDT',
    'TURBOUSDT', 'TWTUSDT', 'VANRYUSDT', 'VETUSDT', 'WIFUSDT', 'WLDUSDT', 'WOOUSDT', 'WUSDT',
    'XRPUSDT', 'YFIUSDT', 'ZILUSDT', 'ZROUSDT', 'ZRXUSDT'
}


class GGShotParser:
    """Parser for ggShot trading signals from Telegram."""
    
    def __init__(self):
        """Initialize the parser."""
        self.logger = logger.bind(module="ggshot.parser")
    
    def is_valid_signal(self, message: str) -> bool:
        """
        Check if a message is a valid ggShot signal (not a report).
        
        Args:
            message (str): Raw Telegram message
            
        Returns:
            bool: True if it's a valid signal, False otherwise
        """
        # Convert to lowercase for case-insensitive matching
        message_lower = message.lower()
        
        # Messages to ignore
        ignore_patterns = [
            '#dailyreport',
            '#report',
            'daily report',
            'signal report',
            'performance report'
        ]
        
        # Check if message contains ignore patterns
        for pattern in ignore_patterns:
            if pattern in message_lower:
                self.logger.debug(f"Ignoring message with pattern: {pattern}")
                return False
        
        # Must contain signal indicators
        required_patterns = [
            r'#[A-Z]+USDT',  # Trading pair like #BTCUSDT
            r'(📈|📉)',      # Direction indicators
            r'entry zone:',  # Entry zone
            r'target \d+:',  # Targets
            r'stop-loss:'    # Stop loss
        ]
        
        for pattern in required_patterns:
            if not re.search(pattern, message, re.IGNORECASE):
                self.logger.debug(f"Missing required pattern: {pattern}")
                return False
        
        self.logger.debug("Message validated as ggShot signal")
        return True
    
    def parse_signal(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Parse a ggShot signal message into structured data.
        
        Args:
            message (str): Raw Telegram message
            
        Returns:
            Optional[Dict[str, Any]]: Parsed signal data or None if parsing fails
        """
        if not self.is_valid_signal(message):
            return None
        
        try:
            signal_data = {
                'raw_message': message,
                'parsed_at': datetime.now(timezone.utc).isoformat(),
                'source': 'telegram',
                'data_type': 'ggshot_signal'
            }
            
            # Parse symbol (e.g., #BTCUSDT -> BTC/USDT)
            symbol_match = re.search(r'#([A-Z0-9]+(?:USDT|USD|BUSD|ETH|BTC))', message)
            if symbol_match:
                symbol_raw = symbol_match.group(1)
                signal_data['symbol'] = self._convert_symbol_format(symbol_raw)
            else:
                self.logger.error("Could not parse symbol from message")
                return None
            
            # Parse timeframe (e.g., "1h | Mid-Term" -> "1h")
            timeframe_match = re.search(r'(\d+[mhd])', message)
            if timeframe_match:
                signal_data['timeframe'] = timeframe_match.group(1)
            else:
                signal_data['timeframe'] = '1h'  # Default fallback
            
            # Parse direction (📈 = Short, 📉 = Long)
            if '📈' in message:
                direction_match = re.search(r'📈\s*(Short|Long)', message, re.IGNORECASE)
                if direction_match:
                    signal_data['direction'] = direction_match.group(1).upper()
                else:
                    signal_data['direction'] = 'SHORT'  # Default for 📈
            elif '📉' in message:
                direction_match = re.search(r'📉\s*(Short|Long)', message, re.IGNORECASE)
                if direction_match:
                    signal_data['direction'] = direction_match.group(1).upper()
                else:
                    signal_data['direction'] = 'LONG'  # Default for 📉
            else:
                self.logger.error("Could not determine signal direction")
                return None
            
            # Parse entry zone (e.g., "Entry Zone: 104289.7-106904.8")
            entry_match = re.search(r'entry zone:\s*([\d.]+)-([\d.]+)', message, re.IGNORECASE)
            if entry_match:
                entry_low = float(entry_match.group(1))
                entry_high = float(entry_match.group(2))
                signal_data['entry_zone'] = {
                    'low': entry_low,
                    'high': entry_high,
                    'mid': (entry_low + entry_high) / 2
                }
            else:
                self.logger.error("Could not parse entry zone")
                return None
            
            # Parse targets
            targets = []
            target_matches = re.findall(r'target (\d+):\s*([\d.]+)', message, re.IGNORECASE)
            for target_num, target_price in target_matches:
                targets.append({
                    'number': int(target_num),
                    'price': float(target_price)
                })
            
            if targets:
                signal_data['targets'] = sorted(targets, key=lambda x: x['number'])
                signal_data['target_1'] = targets[0]['price']  # Primary target for trading
            else:
                self.logger.error("Could not parse targets")
                return None
            
            # Parse stop loss
            sl_match = re.search(r'stop-loss:\s*([\d.]+)', message, re.IGNORECASE)
            if sl_match:
                signal_data['stop_loss'] = float(sl_match.group(1))
            else:
                self.logger.error("Could not parse stop loss")
                return None
            
            # Parse accuracy stats (optional)
            accuracy_match = re.search(r'strategy accuracy:\s*(\d+)%', message, re.IGNORECASE)
            if accuracy_match:
                signal_data['strategy_accuracy'] = int(accuracy_match.group(1))
            
            # Parse trend line (optional)
            trend_match = re.search(r'trend-line:\s*([\d.]+)', message, re.IGNORECASE)
            if trend_match:
                signal_data['trend_line'] = float(trend_match.group(1))
            
            # Create indicators dict for market_data table
            signal_data['indicators'] = {
                'ggshot_signal': {
                    'direction': signal_data['direction'],
                    'entry_zone': signal_data['entry_zone'],
                    'targets': signal_data['targets'],
                    'stop_loss': signal_data['stop_loss'],
                    'timeframe': signal_data['timeframe'],  # Include timeframe in stored data
                    'strategy_accuracy': signal_data.get('strategy_accuracy'),
                    'trend_line': signal_data.get('trend_line')
                }
            }
            
            self.logger.info(
                f"Successfully parsed ggShot signal: {signal_data['symbol']} "
                f"{signal_data['direction']} ({signal_data['timeframe']}) at {signal_data['entry_zone']['mid']}"
            )
            
            return signal_data
            
        except Exception as e:
            self.logger.error(f"Error parsing ggShot signal: {str(e)}")
            return None
    
    def _convert_symbol_format(self, symbol_raw: str) -> str:
        """
        Convert trading symbol to standard format using comprehensive ggShot symbol mapping.
        
        Args:
            symbol_raw (str): Raw symbol from signal (e.g., 'BTCUSDT', 'ETHBTC')
            
        Returns:
            str: Formatted symbol (e.g., 'BTC/USDT', 'ETH/BTC')
        """
        # Check if this is a known ggShot symbol
        if symbol_raw in GGSHOT_SYMBOLS:
            # Convert known ggShot format to standard format
            return self._parse_ggshot_symbol_to_standard(symbol_raw)
        
        # Fallback for unknown symbols: use original logic
        quote_currencies = ['USDT', 'BUSD', 'USD', 'BTC', 'ETH']
        
        for quote in quote_currencies:
            if symbol_raw.endswith(quote):
                base = symbol_raw.replace(quote, '')
                return f"{base}/{quote}"
        
        # Final fallback: assume USDT if no quote currency detected
        self.logger.warning(f"Unknown symbol format for {symbol_raw}, assuming USDT")
        return f"{symbol_raw}/USDT"
    
    def _parse_ggshot_symbol_to_standard(self, symbol_raw: str) -> str:
        """
        Parse ggShot symbol format to standard format.
        
        Args:
            symbol_raw (str): ggShot symbol (e.g., 'BTCUSDT')
            
        Returns:
            str: Standard symbol format (e.g., 'BTC/USDT')
        """
        # All ggShot symbols from CONTEXT.md are USDT pairs
        # Handle special cases and edge cases
        
        # Special handling for specific symbols
        special_cases = {
            '1INCHUSDT': '1INCH/USDT',
            'SUSDT': 'S/USDT',  # Handle single letter base
            'WUSDT': 'W/USDT',   # Handle single letter base
            'SKLUSUSDT': 'SKLUS/USDT',  # Handle SKLUS typo -> maps to SKL/USDT in CCXT
        }
        
        if symbol_raw in special_cases:
            return special_cases[symbol_raw]
        
        # Standard case: all others end with USDT
        if symbol_raw.endswith('USDT'):
            base = symbol_raw[:-4]  # Remove 'USDT'
            return f"{base}/USDT"
        
        # Should not happen for known ggShot symbols, but safety fallback
        self.logger.warning(f"Unexpected ggShot symbol format: {symbol_raw}")
        return f"{symbol_raw}/USDT"
    
    def format_for_storage(self, signal_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Format parsed signal data for storage in market_data table.
        
        Args:
            signal_data (Dict[str, Any]): Parsed signal data
            user_id (str): User ID for the signal
            
        Returns:
            Dict[str, Any]: Formatted data for database storage
        """
        return {
            'user_id': user_id,
            'symbol': signal_data['symbol'],
            'timeframe': signal_data['timeframe'],
            'source': 'telegram',
            'data_type': 'ggshot_signal',
            'indicators': signal_data['indicators'],
            'raw_data': signal_data['raw_message'],
            'created_at': signal_data['parsed_at']  # Will be mapped to updated_at in storage
        }