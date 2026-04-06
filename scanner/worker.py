from __future__ import annotations

import time

import ccxt
import pandas as pd

from config.settings import (
    ALERT_COOLDOWN_MINUTES,
    EXCHANGE_ID,
    MAX_SYMBOLS,
    MIN_LAST_PRICE,
    MIN_QUOTE_VOLUME_24H,
    OHLCV_LIMIT,
    ONLY_PERPETUAL,
    QUOTE_ASSET,
    SCAN_LOOP_SECONDS,
    SYMBOL_PAUSE_SECONDS,
    TIMEFRAME,
)
from db.database import init_db, insert_signal, signal_exists_recently
from scanner.strategy import evaluate_symbol


def build_exchange():
    exchange_class = getattr(ccxt, EXCHANGE_ID)
    return exchange_class(
        {
            "enableRateLimit": True,
            "options": {"defaultType": "future"},
        }
    )


def get_symbols(exchange) -> list[str]:
    markets = exchange.load_markets()
    symbols = []

    for symbol, market in markets.items():
        if not market.get("active", False):
            continue
        if ONLY_PERPETUAL and not market.get("swap", False):
            continue
        if market.get("quote") != QUOTE_ASSET:
            continue
        symbols.append(symbol)

    tickers = exchange.fetch_tickers(symbols)
    filtered = []

    for symbol in symbols:
        ticker = tickers.get(symbol) or {}
        quote_volume = float(ticker.get("quoteVolume") or 0.0)
        last_price = float(ticker.get("last") or 0.0)

        if quote_volume < MIN_QUOTE_VOLUME_24H:
            continue
        if last_price < MIN_LAST_PRICE:
            continue

        filtered.append(symbol)

    filtered = sorted(set(filtered))
    if MAX_SYMBOLS > 0:
        filtered = filtered[:MAX_SYMBOLS]
    return filtered


def fetch_df(exchange, symbol: str) -> pd.DataFrame:
    rows = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=OHLCV_LIMIT)
    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna().reset_index(drop=True)


def run():
    init_db()
    exchange = build_exchange()

    while True:
        try:
            symbols = get_symbols(exchange)
            print(f"scan started | symbols={len(symbols)}")

            for symbol in symbols:
                try:
                    if signal_exists_recently(symbol, ALERT_COOLDOWN_MINUTES):
                        time.sleep(SYMBOL_PAUSE_SECONDS)
                        continue

                    df = fetch_df(exchange, symbol)
                    result = evaluate_symbol(symbol, TIMEFRAME, df)

                    if result.should_alert:
                        insert_signal(result.payload)
                        print(f"SIGNAL | {symbol} | {result.reason} | score={result.score}")

                    time.sleep(SYMBOL_PAUSE_SECONDS)

                except Exception as symbol_exc:
                    print(f"symbol error | {symbol} | {symbol_exc}")

            print(f"cycle done | sleep={SCAN_LOOP_SECONDS}s")
            time.sleep(SCAN_LOOP_SECONDS)

        except Exception as loop_exc:
            print(f"loop error | {loop_exc}")
            time.sleep(10)


if __name__ == "__main__":
    run()
