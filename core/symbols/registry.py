"""
Symbol Registry - Centralized symbol definitions for all formats

This registry contains all supported trading pairs across different systems:
- ggShot: BTCUSDT (no separator) 
- CCXT: BTC/USDT (slash separator)
- Hummingbot: BTC-USDT (dash separator)
- Platform: BTC-USDT (standardized format)
"""

from typing import Dict, List, Optional

# Base symbol registry - built from 141 ggShot symbols
SYMBOL_REGISTRY = {
    # Major cryptocurrencies
    "1inch": {
        "base": "1INCH",
        "quote": "USDT",
        "ggshot": "1INCHUSDT",
        "ccxt": "1INCH/USDT",
        "hummingbot": "1INCH-USDT",
        "platform": "1INCH-USDT",
        "coingecko_id": "1inch"
    },
    "aave": {
        "base": "AAVE", 
        "quote": "USDT",
        "ggshot": "AAVEUSDT",
        "ccxt": "AAVE/USDT",
        "hummingbot": "AAVE-USDT",
        "platform": "AAVE-USDT",
        "coingecko_id": "aave"
    },
    "ach": {
        "base": "ACH",
        "quote": "USDT", 
        "ggshot": "ACHUSDT",
        "ccxt": "ACH/USDT",
        "hummingbot": "ACH-USDT",
        "platform": "ACH-USDT",
        "coingecko_id": "alchemy-pay"
    },
    "ada": {
        "base": "ADA",
        "quote": "USDT",
        "ggshot": "ADAUSDT", 
        "ccxt": "ADA/USDT",
        "hummingbot": "ADA-USDT",
        "platform": "ADA-USDT",
        "coingecko_id": "cardano"
    },
    "algo": {
        "base": "ALGO",
        "quote": "USDT",
        "ggshot": "ALGOUSDT",
        "ccxt": "ALGO/USDT", 
        "hummingbot": "ALGO-USDT",
        "platform": "ALGO-USDT",
        "coingecko_id": "algorand"
    },
    "alice": {
        "base": "ALICE",
        "quote": "USDT",
        "ggshot": "ALICEUSDT",
        "ccxt": "ALICE/USDT",
        "hummingbot": "ALICE-USDT",
        "platform": "ALICE-USDT",
        "coingecko_id": "my-neighbor-alice"
    },
    "alpha": {
        "base": "ALPHA",
        "quote": "USDT",
        "ggshot": "ALPHAUSDT",
        "ccxt": "ALPHA/USDT",
        "hummingbot": "ALPHA-USDT", 
        "platform": "ALPHA-USDT",
        "coingecko_id": "alpha-finance"
    },
    "alt": {
        "base": "ALT",
        "quote": "USDT",
        "ggshot": "ALTUSDT",
        "ccxt": "ALT/USDT",
        "hummingbot": "ALT-USDT",
        "platform": "ALT-USDT",
        "coingecko_id": "altlayer"
    },
    "ankr": {
        "base": "ANKR",
        "quote": "USDT",
        "ggshot": "ANKRUSDT",
        "ccxt": "ANKR/USDT",
        "hummingbot": "ANKR-USDT",
        "platform": "ANKR-USDT",
        "coingecko_id": "ankr"
    },
    "ape": {
        "base": "APE", 
        "quote": "USDT",
        "ggshot": "APEUSDT",
        "ccxt": "APE/USDT",
        "hummingbot": "APE-USDT",
        "platform": "APE-USDT",
        "coingecko_id": "apecoin"
    },
    "api3": {
        "base": "API3",
        "quote": "USDT",
        "ggshot": "API3USDT",
        "ccxt": "API3/USDT",
        "hummingbot": "API3-USDT",
        "platform": "API3-USDT",
        "coingecko_id": "api3"
    },
    "apt": {
        "base": "APT",
        "quote": "USDT",
        "ggshot": "APTUSDT",
        "ccxt": "APT/USDT",
        "hummingbot": "APT-USDT",
        "platform": "APT-USDT",
        "coingecko_id": "aptos"
    },
    "arb": {
        "base": "ARB",
        "quote": "USDT",
        "ggshot": "ARBUSDT",
        "ccxt": "ARB/USDT",
        "hummingbot": "ARB-USDT",
        "platform": "ARB-USDT",
        "coingecko_id": "arbitrum"
    },
    "arkm": {
        "base": "ARKM",
        "quote": "USDT",
        "ggshot": "ARKMUSDT",
        "ccxt": "ARKM/USDT",
        "hummingbot": "ARKM-USDT",
        "platform": "ARKM-USDT",
        "coingecko_id": "arkham"
    },
    "ar": {
        "base": "AR",
        "quote": "USDT",
        "ggshot": "ARUSDT", 
        "ccxt": "AR/USDT",
        "hummingbot": "AR-USDT",
        "platform": "AR-USDT",
        "coingecko_id": "arweave"
    },
    "astr": {
        "base": "ASTR",
        "quote": "USDT",
        "ggshot": "ASTRUSDT",
        "ccxt": "ASTR/USDT",
        "hummingbot": "ASTR-USDT",
        "platform": "ASTR-USDT",
        "coingecko_id": "astar"
    },
    "atom": {
        "base": "ATOM",
        "quote": "USDT",
        "ggshot": "ATOMUSDT",
        "ccxt": "ATOM/USDT",
        "hummingbot": "ATOM-USDT",
        "platform": "ATOM-USDT",
        "coingecko_id": "cosmos"
    },
    "auction": {
        "base": "AUCTION",
        "quote": "USDT",
        "ggshot": "AUCTIONUSDT",
        "ccxt": "AUCTION/USDT",
        "hummingbot": "AUCTION-USDT",
        "platform": "AUCTION-USDT",
        "coingecko_id": "bounce-finance-governance-token"
    },
    "avax": {
        "base": "AVAX",
        "quote": "USDT",
        "ggshot": "AVAXUSDT",
        "ccxt": "AVAX/USDT",
        "hummingbot": "AVAX-USDT",
        "platform": "AVAX-USDT",
        "coingecko_id": "avalanche-2"
    },
    "axs": {
        "base": "AXS",
        "quote": "USDT",
        "ggshot": "AXSUSDT",
        "ccxt": "AXS/USDT",
        "hummingbot": "AXS-USDT",
        "platform": "AXS-USDT",
        "coingecko_id": "axie-infinity"
    },
    "bake": {
        "base": "BAKE",
        "quote": "USDT",
        "ggshot": "BAKEUSDT",
        "ccxt": "BAKE/USDT",
        "hummingbot": "BAKE-USDT",
        "platform": "BAKE-USDT", 
        "coingecko_id": "bakerytoken"
    },
    "bal": {
        "base": "BAL",
        "quote": "USDT",
        "ggshot": "BALUSDT",
        "ccxt": "BAL/USDT",
        "hummingbot": "BAL-USDT",
        "platform": "BAL-USDT",
        "coingecko_id": "balancer"
    },
    "band": {
        "base": "BAND",
        "quote": "USDT",
        "ggshot": "BANDUSDT",
        "ccxt": "BAND/USDT", 
        "hummingbot": "BAND-USDT",
        "platform": "BAND-USDT",
        "coingecko_id": "band-protocol"
    },
    "bat": {
        "base": "BAT",
        "quote": "USDT",
        "ggshot": "BATUSDT",
        "ccxt": "BAT/USDT",
        "hummingbot": "BAT-USDT",
        "platform": "BAT-USDT",
        "coingecko_id": "basic-attention-token"
    },
    "bch": {
        "base": "BCH",
        "quote": "USDT",
        "ggshot": "BCHUSDT",
        "ccxt": "BCH/USDT",
        "hummingbot": "BCH-USDT",
        "platform": "BCH-USDT",
        "coingecko_id": "bitcoin-cash"
    },
    "bel": {
        "base": "BEL",
        "quote": "USDT", 
        "ggshot": "BELUSDT",
        "ccxt": "BEL/USDT",
        "hummingbot": "BEL-USDT",
        "platform": "BEL-USDT",
        "coingecko_id": "bella-protocol"
    },
    "bigtime": {
        "base": "BIGTIME",
        "quote": "USDT",
        "ggshot": "BIGTIMEUSDT",
        "ccxt": "BIGTIME/USDT",
        "hummingbot": "BIGTIME-USDT",
        "platform": "BIGTIME-USDT",
        "coingecko_id": "big-time"
    },
    "bnb": {
        "base": "BNB",
        "quote": "USDT",
        "ggshot": "BNBUSDT",
        "ccxt": "BNB/USDT",
        "hummingbot": "BNB-USDT",
        "platform": "BNB-USDT",
        "coingecko_id": "binancecoin"
    },
    "bnt": {
        "base": "BNT",
        "quote": "USDT",
        "ggshot": "BNTUSDT",
        "ccxt": "BNT/USDT",
        "hummingbot": "BNT-USDT",
        "platform": "BNT-USDT",
        "coingecko_id": "bancor"
    },
    "bome": {
        "base": "BOME",
        "quote": "USDT",
        "ggshot": "BOMEUSDT",
        "ccxt": "BOME/USDT",
        "hummingbot": "BOME-USDT",
        "platform": "BOME-USDT", 
        "coingecko_id": "book-of-meme"
    },
    "btc": {
        "base": "BTC",
        "quote": "USDT",
        "ggshot": "BTCUSDT",
        "ccxt": "BTC/USDT", 
        "hummingbot": "BTC-USDT",
        "platform": "BTC-USDT",
        "coingecko_id": "bitcoin"
    },
    "cake": {
        "base": "CAKE",
        "quote": "USDT",
        "ggshot": "CAKEUSDT",
        "ccxt": "CAKE/USDT",
        "hummingbot": "CAKE-USDT",
        "platform": "CAKE-USDT",
        "coingecko_id": "pancakeswap-token"
    },
    "celr": {
        "base": "CELR",
        "quote": "USDT",
        "ggshot": "CELRUSDT",
        "ccxt": "CELR/USDT",
        "hummingbot": "CELR-USDT",
        "platform": "CELR-USDT",
        "coingecko_id": "celer-network"
    },
    "cetus": {
        "base": "CETUS",
        "quote": "USDT",
        "ggshot": "CETUSUSDT",
        "ccxt": "CETUS/USDT",
        "hummingbot": "CETUS-USDT",
        "platform": "CETUS-USDT",
        "coingecko_id": "cetus-protocol"
    },
    "cfx": {
        "base": "CFX",
        "quote": "USDT",
        "ggshot": "CFXUSDT",
        "ccxt": "CFX/USDT",
        "hummingbot": "CFX-USDT",
        "platform": "CFX-USDT",
        "coingecko_id": "conflux-token"
    },
    "chr": {
        "base": "CHR", 
        "quote": "USDT",
        "ggshot": "CHRUSDT",
        "ccxt": "CHR/USDT",
        "hummingbot": "CHR-USDT",
        "platform": "CHR-USDT",
        "coingecko_id": "chromaway"
    },
    "chz": {
        "base": "CHZ",
        "quote": "USDT",
        "ggshot": "CHZUSDT",
        "ccxt": "CHZ/USDT",
        "hummingbot": "CHZ-USDT", 
        "platform": "CHZ-USDT",
        "coingecko_id": "chiliz"
    },
    "comp": {
        "base": "COMP",
        "quote": "USDT",
        "ggshot": "COMPUSDT",
        "ccxt": "COMP/USDT",
        "hummingbot": "COMP-USDT",
        "platform": "COMP-USDT",
        "coingecko_id": "compound-governance-token"
    },
    "coti": {
        "base": "COTI",
        "quote": "USDT",
        "ggshot": "COTIUSDT",
        "ccxt": "COTI/USDT",
        "hummingbot": "COTI-USDT",
        "platform": "COTI-USDT",
        "coingecko_id": "coti"
    },
    "crv": {
        "base": "CRV",
        "quote": "USDT",
        "ggshot": "CRVUSDT",
        "ccxt": "CRV/USDT",
        "hummingbot": "CRV-USDT",
        "platform": "CRV-USDT",
        "coingecko_id": "curve-dao-token"
    },
    "cyber": {
        "base": "CYBER",
        "quote": "USDT",
        "ggshot": "CYBERUSDT",
        "ccxt": "CYBER/USDT",
        "hummingbot": "CYBER-USDT",
        "platform": "CYBER-USDT",
        "coingecko_id": "cyberconnect"
    },
    "dash": {
        "base": "DASH", 
        "quote": "USDT",
        "ggshot": "DASHUSDT",
        "ccxt": "DASH/USDT",
        "hummingbot": "DASH-USDT",
        "platform": "DASH-USDT",
        "coingecko_id": "dash"
    },
    "doge": {
        "base": "DOGE",
        "quote": "USDT",
        "ggshot": "DOGEUSDT",
        "ccxt": "DOGE/USDT",
        "hummingbot": "DOGE-USDT",
        "platform": "DOGE-USDT",
        "coingecko_id": "dogecoin"
    },
    "dot": {
        "base": "DOT",
        "quote": "USDT",
        "ggshot": "DOTUSDT",
        "ccxt": "DOT/USDT",
        "hummingbot": "DOT-USDT",
        "platform": "DOT-USDT",
        "coingecko_id": "polkadot"
    },
    "dydx": {
        "base": "DYDX",
        "quote": "USDT",
        "ggshot": "DYDXUSDT",
        "ccxt": "DYDX/USDT",
        "hummingbot": "DYDX-USDT",
        "platform": "DYDX-USDT",
        "coingecko_id": "dydx"
    },
    "egld": {
        "base": "EGLD",
        "quote": "USDT",
        "ggshot": "EGLDUSDT",
        "ccxt": "EGLD/USDT", 
        "hummingbot": "EGLD-USDT",
        "platform": "EGLD-USDT",
        "coingecko_id": "elrond-erd-2"
    },
    "ena": {
        "base": "ENA",
        "quote": "USDT",
        "ggshot": "ENAUSDT",
        "ccxt": "ENA/USDT",
        "hummingbot": "ENA-USDT",
        "platform": "ENA-USDT",
        "coingecko_id": "ethena"
    },
    "ens": {
        "base": "ENS", 
        "quote": "USDT",
        "ggshot": "ENSUSDT",
        "ccxt": "ENS/USDT",
        "hummingbot": "ENS-USDT",
        "platform": "ENS-USDT",
        "coingecko_id": "ethereum-name-service"
    },
    "etc": {
        "base": "ETC",
        "quote": "USDT",
        "ggshot": "ETCUSDT",
        "ccxt": "ETC/USDT",
        "hummingbot": "ETC-USDT",
        "platform": "ETC-USDT",
        "coingecko_id": "ethereum-classic"
    },
    "eth": {
        "base": "ETH",
        "quote": "USDT",
        "ggshot": "ETHUSDT",
        "ccxt": "ETH/USDT",
        "hummingbot": "ETH-USDT",
        "platform": "ETH-USDT",
        "coingecko_id": "ethereum"
    },
    "ethfi": {
        "base": "ETHFI",
        "quote": "USDT",
        "ggshot": "ETHFIUSDT",
        "ccxt": "ETHFI/USDT",
        "hummingbot": "ETHFI-USDT",
        "platform": "ETHFI-USDT",
        "coingecko_id": "ether-fi"
    },
    "fet": {
        "base": "FET",
        "quote": "USDT",
        "ggshot": "FETUSDT", 
        "ccxt": "FET/USDT",
        "hummingbot": "FET-USDT",
        "platform": "FET-USDT",
        "coingecko_id": "fetch-ai"
    },
    "fil": {
        "base": "FIL",
        "quote": "USDT",
        "ggshot": "FILUSDT",
        "ccxt": "FIL/USDT",
        "hummingbot": "FIL-USDT",
        "platform": "FIL-USDT",
        "coingecko_id": "filecoin"
    },
    "flm": {
        "base": "FLM",
        "quote": "USDT",
        "ggshot": "FLMUSDT",
        "ccxt": "FLM/USDT",
        "hummingbot": "FLM-USDT",
        "platform": "FLM-USDT",
        "coingecko_id": "flamingo-finance"
    },
    "flow": {
        "base": "FLOW",
        "quote": "USDT",
        "ggshot": "FLOWUSDT",
        "ccxt": "FLOW/USDT",
        "hummingbot": "FLOW-USDT",
        "platform": "FLOW-USDT",
        "coingecko_id": "flow"
    },
    "gala": {
        "base": "GALA",
        "quote": "USDT",
        "ggshot": "GALAUSDT",
        "ccxt": "GALA/USDT",
        "hummingbot": "GALA-USDT",
        "platform": "GALA-USDT",
        "coingecko_id": "gala"
    },
    "gmt": {
        "base": "GMT",
        "quote": "USDT", 
        "ggshot": "GMTUSDT",
        "ccxt": "GMT/USDT",
        "hummingbot": "GMT-USDT",
        "platform": "GMT-USDT",
        "coingecko_id": "stepn"
    },
    "gmx": {
        "base": "GMX",
        "quote": "USDT",
        "ggshot": "GMXUSDT",
        "ccxt": "GMX/USDT",
        "hummingbot": "GMX-USDT",
        "platform": "GMX-USDT",
        "coingecko_id": "gmx"
    },
    "grt": {
        "base": "GRT",
        "quote": "USDT",
        "ggshot": "GRTUSDT",
        "ccxt": "GRT/USDT",
        "hummingbot": "GRT-USDT",
        "platform": "GRT-USDT",
        "coingecko_id": "the-graph"
    },
    "gtc": {
        "base": "GTC",
        "quote": "USDT",
        "ggshot": "GTCUSDT",
        "ccxt": "GTC/USDT",
        "hummingbot": "GTC-USDT",
        "platform": "GTC-USDT",
        "coingecko_id": "gitcoin"
    },
    "hbar": {
        "base": "HBAR",
        "quote": "USDT",
        "ggshot": "HBARUSDT",
        "ccxt": "HBAR/USDT",
        "hummingbot": "HBAR-USDT",
        "platform": "HBAR-USDT",
        "coingecko_id": "hedera-hashgraph"
    },
    "high": {
        "base": "HIGH",
        "quote": "USDT",
        "ggshot": "HIGHUSDT",
        "ccxt": "HIGH/USDT",
        "hummingbot": "HIGH-USDT",
        "platform": "HIGH-USDT",
        "coingecko_id": "highstreet"
    },
    "hook": {
        "base": "HOOK",
        "quote": "USDT",
        "ggshot": "HOOKUSDT", 
        "ccxt": "HOOK/USDT",
        "hummingbot": "HOOK-USDT",
        "platform": "HOOK-USDT",
        "coingecko_id": "hooked-protocol"
    },
    "icp": {
        "base": "ICP",
        "quote": "USDT",
        "ggshot": "ICPUSDT",
        "ccxt": "ICP/USDT",
        "hummingbot": "ICP-USDT",
        "platform": "ICP-USDT",
        "coingecko_id": "internet-computer"
    },
    "icx": {
        "base": "ICX",
        "quote": "USDT",
        "ggshot": "ICXUSDT",
        "ccxt": "ICX/USDT",
        "hummingbot": "ICX-USDT",
        "platform": "ICX-USDT",
        "coingecko_id": "icon"
    },
    "id": {
        "base": "ID",
        "quote": "USDT",
        "ggshot": "IDUSDT",
        "ccxt": "ID/USDT",
        "hummingbot": "ID-USDT",
        "platform": "ID-USDT",
        "coingecko_id": "space-id"
    },
    "inj": {
        "base": "INJ",
        "quote": "USDT",
        "ggshot": "INJUSDT",
        "ccxt": "INJ/USDT",
        "hummingbot": "INJ-USDT",
        "platform": "INJ-USDT",
        "coingecko_id": "injective-protocol"
    },
    "iost": {
        "base": "IOST",
        "quote": "USDT",
        "ggshot": "IOSTUSDT", 
        "ccxt": "IOST/USDT",
        "hummingbot": "IOST-USDT",
        "platform": "IOST-USDT",
        "coingecko_id": "iostoken"
    },
    "iotx": {
        "base": "IOTX",
        "quote": "USDT",
        "ggshot": "IOTXUSDT",
        "ccxt": "IOTX/USDT",
        "hummingbot": "IOTX-USDT",
        "platform": "IOTX-USDT",
        "coingecko_id": "iotex"
    },
    "jasmy": {
        "base": "JASMY",
        "quote": "USDT",
        "ggshot": "JASMYUSDT",
        "ccxt": "JASMY/USDT",
        "hummingbot": "JASMY-USDT",
        "platform": "JASMY-USDT",
        "coingecko_id": "jasmycoin"
    },
    "jto": {
        "base": "JTO",
        "quote": "USDT",
        "ggshot": "JTOUSDT",
        "ccxt": "JTO/USDT",
        "hummingbot": "JTO-USDT",
        "platform": "JTO-USDT",
        "coingecko_id": "jito-governance-token"
    },
    "jup": {
        "base": "JUP",
        "quote": "USDT",
        "ggshot": "JUPUSDT",
        "ccxt": "JUP/USDT",
        "hummingbot": "JUP-USDT",
        "platform": "JUP-USDT",
        "coingecko_id": "jupiter-exchange-solana"
    },
    "kava": {
        "base": "KAVA",
        "quote": "USDT",
        "ggshot": "KAVAUSDT",
        "ccxt": "KAVA/USDT",
        "hummingbot": "KAVA-USDT",
        "platform": "KAVA-USDT",
        "coingecko_id": "kava"
    },
    "knc": {
        "base": "KNC",
        "quote": "USDT",
        "ggshot": "KNCUSDT",
        "ccxt": "KNC/USDT",
        "hummingbot": "KNC-USDT",
        "platform": "KNC-USDT",
        "coingecko_id": "kyber-network-crystal"
    },
    "ksm": {
        "base": "KSM",
        "quote": "USDT",
        "ggshot": "KSMUSDT",
        "ccxt": "KSM/USDT",
        "hummingbot": "KSM-USDT",
        "platform": "KSM-USDT",
        "coingecko_id": "kusama"
    },
    "ldo": {
        "base": "LDO",
        "quote": "USDT",
        "ggshot": "LDOUSDT",
        "ccxt": "LDO/USDT",
        "hummingbot": "LDO-USDT",
        "platform": "LDO-USDT",
        "coingecko_id": "lido-dao"
    },
    "lever": {
        "base": "LEVER",
        "quote": "USDT",
        "ggshot": "LEVERUSDT", 
        "ccxt": "LEVER/USDT",
        "hummingbot": "LEVER-USDT",
        "platform": "LEVER-USDT",
        "coingecko_id": "leverfi"
    },
    "link": {
        "base": "LINK",
        "quote": "USDT",
        "ggshot": "LINKUSDT",
        "ccxt": "LINK/USDT",
        "hummingbot": "LINK-USDT",
        "platform": "LINK-USDT",
        "coingecko_id": "chainlink"
    },
    "lpt": {
        "base": "LPT",
        "quote": "USDT",
        "ggshot": "LPTUSDT",
        "ccxt": "LPT/USDT",
        "hummingbot": "LPT-USDT",
        "platform": "LPT-USDT",
        "coingecko_id": "livepeer"
    },
    "lqty": {
        "base": "LQTY",
        "quote": "USDT",
        "ggshot": "LQTYUSDT",
        "ccxt": "LQTY/USDT",
        "hummingbot": "LQTY-USDT",
        "platform": "LQTY-USDT",
        "coingecko_id": "liquity"
    },
    "lrc": {
        "base": "LRC",
        "quote": "USDT",
        "ggshot": "LRCUSDT",
        "ccxt": "LRC/USDT",
        "hummingbot": "LRC-USDT",
        "platform": "LRC-USDT",
        "coingecko_id": "loopring"
    },
    "ltc": {
        "base": "LTC",
        "quote": "USDT",
        "ggshot": "LTCUSDT",
        "ccxt": "LTC/USDT",
        "hummingbot": "LTC-USDT",
        "platform": "LTC-USDT",
        "coingecko_id": "litecoin"
    },
    "magic": {
        "base": "MAGIC",
        "quote": "USDT",
        "ggshot": "MAGICUSDT",
        "ccxt": "MAGIC/USDT",
        "hummingbot": "MAGIC-USDT",
        "platform": "MAGIC-USDT",
        "coingecko_id": "magic"
    },
    "mana": {
        "base": "MANA",
        "quote": "USDT",
        "ggshot": "MANAUSDT",
        "ccxt": "MANA/USDT",
        "hummingbot": "MANA-USDT",
        "platform": "MANA-USDT",
        "coingecko_id": "decentraland"
    },
    "mask": {
        "base": "MASK",
        "quote": "USDT",
        "ggshot": "MASKUSDT",
        "ccxt": "MASK/USDT",
        "hummingbot": "MASK-USDT",
        "platform": "MASK-USDT",
        "coingecko_id": "mask-network"
    },
    "matic": {
        "base": "MATIC",
        "quote": "USDT",
        "ggshot": "MATICUSDT",
        "ccxt": "MATIC/USDT",
        "hummingbot": "MATIC-USDT",
        "platform": "MATIC-USDT",
        "coingecko_id": "matic-network"
    },
    "mkr": {
        "base": "MKR",
        "quote": "USDT",
        "ggshot": "MKRUSDT",
        "ccxt": "MKR/USDT",
        "hummingbot": "MKR-USDT",
        "platform": "MKR-USDT",
        "coingecko_id": "maker"
    },
    "near": {
        "base": "NEAR",
        "quote": "USDT",
        "ggshot": "NEARUSDT",
        "ccxt": "NEAR/USDT",
        "hummingbot": "NEAR-USDT", 
        "platform": "NEAR-USDT",
        "coingecko_id": "near"
    },
    "neo": {
        "base": "NEO",
        "quote": "USDT",
        "ggshot": "NEOUSDT",
        "ccxt": "NEO/USDT",
        "hummingbot": "NEO-USDT",
        "platform": "NEO-USDT",
        "coingecko_id": "neo"
    },
    "nkn": {
        "base": "NKN",
        "quote": "USDT",
        "ggshot": "NKNUSDT",
        "ccxt": "NKN/USDT", 
        "hummingbot": "NKN-USDT",
        "platform": "NKN-USDT",
        "coingecko_id": "nkn"
    },
    "nmr": {
        "base": "NMR",
        "quote": "USDT",
        "ggshot": "NMRUSDT",
        "ccxt": "NMR/USDT",
        "hummingbot": "NMR-USDT",
        "platform": "NMR-USDT",
        "coingecko_id": "numeraire"
    },
    "not": {
        "base": "NOT",
        "quote": "USDT",
        "ggshot": "NOTUSDT",
        "ccxt": "NOT/USDT",
        "hummingbot": "NOT-USDT",
        "platform": "NOT-USDT",
        "coingecko_id": "notcoin"
    },
    "ntrn": {
        "base": "NTRN",
        "quote": "USDT",
        "ggshot": "NTRNUSDT",
        "ccxt": "NTRN/USDT",
        "hummingbot": "NTRN-USDT",
        "platform": "NTRN-USDT",
        "coingecko_id": "neutron-3"
    },
    "ogn": {
        "base": "OGN",
        "quote": "USDT",
        "ggshot": "OGNUSDT",
        "ccxt": "OGN/USDT",
        "hummingbot": "OGN-USDT",
        "platform": "OGN-USDT",
        "coingecko_id": "origin-protocol"
    },
    "ondo": {
        "base": "ONDO",
        "quote": "USDT",
        "ggshot": "ONDOUSDT",
        "ccxt": "ONDO/USDT",
        "hummingbot": "ONDO-USDT",
        "platform": "ONDO-USDT",
        "coingecko_id": "ondo-finance"
    },
    "one": {
        "base": "ONE",
        "quote": "USDT",
        "ggshot": "ONEUSDT", 
        "ccxt": "ONE/USDT",
        "hummingbot": "ONE-USDT",
        "platform": "ONE-USDT",
        "coingecko_id": "harmony"
    },
    "ont": {
        "base": "ONT",
        "quote": "USDT",
        "ggshot": "ONTUSDT",
        "ccxt": "ONT/USDT",
        "hummingbot": "ONT-USDT",
        "platform": "ONT-USDT",
        "coingecko_id": "ontology"
    },
    "op": {
        "base": "OP",
        "quote": "USDT",
        "ggshot": "OPUSDT",
        "ccxt": "OP/USDT",
        "hummingbot": "OP-USDT",
        "platform": "OP-USDT",
        "coingecko_id": "optimism"
    },
    "ordi": {
        "base": "ORDI",
        "quote": "USDT",
        "ggshot": "ORDIUSDT",
        "ccxt": "ORDI/USDT",
        "hummingbot": "ORDI-USDT",
        "platform": "ORDI-USDT",
        "coingecko_id": "ordi"
    },
    "pendle": {
        "base": "PENDLE",
        "quote": "USDT",
        "ggshot": "PENDLEUSDT",
        "ccxt": "PENDLE/USDT",
        "hummingbot": "PENDLE-USDT",
        "platform": "PENDLE-USDT",
        "coingecko_id": "pendle"
    },
    "people": {
        "base": "PEOPLE",
        "quote": "USDT",
        "ggshot": "PEOPLEUSDT",
        "ccxt": "PEOPLE/USDT",
        "hummingbot": "PEOPLE-USDT",
        "platform": "PEOPLE-USDT",
        "coingecko_id": "constitutiondao"
    },
    "pyth": {
        "base": "PYTH",
        "quote": "USDT",
        "ggshot": "PYTHUSDT", 
        "ccxt": "PYTH/USDT",
        "hummingbot": "PYTH-USDT",
        "platform": "PYTH-USDT",
        "coingecko_id": "pyth-network"
    },
    "qtum": {
        "base": "QTUM",
        "quote": "USDT",
        "ggshot": "QTUMUSDT",
        "ccxt": "QTUM/USDT",
        "hummingbot": "QTUM-USDT",
        "platform": "QTUM-USDT",
        "coingecko_id": "qtum"
    },
    "rare": {
        "base": "RARE",
        "quote": "USDT",
        "ggshot": "RAREUSDT",
        "ccxt": "RARE/USDT",
        "hummingbot": "RARE-USDT",
        "platform": "RARE-USDT",
        "coingecko_id": "superrare"
    },
    "render": {
        "base": "RENDER",
        "quote": "USDT",
        "ggshot": "RENDERUSDT",
        "ccxt": "RENDER/USDT",
        "hummingbot": "RENDER-USDT",
        "platform": "RENDER-USDT",
        "coingecko_id": "render-token"
    },
    "rlc": {
        "base": "RLC",
        "quote": "USDT",
        "ggshot": "RLCUSDT",
        "ccxt": "RLC/USDT",
        "hummingbot": "RLC-USDT",
        "platform": "RLC-USDT",
        "coingecko_id": "iexec-rlc"
    },
    "rose": {
        "base": "ROSE",
        "quote": "USDT",
        "ggshot": "ROSEUSDT",
        "ccxt": "ROSE/USDT",
        "hummingbot": "ROSE-USDT",
        "platform": "ROSE-USDT",
        "coingecko_id": "oasis-network"
    },
    "rsr": {
        "base": "RSR",
        "quote": "USDT",
        "ggshot": "RSRUSDT",
        "ccxt": "RSR/USDT",
        "hummingbot": "RSR-USDT",
        "platform": "RSR-USDT",
        "coingecko_id": "reserve-rights-token"
    },
    "rune": {
        "base": "RUNE",
        "quote": "USDT",
        "ggshot": "RUNEUSDT",
        "ccxt": "RUNE/USDT",
        "hummingbot": "RUNE-USDT",
        "platform": "RUNE-USDT",
        "coingecko_id": "thorchain"
    },
    "rvn": {
        "base": "RVN",
        "quote": "USDT",
        "ggshot": "RVNUSDT",
        "ccxt": "RVN/USDT",
        "hummingbot": "RVN-USDT",
        "platform": "RVN-USDT",
        "coingecko_id": "ravencoin"
    },
    "sand": {
        "base": "SAND",
        "quote": "USDT",
        "ggshot": "SANDUSDT", 
        "ccxt": "SAND/USDT",
        "hummingbot": "SAND-USDT",
        "platform": "SAND-USDT",
        "coingecko_id": "the-sandbox"
    },
    "sei": {
        "base": "SEI",
        "quote": "USDT",
        "ggshot": "SEIUSDT",
        "ccxt": "SEI/USDT",
        "hummingbot": "SEI-USDT",
        "platform": "SEI-USDT",
        "coingecko_id": "sei-network"
    },
    "sfp": {
        "base": "SFP",
        "quote": "USDT",
        "ggshot": "SFPUSDT",
        "ccxt": "SFP/USDT",
        "hummingbot": "SFP-USDT",
        "platform": "SFP-USDT",
        "coingecko_id": "safemoon"
    },
    "sklus": {
        "base": "SKLUS",
        "quote": "USDT",
        "ggshot": "SKLUSUSDT",
        "ccxt": "SKLUS/USDT",
        "hummingbot": "SKLUS-USDT",
        "platform": "SKLUS-USDT",
        "coingecko_id": "skl"
    },
    "skl": {
        "base": "SKL",
        "quote": "USDT",
        "ggshot": "SKLUSDT",
        "ccxt": "SKL/USDT",
        "hummingbot": "SKL-USDT",
        "platform": "SKL-USDT",
        "coingecko_id": "skale"
    },
    "snx": {
        "base": "SNX",
        "quote": "USDT",
        "ggshot": "SNXUSDT",
        "ccxt": "SNX/USDT",
        "hummingbot": "SNX-USDT",
        "platform": "SNX-USDT",
        "coingecko_id": "havven"
    },
    "sol": {
        "base": "SOL",
        "quote": "USDT",
        "ggshot": "SOLUSDT",
        "ccxt": "SOL/USDT",
        "hummingbot": "SOL-USDT",
        "platform": "SOL-USDT",
        "coingecko_id": "solana"
    },
    "storj": {
        "base": "STORJ",
        "quote": "USDT",
        "ggshot": "STORJUSDT",
        "ccxt": "STORJ/USDT",
        "hummingbot": "STORJ-USDT",
        "platform": "STORJ-USDT",
        "coingecko_id": "storj"
    },
    "strk": {
        "base": "STRK",
        "quote": "USDT",
        "ggshot": "STRKUSDT",
        "ccxt": "STRK/USDT",
        "hummingbot": "STRK-USDT",
        "platform": "STRK-USDT",
        "coingecko_id": "starknet"
    },
    "stx": {
        "base": "STX",
        "quote": "USDT",
        "ggshot": "STXUSDT",
        "ccxt": "STX/USDT",
        "hummingbot": "STX-USDT",
        "platform": "STX-USDT",
        "coingecko_id": "blockstack"
    },
    "sui": {
        "base": "SUI",
        "quote": "USDT",
        "ggshot": "SUIUSDT",
        "ccxt": "SUI/USDT",
        "hummingbot": "SUI-USDT",
        "platform": "SUI-USDT",
        "coingecko_id": "sui"
    },
    "s": {
        "base": "S",
        "quote": "USDT",
        "ggshot": "SUSDT",
        "ccxt": "S/USDT",
        "hummingbot": "S-USDT",
        "platform": "S-USDT",
        "coingecko_id": "s"
    },
    "sushi": {
        "base": "SUSHI",
        "quote": "USDT",
        "ggshot": "SUSHIUSDT",
        "ccxt": "SUSHI/USDT",
        "hummingbot": "SUSHI-USDT",
        "platform": "SUSHI-USDT",
        "coingecko_id": "sushi"
    },
    "sxp": {
        "base": "SXP",
        "quote": "USDT",
        "ggshot": "SXPUSDT",
        "ccxt": "SXP/USDT",
        "hummingbot": "SXP-USDT",
        "platform": "SXP-USDT",
        "coingecko_id": "swipe"
    },
    "tao": {
        "base": "TAO",
        "quote": "USDT",
        "ggshot": "TAOUSDT",
        "ccxt": "TAO/USDT",
        "hummingbot": "TAO-USDT",
        "platform": "TAO-USDT",
        "coingecko_id": "bittensor"
    },
    "theta": {
        "base": "THETA",
        "quote": "USDT",
        "ggshot": "THETAUSDT",
        "ccxt": "THETA/USDT",
        "hummingbot": "THETA-USDT",
        "platform": "THETA-USDT",
        "coingecko_id": "theta-token"
    },
    "tia": {
        "base": "TIA",
        "quote": "USDT",
        "ggshot": "TIAUSDT",
        "ccxt": "TIA/USDT",
        "hummingbot": "TIA-USDT",
        "platform": "TIA-USDT",
        "coingecko_id": "celestia"
    },
    "trb": {
        "base": "TRB",
        "quote": "USDT",
        "ggshot": "TRBUSDT",
        "ccxt": "TRB/USDT",
        "hummingbot": "TRB-USDT",
        "platform": "TRB-USDT",
        "coingecko_id": "tellor"
    },
    "trx": {
        "base": "TRX",
        "quote": "USDT",
        "ggshot": "TRXUSDT",
        "ccxt": "TRX/USDT",
        "hummingbot": "TRX-USDT",
        "platform": "TRX-USDT",
        "coingecko_id": "tron"
    },
    "turbo": {
        "base": "TURBO",
        "quote": "USDT",
        "ggshot": "TURBOUSDT",
        "ccxt": "TURBO/USDT",
        "hummingbot": "TURBO-USDT",
        "platform": "TURBO-USDT",
        "coingecko_id": "turbo"
    },
    "twt": {
        "base": "TWT",
        "quote": "USDT",
        "ggshot": "TWTUSDT",
        "ccxt": "TWT/USDT",
        "hummingbot": "TWT-USDT",
        "platform": "TWT-USDT",
        "coingecko_id": "trust-wallet-token"
    },
    "vanry": {
        "base": "VANRY",
        "quote": "USDT",
        "ggshot": "VANRYUSDT",
        "ccxt": "VANRY/USDT",
        "hummingbot": "VANRY-USDT",
        "platform": "VANRY-USDT",
        "coingecko_id": "vanar-chain"
    },
    "vet": {
        "base": "VET",
        "quote": "USDT",
        "ggshot": "VETUSDT",
        "ccxt": "VET/USDT",
        "hummingbot": "VET-USDT",
        "platform": "VET-USDT",
        "coingecko_id": "vechain"
    },
    "wif": {
        "base": "WIF",
        "quote": "USDT",
        "ggshot": "WIFUSDT",
        "ccxt": "WIF/USDT",
        "hummingbot": "WIF-USDT",
        "platform": "WIF-USDT",
        "coingecko_id": "dogwifcoin"
    },
    "wld": {
        "base": "WLD",
        "quote": "USDT",
        "ggshot": "WLDUSDT",
        "ccxt": "WLD/USDT",
        "hummingbot": "WLD-USDT",
        "platform": "WLD-USDT",
        "coingecko_id": "worldcoin-wld"
    },
    "woo": {
        "base": "WOO",
        "quote": "USDT",
        "ggshot": "WOOUSDT",
        "ccxt": "WOO/USDT",
        "hummingbot": "WOO-USDT",
        "platform": "WOO-USDT",
        "coingecko_id": "woo-network"
    },
    "w": {
        "base": "W",
        "quote": "USDT",
        "ggshot": "WUSDT",
        "ccxt": "W/USDT",
        "hummingbot": "W-USDT",
        "platform": "W-USDT",
        "coingecko_id": "wormhole"
    },
    "xrp": {
        "base": "XRP",
        "quote": "USDT",
        "ggshot": "XRPUSDT",
        "ccxt": "XRP/USDT",
        "hummingbot": "XRP-USDT",
        "platform": "XRP-USDT",
        "coingecko_id": "ripple"
    },
    "yfi": {
        "base": "YFI",
        "quote": "USDT",
        "ggshot": "YFIUSDT",
        "ccxt": "YFI/USDT",
        "hummingbot": "YFI-USDT",
        "platform": "YFI-USDT",
        "coingecko_id": "yearn-finance"
    },
    "zil": {
        "base": "ZIL",
        "quote": "USDT",
        "ggshot": "ZILUSDT",
        "ccxt": "ZIL/USDT",
        "hummingbot": "ZIL-USDT",
        "platform": "ZIL-USDT",
        "coingecko_id": "zilliqa"
    },
    "zro": {
        "base": "ZRO",
        "quote": "USDT",
        "ggshot": "ZROUSDT",
        "ccxt": "ZRO/USDT",
        "hummingbot": "ZRO-USDT",
        "platform": "ZRO-USDT",
        "coingecko_id": "layerzero"
    },
    "zrx": {
        "base": "ZRX",
        "quote": "USDT",
        "ggshot": "ZRXUSDT",
        "ccxt": "ZRX/USDT",
        "hummingbot": "ZRX-USDT",
        "platform": "ZRX-USDT",
        "coingecko_id": "0x"
    }
}

def get_all_symbols() -> List[str]:
    """Get all supported symbol keys"""
    return list(SYMBOL_REGISTRY.keys())

def get_symbol_data(symbol_key: str) -> Optional[Dict[str, str]]:
    """Get all format data for a symbol key"""
    return SYMBOL_REGISTRY.get(symbol_key)

def find_symbol_by_format(symbol: str, format_type: str) -> Optional[str]:
    """Find symbol key by any format (ggshot, ccxt, hummingbot, etc.)"""
    for key, data in SYMBOL_REGISTRY.items():
        if data.get(format_type) == symbol:
            return key
    return None