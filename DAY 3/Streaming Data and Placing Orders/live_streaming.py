import configparser as ConfigParser
import alpaca_trade_api as trade_api
import asyncio

configParser = ConfigParser.RawConfigParser()
configFile = 'config.cfg'
configParser.read(configFile)
API_KEY = configParser.get('alpaca', 'api_key')
API_SECRET = configParser.get('alpaca', 'api_secret')


stream_api = trade_api.Stream(API_KEY, API_SECRET)

equities = ['SPY']
crypto = ['BTCUSD']

async def OnBar(bar):
    #do something with the bar
    print(bar)

async def OnTrade(trade):
    #do something with the trades
    print(trade)

async def OnQuote(quote):
 #do something with the quotes
 print(quote)


# Subscribe to live crypto data
#stream_api.subscribe_crypto_bars(OnBar, *crypto)
stream_api.subscribe_crypto_trades(OnTrade, *crypto)
#stream_api.subscribe_crypto_quotes(OnQuote, *crypto)

# Subscribe to live US market data
# stream.subscribe_bars(OnBar, *equities)
# stream.subscribe_trades(OnTrade, *equities)
# stream.subscribe_quotes(OnQuote, *equities)

# Start streaming data
stream_api.run()
