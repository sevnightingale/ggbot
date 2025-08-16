"""
CCXT Price Provider for the Decision Module.

This provider fetches current market prices from liquid cryptocurrency exchanges 
using the CCXT library. It tries multiple exchanges for reliability.
"""

import ccxt.async_support as ccxt
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict
from core.common.logger import logger
from decision.interfaces.price_provider import PriceProvider


class CCXTPriceProvider(PriceProvider):
    """
    Price provider implementation using CCXT library.
    
    This provider fetches prices from multiple liquid exchanges (NOT testnets)
    to ensure accurate real market pricing. It tries exchanges in order of 
    preference until it gets a successful response.
    """
    
    # Ordered list of exchanges to try (most liquid/reliable first)
    EXCHANGE_PRIORITY = ['binance', 'coinbase', 'kraken', 'okx', 'bybit']
    
    # Symbol mappings for different exchanges
    EXCHANGE_SYMBOL_MAPS = {
        'binance': {
            # Major pairs with USD/USDT mapping
            'BTC/USD': 'BTC/USDT',  # Binance doesn't have true USD pairs
            'BTC/USDT': 'BTC/USDT',
            'ETH/USD': 'ETH/USDT',
            'ETH/USDT': 'ETH/USDT',
            'BNB/USD': 'BNB/USDT',
            'BNB/USDT': 'BNB/USDT',
            'XRP/USD': 'XRP/USDT',
            'XRP/USDT': 'XRP/USDT',
            'ADA/USD': 'ADA/USDT',
            'ADA/USDT': 'ADA/USDT',
            'SOL/USD': 'SOL/USDT',
            'SOL/USDT': 'SOL/USDT',
            'DOGE/USD': 'DOGE/USDT',
            'DOGE/USDT': 'DOGE/USDT',
            'AVAX/USD': 'AVAX/USDT',
            'AVAX/USDT': 'AVAX/USDT',
            
            # All 141 ggShot symbols (USDT pairs on Binance - identity mappings since Binance uses slash format)
            '1INCH/USDT': '1INCH/USDT', 'AAVE/USDT': 'AAVE/USDT', 'ACH/USDT': 'ACH/USDT', 'ADA/USDT': 'ADA/USDT',
            'ALGO/USDT': 'ALGO/USDT', 'ALICE/USDT': 'ALICE/USDT', 'ALPHA/USDT': 'ALPHA/USDT', 'ALT/USDT': 'ALT/USDT',
            'ANKR/USDT': 'ANKR/USDT', 'APE/USDT': 'APE/USDT', 'API3/USDT': 'API3/USDT', 'APT/USDT': 'APT/USDT',
            'ARB/USDT': 'ARB/USDT', 'ARKM/USDT': 'ARKM/USDT', 'AR/USDT': 'AR/USDT', 'ASTR/USDT': 'ASTR/USDT',
            'ATOM/USDT': 'ATOM/USDT', 'AUCTION/USDT': 'AUCTION/USDT', 'AXS/USDT': 'AXS/USDT', 'BAKE/USDT': 'BAKE/USDT',
            'BAL/USDT': 'BAL/USDT', 'BAND/USDT': 'BAND/USDT', 'BAT/USDT': 'BAT/USDT', 'BCH/USDT': 'BCH/USDT',
            'BEL/USDT': 'BEL/USDT', 'BIGTIME/USDT': 'BIGTIME/USDT', 'BNT/USDT': 'BNT/USDT', 'BOME/USDT': 'BOME/USDT',
            'CAKE/USDT': 'CAKE/USDT', 'CELR/USDT': 'CELR/USDT', 'CETUS/USDT': 'CETUS/USDT', 'CFX/USDT': 'CFX/USDT',
            'CHR/USDT': 'CHR/USDT', 'CHZ/USDT': 'CHZ/USDT', 'COMP/USDT': 'COMP/USDT', 'COTI/USDT': 'COTI/USDT',
            'CRV/USDT': 'CRV/USDT', 'CYBER/USDT': 'CYBER/USDT', 'DASH/USDT': 'DASH/USDT', 'DOT/USDT': 'DOT/USDT',
            'DYDX/USDT': 'DYDX/USDT', 'EGLD/USDT': 'EGLD/USDT', 'ENA/USDT': 'ENA/USDT', 'ENS/USDT': 'ENS/USDT',
            'ETC/USDT': 'ETC/USDT', 'ETHFI/USDT': 'ETHFI/USDT', 'FET/USDT': 'FET/USDT', 'FIL/USDT': 'FIL/USDT',
            'FLM/USDT': 'FLM/USDT', 'FLOW/USDT': 'FLOW/USDT', 'GALA/USDT': 'GALA/USDT', 'GMT/USDT': 'GMT/USDT',
            'GMX/USDT': 'GMX/USDT', 'GRT/USDT': 'GRT/USDT', 'GTC/USDT': 'GTC/USDT', 'HBAR/USDT': 'HBAR/USDT',
            'HIGH/USDT': 'HIGH/USDT', 'HOOK/USDT': 'HOOK/USDT', 'ICP/USDT': 'ICP/USDT', 'ICX/USDT': 'ICX/USDT',
            'ID/USDT': 'ID/USDT', 'INJ/USDT': 'INJ/USDT', 'IOST/USDT': 'IOST/USDT', 'IOTX/USDT': 'IOTX/USDT',
            'JASMY/USDT': 'JASMY/USDT', 'JTO/USDT': 'JTO/USDT', 'JUP/USDT': 'JUP/USDT', 'KAVA/USDT': 'KAVA/USDT',
            'KNC/USDT': 'KNC/USDT', 'KSM/USDT': 'KSM/USDT', 'LDO/USDT': 'LDO/USDT', 'LEVER/USDT': 'LEVER/USDT',
            'LINK/USDT': 'LINK/USDT', 'LPT/USDT': 'LPT/USDT', 'LQTY/USDT': 'LQTY/USDT', 'LRC/USDT': 'LRC/USDT',
            'LTC/USDT': 'LTC/USDT', 'MAGIC/USDT': 'MAGIC/USDT', 'MANA/USDT': 'MANA/USDT', 'MASK/USDT': 'MASK/USDT',
            'MATIC/USDT': 'MATIC/USDT', 'MKR/USDT': 'MKR/USDT', 'NEAR/USDT': 'NEAR/USDT', 'NEO/USDT': 'NEO/USDT',
            'NKN/USDT': 'NKN/USDT', 'NMR/USDT': 'NMR/USDT', 'NOT/USDT': 'NOT/USDT', 'NTRN/USDT': 'NTRN/USDT',
            'OGN/USDT': 'OGN/USDT', 'ONDO/USDT': 'ONDO/USDT', 'ONE/USDT': 'ONE/USDT', 'ONT/USDT': 'ONT/USDT',
            'OP/USDT': 'OP/USDT', 'ORDI/USDT': 'ORDI/USDT', 'PENDLE/USDT': 'PENDLE/USDT', 'PEOPLE/USDT': 'PEOPLE/USDT',
            'PYTH/USDT': 'PYTH/USDT', 'QTUM/USDT': 'QTUM/USDT', 'RARE/USDT': 'RARE/USDT', 'RENDER/USDT': 'RENDER/USDT',
            'RLC/USDT': 'RLC/USDT', 'ROSE/USDT': 'ROSE/USDT', 'RSR/USDT': 'RSR/USDT', 'RUNE/USDT': 'RUNE/USDT',
            'RVN/USDT': 'RVN/USDT', 'SAND/USDT': 'SAND/USDT', 'SEI/USDT': 'SEI/USDT', 'SFP/USDT': 'SFP/USDT',
            'SKLUS/USDT': 'SKL/USDT', 'SNX/USDT': 'SNX/USDT', 'STORJ/USDT': 'STORJ/USDT', 'STRK/USDT': 'STRK/USDT',
            'STX/USDT': 'STX/USDT', 'SUI/USDT': 'SUI/USDT', 'S/USDT': 'S/USDT', 'SUSHI/USDT': 'SUSHI/USDT',
            'SXP/USDT': 'SXP/USDT', 'TAO/USDT': 'TAO/USDT', 'THETA/USDT': 'THETA/USDT', 'TIA/USDT': 'TIA/USDT',
            'TRB/USDT': 'TRB/USDT', 'TRX/USDT': 'TRX/USDT', 'TURBO/USDT': 'TURBO/USDT', 'TWT/USDT': 'TWT/USDT',
            'VANRY/USDT': 'VANRY/USDT', 'VET/USDT': 'VET/USDT', 'WIF/USDT': 'WIF/USDT', 'WLD/USDT': 'WLD/USDT',
            'WOO/USDT': 'WOO/USDT', 'W/USDT': 'W/USDT', 'YFI/USDT': 'YFI/USDT', 'ZIL/USDT': 'ZIL/USDT',
            'ZRO/USDT': 'ZRO/USDT', 'ZRX/USDT': 'ZRX/USDT',
        },
        'coinbase': {
            # Major pairs with USD/USDT mapping
            'BTC/USD': 'BTC/USD',
            'BTC/USDT': 'BTC/USD',  # Use USD equivalent
            'ETH/USD': 'ETH/USD',
            'ETH/USDT': 'ETH/USD',
            'SOL/USD': 'SOL/USD',
            'SOL/USDT': 'SOL/USD',
            'AVAX/USD': 'AVAX/USD',
            'AVAX/USDT': 'AVAX/USD',
            
            # All 141 ggShot symbols (USDT pairs on Coinbase)
            '1INCH/USDT': '1INCH/USD', 'AAVE/USDT': 'AAVE/USD', 'ACH/USDT': 'ACH/USD', 'ADA/USDT': 'ADA/USD',
            'ALGO/USDT': 'ALGO/USD', 'ALICE/USDT': 'ALICE/USD', 'ALPHA/USDT': 'ALPHA/USD', 'ALT/USDT': 'ALT/USD',
            'ANKR/USDT': 'ANKR/USD', 'APE/USDT': 'APE/USD', 'API3/USDT': 'API3/USD', 'APT/USDT': 'APT/USD',
            'ARB/USDT': 'ARB/USD', 'ARKM/USDT': 'ARKM/USD', 'AR/USDT': 'AR/USD', 'ASTR/USDT': 'ASTR/USD',
            'ATOM/USDT': 'ATOM/USD', 'AUCTION/USDT': 'AUCTION/USD', 'AXS/USDT': 'AXS/USD', 'BAKE/USDT': 'BAKE/USD',
            'BAL/USDT': 'BAL/USD', 'BAND/USDT': 'BAND/USD', 'BAT/USDT': 'BAT/USD', 'BCH/USDT': 'BCH/USD',
            'BEL/USDT': 'BEL/USD', 'BIGTIME/USDT': 'BIGTIME/USD', 'BNT/USDT': 'BNT/USD', 'BOME/USDT': 'BOME/USD',
            'CAKE/USDT': 'CAKE/USD', 'CELR/USDT': 'CELR/USD', 'CETUS/USDT': 'CETUS/USD', 'CFX/USDT': 'CFX/USD',
            'CHR/USDT': 'CHR/USD', 'CHZ/USDT': 'CHZ/USD', 'COMP/USDT': 'COMP/USD', 'COTI/USDT': 'COTI/USD',
            'CRV/USDT': 'CRV/USD', 'CYBER/USDT': 'CYBER/USD', 'DASH/USDT': 'DASH/USD', 'DOT/USDT': 'DOT/USD',
            'DYDX/USDT': 'DYDX/USD', 'EGLD/USDT': 'EGLD/USD', 'ENA/USDT': 'ENA/USD', 'ENS/USDT': 'ENS/USD',
            'ETC/USDT': 'ETC/USD', 'ETHFI/USDT': 'ETHFI/USD', 'FET/USDT': 'FET/USD', 'FIL/USDT': 'FIL/USD',
            'FLM/USDT': 'FLM/USD', 'FLOW/USDT': 'FLOW/USD', 'GALA/USDT': 'GALA/USD', 'GMT/USDT': 'GMT/USD',
            'GMX/USDT': 'GMX/USD', 'GRT/USDT': 'GRT/USD', 'GTC/USDT': 'GTC/USD', 'HBAR/USDT': 'HBAR/USD',
            'HIGH/USDT': 'HIGH/USD', 'HOOK/USDT': 'HOOK/USD', 'ICP/USDT': 'ICP/USD', 'ICX/USDT': 'ICX/USD',
            'ID/USDT': 'ID/USD', 'INJ/USDT': 'INJ/USD', 'IOST/USDT': 'IOST/USD', 'IOTX/USDT': 'IOTX/USD',
            'JASMY/USDT': 'JASMY/USD', 'JTO/USDT': 'JTO/USD', 'JUP/USDT': 'JUP/USD', 'KAVA/USDT': 'KAVA/USD',
            'KNC/USDT': 'KNC/USD', 'KSM/USDT': 'KSM/USD', 'LDO/USDT': 'LDO/USD', 'LEVER/USDT': 'LEVER/USD',
            'LINK/USDT': 'LINK/USD', 'LPT/USDT': 'LPT/USD', 'LQTY/USDT': 'LQTY/USD', 'LRC/USDT': 'LRC/USD',
            'LTC/USDT': 'LTC/USD', 'MAGIC/USDT': 'MAGIC/USD', 'MANA/USDT': 'MANA/USD', 'MASK/USDT': 'MASK/USD',
            'MATIC/USDT': 'MATIC/USD', 'MKR/USDT': 'MKR/USD', 'NEAR/USDT': 'NEAR/USD', 'NEO/USDT': 'NEO/USD',
            'NKN/USDT': 'NKN/USD', 'NMR/USDT': 'NMR/USD', 'NOT/USDT': 'NOT/USD', 'NTRN/USDT': 'NTRN/USD',
            'OGN/USDT': 'OGN/USD', 'ONDO/USDT': 'ONDO/USD', 'ONE/USDT': 'ONE/USD', 'ONT/USDT': 'ONT/USD',
            'OP/USDT': 'OP/USD', 'ORDI/USDT': 'ORDI/USD', 'PENDLE/USDT': 'PENDLE/USD', 'PEOPLE/USDT': 'PEOPLE/USD',
            'PYTH/USDT': 'PYTH/USD', 'QTUM/USDT': 'QTUM/USD', 'RARE/USDT': 'RARE/USD', 'RENDER/USDT': 'RENDER/USD',
            'RLC/USDT': 'RLC/USD', 'ROSE/USDT': 'ROSE/USD', 'RSR/USDT': 'RSR/USD', 'RUNE/USDT': 'RUNE/USD',
            'RVN/USDT': 'RVN/USD', 'SAND/USDT': 'SAND/USD', 'SEI/USDT': 'SEI/USD', 'SFP/USDT': 'SFP/USD',
            'SKLUS/USDT': 'SKLUS/USD', 'SNX/USDT': 'SNX/USD', 'STORJ/USDT': 'STORJ/USD', 'STRK/USDT': 'STRK/USD',
            'STX/USDT': 'STX/USD', 'SUI/USDT': 'SUI/USD', 'S/USDT': 'S/USD', 'SUSHI/USDT': 'SUSHI/USD',
            'SXP/USDT': 'SXP/USD', 'TAO/USDT': 'TAO/USD', 'THETA/USDT': 'THETA/USD', 'TIA/USDT': 'TIA/USD',
            'TRB/USDT': 'TRB/USD', 'TRX/USDT': 'TRX/USD', 'TURBO/USDT': 'TURBO/USD', 'TWT/USDT': 'TWT/USD',
            'VANRY/USDT': 'VANRY/USD', 'VET/USDT': 'VET/USD', 'WIF/USDT': 'WIF/USD', 'WLD/USDT': 'WLD/USD',
            'WOO/USDT': 'WOO/USD', 'W/USDT': 'W/USD', 'YFI/USDT': 'YFI/USD', 'ZIL/USDT': 'ZIL/USD',
            'ZRO/USDT': 'ZRO/USD', 'ZRX/USDT': 'ZRX/USD',
        },
        'kraken': {
            # Major pairs with USD/USDT mapping
            'BTC/USD': 'BTC/USD',
            'BTC/USDT': 'BTC/USDT',
            'ETH/USD': 'ETH/USD',
            'ETH/USDT': 'ETH/USDT',
            'XRP/USD': 'XRP/USD',
            'XRP/USDT': 'XRP/USDT',
            'ADA/USD': 'ADA/USD',
            'ADA/USDT': 'ADA/USDT',
            'SOL/USD': 'SOL/USD',
            'SOL/USDT': 'SOL/USDT',
            'DOGE/USD': 'DOGE/USD',
            'DOGE/USDT': 'DOGE/USDT',
            
            # All 141 ggShot symbols (USDT pairs on Kraken)
            '1INCH/USDT': '1INCH/USDT', 'AAVE/USDT': 'AAVE/USDT', 'ACH/USDT': 'ACH/USDT', 'ADA/USDT': 'ADA/USDT',
            'ALGO/USDT': 'ALGO/USDT', 'ALICE/USDT': 'ALICE/USDT', 'ALPHA/USDT': 'ALPHA/USDT', 'ALT/USDT': 'ALT/USDT',
            'ANKR/USDT': 'ANKR/USDT', 'APE/USDT': 'APE/USDT', 'API3/USDT': 'API3/USDT', 'APT/USDT': 'APT/USDT',
            'ARB/USDT': 'ARB/USDT', 'ARKM/USDT': 'ARKM/USDT', 'AR/USDT': 'AR/USDT', 'ASTR/USDT': 'ASTR/USDT',
            'ATOM/USDT': 'ATOM/USDT', 'AUCTION/USDT': 'AUCTION/USDT', 'AXS/USDT': 'AXS/USDT', 'BAKE/USDT': 'BAKE/USDT',
            'BAL/USDT': 'BAL/USDT', 'BAND/USDT': 'BAND/USDT', 'BAT/USDT': 'BAT/USDT', 'BCH/USDT': 'BCH/USDT',
            'BEL/USDT': 'BEL/USDT', 'BIGTIME/USDT': 'BIGTIME/USDT', 'BNT/USDT': 'BNT/USDT', 'BOME/USDT': 'BOME/USDT',
            'CAKE/USDT': 'CAKE/USDT', 'CELR/USDT': 'CELR/USDT', 'CETUS/USDT': 'CETUS/USDT', 'CFX/USDT': 'CFX/USDT',
            'CHR/USDT': 'CHR/USDT', 'CHZ/USDT': 'CHZ/USDT', 'COMP/USDT': 'COMP/USDT', 'COTI/USDT': 'COTI/USDT',
            'CRV/USDT': 'CRV/USDT', 'CYBER/USDT': 'CYBER/USDT', 'DASH/USDT': 'DASH/USDT', 'DOT/USDT': 'DOT/USDT',
            'DYDX/USDT': 'DYDX/USDT', 'EGLD/USDT': 'EGLD/USDT', 'ENA/USDT': 'ENA/USDT', 'ENS/USDT': 'ENS/USDT',
            'ETC/USDT': 'ETC/USDT', 'ETHFI/USDT': 'ETHFI/USDT', 'FET/USDT': 'FET/USDT', 'FIL/USDT': 'FIL/USDT',
            'FLM/USDT': 'FLM/USDT', 'FLOW/USDT': 'FLOW/USDT', 'GALA/USDT': 'GALA/USDT', 'GMT/USDT': 'GMT/USDT',
            'GMX/USDT': 'GMX/USDT', 'GRT/USDT': 'GRT/USDT', 'GTC/USDT': 'GTC/USDT', 'HBAR/USDT': 'HBAR/USDT',
            'HIGH/USDT': 'HIGH/USDT', 'HOOK/USDT': 'HOOK/USDT', 'ICP/USDT': 'ICP/USDT', 'ICX/USDT': 'ICX/USDT',
            'ID/USDT': 'ID/USDT', 'INJ/USDT': 'INJ/USDT', 'IOST/USDT': 'IOST/USDT', 'IOTX/USDT': 'IOTX/USDT',
            'JASMY/USDT': 'JASMY/USDT', 'JTO/USDT': 'JTO/USDT', 'JUP/USDT': 'JUP/USDT', 'KAVA/USDT': 'KAVA/USDT',
            'KNC/USDT': 'KNC/USDT', 'KSM/USDT': 'KSM/USDT', 'LDO/USDT': 'LDO/USDT', 'LEVER/USDT': 'LEVER/USDT',
            'LINK/USDT': 'LINK/USDT', 'LPT/USDT': 'LPT/USDT', 'LQTY/USDT': 'LQTY/USDT', 'LRC/USDT': 'LRC/USDT',
            'LTC/USDT': 'LTC/USDT', 'MAGIC/USDT': 'MAGIC/USDT', 'MANA/USDT': 'MANA/USDT', 'MASK/USDT': 'MASK/USDT',
            'MATIC/USDT': 'MATIC/USDT', 'MKR/USDT': 'MKR/USDT', 'NEAR/USDT': 'NEAR/USDT', 'NEO/USDT': 'NEO/USDT',
            'NKN/USDT': 'NKN/USDT', 'NMR/USDT': 'NMR/USDT', 'NOT/USDT': 'NOT/USDT', 'NTRN/USDT': 'NTRN/USDT',
            'OGN/USDT': 'OGN/USDT', 'ONDO/USDT': 'ONDO/USDT', 'ONE/USDT': 'ONE/USDT', 'ONT/USDT': 'ONT/USDT',
            'OP/USDT': 'OP/USDT', 'ORDI/USDT': 'ORDI/USDT', 'PENDLE/USDT': 'PENDLE/USDT', 'PEOPLE/USDT': 'PEOPLE/USDT',
            'PYTH/USDT': 'PYTH/USDT', 'QTUM/USDT': 'QTUM/USDT', 'RARE/USDT': 'RARE/USDT', 'RENDER/USDT': 'RENDER/USDT',
            'RLC/USDT': 'RLC/USDT', 'ROSE/USDT': 'ROSE/USDT', 'RSR/USDT': 'RSR/USDT', 'RUNE/USDT': 'RUNE/USDT',
            'RVN/USDT': 'RVN/USDT', 'SAND/USDT': 'SAND/USDT', 'SEI/USDT': 'SEI/USDT', 'SFP/USDT': 'SFP/USDT',
            'SKLUS/USDT': 'SKL/USDT', 'SNX/USDT': 'SNX/USDT', 'STORJ/USDT': 'STORJ/USDT', 'STRK/USDT': 'STRK/USDT',
            'STX/USDT': 'STX/USDT', 'SUI/USDT': 'SUI/USDT', 'S/USDT': 'S/USDT', 'SUSHI/USDT': 'SUSHI/USDT',
            'SXP/USDT': 'SXP/USDT', 'TAO/USDT': 'TAO/USDT', 'THETA/USDT': 'THETA/USDT', 'TIA/USDT': 'TIA/USDT',
            'TRB/USDT': 'TRB/USDT', 'TRX/USDT': 'TRX/USDT', 'TURBO/USDT': 'TURBO/USDT', 'TWT/USDT': 'TWT/USDT',
            'VANRY/USDT': 'VANRY/USDT', 'VET/USDT': 'VET/USDT', 'WIF/USDT': 'WIF/USDT', 'WLD/USDT': 'WLD/USDT',
            'WOO/USDT': 'WOO/USDT', 'W/USDT': 'W/USDT', 'YFI/USDT': 'YFI/USDT', 'ZIL/USDT': 'ZIL/USDT',
            'ZRO/USDT': 'ZRO/USDT', 'ZRX/USDT': 'ZRX/USDT',
        },
        'okx': {
            # Major pairs with USD/USDT mapping
            'BTC/USD': 'BTC/USDT',  # OKX uses USDT
            'BTC/USDT': 'BTC/USDT',
            'ETH/USD': 'ETH/USDT',
            'ETH/USDT': 'ETH/USDT',
            'BNB/USD': 'BNB/USDT',
            'BNB/USDT': 'BNB/USDT',
            'XRP/USD': 'XRP/USDT',
            'XRP/USDT': 'XRP/USDT',
            'ADA/USD': 'ADA/USDT',
            'ADA/USDT': 'ADA/USDT',
            'SOL/USD': 'SOL/USDT',
            'SOL/USDT': 'SOL/USDT',
            'DOGE/USD': 'DOGE/USDT',
            'DOGE/USDT': 'DOGE/USDT',
            
            # All 141 ggShot symbols (USDT pairs on OKX)
            '1INCH/USDT': '1INCH/USDT', 'AAVE/USDT': 'AAVE/USDT', 'ACH/USDT': 'ACH/USDT', 'ADA/USDT': 'ADA/USDT',
            'ALGO/USDT': 'ALGO/USDT', 'ALICE/USDT': 'ALICE/USDT', 'ALPHA/USDT': 'ALPHA/USDT', 'ALT/USDT': 'ALT/USDT',
            'ANKR/USDT': 'ANKR/USDT', 'APE/USDT': 'APE/USDT', 'API3/USDT': 'API3/USDT', 'APT/USDT': 'APT/USDT',
            'ARB/USDT': 'ARB/USDT', 'ARKM/USDT': 'ARKM/USDT', 'AR/USDT': 'AR/USDT', 'ASTR/USDT': 'ASTR/USDT',
            'ATOM/USDT': 'ATOM/USDT', 'AUCTION/USDT': 'AUCTION/USDT', 'AXS/USDT': 'AXS/USDT', 'BAKE/USDT': 'BAKE/USDT',
            'BAL/USDT': 'BAL/USDT', 'BAND/USDT': 'BAND/USDT', 'BAT/USDT': 'BAT/USDT', 'BCH/USDT': 'BCH/USDT',
            'BEL/USDT': 'BEL/USDT', 'BIGTIME/USDT': 'BIGTIME/USDT', 'BNT/USDT': 'BNT/USDT', 'BOME/USDT': 'BOME/USDT',
            'CAKE/USDT': 'CAKE/USDT', 'CELR/USDT': 'CELR/USDT', 'CETUS/USDT': 'CETUS/USDT', 'CFX/USDT': 'CFX/USDT',
            'CHR/USDT': 'CHR/USDT', 'CHZ/USDT': 'CHZ/USDT', 'COMP/USDT': 'COMP/USDT', 'COTI/USDT': 'COTI/USDT',
            'CRV/USDT': 'CRV/USDT', 'CYBER/USDT': 'CYBER/USDT', 'DASH/USDT': 'DASH/USDT', 'DOT/USDT': 'DOT/USDT',
            'DYDX/USDT': 'DYDX/USDT', 'EGLD/USDT': 'EGLD/USDT', 'ENA/USDT': 'ENA/USDT', 'ENS/USDT': 'ENS/USDT',
            'ETC/USDT': 'ETC/USDT', 'ETHFI/USDT': 'ETHFI/USDT', 'FET/USDT': 'FET/USDT', 'FIL/USDT': 'FIL/USDT',
            'FLM/USDT': 'FLM/USDT', 'FLOW/USDT': 'FLOW/USDT', 'GALA/USDT': 'GALA/USDT', 'GMT/USDT': 'GMT/USDT',
            'GMX/USDT': 'GMX/USDT', 'GRT/USDT': 'GRT/USDT', 'GTC/USDT': 'GTC/USDT', 'HBAR/USDT': 'HBAR/USDT',
            'HIGH/USDT': 'HIGH/USDT', 'HOOK/USDT': 'HOOK/USDT', 'ICP/USDT': 'ICP/USDT', 'ICX/USDT': 'ICX/USDT',
            'ID/USDT': 'ID/USDT', 'INJ/USDT': 'INJ/USDT', 'IOST/USDT': 'IOST/USDT', 'IOTX/USDT': 'IOTX/USDT',
            'JASMY/USDT': 'JASMY/USDT', 'JTO/USDT': 'JTO/USDT', 'JUP/USDT': 'JUP/USDT', 'KAVA/USDT': 'KAVA/USDT',
            'KNC/USDT': 'KNC/USDT', 'KSM/USDT': 'KSM/USDT', 'LDO/USDT': 'LDO/USDT', 'LEVER/USDT': 'LEVER/USDT',
            'LINK/USDT': 'LINK/USDT', 'LPT/USDT': 'LPT/USDT', 'LQTY/USDT': 'LQTY/USDT', 'LRC/USDT': 'LRC/USDT',
            'LTC/USDT': 'LTC/USDT', 'MAGIC/USDT': 'MAGIC/USDT', 'MANA/USDT': 'MANA/USDT', 'MASK/USDT': 'MASK/USDT',
            'MATIC/USDT': 'MATIC/USDT', 'MKR/USDT': 'MKR/USDT', 'NEAR/USDT': 'NEAR/USDT', 'NEO/USDT': 'NEO/USDT',
            'NKN/USDT': 'NKN/USDT', 'NMR/USDT': 'NMR/USDT', 'NOT/USDT': 'NOT/USDT', 'NTRN/USDT': 'NTRN/USDT',
            'OGN/USDT': 'OGN/USDT', 'ONDO/USDT': 'ONDO/USDT', 'ONE/USDT': 'ONE/USDT', 'ONT/USDT': 'ONT/USDT',
            'OP/USDT': 'OP/USDT', 'ORDI/USDT': 'ORDI/USDT', 'PENDLE/USDT': 'PENDLE/USDT', 'PEOPLE/USDT': 'PEOPLE/USDT',
            'PYTH/USDT': 'PYTH/USDT', 'QTUM/USDT': 'QTUM/USDT', 'RARE/USDT': 'RARE/USDT', 'RENDER/USDT': 'RENDER/USDT',
            'RLC/USDT': 'RLC/USDT', 'ROSE/USDT': 'ROSE/USDT', 'RSR/USDT': 'RSR/USDT', 'RUNE/USDT': 'RUNE/USDT',
            'RVN/USDT': 'RVN/USDT', 'SAND/USDT': 'SAND/USDT', 'SEI/USDT': 'SEI/USDT', 'SFP/USDT': 'SFP/USDT',
            'SKLUS/USDT': 'SKL/USDT', 'SNX/USDT': 'SNX/USDT', 'STORJ/USDT': 'STORJ/USDT', 'STRK/USDT': 'STRK/USDT',
            'STX/USDT': 'STX/USDT', 'SUI/USDT': 'SUI/USDT', 'S/USDT': 'S/USDT', 'SUSHI/USDT': 'SUSHI/USDT',
            'SXP/USDT': 'SXP/USDT', 'TAO/USDT': 'TAO/USDT', 'THETA/USDT': 'THETA/USDT', 'TIA/USDT': 'TIA/USDT',
            'TRB/USDT': 'TRB/USDT', 'TRX/USDT': 'TRX/USDT', 'TURBO/USDT': 'TURBO/USDT', 'TWT/USDT': 'TWT/USDT',
            'VANRY/USDT': 'VANRY/USDT', 'VET/USDT': 'VET/USDT', 'WIF/USDT': 'WIF/USDT', 'WLD/USDT': 'WLD/USDT',
            'WOO/USDT': 'WOO/USDT', 'W/USDT': 'W/USDT', 'YFI/USDT': 'YFI/USDT', 'ZIL/USDT': 'ZIL/USDT',
            'ZRO/USDT': 'ZRO/USDT', 'ZRX/USDT': 'ZRX/USDT',
        },
        'bybit': {
            # Major pairs with USD/USDT mapping
            'BTC/USD': 'BTC/USDT',
            'BTC/USDT': 'BTC/USDT',
            'ETH/USD': 'ETH/USDT',
            'ETH/USDT': 'ETH/USDT',
            'SOL/USD': 'SOL/USDT',
            'SOL/USDT': 'SOL/USDT',
            
            # All 141 ggShot symbols (USDT pairs on Bybit)
            '1INCH/USDT': '1INCH/USDT', 'AAVE/USDT': 'AAVE/USDT', 'ACH/USDT': 'ACH/USDT', 'ADA/USDT': 'ADA/USDT',
            'ALGO/USDT': 'ALGO/USDT', 'ALICE/USDT': 'ALICE/USDT', 'ALPHA/USDT': 'ALPHA/USDT', 'ALT/USDT': 'ALT/USDT',
            'ANKR/USDT': 'ANKR/USDT', 'APE/USDT': 'APE/USDT', 'API3/USDT': 'API3/USDT', 'APT/USDT': 'APT/USDT',
            'ARB/USDT': 'ARB/USDT', 'ARKM/USDT': 'ARKM/USDT', 'AR/USDT': 'AR/USDT', 'ASTR/USDT': 'ASTR/USDT',
            'ATOM/USDT': 'ATOM/USDT', 'AUCTION/USDT': 'AUCTION/USDT', 'AXS/USDT': 'AXS/USDT', 'BAKE/USDT': 'BAKE/USDT',
            'BAL/USDT': 'BAL/USDT', 'BAND/USDT': 'BAND/USDT', 'BAT/USDT': 'BAT/USDT', 'BCH/USDT': 'BCH/USDT',
            'BEL/USDT': 'BEL/USDT', 'BIGTIME/USDT': 'BIGTIME/USDT', 'BNT/USDT': 'BNT/USDT', 'BOME/USDT': 'BOME/USDT',
            'CAKE/USDT': 'CAKE/USDT', 'CELR/USDT': 'CELR/USDT', 'CETUS/USDT': 'CETUS/USDT', 'CFX/USDT': 'CFX/USDT',
            'CHR/USDT': 'CHR/USDT', 'CHZ/USDT': 'CHZ/USDT', 'COMP/USDT': 'COMP/USDT', 'COTI/USDT': 'COTI/USDT',
            'CRV/USDT': 'CRV/USDT', 'CYBER/USDT': 'CYBER/USDT', 'DASH/USDT': 'DASH/USDT', 'DOT/USDT': 'DOT/USDT',
            'DYDX/USDT': 'DYDX/USDT', 'EGLD/USDT': 'EGLD/USDT', 'ENA/USDT': 'ENA/USDT', 'ENS/USDT': 'ENS/USDT',
            'ETC/USDT': 'ETC/USDT', 'ETHFI/USDT': 'ETHFI/USDT', 'FET/USDT': 'FET/USDT', 'FIL/USDT': 'FIL/USDT',
            'FLM/USDT': 'FLM/USDT', 'FLOW/USDT': 'FLOW/USDT', 'GALA/USDT': 'GALA/USDT', 'GMT/USDT': 'GMT/USDT',
            'GMX/USDT': 'GMX/USDT', 'GRT/USDT': 'GRT/USDT', 'GTC/USDT': 'GTC/USDT', 'HBAR/USDT': 'HBAR/USDT',
            'HIGH/USDT': 'HIGH/USDT', 'HOOK/USDT': 'HOOK/USDT', 'ICP/USDT': 'ICP/USDT', 'ICX/USDT': 'ICX/USDT',
            'ID/USDT': 'ID/USDT', 'INJ/USDT': 'INJ/USDT', 'IOST/USDT': 'IOST/USDT', 'IOTX/USDT': 'IOTX/USDT',
            'JASMY/USDT': 'JASMY/USDT', 'JTO/USDT': 'JTO/USDT', 'JUP/USDT': 'JUP/USDT', 'KAVA/USDT': 'KAVA/USDT',
            'KNC/USDT': 'KNC/USDT', 'KSM/USDT': 'KSM/USDT', 'LDO/USDT': 'LDO/USDT', 'LEVER/USDT': 'LEVER/USDT',
            'LINK/USDT': 'LINK/USDT', 'LPT/USDT': 'LPT/USDT', 'LQTY/USDT': 'LQTY/USDT', 'LRC/USDT': 'LRC/USDT',
            'LTC/USDT': 'LTC/USDT', 'MAGIC/USDT': 'MAGIC/USDT', 'MANA/USDT': 'MANA/USDT', 'MASK/USDT': 'MASK/USDT',
            'MATIC/USDT': 'MATIC/USDT', 'MKR/USDT': 'MKR/USDT', 'NEAR/USDT': 'NEAR/USDT', 'NEO/USDT': 'NEO/USDT',
            'NKN/USDT': 'NKN/USDT', 'NMR/USDT': 'NMR/USDT', 'NOT/USDT': 'NOT/USDT', 'NTRN/USDT': 'NTRN/USDT',
            'OGN/USDT': 'OGN/USDT', 'ONDO/USDT': 'ONDO/USDT', 'ONE/USDT': 'ONE/USDT', 'ONT/USDT': 'ONT/USDT',
            'OP/USDT': 'OP/USDT', 'ORDI/USDT': 'ORDI/USDT', 'PENDLE/USDT': 'PENDLE/USDT', 'PEOPLE/USDT': 'PEOPLE/USDT',
            'PYTH/USDT': 'PYTH/USDT', 'QTUM/USDT': 'QTUM/USDT', 'RARE/USDT': 'RARE/USDT', 'RENDER/USDT': 'RENDER/USDT',
            'RLC/USDT': 'RLC/USDT', 'ROSE/USDT': 'ROSE/USDT', 'RSR/USDT': 'RSR/USDT', 'RUNE/USDT': 'RUNE/USDT',
            'RVN/USDT': 'RVN/USDT', 'SAND/USDT': 'SAND/USDT', 'SEI/USDT': 'SEI/USDT', 'SFP/USDT': 'SFP/USDT',
            'SKLUS/USDT': 'SKL/USDT', 'SNX/USDT': 'SNX/USDT', 'STORJ/USDT': 'STORJ/USDT', 'STRK/USDT': 'STRK/USDT',
            'STX/USDT': 'STX/USDT', 'SUI/USDT': 'SUI/USDT', 'S/USDT': 'S/USDT', 'SUSHI/USDT': 'SUSHI/USDT',
            'SXP/USDT': 'SXP/USDT', 'TAO/USDT': 'TAO/USDT', 'THETA/USDT': 'THETA/USDT', 'TIA/USDT': 'TIA/USDT',
            'TRB/USDT': 'TRB/USDT', 'TRX/USDT': 'TRX/USDT', 'TURBO/USDT': 'TURBO/USDT', 'TWT/USDT': 'TWT/USDT',
            'VANRY/USDT': 'VANRY/USDT', 'VET/USDT': 'VET/USDT', 'WIF/USDT': 'WIF/USDT', 'WLD/USDT': 'WLD/USDT',
            'WOO/USDT': 'WOO/USDT', 'W/USDT': 'W/USDT', 'YFI/USDT': 'YFI/USDT', 'ZIL/USDT': 'ZIL/USDT',
            'ZRO/USDT': 'ZRO/USDT', 'ZRX/USDT': 'ZRX/USDT',
        }
    }
    
    def __init__(self, **kwargs):
        """Initialize CCXT price provider."""
        super().__init__(**kwargs)
        self._log = logger.bind(provider="ccxt")
        self._exchange_clients = {}  # Cache for exchange clients - NOW WE ACTUALLY USE IT!
    
    async def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """
        Get current price from CCXT exchanges.
        
        Args:
            symbol: Standard trading symbol (e.g., 'BTC/USDT')
            
        Returns:
            Current price as Decimal, or None if unable to fetch
        """
        for exchange_name in self.EXCHANGE_PRIORITY:
            try:
                price = await self._get_price_from_exchange(exchange_name, symbol)
                if price:
                    self._log.info(f"CCXT price for {symbol} from {exchange_name}: ${price}")
                    return price
                    
            except Exception as e:
                self._log.warning(f"Failed to get price from {exchange_name}: {e}")
                continue
        
        self._log.error(f"Failed to get price for {symbol} from all CCXT exchanges")
        return None
    
    async def _get_price_from_exchange(self, exchange_name: str, symbol: str) -> Optional[Decimal]:
        """
        Get price from a specific exchange.
        
        Args:
            exchange_name: Name of the exchange (e.g., 'binance')
            symbol: Standard trading symbol
            
        Returns:
            Price as Decimal or None if failed
        """
        try:
            # Get or create exchange client
            exchange = await self._get_exchange_client(exchange_name)
            if not exchange:
                return None
            
            # Map symbol to exchange-specific format
            exchange_symbol = self._map_symbol_for_exchange(exchange_name, symbol)
            if not exchange_symbol:
                self._log.debug(f"Symbol {symbol} not supported on {exchange_name}")
                return None
            
            # Skip loading all markets - just try to fetch the ticker directly
            # This saves hundreds of MB of memory per exchange
            # Most exchanges support fetching tickers without loading all markets
            try:
                ticker = await exchange.fetch_ticker(exchange_symbol)
            except Exception as ticker_error:
                self._log.debug(f"Symbol {exchange_symbol} not available on {exchange_name}: {ticker_error}")
                return None
            
            # Get last price
            price = ticker.get('last')
            if price and price > 0:
                # Convert to Decimal with high precision to preserve exact values
                return Decimal(str(price)).quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
            
            self._log.warning(f"Invalid price from {exchange_name} for {exchange_symbol}: {price}")
            return None
            
        except Exception as e:
            self._log.error(f"Error fetching from {exchange_name}: {e}")
            return None
        finally:
            # Don't close the connection - keep it cached for reuse
            # This avoids recreating exchanges every 5 seconds
            pass
    
    async def _get_exchange_client(self, exchange_name: str):
        """
        Get or create exchange client.
        
        Args:
            exchange_name: Name of the exchange
            
        Returns:
            Exchange client or None if not available
        """
        try:
            # Reuse cached client if available
            if exchange_name in self._exchange_clients:
                return self._exchange_clients[exchange_name]
            
            # Create new client and cache it
            if hasattr(ccxt, exchange_name):
                exchange_class = getattr(ccxt, exchange_name)
                exchange = exchange_class({
                    'enableRateLimit': True,
                    'timeout': 10000,  # 10 second timeout
                })
                self._exchange_clients[exchange_name] = exchange
                self._log.info(f"Created and cached {exchange_name} client")
                return exchange
            else:
                self._log.warning(f"Exchange {exchange_name} not available in CCXT")
                return None
                
        except Exception as e:
            self._log.error(f"Failed to create {exchange_name} client: {e}")
            return None
    
    def _map_symbol_for_exchange(self, exchange_name: str, symbol: str) -> Optional[str]:
        """
        Map standard symbol to exchange-specific format.
        
        Args:
            exchange_name: Name of the exchange
            symbol: Standard symbol format
            
        Returns:
            Exchange-specific symbol or None if not supported
        """
        exchange_map = self.EXCHANGE_SYMBOL_MAPS.get(exchange_name, {})
        return exchange_map.get(symbol)
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of symbols supported by CCXT provider."""
        # Collect all unique symbols from all exchange mappings
        symbols = set()
        for exchange_map in self.EXCHANGE_SYMBOL_MAPS.values():
            symbols.update(exchange_map.keys())
        return list(symbols)
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return 'ccxt'
    
    async def health_check(self) -> bool:
        """
        Check if CCXT exchanges are accessible.
        
        Returns:
            True if can fetch a price from any exchange, False otherwise
        """
        try:
            # Test with BTC/USDT as it's widely available
            test_symbol = 'BTC/USDT'
            
            for exchange_name in self.EXCHANGE_PRIORITY[:2]:  # Test first 2 exchanges
                try:
                    price = await self._get_price_from_exchange(exchange_name, test_symbol)
                    if price and price > 0:
                        self._log.debug(f"CCXT health check passed via {exchange_name}")
                        return True
                except:
                    continue
            
            self._log.warning("CCXT health check failed - no exchanges accessible")
            return False
            
        except Exception as e:
            self._log.error(f"CCXT health check failed: {e}")
            return False
    
    async def get_current_volume_data(self, symbol: str, period: int = 30, timeframe: str = '1h') -> Optional[Dict]:
        """
        Get current volume and average volume for confirmation analysis.
        Based on ggShot founder's guidance: compare current volume to average 
        volume over the last 20-50 candles (using 30 as standard).
        
        NOTE: Uses the previous completed candle as "current" to avoid inconsistent
        data from incomplete candles in real-time analysis.
        
        Args:
            symbol: Standard trading symbol (e.g., 'BTC/USDT')
            period: Number of candles for volume average calculation (default 30)
            timeframe: Timeframe for volume analysis (default '1h')
            
        Returns:
            Dict with volume data:
            {
                'current_volume': float,  # Last completed candle volume
                'average_volume': float,  # 30-period average (excluding current)
                'volume_ratio': float,    # current/average
                'is_volume_spike': bool   # ratio > 1.5
            }
            Or None if unable to fetch
        """
        for exchange_name in self.EXCHANGE_PRIORITY:
            try:
                volume_data = await self._get_volume_from_exchange(exchange_name, symbol, period, timeframe)
                if volume_data:
                    self._log.info(f"Volume data for {symbol} from {exchange_name}: "
                                 f"current={volume_data['current_volume']:.0f}, "
                                 f"avg={volume_data['average_volume']:.0f}, "
                                 f"ratio={volume_data['volume_ratio']:.2f}")
                    return volume_data
                    
            except Exception as e:
                self._log.warning(f"Failed to get volume from {exchange_name}: {e}")
                continue
        
        self._log.error(f"Failed to get volume data for {symbol} from all CCXT exchanges")
        return None

    async def _get_volume_from_exchange(self, exchange_name: str, symbol: str, period: int, timeframe: str = '1h') -> Optional[Dict]:
        """
        Get volume data from a specific exchange using OHLCV data.
        
        Args:
            exchange_name: Name of the exchange
            symbol: Standard trading symbol
            period: Number of candles for average calculation
            timeframe: Timeframe for volume analysis
            
        Returns:
            Volume data dict or None if failed
        """
        try:
            # Get or create exchange client
            exchange = await self._get_exchange_client(exchange_name)
            if not exchange:
                return None
            
            # Map symbol to exchange-specific format
            exchange_symbol = self._map_symbol_for_exchange(exchange_name, symbol)
            if not exchange_symbol:
                self._log.debug(f"Symbol {symbol} not supported on {exchange_name}")
                return None
            
            # Load markets if not already loaded
            if not hasattr(exchange, 'markets') or not exchange.markets:
                await exchange.load_markets()
            
            # Check if symbol exists
            if exchange_symbol not in exchange.markets:
                self._log.debug(f"Symbol {exchange_symbol} not found in {exchange_name} markets")
                return None
            
            # Fetch OHLCV data for volume analysis
            # Get period + 1 candles to have enough data (current + historical)
            ohlcv_data = await exchange.fetch_ohlcv(
                exchange_symbol, 
                timeframe=timeframe,  # Use signal's native timeframe for volume analysis
                limit=period + 1
            )
            
            if not ohlcv_data or len(ohlcv_data) < 2:
                self._log.warning(f"Insufficient OHLCV data from {exchange_name} for {exchange_symbol}")
                return None
            
            # Extract volumes from OHLCV data
            # OHLCV format: [timestamp, open, high, low, close, volume]
            volumes = [candle[5] for candle in ohlcv_data if candle[5] is not None]
            
            if len(volumes) < 2:
                self._log.warning(f"Insufficient volume data from {exchange_name} for {exchange_symbol}")
                return None
            
            # Use the previous completed candle as "current" to avoid incomplete candle issues
            # volumes[-1] is the current incomplete candle, volumes[-2] is the last completed
            if len(volumes) < 3:
                self._log.warning(f"Need at least 3 candles for proper volume analysis")
                return None
                
            current_volume = volumes[-2]  # Last COMPLETED candle
            
            # Average volume over the specified period (excluding the "current" candle for unbiased comparison)
            # This prevents look-ahead bias in volume analysis
            historical_volumes = volumes[:-2]  # Historical candles only
            if len(historical_volumes) > period:
                historical_volumes = historical_volumes[-period:]  # Take last N candles
            
            if not historical_volumes:
                self._log.warning(f"No historical volume data for {exchange_symbol}")
                return None
            
            average_volume = sum(historical_volumes) / len(historical_volumes)
            
            # Calculate volume ratio
            volume_ratio = current_volume / average_volume if average_volume > 0 else 0
            
            # Determine if this is a volume spike (using 1.5x as threshold)
            is_volume_spike = volume_ratio > 1.5
            
            return {
                'current_volume': float(current_volume),
                'average_volume': float(average_volume),
                'volume_ratio': float(volume_ratio),
                'is_volume_spike': is_volume_spike,
                'period_used': len(historical_volumes),
                'timeframe': timeframe
            }
            
        except Exception as e:
            self._log.error(f"Error fetching volume from {exchange_name}: {e}")
            return None
        finally:
            # Clean up connection
            if exchange_name in self._exchange_clients:
                try:
                    await self._exchange_clients[exchange_name].close()
                    del self._exchange_clients[exchange_name]
                except:
                    pass

    async def cleanup(self):
        """Clean up all exchange connections."""
        for exchange_name, exchange in self._exchange_clients.items():
            try:
                await exchange.close()
            except:
                pass
        self._exchange_clients.clear()