"""
This script contains a simple moving average crossover strategy

Strategy -
Step 1: Calculate the fast and slow moving average.
Step 2: If the fast moving average is above the slow moving average then long.
Step 3: If the fast moving average goes below the slow moving average then close
        the long position.

Betting strategy -
Bet 100% of the entire budget of that asset.
"""

import numpy as np

class Momentum:
    def __init__(self, fast_ma:int, slow_ma:int):
        """
        Create an instance of pairs trading strategy.

        :param fast_ma:(int) the window size of moving average.
        :param short_threshold:(float) the window size of moving average.
        """
        self.fast_ma = fast_ma
        self.slow_ma = slow_ma
        #track the current position
        self.position = None

    def get_ma(self, price:np.array)->(float, float):
        """
        Get the moving averages

        :param price:(np.array) historical price series.
        :return:(float, float) fast_ma, slow_ma
        """
        slow_ma = np.mean(price[-self.slow_ma:])
        fast_ma = np.mean(price[-self.fast_ma:])
        return slow_ma, fast_ma

    def check_for_trades(self, price:np.array)->str:
        """
        Check for trade signals i.e. if moving averages cross each other.

        :param price:(np.array) historical price series.
        :return:(str) signals LONG or CLOSE
        """
        slow_ma, fast_ma = self.get_ma(price)
        print(f"Slow_MA : {slow_ma} | Fast_MA : {fast_ma}")
        if self.position is None:
            if fast_ma > slow_ma:
                #long the asset
                self.position = 'long'
                return 'LONG'

        else:
            if fast_ma < slow_ma:
                #short the asset
                self.position = None
                return 'CLOSE'
