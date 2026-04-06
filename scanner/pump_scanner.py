import ccxt
import pandas as pd
from config.settings import *

exchange = ccxt.binance({
    "options": {"defaultType": "future"}
})

def get_symbols():
    markets = exchange.load_markets()
    return [s for s in markets if "USDT" in s]

def fetch_ohlcv(symbol):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=100)
    df = pd.DataFrame(ohlcv, columns=["time","open","high","low","close","volume"])
    return df

def check_breakout(df):

    range_high = df["high"].iloc[-BREAKOUT_LOOKBACK:].max()
    last_close = df["close"].iloc[-1]

    if last_close > range_high:
        return True

    return False

def run():

    symbols = get_symbols()

    for symbol in symbols:

        try:

            df = fetch_ohlcv(symbol)

            if check_breakout(df):

                print("BREAKOUT:", symbol)

        except:
            pass

if __name__ == "__main__":
    run()
