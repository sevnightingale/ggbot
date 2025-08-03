Documentation
Hummingbot is an community-driven, open source Python framework for building automated market making and algorithmic trading bots, maintained by Hummingbot Foundation.

It is designed to be modular and extensible, allowing users to automate any trading strategy on any exchange and blockchain.

Getting Started¶
We recommend installing Hummingbot using Docker if you want the simplest, easiest installation method and don't need to modify the Hummingbot codebase. Check out Install via Docker for the basic process.

For Developers

If you're a developer looking to build custom strategies or exchange connectors, consider installing Hummingbot from source. There are instructions for macOS, Linux and Windows - see Source Installation.

Afterwards, check out the Academy category in the Hummingbot Blog for blog posts and step-by-step tutorials on how to use Hummingbot.

Strategies¶
A Hummingbot strategy automates an algorithmic trading strategy based on a configuration file, allowing the template containing the strategy logic to be defined publicly, while users can keep their configurations private.

As of the 2.0 release, the framework offers two ways to create Hummingbot strategies:

Scripts: Scripts are the entry point for all Hummingbot strategies. A script's on_tick method defines the actions taken each clock tick, and it provides access to core Hummingbot components like connectors. They can range in complexity from a simple Python file that contains all strategy logic to a launcher script launches multiple Controllers, each defining a separate sub-strategy.

Controllers: Controllers define a modularized strategy using components such as Executors, enabling backtesting and faciliates multi-bot deployment using Dashboard.

In the past, there were legacy strategy templates (V1 Strategies), the original Hummingbot strategies that are more rigid and less customizable than those built using the new Strategy V2 framework.

Connectors¶
Hummingbot connectors standardize trading logic and order types across different types of exchanges and blockchain networks, so that strategies can access standardized methods that work across all connectors of that type.

Each connector's code is contained in modularized folders in the Hummingbot and/or Gateway codebases:

CLOB Connectors: Connectors to central limit order book (CLOB) centralized and decentralized exchanges
AMM Connectors: Connectors to automated market maker (AMM) decentralized exchanges
Official Code Repositories¶
All Hummingbot Foundation code is maintained and stored in repositories in the official Github and DockerHub organization accounts. These are the only code repositories used to release official versions of Hummingbot. Please download Hummingbot and Hummingbot-related software from only these official sources.

The Hummingbot framework is comprised of multiple code repositories, hosted on the Hummingbot Foundation Github, that are maintained by the Foundation alongside individual community members. All code is open sourced under the Apache 2.0 or MIT licenses.

Hummingbot started as a command line interface (CLI) tool, and the Hummingbot Client is still the basic way to interact with the framework.

Today, the framework comprises companion modules to assist with other aspects of crypto algorithmic trading:

Gateway: Middleware to interact with AMM connectors and other DeFi protocols on various blockchains
Dashboard: A web-based user interface for deploying multi-bot trading strategies
Backend API: Backend API that exposes bot management endpoints for Dashboard and others to interact with
Quants-Lab: A sandbox for users to test their trading ideas and strategies
Getting Help¶
If you encounter issues or have questions, here’s how you can get assistance:

Consult our FAQ, Troubleshooting Guide, or Glossary.

To report bugs or suggest features, submit a Github issue.

Join our Discord community and ask questions in the #support channel.

We pledge that we will not use the information/data your provide us for trading purposes nor share them with third parties.




Hummingbot V2 + Dashboard¶
Hummingbot 2.0 now features a Dashboard GUI, replacing the traditional CLI for a more intuitive experience.

The recommended installation method, especially for new users, is Hummingbot + Dashboard, allowing you to easily create, backtest, and deploy strategies.

Other standalone installation options like Docker and Source are still available.

System Requirements¶
Cloud server or local machine¶
Component	Specifications
Operating System	Linux x64 or ARM (Ubuntu 20.04+, Debian 10+)
Memory	4 GB RAM per instance
Storage	5 GB HDD space per instance
CPU	at least 1 vCPU per instance / controller
Docker Compose¶
Hummingbot uses Docker Compose, a tool for defining and running multi-container Docker applications.


macOS
Linux
Windows
Install Docker Desktop from the official Docker website


Installation Steps¶
Hummingbot Deploy is a dedicated repo that allows users to quickly deploy Hummingbot using the Dashboard as the front end UI. The compose file spins up containers for the Dashboard, Backend-API as well as the Hummingbot Broker.


git clone https://github.com/hummingbot/deploy.git
cd deploy
bash setup.sh
The setup script will pull the Docker images defined in repo's docker-compose.yml file and start them as new containers:


[+] Running 7/7
 ✔ Network deploy_emqx-bridge   Created
 ✔ Volume "deploy_emqx-data"    Created
 ✔ Volume "deploy_emqx-log"     Created
 ✔ Volume "deploy_emqx-etc"     Created
 ✔ Container dashboard          Started 
 ✔ Container backend-api        Started 
 ✔ Container hummingbot-broker  Started 
After all containers have started, access the Dashboard at http://localhost:8501 in your browser.

Cloud Servers

If you are using a cloud server or VPS, replace localhost with the IP of your server. You may need to edit the firewall rules to allow inbound connections to the necessary ports.

Guides
This page serves as a comprehensive resource hub for learning about algorithmic trading with Hummingbot. With content for new crypto traders to advanced quant developers, you'll find step-by-step guides, Youtube videos, and other content to help you master crypto market making!

🚀 Quickstart Guides¶
Get started with Hummingbot using different interfaces and installation methods:

Hummingbot Dashboard Quickstart Guide
Learn how to install Hummingbot 2.0 and use the Dashboard app to connect exchange credentials, create/backtest strategy configurations, and deploy a fleet of bots

Hummingbot Docker Quickstart Guide
Step-by-step instructions to install and deploy Hummingbot using Docker, including setting up the interface and running your first algorithmic trading strategy.

Hummingbot API Quickstart Guide
Learn how to use the Hummingbot API to add exchange credentials, view portfolio balances, and place your first market order using Docker setup and Python API client examples.

🎓 Hummingbot Academy¶
Just getting started with crypto market making? Start your journey with these foundational articles about crypto algorithmic trading:

What is Market Making Deep dive into market making, one of the most popular algorithmic trading strategies

What is Cross Exchange Market Making?¶ Essential principles for managing risk in automated trading systems

Liquidity Mining in Hummingbot vs DeFi Comparison of liquidity mining approaches in Hummingbot versus traditional DeFi protocols, highlighting key differences and benefits

Take your skills to the next level in Hummingbot Botcamp, the official training and certification program for Hummingbot.

📺 YouTube Playlists¶
Watch and learn from our curated video content:

Introduction to Market Making Step-by-step video tutorials for market making with Hummingbot

Using Quants Lab to Conduct Research Learn how to use Hummingbot's Quants Lab for backtesting strategies, analyzing market data, and conducting quantitative research

Botcamp Member Stories Hear from real users who have successfully completed the Botcamp certification program

🔌 Connector Guides¶
Learn how to setup and run Hummingbot on various CEXs and DEXs:

Using Binance with Hummingbot Step-by-step guide to using Hummingbot with Binance, including generating exchange API keys and adding them to Hummingbot

Funding Rate Arbitrage and Creating Vaults on Hyperliquid Guide on using Hyperliquid Vaults as exchange wallets for individual traders or automated market makers

Running a Trading Bot with Hummingbot Dashboard on dYdX V4 Guide to integrating and trading on dYdX's perpetual contracts using Hummingbot Dashboard

Running a Trading Bot with Hummingbot on Derive Comprehensive resource for integrating and trading on Derive's decentralized derivatives platform using Hummingbot

Trading on XRPL with Hummingbot Guide to setting up and trading on the XRP Ledger's decentralized exchange using Hummingbot

See more examples in the Connector Guides category in our blog.

🧙 Strategy Guides¶
Enhance your trading strategies with advanced development guides:

How to configure a v2 strategy controller This guide walks you through configuring and running V2 strategy controllers in Hummingbot to automate and optimize your trading strategies.

Coding a Liquidation Sniper V2 Strategy Controller Explore how to create a custom V2 Controller for Hummingbot to snipe future liquidations on Binance

Directional Trading with MACD and Bollinger Bands Learn how to implement a directional trading strategy using MACD and Bollinger Bands technical indicators for trend identification and entry/exit signals

Technical Deep Dive into the Avellaneda & Stoikov Strategy Comprehensive analysis of the mathematical model behind the Avellaneda & Stoikov paper and how it's implemented in Hummingbot

Scripts
Scripts are the entry point for Hummingbot strategies. They enable Hummingbot users to build customized strategies using the Strategy V2 framework, and access the full power of Hummingbot exchange connectors in a few lines of Python code.

Note

Should your script run into an error, it's crucial that you exit Hummingbot entirely, correct or debug the faulty script, and then restart Hummingbot. The stop command won't rectify the issue in case of an error. To get back on track, a complete shutdown and subsequent relaunch of Hummingbot is required.

For more info, see the Script Walkthrough. This detailed walkthrough shows you how to run a simple directional algo trading strategy.

Script Examples¶
See Script Examples for a list of the current sample scripts in the Hummingbot codebase. These examples show you how to:

Execute V2 strategies
Download order book data
Download historical candles data
Place orders
Use the rate oracle
Call exchange APIs
And much more!
We welcome new sample script contributions from users! To submit a contribution, please follow the Contribution Guidelines.

Configuration Files¶
Scripts can be created both with and without config files.

To create a configuration file for your script, execute:


create --script-config [SCRIPT_FILE]
This command auto-completes with scripts from the local /scripts directory that are configurable. You'll be prompted to specify strategy parameters, which are then saved in a YAML file within the conf/scripts directory. To run the script, use:


start --script [SCRIPT_FILE] --conf [SCRIPT_CONFIG_FILE]
Auto-complete will suggest config files from the local /conf/scripts directory.

Base Classes¶
Scripts that use the Strategy V2 framework inherit from the StrategyV2Base class. These scripts allow the user to create a config file with parameters.

Other scripts, including simple examples and older scripts, inherit from the ScriptStrategyBase class. These scripts define their parameters in the script code and do not expose config parameters.

Script Architecture¶


The entry point for StrategyV2 is a Hummingbot script that inherits from the StrategyV2Base class.

This script fetches data from the Market Data Provider and manages how each Executor behaves. Optionally, it can load a Controller to manage the stategy logic instead of defining it in within the script. Go through the Walkthrough to learn how it works.

See Sample Scripts for more examples of StrategyV2-compatible scripts.

Adding Config Parameters¶
To add user-defined parameters to a StategyV2 script, add a configuration class that extends the StrategyV2ConfigBase class in StrategyV2Base class.

This defines a set of configuration parameters that are prompted to the user when they run create to generate the config file. Only questions marked prompt_on_new are displayed.

Afterwards, these parameters are stored in a config file. The script checks this config file every config_update_interval (default: 60 seconds) and updates the parameters that it uses in-flight.


class StrategyV2ConfigBase(BaseClientModel):
    """
    Base class for version 2 strategy configurations.
    """
    markets: Dict[str, Set[str]] = Field(
        default="binance_perpetual.JASMY-USDT,RLC-USDT",
        client_data=ClientFieldData(
            prompt_on_new=True,
            prompt=lambda mi: (
                "Enter markets in format 'exchange1.tp1,tp2:exchange2.tp1,tp2':"
            )
        )
    )
    candles_config: List[CandlesConfig] = Field(
        default="binance_perpetual.JASMY-USDT.1m.500:binance_perpetual.RLC-USDT.1m.500",
        client_data=ClientFieldData(
            prompt_on_new=True,
            prompt=lambda mi: (
                "Enter candle configs in format 'exchange1.tp1.interval1.max_records:"
                "exchange2.tp2.interval2.max_records':"
            )
        )
    )
    controllers_config: List[str] = Field(
        default=None,
        client_data=ClientFieldData(
            is_updatable=True,
            prompt_on_new=True,
            prompt=lambda mi: "Enter controller configurations (comma-separated file paths), leave it empty if none: "
        ))
    config_update_interval: int = Field(
        default=60,
        gt=0,
        client_data=ClientFieldData(
            prompt_on_new=False,
            prompt=lambda mi: "Enter the config update interval in seconds (e.g. 60): ",
        )
    )
on_tick Method¶
This method acts as the strategy's heartbeat, is called regularly, and allows the strategy to adapt to new market conditions in real time.


def on_tick(self):
    for executor_handler in self.executor_handlers.values():
        if executor_handler.status == ExecutorHandlerStatus.NOT_STARTED:
            executor_handler.start()
format_status Method¶
This overrides the standard status function and provides a formatted string representing the current status of the strategy, including the name, trading pair, and status of each executor.

Users can customize this function to display their custom strategy variables.


def format_status(self) -> str:
        if not self.ready_to_trade:
            return "Market connectors are not ready."
        lines = []
        for trading_pair, executor_handler in self.executor_handlers.items():
            lines.extend(
                [f"Strategy: {executor_handler.controller.config.strategy_name} | Trading Pair: {trading_pair}",
                 executor_handler.to_format_status()])
        return "\n".join(lines)


Scripts Cheatsheat
See below for reference docs that help you create Scripts that inherit from the ScriptStrategy base class.

This Script Strategies Cheatsheet is also available in PDF form.

Watch the full video that accompanies this page:


Getting started¶
Follow the Installation docs for your environment
Code your script inside the /scripts folder
Run your script with start --script [SCRIPT NAME]
Scripts basics¶
Configuration¶
Scripts are a subclass of ScriptStrategy.

You can define the variables that you will use as class variables. By default, there is no configuration file for scripts.

Markets¶
Define the connectors and trading pairs, in the class variable markets, with the following structure:


Dict["connector_name", Set(Trading pairs)]
Execution¶
The method on_tick is executed every tick_size
The tick_size by default is 1 second
Market Operations¶
Create and cancel Orders¶

