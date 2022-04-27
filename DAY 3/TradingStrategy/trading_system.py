"""
This script contains the main trading system.
"""

import os
import sys
import json
import logging
import numpy as np
from datetime import datetime
import configparser as ConfigParser
from alpaca_trade_api.rest import TimeFrame

from connection import Client
from strategy import Momentum

#intializing parameters
configParser = ConfigParser.RawConfigParser()
configParser.read('config.cfg')

TIMEFRAME = '1Min'
MAX_BUDGET = float(configParser.get('system', 'max_budget'))
EXCHANGE = str(configParser.get('system', 'exchange'))
UNIVERSE = json.loads(configParser.get('system', 'universe'))
FAST_MA = int(configParser.get('strategy', 'fast_ma'))
SLOW_MA = int(configParser.get('strategy', 'slow_ma'))

#split the budget equally among all the assets in the asset UNIVERSE
BUDGET = MAX_BUDGET//len(UNIVERSE)

# logging init
logging.basicConfig(
    filename='error.log',
    level=logging.WARNING,
    format='%(asctime)s:%(levelname)s:%(message)s')


# setup the connection with the API
client = Client()
websocket = client.streaming_api()
api = client.rest_api()


class System:
    def __init__(self, ticker:str):
        """
        Create an instance of the Trading System for Time-series momentum.

        :param ticker: (str) ticker symbol of the security to trade.
        """
        self.ticker = ticker
        print(f"Intializing Momentum Strategy for : {ticker} .............")
        #intialize the strategy
        self.strategy = Momentum(FAST_MA, SLOW_MA)
        self.get_history()

    def get_history(self):
        """
        A function to get the historical bars of pair
        """
        try:
            self.price = api.get_crypto_bars(self.ticker, TIMEFRAME,
                                            datetime.now().date(),
                                            limit=SLOW_MA,
                                            exchanges=[EXCHANGE]).df.close.values
        except Exception as e:
            logging.exception(e)
            print(e)

    def close_position(self):
        """
        Close the current market position of the asset.
        """
        try:
            # close the position if exist
            order = api.close_position(self.ticker)
            # check if filled
            status = api.get_order(order).status
            return status
        except Exception as e:
            logging.exception(e)
            print(e)

    def check_market_open(self):
        """
        A function to check if the market open. If not the sleep till
        the market opens.
        """
        clock = api.get_clock()
        if clock.is_open:
            pass
        else:
            time_to_open = clock.next_open - clock.timestamp
            print(
                f"Market is closed now going to sleep for {time_to_open.total_seconds()//60} minutes")
            time.sleep(time_to_open.total_seconds())

    def get_dollar_qty(self, symbol:str)->int:
        """
        Get the Quantity of stocks to trade based on the dollar value.

        :param symbol:(str) ticker symbol of the stock.
        :return :(int)Quantity to trade.
        """
        current_asset_price = api.get_latest_crypto_trade(symbol,
                                                          exchange=EXCHANGE).price
        qty = (BUDGET//2) // current_asset_price
        return qty

    def OMS(self, side:str):
        """
        A simple Order Management System that sends out orders to the Broker
        on arrival of a trading signal.

        :param side:(str) side of the signal.
        :return: (None)
        """

        if side=='LONG':
            try:
                order_info = api.submit_order(
                                symbol=self.ticker,
                                #qty=self.get_dollar_qty(self.ticker),
                                notional=BUDGET,
                                side='buy',
                                type='market',
                                time_in_force='day')

                print(order_info)
            except Exception as e:
                logging.exception(e)
                print(e)
        else:
            self.close_position()

    def update_price(self, price:float):
        """
        Update the prices in the queue everytime a new price is available.
        :return :(None)
        """
        self.price[:-1] = self.price[1:]
        self.price[-1] = price


    def on_bar(self, bar):
        """
        This function will be called everytime a new bar is generated.
        """
        self.update_price(bar.close)
        signal = self.strategy.check_for_trades(self.price)
        if signal is not None:
            print(f"Signal for {self.ticker} is {signal}")
            self.OMS(signal)

def get_instances():
    """
    Generates System instances for each pair.
    """
    instances = dict()
    for ticker in UNIVERSE:
        instances[ticker] = System(ticker)
    return instances

def get_pnl():
    """
    Gets the account PnL
    """
    # Get account info
    account = api.get_account()
    # Check our current balance vs. our balance at the last market close
    return float(account.equity) - float(account.last_equity)



if __name__ == "__main__":
    try:
        print("Starting Momentum Algorithm ................")
        # generate instances
        instances = get_instances()
        async def OnBar(bar):
             """
             This function will run once a minute on arrival of a minute bar.

             :params bar: (Bar object) the latest minute bar data
             """
             if bar.exchange == EXCHANGE:
                instances[bar.symbol].on_bar(bar)
                print(f"Account PnL : {get_pnl()}")

        # unique ticker to subscribe
        print(f"Listening to feeds from : {UNIVERSE}")
        # Subscribe to live data
        websocket.subscribe_crypto_bars(OnBar, *UNIVERSE)
        # Start streaming data
        websocket.run()

    except (KeyboardInterrupt, RuntimeError):
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
        api.close_all_positions()