self.buy(connector_name, trading_pair, amount, order_type, price, [position_action])
self.sell(connector_name, trading_pair, amount, order_type, price,[position_action])
self.cancel(connector_name, trading_pair, order_id)```
# position_action is only used in perpetual connectors
Account Data¶
Balance¶
self.get_balance_df()

Returns a DataFrame with the following columns: ["Exchange", "Asset", "Total Balance", "Available Balance"]
Open Orders¶
self.active_orders_df()

Returns a DataFrame with the following columns: ["Exchange", "Market", "Side", "Price", "Amount", "Age"]
Events¶
You can create custom handlers for various market events by implementing one or more of the following methods in your script:


did_create_buy_order(self, event: BuyOrderCreatedEvent)
did_create_sell_order(self, event: SellOrderCreatedEvent)
did_fill_order(self, event: OrderFilledEvent)
did_fail_order(self, event: MarketOrderFailureEvent)
did_cancel_order(self, event: OrderCancelledEvent)
did_expire_order(self, event: OrderExpiredEvent)
did_complete_buy_order(self, event: BuyOrderCompletedEvent)
did_complete_sell_order(self, event: SellOrderCompletedEvent)
Other¶
Rate Oracle¶
Provides conversion rates for any given pair token symbols in both async and sync fashions
Sync Method: RateOracle.get_instance().get_pair_rate(trading_pair)
Async Method: RateOracle.get_instance().rate_async(trading_pair)
Notifiers¶
To send notifications to the Hummingbot client, use the following methods:


self.notify_hb_app(msg)
self.notify_hb_app_with_timestamp(msg)
Tip

If you have the Telegram integration activated, you will receive the notifications there too.

Status¶
When you run the status command in the app, you will receive the information that is coded under the method format_status
You can override this method in your script to show any information that you want. Check out Quickstart - Exercise 3 for an example.
By default, the format status shows the balances and active orders. Check the implementation in ScriptStrategy.
Connectors¶
Accessing the Connectors¶
A connection is stored in the instance variable connectors with the following structure: Dict["connector_name", ConnectorBase]

For example, self.connectors["binance"] will return the Binance exchange class.

Connectors Methods¶
Best ask: connector.get_price(trading_pair, is_buy=True)
Best bid: connector.get_price(trading_pair, is_buy=False)
Mid-price: connector.get_mid_price(trading_pair)
Order book: connector.get_order_book(trading_pair). Returns a CompositeOrderBook object, whose most common methods are:
ask_entries() → Iterator of OrderBookRow
bid_entries() → Iterator of OrderBookRow
snapshot() → Tuple(Bids as DataFrame, Asks as DataFrame)
For example, self.connectors["binance"].get_mid_price("ETH-USDT") will return the mid price for the ETH-USDT trading pair on Binance.

Querying the Order Book¶
Use these methods to compute metrics efficiently:


connector.get_vwap_for_volume(trading_pair, is_buy, volume)
connector.get_price_for_volume(trading_pair, is_buy, volume)
connector.get_quote_volume_for_base_amount(trading_pair, is_buy, base_amount)
connector.get_volume_for_price(trading_pair, is_buy, price)
connector.get_quote_volume_for_price(trading_pair, is_buy,price)
Returns a ClientOrderBookQueryResult class with:

query_price
query_volume
result_price
result_volume
Accounting¶
Order Candidate¶
OrderCandidate(trading_pair, is_maker, order_type, order_side, amount, price)
Has methods to populate the object with the collateral needed, the fees, and potential returns
Budget Checker¶
This checks if the balance is enough to place the order, all_or_none=True will set the amount to 0 on insufficient balance and all_or_none=False will adjust the order size to the available balance.


connector.budget_checker.adjust_candidate(OrderCandidate, all_or_none=True)
connector.budget_checker.adjust_candidates(List[OrderCandidate], all_or_none=True)
July 22, 2025


Strategies V2
What is a Hummingbot Strategy?¶


Like a computer program, an algorithmic trading strategy is a set of automated processes that executes repeatedly:

Data Collection: Gathering real-time data from various sources
Data Processing: Analyzing data to identify patterns and make decisions
Order Execution: Placing and cancelling orders based on processed data
A Hummingbot strategy loads market data directly from centralized and decentralized exchanges, adaptable to the unique features of each trading venue's WebSocket/REST APIs and nodes.

Each clock tick, a strategy loads real-time order book snapshots, user balances, order status and other real-time data from trading pairs on these venues and executes the logic defined in the strategy, parametrized by a pre-defined user configuration.

To run a strategy, a user selects a strategy template, defines its input parameters in a Config File, and starts it with the start command in the Hummingbot client or via the command line with Strategy Autostart.

Strategies V2¶
Starting in 2023, Hummingbot Foundation began to iteratively introduce a new framework, called Strategy V2. The new framework allows you to build powerful, dynamic strategies using Lego-like components. To learn more, check out Architecture.

There are two current ways that Hummingbot strategies can be defined:

Scripts: A simple Python file that contains all strategy logic. We recommend starting with a script if you want a simple way to prototype your strategy.

Controllers: Strategy logic is abstracted into a Controller, which may use Executors and other components for greater modularization. Controllers can be backtested and deployed using Dashboard, and a single loader Script may deploy and manage multiple Controller configurations.

Controllers are designed to add another layer of abstraction and circumvent the limit of Hummingbot to only run one strategy per bot instance. You can think of that as the most powerful and advanced setup that Hummingbot currently provides.

This table may help you decide whether to use a Script or Controller for your strategy:

Script	Controller
The strategy is relatively simple	You want to manage the risk and diversify your portfolio in different controllers
The logic is very standard across different trading pairs	The strategy is complex and you want to isolate the decision making
The strategy only trades on one trading pair	You want to try multiple configs in the same bot
You are getting started with Executors and you want a simple way to code your strategy	The strategy trades on multiple trading pairs
Prototype a strategy	You are familiar with the Strategy V2 and how the controllers interact with it
Strategies V1¶
When it launched in 2019, Hummingbot pioneered the concept of configurable templates for algo trading strategies, such as market making strategies based on the Avellaneda & Stoikov paper.

Initially, these strategies were confined to individual bots, complicating the management and scaling across various scenarios, and they lacked the capability to use historical market data, which forced traders to rely solely on real-time data. Furthermore, technical barriers, such as a deep prerequisite knowledge of foundational classes and Cython, hindered easy access to market data, while limited backtesting tools restricted evaluations against historical data.

Users can access these strategy templates at the Strategies V1 page.

Learn Algo Trading and Market Making¶
To gain a deeper understanding of Hummingbot strategies along with access to the latest Hummingbot framework updates, check out Botcamp, the official training and certification for Hummingbot.

Operated by the people behind Hummingbot Foundation, Botcamp offers bootcamps and courses that teach you how to design and deploy advanced algo trading and market making strategies using Hummingbot's Strategy V2 framework.

Architecture
Components¶
The most important components to understand are:

Script: Entry point for all strategies, this Python file orchestrates the strategy. It may be a simple file that contains all strategy logic, or one that loads one or more Controllers.
Market Data Provider: Single point of access to exchange market data such as historical OHCLV Candles, order book data, and trades.
Executor: Manages orders and positions based on pre-defined user settings, ensuring that orders are placed, modified, or canceled according to the strategy's instructions.
Controller: Defines a trading strategy based on a strategy controller base class, i.e. Directional or Market Making.
Inheritance¶
One important information before we delve into the details of each strategy type and when to use which is to understand that they are all built on top of each other.

If we have a quick look together at the inheritance hierarchy this becomes obvious:



V1 Strategies: StrategyBase is the Cython base class for all strategies, while StrategyPyBase extends it and serves as the root for all Python-based strategies
V1 Scripts: ScriptStrategyBase builds on top of these classes and makes it a lot easier to create a simple strategy with nearly no code. This class is still fully supported, but might be deprecated in the future. Therefore we recommend using StrategyV2Base for new script implementations.
Controllers and V2 Scripts: StrategyV2Base inherits from ScriptStrategyBase, but uses Executors for order management instead of the buy() / sell() methods. Controllers extend that even further as additional components that are loosely couple via an event queue.
Please make sure to keep the inheritance structure in mind as this helps you a lot in learning how to code your own custom strategies.

Strategy Guides¶
Check out Walkthrough - Script and Walkthrough - Controller to learn how to create strategies.

Market Data Provider
The Market Data Provider service simplifies access to real-time market data with the following methods.

Any scripts can instantiate the Market Data Provider:


from hummingbot.data_feed.market_data_provider import MarketDataProvider
Below are a some methods that it contains. Each method receives the connector name, trading pair, and other arguments that can be defined as config parameters.

Price¶

    def get_price_by_type(self, connector_name: str, trading_pair: str, price_type: PriceType):
        """
        Retrieves the price for a trading pair from the specified connector.
        :param connector_name: str
        :param trading_pair: str
        :param price_type: str
        :return: Price instance.
        """
        connector = self.get_connector(connector_name)
        return connector.get_price_by_type(trading_pair, price_type)
Example:


price = self.market_data_provider.get_price_by_type('binance', 'BTC-USDT', PriceType.MidPrice)

    def get_price_for_volume(self, connector_name: str, trading_pair: str, volume: float,
                             is_buy: bool) -> OrderBookQueryResult:
        """
        Gets the price for a specified volume on the order book.

        :param connector_name: The name of the connector.
        :param trading_pair: The trading pair for which to retrieve the data.
        :param volume: The volume for which to find the price.
        :param is_buy: True if buying, False if selling.
        :return: OrderBookQueryResult containing the result of the query.
        """

        order_book = self.get_order_book(connector_name, trading_pair)
        return order_book.get_price_for_volume(is_buy, volume)
Example:


price = self.market_data_provider.get_price_by_volume('binance', 'BTC-USDT', volume: 10000, True)
Volume¶

    def get_volume_for_price(self, connector_name: str, trading_pair: str, price: float, is_buy: bool) -> OrderBookQueryResult:
        """
        Gets the volume for a specified price on the order book.

        :param connector_name: The name of the connector.
        :param trading_pair: The trading pair for which to retrieve the data.
        :param price: The price for which to find the volume.
        :param is_buy: True if buying, False if selling.
        :return: OrderBookQueryResult containing the result of the query.
        """
        order_book = self.get_order_book(connector_name, trading_pair)
        return order_book.get_volume_for_price(is_buy, price)
Example:


price = self.market_data_provider.get_volume_for_price('binance', 'BTC-USDT', 70000, True)
Order Book¶

    def get_order_book_snapshot(self, connector_name, trading_pair) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves the order book snapshot for a trading pair from the specified connector, as a tuple of bid and ask in
        DataFrame format.
        :param connector_name: str
        :param trading_pair: str
        :return: Tuple of bid and ask in DataFrame format.
        """
        order_book = self.get_order_book(connector_name, trading_pair)
        return order_book.snapshot
Example:


price = self.market_data_provider.get_order_book_snapshot('binance', 'BTC-USDT')
Candles¶
Candles are trailing intervals of OHCLV data that can be used to generate custom indicators.


    def get_candles_df(self, connector_name: str, trading_pair: str, interval: str, max_records: int = 500):
        """
        Retrieves the candles for a trading pair from the specified connector.
        :param connector_name: str
        :param trading_pair: str
        :param interval: str
        :param max_records: int
        :return: Candles dataframe.
        """
        candles = self.get_candles_feed(CandlesConfig(
            connector=connector_name,
            trading_pair=trading_pair,
            interval=interval,
            max_records=max_records,
        ))
        return candles.candles_df.iloc[-max_records:]
Example:


price = self.market_data_provider.get_candles_df('binance', 'BTC-USDT', '3m', 1000)
July 22, 2025

Candles


Candles allow user to compose a trailing window of real-time market data in OHLCV (Open, High, Low, Close, Volume) form from certain supported exchanges.

It combines historical and real-time data to generate and maintain this window, allowing users to create custom technical indicators, leveraging pandas_ta.

Supported Exchanges¶
See Candles Feed for a list of the currently supported exchanges.

A common practice is to execute bots on decentralized exchanges or smaller exchanges using candles data from other exchanges.

Key Configuration Parameters¶
connector: The data source (e.g., binance or binance_perpetual).
trading_pair: The trading pair (e.g., BTC-USDT).
interval: Time interval between candles (e.g., 5m for 5 minutes).
max_records: Maximum number of candles to store.
Downloading Candles¶
Candles provide a concise way to access historical exchange data. See the download_candles script.

Adding Technical Indicators¶
Incorporate technical indicators to candle data for enhanced strategy insights:


def format_status(self) -> str:
    # Ensure market connectors are ready
    if not self.ready_to_trade:
        return "Market connectors are not ready."
    lines = []
    if self.all_candles_ready:
        # Loop through each candle set
        for candles in [self.eth_1w_candles, self.eth_1m_candles, self.eth_1h_candles]:
            candles_df = candles.candles_df
            # Add RSI, BBANDS, and EMA indicators
            candles_df.ta.rsi(length=14, append=True)
            candles_df.ta.bbands(length=20, std=2, append=True)
            candles_df.ta.ema(length=14, offset=None, append=True)
            # Format and display candle data
            lines.extend([f"Candles: {candles.name} | Interval: {candles.interval}"])
            lines.extend(["    " + line for line in candles_df.tail().to_string(index=False).split("\n")])
    else:
        lines.append("  No data collected.")

    return "\n".join(lines)
Multiple Candles¶
For strategies requiring multiple candle intervals or trading pairs, initialize separate instances:


from hummingbot.data_feed.candles_feed.candles_factory import CandlesFactory, CandlesConfig

class InitializingCandlesExample(ScriptStrategyBase):
    # Configure two different sets of candles
    candles_config_1 = CandlesConfig(connector="binance", trading_pair="BTC-USDT", interval="3m")
    candles_config_2 = CandlesConfig(connector="binance_perpetual", trading_pair="ETH-USDT", interval="1m")

    # Initialize candles using the configurations
    candles_1 = CandlesFactory.get_candle(candles_config_1)
    candles_2 = CandlesFactory.get_candle(candles_config_2)
Displaying Candles in status¶
Modify the format_status method to display candlestick data:


def format_status(self) -> str:
    # Check if trading is ready
    if not self.ready_to_trade:
        return "Market connectors are not ready."

    lines = ["\n############################################ Market Data ############################################\n"]
    # Check if the candle data is ready
    if self.eth_1h_candles.is_ready:
        # Format and display the last few candle records
        candles_df = self.eth_1h_candles.candles_df
        candles_df["timestamp"] = pd.to_datetime(candles_df["timestamp"], unit="ms").dt.strftime('%Y-%m-%d %H:%M:%S')
        display_columns = ["timestamp", "open", "high", "low", "close"]
        formatted_df = candles_df[display_columns].tail()
        lines.append("One-hour Candles for ETH-USDT:")
        lines.append(formatted_df.to_string(index=False))
    else:
        lines.append("  One-hour candle data is not ready.")

    return "\n".join(lines)
Logging Candles Periodically¶
To log candle data in the on_tick method:


def on_tick(self):
    self.logger().info(self.candles.candles_df)
Additional Key Methods and Properties¶
start and stop Methods: Control the initiation and termination of the candle data stream.
is_ready Property: Check if the candle data is complete and ready for use.
candles_df Property: Access the DataFrame containing the latest candle data.
July 22, 2025

Executors
executors

Executors in Hummingbot are self-managing components that handle the execution of orders according to predefined conditions set by Controllers, which, in turn, utilize data from the MarketDataProvider (Candles, Orderbook, Trades). Executors are tasked with managing the state of orders — initiating, refreshing, and canceling orders, as well as halting their own operation when certain conditions are met.

Types of Executors¶
Position Executor
DCA Executor
Arbitrage Executor
TWAP Executor
Benefits of Executors¶
Autonomy: Executors independently manage order states, offloading complex logic from the user.
Simplicity: They simplify strategy code, enabling users to create powerful strategies with ease.
Flexibility: By dynamically adjusting to market data, Executors can set spreads and shift prices, offering greater strategy adaptability.
Executor Orchestrator¶
The ExecutorOrchestrator serves as a utility class that enables trading strategies to dynamically create, stop, and manage executors, which are specialized units responsible for executing trading activities such as placing and managing orders.

Key Features and Operations¶
Initialization: The ExecutorOrchestrator is initialized with a reference to the trading strategy (strategy) and an update interval (executors_update_interval). This setup allows it to periodically update and manage executors based on the strategy's requirements.

Executor Management: It maintains a dictionary of executors, where each executor is associated with a controller ID. This structure facilitates the organization and retrieval of executors for management purposes.

Action Execution: The orchestrator can execute various actions (ExecutorAction) such as creating, stopping, and storing executors. Actions are processed either individually or in batches, allowing for flexible execution management.

Creating Executors: Based on the CreateExecutorAction, it can instantiate different types of executors (e.g., PositionExecutor, DCAExecutor, ArbitrageExecutor) with specific configurations. This allows strategies to deploy diverse trading tactics dynamically.

Stopping Executors: Using the StopExecutorAction, it can gracefully stop executors, ensuring that any ongoing operations are properly concluded before termination.

Storing Executors: The StoreExecutorAction enables the orchestrator to store executor data, facilitating persistence and analysis of executor performance over time.

Performance Reporting: The orchestrator can generate detailed performance reports for individual controllers or globally across all controllers. These reports include metrics such as realized and unrealized P&L (Profit and Loss), trading volume, and the distribution of close types, providing insights into the effectiveness of the trading strategy and its executors.

July 22, 2025

Position Executor
PositionExecutor: Manages opening and closing positions of equal amounts, ensuring the portfolio remains balanced ± the position's profit or loss. It's applicable in both perpetual and spot markets, requiring pre-ownership of the asset for spot markets.

The PositionExecutor uses a configuration object, PositionExecutorConfig, to manage an order after it is placed, following the Triple Barrier Method. This configuration sets pre-defined stop loss, take profit, time limit, and trailing stop parameters.


class TripleBarrierConf(BaseModel):
    # Configure the parameters for the position
    stop_loss: Optional[Decimal]
    take_profit: Optional[Decimal]
    time_limit: Optional[int]
    trailing_stop_activation_price_delta: Optional[Decimal]
    trailing_stop_trailing_delta: Optional[Decimal]
    # Configure the parameters for the order
    open_order_type: OrderType = OrderType.LIMIT
    take_profit_order_type: OrderType = OrderType.MARKET
    stop_loss_order_type: OrderType = OrderType.MARKET
    time_limit_order_type: OrderType = OrderType.MARKET
Key Configs:

stop_loss: Determines the stop-loss percentage
take_profit: Sets the take-profit percentage.
time_limit: Establishes a time limit for the trade.
trailing_stop_activation_price_delta: Specifies the delta for activating a trailing stop.
trailing_stop_trailing_delta: Sets the trailing delta for the trailing stop.
Example:



The PositionExecutor class implements the Triple Barrier Method popularized in Martin Prado's famous book Advances in Financial Machine Learning.

The triple barrier method is a structured approach to position management, where three "barriers" determine the outcome of a trade:

Stop Loss: Caps the potential loss on a position.
Take Profit: Secures profits by specifying a target exit price.
Time Limit: Restricts the duration a trade can remain open, adding a temporal dimension to the exit strategy.
Additionally, PositionExecutor also contains a Trailing Stop mechanism, which dynamically adjusts the stop loss level as favorable price movements occur.

Spot vs Perpetual Behavior¶
The PositionExecutor class is designed to work on both spot and perpetual exchanges, allowing you to write strategies that be used on either type:

On perpetual exchanges, they apply the take-profit and stop-loss levels described below to manage a long or short position after it has been created.
On spot exchanges, they place take-profit and stop-loss orders to manage an order after it has been filled. This is similar to Hanging Orders but on an individual order level.
Configuration¶
The PositionExecutor engages with the market by executing orders based on the PositionConfig. It applies the triple barrier method as follows:


triple_barrier_confs = TripleBarrierConf(
    stop_loss=stop_loss,
    take_profit=take_profit,
    time_limit=time_limit,
    trailing_stop_activation_price_delta=trailing_stop_activation_price_delta,
    trailing_stop_trailing_delta=trailing_stop_trailing_delta,
)
Stop Loss¶
Activated when the price moves against the position beyond a specified threshold.



Take Profit¶
Triggered when the price reaches a pre-set level that represents a desired profit.



Time Limit¶
When the time limit is reached, the position will be closed or an opposing trade will be executed.



Trailing Stop¶
The trailing stop evaluates the position after a certain time has passed and may close it to avoid market shifts or decay.

trailing_stop_activation_price_delta: The price movement required to activate a trailing stop.
trailing_stop_trailing_delta: The distance maintained behind the price as a trailing stop, which adjusts as the price moves favorably.


Execution Flow¶
Here's a simplified flow of how the PositionExecutor operates in conjunction with the triple barrier method:

The PositionExecutor initiates a position based on signals from the strategy, which interprets market data
It continuously monitors market prices and compares them against the defined barriers.
If the price hits the take profit or stop loss levels, the PositionExecutor executes a trade to close the position accordingly.
The trailing stop is adjusted as the price moves favorably, providing a dynamic risk management tool.
The time limit barrier ensures that positions do not remain open indefinitely, addressing the risk of market conditions changing over time.
Conclusion¶
The PositionExecutor is a powerful tool within Hummingbot for implementing strategies that require precise entry and exit conditions. By leveraging the triple barrier method, it provides a structured and disciplined approach to trade management, vital for both market making and directional trading strategies.

Grid Executor
The GridExecutor: is a sophisticated trading executor that implements a grid trading strategy.

Key Concepts:¶
Grid Trading: A strategy that places multiple buy and sell orders at regular price intervals (forming a grid), attempting to profit from price oscillations within a range.

Grid Levels: The executor creates multiple price levels between a start and end price, where each level represents a potential trading opportunity.

Main Features:¶
1. Grid Generation:¶
Creates evenly spaced price levels between start_price and end_price

Each level has an associated order amount and take-profit target

Supports both spot and perpetual futures trading

2. Order Management:¶
Places and monitors orders at different grid levels

Manages both open (entry) and close (exit) orders

Automatically cancels orders that move outside activation bounds

Implements batch order processing to avoid overwhelming the exchange

3. Risk Management:¶
Triple Barrier System:

Stop Loss

Take Profit

Time Limit

Trailing Stop functionality

Position size limits

Maximum open orders control

4. State Management:¶
Grid levels can be in different states:

NOT_ACTIVE: No orders placed

OPEN_ORDER_PLACED: Entry order active

OPEN_ORDER_FILLED: Entry order completed

CLOSE_ORDER_PLACED: Exit order active

COMPLETE: Both entry and exit orders filled

5. Performance Tracking:¶
Tracks realized and unrealized PnL

Monitors fees and execution costs

Calculates position metrics

Records filled and failed orders

Example Usage:


config = GridExecutorConfig(
    connector_name="binance",
    trading_pair="BTC-USDT",
    start_price=30000,
    end_price=40000,
    total_amount_quote=1000,  # Total USDT to deploy
    min_spread_between_orders=0.01,  # 1% minimum spread
    activation_bounds=0.02,  # 2% activation bounds
)
executor = GridExecutor(strategy=my_strategy, config=config)
The executor will:

Create grid levels between $30,000 and $40,000

Deploy $1000 USDT across these levels

Maintain minimum 1% spread between orders

Only keep active orders within 2% of current price

Automatically manage entry and exit orders

This is particularly useful for:

Range-bound markets

Market making strategies

Automated rebalancing

Risk-managed trading execution

DCA Executor
DCAExecutor: Manages the execution of Dollar Cost Averaging (DCA) strategies, allowing users to spread their investment across multiple orders over time to reduce the impact of volatility. It's designed for use in both spot and perpetual markets.

Initialization¶

    def create_dca_order(self, level: int):
        """
        This method is responsible for creating a new DCA order
        """
        price = self.config.prices[level]
        amount = self.config.amounts_quote[level] / price
        order_id = self.place_order(connector_name=self.config.exchange,
                                    trading_pair=self.config.trading_pair, order_type=self.open_order_type,
                                    side=self.config.side, amount=amount, price=price,
                                    position_action=PositionAction.OPEN)
        if order_id:
            self._open_orders.append(TrackedOrder(order_id=order_id))
Key Configs:

connector_name: The exchange the user is currently trading on
trading_pair: Specifies the trading pair
order_amount: Specifies the amount for each DCA order.
order_interval_seconds: Sets the time interval between orders.
total_orders: Determines the total number of orders to be executed.
order_type: Defines the type of orders to be placed (default is LIMIT).
The DCAExecutor class implements a Dollar Cost Averaging strategy, which is a popular method for mitigating the impact of volatility by spreading purchases or sales over time.

The DCA strategy is simple yet effective, involving the execution of orders at regular intervals regardless of the asset's price. This approach can lead to a lower average cost per share or unit over time, making it a favored strategy for long-term investors.

Spot vs Perpetual Behavior¶
The DCAExecutor class is versatile, designed to operate on both spot and perpetual exchanges. This allows for the implementation of DCA strategies across different market types:

On perpetual exchanges, it schedules orders at regular intervals to manage a position over time.
On spot exchanges, it executes a series of buy or sell orders to average out the entry or exit price of an asset.
Configuration¶
The DCAExecutor engages with the market by executing orders based on the DCAExecutorConfig. It applies the DCA strategy as follows:


    type = "dca_executor"
    exchange: str
    trading_pair: str
    side: TradeType
    leverage: int = 1
    amounts_quote: List[Decimal]
    prices: List[Decimal]
    take_profit: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    trailing_stop: Optional[TrailingStop] = None
    time_limit: Optional[int] = None
    mode: DCAMode = DCAMode.MAKER
    activation_bounds: Optional[List[Decimal]] = None
Execution Flow¶
Here's a simplified flow of how the DCAExecutor operates:

The DCAExecutor initiates the first order based on the configured strategy parameters.
It waits for the specified interval before executing the next order.
This process repeats until all configured orders have been executed.
The executor monitors each order's execution and manages any necessary adjustments or cancellations according to market conditions and strategy requirements.
Conclusion¶
The DCAExecutor is an essential component within Hummingbot for traders and investors looking to implement Dollar Cost Averaging strategies. By automating the execution of DCA orders, it simplifies the process of spreading out investments over time, which can help in managing the risks associated with market volatility. Whether for accumulating a position in a bullish market or distributing assets in a bearish scenario, the DCAExecutor provides a disciplined approach to market entry and exit.

Controllers


The Controller plays a crucial role within Hummingbot's Strategy V2 framework, serving as the orchestrator of the strategy's overall behavior. It interfaces with the MarketDataProvider, which includes OrderBook, Trades, and Candles, and forwards a series of ExecutorActions to the main strategy. The strategy then evaluates these actions, deciding to execute them based on its overarching rules and guidelines.

Users can now use controllers as sub-strategies allowing them to use multiple controllers in a single script or trade multiple pairs / configs in a single bot.

Base Classes¶
Currently, the controller base classes available are:

controller_base.py: Defines ControllerBase
directional_trading_controller_base.py: Designed for indicator-based directional strategies, inherits from ControllerBase
market_making_controller_base.py: Designed for two-side market making strategies, inherits from ControllerBase
Directional Trading Controllers¶
These strategies aim to profit from predicting the market's direction (up or down) and takes positions based on signals indicating the future price movement.

Suitable for strategies that rely on market trends, momentum, or other indicators predicting price movements.

Customizing signal generation (get_signal) allows users to change various analytical models to generate trade signals and determine the conditions under which trades should be executed or stopped.

bollinger_v1
macd_bb_v1
trend_follower_v1
dman_v3
Market Making Controllers¶
These strategies provide liquidity by placing buy and sell orders near the current market price, aiming to profit from the spread between these orders.

Customization involves defining how price levels are selected (get_levels_to_execute), how orders are priced and sized (get_price_and_amount), and when orders should be refreshed or stopped early.

User may also adjust the strategy based on market depth, volatility, and other market conditions to optimize spread and order placement.

pmm_simple
pmm_dynamic
dman_maker
dman_maker_v2
Other Controllers¶
xemm_multiple_levels
arbitrage_controller
grid_strike

Connectors
What are Connectors?¶
Connectors are packages of code that link Hummingbot's internal trading engine with real-time and historical data from different cryptocurrency exchanges and blockchains, via WebSocket and/or REST API. They standardize interactions with the idiosyncratic APIs offered by these platforms, for purposes such as gathering order book and blockchain data, as well as sending and cancelling transactions and orders.

CLOB Connectors¶
CLOB (Central Limit Order Book) connectors integrate into a CLOB exchange's WebSocket API, enabling standardized order placement/cancellation and order book data fetching from the perspective of Hummingbot strategies. These connectors work with both centralized exchanges (CEX) and decentralized exchanges (DEX) that utilize a central limit order book model.

See CLOB Connectors for a list of the current CLOB connectors in Hummingbot

Gateway DEX Connectors¶
Gateway connectors establish and maintain connections to automated market maker (AMM) DEXs and other protocols on various blockchain networks, interfaces with their Javascript SDKs, and exposes standard REST API endpoints for trading and liquidity provision-related actions on these DEXs.

See Gateway Connectors for a list of the current Gateway connectors in Hummingbot, and see Gateway for more information about the Gateway API middleware.

Connector Maintenance¶
CLOB connectors requires ongoing maintenance: fixing bugs, addressing user issues, and keeping up with updates to both the exchange/blockchain API as wel as improvements to the Hummingbot connector standard.

Hummingbot Foundation maintains certain reference connectors to maintain an updated standard and leverages community-based developers to maintain other connectors to the same standard. We assign Bounties to community developers to upgrade and fix bugs for each exchange's connectors in the codebase.

Connector Governance¶
Hummingbot Foundation governance lets HBOT holders which exchanges are supported by the open source codebase.

New connectors may be contributed by community members via New Connector Proposals, which require a pull request with the connector code to the Hummingbot Github repo, along with a minimum HBOT balance to create.

For existing connectors, quarterly Exchange Connector Polls allocates HBOT bounties toward top exchanges and determines which exchanges should be included in the codebase going forward. See the Connector Pots tab in HBOT Tracker for the current allocations for each exchange.

July 22, 2025

CLOB Connectors
CLOB (Central Limit Order Book) connectors integrate into a CLOB exchange's WebSocket API, enabling standardized order placement/cancellation and order book data fetching from the perspective of Hummingbot strategies. These connectors work with both centralized exchanges (CEX) and decentralized exchanges (DEX) that utilize a central limit order book model.

Each connector is customized for a particular exchange's idiosyncrasies to enable this level of standardization, so they should ideally have a maintainer, whose role is to ensure consistent performance by fixing bugs, incorporating API updates, and other ongoing work.

CLOB Connector Types¶
Currently, Hummingbot supports two CLOB connector standards, each which define how the code encapsulated in a connector folder should offer standardized API endpoints and hook into the Hummingbot client.

CLOB Spot: WebSocket-based connectors to an exchange's spot order book-based markets. Each connector is a folder in the hummingbot/connector/exchange folder.

CLOB Perp: WebSocket-based connectors to an exchange's perpetual futures order book-based markets. Each connector is a folder in the hummingbot/connector/derivative folder. By convention, these connector names end in _perpetual.

These connector standards allow users to create Strategies and Scripts that can operate on different spot and perpetual markets without modification.

Current CLOB Connectors¶
Here are the CLOB connectors in the codebase for the current Epoch. Note that the Foundation prioritizes fixes for connectors from exchanges that are sponsors or partners, so they tend to be more reliable and better maintained.

Exchange	Foundation Partner	Spot	Perp	Connector Guide
Binance	✓	✓	✓	Guide
Bitmart	✓	✓	✓	
Derive	✓	✓	✓	Guide
dYdX	✓		✓	Guide
Gate.io	✓	✓	✓	
HTX	✓	✓		
Kucoin	✓	✓	✓	
OKX	✓	✓	✓	
XRPL	✓	✓		Guide
AscendEx		✓		
BingX		✓		
Bitstamp		✓		
Bitrue		✓		
Bitget			✓	
Bybit		✓	✓	
BTC Markets		✓		
Coinbase		✓		
Cube		✓		
Dexalot		✓	✓	Guide
Kraken		✓		
MEXC		✓		
NDAX		✓		
Vertex		✓		
Building CLOB Connectors¶
The Notion templates below summarize the file and functionalities needed to build the latest spot and perpetual connectors standards and support V2 Strategies:

Spot Connector v2.1 Notion Template: Use this template to build CLOB spot connectors that conform
Perp Connector v2.1 Notion Template: Use this template to build CLOB perp connectors that conform
See Building Connectors for more information.

If the exchange is not yet supported by Hummingbot, you can submit a governance proposal for it to be included. New connectors may be contributed by community members via New Connector Proposals, which require a pull request with the connector code to the Hummingbot Github repo, along with a minimum HBOT balance to create.

July 22, 2025


Gateway DEX Connectors
Gateway is API middleware that enables Hummingbot to send and receive data from different blockchain protocols and provides a standard interface for community developers to add connectors for common DeFi protocols.

Gateway connectors establish and maintain connections to automated market maker (AMM) DEXs and other protocols on various blockchain networks, interfaces with their Javascript SDKs, and exposes standard REST API endpoints for trading and liquidity provision-related actions on these DEXs.

See Gateway for more information.

Gateway DEX Connector Schemas¶
Gateway schemas define standardized endpoints that chains and connectors must implement to ensure compatibility with Hummingbot. Each schema specifies a set of endpoints with precise request and response structures that the Hummingbot GatewayHTTPClient and related connector interfaces utilize. Each chain and connector route should be self-contained in its own file and contain both the route handler and other logic required.

Gateway currently supports the following connector schemas:

Swap: For taker-only DEXs and DEX aggregators.
AMM: For Automated Market Maker DEXs (like Raydium Standard and Uniswap V2 pools)
CLMM: For Concentrated Liquidity Market Maker DEXs (like Raydium Concentrated and Uniswap V3 pools)
The schema files are located in the src/schemas/trading-types directory of the Gateway repository.

For comprehensive documentation, including detailed endpoint specifications, request parameters, and response formats, please refer to the Schemas page.

Current Gateway DEX Connectors¶
Note

Gateway is currently undergoing a large multi-release codebase refactoring, approved in proposal NCP-22. During this refactoring process, not all connectors are available in the new version, as they are being gradually migrated from the legacy architecture.

Here are the Gateway connectors in the codebase for the current Epoch. The Updated column shows whether the connector has been updated for the changes approvd in NCP-22

Exchange	Chain Architecture	Updated?	Connector Types
Jupiter	solana	✓	swap
Meteora	solana	✓	swap, clmm
Raydium	solana	✓	swap, clmm, amm
Uniswap	ethereum	✓	swap, amm, clmm
Balancer	ethereum		swap, amm
Carbon	ethereum		swap, amm
Curve	ethereum		swap, amm
ETCSwap	ethereum		swap, amm, clmm
Pancakeswap	ethereum		swap, amm
Quickswap	ethereum		amm
Sushiswap	ethereum		amm
TraderJoe	ethereum		amm
Building Gateway DEX Connectors¶
See Adding a New Gateway DEX Connector guide. This guide uses the new Raydium connector as reference and walks through how to build your connector for compatibility with the Hummingbot client.

If the exchange is not yet supported by Hummingbot, you can submit a governance proposal for it to be included. New connectors may be contributed by community members via New Connector Proposals, which require a pull request with the connector code to the Hummingbot Github repo, along with a minimum HBOT balance to create.

Building CLOB Connectors
Note

The information below are for developers building spot and perp connectors that integrate directly into the Hummingbot client. For information on developing gateway connectors that use Gateway, see Building Gateway Connectors.

Exchange API Requirements¶
See Exchange API Requirements for what the exchange API requirements needed to support the latest Hummingbot spot and perp connector standards.

Building Connectors¶
To gain a deeper understanding for how Hummingbot connectors work, we recommend reading the following engineering posts from Hummingbot's original technical founder:

Hummingbot Architecture - Part 1
Hummingbot Architecture - Part 2
The following pages offer more details on various components and classes of a connector:

Connector Architecture: Overview of how a connector works
Order Lifecycle and Market Events: How a connector handles the lifecycle of an order
Handling Rate Limits with API Throttler: Using the AsyncThrottler class to handle exchange rate limits
Debug and Testing Connectors: Various ways to test and debug a connector
Spot Connectors¶
Spot connectors provide WebSocket and REST-based integrations to spot order book-based markets offered by an exchange, which may be centralized (CEX) or decentralized (DEX). Each connector is a folder in the hummingbot/connector/exchange folder.

Spot Connector v2.1 Notion Template: Use this template to build spot connectors that conform to the latest standard, which allows the connector to be used with V2 Strategies.
Spot Connector Developer Checklist: Similar to the Notion Template, this page provides a checklist of the key steps and the main components and functionalities of each class
Spot Connector QA Checklist: Our QA team will conducts these tests before approving spot connectors
Perp Connectors¶
Perp connectors provide WebSocket and REST-based integrations to perpetual futures order book-based markets offered by an exchange, which may be centralized (CEX) or decentralized (DEX). Each connector is a folder in the hummingbot/connector/derivative folder. By convention, these connector names end in _perpetual.

Perp Connector v2.1 Notion Template: Use this template to build perp connectors that conform to the latest standard, which allows the connector to be used with V2 Strategies.
Perp Connector Developer Checklist: Similar to the Notion Template, this page provides a checklist of the key steps and the main components and functionalities of each class
Perp Connector QA Checklist: Our QA team will conducts these tests before approving perp connectors
Contributing Connectors¶
Introducing an exchange connector into the Hummingbot code base requires a mutual commitment from both the Hummingbot Foundation team and the contributing developers to maintaining a high standard of code quality and software reliability.

We encourage and welcome new connector contributions from the community, subject to the guidelines and expectations outlined below.

Connector folder: A folder that contains a complete set of connector files based off of the examples above.
Adherence to standard: Connector should pass both the Developer and QA Checklist for its type
Unit tests: The pull request should pass code coverage checks
Documentation: Accompanying documentation pull request to hummingbot-site repo
Inline code comments Particularly for any code that is materially different from the templates
Here is an overview of the process to get a new connector merged into the codebase:

Fork the Hummingbot or Gateway repositories and add a spot or perp connector that fulfills the respective requirements above.
Submit a pull request with the connector to the development branch in Github, following the Contribution Guidelines.
Submit a New Connector Proposal in the Hummingbot NCP Snapshot
Additional Resources¶
For questions, please visit the #developer-chat channel on our Discord.

July 22, 2025

Building Gateway DEX Connectors
This guide provides a comprehensive walkthrough for integrating a new decentralized exchange (DEX) connector into Hummingbot's Gateway middleware. We'll use the Raydium connector as an example to demonstrate the implementation process.

Prerequisites¶
Before starting, ensure you have:

Familiarity with TypeScript/JavaScript development
Understanding of the DEX's protocol and SDK
Understanding of the blockchain wallet and node architecture where the DEX resides
Access to testnet/mainnet networks for testing
Understanding of the new Gateway architecture
Requirements¶
A connector must implement a set of routes that match one or more Schemas. Connectors implementing these schemas must:

Expose all required routes defined in the corresponding schema
Import and use the request/response TypeScript types from the schema files
Structure each route in a self-contained file that includes route handler function, request validation logic, business logic for the specific DEX/protocol, and error handling
Follow the naming conventions and parameter structures defined in the schema
Return responses that strictly conform to the response type definitions
Add comprehensive unit tests
Add detailed documentation
For reference implementations, see existing connectors in the src/connectors directory.

0. Install Gateway from Source¶
First, install and run Gateway from source - see installation.

Afterwards, follow the steps below to develop a Gateway connector:

1. Create Configuration Template¶
📁 Folder gateway/src/templates

Create a template in the templates folder and name it <exchange_name>.yml. This file defines the configurations needed for connecting to the exchange.

Example configuration for Raydium:


# settings for AMM routes
amm:
  # how much the execution price is allowed to move unfavorably
  allowedSlippage: '1/100'
  # predefined pools
  pools:
    RAY-SOL: 'AVs9TA4nWDzfPJE9gGVNJMVhcQy3V9PGazuz33BfG2RA'
    SOL-USDC: '58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2'
    RAY-USDC: '6UmmUiYoBjSrhakAobJw8BvkmJtDVxaeBtbt7rxWo1mg'
    # ... other pools ...

# settings for CLMM routes
clmm:
  # how much the execution price is allowed to move unfavorably
  allowedSlippage: '1/100'
  # predefined pools
  pools:
    SOL-USDC: '3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv'
    RAY-USDC: '61R1ndXxvsWXXkWSyNkCxnzwd3zUNB8Q2ibmkiLPC8ht'
    # ... other pools ...
2. Create Configuration Schema¶
📁 Folder gateway/src/services/schema

Create a schema that validates your configuration template. Name it <exchange_name>-schema.json. This ensures type safety and validation of configuration values.

Example schema for Raydium:


{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "amm": {
      "type": "object",
      "properties": {
        "allowedSlippage": { "type": "string" },
        "pools": {
          "type": "object",
          "additionalProperties": { "type": "string" }
        }
      },
      "required": ["allowedSlippage", "pools"]
    },
    "clmm": {
      "type": "object",
      "properties": {
        "allowedSlippage": { "type": "string" },
        "pools": {
          "type": "object",
          "additionalProperties": { "type": "string" }
        }
      },
      "required": ["allowedSlippage", "pools"]
    }
  },
  "required": ["amm", "clmm"]
}
3. Create Connector Files¶
📁 Folder gateway/src/connectors

Create a new directory for your connector with the following structure:


connectors/
└── raydium/
    ├── raydium.config.ts     # Configuration types and values loaded from raydium.yml
    ├── raydium.utils.ts      # Shared constants and helper functions
    ├── raydium.ts            # Core connector logic that handles Raydium SDK initialization and Solana chain interactions
    ├── amm-routes/           # AMM-specific routes
    └── clmm-routes/          # CLMM-specific routes
The raydium.config.ts file defines the TypeScript interfaces and configuration values for the config file that you created earlier. Meanwhiel, the raydium.utils.ts file contains shared constants and helper functions used across the connector validation functions (isValidClmm, isValidAmm, isValidCpmm).

The raydium.ts file serves as the core connector class that handles all interactions with the Raydium SDK and Solana blockchain. It implements a singleton pattern to ensure only one instance exists per network. Key responsibilities include: - Initializing the Raydium SDK with proper network configuration and wallet connection - Managing pool information retrieval for both AMM and CLMM pools - Handling position management for CLMM pools - Providing utility methods for slippage calculation and pool discovery - Implementing chain-specific operations like token balance checks and transaction handling

The class provides methods for: - Pool information retrieval (getAmmPoolInfo, getClmmPoolInfo) - Position management (getPositionInfo, getClmmPosition) - Pool type detection (getPoolType) - Slippage calculation (getSlippagePct)

4. Add Routes for Each Schema¶
For each schema type, create the following route files:

Swap Routes¶
For DEX aggregators like Jupiter, add these swap routes in a /routes or /swap-routes folder:

routes/quote-swap.ts: Implements the GET /quote-swap endpoint
routes/execute-swap.ts: Implements the POST /execute-swap endpoint
Since AMM and CLMM DEX connectors implement the Swap schema, create these files in their respective route folders:

amm-routes/quote-swap.ts: Implements the GET /quote-swap endpoint
amm-routes/execute-swap.ts: Implements the POST /execute-swap endpoint
clmm-routes/quote-swap.ts: Implements the GET /quote-swap endpoint
clmm-routes/execute-swap.ts: Implements the POST /execute-swap endpoint
Example structure for amm-routes/quote-swap.ts:


import { GetSwapQuoteRequest, GetSwapQuoteResponse } from '@hummingbot/gateway/schemas/trading-types/swap-schema';

export async function getQuoteSwap(request: GetSwapQuoteRequest): Promise<GetSwapQuoteResponse> {
  // Implementation logic here
  return {
    // Response matching GetSwapQuoteResponse type
  };
}
AMM Routes¶
Create these files in an amm-routes/ subdirectory:

pool-info.ts: Implements GET /pool-info
quote-liquidity.ts: Implements GET /quote-liquidity
add-liquidity.ts: Implements POST /add-liquidity
remove-liquidity.ts: Implements POST /remove-liquidity
Example structure for pool-info.ts:


import { GetPoolInfoRequest, PoolInfo } from '@hummingbot/gateway/schemas/trading-types/amm-schema';

export async function getPoolInfo(request: GetPoolInfoRequest): Promise<PoolInfo> {
  // Implementation logic here
  return {
    // Response matching PoolInfo type
  };
}
CLMM Routes¶
Create these files in a clmm-routes/ subdirectory:

pool-info.ts: Implements GET /pool-info
positions-owned.ts: Implements GET /positions-owned
position-info.ts: Implements GET /position-info
quote-position.ts: Implements GET /quote-position
open-position.ts: Implements POST /open-position
add-liquidity.ts: Implements POST /add-liquidity
remove-liquidity.ts: Implements POST /remove-liquidity
collect-fees.ts: Implements POST /collect-fees
close-position.ts: Implements POST /close-position
Example structure for position-info.ts:


import { GetPositionInfoRequest, PositionInfo } from '@hummingbot/gateway/schemas/trading-types/clmm-schema';

export async function getPositionInfo(request: GetPositionInfoRequest): Promise<PositionInfo> {
  // Implementation logic here
  return {
    // Response matching PositionInfo type
  };
}
For each route file:

Import the appropriate request/response types from the schema
Implement the route handler function with proper typing
Add input validation
Implement the business logic for interacting with the DEX
Handle errors appropriately
Return responses that strictly match the schema types
5. Register Connector Routes¶
Update GET /connectors route:

📁 File gateway/src/connectors/connector.routes.ts


{
    name: 'raydium/amm',
    trading_types: ['amm', 'swap'],
    available_networks: RaydiumConfig.config.availableNetworks,
},
{
    name: 'raydium/clmm',
    trading_types: ['clmm', 'swap'],
    available_networks: RaydiumConfig.config.availableNetworks,
},
Add the new connector routes to Gateway's app.ts:

📁 File gateway/src/app.ts


{ name: 'raydium/clmm', description: 'Raydium CLMM connector endpoints' },
{ name: 'raydium/amm', description: 'Raydium AMM connector endpoints' },
6. Perform Manual Testing¶
Run in dev mode and test each route using the Swagger UI at https://localhost:15888/docs
Verify responses match schema definitions
Test with different tokens, pools, and amounts
Handle common errors with appropriate Fastify responses and error messages
7. Add Unit Tests¶
Warning

Reference implementations coming soon

Create comprehensive test suites for each route
Test edge cases and error conditions
Ensure proper validation of inputs
Verify response formats
8. Add Documentation¶
Add a connector documentation page similar to Raydium
Include exchange-specific information on setting up wallets, accessing markets, etc
Describe configuration options and supported networks
Document known issues and custom endpoints
Add the page to the list of Gateway DEXs in mkdoc.yml
9. (Optional) Propose for Inclusion in Hummingbot¶
New Gateway DEX connectors may be contributed by community members via New Connector Proposals. To propose your connector for inclusion in the official Hummingbot codebase:

Submit a pull request with your connector code to the Hummingbot Gateway repository
Create a corresponding pull request to the Hummingbot Site repository with documentation for your connector
Create a New Connector Proposal following the governance process, which requires a minimum HBOT token balance to submit
If approved, the Hummingbot Foundation will review and merge your connector into the official codebase in a future release.

Hummingbot Client
If you have installed Hummingbot successfully, you should see a welcome screen like the one below: 

Hummingbot features a command-line interface (CLI) that helps you building and run trading bots without coding skills.

Basic Operations¶
Basic features in Hummingbot.

User Interface Guide
Commands and Shortcuts
Launch and Exit Hummingbot
Create and Delete Password
Connect to an Exchange
Create Config Files
Find Log Files
Check Balances
Start and Stop Strategy
Check Bot and Market Status
Check Trading Performance
Paper Trading Mode
Advanced Features¶
Advanced features in Hummingbot for quant traders and developers.

Auto-start from Command Line
Balance Limit
Clock Tick Size
Color Settings
Connect External Database
Kill Switch
Override Fees
Rate Limits Share Pct
Rate Oracle
Telegram Integration

User Interface Guide¶
Hummingbot CLI

The CLI is divided into five panes:

Input pane (lower left): Where users enter commands
Hummingbot CLI

Output pane (upper left): Prints the output of the user's commands
Hummingbot CLI

Log pane (right): Log messages
Log Pane

Top navigation bar: Displays the status/information of the following items

Version:

Reference of Version Release (Currently at 1.13.0)
Strategy:

Hummingbot has different strategy configurations that can be used for trading or liquidity mining. Currently we are moving away from strategy based config in favor of scripts. See the quick start guide for scripts here
Strategy_file:

Displays the current in use strategy or script file
Top Navigation

Bottom navigation bar: Displays the information of the following items

Trades
Number of trades done by the bot
Total P&L
Total profit & loss
Return%
Return percentage of assets
CPU
CPU usage of the computer
Mem

Memory usage of the computer
Threads

Duration
Duration of the trading session
Bottom Navigation

Show and hide log pane¶
The log pane on the right can be shown or hidden in two ways:

Click the log pane button in the upper right hand corner
Press CTRL + T shortcut on your keyboard
Hide Log Pane

Tabs¶
Users can now open another tab in the left pane of Hummingbot where the log pane is supposed to be upon entering a command associated with the Tabs feature. Users can now switch between the log pane and the new tab they have opened simulateneously.

Note

Currently, the feature only works with the order_book parameter.

Opening and Closing¶
Opening a tab¶
Use the tabs by simply inputting a command associated with the tabs feature.

Upon using the order_book command and any suffix it will open a tab automatically.

opening tabs

showing tab

Closing a tab¶
Simply click on the x at the top right corner or inputting parameter_name --close

One option to close the tab is by clicking on the x next to order_book

closing tabs

Alternatively, you can remove the new tab by inputting the order_book --close command to close the tab

alternative closing tabs

closed tabs

Keyboard shortcuts¶
Keyboard Combo	Command	Description
Double CTRL + C	Exit	Press CTRL + C twice to exit the bot
CTRL + S/kbd>	Status	Show bot status
CTRL + F	Search /
Hide Search	Toggle search in log pane
CTRL + X	Exit Config	Exit from the current configuration question
CTRL + A	Select All	* Select all text
CTRL + Z	Undo	* Undo action
Single CTRL + C	Copy	* Copy text
CTRL + V	Paste	* Paste text
CTRL + R	Reset Style	Set default color style
CTRL + T	Toggle logs	Hide / show the logs pane
* Used for text edit in input pane only.

Note about search:

Press CTRL + F to trigger display the search field

Enter your search keyword (not case sensitive)

Hit Enter to jump to the next matching keyword (incremental search)

When you are done, press CTRL + F again to go back to reset

Linux¶
Keyboard Combo	Command
CTRL + C	Copy
SHIFT + RMB (right-mouse button)	Paste
To highlight, hold SHIFT + LMB (left mouse button) and drag across the text you want to select.

macOS¶
Keyboard Combo	Command
⌘ + C	Copy
⌘ + V	Paste
Note

To select text on macOS, you may need to enable the Allow Mouse Reporting option by pressing ⌘ + R or selecting View > Allow Mouse Reporting in the menu bar.

allowmouse

Then you should be able to select text by holding LMB (left mouse button) and drag. You can also hold down ⌥ + shift to select specific lines like the image below.

highlightmacos

When accessing Hummingbot on a Linux cloud server through ssh using a macOS terminal, hold down the Option ⌥ key or ⌥ + ⌘ to highlight text.

Windows¶
Keyboard Combo	Command
CTRL + C	Copy
CTRL + V	Paste
To use this shortcut, check this box by doing a right-click on the title bar at the top of the Hummingbot window, then select Properties.

Gateway DEX Middleware
What is Gateway?¶
Hummingbot Gateway is open source API middleware that helps the Hummingbot client to connect to decentralized exchanges (DEX) on various blockchain networks.

A companion codebase to the Hummingbot, Gateway manages interfacing with DEX connectors and exposes standard REST API endpoints for trading and liquidity-related functionality on these DEXs, enabling Hummingbot to run strategies that operate across multiple CEX and DEXs.

The Gateway code repo is open sourced under the Apache 2.0 license and updated using the same release cycle as the main Hummingbot client codebase.

New vs Legacy¶
Gateway is currently undergoing a large multi-release codebase refactoring, approved in proposal NCP-22. During this refactoring process, not all connectors are available in the new version, as they are being gradually migrated from the legacy architecture.

We will maintain two versions of Gateway throughout this transition period to ensure users can continue using all supported connectors while the migration progresses. Both versions are compatible with the latest upgrades and strategies in the Hummingbot client.

New (v2.5+): The latest version with flexible route schemas, supporting Swap, AMM, and CLMM connector types. This version is designed for future expansion.

Legacy (v2.2): The previous version that supports a wider range of chains and networks but with a more rigid architecture. This version will continue to be maintained while the refactor is in progress.

Supported Chains¶
Each DEX utilizes a chain connector that integrates a Layer 1 blockchain and their networks into Gateway, enabling wallet access, node RPC interactions, and other support needed by tje DEX.

Chain support in Gateway is determined by the decentralized exchanges (DEX) that HBOT holders vote to be included in the Hummingbot codebase in quarterly Exchange Connector Polls for each Epoch. The main chains and networks where each DEX is deployed will be supported in subsequent releases of Hummingbot and Gateway.

Legacy Gateway (v2.2 and before) supported a wide range of chains and their networks including Ethereum, Algorand, Avalanche, BNB Chain, Cosmos, Cronos, Ethereum Classic, Osmosis, Polygon, and Solana. However, its inflexible route architecture tight coupling with the Hummingbot client made it difficult to support more types of trading interactions.

The new version of Gateway (v2.5+) is more flexible and chain-agnostic. Initially, it supports only a few base chain architectures along with any network that is compatible with them, starting with networks based on the Solana and Ethereum-based virtual machines.

See Supported Chains the list of chains and their DEXs supported by Gateway.

History¶
See the following blog posts from Hummingbot co-founder and original CTO Martin Kou for more information about Gateway's history, background, and intended developer experience:

Hummingbot Gateway V2 Architecture - Part 1
Hummingbot Gateway V2 Architecture - Part 2

Hummingbot Dashboard
Overview¶
Hummingbot Dashboard is an open-source graphical interface designed to help users manage their portfolios across multiple exchanges, configure and backtest strategies, and deploy and manage multiple Hummingbot instances efficiently.

Starting with v2.7.0, Dashboard is powered by the new Hummingbot API and Hummingbot API Client, providing a robust and scalable architecture for managing trading operations at scale.

Dashboard simplifies bot management and is fully compatible with Controllers, allowing users to configure and backtest strategies before deploying them live.

Documentation Update

All dashboard pages have been updated to work with the new API architecture. Detailed documentation for each page will be added soon.

Highlights¶
Accessible Framework: Uses the Streamlit open source data visualization framework
Backtestable Strategies: Configure and backtest strategy controllers
Multi-Bot Deployment: Deploy and manage multiple bot instances and monitor their real-time performance
API-Powered: Built on top of the new Hummingbot API for reliable bot management
Getting Started¶
To get started, check out the Hummingbot Dashboard Quickstart guide, or the links below with a short explanation of each page (also in the sidebar).

Adding Credentials:

Viewing Portfolio:

Configuring Strategies:

Backtesting Strategies:

Deploying Instances:

Managing Instances:

July 22, 2025

Adding Credentials
The Credentials page in the Hummingbot Dashboard is a comprehensive interface for managing your API keys and related credentials. It offers several functionalities to streamline the process of handling multiple accounts and their respective credentials.

credentials

Available Accounts and Credentials¶
Displays a list of all the accounts and their associated credentials.
Each account can store multiple credentials for different exchanges or services, making it easy to switch between them.
credentials

In the example above we have two accounts currently setup, the master account with gate_io API keys and a team_account with Kucoin API keys.

Manage Accounts¶
In this section we can create & delete an account or delete a credential from the existing accounts.

credentials

Create a New Account

Allows you to create a new account by providing a name. This is useful for organizing credentials under different categories or user profiles.

Fill in the New Account Name field with your preferred account name
Click Create Account
The newly created account should show in the Available Accounts and Credentials Section
Delete an Account

Provides an option to delete an existing account along with all its associated credentials, helping you keep your credential management clean and up-to-date.

Select the Account you want to delete from the drop down.
Once the desired account is selected, click Delete Account
Delete Credential

Enables you to remove specific credentials from an account without deleting the entire account. This is useful when you need to update or revoke access to a particular exchange.

In the first drop down, select the account you want to delete a credential from
In the next drop down, select the credential you want to delete.
Verify the account and credential selected is correct then click the Delete Credential button
Add Credentials (API Keys)¶
In this section we can add new credentials to an account by selecting the account and connector (e.g., exchange). You can enter the required API key and secret, which will be securely stored and used by Hummingbot for trading activities.

credentials

Select the account you want to add credentials for
Choose the connector (exchange), for example Binance
Copy - Paste your API Key and Secret key
Click the Submit Credentials button, it should take a few seconds to load then you should get the success message below:
credentials

In the Available Accounts and Credentials we now have Binance showing up under the master_account
credentials

If there is an issue with the API keys, or for example it doesn't have the necessary IP permissions you may get the message below:
credentials

Known Issues¶
Credentials / Portfolio page may take some time to load due to encrypting / decrypting of API credentials. Users may need to wait at least 30 - 60 secs for it to load completely.
Manually adding credentials for DEXes¶
Some exchanges, like DEXes will have issues trying to add the API credentials using Dashboard. You may get an error message similar to the one below:

credentials

If you get the above message, you can try the workaround below:

Go to the PMM_Simple (or any controller) page and create a random config and Upload Config

Next in the Deploy V2 page, select the controller you just created and then under Instance Name, enter credentials and then click Launch Bot

Open your terminal and run the command


docker ps -a | grep credentials
This should filter the docker containers that have the name credentials. Take note of the container ID of that instance.

Run the docker attach command to attach to the Hummingbot instance


docker attach [container_ID]
Once inside the Hummingbot CLI, you’ll need to issue the stop command as it will display a bunch of errors in the log pane since we don’t have credentials added for our strategy.

stop
Run the connect command and follow the prompts to enter the API keys for your exchange.

connect [exchange_name]
Once the API keys are successfully added for your exchange the encrypted details will be stored in a YAML file which we will then need to copy over to the master_account To do this, run the exit command first to exit out of Hummingbot and back to the terminal.

exit
Make sure you are in the /deploy folder where you cloned the Hummigbot deploy repo then run the following command to copy the credentials

cp bots/instances/hummingbot-credentials*/conf/connectors/*.yml bots/credentials/master_account/connectors/
Go back to the Dashboard and you should be able to trade with your newly added DEX credential under master_account
July 22, 2025

Viewing Portfolio
The Portfolio page in the Hummingbot Dashboard provides a detailed overview and management interface for your cryptocurrency holdings across different accounts and exchanges. It provides a holistic view of your cryptocurrency assets, allowing for better portfolio management and decision-making.

portfolio

Account, Exchange & Token Selection¶
portfolio

Select Accounts: Allows you to choose individual or multiple accounts to view their combined portfolio. In the Credentials page we added two accounts, the master_account and team_account and both can be selected here.

Select Exchanges: Lets you filter and view the portfolio for specific exchanges you've added API keys for. In this example we have gate_io, binance, and kucoin.

Select Tokens: Enables you to focus on specific tokens within your selected accounts and exchanges. In this example we can select multiple tokens like VERSE, USDT, 1000SATS, etc., to get a detailed view of their distribution and value.

Portfolio Overview¶
portfolio

Total Balance (USD): Displays the aggregated value of all selected tokens across the chosen accounts and exchanges in USD.

Allocation Visualization: A sunburst chart visualizes the percentage allocation of your portfolio by account, exchange, and token. This helps in understanding the distribution and weight of each token in your overall portfolio.

Tabular Data¶
portfolio

Provides a detailed table listing the exchange, token, units, price, value, and available units for each token. This tabular format allows for a clear and precise understanding of your holding
Portfolio Evolution over Time¶
portfolio

A line graph that shows the evolution of your portfolio’s total value over time. This helps in tracking the performance and growth of your portfolio.
Token Value Evolution over Time¶
portfolio

Another line graph that illustrates the value changes of individual tokens over time, offering insights into the volatility and performance of each asset.
July 22, 2025

Config Generator¶
Here's a detailed explanation of the different controllers available for configuration in the Hummingbot Dashboard:

PMM Simple¶
config

The PMM Simple controller in Hummingbot Dashboard implements a basic Pure Market Making strategy. It allows users to provide liquidity by placing both buy and sell orders around the mid-market price. Key features include:

Simple configuration for quick setup.
Customizable order spreads and sizes.
Basic risk management settings like stop loss and take profit.
PMM Dynamic¶
config

config

The PMM Dynamic controller in Hummingbot Dashboard implements a superset of the A+S strategy. Features include:

Using candle data from one exchange to trade on another.
Shifting mid price based on market trends.
Adjusting spread dynamically using the NATR (Normalized Average True Range) indicator for more responsive market making.
D-Man Maker V2¶
config

config

config

The D-Man Maker V2 controller is designed for more advanced market making strategies, integrating various technical indicators and risk management tools. Key features include:

Advanced spread and order size adjustments based on market conditions.
Integration with multiple technical analysis indicators.
Enhanced risk management options.
Bollinger V1¶
config

The Bollinger V1 controller utilizes Bollinger Bands for its trading strategy. Bollinger Bands are a type of statistical chart characterizing the prices and volatility over time of a financial instrument. Key features include:

Using Bollinger Bands to determine optimal entry and exit points.
Configurable band parameters to suit different market conditions.
Automated trading signals based on band interactions.
MACD BB V1¶
config

The MACD BB V1 controller combines the Moving Average Convergence Divergence (MACD) indicator with Bollinger Bands. This strategy aims to leverage the strengths of both indicators for more robust trading signals. Key features include:

Using MACD to identify trend direction and strength.
Employing Bollinger Bands to spot volatility and potential reversal points.
Automated buy and sell signals based on combined indicator analysis.
SuperTrend V1¶
config

The SuperTrend V1 controller uses the SuperTrend indicator to guide its trading decisions. The SuperTrend indicator is a trend-following tool that helps identify the prevailing direction of the market. Key features include:

Utilizing SuperTrend for dynamic support and resistance levels.
Adjusting trading strategies based on trend signals.
Configurable parameters for sensitivity and responsiveness to market changes.
XEMM Controller¶
config

The XEMM Controller (Cross-Exchange Market Making) in Hummingbot Dashboard is designed to exploit price discrepancies across different exchanges. Key features include:

Simultaneously placing buy orders on one exchange and sell orders on another.
Taking advantage of arbitrage opportunities between exchanges.
Advanced configuration for managing multiple exchange accounts and trades.
July 22, 2025

Backtesting Strategies¶
The Backtesting section in the Hummingbot Dashboard is a powerful tool available on all controller pages, allowing users to evaluate the performance of their trading strategies using historical market data.

This feature provides crucial insights into how a strategy would have performed in the past, helping users refine and optimize their configurations before deploying them in a live trading environment.

Strategy Configuration¶
Before backtesting a strategy, you need to configure it. In this example, we'll use the PMM Simple controller with the Binance connector, trading the BTC-USDT pair.
backtest

Select Connector: Choose the exchange (e.g., Binance).

Select Trading Pair: Specify the pair to trade (e.g., BTC-USDT).

Set Parameters: Configure leverage, total quote amount, position mode, and other relevant parameters.

Order Settings: Define buy and sell order levels, spread, and amount distribution.

Run Backtesting¶
With your configuration set, navigate to the backtesting section. Specify the Start Date and End Date for the historical data, the time interval for the Backtesting Resolution, and the Trade Cost percentage. Click the Run Backtesting button to initiate the process.
backtest

The backtesting results will generate in a few seconds, providing you with a comprehensive overview. Here's an example of what you might see:
backtest

Backtesting Metrics:

Net PNL (Quote): The net profit and loss in the quote currency.
Max Drawdown (USD): The maximum loss from the peak during the backtesting period.
Total Volume (Quote): The total trading volume in the quote currency.
Sharpe Ratio: A measure of risk-adjusted return.
Profit Factor: The ratio of gross profit to gross loss.
Total Executors with Position: Number of executors that had open positions during the backtest.
Accuracy Metrics:

Global Accuracy: The overall accuracy of the strategy.
Total Long & Short: Number of long and short positions taken.
Accuracy Long & Short: Accuracy percentages for long and short positions.
Close Types:

Metrics for different types of order closures such as TAKE PROFIT, TRAILING STOP, STOP LOSS, TIME LIMIT, and EARLY STOP.
Graphical Representation:

Candlestick Chart: Visualizes price movements of the trading pair over time.
PNL Quote Chart: Shows the profit and loss over time.

You can return to the configuration page to make adjustments and re-run the backtesting as needed. Once satisfied with the results, you can upload the configuration for deployment.

Upload Config to Backend API¶
backtest

Create a name for the current config

The Config Tag is similar to a version number which allows you to track changes made to the strategy config later on.

Click the Upload button to save the configuration. This makes it available on the Deploy V2 page, where you can create instances based on the saved configuration.

July 22, 2025

Deploying Instances¶
The Deploy V2 page in the Hummingbot Dashboard is designed for launching and managing Hummingbot trading instances. This page offers a streamlined interface to select configurations, set up instances, and deploy bots for automated trading.

deploy

Bot Configuration¶
deploy

Instance Name: A unique name for the bot instance you are about to deploy.

Available Images: Select the Docker image version of Hummingbot to use for the deployment. You can use different Hummingbot Docker versions like development or latest

Credentials: Select the account credentials that the bot will use for trading. This ensures that the bot has the necessary API keys and permissions to operate on the selected exchanges.

Configuration List: Displays all the available controller configurations that you have created and uploaded.

Launch an Instance¶
Choose one of the available configurations from the list by checking the box next to it.
Provide the instance name, select the appropriate Docker image, and choose the credentials.
Click on the Launch Bot button to start the bot with the selected configuration. The bot will begin trading based on the parameters and strategy defined in the configuration.
Delete a Controller Config¶
Choose one of the available configurations from the list by checking the box next to it.

Click the DELETE button to delete the config

Hummingbot API¶
Repository Update

The backend-api has been renamed to hummingbot-api, marking a major revamp of the codebase with improvements in architecture, modularity, and developer experience.

Overview¶
Hummingbot API is a comprehensive RESTful API framework designed for managing trading operations across multiple exchanges. It allows individual traders and teams to deploy custom, private servers for trade execution, portfolio management, and data collection, bot deployment, and other use cases.

GitHub Repository: github.com/hummingbot/hummingbot-api

Key Features¶
⚙️ Standardized and production-ready API for managing bots, executing trades, and monitoring multi-exchange portfolios
🔄 Expanded capabilities including direct trading, portfolio rebalancing, and account management — all via API
📊 Real-time monitoring of portfolio performance across multiple exchanges
🎯 Market data collection for real-time and historical price feeds
🔧 Comprehensive bot orchestration for managing multiple trading instances
Architecture¶
Exchanges

Bots

Hummingbot API

Clients

Hummingbot API Client

Commands & Updates

Trade & Data

Trade & Data

Custom Apps

Hummingbot
Dashboard

AI Agents

FastAPI
Server

PostgreSQL
Database

EMQX
Message Broker

Hummingbot
Instances

Binance, OKX,
Hyperliquid, etc.

Key Components¶
Server Infrastructure:
FastAPI server providing RESTful API with HTTP Basic Authentication
PostgreSQL database for storing trading data, account info, and historical performance
EMQX message broker for real-time communication with bot instances
Exchange Connectors: Built-in connectors for major CEXs and DEXs - trading and data fetching is accessible directly through the Hummingbot API or via bots that it deploys
Bot Instances: Individual Hummingbot containers connected to different exchanges
Docker Management: Orchestrates multiple Hummingbot container instances
Use Cases¶
The Hummingbot API enables various trading applications:

Custom OEMS: Build your own trading order execution management system spanning multiple exchanges
Trading Dashboards: Build custom chat, web, and mobile interfaces for controlling bots
AI-Powered Trading: Integrate with LLMs for agentic trading workflows
Risk Management Tools: Build systems for monitoring and managing trading operations
Market Data Feeds: Create real-time price and historical candles feeds for use with different applications
Getting Started¶
Installation Guide - Complete installation instructions for Docker and source installation
Quickstart Guide - Learn how to:
Add exchange credentials
View portfolio balances
Place your first market order
The guides include Docker setup and Python API client examples to get you trading in minutes.

API Routers¶
The Hummingbot API provides the following key routers:

🐳 Docker Management¶
Manage Docker containers and instances running Hummingbot

GET /docker/running - Check if Docker daemon is running
GET /docker/available-images - List available Docker images
GET /docker/active-containers - Get all running containers
POST /docker/pull-image - Pull new Docker images
POST /docker/start-container/{name} - Start a container
POST /docker/stop-container/{name} - Stop a container
POST /docker/remove-container/{name} - Remove container and archive data
💼 Account Management¶
Handle exchange account credentials and configurations

GET /accounts - List all trading accounts
POST /accounts - Create new trading account
PUT /accounts/{id} - Update account credentials
DELETE /accounts/{id} - Delete trading account
GET /accounts/{id}/balances - Get account balances
🔌 Connector Discovery¶
Discover and manage available exchange connectors

GET /connectors - List all available connectors
GET /connectors/{name} - Get connector details
GET /connectors/{name}/trading-rules - Get trading rules and limits
GET /connectors/{name}/markets - List supported trading pairs
📊 Portfolio Management¶
Monitor and analyze portfolio performance across exchanges

GET /portfolio/balances - Get aggregated portfolio balances
GET /portfolio/performance - Get portfolio performance metrics
GET /portfolio/distribution - Get token distribution analysis
GET /portfolio/history - Get historical portfolio data
💱 Trading Operations¶
Execute trades, manage orders, and monitor positions

POST /trading/orders - Place new order
GET /trading/orders - List active orders
DELETE /trading/orders/{id} - Cancel order
GET /trading/positions - Get open positions
GET /trading/history - Get trade history
POST /trading/close-position - Close a position
📈 Strategy Management¶
Configure and deploy trading strategies with real-time updates

GET /controllers - List available strategy controllers
POST /controllers/{name}/deploy - Deploy strategy controller
PUT /controllers/{id}/config - Update strategy parameters
GET /scripts - List available trading scripts
POST /scripts/run - Execute trading script
📉 Market Data¶
Access real-time and historical market data

GET /market-data/ticker/{pair} - Get current ticker data
GET /market-data/orderbook/{pair} - Get order book snapshot
GET /market-data/candles/{pair} - Get historical candles
GET /market-data/trades/{pair} - Get recent trades
WS /market-data/stream - Real-time market data stream
🤖 Bot Orchestration¶
Deploy, configure, and manage multiple bot instances

GET /bot-orchestration/bots - List all bot instances
POST /bot-orchestration/deploy - Deploy new bot
PUT /bot-orchestration/bots/{id}/config - Update bot configuration
POST /bot-orchestration/bots/{id}/start - Start bot
POST /bot-orchestration/bots/{id}/stop - Stop bot
GET /bot-orchestration/bots/{id}/status - Get bot status
🧪 Backtesting¶
Run strategy backtests with historical data

POST /backtesting/run - Start new backtest
GET /backtesting/results/{id} - Get backtest results
GET /backtesting/metrics/{id} - Get performance metrics
POST /backtesting/optimize - Run parameter optimization
Authentication¶
The API uses HTTP Basic Authentication:

Configure username and password during setup
Include credentials in the Authorization header for all requests
Example: Authorization: Basic <base64-encoded-credentials>
API Client¶
A modern, asynchronous Python client is available for interacting with the Hummingbot API. This client is used by the Hummingbot Dashboard as the interface layer for all API communications.

GitHub: hummingbot-api-client
PyPI: pypi.org/project/hummingbot-api-client
Installation¶

pip install hummingbot-api-client
Usage Example¶

from hummingbot_api_client import HummingbotAPIClient

# Initialize client
client = HummingbotAPIClient(
    base_url="http://localhost:8000",
    username="your-username",
    password="your-password"
)

# Get portfolio data
portfolio = await client.get_portfolio()

# Execute a trade
order = await client.create_order(
    connector="binance",
    trading_pair="BTC-USDT",
    order_type="limit",
    side="buy",
    amount=0.001,
    price=50000
)
Related Resources¶
Hummingbot Dashboard - Web-based interface built on top of Hummingbot API
API Client Documentation - Python client library
Hummingbot Client - Core trading engine

Installation¶
This guide covers all available installation methods for Hummingbot API.

Prerequisites¶
Docker and Docker Compose installed (for Docker installation)
Python 3.10+ and Conda (for source installation)
Exchange API keys for trading
Install with Docker (Recommended)¶
The easiest way to get started with Hummingbot API is using Docker.

1. Clone the repository¶

git clone https://github.com/hummingbot/hummingbot-api
cd hummingbot-api
2. Run the setup script¶

./setup.sh
The setup script will:

Prompt you to set API authentication credentials (username/password)
Configure the database and message broker connections
Create a .env file with all necessary configurations
Start required Docker containers (PostgreSQL, EMQX)
Pull the latest Hummingbot Docker image
Default credentials if you press Enter: admin / admin

3. Start the API¶

./run.sh
This pulls the required Docker images and runs Hummingbot API using Docker Compose and the configuration defined in the docker-compose.yml file.

The API will be accessible at http://localhost:8000. You can view the interactive Swagger UI documentation at http://localhost:8000/docs.

Install from Source (for Developers)¶
If you're developing or contributing to Hummingbot API, you can install from source.

1. Clone and setup¶

git clone https://github.com/hummingbot/hummingbot-api
cd hummingbot-api
./setup.sh
2. Install dependencies¶

make install
This will:

Create a conda environment named hummingbot-api
Activate the environment
Install all required dependencies
Set up pre-commit hooks
3. Start the API in development mode¶

./run.sh --dev
This starts the Broker and Postgres DB containers and runs the API using uvicorn with auto-reload enabled for development.

The API will be accessible at http://localhost:8000.

Install Python Client¶
The Hummingbot API Client is a Python library that provides a convenient interface for interacting with the Hummingbot API.

Install via pip¶

pip install hummingbot-api-client
Basic usage¶

import asyncio
from hummingbot_api_client import HummingbotAPIClient

# Create client instance
client = HummingbotAPIClient(
    base_url="http://localhost:8000",
    username="admin",
    password="admin"
)

# Use the client
async def main():
    accounts = await client.list_accounts()
    print(accounts)

asyncio.run(main())
Verify Installation¶
Once installed, you can verify the API is running:

Check API health¶

curl http://localhost:8000/health
Access API documentation¶
Open your browser and navigate to: - Interactive API docs: http://localhost:8000/docs - Alternative API docs: http://localhost:8000/redoc

Configuration¶
The installation creates a .env file with your configuration. You can modify these settings:

API_USERNAME and API_PASSWORD: API authentication credentials
DATABASE_URL: PostgreSQL connection string
MQTT_HOST, MQTT_PORT: EMQX message broker settings
HUMMINGBOT_IMAGE: Docker image to use for bots
Troubleshooting¶
Docker issues¶
If Docker containers fail to start:


# Stop all containers
docker-compose down

# Remove volumes and restart
docker-compose down -v
./setup.sh
./run.sh
Port conflicts¶
If port 8000 is already in use on your system, you can change it by modifying the configuration depending on your setup:

Docker¶
Update the ports mapping in your docker-compose.yml file to use a different external port. For example, to use port 8001 instead:


services:
  hummingbot-api:
    ports:
      - "8001:8000"  # Maps local port 8001 to container's port 8000
Running from Source¶
Edit the ./run.sh script to include the --port flag in the uvicorn command. For example, to run on port 8001:


if [[ "$1" == "--dev" ]]; then
    echo "Running API from source..."
    # Start dependencies and launch API with uvicorn
    docker compose up emqx postgres -d
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate hummingbot-api
    uvicorn main:app --reload --port 8001
fi
Make sure the new port you choose is not already in use.

Development issues¶
For source installation issues:


# Clean conda environment
make uninstall
make install

# Check logs
make run
Next Steps¶
After installation, proceed to the Quickstart Guide to learn how to:

Add exchange credentials
View your portfolio
Place your first order
July 22, 2025

Quickstart
This guide demonstrates how to use Hummingbot API to add exchange credentials, view your portfolio, and place a market order.

Prerequisites¶
Hummingbot API installed and running (see Installation Guide)
Exchange API keys (e.g., Binance)
Python 3.7+ with hummingbot-api-client installed (optional)
Setup Python Client (Optional)¶
If you want to use the Python client for the examples below:

Install the Hummingbot API Client:


pip install hummingbot-api-client
Create a new Python file (e.g., hummingbot_api_demo.py):


touch hummingbot_api_demo.py
Add the following code to initialize the client:


import asyncio
from hummingbot_api_client import HummingbotAPIClient

# Create client instance
client = HummingbotAPIClient(
    base_url="http://localhost:8000",
    username="admin",
    password="admin"
)
To run any of the examples below, use:


python hummingbot_api_demo.py
List Available Exchanges¶
Get a list of all available exchange connectors. Note that spot and perpetual markets are separate connectors (e.g., hyperliquid for spot and hyperliquid_perpetual for perps).


curl
Python Client

curl -u admin:admin -X 'GET' \
  'http://localhost:8000/connectors/' \
  -H 'accept: application/json'

Response:


curl
Python Client

[
  "binance",
  "binance_perpetual",
  "hyperliquid",
  "hyperliquid_perpetual",
  "okx",
  "okx_perpetual",
]

Get Connector Configuration¶
Before adding credentials, check what configuration fields are required for your connector:


curl
Python Client

curl -u admin:admin -X 'GET' \
  'http://localhost:8000/connectors/hyperliquid/config-map' \
  -H 'accept: application/json'

Response:


curl
Python Client

[
  "hyperliquid_api_secret",
  "use_vault",
  "hyperliquid_api_key"
]

Add Exchange Credentials¶
Add your exchange credentials to the API. By default, only the master_account is created. You can add multiple accounts with different names if needed.

For Hyperliquid:

hyperliquid_api_secret: Your Hyperliquid public address or vault address
hyperliquid_api_key: Your API private key
use_vault: Set to true if using vault address, false for normal account

curl
Python Client

curl -X POST http://localhost:8000/accounts/add-credential/master_account/hyperliquid \
  -u "admin:admin" \
  -H "Content-Type: application/json" \
  -d '{
    "hyperliquid_api_key": "0x1234...abcd",
    "hyperliquid_api_secret": "your-private-key",
    "use_vault": false
  }'

Response:


curl
Python Client

{
  "message": "Connector credentials added successfully,
}

View Your Portfolio¶
Check your portfolio balances across all connected exchanges:


curl
Python Client

curl -u admin:admin -X 'POST' \
  'http://localhost:8000/portfolio/state' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{}'

Response:


curl
Python Client

{
  "master_account": {
    "hyperliquid": [
      {
        "token": "USDC",
        "units": 100.00,
        "price": 1,
        "value": 100.00,
        "available_units": 100.00
      }
    ]
  }
}

Get Trading Rules¶
Before placing orders, fetch the trading rules for your intended trading pair to understand order size limits and price increments:


curl
Python Client

curl -u admin:admin -X 'GET' \
  'http://localhost:8000/connectors/hyperliquid/trading-rules?trading_pairs=HYPE-USDC' \
  -H 'accept: application/json'

Response:


curl
Python Client

{
  "HYPE-USDC": {
    "min_order_size": 0,
    "max_order_size": 1e+56,
    "min_price_increment": 0.0001,
    "min_base_amount_increment": 0.01,
    "min_quote_amount_increment": 1e-56,
    "min_notional_size": 0,
    "min_order_value": 0,
    "max_price_significant_digits": 1e+56,
    "supports_limit_orders": true,
    "supports_market_orders": true,
    "buy_order_collateral_token": "USDC",
    "sell_order_collateral_token": "USDC"
  }
}

Place a Limit Order¶
Execute a limit sell order for HYPE:


curl
Python Client

curl -u admin:admin -X 'POST' \
  'http://localhost:8000/trading/orders' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "account_name": "master_account",
  "connector_name": "hyperliquid",
  "trading_pair": "HYPE-USDC",
  "trade_type": "SELL",
  "amount": 1,
  "order_type": "LIMIT",
  "price": 47.1,
  "position_action": "OPEN"
}'

Geo-Restriction Error

If you receive an error like:


{
  "detail": "Failed to place trade: No order book exists for 'HYPE-USDC'."
}
This may indicate you are geo-restricted from trading on the exchange. Check your API logs for more details:

docker logs hummingbot-api
Complete Example¶
Here's a complete example that performs all three operations:


curl
Python Client

echo "🔑 Adding Exchange Account..."
curl -X POST "http://localhost:8000/accounts/add-account" \
  -u "admin:admin" \
  -H "Content-Type: application/json" \
  -d '{"account_name": "master_account"}'

# Step 2: Add credentials for hyperliquid
curl -X POST "http://localhost:8000/accounts/add-credential/master_account/hyperliquid" \
  -u "admin:admin" \
  -H "Content-Type: application/json" \
  -d '{
    "hyperliquid_api_key": "0x1234...abcd",
    "hyperliquid_api_secret": "your-arbitrum-private-key",
    "use_vault": false
  }'

# Wait for account sync
sleep 2

# Step 3: View portfolio
echo -e "\n\U0001F4CA Fetching Portfolio..."
curl -X POST "http://localhost:8000/portfolio/state" \
  -u "admin:admin" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{}'

# Step 4: Get trading rules for HYPE-USDC
echo -e "\n\U0001F4CF Getting Trading Rules..."
curl -X GET "http://localhost:8000/connectors/hyperliquid/trading-rules?trading_pairs=HYPE-USDC" \
  -u "admin:admin" \
  -H "accept: application/json"

# Step 5: Place limit order
echo -e "\n\U0001F4B1 Placing Limit Order..."
curl -X POST "http://localhost:8000/trading/orders" \
  -u "admin:admin" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "account_name": "master_account",
    "connector_name": "hyperliquid",
    "trading_pair": "HYPE-USDC",
    "trade_type": "SELL",
    "amount": 1,
    "order_type": "LIMIT",
    "price": 47.1,
    "position_action": "OPEN"
  }'

Next Steps¶
Now that you've completed the quickstart, explore more advanced features:

Bot Management: Deploy and manage multiple trading bots
Strategy Configuration: Configure and deploy trading strategies
Market Data: Access real-time and historical market data
Backtesting: Test your strategies with historical data
For the complete API reference, visit the API documentation when your API is running.

July 22, 2025

Broker Module
Hummingbot's brokers module allows for remote control and monitoring of multi-bot environments in a distributed context , so that bots can "live" on different machines and infrastructures (e.g. having a bot local and another bot on AWS).

To achieve this approach, there is an MQTT layer for bots to connect remotely to message brokers, as a single point of reference, using asynchronous bidirectional communication channels (push/pull). In this architecture, bots can be considered as clients to the overall environment. Bot scaling is seamless and does not require any further setup, anyone can connect any number of bots the a message broker (e.g. RabbitMQ, EMQX etc) without any other dependencies.

See the following repos for more information:

Brokers: Various deployment examples using Docker Compose
Remote client: Package that implements a remote client for Hummingbot in Python.
Watch the February 2023 community call that contains a demo of this feature:


Thanks to klpanagi and TheHolyRoger for your work! 🙏

Phase I¶
Released in v1.12.0

Interface to execute remote commands: Start , Stop , Import , Config strategy, Balance , Change balance limits
All these commands can be called using an unified web application that also receives the following information from the bots - Heartbeat - Status, PNL - History
The configuration of the broker in the client should be in the conf_client.yml file
Phase II¶
Released in v1.14.0

In this Phase, an event and data layer will be integrated into the Hummingbot codebase to support receiving and handling remote events via the message broker (MQTT), such as the case of TradingView signals.

An MQTTEventListener will be developed and integrated into the hummingbot codebase, which will provide configuration for setting the URIs of the events to listen on. Upon receiving an event, a handling callback provided by the user/developer will be executed by the MQTTEventListener, so that users operate/develop their strategy based on the input event.

Defines interfaces for subscribing to external topics and listening to messages through the EEventQueueFactory, EEventListenerFactory, ETopicQueueFactory, and ETopicListenerFactory classes.
The specification defines a base URI format for consuming external events, and URI slashes are transformed to dots for multi-broker and multi-protocol support
This extends the global configuration and adds the mqtt_external_events parameter for globally enabling/disabling external events feature for bot instances.
Future phases¶
See this Notion doc for an overview of the project. This is an ongoing project funded by Proposal HIP-20.

July 22, 2025

FAQ
See below for answers to frequently asked questions about:

Hummingbot client
Gateway middleware
Hummingbot Foundation
HBOT token
Hummingbot client¶
What type of software is Hummingbot?¶
Hummingbot is software that helps you build and run crypto trading bots, freely available at https://github.com/hummingbot/hummingbot under the open source Apache 2.0 license.

Is Hummingbot a protocol or an exchange?¶
No, Hummingbot is open source client software that you install on a local machine that interacts with exchanges and protocols.

With many connectors and strategies being added all the time, Hummingbot is a constantly evolving publicly available codebase with frequent external contributors seeking to merge their changes into the master branch, which is released once a month and widely used by tens of thousands of individual and professional bot-runners globally.

How do people use Hummingbot?¶
You can use Hummingbot to build any type of automated crypto trading bot, with the most common bot types being market making and arbitrage bots. Market making bots provide liquidity to a trading pair on an exchange, while arbitrage bots exploit price differences between trading pairs on different exchanges.

Typically, users install the Docker image version on AWS or another cloud provider. Afterwards, they can add their API key or private keys to it, which allows them to configure and run one of Hummingbot's pre-built strategies on many different exchanges.

Since Hummingbot is an open, modular codebase, many developers and professional firms fork the codebase and use it for their own purposes.

Why is Hummingbot open source?¶
Trust and transparency: Market makers need to keep their API keys, private keys, and strategy configuration private and secure, so which is why Hummingbot is a local software client, not a web-based platform. In addition, Hummingbot's open source codebase enables anyone to inspect and audit the code.

Community maintenance: Hummingbot's value proposition is that it connects to many different centralized and decentralized exchanges, along with pre-built strategy templates that enable users to run many different types of trading strategies. In order to scale the number of connectors and strategies, Hummingbot relies upon its open source community.

Democratizing HFT: From the beginning, our mission has been to democratize high-frequency trading with open source software.

Why did you make Hummingbot available to the general public?¶
As we wrote in the original Hummingbot whitepaper, market making is an important function critical to organic, efficient markets that should be decentralized to prevent the concentration risk that exists in traditional finance.

Later, we pioneered the concept of decentralized market making by writing the Liquidity Mining whitepaper and built the first such platform: Hummingbot Miner. Miner has turned into a successful, standalone business that provides liquidity to hundreds of tokens across multiple exchanges, powered by thousands of individual market makers running Hummingbot.

This has allowed CoinAlpha to spin off Hummingbot into a not-for-profit foundation, which is dedicated to keeping Hummingbot open source.

What is market making?¶
Market making is the act of simultaneously creating buy and sell orders for an asset in a market. By doing so, a market maker acts as a liquidity provider, facilitating other market participants to trade by giving them the ability to fill the market maker's orders. Traditionally, market-making industry has been dominated by highly technical quantitative hedge funds and trading firms that have the infrastructure and intelligence to deploy sophisticated algorithms at scale.

Market makers play an important role in providing liquidity to financial markets, especially in the highly fragmented cryptocurrency industry. While large professional market makers fight over the most actively traded pairs on the highest volume exchanges, there exists a massive long tail of smaller markets who also need liquidity: tokens outside the top 10, smaller exchanges, decentralized exchanges, and new blockchains.

See What is market making? for more information.

How does Hummingbot store my private keys and API keys?¶
Similar to wallet software, Hummingbot stores your private keys and API keys in encrypted form, using the password you enter when you first start Hummingbot. These keys are saved in your /conf folder.

Since Hummingbot is a local client, your private keys and API keys are as secure as the computer you are running them on. This is because the keys are used to create authorized instructions locally on the local machine, and only the instructions which have already been signed or authorized are sent out from the client.

What does it cost for me to run Hummingbot?¶
Hummingbot is a free software, so you can download, install, and run it for free.

Transactions from Hummingbot are normal transactions conducted on exchanges; therefore when operating Hummingbot, you would be subject to each exchange’s fees (e.g. maker, taker, and withdrawal fees), as you would if you were trading on that exchange normally (i.e. without Hummingbot).

There is no minimum amount of assets to use Hummingbot, but users should pay heed to exchange-specific minimum order sizes. We include links to the exchange's minimum order size page. This can be found in each exchange's page in Exchange Connectors.

Gateway middleware¶
💡 DEX / Blockchain Experience Needed

Since Hummingbot Gateway is still nascent and DEX trading bots entails more specialized blockchain engineering than running CEX bots, we recommend Gateway for users with blockchain engineering or DEX trading experience.

What is Gateway?¶
Hummingbot Gateway is API middleware that helps Hummingbot clients interact with decentralized exchanges (DEXs) on various blockchain networks. It:

Standardizes DEX API endpoints
Manages interactions with node providers, and
Utilizes Javascript-based DEX SDKs
Similar to Hummingbot client, Gateway is open source under the Apache 2.0 license. Community developers can contribute DEX and blockchain connectors to the Gateway codebase via Pull Request Proposals.

How do I use Gateway with Hummingbot?¶
If you want to understand how Gateway works, install the standalone Gateway repository: https://github.com/hummingbot/gateway

If you just want to get Gateway up and running alongside Hummingbot, following the Install with Docker process is the easiest method.

Afterwards, follow the instructions at Using Gateway with Hummingbot.

What kinds of DEX bots can you build with Gateway?¶
Currently, Hummingbot Gateway is ideal for bots that:

Find and execute arbitrage opportunities on AMM DEXs on multiple blockchains or between AMM DEXs and CEXs (cross-domain)
Automate liquidity provision behavior on AMM-RANGE DEXs such as Uniswap-V3
In the future, as Gateway should support additional use cases, but we are currently focused on enabling these only.

Can Gateway help me build MEV bots?¶
Bots that compete with others for transactions on the same blockchain (single-domain) need to compete to get transactions confirmed and thus need to play at the MEV level.

However, to improve latency, you may explore using Flashbots Protect as the RPC endpoint, i.e. use it as nodeUrl.

What background information should I learn before building DEX bots with Gateway?¶
Here are some helpful articles and videos:

Getting started with Metamask: Metamask is the current industry standard for wallets, which you use will interact with blockchains
Intro to Ethereum: Great guide from OpenZeppelin that explains how Ethereum works today (aimed at developers)
What Is Uniswap and How Does It Work?: Binance Academy article that explain Uniswap and AMMs in general.
Comparing liquidity mining options in DeFi vs. Hummingbot: This CoinAlpha blog post explains how liquidity mining is similar in DeFi and CeFi
Uniswap V3 Explained: Other DEXs like TraderJoe, SushiSwap, and PancakeSwap are starting to emulate Uniswap V3. Watch this video to understand how Uniswap V3 works.
How do node providers and mempool services work?¶
Speed and latency in DEX trading is heavily dependent on your connection to the blockchain network. Your options are to:

1 - Use a node provider

This is the most common route. Gateway ships with [Ankr] as the default node provider, since they don’t require API keys. See default settings for each chain.

Providers include:

Ankr (current default)
Alchemy
Blockdaemon
Infura
Pocket Network
2 - Use a mempool service

For advanced or professional users, mempool services allow you to “skip the line” and send your transaction bundle to a miner for inclusion in a block.

Providers include:

Flashbots
bloxRoute
BlockNative
3 - Run your own node

While this is infeasible on Solana or BNB Chain, this is possible on Ethereum and EVM-based chains. See Run a Node for more details.

How do I use Hummingbot on a AMM DEX like Uniswap?¶
Check out the amm-arb or amm-v3-lp strategies.

Hummingbot Foundation¶
What does the Hummingbot Foundation do?¶
The Hummingbot Foundation is a not-for-profit organization established in the Cayman Islands. The Foundation’s mission is to democratize high-frequency trading by enabling decentralized maintenance and community governance over the open-source Hummingbot code repository.

Below are its main roles and responsibilities:

Maintenance: Appoint and compensate maintainers who maintain Hummingbot exchange connectors by fixing bugs, resolving API changes, and adding features.
Bounties: Enable the community to sponsor bounties that reward community contributors for building new connectors, features, and enhancements
Governance: Enable the community to steer the evolution of the codebase by prioritizing work on Github issues and pull requests
Since Hummingbot is not a blockchain protocol, but rather open source client software run locally on individual client devices that interacts with protocols and exchanges, the Foundation governance system aims to fits into the existing Hummingbot open source software release process, which has been used to handle thousands of Github issues and pull requests created by the community over the past three years.

How is the Hummingbot Foundation sustainable?¶
A large part of Hummingbot’s value comes from the number of connectors it supports and its overall usage, which can be measured by the aggregate trading activity that Hummingbot users supply to connected exchanges and protocols. The Foundation has fee share agreements and other partnerships with these exchanges and protocols that rebate fees based on usage, tracked at the API header level.

Meanwhile, community developers can maintain Hummingbot components of the codebase and extend the toolset to more markets and asset types, keeping maintenance costs low.

In addition, the Foundation plans to charge bounty administration fees to administer, review and merge the development work performed by bounty contributors.

Based on the source of income above, the Foundation is projected to be self-sustainable at inception. Over time, we expect this margin to increase as volume and fees generated grow as the Hummingbot user base expands.

Who runs the Hummingbot Foundation?¶
A five-person Board of Directors provides oversight over the Foundation and oversees staff who manage day-to-day operations. This board is elected by HBOT token holders every 12 months.

In addition, the Foundation has a Chief Operating Officer and Chief Finance Officer, who collectively manage partnerships with exchanges, negotiate contracts with maintainers, and oversee the Foundation’s budget and finances.

The Foundation also employs staff who administer the governance system, respond to users on Discord, and handle other day-to-day operations of maintaining Hummingbot, including:

Review pull requests and issues linked to proposals
Communicate and coordinate with sponsors, maintainers, and contributors
Package monthly releases into Docker containers for various environments
Maintain and update documentation
Why is the Hummingbot Foundation domiciled in the Cayman Islands?¶
For the past 20 years, the Cayman Islands has been one of the preferred global jurisdictions for the incorporation of new securitizations, special purpose vehicles, and other new organizations. In 2017, the Cayman Islands introduced the Foundation Company structure, a flexible structure that allows a limited liability legal entity to operate similar to a civil law foundation, steered by a decentralized set of participants. The Hummingbot Foundation uses this structure.

See What is a Cayman Foundation Company? from Zedra, our corporate services provider in the Cayman Islands.

How do I apply for a job with the Hummingbot Foundation?¶
Post a message with your CV to one of the Foundation staff on Discord.

HBOT token¶
What is the HBOT token?¶
The Hummingbot Governance Token (HBOT) is the medium of governance for the Hummingbot open source ecosystem. It is a standard Ethereum ERC-20 token with a fixed total supply of 1,000,000,000 HBOT tokens.

What can I do with the HBOT token?¶
HBOT is a governance token that give holders control over the Hummingbot codebase, the HBOT community treasury, and the Hummingbot Foundation. For instance, holders can:

Approve all pull requests to the Hummingbot codebase
Propose architectural changes and steer the roadmap
Allocate the HBOT community treasury
Appoint maintainers for exchange connectors who share in fees rebated from that exchange
Elect Foundation board of directors
HBOT token holders make these decisions by creating proposals and voting with their token balances. One HBOT equals one vote, and voting does not consume any tokens.

Will voting with HBOT cost gas or incur other transaction fees?¶
No. All Hummingbot Foundation proposals are on Snapshot, which lets HBOT holders vote by signing messages using their HBOT token balance to vote on issues without paying gas. Snapshots are recorded to IPFS to generate a permanent record.

How do I know that I'm using the correct HBOT token?¶
To prevent HBOT token holders from being scammed by fraudulent versions of the token, unverified pools/DEXs, or incorrect coin listings, we maintain a compilation of verified HBOT-related pages from Reputable Sources. This does not constitute investment advice or a recommendation for any platform or market listed.

Does the Foundation plan to list HBOT on (any crypto exchange)?¶
Please see Reputable Sources for information about venues where HBOT may be traded.

How does the Foundation plan to distribute remaining HBOT tokens?¶
The Foundation plans to distribute the remaining 36 million tokens (36% of total supply) to Hummingbot users over the 4 years after inception across fixed Epochs. The goal is to distribute tokens to developers who contribute improvements to the codebase, and users of the Hummingbot software on connected exchanges and market making platforms.

See Hummingbot Governance Proposals for more information on the categories of HBOT grants.

I was an early user of Hummingbot. Am I eligible to claim HBOT tokens?¶
The Hummingbot Foundation is grateful to everyone who has used Hummingbot, found bugs, and contributed to the codebase in the past. However, for the Retroactive Distribution, the Foundation decided to allocate tokens only to two types of historical activity: 1) Github code contributors and 2) users of the Hummingbot Miner platform. We chose these two types because past activity can be verified through public commit history and Miner API keys, respectively.

Other than those listed in the HBOT announcement, there are no other eligible HBOT recipients.

What if I accidentally used an exchange address to claim HBOT tokens?¶
If you accidentally entered a Binance.com deposit address to claim your tokens, here is how you may be able to retrieve those tokens:

Log into Binance.com
In the Wallet section -> Deposit Crypto, there is a "deposit hasn't arrived?" section
Select "Search" and "Deposited an Unlisted coin"
Select "Submit Appeal" and enter the transaction details
July 22, 2025

Glossary¶
When you start diving into the Hummingbot ecosystem, you'll probably encounter some unfamiliar terms and phrases along the way. To help you on your journey, we've defined some of the most common trading vocabularies here in this handy cheat sheet.

Base asset¶
The asset in a trading pair whose quantity is fixed as a single unit in a price quote. For example, in a price quotation of ETH/DAI 100, ETH is the base asset and 100 is the amount of DAI exchangeable for each unit of ETH.

In Hummingbot, the first token in a trading pair is always the base asset. See quote asset for more info.

Bollinger Bands¶
Bollinger Bands (BB) are a widely popular technical analysis instrument created by John Bollinger in the early 1980’s. Bollinger Bands consist of a band of three lines which are plotted in relation to security prices. The line in the middle is usually a Simple Moving Average (SMA) based on a certain historical window length.

The SMA then serves as a base for the Upper and Lower Bands, which are used as a way to measure volatility by observing the relationship between the Bands and price. Typically the Upper and Lower Bands are set a number of standard deviations away from the SMA (The Middle Line).



Parameters used in V2 Strategies:

bb_std: Number of standard deviations used to set the upper and lower Bollinger Bands.
bb_length: Number of candle intervals used to calculate the SMA.
Centralized exchange (“CEX”)¶
An exchange which is operated by a central authority. In addition to order matching and broadcasting, the centralized exchange keeps custody of users’ assets.

Decentralized exchange (“DEX”)¶
An exchange which operates in a decentralized way, using smart contracts to facilitate the transacting in and settling of assets. Generally, one distinguishing feature of a decentralized exchange is that participants keep custody of their own assets in their own wallets; the DEX facilitates the direct wallet-to-wallet settlement between counterparties in a transaction.

MACD¶
MACD (Mean Average Convergence Divergence) is an extremely popular indicator used in technical analysis. MACD can be used to identify aspects of a security's overall trend. Most notably these aspects are momentum, as well as trend direction and duration. What makes MACD so informative is that it is actually the combination of two different types of indicators. First, MACD employs two Moving Averages of varying lengths (which are lagging indicators) to identify trend direction and duration. Then, MACD takes the difference in values between those two Moving Averages (MACD Line) and an EMA of those Moving Averages (Signal Line) and plots that difference between the two lines as a histogram which oscillates above and below a center Zero Line. The histogram is used as a good indication of a security's momentum.

To fully understand the MACD indicator, it is first necessary to break down each of the indicator's components.

The three major components of MACD

The MACD Line: The MACD Line is a result of taking a longer term EMA and subtracting it from a shorter term EMA.The most commonly used values are 26 days for the longer term EMA and 12 days for the shorter term EMA, but it is the trader's choice.
The Signal Line: The Signal Line is an EMA of the MACD Line described in Component 1. The trader can choose what period length EMA to use for the Signal Line however 9 is the most common.
The MACD Histogram: As time advances, the difference between the MACD Line and Signal Line will continually differ. The MACD histogram takes that difference and plots it into an easily readable histogram. The difference between the two lines oscillates around a Zero Line.


Parameters used in V2 Strategies:

macd_fast: number of candle intervals used to calculate the shorter-term EMA
macd_slow: number of candle intervals used to calculate the longer-term EMA
macd_signal: EMA of the MACD signal line
Maker¶
A party that places maker orders, and in doing so, provides liquidity to the market.

Maker order¶
A “limit order”; which is an order to buy or sell an asset at a specified price and quantity. Executing this order is not guaranteed; the order is only filled if there is a taker that accepts the price and quantity and transacts.

Order book¶
A list of currently available (maker) orders on an exchange, showing all of the current buyer and seller interest in an asset.

Quote asset¶
The asset in a asset pair whose quantity varies and whose quantity is denoted by the numerical figure of the price quote. For example, in a price quotation of ETH/DAI 100, DAI is the quote currency and 100 units of DAI are referenced in this exchange.

In Hummingbot, the second token in a trading pair is always the quote asset. See base asset for more info.

Taker¶
A party that places taker orders, which execute immediately and fill a maker order.

Taker order¶
A “market order”; an order to buy or sell a specified quantity of an asset which is filled immediately at the best available price(s) available on the exchange.

Mid price¶
The average of best bid and best ask price in the orderbook.

Hedging price¶
In cross exchange strategy, is the net cost of the other side of your limit order i.e., the cost of you making a taker order.

For example on your taker market, if you can buy 25 tokens for say a net price of $100 (other market makers have limit sell orders at a net price of 100 for all 25, e.g. 7.5 @ $99, 10 @ $100, 7.5 @ $101), then on your maker side, you would place a limit sell order for 25 @ $101 (assume 1% min profitability). If someone fills your sell order (you sell at $101), you immediately try to hedge by buying on the taker side at $100.

July 22, 2025